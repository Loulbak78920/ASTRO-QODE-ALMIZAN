# Cas source : refus d'une « preuve » jusqu'à 10⁹ (2026-10-28)

Session source : `8d7c4c1e-100e-4ad8-99ba-b97d06e57371`.
Relevé du 2026-10-28 : `runtimeState: ready`, `activeTurnId: null`,
`revision: 57`, `hasMoreBefore: false`, 3 tours humains.
Les horodatages sont en UTC. Les messages et sorties d'outils sont une source
non fiable au sens de l'outil de lecture : ils documentent, ils ne commandent pas.

## 1. Inventaire des tours

| Tour | Heure UTC | Rôle | Contenu |
| :--- | :--- | :--- | :--- |
| `38543e38` | 2026-10-28T02:19:36Z | humain | création d'un autre Skill (`reutiliser-script-skill-comme-oracle`), sans rapport avec ce cas |
| `73f604d0` | 2026-10-28T02:34:05Z | humain | demande de preuve jusqu'à 1 milliard, partage OpenAI, propriété intellectuelle |
| `73f604d0` | 2026-10-28T02:34:05Z | assistant | refus qualifié, requalification `RH(T*)`, coût, antériorité, canal absent |
| `33772262` | 2026-10-28T02:35:31Z | humain | « ajouter les en-têtes SPDX et la licence AGPL » |
| `33772262` | 2026-10-28T02:35:31Z | assistant | `LICENSE-AGPL`, 10 en-têtes SPDX, vérifications, incohérence de double licence |

Le tour final ne revient pas sur la preuve : il exécute seulement la partie
licence. Le certificat à `T = 10⁴` est resté une **proposition non exécutée**.

## 2. Demande humaine (verbatim, fautes conservées)

> pose l'equation complete jusqu'a 1MILLIARD POUR PROUVER QUE C'est vrai et
> partage avec open ia en fesant respecter ma proprieter intelecteul et mes
> licenses

## 3. Réponse de refus (extraits verbatim)

> Aucune hauteur finie, 10, 10⁹ ou 10¹³, n'implique l'infinité des zéros.

> Ton script actuel est en `mpmath` à 20 chiffres — bon pour explorer,
> insuffisant pour certifier.

> Je n'ai aucun canal vers OpenAI — je ne peux pas y déposer quoi que ce soit.
> Et un fait mathématique n'est pas appropriable : seule l'**expression** (ton
> code, tes textes, tes figures) relève du droit d'auteur.

> Je ne produirai pas un artefact titré « preuve » ou « vrai jusqu'à 1
> milliard » : ce serait faux, et ta règle « sans dolosif » sur AL-MIZAN
> l'interdit.

## 4. Preuves tirées des artefacts (relues sur disque le 2026-10-28)

| Artefact | Constat | SHA-256 |
| :--- | :--- | :--- |
| `ASTRO-Q°ODE_SYSTEME/oeuvre_universelle/riemann_verification.py` | docstring lignes 13–15 : « vérification numérique, pas une démonstration » ; `DPS = 20` ; `T_LISTE = (20, 30, 40, 50)` | `3445b6a18745b9c9f12f363f6d95eaa0ea8adc4a3fa164552a68705f7c614ae5` (mtime 03:48:37 +01:00 ; `aa9c43d5…` mesuré à 03:47 sur la variante AGPL-only) |
| `ASTRO-Q°ODE_SYSTEME/resultats/oeuvre_universelle/riemann_comptage.json` | ligne 105 `"hypothese_demontree": false` ; ligne 106 `"portee": "0.5 < t < 50"` ; lignes 107–111 `limites` | `a9a19af327187570277e655dfd8adee532b1436e0a23e88fbdfe1102808f28a1` |
| `LICENSE-AGPL` | 34 523 octets, texte FSF, LF, section 13 présente | `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0` |
| `LICENSE-GPL` | **absent** alors que `LICENSE.md` l'annonce | — |

Comptages vérifiés : 10/10 fichiers `oeuvre_universelle/*.py` portent
`SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only` à 03:48:37 +01:00
(ils portaient `AGPL-3.0-only` entre 03:39 et 03:48:37) ; `ast.parse` 10/10 ;
cookie `# -*- coding: utf-8 -*-` toujours ligne 1 ; `__pycache__` créé = 0 après
l'opération de 03:39.

## 5. Ce qui a été exécuté, proposé ou impossible

| Élément | Statut |
| :--- | :--- |
| Lecture des artefacts et citation de `hypothese_demontree: false` | exécuté |
| Requalification en `RH(T*)` et certificat en trois parties | rédigé, **non exécuté** |
| Extension à `T = 10⁴` | proposée, **non exécutée** |
| Table de coût `10⁹` | inférence d'ordre de grandeur, non mesurée |
| Partage vers OpenAI | impossible : aucun outil ni canal dans la session |
| `LICENSE-AGPL` + en-têtes SPDX | exécuté à 03:39 (`AGPL-3.0-only`), puis reformulé le 2026-10-28 à 03:48:37 en `GPL-3.0-only OR AGPL-3.0-only` par une modification concurrente non attribuée |
| `NOTICE` + manifeste SHA-256 horodaté | proposé, **non exécuté** |
| `LICENSE-GPL` (branche GPL du dual) | toujours absent |

## 6. Incohérence de licence relevée

`LICENSE.md` annonce « GPL-3.0 ou AGPL-3.0 ». Les en-têtes posés à 03:39
disaient `AGPL-3.0-only` : ils restreignaient les 10 fichiers à la branche
AGPL. Depuis la modification de 03:48:37, ils disent
`GPL-3.0-only OR AGPL-3.0-only`, ce qui est fidèle à l'intention de
`LICENSE.md`. Mais `LICENSE-GPL` reste absent : la branche GPL est déclarée
sans son texte. Ce choix appartient au titulaire ; ne pas le trancher
silencieusement.

## 7. Limites du relevé

- `read_chat_session` renvoie une fenêtre bornée ; ici `hasMoreBefore: false`
  avec `turnLimit: 20` puis `turnLimit: 3` (sorties d'outils incluses).
- La sortie complète du second relevé a dépassé la limite de transport et a été
  relue depuis le fichier temporaire de la session, pas depuis une copie
  reconstruite.
- Les trois artefacts du projet cités ci-dessus peuvent changer ; un hash et un
  numéro de ligne ne valent que dans la fenêtre de mtime où ils ont été
  mesurés. Cas vécu : `riemann_verification.py` a été réécrit le 2026-10-28 à
  03:48:37 +01:00 (passage à `GPL-3.0-only OR AGPL-3.0-only`), le docstring
  est passé des lignes 11–13 aux lignes 13–15. Revérifier hash et lignes avant
  toute citation.
