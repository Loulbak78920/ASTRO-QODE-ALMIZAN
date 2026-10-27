#!/usr/bin/env python3
"""Read-only documentation/script output-key parity checker for a Skill package.

It extracts KEY=VALUE tokens from SKILL.md and references, extracts the keys a
script actually emits (emit("KEY", ...), print("KEY=..."), f-strings), and
reports documented keys that never appear in the script source.

It never executes the target script and never writes to the skill directory.
It checks presence only; branch-appropriate values and exit codes must be
asserted by fixtures (see references/harnais-fixtures.md).

Exit codes: 0 = PASS, 1 = documented key missing from scripts, 2 = usage or
environment error.
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

KEY_RE = re.compile(r"\b([A-Z][A-Z0-9_]{2,})\s*=\s*([^\s`\"'();,]+)")
RUNTIME_KEY_RE = re.compile(r"^([A-Z][A-Z0-9_]{2,})=")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^\s*```")
INLINE_CODE_RE = re.compile(r"`([^`]*)`")
EMIT_FUNCTIONS = {"emit", "emit_kv", "log_kv", "write_kv"}


class UsageError(Exception):
    pass


def safe(value):
    text = str(value)
    try:
        text.encode("ascii")
        return text
    except UnicodeEncodeError:
        return text.encode("ascii", "backslashreplace").decode("ascii")


def emit(key, value=None):
    if value is None:
        print(key)
    else:
        print("{}={}".format(key, safe(value)))


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def find_docs(skill, explicit):
    if explicit:
        return [Path(item) for item in explicit]
    docs = []
    skill_md = skill / "SKILL.md"
    if skill_md.is_file():
        docs.append(skill_md)
    refs = skill / "references"
    if refs.is_dir():
        docs.extend(sorted(refs.rglob("*.md")))
    return docs


def find_scripts(skill, explicit):
    if explicit:
        return [Path(item) for item in explicit]
    scripts = skill / "scripts"
    if scripts.is_dir():
        return sorted(scripts.rglob("*.py"))
    return []


def load_sections(path):
    lines = read_text(path).splitlines()
    sections = []
    heading = ""
    start = 1
    for number, raw in enumerate(lines, 1):
        match = HEADING_RE.match(raw)
        if match:
            if number > start:
                sections.append((heading, start, number - 1, "\n".join(lines[start - 1:number - 1])))
            heading = match.group(2).strip()
            start = number
    sections.append((heading, start, len(lines), "\n".join(lines[start - 1:])))
    return lines, sections


def section_at(sections, line_number):
    for heading, first, last, text in sections:
        if first <= line_number <= last:
            return heading, text
    return "", ""


def iter_code_fragments(path):
    """Yield (line_number, text) for fenced-block lines and inline code spans."""
    lines = read_text(path).splitlines()
    in_fence = False
    for number, raw in enumerate(lines, 1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            yield number, raw
        else:
            for span in INLINE_CODE_RE.findall(raw):
                yield number, span


def extract_doc_occurrences(docs):
    occurrences = []
    for path in docs:
        _, sections = load_sections(path)
        for line_number, text in iter_code_fragments(path):
            heading, section_text = section_at(sections, line_number)
            for match in KEY_RE.finditer(text):
                occurrences.append({
                    "key": match.group(1),
                    "value": match.group(2),
                    "file": str(path),
                    "line": line_number,
                    "heading": heading,
                    "section_text": section_text,
                })
    return occurrences


def script_basenames(scripts):
    return {path.name for path in scripts}


def doc_mentions_any(sections, names):
    return any(any(name in text for name in names) for _, _, _, text in sections)


def in_scope(occurrence, names, force_scope):
    if occurrence["key"] in force_scope:
        return True
    return any(name in occurrence["section_text"] for name in names)


def func_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def runtime_key_from_string(text):
    match = RUNTIME_KEY_RE.match(text)
    return match.group(1) if match else None


def extract_runtime_keys(path):
    tree = ast.parse(read_text(path), filename=str(path))
    keys = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = func_name(node.func)
        for argument in node.args[:1]:
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                key = runtime_key_from_string(argument.value)
                if key:
                    keys.add(key)
                elif name in EMIT_FUNCTIONS and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", argument.value):
                    keys.add(argument.value)
            elif isinstance(argument, ast.JoinedStr):
                for part in argument.values:
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        key = runtime_key_from_string(part.value)
                        if key:
                            keys.add(key)
                        break
    return keys


def compact_heading(text, limit=80):
    return " ".join(text.split())[:limit]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Read-only parity check between documented KEY=VALUE tokens and keys emitted by a Skill script.",
    )
    parser.add_argument("--skill", required=True, help="Skill directory to inspect")
    parser.add_argument("--doc", action="append", default=[], help="Documentation file (repeatable; default: SKILL.md and references/*.md)")
    parser.add_argument("--script", action="append", default=[], help="Python script (repeatable; default: scripts/**/*.py)")
    parser.add_argument("--allow-key", action="append", default=[], help="Documented key that is illustrative, not contractual (repeatable)")
    parser.add_argument("--scope-key", action="append", default=[], help="Force a documented key into the contract scope (repeatable)")
    parser.add_argument("--json", action="store_true", help="Emit a single JSON object instead of KEY=VALUE lines")
    args = parser.parse_args(argv)

    skill = Path(args.skill).resolve()
    if not skill.is_dir():
        raise UsageError("skill directory not found: {}".format(skill))

    docs = find_docs(skill, args.doc)
    if not docs:
        raise UsageError("no documentation found under {}".format(skill))
    missing_docs = [path for path in docs if not path.is_file()]
    if missing_docs:
        raise UsageError("documentation not found: {}".format(", ".join(map(str, missing_docs))))

    scripts = find_scripts(skill, args.script)
    if not scripts:
        raise UsageError("no script found under {}".format(skill))
    missing_scripts = [path for path in scripts if not path.is_file()]
    if missing_scripts:
        raise UsageError("script not found: {}".format(", ".join(map(str, missing_scripts))))

    names = script_basenames(scripts)
    docs_with_script_name = []
    for path in docs:
        _, sections = load_sections(path)
        if doc_mentions_any(sections, names):
            docs_with_script_name.append(path)
    scope_fallback_all = not docs_with_script_name
    force_scope = set(args.scope_key)

    occurrences = extract_doc_occurrences(docs)
    doc_keys = {}
    out_of_scope = {}
    for occurrence in occurrences:
        key = occurrence["key"]
        if scope_fallback_all or in_scope(occurrence, names, force_scope):
            doc_keys.setdefault(key, []).append(occurrence)
        else:
            out_of_scope.setdefault(key, []).append(occurrence)

    runtime_keys = set()
    runtime_key_files = {}
    for path in scripts:
        for key in extract_runtime_keys(path):
            runtime_keys.add(key)
            runtime_key_files.setdefault(key, set()).add(path.name)

    allowed = set(args.allow_key)
    contractual = set(doc_keys) - allowed
    doc_only = contractual - runtime_keys
    runtime_only = runtime_keys - contractual
    matched = contractual & runtime_keys

    result = "FAIL" if doc_only else "PASS"

    if args.json:
        payload = {
            "skill": str(skill),
            "docs": [str(path) for path in docs],
            "scripts": [str(path) for path in scripts],
            "scope_fallback_all": scope_fallback_all,
            "doc_keys": sorted(doc_keys),
            "runtime_keys": sorted(runtime_keys),
            "matched": sorted(matched),
            "doc_only": sorted(doc_only),
            "runtime_only": sorted(runtime_only),
            "allowed": sorted(allowed & set(doc_keys)),
            "out_of_scope": sorted(out_of_scope),
            "result": result,
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        emit("SKILL", skill)
        emit("DOCS", len(docs))
        emit("SCRIPTS", len(scripts))
        emit("SCOPE_FALLBACK_ALL", "yes" if scope_fallback_all else "no")
        emit("DOC_KEYS", len(doc_keys))
        emit("RUNTIME_KEYS", len(runtime_keys))
        emit("MATCHED", len(matched))
        emit("DOC_ONLY", len(doc_only))
        emit("RUNTIME_ONLY", len(runtime_only))
        emit("ALLOWED", len(allowed & set(doc_keys)))
        emit("OUT_OF_SCOPE", len(out_of_scope))
        for key in sorted(doc_only):
            first = doc_keys[key][0]
            emit(
                "DOC_ONLY_KEY",
                "{} | occurrences={} | first={}:{} | section={}".format(
                    key,
                    len(doc_keys[key]),
                    first["file"],
                    first["line"],
                    compact_heading(first["heading"]),
                ),
            )
        for key in sorted(runtime_only):
            emit("RUNTIME_ONLY_KEY", "{} | scripts={}".format(key, ",".join(sorted(runtime_key_files.get(key, set())))))
        for key in sorted(allowed & set(doc_keys)):
            emit("ALLOWED_KEY", key)
        for key in sorted(out_of_scope):
            first = out_of_scope[key][0]
            emit("OUT_OF_SCOPE_KEY", "{} | first={}:{}".format(key, first["file"], first["line"]))
        emit("RESULT", result)

    return EXIT_PASS if result == "PASS" else EXIT_FAIL


if __name__ == "__main__":
    configure_stdout()
    try:
        sys.exit(main())
    except UsageError as error:
        emit("ERROR", error)
        sys.exit(EXIT_USAGE)
    except SyntaxError as error:
        emit("ERROR", "python syntax error: {}: {}".format(error.filename, error.msg))
        sys.exit(EXIT_USAGE)
    except OSError as error:
        emit("ERROR", error)
        sys.exit(EXIT_USAGE)
