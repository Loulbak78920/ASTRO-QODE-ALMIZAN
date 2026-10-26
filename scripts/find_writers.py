#!/usr/bin/env python3
"""Read-only attribution of Skill writers from Qoder session JSONL files.

Scans session JSONL under --jsonl-dir, keeps tool_use records named Write/Edit
whose input.file_path is inside --target, and reports the latest timestamp per
session. Never writes, fetches, or modifies any file.

Exit codes: 0 writer(s) found, 1 none found, 2 usage/environment error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Iterator

MAX_FILES_DEFAULT = 500
ACTIONS = ("Write", "Edit")


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def norm(path: str) -> str:
    return os.path.normcase(os.path.abspath(path)).replace("\\", "/")


def in_target(file_path: str, target: str) -> bool:
    candidate = norm(file_path).rstrip("/")
    base = norm(target).rstrip("/")
    return candidate == base or candidate.startswith(base + "/")


def iso_timestamp(value: object) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        seconds = value / 1000 if value > 1e11 else float(value)
        try:
            moment = dt.datetime.fromtimestamp(seconds, dt.timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
        return moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            moment = dt.datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
        except ValueError:
            return text
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=dt.timezone.utc)
        return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return None


def iter_tool_uses(node: object) -> Iterator[dict]:
    stack = [node]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            if current.get("type") == "tool_use" and current.get("name") in ACTIONS:
                yield current
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)


def scan_file(path: Path, target: str, best: dict[str, tuple[str, str, str, int]]) -> dict[str, int]:
    stats = {"malformed": 0, "no_timestamp": 0}
    session = path.stem
    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        stats["malformed"] += 1
        return stats
    with handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                stats["malformed"] += 1
                continue
            if not isinstance(record, dict):
                stats["malformed"] += 1
                continue
            timestamp = iso_timestamp(record.get("timestamp"))
            if timestamp is None:
                if any(True for _ in iter_tool_uses(record)):
                    stats["no_timestamp"] += 1
                continue
            for tool_use in iter_tool_uses(record):
                payload = tool_use.get("input") or {}
                if not isinstance(payload, dict):
                    continue
                file_path = payload.get("file_path")
                if not isinstance(file_path, str) or not file_path.strip():
                    continue
                if not in_target(file_path, target):
                    continue
                rel = os.path.relpath(os.path.abspath(file_path), os.path.abspath(target)).replace("\\", "/")
                action = str(tool_use.get("name"))
                current = best.get(session)
                count = 1 if current is None else current[3] + 1
                if current is None or timestamp > current[0]:
                    best[session] = (timestamp, action, rel, count)
                else:
                    best[session] = (current[0], current[1], current[2], count)
    return stats


def file_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def main() -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Read-only attribution of Skill writers from session JSONL files.",
    )
    parser.add_argument("--target", required=True, help="Skill directory matched against input.file_path")
    parser.add_argument("--jsonl-dir", required=True, help="Directory containing session *.jsonl files")
    parser.add_argument(
        "--session",
        action="append",
        default=[],
        help="Only sessions whose filename starts with this prefix; repeatable",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=MAX_FILES_DEFAULT,
        help="Maximum JSONL files to scan, most recent first",
    )
    args = parser.parse_args()

    target = os.path.abspath(os.path.expanduser(args.target))
    jsonl_dir = os.path.abspath(os.path.expanduser(args.jsonl_dir))
    if not os.path.isdir(target):
        print(f"RESULT FAIL target not a directory: {ascii_text(target)}")
        return 2
    if not os.path.isdir(jsonl_dir):
        print(f"RESULT FAIL jsonl-dir not a directory: {ascii_text(jsonl_dir)}")
        return 2
    if args.max_files < 1:
        print("RESULT FAIL --max-files must be >= 1")
        return 2

    try:
        files = [
            Path(entry.path)
            for entry in os.scandir(jsonl_dir)
            if entry.is_file() and entry.name.lower().endswith(".jsonl")
        ]
    except OSError as exc:
        print(f"RESULT FAIL cannot read jsonl-dir: {ascii_text(exc)}")
        return 2

    if args.session:
        prefixes = tuple(args.session)
        files = [path for path in files if path.stem.startswith(prefixes)]
    files = sorted(files, key=file_mtime, reverse=True)
    scanned = files[: args.max_files]

    if not scanned:
        print("RESULT NONE")
        print("NOTE files=0 scanned=0 malformed=0 no_timestamp=0")
        return 1

    best: dict[str, tuple[str, str, str, int]] = {}
    totals = {"malformed": 0, "no_timestamp": 0}
    for path in scanned:
        stats = scan_file(path, target, best)
        totals["malformed"] += stats["malformed"]
        totals["no_timestamp"] += stats["no_timestamp"]

    if not best:
        print("RESULT NONE")
        print(
            f"NOTE files={len(files)} scanned={len(scanned)} "
            f"malformed={totals['malformed']} no_timestamp={totals['no_timestamp']}"
        )
        return 1

    for session in sorted(best, key=lambda name: best[name][0]):
        timestamp, action, rel, count = best[session]
        print(
            f"SESSION {ascii_text(session)} | last {timestamp} | {action} | "
            f"{ascii_text(rel)} | records {count}"
        )

    last_session = max(best, key=lambda name: best[name][0])
    last_timestamp = best[last_session][0]
    print(f"RESULT FOUND {len(best)} session(s) | last {last_timestamp} | {ascii_text(last_session)}")
    print(
        f"NOTE files={len(files)} scanned={len(scanned)} "
        f"malformed={totals['malformed']} no_timestamp={totals['no_timestamp']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
