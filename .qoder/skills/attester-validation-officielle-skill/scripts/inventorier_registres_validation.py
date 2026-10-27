#!/usr/bin/env python3
"""Inventaire en lecture seule des registres de validation de Skills.

Ne cree ni ne modifie aucun fichier. Sortie ASCII, lignes KEY=VALUE.
Codes de sortie : 0 = aucun candidat, 1 = candidat trouve, 2 = usage/IO.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build",
    ".mypy_cache", ".pytest_cache", ".idea", ".vscode",
}
TEXT_EXT = {".json", ".jsonl", ".md", ".csv", ".yaml", ".yml", ".txt"}
DB_EXT = {".db", ".sqlite", ".sqlite3"}
NAME_RE = re.compile(
    r"(registre|registry|inventory|inventaire|validation|skill-usage|skills?-snapshot)",
    re.I,
)
STATUS_TOKENS = (
    "validation", "validated", "statut", "status", "verified", "verifie",
)
DB_STATUS_TOKENS = ("valid", "statut", "status", "verif")


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def emit(line: str) -> None:
    sys.stdout.write(ascii_text(line) + "\n")


def load_skill_names(roots):
    names = set()
    for root in roots:
        path = Path(root)
        if not path.is_dir():
            continue
        try:
            skill_files = sorted(path.glob("*/SKILL.md"))
        except OSError:
            continue
        for skill_md in skill_files:
            try:
                text = skill_md.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            name = skill_md.parent.name
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    match = re.search(
                        r"^name:\s*[\"']?([A-Za-z0-9._-]+)", parts[1], re.M
                    )
                    if match:
                        name = match.group(1)
            names.add(name)
    return names


def iter_files(root, max_depth, skip_prefixes, skip_roots):
    root = Path(root).resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        rel = here.relative_to(root)
        kept = []
        for name in sorted(dirnames):
            child_rel = (rel / name).as_posix()
            if name in SKIP_DIRS:
                continue
            if any(child_rel == p or child_rel.startswith(p + "/") for p in skip_prefixes):
                continue
            kept.append(name)
        dirnames[:] = kept
        if len(rel.parts) >= max_depth:
            dirnames[:] = []
        for filename in sorted(filenames):
            path = here / filename
            try:
                resolved = path.resolve()
            except OSError:
                resolved = path
            if any(_is_under(resolved, skip) for skip in skip_roots):
                continue
            yield path


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(Path(root).resolve())
        return True
    except (ValueError, OSError):
        return False


def classify_text(path: Path, text: str, names):
    low = text.lower()
    mentions = sum(1 for name in names if name.lower() in low)
    has_status = any(token in low for token in STATUS_TOKENS)
    if path.name.lower() == "skill-usage.json" or "usagecount" in low:
        return "USAGE_COUNTERS_ONLY", "usageCount/lastUsedAt seulement"
    if "qoder-skill-inventory" in low:
        return "READ_ONLY_INVENTORY", "format=qoder-skill-inventory/1"
    if mentions and has_status:
        return "CANDIDATE", "mentions=%d statut=oui" % mentions
    if mentions:
        return "NO_VALIDATION_STATUS", "mentions=%d statut=non" % mentions
    if re.search(r"(registre|registry)", path.name, re.I):
        return "BUSINESS_REGISTRY", "mentions=0"
    return "UNRELATED", "mentions=0"


def classify_db(path: Path):
    try:
        uri = Path(path).resolve().as_uri() + "?mode=ro&immutable=1"
        connection = sqlite3.connect(uri, uri=True, timeout=1)
    except (sqlite3.Error, OSError, ValueError) as exc:
        return "UNREADABLE_DB", exc.__class__.__name__
    try:
        cursor = connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        columns = []
        for table in tables:
            safe = str(table).replace('"', '""')
            try:
                cursor = connection.execute('PRAGMA table_info("%s")' % safe)
                columns.extend(str(row[1]) for row in cursor.fetchall())
            except sqlite3.Error:
                continue
        blob = " ".join(tables + columns).lower()
        if "skill" in blob:
            if any(token in blob for token in DB_STATUS_TOKENS):
                return "CANDIDATE", "tables=%d skill+statut" % len(tables)
            return "NO_VALIDATION_STATUS", "tables=%d skill" % len(tables)
        return "UNRELATED_DB", "tables=%d" % len(tables)
    except sqlite3.Error as exc:
        return "UNREADABLE_DB", exc.__class__.__name__
    finally:
        connection.close()


def scan_location(label, root, args, names, skill_roots, skip_prefixes, found):
    root = Path(root)
    if not root.is_dir():
        emit("LOCATION=%s|%s|missing" % (label, root))
        return 0
    emit("LOCATION=%s|%s|exists" % (label, root))
    examined = 0
    for path in iter_files(root, args.max_depth, skip_prefixes, skill_roots):
        suffix = path.suffix.lower()
        if suffix in DB_EXT:
            examined += 1
            cls, detail = classify_db(path)
            found.append((cls, path, "%s|%s" % (label, detail)))
            continue
        if suffix not in TEXT_EXT or not NAME_RE.search(path.name):
            continue
        examined += 1
        try:
            with open(path, "rb") as handle:
                raw = handle.read(args.max_file_bytes)
        except OSError as exc:
            found.append(("UNREADABLE", path, "%s|%s" % (label, exc.__class__.__name__)))
            continue
        text = raw.decode("utf-8", "replace")
        cls, detail = classify_text(path, text, names)
        found.append((cls, path, "%s|%s" % (label, detail)))
    return examined


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inventaire lecture seule des registres de validation de Skills."
    )
    parser.add_argument("--workspace", required=True, help="racine du projet")
    parser.add_argument("--archive", default=None, help="depot d'archive (optionnel)")
    parser.add_argument("--qoder-home", default=str(Path.home() / ".qoder"))
    parser.add_argument("--skills-root", action="append", default=[])
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--max-file-bytes", type=int, default=3_000_000)
    args = parser.parse_args(argv)

    workspace = Path(args.workspace)
    if not workspace.is_dir():
        emit("RESULT FAIL")
        emit("EXIT=2")
        return 2
    if args.max_depth < 1:
        emit("RESULT FAIL")
        emit("EXIT=2")
        return 2

    skill_roots = [Path(p) for p in args.skills_root]
    if not skill_roots:
        skill_roots = [Path(args.qoder_home) / "skills", workspace / ".qoder" / "skills"]

    names = load_skill_names(skill_roots)
    found = []
    emit("TOOL=inventaire-registres-validation/1")
    emit("WORKSPACE=%s" % workspace.resolve())
    emit("QODER_HOME=%s" % Path(args.qoder_home).resolve())
    emit("ARCHIVE=%s" % (Path(args.archive).resolve() if args.archive else "n/a"))
    emit("SKILLS_ROOTS=%d" % len(skill_roots))
    emit("SKILL_NAMES_LOADED=%d" % len(names))

    examined = 0
    examined += scan_location(
        "WORKSPACE", workspace, args, names, skill_roots,
        (".qoder/tmp", ".qoder/skills", ".qoder/projects"), found,
    )
    examined += scan_location(
        "QODER_HOME", Path(args.qoder_home), args, names, skill_roots,
        ("skills", "projects", "app", "cache", ".cache", ".models", "file-history",
         "logs", "tasks", "tmp", "shell-snapshots", "entry", "host-actions", "ipc",
         "sites", "plugins", "qoder-knowledge", "security-resources", "bin", ".bin",
         ".auth"),
        found,
    )
    if args.archive:
        examined += scan_location(
            "ARCHIVE", Path(args.archive), args, names, skill_roots,
            (".qoder/skills",), found,
        )

    counts = Counter(item[0] for item in found)
    candidates = [item for item in found if item[0] == "CANDIDATE"]
    visible = {
        "CANDIDATE", "NO_VALIDATION_STATUS", "READ_ONLY_INVENTORY",
        "USAGE_COUNTERS_ONLY", "UNREADABLE_DB", "UNREADABLE",
    }
    entries = sorted(
        (item for item in found if item[0] in visible),
        key=lambda item: (item[0], str(item[1])),
    )
    for cls, path, detail in entries:
        emit("ENTRY=%s|%s|%s" % (cls, path, detail))

    aggregated = {"BUSINESS_REGISTRY", "UNRELATED", "UNRELATED_DB"}
    for cls in sorted(aggregated):
        examples = [item for item in found if item[0] == cls]
        for _, path, detail in examples[:3]:
            emit("EXAMPLE=%s|%s|%s" % (cls, path, detail))

    emit("EXAMINED_FILES=%d" % examined)
    for cls in sorted(counts):
        emit("CLASS_COUNT=%s:%d" % (cls, counts[cls]))
    emit("CANDIDATE_COUNT=%d" % len(candidates))
    verdict = "REGISTRY_CANDIDATE_FOUND" if candidates else "NO_SKILL_VALIDATION_REGISTRY"
    emit("VERDICT=%s" % verdict)
    emit("RESULT PASS")
    code = 1 if candidates else 0
    emit("EXIT=%d" % code)
    return code


if __name__ == "__main__":
    sys.exit(main())
