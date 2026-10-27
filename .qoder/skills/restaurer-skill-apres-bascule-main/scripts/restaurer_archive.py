#!/usr/bin/env python3
"""Restore a Skill's files from its Git archive into the repository root.

Source: <ref>:.qoder/skills/<skill>/
Destination: repository root, same relative paths.

The archive is the only source of truth. Files are read with
`git cat-file blob` and written byte-for-byte, so the checkout EOL filter
cannot alter them. Dry-run is the default; --apply writes.

Never touches the index, branches, HEAD or commits.

Exit codes: 0 success, 1 refusal or verification failure, 2 usage/environment.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ARCHIVE_ROOT = ".qoder/skills"
SKILL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
FORBIDDEN_PARTS = {"__pycache__"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo"}


def emit(message: str) -> None:
    print(message)


def error(message: str) -> int:
    emit(f"ERROR {message}")
    return 2


def refuse(message: str) -> int:
    emit(f"REFUSE {message}")
    return 1


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_eol(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


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
        raise SystemExit(error("git introuvable dans le PATH"))


def git_text(repo: Path, *args: str) -> str:
    proc = git(repo, *args)
    return proc.stdout.decode("utf-8", "replace").strip()


def is_within(repo: Path, path: Path) -> bool:
    try:
        resolved = path.resolve(strict=False)
    except OSError:
        return False
    repo_resolved = repo.resolve()
    return resolved == repo_resolved or repo_resolved in resolved.parents


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Restaurer les fichiers racine d'un Skill depuis les blobs de "
            ".qoder/skills/<skill>/ (dry-run par défaut)."
        )
    )
    parser.add_argument("--repo", required=True, help="racine du dépôt Git du Skill")
    parser.add_argument("--skill", required=True, help="nom du Skill archivé")
    parser.add_argument("--ref", default="HEAD", help="ref source (défaut : HEAD)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="écrire les fichiers ; sans cette option, dry-run seulement",
    )
    return parser.parse_args()


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    args = parse_args()

    repo = Path(args.repo).expanduser()
    if not repo.is_dir():
        return error(f"répertoire introuvable : {repo}")
    repo = repo.resolve()

    if not SKILL_NAME.fullmatch(args.skill) or args.skill in {".", ".."}:
        return error(f"nom de Skill invalide : {args.skill!r}")

    ref = args.ref.strip()
    if not ref or ref.startswith("-") or any(char.isspace() for char in ref):
        return error(f"ref invalide : {args.ref!r}")

    proc = git(repo, "rev-parse", "--show-toplevel")
    if proc.returncode != 0:
        return error(f"dépôt Git introuvable : {git_text(repo, 'rev-parse', '--show-toplevel')}")
    toplevel = Path(proc.stdout.decode("utf-8", "replace").strip()).resolve()
    if os.path.normcase(str(toplevel)) != os.path.normcase(str(repo)):
        return error(f"--repo doit être la racine du dépôt : {toplevel}")

    proc = git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    if proc.returncode != 0:
        return error(f"ref introuvable : {ref}")
    commit = proc.stdout.decode("ascii", "replace").strip()

    archive_dir = f"{ARCHIVE_ROOT}/{args.skill}"
    prefix = archive_dir + "/"

    proc = git(repo, "ls-tree", "-r", "-z", "--full-tree", ref, "--", archive_dir)
    if proc.returncode != 0:
        return error(f"git ls-tree a échoué pour {ref}:{archive_dir}")

    entries: list[tuple[str, str, str]] = []
    seen: dict[str, str] = {}
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            header, path_bytes = raw.split(b"\t", 1)
            mode, object_type, oid = header.decode("ascii").split(" ", 2)
            path = path_bytes.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return refuse("sortie git ls-tree illisible")

        if object_type != "blob":
            return refuse(f"entrée non blob : {path}")
        if mode not in {"100644", "100755"}:
            return refuse(f"mode non régulier : {mode} {path}")
        if not path.startswith(prefix):
            return refuse(f"chemin hors archive : {path}")

        rel = path[len(prefix):]
        pure = PurePosixPath(rel)
        if (
            not rel
            or pure.is_absolute()
            or ".." in pure.parts
            or "\\" in rel
            or rel != pure.as_posix()
        ):
            return refuse(f"chemin relatif non sûr : {rel!r}")
        if any(part in FORBIDDEN_PARTS for part in pure.parts):
            return refuse(f"cache interdit dans l'archive : {rel}")
        if pure.suffix.lower() in FORBIDDEN_SUFFIXES:
            return refuse(f"fichier compilé interdit dans l'archive : {rel}")

        key = os.path.normcase(rel)
        if key in seen:
            return refuse(f"collision de casse : {rel} et {seen[key]}")
        seen[key] = rel
        entries.append((rel, oid, mode))

    if not entries:
        return refuse(f"archive absente ou vide : {ref}:{archive_dir}")

    if "SKILL.md" not in {rel for rel, _oid, _mode in entries}:
        return refuse(f"SKILL.md absent de l'archive : {ref}:{prefix}")

    mode_label = "apply" if args.apply else "dry-run"
    emit(f"MODE {mode_label}")
    emit(f"REPO {repo}")
    emit(f"REF {ref} COMMIT {commit}")
    emit(f"ARCHIVE {prefix} FILES {len(entries)}")

    changed = 0
    for rel, oid, mode in entries:
        proc = git(repo, "cat-file", "blob", oid)
        if proc.returncode != 0:
            return refuse(f"blob illisible : {oid} ({rel})")
        data = proc.stdout

        dest = repo / rel
        if dest.is_symlink():
            return refuse(f"cible symbolique refusée : {rel}")
        if dest.exists() and not dest.is_file():
            return refuse(f"cible non régulière : {rel}")
        if not is_within(repo, dest.parent):
            return refuse(f"parent hors dépôt : {rel}")

        existing = dest.read_bytes() if dest.is_file() else None
        if existing is None:
            state = "MISSING"
        elif existing == data:
            state = "SAME"
        elif normalize_eol(existing) == normalize_eol(data):
            state = "EOL_ONLY"
        else:
            state = "DIFF"

        action = "NONE"
        if state != "SAME":
            changed += 1
            if args.apply:
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    tmp = dest.with_name(f".{dest.name}.restore-{os.getpid()}.tmp")
                    tmp.write_bytes(data)
                    os.replace(tmp, dest)
                except OSError as exc:
                    try:
                        tmp.unlink()
                    except (OSError, UnboundLocalError):
                        pass
                    return refuse(f"écriture impossible : {rel}: {exc}")
                if dest.read_bytes() != data:
                    return refuse(f"vérification après écriture échouée : {rel}")
                action = "WROTE"
            else:
                action = "WOULD_WRITE"

        emit(
            f"FILE rel={rel} oid={oid} sha256={sha256(data)} bytes={len(data)} "
            f"state={state} action={action} mode={mode}"
        )

    if args.apply:
        emit(f"RESULT APPLIED_OK files={len(entries)} changed={changed} verified={len(entries)}")
    else:
        emit(f"RESULT DRY_RUN_OK files={len(entries)} would_change={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
