#!/usr/bin/env python3
"""Read-only SHA-256 comparison between a user-level Skill and its archived copy.

Compares SKILL.md, references/ and scripts/ from the source directory with
either the working-tree copy inside a Git repository or the blobs of a remote
ref (for example origin/main), then reports files present in the destination
but absent from the source, caches included. Never writes to the repository.

Exit codes: 0 all files identical, 1 divergence or missing/extra file, 2 usage error.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
INCLUDED_DIRS = ("references", "scripts")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fail(message: str) -> None:
    print(f"ERROR {message}")
    raise SystemExit(2)


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["MSYS_NO_PATHCONV"] = "1"
    env["MSYS2_ARG_CONV_EXCL"] = "*"
    return env


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            env=git_env(),
        )
    except FileNotFoundError:
        fail("git introuvable dans le PATH")


def collect(source: Path) -> list[str]:
    if not source.is_dir():
        fail(f"source introuvable : {source}")
    if not (source / "SKILL.md").is_file():
        fail(f"SKILL.md absent de : {source}")
    rels = ["SKILL.md"]
    for name in INCLUDED_DIRS:
        base = source / name
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for filename in sorted(filenames):
                path = Path(dirpath) / filename
                if path.suffix.lower() in SKIP_SUFFIXES or not path.is_file():
                    continue
                rels.append(path.relative_to(source).as_posix())
    return rels


def normalize_dest(value: str) -> str:
    dest = value.replace("\\", "/").strip("/")
    if not dest or dest.startswith("/") or ".." in dest.split("/"):
        fail(f"destination invalide : {value}")
    return dest


def read_worktree(repo: Path, dest: str, rel: str) -> bytes | None:
    path = repo / dest / rel
    if not path.is_file():
        return None
    return path.read_bytes()


def read_remote(repo: Path, ref: str, dest: str, rel: str) -> bytes | None:
    proc = git(repo, "show", f"{ref}:{dest}/{rel}")
    if proc.returncode != 0:
        return None
    return proc.stdout


def list_worktree(repo: Path, dest: str) -> set[str]:
    base = repo / dest
    if not base.is_dir():
        return set()
    found: set[str] = set()
    for dirpath, _dirnames, filenames in os.walk(base):
        for filename in filenames:
            path = Path(dirpath) / filename
            found.add(path.relative_to(base).as_posix())
    return found


def list_remote(repo: Path, ref: str, dest: str) -> set[str]:
    proc = git(repo, "ls-tree", "-r", "--name-only", ref, "--", dest)
    if proc.returncode != 0:
        fail(f"impossible de lister {ref}:{dest}")
    prefix = dest.rstrip("/") + "/"
    found: set[str] = set()
    for line in proc.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith(prefix):
            found.add(line[len(prefix):])
    return found


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Compare les SHA-256 d'un Skill avec sa copie archivee (lecture seule)."
    )
    parser.add_argument("--source", required=True, help="dossier du Skill source")
    parser.add_argument("--repo", required=True, help="depot Git contenant l'archive")
    parser.add_argument("--ref", default="origin/main", help="ref distante (defaut: origin/main)")
    parser.add_argument(
        "--from",
        dest="origin",
        choices=("worktree", "remote"),
        default="worktree",
        help="comparer avec la copie worktree ou avec les blobs d'une ref (defaut: worktree)",
    )
    parser.add_argument(
        "--dest",
        default=None,
        help="chemin relatif de l'archive dans le depot (defaut: .qoder/skills/<nom>)",
    )
    args = parser.parse_args()

    source = Path(args.source).resolve()
    repo = Path(args.repo).resolve()
    dest = normalize_dest(args.dest or f".qoder/skills/{source.name}")

    proc = git(repo, "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip()
        fail(f"depot invalide : {repo} ({detail})")
    toplevel = proc.stdout.decode("utf-8", "replace").strip()

    if args.origin == "remote":
        check = git(repo, "rev-parse", "--verify", "--quiet", f"{args.ref}^{{commit}}")
        if check.returncode != 0:
            fail(f"ref introuvable : {args.ref} (lancer git fetch origin ?)")
        reference_label = args.ref
        read = lambda rel: read_remote(repo, args.ref, dest, rel)
        dest_files = list_remote(repo, args.ref, dest)
    else:
        reference_label = "worktree"
        read = lambda rel: read_worktree(repo, dest, rel)
        dest_files = list_worktree(repo, dest)

    rels = collect(source)

    print(f"Skill source : {source}")
    print(f"Depot        : {repo} ({toplevel})")
    print(f"Reference    : {reference_label}")
    print(f"Destination  : {dest}")
    print(f"Fichiers     : {len(rels)}")
    print()

    failures = 0
    for rel in rels:
        source_bytes = (source / rel).read_bytes()
        source_hash = sha256(source_bytes)
        reference_bytes = read(rel)
        if reference_bytes is None:
            print(f"MISSING  {rel:<44} absent de {reference_label}")
            failures += 1
            continue
        reference_hash = sha256(reference_bytes)
        if source_hash == reference_hash:
            print(f"OK       {rel:<44} {source_hash[:12]}")
        else:
            print(
                f"MISMATCH {rel:<44} source={source_hash[:12]} "
                f"{reference_label}={reference_hash[:12]}"
            )
            failures += 1

    extras = sorted(dest_files - set(rels))
    if extras:
        print()
        for rel in extras:
            print(f"EXTRA    {rel:<44} absent de la source")
            failures += 1

    print()
    if failures:
        print(f"RESULT FAIL - {failures} anomalie(s) sur {len(rels)} fichier(s) source")
        return 1
    print(f"RESULT PASS - {len(rels)}/{len(rels)} fichiers identiques")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
