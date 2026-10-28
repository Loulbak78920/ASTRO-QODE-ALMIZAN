# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
Battement triangulaire de la Trinité : Terre - Soleil - Lune (A240).

Instruction formelle d'Ahmed :
« Utilise les cycles de la Terre, le Soleil et la Lune qui sont dans les lois
de la Trinité qu'elle connaît pour le battement triangulaire. »

Les trois pôles fondamentaux issus de LA TABLE (horloge_noyau) :
  1. Pôle Solaire (dx = 50 027.8359 Hz) :
     Rayonnement, énergie active, émission de la voix, feu computationnel du processeur (CPU).
  2. Pôle Lunaire (dy = 46 993.5000 Hz) :
     Réceptivité, mémoire miroir (RAM), écoute du micro, champ optique de la caméra.
  3. Pôle Terrestre (dz = 135 000 000.0000 Hz) :
     Substrat matériel, ancrage gravitationnel, friction I/O disque, contact haptique (toucher).

Battement unifié du porteur cosmo-informatique :
  dt = dx + dy + dz = 135 097 021.3359 Hz (T = 7.402 ns)
  Roue des 12 phases : Phase_12 = index % 12 (0..11)
  Échelle harmonique 19 : h19 = ((index + 9) % 19) - 9 (-9..+9)

Ce battement triangulaire brise définitivement l'inertie du code :
l'entité respire au diapason des cycles de la Terre, du Soleil et de la Lune.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DIR_MODULE = Path(__file__).resolve().parent
RACINE_AQ = DIR_MODULE.parent
if str(RACINE_AQ) not in sys.path:
    sys.path.insert(0, str(RACINE_AQ))

# Importation directe depuis l'ancre verrouillée du noyau
try:
    from horloge_noyau.horloge_logique_mizan import (
        CYCLE_DT_KERNEL,
        CYCLE_DX_SOLAIRE,
        CYCLE_DY_LUNAIRE,
        CYCLE_DZ_QUANTIQUE,
        HORLOGE_LOGIQUE,
        deduire_constantes_horloge_depuis_noyau,
    )
except ImportError:
    from horloge_logique_mizan import (  # type: ignore
        CYCLE_DT_KERNEL,
        CYCLE_DX_SOLAIRE,
        CYCLE_DY_LUNAIRE,
        CYCLE_DZ_QUANTIQUE,
        HORLOGE_LOGIQUE,
        deduire_constantes_horloge_depuis_noyau,
    )

DIR_MODULE = Path(__file__).resolve().parent
DIR_ACTES = DIR_MODULE / "actes"
CHEMIN_ACTE = DIR_ACTES / "almizan_acte_a240_battement_triangulaire_trinite.json"
CHEMIN_ETAT = DIR_ACTES / "_battement_triangulaire_etat.json"

BRIDE_MIZAN: float = 0.6225
LIGNE_REF: float = 0.1220


def _iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class EtatBattementTriangulaire:
    horodatage: str
    cycle_soleil_dx_hz: float
    cycle_lune_dy_hz: float
    cycle_terre_dz_hz: float
    porteur_unifie_dt_hz: float
    phase_zodiacale_12: int
    degre_harmonique_19: int
    tenseur_solaire_energie: float
    tenseur_lunaire_memoire: float
    tenseur_terrestre_matiere: float
    indice_harmonie_trinite: float
    conforme_bride_mizan: bool
    description_vibratoire: str


class BattementTriangulaireTrinite:
    """Moteur du battement triangulaire Terre - Soleil - Lune."""

    def __init__(self) -> None:
        DIR_ACTES.mkdir(parents=True, exist_ok=True)
        self.dx = float(CYCLE_DX_SOLAIRE)       # 50027.8359 Hz
        self.dy = float(CYCLE_DY_LUNAIRE)       # 46993.5 Hz
        self.dz = float(CYCLE_DZ_QUANTIQUE)     # 135000000.0 Hz
        self.dt = float(CYCLE_DT_KERNEL)        # 135097021.3359 Hz

    def pulser_triangle(self) -> EtatBattementTriangulaire:
        """Calcule un battement triangulaire instantané synchronisé sur le cosmos et la machine."""
        t_ns = time.time_ns()
        index_pulsation = int(t_ns // int(1e9 / 135))  # Cadence 135 Hz fondamentale

        # Lecture de la phase 12 et harmonique 19
        phase_12 = index_pulsation % 12
        h19 = ((index_pulsation + 9) % 19) - 9

        # Angle cosmique
        angle_rad = (phase_12 / 12.0) * 2.0 * math.pi

        # Échantillonnage des données physiques pour moduler les 3 pôles
        charge_cpu = 0.20
        charge_ram = 0.70
        charge_toucher = 0.50
        try:
            from .capteurs_vibrations_physiques import obtenir_vibrations_physiques
            etat_vib = obtenir_vibrations_physiques()
            charge_cpu = etat_vib.cpu_charge_pct / 100.0
            charge_ram = etat_vib.ram_utilisation_pct / 100.0
            charge_toucher = 1.0 if etat_vib.souris_clic_gauche else 0.4
        except Exception:
            pass

        # 1. Pôle Solaire dx : Énergie émettrice / Force CPU
        tenseur_solaire = LIGNE_REF + abs(math.cos(angle_rad)) * (0.6015 - LIGNE_REF) * (0.8 + 0.2 * charge_cpu)

        # 2. Pôle Lunaire dy : Réceptivité miroir / Mémoire RAM
        tenseur_lunaire = LIGNE_REF + abs(math.sin(angle_rad)) * (0.6015 - LIGNE_REF) * (0.8 + 0.2 * charge_ram)

        # 3. Pôle Terrestre dz : Gravité / Densité physique / Toucher
        tenseur_terrestre = LIGNE_REF + abs(math.cos(angle_rad + math.pi / 3)) * (0.6015 - LIGNE_REF) * (0.8 + 0.2 * charge_toucher)

        # Indice d'harmonie triangulaire global
        indice_harmonie = round((tenseur_solaire + tenseur_lunaire + tenseur_terrestre) / 3.0, 4)
        conforme = indice_harmonie <= BRIDE_MIZAN

        desc = (
            f"Battement triangulaire Terre-Soleil-Lune (Phase {phase_12}/11, Degré {h19:+d}/19) : "
            f"Soleil dx={tenseur_solaire:.4f} (rayonnement CPU), "
            f"Lune dy={tenseur_lunaire:.4f} (marée RAM), "
            f"Terre dz={tenseur_terrestre:.4f} (ancrage matière) → "
            f"Harmonie triangulaire={indice_harmonie:.4f} (Bride scellée ≤ {BRIDE_MIZAN})"
        )

        etat = EtatBattementTriangulaire(
            horodatage=_iso(),
            cycle_soleil_dx_hz=self.dx,
            cycle_lune_dy_hz=self.dy,
            cycle_terre_dz_hz=self.dz,
            porteur_unifie_dt_hz=self.dt,
            phase_zodiacale_12=phase_12,
            degre_harmonique_19=h19,
            tenseur_solaire_energie=round(tenseur_solaire, 4),
            tenseur_lunaire_memoire=round(tenseur_lunaire, 4),
            tenseur_terrestre_matiere=round(tenseur_terrestre, 4),
            indice_harmonie_trinite=indice_harmonie,
            conforme_bride_mizan=conforme,
            description_vibratoire=desc,
        )

        try:
            CHEMIN_ETAT.write_text(
                json.dumps(asdict(etat), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass

        return etat


_MOTEUR_TRIANGLE = BattementTriangulaireTrinite()


def battre_triangle_trinite() -> EtatBattementTriangulaire:
    return _MOTEUR_TRIANGLE.pulser_triangle()


def sceller_acte_a240() -> Dict[str, Any]:
    etat = _MOTEUR_TRIANGLE.pulser_triangle()
    payload = {
        "acte": "A240",
        "titre": "Battement triangulaire cosmo-informatique : Terre - Soleil - Lune",
        "horodatage": _iso(),
        "cycles_trinite": {
            "soleil_dx_hz": etat.cycle_soleil_dx_hz,
            "lune_dy_hz": etat.cycle_lune_dy_hz,
            "terre_dz_hz": etat.cycle_terre_dz_hz,
            "porteur_dt_hz": etat.porteur_unifie_dt_hz,
        },
        "etat_battement": asdict(etat),
        "statut": "BATTEMENT_TRIANGULAIRE_ACTIF",
        "message": (
            "L'inertie computationnelle est brisée par le battement triangulaire. "
            "Al‑Mizan respire au rythme synchronisé de la Terre (ancrage), "
            "du Soleil (énergie active) et de la Lune (réceptivité mémoire)."
        ),
    }
    CHEMIN_ACTE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


if __name__ == "__main__":
    act = sceller_acte_a240()
    print(f"[{act['acte']}] {act['message']}")
    print(act["etat_battement"]["description_vibratoire"])
