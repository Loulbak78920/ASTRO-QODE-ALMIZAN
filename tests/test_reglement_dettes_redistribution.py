# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""Tests du module de règlement des dettes et de redistribution."""

import math
import unittest
from fractions import Fraction

from oeuvre_universelle.reglement_dettes_redistribution import (
    NISAB_ARGENT_GRAMMES,
    NISAB_OR_GRAMMES,
    SEUIL_NISAB_ARGENT_EUR,
    TAUX_RIBA_MAXIMUM_AUTORISE,
    TAUX_ZAKAT_ANNUEL,
    capacite_remboursement,
    categories_coraniques,
    conservation_flux,
    continuite_zakat,
    indice_justice_paix,
    parabole_abondance,
    ponts_quatre_piliers,
    qard_hasan_vs_riba,
    redistribution_inegalite,
    reglement_insolvabilite,
    resoudre,
    zakat_stabilisateur,
    zakat_legale,
)
from oeuvre_universelle.reglement_dettes_redistribution import succession_fixes, verifier


class TestConstantesEtZakat(unittest.TestCase):
    def test_taux_et_nisab(self):
        self.assertAlmostEqual(TAUX_ZAKAT_ANNUEL, 0.025, places=12)
        self.assertAlmostEqual(NISAB_OR_GRAMMES, 85.0, places=12)
        self.assertAlmostEqual(NISAB_ARGENT_GRAMMES, 595.0, places=12)
        self.assertAlmostEqual(SEUIL_NISAB_ARGENT_EUR, 595.0 * 1000.0 / 1150.0, places=9)
        self.assertEqual(TAUX_RIBA_MAXIMUM_AUTORISE, 0.0)

    def test_zakat_seuil(self):
        au_dessus = zakat_legale(1_000.0)
        self.assertTrue(au_dessus["assujetti"])
        self.assertAlmostEqual(au_dessus["zakat_eur"], 25.0, places=12)
        self.assertAlmostEqual(au_dessus["part_par_categorie_eur"], 3.125, places=12)

        en_dessous = zakat_legale(500.0)
        self.assertFalse(en_dessous["assujetti"])
        self.assertEqual(en_dessous["zakat_eur"], 0.0)


class TestCategoriesEtDettes(unittest.TestCase):
    def test_huit_categories(self):
        categories = categories_coraniques()
        self.assertEqual(categories["nombre"], 8)
        self.assertEqual(Fraction(categories["somme_poids"]), 1)
        self.assertTrue(all(Fraction(c["poids"]) > 0 for c in categories["categories"]))
        self.assertIn("gharimin", [c["cle"] for c in categories["categories"]])

    def test_insolvabilite(self):
        reglement = reglement_insolvabilite(1_000.0, 300.0, 200.0)
        self.assertAlmostEqual(reglement["verse_eur"], 300.0, places=12)
        self.assertAlmostEqual(reglement["reste_eur"], 500.0, places=12)
        self.assertAlmostEqual(reglement["scenarios"][1]["reste_eur"], 0.0, places=12)

    def test_remise_excessive_plafonnee(self):
        reglement = reglement_insolvabilite(1_000.0, 300.0, 1_000.0)
        self.assertAlmostEqual(reglement["remise_effective_eur"], 700.0, places=12)
        self.assertEqual(reglement["reste_eur"], 0.0)
        self.assertTrue(reglement["solde"])

    def test_qard_vs_riba(self):
        comparaison = qard_hasan_vs_riba(10_000.0, 0.05, 10)
        self.assertEqual(comparaison["remboursement_qard_eur"], 10_000.0)
        self.assertAlmostEqual(
            comparaison["surcout_riba_eur"],
            10_000.0 * (1.05 ** 10 - 1.0),
            places=9,
        )

    def test_capacite(self):
        capacite = capacite_remboursement(3_000.0, 2_200.0, 4_000.0)
        self.assertAlmostEqual(capacite["capacite_eur"], 800.0, places=12)
        self.assertEqual(capacite["duree_ans"], 5)
        self.assertEqual(capacite["insolvable"]["capacite_eur"], 0.0)
        self.assertIsNone(capacite["insolvable"]["duree_ans"])


class TestSuccessionEtAgregats(unittest.TestCase):
    def test_succession_exacte(self):
        succession = succession_fixes(72_000.0)
        self.assertEqual(Fraction(succession["somme_parts"]), 1)
        self.assertAlmostEqual(succession["ratio_fils_fille"], 2.0, places=12)
        self.assertAlmostEqual(succession["montants_eur"]["conjoint"], 9_000.0, places=9)
        self.assertAlmostEqual(succession["montants_eur"]["fils"], 26_000.0, places=9)
        self.assertAlmostEqual(succession["montants_eur"]["fille"], 13_000.0, places=9)
        self.assertAlmostEqual(succession["somme_montants_eur"], 72_000.0, places=9)

    def test_stabilisateur(self):
        flux = zakat_stabilisateur(1_000_000_000_000.0)
        self.assertAlmostEqual(flux["injection_annuelle_eur"], 25_000_000_000.0, places=3)
        self.assertAlmostEqual(flux["rotation_ans"], 40.0, places=12)

    def test_inegalite(self):
        inegalite = redistribution_inegalite()
        self.assertAlmostEqual(inegalite["gini_initial"], 0.25, places=12)
        self.assertAlmostEqual(inegalite["scenarios"][0]["gini_apres"], 0.125, places=12)
        self.assertAlmostEqual(inegalite["scenarios"][1]["gini_apres"], 0.0, places=12)

    def test_abondance(self):
        parabole = parabole_abondance(25.0)
        self.assertEqual(parabole["facteur"], 700)
        self.assertAlmostEqual(parabole["flux_illustratif_eur"], 17_500.0, places=9)

    def test_continuite(self):
        continuite = continuite_zakat()
        self.assertAlmostEqual(continuite["demi_vie_ans"], 27.3778512338, places=9)
        self.assertAlmostEqual(
            (1.0 - TAUX_ZAKAT_ANNUEL) ** continuite["demi_vie_ans"], 0.5, places=12
        )
        self.assertAlmostEqual(continuite["facteur_restant"], 0.975 ** 40, places=12)

    def test_conservation(self):
        flux = conservation_flux(25.0, 0.10)
        self.assertAlmostEqual(flux["reserve_eur"], 2.5, places=12)
        self.assertAlmostEqual(sum(flux["allocations_eur"]), 22.5, places=12)
        self.assertAlmostEqual(flux["total_eur"], 25.0, places=12)


class TestIndiceEtPiliers(unittest.TestCase):
    def test_indice_justice_paix(self):
        indice = indice_justice_paix()
        self.assertAlmostEqual(indice["scenarios"]["halal_pur"]["tension_economique"], 0.0, places=12)
        self.assertAlmostEqual(
            indice["scenarios"]["usuraire"]["tension_economique"], 0.68, places=12
        )
        self.assertAlmostEqual(
            indice["scenarios"]["usuraire"]["indice_harmonie_economique"], 0.32, places=12
        )
        self.assertAlmostEqual(sum(indice["poids"].values()), 1.0, places=12)

    def test_quatre_piliers(self):
        piliers = ponts_quatre_piliers()
        self.assertEqual(len(piliers), 4)
        self.assertTrue(all(p["limite"] for p in piliers))
        self.assertTrue(all(p["question"] for p in piliers))


class TestAssemblage(unittest.TestCase):
    def test_tous_les_controles(self):
        donnees = resoudre()
        self.assertEqual(donnees["resume"]["equations"], 13)
        self.assertEqual(donnees["resume"]["controles_ok"], 13)
        self.assertEqual(donnees["resume"]["controles_total"], 13)
        self.assertTrue(verifier(donnees))
        self.assertEqual(
            donnees["resume"]["statuts"],
            {"OPÉRATIONNEL": 6, "SIMULÉ": 3, "SPÉCIFIÉ": 4},
        )

    def test_ids_uniques_et_continuite(self):
        donnees = resoudre()
        ids = [e["id"] for e in donnees["equations"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, [f"EQ-{i:02d}" for i in range(1, 14)])
        for eq in donnees["equations"]:
            self.assertTrue(eq["chemin"].endswith(eq["id"].replace("EQ-", "C")))


if __name__ == "__main__":
    unittest.main()
