#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verification LECTURE SEULE de l'observateur Triniter (couche 36).

Necessite : Python 3.9+, stdlib uniquement.
N'ecrit rien : pas de bytecode (sys.dont_write_bytecode), pas d'acte,
pas de plan, pas de fichier protege.

Sortie : lignes KEY=VALUE en ASCII, puis RESULT OK ou RESULT FAIL.
Codes de retour : 0 = tout est conforme, 1 = au moins un controle echoue,
2 = argument invalide (argparse).

Usage :
  py -3 -B verifier_observateur_triniter.py
  py -3 -B verifier_observateur_triniter.py --racine "D:/copie/ASTRO-Q°ODE_SYSTEME"
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import csv
import importlib
import traceback
from pathlib import Path
from typing import List, Tuple

RACINE_DEFAUT = Path(r"C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME")

MODULE_MOTEUR = "moteur_triniter_observateur_multimodal_mizan"
CODES_ATTENDUS = ["F0", "F1", "F2", "F3", "G1", "G2", "G3"]
ACTES = [
    "almizan_acte_a243_spectre_plasma_couche_36.json",
    "almizan_acte_a244_resoudre_spectre_plasma.json",
    "almizan_acte_a245_ignorance_spectrale_continue.json",
]


class Rapport:
    def __init__(self) -> None:
        self.controles: List[Tuple[str, bool, str]] = []

    def ajouter(self, cle: str, ok: bool, valeur: str = "") -> None:
        self.controles.append((cle, bool(ok), valeur))

    def ok(self) -> bool:
        return all(ok for _, ok, _ in self.controles)

    def afficher(self) -> None:
        for cle, ok, valeur in self.controles:
            print(f"CHECK_{cle}={'OK' if ok else 'FAIL'}")
            if valeur != "":
                print(f"VALUE_{cle}={valeur}")
        print(f"CONTROLES_OK={sum(1 for _, ok, _ in self.controles if ok)}")
        print(f"CONTROLES_TOTAL={len(self.controles)}")
        print("RESULT " + ("OK" if self.ok() else "FAIL"))


def _lire(chemin: Path) -> str:
    try:
        return chemin.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _presque_egal(a: float, b: float, tolerance: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tolerance


def verifier(racine: Path) -> Rapport:
    r = Rapport()
    r.ajouter("RACINE", racine.is_dir(), str(racine))
    if not racine.is_dir():
        return r

    # 1. Artefacts du dossier
    artefacts = {
        "MOTEUR": racine / "moteur_triniter_observateur_multimodal_mizan.py",
        "COUCHE": racine / "conscience_logique" / "spectre_plasma_couche.py",
        "PAGE": racine / "web_cloud" / "observateur_triniter.html",
        "TESTS": racine / "tests" / "test_spectre_plasma_triniter.py",
        "PASSERELLE": racine / "passerelle_api_vps_mizan.py",
        "SITEMAP": racine / "web_cloud" / "sitemap.xml",
        "CSV": racine.parent / "TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv",
    }
    for cle, chemin in artefacts.items():
        r.ajouter(cle, chemin.is_file(), chemin.name)

    # 2. Export de la couche
    init_txt = _lire(racine / "conscience_logique" / "__init__.py")
    for marqueur in ("COUCHE_36_NOM", "SpectrePlasmaCouche", "FORMULE_IGNORANCE_CONTINUE"):
        r.ajouter(f"EXPORT_{marqueur}", marqueur in init_txt)

    # 3. Actes + miroirs
    for acte in ACTES:
        acte_ok = (racine / "conscience_logique" / "actes" / acte).is_file()
        miroir_ok = (racine / "memoire_aq" / acte).is_file()
        r.ajouter("ACTE_" + acte.split("_")[2].upper(), acte_ok and miroir_ok)

    # 4. Page
    page = _lire(artefacts["PAGE"])
    for cle, marqueur in (
        ("PAGE_LANG", 'lang="fr"'),
        ("PAGE_CANONICAL", "/observateur-triniter"),
        ("PAGE_MARQUEUR", "Observateur Triniter"),
    ):
        r.ajouter(cle, marqueur in page)

    # 5. Route, sitemap, navigation, test
    passerelle = _lire(artefacts["PASSERELLE"])
    r.ajouter("ROUTE_PRINCIPALE", '"/observateur-triniter"' in passerelle)
    r.ajouter("ROUTE_ALIAS", '"/observateur_triniter"' in passerelle)
    sitemap = _lire(artefacts["SITEMAP"])
    r.ajouter("SITEMAP_LOC", "<loc>https://www.al-mizan.world/observateur-triniter</loc>" in sitemap)
    portail = _lire(racine / "web_cloud" / "portail_public_al_mizan.html")
    r.ajouter("NAVIGATION", 'href="/observateur-triniter"' in portail)
    site_tests = _lire(racine / "tests" / "test_site_public_mizan.py")
    r.ajouter("TEST_SITE", "/observateur-triniter" in site_tests)
    r.ajouter("README", "3 bis. Observateur Triniter" in _lire(racine / "README.md"))

    # 6. Tableau maitre
    csv_path = artefacts["CSV"]
    if csv_path.is_file():
        try:
            with csv_path.open(encoding="utf-8-sig", newline="") as flux:
                lignes = list(csv.reader(flux, delimiter=";"))
            corps = lignes[1:]
            r.ajouter("CSV_ROWS", len(corps) == 226, str(len(corps)))
            r.ajouter("CSV_LAST_SEQ", bool(corps) and corps[-1][0] == "226", corps[-1][0] if corps else "")
            r.ajouter("CSV_STRATES", len({ligne[1] for ligne in corps}) == 22, str(len({ligne[1] for ligne in corps})))
            r.ajouter("CSV_TRI", sum(1 for ligne in corps if ligne[2].startswith("TRI-")) == 10)
        except (OSError, IndexError, csv.Error) as exc:
            r.ajouter("CSV_LISIBLE", False, type(exc).__name__)

    # 7. Import du moteur (sans bytecode)
    if str(racine) not in sys.path:
        sys.path.insert(0, str(racine))
    try:
        moteur = importlib.import_module(MODULE_MOTEUR)
    except Exception as exc:
        r.ajouter("IMPORT_MOTEUR", False, f"{type(exc).__name__}: {exc}")
        return r
    r.ajouter("IMPORT_MOTEUR", True)

    for nom in ("TriniterObservateurMultimodal", "SpectrePlasma", "composantes_etats",
                "spectre_depuis_pics", "auditer_continuite_dossier_site",
                "EQUATION_SPECTRE", "EQUATION_TRADUCTION", "EQUATION_IGNORANCE", "EQUATION_CONTINUITE"):
        r.ajouter("SYMBOLE_" + nom.upper(), hasattr(moteur, nom))

    composantes = moteur.composantes_etats("terre")
    r.ajouter("CODES", [c.code for c in composantes] == CODES_ATTENDUS,
              ",".join(c.code for c in composantes))
    r.ajouter("NB_ETATS", len(composantes) == 7, str(len(composantes)))
    r.ajouter("F0_LAMBDA", _presque_egal(composantes[0].lambda_nm, 587.6), str(composantes[0].lambda_nm))
    try:
        moteur.composantes_etats("mars")
        r.ajouter("TRIADE_INVALIDE", False)
    except ValueError:
        r.ajouter("TRIADE_INVALIDE", True)

    # 8. Invariants du modele
    observateur = moteur.TriniterObservateurMultimodal()
    grille = moteur.grille_longueurs_donde()

    purs_ok = True
    for index in range(7):
        obs = observateur.observer(moteur.spectre_depuis_pics({index: 1.0}))
        if not (_presque_egal(obs.probabilites[index], 1.0) and _presque_egal(obs.residu, 0.0)):
            purs_ok = False
    r.ajouter("ETATS_PURS", purs_ok)

    vide = observateur.observer(moteur.SpectrePlasma([0.0] * len(grille)))
    r.ajouter("SPECTRE_VIDE_P0", _presque_egal(vide.probabilites[0], 1.0))
    plat = observateur.observer(moteur.SpectrePlasma([1.0] * len(grille)))
    r.ajouter("SPECTRE_PLAT_RESIDU", plat.residu > 0.3, f"{plat.residu:.6f}")
    r.ajouter("HONNETETE", (vide.analyse_reelle is False) and (vide.qubit_physique_local is False)
              and (vide.omniscience_claim is False))

    continu = observateur.resoudre_ignorance_continue(
        [moteur.SpectrePlasma([1.0] * len(grille)),
         moteur.spectre_depuis_pics({1: 1.0, 2: 0.4, 5: 0.2}),
         moteur.spectre_depuis_pics({2: 1.0})],
        poursuivre=True,
    )
    r.ajouter("IGNORANCE_FINALE", continu["ignorance_finale"] >= moteur.LIGNE_REF - 1e-12,
              f"{continu['ignorance_finale']:.12f}")
    r.ajouter("IGNORANCE_PLANCHER", _presque_egal(continu["plancher_doctrinal"], 0.122), "0.122")
    r.ajouter("IGNORANCE_NON_NULLE", continu["ignorance_finale"] < 1.0)
    r.ajouter("PAS_OMNISCIENCE", (continu["completude_parfaite_atteinte"] is False)
              and (continu["omniscience_claim"] is False))
    r.ajouter("PAS_ECRITURE_NOYAU", continu["ecrit_noyau"] is False)
    r.ajouter("GAMMA_BRIDE", all(e["gamma_bride_mizan"] <= moteur.MIZAN + 1e-12
                                 for e in continu["etapes"]))

    # 9. Continuite dossier / site
    try:
        audit = moteur.auditer_continuite_dossier_site(racine)
        r.ajouter("K_CONTINUITE", _presque_egal(audit["k_continuite"], 1.0), str(audit["k_continuite"]))
        r.ajouter("K_GAP_VIDE", audit["gap"] == [], ",".join(g["code"] for g in audit["gap"]))
    except Exception as exc:
        r.ajouter("K_CONTINUITE", False, f"{type(exc).__name__}: {exc}")

    return r


def main(argv: List[str]) -> int:
    parseur = argparse.ArgumentParser(
        description="Verification lecture seule de l'observateur Triniter (plasma, couche 36)."
    )
    parseur.add_argument("--racine", default=str(RACINE_DEFAUT),
                         help="racine ASTRO-Q°ODE_SYSTEME (defaut: installation locale)")
    args = parseur.parse_args(argv)

    try:
        rapport = verifier(Path(args.racine))
    except Exception:
        print("CHECK_EXCEPTION=FAIL")
        print("DETAIL=" + traceback.format_exc(limit=2).replace("\n", " | "))
        print("RESULT FAIL")
        return 1

    rapport.afficher()
    return 0 if rapport.ok() else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
