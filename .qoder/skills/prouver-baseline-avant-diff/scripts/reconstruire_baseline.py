#!/usr/bin/env python3
"""Rebuild an older file version by reversing known edits.

Each edit maps the text currently present ("new") back to the text present
before that edit ("old"). Every "new" must occur exactly once in the working
text. The rebuilt bytes are accepted only if their SHA-256, and optionally
their size and line count, equal the recorded values.

Exit codes: 0 = byte-exact, 1 = edit or fingerprint failure, 2 = usage/IO.
"""

import argparse
import hashlib
import json
import os
import re
import sys

SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass


def fail_usage(message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(2)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_edits(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        fail_usage("cannot read edits {}: {}".format(path, exc.strerror))
    except ValueError as exc:
        fail_usage("invalid edits JSON {}: {}".format(path, exc))
    if not isinstance(payload, list) or not payload:
        fail_usage("edits must be a non-empty JSON array")
    edits = []
    for index, item in enumerate(payload, 1):
        if not isinstance(item, dict):
            fail_usage("edit {} is not an object".format(index))
        missing = [key for key in ("new", "old") if key not in item]
        if missing:
            fail_usage("edit {} missing key(s): {}".format(
                index, ", ".join(missing)))
        new, old = item["new"], item["old"]
        if not isinstance(new, str) or not isinstance(old, str):
            fail_usage("edit {} keys new/old must be strings".format(index))
        if not new:
            fail_usage("edit {} has an empty new string".format(index))
        edit_id = item.get("id", "edit-{}".format(index))
        if not isinstance(edit_id, str) or not edit_id:
            fail_usage("edit {} has an invalid id".format(index))
        edits.append({"id": edit_id, "new": new, "old": old})
    return edits


def main():
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Rebuild an older version by reversing known edits.")
    parser.add_argument("--current", required=True,
                        help="file currently on disk")
    parser.add_argument("--edits", required=True,
                        help="JSON array of {id, new, old} in reverse order")
    parser.add_argument("--out", required=True,
                        help="reconstructed bytes, outside the target directory")
    parser.add_argument("--expect-sha256", required=True,
                        help="full 64-hex SHA-256 of the older version")
    parser.add_argument("--expect-size", type=int,
                        help="optional expected size in bytes")
    parser.add_argument("--expect-lines", type=int,
                        help="optional expected line count")
    parser.add_argument("--overwrite", action="store_true",
                        help="replace --out if it already exists")
    args = parser.parse_args()

    expected_sha = args.expect_sha256.lower()
    if not SHA_RE.match(expected_sha):
        fail_usage("--expect-sha256 must be a full 64-hex SHA-256, not a prefix")
    if args.expect_size is not None and args.expect_size < 0:
        fail_usage("--expect-size must be >= 0")
    if args.expect_lines is not None and args.expect_lines < 1:
        fail_usage("--expect-lines must be >= 1")

    current = os.path.abspath(args.current)
    out = os.path.abspath(args.out)
    target_dir = os.path.dirname(current)
    out_dir = os.path.dirname(out)
    if os.path.normcase(current) == os.path.normcase(out):
        fail_usage("--out must differ from --current")
    try:
        inside = os.path.commonpath(
            [os.path.normcase(target_dir), os.path.normcase(out_dir)]
        ) == os.path.normcase(target_dir)
    except ValueError:
        inside = False
    if inside:
        fail_usage("refusing to write inside the target directory: " + target_dir)
    if not os.path.isdir(out_dir):
        fail_usage("output directory does not exist: " + out_dir)
    if os.path.exists(out) and not args.overwrite:
        fail_usage("output already exists (use --overwrite): " + out)

    try:
        with open(current, "rb") as handle:
            current_raw = handle.read()
    except OSError as exc:
        fail_usage("cannot read {}: {}".format(current, exc.strerror))
    try:
        text = current_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail_usage("not valid UTF-8: {} ({})".format(current, exc.reason))

    edits = load_edits(args.edits)
    print("CURRENT size={} sha256={} lines={}".format(
        len(current_raw), sha256(current_raw), len(text.splitlines())))
    print("EDITS n={}".format(len(edits)))

    work = text
    for edit in edits:
        occurrences = work.count(edit["new"])
        print("EDIT {} occurrences={}".format(edit["id"], occurrences))
        if occurrences != 1:
            print("REASON: edit {} matched {} time(s), expected exactly 1".format(
                edit["id"], occurrences))
            print("RESULT: FAIL")
            return 1
        work = work.replace(edit["new"], edit["old"], 1)

    encoded = work.encode("utf-8")
    lines = len(work.splitlines())
    actual_sha = sha256(encoded)
    try:
        with open(out, "wb") as handle:
            handle.write(encoded)
    except OSError as exc:
        fail_usage("cannot write {}: {}".format(out, exc.strerror))

    print("OUT size={} sha256={} lines={}".format(
        len(encoded), actual_sha, lines))
    print("EXPECT size={} sha256={} lines={}".format(
        "any" if args.expect_size is None else args.expect_size,
        expected_sha,
        "any" if args.expect_lines is None else args.expect_lines))

    checks = [("sha256", actual_sha, expected_sha)]
    if args.expect_size is not None:
        checks.append(("size", len(encoded), args.expect_size))
    if args.expect_lines is not None:
        checks.append(("lines", lines, args.expect_lines))

    ok = True
    for label, actual, expected in checks:
        passed = actual == expected
        ok = ok and passed
        print("CHECK {} {} actual={} expected={}".format(
            label, "PASS" if passed else "FAIL", actual, expected))

    print("BYTE-EXACT {}".format("True" if ok else "False"))
    if not ok:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
