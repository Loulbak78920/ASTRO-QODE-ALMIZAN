# -*- coding: utf-8 -*-
"""
Interpréteur Complet du Langage ASTRO-Q°ODE (V1.0 & V2.0)
=========================================================
Exécute un arbre syntaxique `ProgrammeAstroQode` sur la `MachineVirtuelleBiomecanique`.
Gère :
- Les constantes d'horloge (`SET CLOCK_...`)
- Les blocs `MECQUOIS` (immuables, Niveaux 1 & 2) et `MEDINOIS` (exécutifs, Niveaux 3 & 4)
- Tous les opérateurs des 3 états de `tablettes_apprise_opérateur.csv`
- La gouvernance `⊃` (`INCL`), l'union `∪` (`UNION`), l'inclusion stricte `⊂` (`STRICT`)
- Le modificateur de force `??` (Doigt 2 Majeur), le conteneur Sandbox `( ... )` et `(( ... ))`
- L'inversion culturelle `¿ { ... }` (Catch d'exception et alternative d'état)
- La Monade Suprême V2.0 (`Monad(...)`, `>>=`, `lambda`, retour `0 : HÉLIUM`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from bibliotheques.lib_almizan_extension import (
    MIZAN,
    SphereHolographiqueAlmizan,
    TriadeBitQubitIBit,
    clamp_domaine_mizan,
    executer_cycle_15_phases,
    obtenir_forme_etendue_almizan,
)
from bibliotheques.lib_monade import MonadeSupreme
from bibliotheques.lib_physique import MatriceLogiqueInversee, obtenir_forme_matiere
from bibliotheques.lib_pont_materiel_emule import PontMaterielEmuleAlmizan
from bibliotheques.lib_matrice_unisson_or_argent import MatriceFondatriceUnisson
from .compilateur_qasm_isa import CompilateurQasmIsaAstroQode
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
from .runtime_values import (
    EnergieJoules,
    EnsembleContexte,
    EtatHeliumInerte,
    FonctionLambdaAstro,
    SignalKelvin,
    ValeurAstro,
)
from .vm_biomecanique import MachineVirtuelleBiomecanique


class _SignalRetourLambda(Exception):
    """Exception de contrôle interne pour propager la valeur d'un `return`."""

    def __init__(self, valeur: object) -> None:
        super().__init__()
        self.valeur = valeur


@dataclass
class ResultatExecutionAstroQode:
    """Résultat structuré d'une exécution ASTRO-Q°ODE."""
    succes: bool
    valeur_finale: object
    registre_mecquois: Dict[str, object]
    memoire_medinoise: Dict[str, object]
    sorties_console: List[str]
    rapport_vm: Dict[str, object]
    erreur: Optional[str] = None


class InterpreteurAstroQode:
    """Moteur d'exécution principal pour ASTRO-Q°ODE V1.0 & V2.0."""

    def __init__(self, vm: Optional[MachineVirtuelleBiomecanique] = None) -> None:
        self.vm = vm or MachineVirtuelleBiomecanique()
        self._exception_medinoise_en_attente: bool = False

    def executer_source(self, source: str) -> ResultatExecutionAstroQode:
        """Parse et exécute directement une chaîne de code source ASTRO-Q°ODE."""
        parser = ParserAstroQode.depuis_source(source)
        programme = parser.parser_programme()
        return self.executer_programme(programme)

    def executer_programme(self, programme: ProgrammeAstroQode) -> ResultatExecutionAstroQode:
        try:
            for instr in programme.toutes_instructions:
                self._executer_instruction(instr, portee_locale=None)
            return ResultatExecutionAstroQode(
                succes=True,
                valeur_finale=self.vm.derniere_valeur,
                registre_mecquois=dict(self.vm.registre_mecquois),
                memoire_medinoise=dict(self.vm.memoire_medinoise),
                sorties_console=list(self.vm.sorties_console),
                rapport_vm=self.vm.rapport_etat_complet(),
            )
        except _SignalRetourLambda as ret:
            if isinstance(ret.valeur, (int, float)) and ret.valeur == 0:
                val_fin = self.vm.purger_vers_helium("return 0")
            elif isinstance(ret.valeur, EtatHeliumInerte):
                val_fin = self.vm.purger_vers_helium("return 0 : HÉLIUM")
            else:
                val_fin = ret.valeur
            return ResultatExecutionAstroQode(
                succes=True,
                valeur_finale=val_fin,
                registre_mecquois=dict(self.vm.registre_mecquois),
                memoire_medinoise=dict(self.vm.memoire_medinoise),
                sorties_console=list(self.vm.sorties_console),
                rapport_vm=self.vm.rapport_etat_complet(),
            )
        except Exception as exc:
            return ResultatExecutionAstroQode(
                succes=False,
                valeur_finale=self.vm.purger_vers_helium(f"Exception: {exc}"),
                registre_mecquois=dict(self.vm.registre_mecquois),
                memoire_medinoise=dict(self.vm.memoire_medinoise),
                sorties_console=list(self.vm.sorties_console),
                rapport_vm=self.vm.rapport_etat_complet(),
                erreur=str(exc),
            )

    # ==========================================================================
    # EXÉCUTION DES INSTRUCTIONS
    # ==========================================================================

    def _executer_instruction(
        self,
        instr: InstructionAstro,
        portee_locale: Optional[Dict[str, object]],
    ) -> object:
        if isinstance(instr, DirectiveHorloge):
            self.vm.configurer_horloge(instr.nom_horloge, instr.valeur)
            return instr.valeur

        if isinstance(instr, DeclarationSpecification):
            # Bloc documentaire de spécification (TYPES, PROPRIÉTÉS, etc.)
            self.vm.horloge.consommer_tick("LUNE", cout=0.5, operation="SPEC_DECLARATION")
            return None

        if isinstance(instr, BlocMecquois):
            for decl in instr.declarations:
                self._executer_instruction(decl, portee_locale=portee_locale)
            return None

        if isinstance(instr, BlocMedinois):
            self._exception_medinoise_en_attente = False
            for sous_instr in instr.instructions:
                try:
                    self._executer_instruction(sous_instr, portee_locale=portee_locale)
                except _SignalRetourLambda:
                    raise
                except Exception:
                    self._exception_medinoise_en_attente = True
            return self.vm.derniere_valeur

        if isinstance(instr, DeclarationConstanteMecquoise):
            valeur = self._evaluer_expression(instr.expression, portee_locale=portee_locale)
            self.vm.sceller_constante_mecquoise(instr.nom, valeur)
            return valeur

        if isinstance(instr, AffectationLocaleMedinoise):
            valeur = self._evaluer_expression(instr.expression, portee_locale=portee_locale)
            if portee_locale is not None and instr.nom in portee_locale:
                portee_locale[instr.nom] = valeur
            else:
                self.vm.affecter_variable_medinoise(instr.nom, valeur, forcee=instr.forcee)
            return valeur

        if isinstance(instr, InstructionConditionnelleForcee):
            self.vm.pipeline_doigts.forcer_energie_majeur("Condition ??")
            try:
                cond_val = self._evaluer_expression(instr.condition, portee_locale=portee_locale)
                est_vrai = self._est_vrai(cond_val)
            except Exception:
                est_vrai = False
                self._exception_medinoise_en_attente = True

            if est_vrai:
                res = None
                for s_instr in instr.bloc_alors:
                    res = self._executer_instruction(s_instr, portee_locale=portee_locale)
                return res
            else:
                if instr.bloc_sinon_catch is not None:
                    self._exception_medinoise_en_attente = False
                    res = None
                    for s_instr in instr.bloc_sinon_catch:
                        res = self._executer_instruction(s_instr, portee_locale=portee_locale)
                    return res
                return None

        if isinstance(instr, InstructionInversionCatch):
            # S'exécute si une exception est en attente dans le bloc MEDINOIS
            if self._exception_medinoise_en_attente:
                self._exception_medinoise_en_attente = False
                res = None
                for s_instr in instr.corps:
                    res = self._executer_instruction(s_instr, portee_locale=portee_locale)
                return res
            return None

        if isinstance(instr, InstructionIsolationMonadique):
            self.vm.omoplate.activer_sandbox_beta(niveau_imbrication=2)
            try:
                cible = instr.expression
                while isinstance(cible, ExpressionSandbox):
                    cible = cible.interne
                val = self._evaluer_expression(cible, portee_locale=portee_locale)
                if isinstance(val, MonadeSupreme):
                    val_isolee = val.isoler()
                    if isinstance(cible, ReferenceVariable):
                        self.vm.affecter_variable_medinoise(cible.nom, val_isolee, forcee=True)
                    self.vm.derniere_valeur = val_isolee
                    return val_isolee
                return val
            finally:
                self.vm.omoplate.relacher_sandbox_beta(niveau_imbrication=2)

        if isinstance(instr, InstructionForceExpression):
            # Cas particulier : `( alpha_cell_monad >>= (lambda ...)) ??`
            # Met à jour la variable monadique à gauche du `>>=` avec la Monade transcrite !
            expr_interne = instr.expression
            while isinstance(expr_interne, ExpressionSandbox):
                expr_interne = expr_interne.interne

            self.vm.pipeline_doigts.forcer_energie_majeur("ForceExpression ??")
            val = self._evaluer_expression(instr.expression, portee_locale=portee_locale)

            if (
                isinstance(expr_interne, ExpressionBinaire)
                and expr_interne.operateur == ">>="
                and isinstance(expr_interne.gauche, ReferenceVariable)
            ):
                nom_var = expr_interne.gauche.nom
                self.vm.affecter_variable_medinoise(nom_var, val, forcee=True)

            self.vm.derniere_valeur = val
            return val

        if isinstance(instr, InstructionRetour):
            val = self._evaluer_expression(instr.expression, portee_locale=portee_locale)
            if isinstance(val, (int, float)) and val == 0:
                val = EtatHeliumInerte()
            raise _SignalRetourLambda(val)

        if isinstance(instr, InstructionAfficher):
            val = self._evaluer_expression(instr.expression, portee_locale=portee_locale)
            texte = str(val) if isinstance(val, str) else repr(val)
            self.vm.sorties_console.append(texte)
            return val

        raise RuntimeError(f"Instruction AST non supportée : {type(instr).__name__}")

    # ==========================================================================
    # ÉVALUATION DES EXPRESSIONS
    # ==========================================================================

    def _evaluer_expression(
        self,
        expr: ExpressionAstro,
        portee_locale: Optional[Dict[str, object]],
    ) -> object:
        if isinstance(expr, LitteralNombreUnite):
            if expr.unite == "i":
                return SignalKelvin(valeur=expr.valeur)
            if expr.unite == "I":
                return EnergieJoules(valeur=expr.valeur)
            return int(expr.valeur) if expr.est_entier else expr.valeur

        if isinstance(expr, LitteralHeliumInerte):
            return EtatHeliumInerte()

        if isinstance(expr, LitteralChaine):
            return expr.valeur

        if isinstance(expr, ReferenceVariable):
            return self.vm.lire_symbole(expr.nom, portee_locale=portee_locale)

        if isinstance(expr, ExpressionEnsemble):
            vals = [self._evaluer_expression(el, portee_locale=portee_locale) for el in expr.elements]
            return EnsembleContexte.depuis_sequence(vals)

        if isinstance(expr, ExpressionMonad):
            val_interne = self._evaluer_expression(expr.interne, portee_locale=portee_locale)
            if isinstance(val_interne, EtatHeliumInerte):
                return MonadeSupreme.helium_inerte()
            return MonadeSupreme.unit(val_interne)

        if isinstance(expr, ExpressionForme):
            idx_val = self._evaluer_expression(expr.index_expr, portee_locale=portee_locale)
            idx_int = int(round(self._extraire_flottant(idx_val)))
            forme = obtenir_forme_etendue_almizan(idx_int)
            self.vm.forme_active = forme
            return forme

        if isinstance(expr, ExpressionFusionPP):
            nb_val = self._evaluer_expression(expr.nb_noyaux_expr, portee_locale=portee_locale)
            nb_int = int(round(self._extraire_flottant(nb_val)))
            return MatriceLogiqueInversee.fusionner_hydrogene_en_helium(nb_int)

        if isinstance(expr, ExpressionAppelAlmizan):
            arg_val = self._evaluer_expression(expr.argument, portee_locale=portee_locale)
            nom = expr.nom_primitive.lower()
            if nom == "clamp_mizan":
                return clamp_domaine_mizan(self._extraire_flottant(arg_val))
            if nom == "sphere_holographique":
                return SphereHolographiqueAlmizan.cartographier(temp_mk=self._extraire_flottant(arg_val))
            if nom == "triade_ibit":
                return TriadeBitQubitIBit.synchroniser(nb_cycles_si29=int(round(self._extraire_flottant(arg_val))))
            if nom == "cycle_15_phases":
                return executer_cycle_15_phases(message=str(arg_val))
            if nom == "tir_scpi_5025":
                return PontMaterielEmuleAlmizan.piloter_scpi_5025(
                    frequence_ghz=4.85,
                    puissance_dbm=-15.0,
                    forme_impulsion=str(arg_val) if isinstance(arg_val, str) else "GAUSS",
                )
            if nom == "capteur_cryo_5026":
                return PontMaterielEmuleAlmizan.interroger_cryo_5026(
                    commande=str(arg_val) if isinstance(arg_val, str) else "READ:CRYO:ALL?"
                )
            if nom == "executer_qasm_5030":
                compil = CompilateurQasmIsaAstroQode()
                res_qasm = compil.compiler_et_executer_circuit(
                    nom_circuit=str(arg_val) if isinstance(arg_val, str) else "BELL",
                    shots=512,
                )
                return res_qasm.execution_die_5030
            if nom == "sceller_sha256":
                from outils.scelleur_cryptographique import ScelleurMemoireAstroQode
                return ScelleurMemoireAstroQode.sceller_etat_execution(
                    nom_sceau=str(arg_val),
                    rapport_vm=self.vm.rapport_etat_complet(),
                )
            if nom == "matrice_unisson":
                masse_or = self._extraire_flottant(arg_val) if self._extraire_flottant(arg_val) > 0 else 85.0
                return MatriceFondatriceUnisson.calculer_matrice_unisson_complete(
                    masse_or_grammes=masse_or,
                    masse_argent_grammes=masse_or * 7.0,
                )
            if nom == "valeur_or":
                masse_g = self._extraire_flottant(arg_val) if self._extraire_flottant(arg_val) > 0 else 85.0
                return MatriceFondatriceUnisson.calculer_valeur_or(masse_grammes=masse_g).vers_dict()
            if nom == "valeur_argent":
                masse_g = self._extraire_flottant(arg_val) if self._extraire_flottant(arg_val) > 0 else 595.0
                return MatriceFondatriceUnisson.calculer_valeur_argent(masse_grammes=masse_g).vers_dict()
            raise RuntimeError(f"Primitive Al-Mizan inconnue : {expr.nom_primitive}")

        if isinstance(expr, ExpressionLambda):
            def _executer_corps_lambda(argument: object) -> object:
                nouvelle_portee = dict(portee_locale or {})
                nouvelle_portee[expr.parametre] = argument
                dernier = None
                try:
                    for inst in expr.corps:
                        dernier = self._executer_instruction(inst, portee_locale=nouvelle_portee)
                except _SignalRetourLambda as sig:
                    return sig.valeur
                return dernier

            return FonctionLambdaAstro(
                parametre=expr.parametre,
                corps=expr.corps,
                executer_callback=_executer_corps_lambda,
            )

        if isinstance(expr, ExpressionSandbox):
            self.vm.omoplate.activer_sandbox_beta(niveau_imbrication=expr.niveau)
            try:
                val = self._evaluer_expression(expr.interne, portee_locale=portee_locale)
                if expr.niveau >= 2 and isinstance(val, MonadeSupreme):
                    return val.isoler()
                return val
            finally:
                self.vm.omoplate.relacher_sandbox_beta(niveau_imbrication=expr.niveau)

        if isinstance(expr, ExpressionUnaire):
            op_val = self._evaluer_expression(expr.operande, portee_locale=portee_locale)
            if expr.operateur in ("!", "NOT"):
                return not self._est_vrai(op_val)
            if expr.operateur == "-":
                if isinstance(op_val, SignalKelvin):
                    return SignalKelvin(-op_val.valeur)
                if isinstance(op_val, EnergieJoules):
                    return EnergieJoules(-op_val.valeur)
                return -self._extraire_flottant(op_val)
            return op_val

        if isinstance(expr, ExpressionBinaire):
            return self._evaluer_binaire(expr, portee_locale=portee_locale)

        raise RuntimeError(f"Expression AST non supportée : {type(expr).__name__}")

    def _evaluer_binaire(
        self,
        expr: ExpressionBinaire,
        portee_locale: Optional[Dict[str, object]],
    ) -> object:
        gauche = self._evaluer_expression(expr.gauche, portee_locale=portee_locale)
        op = expr.operateur

        # 1. Transcription Monadique V2.0 : `monade >>= lambda`
        if op == ">>=":
            droite = self._evaluer_expression(expr.droite, portee_locale=portee_locale)
            self.vm.horloge.consommer_tick("MEDINOIS", cout=2.0, operation="BIND_MONADE >>=")
            if not isinstance(gauche, MonadeSupreme):
                gauche = MonadeSupreme.unit(gauche)
            if isinstance(droite, FonctionLambdaAstro):
                return gauche.bind(droite.appeler)
            if callable(droite):
                return gauche.bind(droite)
            raise TypeError(f"Opérande droit de '>>=' doit être un lambda, obtenu : {droite!r}")

        droite = self._evaluer_expression(expr.droite, portee_locale=portee_locale)

        # 2. Opérateurs de Niveau 3 & 4 (Relationnels / Ensemblistes / Topologiques) -> Doigt 3 Annulaire
        if op in ("∪", "U", "UNION"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("∪", gauche, droite)
            return self._appliquer_union(gauche, droite)

        if op in ("⊃", "INCL"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("⊃", gauche, droite)
            return self._verifier_inclusion_gouvernance(gauche, droite, stricte=False)

        if op in ("⊂", "STRICT"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("⊂", gauche, droite)
            return self._verifier_inclusion_gouvernance(gauche, droite, stricte=True)

        if op in ("∖", "DIFF"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("∖", gauche, droite)
            return self._appliquer_difference(gauche, droite)

        if op in ("∩", "INTER"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("∩", gauche, droite)
            return (self._extraire_flottant(gauche) + self._extraire_flottant(droite)) / 2.0

        if op in ("⊘", "HDIV"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("⊘", gauche, droite)
            vg, vd = self._extraire_flottant(gauche), self._extraire_flottant(droite)
            if vd == 0:
                return EtatHeliumInerte()
            return vg / vd

        if op in ("≡", "CONGR"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("≡", gauche, droite)
            return type(gauche) is type(droite)

        if op in ("≢", "NCONGR"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("≢", gauche, droite)
            return type(gauche) is not type(droite)

        if op in ("‰", "PERMILLE"):
            return (self._extraire_flottant(gauche) * self._extraire_flottant(droite)) / 1000.0

        if op in ("⊕", "OPLUS"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("⊕", gauche, droite)
            somme_kronecker = self._extraire_flottant(gauche) + self._extraire_flottant(droite)
            return clamp_domaine_mizan(somme_kronecker)

        if op in ("⊗", "OTIMES"):
            self.vm.pipeline_doigts.lier_contexte_annulaire("⊗", gauche, droite)
            prod_kronecker = self._extraire_flottant(gauche) * self._extraire_flottant(droite)
            return clamp_domaine_mizan(prod_kronecker)

        # 3. Opérateurs de Niveau 2 (Logique / Booléen)
        if op in ("&&", "AND"):
            return self._est_vrai(gauche) and self._est_vrai(droite)
        if op in ("||", "OR"):
            return self._est_vrai(gauche) or self._est_vrai(droite)
        if op == "NAND":
            return not (self._est_vrai(gauche) and self._est_vrai(droite))
        if op == "XOR":
            return self._est_vrai(gauche) ^ self._est_vrai(droite)
        if op == "==":
            return self._extraire_flottant(gauche) == self._extraire_flottant(droite)
        if op in ("!=", "≠"):
            return self._extraire_flottant(gauche) != self._extraire_flottant(droite)

        # 4. Opérateurs de Niveau 1 (Arithmétique)
        vg = self._extraire_flottant(gauche)
        vd = self._extraire_flottant(droite)

        if op == "+":
            return self._reconstruire_unite(gauche, droite, vg + vd)
        if op == "-":
            return self._reconstruire_unite(gauche, droite, vg - vd)
        if op in ("*", "×"):
            return self._reconstruire_unite(gauche, droite, vg * vd)
        if op in ("/", "÷"):
            if vd == 0:
                return EtatHeliumInerte()
            return self._reconstruire_unite(gauche, droite, vg / vd)
        if op == "%":
            return vg % vd
        if op == ">":
            return vg > vd
        if op == "<":
            return vg < vd

        raise RuntimeError(f"Opérateur binaire non reconnu : {op!r}")

    # ==========================================================================
    # SÉMANTIQUE DES OPÉRATEURS ONTOLOGIQUES (∪, ⊃, ⊂, ∖)
    # ==========================================================================

    def _appliquer_union(self, gauche: object, droite: object) -> object:
        """
        Applique l'opérateur d'Union `∪` (État 3 de l'Addition) :
        - Si deux `SignalKelvin` (`-3 i ∪ +2 i`) : fusion additive des signaux thermiques (`-1 i`).
        - Si deux `EnergieJoules` (`+5 I ∪ +1 I`) : fusion additive des énergies (`+6 I`).
        - Si `SignalKelvin` et `EnergieJoules` (`0 i ∪ +1 I`) : élévation thermo-cinétique
          (`SignalKelvin(vg + vd)` si vg != 0, ou `EnergieJoules(vg + vd)` si promu en Joules).
        - Si ensembles : union des contextes `EnsembleContexte`.
        """
        if isinstance(gauche, SignalKelvin) and isinstance(droite, SignalKelvin):
            return SignalKelvin(gauche.valeur + droite.valeur)
        if isinstance(gauche, EnergieJoules) and isinstance(droite, EnergieJoules):
            return EnergieJoules(gauche.valeur + droite.valeur)
        if isinstance(gauche, SignalKelvin) and isinstance(droite, EnergieJoules):
            return EnergieJoules(gauche.valeur + droite.valeur)
        if isinstance(gauche, EnergieJoules) and isinstance(droite, SignalKelvin):
            return EnergieJoules(gauche.valeur + droite.valeur)
        if isinstance(gauche, EnsembleContexte) or isinstance(droite, EnsembleContexte):
            return EnsembleContexte.depuis_sequence([gauche, droite])
        return self._extraire_flottant(gauche) + self._extraire_flottant(droite)

    def _appliquer_difference(self, gauche: object, droite: object) -> object:
        if isinstance(gauche, SignalKelvin) and isinstance(droite, SignalKelvin):
            return SignalKelvin(gauche.valeur - droite.valeur)
        if isinstance(gauche, EnergieJoules) and isinstance(droite, EnergieJoules):
            return EnergieJoules(gauche.valeur - droite.valeur)
        return self._extraire_flottant(gauche) - self._extraire_flottant(droite)

    def _verifier_inclusion_gouvernance(
        self,
        gauche: object,
        droite: object,
        stricte: bool = False,
    ) -> bool:
        """
        Implémente `(alpha_c ⊃ omega_A)` et `(signal_thermique ⊃ omega_MONAD_SOUL)` :
        Vérifie si la variable/signal `gauche` interagit légitimement sous la gouvernance
        de la constante ou de l'âme monadique `droite`.
        """
        if isinstance(gauche, EtatHeliumInerte):
            return not stricte
        if isinstance(droite, EnsembleContexte):
            return droite.contient_ou_gouverne(gauche)
        vg = abs(self._extraire_flottant(gauche))
        vd = abs(self._extraire_flottant(droite))
        if stricte:
            return vg < vd
        return vg <= vd

    @staticmethod
    def _reconstruire_unite(gauche: object, droite: object, resultat: float) -> object:
        if isinstance(gauche, SignalKelvin) and isinstance(droite, SignalKelvin):
            return SignalKelvin(resultat)
        if isinstance(gauche, EnergieJoules) or isinstance(droite, EnergieJoules):
            return EnergieJoules(resultat)
        if isinstance(gauche, SignalKelvin):
            return SignalKelvin(resultat)
        return resultat

    @staticmethod
    def _extraire_flottant(val: object) -> float:
        if isinstance(val, ValeurAstro):
            return val.valeur_numerique()
        if isinstance(val, MonadeSupreme):
            interne = val.valeur_interne
            if isinstance(interne, ValeurAstro):
                return interne.valeur_numerique()
            if isinstance(interne, (int, float)):
                return float(interne)
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        return 0.0

    @staticmethod
    def _est_vrai(val: object) -> bool:
        if isinstance(val, bool):
            return val
        if isinstance(val, ValeurAstro):
            return val.est_veridique()
        if isinstance(val, MonadeSupreme):
            return not val.est_helium_inerte
        if isinstance(val, (int, float)):
            return val != 0
        return bool(val)
