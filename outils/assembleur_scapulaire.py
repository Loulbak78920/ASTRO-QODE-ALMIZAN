# -*- coding: utf-8 -*-
"""
Outil 3 : Assembleur & Désassembleur Biomécanique Scapulaire (`assembleur_scapulaire.py`)
=========================================================================================
Traduit un programme ASTRO-Q°ODE en une séquence d'instructions matérielles
biomécaniques conformes à `matrice_scapulaire_astro_q°ode.pdf` et `axe_execution_astro_q°ode.pdf` :
- `SCAPULA_ALPHA` : Orientation de l'adresse [-9 ; +9]
- `SCAPULA_BETA`  : Ouverture / Fermeture du pare-feu Sandbox `( )` ou `(( ))`
- `SCAPULA_GAMMA` : Routage sur le bus Photon
- `BRAS_SYNC_DT`  : Synchronisation sur l'horloge maîtresse `dt = 135097021.3359375`
- `DOIGT_0_POUCE` : Purge / Retour à l'Origine `0 : HÉLIUM`
- `DOIGT_1_INDEX` : Pointage d'une variable `alpha_*`
- `DOIGT_2_MAJEUR`: Forçage d'énergie `??`
- `DOIGT_3_ANNUL` : Liaison contextuelle `∪`, `⊃`, `⊂`
- `DOIGT_4_AURIC` : Verrouillage symétrique `omega_*`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from bibliotheques.lib_informe import MatriceLogiqueComplexe
from lang.ast_nodes import (
    AffectationLocaleMedinoise,
    BlocMecquois,
    BlocMedinois,
    DeclarationConstanteMecquoise,
    DirectiveHorloge,
    ExpressionBinaire,
    InstructionConditionnelleForcee,
    InstructionForceExpression,
    InstructionInversionCatch,
    InstructionIsolationMonadique,
    InstructionRetour,
    ProgrammeAstroQode,
)
from lang.parser import ParserAstroQode


@dataclass
class InstructionAssembleurBiomécanique:
    """Représente une micro-instruction de l'Axe d'Exécution Biomécanique."""
    adresse: int
    segment_anatomique: str
    mnemonique: str
    operande_1: str
    operande_2: str
    commentaire: str

    def formater_ligne(self) -> str:
        return (
            f"0x{self.adresse:04X} | {self.segment_anatomique:<20} | "
            f"{self.mnemonique:<16} | {self.operande_1:<18} | {self.operande_2:<18} # {self.commentaire}"
        )


class AssembleurScapulaire:
    """Génère le listing assembleur biomécanique d'un script ASTRO-Q°ODE."""

    def desassembler_source(self, source: str) -> List[InstructionAssembleurBiomécanique]:
        programme = ParserAstroQode.depuis_source(source).parser_programme()
        return self.desassembler_programme(programme)

    def desassembler_programme(
        self,
        programme: ProgrammeAstroQode,
    ) -> List[InstructionAssembleurBiomécanique]:
        code: List[InstructionAssembleurBiomécanique] = []
        pc = 0

        def emettre(segment: str, mnem: str, op1: str, op2: str, comm: str) -> None:
            nonlocal pc
            code.append(
                InstructionAssembleurBiomécanique(
                    adresse=pc,
                    segment_anatomique=segment,
                    mnemonique=mnem,
                    operande_1=op1,
                    operande_2=op2,
                    commentaire=comm,
                )
            )
            pc += 4

        emettre("OMOPLATE (Scapula)", "SCAPULA_INIT", "0 : HÉLIUM", "ALPHA=0,BETA=0", "Initialisation au repos inerte")
        emettre("BRAS / AVANT-BRAS", "BRAS_SYNC_DT", "dt", "135097021.3359375", "Verrouillage de l'horloge maîtresse")

        for d in programme.directives_horloge:
            emettre("BRAS / AVANT-BRAS", "SET_CLOCK", d.nom_horloge, str(d.valeur), "Configuration de canal temporel")

        for bloc_mec in programme.blocs_mecquois:
            emettre("OMOPLATE (Scapula)", "ENTER_NAMESPACE", "MECQUOIS", "IMMUABLE", "Entrée dans le paradigme ontologique")
            for decl in bloc_mec.declarations:
                if isinstance(decl, DeclarationConstanteMecquoise):
                    coord = MatriceLogiqueComplexe.chiffre_depuis_identifiant(decl.nom)
                    coord_str = f"Axe={coord:+d}" if coord is not None else "Axe=UNIVERSEL"
                    emettre(
                        "DOIGT 4 (Auriculaire)",
                        "VERROU_OMEGA",
                        decl.nom,
                        coord_str,
                        "Ancrage de constante globale et fin de ligne (;)",
                    )

        for bloc_med in programme.blocs_medinois:
            emettre("OMOPLATE (Scapula)", "ENTER_NAMESPACE", "MEDINOIS", "EXECUTIF", "Entrée dans le paradigme législatif")
            for instr in bloc_med.instructions:
                if isinstance(instr, AffectationLocaleMedinoise):
                    coord = MatriceLogiqueComplexe.chiffre_depuis_identifiant(instr.nom)
                    coord_str = f"Alpha={coord:+d}" if coord is not None else "Alpha=DYNAMIQUE"
                    emettre("OMOPLATE (Scapula)", "SCAPULA_ALPHA", instr.nom, coord_str, "Élévation/Dépression vers l'adresse RAM")
                    emettre("DOIGT 1 (Index)", "POINTEUR_SIGNAL", instr.nom, "RAM_WRITE", "Sélection et écriture de variable locale")
                    if instr.forcee:
                        emettre("DOIGT 2 (Majeur)", "FORCAGE_ENERGIE", "??", instr.nom, "Priorité absolue d'affectation")

                elif isinstance(instr, InstructionConditionnelleForcee):
                    emettre("OMOPLATE (Scapula)", "SCAPULA_BETA", "( condition )", "SANDBOX_NIV_1", "Isolement sémantique de la condition")
                    emettre("DOIGT 3 (Annulaire)", "LIAISON_CONTEXTE", "⊃ / ∪", "GOUVERNANCE", "Vérification topologique et relationnelle")
                    emettre("DOIGT 2 (Majeur)", "FORCAGE_ENERGIE", "??", "BRANCH_TRUE", "Exécution impérative de la loi")
                    if instr.bloc_sinon_catch is not None:
                        emettre("DOIGT 0 (Pouce)", "INVERSION_CATCH", "¿", "FALLBACK_HELIUM", "Interception culturelle en cas de rejet")

                elif isinstance(instr, InstructionForceExpression):
                    emettre("OMOPLATE (Scapula)", "SCAPULA_GAMMA", "BUS_PHOTON", ">>=", "Transcription monadique polymérase")
                    emettre("DOIGT 2 (Majeur)", "FORCAGE_ENERGIE", "??", "COMMIT_MONAD", "Validation forcée de la transcription")

                elif isinstance(instr, InstructionIsolationMonadique):
                    emettre("OMOPLATE (Scapula)", "SCAPULA_BETA", "(( MONAD ))", "SANDBOX_NIV_2", "Verrouillage membranaire absolu")

                elif isinstance(instr, InstructionInversionCatch):
                    emettre("DOIGT 0 (Pouce)", "INVERSION_CATCH", "¿", "0 : HÉLIUM", "Bloc de secours et purge mémoire")

                elif isinstance(instr, InstructionRetour):
                    emettre("DOIGT 0 (Pouce)", "ANCRE_HELIUM", "return 0", "0 : HÉLIUM", "Purge mémoire et clôture absolue")

        emettre("DOIGT 0 (Pouce)", "HALT_HELIUM", "0 : HÉLIUM", "REPOS_STABLE", "Fin de cycle et retour à l'Origine Inerte")
        return code

    def formater_listing(self, source: str) -> str:
        instructions = self.desassembler_source(source)
        entete = [
            "=" * 112,
            "LISTING ASSEMBLEUR BIOMÉCANIQUE ASTRO-Q°ODE (OMOPLATE -> BRAS dt -> 5 DOIGTS)",
            "=" * 112,
            f"{'ADDR':<6} | {'SEGMENT ANATOMIQUE':<20} | {'MNÉMONIQUE':<16} | {'OPÉRANDE 1':<18} | {'OPÉRANDE 2':<18} # DESCRIPTION",
            "-" * 112,
        ]
        corps = [inst.formater_ligne() for inst in instructions]
        pied = ["=" * 112]
        return "\n".join(entete + corps + pied)
