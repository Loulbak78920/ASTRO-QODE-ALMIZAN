---
name: publier-skill-qoder-vers-depot-git
description: "Publier ou archiver un Skill Qoder dans un dépôt Git vers main : valider, créer une branche temporaire depuis origin/main (nom horodaté si merge/skill-<nom> existe), copier SKILL.md, references/ et scripts/ sans cache, comparer les SHA-256, committer, fast-forward, pousser sur demande puis vérifier HEAD et blobs distants. Sans push, conserver la branche. Relire branche/HEAD/origin/main avant merge/push ; sur dérive externe (STOP_BRANCH/STOP_ORIGIN), s'arrêter, attribuer par reflog, si un tiers pousse notre commit, vérifier les blobs distants et le rapporter sans l'annuler. Utiliser pour « publier un Skill », « merge to main », « push the Skill repository », archivage en série («继续下一个»), collision de branche temporaire, historique racine indépendant, 'origin\\main;...' MSYS, archive périmée, MISMATCH après modification, reflog ou push d'une autre session. 中文触发：发布 Skill、合并到 main、fast-forward、独立根历史、MSYS 路径转换、未推送、branch -d 拒绝、归档过期、MISMATCH、其他会话、reflog、临时分支已存在、时间戳分支、外部 push、批量归档、继续下一个、推送授权。"
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
- Reprendre quand `merge/skill-<nom>` existe déjà (autre session ou essai précédent) et créer une branche horodatée sans réutiliser l'existante.
- Reprendre après `STOP_BRANCH` ou `STOP_ORIGIN` quand une autre session a changé la branche, avancé `main` ou poussé le commit.
- Constater qu'un tiers a fast-forwardé puis poussé le commit de cette session et le rapporter comme push externe, sans rollback.
- Publier quand le worktree du dépôt cible est occupé par une autre session (branche autre que `main` ou fichiers non commités) : s'arrêter, puis, après accord, utiliser un clone temporaire isolé sans toucher à ce worktree.
- Enchaîner plusieurs archivages sans nommer la cible («继续下一个», «继续», «archive le prochain Skill») : calculer le diff utilisateur/archive et proposer la cible la plus récente (étape 0c), sans jamais réutiliser la liste d'un tour précédent.
- Décider si une autorisation de push couvre les Skills suivants d'une même série (contrat 6).

Ne pas utiliser pour : committer sans publier (voir `commit-skill-work`), modifier le Skill (voir `skill-update-concurrency-safe`), fusionner du code applicatif, ou pousser sans instruction explicite de l'utilisateur.

## Contrat non négociable

1. **Périmètre** : copier uniquement le fichier `SKILL.md` et les dossiers `references` et `scripts`. Jamais `.git/`, `__pycache__/`, `*.pyc`, ni le dossier source en entier. La copie se fait fichier par fichier ; les caches sont exclus à la source (étape 3) et contrôlés dans la destination (étape 4).
2. **Destination** : `<depot>/.qoder/skills/<nom>/`, où <nom> est le nom du dossier source et le champ `name` du frontmatter.
3. **Identité octet pour octet** : SHA-256 identique pour chaque fichier avant le commit (copie worktree) et après le push (blob `origin/main`).
4. **Branche de fusion** : `merge/skill-<nom>` créée depuis `origin/main`. Si ce nom existe déjà, utiliser une branche unique `merge/skill-<nom>-YYYYMMDD-HHMMSS`, également créée depuis `origin/main` ; ne jamais réutiliser, déplacer ni supprimer une branche existante. `main` avance uniquement par `git merge --ff-only`. Aucun merge commit, aucun `--force`, aucun `--amend`.
5. **Historique indépendant** : ne jamais fusionner une branche de Skill sans ancêtre commun avec `main`. Recréer une branche depuis `main` et copier les fichiers.
6. **Push sur instruction explicite** : ne pousser `main` qu'après demande claire, en confirmant dépôt et branche. Une autorisation porte sur le commit et le dépôt nommés : «continue», «继续下一个», «继续同一流程» ne l'étendent pas. Pour une série, demander une fois avant le premier push et proposer soit l'accord pour ce push, soit une autorisation de lot explicite (dépôt, branche, nombre de Skills restants) ; sans accord de lot, redemander avant chaque push. Si `main` a divergé, s'arrêter et demander. Un push effectué par une autre session n'est jamais le push de cette session : ne pas le revendiquer, ne pas le refaire, ne pas l'annuler.
7. **Validation avant publication** : `skill-file-qa` doit rendre `RESULT PASS`. Aucun secret, binaire volumineux ou cache dans le périmètre.
8. **Archive, pas fonctionnel** : les chemins relatifs du Skill peuvent viser l'arborescence du projet principal, absente du dépôt. Le signaler dans le rapport.
9. **Aucune réécriture** : pas de `git config`, pas de `reset --hard`, pas de force push, pas de modification de l'historique existant.
10. **État relu avant merge et push** : relire la branche courante, `HEAD` et `origin/main` juste avant l'étape 6 puis juste avant l'étape 7. Tout écart avec la baseline de l'étape 0 arrête les écritures et déclenche l'étape 6b en lecture seule ; attribuer la dérive avec `git reflog --date=iso` et `git reflog show --date=iso origin/main`, ne jamais se l'approprier ni corriger l'état d'une autre session sans instruction.
11. **Worktree occupé** : si le préflight trouve une branche autre que `main` ou un worktree sale, ne jamais `switch`, `stash`, `add`, `commit`, `clean` ni supprimer les fichiers d'une autre session. S'arrêter, lister les chemins, attribuer avec `git reflog --date=iso` et `git reflog show --date=iso origin/main`, puis demander. Après accord explicite seulement, publier depuis un clone temporaire du remote (étape 0b) et exécuter les étapes 1 à 9 dans ce clone ; le dépôt d'origine reste en lecture seule. Les gardes de merge et de push comparent des hashes complets (`rev-parse`, 40 caractères en SHA-1), jamais des hashes abrégés.
12. **Achèvement externe** : si un tiers a fast-forwardé `main` et poussé le commit de cette session, vérifier `origin/main` et les blobs distants, puis rapporter « push externe » avec l'horodatage observé dans le reflog. Ne pas repousser, ne pas annuler, ne pas réécrire. Supprimer la branche temporaire de cette session avec `-d` seulement si elle est contenue dans `origin/main` ; sinon la conserver et demander.
13. **Cible de republication unique** : si plusieurs clones du même remote contiennent l'archive, un seul reçoit la publication (étape 0a). Ne jamais basculer, `stash` ni committer dans un dépôt de Skill resté sur `master` ; ne jamais republier une ref `merge/*` ni écrire dans plusieurs clones. Un `RESULT STALE` global qui subsiste après publication vient de ces refs hors périmètre : le rapporter, ne pas le corriger.

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
git -C "<depot>" branch --list "merge/skill-<nom>*"
git -C "<depot>" reflog --date=iso -n 20
git -C "<depot>" reflog show --date=iso origin/main -n 10
```

Exiger `RESULT PASS`, la branche `main`, un worktree propre et un `origin` qui correspond au dépôt visé. Consigner la branche, `HEAD`, `origin/main`, les branches `merge/skill-<nom>*` existantes et les dernières entrées de reflog (HEAD et `origin/main`) : c'est la baseline des étapes 6 et 7. Un nom déjà pris impose la variante horodatée de l'étape 2. Le dépôt peut être partagé avec une autre session Qoder ; ne pas supposer que cet état reste vrai pendant l'opération. Si la branche n'est pas `main` ou si le worktree est sale : ne rien écrire dans ce dépôt (aucun `switch`, `stash`, `add`, `commit`, `clean`), lister les chemins, attribuer avec `git reflog --date=iso` et `git reflog show --date=iso origin/main`, puis demander (voir `commit-skill-work`). Si l'utilisateur autorise une publication isolée, suivre l'étape 0b ; sinon s'arrêter. Si un autre clone du même remote est propre sur `main`, appliquer d'abord l'étape 0a. La racine du projet n'est pas forcément un dépôt : localiser le vrai dépôt avec `git -C`, ne pas en déduire un chemin.

### 0a. Choisir l'unique clone d'archive (rapport STALE multi-dépôts)

À exécuter quand le rapport d'archives liste plusieurs dépôts ou refs, ou quand le clone nommé n'est pas sur `main`. Lecture seule dans tous les candidats : ni `fetch`, ni `switch`, ni `stash`, ni commit.

1. **Périmètre** — ne retenir que la ligne `ARCHIVE main, origin/main` du dépôt d'archive confirmé. Les `origin/merge/*` et les `origin/main` d'autres clones sont hors périmètre : les premiers ne sont pas des ancêtres de `main` (instantanés de branches de fusion), les seconds sont des refs locales en retard (ancêtres de `main`). Vérifié le 2026-10-26 par `git merge-base --is-ancestor`. Ne jamais les republier, lancer `git fetch` dessus ni les supprimer.
2. **Candidats** — les chemins `== REPO` du rapport et ceux nommés par l'utilisateur :

```bash
for repo in "<clone-1>" "<clone-2>"; do
  echo "== $repo"
  git -C "$repo" remote get-url origin
  git -C "$repo" rev-parse --abbrev-ref HEAD
  git -C "$repo" rev-parse HEAD
  git -C "$repo" rev-parse origin/main
  git -C "$repo" status --porcelain=v1
  git -C "$repo" ls-remote origin refs/heads/main
done
```

3. **Sélection** — un clone qualifie si son `origin` est l'URL de l'archive, sa branche est `main`, son worktree est propre et `HEAD` égale `ls-remote origin refs/heads/main`.
   - Un seul qualifié : le retenir comme `<depot>`, relancer l'étape 0 dessus et consigner le choix et sa raison ; pas d'étape 0b, la baseline des étapes 6 et 7 devient celle de ce clone.
   - Plusieurs qualifiés : ils sont équivalents ; utiliser celui nommé par l'utilisateur, sinon demander ; n'écrire que dans un seul.
   - Aucun qualifié : ne pas forcer les autres clones ; s'arrêter et demander, puis 0b seulement après accord.
4. **Dépôt source** — un dossier Skill peut être lui-même un dépôt sur `master` avec `origin/skill/<nom>` : c'est la source fonctionnelle, jamais la destination d'archive. Ne pas y basculer, ne pas y committer ; son `origin/main` peut être en retard et n'est pas corrigé ici. Ce cas n'est pas un « worktree occupé » au sens du contrat 11. Si l'utilisateur a explicitement nommé ce dépôt comme cible alors qu'un autre clone qualifie, demander avant d'en changer.

### 0b. Publication depuis un clone isolé (worktree occupé)

À n'utiliser qu'après accord explicite. Conserver le chemin d'origine sous `<depot-original>` ; remplacer ensuite `<depot>` par `"$tmp/repo"` et exécuter les étapes 1 à 9 dans le clone. Le dépôt d'origine reste en lecture seule.

```bash
url="$(git -C "<depot-original>" remote get-url origin)"
tmp="$(mktemp -d "$HOME/.qoder/tmp/publish-<nom>.XXXXXX")"
git clone --branch main --single-branch "$url" "$tmp/repo"
git -C "$tmp/repo" rev-parse --abbrev-ref HEAD
git -C "$tmp/repo" rev-parse HEAD origin/main
git -C "$tmp/repo" status --porcelain=v1
```

Exiger `main`, `HEAD` égal à `origin/main` et un worktree propre. La baseline des étapes 6 et 7 est celle du clone, pas celle du dépôt d'origine. Ne pas exécuter `fetch`, `switch`, `merge`, `stash` ou `clean` dans le dépôt d'origine, ne pas y créer de worktree (`git worktree add`) et ne pas modifier sa configuration. Le clone prend l'état réel du remote, même si l'`origin/main` local du dépôt d'origine est en retard : ne pas corriger ce dernier. Avant la copie, un contrôle `--ref origin/main --from remote` peut renvoyer `MISMATCH` si l'archive est périmée ; c'est attendu et ne bloque pas la copie.

### 0c. Choisir la cible quand elle n'est pas nommée

À exécuter avant l'étape 0 quand l'utilisateur dit «继续下一个», «继续» ou «archive le prochain Skill» sans nommer le Skill. Ne jamais deviner silencieusement la cible.

```bash
repo="<depot>"
arch="$HOME/.qoder/tmp/arch-now.txt"
[ -d "$repo/.qoder/skills" ] || { echo STOP_ARCHIVE; exit 1; }
ls "$repo/.qoder/skills" | sort > "$arch"
for d in "$HOME/.qoder/skills"/*/; do
  n="$(basename "$d")"
  [ -f "$d/SKILL.md" ] || continue
  grep -qx "$n" "$arch" && continue
  printf '%s %s\n' "$(stat -c '%y' "$d/SKILL.md" | cut -d. -f1)" "$n"
done | sort -r
rm -f "$arch"
```

La sortie liste les Skills du dossier utilisateur absents de l'archive, du plus récemment modifié au plus ancien. Poser ensuite une seule question (`AskUserQuestion`) : recommander le premier, proposer les deux suivants, consigner le choix. Si l'utilisateur a déjà délégué le choix («继续, prends le plus récent»), prendre le premier, mais annoncer son nom et son `mtime` avant de commencer.

- Le diff porte sur le **nom de dossier** du clone d'archive retenu à l'étape 0a, pas sur le champ `name` du frontmatter ; seul le dossier utilisateur est scanné. Une cible de niveau projet doit être nommée explicitement.
- Recalculer la liste avant chaque Skill : c'est un instantané. Observé le 2026-10-26 : `USER=69 ARCHIVE=9` (60 non archivés), puis 10 et 11 entrées après deux publications, la cible publiée disparaissant du diff. Relu le 2026-10-27 : `ARCHIVE=13`, 56 non archivés, l'archive ayant encore bougé. Après un push d'une autre session, refaire l'étape 1 (`fetch`) avant de la recalculer.
- Un Skill déjà présent dans l'archive est une **mise à jour** : message `docs(skill): actualiser l'archive <nom> (<hash court du HEAD source>)` (étape 5) et `MISMATCH` attendu à l'étape 8 tant qu'il n'est pas republié.

### 1. Aligner main

```bash
git -C "<depot>" fetch origin
git -C "<depot>" rev-parse HEAD origin/main
```

Les deux hashes doivent être égaux. Si `main` est derrière, avancer en fast-forward uniquement. Si les hashes divergent, s'arrêter : ne pas rebaser, ne pas forcer. Si `origin/main` diffère de la baseline de l'étape 0, une autre session ou le distant a avancé : relire l'historique, repartir de cette nouvelle valeur et recréer la branche temporaire à l'étape 2 ; ne pas réutiliser une base périmée.

### 2. Créer la branche temporaire depuis main

Si `merge/skill-<nom>` existe déjà, ne pas la réutiliser : créer une branche unique horodatée depuis le même `origin/main`.

```bash
base="$(git -C "<depot>" rev-parse origin/main)"
branch="merge/skill-<nom>"
if git -C "<depot>" show-ref --verify --quiet "refs/heads/$branch"; then
  branch="merge/skill-<nom>-$(date +%Y%m%d-%H%M%S)"
  if git -C "<depot>" show-ref --verify --quiet "refs/heads/$branch"; then
    echo STOP_BRANCH_NAME
    exit 1
  fi
fi
git -C "<depot>" switch -c "$branch" origin/main
[ "$(git -C "<depot>" rev-parse --abbrev-ref HEAD)" = "$branch" ] || { echo STOP_BRANCH; exit 1; }
[ "$(git -C "<depot>" rev-parse HEAD)" = "$base" ] || { echo STOP_HEAD; exit 1; }
```

Consigner `$branch` : les étapes 5 à 9 l'utilisent à la place du nom littéral. Une branche existante peut appartenir à une autre session ou à un essai précédent ; ne jamais la déplacer, la forcer ni la supprimer pour réutiliser son nom.

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

Chemins explicites uniquement, jamais `git add -A` ni `git add .`. Le message suit l'historique du dépôt ; le corps peut préciser qu'il s'agit d'une copie d'archive et que le Skill fonctionnel reste dans le dossier utilisateur. Pour une archive déjà publiée, le message observé est `docs(skill): actualiser l'archive <nom> (<hash court du HEAD source>)` ; réserver `feat(skills): ajouter le Skill <nom>` à la première publication. `git show --stat` ne doit lister que les fichiers réellement modifiés, pas les fichiers inchangés recopiés.

### 6. Avancer main en fast-forward

```bash
EXPECT_BRANCH="<nom de la branche créée à l'étape 2>"
EXPECT_HEAD="<hash complet du commit de l'étape 5>"
EXPECT_ORIGIN="<hash complet de origin/main de l'étape 1>"
[ "$(git -C "<depot>" rev-parse --abbrev-ref HEAD)" = "$EXPECT_BRANCH" ] || { echo STOP_BRANCH; exit 1; }
[ "$(git -C "<depot>" rev-parse HEAD)" = "$EXPECT_HEAD" ] || { echo STOP_HEAD; exit 1; }
[ "$(git -C "<depot>" rev-parse origin/main)" = "$EXPECT_ORIGIN" ] || { echo STOP_ORIGIN; exit 1; }
[ -z "$(git -C "<depot>" status --porcelain=v1)" ] || { echo STOP_DIRTY; exit 1; }
git -C "<depot>" switch main
[ "$(git -C "<depot>" rev-parse --abbrev-ref HEAD)" = "main" ] || { echo STOP_BRANCH; exit 1; }
[ "$(git -C "<depot>" rev-parse HEAD)" = "$EXPECT_ORIGIN" ] || { echo STOP_HEAD; exit 1; }
git -C "<depot>" merge --ff-only "$EXPECT_BRANCH"
git -C "<depot>" log --oneline -2
git -C "<depot>" status -sb
```

Avant de basculer : la branche doit être `$EXPECT_BRANCH`, `HEAD` le commit de l'étape 5, `origin/main` la base de l'étape 1 et le worktree propre. Tout écart arrête les écritures et renvoie à l'étape 6b (lecture seule) ; inspecter `git reflog --date=iso` et ne pas attribuer le changement à cette session. Les gardes comparent les hashes complets rendus par `rev-parse` : un hash abrégé (`c669d02`) comparé à un hash complet (`c669d029…`) produit un faux `STOP_HEAD` (observé, `EXIT=31`). Après `switch main`, relire la branche et `HEAD` avant le merge. Si `main` est déjà extraite dans un autre worktree (`git worktree list`), s'arrêter et demander.

Attendre `Fast-forward`, un seul commit ajouté et `[ahead 1]`. Si `--ff-only` refuse, `main` a bougé : vérifier dans le reflog si le mouvement vient de cette session ou d'une autre, puis revenir à l'étape 2, recréer la branche depuis le nouveau `origin/main` et recopier. Ne jamais utiliser `--no-ff` ni forcer, ni présenter un changement externe comme le sien. Si une autre session a déjà avancé `main` avec le commit de cette étape, ne pas relancer le merge : passer à l'étape 6b.

### 6b. Reprise après dérive externe (lecture seule)

À exécuter après tout `STOP_BRANCH`, `STOP_ORIGIN` ou `STOP_DIRTY` inexpliqué, sans plus écrire dans le dépôt. Ne pas relancer `switch`, `merge`, `push`, `reset` ni `checkout` : seulement lire et attribuer. Le `fetch` ci-dessous ne met à jour que les refs distantes ; aucune branche locale, aucun worktree et aucun commit n'est modifié.

```bash
branch="<nom de la branche créée à l'étape 2>"
commit="$(git -C "<depot>" rev-parse "$branch")"
git -C "<depot>" fetch origin
origin_main="$(git -C "<depot>" rev-parse origin/main)"
main_head="$(git -C "<depot>" rev-parse main)"
git -C "<depot>" ls-remote origin refs/heads/main
git -C "<depot>" reflog --date=iso -n 12
git -C "<depot>" reflog show --date=iso origin/main -n 8
if git -C "<depot>" merge-base --is-ancestor "$commit" origin/main; then
  echo EXTERNAL_MERGED
else
  echo NOT_MERGED
fi
```

Décision :

| Constat | Action |
|---|---|
| `EXTERNAL_MERGED`, `origin_main == commit`, `main_head == commit`, worktree propre, vérificateur `--ref origin/main --from remote` `RESULT PASS` | un tiers a fait le fast-forward et le push : rapporter « push externe » avec l'horodatage `update by push` du reflog ; ne pas pousser ni annuler ; supprimer seulement `$branch` avec `-d` |
| `EXTERNAL_MERGED` mais `origin_main != commit` ou vérificateur non `PASS` | le tiers a avancé au-delà ou modifié l'archive : conserver `$branch`, rapporter la divergence, demander |
| `NOT_MERGED` | le commit de cette session n'est pas dans `origin/main` : conserver `$branch`, ne pas merger/pousser, demander |
| `main_head != origin_main` | `main` locale a divergé : ne pas `reset`, ne pas `checkout`, rapporter et demander |

Dans tous les cas, ne jamais supprimer ni déplacer une branche d'une autre session (`merge/skill-<nom>` initiale, `skill/<nom>`, etc.) et ne jamais attribuer le push externe à cette session. L'horodatage du reflog est une observation locale, pas l'heure du serveur.

### 7. Pousser (sur instruction explicite)

Si l'étape 6b a conclu `EXTERNAL_MERGED` avec `origin/main == commit`, ne pas exécuter le push de cette étape : passer directement à l'étape 8. Le push est alors externe.

```bash
EXPECT_HEAD="<hash complet du commit de fusion>"
EXPECT_BASE="<hash complet de origin/main attendu, celui de l'étape 6>"
git -C "<depot>" fetch origin
[ "$(git -C "<depot>" rev-parse --abbrev-ref HEAD)" = "main" ] || { echo STOP_BRANCH; exit 1; }
[ "$(git -C "<depot>" rev-parse HEAD)" = "$EXPECT_HEAD" ] || { echo STOP_HEAD; exit 1; }
[ "$(git -C "<depot>" rev-parse origin/main)" = "$EXPECT_BASE" ] || { echo STOP_ORIGIN; exit 1; }
[ "$(git -C "<depot>" ls-remote origin refs/heads/main | cut -f1)" = "$EXPECT_BASE" ] || { echo STOP_REMOTE; exit 1; }
git -C "<depot>" push origin main
```

Avant de pousser : la branche doit être `main`, `HEAD` le commit de fusion, `origin/main` et `ls-remote` égaux à la base de l'étape 6. Si le fetch a avancé `origin/main`, une autre session a poussé : `STOP_ORIGIN` arrête les écritures et renvoie à l'étape 6b ; ne pas rebaser, merger ni forcer. Les gardes comparent des hashes complets, jamais des hashes abrégés.

Attendre une ligne de la forme `<ancien>..<nouveau>  main -> main`. Jamais `--force` ni `-f`. Si le push est rejeté, relire `git log HEAD..origin/main` et `git reflog --date=iso`, puis demander avant toute action.

### 8. Vérifier le distant (si un push a eu lieu, y compris externe)

```bash
git -C "<depot>" rev-parse HEAD
git -C "<depot>" ls-remote origin refs/heads/main
py -3 "C:/Users/Administrateur/.qoder/skills/publier-skill-qoder-vers-depot-git/scripts/verifier_archive_skill.py" --source "<skill>" --repo "<depot>" --ref origin/main --from remote
```

Le hash local et le hash `refs/heads/main` doivent être identiques, puis le script doit rendre `RESULT PASS`. Un push externe se vérifie de la même façon, mais le rapport l'étiquette « push externe » et rappelle qu'il n'a pas été exécuté par cette session.

Sans push, `origin/main` pointe encore sur le commit précédent : le mode `remote` renvoie `MISSING` sur tous les fichiers et `RESULT FAIL` (rejoué le 2026-10-26 sur `ddfd179` non poussé), ce n'est pas un défaut de copie. Ne pas pousser sans instruction : consigner `Distant : non exécuté (push non effectué)`.

Si la ref contient déjà une version antérieure du Skill (par exemple l'archive `ddfd179` après modification de la source), le script renvoie `MISMATCH` avec deux hashes différents, pas `MISSING` : c'est aussi une archive périmée. Republier ; ne pas comparer une ref figée à une source qui a changé.

Rejeu du détecteur d'archives (facultatif ; `find_stale_archives.py` du Skill `commit-skill-work`) : la ligne de l'archive cible doit afficher `FRESH N/N`. Un `RESULT STALE` / exit 1 résiduel vient des refs `merge/*` et des `origin/main` d'autres clones, laissés hors périmètre à l'étape 0a ; ce n'est pas un échec de republication. Le signaler sans modifier ces refs.

Contrôle manuel possible pour un fichier, avec la conversion MSYS désactivée :

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' git -C "<depot>" show "origin/main:<chemin>" | sha256sum
sha256sum "<skill>/<chemin>"
```

### 9. Nettoyer

```bash
branch="<nom de la branche créée à l'étape 2>"
if git -C "<depot>" show-ref --verify --quiet "refs/heads/$branch"; then
  if git -C "<depot>" merge-base --is-ancestor "$branch" origin/main; then
    git -C "<depot>" branch -d "$branch"
  else
    echo "CONSERVER $branch (non contenu dans origin/main)"
  fi
else
  echo "BRANCHE $branch DEJA ABSENTE (nettoyée en 6b)"
fi
git -C "<depot>" branch -vv
git -C "<depot>" status -sb
```

Après un push, la suppression doit être confirmée par `Deleted branch ... (was <hash>)` et l'état final doit être `## main...origin/main` sans écart. Le test d'ancêtre autorise `-d` même si cette session n'a pas poussé, lorsque le commit a été absorbé par un push externe ; ne jamais l'étendre à une autre branche.

Sans push, la branche n'est pas contenue dans `origin/main` : le garde affiche `CONSERVER` et ne tente pas `-d`. Un `-d` direct serait refusé même quand `main` contient le commit, car le contrôle porte sur `refs/remotes/origin/main`. Message observé le 2026-10-26 :

```text
warning: not deleting branch 'merge/skill-<nom>' that is not yet merged to
         'refs/remotes/origin/main', even though it is merged to HEAD
error: the branch 'merge/skill-<nom>' is not fully merged
```

Conserver alors la branche, la signaler dans le rapport et terminer avec `## main...origin/main [ahead 1]`, état attendu tant que le push n'a pas eu lieu. La supprimer après le push. `git branch -D` seulement sur instruction explicite de l'utilisateur. Si un push externe a absorbé le commit, `merge-base --is-ancestor` réussit et `-d` supprime la branche ; le message observé est `Deleted branch ... (was 2dade6c)`. Cela ne signifie pas que cette session a poussé.

Une branche distante indépendante `skill/<nom>`, poussée avant la fusion, reste sur `origin` : ne pas la supprimer sans instruction explicite. Vérifier avec `branch -vv` que `main` suit `origin/main` et non `origin/skill/<nom>`.

Dans la variante 0b, après le push et la suppression de la branche, supprimer le clone créé à l'étape 0b, uniquement après avoir vérifié le préfixe :

```bash
case "$tmp" in
  "$HOME"/.qoder/tmp/publish-<nom>.*) rm -rf "$tmp" ;;
  *) echo "REFUS $tmp"; exit 1 ;;
esac
```

Revenir ensuite au dépôt d'origine en lecture seule pour consigner son état final :

```bash
git -C "<depot-original>" rev-parse --abbrev-ref HEAD
git -C "<depot-original>" rev-parse HEAD
git -C "<depot-original>" rev-parse origin/main
git -C "<depot-original>" status --porcelain=v1
```

Le dépôt d'origine doit être inchangé par cette session ; son `origin/main` local peut rester en retard jusqu'au prochain `git fetch`, qui n'est pas exécuté ici. Consigner cette valeur et ne pas la corriger.

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
| `fatal: a branch named 'merge/skill-<nom>' already exists` | une autre session ou un essai précédent occupe le nom | créer `merge/skill-<nom>-YYYYMMDD-HHMMSS` depuis `origin/main` ; ne pas réutiliser, déplacer ni supprimer l'existante |
| `STOP_BRANCH` juste après le commit, avec un `checkout` externe dans le reflog | une autre session a changé la branche du worktree | arrêter les écritures, passer à l'étape 6b, attribuer par reflog ; ne pas se réapproprier le mouvement |
| `STOP_ORIGIN` après un `fetch`, avec `origin/main` qui contient le commit | un tiers a fast-forwardé et poussé le commit | 6b : vérifier `ls-remote` et les blobs `origin/main` ; rapporter « push externe » ; ne pas repousser ni annuler |
| `branch -d` réussit alors que cette session n'a pas poussé | la branche est contenue dans `origin/main` après un push externe | attendu ; supprimer seulement `$branch` ; ne pas généraliser aux autres branches |
| `main` locale déjà avancée par une autre session | fast-forward externe | ne pas `reset`/`checkout` ; vérifier `main == origin/main` et rapporter |
| branche de Skill sans ancêtre commun avec `main` | dépôt de Skill initialisé séparément, puis poussé sur une branche dédiée | ne pas la fusionner ni ouvrir une PR de merge ; recréer `merge/skill-<nom>` depuis `main` et copier |
| `fatal: not a git repository` à la racine du projet | la racine n'est pas un dépôt | énumérer les `.git` imbriqués, puis `git -C` sur le vrai dépôt |
| `fatal: cannot change to '...ASTRO-Q°ODE_SYSTEME'` | chemin non ASCII ou relatif résolu depuis un autre répertoire courant | vérifier avec `test -d`, puis passer un chemin absolu |
| la branche locale suit `origin/skill/...` après un push | refspec `HEAD:refs/heads/<branche>` | vérifier `git -C "<depot>" branch -vv` ; préférer `git push origin main` |
| `error: the branch 'merge/skill-<nom>' is not fully merged` alors que `main` contient le commit | commit non poussé : `-d` compare à `refs/remotes/origin/main`, créé depuis `origin/main` | conserver la branche et la signaler ; pousser puis relancer `-d` ; `-D` sur accord explicite seulement |
| vérificateur `--from remote` : `MISSING` sur tous les fichiers alors que la copie worktree est `PASS` | push non effectué, `origin/main` inchangé | ne pas pousser sans instruction ; consigner le contrôle distant comme non exécuté |
| worktree sur une branche autre que `main` avec des fichiers non commités d'une autre session | une autre session Qoder travaille dans le même dépôt | ne rien écrire (`switch`, `stash`, `clean`) ; attribuer via reflog ; clone isolé après accord |
| `STOP_HEAD` juste après le commit alors que `HEAD` est le bon commit | hash abrégé comparé à un hash complet | comparer les sorties complètes de `rev-parse` (40 caractères en SHA-1) |
| `fatal: Not a valid object name <hash>` dans le dépôt d'origine après une publication isolée | le commit existe côté remote mais n'a pas été récupéré localement | vérifier `git ls-remote origin refs/heads/main` ; ne pas conclure à un échec |
| `origin/main` local en retard après une publication isolée | le dépôt d'origine n'a pas fait `fetch` | attendu ; signaler dans le rapport ; ne pas fetch/merge sans instruction |
| `RESULT STALE` global alors que l'archive cible affiche `FRESH N/N` | le verdict agrège des refs `merge/*` et des `origin/main` d'autres clones | lire par archive, pas le verdict global ; ne rien modifier hors cible |
| clone nommé sur `master`, autre clone du même remote propre sur `main` à `HEAD == ls-remote` | source fonctionnelle vs clone d'archive | ne pas basculer la source ; publier depuis le clone `main` (étape 0a), sans 0b |
| «继续» ou «继续下一个» traité comme une autorisation de push pour le Skill suivant | contrat 6 : l'autorisation nomme un commit | redemander, ou consigner un accord de lot explicite (dépôt, branche, périmètre) avant de pousser |
| liste des Skills à archiver réutilisée d'un tour à l'autre | l'archive a gagné le Skill publié au tour précédent | recalculer le diff de l'étape 0c avant chaque Skill |
| `warning: ... CRLF will be replaced by LF` | normalisation des fins de ligne | informationnel ; ne pas réécrire le dépôt |

## Définition de terminé

- [ ] `skill-file-qa` : `RESULT PASS` avant toute copie.
- [ ] Copie limitée au fichier `SKILL.md` et aux dossiers `references` et `scripts` ; aucun `.git`, cache ou fichier hors périmètre ; l'assertion `find` de l'étape 3 ne renvoie rien et le vérificateur ne signale aucun `EXTRA`.
- [ ] Vérificateur en mode worktree : `RESULT PASS`, un `OK` par fichier.
- [ ] Un seul commit sur la branche de fusion retenue (`merge/skill-<nom>` ou variante horodatée), chemins explicites, message conforme à l'historique.
- [ ] Branche de fusion nommée sans collision : nom existant consigné à l'étape 0, variante horodatée unique créée et utilisée dans les étapes 5 à 9 ; aucune branche existante déplacée ou supprimée.
- [ ] `main` avancée par `Fast-forward` ; aucun merge commit.
- [ ] Push effectué seulement sur demande ; si non poussé, l'annoncer et ne pas présenter le distant comme validé. Un push externe est rapporté comme tel, jamais revendiqué.
- [ ] Si push (interne ou externe) : hash local égal à `ls-remote origin refs/heads/main` et vérificateur en mode remote `RESULT PASS` ; sinon contrôle distant marqué non exécuté.
- [ ] Nettoyage : `$branch` supprimée avec `-d` seulement si contenue dans `origin/main` ; sinon conservée et signalée, sans `-D` ; aucune autre branche touchée.
- [ ] Baseline de l'étape 0 consignée (branche, `HEAD`, `origin/main`, branches `merge/skill-<nom>*`), puis branche/`HEAD`/`origin/main` relus avant le merge et avant le push ; aucun écart inexpliqué.
- [ ] Toute dérive externe arrête les écritures, passe en 6b et est attribuée via `git reflog --date=iso` et `git reflog show --date=iso origin/main`, sans revendication.
- [ ] Achèvement externe : `origin/main` contient le commit, `ls-remote` et blobs vérifiés, rapport « push externe » avec horodatage observé, aucun rollback ni nouveau push.
- [ ] `MISMATCH` qualifié : archive périmée si la ref est antérieure, MSYS réservé à `fatal: ambiguous argument` hors script.
- [ ] Rapport : réserve d'archive, branche retenue, push interne/externe/non effectué, reprise 6b et chemins relatifs signalés.
- [ ] Worktree occupé : arrêt sans écriture, chemins listés, dérive attribuée via reflog, accord explicite avant clone isolé.
- [ ] Variante isolée : clone depuis l'URL remote, `main` = `origin/main`, worktree propre, étapes 1 à 9 exécutées dans le clone ; dépôt d'origine intact.
- [ ] Gardes merge/push : comparaison de hashes complets ; aucun `STOP_*` inexpliqué.
- [ ] Variante isolée terminée : branche temporaire et clone supprimés ; `origin/main` local du dépôt d'origine signalé s'il est en retard.
- [ ] Cible unique verrouillée (étape 0a) : candidats listés, un seul clone retenu et sa raison consignée ; dépôt source sur `master` intact (aucun `switch`, `stash`, commit).
- [ ] STALE résiduel : archive cible `FRESH N/N` ; refs `merge/*` et autres clones listés comme hors périmètre et non modifiés.
- [ ] Cible non nommée : diff utilisateur/archive recalculé à l'étape 0c, tri par `mtime` du `SKILL.md`, question unique (ou délégation explicite consignée) ; compteurs avant/après et choix dans le rapport.
- [ ] Push : autorisation liée au commit publié ; «continue»/«继续» ne l'étend pas ; accord de lot consigné avec dépôt, branche et périmètre s'il est accordé.

## Rapport

```text
Skill : <nom> | source <chemin absolu>
Depot : <chemin absolu> | remote <URL> | branche main
Copie : <N> fichiers sous .qoder/skills/<nom> | SHA-256 worktree PASS
Commit : <hash court> feat(skills): ajouter le Skill <nom> | docs(skill): actualiser l'archive <nom> (<HEAD source>)
Branche : merge/skill-<nom> | merge/skill-<nom>-<horodatage> (collision)
Main : <ancien>..<nouveau> fast-forward | push oui/non/externe
Push : oui | non | externe à HH:MM:SS (reflog origin/main, non exécuté par cette session)
Série : <N> non archivés avant/après | cible choisie par question unique | délégation explicite | cible nommée
Autorisation : push par Skill | lot (dépôt/branche/périmètre) | non accordée
État : <branche>@<hash> | origin/main <hash> | relu avant merge et push | dérive : aucune|<reflog>
Reprise : aucune | EXTERNAL_MERGED | NOT_MERGED | main locale divergente
Distant : HEAD <hash> | blobs PASS/FAIL | non exécuté (push non effectué)
Nettoyage : branche supprimée | conservée (non contenue dans origin/main) | autre branche intacte
Variante : standard | clone isolé
Cible : <depot> | clone <k>/<N> qualifié | source <chemin> intacte
STALE résiduel : <refs> hors périmètre, non modifiés
Source repo : <chemin> | intact | <branche>@<hash> | origin/main local <hash>
Clone : <chemin> | supprimé | créé depuis <URL remote>
Gardes : HEAD <hash complet> | origin/main <hash complet> | STOP_* : aucun
Reserve : archive, chemins relatifs non garantis dans ce depot
```

## Ressources

- `scripts/verifier_archive_skill.py` : compare en lecture seule les SHA-256 de la source avec la copie worktree ou les blobs d'une ref distante, et signale tout fichier `EXTRA` présent dans la destination ; sortie ASCII, codes 0/1/2.
- `references/preuves-publication.md` : transcription des sorties observées (commit `3a4732a`, 5 hashes, échec MSYS, archivage non poussé `ddfd179`, dérive d'état et archive périmée, collision de branche, push externe et reprise 6b, plusieurs clones du même remote et STALE résiduel) et re-vérifications du 2026-10-26.
- `commit-skill-work` : localisation du dépôt, classification des changements, commit et push de base.
- `skill-file-qa` : validation statique du Skill avant publication.
- `skill-update-concurrency-safe` : édition sûre du Skill source avant publication.
