#!/usr/bin/env python3
"""Locate a Skill injection record in a Qoder session JSONL (read-only).

Binds a Skill tool_use to its tool_result and to the isMeta injection record,
then checks the base-directory first line, the tail (ARGUMENTS or disk last line),
the last section heading, and optional sentinel phrases. Sentinel phrases are
classified as body or frontmatter on disk; frontmatter (name/description) never
enters the injection body.

Exit codes: 0 PASS, 1 FAIL/UNVERIFIED, 2 ERROR.
"""

import argparse
import json
import os
import sys
from pathlib import Path

BASE_PREFIX = "Base directory for this skill:"


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def load_records(path):
    records = []
    errors = []
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        for lineno, line in enumerate(handle, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append((lineno, str(exc)))
                continue
            if isinstance(record, dict):
                records.append((lineno, record))
    return records, errors


def content_of(record):
    message = record.get("message")
    if isinstance(message, dict):
        return message.get("content")
    if isinstance(message, str):
        return message
    return None


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        for key in ("text", "content"):
            value = content.get(key)
            if isinstance(value, str):
                return value
        return ""
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for key in ("text", "content"):
                    value = item.get(key)
                    if isinstance(value, str):
                        parts.append(value)
        return "\n".join(parts)
    return ""


def find_calls(records, skill, nonce, args_exact, args_contains):
    calls = []
    for lineno, record in records:
        if record.get("type") != "assistant":
            continue
        content = content_of(record)
        if isinstance(content, dict):
            content = [content]
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "tool_use" or item.get("name") != "Skill":
                continue
            tool_input = item.get("input")
            if not isinstance(tool_input, dict):
                continue
            if tool_input.get("skill") != skill:
                continue
            call_args = tool_input.get("args", "")
            if call_args is None:
                call_args = ""
            if not isinstance(call_args, str):
                call_args = str(call_args)
            if nonce and nonce not in call_args:
                continue
            if args_exact is not None and call_args != args_exact:
                continue
            if args_contains and args_contains not in call_args:
                continue
            calls.append({
                "line": lineno,
                "timestamp": record.get("timestamp"),
                "id": item.get("id"),
                "args": call_args,
            })
    return calls


def find_results(records, call):
    results = []
    for lineno, record in records:
        if lineno <= call["line"]:
            continue
        if record.get("type") != "user":
            continue
        content = content_of(record)
        if isinstance(content, dict):
            content = [content]
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "tool_result":
                continue
            if item.get("tool_use_id") != call["id"]:
                continue
            results.append({
                "line": lineno,
                "timestamp": record.get("timestamp"),
                "uuid": record.get("uuid"),
                "tool_use_id": item.get("tool_use_id"),
            })
    return results


def find_injections(records, result):
    matches = []
    candidates = []
    for lineno, record in records:
        if lineno <= result["line"]:
            continue
        if record.get("type") != "user":
            continue
        body = text_of(content_of(record))
        if not body.startswith(BASE_PREFIX):
            continue
        item = {
            "line": lineno,
            "timestamp": record.get("timestamp"),
            "body": body,
            "parent": record.get("parentUuid"),
            "is_meta": record.get("isMeta"),
            "session": record.get("sessionId"),
        }
        if record.get("isMeta") is True and record.get("parentUuid") == result["uuid"]:
            matches.append(item)
        else:
            candidates.append(item)
    return matches, candidates


def read_disk(path):
    data = Path(path).read_bytes()
    text = data.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    nonempty = [line for line in lines if line.strip()]
    headings = [line for line in lines if line.startswith("## ")]
    frontmatter_end = None
    if lines and lines[0].strip() == "---":
        for index, line in enumerate(lines[1:], 2):
            if line.strip() == "---":
                frontmatter_end = index
                break
    return {
        "path": str(Path(path)),
        "bytes": len(data),
        "chars": len(text),
        "last_line": nonempty[-1] if nonempty else "",
        "last_heading": headings[-1] if headings else None,
        "frontmatter_end": frontmatter_end,
        "body_start": (frontmatter_end + 1) if frontmatter_end else 1,
        "text": text,
    }


def disk_scope(disk, phrase):
    if disk is None:
        return [], []
    lines = [
        i for i, line in enumerate(disk["text"].splitlines(), 1)
        if phrase in line
    ]
    end = disk.get("frontmatter_end")
    if not end:
        return lines, []
    return [i for i in lines if i > end], [i for i in lines if i <= end]



def norm_path(value):
    return os.path.normcase(os.path.realpath(value))


def compact(value, limit):
    value = value.replace("\r", "\\r").replace("\n", "\\n")
    if len(value) <= limit:
        return value
    return value[:limit] + "... [{} chars]".format(len(value))


def find_matches(directory, skill, nonce, args_exact, args_contains):
    files = sorted(Path(directory).glob("*.jsonl"), key=lambda item: item.name)
    matches = []
    parsed = 0
    for path in files:
        if nonce:
            try:
                with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
                    if nonce not in handle.read():
                        continue
            except OSError as exc:
                print("WARN cannot read {}: {}".format(path, exc))
                continue
        records, errors = load_records(path)
        parsed += 1
        if errors:
            print("WARN {} parse_errors {}".format(path.name, len(errors)))
        for call in find_calls(records, skill, nonce, args_exact, args_contains):
            matches.append((path, call))
    return files, parsed, matches


def check_tail(body, call_args, disk):
    nonempty = [line for line in body.splitlines() if line.strip()]
    last = nonempty[-1] if nonempty else ""
    expected_tail = "ARGUMENTS: {}".format(call_args) if call_args else None
    if expected_tail is not None:
        tail_ok = last == expected_tail
    elif disk is not None:
        tail_ok = last == disk["last_line"]
    else:
        tail_ok = None
    last_heading_present = None
    disk_last_present = None
    if disk is not None:
        if disk["last_heading"]:
            last_heading_present = disk["last_heading"] in body
        if disk["last_line"]:
            disk_last_present = disk["last_line"] in body
    truncated = False
    if tail_ok is False:
        truncated = True
    if last_heading_present is False:
        truncated = True
    if disk_last_present is False:
        truncated = True
    return {
        "last": last,
        "expected_tail": expected_tail,
        "tail_ok": tail_ok,
        "last_heading_present": last_heading_present,
        "disk_last_present": disk_last_present,
        "truncated": truncated,
    }


def session_of(records, path, injection):
    if injection and injection.get("session"):
        return injection["session"]
    for _, record in records:
        if record.get("sessionId"):
            return record["sessionId"]
    return Path(path).stem


def verify_candidate(jsonl, records, call, result, injection, sentinels, disk, expect_base, max_text):
    body = injection["body"]
    first = body.splitlines()[0] if body.splitlines() else ""
    tail = check_tail(body, call["args"], disk)

    parent_ok = injection["parent"] == result["uuid"]
    id_ok = result["tool_use_id"] == call["id"]

    observed = None
    if first.startswith(BASE_PREFIX):
        observed = first[len(BASE_PREFIX):].strip()

    base_missing = observed is None
    base_mismatch = False
    if expect_base and observed is not None:
        base_mismatch = norm_path(observed) != norm_path(expect_base)

    reasons = []
    if not parent_ok:
        reasons.append("injection parentUuid != result.uuid")
    if not id_ok:
        reasons.append("tool_result tool_use_id != call.id")
    if base_missing:
        reasons.append("base directory first line missing")
    if base_mismatch:
        reasons.append("base directory mismatch")
    if tail["truncated"]:
        reasons.append("injection appears truncated")
    if tail["tail_ok"] is None:
        reasons.append("no args/disk reference for tail")
    for phrase in sentinels:
        if body.count(phrase) == 0:
            body_lines, frontmatter_lines = disk_scope(disk, phrase)
            if disk is not None and frontmatter_lines and not body_lines:
                reasons.append("sentinel only in frontmatter: {}".format(phrase))
            else:
                reasons.append("sentinel missing: {}".format(phrase))

    print("JSONL {}".format(jsonl))
    print("SESSION {}".format(session_of(records, jsonl, injection)))
    print("CALL L{} {} tool_use_id {} args {}".format(
        call["line"], call["timestamp"], call["id"],
        json.dumps(call["args"], ensure_ascii=False)))
    print("TOOL_RESULT L{} {} uuid {} tool_use_id {}".format(
        result["line"], result["timestamp"], result["uuid"], result["tool_use_id"]))
    print("INJECTION L{} {} isMeta {} chars {}".format(
        injection["line"], injection["timestamp"], injection["is_meta"], len(body)))
    print("FIRST {}".format(compact(first, max_text)))
    print("TAIL {}".format(compact(tail["last"], max_text)))
    print("BINDING parentUuid==result.uuid {} tool_use_id==call.id {}".format(parent_ok, id_ok))
    print("BASE OBSERVED {} EXPECTED {} EQUAL {}".format(
        observed if observed is not None else "<missing>",
        expect_base if expect_base else "<not provided>",
        (not base_mismatch and not base_missing) if expect_base else "n/a"))
    print("TRUNCATION {} (tail_ok={} last_heading={} disk_last={})".format(
        tail["truncated"], tail["tail_ok"],
        tail["last_heading_present"], tail["disk_last_present"]))
    for phrase in sentinels:
        count = body.count(phrase)
        body_lines, frontmatter_lines = disk_scope(disk, phrase)
        disk_lines = sorted(body_lines + frontmatter_lines)
        print("SENTINEL {} disk {} present {} count {}".format(
            json.dumps(phrase, ensure_ascii=False), disk_lines or "-", count > 0, count))
        if disk is not None:
            print("SENTINEL_SCOPE {} body {} frontmatter {}".format(
                json.dumps(phrase, ensure_ascii=False),
                body_lines or "-", frontmatter_lines or "-"))
    if disk is not None:
        print("SIZE injection_chars {} disk_bytes {} (not directly comparable)".format(
            len(body), disk["bytes"]))

    if base_mismatch:
        verdict = "FAIL"
    elif reasons:
        verdict = "UNVERIFIED"
    else:
        verdict = "PASS"
    if reasons:
        print("REASONS {}".format("; ".join(reasons)))
    print("RESULT {}".format(verdict))
    return 0 if verdict == "PASS" else 1


def main(argv=None):
    configure_stdio()
    parser = argparse.ArgumentParser(
        description="Locate a Skill injection record in a Qoder session JSONL (read-only).",
        epilog=(
            "Examples:\n"
            "  locate_injection.py --jsonl SESSION.jsonl --skill NAME --nonce BINDING-123 "
            "--sentinel 'phrase' --disk-skill-md SKILL.md --expect-base DIR\n"
            "  locate_injection.py --scan-dir PROJECT_DIR --skill NAME --nonce BINDING-123 "
            "--sentinel 'phrase' --disk-skill-md SKILL.md --expect-base DIR"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--jsonl", help="Session JSONL to inspect")
    group.add_argument(
        "--scan-dir",
        help="Directory of *.jsonl files; requires --nonce or --args-exact")
    parser.add_argument("--skill", required=True, help="Skill name passed to the Skill tool")
    parser.add_argument("--nonce", help="Unique token added to the Skill args")
    parser.add_argument("--args-exact", help="Exact args string to match")
    parser.add_argument("--args-contains", help="Substring that must appear in args")
    parser.add_argument(
        "--sentinel", action="append", default=[],
        help=("Phrase that must appear in the injection body; repeatable. "
              "Terms found only in frontmatter are reported separately."))
    parser.add_argument(
        "--disk-skill-md",
        help="SKILL.md on disk, used for tail and sentinel line checks")
    parser.add_argument(
        "--expect-base",
        help="Expected base directory from the injection first line")
    parser.add_argument(
        "--max-text", type=int, default=300,
        help="Max chars for FIRST/TAIL output (default 300)")
    args = parser.parse_args(argv)

    if args.scan_dir:
        if not (args.nonce or args.args_exact):
            print("ERROR scan mode requires --nonce or --args-exact")
            return 2
        if not Path(args.scan_dir).is_dir():
            print("ERROR scan directory not found: {}".format(args.scan_dir))
            return 2
        files, parsed, matches = find_matches(
            args.scan_dir, args.skill, args.nonce, args.args_exact, args.args_contains)
        print("SCAN dir {} files {} parsed {} matches {}".format(
            args.scan_dir, len(files), parsed, len(matches)))
        for path, call in matches:
            print("MATCH {} L{} {} tool_use_id {} args {}".format(
                path.name, call["line"], call["timestamp"], call["id"],
                json.dumps(call["args"], ensure_ascii=False)))
        if len(matches) != 1:
            print("RESULT UNVERIFIED (expected exactly one match, found {})".format(
                len(matches)))
            return 1
        jsonl = str(matches[0][0])
        call = matches[0][1]
        records, errors = load_records(jsonl)
        if errors:
            print("WARN parse_errors {}".format(len(errors)))
    else:
        jsonl = args.jsonl
        if not Path(jsonl).is_file():
            print("ERROR JSONL not found: {}".format(jsonl))
            return 2
        records, errors = load_records(jsonl)
        if errors:
            print("WARN parse_errors {}".format(len(errors)))
        calls = find_calls(
            records, args.skill, args.nonce, args.args_exact, args.args_contains)
        if not calls:
            print("JSONL {}".format(jsonl))
            print("SKILL {}".format(args.skill))
            print("CALL NOT FOUND")
            print("RESULT UNVERIFIED (no Skill tool_use matched)")
            return 1
        if len(calls) > 1:
            print("JSONL {}".format(jsonl))
            print("CALLS {}".format(len(calls)))
            for call in calls:
                print("MATCH L{} {} tool_use_id {} args {}".format(
                    call["line"], call["timestamp"], call["id"],
                    json.dumps(call["args"], ensure_ascii=False)))
            print("RESULT UNVERIFIED (ambiguous: multiple Skill calls matched)")
            return 1
        call = calls[0]

    results = find_results(records, call)
    if not results:
        print("JSONL {}".format(jsonl))
        print("CALL L{} tool_use_id {}".format(call["line"], call["id"]))
        print("TOOL_RESULT NOT FOUND")
        print("RESULT UNVERIFIED (tool_result not found)")
        return 1
    if len(results) > 1:
        print("JSONL {}".format(jsonl))
        print("TOOL_RESULTS {}".format(len(results)))
        for result in results:
            print("MATCH L{} uuid {}".format(result["line"], result["uuid"]))
        print("RESULT UNVERIFIED (ambiguous: multiple tool_results matched)")
        return 1
    result = results[0]

    injections, candidates = find_injections(records, result)
    if not injections:
        print("JSONL {}".format(jsonl))
        print("CALL L{} tool_use_id {}".format(call["line"], call["id"]))
        print("TOOL_RESULT L{} uuid {}".format(result["line"], result["uuid"]))
        print("INJECTION NOT FOUND")
        for candidate in candidates:
            print("CANDIDATE L{} {} parentUuid {} (not bound)".format(
                candidate["line"], candidate["timestamp"], candidate["parent"]))
        print("RESULT UNVERIFIED (no isMeta injection with parentUuid == tool_result.uuid)")
        return 1
    if len(injections) > 1:
        print("JSONL {}".format(jsonl))
        print("INJECTIONS {}".format(len(injections)))
        for injection in injections:
            print("MATCH L{} {}".format(injection["line"], injection["timestamp"]))
        print("RESULT UNVERIFIED (ambiguous: multiple injections matched)")
        return 1
    injection = injections[0]

    disk = None
    if args.disk_skill_md:
        try:
            disk = read_disk(args.disk_skill_md)
        except OSError as exc:
            print("ERROR cannot read disk SKILL.md: {}".format(exc))
            return 2

    return verify_candidate(
        jsonl, records, call, result, injection,
        args.sentinel, disk, args.expect_base, args.max_text)


if __name__ == "__main__":
    sys.exit(main())
