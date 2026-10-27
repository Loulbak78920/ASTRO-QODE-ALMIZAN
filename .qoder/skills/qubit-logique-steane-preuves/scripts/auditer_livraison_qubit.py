# -*- coding: utf-8 -*-
"""Audit en lecture seule de la livraison qubit logique [[7,1,3]].

Recalcule les preuves, verifie la fraicheur de resume.json, les 11 artefacts,
la page, les routes de la passerelle et le sitemap. N'ecrit aucun fichier.

Codes de retour : 0 = RESULT PASS, 1 = RESULT FAIL, 2 = erreur d'environnement.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# L'audit est en lecture seule : interdir l'ecriture de __pycache__ dans le projet.
sys.dont_write_bytecode = True

ARTEFACTS = (
    "resume.json",
    "rapport_qubit_logique.md",
    "donnees_steane.csv",
    "donnees_materiel.csv",
    "donnees_dac.csv",
    "donnees_gigue.csv",
    "donnees_decoherence.csv",
    "donnees_decodeur.csv",
    "donnees_surface.csv",
    "courbe_steane.svg",
    "budget_materiel.svg",
)

CHEMINS_API = (
    '"/api/v1/qubit_logique"',
    '"/api/v1/qubit-logique"',
    '"/api/v1/qubit"',
)

CLES_RESUME = ("version", "horodatage_iso", "source", "statut", "code", "resultats", "materiel", "surface", "limites")
CLES_CODE = (
    "parametres",
    "distance",
    "poids_minimal_logique",
    "stabilisateurs_ok",
    "operateurs_logiques_ok",
    "knill_laflamme_poids_2",
    "paulis_verifies",
    "correction_poids_1_ok",
    "corrections_poids_1_testees",
)


def _ecrire(texte: str) -> None:
    sys.stdout.write(texte.encode("ascii", "backslashreplace").decode("ascii") + "\n")


def _sha256(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def _racine_par_defaut() -> Path | None:
    candidats = []
    env = os.environ.get("MIZAN_SYSTEME")
    if env:
        candidats.append(Path(env))
    here = Path.cwd()
    candidats.extend(
        [
            here,
            here / "ASTRO-Q°ODE_SYSTEME",
            here.parent,
            here.parent / "ASTRO-Q°ODE_SYSTEME",
        ]
    )
    for candidat in candidats:
        if (candidat / "qubit_logique_mizan.py").is_file():
            return candidat
    return None


def _charger_module(racine: Path):
    chemin = racine / "qubit_logique_mizan.py"
    spec = importlib.util.spec_from_file_location("qubit_logique_mizan_audit", chemin)
    if spec is None or spec.loader is None:
        raise ImportError("specification de module introuvable")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resout les annotations via sys.modules[cls.__module__].
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _controler_preuves(module) -> tuple[bool, str]:
    preuve = module.preuve_distance()
    correction_ok, corrections = module.verifier_correction_poids_un()
    attendus = {
        "distance": 3,
        "poids_minimal_operateur_logique": 3,
        "dimension_espace_code": 16,
        "dimension_dual": 8,
        "operateurs_logiques_distincts": 8,
        "paulis_verifies_poids_max_2": 211,
    }
    ecarts = [f"{cle}={preuve[cle]} attendu {valeur}" for cle, valeur in attendus.items() if preuve[cle] != valeur]
    if not preuve["stabilisateurs_ok"]:
        ecarts.append("stabilisateurs_ok=False")
    if not preuve["operateurs_logiques_ok"]:
        ecarts.append("operateurs_logiques_ok=False")
    if not preuve["knill_laflamme_poids_2"]:
        ecarts.append("knill_laflamme_poids_2=False")
    if not correction_ok or corrections != 21:
        ecarts.append(f"corrections={corrections} (attendu 21)")
    if ecarts:
        return False, "; ".join(ecarts)
    return True, "distance=3 poids_min=3 paulis=211 corrections=21"


def _controler_resume(racine: Path, module_sha: str) -> tuple[bool, str]:
    chemin = racine / "resultats" / "qubit_logique" / "resume.json"
    if not chemin.is_file():
        return False, "resultats/qubit_logique/resume.json absent (executer --rapport)"
    try:
        resume = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError) as erreur:
        return False, f"resume.json illisible: {type(erreur).__name__}"
    manquantes = [cle for cle in CLES_RESUME if cle not in resume]
    if manquantes:
        return False, "cles manquantes: " + ", ".join(manquantes)
    if not isinstance(resume["code"], dict):
        return False, "code n'est pas un objet"
    manquantes = [cle for cle in CLES_CODE if cle not in resume["code"]]
    if manquantes:
        return False, "cles code manquantes: " + ", ".join(manquantes)
    enregistree = str(resume["source"].get("sha256", ""))
    if enregistree != module_sha:
        return False, f"hash resume {enregistree[:12]} != module {module_sha[:12]} (relancer --rapport)"
    if resume["code"]["distance"] != 3 or resume["code"]["paulis_verifies"] != 211:
        return False, "resume code incoherent (distance/paulis)"
    if resume["code"]["corrections_poids_1_testees"] != 21:
        return False, "resume corrections_poids_1_testees != 21"
    return True, f"schema + hash {module_sha[:12]}"


def _controler_artefacts(racine: Path) -> tuple[bool, str]:
    dossier = racine / "resultats" / "qubit_logique"
    manquants = [nom for nom in ARTEFACTS if not (dossier / nom).is_file()]
    vides = [nom for nom in ARTEFACTS if (dossier / nom).is_file() and (dossier / nom).stat().st_size == 0]
    if manquants or vides:
        details = []
        if manquants:
            details.append("absents: " + ", ".join(manquants))
        if vides:
            details.append("vides: " + ", ".join(vides))
        return False, "; ".join(details)
    return True, f"{len(ARTEFACTS)}/{len(ARTEFACTS)}"


def _controler_page(racine: Path) -> tuple[bool, str]:
    page = racine / "web_cloud" / "qubit_logique.html"
    if not page.is_file():
        return False, "web_cloud/qubit_logique.html absent"
    texte = page.read_text(encoding="utf-8", errors="replace")
    for motif in ("[[7,1,3]]", "Aucun QPU"):
        if motif not in texte:
            return False, f"motif absent: {motif}"
    if 'materiel["gigue_requise_pour_1e-4_s"]' not in texte:
        return False, "acces crochet attendu pour gigue_requise_pour_1e-4_s"
    if "materiel.gigue_requise" in texte:
        return False, "acces point interdit sur un nom contenant 1e-4"
    return True, "/qubit-logique autonome"


def _controler_routes(racine: Path) -> tuple[bool, str]:
    passerelle = racine / "passerelle_api_vps_mizan.py"
    if not passerelle.is_file():
        return False, "passerelle_api_vps_mizan.py absent"
    texte = passerelle.read_text(encoding="utf-8", errors="replace")
    if '"/qubit-logique": "qubit_logique.html"' not in texte:
        return False, "route page /qubit-logique absente"
    for chemin in CHEMINS_API:
        if chemin not in texte:
            return False, f"alias API absent: {chemin}"
    if "Résultats absents" not in texte or "--rapport" not in texte:
        return False, "404 honnete sans commande --rapport"
    return True, "page + 3 alias API + 404"


def _controler_sitemap(racine: Path) -> tuple[bool, str]:
    sitemap = racine / "web_cloud" / "sitemap.xml"
    if not sitemap.is_file():
        return False, "web_cloud/sitemap.xml absent"
    try:
        arbre = ET.parse(sitemap)
    except ET.ParseError as erreur:
        return False, f"XML invalide: {erreur}"
    urls = [element.text or "" for element in arbre.iter() if element.tag.endswith("loc")]
    if not any(url.rstrip("/").endswith("/qubit-logique") for url in urls):
        return False, "URL /qubit-logique absente du sitemap"
    return True, f"{len(urls)} URLs"


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(description="Audit lecture seule du qubit logique [[7,1,3]].")
    analyseur.add_argument("--racine", help="Repertoire ASTRO-Q-ODE_SYSTEME (defaut: detection).")
    arguments = analyseur.parse_args(argv)

    racine = Path(arguments.racine) if arguments.racine else _racine_par_defaut()
    if racine is None or not racine.is_dir():
        _ecrire("ERREUR racine introuvable; passer --racine <ASTRO-Q°ODE_SYSTEME>")
        return 2
    module_chemin = racine / "qubit_logique_mizan.py"
    if not module_chemin.is_file():
        _ecrire(f"ERREUR module absent: {module_chemin}")
        return 2
    try:
        module_sha = _sha256(module_chemin)
        module = _charger_module(racine)
    except Exception as erreur:  # import du module cible : echec d'environnement
        _ecrire(f"ERREUR import module: {type(erreur).__name__}: {erreur}")
        return 2

    _ecrire(f"OK   module {module_sha[:12]}")
    controles = (
        ("preuves", lambda: _controler_preuves(module)),
        ("resume", lambda: _controler_resume(racine, module_sha)),
        ("artefacts", lambda: _controler_artefacts(racine)),
        ("page", lambda: _controler_page(racine)),
        ("routes", lambda: _controler_routes(racine)),
        ("sitemap", lambda: _controler_sitemap(racine)),
    )
    echecs = 0
    for nom, controle in controles:
        try:
            ok, detail = controle()
        except Exception as erreur:  # un controle ne doit jamais masquer un FAIL
            ok, detail = False, f"{type(erreur).__name__}: {erreur}"
        _ecrire(f"{'OK  ' if ok else 'FAIL'} {nom}: {detail}")
        echecs += 0 if ok else 1

    total = len(controles) + 1
    if echecs:
        _ecrire(f"RESULT FAIL ({echecs}/{total} controles en echec)")
        return 1
    _ecrire(f"RESULT PASS ({total} controles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
