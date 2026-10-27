#!/usr/bin/env python3
"""Read-only snapshot and comparison of an installed Skill package.

snapshot <skill_dir> emits a JSON baseline on stdout.
compare <skill_dir> --baseline <file> [--expect-skill-sha <sha>] re-reads the
package and reports files added, removed or modified, __pycache__ growth and,
optionally, the SKILL.md hash against an expected value.

Never writes. Output is ASCII-only JSON on one line.
Exit codes: 0 identical, 1 changed, 2 environment error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_CHANGED = 1
EXIT_ENV = 2


class EnvError(Exception):
    pass


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        emit({"ok": False, "error": "usage: " + message})
        raise SystemExit(EXIT_ENV)


def emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")
    sys.stdout.flush()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(skill_dir: Path) -> dict:
    if not skill_dir.is_dir():
        raise EnvError("skill directory not found: " + str(skill_dir))
    if not (skill_dir / "SKILL.md").is_file():
        raise EnvError("SKILL.md not found in " + str(skill_dir))
    files = []
    pycache = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(skill_dir).as_posix()
        parts = relative.split("/")
        if "__pycache__" in parts or relative.endswith(".pyc"):
            pycache.append(relative)
            continue
        stat = path.stat()
        files.append(
            {
                "path": relative,
                "bytes": stat.st_size,
                "sha256": sha256_file(path),
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    skill = next((item for item in files if item["path"] == "SKILL.md"), None)
    if skill is None:
        raise EnvError("SKILL.md missing from file list: " + str(skill_dir))
    return {
        "files": files,
        "pycache": pycache,
        "skill_sha256": skill["sha256"],
        "skill_bytes": skill["bytes"],
    }


def command_snapshot(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    state = collect(skill_dir)
    emit(
        {
            "command": "snapshot",
            "ok": True,
            "skill_dir": str(skill_dir),
            "file_count": len(state["files"]),
            "files": state["files"],
            "pycache": state["pycache"],
            "pycache_count": len(state["pycache"]),
            "skill_sha256": state["skill_sha256"],
            "skill_bytes": state["skill_bytes"],
        }
    )
    return EXIT_OK


def load_baseline(path: Path) -> dict:
    if not path.is_file():
        raise EnvError("baseline not found: " + str(path))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise EnvError("cannot parse baseline: " + str(exc))
    if not isinstance(data, dict) or not isinstance(data.get("files"), list):
        raise EnvError("baseline has no files list: " + str(path))
    for item in data["files"]:
        if not isinstance(item, dict) or "path" not in item or "sha256" not in item:
            raise EnvError("baseline entry missing path or sha256: " + str(path))
    if not data.get("skill_sha256"):
        raise EnvError("baseline has no skill_sha256: " + str(path))
    return data


def command_compare(args) -> int:
    skill_dir = Path(args.skill_dir).resolve()
    baseline = load_baseline(Path(args.baseline))
    state = collect(skill_dir)
    before = {item["path"]: item["sha256"] for item in baseline["files"]}
    after = {item["path"]: item["sha256"] for item in state["files"]}
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(path for path in set(before) & set(after) if before[path] != after[path])
    pycache_before = list(baseline.get("pycache") or [])
    pycache_added = sorted(set(state["pycache"]) - set(pycache_before))
    expected = args.expect_skill_sha.lower() if args.expect_skill_sha else None
    sha_matches = None if expected is None else expected == state["skill_sha256"]
    changed = bool(added or removed or modified or pycache_added) or sha_matches is False
    emit(
        {
            "command": "compare",
            "ok": not changed,
            "verdict": "CHANGED" if changed else "SAME",
            "skill_dir": str(skill_dir),
            "baseline_skill_dir": baseline.get("skill_dir"),
            "added": added,
            "removed": removed,
            "modified": modified,
            "file_count": len(after),
            "baseline_file_count": len(before),
            "pycache_now": state["pycache"],
            "pycache_added": pycache_added,
            "skill_sha256": state["skill_sha256"],
            "expected_skill_sha256": expected,
            "skill_sha_matches": sha_matches,
        }
    )
    return EXIT_CHANGED if changed else EXIT_OK


def main(argv: list) -> int:
    parser = JsonParser(prog="acceptance_snapshot.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot", help="emit a JSON baseline")
    snap.add_argument("skill_dir")
    comp = sub.add_parser("compare", help="compare a package with a baseline")
    comp.add_argument("skill_dir")
    comp.add_argument("--baseline", required=True)
    comp.add_argument("--expect-skill-sha", default=None)
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        return command_snapshot(args)
    return command_compare(args)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except EnvError as exc:
        emit({"ok": False, "error": str(exc)})
        sys.exit(EXIT_ENV)
