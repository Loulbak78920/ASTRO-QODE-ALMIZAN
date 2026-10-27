#!/usr/bin/env python3
"""Extract fenced bash blocks from a SKILL.md by unique anchor."""

import argparse
import hashlib
import pathlib
import re
import sys

FENCE = re.compile(r"^```bash[ \t]*\n(.*?)\n```[ \t]*$", re.S | re.M)
NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def fail(message):
    print(f"EXTRACT_FAIL {message}")
    print("EXTRACT_RESULT=FAIL")
    return 1


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(
        description="Extract fenced bash blocks from SKILL.md by unique anchor."
    )
    parser.add_argument("skill_md", help="path to SKILL.md")
    parser.add_argument(
        "--out-dir", required=True, help="directory for extracted blocks"
    )
    parser.add_argument(
        "--anchor",
        action="append",
        required=True,
        metavar="NAME=SUBSTRING",
        help="output name and unique substring identifying one bash block; repeatable",
    )
    args = parser.parse_args(argv)

    path = pathlib.Path(args.skill_md)
    try:
        raw = path.read_bytes()
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return fail(f"read {path} {exc}")

    blocks = FENCE.findall(text)
    print(f"BLOCK_COUNT={len(blocks)}")
    print(f"SKILL_SHA256={hashlib.sha256(raw).hexdigest()}")

    selected = []
    seen = set()
    errors = []
    for spec in args.anchor:
        name, sep, needle = spec.partition("=")
        if not sep or not name or not needle:
            errors.append(f"anchor format {spec!r} expected NAME=SUBSTRING")
            continue
        if not NAME_RE.fullmatch(name):
            errors.append(f"anchor name {name!r} invalid")
            continue
        if name in seen:
            errors.append(f"anchor name {name!r} duplicated")
            continue
        seen.add(name)
        hits = [block for block in blocks if needle in block]
        if len(hits) != 1:
            errors.append(f"{name} matches={len(hits)}")
            continue
        selected.append((name, hits[0]))

    if errors:
        for error in errors:
            print(f"EXTRACT_FAIL {error}")
        print("EXTRACT_RESULT=FAIL")
        return 1

    out_dir = pathlib.Path(args.out_dir)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return fail(f"mkdir {out_dir} {exc}")

    for name, body in selected:
        payload = body + "\n"
        target = out_dir / f"{name}.sh"
        try:
            target.write_text(payload, encoding="utf-8", newline="\n")
        except OSError as exc:
            return fail(f"write {target} {exc}")
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        lines = body.count("\n") + 1
        print(f"EXTRACT_OK {name} lines={lines} sha256={digest}")

    print("EXTRACT_RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
