# Cas `os.chmod` — 2026-10-28

Deux sessions concourent :

- `8d7c4c1e-100e-4ad8-99ba-b97d06e57371` : session cible, lot d'en-têtes SPDX sur 283 fichiers, deux échecs sur `horloge_noyau/__init__.py`.
- `d2ffe162-3452-4fcf-93e2-860dc7559887` : session d'audit qui a archivé le dump de la première, constaté `chmod: 0`, puis reproduit le mécanisme en fixture.

## Empreintes

| Artefact | Octets | Lignes | SHA-256 |
| :--- | ---: | ---: | :--- |
| `8d7c4c1e….jsonl` | 2 151 156 | 595 | `07115b5ee627b8e794c7954a44da26f856be152f4a8c75938b3e9a239c1c8f01` |
| dump `read_chat_session` archivé | 167 258 | 519 | `c596471475627dbc90207e11470807716dc1194a2b1c65f4c92bc6cd96836804` |

Le dump de `8d7c4c1e` a été archivié par `d2ffe162` dans son propre dossier `.qoder/tmp/<slug>/d2ffe162…/tool-results/builtin_read_chat_session_c59647147562.txt`. Les deux fichiers sont en lecture seule pour ce Skill.

## Comptages comparés

Mesurés le 2026-10-28 sur les deux artefacts.

| Motif | Dump | `tool_use.input` | `tool_result` | Verdict du dump |
| :--- | ---: | ---: | ---: | :--- |
| `chmod` | **0** | **2** (1 appel) | 0 | faux négatif |
| `S_IWRITE` | 0 | 1 | 0 | faux négatif |
| `S_IREAD` | 0 | 1 | 0 | faux négatif |
| `icacls` | 0 | 3 (2 appels) | 0 | faux négatif |
| `attrib` | 7 | 11 (6 appels) | 10 | partiel |
| `takeown` | 2 | **0** | 0 | présent en prose seulement |
| `PermissionError` | 2 | 0 | 2 | cohérent |
| `WinError` | 1 | 0 | 1 | cohérent |

La ligne `attrib` illustre le piège inverse : sur 11 occurrences dans les entrées, **une seule** est la commande elle-même (ligne 365, `cmd //c "attrib horloge_noyau\*.py"`). Les autres sont le mot français « attribué » dans des `Write`/`Edit` (lignes 118, 128, 181), « l'attribuer » dans un `echo` (ligne 100) et `read-only attribute(s)` dans deux champs `description` (lignes 358, 365). Un `tool_use.input` porte donc aussi de la prose : compter n'identifie pas une commande, seule la lecture de `command` le fait.

`takeown` est le contrôle inverse : 2 occurrences dans le dump, aucune dans une entrée, car le mot n'apparaît que dans la narration de l'assistant. Un comptage global sur le JSONL (26 occurrences de `chmod`) mélange prose, entrées et sorties et ne tranche rien.

## Tracebacks verbatim du dump

```text
Exit code 1
Traceback (most recent call last):
  File "<stdin>", line 32, in <module>
  File "…\Lib\pathlib\__init__.py", line 796, in write_bytes
    with self.open(mode='wb') as f:
  …
PermissionError: [Errno 13] Permission denied: 'horloge_noyau\\__init__.py'
```

```text
Exit code 1
Traceback (most recent call last):
  File "<stdin>", line 33, in <module>
PermissionError: [WinError 5] Acc?s refus?: 'horloge_noyau\\__init__.py'
```

Le second bloc n'a **aucune** frame de bibliothèque. Les accents sont déjà corrompus dans l'enregistrement : le JSONL contient littéralement `U+FFFD` (`EF BF BD`) à la place de `è`, produit par la console cp1252 de la session source. Ne jamais chercher la fin accentuée d'un message ; chercher `WinError 5`.

## Réconciliation des lignes

Le script réapparie chaque traceback à son `tool_use` par identifiant, puis lit la ligne du corps heredoc numérotée comme `<stdin>`.

| Résultat | Appel | `<stdin>` | Instruction exécutée | Frames |
| ---: | ---: | ---: | :--- | :--- |
| 349 | 347 | 32 | `p.write_bytes(new.encode("utf-8"))` | stdlib |
| 360 | 358 | 33 | `os.chmod(p, stat.S_IWRITE)` | aucune |
| 339 | 337 | 30 | `if "\r\n" in b:` | aucune |
| 378 | 376 | 31 | `ast.parse(new, filename=str(p))` | aucune |
| 384 | 382 | 49 | `pathlib.Path("/tmp/spdx-headers-avant-2026-10-28.json").write_text(` | stdlib |

Entre l'appel 347 et l'appel 358, trois lignes ont été insérées avant l'écriture (`was_ro = …`, `if was_ro:`, `os.chmod(…)`) : `write_bytes` passe de `<stdin>` 32 à 35. Le numéro 33 du second traceback désigne donc bien le `chmod` inséré, et non l'écriture décalée.

Contrôle de cohérence interne : les quatre autres tracebacks tombent chacun sur une instruction dont le type d'erreur est plausible (`ast.parse` → `SyntaxError`, `write_text` → `FileNotFoundError`). Une reconstruction fausse produirait des appariements incohérents.

## Fixtures de `d2ffe162`

Hors installation, `%TEMP%\acl-*`, propriétaire = compte courant.

| Cas | Résultat mesuré |
| :--- | :--- |
| A — attribut `R` seul, aucune ACE | `write_text` → `[Errno 13]` ; `chmod(S_IWRITE)` → OK ; écriture → OK |
| B — DENY `WD,AD,WA`, sans attribut `R` | `write_text`/`write_bytes` → `[Errno 13]`, `winerror=None`, `READONLY_ATTR False` |
| B — `os.chmod(S_IWRITE)` | refusé, `errno=13 winerror=5` |
| B — `attrib -R` | **rc 0**, stdout « Accès refusé », attribut `R` toujours posé |
| B — `rmtree` après `/remove:d` sans retirer `R` | `PermissionError [WinError 5]` |
| Nettoyage `/remove:d` → `attrib -R` → `rmtree` | supprimé, `%TEMP%\acl-*` vide |

Ces résultats établissent que `chmod` sous refus `WA` rend exactement `errno=13 / winerror=5` avec un message localisé, c'est-à-dire la signature du second traceback.

## Classification

| Affirmation | Statut | Preuve |
| :--- | :--- | :--- |
| `chmod` ne figure pas dans le dump `read_chat_session` | VÉRIFIÉ | comptage 0 sur le dump |
| le dump ne transporte pas les entrées d'outils | VÉRIFIÉ | `tools[] = {name,status,output}` |
| l'appel exécuté contenait `os.chmod(p, stat.S_IWRITE)` à `<stdin>` 33 | VÉRIFIÉ | JSONL ligne 358, apparié au résultat 360 |
| `write_bytes` occupait `<stdin>` 32 dans la version précédente | VÉRIFIÉ | JSONL ligne 347, apparié au résultat 349 |
| `chmod` sous `DENY WD,AD,WA` rend `errno=13 / winerror=5` | REPRODUIT | fixture B |
| `attrib -R` peut sortir rc 0 sans changer l'attribut | REPRODUIT | fixture B |
| `rmtree` échoue en `WinError 5` tant que `R` reste posé | REPRODUIT | fixture B, puis nettoyage réussi |
| une fixture `DENY` incluant `WDAC`/`WO` serait indélébile sans `takeown` | INFÉRÉ | sémantique du masque ; jamais créée, par précaution |

## Limites

- Le dump archivé appartient au dossier temporaire d'une autre session ; un nettoyage de `.qoder/tmp` le supprime. Le JSONL, lui, reste la source des entrées.
- Le JSONL peut être compacté ou purgé : un `tool_use` absent n'autorise pas la conclusion « commande jamais exécutée », seulement « entrée non disponible ».
- Les accents des sorties sont déjà perdus (`U+FFFD`) dans l'enregistrement ; aucun texte localisé ne peut être cité à l'octet près.
- La fixture prouve le mécanisme du refus, pas l'identité de la commande ; seul l'appariement JSONL la fixe.
- Le script rattache une ligne de traceback au premier corps heredoc assez long de l'appel apparié : un appel contenant plusieurs heredocs peut donc afficher une instruction provenant d'un autre bloc. Vérifier `statement` avant de conclure ; ici chaque appel n'a qu'un heredoc.
