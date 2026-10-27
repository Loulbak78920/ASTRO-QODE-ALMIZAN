#!/usr/bin/env python3
"""Read-only evidence extraction from a Qoder session JSONL."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

SUMMARY_PREFIX = "This session is being continued from a previous conversation"
ANSWER_PREFIX = "Your questions have been answered:"
ERROR_PREFIX_RE = re.compile(
    r"(?i)^\s*(?:error:|traceback \(most recent call last\)|(?:[a-z_]*error|exception):|"
    r"native_browser_viewport_unavailable|exit code [1-9])"
)
TRUNCATED_RE = re.compile(r"(?i)(output truncated|exceeded the .*?(?:token|character) limit)")
DATA_URI_RE = re.compile(r"data:[\w.+-]+/[\w.+-]+;base64,[A-Za-z0-9+/=\s]+")
BASE64_RE = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")
URL_RE = re.compile(r"https?://[^\s\"'<>]+")
SIGNED_KEYS = ("Signature", "OSSAccessKeyId", "Expires", "token", "access_key", "secret")


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def redact(text: str) -> str:
    text = DATA_URI_RE.sub("<REDACTED_DATA_URI>", text)
    text = BASE64_RE.sub("<REDACTED_BASE64>", text)

    def replace_url(match: re.Match[str]) -> str:
        url = match.group(0)
        for key in SIGNED_KEYS:
            url = re.sub(rf"([?&]{re.escape(key)}=)[^&]+", r"\1***", url)
        return url[:160]

    return URL_RE.sub(replace_url, text)


def flatten_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                kind = item.get("type")
                if kind == "text":
                    parts.append(str(item.get("text", "")))
                elif kind == "tool_result":
                    parts.append(flatten_content(item.get("content")))
                elif kind == "image":
                    parts.append("<image>")
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
        return "\n".join(part for part in parts if part)
    if content is None:
        return ""
    return str(content)


def text_from_content(content: object) -> tuple[str, bool]:
    if isinstance(content, str):
        return content, False
    if isinstance(content, list):
        parts: list[str] = []
        has_image = False
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, dict) and item.get("type") == "image":
                has_image = True
                parts.append("<image>")
        return "\n".join(parts), has_image
    return "", False


def tool_result_blocks(content: object) -> list[dict]:
    if not isinstance(content, list):
        return []
    return [
        item
        for item in content
        if isinstance(item, dict) and item.get("type") == "tool_result"
    ]


def summarize_input(name: str, payload: object, max_chars: int) -> str:
    if not isinstance(payload, dict):
        return redact(ascii_text(payload))[:max_chars]
    if name == "mcp_call":
        tool = str(payload.get("toolName", "?"))
        args = payload.get("arguments")
        if not isinstance(args, dict):
            args = {}
        if isinstance(args.get("sessionId"), str):
            detail = "sessionId=" + args["sessionId"]
        elif isinstance(args.get("url"), str):
            detail = "url=" + args["url"]
        elif isinstance(args.get("function"), str):
            detail = "function[%dch]" % len(args["function"])
        elif isinstance(args.get("script"), str):
            detail = "script=" + args["script"][:80]
        elif isinstance(args.get("filePath"), str):
            detail = "filePath=" + args["filePath"]
        else:
            detail = "keys=" + ",".join(str(key) for key in list(args.keys())[:6])
        keys = ",".join(str(key) for key in args.keys())
        return redact(ascii_text(("%s(%s) %s" % (tool, keys, detail)).strip()))[:max_chars]
    for key in ("command", "file_path", "pattern", "path", "skill", "query", "url"):
        if key in payload:
            value = payload[key]
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            return redact(ascii_text(("%s=%s" % (key, value))))[:max_chars]
    return redact(ascii_text(json.dumps(payload, ensure_ascii=False)))[:max_chars]


def parse_input_keys(value: str) -> tuple[str, ...]:
    return tuple(key.strip() for key in value.split(",") if key.strip())


def render_input(
    name: str, payload: object, keys: tuple[str, ...], max_chars: int
) -> str:
    if not keys:
        return summarize_input(name, payload, max_chars)
    note = ""
    if isinstance(payload, dict):
        if "*" in keys:
            selected = list(payload.items())
        else:
            selected = [(key, payload[key]) for key in keys if key in payload]
            missing = [key for key in keys if key not in payload]
            if missing:
                note = " (missing=%s; available=%s)" % (
                    ",".join(missing),
                    ",".join(str(key) for key in payload),
                )
        body = "\n".join(
            "%s=%s"
            % (
                key,
                value
                if isinstance(value, str)
                else json.dumps(value, ensure_ascii=False),
            )
            for key, value in selected
        )
    else:
        body = ascii_text(payload)
    text = redact(ascii_text(body + note))
    if len(text) > max_chars:
        text = text[:max_chars] + "<TRUNCATED %d chars>" % (len(text) - max_chars)
    return text


def parse_line_range(value: str) -> tuple[int, int] | None:
    if not value:
        return None
    if "-" in value:
        start_text, end_text = value.split("-", 1)
        start, end = int(start_text), int(end_text)
    else:
        start = end = int(value)
    if start < 1 or end < start:
        raise ValueError(value)
    return start, end


def status_for(text: str, is_error: bool, tool_name: str | None = None) -> str:
    if TRUNCATED_RE.search(text):
        return "TRUNCATED"
    if is_error:
        return "ERROR"
    if tool_name in ("Read", "Grep", "Glob"):
        return "OK"
    if ERROR_PREFIX_RE.search(text):
        return "ERROR"
    return "OK"


def parse_session(path: Path, max_chars: int) -> tuple[dict, list[dict], list[dict], list[dict], dict]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    lines = raw.decode("utf-8-sig", errors="replace").splitlines()
    physical_lines = raw.count(b"\n") + (1 if raw and not raw.endswith(b"\n") else 0)
    mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    header = {
        "file": ascii_text(path),
        "lines": physical_lines,
        "size": len(raw),
        "mtime": mtime,
        "sha256": digest,
    }
    counts = {
        "records": 0,
        "invalid_json": 0,
        "type_user_records": 0,
        "human_users": 0,
        "summaries": 0,
        "meta": 0,
        "synthetic_answers": 0,
        "tool_result_records": 0,
        "attachments": 0,
        "tool_uses": 0,
        "results": 0,
        "paired_results": 0,
        "unpaired_results": 0,
        "errors": 0,
        "truncated": 0,
        "no_result_tools": 0,
    }
    users: list[dict] = []
    uses: list[dict] = []
    results: list[dict] = []
    uses_by_id: dict[str, dict] = {}
    uses_by_uuid: dict[str, dict] = {}

    for number, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            counts["invalid_json"] += 1
            continue
        if not isinstance(record, dict):
            counts["invalid_json"] += 1
            continue
        counts["records"] += 1
        timestamp = str(record.get("timestamp", ""))
        record_type = record.get("type")
        message = record.get("message") if isinstance(record.get("message"), dict) else {}
        role = message.get("role")
        content = message.get("content")
        is_meta = bool(record.get("isMeta"))
        tool_use_result = record.get("toolUseResult")
        record_uuid = record.get("uuid")
        parent_uuid = record.get("parentUuid")
        source_uuid = record.get("sourceToolAssistantUUID")

        if record_type == "attachment":
            counts["attachments"] += 1
            continue

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    use = {
                        "line": number,
                        "timestamp": timestamp,
                        "id": str(block.get("id", "")),
                        "name": str(block.get("name", "?")),
                        "input": block.get("input"),
                        "results": [],
                    }
                    uses.append(use)
                    counts["tool_uses"] += 1
                    if use["id"]:
                        uses_by_id[use["id"]] = use
                    if record_uuid:
                        uses_by_uuid[str(record_uuid)] = use

        if record_type != "user":
            continue

        counts["type_user_records"] += 1
        if is_meta:
            counts["meta"] += 1
            continue

        text, has_image = text_from_content(content)
        blocks = tool_result_blocks(content)

        if blocks:
            counts["tool_result_records"] += 1
            if (
                isinstance(tool_use_result, dict)
                and "questions" in tool_use_result
            ) or text.startswith(ANSWER_PREFIX) or ANSWER_PREFIX in text:
                counts["synthetic_answers"] += 1
            for block in blocks:
                result_text = flatten_content(block.get("content"))
                if not result_text and tool_use_result is not None:
                    result_text = flatten_content(tool_use_result)
                results.append(
                    {
                        "line": number,
                        "timestamp": timestamp,
                        "tool_use_id": str(block.get("tool_use_id", "")) or None,
                        "is_error": bool(block.get("is_error")),
                        "text": result_text,
                        "source": "tool_result",
                        "parent_uuid": str(parent_uuid) if parent_uuid else None,
                        "source_uuid": str(source_uuid) if source_uuid else None,
                        "use": None,
                    }
                )
                counts["results"] += 1
            continue

        if tool_use_result is not None:
            counts["tool_result_records"] += 1
            if (
                isinstance(tool_use_result, dict)
                and "questions" in tool_use_result
            ) or text.startswith(ANSWER_PREFIX) or ANSWER_PREFIX in text:
                counts["synthetic_answers"] += 1
            results.append(
                {
                    "line": number,
                    "timestamp": timestamp,
                    "tool_use_id": None,
                    "is_error": False,
                    "text": flatten_content(tool_use_result),
                    "source": "toolUseResult",
                    "parent_uuid": str(parent_uuid) if parent_uuid else None,
                    "source_uuid": str(source_uuid) if source_uuid else None,
                    "use": None,
                }
            )
            counts["results"] += 1
            continue

        if role != "user":
            continue
        if not text.strip() and not has_image:
            continue
        if text.startswith(SUMMARY_PREFIX):
            counts["summaries"] += 1
            continue
        if text.startswith(ANSWER_PREFIX):
            counts["synthetic_answers"] += 1
            continue
        users.append(
            {
                "line": number,
                "timestamp": timestamp,
                "text": text,
                "images": 1 if has_image else 0,
            }
        )
        counts["human_users"] += 1

    for result in results:
        use = uses_by_id.get(result["tool_use_id"]) if result["tool_use_id"] else None
        if use is None:
            fallback_uuid = result["source_uuid"] or result["parent_uuid"]
            if fallback_uuid:
                use = uses_by_uuid.get(fallback_uuid)
        result["use"] = use
        result["status"] = status_for(
            result["text"], result["is_error"], use["name"] if use else None
        )
        if use is not None:
            use["results"].append(result)
            counts["paired_results"] += 1
        else:
            counts["unpaired_results"] += 1
        if result["status"] == "ERROR":
            counts["errors"] += 1
        elif result["status"] == "TRUNCATED":
            counts["truncated"] += 1

    for use in uses:
        if not use["results"]:
            counts["no_result_tools"] += 1

    return header, users, uses, results, counts


def filter_users(users: list[dict], args: argparse.Namespace, line_range: tuple[int, int] | None) -> list[dict]:
    out = []
    for user in users:
        if line_range and not (line_range[0] <= user["line"] <= line_range[1]):
            continue
        if args.grep and args.grep.lower() not in user["text"].lower():
            continue
        out.append(user)
    return out


def build_rows(uses: list[dict], results: list[dict]) -> list[tuple[dict | None, dict | None]]:
    rows: list[tuple[dict | None, dict | None]] = []
    for use in uses:
        if use["results"]:
            for result in use["results"]:
                rows.append((use, result))
        else:
            rows.append((use, None))
    for result in results:
        if result["use"] is None:
            rows.append((None, result))
    return rows


def filter_rows(
    uses: list[dict],
    results: list[dict],
    args: argparse.Namespace,
    line_range: tuple[int, int] | None,
    max_chars: int,
    errors_only: bool,
) -> list[tuple[dict | None, dict | None]]:
    tools = {name.strip().lower() for name in args.tool.split(",") if name.strip()}
    input_keys = parse_input_keys(args.input_keys)
    out: list[tuple[dict | None, dict | None]] = []
    for use, result in build_rows(uses, results):
        if errors_only and (result is None or result["status"] not in ("ERROR", "TRUNCATED")):
            continue
        if tools:
            if use is None or use["name"].lower() not in tools:
                continue
        if line_range:
            use_line = use["line"] if use else None
            result_line = result["line"] if result else None
            if not (
                (use_line is not None and line_range[0] <= use_line <= line_range[1])
                or (result_line is not None and line_range[0] <= result_line <= line_range[1])
            ):
                continue
        if args.grep:
            blob = " ".join(
                [
                    use["name"] if use else "",
                    render_input(use["name"], use.get("input"), input_keys, max_chars)
                    if use
                    else "",
                    result["text"] if result else "",
                ]
            )
            if args.grep.lower() not in blob.lower():
                continue
        out.append((use, result))
    return out


def format_user(user: dict, max_chars: int) -> str:
    text = redact(user["text"])[:max_chars]
    return ascii_text(
        "L%d %s USER images=%d len=%d | %s"
        % (user["line"], user["timestamp"], user["images"], len(user["text"]), text)
    )


def format_pair(
    use: dict | None,
    result: dict | None,
    max_chars: int,
    input_keys: tuple[str, ...] = (),
) -> str:
    if use is None and result is not None:
        tool = "?"
        uid = result["tool_use_id"] or "?"
        use_line = "-"
        use_ts = ""
    else:
        tool = use["name"] if use else "?"
        uid = (use["id"] if use else "") or "?"
        use_line = str(use["line"]) if use else "-"
        use_ts = use["timestamp"] if use else ""
    if result is None:
        result_line = "-"
        result_ts = ""
        status = "NO_RESULT"
        output = ""
    else:
        result_line = str(result["line"])
        result_ts = result["timestamp"]
        status = result["status"]
        output = redact(result["text"])[:max_chars]
    input_text = (
        render_input(use["name"], use.get("input"), input_keys, max_chars)
        if use
        else ""
    )
    parts = [
        "L%s->L%s %s..%s %s id=%s status=%s"
        % (use_line, result_line, use_ts, result_ts, tool, uid, status)
    ]
    if input_text:
        parts.append("IN: " + input_text)
    if output:
        parts.append("OUT: " + output)
    return ascii_text(" | ".join(parts))


def pair_to_dict(
    use: dict | None,
    result: dict | None,
    max_chars: int,
    input_keys: tuple[str, ...] = (),
) -> dict:
    return {
        "tool": use["name"] if use else None,
        "tool_use_id": (use["id"] if use else None) or (result["tool_use_id"] if result else None),
        "use_line": use["line"] if use else None,
        "result_line": result["line"] if result else None,
        "use_timestamp": use["timestamp"] if use else None,
        "result_timestamp": result["timestamp"] if result else None,
        "status": result["status"] if result else "NO_RESULT",
        "input": (
            render_input(use["name"], use.get("input"), input_keys, max_chars)
            if use
            else ""
        ),
        "output": redact(result["text"])[:max_chars] if result else "",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only evidence extraction from a Qoder session JSONL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  py -3 extract_session_evidence.py session.jsonl --users\n"
            "  py -3 extract_session_evidence.py session.jsonl --errors\n"
            "  py -3 extract_session_evidence.py session.jsonl --pairs --tool mcp_call --line 235-265\n"
            "  py -3 extract_session_evidence.py session.jsonl --pairs --tool Edit --line 2436 --input-keys old_string,new_string --max-chars 2000\n"
            "  py -3 extract_session_evidence.py session.jsonl --pairs --grep motif --max-chars 2000\n"
            "  py -3 extract_session_evidence.py session.jsonl --json --errors\n"
        ),
    )
    parser.add_argument("jsonl", type=Path, help="path to <sessionId>.jsonl")
    parser.add_argument("--users", action="store_true", help="show human user messages only")
    parser.add_argument("--pairs", action="store_true", help="show paired tool calls and results")
    parser.add_argument("--errors", action="store_true", help="show only ERROR or TRUNCATED results")
    parser.add_argument("--tool", default="", help="comma-separated tool names to keep")
    parser.add_argument(
        "--grep",
        default="",
        help=(
            "case-insensitive substring filter over tool name, rendered input "
            "(truncated by --max-chars), and full result text"
        ),
    )
    parser.add_argument("--line", default="", help="line range, e.g. 230-330 or 243")
    parser.add_argument("--max-items", type=int, default=200, help="maximum lines per section")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=300,
        help="maximum characters per excerpt (default 300, capped at 2000)",
    )
    parser.add_argument("--summary", action="store_true", help="show counts only")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON")
    parser.add_argument(
        "--input-keys",
        default="",
        help=(
            "comma-separated input keys to show instead of the IN summary, "
            "or * for all; all keys share the --max-chars budget"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = args.jsonl.expanduser()
    if not path.is_file():
        print("ERROR: file not found: %s" % ascii_text(path))
        return 2
    try:
        line_range = parse_line_range(args.line)
    except ValueError:
        print("ERROR: invalid --line value: %s" % ascii_text(args.line))
        return 2
    max_chars = max(80, min(args.max_chars, 2000))
    max_items = max(1, args.max_items)
    input_keys = parse_input_keys(args.input_keys)
    try:
        header, users, uses, results, counts = parse_session(path, max_chars)
    except OSError as exc:
        print("ERROR: cannot read %s: %s" % (ascii_text(path), ascii_text(exc)))
        return 2

    explicit_pair = bool(args.pairs or args.errors or args.tool or args.input_keys)
    explicit_user = bool(args.users)
    if args.summary and not (explicit_pair or explicit_user or args.grep or args.line):
        mode = "summary"
    elif explicit_user and not explicit_pair:
        mode = "users"
    elif explicit_pair and not explicit_user:
        mode = "pairs"
    elif explicit_user and explicit_pair:
        mode = "both"
    elif args.grep or args.line:
        mode = "both"
    else:
        mode = "default"
    errors_only = bool(args.errors or mode == "default")

    filtered_users = filter_users(users, args, line_range)
    filtered_rows = filter_rows(uses, results, args, line_range, max_chars, errors_only)

    if args.as_json:
        payload = {
            "file": header["file"],
            "lines": header["lines"],
            "size": header["size"],
            "mtime": header["mtime"],
            "sha256": header["sha256"],
            "counts": counts,
            "users": [
                {
                    "line": user["line"],
                    "timestamp": user["timestamp"],
                    "images": user["images"],
                    "text": redact(user["text"])[:max_chars],
                }
                for user in filtered_users
            ],
            "pairs": [
                pair_to_dict(use, result, max_chars, input_keys)
                for use, result in filtered_rows
            ],
            "unpaired_results": [
                pair_to_dict(None, result, max_chars, input_keys)
                for use, result in filtered_rows
                if use is None
            ],
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print("# file=%s" % header["file"])
    print(
        "# lines=%d size=%d mtime=%s sha256=%s"
        % (header["lines"], header["size"], header["mtime"], header["sha256"])
    )
    print("# counts: " + " ".join("%s=%s" % (key, counts[key]) for key in counts))

    if mode == "summary":
        return 0

    if mode in ("users", "both", "default"):
        printed = 0
        for user in filtered_users:
            if printed >= max_items:
                break
            print(format_user(user, max_chars))
            printed += 1
        if len(filtered_users) > printed:
            print("# truncated users: printed=%d matched=%d" % (printed, len(filtered_users)))
        elif printed == 0:
            print("# no matching users")

    if mode in ("pairs", "both", "default"):
        printed = 0
        for use, result in filtered_rows:
            if printed >= max_items:
                break
            print(format_pair(use, result, max_chars, input_keys))
            printed += 1
        if len(filtered_rows) > printed:
            print("# truncated pairs: printed=%d matched=%d" % (printed, len(filtered_rows)))
        elif printed == 0:
            print("# no matching pairs")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
