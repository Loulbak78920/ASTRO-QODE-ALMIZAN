#!/usr/bin/env python3
"""Read-only reconciliation between a Skill directory's HEAD tree and its worktree.

Never stages, commits, initializes, checks out, cleans, or deletes anything.
Uses plumbing commands only (no `git status` / `git diff`), so git's optional
index refresh is disabled (GIT_OPTIONAL_LOCKS=0). Snapshots `.git/index`
(size, mtime_ns, SHA-256) before and after, and prints `INDEX_UNCHANGED`.

Also reads the HEAD pointer (via `--git-path HEAD`), symbolic ref, target ref,
object type, tree, latest reflog entry, shallow state, and worktree list, and
prints an independent `HEAD_POINTER` verdict. Exit codes describe worktree
reconciliation only, except `HEAD_OBJECT_INVALID` which exits 1.

Exit codes: 0 reconciled, 1 not reconciled, 2 environment or usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CACHE_DIRS = {"__pycache__"}
CACHE_SUFFIXES = {".pyc", ".pyo"}
DEFAULT_MAX_DIVERGENT = 300
DEFAULT_MAX_IGNORED = 20

DIVERGENT_STATES = {
    "WORKTREE_ONLY",
    "STAGED_ONLY",
    "BOTH",
    "DELETED_ON_DISK",
    "DELETED_IN_INDEX",
    "UNTRACKED",
}


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def local_iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch).astimezone().isoformat(timespec="seconds")


def tz_iso(epoch: int, offset: str) -> str:
    try:
        sign = -1 if offset.startswith("-") else 1
        seconds = sign * (int(offset[1:3]) * 3600 + int(offset[3:5]) * 60)
        tz = timezone(timedelta(seconds=seconds))
    except (ValueError, IndexError):
        tz = timezone.utc
    return datetime.fromtimestamp(epoch, tz).isoformat(timespec="seconds")


def decode(raw: bytes) -> str:
    return raw.decode("utf-8", "replace")


class Git:
    def __init__(self) -> None:
        self.env = os.environ.copy()
        self.env["GIT_OPTIONAL_LOCKS"] = "0"
        self.env["GIT_TERMINAL_PROMPT"] = "0"
        self.env["GIT_PAGER"] = "cat"

    def run(self, cwd: Path, *args: str) -> tuple[int, bytes, bytes]:
        cmd = ["git", "--no-pager", "-C", str(cwd), *args]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,
                env=self.env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 128, b"", str(exc).encode("utf-8", "replace")
        return proc.returncode, proc.stdout, proc.stderr

    def text(self, cwd: Path, *args: str) -> tuple[int, str]:
        code, out, err = self.run(cwd, *args)
        return code, decode(out).strip() if code == 0 else decode(err).strip()

    def zlist(self, cwd: Path, *args: str) -> tuple[int, list[str]]:
        code, out, err = self.run(cwd, *args)
        if code != 0:
            return code, [decode(err).strip()]
        return 0, [decode(item) for item in out.split(b"\0") if item]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_index(git: Git, root: Path) -> dict[str, object]:
    code, path_text = git.text(root, "rev-parse", "--git-path", "index")
    if code != 0 or not path_text:
        return {"path": "", "exists": False}
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


def walk_package(skill_dir: Path) -> list[str]:
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


def parse_tree(git: Git, root: Path) -> tuple[dict[str, str], set[str]]:
    code, items = git.zlist(root, "ls-tree", "-r", "-z", "HEAD")
    if code != 0:
        return {}, set()
    tree: dict[str, str] = {}
    gitlinks: set[str] = set()
    for item in items:
        meta, _, path = item.partition("\t")
        parts = meta.split()
        if len(parts) != 3:
            continue
        if parts[1] == "blob":
            tree[path] = parts[2]
        elif parts[1] == "commit":
            gitlinks.add(path)
    return tree, gitlinks


def parse_index(git: Git, root: Path) -> tuple[dict[str, str], set[str]]:
    code, items = git.zlist(root, "ls-files", "-s", "-z")
    index: dict[str, str] = {}
    conflicts: set[str] = set()
    if code != 0:
        return index, conflicts
    for item in items:
        meta, _, path = item.partition("\t")
        parts = meta.split()
        if len(parts) != 3:
            continue
        stage = parts[2]
        if stage == "0":
            index[path] = parts[1]
        else:
            conflicts.add(path)
    return index, conflicts


def parse_eol(git: Git, root: Path) -> dict[str, str]:
    code, items = git.zlist(root, "ls-files", "-z", "--eol")
    eol: dict[str, str] = {}
    if code != 0:
        return eol
    for item in items:
        meta, _, path = item.partition("\t")
        eol[path] = " ".join(meta.split())
    return eol


def parse_reflog(git: Git, root: Path) -> tuple[str, str] | None:
    code, path_text = git.text(root, "rev-parse", "--git-path", "logs/HEAD")
    if code != 0 or not path_text:
        return None
    log_path = Path(path_text)
    if not log_path.is_absolute():
        log_path = root / log_path
    try:
        first = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return None
    head, _, message = first.partition("\t")
    parts = head.rsplit(" ", 2)
    if len(parts) != 3 or not parts[1].lstrip("-").isdigit():
        return None
    epoch = int(parts[1])
    return tz_iso(epoch, parts[2]), message.strip()


def collect_pointer(git: Git, root: Path, head: str | None) -> dict[str, object]:
    code, path_text = git.text(root, "rev-parse", "--git-path", "HEAD")
    head_file = ""
    head_content = ""
    if code == 0 and path_text:
        head_path = Path(path_text)
        if not head_path.is_absolute():
            head_path = root / head_path
        head_file = str(head_path)
        try:
            head_content = head_path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            head_content = ""

    code, symbolic_text = git.text(root, "symbolic-ref", "-q", "HEAD")
    symbolic = symbolic_text if code == 0 and symbolic_text else ""
    target_oid = ""
    target_status = "-"
    if symbolic:
        code, target_text = git.text(root, "rev-parse", "--verify", f"{symbolic}^{{commit}}")
        if not head:
            target_status = "UNBORN"
        elif code != 0 or not target_text:
            target_status = "MISSING"
        else:
            target_oid = target_text
            target_status = "MATCH" if target_oid == head else "MISMATCH"

    object_type = "UNRESOLVED"
    tree = ""
    tree_entries = 0
    if head:
        code, type_text = git.text(root, "cat-file", "-t", head)
        if code == 0 and type_text:
            object_type = type_text
        if object_type == "commit":
            code, tree_text = git.text(root, "rev-parse", f"{head}^{{tree}}")
            if code == 0 and tree_text:
                tree = tree_text
                code, items = git.zlist(root, "ls-tree", "-r", "-z", head)
                tree_entries = len(items) if code == 0 else 0

    reflog_selector = ""
    reflog_oid = ""
    reflog_message = ""
    reflog_match: bool | None = None
    code, reflog_text = git.text(root, "reflog", "-1", "--format=%H%x1f%gd%x1f%gs", "HEAD")
    if code == 0 and reflog_text:
        fields = reflog_text.split("\x1f")
        if len(fields) >= 3:
            reflog_oid, reflog_selector, reflog_message = fields[0], fields[1], fields[2]
            if head:
                reflog_match = reflog_oid == head

    shallow = "unknown"
    code, shallow_text = git.text(root, "rev-parse", "--is-shallow-repository")
    if code == 0 and shallow_text in ("true", "false"):
        shallow = shallow_text

    worktrees: list[str] = []
    code, worktree_text = git.text(root, "worktree", "list", "--porcelain")
    if code == 0:
        for line in worktree_text.splitlines():
            if line.startswith("worktree "):
                worktrees.append(line[len("worktree "):])

    if not head:
        verdict = "UNBORN" if symbolic else "UNRESOLVED"
    elif object_type != "commit":
        verdict = "OBJECT_INVALID"
    elif not symbolic:
        verdict = "DETACHED"
    elif target_status in ("MISSING", "MISMATCH"):
        verdict = "REF_MISMATCH"
    else:
        verdict = "OK"

    return {
        "head_file": head_file,
        "head_content": head_content,
        "symbolic": symbolic,
        "target_oid": target_oid,
        "target_status": target_status,
        "object_type": object_type,
        "tree": tree,
        "tree_entries": tree_entries,
        "reflog_selector": reflog_selector,
        "reflog_oid": reflog_oid,
        "reflog_message": reflog_message,
        "reflog_match": reflog_match,
        "shallow": shallow,
        "worktrees": worktrees,
        "verdict": verdict,
    }


def print_pointer(pointer: dict[str, object], root: Path) -> None:
    print(f"POINTER_HEAD_FILE: {pointer['head_file'] or '(unresolved)'}")
    print(f"POINTER_HEAD_CONTENT: {pointer['head_content'] or '(empty)'}")
    print(f"POINTER_SYMBOLIC_REF: {pointer['symbolic'] or 'DETACHED'}")
    if pointer["symbolic"]:
        target = str(pointer["target_oid"])[:12] or "-"
        print(f"POINTER_TARGET: {pointer['symbolic']} {target} {pointer['target_status']}")
    else:
        print("POINTER_TARGET: - (detached)")
    print(f"POINTER_OBJECT: {pointer['object_type']}")
    print(f"POINTER_TREE: {pointer['tree'] or '-'} entries={pointer['tree_entries']}")
    if pointer["reflog_selector"]:
        match = "UNKNOWN" if pointer["reflog_match"] is None else (
            "MATCH" if pointer["reflog_match"] else "MISMATCH"
        )
        print(
            f"POINTER_REFLOG_LATEST: {pointer['reflog_selector']} "
            f"{str(pointer['reflog_oid'])[:12]} {match} {pointer['reflog_message']}"
        )
    else:
        print("POINTER_REFLOG_LATEST: unavailable")
    print(f"POINTER_SHALLOW: {pointer['shallow']}")
    worktrees = [str(item) for item in pointer["worktrees"]] if isinstance(pointer["worktrees"], list) else []
    marked = []
    for path in worktrees:
        try:
            current = Path(path).resolve() == root
        except OSError:
            current = False
        marked.append(path + (" (current)" if current else ""))
    print(f"POINTER_WORKTREES: {len(worktrees)}" + (f" [{' ; '.join(marked)}]" if marked else ""))
    print(f"HEAD_POINTER: {pointer['verdict']}")


def classify(
    head_oid: str | None,
    index_oid: str | None,
    work_oid: str | None,
    on_disk: bool,
) -> tuple[str, str]:
    if head_oid:
        if not on_disk:
            if index_oid is None:
                return "DELETED_ON_DISK", "staged deletion"
            if index_oid == head_oid:
                return "DELETED_ON_DISK", "unstaged deletion"
            return "DELETED_ON_DISK", "edited then deleted"
        if index_oid is None:
            return "DELETED_IN_INDEX", "staged deletion but file exists on disk"
        if work_oid == head_oid and index_oid == head_oid:
            return "SAME", ""
        if work_oid != head_oid and index_oid == head_oid:
            return "WORKTREE_ONLY", "unstaged edit"
        if work_oid == head_oid and index_oid != head_oid:
            return "STAGED_ONLY", "staged edit, worktree matches HEAD"
        if work_oid == index_oid:
            return "STAGED_ONLY", "staged edit, worktree matches index"
        return "BOTH", "staged and unstaged edits"
    if not on_disk:
        return "DELETED_ON_DISK", "path tracked in index but absent in HEAD and on disk"
    if index_oid:
        if work_oid == index_oid:
            return "STAGED_ONLY", "new file staged"
        return "BOTH", "new file staged and edited"
    return "UNTRACKED", "not in HEAD, not in index"


def describe_head(row: dict[str, object], expected: str) -> str:
    head = str(row["head"])
    if not head:
        return "NOT_AT_HEAD (path absent from HEAD tree)"
    if row["head_sha"] == expected:
        return f"HEAD_MATCH_BYTES (head={head[:12]})"
    return f"HEAD_MISMATCH (head={head[:12]} blob_sha256={row['head_sha']})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only HEAD vs worktree reconciliation for a Skill directory.",
    )
    parser.add_argument("skill_dir", help="absolute path of the Skill directory")
    parser.add_argument(
        "--expect-sha256",
        action="append",
        default=[],
        metavar="REL=HEX64",
        help="bind a recorded worktree SHA-256 (e.g. from skill-file-qa) to HEAD; repeatable, path relative to the Skill directory",
    )
    parser.add_argument("--verbose", action="store_true", help="list reconciled files too")
    parser.add_argument("--max-divergent", type=int, default=DEFAULT_MAX_DIVERGENT)
    parser.add_argument("--max-ignored", type=int, default=DEFAULT_MAX_IGNORED)
    args = parser.parse_args(argv)

    configure_stdout()

    if shutil.which("git") is None:
        print("FAIL environment: git not found in PATH")
        print("RESULT FAIL")
        return 2

    skill_dir = Path(args.skill_dir).expanduser()
    if not skill_dir.is_dir():
        print(f"FAIL usage: not a directory: {skill_dir}")
        print("RESULT FAIL")
        return 2
    skill_dir = skill_dir.resolve()

    expects: list[tuple[str, str]] = []
    for raw in args.expect_sha256:
        rel, sep, value = raw.partition("=")
        value = value.strip().lower()
        if not sep or not rel or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            print(f"FAIL usage: --expect-sha256 needs REL=64-hex, got {raw!r}")
            print("RESULT FAIL")
            return 2
        rel = rel.replace("\\", "/").strip("/")
        while rel.startswith("./"):
            rel = rel[2:]
        expects.append((rel, value))
    if args.max_divergent < 1 or args.max_ignored < 0:
        print("FAIL usage: --max-divergent must be >= 1 and --max-ignored >= 0")
        print("RESULT FAIL")
        return 2

    git = Git()
    print(f"SKILL_DIR: {skill_dir}")

    code, root_text = git.text(skill_dir, "rev-parse", "--show-toplevel")
    if code != 0 or not root_text:
        print("VERDICT: NO_REPO")
        print(f"NOTE: git rev-parse failed with exit {code}: {root_text}")
        print("NOTE: this directory is not covered by a Git worktree; nothing can be reconciled")
        print("RESULT NO_REPO")
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

    code, git_dir_text = git.text(skill_dir, "rev-parse", "--absolute-git-dir")
    git_dir = Path(git_dir_text).resolve() if code == 0 and git_dir_text else Path()
    dot_git = root / ".git"
    if dot_git.is_file():
        kind = "file (linked worktree/submodule)"
    elif dot_git.is_dir():
        kind = "dir"
    else:
        kind = "absent at root"

    code, prefix_text = git.text(skill_dir, "rev-parse", "--show-prefix")
    prefix = (prefix_text if code == 0 else "").replace("\\", "/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    print(f"REPO_ROOT: {root}")
    print(f"PREFIX: {prefix or '(skill dir is repo root)'}")
    print(f"GIT_DIR: {git_dir} [{kind}]")

    code, branch = git.text(root, "rev-parse", "--abbrev-ref", "HEAD")
    print(f"BRANCH: {branch if code == 0 else 'UNKNOWN'}")

    code, head_text = git.text(root, "rev-parse", "HEAD")
    head_value = head_text if code == 0 and head_text else None
    pointer = collect_pointer(git, root, head_value)
    if head_value:
        print(f"HEAD: {head_value}")
    print_pointer(pointer, root)
    if not head_value:
        print("VERDICT: NO_COMMITS")
        print("NOTE: repository exists but HEAD has no commit; every package file is uncommitted")
        for rel in walk_package(skill_dir):
            print(f"UNTRACKED {rel} (no HEAD)")
        print("RESULT NO_COMMITS")
        return finish(1)
    head = head_value
    if pointer["verdict"] == "OBJECT_INVALID":
        print("VERDICT: HEAD_OBJECT_INVALID")
        print("NOTE: HEAD does not resolve to a commit; tree/index reconciliation is not trustworthy")
        print("RESULT DIVERGES")
        return finish(1)

    code, meta = git.text(root, "log", "-1", "--format=%H%x1f%cI%x1f%ct%x1f%s")
    subject = ""
    head_iso = ""
    head_epoch = 0
    if code == 0:
        fields = meta.split("\x1f")
        if len(fields) >= 4:
            head_iso, subject = fields[1], fields[3]
            try:
                head_epoch = int(fields[2])
            except ValueError:
                head_epoch = 0
    print(f"HEAD_TIME: {head_iso or 'UNKNOWN'}")
    print(f"HEAD_SUBJECT: {subject}")

    code, root_commit = git.text(root, "rev-list", "--max-parents=0", "HEAD")
    roots = root_commit.splitlines() if code == 0 else []
    print(f"ROOT_COMMIT: {roots[0] if roots else 'UNKNOWN'}" + (f" (+{len(roots) - 1} more)" if len(roots) > 1 else ""))
    if roots:
        code, root_iso = git.text(root, "log", "-1", "--format=%cI", roots[0])
        if code == 0:
            print(f"ROOT_COMMIT_TIME: {root_iso}")

    reflog = parse_reflog(git, root)
    if reflog:
        print(f"REFLOG_FIRST: {reflog[0]} ({reflog[1] or 'no message'})")
    else:
        print("REFLOG_FIRST: unavailable")

    if git_dir and (git_dir / "HEAD").exists():
        try:
            created = (git_dir / "HEAD").stat().st_ctime
            print(f"REPO_CREATED_HINT: {local_iso(created)} (.git/HEAD ctime; Windows=creation, POSIX=inode change)")
        except OSError:
            pass

    code, config = git.text(root, "config", "--show-origin", "--get-all", "core.autocrlf")
    config_lines = [line for line in config.splitlines() if line.strip()] if code == 0 else []
    effective_autocrlf = ""
    if config_lines:
        effective_autocrlf = config_lines[-1].partition("\t")[2].strip().lower()
        for line in config_lines:
            print(f"AUTOCRLF: {line.replace(chr(9), '=')}")
    else:
        print("AUTOCRLF: unset (no line from --show-origin)")

    tree, gitlinks = parse_tree(git, root)
    index, conflicts = parse_index(git, root)
    eol = parse_eol(git, root)
    code, untracked_paths = git.zlist(root, "ls-files", "-o", "--exclude-standard", "-z")
    untracked = set(untracked_paths) if code == 0 else set()
    code, ignored_paths = git.zlist(root, "ls-files", "-o", "-i", "--exclude-standard", "-z")
    ignored = set(ignored_paths) if code == 0 else set()

    tree_pkg = {path: oid for path, oid in tree.items() if path.startswith(prefix)}
    gitlinks_pkg = {path for path in gitlinks if path.startswith(prefix)}
    index_pkg = {path: oid for path, oid in index.items() if path.startswith(prefix)}
    untracked_pkg = {path for path in untracked if path.startswith(prefix)}
    ignored_pkg = {path for path in ignored if path.startswith(prefix)}
    conflicts_pkg = {path for path in conflicts if path.startswith(prefix)}

    disk = walk_package(skill_dir)
    all_paths = sorted(
        {prefix + rel for rel in disk} | set(tree_pkg) | set(index_pkg) | untracked_pkg,
    )

    rows: list[dict[str, object]] = []
    newest_mtime = 0.0
    for repo_rel in all_paths:
        rel = repo_rel[len(prefix):] if prefix else repo_rel
        path = skill_dir / rel
        on_disk = path.is_file()
        work_oid = None
        disk_sha = ""
        mtime = 0.0
        if on_disk:
            code, oid = git.text(root, "hash-object", f"--path={repo_rel}", str(path))
            work_oid = oid if code == 0 else None
            disk_sha = sha256_file(path)
            try:
                mtime = path.stat().st_mtime
            except OSError:
                mtime = 0.0
            newest_mtime = max(newest_mtime, mtime)
        head_oid = tree_pkg.get(repo_rel)
        index_oid = index_pkg.get(repo_rel)
        state, detail = classify(head_oid, index_oid, work_oid, on_disk)
        if repo_rel in conflicts_pkg:
            state, detail = "CONFLICT", "unmerged index entry"
        head_bytes_sha = ""
        if head_oid:
            code, blob, _ = git.run(root, "cat-file", "blob", head_oid)
            if code == 0:
                head_bytes_sha = hashlib.sha256(blob).hexdigest()
        rows.append(
            {
                "rel": rel,
                "repo_rel": repo_rel,
                "state": state,
                "detail": detail,
                "head": head_oid or "",
                "index": index_oid or "",
                "work": work_oid or "",
                "disk_sha": disk_sha,
                "head_sha": head_bytes_sha,
                "on_disk": on_disk,
                "mtime": mtime,
                "eol": eol.get(repo_rel, ""),
                "ignored": repo_rel in ignored_pkg,
            }
        )

    divergent = [row for row in rows if row["state"] in DIVERGENT_STATES or row["state"] == "CONFLICT"]
    same = [row for row in rows if row["state"] == "SAME"]

    print("")
    print(f"FILES: {len(rows)} (head={len(tree_pkg)}, index={len(index_pkg)}, disk={len(disk)})")
    print(f"DIVERGENT: {len(divergent)}  RECONCILED_FILES: {len(same)}  IGNORED: {len(ignored_pkg)}")
    if conflicts_pkg:
        print(f"CONFLICTS: {len(conflicts_pkg)}")

    for row in divergent[: args.max_divergent]:
        print(
            f"{row['state']} {row['rel']} head={row['head'][:12] or '-'} "
            f"index={row['index'][:12] or '-'} work={row['work'][:12] or '-'}"
        )
        print(
            f"  detail={row['detail']} on_disk={row['on_disk']} "
            f"disk_sha256={row['disk_sha'] or '-'} head_sha256={row['head_sha'] or '-'} "
            f"eol={row['eol'] or '-'} mtime={local_iso(row['mtime']) if row['mtime'] else '-'}"
        )
    if len(divergent) > args.max_divergent:
        print(f"... ({len(divergent) - args.max_divergent} more divergent files)")

    if args.verbose:
        for row in same:
            note = " (byte-diff vs blob)" if row["head_sha"] and row["disk_sha"] and row["head_sha"] != row["disk_sha"] else ""
            print(
                f"SAME {row['rel']} head={row['head'][:12]} work={row['work'][:12]} "
                f"disk_sha256={row['disk_sha']} eol={row['eol'] or '-'}{note}"
            )

    if ignored_pkg:
        for path in sorted(ignored_pkg)[: args.max_ignored]:
            print(f"IGNORED {path[len(prefix):] if prefix else path}")
        if len(ignored_pkg) > args.max_ignored:
            print(f"... ({len(ignored_pkg) - args.max_ignored} more ignored files)")

    if gitlinks_pkg:
        for path in sorted(gitlinks_pkg):
            print(f"NOTE gitlink: {path[len(prefix):] if prefix else path} (submodule; not reconciled)")

    expect_failures = 0
    if expects:
        print("")
        by_rel = {row["rel"]: row for row in rows}
        by_repo = {row["repo_rel"]: row for row in rows}
        for rel, expected in expects:
            row = by_rel.get(rel) or by_repo.get(rel)
            if row is None:
                print(f"EXPECT {rel}: UNKNOWN_FILE (not part of this Skill package)")
                expect_failures += 1
                continue
            if not row["on_disk"]:
                print(f"EXPECT {rel}: FILE_MISSING")
                print(f"  HEAD: {describe_head(row, expected)}")
                expect_failures += 1
                continue
            if row["disk_sha"] != expected:
                print(
                    f"EXPECT {rel}: DISK_CHANGED_SINCE_EXPECT "
                    f"expected={expected} disk={row['disk_sha']}"
                )
                print(f"  HEAD: {describe_head(row, expected)}")
                expect_failures += 1
                continue
            if not row["head"]:
                print(f"EXPECT {rel}: NOT_AT_HEAD (path absent from HEAD tree)")
                expect_failures += 1
                continue
            if row["work"] == row["head"]:
                if row["head_sha"] == expected:
                    print(f"EXPECT {rel}: MATCH_BYTES (HEAD blob bytes == recorded SHA-256)")
                else:
                    print(
                        f"EXPECT {rel}: MATCH_CONTENT_EOL_DIFF "
                        f"content_oid={row['work'][:12]} blob_sha256={row['head_sha']}"
                    )
            else:
                print(
                    f"EXPECT {rel}: NOT_AT_HEAD "
                    f"work={row['work'][:12]} head={row['head'][:12]}"
                )
                expect_failures += 1

    flags: list[str] = []
    if divergent and head_epoch and newest_mtime and head_epoch < newest_mtime:
        flags.append("HEAD_PREDATES_DISK (HEAD commit is older than the newest package file: edits are uncommitted)")
    if divergent and head_epoch and newest_mtime and head_epoch > newest_mtime:
        flags.append("HEAD_POSTDATES_DISK (HEAD commit is newer than the newest package file: worktree may have been checked out or reset to older bytes)")
    if any(row["state"] == "SAME" and row["head_sha"] and row["disk_sha"] and row["head_sha"] != row["disk_sha"] for row in rows):
        flags.append("EOL_BYTE_DIFF (content OIDs match but blob and worktree bytes differ; checkout normalization)")
    if effective_autocrlf == "true":
        flags.append("AUTOCRLF_TRUE (the effective core.autocrlf may rewrite line endings on checkout)")
    if ignored_pkg:
        flags.append("IGNORED_PRESENT (ignored files only; see skill-package-integrity-audit)")
    if pointer["verdict"] == "DETACHED":
        flags.append("HEAD_DETACHED (HEAD is not on a branch; content reconciliation still applies)")
    if pointer["shallow"] == "true":
        flags.append("SHALLOW_REPO (root commit and history are incomplete)")
    if pointer["reflog_match"] is False:
        flags.append("REFLOG_LATEST_MISMATCH (latest reflog entry does not equal HEAD)")
    if not pointer["reflog_selector"]:
        flags.append("REFLOG_UNAVAILABLE (reflog missing, disabled, or unreadable)")
    if pointer["target_status"] == "MISMATCH":
        flags.append("HEAD_REF_MISMATCH (HEAD differs from its symbolic target)")
    if isinstance(pointer["worktrees"], list) and len(pointer["worktrees"]) > 1:
        flags.append("MULTIPLE_WORKTREES (verify which worktree this index belongs to)")

    print("")
    if flags:
        for flag in flags:
            print(f"FLAG: {flag}")
    else:
        print("FLAG: NONE")

    if divergent or conflicts_pkg:
        worktree_states = {"WORKTREE_ONLY", "BOTH", "DELETED_ON_DISK", "DELETED_IN_INDEX", "CONFLICT"}
        if any(row["state"] in worktree_states for row in divergent):
            verdict = "WORKTREE_DIVERGES"
        elif any(row["state"] == "STAGED_ONLY" for row in divergent):
            verdict = "STAGED_ONLY"
        else:
            verdict = "UNTRACKED_PRESENT"
        if expect_failures:
            verdict += "+EXPECT_MISMATCH"
        if gitlinks_pkg:
            verdict += "+GITLINK_UNSUPPORTED"
        print(f"VERDICT: {verdict}")
        print("RESULT DIVERGES")
        return finish(1)

    if expect_failures:
        verdict = "EXPECT_MISMATCH"
        if gitlinks_pkg:
            verdict += "+GITLINK_UNSUPPORTED"
        print(f"VERDICT: {verdict}")
        print("RESULT DIVERGES")
        return finish(1)

    if gitlinks_pkg:
        print("VERDICT: GITLINK_UNSUPPORTED")
        print("RESULT UNSUPPORTED")
        return finish(1)

    print("VERDICT: RECONCILED")
    print("RESULT RECONCILED")
    return finish(0)


if __name__ == "__main__":
    sys.exit(main())
