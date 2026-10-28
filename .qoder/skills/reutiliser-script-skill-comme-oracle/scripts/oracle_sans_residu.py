#!/usr/bin/env python3
"""Run a dependency Skill's command and prove it leaves no bytecode cache."""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

CACHE = "__pycache__"
MTIME_TOLERANCE_NS = 2_000_000_000


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def snapshot(root: Path) -> tuple[dict[str, tuple[int, int, str]], set[str]]:
    files: dict[str, tuple[int, int, str]] = {}
    for pyc in sorted(root.rglob("*.pyc")):
        rel = pyc.relative_to(root).as_posix()
        try:
            st = pyc.stat()
            digest = hashlib.sha256(pyc.read_bytes()).hexdigest()
        except OSError as exc:
            files[rel] = (-1, -1, f"unreadable:{ascii_text(exc)}")
            continue
        files[rel] = (st.st_size, st.st_mtime_ns, digest)
    dirs = {p.relative_to(root).as_posix() for p in root.rglob(CACHE) if p.is_dir()}
    return files, dirs


def describe(entry: tuple[int, int, str]) -> str:
    size, mtime_ns, digest = entry
    return f"{size} bytes mtime_ns={mtime_ns} sha256={digest[:12]}"


def diff(
    before: tuple[dict[str, tuple[int, int, str]], set[str]],
    after: tuple[dict[str, tuple[int, int, str]], set[str]],
) -> tuple[dict[str, tuple[int, int, str]], set[str], list[str]]:
    new_files = {rel: entry for rel, entry in after[0].items() if rel not in before[0]}
    new_dirs = after[1] - before[1]
    changed = [
        rel
        for rel in sorted(set(before[0]) & set(after[0]))
        if before[0][rel] != after[0][rel]
    ]
    return new_files, new_dirs, changed


def report_new(label: str, new_files: dict, new_dirs: set[str], changed: list[str]) -> None:
    for rel in sorted(new_files):
        print(f"{label} {ascii_text(rel)} {describe(new_files[rel])}")
    for rel in sorted(new_dirs):
        print(f"{label}_DIR {ascii_text(rel)}")
    for rel in changed:
        print(f"MODIFIED {ascii_text(rel)}")
    if not new_files and not new_dirs and not changed:
        print(f"{label} (none)")


def run(command: list[str]) -> int:
    print(f"COMMANDE {' '.join(ascii_text(part) for part in command)}")
    try:
        completed = subprocess.run(command, check=False)
    except FileNotFoundError:
        print(f"FAIL  command not found: {ascii_text(command[0])}")
        return 127
    print(f"ORACLE_RC={completed.returncode}")
    return completed.returncode


def clean(root: Path, new_files: dict, new_dirs: set[str], started_ns: int) -> int:
    unsafe = 0
    for rel in sorted(new_files):
        path = root / rel
        if CACHE not in Path(rel).parts:
            print(f"REFUS {ascii_text(rel)} not under {CACHE}")
            unsafe += 1
            continue
        try:
            mtime_ns = path.stat().st_mtime_ns
        except OSError as exc:
            print(f"REFUS {ascii_text(rel)} stat failed: {ascii_text(exc)}")
            unsafe += 1
            continue
        if mtime_ns < started_ns - MTIME_TOLERANCE_NS:
            print(f"REFUS {ascii_text(rel)} predates this run (mtime_ns={mtime_ns})")
            unsafe += 1
            continue
        try:
            path.unlink()
        except OSError as exc:
            print(f"REFUS {ascii_text(rel)} delete failed: {ascii_text(exc)}")
            unsafe += 1
            continue
        print(f"REMOVED {ascii_text(rel)}")
    for rel in sorted(new_dirs, key=lambda item: len(Path(item).parts), reverse=True):
        path = root / rel
        try:
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
                print(f"REMOVED_DIR {ascii_text(rel)}")
            elif path.is_dir():
                print(f"KEPT_DIR {ascii_text(rel)} not empty")
        except OSError as exc:
            print(f"REFUS {ascii_text(rel)} rmdir failed: {ascii_text(exc)}")
            unsafe += 1
    return unsafe


def split_command(argv: list[str]) -> tuple[list[str], list[str]]:
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1:]
    return argv, []


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except (AttributeError, OSError):
        pass
    raw = list(sys.argv[1:] if argv is None else argv)
    options, command = split_command(raw)
    parser = argparse.ArgumentParser(
        prog="oracle_sans_residu.py",
        description="Run a dependency command and prove it leaves no bytecode cache.",
    )
    parser.add_argument("--dependance", type=Path, required=True)
    parser.add_argument("--nettoyer", action="store_true")
    parser.add_argument("--rejouer", action="store_true")
    args = parser.parse_args(options)

    dependance = args.dependance.expanduser().resolve()
    if not dependance.is_dir():
        print(f"FAIL  dependency directory not found: {ascii_text(dependance)}")
        return 2
    if not command:
        print("FAIL  no command given after --")
        return 2
    if os.environ.get("PYTHONDONTWRITEBYTECODE"):
        print("FAIL  PYTHONDONTWRITEBYTECODE is set; the observation would be vacuous")
        return 2

    print(f"DEPENDANCE {ascii_text(dependance)}")
    baseline = snapshot(dependance)
    print(f"AVANT files={len(baseline[0])} dirs={len(baseline[1])}")

    started_ns = time.time_ns()
    oracle_rc = run(command)
    first = snapshot(dependance)
    print(f"APRES files={len(first[0])} dirs={len(first[1])}")
    new_files, new_dirs, changed = diff(baseline, first)
    report_new("NEW", new_files, new_dirs, changed)

    unsafe = 0
    if args.nettoyer:
        unsafe = clean(dependance, new_files, new_dirs, started_ns)
        baseline = snapshot(dependance)
        print(f"APRES_NETTOYAGE files={len(baseline[0])} dirs={len(baseline[1])}")

    replay_rc = oracle_rc
    if args.rejouer:
        replay_rc = run(command)
        final = snapshot(dependance)
        print(f"APRES_REJEU files={len(final[0])} dirs={len(final[1])}")
        residue_files, residue_dirs, residue_changed = diff(baseline, final)
        report_new("NEW_REJEU", residue_files, residue_dirs, residue_changed)
        print(f"PROOF={'NO_RECREATION' if not (residue_files or residue_dirs or residue_changed) else 'RECREATED'}")
    else:
        residue_files, residue_dirs, residue_changed = diff(baseline, snapshot(dependance))
        print("PROOF=NOT_RUN")

    residue = bool(residue_files or residue_dirs or residue_changed)
    ok = oracle_rc == 0 and replay_rc == 0 and not residue and unsafe == 0
    print(f"ORACLE_RC_FINAL={replay_rc}")
    print(f"NEW_RESIDUE={'PRESENT' if residue else 'NONE'}")
    print(f"RESULT {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
