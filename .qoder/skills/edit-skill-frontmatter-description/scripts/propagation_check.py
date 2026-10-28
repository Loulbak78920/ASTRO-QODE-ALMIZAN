#!/usr/bin/env python3
"""Read-only checks that a Skill description propagated into Qoder sessions.

`check` compares the injected body and the skill_listing attachments with the
SKILL.md on disk. `listing` evaluates only the listing layer, for description
edits where the Skill was deliberately not invoked. Never writes.
Exit codes: 0 match or no contradiction, 1 mismatch, 2 environment or usage.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HEADER = "Base directory for this skill:"
ELLIPSIS = "\u2026"
LISTING_DESC_CHARS = 300
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_ENV = 2


class CheckError(Exception):
    def __init__(self, message: str, code: int = EXIT_FAIL, **extra):
        super().__init__(message)
        self.code = code
        self.extra = extra


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        emit({"ok": False, "error": "usage: " + message})
        raise SystemExit(EXIT_ENV)


def emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")
    sys.stdout.flush()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_timestamp(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        seconds = float(value)
        return seconds / 1000.0 if seconds > 1e11 else seconds
    if not isinstance(value, str):
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def unquote_scalar(raw: str) -> str:
    if len(raw) >= 2 and raw.startswith('"') and raw.endswith('"'):
        try:
            return json.loads(raw)
        except ValueError:
            return raw[1:-1]
    if len(raw) >= 2 and raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    return raw


def read_skill(skill_dir: Path) -> dict:
    target = skill_dir / "SKILL.md"
    if not target.is_file():
        raise CheckError("SKILL.md not found in " + str(skill_dir), EXIT_ENV)
    data = target.read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CheckError("SKILL.md is not valid UTF-8: " + str(exc), EXIT_ENV)
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise CheckError("SKILL.md does not start with a frontmatter line", EXIT_FAIL)
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        raise CheckError("frontmatter closing marker not found", EXIT_FAIL)
    name = None
    description = None
    for line in lines[1:end]:
        stripped = line.rstrip("\r\n")
        if name is None and stripped.startswith("name:"):
            name = unquote_scalar(stripped[len("name:"):].strip())
        if description is None and stripped.startswith("description:"):
            description = unquote_scalar(stripped[len("description:"):].strip())
    if not name:
        raise CheckError("name key not found in frontmatter", EXIT_FAIL)
    body = "".join(lines[end + 1:])
    stat = target.stat()
    return {
        "name": name,
        "description": description or "",
        "body": body,
        "body_stripped": body.strip(),
        "size": len(data),
        "mtime": stat.st_mtime,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def parse_injection(number: int, obj: dict, content: str) -> dict:
    first_line = content.split("\n", 1)[0]
    declared = first_line[len(HEADER):].strip()
    body = content.split("\n\n", 1)[1] if "\n\n" in content else ""
    marker = "\n\nARGUMENTS:"
    trailer = ""
    if marker in body:
        body, trailer = body.split(marker, 1)
        trailer = "ARGUMENTS:" + trailer
    stripped = body.strip()
    return {
        "line": number,
        "timestamp": obj.get("timestamp"),
        "timestamp_epoch": parse_timestamp(obj.get("timestamp")),
        "declared_base_dir": declared,
        "injected_chars": len(content),
        "arguments_trailer_present": bool(trailer),
        "arguments_trailer_chars": len(trailer),
        "injected_body_raw_chars": len(body),
        "injected_body_stripped_chars": len(stripped),
        "injected_body_sha256": sha256_text(stripped),
        "injected_body_text": stripped,
    }


def parse_listing(number: int, obj: dict, att: dict, name: str) -> dict:
    content = att.get("content") or ""
    entry = None
    prefix = "- " + name
    for line in content.splitlines():
        if line == prefix or line.startswith(prefix + ": "):
            entry = line
            break
    segment = entry[len(prefix) + 2:] if entry is not None and entry.startswith(prefix + ": ") else ""
    return {
        "line": number,
        "timestamp": obj.get("timestamp"),
        "timestamp_epoch": parse_timestamp(obj.get("timestamp")),
        "is_initial": att.get("isInitial"),
        "skill_count": att.get("skillCount"),
        "name_present": entry is not None,
        "desc_present": bool(segment),
        "desc_segment_chars": len(segment),
        "ends_with_ellipsis": segment.endswith(ELLIPSIS),
        "desc_segment": segment,
    }


def scan_jsonl(path: Path, name: str) -> tuple:
    injections = []
    listings = []
    try:
        handle = io.open(path, encoding="utf-8")
    except OSError as exc:
        raise CheckError("cannot read session JSONL: " + str(exc), EXIT_ENV)
    with handle:
        try:
            for number, line in enumerate(handle, 1):
                if '"skill_listing"' not in line and HEADER not in line:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                att = obj.get("attachment")
                if isinstance(att, dict) and att.get("type") == "skill_listing":
                    listings.append(parse_listing(number, obj, att, name))
                    continue
                if obj.get("type") != "user" or obj.get("isMeta") is not True:
                    continue
                message = obj.get("message") or {}
                content = message.get("content")
                if not isinstance(content, str) or not content.startswith(HEADER):
                    continue
                injections.append(parse_injection(number, obj, content))
        except UnicodeDecodeError as exc:
            raise CheckError("session JSONL is not valid UTF-8: " + str(exc), EXIT_ENV)
    return injections, listings


def pick_injection(injections: list, wanted):
    if not injections:
        raise CheckError("no injection record found for this Skill", EXIT_ENV)
    if wanted:
        epoch = parse_timestamp(wanted)
        for item in injections:
            if item["timestamp"] == wanted or (epoch is not None and item["timestamp_epoch"] == epoch):
                return item
        raise CheckError("no injection record matches --injection-timestamp", EXIT_ENV)
    ordered = [item for item in injections if item["timestamp_epoch"] is not None]
    if not ordered:
        return injections[-1]
    return max(ordered, key=lambda item: item["timestamp_epoch"])


def same_dir(left: str, right: Path) -> bool:
    try:
        resolved = Path(left).resolve()
    except OSError:
        return False
    return os.path.normcase(str(resolved)) == os.path.normcase(str(right.resolve()))


def evaluate_listing(item: dict, description: str, reference_epoch: float) -> dict:
    segment = item.pop("desc_segment")
    prefix_body = segment[:-1] if segment.endswith(ELLIPSIS) else segment
    item["prefix_matches"] = bool(segment) and description.startswith(prefix_body)
    item["common_prefix_chars"] = len(os.path.commonprefix([prefix_body, description])) if segment else 0
    item["length_ok"] = bool(segment) and (
        segment == description
        or (len(segment) == LISTING_DESC_CHARS and segment.endswith(ELLIPSIS) and description.startswith(prefix_body))
    )
    item["stale"] = item["timestamp_epoch"] is None or item["timestamp_epoch"] < reference_epoch
    return item


def cmd_check(args) -> int:
    skill_dir = Path(args.skill_dir)
    skill = read_skill(skill_dir)
    injections_all, listings = scan_jsonl(Path(args.session_jsonl), skill["name"])
    injections = [item for item in injections_all if same_dir(item["declared_base_dir"], skill_dir)]
    counts = {"injection_records_total": len(injections_all), "injection_records_for_skill": len(injections)}
    if not injections:
        raise CheckError("no injection record found for this Skill", EXIT_ENV, **counts)
    try:
        injection = pick_injection(injections, args.injection_timestamp)
    except CheckError as exc:
        exc.extra.update(counts)
        raise
    injected_body = injection.pop("injected_body_text")
    dir_matches = same_dir(injection["declared_base_dir"], skill_dir)
    body_matches = injection["injected_body_sha256"] == sha256_text(skill["body_stripped"])
    sentinel_rows = [{"text": text, "count": injected_body.count(text)} for text in args.sentinel]
    sentinels_ok = all(row["count"] >= 1 for row in sentinel_rows)
    report_listings = [evaluate_listing(item, skill["description"], skill["mtime"]) for item in listings]
    usable = [item for item in report_listings if not item["stale"] and item["desc_present"]]
    if any(not (item["prefix_matches"] and item["length_ok"]) for item in usable):
        listing_status = "mismatch"
    elif any(item["prefix_matches"] and item["length_ok"] for item in usable):
        listing_status = "ok"
    else:
        listing_status = "unverified"
    injection_ok = dir_matches and body_matches and sentinels_ok
    verdict = "INJECTION_OK" if injection_ok else "FAIL"
    if injection_ok:
        verdict += "_LISTING_" + listing_status.upper()
    ok = injection_ok and listing_status != "mismatch"
    payload = {
        "ok": ok,
        "command": "check",
        "skill_dir": str(skill_dir),
        "skill_name": skill["name"],
        "disk_size": skill["size"],
        "disk_mtime_ns": skill["mtime_ns"],
        "disk_sha256": skill["sha256"],
        "disk_description_chars": len(skill["description"]),
        "disk_body_raw_chars": len(skill["body"]),
        "disk_body_stripped_chars": len(skill["body_stripped"]),
        "disk_body_sha256": sha256_text(skill["body_stripped"]),
        "injection_records_total": len(injections_all),
        "injection_records_for_skill": len(injections),
        "injection": injection,
        "dir_matches": dir_matches,
        "body_matches": body_matches,
        "sentinels": sentinel_rows,
        "sentinels_ok": sentinels_ok,
        "listings": report_listings,
        "listing_status": listing_status,
        "panel": "unverified_manual",
        "verdict": verdict,
    }
    emit(payload)
    return EXIT_OK if ok else EXIT_FAIL


def cmd_listing(args) -> int:
    skill_dir = Path(args.skill_dir)
    skill = read_skill(skill_dir)
    reference_epoch = skill["mtime"]
    if args.after:
        parsed = parse_timestamp(args.after)
        if parsed is None:
            raise CheckError("--after is not an ISO timestamp", EXIT_ENV)
        reference_epoch = parsed
    entries = []
    for raw_path in args.session_jsonl:
        _, listings = scan_jsonl(Path(raw_path), skill["name"])
        entries.extend(listings)
    report = [evaluate_listing(item, skill["description"], reference_epoch) for item in entries]
    report.sort(key=lambda item: item["timestamp_epoch"] if item["timestamp_epoch"] is not None else -1)
    fresh = [item for item in report if not item["stale"] and item["desc_present"]]
    if any(not (item["prefix_matches"] and item["length_ok"]) for item in fresh):
        status = "mismatch"
    elif fresh:
        status = "ok"
    else:
        status = "unverified"
    latest = next((item for item in reversed(report) if item["timestamp_epoch"] is not None), None)
    payload = {
        "ok": status != "mismatch",
        "command": "listing",
        "skill_dir": str(skill_dir),
        "skill_name": skill["name"],
        "disk_size": skill["size"],
        "disk_mtime_ns": skill["mtime_ns"],
        "disk_sha256": skill["sha256"],
        "disk_description_chars": len(skill["description"]),
        "session_jsonl": [str(Path(item)) for item in args.session_jsonl],
        "after_epoch": reference_epoch,
        "after_source": "argument" if args.after else "mtime",
        "entries_total": len(report),
        "entries_fresh": len(fresh),
        "latest_timestamp": latest["timestamp"] if latest else None,
        "listings": report,
        "injection": "unverified",
        "panel": "unverified_manual",
        "verdict": "LISTING_" + status.upper(),
    }
    emit(payload)
    return EXIT_OK if status != "mismatch" else EXIT_FAIL


def main(argv=None) -> int:
    parser = JsonArgumentParser(description="Check description propagation in a Qoder session JSONL.")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="read-only comparison of injection, body and listings")
    check.add_argument("skill_dir")
    check.add_argument("--session-jsonl", required=True)
    check.add_argument("--injection-timestamp")
    check.add_argument("--sentinel", action="append", default=[], required=True)
    check.set_defaults(func=cmd_check)
    listing = sub.add_parser("listing", help="read-only listing-layer comparison, without an injection")
    listing.add_argument("skill_dir")
    listing.add_argument("--session-jsonl", action="append", required=True, dest="session_jsonl")
    listing.add_argument("--after")
    listing.set_defaults(func=cmd_listing)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CheckError as exc:
        payload = {"ok": False, "command": getattr(args, "command", None), "error": str(exc)}
        payload.update(exc.extra)
        emit(payload)
        return exc.code
    except Exception as exc:
        emit({"ok": False, "command": getattr(args, "command", None), "error": type(exc).__name__ + ": " + str(exc)})
        return EXIT_ENV


if __name__ == "__main__":
    sys.exit(main())
