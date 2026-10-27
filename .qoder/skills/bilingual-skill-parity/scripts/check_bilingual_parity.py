#!/usr/bin/env python3
"""Static bilingual parity checks for a SKILL.md. Read-only; never executes skill code."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

NAME_RE = re.compile(r"^[a-z0-9-]+$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_OPEN_RE = re.compile(r"^\s*```\s*([^\s`]*)")
FENCE_CLOSE_RE = re.compile(r"^\s*```\s*$")
INLINE_RE = re.compile(r"`([^`\n]+)`")
CHECKLIST_RE = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+")
ORDERED_RE = re.compile(r"^\s*\d+[.)]\s+")
NUMBER_RE = re.compile(r"\d+(?:[ \u00a0\u202f,'\u2019]\d+)*")
DIVIDER_RE = re.compile(
    r"^##\s+(?=.*(?:chinois|chinoise|\u4e2d\u6587))(?=.*(?:compl|\u5b8c\u6574)).*$",
    re.IGNORECASE,
)


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


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
        return None, None, "SKILL.md must start with a '---' frontmatter line"
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return None, None, "frontmatter closing '---' not found"
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1:]), None


def normalize_code(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def scan_fences(lines: list[str]):
    blocks = []
    fence_lines = set()
    in_fence = False
    lang = ""
    buffer = []
    for index, line in enumerate(lines):
        if in_fence and FENCE_CLOSE_RE.match(line):
            in_fence = False
            fence_lines.add(index)
            blocks.append((lang, normalize_code("\n".join(buffer))))
            buffer = []
            continue
        if not in_fence:
            match = FENCE_OPEN_RE.match(line)
            if match:
                in_fence = True
                lang = (match.group(1) or "").lower()
                fence_lines.add(index)
                buffer = []
            continue
        fence_lines.add(index)
        buffer.append(line)
    if in_fence:
        raise ValueError("unclosed fenced code block")
    return blocks, fence_lines


def masked_lines(lines: list[str], fence_lines: set[int]) -> list[str]:
    return ["" if index in fence_lines else line for index, line in enumerate(lines)]


def split_cells(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [cell.strip() for cell in text.split("|")]


def is_table_separator(line: str) -> bool:
    if "|" not in line:
        return False
    cells = split_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def extract_tables(lines: list[str], fence_lines: set[int]):
    table_lines = masked_lines(lines, fence_lines)
    tables = []
    index = 0
    while index < len(table_lines) - 1:
        header = table_lines[index]
        separator = table_lines[index + 1]
        if "|" in header and is_table_separator(separator):
            columns = len(split_cells(header))
            row_widths = []
            cursor = index + 2
            while cursor < len(table_lines):
                row = table_lines[cursor]
                if not row.strip() or "|" not in row:
                    break
                row_widths.append(len(split_cells(row)))
                cursor += 1
            tables.append((len(row_widths), columns, tuple(row_widths)))
            index = cursor
        else:
            index += 1
    return tables


def count_checklist(lines: list[str], fence_lines: set[int]) -> int:
    return sum(
        1
        for index, line in enumerate(lines)
        if index not in fence_lines and CHECKLIST_RE.match(line)
    )


def extract_inline(lines: list[str], fence_lines: set[int]) -> Counter:
    tokens = []
    for index, line in enumerate(lines):
        if index in fence_lines:
            continue
        for match in INLINE_RE.finditer(line):
            tokens.append(match.group(1).strip())
    return Counter(tokens)


def extract_numbers(lines: list[str], fence_lines: set[int]) -> Counter:
    numbers = []
    for index, line in enumerate(lines):
        if index in fence_lines:
            continue
        stripped = INLINE_RE.sub(" ", line)
        stripped = ORDERED_RE.sub("", stripped)
        for match in NUMBER_RE.finditer(stripped):
            raw = match.group(0)
            numbers.append(re.sub(r"[ \u00a0\u202f,'\u2019]", "", raw))
    return Counter(numbers)


def collect_headings(lines: list[str], fence_lines: set[int], level: int | None = None):
    headings = []
    for index, line in enumerate(lines):
        if index in fence_lines:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        heading_level = len(match.group(1))
        if level is None or heading_level == level:
            headings.append((index, heading_level, match.group(2).strip()))
    return headings


def has_second_frontmatter(body: str) -> bool:
    lines = body.splitlines()
    try:
        _, fence_lines = scan_fences(lines)
    except ValueError:
        fence_lines = set()
    for index in range(len(lines) - 1):
        if index in fence_lines:
            continue
        if (
            lines[index].strip() == "---"
            and index + 1 not in fence_lines
            and re.match(r"^\s*name\s*:", lines[index + 1])
        ):
            return True
    return False


def check_frontmatter(frontmatter: str, body: str, skill_dir: Path, report: Reporter):
    if yaml is None:
        report.fail("environment: PyYAML is not installed")
        return None
    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        report.fail(f"frontmatter: YAML parse error: {exc}")
        return None
    if not isinstance(data, dict):
        report.fail("frontmatter: expected a mapping")
        return None
    name = data.get("name")
    description = data.get("description")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        report.fail("frontmatter: 'name' must be hyphen-case")
        return None
    if name != skill_dir.name:
        report.fail(
            f"frontmatter: name '{name}' does not match directory '{skill_dir.name}'"
        )
        return None
    if not isinstance(description, str) or not description.strip():
        report.fail("frontmatter: 'description' must be a non-empty string")
        return None
    if "\n" in description:
        report.fail("frontmatter: 'description' spans multiple lines")
        return None
    if len(description) > 1024:
        report.fail(f"frontmatter: description is {len(description)} chars (> 1024)")
        return None
    desc_lines = [
        line for line in frontmatter.splitlines() if re.match(r"^description\s*:", line)
    ]
    if len(desc_lines) != 1:
        report.fail(
            f"frontmatter: expected one description key, found {len(desc_lines)}"
        )
        return None
    raw_value = desc_lines[0].split(":", 1)[1].strip()
    if ": " in raw_value and not raw_value.startswith(('"', "'")):
        report.fail("frontmatter: quote a description containing ': '")
        return None
    try:
        node = yaml.compose(frontmatter)
    except yaml.YAMLError as exc:
        report.fail(f"frontmatter: YAML compose error: {exc}")
        return None
    span_ok = False
    if isinstance(node, yaml.MappingNode):
        for key_node, value_node in node.value:
            if isinstance(key_node, yaml.ScalarNode) and key_node.value == "description":
                span_ok = value_node.end_mark.line == value_node.start_mark.line
                break
    if not span_ok:
        report.fail("frontmatter: 'description' is not single-line in source")
        return None
    if has_second_frontmatter(body):
        report.fail("frontmatter: a second frontmatter block was found in the body")
        return None
    return description


def compare_section(primary_lines: list[str], secondary_lines: list[str]):
    issues = []
    try:
        primary_code, primary_fences = scan_fences(primary_lines)
        secondary_code, secondary_fences = scan_fences(secondary_lines)
    except ValueError as exc:
        return [str(exc)]
    if len(primary_code) != len(secondary_code):
        issues.append(
            f"code blocks primary={len(primary_code)} secondary={len(secondary_code)}"
        )
    else:
        for index, (primary_block, secondary_block) in enumerate(
            zip(primary_code, secondary_code), 1
        ):
            if primary_block[0] != secondary_block[0]:
                issues.append(
                    f"code block {index} language {primary_block[0]!r} != "
                    f"{secondary_block[0]!r}"
                )
            if primary_block[1] != secondary_block[1]:
                issues.append(f"code block {index} content differs")
    primary_tables = extract_tables(primary_lines, primary_fences)
    secondary_tables = extract_tables(secondary_lines, secondary_fences)
    if primary_tables != secondary_tables:
        issues.append(f"tables primary={primary_tables} secondary={secondary_tables}")
    primary_checklist = count_checklist(primary_lines, primary_fences)
    secondary_checklist = count_checklist(secondary_lines, secondary_fences)
    if primary_checklist != secondary_checklist:
        issues.append(
            f"checklist primary={primary_checklist} secondary={secondary_checklist}"
        )
    primary_inline = extract_inline(primary_lines, primary_fences)
    secondary_inline = extract_inline(secondary_lines, secondary_fences)
    if primary_inline != secondary_inline:
        missing = list((primary_inline - secondary_inline).elements())[:5]
        extra = list((secondary_inline - primary_inline).elements())[:5]
        issues.append(f"inline tokens missing={missing} extra={extra}")
    primary_numbers = extract_numbers(primary_lines, primary_fences)
    secondary_numbers = extract_numbers(secondary_lines, secondary_fences)
    if primary_numbers != secondary_numbers:
        missing = list((primary_numbers - secondary_numbers).elements())[:5]
        extra = list((secondary_numbers - primary_numbers).elements())[:5]
        issues.append(f"numbers missing={missing} extra={extra}")
    return issues


def slice_sections(lines: list[str], headings):
    sections = []
    for position, (start, _, title) in enumerate(headings):
        end = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        sections.append((title, lines[start:end]))
    return sections


def finish(report: Reporter) -> int:
    print(
        f"Summary: {report.passed} pass, {report.failed} fail, {report.warned} warn"
    )
    if report.failed:
        print("RESULT FAIL")
        return 1
    print("RESULT PASS")
    return 0


def validate(skill_dir: Path, max_lines: int, divider_arg: str | None) -> int:
    report = Reporter()
    skill_file = skill_dir / "SKILL.md"
    print(f"Skill: {ascii_text(skill_dir.name)}")
    print(f"File: {ascii_text(skill_file)}")
    if not skill_file.is_file():
        print(f"FAIL environment: missing {ascii_text(skill_file)}")
        print("RESULT FAIL")
        return 2
    raw = skill_file.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        report.warn("encoding: UTF-8 BOM detected")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        print(f"FAIL environment: SKILL.md is not valid UTF-8: {ascii_text(exc)}")
        print("RESULT FAIL")
        return 2
    frontmatter, body, error = split_frontmatter(text)
    if error:
        report.fail(error)
        return finish(report)
    description = check_frontmatter(frontmatter, body, skill_dir, report)
    if description is None:
        return finish(report)
    report.ok(
        f"frontmatter: YAML parsed; name matches directory; "
        f"description single line ({len(description)} chars)"
    )
    body_lines = body.splitlines()
    if len(body_lines) >= max_lines:
        report.fail(f"body: {len(body_lines)} lines is not under {max_lines}")
    else:
        report.ok(f"body: {len(body_lines)} lines (< {max_lines})")
    try:
        _, body_fence_lines = scan_fences(body_lines)
    except ValueError as exc:
        report.fail(f"markdown: {exc}")
        return finish(report)
    candidates = []
    for index, line in enumerate(body_lines):
        if index in body_fence_lines:
            continue
        match = HEADING_RE.match(line)
        if not match or len(match.group(1)) != 2:
            continue
        title = match.group(2).strip()
        if divider_arg:
            if divider_arg in title:
                candidates.append((index, title))
        elif DIVIDER_RE.match(line):
            candidates.append((index, title))
    if not candidates:
        report.fail(
            "languages: second complete language divider not found "
            "(a summary-only second language is not accepted)"
        )
        return finish(report)
    if len(candidates) > 1:
        report.fail(
            f"languages: ambiguous second language divider, found {len(candidates)}"
        )
        return finish(report)
    divider_index, _ = candidates[0]
    primary_lines = body_lines[:divider_index]
    secondary_lines = body_lines[divider_index + 1:]
    try:
        primary_code, primary_fences = scan_fences(primary_lines)
        secondary_code, secondary_fences = scan_fences(secondary_lines)
    except ValueError as exc:
        report.fail(f"markdown: {exc}")
        return finish(report)
    primary_headings = collect_headings(primary_lines, primary_fences, level=2)
    secondary_headings = collect_headings(secondary_lines, secondary_fences, level=3)
    if not primary_headings:
        report.fail("languages: primary block has no H2 sections")
        return finish(report)
    if not secondary_headings:
        report.fail("languages: secondary block has no H3 sections")
        return finish(report)
    for _, level, title in collect_headings(primary_lines, primary_fences):
        if level not in (1, 2):
            report.fail(
                f"languages: primary heading '{title}' is H{level}, expected H1 or H2"
            )
            return finish(report)
    for _, level, title in collect_headings(secondary_lines, secondary_fences):
        if level != 3:
            report.fail(
                f"languages: secondary heading '{title}' is H{level}, expected H3"
            )
            return finish(report)
    if len(primary_headings) != len(secondary_headings):
        report.fail(
            f"languages: primary {len(primary_headings)} sections, "
            f"secondary {len(secondary_headings)} sections"
        )
        return finish(report)
    report.ok(
        f"languages: primary {len(primary_headings)} sections, "
        f"secondary {len(secondary_headings)} sections"
    )
    primary_sections = slice_sections(primary_lines, primary_headings)
    secondary_sections = slice_sections(secondary_lines, secondary_headings)
    section_failures = 0
    for index, (primary, secondary) in enumerate(
        zip(primary_sections, secondary_sections), 1
    ):
        issues = compare_section(primary[1], secondary[1])
        if issues:
            report.fail(f"section {index}: " + "; ".join(issues))
            section_failures += 1
    if not section_failures:
        report.ok(
            f"sections: {len(primary_sections)}/{len(secondary_sections)} pairs match "
            "(tables, code, checklist, inline tokens, numbers)"
        )
    return finish(report)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Static bilingual parity checks for a SKILL.md."
    )
    parser.add_argument(
        "skill_dir",
        nargs="?",
        default=".",
        help="directory containing SKILL.md (default: current directory)",
    )
    parser.add_argument(
        "--divider",
        default=None,
        help="substring of the H2 heading that starts the second language block",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=500,
        help="maximum body lines excluding frontmatter (default: 500)",
    )
    args = parser.parse_args(argv)
    skill_dir = Path(args.skill_dir).expanduser().resolve()
    if not skill_dir.is_dir():
        print(f"FAIL environment: skill directory not found: {ascii_text(skill_dir)}")
        print("RESULT FAIL")
        return 2
    if args.max_lines < 1:
        print("FAIL environment: --max-lines must be positive")
        print("RESULT FAIL")
        return 2
    try:
        return validate(skill_dir, args.max_lines, args.divider)
    except Exception as exc:
        print(f"FAIL environment: {ascii_text(type(exc).__name__)}: {ascii_text(exc)}")
        print("RESULT FAIL")
        return 2


if __name__ == "__main__":
    sys.exit(main())
