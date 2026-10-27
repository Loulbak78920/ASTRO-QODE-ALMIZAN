#!/usr/bin/env python3
"""Read-only scan of production write operations in a Skill or runbook.

Command rules (R1-R6) run only inside fenced code blocks, so prose warnings
such as "never run chown -R" do not trigger. Document rules (R7-R9) run on
the whole text. This scan is a first-pass trigger, not a safety proof.

Exit codes: 0 = CLEAN or WARN only, 1 = CRITICAL findings, 2 = usage/IO error.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", "node_modules", "assets", "scripts"}
MAX_FINDINGS = 40
SNIPPET = 140

COMMAND_RULES = [
    ("R1", "CRITICAL", "recursive ownership or permission change",
     re.compile(r"\b(?:chown|chmod)\b[^\n]*?(?:\s-[A-Za-z]*R[A-Za-z]*(?=\s|$)|--recursive)")),
    ("R2", "CRITICAL", "recursive or forced delete",
     re.compile(r"\brm\s+-[A-Za-z]*[rf][A-Za-z]*\s")),
    ("R3", "CRITICAL", "password piped to sudo -S",
     re.compile(r"\bsudo\s+-S\b")),
    ("R4", "CRITICAL", "password passed as a command-line argument",
     re.compile(r"--mot-de-passe(?!-stdin)|--password(?!-stdin)")),
    ("R5", "CRITICAL", "secret variable printed",
     re.compile(r"\b(?:echo|printf|print)\b[^\n]*\$(?:MDP|MOT_DE_PASSE|PASSWORD)\b", re.I)),
    ("R6", "WARN", "shell tracing may leak a secret",
     re.compile(r"\bset\s+-x\b|\bssh\s+-v\b")),
]

SECRET_WRITE = re.compile(
    r"(?:écrire|ecrire|write|写入|open\s*\([^)\n]*['\"]w|json\.dump)[^\n]{0,120}secrets"
    r"|secrets[^\n]{0,120}\.json[^\n]{0,120}(?:écrire|ecrire|write|写入|open)",
    re.I,
)
GUARD = re.compile(
    r"ne jamais [ée]craser|ne pas [ée]craser|do not overwrite|"
    r"不覆盖|不重写|ne jamais r[ée]utiliser",
    re.I,
)
REVOKE = re.compile(r"r[ée]voqu|revok|吊销|已注销", re.I)
HEADING = re.compile(r"^#{2,4}\s")


def setup_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def fail(message: str) -> None:
    print("ERROR: " + message, file=sys.stderr)
    print("RESULT FAIL", file=sys.stderr)
    raise SystemExit(2)


def collect(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.is_dir():
        fail("path not found: " + str(target))
    files: list[Path] = []
    skill = target / "SKILL.md"
    if skill.is_file():
        files.append(skill)
    refs = target / "references"
    if refs.is_dir():
        files.extend(sorted(refs.rglob("*.md")))
    if not files:
        fail("no SKILL.md or references/*.md under: " + str(target))
    return files


def scan_file(path: Path) -> list[tuple[Path, int, str, str, str, str]]:
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError as exc:
        fail("cannot read " + str(path) + ": " + str(exc))

    findings = []
    in_fence = False
    for number, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            continue
        for rule_id, severity, message, pattern in COMMAND_RULES:
            if pattern.search(line):
                findings.append((path, number, rule_id, severity, message, line.strip()))

    text = "\n".join(lines)

    writes = [n for n, line in enumerate(lines, 1) if SECRET_WRITE.search(line)]
    acls = [n for n, line in enumerate(lines, 1) if re.search(r"\bicacls\b", line, re.I)]

    if writes and not GUARD.search(text):
        number = writes[0]
        findings.append((path, number, "R7", "CRITICAL",
                         "secret write without an overwrite guard", lines[number - 1].strip()))

    if writes and acls and acls[0] > writes[0]:
        between = lines[writes[0]:acls[0] - 1]
        if any(HEADING.match(item) for item in between):
            number = acls[0]
            findings.append((path, number, "R8", "WARN",
                             "ACL tightened in a later section than the secret write",
                             lines[number - 1].strip()))

    if REVOKE.search(text) and "401" not in text:
        number = next(n for n, line in enumerate(lines, 1) if REVOKE.search(line))
        findings.append((path, number, "R9", "WARN",
                         "revocation claimed without 401 evidence", lines[number - 1].strip()))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only scan of production write risks in SKILL.md and references/*.md.")
    parser.add_argument("path", help="Skill directory or Markdown file")
    args = parser.parse_args()

    setup_streams()
    files = collect(Path(args.path).expanduser())
    findings = []
    for path in files:
        findings.extend(scan_file(path))

    critical = sum(1 for item in findings if item[3] == "CRITICAL")
    warn = sum(1 for item in findings if item[3] == "WARN")

    print(f"SCAN {len(files)} file(s)")
    for path, number, rule, severity, message, snippet in findings[:MAX_FINDINGS]:
        print(f"{path}:{number}: {rule} {severity} {message} | {snippet[:SNIPPET]}")
    if len(findings) > MAX_FINDINGS:
        print(f"... {len(findings) - MAX_FINDINGS} finding(s) omitted")

    print(f"SCAN SUMMARY {len(files)} file(s) | CRITICAL {critical} | WARN {warn}")
    print("RESULT CRITICAL" if critical else ("RESULT WARN" if warn else "RESULT CLEAN"))
    return 1 if critical else 0


if __name__ == "__main__":
    raise SystemExit(main())
