#!/usr/bin/env python3
"""Static checks for a skill package; never executes the skill's code."""
from __future__ import annotations

import argparse
import ast
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import NamedTuple
from urllib.parse import unquote

try:
    import yaml
except ImportError:
    yaml = None

NAME_RE = re.compile(r"^[a-z0-9-]+$")
TODO_MARKER_RE = re.compile(
    r"(?im)^\s*(?:#|//|<!--|;|\*)?\s*(?:[-*+]\s+)?TODO\b|\bTODO\s*[:(]"
)
FENCE_RE = re.compile(r"^\s*```\s*([^\s`]*)")
FENCE_END_RE = re.compile(r"^\s*```\s*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SPAN_RE = re.compile(r"`([^`\n]+)`")
PY_LANGS = {"python", "py"}
JS_LANGS = {"js", "javascript", "mjs", "cjs"}
RESOURCE_PREFIXES = ("scripts/", "references/", "assets/")
ALLOWED_DIRS = {"scripts", "references", "assets"}
ALLOWED_ROOT_FILES = {"SKILL.md", ".gitattributes"}
PROHIBITED_DOCS = {"README.md", "CHANGELOG.md", "INSTALLATION_GUIDE.md"}
KNOWN_EXTS = {
    ".py", ".js", ".cjs", ".mjs", ".ts", ".tsx", ".json", ".yaml", ".yml",
    ".md", ".txt", ".csv", ".html", ".htm", ".sh", ".ps1", ".bat", ".toml",
}


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


class Fingerprint(NamedTuple):
    size: int
    mtime_ns: int
    sha256: str


class RefsFingerprint(NamedTuple):
    count: int
    sha256: str


class StabilityError(RuntimeError):
    pass


def format_mtime(mtime_ns: int) -> str:
    try:
        return datetime.fromtimestamp(mtime_ns / 1_000_000_000).astimezone().isoformat(
            timespec="seconds"
        )
    except (OSError, OverflowError, ValueError):
        return f"{mtime_ns}ns"


def format_fingerprint(fp: Fingerprint) -> str:
    return f"{fp.size} bytes | mtime={format_mtime(fp.mtime_ns)} | sha256={fp.sha256}"


def format_refs_fingerprint(fp: RefsFingerprint) -> str:
    return f"{fp.count} file(s) | sha256={fp.sha256}"


def snapshot(path: Path) -> tuple[Fingerprint, bytes] | None:
    before = path.stat()
    data = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        return None
    return Fingerprint(len(data), after.st_mtime_ns, hashlib.sha256(data).hexdigest()), data


def list_reference_files(skill_dir: Path) -> list[Path]:
    refs_dir = skill_dir / "references"
    if not refs_dir.is_dir():
        return []
    files = []
    for path in refs_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir)
        if ".git" in rel.parts or "__pycache__" in rel.parts:
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(skill_dir).as_posix())


def snapshot_refs(skill_dir: Path) -> RefsFingerprint | None:
    entries = []
    for path in list_reference_files(skill_dir):
        snap = snapshot(path)
        if snap is None:
            return None
        fp, _ = snap
        rel = path.relative_to(skill_dir).as_posix()
        entries.append(f"{rel}\0{fp.size}\0{fp.sha256}\n")
    digest = hashlib.sha256("".join(entries).encode("utf-8")).hexdigest()
    return RefsFingerprint(len(entries), digest)


def wait_for_stable(
    skill_dir: Path, window: float, timeout: float
) -> tuple[Fingerprint, RefsFingerprint, bytes, float]:
    skill_md = skill_dir / "SKILL.md"
    started = time.monotonic()
    last = None
    stable_since = started
    while True:
        try:
            snap = snapshot(skill_md)
            refs = snapshot_refs(skill_dir)
        except OSError as exc:
            raise StabilityError(f"cannot read SKILL.md or references/: {exc}") from exc
        now = time.monotonic()
        if snap is None or refs is None:
            last = None
            stable_since = now
        else:
            fp, data = snap
            current = (fp, refs)
            if last is None or current != last:
                last = current
                stable_since = now
            elif window == 0 or now - stable_since >= window:
                return fp, refs, data, now - started
        if now - started > timeout:
            detail = (
                "last snapshot was unstable"
                if last is None
                else f"last sha256={last[0].sha256[:12]}..., "
                f"references sha256={last[1].sha256[:12]}..."
            )
            raise StabilityError(
                f"SKILL.md and references/ did not remain unchanged for {window:.1f}s "
                f"within {timeout:.1f}s ({detail})"
            )
        time.sleep(min(0.2, max(0.02, timeout - (now - started))))


class Reporter:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.warned = 0

    def _line(self, level: str, message: str) -> None:
        print(f"{level:<4} {ascii_text(message)}")

    def ok(self, message: str) -> None:
        self.passed += 1
        self._line("PASS", message)

    def fail(self, message: str) -> None:
        self.failed += 1
        self._line("FAIL", message)

    def warn(self, message: str) -> None:
        self.warned += 1
        self._line("WARN", message)


def split_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None, None, "SKILL.md must start with a '---' frontmatter line"
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return None, None, None, "frontmatter closing '---' not found"
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1:]), end + 2, None


def description_line_span(frontmatter: str) -> int | None:
    try:
        node = yaml.compose(frontmatter)
    except yaml.YAMLError:
        return None
    if not isinstance(node, yaml.MappingNode):
        return None
    for key_node, value_node in node.value:
        if isinstance(key_node, yaml.ScalarNode) and key_node.value == "description":
            return value_node.end_mark.line - value_node.start_mark.line + 1
    return None


def list_files(skill_dir: Path) -> list[str]:
    files = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir)
        if ".git" in rel.parts:
            continue
        files.append(rel.as_posix())
    return sorted(files)


def check_layout(files: list[str], report: Reporter) -> None:
    bad_doc = False
    for rel in files:
        if rel in ALLOWED_ROOT_FILES:
            continue
        parts = rel.split("/")
        if len(parts) > 1 and parts[0] in ALLOWED_DIRS:
            continue
        if len(parts) == 1 and parts[0] in PROHIBITED_DOCS:
            report.fail(f"layout: extraneous documentation '{rel}'")
            bad_doc = True
        else:
            report.warn(f"layout: unexpected file '{rel}'")
    if not bad_doc:
        report.ok(f"layout: {len(files)} file(s), no extraneous documentation")


def normalize_ref(raw: str) -> str | None:
    ref = raw.strip()
    if ref.startswith("<") and ref.endswith(">"):
        ref = ref[1:-1]
    if not ref or "://" in ref or ref.startswith(("#", "mailto:")):
        return None
    ref = ref.split("#", 1)[0]
    ref = re.sub(r":\d+(?:-\d+)?$", "", ref)
    ref = unquote(ref).strip().rstrip(".,;")
    while ref.startswith("./"):
        ref = ref[2:]
    if not ref or ref.startswith(("/", "~", "$", "..")):
        return None
    if re.match(r"^[A-Za-z]:", ref):
        return None
    return ref


def looks_like_inline_ref(token: str) -> bool:
    if not token or any(ch.isspace() or ch in "<>{}*?=" for ch in token) or "#" in token:
        return False
    ref = normalize_ref(token)
    if ref is None:
        return False
    if ref.startswith(RESOURCE_PREFIXES):
        return True
    return "/" in ref and Path(ref).suffix.lower() in KNOWN_EXTS


def collect_refs(text: str) -> list[str]:
    refs = set()
    for raw in LINK_RE.findall(text):
        token = raw.split()[0] if raw.split() else raw
        ref = normalize_ref(token)
        if ref:
            refs.add(ref)
    for raw in SPAN_RE.findall(text):
        if looks_like_inline_ref(raw):
            ref = normalize_ref(raw)
            if ref:
                refs.add(ref)
    return sorted(refs)


def check_refs(skill_dir: Path, workspace: Path, text: str, report: Reporter) -> None:
    refs = collect_refs(text)
    missing = []
    for ref in refs:
        candidates = [skill_dir / ref, workspace / ref]
        if not any(candidate.exists() for candidate in candidates):
            missing.append(ref)
    for ref in missing:
        report.fail(f"local reference not found: '{ref}'")
    if not missing:
        report.ok(f"local references: {len(refs)} checked")


def strip_fenced_blocks(text: str) -> str:
    kept = []
    in_block = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_block = not in_block
            continue
        if not in_block:
            kept.append(line)
    return "\n".join(kept)


def build_skill_registry(roots: list[Path]) -> dict[str, list[Path]]:
    registry: dict[str, list[Path]] = {}
    for root in roots:
        for child in sorted(root.iterdir()):
            if child.is_dir() and NAME_RE.fullmatch(child.name):
                registry.setdefault(child.name, []).append(child)
    return registry


def collect_skill_refs(
    text: str, registry: dict[str, list[Path]], self_name: str
) -> dict[str, list[Path]]:
    refs: dict[str, list[Path]] = {}
    for raw in SPAN_RE.findall(strip_fenced_blocks(text)):
        name = raw.strip()
        if name == self_name or name not in registry:
            continue
        refs[name] = registry[name]
    return refs


def summarize_names(names: list[str], limit: int = 3) -> str:
    ordered = sorted(names)
    shown = ", ".join(ordered[:limit])
    if len(ordered) > limit:
        shown += f", +{len(ordered) - limit}"
    return shown


def check_skill_refs(
    text: str, roots: list[Path], self_name: str, report: Reporter
) -> None:
    if not roots:
        report.warn("skill references: no local skill roots found; not checked")
        return
    refs = collect_skill_refs(text, build_skill_registry(roots), self_name)
    if not refs:
        report.ok("skill references: 0 found (no installed skill names in backticks)")
        return
    missing = []
    for name, paths in sorted(refs.items()):
        if any((path / "SKILL.md").is_file() for path in paths):
            continue
        missing.append(name)
    resolved = [name for name in refs if name not in missing]
    for name in missing:
        locations = "; ".join(ascii_text(path) for path in refs[name])
        report.fail(f"skill reference '{name}': SKILL.md missing in {locations}")
    if missing:
        if resolved:
            report.ok(
                f"skill references: {len(resolved)} resolved of {len(refs)} "
                f"({summarize_names(resolved)})"
            )
    else:
        report.ok(f"skill references: {len(refs)} checked ({summarize_names(resolved)})")


def extract_blocks(text: str):
    blocks = []
    unterminated = None
    lines = text.splitlines()
    in_block = False
    lang = ""
    start = 0
    buffer = []
    for lineno, line in enumerate(lines, 1):
        if not in_block:
            match = FENCE_RE.match(line)
            if match:
                in_block = True
                lang = (match.group(1) or "").strip().lower()
                start = lineno
                buffer = []
        elif FENCE_END_RE.match(line):
            blocks.append((lang, start, "\n".join(buffer)))
            in_block = False
        else:
            buffer.append(line)
    if in_block:
        unterminated = start
    return blocks, unterminated


def run_node_check(node: str, path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [node, "--check", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )


def check_js(code: str, node: str) -> str | None:
    with tempfile.TemporaryDirectory(prefix="skill-file-qa-") as temp_dir:
        path = Path(temp_dir) / "block.js"
        path.write_text(code + ("\n" if not code.endswith("\n") else ""), encoding="utf-8")
        result = run_node_check(node, path)
        if result.returncode == 0:
            return None
        wrapped = "const __skillFileQa = (\n" + code + "\n);\n"
        path.write_text(wrapped, encoding="utf-8")
        wrapped_result = run_node_check(node, path)
        if wrapped_result.returncode == 0:
            return None
        error = (wrapped_result.stderr or wrapped_result.stdout or "node --check failed").strip()
        return " | ".join(error.splitlines()[:3])[:500]


def finish_fingerprint(
    skill_dir: Path,
    start_fp: Fingerprint,
    start_refs: RefsFingerprint,
    report: Reporter,
) -> None:
    try:
        snap = snapshot(skill_dir / "SKILL.md")
        refs = snapshot_refs(skill_dir)
    except OSError as exc:
        report.fail(
            "fingerprint: cannot re-read SKILL.md or references/ after validation "
            f"({ascii_text(exc)})"
        )
        return
    if snap is None or refs is None:
        report.fail("fingerprint: files were being modified at the end of validation; rerun")
        return
    final_fp, _ = snap
    print(f"Fingerprint (final): {ascii_text(format_fingerprint(final_fp))}")
    print(f"References fingerprint (final): {ascii_text(format_refs_fingerprint(refs))}")
    changed = False
    if final_fp.sha256 != start_fp.sha256 or final_fp.size != start_fp.size:
        report.fail("fingerprint: SKILL.md changed during validation; rerun on the stable version")
        changed = True
    if refs != start_refs:
        report.fail("fingerprint: references/ changed during validation; rerun on the stable version")
        changed = True
    if not changed:
        report.ok("fingerprint: SKILL.md and references/ unchanged during validation")


def validate(
    skill_dir: Path,
    workspace: Path,
    skill_roots: list[Path],
    raw: bytes,
    start_fp: Fingerprint,
    start_refs: RefsFingerprint,
    stability_text: str,
) -> int:
    report = Reporter()
    print("Validator: read-only (skill files are not modified)")
    print(f"Stability: {ascii_text(stability_text)}")
    print(f"Fingerprint (start): {ascii_text(format_fingerprint(start_fp))}")
    print(f"References fingerprint (start): {ascii_text(format_refs_fingerprint(start_refs))}")
    if raw.startswith(b"\xef\xbb\xbf"):
        report.fail("frontmatter: SKILL.md starts with a UTF-8 BOM; frontmatter detection may fail")
        text = raw.decode("utf-8-sig")
    else:
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            print(f"FAIL  encoding: SKILL.md is not valid UTF-8 ({ascii_text(exc)})")
            finish_fingerprint(skill_dir, start_fp, start_refs, report)
            print("RESULT FAIL")
            return 1

    files = list_files(skill_dir)
    shown = ", ".join(files[:10])
    if len(files) > 10:
        shown += f", ... (+{len(files) - 10})"
    print(f"Skill: {ascii_text(skill_dir.name)}")
    print(f"Files ({len(files)}): {ascii_text(shown)}")
    roots_shown = "; ".join(ascii_text(root) for root in skill_roots) if skill_roots else "none"
    print(f"Skill roots ({len(skill_roots)}): {roots_shown}")
    check_layout(files, report)

    frontmatter, body, _body_start, frontmatter_error = split_frontmatter(text)
    metadata = None
    if frontmatter_error:
        report.fail(f"frontmatter: {frontmatter_error}")
    elif yaml is None:
        report.fail("frontmatter: PyYAML is not installed; run 'py -3 -m pip install pyyaml'")
    else:
        try:
            metadata = yaml.safe_load(frontmatter)
        except yaml.YAMLError as exc:
            detail = " | ".join(ascii_text(exc).splitlines()[:4])[:600]
            hint = ""
            if "mapping values are not allowed" in detail or "could not find expected" in detail:
                hint = " Hint: quote the whole description if it contains ': '."
            report.fail(f"frontmatter: YAML parse error: {detail}{hint}")
        else:
            if not isinstance(metadata, dict):
                report.fail("frontmatter: YAML root is not a mapping")
                metadata = None
            else:
                version = getattr(yaml, "__version__", "unknown")
                report.ok(f"frontmatter: YAML parsed (PyYAML {version})")

    if metadata is not None:
        name = metadata.get("name")
        if not isinstance(name, str) or not name:
            report.fail("name: missing or not a string")
        elif not NAME_RE.fullmatch(name):
            report.fail(f"name: '{name}' is not lowercase hyphen-case")
        elif name != skill_dir.name:
            report.fail(f"name: '{name}' does not match directory '{skill_dir.name}'")
        else:
            report.ok(f"name: '{name}' matches directory")

        description = metadata.get("description")
        description_span = description_line_span(frontmatter)
        if not isinstance(description, str) or not description.strip():
            report.fail("description: missing, empty, or not a string")
        elif description_span is not None and description_span > 1:
            report.fail(f"description: spans {description_span} lines; keep it on a single line")
        elif "\n" in description or "\r" in description:
            report.fail("description: must be a single-line string")
        elif len(description) > 1024:
            report.fail(f"description: {len(description)} chars exceeds 1024")
        else:
            report.ok(f"description: single line, {len(description)} chars")

    if body is None:
        report.fail("body: cannot read body because frontmatter is invalid")
    else:
        body_lines = len(body.splitlines())
        if not body.strip():
            report.fail("body: empty")
        elif body_lines >= 500:
            report.fail(f"body: {body_lines} lines is not under 500")
        else:
            report.ok(f"body: {body_lines} lines (< 500)")

    todo_count = len(TODO_MARKER_RE.findall(text))
    if todo_count:
        report.fail(f"content: {todo_count} unresolved TODO marker(s)")
    else:
        report.ok("content: no TODO markers")

    check_refs(skill_dir, workspace, text, report)
    if body is not None:
        check_skill_refs(body, skill_roots, skill_dir.name, report)

    blocks, unterminated = extract_blocks(text)
    if unterminated:
        report.fail(f"code blocks: unterminated fence starting at SKILL.md:{unterminated}")
    python_checked = 0
    js_checked = 0
    skipped = 0
    node = shutil.which("node")
    for lang, start, code in blocks:
        if lang in PY_LANGS:
            try:
                ast.parse(code)
            except SyntaxError as exc:
                report.fail(f"python block at SKILL.md:{start}: {exc.msg} (line {exc.lineno})")
            else:
                python_checked += 1
        elif lang in JS_LANGS:
            if node is None:
                report.warn(f"js block at SKILL.md:{start}: not checked (node not found)")
                skipped += 1
            else:
                error = check_js(code, node)
                if error:
                    report.fail(f"js block at SKILL.md:{start}: {error}")
                else:
                    js_checked += 1
        else:
            skipped += 1

    if python_checked:
        report.ok(f"python blocks: {python_checked} parsed (ast.parse, not executed)")
    if js_checked:
        report.ok(f"js blocks: {js_checked} checked (node --check, not executed)")

    finish_fingerprint(skill_dir, start_fp, start_refs, report)

    print(f"Code blocks: python={python_checked} js={js_checked} skipped={skipped}")
    print(f"Summary: {report.passed} pass, {report.failed} fail, {report.warned} warn")
    print("RESULT PASS" if report.failed == 0 else "RESULT FAIL")
    return 0 if report.failed == 0 else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Static validation for a skill package.")
    parser.add_argument("skill_dir", type=Path, help="directory containing SKILL.md")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="root used to resolve references outside the skill directory (default: cwd)",
    )
    parser.add_argument(
        "--skills-root",
        action="append",
        type=Path,
        default=None,
        help="local skills directory for cross-skill refs; repeatable; overrides defaults",
    )
    parser.add_argument(
        "--stable-seconds",
        type=float,
        default=2.0,
        help="seconds SKILL.md must remain byte-identical before validation (default: 2.0)",
    )
    parser.add_argument(
        "--stability-timeout",
        type=float,
        default=30.0,
        help="maximum seconds to wait for a stable SKILL.md (default: 30.0)",
    )
    args = parser.parse_args(argv)
    if args.stable_seconds < 0:
        print("FAIL  --stable-seconds must be >= 0")
        return 2
    if args.stability_timeout <= 0:
        print("FAIL  --stability-timeout must be > 0")
        return 2
    skill_dir = args.skill_dir.expanduser().resolve()
    workspace = args.workspace.expanduser().resolve()
    if not skill_dir.is_dir():
        print(f"FAIL  skill directory not found: {ascii_text(skill_dir)}")
        return 2
    if not workspace.is_dir():
        print(f"FAIL  workspace directory not found: {ascii_text(workspace)}")
        return 2
    skill_roots = []
    seen = set()
    if args.skills_root:
        for root in args.skills_root:
            resolved = root.expanduser().resolve()
            if not resolved.is_dir():
                print(f"FAIL  skill root not found: {ascii_text(resolved)}")
                return 2
            if resolved not in seen:
                seen.add(resolved)
                skill_roots.append(resolved)
    else:
        candidates = (
            Path.home() / ".qoder" / "skills",
            workspace / ".qoder" / "skills",
        )
        for candidate in candidates:
            resolved = candidate.expanduser().resolve()
            if resolved.is_dir() and resolved not in seen:
                seen.add(resolved)
                skill_roots.append(resolved)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(f"FAIL  SKILL.md not found in {ascii_text(skill_dir)}")
        return 2
    try:
        start_fp, start_refs, raw, waited = wait_for_stable(
            skill_dir, args.stable_seconds, args.stability_timeout
        )
    except StabilityError as exc:
        print(f"FAIL  stability: {ascii_text(exc)}")
        print("RESULT FAIL")
        return 1
    if args.stable_seconds == 0:
        stability_text = f"snapshot taken without waiting after {waited:.1f}s"
    else:
        stability_text = (
            f"unchanged for {args.stable_seconds:.1f}s after {waited:.1f}s"
        )
    try:
        return validate(
            skill_dir, workspace, skill_roots, raw, start_fp, start_refs, stability_text
        )
    except subprocess.TimeoutExpired:
        print("FAIL  node --check timed out")
        print("RESULT FAIL")
        return 1
    except OSError as exc:
        print(f"FAIL  validator error: {ascii_text(exc)}")
        print("RESULT FAIL")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
    except Exception as exc:
        print(f"FAIL  validator error: {ascii_text(exc)}")
        sys.exit(2)
