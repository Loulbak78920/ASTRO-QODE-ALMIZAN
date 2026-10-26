#!/usr/bin/env python3
"""Read-only capability coverage scan across installed Qoder Skills.

Enumerate user-level and project-level Skill roots, then search capability
tokens across each Skill's SKILL.md, references/ and scripts/.

Exit codes: 0 = RESULT OK or PARTIAL, 2 = RESULT FAIL (usage or environment).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", "node_modules", "assets", ".qoder"}
TEXT_SUFFIXES = {
    ".md", ".py", ".sh", ".ps1", ".js", ".cjs", ".mjs",
    ".json", ".yaml", ".yml", ".txt",
}
MAX_FILE_BYTES = 2_000_000
MAX_SNIPPET = 200
GENERIC_RATIO = 3


def setup_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def fail(message: str, code: int = 2) -> None:
    print("ERROR: " + message, file=sys.stderr)
    print("RESULT FAIL", file=sys.stderr)
    raise SystemExit(code)


def resolve_project_root(arg: str | None, user_root: Path) -> Path | None:
    if arg:
        path = Path(arg).expanduser().resolve()
        if not path.is_dir():
            fail("project root not found: {}".format(path))
        if path == user_root:
            fail("project root must differ from the user root: {}".format(path))
        return path
    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        path = candidate / ".qoder" / "skills"
        if path.is_dir() and path.resolve() != user_root:
            return path.resolve()
    return None


def discover(root: Path | None) -> list[Path]:
    if root is None:
        return []
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except OSError as exc:
        fail("cannot list {}: {}".format(root, exc))
    return [
        path
        for path in entries
        if path.is_dir() and not path.name.startswith(".") and (path / "SKILL.md").is_file()
    ]


def scan_files(skill: Path):
    yield skill / "SKILL.md"
    for sub in ("references", "scripts"):
        base = skill / sub
        if not base.is_dir():
            continue
        try:
            paths = sorted(base.rglob("*"))
        except OSError:
            continue
        for path in paths:
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.relative_to(skill).parts):
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path


def read_text(path: Path):
    try:
        return path.read_text(encoding="utf-8", errors="replace"), None
    except OSError as exc:
        return None, str(exc)


def compile_tokens(tokens: list[str], use_regex: bool, ignore_case: bool):
    patterns = []
    for token in tokens:
        if not use_regex:
            patterns.append(None)
            continue
        flags = re.IGNORECASE if ignore_case else 0
        try:
            patterns.append(re.compile(token, flags))
        except re.error as exc:
            fail("invalid regex for token {!r}: {}".format(token, exc))
    return patterns


def count_line(line: str, token: str, pattern, ignore_case: bool) -> int:
    if pattern is not None:
        return len(pattern.findall(line))
    if ignore_case:
        return line.lower().count(token.lower())
    return line.count(token)


def scan(token_list, skills, patterns, ignore_case, max_hits):
    results = [
        {"token": token, "occurrences": 0, "skills": []}
        for token in token_list
    ]
    errors = []
    for skill, label in skills:
        per_skill = {}
        budgets = [max_hits for _ in token_list]
        for path in scan_files(skill):
            text, error = read_text(path)
            if error is not None:
                errors.append("{}:{}".format(skill.name, error))
                continue
            rel = path.relative_to(skill).as_posix()
            for index, token in enumerate(token_list):
                occurrences = 0
                hits = []
                for number, line in enumerate(text.splitlines(), 1):
                    found = count_line(line, token, patterns[index], ignore_case)
                    if not found:
                        continue
                    occurrences += found
                    if len(hits) < budgets[index]:
                        hits.append({
                            "line": number,
                            "text": line.strip()[:MAX_SNIPPET],
                        })
                        budgets[index] -= 1
                if not occurrences:
                    continue
                per_skill.setdefault(index, []).append({
                    "path": rel,
                    "occurrences": occurrences,
                    "hits": hits,
                })
                results[index]["occurrences"] += occurrences
        for index, files in per_skill.items():
            results[index]["skills"].append({
                "root": label,
                "name": skill.name,
                "files": files,
            })
    return results, errors


def build_warnings(results, total: int) -> list[str]:
    warnings = []
    for result in results:
        count = len(result["skills"])
        if count == 0:
            warnings.append("TOKEN_NO_HIT {}".format(result["token"]))
        elif total and count * GENERIC_RATIO > total:
            warnings.append(
                "TOKEN_TOO_GENERIC {} skills={}/{}".format(
                    result["token"], count, total
                )
            )
    return warnings


def print_md(roots, counts, results, warnings, errors) -> None:
    print("ROOTS user={} project={}".format(
        roots["user"], roots["project"] or "none"
    ))
    print("SKILLS {} (user={} project={})".format(
        counts["total"], counts["user"], counts["project"]
    ))
    for result in results:
        print("TOKEN {} occurrences={} skills={}".format(
            result["token"],
            result["occurrences"],
            len(result["skills"]),
        ))
        for skill in result["skills"]:
            for file_entry in skill["files"]:
                for hit in file_entry["hits"]:
                    snippet = hit["text"].replace("|", "\\|")
                    print("  HIT {}|{}|{}|{}".format(
                        skill["name"], file_entry["path"], hit["line"], snippet
                    ))
    print("MATRIX")
    for result in results:
        for skill in result["skills"]:
            paths = ",".join(entry["path"] for entry in skill["files"])
            occurrences = sum(entry["occurrences"] for entry in skill["files"])
            print("  {}|{}|{}|{}".format(
                skill["name"], result["token"], occurrences, paths
            ))
    for warning in warnings:
        print("WARN " + warning)
    for error in errors:
        print("ERROR " + error)
    print("RESULT " + ("PARTIAL" if errors else "OK"))


def print_json(roots, counts, results, warnings, errors) -> None:
    payload = {
        "result": "PARTIAL" if errors else "OK",
        "roots": roots,
        "skills": {
            "total": counts["total"],
            "user": counts["user"],
            "project": counts["project"],
        },
        "tokens": results,
        "warnings": warnings,
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def print_skill_list(roots, counts, skills, fmt: str) -> None:
    if fmt == "json":
        payload = {
            "result": "OK",
            "roots": roots,
            "skills": {
                "total": counts["total"],
                "user": counts["user"],
                "project": counts["project"],
                "entries": [
                    {"root": label, "name": skill.name, "path": str(skill)}
                    for skill, label in skills
                ],
            },
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print("ROOTS user={} project={}".format(
        roots["user"], roots["project"] or "none"
    ))
    print("SKILLS {} (user={} project={})".format(
        counts["total"], counts["user"], counts["project"]
    ))
    for skill, label in skills:
        print("SKILL {}|{}|{}".format(label, skill.name, skill))
    print("RESULT OK")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only capability coverage scan across installed Qoder Skills."
    )
    parser.add_argument(
        "--user-root",
        default=str(Path.home() / ".qoder" / "skills"),
        help="user-level skills root (default: ~/.qoder/skills)",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="project-level skills root (default: nearest .qoder/skills)",
    )
    parser.add_argument(
        "--token",
        action="append",
        default=[],
        help="capability token to search (repeatable)",
    )
    parser.add_argument(
        "--regex",
        action="store_true",
        help="treat each --token value as a regular expression",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="match tokens case-sensitively (default: ignore case)",
    )
    parser.add_argument(
        "--max-hits-per-skill",
        type=int,
        default=20,
        help="maximum HIT lines printed per skill per token (default: 20)",
    )
    parser.add_argument(
        "--format",
        choices=("md", "json"),
        default="md",
        help="output format (default: md)",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="only enumerate Skill roots and names; no tokens required",
    )
    args = parser.parse_args(argv)

    user_root = Path(args.user_root).expanduser().resolve()
    if not user_root.is_dir():
        fail("user root not found: {}".format(user_root))
    project_root = resolve_project_root(args.project_root, user_root)
    roots = {
        "user": str(user_root),
        "project": str(project_root) if project_root else None,
    }

    user_skills = discover(user_root)
    project_skills = discover(project_root) if project_root else []
    skills = [(skill, "user") for skill in user_skills]
    skills += [(skill, "project") for skill in project_skills]
    counts = {
        "total": len(skills),
        "user": len(user_skills),
        "project": len(project_skills),
    }

    if args.list_skills:
        print_skill_list(roots, counts, skills, args.format)
        return 0

    tokens = []
    for raw in args.token:
        token = raw.strip()
        if token and token not in tokens:
            tokens.append(token)
    if not tokens:
        fail("provide at least one --token (or use --list-skills)")
    if args.max_hits_per_skill < 0:
        fail("--max-hits-per-skill must be >= 0")
    if not args.regex:
        too_short = [
            token for token in tokens if token.isascii() and len(token) < 3
        ]
        if too_short:
            fail(
                "ASCII literal tokens shorter than 3 chars are too generic: {}".format(
                    ", ".join(too_short)
                )
            )

    ignore_case = not args.case_sensitive
    patterns = compile_tokens(tokens, args.regex, ignore_case)
    results, errors = scan(
        tokens, skills, patterns, ignore_case, args.max_hits_per_skill
    )
    warnings = build_warnings(results, counts["total"])

    if args.format == "json":
        print_json(roots, counts, results, warnings, errors)
    else:
        print_md(roots, counts, results, warnings, errors)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
