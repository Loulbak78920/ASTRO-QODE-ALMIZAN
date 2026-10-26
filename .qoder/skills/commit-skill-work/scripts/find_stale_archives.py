#!/usr/bin/env python3
"""Read-only detection of archived copies of a Skill in Git repositories.

Finds refs that contain .qoder/skills/<name>, compares their blob OIDs with the
source files (SKILL.md, references/, scripts/; caches excluded), and reports
stale archives. Never writes, fetches, commits, or pushes.

Exit codes: 0 no archive or all fresh, 1 at least one stale archive, 2 usage/env.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

INCLUDED_DIRS = ("references", "scripts")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".mypy_cache", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
MAX_REPOS = 50


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError):
            pass


def git(repo: Path, *args: str) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 128, "", ascii_text(exc)
    return proc.returncode, proc.stdout, proc.stderr


def source_files(skill: Path) -> list[str]:
    files = ["SKILL.md"] if (skill / "SKILL.md").is_file() else []
    for name in INCLUDED_DIRS:
        base = skill / name
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for filename in sorted(filenames):
                path = Path(dirpath) / filename
                if path.suffix.lower() in SKIP_SUFFIXES or not path.is_file():
                    continue
                files.append(path.relative_to(skill).as_posix())
    return sorted(files)


def find_repos(root: Path, max_depth: int) -> list[Path]:
    found: list[Path] = []
    root = root.resolve()
    for current, dirs, files in os.walk(root):
        here = Path(current)
        depth = len(here.relative_to(root).parts)
        if ".git" in dirs or ".git" in files:
            found.append(here)
            if len(found) >= MAX_REPOS:
                return found
        if depth >= max_depth:
            dirs[:] = []
        else:
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
    return found


def toplevel(path: Path) -> Path | None:
    code, out, _ = git(path, "rev-parse", "--show-toplevel")
    if code != 0 or not out.strip():
        return None
    return Path(out.strip()).resolve()


def list_refs(repo: Path) -> list[str]:
    code, out, _ = git(
        repo, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes", "refs/tags"
    )
    if code != 0:
        return []
    refs: list[str] = []
    for line in out.splitlines():
        ref = line.strip()
        if not ref:
            continue
        code, _, _ = git(repo, "symbolic-ref", "-q", ref)
        if code == 0:
            continue
        refs.append(ref)
    return refs


def archive_tree(repo: Path, ref: str, dest: str) -> dict[str, str] | None:
    code, out, _ = git(repo, "ls-tree", "-r", ref, "--", dest)
    if code != 0 or not out.strip():
        return None
    prefix = dest.rstrip("/") + "/"
    tree: dict[str, str] = {}
    for line in out.splitlines():
        meta, sep, path = line.partition("\t")
        if not sep:
            continue
        parts = meta.split()
        if len(parts) != 3 or parts[1] != "blob" or not path.startswith(prefix):
            continue
        tree[path[len(prefix):]] = parts[2]
    return tree or None


def short_ref(ref: str) -> str:
    for prefix in ("refs/heads/", "refs/remotes/", "refs/tags/"):
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref


def compare(repo: Path, skill: Path, dest: str, files: list[str], tree: dict[str, str]) -> list[str]:
    problems: list[str] = []
    for rel in files:
        archived = tree.get(rel)
        if archived is None:
            problems.append(f"MISSING  {rel}")
            continue
        code, out, err = git(repo, "hash-object", f"--path={dest}/{rel}", str(skill / rel))
        if code != 0:
            detail = ascii_text(err.strip() or out.strip())
            problems.append(f"FAIL     {rel} (hash-object: {detail})")
            continue
        expected = out.strip()
        if archived != expected:
            problems.append(f"MISMATCH {rel} archive={archived[:12]} source={expected[:12]}")
    for rel in sorted(set(tree) - set(files)):
        problems.append(f"EXTRA    {rel} absent de la source")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect stale archived copies of a Skill in Git repositories (read-only)."
    )
    parser.add_argument("--skill", required=True, help="Skill source directory")
    parser.add_argument(
        "--search-root", action="append", default=[], help="root scanned for .git directories (repeatable)"
    )
    parser.add_argument("--repo", action="append", default=[], help="explicit repository (repeatable)")
    parser.add_argument(
        "--dest", default=None, help="archive path in the repository (default: .qoder/skills/<name>)"
    )
    parser.add_argument("--max-depth", type=int, default=3, help="scan depth for --search-root (default: 3)")
    args = parser.parse_args(argv)

    configure_stdout()
    if shutil.which("git") is None:
        print("FAIL environment: git not found in PATH")
        print("RESULT FAIL")
        return 2
    if args.max_depth < 1:
        print("FAIL usage: --max-depth must be >= 1")
        print("RESULT FAIL")
        return 2
    if not args.search_root and not args.repo:
        print("FAIL usage: provide --search-root or --repo")
        print("RESULT FAIL")
        return 2

    skill = Path(args.skill).expanduser().resolve()
    if not (skill / "SKILL.md").is_file():
        print(f"FAIL usage: SKILL.md absent from {ascii_text(skill)}")
        print("RESULT FAIL")
        return 2
    files = source_files(skill)
    dest = (args.dest or f".qoder/skills/{skill.name}").replace("\\", "/").strip("/")
    if not dest or dest.startswith("/") or ".." in dest.split("/"):
        print(f"FAIL usage: invalid --dest {ascii_text(args.dest)}")
        print("RESULT FAIL")
        return 2

    candidates: list[Path] = []
    env_error = False
    for raw in args.repo:
        path = Path(raw).expanduser()
        if not path.is_dir():
            print(f"FAIL environment: repository not found: {ascii_text(path)}")
            env_error = True
            continue
        candidates.append(path)
    for raw in args.search_root:
        path = Path(raw).expanduser()
        if not path.is_dir():
            print(f"FAIL environment: search root not found: {ascii_text(path)}")
            env_error = True
            continue
        candidates.extend(find_repos(path, args.max_depth))

    ordered: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        top = toplevel(candidate)
        if top is None:
            print(f"NOTE not a repository: {ascii_text(candidate)}")
            continue
        if top not in seen:
            seen.add(top)
            ordered.append(top)

    print(f"Skill source : {ascii_text(skill)}")
    print(f"Destination  : {dest}")
    print(f"Repositories : {len(ordered)}")
    print(f"Fichiers     : {len(files)}")
    print()

    stale = False
    found = False
    for repo in ordered:
        groups: dict[str, tuple[list[str], dict[str, str]]] = {}
        for ref in list_refs(repo):
            tree = archive_tree(repo, ref, dest)
            if tree is None:
                continue
            code, out, _ = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
            if code != 0 or not out.strip():
                continue
            commit = out.strip()
            if commit not in groups:
                groups[commit] = ([], tree)
            groups[commit][0].append(ref)
        if not groups:
            continue
        found = True
        print(f"== REPO {ascii_text(repo)}")
        for commit, (refs, tree) in groups.items():
            published = any(ref.startswith("refs/remotes/") for ref in refs)
            label = "published" if published else "local"
            names = ", ".join(sorted({short_ref(ref) for ref in refs}))
            code, subject, _ = git(repo, "log", "-1", "--format=%s", commit)
            subject = subject.strip() if code == 0 else ""
            print(f"ARCHIVE {ascii_text(names)} ({commit[:12]} {ascii_text(subject)}) [{label}]")
            problems = compare(repo, skill, dest, files, tree)
            if problems:
                stale = True
                print(f"  STALE {len(problems)} anomalie(s) sur {len(files)} fichier(s) source")
                for problem in problems:
                    print(f"  {ascii_text(problem)}")
            else:
                print(f"  FRESH {len(files)}/{len(files)} fichiers identiques")
        print()

    if env_error:
        print("NOTE: resultats partiels, voir les lignes FAIL ci-dessus.")
        print("RESULT FAIL")
        return 2
    if not found:
        print("RESULT NONE")
        return 0
    if stale:
        print("NOTE: aucune archive n'a ete modifiee, commitee ni poussee.")
        print("RESULT STALE")
        return 1
    print("RESULT FRESH")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
