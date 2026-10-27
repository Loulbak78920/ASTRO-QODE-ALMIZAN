#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verifie une documentation technique contre la passerelle reelle.

Controles en lecture seule : fences equilibrees, liens locaux existants,
blocs Python compilables et couverture des routes de la passerelle.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import unquote

sys.dont_write_bytecode = True

from inventorier_routes import extraire_routes, routes_manquantes


def _configurer_stdout() -> None:
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            try:
                flux.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def extraire_blocs(texte: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Retourne les blocs de code et les erreurs de fences non equilibrees."""
    blocs: List[Dict[str, Any]] = []
    erreurs: List[str] = []
    langue: str | None = None
    debut = 0
    contenu: List[str] = []
    for numero, ligne in enumerate(texte.splitlines(), 1):
        correspondance = re.match(r"^[ \t]*```[ \t]*([^\s`]*)", ligne)
        if correspondance:
            if langue is None:
                langue = correspondance.group(1).lower()
                debut = numero
                contenu = []
            else:
                blocs.append({"langue": langue, "debut": debut, "contenu": "\n".join(contenu)})
                langue = None
            continue
        if langue is not None:
            contenu.append(ligne)
    if langue is not None:
        erreurs.append(f"bloc non ferme ouvert ligne {debut} ({langue or 'sans langage'})")
    return blocs, erreurs


def texte_hors_blocs(texte: str) -> str:
    """Blanchit les blocs de code pour ne pas y chercher de liens Markdown."""
    sorties: List[str] = []
    dedans = False
    for ligne in texte.splitlines():
        if re.match(r"^[ \t]*```", ligne):
            dedans = not dedans
            sorties.append("")
            continue
        sorties.append("" if dedans else ligne)
    return "\n".join(sorties)


def liens_locaux(texte: str) -> List[str]:
    """Extrait les cibles de liens Markdown qui pointent vers le disque."""
    cibles: List[str] = []
    for correspondance in re.finditer(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", texte):
        cible = correspondance.group(1).strip("<>")
        if re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//|#)", cible):
            continue
        cible = unquote(cible.split("#", 1)[0].split("?", 1)[0])
        if cible:
            cibles.append(cible)
    return cibles


def verifier_liens(texte: str, dossier_doc: Path, racine: Path) -> List[str]:
    manquants: List[str] = []
    for cible in liens_locaux(texte_hors_blocs(texte)):
        chemin = Path(cible)
        if not chemin.is_absolute():
            chemin = dossier_doc / chemin
        elif cible.startswith(("/", "\\")):
            chemin = racine / cible.lstrip("/\\")
        try:
            if not chemin.exists():
                manquants.append(cible)
        except OSError:
            manquants.append(cible)
    return manquants


def verifier_blocs_python(blocs: List[Dict[str, Any]]) -> List[str]:
    erreurs: List[str] = []
    for bloc in blocs:
        if bloc["langue"] not in {"python", "py"} or not bloc["contenu"].strip():
            continue
        try:
            ast.parse(bloc["contenu"], filename=f"<bloc ligne {bloc['debut']}>")
        except SyntaxError as erreur:
            erreurs.append(f"bloc ligne {bloc['debut']}: {erreur.msg} (ligne {erreur.lineno})")
    return erreurs


def main(argv: List[str] | None = None) -> int:
    _configurer_stdout()
    analyseur = argparse.ArgumentParser(
        description="Verifie une documentation Markdown contre une passerelle Python stdlib."
    )
    analyseur.add_argument("--gateway", required=True, help="Fichier Python de la passerelle")
    analyseur.add_argument(
        "--docs", action="append", default=[], metavar="CHEMIN",
        help="Fichier Markdown ou dossier (repetable)",
    )
    analyseur.add_argument("--root", default="", help="Racine des liens absolus (defaut: dossier de la passerelle)")
    analyseur.add_argument("--allow-missing", action="store_true", help="Tolere les routes absentes")
    analyseur.add_argument("--skip-python", action="store_true", help="Ne pas compiler les blocs Python")
    analyseur.add_argument("--json", action="store_true", help="Sortie JSON")
    arguments = analyseur.parse_args(argv)

    passerelle = Path(arguments.gateway)
    if not passerelle.is_file():
        print(f"RESULT FAIL passerelle introuvable: {passerelle}")
        return 2
    if not arguments.docs:
        print("RESULT FAIL aucun document fourni (--docs)")
        return 2
    racine = Path(arguments.root) if arguments.root else passerelle.parent

    fichiers: List[Path] = []
    for entree in arguments.docs:
        chemin = Path(entree)
        if chemin.is_dir():
            fichiers.extend(sorted(chemin.rglob("*.md")))
        elif chemin.is_file():
            fichiers.append(chemin)
        else:
            print(f"RESULT FAIL document introuvable: {chemin}")
            return 2
    if not fichiers:
        print("RESULT FAIL aucun fichier Markdown trouve")
        return 2

    try:
        texte_passerelle = passerelle.read_text(encoding="utf-8")
        routes = extraire_routes(texte_passerelle, str(passerelle))
    except (OSError, UnicodeDecodeError, SyntaxError) as erreur:
        print(f"RESULT FAIL passerelle illisible: {erreur}")
        return 2

    rapport: List[Dict[str, Any]] = []
    echecs: List[str] = []
    corpus: List[str] = []
    for fichier in fichiers:
        try:
            texte = fichier.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as erreur:
            echecs.append(f"{fichier}: lecture impossible ({erreur})")
            continue
        corpus.append(texte)
        blocs, erreurs_fences = extraire_blocs(texte)
        erreurs_python = [] if arguments.skip_python else verifier_blocs_python(blocs)
        liens_ko = verifier_liens(texte, fichier.parent, racine)
        for erreur in erreurs_fences + erreurs_python:
            echecs.append(f"{fichier.name}: {erreur}")
        for lien in liens_ko:
            echecs.append(f"{fichier.name}: lien local absent ({lien})")
        rapport.append(
            {
                "document": fichier.name,
                "fences": len(blocs) * 2,
                "blocs_python": sum(1 for b in blocs if b["langue"] in {"python", "py"}),
                "liens_locaux": len(liens_locaux(texte_hors_blocs(texte))),
                "liens_absents": liens_ko,
                "erreurs_fences": erreurs_fences,
                "erreurs_python": erreurs_python,
            }
        )

    manquantes = routes_manquantes(routes, "\n".join(corpus))
    total_routes = sum(len(chemins) for chemins in routes.values())
    if manquantes and not arguments.allow_missing:
        echecs.extend(f"route absente du corpus: {methode} {chemin}" for methode, chemin in manquantes)
    if total_routes == 0:
        echecs.append("aucune route extraite de la passerelle")

    resultat = "FAIL" if echecs else "PASS"
    if arguments.json:
        print(
            json.dumps(
                {
                    "passerelle": str(passerelle),
                    "routes_uniques": total_routes,
                    "routes_absentes": [
                        {"methode": methode, "chemin": chemin} for methode, chemin in manquantes
                    ],
                    "documents": rapport,
                    "erreurs": echecs,
                    "resultat": resultat,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"passerelle={passerelle}")
        print(f"routes uniques: {total_routes}")
        print(f"routes absentes du corpus: {len(manquantes)}")
        for methode, chemin in manquantes:
            print(f"  MANQUANTE {methode} {chemin}")
        for entree in rapport:
            print(
                f"  {entree['document']}: fences={entree['fences']} "
                f"liens_locaux={entree['liens_locaux']} liens_absents={len(entree['liens_absents'])} "
                f"blocs_python={entree['blocs_python']}"
            )
        for erreur in echecs:
            print(f"  ERREUR {erreur}")
        print(f"RESULT {resultat}")

    return 0 if resultat == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
