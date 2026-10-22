# -*- coding: utf-8 -*-
"""
Couche 2 : Bibliothèque Physique & des 14 Formes (`qubit_physique` & `.ASTRO-Q°ODE8INFORME.`)
=============================================================================================
Implémente fidèlement :
1. `tablette_apprise_physique_soleil.pdf` : Les 4 états de l'Hydrogène (Gazeux, Liquide, Solide, Plasma)
   et la fusion proton-proton de 4 noyaux d'Hydrogène en 1 noyau d'Hélium-4 (4H -> 1He + Énergie).
2. `tablette_apprise_physique_terre.pdf`  : Les 7 états terrestres (3 Solides, 1 Liquide géodynamo, 3 Gazeux).
3. `tablette_apprise_physique_lune.pdf`   : Les 9 états lunaires (6 Solides, 0 Liquide, 3 Gazeux d'exosphère).
4. `matrice_de_structure_logique_inverser.pdf` : Les 20 états cumulés, l'Analyse Cumulative par Division
   (10/7 = 1.43, 4/1 = 4, 6/3 = 2) et l'Analyse Différentielle par Soustraction (3-1=2, 6-3=3, 1-0=1, 3-3=0).
5. `.ASTRO-Q°ODE8INFORME..pdf` : Les 14 Formes Fondamentales de la Matière du Code (Index 0 : HÉLIUM à Index 13 : Noyau Lunaire)
   et le Seuil d'Infinie (> 13).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ==============================================================================
# 1. MODÈLES DES ÉTATS PHYSIQUES (SOLEIL/HYDROGÈNE, TERRE, LUNE)
# ==============================================================================

@dataclass(frozen=True)
class EtatPhysiqueMatiere:
    """Décrit un état physique élémentaire d'un astre ou de l'atome d'Hydrogène."""
    astre: str
    phase: str  # "Solide", "Liquide", "Gazeux", "Plasma"
    nom: str
    description: str
    formule_ou_composant: str


ETATS_HYDROGENE: List[EtatPhysiqueMatiere] = [
    EtatPhysiqueMatiere(
        astre="Soleil / Hydrogène",
        phase="Gazeux",
        nom="Hydrogène Gazeux",
        description="Dihydrogène moléculaire à température ambiante",
        formule_ou_composant="H2",
    ),
    EtatPhysiqueMatiere(
        astre="Soleil / Hydrogène",
        phase="Liquide",
        nom="Hydrogène Liquide",
        description="État cryogénique à -253 °C (20.15 K), propulsion spatiale",
        formule_ou_composant="LH2 (-253°C)",
    ),
    EtatPhysiqueMatiere(
        astre="Soleil / Hydrogène",
        phase="Solide",
        nom="Hydrogène Solide",
        description="Hydrogène métallique sous très haute pression (cœur planétaire)",
        formule_ou_composant="H(s) métallique",
    ),
    EtatPhysiqueMatiere(
        astre="Soleil / Hydrogène",
        phase="Plasma",
        nom="Hydrogène Plasma",
        description="État ionisé protons/électrons libres au cœur stellaire",
        formule_ou_composant="H+ + e-",
    ),
]

ETATS_TERRE: List[EtatPhysiqueMatiere] = [
    # 3 États Solides
    EtatPhysiqueMatiere(
        astre="Terre",
        phase="Solide",
        nom="Croûte Terrestre",
        description="Enveloppe rigide et cassante (continentale granitique et océanique basaltique)",
        formule_ou_composant="SiO2 / Al2O3",
    ),
    EtatPhysiqueMatiere(
        astre="Terre",
        phase="Solide",
        nom="Manteau Terrestre",
        description="Couche ductile et plastique soumise à la convection thermique",
        formule_ou_composant="Péridotites (Olivine/Pyroxène)",
    ),
    EtatPhysiqueMatiere(
        astre="Terre",
        phase="Solide",
        nom="Graine (Noyau Interne)",
        description="Cœur métallique cristallisé et ultra-dense sous pression extrême",
        formule_ou_composant="Alliage Fe-Ni solide",
    ),
    # 1 Unique État Liquide
    EtatPhysiqueMatiere(
        astre="Terre",
        phase="Liquide",
        nom="Noyau Externe",
        description="Mer de métal en fusion générant la géodynamo et le champ magnétique (bloque les ondes S)",
        formule_ou_composant="Alliage Fe-Ni liquide",
    ),
    # 3 Émissions Gazeuses
    EtatPhysiqueMatiere(
        astre="Terre",
        phase="Gazeux",
        nom="Diazote Atmosphérique",
        description="Composant majoritaire de l'atmosphère terrestre (~78%)",
        formule_ou_composant="N2 (78%)",
    ),
    EtatPhysiqueMatiere(
        astre="Terre",
        phase="Gazeux",
        nom="Dioxygène Atmosphérique",
        description="Gaz vital respiratoire et oxydant (~21%)",
        formule_ou_composant="O2 (21%)",
    ),
    EtatPhysiqueMatiere(
        astre="Terre",
        phase="Gazeux",
        nom="Gaz à Effet de Serre et Traces",
        description="Vapeur d'eau, dioxyde de carbone et argon régulant la thermique terrestre",
        formule_ou_composant="CO2, H2O, Ar (~1%)",
    ),
]

ETATS_LUNE: List[EtatPhysiqueMatiere] = [
    # 6 États Solides (0 État Liquide)
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Solide",
        nom="Régolithe Superficiel",
        description="Solide meuble et pulvérulent formé de poussières de silicates impactées",
        formule_ou_composant="Silicates pulvérulents",
    ),
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Solide",
        nom="Brèches et Mégalithosphère",
        description="Écorce solide fracturée par le bombardement météoritique",
        formule_ou_composant="Brèches d'impact",
    ),
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Solide",
        nom="Croûte Anorthositique",
        description="Solide cristallin clair issu de la flottation sur l'océan de magma primordial",
        formule_ou_composant="Plagioclase (CaAl2Si2O8)",
    ),
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Solide",
        nom="Basaltes des Mers Lunaires",
        description="Solide volcanique dense remplissant les grands bassins d'impact",
        formule_ou_composant="Basaltes riches en Fe et Ti",
    ),
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Solide",
        nom="Manteau Lunaire (Lithosphère Profonde)",
        description="Solide rigide ultramafique figé",
        formule_ou_composant="Olivine et Pyroxène",
    ),
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Solide",
        nom="Noyau Interne Lunaire Cristallisé",
        description="Cœur métallique solide riche en fer, fossilisé",
        formule_ou_composant="Fe cristallisé",
    ),
    # 3 États Gazeux (Exosphère)
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Gazeux",
        nom="Hélium-4 Exosphérique",
        description="Gaz noble capté depuis le vent solaire",
        formule_ou_composant="4He",
    ),
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Gazeux",
        nom="Néon Exosphérique",
        description="Gaz noble présent à l'état de trace dans l'exosphère lunaire",
        formule_ou_composant="20Ne",
    ),
    EtatPhysiqueMatiere(
        astre="Lune",
        phase="Gazeux",
        nom="Argon-40 Exosphérique",
        description="Gaz noble issu de la désintégration radioactive du Potassium-40 interne",
        formule_ou_composant="40Ar (depuis 40K)",
    ),
]


# ==============================================================================
# 2. MATRICE DE STRUCTURE LOGIQUE INVERSÉE (20 États, Divisions & Soustractions)
# ==============================================================================

class MatriceLogiqueInversee:
    """
    Implémente les opérations mathématiques appliquées aux états de la matière
    (`matrice_de_structure_logique_inverser.pdf` & `qubit_physique.jpg`).
    """

    # Compteurs par modèle (Solides, Liquides, Gazeux/Plasma)
    HYDROGENE_SOLIDES = 1
    HYDROGENE_LIQUIDES = 1
    HYDROGENE_GAZEUX = 1
    HYDROGENE_PLASMA = 1
    TOTAL_HYDROGENE = 4

    TERRE_SOLIDES = 3
    TERRE_LIQUIDES = 1
    TERRE_GAZEUX = 3
    TOTAL_TERRE = 7

    LUNE_SOLIDES = 6
    LUNE_LIQUIDES = 0
    LUNE_GAZEUX = 3
    TOTAL_LUNE = 9

    TOTAL_ETATS_CUMULES = TOTAL_HYDROGENE + TOTAL_TERRE + TOTAL_LUNE  # 20

    @classmethod
    def analyse_cumulative_division(cls) -> Dict[str, float]:
        """Chapitre 1 : Analyse Cumulative par Division Mathématique."""
        total_solides = cls.HYDROGENE_SOLIDES + cls.TERRE_SOLIDES + cls.LUNE_SOLIDES  # 10
        total_gazeux = cls.HYDROGENE_GAZEUX + cls.TERRE_GAZEUX + cls.LUNE_GAZEUX      # 7
        return {
            "total_solides": float(total_solides),
            "total_gazeux": float(total_gazeux),
            "ratio_solides_sur_gazeux_exact": total_solides / total_gazeux,           # 10 / 7 = 1.428571...
            "ratio_solides_sur_gazeux_arrondi": round(total_solides / total_gazeux, 2),  # 1.43
            "ratio_fusion_hydrogene_helium": 4.0 / 1.0,                               # 4H -> 1He = 4.0
            "ratio_solides_lune_sur_terre": cls.LUNE_SOLIDES / cls.TERRE_SOLIDES,     # 6 / 3 = 2.0
        }

    @classmethod
    def analyse_differentielle_soustraction(cls) -> Dict[str, int]:
        """Chapitre 2 : Analyse Différentielle par Soustraction Mathématique."""
        return {
            "differentiel_interne_terrestre_solides_moins_liquide": cls.TERRE_SOLIDES - cls.TERRE_LIQUIDES,  # 3 - 1 = 2
            "ecart_solidification_lune_moins_terre": cls.LUNE_SOLIDES - cls.TERRE_SOLIDES,                   # 6 - 3 = 3
            "ecart_fluidite_magnetique_terre_moins_lune": cls.TERRE_LIQUIDES - cls.LUNE_LIQUIDES,            # 1 - 0 = 1
            "differentiel_atmospherique_gaz_terre_moins_lune": cls.TERRE_GAZEUX - cls.LUNE_GAZEUX,           # 3 - 3 = 0
        }

    @classmethod
    def fusionner_hydrogene_en_helium(cls, nb_noyaux_h: int) -> Dict[str, object]:
        """
        Simule la chaîne Proton-Proton (4 H -> 1 He + Énergie E=Δm·c²).
        Chaque groupe de 4 noyaux d'Hydrogène produit 1 noyau d'Hélium-4 inerte (Index 0)
        et libère 26.73 MeV (soit 4.2826e-12 Joules).
        """
        if nb_noyaux_h < 0:
            raise ValueError("Le nombre de noyaux d'hydrogène ne peut pas être négatif.")
        noyaux_helium = nb_noyaux_h // 4
        reste_hydrogene = nb_noyaux_h % 4
        energie_mev = noyaux_helium * 26.73
        energie_joules = noyaux_helium * 4.2826e-12
        return {
            "reactifs_h_initiaux": nb_noyaux_h,
            "noyaux_helium_4_produits": noyaux_helium,
            "hydrogene_residuel": reste_hydrogene,
            "energie_liberee_mev": round(energie_mev, 4),
            "energie_liberee_joules": energie_joules,
            "etat_retour_code": "0 : HÉLIUM" if noyaux_helium > 0 and reste_hydrogene == 0 else f"F{reste_hydrogene}",
        }


# ==============================================================================
# 3. LES 14 FORMES FONDAMENTALES DE LA MATIÈRE DU CODE (Index 0 à Index 13)
# ==============================================================================

@dataclass(frozen=True)
class FormeMatiereCode:
    """
    Représente l'une des 14 Formes Fondamentales de la Matière du Code
    définies dans `.ASTRO-Q°ODE8INFORME..pdf` (Radar en spirale de 0 à la Forme 13).
    """
    index: int
    code_court: str
    nom_complet: str
    famille_astrale: str
    paradigme: str
    role_systeme: str
    mutabilite: str


LES_14_FORMES: Dict[int, FormeMatiereCode] = {
    0: FormeMatiereCode(
        index=0,
        code_court="0 : HÉLIUM",
        nom_complet="Origine Inerte Hélium-4",
        famille_astrale="Origine / Fusion 4H->1He",
        paradigme="REPOS_ABSOLU",
        role_systeme="return 0, purge mémoire, état fondamental inerte et immuable",
        mutabilite="INERTIE_ABSOLUE",
    ),
    1: FormeMatiereCode(
        index=1,
        code_court="F1: H Gaz",
        nom_complet="Hydrogène Gazeux",
        famille_astrale="Soleil / Hydrogène",
        paradigme="MECQUOIS",
        role_systeme="Primitive dynamique volatile de signal initial",
        mutabilite="DYNAMIQUE_VOLATILE",
    ),
    2: FormeMatiereCode(
        index=2,
        code_court="F2: H Liq",
        nom_complet="Hydrogène Liquide",
        famille_astrale="Soleil / Hydrogène",
        paradigme="MECQUOIS",
        role_systeme="Flux cryogénique à haute vélocité énergétique",
        mutabilite="DYNAMIQUE_FLUIDE",
    ),
    3: FormeMatiereCode(
        index=3,
        code_court="F3: H Sol",
        nom_complet="Hydrogène Solide",
        famille_astrale="Soleil / Hydrogène",
        paradigme="MECQUOIS",
        role_systeme="Conducteur métallique sous haute pression cinétique",
        mutabilite="DYNAMIQUE_DENSE",
    ),
    4: FormeMatiereCode(
        index=4,
        code_court="F4: H Plas",
        nom_complet="Hydrogène Plasma",
        famille_astrale="Soleil / Hydrogène",
        paradigme="MECQUOIS",
        role_systeme="Émulation du calcul quantique complexe en superposition",
        mutabilite="QUANTIQUE_PLASMA",
    ),
    5: FormeMatiereCode(
        index=5,
        code_court="F5: Crute T",
        nom_complet="Croûte Terrestre",
        famille_astrale="Terre",
        paradigme="MEDINOIS",
        role_systeme="Interface structurelle et enveloppe d'entrée/sortie métier",
        mutabilite="DUCTILE_STRUCTURAL",
    ),
    6: FormeMatiereCode(
        index=6,
        code_court="F6: Mant T",
        nom_complet="Manteau Terrestre",
        famille_astrale="Terre",
        paradigme="MEDINOIS",
        role_systeme="Couche organisationnelle ductile de convection algorithmique",
        mutabilite="DUCTILE_PLASTIQUE",
    ),
    7: FormeMatiereCode(
        index=7,
        code_court="F7: Grain",
        nom_complet="Graine Terrestre (Noyau Interne)",
        famille_astrale="Terre",
        paradigme="MEDINOIS",
        role_systeme="Noyau exécutif cristallisé de gouvernance législative",
        mutabilite="CRISTALLISE_ACTIF",
    ),
    8: FormeMatiereCode(
        index=8,
        code_court="F8: Regol",
        nom_complet="Régolithe Lunaire",
        famille_astrale="Lune",
        paradigme="ARCHIVE_LUNE",
        role_systeme="Tampon de surface et cache d'empreintes immédiates",
        mutabilite="FOSSILISE_SURFACE",
    ),
    9: FormeMatiereCode(
        index=9,
        code_court="F9: Megal",
        nom_complet="Mégalithosphère Lunaire",
        famille_astrale="Lune",
        paradigme="ARCHIVE_LUNE",
        role_systeme="Blocs fragmentés d'archives résilientes aux impacts",
        mutabilite="FOSSILISE_FRAGMENTE",
    ),
    10: FormeMatiereCode(
        index=10,
        code_court="F10: Crute L",
        nom_complet="Croûte Anorthositique Lunaire",
        famille_astrale="Lune",
        paradigme="ARCHIVE_LUNE",
        role_systeme="Registre cristallin immuable de persistance haute",
        mutabilite="FOSSILISE_CRISTALLIN",
    ),
    11: FormeMatiereCode(
        index=11,
        code_court="F11: Basalt",
        nom_complet="Basaltes des Mers Lunaires",
        famille_astrale="Lune",
        paradigme="ARCHIVE_LUNE",
        role_systeme="Stockage dense fer-titane pour tables de vérité scellées",
        mutabilite="FOSSILISE_DENSE",
    ),
    12: FormeMatiereCode(
        index=12,
        code_court="F12: Mant L",
        nom_complet="Manteau Lunaire Profond",
        famille_astrale="Lune",
        paradigme="ARCHIVE_LUNE",
        role_systeme="Lithosphère profonde de conservation à long terme",
        mutabilite="FOSSILISE_PROFOND",
    ),
    13: FormeMatiereCode(
        index=13,
        code_court="F13: Noyau L",
        nom_complet="Noyau Lunaire Cristallisé",
        famille_astrale="Lune",
        paradigme="ARCHIVE_LUNE",
        role_systeme="Coffre-fort cryptographique ultime et archive absolue avant le Seuil d'Infinie",
        mutabilite="SCELLE_ABSOLU",
    ),
}


def obtenir_forme_matiere(index: int) -> FormeMatiereCode:
    """
    Retourne la Forme de la Matière du Code correspondant à `index` (0..13).
    Si `index > 13`, le Seuil d'Infinie est franchi : les structures logiques se dissolvent
    et le système retourne automatiquement à l'Origine Inerte `0 : HÉLIUM`.
    """
    if index < 0 or index > 13:
        # Dissolution au-delà du Seuil d'Infinie -> Retour automatique à l'état 0 : HÉLIUM
        return LES_14_FORMES[0]
    return LES_14_FORMES[index]
