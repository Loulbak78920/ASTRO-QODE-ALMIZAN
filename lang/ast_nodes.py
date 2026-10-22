# -*- coding: utf-8 -*-
"""
Arbre Syntaxique Abstrait (AST) du Langage ASTRO-Q°ODE (V1.0 & V2.0)
====================================================================
Modélise l'ensemble des constructions ontologiques (`MECQUOIS`), législatives (`MEDINOIS`),
temporelles (`SET CLOCK_...`) et monadiques (`Monad`, `>>=`, `lambda`, `(( ))`, `??`, `¿`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


# ==============================================================================
# 1. NŒUDS D'EXPRESSIONS
# ==============================================================================

class ExpressionAstro:
    """Classe de base de toutes les expressions ASTRO-Q°ODE."""


@dataclass
class LitteralNombreUnite(ExpressionAstro):
    """Littéral numérique avec unité optionnelle ('i' Kelvin, 'I' Joules, ou scalaire pur)."""
    valeur: float
    est_entier: bool
    unite: Optional[str] = None  # 'i' (Kelvin), 'I' (Joules) ou None


@dataclass
class LitteralHeliumInerte(ExpressionAstro):
    """L'Origine Inerte `0 : HÉLIUM` (Index 0 des 14 Formes)."""
    libelle: str = "0 : HÉLIUM"


@dataclass
class LitteralChaine(ExpressionAstro):
    """Chaîne de caractères."""
    valeur: str


@dataclass
class ReferenceVariable(ExpressionAstro):
    """Référence à `omega_*`, `alpha_*`, `dx`, `dy`, `dz`, `dt` ou paramètre de lambda."""
    nom: str


@dataclass
class ExpressionEnsemble(ExpressionAstro):
    """Ensemble ou contexte `[dx U dy U dz]` ou `[a, b, c]`."""
    elements: List[ExpressionAstro]
    operateur_interne: str = "∪"


@dataclass
class ExpressionMonad(ExpressionAstro):
    """Constructeur monadique `Monad(expr)` (V2.0)."""
    interne: ExpressionAstro


@dataclass
class ExpressionForme(ExpressionAstro):
    """Constructeur d'une des 14 Formes de la Matière du Code `Forme(0..13)`."""
    index_expr: ExpressionAstro


@dataclass
class ExpressionFusionPP(ExpressionAstro):
    """Appel de fusion proton-proton `fusion_pp(nb_noyaux_h)` (4H -> 1He)."""
    nb_noyaux_expr: ExpressionAstro


@dataclass
class ExpressionAppelAlmizan(ExpressionAstro):
    """Appel d'une primitive d'extension Al-Mizan V3.0 (`clamp_mizan`, `sphere_holographique`, `triade_ibit`, `cycle_15_phases`)."""
    nom_primitive: str
    argument: ExpressionAstro


@dataclass
class ExpressionLambda(ExpressionAstro):
    """Expression fonctionnelle `lambda param { instructions... }` (V2.0)."""
    parametre: str
    corps: List["InstructionAstro"]


@dataclass
class ExpressionUnaire(ExpressionAstro):
    """Opération unaire (`!expr`, `-expr`, `+expr`)."""
    operateur: str
    operande: ExpressionAstro


@dataclass
class ExpressionBinaire(ExpressionAstro):
    """
    Opération binaire couvrant les 3 états d'opérateurs (`+`, `-`, `*`, `/`,
    `&&`, `||`, `==`, `!=`, `∪`, `∖`, `∩`, `⊘`, `≡`, `≢`, `⊃`, `⊂`, `‰`)
    ainsi que la transcription monadique `>>=`.
    """
    gauche: ExpressionAstro
    operateur: str
    droite: ExpressionAstro


@dataclass
class ExpressionSandbox(ExpressionAstro):
    """
    Conteneur d'isolation sémantique :
    - `niveau = 1` : `( expr )` (Sandbox standard sur l'Axe Bêta scapulaire)
    - `niveau = 2` : `(( expr ))` (Isolation Monadique Absolue)
    """
    interne: ExpressionAstro
    niveau: int = 1


# ==============================================================================
# 2. NŒUDS D'INSTRUCTIONS ET DE BLOCS
# ==============================================================================

class InstructionAstro:
    """Classe de base de toutes les instructions ASTRO-Q°ODE."""


@dataclass
class DirectiveHorloge(InstructionAstro):
    """Directive Kernel : `SET CLOCK_DX_SOLEIL = 50027.8359375`."""
    nom_horloge: str
    valeur: float


@dataclass
class DeclarationSpecification(InstructionAstro):
    """Bloc déclaratif de spécification (`TYPES [...]`, `PROPRIÉTÉS [...]`, etc.)."""
    contenu: str


@dataclass
class DeclarationConstanteMecquoise(InstructionAstro):
    """Déclaration immuable dans `MECQUOIS { omega_X = expr }` (Verrou Auriculaire Doigt 4)."""
    nom: str
    expression: ExpressionAstro


@dataclass
class AffectationLocaleMedinoise(InstructionAstro):
    """Affectation d'une variable locale dans `MEDINOIS { alpha_x = expr }` (Pointeur Index Doigt 1)."""
    nom: str
    expression: ExpressionAstro
    forcee: bool = False


@dataclass
class InstructionConditionnelleForcee(InstructionAstro):
    """
    Loi exécutive Médinoise avec modificateur de force `??` (Majeur Doigt 2) :
        `(condition) ?? { ... } ¿ { ... }`
    """
    condition: ExpressionAstro
    bloc_alors: List[InstructionAstro]
    bloc_sinon_catch: Optional[List[InstructionAstro]] = None


@dataclass
class InstructionForceExpression(InstructionAstro):
    """
    Exécution impérative forcée d'une expression (notamment transcription monadique) :
        `( alpha_cell_monad >>= (lambda signal { ... })) ??`
    """
    expression: ExpressionAstro


@dataclass
class InstructionInversionCatch(InstructionAstro):
    """
    Bloc d'inversion culturelle autonome `¿ { ... }` dans un bloc `MEDINOIS`,
    servant de gestionnaire d'exception / repli vers l'état neutre ou `0 : HÉLIUM`.
    """
    corps: List[InstructionAstro]


@dataclass
class InstructionIsolationMonadique(InstructionAstro):
    """Instruction d'isolation absolue `(( alpha_cell_monad ))`."""
    expression: ExpressionAstro


@dataclass
class InstructionRetour(InstructionAstro):
    """Instruction `return expr` (retour de fonction lambda ou ancre Pouce Doigt 0 `return 0`)."""
    expression: ExpressionAstro


@dataclass
class InstructionAfficher(InstructionAstro):
    """Instruction d'affichage / télémétrie `afficher(expr)`."""
    expression: ExpressionAstro


@dataclass
class BlocMecquois(InstructionAstro):
    """Namespace `MECQUOIS { ... }` : Paradigme déclaratif, ontologique et immuable."""
    declarations: List[InstructionAstro] = field(default_factory=list)


@dataclass
class BlocMedinois(InstructionAstro):
    """Namespace `MEDINOIS { ... }` : Paradigme impératif, législatif et exécutif."""
    instructions: List[InstructionAstro] = field(default_factory=list)


@dataclass
class ProgrammeAstroQode:
    """Racine de l'Arbre Syntaxique Abstrait (AST) d'un programme ASTRO-Q°ODE."""
    directives_horloge: List[DirectiveHorloge] = field(default_factory=list)
    metadonnees_spec: List[DeclarationSpecification] = field(default_factory=list)
    blocs_mecquois: List[BlocMecquois] = field(default_factory=list)
    blocs_medinois: List[BlocMedinois] = field(default_factory=list)
    toutes_instructions: List[InstructionAstro] = field(default_factory=list)
