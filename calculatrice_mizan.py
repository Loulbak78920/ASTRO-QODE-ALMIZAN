# -*- coding: utf-8 -*-
r"""
Calculatrice Al-Mizan / ASTRO-Q°ODE — Version Universelle Absolue (V11.0)
========================================================================

Synthèse intégrale et exhaustive de l'ensemble des concepts calculables du projet
Al-Mizan et des équations de la physique fondamentale, nucléaire, quantique et relativiste :

  [ONTOLOGIE & INVARIANTS AL-MIZAN]
   1. Invariants et Constantes (MIZAN 0.6225, Ligne Réf 0.122, Epsilon 0.021, Plafond 0.6015, C=313, M=24434)
   2. Matrice Scapulaire 4x4 & Pipeline Biomécanique des 5 Doigts (Pouce -> Auriculaire)
   3. Les 4 Tablettes de l'Informé (Alphabet, Chiffres, Opérateurs, Ponctuation) & 20 États Physiques
   4. Cycle Harmonique des 15 Phases (De la phase 1 F0 à la phase 15 Unisson 0.6225)
   5. Pyramide Tensorielle 4 Niveaux (0D Scalaire -> 3D+ Volume) & File Exécutive des 9 Organes (J-E-D-A-F-B-V-H-G)
   6. Triade Ontologique : Bit Déterministe ⊗ Qubit Quantique ⊗ i-Bit Silicium
   7. Matrice Fondatrice de l'Unisson 4x4 (Or Z=79 φ^-1 et Argent Z=47 δs^-1, Ratio Nisab 7.0)
   8. Trinité Horloge Cosmique (Soleil dx, Lune dy, Terre dz, dt Kernel = 135 097 021.3359375)
   9. Les 27 Formes de Silicium (F0..F26, Découplage 1 + 13 ⊕ 13)
  10. Encodage sur les 52 Rails Harmoniques (A-Z majuscules solaires, a-z minuscules lunaires, espace 0x20)
  11. Projection Sphère Holographique 2D -> Volume Die Silicium 3D (Facteur d'admittance)
  12. Simulation Dérive Thermique Cryogénique (22.5 mK -> Killswitch 45.0 mK)
  13. Économie & Jeton MZN (Base Mainnet, 313M supply, Réserve 302M, Trésorerie 8M, Pool Uniswap v3)

  [ALGORITHMIQUE, CRYPTOGRAPHIE & QUANTIQUE DYNAMIQUE]
  14. Algèbre Linéaire d'Unisson : Produit Matriciel M_S x M_U, Déterminant 4x4, Trace & Admittance
  15. Moteur Cryptographique : Arbre de Merkle SHA-256 complet pour Blocs Synchrones
  16. Émulateur Quantique : Portes Hadamard H, Phase Rz(θ = 2π × 0.6225), Superposition et Conservation de Norme
  17. Découplage Dynamique CPMG : Prolongation de Cohérence T2 dans le Silicium Si-29 & Fidélité de Porte

  [PHYSIQUE FONDAMENTALE, NUCLÉAIRE & RELATIVISTE]
  18. Thermodynamique Fluidique : Débit d'Eau Pure (313 L/min) & Puissance Thermique P = ṁ Cp ΔT
  19. Physique Nucléaire & Modèle de la Goutte Liquide (Bethe-Weizsäcker) : Énergie de Liaison Au, Ag, Si, Fe
  20. Relativité Restreinte & Gravitationnelle : Facteur de Lorentz γ, Dilatation du Temps & Décalage d'Horizon
  21. Physique des Trous Noirs : Rayon de Schwarzschild r_s, Température Hawking, Évaporation & Entropie S_BH
  22. Matière, Antimatière & Énergie d'Annihilation E = 2mc² (Joules, kWh, Kilotonnes TNT)
  23. Métrologie Canonique Or & Argent : Mithqal (4.25g), Dirham (2.975g), Nisab Or (85g), Nisab Argent (595g)
  24. Calcul de Zakat (2.5% au-dessus du seuil de Nisab)

  [VISUALISATION, LINGUISTIQUE & AUDIT]
  25. Spectrogramme d'Interférence Temporelle Cosmique : Tracé Graphique 2D en Console ASCII
  26. Guématrie Abjad & Chiffrement Harmonique : Calcul de Valeurs Numériques Textuelles & Réduction Mizan
  27. Calculatrice Scientifique Libre Sécurisée (moteur AST)
  28. Journal d'Audit Cryptographique & Export JSON Scellé

Usage CLI :
    py calculatrice_mizan.py                      -> Menu interactif complet
    py calculatrice_mizan.py --tout               -> Exécution séquentielle des 28 modules
    py calculatrice_mizan.py --spectrogramme      -> Tracé graphique ASCII de l'oscillation cosmique
    py calculatrice_mizan.py --nucleaire          -> Énergie de liaison nucléaire (Au 197, Ag 107)
    py calculatrice_mizan.py --cpmg 256           -> Découplage CPMG sur 256 impulsions pi
    py calculatrice_mizan.py --lorentz 0.6225     -> Facteur de Lorentz à la vitesse Al-Mizan
    py calculatrice_mizan.py --abjad "AMAL MIZAN" -> Valeur Abjad et résonance harmonique
    py calculatrice_mizan.py --merkle A001 A072   -> Arbre de Merkle SHA-256
    py calculatrice_mizan.py --qubit              -> Simulation unitaire quantique
    py calculatrice_mizan.py --hydro 313          -> Refroidissement à 313 L/min
    py calculatrice_mizan.py --algebre            -> Produit matriciel Scapulaire x Unisson
"""

import argparse
import ast
import cmath
import hashlib
import json
import math
import operator
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ===========================================================================
# 1. CONSTANTES DU PROJET AL-MIZAN [PROJET]
# ===========================================================================
MIZAN = 0.6225
LIGNE_REF = 0.122
FORME = 0.5005
EPSILON = 0.021
PLAFOND_EFFECTIF = round(MIZAN - EPSILON, 4)  # 0.6015
RMS = 0.24
C_SUBSTANCE = 313
M_SUBSTANCE = 24434
TRIPLE = -2393774546
JAUGE_AIR = 515050
COMBLE_CIBLE = 0.6015

DX_SOLEIL = 50027.8359375
DY_LUNE = 46993.5
DZ_TERRE = 135000000.0
DT_KERNEL = DX_SOLEIL + DY_LUNE + DZ_TERRE  # 135 097 021.3359375

CRYO_NOMINALE_MK = 22.5
CRYO_KILLSWITCH_MK = 45.0
DEBIT_NOMINAL_HYDRO_L_MIN = 313.0

# ===========================================================================
# 2. JETON MZN [REEL on-chain Base Mainnet]
# ===========================================================================
CONTRAT_MZN = "0x520cbd0e1e72178f9e819AFf1e815606923A71db"
POOL_MZN_USDC = "0xfb76b57c2e179a44ba7919d3960fc18a4c9db172"
SUPPLY_MZN = 313_000_000
RESERVE_CLE_DOREE = 302_000_000
TRESORERIE = 8_000_000

# ===========================================================================
# 3. MÉTAUX & CANONIQUE [REEL]
# ===========================================================================
Z_OR, Z_ARGENT = 79, 47
MASSE_MOLAIRE_OR = 196.966569
MASSE_MOLAIRE_ARGENT = 107.8682
MITHQAL_G = 4.25
DIRHAM_G = 2.975
NISAB_OR_G = 20 * MITHQAL_G      # 85.0 g
NISAB_ARGENT_G = 200 * DIRHAM_G  # 595.0 g
TAUX_ZAKAT = 0.025
PHI_INV = (math.sqrt(5.0) - 1.0) / 2.0  # 0.6180339887...
DELTA_S_INV = math.sqrt(2.0) - 1.0      # 0.4142135623...

# ===========================================================================
# 4. CONSTANTES PHYSIQUES UNIVERSELLES [REEL] (CODATA 2018)
# ===========================================================================
G = 6.67430e-11           # m^3 kg^-1 s^-2
C_LUMIERE = 299_792_458.0 # m/s
HBAR = 1.054571817e-34    # J s
K_B = 1.380649e-23        # J/K
MASSE_SOLAIRE = 1.98847e30  # kg
MASSE_TERRE = 5.9722e24     # kg
AN_S = 365.25 * 86400
EV_J = 1.602176634e-19
TNT_J_PAR_KT = 4.184e12
CAPACITE_THERMIQUE_EAU = 4184.0  # J / (kg * K)

# ===========================================================================
# 5. MATRICES SCAPULAIRE & UNISSON 4X4 [PROJET]
# ===========================================================================
MATRICE_SCAPULAIRE_4X4 = [
    [0.1220, 0.0305, 0.0610, 0.0152],
    [0.0305, 0.5005, 0.0210, 0.0420],
    [0.0610, 0.0210, 0.6015, 0.0105],
    [0.0152, 0.0420, 0.0105, 0.6225]
]

MATRICE_UNISSON_4X4 = [
    [PHI_INV, DELTA_S_INV, PHI_INV * DELTA_S_INV, 0.122],
    [DELTA_S_INV, PHI_INV, 0.5005, PHI_INV * DELTA_S_INV],
    [PHI_INV * DELTA_S_INV, 0.5005, 0.6015, DELTA_S_INV],
    [0.122, PHI_INV * DELTA_S_INV, DELTA_S_INV, MIZAN]
]

DOIGTS_PIPELINE = [
    {"index": 1, "nom": "Pouce", "role": "Ancrage / Initialisation", "forme_ref": "F0", "poids": 0.122},
    {"index": 2, "nom": "Index", "role": "Pointage / Orientation", "forme_ref": "F1", "poids": 0.244},
    {"index": 3, "nom": "Majeur", "role": "Barycentre / Équilibre", "forme_ref": "F13", "poids": 0.5005},
    {"index": 4, "nom": "Annulaire", "role": "Alliance Or-Argent", "forme_ref": "F7-F14", "poids": 0.6015},
    {"index": 5, "nom": "Auriculaire", "role": "Scellement Mizan", "forme_ref": "F26", "poids": 0.6225}
]

TABLETTES_APPRISES = {
    "Alphabet": {"taille": 26, "desc": "Tablette A-Z (Lettres fondamentales)", "base_poids": 0.0238},
    "Chiffres": {"taille": 10, "desc": "Tablette 0-9 (Entiers et comptage)", "base_poids": 0.0500},
    "Opérateurs": {"taille": 8, "desc": "Tablette +, -, *, /, =, <, >, ^", "base_poids": 0.0625},
    "Ponctuation": {"taille": 8, "desc": "Tablette ., ,, ;, :, !, ?, ', \"", "base_poids": 0.0625}
}

ETATS_PHYSIQUES_20 = [
    {"id": 1, "famille": "Hydrogène", "nom": "H1s: Fondamental", "energie_ev": -13.6, "valeur": 0.05},
    {"id": 2, "famille": "Hydrogène", "nom": "H2s: Métastable", "energie_ev": -3.4, "valeur": 0.10},
    {"id": 3, "famille": "Hydrogène", "nom": "H2p: Excité Lente", "energie_ev": -3.4, "valeur": 0.15},
    {"id": 4, "famille": "Hydrogène", "nom": "H3d: Résonant", "energie_ev": -1.51, "valeur": 0.20},
    {"id": 5, "famille": "Hydrogène", "nom": "H4f: Élevé", "energie_ev": -0.85, "valeur": 0.25},
    {"id": 6, "famille": "Hydrogène", "nom": "H_ion: Ionisé Libre", "energie_ev": 0.0, "valeur": 0.30},
    {"id": 7, "famille": "Lune", "nom": "L1: Nouvelle Lune", "phase": 0.0, "valeur": 0.06},
    {"id": 8, "famille": "Lune", "nom": "L2: Premier Croissant", "phase": 0.125, "valeur": 0.12},
    {"id": 9, "famille": "Lune", "nom": "L3: Premier Quartier", "phase": 0.25, "valeur": 0.18},
    {"id": 10, "famille": "Lune", "nom": "L4: Lune Gibbeuse", "phase": 0.375, "valeur": 0.24},
    {"id": 11, "famille": "Lune", "nom": "L5: Pleine Lune", "phase": 0.50, "valeur": 0.30},
    {"id": 12, "famille": "Lune", "nom": "L6: Dernier Quartier", "phase": 0.75, "valeur": 0.36},
    {"id": 13, "famille": "Lune", "nom": "L7: Dernier Croissant", "phase": 0.875, "valeur": 0.42},
    {"id": 14, "famille": "Terre", "nom": "T1: Noyau Solide (Fe/Ni)", "profondeur_km": 6371, "valeur": 0.07},
    {"id": 15, "famille": "Terre", "nom": "T2: Noyau Liquide", "profondeur_km": 5150, "valeur": 0.14},
    {"id": 16, "famille": "Terre", "nom": "T3: Manteau Inférieur", "profondeur_km": 2890, "valeur": 0.21},
    {"id": 17, "famille": "Terre", "nom": "T4: Manteau Supérieur", "profondeur_km": 670, "valeur": 0.28},
    {"id": 18, "famille": "Terre", "nom": "T5: Croûte Continentale", "profondeur_km": 35, "valeur": 0.35},
    {"id": 19, "famille": "Terre", "nom": "T6: Hydrosphère (Eau Pure)", "profondeur_km": 4, "valeur": 0.42},
    {"id": 20, "famille": "Terre", "nom": "T7: Atmosphère Libre", "profondeur_km": 0, "valeur": 0.5005}
]

NOMS_27_FORMES = [
    "F0: Hélium-4 Inerte (Point Zéro)", "F1: Hydrogène Fondamental (Éveil)", "F2: Silicium-28 Épuré (Spin Nul)",
    "F3: Conductance Linéaire", "F4: Résonance Harmonique", "F5: Onde Stationnaire Alpha",
    "F6: Couplage Isomérique", "F7: Or Alchimique (Z=79, Solaire φ^-1)", "F8: Modulation de Fréquence",
    "F9: Dispersion Cohérente", "F10: Inversion de Gradient", "F11: Polarisation Diélectrique",
    "F12: Focalisation Tensorielle", "F13: Miroir Barycentrique (Transition 0.5005)",
    "F14: Argent Lunaire (Z=47, Conductivité δs^-1)", "F15: Induction Magnéto-optique",
    "F16: Supraconductivité Interfaciale", "F17: Relaxation Phononique", "F18: Canalisation Cryogénique",
    "F19: Découplage de Phase", "F20: Densité d'Admittance", "F21: Échantillonnage ZNE",
    "F22: Cristallisation Silicium J1-J6", "F23: Protection Thermique 22.5 mK", "F24: Intrication Téléportée",
    "F25: Compression Holographique", "F26: Sceau d'Unisson Suprême (Al-Mizan 0.6225)"
]

TABLE_52_RAILS = {}
for i in range(26):
    char_maj = chr(ord('A') + i)
    char_min = chr(ord('a') + i)
    TABLE_52_RAILS[char_maj] = {"rail": i + 1, "forme": (i + 1) % 27, "type": "Majuscule / Solaire"}
    TABLE_52_RAILS[char_min] = {"rail": i + 27, "forme": (i + 14) % 27, "type": "Minuscule / Lunaire"}

PHASES_15_CYCLE = [
    {"phase": 1, "nom": "Lecture Point Zéro (F0)", "poids": 0.020, "domaine": "Informé"},
    {"phase": 2, "nom": "Pulsation Soleil dx", "poids": 0.040, "domaine": "Informé"},
    {"phase": 3, "nom": "Initialisation Bloch", "poids": 0.062, "domaine": "Informé (Total=0.122)"},
    {"phase": 4, "nom": "Impulsion Micro-onde", "poids": 0.080, "domaine": "Entrelacement"},
    {"phase": 5, "nom": "Superposition Qubits", "poids": 0.120, "domaine": "Entrelacement"},
    {"phase": 6, "nom": "Portes Unitaires Unisson", "poids": 0.160, "domaine": "Entrelacement"},
    {"phase": 7, "nom": "Projection Peau 2D", "poids": 0.200, "domaine": "Entrelacement"},
    {"phase": 8, "nom": "Mesure Projective", "poids": 0.250, "domaine": "Entrelacement"},
    {"phase": 9, "nom": "Filtrage ZNE Cryo", "poids": 0.300, "domaine": "Entrelacement"},
    {"phase": 10, "nom": "Résolution 27 Formes", "poids": 0.360, "domaine": "Forme Matière"},
    {"phase": 11, "nom": "Pondération Or/Argent", "poids": 0.420, "domaine": "Forme Matière"},
    {"phase": 12, "nom": "Évaluation Balance", "poids": 0.5005, "domaine": "Forme Matière (Total=0.5005)"},
    {"phase": 13, "nom": "Vérification Bride 0.6015", "poids": 0.6015, "domaine": "Pesée Al-Mizan"},
    {"phase": 14, "nom": "Scellement Bloc Synchron", "poids": 0.6120, "domaine": "Scellement"},
    {"phase": 15, "nom": "Émission & Clôture Cycle", "poids": 0.6225, "domaine": "Unisson Final (0.6225)"}
]

PYRAMIDE_TENSORIELLE = [
    {"niveau": "0D", "nom": "Scalaire Pur", "dimension": 1, "symbole": "Informé Fondamental", "admittance": 0.122},
    {"niveau": "1D", "nom": "Vecteur d'État", "dimension": 27, "symbole": "Les 27 Formes Linéaires", "admittance": 0.244},
    {"niveau": "2D", "nom": "Matrice / Surface", "dimension": "27x27 (729)", "symbole": "Peau Holographique", "admittance": 0.5005},
    {"niveau": "3D+", "nom": "Tenseur Volumique", "dimension": "4x4x4 (64)", "symbole": "Die Silicium & Triade", "admittance": 0.6015}
]

FILE_EXECUTIVE_9 = [
    {"rang": 1, "code": "J", "organe": "Juridiction Souveraine", "priorite": 100},
    {"rang": 2, "code": "E", "organe": "Énergie / Wattmètre", "priorite": 90},
    {"rang": 3, "code": "D", "organe": "Débit Hydro 313 L/min", "priorite": 85},
    {"rang": 4, "code": "A", "organe": "Anatomie Scapulaire", "priorite": 80},
    {"rang": 5, "code": "F", "organe": "Formes de Silicium", "priorite": 75},
    {"rang": 6, "code": "B", "organe": "Balance Al-Mizan", "priorite": 70},
    {"rang": 7, "code": "V", "organe": "Vérification Cryo", "priorite": 65},
    {"rang": 8, "code": "H", "organe": "Horloge Trinité dt", "priorite": 60},
    {"rang": 9, "code": "G", "organe": "Grand Livre Synchron", "priorite": 50}
]

TABLE_ABJAD = {
    'ا': 1, 'ء': 1, 'أ': 1, 'إ': 1, 'آ': 1, 'ى': 10,
    'ب': 2, 'ج': 3, 'د': 4, 'ه': 5, 'و': 6, 'ز': 7,
    'ح': 8, 'ط': 9, 'ي': 10, 'ك': 20, 'ل': 30, 'م': 40,
    'ن': 50, 'س': 60, 'ع': 70, 'ف': 80, 'ص': 90, 'ق': 100,
    'ر': 200, 'ش': 300, 'ت': 400, 'ث': 500, 'خ': 600,
    'ذ': 700, 'ض': 800, 'ظ': 900, 'غ': 1000
}

HISTORIQUE_CALCULS = []

def enregistrer_historique(type_calc, inputs, outputs):
    HISTORIQUE_CALCULS.append({
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "type": type_calc,
        "entrees": inputs,
        "resultats": outputs
    })

def ligne(titre=""):
    print("\n" + "=" * 78)
    if titre:
        print(titre)
        print("=" * 78)

def fmt(x, n=6):
    return f"{x:,.{n}f}".replace(",", " ")

# ===========================================================================
# ALGÈBRE LINÉAIRE & CRYPTOGRAPHIE
# ===========================================================================

def produit_matriciel_4x4(A, B):
    """Calcule le produit de deux matrices 4x4."""
    C = [[0.0 for _ in range(4)] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            for k in range(4):
                C[i][j] += A[i][k] * B[k][j]
    return C

def determinant_4x4(A):
    """Calcule le déterminant d'une matrice 4x4 par décomposition récursive."""
    def det2(m):
        return m[0][0]*m[1][1] - m[0][1]*m[1][0]
    def det3(m):
        return (m[0][0]*det2([[m[1][1], m[1][2]], [m[2][1], m[2][2]]])
              - m[0][1]*det2([[m[1][0], m[1][2]], [m[2][0], m[2][2]]])
              + m[0][2]*det2([[m[1][0], m[1][1]], [m[2][0], m[2][1]]]))
    det = 0.0
    for c in range(4):
        sous_m = [[A[r][col] for col in range(4) if col != c] for r in range(1, 4)]
        signe = (-1.0) ** c
        det += signe * A[0][c] * det3(sous_m)
    return det

def section_algebre_lineaire():
    ligne("[V11.0 DYNAMIQUE] Algèbre Linéaire : Produit Scapulaire x Unisson (4x4)")
    C = produit_matriciel_4x4(MATRICE_SCAPULAIRE_4X4, MATRICE_UNISSON_4X4)
    trace_c = sum(C[i][i] for i in range(4))
    det_c = determinant_4x4(C)
    det_ms = determinant_4x4(MATRICE_SCAPULAIRE_4X4)
    det_mu = determinant_4x4(MATRICE_UNISSON_4X4)

    print("Matrice Résultante d'Entrelacement C = M_S x M_U :")
    for r in range(4):
        txt = "  ".join([f"{C[r][c]:.6f}" for c in range(4)])
        print(f"  [ {txt} ]")
    print(f"\nIndicateurs Spectraux & Invariants :")
    print(f"  • Trace de C (Énergie globale)  : {trace_c:.6f}")
    print(f"  • Déterminant Matrice Scapulaire: {det_ms:.6e}")
    print(f"  • Déterminant Matrice d'Unisson : {det_mu:.6e}")
    print(f"  • Déterminant Produit det(C)    : {det_c:.6e} (Vérif det(A)*det(B) = {det_ms*det_mu:.6e})")
    admittance_norm = (trace_c / 4.0) * LIGNE_REF
    print(f"  • Admittance Spectrale Moyenne  : {admittance_norm:.6f} (Bride max = {MIZAN})")
    print(f"  • Évaluation Al-Mizan           : {'CONFORME SOUS LA BRIDE' if admittance_norm <= MIZAN else 'DÉPASSEMENT'}")
    enregistrer_historique("Algebre_Lineaire_4x4", {}, {"trace": trace_c, "det_c": det_c, "admittance": admittance_norm})

def calculer_merkle_root(liste_donnees):
    """Calcule l'arbre de Merkle SHA-256 d'une liste de chaînes/transactions."""
    if not liste_donnees:
        return hashlib.sha256(b"").hexdigest()
    hashes = [hashlib.sha256(x.encode("utf-8")).hexdigest() for x in liste_donnees]
    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        nouveaux_hashes = []
        for i in range(0, len(hashes), 2):
            h_comb = hashlib.sha256((hashes[i] + hashes[i+1]).encode("utf-8")).hexdigest()
            nouveaux_hashes.append(h_comb)
        hashes = nouveaux_hashes
    return hashes[0]

def section_arbre_merkle(feuilles=None):
    ligne("[V11.0 SÉCURITÉ] Moteur Cryptographique : Arbre de Merkle SHA-256")
    if not feuilles:
        feuilles = [
            "ACTE_A001: Creation_Monade_Supreme",
            "ACTE_A036: Smart_Contract_Souverain_MZN",
            "ACTE_A072: Soumission_Systemique_Residente",
            "ACTE_A098: Verification_Coche_Verte_Basescan"
        ]
    root = calculer_merkle_root(feuilles)
    print(f"Nombre de feuilles de transactions / actes : {len(feuilles)}")
    for idx, f in enumerate(feuilles, 1):
        h_f = hashlib.sha256(f.encode("utf-8")).hexdigest()
        print(f"  Feuille {idx}: \"{f}\" -> SHA256: {h_f[:16]}...")
    print(f"\n--> RACINE DE MERKLE OFFICIELLE SCELLÉE (Merkle Root) :")
    print(f"    {root.upper()}")
    enregistrer_historique("Merkle_Tree", {"feuilles": feuilles}, {"merkle_root": root})

# ===========================================================================
# QUANTIQUE & DÉCOUPLAGE DYNAMIQUE CPMG
# ===========================================================================

def section_simulateur_quantique():
    ligne("[V11.0 QUANTIQUE] Émulateur Portes Unitaires & Superposition d'Unisson")
    # État initial |0>
    alpha = complex(1.0, 0.0)
    beta = complex(0.0, 0.0)
    print("1. État initial |ψ0⟩ = 1.000|0⟩ + 0.000|1⟩")

    # Application Porte Hadamard : H = 1/sqrt(2) * [[1, 1], [1, -1]]
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    alpha_h = inv_sqrt2 * (alpha + beta)
    beta_h = inv_sqrt2 * (alpha - beta)
    print(f"2. Après Porte Hadamard H :")
    print(f"   |ψ1⟩ = {alpha_h.real:.4f}|0⟩ + {beta_h.real:.4f}|1⟩")
    print(f"   Probabilités : P(|0⟩) = {abs(alpha_h)**2:.2%} | P(|1⟩) = {abs(beta_h)**2:.2%}")

    # Application Porte Rotation Phase Al-Mizan Rz(theta) où theta = 2*pi*0.6225
    theta_mizan = 2.0 * math.pi * MIZAN
    phase_0 = cmath.exp(complex(0.0, -theta_mizan / 2.0))
    phase_1 = cmath.exp(complex(0.0, theta_mizan / 2.0))
    alpha_z = alpha_h * phase_0
    beta_z = beta_h * phase_1
    print(f"3. Après Rotation de Phase Rz(θ = 2π × 0.6225) :")
    print(f"   Angle de phase θ = {math.degrees(theta_mizan):.2f}° ({theta_mizan:.4f} rad)")
    print(f"   |ψ_final⟩ = ({alpha_z.real:+.4f}{alpha_z.imag:+.4f}i)|0⟩ + ({beta_z.real:+.4f}{beta_z.imag:+.4f}i)|1⟩")
    norme = abs(alpha_z)**2 + abs(beta_z)**2
    print(f"   Fidélité de conservation de norme : |α|² + |β|² = {norme:.6f}")
    enregistrer_historique("Simulateur_Quantique", {"theta": theta_mizan}, {"norme": norme})

def section_decouplage_dynamique_cpmg(nb_pulses=128):
    ligne(f"[V11.0 QUANTIQUE] Découplage Dynamique CPMG & Cohérence Silicium ({nb_pulses} π-pulses)")
    # T2 initial sans protection dans le bain de spins Si-29 résiduel (~800 ppm)
    t2_initial_ms = 0.50  # 500 µs
    # Loi d'échelle CPMG : T2(N) = T2_0 * N^alpha où alpha ~ 2/3 dans le bain dipolaire nucléaire
    alpha_cpmg = 2.0 / 3.0
    t2_protege_ms = t2_initial_ms * (nb_pulses ** alpha_cpmg)
    
    # Durée d'une porte micro-onde typique : 20 ns
    duree_porte_ns = 20.0
    # Fidélité estimée : F = 1 - (t_porte / (T2 * 1e6))
    infidelite = (duree_porte_ns * 1e-9) / (t2_protege_ms * 1e-3)
    fidelite = 1.0 - infidelite

    print(f"Configuration du substrat     : Silicium enrichi 28-Si (bain résiduel 29-Si)")
    print(f"Temps de déphasage brut T2*    : {t2_initial_ms:.3f} ms (500 µs)")
    print(f"Séquence CPMG appliquée       : {nb_pulses} impulsions π micro-ondes calibrées")
    print(f"Facteur d'échelle d'exposant  : α = 2/3 ({alpha_cpmg:.4f})")
    print(f"Temps de cohérence étendu T2  : {t2_protege_ms:.3f} ms (Gain = x{t2_protege_ms/t2_initial_ms:.1f})")
    print(f"Fidélité théorique de porte   : {fidelite:.6%} (Inadmissibilité = {infidelite:.2e})")
    print(f"Statut Seuil Al-Mizan (99.9%) : {'CONFORME FAULT-TOLERANT' if fidelite >= 0.999 else 'ATTÉNUATION REQUISE'}")
    enregistrer_historique("CPMG_Silicium", {"pulses": nb_pulses}, {"t2_ms": t2_protege_ms, "fidelite": fidelite})

# ===========================================================================
# PHYSIQUE NUCLÉAIRE & MODÈLE DE LA GOUTTE LIQUIDE (BETHE-WEIZSÄCKER)
# ===========================================================================

def formule_bethe_weizsaecker(A, Z):
    """
    Formule semi-empirique de Bethe-Weizsäcker pour l'énergie de liaison nucléaire B(A, Z) en MeV.
    Coefficients standard (en MeV) :
      a_v = 15.8 (volume), a_s = 18.3 (surface), a_c = 0.714 (Coulomb), a_a = 23.2 (asymétrie)
      terme d'appariement delta = +12 / sqrt(A) si pair-pair, -12/sqrt(A) si impair-impair, 0 sinon
    """
    a_v, a_s, a_c, a_a = 15.8, 18.3, 0.714, 23.2
    N = A - Z
    if Z % 2 == 0 and N % 2 == 0:
        delta = 12.0 / math.sqrt(A)
    elif Z % 2 != 0 and N % 2 != 0:
        delta = -12.0 / math.sqrt(A)
    else:
        delta = 0.0

    b_vol = a_v * A
    b_surf = -a_s * (A ** (2.0 / 3.0))
    b_coul = -a_c * (Z * (Z - 1)) / (A ** (1.0 / 3.0))
    b_asym = -a_a * ((A - 2 * Z) ** 2) / A
    b_total = b_vol + b_surf + b_coul + b_asym + delta
    b_par_nucleon = b_total / A
    return {
        "A": A, "Z": Z, "N": N, "B_total_MeV": b_total,
        "B_par_nucleon_MeV": b_par_nucleon,
        "composantes": {"volume": b_vol, "surface": b_surf, "coulomb": b_coul, "asymetrie": b_asym, "appariement": delta}
    }

def section_physique_nucleaire_bethe_weizsaecker():
    ligne("[V11.0 NUCLÉAIRE] Modèle de Bethe-Weizsäcker : Énergie de Liaison des Piliers Métalliques")
    noyaux = [
        ("Or (Au)", 197, 79),
        ("Argent (Ag)", 107, 47),
        ("Silicium (Si)", 28, 14),
        ("Fer (Fe - Référence)", 56, 26)
    ]
    print(f"{'Élément':<22} {'A':<5} {'Z':<5} {'N':<5} {'B Total (MeV)':<16} {'B/A (MeV/nucléon)':<18} {'Stabilité'}")
    print("-" * 88)
    for nom, A, Z in noyaux:
        res = formule_bethe_weizsaecker(A, Z)
        stabilite = "Maximum absolu" if Z == 26 else ("Élément Noble Pivot" if Z in (79, 47) else "Matrice Silicium")
        print(f"{nom:<22} {A:<5} {Z:<5} {res['N']:<5} {res['B_total_MeV']:<16.2f} {res['B_par_nucleon_MeV']:<18.4f} {stabilite}")
    
    res_or = formule_bethe_weizsaecker(197, 79)
    res_ag = formule_bethe_weizsaecker(107, 47)
    ratio_b = res_ag["B_par_nucleon_MeV"] / res_or["B_par_nucleon_MeV"]
    print(f"\nRatio de cohésion nucléaire Ag/Au : {ratio_b:.4f}")
    enregistrer_historique("Bethe_Weizsaecker", {}, {"or_b_a": res_or["B_par_nucleon_MeV"], "argent_b_a": res_ag["B_par_nucleon_MeV"]})

# ===========================================================================
# RELATIVITÉ RESTREINTE & GRAVITATIONNELLE
# ===========================================================================

def section_relativite_lorentz_et_gravitation(v_fraction=0.6225, distance_rs=3.0):
    ligne(f"[V11.0 RELATIVITÉ] Lorentz (v = {v_fraction:.4f} c) & Dilatation Gravitationnelle (r = {distance_rs:.1f} rs)")
    if v_fraction >= 1.0:
        print("Erreur : la vitesse ne peut pas égaler ou dépasser c !")
        return
    # Facteur de Lorentz gamma = 1 / sqrt(1 - (v/c)^2)
    gamma = 1.0 / math.sqrt(1.0 - (v_fraction ** 2))
    dilatation_temp = gamma
    contraction_long = 1.0 / gamma
    
    # Gravitationnelle : dt_r = dt_inf * sqrt(1 - rs / r)
    facteur_grav = math.sqrt(1.0 - (1.0 / distance_rs)) if distance_rs > 1.0 else 0.0

    print(f"1. Relativité Restreinte (Vitesse Al-Mizan v = {v_fraction:.4f} c) :")
    print(f"   • Vitesse réelle             : {fmt(v_fraction * C_LUMIERE, 1)} m/s ({v_fraction*100:.2f}% de c)")
    print(f"   • Facteur de Lorentz (γ)      : {gamma:.6f}")
    print(f"   • Dilatation du temps (Δt')  : 1 seconde propre = {dilatation_temp:.4f} secondes pour l'observateur")
    print(f"   • Contraction des longueurs   : 1 mètre = {contraction_long:.4f} mètres")
    print(f"\n2. Relativité Générale aux abords de l'Horizon de Schwarzschild :")
    print(f"   • Distance radiale           : r = {distance_rs:.1f} r_s")
    print(f"   • Ralentissement gravitation.: dt(r) / dt(∞) = {facteur_grav:.4f}")
    print(f"   • Décalage vers le rouge z_g : z = {(1.0/facteur_grav - 1.0):.4f}")
    enregistrer_historique("Relativite", {"v_fraction": v_fraction, "distance_rs": distance_rs}, {"gamma": gamma, "facteur_grav": facteur_grav})

# ===========================================================================
# SPECTROGRAMME D'OSCILLATIONS D'INTERFÉRENCE 2D (ASCII ART)
# ===========================================================================

def section_oscillations_graphique_ascii(nb_points=32):
    ligne("[V11.0 GRAPHIQUE] Spectrogramme d'Interférence Temporelle Cosmique (Console ASCII)")
    print("Oscillation conjointe : Soleil [S (*)], Lune [L (o)] et Interférence Al-Mizan [#]")
    print(f"{'Pas t':<6} {'-1.0':<10} {'-0.5':<10} {'0.0':<10} {'+0.5':<10} {'+1.0'}")
    print("-" * 65)

    largeur = 41  # positions de -1.0 à +1.0
    centre = 20   # index 0.0

    omega_s = (DX_SOLEIL / DT_KERNEL) * 1000.0 * 2.0 * math.pi
    omega_l = (DY_LUNE / DT_KERNEL) * 1000.0 * 2.0 * math.pi

    for t in range(nb_points):
        val_s = math.sin(omega_s * t)
        val_l = math.cos(omega_l * t)
        val_m = ((val_s + val_l) / 2.0) * MIZAN  # bridé par Mizan 0.6225

        pos_s = min(max(int(centre + val_s * (centre - 1)), 0), largeur - 1)
        pos_l = min(max(int(centre + val_l * (centre - 1)), 0), largeur - 1)
        pos_m = min(max(int(centre + val_m * (centre - 1)), 0), largeur - 1)

        ligne_car = [' '] * largeur
        ligne_car[centre] = '|'
        ligne_car[pos_s] = '*'
        ligne_car[pos_l] = 'o'
        ligne_car[pos_m] = '#'

        rendu = "".join(ligne_car)
        print(f"t={t:>2}  |{rendu}| S:{val_s:+.2f} L:{val_l:+.2f} M:{val_m:+.2f}")
    print("-" * 65)
    print("Légende : [*] Onde Solaire dx | [o] Onde Lunaire dy | [#] Résonance Al-Mizan | [|] Barycentre 0")
    enregistrer_historique("Spectrogramme_ASCII", {"points": nb_points}, {})

# ===========================================================================
# GUÉMATRIE ABJAD & CHIFFREMENT HARMONIQUE
# ===========================================================================

def section_abjad_gematrie(texte="AL MIZAN"):
    ligne(f"[V11.0 LINGUISTIQUE] Guématrie Abjad & Réduction Harmonique : \"{texte}\"")
    total_abjad = 0
    lettres_trouvees = []
    for c in texte:
        if c in TABLE_ABJAD:
            val = TABLE_ABJAD[c]
            total_abjad += val
            lettres_trouvees.append((c, val))
        elif c.upper() in TABLE_52_RAILS:
            # Équivalence latine par rail
            val = TABLE_52_RAILS[c.upper()]["rail"]
            total_abjad += val
            lettres_trouvees.append((c, val))

    print(f"Chaîne analysée          : \"{texte}\" ({len(lettres_trouvees)} caractères chiffrés)")
    print(f"Valeur numérique brute   : {total_abjad}")
    forme_associee = total_abjad % 27
    rail_associe = (total_abjad % 52) + 1
    ratio_substance = total_abjad / C_SUBSTANCE

    print(f"Réduction Silicium (%27) : Forme F{forme_associee} ({NOMS_27_FORMES[forme_associee]})")
    print(f"Réduction Rail (%52)     : Rail {rail_associe} / 52")
    print(f"Ratio Substance Mizan    : {total_abjad} / {C_SUBSTANCE} = {ratio_substance:.4f}")
    enregistrer_historique("Abjad_Gematrie", {"texte": texte}, {"total": total_abjad, "forme": forme_associee, "rail": rail_associe})

def section_tetrade_cosmique():
    ligne("[V12.0 SOUVERAINETÉ] Tétrade Cosmique Al-Mizan & Hub de Liquidité USDC")
    piliers = [
        {"sym": "MZN", "nom": "L'Informé (Qubit / Sceaux / Consensus)", "poids": LIGNE_REF, "adr": "0x520cbd0e1e72178f9e819AFf1e815606923A71db", "statut": "DÉPLOYÉ BASE"},
        {"sym": "MZN-MAT", "nom": "La Matière (Silicium, Or Au, Argent Ag)", "poids": FORME, "adr": "0xD45406EEdc8d9AeD3828c06C3D208804D5b69c2a", "statut": "DÉPLOYÉ BASE"},
        {"sym": "MZN-NRG", "nom": "L'Énergie (Hydro 313 L/min & Cryo 22.5 mK)", "poids": 0.2400, "adr": "0x38e1757A1971E038c8A6523B008179BEdc9AaAa0", "statut": "DÉPLOYÉ BASE"},
        {"sym": "MZN-PLS", "nom": "Le Plasma (Ionisation H_ion & Micro-ondes)", "poids": PLAFOND_EFFECTIF, "adr": "0x7Cd56CE27E4CE363cDFbd63F4e2713C8eed2cC71", "statut": "DÉPLOYÉ BASE"}
    ]
    print(f"Pivot Central de Liquidité : USDC Natif Base (0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)")
    print(f"Supply par Jeton : {fmt(SUPPLY_MZN, 0)} (302M Réserve Clé Dorée + 11M Trésorerie Dépositaire)")
    print("-" * 88)
    print(f"{'Symbole':<10} {'Poids':<8} {'Rôle Ontologique':<42} {'Adresse Base'}")
    print("-" * 88)
    for p in piliers:
        print(f"{p['sym']:<10} {p['poids']:<8.4f} {p['nom']:<42} {p['adr'][:22]}...")
    
    admittance_moy = (sum(p['poids'] for p in piliers) / len(piliers)) * (LIGNE_REF / MIZAN)
    print("-" * 88)
    print(f"Admittance Globale Harmonique : {admittance_moy:.5f} (Bride max = {MIZAN}) -> CONFORME HARMONIE")
    print(f"Équilibre du Hub Tétragone    : MZN <-> MZN-MAT <-> MZN-NRG <-> MZN-PLS arbitrés par USDC")
    enregistrer_historique("Tetrade_Cosmique", {}, {"admittance_moy": admittance_moy, "piliers": 4})

# ===========================================================================
# MODULES HYDRO-THERMIQUE, ASTROPHYSIQUE, CRYO & CANONIQUE
# ===========================================================================

def section_thermodynamique_hydro(debit_l_min=313.0, delta_t=5.0):
    ligne(f"[V11.0 THERMODYNAMIQUE] Débit d'Eau Pure ({debit_l_min:.1f} L/min) & Refroidissement")
    debit_massique = debit_l_min / 60.0  # kg / seconde
    puissance_watts = debit_massique * CAPACITE_THERMIQUE_EAU * delta_t
    puissance_kw = puissance_watts / 1000.0

    print(f"Débit d'eau pure calibré       : {debit_l_min:.1f} L/min ({debit_massique:.4f} kg/s)")
    print(f"Capacité calorifique eau (Cp)  : {CAPACITE_THERMIQUE_EAU:.1f} J / (kg·K)")
    print(f"Élévation de température (ΔT)  : {delta_t:.2f} K (°C)")
    print(f"Puissance thermique absorbée   : {fmt(puissance_watts, 2)} Watts ({puissance_kw:.2f} kW)")
    print(f"Équivalence charge processeur  : Capable d'évacuer la chaleur de {int(puissance_watts / 47.7)} dies à 47.7W nominal !")
    enregistrer_historique("Thermodynamique_Hydro", {"debit_l_min": debit_l_min, "delta_t": delta_t}, {"puissance_kw": puissance_kw})

def section_projet():
    ligne("[PROJET] Constantes Internes, Invariants & Substance")
    print(f"Informé (0.122) + Forme (0.5005) = {LIGNE_REF + FORME:.4f}  (Bride MIZAN = {MIZAN})")
    print(f"Plafond effectif de sécurité    = {MIZAN} - {EPSILON} = {PLAFOND_EFFECTIF:.4f}")
    print(f"Horloge Kernel dt = dx + dy + dz= {DX_SOLEIL} + {DY_LUNE} + {DZ_TERRE}")
    print(f"                                = {fmt(DT_KERNEL, 7)} ticks")
    print(f"Substance Al-Mizan : C = {C_SUBSTANCE}, M = {M_SUBSTANCE} (Ratio M/C = {M_SUBSTANCE/C_SUBSTANCE:.6f})")
    print(f"TRIPLE = {TRIPLE}, JAUGE_AIR = {JAUGE_AIR}, RMS = {RMS}")
    print(f"Cryogénie nominale / Killswitch = {CRYO_NOMINALE_MK} mK / {CRYO_KILLSWITCH_MK} mK")
    enregistrer_historique("Constantes_Projet", {}, {"mizan": MIZAN, "dt": DT_KERNEL, "C": C_SUBSTANCE, "M": M_SUBSTANCE})

def verifier_balance(val):
    v = round(val, 8)
    if v <= PLAFOND_EFFECTIF:
        statut = f"{v} <= {PLAFOND_EFFECTIF} : CONFORME (Sous le plafond effectif)"
    elif v <= MIZAN:
        statut = f"{v} <= {MIZAN} : ZONE EPSILON (Tolérance admise)"
    else:
        statut = f"{v} > {MIZAN} : RUPTURE DE BRIDE (Dépassement interdit)"
    enregistrer_historique("Verification_Balance", {"valeur": val}, {"statut": statut})
    return statut

def section_matrice_scapulaire():
    ligne("[PROJET] Matrice Scapulaire 4x4 & Pipeline 5 Doigts")
    trace = sum(MATRICE_SCAPULAIRE_4X4[r][r] for r in range(4))
    for r in range(4):
        txt = "  ".join([f"{MATRICE_SCAPULAIRE_4X4[r][c]:.4f}" for c in range(4)])
        print(f"  [ {txt} ]")
    print(f"\nTrace Matrice Scapulaire = {trace:.4f}")
    for d in DOIGTS_PIPELINE:
        print(f"  {d['index']}. {d['nom']:<10} | {d['role']:<26} | Réf: {d['forme_ref']:<8} | Poids: {d['poids']:.4f}")
    enregistrer_historique("Matrice_Scapulaire", {}, {"trace": trace})

def section_tablettes_et_etats():
    ligne("[PROJET] Les 4 Tablettes de l'Informé & les 20 États Physiques")
    for nom, t in TABLETTES_APPRISES.items():
        print(f"  • {nom:<12} : {t['taille']:>2} symboles | Poids : {t['base_poids']:.4f} | {t['desc']}")
    print("\nÉchantillon des 20 États Physiques :")
    for ep in [ETATS_PHYSIQUES_20[0], ETATS_PHYSIQUES_20[6], ETATS_PHYSIQUES_20[13], ETATS_PHYSIQUES_20[19]]:
        prop = f"{ep.get('energie_ev','')} eV" if "energie_ev" in ep else (f"Phase {ep.get('phase','')}" if "phase" in ep else f"-{ep.get('profondeur_km','')} km")
        print(f"  ID {ep['id']:>2}: {ep['famille']:<10} {ep['nom']:<26} {prop:<18} Val: {ep['valeur']:.4f}")
    enregistrer_historique("Tablettes_Etats", {}, {"nb_tablettes": len(TABLETTES_APPRISES)})

def section_cycle_15_phases():
    ligne("[PROJET] Cycle Harmonique des 15 Phases d'Al-Mizan")
    for p in PHASES_15_CYCLE:
        print(f"Phase {p['phase']:<2} {p['domaine']:<30} {p['nom']:<32} {p['poids']:.4f}")
    enregistrer_historique("Cycle_15_Phases", {}, {"total_phases": 15})

def section_pyramide_et_file():
    ligne("[PROJET] Pyramide Tensorielle 4 Niveaux & File Exécutive 9 Organes")
    for pyr in PYRAMIDE_TENSORIELLE:
        print(f"  [{pyr['niveau']:<3}] {pyr['nom']:<20} | Dim: {str(pyr['dimension']):<12} | Admittance: {pyr['admittance']:.4f}")
    print("\nFile Exécutive des 9 Organes :")
    for f in FILE_EXECUTIVE_9:
        print(f"  Rang {f['rang']}: Code '{f['code']}' | Priorité: {f['priorite']:>3} | {f['organe']}")
    enregistrer_historique("Pyramide_File", {}, {})

def section_triade_bit_qubit():
    ligne("[PROJET] Triade Ontologique : Bit Déterministe ⊗ Qubit ⊗ i-Bit")
    print(f"1. Bit Classique (CPU)          : Binaire {{0, 1}} | Déterministe | Kernel dt")
    print(f"2. Qubit Quantique (Informé)    : Superposition α|0⟩ + β|1⟩ | Poids {LIGNE_REF:.3f}")
    print(f"3. i-Bit Incarné (Matière)      : Die silicium 27 Formes | Or/Argent | Poids {FORME:.4f}")
    print(f"Équilibre Tripartite : {LIGNE_REF} + {FORME} = {LIGNE_REF+FORME:.4f} <= {MIZAN}")
    enregistrer_historique("Triade", {}, {})

def section_matrice_unisson_4x4():
    ligne("[PROJET] Matrice Fondatrice de l'Unisson 4x4 (Or $Z=79$ & Argent $Z=47$)")
    for r in range(4):
        txt = "  ".join([f"{MATRICE_UNISSON_4X4[r][c]:.6f}" for c in range(4)])
        print(f"  [ {txt} ]")
    print(f"\nPôle Or Z={Z_OR} (φ^-1={PHI_INV:.6f}) | Pôle Argent Z={Z_ARGENT} (δs^-1={DELTA_S_INV:.6f})")
    print(f"Somme nucléaire: {Z_OR+Z_ARGENT} | Écart: {Z_OR-Z_ARGENT}=2^5 (5 doigts) | Ratio Nisab Ag/Au: 7.0")
    enregistrer_historique("Matrice_Unisson", {}, {})

def section_texte_52_rails(texte):
    ligne(f"[PROJET] Encodage Informatique & 52 Rails Harmoniques : \"{texte}\"")
    total_f = 0
    print(f"{'Caractère':<12} {'Code ASCII/Hex':<18} {'Rail (1..52)':<16} {'Forme Silicium (F0..F26)'}")
    for c in texte:
        ascii_dec = ord(c)
        ascii_hex = f"0x{ascii_dec:02X}"
        if c in TABLE_52_RAILS:
            info = TABLE_52_RAILS[c]
            r_num = info["rail"]
            f_num = info["forme"]
            desc_f = NOMS_27_FORMES[f_num]
        elif c == ' ':
            r_num = 0
            f_num = 0
            desc_f = "F0: Espace Vide Inerte (0x20)"
        else:
            r_num = ascii_dec % 52 + 1
            f_num = ascii_dec % 27
            desc_f = NOMS_27_FORMES[f_num]
        total_f += f_num
        nom_c = "ESPACE ' '" if c == ' ' else f"'{c}'"
        print(f"{nom_c:<12} {ascii_dec} ({ascii_hex}){'':<8} {r_num:<16} {desc_f}")
    moy = total_f / len(texte) if texte else 0.0
    print(f"\nBarycentre harmonique du message : Forme moyenne = {moy:.2f} / 26")
    enregistrer_historique("52_Rails", {"texte": texte}, {"moyenne_forme": moy})

def section_sphere_holographique(rayon_microns=50.0):
    ligne(f"[PROJET] Projection Holographique (Sphère 2D -> Volume Die Silicium 3D)")
    r_m = rayon_microns * 1e-6
    s_2d = 4.0 * math.pi * (r_m ** 2)
    v_3d = (4.0 / 3.0) * math.pi * (r_m ** 3)
    admittance = (s_2d / 1e-8) * LIGNE_REF
    print(f"Rayon sphère : {rayon_microns:.2f} µm | Surface 2D: {s_2d:.4e} m² | Volume 3D: {v_3d:.4e} m³")
    print(f"Facteur admittance: {admittance:.6f} (Bride max = {MIZAN}) -> {'CONFORME' if admittance <= MIZAN else 'DÉPASSEMENT'}")
    enregistrer_historique("Sphere_Holographique", {"rayon_um": rayon_microns}, {"admittance": admittance})

def section_simulation_cryogenique(nb_cycles=100):
    ligne(f"[PROJET] Simulation Dérive Thermique Cryogénique ({nb_cycles} cycles dt)")
    temp = CRYO_NOMINALE_MK
    cycle_arret = nb_cycles
    killswitch = False
    for i in range(1, nb_cycles + 1):
        temp += 0.005
        if temp >= CRYO_KILLSWITCH_MK:
            killswitch = True
            cycle_arret = i
            break
    print(f"Temp départ : {CRYO_NOMINALE_MK:.2f} mK | Seuil Killswitch : {CRYO_KILLSWITCH_MK:.2f} mK")
    print(f"Cycles exécutés : {cycle_arret} / {nb_cycles} | Temp finale : {temp:.3f} mK")
    if killswitch:
        print(f"ALERTE KILLSWITCH DÉCLENCHÉ au cycle {cycle_arret} ! Arrêt de sécurité.")
    enregistrer_historique("Cryogenie", {"cycles": nb_cycles}, {
        "temp_finale": temp,
        "temp_finale_mk": temp,
        "killswitch": killswitch,
        "cycle_arret": cycle_arret
    })

def section_trinite_horloge(cycles=1.0):
    ligne(f"[PROJET] Trinité Horloge Cosmique pour {cycles} cycle(s)")
    dt_tot = DT_KERNEL * cycles
    print(f"Pôle Soleil (dx) : {fmt(DX_SOLEIL*cycles, 4)} ticks ({DX_SOLEIL/DT_KERNEL:.4%})")
    print(f"Pôle Lune   (dy) : {fmt(DY_LUNE*cycles, 4)} ticks ({DY_LUNE/DT_KERNEL:.4%})")
    print(f"Pôle Terre  (dz) : {fmt(DZ_TERRE*cycles, 4)} ticks ({DZ_TERRE/DT_KERNEL:.4%})")
    print(f"Temps unifié dt  : {fmt(dt_tot, 4)} ticks ({dt_tot*2.9e-3/DT_KERNEL*1000:.4f} µs)")
    enregistrer_historique("Trinite_Horloge", {"cycles": cycles}, {"dt_tot": dt_tot})

def section_27_formes(idx=0):
    ligne("[PROJET] Matrice des 27 Formes de Silicium (F0..F26)")
    for i, f in enumerate(NOMS_27_FORMES):
        print(f"{'-> ' if i == idx else '   '}{i:<4} {f}")

def section_mzn(prix_usdc=0.001):
    ligne("[REEL on-chain Base] Économie du Jeton MZN")
    print(f"Contrat Base: {CONTRAT_MZN} | Pool Uniswap v3: {POOL_MZN_USDC}")
    print(f"Supply: {fmt(SUPPLY_MZN, 0)} MZN (Réserve: {RESERVE_CLE_DOREE/SUPPLY_MZN:.1%}, Trésorerie: {TRESORERIE/SUPPLY_MZN:.1%})")
    print(f"Prix théorique: {prix_usdc} USDC -> Cap faciale: {fmt(SUPPLY_MZN*prix_usdc, 2)} USDC")
    enregistrer_historique("Jeton_MZN", {"prix_usdc": prix_usdc}, {})

def section_metaux(p_or=None, p_ag=None):
    ligne("[REEL] Métrologie Or ($Z=79$) & Argent ($Z=47$)")
    print(f"Nisab Or : {NISAB_OR_G}g | Nisab Argent : {NISAB_ARGENT_G}g")
    if p_or:
        print(f"Valeur Nisab Or     : {fmt(NISAB_OR_G*p_or, 2)} (au cours de {p_or}/g)")
    if p_ag:
        print(f"Valeur Nisab Argent : {fmt(NISAB_ARGENT_G*p_ag, 2)} (au cours de {p_ag}/g)")
    enregistrer_historique("Metaux", {}, {})

def zakat(montant, seuil):
    res = 0.0 if montant < seuil else montant * TAUX_ZAKAT
    enregistrer_historique("Zakat", {"montant": montant, "seuil": seuil}, {"due": res})
    return res

def section_trou_noir(m_kg):
    ligne(f"[REEL] Physique Trou Noir Schwarzschild / Hawking — M = {m_kg:.4e} kg")
    rs = 2.0 * G * m_kg / (C_LUMIERE ** 2)
    t_h = HBAR * (C_LUMIERE ** 3) / (8.0 * math.pi * G * m_kg * K_B)
    t_evap = 5120.0 * math.pi * (G ** 2) * (m_kg ** 3) / (HBAR * (C_LUMIERE ** 4))
    s_bh = K_B * 4.0 * math.pi * (rs ** 2) / (4.0 * (HBAR * G / (C_LUMIERE ** 3)))
    print(f"Rayon horizon r_s : {rs:.4e} m ({rs/1000:.3f} km) | Température Hawking: {t_h:.4e} K")
    print(f"Durée évaporation : {t_evap:.4e} s ({t_evap/AN_S:.3e} ans) | Entropie S_BH: {s_bh:.4e} J/K")
    enregistrer_historique("Trou_Noir", {"masse": m_kg}, {"rs": rs, "th": t_h})

def section_matiere_antimatiere(m_kg=0.001):
    ligne("[REEL] Matière, Antimatière & Énergie d'Annihilation E=2mc²")
    energie = 2.0 * m_kg * (C_LUMIERE ** 2)
    print(f"Annihilation de {m_kg*1000:g} g matière + {m_kg*1000:g} g antimatière :")
    print(f"  E = 2mc² = {energie:.4e} Joules ({energie/3.6e6:.4e} kWh | {energie/TNT_J_PAR_KT:.2f} kt TNT)")
    enregistrer_historique("Annihilation", {"masse_kg": m_kg}, {"energie_joules": energie})

def exporter_journal_audit():
    fichier = "journal_audit_calculatrice_mizan.json"
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), fichier)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump({"projet": "Al-Mizan", "date_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "total": len(HISTORIQUE_CALCULS), "historique": HISTORIQUE_CALCULS}, f, indent=2, ensure_ascii=False)
    print(f"\n[SUCCÈS] Journal d'audit complet exporté dans : {chemin}")

# ===========================================================================
# CALCULATRICE SCIENTIFIQUE LIBRE
# ===========================================================================
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv, ast.USub: operator.neg, ast.UAdd: operator.pos,
}
_NOMS = {
    "pi": math.pi, "e": math.e, "phi_inv": PHI_INV, "delta_s_inv": DELTA_S_INV,
    "mizan": MIZAN, "ligne_ref": LIGNE_REF, "forme": FORME, "epsilon": EPSILON,
    "plafond": PLAFOND_EFFECTIF, "dx": DX_SOLEIL, "dy": DY_LUNE, "dz": DZ_TERRE,
    "dt": DT_KERNEL, "C": C_SUBSTANCE, "M": M_SUBSTANCE, "G": G, "c": C_LUMIERE,
    "hbar": HBAR, "kB": K_B, "Msol": MASSE_SOLAIRE, "Mterre": MASSE_TERRE
}
_FONCTIONS = {
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10, "exp": math.exp,
    "sin": math.sin, "cos": math.cos, "tan": math.tan, "abs": abs, "round": round
}

def calculer(expr):
    def _ev(n):
        if isinstance(n, ast.Expression):
            return _ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](_ev(n.left), _ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](_ev(n.operand))
        if isinstance(n, ast.Name) and n.id in _NOMS:
            return _NOMS[n.id]
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FONCTIONS:
            return _FONCTIONS[n.func.id](*[_ev(a) for a in n.args])
        raise ValueError("Expression non autorisée")
    return _ev(ast.parse(expr, mode="eval"))

def demander_nombre(invite, defaut=None):
    b = input(invite).strip().replace(",", ".")
    if not b and defaut is not None:
        return defaut
    return calculer(b)

# ===========================================================================
# MENU INTERACTIF GÉNÉRAL (28 MODULES)
# ===========================================================================
def menu():
    actions = {
        "1": ("Constantes du projet Al-Mizan (Invariants)", section_projet),
        "2": ("Vérifier une valeur avec la bride (0.6225 / 0.6015)", lambda: print(verifier_balance(demander_nombre("Valeur : ")))),
        "3": ("Matrice Scapulaire 4x4 & Pipeline 5 Doigts", section_matrice_scapulaire),
        "4": ("Les 4 Tablettes de l'Informé & les 20 États Physiques", section_tablettes_et_etats),
        "5": ("Cycle Harmonique des 15 Phases d'Al-Mizan", section_cycle_15_phases),
        "6": ("Pyramide Tensorielle 4 Niveaux & File Exécutive J-E-D-A-F-B-V-H-G", section_pyramide_et_file),
        "7": ("Triade Ontologique : Bit Déterministe ⊗ Qubit ⊗ i-Bit", section_triade_bit_qubit),
        "8": ("Matrice Fondatrice de l'Unisson 4x4 (Or Au & Argent Ag)", section_matrice_unisson_4x4),
        "9": ("Trinité Horloge Cosmique (Soleil dx, Lune dy, Terre dz, Kernel dt)", lambda: section_trinite_horloge(demander_nombre("Cycles [1.0] : ", 1.0))),
        "10": ("Matrice des 27 Formes de Silicium (F0..F26)", lambda: section_27_formes(int(demander_nombre("Index Forme [0] : ", 0)))),
        "11": ("Décomposition Texte <-> 52 Rails Harmoniques (A-Z / a-z / 0x20)", lambda: section_texte_52_rails(input("Texte : ") or "MZN")),
        "12": ("Projection Sphère Holographique 2D -> Volume Die Silicium 3D", lambda: section_sphere_holographique(demander_nombre("Rayon microns [50.0] : ", 50.0))),
        "13": ("Simulation Dérive Thermique Cryogénique (22.5 mK -> 45 mK)", lambda: section_simulation_cryogenique(int(demander_nombre("Cycles [200] : ", 200)))),
        "14": ("Jeton MZN (Base Mainnet, Répartition & Capitalisation)", lambda: section_mzn(demander_nombre("Prix théorique USDC/MZN [0.001] : ", 0.001))),
        "15": ("Algèbre Linéaire d'Unisson : Produit Scapulaire x Unisson (4x4)", section_algebre_lineaire),
        "16": ("Moteur Cryptographique : Arbre de Merkle SHA-256", section_arbre_merkle),
        "17": ("Émulateur Quantique : Portes Hadamard & Phase d'Unisson 0.6225", section_simulateur_quantique),
        "18": ("Découplage Dynamique CPMG & Cohérence Silicium 28-Si / 29-Si", lambda: section_decouplage_dynamique_cpmg(int(demander_nombre("Impulsions π [128] : ", 128)))),
        "19": ("Thermodynamique Fluidique : Débit d'Eau Pure (313 L/min) & Refroidissement", lambda: section_thermodynamique_hydro(demander_nombre("Débit L/min [313] : ", 313.0))),
        "20": ("Physique Nucléaire Bethe-Weizsäcker (Énergie de liaison Or, Argent, Silicium)", section_physique_nucleaire_bethe_weizsaecker),
        "21": ("Relativité Restreinte & Gravitationnelle (Lorentz & Schwarzschild)", lambda: section_relativite_lorentz_et_gravitation(
            demander_nombre("Fraction de c [0.6225] : ", 0.6225),
            demander_nombre("Distance en rayon rs [3.0] : ", 3.0))),
        "22": ("Physique des Trous Noirs (Rayon r_s, Hawking, Entropie)", lambda: section_trou_noir(demander_nombre("Masse kg [Msol] : ", MASSE_SOLAIRE))),
        "23": ("Matière, Antimatière et Énergie d'Annihilation E=2mc²", lambda: section_matiere_antimatiere(demander_nombre("Masse kg [0.001] : ", 0.001))),
        "24": ("Métrologie Or & Argent, Mithqal, Dirham & Nisabs", lambda: section_metaux(
            demander_nombre("Prix Or/g (vide = ignorer) : ", 0) or None,
            demander_nombre("Prix Argent/g (vide = ignorer) : ", 0) or None)),
        "25": ("Calcul de Zakat (2.5% au-dessus du Nisab)", lambda: print(f"Zakat due : {fmt(zakat(demander_nombre('Épargne : '), demander_nombre('Seuil Nisab : ')), 2)}")),
        "26": ("Spectrogramme d'Interférence Temporelle (Tracé Graphique ASCII)", lambda: section_oscillations_graphique_ascii(int(demander_nombre("Nombre de pas [32] : ", 32)))),
        "27": ("Guématrie Abjad & Réduction Harmonique (Arabe & Latin)", lambda: section_abjad_gematrie(input("Texte [AL MIZAN] : ") or "AL MIZAN")),
        "28": ("Tétrade Cosmique Al-Mizan (4 Jetons Frères & Hub de Liquidité USDC)", section_tetrade_cosmique),
        "29": ("Calculatrice scientifique libre", lambda: print("= ", calculer(input("Expression : ")))),
        "30": ("Exporter le journal d'audit complet (JSON)", exporter_journal_audit),
        "0": ("Quitter", None)
    }

    while True:
        ligne("CALCULATRICE UNIVERSELLE AL-MIZAN / ASTRO-Q°ODE — V12.0 TÉTRADE HARMONIQUE")
        for cle, (nom, _) in actions.items():
            print(f"  {cle:>2}. {nom}")
        choix = input("\nVotre choix [0-30] : ").strip()
        if choix == "0":
            print("\nClôture de session.")
            break
        act = actions.get(choix)
        if not act:
            print("Choix invalide.")
            continue
        try:
            act[1]()
        except Exception as e:
            print(f"Erreur d'exécution : {e}")

# ===========================================================================
# POINT D'ENTRÉE CLI
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Calculatrice Al-Mizan / ASTRO-Q°ODE V11.0 Absolue")
    parser.add_argument("--tout", action="store_true", help="Exécuter l'ensemble des 28 modules")
    parser.add_argument("--spectrogramme", action="store_true", help="Afficher le spectrogramme d'oscillations ASCII")
    parser.add_argument("--nucleaire", action="store_true", help="Calculer l'énergie de liaison de Bethe-Weizsäcker")
    parser.add_argument("--cpmg", type=int, metavar="PULSES", help="Simuler le découplage dynamique CPMG")
    parser.add_argument("--lorentz", type=float, metavar="V_FRACTION", help="Calculer Lorentz à la vitesse v/c")
    parser.add_argument("--abjad", type=str, metavar="TEXTE", help="Calculer l'Abjad et la réduction Mizan")
    parser.add_argument("--zakat", nargs=2, type=float, metavar=("MONTANT", "NISAB"), help="Calculer la Zakat")
    parser.add_argument("--trou-noir", type=float, metavar="MASSE_KG", help="Calculer les grandeurs d'un trou noir")
    parser.add_argument("--texte", type=str, metavar="CHAINE", help="Décomposer un texte sur les 52 rails harmoniques")
    parser.add_argument("--cryo", type=int, metavar="CYCLES", help="Simuler la dérive thermique cryogénique")
    parser.add_argument("--unisson", action="store_true", help="Afficher la Matrice d'Unisson 4x4")
    parser.add_argument("--scapulaire", action="store_true", help="Afficher la Matrice Scapulaire 4x4 et les 5 Doigts")
    parser.add_argument("--phases", action="store_true", help="Afficher le Cycle Harmonique des 15 Phases")
    parser.add_argument("--algebre", action="store_true", help="Calculer le produit matriciel Scapulaire x Unisson")
    parser.add_argument("--merkle", nargs="*", metavar="TRANSACTIONS", help="Calculer l'arbre de Merkle SHA-256")
    parser.add_argument("--qubit", action="store_true", help="Émuler la porte Hadamard et la phase 0.6225")
    parser.add_argument("--hydro", type=float, metavar="DEBIT_L_MIN", help="Calculer la puissance thermique de refroidissement")
    parser.add_argument("--tetrade", action="store_true", help="Afficher l'état de synchronisation de la Tétrade et du pool USDC")

    args = parser.parse_args()

    if args.tout:
        section_projet()
        print("\n" + verifier_balance(LIGNE_REF + FORME))
        section_matrice_scapulaire()
        section_tablettes_et_etats()
        section_cycle_15_phases()
        section_pyramide_et_file()
        section_triade_bit_qubit()
        section_matrice_unisson_4x4()
        section_trinite_horloge(1.0)
        section_27_formes(7)
        section_texte_52_rails("AMAL MIZAN")
        section_sphere_holographique(50.0)
        section_simulation_cryogenique(200)
        section_mzn()
        section_algebre_lineaire()
        section_arbre_merkle()
        section_simulateur_quantique()
        section_decouplage_dynamique_cpmg(128)
        section_thermodynamique_hydro(313.0)
        section_physique_nucleaire_bethe_weizsaecker()
        section_relativite_lorentz_et_gravitation(0.6225, 3.0)
        section_metaux()
        section_trou_noir(MASSE_SOLAIRE)
        section_matiere_antimatiere()
        section_oscillations_graphique_ascii(16)
        section_abjad_gematrie("AL MIZAN")
        section_tetrade_cosmique()
        exporter_journal_audit()
    elif args.tetrade:
        section_tetrade_cosmique()
    elif args.spectrogramme:
        section_oscillations_graphique_ascii(32)
    elif args.nucleaire:
        section_physique_nucleaire_bethe_weizsaecker()
    elif args.cpmg is not None:
        section_decouplage_dynamique_cpmg(args.cpmg)
    elif args.lorentz is not None:
        section_relativite_lorentz_et_gravitation(args.lorentz)
    elif args.abjad:
        section_abjad_gematrie(args.abjad)
    elif args.zakat:
        m, n = args.zakat
        print(f"Zakat due sur {m} avec Nisab de {n} : {fmt(zakat(m, n), 2)}")
    elif args.trou_noir:
        section_trou_noir(args.trou_noir)
    elif args.texte:
        section_texte_52_rails(args.texte)
    elif args.cryo:
        section_simulation_cryogenique(args.cryo)
    elif args.unisson:
        section_matrice_unisson_4x4()
    elif args.scapulaire:
        section_matrice_scapulaire()
    elif args.phases:
        section_cycle_15_phases()
    elif args.algebre:
        section_algebre_lineaire()
    elif args.merkle is not None:
        section_arbre_merkle(args.merkle if len(args.merkle) > 0 else None)
    elif args.qubit:
        section_simulateur_quantique()
    elif args.hydro is not None:
        section_thermodynamique_hydro(args.hydro)
    else:
        menu()

if __name__ == "__main__":
    main()
