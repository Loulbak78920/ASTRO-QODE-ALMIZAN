#!/usr/bin/env python3
"""Read-only Git inventory: repositories, branches, worktrees, remotes. Never stages or commits."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache", ".pytest_cache"}
MAX_LINE_COUNT = 40
MAX_REPOS = 50


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def git(path: Path, *args: str, optional_locks: bool = False) -> tuple[int, str]:
    cmd = ["git", "-C", str(path)]
    if optional_locks:
        cmd.append("--no-optional-locks")
    cmd.extend(args)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 128, ascii_text(exc)
    output = "\n".join(part for part in (proc.stdout, proc.stderr) if part and part.strip())
    return proc.returncode, output.strip()


def print_block(label: str, text: str, code: int) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()] if text else []
    if code != 0:
        print(f"{label}: ERROR exit {code}")
        for line in lines[:MAX_LINE_COUNT]:
            print(f"  {ascii_text(line)}")
        return lines
    print(f"{label}: {len(lines)} line(s)")
    for line in lines[:MAX_LINE_COUNT]:
        print(f"  {ascii_text(line)}")
    if len(lines) > MAX_LINE_COUNT:
        print(f"  ... ({len(lines) - MAX_LINE_COUNT} more)")
    return lines


def find_repos(root: Path, max_depth: int) -> list[Path]:
    found: list[Path] = []
    root = root.resolve()
    for current, dirs, files in os.walk(root):
        here = Path(current)
        relative = here.relative_to(root)
        depth = len(relative.parts)
        if ".git" in dirs or ".git" in files:
            found.append(here)
            if len(found) >= MAX_REPOS:
                return found
        if depth >= max_depth:
            dirs[:] = []
        else:
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
    return found


def repo_state(repo: Path) -> None:
    print(f"== REPO {ascii_text(repo)}")
    code, branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    print(f"BRANCH: {ascii_text(branch) if code == 0 else 'UNKNOWN'}")
    code, upstream = git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if code == 0 and upstream:
        print(f"UPSTREAM: {ascii_text(upstream)}")
        code, counts = git(repo, "rev-list", "--left-right", "--count", "@{u}...HEAD")
        if code == 0 and len(counts.split()) == 2:
            behind, ahead = counts.split()
            print(f"AHEAD: {ahead} BEHIND: {behind}")
    else:
        print("UPSTREAM: none")
    code, head = git(repo, "log", "-1", "--format=%h %s")
    print(f"HEAD: {ascii_text(head) if code == 0 and head else 'none'}")
    code, status = git(
        repo, "status", "--porcelain=v1", "--untracked-files=normal", optional_locks=True
    )
    status_lines = print_block("STATUS", status, code)
    code, staged = git(repo, "diff", "--cached", "--stat")
    print_block("STAGED", staged, code)
    code, unstaged = git(repo, "diff", "--stat")
    print_block("DIFF", unstaged, code)
    code, remotes = git(repo, "remote", "-v")
    remote_lines = print_block("REMOTES", remotes, code)
    if not remote_lines and code == 0:
        print("REMOTE: none")
    for line in status_lines:
        if line.startswith("??") and ("__pycache__" in line or line.rstrip().endswith(".pyc")):
            print(f"NOTE untracked cache: {ascii_text(line[3:].strip())}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Git repository inventory.")
    parser.add_argument("paths", nargs="+", help="directories to inspect (absolute paths recommended)")
    parser.add_argument("--max-depth", type=int, default=3, help="scan depth for nested repositories (default: 3)")
    parser.add_argument("--strict", action="store_true", help="exit 1 when no repository is found")
    args = parser.parse_args(argv)

    configure_stdout()
    if args.max_depth < 1:
        print("FAIL usage: --max-depth must be >= 1")
        print("RESULT FAIL")
        return 2
    if shutil.which("git") is None:
        print("FAIL environment: git not found in PATH")
        print("RESULT FAIL")
        return 2

    env_error = False
    seen: set[Path] = set()
    ordered: list[Path] = []
    for raw in args.paths:
        path = Path(raw).expanduser()
        print(f"== INPUT {ascii_text(path)}")
        if not path.is_dir():
            print("FAIL environment: directory not found")
            env_error = True
            continue
        path = path.resolve()
        code, top = git(path, "rev-parse", "--show-toplevel")
        if code == 0 and top:
            print(f"ROOT: {ascii_text(top)}")
            candidates = [Path(top)]
        else:
            print(f"ROOT: not a repository (exit {code})")
            candidates = find_repos(path, args.max_depth)
            print(f"CANDIDATES: {len(candidates)}")
            if len(candidates) >= MAX_REPOS:
                print(f"NOTE candidate list truncated at {MAX_REPOS}")
            for candidate in candidates:
                print(f"  {ascii_text(candidate)}")
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                ordered.append(resolved)

    for repo in ordered:
        print("")
        repo_state(repo)

    print("")
    print(f"REPOS: {len(ordered)}")
    if env_error:
        print("RESULT FAIL")
        return 2
    if args.strict and not ordered:
        print("FAIL: no repository found")
        print("RESULT FAIL")
        return 1
    print("RESULT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
