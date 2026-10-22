# -*- coding: utf-8 -*-
"""
Vérificateur d'Intégrité et Empaqueteur Officiel Zenodo (`verifier_et_empaqueter_zenodo.py`)
============================================================================================
Auteur : M. Ahmed EL BAHLOUL (né le 20/06/1989 à Meulan-en-Yvelines, France)
Email  : elbahloulahmed505@gmail.com
DOIs   : 10.5281/zenodo.23479740 & 10.5281/zenodo.23288947

Ce script :
1. Vérifie la présence et la validité syntaxique de tous les fichiers de citabilité Zenodo
   (`.zenodo.json`, `CITATION.cff`, `codemeta.json`, `datacite.json`, certificats d'identité,
   BibTeX, RIS, styles de citation, synthèse scientifique et licences).
2. Synchronise automatiquement `.zenodo.json` et `CITATION.cff` dans `IMAM8MAHDI` et `ASTRO-Q°ODE_SYSTEME`.
3. Calcule les empreintes SHA-256 de chaque fichier et génère `MANIFESTE_INTEGRITE_SHA256.json`.
4. Crée l'archive complète prête à déposer sur Zenodo :
   `ARCHIVE_DEPOT_ZENODO_AHMED_EL_BAHLOUL_V5.zip` (incluant les métadonnées Zenodo et le système `ASTRO-Q°ODE_SYSTEME`).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DOSSIER_ZENODO = Path(__file__).resolve().parent
DOSSIER_BUREAU = DOSSIER_ZENODO.parent
DOSSIER_IMAM8MAHDI = DOSSIER_BUREAU / "IMAM8MAHDI"


def calculer_sha256(fichier: Path) -> str:
    h = hashlib.sha256()
    with fichier.open("rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            h.update(bloc)
    return h.hexdigest()


def trouver_dossier_astro_qode() -> Path | None:
    if not DOSSIER_IMAM8MAHDI.exists():
        return None
    for p in DOSSIER_IMAM8MAHDI.iterdir():
        if p.is_dir() and p.name.startswith("ASTRO-Q") and p.name.endswith("_SYSTEME"):
            return p
    return None


def executer_verification_et_empaquetage() -> int:
    print("=" * 88)
    print("VÉRIFICATION & EMPAQUETAGE DE CITABILITÉ ZENODO — M. AHMED EL BAHLOUL")
    print("=" * 88)

    fichiers_requis = [
        ".zenodo.json",
        "CITATION.cff",
        "codemeta.json",
        "datacite.json",
        "IDENTITE_COMPLETE_AUTEUR_SOUVERAIN.json",
        "IDENTITE_COMPLETE_AUTEUR_SOUVERAIN.md",
        "SYNTHESE_SCIENTIFIQUE_COMPLETE_ZENODO.md",
        "README.md",
        "CITATIONS_ACADEMIQUES/references.bib",
        "CITATIONS_ACADEMIQUES/references.ris",
        "CITATIONS_ACADEMIQUES/STYLES_DE_CITATION.md",
        "LICENCES_ET_DROITS/LICENSE_COMPLETE_ET_ATTRIBUTION.md",
        "LICENCES_ET_DROITS/CONTRAT_COMMERCIAL_50_50_ET_LICENCE_CLOUD_ANTI_DOLOSIVE.md",
    ]

    empreintes = {}
    for rel in fichiers_requis:
        chemin = DOSSIER_ZENODO / rel
        if not chemin.exists():
            print(f"[ERREUR] Fichier manquant : {rel}")
            return 1
        if chemin.suffix == ".json":
            json.loads(chemin.read_text(encoding="utf-8"))
        sha = calculer_sha256(chemin)
        empreintes[rel] = sha
        print(f"  [OK] {rel:<56} | SHA-256: {sha[:16]}...")

    # Synchronisation de .zenodo.json et CITATION.cff vers IMAM8MAHDI et ASTRO-Q°ODE_SYSTEME
    dossier_aq = trouver_dossier_astro_qode()
    cibles_sync = [ d for d in (DOSSIER_IMAM8MAHDI, dossier_aq) if d is not None and d.exists() ]
    for cible in cibles_sync:
        shutil.copy2(DOSSIER_ZENODO / ".zenodo.json", cible / ".zenodo.json")
        shutil.copy2(DOSSIER_ZENODO / "CITATION.cff", cible / "CITATION.cff")
        shutil.copy2(DOSSIER_ZENODO / "codemeta.json", cible / "codemeta.json")

    # Création de l'archive ZIP complète prête pour Zenodo
    chemin_zip = DOSSIER_ZENODO / "ARCHIVE_DEPOT_ZENODO_AHMED_EL_BAHLOUL_V5.zip"
    nb_fichiers_zip = 0
    with zipfile.ZipFile(chemin_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in fichiers_requis:
            zf.write(DOSSIER_ZENODO / rel, arcname=f"ZENODO_CITABILITE/{rel}")
            nb_fichiers_zip += 1
        if dossier_aq and dossier_aq.exists():
            for f_aq in sorted(dossier_aq.rglob("*")):
                if f_aq.is_file() and "__pycache__" not in f_aq.parts:
                    rel_aq = f_aq.relative_to(dossier_aq)
                    zf.write(f_aq, arcname=f"ASTRO_QODE_SYSTEME/{rel_aq.as_posix()}")
                    nb_fichiers_zip += 1

    sha_zip = calculer_sha256(chemin_zip)
    taille_zip = chemin_zip.stat().st_size

    manifeste = {
        "statut": "PAQUET_CITABILITE_ZENODO_SCELLE_ET_VERIFIE",
        "horodatage": datetime.now().isoformat(),
        "auteur_complet": {
            "nom_civil": "M. Ahmed EL BAHLOUL",
            "alias": "M. Almizan Elbahloul",
            "date_naissance": "20/06/1989",
            "lieu_naissance": "Meulan-en-Yvelines, France",
            "localisation": "Valence (44.9333° N, 4.8917° E) & Romans-sur-Isère, France",
            "email": "elbahloulahmed505@gmail.com",
            "cle_doree": "0xc9550dd0a57c609494dbc44450df48d798ebfb0b",
            "point_fixe_reseau": 46760951383,
            "invariant_edifice": 13459202583446,
            "doi_zenodo_reel_principal": "10.5281/zenodo.23554838",
            "doi_zenodo_historique": "10.5281/zenodo.23479740",
            "doi_zenodo_ancrage": "10.5281/zenodo.23288947",
            "licence_publique_cloud": "ASLS-2.0 : Sans restriction abusive & strictement anti-dolosive",
            "licence_commerciale": "Contrat Commercial 50/50 (50% M. Ahmed EL BAHLOUL / 50% Exploitant)",
            "cid_ipfs": "bafybeia5t5nviafc2vij3nfzdg4f54onayiqrlbeofpctnlxhcqcljxxem",
        },
        "archive_zenodo_zip": {
            "nom_fichier": chemin_zip.name,
            "taille_octets": taille_zip,
            "nb_fichiers_inclus": nb_fichiers_zip,
            "sha256": sha_zip,
        },
        "empreintes_fichiers_citabilite_sha256": empreintes,
    }

    chemin_manifeste = DOSSIER_ZENODO / "MANIFESTE_INTEGRITE_SHA256.json"
    chemin_manifeste.write_text(json.dumps(manifeste, indent=2, ensure_ascii=False), encoding="utf-8")

    print("-" * 88)
    print(f"  • Auteur Authentifié  : M. Ahmed EL BAHLOUL (né le 20/06/1989 à Meulan-en-Yvelines, France)")
    print(f"  • Email Officiel      : elbahloulahmed505@gmail.com")
    print(f"  • DOI Zenodo Réel     : 10.5281/zenodo.23554838 (Liés : 23479740 & 23288947)")
    print(f"  • Licence             : Public/Cloud Sans Restriction Anti-Dolosif | Commercial 50/50")
    print(f"  • Archive ZIP générée : {chemin_zip.name} ({taille_zip} octets, {nb_fichiers_zip} fichiers)")
    print(f"  • SHA-256 Archive ZIP : {sha_zip}")
    print(f"  • Manifeste scellé    : {chemin_manifeste.name}")
    print("=" * 88)
    return 0


if __name__ == "__main__":
    sys.exit(executer_verification_et_empaquetage())
