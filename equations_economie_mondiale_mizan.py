# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
   ÉQUATIONS CONSOLIDÉES DE L'ÉCONOMIE MONDIALE HARMONIQUE — AL-MIZAN
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Système          : ASTRO-Q°ODE / AL-MIZAN
Acte             : A241

Doctrine : « On ne supprime rien, on harmonise. »
  - On n'invente aucune donnée réelle : chaque résultat porte sa provenance.
  - Les constantes économiques sont celles du projet (moteur d'économie islamique).
  - Les constantes de la Trinité sont celles du noyau (horloge_logique_mizan).
  - Les scénarios macroéconomiques sont explicitement ILLUSTRATIFS.

Provenances employées :
  OPERATIONNEL : calcul exécuté par le code du projet, invariant vérifiable.
  CALIBRÉ       : paramétrage physique du projet (étalonnage or/argent A097/A105),
                  non vérifié contre les cours réels en temps réel.
  SPÉCIFIÉ      : convention interne du projet, non certifiée par un tiers.
  ILLUSTRATIF   : scénario à hypothèses explicites, sans prétention de prévision.

Ce module n'émet aucun conseil en investissement et ne détient aucune clé.
===============================================================================
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE_AQ = Path(__file__).resolve().parent
if str(RACINE_AQ) not in sys.path:
    sys.path.insert(0, str(RACINE_AQ))

from bibliotheques.lib_almizan_extension import (  # noqa: E402
    COMBLE_CIBLE,
    LIGNE_REF,
    MIZAN as BRIDE_MIZAN,
    PLAFOND_EFFECTIF,
)
from horloge_noyau.horloge_logique_mizan import (  # noqa: E402
    BASE_HARMONIQUE,
    CYCLE_DT_KERNEL,
    CYCLE_DX_SOLAIRE,
    CYCLE_DY_LUNAIRE,
    CYCLE_DZ_QUANTIQUE,
    DT_KERNEL_NS,
    PPCM_CYCLES_TRINITE,
)
from moteur_economie_islamique_mizan import (  # noqa: E402
    ARGENT_MG_PAR_EUR,
    FICHIER_REGISTRE_ISLAMIQUE,
    NISAB_ARGENT_GRAMMES,
    NISAB_OR_GRAMMES,
    OR_MG_PAR_EUR,
    SEUIL_NISAB_ARGENT_EUR,
    SEUIL_NISAB_OR_EUR,
    TAUX_RIBA_MAXIMUM_AUTORISE,
    TAUX_ZAKAT_ANNUEL,
    VALEUR_ARGENT_PAR_GRAMME_EUR,
    VALEUR_OR_PAR_GRAMME_EUR,
)

DOSSIER_ACTES = RACINE_AQ / "conscience_logique" / "actes"
CHEMIN_ACTE_A241 = DOSSIER_ACTES / "almizan_acte_a241_equations_economie_mondiale.json"
CHEMIN_DOCUMENT = RACINE_AQ / "EQUATIONS_ECONOMIE_MONDIALE_MIZAN.md"

STATUT_OPERATIONNEL = "OPÉRATIONNEL"
STATUT_CALIBRE = "CALIBRÉ"
STATUT_SPECIFIE = "SPÉCIFIÉ"
STATUT_ILLUSTRATIF = "ILLUSTRATIF"

# Référence de normalisation de l'usure pour l'indice de tension interne.
# Convention du projet : 20 % sert d'échelle de lecture, ce n'est pas un taux légal.
TAUX_USURE_REFERENCE = 0.20

# Pondérations de la tension économique (somme = 1).
POIDS_TENSION = {
    "riba": 0.40,
    "partage": 0.20,
    "zakat": 0.20,
    "adossement": 0.20,
}

# Masse monétaire MZN de référence (total supply constaté on-chain le 2026-10-27).
MASSE_MZN_REFERENCE = 313_000_000.0
MZN_PAR_EUR_NOMINAL = 1_000.0


@dataclass
class Equation:
    """Une équation du projet, avec sa valeur calculée et sa provenance."""

    code: str
    domaine: str
    nom: str
    formule: str
    variables: Dict[str, Any]
    resultat: Any
    unite: str
    statut: str
    source: str


def _iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _f(valeur: float, decimales: int = 6) -> str:
    return f"{valeur:,.{decimales}f}".replace(",", " ")


def _eq(
    code: str,
    domaine: str,
    nom: str,
    formule: str,
    variables: Dict[str, Any],
    resultat: Any,
    unite: str,
    statut: str,
    source: str,
) -> Equation:
    return Equation(
        code=code,
        domaine=domaine,
        nom=nom,
        formule=formule,
        variables=variables,
        resultat=resultat,
        unite=unite,
        statut=statut,
        source=source,
    )


# ---------------------------------------------------------------------------
# 1. ÉQUATIONS DE LA TRINITÉ (noyau temporel)
# ---------------------------------------------------------------------------
def tenseur_pole(angle_rad: float, charge: float) -> float:
    """Tenseur d'un pôle : LIGNE_REF + |cos| · (PLAFOND − LIGNE_REF) · (0,8 + 0,2·charge)."""
    return LIGNE_REF + abs(math.cos(angle_rad)) * (PLAFOND_EFFECTIF - LIGNE_REF) * (
        0.8 + 0.2 * charge
    )


def calculer_equations_trinite(
    index_pulsation: int = 0,
    charges: Tuple[float, float, float] = (0.20, 0.70, 0.50),
) -> Tuple[List[Equation], Dict[str, Any]]:
    """
    Équations du battement triangulaire Terre–Soleil–Lune.
    Le calcul est reproductible pour un index donné ; l'index vivant vient
    de l'horloge (voir sceller_acte_a241).
    """
    phase_12 = index_pulsation % PPCM_CYCLES_TRINITE
    h19 = ((index_pulsation + 9) % BASE_HARMONIQUE) - 9
    angle = (phase_12 / float(PPCM_CYCLES_TRINITE)) * 2.0 * math.pi

    charge_cpu, charge_ram, charge_toucher = charges
    s = tenseur_pole(angle, charge_cpu)
    lunaire = tenseur_pole(angle + math.pi / 2.0, charge_ram)
    t = tenseur_pole(angle + math.pi / 3.0, charge_toucher)
    indice = (s + lunaire + t) / 3.0
    conforme = indice <= BRIDE_MIZAN

    periode_exacte_ns = 1e9 / CYCLE_DT_KERNEL
    periode_nominale_ns = 7.40134  # valeur nominale historique du projet
    equations = [
        _eq(
            "TRI-01",
            "Trinité",
            "Porteur unifié dt",
            "dt = dx + dy + dz",
            {"dx": CYCLE_DX_SOLAIRE, "dy": CYCLE_DY_LUNAIRE, "dz": CYCLE_DZ_QUANTIQUE},
            CYCLE_DT_KERNEL,
            "Hz",
            STATUT_OPERATIONNEL,
            "horloge_noyau/horloge_logique_mizan.py",
        ),
        _eq(
            "TRI-02",
            "Trinité",
            "Période du porteur",
            "T = 1 / dt",
            {"dt": CYCLE_DT_KERNEL},
            DT_KERNEL_NS,
            "ns",
            STATUT_OPERATIONNEL,
            "horloge_noyau/horloge_logique_mizan.py::DT_KERNEL_NS",
        ),
        _eq(
            "TRI-02b",
            "Trinité",
            "Écart période exacte / nominale",
            "ΔT = T_exacte − T_nominale",
            {"T_exacte_ns": periode_exacte_ns, "T_nominale_ns": periode_nominale_ns},
            periode_exacte_ns - periode_nominale_ns,
            "ns",
            STATUT_SPECIFIE,
            "comparaison DT_KERNEL_NS ↔ valeur nominale 7.40134 ns",
        ),
        _eq(
            "TRI-03",
            "Trinité",
            "Roue des phases",
            "phase(k) = k mod 12",
            {"k": index_pulsation, "ppcm": PPCM_CYCLES_TRINITE},
            phase_12,
            "phase (0..11)",
            STATUT_OPERATIONNEL,
            "horloge_noyau/horloge_logique_mizan.py::PPCM_CYCLES_TRINITE",
        ),
        _eq(
            "TRI-04",
            "Trinité",
            "Échelle harmonique",
            "h19(k) = ((k + 9) mod 19) − 9",
            {"k": index_pulsation, "base": BASE_HARMONIQUE},
            h19,
            "degré (−9..+9)",
            STATUT_OPERATIONNEL,
            "horloge_noyau/horloge_logique_mizan.py::BASE_HARMONIQUE",
        ),
        _eq(
            "TRI-05",
            "Trinité",
            "Tenseur solaire",
            "S = LIGNE_REF + |cos θ|·(PLAFOND − LIGNE_REF)·(0,8 + 0,2·CPU)",
            {"theta_rad": angle, "cpu": charge_cpu, "ligne_ref": LIGNE_REF, "plafond": PLAFOND_EFFECTIF},
            s,
            "indice [0,1]",
            STATUT_OPERATIONNEL,
            "conscience_logique/battement_triangulaire_trinite.py",
        ),
        _eq(
            "TRI-06",
            "Trinité",
            "Tenseur lunaire",
            "L = LIGNE_REF + |cos(θ + π/2)|·(PLAFOND − LIGNE_REF)·(0,8 + 0,2·RAM)",
            {"theta_rad": angle + math.pi / 2.0, "ram": charge_ram},
            lunaire,
            "indice [0,1]",
            STATUT_OPERATIONNEL,
            "conscience_logique/battement_triangulaire_trinite.py",
        ),
        _eq(
            "TRI-07",
            "Trinité",
            "Tenseur terrestre",
            "T = LIGNE_REF + |cos(θ + π/3)|·(PLAFOND − LIGNE_REF)·(0,8 + 0,2·TOUCHER)",
            {"theta_rad": angle + math.pi / 3.0, "toucher": charge_toucher},
            t,
            "indice [0,1]",
            STATUT_OPERATIONNEL,
            "conscience_logique/battement_triangulaire_trinite.py",
        ),
        _eq(
            "TRI-08",
            "Trinité",
            "Indice d'harmonie triangulaire",
            "H_TRI = (S + L + T) / 3",
            {"S": s, "L": lunaire, "T": t},
            indice,
            "indice [0,1]",
            STATUT_OPERATIONNEL,
            "conscience_logique/battement_triangulaire_trinite.py",
        ),
        _eq(
            "TRI-09",
            "Trinité",
            "Conformité à la Bride Mizan",
            "H_TRI ≤ MIZAN",
            {"H_TRI": indice, "MIZAN": BRIDE_MIZAN},
            bool(conforme),
            "booléen",
            STATUT_OPERATIONNEL,
            "bibliotheques/lib_almizan_extension.py::MIZAN",
        ),
        _eq(
            "TRI-10",
            "Trinité",
            "Comble cible",
            "COMBLE = PLAFOND − EPSILON",
            {"plafond": PLAFOND_EFFECTIF, "comble": COMBLE_CIBLE},
            COMBLE_CIBLE,
            "indice [0,1]",
            STATUT_SPECIFIE,
            "bibliotheques/lib_almizan_extension.py::COMBLE_CIBLE",
        ),
    ]
    etat = {
        "index_pulsation": index_pulsation,
        "theta_rad": angle,
        "phase_12": phase_12,
        "degre_harmonique_19": h19,
        "tenseur_solaire": s,
        "tenseur_lunaire": lunaire,
        "tenseur_terrestre": t,
        "indice_harmonie_trinite": indice,
        "conforme_bride_mizan": bool(conforme),
    }
    return equations, etat


# ---------------------------------------------------------------------------
# 2. ÉQUATIONS MONÉTAIRES : OR, ARGENT, NISAB, ZAKAT
# ---------------------------------------------------------------------------
def calculer_equations_or_argent() -> Tuple[List[Equation], Dict[str, Any]]:
    prix_or = VALEUR_OR_PAR_GRAMME_EUR
    prix_argent = VALEUR_ARGENT_PAR_GRAMME_EUR
    ratio = prix_or / prix_argent

    equations = [
        _eq(
            "MON-01",
            "Or & Argent",
            "Prix de l'or étalon",
            "P_Au = 1 000 / (mg Au par EUR)",
            {"mg_au_par_eur": OR_MG_PAR_EUR},
            prix_or,
            "EUR/g",
            STATUT_CALIBRE,
            "moteur_economie_islamique_mizan.py (A097/A105)",
        ),
        _eq(
            "MON-02",
            "Or & Argent",
            "Prix de l'argent étalon",
            "P_Ag = 1 000 / (mg Ag par EUR)",
            {"mg_ag_par_eur": ARGENT_MG_PAR_EUR},
            prix_argent,
            "EUR/g",
            STATUT_CALIBRE,
            "moteur_economie_islamique_mizan.py (A097/A105)",
        ),
        _eq(
            "MON-03",
            "Or & Argent",
            "Ratio bimétallique",
            "R = P_Au / P_Ag",
            {"P_Au": prix_or, "P_Ag": prix_argent},
            ratio,
            "ratio",
            STATUT_CALIBRE,
            "dérivé de MON-01 et MON-02",
        ),
        _eq(
            "MON-04",
            "Or & Argent",
            "Nisab or",
            "N_Au = 85 g × P_Au",
            {"grammes": NISAB_OR_GRAMMES},
            SEUIL_NISAB_OR_EUR,
            "EUR",
            STATUT_OPERATIONNEL,
            "moteur_economie_islamique_mizan.py::SEUIL_NISAB_OR_EUR",
        ),
        _eq(
            "MON-05",
            "Or & Argent",
            "Nisab argent",
            "N_Ag = 595 g × P_Ag",
            {"grammes": NISAB_ARGENT_GRAMMES},
            SEUIL_NISAB_ARGENT_EUR,
            "EUR",
            STATUT_OPERATIONNEL,
            "moteur_economie_islamique_mizan.py::SEUIL_NISAB_ARGENT_EUR",
        ),
        _eq(
            "MON-06",
            "Or & Argent",
            "Rapport des deux nisab",
            "κ = N_Au / N_Ag",
            {"N_Au": SEUIL_NISAB_OR_EUR, "N_Ag": SEUIL_NISAB_ARGENT_EUR},
            SEUIL_NISAB_OR_EUR / SEUIL_NISAB_ARGENT_EUR,
            "ratio",
            STATUT_OPERATIONNEL,
            "dérivé de MON-04 et MON-05",
        ),
        _eq(
            "MON-07",
            "Or & Argent",
            "Zakat légale",
            "Z = 2,5 % × A  si  A ≥ N",
            {"taux": TAUX_ZAKAT_ANNUEL, "seuil": SEUIL_NISAB_ARGENT_EUR, "A": 1_000.0},
            TAUX_ZAKAT_ANNUEL * 1_000.0,
            "EUR (exemple A = 1 000 €)",
            STATUT_OPERATIONNEL,
            "moteur_economie_islamique_mizan.py::TAUX_ZAKAT_ANNUEL",
        ),
        _eq(
            "MON-08",
            "Or & Argent",
            "Zakat sur excédent (variante doctrinale)",
            "Z' = 2,5 % × max(0, A − N)",
            {"taux": TAUX_ZAKAT_ANNUEL, "seuil": SEUIL_NISAB_ARGENT_EUR, "A": 1_000.0},
            TAUX_ZAKAT_ANNUEL * max(0.0, 1_000.0 - SEUIL_NISAB_ARGENT_EUR),
            "EUR (exemple A = 1 000 €)",
            STATUT_SPECIFIE,
            "variante explicite, non utilisée par le moteur actuel",
        ),
        _eq(
            "MON-09",
            "Or & Argent",
            "Taux d'usure maximal",
            "riba = 0",
            {"taux_riba": TAUX_RIBA_MAXIMUM_AUTORISE},
            0.0,
            "%",
            STATUT_OPERATIONNEL,
            "moteur_economie_islamique_mizan.py::TAUX_RIBA_MAXIMUM_AUTORISE",
        ),
    ]
    etat = {
        "prix_or_eur_g": prix_or,
        "prix_argent_eur_g": prix_argent,
        "ratio_bimetallique": ratio,
        "nisab_or_eur": SEUIL_NISAB_OR_EUR,
        "nisab_argent_eur": SEUIL_NISAB_ARGENT_EUR,
        "zakat_exemple_1000_eur": TAUX_ZAKAT_ANNUEL * 1_000.0,
    }
    return equations, etat


# ---------------------------------------------------------------------------
# 3. ÉQUATIONS DE FINANCEMENT : HALAL vs USURAIRE
# ---------------------------------------------------------------------------
def calculer_financement_halal_vs_usure(
    capital: float = 10_000.0,
    taux_profit: float = 0.08,
    part_profit: float = 0.50,
    taux_usure: float = 0.05,
    annees: int = 10,
) -> Tuple[List[Equation], Dict[str, Any]]:
    a_halal = capital * (1.0 + part_profit * taux_profit) ** annees
    a_usure = capital * (1.0 + taux_usure) ** annees
    ecart = a_usure - a_halal
    ratio = a_usure / a_halal

    perte = -abs(taux_profit)
    a_halal_perte = capital * (1.0 + part_profit * perte) ** annees
    surendettement = a_usure - a_halal_perte

    # Mudaraba / Musharaka 50/50 sur un profit de 2 000.
    profit_exemple = 2_000.0
    part_a = profit_exemple * part_profit
    part_b = profit_exemple * (1.0 - part_profit)

    # Partage des pertes au prorata des capitaux.
    cap_a, cap_b, perte_exemple = 6_000.0, 4_000.0, 1_000.0
    perte_a = perte_exemple * cap_a / (cap_a + cap_b)
    perte_b = perte_exemple - perte_a

    # Murabaha : coût + marge fixe, sans intérêt.
    cout, marge, mensualites = 10_000.0, 0.10, 12
    prix_murabaha = cout * (1.0 + marge)
    mensualite = prix_murabaha / mensualites

    equations = [
        _eq(
            "FIN-01",
            "Financement",
            "Capital halal participatif",
            "A_h = C·(1 + s·q)^n",
            {"C": capital, "s": part_profit, "q": taux_profit, "n": annees},
            a_halal,
            "EUR",
            STATUT_ILLUSTRATIF,
            "scénario Mudaraba/Musharaka",
        ),
        _eq(
            "FIN-02",
            "Financement",
            "Capital usuraire composé",
            "A_u = C·(1 + r)^n",
            {"C": capital, "r": taux_usure, "n": annees},
            a_usure,
            "EUR",
            STATUT_ILLUSTRATIF,
            "scénario prêt à intérêt",
        ),
        _eq(
            "FIN-03",
            "Financement",
            "Écart nominal riba / halal",
            "Δ = A_u − A_h",
            {"A_u": a_usure, "A_h": a_halal},
            ecart,
            "EUR",
            STATUT_ILLUSTRATIF,
            "dérivé de FIN-01 et FIN-02",
        ),
        _eq(
            "FIN-04",
            "Financement",
            "Ratio de divergence",
            "ρ = A_u / A_h",
            {"A_u": a_usure, "A_h": a_halal},
            ratio,
            "ratio",
            STATUT_ILLUSTRATIF,
            "dérivé de FIN-01 et FIN-02",
        ),
        _eq(
            "FIN-05",
            "Financement",
            "Scénario de perte partagée",
            "A_h⁻ = C·(1 + s·(−|q|))^n",
            {"C": capital, "s": part_profit, "q": perte, "n": annees},
            a_halal_perte,
            "EUR",
            STATUT_ILLUSTRATIF,
            "scénario de perte, même formule participative",
        ),
        _eq(
            "FIN-06",
            "Financement",
            "Surendettement en cas de perte",
            "Σ = dette_usuraire − valeur_halal_résiduelle",
            {"dette": a_usure, "valeur_residuelle": a_halal_perte},
            surendettement,
            "EUR",
            STATUT_ILLUSTRATIF,
            "dérivé de FIN-02 et FIN-05",
        ),
        _eq(
            "FIN-07",
            "Financement",
            "Partage 50/50 d'un profit",
            "Π_A = Π·s ; Π_B = Π·(1 − s)",
            {"profit": profit_exemple, "part_A": part_a, "part_B": part_b},
            part_a,
            "EUR (part A)",
            STATUT_OPERATIONNEL,
            "moteur_economie_islamique_mizan.py (clé 50/50)",
        ),
        _eq(
            "FIN-08",
            "Financement",
            "Partage des pertes au prorata",
            "L_A = L·C_A/(C_A + C_B)",
            {"perte": perte_exemple, "C_A": cap_a, "C_B": cap_b},
            perte_a,
            "EUR (part A)",
            STATUT_SPECIFIE,
            "convention Musharaka du projet",
        ),
        _eq(
            "FIN-09",
            "Financement",
            "Murabaha (coût + marge)",
            "P = C·(1 + m) ; mensualité = P/k",
            {"cout": cout, "marge": marge, "mensualites": mensualites},
            prix_murabaha,
            "EUR (prix total)",
            STATUT_ILLUSTRATIF,
            "moteur_economie_islamique_mizan.py (MURABAHA)",
        ),
        _eq(
            "FIN-10",
            "Financement",
            "Qard Hassan",
            "R = C ; intérêt = 0",
            {"capital": cout},
            cout,
            "EUR (remboursement)",
            STATUT_OPERATIONNEL,
            "moteur_economie_islamique_mizan.py (QARD_HASSAN)",
        ),
    ]
    etat = {
        "capital_initial": capital,
        "taux_profit": taux_profit,
        "part_profit": part_profit,
        "taux_usure": taux_usure,
        "annees": annees,
        "capital_halal": a_halal,
        "capital_usuraire": a_usure,
        "ecart_nominal": ecart,
        "ratio_divergence": ratio,
        "capital_halal_en_perte": a_halal_perte,
        "surendettement": surendettement,
        "prix_murabaha": prix_murabaha,
        "mensualite_murabaha": mensualite,
    }
    return equations, etat


# ---------------------------------------------------------------------------
# 4. ÉQUATIONS MACROÉCONOMIQUES MONDIALES (illustratives)
# ---------------------------------------------------------------------------
def calculer_equations_macro(
    conso: float = 60.0,
    invest: float = 20.0,
    depenses_publiques: float = 15.0,
    exportations: float = 25.0,
    importations: float = 20.0,
    dette_initiale: float = 100.0,
    pib_initial: float = 100.0,
    taux_dette: float = 0.05,
    croissance: float = 0.02,
    annees: int = 30,
    masse_monetaire: float = 1_000.0,
    vitesse: float = 2.5,
    transactions: float = 1_000.0,
    croissance_monetaire: float = 0.07,
    croissance_vitesse: float = 0.0,
    croissance_reelle: float = 0.02,
) -> Tuple[List[Equation], Dict[str, Any]]:
    pib = conso + invest + depenses_publiques + (exportations - importations)
    dette_n = dette_initiale * (1.0 + taux_dette) ** annees
    pib_n = pib_initial * (1.0 + croissance) ** annees
    ratio_dette = dette_n / pib_n
    niveau_prix = masse_monetaire * vitesse / transactions
    inflation = croissance_monetaire + croissance_vitesse - croissance_reelle

    equations = [
        _eq(
            "MAC-01",
            "Macro-monde",
            "Identité du PIB",
            "Y = C + I + G + (X − M)",
            {
                "C": conso,
                "I": invest,
                "G": depenses_publiques,
                "X": exportations,
                "M": importations,
            },
            pib,
            "UM (unités monétaires normalisées)",
            STATUT_ILLUSTRATIF,
            "comptabilité nationale (scénario)",
        ),
        _eq(
            "MAC-02",
            "Macro-monde",
            "Dynamique de la dette",
            "D_n = D_0·(1 + r)^n",
            {"D_0": dette_initiale, "r": taux_dette, "n": annees},
            dette_n,
            "UM",
            STATUT_ILLUSTRATIF,
            "intérêt composé (scénario)",
        ),
        _eq(
            "MAC-03",
            "Macro-monde",
            "Dynamique du PIB",
            "Y_n = Y_0·(1 + g)^n",
            {"Y_0": pib_initial, "g": croissance, "n": annees},
            pib_n,
            "UM",
            STATUT_ILLUSTRATIF,
            "croissance composée (scénario)",
        ),
        _eq(
            "MAC-04",
            "Macro-monde",
            "Ratio dette / PIB",
            "d_n = D_n / Y_n",
            {"D_n": dette_n, "Y_n": pib_n},
            ratio_dette,
            "ratio",
            STATUT_ILLUSTRATIF,
            "dérivé de MAC-02 et MAC-03",
        ),
        _eq(
            "MAC-05",
            "Macro-monde",
            "Condition de divergence r > g",
            "r − g",
            {"r": taux_dette, "g": croissance},
            taux_dette - croissance,
            "point de %",
            STATUT_ILLUSTRATIF,
            "critère de divergence de la dette",
        ),
        _eq(
            "MAC-06",
            "Macro-monde",
            "Équation des échanges (Fisher)",
            "M·V = P·T ⇒ P = M·V / T",
            {"M": masse_monetaire, "V": vitesse, "T": transactions},
            niveau_prix,
            "prix par transaction",
            STATUT_ILLUSTRATIF,
            "théorie quantitative de la monnaie (scénario)",
        ),
        _eq(
            "MAC-07",
            "Macro-monde",
            "Décomposition de l'inflation",
            "π ≈ μ + v − y",
            {"mu": croissance_monetaire, "v": croissance_vitesse, "y": croissance_reelle},
            inflation,
            "taux (fraction)",
            STATUT_ILLUSTRATIF,
            "approximation en taux de croissance",
        ),
        _eq(
            "MAC-08",
            "Macro-monde",
            "Charge d'intérêt de la dette",
            "B = D_0·r",
            {"D_0": dette_initiale, "r": taux_dette},
            dette_initiale * taux_dette,
            "UM/an",
            STATUT_ILLUSTRATIF,
            "service de la dette (scénario)",
        ),
        _eq(
            "MAC-09",
            "Macro-monde",
            "Injection redistributive de la Zakat",
            "I_Z = 2,5 % × W",
            {"taux": TAUX_ZAKAT_ANNUEL, "richesse": pib_initial},
            TAUX_ZAKAT_ANNUEL * pib_initial,
            "UM",
            STATUT_ILLUSTRATIF,
            "stabilisateur automatique (scénario)",
        ),
    ]
    etat = {
        "pib": pib,
        "dette_finale": dette_n,
        "pib_final": pib_n,
        "ratio_dette_pib": ratio_dette,
        "condition_r_superieur_g": taux_dette > croissance,
        "niveau_prix": niveau_prix,
        "inflation": inflation,
        "charge_interet": dette_initiale * taux_dette,
    }
    return equations, etat


# ---------------------------------------------------------------------------
# 5. ADOSSEMENT MONÉTAIRE MZN (or et argent)
# ---------------------------------------------------------------------------
def calculer_adossement_monetaire(
    masse_mzn: float = MASSE_MZN_REFERENCE,
    mzn_par_eur: float = MZN_PAR_EUR_NOMINAL,
    reserve_or_kg: Optional[float] = None,
) -> Tuple[List[Equation], Dict[str, Any]]:
    equivalent_eur = masse_mzn / mzn_par_eur
    or_kg = equivalent_eur * OR_MG_PAR_EUR / 1_000_000.0
    argent_kg = equivalent_eur * ARGENT_MG_PAR_EUR / 1_000_000.0

    equations = [
        _eq(
            "ADO-01",
            "Adossement",
            "Équivalent nominal en EUR",
            "E = M_MZN / 1 000",
            {"masse_mzn": masse_mzn, "mzn_par_eur": mzn_par_eur},
            equivalent_eur,
            "EUR",
            STATUT_SPECIFIE,
            "parité nominale du projet (1 000 MZN = 1 EUR)",
        ),
        _eq(
            "ADO-02",
            "Adossement",
            "Exigence d'or",
            "G_Au = E × 14,50 mg / 10⁶",
            {"E": equivalent_eur, "mg_par_eur": OR_MG_PAR_EUR},
            or_kg,
            "kg Au",
            STATUT_CALIBRE,
            "étalonnage A097/A105",
        ),
        _eq(
            "ADO-03",
            "Adossement",
            "Exigence d'argent",
            "G_Ag = E × 1 150 mg / 10⁶",
            {"E": equivalent_eur, "mg_par_eur": ARGENT_MG_PAR_EUR},
            argent_kg,
            "kg Ag",
            STATUT_CALIBRE,
            "étalonnage A097/A105",
        ),
    ]

    etat: Dict[str, Any] = {
        "masse_mzn": masse_mzn,
        "equivalent_eur": equivalent_eur,
        "exigence_or_kg": or_kg,
        "exigence_argent_kg": argent_kg,
    }
    if reserve_or_kg is not None and or_kg > 0:
        couverture = reserve_or_kg / or_kg
        equations.append(
            _eq(
                "ADO-04",
                "Adossement",
                "Taux de couverture or",
                "ρ = Réserve_or / G_Au",
                {"reserve_or_kg": reserve_or_kg, "exigence_or_kg": or_kg},
                couverture,
                "ratio",
                STATUT_ILLUSTRATIF,
                "exemple de réserve déclarée, non auditée",
            )
        )
        etat["taux_couverture_or"] = couverture
    return equations, etat


# ---------------------------------------------------------------------------
# 6. TENSION ÉCONOMIQUE ET HARMONISATION HALAL / USURAIRE
# ---------------------------------------------------------------------------
def calculer_tension_economique(
    taux_interet: float,
    part_profit: float,
    zakat_payee: bool,
    taux_adossement: float,
) -> Dict[str, Any]:
    """
    Tension économique interne dans [0,1] (0 = harmonie parfaite).
    Elle agrège : riba, écart au partage 50/50, zakat payée, adossement.
    Convention interne, non certifiée par un tiers.
    """
    t_riba = min(1.0, max(0.0, float(taux_interet)) / TAUX_USURE_REFERENCE)
    t_partage = min(1.0, abs(float(part_profit) - 0.5) / 0.5)
    t_zakat = 0.0 if zakat_payee else 1.0
    t_adossement = 1.0 - min(1.0, max(0.0, float(taux_adossement)))

    tension = (
        POIDS_TENSION["riba"] * t_riba
        + POIDS_TENSION["partage"] * t_partage
        + POIDS_TENSION["zakat"] * t_zakat
        + POIDS_TENSION["adossement"] * t_adossement
    )
    return {
        "tension_riba": round(t_riba, 6),
        "tension_partage": round(t_partage, 6),
        "tension_zakat": round(t_zakat, 6),
        "tension_adossement": round(t_adossement, 6),
        "tension_economique": round(tension, 6),
        "indice_harmonie_economique": round(1.0 - tension, 6),
        "conforme_bride_mizan": bool(tension <= BRIDE_MIZAN),
    }


def calculer_scenarios_harmonisation() -> Tuple[List[Equation], Dict[str, Any]]:
    scenarios = {
        "halal_pur": {
            "taux_interet": 0.0,
            "part_profit": 0.5,
            "zakat_payee": True,
            "taux_adossement": 1.0,
        },
        "usuraire": {
            "taux_interet": 0.05,
            "part_profit": 0.0,
            "zakat_payee": False,
            "taux_adossement": 0.10,
        },
        "hybride_harmonise": {
            "taux_interet": 0.0,
            "part_profit": 0.5,
            "zakat_payee": True,
            "taux_adossement": 0.50,
        },
    }
    resultats = {nom: calculer_tension_economique(**params) for nom, params in scenarios.items()}

    equations = [
        _eq(
            "HAR-01",
            "Harmonisation",
            "Tension économique",
            "T = 0,40·t_riba + 0,20·t_partage + 0,20·t_zakat + 0,20·t_adossement",
            {
                "t_riba": "min(1, r/0,20)",
                "t_partage": "|s − 0,5|/0,5",
                "t_zakat": "0 si payée, sinon 1",
                "t_adossement": "1 − min(1, ρ)",
            },
            resultats["halal_pur"]["tension_economique"],
            "indice [0,1]",
            STATUT_SPECIFIE,
            "convention interne du projet",
        ),
        _eq(
            "HAR-02",
            "Harmonisation",
            "Scénario halal pur",
            "T(h=0, s=0,5, Z=1, ρ=1)",
            scenarios["halal_pur"],
            resultats["halal_pur"]["tension_economique"],
            "tension",
            STATUT_ILLUSTRATIF,
            "scénario de référence",
        ),
        _eq(
            "HAR-03",
            "Harmonisation",
            "Scénario usuraire",
            "T(r=5 %, s=0, Z=0, ρ=0,1)",
            scenarios["usuraire"],
            resultats["usuraire"]["tension_economique"],
            "tension",
            STATUT_ILLUSTRATIF,
            "scénario de comparaison",
        ),
        _eq(
            "HAR-04",
            "Harmonisation",
            "Scénario hybride harmonisé",
            "T(r=0, s=0,5, Z=1, ρ=0,5)",
            scenarios["hybride_harmonise"],
            resultats["hybride_harmonise"]["tension_economique"],
            "tension",
            STATUT_ILLUSTRATIF,
            "usure interceptée + adossement partiel",
        ),
        _eq(
            "HAR-05",
            "Harmonisation",
            "Pont de purification",
            "Φ = flux_usuraires_interceptés / flux_totaux_offerts",
            {"definition": "les flux à intérêt sont refusés, jamais conservés"},
            "mesuré sur le registre réel",
            "ratio",
            STATUT_OPERATIONNEL,
            "registre_economie_islamique_mizan.json",
        ),
        _eq(
            "HAR-06",
            "Harmonisation",
            "Indice d'harmonie économique",
            "H = 1 − T",
            {"T": resultats["halal_pur"]["tension_economique"]},
            1.0 - resultats["halal_pur"]["tension_economique"],
            "indice [0,1]",
            STATUT_SPECIFIE,
            "dérivé de HAR-01",
        ),
    ]
    return equations, {"parametres": scenarios, "resultats": resultats}


# ---------------------------------------------------------------------------
# 7. LECTURE RÉELLE DU REGISTRE ÉCONOMIQUE
# ---------------------------------------------------------------------------
def statistiques_registre_islamique(
    chemin: Path = FICHIER_REGISTRE_ISLAMIQUE,
) -> Dict[str, Any]:
    """Lit le registre persisté sans le modifier. Retourne des compteurs réels."""
    vide = {
        "registre_present": False,
        "contrats_total": 0,
        "contrats_valides": 0,
        "contrats_rejetes_riba": 0,
        "contrats_rejetes_gharar": 0,
        "capital_valide_eur": 0.0,
        "capital_rejete_riba_eur": 0.0,
        "taux_interception_riba": 0.0,
        "operations_zakat": 0,
        "zakat_prelevee_totale": 0.0,
        "tension_moyenne_contrats": 0.0,
        "tension_moyenne_contrats_valides": 0.0,
        "tension_moyenne_contrats_rejetes": 0.0,
    }
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return vide

    contrats = data.get("contrats", {}) or {}
    operations = data.get("operations_zakat", []) or []
    valides = [c for c in contrats.values() if c.get("statut_conformite_sharia") == "VALIDE_CONFORME"]
    rejetes_riba = [c for c in contrats.values() if c.get("statut_conformite_sharia") == "REJETE_RIBA"]
    rejetes_gharar = [c for c in contrats.values() if c.get("statut_conformite_sharia") == "REJETE_GHARAR"]

    tensions: List[float] = []
    tensions_valides: List[float] = []
    tensions_rejetes: List[float] = []
    for contrat in contrats.values():
        part = 0.5
        cle = str(contrat.get("cle_partage_profits", "50/50"))
        try:
            if "/" in cle:
                haut, bas = cle.split("/", 1)
                part = float(haut) / (float(haut) + float(bas)) if float(haut) + float(bas) else 0.5
        except ValueError:
            part = 0.5
        adossement = 1.0 if (contrat.get("adossement_physique") or {}).get("actif_reel") else 0.0
        statut = contrat.get("statut_conformite_sharia")
        # La zakat n'est imputable qu'aux contrats effectivement homologués.
        zakat_payee = bool(operations) and statut == "VALIDE_CONFORME"
        tension = calculer_tension_economique(
            taux_interet=float(contrat.get("taux_interet_annuel", 0.0)),
            part_profit=part,
            zakat_payee=zakat_payee,
            taux_adossement=adossement,
        )["tension_economique"]
        tensions.append(tension)
        if statut == "VALIDE_CONFORME":
            tensions_valides.append(tension)
        else:
            tensions_rejetes.append(tension)

    return {
        "registre_present": True,
        "contrats_total": len(contrats),
        "contrats_valides": len(valides),
        "contrats_rejetes_riba": len(rejetes_riba),
        "contrats_rejetes_gharar": len(rejetes_gharar),
        "capital_valide_eur": round(sum(float(c.get("capital_initial", 0.0)) for c in valides), 2),
        "capital_rejete_riba_eur": round(
            sum(float(c.get("capital_initial", 0.0)) for c in rejetes_riba), 2
        ),
        "taux_interception_riba": round(len(rejetes_riba) / len(contrats), 6) if contrats else 0.0,
        "operations_zakat": len(operations),
        "zakat_prelevee_totale": round(
            sum(float(op.get("montant_zakat_preleve", 0.0)) for op in operations), 2
        ),
        "tension_moyenne_contrats": round(sum(tensions) / len(tensions), 6) if tensions else 0.0,
        "tension_moyenne_contrats_valides": (
            round(sum(tensions_valides) / len(tensions_valides), 6) if tensions_valides else 0.0
        ),
        "tension_moyenne_contrats_rejetes": (
            round(sum(tensions_rejetes) / len(tensions_rejetes), 6) if tensions_rejetes else 0.0
        ),
    }


# ---------------------------------------------------------------------------
# 8. BILAN CONSOLIDÉ
# ---------------------------------------------------------------------------
def construire_bilan_complet(index_pulsation: int = 0) -> Dict[str, Any]:
    """Assemble toutes les équations et tous les résultats, sans écrire de fichier."""
    eq_tri, etat_tri = calculer_equations_trinite(index_pulsation=index_pulsation)
    eq_mon, etat_mon = calculer_equations_or_argent()
    eq_fin, etat_fin = calculer_financement_halal_vs_usure()
    eq_mac, etat_mac = calculer_equations_macro()
    eq_ado, etat_ado = calculer_adossement_monetaire()
    eq_har, etat_har = calculer_scenarios_harmonisation()
    stats = statistiques_registre_islamique()

    equations = eq_tri + eq_mon + eq_fin + eq_mac + eq_ado + eq_har
    return {
        "titre": "ÉQUATIONS CONSOLIDÉES DE L'ÉCONOMIE MONDIALE HARMONIQUE AL-MIZAN",
        "acte": "A241",
        "horodatage": _iso(),
        "nombre_equations": len(equations),
        "invariants": {
            "bride_mizan": BRIDE_MIZAN,
            "ligne_ref": LIGNE_REF,
            "plafond_effectif": PLAFOND_EFFECTIF,
            "riba": TAUX_RIBA_MAXIMUM_AUTORISE,
            "zakat": TAUX_ZAKAT_ANNUEL,
            "partage_cible": 0.5,
        },
        "etats": {
            "trinite": etat_tri,
            "or_argent": etat_mon,
            "financement": etat_fin,
            "macro": etat_mac,
            "adossement": etat_ado,
            "harmonisation": etat_har,
            "registre": stats,
        },
        "equations": [asdict(e) for e in equations],
        "provenances": {
            STATUT_OPERATIONNEL: "calcul exécuté par le code, invariant vérifiable",
            STATUT_CALIBRE: "étalonnage or/argent A097/A105, non vérifié temps réel",
            STATUT_SPECIFIE: "convention interne, non certifiée par un tiers",
            STATUT_ILLUSTRATIF: "scénario à hypothèses explicites, sans prévision",
        },
        "avertissement": (
            "Aucun résultat illustratif ne constitue une prévision, un conseil en "
            "investissement ou une mesure de l'économie réelle. Les exigences "
            "d'adossement sont des paramétrages, pas une preuve de réserve physique."
        ),
    }


# ---------------------------------------------------------------------------
# 9. RENDU MARKDOWN
# ---------------------------------------------------------------------------
def _ligne_tableau(e: Dict[str, Any]) -> str:
    resultat = e["resultat"]
    if isinstance(resultat, bool):
        resultat_txt = "oui" if resultat else "non"
    elif isinstance(resultat, (int, float)):
        resultat_txt = _f(float(resultat), 6)
    else:
        resultat_txt = str(resultat)
    formule = str(e["formule"]).replace("|", "\\|")
    return (
        f"| `{e['code']}` | {e['nom']} | `{formule}` | {resultat_txt} | "
        f"{e['unite']} | {e['statut']} | {e['source']} |"
    )


def generer_markdown(bilan: Dict[str, Any]) -> str:
    domaines: List[str] = []
    for e in bilan["equations"]:
        if e["domaine"] not in domaines:
            domaines.append(e["domaine"])

    lignes: List[str] = [
        "# Équations consolidées de l'économie mondiale harmonique — Al-Mizan",
        "",
        f"- **Acte** : {bilan['acte']}",
        f"- **Horodatage UTC** : {bilan['horodatage']}",
        f"- **Nombre d'équations** : {bilan['nombre_equations']}",
        f"- **Bride Mizan** : {bilan['invariants']['bride_mizan']}",
        f"- **Riba** : {bilan['invariants']['riba']}",
        f"- **Zakat** : {bilan['invariants']['zakat'] * 100:.1f} %",
        "",
        "> Avertissement : les résultats marqués **ILLUSTRATIF** sont des scénarios à "
        "hypothèses explicites. Ils ne constituent ni une prévision, ni un conseil en "
        "investissement, ni une mesure de l'économie réelle. Les exigences d'adossement "
        "or/argent sont des paramétrages du projet, pas une preuve de réserve physique.",
        "",
    ]

    for domaine in domaines:
        lignes.append(f"## {domaine}")
        lignes.append("")
        lignes.append("| Code | Équation | Formule | Résultat | Unité | Provenance | Source |")
        lignes.append("|---|---|---|---|---|---|---|")
        for e in bilan["equations"]:
            if e["domaine"] == domaine:
                lignes.append(_ligne_tableau(e))
        lignes.append("")

    stats = bilan["etats"]["registre"]
    lignes.extend(
        [
            "## Registre économique réel (lecture seule)",
            "",
            f"- Registre présent : {'oui' if stats['registre_present'] else 'non'}",
            f"- Contrats soumis : {stats['contrats_total']}",
            f"- Contrats validés : {stats['contrats_valides']}",
            f"- Tentatives d'usure rejetées : {stats['contrats_rejetes_riba']}",
            f"- Autres rejets (gharar) : {stats['contrats_rejetes_gharar']}",
            f"- Capital validé : {_f(stats['capital_valide_eur'], 2)} EUR",
            f"- Capital usuraire intercepté : {_f(stats['capital_rejete_riba_eur'], 2)} EUR",
            f"- Taux d'interception de l'usure : {stats['taux_interception_riba'] * 100:.2f} %",
            f"- Opérations de zakat : {stats['operations_zakat']}",
            f"- Zakat prélevée cumulée : {_f(stats['zakat_prelevee_totale'], 2)} MZN",
            f"- Tension moyenne des contrats validés : {stats['tension_moyenne_contrats_valides']}",
            f"- Tension moyenne des contrats rejetés : {stats['tension_moyenne_contrats_rejetes']}",
            f"- Tension moyenne de tous les contrats soumis : {stats['tension_moyenne_contrats']}",
            "",
            "## Provenances",
            "",
        ]
    )
    for statut, description in bilan["provenances"].items():
        lignes.append(f"- **{statut}** : {description}")
    lignes.extend(
        [
            "",
            "## Limites explicites",
            "",
            "- Aucune donnée de marché en temps réel n'est consultée par ce module.",
            "- Aucun portefeuille, aucune clé privée et aucun actif ne sont détenus.",
            "- Les scénarios macroéconomiques ne sont pas des prévisions.",
            "- La conformité religieuse relève d'une autorité compétente, pas de ce code.",
            "",
        ]
    )
    return "\n".join(lignes)


# ---------------------------------------------------------------------------
# 10. SCEAU DE L'ACTE A241
# ---------------------------------------------------------------------------
def _sceau(payload: Dict[str, Any]) -> str:
    canonique = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonique.encode("utf-8")).hexdigest()


def sceller_acte_a241(persister: bool = True) -> Dict[str, Any]:
    """
    Exécute le bilan complet, pulse la Trinité, audite la base avec l'agent de
    code, puis scelle l'acte A241.
    persister=False n'écrit rien et n'appelle aucune sonde qui écrit
    (ni le battement, ni l'agent) : retour purement calculé.
    """
    index_vivant = int(time.time_ns() // (1_000_000_000 / 135))
    bilan = construire_bilan_complet(index_pulsation=index_vivant)

    trinite_vivante: Dict[str, Any] = {}
    audit_agent: Dict[str, Any] = {}
    if persister:
        try:
            from conscience_logique.battement_triangulaire_trinite import battre_triangle_trinite

            etat = battre_triangle_trinite()
            trinite_vivante = asdict(etat)
        except Exception as exc:  # le bilan reste valide même si la sonde physique échoue
            trinite_vivante = {"erreur": f"sonde indisponible : {type(exc).__name__}"}

        try:
            from agent_de_code_harmonisateur_mizan import AGENT_CODE_AL_MIZAN

            audit = AGENT_CODE_AL_MIZAN.harmoniser_base_complete()
            audit_agent = {
                "agent": audit.get("agent"),
                "total_modules_examines": audit.get("total_modules_examines"),
                "score_harmonie_global_mizan": audit.get("score_harmonie_global_mizan"),
                "invariants_garantis": audit.get("invariants_garantis"),
            }
        except Exception as exc:
            audit_agent = {"erreur": f"agent indisponible : {type(exc).__name__}"}
    else:
        trinite_vivante = {
            "mode": "calcul_pur",
            "indice_harmonie_trinite": bilan["etats"]["trinite"]["indice_harmonie_trinite"],
        }
        audit_agent = {"mode": "non_execute_en_mode_calcul_pur"}

    tension_economique = bilan["etats"]["registre"]["tension_moyenne_contrats"]
    indice_trinite_calcule = bilan["etats"]["trinite"]["indice_harmonie_trinite"]
    indice_trinite = float(trinite_vivante.get("indice_harmonie_trinite", indice_trinite_calcule))
    indice_global = (tension_economique + indice_trinite) / 2.0

    payload: Dict[str, Any] = {
        "acte": "A241",
        "titre": "Équations consolidées de l'économie mondiale harmonique et invariants de la Trinité",
        "horodatage": bilan["horodatage"],
        "bilan_equations": bilan,
        "trinite_vivante": trinite_vivante,
        "audit_agent_code": audit_agent,
        "pont_global": {
            "tension_economique_moyenne": tension_economique,
            "indice_harmonie_trinite": round(indice_trinite, 6),
            "indice_harmonie_trinite_calcul_pur": round(indice_trinite_calcule, 6),
            "indice_global": round(indice_global, 6),
            "conforme_bride_mizan": bool(indice_global <= BRIDE_MIZAN),
            "nature": "indice interne du projet, non certifié",
        },
        "sources_utilisees": [
            "moteur_economie_islamique_mizan.py",
            "horloge_noyau/horloge_logique_mizan.py",
            "bibliotheques/lib_almizan_extension.py",
            "conscience_logique/battement_triangulaire_trinite.py",
            "agent_de_code_harmonisateur_mizan.py",
            "memoire_aq/registre_economie_islamique_mizan.json",
        ],
        "doctrine": "On ne supprime rien, on harmonise.",
    }
    payload["sceau_sha256"] = _sceau(payload)

    if persister:
        DOSSIER_ACTES.mkdir(parents=True, exist_ok=True)
        CHEMIN_ACTE_A241.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        CHEMIN_DOCUMENT.write_text(generer_markdown(bilan), encoding="utf-8")
    return payload


if __name__ == "__main__":
    acte = sceller_acte_a241(persister=True)
    bilan = acte["bilan_equations"]
    print("=" * 78)
    print("ÉQUATIONS CONSOLIDÉES — ÉCONOMIE MONDIALE HARMONIQUE AL-MIZAN")
    print("=" * 78)
    print(f"Acte          : {acte['acte']} — {bilan['nombre_equations']} équations")
    print(f"Or            : {_f(bilan['etats']['or_argent']['prix_or_eur_g'], 4)} EUR/g")
    print(f"Argent        : {_f(bilan['etats']['or_argent']['prix_argent_eur_g'], 4)} EUR/g")
    print(f"Ratio Au/Ag   : {_f(bilan['etats']['or_argent']['ratio_bimetallique'], 4)}")
    print(f"Nisab or      : {_f(bilan['etats']['or_argent']['nisab_or_eur'], 2)} EUR")
    print(f"Nisab argent  : {_f(bilan['etats']['or_argent']['nisab_argent_eur'], 2)} EUR")
    print(f"Halal 10 ans  : {_f(bilan['etats']['financement']['capital_halal'], 2)} EUR")
    print(f"Riba 10 ans   : {_f(bilan['etats']['financement']['capital_usuraire'], 2)} EUR")
    print(f"Exigence Au   : {_f(bilan['etats']['adossement']['exigence_or_kg'], 4)} kg")
    print(f"Exigence Ag   : {_f(bilan['etats']['adossement']['exigence_argent_kg'], 2)} kg")
    print(f"Bride Mizan   : {BRIDE_MIZAN}")
    print(f"Indice global : {acte['pont_global']['indice_global']} "
          f"(conforme={acte['pont_global']['conforme_bride_mizan']})")
    print(f"Acte scellé   : {CHEMIN_ACTE_A241}")
    print(f"Document      : {CHEMIN_DOCUMENT}")
    print("=" * 78)
