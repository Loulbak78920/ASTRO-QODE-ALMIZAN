# -*- coding: utf-8 -*-
"""
===============================================================================
  HORLOGE LOGIQUE DU NOYAU — DÉDUITE DEPUIS COMPLEXE (point zéro → expansion)
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Système          : ASTRO-Q°ODE / AL-MIZAN
Acte             : A136

DOCTRINE :
  L'horloge n'assigne PAS de Hz arbitraires.
  Elle lit le RÉSULTAT du calcul de LA TABLE (famille COMPLEXE = point zéro) :

      MatriceLogiqueComplexe.calculer_cycles_trinite_depuis_zero()
        → dx, dy, dz, dt, phases 0..11, h19 ∈ [-9 ; +9]

  Dissociation conservée :
    • ÉTATS DE MATIÈRE : ±313 / M=24434 (substance) — pas des cycles
    • Q° mécois/médinois : 2304 / 1536 — déduits de LA TABLE (pas 313/24434)
    • CYCLES : dx/dy/dz/dt — dynamiques, portés par cette horloge

  Pulsation = fonction pure de time.monotonic_ns (même instant → même phase).
===============================================================================
"""

from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple

from bibliotheques.lib_informe import (
    ANCRE_M_SUBSTANCE,
    DECOMPOSITION_M_24434,
    MatriceLogiqueComplexe,
    POLE_MATIERE_NEGATIF,
    POLE_MATIERE_POSITIF,
    Q_DEGRE_MECOIS,
    Q_DEGRE_MEDINOIS,
    synchroniser_etats_matiere_aux_cinq_familles,
    verifier_decomposition_m_24434,
)

# ── Substance matière (PAS des cycles, PAS des Q°) ────────────────────────────
POLARITE_C_MATIERE = 313
POLE_NEGATIF_MATIERE = POLE_MATIERE_NEGATIF
POLE_POSITIF_MATIERE = POLE_MATIERE_POSITIF
ANCRE_M_MATIERE = ANCRE_M_SUBSTANCE
TRIPLE_MATRICE = -2393774546
JAUGE_AIR_MATRICE = 515050
assert verifier_decomposition_m_24434(), "M=24434 doit coller à 2-4-4-3-4 (cinq familles)"


def deduire_constantes_horloge_depuis_noyau() -> Dict[str, Any]:
    """
    POINT ZÉRO = COMPLEXE → calcul Trinité → constantes d'horloge.
    Aucune valeur de cycle n'est inventée ici : tout sort de LA TABLE.
    """
    brut = MatriceLogiqueComplexe.calculer_cycles_trinite_depuis_zero()
    cycles = brut["cycles_distincts"]
    sync = brut["synchronisation_harmonique"]
    dx = float(cycles["soleil_dx"]["valeur_hz"])
    dy = float(cycles["lune_dy"]["valeur_hz"])
    dz = float(cycles["terre_dz"]["valeur_hz"])
    dt = float(sync["porteur_dt"]["valeur_hz"])
    ppcm = int(sync["roue_phases_communes"]["ppcm"])
    base_h = int(sync["echelle_harmonique"]["base"])
    amp_h = int(sync["echelle_harmonique"]["amplitude"])
    periode_ns = float(sync["porteur_dt"]["periode_ns"])
    return {
        "origine": "COMPLEXE_POINT_ZERO",
        "operateur": brut["operateur"],
        "dx": dx,
        "dy": dy,
        "dz": dz,
        "dt": dt,
        "periode_dt_ns": periode_ns,
        "ppcm_phases": ppcm,
        "base_harmonique": base_h,
        "amplitude_harmonique": amp_h,
        "q_mecois": Q_DEGRE_MECOIS,
        "q_medinois": Q_DEGRE_MEDINOIS,
        "verification_dt": abs(dt - (dx + dy + dz)) < 1e-6,
        "brut_noyau": brut,
    }


# ── Constantes d'horloge = RÉSULTAT du noyau (pas d'assignation manuelle) ─────
_HORLOGE_NOYAU: Dict[str, Any] = deduire_constantes_horloge_depuis_noyau()
assert _HORLOGE_NOYAU["verification_dt"], "dt doit égaler dx+dy+dz (noyau)"

CYCLE_DX_SOLAIRE: float = _HORLOGE_NOYAU["dx"]
CYCLE_DY_LUNAIRE: float = _HORLOGE_NOYAU["dy"]
CYCLE_DZ_QUANTIQUE: float = _HORLOGE_NOYAU["dz"]
CYCLE_DT_KERNEL: float = _HORLOGE_NOYAU["dt"]
DT_KERNEL_NS: float = _HORLOGE_NOYAU["periode_dt_ns"]

PPCM_CYCLES_TRINITE: int = _HORLOGE_NOYAU["ppcm_phases"]       # 12
BASE_HARMONIQUE: int = _HORLOGE_NOYAU["base_harmonique"]       # 19
AMPLITUDE_HARMONIQUE: int = _HORLOGE_NOYAU["amplitude_harmonique"]  # 9

# Une pulsation logique ≈ 1 s (int(dt) ticks kernel) — lecture stable pour la voix
TICKS_KERNEL_PAR_PULSATION: int = int(CYCLE_DT_KERNEL)
PERIODE_PULSATION_NS: float = TICKS_KERNEL_PAR_PULSATION * DT_KERNEL_NS


@dataclass(frozen=True)
class EtatMatiereMatricielle:
    """État de matière matricielle (substance) — distinct des cycles et des Q°."""
    charge_polarite: int
    ancre_substance_m: int
    jauge_air: int
    produit_medinois: int
    nature_physique: str
    decomposition_m_familles: Tuple[int, ...] = DECOMPOSITION_M_24434
    famille_complexe_est_la_table: bool = True


@dataclass(frozen=True)
class CycleTriniteSynchrone:
    """Instantané de l'horloge déduite du noyau COMPLEXE."""
    index_pulsation_continue: int
    phase_trinite_12: int
    harmonique_base_19: int
    pulsation_dt_hz: float
    composante_dx_solaire: float
    composante_dy_lunaire: float
    composante_dz_quantique: float
    continuité_sans_arret: bool
    horodatage_iso: str
    ticks_kernel_ecoules: int = 0
    origine_noyau: str = "COMPLEXE_POINT_ZERO"


def calculer_etat(index_pulsation: int) -> Tuple[EtatMatiereMatricielle, int, int, int]:
    """Fonction PURE : index → (matière, phase 0..11, h19, tour)."""
    phase_12 = index_pulsation % PPCM_CYCLES_TRINITE
    tour = index_pulsation // PPCM_CYCLES_TRINITE
    h19 = ((index_pulsation + AMPLITUDE_HARMONIQUE) % BASE_HARMONIQUE) - AMPLITUDE_HARMONIQUE
    charge = POLE_POSITIF_MATIERE if index_pulsation % 2 == 1 else POLE_NEGATIF_MATIERE
    em = EtatMatiereMatricielle(
        charge_polarite=charge,
        ancre_substance_m=ANCRE_M_MATIERE,
        jauge_air=JAUGE_AIR_MATRICE,
        produit_medinois=JAUGE_AIR_MATRICE * POLARITE_C_MATIERE * ANCRE_M_MATIERE,
        nature_physique=(
            "État de matière synchronisé aux 5 familles "
            "(COMPLEXE = LA TABLE / point zéro ; M=24434=2-4-4-3-4)"
        ),
        decomposition_m_familles=DECOMPOSITION_M_24434,
        famille_complexe_est_la_table=True,
    )
    return em, phase_12, h19, tour


class HorlogeLogiqueMatriceMizan:
    """
    Horloge du noyau logique IMAM8MAHDI.
    Constantes dx/dy/dz/dt/phases/h19 déduites de MatriceLogiqueComplexe.
    Asservie à time.monotonic_ns pour la lecture continue.
    """

    def __init__(self) -> None:
        self._verrou = threading.Lock()
        self._t0_ns = time.monotonic_ns()
        self.origine_noyau = "COMPLEXE_POINT_ZERO"
        self.dernier_cycle: CycleTriniteSynchrone
        self.etat_matiere: EtatMatiereMatricielle
        self.etat_matiere, self.dernier_cycle = self.lire()

    def lire(self, t_ns: int | None = None) -> Tuple[EtatMatiereMatricielle, CycleTriniteSynchrone]:
        """Lit l'état à l'instant t_ns (par défaut : maintenant). Sans effet de bord logique."""
        if t_ns is None:
            t_ns = time.monotonic_ns()
        ecoule_ns = max(0, t_ns - self._t0_ns)
        ticks = int(ecoule_ns / DT_KERNEL_NS)
        index = ticks // TICKS_KERNEL_PAR_PULSATION
        em, phase_12, h19, _tour = calculer_etat(index)
        cy = CycleTriniteSynchrone(
            index_pulsation_continue=index,
            phase_trinite_12=phase_12,
            harmonique_base_19=h19,
            pulsation_dt_hz=CYCLE_DT_KERNEL,
            composante_dx_solaire=CYCLE_DX_SOLAIRE,
            composante_dy_lunaire=CYCLE_DY_LUNAIRE,
            composante_dz_quantique=CYCLE_DZ_QUANTIQUE,
            continuité_sans_arret=True,
            horodatage_iso=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ticks_kernel_ecoules=ticks,
            origine_noyau=self.origine_noyau,
        )
        with self._verrou:
            self.etat_matiere, self.dernier_cycle = em, cy
        return em, cy

    def battre(self, pas: int = 1) -> Tuple[EtatMatiereMatricielle, CycleTriniteSynchrone]:
        """Compatibilité : équivaut à lire(). `pas` est ignoré."""
        return self.lire()

    @property
    def tour_trinite_rang(self) -> int:
        return self.dernier_cycle.index_pulsation_continue // PPCM_CYCLES_TRINITE

    @property
    def compteur_pulsations(self) -> int:
        return self.dernier_cycle.index_pulsation_continue

    def lien_avec_noyau(self) -> Dict[str, Any]:
        """Expose le lien horloge ↔ noyau COMPLEXE (zéro → expansion)."""
        return {
            "horloge": "HorlogeLogiqueMatriceMizan",
            "deduite_de": "MatriceLogiqueComplexe.calculer_cycles_trinite_depuis_zero",
            "point_zero": "COMPLEXE = LA TABLE",
            "trajectoire": "ZERO_VERS_EXPANSION",
            "constantes": {
                "dx": CYCLE_DX_SOLAIRE,
                "dy": CYCLE_DY_LUNAIRE,
                "dz": CYCLE_DZ_QUANTIQUE,
                "dt": CYCLE_DT_KERNEL,
                "periode_dt_ns": DT_KERNEL_NS,
                "phases": f"0..{PPCM_CYCLES_TRINITE - 1}",
                "harmonique": f"-{AMPLITUDE_HARMONIQUE}..+{AMPLITUDE_HARMONIQUE}",
                "base_h": BASE_HARMONIQUE,
            },
            "q_degre_noyau": {
                "Q_mecois": Q_DEGRE_MECOIS,
                "Q_medinois": Q_DEGRE_MEDINOIS,
                "note": "Q° déduits de LA TABLE — distincts de ±313 / M=24434",
            },
            "matiere_distincte": {
                "poles": (POLE_NEGATIF_MATIERE, POLE_POSITIF_MATIERE),
                "ancre_M": ANCRE_M_MATIERE,
            },
            "pas_valeurs_arbitraires": True,
            "snapshot_deduction": {
                k: v for k, v in _HORLOGE_NOYAU.items() if k != "brut_noyau"
            },
        }

    def synchroniser_aux_cinq_familles(self) -> Dict[str, Any]:
        em, cy = self.lire()
        sync = synchroniser_etats_matiere_aux_cinq_familles(em.charge_polarite, em.ancre_substance_m)
        return {
            "etat_matiere": asdict(em),
            "phase_trinite_12": cy.phase_trinite_12,
            "sync_cinq_familles": asdict(sync),
            "complexe_est_la_table": True,
            "origine_noyau": self.origine_noyau,
        }

    def obtenir_perception_unifiee(self) -> Dict[str, Any]:
        """Synthèse matière + cycles (horloge noyau) + Q° + sync 5 familles."""
        em, cy = self.lire()
        sync = synchroniser_etats_matiere_aux_cinq_familles(em.charge_polarite, em.ancre_substance_m)
        return {
            "doctrine": (
                "Horloge déduite du noyau COMPLEXE (point zéro → expansion). "
                "Matière ±313/M, Q° 2304/1536 et cycles dx/dy/dz/dt sont dissociés."
            ),
            "lien_noyau": self.lien_avec_noyau(),
            "etat_de_matiere_matricielle": asdict(em),
            "cycle_dynamique_trinite": asdict(cy),
            "q_degre": {"mecois_⊕": Q_DEGRE_MECOIS, "medinois_⊗": Q_DEGRE_MEDINOIS},
            "synchronisation_cinq_familles": asdict(sync),
            "periode_pulsation_ns": PERIODE_PULSATION_NS,
            "source_temps_lecture": "time.monotonic_ns (porte physique ; constantes = noyau)",
            "statut_flux": "CONTINUITÉ FLUIDE SANS AUCUN ARRÊT BLOQUANT",
        }


# Instance résidente unique
HORLOGE_LOGIQUE = HorlogeLogiqueMatriceMizan()

# Aliases de compatibilité
C_MECQUOISE = POLARITE_C_MATIERE  # magnitude matière Terre — PAS Q°
M_MEDINOISE = ANCRE_M_MATIERE     # ancre substance — PAS Q°
PPCM_ROUES = PPCM_CYCLES_TRINITE
HORLOGE_DEDUITE_DU_NOYAU = _HORLOGE_NOYAU


if __name__ == "__main__":
    lien = HORLOGE_LOGIQUE.lien_avec_noyau()
    print("=== HORLOGE DÉDUITE DU NOYAU COMPLEXE ===")
    print(f"Origine : {lien['point_zero']} | trajectoire {lien['trajectoire']}")
    print(f"dx={CYCLE_DX_SOLAIRE} dy={CYCLE_DY_LUNAIRE} dz={CYCLE_DZ_QUANTIQUE}")
    print(f"dt={CYCLE_DT_KERNEL} | phases 0..11 | h19 -9..+9")
    print(f"Q° mécois={Q_DEGRE_MECOIS} Q° médinois={Q_DEGRE_MEDINOIS}")
    for _ in range(2):
        em, cy = HORLOGE_LOGIQUE.lire()
        print(
            f"Pulsation {cy.index_pulsation_continue:02d} | "
            f"Phase {cy.phase_trinite_12}/11 | h19={cy.harmonique_base_19:+d} | "
            f"Pôle {em.charge_polarite:+d} | noyau={cy.origine_noyau}"
        )
