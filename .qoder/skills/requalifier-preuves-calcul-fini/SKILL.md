---
name: requalifier-preuves-calcul-fini
description: "Requalifier une demande de « preuve » mathématique par calcul fini (hypothèse de Riemann jusqu'à 10⁹, Collatz, conjecture du registre des problèmes du monde) sans produire de fausse preuve : lire l'artefact existant et citer ses marqueurs d'honnêteté (`hypothese_demontree: false`), reformuler en proposition bornée RH(T*) avec certificat en trois parties, chiffrer la hauteur et le coût, vérifier l'antériorité publiée en distinguant hauteur et nombre de zéros, refuser un canal externe inexistant, séparer fait mathématique et expression (SPDX, LICENSE, NOTICE, manifeste SHA-256), puis ne livrer qu'une échelle certifiable (T = 10³–10⁴) avec sa limite explicite. 中文触发：用计算证明数学猜想、证明到十亿、黎曼假设、Collatz、世界问题登记簿、分享给 OpenAI、知识产权与许可证、SPDX/AGPL、有限计算不等于证明。English: qualify a finite-computation claim, bounded RH(T*) certificate, zero count versus height, prior-art check, fact versus expression licensing."
---

# Requalifier une « preuve » par calcul fini

Une demande « prouve X jusqu'à N » sur une conjecture ouverte ne peut pas être
satisfaite par un calcul plus long. Ce Skill transforme la demande en une
proposition bornée, chiffrée, sourcée et sans dol, puis ne livre que l'échelle
réellement certifiable.

## Quand utiliser

- L'utilisateur demande de « prouver » l'hypothèse de Riemann, Collatz ou une
  conjecture du registre jusqu'à `10⁹`, `10¹²` ou « un milliard ».
- Un script et un JSON existent déjà et sont présentés comme une preuve.
- La demande inclut un partage externe (« OpenAI ») ou une revendication de
  propriété intellectuelle sur le résultat.
- Il faut étendre un calcul existant sans transformer une vérification en
  démonstration.

## Quand ne pas utiliser

- Publier un dossier d'antériorité caviardé : `publier-preuves-anteriorite-caviardees`.
- Sceller un manifeste SHA-256 ou Merkle : `sceller-manifeste-integrite-sans-circularite`.
- Requalifier les allégations d'un site public : `deployer-site-sans-dol-vps`.
- Rejouer un objet de preuve déjà livré (qubit Steane) : `qubit-logique-steane-preuves`.
- Décider des assertions à écrire dans un SKILL.md : `verify-skill-doc-claims-before-edit`.

## Invariants

1. Une hauteur finie ne prouve jamais l'infinité. Ne jamais titrer un artefact
   « preuve », « démontré » ou « vrai jusqu'à N ».
2. Conserver les marqueurs d'honnêteté de l'artefact : `hypothese_demontree: false`, `portee`, `limites`. Les citer avant de proposer quoi que ce soit.
3. Nommer l'unité : **hauteur** `T` ou **nombre de zéros** `N(T)`. Ne jamais
   comparer deux valeurs sans conversion.
4. Ne jamais inventer un canal externe. Sans outil disponible, dire « aucun
   canal », pas « partagé ».
5. Un fait mathématique n'est pas appropriable ; seule l'expression (code,
   textes, figures) relève du droit d'auteur.
6. Ne pas élargir un script existant avant d'avoir requalifié l'énoncé : un
   calcul plus long ne change pas la nature de la conclusion.

## Étape 0 — Lire l'artefact et citer ses propres marqueurs

Depuis la racine du workspace IMAM8MAHDI, localiser le script et le JSON du
projet, puis citer les lignes exactes :

```bash
grep -n "hypothese_demontree\|portee\|limites" \
  ASTRO-Q°ODE_SYSTEME/resultats/oeuvre_universelle/riemann_comptage.json
grep -n "vérification numérique, pas une démonstration" \
  ASTRO-Q°ODE_SYSTEME/oeuvre_universelle/riemann_verification.py
```

Constats du 2026-10-28 : `riemann_comptage.json` ligne 105 porte
`"hypothese_demontree": false` ; le docstring de `riemann_verification.py`,
lignes 13–15 (11–13 avant l'insertion des en-têtes SPDX), écrit « vérification
numérique, pas une démonstration ». `DPS = 20` et
`T_LISTE = (20, 30, 40, 50)` : le calcul s'arrête à `t = 50`. Les en-têtes
SPDX de ces fichiers ont changé pendant la rédaction du Skill : revérifier le
hash et les numéros de ligne avant de les citer.

Si un marqueur manque, c'est un défaut à corriger avant toute revendication.
Ne jamais présenter l'artefact comme plus fort que ce qu'il déclare.

## Étape 1 — Requalifier l'énoncé

Remplacer « prouver jusqu'à N » par une proposition bornée :

> `RH(T*)` : pour tout zéro `ρ = β + iγ` de `ζ` avec `0 < γ ≤ T*`, `β = 1/2`
> et le zéro est simple.

Le certificat tient en trois égalités : comptage `N(T*)` par principe de
l'argument borné ; un changement de signe de `Z(t)` par intervalle de Gram avec
règle de Rosser vérifiée ; égalité des deux comptages. Les étapes de comptage
exigent une arithmétique d'intervalle. Un calcul `mpmath` à 20 chiffres est
exploratoire, pas certifiant. Détail des formules :
`references/certificat-et-anteriorite.md`.

Annoncer explicitement ce que `RH(T*)` n'établit pas : rien au-delà de `T*`,
aucune éligibilité au prix Clay.

## Étape 2 — Chiffrer la demande

Lancer le script fourni depuis le répertoire de ce Skill (chemin donné par
l'injection `Base directory`), sortie ASCII, sans dépendance :

```bash
py -3 scripts/qualifier_portee.py --zeros 1e9
py -3 scripts/qualifier_portee.py --hauteur 1e4
py -3 scripts/qualifier_portee.py --table
```

Sortie réelle pour `--zeros 1e9` :

```text
mode=zeros
valeur_demandee=1e+09
hauteur_T=3.7187e+08
zeros_lisses_a_T=1e+09
evaluations_estimees=1e+09
classe_cout=decennies a un siecle
classe_cout_base=ordre de grandeur, non mesure
deja_publie=oui
couvert_par=van de Lune, te Riele, Winter (1986) (1.5e+09 zeros)
anteriorite_revendicable=non
```

Lire `hauteur_T`, `evaluations_estimees`, `deja_publie`, `couvert_par`. La
classe de coût est une inférence d'ordre de grandeur fondée sur le nombre
d'évaluations ; elle n'est pas mesurée. Ne jamais la présenter comme un
benchmark.

## Étape 3 — Vérifier l'antériorité avant toute revendication

Comparer après conversion, jamais sur les valeurs brutes :

| Source | Unité | Valeur | Équivalent |
| :--- | :--- | ---: | :--- |
| van de Lune et al. (1986) | zéros | 1,5×10⁹ | hauteur ≈ 5,45×10⁸ |
| Gourdon (2004) | zéros | 10¹³ | hauteur ≈ 2,45×10¹² |
| Platt–Trudgian (2021) | hauteur | 3×10¹² | ≈ 1,24×10¹³ zéros |

À `10⁹` zéros, la seule qualification honnête est **reproduction** : aucune
antériorité, aucune nouveauté. Refondre la recherche bibliographique si le
résultat est présenté comme actuel, et citer la source retenue.

## Étape 4 — Canal externe et propriété intellectuelle

- Aucun outil ne permet de déposer un fichier chez OpenAI dans cette session.
  Le dire et proposer un paquet que l'utilisateur diffusera lui-même.
- Séparer le fait (non appropriable) de l'expression (code, textes, figures).
- Poser les en-têtes SPDX après le cookie d'encodage, puis vérifier :

```python
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
```

Vérifier `ast.parse`, le cookie en ligne 1, et l'absence de `__pycache__`
créé par l'opération. La variante `AGPL-3.0-only` **restreint** un document qui
annonce « GPL ou AGPL » ; la forme fidèle est la ligne duale ci-dessus, et elle
exige un `LICENSE-GPL` réellement présent — vérifier son existence, pas sa
mention. Faire trancher le titulaire, ne pas choisir silencieusement. Pour le
`NOTICE` et le manifeste horodaté, déléguer à
`publier-preuves-anteriorite-caviardees` et
`sceller-manifeste-integrite-sans-circularite`.

## Étape 5 — Ne livrer qu'une échelle certifiable

| Livrable | Zéros | Statut |
| :--- | ---: | :--- |
| `T = 10³` | ≈ 649 | reproductible, sans antériorité |
| `T = 10⁴` | ≈ 10 143 | reproductible en dizaines de minutes, sans antériorité |
| `T = 10⁶` | ≈ 1,75×10⁶ | jours de calcul, sans antériorité |
| `10⁹` zéros | hauteur ≈ 3,72×10⁸ | décennies estimées, couvert depuis 1986 |

Le JSON livré conserve `hypothese_demontree: false`, `portee` et `limites`.
Séparer dans le rapport « vérifié par calcul sur [0, T] » de « démontré ».
Le certificat à `T = 10⁴` n'a jamais été exécuté dans la session source :
le présenter comme méthode, pas comme résultat.

## Modèle de rapport final

| Rubrique | Contenu |
| :--- | :--- |
| Demande initiale | citation exacte, sans la reformuler en promesse |
| Énoncé requalifié | `RH(T*)`, unité et plage |
| Hauteur et coût | sortie du script, classe marquée « ordre de grandeur » |
| Antériorité | source, unité, équivalent ; « reproduction » si couvert |
| Livré | échelle, fichier, marqueurs conservés |
| Non livré | preuve infinie, partage externe, revendication d'antériorité |

## Pièges

- `N(50) ≈ 9,42` (comptage lissé) alors que le projet trouve 10 zéros sous
  `t = 50` : le lissé n'est pas le comptage exact.
- `--hauteur 1e4` ne signifie pas 10⁴ zéros : le script donne 10 143.
- Platt–Trudgian annoncent une **hauteur** de 3×10¹², pas 3×10¹² zéros.
- Un pas de scan plus fin ou une boucle plus longue ne prouve rien de plus.
- « Partagé avec OpenAI » est faux : aucun canal n'existe dans la session.
- Le certificat `T = 10⁴` est une proposition non exécutée.
- `mpmath` à 20 chiffres ne remplace pas l'arithmétique d'intervalle.
- Un titre « preuve » rend l'artefact dolosif même si les nombres sont justes.
- Un fichier relu peut changer entre deux mesures : recalculer le hash et les
  numéros de ligne avant de citer (SPDX inséré puis expression modifiée le
  2026-10-28 pendant la rédaction).
- Sous Windows, `py -3` et sortie ASCII : la console est en cp1252.

## Checklist de fin

- [ ] Marqueurs de l'artefact cités avec fichier et ligne.
- [ ] Énoncé borné `RH(T*)` avec unité et plage.
- [ ] Coût chiffré par le script, classe marquée non mesurée.
- [ ] Antériorité vérifiée après conversion d'unité.
- [ ] Aucun canal externe inventé.
- [ ] Fait et expression séparés ; licence tranchée, pas supposée.
- [ ] Livrable avec `hypothese_demontree: false`, `portee`, `limites`.
- [ ] Aucun artefact titré « preuve » ou « vrai jusqu'à N ».

## Cas vérifié (2026-10-28)

Session `8d7c4c1e-100e-4ad8-99ba-b97d06e57371` : demande de preuve jusqu'à
1 milliard et de partage OpenAI ; la réponse a refusé le titre de preuve, cité
`hypothese_demontree: false`, proposé `RH(T*)`, puis exécuté uniquement la
partie SPDX/AGPL. Le certificat et l'extension à `T = 10⁴` sont restés non
exécutés. Détail et hashes : `references/requalification-riemann-2026-10-28.md`.

## Ressources

- `references/certificat-et-anteriorite.md` — énoncé, certificat, coût, records publiés, sources.
- `references/requalification-riemann-2026-10-28.md` — preuves de la session source, exécuté vs proposé.
- `scripts/qualifier_portee.py` — `--zeros`, `--hauteur`, `--table`, `--json` ; code retour 2 sur entrée invalide.
