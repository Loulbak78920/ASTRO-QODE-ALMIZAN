# -*- coding: utf-8 -*-
"""
Système de Types et Valeurs d'Exécution (Runtime Values) d'ASTRO-Q°ODE
======================================================================
Implémente les objets manipulés par la Machine Virtuelle Biomécanique :
- `SignalKelvin`      : Entier ou flottant thermique avec suffixe `i` (Unité : Kelvin, axe [-9 ; +9] ou cycle).
- `EnergieJoules`     : Flottant énergétique avec suffixe `I` (Unité : Joules).
- `EtatHeliumInerte`  : L'Origine Inerte `0 : HÉLIUM` (Forme 0, purge et repos absolu).
- `EnsembleContexte`  : Union de signaux, d'énergies et de cycles temporels (ex: `[dx U dy U dz]`).
- `FonctionLambdaAstro` : Fermeture fonctionnelle (`lambda x { ... }`) pour la transcription monadique `>>=`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Sequence, Union

from bibliotheques.lib_informe import QubitInforme
from bibliotheques.lib_physique import LES_14_FORMES, FormeMatiereCode, obtenir_forme_matiere


class ValeurAstro:
    """Classe racine de toutes les valeurs manipulées au runtime ASTRO-Q°ODE."""

    def valeur_numerique(self) -> float:
        return 0.0

    def est_veridique(self) -> bool:
        return True


@dataclass(frozen=True)
class SignalKelvin(ValeurAstro):
    """
    Niveau 1 (Signal / Thermodynamique) : Valeur dotée du suffixe `i` (Kelvin).
    Sur l'axe discret de base, appartient à [-9 ; +9], mais peut aussi représenter
    une constante temporelle solaire comme `8766 i`.
    """
    valeur: float

    @property
    def est_dans_axe_discret(self) -> bool:
        return -9.0 <= self.valeur <= 9.0

    @property
    def est_nul_helium(self) -> bool:
        return abs(self.valeur) < 1e-12

    def valeur_numerique(self) -> float:
        return float(self.valeur)

    def est_veridique(self) -> bool:
        return not self.est_nul_helium

    def vers_qubit_bloch(self) -> QubitInforme:
        return QubitInforme.depuis_echelon_thermique(int(round(self.valeur)))

    def forme_matiere(self) -> FormeMatiereCode:
        if self.est_nul_helium:
            return LES_14_FORMES[0]
        idx = int(abs(round(self.valeur)))
        return obtenir_forme_matiere(idx if idx <= 13 else (idx % 13) + 1)

    def __repr__(self) -> str:
        if float(self.valeur).is_integer():
            v = int(self.valeur)
            prefixe = f"+{v}" if v > 0 else str(v)
            return f"{prefixe} i"
        prefixe = f"+{self.valeur}" if self.valeur > 0 else str(self.valeur)
        return f"{prefixe} i"


@dataclass(frozen=True)
class EnergieJoules(ValeurAstro):
    """
    Niveau 2 (Énergie / Cinétique) : Flottant doté du suffixe `I` (Joules).
    """
    valeur: float

    def valeur_numerique(self) -> float:
        return float(self.valeur)

    def est_veridique(self) -> bool:
        return abs(self.valeur) >= 1e-12

    def __repr__(self) -> str:
        if float(self.valeur).is_integer():
            v = int(self.valeur)
            prefixe = f"+{v}" if v > 0 else str(v)
            return f"{prefixe} I"
        prefixe = f"+{self.valeur}" if self.valeur > 0 else str(self.valeur)
        return f"{prefixe} I"


@dataclass(frozen=True)
class EtatHeliumInerte(ValeurAstro):
    """
    Index 0 des 14 Formes : `0 : HÉLIUM`.
    Origine inerte, repos absolu, purge mémoire (`return 0`).
    """
    code: str = "0 : HÉLIUM"

    def valeur_numerique(self) -> float:
        return 0.0

    def est_veridique(self) -> bool:
        return False

    def forme_matiere(self) -> FormeMatiereCode:
        return LES_14_FORMES[0]

    def __repr__(self) -> str:
        return "0 : HÉLIUM"


@dataclass(frozen=True)
class EnsembleContexte(ValeurAstro):
    """
    Niveau 3 & 4 (Topologique / Ensembliste) : Représente l'union `∪` de plusieurs
    signaux, énergies ou cycles temporels (ex: `omega_MONAD_SOUL = [dx U dy U dz]`).
    """
    elements: tuple = field(default_factory=tuple)

    @classmethod
    def depuis_sequence(cls, seq: Sequence[object]) -> "EnsembleContexte":
        aplatis: List[object] = []
        for item in seq:
            if isinstance(item, EnsembleContexte):
                aplatis.extend(item.elements)
            else:
                aplatis.append(item)
        return cls(elements=tuple(aplatis))

    def valeur_numerique(self) -> float:
        total = 0.0
        for el in self.elements:
            if isinstance(el, ValeurAstro):
                total += el.valeur_numerique()
            elif isinstance(el, (int, float)):
                total += float(el)
        return total

    def contient_ou_gouverne(self, candidat: object) -> bool:
        """
        Implémente la relation d'inclusion large `⊃` (Gouvernance Médinoise) :
        Un contexte ou une constante globale gouverne un signal local si :
        - Le signal n'est pas en état d'erreur / corruption, ET
        - Soit le signal fait partie des éléments, soit sa magnitude énergétique/thermique
          est englobée par la capacité totale du contexte ou de la constante globale.
        """
        if isinstance(candidat, EtatHeliumInerte):
            return True
        val_cand = (
            candidat.valeur_numerique()
            if isinstance(candidat, ValeurAstro)
            else (float(candidat) if isinstance(candidat, (int, float)) else 0.0)
        )
        return abs(val_cand) <= abs(self.valeur_numerique())

    def __repr__(self) -> str:
        interne = " ∪ ".join(repr(e) for e in self.elements)
        return f"[{interne}]"


@dataclass
class FonctionLambdaAstro(ValeurAstro):
    """Représente une fermeture `lambda param { ... }` exécutable par `>>=`."""
    parametre: str
    corps: list
    executer_callback: Callable[[object], object]

    def appeler(self, argument: object) -> object:
        return self.executer_callback(argument)

    def __repr__(self) -> str:
        return f"<lambda {self.parametre} {{...}}>"
