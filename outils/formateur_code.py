# -*- coding: utf-8 -*-
"""
Outil 2 : Formateur Canonique de Code ASTRO-Q°ODE (`formateur_code.py`)
=======================================================================
Normalise la présentation des scripts `.aq` :
- Aligne les directives `SET CLOCK_...`
- Normalise les alias d'opérateurs (`UNION` -> `∪`, `INCL` -> `⊃`, `STRICT` -> `⊂`)
- Indente proprement les blocs `MECQUOIS { ... }`, `MEDINOIS { ... }`, `?? { ... }`, `¿ { ... }`
  et les expressions `lambda`.
"""

from __future__ import annotations

from typing import List

from lang.ast_nodes import (
    AffectationLocaleMedinoise,
    BlocMecquois,
    BlocMedinois,
    DeclarationConstanteMecquoise,
    DeclarationSpecification,
    DirectiveHorloge,
    ExpressionAppelAlmizan,
    ExpressionAstro,
    ExpressionBinaire,
    ExpressionEnsemble,
    ExpressionForme,
    ExpressionFusionPP,
    ExpressionLambda,
    ExpressionMonad,
    ExpressionSandbox,
    ExpressionUnaire,
    InstructionAfficher,
    InstructionAstro,
    InstructionConditionnelleForcee,
    InstructionForceExpression,
    InstructionInversionCatch,
    InstructionIsolationMonadique,
    InstructionRetour,
    LitteralChaine,
    LitteralHeliumInerte,
    LitteralNombreUnite,
    ProgrammeAstroQode,
    ReferenceVariable,
)
from lang.parser import ParserAstroQode


class FormateurAstroQode:
    """Formateur canonique de code source ASTRO-Q°ODE."""

    def __init__(self) -> None:
        self.lignes: List[str] = []
        self.indentation: int = 0

    def _emettre(self, texte: str = "") -> None:
        if not texte:
            self.lignes.append("")
        else:
            self.lignes.append(("    " * self.indentation) + texte)

    def formater_source(self, source: str) -> str:
        programme = ParserAstroQode.depuis_source(source).parser_programme()
        return self.formater_programme(programme)

    def formater_programme(self, programme: ProgrammeAstroQode) -> str:
        self.lignes.clear()
        self.indentation = 0

        self._emettre("# ==============================================================================")
        self._emettre("# PROGRAMME ASTRO-Q°ODE FORMATÉ CANONIQUEMENT")
        self._emettre("# ==============================================================================")
        self._emettre("")

        if programme.directives_horloge:
            for d in programme.directives_horloge:
                self._emettre(f"SET {d.nom_horloge:<16} = {d.valeur}")
            self._emettre("")

        for bloc_mec in programme.blocs_mecquois:
            self._formater_instruction(bloc_mec)
            self._emettre("")

        for bloc_med in programme.blocs_medinois:
            self._formater_instruction(bloc_med)
            self._emettre("")

        return "\n".join(self.lignes).rstrip() + "\n"

    def _formater_instruction(self, instr: InstructionAstro) -> None:
        if isinstance(instr, BlocMecquois):
            self._emettre("MECQUOIS {")
            self.indentation += 1
            for decl in instr.declarations:
                self._formater_instruction(decl)
            self.indentation -= 1
            self._emettre("}")
            return

        if isinstance(instr, BlocMedinois):
            self._emettre("MEDINOIS {")
            self.indentation += 1
            for s_instr in instr.instructions:
                self._formater_instruction(s_instr)
            self.indentation -= 1
            self._emettre("}")
            return

        if isinstance(instr, DeclarationSpecification):
            self._emettre(instr.contenu)
            return

        if isinstance(instr, DeclarationConstanteMecquoise):
            self._emettre(f"{instr.nom} = {self._formater_expression(instr.expression)}")
            return

        if isinstance(instr, AffectationLocaleMedinoise):
            suffixe = " ??" if instr.forcee else ""
            self._emettre(f"{instr.nom} = {self._formater_expression(instr.expression)}{suffixe}")
            return

        if isinstance(instr, InstructionConditionnelleForcee):
            cond_str = self._formater_expression(instr.condition)
            if not cond_str.startswith("("):
                cond_str = f"({cond_str})"
            self._emettre(f"{cond_str} ??")
            self._emettre("{")
            self.indentation += 1
            for s_instr in instr.bloc_alors:
                self._formater_instruction(s_instr)
            self.indentation -= 1
            self._emettre("}")
            if instr.bloc_sinon_catch is not None:
                self._emettre("¿ {")
                self.indentation += 1
                for s_instr in instr.bloc_sinon_catch:
                    self._formater_instruction(s_instr)
                self.indentation -= 1
                self._emettre("}")
            return

        if isinstance(instr, InstructionInversionCatch):
            self._emettre("¿ {")
            self.indentation += 1
            for s_instr in instr.corps:
                self._formater_instruction(s_instr)
            self.indentation -= 1
            self._emettre("}")
            return

        if isinstance(instr, InstructionIsolationMonadique):
            cible = instr.expression
            while isinstance(cible, ExpressionSandbox):
                cible = cible.interne
            self._emettre(f"(( {self._formater_expression(cible)} ))")
            return

        if isinstance(instr, InstructionForceExpression):
            self._emettre(f"{self._formater_expression(instr.expression)} ??")
            return

        if isinstance(instr, InstructionRetour):
            self._emettre(f"return {self._formater_expression(instr.expression)}")
            return

        if isinstance(instr, InstructionAfficher):
            self._emettre(f"afficher({self._formater_expression(instr.expression)})")
            return

    def _formater_expression(self, expr: ExpressionAstro) -> str:
        if isinstance(expr, LitteralNombreUnite):
            val_str = str(int(expr.valeur)) if expr.est_entier else str(expr.valeur)
            if expr.valeur > 0 and expr.unite in ("i", "I") and expr.valeur <= 9:
                val_str = f"+{val_str}"
            if expr.unite:
                return f"{val_str} {expr.unite}"
            return val_str

        if isinstance(expr, LitteralHeliumInerte):
            return "0 : HÉLIUM"

        if isinstance(expr, LitteralChaine):
            return f'"{expr.valeur}"'

        if isinstance(expr, ReferenceVariable):
            return expr.nom

        if isinstance(expr, ExpressionEnsemble):
            interne = " U ".join(self._formater_expression(e) for e in expr.elements)
            return f"[{interne}]"

        if isinstance(expr, ExpressionMonad):
            return f"Monad({self._formater_expression(expr.interne)})"

        if isinstance(expr, ExpressionForme):
            return f"Forme({self._formater_expression(expr.index_expr)})"

        if isinstance(expr, ExpressionFusionPP):
            return f"fusion_pp({self._formater_expression(expr.nb_noyaux_expr)})"

        if isinstance(expr, ExpressionAppelAlmizan):
            return f"{expr.nom_primitive}({self._formater_expression(expr.argument)})"

        if isinstance(expr, ExpressionLambda):
            lignes_corps = []
            for s in expr.corps:
                if isinstance(s, InstructionRetour):
                    lignes_corps.append(f"return {self._formater_expression(s.expression)}")
                else:
                    lignes_corps.append("...")
            return f"(lambda {expr.parametre} {{ {' ; '.join(lignes_corps)} }})"

        if isinstance(expr, ExpressionSandbox):
            if expr.niveau >= 2:
                return f"(( {self._formater_expression(expr.interne)} ))"
            return f"({self._formater_expression(expr.interne)})"

        if isinstance(expr, ExpressionUnaire):
            return f"{expr.operateur}{self._formater_expression(expr.operande)}"

        if isinstance(expr, ExpressionBinaire):
            g = self._formater_expression(expr.gauche)
            d = self._formater_expression(expr.droite)
            op = expr.operateur
            if op in ("U", "UNION"):
                op = "∪"
            elif op == "INCL":
                op = "⊃"
            elif op == "STRICT":
                op = "⊂"
            return f"{g} {op} {d}"

        return ""
