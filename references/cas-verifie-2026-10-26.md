# Cas vérifié — parité document / script (session 8ed233aa, 2026-10-26)

## Source et méthode

- Session Qoder : `8ed233aa-6884-44d3-9dd7-d21a0217fe5e`, révision 102, `runtimeState` prêt, `hasMoreBefore=false`, un seul tour utilisateur, aucune correction utilisateur.
- Fichier brut : `C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/8ed233aa-6884-44d3-9dd7-d21a0217fe5e.jsonl` (361 lignes).
- Skill produit dans cette session : `retirer-depot-github-et-copie-locale` (dossier utilisateur).
- Les extraits de doc et de script ci-dessous proviennent des enregistrements `Write` du JSONL, pas d'un résumé. Les sorties QA et les empreintes proviennent des sorties d'outils enregistrées (lignes 255, 275, 317, 324, 329, 343, 348 du fichier de sortie extrait).
- Domaine : suppression d'un dépôt GitHub et/ou de sa copie locale. Aucun appel réseau n'a été exécuté dans la session ; les branches GitHub sont documentées, pas exercées.

## Chronologie vérifiée

| # | Événement | Preuve |
|---|---|---|
| 1 | Création du Skill cible avec `SKILL.md`, une référence et `scripts/verifier_copie_locale.py` | enregistrements `Write` du JSONL |
| 2 | `skill-file-qa` : 9 PASS, 0 FAIL, 0 WARN ; `SKILL.md` 15 292 B, SHA-256 `02c024e27128c4406c458f315a6b2a4ce3eef37e9b5fbf15b2acd10c7a99f197` | sortie QA, ligne 255 |
| 3 | Ajout de contenu à la référence ; second QA PASS : 9 PASS ; `SKILL.md` 15 478 B, SHA-256 `4f9bdeb7c91ba7f8d6c5b3ce91db8a723b44ee1a575932a55e01b1889f99ea92` | sortie QA, ligne 275 |
| 4 | Harnais de 12 fixtures exécuté : tous les cas passent alors que le défaut est encore présent | `Write` du harnais + `SUMMARY` sans échec |
| 5 | Correction du script et du harnais ; troisième QA PASS : 9 PASS ; `SKILL.md` 15 532 B, SHA-256 `bdb6ec34b89030e442dd05aed976140bfe59b769a01319028ca94830cbc1302e` | sortie QA, ligne 317 |
| 6 | Porte finale : `QA_FINAL_MATCH=True`, `FINAL_GATE=PASS`, trois fichiers `STABLE` | lignes 329 et 348 |

Les trois PASS intermédiaires portent sur la structure, pas sur le contrat. Le défaut a survécu à deux PASS avant d'être corrigé.

## Défaut exact

Le `SKILL.md` historique, section 5.3 « Vérifier la sauvegarde avant de supprimer », demandait d'attendre ces clés :

```text
CONTENT_HASH_MATCH=yes
SKILL_SHA256_MATCH=yes
HEAD_MATCH=yes
COMMITS_MATCH=yes
```

Le script initial ne les émettait pas. Il émettait uniquement les valeurs brutes :

```text
SRC_CONTENT_HASH=...
BAK_CONTENT_HASH=...
SRC_SKILL_SHA256=...
BAK_SKILL_SHA256=...
SRC_HEAD=...
BAK_HEAD=...
SRC_COMMITS=...
BAK_COMMITS=...
```

Constats mesurés sur la paire historique extraite :

- 23 clés uniques émises par `emit("KEY", …)` ;
- zéro occurrence de `MATCH` dans le script ;
- `SRC_STATUS_CLEAN` et `BAK_STATUS_CLEAN` présents, mais les quatre clés comparatives absentes.

Le vérificateur de parité appliqué à cette paire rend :

```text
DOC_KEYS=8
RUNTIME_KEYS=25
MATCHED=4
DOC_ONLY=4
RUNTIME_ONLY=21
OUT_OF_SCOPE=12
DOC_ONLY_KEY=COMMITS_MATCH | SKILL.md:169 | section=5.3 Vérifier la sauvegarde avant de supprimer
DOC_ONLY_KEY=CONTENT_HASH_MATCH | SKILL.md:167 | section=5.3 Vérifier la sauvegarde avant de supprimer
DOC_ONLY_KEY=HEAD_MATCH | SKILL.md:169 | section=5.3 Vérifier la sauvegarde avant de supprimer
DOC_ONLY_KEY=SKILL_SHA256_MATCH | SKILL.md:168 | section=5.3 Vérifier la sauvegarde avant de supprimer
RESULT=FAIL
HIST_EXIT=1
```

Après correction, sur le Skill réel :

```text
DOCS=2
DOC_KEYS=10
RUNTIME_KEYS=31
MATCHED=10
DOC_ONLY=0
RESULT=PASS
FIXED_EXIT=0
```

## Pourquoi le harnais de 12 cas n'a rien vu

Le premier harnais vérifiait `rc` et un ou deux textes par cas. Le cas baseline n'attendait que `RESULT PASS` ; aucun cas n'attendait les clés `*_MATCH`. Un script qui n'émet jamais une clé documentée passait donc 12/12.

Règle qui en découle : un cas positif doit assertir chaque clé normative de la branche, avec sa valeur exacte. Un cas négatif doit assertir la bascule de la clé concernée (`yes` → `no`) en plus du code de retour.

## Remède appliqué

1. Ajout d'une fonction `match_flag(a, b)` rendant `yes`, `no` ou `NA` (les deux côtés absents).
2. Émission de six clés comparatives : `FILES_MATCH`, `CONTENT_HASH_MATCH`, `SKILL_SHA256_MATCH`, `GIT_PRESENT_MATCH`, `HEAD_MATCH`, `COMMITS_MATCH`.
3. Intégration de ces clés dans la liste des échecs du script : une clé affichée mais absente de la décision laisserait passer un faux PASS.
4. Extension du harnais : le baseline et chaque négatif attendent désormais les paires exactes.
5. Mise à jour du `SKILL.md` et de la référence dans le même passage.

Les promesses de la section 5.3 sont restées identiques : elles sont devenues vraies. Aucune promesse n'a été supprimée pour faire passer le script.

## Matrice de fixtures de la session source

| # | Cas | Attendu |
|---|---|---|
| 1 | baseline, source et sauvegarde identiques | rc 0, `RESULT PASS`, six `*_MATCH=yes` |
| 2 | contenu de la sauvegarde modifié | rc 1, `CONTENT_HASH_MATCH=no`, `SKILL_SHA256_MATCH=no` |
| 3 | source absente | rc 2, `ERROR=` |
| 4 | worktree sale des deux côtés | rc 1, `source worktree is dirty` |
| 5 | sauvegarde à l'intérieur de la source | rc 1, `backup is inside source` |
| 6 | paire sans dépôt Git | rc 0, `GIT_PRESENT_MATCH=yes`, `HEAD_MATCH=NA`, `COMMITS_MATCH=NA` |
| 7 | mode absence, cible déjà supprimée | rc 0, `TARGET_EXISTS=no`, `REMAINING_COPIES=0` |
| 8 | mode absence, copie homonyme restante | rc 1, `same-name copies remain`, `REMAINING_COPIES=1` |
| 9 | mode absence, cible toujours présente | rc 1, `target still exists` |
| 10 | sauvegarde vide | rc 1, `backup is empty` |
| 11 | racine de skills inexistante | rc 2, `skills root does not exist` |
| 12 | cible jonction | rc 1, `symbolic link or junction`, sinon `CASE SKIP` explicite |

Les cas 7 à 10 prouvent que la branche `NA` du cas 6 n'est pas une omission : les clés Git sont émises avec `NA`, jamais supprimées.

## Piège Windows observé

Le nettoyage de la fixture a échoué avec `PermissionError [WinError 5]` sur des objets `.git` en lecture seule. Remède : `force_rmtree` qui applique `chmod` aux dossiers (`0o777`) et fichiers (`0o666`) avant `shutil.rmtree`. Le code du modèle est dans `harnais-fixtures.md`.

## Empreintes finales du Skill cible

| Fichier | Taille | SHA-256 |
|---|---|---|
| `SKILL.md` | 15 532 B | `bdb6ec34b89030e442dd05aed976140bfe59b769a01319028ca94830cbc1302e` |
| `references/cas-verifie-2026-10-26.md` | 9 441 B | `f7344cd600cd0d8e080713cc0d0a2ca655e687bbf08ca694c389561c9a3a26f0` |
| `scripts/verifier_copie_locale.py` | 13 059 B | `0fa60de4a1ae87dc7ab20c262e38ea9ecc80718f40843f28d96f10b7c210f0f0` |

Ces empreintes sont celles du Skill source, pas celles de ce Skill.

## Non vérifié

- Archivage, suppression et détachement GitHub : aucune requête réseau dans la session.
- Jonction indisponible sur un hôte sans privilège de création : le cas est alors `CASE SKIP`, pas un PASS.
- Comportement sur une autre version de Python ou hors Windows.

## Limites de couverture

`skill-file-qa` valide structure, frontmatter, références, syntaxe et empreintes ; il ne compare pas les clés documentées aux sorties. Le vérificateur de parité lit la source, pas l'exécution : une clé émise mais dans une branche non exécutée reste à prouver par un fixture.

## Auto-contrôle du paquet (session 05dfc264, 2026-10-26)

La session de création `05dfc264-a669-4139-8c6b-9a0418997931` a lancé le vérificateur sur son propre paquet après avoir écrit les documents. Lecture : 6 messages, révision 14, `hasMoreBefore=false`, `runtimeState=running` au moment du snapshot. Aucune correction utilisateur du contenu ; les deux messages suivants demandent un test après rechargement et l'affichage détaillé du cas positif.

| Étape | Constat | Compteurs observés |
|---|---|---|
| 1 | Un placeholder méta en majuscules de l'Étape 1 est extrait comme clé promise | `DOC_KEYS=1`, `MATCHED=0`, `DOC_ONLY=1`, `DOC_ONLY_KEY` sur ce placeholder, code 1 |
| 2 | Les six en-têtes réels sont documentés dans la section qui nomme le script | `DOC_KEYS=7`, `MATCHED=6`, `DOC_ONLY=1` (le placeholder subsiste), code 1 |
| 3 | Le placeholder est passé en minuscules, aucune promesse supprimée | `DOC_KEYS=6`, `MATCHED=6`, `DOC_ONLY=0`, `RESULT=PASS`, code 0 |
| 4 | Rejeu sur le paquet livré, puis le 2026-10-26 avant cette mise à jour | mêmes compteurs, `RESULT=PASS`, code 0 |

Un `DOC_KEYS=0` avec `RESULT=PASS` n'aurait comparé aucun jeton : le PASS serait vide. La correction a consisté à documenter les en-têtes réels et à écrire les placeholders en minuscules, jamais à retirer une promesse.

## Remédiation 2026-10-27 — mode JSON et options (session f38c2627)

- Session `f38c2627-432b-4f25-a08e-86c5129f4b14`, 14 messages, révision 16, `hasMoreBefore=false`, `runtimeState=running` au snapshot : l'activité ne prouve pas qu'un tour d'écriture restait ouvert.
- Aucune correction utilisateur sur le contenu : le défaut a été trouvé en appliquant `reparer-contrat-sortie-skill` au paquet lui-même (message 6 de la session).
- Défauts mesurés avant correction : `--json` absent du document (0 occurrence), seules `--allow-key` et `--scope-key` documentées, 6 en-têtes listés sur 11 réels, lignes de détail et `ERROR` absentes.
- Correction : 12 en-têtes documentés, lignes de détail, options `--doc`/`--script`/`--json`, valeurs mesurées (compteurs `DOCS` et `SCRIPTS` à 1, `OUT_OF_SCOPE` 33→5, JSON 12 clés, négatif `result=FAIL` rc 1).
- Auto-contrôle avant/après : `DOC_KEYS=6`, `RUNTIME_ONLY=11`, `DOC_ONLY=0` → `DOC_KEYS=17`, `MATCHED=17`, `DOC_ONLY=0`, `RUNTIME_ONLY=0`, `RESULT=PASS` rc 0. La session rapporte 36 assertions de rejeu et `skill-file-qa` 9 PASS.
- Re-mesure indépendante le 2026-10-27 : auto-contrôle 17/17/17/0/0, `OUT_OF_SCOPE=33`, rc 0 ; `--json` 12 clés ; restreint compteurs `DOCS` et `SCRIPTS` à 1, `OUT_OF_SCOPE=5`, `DOC_KEYS=17` ; négatif JSON `result=FAIL` rc 1 ; usage JSON : seule la ligne `ERROR` sort, rc 2 ; 6 options `--help`.
- Limite : les 36 assertions et le PASS QA sont rapportés par la session source, pas rejoués ici ; les mesures ci-dessus ont été rejouées sur le paquet installé.
