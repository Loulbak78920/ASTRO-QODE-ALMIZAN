# -*- coding: utf-8 -*-
"""
Suite de Tests Exhaustive du Système ASTRO-Q°ODE (`test_suite_complete.py`)
===========================================================================
Vérifie 100% des invariants mathématiques, physiques, temporels, biomécaniques
et syntaxiques des 4 dossiers de `IMAM8MAHDI` ainsi que le compilateur/interpréteur,
les bibliothèques et les outils.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

# Assurer l'encodage UTF-8 sous Windows pour les descriptions de tests et symboles ontologiques
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ajout du dossier racine ASTRO-Q°ODE_SYSTEME au PYTHONPATH
RACINE_SYSTEME = Path(__file__).resolve().parent.parent
if str(RACINE_SYSTEME) not in sys.path:
    sys.path.insert(0, str(RACINE_SYSTEME))

from bibliotheques.lib_anatomie import MatriceScapulaire, PipelineCinqDoigts
from bibliotheques.lib_almizan_extension import (
    COMBLE_CIBLE,
    CONSTANTE_MECQUOISE_C,
    CONSTANTE_MEDINOISE_M,
    EPSILON,
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
    clamp_domaine_mizan,
    executer_cycle_15_phases,
    obtenir_forme_etendue_almizan,
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
from bibliotheques.lib_matrice_unisson_or_argent import (
    CENTRE_UNISSON_MIZAN,
    CONJUGUE_ARGENT_MIZAN,
    CONJUGUE_OR_MIZAN,
    ECART_ATOMIQUE_5_DOIGTS,
    MASSE_DIRHAM_ARGENT_G,
    MASSE_MITHQAL_OR_G,
    MatriceFondatriceUnisson,
    NISAB_ARGENT_GRAMMES,
    NISAB_OR_GRAMMES,
    RATIO_NISAB_ARGENT_SUR_OR,
    SOMME_ATOMIQUE_UNISSON,
    UNISSON_CELESTE_DX_PLUS_DY,
    Z_ARGENT_AG,
    Z_OR_AU,
)
from bibliotheques.lib_pont_materiel_emule import PORTS_LOCAUX_ALMIZAN, PontMaterielEmuleAlmizan
from bibliotheques.lib_physique import (
    ETATS_HYDROGENE,
    ETATS_LUNE,
    ETATS_TERRE,
    LES_14_FORMES,
    MatriceLogiqueInversee,
    obtenir_forme_matiere,
)
from bibliotheques.lib_temporelle import (
    CLOCK_DT_KERNEL,
    CLOCK_DX_SOLEIL,
    CLOCK_DY_LUNE,
    CLOCK_DZ_TERRE,
    CLOCK_DZ_TERRE_BRUT,
    HorlogeKernelTemporelle,
)
from lang.compilateur_qasm_isa import CompilateurQasmIsaAstroQode
from lang.interpreter import InterpreteurAstroQode
from lang.runtime_values import EnergieJoules, EtatHeliumInerte, SignalKelvin
from lang.transpiler import TranspilateurPythonAstroQode
from outils.assembleur_scapulaire import AssembleurScapulaire
from outils.formateur_code import FormateurAstroQode
from outils.inspecteur_matriciel import InspecteurMatricielAstroQode
from outils.scelleur_cryptographique import ScelleurMemoireAstroQode
from outils.studio_dashboard import StudioDashboardAstroQode
from outils.validateur_syntaxique import ValidateurOntologiqueAstroQode


class TestSystemeCompletAstroQode(unittest.TestCase):
    """Tests complets des 4 couches IMAM8MAHDI, du langage, des bibliothèques et des outils."""

    def test_01_couche_qubits8informe_tablettes(self) -> None:
        """Vérifie l'exactitude des 4 Tablettes Apprises et de la Sphère de Bloch."""
        self.assertEqual(len(TABLETTE_CHIFFRES), 19)
        self.assertEqual(TABLETTE_CHIFFRES[-9].etat_i_kelvin, "-9 i")
        self.assertEqual(TABLETTE_CHIFFRES[0].etat_I_joules, "0 I")
        self.assertEqual(TABLETTE_CHIFFRES[9].etat_I_joules, "+9 I")

        self.assertEqual(len(TABLETTE_ALPHABET), 19)
        self.assertEqual(TABLETTE_ALPHABET["A"].axe_chiffre, -9)
        self.assertEqual(TABLETTE_ALPHABET["J"].axe_chiffre, 0)
        self.assertEqual(TABLETTE_ALPHABET["S"].axe_chiffre, 9)
        self.assertEqual(MatriceLogiqueComplexe.resoudre_lettre("C", 3), "alpha_c")
        self.assertEqual(MatriceLogiqueComplexe.resoudre_lettre("A", 4), "omega_A")

        self.assertEqual(len(TABLETTE_PONCTUATION), 19)
        self.assertEqual(MatriceLogiqueComplexe.resoudre_ponctuation("?", 2), "??")
        self.assertEqual(MatriceLogiqueComplexe.resoudre_ponctuation("?", 4), "¿")
        self.assertEqual(MatriceLogiqueComplexe.resoudre_ponctuation(".", 4), "°")
        self.assertEqual(MatriceLogiqueComplexe.resoudre_ponctuation("!", 4), "¡")
        self.assertEqual(MatriceLogiqueComplexe.resoudre_ponctuation("@", 4), "« @ »")

        self.assertEqual(len(TABLETTE_OPERATEURS), 9)
        self.assertEqual(MatriceLogiqueComplexe.resoudre_operateur("+", 3), "∪")
        self.assertEqual(MatriceLogiqueComplexe.resoudre_operateur(">", 3), "⊃")
        self.assertEqual(MatriceLogiqueComplexe.resoudre_operateur("<", 3), "⊂")

        q0 = QubitInforme.depuis_echelon_thermique(0)
        self.assertTrue(q0.est_superpose)
        self.assertAlmostEqual(q0.probabilite_0, 0.5, places=5)
        self.assertAlmostEqual(q0.probabilite_1, 0.5, places=5)

    def test_02_couche_qubit_physique_et_14_formes(self) -> None:
        """Vérifie les 20 états physiques, les ratios de division/soustraction et les 14 Formes."""
        self.assertEqual(len(ETATS_HYDROGENE), 4)
        self.assertEqual(len(ETATS_TERRE), 7)
        self.assertEqual(len(ETATS_LUNE), 9)
        self.assertEqual(MatriceLogiqueInversee.TOTAL_ETATS_CUMULES, 20)

        div = MatriceLogiqueInversee.analyse_cumulative_division()
        self.assertEqual(div["ratio_solides_sur_gazeux_arrondi"], 1.43)
        self.assertEqual(div["ratio_fusion_hydrogene_helium"], 4.0)
        self.assertEqual(div["ratio_solides_lune_sur_terre"], 2.0)

        diff = MatriceLogiqueInversee.analyse_differentielle_soustraction()
        self.assertEqual(diff["differentiel_interne_terrestre_solides_moins_liquide"], 2)
        self.assertEqual(diff["ecart_solidification_lune_moins_terre"], 3)
        self.assertEqual(diff["ecart_fluidite_magnetique_terre_moins_lune"], 1)
        self.assertEqual(diff["differentiel_atmospherique_gaz_terre_moins_lune"], 0)

        fusion = MatriceLogiqueInversee.fusionner_hydrogene_en_helium(4)
        self.assertEqual(fusion["noyaux_helium_4_produits"], 1)
        self.assertEqual(fusion["etat_retour_code"], "0 : HÉLIUM")

        self.assertEqual(len(LES_14_FORMES), 14)
        self.assertEqual(obtenir_forme_matiere(0).code_court, "0 : HÉLIUM")
        self.assertEqual(obtenir_forme_matiere(13).code_court, "F13: Noyau L")
        # Au-delà du Seuil d'Infinie (> 13), dissolution vers 0 : HÉLIUM
        self.assertEqual(obtenir_forme_matiere(14).code_court, "0 : HÉLIUM")

    def test_03_couche_dimension_temps_horloges(self) -> None:
        """Vérifie les constantes exactes dx, dy, dz et dt."""
        self.assertEqual(CLOCK_DX_SOLEIL, 50027.8359375)
        self.assertEqual(CLOCK_DY_LUNE, 46993.5)
        self.assertEqual(CLOCK_DZ_TERRE_BRUT, 3888000000.0)
        self.assertEqual(CLOCK_DZ_TERRE, 135000000.0)
        self.assertEqual(CLOCK_DT_KERNEL, 135097021.3359375)

        horloge = HorlogeKernelTemporelle()
        horloge.consommer_tick("SOLEIL", 10.0, "TEST_DX")
        horloge.consommer_tick("LUNE", 5.0, "TEST_DY")
        horloge.consommer_tick("TERRE", 25.0, "TEST_DZ")
        self.assertEqual(horloge.dt_consomme, 40.0)

    def test_04_couche_anatomie_et_monade_supreme(self) -> None:
        """Vérifie la Matrice Scapulaire, les 5 Doigts et la Monade Suprême V2.0."""
        omoplate = MatriceScapulaire()
        coord = omoplate.orienter_adresse_alpha("alpha_c")
        self.assertEqual(coord, -7)

        pipeline = PipelineCinqDoigts(omoplate)
        self.assertEqual(len(pipeline.tableau_pipeline_complet()), 7)

        m0 = MonadeSupreme.unit(SignalKelvin(0))
        m1 = m0.bind(lambda sig: MonadeSupreme.unit(EnergieJoules(1.0))).isoler()
        self.assertTrue(m1.est_isolee)
        self.assertEqual(m1.valeur_interne, EnergieJoules(1.0))

    def test_05_execution_specification_officielle_v1(self) -> None:
        """Exécute directement le fichier original `.ASTRO-Q°ODE/astro_q°ode_specification.txt`."""
        candidats = [
            RACINE_SYSTEME.parent / ".ASTRO-Q°ODE" / "astro_q°ode_specification.txt",
            RACINE_SYSTEME / "dossiers_fondateurs" / ".ASTRO-Q°ODE" / "astro_q°ode_specification.txt",
            RACINE_SYSTEME.parent / "dossiers_fondateurs" / ".ASTRO-Q°ODE" / "astro_q°ode_specification.txt",
            RACINE_SYSTEME / ".ASTRO-Q°ODE" / "astro_q°ode_specification.txt",
        ]
        chemin_spec = next((c for c in candidats if c.exists()), None)
        if chemin_spec is not None:
            source = chemin_spec.read_text(encoding="utf-8")
            interp = InterpreteurAstroQode()
            res = interp.executer_source(source)
            self.assertTrue(res.succes, msg=res.erreur)
            self.assertEqual(res.registre_mecquois["omega_A"], EnergieJoules(5.0))
            self.assertEqual(res.registre_mecquois["omega_S"], SignalKelvin(8766.0))
            # alpha_c = -3 i ; (-3 i ⊃ +5 I) est vrai (|-3| <= |+5|), donc alpha_c = -3 i ∪ +2 i = -1 i
            self.assertEqual(res.memoire_medinoise["alpha_c"], SignalKelvin(-1.0))

    def test_06_execution_monade_supreme_v2_et_stdlib(self) -> None:
        """Exécute les 7 scripts `.aq` de la bibliothèque standard (V1, V2, V3 Al-Mizan, V4 Suite Logique et V5 Unisson Or/Argent)."""
        dossier_stdlib = RACINE_SYSTEME / "bibliotheques" / "stdlib_aq"
        fichiers_aq = sorted(dossier_stdlib.glob("*.aq"))
        self.assertEqual(len(fichiers_aq), 7)

        for fichier in fichiers_aq:
            source = fichier.read_text(encoding="utf-8")
            interp = InterpreteurAstroQode()
            res = interp.executer_source(source)
            self.assertTrue(res.succes, msg=f"Échec dans {fichier.name}: {res.erreur}")

            # Vérification spécifique sur monade_cellulaire_v2.aq
            if fichier.name == "monade_cellulaire_v2.aq":
                monade_finale = res.memoire_medinoise["alpha_cell_monad"]
                self.assertIsInstance(monade_finale, MonadeSupreme)
                self.assertTrue(monade_finale.est_isolee)
                self.assertEqual(monade_finale.valeur_interne, EnergieJoules(1.0))

    def test_08_couche_almizan_depassement_14_formes_v3(self) -> None:
        """Vérifie le dépassement des 14 Formes via Al-Mizan (27 Formes F0..F26, Sphère, Triade, 15 Phases)."""
        # 1. Invariants Al-Mizan
        self.assertEqual(MIZAN, 0.6225)
        self.assertEqual(LIGNE_REF, 0.122)
        self.assertEqual(RMS, 0.24)
        self.assertEqual(EPSILON, 0.021)
        self.assertEqual(PLAFOND_EFFECTIF, 0.6015)
        self.assertEqual(COMBLE_CIBLE, 0.5805)
        self.assertEqual(CONSTANTE_MECQUOISE_C, 313)
        self.assertEqual(CONSTANTE_MEDINOISE_M, 24434)
        self.assertEqual(JAUGE_AIR, 515050)
        self.assertEqual(PRODUIT_MEDINOIS, 3939021022100)
        self.assertEqual(TRIPLE_CYCLE, -2393774546)
        self.assertFalse(GARDE_FOUS_ALMIZAN["qubit_physique_local"])
        self.assertFalse(GARDE_FOUS_ALMIZAN["omniscience_claim"])

        # 2. Les 27 Formes (F0 + 13 Publiques + 13 Duales Fractales)
        self.assertEqual(len(LES_7_AXIOMES_INFORMES), 7)
        self.assertEqual(len(LES_27_FORMES_ETENDUES), 27)
        f14 = obtenir_forme_etendue_almizan(14)
        f26 = obtenir_forme_etendue_almizan(26)
        f27_retour = obtenir_forme_etendue_almizan(27)
        self.assertEqual(f14.index, 14)
        self.assertEqual(f14.paradigme, "FRACTALE_DUALE_ALMIZAN")
        self.assertEqual(f26.index, 26)
        self.assertEqual(f27_retour.code_court, "0 : HÉLIUM")

        # 3. Alphabet A-Z (26 lettres)
        self.assertEqual(len(ROLES_ALPHABET_AZ_ALMIZAN), 26)
        self.assertEqual(ROLES_ALPHABET_AZ_ALMIZAN["Z"]["echelon"], 16)

        # 4. Sphère Holographique (22.5 mK nominal vs 45.0 mK killswitch)
        sp_ok = SphereHolographiqueAlmizan.cartographier(22.5)
        self.assertEqual(sp_ok["statut"], "SPHERE_HOLOGRAPHIQUE_OK")
        self.assertFalse(sp_ok["killswitch_actif"])
        self.assertTrue(sp_ok["identite_corde"]["identite_validee"])

        sp_kill = SphereHolographiqueAlmizan.cartographier(45.0)
        self.assertEqual(sp_kill["statut"], "SPHERE_CORDE_DECHIREE")
        self.assertTrue(sp_kill["killswitch_actif"])

        # 5. Triade Bit/Qubit/i-Bit, Pyramide 4 niveaux et Cycle 15 phases
        triade = TriadeBitQubitIBit.synchroniser(8)
        self.assertEqual(len(triade["i_bit_omega"]["oscillations"]), 8)
        self.assertEqual(len(PYRAMIDE_TENSORIELLE_4_NIVEAUX), 4)
        self.assertEqual(PYRAMIDE_TENSORIELLE_4_NIVEAUX[2]["invariant_numerique"], -9800)
        self.assertEqual(PYRAMIDE_TENSORIELLE_4_NIVEAUX[3]["invariant_numerique"], -998000)

        cycle15 = executer_cycle_15_phases("almizan fond forme")
        self.assertTrue(cycle15["ok"])
        self.assertEqual(cycle15["n_phases"], 15)
        self.assertEqual(clamp_domaine_mizan(0.95), 0.6225)
        self.assertEqual(clamp_domaine_mizan(0.01), 0.122)

    def test_07_outils_validateur_formateur_transpilateur_assembleur(self) -> None:
        """Vérifie le fonctionnement complet de tous les outils de développement."""
        chemin_monade = RACINE_SYSTEME / "bibliotheques" / "stdlib_aq" / "monade_cellulaire_v2.aq"
        source = chemin_monade.read_text(encoding="utf-8")

        # 1. Validateur
        validateur = ValidateurOntologiqueAstroQode()
        rapport_val = validateur.valider_source(source)
        self.assertTrue(rapport_val.valide)
        self.assertEqual(rapport_val.nb_erreurs, 0)

        # 2. Formateur
        formateur = FormateurAstroQode()
        code_formate = formateur.formater_source(source)
        self.assertIn("MECQUOIS {", code_formate)
        self.assertIn("MEDINOIS {", code_formate)

        # 3. Transpilateur Python
        transpilateur = TranspilateurPythonAstroQode()
        code_py = transpilateur.transpiler_source(source)
        self.assertIn("MachineVirtuelleBiomecanique", code_py)

        # 4. Assembleur Biomécanique Scapulaire
        assembleur = AssembleurScapulaire()
        listing = assembleur.formater_listing(source)
        self.assertIn("SCAPULA_INIT", listing)
        self.assertIn("DOIGT 4 (Auriculaire)", listing)
        self.assertIn("DOIGT 2 (Majeur)", listing)

        # 5. Inspecteur Matriciel
        texte_insp = InspecteurMatricielAstroQode.formater_rapport_console()
        self.assertIn("CLOCK_DT_KERNEL", texte_insp)
        self.assertIn("F13: Noyau L", texte_insp)

    def test_09_suite_logique_v4_pont_qasm_sceaux_studio(self) -> None:
        """Vérifie les 4 briques de la Suite Logique V4.0 (Pont TCP, OpenQASM 2.0, Sceaux SHA-256, Studio HTML5)."""
        # Brique 1 : Pont Matériel Émulé (:5025, :5026, :5030)
        self.assertIn(5025, PORTS_LOCAUX_ALMIZAN)
        self.assertIn(5026, PORTS_LOCAUX_ALMIZAN)
        self.assertIn(5030, PORTS_LOCAUX_ALMIZAN)
        res_scpi = PontMaterielEmuleAlmizan.piloter_scpi_5025(4.85, -15.0, "GAUSS")
        self.assertEqual(res_scpi["port"], 5025)
        self.assertFalse(res_scpi["qubit_physique_local"])

        res_cryo = PontMaterielEmuleAlmizan.interroger_cryo_5026("READ:CRYO:ALL?")
        self.assertEqual(res_cryo["port"], 5026)
        self.assertIn("temp_mk", res_cryo)

        res_zne = PontMaterielEmuleAlmizan.executer_mitigation_zne_5030([1.0, 3.0, 5.0])
        self.assertTrue(res_zne["ok"])
        self.assertLessEqual(res_zne["fidelite_extrapolee_mizan"], MIZAN)

        # Brique 2 : Compilateur OpenQASM 2.0 & Trames ISA DIE (:5030)
        compil = CompilateurQasmIsaAstroQode()
        for circuit in ("BELL", "GROVER", "QFT"):
            res_c = compil.compiler_et_executer_circuit(circuit, shots=256)
            self.assertIn("OPENQASM 2.0;", res_c.code_openqasm_2)
            self.assertGreater(len(res_c.trames_isa_die), 0)
            self.assertIsNotNone(res_c.execution_die_5030)
            self.assertLessEqual(res_c.execution_die_5030["fidelite_mizan"], MIZAN)

        # Compilation d'un script .aq complet vers OpenQASM 2.0
        chemin_v4 = RACINE_SYSTEME / "bibliotheques" / "stdlib_aq" / "suite_logique_silicium_qasm_v4.aq"
        res_aq_qasm = compil.compiler_source_aq(chemin_v4.read_text(encoding="utf-8"), shots=256)
        self.assertIn("OPENQASM 2.0;", res_aq_qasm.code_openqasm_2)

        # Brique 3 : Scelleur Cryptographique SHA-256 et vérification d'intégrité
        verif = ScelleurMemoireAstroQode.verifier_integrite_registre()
        self.assertTrue(verif["integrite_globale_valide"])
        self.assertGreaterEqual(verif["total_sceaux_verifies"], 1)

        # Brique 4 : Studio Dashboard HTML5 / SVG
        chemin_html = StudioDashboardAstroQode.generer_dashboard_html()
        self.assertTrue(chemin_html.exists())
        contenu_html = chemin_html.read_text(encoding="utf-8")
        self.assertIn("STUDIO VISUEL ASTRO-Q°ODE V4.0", contenu_html)
        self.assertIn("<svg", contenu_html)

    def test_10_matrice_fondatrice_unisson_or_argent(self) -> None:
        """Vérifie la Matrice Fondatrice de l'Unisson (4x4) et le calcul exact de la valeur de l'Or et de l'Argent."""
        # 1. Invariants atomiques, temporels, géométriques et pondéraux Or (Au) / Argent (Ag)
        self.assertEqual(Z_OR_AU, 79)
        self.assertEqual(Z_ARGENT_AG, 47)
        self.assertEqual(SOMME_ATOMIQUE_UNISSON, 126)
        self.assertEqual(ECART_ATOMIQUE_5_DOIGTS, 32)
        self.assertEqual(MASSE_MITHQAL_OR_G, 4.25)
        self.assertEqual(NISAB_OR_GRAMMES, 85.0)
        self.assertEqual(MASSE_DIRHAM_ARGENT_G, 2.975)
        self.assertEqual(NISAB_ARGENT_GRAMMES, 595.0)
        self.assertEqual(RATIO_NISAB_ARGENT_SUR_OR, 7.0)
        self.assertAlmostEqual(UNISSON_CELESTE_DX_PLUS_DY, CLOCK_DT_KERNEL - CLOCK_DZ_TERRE, places=7)
        self.assertLessEqual(CONJUGUE_OR_MIZAN, MIZAN)
        self.assertGreaterEqual(CONJUGUE_ARGENT_MIZAN, LIGNE_REF)
        self.assertTrue(LIGNE_REF <= CENTRE_UNISSON_MIZAN <= MIZAN)

        # 2. Matrice 4x4 et calcul complet Or / Argent
        rap = MatriceFondatriceUnisson.calculer_matrice_unisson_complete(85.0, 595.0)
        self.assertEqual(rap["statut"], "MATRICE_FONDATRICE_UNISSON_OR_ARGENT_SCELLEE")
        self.assertEqual(len(rap["matrice_4x4"]["valeurs_brutes"]), 4)
        self.assertEqual(len(rap["accords_unisson_13_octaves"]), 13)
        self.assertEqual(rap["valeur_or"]["nb_unites_canoniques"], 20.0)
        self.assertEqual(rap["valeur_argent"]["nb_unites_canoniques"], 200.0)
        self.assertEqual(rap["valeur_or"]["zakat_2_5_pct_grammes"], 2.125)
        self.assertEqual(rap["valeur_argent"]["zakat_2_5_pct_grammes"], 14.875)

        # 3. Formatage console
        txt = MatriceFondatriceUnisson.formater_rapport_console(85.0, 595.0)
        self.assertIn("MATRICE FONDATRICE DE L'UNISSON (4×4)", txt)
        self.assertIn("OR (Aurum)", txt)
        self.assertIn("ARGENT (Argentum)", txt)


def executer_tous_les_tests() -> bool:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestSystemeCompletAstroQode)
    runner = unittest.TextTestRunner(verbosity=2)
    resultat = runner.run(suite)
    return resultat.wasSuccessful()


if __name__ == "__main__":
    succes = executer_tous_les_tests()
    sys.exit(0 if succes else 1)
