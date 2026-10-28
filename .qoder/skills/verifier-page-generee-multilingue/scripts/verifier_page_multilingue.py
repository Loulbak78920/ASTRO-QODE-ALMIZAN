# -*- coding: utf-8 -*-
"""Assertions structurelles sur des pages HTML generees en plusieurs langues.

Usage :
    py -3 -B scripts/verifier_page_multilingue.py \
        --page fr=web_cloud/oeuvre_universelle.html \
        --page en=web_cloud/oeuvre_universelle_en.html \
        --page ar=web_cloud/oeuvre_universelle_ar.html \
        --cartes 19

Sortie ASCII uniquement (console Windows cp1252), verdict final
`RESULT: PASS` ou `RESULT: FAIL`, code retour 0 (PASS), 1 (FAIL) ou 2 (usage).
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Dict, List, Tuple

DIRS_PAR_DEFAUT = {"ar": "rtl"}
CLASSE_CARTE = re.compile(r"class\s*=\s*[\"']carte[\"']")
CLASSE_EQUATION = re.compile(r"class\s*=\s*[\"']equation[\"']")
HREFLANG = re.compile(r"hreflang\s*=\s*[\"']([^\"']+)[\"']")
BALISE_HTML = re.compile(r"<html\b[^>]*>", re.IGNORECASE)
H1 = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
BALISE = re.compile(r"<[^>]+>")


def ascii_sur(valeur: object) -> str:
    return str(valeur).encode("ascii", "backslashreplace").decode("ascii")


def attribut(balise: str, nom: str) -> str | None:
    motif = r"(?<![-\w])" + re.escape(nom) + r"\s*=\s*[\"']([^\"']*)[\"']"
    trouve = re.search(motif, balise, re.IGNORECASE)
    return trouve.group(1) if trouve else None


def h1_texte(document: str) -> str:
    trouve = H1.search(document)
    if not trouve:
        return ""
    texte = unescape(BALISE.sub("", trouve.group(1)))
    return re.sub(r"\s+", " ", texte).strip()


def verifier_page(
    langue: str,
    chemin: Path,
    cartes_attendues: int,
    langues_attendues: List[str],
    dir_attendu: str,
    exiger_x_default: bool,
) -> Tuple[List[Tuple[bool, str, str]], str]:
    controles: List[Tuple[bool, str, str]] = []

    def noter(ok: bool, cle: str, detail: str) -> None:
        controles.append((ok, cle, detail))

    if not chemin.is_file():
        noter(False, "fichier", "absent path=" + ascii_sur(chemin))
        return controles, ""
    octets = chemin.read_bytes()
    empreinte = hashlib.sha256(octets).hexdigest()
    noter(len(octets) > 0, "taille", "octets=" + str(len(octets)))
    try:
        html = octets.decode("utf-8")
    except UnicodeDecodeError as erreur:
        noter(False, "utf8", "erreur=" + ascii_sur(erreur.reason) + " offset=" + str(erreur.start))
        return controles, empreinte
    noter(True, "utf8", "octets_valides")

    balise = BALISE_HTML.search(html)
    if not balise:
        noter(False, "html", "balise_absente")
    else:
        lang = attribut(balise.group(0), "lang")
        direction = attribut(balise.group(0), "dir")
        noter(lang == langue, "lang", "observe=" + ascii_sur(lang) + " attendu=" + langue)
        noter(
            direction == dir_attendu,
            "dir",
            "observe=" + ascii_sur(direction) + " attendu=" + dir_attendu,
        )

    nb_cartes = len(CLASSE_CARTE.findall(html))
    noter(nb_cartes == cartes_attendues, "cartes", "observe=" + str(nb_cartes) + " attendu=" + str(cartes_attendues))

    nb_equations = len(CLASSE_EQUATION.findall(html))
    noter(
        nb_equations >= cartes_attendues,
        "equation",
        "observe=" + str(nb_equations) + " minimum=" + str(cartes_attendues),
    )

    hreflangs = set(HREFLANG.findall(html))
    manquants = [code for code in langues_attendues if code not in hreflangs]
    noter(
        not manquants,
        "hreflang",
        "observe=" + ascii_sur(",".join(sorted(hreflangs))) + " manquants=" + ascii_sur(",".join(manquants) or "-"),
    )
    if exiger_x_default:
        noter(
            "x-default" in hreflangs,
            "x-default",
            "observe=" + ("present" if "x-default" in hreflangs else "absent"),
        )

    titre = h1_texte(html)
    noter(len(titre) >= 2, "h1", "longueur=" + str(len(titre)) + " texte=" + ascii_sur(titre[:80]))

    doubles = [motif for motif in ("&amp;#", "&amp;amp;") if motif in html]
    noter(
        not doubles,
        "entites_double_encodees",
        "motifs=" + ascii_sur(",".join(doubles) or "aucun"),
    )
    return controles, empreinte


def main(argv: List[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Assertions structurelles sur des pages HTML multilingues generees."
    )
    analyseur.add_argument(
        "--page",
        action="append",
        required=True,
        metavar="LANGUE=CHEMIN",
        help="page a verifier, repetable (ex. fr=web_cloud/page.html)",
    )
    analyseur.add_argument(
        "--cartes",
        type=int,
        default=19,
        metavar="N",
        help="nombre exact de cartes attendu (defaut 19)",
    )
    analyseur.add_argument(
        "--dir",
        action="append",
        default=[],
        metavar="LANGUE=DIRECTION",
        help="direction attendue, repetable (defaut ltr, ar=rtl)",
    )
    analyseur.add_argument(
        "--sans-x-default",
        action="store_true",
        help="ne pas exiger la liaison hreflang x-default",
    )
    arguments = analyseur.parse_args(argv)

    pages: Dict[str, Path] = {}
    for element in arguments.page:
        if "=" not in element:
            print("FAIL page= argument_invalide attendu=LANGUE=CHEMIN recu=" + ascii_sur(element))
            print("RESULT: FAIL")
            return 2
        langue, chemin = element.split("=", 1)
        langue = langue.strip()
        chemin = chemin.strip()
        if not langue or not chemin:
            print("FAIL page= argument_vide recu=" + ascii_sur(element))
            print("RESULT: FAIL")
            return 2
        if langue in pages:
            print("FAIL page= langue_dupliquee langue=" + ascii_sur(langue))
            print("RESULT: FAIL")
            return 2
        pages[langue] = Path(chemin)
    if not pages:
        print("FAIL page= aucune_page_fournie")
        print("RESULT: FAIL")
        return 2

    directions = dict(DIRS_PAR_DEFAUT)
    langues_dir: set[str] = set()
    for element in arguments.dir:
        if "=" not in element:
            print("FAIL dir= argument_invalide attendu=LANGUE=DIRECTION recu=" + ascii_sur(element))
            print("RESULT: FAIL")
            return 2
        langue, direction = element.split("=", 1)
        langue = langue.strip()
        direction = direction.strip()
        if not langue or not direction:
            print("FAIL dir= argument_vide recu=" + ascii_sur(element))
            print("RESULT: FAIL")
            return 2
        if langue in langues_dir:
            print("FAIL dir= langue_dupliquee langue=" + ascii_sur(langue))
            print("RESULT: FAIL")
            return 2
        langues_dir.add(langue)
        directions[langue] = direction

    langues = list(pages)
    echecs = 0
    for langue, chemin in pages.items():
        controles, empreinte = verifier_page(
            langue,
            chemin,
            arguments.cartes,
            langues,
            directions.get(langue, "ltr"),
            not arguments.sans_x_default,
        )
        try:
            mtime = datetime.fromtimestamp(chemin.stat().st_mtime).astimezone().isoformat(
                timespec="seconds"
            )
        except OSError:
            mtime = "-"
        print(
            "page " + langue
            + " path=" + ascii_sur(chemin.resolve())
            + " sha256=" + (empreinte or "-")
            + " mtime=" + mtime
        )
        for ok, cle, detail in controles:
            if not ok:
                echecs += 1
            print("  " + ("OK " if ok else "FAIL") + " " + cle + " " + detail)

    print("RESULT: PASS" if echecs == 0 else "RESULT: FAIL")
    return 0 if echecs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
