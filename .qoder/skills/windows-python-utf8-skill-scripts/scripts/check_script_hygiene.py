#!/usr/bin/env python3
"""Read-only static hygiene checks for bundled Python scripts in a Skill."""

import argparse
import ast
import json
import sys
from pathlib import Path

UTF8_VALUES = {"utf-8", "utf8"}
OUTPUT_WRITE_NAMES = {"sys.stdout.write", "sys.stdout.writelines", "sys.stderr.write"}
CACHE_SUFFIXES = {".pyc", ".pyo"}


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def call_name(node):
    if isinstance(node, ast.Call):
        node = node.func
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def method_name(node):
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def const_text(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def has_non_ascii(text):
    return any(ord(char) > 127 for char in text)


def string_literals(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.JoinedStr):
        return [
            value.value
            for value in node.values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        ]
    return []


def direct_strings(call):
    values = []
    for arg in call.args:
        values.extend(string_literals(arg))
    for keyword in call.keywords:
        if keyword.arg not in {"file", "flush"}:
            values.extend(string_literals(keyword.value))
    return values


def keyword_node(call, name):
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def has_ascii_encode(node):
    for child in ast.walk(node):
        if not isinstance(child, ast.Call) or method_name(child) != "encode":
            continue
        args = [const_text(arg) for arg in child.args]
        if "ascii" in args and "backslashreplace" in args:
            return True
    return False


def ascii_helpers(tree):
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and has_ascii_encode(node)
    }


def calls_ascii_helper(node, helpers):
    for child in ast.walk(node):
        if isinstance(child, ast.Call) and call_name(child) in helpers:
            return True
        if isinstance(child, ast.Call) and has_ascii_encode(child):
            return True
    return False


def parent_map(tree):
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def is_output_call(node):
    name = call_name(node)
    if name == "print":
        file_node = keyword_node(node, "file")
        if file_node is None:
            return True
        return isinstance(file_node, ast.Constant) and file_node.value is None
    return name in OUTPUT_WRITE_NAMES


def output_calls(tree):
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and is_output_call(node)
    ]


def output_ancestor(node, parents):
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.Call) and is_output_call(current):
            return current
    return None


def stdout_utf8(tree):
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if call_name(node) != "sys.stdout.reconfigure":
            continue
        encoding = const_text(keyword_node(node, "encoding"))
        if encoding and encoding.lower() in UTF8_VALUES:
            return True
    return False


def has_cache_risk(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
            if "py_compile" in names or "compileall" in names:
                return True
        if isinstance(node, ast.ImportFrom):
            module = (node.module or "").split(".")[0]
            if module in {"py_compile", "compileall"}:
                return True
        if isinstance(node, ast.Call):
            name = call_name(node)
            if name in {
                "py_compile.compile",
                "compileall.compile_dir",
                "compileall.compile_file",
            }:
                return True
    return False


class Finding:
    def __init__(self, level, code, line, message):
        self.level = level
        self.code = code
        self.line = line
        self.message = message

    def as_dict(self):
        return {
            "level": self.level,
            "code": self.code,
            "line": self.line,
            "message": self.message,
        }


def check_file(path, root):
    relative = path.relative_to(root).as_posix()
    try:
        data = path.read_bytes()
    except OSError as exc:
        return relative, [Finding("FAIL", "read-error", 1, "cannot read file: %s" % exc)], "FAIL"
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return (
            relative,
            [Finding("FAIL", "invalid-utf8", 1, "not valid UTF-8: %s" % exc.reason)],
            "FAIL",
        )
    try:
        tree = ast.parse(text, filename=relative)
    except SyntaxError as exc:
        return relative, [Finding("FAIL", "syntax-error", exc.lineno or 1, exc.msg)], "FAIL"

    findings = []
    protected = stdout_utf8(tree)
    helpers = ascii_helpers(tree)
    parents = parent_map(tree)

    for call in output_calls(tree):
        call_protected = protected or calls_ascii_helper(call, helpers)
        if not call_protected and any(
            has_non_ascii(value) for value in direct_strings(call)
        ):
            findings.append(
                Finding(
                    "FAIL",
                    "non-ascii-output",
                    call.lineno,
                    "non-ASCII string in a stdout/stderr call without UTF-8 stdout or ASCII escaping",
                )
            )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node) != "json.dumps":
            continue
        ensure = keyword_node(node, "ensure_ascii")
        if not (isinstance(ensure, ast.Constant) and ensure.value is False):
            continue
        ancestor = output_ancestor(node, parents)
        if ancestor is not None:
            if not (protected or calls_ascii_helper(ancestor, helpers)):
                findings.append(
                    Finding(
                        "FAIL",
                        "json-ensure-ascii-false",
                        node.lineno,
                        "json.dumps(ensure_ascii=False) reaches stdout without UTF-8 stdout or ASCII escaping",
                    )
                )
        else:
            findings.append(
                Finding(
                    "WARN",
                    "json-ensure-ascii-false",
                    node.lineno,
                    "ensure_ascii=False outside a detected stdout call; verify the sink encoding",
                )
            )

    if has_cache_risk(tree):
        findings.append(
            Finding(
                "WARN",
                "cache-risk",
                1,
                "py_compile or compileall can create __pycache__; use ast.parse or redirect PYTHONPYCACHEPREFIX",
            )
        )

    status = "PASS"
    if any(item.level == "FAIL" for item in findings):
        status = "FAIL"
    elif any(item.level == "WARN" for item in findings):
        status = "WARN"
    return relative, findings, status


def cache_files(skill_dir):
    found = []
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix.lower() in CACHE_SUFFIXES:
            found.append(path.relative_to(skill_dir).as_posix())
    return sorted(found)


def main():
    configure_stdout()
    parser = argparse.ArgumentParser(
        description="Read-only static hygiene checks for bundled Python scripts in a Skill."
    )
    parser.add_argument("skill_dir", help="Skill directory containing scripts/")
    parser.add_argument("--json", action="store_true", help="emit machine-readable ASCII JSON")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    if not skill_dir.is_dir():
        print("ERROR: skill directory not found: %s" % args.skill_dir, file=sys.stderr)
        return 2
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        print("ERROR: scripts directory not found: %s" % scripts_dir, file=sys.stderr)
        return 2

    files = sorted(path for path in scripts_dir.rglob("*.py") if path.is_file())
    results = []
    for path in files:
        relative, findings, status = check_file(path, skill_dir)
        results.append({"path": relative, "status": status, "findings": findings})

    caches = cache_files(skill_dir)
    fail_count = sum(1 for item in results if item["status"] == "FAIL")
    warn_count = sum(1 for item in results if item["status"] == "WARN")
    pass_count = len(results) - fail_count - warn_count
    warning_count = warn_count + (1 if caches else 0)
    result = "FAIL" if fail_count else "PASS"
    resolved_skill = skill_dir.resolve().as_posix()

    if args.json:
        payload = {
            "skill": resolved_skill,
            "scripts": [
                {
                    "path": item["path"],
                    "status": item["status"],
                    "findings": [finding.as_dict() for finding in item["findings"]],
                }
                for item in results
            ],
            "caches": caches,
            "summary": {
                "scripts": len(results),
                "pass": pass_count,
                "fail": fail_count,
                "warn": warning_count,
            },
            "result": result,
        }
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 1 if fail_count else 0

    print("SKILL %s" % resolved_skill)
    for item in results:
        print("FILE %s" % item["path"])
        if not item["findings"]:
            print("  PASS no known output or cache risk")
        for finding in item["findings"]:
            print(
                "  %s %s L%d %s"
                % (finding.level, finding.code, finding.line, finding.message)
            )
    if caches:
        print(
            "WARN cache-present %d file(s): %s"
            % (len(caches), ", ".join(caches[:5]))
        )
    print(
        "SUMMARY scripts=%d pass=%d fail=%d warn=%d"
        % (len(results), pass_count, fail_count, warning_count)
    )
    print("RESULT %s" % result)
    return 1 if fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
