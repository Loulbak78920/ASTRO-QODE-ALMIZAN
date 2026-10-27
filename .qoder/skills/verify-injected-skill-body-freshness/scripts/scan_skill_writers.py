#!/usr/bin/env python3
"""Read-only scan of Qoder session JSONL files for writes to one SKILL.md."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOLS = ("Write", "Edit", "MultiEdit")


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass


def parse_ts(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def norm_path(value):
    return os.path.normcase(os.path.abspath(str(value)))


def result_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, str):
                parts.append(item)
        return " ".join(parts)
    return "" if content is None else str(content)


def collect_results(records):
    results = {}
    for record in records:
        content = (record.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "tool_result":
                continue
            tool_id = item.get("tool_use_id")
            if tool_id:
                results[tool_id] = {
                    "is_error": bool(item.get("is_error")),
                    "text": result_text(item.get("content")),
                }
    return results


def iter_files(args):
    if args.jsonl:
        return [Path(args.jsonl)]
    if args.scan_dir:
        path = Path(args.scan_dir)
        if not path.is_dir():
            raise FileNotFoundError(f"scan dir not found: {path}")
        return sorted(path.glob("*.jsonl"))
    raise ValueError("provide --jsonl or --scan-dir")


def main():
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="List Write/Edit tool calls targeting one SKILL.md in Qoder session JSONL files (read-only)."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--scan-dir", help="Directory containing *.jsonl session files")
    source.add_argument("--jsonl", help="One session JSONL file")
    parser.add_argument("--target", required=True, help="Exact SKILL.md path to match")
    parser.add_argument("--since", help="Only hits at or after this ISO-8601 time")
    parser.add_argument("--until", help="Only hits at or before this ISO-8601 time")
    parser.add_argument("--include-results", action="store_true", help="Include tool_result status and snippet")
    parser.add_argument("--json", action="store_true", help="Emit one JSON object")
    parser.add_argument("--max-snippet", type=int, default=160, help="Result snippet length (default 160)")
    args = parser.parse_args()

    target = norm_path(args.target)
    since = parse_ts(args.since)
    until = parse_ts(args.until)

    try:
        files = iter_files(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("ERROR: no *.jsonl files found", file=sys.stderr)
        return 2

    hits = []
    warnings = 0
    records_scanned = 0

    for file_path in files:
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            warnings += 1
            print(f"WARN: cannot read {file_path}: {exc}", file=sys.stderr)
            continue

        parsed = []
        for line_no, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                warnings += 1
                continue
            parsed.append((line_no, record))
            records_scanned += 1

        results = collect_results(record for _, record in parsed)

        for line_no, record in parsed:
            content = (record.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict) or item.get("type") != "tool_use":
                    continue
                if item.get("name") not in TOOLS:
                    continue
                tool_input = item.get("input") or {}
                file_value = tool_input.get("file_path")
                if not file_value or norm_path(file_value) != target:
                    continue
                stamp = parse_ts(record.get("timestamp"))
                if since and (stamp is None or stamp < since):
                    continue
                if until and (stamp is None or stamp > until):
                    continue
                tool_id = item.get("id")
                result = results.get(tool_id, {})
                if result.get("is_error"):
                    status = "ERROR"
                elif tool_id in results:
                    status = "OK"
                else:
                    status = "UNKNOWN"
                old_text = str(tool_input.get("old_string") or "")
                new_text = str(tool_input.get("new_string") or "")
                content_text = str(tool_input.get("content") or "")
                hit = {
                    "session": record.get("sessionId") or file_path.stem,
                    "jsonl": file_path.name,
                    "line": line_no,
                    "timestamp": record.get("timestamp"),
                    "tool": item.get("name"),
                    "file_path": file_value,
                    "old_len": len(old_text),
                    "new_len": len(content_text) if item.get("name") == "Write" else len(new_text),
                    "content_len": len(content_text),
                    "tool_use_id": tool_id,
                    "result": status,
                    "snippet": result.get("text", "")[: args.max_snippet],
                }
                hits.append(hit)

    hits.sort(key=lambda hit: (hit.get("timestamp") or "", hit.get("session") or "", hit.get("line") or 0))
    sessions = sorted({hit["session"] for hit in hits})
    payload = {
        "target": target,
        "files_scanned": len(files),
        "records_scanned": records_scanned,
        "warnings": warnings,
        "sessions": sessions,
        "hits": hits,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"TARGET: {args.target}")
        print(f"FILES: {len(files)} scanned; RECORDS: {records_scanned}; WARNINGS: {warnings}")
        print(f"{'SESSION':38} {'LINE':>5} {'TIMESTAMP':24} {'TOOL':5} {'OLD':>5} {'NEW':>5} {'RESULT':7}")
        for hit in hits:
            print(
                f"{hit['session'][:38]:38} {hit['line']:>5} {str(hit['timestamp'])[:24]:24} "
                f"{hit['tool']:5} {hit['old_len']:>5} {hit['new_len']:>5} {hit['result']:7}"
            )
        if args.include_results:
            for hit in hits:
                print(f"  {hit['session']}:{hit['line']} {hit['result']} {hit['snippet']!r}")
        print(f"SUMMARY: sessions={len(sessions)} hits={len(hits)}")
        if sessions:
            print("SESSIONS: " + ", ".join(sessions))

    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main())
