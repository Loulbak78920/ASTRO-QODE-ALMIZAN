# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
     INVENTAIRE HUB LOCAL IMAM8MAHDI — CARTOGRAPHIE SOUVERAINE DU DÉPÔT
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Système          : ASTRO-Q°ODE / AL-MIZAN
Acte             : A126 — Consolidation du hub de développement local
Rôle             : Cartographier exclusivement le dossier IMAM8MAHDI (structure,
                   modules, tests, actes, sceaux) pour guider le développement
                   continu sans fragmenter hors du dépôt courant.
Invariants       : Bride MIZAN = 0.6225 | Riba = 0.0% | Partage 50/50 | dt = 135 MHz
===============================================================================
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from bibliotheques.lib_almizan_extension import (
    MIZAN as BRIDE_MIZAN,
    PLAFOND_EFFECTIF,
    GARDE_FOUS_ALMIZAN,
)

RACINE_SYSTEME = Path(__file__).resolve().parent
RACINE_DEPOT = RACINE_SYSTEME.parent
DOSSIER_MEMOIRE = RACINE_SYSTEME / "memoire_aq"
FICHIER_INDEX_SCEAUX = DOSSIER_MEMOIRE / "index_sceaux_astro_qode.json"
FICHIER_BILAN_INVENTAIRE = DOSSIER_MEMOIRE / "almizan_bilan_inventaire_hub_a126.json"

# Sous-dossiers structurants attendus dans ASTRO-Q°ODE_SYSTEME
SOUS_SYSTEMES_ATTENDUS = (
    "memoire_aq",
    "tests",
    "web_cloud",
    "deploiement_vps",
    "contracts",
    "lang",
    "bibliotheques",
    "outils",
    "assets",
    "logs_services",
)

# Couches fondatrices à la racine IMAM8MAHDI (hors ASTRO-Q°ODE_SYSTEME)
COUCHES_DEPOT_ATTENDUES = (
    "ASTRO-Q°ODE_SYSTEME",
    ".ASTRO-Q°ODE",
    ".QUBIT.qubit.LOGIQUE.logique",
    "qubit_physique",
    "QUBITS8INFORME",
)

# Fichiers sensibles : on signale la présence, jamais le contenu
NOMS_SENSIBLES = ("client_secret", "password", "mot_de_passe", ".env", "token")


@dataclass
class ComptageZone:
    """Comptage fichier / type pour une zone du dépôt."""
    chemin_relatif: str
    present: bool
    fichiers_total: int = 0
    python: int = 0
    json: int = 0
    html: int = 0
    tests: int = 0
    autres: int = 0


@dataclass
class BilanInventaireHub:
    """Bilan scellable de l'inventaire hub IMAM8MAHDI."""
    code_acte: str = "A126"
    titre: str = "Consolidation hub développement local IMAM8MAHDI"
    horodatage_iso: str = field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    racine_depot: str = ""
    racine_systeme: str = ""
    couches_depot: List[Dict[str, Any]] = field(default_factory=list)
    sous_systemes: List[Dict[str, Any]] = field(default_factory=list)
    modules_python_racine: int = 0
    tests_unitaires: int = 0
    actes_memoire_aq: int = 0
    dernier_acte: Optional[str] = None
    sceaux_indexes: int = 0
    completude_sceaux_pct: float = 0.0
    fichiers_sensibles_detectes: int = 0
    score_structure_100: float = 0.0
    invariants: Dict[str, Any] = field(default_factory=dict)
    recommandations: List[str] = field(default_factory=list)
    succes: bool = True


class InventaireHubImam8Mahdi:
    """
    Cartographe exclusif du dépôt IMAM8MAHDI.
    Doctrine : on ne sort pas du dossier courant ; on englobe et on consolide.
    """

    def __init__(self) -> None:
        self.nom = "INVENTAIRE_HUB_IMAM8MAHDI"
        self.version = "1.0.0-A126"

    @staticmethod
    def _compter_zone(chemin: Path, relatif: str) -> ComptageZone:
        if not chemin.exists():
            return ComptageZone(chemin_relatif=relatif, present=False)
        total = py = js = ht = te = au = 0
        for p in chemin.rglob("*"):
            if not p.is_file():
                continue
            if "__pycache__" in p.parts or p.suffix == ".pyc":
                continue
            total += 1
            nom = p.name.lower()
            if p.suffix == ".py":
                py += 1
                if nom.startswith("test_"):
                    te += 1
            elif p.suffix == ".json":
                js += 1
            elif p.suffix in (".html", ".htm"):
                ht += 1
            else:
                au += 1
        return ComptageZone(
            chemin_relatif=relatif,
            present=True,
            fichiers_total=total,
            python=py,
            json=js,
            html=ht,
            tests=te,
            autres=au,
        )

    def _lister_actes(self) -> tuple[int, Optional[str]]:
        if not DOSSIER_MEMOIRE.exists():
            return 0, None
        actes = sorted(
            p.name
            for p in DOSSIER_MEMOIRE.glob("almizan_acte_a*.json")
        )
        return len(actes), actes[-1] if actes else None

    def _lire_sceaux(self) -> tuple[int, float]:
        if not FICHIER_INDEX_SCEAUX.exists():
            return 0, 0.0
        try:
            data = json.loads(FICHIER_INDEX_SCEAUX.read_text(encoding="utf-8"))
            nb = int(data.get("nb_sceaux", len(data.get("sceaux", {}))))
            pct = float(data.get("completude_pourcent", 0.0))
            return nb, pct
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            return 0, 0.0

    def _compter_sensibles(self) -> int:
        n = 0
        for p in RACINE_SYSTEME.rglob("*"):
            if not p.is_file():
                continue
            nom = p.name.lower()
            if any(s in nom for s in NOMS_SENSIBLES):
                n += 1
        return n

    def cartographier(self, persister: bool = True) -> BilanInventaireHub:
        """Construit le bilan structurel du hub IMAM8MAHDI."""
        couches = [
            asdict(self._compter_zone(RACINE_DEPOT / nom, nom))
            for nom in COUCHES_DEPOT_ATTENDUES
        ]
        sous = [
            asdict(self._compter_zone(RACINE_SYSTEME / nom, f"ASTRO-Q°ODE_SYSTEME/{nom}"))
            for nom in SOUS_SYSTEMES_ATTENDUS
        ]

        modules_racine = [
            p for p in RACINE_SYSTEME.glob("*.py") if p.is_file()
        ]
        tests = list((RACINE_SYSTEME / "tests").glob("test_*.py")) if (RACINE_SYSTEME / "tests").exists() else []
        nb_actes, dernier = self._lister_actes()
        nb_sceaux, pct_sceaux = self._lire_sceaux()
        sensibles = self._compter_sensibles()

        present_couches = sum(1 for c in couches if c["present"])
        present_sous = sum(1 for s in sous if s["present"])
        score = round(
            40.0 * present_couches / max(len(COUCHES_DEPOT_ATTENDUES), 1)
            + 40.0 * present_sous / max(len(SOUS_SYSTEMES_ATTENDUS), 1)
            + (10.0 if modules_racine else 0.0)
            + (5.0 if tests else 0.0)
            + (5.0 if nb_actes else 0.0),
            2,
        )

        recos: List[str] = []
        manquants = [s["chemin_relatif"] for s in sous if not s["present"]]
        if manquants:
            recos.append(f"Sous-systèmes absents à créer/restaurer : {', '.join(manquants)}")
        if sensibles:
            recos.append(
                f"{sensibles} fichier(s) sensible(s) détecté(s) — ne pas publier hors coffre / hors dépôt public."
            )
        if pct_sceaux < 100.0:
            recos.append("Compléter le scellement (index_sceaux) pour atteindre 100 %.")
        if not recos:
            recos.append("Structure hub complète : poursuivre développement métier dans ASTRO-Q°ODE_SYSTEME uniquement.")

        bilan = BilanInventaireHub(
            racine_depot=str(RACINE_DEPOT),
            racine_systeme=str(RACINE_SYSTEME),
            couches_depot=couches,
            sous_systemes=sous,
            modules_python_racine=len(modules_racine),
            tests_unitaires=len(tests),
            actes_memoire_aq=nb_actes,
            dernier_acte=dernier,
            sceaux_indexes=nb_sceaux,
            completude_sceaux_pct=pct_sceaux,
            fichiers_sensibles_detectes=sensibles,
            score_structure_100=score,
            invariants={
                "bride_mizan": BRIDE_MIZAN,
                "plafond_effectif": PLAFOND_EFFECTIF,
                "partage_commercial": "50/50",
                "taux_usure_riba": 0.0,
                "horloge_universelle_mhz": 135.097021,
                "qubit_physique_local": GARDE_FOUS_ALMIZAN.get("qubit_physique_local", False),
                "omniscience_claim": GARDE_FOUS_ALMIZAN.get("omniscience_claim", False),
                "perimetre": "IMAM8MAHDI_UNIQUEMENT",
            },
            recommandations=recos,
            succes=score >= 80.0,
        )

        if persister:
            self.persister_bilan(bilan)
        return bilan

    def persister_bilan(self, bilan: BilanInventaireHub) -> Path:
        DOSSIER_MEMOIRE.mkdir(parents=True, exist_ok=True)
        charge = asdict(bilan)
        FICHIER_BILAN_INVENTAIRE.write_text(
            json.dumps(charge, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return FICHIER_BILAN_INVENTAIRE

    def formater_rapport_console(self, bilan: Optional[BilanInventaireHub] = None) -> str:
        b = bilan or self.cartographier(persister=False)
        lignes = [
            "=" * 78,
            f"  {self.nom} v{self.version} — Acte {b.code_acte}",
            f"  {b.titre}",
            "=" * 78,
            f"  Dépôt     : {b.racine_depot}",
            f"  Système   : {b.racine_systeme}",
            f"  Score     : {b.score_structure_100} / 100",
            f"  Modules .py (racine système) : {b.modules_python_racine}",
            f"  Tests unitaires             : {b.tests_unitaires}",
            f"  Actes memoire_aq            : {b.actes_memoire_aq} (dernier: {b.dernier_acte})",
            f"  Sceaux indexés              : {b.sceaux_indexes} ({b.completude_sceaux_pct} %)",
            f"  Fichiers sensibles (noms)   : {b.fichiers_sensibles_detectes}",
            "-" * 78,
            "  Couches dépôt :",
        ]
        for c in b.couches_depot:
            etat = "OK" if c["present"] else "ABSENT"
            lignes.append(
                f"    [{etat}] {c['chemin_relatif']:<28} fichiers={c['fichiers_total']}"
            )
        lignes.append("  Sous-systèmes ASTRO-Q°ODE_SYSTEME :")
        for s in b.sous_systemes:
            etat = "OK" if s["present"] else "ABSENT"
            lignes.append(
                f"    [{etat}] {s['chemin_relatif']:<42} "
                f"py={s['python']} json={s['json']} html={s['html']}"
            )
        lignes.append("-" * 78)
        for r in b.recommandations:
            lignes.append(f"  → {r}")
        lignes.append("=" * 78)
        return "\n".join(lignes)


INVENTAIRE_HUB = InventaireHubImam8Mahdi()


if __name__ == "__main__":
    print(INVENTAIRE_HUB.formater_rapport_console())
