---
name: qualify-dependency-behavior-provenance
description: "在把依赖脚本（另一 Skill 的审计/校验脚本、外部 CLI 或生成器）的实测行为写进 SKILL.md 或 references 前，先判定该行为来自已提交的 HEAD 还是仅本机工作区未提交改动：记录实际执行路径、仓库根、HEAD 与 git status，用 git diff、git show HEAD:<script> 与 git blame 的 Not Committed Yet 标记定位产生该行为的代码，必要时在隔离副本执行 HEAD 版本；把结论分为 COMMITTED、WORKTREE_ONLY、UNKNOWN，并按「HEAD 行为」与「本机工作区行为」写成版本限定双分支，保留日期、提交号、命令、输出与退出码，历史证据只追加不改写，最后重跑 skill-file-qa 与包清单审计。用于推荐数据声称「当前脚本接受/输出 X」但可能只是本地临时改动、文档实测结果在另一台机器复现不了、依赖脚本哈希未变而行为变化、需要把观测写成稳定契约或版本限定说明时；不替代依赖哈希变化后的完整契约复审计、工具契约审计或证据新鲜度检查。中文触发：依赖行为来源、HEAD 还是工作区、未提交改动、Not Committed Yet、版本限定、双分支、契约漂移、本机能过别处不行；English: dependency behavior provenance, HEAD vs working tree, uncommitted change, version-qualified documentation; Français: provenance du comportement d'une dépendance, HEAD ou copie de travail, modification non validée."
---

# 依赖行为来源判别

## 交付范围（2026-10-26）

本版本只交付本 SKILL.md 与 `references/preuves-session-provenance.md`。所有取证使用 `git`、`py -3` 与内联命令，不随附脚本；目录中若出现未在本文件登记的脚本，视为范围外文件，不是本 Skill 的已验证组成部分。

## 目标

在把某个依赖脚本的实测行为当作契约写进文档之前，先回答一个问题：这个行为来自该仓库已提交的 HEAD，还是只来自本机工作区里尚未提交的改动？只有前者能作为其他机器可复现的契约；后者只能写成日期与提交号限定的本机观察。

## 适用与不适用

适用：

- 推荐数据或上一轮结论声称「当前脚本接受 / 输出 / 退出 0」，准备据此修改文档。
- 文档已有实测结果，但换机器、换克隆或换归档后复现不了。
- 依赖脚本文件哈希未变，行为却变了（差异可能来自工作区、索引或另一份副本）。
- 需要把版本差异写成双分支，而不是删掉旧记录来让文档「一致」。

不适用：

- 依赖脚本哈希变化后需要复跑完整 CLI 契约：用 `dependency-script-contract-reaudit`。
- 首次审计脚本是否存在、参数与退出码契约：用 `audit-skill-tool-contracts`。
- 只核对证据文件里的计数或「实测」标注来源：用 `audit-evidence-count-provenance`。
- 仅检查证据文件是否过期：用 `verifier-fraicheur-preuves-skill`。

## 不可协商约束

1. 只读取证。不修改依赖脚本、不修改其白名单或测试夹具；那属于另一个 Skill，需要单独授权。
2. 不用 `git stash`、`git checkout`、`git reset`、`git clean` 或临时提交来让比较「变干净」。工作区脏本身就是证据。
3. 不把本机工作区版本的行为写成「当前脚本」「稳定契约」或跨机器承诺。
4. 必须记录实际执行的脚本路径与退出码。`RESULT` 行不能替代退出码，管道的退出码不能替代脚本退出码。
5. 非 Git 仓库、无 HEAD、脚本是副本或归档时，结论标 `UNKNOWN` 并说明，不得猜测。
6. 历史证据只追加带日期的观察，不改写旧记录原文。
7. 不提交、不推送、不新建 remote；本 Skill 只读。

## 工作流

### Step 0 定位实际执行的脚本

先确认命令真正执行的是哪个文件，而不是「应该是哪个」。

```bash
SCRIPT="<absolute script path used in the command>"
ls -l "$SCRIPT"
sha256sum "$SCRIPT"
git -C "$(dirname "$SCRIPT")" rev-parse --show-toplevel 2>&1
```

- 从另一份文档、归档或旧会话抄来的路径，必须重新确认；同名副本是假来源的常见原因。
- 记录解释器（本机用 `py -3`）与命令行参数。
- 目录不在任何仓库时，跳到 Step 2 的 `UNKNOWN` 分支，仍可记录本机行为，但不得写成契约。

### Step 1 记录脚本与仓库身份

```bash
REPO="<repo root from Step 0>"
REL="<script path relative to REPO>"
git -C "$REPO" log -1 --oneline -- "$REL"
git -C "$REPO" status --short -- "$REL"
git -C "$REPO" ls-files -s -- "$REL"
git -C "$REPO" rev-parse HEAD:"$REL" 2>/dev/null || echo "TRACKED_AT_HEAD=no"
git -C "$REPO" show HEAD:"$REL" | sha256sum
sha256sum "$SCRIPT"
# 内容一致性（过滤后，等价于 git add 会存入的 blob）
git -C "$REPO" hash-object --path="$REL" "$SCRIPT"
git -C "$REPO" rev-parse HEAD:"$REL"
git -C "$REPO" diff --quiet -- "$REL"; echo "DIFF_RC=$?"
git -C "$REPO" diff --cached --quiet -- "$REL"; echo "CACHED_RC=$?"
```

- `status --short` 首列 ` M` 是未暂存改动，`M ` 是已暂存未提交，`MM` 两者都有，`??` 未跟踪。这些都不等于 HEAD。
- `git hash-object --path="$REL"` 与 `git rev-parse HEAD:"$REL"` 相等表示**内容**一致（过滤后）；`sha256sum` 相等表示**字节**一致。`core.autocrlf=true` 下干净的 CRLF 检出可以满足前者而不满足后者，不得据此判 `WORKTREE_ONLY`。
- `DIFF_RC=0`、`CACHED_RC=0` 且 `status` 为空，表示工作区与索引都没有相对 HEAD 的内容改动；仍要用 Step 2 确认行为来自这段代码。
- `TRACKED_AT_HEAD=no` 表示文件在该提交中不存在；不要把它当作 HEAD 版本。

### Step 2 定位产生该行为的代码

```bash
git -C "$REPO" diff -- "$REL"
git -C "$REPO" diff --cached -- "$REL"
git -C "$REPO" show HEAD:"$REL" | grep -n "<constant or branch>"
grep -n "<constant or branch>" "$SCRIPT"
git -C "$REPO" blame -L <start>,<end> -- "$REL"
```

- 比较产生行为的常量、白名单、条件分支或默认值，不要只比较文件整体。
- `git blame` 出现 `00000000 (Not Committed Yet ...)` 即证明该行未提交。
- `core.autocrlf` 的 LF/CRLF 警告本身与来源无关，可忽略；但 checkout/archive 会改变工作字节，`sha256sum` 的差异不等于未提交改动，按 Step 1 的 `hash-object --path` 与 `git diff` 判断内容。
- 分类：

| 证据 | 结论 |
|---|---|
| `status` 为空，`DIFF_RC=0`、`CACHED_RC=0`，`hash-object --path` 等于 HEAD blob，实测由该文件产生 | `COMMITTED` |
| `status` 非空，或 `DIFF_RC`/`CACHED_RC` 非 0，或 `blame` 显示 `Not Committed Yet`，或 HEAD 内容缺少产生该行为的分支 | `WORKTREE_ONLY` |
| 不在仓库、无 HEAD、执行路径无法确认 | `UNKNOWN` |

- 先看内容、再看字节：干净检出的 `sha256sum` 可能因 CRLF 与 blob 不同；只有 `hash-object --path` 与 `git diff` 能判定内容是否来自 HEAD。

### Step 3 需要时执行 HEAD 版本

源码差异已经证明 HEAD 缺少该分支时，可只记为「源码推断」，不必执行。需要执行时，把 HEAD 内容解到隔离临时目录，绝不切换工作区。默认按 blob 字节解出，不用 `git archive`：

```bash
TMP="<temp>/dep-head"
rm -rf "$TMP"
mkdir -p "$(dirname "$TMP/$REL")"
git -C "$REPO" show HEAD:"$REL" > "$TMP/$REL"
want=$(git -C "$REPO" show HEAD:"$REL" | sha256sum | cut -d' ' -f1)
got=$(sha256sum "$TMP/$REL" | cut -d' ' -f1)
if [ "$want" = "$got" ]; then
  echo "HEAD_BYTES=ok"
  py -3 "$TMP/$REL" <args> > "$TMP/run.log" 2>&1
  rc=$?
  echo "HEAD_EXIT=$rc"
else
  echo "HEAD_BYTES=DRIFT"
fi
chmod -R u+w "$TMP" && rm -rf "$TMP"
test -e "$TMP" && echo "STILL_EXISTS" || echo "REMOVED"
```

- `git show HEAD:<rel>` 输出 blob 原始字节；`git archive HEAD | tar -x` 在 `core.autocrlf=true` 下会把 LF 转成 CRLF。本机实测同一脚本：blob 681 B、`018c1de1…`；归档 703 B、CR=22、`42bfd9f1…`。两者哈希不同，归档副本不能当作 HEAD 字节证据。
- 需要整棵树（多文件脚本）才用 `git archive`，并在执行前做同一 `sha256sum` 断言；不通过时停止，不要把该次运行当 HEAD 证据。需要让归档/克隆稳定复现字节时，在**被归档的提交**里加夹具根 `.gitattributes`（`* text=auto eol=lf`）后重试；工作区里有但未提交的 `.gitattributes` 不生效。
- `git hash-object <file>` 默认会按 `core.autocrlf` 归一化 CRLF，不能当字节断言；字节断言用 `sha256sum` 或 `git hash-object --no-filters`。
- 只适用于自包含脚本；缺少同目录模块或数据文件时，记录失败原因，回退到源码推断。`git show` 不保留可执行位，统一用 `py -3` 运行。
- 临时目录只清理本次创建的那一个；不要对源仓库执行 `chmod`。

### Step 4 实跑工作区版本并记录退出码

```bash
OUT="<temp>/dep-run.log"
py -3 "$SCRIPT" <args> > "$OUT" 2>&1
rc=$?
echo "DEP_EXIT=$rc"
grep -E "^(RESULT|Summary:)|Unexpected|UNEXPECTED|Files \(" "$OUT"
```

- 先取 `rc=$?`，再过滤输出；把输出管道给 `tail` 或 `grep` 后拿到的是过滤器的退出码。
- 逐字保存关键行，不要只保存自己的总结。

### Step 5 写成版本限定双分支

```markdown
依赖脚本：<absolute path> | HEAD：<hash> <subject> | 观察日期：<YYYY-MM-DD> <tz>

- 已提交 HEAD <hash>：<behavior A>（证据：git show HEAD:<rel> 第 N 行缺少/包含 <token>）
- 本机工作区（未提交改动：<diff stat 或摘要>）：<behavior B>（证据：<command> → <RESULT>，DEP_EXIT=<n>）
- 其他机器按 HEAD 复现；不要把本机结果写成当前脚本的固定契约。
```

- 两个分支都要有命令、关键输出、退出码与日期。
- 无法确认的一侧写 `UNKNOWN`，不要删除或省略。
- 没有提交号与日期的「当前脚本」表述一律视为不合格。

### Step 6 追加证据并验收

- 在 references 追加 `## 后续观察：<主题>（YYYY-MM-DD）`，保留旧记录原文。分类与 `§N` 写法见 `verifier-fraicheur-preuves-skill`；「已核实 / 推断 / 未验证」标注见 `write-skill-evidence-case-study`。
- 登记来源会话、执行时间与时区（消息用 UTC，工具输出用本地偏移）。
- 重跑两项审计并分别记录哈希：

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<skill-dir>" \
  --workspace "<workspace-root>" --stable-seconds 2
py -3 "$HOME/.qoder/skills/skill-package-integrity-audit/scripts/check_package_manifest.py" \
  "<skill-dir>" --qa-log "<qa log>"
sha256sum "<skill-dir>/SKILL.md" "<skill-dir>/references/<evidence>.md"
```

- 校验器指纹只覆盖 SKILL.md，references 必须单独记录哈希。
- QA 或 manifest 的 WARN/UNEXPECTED 按实际输出报告，不要为了让结果好看而改动依赖脚本。

### Step 7（可选）把样例夹具落盘，便于逐字复跑

需要把本次测试交给下一个代理、或用户要求提交夹具时才做。不要在样例仓库内部提交（会抹掉 `WORKTREE_ONLY` 的 ` M` 状态）；在夹具根提交，并保留内层仓库原样。

```bash
FX="<fixture root>"
# 1) 嵌套仓库的文件不能用 git add -f 暂存；写入 blob 后直接更新外层索引
BLOB=$(git -C "$FX" hash-object -w repo/dep.py)
git -C "$FX" update-index --add --cacheinfo 100644,"$BLOB",repo/dep.py
# 2) 保存内层 HEAD，供 HEAD 侧复跑
git -C "$FX/repo" bundle create "$FX/repo.bundle" HEAD
# 3) 锁定夹具根的行尾（已有 .gitattributes 时追加，不覆盖其他规则）
grep -qxF '* text=auto eol=lf' "$FX/.gitattributes" 2>/dev/null \
  || printf '* text=auto eol=lf\n' >> "$FX/.gitattributes"
git -C "$FX" add .gitattributes repo.bundle
git -C "$FX" commit -m "test: capture provenance fixture"
```

- `git add -f repo/dep.py` 返回 0 但什么都不暂存（`status` 仍为 `?? repo/`）；`git add -f repo` 只暂存 `160000` gitlink，克隆不含内容。若误加了 gitlink，用 `git rm --cached -f repo` 撤销（只改外层索引，内层仓库不受影响），再重试上面的 `hash-object`/`update-index`。
- 外层仓库提交的是**工作区内容**（`$FX/repo/dep.py` 通过 `cacheinfo` 进入索引），内层 HEAD 的旧内容只保留在 `$FX/repo.bundle`。因此快照侧从外层夹具取，HEAD 侧必须从 bundle 克隆取，不能用外层 `repo/` 冒充 HEAD。
- `.gitattributes` 必须进入被克隆/归档的提交；`* text=auto eol=lf` 用来阻止外层 checkout/archive 把证据字节改成 CRLF。
- 用新克隆验收，双侧都要复跑：

```bash
git clone "$FX" "<verify-dir>"
sha256sum "<verify-dir>/repo/dep.py" "$FX/repo/dep.py"      # 必须一致
py -3 "<verify-dir>/repo/dep.py" "<target>" ; echo "SNAPSHOT_EXIT=$?"   # 期望 PASS/0
git clone "<verify-dir>/repo.bundle" "<head-dir>"
py -3 "<head-dir>/dep.py" "<target>" ; echo "HEAD_EXIT=$?"              # 期望 FAIL/1
chmod -R u+w "<verify-dir>" "<head-dir>" && rm -rf "<verify-dir>" "<head-dir>"
test ! -e "<verify-dir>" && test ! -e "<head-dir>" && echo "REMOVED" || echo "STILL_EXISTS"
```

- 克隆后的外层 `repo/` 不再是嵌套仓库，只用于复跑快照行为；来源判定要在原始夹具里做。
- `UNKNOWN` 侧要把脚本复制到夹具根之外的空目录再跑 `rev-parse`；夹具提交后，夹具内的 `loose/` 已属于外层仓库，不再产生 `128`。
- bundle HEAD 的**检出**字节可能因 `core.autocrlf` 漂移（实测内层 663 B → 685 B、CR=22）；HEAD 侧以行为/退出码为验收，字节断言用 `git show HEAD:`。
- 不新建 remote、不推送；只清理本次创建的两个克隆目录。

## 报告模板

```text
Script      : <abs path> | sha256=<worktree bytes> | blob=<HEAD blob OID>
Repo        : <root> | HEAD: <hash> <subject> | status: <short>
Provenance  : COMMITTED | WORKTREE_ONLY | UNKNOWN
Evidence    : HEAD <rel> <token>=<present/absent> | blame=<line or Not Committed Yet>
Run         : <command> | DEP_EXIT=<n> | <key output line>
Docs        : dual-branch written | dated observation appended | history unchanged
Validation  : QA <PASS/FAIL> <p/f/w> Files (<N>) | manifest <PASS/FAIL> Unexpected <n> exit=<n>
Hashes      : SKILL.md <sha256> | evidence <sha256>
VCS         : none (read-only)
```

## 陷阱

| 现象 | 原因 | 处理 |
|---|---|---|
| 本机 PASS，另一台机器 FAIL | 实测用的是工作区未提交改动 | 按 Step 1–2 定性，文档写双分支 |
| `git diff` 为空但行为不同 | 执行的是另一份副本、归档或缓存的 `__pycache__` | `ls -l` 与 `sha256sum` 确认实际路径；只在确认归属后清缓存 |
| `git blame` 显示 `00000000 (Not Committed Yet)` | 该行未提交 | 判 `WORKTREE_ONLY`，不得写成契约 |
| `status --short` 显示 `M ` | 改动已暂存但未提交 | 仍不等于 HEAD；用 `git show HEAD:` 比较 |
| 脚本不在任何仓库 | 外部安装或复制件 | 标 `UNKNOWN`，报告无提交来源 |
| 用 `git stash` 得到「干净」比较 | stash 改变工作区状态，可能影响其他工作 | 禁止；只读比较 |
| 先 `py -3 script.py > log` 再取 `rc=$?` 却得到 0 | 若把输出管道给 `tail`，拿到的是 `tail` 的退出码 | 先记录脚本退出码，再过滤输出 |
| 文档只剩「现在 PASS」 | 覆盖或删除了旧 FAIL 记录 | 保留原文，追加带日期观察 |
| 为让根 `.gitattributes` 通过而改白名单 | 修改了依赖 Skill | 本 Skill 只报告；改动需要独立授权，见 `lock-lf-endings-skill-repo` |
| `git archive` 解出的副本与 `git show` 哈希不同，大小正好多出行数个字节 | `core.autocrlf=true` 把 LF 转 CRLF | 用 `git show HEAD:<rel>` 取字节；必须归档时先做 `sha256sum` 断言，并在被归档的提交里加夹具根 `.gitattributes`（`* text=auto eol=lf`） |
| `git hash-object <file>` 与 `git show HEAD:` 一致，但 `sha256sum` 不同 | `hash-object` 默认按 `core.autocrlf` 归一化 CRLF | 字节断言用 `sha256sum` 或 `git hash-object --no-filters`；内容断言才用默认 `hash-object --path` |
| `git add -f <nested>/<file>` 返回 0，`status` 仍是 `?? <nested>/` | Git 不进入嵌套仓库；加目录只会得到 `160000` gitlink | 用 `git hash-object -w` + `git update-index --add --cacheinfo 100644,<blob>,<path>`；误加 gitlink 用 `git rm --cached -f <nested>` 撤销 |

## 完成检查

- [ ] 已确认真实执行路径，排除了副本与缓存。
- [ ] 已记录仓库根、HEAD、`status`、tracked blob 与工作区内容哈希。
- [ ] 已用 `git diff`、`git show HEAD:` 与 `git blame` 定位产生该行为的代码。
- [ ] 结论为 `COMMITTED`、`WORKTREE_ONLY` 或 `UNKNOWN` 之一，并有逐字证据。
- [ ] 实测命令、关键输出与退出码均已记录，退出码未经过过滤器管道。
- [ ] Step 3 的 HEAD 副本已用 `sha256sum` 与 `git show HEAD:` 断言字节一致；不一致时没有执行或引用该副本。
- [ ] 文档为版本限定双分支，含日期、提交号与「不得外推」说明。
- [ ] references 只追加带日期观察，历史原文未改。
- [ ] 已重跑 QA 与包清单审计并如实报告，两文件分别记录 SHA-256。
- [ ] 未修改依赖脚本，未 stash/reset/checkout，未提交或推送。
- [ ] 若落盘夹具：外层新克隆哈希与工作区一致，快照 `PASS`/0 与 bundle HEAD `FAIL`/1 均已复跑，且未推送。

## 资源

- `references/preuves-session-provenance.md`：来源会话、逐字审计输出、未提交改动的 `git diff` 与 `blame`、HEAD 缺失常量、2026-10-26 当前状态复核、2026-10-26 独立复核（会话 `8bf351ff-0bfa-46f6-aeb5-eb8873808d0d`：并发写入、最终 QA/manifest 与哈希）、2026-10-26 Step 3 归档字节漂移与夹具落盘（会话 `3532d974-8dd9-4fde-9195-03abf7aa4333`：`git show` vs `archive`、嵌套仓库暂存、bundle 与新克隆复跑）、限制与未验证项。
- 依赖：`skill-file-qa` 提供 `C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py`；`skill-package-integrity-audit` 提供 `C:/Users/Administrateur/.qoder/skills/skill-package-integrity-audit/scripts/check_package_manifest.py`。
- 相邻 Skills：`dependency-script-contract-reaudit`（哈希变化后的完整契约复审计）、`audit-skill-tool-contracts`（脚本存在性与参数契约）、`audit-evidence-count-provenance`（计数来源）、`verifier-fraicheur-preuves-skill`（`§N` 追加与 CONFIRME/PERIME）、`write-skill-evidence-case-study`（已核实/推断/未验证）、`lock-lf-endings-skill-repo`（本案例的消费者）。
