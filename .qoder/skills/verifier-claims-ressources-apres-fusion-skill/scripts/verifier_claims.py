#!/usr/bin/env python3
"""Controle lecture seule de la parite affirmations/fichiers d'un paquet Skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__"}


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="verifier_claims.py",
        description="Verifie en lecture seule qu'un jeton distinctif existe dans chaque fichier cite.",
    )
    parser.add_argument("skill_dir")
    parser.add_argument("--claim", action="append", default=[], metavar="PATH::TOKEN")
    parser.add_argument("--marker", action="append", default=[], metavar="TOKEN[@N]")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def parse_claim(raw):
    if "::" not in raw:
        raise ValueError(f"--claim attendu PATH::TOKEN, recu: {raw!r}")
    rel, token = raw.split("::", 1)
    rel, token = rel.strip(), token.strip()
    if not rel or not token:
        raise ValueError(f"--claim vide dans: {raw!r}")
    return rel, token


def parse_marker(raw):
    if "@" in raw:
        token, _, number = raw.rpartition("@")
        token = token.strip()
        try:
            expected = int(number)
        except ValueError as exc:
            raise ValueError(f"--marker attendu TOKEN ou TOKEN@N, recu: {raw!r}") from exc
    else:
        token, expected = raw.strip(), 1
    if not token or expected < 1:
        raise ValueError(f"--marker invalide: {raw!r}")
    return token, expected


def inventory(root):
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or rel.suffix == ".pyc":
            continue
        data = path.read_bytes()
        rows.append({
            "path": rel.as_posix(),
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return rows


def safe_target(root, rel):
    candidate = Path(rel)
    if candidate.is_absolute():
        raise ValueError(f"chemin absolu interdit: {rel!r}")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"chemin hors du paquet interdit: {rel!r}")
    return resolved


def read_text(path):
    return path.read_text(encoding="utf-8-sig")


def check_claim(root, rel, token):
    result = {"path": rel, "token": token, "count": 0, "first_line": None}
    try:
        target = safe_target(root, rel)
    except ValueError as exc:
        result["status"] = "CLAIM_INVALID_PATH"
        result["detail"] = str(exc)
        return result
    if not target.is_file():
        result["status"] = "CLAIM_MISSING"
        return result
    try:
        text = read_text(target)
    except UnicodeDecodeError:
        result["status"] = "CLAIM_ENCODING_ERROR"
        return result
    result["count"] = text.count(token)
    for number, line in enumerate(text.splitlines(), 1):
        if token in line:
            result["first_line"] = number
            break
    result["status"] = "CLAIM_SUPPORTED" if result["count"] else "CLAIM_EMPTY"
    return result


def check_marker(text, token, expected):
    count = text.count(token)
    return {
        "token": token,
        "count": count,
        "expected": expected,
        "status": "MARKER_OK" if count == expected else "MARKER_MISMATCH",
    }


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    root = Path(args.skill_dir)
    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        print(f"ERROR SKILL.md introuvable sous {root}", file=sys.stderr)
        return 2
    if not args.claim and not args.marker:
        print("ERROR fournir au moins un --claim ou un --marker", file=sys.stderr)
        return 2
    try:
        claims = [parse_claim(raw) for raw in args.claim]
        markers = [parse_marker(raw) for raw in args.marker]
        files = inventory(root)
        marker_text = read_text(skill_md)
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    claim_rows = [check_claim(root, rel, token) for rel, token in claims]
    marker_rows = [check_marker(marker_text, token, expected) for token, expected in markers]
    bad_claims = sum(1 for row in claim_rows if row["status"] != "CLAIM_SUPPORTED")
    bad_markers = sum(1 for row in marker_rows if row["status"] != "MARKER_OK")
    failed = bool(bad_claims or bad_markers)
    summary = {
        "files": len(files),
        "claims": len(claim_rows),
        "claims_supported": len(claim_rows) - bad_claims,
        "claims_bad": bad_claims,
        "markers": len(marker_rows),
        "markers_ok": len(marker_rows) - bad_markers,
        "markers_bad": bad_markers,
    }

    if args.json:
        print(json.dumps({
            "root": str(root.resolve()),
            "files": files,
            "claims": claim_rows,
            "markers": marker_rows,
            "summary": summary,
            "result": "FAIL" if failed else "PASS",
        }, ensure_ascii=True, indent=2))
    else:
        print(f"Root: {root.resolve()}")
        print(f"Fichiers ({len(files)}):")
        for row in files:
            print(f"  {row['path']} {row['size']} {row['sha256']}")
        for row in claim_rows:
            line = row["first_line"] if row["first_line"] is not None else "-"
            detail = f" detail={row['detail']}" if "detail" in row else ""
            print(f"Affirmation: {row['path']} :: {row['token']!r} -> {row['count']} "
                  f"({row['status']}) ligne={line}{detail}")
        for row in marker_rows:
            print(f"Marqueur: {row['token']!r} -> {row['count']}/{row['expected']} ({row['status']})")
        print(f"Resume: affirmations={summary['claims']} supportees={summary['claims_supported']} "
              f"ecarts={summary['claims_bad']} marqueurs={summary['markers']} ok={summary['markers_ok']}")
        print(f"RESULT {'FAIL' if failed else 'PASS'}")
        print(f"rc={1 if failed else 0}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
