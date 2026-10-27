#!/usr/bin/env python3
"""Read-only structural parity checks between a source document and its translation."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_OPEN_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([^\s`~]*)")
INLINE_RE = re.compile(r"`([^`\n]+)`")
CHECKLIST_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+")
ORDERED_RE = re.compile(r"^\s*\d+[.)]\s+")
NUMBER_RE = re.compile(r"\d+(?:[ \u00a0\u202f'\u2019]\d{3})*(?:[.,]\d+)?")
SHA_RE = re.compile(r"\b[0-9a-fA-F]{64}\b")
NAME_LINE_RE = re.compile(r"^name\s*:\s*(.+?)\s*$", re.MULTILINE)


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def brief(value: object, limit: int = 80) -> str:
    text = ascii_text(value)
    if len(text) > limit:
        return text[:limit] + "..."
    return text


class Reporter:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, message: str) -> None:
        self.passed += 1
        print(f"PASS {ascii_text(message)}")

    def fail(self, message: str) -> None:
        self.failed += 1
        print(f"FAIL {ascii_text(message)}")


def split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1:])
    raise ValueError("frontmatter closing '---' not found")


def frontmatter_name(frontmatter: str) -> str | None:
    match = NAME_LINE_RE.search(frontmatter)
    if not match:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def normalize_code(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalized.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def fence_closes(line: str, marker: str, length: int) -> bool:
    return bool(
        re.fullmatch(
            rf"\s*{re.escape(marker[0])}{{{length},}}\s*",
            line,
        )
    )


def scan_fences(lines: list[str]) -> tuple[list[tuple[str, str]], set[int]]:
    blocks = []
    fence_lines: set[int] = set()
    in_fence = False
    marker = ""
    marker_length = 0
    language = ""
    buffer: list[str] = []
    for index, line in enumerate(lines):
        if in_fence:
            if fence_closes(line, marker, marker_length):
                in_fence = False
                fence_lines.add(index)
                blocks.append((language, normalize_code("\n".join(buffer))))
                buffer = []
            else:
                fence_lines.add(index)
                buffer.append(line)
            continue
        match = FENCE_OPEN_RE.match(line)
        if match:
            in_fence = True
            marker = match.group(1)
            marker_length = len(marker)
            language = (match.group(2) or "").lower()
            fence_lines.add(index)
            buffer = []
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
    masked = masked_lines(lines, fence_lines)
    tables = []
    bad_rows = []
    index = 0
    while index < len(masked) - 1:
        header = masked[index]
        separator = masked[index + 1]
        if "|" in header and is_table_separator(separator):
            columns = len(split_cells(header))
            rows = 0
            cursor = index + 2
            while cursor < len(masked):
                row = masked[cursor]
                if not row.strip() or "|" not in row:
                    break
                width = len(split_cells(row))
                if width != columns:
                    bad_rows.append(
                        f"table {len(tables) + 1} row {rows + 2} width {width} != {columns}"
                    )
                rows += 1
                cursor += 1
            tables.append((rows + 1, columns))
            index = cursor
        else:
            index += 1
    return tables, bad_rows


def extract_heading_levels(lines: list[str], fence_lines: set[int]) -> list[int]:
    levels = []
    for index, line in enumerate(lines):
        if index in fence_lines:
            continue
        match = HEADING_RE.match(line)
        if match:
            levels.append(len(match.group(1)))
    return levels


def count_checklist(lines: list[str], fence_lines: set[int]) -> Counter:
    states: Counter = Counter()
    for index, line in enumerate(lines):
        if index in fence_lines:
            continue
        match = CHECKLIST_RE.match(line)
        if match:
            states[match.group(1).lower()] += 1
    return states


def extract_inline(lines: list[str], fence_lines: set[int]) -> Counter:
    tokens = []
    for index, line in enumerate(lines):
        if index in fence_lines:
            continue
        for match in INLINE_RE.finditer(line):
            token = match.group(1).strip()
            if token:
                tokens.append(token)
    return Counter(tokens)


def normalize_number(raw: str) -> str:
    value = re.sub(r"[ \u00a0\u202f'\u2019]", "", raw)
    grouped = re.fullmatch(r"(\d{1,3}(?:,\d{3})+)(?:\.(\d+))?", value)
    if grouped:
        integer = grouped.group(1).replace(",", "")
        return integer + ("." + grouped.group(2) if grouped.group(2) else "")
    if "," in value and "." not in value:
        return value.replace(",", ".")
    return value


def extract_numbers(lines: list[str], fence_lines: set[int]) -> Counter:
    numbers = []
    for index, line in enumerate(lines):
        if index in fence_lines:
            continue
        stripped = INLINE_RE.sub(" ", line)
        stripped = ORDERED_RE.sub("", stripped)
        for match in NUMBER_RE.finditer(stripped):
            numbers.append(normalize_number(match.group(0)))
    return Counter(numbers)


def extract_sha(lines: list[str], fence_lines: set[int]) -> Counter:
    hashes = []
    for index, line in enumerate(lines):
        if index in fence_lines:
            continue
        stripped = INLINE_RE.sub(" ", line)
        hashes.extend(match.lower() for match in SHA_RE.findall(stripped))
    return Counter(hashes)


def first_difference(left: str, right: str) -> tuple[int, str, str]:
    left_lines = left.split("\n")
    right_lines = right.split("\n")
    for index in range(min(len(left_lines), len(right_lines))):
        if left_lines[index] != right_lines[index]:
            return index + 1, left_lines[index], right_lines[index]
    if len(left_lines) != len(right_lines):
        index = min(len(left_lines), len(right_lines))
        left_value = left_lines[index] if index < len(left_lines) else "<missing>"
        right_value = right_lines[index] if index < len(right_lines) else "<missing>"
        return index + 1, left_value, right_value
    return 0, "", ""


def counter_diff(source: Counter, translation: Counter, limit: int):
    missing = sorted((source - translation).elements())[:limit]
    extra = sorted((translation - source).elements())[:limit]
    return missing, extra


def compare_pair(
    source: Path,
    translation: Path,
    max_report: int,
) -> int:
    report = Reporter()
    source_text = source.read_bytes().decode("utf-8-sig")
    translation_text = translation.read_bytes().decode("utf-8-sig")
    source_frontmatter, source_body = split_frontmatter(source_text)
    translation_frontmatter, translation_body = split_frontmatter(translation_text)

    source_name = frontmatter_name(source_frontmatter)
    translation_name = frontmatter_name(translation_frontmatter)
    if source_name and translation_name and source_name != translation_name:
        report.fail(
            f"frontmatter: name '{translation_name}' != source '{source_name}'"
        )
    elif translation_name and not source_name:
        report.fail(
            f"frontmatter: translation declares name '{translation_name}' but source has none"
        )
    elif source_name:
        report.ok(f"frontmatter: name '{source_name}' aligned")
    else:
        report.ok("frontmatter: no name key to compare")

    source_lines = source_body.splitlines()
    translation_lines = translation_body.splitlines()
    source_blocks, source_fences = scan_fences(source_lines)
    translation_blocks, translation_fences = scan_fences(translation_lines)

    if len(source_blocks) != len(translation_blocks):
        report.fail(
            f"code blocks: source={len(source_blocks)} translation={len(translation_blocks)}"
        )
    else:
        issues = []
        for index, (source_block, translation_block) in enumerate(
            zip(source_blocks, translation_blocks), 1
        ):
            if source_block[0] != translation_block[0]:
                issues.append(
                    f"block {index} language '{source_block[0]}' != '{translation_block[0]}'"
                )
            if source_block[1] != translation_block[1]:
                line, left, right = first_difference(
                    source_block[1], translation_block[1]
                )
                issues.append(
                    f"block {index} content differs at line {line}: "
                    f"{brief(left)} != {brief(right)}"
                )
        if issues:
            for issue in issues[:max_report]:
                report.fail(f"code block: {issue}")
        else:
            report.ok(
                f"code blocks: {len(source_blocks)} block(s), languages and content identical"
            )

    source_tables, source_bad_rows = extract_tables(source_lines, source_fences)
    translation_tables, translation_bad_rows = extract_tables(
        translation_lines, translation_fences
    )
    if source_bad_rows or translation_bad_rows:
        for issue in (source_bad_rows + translation_bad_rows)[:max_report]:
            report.fail(f"table width: {issue}")
    if source_tables != translation_tables:
        report.fail(
            f"tables: source={source_tables} translation={translation_tables}"
        )
    else:
        report.ok(f"tables: {len(source_tables)} table(s) {source_tables}")

    source_headings = extract_heading_levels(source_lines, source_fences)
    translation_headings = extract_heading_levels(
        translation_lines, translation_fences
    )
    if source_headings != translation_headings:
        report.fail(
            "headings: sequence source="
            f"{source_headings} translation={translation_headings}"
        )
    else:
        counts = Counter(source_headings)
        detail = " ".join(
            f"H{level}={counts[level]}" for level in sorted(counts)
        )
        report.ok(f"headings: {detail} (sequence aligned)")

    source_checklist = count_checklist(source_lines, source_fences)
    translation_checklist = count_checklist(translation_lines, translation_fences)
    if source_checklist != translation_checklist:
        report.fail(
            "checklist: "
            f"source unchecked={source_checklist[' ']} checked={source_checklist['x']} "
            f"translation unchecked={translation_checklist[' ']} "
            f"checked={translation_checklist['x']}"
        )
    else:
        report.ok(
            f"checklist: {sum(source_checklist.values())} item(s) "
            f"(unchecked={source_checklist[' ']} checked={source_checklist['x']})"
        )

    source_inline = extract_inline(source_lines, source_fences)
    translation_inline = extract_inline(translation_lines, translation_fences)
    missing, extra = counter_diff(source_inline, translation_inline, max_report)
    if missing or extra:
        report.fail(
            "inline tokens: "
            f"missing={[ascii_text(token) for token in missing]} "
            f"extra={[ascii_text(token) for token in extra]}"
        )
    else:
        report.ok(f"inline tokens: {sum(source_inline.values())} token(s) matched")

    source_numbers = extract_numbers(source_lines, source_fences)
    translation_numbers = extract_numbers(translation_lines, translation_fences)
    missing, extra = counter_diff(source_numbers, translation_numbers, max_report)
    if missing or extra:
        report.fail(
            "numbers: "
            f"missing={[ascii_text(token) for token in missing]} "
            f"extra={[ascii_text(token) for token in extra]}"
        )
    else:
        report.ok(f"numbers: {sum(source_numbers.values())} token(s) matched")

    source_sha = extract_sha(source_lines, source_fences)
    translation_sha = extract_sha(translation_lines, translation_fences)
    missing, extra = counter_diff(source_sha, translation_sha, max_report)
    if missing or extra:
        report.fail(
            "sha256: "
            f"missing={[ascii_text(token) for token in missing]} "
            f"extra={[ascii_text(token) for token in extra]}"
        )
    else:
        report.ok(f"sha256: {sum(source_sha.values())} hash(es) matched")

    print(f"Summary: {report.passed} pass, {report.failed} fail")
    if report.failed:
        print("RESULT FAIL")
        return 1
    print("RESULT PASS")
    return 0


def validate(source: Path, translation: Path, max_report: int) -> int:
    print(f"Source: {ascii_text(source)}")
    print(f"Translation: {ascii_text(translation)}")
    for path in (source, translation):
        if not path.is_file():
            print(f"FAIL environment: missing file {ascii_text(path)}")
            print("RESULT FAIL")
            return 2
    try:
        return compare_pair(source, translation, max_report)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(
            f"FAIL environment: {ascii_text(type(exc).__name__)}: {ascii_text(exc)}"
        )
        print("RESULT FAIL")
        return 2


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check structural parity between a source document and its translation."
    )
    parser.add_argument("source", help="authoritative source markdown file")
    parser.add_argument("translation", help="translated markdown file")
    parser.add_argument(
        "--max-report",
        type=int,
        default=10,
        help="maximum differences listed per check (default: 10)",
    )
    args = parser.parse_args(argv)
    if args.max_report < 1:
        print("FAIL environment: --max-report must be positive")
        print("RESULT FAIL")
        return 2
    source = Path(args.source).expanduser().resolve()
    translation = Path(args.translation).expanduser().resolve()
    return validate(source, translation, args.max_report)


if __name__ == "__main__":
    sys.exit(main())
