#!/usr/bin/env python3
"""Read-only inventory of a Qoder temporary directory.

Scans the given root (default ~/.qoder/tmp) and reports top-level entries
with size/mtime/recent flags, nested .git directories and .git files,
system-commandline-sentinel-files directories, and __pycache__/.pyc build
artifacts. It never deletes, moves, renames or opens files for writing, and
it does not follow symbolic links.

This tool only inventories. It does not decide ownership and does not delete
anything; ownership still comes from session JSONL references and user
confirmation in the calling workflow.

Exit codes: 0 = RESULT OK or PARTIAL, 2 = RESULT FAIL (bad root or usage).
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import time
from datetime import datetime, timezone

DEFAULT_MAX_DEPTH = 5
DEFAULT_RECENT_MINUTES = 60
DEFAULT_ENTRY_LIMIT = 200000


def configure_stdout() -> None:
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, OSError):
        pass


def human_size(value: int) -> str:
    number = float(value)
    for unit in ("B", "K", "M", "G"):
        if number < 1024.0:
            return f"{number:.0f}B" if unit == "B" else f"{number:.1f}{unit}"
        number /= 1024.0
    return f"{number:.1f}T"


def iso_local(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")


def new_bucket(name: str, entry_type: str, mtime: float) -> dict:
    return {
        "name": name,
        "type": entry_type,
        "size_bytes": 0,
        "files": 0,
        "dirs": 0,
        "others": 0,
        "children": 0,
        "empty": False,
        "mtime": mtime,
        "nested_git": 0,
        "sentinel_dirs": 0,
        "pycache_dirs": 0,
        "pyc_files": 0,
        "git_root": False,
    }


def scan_tree(root: str, max_depth: int, entry_limit: int) -> dict:
    top: dict[str, dict] = {}
    nested_git: list[dict] = []
    sentinel_dirs: list[str] = []
    pycache_dirs: list[str] = []
    pyc_files: list[str] = []
    errors: list[str] = []
    unreadable: set[str] = set()
    totals = {"entries": 0, "dirs": 0, "files": 0, "others": 0, "size_bytes": 0}
    truncated = False
    stack: list[tuple[str, int]] = [(root, 0)]

    while stack:
        dirpath, depth = stack.pop()
        try:
            with os.scandir(dirpath) as handle:
                children = list(handle)
        except OSError as exc:
            errors.append(f"{dirpath}: {exc.strerror or exc}")
            if depth >= 1:
                unreadable.add(os.path.relpath(dirpath, root).split(os.sep)[0])
            continue

        for entry in children:
            totals["entries"] += 1
            if totals["entries"] > entry_limit:
                truncated = True
                stack.clear()
                break

            relative = os.path.relpath(entry.path, root)
            first = relative.split(os.sep)[0]
            entry_depth = depth + 1

            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                errors.append(f"{entry.path}: {exc.strerror or exc}")
                continue

            mode = info.st_mode
            is_dir = stat.S_ISDIR(mode)
            is_file = stat.S_ISREG(mode)
            entry_type = "dir" if is_dir else ("file" if is_file else "other")

            if depth == 0:
                bucket = top.setdefault(
                    first, new_bucket(first, entry_type, info.st_mtime)
                )
            else:
                bucket = top.get(first)
                if bucket:
                    bucket["children"] += 1

            if is_dir:
                totals["dirs"] += 1
                if bucket:
                    bucket["dirs"] += 1
            elif is_file:
                totals["files"] += 1
                totals["size_bytes"] += info.st_size
                if bucket:
                    bucket["files"] += 1
                    bucket["size_bytes"] += info.st_size
            else:
                totals["others"] += 1
                if bucket:
                    bucket["others"] += 1

            if entry_depth <= max_depth:
                if entry.name == ".git" and (is_dir or is_file):
                    nested_git.append(
                        {"path": relative, "kind": "dir" if is_dir else "file"}
                    )
                    if bucket:
                        bucket["nested_git"] += 1
                        if entry_depth == 2:
                            bucket["git_root"] = True
                if is_dir and entry.name == "system-commandline-sentinel-files":
                    sentinel_dirs.append(relative)
                    if bucket:
                        bucket["sentinel_dirs"] += 1
                if is_dir and entry.name == "__pycache__":
                    pycache_dirs.append(relative)
                    if bucket:
                        bucket["pycache_dirs"] += 1
                if is_file and relative.lower().endswith(".pyc"):
                    pyc_files.append(relative)
                    if bucket:
                        bucket["pyc_files"] += 1

            if is_dir:
                stack.append((entry.path, entry_depth))

    entries = []
    now = time.time()
    for name in sorted(top, key=str.casefold):
        bucket = top[name]
        if (
            bucket["type"] == "dir"
            and bucket["children"] == 0
            and not truncated
            and name not in unreadable
        ):
            bucket["empty"] = True
        mtime = bucket["mtime"]
        entries.append(
            {
                "name": name,
                "type": bucket["type"],
                "size_bytes": bucket["size_bytes"],
                "size_human": human_size(bucket["size_bytes"]),
                "mtime": iso_local(mtime) if mtime is not None else None,
                "age_minutes": round((now - mtime) / 60.0, 1) if mtime else None,
                "recent": False,
                "empty": bucket["empty"],
                "git_root": bucket["git_root"],
                "nested_git": bucket["nested_git"],
                "sentinel_dirs": bucket["sentinel_dirs"],
                "pycache_dirs": bucket["pycache_dirs"],
                "pyc_files": bucket["pyc_files"],
                "files": bucket["files"],
                "dirs": bucket["dirs"],
                "others": bucket["others"],
            }
        )

    return {
        "entries": entries,
        "nested_git": sorted(nested_git, key=lambda item: item["path"].casefold()),
        "sentinel_dirs": sorted(sentinel_dirs, key=str.casefold),
        "pycache_dirs": sorted(pycache_dirs, key=str.casefold),
        "pyc_files": sorted(pyc_files, key=str.casefold),
        "errors": errors,
        "truncated": truncated,
        "totals": totals,
    }


def main(argv: list[str] | None = None) -> int:
    configure_stdout()

    def positive(value: str) -> int:
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError("must be an integer")
        if number < 1:
            raise argparse.ArgumentTypeError("must be >= 1")
        return number

    def non_negative(value: str) -> int:
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError("must be an integer")
        if number < 0:
            raise argparse.ArgumentTypeError("must be >= 0")
        return number

    parser = argparse.ArgumentParser(
        description="Read-only inventory of a Qoder temporary directory."
    )
    parser.add_argument(
        "--root",
        default=os.path.join(os.path.expanduser("~"), ".qoder", "tmp"),
        help="directory to scan (default: ~/.qoder/tmp)",
    )
    parser.add_argument(
        "--max-depth",
        type=positive,
        default=DEFAULT_MAX_DEPTH,
        help="depth limit for .git, sentinel and cache markers (default: 5)",
    )
    parser.add_argument(
        "--recent-minutes",
        type=non_negative,
        default=DEFAULT_RECENT_MINUTES,
        help="recent window for top-level entries (default: 60)",
    )
    parser.add_argument(
        "--entry-limit",
        type=positive,
        default=DEFAULT_ENTRY_LIMIT,
        help="maximum entries walked before reporting PARTIAL (default: 200000)",
    )
    parser.add_argument(
        "--json", action="store_true", help="print a single ASCII JSON object"
    )
    args = parser.parse_args(argv)

    root = os.path.abspath(os.path.expanduser(args.root))
    now = time.time()
    cutoff = now - args.recent_minutes * 60.0

    def fail(code: str, message: str) -> int:
        if args.json:
            print(
                json.dumps(
                    {
                        "tool": "inventorier_tmp_qoder",
                        "result": "FAIL",
                        "error": code,
                        "message": message,
                        "root": root,
                        "read_only": True,
                    },
                    ensure_ascii=True,
                    indent=2,
                )
            )
        else:
            print(f"ROOT {root}")
            print("RESULT FAIL")
            print(f"ERROR {code} {message}")
        return 2

    if not os.path.exists(root):
        return fail("ROOT_MISSING", root)
    if not os.path.isdir(root):
        return fail("ROOT_NOT_DIR", root)
    try:
        with os.scandir(root):
            pass
    except OSError as exc:
        return fail("ROOT_UNREADABLE", f"{root}: {exc.strerror or exc}")

    scanned = scan_tree(root, args.max_depth, args.entry_limit)
    for bucket in scanned["entries"]:
        bucket["recent"] = bool(
            bucket["age_minutes"] is not None
            and bucket["age_minutes"] * 60.0 <= args.recent_minutes * 60.0
        )

    result = "PARTIAL" if (scanned["errors"] or scanned["truncated"]) else "OK"
    totals = scanned["totals"]
    report = {
        "tool": "inventorier_tmp_qoder",
        "version": 1,
        "read_only": True,
        "root": root,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scan_depth": args.max_depth,
        "recent_minutes": args.recent_minutes,
        "entry_limit": args.entry_limit,
        "result": result,
        "totals": {
            "entries": totals["entries"],
            "dirs": totals["dirs"],
            "files": totals["files"],
            "others": totals["others"],
            "size_bytes": totals["size_bytes"],
            "size_human": human_size(totals["size_bytes"]),
            "top_entries": len(scanned["entries"]),
        },
        "markers": {
            "nested_git": len(scanned["nested_git"]),
            "sentinel_dirs": len(scanned["sentinel_dirs"]),
            "pycache_dirs": len(scanned["pycache_dirs"]),
            "pyc_files": len(scanned["pyc_files"]),
        },
        "nested_git": scanned["nested_git"],
        "sentinel_dirs": scanned["sentinel_dirs"],
        "pycache_dirs": scanned["pycache_dirs"],
        "pyc_files": scanned["pyc_files"],
        "entries": scanned["entries"],
        "errors": scanned["errors"],
        "truncated": scanned["truncated"],
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print(f"ROOT {root}")
        print(f"GENERATED_AT {report['generated_at']}")
        print("MODE READ_ONLY")
        print(f"SCAN_DEPTH {args.max_depth}")
        print(f"RECENT_WINDOW_MINUTES {args.recent_minutes}")
        print(f"ENTRY_LIMIT {args.entry_limit}")
        print(f"RESULT {result}")
        print(
            "TOTALS"
            f" entries={totals['entries']}"
            f" dirs={totals['dirs']}"
            f" files={totals['files']}"
            f" others={totals['others']}"
            f" size_bytes={totals['size_bytes']}"
            f" size={human_size(totals['size_bytes'])}"
            f" top_entries={len(scanned['entries'])}"
        )
        print(
            "MARKERS"
            f" nested_git={len(scanned['nested_git'])}"
            f" sentinel_dirs={len(scanned['sentinel_dirs'])}"
            f" pycache_dirs={len(scanned['pycache_dirs'])}"
            f" pyc_files={len(scanned['pyc_files'])}"
            f" errors={len(scanned['errors'])}"
            f" truncated={'yes' if scanned['truncated'] else 'no'}"
        )
        print("--- ENTRIES ---")
        for entry in scanned["entries"]:
            label = {"dir": "DIR", "file": "FILE", "other": "OTHER"}[entry["type"]]
            recent = "yes" if entry["recent"] else "no"
            empty = "yes" if entry["empty"] else "no"
            git = "root" if entry["git_root"] else "no"
            print(
                f"{label:<5} {entry['name']}"
                f" | size={entry['size_human']} ({entry['size_bytes']}B)"
                f" | mtime={entry['mtime'] or 'unknown'}"
                f" | age_min={entry['age_minutes'] if entry['age_minutes'] is not None else 'unknown'}"
                f" | recent={recent}"
                f" | empty={empty}"
                f" | git={git}"
                f" | nested_git={entry['nested_git']}"
                f" | sentinel={entry['sentinel_dirs']}"
                f" | pycache={entry['pycache_dirs']}"
                f" | pyc={entry['pyc_files']}"
            )
        if scanned["nested_git"]:
            print("--- NESTED_GIT ---")
            for item in scanned["nested_git"]:
                print(f"{item['kind']:<4} {item['path']}")
        if scanned["sentinel_dirs"]:
            print("--- SENTINEL_DIRS ---")
            for path in scanned["sentinel_dirs"]:
                print(path)
        if scanned["pycache_dirs"] or scanned["pyc_files"]:
            print("--- PYCACHE ---")
            for path in scanned["pycache_dirs"]:
                print(f"dir  {path}")
            for path in scanned["pyc_files"]:
                print(f"pyc  {path}")
        if scanned["errors"]:
            print("--- ERRORS ---")
            for message in scanned["errors"]:
                print(message)

    return 0


if __name__ == "__main__":
    sys.exit(main())
