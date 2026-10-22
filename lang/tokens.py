# -*- coding: utf-8 -*-
"""
Définition des Lexèmes (Tokens) du Langage ASTRO-Q°ODE (V1.0 & V2.0)
====================================================================
Couvre l'intégralité des symboles des 4 Tablettes Apprises (`QUBITS8INFORME`),
des directives d'horloge (`.QUBIT.qubit.LOGIQUE.logique`), des namespaces
`MECQUOIS` / `MEDINOIS` et de la Monade Suprême V2.0 (`.ASTRO-Q°ODE`).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Mots-clés de structure et paradigmes
    SET = auto()               # SET CLOCK_...
    MECQUOIS = auto()          # MECQUOIS { ... }
    MEDINOIS = auto()          # MEDINOIS { ... }
    MONAD = auto()             # Monad(...)
    LAMBDA = auto()            # lambda x { ... }
    RETURN = auto()            # return ...
    HELIUM = auto()            # HÉLIUM / HELIUM (dans 0 : HÉLIUM)
    FORME = auto()             # Forme(0..26) ou F0..F26
    AFFICHER = auto()          # afficher(...) / print(...)
    FUSION = auto()            # fusion_pp(...)
    CLAMP_MIZAN = auto()       # clamp_mizan(...)
    SPHERE_HOLO = auto()       # sphere_holographique(...)
    TRIADE_IBIT = auto()       # triade_ibit(...)
    CYCLE_15 = auto()          # cycle_15_phases(...)
    TIR_SCPI = auto()          # tir_scpi_5025(...)
    CAPTEUR_CRYO = auto()      # capteur_cryo_5026(...)
    EXEC_QASM = auto()         # executer_qasm_5030(...)
    SCELLER_SHA256 = auto()    # sceller_sha256(...)
    MATRICE_UNISSON = auto()   # matrice_unisson(...)
    VALEUR_OR = auto()         # valeur_or(...)
    VALEUR_ARGENT = auto()     # valeur_argent(...)

    # Blocs déclaratifs de spécification (compatibilité directe avec astro_q°ode_specification.txt)
    SPEC_BLOC = auto()         # TYPES [...], PROPRIÉTÉS [...], OPERATEURS_NIVEAU_3/4 [...]
    SPEC_META = auto()         # MODIFICATEUR_FORCE : "...", etc.

    # Identifiants et variables ontologiques
    OMEGA_CONST = auto()       # omega_A .. omega_S, omega_MONAD_SOUL
    ALPHA_VAR = auto()         # alpha_a .. alpha_s, alpha_cell_monad
    IDENTIFIANT = auto()       # dx, dy, dz, dt, CLOCK_..., paramètres de lambda

    # Littéraux numériques et chaînes
    NOMBRE = auto()            # Entier ou flottant (avec signe optionnel + ou -)
    UNITE_KELVIN = auto()      # Suffixe 'i' (Thermodynamique - Kelvin)
    UNITE_JOULES = auto()      # Suffixe 'I' (Cinétique - Joules)
    CHAINE = auto()            # "..."

    # Modificateurs typographiques et sécurité (Niveau 2, 3, 4)
    FORCE_DOUBLE = auto()      # ?? (Modificateur de force / Majeur Doigt 2)
    EXCLAM_DOUBLE = auto()     # !! (Intensité d'alerte)
    INVERSION_CATCH = auto()   # ¿  (Inversion culturelle / Catch d'exception)
    INVERSION_EXCLAM = auto()  # ¡  (Inversion d'alerte)
    DEGRE_QODE = auto()        # °  (Inversion du point '.')

    # Opérateurs Monadiques (V2.0)
    BIND_MONADE = auto()       # >>= (Transcription polymérase)

    # Opérateurs Niveau 1 (Arithmétique)
    PLUS = auto()              # +
    MOINS = auto()             # -
    FOIS = auto()              # * ou ×
    DIV = auto()               # / ou ÷
    MODULO = auto()            # %
    AFFECTATION = auto()       # =
    SUPERIEUR = auto()         # >
    INFERIEUR = auto()         # <

    # Opérateurs Niveau 2 (Logique / Booléen)
    ET_LOGIQUE = auto()        # && ou AND
    OU_LOGIQUE = auto()        # || ou OR
    NON_LOGIQUE = auto()       # ! ou NOT
    NAND_LOGIQUE = auto()      # NAND
    XOR_LOGIQUE = auto()       # XOR
    EGAL_LOGIQUE = auto()      # ==
    DIFF_LOGIQUE = auto()      # != ou ≠

    # Opérateurs Niveau 3 & 4 (Relationnel / Ensembliste / Topologique)
    UNION = auto()             # ∪ ou U (entre espaces) ou UNION
    DIFFERENCE_ENS = auto()    # ∖ ou DIFF
    INTERSECTION = auto()      # ∩ ou INTER
    DIV_HARMONIQUE = auto()    # ⊘ ou HDIV
    CONGRUENCE = auto()        # ≡ ou CONGR
    NON_CONGRUENCE = auto()    # ≢ ou NCONGR
    INCLUSION_LARGE = auto()   # ⊃ ou INCL (Gouvernance)
    INCLUSION_STRICTE = auto() # ⊂ ou STRICT
    POUR_MILLE = auto()        # ‰ ou PERMILLE
    OPLUS_KRONECKER = auto()   # ⊕ ou OPLUS (Calotte Haute Sphère Holographique)
    OTIMES_KRONECKER = auto()  # ⊗ ou OTIMES (Calotte Basse Sphère Holographique)

    # Délimiteurs et conteneurs Sandbox
    DOUBLE_PAREN_G = auto()    # (( (Ouverture d'isolation monadique absolue)
    DOUBLE_PAREN_D = auto()    # )) (Fermeture d'isolation monadique absolue)
    PAREN_G = auto()           # (  (Ouverture Sandbox Niveau 3)
    PAREN_D = auto()           # )  (Fermeture Sandbox Niveau 3)
    ACCOLADE_G = auto()        # {
    ACCOLADE_D = auto()        # }
    CROCHET_G = auto()         # [
    CROCHET_D = auto()         # ]
    GUILLEMET_FR_G = auto()    # «
    GUILLEMET_FR_D = auto()    # »
    DEUX_POINTS = auto()       # :
    POINT_VIRGULE = auto()     # ; (Verrou symétrique / Auriculaire Doigt 4)
    VIRGULE = auto()           # ,

    EOF = auto()


@dataclass(frozen=True)
class Token:
    """Représente un lexème localisé dans un fichier source ASTRO-Q°ODE."""
    type: TokenType
    valeur: str
    ligne: int
    colonne: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.valeur!r}, L{self.ligne}:C{self.colonne})"
