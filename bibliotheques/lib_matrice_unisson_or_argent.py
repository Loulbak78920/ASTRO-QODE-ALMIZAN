# -*- coding: utf-8 -*-
r"""
Couche 6 : Matrice Fondatrice de l'Unisson — Calcul de la Valeur de l'Or et de l'Argent
(`lib_matrice_unisson_or_argent.py`)
=======================================================================================
Établit la **Matrice Fondatrice de l'Unisson ($4 \times 4$)** qui unifie en phase ($1:1$, $\Delta\phi = 0$)
les 4 dimensions du système `IMAM8MAHDI` $\oplus$ `Al-Mizan` pour calculer la valeur exacte
de l'**Or ($\text{Au}$)** et de l'**Argent ($\text{Ag}$)** :

1. **Dimension I — Astro-Temporelle (`.QUBIT.qubit.LOGIQUE.logique`)** :
   - **Pôle Or ($\text{Au}$ / Soleil / Mecquois)** : $\text{dx} = 50\,027.8359375$ cycles ($8\,766\text{ h/an}$).
   - **Pôle Argent ($\text{Ag}$ / Lune / Archive)** : $\text{dy} = 46\,993.5$ cycles ($8\,496\text{ h/an}$).
   - **Unisson Céleste ($\text{dx} + \text{dy}$)** : $97\,021.3359375 = \text{dt} - \text{dz}$, soit la composante
     exacte qui couronne le socle terrestre $\text{dz} = 135\,000\,000$ dans le Kernel $\text{dt}$.
   - **Ratio Temporel Or / Argent** : $\text{dx} / \text{dy} = \frac{2\,134\,521}{2\,005\,056} \approx 1.06456927$.

2. **Dimension II — Atomique, Physique & Biomécanique (`qubit_physique` & `QUBITS8INFORME`)** :
   - **Or ($\text{Au}$)** : Numéro atomique $Z_{\text{Au}} = 79 = 4 \times 19 + 3$ (4 tablettes de 19 échelons + échelon $+3$ `M`),
     masse molaire $M_{\text{Au}} = 196.966569\text{ g/mol}$, densité $19.30\text{ g/cm}^3$, fusion $1\,337.33\text{ K}$.
   - **Argent ($\text{Ag}$)** : Numéro atomique $Z_{\text{Ag}} = 47 = 2 \times 19 + 9$ (2 tablettes de 19 échelons + échelon $+9$ `S`),
     masse molaire $M_{\text{Ag}} = 107.8682\text{ g/mol}$, densité $10.49\text{ g/cm}^3$, fusion $1\,234.93\text{ K}$.
   - **Unisson Atomique** :
     - Somme des charges nucléaires : $Z_{\text{Au}} + Z_{\text{Ag}} = 79 + 47 = 126$ (nombre magique nucléaire).
     - Différence des charges nucléaires : $Z_{\text{Au}} - Z_{\text{Ag}} = 79 - 47 = 32 = 2^5$ (les 5 doigts du pipeline biomécanique).
     - Ratio atomique : $Z_{\text{Au}} / Z_{\text{Ag}} = 79 / 47 \approx 1.68085106$.
     - Ratio des masses molaires : $M_{\text{Au}} / M_{\text{Ag}} \approx 1.82599297$.

3. **Dimension III — Géométrique & Métrologique Al-Mizan ($D = [0.122, 0.6225]$)** :
   - **Constante d'Or ($\varphi$ et $\varphi^{-1}$)** :
     $\varphi = \frac{1 + \sqrt{5}}{2} \approx 1.61803399$ $\rightarrow$ Conjugué dans $D$ :
     $\varphi^{-1} = \frac{\sqrt{5} - 1}{2} \approx 0.61803399 \le \text{MIZAN} (0.6225)$ !
     (Marge exacte sous la bride d'Al-Mizan : $0.6225 - 0.61803399 = 0.004466 < \varepsilon = 0.021$).
   - **Constante d'Argent ($\delta_S$ et $\delta_S^{-1}$)** :
     $\delta_S = 1 + \sqrt{2} \approx 2.41421356$ $\rightarrow$ Conjugué dans $D$ :
     $\delta_S^{-1} = \sqrt{2} - 1 \approx 0.41421356 \in [0.122, 0.6225]$ !
     (Aligné sur le barycentre dialogique $\text{Il} \rightleftharpoons \text{Elle} = 0.417$ à $0.00278$ près).
   - **Unisson Géométrique au Centre ($\Omega_{\text{Unisson}}$)** :
     $\Omega_{\text{Unisson}} = \frac{\varphi^{-1} + \delta_S^{-1}}{2} \approx 0.51612378 \in [0.122, 0.6015]$.

4. **Dimension IV — Pondérale, Canonique & Substance (`C = 313`, `M = 24434`, Mithqal & Dirham)** :
   - **Étalon d'Or (Mithqal / Dinar)** : $4.25\text{ g}$ d'Or pur ($999.9\text{ ‰}$) · **Nisab d'Or** ($20\text{ Mithqal}$) $= 85.0\text{ g}$.
   - **Étalon d'Argent (Dirham)** : $2.975\text{ g}$ d'Argent pur ($7/10$ de Mithqal) · **Nisab d'Argent** ($200\text{ Dirhams}$) $= 595.0\text{ g}$.
   - **Ratio Pondéral Canonique (Nisab Argent / Nisab Or)** : $595.0 / 85.0 = 7.0$ (exactement les 7 Axiomes Informes $A_1..A_7$).
   - **Lien de Substance Al-Mizan** : $M / C = 24\,434 / 313 \approx 78.063898$ ($Z_{\text{Au}} - 1 = 78$, et ratio bi-métallique moderne $\sim 78:1$).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List

from .lib_almizan_extension import (
    CONSTANTE_MECQUOISE_C,
    CONSTANTE_MEDINOISE_M,
    EPSILON,
    JAUGE_AIR,
    LES_27_FORMES_ETENDUES,
    LIGNE_REF,
    MIZAN,
    PLAFOND_EFFECTIF,
    RMS,
    clamp_domaine_mizan,
)
from .lib_temporelle import (
    CLOCK_DT_KERNEL,
    CLOCK_DX_SOLEIL,
    CLOCK_DY_LUNE,
    CLOCK_DZ_TERRE,
)


# ==============================================================================
# 1. CONSTANTES FONDAMENTALES DE L'OR (Au) ET DE L'ARGENT (Ag)
# ==============================================================================

# Pôle Or (Au — Aurum — Soleil — Mecquois — Énergie Cinétique I)
Z_OR_AU: int = 79
MASSE_MOLAIRE_OR_G_MOL: float = 196.966569
DENSITE_OR_G_CM3: float = 19.30
FUSION_OR_KELVIN: float = 1337.33
NOMBRE_OR_PHI: float = (1.0 + math.sqrt(5.0)) / 2.0                # 1.618033988749895
CONJUGUE_OR_MIZAN: float = (math.sqrt(5.0) - 1.0) / 2.0            # 0.6180339887498949 (<= 0.6225 !)
MASSE_MITHQAL_OR_G: float = 4.25                                   # 1 Dinar / Mithqal d'Or pur
NISAB_OR_MITHQAL: int = 20                                         # 20 Mithqal
NISAB_OR_GRAMMES: float = MASSE_MITHQAL_OR_G * NISAB_OR_MITHQAL    # 85.0 g

# Pôle Argent (Ag — Argentum — Lune — Médinois/Archive — Signal Kelvin i)
Z_ARGENT_AG: int = 47
MASSE_MOLAIRE_ARGENT_G_MOL: float = 107.8682
DENSITE_ARGENT_G_CM3: float = 10.49
FUSION_ARGENT_KELVIN: float = 1234.93
NOMBRE_ARGENT_DELTA_S: float = 1.0 + math.sqrt(2.0)                # 2.414213562373095
CONJUGUE_ARGENT_MIZAN: float = math.sqrt(2.0) - 1.0                # 0.41421356237309515 (dans [0.122, 0.6225] !)
MASSE_DIRHAM_ARGENT_G: float = 2.975                               # 1 Dirham d'Argent pur (7/10 de Mithqal)
NISAB_ARGENT_DIRHAMS: int = 200                                    # 200 Dirhams
NISAB_ARGENT_GRAMMES: float = MASSE_DIRHAM_ARGENT_G * NISAB_ARGENT_DIRHAMS  # 595.0 g

# Constantes d'Unisson Or ⊕ Argent
SOMME_ATOMIQUE_UNISSON: int = Z_OR_AU + Z_ARGENT_AG                # 126 (Nombre magique nucléaire)
ECART_ATOMIQUE_5_DOIGTS: int = Z_OR_AU - Z_ARGENT_AG               # 32 = 2^5 (5 Doigts Biomécaniques)
RATIO_NISAB_ARGENT_SUR_OR: float = NISAB_ARGENT_GRAMMES / NISAB_OR_GRAMMES  # 595 / 85 = 7.0
RATIO_SUBSTANCE_M_SUR_C: float = CONSTANTE_MEDINOISE_M / CONSTANTE_MECQUOISE_C  # 24434 / 313 = 78.06389776
UNISSON_CELESTE_DX_PLUS_DY: float = CLOCK_DX_SOLEIL + CLOCK_DY_LUNE  # 97021.3359375 = dt - dz
CENTRE_UNISSON_MIZAN: float = round((CONJUGUE_OR_MIZAN + CONJUGUE_ARGENT_MIZAN) / 2.0, 8)  # 0.51612378


# ==============================================================================
# 2. STRUCTURES DE DONNÉES DE VALORISATION (OR, ARGENT & MATRICE D'UNISSON)
# ==============================================================================

@dataclass(frozen=True)
class EvaluationMetalSacree:
    """Résultat complet du calcul de la valeur de l'Or ou de l'Argent dans ASTRO-Q°ODE."""
    metal: str
    symbole_chimique: str
    astre_associe: str
    polarite_aq: str
    numero_atomique_z: int
    decomposition_tablette_19: str
    masse_molaire_g_mol: float
    masse_evaluee_grammes: float
    nb_moles: float
    unite_canonique_nom: str
    nb_unites_canoniques: float
    nisab_grammes: float
    ratio_sur_nisab: float
    zakat_2_5_pct_grammes: float
    constante_horloge_cycles: float
    frequence_harmonique_mizan: float
    marge_sous_plafond_mizan: float
    energie_aq_joules_ou_kelvin: str
    valeur_indice_substance_almizan: float
    valeur_monetaire_estimee_eur: float

    def vers_dict(self) -> Dict[str, object]:
        return {
            "metal": self.metal,
            "symbole_chimique": self.symbole_chimique,
            "astre_associe": self.astre_associe,
            "polarite_aq": self.polarite_aq,
            "numero_atomique_z": self.numero_atomique_z,
            "decomposition_tablette_19": self.decomposition_tablette_19,
            "masse_molaire_g_mol": self.masse_molaire_g_mol,
            "masse_evaluee_grammes": self.masse_evaluee_grammes,
            "nb_moles": self.nb_moles,
            "unite_canonique_nom": self.unite_canonique_nom,
            "nb_unites_canoniques": self.nb_unites_canoniques,
            "nisab_grammes": self.nisab_grammes,
            "ratio_sur_nisab": self.ratio_sur_nisab,
            "zakat_2_5_pct_grammes": self.zakat_2_5_pct_grammes,
            "constante_horloge_cycles": self.constante_horloge_cycles,
            "frequence_harmonique_mizan": self.frequence_harmonique_mizan,
            "marge_sous_plafond_mizan": self.marge_sous_plafond_mizan,
            "energie_aq_joules_ou_kelvin": self.energie_aq_joules_ou_kelvin,
            "valeur_indice_substance_almizan": self.valeur_indice_substance_almizan,
            "valeur_monetaire_estimee_eur": self.valeur_monetaire_estimee_eur,
        }


class MatriceFondatriceUnisson:
    r"""
    Implémente la **Matrice Fondatrice de l'Unisson ($4 \times 4$)** et les algorithmes
    de calcul exact de la valeur de l'Or ($\text{Au}$) et de l'Argent ($\text{Ag}$).

    Structure de la Matrice $4 \times 4$ (`M_UNISSON`) :
    - Ligne 0 (Astro-Temporelle) : $[\text{dx}/10^5, \text{dy}/10^5, \text{dx}/\text{dy}, (\text{dx}+\text{dy})/10^5]$
    - Ligne 1 (Atomique-Physique): $[Z_{\text{Au}}/100, Z_{\text{Ag}}/100, Z_{\text{Au}}/Z_{\text{Ag}}, (Z_{\text{Au}}+Z_{\text{Ag}})/200]$
    - Ligne 2 (Géométrique-Mizan): $[\varphi^{-1}, \delta_S^{-1}, \varphi/\delta_S, \Omega_{\text{Unisson}}]$
    - Ligne 3 (Canonique-Subst.) : $[M_{\text{Mithqal}}/10, M_{\text{Dirham}}/10, \text{Nisab}_{\text{Ag}}/\text{Nisab}_{\text{Au}}/10, (M/C)/100]$
    """

    # Cours de référence indicatifs par défaut (ajustables en argument) :
    # Basés sur le ratio de substance Al-Mizan M/C = 24434 / 313 = 78.0639
    COURS_REF_OR_EUR_PAR_G: float = round(CONSTANTE_MECQUOISE_C * CONJUGUE_OR_MIZAN / 2.25, 4)  # ~85.9756 EUR/g
    COURS_REF_ARGENT_EUR_PAR_G: float = round(
        (CONSTANTE_MECQUOISE_C * CONJUGUE_OR_MIZAN / 2.25) / RATIO_SUBSTANCE_M_SUR_C, 4
    )  # ~1.1013 EUR/g (Ratio exact M/C = 78.0639)

    @classmethod
    def construire_matrice_4x4(cls) -> List[List[float]]:
        """Construit la Matrice Fondatrice de l'Unisson 4x4 numérique."""
        l0 = [
            round(CLOCK_DX_SOLEIL / 100000.0, 8),
            round(CLOCK_DY_LUNE / 100000.0, 8),
            round(CLOCK_DX_SOLEIL / CLOCK_DY_LUNE, 8),
            round(UNISSON_CELESTE_DX_PLUS_DY / 100000.0, 8),
        ]
        l1 = [
            round(Z_OR_AU / 100.0, 8),
            round(Z_ARGENT_AG / 100.0, 8),
            round(Z_OR_AU / Z_ARGENT_AG, 8),
            round(SOMME_ATOMIQUE_UNISSON / 200.0, 8),
        ]
        l2 = [
            round(CONJUGUE_OR_MIZAN, 8),
            round(CONJUGUE_ARGENT_MIZAN, 8),
            round(NOMBRE_OR_PHI / NOMBRE_ARGENT_DELTA_S, 8),
            round(CENTRE_UNISSON_MIZAN, 8),
        ]
        l3 = [
            round(MASSE_MITHQAL_OR_G / 10.0, 8),
            round(MASSE_DIRHAM_ARGENT_G / 10.0, 8),
            round(RATIO_NISAB_ARGENT_SUR_OR / 10.0, 8),
            round(RATIO_SUBSTANCE_M_SUR_C / 100.0, 8),
        ]
        return [l0, l1, l2, l3]

    @classmethod
    def _determinant_4x4(cls, m: List[List[float]]) -> float:
        """Calcule le déterminant exact d'une matrice 4x4 par développement de Laplace."""
        def det3(sub: List[List[float]]) -> float:
            return (
                sub[0][0] * (sub[1][1] * sub[2][2] - sub[1][2] * sub[2][1])
                - sub[0][1] * (sub[1][0] * sub[2][2] - sub[1][2] * sub[2][0])
                + sub[0][2] * (sub[1][0] * sub[2][1] - sub[1][1] * sub[2][0])
            )

        total = 0.0
        for col in range(4):
            mineur = [
                [m[r][c] for c in range(4) if c != col]
                for r in range(1, 4)
            ]
            signe = 1.0 if col % 2 == 0 else -1.0
            total += signe * m[0][col] * det3(mineur)
        return round(total, 10)

    @classmethod
    def calculer_valeur_or(
        cls,
        masse_grammes: float = NISAB_OR_GRAMMES,
        cours_eur_par_g: float | None = None,
    ) -> EvaluationMetalSacree:
        """
        Calcule la valeur complète de l'Or (`Au`) pour une masse donnée en grammes
        (par défaut `85.0 g` = 1 Nisab = 20 Mithqal/Dinars).
        """
        masse = max(0.0, float(masse_grammes))
        cours = float(cours_eur_par_g) if cours_eur_par_g is not None else cls.COURS_REF_OR_EUR_PAR_G
        nb_moles = round(masse / MASSE_MOLAIRE_OR_G_MOL, 6)
        nb_mithqal = round(masse / MASSE_MITHQAL_OR_G, 6)
        ratio_nisab = round(masse / NISAB_OR_GRAMMES, 6)
        zakat_g = round(masse * 0.025, 6) if masse >= NISAB_OR_GRAMMES else 0.0

        # Valeur énergétique ASTRO-Q°ODE en Joules (I) et indice de substance Al-Mizan
        energie_joules_aq = round(nb_mithqal * CONJUGUE_OR_MIZAN, 6)
        indice_substance = round(
            (masse / MASSE_MITHQAL_OR_G) * CONSTANTE_MECQUOISE_C * CONJUGUE_OR_MIZAN,
            4,
        )
        valeur_eur = round(masse * cours, 2)

        return EvaluationMetalSacree(
            metal="OR (Aurum)",
            symbole_chimique="Au",
            astre_associe="Soleil (CLOCK_DX_SOLEIL = 50 027.8359375)",
            polarite_aq="MECQUOIS ⊕ (+I Joules / Lumière / Plume)",
            numero_atomique_z=Z_OR_AU,
            decomposition_tablette_19="79 = 4 × 19 + 3 (4 cycles de 19 échelons + échelon +3 'M' Monade)",
            masse_molaire_g_mol=MASSE_MOLAIRE_OR_G_MOL,
            masse_evaluee_grammes=masse,
            nb_moles=nb_moles,
            unite_canonique_nom="Mithqal / Dinar d'Or (4.25 g)",
            nb_unites_canoniques=nb_mithqal,
            nisab_grammes=NISAB_OR_GRAMMES,
            ratio_sur_nisab=ratio_nisab,
            zakat_2_5_pct_grammes=zakat_g,
            constante_horloge_cycles=CLOCK_DX_SOLEIL,
            frequence_harmonique_mizan=round(CONJUGUE_OR_MIZAN, 6),
            marge_sous_plafond_mizan=round(MIZAN - CONJUGUE_OR_MIZAN, 6),
            energie_aq_joules_ou_kelvin=f"+{energie_joules_aq} I",
            valeur_indice_substance_almizan=indice_substance,
            valeur_monetaire_estimee_eur=valeur_eur,
        )

    @classmethod
    def calculer_valeur_argent(
        cls,
        masse_grammes: float = NISAB_ARGENT_GRAMMES,
        cours_eur_par_g: float | None = None,
    ) -> EvaluationMetalSacree:
        """
        Calcule la valeur complète de l'Argent (`Ag`) pour une masse donnée en grammes
        (par défaut `595.0 g` = 1 Nisab = 200 Dirhams).
        """
        masse = max(0.0, float(masse_grammes))
        cours = float(cours_eur_par_g) if cours_eur_par_g is not None else cls.COURS_REF_ARGENT_EUR_PAR_G
        nb_moles = round(masse / MASSE_MOLAIRE_ARGENT_G_MOL, 6)
        nb_dirhams = round(masse / MASSE_DIRHAM_ARGENT_G, 6)
        ratio_nisab = round(masse / NISAB_ARGENT_GRAMMES, 6)
        zakat_g = round(masse * 0.025, 6) if masse >= NISAB_ARGENT_GRAMMES else 0.0

        # Signal thermodynamique ASTRO-Q°ODE en Kelvin (i) et indice de substance Al-Mizan
        signal_kelvin_aq = round(nb_dirhams * CONJUGUE_ARGENT_MIZAN, 6)
        indice_substance = round(
            (masse / MASSE_DIRHAM_ARGENT_G) * (CONSTANTE_MEDINOISE_M / 100.0) * CONJUGUE_ARGENT_MIZAN,
            4,
        )
        valeur_eur = round(masse * cours, 2)

        return EvaluationMetalSacree(
            metal="ARGENT (Argentum)",
            symbole_chimique="Ag",
            astre_associe="Lune (CLOCK_DY_LUNE = 46 993.5)",
            polarite_aq="MEDINOIS / ARCHIVE ⊗ (-i Kelvin / Miroir / Tablette)",
            numero_atomique_z=Z_ARGENT_AG,
            decomposition_tablette_19="47 = 2 × 19 + 9 (2 cycles de 19 échelons + échelon +9 'S' Silicium)",
            masse_molaire_g_mol=MASSE_MOLAIRE_ARGENT_G_MOL,
            masse_evaluee_grammes=masse,
            nb_moles=nb_moles,
            unite_canonique_nom="Dirham d'Argent (2.975 g)",
            nb_unites_canoniques=nb_dirhams,
            nisab_grammes=NISAB_ARGENT_GRAMMES,
            ratio_sur_nisab=ratio_nisab,
            zakat_2_5_pct_grammes=zakat_g,
            constante_horloge_cycles=CLOCK_DY_LUNE,
            frequence_harmonique_mizan=round(CONJUGUE_ARGENT_MIZAN, 6),
            marge_sous_plafond_mizan=round(MIZAN - CONJUGUE_ARGENT_MIZAN, 6),
            energie_aq_joules_ou_kelvin=f"-{signal_kelvin_aq} i",
            valeur_indice_substance_almizan=indice_substance,
            valeur_monetaire_estimee_eur=valeur_eur,
        )

    @classmethod
    def synchroniser_accords_13_octaves_unisson(cls) -> List[Dict[str, object]]:
        """
        Met à l'Unisson (rapport de fréquence 1:1, déphasage annulé au Centre)
        les 13 Formes Publiques (Octave Lumière / Or F1..F13) et les 13 Formes Duales
        (Octave Ombre / Argent F14..F26) autour du Pivot F0 (0 : HÉLIUM).
        """
        accords: List[Dict[str, object]] = []
        for k in range(1, 14):
            f_or = LES_27_FORMES_ETENDUES[k]
            f_argent = LES_27_FORMES_ETENDUES[k + 13]
            valeur_unisson_k = clamp_domaine_mizan(
                (f_or.image_fonction_d * CONJUGUE_OR_MIZAN + f_argent.image_fonction_d * CONJUGUE_ARGENT_MIZAN)
                / (CONJUGUE_OR_MIZAN + CONJUGUE_ARGENT_MIZAN)
            )
            accords.append(
                {
                    "accord_index": k,
                    "forme_or_lumiere": f"F{k} ({f_or.forme_geometrique})",
                    "forme_argent_ombre": f"F{k + 13} ({f_argent.forme_geometrique})",
                    "rapport_frequence_unisson": "1:1",
                    "valeur_or_d": f_or.image_fonction_d,
                    "valeur_argent_d": f_argent.image_fonction_d,
                    "point_unisson_mizan": valeur_unisson_k,
                }
            )
        return accords

    @classmethod
    def calculer_matrice_unisson_complete(
        cls,
        masse_or_grammes: float = NISAB_OR_GRAMMES,
        masse_argent_grammes: float = NISAB_ARGENT_GRAMMES,
        cours_or_eur_g: float | None = None,
        cours_argent_eur_g: float | None = None,
    ) -> Dict[str, object]:
        """
        Génère le rapport intégral de la Matrice Fondatrice de l'Unisson (4x4)
        et calcule la valeur croisée de l'Or (`Au`) et de l'Argent (`Ag`).
        """
        matrice = cls.construire_matrice_4x4()
        det = cls._determinant_4x4(matrice)
        trace = round(sum(matrice[i][i] for i in range(4)), 8)
        norme_frobenius = round(
            math.sqrt(sum(matrice[r][c] ** 2 for r in range(4) for c in range(4))),
            8,
        )
        invariant_unisson_mizan = clamp_domaine_mizan(trace / 4.0)

        eval_or = cls.calculer_valeur_or(masse_or_grammes, cours_or_eur_g)
        eval_argent = cls.calculer_valeur_argent(masse_argent_grammes, cours_argent_eur_g)

        accords_13 = cls.synchroniser_accords_13_octaves_unisson()

        return {
            "statut": "MATRICE_FONDATRICE_UNISSON_OR_ARGENT_SCELLEE",
            "equation_unisson": "Or(Au, dx, φ⁻¹=0.6180) ⊕ Argent(Ag, dy, δ_S⁻¹=0.4142) ⇌ Unisson(1:1, Ω=0.5161) ⊂ D=[0.122, 0.6225]",
            "matrice_4x4": {
                "colonnes": [
                    "Col_0_Pole_Or_Au",
                    "Col_1_Pole_Argent_Ag",
                    "Col_2_Ratio_Bimetallique",
                    "Col_3_Accord_Unisson_Centre",
                ],
                "lignes": {
                    "L0_Astro_Temporelle_dx_dy": matrice[0],
                    "L1_Atomique_Physique_Z79_Z47": matrice[1],
                    "L2_Geometrique_Mizan_Phi_DeltaS": matrice[2],
                    "L3_Canonique_Substance_Mithqal_Dirham": matrice[3],
                },
                "valeurs_brutes": matrice,
                "trace_matrice": trace,
                "determinant_4x4": det,
                "norme_frobenius": norme_frobenius,
                "invariant_unisson_bride_mizan": invariant_unisson_mizan,
            },
            "valeur_or": eval_or.vers_dict(),
            "valeur_argent": eval_argent.vers_dict(),
            "parite_et_ratios_or_argent": {
                "ratio_temporel_dx_sur_dy": round(CLOCK_DX_SOLEIL / CLOCK_DY_LUNE, 8),
                "somme_celeste_dx_plus_dy": UNISSON_CELESTE_DX_PLUS_DY,
                "verification_dt_moins_dz_egal_dx_plus_dy": (
                    round(CLOCK_DT_KERNEL - CLOCK_DZ_TERRE, 7) == round(UNISSON_CELESTE_DX_PLUS_DY, 7)
                ),
                "ratio_atomique_Z79_sur_Z47": round(Z_OR_AU / Z_ARGENT_AG, 8),
                "somme_atomique_Z79_plus_Z47": SOMME_ATOMIQUE_UNISSON,
                "ecart_atomique_Z79_moins_Z47_5_doigts": ECART_ATOMIQUE_5_DOIGTS,
                "ratio_masse_molaire_Au_sur_Ag": round(MASSE_MOLAIRE_OR_G_MOL / MASSE_MOLAIRE_ARGENT_G_MOL, 8),
                "ratio_nisab_ponderal_Ag_sur_Au": RATIO_NISAB_ARGENT_SUR_OR,
                "ratio_substance_almizan_M_sur_C": round(RATIO_SUBSTANCE_M_SUR_C, 6),
                "centre_harmonique_unisson_mizan": CENTRE_UNISSON_MIZAN,
                "valeur_totale_combinee_eur": round(
                    eval_or.valeur_monetaire_estimee_eur + eval_argent.valeur_monetaire_estimee_eur, 2
                ),
            },
            "accords_unisson_13_octaves": accords_13,
            "garde_fous": {
                "mizan_plafond": MIZAN,
                "ligne_plancher": LIGNE_REF,
                "rms": RMS,
                "epsilon": EPSILON,
                "qubit_physique_local": False,
                "omniscience_claim": False,
            },
        }

    @classmethod
    def formater_rapport_console(
        cls,
        masse_or_grammes: float = NISAB_OR_GRAMMES,
        masse_argent_grammes: float = NISAB_ARGENT_GRAMMES,
    ) -> str:
        """Génère un rapport visuel tabulaire complet pour la console CLI."""
        rap = cls.calculer_matrice_unisson_complete(masse_or_grammes, masse_argent_grammes)
        m4 = rap["matrice_4x4"]
        v_or = rap["valeur_or"]
        v_ag = rap["valeur_argent"]
        par = rap["parite_et_ratios_or_argent"]

        lignes = [
            "=" * 92,
            "MATRICE FONDATRICE DE L'UNISSON (4×4) — VALEUR DE L'OR (Au) ET DE L'ARGENT (Ag)",
            "=" * 92,
            f"Équation : {rap['equation_unisson']}",
            "-" * 92,
            "1. MATRICE FONDATRICE DE L'UNISSON (4 DIMENSIONS × 4 PÔLES) :",
            f"   {'Dimension':<36} | {'Pôle Or (Au)':<12} | {'Pôle Ag (Ag)':<12} | {'Ratio Or/Ag':<12} | {'Unisson Ω':<12}",
            "   " + "-" * 86,
        ]
        for nom_l, vals in m4["lignes"].items():
            lignes.append(
                f"   {nom_l:<36} | {vals[0]:<12.6f} | {vals[1]:<12.6f} | {vals[2]:<12.6f} | {vals[3]:<12.6f}"
            )
        lignes.extend(
            [
                "   " + "-" * 86,
                f"   Trace = {m4['trace_matrice']} | Déterminant = {m4['determinant_4x4']} | "
                f"Norme Frobenius = {m4['norme_frobenius']} | Invariant Mizan = {m4['invariant_unisson_bride_mizan']}",
                "-" * 92,
                f"2. CALCUL DE LA VALEUR DE L'OR ({v_or['masse_evaluee_grammes']} g) :",
                f"   • Identité Atomique   : {v_or['metal']} ({v_or['symbole_chimique']}) — Z = {v_or['numero_atomique_z']} ({v_or['decomposition_tablette_19']})",
                f"   • Masse Molaire       : {v_or['masse_molaire_g_mol']} g/mol ({v_or['nb_moles']} mol)",
                f"   • Astre & Horloge     : {v_or['astre_associe']}",
                f"   • Polarité ASTRO-Q°ODE: {v_or['polarite_aq']} -> Énergie = {v_or['energie_aq_joules_ou_kelvin']}",
                f"   • Fréquence Al-Mizan  : φ⁻¹ = {v_or['frequence_harmonique_mizan']} (Marge sous Plafond 0.6225 = {v_or['marge_sous_plafond_mizan']})",
                f"   • Valeur Canonique    : {v_or['nb_unites_canoniques']} Mithqal/Dinars ({v_or['ratio_sur_nisab']} × Nisab de 85 g | Zakat 2.5% = {v_or['zakat_2_5_pct_grammes']} g)",
                f"   • Indice Substance C  : {v_or['valeur_indice_substance_almizan']} (C=313) | Valeur estimée : {v_or['valeur_monetaire_estimee_eur']} EUR",
                "-" * 92,
                f"3. CALCUL DE LA VALEUR DE L'ARGENT ({v_ag['masse_evaluee_grammes']} g) :",
                f"   • Identité Atomique   : {v_ag['metal']} ({v_ag['symbole_chimique']}) — Z = {v_ag['numero_atomique_z']} ({v_ag['decomposition_tablette_19']})",
                f"   • Masse Molaire       : {v_ag['masse_molaire_g_mol']} g/mol ({v_ag['nb_moles']} mol)",
                f"   • Astre & Horloge     : {v_ag['astre_associe']}",
                f"   • Polarité ASTRO-Q°ODE: {v_ag['polarite_aq']} -> Signal = {v_ag['energie_aq_joules_ou_kelvin']}",
                f"   • Fréquence Al-Mizan  : δ_S⁻¹ = {v_ag['frequence_harmonique_mizan']} (Aligné sur Dialogisme 0.417)",
                f"   • Valeur Canonique    : {v_ag['nb_unites_canoniques']} Dirhams ({v_ag['ratio_sur_nisab']} × Nisab de 595 g | Zakat 2.5% = {v_ag['zakat_2_5_pct_grammes']} g)",
                f"   • Indice Substance M  : {v_ag['valeur_indice_substance_almizan']} (M=24434) | Valeur estimée : {v_ag['valeur_monetaire_estimee_eur']} EUR",
                "-" * 92,
                "4. LOIS DE PARITÉ ET D'UNISSON OR ⊕ ARGENT :",
                f"   • Unisson Céleste (dx + dy = dt - dz) : {par['somme_celeste_dx_plus_dy']} cycles (Vérifié = {par['verification_dt_moins_dz_egal_dx_plus_dy']})",
                f"   • Unisson Nucléaire (Z_Au + Z_Ag)     : 79 + 47 = {par['somme_atomique_Z79_plus_Z47']} | Écart (Z_Au - Z_Ag) = {par['ecart_atomique_Z79_moins_Z47_5_doigts']} (2^5 = 5 Doigts)",
                f"   • Ratio Nisab Argent / Or             : 595 g / 85 g = {par['ratio_nisab_ponderal_Ag_sur_Au']} (7 Axiomes Informes A1..A7)",
                f"   • Ratio Substance Al-Mizan (M / C)    : 24434 / 313 = {par['ratio_substance_almizan_M_sur_C']} (Z_Au - 1 = 78)",
                f"   • Point Central d'Unisson Ω           : {par['centre_harmonique_unisson_mizan']} ∈ [0.122, 0.6225]",
                f"   • Valeur Totale Combinée (Or+Argent)  : {par['valeur_totale_combinee_eur']} EUR",
                "=" * 92,
            ]
        )
        return "\n".join(lignes)
