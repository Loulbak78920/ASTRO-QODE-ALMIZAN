#!/usr/bin/env python3
"""Recalcule les empreintes SHA-256 d'un dossier publie. Sortie ASCII, code 0/1/2.

Usage:
  py -3 verifier_empreintes.py [--dossier DIR]

Sans --dossier, la racine est le parent du dossier du script : le fichier est
destine a etre copie dans 05_EMPREINTES/ du dossier publie. Codes :
  0 = RESULT OK, 1 = ecart detecte, 2 = manifeste ou racine absents.
"""
import argparse
import hashlib
import json
import os
import sys

SKIP_DIRS = {".git", "__pycache__"}
MANIFEST_REL = "05_EMPREINTES/MANIFESTE_SHA256.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".pyc"):
                continue
            yield os.path.relpath(os.path.join(base, name), root).replace(os.sep, "/")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verifie un manifeste SHA-256.")
    parser.add_argument("--dossier", help="racine du dossier publie")
    args = parser.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(args.dossier) if args.dossier else os.path.dirname(here)
    manifest_path = os.path.join(root, "05_EMPREINTES", "MANIFESTE_SHA256.json")
    if not os.path.isfile(manifest_path):
        print("MANIFEST_ABSENT %s" % manifest_path.replace(os.sep, "/"))
        return 2

    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    expected = {e["chemin"]: e for e in data.get("fichiers", [])}
    if not expected:
        print("MANIFEST_VIDE %s" % manifest_path.replace(os.sep, "/"))
        return 2

    ok = mismatch = missing = 0
    for rel in sorted(expected):
        entry = expected[rel]
        path = os.path.join(root, *rel.split("/"))
        if not os.path.isfile(path):
            print("MISSING %s" % rel)
            missing += 1
            continue
        got = sha256(path)
        if got != entry["sha256"]:
            print("MISMATCH %s attendu=%s obtenu=%s" % (rel, entry["sha256"], got))
            mismatch += 1
        elif os.path.getsize(path) != entry["octets"]:
            print("MISMATCH_SIZE %s attendu=%s obtenu=%s"
                  % (rel, entry["octets"], os.path.getsize(path)))
            mismatch += 1
        else:
            ok += 1

    found = {rel for rel in iter_files(root) if rel != MANIFEST_REL}
    extra = sorted(found - set(expected))
    for rel in extra:
        print("EXTRA %s" % rel)

    print("OK=%d MISMATCH=%d MISSING=%d EXTRA=%d"
          % (ok, mismatch, missing, len(extra)))
    if mismatch or missing or extra:
        print("RESULT FAIL")
        return 1
    print("RESULT OK")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
    sys.exit(main())
