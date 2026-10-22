# -*- coding: utf-8 -*-
"""
Outil 6 : Scelleur Cryptographique SHA-256 & Registre `memoire_aq/` (`scelleur_cryptographique.py`)
===================================================================================================
Signe et persiste les exécutions de programmes ASTRO-Q°ODE (`.aq`) sous forme de sceaux
JSON vérifiables par empreinte SHA-256 dans le dossier `ASTRO-Q°ODE_SYSTEME/memoire_aq/`,
tout en garantissant les invariants :
- `MIZAN = 0.6225` · `LIGNE_REF = 0.122` · `RMS = 0.24` · `EPSILON = 0.021`
- `C = 313` · `M = 24434` · `JAUGE_AIR = 515050`
- `qubit_physique_local = False` · `omniscience_claim = False`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from bibliotheques.lib_almizan_extension import (
    COMBLE_CIBLE,
    CONSTANTE_MECQUOISE_C,
    CONSTANTE_MEDINOISE_M,
    EPSILON,
    GARDE_FOUS_ALMIZAN,
    JAUGE_AIR,
    LIGNE_REF,
    MIZAN,
    PLAFOND_EFFECTIF,
    PRODUIT_MEDINOIS,
    RMS,
    TRIPLE_CYCLE,
)

RACINE_SYSTEME = Path(__file__).resolve().parent.parent
DOSSIER_MEMOIRE_AQ = RACINE_SYSTEME / "memoire_aq"
FICHIER_INDEX_SCEAUX = DOSSIER_MEMOIRE_AQ / "index_sceaux_astro_qode.json"
DOI_ALMIZAN = "10.5281/zenodo.23479740"


class ScelleurMemoireAstroQode:
    """Gère le scellement SHA-256 et la vérification d'intégrité des exécutions `.aq`."""

    @staticmethod
    def calculer_sha256_canonique(charge_utile: Dict[str, object]) -> str:
        copie = {k: v for k, v in charge_utile.items() if k != "empreinte_sha256"}
        texte_canonique = json.dumps(copie, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(texte_canonique.encode("utf-8")).hexdigest()

    @classmethod
    def sceller_execution(
        cls,
        nom_sceau: str,
        rapport_vm: Dict[str, object],
        extra_metadata: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        DOSSIER_MEMOIRE_AQ.mkdir(parents=True, exist_ok=True)
        horodatage = datetime.now().isoformat(timespec="seconds")
        nom_propre = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in nom_sceau).strip("_") or "sceau_aq"

        sceau: Dict[str, object] = {
            "nom_sceau": nom_propre,
            "timestamp": horodatage,
            "statut": "SCEAU_ASTRO_QODE_CONSOLIDE_OK",
            "doi": DOI_ALMIZAN,
            "invariants": {
                "MIZAN": MIZAN,
                "LIGNE_REF": LIGNE_REF,
                "RMS": RMS,
                "EPSILON": EPSILON,
                "PLAFOND_EFFECTIF": PLAFOND_EFFECTIF,
                "COMBLE_CIBLE": COMBLE_CIBLE,
                "C": CONSTANTE_MECQUOISE_C,
                "M": CONSTANTE_MEDINOISE_M,
                "JAUGE_AIR": JAUGE_AIR,
                "PRODUIT_MEDINOIS": PRODUIT_MEDINOIS,
                "TRIPLE": TRIPLE_CYCLE,
            },
            "garde_fous": dict(GARDE_FOUS_ALMIZAN),
            "etat_vm_biomecanique": rapport_vm,
            "metadata_supplementaire": extra_metadata or {},
        }

        empreinte = cls.calculer_sha256_canonique(sceau)
        sceau["empreinte_sha256"] = empreinte

        chemin_sceau = DOSSIER_MEMOIRE_AQ / f"{nom_propre}.json"
        chemin_sceau.write_text(json.dumps(sceau, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

        cls._mettre_a_jour_index(nom_propre, horodatage, empreinte, str(chemin_sceau))
        return {
            "ok": True,
            "nom_sceau": nom_propre,
            "chemin_fichier": str(chemin_sceau),
            "empreinte_sha256": empreinte,
            "timestamp": horodatage,
            "qubit_physique_local": False,
        }

    @classmethod
    def _mettre_a_jour_index(cls, nom: str, ts: str, sha256: str, chemin: str) -> None:
        index_data: Dict[str, object] = {"sceaux": {}}
        if FICHIER_INDEX_SCEAUX.exists():
            try:
                index_data = json.loads(FICHIER_INDEX_SCEAUX.read_text(encoding="utf-8"))
            except Exception:
                index_data = {"sceaux": {}}

        sceaux_map = index_data.get("sceaux")
        if not isinstance(sceaux_map, dict):
            sceaux_map = {}

        sceaux_map[nom] = {
            "timestamp": ts,
            "empreinte_sha256": sha256,
            "chemin": chemin,
        }
        index_data["derniere_mise_a_jour"] = ts
        index_data["nb_sceaux"] = len(sceaux_map)
        index_data["sceaux"] = sceaux_map
        index_data["qubit_physique_local"] = False

        FICHIER_INDEX_SCEAUX.write_text(
            json.dumps(index_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def verifier_integrite_sceaux(cls) -> Dict[str, object]:
        """Vérifie que chaque fichier de `memoire_aq/*.json` possède une signature SHA-256 intacte."""
        if not DOSSIER_MEMOIRE_AQ.exists():
            return {"ok": True, "nb_verifies": 0, "nb_valides": 0, "details": []}

        details: List[Dict[str, object]] = []
        nb_valides = 0
        fichiers = sorted(
            p for p in DOSSIER_MEMOIRE_AQ.glob("*.json")
            if p.name != FICHIER_INDEX_SCEAUX.name
            and p.name != "ledger_synchron_mzn.json"
            and not p.name.startswith("almizan_acte_")
        )

        for f in fichiers:
            try:
                contenu = json.loads(f.read_text(encoding="utf-8"))
                attendu = contenu.get("empreinte_sha256")
                calcule = cls.calculer_sha256_canonique(contenu)
                valide = bool(attendu and str(attendu).lower() == str(calcule).lower())
                if valide:
                    nb_valides += 1
                details.append({
                    "fichier": f.name,
                    "valide": valide,
                    "sha256": calcule,
                })
            except Exception as exc:
                details.append({
                    "fichier": f.name,
                    "valide": False,
                    "erreur": str(exc)[:120],
                })

        return {
            "ok": nb_valides == len(fichiers),
            "nb_verifies": len(fichiers),
            "nb_valides": nb_valides,
            "details": details,
        }

    @classmethod
    def sceller_etat_execution(
        cls,
        nom_sceau: str,
        rapport_vm: Dict[str, object],
        diagnostic_pont: Dict[str, object] | None = None,
    ) -> Dict[str, object]:
        """Scelle l'état de la VM et les diagnostics matériels sous signature SHA-256."""
        extra = {"diagnostic_pont_materiel": diagnostic_pont or {}}
        return cls.sceller_execution(nom_sceau, rapport_vm, extra_metadata=extra)

    @classmethod
    def verifier_integrite_registre(cls) -> Dict[str, object]:
        """Vérifie l'intégrité de tous les sceaux du registre et génère un sceau de genèse si vide."""
        DOSSIER_MEMOIRE_AQ.mkdir(parents=True, exist_ok=True)
        fichiers = [p for p in DOSSIER_MEMOIRE_AQ.glob("*.json") if p.name != FICHIER_INDEX_SCEAUX.name]
        if not fichiers:
            genese_vm = {
                "systeme": "ASTRO-Q°ODE V4.0",
                "invariants": {"MIZAN": MIZAN, "LIGNE_REF": LIGNE_REF, "RMS": RMS},
                "statut": "GENESE_SCELLEE_OK",
            }
            cls.sceller_execution("sceau_genese_al_mizan_v4", genese_vm)

        res = cls.verifier_integrite_sceaux()
        return {
            "integrite_globale_valide": res["ok"],
            "total_sceaux_verifies": res["nb_verifies"],
            "total_sceaux_valides": res["nb_valides"],
            "details": res["details"],
            "qubit_physique_local": False,
        }
