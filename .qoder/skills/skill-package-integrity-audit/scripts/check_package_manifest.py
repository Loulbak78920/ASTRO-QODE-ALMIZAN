#!/usr/bin/env python3
"""Read-only audit of a Skill package manifest and cache residue."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

ALLOWED_DIRS = {"scripts", "references", "assets"}
ALLOWED_FILES = {"SKILL.md", ".gitattributes"}
CACHE_DIRS = {"__pycache__"}
CACHE_SUFFIXES = {".pyc", ".pyo"}
QA_RE = re.compile(r"^Files \((\d+)\):", re.MULTILINE)


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def format_mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(
            timespec="seconds"
        )
    except (OSError, OverflowError, ValueError):
        return "unknown"


def collect(skill: Path) -> tuple[list[str], list[str], list[str], list[str]]:
    all_files: list[str] = []
    for path in skill.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(skill)
        if ".git" in rel.parts:
            continue
        all_files.append(rel.as_posix())
    all_files.sort()

    caches: list[str] = []
    clean: list[str] = []
    for rel in all_files:
        parts = rel.split("/")
        if any(part in CACHE_DIRS for part in parts):
            caches.append(rel)
        elif Path(rel).suffix.lower() in CACHE_SUFFIXES:
            caches.append(rel)
        else:
            clean.append(rel)

    unexpected: list[str] = []
    for rel in clean:
        if rel in ALLOWED_FILES:
            continue
        parts = rel.split("/")
        if len(parts) > 1 and parts[0] in ALLOWED_DIRS:
            continue
        unexpected.append(rel)
    return all_files, clean, caches, unexpected


def parse_qa(path: Path) -> tuple[int | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return None, f"unreadable: {exc}"
    matches = QA_RE.findall(text.replace("\r", ""))
    if not matches:
        return None, "absent"
    return int(matches[-1]), None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Skill package manifest and cache audit."
    )
    parser.add_argument("skill", help="Skill directory")
    parser.add_argument("--qa-log", help="saved skill-file-qa output to compare Files (N)")
    args = parser.parse_args(argv)

    configure_stdout()
    skill = Path(args.skill).expanduser()
    if not skill.is_dir():
        print(f"FAIL usage: directory not found: {ascii_text(skill)}")
        print("RESULT FAIL")
        return 2
    skill = skill.resolve()
    if not (skill / "SKILL.md").is_file():
        print(f"FAIL usage: SKILL.md absent from {ascii_text(skill)}")
        print("RESULT FAIL")
        return 2

    all_files, clean, caches, unexpected = collect(skill)
    qa_n: int | None = None
    qa_error: str | None = None
    if args.qa_log:
        qa_path = Path(args.qa_log).expanduser()
        if not qa_path.is_file():
            print(f"FAIL usage: QA log not found: {ascii_text(qa_path)}")
            print("RESULT FAIL")
            return 2
        qa_n, qa_error = parse_qa(qa_path)

    print(f"Skill: {ascii_text(skill.name)}")
    print(
        f"All files: {len(all_files)} | Clean: {len(clean)} | "
        f"Caches: {len(caches)} | Unexpected: {len(unexpected)}"
    )
    for rel in caches:
        path = skill / rel
        try:
            size = path.stat().st_size
        except OSError:
            size = "?"
        print(f"CACHE {ascii_text(rel)} | mtime={format_mtime(path)} | size={size}")
    for rel in unexpected:
        print(f"UNEXPECTED {ascii_text(rel)}")

    failed = bool(caches or unexpected)
    if args.qa_log:
        if qa_n is None:
            print(f"QA Files (N): ABSENT ({qa_error})")
            failed = True
        elif qa_n == len(all_files):
            print(f"QA Files (N): {qa_n} | MATCH on-disk total {len(all_files)}")
        else:
            print(f"QA Files (N): {qa_n} | MISMATCH on-disk total {len(all_files)}")
            failed = True
    else:
        print("QA Files (N): NOT CHECKED")

    if caches:
        print(
            "NOTE: read-only; remove only session-created caches after listing "
            "and provenance check."
        )
    print("RESULT FAIL" if failed else "RESULT PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
