#!/usr/bin/env python3
"""Reconcile a command string across the channels of a Qoder session.

Read-only. Counts a pattern separately in the archived read_chat_session
dump, in tool_use inputs, in tool_result texts and in message prose, then
reconstructs heredoc <stdin> line numbers and aligns them with tracebacks.

Exit codes: 0 = pattern present in tool_use inputs, 10 = absent from inputs
(whatever the other channels show), 2 = invalid argument or unreadable file.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time

HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
STDIN_FRAME = re.compile(r'File "<(stdin|string)>", line (\d+)')
STDLIB_HINTS = ("pathlib", "shutil", "tempfile", "subprocess.py", "os.py", "io.py")


def a(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def fingerprint(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    st = os.stat(path)
    return {
        "bytes": st.st_size,
        "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(st.st_mtime)),
        "sha256": h.hexdigest(),
    }


def iter_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from iter_strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_strings(value)


def heredoc_bodies(command):
    """Return [(delimiter, body_lines)] for each heredoc in a shell command."""
    lines = command.split("\n")
    bodies = []
    i = 0
    while i < len(lines):
        match = HEREDOC.search(lines[i])
        if not match:
            i += 1
            continue
        delimiter = match.group(2)
        start = i + 1
        end = start
        while end < len(lines) and lines[end].rstrip("\r").strip("\t") != delimiter:
            end += 1
        bodies.append((delimiter, lines[start:end]))
        i = end + 1
    return bodies


def stdin_hits(command, pattern):
    """Lines of the heredoc body that contain the pattern, numbered as stdin."""
    hits = []
    for _delimiter, body in heredoc_bodies(command):
        for number, line in enumerate(body, 1):
            if pattern in line:
                hits.append((number, line.strip()))
    return hits


def statement_at(command, number):
    """Heredoc body line seen as stdin line `number`, or None."""
    for _delimiter, body in heredoc_bodies(command):
        if len(body) >= number >= 1:
            return body[number - 1].strip()
    return None


def tracebacks(text):
    """Parse traceback blocks: stdin line, stdlib frames, final error line."""
    lines = text.splitlines()
    found = []
    i = 0
    while i < len(lines):
        if not lines[i].strip().startswith("Traceback (most recent call last)"):
            i += 1
            continue
        block = [lines[i]]
        j = i + 1
        while j < len(lines) and (not lines[j].strip() or lines[j][:1] in (" ", "\t")):
            block.append(lines[j])
            j += 1
        if j < len(lines):
            block.append(lines[j])
        frames = [m for line in block for m in [STDIN_FRAME.search(line)] if m]
        error = ""
        for line in reversed(block):
            if line.strip() and line[:1] not in (" ", "\t") and not line.startswith("Traceback"):
                error = line
                break
        found.append({
            "kind": frames[-1].group(1) if frames else None,
            "stdin_line": int(frames[-1].group(2)) if frames else None,
            "stdlib_frame": any(hint in line for line in block for hint in STDLIB_HINTS),
            "error": error,
        })
        i = j + 1
    return found


def load(path):
    calls, results, prose = [], [], 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for index, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = record.get("message") or {}
            content = message.get("content")
            if isinstance(content, str):
                prose += len(content)
                continue
            if not isinstance(content, list):
                continue
            role = message.get("role")
            for block in content:
                if not isinstance(block, dict):
                    continue
                kind = block.get("type")
                if kind == "tool_use":
                    calls.append({
                        "line": index,
                        "tool": block.get("name"),
                        "id": block.get("id"),
                        "input": block.get("input") or {},
                    })
                elif kind == "tool_result":
                    text = block.get("content")
                    if isinstance(text, list):
                        text = "\n".join(
                            part.get("text", "")
                            for part in text
                            if isinstance(part, dict)
                        )
                    results.append({"line": index, "id": block.get("tool_use_id"), "text": str(text)})
                elif kind == "text" and role in ("assistant", "user"):
                    prose += len(block.get("text", ""))
                elif kind == "thinking":
                    prose += len(block.get("thinking", ""))
    return calls, results, prose


def count_in_calls(calls, pattern):
    total = 0
    matched = []
    for call in calls:
        hits = sum(text.count(pattern) for text in iter_strings(call["input"]))
        total += hits
        if not hits:
            continue
        command = call["input"].get("command")
        lines = stdin_hits(command, pattern) if isinstance(command, str) else []
        matched.append({
            "line": call["line"],
            "tool": call["tool"],
            "id": call["id"],
            "occurrences": hits,
            "stdin_lines": [number for number, _text in lines],
        })
    return total, matched


def main():
    parser = argparse.ArgumentParser(
        description="Reconcile a command string across session channels (read-only)."
    )
    parser.add_argument("jsonl", help="path to <sessionId>.jsonl")
    parser.add_argument("--pattern", required=True, help="literal substring, case-sensitive")
    parser.add_argument("--dump", help="archived read_chat_session output to count as well")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of KEY=VALUE lines")
    args = parser.parse_args()

    if not args.pattern:
        print("ERROR empty pattern", file=sys.stderr)
        return 2
    if not os.path.isfile(args.jsonl):
        print("ERROR missing jsonl: %s" % a(args.jsonl), file=sys.stderr)
        return 2

    try:
        info = fingerprint(args.jsonl)
        calls, results, prose_chars = load(args.jsonl)
    except OSError as exc:
        print("ERROR unreadable jsonl: %s" % a(exc), file=sys.stderr)
        return 2

    input_total, matched_calls = count_in_calls(calls, args.pattern)
    result_total = sum(r["text"].count(args.pattern) for r in results)

    dump_info, dump_total = None, None
    if args.dump:
        try:
            with open(args.dump, encoding="utf-8", errors="replace") as f:
                dump_text = f.read()
            dump_total = dump_text.count(args.pattern)
            dump_info = fingerprint(args.dump)
        except OSError as exc:
            print("ERROR unreadable dump: %s" % a(exc), file=sys.stderr)
            return 2

    trace = []
    for result in results:
        for record in tracebacks(result["text"]):
            record["result_line"] = result["line"]
            record["tool_use_id"] = result["id"]
            trace.append(record)

    calls_by_id = {call["id"]: call for call in calls}
    pairs = []
    for item in trace:
        if item["kind"] != "stdin" or item["stdin_line"] is None:
            continue
        call = calls_by_id.get(item["tool_use_id"])
        command = call["input"].get("command") if call else None
        statement = statement_at(command, item["stdin_line"]) if isinstance(command, str) else None
        pairs.append({
            "call_line": call["line"] if call else None,
            "call_id": item["tool_use_id"],
            "result_line": item["result_line"],
            "stdin_line": item["stdin_line"],
            "statement": statement,
            "pattern_hit": bool(statement and args.pattern in statement),
        })

    verdict = "INPUT_RECORDED" if input_total else "NOT_IN_INPUTS"

    if args.json:
        payload = {
            "jsonl": args.jsonl,
            "fingerprint": info,
            "pattern": args.pattern,
            "dump": {"path": args.dump, "fingerprint": dump_info, "count": dump_total},
            "counts": {
                "input": input_total,
                "result": result_total,
                "calls_with": len(matched_calls),
                "prose_chars": prose_chars,
            },
            "calls": matched_calls,
            "tracebacks": trace,
            "pairs": pairs,
            "verdict": verdict,
        }
        print(json.dumps(payload, indent=1, ensure_ascii=True))
        return 0 if input_total else 10

    print("# file=%s bytes=%d mtime=%s sha256=%s"
          % (a(args.jsonl), info["bytes"], info["mtime"], info["sha256"]))
    print("PATTERN %s" % a(args.pattern))
    if dump_total is not None:
        print("DUMP %s bytes=%d count=%d"
              % (a(args.dump), dump_info["bytes"], dump_total))
    print("INPUT_OCCURRENCES %d CALLS_WITH %d" % (input_total, len(matched_calls)))
    print("RESULT_OCCURRENCES %d" % result_total)
    for call in matched_calls:
        lines = ",".join(str(n) for n in call["stdin_lines"]) or "NA"
        print("CALL line=%d tool=%s id=%s stdin_lines=%s occurrences=%d"
              % (call["line"], a(call["tool"]), a(call["id"]), lines, call["occurrences"]))
    for item in trace:
        kind = item["kind"] or "other"
        line = item["stdin_line"] if item["stdin_line"] is not None else "NA"
        frames = "stdlib" if item["stdlib_frame"] else "none"
        print("TRACEBACK result_line=%d kind=%s stdin_line=%s frames=%s error=%s"
              % (item["result_line"], kind, line, frames, a(item["error"])))
    for item in pairs:
        call_line = item["call_line"] if item["call_line"] is not None else "NA"
        print("PAIR result_line=%d call_line=%s stdin_line=%d pattern=%s statement=%s"
              % (item["result_line"], call_line, item["stdin_line"],
                 "hit" if item["pattern_hit"] else "miss", a(item["statement"])))
    print("VERDICT %s" % verdict)
    return 0 if input_total else 10


if __name__ == "__main__":
    sys.exit(main())
