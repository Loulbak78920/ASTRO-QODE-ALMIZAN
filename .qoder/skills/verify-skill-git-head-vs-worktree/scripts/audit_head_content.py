#!/usr/bin/env python3
"""Read-only audit of the *content* of committed Skill blobs.

The companion script `head_vs_worktree.py` answers "is the disk byte-identical
to HEAD" using OIDs and byte hashes. This script answers the next questions:
what is actually committed, is that text structurally valid, and where does it
differ from the worktree?

It extracts `git cat-file blob HEAD:<path>` under the Skill prefix into a
directory outside the repository, compares bytes with the worktree, emits a
bounded unified diff, and runs byte-level and structural checks on the
committed bytes. It never stages, commits, checks out, or writes inside the
repository. The extraction directory is removed unless `--keep` is passed.

Exit codes: 0 CONTENT_OK, 1 CONTENT_OK_DISK_DIFFERS or CONTENT_FAIL, 2 usage or
environment error.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

CACHE_DIRS = {"__pycache__"}
CACHE_SUFFIXES = {".pyc", ".pyo"}
FAIL_MARKERS = re.compile(r"\b(TODO|TBD|FIXME|XXX)\b")
NAME_RE = re.compile(r"^[a-z0-9-]+$")


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Git:
    def __init__(self) -> None:
        self.env = os.environ.copy()
        self.env["GIT_OPTIONAL_LOCKS"] = "0"
        self.env["GIT_TERMINAL_PROMPT"] = "0"
        self.env["GIT_PAGER"] = "cat"

    def run(self, cwd: Path, *args: str) -> tuple[int, bytes, bytes]:
        cmd = ["git", "--no-pager", "-C", str(cwd), *args]
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=120, env=self.env)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 128, b"", str(exc).encode("utf-8", "replace")
        return proc.returncode, proc.stdout, proc.stderr

    def text(self, cwd: Path, *args: str) -> tuple[int, str]:
        code, out, err = self.run(cwd, *args)
        return code, out.decode("utf-8", "replace").strip() if code == 0 else err.decode("utf-8", "replace").strip()

    def zlist(self, cwd: Path, *args: str) -> tuple[int, list[str]]:
        code, out, err = self.run(cwd, *args)
        if code != 0:
            return code, [err.decode("utf-8", "replace").strip()]
        return 0, [item.decode("utf-8", "replace") for item in out.split(b"\0") if item]


def parse_tree(git: Git, root: Path) -> tuple[dict[str, str], set[str]]:
    code, items = git.zlist(root, "ls-tree", "-r", "-z", "HEAD")
    if code != 0:
        return {}, set()
    blobs: dict[str, str] = {}
    gitlinks: set[str] = set()
    for item in items:
        meta, _, path = item.partition("\t")
        parts = meta.split()
        if len(parts) != 3:
            continue
        if parts[1] == "blob":
            blobs[path] = parts[2]
        elif parts[1] == "commit":
            gitlinks.add(path)
    return blobs, gitlinks


def walk_disk(skill_dir: Path) -> list[str]:
    found: list[str] = []
    for current, dirs, files in os.walk(skill_dir):
        here = Path(current)
        dirs[:] = sorted(d for d in dirs if d != ".git" and d not in CACHE_DIRS)
        for name in sorted(files):
            if name == ".git" or Path(name).suffix.lower() in CACHE_SUFFIXES:
                continue
            path = here / name
            try:
                if not stat.S_ISREG(path.stat().st_mode):
                    continue
            except OSError:
                continue
            found.append(path.relative_to(skill_dir).as_posix())
    return found


def snapshot_index(git: Git, root: Path) -> dict[str, object]:
    code, path_text = git.text(root, "rev-parse", "--git-path", "index")
    if code != 0 or not path_text:
        return {"exists": False}
    index_path = Path(path_text)
    if not index_path.is_absolute():
        index_path = root / index_path
    try:
        info = index_path.stat()
    except OSError:
        return {"path": str(index_path), "exists": False}
    try:
        digest = sha256_file(index_path)
    except OSError:
        digest = ""
    return {
        "path": str(index_path),
        "exists": True,
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "sha256": digest,
    }


def describe_index(snap: dict[str, object]) -> str:
    if not snap.get("exists"):
        return f"INDEX: {snap.get('path') or '(unknown)'} absent"
    return (
        f"INDEX: {snap['path']} size={snap['size']} "
        f"mtime_ns={snap['mtime_ns']} sha256={snap['sha256']}"
    )


def split_frontmatter(text: str) -> tuple[list[str] | None, str, int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, 0
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], "\n".join(lines[index + 1:]), index + 1
    return None, text, 0


def parse_yaml(frontmatter: list[str]) -> tuple[dict[str, object] | None, str]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return None, "YAML_UNAVAILABLE"
    try:
        data = yaml.safe_load("\n".join(frontmatter))
    except Exception as exc:  # noqa: BLE001 - report the parser message verbatim
        return None, f"YAML_INVALID: {exc}"
    if not isinstance(data, dict):
        return None, "YAML_NOT_MAPPING"
    return data, ""


def structural_audit(
    data: bytes,
    rel: str,
    skill_name: str,
    strict_lf: bool,
) -> tuple[list[tuple[str, str]], dict[str, object]]:
    checks: list[tuple[str, str]] = []
    info: dict[str, object] = {}

    def add(status: str, code: str, detail: str = "") -> None:
        checks.append((status, f"{code}{(' ' + detail) if detail else ''}"))

    if rel != "SKILL.md":
        try:
            data.decode("utf-8")
            add("PASS", "utf8_strict")
        except UnicodeDecodeError as exc:
            add("FAIL", "utf8_invalid", f"byte={exc.start}")
        if data.startswith(b"\xef\xbb\xbf"):
            add("WARN", "bom_present")
        crlf = data.count(b"\r\n")
        info["crlf"] = crlf
        if crlf:
            add("FAIL" if strict_lf else "WARN", "crlf_present", f"count={crlf}")
        if not data.endswith(b"\n"):
            add("WARN", "no_final_newline")
        fences = sum(1 for line in data.decode("utf-8", "replace").splitlines() if line.lstrip().startswith("```"))
        info["fences"] = fences
        if fences % 2:
            add("FAIL", "fences_unbalanced", f"count={fences}")
        return checks, info

    text = data.decode("utf-8", "replace")
    bom = data.startswith(b"\xef\xbb\xbf")
    info["bom"] = bom
    if bom:
        add("FAIL", "bom_present")

    try:
        decoded = data.decode("utf-8")
        add("PASS", "utf8_strict")
    except UnicodeDecodeError as exc:
        add("FAIL", "utf8_invalid", f"byte={exc.start}")
        decoded = text

    if decoded.startswith("\ufeff"):
        decoded = decoded[1:]

    frontmatter, body, close_index = split_frontmatter(decoded)
    if frontmatter is None:
        add("FAIL", "frontmatter_missing")
        fm: dict[str, object] = {}
    else:
        add("PASS", "frontmatter_delimiters")
        fm, yaml_error = parse_yaml(frontmatter)
        if fm is None:
            add("FAIL", yaml_error.split(":")[0], yaml_error)
            fm = {}
        else:
            add("PASS", "yaml_parse")

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        add("FAIL", "name_missing")
    else:
        info["name"] = name
        if not NAME_RE.match(name):
            add("FAIL", "name_not_hyphen_case", name)
        else:
            add("PASS", "name_hyphen_case", name)
        if name != skill_name:
            add("FAIL", "name_dir_mismatch", f"name={name} dir={skill_name}")
        else:
            add("PASS", "name_matches_real_dir", skill_name)

    description = fm.get("description")
    if not isinstance(description, str) or not description:
        add("FAIL", "description_missing")
    else:
        desc_lines = len(description.splitlines())
        desc_chars = len(description)
        info["desc_lines"] = desc_lines
        info["desc_chars"] = desc_chars
        if desc_lines != 1:
            add("FAIL", "description_multiline", f"lines={desc_lines}")
        else:
            add("PASS", "description_single_line", f"chars={desc_chars}")
        if desc_chars > 1024:
            add("FAIL", "description_too_long", f"chars={desc_chars}")

    all_lines = decoded.splitlines()
    body_lines = max(0, len(all_lines) - close_index) if frontmatter is not None else len(all_lines)
    info["body_lines"] = body_lines
    if body_lines >= 500:
        add("FAIL", "body_too_long", f"lines={body_lines}")
    else:
        add("PASS", "body_line_limit", f"lines={body_lines}")

    body_lines_list = body.splitlines()
    in_fence = False
    h1 = h2 = h3 = fences = 0
    trailing = 0
    tabs = 0
    placeholders: list[tuple[int, str]] = []
    for offset, line in enumerate(body_lines_list):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fences += 1
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("# "):
            h1 += 1
        elif line.startswith("## "):
            h2 += 1
        elif line.startswith("### "):
            h3 += 1
        if line != line.rstrip():
            trailing += 1
        if "\t" in line:
            tabs += 1
        marker = FAIL_MARKERS.search(line)
        if marker:
            placeholders.append((close_index + offset + 1, marker.group(1)))
        if "<skill-name>" in line:
            placeholders.append((close_index + offset + 1, "<skill-name>"))

    info["h1"] = h1
    info["h2"] = h2
    info["h3"] = h3
    info["fences"] = fences
    info["trailing_ws"] = trailing
    info["tabs"] = tabs
    info["checklist"] = sum(1 for line in body_lines_list if re.match(r"^- \[[ x]\] ", line))
    info["table_rows"] = sum(
        1 for line in body_lines_list if line.startswith("|") and not re.match(r"^\|[-: |]+\|$", line)
    )

    if fences % 2:
        add("FAIL", "fences_unbalanced", f"count={fences}")
    else:
        add("PASS", "fences_balanced", f"count={fences}")
    if h1 == 1:
        add("PASS", "single_h1")
    elif h1 == 0:
        add("FAIL", "h1_missing")
    else:
        add("FAIL", "h1_multiple", f"count={h1}")

    crlf = data.count(b"\r\n")
    info["crlf"] = crlf
    if crlf:
        add("FAIL" if strict_lf else "WARN", "crlf_present", f"count={crlf}")
    if tabs:
        add("WARN", "tab_present", f"lines={tabs}")
    if trailing:
        add("WARN", "trailing_whitespace", f"lines={trailing}")
    if not data.endswith(b"\n"):
        add("WARN", "no_final_newline")

    controls = [
        (index, hex(ord(char)))
        for index, char in enumerate(decoded)
        if (ord(char) < 0x20 and char not in "\n\r\t") or ord(char) == 0x7F
    ]
    if controls:
        add("FAIL", "control_characters", f"count={len(controls)} first={controls[0][1]}")

    for line_number, marker in placeholders:
        add("FAIL", "placeholder_outside_fence", f"line={line_number} token={marker}")

    return checks, info


def bounded_diff(
    head: bytes,
    disk: bytes,
    rel: str,
    context: int,
    max_lines: int,
) -> tuple[list[str], int, str]:
    if b"\0" in head[:8192] or b"\0" in disk[:8192]:
        return [], 0, "binary"
    try:
        left = head.decode("utf-8").splitlines(keepends=True)
        right = disk.decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return [], 0, "non-utf8"
    lines = list(
        difflib.unified_diff(
            left,
            right,
            fromfile=f"HEAD:{rel}",
            tofile=f"disk:{rel}",
            n=context,
            lineterm="",
        )
    )
    total = len(lines)
    if total > max_lines:
        return lines[:max_lines] + [f"... (diff truncated, {total - max_lines} more lines)"], total, "text"
    return lines, total, "text"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only audit of committed Skill blob content (extract, diff, structure).",
    )
    parser.add_argument("skill_dir", help="absolute path of the Skill directory")
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        metavar="REL",
        help="audit only this path (relative to the Skill directory); repeatable",
    )
    parser.add_argument("--out", help="parent directory for extraction; must be outside the repository")
    parser.add_argument("--keep", action="store_true", help="keep the extraction directory")
    parser.add_argument("--strict-lf", action="store_true", help="treat CRLF as a failure")
    parser.add_argument("--no-diff", action="store_true", help="skip the unified diff")
    parser.add_argument("--context", type=int, default=3)
    parser.add_argument("--max-diff-lines", type=int, default=200)
    parser.add_argument("--max-files", type=int, default=400)
    args = parser.parse_args(argv)

    configure_stdout()
    if shutil.which("git") is None:
        print("FAIL environment: git not found in PATH")
        print("RESULT CONTENT_ERROR")
        return 2
    if args.context < 0 or args.max_diff_lines < 1 or args.max_files < 1:
        print("FAIL usage: --context must be >= 0, --max-diff-lines and --max-files >= 1")
        print("RESULT CONTENT_ERROR")
        return 2

    skill_dir = Path(args.skill_dir).expanduser()
    if not skill_dir.is_dir():
        print(f"FAIL usage: not a directory: {skill_dir}")
        print("RESULT CONTENT_ERROR")
        return 2
    skill_dir = skill_dir.resolve()
    print(f"SKILL_DIR: {skill_dir}")

    git = Git()
    code, root_text = git.text(skill_dir, "rev-parse", "--show-toplevel")
    if code != 0 or not root_text:
        print("VERDICT: NO_REPO")
        print(f"NOTE: git rev-parse failed with exit {code}: {root_text}")
        print("RESULT CONTENT_FAIL")
        return 1
    root = Path(root_text).resolve()
    index_before = snapshot_index(git, root)

    def finish(exit_code: int) -> int:
        index_after = snapshot_index(git, root)
        print("")
        print(describe_index(index_after))
        unchanged = all(
            index_before.get(key) == index_after.get(key)
            for key in ("exists", "size", "mtime_ns", "sha256")
        )
        print(f"INDEX_UNCHANGED: {unchanged}")
        return exit_code

    code, prefix_text = git.text(skill_dir, "rev-parse", "--show-prefix")
    prefix = (prefix_text if code == 0 else "").replace("\\", "/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    code, head_text = git.text(root, "rev-parse", "HEAD")
    if code != 0 or not head_text:
        print("VERDICT: NO_COMMITS")
        print("RESULT CONTENT_FAIL")
        return finish(1)
    head = head_text
    code, object_type = git.text(root, "cat-file", "-t", head)
    if code != 0 or object_type != "commit":
        print(f"HEAD: {head}")
        print(f"VERDICT: HEAD_OBJECT_INVALID ({object_type or 'unresolved'})")
        print("RESULT CONTENT_FAIL")
        return finish(1)

    code, meta = git.text(root, "log", "-1", "--format=%H%x1f%cI%x1f%s")
    head_iso = head_subject = ""
    if code == 0:
        fields = meta.split("\x1f")
        if len(fields) >= 3:
            head_iso, head_subject = fields[1], fields[2]

    blobs, gitlinks = parse_tree(git, root)
    package_blobs = {path: oid for path, oid in blobs.items() if path.startswith(prefix)}
    package_gitlinks = {path for path in gitlinks if path.startswith(prefix)}

    selected: list[str] = []
    if args.path:
        seen: set[str] = set()
        for raw in args.path:
            rel = raw.replace("\\", "/").strip()
            while rel.startswith("./"):
                rel = rel[2:]
            rel = rel.strip("/")
            if not rel:
                print(f"FAIL usage: empty --path {raw!r}")
                print("RESULT CONTENT_ERROR")
                return finish(2)
            repo_rel = prefix + rel
            if repo_rel not in package_blobs:
                if repo_rel in package_gitlinks:
                    print(f"PATH {rel}: GITLINK_UNSUPPORTED")
                else:
                    print(f"PATH {rel}: PATH_NOT_AT_HEAD")
                print("RESULT CONTENT_FAIL")
                return finish(1)
            if rel not in seen:
                seen.add(rel)
                selected.append(rel)
    else:
        selected = sorted(path[len(prefix):] for path in package_blobs)
        if len(selected) > args.max_files:
            print(f"FAIL usage: {len(selected)} files exceed --max-files {args.max_files}; use --path")
            print("RESULT CONTENT_ERROR")
            return finish(2)

    print(f"REPO_ROOT: {root}")
    print(f"PREFIX: {prefix or '(skill dir is repo root)'}")
    print(f"HEAD: {head}")
    print(f"HEAD_TIME: {head_iso or 'UNKNOWN'}")
    print(f"HEAD_SUBJECT: {head_subject}")

    if args.out:
        out_root = Path(args.out).expanduser().resolve()
    else:
        out_root = Path(tempfile.gettempdir()) / f"audit-head-content-{head[:12]}-{os.getpid()}"
    if (
        out_root == root
        or root in out_root.parents
        or out_root == skill_dir
        or skill_dir in out_root.parents
    ):
        print(f"FAIL usage: --out must be outside the repository and the Skill directory: {out_root}")
        print("RESULT CONTENT_ERROR")
        return finish(2)
    extract_root = out_root / skill_dir.name
    created_out = not out_root.exists()
    if extract_root.exists() and any(extract_root.iterdir()):
        print(f"FAIL usage: extraction directory is not empty: {extract_root}")
        print("RESULT CONTENT_ERROR")
        return finish(2)

    print(f"EXTRACT: {extract_root}")
    print(f"FILES: {len(selected)} (selected) | head_blobs={len(package_blobs)}")

    rows: list[dict[str, object]] = []
    structural_failures = 0
    warnings = 0
    equal = differ = missing = 0
    diff_files = 0

    try:
        extract_root.mkdir(parents=True, exist_ok=True)
        for rel in selected:
            repo_rel = prefix + rel
            oid = package_blobs[repo_rel]
            code, head_bytes, err = git.run(root, "cat-file", "blob", oid)
            if code != 0:
                print(f"FILE {rel} head={oid[:12]} EXTRACT_FAIL {err.decode('utf-8', 'replace').strip()}")
                structural_failures += 1
                continue

            target = extract_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(head_bytes)

            disk_path = skill_dir / rel
            disk_bytes: bytes | None = None
            if disk_path.is_file():
                try:
                    disk_bytes = disk_path.read_bytes()
                except OSError:
                    disk_bytes = None

            if disk_bytes is None:
                state = "MISSING_ON_DISK"
                missing += 1
            elif disk_bytes == head_bytes:
                state = "BYTES_EQUAL"
                equal += 1
            else:
                state = "BYTES_DIFFER"
                differ += 1

            checks, info = structural_audit(head_bytes, rel, skill_dir.name, args.strict_lf)
            file_failures = sum(1 for status, _ in checks if status == "FAIL")
            file_warnings = sum(1 for status, _ in checks if status == "WARN")
            structural_failures += file_failures
            warnings += file_warnings

            print("")
            print(
                f"FILE {rel} head={oid[:12]} bytes={len(head_bytes)} disk={state} "
                f"head_sha256={sha256_bytes(head_bytes)} "
                f"disk_sha256={sha256_bytes(disk_bytes) if disk_bytes is not None else '-'}"
            )
            if rel == "SKILL.md":
                print(
                    "  STRUCT "
                    f"name={info.get('name', '-')} dir_match={'yes' if info.get('name') == skill_dir.name else 'no'} "
                    f"desc_lines={info.get('desc_lines', '-')} desc_chars={info.get('desc_chars', '-')} "
                    f"body_lines={info.get('body_lines', '-')} "
                    f"h1={info.get('h1', '-')} h2={info.get('h2', '-')} h3={info.get('h3', '-')} "
                    f"fences={info.get('fences', '-')} checklist={info.get('checklist', '-')} "
                    f"tables={info.get('table_rows', '-')}"
                )
            crlf_count = head_bytes.count(b"\r\n")
            tab_lines = sum(1 for line in head_bytes.splitlines() if b"\t" in line)
            trailing_lines = sum(1 for line in head_bytes.splitlines() if line != line.rstrip())
            final_newline = "yes" if head_bytes.endswith(b"\n") else "no"
            print(
                "  BYTES "
                f"bom={'yes' if data_has_bom(head_bytes) else 'no'} "
                f"crlf={crlf_count} tabs={tab_lines} "
                f"trailing_ws={trailing_lines} final_newline={final_newline}"
            )
            for status, detail in checks:
                if status != "PASS":
                    print(f"  CHECK {status} {detail}")

            if state == "BYTES_DIFFER" and not args.no_diff:
                lines, total, kind = bounded_diff(
                    head_bytes, disk_bytes or b"", rel, args.context, args.max_diff_lines
                )
                if kind == "text":
                    diff_files += 1
                    print(f"  DIFF_LINES: {total}" + (" (truncated)" if total > args.max_diff_lines else ""))
                    for line in lines:
                        print(f"  {line.rstrip()}")
                else:
                    print(f"  DIFF SKIP ({kind})")

            rows.append(
                {
                    "rel": rel,
                    "oid": oid,
                    "state": state,
                    "failures": file_failures,
                    "warnings": file_warnings,
                }
            )

        extra: list[str] = []
        if not args.path:
            head_set = set(package_blobs)
            for rel in walk_disk(skill_dir):
                repo_rel = prefix + rel
                if repo_rel not in head_set:
                    extra.append(rel)
        for rel in extra:
            print(f"EXTRA_ON_DISK {rel}")

        print("")
        print(
            f"SUMMARY files={len(rows)} equal={equal} differ={differ} missing={missing} "
            f"extra={len(extra)} structural_fail={structural_failures} warnings={warnings}"
        )
        if structural_failures:
            print("VERDICT: CONTENT_FAIL")
            print("RESULT CONTENT_FAIL")
            return finish(1)
        if differ or missing:
            print("VERDICT: CONTENT_OK_DISK_DIFFERS")
            print("RESULT CONTENT_OK_DISK_DIFFERS")
            return finish(1)
        print("VERDICT: CONTENT_OK")
        print("RESULT CONTENT_OK")
        return finish(0)
    finally:
        if args.keep:
            print(f"KEPT: {extract_root}")
        else:
            shutil.rmtree(extract_root, ignore_errors=True)
            if created_out:
                shutil.rmtree(out_root, ignore_errors=True)
            print(f"CLEANED: {not extract_root.exists()}")


def data_has_bom(data: bytes) -> bool:
    return data.startswith(b"\xef\xbb\xbf")


if __name__ == "__main__":
    sys.exit(main())
