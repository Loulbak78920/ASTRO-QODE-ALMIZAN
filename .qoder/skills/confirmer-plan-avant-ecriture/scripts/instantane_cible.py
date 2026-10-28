#!/usr/bin/env python3
"""Snapshot or compare a target directory by size, mtime_ns and SHA-256.

Record mode writes a JSON baseline and may copy bytes for rollback.
Compare mode reports CURRENT / CHANGED / ADDED / REMOVED per file.

Exit codes: 0 unchanged or recorded, 1 target changed, 2 usage error.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

VERSION = 1
FIELDS = ("size", "mtime_ns", "sha256")


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass


def fail_usage(message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(2)


def sha256_file(path):
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    except OSError as exc:
        fail_usage("cannot read {}: {}".format(path, exc.strerror))
    return digest.hexdigest()


def split_rel(rel):
    return rel.split("/")


def absolute(root, rel):
    return os.path.join(root, *split_rel(rel))


def collect(root, excludes):
    entries = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            if any(fnmatch.fnmatchcase(rel, pattern) for pattern in excludes):
                continue
            if not os.path.isfile(path):
                continue
            try:
                stat = os.stat(path)
            except OSError as exc:
                fail_usage("cannot stat {}: {}".format(path, exc.strerror))
            entries[rel] = {
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
                "sha256": sha256_file(path),
            }
    return entries


def record(root, baseline_path, copy_root, excludes):
    entries = collect(root, excludes)
    copy_root_abs = None
    if copy_root:
        copy_root_abs = os.path.abspath(copy_root)
        root_abs = os.path.abspath(root)
        try:
            inside = os.path.commonpath([copy_root_abs, root_abs]) == root_abs
        except ValueError:
            inside = False
        if inside:
            fail_usage("--copie must live outside --racine")
        for rel in sorted(entries):
            destination = os.path.join(copy_root_abs, "files", *split_rel(rel))
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            try:
                shutil.copy2(absolute(root, rel), destination)
            except OSError as exc:
                fail_usage("cannot copy {}: {}".format(rel, exc.strerror))
            if sha256_file(destination) != entries[rel]["sha256"]:
                fail_usage("copy hash mismatch: " + rel)
            print("COPY {} OK".format(rel))

    payload = {
        "version": VERSION,
        "root": os.path.abspath(root),
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "copy_root": copy_root_abs,
        "excludes": list(excludes),
        "files": entries,
    }
    parent = os.path.dirname(os.path.abspath(baseline_path))
    if parent and not os.path.isdir(parent):
        fail_usage("baseline directory does not exist: " + parent)
    try:
        with open(baseline_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, indent=2) + "\n")
    except OSError as exc:
        fail_usage("cannot write baseline {}: {}".format(baseline_path, exc.strerror))

    print("SNAPSHOT root={} files={} excludes={} copy={}".format(
        payload["root"], len(entries), len(excludes), copy_root_abs or "none"))
    for rel in sorted(entries):
        meta = entries[rel]
        print("FILE {} size={} mtime_ns={} sha256={}".format(
            rel, meta["size"], meta["mtime_ns"], meta["sha256"]))
    print("RESULT: RECORDED")
    sys.exit(0)


def load_baseline(baseline_path):
    try:
        with open(baseline_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        fail_usage("cannot read baseline {}: {}".format(baseline_path, exc.strerror))
    except ValueError as exc:
        fail_usage("invalid baseline JSON {}: {}".format(baseline_path, exc))
    if not isinstance(payload, dict):
        fail_usage("baseline is not a JSON object: " + baseline_path)
    for key in ("version", "root", "files"):
        if key not in payload:
            fail_usage("baseline missing key: " + key)
    if not isinstance(payload["files"], dict):
        fail_usage("baseline files is not an object: " + baseline_path)
    return payload


def compare(root, baseline_path, excludes):
    baseline = load_baseline(baseline_path)
    if excludes:
        fail_usage("--exclure is fixed by --enregistrer; re-record to change it")
    root_abs = os.path.abspath(root)
    if os.path.normcase(os.path.abspath(baseline["root"])) != os.path.normcase(root_abs):
        fail_usage("baseline root differs: baseline={} current={}".format(
            baseline["root"], root_abs))
    old = baseline["files"]
    new = collect(root_abs, baseline.get("excludes", []))

    changed = 0
    print("COMPARE root={} baseline_files={} current_files={}".format(
        root_abs, len(old), len(new)))
    for rel in sorted(old):
        if rel not in new:
            print("COMPARE {} REMOVED".format(rel))
            changed += 1
            continue
        fields = [key for key in FIELDS if old[rel].get(key) != new[rel].get(key)]
        if fields:
            print("COMPARE {} CHANGED fields={}".format(rel, ",".join(fields)))
            changed += 1
        else:
            print("COMPARE {} CURRENT".format(rel))
    for rel in sorted(new):
        if rel not in old:
            print("COMPARE {} ADDED size={} sha256={}".format(
                rel, new[rel]["size"], new[rel]["sha256"]))
            changed += 1
    print("RESULT: {}".format("UNCHANGED" if changed == 0 else "CHANGED"))
    sys.exit(0 if changed == 0 else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Snapshot or compare a directory by size, mtime_ns, SHA-256.")
    parser.add_argument("--racine", required=True,
                        help="directory to snapshot or compare")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--enregistrer",
                        help="write baseline JSON at this path")
    action.add_argument("--comparer",
                        help="compare against this baseline JSON")
    parser.add_argument("--copie",
                        help="copy bytes for rollback into this directory")
    parser.add_argument("--exclure", action="append", default=[],
                        help="glob of relative path to skip (repeatable, record only)")
    args = parser.parse_args()

    configure_stdout()
    if not os.path.isdir(args.racine):
        fail_usage("--racine is not a directory: " + args.racine)
    if args.copie and not args.enregistrer:
        fail_usage("--copie requires --enregistrer")

    if args.enregistrer:
        record(args.racine, args.enregistrer, args.copie, args.exclure)
    compare(args.racine, args.comparer, args.exclure)


if __name__ == "__main__":
    main()
