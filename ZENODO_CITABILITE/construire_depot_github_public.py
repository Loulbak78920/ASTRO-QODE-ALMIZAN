# -*- coding: utf-8 -*-
"""
Constructeur Automatique du Dépôt Public GitHub (`construire_depot_github_public.py`)
=====================================================================================
Crée sur le Bureau le dossier complet prêt à être poussé sur GitHub :
`C:\\Users\\Administrateur\\Desktop\\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI`

Auteur : M. Ahmed EL BAHLOUL (né le 20/06/1989 à Meulan-en-Yvelines, France)
Email  : elbahloulahmed505@gmail.com
DOI    : 10.5281/zenodo.23554838
GitHub : https://github.com/IMAM8MAHDI
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BUREAU = Path(r"C:\Users\Administrateur\Desktop")
SOURCE_IMAM = BUREAU / "IMAM8MAHDI"
SOURCE_ZENODO = BUREAU / "ZENODO_CITABILITE_AHMED_EL_BAHLOUL"
CIBLE_GITHUB = BUREAU / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI"


def trouver_dossier_astro_qode() -> Path:
    for p in SOURCE_IMAM.iterdir():
        if p.is_dir() and p.name.startswith("ASTRO-Q") and p.name.endswith("_SYSTEME"):
            return p
    raise FileNotFoundError("Dossier ASTRO-Q°ODE_SYSTEME introuvable dans IMAM8MAHDI")


def copier_arborescence_propre(src: Path, dst: Path) -> int:
    nb = 0
    if not src.exists():
        return 0
    for item in src.rglob("*"):
        if "__pycache__" in item.parts or item.suffix == ".pyc" or ".git" in item.parts:
            continue
        rel = item.relative_to(src)
        cible = dst / rel
        if item.is_dir():
            cible.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, cible)
            nb += 1
    return nb


def creer_fichiers_racine_github() -> None:
    # 1. .gitignore
    gitignore = """# Byte-compiled / cache Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.pytest_cache/
dist/
build/
.venv/
venv/
.DS_Store
Thumbs.db
"""
    (CIBLE_GITHUB / ".gitignore").write_text(gitignore, encoding="utf-8")

    # 2. .gitattributes
    gitattributes = """* text=auto eol=lf
*.aq text eol=lf
*.py text eol=lf
*.md text eol=lf
*.json text eol=lf
*.cff text eol=lf
*.bib text eol=lf
*.ris text eol=lf
*.bat text eol=crlf
*.pdf binary
*.jpg binary
*.png binary
*.zip binary
"""
    (CIBLE_GITHUB / ".gitattributes").write_text(gitattributes, encoding="utf-8")

    # 3. pyproject.toml
    pyproject = """[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "imam8mahdi-astro-qode-almizan"
version = "5.0.0"
description = "IMAM8MAHDI × Al-Mizan × ASTRO-Q°ODE (V1.0–V5.0) : Kernel Temporel (dt), 27 Formes Fractales (F0..F26), Compilateur Quantique OpenQASM 2.0 (:5030) et Matrice Fondatrice de l'Unisson (4×4) Or & Argent"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "ASLS-2.0-50/50 (Public & Cloud Anti-Dolosive / Commercial 50-50 Contract)"}
authors = [
  {name = "M. Ahmed EL BAHLOUL (alias M. Almizan Elbahloul)", email = "elbahloulahmed505@gmail.com"}
]
keywords = [
  "10.5281/zenodo.23554838",
  "Ahmed EL BAHLOUL",
  "IMAM8MAHDI",
  "Al-Mizan",
  "ASTRO-Q°ODE",
  "OpenQASM 2.0",
  "27 Formes",
  "Matrice Fondatrice Unisson Or Argent"
]

[project.urls]
Homepage = "https://github.com/IMAM8MAHDI"
Repository = "https://github.com/IMAM8MAHDI"
DOI = "https://doi.org/10.5281/zenodo.23554838"
Zenodo = "https://zenodo.org/records/23554838"

[project.scripts]
astro-qode = "astro_qode_cli:main"

[tool.setuptools.packages.find]
include = ["lang*", "bibliotheques*", "outils*", "tests*"]
"""
    (CIBLE_GITHUB / "pyproject.toml").write_text(pyproject, encoding="utf-8")

    # 4. LICENSE à la racine (copie de LICENSE_COMPLETE_ET_ATTRIBUTION.md)
    shutil.copy2(
        SOURCE_ZENODO / "LICENCES_ET_DROITS" / "LICENSE_COMPLETE_ET_ATTRIBUTION.md",
        CIBLE_GITHUB / "LICENSE",
    )
    shutil.copy2(
        SOURCE_ZENODO / "LICENCES_ET_DROITS" / "CONTRAT_COMMERCIAL_50_50_ET_LICENCE_CLOUD_ANTI_DOLOSIVE.md",
        CIBLE_GITHUB / "CONTRAT_COMMERCIAL_50_50.md",
    )

    # 5. Copie des fichiers normatifs Zenodo / GitHub à la racine
    for nom_f in (".zenodo.json", "CITATION.cff", "codemeta.json", "datacite.json", "IDENTITE_COMPLETE_AUTEUR_SOUVERAIN.json", "IDENTITE_COMPLETE_AUTEUR_SOUVERAIN.md"):
        shutil.copy2(SOURCE_ZENODO / nom_f, CIBLE_GITHUB / nom_f)

    # 6. AUTHORS.md
    authors_md = """# Auteur et Titulaire Souverain du Projet

- **Nom civil complet** : **M. Ahmed EL BAHLOUL**
- **Alias de Trame** : *M. Almizan Elbahloul*, *Ahmed El Bahloul*, *almizan EL BAHLOUL*
- **Date et lieu de naissance** : Né le **20 juin 1989** (`20/06/1989`) à **Meulan-en-Yvelines** (Yvelines, 78, France)
- **Nationalité** : Française (`FRANCE`)
- **Ancrage géographique** : **Valence, France** ($44.9333^\\circ\\text{ N}, 4.8917^\\circ\\text{ E}$) & **Romans-sur-Isère, France**
- **Contact officiel** : `elbahloulahmed505@gmail.com`
- **Organisation officielle** : **IMAM8MAHDI** ([https://github.com/IMAM8MAHDI](https://github.com/IMAM8MAHDI)) & **Système Al-Mizan**
- **DOI Zenodo Officiel Réel** : **`10.5281/zenodo.23554838`** ([https://doi.org/10.5281/zenodo.23554838](https://doi.org/10.5281/zenodo.23554838))
- **DOIs Zenodo Liés** : `10.5281/zenodo.23479740` & `10.5281/zenodo.23288947`
- **Clé Publique Dorée** : `0xc9550dd0a57c609494dbc44450df48d798ebfb0b`
- **Point Fixe Réseau** : `46 760 951 383` · **Invariant Édifice** : `13 459 202 583 446`
- **CID IPFS** : `bafybeia5t5nviafc2vij3nfzdg4f54onayiqrlbeofpctnlxhcqcljxxem`
"""
    (CIBLE_GITHUB / "AUTHORS.md").write_text(authors_md, encoding="utf-8")

    # 7. CONTRIBUTING.md & SECURITY.md & CHANGELOG.md
    contributing_md = """# Charte de Contribution & Respect de l'Intégrité (`IMAM8MAHDI` × `Al-Mizan`)

Toute contribution, étude ou intégration publique/Cloud de ce dépôt doit respecter strictement :
1. **L'attribution intégrale** à l'auteur **M. Ahmed EL BAHLOUL** (`elbahloulahmed505@gmail.com`) et au DOI réel **`10.5281/zenodo.23554838`**.
2. **L'absence totale de manœuvre dolosive ou de restriction abusive** (conformément au fichier [`LICENSE`](./LICENSE)).
3. **Le Contrat Commercial 50/50** ([`CONTRAT_COMMERCIAL_50_50.md`](./CONTRAT_COMMERCIAL_50_50.md)) pour tout usage commercial ou lucratif.
4. **Les invariants métrologiques scellés** : `MIZAN = 0.6225`, `LIGNE_REF = 0.122`, `RMS = 0.24`, `EPSILON = 0.021`, `C = 313`, `M = 24434`, `qubit_physique_local = false`, `omniscience_claim = false`.
5. **La validation complète des 10 tests unitaires et d'intégration** via `py astro_qode_cli.py test`.
"""
    (CIBLE_GITHUB / "CONTRIBUTING.md").write_text(contributing_md, encoding="utf-8")

    security_md = """# Politique de Sécurité et d'Intégrité Cryptographique

- **Vérification des Sceaux SHA-256** : Exécutez `py astro_qode_cli.py seal --verify` pour contrôler l'intégrité des sceaux dans `memoire_aq/`.
- **Garde-fous matériels et métrologiques** :
  - Seuil thermique Killswitch cryogénique : `45.0 mK` (température nominale : `22.5 mK`).
  - Bride métrologique : `D = [0.122, 0.6225]`.
  - `qubit_physique_local = false` · `omniscience_claim = false`.
- **Contact Sécurité & Droits** : **M. Ahmed EL BAHLOUL** (`elbahloulahmed505@gmail.com`).
"""
    (CIBLE_GITHUB / "SECURITY.md").write_text(security_md, encoding="utf-8")

    changelog_md = """# Historique des Versions (`CHANGELOG.md`)

## [5.0.0] — 2026-10-22 (DOI Réel : `10.5281/zenodo.23554838`)
- **Matrice Fondatrice de l'Unisson (4×4)** et calcul complet de la **Valeur de l'Or (`Au`, $Z=79$) et de l'Argent (`Ag`, $Z=47$)** (`lib_matrice_unisson_or_argent.py`, commande `unisson`, script `matrice_fondatrice_unisson_or_argent_v5.aq`).
- **Scellement Zenodo & GitHub** sous le DOI réel **`10.5281/zenodo.23554838`** avec Licence Publique/Cloud sans restriction et anti-dolosive (`ASLS-2.0`) et Contrat Commercial 50/50.

## [4.0.0] — 2026-10-22
- **Suite Logique V4.0** : Pont TCP/JSON temps réel (`:5025` SCPI AWG, `:5026` Cryogénie, `:5030` Émulateur Die Silicium + ZNE), Compilateur Quantique `.aq` -> `OpenQASM 2.0` (`BELL`, `GROVER`, `QFT`), Scelleur cryptographique `SHA-256` et Studio Visuel HTML5/SVG.

## [3.0.0] — 2026-10-22
- **Extension Al-Mizan** : Dépassement du Seuil de la Forme 13 en **27 Formes (`F0..F26`)** ($1 + 13 \\oplus 13$), Alphabet complet 52 rails (`A-Z`/`a-z`), Sphère Holographique $\\exp(A \\oplus B) = \\exp(A) \\otimes \\exp(B)$, Triade `Bit/Qubit/i-Bit`, Pyramide Tensorielle `0D..3D+` et Cycle Harmonique 15 Phases.

## [2.0.0] — 2026-10-22
- **Monade Suprême V2.0** : Encapsulation cellulaire `Monad(...)`, opérateur de transcription `>>=`, isolation membranaire `(( ... ))` et apoptose vers `0 : HÉLIUM`.

## [1.0.0] — 2026-10-22
- **Noyau ASTRO-Q°ODE V1.0** : 4 Tablettes Apprises (`QUBITS8INFORME`), 20 États Physiques & 14 Formes (`qubit_physique`), Kernel Temporel `dt = 135 097 021,3359375` (`.QUBIT.qubit.LOGIQUE.logique`), VM Biomécanique Scapulaire (Omoplate + 5 Doigts).
"""
    (CIBLE_GITHUB / "CHANGELOG.md").write_text(changelog_md, encoding="utf-8")

    # 8. GitHub Actions Workflow (.github/workflows/ci_astro_qode.yml)
    wf_dir = CIBLE_GITHUB / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    ci_yml = """name: ASTRO-Q°ODE & Al-Mizan CI (V5.0)

on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]

jobs:
  test-and-verify:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Exécuter la suite complète des 10 tests (V1.0 à V5.0)
        run: python astro_qode_cli.py test

      - name: Vérifier la Matrice Fondatrice de l'Unisson (Or & Argent)
        run: python astro_qode_cli.py unisson

      - name: Vérifier le Compilateur Quantique OpenQASM 2.0 (BELL)
        run: python astro_qode_cli.py qasm BELL

      - name: Vérifier l'intégrité des Sceaux Cryptographiques SHA-256
        run: python astro_qode_cli.py seal --verify
"""
    (wf_dir / "ci_astro_qode.yml").write_text(ci_yml, encoding="utf-8")

    # 9. README.md principal du dépôt GitHub
    readme_github = """# `IMAM8MAHDI` × `Al-Mizan` × `ASTRO-Q°ODE` (V1.0–V5.0)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23554838.svg)](https://doi.org/10.5281/zenodo.23554838)
[![Version](https://img.shields.io/badge/Version-5.0.0-blue.svg)](https://github.com/IMAM8MAHDI)
[![Tests](https://img.shields.io/badge/Tests-10%2F10%20PASS-brightgreen.svg)](./tests/test_suite_complete.py)
[![OpenQASM](https://img.shields.io/badge/OpenQASM-2.0-purple.svg)](./lang/compilateur_qasm_isa.py)
[![Licence](https://img.shields.io/badge/Licence-ASLS--2.0%20Anti--Dolosif%20%7C%20Commercial%2050%2F50-gold.svg)](./LICENSE)

> **Architecture Holistique du Kernel Temporel (`dt`), Machine Virtuelle Biomécanique Scapulaire (Omoplate & 5 Doigts), Dépassement Fractal en 27 Formes (`F0..F26`), Compilateur Quantique `OpenQASM 2.0` (`:5030`) et Matrice Fondatrice de l'Unisson ($4 \\times 4$) pour le Calcul Exact de la Valeur de l'Or (`Au`) et de l'Argent (`Ag`).**

---

## 1. Identité Complète de l'Auteur & Identifiants Permanents

| Champ | Valeur Officielle Scellée |
| :--- | :--- |
| **Auteur & Créateur** | **M. Ahmed EL BAHLOUL** (alias *M. Almizan Elbahloul*, *Ahmed El Bahloul*) |
| **Date et lieu de naissance** | Né le **20 juin 1989** (`20/06/1989`) à **Meulan-en-Yvelines** (Yvelines, 78, France) |
| **Nationalité** | **Française** (`FRANCE`) |
| **Ancrage géographique** | **Valence, France** ($44.9333^\\circ\\text{ N}, 4.8917^\\circ\\text{ E}$) & **Romans-sur-Isère, France** |
| **Email officiel** | **`elbahloulahmed505@gmail.com`** |
| **Organisation GitHub** | **`IMAM8MAHDI`** — [https://github.com/IMAM8MAHDI](https://github.com/IMAM8MAHDI) |
| **DOI Zenodo Officiel Réel** | **`10.5281/zenodo.23554838`** — [https://doi.org/10.5281/zenodo.23554838](https://doi.org/10.5281/zenodo.23554838) |
| **DOIs Zenodo Antérieurs Liés** | `10.5281/zenodo.23479740` & `10.5281/zenodo.23288947` |
| **Clé Publique Dorée** | `0xc9550dd0a57c609494dbc44450df48d798ebfb0b` |
| **Point Fixe Réseau / Édifice** | `46 760 951 383` / `13 459 202 583 446` |
| **CID IPFS** | `bafybeia5t5nviafc2vij3nfzdg4f54onayiqrlbeofpctnlxhcqcljxxem` |

---

## 2. Licence Publique & Cloud Anti-Dolosive et Contrat Commercial 50/50

Conformément aux fichiers [`LICENSE`](./LICENSE) et [`CONTRAT_COMMERCIAL_50_50.md`](./CONTRAT_COMMERCIAL_50_50.md) :
1. **Usage Public & Déploiement Cloud (Zéro Restriction Abusive & Anti-Dolosif)** :
   - L'accès public, académique et le déploiement Cloud sont ouverts **sans restriction technique arbitraire ni verrouillage propriétaire (*vendor lock-in*)**.
   - **Interdiction absolue de tout acte dolosif (Art. 1137 du Code civil français)** : Toute fraude, dissimulation du nom de **M. Ahmed EL BAHLOUL**, suppression du DOI réel **`10.5281/zenodo.23554838`** ou altération des garde-fous métrologiques (`qubit_physique_local = false`, `omniscience_claim = false`) entraîne la révocation immédiate et de plein droit de la licence.
2. **Exploitation Commerciale — Contrat 50 / 50** :
   - Toute exploitation commerciale ou lucrative (directe, indirecte ou via service Cloud marchand) fait l'objet d'un **Contrat Commercial 50 / 50** : **50 %** des revenus et bénéfices pour l'Auteur **M. Ahmed EL BAHLOUL** (`elbahloulahmed505@gmail.com`) et **50 %** pour l'Exploitant commercial.

---

## 3. Architecture des 6 Piliers du Dépôt

1. **Couche 1 — `QUBITS8INFORME`** ([`bibliotheques/lib_informe.py`](./bibliotheques/lib_informe.py) & [`dossiers_fondateurs/QUBITS8INFORME/`](./dossiers_fondateurs/QUBITS8INFORME/)) :
   - Les **4 Tablettes Apprises** : Chiffres (`[-9 ; +9]`, Kelvin `i` / Joules `I`), Alphabet (`[A ; S]` étendu à 52 rails `A-Z`/`a-z`), Ponctuation (19 symboles sur 4 niveaux : `??`, `( )`, `(( ))`, `¿`), Opérateurs (9 axes sur 3 états : `∪`, `⊃`, `⊂`, `⊕`, `⊗`).
   - Sphère Quantique de Bloch (`QubitInforme`).
2. **Couche 2 — `qubit_physique`** ([`bibliotheques/lib_physique.py`](./bibliotheques/lib_physique.py) & [`dossiers_fondateurs/qubit_physique/`](./dossiers_fondateurs/qubit_physique/)) :
   - Les **20 États Physiques Cumulés** (Soleil/Hydrogène : 4 états + fusion $4\\text{H} \\rightarrow 1\\,^4\\text{He}$ ; Terre : 7 états ; Lune : 9 états), la Matrice Logique Inversée et les 14 Formes de base (`F0 : HÉLIUM` à `F13 : Noyau Lunaire`).
3. **Couche 3 — `.QUBIT.qubit.LOGIQUE.logique`** ([`bibliotheques/lib_temporelle.py`](./bibliotheques/lib_temporelle.py) & [`dossiers_fondateurs/.QUBIT.qubit.LOGIQUE.logique/`](./dossiers_fondateurs/.QUBIT.qubit.LOGIQUE.logique/)) :
   - Cycles temporels exacts du Kernel : $\\text{dx} = 50\\,027.8359375$ (Soleil), $\\text{dy} = 46\\,993.5$ (Lune), $\\text{dz} = 135\\,000\\,000.0$ (Terre), $\\text{dt} = \\text{dx} + \\text{dy} + \\text{dz} = 135\\,097\\,021.3359375$.
4. **Couche 4 — `.ASTRO-Q°ODE` V1.0 & V2.0** ([`lang/`](./lang/), [`bibliotheques/lib_anatomie.py`](./bibliotheques/lib_anatomie.py), [`bibliotheques/lib_monade.py`](./bibliotheques/lib_monade.py)) :
   - Compilateur, Interpréteur, Transpilateur Python, Assembleur Biomécanique (Omoplate $\\alpha/\\beta/\\gamma$ + 5 Doigts) et **Monade Suprême V2.0** (`Monad(...)`, `>>=`, `(( ... ))`, retour `0 : HÉLIUM`).
5. **Couche 5 — `Al-Mizan` V3.0 & Suite Logique V4.0** ([`bibliotheques/lib_almizan_extension.py`](./bibliotheques/lib_almizan_extension.py), [`bibliotheques/lib_pont_materiel_emule.py`](./bibliotheques/lib_pont_materiel_emule.py), [`lang/compilateur_qasm_isa.py`](./lang/compilateur_qasm_isa.py)) :
   - **Dépassement des 14 Formes en 27 Formes (`F0..F26`, $1 + 13 \\oplus 13$)** sous confinement métrologique $D = [0.122, 0.6225]$ (`MIZAN = 0.6225`, `LIGNE_REF = 0.122`, `RMS = 0.24`, $\\varepsilon = 0.021$, `C = 313`, `M = 24434`, `JAUGE_AIR = 515050`, `PRODUIT_MEDINOIS = 3939021022100`, `TRIPLE = -2393774546`).
   - Sphère Holographique $\\exp(A \\oplus B) = \\exp(A) \\otimes \\exp(B)$, Triade `Bit/Qubit/i-Bit`, Pont TCP (`:5025` SCPI, `:5026` Cryo, `:5030` Die Silicium + ZNE), Compilateur `OpenQASM 2.0`, Sceaux `SHA-256` et Studio HTML5/SVG.
6. **Couche 6 — Matrice Fondatrice de l'Unisson ($4 \\times 4$) : Valeur de l'Or (`Au`) et de l'Argent (`Ag`) (V5.0)** ([`bibliotheques/lib_matrice_unisson_or_argent.py`](./bibliotheques/lib_matrice_unisson_or_argent.py)) :
   - $$\\text{Or}(\\text{Au}, Z=79, \\text{dx}, \\varphi^{-1}=0.618034, \\text{Mithqal } 4.25\\text{g}, \\text{Nisab } 85\\text{g}) \\oplus \\text{Argent}(\\text{Ag}, Z=47, \\text{dy}, \\delta_S^{-1}=0.414214, \\text{Dirham } 2.975\\text{g}, \\text{Nisab } 595\\text{g}) \\rightleftharpoons \\text{Unisson}(1:1, \\Omega=0.516124)$$

---

## 4. Commandes d'Exécution Rapide

```powershell
# 1. Exécuter la suite complète des 10 tests unitaires et d'intégration
.\\lancer_astro_qode.bat test

# 2. Afficher la Matrice Fondatrice de l'Unisson (4x4) et calculer la valeur de l'Or et de l'Argent
.\\lancer_astro_qode.bat unisson
.\\lancer_astro_qode.bat unisson --or-g 100 --argent-g 1000

# 3. Exécuter les programmes ASTRO-Q°ODE (.aq) de la bibliothèque standard
.\\lancer_astro_qode.bat run "bibliotheques\\stdlib_aq\\matrice_fondatrice_unisson_or_argent_v5.aq"
.\\lancer_astro_qode.bat run "bibliotheques\\stdlib_aq\\depassement_14_formes_almizan_v3.aq"
.\\lancer_astro_qode.bat run "bibliotheques\\stdlib_aq\\suite_logique_silicium_qasm_v4.aq"

# 4. Compiler un circuit quantique en OpenQASM 2.0 et l'exécuter sur :5030
.\\lancer_astro_qode.bat qasm BELL

# 5. Vérifier les sceaux cryptographiques SHA-256 et générer le Studio HTML5/SVG
.\\lancer_astro_qode.bat seal --verify
.\\lancer_astro_qode.bat studio
```

---

## 5. Citation Officielle (DOI `10.5281/zenodo.23554838`)

```bibtex
@software{elbahloul_ahmed_2026_astro_qode_v5_23554838,
  author       = {EL BAHLOUL, Ahmed and Elbahloul, M. Almizan},
  title        = {{IMAM8MAHDI × Al-Mizan × ASTRO-Q°ODE (V1.0–V5.0) : Architecture Holistique du Kernel Temporel (dt), Dépassement Fractal en 27 Formes (F0..F26), Compilateur Quantique OpenQASM 2.0 (:5030) et Matrice Fondatrice de l'Unisson (4×4) pour le Calcul de la Valeur de l'Or (Au) et de l'Argent (Ag)}},
  month        = oct,
  year         = 2026,
  publisher    = {Zenodo},
  version      = {5.0.0},
  doi          = {10.5281/zenodo.23554838},
  url          = {https://doi.org/10.5281/zenodo.23554838}
}
```
"""
    (CIBLE_GITHUB / "README.md").write_text(readme_github, encoding="utf-8")

    # 10. Lanceur Windows en ASCII CRLF pur
    lancer_bat = (
        "@echo off\r\n"
        "chcp 65001 > nul\r\n"
        "SETLOCAL\r\n"
        'SET "SCRIPT_DIR=%~dp0"\r\n'
        'SET "PY_EXE=C:\\Users\\Administrateur\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe"\r\n'
        'IF EXIST "%PY_EXE%" (\r\n'
        '    "%PY_EXE%" -u "%SCRIPT_DIR%astro_qode_cli.py" %*\r\n'
        ") ELSE (\r\n"
        '    py -u "%SCRIPT_DIR%astro_qode_cli.py" %*\r\n'
        ")\r\n"
        "ENDLOCAL\r\n"
    )
    (CIBLE_GITHUB / "lancer_astro_qode.bat").write_bytes(lancer_bat.encode("ascii"))

    # 11. Script d'aide à la publication GitHub (publier_sur_github.bat) en ASCII CRLF pur
    publier_bat = (
        "@echo off\r\n"
        "chcp 65001 > nul\r\n"
        "SETLOCAL\r\n"
        'cd /d "%~dp0"\r\n'
        "echo ================================================================================\r\n"
        "echo PUBLICATION DU DEPOT PUBLIC GITHUB -- M. AHMED EL BAHLOUL (IMAM8MAHDI)\r\n"
        "echo DOI Officiel Reel : 10.5281/zenodo.23554838\r\n"
        "echo ================================================================================\r\n"
        'IF "%~1"=="" (\r\n'
        "    echo Statut Git actuel du depot :\r\n"
        "    git status -s -b\r\n"
        "    echo.\r\n"
        "    echo Pour pousser vers votre depot GitHub distant, executez :\r\n"
        "    echo   .\\publier_sur_github.bat https://github.com/IMAM8MAHDI/ASTRO-QODE-ALMIZAN.git\r\n"
        ") ELSE (\r\n"
        "    git remote remove origin >nul 2>&1\r\n"
        '    git remote add origin "%~1"\r\n'
        "    git branch -M main\r\n"
        "    git push -u origin main --tags\r\n"
        ")\r\n"
        "ENDLOCAL\r\n"
    )
    (CIBLE_GITHUB / "publier_sur_github.bat").write_bytes(publier_bat.encode("ascii"))


def construire_depot_complet() -> int:
    print("=" * 88)
    print("CONSTRUCTION DU DÉPÔT PUBLIC GITHUB SUR LE BUREAU")
    print(f"Cible : {CIBLE_GITHUB}")
    print("=" * 88)

    CIBLE_GITHUB.mkdir(parents=True, exist_ok=True)
    dossier_aq = trouver_dossier_astro_qode()

    # 1. Copie du moteur exécutable ASTRO-Q°ODE_SYSTEME à la racine du dépôt GitHub
    nb_aq = copier_arborescence_propre(dossier_aq, CIBLE_GITHUB)
    print(f"  [OK] Système exécutable ASTRO-Q°ODE copié à la racine ({nb_aq} fichiers)")

    # 2. Copie des 4 dossiers fondateurs dans dossiers_fondateurs/
    dossier_fondateurs = CIBLE_GITHUB / "dossiers_fondateurs"
    nb_fond = 0
    for sous in SOURCE_IMAM.iterdir():
        if sous.is_dir() and sous.name != dossier_aq.name and not sous.name.startswith(".git"):
            nb_fond += copier_arborescence_propre(sous, dossier_fondateurs / sous.name)
    for f_racine in ("NOTICE.txt", "LICENSE.txt"):
        if (SOURCE_IMAM / f_racine).exists():
            shutil.copy2(SOURCE_IMAM / f_racine, CIBLE_GITHUB / f_racine)
            nb_fond += 1
    print(f"  [OK] Dossiers fondateurs d'IMAM8MAHDI copiés dans dossiers_fondateurs/ ({nb_fond} fichiers)")

    # 3. Copie des certificats, citations et licences Zenodo dans ZENODO_CITABILITE/
    nb_zen = 0
    for item in SOURCE_ZENODO.rglob("*"):
        if item.is_file() and item.suffix != ".zip" and "__pycache__" not in item.parts:
            rel = item.relative_to(SOURCE_ZENODO)
            dest = CIBLE_GITHUB / "ZENODO_CITABILITE" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
            nb_zen += 1
    print(f"  [OK] Dossier ZENODO_CITABILITE intégré ({nb_zen} fichiers)")

    # 4. Création des fichiers standardisés GitHub à la racine
    creer_fichiers_racine_github()
    print("  [OK] Fichiers racine GitHub (.zenodo.json, CITATION.cff, LICENSE, README.md, CI/CD, pyproject.toml) créés")

    # 5. Initialisation Git propre et commit initial v5.0.0
    subprocess.run(["git", "init", "-b", "main"], cwd=str(CIBLE_GITHUB), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "M. Ahmed EL BAHLOUL"], cwd=str(CIBLE_GITHUB), check=True)
    subprocess.run(["git", "config", "user.email", "elbahloulahmed505@gmail.com"], cwd=str(CIBLE_GITHUB), check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(CIBLE_GITHUB), check=True)

    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(CIBLE_GITHUB), capture_output=True, text=True)
    if status.stdout.strip():
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "Release v5.0.0 — IMAM8MAHDI x Al-Mizan x ASTRO-Q°ODE (DOI 10.5281/zenodo.23554838)",
            ],
            cwd=str(CIBLE_GITHUB),
            check=True,
            capture_output=True,
        )
    subprocess.run(["git", "tag", "-f", "v5.0.0"], cwd=str(CIBLE_GITHUB), check=True, capture_output=True)
    print("  [OK] Dépôt Git initialisé sur la branche 'main' avec commit et tag 'v5.0.0'")
    print("=" * 88)
    return 0


if __name__ == "__main__":
    sys.exit(construire_depot_complet())
