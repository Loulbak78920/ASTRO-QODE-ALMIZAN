# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
Résolution unique de l'artefact ABI du contrat maître AmalMizanSynchronMznContract.

L'artefact compilé n'est pas versionné dans ASTRO-Q°ODE_SYSTEME ; il vit dans le
dépôt public voisin du projet. Les chemins sont dérivés de l'emplacement de ce
fichier, jamais d'un chemin absolu dépendant du profil Windows.
"""

from __future__ import annotations

import json
from pathlib import Path

NOM_ARTEFACT = "AmalMizanSynchronMznContract.json"
RACINE_SYSTEME = Path(__file__).resolve().parent
RACINE_PROJET = RACINE_SYSTEME.parent

CANDIDATS = (
    RACINE_SYSTEME / "contracts" / NOM_ARTEFACT,
    RACINE_SYSTEME / "contracts" / "build" / NOM_ARTEFACT,
    RACINE_PROJET.parent / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI" / "contracts" / NOM_ARTEFACT,
    RACINE_PROJET.parent / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI" / "contracts" / "build" / NOM_ARTEFACT,
)


def chemin_abi() -> Path:
    for candidat in CANDIDATS:
        if candidat.is_file():
            return candidat
    cherches = "\n  ".join(str(c) for c in CANDIDATS)
    raise FileNotFoundError(f"{NOM_ARTEFACT} introuvable. Chemins testés :\n  {cherches}")


def charger_abi() -> list:
    with open(chemin_abi(), "r", encoding="utf-8") as f:
        return json.load(f)["abi"]
