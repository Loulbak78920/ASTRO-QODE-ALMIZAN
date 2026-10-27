# Cas 2026-10-26 — ressource déclarée manquante puis réparée

Date du cas : 2026-10-26 (UTC). Cible : `verifier-effets-de-bord-verification-lecture-seule`. Source : session `4701c87e-3202-4ca4-a411-06b46c0f89b2`.

## Objet et empreintes des artefacts

Toutes les heures de cette section sont locales, offset `+01:00`.

| Artefact | Taille (B) | mtime | SHA-256 complet |
|---|---:|---|---|
| `SKILL.md` de la cible (version utilisée par la preuve) | 15154 | 2026-10-26 13:29:08 | `6d755440b877d69484533eee0eba663abfb0f23dca54673364102f5fd3f6b632` |
| script d'instantané, version corrigée | 29761 | 2026-10-26 13:35:36 | `a500711817f826e03b0903cbb3aed78b73a2bbc638c919887f17578316723081` |
| protocole de restauration, version corrigée | 15676 | 2026-10-26 13:36:15 | `1de3f4edd8b7e7b3f489d7d83586588f4b706876efeab1b8b87fe7659481fff9` |
| cas antérieur de la cible, non modifié | 9792 | 2026-10-26 13:29:35 | `bf4a778a1868bbe548eb9ce7f3940970b1d07627fc65459c1f5799570fd8319c` |
| script d'instantané, version d'avant correctif | 29725 | 2026-10-26 13:19:16 | `be2b86b425b424aed034e980e400241a631830ebe4c1b74fecd7d9c781181e97` |
| protocole, version d'avant correctif | 15240 | 2026-10-26 13:19:33 | `fc2618d6f77d5a027f028fdc08081b4e106e8cf1a3cc4bb4fa6d69cf0517a290` |

## Source

| Champ | Valeur |
|---|---|
| `sessionId` | `4701c87e-3202-4ca4-a411-06b46c0f89b2` |
| `revision` | 25 |
| `runtimeState` | running |
| `activeTurnId` | `412b9107-4374-4d65-b70a-38fd48c8d3ac` |
| Requête associée à `activeTurnId` | « commit les changements », message du 2026-10-26T12:36:55.785Z |
| `hasMoreBefore` | false |
| Messages retournés | 8 |
| Lecture effectuée | 2026-10-26T12:52:50Z (UTC), soit 13:52:50 `+01:00` |
| Sortie brute conservée | `C:\Users\Administrateur\.qoder\tmp\C--Users-Administrateur-Desktop-IMAM8MAHDI\56a83cc8-eb8f-4057-800e-785c02740f34\tool-results\builtin_read_chat_session_8a675cff5fd8.txt` |

Le tour de réparation est `9517b8a5-f05c-4e9e-842d-64243d32c9ef`, marqué `completed`. `runtimeState: running` ne décrit donc que le tour de commit, postérieur ; il ne prouve pas que la réparation était encore en cours d'écriture.

## Chronologie

Heures locales `+01:00`, avec l'équivalent UTC.

| Élément | Local (+01:00) | UTC |
|---|---|---|
| Création des deux ressources (script, protocole) | 13:19:16 / 13:19:33 | 12:19:16 / 12:19:33 |
| Réécriture du `SKILL.md` de la cible | 13:29:08 | 12:29:08 |
| Écriture du cas antérieur de la cible | 13:29:35 | 12:29:35 |
| Message utilisateur « 继续修复 … 的缺失文件 » | 13:31:20 | 12:31:20 |
| Observation d'un index de sceaux mis à jour par un écrivain externe | 13:32:09 | 12:32:09 |
| Premier passage de la suite de fixtures (fenêtre bornée) | entre 13:31:20 et 13:35:36 | entre 12:31:20 et 12:35:36 |
| Correctif du script | 13:35:36 | 12:35:36 |
| Correctif du protocole | 13:36:15 | 12:36:15 |
| Message utilisateur « commit les changements » | 13:36:55 | 12:36:55 |
| Dépôt Git de la cible créé par une autre session (observé) | 13:44–13:45 | 12:44–12:45 |
| Ré-échantillonnage de contrôle lors de la rédaction | 13:52:50 | 12:52:50 |

## Sorties verbatim

### Re-inventaire après l'annonce de « fichiers manquants »

```text
f      15154 2026-10-26 13:29:08.3174832000 ./SKILL.md
f       9792 2026-10-26 13:29:35.5637706000 ./references/cas-entite-2026-10-26.md
f      15240 2026-10-26 13:19:33.9686456000 ./references/protocole-restauration.md
f      29725 2026-10-26 13:19:16.5085727000 ./scripts/instantane_effets_de_bord.py
```

Les deux ressources déclarées manquantes étaient présentes, avec un mtime postérieur au rapport qui affirmait leur absence.

### Double échantillon avant édition

```text
be2b86b425b424aed034e980e400241a631830ebe4c1b74fecd7d9c781181e97 *scripts/instantane_effets_de_bord.py
fc2618d6f77d5a027f028fdc08081b4e106e8cf1a3cc4bb4fa6d69cf0517a290 *references/protocole-restauration.md
---SECOND_SAMPLE---
29725 1793017156.5085727000 scripts/instantane_effets_de_bord.py
15240 1793017173.9686456000 references/protocole-restauration.md
be2b86b425b424aed034e980e400241a631830ebe4c1b74fecd7d9c781181e97 *scripts/instantane_effets_de_bord.py
fc2618d6f77d5a027f028fdc08081b4e106e8cf1a3cc4bb4fa6d69cf0517a290 *references/protocole-restauration.md
```

### Schéma réel du journal

```text
journal keys of last entry: ['chemin_fichier', 'lignes_totales', 'arbre_ast_valide', 'respect_bride_mizan', 'respect_anti_riba', 'respect_killswitch_cryo', 'detecte_fragmentation', 'score_harmonie_100', 'empreinte_sha256', 'recommandations_harmonisation', 'horodatage_iso']
horodatage_iso sample: 2026-10-26T12:31:19Z
chemin_fichier sample: moteur_intelligence_generative_vivante.py
index seal keys: ['timestamp', 'empreinte_sha256', 'chemin']
```

### Premier passage de la suite : échecs

```text
FAIL snapshot journal 100 + signatures :: {"longueur": 100, "signatures": {}, "sans_signature": 100, "distribution": {}, "empreinte": "618691ed6491137f9a2fb56ffd082bdcf90de41aa62eeb5730c36c49ec50b50d"}
FAIL ATTENTION eviction longueur inchangee :: ...
FAIL AJOUTE entrees journal :: ...
FAIL 5 signatures disparues :: ...
TOTAL=34 ECHECS=4
HARNESS_EXIT=1
```

Les quatre échecs partagent la même cause : l'extraction était vide sur une source non vide. Ce ne sont pas quatre défauts indépendants.

### Après correctif : suite complète

```text
PASS ATTENTION eviction longueur inchangee
PASS AJOUTE entrees journal
PASS 5 signatures disparues
TOTAL=34 ECHECS=0
HARNESS_EXIT=0
```

### Re-preuve en lecture seule sur les données réelles

```text
[OK] instantane: 184 fichier(s), 183 JSON
RESULT: OK
INSTANTANE_EXIT=0
fichiers: 184 | stable: True
journal longueur: 100 | signatures: 100 | sans_signature: 0
distribution: {'2026-10-26T12:24:31Z': 22, '2026-10-26T12:24:52Z': 29, '2026-10-26T12:24:53Z': 47, '2026-10-26T12:27:52Z': 1, '2026-10-26T12:31:19Z': 1}
index sceaux: 14 | nb_sceaux: 14 | maj: 2026-10-26T13:32:09
---COMPARER---
RESULT: OK
COMPARER_EXIT=0
```

### Acceptation statique et nettoyage

```text
PASS layout: 4 file(s), no extraneous documentation
PASS frontmatter: YAML parsed (PyYAML 6.0.3)
PASS name: 'verifier-effets-de-bord-verification-lecture-seule' matches directory
PASS description: single line, 741 chars
PASS body: 156 lines (< 500)
PASS fingerprint: unchanged during validation
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
exit=0
```

```text
CLEANED
NO_RESIDUE
```

## Prémisse corrigée

| Assertion d'origine | Constat sur disque | Correction appliquée |
|---|---|---|
| « Les deux fichiers déclarés sont manquants ; il faut les créer. » | Script 29725 B et protocole 15240 B présents, mtimes 13:19:16 et 13:19:33 ; `SKILL.md` réécrit à 13:29:08. | Aucun fichier recréé ; audit puis correctif. |
| « Le journal n'a pas de signature exploitable. » | Le journal réel emploie `horodatage_iso` et `chemin_fichier` ; les alias du script ne les couvraient pas. | Alias ajoutés dans le script et dans le modèle `signature()` du protocole, plus une ligne de piège. |
| « Quatre assertions échouent indépendamment. » | `signatures: {}` et `sans_signature: 100` expliquent les quatre échecs. | Une seule cause corrigée, suite complète repassée à zéro échec. |

## Niveaux de preuve

| Fait | Niveau | Justification |
|---|---|---|
| Les deux ressources étaient présentes au re-inventaire | vérifié | Listing avec tailles et mtimes |
| Elles ont été écrites par une autre session à 13:19 | inféré | Mtimes postérieurs au rapport d'absence ; aucun auteur identifié dans la sortie |
| Le `SKILL.md` de la cible a été réécrit à 13:29 | vérifié | mtime 13:29:08 ; auteur non identifié |
| Double échantillon identique avant édition | vérifié | Deux hashes identiques, tailles identiques |
| Le journal réel utilise `horodatage_iso` et `chemin_fichier` | vérifié | Sortie des clés de la dernière entrée |
| La suite a échoué sur une extraction vide | vérifié | Ligne `FAIL` et totaux |
| Le correctif d'alias a produit zéro échec | vérifié | `TOTAL=34 ECHECS=0`, `HARNESS_EXIT=0` |
| 100 entrées réelles, 100 signatures, 0 sans signature | vérifié à 13:3x | Sortie de la re-preuve |
| `skill-file-qa` PASS sur le `SKILL.md` de 15154 B | vérifié | Sortie du validateur et empreinte |
| Un écrivain externe modifiait encore les données réelles | vérifié comme observation | `maj: 2026-10-26T13:32:09` pendant l'audit ; attribution non prouvée |
| Le tour de réparation était encore actif pendant la rédaction | non vérifié | `activeTurnId` correspond au tour de commit, pas au tour de réparation |

## Limites

- Aucun identifiant de session ne prouve qui a écrit les fichiers à 13:19 ; seule la chronologie des mtimes le suggère.
- Les heures exactes des commandes ne sont pas horodatées individuellement ; seules les bornes fournies par les mtimes et les messages le sont.
- La version de Python n'est pas consignée dans les sorties.
- Les compteurs réels (184 fichiers, 100 entrées, index à 14) sont des observations datées. L'index a ensuite été réécrit par un processus externe ; ces valeurs ne sont pas des constantes.
- La re-preuve réelle n'a pas restauré ni modifié les données ; elle ne prouve pas l'absence d'écritures par d'autres processus après 13:36.

## État disque au moment de la rédaction

Contrôle effectué le 2026-10-26T12:52:50Z (13:52:50 `+01:00`) :

- Les quatre empreintes de la cible sont inchangées par rapport à la version corrigée.
- Les alias `horodatage_iso` et `chemin_fichier` sont présents dans le script (lignes 30–31) et dans le protocole (lignes 151 et 156).
- Un dépôt Git a été créé dans le dossier de la cible à 13:44–13:45 par une autre session ; le commit observé est `ddd3246`.
- Aucun de ces éléments n'a été modifié par la présente rédaction.

## Complément — seconde lecture de la source

Seconde lecture effectuée le 2026-10-26T12:57:14Z, soit 13:57:14 `+01:00`.

| Champ | Valeur |
|---|---|
| `revision` | 40 |
| `runtimeState` | ready |
| `activeTurnId` | null |
| `hasMoreBefore` | true |
| Dernier tour retourné | `8e832a09-016f-4d81-9366-758574303ea1` |
| Requête | « 跑一下 verifier-effets-de-bord-verification-lecture-seule 确认修复有效 » |
| Horodatage du tour | 2026-10-26T12:46:12.715Z |
| Statut | completed |

Ce tour est absent du premier snapshot (revision 25) ; la sortie ne permet pas d'expliquer cet écart. Il n'infirme aucun fait établi ci-dessus : il ajoute une vérification indépendante du correctif.

### Contrôle A/B

Fixture : deux sceaux et 100 entrées aux clés réelles, puis cinq ajouts et une troncature à 100, soit cinq évictions sans changement de longueur.

| Version | Signatures sur 100 entrées | Détection des cinq entrées évincées |
|---|---|---|
| AVANT (alias retirés) | `signatures=0 sans_signature=100` | aucune ligne `[ATTENTION]` ; seulement « contenu de la liste journal change (signatures identiques) » |
| APRÈS (version commitée) | `signatures=100 sans_signature=0` | `[ATTENTION] … 5 entree(s) disparue(s) dans journal (longueur inchangee: eviction possible)` et `[AJOUTE] … 5 entree(s)` |

Le harnais A/B rapporte `RESULT: TOTAL=11 ECHECS=0`. Les deux versions rendent un code 1 pour la comparaison : la différence n'est pas le code de sortie, mais la capacité à localiser les cinq signatures évincées.

### Contrôle réel et état

- `instantane` sur les données réelles : 184 fichiers, 183 JSON, `RESULT: OK`, `comparer: RESULT: OK` avec `EXIT=0`.
- Journal : `longueur=100 signatures=100 sans_signature=0`, `total_fichiers_harmonises=100`.
- Index : `nb_sceaux=14`, `sceaux=14`, `derniere_mise_a_jour=2026-10-26T13:32:09`.
- Commit `ddd3246`, `git status` vide, aucun `__pycache__` ni `.pyc`.
- Les quatre empreintes relevées correspondent à celles du tableau ci-dessus.

### Limites ajoutées

- Les valeurs de cette section proviennent du rapport final du tour `8e832a09…` ; les sorties d'outils correspondantes n'étaient pas incluses dans le snapshot. Elles sont classées « rapport du tour », non « sortie verbatim ».
- Le comportement de la version sans alias a été reproduit sur fixture, pas sur le journal réel : le rejouer sur les données réelles aurait exigé de les réécrire.
- `comparer: RESULT: OK` prouve la cohérence entre l'instantané et l'état courant, pas l'absence d'écritures temporaires entre les deux mesures.
- Le second snapshot est `ready` avec `activeTurnId: null` ; il ne prouve pas l'état de la session entre les deux lectures.

## Complément — dérive observée après la rédaction (2026-10-26)

Ajout append-only : les sections précédentes restent vraies pour les instants qu'elles datent. Les deux contrôles ci-dessous montrent que le paquet audité a continué d'évoluer après le contrôle de 13:52:50.

### Contrôle du 2026-10-26T12:59:25Z (13:59:25 +01:00)

- `scripts/tester_instantane.py` : 24235 B, mtime 13:58:50 +01:00, SHA-256 `6184122ec59f21afb7489253b03d63d4e4ea542be017e256920174a1f8d5c924`.
- Fichier non suivi (`??`) dans le dépôt Git de la cible, absent du contrôle de 13:52:50 ; ni créé ni modifié par la présente rédaction.
- `SKILL.md`, `scripts/instantane_effets_de_bord.py` et `references/cas-entite-2026-10-26.md` inchangés à cet instant.

### Contrôle du 2026-10-26T13:00:31Z (14:00:31 +01:00)

| Fichier | Taille | mtime (+01:00) | SHA-256 |
|---|---:|---|---|
| `SKILL.md` | 15154 | 13:29:08 | `6d755440b877d69484533eee0eba663abfb0f23dca54673364102f5fd3f6b632` |
| `scripts/instantane_effets_de_bord.py` | 29761 | 13:35:36 | `a500711817f826e03b0903cbb3aed78b73a2bbc638c919887f17578316723081` |
| `scripts/tester_instantane.py` | 24235 | 13:58:50 | `6184122ec59f21afb7489253b03d63d4e4ea542be017e256920174a1f8d5c924` |
| `references/protocole-restauration.md` | 15932 | 14:00:20 | `662cad6812045998e433c80e0017605023d77844f2ffcd521a96bf028bf70bc4` |
| `references/cas-entite-2026-10-26.md` | 9792 | 13:29:35 | `bf4a778a1868bbe548eb9ce7f3940970b1d07627fc65459c1f5799570fd8319c` |

- `git status --porcelain` rend `M references/protocole-restauration.md` et `?? scripts/tester_instantane.py` ; `HEAD` reste `ddd3246`.
- Le protocole est donc passé de 15676 B (`1de3f4ed…`, 13:36:15) à 15932 B (`662cad68…`, 14:00:20). Le tableau d'empreintes en tête de ce fichier décrit la version utilisée par la preuve, pas l'état courant.
- La session source reste en `revision` 41, `runtimeState: ready`, `activeTurnId: null`, même dernier tour retourné `8e832a09…` (12:46:12.715Z). La dérive du protocole n'est donc pas expliquée par un tour supplémentaire visible dans cette fenêtre.

### Conséquences pour la lecture de ce fichier

- Les affirmations « les quatre empreintes sont inchangées » valent pour le contrôle de 13:52:50 seulement.
- Un écrivain externe modifie encore le paquet audité ; toute empreinte de ce fichier est une observation datée, jamais une constante.
- L'auteur de ces deux écritures n'est pas identifié dans les sorties ; la coïncidence temporelle avec la session source est une inférence, non un fait vérifié.
