#!/usr/bin/env python3
"""Read-only summary of a Qoder session JSONL for evidence audits."""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ERROR_RE = re.compile(
    r"(?i)(error|failed|failure|exception|traceback|syntaxerror|unavailable|"
    r"invalid|required property|exceeded|truncated|timeout|exit code [1-9])"
)
DATA_URI_RE = re.compile(r"data:[\w.+-]+/[\w.+-]+;base64,[A-Za-z0-9+/=\s]+")
BASE64_RE = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")
URL_RE = re.compile(r"https?://[^\s\"'<>]+")
SIGNED_QUERY_RE = re.compile(
    r"(?i)([?&](?:signature|ossaccesskeyid|expires|x-amz-signature|x-amz-credential|"
    r"x-amz-security-token|access_key|api_key|apikey|token|secret|password|passwd)=)[^&\s]+"
)
BEARER_RE = re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+")
KEY_VALUE_RE = re.compile(
    r"(?i)\b(api[_-]?key|password|passwd|secret|access[_-]?key|token)\b(\s*[:=]\s*)([^\s,;\"']+)"
)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I
)
SUMMARY_PREFIX = "This session is being continued from a previous conversation"


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def redact(text: str) -> str:
    text = DATA_URI_RE.sub("<REDACTED_DATA_URI>", text)
    text = BASE64_RE.sub("<REDACTED_BASE64>", text)
    text = BEARER_RE.sub(r"\1***", text)
    text = KEY_VALUE_RE.sub(r"\1\2***", text)

    def replace_url(match: re.Match[str]) -> str:
        url = SIGNED_QUERY_RE.sub(r"\1***", match.group(0))
        return url[:160]

    return URL_RE.sub(replace_url, text)


def flatten_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    if isinstance(content, list):
        parts = []
        for item in content:
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "text":
                parts.append(str(item.get("text", "")))
            elif kind == "tool_result":
                parts.append(flatten_content(item.get("content")))
            elif kind == "image":
                parts.append("<image>")
        return "\n".join(part for part in parts if part)
    return ""


def summarize_input(name: str, payload: object, max_chars: int) -> str:
    if not isinstance(payload, dict):
        return str(payload)[:max_chars]
    if name == "mcp_call":
        tool = str(payload.get("toolName", "?"))
        args = payload.get("arguments")
        if not isinstance(args, dict):
            args = {}
        keys = ",".join(str(key) for key in args.keys())
        detail = ""
        if isinstance(args.get("sessionId"), str):
            detail = "sessionId=" + args["sessionId"]
        elif isinstance(args.get("url"), str):
            detail = "url=" + args["url"]
        elif isinstance(args.get("function"), str):
            detail = "function[%dch]=%s" % (len(args["function"]), args["function"][:80])
        elif isinstance(args.get("script"), str):
            detail = "script=" + args["script"][:80]
        elif isinstance(args.get("filePath"), str):
            detail = "filePath=" + args["filePath"]
        if not detail:
            pairs = []
            for key, value in list(args.items())[:3]:
                pairs.append("%s=%s" % (key, str(value)[:60]))
            detail = " ".join(pairs)
        return ("%s(%s) %s" % (tool, keys, detail)).strip()[:max_chars]
    for key in ("command", "file_path", "pattern", "path", "skill", "query", "url"):
        if key in payload:
            value = payload[key]
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            return ("%s=%s" % (key, value))[:max_chars]
    return json.dumps(payload, ensure_ascii=False)[:max_chars]


def iter_records(path: Path):
    invalid = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                invalid += 1
                continue
            if not isinstance(record, dict):
                invalid += 1
                continue
            yield number, record
    if invalid:
        print("# skipped invalid JSON lines: %d" % invalid)


def classify(record: dict) -> list[dict]:
    message = record.get("message")
    if not isinstance(message, dict):
        return []
    role = message.get("role")
    content = message.get("content")
    is_meta = bool(record.get("isMeta"))
    tool_result = record.get("toolUseResult")
    items: list[dict] = []

    if isinstance(content, list):
        has_result = False
        for item in content:
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "tool_use":
                name = str(item.get("name", "?"))
                items.append(
                    {
                        "kind": "TOOL",
                        "name": name,
                        "text": summarize_input(name, item.get("input"), 100000),
                    }
                )
            elif kind == "tool_result":
                has_result = True
                items.append(
                    {
                        "kind": "RESULT",
                        "name": "",
                        "text": flatten_content(item.get("content")),
                    }
                )
            elif kind == "text" and role == "user" and not is_meta:
                text = str(item.get("text", ""))
                if not text.strip():
                    continue
                item_kind = "SUMMARY" if text.startswith(SUMMARY_PREFIX) else "USER"
                items.append({"kind": item_kind, "name": "", "text": text})
        if not has_result and tool_result is not None:
            items.append({"kind": "RESULT", "name": "", "text": flatten_content(tool_result)})
        return items

    if isinstance(content, str):
        if is_meta or role != "user" or not content.strip():
            return []
        item_kind = "SUMMARY" if content.startswith(SUMMARY_PREFIX) else "USER"
        return [{"kind": item_kind, "name": "", "text": content}]

    if tool_result is not None:
        return [{"kind": "RESULT", "name": "", "text": flatten_content(tool_result)}]
    return []


def parse_line_range(value: str) -> tuple[int, int]:
    if "-" in value:
        start_text, end_text = value.split("-", 1)
        start, end = int(start_text), int(end_text)
    else:
        start = end = int(value)
    if start < 1 or end < start:
        raise ValueError("expected 1 <= start <= end")
    return start, end


def scan_line_count(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for _ in handle:
            count += 1
    return count


def warn_if_changed(path: Path, before: os.stat_result) -> None:
    try:
        after = path.stat()
    except OSError as exc:
        print("# WARNING: cannot restat file: %s" % ascii_text(exc))
        return
    if (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
        print(
            "# WARNING: file changed during read (size %d -> %d); results may be inconsistent"
            % (before.st_size, after.st_size)
        )


def collect_refs(
    path: Path, line_range: tuple[int, int] | None, current_id: str
) -> dict[str, tuple[int, str]]:
    refs: dict[str, tuple[int, str]] = {}
    for number, record in iter_records(path):
        if line_range and not (line_range[0] <= number <= line_range[1]):
            continue
        timestamp = str(record.get("timestamp", ""))
        for item in classify(record):
            for match in UUID_RE.finditer(item["text"]):
                ref = match.group(0).lower()
                if ref == current_id or ref in refs:
                    continue
                refs[ref] = (number, timestamp)
    return refs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only summary of a Qoder session JSONL for evidence audits.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 audit_session.py session.jsonl --user\n"
            "  py -3 audit_session.py session.jsonl --errors\n"
            "  py -3 audit_session.py session.jsonl --grep \"required property\"\n"
            "  py -3 audit_session.py session.jsonl --tools mcp_call,Bash --line 230-330\n"
            "  py -3 audit_session.py session.jsonl --refs\n"
        ),
    )
    parser.add_argument("jsonl", type=Path, help="path to <sessionId>.jsonl")
    parser.add_argument("--user", action="store_true", help="show real user messages only")
    parser.add_argument("--errors", action="store_true", help="show records containing error-like text")
    parser.add_argument("--results", action="store_true", help="show tool results")
    parser.add_argument("--tools", default="", help="comma-separated tool names to show")
    parser.add_argument("--grep", default="", help="case-insensitive substring filter on summaries")
    parser.add_argument("--line", default="", help="line range, e.g. 230-330 or 243")
    parser.add_argument(
        "--refs",
        action="store_true",
        help="list UUID candidates (may include non-session IDs; excludes this session)",
    )
    parser.add_argument("--max-items", type=int, default=200, help="maximum number of output lines")
    parser.add_argument("--max-chars", type=int, default=300, help="maximum characters per summary")
    args = parser.parse_args(argv)

    path = args.jsonl.expanduser()
    if not path.is_file():
        print("ERROR: file not found: %s" % ascii_text(path))
        return 2
    max_chars = max(80, min(args.max_chars, 2000))
    max_items = max(1, args.max_items)
    tools = {name.strip().lower() for name in args.tools.split(",") if name.strip()}
    if args.line:
        try:
            line_range = parse_line_range(args.line)
        except ValueError as exc:
            print(
                "ERROR: invalid --line value: %s (%s)"
                % (ascii_text(args.line), ascii_text(exc))
            )
            return 2
    else:
        line_range = None

    try:
        stat = path.stat()
        total_lines = scan_line_count(path)
    except OSError as exc:
        print("ERROR: cannot read %s: %s" % (ascii_text(path), ascii_text(exc)))
        return 2

    mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds")
    print("# file=%s" % ascii_text(path))
    print("# lines=%d size=%d mtime=%s" % (total_lines, stat.st_size, mtime))

    if args.refs:
        refs = collect_refs(path, line_range, path.stem.lower())
        for ref, (number, timestamp) in refs.items():
            print("# ref %s first=L%d %s" % (ref, number, timestamp))
        if not refs:
            print("# no session references")
        warn_if_changed(path, stat)
        return 0

    printed = 0
    matched = 0
    for number, record in iter_records(path):
        if line_range and not (line_range[0] <= number <= line_range[1]):
            continue
        timestamp = str(record.get("timestamp", ""))
        for item in classify(record):
            text = redact(item["text"])
            kind = item["kind"]
            name = item["name"]
            if args.user and kind != "USER":
                continue
            if tools and (kind != "TOOL" or name.lower() not in tools):
                continue
            if args.errors and (kind not in ("RESULT", "TOOL") or not ERROR_RE.search(text)):
                continue
            if args.results and kind != "RESULT":
                continue
            if args.grep and args.grep.lower() not in text.lower():
                continue
            matched += 1
            if printed >= max_items:
                continue
            summary = " ".join(text.split())[:max_chars]
            label = "L%d %s %s" % (number, timestamp, kind)
            if name:
                label += " " + name
            print("%s: %s" % (label, ascii_text(summary)))
            printed += 1

    warn_if_changed(path, stat)
    if matched > printed:
        print("# truncated: printed=%d matched=%d; use --grep/--line/--max-items" % (printed, matched))
    elif printed == 0:
        print("# no matching records")
    else:
        print("# printed=%d matched=%d" % (printed, matched))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
