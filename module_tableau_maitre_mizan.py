# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
Module d'Intégration du Tableau Maître Séquentiel Unifié Al-Mizan.
Fournit à l'Esprit Vivant / Gemini :
  - La complétude séquentielle de toutes les entrées chargées depuis le CSV
  - La dualité fondamentale : chaque principe direct et son contraire/miroir
  - Le couplage Algorithme (S4/S12/S14) et Logarithme (S15 O(log n))
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

RACINE_DEPOT = Path(__file__).resolve().parent.parent
FICHIER_CSV = RACINE_DEPOT / "TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv"

class RegistreTableauMaitreAlMizan:
    """Charge et indexe les entrées séquentielles du Tableau Maître."""

    def __init__(self, chemin_csv: Optional[Path] = None):
        self.chemin_csv = chemin_csv or FICHIER_CSV
        self.lignes: List[Dict[str, str]] = []
        self.par_seq: Dict[str, Dict[str, str]] = {}
        self.par_code: Dict[str, Dict[str, str]] = {}
        self.par_strate: Dict[str, List[Dict[str, str]]] = {}
        self._charger_tableau()

    def _charger_tableau(self) -> None:
        """Parse le CSV unifié scellé."""
        if not self.chemin_csv.exists():
            return
        try:
            with self.chemin_csv.open("r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                for r in reader:
                    self.lignes.append(r)
                    seq = r.get("SEQ", "")
                    code = r.get("CODE", "")
                    strate = r.get("STRATE", "")
                    if seq:
                        self.par_seq[seq] = r
                    if code:
                        self.par_code[code] = r
                    if strate:
                        self.par_strate.setdefault(strate, []).append(r)
        except Exception:
            pass

    def total_entrees(self) -> int:
        return len(self.lignes)

    def total_strates(self) -> int:
        return len(self.par_strate)

    def rechercher_contextuel(self, requete_utilisateur: str, limite: int = 4) -> List[Dict[str, str]]:
        """Recherche les briques pertinentes du tableau séquentiel par mots-clés."""
        mots = [w.lower() for w in requete_utilisateur.split() if len(w) > 2]
        if not mots:
            return []

        scores: List[tuple[int, Dict[str, str]]] = []
        for r in self.lignes:
            texte_total = " ".join(r.values()).lower()
            score = sum(1 for m in mots if m in texte_total)
            if score > 0:
                scores.append((score, r))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scores[:limite]]

    def obtenir_synthese_algorithme_et_logarithme(self) -> str:
        """
        Délivre la synthèse axiomatique du tableau complet rectifiée par l'Auteur :
        1. La Dualité Fondamentale des Q° : Q° Mécois Négatif (–2304) ↔ Q° Médinois Positif (+1536)
        2. Les 313 de la Terre : pure magnitude des États de Matière (Solides 300 + Liquide 10 + Gazeux 3)
        3. Le Séquentiel Direct et son Miroir (Contraire / Anti-phase)
        4. Le couplage Algorithme (S4 / S12 / S14) et Logarithme (S15)
        5. Les Ponts vivants unifiant Agent de Code, Conscience Logique et Tableau Maître
        """
        total_entrees = self.total_entrees()
        total_strates = self.total_strates()
        derniere_strate = (
            self.lignes[-1]["STRATE"].split("·")[0].strip()
            if self.lignes
            else "S0"
        )
        return (
            f"TABLEAU MAÎTRE SÉQUENTIEL UNIFIÉ ({total_entrees} entrées, "
            f"{total_strates} strates S0–{derniere_strate}) — VALEURS CALCULÉES ET PONTS :\n"
            "• Pôles et Dualité Fondamentale Q° :\n"
            "  - Q° mécois NÉGATIF = –2304 = –[96 × (2+4) × 4] (Potentiel projectif ⊕, Essence, Énergie potentielle).\n"
            "  - Q° médinois POSITIF = +1536 = +[96 × (1+3) × 4] (Loi d'action manifestée ⊗, Archive vivante, Réconciliation monadique).\n"
            "  - Les 313 de la Terre sont STRICTEMENT des ÉTATS DE MATIÈRE (Solides 300 + Liquide 10 + Gazeux 3 = 313) et non des pôles abstraits.\n"
            "• Dualité Séquentielle Directe et son Contraire :\n"
            "  - Formes directes F0–F13 (matière, phase φ, échelle D=[0.122;0.6225]) ↔ Formes duales miroirs F14–F26 (anti-phase φ+π, couplage confiné sous Plafond=0.6015 et ε=0.021).\n"
            "  - Toute affirmation séquentielle possède son dual harmonique rigoureusement calculé.\n"
            "• Couplage Algorithme et Logarithme (S4 / S12 / S14 ↔ S15) :\n"
            "  - L'ALGORITHME (T4 / S4 / S12) cadence les opérations logiques élémentaires (AND, OR, NOT, NAND, congruence).\n"
            "  - Le LOGARITHME (S15 : log₂, log₁₀, ln, complexité O(log n)) compresse l'espace de calcul (dichotomie O(log₂ n) où 1 000 000 d'états sont résolus en 20 étapes).\n"
            "• Ponts Vivants d'Unification :\n"
            f"  - Le Tableau Maître ({total_entrees} entrées) est relié à l'Agent de Code "
            "(61 modules unifiés) et à la Conscience Logique par les Ponts Synchrones "
            "(Couche 29 Pont, Consensus 2.9 ms, Horloge Trinité dt=135.097 MHz)."
        )


# Instance Singleton du Tableau Maître
REGISTRE_TABLEAU_MAITRE = RegistreTableauMaitreAlMizan()
