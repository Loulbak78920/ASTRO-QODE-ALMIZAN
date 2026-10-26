---
name: publier-skill-qoder-vers-depot-git
description: "Archiver ou publier un Skill Qoder du dossier utilisateur dans un dépôt Git, en visant sa branche main : valider le Skill, créer une branche temporaire depuis origin/main, copier uniquement SKILL.md, references/ et scripts/, comparer les SHA-256 source/copie, committer, avancer main en fast-forward, pousser puis vérifier le HEAD et les blobs distants. Utiliser pour « publier un Skill », « archiver le Skill dans le dépôt », « merge to main », « push the Skill repository », une branche de Skill à historique racine indépendant, ou l'erreur MSYS 'origin\\main;...'. 中文触发：发布 Skill、合并到 main、fast-forward、独立根历史、MSYS 路径转换。"
---

# Publier un Skill utilisateur dans un dépôt Git

Publier un Skill du dossier utilisateur Qoder dans un dépôt Git sans réécrire l'historique de ce dépôt : branche temporaire depuis `main`, copie du seul périmètre du Skill, contrôle SHA-256, fast-forward et vérification du distant. Le Skill fonctionnel reste dans le dossier utilisateur ; la copie publiée est une archive.

`commit-skill-work` couvre la mécanique commit/push et le choix du dépôt ; ce Skill couvre la publication vers `main` et la preuve que les blobs distants sont identiques à la source.

## Quand l'utiliser

- Publier ou archiver un Skill utilisateur dans un dépôt existant, sur `main` ou une branche convenue.
- Reprendre une branche de Skill à historique racine indépendant qui ne peut pas être fusionnée.
- Vérifier qu'une copie publiée est octet pour octet identique à la source.
- Diagnostiquer `fatal: ambiguous argument 'origin\main;...'` sous Git Bash.

Ne pas utiliser pour : committer sans publier (voir `commit-skill-work`), modifier le Skill (voir `skill-update-concurrency-safe`), fusionner du code applicatif, ou pousser sans instruction explicite de l'utilisateur.

## Contrat non négociable

1. **Périmètre** : copier uniquement le fichier `SKILL.md` et les dossiers `references` et `scripts`. Jamais `.git/`, `__pycache__/`, `*.pyc`, ni le dossier source en entier.
2. **Destination** : `<depot>/.qoder/skills/<nom>/`, où <nom> est le nom du dossier source et le champ `name` du frontmatter.
3. **Identité octet pour octet** : SHA-256 identique pour chaque fichier avant le commit (copie worktree) et après le push (blob `origin/main`).
4. **Branche de fusion** : `merge/skill-<nom>` créée depuis `origin/main`. `main` avance uniquement par `git merge --ff-only`. Aucun merge commit, aucun `--force`, aucun `--amend`.
5. **Historique indépendant** : ne jamais fusionner une branche de Skill sans ancêtre commun avec `main`. Recréer une branche depuis `main` et copier les fichiers.
6. **Push sur instruction explicite** : ne pousser `main` qu'après demande claire, en confirmant dépôt et branche. Si `main` a divergé, s'arrêter et demander.
7. **Validation avant publication** : `skill-file-qa` doit rendre `RESULT PASS`. Aucun secret, binaire volumineux ou cache dans le périmètre.
8. **Archive, pas fonctionnel** : les chemins relatifs du Skill peuvent viser l'arborescence du projet principal, absente du dépôt. Le signaler dans le rapport.
9. **Aucune réécriture** : pas de `git config`, pas de `reset --hard`, pas de force push, pas de modification de l'historique existant.

## Procédure

Remplacer `<depot>`, `<skill>`, <nom> et <chemin> par les valeurs réelles. Toujours passer les chemins absolus entre guillemets.

### 0. Préflight

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<skill>" --workspace "<racine-espace>" --stable-seconds 2
git -C "<depot>" rev-parse --show-toplevel
git -C "<depot>" rev-parse --abbrev-ref HEAD
git -C "<depot>" status --porcelain=v1
git -C "<depot>" remote -v
```

Exiger `RESULT PASS`, la branche `main`, un worktree propre et un `origin` qui correspond au dépôt visé. Si le worktree est sale : s'arrêter, lister les chemins et demander (voir `commit-skill-work`). La racine du projet n'est pas forcément un dépôt : localiser le vrai dépôt avec `git -C`, ne pas en déduire un chemin.

### 1. Aligner main

```bash
git -C "<depot>" fetch origin
git -C "<depot>" rev-parse HEAD origin/main
```

Les deux hashes doivent être égaux. Si `main` est derrière, avancer en fast-forward uniquement. Si les hashes divergent, s'arrêter : ne pas rebaser, ne pas forcer.

### 2. Créer la branche temporaire depuis main

```bash
git -C "<depot>" switch -c "merge/skill-<nom>" origin/main
```

### 3. Copier le périmètre exact

```bash
mkdir -p "<depot>/.qoder/skills/<nom>"
cp "<skill>/SKILL.md" "<depot>/.qoder/skills/<nom>/"
cp -R "<skill>/references" "<depot>/.qoder/skills/<nom>/"
cp -R "<skill>/scripts" "<depot>/.qoder/skills/<nom>/"
find "<depot>/.qoder/skills/<nom>" -type f
```

Copier les deux dossiers seulement s'ils existent dans la source. Ne jamais copier le dossier source entier : il peut contenir son propre `.git/` (cas observé d'un Skill versionné localement).

### 4. Vérifier la copie

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/publier-skill-qoder-vers-depot-git/scripts/verifier_archive_skill.py" --source "<skill>" --repo "<depot>" --from worktree
```

Attendre `RESULT PASS` et un `OK` par fichier. En cas de `MISMATCH`, ne pas committer : recopier le fichier et relancer. En cas de `MISSING`, vérifier le nom du dossier de destination.

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
git -C "<depot>" switch main
git -C "<depot>" merge --ff-only "merge/skill-<nom>"
git -C "<depot>" log --oneline -2
git -C "<depot>" status -sb
```

Attendre `Fast-forward`, un seul commit ajouté et `[ahead 1]`. Si `--ff-only` refuse, `main` a bougé : revenir à l'étape 2, recréer la branche depuis le nouveau `origin/main` et recopier. Ne jamais utiliser `--no-ff` ni forcer.

### 7. Pousser (sur instruction explicite)

```bash
git -C "<depot>" push origin main
```

Attendre une ligne de la forme `<ancien>..<nouveau>  main -> main`. Jamais `--force` ni `-f`. Si le push est rejeté, relire `git log HEAD..origin/main` et demander avant toute action.

### 8. Vérifier le distant

```bash
git -C "<depot>" rev-parse HEAD
git -C "<depot>" ls-remote origin refs/heads/main
py -3 "C:/Users/Administrateur/.qoder/skills/publier-skill-qoder-vers-depot-git/scripts/verifier_archive_skill.py" --source "<skill>" --repo "<depot>" --ref origin/main --from remote
```

Le hash local et le hash `refs/heads/main` doivent être identiques, puis le script doit rendre `RESULT PASS`. Contrôle manuel possible pour un fichier, avec la conversion MSYS désactivée :

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

La suppression doit être confirmée par `Deleted branch ... (was <hash>)`. Finir avec un worktree propre et `## main...origin/main` sans écart.

Une branche distante indépendante `skill/<nom>`, poussée avant la fusion, reste sur `origin` : ne pas la supprimer sans instruction explicite. Vérifier avec `branch -vv` que `main` suit `origin/main` et non `origin/skill/<nom>`.

## Piège MSYS (vérifié le 2026-10-26)

Sous Git Bash, un argument de la forme `origin/main:<chemin>` est converti comme une liste de chemins Windows (`:` devient `;`, `/` devient `\`). Erreur observée sur cinq fichiers :

```text
fatal: ambiguous argument 'origin\main;.qoder\skills\...\SKILL.md': unknown revision or path not in the working tree.
```

Sans variable d'environnement, la commande sort en 128 ; avec `MSYS_NO_PATHCONV=1` et `MSYS2_ARG_CONV_EXCL='*'`, elle sort en 0 et affiche le contenu du blob. Le script évite le problème : il appelle `git` par `subprocess` sans shell et force ces deux variables dans son environnement. Transcription complète des commandes et sorties : `references/preuves-publication.md`.

## Erreurs et pièges vérifiés

| Symptôme | Cause | Correctif |
|---|---|---|
| `fatal: ambiguous argument 'origin\main;...'` ou `MISMATCH` sur tous les fichiers alors que la copie est identique | conversion de chemins MSYS sous Git Bash | `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`, ou le script |
| branche de Skill sans ancêtre commun avec `main` | dépôt de Skill initialisé séparément, puis poussé sur une branche dédiée | ne pas la fusionner ni ouvrir une PR de merge ; recréer `merge/skill-<nom>` depuis `main` et copier |
| `fatal: not a git repository` à la racine du projet | la racine n'est pas un dépôt | énumérer les `.git` imbriqués, puis `git -C` sur le vrai dépôt |
| `fatal: cannot change to '...ASTRO-Q°ODE_SYSTEME'` | chemin non ASCII ou relatif résolu depuis un autre répertoire courant | vérifier avec `test -d`, puis passer un chemin absolu |
| la branche locale suit `origin/skill/...` après un push | refspec `HEAD:refs/heads/<branche>` | vérifier `git -C "<depot>" branch -vv` ; préférer `git push origin main` |
| `warning: ... CRLF will be replaced by LF` | normalisation des fins de ligne | informationnel ; ne pas réécrire le dépôt |

## Définition de terminé

- [ ] `skill-file-qa` : `RESULT PASS` avant toute copie.
- [ ] Copie limitée au fichier `SKILL.md` et aux dossiers `references` et `scripts` ; aucun `.git`, cache ou fichier hors périmètre.
- [ ] Vérificateur en mode worktree : `RESULT PASS`, un `OK` par fichier.
- [ ] Un seul commit sur `merge/skill-<nom>`, chemins explicites, message conforme à l'historique.
- [ ] `main` avancée par `Fast-forward` ; aucun merge commit.
- [ ] Push effectué seulement sur demande ; hash local égal à `ls-remote origin refs/heads/main`.
- [ ] Vérificateur en mode remote : `RESULT PASS`.
- [ ] Branche temporaire supprimée ; worktree propre et synchronisé.
- [ ] Rapport : réserve d'archive et chemins relatifs signalés.

## Rapport

```text
Skill : <nom> | source <chemin absolu>
Depot : <chemin absolu> | remote <URL> | branche main
Copie : <N> fichiers sous .qoder/skills/<nom> | SHA-256 worktree PASS
Commit : <hash court> feat(skills): ajouter le Skill <nom>
Main : <ancien>..<nouveau> fast-forward | push oui/non
Distant : HEAD <hash> | blobs PASS/FAIL
Reserve : archive, chemins relatifs non garantis dans ce depot
```

## Ressources

- `scripts/verifier_archive_skill.py` : compare en lecture seule les SHA-256 de la source avec la copie worktree ou les blobs d'une ref distante ; sortie ASCII, codes 0/1/2.
- `references/preuves-publication.md` : transcription des sorties observées (commit `3a4732a`, 5 hashes, échec MSYS) et re-vérification indépendante du 2026-10-26.
- `commit-skill-work` : localisation du dépôt, classification des changements, commit et push de base.
- `skill-file-qa` : validation statique du Skill avant publication.
- `skill-update-concurrency-safe` : édition sûre du Skill source avant publication.
