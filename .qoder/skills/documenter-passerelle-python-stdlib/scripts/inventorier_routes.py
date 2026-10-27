#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventorie les routes d'une passerelle Python stdlib (http.server).

Analyse statique (AST), lecture seule : le serveur n'est jamais demarre.
Compte chaque motif de route, alias compris, et peut verifier la couverture
d'un ou plusieurs fichiers Markdown.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

METHODES = {
    "do_GET": "GET",
    "do_POST": "POST",
    "do_PUT": "PUT",
    "do_PATCH": "PATCH",
    "do_DELETE": "DELETE",
    "do_HEAD": "HEAD",
}

VARIABLES_ROUTE = ("chemin", "path", "route", "endpoint")


def _configurer_stdout() -> None:
    for flux in (sys.stdout, sys.stderr):
        if hasattr(flux, "reconfigure"):
            try:
                flux.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def _chaines(noeud: ast.AST) -> List[str]:
    """Extrait les chaines d'un litteral, d'une liste, d'un tuple ou d'un set."""
    if isinstance(noeud, ast.Constant) and isinstance(noeud.value, str):
        return [noeud.value]
    if isinstance(noeud, (ast.List, ast.Tuple, ast.Set)):
        valeurs = []
        for element in noeud.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                valeurs.append(element.value)
        return valeurs
    return []


def _variable_route(fonction: ast.AST) -> str:
    """Detecte la variable affectee depuis un attribut .path (ex. chemin)."""
    for noeud in ast.walk(fonction):
        if isinstance(noeud, ast.Assign) and isinstance(noeud.value, ast.Attribute):
            if noeud.value.attr == "path":
                for cible in noeud.targets:
                    if isinstance(cible, ast.Name):
                        return cible.id
    return "chemin"


def _motifs_test(test: ast.AST, variable: str) -> List[str]:
    """Retourne les chemins compares a la variable de route (==, in, or)."""
    valeurs: List[str] = []
    if isinstance(test, ast.BoolOp):
        for valeur in test.values:
            valeurs.extend(_motifs_test(valeur, variable))
        return valeurs
    if not isinstance(test, ast.Compare):
        return valeurs
    if not (isinstance(test.left, ast.Name) and test.left.id == variable):
        return valeurs
    for operateur, comparateur in zip(test.ops, test.comparators):
        if isinstance(operateur, (ast.In, ast.Eq)):
            valeurs.extend(_chaines(comparateur))
    return valeurs


def extraire_routes(source: str, nom_fichier: str = "<source>") -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """Retourne {methode: {chemin: [occurrences]}} a partir du code source."""
    arbre = ast.parse(source, filename=nom_fichier)
    routes: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        methode = METHODES.get(noeud.name)
        if not methode:
            continue
        variable = _variable_route(noeud)
        for sous_noeud in ast.walk(noeud):
            if not isinstance(sous_noeud, ast.If):
                continue
            for chemin in _motifs_test(sous_noeud.test, variable):
                if not chemin.startswith("/"):
                    continue
                occurrences = routes.setdefault(methode, {}).setdefault(chemin, [])
                occurrence = {"ligne": getattr(sous_noeud, "lineno", 0), "fonction": noeud.name}
                if occurrence not in occurrences:
                    occurrences.append(occurrence)
    return routes


def compter(routes: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> Dict[str, int]:
    return {methode: len(chemins) for methode, chemins in sorted(routes.items())}


def jetons_code(texte: str) -> Set[str]:
    """Extrait les chemins cites en code inline, sans requete ni ancre."""
    jetons: Set[str] = set()
    for correspondance in re.finditer(r"`([^`\n]+)`", texte):
        jeton = correspondance.group(1).strip()
        if not jeton.startswith("/"):
            continue
        jeton = re.split(r"[?#\s]", jeton, maxsplit=1)[0]
        jeton = jeton.rstrip(".,;:)")
        if jeton:
            jetons.add(jeton)
    return jetons


def routes_manquantes(
    routes: Dict[str, Dict[str, List[Dict[str, Any]]]], texte: str
) -> List[Tuple[str, str]]:
    """Liste les routes absentes de la documentation fournie."""
    jetons = jetons_code(texte)
    manquantes: List[Tuple[str, str]] = []
    for methode, chemins in sorted(routes.items()):
        for chemin in sorted(chemins):
            if chemin in jetons:
                continue
            if chemin != "/" and re.search(re.escape(chemin) + r"(?![A-Za-z0-9_\-/])", texte):
                continue
            manquantes.append((methode, chemin))
    return manquantes


def _charger_texte(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    _configurer_stdout()
    analyseur = argparse.ArgumentParser(
        description="Inventorie les routes d'une passerelle Python stdlib (lecture seule)."
    )
    analyseur.add_argument("source", help="Fichier Python de la passerelle")
    analyseur.add_argument(
        "--doc",
        action="append",
        default=[],
        metavar="FICHIER",
        help="Document Markdown a verifier (repetable)",
    )
    analyseur.add_argument("--json", action="store_true", help="Sortie JSON")
    analyseur.add_argument(
        "--allow-missing",
        action="store_true",
        help="Ne pas echouer si des routes manquent dans la documentation",
    )
    arguments = analyseur.parse_args(argv)

    source = Path(arguments.source)
    if not source.is_file():
        print(f"RESULT FAIL source introuvable: {source}")
        return 2
    try:
        texte_source = _charger_texte(source)
    except (OSError, UnicodeDecodeError) as erreur:
        print(f"RESULT FAIL lecture impossible: {erreur}")
        return 2
    try:
        routes = extraire_routes(texte_source, str(source))
    except SyntaxError as erreur:
        print(f"RESULT FAIL syntaxe Python invalide: {erreur}")
        return 2

    total = sum(len(chemins) for chemins in routes.values())
    if total == 0:
        print("RESULT FAIL aucune route extraite (verifier do_GET/do_POST et la variable de route)")
        return 1

    manquantes: List[Tuple[str, str]] = []
    corpus = ""
    for chemin_doc in arguments.doc:
        fichier_doc = Path(chemin_doc)
        if not fichier_doc.is_file():
            print(f"RESULT FAIL document introuvable: {fichier_doc}")
            return 2
        try:
            corpus += "\n" + _charger_texte(fichier_doc)
        except (OSError, UnicodeDecodeError) as erreur:
            print(f"RESULT FAIL lecture document impossible: {erreur}")
            return 2
    if arguments.doc:
        manquantes = routes_manquantes(routes, corpus)

    if arguments.json:
        charge = {
            "source": str(source),
            "total_routes_uniques": total,
            "par_methode": compter(routes),
            "routes": [
                {"methode": methode, "chemin": chemin, "occurrences": occurrences}
                for methode, chemins in sorted(routes.items())
                for chemin, occurrences in sorted(chemins.items())
            ],
            "documents": arguments.doc,
            "routes_manquantes": [
                {"methode": methode, "chemin": chemin} for methode, chemin in manquantes
            ],
            "resultat": "FAIL" if manquantes and not arguments.allow_missing else "OK",
        }
        print(json.dumps(charge, ensure_ascii=False, indent=2))
    else:
        print(f"source={source}")
        print(f"routes uniques: {total}")
        for methode, nombre in compter(routes).items():
            print(f"  {methode}: {nombre}")
        if arguments.doc:
            print(f"documents verifies: {len(arguments.doc)}")
            print(f"routes absentes du doc: {len(manquantes)}")
            for methode, chemin in manquantes:
                print(f"  MANQUANTE {methode} {chemin}")
        resultat = "FAIL" if manquantes and not arguments.allow_missing else "OK"
        print(f"RESULT {resultat}")

    return 1 if manquantes and not arguments.allow_missing else 0


if __name__ == "__main__":
    sys.exit(main())
