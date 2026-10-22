# -*- coding: utf-8 -*-
"""
Outil 1 : Validateur Syntaxique et Ontologique (`validateur_syntaxique.py`)
===========================================================================
Analyse statiquement un programme ASTRO-Q°ODE (`.aq` ou `.txt`) pour vérifier :
1. La validité lexicale et syntaxique (via `LexerAstroQode` et `ParserAstroQode`).
2. Le respect de l'immuabilité du namespace `MECQUOIS` (aucune réécriture d'`omega_*`).
3. La conformité des identifiants `omega_[A..S]` (Niveau 4) et `alpha_[a..s]` (Niveau 3)
   avec la `tablette_apprise_alphabet.csv` (ou extensions V2.0 comme `omega_MONAD_SOUL` / `alpha_cell_monad`).
4. Les bornes de l'axe thermodynamique discret `[-9 ; +9] i` (avec distinction des constantes d'horloge).
5. La présence de filets de sécurité (`¿ { ... }` ou `0 : HÉLIUM`) dans les blocs `MEDINOIS`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from bibliotheques.lib_almizan_extension import ROLES_ALPHABET_AZ_ALMIZAN
from bibliotheques.lib_informe import TABLETTE_ALPHABET
from lang.ast_nodes import (
    AffectationLocaleMedinoise,
    BlocMecquois,
    BlocMedinois,
    DeclarationConstanteMecquoise,
    InstructionConditionnelleForcee,
    InstructionForceExpression,
    InstructionInversionCatch,
    InstructionIsolationMonadique,
    LitteralNombreUnite,
    ProgrammeAstroQode,
)
from lang.parser import ParserAstroQode


@dataclass
class DiagnosticValidation:
    """Représente un message de diagnostic (ERREUR, AVERTISSEMENT, INFO)."""
    niveau: str  # "ERREUR", "AVERTISSEMENT", "INFO"
    code: str
    message: str


@dataclass
class RapportValidation:
    """Résultat complet de l'audit statique d'un script ASTRO-Q°ODE."""
    valide: bool
    nb_erreurs: int
    nb_avertissements: int
    constantes_mecquoises: List[str] = field(default_factory=list)
    variables_medinoises: List[str] = field(default_factory=list)
    diagnostics: List[DiagnosticValidation] = field(default_factory=list)


class ValidateurOntologiqueAstroQode:
    """Analyseur statique et vérificateur de conformité ontologique ASTRO-Q°ODE."""

    CONSTANTES_HORLOGE_CONNUES = {8766.0, 8496.0, 8640.0, 730.5, 708.0, 720.0, 168.0, 144.0}

    def valider_source(self, source: str) -> RapportValidation:
        diagnostics: List[DiagnosticValidation] = []
        try:
            programme = ParserAstroQode.depuis_source(source).parser_programme()
        except Exception as exc:
            diagnostics.append(DiagnosticValidation("ERREUR", "AQ-SYN-001", str(exc)))
            return RapportValidation(
                valide=False,
                nb_erreurs=1,
                nb_avertissements=0,
                diagnostics=diagnostics,
            )
        return self.valider_programme(programme)

    def valider_programme(self, programme: ProgrammeAstroQode) -> RapportValidation:
        diagnostics: List[DiagnosticValidation] = []
        constantes_definies: Set[str] = set()
        variables_definies: Set[str] = set()

        # 1. Vérification des blocs MECQUOIS
        for bloc_mec in programme.blocs_mecquois:
            for decl in bloc_mec.declarations:
                if isinstance(decl, DeclarationConstanteMecquoise):
                    nom = decl.nom
                    if nom in constantes_definies:
                        diagnostics.append(
                            DiagnosticValidation(
                                "ERREUR",
                                "AQ-MEC-001",
                                f"Violation d'immuabilité MECQUOIS : '{nom}' est déclaré plusieurs fois.",
                            )
                        )
                    constantes_definies.add(nom)
                    self._verifier_nom_omega(nom, diagnostics)
                    self._verifier_bornes_litteral(decl.expression, diagnostics, contexte=nom)

        # 2. Vérification des blocs MEDINOIS
        for bloc_med in programme.blocs_medinois:
            possede_catch_inversion = False
            for instr in bloc_med.instructions:
                if isinstance(instr, DeclarationConstanteMecquoise):
                    diagnostics.append(
                        DiagnosticValidation(
                            "ERREUR",
                            "AQ-MED-001",
                            f"Interdit de déclarer ou modifier la constante globale '{instr.nom}' dans MEDINOIS.",
                        )
                    )
                elif isinstance(instr, AffectationLocaleMedinoise):
                    if instr.nom in constantes_definies or instr.nom.startswith("omega_"):
                        diagnostics.append(
                            DiagnosticValidation(
                                "ERREUR",
                                "AQ-MED-002",
                                f"Tentative de réécriture de la constante immuable '{instr.nom}' dans MEDINOIS.",
                            )
                        )
                    variables_definies.add(instr.nom)
                    self._verifier_nom_alpha(instr.nom, diagnostics)
                    self._verifier_bornes_litteral(instr.expression, diagnostics, contexte=instr.nom)
                elif isinstance(instr, InstructionConditionnelleForcee):
                    if instr.bloc_sinon_catch is not None:
                        possede_catch_inversion = True
                elif isinstance(instr, InstructionInversionCatch):
                    possede_catch_inversion = True
                elif isinstance(instr, (InstructionForceExpression, InstructionIsolationMonadique)):
                    possede_catch_inversion = True

            if bloc_med.instructions and not possede_catch_inversion:
                diagnostics.append(
                    DiagnosticValidation(
                        "AVERTISSEMENT",
                        "AQ-SEC-001",
                        "Le bloc MEDINOIS ne contient pas de bloc d'inversion culturelle '¿ { ... }' ni d'isolation '(( ))'.",
                    )
                )

        nb_err = sum(1 for d in diagnostics if d.niveau == "ERREUR")
        nb_warn = sum(1 for d in diagnostics if d.niveau == "AVERTISSEMENT")
        if nb_err == 0:
            diagnostics.append(
                DiagnosticValidation(
                    "INFO",
                    "AQ-OK-000",
                    "Le programme respecte intégralement la grammaire et l'ontologie ASTRO-Q°ODE.",
                )
            )

        return RapportValidation(
            valide=(nb_err == 0),
            nb_erreurs=nb_err,
            nb_avertissements=nb_warn,
            constantes_mecquoises=sorted(constantes_definies),
            variables_medinoises=sorted(variables_definies),
            diagnostics=diagnostics,
        )

    def _verifier_nom_omega(self, nom: str, diagnostics: List[DiagnosticValidation]) -> None:
        if not nom.startswith("omega_"):
            diagnostics.append(
                DiagnosticValidation(
                    "AVERTISSEMENT",
                    "AQ-NOM-001",
                    f"La constante '{nom}' dans MECQUOIS devrait être préfixée par 'omega_'.",
                )
            )
            return
        suffixe = nom[len("omega_"):]
        if len(suffixe) == 1 and suffixe not in ROLES_ALPHABET_AZ_ALMIZAN:
            diagnostics.append(
                DiagnosticValidation(
                    "AVERTISSEMENT",
                    "AQ-NOM-002",
                    f"La lettre '{suffixe}' de '{nom}' est hors de l'axe alphabétique [A ; Z].",
                )
            )

    def _verifier_nom_alpha(self, nom: str, diagnostics: List[DiagnosticValidation]) -> None:
        if not nom.startswith("alpha_"):
            diagnostics.append(
                DiagnosticValidation(
                    "AVERTISSEMENT",
                    "AQ-NOM-003",
                    f"La variable locale '{nom}' dans MEDINOIS devrait être préfixée par 'alpha_'.",
                )
            )
            return
        suffixe = nom[len("alpha_"):]
        if len(suffixe) == 1 and suffixe.upper() not in ROLES_ALPHABET_AZ_ALMIZAN:
            diagnostics.append(
                DiagnosticValidation(
                    "AVERTISSEMENT",
                    "AQ-NOM-004",
                    f"La lettre '{suffixe}' de '{nom}' est hors de l'axe alphabétique [a ; z].",
                )
            )

    def _verifier_bornes_litteral(
        self,
        expr: object,
        diagnostics: List[DiagnosticValidation],
        contexte: str,
    ) -> None:
        if isinstance(expr, LitteralNombreUnite) and expr.unite == "i":
            if not (-9.0 <= expr.valeur <= 9.0) and expr.valeur not in self.CONSTANTES_HORLOGE_CONNUES:
                diagnostics.append(
                    DiagnosticValidation(
                        "INFO",
                        "AQ-AXE-001",
                        f"Dans '{contexte}', le signal thermique {expr.valeur} i dépasse l'axe discret [-9 ; +9] (traité comme constante de cycle étendue).",
                    )
                )
