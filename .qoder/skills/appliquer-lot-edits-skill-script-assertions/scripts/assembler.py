#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble labelled anchored edits into a draft Markdown file.

Spec contract (a Python module passed to --spec):

    EDITS = [
        ("exact", "label", OLD, NEW),
        ("section", "label", START, END, NEW_INNER),
        ("scoped", "label", START, END, [(OLD, NEW, EXPECTED_COUNT), ...]),
    ]

- exact: OLD must occur exactly once in the whole text.
- section: START and END must each occur once; the text strictly between
  them is replaced by NEW_INNER; both boundary markers are kept.
- scoped: boundary rules as section; each pair is applied in order inside
  the slice and must match EXPECTED_COUNT times.

Anchors are written with LF; they are normalised to LF and the draft is
rendered back with the source EOL (CRLF preserved). A failure aborts before
any draft is written.
"""

from __future__ import annotations

import argparse
import difflib
import re
import runpy
import sys
from pathlib import Path

BOM = b"\xef\xbb\xbf"


class EditError(Exception):
    def __init__(self, label, message):
        self.label = label
        self.message = message
        self.applied = 0
        super().__init__("%s: %s" % (label, message))


class UsageError(Exception):
    pass


def asc(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def norm(value):
    return value.replace("\r\n", "\n").replace("\r", "\n")


def detect_eol(text):
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    cr = text.count("\r") - crlf
    if crlf and (lf or cr):
        raise EditError(
            "eol",
            "mixed line endings (CRLF=%d LF=%d CR=%d)" % (crlf, lf, cr),
        )
    if cr and not crlf:
        raise EditError("eol", "CR-only line endings")
    return ("\r\n" if crlf else "\n"), crlf, lf


def decode_source(raw):
    bom = raw.startswith(BOM)
    try:
        text = raw.decode("utf-8-sig" if bom else "utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError("source is not valid UTF-8 (%s)" % type(exc).__name__)
    eol, _, _ = detect_eol(text)
    return norm(text), eol, bom


def encode_draft(text, eol, bom):
    rendered = text.replace("\n", eol) if eol != "\n" else text
    data = rendered.encode("utf-8")
    return (BOM + data) if bom else data


def split_frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise EditError("frontmatter", "first line is not ---")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines, index + 1
    raise EditError("frontmatter", "closing --- not found")


def parse_description(frontmatter_text):
    try:
        import yaml  # type: ignore
    except ImportError:
        match = re.search(r"^description:\s*(.+)$", frontmatter_text, re.M)
        if not match:
            raise EditError("yaml", "description missing (PyYAML unavailable)")
        raw = match.group(1).strip()
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            raw = raw[1:-1]
        return raw, "line-fallback"
    try:
        data = yaml.safe_load(frontmatter_text)
    except Exception as exc:  # noqa: BLE001 - surface the YAML class only
        raise EditError("yaml", "parse failed (%s)" % type(exc).__name__)
    if not isinstance(data, dict):
        raise EditError("yaml", "frontmatter is not a mapping")
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise EditError("yaml", "name missing or not a string")
    desc = data.get("description")
    if not isinstance(desc, str):
        raise EditError("yaml", "description missing or not a string")
    return desc, "pyyaml"


def boundary_slice(text, label, start, end):
    start = norm(start)
    end = norm(end)
    start_count = text.count(start)
    if start_count != 1:
        raise EditError(label, "start count=%d expected=1" % start_count)
    end_count = text.count(end)
    if end_count != 1:
        raise EditError(label, "end count=%d expected=1" % end_count)
    left = text.index(start) + len(start)
    if text.startswith("\n", left):
        left += 1
    right = text.index(end)
    if right < left:
        raise EditError(label, "end marker precedes start marker")
    return left, right


def apply_one(text, edit):
    if not isinstance(edit, (tuple, list)) or not edit:
        raise EditError("spec", "edit is not a non-empty tuple")
    kind = edit[0]
    if kind == "exact":
        if len(edit) != 4:
            raise EditError("spec", "exact expects (kind, label, old, new)")
        label, old, new = edit[1], norm(edit[2]), norm(edit[3])
        count = text.count(old)
        if count != 1:
            raise EditError(label, "count=%d expected=1" % count)
        return text.replace(old, new, 1)
    if kind == "section":
        if len(edit) != 5:
            raise EditError("spec", "section expects (kind, label, start, end, inner)")
        label, start, end, inner = edit[1], edit[2], edit[3], norm(edit[4])
        left, right = boundary_slice(text, label, start, end)
        return text[:left] + inner + text[right:]
    if kind == "scoped":
        if len(edit) != 5:
            raise EditError("spec", "scoped expects (kind, label, start, end, pairs)")
        label, start, end, pairs = edit[1], edit[2], edit[3], edit[4]
        left, right = boundary_slice(text, label, start, end)
        block = text[left:right]
        for index, pair in enumerate(pairs):
            pair_label = "%s[%d]" % (label, index)
            if not isinstance(pair, (tuple, list)) or len(pair) != 3:
                raise EditError(pair_label, "pair expects (old, new, expected)")
            old, new, expected = norm(pair[0]), norm(pair[1]), pair[2]
            if not isinstance(expected, int) or expected < 0:
                raise EditError(pair_label, "expected must be a non-negative integer")
            count = block.count(old)
            if count != expected:
                raise EditError(
                    pair_label, "count=%d expected=%d" % (count, expected)
                )
            block = block.replace(old, new)
        return text[:left] + block + text[right:]
    raise EditError("spec", "unknown kind=%s" % asc(kind))


def changed_ranges(before, after):
    old_lines = before.split("\n")
    new_lines = after.split("\n")
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines, autojunk=False)
    ranges = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        ranges.append("%s:%d-%d>%d-%d" % (tag, i1 + 1, i2, j1 + 1, j2))
    return ranges


def inspect_text(text):
    _, frontmatter_lines = split_frontmatter(text)
    total_lines = len(text.splitlines())
    lines = text.split("\n")
    frontmatter_text = "\n".join(lines[1 : frontmatter_lines - 1])
    desc, yaml_source = parse_description(frontmatter_text)
    if "\n" in desc or "\r" in desc:
        raise EditError("desc", "description is not a single line")
    return {
        "total_lines": total_lines,
        "frontmatter_lines": frontmatter_lines,
        "body_lines": total_lines - frontmatter_lines,
        "desc_lines": len(desc),
        "desc_source": yaml_source,
        "fences": sum(1 for line in lines if line.lstrip().startswith("```")),
        "h2": sum(1 for line in lines if line.startswith("## ")),
    }


def assemble(text, edits, body_max, desc_max, emit):
    if not isinstance(edits, (list, tuple)) or not edits:
        raise UsageError("spec EDITS must be a non-empty list")
    total = len(edits)
    current = text
    for index, edit in enumerate(edits):
        try:
            current = apply_one(current, edit)
        except EditError as exc:
            exc.applied = index
            raise
        label = edit[1] if len(edit) > 1 else "spec"
        emit("APPLY %s (%s)" % (asc(label), asc(edit[0])))
    info = inspect_text(current)
    errors = []
    if info["body_lines"] >= body_max:
        errors.append("BODY %d >= %d" % (info["body_lines"], body_max))
    if info["desc_lines"] > desc_max:
        errors.append("DESC %d > %d" % (info["desc_lines"], desc_max))
    if info["fences"] % 2:
        errors.append("FENCES %d is odd" % info["fences"])
    meta = dict(info)
    meta["edits"] = total
    meta["ranges"] = changed_ranges(text, current)
    meta["errors"] = errors
    return current, meta


def eol_label(eol):
    return "CRLF" if eol == "\r\n" else "LF"


MINI = (
    "---\n"
    "name: demo\n"
    'description: "d"\n'
    "---\n"
    "# Demo\n"
    "alpha\n"
    "beta\n"
    "## A\n"
    "one\n"
    "## B\n"
    "two\n"
)


def expect_error(name, source, edits, needle, failures):
    try:
        assemble(source, edits, 500, 1024, lambda _: None)
    except EditError as exc:
        rendered = "%s: %s" % (exc.label, exc.message)
        if needle in rendered:
            print("SELFTEST PASS %s" % name)
            return
        failures.append("%s: got %s, wanted %s" % (name, rendered, needle))
        return
    failures.append("%s: no EditError, wanted %s" % (name, needle))


def run_selftest():
    failures = []
    out, meta = assemble(
        MINI, [("exact", "e", "alpha", "ALPHA")], 500, 1024, lambda _: None
    )
    if "ALPHA" in out and meta["body_lines"] == 7:
        print("SELFTEST PASS exact-positive")
    else:
        failures.append("exact-positive: edit or body count wrong")

    out, _ = assemble(
        MINI,
        [("section", "s", "## A", "## B", "one\nONE\n")],
        500,
        1024,
        lambda _: None,
    )
    if out == MINI.replace("one\n", "one\nONE\n"):
        print("SELFTEST PASS section-positive")
    else:
        failures.append("section-positive: boundaries or inner text wrong")

    out, _ = assemble(
        MINI,
        [("scoped", "sc", "## A", "## B", [("one", "ONE", 1)])],
        500,
        1024,
        lambda _: None,
    )
    if out == MINI.replace("one\n", "ONE\n"):
        print("SELFTEST PASS scoped-positive")
    else:
        failures.append("scoped-positive: slice replacement wrong")

    expect_error(
        "exact-missing",
        MINI,
        [("exact", "e", "gamma", "G")],
        "e: count=0 expected=1",
        failures,
    )
    expect_error(
        "exact-duplicate",
        MINI.replace("beta", "alpha"),
        [("exact", "e", "alpha", "A")],
        "e: count=2 expected=1",
        failures,
    )
    expect_error(
        "section-missing",
        MINI,
        [("section", "s", "## Z", "## B", "x\n")],
        "s: start count=0 expected=1",
        failures,
    )

    trap = (
        "## S\n"
        'A="$DEPOT"\n'
        'B="$DEPOT"\n'
        'git -C "$DEPOT" merge\n'
        "## T\n"
    )
    expect_error(
        "order-trap",
        trap,
        [
            (
                "scoped",
                "trap",
                "## S",
                "## T",
                [
                    ('"$DEPOT"', '"$VERIF"', 3),
                    ('git -C "$DEPOT" merge', "X", 1),
                ],
            )
        ],
        "trap[1]: count=0 expected=1",
        failures,
    )

    _, meta = assemble(MINI, [("exact", "e", "alpha", "A")], 5, 1024, lambda _: None)
    if meta["errors"] and "BODY 7 >= 5" in meta["errors"][0]:
        print("SELFTEST PASS budget-fail")
    else:
        failures.append("budget-fail: no BODY error")

    try:
        detect_eol("a\r\nb\nc")
    except EditError as exc:
        if "mixed line endings" in exc.message:
            print("SELFTEST PASS eol-mixed")
        else:
            failures.append("eol-mixed: wrong message %s" % exc.message)
    else:
        failures.append("eol-mixed: no EditError")

    raw = BOM + MINI.replace("\n", "\r\n").encode("utf-8")
    text, eol, bom = decode_source(raw)
    out, _ = assemble(
        text, [("exact", "e", "alpha", "ALPHA")], 500, 1024, lambda _: None
    )
    data = encode_draft(out, eol, bom)
    if data.startswith(BOM) and data.count(b"\r\n") == data.count(b"\n"):
        if b"ALPHA" in data and re.search(rb"(?<!\r)\n", data) is None:
            print("SELFTEST PASS eol-bom-preserved")
        else:
            failures.append("eol-bom-preserved: content or lone LF")
    else:
        failures.append("eol-bom-preserved: BOM or CRLF lost")

    total = 10
    print("SELFTEST %d/%d" % (total - len(failures), total))
    for failure in failures:
        print("SELFTEST FAIL %s" % asc(failure))
    return 0 if not failures else 1


def load_spec(path):
    try:
        namespace = runpy.run_path(str(path))
    except Exception as exc:  # noqa: BLE001 - any spec failure is usage
        raise UsageError("cannot load spec (%s)" % type(exc).__name__)
    edits = namespace.get("EDITS")
    if not isinstance(edits, (list, tuple)) or not edits:
        raise UsageError("spec must define a non-empty EDITS list")
    return edits


def print_inspection(path):
    raw = path.read_bytes()
    text, eol, bom = decode_source(raw)
    info = inspect_text(text)
    print(
        "LOAD source=%s bytes=%d lines=%d eol=%s bom=%s"
        % (asc(path), len(raw), info["total_lines"], eol_label(eol), bom)
    )
    print("BODY %d" % info["body_lines"])
    print("DESC %d (%s)" % (info["desc_lines"], info["desc_source"]))
    print(
        "FENCES %d (%s)"
        % (info["fences"], "even" if info["fences"] % 2 == 0 else "odd")
    )
    print("H2 %d" % info["h2"])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Assemble anchored edits into a draft Markdown file."
    )
    parser.add_argument("--source", type=Path, help="live Markdown file (read only)")
    parser.add_argument("--out", type=Path, help="draft file to create")
    parser.add_argument("--spec", type=Path, help="Python module defining EDITS")
    parser.add_argument("--body-max", type=int, default=500)
    parser.add_argument("--desc-max", type=int, default=1024)
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_selftest()
    if args.inspect:
        if not args.source:
            parser.error("--source is required with --inspect")
        try:
            print_inspection(args.source)
            return 0
        except EditError as exc:
            print("FAIL %s: %s" % (asc(exc.label), asc(exc.message)))
            return 1
        except UsageError as exc:
            print("ERROR %s" % asc(exc))
            return 2
        except OSError as exc:
            print("ERROR io (%s)" % type(exc).__name__)
            return 2
    if not (args.source and args.out and args.spec):
        parser.error("--source, --out and --spec are required")
    if args.source.resolve() == args.out.resolve():
        print("ERROR out must differ from source")
        return 2

    try:
        raw = args.source.read_bytes()
        text, eol, bom = decode_source(raw)
        edits = load_spec(args.spec)
        print(
            "LOAD source=%s bytes=%d lines=%d eol=%s bom=%s"
            % (
                asc(args.source),
                len(raw),
                len(text.splitlines()),
                eol_label(eol),
                bom,
            )
        )
        print("SPEC edits=%d" % len(edits))

        def emit(line):
            print(asc(line))

        out_text, meta = assemble(
            text, edits, args.body_max, args.desc_max, emit
        )
        if meta["errors"]:
            for error in meta["errors"]:
                print("FAIL budget: %s" % asc(error))
            print("RESULT FAIL applied=%d/%d" % (meta["edits"], meta["edits"]))
            return 1
        data = encode_draft(out_text, eol, bom)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(data)
        print(
            "DRAFT out=%s bytes=%d lines=%d eol=%s bom=%s"
            % (
                asc(args.out),
                len(data),
                len(out_text.splitlines()),
                eol_label(eol),
                bom,
            )
        )
        print("BODY %d (< %d)" % (meta["body_lines"], args.body_max))
        print("DESC %d (<= %d, %s)" % (meta["desc_lines"], args.desc_max, meta["desc_source"]))
        print("FENCES %d (%s)" % (meta["fences"], "even" if meta["fences"] % 2 == 0 else "odd"))
        print("H2 %d" % meta["h2"])
        print("CHANGED %d" % len(meta["ranges"]))
        print("CHANGED_RANGES %s" % ",".join(meta["ranges"]))
        print("RESULT OK")
        return 0
    except EditError as exc:
        print("FAIL %s: %s" % (asc(exc.label), asc(exc.message)))
        print("RESULT FAIL applied=%d/%d" % (exc.applied, len(edits)))
        return 1
    except UsageError as exc:
        print("ERROR %s" % asc(exc))
        return 2
    except OSError as exc:
        print("ERROR io (%s)" % type(exc).__name__)
        return 2


if __name__ == "__main__":
    sys.exit(main())
