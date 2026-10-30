# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""Règlement des dettes et redistribution — équations posées et contrôlées.

Sources normatives : Coran 2:275-279 (interdiction du riba), 2:280 (report du
débiteur insolvable et remise), 2:282 (écriture et témoins du contrat de dette),
2:245 (prêt d'honneur sans intérêt), 2:261 (parabole des sept épis),
9:60 (huit catégories de bénéficiaires de la zakat), 4:11-12 (parts
successorales fixes), 5:8 et 16:90 (justice), 49:10 (réconciliation et paix).
Les versets sont cités par référence et paraphrase ; aucune traduction n'est
présentée comme officielle.

Les constantes de zakat et de nisab sont celles du moteur d'économie islamique
du dossier (moteur_economie_islamique_mizan.py). Les scénarios agrégés sont des
modèles explicitement déclarés : le module ne déplace aucun fonds, ne perçoit
aucune zakat et n'exerce aucune contrainte.

Usage :
    py -3 oeuvre_universelle/reglement_dettes_redistribution.py
"""

from __future__ import annotations

import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from equations_economie_mondiale_mizan import calculer_tension_economique  # noqa: E402
from moteur_economie_islamique_mizan import (  # noqa: E402
    NISAB_ARGENT_GRAMMES,
    NISAB_OR_GRAMMES,
    SEUIL_NISAB_ARGENT_EUR,
    SEUIL_NISAB_OR_EUR,
    TAUX_RIBA_MAXIMUM_AUTORISE,
    TAUX_ZAKAT_ANNUEL,
)

SOURCE = {
    "type": "corpus normatif",
    "titre": "Règlement des dettes et redistribution selon les règles islamiques",
    "references": [
        {"ref": "Coran 2:275-279", "regle": "interdiction du riba et appel à l'effacement des intérêts"},
        {"ref": "Coran 2:280", "regle": "report du débiteur en difficulté ; remise de la dette meilleure que l'exigence"},
        {"ref": "Coran 2:282", "regle": "écriture du contrat de dette et témoins"},
        {"ref": "Coran 2:245", "regle": "prêt d'honneur (qard hasan) sans intérêt"},
        {"ref": "Coran 2:261", "regle": "parabole de la multiplication : sept épis, cent grains par épi"},
        {"ref": "Coran 9:60", "regle": "huit catégories de bénéficiaires de la zakat"},
        {"ref": "Coran 4:11-12", "regle": "parts successorales fixes"},
        {"ref": "Coran 5:8", "regle": "justice sans partialité"},
        {"ref": "Coran 16:90", "regle": "justice, bienfaisance, interdiction de l'oppression"},
        {"ref": "Coran 49:10", "regle": "réconciliation et paix entre croyants"},
    ],
    "conventions_classiques": [
        "zakat : 1/40 (2,5 %) de la richesse dépassant le nisab après une année lunaire",
        "nisab : 85 g d'or ou 595 g d'argent, seuils du moteur du dossier",
    ],
    "transcript": "sans objet",
    "note": "Les versets sont cités par référence et paraphrase. Aucune mesure, aucune donnée de marché en temps réel.",
}

STATUTS = {
    "OPÉRATIONNEL": "arithmétique exacte reproductible sur des règles déclarées",
    "SIMULÉ": "convention ou modèle du dossier, explicité comme tel",
    "SPÉCIFIÉ": "règle, index ou analogie posés, non mesurés",
}


def _f(x: float, n: int = 6) -> str:
    return f"{x:,.{n}f}".replace(",", " ")


def _c(x: float, n: int = 6) -> str:
    return f"{x:.{n}f}"


# ============================================================================
# 1. ZAKAT LÉGALE — seuil et taux
# ============================================================================

def zakat_legale(
    patrimoine_eur: float = 1_000.0,
    nisab_eur: float = SEUIL_NISAB_ARGENT_EUR,
) -> Dict[str, Any]:
    """Z = τ·A·1[A ≥ N], τ = 1/40 ; N = 595 g d'argent aux constantes du dossier."""
    assujetti = patrimoine_eur >= nisab_eur
    zakat = patrimoine_eur * TAUX_ZAKAT_ANNUEL if assujetti else 0.0
    sous_seuil = 500.0
    zakat_sous_seuil = sous_seuil * TAUX_ZAKAT_ANNUEL if sous_seuil >= nisab_eur else 0.0
    return {
        "patrimoine_eur": patrimoine_eur,
        "nisab_argent_eur": nisab_eur,
        "nisab_or_eur": SEUIL_NISAB_OR_EUR,
        "nisab_argent_g": NISAB_ARGENT_GRAMMES,
        "nisab_or_g": NISAB_OR_GRAMMES,
        "taux": TAUX_ZAKAT_ANNUEL,
        "assujetti": assujetti,
        "zakat_eur": zakat,
        "patrimoine_sous_seuil_eur": sous_seuil,
        "zakat_sous_seuil_eur": zakat_sous_seuil,
        "part_par_categorie_eur": zakat / 8.0,
        "lecture": "La zakat porte sur la richesse qui dépasse le nisab, au taux 1/40. Sous le seuil, elle est nulle : la règle protège les petits patrimoines.",
    }


# ============================================================================
# 2. HUIT CATÉGORIES CORANIQUES — allocation déclarée
# ============================================================================

def categories_coraniques() -> Dict[str, Any]:
    """Coran 9:60 : huit catégories. Le Coran fixe les catégories, pas des parts égales."""
    noms = [
        ("fuqara", "الفقراء", "les pauvres"),
        ("masakin", "المساكين", "les nécessiteux"),
        ("amilin", "العاملين عليها", "ceux qui en ont la charge"),
        ("muallafa", "المؤلفة قلوبهم", "ceux dont les cœurs sont à rallier"),
        ("riqab", "الرقاب", "l'affranchissement"),
        ("gharimin", "الغارمين", "les endettés"),
        ("fi_sabil", "في سبيل الله", "dans le sentier de Dieu"),
        ("ibn_sabil", "ابن السبيل", "le voyageur en détresse"),
    ]
    poids = Fraction(1, 8)
    categories = [
        {"cle": cle, "ar": ar, "fr": fr, "poids": str(poids)}
        for cle, ar, fr in noms
    ]
    somme = sum((Fraction(c["poids"]) for c in categories), Fraction(0, 1))
    return {
        "categories": categories,
        "nombre": len(categories),
        "poids_unitaire": str(poids),
        "somme_poids": str(somme),
        "note": "Répartition à parts égales retenue comme convention de calcul du dossier ; elle n'est pas une prescription coranique de huit parts égales.",
    }


# ============================================================================
# 3. INSOLVABILITÉ — report et remise
# ============================================================================

def reglement_insolvabilite(
    dette_eur: float = 1_000.0,
    capacite_eur: float = 300.0,
    remise_eur: float = 200.0,
) -> Dict[str, Any]:
    """D' = D − min(C, D) − F ; 0 ≤ F ≤ D − min(C, D). Coran 2:280."""
    verse = min(max(capacite_eur, 0.0), dette_eur)
    reste_avant = dette_eur - verse
    remise_effective = min(max(remise_eur, 0.0), reste_avant)
    reste = reste_avant - remise_effective
    scenarios = []
    for remise in (200.0, 700.0, 1_000.0):
        r_eff = min(max(remise, 0.0), reste_avant)
        scenarios.append({
            "remise_demandee_eur": remise,
            "remise_effective_eur": r_eff,
            "reste_eur": reste_avant - r_eff,
        })
    return {
        "dette_eur": dette_eur,
        "capacite_eur": capacite_eur,
        "verse_eur": verse,
        "reste_avant_remise_eur": reste_avant,
        "remise_demandee_eur": remise_eur,
        "remise_effective_eur": remise_effective,
        "reste_eur": reste,
        "solde": reste == 0.0,
        "scenarios": scenarios,
        "lecture": "Le débiteur sans capacité n'est pas contraint : sa dette est reportée. La remise ne peut pas dépasser le reste dû ; au-delà, elle est plafonnée.",
    }


# ============================================================================
# 4. QARD HASAN CONTRE RIBA
# ============================================================================

def qard_hasan_vs_riba(
    capital_eur: float = 10_000.0,
    taux_annuel: float = 0.05,
    annees: int = 10,
) -> Dict[str, Any]:
    """Qard hasan : R = C, intérêt nul. Prêt usuraire : R = C(1+r)^n. Coran 2:245, 2:275-279."""
    remboursement_qard = capital_eur
    remboursement_riba = capital_eur * (1.0 + taux_annuel) ** annees
    surcout = remboursement_riba - capital_eur
    return {
        "capital_eur": capital_eur,
        "taux_annuel": taux_annuel,
        "annees": annees,
        "remboursement_qard_eur": remboursement_qard,
        "remboursement_riba_eur": remboursement_riba,
        "surcout_riba_eur": surcout,
        "taux_riba_autorise": TAUX_RIBA_MAXIMUM_AUTORISE,
        "lecture": "Le prêt d'honneur restitue le capital sans surplus. Le surplus d'un prêt à intérêt est le riba que le dossier rejette strictement.",
    }


# ============================================================================
# 5. CAPACITÉ DE REMBOURSEMENT
# ============================================================================

def capacite_remboursement(
    revenu_eur: float = 3_000.0,
    depenses_essentielles_eur: float = 2_200.0,
    dette_eur: float = 4_000.0,
) -> Dict[str, Any]:
    """C = max(0, Y − E) ; versement = min(C, D) ; durée = ⌈D/C⌉ si C > 0."""
    capacite = max(0.0, revenu_eur - depenses_essentielles_eur)
    versement = min(capacite, dette_eur)
    duree = math.ceil(dette_eur / capacite) if capacite > 0.0 else None
    insolvable = {
        "revenu_eur": 2_000.0,
        "depenses_essentielles_eur": 2_200.0,
        "capacite_eur": 0.0,
        "duree_ans": None,
        "conclusion": "report (Coran 2:280), pas de contrainte",
    }
    return {
        "revenu_eur": revenu_eur,
        "depenses_essentielles_eur": depenses_essentielles_eur,
        "capacite_eur": capacite,
        "dette_eur": dette_eur,
        "versement_eur": versement,
        "duree_ans": duree,
        "insolvable": insolvable,
        "lecture": "La capacité ne saisit que le surplus après les besoins essentiels. Un revenu inférieur aux besoins donne une capacité nulle, donc un report.",
    }


# ============================================================================
# 6. SUCCESSION — parts fixes du Coran 4:11-12
# ============================================================================

def succession_fixes(masse_apres_dettes_eur: float = 72_000.0) -> Dict[str, Any]:
    """Cas déclaré : conjoint, père, mère, un fils, une fille. Parts exactes en fractions."""
    parts = {
        "conjoint": Fraction(1, 8),
        "pere": Fraction(1, 6),
        "mere": Fraction(1, 6),
    }
    reste = Fraction(1, 1) - sum(parts.values(), Fraction(0, 1))
    parts["fils"] = reste * Fraction(2, 3)
    parts["fille"] = reste * Fraction(1, 3)
    somme = sum(parts.values(), Fraction(0, 1))
    montants = {cle: float(masse_apres_dettes_eur * part) for cle, part in parts.items()}
    return {
        "cas": "conjoint, père, mère, un fils, une fille ; masse après dettes",
        "masse_apres_dettes_eur": masse_apres_dettes_eur,
        "parts": {cle: str(part) for cle, part in parts.items()},
        "montants_eur": montants,
        "somme_parts": str(somme),
        "somme_montants_eur": sum(montants.values()),
        "ratio_fils_fille": float(parts["fils"] / parts["fille"]),
        "note": "Cas unique et déclaré ; le module n'est pas un calculateur général de succession (awl, radd et autres cas ne sont pas traités).",
    }


# ============================================================================
# 7. ZAKAT AGRÉGÉE — stabilisateur automatique
# ============================================================================

def zakat_stabilisateur(masse_eur: float = 1_000_000_000_000.0) -> Dict[str, Any]:
    """I_Z = τ·W ; la masse est renouvelée en 1/τ années si le flux est constant."""
    injection = masse_eur * TAUX_ZAKAT_ANNUEL
    rotation = 1.0 / TAUX_ZAKAT_ANNUEL
    return {
        "masse_eur": masse_eur,
        "taux": TAUX_ZAKAT_ANNUEL,
        "injection_annuelle_eur": injection,
        "rotation_ans": rotation,
        "lecture": "À flux constant et sans croissance, la zakat fait circuler l'équivalent de la masse en quarante ans.",
    }


# ============================================================================
# 8. REDISTRIBUTION ET INÉGALITÉ — modèle à deux groupes
# ============================================================================

def redistribution_inegalite(
    haut_eur: float = 150.0,
    bas_eur: float = 50.0,
    transferts_eur: tuple = (25.0, 50.0),
) -> Dict[str, Any]:
    """Deux groupes égaux : G = (a−b)/(2(a+b)) ; transfert t : G' = G − t/(a+b)."""
    moyenne = (haut_eur + bas_eur) / 2.0
    ecart = haut_eur - bas_eur
    gini_initial = ecart / (2.0 * (haut_eur + bas_eur))
    scenarios = []
    for transfert in transferts_eur:
        gini_apres = (ecart - 2.0 * transfert) / (2.0 * (haut_eur + bas_eur))
        scenarios.append({
            "transfert_eur": transfert,
            "haut_apres_eur": haut_eur - transfert,
            "bas_apres_eur": bas_eur + transfert,
            "gini_apres": gini_apres,
        })
    return {
        "haut_eur": haut_eur,
        "bas_eur": bas_eur,
        "moyenne_eur": moyenne,
        "gini_initial": gini_initial,
        "transfert_egalisation_eur": ecart / 2.0,
        "scenarios": scenarios,
        "note": "Modèle-jouet à deux groupes de même taille, revenu total constant. Ce n'est pas une mesure de la distribution réelle.",
    }


# ============================================================================
# 9. PARABOLE DE L'ABONDANCE
# ============================================================================

def parabole_abondance(zakat_eur: float = 25.0) -> Dict[str, Any]:
    """Coran 2:261 : sept épis, cent grains par épi, facteur 700. Parabole, pas un rendement."""
    epis = 7
    grains_par_epi = 100
    facteur = epis * grains_par_epi
    flux = facteur * zakat_eur
    return {
        "epis": epis,
        "grains_par_epi": grains_par_epi,
        "facteur": facteur,
        "zakat_eur": zakat_eur,
        "flux_illustratif_eur": flux,
        "nature": "parabole révélée (Coran 2:261), non un taux de rendement financier",
    }


# ============================================================================
# 10. CONTINUITÉ — demi-vie du stock sous zakat
# ============================================================================

def continuite_zakat(
    taux: float = TAUX_ZAKAT_ANNUEL,
    annees: int = 40,
) -> Dict[str, Any]:
    """W_n = W_0(1−τ)^n ; demi-vie n½ = ln(1/2)/ln(1−τ)."""
    demi_vie = math.log(0.5) / math.log(1.0 - taux)
    facteur = (1.0 - taux) ** annees
    return {
        "taux": taux,
        "annees": annees,
        "demi_vie_ans": demi_vie,
        "facteur_restant": facteur,
        "lecture": "Sans croissance, la zakat réduit de moitié un stock non renouvelé en environ 27,38 ans. La continuité vient du flux, pas de l'accumulation.",
    }


# ============================================================================
# 11. CONSERVATION DU FLUX
# ============================================================================

def conservation_flux(
    zakat_eur: float = 25.0,
    taux_reserve: float = 0.10,
) -> Dict[str, Any]:
    """Z = Σ_k A_k + R : aucune unité ne disparaît du circuit déclaré."""
    reserve = zakat_eur * taux_reserve
    distributable = zakat_eur - reserve
    part = distributable / 8.0
    allocations = [part] * 8
    total = sum(allocations) + reserve
    return {
        "zakat_eur": zakat_eur,
        "taux_reserve": taux_reserve,
        "reserve_eur": reserve,
        "distributable_eur": distributable,
        "allocation_par_categorie_eur": part,
        "allocations_eur": allocations,
        "total_eur": total,
        "lecture": "Le flux est conservé : la somme des allocations et de la réserve égale exactement la zakat perçue.",
    }


# ============================================================================
# 12. INDICE DE JUSTICE ET DE PAIX
# ============================================================================

def indice_justice_paix() -> Dict[str, Any]:
    """J = 1 − T, T = 0,40·t_riba + 0,20·t_partage + 0,20·t_zakat + 0,20·t_adossement."""
    halal = calculer_tension_economique(0.0, 0.5, True, 1.0)
    usuraire = calculer_tension_economique(0.05, 0.0, False, 0.1)
    return {
        "poids": {"riba": 0.40, "partage": 0.20, "zakat": 0.20, "adossement": 0.20},
        "scenarios": {"halal_pur": halal, "usuraire": usuraire},
        "lecture": "L'indice est une convention interne du dossier : 1 = harmonie déclarée, 0 = tension maximale. Il ne mesure ni la paix sociale ni la justice réelle.",
    }


# ============================================================================
# 13. PONTS AVEC LES QUATRE PILIERS — complétude du protocole déclaré
# ============================================================================

def ponts_quatre_piliers() -> List[Dict[str, str]]:
    """Chaque pilier du dossier reçoit un répondant dans le protocole de dette."""
    return [
        {
            "pilier": "P1 — Identité et mandat",
            "question": "Qui agit, à quel titre, pour quelle durée ?",
            "regle": "Parties identifiées, capacité et mandat écrits, signature du contrat (Coran 2:282).",
            "limite": "Le module ne vérifie pas l'identité réelle ; il formalise les champs.",
        },
        {
            "pilier": "P2 — Intégrité et provenance",
            "question": "Ce qui s'exécute est-il ce qui a été signé ?",
            "regle": "Écriture, témoins, empreinte SHA-256 du contrat et quittance.",
            "limite": "L'empreinte prouve l'intégrité du contenu, pas la véracité des faits déclarés.",
        },
        {
            "pilier": "P3 — Confidentialité et maîtrise",
            "question": "Qui peut lire, restaurer, effacer ?",
            "regle": "Registre accessible aux parties, aucune clé privée détenue par le module.",
            "limite": "Le module ne détient aucun fonds et n'offre aucune garde.",
        },
        {
            "pilier": "P4 — Résilience et preuve",
            "question": "Que reste-t-il quand l'attaque réussit ?",
            "regle": "Journal d'audit, quittance vérifiable, voie de recours et de réconciliation (Coran 49:10).",
            "limite": "La preuve est documentaire ; elle ne garantit pas l'exécution forcée.",
        },
    ]


# ============================================================================
# ASSEMBLAGE
# ============================================================================

def _eq(id_: str, chemin: str, formule: str, resultat: str, statut: str,
        detail: Any) -> Dict[str, Any]:
    return {
        "id": id_,
        "chemin": chemin,
        "formule": formule,
        "resultat": resultat,
        "statut": statut,
        "detail": detail,
    }


def resoudre() -> Dict[str, Any]:
    zakat = zakat_legale()
    categories = categories_coraniques()
    insolv = reglement_insolvabilite()
    qard = qard_hasan_vs_riba()
    capacite = capacite_remboursement()
    succession = succession_fixes()
    stabilisateur = zakat_stabilisateur()
    inegalite = redistribution_inegalite()
    abondance = parabole_abondance()
    continuite = continuite_zakat()
    conservation = conservation_flux()
    justice = indice_justice_paix()
    piliers = ponts_quatre_piliers()

    eqs = [
        _eq(
            "EQ-01", "reglement_dettes_redistribution.py → zakat_legale() → C01",
            "Z = τ·A·1[A ≥ N] ;  τ = 1/40 ;  N = 595 g (Ag)",
            f"Z(1 000 €) = {_f(zakat['zakat_eur'])} € · Z(500 €) = {_f(zakat['zakat_sous_seuil_eur'])} € · N = {_f(zakat['nisab_argent_eur'])} €",
            "OPÉRATIONNEL", zakat,
        ),
        _eq(
            "EQ-02", "reglement_dettes_redistribution.py → categories_coraniques() → C02",
            "Q 9:60 ;  k = 1..8 ;  Σ_k s_k = 1 ;  s_k ≥ 0",
            f"s_k = {categories['poids_unitaire']} (k = 1..8) · Σ_k s_k = {categories['somme_poids']}",
            "SPÉCIFIÉ", categories,
        ),
        _eq(
            "EQ-03", "reglement_dettes_redistribution.py → reglement_insolvabilite() → C03",
            "D' = D − min(C, D) − F ;  0 ≤ F ≤ D − min(C, D) ;  D' ≥ 0",
            f"D' = {_f(insolv['reste_eur'])} € · F = 0 € ⇒ D' = 0 € · F_max = {_f(insolv['scenarios'][2]['remise_effective_eur'])} €",
            "OPÉRATIONNEL", insolv,
        ),
        _eq(
            "EQ-04", "reglement_dettes_redistribution.py → qard_hasan_vs_riba() → C04",
            "qard : R = C ;  ribā : R = C(1+r)^n ;  ΔR = R − C",
            f"R_qard = {_f(qard['remboursement_qard_eur'])} € · R_ribā(5 %, 10 a) = {_f(qard['remboursement_riba_eur'])} € · ΔR = {_f(qard['surcout_riba_eur'])} €",
            "OPÉRATIONNEL", qard,
        ),
        _eq(
            "EQ-05", "reglement_dettes_redistribution.py → capacite_remboursement() → C05",
            "C = max(0, Y − E) ;  v = min(C, D) ;  n = ⌈D/C⌉ (C > 0)",
            f"C = {_f(capacite['capacite_eur'])} €/a · n = {capacite['duree_ans']} a · C = 0 ⇒ 2:280",
            "SIMULÉ", capacite,
        ),
        _eq(
            "EQ-06", "reglement_dettes_redistribution.py → succession_fixes() → C06",
            "s1 = 1/8 ;  s2 = 1/6 ;  s3 = 1/6 ;  R = 13/24 ;  s4:s5 = 2:1",
            f"Σ s = {succession['somme_parts']} · s4/s5 = {_c(succession['ratio_fils_fille'], 0)} · s1 = {_f(succession['montants_eur']['conjoint'])} €",
            "OPÉRATIONNEL", succession,
        ),
        _eq(
            "EQ-07", "reglement_dettes_redistribution.py → zakat_stabilisateur() → C07",
            "I_Z = τ·W ;  1/τ = rotation",
            f"I_Z = {_f(stabilisateur['injection_annuelle_eur'])} € · 1/τ = {_f(stabilisateur['rotation_ans'])} a",
            "SIMULÉ", stabilisateur,
        ),
        _eq(
            "EQ-08", "reglement_dettes_redistribution.py → redistribution_inegalite() → C08",
            "G = (a−b)/(2(a+b)) ;  G' = G − t/(a+b) ;  t* = (a−b)/2",
            f"G = {_c(inegalite['gini_initial'])} → {_c(inegalite['scenarios'][0]['gini_apres'])} (t = 25) → {_c(inegalite['scenarios'][1]['gini_apres'])} (t = 50)",
            "SIMULÉ", inegalite,
        ),
        _eq(
            "EQ-09", "reglement_dettes_redistribution.py → parabole_abondance() → C09",
            "7 × 100 = 700 ;  700·Z (illustration)",
            f"7 × 100 = {abondance['facteur']} · 700·Z = {_f(abondance['flux_illustratif_eur'])} € (Z = {_f(abondance['zakat_eur'])} €)",
            "SPÉCIFIÉ", abondance,
        ),
        _eq(
            "EQ-10", "reglement_dettes_redistribution.py → continuite_zakat() → C10",
            "W_n = W_0(1−τ)^n ;  n½ = ln(1/2)/ln(1−τ)",
            f"n½ = {_f(continuite['demi_vie_ans'])} a · W(40)/W0 = {_f(continuite['facteur_restant'])}",
            "OPÉRATIONNEL", continuite,
        ),
        _eq(
            "EQ-11", "reglement_dettes_redistribution.py → conservation_flux() → C11",
            "Z = Σ_k A_k + R ;  A_k = (1−ρ)·Z/8",
            f"Z = {_f(conservation['zakat_eur'])} € = Σ A_k ({_f(conservation['distributable_eur'])} €) + R ({_f(conservation['reserve_eur'])} €)",
            "OPÉRATIONNEL", conservation,
        ),
        _eq(
            "EQ-12", "reglement_dettes_redistribution.py → indice_justice_paix() → C12",
            "J = 1 − T ;  T = 0.40·t_riba + 0.20·t_partage + 0.20·t_zakat + 0.20·t_adossement",
            f"T = 0 : J = {_c(justice['scenarios']['halal_pur']['indice_harmonie_economique'])} · T = {_c(justice['scenarios']['usuraire']['tension_economique'])} : J = {_c(justice['scenarios']['usuraire']['indice_harmonie_economique'])}",
            "SPÉCIFIÉ", justice,
        ),
        _eq(
            "EQ-13", "reglement_dettes_redistribution.py → ponts_quatre_piliers() → C13",
            "P1 ↔ S · P2 ↔ H · P3 ↔ R · P4 ↔ A",
            f"{len(piliers)}/4 · K = {_c(len(piliers) / 4.0)}",
            "SPÉCIFIÉ", piliers,
        ),
    ]

    controles = [
        {
            "id": "C01", "nom": "Zakat 2,5 % au-dessus du nisab, nulle en dessous",
            "attendu": "25.000000 / 0.000000",
            "obtenu": f"{_c(zakat['zakat_eur'])} / {_c(zakat['zakat_sous_seuil_eur'])}",
            "ok": abs(zakat["zakat_eur"] - 25.0) < 1e-12
            and zakat["zakat_sous_seuil_eur"] == 0.0
            and 500.0 < zakat["nisab_argent_eur"] < 1_000.0,
        },
        {
            "id": "C02", "nom": "Huit catégories, poids positifs, somme exacte 1",
            "attendu": "8 / 1",
            "obtenu": f"{categories['nombre']} / {categories['somme_poids']}",
            "ok": categories["nombre"] == 8
            and sum((Fraction(c["poids"]) for c in categories["categories"]), Fraction(0, 1)) == 1
            and all(Fraction(c["poids"]) > 0 for c in categories["categories"]),
        },
        {
            "id": "C03", "nom": "Report, remise totale et remise excessive plafonnée",
            "attendu": "500.000000 / 0.000000 / 700.000000",
            "obtenu": f"{_c(insolv['scenarios'][0]['reste_eur'])} / {_c(insolv['scenarios'][1]['reste_eur'])} / {_c(insolv['scenarios'][2]['remise_effective_eur'])}",
            "ok": abs(insolv["scenarios"][0]["reste_eur"] - 500.0) < 1e-12
            and insolv["scenarios"][1]["reste_eur"] == 0.0
            and abs(insolv["scenarios"][2]["remise_effective_eur"] - 700.0) < 1e-12
            and all(s["reste_eur"] >= 0.0 for s in insolv["scenarios"]),
        },
        {
            "id": "C04", "nom": "Qard sans surcoût ; riba 5 % / 10 ans = 6 288,946268 €",
            "attendu": "6288.946268",
            "obtenu": _c(qard["surcout_riba_eur"]),
            "ok": abs(qard["surcout_riba_eur"] - 10_000.0 * (1.05 ** 10 - 1.0)) < 1e-6
            and qard["remboursement_qard_eur"] == qard["capital_eur"]
            and qard["taux_riba_autorise"] == 0.0,
        },
        {
            "id": "C05", "nom": "Capacité 800 €/an, 5 ans ; capacité nulle ⇒ report",
            "attendu": "800.000000 / 5",
            "obtenu": f"{_c(capacite['capacite_eur'])} / {capacite['duree_ans']}",
            "ok": abs(capacite["capacite_eur"] - 800.0) < 1e-12
            and capacite["duree_ans"] == 5
            and capacite["insolvable"]["capacite_eur"] == 0.0
            and capacite["insolvable"]["duree_ans"] is None,
        },
        {
            "id": "C06", "nom": "Parts successorales exactes : somme 1, ratio 2, conjoint 9 000 €",
            "attendu": "1 / 2 / 9000.000000",
            "obtenu": f"{succession['somme_parts']} / {_c(succession['ratio_fils_fille'], 0)} / {_c(succession['montants_eur']['conjoint'])}",
            "ok": Fraction(succession["somme_parts"]) == 1
            and abs(succession["ratio_fils_fille"] - 2.0) < 1e-12
            and abs(succession["montants_eur"]["conjoint"] - 9_000.0) < 1e-9
            and abs(succession["somme_montants_eur"] - 72_000.0) < 1e-9,
        },
        {
            "id": "C07", "nom": "Injection 2,5 % et rotation de 40 ans",
            "attendu": "40.000000",
            "obtenu": _c(stabilisateur["rotation_ans"]),
            "ok": abs(stabilisateur["rotation_ans"] - 40.0) < 1e-12
            and abs(stabilisateur["injection_annuelle_eur"] - 25_000_000_000.0) < 1.0,
        },
        {
            "id": "C08", "nom": "Gini 0,25 → 0,125 → 0 sous transferts 25 puis 50",
            "attendu": "0.250000 / 0.125000 / 0.000000",
            "obtenu": f"{_c(inegalite['gini_initial'])} / {_c(inegalite['scenarios'][0]['gini_apres'])} / {_c(inegalite['scenarios'][1]['gini_apres'])}",
            "ok": abs(inegalite["gini_initial"] - 0.25) < 1e-12
            and abs(inegalite["scenarios"][0]["gini_apres"] - 0.125) < 1e-12
            and abs(inegalite["scenarios"][1]["gini_apres"]) < 1e-12,
        },
        {
            "id": "C09", "nom": "Parabole : 7 × 100 = 700 ; flux = 700·Z",
            "attendu": "700 / 17500.000000",
            "obtenu": f"{abondance['facteur']} / {_c(abondance['flux_illustratif_eur'])}",
            "ok": abondance["facteur"] == 700
            and abs(abondance["flux_illustratif_eur"] - 700.0 * abondance["zakat_eur"]) < 1e-9,
        },
        {
            "id": "C10", "nom": "Demi-vie 27,377851 ans ; W(40)/W0 = 0,363232",
            "attendu": "27.377851 / 0.363232",
            "obtenu": f"{_c(continuite['demi_vie_ans'])} / {_c(continuite['facteur_restant'])}",
            "ok": abs(continuite["demi_vie_ans"] - math.log(0.5) / math.log(0.975)) < 1e-12
            and abs((1.0 - TAUX_ZAKAT_ANNUEL) ** continuite["demi_vie_ans"] - 0.5) < 1e-9
            and abs(continuite["facteur_restant"] - 0.975 ** 40) < 1e-12,
        },
        {
            "id": "C11", "nom": "Conservation : allocations + réserve = zakat",
            "attendu": "25.000000",
            "obtenu": _c(conservation["total_eur"]),
            "ok": abs(conservation["total_eur"] - 25.0) < 1e-12
            and abs(sum(conservation["allocations_eur"]) - 22.5) < 1e-12
            and abs(conservation["reserve_eur"] - 2.5) < 1e-12,
        },
        {
            "id": "C12", "nom": "Indice : halal J = 1 ; usuraire T = 0,68, J = 0,32",
            "attendu": "0.680000 / 0.320000",
            "obtenu": f"{_c(justice['scenarios']['usuraire']['tension_economique'])} / {_c(justice['scenarios']['usuraire']['indice_harmonie_economique'])}",
            "ok": abs(justice["scenarios"]["halal_pur"]["tension_economique"]) < 1e-12
            and abs(justice["scenarios"]["halal_pur"]["indice_harmonie_economique"] - 1.0) < 1e-12
            and abs(justice["scenarios"]["usuraire"]["tension_economique"] - 0.68) < 1e-12
            and abs(sum(justice["poids"].values()) - 1.0) < 1e-12,
        },
        {
            "id": "C13", "nom": "Quatre piliers reliés, chacun avec sa limite",
            "attendu": "4 / 1.000000",
            "obtenu": f"{len(piliers)} / {_c(len(piliers) / 4.0)}",
            "ok": len(piliers) == 4
            and all(p["limite"] for p in piliers)
            and abs(len(piliers) / 4.0 - 1.0) < 1e-12,
        },
    ]

    return {
        "version": "1.0",
        "source": SOURCE,
        "invariants": {
            "taux_zakat": TAUX_ZAKAT_ANNUEL,
            "nisab_argent_g": NISAB_ARGENT_GRAMMES,
            "nisab_or_g": NISAB_OR_GRAMMES,
            "seuil_nisab_argent_eur": SEUIL_NISAB_ARGENT_EUR,
            "seuil_nisab_or_eur": SEUIL_NISAB_OR_EUR,
            "taux_riba_autorise": TAUX_RIBA_MAXIMUM_AUTORISE,
        },
        "equations": eqs,
        "controles": controles,
        "resume": {
            "equations": len(eqs),
            "controles_ok": sum(1 for c in controles if c["ok"]),
            "controles_total": len(controles),
            "statuts": {s: sum(1 for e in eqs if e["statut"] == s) for s in STATUTS},
        },
    }


def verifier(donnees: Dict[str, Any] | None = None) -> bool:
    donnees = donnees or resoudre()
    return all(c["ok"] for c in donnees["controles"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    resultat = resoudre()
    print(json.dumps(resultat, ensure_ascii=False, indent=2, default=str))
    sys.exit(0 if verifier(resultat) else 1)
