#!/usr/bin/env python3
"""Read-only count provenance checks for Qoder read_chat_session snapshots."""

import argparse
import json
import re
import sys
from pathlib import Path

COUNT_RE = re.compile(r"(\d+)\s*条消息")
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def load_json(path):
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise SystemExit(f"ERROR: cannot read {path}: {exc}")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"ERROR: {path} is not valid UTF-8: {exc}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ERROR: {path} is not valid JSON: {exc}")


def parse_path(path):
    if path.startswith("len(") and path.endswith(")"):
        return ("len", parse_path(path[4:-1]))
    tokens = []
    for key, idx in re.findall(r"([^.\[\]]+)|\[(\d+)\]", path):
        tokens.append(int(idx) if idx else key)
    if not tokens:
        raise SystemExit(f"ERROR: empty JSON path: {path!r}")
    return tokens


def get_value(obj, tokens):
    if isinstance(tokens, tuple) and tokens[0] == "len":
        return len(get_value(obj, tokens[1]))
    cur = obj
    for token in tokens:
        try:
            if isinstance(token, int):
                if not isinstance(cur, list):
                    raise TypeError
                cur = cur[token]
            else:
                if not isinstance(cur, dict):
                    raise TypeError
                cur = cur[token]
        except (KeyError, IndexError, TypeError):
            raise SystemExit(f"ERROR: path not found: {tokens!r}")
    return cur


def json_path(path):
    out = "$"
    for token in path:
        out += f"[{token}]" if isinstance(token, int) else f".{token}"
    return out


def iter_strings(obj, path=None):
    path = path or []
    if isinstance(obj, dict):
        for key, val in obj.items():
            yield from iter_strings(val, path + [key])
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            yield from iter_strings(val, path + [idx])
    elif isinstance(obj, str):
        yield path, obj


def iter_count_claims(text):
    for match in COUNT_RE.finditer(text):
        prefix = text[max(0, match.start() - 3):match.start()]
        if re.search(r"第\s*$", prefix):
            continue
        yield match


def session_ids(text):
    found = []
    for match in UUID_RE.finditer(text):
        prefix = text[max(0, match.start() - 40):match.start()]
        if "activeTurnId" in prefix[-30:] and not re.search(r"(?:来源)?会话|sessionId", prefix[-30:]):
            continue
        found.append((match.start(), match.end(), match.group(0)))
    for match in re.finditer(r"`([0-9a-f]{8})`", text):
        found.append((match.start(1), match.end(1), match.group(1)))
    for match in re.finditer(r"(?:会话|session|来源会话)\s*[`：:]?\s*([0-9a-f]{8})(?![0-9a-f-])", text, re.I):
        found.append((match.start(1), match.end(1), match.group(1)))
    found.sort()
    unique = []
    for item in found:
        if item not in unique:
            unique.append(item)
    return unique


def nearest_session(text, start, end):
    ids = session_ids(text)
    before = [item for item in ids if item[1] <= start]
    if before:
        return before[-1][2]
    after = [item for item in ids if item[0] >= end]
    if after:
        return after[0][2]
    return "-"


def cmd_summary(args):
    obj = load_json(args.snapshot)
    msgs = obj.get("messages")
    if not isinstance(msgs, list):
        raise SystemExit("ERROR: snapshot has no messages array")
    last = msgs[-1] if msgs else {}
    tools_total = sum(len(m.get("tools") or []) for m in msgs if isinstance(m, dict))
    print(f"file={args.snapshot}")
    print(f"sessionId={obj.get('sessionId')}")
    print(f"revision={obj.get('revision')}")
    print(f"runtimeState={obj.get('runtimeState')}")
    print(f"hasMoreBefore={obj.get('hasMoreBefore')}")
    print(f"messages={len(msgs)}")
    print(f"last={last.get('role')}/{last.get('status')}")
    print(f"tools_total={tools_total}")
    for idx, msg in enumerate(msgs):
        if isinstance(msg, dict) and msg.get("tools"):
            print(f"messages[{idx}].tools={len(msg['tools'])}")
    return 0


def cmd_path(args):
    obj = load_json(args.snapshot)
    value = get_value(obj, parse_path(args.json_path))
    if isinstance(value, (dict, list)):
        full = json.dumps(value, ensure_ascii=False)
    else:
        full = "" if value is None else str(value)
    print(f"path={args.json_path}")
    print(f"type={type(value).__name__}")
    if isinstance(value, (dict, list)):
        print(f"len={len(value)}")
    print(f"len_chars={len(full)}")
    preview = full.replace("\r", "").replace("\n", "\\n")
    print(f"preview={preview[:args.max_chars]}")
    hits = [match.group(1) for match in iter_count_claims(full)]
    if hits:
        print("count_claims=" + ", ".join(hits[:20]))
    return 0


def cmd_scan(args):
    obj = load_json(args.snapshot)
    printed = 0
    for path, text in iter_strings(obj):
        for match in iter_count_claims(text):
            if printed >= args.max_items:
                print(f"# TRUNCATED at {args.max_items} items")
                return 0
            printed += 1
            context = text[max(0, match.start() - args.max_chars // 2): match.end() + args.max_chars // 2]
            context = context.replace("\r", "").replace("\n", "\\n")
            print(f"path={json_path(path)} count={match.group(1)} session_near={nearest_session(text, match.start(), match.end())}")
            print(f"  context={context}")
    if not printed:
        print("NO_COUNT_CLAIMS")
    return 0


def doc_subject(lines):
    for line in lines:
        ids = session_ids(line)
        if ids:
            return ids[0][2]
    return None


def cmd_check_doc(args):
    obj = load_json(args.snapshot)
    msgs = obj.get("messages")
    if not isinstance(msgs, list):
        raise SystemExit("ERROR: snapshot has no messages array")
    subject = args.subject_session or obj.get("sessionId")
    expected = len(msgs)
    doc = Path(args.doc).read_text(encoding="utf-8-sig", errors="replace").splitlines()
    inferred = args.subject_session or doc_subject(doc)
    print(f"doc={args.doc}")
    print(f"subject={subject}")
    print(f"inferred={inferred}")
    print(f"expected_messages={expected}")
    if inferred and subject and inferred != subject:
        print("RESULT SUBJECT_MISMATCH")
        print(f"document subject {inferred} is not snapshot subject {subject}")
        return 1
    claims = []
    for lineno, line in enumerate(doc, 1):
        for match in iter_count_claims(line):
            count = int(match.group(1))
            ids = [item[2] for item in session_ids(line)]
            claim_session = ids[-1] if ids else inferred
            if claim_session and subject and claim_session != subject:
                status = "OTHER_SESSION"
            elif count == expected:
                status = "PASS"
            else:
                status = "FAIL"
            claims.append((lineno, count, claim_session, status, line.strip()))
    if not claims:
        print("RESULT FAIL")
        print("no count claims found")
        return 1
    worst = 0
    warnings = 0
    for lineno, count, claim_session, status, line in claims:
        print(f"L{lineno} claim={count} session={claim_session or '-'} status={status}")
        print(f"  {line[:args.max_chars]}")
        if status == "FAIL":
            worst = 1
        elif status == "OTHER_SESSION":
            warnings += 1
    print(f"warnings_other_session={warnings}")
    print("RESULT " + ("PASS" if worst == 0 else "FAIL"))
    return worst


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read-only count provenance checks for Qoder read_chat_session snapshots."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_summary = sub.add_parser("summary", help="show top-level snapshot counts")
    p_summary.add_argument("snapshot")
    p_summary.set_defaults(func=cmd_summary)

    p_path = sub.add_parser("path", help="read a JSON path such as messages[1].tools[31].output")
    p_path.add_argument("snapshot")
    p_path.add_argument("json_path")
    p_path.add_argument("--max-chars", type=int, default=300)
    p_path.set_defaults(func=cmd_path)

    p_scan = sub.add_parser("scan-counts", help="find 'N 条消息' claims and their JSON paths")
    p_scan.add_argument("snapshot")
    p_scan.add_argument("--max-items", type=int, default=50)
    p_scan.add_argument("--max-chars", type=int, default=240)
    p_scan.set_defaults(func=cmd_scan)

    p_check = sub.add_parser("check-doc", help="compare a document's count claims with a snapshot")
    p_check.add_argument("doc")
    p_check.add_argument("--snapshot", required=True)
    p_check.add_argument("--subject-session")
    p_check.add_argument("--max-chars", type=int, default=240)
    p_check.set_defaults(func=cmd_check_doc)

    return parser


def main(argv=None):
    configure_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
