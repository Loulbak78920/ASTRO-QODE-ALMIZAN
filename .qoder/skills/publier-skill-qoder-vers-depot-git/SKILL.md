---
name: publier-skill-qoder-vers-depot-git
description: "Archiver ou publier un Skill Qoder du dossier utilisateur dans un dépôt Git, en visant sa branche main : valider le Skill, créer une branche temporaire depuis origin/main, copier fichier par fichier uniquement SKILL.md, references/ et scripts/ sans cache, comparer les SHA-256 source/copie, committer, avancer main en fast-forward, pousser puis vérifier le HEAD et les blobs distants. En l'absence de push, sauter la vérification distante et conserver la branche temporaire. Distinguer archive périmée et MSYS, et relire branche, HEAD et origin/main avant merge/push car une autre session peut changer l'état. Utiliser pour « publier un Skill », « archiver le Skill dans le dépôt », « merge to main », « push the Skill repository », une branche de Skill à historique racine indépendant, l'erreur MSYS 'origin\\main;...', une archive périmée, un MISMATCH après modification ou un reflog d'autre session. 中文触发：发布 Skill、合并到 main、fast-forward、独立根历史、MSYS 路径转换、未推送、branch -d 被拒绝、归档过期、修改后 MISMATCH、其他会话、reflog。"
---

# Publier un Skill utilisateur dans un dépôt Git

Publier un Skill du dossier utilisateur Qoder dans un dépôt Git sans réécrire l'historique de ce dépôt : branche temporaire depuis `main`, copie du seul périmètre du Skill, contrôle SHA-256, fast-forward et vérification du distant. Le Skill fonctionnel reste dans le dossier utilisateur ; la copie publiée est une archive.

`commit-skill-work` couvre la mécanique commit/push et le choix du dépôt ; ce Skill couvre la publication vers `main` et la preuve que les blobs distants sont identiques à la source.

## Quand l'utiliser

- Publier ou archiver un Skill utilisateur dans un dépôt existant, sur `main` ou une branche convenue.
- Reprendre une branche de Skill à historique racine indépendant qui ne peut pas être fusionnée.
- Vérifier qu'une copie publiée est octet pour octet identique à la source.
- Diagnostiquer `fatal: ambiguous argument 'origin\main;...'` sous Git Bash.
- Diagnostiquer un `MISMATCH` après modification du Skill (archive périmée) ou une branche/`origin/main` déplacée par une autre session en cours d'opération.

Ne pas utiliser pour : committer sans publier (voir `commit-skill-work`), modifier le Skill (voir `skill-update-concurrency-safe`), fusionner du code applicatif, ou pousser sans instruction explicite de l'utilisateur.

## Contrat non négociable

1. **Périmètre** : copier uniquement le fichier `SKILL.md` et les dossiers `references` et `scripts`. Jamais `.git/`, `__pycache__/`, `*.pyc`, ni le dossier source en entier. La copie se fait fichier par fichier ; les caches sont exclus à la source (étape 3) et contrôlés dans la destination (étape 4).
2. **Destination** : `<depot>/.qoder/skills/<nom>/`, où <nom> est le nom du dossier source et le champ `name` du frontmatter.
3. **Identité octet pour octet** : SHA-256 identique pour chaque fichier avant le commit (copie worktree) et après le push (blob `origin/main`).
4. **Branche de fusion** : `merge/skill-<nom>` créée depuis `origin/main`. `main` avance uniquement par `git merge --ff-only`. Aucun merge commit, aucun `--force`, aucun `--amend`.
5. **Historique indépendant** : ne jamais fusionner une branche de Skill sans ancêtre commun avec `main`. Recréer une branche depuis `main` et copier les fichiers.
6. **Push sur instruction explicite** : ne pousser `main` qu'après demande claire, en confirmant dépôt et branche. Si `main` a divergé, s'arrêter et demander.
7. **Validation avant publication** : `skill-file-qa` doit rendre `RESULT PASS`. Aucun secret, binaire volumineux ou cache dans le périmètre.
8. **Archive, pas fonctionnel** : les chemins relatifs du Skill peuvent viser l'arborescence du projet principal, absente du dépôt. Le signaler dans le rapport.
9. **Aucune réécriture** : pas de `git config`, pas de `reset --hard`, pas de force push, pas de modification de l'historique existant.
10. **État relu avant merge et push** : relire la branche courante, `HEAD` et `origin/main` juste avant l'étape 6 puis juste avant l'étape 7. Tout écart avec la baseline de l'étape 0 arrête la procédure ; attribuer la dérive avec `git reflog --date=iso` et `git reflog show --date=iso origin/main`, ne jamais se l'approprier ni corriger l'état d'une autre session sans instruction.

## Procédure

Remplacer `<depot>`, `<skill>`, <nom> et <chemin> par les valeurs réelles. Toujours passer les chemins absolus entre guillemets.

### 0. Préflight

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<skill>" --workspace "<racine-espace>" --stable-seconds 2
git -C "<depot>" rev-parse --show-toplevel
git -C "<depot>" rev-parse --abbrev-ref HEAD
git -C "<depot>" rev-parse HEAD
git -C "<depot>" rev-parse origin/main
git -C "<depot>" status --porcelain=v1
git -C "<depot>" remote -v
git -C "<depot>" reflog --date=iso -n 20
git -C "<depot>" reflog show --date=iso origin/main -n 10
```

Exiger `RESULT PASS`, la branche `main`, un worktree propre et un `origin` qui correspond au dépôt visé. Consigner la branche, `HEAD`, `origin/main` et les dernières entrées de reflog (HEAD et `origin/main`) : c'est la baseline des étapes 6 et 7. Le dépôt peut être partagé avec une autre session Qoder ; ne pas supposer que cet état reste vrai pendant l'opération. Si le worktree est sale : s'arrêter, lister les chemins et demander (voir `commit-skill-work`). La racine du projet n'est pas forcément un dépôt : localiser le vrai dépôt avec `git -C`, ne pas en déduire un chemin.

### 1. Aligner main

```bash
git -C "<depot>" fetch origin
git -C "<depot>" rev-parse HEAD origin/main
```

Les deux hashes doivent être égaux. Si `main` est derrière, avancer en fast-forward uniquement. Si les hashes divergent, s'arrêter : ne pas rebaser, ne pas forcer. Si `origin/main` diffère de la baseline de l'étape 0, une autre session ou le distant a avancé : relire l'historique, repartir de cette nouvelle valeur et recréer la branche temporaire à l'étape 2 ; ne pas réutiliser une base périmée.

### 2. Créer la branche temporaire depuis main

```bash
git -C "<depot>" switch -c "merge/skill-<nom>" origin/main
```

### 3. Copier le périmètre exact

```bash
dest="<depot>/.qoder/skills/<nom>"
src="<skill>"
mkdir -p "$dest"
cp "$src/SKILL.md" "$dest/"
for d in references scripts; do
  [ -d "$src/$d" ] || continue
  ( cd "$src" && find "$d" \( -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' \) -prune -o -type f -print ) |
  while IFS= read -r rel; do
    mkdir -p "$dest/$(dirname "$rel")"
    cp "$src/$rel" "$dest/$rel"
  done
done
find "$dest" -type f
find "$dest" \( -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' \) -print
```

La seconde commande `find` doit ne rien afficher : elle prouve l'absence de cache dans l'archive. Copier les deux dossiers seulement s'ils existent dans la source. Ne jamais copier le dossier source entier : il peut contenir son propre `.git/` (cas observé d'un Skill versionné localement). Un `.gitignore` qui ignore `__pycache__/` empêche le commit du cache, pas sa présence dans le worktree : ne pas s'y fier.

### 4. Vérifier la copie

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/publier-skill-qoder-vers-depot-git/scripts/verifier_archive_skill.py" --source "<skill>" --repo "<depot>" --from worktree
```

Attendre `RESULT PASS` et un `OK` par fichier. En mode `worktree`, un `MISMATCH` signifie que la copie diffère : ne pas committer, recopier le fichier et relancer. En mode `remote` sur une ref antérieure aux dernières modifications, un `MISMATCH` (hashes source et ref différents) signifie **archive périmée** : republier, ne pas recopier dans une ref figée. Le script force déjà `MSYS_NO_PATHCONV` et `MSYS2_ARG_CONV_EXCL` : un `MISMATCH` rendu par le script n'est pas une conversion MSYS. En cas de `MISSING`, vérifier le nom du dossier de destination. Toute ligne `EXTRA` signale un fichier présent dans la destination mais absent de la source, cache compris : retirer les caches ; pour tout autre fichier, demander avant de supprimer.

### 5. Committer sur la branche temporaire

```bash
git -C "<depot>" add -- "<depot-relatif>/SKILL.md" "<depot-relatif>/references" "<depot-relatif>/scripts"
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --cached --stat
git -C "<depot>" commit -m "feat(skills): ajouter le Skill <nom>"
```

Chemins explicites uniquement, jamais `git add -A` ni `git add .`. Le message suit l'historique du dépôt ; le corps peut préciser qu'il s'agit d'une copie d'archive et que le Skill fonctionnel reste dans le dossier utilisateur.

### 6. Avancer main en fast-forward

```bash
git -C "<depot>" rev-parse --abbrev-ref HEAD
git -C "<depot>" rev-parse HEAD
git -C "<depot>" rev-parse origin/main
git -C "<depot>" status --porcelain=v1
git -C "<depot>" switch main
git -C "<depot>" rev-parse --abbrev-ref HEAD
git -C "<depot>" rev-parse HEAD
git -C "<depot>" merge --ff-only "merge/skill-<nom>"
git -C "<depot>" log --oneline -2
git -C "<depot>" status -sb
```

Avant de basculer : la branche doit être `merge/skill-<nom>`, `HEAD` le commit de l'étape 5, `origin/main` la base de l'étape 1 et le worktree propre. Tout écart arrête la procédure ; inspecter `git reflog --date=iso` et ne pas attribuer le changement à cette session. Après `switch main`, relire la branche et `HEAD` avant le merge. Si `main` est déjà extraite dans un autre worktree (`git worktree list`), s'arrêter et demander.

Attendre `Fast-forward`, un seul commit ajouté et `[ahead 1]`. Si `--ff-only` refuse, `main` a bougé : vérifier dans le reflog si le mouvement vient de cette session ou d'une autre, puis revenir à l'étape 2, recréer la branche depuis le nouveau `origin/main` et recopier. Ne jamais utiliser `--no-ff` ni forcer, ni présenter un changement externe comme le sien.

### 7. Pousser (sur instruction explicite)

```bash
git -C "<depot>" fetch origin
git -C "<depot>" rev-parse --abbrev-ref HEAD
git -C "<depot>" rev-parse HEAD
git -C "<depot>" rev-parse origin/main
git -C "<depot>" ls-remote origin refs/heads/main
git -C "<depot>" push origin main
```

Avant de pousser : la branche doit être `main`, `HEAD` le commit de fusion, et `origin/main` égal à `ls-remote`. Si le fetch a avancé `origin/main`, une autre session a poussé : s'arrêter et demander ; ne pas rebaser, merger ni forcer.

Attendre une ligne de la forme `<ancien>..<nouveau>  main -> main`. Jamais `--force` ni `-f`. Si le push est rejeté, relire `git log HEAD..origin/main` et `git reflog --date=iso`, puis demander avant toute action.

### 8. Vérifier le distant (uniquement si le push a eu lieu)

```bash
git -C "<depot>" rev-parse HEAD
git -C "<depot>" ls-remote origin refs/heads/main
py -3 "C:/Users/Administrateur/.qoder/skills/publier-skill-qoder-vers-depot-git/scripts/verifier_archive_skill.py" --source "<skill>" --repo "<depot>" --ref origin/main --from remote
```

Le hash local et le hash `refs/heads/main` doivent être identiques, puis le script doit rendre `RESULT PASS`.

Sans push, `origin/main` pointe encore sur le commit précédent : le mode `remote` renvoie `MISSING` sur tous les fichiers et `RESULT FAIL` (rejoué le 2026-10-26 sur `ddfd179` non poussé), ce n'est pas un défaut de copie. Ne pas pousser sans instruction : consigner `Distant : non exécuté (push non effectué)`.

Si la ref contient déjà une version antérieure du Skill (par exemple l'archive `ddfd179` après modification de la source), le script renvoie `MISMATCH` avec deux hashes différents, pas `MISSING` : c'est aussi une archive périmée. Republier ; ne pas comparer une ref figée à une source qui a changé.

Contrôle manuel possible pour un fichier, avec la conversion MSYS désactivée :

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' git -C "<depot>" show "origin/main:<chemin>" | sha256sum
sha256sum "<skill>/<chemin>"
```

### 9. Nettoyer

```bash
git -C "<depot>" branch -d "merge/skill-<nom>"
git -C "<depot>" branch -vv
git -C "<depot>" status -sb
```

Après un push, la suppression doit être confirmée par `Deleted branch ... (was <hash>)` et l'état final doit être `## main...origin/main` sans écart.

Sans push, `-d` est refusé même quand `main` contient le commit, car le contrôle porte sur `refs/remotes/origin/main`. Message observé le 2026-10-26 :

```text
warning: not deleting branch 'merge/skill-<nom>' that is not yet merged to
         'refs/remotes/origin/main', even though it is merged to HEAD
error: the branch 'merge/skill-<nom>' is not fully merged
```

Conserver alors la branche, la signaler dans le rapport et terminer avec `## main...origin/main [ahead 1]`, état attendu tant que le push n'a pas eu lieu. La supprimer après le push. `git branch -D` seulement sur instruction explicite de l'utilisateur.

Une branche distante indépendante `skill/<nom>`, poussée avant la fusion, reste sur `origin` : ne pas la supprimer sans instruction explicite. Vérifier avec `branch -vv` que `main` suit `origin/main` et non `origin/skill/<nom>`.

## Piège MSYS (vérifié le 2026-10-26)

Sous Git Bash, un argument de la forme `origin/main:<chemin>` est converti comme une liste de chemins Windows (`:` devient `;`, `/` devient `\`). Erreur observée sur cinq fichiers :

```text
fatal: ambiguous argument 'origin\main;.qoder\skills\...\SKILL.md': unknown revision or path not in the working tree.
```

Sans variable d'environnement, la commande sort en 128 ; avec `MSYS_NO_PATHCONV=1` et `MSYS2_ARG_CONV_EXCL='*'`, elle sort en 0 et affiche le contenu du blob. Le script évite le problème : il appelle `git` par `subprocess` sans shell et force ces deux variables dans son environnement. Inversement, un `MISMATCH` rendu par le script n'est pas attribuable à MSYS : sur une ref ancienne, c'est une archive périmée. Transcription complète des commandes et sorties : `references/preuves-publication.md`.

## Erreurs et pièges vérifiés

| Symptôme | Cause | Correctif |
|---|---|---|
| `fatal: ambiguous argument 'origin\main;...'` | conversion de chemins MSYS sous Git Bash | `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`, ou le script |
| `MISMATCH` avec deux hashes différents sur une ref distante après modification du Skill | archive périmée : la ref contient l'ancienne version | republier ; ne pas recopier dans une ref figée, ce n'est pas MSYS |
| branche courante, `HEAD` ou `origin/main` différents de la baseline pendant l'opération | autre session Qoder sur le même dépôt | s'arrêter, relire, attribuer avec `git reflog --date=iso` et `git reflog show --date=iso origin/main` ; ne pas revendiquer ni corriger l'état externe |
| branche de Skill sans ancêtre commun avec `main` | dépôt de Skill initialisé séparément, puis poussé sur une branche dédiée | ne pas la fusionner ni ouvrir une PR de merge ; recréer `merge/skill-<nom>` depuis `main` et copier |
| `fatal: not a git repository` à la racine du projet | la racine n'est pas un dépôt | énumérer les `.git` imbriqués, puis `git -C` sur le vrai dépôt |
| `fatal: cannot change to '...ASTRO-Q°ODE_SYSTEME'` | chemin non ASCII ou relatif résolu depuis un autre répertoire courant | vérifier avec `test -d`, puis passer un chemin absolu |
| la branche locale suit `origin/skill/...` après un push | refspec `HEAD:refs/heads/<branche>` | vérifier `git -C "<depot>" branch -vv` ; préférer `git push origin main` |
| `error: the branch 'merge/skill-<nom>' is not fully merged` alors que `main` contient le commit | commit non poussé : `-d` compare à `refs/remotes/origin/main`, créé depuis `origin/main` | conserver la branche et la signaler ; pousser puis relancer `-d` ; `-D` sur accord explicite seulement |
| vérificateur `--from remote` : `MISSING` sur tous les fichiers alors que la copie worktree est `PASS` | push non effectué, `origin/main` inchangé | ne pas pousser sans instruction ; consigner le contrôle distant comme non exécuté |
| `warning: ... CRLF will be replaced by LF` | normalisation des fins de ligne | informationnel ; ne pas réécrire le dépôt |

## Définition de terminé

- [ ] `skill-file-qa` : `RESULT PASS` avant toute copie.
- [ ] Copie limitée au fichier `SKILL.md` et aux dossiers `references` et `scripts` ; aucun `.git`, cache ou fichier hors périmètre ; l'assertion `find` de l'étape 3 ne renvoie rien et le vérificateur ne signale aucun `EXTRA`.
- [ ] Vérificateur en mode worktree : `RESULT PASS`, un `OK` par fichier.
- [ ] Un seul commit sur `merge/skill-<nom>`, chemins explicites, message conforme à l'historique.
- [ ] `main` avancée par `Fast-forward` ; aucun merge commit.
- [ ] Push effectué seulement sur demande ; si non poussé, l'annoncer et ne pas présenter le distant comme validé.
- [ ] Si push effectué : hash local égal à `ls-remote origin refs/heads/main` et vérificateur en mode remote `RESULT PASS` ; sinon contrôle distant marqué non exécuté.
- [ ] Si push effectué : branche temporaire supprimée et worktree synchronisé ; sinon branche conservée et signalée, sans `-D`.
- [ ] Baseline de l'étape 0 consignée, puis branche/`HEAD`/`origin/main` relus avant le merge et avant le push ; aucun écart inexpliqué.
- [ ] Toute dérive externe arrête la procédure et est attribuée via `git reflog --date=iso` et `git reflog show --date=iso origin/main`, sans revendication.
- [ ] `MISMATCH` qualifié : archive périmée si la ref est antérieure, MSYS réservé à `fatal: ambiguous argument` hors script.
- [ ] Rapport : réserve d'archive, état du push et des chemins relatifs signalés.

## Rapport

```text
Skill : <nom> | source <chemin absolu>
Depot : <chemin absolu> | remote <URL> | branche main
Copie : <N> fichiers sous .qoder/skills/<nom> | SHA-256 worktree PASS
Commit : <hash court> feat(skills): ajouter le Skill <nom>
Main : <ancien>..<nouveau> fast-forward | push oui/non
État : <branche>@<hash> | origin/main <hash> | relu avant merge et push | dérive : aucune|<reflog>
Distant : HEAD <hash> | blobs PASS/FAIL | non exécuté (push non effectué)
Nettoyage : branche supprimée | conservée (non poussé)
Reserve : archive, chemins relatifs non garantis dans ce depot
```

## Ressources

- `scripts/verifier_archive_skill.py` : compare en lecture seule les SHA-256 de la source avec la copie worktree ou les blobs d'une ref distante, et signale tout fichier `EXTRA` présent dans la destination ; sortie ASCII, codes 0/1/2.
- `references/preuves-publication.md` : transcription des sorties observées (commit `3a4732a`, 5 hashes, échec MSYS, archivage non poussé `ddfd179`, dérive d'état et archive périmée) et re-vérifications du 2026-10-26.
- `commit-skill-work` : localisation du dépôt, classification des changements, commit et push de base.
- `skill-file-qa` : validation statique du Skill avant publication.
- `skill-update-concurrency-safe` : édition sûre du Skill source avant publication.
