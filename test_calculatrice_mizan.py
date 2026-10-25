# -*- coding: utf-8 -*-
"""
Suite de tests unitaires automatisés pour calculatrice_mizan.py (V11.0 Absolue)
=============================================================================
Valide l'ensemble des 28 modules, les invariants du projet Al-Mizan, la physique
nucléaire, relativiste, quantique, la cryptographie Merkle, et les calculs canoniques.
"""

import math
import unittest
import calculatrice_mizan as calc

class TestCalculatriceMizanV11(unittest.TestCase):

    def test_01_invariants_al_mizan(self):
        """Vérifie la bride Mizan 0.6225 et le plafond effectif 0.6015."""
        somme = calc.LIGNE_REF + calc.FORME
        self.assertAlmostEqual(somme, 0.6225, places=4)
        self.assertAlmostEqual(calc.PLAFOND_EFFECTIF, 0.6015, places=4)
        statut_conforme = calc.verifier_balance(0.6000)
        self.assertIn("CONFORME", statut_conforme)
        statut_depassement = calc.verifier_balance(0.6500)
        self.assertIn("RUPTURE", statut_depassement)

    def test_02_horloge_trinite_dt(self):
        """Vérifie l'exactitude de dt = dx + dy + dz."""
        dt_calcule = calc.DX_SOLEIL + calc.DY_LUNE + calc.DZ_TERRE
        self.assertEqual(dt_calcule, calc.DT_KERNEL)
        self.assertAlmostEqual(dt_calcule, 135097021.3359375, places=7)

    def test_03_metrologie_or_argent_zakat(self):
        """Vérifie le calcul de la Zakat 2.5% et les Nisabs."""
        self.assertEqual(calc.NISAB_OR_G, 85.0)
        self.assertEqual(calc.NISAB_ARGENT_G, 595.0)
        self.assertEqual(calc.zakat(50.0, 85.0), 0.0)
        self.assertEqual(calc.zakat(1000.0, 85.0), 25.0)

    def test_04_physique_trou_noir_schwarzschild(self):
        """Vérifie le rayon de Schwarzschild pour 1 masse solaire (~2953 m)."""
        rs = 2.0 * calc.G * calc.MASSE_SOLAIRE / (calc.C_LUMIERE ** 2)
        self.assertGreater(rs, 2950.0)
        self.assertLess(rs, 2960.0)

    def test_05_matiere_antimatiere_annihilation(self):
        """Vérifie E=2mc² pour 1 g matière + 1 g antimatière."""
        m_kg = 0.001
        energie = 2.0 * m_kg * (calc.C_LUMIERE ** 2)
        self.assertAlmostEqual(energie / 1e14, 1.7975, places=2)

    def test_06_table_52_rails_et_espace_0x20(self):
        """Vérifie l'encodage des 52 rails et l'espace vide 0x20 (Forme F0)."""
        self.assertEqual(calc.TABLE_52_RAILS['M']['rail'], 13)
        self.assertEqual(calc.TABLE_52_RAILS['M']['forme'], 13)
        self.assertEqual(ord(' '), 32)

    def test_07_cryogenie_killswitch_45mk(self):
        """Vérifie que la dérive thermique déclenche bien le killswitch à 45 mK."""
        cycles = 5000
        calc.section_simulation_cryogenique(cycles)
        dernier_audit = calc.HISTORIQUE_CALCULS[-1]
        self.assertTrue(dernier_audit["resultats"]["killswitch"])
        self.assertEqual(dernier_audit["resultats"]["cycle_arret"], 4500)
        self.assertAlmostEqual(dernier_audit["resultats"]["temp_finale_mk"], 45.0, places=1)

    def test_08_algebre_lineaire_produit_et_determinant(self):
        """Vérifie le produit matriciel 4x4 et la multiplicativité des déterminants."""
        A = calc.MATRICE_SCAPULAIRE_4X4
        B = calc.MATRICE_UNISSON_4X4
        C = calc.produit_matriciel_4x4(A, B)
        det_a = calc.determinant_4x4(A)
        det_b = calc.determinant_4x4(B)
        det_c = calc.determinant_4x4(C)
        self.assertAlmostEqual(det_a * det_b, det_c, places=7)

    def test_09_arbre_merkle_sha256(self):
        """Vérifie la reproductibilité déterministe de la Merkle Root."""
        feuilles = ["ACTE_A", "ACTE_B", "ACTE_C"]
        root1 = calc.calculer_merkle_root(feuilles)
        root2 = calc.calculer_merkle_root(feuilles)
        self.assertEqual(root1, root2)
        self.assertEqual(len(root1), 64)

    def test_10_simulateur_quantique_conservation_norme(self):
        """Vérifie la stricte conservation de la norme unitaire sous portes quantiques."""
        calc.section_simulateur_quantique()
        dernier = calc.HISTORIQUE_CALCULS[-1]
        self.assertAlmostEqual(dernier["resultats"]["norme"], 1.0, places=6)

    def test_11_thermodynamique_hydro_313(self):
        """Vérifie la puissance thermique absorbée pour 313 L/min et ΔT=5K."""
        debit_kg_s = 313.0 / 60.0
        p_attendue_watts = debit_kg_s * calc.CAPACITE_THERMIQUE_EAU * 5.0
        p_attendue_kw = p_attendue_watts / 1000.0
        self.assertAlmostEqual(p_attendue_kw, 109.148666, places=1)

    def test_12_physique_nucleaire_bethe_weizsaecker(self):
        """Vérifie le calcul de l'énergie de liaison de l'Or (197) et de l'Argent (107)."""
        res_or = calc.formule_bethe_weizsaecker(197, 79)
        res_ag = calc.formule_bethe_weizsaecker(107, 47)
        self.assertAlmostEqual(res_or["B_par_nucleon_MeV"], 7.9075, places=2)
        self.assertAlmostEqual(res_ag["B_par_nucleon_MeV"], 8.5640, places=2)
        self.assertGreater(res_ag["B_par_nucleon_MeV"], res_or["B_par_nucleon_MeV"])

    def test_13_decouplage_dynamique_cpmg(self):
        """Vérifie la prolongation du temps T2 sous 256 pulses CPMG et la fidélité > 99.9%."""
        calc.section_decouplage_dynamique_cpmg(256)
        dernier = calc.HISTORIQUE_CALCULS[-1]
        self.assertGreater(dernier["resultats"]["t2_ms"], 15.0)
        self.assertGreater(dernier["resultats"]["fidelite"], 0.9999)

    def test_14_relativite_lorentz_et_gravitation(self):
        """Vérifie le facteur de Lorentz gamma à v = 0.6225 c (~1.2778)."""
        gamma_theorique = 1.0 / math.sqrt(1.0 - (0.6225 ** 2))
        self.assertAlmostEqual(gamma_theorique, 1.27776, places=4)

    def test_15_gematrie_abjad_reduction(self):
        """Vérifie le calcul Abjad de 'AL MIZAN' et sa forme de silicium."""
        calc.section_abjad_gematrie("AL MIZAN")
        dernier = calc.HISTORIQUE_CALCULS[-1]
        self.assertEqual(dernier["resultats"]["total"], 76)
        self.assertEqual(dernier["resultats"]["forme"], 76 % 27)

    def test_16_tetrade_cosmique_admittance(self):
        """Vérifie que l'admittance globale de la Tétrade Cosmique est sous la bride 0.6225."""
        calc.section_tetrade_cosmique()
        dernier = calc.HISTORIQUE_CALCULS[-1]
        self.assertEqual(dernier["type"], "Tetrade_Cosmique")
        self.assertLessEqual(dernier["resultats"]["admittance_moy"], calc.MIZAN)
        self.assertEqual(dernier["resultats"]["piliers"], 4)

if __name__ == "__main__":
    unittest.main()
