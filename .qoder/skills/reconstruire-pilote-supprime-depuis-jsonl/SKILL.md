---
name: reconstruire-pilote-supprime-depuis-jsonl
description: "Reconstituer et vérifier un pilote temporaire supprimé depuis le JSONL d'une session Qoder : choisir la session qui contient le Write, rejouer les tool_use Write/Edit dans l'ordre (EDIT MISS si absent, EDIT AMBIGUOUS si multiple), compter Write, caractères du Write, Edit, lignes et caractères finaux, et ne garder une affirmation chiffrée que si la mesure concorde ; sinon corriger minimalement SKILL.md et les preuves, puis marquer « reconstituable, non livré » (可复原但未随包交付). Utiliser quand une Skill dit qu'un script supprimé a été récupéré ou cite 567/568 lignes, 22 064 caractères, un nombre de Write/Edit, quand read_chat_session est tronqué, ou quand le fichier temporaire n'existe plus. 中文触发：从会话 JSONL 复原已删除脚本、核实行数/字符数、Write + Edit 重放、EDIT MISS、EDIT AMBIGUOUS、文档自述与实物不符、可复原但未随包交付。"
---

# Reconstituer et vérifier un pilote supprimé depuis le JSONL

## État livré (2026-10-26)

Les trois fichiers existent : `SKILL.md`, `scripts/rejouer_pilote_jsonl.py` et `references/preuves-reconstruction.md`. Le script a été exécuté sur le JSONL source `c4fcd88c-…` : 1 `Write` de 22 064 caractères, 7 `Edit`, 567 lignes et 22 347 caractères finaux. Les contrôles négatifs et les empreintes sont dans `references/preuves-reconstruction.md`.

Un `CLAIM PASS` ne prouve que la cohérence entre les `tool_use` enregistrés et les nombres déclarés ; il ne prouve ni l'exécution du pilote, ni son comportement, ni l'absence de contenu non enregistré.

## Objectif

Rejouer un fichier temporaire supprimé à partir des seuls inputs `Write` et `Edit` de la session Qoder, puis vérifier les affirmations chiffrées d'une Skill : nombre de `Write`, caractères du `Write`, nombre d'`Edit`, lignes et caractères finaux.

## Quand l'utiliser

- Une Skill affirme qu'un script temporaire supprimé a été « récupéré depuis le JSONL ».
- Une Skill cite `567`/`568` lignes, `22 064` caractères, un nombre de `Write`/`Edit`, ou « 1 Write + 7 Edit ».
- `read_chat_session` est tronqué et un `Write`/`Edit` n'apparaît pas dans le snapshot.
- Le fichier n'existe plus sur disque et il faut décider si le contenu est reconstituable.
- Il faut distinguer « reconstituable, non livré » de « récupéré sur disque ».

Ne pas utiliser pour : auditer toute une session (`audit-session-evidence`), rejouer une fixture documentée (`replay-skill-reference-fixtures`), extraire un inventaire d'évidences (`extraire-preuves-session-qoder`), exécuter le pilote, prouver son succès, ou reconstruire un fichier créé par heredoc/`apply_patch`/`MultiEdit`.

## Contrat non négociable

1. **JSONL en lecture seule** : ne jamais modifier, tronquer, reformater ou normaliser le fichier de session. Relever taille, mtime et SHA-256 avant/après.
2. **Session avec `Write`** : choisir le JSONL qui contient un `Write` pour le chemin exact, pas celui qui mentionne seulement le fichier. Les mentions augmentent avec les sessions ; elles ne prouvent rien.
3. **Inputs seulement** : rejouer uniquement les blocs `tool_use` `Write`/`Edit` de la chaîne principale (`isSidechain=false`). Ignorer `tool_result`, résumés et prose ; un `tool_result` peut être tronqué.
4. **Chemin exact** : si un basename correspond à plusieurs chemins, s'arrêter et demander le chemin exact. Ne pas choisir au hasard.
5. **Éditions exactes** : `old_string` absent = `EDIT MISS` ; présent plusieurs fois sans `replace_all` enregistré = `EDIT AMBIGUOUS`. Ne jamais prendre la première occurrence par défaut.
6. **Outils non supportés** : `MultiEdit`, `NotebookEdit`, `apply_patch`, heredoc Bash = arrêt. Ne pas reconstruire par déduction.
7. **Conventions de mesure** : `lines = len(text.splitlines())`, `chars = len(text)` (points de code Unicode), `bytes_utf8` séparé. Ne pas confondre octets et caractères ; ne pas normaliser CRLF avant de compter.
8. **Porte des déclarations** : aucune affirmation chiffrée conservée sans `CLAIM PASS`. En cas d'écart, édition minimale dans `SKILL.md` et les références, puis re-`grep` pour éliminer les anciens nombres des déclarations courantes ; les exemples négatifs explicitement étiquetés (tableau des échecs, cas de test) restent. Ne jamais ajuster l'attendu pour faire passer.
9. **Vocabulaire** : sans fichier livré, écrire « reconstituable, non livré » (可复原但未随包交付), jamais « récupéré ». Avec `--dump`, ne dire « identique » qu'après comparaison SHA-256 avec le fichier sur disque.
10. **Pas d'exécution** : ne pas exécuter le pilote reconstruit sans demande explicite. Sortie ASCII, `py -3`, codes 0/1/2, aucun réseau.

## Fichiers

| Fichier | État | Rôle |
|---|---|---|
| `SKILL.md` | présent | Contrat, procédure et limites |
| `scripts/rejouer_pilote_jsonl.py` | présent, testé | Rejeu déterministe, mesures et porte de déclarations |
| `references/preuves-reconstruction.md` | présent | Preuves datées, cas source, tests négatifs, limites |

## CLI

```bash
py -3 "<dossier-skill>/scripts/rejouer_pilote_jsonl.py" \
  --jsonl "<session>.jsonl" \
  --file "C:/Users/Administrateur/.qoder/tmp/isolated_publish_flow_test.py" \
  --expect-writes 1 --expect-write-chars 22064 \
  --expect-edits 7 --expect-lines 567 --expect-chars 22347
```

| Option | Effet |
|---|---|
| `--jsonl` | chemin explicite du JSONL de session ; obligatoire |
| `--file` | chemin exact ou basename ; basename ambigu = sortie 2 |
| `--expect-writes` | nombre attendu de `Write` |
| `--expect-write-chars` | somme des caractères de tous les `Write` |
| `--expect-edits` | nombre d'`Edit` appliqués |
| `--expect-lines` | lignes finales, via `splitlines()` |
| `--expect-chars` | caractères finaux, points de code Unicode |
| `--dump` | écrit la reconstruction dans un nouveau fichier UTF-8/LF ; refuse d'écraser ; ne l'exécute pas |

Codes de retour : `0` = rejeu et déclarations conformes ; `1` = `EDIT MISS`, `EDIT AMBIGUOUS` ou `CLAIM FAIL` ; `2` = usage, JSONL invalide, cible absente/ambiguë, sidechain seule, outil non supporté ou erreur d'écriture.

## Procédure

### 1. Localiser le JSONL et la cible

Chemin habituel : `C:\Users\Administrateur\.qoder\projects\<project-slug>\<sessionId>.jsonl`. Vérifier le `sessionId` dans le fichier. Pour un inventaire plus large, utiliser `extraire-preuves-session-qoder` ; pour l'audit de la chaîne de références, `audit-session-evidence`.

Chercher les mentions du pilote dans tous les JSONL du projet, puis **confirmer lequel contient le `Write`** pour le chemin exact. Ne pas déduire la session du nombre de mentions.

### 2. Relever toutes les déclarations

```bash
grep -rn -E "JSONL|reconstitu|récupér|lignes finales|caractères|chars|Write|Edit" "<skill-dir>"
```

Relever chaque nombre avec son fichier et sa ligne. Retirer les séparateurs de milliers (`22 064` → `22064`). Vérifier aussi les anciennes valeurs (`568`, `23 714`) : elles peuvent subsister dans une référence.

### 3. Rejouer et mesurer

```bash
py -3 "<dossier-skill>/scripts/rejouer_pilote_jsonl.py" \
  --jsonl "<session>.jsonl" --file "<cible>" \
  --expect-writes 1 --expect-write-chars 22064 \
  --expect-edits 7 --expect-lines 567 --expect-chars 22347
```

Lire `WRITE`, `EDIT`, `EVENTS`, `RESULT`, `CLAIM`. Conserver la sortie et le code de retour pour la référence de preuves.

### 4. Décider

- `CLAIM PASS` : conserver les nombres. Si le fichier n'est pas livré, garder « reconstituable, non livré ».
- `CLAIM FAIL` : corriger uniquement les nombres fautifs dans toutes les occurrences courantes (hors exemples négatifs étiquetés), puis re-`grep`.
- `EDIT MISS` / `EDIT AMBIGUOUS` : ne pas rafistoler à la main ; vérifier la session, le chemin, l'ordre et l'unicité. Si l'ambiguïté persiste, s'arrêter.
- `2` : problème d'environnement ou de cible, pas une preuve de faux. Ne rien conclure sur les nombres.

### 5. Matérialiser seulement si demandé

`--dump <nouveau-chemin>` écrit la reconstruction en UTF-8/LF, sans BOM, et affiche octets et SHA-256. Refuser d'écraser. Comparer ce SHA-256 à un éventuel fichier sur disque avant de dire « identique ». Ne pas exécuter le fichier produit.

### 6. Documenter et revalider

Ajouter dans `references/preuves-reconstruction.md` : date, `sessionId`, chemin/taille/lignes/SHA-256 du JSONL, chemin cible, entrées `Write`/`Edit`, commande, sortie, anciennes valeurs, décision. Re-`grep` les anciens nombres dans les déclarations courantes. Lancer `skill-file-qa` sur le paquet modifié et vérifier l'absence de `__pycache__`.

## Sortie mesurée sur le cas source (2026-10-26)

Cette sortie provient du JSONL `c4fcd88c-4b53-4843-a74c-f4a901244e96`. Taille, `mtime_ns`, nombre de lignes et SHA-256 sont un instantané : une session encore active étend son JSONL. Les entrées `Write`/`Edit` et les mesures du pilote sont restées identiques malgré la croissance observée. Vérifier les nombres, pas le SHA-256.

```text
JSONL C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\c4fcd88c-4b53-4843-a74c-f4a901244e96.jsonl
JSONL_FINGERPRINT size=1744756 mtime_ns=1793016940135931000 lines=478 sha256=b049387ee6803c301649da88ff5f35df940059bb64de50faf8f5380a6ffed6b4
TARGET C:\Users\Administrateur\.qoder\tmp\isolated_publish_flow_test.py
WRITE entry=252 chars=22064 lines=564
EDIT entry=264 occurrence=1
EDIT entry=279 occurrence=1
EDIT entry=283 occurrence=1
EDIT entry=289 occurrence=1
EDIT entry=294 occurrence=1
EDIT entry=298 occurrence=1
EDIT entry=307 occurrence=1
EVENTS writes=1 write_chars=22064 edits=7
RESULT lines=567 chars=22347 bytes_utf8=22347 trailing_newline=true
CLAIM PASS writes=1 write_chars=22064 edits=7 lines=567 chars=22347
```

## Échecs observés et correctifs

| Symptôme | Cause | Correctif |
|---|---|---|
| `EDIT MISS entry=N` | session/chemin erroné, `Write` antérieur absent, ou édition non enregistrée | vérifier le chemin exact et l'ordre ; ne pas patcher à la main |
| `EDIT AMBIGUOUS occurrence=K` | `old_string` apparaît plusieurs fois | utiliser `replace_all` seulement s'il est enregistré ; sinon s'arrêter |
| `no Write/Edit for target` | fichier créé par heredoc, `apply_patch`, `MultiEdit`, ou mauvaise session | changer d'outil/méthode ; ne pas reconstruire par prose |
| `multiple target paths` | basename présent dans plusieurs dossiers | passer le chemin exact avec `--file` |
| `CLAIM FAIL lines expected=568 measured=567` | déclaration obsolète | édition minimale, puis re-`grep` toutes les occurrences |
| `CLAIM FAIL write_chars expected=23714 measured=22064` | ancien nombre erroné dans la provenance | idem ; vérifier aussi la référence de preuves |
| `UnicodeDecodeError` | JSONL non UTF-8 ou ligne partielle | s'arrêter ; ne pas utiliser `errors="replace"` |
| `UnicodeEncodeError` / cp1252 | console Windows non UTF-8 | le script sort en ASCII ; sinon `PYTHONIOENCODING=utf-8` |
| `chars` différents après `--dump` | traduction CRLF à l'écriture | écrire avec `newline=""` ; ne pas normaliser avant de compter |
| `bytes_utf8` ≠ `chars` | caractères non ASCII | comparer les caractères pour les déclarations, les octets pour le fichier |
| `WARN sidechain_ignored` | événements d'une branche latérale | vérifier la chaîne principale ; ne pas rejouer une sidechain |
| `WARN multiple_writes` | plusieurs `Write` complets | le dernier `Write` remplace le texte ; le signaler dans les preuves |
| `WARN jsonl_changed_during_read` | JSONL étendu pendant la lecture par la session hôte | relancer la mesure ; les entrées déjà lues restent valides, le SHA-256 n'est pas un attendu |

## Provenance et limites

- **Observé dans la session de reconstruction** (`b8448766-bcf0-40dc-9ea5-9622f129877e`, revision 87) : le JSONL source a été localisé ; seuls `c4fcd88c-…` contient le `Write` et les 7 `Edit` du pilote ; le rejeu a donné 567 lignes et 22 347 caractères ; les déclarations 568 lignes et 23 714 caractères ont été corrigées.
- **Rejoué indépendamment** : JSONL `c4fcd88c-…`, instantané daté du 2026-10-26 à 13:15 (478 lignes, 1 744 756 octets, `sha256=b049387e…`) ; `Write` entrée 252, 22 064 caractères, 564 lignes ; 7 `Edit` (entrées 264, 279, 283, 289, 294, 298, 307), chacun avec une occurrence unique ; résultat 567 lignes, 22 347 caractères, 22 347 octets UTF-8, saut de ligne final. Le fichier a augmenté de 1 586 492 à 1 744 756 octets pendant l'audit sans changer ces entrées ni ces mesures ; voir `references/preuves-reconstruction.md` §5.
- **Livré et testé** : script de rejeu, porte de déclarations, `--dump` refusant l'écrasement ; 15 contrôles positifs/négatifs PASS sur le cas réel et des fixtures synthétiques.
- **Non prouvé** : l'exécution ou la correction sémantique du pilote, l'absence de contenu non enregistré, l'immutabilité d'une session active, un fichier créé sans `Write`/`Edit`, la sécurité d'un `--dump` exécuté ensuite. Un `CLAIM PASS` ne couvre que le texte enregistré et les nombres mesurés.
- **Frontière de vocabulaire** : le pilote n'a pas été récupéré sur disque ; il est reconstituable depuis le JSONL mais n'est pas livré dans ce paquet.

## Définition de terminé

- [x] `SKILL.md` présent, frontmatter valide, description sur une ligne.
- [x] Script créé, `py_compile` sans erreur.
- [x] Cas réel : `CLAIM PASS` avec 1 Write, 22 064 caractères de Write, 7 Edit, 567 lignes, 22 347 caractères.
- [x] Négatifs : `568`, `23 714`, `EDIT MISS`, `EDIT AMBIGUOUS`, cible absente, multi-chemins, `MultiEdit`, sidechain, doublon d'ID.
- [x] `--dump` : 22 347 octets, 567 lignes, refus d'écrasement.
- [x] Script en lecture seule : le JSONL source n'est pas modifié par le script ; la session hôte peut l'étendre (croissance observée et documentée). Skill voisine inchangée.
- [x] `skill-file-qa` : `RESULT PASS`, 3 fichiers, pas de `__pycache__`.
- [x] Aucun commit, aucun push, aucune exécution du pilote reconstruit.

## Ressources

- `scripts/rejouer_pilote_jsonl.py` — rejeu, mesures, `CLAIM PASS/FAIL`, `--dump`.
- `references/preuves-reconstruction.md` — preuves datées, cas source, tests négatifs, limites.
- `extraire-preuves-session-qoder` — localiser et inventorier les preuves d'une session.
- `audit-session-evidence` — auditer la chaîne de références et attribuer les corrections.
- `replay-skill-reference-fixtures` — rejouer une fixture documentée, hors du cas « fichier supprimé ».
- `skill-file-qa` — validation statique après écriture.
- `tester-publication-isolee-skill` — cas source du pilote supprimé, en lecture seule.
