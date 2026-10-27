#!/usr/bin/env python3
"""Safely inspect or replace the description scalar of a SKILL.md frontmatter.

Read-only unless `replace --apply` is given. All output is ASCII JSON.
Exit codes: 0 success, 1 invariant or candidate failure, 2 environment or usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

MAX_DESCRIPTION = 1024
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_ENV = 2


class GuardError(Exception):
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


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_keepends(text: str) -> list[str]:
    lines = []
    start = 0
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\r":
            if index + 1 < length and text[index + 1] == "\n":
                lines.append(text[start:index + 2])
                index += 2
            else:
                lines.append(text[start:index + 1])
                index += 1
            start = index
        elif char == "\n":
            lines.append(text[start:index + 1])
            index += 1
            start = index
        else:
            index += 1
    if start < length:
        lines.append(text[start:])
    return lines


def strip_eol(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


def eol_of(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return ""


def eol_profile(lines: list[str]) -> tuple[str, dict]:
    crlf = sum(1 for line in lines if line.endswith("\r\n"))
    lf = sum(1 for line in lines if line.endswith("\n") and not line.endswith("\r\n"))
    cr = sum(1 for line in lines if line.endswith("\r") and not line.endswith("\r\n"))
    kinds = [name for name, count in (("CRLF", crlf), ("LF", lf), ("CR", cr)) if count]
    if len(kinds) > 1:
        return "MIXED", {"crlf": crlf, "lf": lf, "cr": cr}
    return (kinds[0] if kinds else "NONE"), {"crlf": crlf, "lf": lf, "cr": cr}


def load_skill(skill_dir: Path) -> dict:
    if yaml is None:
        raise GuardError("PyYAML is not installed; run 'py -3 -m pip install pyyaml'", EXIT_ENV)
    target = skill_dir / "SKILL.md"
    if not target.is_file():
        raise GuardError(f"SKILL.md not found in {skill_dir}", EXIT_ENV)
    data = target.read_bytes()
    bom = data.startswith(b"\xef\xbb\xbf")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise GuardError(f"SKILL.md is not valid UTF-8: {exc}", EXIT_ENV)
    lines = split_keepends(text)
    eol, eol_counts = eol_profile(lines)
    if eol == "MIXED":
        raise GuardError("mixed line endings; normalize the file before editing", EXIT_ENV)
    if not lines or strip_eol(lines[0]).strip() != "---":
        raise GuardError("SKILL.md must start with a '---' frontmatter line", EXIT_FAIL)
    end = None
    for index in range(1, len(lines)):
        if strip_eol(lines[index]).strip() == "---":
            end = index
            break
    if end is None:
        raise GuardError("frontmatter closing '---' not found", EXIT_FAIL)
    frontmatter = "\n".join(strip_eol(line) for line in lines[1:end])
    try:
        metadata = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        raise GuardError(f"frontmatter YAML parse error: {exc}", EXIT_FAIL)
    if not isinstance(metadata, dict):
        raise GuardError("frontmatter YAML root is not a mapping", EXIT_FAIL)
    try:
        node = yaml.compose(frontmatter)
    except yaml.YAMLError as exc:
        raise GuardError(f"frontmatter compose error: {exc}", EXIT_FAIL)
    value_node = None
    key_node = None
    if isinstance(node, yaml.MappingNode):
        for candidate_key, candidate_value in node.value:
            if isinstance(candidate_key, yaml.ScalarNode) and candidate_key.value == "description":
                key_node = candidate_key
                value_node = candidate_value
                break
    if value_node is None or key_node is None:
        raise GuardError("description key not found in frontmatter", EXIT_FAIL)
    if key_node.start_mark.column != 0:
        raise GuardError("description is not a top-level column-0 key", EXIT_FAIL)
    if not isinstance(value_node, yaml.ScalarNode):
        raise GuardError("description value is not a YAML scalar", EXIT_FAIL)
    description = metadata.get("description")
    if not isinstance(description, str):
        raise GuardError("description is missing or not a string", EXIT_FAIL)
    if "\n" in description or "\r" in description:
        raise GuardError("description contains a line break", EXIT_FAIL)
    span = value_node.end_mark.line - value_node.start_mark.line + 1
    if span != 1:
        raise GuardError(f"description spans {span} YAML lines; only single-line values are supported", EXIT_FAIL)
    line_index = 1 + value_node.start_mark.line
    if line_index >= len(lines) or not strip_eol(lines[line_index]).startswith("description:"):
        raise GuardError("description line could not be located reliably", EXIT_FAIL)
    quote_style = value_node.style or "plain"
    if quote_style not in ("'", '"', "plain"):
        raise GuardError(f"unsupported description style: {quote_style}", EXIT_FAIL)
    body = "".join(lines[end + 1:])
    return {
        "target": target,
        "data": data,
        "text": text,
        "lines": lines,
        "bom": bom,
        "eol": eol,
        "eol_counts": eol_counts,
        "frontmatter_end": end,
        "metadata": metadata,
        "description": description,
        "description_line_index": line_index,
        "description_line": strip_eol(lines[line_index]),
        "quote_style": quote_style,
        "span": span,
        "body": body,
        "body_lines": len(body.splitlines()),
    }


def encode_scalar(value: str, style: str) -> str:
    if style == '"':
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return '"' + escaped + '"'
    if style == "'":
        return "'" + value.replace("'", "''") + "'"
    return value


def validate_candidate(candidate: str, style: str) -> str:
    if not candidate.strip():
        raise GuardError("candidate is empty", EXIT_FAIL)
    if len(candidate) > MAX_DESCRIPTION:
        raise GuardError(f"candidate is {len(candidate)} chars; limit is {MAX_DESCRIPTION}", EXIT_FAIL)
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in candidate):
        raise GuardError("candidate contains a control character", EXIT_FAIL)
    encoded = encode_scalar(candidate, style)
    try:
        parsed = yaml.safe_load("description: " + encoded)
    except yaml.YAMLError as exc:
        raise GuardError(f"candidate is not valid YAML in {style} style: {exc}", EXIT_FAIL)
    if not isinstance(parsed, dict) or parsed.get("description") != candidate:
        raise GuardError(f"candidate cannot round-trip in {style} style; keep the existing quote style", EXIT_FAIL)
    return encoded


def canonical_prefix(skill: dict, encoded: str) -> str:
    match = re.fullmatch(r"(description:[ \t]+)(.*)", skill["description_line"])
    if not match:
        raise GuardError("description line does not match 'description: value'", EXIT_FAIL)
    if match.group(2) != encoded:
        raise GuardError("description line has extra content, comments, or non-canonical quoting; edit it manually once", EXIT_FAIL)
    return match.group(1)


def build_plan(skill: dict, candidate: str) -> dict:
    encoded = validate_candidate(candidate, skill["quote_style"])
    old_encoded = encode_scalar(skill["description"], skill["quote_style"])
    prefix = canonical_prefix(skill, old_encoded)
    if candidate == skill["description"]:
        return {"changed": False, "encoded": encoded, "prefix": prefix}
    line_index = skill["description_line_index"]
    new_line = prefix + encoded + eol_of(skill["lines"][line_index])
    new_lines = list(skill["lines"])
    new_lines[line_index] = new_line
    new_text = "".join(new_lines)
    new_bytes = new_text.encode("utf-8")
    if skill["bom"]:
        new_bytes = b"\xef\xbb\xbf" + new_bytes
    return {
        "changed": True,
        "encoded": encoded,
        "prefix": prefix,
        "new_line": new_line,
        "new_text": new_text,
        "new_bytes": new_bytes,
    }


def read_candidate(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise GuardError(f"cannot read candidate: {exc}", EXIT_ENV)
    if raw.startswith(b"\xef\xbb\xbf"):
        raise GuardError("candidate must not start with a UTF-8 BOM", EXIT_FAIL)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GuardError(f"candidate is not valid UTF-8: {exc}", EXIT_FAIL)
    if text.endswith("\r\n"):
        text = text[:-2]
    elif text.endswith("\n"):
        text = text[:-1]
    if "\r" in text or "\n" in text:
        raise GuardError("candidate must contain exactly one line", EXIT_FAIL)
    if not text.strip():
        raise GuardError("candidate is empty", EXIT_FAIL)
    return text


def check_backup_location(skill_dir: Path, backup_dir: Path) -> None:
    skill_resolved = skill_dir.resolve()
    backup_resolved = backup_dir.resolve()
    if os.path.normcase(str(skill_resolved)) == os.path.normcase(str(backup_resolved)):
        raise GuardError("backup directory must be outside the skill directory", EXIT_ENV)
    try:
        common = Path(os.path.commonpath([str(skill_resolved), str(backup_resolved)]))
    except ValueError:
        common = None
    if common is not None and os.path.normcase(str(common)) == os.path.normcase(str(skill_resolved)):
        raise GuardError("backup directory must be outside the skill directory", EXIT_ENV)


def write_backup(skill_dir: Path, backup_dir: Path, data: bytes) -> Path:
    check_backup_location(skill_dir, backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = backup_dir / f"SKILL.md.{stamp}.bak"
    counter = 1
    while backup.exists():
        backup = backup_dir / f"SKILL.md.{stamp}.{counter}.bak"
        counter += 1
    with open(backup, "xb") as handle:
        handle.write(data)
    if sha256(backup.read_bytes()) != sha256(data):
        raise GuardError("backup verification failed", EXIT_ENV)
    return backup


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=".SKILL.md.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def verify_write(skill: dict, candidate: str, new_bytes: bytes) -> dict:
    if new_bytes == skill["data"]:
        raise GuardError("replacement produced identical bytes", EXIT_ENV)
    after = load_skill(skill["target"].parent)
    old_metadata = {key: value for key, value in skill["metadata"].items() if key != "description"}
    new_metadata = {key: value for key, value in after["metadata"].items() if key != "description"}
    checks = {
        "description_matches": after["description"] == candidate,
        "length_matches": len(after["description"]) == len(candidate) and len(after["description"]) <= MAX_DESCRIPTION,
        "name_preserved": after["metadata"].get("name") == skill["metadata"].get("name"),
        "other_keys_preserved": old_metadata == new_metadata,
        "eol_preserved": after["eol"] == skill["eol"] and after["eol_counts"] == skill["eol_counts"],
        "bom_preserved": after["bom"] == skill["bom"],
        "line_count_preserved": len(after["lines"]) == len(skill["lines"]),
        "body_bytes_preserved": after["body"] == skill["body"],
        "body_line_count_preserved": after["body_lines"] == skill["body_lines"],
        "quote_style_preserved": after["quote_style"] == skill["quote_style"],
        "description_span_one": after["span"] == 1,
    }
    if len(after["lines"]) == len(skill["lines"]):
        diff_lines = [index for index, (old, new) in enumerate(zip(skill["lines"], after["lines"])) if old != new]
    else:
        diff_lines = [-1]
    checks["only_description_line_changed"] = diff_lines == [skill["description_line_index"]]
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise GuardError("post-write invariant failed: " + ", ".join(failed), EXIT_FAIL, checks=checks)
    return checks


def cmd_inspect(args) -> int:
    skill_dir = Path(args.skill_dir)
    skill = load_skill(skill_dir)
    emit({
        "ok": True,
        "command": "inspect",
        "skill_dir": str(skill_dir),
        "name": skill["metadata"].get("name"),
        "name_matches_dir": skill["metadata"].get("name") == skill_dir.resolve().name,
        "description_len": len(skill["description"]),
        "remaining": MAX_DESCRIPTION - len(skill["description"]),
        "over_limit": len(skill["description"]) > MAX_DESCRIPTION,
        "description_line": skill["description_line_index"] + 1,
        "description_span": skill["span"],
        "quote_style": skill["quote_style"],
        "eol": skill["eol"],
        "eol_counts": skill["eol_counts"],
        "bom": skill["bom"],
        "body_lines": skill["body_lines"],
        "file_bytes": len(skill["data"]),
        "sha256": sha256(skill["data"]),
        "editable": True,
    })
    return EXIT_OK


def cmd_anchors(args) -> int:
    skill = load_skill(Path(args.skill_dir))
    if not args.anchor:
        raise GuardError("at least one --anchor is required", EXIT_ENV)
    anchors = []
    for anchor in args.anchor:
        if anchor == "":
            raise GuardError("empty anchor", EXIT_ENV)
        anchors.append({"anchor": anchor, "count": skill["description"].count(anchor)})
    unique = all(item["count"] == 1 for item in anchors)
    payload = {
        "ok": True,
        "command": "anchors",
        "description_len": len(skill["description"]),
        "anchors": anchors,
        "unique": unique,
    }
    if args.require_unique and not unique:
        payload["ok"] = False
        payload["error"] = "each anchor must occur exactly once"
        emit(payload)
        return EXIT_FAIL
    emit(payload)
    return EXIT_OK


def cmd_replace(args) -> int:
    skill_dir = Path(args.skill_dir)
    skill = load_skill(skill_dir)
    candidate = read_candidate(Path(args.candidate_file))
    replacement = build_plan(skill, candidate)
    sha_before = sha256(skill["data"])
    payload = {
        "ok": True,
        "command": "replace",
        "skill_dir": str(skill_dir),
        "dry_run": not args.apply,
        "old_len": len(skill["description"]),
        "new_len": len(candidate),
        "remaining": MAX_DESCRIPTION - len(candidate),
        "quote_style": skill["quote_style"],
        "eol": skill["eol"],
        "bom": skill["bom"],
        "description_line": skill["description_line_index"] + 1,
        "changed": replacement["changed"],
        "sha256_before": sha_before,
    }
    if args.expect_sha256 is not None:
        if args.expect_sha256.strip().lower() != sha_before:
            raise GuardError("--expect-sha256 does not match the current SKILL.md", EXIT_ENV)
    backup_dir = Path(args.backup_dir) if args.backup_dir else None
    if backup_dir is not None:
        check_backup_location(skill_dir, backup_dir)
        payload["backup_dir"] = str(backup_dir)
    if not replacement["changed"]:
        payload["status"] = "unchanged"
        emit(payload)
        return EXIT_OK
    if not args.apply:
        payload["status"] = "would-apply"
        payload["new_description"] = candidate
        payload["note"] = "dry-run; no bytes were written"
        emit(payload)
        return EXIT_OK
    if backup_dir is None:
        raise GuardError("--backup-dir is required with --apply", EXIT_ENV)
    backup = write_backup(skill_dir, backup_dir, skill["data"])
    payload["backup"] = str(backup)
    if sha256(skill["target"].read_bytes()) != sha_before:
        raise GuardError("SKILL.md changed before write; rerun the workflow", EXIT_ENV, backup=str(backup))
    atomic_write(skill["target"], replacement["new_bytes"])
    try:
        checks = verify_write(skill, candidate, replacement["new_bytes"])
    except Exception as exc:
        try:
            atomic_write(skill["target"], skill["data"])
            restored = sha256(skill["target"].read_bytes()) == sha_before
        except OSError:
            restored = False
        emit({
            "ok": False,
            "command": "replace",
            "error": f"{type(exc).__name__}: {exc}",
            "restored": restored,
            "backup": str(backup),
        })
        return EXIT_FAIL
    payload.update({
        "ok": True,
        "status": "applied",
        "sha256_after": sha256(skill["target"].read_bytes()),
        "invariants": checks,
    })
    emit(payload)
    return EXIT_OK


def build_parser() -> JsonArgumentParser:
    parser = JsonArgumentParser(description="Guard description edits in a SKILL.md frontmatter.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="measure the description without writing")
    inspect_parser.add_argument("skill_dir")
    inspect_parser.set_defaults(func=cmd_inspect)

    anchors_parser = subparsers.add_parser("anchors", help="count literal anchors in the parsed description")
    anchors_parser.add_argument("skill_dir")
    anchors_parser.add_argument("--anchor", action="append", default=[])
    anchors_parser.add_argument("--require-unique", action="store_true")
    anchors_parser.set_defaults(func=cmd_anchors)

    replace_parser = subparsers.add_parser("replace", help="replace the description line, dry-run by default")
    replace_parser.add_argument("skill_dir")
    replace_parser.add_argument("--candidate-file", required=True)
    replace_parser.add_argument("--backup-dir")
    replace_parser.add_argument("--apply", action="store_true")
    replace_parser.add_argument("--expect-sha256")
    replace_parser.set_defaults(func=cmd_replace)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GuardError as exc:
        payload = {"ok": False, "command": getattr(args, "command", None), "error": str(exc)}
        payload.update(exc.extra)
        emit(payload)
        return exc.code
    except SystemExit:
        raise
    except Exception as exc:
        emit({"ok": False, "command": getattr(args, "command", None), "error": f"{type(exc).__name__}: {exc}"})
        return EXIT_ENV


if __name__ == "__main__":
    sys.exit(main())
