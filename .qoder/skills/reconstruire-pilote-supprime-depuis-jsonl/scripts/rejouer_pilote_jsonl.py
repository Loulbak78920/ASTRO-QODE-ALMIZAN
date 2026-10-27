#!/usr/bin/env python3
"""Replay Write/Edit tool_use records from a Qoder session JSONL."""

import argparse
import hashlib
import json
import ntpath
import sys
from pathlib import Path

WRITE = "Write"
EDIT = "Edit"
UNSUPPORTED = {"MultiEdit", "NotebookEdit", "apply_patch", "update_file"}


class CliError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def ascii_safe(value):
    text = str(value).encode("ascii", "backslashreplace").decode("ascii")
    return text.replace("\r", "\\r").replace("\n", "\\n")


def norm_case(path):
    return ntpath.normcase(ntpath.normpath(str(path)))


def base_name(path):
    return ntpath.basename(str(path).replace("/", "\\"))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="rejouer_pilote_jsonl.py",
        description="Replay Write/Edit records from a Qoder session JSONL and verify numeric claims.",
        allow_abbrev=False,
    )
    parser.add_argument("--jsonl", required=True, help="Path to <sessionId>.jsonl")
    parser.add_argument("--file", required=True, help="Exact path or basename of the deleted file")
    parser.add_argument("--expect-writes", type=int)
    parser.add_argument("--expect-write-chars", type=int)
    parser.add_argument("--expect-edits", type=int)
    parser.add_argument("--expect-lines", type=int)
    parser.add_argument("--expect-chars", type=int)
    parser.add_argument("--dump", help="Write the reconstruction to a new UTF-8/LF file")
    return parser


def run(args):
    jsonl_path = Path(args.jsonl)
    if not jsonl_path.is_file():
        raise CliError(2, f"jsonl not found: {jsonl_path}")
    try:
        stat_before = jsonl_path.stat()
        data = jsonl_path.read_bytes()
    except OSError as exc:
        raise CliError(2, f"cannot read jsonl: {exc}")

    digest = hashlib.sha256(data).hexdigest()
    bom = data.startswith(b"\xef\xbb\xbf")
    try:
        text_jsonl = data.decode("utf-8-sig" if bom else "utf-8")
    except UnicodeDecodeError as exc:
        raise CliError(2, f"jsonl is not valid UTF-8: {exc}")

    jsonl_lines = len(text_jsonl.splitlines())
    print(f"JSONL {ascii_safe(jsonl_path)}")
    print(
        f"JSONL_FINGERPRINT size={len(data)} mtime_ns={stat_before.st_mtime_ns} "
        f"lines={jsonl_lines} sha256={digest}"
    )
    if bom:
        print("WARN jsonl_bom")
    if not data.endswith(b"\n"):
        print("WARN jsonl_no_trailing_newline")
    if stat_before.st_size != len(data):
        print("WARN jsonl_changed_during_read")

    target_arg = args.file
    exact = ("/" in target_arg) or ("\\" in target_arg)
    target_key = norm_case(target_arg) if exact else norm_case(base_name(target_arg))

    events = []
    main_paths = {}
    side_paths = {}
    side_events = 0
    seen_ids = {}

    for lineno, raw in enumerate(text_jsonl.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CliError(2, f"invalid JSON at line {lineno}: {exc.msg}")
        if obj.get("type") != "assistant":
            continue
        content = (obj.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if name not in (WRITE, EDIT) and name not in UNSUPPORTED:
                continue
            inp = block.get("input") or {}
            file_path = inp.get("file_path") or inp.get("path")
            if not isinstance(file_path, str) or not file_path:
                continue
            if exact:
                matched = norm_case(file_path) == target_key
            else:
                matched = norm_case(base_name(file_path)) == target_key
            if not matched:
                continue
            path_key = norm_case(file_path)
            if obj.get("isSidechain"):
                side_paths[path_key] = file_path
                side_events += 1
                continue
            main_paths[path_key] = file_path
            tool_id = block.get("id")
            if isinstance(tool_id, str) and tool_id:
                payload = hashlib.sha256(
                    json.dumps(inp, sort_keys=True, ensure_ascii=False).encode("utf-8")
                ).hexdigest()
                previous = seen_ids.get(tool_id)
                if previous is not None:
                    if previous != payload:
                        raise CliError(2, f"duplicate tool_use id with different input: {tool_id}")
                    continue
                seen_ids[tool_id] = payload
            events.append((lineno, name, inp, file_path))

    if not main_paths:
        if side_paths:
            raise CliError(
                2,
                f"target only appears in {side_events} sidechain event(s); inspect manually",
            )
        raise CliError(2, f"no Write/Edit for target: {target_arg}")
    if len(main_paths) > 1:
        listing = "; ".join(sorted(main_paths.values()))
        raise CliError(2, f"multiple target paths; pass an exact --file: {listing}")
    if side_events:
        print(f"WARN sidechain_ignored={side_events}")

    target_path = next(iter(main_paths.values()))
    print(f"TARGET {ascii_safe(target_path)}")

    text = None
    writes = 0
    write_chars = 0
    edits = 0

    for lineno, name, inp, _ in events:
        if name == WRITE:
            content = inp.get("content")
            if not isinstance(content, str):
                raise CliError(2, f"Write without string content at line {lineno}")
            text = content
            writes += 1
            write_chars += len(content)
            print(
                f"WRITE entry={lineno} chars={len(content)} "
                f"lines={len(content.splitlines())}"
            )
        elif name == EDIT:
            if text is None:
                raise CliError(2, f"Edit before Write at line {lineno}")
            old = inp.get("old_string")
            new = inp.get("new_string")
            if not isinstance(old, str) or not isinstance(new, str):
                raise CliError(2, f"Edit without string old_string/new_string at line {lineno}")
            if old == "":
                raise CliError(2, f"Edit with empty old_string at line {lineno}")
            occurrences = text.count(old)
            replace_all = bool(inp.get("replace_all") or inp.get("allow_multiple"))
            if occurrences == 0:
                print(f"EDIT MISS entry={lineno} old_chars={len(old)}")
                return 1
            if occurrences > 1 and not replace_all:
                print(f"EDIT AMBIGUOUS entry={lineno} occurrence={occurrences}")
                return 1
            text = text.replace(old, new) if replace_all else text.replace(old, new, 1)
            edits += 1
            print(f"EDIT entry={lineno} occurrence={occurrences}")
        else:
            raise CliError(2, f"unsupported tool {name} at line {lineno}")

    if text is None:
        raise CliError(2, "no Write event")
    if writes > 1:
        print(f"WARN multiple_writes={writes}; final text follows the last Write")

    lines = len(text.splitlines())
    chars = len(text)
    bytes_utf8 = len(text.encode("utf-8"))
    trailing = "true" if text.endswith("\n") else "false"
    print(f"EVENTS writes={writes} write_chars={write_chars} edits={edits}")
    print(
        f"RESULT lines={lines} chars={chars} bytes_utf8={bytes_utf8} "
        f"trailing_newline={trailing}"
    )

    if args.dump is not None:
        dump_path = Path(args.dump)
        if dump_path.exists():
            raise CliError(2, f"dump target exists: {dump_path}")
        parent = dump_path.parent
        if not parent.exists() or not parent.is_dir():
            raise CliError(2, f"dump parent missing or not a directory: {parent}")
        try:
            with open(dump_path, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
            raw = dump_path.read_bytes()
        except OSError as exc:
            raise CliError(2, f"dump failed: {exc}")
        if len(raw) != bytes_utf8:
            try:
                dump_path.unlink()
            except OSError:
                pass
            raise CliError(
                1,
                f"dump bytes mismatch expected={bytes_utf8} measured={len(raw)}",
            )
        print(
            f"DUMP {ascii_safe(dump_path)} bytes={len(raw)} "
            f"sha256={hashlib.sha256(raw).hexdigest()}"
        )

    specs = (
        ("writes", args.expect_writes, writes),
        ("write_chars", args.expect_write_chars, write_chars),
        ("edits", args.expect_edits, edits),
        ("lines", args.expect_lines, lines),
        ("chars", args.expect_chars, chars),
    )
    given = [(name, expected, actual) for name, expected, actual in specs if expected is not None]
    if not given:
        print("CLAIM NONE")
        return 0
    mismatches = [
        (name, expected, actual)
        for name, expected, actual in given
        if expected != actual
    ]
    if mismatches:
        for name, expected, actual in mismatches:
            print(f"CLAIM FAIL {name} expected={expected} measured={actual}")
        return 1
    summary = " ".join(f"{name}={actual}" for name, _, actual in given)
    print(f"CLAIM PASS {summary}")
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except CliError as exc:
        print(f"ERROR {ascii_safe(exc.message)}")
        return exc.code
    except Exception as exc:
        print(f"ERROR internal {type(exc).__name__}: {ascii_safe(exc)}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
