# Preuves d'audit — intégrité d'un paquet Skill

Date : 2026-10-26 (Europe/Paris, UTC+1). Chaque valeur ci-dessous est un fait daté, pas une garantie permanente.

## Sources consultées

- Session b76f168c (« 更新 commit-skill-work ») : revision 17, `runtimeState` running, `hasMoreBefore` false. Dernier message utilisateur : « 按方案执行并保留新脚本 ».
- Session imbriquée a072b096 : revision 33, `runtimeState` ready, `hasMoreBefore` false. Les sorties d'outils citées ci-dessous en proviennent.
- Aucune correction utilisateur n'a porté sur les deux constats. L'échec est sémantique : un `RESULT PASS` ne prouve pas la propreté du paquet, et l'archive n'était pas contrôlée après le commit.

## Constat 1 — `RESULT PASS` avec un cache

Après un contrôle de syntaxe, le validateur a listé le cache et a quand même rendu `PASS` :

```text
PY_COMPILE_OK
Files (4): SKILL.md, references/preuves-publication.md, scripts/__pycache__/verifier_archive_skill.cpython-314.pyc, scripts/verifier_archive_skill.py
PASS layout: 4 file(s), no extraneous documentation
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
```

Après suppression du cache, le manifeste est revenu à trois fichiers :

```text
Files (3): SKILL.md, references/preuves-publication.md, scripts/verifier_archive_skill.py
RESULT PASS
```

Cause : `list_files` énumère tous les fichiers hors `.git`, et le contrôle de disposition accepte tout contenu sous un dossier autorisé, y compris un dossier de cache. Le compteur `Files (N)` inclut donc le cache sans avertissement.

## Constat 2 — archive obsolète après modification de la source

La source a été modifiée, puis l'archive existante a été comparée à la source finale :

```text
MISMATCH SKILL.md                                     source=b51008639c63 ddfd179=21ed7b412853
MISMATCH references/preuves-publication.md            source=07bedd4e9f51 ddfd179=b8573e4ea521
MISMATCH scripts/verifier_archive_skill.py            source=d11f8864789d ddfd179=f4ce464c0aba
RESULT FAIL - 3 anomalie(s) sur 3 fichier(s) source
EXIT=1
```

Le même contrôle sur `origin/main` a produit 3/3 `MISMATCH`. Le commit source de l'époque était `3a47dab` ; l'archive `ddfd179` n'a pas été mise à jour. La vérification n'était pas une étape rejouable du flux de commit à ce moment-là.

## Reproduction indépendante du cache

Le 2026-10-26 à 11:53, un Skill temporaire a été validé avant puis après `py_compile` :

```text
Files (2): SKILL.md, scripts/sample.py
RESULT PASS

PY_COMPILE_OK

Files (3): SKILL.md, scripts/__pycache__/sample.cpython-314.pyc, scripts/sample.py
RESULT PASS
```

Le cache apparaît dans `Files (N)` et les deux validations passent. Les fichiers du Skill temporaire ont été supprimés après le test.

## Contrat de la dépendance d'archive

Le script `find_stale_archives.py` de `commit-skill-work` a été audité en lecture seule. Matrice rejouée intégralement sur la version `eb3ccb61…` :

| Cas | Sortie observée | Code |
|---|---|---|
| `--help` | options `--skill`, `--search-root`, `--repo`, `--dest`, `--max-depth` | 0 |
| `--dest` par défaut, source = archive | `RESULT FRESH` (`2/2 fichiers identiques`) | 0 |
| source modifiée après archivage | `RESULT STALE`, `MISMATCH` | 1 |
| fichier en trop dans l'archive | `RESULT STALE`, `EXTRA` | 1 |
| `--dest` erroné | `RESULT NONE` | 0 |
| sans root | `FAIL usage: provide --search-root or --repo` | 2 |
| `--max-depth 0` | `FAIL usage: --max-depth must be >= 1` | 2 |
| `SKILL.md` absent | `FAIL usage: SKILL.md absent` | 2 |
| dépôt valide + `--repo` invalide | `RESULT FAIL`, ligne `NOTE: resultats partiels` | 2 |
| ref `refs/remotes/` / branche locale seule | `[published]` / `[local]` | — |

Deux points de sémantique vérifiés dans le code et par exécution :

- L'erreur d'environnement (`--repo` ou `--search-root` inexistant) est prioritaire : `RESULT FAIL` et code 2, même si une archive trouvée est `STALE`. Le code collecte `env_error`, puis le teste avant la branche `stale` ([find_stale_archives.py:196](file:///C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py#L196), [find_stale_archives.py:266](file:///C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py#L266)).
- La destination par défaut est `.qoder/skills/<nom-du-dossier>` ; un `--dest` erroné produit `NONE` (faux négatif), pas une erreur.

Dépôts publics réels audités sans écriture : archive de `publier-skill-qoder-vers-depot-git` en 3/3 `STALE` sur `96fd809` (published) et `3628f249` (local) ; archive de `commit-skill-work` en 3/4 `STALE` sur `96fd809` et `c5b7f17` (script absent) et sur `3628f249` (script différent).

## Empreinte et historique

Valeur courante :

```text
eb3ccb616626456de47ca2d6be84d8267915538dbba5b9f27af8aff772fbe883
9887 octets | mtime 2026-10-26 12:00:20 +01:00
```

Historique observé :

| Date | Taille | SHA-256 | Contexte |
|---|---|---|---|
| 2026-10-26 11:52:49 | 9869 | `9d0ef62980dfd19f7f49c71a10e9daef0d22e8f0aaa1cc2d6a319b646114fcfa` | création par la session b76f168c |
| 2026-10-26 12:00:20 | 9887 | `eb3ccb616626456de47ca2d6be84d8267915538dbba5b9f27af8aff772fbe883` | édition concurrente ; `env_error` renvoie désormais 2 même si une archive est `STALE` |

La seconde version a passé la matrice complète le 2026-10-26. La règle « rejouer un seul cas `FRESH`/`STALE` » est insuffisante : elle n'aurait pas détecté le changement de priorité de l'erreur d'environnement. Après tout changement d'empreinte, rejouer la matrice, puis mettre à jour ensemble la valeur dans `SKILL.md` et dans ce fichier, avec l'ancienne et la nouvelle valeur, la taille et le mtime. Si un cas échoue ou si le script manque, s'arrêter.

## Concurrence et état courant

`commit-skill-work` était encore en cours d'écriture à 11:54–11:56. Sa validation à 11:56 a échoué sur une référence locale introuvable, car un chemin de cache était écrit en code inline dans la documentation. Ne pas utiliser un `PASS` antérieur de ce Skill comme preuve de l'état courant ; relancer après la dernière écriture.

## Limites

- L'audit est structurel : il ne prouve pas la qualité sémantique d'une traduction ni la pertinence du contenu.
- `RESULT NONE` ne couvre que les dépôts interrogés ; ce n'est pas une garantie globale.
- Aucun `fetch`, copie, commit, push ou suppression d'archive n'est effectué. La suppression de cache est une action manuelle, limitée aux caches de session du paquet ciblé.
- La procédure générique et les cas limites (`--dest ../escape`, `--dest` absolu, réécriture MSYS) sont détaillés dans le Skill `dependency-script-contract-reaudit` ; ce fichier ne conserve que les preuves datées de cet audit.
