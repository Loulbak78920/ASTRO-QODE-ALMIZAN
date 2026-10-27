---
name: skill-package-integrity-audit
description: "Auditer en lecture seule l'intégrité d'un paquet Skill après modification : vérifier le manifeste Files (N) de skill-file-qa, signaler et faire retirer uniquement les caches __pycache__/pyc créés par la session, puis détecter les archives obsolètes dans les dépôts voisins par ref/commit (OID blob vs git hash-object --path). Sortie NONE/FRESH/STALE ; ne copie, ne commite, ne pousse et ne supprime jamais une archive. Utiliser après un PASS de skill-file-qa, avant commit/publication, en cas de cache dans le paquet ou d'archive publiée soupçonnée obsolète. 中文触发：Skill 包完整性审计、QA PASS 仍含 __pycache__、Files (N) 清单、归档过期、STALE、ref/commit、只读审计。"
---

# Auditer l'intégrité d'un paquet Skill

## Objectif

Vérifier qu'un paquet Skill est propre et que ses copies archivées sont à jour, sans modifier les dépôts. Un `RESULT PASS` de `skill-file-qa` ne prouve pas l'absence de cache : le validateur compte tous les fichiers hors `.git` et accepte le contenu de `scripts/`.

## Déclencheurs

- après une modification de `SKILL.md`, d'un script ou d'une référence, avant commit ou publication ;
- `skill-file-qa` renvoie `RESULT PASS` mais `Files (N)` semble trop élevé ou contient `__pycache__` ;
- un `py_compile`, un import ou un test a pu créer des `.pyc` ;
- une archive du Skill existe dans un dépôt voisin et peut être obsolète ;
- besoin d'un rapport `NONE` / `FRESH` / `STALE` sans copier, commiter ni pousser.

## Contrat

- Lecture seule par défaut.
- Seule mutation autorisée : supprimer les caches créés par la session dans le paquet ciblé, après les avoir listés et avoir vérifié leur provenance. Ne jamais supprimer un cache préexistant, un fichier source, ni un chemin hors du paquet ciblé.
- Aucun `git fetch`, `git add`, `git commit`, `git push`, `git merge`, copie ou suppression d'archive. La republication appartient à `publier-skill-qoder-vers-depot-git` et exige une instruction explicite.
- Toute écriture pendant l'audit invalide les empreintes et OID déjà relevés : reprendre les deux étapes sur la version finale.
- Ne pas confondre `RESULT STALE` (constat, code 1) avec une erreur d'exécution (code 2).

## Étape 1 — Manifeste et caches

1. Lancer `skill-file-qa` et conserver sa sortie hors du paquet :

```bash
TMP=".qoder/tmp/skill-package-integrity"
mkdir -p "$TMP"
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "<dossier-skill>" --workspace "<racine-espace>" --stable-seconds 2 > "$TMP/qa.log" 2>&1
grep -E "^Files \(|^Summary:|^RESULT " "$TMP/qa.log"
```

2. Auditer le manifeste et les caches :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/skill-package-integrity-audit/scripts/check_package_manifest.py" \
  "<dossier-skill>" --qa-log "$TMP/qa.log"
```

Lire `All files`, `Clean`, `Caches`, `Unexpected` et `QA Files (N)`. Le nombre QA doit égaler le total sur disque ; un `MATCH` ne prouve pas que le paquet est propre, seulement que QA a vu le même état.

3. Si des lignes `CACHE` apparaissent, lister les chemins exacts et vérifier leur provenance (mtime contemporain de la session, `py_compile` ou import observé). En cas de doute, demander avant de supprimer.

```bash
find "<dossier-skill>" -type d -name "__pycache__" -prune -print
find "<dossier-skill>" -type f \( -name "*.pyc" -o -name "*.pyo" \) -print
```

Supprimer uniquement les chemins listés et attribués à la session :

```bash
rm -rf "<dossier-skill>/scripts/__pycache__"
rm -f "<dossier-skill>/scripts/<fichier>.pyc"
```

Répéter pour chaque chemin listé. Ne jamais utiliser `git clean`, `rm -rf` sur la racine du Skill ou une suppression par motif large.

4. Relancer QA puis le script de manifeste. Exiger `RESULT PASS`, `Caches: 0`, `Unexpected: 0`, `QA Files (N)` en `MATCH` et `Clean` égal à `N`. Sinon, s'arrêter et rapporter.

5. Relever les empreintes de toutes les ressources :

```bash
find "<dossier-skill>" -type f \( -name "SKILL.md" -o -path "*/scripts/*" -o -path "*/references/*" -o -path "*/assets/*" \) \
  ! -path "*/__pycache__/*" -print0 | xargs -0 sha256sum
```

6. Toute écriture après cette étape impose de reprendre à l'étape 1.

## Étape 2 — Archives par ref/commit

1. Vérifier la dépendance canonique et son contrat :

```bash
DEP="C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py"
test -f "$DEP" || { echo "FAIL dependance absente"; exit 2; }
py -3 "$DEP" --help
sha256sum "$DEP"
```

Empreinte observée le 2026-10-26 à 12:00 : `eb3ccb616626456de47ca2d6be84d8267915538dbba5b9f27af8aff772fbe883` (9887 octets, mtime 12:00:20). Le script peut être modifié par une autre session : ne pas réutiliser une empreinte antérieure sans re-audit.

Si le fichier manque, s'arrêter. Si l'empreinte, la taille ou le mtime diffèrent, mesurer deux fois à quelques secondes d'intervalle pour exclure une écriture en cours, puis rejouer toute la matrice suivante dans un dépôt temporaire hors du paquet (`.qoder/tmp/...`) :

| Cas | Attendu |
|---|---|
| `--help` | code 0 ; options `--skill`, `--search-root`, `--repo`, `--dest`, `--max-depth` |
| source = archive, `--dest` par défaut `.qoder/skills/<nom>` | `RESULT FRESH`, code 0 |
| source modifiée après archivage | `RESULT STALE` + `MISMATCH`, code 1 |
| fichier en trop dans l'archive | `RESULT STALE` + `EXTRA`, code 1 |
| `--dest` erroné | `RESULT NONE`, code 0 (faux négatif) |
| dépôt valide + `--repo` ou `--search-root` invalide | `RESULT FAIL`, code 2, résultats partiels ; l'erreur d'environnement prime sur `STALE` |
| branche locale seule / ref `refs/remotes/` | `[local]` / `[published]` |
| sans root, `--max-depth 0`, `SKILL.md` absent | `RESULT FAIL`, code 2 |

Ne mettre à jour les empreintes de ce fichier et de `references/preuves-audit.md` qu'après un passage intégral de la matrice, en notant l'ancienne et la nouvelle valeur, la taille, le mtime et la date. Un seul cas `FRESH`/`STALE` ne suffit pas : la priorité des erreurs d'environnement ou les libellés `published`/`local` peuvent changer sans casser ces deux cas. En cas d'écart inexpliqué, s'arrêter ; ne pas improviser un remplacement ni conserver l'ancienne empreinte.

Pour la procédure générique, les fixtures rejouables et les cas limites (`--dest ../escape`, `--dest` absolu, réécriture MSYS), utiliser le Skill `dependency-script-contract-reaudit` ; la matrice ci-dessus reste le minimum à rejouer dans cet audit.

2. Auditer les dépôts voisins :

```bash
py -3 "$DEP" --skill "<dossier-skill>" --repo "<depot>"
py -3 "$DEP" --skill "<dossier-skill>" --search-root "<racine>" --max-depth 3
```

`--repo` et `--search-root` sont répétables. La destination par défaut est `.qoder/skills/<nom-du-dossier>` ; si l'archive est ailleurs, passer `--dest`. Une destination erronée produit `NONE` (faux négatif).

3. Interpréter :

| Sortie | Code | Action |
|---|---|---|
| `RESULT NONE` | 0 | aucune archive trouvée dans les dépôts interrogés ; rapporter le nombre de dépôts, ne pas conclure `FRESH` |
| `RESULT FRESH` | 0 | toutes les archives sont identiques à la source |
| `RESULT STALE` | 1 | constat : rapporter `MISMATCH`, `MISSING`, `EXTRA`, refs, commit et `published`/`local` ; attendre une instruction |
| `RESULT FAIL` ou usage | 2 | corriger les entrées ou l'environnement ; ce n'est pas un constat d'obsolescence |
| un dépôt invalide parmi plusieurs | certains chemins `--repo` ou `--search-root` sont invalides | `RESULT FAIL` code 2 avec résultats partiels ; corriger les chemins et relancer |

Une archive n'est `published` que si un ref sous `refs/remotes/` pointe sur le commit ; une branche locale reste `local`.

4. Ne rien recopier, commiter, fusionner, pousser ni supprimer. Consigner l'empreinte du script et les commits audités. Relancer après toute modification de la source.

## Erreurs et pièges

| Symptôme | Cause | Action |
|---|---|---|
| `RESULT PASS` avec un cache dans `Files (N)` | le validateur compte tous les fichiers hors `.git` et accepte `scripts/` | lancer le script de manifeste, lister, retirer les caches de session, relancer QA |
| `QA Files (N)` en `MATCH` alors qu'un cache existe | QA et le disque comptent le même cache | un `MATCH` ne prouve pas la propreté ; retirer le cache et relancer |
| `QA Files (N)` en `MISMATCH` | QA a tourné avant une écriture, après une écriture, ou sur un autre dossier | relancer QA et le script sur la version finale |
| `FAIL local reference not found` avec un chemin de cache | un chemin `.pyc` a été écrit en code inline dans la documentation | placer ces exemples dans un bloc de code, pas entre backticks |
| `RESULT STALE` code 1 | archive différente de la source | rapporter seulement ; la republication est une étape séparée |
| `RESULT NONE` inattendu | `--dest` erroné ou archive dans un dépôt non interrogé | vérifier `--dest`, ajouter `--repo` ou `--search-root` |
| archive `local` présentée comme `published` | aucun ref `refs/remotes/` ne pointe sur le commit | vérifier les refs avant de conclure |
| source modifiée pendant l'audit | écriture concurrente | reprendre l'étape 1 puis l'étape 2 |
| dépendance absente ou empreinte différente | script déplacé ou modifié | s'arrêter ; rejouer la matrice complète de l'étape 2 et ne mettre à jour les deux empreintes qu'après succès |

## Checklist finale

- [ ] Sortie QA conservée hors du paquet.
- [ ] `Caches: 0`, `Unexpected: 0`, `QA Files (N)` en `MATCH`, `Clean` égal à `N`.
- [ ] Seuls les caches de session ont été supprimés ; aucun fichier source ni cache préexistant touché.
- [ ] Empreintes SHA-256 de `SKILL.md` et des ressources relevées.
- [ ] Dépendance présente ; empreinte, taille et mtime consignés ; si elle diffère, matrice complète de l'étape 2 rejouée et les deux empreintes mises à jour ensemble.
- [ ] Résultat d'archive `NONE`/`FRESH`/`STALE` rapporté avec refs, commit et `published`/`local`.
- [ ] Aucune copie, commit, push ou suppression d'archive.
- [ ] Contrôles rejoués après la dernière écriture.

## Rapport

```text
Paquet   : <nom> | QA <PASS/FAIL> | Fichiers <N> -> <N_propre> | Caches <k> | Unexpected <m>
Empreintes : SKILL.md <sha> | ressources <n> fichiers
Archives : NONE (repos <n>) | FRESH <refs> | STALE <ref> <commit> (<n>/<N>) [published|local]
Outil    : find_stale_archives.py sha256=<...>
Action   : aucune (lecture seule) | caches retires (<n>) | republication requise (instruction explicite)
```

## Ressources

- `scripts/check_package_manifest.py` : audit lecture seule du manifeste, des caches et des fichiers inattendus ; compare `Files (N)` d'un journal QA au total sur disque ; sortie ASCII, codes 0/1/2.
- `references/preuves-audit.md` : preuves datées, sorties exactes, tests de contrat et limites.
- `dependency-script-contract-reaudit` : procédure générique de re-audit d'un script de dépendance après changement d'empreinte (double échantillonnage, matrice 8 cas, fixtures rejouables, limites d'environnement). À invoquer lorsque l'empreinte de `find_stale_archives.py` diffère ou que le comportement CLI doit être re-prouvé.
- Dépendance : le Skill `commit-skill-work` fournit `C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py` pour la détection en lecture seule des archives par ref/commit ; ne pas réimplémenter cet algorithme.
