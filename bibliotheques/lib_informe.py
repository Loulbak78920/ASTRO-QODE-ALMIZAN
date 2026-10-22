# -*- coding: utf-8 -*-
"""
Couche 1 : Bibliothèque de l'Informe (`QUBITS8INFORME`)
=======================================================
Implémente fidèlement :
- `tablette_apprise_chiffres.csv` : Axe [-9 ; +9], État i (Kelvin / Thermodynamique) et État I (Joules / Cinétique).
- `tablette_apprise_alphabet.csv` : Correspondance bijective [-9 ; +9] <-> [A ; S] sur 4 états (a, A, alpha_, omega_).
- `tablette_apprise_ponctuation.csv` : 19 symboles typographiques sur 4 états (Simple, Double, Enclos, Inversé).
- `tablettes_apprise_opérateur.csv` : 9 axes d'opérateurs sur 3 états (Arithmétique, Logique/Booléen, Relationnel/Ensembliste).
- `Matrice de la Structure Logique Complexe.pdf` : Résolution croisée des 4 Familles d'Axes × 4 Niveaux d'États.
- `Qubit_informe.jpg` : Modèle de la sphère de Bloch |ψ⟩ = α|0⟩ + β|1⟩ avec longueur d'onde λ = 5.77e-11.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union


# ==============================================================================
# 1. TABLETTE APPRISE DES CHIFFRES (Axe [-9 ; +9])
# ==============================================================================

@dataclass(frozen=True)
class EntreeChiffre:
    """Représente un échelon sur l'axe numérique [-9 ; +9]."""
    valeur: int
    formatee: str
    etat_i_kelvin: str
    etat_I_joules: str


def _construire_tablette_chiffres() -> Dict[int, EntreeChiffre]:
    table: Dict[int, EntreeChiffre] = {}
    for v in range(-9, 10):
        prefixe = f"+{v}" if v > 0 else str(v)
        table[v] = EntreeChiffre(
            valeur=v,
            formatee=prefixe,
            etat_i_kelvin=f"{prefixe} i",
            etat_I_joules=f"{prefixe} I",
        )
    return table


TABLETTE_CHIFFRES: Dict[int, EntreeChiffre] = _construire_tablette_chiffres()


# ==============================================================================
# 2. TABLETTE APPRISE DE L'ALPHABET (Axe [A ; S] <-> [-9 ; +9])
# ==============================================================================

@dataclass(frozen=True)
class EntreeAlphabet:
    """Représente une lettre de l'axe [A ; S] couplée à sa valeur [-9 ; +9] et ses 4 états."""
    axe_chiffre: int
    lettre_base: str
    etat_1_minuscule: str       # Niveau 1 : 'a' .. 's'
    etat_2_majuscule: str       # Niveau 2 : 'A' .. 'S'
    etat_3_alpha_locale: str    # Niveau 3 : 'alpha_a' .. 'alpha_s' (MEDINOIS)
    etat_4_omega_globale: str   # Niveau 4 : 'omega_A' .. 'omega_S' (MECQUOIS)
    etat_i_kelvin: str
    etat_I_joules: str


def _construire_tablette_alphabet() -> Dict[str, EntreeAlphabet]:
    lettres = "ABCDEFGHIJKLMNOPQRS"  # 19 lettres exactes (-9 à +9)
    table: Dict[str, EntreeAlphabet] = {}
    for idx, lettre in enumerate(lettres):
        valeur = idx - 9
        prefixe = f"+{valeur}" if valeur > 0 else str(valeur)
        minuscule = lettre.lower()
        table[lettre] = EntreeAlphabet(
            axe_chiffre=valeur,
            lettre_base=lettre,
            etat_1_minuscule=minuscule,
            etat_2_majuscule=lettre,
            etat_3_alpha_locale=f"alpha_{minuscule}",
            etat_4_omega_globale=f"omega_{lettre}",
            etat_i_kelvin=f"{prefixe} i",
            etat_I_joules=f"{prefixe} I",
        )
    return table


TABLETTE_ALPHABET: Dict[str, EntreeAlphabet] = _construire_tablette_alphabet()

# Index inversé : chiffre [-9 ; +9] -> EntreeAlphabet
INDEX_CHIFFRE_VERS_ALPHABET: Dict[int, EntreeAlphabet] = {
    entree.axe_chiffre: entree for entree in TABLETTE_ALPHABET.values()
}


# ==============================================================================
# 3. TABLETTE APPRISE DE LA PONCTUATION (19 Symboles × 4 États)
# ==============================================================================

@dataclass(frozen=True)
class EntreePonctuation:
    """Représente un symbole typographique sur ses 4 états."""
    symbole_base: str
    etat_1_simple: str
    etat_2_double: str
    etat_3_enclos: str
    etat_4_inverse: str


def _construire_tablette_ponctuation() -> Dict[str, EntreePonctuation]:
    symboles = [
        "!", "?", ".", ",", ";", ":", "...", "-", "_",
        "@", "#", "$", "%", "&", "*", "+", "=", "/", "\\",
    ]
    inversions_speciales = {
        "!": "¡",
        "?": "¿",
        ".": "°",
    }
    table: Dict[str, EntreePonctuation] = {}
    for sym in symboles:
        inv = inversions_speciales.get(sym, f"« {sym} »")
        table[sym] = EntreePonctuation(
            symbole_base=sym,
            etat_1_simple=sym,
            etat_2_double=sym + sym,
            etat_3_enclos=f"({sym})",
            etat_4_inverse=inv,
        )
    return table


TABLETTE_PONCTUATION: Dict[str, EntreePonctuation] = _construire_tablette_ponctuation()


# ==============================================================================
# 4. TABLETTE APPRISE DES OPÉRATEURS (9 Axes × 3 États)
# ==============================================================================

@dataclass(frozen=True)
class EntreeOperateur:
    """Représente un axe d'opérateur selon ses 3 états."""
    nom_axe: str
    symbole_base: str
    etat_1_arithmetique: str
    etat_2_logique_booleen: str
    etat_3_relationnel_ensembliste: str
    description_ensembliste: str


TABLETTE_OPERATEURS: Dict[str, EntreeOperateur] = {
    "Addition": EntreeOperateur(
        nom_axe="Addition",
        symbole_base="+",
        etat_1_arithmetique="+",
        etat_2_logique_booleen="&&",
        etat_3_relationnel_ensembliste="∪",
        description_ensembliste="Union",
    ),
    "Soustraction": EntreeOperateur(
        nom_axe="Soustraction",
        symbole_base="-",
        etat_1_arithmetique="-",
        etat_2_logique_booleen="!",
        etat_3_relationnel_ensembliste="∖",
        description_ensembliste="Différence",
    ),
    "Multiplication": EntreeOperateur(
        nom_axe="Multiplication",
        symbole_base="x",
        etat_1_arithmetique="×",
        etat_2_logique_booleen="||",
        etat_3_relationnel_ensembliste="∩",
        description_ensembliste="Intersection",
    ),
    "Division": EntreeOperateur(
        nom_axe="Division",
        symbole_base="/",
        etat_1_arithmetique="÷",
        etat_2_logique_booleen="NAND",
        etat_3_relationnel_ensembliste="⊘",
        description_ensembliste="Division harmonique",
    ),
    "Egalite": EntreeOperateur(
        nom_axe="Égalité",
        symbole_base="=",
        etat_1_arithmetique="=",
        etat_2_logique_booleen="==",
        etat_3_relationnel_ensembliste="≡",
        description_ensembliste="Congruence",
    ),
    "Inegalite": EntreeOperateur(
        nom_axe="Inégalité",
        symbole_base="!=",
        etat_1_arithmetique="≠",
        etat_2_logique_booleen="!=",
        etat_3_relationnel_ensembliste="≢",
        description_ensembliste="Non congruence",
    ),
    "Superieur": EntreeOperateur(
        nom_axe="Supérieur",
        symbole_base=">",
        etat_1_arithmetique=">",
        etat_2_logique_booleen="&& >",
        etat_3_relationnel_ensembliste="⊃",
        description_ensembliste="Inclusion large (Gouvernance)",
    ),
    "Inferieur": EntreeOperateur(
        nom_axe="Inférieur",
        symbole_base="<",
        etat_1_arithmetique="<",
        etat_2_logique_booleen="&& <",
        etat_3_relationnel_ensembliste="⊂",
        description_ensembliste="Inclusion stricte",
    ),
    "Pourcentage": EntreeOperateur(
        nom_axe="Pourcentage",
        symbole_base="%",
        etat_1_arithmetique="%",
        etat_2_logique_booleen="XOR",
        etat_3_relationnel_ensembliste="‰",
        description_ensembliste="Pour mille",
    ),
}


# ==============================================================================
# 5. MATRICE DE LA STRUCTURE LOGIQUE COMPLEXE (4 Familles × 4 Niveaux)
# ==============================================================================

class MatriceLogiqueComplexe:
    """
    Synthétise les 4 familles d'axes (Numérique, Linguistique, Typographique, Algorithmique)
    sur les 4 niveaux d'états :
    - Niveau 1 : État de Base (Signal / Thermodynamique Kelvin / Minuscule / Unitaire / Arithmétique)
    - Niveau 2 : État d'Énergie / Force (Cinétique Joules / Majuscule / Doublement / Booléen)
    - Niveau 3 : État de Relation / Contexte (Variable locale alpha_ / Sandbox (x) / Ensembliste)
    - Niveau 4 : État Méta / Symétrie (Constante globale omega_ / Inversion culturelle ¿ ¡ ° «»)
    """

    FAMILLES = ("NUMERIQUE", "LINGUISTIQUE", "TYPOGRAPHIQUE", "ALGORITHMIQUE")

    @staticmethod
    def resoudre_chiffre(valeur: int, niveau: int = 1) -> str:
        """Résout un entier de [-9 ; +9] au niveau demandé (1: Kelvin 'i', 2: Joules 'I')."""
        if valeur not in TABLETTE_CHIFFRES:
            raise ValueError(f"Valeur {valeur} hors de l'axe discret [-9 ; +9].")
        entree = TABLETTE_CHIFFRES[valeur]
        if niveau == 1:
            return entree.etat_i_kelvin
        if niveau == 2:
            return entree.etat_I_joules
        if niveau == 3:
            return INDEX_CHIFFRE_VERS_ALPHABET[valeur].etat_3_alpha_locale
        if niveau == 4:
            return INDEX_CHIFFRE_VERS_ALPHABET[valeur].etat_4_omega_globale
        raise ValueError(f"Niveau {niveau} invalide (attendu: 1..4).")

    @staticmethod
    def resoudre_lettre(lettre: str, niveau: int = 1) -> str:
        """Résout une lettre de [A ; S] selon le niveau (1: a, 2: A, 3: alpha_a, 4: omega_A)."""
        cle = lettre.upper()
        if cle not in TABLETTE_ALPHABET:
            raise ValueError(f"Lettre '{lettre}' hors du domaine ontologique [A ; S].")
        entree = TABLETTE_ALPHABET[cle]
        if niveau == 1:
            return entree.etat_1_minuscule
        if niveau == 2:
            return entree.etat_2_majuscule
        if niveau == 3:
            return entree.etat_3_alpha_locale
        if niveau == 4:
            return entree.etat_4_omega_globale
        raise ValueError(f"Niveau {niveau} invalide (attendu: 1..4).")

    @staticmethod
    def chiffre_depuis_identifiant(identifiant: str) -> Optional[int]:
        """Retrouve la coordonnée [-9 ; +9] associée à un identifiant alpha_x ou omega_X."""
        if identifiant.startswith("alpha_") and len(identifiant) == 7:
            lettre = identifiant[-1].upper()
            if lettre in TABLETTE_ALPHABET:
                return TABLETTE_ALPHABET[lettre].axe_chiffre
        elif identifiant.startswith("omega_") and len(identifiant) == 7:
            lettre = identifiant[-1].upper()
            if lettre in TABLETTE_ALPHABET:
                return TABLETTE_ALPHABET[lettre].axe_chiffre
        elif len(identifiant) == 1 and identifiant.upper() in TABLETTE_ALPHABET:
            return TABLETTE_ALPHABET[identifiant.upper()].axe_chiffre
        return None

    @staticmethod
    def resoudre_ponctuation(symbole: str, niveau: int = 1) -> str:
        """Résout un symbole de ponctuation sur ses 4 états."""
        if symbole not in TABLETTE_PONCTUATION:
            raise ValueError(f"Symbole '{symbole}' absent de la tablette de ponctuation.")
        entree = TABLETTE_PONCTUATION[symbole]
        if niveau == 1:
            return entree.etat_1_simple
        if niveau == 2:
            return entree.etat_2_double
        if niveau == 3:
            return entree.etat_3_enclos
        if niveau == 4:
            return entree.etat_4_inverse
        raise ValueError(f"Niveau {niveau} invalide (attendu: 1..4).")

    @staticmethod
    def resoudre_operateur(axe_ou_symbole: str, niveau: int = 1) -> str:
        """Résout un opérateur selon son niveau (1: Arithmétique, 2: Booléen, 3: Ensembliste)."""
        cible: Optional[EntreeOperateur] = None
        for cle, entree in TABLETTE_OPERATEURS.items():
            if axe_ou_symbole in (
                cle,
                entree.nom_axe,
                entree.symbole_base,
                entree.etat_1_arithmetique,
                entree.etat_2_logique_booleen,
                entree.etat_3_relationnel_ensembliste,
            ):
                cible = entree
                break
        if cible is None:
            raise ValueError(f"Opérateur '{axe_ou_symbole}' inconnu dans la tablette.")
        if niveau == 1:
            return cible.etat_1_arithmetique
        if niveau == 2:
            return cible.etat_2_logique_booleen
        if niveau in (3, 4):
            return cible.etat_3_relationnel_ensembliste
        raise ValueError(f"Niveau {niveau} invalide (attendu: 1..4).")

    @classmethod
    def exporter_resume_complet(cls) -> Dict[str, object]:
        """Exporte la matrice 4x4 complète sous forme de dictionnaire sérialisable."""
        return {
            "axe_numerique": [
                {
                    "valeur": e.valeur,
                    "niveau_1_kelvin": e.etat_i_kelvin,
                    "niveau_2_joules": e.etat_I_joules,
                }
                for e in TABLETTE_CHIFFRES.values()
            ],
            "axe_linguistique": [
                {
                    "chiffre": e.axe_chiffre,
                    "lettre": e.lettre_base,
                    "niveau_1": e.etat_1_minuscule,
                    "niveau_2": e.etat_2_majuscule,
                    "niveau_3": e.etat_3_alpha_locale,
                    "niveau_4": e.etat_4_omega_globale,
                }
                for e in TABLETTE_ALPHABET.values()
            ],
            "axe_typographique": [
                {
                    "base": e.symbole_base,
                    "niveau_1_simple": e.etat_1_simple,
                    "niveau_2_double": e.etat_2_double,
                    "niveau_3_enclos": e.etat_3_enclos,
                    "niveau_4_inverse": e.etat_4_inverse,
                }
                for e in TABLETTE_PONCTUATION.values()
            ],
            "axe_algorithmique": [
                {
                    "axe": e.nom_axe,
                    "base": e.symbole_base,
                    "niveau_1_arithmetique": e.etat_1_arithmetique,
                    "niveau_2_booleen": e.etat_2_logique_booleen,
                    "niveau_3_ensembliste": e.etat_3_relationnel_ensembliste,
                }
                for e in TABLETTE_OPERATEURS.values()
            ],
        }


# ==============================================================================
# 6. SPHÈRE QUANTIQUE DE BLOCH (`Qubit_informe.jpg`)
# ==============================================================================

class QubitInforme:
    """
    Modélise le Qubit Informe sur la sphère de Bloch :
        |ψ⟩ = α|0⟩ + β|1⟩  avec |α|² + |β|² = 1
    Constante d'onde associée dans QUBITS8INFORME : λ = 5.77e-11 m.
    Permet de projeter n'importe quel signal thermique [-9 ; +9] i sur la sphère de Bloch.
    """

    LAMBDA_INFORME: float = 5.77e-11

    def __init__(self, alpha: complex = 1.0 + 0.0j, beta: complex = 0.0 + 0.0j) -> None:
        norme = math.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)
        if norme == 0:
            self.alpha = 1.0 + 0.0j
            self.beta = 0.0 + 0.0j
        else:
            self.alpha = alpha / norme
            self.beta = beta / norme

    @classmethod
    def depuis_echelon_thermique(cls, echelon: int, phase_joules: float = 0.0) -> "QubitInforme":
        """
        Construit un état |ψ⟩ à partir d'un échelon [-9 ; +9] (Kelvin) et d'une phase (Joules).
        -9 i -> |1⟩ pur (pôle sud thermique)
         0 i -> superposition équilibrée (|0⟩ + |1⟩)/√2 (équateur J / Hélium)
        +9 i -> |0⟩ pur (pôle nord thermique)
        """
        borne = max(-9.0, min(9.0, float(echelon)))
        # Angle polaire theta dans [0, pi] : +9 -> 0, 0 -> pi/2, -9 -> pi
        theta = (9.0 - borne) * (math.pi / 18.0)
        phi = phase_joules * (math.pi / 9.0)
        alpha = complex(math.cos(theta / 2.0), 0.0)
        beta = cmath.rect(math.sin(theta / 2.0), phi)
        return cls(alpha=alpha, beta=beta)

    @property
    def probabilite_0(self) -> float:
        return round(abs(self.alpha) ** 2, 6)

    @property
    def probabilite_1(self) -> float:
        return round(abs(self.beta) ** 2, 6)

    @property
    def est_superpose(self) -> bool:
        return 0.001 < self.probabilite_0 < 0.999

    def coordonnees_bloch(self) -> Tuple[float, float, float]:
        """Retourne le vecteur (x, y, z) sur la sphère unité de Bloch."""
        x = 2.0 * (self.alpha.conjugate() * self.beta).real
        y = 2.0 * (self.alpha.conjugate() * self.beta).imag
        z = abs(self.alpha) ** 2 - abs(self.beta) ** 2
        return (round(x, 6), round(y, 6), round(z, 6))

    def representation_ket(self) -> str:
        return (
            f"|ψ⟩ = ({self.alpha.real:+.4f}{self.alpha.imag:+.4f}j)|0⟩ "
            f"+ ({self.beta.real:+.4f}{self.beta.imag:+.4f}j)|1⟩ "
            f"[λ={self.LAMBDA_INFORME:.2e} m]"
        )
