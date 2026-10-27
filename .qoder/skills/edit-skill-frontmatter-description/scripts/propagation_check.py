#!/usr/bin/env python3
"""Read-only check that a Skill description propagated into a Qoder session.

Compares the injected skill body and the skill_listing attachment in a session
JSONL with the SKILL.md on disk. Never writes.
Exit codes: 0 injection matches and no contradiction, 1 mismatch, 2 environment.
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


def evaluate_listing(item: dict, description: str, mtime: float) -> dict:
    segment = item.pop("desc_segment")
    prefix_body = segment[:-1] if segment.endswith(ELLIPSIS) else segment
    item["prefix_matches"] = bool(segment) and description.startswith(prefix_body)
    item["common_prefix_chars"] = len(os.path.commonprefix([prefix_body, description])) if segment else 0
    item["length_ok"] = bool(segment) and (
        segment == description
        or (len(segment) == LISTING_DESC_CHARS and segment.endswith(ELLIPSIS) and description.startswith(prefix_body))
    )
    item["stale"] = item["timestamp_epoch"] is None or item["timestamp_epoch"] < mtime
    return item


def main(argv=None) -> int:
    parser = JsonArgumentParser(description="Check description propagation in a Qoder session JSONL.")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="read-only comparison of injection, body and listings")
    check.add_argument("skill_dir")
    check.add_argument("--session-jsonl", required=True)
    check.add_argument("--injection-timestamp")
    check.add_argument("--sentinel", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        skill = read_skill(Path(args.skill_dir))
        injections, listings = scan_jsonl(Path(args.session_jsonl), skill["name"])
        injection = pick_injection(injections, args.injection_timestamp)
        injected_body = injection.pop("injected_body_text")
        dir_matches = same_dir(injection["declared_base_dir"], Path(args.skill_dir))
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
            "skill_dir": str(Path(args.skill_dir)),
            "skill_name": skill["name"],
            "disk_size": skill["size"],
            "disk_mtime_ns": skill["mtime_ns"],
            "disk_sha256": skill["sha256"],
            "disk_description_chars": len(skill["description"]),
            "disk_body_raw_chars": len(skill["body"]),
            "disk_body_stripped_chars": len(skill["body_stripped"]),
            "disk_body_sha256": sha256_text(skill["body_stripped"]),
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
