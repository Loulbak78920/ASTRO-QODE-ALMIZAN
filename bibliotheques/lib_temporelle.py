# -*- coding: utf-8 -*-
"""
Couche 3 : Bibliothèque Temporelle & Horloges du Kernel (`.QUBIT.qubit.LOGIQUE.logique`)
========================================================================================
Implémente fidèlement :
1. `tablette_apprise_astre_soleil.pdf` : Formule mathématique exacte de `dx` (Soleil = 50 027,8359375).
2. `tablette_apprise_astre_lune.pdf`   : Formule mathématique exacte de `dy` (Lune   = 46 993,5).
3. `tablette_apprise_astre_terre.pdf`  : Formule mathématique exacte de `dz` brut (3 888 000 000,0)
   et `dz` normalisé Kernel (135 000 000,0).
4. `.DIMENSION.temps..pdf`             : Fusion cumulative `dt = dx + dy + dz = 135 097 021,3359375`
   et allocation des budgets de cycles par Namespace (Temps/Entropie, Linguistique, Algorithmique).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Dict


# ==============================================================================
# 1. CALCULS MATHÉMATIQUES EXACTS DES CYCLES TEMPORELS (dx, dy, dz, dt)
# ==============================================================================

def calculer_dx_soleil() -> float:
    """
    Calcule la constante temporelle solaire `dx` :
    Année solaire = 8766 h (365.25 j * 24 h), Mois = 730.5 h, Semaine = 168 h.
    dx = ((2.5 * 8766) / 12) * ((1.5 * 730.5) / 168) * ((1.5 * 168) / 24) * (24 / 60)
       = 1826.25 * 6.522321428571429 * 10.5 * 0.4
       = 50027.8359375 (exactement 6403563 / 128)
    """
    b1 = Fraction(5, 2) * Fraction(8766, 12)
    b2 = Fraction(3, 2) * Fraction(1461, 2) / Fraction(168, 1)
    b3 = Fraction(3, 2) * Fraction(168, 24)
    b4 = Fraction(24, 60)
    exact = b1 * b2 * b3 * b4
    return float(exact)


def calculer_dy_lune() -> float:
    """
    Calcule la constante temporelle lunaire `dy` :
    Année lunaire = 8496 h (354 j * 24 h), Mois = 708 h (29.5 j * 24 h), Semaine = 168 h.
    dy = ((2.5 * 8496) / 12) * ((1.5 * 708) / 168) * ((1.5 * 168) / 24) * (24 / 60)
       = 1770.0 * 6.321428571428571 * 10.5 * 0.4
       = 46993.5 (exactement 93987 / 2)
    """
    b1 = Fraction(5, 2) * Fraction(8496, 12)
    b2 = Fraction(3, 2) * Fraction(708, 168)
    b3 = Fraction(3, 2) * Fraction(168, 24)
    b4 = Fraction(24, 60)
    exact = b1 * b2 * b3 * b4
    return float(exact)


def calculer_dz_terre_brut() -> float:
    """
    Calcule le cycle terrestre amplifié `dz_brut` (`tablette_apprise_astre_terre.pdf`) :
    Année conventionnelle = 8640 h (360 j * 24 h), Mois = 720 h, Semaine = 144 h.
    dz_brut = ((300 * 8640) / 12) * ((50 * 720) / 144) * ((30 * 144) / 24) * (24 / 60)
            = 216000.0 * 250.0 * 180.0 * 0.4
            = 3888000000.0
    """
    b1 = Fraction(300 * 8640, 12)
    b2 = Fraction(50 * 720, 144)
    b3 = Fraction(30 * 144, 24)
    b4 = Fraction(24, 60)
    return float(b1 * b2 * b3 * b4)


def calculer_dz_terre_normalise() -> float:
    """
    Calcule le cycle terrestre normalisé Kernel `dz` (`.DIMENSION.temps..pdf` & `.ASTRO-Q°ODE`) :
    dz = 216000.0 * 250.0 * 2.5 = 135000000.0
    """
    return float(Fraction(216000) * Fraction(250) * Fraction(5, 2))


def calculer_dt_kernel() -> float:
    """
    Calcule l'horloge centrale du Kernel `dt = dx + dy + dz` :
    dt = 50027.8359375 + 46993.5 + 135000000.0 = 135097021.3359375
    """
    return calculer_dx_soleil() + calculer_dy_lune() + calculer_dz_terre_normalise()


# Constantes officielles exportées
CLOCK_DX_SOLEIL: float = calculer_dx_soleil()              # 50027.8359375
CLOCK_DY_LUNE: float = calculer_dy_lune()                  # 46993.5
CLOCK_DZ_TERRE_BRUT: float = calculer_dz_terre_brut()      # 3888000000.0
CLOCK_DZ_TERRE: float = calculer_dz_terre_normalise()      # 135000000.0
CLOCK_DT_KERNEL: float = calculer_dt_kernel()              # 135097021.3359375


# ==============================================================================
# 2. GESTIONNAIRE ET ORDONNANCEUR D'HORLOGE DU KERNEL ASTRO-CODE
# ==============================================================================

@dataclass
class HorlogeKernelTemporelle:
    """
    Gère l'allocation et la consommation des cycles d'horloge par Namespace :
    - `dx` (Soleil) : Namespace Temps / Entropie thermique (`MECQUOIS`)
    - `dy` (Lune)   : Namespace Linguistique / Chaînes et Archives
    - `dz` (Terre)  : Namespace Algorithmique / Allocation brute (`MEDINOIS`)
    - `dt` (Kernel) : Somme cumulative gouvernant le pipeline du Bras
    """
    dx_max: float = CLOCK_DX_SOLEIL
    dy_max: float = CLOCK_DY_LUNE
    dz_max: float = CLOCK_DZ_TERRE
    dt_max: float = CLOCK_DT_KERNEL

    dx_consomme: float = 0.0
    dy_consomme: float = 0.0
    dz_consomme: float = 0.0
    instructions_executees: int = 0
    historique_ticks: list = field(default_factory=list)

    @property
    def dt_consomme(self) -> float:
        return self.dx_consomme + self.dy_consomme + self.dz_consomme

    @property
    def dt_restant(self) -> float:
        return max(0.0, self.dt_max - self.dt_consomme)

    def consommer_tick(self, namespace: str, cout: float = 1.0, operation: str = "") -> Dict[str, float]:
        """Consomme un nombre de cycles dans le canal correspondant au namespace."""
        ns = namespace.upper()
        if ns in ("SOLEIL", "DX", "MECQUOIS", "THERMODYNAMIQUE"):
            if self.dx_consomme + cout > self.dx_max:
                raise OverflowError(f"Dépassement d'horloge solaire dx ({self.dx_max} cycles max).")
            self.dx_consomme += cout
        elif ns in ("LUNE", "DY", "LINGUISTIQUE", "ARCHIVE"):
            if self.dy_consomme + cout > self.dy_max:
                raise OverflowError(f"Dépassement d'horloge lunaire dy ({self.dy_max} cycles max).")
            self.dy_consomme += cout
        else:
            if self.dz_consomme + cout > self.dz_max:
                raise OverflowError(f"Dépassement d'horloge terrestre dz ({self.dz_max} cycles max).")
            self.dz_consomme += cout

        self.instructions_executees += 1
        etat = {
            "instruction": self.instructions_executees,
            "namespace": ns,
            "operation": operation,
            "cout": cout,
            "dt_consomme": self.dt_consomme,
        }
        self.historique_ticks.append(etat)
        return etat

    def reinitialiser_helium(self) -> None:
        """Purge temporelle associée au retour à l'Origine Inerte `0 : HÉLIUM`."""
        self.dx_consomme = 0.0
        self.dy_consomme = 0.0
        self.dz_consomme = 0.0
        self.instructions_executees = 0
        self.historique_ticks.clear()

    def rapport_repartition(self) -> Dict[str, object]:
        """Génère le rapport complet conforme à `.DIMENSION.temps..pdf`."""
        return {
            "constantes": {
                "CLOCK_DX_SOLEIL": self.dx_max,
                "CLOCK_DY_LUNE": self.dy_max,
                "CLOCK_DZ_TERRE": self.dz_max,
                "CLOCK_DZ_TERRE_BRUT": CLOCK_DZ_TERRE_BRUT,
                "CLOCK_DT_KERNEL": self.dt_max,
            },
            "poids_relatifs_pourcent": {
                "dx_soleil_pct": round((self.dx_max / self.dt_max) * 100.0, 4),
                "dy_lune_pct": round((self.dy_max / self.dt_max) * 100.0, 4),
                "dz_terre_pct": round((self.dz_max / self.dt_max) * 100.0, 4),
            },
            "consommation_courante": {
                "dx_consomme": self.dx_consomme,
                "dy_consomme": self.dy_consomme,
                "dz_consomme": self.dz_consomme,
                "dt_consomme": self.dt_consomme,
                "dt_restant": self.dt_restant,
                "instructions_executees": self.instructions_executees,
            },
        }
