#!/usr/bin/env python3
"""Audit a relocated skill for stale install-location narratives.

Counts literal path prefixes in every text file and flags location/scope
statements in SKILL.md and references for manual classification. It never
rewrites files.

Exit codes: 0 audit completed (RESULT PASS or REVIEW), 1 hard inconsistency
(old prefix remains, or the old directory still exists), 2 usage/input error.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

TEXT_EXTS = {
    ".md", ".txt", ".py", ".js", ".cjs", ".mjs", ".json", ".yaml", ".yml",
    ".sh", ".ps1", ".bat", ".toml", ".csv", ".html", ".htm",
}
DOC_EXTS = {".md", ".txt"}
SKIP_DIRS = {"__pycache__", ".git", ".qoder", "node_modules", ".venv"}
MAX_BYTES = 2 * 1024 * 1024
MAX_HITS = 60
LOCATION_PHRASES = (
    "未移动", "仍在", "已不存在", "现仅", "仅当前项目", "仅在本项目",
    "仅本项目", "本机", "用户级", "项目级", "用户目录", "项目目录",
    "可用范围", "归属", "其他项目", "另一项目", "当前项目可见",
    "user-level", "project-level", "user directory", "project directory",
    "not moved", "only visible", "other projects", "current project",
    "install location", "installation scope",
)


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix.lower() == ".pyc":
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
        except OSError:
            continue
        yield path


def read_text(path: Path) -> str | None:
    if path.suffix.lower() not in TEXT_EXTS:
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def normalize_spelling(value: str) -> str:
    text = value.replace("\\", "/")
    text = re.sub(r"/{2,}", "/", text)
    if len(text) > 2 and text[0] == "/" and text[1].isalpha() and text[2] == "/":
        text = f"{text[1]}:/{text[3:]}"
    return text.rstrip("/").lower()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit a relocated skill for stale location narratives."
    )
    parser.add_argument("skill_dir", type=Path, help="skill directory at its new location")
    parser.add_argument("--old-prefix", default="", help="literal absolute prefix before the move")
    parser.add_argument("--new-prefix", default="", help="literal absolute prefix after the move")
    parser.add_argument("--old-dir", type=Path, default=None, help="old skill directory that must be absent")
    args = parser.parse_args(argv)

    configure_stdout()
    skill_dir = args.skill_dir.expanduser()
    if not skill_dir.is_dir():
        print(f"ERROR skill directory not found: {skill_dir}")
        return 2
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(f"ERROR SKILL.md not found: {skill_md}")
        return 2
    if bool(args.old_prefix) != bool(args.new_prefix):
        print("ERROR pass --old-prefix and --new-prefix together, or neither")
        return 2

    print(f"Skill: {skill_dir}")
    files = list(iter_files(skill_dir))
    print(f"files: {len(files)}")
    print("--- hashes ---")
    for path in files:
        print(f"{sha256(path)}  {path.relative_to(skill_dir).as_posix()}")

    texts: dict[Path, str] = {}
    for path in files:
        text = read_text(path)
        if text is not None:
            texts[path] = text

    old_total = 0
    new_total = 0
    variant_review = False
    print("--- prefix counts ---")
    if args.old_prefix:
        for path, text in texts.items():
            old = text.count(args.old_prefix)
            new = text.count(args.new_prefix)
            old_total += old
            new_total += new
            if old or new:
                print(f"{path.relative_to(skill_dir).as_posix()}: old {old} / new {new}")
        print(f"TOTAL old {old_total} / new {new_total}")
        if old_total == 0 and new_total == 0:
            print("NOTE 0/0: no prefix to replace; location statements below still require classification.")
            norm_old = normalize_spelling(args.old_prefix)
            if len(norm_old) >= 8:
                variants = []
                for path, text in texts.items():
                    count = normalize_spelling(text).count(norm_old)
                    if count:
                        variants.append((path.relative_to(skill_dir).as_posix(), count))
                if variants:
                    variant_review = True
                    print("WARN old prefix not found literally; normalized matches exist:")
                    for rel, count in variants:
                        print(f"  {rel}: {count} normalized match(es)")
                    print("WARN pass the on-disk spelling (separators, drive letter, case) so counts are exact")
    else:
        print("skipped (pass --old-prefix and --new-prefix)")

    hits = []
    print("--- location statements (docs only) ---")
    for path, text in texts.items():
        if path.suffix.lower() not in DOC_EXTS:
            continue
        rel = path.relative_to(skill_dir).as_posix()
        for lineno, line in enumerate(text.splitlines(), 1):
            lowered = line.lower()
            for phrase in LOCATION_PHRASES:
                if phrase.lower() in lowered:
                    hits.append((rel, lineno, phrase, line.strip()))
                    break
    for rel, lineno, phrase, line in hits[:MAX_HITS]:
        print(f"{rel}:{lineno}: [{phrase}] {line[:160]}")
    if len(hits) > MAX_HITS:
        print(f"... truncated {len(hits) - MAX_HITS} more hit(s)")
    print(f"location statements: {len(hits)} (manual classification required: STALE / VALID / GENERIC)")

    print("--- old dir ---")
    old_dir_present = False
    if args.old_dir is None:
        print("OLD dir check: skipped")
    else:
        old_dir = args.old_dir.expanduser()
        if old_dir.exists():
            print(f"OLD_PRESENT {old_dir}")
            old_dir_present = True
        else:
            print(f"OLD_ABSENT {old_dir}")

    failed = old_total > 0 or old_dir_present
    if failed:
        if old_total > 0:
            print(f"FAIL old prefix still present: {old_total} occurrence(s)")
        if old_dir_present:
            print("FAIL old directory still exists: the move is not complete")
        print("RESULT FAIL")
        return 1
    print("RESULT REVIEW" if (hits or variant_review) else "RESULT PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
