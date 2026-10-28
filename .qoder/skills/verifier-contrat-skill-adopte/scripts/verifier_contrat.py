#!/usr/bin/env python3
"""Read-only helpers: tree stability, package fingerprints, contract assertions.

Subcommands:
  arbre      --racine DIR [--echantillons 4] [--intervalle 3]
  empreintes --racine DIR
  selftest

Stdout is ASCII. Exit codes: 0 ok/stable, 1 unstable/selftest failure, 2 usage.
Import the helpers from a target-specific check.py; they print NAME=TRUE|FALSE
tokens so a replay never depends on reading output by eye.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

Inventory = dict[str, tuple[int, int, str]]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventaire(racine: Path) -> Inventory:
    """Relative path -> (size, mtime_ns, sha256), sorted, files only."""
    result: Inventory = {}
    for path in sorted(racine.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(racine).as_posix()
        stat = path.stat()
        result[rel] = (stat.st_size, stat.st_mtime_ns, sha256_file(path))
    return result


def empreinte_arbre(racine: Path) -> tuple[str, Inventory]:
    inventaire_courant = inventaire(racine)
    digest = hashlib.sha256()
    for rel in sorted(inventaire_courant):
        size, mtime_ns, file_sha = inventaire_courant[rel]
        digest.update("{}\t{}\t{}\t{}\n".format(rel, size, mtime_ns, file_sha).encode("utf-8"))
    return digest.hexdigest(), inventaire_courant


def differences(avant: Inventory, apres: Inventory) -> list[str]:
    return [
        rel
        for rel in sorted(set(avant) | set(apres))
        if avant.get(rel) != apres.get(rel)
    ]


def jeton(nom: str, ok: bool) -> bool:
    print("{}={}".format(nom, "TRUE" if ok else "FALSE"))
    return bool(ok)


def controle_zero(
    texte: str, absent: str, present: str, prefixe: str = "CONTRAT"
) -> bool:
    """Zero occurrences is only evidence when the positive control fires."""
    positif = len(re.findall(present, texte, flags=re.M))
    zero = len(re.findall(absent, texte, flags=re.M))
    ok_positif = jeton(prefixe + "_CONTROLE_POSITIF", positif >= 1)
    ok_zero = jeton(prefixe + "_ZERO_OCCURRENCE", zero == 0)
    return ok_positif and ok_zero


def clefs(texte: str, attendues, prefixe: str = "CONTRAT") -> bool:
    try:
        document = json.loads(texte)
    except ValueError:
        return jeton(prefixe + "_JSON_KEYS", False)
    ok = sorted(document) == sorted(attendues)
    if not ok:
        print("EXPECTED=" + "|".join(sorted(map(str, attendues))))
        print("ACTUAL=" + "|".join(sorted(map(str, document))))
    return jeton(prefixe + "_JSON_KEYS", ok)


def executer(args, cwd=None):
    """Run without a shell; capture rc/output as UTF-8. Take rc before any pipe."""
    return subprocess.run(
        [str(item) for item in args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def cmd_arbre(args) -> int:
    racine = Path(args.racine)
    if not racine.is_dir():
        print("ERROR: root not found: " + str(racine))
        return EXIT_USAGE
    if args.echantillons < 2:
        print("ERROR: --echantillons must be >= 2")
        return EXIT_USAGE
    if args.intervalle < 0:
        print("ERROR: --intervalle must be >= 0")
        return EXIT_USAGE

    stable = True
    precedent: Inventory | None = None
    for numero in range(1, args.echantillons + 1):
        if numero > 1:
            time.sleep(args.intervalle)
        empreinte, courant = empreinte_arbre(racine)
        print("SAMPLE {} TREE_SHA256={}".format(numero, empreinte))
        if precedent is None:
            print("FILES={}".format(len(courant)))
        else:
            for rel in differences(precedent, courant):
                print("CHANGED " + rel)
                stable = False
        precedent = courant
    print("STABLE=" + ("TRUE" if stable else "FALSE"))
    return EXIT_OK if stable else EXIT_FAIL


def cmd_empreintes(args) -> int:
    racine = Path(args.racine)
    if not racine.is_dir():
        print("ERROR: root not found: " + str(racine))
        return EXIT_USAGE
    courant = inventaire(racine)
    print("FILES={}".format(len(courant)))
    for rel in sorted(courant):
        size, mtime_ns, file_sha = courant[rel]
        print("{}  {}  {}  {}".format(file_sha, size, mtime_ns, rel))
    return EXIT_OK


def cmd_selftest(_args) -> int:
    ok = True

    print("-- positive control fires --")
    ok = controle_zero(
        "## Drift vs snapshot (t)\nadded: 0 | removed: 0\n",
        absent=r"^stability:",
        present=r"^## Drift vs snapshot",
        prefixe="T1",
    ) and ok

    print("-- negative control: missing anchor must fail --")
    negatif = controle_zero(
        "no anchor here\n",
        absent=r"^stability:",
        present=r"^## Drift vs snapshot",
        prefixe="T2",
    )
    ok = jeton("SELFTEST_CONTROLE_NEGATIF", negatif is False) and ok

    print("-- keyset equality --")
    ok = clefs('{"b": 1, "a": 2}', ["a", "b"], prefixe="T3") and ok
    negatif_clefs = clefs('{"b": 1}', ["a", "b"], prefixe="T4")
    ok = jeton("SELFTEST_KEYSET_NEGATIF", negatif_clefs is False) and ok

    print("-- rc capture --")
    proc = executer([sys.executable, "-B", "-c", "import sys; sys.exit(3)"])
    ok = jeton("SELFTEST_RUN_RC", proc.returncode == 3) and ok

    print("-- tree fingerprint determinism --")
    base = Path(tempfile.mkdtemp(prefix="verifier-contrat-"))
    try:
        (base / "a.txt").write_text("a", encoding="utf-8")
        (base / "sub").mkdir()
        (base / "sub" / "b.txt").write_text("b", encoding="utf-8")
        premier, inventaire_un = empreinte_arbre(base)
        second, _ = empreinte_arbre(base)
        ok = jeton(
            "SELFTEST_TREE_DETERMINISTE",
            premier == second and len(inventaire_un) == 2,
        ) and ok
        (base / "a.txt").write_text("a2", encoding="utf-8")
        troisieme, _ = empreinte_arbre(base)
        ok = jeton("SELFTEST_TREE_CHANGEMENT_DETECTE", troisieme != premier) and ok
    finally:
        shutil.rmtree(base, ignore_errors=True)

    print("SELFTEST=" + ("PASS" if ok else "FAIL"))
    return EXIT_OK if ok else EXIT_FAIL


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only acceptance helpers for a Skill package."
    )
    sub = parser.add_subparsers(dest="commande", required=True)

    arbre = sub.add_parser("arbre", help="sample the whole-tree fingerprint")
    arbre.add_argument("--racine", required=True)
    arbre.add_argument("--echantillons", type=int, default=4)
    arbre.add_argument("--intervalle", type=float, default=3.0)
    arbre.set_defaults(func=cmd_arbre)

    empreintes = sub.add_parser("empreintes", help="list size/mtime_ns/sha256")
    empreintes.add_argument("--racine", required=True)
    empreintes.set_defaults(func=cmd_empreintes)

    self_test = sub.add_parser("selftest", help="prove the assertion helpers fire")
    self_test.set_defaults(func=cmd_selftest)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (OSError, ValueError) as exc:
        print("ERROR: " + str(exc))
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
