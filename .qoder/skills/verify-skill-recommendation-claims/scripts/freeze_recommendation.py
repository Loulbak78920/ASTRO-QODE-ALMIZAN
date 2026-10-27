#!/usr/bin/env python3
"""Read-only extraction of a recommendation object from a Qoder JSONL log.

Prints the recommendation slice as frozen bytes: character count plus the
SHA-256 of the slice without and with a trailing LF. Optionally writes the
exact slice to --out, which must be outside the Skill directory.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

FIELDS = ("skillName", "action", "summary", "rationale")
BACKSLASH = chr(92)
QUOTE = chr(34)
SKILL_DIR = Path(__file__).resolve().parent.parent


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def ascii_json(value):
    return json.dumps(value, ensure_ascii=True)


def emit(key, value):
    if isinstance(value, bool):
        print(f"{key}={'true' if value else 'false'}")
    elif value is None:
        print(f"{key}=none")
    elif isinstance(value, str):
        print(f"{key}={ascii_json(value)}")
    else:
        print(f"{key}={value}")


def fail(message, code):
    emit("ERROR", message)
    print("RESULT FAIL")
    print(f"EXIT={code}")
    return code


def message_text(event):
    message = event.get("message")
    if not isinstance(message, dict) or message.get("role") != "user":
        return None
    if event.get("isMeta") or event.get("isCompactSummary"):
        return None
    if "toolUseResult" in event:
        return None
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = [
            item["text"]
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        ]
        if not parts:
            return None
        text = "\n".join(parts)
    else:
        return None
    if "Base directory for this skill:" in text:
        return None
    return text


def scan_objects(text):
    """Yield (start, slice_text, obj) for balanced-brace JSON objects.

    Tracks strings and backslash escapes so braces inside summary or rationale
    do not truncate the slice.
    """
    length = len(text)
    for start in range(length):
        if text[start] != "{":
            continue
        depth = 0
        in_string = False
        escaped = False
        end = None
        for index in range(start, length):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == BACKSLASH:
                    escaped = True
                elif char == QUOTE:
                    in_string = False
                continue
            if char == QUOTE:
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index + 1
                    break
        if end is None:
            continue
        slice_text = text[start:end]
        try:
            obj = json.loads(slice_text)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and "skillName" in obj:
            yield start, slice_text, obj


def complete(obj):
    return all(isinstance(obj.get(field), str) and obj[field].strip() for field in FIELDS)


def collect(line_number, text):
    return [
        (line_number, slice_text, obj)
        for _, slice_text, obj in scan_objects(text)
    ]


def main():
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Freeze a recommendation object from a Qoder project JSONL log."
    )
    parser.add_argument("--session-jsonl", required=True, help="project JSONL path")
    parser.add_argument("--line", type=int, help="1-based JSONL line to read")
    parser.add_argument("--list", action="store_true", help="list candidates instead of freezing")
    parser.add_argument("--out", help="write the exact slice here (must be outside the Skill)")
    parser.add_argument("--trailing-lf", action="store_true", help="append LF when writing --out")
    parser.add_argument("--expect-sha256", help="expected hash, with or without trailing LF")
    args = parser.parse_args()

    if args.line is not None and args.line < 1:
        return fail("--line must be >= 1", 2)

    source = Path(args.session_jsonl).expanduser()
    try:
        raw = source.read_bytes()
    except OSError as exc:
        return fail(f"cannot read session jsonl {source}: {exc}", 2)

    lines = raw.split(b"\n")
    bad_lines = 0
    candidates = []
    for line_number, raw_line in enumerate(lines, 1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            bad_lines += 1
            continue
        if not isinstance(event, dict):
            continue
        text = message_text(event)
        if text is None:
            continue
        candidates.extend(collect(line_number, text))

    if args.line is not None:
        candidates = [item for item in candidates if item[0] == args.line]

    emit("SOURCE_JSONL", str(source))
    emit("BAD_LINES", bad_lines)
    emit("CANDIDATE_COUNT", len(candidates))

    if args.list:
        for line_number, _, obj in candidates:
            fields = ",".join(FIELDS)
            emit("LIST_LINE", line_number)
            emit("LIST_FIELDS", fields)
            emit("LIST_NAME", obj.get("skillName") if isinstance(obj.get("skillName"), str) else "")
            emit("LIST_ACTION", obj.get("action") if isinstance(obj.get("action"), str) else "")
            emit("LIST_COMPLETE", complete(obj))
        if not candidates:
            return fail("no candidate recommendation object found", 1)
        print("RESULT PASS")
        print("EXIT=0")
        return 0

    if not candidates:
        return fail("no candidate recommendation object found", 1)

    chosen = None
    for item in candidates:
        if complete(item[2]):
            chosen = item
    if chosen is None:
        chosen = candidates[-1]

    line_number, slice_text, obj = chosen
    data_no_lf = slice_text.encode("utf-8")
    data_with_lf = data_no_lf + b"\n"
    sha_no_lf = hashlib.sha256(data_no_lf).hexdigest()
    sha_with_lf = hashlib.sha256(data_with_lf).hexdigest()
    missing = [
        field
        for field in FIELDS
        if not isinstance(obj.get(field), str) or not obj.get(field, "").strip()
    ]

    emit("SOURCE_LINE", line_number)
    emit("SOURCE_ROLE", "user")
    emit("JSON_CHARS", len(slice_text))
    emit("SHA256_NO_LF", sha_no_lf)
    emit("SHA256_WITH_LF", sha_with_lf)
    emit("FIELDS_OK", complete(obj))
    emit("MISSING_FIELDS", ",".join(missing) if missing else "none")
    emit("SKILL_NAME", obj.get("skillName") if isinstance(obj.get("skillName"), str) else "")
    emit("ACTION", obj.get("action") if isinstance(obj.get("action"), str) else "")

    expect_ok = None
    if args.expect_sha256:
        expected = args.expect_sha256.strip().lower()
        expect_ok = expected in (sha_no_lf, sha_with_lf)
        emit("EXPECT_SHA256", expected)
        emit("EXPECT_SHA256_MATCH", expect_ok)

    out_status = "none"
    if args.out:
        out_path = Path(args.out).expanduser()
        try:
            out_path.resolve().relative_to(SKILL_DIR.resolve())
            return fail("refusing to write inside the Skill directory", 2)
        except ValueError:
            pass
        if not out_path.parent.is_dir():
            return fail(f"parent directory does not exist: {out_path.parent}", 2)
        payload = slice_text + ("\n" if args.trailing_lf else "")
        try:
            out_path.write_bytes(payload.encode("utf-8"))
        except OSError as exc:
            return fail(f"cannot write {out_path}: {exc}", 2)
        written = out_path.read_bytes()
        emit("OUT", str(out_path))
        emit("OUT_BYTES", len(written))
        emit("OUT_SHA256", hashlib.sha256(written).hexdigest())
        out_status = "written"

    emit("OUT_STATUS", out_status)

    ok = complete(obj) and (expect_ok is not False)
    print(f"RESULT {'PASS' if ok else 'FAIL'}")
    print(f"EXIT={0 if ok else 1}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
