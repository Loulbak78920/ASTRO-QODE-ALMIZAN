#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifie une paire source Solidity / artefact compilé avant tout déploiement.

Contrôles, dans l'ordre :
  1. lisibilité de la source et de l'artefact, JSON valide ;
  2. clés requises présentes, bytecode hexadécimal non vide ;
  3. longueur du bytecode cohérente avec bytecode_octets ;
  4. fraîcheur : SHA-256 de la source == artefact.source_sha256 ;
  5. taille sous la limite EIP-170 (24 576 octets par défaut) ;
  6. fonctions ABI demandées présentes ;
  7. motifs interdits absents de la source.

Codes de sortie : 0 = PASS, 1 = contrôle échoué, 2 = usage ou lecture impossible.
La sortie est volontairement ASCII pour rester lisible sur une console Windows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

CLES_REQUISES = ("contrat", "compilateur", "source_sha256", "bytecode_hex")
HEX = re.compile(r"^[0-9a-fA-F]+$")
MOTIFS_INTERDITS = (
    ("selfdestruct", r"\bselfdestruct\s*\("),
    ("delegatecall", r"\.delegatecall\s*\("),
    ("tx.origin", r"\btx\.origin\b"),
    ("assembly", r"\bassembly\b"),
    ("litteral 32 octets", r"0x[0-9a-fA-F]{64}"),
)
MOTS_SECRETS = ("private key", "private_key", "mnemonic", "seed phrase")


def ascii_sur(message: str) -> str:
    return message.encode("ascii", "backslashreplace").decode("ascii")


class Rapport:
    def __init__(self) -> None:
        self.echecs = 0

    def ok(self, message: str) -> None:
        print("OK   " + ascii_sur(message))

    def echec(self, message: str) -> None:
        print("FAIL " + ascii_sur(message))
        self.echecs += 1


def construire_parseur() -> argparse.ArgumentParser:
    parseur = argparse.ArgumentParser(
        description="Vérifie la fraîcheur et la sûreté d'un artefact Solidity avant déploiement.",
    )
    parseur.add_argument("--source", required=True, help="fichier .sol")
    parseur.add_argument("--artifact", required=True, help="artefact JSON compilé")
    parseur.add_argument(
        "--limit",
        type=int,
        default=24576,
        help="limite de taille du bytecode en octets (EIP-170 = 24576)",
    )
    parseur.add_argument(
        "--require",
        action="append",
        default=[],
        metavar="FONCTION",
        help="fonction ABI devant être présente (répétable)",
    )
    return parseur


def main(argv: list[str] | None = None) -> int:
    args = construire_parseur().parse_args(argv)

    if args.limit <= 0:
        print("ERROR --limit doit etre un entier positif")
        return 2

    source_path = Path(args.source)
    artifact_path = Path(args.artifact)

    try:
        source_bytes = source_path.read_bytes()
    except OSError as erreur:
        print("ERROR lecture source impossible : %s" % ascii_sur(str(erreur)))
        return 2

    try:
        texte_artefact = artifact_path.read_text(encoding="utf-8")
    except OSError as erreur:
        print("ERROR lecture artefact impossible : %s" % ascii_sur(str(erreur)))
        return 2

    rapport = Rapport()

    try:
        artefact = json.loads(texte_artefact)
    except json.JSONDecodeError as erreur:
        rapport.echec("artefact JSON invalide : %s" % erreur)
        print("RESULT FAIL (%d)" % rapport.echecs)
        return 1

    if not isinstance(artefact, dict):
        rapport.echec("artefact JSON : objet attendu")
        print("RESULT FAIL (%d)" % rapport.echecs)
        return 1

    rapport.ok("artefact lu : %s" % artifact_path.name)
    rapport.ok("source lue : %s (%d octets)" % (source_path.name, len(source_bytes)))

    absentes = [cle for cle in CLES_REQUISES if cle not in artefact]
    if absentes:
        rapport.echec("cles manquantes : %s" % ", ".join(absentes))
    else:
        rapport.ok("cles requises presentes")

    bytecode = artefact.get("bytecode_hex")
    if not isinstance(bytecode, str) or not HEX.match(bytecode):
        rapport.echec("bytecode_hex absent ou non hexadecimal")
        octets = None
    else:
        octets = len(bytecode) // 2
        rapport.ok("bytecode hexadecimal : %d octets" % octets)
        declare = artefact.get("bytecode_octets")
        if isinstance(declare, int) and declare != octets:
            rapport.echec(
                "bytecode_octets declare %d, longueur reelle %d" % (declare, octets)
            )
        elif isinstance(declare, int):
            rapport.ok("bytecode_octets coherent (%d)" % declare)

    empreinte = hashlib.sha256(source_bytes).hexdigest()
    empreinte_artefact = artefact.get("source_sha256")
    if not isinstance(empreinte_artefact, str):
        rapport.echec("source_sha256 absent")
    elif empreinte.lower() != empreinte_artefact.lower():
        rapport.echec(
            "artefact perime : source %s != artefact %s"
            % (empreinte[:16], empreinte_artefact[:16])
        )
    else:
        rapport.ok("fraicheur : source %s" % empreinte[:16])

    if octets is None:
        pass
    elif octets == 0:
        rapport.echec("bytecode vide")
    elif octets > args.limit:
        rapport.echec("bytecode %d octets > limite %d" % (octets, args.limit))
    else:
        rapport.ok("taille : %d <= %d octets" % (octets, args.limit))

    abi = artefact.get("abi")
    noms = set()
    if isinstance(abi, list):
        noms = {
            entree.get("name")
            for entree in abi
            if isinstance(entree, dict) and entree.get("type") == "function"
        }
        rapport.ok("abi : %d fonctions" % len(noms))
    else:
        rapport.echec("abi absente ou non tableau")

    manquantes = [nom for nom in args.require if nom not in noms]
    if manquantes:
        rapport.echec("fonctions ABI manquantes : %s" % ", ".join(manquantes))
    elif args.require:
        rapport.ok("fonctions ABI demandees presentes (%d)" % len(args.require))

    source_texte = source_bytes.decode("utf-8", errors="replace").lower()
    for nom, motif in MOTIFS_INTERDITS:
        if re.search(motif, source_texte):
            rapport.echec("motif interdit present : %s" % nom)
    for mot in MOTS_SECRETS:
        if mot in source_texte:
            rapport.echec("mot secret present : %s" % mot)

    if rapport.echecs:
        print("RESULT FAIL (%d)" % rapport.echecs)
        return 1

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
