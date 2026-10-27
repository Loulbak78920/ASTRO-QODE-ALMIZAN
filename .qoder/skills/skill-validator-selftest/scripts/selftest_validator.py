#!/usr/bin/env python3
"""Self-test harness for a Skill static validator; never executes skill code."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

GOOD_DESCRIPTION = '"Use this fixture to exercise the validator: every check must pass."'
GOOD_BODY = """# Fixture

Read `scripts/check.py` for the check.

```python
print("ok")
```

```js
const value = 1;
```
"""

FAIL_LINE = "FAIL"
WARN_LINE = "WARN"
RESULT_PASS = "RESULT PASS"


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


@dataclass
class Case:
    name: str
    skill_dir: Path
    expect_exit: int
    expect_result: str | None
    fragments: tuple[str, ...] = ()
    fail_count: int | None = None
    warn_fragment: str | None = None
    python_flags: tuple[str, ...] = ()
    env_path: Path | None = None
    workspace: Path | None = None
    skip_if_no_node: bool = False
    allow_pyyaml_skip: bool = False


@dataclass
class Result:
    status: str
    detail: str
    output: str = ""
    returncode: int | None = None


def build_skill(
    root: Path,
    dir_name: str,
    *,
    name: str | None = None,
    description: str = GOOD_DESCRIPTION,
    body: str = GOOD_BODY,
    frontmatter: str | None = None,
    with_frontmatter: bool = True,
    bom: bool = False,
    extra_files: dict[str, str] | None = None,
    make_scripts: bool = True,
    raw_bytes: bytes | None = None,
) -> Path:
    skill_dir = root / dir_name
    skill_dir.mkdir(parents=True)
    if raw_bytes is not None:
        (skill_dir / "SKILL.md").write_bytes(raw_bytes)
    else:
        if with_frontmatter:
            if frontmatter is None:
                frontmatter = f"name: {name or dir_name}\ndescription: {description}"
            text = f"---\n{frontmatter}\n---\n{body}"
        else:
            text = body
        data = text.encode("utf-8")
        if bom:
            data = b"\xef\xbb\xbf" + data
        (skill_dir / "SKILL.md").write_bytes(data)
    if make_scripts:
        scripts = skill_dir / "scripts"
        scripts.mkdir(exist_ok=True)
        (scripts / "check.py").write_text('print("ok")\n', encoding="utf-8")
    for rel, content in (extra_files or {}).items():
        path = skill_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return skill_dir


def make_fixtures(root: Path) -> dict[str, Path]:
    fixtures: dict[str, Path] = {}
    fixtures["pos-good"] = build_skill(root, "pos-good")
    fixtures["neg-yaml-colon"] = build_skill(
        root,
        "neg-yaml-colon",
        description="Use this fixture: unquoted colon breaks YAML.",
    )
    fixtures["neg-name-mismatch"] = build_skill(
        root, "neg-name-mismatch", name="fixture-other-name"
    )
    fixtures["neg-invalid-name"] = build_skill(
        root, "neg-invalid-name", name="Bad_Name"
    )
    fixtures["neg-broken-python"] = build_skill(
        root,
        "neg-broken-python",
        body=GOOD_BODY.replace('print("ok")', "def broken(:\n    pass"),
    )
    fixtures["neg-broken-js"] = build_skill(
        root,
        "neg-broken-js",
        body=GOOD_BODY.replace("const value = 1;", "const value = ;"),
    )
    fixtures["neg-missing-ref"] = build_skill(
        root,
        "neg-missing-ref",
        body=GOOD_BODY.replace("scripts/check.py", "scripts/missing.py"),
    )
    fixtures["neg-extra-readme"] = build_skill(
        root, "neg-extra-readme", extra_files={"README.md": "fixture\n"}
    )
    fixtures["neg-real-todo"] = build_skill(
        root,
        "neg-real-todo",
        body=GOOD_BODY + "\n" + "TO" + "DO: replace this fixture text.\n",
    )
    fixtures["neg-multiline-description"] = build_skill(
        root,
        "neg-multiline-description",
        description=(
            ">-\n"
            "  Use this fixture to exercise the validator:\n"
            "  it must remain on one physical line."
        ),
    )
    fixtures["neg-bom"] = build_skill(root, "neg-bom", bom=True)
    fixtures["neg-invalid-utf8"] = build_skill(
        root,
        "neg-invalid-utf8",
        raw_bytes=(
            b"---\n"
            b"name: neg-invalid-utf8\n"
            b"description: \"fixture\"\n"
            b"---\n"
            b"# Fixture\n"
            b"\xff\n"
        ),
        make_scripts=False,
    )
    fixtures["neg-no-frontmatter"] = build_skill(
        root, "neg-no-frontmatter", with_frontmatter=False, body=GOOD_BODY
    )
    fixtures["neg-root-list"] = build_skill(
        root,
        "neg-root-list",
        frontmatter="- name: neg-root-list\n- description: \"root list fixture\"",
    )
    fixtures["neg-unterminated-fence"] = build_skill(
        root,
        "neg-unterminated-fence",
        body="# Fixture\n\n```python\nprint(\"ok\")\n",
    )
    fixtures["warn-unexpected-file"] = build_skill(
        root, "warn-unexpected-file", extra_files={"notes.txt": "fixture\n"}
    )
    fixtures["boundary-description-1024"] = build_skill(
        root,
        "boundary-description-1024",
        description='"' + ("a" * 1024) + '"',
    )
    fixtures["neg-description-1025"] = build_skill(
        root,
        "neg-description-1025",
        description='"' + ("a" * 1025) + '"',
    )
    fixtures["boundary-body-499"] = build_skill(
        root,
        "boundary-body-499",
        body="\n".join(f"line {index}" for index in range(499)) + "\n",
    )
    fixtures["neg-body-500"] = build_skill(
        root,
        "neg-body-500",
        body="\n".join(f"line {index}" for index in range(500)) + "\n",
    )
    fixtures["selfref-todo"] = build_skill(
        root,
        "selfref-todo",
        body=(
            GOOD_BODY
            + "\nThe word TODO appears in prose without a colon and must not be flagged.\n"
        ),
    )
    fixtures["selfref-placeholder"] = build_skill(
        root,
        "selfref-placeholder",
        body=(
            GOOD_BODY
            + "\nRead `<skill-dir>/SKILL.md` and `<validator-script>` before running.\n"
        ),
    )
    fixtures["usage-missing-skill-md"] = root / "usage-missing-skill-md"
    fixtures["usage-missing-skill-md"].mkdir()
    fixtures["usage-missing-dir"] = root / "usage-missing-dir"
    fixtures["usage-missing-workspace"] = root / "usage-missing-workspace"
    (root / "empty-path").mkdir()
    return fixtures


def make_cases(fixtures: dict[str, Path], root: Path, node: str | None) -> list[Case]:
    node_ok = node is not None
    js_fragments: tuple[str, ...] = ("js blocks: 1 checked",) if node_ok else ()
    return [
        Case(
            "pos-good",
            fixtures["pos-good"],
            0,
            "PASS",
            (
                "frontmatter: YAML parsed",
                "local references: 1 checked",
                "python blocks: 1 parsed",
                *js_fragments,
            ),
            fail_count=0,
            warn_fragment=None if node_ok else "not checked (node not found)",
        ),
        Case(
            "neg-yaml-colon",
            fixtures["neg-yaml-colon"],
            1,
            "FAIL",
            ("frontmatter: YAML parse error", "quote the whole description"),
            fail_count=1,
        ),
        Case(
            "neg-name-mismatch",
            fixtures["neg-name-mismatch"],
            1,
            "FAIL",
            ("does not match directory",),
            fail_count=1,
        ),
        Case(
            "neg-invalid-name",
            fixtures["neg-invalid-name"],
            1,
            "FAIL",
            ("not lowercase hyphen-case",),
            fail_count=1,
        ),
        Case(
            "neg-broken-python",
            fixtures["neg-broken-python"],
            1,
            "FAIL",
            ("python block at SKILL.md",),
            fail_count=1,
        ),
        Case(
            "neg-broken-js",
            fixtures["neg-broken-js"],
            1,
            "FAIL",
            ("js block at SKILL.md",),
            fail_count=1,
            skip_if_no_node=True,
        ),
        Case(
            "neg-missing-ref",
            fixtures["neg-missing-ref"],
            1,
            "FAIL",
            ("local reference not found",),
            fail_count=1,
        ),
        Case(
            "neg-extra-readme",
            fixtures["neg-extra-readme"],
            1,
            "FAIL",
            ("extraneous documentation",),
            fail_count=1,
        ),
        Case(
            "neg-real-todo",
            fixtures["neg-real-todo"],
            1,
            "FAIL",
            ("unresolved TODO marker",),
            fail_count=1,
        ),
        Case(
            "neg-multiline-description",
            fixtures["neg-multiline-description"],
            1,
            "FAIL",
            ("description: spans", "single line"),
            fail_count=1,
        ),
        Case(
            "neg-bom",
            fixtures["neg-bom"],
            1,
            "FAIL",
            ("UTF-8 BOM",),
            fail_count=1,
        ),
        Case(
            "neg-invalid-utf8",
            fixtures["neg-invalid-utf8"],
            1,
            "FAIL",
            ("not valid UTF-8",),
            fail_count=1,
        ),
        Case(
            "neg-no-frontmatter",
            fixtures["neg-no-frontmatter"],
            1,
            "FAIL",
            ("must start with a '---' frontmatter line", "cannot read body"),
            fail_count=2,
        ),
        Case(
            "neg-root-list",
            fixtures["neg-root-list"],
            1,
            "FAIL",
            ("YAML root is not a mapping",),
            fail_count=1,
        ),
        Case(
            "neg-unterminated-fence",
            fixtures["neg-unterminated-fence"],
            1,
            "FAIL",
            ("unterminated fence",),
            fail_count=1,
        ),
        Case(
            "warn-unexpected-file",
            fixtures["warn-unexpected-file"],
            0,
            "PASS",
            ("unexpected file",),
            fail_count=0,
            warn_fragment="unexpected file",
        ),
        Case(
            "boundary-description-1024",
            fixtures["boundary-description-1024"],
            0,
            "PASS",
            ("description: single line, 1024 chars",),
            fail_count=0,
        ),
        Case(
            "neg-description-1025",
            fixtures["neg-description-1025"],
            1,
            "FAIL",
            ("exceeds 1024",),
            fail_count=1,
        ),
        Case(
            "boundary-body-499",
            fixtures["boundary-body-499"],
            0,
            "PASS",
            ("body: 499 lines",),
            fail_count=0,
        ),
        Case(
            "neg-body-500",
            fixtures["neg-body-500"],
            1,
            "FAIL",
            ("is not under 500",),
            fail_count=1,
        ),
        Case(
            "selfref-todo",
            fixtures["selfref-todo"],
            0,
            "PASS",
            ("content: no TODO markers",),
            fail_count=0,
        ),
        Case(
            "selfref-placeholder",
            fixtures["selfref-placeholder"],
            0,
            "PASS",
            ("local references: 1 checked",),
            fail_count=0,
        ),
        Case(
            "dep-pyyaml-missing",
            fixtures["pos-good"],
            1,
            "FAIL",
            ("PyYAML is not installed",),
            fail_count=1,
            python_flags=("-S",),
            allow_pyyaml_skip=True,
        ),
        Case(
            "dep-node-missing",
            fixtures["pos-good"],
            0,
            "PASS",
            ("not checked (node not found)",),
            fail_count=0,
            env_path=root / "empty-path",
            warn_fragment="not checked (node not found)",
        ),
        Case(
            "usage-missing-skill-md",
            fixtures["usage-missing-skill-md"],
            2,
            None,
            ("SKILL.md not found",),
        ),
        Case(
            "usage-missing-dir",
            fixtures["usage-missing-dir"],
            2,
            None,
            ("skill directory not found",),
        ),
        Case(
            "usage-missing-workspace",
            fixtures["pos-good"],
            2,
            None,
            ("workspace directory not found",),
            workspace=fixtures["usage-missing-workspace"],
        ),
    ]


def run_validator(
    python: str,
    flags: tuple[str, ...],
    validator: Path,
    skill_dir: Path,
    workspace: Path,
    root: Path,
    env_path: Path | None = None,
) -> tuple[int, str]:
    env = None
    if env_path is not None:
        env = {key: value for key, value in os.environ.items() if key.upper() != "PATH"}
        env["PATH"] = str(env_path)
    command = [
        python,
        *flags,
        str(validator),
        str(skill_dir),
        "--workspace",
        str(workspace),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            env=env,
            cwd=str(root),
        )
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT: validator exceeded 60 seconds"
    except OSError as exc:
        return 126, f"OSError: {ascii_text(exc)}"
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output


def count_prefix(output: str, prefix: str) -> int:
    return sum(1 for line in output.splitlines() if line.startswith(prefix))


def short_output(output: str, limit: int = 20) -> str:
    if not output.strip():
        return "(no output)"
    lines = [ascii_text(line)[:300] for line in output.splitlines()[:limit]]
    return "\n".join(lines)


def run_case(
    case: Case,
    python: str,
    validator: Path,
    root: Path,
    node: str | None,
) -> Result:
    if case.skip_if_no_node and node is None:
        return Result("skip", "node not found")
    workspace = case.workspace or root
    returncode, output = run_validator(
        python,
        case.python_flags,
        validator,
        case.skill_dir,
        workspace,
        root,
        case.env_path,
    )
    if (
        case.allow_pyyaml_skip
        and returncode == 0
        and RESULT_PASS in output
        and "PyYAML is not installed" not in output
    ):
        return Result("skip", "PyYAML missing branch not triggered under -S", output, returncode)
    problems: list[str] = []
    if returncode != case.expect_exit:
        problems.append(f"exit {returncode} != {case.expect_exit}")
    if case.expect_result is not None and f"RESULT {case.expect_result}" not in output:
        problems.append(f"missing 'RESULT {case.expect_result}'")
    for fragment in case.fragments:
        if fragment not in output:
            problems.append(f"missing fragment: {fragment!r}")
    if case.fail_count is not None:
        actual_fails = count_prefix(output, FAIL_LINE)
        if actual_fails != case.fail_count:
            problems.append(f"FAIL lines {actual_fails} != {case.fail_count}")
    if case.warn_fragment is not None and case.warn_fragment not in output:
        problems.append(f"missing WARN fragment: {case.warn_fragment!r}")
    if "Traceback" in output:
        problems.append("output contains Traceback")
    if problems:
        return Result("fail", "; ".join(problems), output, returncode)
    actual_fails = count_prefix(output, FAIL_LINE)
    actual_warns = count_prefix(output, WARN_LINE)
    detail = f"exit={returncode} fails={actual_fails} warns={actual_warns}"
    return Result("pass", detail, output, returncode)


def run_real_positive(
    path: Path,
    python: str,
    validator: Path,
    workspace: Path,
    root: Path,
) -> Result:
    returncode, output = run_validator(
        python, (), validator, path, workspace, root
    )
    problems: list[str] = []
    if returncode != 0:
        problems.append(f"exit {returncode} != 0")
    if RESULT_PASS not in output:
        problems.append("missing 'RESULT PASS'")
    failures = count_prefix(output, FAIL_LINE)
    if failures:
        problems.append(f"{failures} FAIL line(s)")
    if "Traceback" in output:
        problems.append("output contains Traceback")
    if problems:
        return Result("fail", "; ".join(problems), output, returncode)
    warns = count_prefix(output, WARN_LINE)
    return Result("pass", f"exit=0 fails=0 warns={warns}", output, returncode)


def report_case(case_name: str, result: Result) -> None:
    prefix = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[result.status]
    print(f"{prefix}  case={case_name} {ascii_text(result.detail)}")
    if result.status == "fail":
        print("---- output (first 20 lines) ----")
        print(short_output(result.output))
        print("---------------------------------")
    elif result.output:
        for line in result.output.splitlines():
            if line.startswith(WARN_LINE):
                print(f"NOTE  {ascii_text(line)}")


def run_suite(
    validator: Path,
    positive_skills: list[Path],
    workspace: Path,
    python: str,
    node: str | None,
    root: Path,
) -> int:
    fixtures = make_fixtures(root)
    cases = make_cases(fixtures, root, node)
    passed = 0
    failed = 0
    skipped = 0

    baseline = cases[0]
    baseline_result = run_case(baseline, python, validator, root, node)
    report_case(baseline.name, baseline_result)
    if baseline_result.status == "fail":
        if "PyYAML is not installed" in baseline_result.output:
            print("SETUP FAIL  PyYAML is required by the validator; install it before self-testing.")
            return 2
        print("BASELINE FAIL  fix the positive fixture or the validator before trusting negative cases.")
        print("SELFTEST FAIL")
        return 1
    passed += 1

    for path in positive_skills:
        result = run_real_positive(path, python, validator, workspace, root)
        report_case(f"real:{path.name}", result)
        if result.status == "pass":
            passed += 1
        else:
            failed += 1

    for case in cases[1:]:
        result = run_case(case, python, validator, root, node)
        report_case(case.name, result)
        if result.status == "pass":
            passed += 1
        elif result.status == "skip":
            skipped += 1
        else:
            failed += 1

    print(f"SUMMARY: passed={passed} failed={failed} skipped={skipped}")
    if failed:
        print("SELFTEST FAIL")
        return 1
    if skipped:
        print("SELFTEST PASS (some branches skipped and unverified)")
    else:
        print("SELFTEST PASS")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Self-test a Skill static validator with synthetic fixtures."
    )
    parser.add_argument("--validator", required=True, type=Path, help="validator script to test")
    parser.add_argument(
        "--positive-skill",
        action="append",
        default=[],
        type=Path,
        dest="positive_skills",
        help="known-good skill directory; repeatable",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="root for resolving references in real skill packages (default: cwd)",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter used to run the validator (default: current interpreter)",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="keep temporary fixtures for debugging",
    )
    args = parser.parse_args(argv)

    validator = args.validator.expanduser().resolve()
    workspace = args.workspace.expanduser().resolve()
    if not validator.is_file():
        print(f"SETUP FAIL  validator not found: {ascii_text(validator)}")
        return 2
    if not workspace.is_dir():
        print(f"SETUP FAIL  workspace not found: {ascii_text(workspace)}")
        return 2
    positive_skills: list[Path] = []
    for path in args.positive_skills:
        resolved = path.expanduser().resolve()
        if not resolved.is_dir() or not (resolved / "SKILL.md").is_file():
            print(f"SETUP FAIL  positive skill not found: {ascii_text(resolved)}")
            return 2
        positive_skills.append(resolved)
    python = args.python
    if not Path(python).is_file():
        found = shutil.which(python)
        if found is None:
            print(f"SETUP FAIL  Python interpreter not found: {ascii_text(python)}")
            return 2
        python = found
    node = shutil.which("node")
    print(f"SELFTEST validator={ascii_text(validator)}")
    print(f"Python: {ascii_text(python)}")
    print(f"Node: {ascii_text(node) if node else 'not found'}")
    root = Path(tempfile.mkdtemp(prefix="skill-validator-selftest-"))
    try:
        return run_suite(validator, positive_skills, workspace, python, node, root)
    finally:
        if args.keep:
            print(f"TEMP KEPT: {ascii_text(root)}")
        else:
            shutil.rmtree(root, ignore_errors=True)
            if root.exists():
                print(f"WARN  temp cleanup incomplete: {ascii_text(root)}")
            else:
                print("TEMP REMOVED")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("SELFTEST FAIL  interrupted")
        raise SystemExit(2)
    except Exception as exc:
        print(f"SETUP FAIL  harness error: {ascii_text(exc)}")
        raise SystemExit(2)
