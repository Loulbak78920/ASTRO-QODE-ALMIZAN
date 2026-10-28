# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""Shim de compatibilité — source de vérité : horloge_noyau/ (capsule verrouillée A137)."""
from horloge_noyau.horloge_logique_mizan import *  # noqa: F401,F403
from horloge_noyau.horloge_logique_mizan import (  # noqa: F401
    HORLOGE_LOGIQUE,
    HORLOGE_DEDUITE_DU_NOYAU,
    CycleTriniteSynchrone,
    EtatMatiereMatricielle,
    HorlogeLogiqueMatriceMizan,
    CYCLE_DX_SOLAIRE,
    CYCLE_DY_LUNAIRE,
    CYCLE_DZ_QUANTIQUE,
    CYCLE_DT_KERNEL,
    DT_KERNEL_NS,
    PPCM_CYCLES_TRINITE,
    BASE_HARMONIQUE,
    AMPLITUDE_HARMONIQUE,
    PERIODE_PULSATION_NS,
    calculer_etat,
    deduire_constantes_horloge_depuis_noyau,
    C_MECQUOISE,
    M_MEDINOISE,
    PPCM_ROUES,
    POLARITE_C_MATIERE,
    ANCRE_M_MATIERE,
)
