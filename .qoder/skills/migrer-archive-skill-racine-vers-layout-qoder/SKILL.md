---
name: migrer-archive-skill-racine-vers-layout-qoder
description: "在 Skill 仓库内把旧布局的根目录包（根 SKILL.md 与 references/scripts）迁入 `.qoder/skills/<name>/`，或处理根副本与既有嵌套包逐 blob 相同的重复：先核对真实仓库根、工作区干净、HEAD 与 origin/main、根 frontmatter name 和目标是否存在，再用逐文件 `git mv`（不编辑内容）证明 100% 重命名、0 行增删、blob OID 不变，随后对迁移包跑 skill-file-qa 与 check_package_manifest、复跑其余包，最后提交并在获授权时 fetch/推送、用远端树证明根目录不再有旧包。用于仓库根出现 SKILL.md、根 QA 报 name 与目录不匹配及 layout WARN、根包与 .qoder/skills 下同名包重复、目标目录已存在、根文件被合并恢复、迁移后需证明未改内容、git ls-tree -s 不可用、推送后远端根仍有 SKILL.md 等场景；不替代跨仓库发布（publier-skill-qoder-vers-depot-git）、README/首页展示放置决策（skill-repo-readme-placement）、一般提交（commit-skill-work）、行尾锁定（lock-lf-endings-skill-repo）或运行时绑定（verify-skill-runtime-binding）。"
---

# 将根目录旧布局 Skill 迁入 .qoder/skills

## 目标与边界

本 Skill 只处理一种仓库内迁移：仓库已经是容器布局（`.qoder/skills/<name>/` 下至少一个包），但仓库根还残留旧布局包（根 `SKILL.md`，以及 references、scripts、assets 目录）。目标是用纯重命名把包移入新布局，并用 blob OID 证明内容未变。

不适用：

- 仓库根就是唯一 Skill 的唯一副本，没有 `.qoder/skills/` 容器：先用 `verify-skill-runtime-binding` 判断运行时依赖，再决定是否改布局。
- 从用户级 Skill 目录复制或发布到仓库：用 `publier-skill-qoder-vers-depot-git`。
- 根 README、首页文档或根 `SKILL.md` 是否作为展示：用 `skill-repo-readme-placement` 做取舍。
- 一般提交、缓存清扫：用 `commit-skill-work`。
- 行尾统一：用 `lock-lf-endings-skill-repo`。
- 不新增脚本；验收复用 `skill-file-qa` 与 `skill-package-integrity-audit` 的现有脚本。

## 不可协商约束

1. 先分类，再移动。目标不存在才允许 `git mv`；目标已存在时不得覆盖。
2. 根副本与目标包逐 blob 相同时，默认只读报告并等待用户确认；删除根文件是破坏性操作，必须显式授权。
3. 根副本与目标包不同，或目标目录存在但内容不明：停止，不移动、不合并、不删除。
4. 迁移期间不编辑 `SKILL.md` 或 references、scripts、assets 目录中的内容；只做重命名。
5. 只对真实 Git 工作区操作；已安装的 `~/.qoder/skills/<name>` 目录没有 `.git` 时不要迁移。
6. 工作区必须干净，`HEAD` 必须等于 `origin/main`；不 stash、不 reset、不强推。
7. 逐文件 `git mv`，禁止 `git add -A` 或 `git add .`；只移除已经为空的目录。
8. 提交前必须证明暂存区是 100% rename、0 行增删、blob OID 不变；QA 或 manifest 任一失败不提交。
9. 推送只在明确授权时执行；推送后必须验证远端 ref 与远端树。
10. 没有实测证据时报告“未验证/未完成”，不写“已迁移/已通过”。

## 触发条件

- 仓库根出现 `SKILL.md`，而 `.qoder/skills/` 下已有其他包。
- 对仓库根跑校验器得到 `FAIL name: ... does not match directory ...` 和 layout WARN。
- 根包与 `.qoder/skills/<name>/` 下同名包重复，或根文件被某次合并恢复。
- 用户要求“统一布局”“把根包归档”“修根目录的 layout”。
- 迁移后需要证明 0 行改动、blob OID 不变，而不只是“文件还在”。
- 推送后需要证明远端根目录不再有旧 `SKILL.md` 或 references 目录。

## 0. 预检

```bash
cd "$REPO"
git rev-parse --show-toplevel
git status --porcelain
git fetch origin main
git rev-parse HEAD origin/main
git log --oneline -3 origin/main
test -d .qoder/skills && echo CONTAINER_LAYOUT || echo NOT_CONTAINER_LAYOUT
find .qoder/skills -maxdepth 1 -mindepth 1 -type d | sort
git ls-tree --name-only HEAD
```

停止条件：工作区不干净；`HEAD` 不等于 `origin/main`；没有 `.qoder/skills/`；根没有 `SKILL.md`；当前目录不是 Git 工作区。若 `HEAD` 落后，先确认是否允许 rebase；不允许就停止，不要在旧基线上迁移。

读取真实名称，不要沿用用户提到的包名：

```bash
sed -n '1,20p' SKILL.md
NAME=$(sed -n 's/^name:[[:space:]]*//p' SKILL.md | head -1 | tr -d '\r"')
case "$NAME" in
  ""|*[!a-z0-9-]*) echo "INVALID_NAME"; exit 1 ;;
esac
TARGET=".qoder/skills/$NAME"
test -e "$TARGET" && echo TARGET_EXISTS || echo TARGET_ABSENT
git ls-tree -r HEAD -- SKILL.md references scripts assets
```

`git ls-tree` 对不存在的路径返回 RC 0 和空输出，必须看输出，不要只看退出码。根 `SKILL.md` 的 `name` 与用户描述不一致时，以 frontmatter 为准；目标是 `<TARGET>` 的目录名必须等于 `name`。

同时扫描移动后可能失效的引用：`../`、仓库根绝对路径、脚本按当前目录而非 `__file__` 计算资源。发现后先停下询问，不要用编辑内容来“顺手修复”。

## 1. 分类

| 情况 | 条件 | 动作 |
|---|---|---|
| A | 目标不存在；`name` 有效；根文件都属于该包 | 进入第 2 节迁移 |
| B | 目标存在；根与目标的 `SKILL.md` 及每个 references/scripts 文件 blob 相同 | 只读报告，等待确认；确认后才删除根副本 |
| C | 目标存在但任一对应文件 blob 不同 | 停止，出示差异，交用户决定 |
| D | 根 `SKILL.md` 被有意作为 GitHub 首页展示 | 转 `skill-repo-readme-placement`；迁走后根不再渲染该 Skill |

比较 B 时逐文件比较 blob OID，不要比较修改时间或文本肉眼结果：

```bash
git ls-tree HEAD -- SKILL.md
git ls-tree HEAD -- "$TARGET/SKILL.md"
git ls-tree HEAD -- references
git ls-tree HEAD -- "$TARGET/references"
```

不要用 `git show origin/main:path` 或 `git diff ref:path` 在 Git Bash/MSYS 下比较；冒号可能被改写成 `ref\path;...`。用 `git ls-tree` 取 OID，再用 `git cat-file blob <oid>` 读取内容。

## 2. 迁移（仅情况 A）

先记录迁移前的文件与 OID：

```bash
git ls-tree -r HEAD -- SKILL.md references scripts assets > "$HOME/.qoder/tmp/before-tree.txt"
```

逐文件移动，不移动整个目录，也不改动内容：

```bash
[ -d references ] && mkdir -p "$TARGET/references"
[ -d scripts ] && mkdir -p "$TARGET/scripts"
[ -d assets ] && mkdir -p "$TARGET/assets"
git mv -- SKILL.md "$TARGET/SKILL.md"
git ls-tree -r --name-only -z HEAD -- references scripts assets > "$HOME/.qoder/tmp/move-list.z"
while IFS= read -r -d '' f; do
  mkdir -p "$TARGET/$(dirname "$f")"
  git mv -- "$f" "$TARGET/$f" || exit 1
done < "$HOME/.qoder/tmp/move-list.z"
for d in references scripts assets; do
  [ -d "$d" ] && find "$d" -depth -type d -empty -exec rmdir {} + 2>/dev/null
done
```

`git mv` 已经暂存；不要随后执行 `git add`。如果 `git mv` 失败，先检查目标是否已存在、路径是否跨文件系统、是否有未跟踪同名文件。

证明重命名而不是删加：

```bash
git status --short
git diff --cached --stat
git diff --cached --name-status
before=$(git ls-tree -r HEAD -- SKILL.md references scripts assets | awk '{print $3}' | sort)
after=$(git ls-files -s -- "$TARGET" | awk '{print $2}' | sort)
[ "$before" = "$after" ] && echo BLOB_OIDS_UNCHANGED || echo BLOB_OIDS_CHANGED
```

期望：暂存区全部是 `R100`；`git diff --cached --stat` 显示 0 insertions、0 deletions；`BLOB_OIDS_UNCHANGED`。出现 delete/add、非 0 行改动或 OID 变化时停止，检查 `core.autocrlf`、`.gitattributes` 或并发修改；不要用提交掩盖。

## 3. 重复根副本（情况 B）

默认只读报告，不移动、不删除：

```bash
echo "ROOT_AND_TARGET_MAY_BE_IDENTICAL"
git ls-tree HEAD -- SKILL.md
git ls-tree HEAD -- "$TARGET/SKILL.md"
git ls-tree HEAD -- references
git ls-tree HEAD -- "$TARGET/references"
```

逐项确认 OID 全部相同后，报告目标包路径、根路径、相同项、目标包 QA 结果，并等待用户选择。只有用户明确授权删除根副本时才执行：

```bash
git rm -- SKILL.md references/<evidence>.md
[ -d references ] && find references -depth -type d -empty -exec rmdir {} + 2>/dev/null
git diff --cached --name-status
git commit -m "docs(skill): retirer le doublon racine de $NAME"
```

删除后复跑目标包 QA 和 manifest；目标包的内容不应因删除根副本而变化。若目标包 QA 原本就不通过，不要用删除根副本冒充修复。

## 4. 目标已存在但不同（情况 C）与展示（情况 D）

- C：出示根与目标的 OID、文件清单和差异摘要，停止。不要 `git mv`、不要覆盖、不要替用户选择保留哪一版。
- D：根 `SKILL.md` 若被有意作为 GitHub 首页展示，迁移会让仓库首页不再渲染该 Skill。按 `skill-repo-readme-placement` 让用户在“保留展示并接受根 QA FAIL”和“迁入包并失去根渲染”之间确认。

## 5. 验收

对迁移包运行静态校验与 manifest：

```bash
LOG="$HOME/.qoder/tmp/qa-$NAME-moved.log"
PYTHONIOENCODING=utf-8 py -3 -B "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$TARGET" --workspace "$PWD" --stable-seconds 2 > "$LOG" 2>&1
echo "QA_RC=$?"
grep -E '^Files \(|^Summary:|^RESULT |WARN|FAIL' "$LOG"
PYTHONIOENCODING=utf-8 py -3 -B "C:/Users/Administrateur/.qoder/skills/skill-package-integrity-audit/scripts/check_package_manifest.py" "$TARGET" --qa-log "$LOG"
echo "MANIFEST_RC=$?"
```

期望：`RESULT PASS`；`Files (N)` 等于包内实际文件数；manifest `Unexpected 0` 且 RC 0。然后复跑其余嵌套包：

```bash
for p in .qoder/skills/*; do
  [ "$p" = "$TARGET" ] && continue
  log="$HOME/.qoder/tmp/qa-$(basename "$p")-after-move.log"
  PYTHONIOENCODING=utf-8 py -3 -B "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$p" --workspace "$PWD" --stable-seconds 2 > "$log" 2>&1
  echo "$(basename "$p") rc=$? | $(grep -E '^Files \(|^Summary:|^RESULT ' "$log" | tr '\n' ' ')"
done
```

检查根目录：

```bash
test -f SKILL.md && echo ROOT_SKILL_PRESENT || echo ROOT_HAS_NO_SKILL
test -d references && echo ROOT_REFERENCES_PRESENT || echo ROOT_HAS_NO_REFERENCES
```

根 `.gitattributes` 是 LF 策略文件，不是 Skill 包文件；不要移动它。迁移完成后不要再把仓库根当作 Skill 包跑 QA 并期待 PASS；根不再是包，验收对象是 `.qoder/skills/<name>/`。

## 6. 提交

提交前确认暂存区只有预期改动：

```bash
git diff --cached --name-status
git status --short
git commit -m "docs(skill): archiver $NAME"
git show --stat --oneline HEAD
git status --short
git ls-files --eol -- "$TARGET"
```

期望：只包含迁移路径；`git show --stat` 仍显示 100% rename、0 行增删；工作区干净；迁移文件行尾与仓库策略一致。若有其他暂存文件，停止；若显示 `nothing to commit`，核对 `git rev-parse HEAD origin/main` 和 `git log -1`，报告已完成，不要制造空提交，也不要改写已推送历史。

## 7. 推送与远端验证（仅授权时）

```bash
git fetch origin main
git rev-parse HEAD origin/main
git log --oneline HEAD..origin/main
```

若 `origin/main` 已前进，优先 `git rebase origin/main`；冲突或不允许 rebase 时停止。不要强推。推送后验证 ref、远端树和旧根路径：

```bash
git push origin main
git ls-remote origin refs/heads/main
git rev-parse HEAD
git ls-tree -r --name-only origin/main
out=$(git ls-tree origin/main -- SKILL.md references)
[ -z "$out" ] && echo ROOT_CLEAN || echo ROOT_LEFTOVER
git ls-tree -r origin/main -- "$TARGET"
```

`git ls-tree` 在路径不存在时 RC 仍为 0；必须用输出是否为空判断 `ROOT_CLEAN`。远端迁移文件的 blob OID 应与本地 `HEAD` 相同。推送期间远端再次前进时，重复 fetch、rebase、push 和验证；不要用 `--force`。

## 陷阱表

| 现象 | 原因 | 处理 |
|---|---|---|
| 根 QA `name` 与目录不匹配、大量 layout WARN | 根目录被当作 Skill 包，嵌套包被当作 unexpected | 验收对象改为 `.qoder/skills/<name>/`；不要据此判定嵌套包失败 |
| 用户说包是 X，根 frontmatter 是 Y | 用户记忆或旧报告与当前根文件不一致 | 以实际 frontmatter `name` 为准；来源会话中 `verify` 与 `audit` 就曾混淆 |
| 目标已存在，根与目标逐 blob 相同 | 根旧副本被合并恢复，或另一会话重新归档 | 默认只读报告并等待确认；删除根副本需显式授权 |
| 目标已存在但内容不同 | 两版分叉或并发写入 | 停止；出示 OID，不覆盖、不合并 |
| `git ls-tree -r -s` 报 `unknown switch 's'` | Git 版本不支持该短选项 | 用 `git ls-tree -r` 或 `git ls-tree -r -l` |
| `git ls-tree origin/main -- path` 输出空但 RC 0 | 路径不存在时 Git 仍成功 | 判断输出是否为空，不要判断退出码 |
| `git show ref:path` 报 `ambiguous argument 'ref\path;...'` | Git Bash/MSYS 改写冒号 | 用 `git ls-tree` 取 OID，再 `git cat-file blob <oid>` |
| 中文内容经管道交给 `py -3 -c` 报 cp1252 `UnicodeEncodeError` | Python 标准输出编码不是 UTF-8 | 设置 `PYTHONIOENCODING=utf-8`，或避免该管道 |
| `git mv` 后 diff 显示 delete/add 或非 0 行 | 内容或行尾被改变 | 停止；检查 `core.autocrlf`、`.gitattributes` 和并发修改 |
| 根 `.gitattributes` 被判 layout WARN | 它不是包文件 | 保留；不要为了消除 WARN 而移动或删除 |
| 推送被拒，远端 main 已前进 | 另一会话在期间推送 | fetch、rebase、重新验证后再推；不强推 |
| 已推送后用户再次要求 commit/push | 工作区已干净，没有待提交内容 | 核对 `HEAD == origin/main` 后报告；不建空提交、不改写历史 |
| 根文件在迁移后又出现 | 旧布局分支被合并，或另一会话恢复 | 重新执行预检和分类；不要假设根仍然干净 |
| `rmdir` 报目录非空 | 还有未移动文件 | 停止并列出文件；不要 `rm -rf` |

## 报告模板

```text
Repo / HEAD:
Root package:
Target:
Decision: MIGRATE / DUPLICATE-REPORT / STOP
Changes: <N> renames, 0 insertions, 0 deletions
Blob OIDs: before=<...> after=<...>
QA: Files (<N>), <X> pass / <Y> fail / <Z> warn, RESULT
Manifest: Unexpected <N>, RESULT
Other packages: <name rc / Files / Summary / RESULT>...
Commit:
Push: done / not authorized
Remote: origin/main=<oid>; root SKILL.md/references=absent/present
Worktree:
Unverified:
```

## 已验证案例（2026-10-26）

- 来源会话 `52ce9bcb-d076-4b0f-9cb8-ef3e35d75113`：根包 `audit-skill-during-live-creation` 用 2 个 `git mv` 迁入 `.qoder/skills/audit-skill-during-live-creation/`；提交 `3a9f519` 为 100% rename、0 行增删；blob OID `39909164…`、`de310c4d…` 前后不变。
- 迁移包 QA `Files (2)`、9 pass / 0 fail / 0 warn、`RESULT PASS`；manifest `Unexpected 0`、`RESULT PASS`；其余三个包复跑 QA 全部 PASS。
- 当时远端 `origin/main` 为 `3a9f519`，远端根已无 `SKILL.md` 和 references 目录。
- 2026-10-26 补充观察：远端 `origin/main=d4d8658` 的根 `SKILL.md` 与已存在的嵌套包 `SKILL.md` 逐 blob 相同（`6470a525…`），根 references 目录下的对应文件也与嵌套副本相同（`f319a3ea…`）；根 QA 在临时 archive 上为 9 pass / 1 fail / 12 warn。这是情况 B，默认只读报告，不自动删除。
- 2026-10-26 本地一次性夹具（裸 origin 加临时克隆）验证：目标不存在时得到 `R100`、0 行增删、OID 不变、QA/manifest PASS；目标存在且 blob 相同时识别为 B；根副本改动后识别为 C；`git ls-tree -r -s` 返回 129；空路径返回 RC 0 且输出为空。夹具已删除。
- 未验证：根包含 scripts 或 assets 目录的迁移；非 LF 仓库；非 GitHub 远端；当前 `d4d8658` 上全部 5 个包的 QA（只验证了根 QA 与本地 `3a9f519` 的 4 个包）。

完整命令、输出与边界见 `references/preuves-migration-2026-10-26.md`。

## 资源

- `references/preuves-migration-2026-10-26.md`：来源会话逐字证据、当前重复根观察、失败与纠正记录。
- `skill-file-qa`：静态校验器，脚本位于其包的 scripts 目录（validate_skill.py）。
- `skill-package-integrity-audit`：包清单与缓存审计，脚本位于其包的 scripts 目录（check_package_manifest.py）。
