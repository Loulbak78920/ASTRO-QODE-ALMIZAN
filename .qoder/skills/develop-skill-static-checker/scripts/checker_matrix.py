#!/usr/bin/env python3
"""Fixture matrix for read-only Python static checkers bundled with a Skill."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

CHECKER_TIMEOUT = 60
CACHE_SUFFIXES = {".pyc", ".pyo"}
ALL_SUMMARY = {"scripts": 8, "pass": 3, "fail": 3, "warn": 2}

GOOD_UTF8 = """\
import sys


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


configure_stdout()
print("中文输出 OK")
"""

GOOD_ASCII = """\
import json

print("中文".encode("ascii", "backslashreplace").decode("ascii"))
print(json.dumps({"message": "中文"}, ensure_ascii=True))
"""

GOOD_HELPER = """\
def ascii_text(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


print(ascii_text("中文"))
"""

BAD_PRINT = """\
print("中文")
"""

BAD_JSON = """\
import json

print(json.dumps({"message": "中文"}, ensure_ascii=False))
"""

BAD_SYNTAX = """\
def broken(:
    pass
"""

WARN_COMPILE = """\
import py_compile

py_compile.compile("x.py")
"""

WARN_JSON = """\
import json

payload = json.dumps({"message": "中文"}, ensure_ascii=False)
print(payload)
"""

EDGE_BAD_FSTRING = """\
print(f"中文{1}")
"""

EDGE_BAD_WRITE = """\
import sys

sys.stdout.write("中文")
"""

EDGE_BAD_END = """\
print("中文", end="")
"""

EDGE_GOOD_JSON_UTF8 = """\
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print(json.dumps({"message": "中文"}, ensure_ascii=False))
"""

EDGE_GOOD_JSON_HELPER = """\
import json


def ascii_text(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def emit(payload):
    print(ascii_text(json.dumps(payload, ensure_ascii=False)))


emit({"message": "中文"})
"""

EDGE_GOOD_FILE_SINK = """\
import json
from pathlib import Path

Path("out.json").write_text(
    json.dumps({"message": "中文"}, ensure_ascii=False),
    encoding="utf-8",
)
"""


def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def safe(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


class HarnessError(Exception):
    pass


def manifest(root):
    if not root.exists():
        return {}
    result = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        data = path.read_bytes()
        result[relative] = [len(data), hashlib.sha256(data).hexdigest()]
    return result


def cache_paths(root):
    if not root.exists():
        return set()
    found = set()
    for path in root.rglob("*"):
        if path.name == "__pycache__" or path.suffix.lower() in CACHE_SUFFIXES:
            found.add(path.relative_to(root).as_posix())
    return found


def write_fixture(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8", newline="\n")


@dataclass
class Case:
    name: str
    files: dict = field(default_factory=dict)
    dirs: tuple = ()
    build: bool = True
    no_fixture: bool = False
    expected_rc: int = 0
    extra_args: tuple = ()
    required: tuple = ()
    forbidden: tuple = ("Traceback",)
    required_counts: dict = field(default_factory=dict)
    json_payload: bool = False


def all_files():
    return {
        "scripts/good_utf8.py": GOOD_UTF8,
        "scripts/good_ascii.py": GOOD_ASCII,
        "scripts/good_helper.py": GOOD_HELPER,
        "scripts/bad_print.py": BAD_PRINT,
        "scripts/bad_json.py": BAD_JSON,
        "scripts/bad_syntax.py": BAD_SYNTAX,
        "scripts/warn_compile.py": WARN_COMPILE,
        "scripts/warn_json.py": WARN_JSON,
    }


def case_list():
    return [
        Case(
            name="pass_only",
            files={
                "scripts/good_utf8.py": GOOD_UTF8,
                "scripts/good_ascii.py": GOOD_ASCII,
                "scripts/good_helper.py": GOOD_HELPER,
            },
            required=("SUMMARY scripts=3 pass=3 fail=0 warn=0", "RESULT PASS"),
            forbidden=("FAIL ", "Traceback"),
        ),
        Case(
            name="all",
            files=all_files(),
            expected_rc=1,
            required=(
                "FAIL non-ascii-output",
                "FAIL json-ensure-ascii-false",
                "FAIL syntax-error",
                "SUMMARY scripts=8 pass=3 fail=3 warn=2",
                "RESULT FAIL",
            ),
        ),
        Case(
            name="warn_only",
            files={
                "scripts/warn_compile.py": WARN_COMPILE,
                "scripts/warn_json.py": WARN_JSON,
            },
            required=(
                "WARN cache-risk",
                "WARN json-ensure-ascii-false",
                "SUMMARY scripts=2 pass=0 fail=0 warn=2",
                "RESULT PASS",
            ),
            forbidden=("FAIL ", "Traceback"),
        ),
        Case(
            name="edge_bad",
            files={
                "scripts/bad_fstring.py": EDGE_BAD_FSTRING,
                "scripts/bad_write.py": EDGE_BAD_WRITE,
                "scripts/bad_end.py": EDGE_BAD_END,
            },
            expected_rc=1,
            required=(
                "SUMMARY scripts=3 pass=0 fail=3 warn=0",
                "RESULT FAIL",
            ),
            required_counts={"FAIL non-ascii-output": 3},
        ),
        Case(
            name="edge_good",
            files={
                "scripts/good_json_utf8.py": EDGE_GOOD_JSON_UTF8,
                "scripts/good_json_helper.py": EDGE_GOOD_JSON_HELPER,
                "scripts/good_file_sink.py": EDGE_GOOD_FILE_SINK,
            },
            required=(
                "WARN json-ensure-ascii-false",
                "SUMMARY scripts=3 pass=2 fail=0 warn=1",
                "RESULT PASS",
            ),
            forbidden=("FAIL ", "Traceback"),
        ),
        Case(
            name="cache",
            files={
                "scripts/ok.py": "print(\"ok\")\n",
                "scripts/__pycache__/dummy.pyc": b"\x00",
            },
            required=(
                "WARN cache-present 1 file(s)",
                "SUMMARY scripts=1 pass=1 fail=0 warn=1",
                "RESULT PASS",
            ),
            forbidden=("FAIL ", "Traceback"),
        ),
        Case(
            name="empty",
            dirs=("scripts",),
            required=("SUMMARY scripts=0 pass=0 fail=0 warn=0", "RESULT PASS"),
            forbidden=("FAIL ", "Traceback"),
        ),
        Case(
            name="no_scripts",
            expected_rc=2,
            required=("ERROR: scripts directory not found",),
        ),
        Case(
            name="missing",
            build=False,
            expected_rc=2,
            required=("ERROR: skill directory not found",),
        ),
        Case(
            name="bad_encoding",
            files={"scripts/bad_encoding.py": b"print(\"\xff\")\n"},
            expected_rc=1,
            required=("FAIL invalid-utf8", "RESULT FAIL"),
        ),
        Case(
            name="json_contract",
            files=all_files(),
            expected_rc=1,
            extra_args=("--json",),
            json_payload=True,
        ),
        Case(
            name="help",
            build=False,
            no_fixture=True,
            extra_args=("--help",),
            required=("usage:",),
        ),
    ]


def build_case(root, case):
    case_dir = root / case.name
    if not case.build:
        return case_dir
    case_dir.mkdir(parents=True, exist_ok=True)
    for relative in case.dirs:
        (case_dir / relative).mkdir(parents=True, exist_ok=True)
    for relative, data in case.files.items():
        write_fixture(case_dir / relative, data)
    return case_dir


def run_checker(checker, case, root):
    command = [sys.executable, str(checker)]
    if case.no_fixture:
        command.extend(case.extra_args)
    else:
        command.append(str(root / case.name))
        command.extend(case.extra_args)
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(
            command,
            cwd=str(checker.parent),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CHECKER_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return None, "", "TIMEOUT after %d seconds" % CHECKER_TIMEOUT
    except OSError as exc:
        raise HarnessError("cannot run checker: %s" % safe(exc))
    return (
        completed.returncode,
        completed.stdout.decode("utf-8", "replace"),
        completed.stderr.decode("utf-8", "replace"),
    )


def inspect_case(case, rc, out, err):
    problems = []
    if rc is None:
        return ["timeout"]
    combined = out + err
    if rc != case.expected_rc:
        problems.append("rc=%s want=%s" % (rc, case.expected_rc))
    for token in case.required:
        if token not in combined:
            problems.append("missing token: %s" % token)
    for token in case.forbidden:
        if token in combined:
            problems.append("unexpected token: %s" % token)
    for token, expected in case.required_counts.items():
        actual = combined.count(token)
        if actual != expected:
            problems.append("count %s=%d want=%d" % (token, actual, expected))
    if case.json_payload:
        if any(ord(char) > 127 for char in out):
            problems.append("json output is not ASCII")
        try:
            payload = json.loads(out)
        except json.JSONDecodeError as exc:
            problems.append("json parse: %s" % safe(exc))
        else:
            if payload.get("result") != "FAIL":
                problems.append("json result=%r" % payload.get("result"))
            if payload.get("summary") != ALL_SUMMARY:
                problems.append("json summary=%r" % payload.get("summary"))
            if payload.get("caches") != []:
                problems.append("json caches=%r" % payload.get("caches"))
    return problems


def emit_case(case, rc, problems, quiet):
    if quiet:
        return
    if problems:
        print("CASE %s FAIL rc=%s want=%s" % (case.name, rc, case.expected_rc))
        for problem in problems:
            print("  %s" % safe(problem))
    else:
        print("CASE %s PASS rc=%s" % (case.name, rc))


def run_real_skills(checker, real_skills, quiet):
    failures = []
    for skill in real_skills:
        scripts_dir = skill / "scripts"
        if not skill.is_dir():
            raise HarnessError("real skill directory not found: %s" % safe(skill))
        if not scripts_dir.is_dir():
            raise HarnessError("real skill has no scripts directory: %s" % safe(skill))
        before = manifest(scripts_dir)
        caches_before = cache_paths(skill)
        command = [sys.executable, str(checker), str(skill)]
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        try:
            completed = subprocess.run(
                command,
                cwd=str(checker.parent),
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=CHECKER_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            failures.append("REAL %s timeout" % safe(skill))
            if not quiet:
                print("REAL %s FAIL timeout" % safe(skill))
            continue
        except OSError as exc:
            raise HarnessError("cannot run checker: %s" % safe(exc))
        out = completed.stdout.decode("utf-8", "replace")
        err = completed.stderr.decode("utf-8", "replace")
        combined = out + err
        problems = []
        if completed.returncode not in (0, 1):
            problems.append("rc=%s want 0 or 1" % completed.returncode)
        if "Traceback" in combined:
            problems.append("Traceback")
        if "RESULT " not in out:
            problems.append("missing RESULT")
        if manifest(scripts_dir) != before:
            problems.append("scripts modified")
        new_caches = cache_paths(skill) - caches_before
        if new_caches:
            problems.append("new cache: %s" % ", ".join(sorted(new_caches)))
        result = "UNKNOWN"
        summary = "none"
        warn_lines = 0
        for line in out.splitlines():
            if line.startswith("RESULT "):
                result = line[len("RESULT "):].strip()
            elif line.startswith("SUMMARY "):
                summary = line[len("SUMMARY "):].strip()
            elif line.startswith("  WARN ") or line.startswith("WARN cache-present"):
                warn_lines += 1
        if not quiet:
            print(
                "REAL %s rc=%s result=%s summary=%s warn_lines=%d"
                % (safe(skill), completed.returncode, result, summary, warn_lines)
            )
            if warn_lines:
                for line in out.splitlines():
                    if line.startswith("  WARN ") or line.startswith("WARN cache-present"):
                        print("REAL   %s" % safe(line.strip()))
            else:
                print("REAL   WARN none")
            for problem in problems:
                print("REAL   %s" % safe(problem))
        if problems:
            failures.append("REAL %s: %s" % (safe(skill), "; ".join(problems)))
    return failures


def execute_matrix(checker, real_skills, root, quiet):
    failures = []
    cases = case_list()
    side_effect_failures = 0
    for case in cases:
        case_dir = build_case(root, case)
        before = manifest(case_dir) if case.build else {}
        caches_before = cache_paths(checker.parent)
        rc, out, err = run_checker(checker, case, root)
        problems = inspect_case(case, rc, out, err)
        if case.build and manifest(case_dir) != before:
            problems.append("fixture modified")
            side_effect_failures += 1
        new_caches = cache_paths(checker.parent) - caches_before
        if new_caches:
            problems.append("new cache: %s" % ", ".join(sorted(new_caches)))
            side_effect_failures += 1
        emit_case(case, rc, problems, quiet)
        if problems:
            failures.append("%s: %s" % (case.name, "; ".join(problems)))
    failures.extend(run_real_skills(checker, real_skills, quiet))
    if not quiet:
        print("SIDE_EFFECTS %s" % ("PASS" if side_effect_failures == 0 else "FAIL"))
        print(
            "SUMMARY cases=%d failures=%d real=%d"
            % (len(cases), len(failures), len(real_skills))
        )
        print("RESULT %s" % ("PASS" if not failures else "FAIL"))
    return failures, len(cases)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run a fixture matrix against a read-only Python static checker."
    )
    parser.add_argument("--checker", help="path to the checker script")
    parser.add_argument(
        "--real-skill",
        action="append",
        default=[],
        help="real Skill directory to scan; repeatable",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="run the matrix against a stub checker that always passes",
    )
    parser.add_argument("--keep", action="store_true", help="keep the temporary fixture root")
    return parser.parse_args(argv)


def main(argv=None):
    configure_stdout()
    args = parse_args(argv)
    root = Path(tempfile.mkdtemp(prefix="static-checker-matrix-"))
    exit_code = 0
    try:
        if args.selftest:
            stub_dir = root / "stub"
            stub_dir.mkdir(parents=True, exist_ok=True)
            stub = stub_dir / "stub_checker.py"
            stub.write_text(
                'print("RESULT PASS")\nraise SystemExit(0)\n', encoding="utf-8"
            )
            failures, case_count = execute_matrix(stub, [], root, quiet=True)
            if failures:
                print(
                    "SELFTEST PASS cases=%d caught=%d"
                    % (case_count, len(failures))
                )
            else:
                print("SELFTEST FAIL cases=%d caught=0" % case_count)
                exit_code = 1
        else:
            if not args.checker:
                raise HarnessError("--checker is required unless --selftest is used")
            checker = Path(args.checker)
            if not checker.is_file():
                raise HarnessError("checker not found: %s" % safe(checker))
            real_skills = [Path(item) for item in args.real_skill]
            failures, _ = execute_matrix(checker, real_skills, root, quiet=False)
            exit_code = 1 if failures else 0
    except HarnessError as exc:
        print("ERROR %s" % safe(exc), file=sys.stderr)
        exit_code = 2
    except Exception as exc:  # noqa: BLE001 - report without a traceback
        print("ERROR %s: %s" % (type(exc).__name__, safe(exc)), file=sys.stderr)
        exit_code = 2
    finally:
        if args.keep:
            print("KEPT %s" % safe(root))
        else:
            try:
                shutil.rmtree(root)
                print("CLEANUP OK")
            except OSError as exc:
                print("CLEANUP FAIL %s" % safe(exc), file=sys.stderr)
                if exit_code == 0:
                    exit_code = 2
    print("EXIT=%d" % exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
