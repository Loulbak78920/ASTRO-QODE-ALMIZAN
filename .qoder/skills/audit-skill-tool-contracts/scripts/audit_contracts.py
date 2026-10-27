#!/usr/bin/env python3
"""Read-only audit of declared Skill resources and CLI contracts.

Subcommands:
  audit    check declared scripts/assets/references and probe --help positionals
  compare  structural parity fallback for a source/translation pair
  mutate   mutate a copy of a document and require a validator to fail

Exit codes: audit/compare 0 PASS, 1 FAIL, 2 usage/environment error,
3 UNVERIFIED; mutate 0 expected failure observed, 1 validator missed the
mutation (or returned another code), 2 usage/environment/target/timeout.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shlex
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2
EXIT_UNVERIFIED = 3

SPAN_RE = re.compile(r"`([^`\n]+)`")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
DECL_RE = re.compile(r"^(?:scripts|references|assets)/[A-Za-z0-9._\-/]+$")
FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([^\s`]*)\s*$")
FENCE_CLOSE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
CHECKLIST_RE = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+")
HASH_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
DIGIT_RE = re.compile(r"\d+")
USAGE_RE = re.compile(r"(?i)^\s*usage:\s*(.*)$")
POS_HEADER_RE = re.compile(r"(?i)^\s*positional arguments:\s*$")
OPT_HEADER_RE = re.compile(r"(?i)^\s*(?:options|optional arguments):\s*$")
OPT_METAVAR_RE = re.compile(r"^[A-Z][A-Z0-9_\-]*$")


def safe(text: object) -> str:
    return str(text).encode("ascii", "backslashreplace").decode("ascii")


def configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


class Report:
    def __init__(self) -> None:
        self.passes = 0
        self.failures = 0
        self.unverified = 0

    def _line(self, level: str, message: str) -> None:
        print(f"{level:<10} {safe(message)}")

    def ok(self, message: str) -> None:
        self.passes += 1
        self._line("PASS", message)

    def fail(self, message: str) -> None:
        self.failures += 1
        self._line("FAIL", message)

    def unknown(self, message: str) -> None:
        self.unverified += 1
        self._line("UNVERIFIED", message)

    def info(self, message: str) -> None:
        self._line("INFO", message)

    def skip(self, message: str) -> None:
        self._line("SKIP", message)


def verdict(report: Report) -> int:
    print(
        f"Summary: {report.passes} pass, {report.failures} fail, "
        f"{report.unverified} unverified"
    )
    if report.failures:
        print("RESULT FAIL")
        return EXIT_FAIL
    if report.unverified:
        print("RESULT UNVERIFIED")
        return EXIT_UNVERIFIED
    print("RESULT PASS")
    return EXIT_PASS


def error_line(kind: str, message: str) -> int:
    print(f"FAIL {kind}: {safe(message)}")
    print("RESULT ERROR")
    return EXIT_USAGE


@dataclass(frozen=True)
class Shape:
    required: int
    optional: int
    kinds: tuple[str, ...] | None
    total: int | None = None


SHAPES = {
    "none": Shape(0, 0, ()),
    "optional-dir": Shape(0, 1, ("dir",)),
    "required-dir": Shape(1, 0, ("dir",)),
    "one-file": Shape(1, 0, ("file",)),
    "two-files": Shape(2, 0, ("file", "file")),
    "dir": Shape(0, 0, ("dir",), total=1),
    "file": Shape(0, 0, ("file",), total=1),
}
SHAPE_LIST = (
    ", ".join(sorted(SHAPES)) + ", required=N,optional=M, total=N (dir/file aliases)"
)


def parse_shape(raw: str) -> Shape | None:
    text = raw.strip().lower()
    if text in SHAPES:
        return SHAPES[text]
    match = re.fullmatch(r"required=(\d+),optional=(\d+)", text)
    if match:
        return Shape(int(match.group(1)), int(match.group(2)), None)
    match = re.fullmatch(r"total=(\d+)", text)
    if match:
        return Shape(0, 0, None, total=int(match.group(1)))
    return None


def parse_expect(raw: str) -> tuple[str, Shape]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"expected REL=SHAPE, got {raw!r}")
    rel_raw, shape_raw = raw.split("=", 1)
    rel = rel_raw.strip().replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    rel = rel.strip("/")
    if not re.fullmatch(r"scripts/[A-Za-z0-9._\-/]+", rel):
        raise argparse.ArgumentTypeError("--expect only accepts declared scripts/ paths")
    shape = parse_shape(shape_raw)
    if shape is None:
        raise argparse.ArgumentTypeError(
            f"unknown shape {shape_raw!r}; allowed: {SHAPE_LIST}"
        )
    return rel, shape


def positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an integer: {raw}")
    if value < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return value


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        print(f"FAIL usage: {safe(message)}")
        print("RESULT ERROR")
        raise SystemExit(EXIT_USAGE)


def default_roots() -> list[Path]:
    candidates = [Path.home() / ".qoder" / "skills", Path.cwd() / ".qoder" / "skills"]
    roots: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return roots


def resolve_target(target: str, roots: list[Path]) -> tuple[Path | None, str | None]:
    path = Path(target)
    if path.exists():
        if not path.is_dir():
            return None, f"target is not a directory: {target}"
        if not (path / "SKILL.md").is_file():
            return None, f"SKILL.md not found in {target}"
        return path.resolve(), None
    if path.is_absolute() or "/" in target or "\\" in target:
        return None, f"path not found: {target}"
    for root in roots:
        candidate = root / target
        if (candidate / "SKILL.md").is_file():
            return candidate.resolve(), None
    joined = "; ".join(str(root) for root in roots)
    return None, f"skill '{target}' not found under {joined}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_skill_md(skill_dir: Path) -> tuple[str | None, str | None, str | None]:
    path = skill_dir / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, None, f"cannot read SKILL.md: {exc}"
    if not text.startswith("---"):
        return None, None, "SKILL.md must start with a '---' frontmatter line"
    lines = text.splitlines()
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return None, None, "frontmatter closing '---' not found"
    return text, "\n".join(lines[end + 1:]), None


def collect_declared(body: str) -> list[str]:
    candidates: list[str] = []
    for span in SPAN_RE.findall(body):
        parts = span.split()
        if parts:
            candidates.append(parts[0])
    for target in LINK_RE.findall(body):
        parts = target.split()
        if parts:
            candidates.append(parts[0])
    declared: list[str] = []
    for raw in candidates:
        ref = raw.strip()
        if ref.startswith("<") and ref.endswith(">"):
            ref = ref[1:-1]
        ref = ref.split("#", 1)[0].rstrip(".,;:")
        while ref.startswith("./"):
            ref = ref[2:]
        if not DECL_RE.fullmatch(ref):
            continue
        if ".." in ref.split("/"):
            continue
        if ref not in declared:
            declared.append(ref)
    return declared


def check_manifest(skill_dir: Path, declared: list[str], report: Report) -> None:
    if not declared:
        report.info("declared resources: none found in inline code or links")
        return
    for rel in declared:
        resolved = (skill_dir / rel).resolve()
        try:
            resolved.relative_to(skill_dir)
        except ValueError:
            report.fail(f"declared resource escapes skill directory: {rel}")
            continue
        if resolved.is_dir():
            report.fail(f"declared resource is a directory, not a file: {rel}")
            continue
        if not resolved.is_file():
            report.fail(f"declared resource missing: {rel}")
            continue
        report.ok(
            f"resource: {rel} ({resolved.stat().st_size} bytes, "
            f"sha256={file_sha256(resolved)})"
        )


@dataclass
class Probe:
    state: str
    detail: str = ""
    help_text: str = ""
    sha_before: str = ""
    sha_after: str = ""


def probe_help(script: Path, timeout: int) -> Probe:
    before = file_sha256(script)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=str(script.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="backslashreplace",
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return Probe(
            "timeout",
            f"--help exceeded {timeout}s",
            sha_before=before,
            sha_after=before,
        )
    except OSError as exc:
        return Probe(
            "error", f"cannot execute: {exc}", sha_before=before, sha_after=before
        )
    after = file_sha256(script)
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        return Probe(
            "nonzero",
            f"--help exited {completed.returncode}",
            output,
            before,
            after,
        )
    if before != after:
        return Probe(
            "changed", "script changed while --help was running", output, before, after
        )
    return Probe("ok", "", output, before, after)


def extract_usage(help_text: str) -> str | None:
    lines = help_text.splitlines()
    for index, line in enumerate(lines):
        match = USAGE_RE.match(line)
        if not match:
            continue
        parts = [match.group(1).strip()]
        cursor = index + 1
        while cursor < len(lines):
            nxt = lines[cursor]
            if not nxt.strip() or not nxt[:1].isspace():
                break
            parts.append(nxt.strip())
            cursor += 1
        return " ".join(part for part in parts if part)
    return None


def extract_positional_help(help_text: str) -> dict[str, str]:
    lines = help_text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if POS_HEADER_RE.match(line):
            start = index + 1
            break
    if start is None:
        return {}
    entries: dict[str, str] = {}
    current = None
    for line in lines[start:]:
        if OPT_HEADER_RE.match(line):
            break
        if not line.strip():
            if current is not None:
                break
            continue
        match = re.match(r"^ {2}(\S+)(?: {2,}(.*))?$", line)
        if match:
            current = match.group(1)
            entries[current] = (match.group(2) or "").strip()
        elif current is not None:
            entries[current] = (entries[current] + " " + line.strip()).strip()
    return entries


def split_usage_groups(usage: str) -> list[tuple[str, bool]] | None:
    match = re.match(r"^\S+\s*(.*)$", usage)
    if not match:
        return None
    rest = match.group(1)
    groups: list[tuple[str, bool]] = []
    index = 0
    while index < len(rest):
        char = rest[index]
        if char.isspace():
            index += 1
            continue
        if char == "[":
            depth = 1
            cursor = index + 1
            while cursor < len(rest) and depth:
                if rest[cursor] == "[":
                    depth += 1
                elif rest[cursor] == "]":
                    depth -= 1
                cursor += 1
            if depth:
                return None
            groups.append((rest[index + 1:cursor - 1].strip(), True))
            index = cursor
            continue
        cursor = index
        while cursor < len(rest) and not rest[cursor].isspace() and rest[cursor] not in "[]":
            cursor += 1
        groups.append((rest[index:cursor], False))
        index = cursor
    return groups


def strip_option_tokens(tokens: list[str]) -> list[str]:
    kept: list[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            if OPT_METAVAR_RE.match(token):
                continue
        if token.startswith("-"):
            if "=" not in token:
                skip_next = True
            continue
        kept.append(token)
    return kept


def parse_usage_shape(
    usage: str, positional_help: dict[str, str]
) -> tuple[int, int, tuple[str, ...]] | None:
    groups = split_usage_groups(usage)
    if groups is None:
        return None
    required = 0
    optional = 0
    names: list[str] = []
    skip_value = False
    for text, is_group in groups:
        token = text.strip()
        if "..." in token.split():
            return None
        if is_group:
            skip_value = False
            if "[" in token or "]" in token:
                return None
            inner = strip_option_tokens([tok for tok in token.split() if tok])
            for name in inner:
                if "{" in name or "}" in name:
                    return None
                names.append(name)
                optional += 1
            continue
        if token.startswith("-"):
            if "=" not in token:
                skip_value = True
            continue
        if skip_value:
            skip_value = False
            if OPT_METAVAR_RE.match(token):
                continue
        if token.startswith("{") and token.endswith("}"):
            return None
        if re.search(r"[\[\]{}]", token):
            return None
        names.append(token)
        required += 1
    if positional_help:
        for name in names:
            if name not in positional_help:
                return None
    return required, optional, tuple(names)


def infer_kind(name: str, positional_help: dict[str, str]) -> str | None:
    text = positional_help.get(name, "").lower()
    if not text:
        return None
    has_dir = re.search(r"\bdirector(?:y|ies)\b", text) is not None
    has_file = re.search(r"\bfiles?\b", text) is not None
    if has_dir == has_file:
        return None
    return "dir" if has_dir else "file"


def check_expectation(
    rel: str,
    shape: Shape,
    probe: Probe,
    positional_help: dict[str, str],
    report: Report,
) -> None:
    if probe.state != "ok":
        report.unknown(f"expect {rel}: probe {probe.state} ({probe.detail})")
        return
    usage = extract_usage(probe.help_text)
    if usage is None:
        report.unknown(f"expect {rel}: usage line not found in --help output")
        return
    print(f"USAGE {safe(usage)}")
    for name, text in positional_help.items():
        print(f"POSITIONAL {safe(name)}: {safe(text)}")
    parsed = parse_usage_shape(usage, positional_help)
    if parsed is None:
        report.unknown(f"expect {rel}: positional arity not derivable from usage")
        return
    required, optional, names = parsed
    kinds = tuple(infer_kind(name, positional_help) for name in names)
    kinds_known = all(kind is not None for kind in kinds)
    shown = ", ".join(kind or "?" for kind in kinds)
    print(
        f"OBSERVED {safe(rel)}: required={required} optional={optional} kinds=[{safe(shown)}]"
    )
    if shape.total is not None:
        expected = f"total={shape.total}"
    else:
        expected = f"required={shape.required} optional={shape.optional}"
    if shape.kinds is not None:
        expected += f" kinds=[{', '.join(shape.kinds)}]"
    print(f"EXPECT {safe(rel)}: {safe(expected)}")
    if shape.total is not None:
        if required + optional != shape.total:
            report.fail(
                f"expect arity for {rel}: expected {shape.total} positional(s) total, "
                f"observed {required} required/{optional} optional"
            )
            report.skip(f"expect kind for {rel}: arity mismatch")
            return
        report.ok(
            f"expect arity for {rel}: {required + optional} positional(s) total "
            f"({required} required / {optional} optional)"
        )
    else:
        if (required, optional) != (shape.required, shape.optional):
            report.fail(
                f"expect arity for {rel}: expected {shape.required} required/"
                f"{shape.optional} optional, observed {required} required/{optional} optional"
            )
            report.skip(f"expect kind for {rel}: arity mismatch")
            return
        report.ok(f"expect arity for {rel}: {required} required / {optional} optional")
    if shape.kinds is None:
        report.info(f"expect kind for {rel}: not asserted (generic shape)")
        return
    if not kinds_known:
        report.unknown(f"expect kind for {rel}: kind not derivable from positional help")
        return
    if not shape.kinds:
        report.ok(f"expect kind for {rel}: no positionals")
    elif kinds == shape.kinds:
        report.ok(f"expect kind for {rel}: {', '.join(shape.kinds)}")
    else:
        report.fail(
            f"expect kind for {rel}: expected {', '.join(shape.kinds)}, "
            f"observed {', '.join(kind or '?' for kind in kinds)}"
        )


def run_audit(args: argparse.Namespace) -> int:
    targets: list[tuple[str, Shape]] = []
    seen: set[str] = set()
    for rel, shape in args.expect:
        key = rel.lower() if os.name == "nt" else rel
        if key in seen:
            return error_line("usage", f"duplicate --expect target: {rel}")
        seen.add(key)
        targets.append((rel, shape))
    if targets and not args.help_probe:
        return error_line("usage", "--expect requires --help-probe")

    roots = [path.resolve() for path in args.skills_root] if args.skills_root else default_roots()
    skill_dir, err = resolve_target(args.target, roots)
    if err:
        return error_line("environment", err)
    print(f"TARGET {safe(skill_dir)}")

    text, body, err = read_skill_md(skill_dir)
    if err:
        print(f"FAIL frontmatter: {safe(err)}")
        print("RESULT FAIL")
        return EXIT_FAIL
    report = Report()
    report.ok(
        f"skill: SKILL.md ({len(text.encode('utf-8'))} bytes, "
        f"sha256={file_sha256(skill_dir / 'SKILL.md')})"
    )
    declared = collect_declared(body)
    check_manifest(skill_dir, declared, report)

    probes: dict[str, Probe] = {}
    if args.help_probe:
        for rel in declared:
            if not rel.startswith("scripts/"):
                continue
            path = (skill_dir / rel).resolve()
            if not path.is_file():
                report.skip(f"probe {rel}: declared resource missing")
                continue
            if path.suffix.lower() != ".py":
                report.unknown(f"probe {rel}: unsupported probe type")
                continue
            probe = probe_help(path, args.timeout)
            probes[rel] = probe
            if probe.state == "ok":
                report.ok(f"probe {rel}: --help exit=0 (sha256={probe.sha_after})")
            else:
                report.unknown(f"probe {rel}: {probe.state} ({probe.detail})")

    declared_keys = {
        (rel.lower() if os.name == "nt" else rel): rel for rel in declared
    }
    for rel, shape in targets:
        key = rel.lower() if os.name == "nt" else rel
        actual = declared_keys.get(key)
        if actual is None:
            base = rel.rsplit("/", 1)[-1].lower()
            same = [d for d in declared if d.rsplit("/", 1)[-1].lower() == base]
            hint = f" (did you mean {same[0]}?)" if same else ""
            report.fail(f"expect target not declared in SKILL.md: {rel}{hint}")
            continue
        path = (skill_dir / actual).resolve()
        if not path.is_file():
            report.skip(f"expect {actual}: declared resource missing")
            continue
        probe = probes.get(actual)
        if probe is None:
            if path.suffix.lower() != ".py":
                continue
            report.skip(f"expect {actual}: not probed")
            continue
        positional_help = (
            extract_positional_help(probe.help_text) if probe.state == "ok" else {}
        )
        check_expectation(actual, shape, probe, positional_help, report)

    return verdict(report)


def strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                return "\n".join(lines[index + 1:])
    return "\n".join(lines)


@dataclass
class Doc:
    headings: list[tuple[int, str]]
    tables: list[tuple[int, tuple[int, ...]]]
    blocks: list[tuple[str, str]]
    checklist: list[str]
    inline: list[str]
    numbers: list[str]


def count_cells(row: str) -> int:
    text = row.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return len(re.split(r"(?<!\\)\|", text))


def parse_doc(text: str) -> Doc:
    lines = strip_frontmatter(text).splitlines()
    prose: list[str] = []
    blocks: list[tuple[str, str]] = []
    index = 0
    while index < len(lines):
        opening = FENCE_OPEN_RE.match(lines[index])
        if opening:
            marker = opening.group(1)
            lang = opening.group(2)
            body: list[str] = []
            index += 1
            while index < len(lines):
                closing = FENCE_CLOSE_RE.match(lines[index])
                if (
                    closing
                    and closing.group(1)[0] == marker[0]
                    and len(closing.group(1)) >= len(marker)
                ):
                    index += 1
                    break
                body.append(lines[index])
                index += 1
            blocks.append((lang, "\n".join(body)))
            continue
        prose.append(lines[index])
        index += 1

    headings: list[tuple[int, str]] = []
    for line in prose:
        match = HEADING_RE.match(line)
        if match:
            headings.append((len(match.group(1)), match.group(2).strip()))

    tables: list[tuple[int, tuple[int, ...]]] = []
    index = 0
    while index < len(prose):
        if prose[index].lstrip().startswith("|"):
            rows: list[str] = []
            while index < len(prose) and prose[index].lstrip().startswith("|"):
                rows.append(prose[index])
                index += 1
            tables.append((len(rows), tuple(count_cells(row) for row in rows)))
            continue
        index += 1

    checklist: list[str] = []
    for line in prose:
        match = CHECKLIST_RE.match(line)
        if match:
            checklist.append("x" if match.group(1).lower() == "x" else " ")

    inline: list[str] = []
    for line in prose:
        for span in SPAN_RE.findall(line):
            value = span.strip()
            if value:
                inline.append(value)

    numbers: list[str] = []
    for line in prose:
        for item in HASH_RE.findall(line):
            numbers.append("sha256:" + item.lower())
        remainder = HASH_RE.sub(" ", line)
        for item in DIGIT_RE.findall(remainder):
            numbers.append("num:" + item)

    return Doc(headings, tables, blocks, checklist, inline, numbers)


def first_diff(left, right) -> tuple[int, str]:
    limit = min(len(left), len(right))
    for index in range(limit):
        if left[index] != right[index]:
            return index, f"{left[index]!r} vs {right[index]!r}"
    return limit, f"length {len(left)} vs {len(right)}"


def truncate(text: str, limit: int = 120) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def heading_summary(headings: list[tuple[int, str]]) -> str:
    counts = Counter(level for level, _ in headings)
    if not counts:
        return "none"
    return " ".join(f"H{level}={counts[level]}" for level in sorted(counts))


def summarize_tables(tables: list[tuple[int, tuple[int, ...]]]) -> str:
    if not tables:
        return "none"
    parts = []
    for rows, columns in tables:
        head = columns[0] if columns else 0
        parts.append(f"({rows}, {head})")
    return ", ".join(parts)


def compare_blocks(
    left: list[tuple[str, str]], right: list[tuple[str, str]], limit: int
) -> list[str]:
    problems: list[str] = []
    for index in range(max(len(left), len(right))):
        if len(problems) >= limit:
            break
        if index >= len(left):
            problems.append(f"block {index + 1}: missing in source")
            continue
        if index >= len(right):
            problems.append(f"block {index + 1}: missing in translation")
            continue
        left_lang, left_code = left[index]
        right_lang, right_code = right[index]
        if left_lang != right_lang:
            problems.append(
                f"block {index + 1}: language {left_lang!r} vs {right_lang!r}"
            )
            continue
        if left_code != right_code:
            line_no, detail = first_diff(left_code.splitlines(), right_code.splitlines())
            problems.append(
                f"block {index + 1}: content differs at line {line_no + 1} "
                f"({truncate(detail, 80)})"
            )
    return problems


def list_diff(left: Counter, right: Counter, limit: int) -> str:
    missing = sorted((left - right).elements())
    extra = sorted((right - left).elements())
    parts = []
    if missing:
        parts.append(
            f"missing {len(missing)}: {', '.join(truncate(item, 40) for item in missing[:limit])}"
        )
    if extra:
        parts.append(
            f"extra {len(extra)}: {', '.join(truncate(item, 40) for item in extra[:limit])}"
        )
    return "; ".join(parts)


def compare_docs(source: Doc, translation: Doc, limit: int, report: Report) -> None:
    source_levels = [level for level, _ in source.headings]
    translation_levels = [level for level, _ in translation.headings]
    if source_levels == translation_levels:
        report.ok(f"headings: {heading_summary(source.headings)} (sequence aligned)")
    else:
        index, detail = first_diff(source_levels, translation_levels)
        report.fail(f"headings: sequence differs at index {index} ({detail})")

    if source.blocks == translation.blocks:
        report.ok(
            f"code blocks: {len(source.blocks)} block(s) identical "
            f"(language and content)"
        )
    else:
        problems = compare_blocks(source.blocks, translation.blocks, limit)
        report.fail("code blocks: " + "; ".join(problems))

    if source.tables == translation.tables:
        report.ok(f"tables: {len(source.tables)} table(s) [{summarize_tables(source.tables)}]")
    else:
        index, detail = first_diff(source.tables, translation.tables)
        report.fail(
            f"tables: differ at index {index} ({truncate(detail, 120)}); "
            f"source [{summarize_tables(source.tables)}], "
            f"translation [{summarize_tables(translation.tables)}]"
        )

    source_checks = Counter(source.checklist)
    translation_checks = Counter(translation.checklist)
    if source_checks == translation_checks:
        checked = source.checklist.count("x")
        report.ok(
            f"checklist: {len(source.checklist)} item(s) "
            f"(unchecked={len(source.checklist) - checked} checked={checked})"
        )
    else:
        report.fail(
            f"checklist: {len(source.checklist)} vs {len(translation.checklist)} item(s); "
            f"checked {source.checklist.count('x')} vs {translation.checklist.count('x')}"
        )

    source_inline = Counter(source.inline)
    translation_inline = Counter(translation.inline)
    if source_inline == translation_inline:
        report.ok(f"inline identifiers: {sum(source_inline.values())} token(s) matched")
    else:
        detail = list_diff(source_inline, translation_inline, limit)
        report.fail(f"inline identifiers: {detail}")

    source_numbers = Counter(source.numbers)
    translation_numbers = Counter(translation.numbers)
    if source_numbers == translation_numbers:
        report.ok(f"numbers: {sum(source_numbers.values())} token(s) matched")
    else:
        detail = list_diff(source_numbers, translation_numbers, limit)
        report.fail(f"numbers: {detail}")


def run_compare(args: argparse.Namespace) -> int:
    for path in (args.source, args.translation):
        if not path.is_file():
            return error_line("environment", f"file not found: {path}")
    try:
        source_text = args.source.read_text(encoding="utf-8")
        translation_text = args.translation.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return error_line("environment", f"cannot read input: {exc}")
    report = Report()
    report.ok(f"source: {args.source} (sha256={file_sha256(args.source)})")
    report.ok(
        f"translation: {args.translation} (sha256={file_sha256(args.translation)})"
    )
    compare_docs(
        parse_doc(source_text), parse_doc(translation_text), args.max_report, report
    )
    return verdict(report)


TABLE_DIVIDER_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
MUTATIONS = {
    "heading": "demote the first heading between H2 and H5",
    "table": "add one cell to the last data row of the first table",
    "code": "append a 'drift' line inside the first fenced block",
    "language": "change the first fenced block's language",
    "checklist": "flip the first checklist item",
    "inline": "alter the first backticked identifier",
    "number": "increment the first number token",
}
DIMENSIONS = {
    "heading": lambda doc: [level for level, _ in doc.headings],
    "table": lambda doc: doc.tables,
    "code": lambda doc: doc.blocks,
    "language": lambda doc: [lang for lang, _ in doc.blocks],
    "checklist": lambda doc: doc.checklist,
    "inline": lambda doc: Counter(doc.inline),
    "number": lambda doc: Counter(doc.numbers),
}


def scan_layout(lines: list[str]) -> tuple[list[str], list[tuple[int, int, str]]]:
    kinds = ["prose"] * len(lines)
    blocks: list[tuple[int, int, str]] = []
    index = 0
    if lines and lines[0].strip() == "---":
        for cursor in range(1, len(lines)):
            if lines[cursor].strip() == "---":
                for slot in range(cursor + 1):
                    kinds[slot] = "frontmatter"
                index = cursor + 1
                break
    while index < len(lines):
        opening = FENCE_OPEN_RE.match(lines[index])
        if not opening:
            index += 1
            continue
        marker = opening.group(1)
        kinds[index] = "fence"
        cursor = index + 1
        close: int | None = None
        while cursor < len(lines):
            closing = FENCE_CLOSE_RE.match(lines[cursor])
            if (
                closing
                and closing.group(1)[0] == marker[0]
                and len(closing.group(1)) >= len(marker)
            ):
                kinds[cursor] = "fence"
                close = cursor
                break
            kinds[cursor] = "block"
            cursor += 1
        blocks.append((index, close if close is not None else len(lines), opening.group(2)))
        index = cursor + 1 if close is not None else cursor
    return kinds, blocks


def mutate_heading(
    lines: list[str], kinds: list[str], blocks: list[tuple[int, int, str]]
) -> tuple[list[str], str] | None:
    for index, line in enumerate(lines):
        if kinds[index] != "prose":
            continue
        match = HEADING_RE.match(line)
        if match and 2 <= len(match.group(1)) <= 5:
            level = len(match.group(1)) + 1
            lines = list(lines)
            lines[index] = "#" * level + " " + match.group(2)
            return lines, f"line {index + 1}: heading level -> H{level}"
    return None


def mutate_table(
    lines: list[str], kinds: list[str], blocks: list[tuple[int, int, str]]
) -> tuple[list[str], str] | None:
    index = 0
    while index < len(lines):
        if kinds[index] != "prose" or not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        rows: list[int] = []
        while (
            index < len(lines)
            and kinds[index] == "prose"
            and lines[index].lstrip().startswith("|")
        ):
            rows.append(index)
            index += 1
        for row in reversed(rows[1:]):
            if TABLE_DIVIDER_RE.match(lines[row]):
                continue
            lines = list(lines)
            lines[row] = lines[row].rstrip() + " drift |"
            return lines, f"line {row + 1}: table row gains one cell"
        return None
    return None


def mutate_code(
    lines: list[str], kinds: list[str], blocks: list[tuple[int, int, str]]
) -> tuple[list[str], str] | None:
    for open_index, close_index, _lang in blocks:
        lines = list(lines)
        lines.insert(close_index, "drift")
        return lines, f"line {open_index + 1}: code block gains a 'drift' line"
    return None


def mutate_language(
    lines: list[str], kinds: list[str], blocks: list[tuple[int, int, str]]
) -> tuple[list[str], str] | None:
    for open_index, _close_index, lang in blocks:
        opening = FENCE_OPEN_RE.match(lines[open_index])
        if opening is None:
            continue
        new_lang = "text" if lang != "text" else "bash"
        lines = list(lines)
        lines[open_index] = opening.group(1) + new_lang
        return lines, f"line {open_index + 1}: code language -> {new_lang!r}"
    return None


def mutate_checklist(
    lines: list[str], kinds: list[str], blocks: list[tuple[int, int, str]]
) -> tuple[list[str], str] | None:
    for index, line in enumerate(lines):
        if kinds[index] != "prose":
            continue
        match = CHECKLIST_RE.match(line)
        if match is None:
            continue
        mark = " " if match.group(1).lower() == "x" else "x"
        lines = list(lines)
        lines[index] = line[: match.start(1)] + mark + line[match.end(1):]
        return lines, f"line {index + 1}: checklist state -> [{mark}]"
    return None


def mutate_inline(
    lines: list[str], kinds: list[str], blocks: list[tuple[int, int, str]]
) -> tuple[list[str], str] | None:
    for index, line in enumerate(lines):
        if kinds[index] != "prose":
            continue
        match = SPAN_RE.search(line)
        if match is None:
            continue
        lines = list(lines)
        lines[index] = (
            line[: match.start()] + "`" + match.group(1) + "x`" + line[match.end():]
        )
        return lines, f"line {index + 1}: inline identifier {match.group(1)!r} altered"
    return None


def mutate_number(
    lines: list[str], kinds: list[str], blocks: list[tuple[int, int, str]]
) -> tuple[list[str], str] | None:
    for index, line in enumerate(lines):
        if kinds[index] != "prose":
            continue
        hashes = list(HASH_RE.finditer(line))
        for match in DIGIT_RE.finditer(line):
            if any(span.start() <= match.start() < span.end() for span in hashes):
                continue
            value = int(match.group(0)) + 1
            lines = list(lines)
            lines[index] = line[: match.start()] + str(value) + line[match.end():]
            return lines, f"line {index + 1}: number {match.group(0)} -> {value}"
    return None


MUTATORS = {
    "heading": mutate_heading,
    "table": mutate_table,
    "code": mutate_code,
    "language": mutate_language,
    "checklist": mutate_checklist,
    "inline": mutate_inline,
    "number": mutate_number,
}


def run_mutate(args: argparse.Namespace) -> int:
    replace_mode = any(
        value is not None for value in (args.copy, args.replace, args.with_text)
    )
    if replace_mode:
        return run_mutate_replace(args)
    return run_mutate_kind(args)


def run_mutate_kind(args: argparse.Namespace) -> int:
    if getattr(args, "validator_argv", []):
        return error_line(
            "usage", "kind mode takes --validator; trailing argv is for --copy mode"
        )
    source: Path | None = args.source
    out: Path | None = args.out
    if source is None or out is None or args.kind is None or args.validator is None:
        return error_line(
            "usage",
            "kind mode requires SOURCE, --out, --kind and --validator",
        )
    if not source.is_file():
        return error_line("environment", f"source not found: {source}")
    if source.resolve() == out.resolve():
        return error_line(
            "usage", "--out must differ from source; the original is never modified"
        )
    try:
        text = source.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return error_line("environment", f"cannot read source: {exc}")
    before = file_sha256(source)
    lines = text.splitlines()
    kinds, blocks = scan_layout(lines)
    result = MUTATORS[args.kind](lines, kinds, blocks)
    if result is None:
        return error_line(
            "environment", f"mutation target not found for kind {args.kind!r}"
        )
    mutated_lines, detail = result
    mutated = "\n".join(mutated_lines) + "\n"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(mutated, encoding="utf-8")
    except OSError as exc:
        return error_line("environment", f"cannot write copy: {exc}")
    after = file_sha256(out)
    report = Report()
    report.ok(f"source: {source} (sha256={before})")
    report.ok(f"copy: {out} (sha256={after})")
    report.ok(f"mutation: {args.kind} at {detail}")
    if before == after:
        report.fail("mutation ineffective: copy hash equals source")
        return verdict(report)
    dimension = DIMENSIONS[args.kind]
    if dimension(parse_doc(text)) == dimension(parse_doc(mutated)):
        report.fail(f"mutation ineffective: {args.kind} dimension unchanged")
        return verdict(report)
    report.ok(f"mutation verified: {args.kind} dimension differs")
    if file_sha256(source) != before:
        report.fail("source changed during mutation; copy result is invalid")
        return verdict(report)

    tokens = shlex.split(args.validator, posix=True)
    if not tokens or not any("{target}" in token for token in tokens):
        return error_line("usage", "--validator must contain the {target} placeholder")
    argv = [token.replace("{target}", str(out)) for token in tokens]
    print(f"VALIDATOR {safe(' '.join(shlex.quote(token) for token in argv))}")
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        completed = subprocess.run(
            argv,
            cwd=str(out.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="backslashreplace",
            timeout=args.timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return error_line("environment", f"validator exceeded {args.timeout}s")
    except OSError as exc:
        return error_line("environment", f"cannot execute validator: {exc}")
    output = (completed.stdout or "") + (completed.stderr or "")
    for line in [item for item in output.splitlines() if item.strip()][-8:]:
        print(f"VALIDATOR-OUT {safe(line)}")
    if file_sha256(source) != before:
        report.fail("source changed while the validator ran")
    if completed.returncode == args.expect_exit:
        report.ok(f"validator exited {completed.returncode} as expected")
        return verdict(report)
    report.fail(
        f"validator exited {completed.returncode}, expected {args.expect_exit}"
    )
    return verdict(report)


def unique_copy_path(workdir: Path, origin: Path) -> Path:
    base = origin.stem + ".mutated"
    candidate = workdir / f"{base}{origin.suffix}"
    counter = 2
    while candidate.exists():
        candidate = workdir / f"{base}-{counter}{origin.suffix}"
        counter += 1
    return candidate


def run_mutate_replace(args: argparse.Namespace) -> int:
    if (
        args.source is not None
        or args.out is not None
        or args.kind is not None
        or args.validator is not None
    ):
        return error_line(
            "usage", "--copy mode and --kind mode are mutually exclusive"
        )
    origin: Path | None = args.copy
    old: str | None = args.replace
    new: str = args.with_text if args.with_text is not None else ""
    if origin is None or old is None or args.with_text is None:
        return error_line("usage", "--copy mode requires --copy, --replace and --with")
    if not old:
        return error_line("usage", "--replace must not be empty")
    if not origin.is_file():
        return error_line("environment", f"copy source not found: {origin}")
    try:
        text = origin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return error_line("environment", f"cannot read --copy: {exc}")
    before = file_sha256(origin)
    positions = [match.start() for match in re.finditer(re.escape(old), text)]
    if len(positions) < args.occurrence:
        return error_line(
            "environment",
            f"target not found: occurrence {args.occurrence} of {old!r} "
            f"(found {len(positions)})",
        )
    start = positions[args.occurrence - 1]
    mutated = text[:start] + new + text[start + len(old):]
    workdir: Path = args.workdir
    try:
        workdir.mkdir(parents=True, exist_ok=True)
        out = unique_copy_path(workdir, origin)
        out.write_text(mutated, encoding="utf-8")
    except OSError as exc:
        return error_line("environment", f"cannot write mutated copy: {exc}")
    after = file_sha256(out)
    report = Report()
    report.ok(f"source: {origin} (sha256={before})")
    report.ok(f"copy: {out} (sha256={after})")
    report.ok(f"mutation: occurrence {args.occurrence} of {old!r} replaced")
    if before == after:
        report.fail("mutation ineffective: copy hash equals source")
    elif file_sha256(origin) != before:
        report.fail("source changed during mutation; copy result is invalid")
    if report.failures:
        if not args.keep:
            out.unlink(missing_ok=True)
        return verdict(report)

    argv = [token for token in getattr(args, "validator_argv", []) if token != "--"]
    if not argv:
        if not args.keep:
            out.unlink(missing_ok=True)
        return error_line("usage", "provide the validator argv after '--'")
    has_placeholder = any("{mutated}" in token for token in argv)
    argv = [token.replace("{mutated}", str(out)) for token in argv]
    if not has_placeholder:
        argv.append(str(out))
    print(f"VALIDATOR {safe(' '.join(shlex.quote(token) for token in argv))}")
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="backslashreplace",
            timeout=args.timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        if not args.keep:
            out.unlink(missing_ok=True)
        return error_line("environment", f"validator exceeded {args.timeout}s")
    except OSError as exc:
        if not args.keep:
            out.unlink(missing_ok=True)
        return error_line("environment", f"cannot execute validator: {exc}")
    output = (completed.stdout or "") + (completed.stderr or "")
    for line in [item for item in output.splitlines() if item.strip()][-8:]:
        print(f"VALIDATOR-OUT {safe(line)}")
    if file_sha256(origin) != before:
        report.fail("source changed while the validator ran")
    if completed.returncode == args.expect_exit:
        report.ok(f"validator exited {completed.returncode} as expected")
    else:
        report.fail(
            f"validator exited {completed.returncode}, expected {args.expect_exit}"
        )
    if args.keep:
        print(f"KEPT {safe(out)}")
    else:
        out.unlink(missing_ok=True)
        print(f"CLEANED {safe(out)}")
    return verdict(report)


def build_parser() -> Parser:
    parser = Parser(
        description="Read-only audit of declared Skill resources and CLI contracts."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    audit = sub.add_parser("audit", help="check declared resources and --help positionals")
    audit.add_argument("target", help="skill directory or installed skill name")
    audit.add_argument(
        "--skills-root",
        action="append",
        type=Path,
        default=[],
        help="root used to resolve skill names; repeatable",
    )
    audit.add_argument(
        "--help-probe",
        action="store_true",
        help="run '<script> --help' for declared scripts (never runs them without --help)",
    )
    audit.add_argument(
        "--expect",
        action="append",
        type=parse_expect,
        default=[],
        metavar="REL=SHAPE",
        help=f"expected CLI shape for a declared script; {SHAPE_LIST}",
    )
    audit.add_argument(
        "--timeout",
        type=positive_int,
        default=10,
        help="seconds allowed for each --help probe (default: 10)",
    )
    audit.add_argument(
        "--max-report",
        type=positive_int,
        default=10,
        help="maximum differences listed per check (default: 10)",
    )

    compare = sub.add_parser("compare", help="structural parity fallback")
    compare.add_argument("source", type=Path, help="authoritative source markdown")
    compare.add_argument("translation", type=Path, help="translated markdown")
    compare.add_argument(
        "--max-report",
        type=positive_int,
        default=10,
        help="maximum differences listed per check (default: 10)",
    )

    mutate = sub.add_parser(
        "mutate", help="mutate a copy and require the validator to fail"
    )
    mutate.add_argument(
        "source", nargs="?", type=Path, help="authoritative markdown (kind mode)"
    )
    mutate.add_argument("--out", type=Path, help="copy to write (kind mode)")
    mutate.add_argument(
        "--kind",
        choices=sorted(MUTATIONS),
        help="deterministic mutation kind (kind mode)",
    )
    mutate.add_argument(
        "--validator",
        help="command template containing {target} (kind mode)",
    )
    mutate.add_argument("--copy", type=Path, help="file to copy (replace mode)")
    mutate.add_argument("--replace", help="exact text to replace (replace mode)")
    mutate.add_argument(
        "--with", dest="with_text", help="replacement text (replace mode)"
    )
    mutate.add_argument(
        "--occurrence",
        type=positive_int,
        default=1,
        help="1-based occurrence to replace (default: 1)",
    )
    mutate.add_argument(
        "--workdir",
        type=Path,
        default=Path(".qoder/tmp/negative"),
        help="directory for the mutated copy (default: .qoder/tmp/negative)",
    )
    mutate.add_argument(
        "--keep",
        action="store_true",
        help="keep the mutated copy and print its path",
    )
    mutate.add_argument(
        "--expect-exit",
        type=positive_int,
        default=1,
        help="validator exit code that proves the mutation was detected (default: 1)",
    )
    mutate.add_argument(
        "--timeout",
        type=positive_int,
        default=60,
        help="seconds allowed for the validator (default: 60)",
    )
    return parser


def main(argv=None) -> int:
    configure_streams()
    argv = list(sys.argv[1:] if argv is None else argv)
    validator_argv: list[str] = []
    if argv[:1] == ["mutate"] and "--" in argv:
        cut = argv.index("--")
        argv, validator_argv = argv[:cut], argv[cut + 1:]
    args = build_parser().parse_args(argv)
    if args.command == "audit":
        return run_audit(args)
    if args.command == "mutate":
        args.validator_argv = validator_argv
        return run_mutate(args)
    return run_compare(args)


if __name__ == "__main__":
    raise SystemExit(main())
