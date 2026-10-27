#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifie un manifeste SHA-256/Merkle sans circularite (lecture seule).

Controles : empreintes, EXTRA par globs, racine recalculee, porteurs concordants
et non scelles. Sortie ASCII, codes 0/1/2. Aucun fichier n'est ecrit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

EXCLUSIONS_DEFAUT = {".git", "__pycache__", "node_modules", ".qoder"}
SUFFIXES_IGNORES = {".pyc", ".log", ".tmp"}
MAX_LIGNES = 20


def ascii_text(valeur: object) -> str:
    return str(valeur).encode("ascii", "backslashreplace").decode("ascii")


def echec(message: str) -> int:
    print("ERREUR " + ascii_text(message))
    print("RESULT FAIL")
    return 2


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as flux:
        for bloc in iter(lambda: flux.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def merkle(empreintes: Iterable[str]) -> str:
    couche = sorted(empreintes)
    if not couche:
        return hashlib.sha256(b"").hexdigest()
    while len(couche) > 1:
        if len(couche) % 2:
            couche.append(couche[-1])
        couche = [
            hashlib.sha256(bytes.fromhex(a) + bytes.fromhex(b)).hexdigest()
            for a, b in zip(couche[::2], couche[1::2])
        ]
    return couche[0]


def normaliser(chemin: str) -> str:
    while chemin.startswith("./"):
        chemin = chemin[2:]
    return chemin.replace("\\", "/")


def dans_racine(racine: Path, relatif: str) -> Path:
    candidat = (racine / relatif).resolve()
    candidat.relative_to(racine)
    return candidat


def chemins_globs(racine: Path, motifs: List[str], exclusions: Set[str]) -> Set[str]:
    trouves: Set[str] = set()
    for motif in motifs:
        for chemin in racine.glob(motif):
            if not chemin.is_file():
                continue
            relatif = chemin.relative_to(racine).as_posix()
            if any(part in exclusions for part in relatif.split("/")):
                continue
            if chemin.suffix.lower() in SUFFIXES_IGNORES:
                continue
            trouves.add(relatif)
    return trouves


def charger(chemin: Path) -> Tuple[Dict[str, Any], str]:
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "manifeste absent"
    except (OSError, ValueError) as exc:
        return {}, "manifeste illisible: " + str(exc)
    if not isinstance(donnees, dict):
        return {}, "manifeste: la racine JSON n'est pas un objet"
    fichiers = donnees.get("fichiers")
    if not isinstance(fichiers, list):
        return {}, "manifeste: cle 'fichiers' absente ou invalide"
    for entree in fichiers:
        if not isinstance(entree, dict) or not isinstance(entree.get("chemin"), str) or not isinstance(entree.get("sha256"), str):
            return {}, "manifeste: entree de fichier invalide"
    return donnees, ""


def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Verifie un manifeste SHA-256/Merkle sans circularite (lecture seule).")
    p.add_argument("--manifest", required=True, help="manifeste JSON")
    p.add_argument("--racine", required=True, help="racine des chemins relatifs")
    p.add_argument("--glob", action="append", default=[], dest="globs", help="motif couvert, relatif a la racine (repetable)")
    p.add_argument("--porteur-de-racine", action="append", default=[], dest="porteurs", help="fichier qui doit afficher la racine sans etre scelle (repetable)")
    return p


def signaler(problemes: List[str], code: str, relatif: str = "") -> None:
    problemes.append(code + (" " + relatif if relatif else ""))


def main(argv: List[str] | None = None) -> int:
    options = construire_parseur().parse_args(argv)
    racine = Path(options.racine).resolve()
    if not racine.is_dir():
        return echec("racine introuvable: " + str(options.racine))
    manifeste_chemin = Path(options.manifest)
    if not manifeste_chemin.is_absolute():
        manifeste_chemin = racine / manifeste_chemin
    manifeste, erreur = charger(manifeste_chemin)
    if erreur:
        return echec(erreur)

    declarations = manifeste["fichiers"]
    liste = [normaliser(entree["chemin"]) for entree in declarations]
    stockees = {normaliser(e["chemin"]): e["sha256"].lower() for e in declarations}
    declaree = str(manifeste.get("racine_merkle_sha256", "")).lower()
    if not declaree:
        return echec("manifeste: racine_merkle_sha256 absente")

    problemes: List[str] = []
    if len(set(liste)) != len(liste):
        signaler(problemes, "LISTE_DUPLIQUEE")
    nb_declare = manifeste.get("nb_fichiers")
    if isinstance(nb_declare, int) and nb_declare != len(declarations):
        signaler(problemes, "NB_FICHIERS_DECLARE " + str(nb_declare) + " != " + str(len(declarations)))
    observees: Dict[str, str] = {}
    for relatif in liste:
        try:
            fichier = dans_racine(racine, relatif)
        except ValueError:
            signaler(problemes, "CHEMIN_HORS_RACINE", relatif)
            observees[relatif] = stockees[relatif]
            continue
        if not fichier.is_file():
            signaler(problemes, "ABSENT", relatif)
            observees[relatif] = stockees[relatif]
            continue
        actuelle = sha256_fichier(fichier)
        observees[relatif] = actuelle
        if actuelle != stockees[relatif]:
            signaler(problemes, "MODIFIE", relatif)

    couverts: Set[str] = set()
    if options.globs:
        couverts = chemins_globs(racine, options.globs, EXCLUSIONS_DEFAUT)
        for relatif in sorted(couverts - set(liste)):
            signaler(problemes, "EXTRA", relatif)

    calculee = merkle(observees[relatif] for relatif in liste)
    if calculee != declaree:
        signaler(problemes, "RACINE_DIVERGENTE")

    print("FILES " + str(len(declarations)))
    print("COUVERTS " + (str(len(couverts)) if options.globs else "na"))
    print("RACINE_MANIFESTE " + declaree)
    print("RACINE_CALCULEE " + calculee)

    for brut in options.porteurs:
        relatif = normaliser(brut)
        if relatif in set(liste):
            signaler(problemes, "PORTEUR_SCELLE", relatif)
        try:
            fichier = dans_racine(racine, relatif)
        except ValueError:
            signaler(problemes, "PORTEUR_HORS_RACINE", relatif)
            continue
        if not fichier.is_file():
            signaler(problemes, "PORTEUR_ABSENT", relatif)
            continue
        if declaree in fichier.read_text(encoding="utf-8", errors="replace").lower():
            print("RACINE_FICHIER " + ascii_text(relatif) + " MATCH")
        else:
            print("RACINE_FICHIER " + ascii_text(relatif) + " DIVERGENCE")
            signaler(problemes, "PORTEUR_DIVERGENT", relatif)

    for ligne in problemes[:MAX_LIGNES]:
        print("FAIL " + ascii_text(ligne))
    if len(problemes) > MAX_LIGNES:
        print("... " + str(len(problemes) - MAX_LIGNES) + " autre(s) constat(s)")
    if problemes:
        print("RESULT FAIL (" + str(len(problemes)) + ")")
        return 1
    print("RESULT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
