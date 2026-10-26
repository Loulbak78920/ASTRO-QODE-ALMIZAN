#!/usr/bin/env python3
"""Read-only inventory of installed Qoder Skills (user-level and project-level)."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
SNAPSHOT_FORMAT = "qoder-skill-inventory/1"


def setup_streams():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def fail(message, code):
    print("ERROR: " + message, file=sys.stderr)
    raise SystemExit(code)


def require_yaml():
    try:
        import yaml
    except ImportError:
        fail("PyYAML is required; run: py -3 -m pip install pyyaml", 2)
    return yaml


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def resolve_project_root(arg, user_root):
    if arg:
        path = Path(arg).expanduser().resolve()
        if not path.is_dir():
            fail("project root not found: {}".format(path), 2)
        if path == user_root:
            fail("project root must differ from the user root: {}".format(path), 2)
        return path
    current = Path.cwd().resolve()
    for candidate in [current] + list(current.parents):
        path = candidate / ".qoder" / "skills"
        if path.is_dir() and path.resolve() != user_root:
            return path.resolve()
    return None


def scan_root(root, label, yaml, anomalies):
    records = []
    if root is None:
        return records
    if not root.is_dir():
        fail("{} root not found: {}".format(label, root), 2)
    try:
        entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
    except OSError as exc:
        fail("cannot list {}: {}".format(root, exc), 2)
    for entry in entries:
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        skill_md = entry / "SKILL.md"
        record = {
            "dir": entry.name,
            "root": label,
            "path": str(skill_md),
            "name": None,
            "description_sha256": None,
            "desc_chars": None,
            "size": None,
            "mtime_ns": None,
            "sha256": None,
            "has_skill_md": skill_md.is_file(),
        }
        if not skill_md.is_file():
            anomalies.append({"kind": "missing-skill-md", "root": label, "dir": entry.name})
            records.append(record)
            continue
        try:
            data = skill_md.read_bytes()
            record["mtime_ns"] = skill_md.stat().st_mtime_ns
        except OSError as exc:
            anomalies.append({"kind": "unreadable-skill-md", "root": label, "dir": entry.name, "detail": str(exc)})
            records.append(record)
            continue
        record["size"] = len(data)
        record["sha256"] = sha256_bytes(data)
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            anomalies.append({"kind": "bad-encoding", "root": label, "dir": entry.name, "detail": str(exc)})
            records.append(record)
            continue
        match = FM_RE.match(text)
        if not match:
            anomalies.append({"kind": "missing-frontmatter", "root": label, "dir": entry.name})
            records.append(record)
            continue
        try:
            meta = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            detail = str(exc).strip().splitlines()
            anomalies.append({
                "kind": "yaml-error",
                "root": label,
                "dir": entry.name,
                "detail": detail[0] if detail else "invalid YAML",
            })
            records.append(record)
            continue
        if not isinstance(meta, dict):
            anomalies.append({"kind": "frontmatter-not-mapping", "root": label, "dir": entry.name})
            records.append(record)
            continue
        name = meta.get("name")
        description = meta.get("description")
        if not isinstance(name, str) or not name.strip():
            anomalies.append({"kind": "missing-name", "root": label, "dir": entry.name})
        else:
            record["name"] = name
            if name != entry.name:
                anomalies.append({"kind": "name-dir-mismatch", "root": label, "dir": entry.name, "name": name})
            if not NAME_RE.match(name):
                anomalies.append({"kind": "invalid-name", "root": label, "dir": entry.name, "name": name})
        if not isinstance(description, str) or not description.strip():
            anomalies.append({"kind": "missing-description", "root": label, "dir": entry.name})
        else:
            record["description_sha256"] = sha256_bytes(description.encode("utf-8"))
            record["desc_chars"] = len(description)
            if "\n" in description or "\r" in description:
                anomalies.append({"kind": "multiline-description", "root": label, "dir": entry.name})
            if len(description) > 1024:
                anomalies.append({
                    "kind": "description-too-long",
                    "root": label,
                    "dir": entry.name,
                    "chars": len(description),
                })
        records.append(record)
    return records


def find_duplicates(records):
    seen = {}
    for record in records:
        if record["name"]:
            seen.setdefault(record["name"], []).append(record)
    return {name: items for name, items in seen.items() if len(items) > 1}


def load_groups(path, local_names):
    try:
        groups = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        fail("cannot read groups file: {}".format(exc), 2)
    except json.JSONDecodeError as exc:
        fail("groups file is not valid JSON: {}".format(exc), 2)
    if not isinstance(groups, dict):
        fail("groups file must be a JSON object: {theme: [skill, ...]}", 2)
    errors = []
    assigned = {}
    for theme, names in groups.items():
        if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
            errors.append("group {!r}: value must be a list of skill names".format(theme))
            continue
        for name in names:
            if name not in local_names:
                errors.append("unknown skill in group {!r}: {}".format(theme, name))
            assigned.setdefault(name, []).append(theme)
    for name, themes in sorted(assigned.items()):
        if len(themes) > 1:
            errors.append("skill assigned to several groups: {} -> {}".format(name, ", ".join(themes)))
    for name in sorted(local_names - set(assigned)):
        errors.append("unassigned skill: {}".format(name))
    return groups, errors


def compare_snapshot(path, records, counts):
    try:
        old = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        fail("cannot read snapshot: {}".format(exc), 2)
    except json.JSONDecodeError as exc:
        fail("snapshot is not valid JSON: {}".format(exc), 2)
    if old.get("format") != SNAPSHOT_FORMAT:
        fail("unsupported snapshot format: {!r}".format(old.get("format")), 2)
    old_records = old.get("skills") or []
    old_by_key = {(item.get("root"), item.get("dir")): item for item in old_records}
    new_by_key = {(item["root"], item["dir"]): item for item in records if item["has_skill_md"]}
    removed_keys = sorted(key for key in old_by_key if key not in new_by_key)
    added_keys = sorted(key for key in new_by_key if key not in old_by_key)
    removed = [old_by_key[key] for key in removed_keys]
    added = [new_by_key[key] for key in added_keys]
    moved = []
    for new_item in list(added):
        identity = new_item.get("name") or new_item["dir"]
        match = next((item for item in removed if (item.get("name") or item["dir"]) == identity), None)
        if match:
            moved.append({
                "name": identity,
                "from_root": match.get("root"),
                "to_root": new_item["root"],
            })
            removed.remove(match)
            added.remove(new_item)
    description_changed = []
    content_changed = []
    for key in sorted(set(old_by_key) & set(new_by_key)):
        before, after = old_by_key[key], new_by_key[key]
        label = after.get("name") or after["dir"]
        if (before.get("description_sha256") != after.get("description_sha256")
                or before.get("desc_chars") != after.get("desc_chars")):
            description_changed.append({
                "name": label,
                "root": after["root"],
                "desc_chars_before": before.get("desc_chars"),
                "desc_chars_after": after.get("desc_chars"),
            })
        elif before.get("sha256") != after.get("sha256"):
            content_changed.append({"name": label, "root": after["root"]})
    return {
        "snapshot_generated_at": old.get("generated_at"),
        "old_counts": old.get("counts"),
        "new_counts": counts,
        "added": ["{}/{}".format(item["root"], item["dir"]) for item in added],
        "removed": ["{}/{}".format(item["root"], item["dir"]) for item in removed],
        "moved": moved,
        "description_changed": description_changed,
        "content_changed": content_changed,
        "unchanged": len(set(old_by_key) & set(new_by_key)) - len(description_changed) - len(content_changed),
    }


def render_drift(drift):
    lines = ["", "## Drift vs snapshot ({})".format(drift["snapshot_generated_at"])]
    lines.append(
        "added: {} | removed: {} | moved: {} | description changed: {} | content changed: {} | unchanged: {}".format(
            len(drift["added"]),
            len(drift["removed"]),
            len(drift["moved"]),
            len(drift["description_changed"]),
            len(drift["content_changed"]),
            drift["unchanged"],
        )
    )
    if not any((drift["added"], drift["removed"], drift["moved"],
                drift["description_changed"], drift["content_changed"])):
        lines.append("- no drift detected")
    for item in drift["added"]:
        lines.append("- added: {}".format(item))
    for item in drift["removed"]:
        lines.append("- removed: {}".format(item))
    for item in drift["moved"]:
        lines.append("- moved: {}: {} -> {}".format(item["name"], item["from_root"], item["to_root"]))
    for item in drift["description_changed"]:
        lines.append("- description changed: {} ({}/{} chars -> {} chars)".format(
            item["name"], item["root"], item["desc_chars_before"], item["desc_chars_after"]))
    for item in drift["content_changed"]:
        lines.append("- content changed: {} ({})".format(item["name"], item["root"]))
    return lines


def render_text(generated_at, user_root, project_root, records, counts, duplicates,
                builtin, groups, group_errors, anomalies, drift):
    installed = [record for record in records if record["has_skill_md"]]
    lines = ["=== skill inventory ==="]
    lines.append("generated: {}".format(generated_at))
    lines.append("user root: {} | count: {}".format(user_root, counts["user"]))
    if project_root is None:
        lines.append("project root: not found (no .qoder/skills in cwd or parents) | count: 0")
    else:
        lines.append("project root: {} | count: {}".format(project_root, counts["project"]))
    lines.append("local total: {} = {} user + {} project".format(
        counts["local"], counts["user"], counts["project"]))
    if builtin:
        lines.append("built-in/plugin (declared, not on disk): {}".format(len(builtin)))
    lines.append("duplicates across roots: {}".format(
        "none" if not duplicates else ", ".join(sorted(duplicates))))
    lines.append("anomalies: {}".format(len(anomalies)))

    for label, title in (("user", "User-level"), ("project", "Project-level")):
        section = [record for record in installed if record["root"] == label]
        lines.append("")
        lines.append("## {} ({})".format(title, len(section)))
        lines.extend("- {}".format(record["name"] or record["dir"]) for record in section)

    if builtin:
        lines.append("")
        lines.append("## Built-in / plugin (declared, {})".format(len(builtin)))
        lines.extend("- {}".format(name) for name in builtin)

    if groups is not None:
        lines.append("")
        if group_errors:
            lines.append("## Groups (INVALID)")
            lines.extend("- {}".format(error) for error in group_errors)
        else:
            total = sum(len(names) for names in groups.values())
            lines.append("## Groups (validated: {} assigned = {} local total)".format(total, counts["local"]))
            for theme in sorted(groups):
                names = groups[theme]
                lines.append("- {} ({}): {}".format(theme, len(names), ", ".join(names)))

    lines.append("")
    lines.append("## Anomalies")
    if not anomalies:
        lines.append("none")
    for item in anomalies:
        details = []
        for key in ("root", "dir", "name", "chars", "detail"):
            if item.get(key) not in (None, ""):
                details.append(str(item[key]))
        lines.append("- {}: {}".format(item["kind"], " | ".join(details)))

    if group_errors:
        lines.append("")
        lines.append("## Group errors")
        lines.extend("- {}".format(error) for error in group_errors)

    if drift is not None:
        lines.extend(render_drift(drift))
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Read-only inventory of installed Qoder Skills.")
    parser.add_argument("--user-root", help="user-level skills root (default: ~/.qoder/skills)")
    parser.add_argument("--project-root", help="project-level skills root (default: nearest .qoder/skills)")
    parser.add_argument("--snapshot", help="write a JSON snapshot to this path (the only write)")
    parser.add_argument("--compare", help="compare against a snapshot previously written with --snapshot")
    parser.add_argument("--groups", help="JSON object {theme: [skill, ...]} kept as a validated view")
    parser.add_argument("--builtin", default="", help="comma-separated built-in/plugin names (never counted as local)")
    parser.add_argument("--format", choices=("md", "json"), default="md")
    return parser.parse_args(argv)


def main(argv=None):
    setup_streams()
    args = parse_args(argv)
    yaml = require_yaml()

    if args.user_root:
        user_root = Path(args.user_root).expanduser().resolve()
        if not user_root.is_dir():
            fail("user root not found: {}".format(user_root), 2)
    else:
        user_root = (Path.home() / ".qoder" / "skills").resolve()
        if not user_root.is_dir():
            fail("user root not found: {}".format(user_root), 2)
    project_root = resolve_project_root(args.project_root, user_root)

    anomalies = []
    records = scan_root(user_root, "user", yaml, anomalies)
    records += scan_root(project_root, "project", yaml, anomalies)
    counts = {
        "user": sum(1 for record in records if record["root"] == "user" and record["has_skill_md"]),
        "project": sum(1 for record in records if record["root"] == "project" and record["has_skill_md"]),
    }
    counts["local"] = counts["user"] + counts["project"]

    duplicates = find_duplicates(records)
    for name, items in sorted(duplicates.items()):
        anomalies.append({
            "kind": "duplicate-name",
            "name": name,
            "detail": ", ".join(item["root"] for item in items),
        })

    builtin = [name.strip() for name in args.builtin.split(",") if name.strip()]
    local_names = {record["name"] for record in records if record["name"]}
    for name in builtin:
        if name in local_names:
            anomalies.append({"kind": "builtin-also-local", "name": name})

    groups = None
    group_errors = []
    if args.groups:
        groups, group_errors = load_groups(args.groups, local_names)

    generated_at = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    snapshot = {
        "format": SNAPSHOT_FORMAT,
        "generated_at": generated_at,
        "user_root": str(user_root),
        "project_root": str(project_root) if project_root else None,
        "counts": counts,
        "skills": [record for record in records if record["has_skill_md"]],
        "anomalies": anomalies,
    }
    drift = compare_snapshot(args.compare, records, counts) if args.compare else None

    if args.snapshot:
        target = Path(args.snapshot).expanduser()
        if not target.parent.is_dir():
            fail("snapshot directory does not exist: {}".format(target.parent), 2)

    if args.format == "json":
        payload = dict(snapshot)
        payload["duplicates"] = {name: [item["root"] for item in items]
                                 for name, items in sorted(duplicates.items())}
        payload["builtin"] = builtin
        payload["groups"] = groups
        payload["group_errors"] = group_errors
        payload["drift"] = drift
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(generated_at, user_root, project_root, records, counts,
                          duplicates, builtin, groups, group_errors, anomalies, drift))

    if args.snapshot:
        try:
            target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            fail("cannot write snapshot: {}".format(exc), 2)
        if args.format == "md":
            print("\nsnapshot written: {}".format(target))

    return 1 if (anomalies or group_errors) else 0


if __name__ == "__main__":
    raise SystemExit(main())
