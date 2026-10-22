# -*- coding: utf-8 -*-
"""
Transpilateur ASTRO-Q°ODE (.aq) vers Python (.py)
=================================================
Convertit n'importe quel programme ASTRO-Q°ODE V1.0 ou V2.0 en un script Python
autonome et lisible s'appuyant sur les bibliothèques du système `ASTRO-Q°ODE_SYSTEME`.
"""

from __future__ import annotations

from typing import List

from .ast_nodes import (
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
from .parser import ParserAstroQode


class TranspilateurPythonAstroQode:
    """Génère du code Python exécutable à partir d'un AST ASTRO-Q°ODE."""

    def __init__(self) -> None:
        self.lignes: List[str] = []
        self.indentation: int = 0

    def _emettre(self, ligne: str = "") -> None:
        if not ligne:
            self.lignes.append("")
        else:
            self.lignes.append(("    " * self.indentation) + ligne)

    def transpiler_source(self, source: str) -> str:
        programme = ParserAstroQode.depuis_source(source).parser_programme()
        return self.transpiler_programme(programme)

    def transpiler_programme(self, programme: ProgrammeAstroQode) -> str:
        self.lignes.clear()
        self.indentation = 0

        self._emettre("# -*- coding: utf-8 -*-")
        self._emettre('"""Script Python généré automatiquement par le Transpilateur ASTRO-Q°ODE."""')
        self._emettre("from bibliotheques.lib_temporelle import CLOCK_DX_SOLEIL, CLOCK_DY_LUNE, CLOCK_DZ_TERRE, CLOCK_DT_KERNEL")
        self._emettre("from bibliotheques.lib_monade import MonadeSupreme")
        self._emettre("from bibliotheques.lib_physique import obtenir_forme_matiere, MatriceLogiqueInversee")
        self._emettre("from bibliotheques.lib_almizan_extension import MIZAN, LIGNE_REF, RMS, EPSILON, clamp_domaine_mizan, obtenir_forme_etendue_almizan, SphereHolographiqueAlmizan, TriadeBitQubitIBit, executer_cycle_15_phases")
        self._emettre("from bibliotheques.lib_pont_materiel_emule import PontMaterielEmuleAlmizan")
        self._emettre("from bibliotheques.lib_matrice_unisson_or_argent import MatriceFondatriceUnisson")
        self._emettre("from lang.compilateur_qasm_isa import CompilateurQasmIsaAstroQode")
        self._emettre("from outils.scelleur_cryptographique import ScelleurMemoireAstroQode")
        self._emettre("from lang.runtime_values import SignalKelvin, EnergieJoules, EtatHeliumInerte, EnsembleContexte")
        self._emettre("from lang.vm_biomecanique import MachineVirtuelleBiomecanique")
        self._emettre("")
        self._emettre("vm = MachineVirtuelleBiomecanique()")
        self._emettre("dx = CLOCK_DX_SOLEIL")
        self._emettre("dy = CLOCK_DY_LUNE")
        self._emettre("dz = CLOCK_DZ_TERRE")
        self._emettre("dt = CLOCK_DT_KERNEL")
        self._emettre("")

        for instr in programme.toutes_instructions:
            self._transpiler_instruction(instr)

        self._emettre("")
        self._emettre("if __name__ == '__main__':")
        self.indentation += 1
        self._emettre("import json")
        self._emettre("print(json.dumps(vm.rapport_etat_complet(), indent=2, ensure_ascii=False))")
        self.indentation -= 1

        return "\n".join(self.lignes) + "\n"

    def _transpiler_instruction(self, instr: InstructionAstro) -> None:
        if isinstance(instr, DirectiveHorloge):
            self._emettre(f"vm.configurer_horloge({instr.nom_horloge!r}, {instr.valeur})")
            return

        if isinstance(instr, DeclarationSpecification):
            self._emettre(f"# [SPEC] {instr.contenu.splitlines()[0] if instr.contenu else ''}")
            return

        if isinstance(instr, BlocMecquois):
            self._emettre("# === NAMESPACE MECQUOIS (Ontologique & Immuable) ===")
            for decl in instr.declarations:
                self._transpiler_instruction(decl)
            return

        if isinstance(instr, BlocMedinois):
            self._emettre("# === NAMESPACE MEDINOIS (Législatif & Exécutif) ===")
            for s_instr in instr.instructions:
                self._transpiler_instruction(s_instr)
            return

        if isinstance(instr, DeclarationConstanteMecquoise):
            code_expr = self._transpiler_expression(instr.expression)
            self._emettre(f"{instr.nom} = {code_expr}")
            self._emettre(f"vm.sceller_constante_mecquoise({instr.nom!r}, {instr.nom})")
            return

        if isinstance(instr, AffectationLocaleMedinoise):
            code_expr = self._transpiler_expression(instr.expression)
            self._emettre(f"{instr.nom} = {code_expr}")
            self._emettre(
                f"vm.affecter_variable_medinoise({instr.nom!r}, {instr.nom}, forcee={instr.forcee})"
            )
            return

        if isinstance(instr, InstructionConditionnelleForcee):
            cond_py = self._transpiler_expression(instr.condition)
            self._emettre(f"if bool({cond_py}):")
            self.indentation += 1
            if not instr.bloc_alors:
                self._emettre("pass")
            for s_instr in instr.bloc_alors:
                self._transpiler_instruction(s_instr)
            self.indentation -= 1
            if instr.bloc_sinon_catch:
                self._emettre("else:  # ¿ Inversion culturelle")
                self.indentation += 1
                for s_instr in instr.bloc_sinon_catch:
                    self._transpiler_instruction(s_instr)
                self.indentation -= 1
            return

        if isinstance(instr, InstructionInversionCatch):
            self._emettre("# Bloc d'inversion culturelle autonome ¿ { ... }")
            for s_instr in instr.corps:
                self._transpiler_instruction(s_instr)
            return

        if isinstance(instr, InstructionIsolationMonadique):
            cible = instr.expression
            while isinstance(cible, ExpressionSandbox):
                cible = cible.interne
            code_expr = self._transpiler_expression(cible)
            if isinstance(cible, ReferenceVariable):
                self._emettre(f"{cible.nom} = ({code_expr}).isoler()")
                self._emettre(f"vm.affecter_variable_medinoise({cible.nom!r}, {cible.nom}, forcee=True)")
            else:
                self._emettre(f"_ = ({code_expr}).isoler()")
            return

        if isinstance(instr, InstructionForceExpression):
            code_expr = self._transpiler_expression(instr.expression)
            interne = instr.expression
            while isinstance(interne, ExpressionSandbox):
                interne = interne.interne
            if (
                isinstance(interne, ExpressionBinaire)
                and interne.operateur == ">>="
                and isinstance(interne.gauche, ReferenceVariable)
            ):
                nom_var = interne.gauche.nom
                self._emettre(f"{nom_var} = {code_expr}")
                self._emettre(f"vm.affecter_variable_medinoise({nom_var!r}, {nom_var}, forcee=True)")
            else:
                self._emettre(f"_ = {code_expr}")
            return

        if isinstance(instr, InstructionRetour):
            code_expr = self._transpiler_expression(instr.expression)
            self._emettre(f"return {code_expr}")
            return

        if isinstance(instr, InstructionAfficher):
            code_expr = self._transpiler_expression(instr.expression)
            self._emettre(f"print({code_expr})")
            return

    def _transpiler_expression(self, expr: ExpressionAstro) -> str:
        if isinstance(expr, LitteralNombreUnite):
            if expr.unite == "i":
                return f"SignalKelvin({expr.valeur})"
            if expr.unite == "I":
                return f"EnergieJoules({expr.valeur})"
            return str(int(expr.valeur) if expr.est_entier else expr.valeur)

        if isinstance(expr, LitteralHeliumInerte):
            return "EtatHeliumInerte()"

        if isinstance(expr, LitteralChaine):
            return repr(expr.valeur)

        if isinstance(expr, ReferenceVariable):
            return expr.nom

        if isinstance(expr, ExpressionEnsemble):
            items = ", ".join(self._transpiler_expression(e) for e in expr.elements)
            return f"EnsembleContexte.depuis_sequence([{items}])"

        if isinstance(expr, ExpressionMonad):
            interne = self._transpiler_expression(expr.interne)
            return f"MonadeSupreme.unit({interne})"

        if isinstance(expr, ExpressionForme):
            idx = self._transpiler_expression(expr.index_expr)
            return f"obtenir_forme_etendue_almizan(int({idx}))"

        if isinstance(expr, ExpressionFusionPP):
            nb = self._transpiler_expression(expr.nb_noyaux_expr)
            return f"MatriceLogiqueInversee.fusionner_hydrogene_en_helium(int({nb}))"

        if isinstance(expr, ExpressionAppelAlmizan):
            arg = self._transpiler_expression(expr.argument)
            nom = expr.nom_primitive.lower()
            if nom == "clamp_mizan":
                return f"clamp_domaine_mizan({arg})"
            if nom == "sphere_holographique":
                return f"SphereHolographiqueAlmizan.cartographier(temp_mk=float({arg}))"
            if nom == "triade_ibit":
                return f"TriadeBitQubitIBit.synchroniser(nb_cycles_si29=int({arg}))"
            if nom == "cycle_15_phases":
                return f"executer_cycle_15_phases(message=str({arg}))"
            if nom == "tir_scpi_5025":
                return f"PontMaterielEmuleAlmizan.piloter_scpi_5025(forme_impulsion=str({arg}))"
            if nom == "capteur_cryo_5026":
                return f"PontMaterielEmuleAlmizan.interroger_cryo_5026(commande=str({arg}))"
            if nom == "executer_qasm_5030":
                return f"CompilateurQasmIsaAstroQode().compiler_et_executer_circuit(str({arg})).execution_die_5030"
            if nom == "sceller_sha256":
                return f"ScelleurMemoireAstroQode.sceller_etat_execution(str({arg}), vm.rapport_etat_complet())"
            if nom == "matrice_unisson":
                return f"MatriceFondatriceUnisson.calculer_matrice_unisson_complete(float({arg}))"
            if nom == "valeur_or":
                return f"MatriceFondatriceUnisson.calculer_valeur_or(float({arg})).vers_dict()"
            if nom == "valeur_argent":
                return f"MatriceFondatriceUnisson.calculer_valeur_argent(float({arg})).vers_dict()"

        if isinstance(expr, ExpressionLambda):
            # Pour un lambda multi-lignes en Python, on génère un appel inline via fonction lambda
            return f"(lambda {expr.parametre}: {self._transpiler_corps_lambda_inline(expr.corps)})"

        if isinstance(expr, ExpressionSandbox):
            interne = self._transpiler_expression(expr.interne)
            if expr.niveau >= 2:
                return f"({interne}).isoler()"
            return f"({interne})"

        if isinstance(expr, ExpressionUnaire):
            op_py = "not " if expr.operateur in ("!", "NOT") else expr.operateur
            return f"({op_py}{self._transpiler_expression(expr.operande)})"

        if isinstance(expr, ExpressionBinaire):
            g = self._transpiler_expression(expr.gauche)
            d = self._transpiler_expression(expr.droite)
            op = expr.operateur
            if op == ">>=":
                return f"({g}).bind({d})"
            if op in ("∪", "U", "UNION"):
                return f"EnsembleContexte.depuis_sequence([{g}, {d}])"
            if op in ("⊃", "INCL"):
                return f"(abs(getattr({g}, 'valeur_numerique', lambda: float({g}))()) <= abs(getattr({d}, 'valeur_numerique', lambda: float({d}))()))"
            if op in ("&&", "AND"):
                return f"({g} and {d})"
            if op in ("||", "OR"):
                return f"({g} or {d})"
            return f"({g} {op} {d})"

        return "None"

    def _transpiler_corps_lambda_inline(self, instructions: List[InstructionAstro]) -> str:
        if not instructions:
            return "EtatHeliumInerte()"
        inst = instructions[0]
        if isinstance(inst, InstructionRetour):
            return self._transpiler_expression(inst.expression)
        if isinstance(inst, InstructionConditionnelleForcee):
            cond = self._transpiler_expression(inst.condition)
            alors = self._transpiler_corps_lambda_inline(inst.bloc_alors)
            sinon = (
                self._transpiler_corps_lambda_inline(inst.bloc_sinon_catch)
                if inst.bloc_sinon_catch
                else "MonadeSupreme.helium_inerte()"
            )
            return f"({alors} if {cond} else {sinon})"
        return "MonadeSupreme.helium_inerte()"
