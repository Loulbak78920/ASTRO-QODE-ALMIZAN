# -*- coding: utf-8 -*-
"""
Outil 4 : Inspecteur Matriciel & Explorateur Ontologique (`inspecteur_matriciel.py`)
====================================================================================
Permet d'explorer et d'exporter en texte formaté ou JSON les 4 couches complètes
du dossier `IMAM8MAHDI` :
1. Couche `QUBITS8INFORME` : Les 4 Tablettes Apprises et la Sphère de Bloch.
2. Couche `qubit_physique` : Les 20 États Physiques (Soleil, Terre, Lune) et la Matrice Inversée.
3. Couche `.QUBIT.qubit.LOGIQUE.logique` : Les cycles temporels `dx`, `dy`, `dz`, `dt`.
4. Couche `.ASTRO-Q°ODE` : Les 14 Formes de la Matière du Code, l'Omoplate, les 5 Doigts et la Monade V2.0.
"""

from __future__ import annotations

from typing import Dict

from bibliotheques.lib_anatomie import PipelineCinqDoigts
from bibliotheques.lib_almizan_extension import (
    COMBLE_CIBLE,
    CONSTANTE_MECQUOISE_C,
    CONSTANTE_MEDINOISE_M,
    EPSILON,
    FILE_EXECUTIVE_JEDAFBVHG,
    GARDE_FOUS_ALMIZAN,
    JAUGE_AIR,
    LES_27_FORMES_ETENDUES,
    LES_7_AXIOMES_INFORMES,
    LIGNE_REF,
    MIZAN,
    PHASES_15_CYCLE_HARMONIQUE,
    PLAFOND_EFFECTIF,
    PRODUIT_MEDINOIS,
    PYRAMIDE_TENSORIELLE_4_NIVEAUX,
    RMS,
    ROLES_ALPHABET_AZ_ALMIZAN,
    SphereHolographiqueAlmizan,
    TRIPLE_CYCLE,
    TriadeBitQubitIBit,
    executer_cycle_15_phases,
)
from bibliotheques.lib_informe import (
    MatriceLogiqueComplexe,
    QubitInforme,
    TABLETTE_ALPHABET,
    TABLETTE_CHIFFRES,
    TABLETTE_OPERATEURS,
    TABLETTE_PONCTUATION,
)
from bibliotheques.lib_monade import MonadeSupreme, OMEGA_MONAD_SOUL
from bibliotheques.lib_physique import (
    ETATS_LUNE,
    ETATS_SOLEIL_PLASMA,
    ETATS_TERRE,
    LES_14_FORMES,
    MatriceLogiqueInversee,
)
from bibliotheques.lib_temporelle import HorlogeKernelTemporelle


class InspecteurMatricielAstroQode:
    """Génère des rapports d'inspection complets sur les 4 couches du système."""

    @classmethod
    def rapport_global_dictionnaire(cls) -> Dict[str, object]:
        horloge = HorlogeKernelTemporelle()
        pipeline = PipelineCinqDoigts()
        qubit_eq = QubitInforme.depuis_echelon_thermique(0)

        return {
            "couche_1_qubits8informe": {
                "matrice_4x4": MatriceLogiqueComplexe.exporter_resume_complet(),
                "qubit_informe_equateur_J": {
                    "ket": qubit_eq.representation_ket(),
                    "coordonnees_bloch": qubit_eq.coordonnees_bloch(),
                    "lambda_m": QubitInforme.LAMBDA_INFORME,
                },
            },
            "couche_2_qubit_physique": {
                "total_etats_cumules": MatriceLogiqueInversee.TOTAL_ETATS_CUMULES,
                "analyse_cumulative_division": MatriceLogiqueInversee.analyse_cumulative_division(),
                "analyse_differentielle_soustraction": MatriceLogiqueInversee.analyse_differentielle_soustraction(),
                "fusion_4H_vers_1He": MatriceLogiqueInversee.fusionner_hydrogene_en_helium(4),
                "les_14_formes": [
                    {
                        "index": f.index,
                        "code": f.code_court,
                        "nom": f.nom_complet,
                        "famille": f.famille_astrale,
                        "paradigme": f.paradigme,
                        "role": f.role_systeme,
                    }
                    for f in LES_14_FORMES.values()
                ],
            },
            "couche_3_dimension_temps": horloge.rapport_repartition(),
            "couche_4_astro_qode_biomecanique_et_monade": {
                "pipeline_anatomique": pipeline.tableau_pipeline_complet(),
                "omega_monad_soul": repr(OMEGA_MONAD_SOUL),
                "monade_repos_helium": repr(MonadeSupreme.helium_inerte()),
            },
            "couche_5_extension_almizan_depassement_14_formes": {
                "invariants_metrologiques": {
                    "MIZAN": MIZAN,
                    "LIGNE_REF": LIGNE_REF,
                    "RMS": RMS,
                    "EPSILON": EPSILON,
                    "PLAFOND_EFFECTIF": PLAFOND_EFFECTIF,
                    "COMBLE_CIBLE": COMBLE_CIBLE,
                    "C": CONSTANTE_MECQUOISE_C,
                    "M": CONSTANTE_MEDINOISE_M,
                    "JAUGE_AIR": JAUGE_AIR,
                    "PRODUIT_MEDINOIS": PRODUIT_MEDINOIS,
                    "TRIPLE": TRIPLE_CYCLE,
                    "garde_fous": GARDE_FOUS_ALMIZAN,
                },
                "axiomes_informes_7": [a.__dict__ for a in LES_7_AXIOMES_INFORMES],
                "les_27_formes_etendues": [f.__dict__ for f in LES_27_FORMES_ETENDUES.values()],
                "alphabet_52_rails_AZ": ROLES_ALPHABET_AZ_ALMIZAN,
                "file_executive_jedafbvhg": FILE_EXECUTIVE_JEDAFBVHG,
                "sphere_holographique_22_5mK": SphereHolographiqueAlmizan.cartographier(22.5),
                "triade_bit_qubit_ibit": TriadeBitQubitIBit.synchroniser(8),
                "pyramide_tensorielle_4_niveaux": PYRAMIDE_TENSORIELLE_4_NIVEAUX,
                "cycle_15_phases": executer_cycle_15_phases("almizan fond forme"),
            },
        }

    @classmethod
    def formater_rapport_console(cls) -> str:
        div = MatriceLogiqueInversee.analyse_cumulative_division()
        diff = MatriceLogiqueInversee.analyse_differentielle_soustraction()
        horloge = HorlogeKernelTemporelle().rapport_repartition()
        pipeline = PipelineCinqDoigts().tableau_pipeline_complet()

        lignes = [
            "=" * 96,
            "RAPPORT D'INSPECTION INTÉGRALE DU SYSTÈME ASTRO-Q°ODE (V1.0 & V2.0)",
            "=" * 96,
            "",
            "[1] COUCHE QUBITS8INFORME — LES 4 TABLETTES APPRISES & SPHÈRE DE BLOCH",
            f"  • Tablette Chiffres    : {len(TABLETTE_CHIFFRES)} échelons discrets de -9 à +9 (Niveau 1: 'i' Kelvin | Niveau 2: 'I' Joules)",
            f"  • Tablette Alphabet    : {len(TABLETTE_ALPHABET)} lettres [A ; S] (États: a, A, alpha_a..alpha_s, omega_A..omega_S)",
            f"  • Tablette Ponctuation : {len(TABLETTE_PONCTUATION)} symboles × 4 états (! -> ¡, ? -> ¿, . -> °, autres -> « x »)",
            f"  • Tablette Opérateurs  : {len(TABLETTE_OPERATEURS)} axes × 3 états (+/&&/∪, -/!/∖, ×/||/∩, ÷/NAND/⊘, =/==/≡, >/&& >/⊃, </&& </⊂)",
            f"  • Qubit Informe (0 i)  : {QubitInforme.depuis_echelon_thermique(0).representation_ket()}",
            "",
            "[2] COUCHE QUBIT_PHYSIQUE — LES 20 ÉTATS DE LA MATIÈRE & OPÉRATIONS INVERSÉES",
            f"  • Soleil / Plasma      : {len(ETATS_SOLEIL_PLASMA)} états (Photosphérique, Chromosphérique, Coronaire, Cœur de fusion) + origine Hélium 0 -> Fusion 4H = 1He (Ratio = {div['ratio_fusion_hydrogene_helium']})",
            f"  • Planète Terre        : {len(ETATS_TERRE)} états (3 Solides, 1 Liquide géodynamo, 3 Gazeux)",
            f"  • Satellite Lune       : {len(ETATS_LUNE)} états (6 Solides fossilisés, 0 Liquide, 3 Gazeux d'exosphère)",
            f"  • Total Cumulé         : {MatriceLogiqueInversee.TOTAL_ETATS_CUMULES} états",
            f"  • Division Globale     : {int(div['total_solides'])} Solides / {int(div['total_gazeux'])} Gazeux = {div['ratio_solides_sur_gazeux_arrondi']} | Solides Lune/Terre = {div['ratio_solides_lune_sur_terre']}",
            f"  • Soustraction Diff.   : Terre(3S-1L)={diff['differentiel_interne_terrestre_solides_moins_liquide']} | Lune-Terre(6S-3S)={diff['ecart_solidification_lune_moins_terre']} | Liquide(1-0)={diff['ecart_fluidite_magnetique_terre_moins_lune']} | Gaz(3-3)={diff['differentiel_atmospherique_gaz_terre_moins_lune']}",
            "",
            "[3] COUCHE .QUBIT.qubit.LOGIQUE.logique — CONSTANTES D'HORLOGE DU KERNEL",
            f"  • CLOCK_DX_SOLEIL      = {horloge['constantes']['CLOCK_DX_SOLEIL']} ({horloge['poids_relatifs_pourcent']['dx_soleil_pct']} %)",
            f"  • CLOCK_DY_LUNE        = {horloge['constantes']['CLOCK_DY_LUNE']} ({horloge['poids_relatifs_pourcent']['dy_lune_pct']} %)",
            f"  • CLOCK_DZ_TERRE       = {horloge['constantes']['CLOCK_DZ_TERRE']} ({horloge['poids_relatifs_pourcent']['dz_terre_pct']} %) [Brut = {horloge['constantes']['CLOCK_DZ_TERRE_BRUT']}]",
            f"  • CLOCK_DT_KERNEL (dt) = {horloge['constantes']['CLOCK_DT_KERNEL']} (100.00 %)",
            "",
            "[4] COUCHE .ASTRO-Q°ODE — LES 14 FORMES DE LA MATIÈRE DU CODE (0 À 13)",
        ]
        for idx, forme in LES_14_FORMES.items():
            lignes.append(
                f"  • [{idx:02d}] {forme.code_court:<12} | {forme.famille_astrale:<18} | {forme.paradigme:<14} | {forme.role_systeme}"
            )
        lignes.append("")
        lignes.append("[5] PIPELINE D'EXÉCUTION BIOMÉCANIQUE (OMOPLATE -> BRAS -> 5 DOIGTS)")
        for seg in pipeline:
            lignes.append(
                f"  • {str(seg['segment']):<20} -> {str(seg['role_systeme']):<24} | Symbole: {str(seg['symbole']):<24} | {seg['paradigme']}"
            )
        lignes.append("")
        lignes.append("[6] COUCHE 5 AL-MIZAN — DÉPASSEMENT DES 14 FORMES (FRACTALE 1 + 13 ⊕ 13 = 27 FORMES : F0..F26)")
        lignes.append(
            f"  • Invariants Scellés   : MIZAN={MIZAN} | LIGNE={LIGNE_REF} | RMS={RMS} | ε={EPSILON} | Plafond={PLAFOND_EFFECTIF} | Comble={COMBLE_CIBLE}"
        )
        lignes.append(
            f"  • Substance            : C={CONSTANTE_MECQUOISE_C} | M={CONSTANTE_MEDINOISE_M} | JAUGE_AIR={JAUGE_AIR} | PRODUIT={PRODUIT_MEDINOIS} | TRIPLE={TRIPLE_CYCLE}"
        )
        lignes.append(
            f"  • Alphabet Étendu      : 26 Majuscules [A..Z] + 26 Minuscules [a..z] (52 rails) | File exécutive : {'-'.join(FILE_EXECUTIVE_JEDAFBVHG)}"
        )
        lignes.append(
            f"  • Pyramide Tensorielle : 0D Scalaire(0) -> 1D Vecteur(19) -> 2D Matrice(-9800) -> 3D+ Tenseur(-998000)"
        )
        lignes.append(
            f"  • Cycle Harmonique     : 15 Phases ({', '.join(PHASES_15_CYCLE_HARMONIQUE[:5])} ... {PHASES_15_CYCLE_HARMONIQUE[-1]})"
        )
        lignes.append("  • Octave 2 Duale (Formes F14 à F26 — Au-delà du Seuil 13 sous confinement D=[0.122, 0.6225]) :")
        for idx in range(14, 27):
            fe = LES_27_FORMES_ETENDUES[idx]
            lignes.append(
                f"    - [{idx:02d}] {fe.code_court:<15} | Géom: {fe.forme_geometrique:<28} | φ={fe.phase_rad:<10.4f} | D={fe.image_fonction_d:.4f}"
            )
        lignes.append("=" * 96)
        return "\n".join(lignes)
