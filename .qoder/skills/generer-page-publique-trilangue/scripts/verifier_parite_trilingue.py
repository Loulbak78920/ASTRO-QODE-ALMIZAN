# -*- coding: utf-8 -*-
"""Controle de parite d'une page publique generee en plusieurs langues.

Lit le generateur par AST (aucune execution, aucun effet de bord) et les
pages HTML produites, puis verifie les invariants de generation :
parite des cles du dictionnaire, lang/dir, canonique, alternates hreflang et
x-default, selecteur de langues, titres d'equations, absence de residus d'une
autre langue, figure neutre, signatures PDF et PNG.

Usage :
    py -3 -B scripts/verifier_parite_trilingue.py \
        --racine "ASTRO-Q°ODE_SYSTEME" \
        --generateur "oeuvre_universelle/generer_page_riemann.py"

Sortie ASCII uniquement, une ligne OK/FAIL par controle, verdict final
`RESULT: PASS` ou `RESULT: FAIL`.
Codes retour : 0 (PASS), 1 (FAIL), 2 (usage ou generateur illisible).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import re
import sys
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

CLEFS_STRUCTURANTES = (
    "lang",
    "dir",
    "locale",
    "titre",
    "description",
    "og_titre",
    "nav",
    "h1",
    "lead",
    "warn_titre",
    "warn_corps",
    "eq_titres",
    "actions",
    "note_pdf",
    "pied",
)

BALISE_HTML = re.compile(r"<html\b[^>]*>", re.IGNORECASE)
BALISE_LINK = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
BALISE_A = re.compile(r"<a\b[^>]*>.*?</a>", re.IGNORECASE | re.DOTALL)
SPAN_SELECTEUR = re.compile(
    r"<span\s+class=(['\"])langues\1>(.*?)</span>", re.IGNORECASE | re.DOTALL
)
SVG = re.compile(r"<svg\b.*?</svg>", re.IGNORECASE | re.DOTALL)
EQ_TITRE = re.compile(r"""class\s*=\s*["']eq-titre["']""", re.IGNORECASE)
EQ_BLOC = re.compile(r"""<div\s+class\s*=\s*["']eq(?:["'\s])""", re.IGNORECASE)
ARABE = re.compile(r"[\u0600-\u06FF]")


def ascii_sur(valeur: object) -> str:
    return str(valeur).encode("ascii", "backslashreplace").decode("ascii")


def empreinte(octets: bytes) -> str:
    return hashlib.sha256(octets).hexdigest()


class Controles:
    def __init__(self) -> None:
        self.echecs = 0
        self.total = 0

    def noter(self, ok: bool, cle: str, detail: str = "") -> None:
        self.total += 1
        if not ok:
            self.echecs += 1
        ligne = ("OK   " if ok else "FAIL ") + cle
        if detail:
            ligne += " " + detail
        print(ligne)


def attribut(balise: str, nom: str) -> Optional[str]:
    motif = r"(?<![-\w])" + re.escape(nom) + r"\s*=\s*(['\"])(.*?)\1"
    trouve = re.search(motif, balise, re.IGNORECASE | re.DOTALL)
    return trouve.group(2) if trouve else None


def litteral(noeud: ast.AST) -> Any:
    try:
        return ast.literal_eval(noeud)
    except (ValueError, SyntaxError, TypeError):
        return None


def lire_generateur(chemin: Path) -> Tuple[Dict[str, Any], Dict[str, ast.AST]]:
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    valeurs: Dict[str, Any] = {}
    noeuds: Dict[str, ast.AST] = {}
    for instruction in arbre.body:
        cible: Optional[str] = None
        valeur: Optional[ast.AST] = None
        if (
            isinstance(instruction, ast.Assign)
            and len(instruction.targets) == 1
            and isinstance(instruction.targets[0], ast.Name)
        ):
            cible = instruction.targets[0].id
            valeur = instruction.value
        elif (
            isinstance(instruction, ast.AnnAssign)
            and isinstance(instruction.target, ast.Name)
            and instruction.value is not None
        ):
            cible = instruction.target.id
            valeur = instruction.value
        if cible is None or valeur is None:
            continue
        noeuds[cible] = valeur
        contenu = litteral(valeur)
        if contenu is not None:
            valeurs[cible] = contenu
    return valeurs, noeuds


def nom_fichier(noeud: ast.AST, suffixe: str) -> Optional[str]:
    candidats = [
        constante.value
        for constante in ast.walk(noeud)
        if isinstance(constante, ast.Constant)
        and isinstance(constante.value, str)
        and constante.value.lower().endswith(suffixe)
    ]
    return candidats[-1] if candidats else None


def noms_pages(noeud: Optional[ast.AST]) -> Dict[str, str]:
    resultat: Dict[str, str] = {}
    if not isinstance(noeud, ast.Dict):
        return resultat
    for cle, valeur in zip(noeud.keys, noeud.values):
        langue = litteral(cle) if cle is not None else None
        nom = nom_fichier(valeur, ".html")
        if isinstance(langue, str) and nom:
            resultat[langue] = nom
    return resultat


def meme_url(observe: str, attendu: str) -> bool:
    return observe == attendu or observe.rstrip("/") == attendu.rstrip("/")


def present(texte: str, page: str) -> bool:
    return texte in page or escape(texte, quote=True) in page


def regle_rtl_ltr(css: str, selecteur: str) -> bool:
    motif = (
        r"html\[dir=(['\"])rtl\1\][^{}]*"
        + re.escape(selecteur)
        + r"[^{}]*\{[^}]*direction\s*:\s*ltr"
    )
    return re.search(motif, css, re.IGNORECASE) is not None


def alternates(page: str) -> List[Tuple[str, str]]:
    resultat: List[Tuple[str, str]] = []
    for balise in BALISE_LINK.findall(page):
        if (attribut(balise, "rel") or "").lower() != "alternate":
            continue
        code = attribut(balise, "hreflang")
        href = attribut(balise, "href")
        if code and href:
            resultat.append((code, href))
    return resultat


def canonique(page: str) -> Optional[str]:
    for balise in BALISE_LINK.findall(page):
        if (attribut(balise, "rel") or "").lower() == "canonical":
            return attribut(balise, "href")
    return None


def liens_langues(page: str) -> Optional[List[Tuple[str, str, bool]]]:
    bloc = SPAN_SELECTEUR.search(page)
    if not bloc:
        return None
    liens: List[Tuple[str, str, bool]] = []
    for balise in BALISE_A.findall(bloc.group(2)):
        classes = (attribut(balise, "class") or "").split()
        if "langue" not in classes:
            continue
        liens.append(
            (
                attribut(balise, "hreflang") or "",
                attribut(balise, "href") or "",
                "on" in classes,
            )
        )
    return liens


def verifier_dictionnaire(
    controles: Controles,
    valeurs: Dict[str, Any],
) -> Tuple[List[str], Dict[str, str], Dict[str, Dict[str, Any]]]:
    langues = list(valeurs["LANGUES"])
    chemins = dict(valeurs["CHEMINS"])
    dictionnaire = dict(valeurs["T"])

    controles.noter(len(langues) >= 2, "langues_declarees", "n=" + str(len(langues)))
    controles.noter(
        set(dictionnaire) == set(langues),
        "dictionnaire_langues",
        "observe=" + ",".join(sorted(dictionnaire)) + " attendu=" + ",".join(sorted(langues)),
    )
    controles.noter(
        set(chemins) == set(langues),
        "chemins_langues",
        "observe=" + ",".join(sorted(chemins)),
    )

    reference = (
        set(dictionnaire[langues[0]])
        if langues and langues[0] in dictionnaire
        else set()
    )
    for langue in langues:
        if langue not in dictionnaire:
            continue
        controles.noter(
            set(dictionnaire[langue]) == reference,
            "cles_parite",
            "langue=" + langue
            + " manquantes=" + (",".join(sorted(reference - set(dictionnaire[langue]))) or "-")
            + " superflues=" + (",".join(sorted(set(dictionnaire[langue]) - reference)) or "-"),
        )
        absentes = [cle for cle in CLEFS_STRUCTURANTES if cle not in dictionnaire[langue]]
        controles.noter(
            not absentes,
            "cles_structurantes",
            "langue=" + langue + " absentes=" + (",".join(absentes) or "-"),
        )
        direction = dictionnaire[langue].get("dir")
        controles.noter(
            direction in ("ltr", "rtl"),
            "direction_declaree",
            "langue=" + langue + " dir=" + ascii_sur(direction),
        )

    for cle in ("nav", "actions", "eq_titres"):
        longueurs = {
            langue: len(dictionnaire[langue].get(cle) or [])
            for langue in langues
            if langue in dictionnaire
        }
        controles.noter(
            len(set(longueurs.values())) == 1,
            "longueur_" + cle,
            " ".join(langue + "=" + str(n) for langue, n in longueurs.items()),
        )

    controles.noter(
        all(chemins.get(langue) for langue in langues),
        "chemins_non_vides",
        " ".join(langue + "=" + ascii_sur(chemins.get(langue)) for langue in langues),
    )
    return langues, chemins, dictionnaire


def verifier_css(controles: Controles, valeurs: Dict[str, Any], langues: List[str], t: Dict[str, Dict[str, Any]]) -> None:
    css = valeurs.get("CSS") or ""
    controles.noter(bool(css), "css_present", "octets=" + str(len(css)))
    rtl = [langue for langue in langues if (t.get(langue) or {}).get("dir") == "rtl"]
    if not rtl:
        controles.noter(True, "css_rtl_applicable", "aucune_langue_rtl")
        return
    for selecteur in (".formule", "table", "pre", "code"):
        controles.noter(
            regle_rtl_ltr(css, selecteur),
            "css_rtl_ltr",
            "selecteur=" + selecteur,
        )


def verifier_page(
    controles: Controles,
    langue: str,
    chemin: Path,
    langues: List[str],
    chemins: Dict[str, str],
    t: Dict[str, Dict[str, Any]],
    site: str,
) -> None:
    if not chemin.is_file():
        controles.noter(False, "page_absente", "langue=" + langue + " path=" + ascii_sur(chemin))
        return
    octets = chemin.read_bytes()
    controles.noter(len(octets) > 0, "page_taille", "langue=" + langue + " octets=" + str(len(octets)))
    print(
        "page " + langue
        + " path=" + ascii_sur(chemin.resolve())
        + " sha256=" + empreinte(octets)
    )
    try:
        page = octets.decode("utf-8")
    except UnicodeDecodeError as erreur:
        controles.noter(False, "page_utf8", "langue=" + langue + " " + ascii_sur(erreur.reason))
        return
    controles.noter(True, "page_utf8", "langue=" + langue)

    balise = BALISE_HTML.search(page)
    if not balise:
        controles.noter(False, "html_lang", "langue=" + langue + " balise_absente")
    else:
        observe = attribut(balise.group(0), "lang")
        controles.noter(
            observe == langue,
            "html_lang",
            "langue=" + langue + " observe=" + ascii_sur(observe),
        )
        attendu_dir = (t.get(langue) or {}).get("dir", "ltr")
        observe_dir = attribut(balise.group(0), "dir")
        if attendu_dir == "rtl":
            ok_dir = observe_dir == "rtl"
        else:
            ok_dir = observe_dir in (None, "", "ltr")
        controles.noter(
            ok_dir,
            "html_dir",
            "langue=" + langue + " observe=" + ascii_sur(observe_dir) + " attendu=" + attendu_dir,
        )

    canon = canonique(page)
    attendu_canon = site + chemins.get(langue, "")
    controles.noter(
        bool(canon) and meme_url(canon or "", attendu_canon),
        "canonique",
        "langue=" + langue + " observe=" + ascii_sur(canon) + " attendu=" + ascii_sur(attendu_canon),
    )

    liens = alternates(page)
    par_langue: Dict[str, List[str]] = {}
    for code, href in liens:
        par_langue.setdefault(code, []).append(href)
    for code in langues:
        hrefs = par_langue.get(code, [])
        attendu = site + chemins.get(code, "")
        controles.noter(
            len(hrefs) == 1 and meme_url(hrefs[0], attendu),
            "alternate",
            "page=" + langue + " hreflang=" + code
            + " n=" + str(len(hrefs))
            + " href=" + ascii_sur(hrefs[0] if hrefs else "-"),
        )
    x_default = par_langue.get("x-default", [])
    controles.noter(
        len(x_default) == 1 and meme_url(x_default[0], site + chemins.get(langues[0], "")),
        "x_default",
        "page=" + langue + " n=" + str(len(x_default))
        + " href=" + ascii_sur(x_default[0] if x_default else "-"),
    )
    controles.noter(
        len(liens) == len(langues) + 1,
        "alternates_total",
        "page=" + langue + " n=" + str(len(liens)) + " attendu=" + str(len(langues) + 1),
    )

    selecteur = liens_langues(page)
    if selecteur is None:
        controles.noter(False, "selecteur_present", "page=" + langue)
    else:
        controles.noter(
            len(selecteur) == len(langues),
            "selecteur_liens",
            "page=" + langue + " n=" + str(len(selecteur)),
        )
        actifs = [lien for lien in selecteur if lien[2]]
        controles.noter(
            len(actifs) == 1,
            "selecteur_actif",
            "page=" + langue + " n=" + str(len(actifs)),
        )
        controles.noter(
            set(lien[0] for lien in selecteur) == set(langues),
            "selecteur_hreflang",
            "page=" + langue + " " + ",".join(sorted(lien[0] for lien in selecteur)),
        )
        correspondances = {lien[0]: lien[1] for lien in selecteur}
        controles.noter(
            len(correspondances) == len(langues)
            and all(
                meme_url(correspondances.get(code, ""), chemins.get(code, ""))
                for code in langues
            ),
            "selecteur_correspondance",
            "page=" + langue,
        )
        if actifs:
            controles.noter(
                actifs[0][0] == langue,
                "selecteur_courant",
                "page=" + langue + " actif=" + ascii_sur(actifs[0][0]),
            )

    contenu = (t.get(langue) or {})
    h1 = contenu.get("h1", "")
    controles.noter(bool(h1) and present(h1, page), "h1", "langue=" + langue)

    titres_attendus = len(contenu.get("eq_titres") or [])
    titres = len(EQ_TITRE.findall(page))
    blocs = len(EQ_BLOC.findall(page))
    controles.noter(
        titres_attendus > 0 and titres == titres_attendus,
        "equations_titres",
        "langue=" + langue + " observe=" + str(titres) + " attendu=" + str(titres_attendus),
    )
    controles.noter(
        titres_attendus > 0 and blocs >= titres_attendus,
        "equations_blocs",
        "langue=" + langue + " observe=" + str(blocs) + " minimum=" + str(titres_attendus),
    )

    sans_selecteur = SPAN_SELECTEUR.sub("", page)
    for autre in langues:
        if autre == langue:
            continue
        marqueurs = [
            (t.get(autre) or {}).get("h1", ""),
            (t.get(autre) or {}).get("warn_titre", ""),
        ]
        trouves = [marqueur for marqueur in marqueurs if marqueur and present(marqueur, sans_selecteur)]
        controles.noter(
            not trouves,
            "residu_langue",
            "page=" + langue + " residus_de=" + autre + " n=" + str(len(trouves)),
        )

    figures = SVG.findall(page)
    controles.noter(len(figures) > 0, "figure_svg", "langue=" + langue + " n=" + str(len(figures)))
    if figures:
        controles.noter(
            all(ARABE.search(figure) is None for figure in figures),
            "figure_neutre",
            "langue=" + langue,
        )


def verifier_artefact(
    controles: Controles, chemin: Path, cle: str, signature: bytes
) -> None:
    if not chemin.is_file():
        controles.noter(False, cle, "absent=" + ascii_sur(chemin))
        return
    octets = chemin.read_bytes()
    controles.noter(
        len(octets) > 0 and octets.startswith(signature),
        cle,
        "path=" + ascii_sur(chemin) + " octets=" + str(len(octets)),
    )


def main(argv: Optional[List[str]] = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Controle de parite d'une page generee en plusieurs langues."
    )
    analyseur.add_argument("--racine", required=True, help="racine du projet")
    analyseur.add_argument(
        "--generateur", required=True, help="chemin du generateur, relatif a la racine ou absolu"
    )
    analyseur.add_argument(
        "--page",
        action="append",
        default=[],
        metavar="LANGUE=CHEMIN",
        help="surcharge du chemin d'une page, repetable",
    )
    arguments = analyseur.parse_args(argv)

    racine = Path(arguments.racine).expanduser().resolve()
    generateur = Path(arguments.generateur)
    if not generateur.is_absolute():
        generateur = racine / generateur
    if not racine.is_dir():
        print("FAIL usage racine_absente path=" + ascii_sur(racine))
        print("RESULT: FAIL")
        return 2
    if not generateur.is_file():
        print("FAIL usage generateur_absent path=" + ascii_sur(generateur))
        print("RESULT: FAIL")
        return 2
    try:
        valeurs, noeuds = lire_generateur(generateur)
    except SyntaxError as erreur:
        print("FAIL usage generateur_syntaxe " + ascii_sur(erreur))
        print("RESULT: FAIL")
        return 2
    absentes = [cle for cle in ("LANGUES", "CHEMINS", "T", "SITE") if cle not in valeurs]
    if absentes:
        print("FAIL usage constantes_absentes " + ",".join(absentes))
        print("RESULT: FAIL")
        return 2

    surcharges: Dict[str, Path] = {}
    for element in arguments.page:
        if "=" not in element:
            print("FAIL usage page_invalide attendu=LANGUE=CHEMIN recu=" + ascii_sur(element))
            print("RESULT: FAIL")
            return 2
        langue, chemin = element.split("=", 1)
        langue, chemin = langue.strip(), chemin.strip()
        if not langue or not chemin:
            print("FAIL usage page_vide recu=" + ascii_sur(element))
            print("RESULT: FAIL")
            return 2
        if langue in surcharges:
            print("FAIL usage page_dupliquee langue=" + ascii_sur(langue))
            print("RESULT: FAIL")
            return 2
        surcharges[langue] = Path(chemin)

    controles = Controles()
    print(
        "generateur path=" + ascii_sur(generateur.resolve())
        + " sha256=" + empreinte(generateur.read_bytes())
    )

    langues, chemins, t = verifier_dictionnaire(controles, valeurs)
    verifier_css(controles, valeurs, langues, t)

    noms = noms_pages(noeuds.get("PAGES"))
    for langue in langues:
        if langue in surcharges:
            chemin = surcharges[langue]
            if not chemin.is_absolute():
                chemin = racine / chemin
        elif langue in noms:
            chemin = racine / "web_cloud" / noms[langue]
        else:
            print("FAIL usage page_introuvable langue=" + ascii_sur(langue))
            print("RESULT: FAIL")
            return 2
        verifier_page(
            controles, langue, chemin, langues, chemins, t, str(valeurs["SITE"]).rstrip("/")
        )

    for constante, suffixe, cle, signature in (
        ("PDF", ".pdf", "artefact_pdf", b"%PDF"),
        ("FIGURE_PNG", ".png", "artefact_png", b"\x89PNG\r\n\x1a\n"),
    ):
        nom = nom_fichier(noeuds[constante], suffixe) if constante in noeuds else None
        if not nom:
            controles.noter(False, cle + "_declare", "constante " + constante + " absente")
            continue
        verifier_artefact(controles, racine / "web_cloud" / nom, cle, signature)

    print(
        "controles=" + str(controles.total)
        + " echecs=" + str(controles.echecs)
    )
    print("RESULT: PASS" if controles.echecs == 0 else "RESULT: FAIL")
    return 0 if controles.echecs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
