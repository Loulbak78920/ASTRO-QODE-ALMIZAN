#!/usr/bin/env python3
"""Copy a file, apply one exact replacement, and prove the copy changed."""
import argparse
import hashlib
import os
import re
import sys
from pathlib import Path


def out(line):
    print(line, flush=True)


def not_applied(reason, code=1):
    out("RESULT MUTATION_NOT_APPLIED reason=%s" % reason)
    return code


MSYS_PATTERNS = (
    re.compile(r"^/([A-Za-z])/(.*)$"),
    re.compile(r"^/cygdrive/([A-Za-z])/(.*)$"),
)


def normalize_path(raw):
    """Accept Git Bash /c/... paths and strip trailing separators."""
    if os.name == "nt":
        for pattern in MSYS_PATTERNS:
            match = pattern.match(raw)
            if match:
                raw = "%s:/%s" % (match.group(1), match.group(2))
                break
    return Path(os.path.normpath(raw))


def decode_hex(value, name):
    try:
        return bytes.fromhex(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        out("RESULT MUTATION_NOT_APPLIED reason=bad_%s" % name)
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Copy --source to --dest with exactly one replacement, "
                    "asserting the replacement was applied."
    )
    parser.add_argument("--source", required=True, help="file to copy (never modified)")
    parser.add_argument("--dest", required=True, help="new file to create")
    parser.add_argument("--old-hex", required=True, help="exact old text, UTF-8 encoded as hex")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--new-hex", help="replacement text, UTF-8 encoded as hex")
    group.add_argument("--new-text", help="replacement text, passed as-is")
    args = parser.parse_args(argv)

    source = normalize_path(args.source)
    dest = normalize_path(args.dest)

    if not source.is_file():
        return not_applied("source_missing", 2)
    if dest.exists():
        try:
            if os.path.samefile(source, dest):
                return not_applied("dest_equals_source", 2)
        except OSError:
            pass
        return not_applied("dest_exists", 2)
    try:
        if dest.resolve() == source.resolve():
            return not_applied("dest_equals_source", 2)
    except OSError:
        return not_applied("bad_path", 2)
    if not dest.parent.is_dir():
        return not_applied("dest_parent_missing", 2)

    old = decode_hex(args.old_hex, "old_hex")
    if old is None:
        return 2
    if old == "":
        return not_applied("empty_old", 2)

    if args.new_hex is not None:
        new = decode_hex(args.new_hex, "new_hex")
        if new is None:
            return 2
    else:
        new = args.new_text

    try:
        raw = source.read_bytes()
    except OSError:
        return not_applied("source_unreadable", 2)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return not_applied("source_not_utf8", 2)

    old_count = text.count(old)
    out("OLD_OCCURS %d" % old_count)
    if old_count != 1:
        return not_applied("old_count_%d" % old_count)

    mutated = text.replace(old, new)
    if mutated == text:
        return not_applied("no_change")
    new_count = mutated.count(new)
    out("NEW_OCCURS %d" % new_count)
    if new_count < 1:
        return not_applied("new_absent")

    source_sha = hashlib.sha256(raw).hexdigest()
    dest_bytes = mutated.encode("utf-8")
    dest_sha = hashlib.sha256(dest_bytes).hexdigest()
    if dest_sha == source_sha:
        return not_applied("hash_unchanged")

    try:
        dest.write_bytes(dest_bytes)
        written = hashlib.sha256(dest.read_bytes()).hexdigest()
        same_file = os.path.samefile(source, dest)
        source_after = hashlib.sha256(source.read_bytes()).hexdigest()
    except OSError:
        return not_applied("dest_write_failed", 2)

    if same_file:
        try:
            source.write_bytes(raw)
        except OSError:
            pass
        return not_applied("dest_equals_source_after_write", 2)
    if source_after != source_sha:
        return not_applied("source_modified_by_write", 2)

    out("SOURCE_SHA256 %s" % source_sha)
    out("DEST_SHA256 %s" % written)
    if written != dest_sha:
        try:
            dest.unlink()
        except OSError:
            pass
        return not_applied("hash_reread_mismatch")
    if written == source_sha:
        return not_applied("copy_matches_source")
    out("CHANGED yes")
    out("RESULT MUTATION_APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
