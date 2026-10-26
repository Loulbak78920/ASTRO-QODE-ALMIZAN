# Appliquer le contenu d'un Skill à `main` sans ancêtre commun

## Quand l'utiliser

`main` porte l'arbre du projet (dont `.qoder/skills/<nom>/`) et la branche de travail du Skill a une histoire sans ancêtre commun : `git merge-base origin/main HEAD` reste vide (exit 1). Une fusion classique est interdite ; `--allow-unrelated-histories` importerait tout l'arbre projet dans le Skill.

La seule opération correcte est un transfert de contenu : construire un commit dont le parent est `origin/main`, dont l'arbre est celui de `origin/main` avec les fichiers du Skill remplacés par les octets validés, puis pousser en fast-forward.

## Préconditions

- Accord explicite de l'utilisateur pour modifier `main`.
- Le dossier est le Skill installé : ne pas y extraire `main` (`git checkout main` écraserait le paquet).
- `origin` pointe vers le dépôt attendu ; `git remote -v` lu.
- Gate de concurrence terminée et version validée (parité, `skill-file-qa`, manifeste hors Skill, invocation).
- `git fetch origin` exécuté ; `origin/main` connu.

## Diagnostic

```bash
git -C "<depot>" remote -v
git -C "<depot>" fetch origin
git -C "<depot>" merge-base origin/main HEAD; echo "EXIT=$?"
git -C "<depot>" ls-tree origin/main -- ".qoder/skills/<nom>"
```

- `EXIT=1` et sortie vide : aucun ancêtre commun ; c'est le cas visé.
- `ls-tree` vide : `main` ne contient pas encore le Skill ; les entrées seront des ajouts.
- Ne pas utiliser `git merge`, `git rebase` ni `git checkout main` dans ce worktree.
- Éviter `origin/main:<chemin>` sous Git Bash/MSYS : la ref est réécrite (`fatal: ambiguous argument 'origin\main;...'`). Utiliser `ls-tree <ref> -- <chemin>` puis `cat-file blob <oid>`.

## Gel et baseline

Avant de construire le commit :

1. `wait_chat_sessions` sur les écrivains connus jusqu'à `ready` ou `cold`.
2. Quatre échantillons SHA-256 identiques à 5 s d'intervalle sur `SKILL.md`, `scripts/` et `references/`.
3. Rejouer parité, `skill-file-qa`, manifeste hors Skill et invocation sur ces octets.
4. Juste avant le push, refaire le `diff` live vs manifeste.

## Construire le commit sans checkout

L'index temporaire laisse `HEAD`, l'index réel et le worktree intacts. `hash-object --path` applique les mêmes filtres que `git add` (`core.autocrlf`, `.gitattributes`). Ajuster la liste `files` à l'inventaire validé, sans cache.

```bash
idx="$(mktemp)"
GIT_INDEX_FILE="$idx" git -C "<depot>" read-tree origin/main || exit 1
files="SKILL.md scripts/find_stale_archives.py scripts/inspect_git_state.py scripts/run-fixture.sh references/skill-zh.md references/contenu-vers-main.md"
for f in $files; do
  blob=$(git -C "<depot>" hash-object -w --path=".qoder/skills/<nom>/$f" "<dossier-skill>/$f") || exit 1
  GIT_INDEX_FILE="$idx" git -C "<depot>" update-index --add --cacheinfo "100644,$blob,.qoder/skills/<nom>/$f" || exit 1
done
tree=$(GIT_INDEX_FILE="$idx" git -C "<depot>" write-tree) || exit 1
commit=$(git -C "<depot>" commit-tree "$tree" -p origin/main -m "<message>") || exit 1
rm -f "$idx"
```

- `commit-tree -p origin/main` rend le push fast-forward par construction.
- Un fichier supprimé côté Skill se retire avec `update-index --force-remove` ; ne pas recopier tout l'arbre projet.
- Garder l'index temporaire hors du dépôt et le supprimer ensuite.

## Vérifier avant le push

```bash
git -C "<depot>" cat-file -p "$commit" | head -3
git -C "<depot>" diff-tree --no-commit-id --name-status -r "$commit"
prefix=".qoder/skills/<nom>"
for f in $files; do
  coid=$(git -C "<depot>" ls-tree --format='%(objectname)' "$commit" -- "$prefix/$f") || exit 1
  n=$(printf '%s\n' "$coid" | grep -c . || true)
  exp=$(git -C "<depot>" hash-object --path="$prefix/$f" "<dossier-skill>/$f") || exit 1
  [ "$n" -eq 1 ] && [ "$coid" = "$exp" ] || { echo "MISMATCH $f count=$n commit=$coid exp=$exp"; exit 1; }
  echo "MATCH $f $coid"
done
git -C "<depot>" status --porcelain=v1
```

- Le parent doit être `origin/main` ; `diff-tree` ne doit lister que les chemins attendus.
- `--format='%(objectname)'` doit précéder le commit et le pathspec : placé après `-- <chemin>`, Git le traite comme un chemin et l'ignore silencieusement (`RC=0`), en renvoyant le format par défaut `<mode> <type> <oid>\t<chemin>`.
- La sortie par défaut est tabulée en deux champs : `cut -f1` renvoie `100644 blob <oid>` (jamais l'OID) et `cut -f3` est vide ; extraire avec `--format`, jamais avec `cut`.
- Exiger exactement une ligne non vide (`n=1`) : un chemin absent renvoie une sortie vide avec `RC=0`.
- Chaque OID de `ls-tree` doit égaler le `hash-object --path` correspondant ; avec `core.autocrlf=true`, comparer les OID, pas les SHA-256 (`cat-file blob <oid> | sha256sum` n'égale la source que sans filtre eol).
- `git status` doit rester vide et la branche courante inchangée : le worktree n'a pas bougé.

## Push et vérification distante

```bash
git -C "<depot>" push origin "$commit:refs/heads/main"
git -C "<depot>" ls-remote origin refs/heads/main
```

- Le push doit être accepté sans `--force` ; un rejet signale que `origin/main` a avancé : reprendre au diagnostic, sans forcer.
- `ls-remote` doit renvoyer le hash de `$commit`.
- La branche locale (`master`, `skill/<nom>`) n'est pas fusionnée : l'historique reste sans ancêtre commun, seul le contenu de `main` progresse.

## Après le push

```bash
git -C "<depot>" fetch origin
py -3 "C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py" --skill "<dossier-skill>" --search-root "<racine-espace>"
```

- L'archive de ce dépôt (`origin/main`) doit être `FRESH` ; les autres clones non rafraîchis peuvent rester `STALE` : les signaler, ne pas republier.
- Si `live` a changé après le commit, ces octets appartiennent à une autre session : les signaler, ne pas les absorber.
- Ne pas présenter `master` ou `skill/<nom>` comme fusionnée : le transfert ne crée aucun lien d'ascendance.

## Pièges

| Symptôme | Cause | Action |
|---|---|---|
| `fatal: refusing to merge unrelated histories` | fusion tentée entre histoires sans ancêtre | ne pas ajouter `--allow-unrelated-histories` ; transférer le contenu (ce fichier) |
| `main` extrait dans le worktree du Skill | `git checkout main` dans le dossier installé | restaurer le paquet depuis sa source validée ; refaire le transfert sans checkout |
| `fatal: ambiguous argument 'origin\main;...'` | MSYS réécrit `ref:chemin` | `ls-tree <ref> -- <chemin>` puis `cat-file blob <oid>` |
| push rejeté (non-fast-forward) | `origin/main` a avancé après le `fetch` | refaire diagnostic, arbre et commit depuis le nouveau `origin/main` ; jamais `--force` |
| `diff-tree` liste des chemins inattendus | arbre de base incomplet ou index temporaire pollué | repartir de `read-tree origin/main` avec un index neuf |
| OID différent entre `ls-tree` et `hash-object --path` | filtre eol, chemin ou fichier erroné | vérifier `--path`, `core.autocrlf` et l'identité du fichier ; ne pas pousser |
| `MISMATCH … commit=100644 blob <oid>` alors que les OID semblent identiques | extraction par `cut -f1` sur la sortie par défaut : le premier champ tabulé vaut `<mode> blob <oid>`, et `cut -f3` est vide | extraire avec `ls-tree --format='%(objectname)'` |
| `--format='%(objectname)'` sans effet (`RC=0`, sortie par défaut `<mode> <type> <oid>\t<chemin>`) | option placée après le pathspec : Git la traite comme un chemin et l'ignore | placer `--format` avant le commit : `ls-tree --format='%(objectname)' "$commit" -- "$prefix/$f"` |
| SHA-256 source différent du blob | normalisation eol attendue | comparer les OID ; ne pas conclure à une corruption |

## Cas observé (2026-10-26)

Dépôt du Skill : `HEAD=fe57c7c` sur `master`, `origin/main=4f18419` ; `git merge-base origin/main HEAD` vide (exit 1) ; les blobs de `HEAD` égalent ceux de `origin/main` (contenu identique, histoires distinctes). La recette a été rejouée dans deux fixtures jetables (un fichier modifié ; un modifié et un ajouté) : parent = base, `diff-tree` limité aux chemins attendus, blobs identiques au disque, push fast-forward accepté, `ls-remote` égal au commit local, worktree et branche inchangés. Lors de la publication du commit `966bac0` (4 fichiers), `cut -f1` puis `--format` placé après le pathspec ont produit deux faux `MISMATCH` successifs (`commit=100644 blob <oid>`, `RC=0`) ; la forme `ls-tree --format='%(objectname)' "$commit" -- "$prefix/$f"` avec exactement une ligne non vide a donné `MATCH` 4/4 avant le push (git 2.52.0.windows.1).

## 中文版

### 何时使用

`main` 承载项目树（含 `.qoder/skills/<nom>/`），而 Skill 工作分支与其无共同祖先：`git merge-base origin/main HEAD` 为空（退出 1）。不得使用普通合并；`--allow-unrelated-histories` 会把整个项目树导入 Skill。

正确做法是内容移植：以 `origin/main` 为父提交，树取自 `origin/main` 并用已验证的 Skill 文件替换，然后 fast-forward 推送。

### 前置条件

- 用户明确同意修改 `main`。
- 当前目录是已安装的 Skill：不要在此检出 `main`（`git checkout main` 会覆盖包）。
- 已读取 `git remote -v`，`origin` 指向预期仓库。
- 并发闸门已完成，版本已验证（对等、`skill-file-qa`、Skill 外清单、实际调用）。
- 已执行 `git fetch origin`。

### 诊断

```bash
git -C "<depot>" remote -v
git -C "<depot>" fetch origin
git -C "<depot>" merge-base origin/main HEAD; echo "EXIT=$?"
git -C "<depot>" ls-tree origin/main -- ".qoder/skills/<nom>"
```

`EXIT=1` 且输出为空表示无共同祖先，正是目标场景；`ls-tree` 为空表示 `main` 尚无该 Skill，按新增处理。Git Bash/MSYS 下避免 `origin/main:<chemin>`（ref 会被改写），改用 `ls-tree` 与 `cat-file blob`。

### 冻结与基线

先 `wait_chat_sessions` 等待已知写入者转为 `ready` 或 `cold`；对 `SKILL.md`、`scripts/`、`references/` 每 5 秒采样 SHA-256，连续 4 次相同；重跑对等、`skill-file-qa`、Skill 外清单与实际调用；推送前再次比对 live 与清单。

### 构建提交（不检出）

临时索引不影响 `HEAD`、真实索引与 worktree；`hash-object --path` 与 `git add` 应用相同的过滤（`core.autocrlf`、`.gitattributes`）。按已验证清单调整 `files`，排除缓存。

```bash
idx="$(mktemp)"
GIT_INDEX_FILE="$idx" git -C "<depot>" read-tree origin/main || exit 1
files="SKILL.md scripts/find_stale_archives.py scripts/inspect_git_state.py scripts/run-fixture.sh references/skill-zh.md references/contenu-vers-main.md"
for f in $files; do
  blob=$(git -C "<depot>" hash-object -w --path=".qoder/skills/<nom>/$f" "<dossier-skill>/$f") || exit 1
  GIT_INDEX_FILE="$idx" git -C "<depot>" update-index --add --cacheinfo "100644,$blob,.qoder/skills/<nom>/$f" || exit 1
done
tree=$(GIT_INDEX_FILE="$idx" git -C "<depot>" write-tree) || exit 1
commit=$(git -C "<depot>" commit-tree "$tree" -p origin/main -m "<message>") || exit 1
rm -f "$idx"
```

`-p origin/main` 使推送天然为 fast-forward；删除的文件用 `update-index --force-remove` 移除；不要整树复制项目。

### 推送前校验

```bash
git -C "<depot>" cat-file -p "$commit" | head -3
git -C "<depot>" diff-tree --no-commit-id --name-status -r "$commit"
prefix=".qoder/skills/<nom>"
for f in $files; do
  coid=$(git -C "<depot>" ls-tree --format='%(objectname)' "$commit" -- "$prefix/$f") || exit 1
  n=$(printf '%s\n' "$coid" | grep -c . || true)
  exp=$(git -C "<depot>" hash-object --path="$prefix/$f" "<dossier-skill>/$f") || exit 1
  [ "$n" -eq 1 ] && [ "$coid" = "$exp" ] || { echo "MISMATCH $f count=$n commit=$coid exp=$exp"; exit 1; }
  echo "MATCH $f $coid"
done
git -C "<depot>" status --porcelain=v1
```

父提交必须是 `origin/main`；`diff-tree` 只应出现预期路径。`--format='%(objectname)'` 必须位于 commit 与 pathspec 之前：放在 `-- <chemin>` 之后会被当作路径而静默忽略（`RC=0`），返回默认格式 `<mode> <type> <oid>\t<chemin>`。默认输出按 Tab 分为两个字段：`cut -f1` 返回 `100644 blob <oid>`（永远不是 OID），`cut -f3` 为空；应使用 `--format` 提取，而不是 `cut`。要求恰好一行非空（`n=1`）：路径不存在时输出为空且 `RC=0`。每个 OID 必须等于对应的 `hash-object --path`；`core.autocrlf=true` 时比较 OID 而非 SHA-256；`git status` 保持为空且当前分支不变。

### 推送与远端核对

```bash
git -C "<depot>" push origin "$commit:refs/heads/main"
git -C "<depot>" ls-remote origin refs/heads/main
```

不得使用 `--force`；被拒说明 `origin/main` 已前进，应重新诊断并基于新基线重建。`ls-remote` 必须返回 `$commit`。本地分支不会被合并，历史仍无共同祖先。

### 推送之后

重新 `fetch` 并运行 `find_stale_archives.py`：本仓库 `origin/main` 的归档应为 `FRESH`；未刷新的其他克隆可为 `STALE`，只报告、不重发。若 live 在提交后变化，归另一会话所有，不得吸收。

### 陷阱

| 现象 | 原因 | 处理 |
|---|---|---|
| `fatal: refusing to merge unrelated histories` | 试图合并不相关历史 | 不要加 `--allow-unrelated-histories`；按本文件移植内容 |
| `main` 被检出到 Skill worktree | 在安装目录执行 `git checkout main` | 从已验证源恢复包；不要检出，重新移植 |
| `fatal: ambiguous argument 'origin\main;...'` | MSYS 改写 `ref:chemin` | 用 `ls-tree <ref> -- <chemin>` 与 `cat-file blob <oid>` |
| push 被拒（non-fast-forward） | `fetch` 后 `origin/main` 又前进 | 重新诊断并基于新 `origin/main` 重建；绝不 `--force` |
| `diff-tree` 出现意外路径 | 基线树不完整或临时索引被污染 | 用全新索引重新 `read-tree origin/main` |
| `ls-tree` 与 `hash-object --path` 的 OID 不同 | eol 过滤器、路径或文件错误 | 核对 `--path`、`core.autocrlf` 与文件；不要推送 |
| `MISMATCH … commit=100644 blob <oid>` 但 OID 看似相同 | 用 `cut -f1` 截取默认输出：第一个 Tab 字段是 `<mode> blob <oid>`，而 `cut -f3` 为空 | 用 `ls-tree --format='%(objectname)'` 提取 |
| `--format='%(objectname)'` 无效（`RC=0`，仍返回默认 `<mode> <type> <oid>\t<chemin>`） | 选项放在 pathspec 之后，Git 把它当路径并忽略 | 把 `--format` 放在 commit 之前：`ls-tree --format='%(objectname)' "$commit" -- "$prefix/$f"` |
| 源 SHA-256 与 blob 不同 | 预期 eol 规范化 | 比较 OID，不要判定为损坏 |

### 已观察案例（2026-10-26）

Skill 仓库：`HEAD=fe57c7c`（`master`），`origin/main=4f18419`；`git merge-base origin/main HEAD` 为空（退出 1）；`HEAD` 与 `origin/main` 的 blob 相同（内容一致、历史不同）。该做法已在两个一次性夹具中重放（一个修改文件；一个修改加一个新增）：父提交 = 基线，`diff-tree` 仅预期路径，blob 与磁盘一致，fast-forward 推送成功，`ls-remote` 等于本地提交，worktree 与分支未变。发布提交 `966bac0`（4 个文件）时，`cut -f1` 与放在 pathspec 之后的 `--format` 连续产生两次假 `MISMATCH`（`commit=100644 blob <oid>`，`RC=0`）；使用 `ls-tree --format='%(objectname)' "$commit" -- "$prefix/$f"` 并断言恰好一行非空后，推送前 `MATCH` 4/4（git 2.52.0.windows.1）。
