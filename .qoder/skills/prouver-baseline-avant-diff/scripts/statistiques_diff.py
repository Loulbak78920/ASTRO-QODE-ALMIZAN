#!/usr/bin/env python3
"""Compute line statistics from a unified diff and its two files.

The patch must come from `diff -u` or a compatible producer. The script
checks each hunk's declared spans against the patch body and the supplied
files, and never redefines hunk merging.

Exit codes: 0 = statistics produced, 2 = usage/IO/malformed input.
"""

import argparse
import hashlib
import os
import re
import sys

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass


def fail_usage(message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(2)


def read_file(path):
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        fail_usage("cannot read {}: {}".format(path, exc.strerror))
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail_usage("not valid UTF-8: {} ({})".format(path, exc.reason))
    return text, hashlib.sha256(raw).hexdigest()


def parse_patch(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        fail_usage("cannot read {}: {}".format(path, exc.strerror))
    except UnicodeDecodeError as exc:
        fail_usage("patch is not valid UTF-8: {} ({})".format(path, exc.reason))

    lines = text.splitlines()
    hunks = []
    current = None
    for number, line in enumerate(lines, 1):
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        if line.startswith("@@"):
            match = HUNK_RE.match(line)
            if not match:
                fail_usage("malformed hunk header at patch line {}: {}".format(
                    number, line))
            old_count = 1 if match.group(2) is None else int(match.group(2))
            new_count = 1 if match.group(4) is None else int(match.group(4))
            current = {
                "old_start": int(match.group(1)),
                "old_count": old_count,
                "new_start": int(match.group(3)),
                "new_count": new_count,
                "context": 0,
                "removed": 0,
                "added": 0,
            }
            hunks.append(current)
            continue
        if current is None:
            if line.strip():
                fail_usage("patch content before first hunk at line {}".format(number))
            continue
        if line.startswith("\\"):
            continue
        if line.startswith(" "):
            current["context"] += 1
        elif line.startswith("-"):
            current["removed"] += 1
        elif line.startswith("+"):
            current["added"] += 1
        elif line == "":
            fail_usage("blank line inside hunk at patch line {}".format(number))
        else:
            fail_usage("unexpected line inside hunk at patch line {}: {!r}".format(
                number, line))
    return hunks


def main():
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Compute line statistics from a unified diff.")
    parser.add_argument("--old", required=True, help="older version")
    parser.add_argument("--new", required=True, help="current version")
    parser.add_argument("--diff", required=True, help="unified diff of old -> new")
    args = parser.parse_args()

    old_text, old_sha = read_file(args.old)
    new_text, new_sha = read_file(args.new)
    old_lines = len(old_text.splitlines())
    new_lines = len(new_text.splitlines())
    hunks = parse_patch(args.diff)

    print("FILES old_lines={} new_lines={}".format(old_lines, new_lines))
    if not hunks:
        if old_sha != new_sha:
            fail_usage("empty patch but the two files differ")
        print("HUNKS=0")
        print("REMOVED=0 ADDED=0")
        print("MODE=IDENTICAL")
        print("UNCHANGED old={} new={}".format(old_lines, new_lines))
        print("RESULT: PASS")
        return 0

    for index, hunk in enumerate(hunks, 1):
        if hunk["old_count"] != hunk["context"] + hunk["removed"]:
            fail_usage(
                "hunk {} old span {} != context {} + removed {}".format(
                    index, hunk["old_count"], hunk["context"], hunk["removed"]))
        if hunk["new_count"] != hunk["context"] + hunk["added"]:
            fail_usage(
                "hunk {} new span {} != context {} + added {}".format(
                    index, hunk["new_count"], hunk["context"], hunk["added"]))
        if hunk["old_count"] and hunk["old_start"] + hunk["old_count"] - 1 > old_lines:
            fail_usage("hunk {} exceeds old file ({} lines)".format(
                index, old_lines))
        if hunk["new_count"] and hunk["new_start"] + hunk["new_count"] - 1 > new_lines:
            fail_usage("hunk {} exceeds new file ({} lines)".format(
                index, new_lines))

    removed = sum(hunk["removed"] for hunk in hunks)
    added = sum(hunk["added"] for hunk in hunks)
    unchanged_old = old_lines - removed
    unchanged_new = new_lines - added
    if unchanged_old < 0 or unchanged_new < 0:
        fail_usage("patch removes more lines than the supplied files contain")

    substitution = all(
        hunk["removed"] > 0 and hunk["removed"] == hunk["added"]
        for hunk in hunks
    )

    print("HUNKS={}".format(len(hunks)))
    print("REMOVED={} ADDED={}".format(removed, added))
    if substitution:
        print("MODE=SUBSTITUTION")
        print("CHANGED={}".format(removed))
    else:
        print("MODE=INSERT_DELETE")
    print("UNCHANGED old={} new={}".format(unchanged_old, unchanged_new))
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
