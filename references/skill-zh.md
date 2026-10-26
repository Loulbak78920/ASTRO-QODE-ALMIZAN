# 提交 Skill 或嵌套仓库的改动

## 目标

定位真正包含被修改文件的仓库，只提交预期范围，且在没有明确要求时绝不推送。项目根目录不一定是仓库：有用的仓库通常是嵌套的，或每个 Skill 各自一个仓库。

## 触发条件

- 提出「commit」「git commit」「把这个 Skill 版本化」；
- 用户级 skills 目录下的 Skill 不在任何仓库中；
- 存在多个嵌套仓库且范围不明确；
- 测试在提交后重写了生成文件；
- 要求 push、在无共同祖先时「合并到 `main`」，或 Skill 仓库没有 `origin`；
- 核对 blob/源文件 OID，或出现 `core.autocrlf` 警告；
- `SKILL.md`、脚本或译本在验证后才被写入，需要重新验收；
- `skill-file-qa` 返回 `RESULT PASS`，但 `Files (N)` 中含缓存；
- 提交后其他仓库中存在该 Skill 的归档；
- 预期有提交但 `git status` 为空（提交已由另一会话创建）；
- 验证与 `git add` 之间发生并发写入，或指纹清单不一致；
- 持续并发写入（验证期间源文件仍每 10–30 秒变化），已批准的方案自规划后大小/mtime/SHA-256/行数已变化，或已批准的方案已被另一会话部分实现；
- 为不在任何仓库中的 Skill 初始化仓库（LOCAL-ONLY，或共享远程 + 专用分支）、根提交，或流程中途范围前提变化；
- 只更新源文件、译本保持不变（预期对等失败）。

## 步骤 1 — 定位真实仓库

始终使用带引号的绝对路径：

```bash
git -C "<chemin absolu>" rev-parse --show-toplevel
```

- 返回 `EXIT=128` 并提示 `fatal: not a git repository`：该目录不是仓库。不要因此推断项目根是仓库。
- 相对路径或非 ASCII 路径可能从另一个当前目录解析。先用 `test -d "<chemin>"` 确认存在，再传绝对路径。已观察案例：`ASTRO-Q°ODE_SYSTEME` 失败并提示 `fatal: cannot change to ...`。
- 根目录不是仓库时枚举候选：

```bash
find "<racine>" -maxdepth 3 -name .git -type d
find "C:/Users/Administrateur/.qoder/skills" -maxdepth 2 -name .git -type d
```

- 只读清点，ASCII 输出，退出码 0/1/2：

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/inspect_git_state.py" "<racine>" "C:/Users/Administrateur/.qoder/skills"
```

该脚本调用 `rev-parse`、`status`、`diff`、`log` 和 `remote`，不修改索引，并标出未跟踪的缓存目录。脚本属于 `commit-skill-work`，不属于被提交的 Skill：`<dossier-skill>` 可能只有 `SKILL.md`。路径必须保持绝对并指向本 Skill；从项目根执行 `scripts/inspect_git_state.py` 会因 `can't open file` 失败（退出码 2）。

## 步骤 2 — 分类改动

```bash
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --stat
git -C "<depot>" log --oneline -5
git -C "<depot>" ls-files --error-unmatch -- "<chemin>"
```

把每个路径归入三类：**SESSION**（本次工作产生）、**PREEXISTANT**（会话前已修改）、**INCERTAIN**。绝不静默纳入 PREEXISTANT 或 INCERTAIN：先给出准确清单并请求确认。不要纳入 `__pycache__`、`.pyc` 或临时产物。

## 步骤 3 — 选择目标仓库

| 情况 | 动作 |
|---|---|
| Skill 目录不在任何仓库中 | 提出三个互斥目标：(a) **LOCAL-ONLY**（无 origin、不 push）；(b) 已有仓库，或通过 `publier-skill-qoder-vers-depot-git` 归档 `main`；(c) init + 共享远程：读取邻近 Skill 的 `branch -vv`/`remote -v` 与 `git ls-remote`，提出目标，经同意后 `git init`、`git remote add`、push `skill/<nom>`；不要预设 LOCAL-ONLY |
| 目录位于嵌套仓库内 | 使用该仓库，并用 `ls-files --error-unmatch` 确认 |
| 多个仓库都有改动 | 每个仓库、每个主题各自提交 |
| 存在无关的既有改动 | 纳入前先询问 |
| Skill 仓库的 `origin` 是共享仓库 | 推送到专用分支 `skill/<nom>`，未经同意绝不推 `main`；无共同祖先时向 `main` 应用内容按 `references/contenu-vers-main.md` 执行 |
| 仓库没有 `origin` | 询问 URL；不要猜测。提出目标前，用 `git ls-remote --heads <url>` 只读探测候选：仅保留 `RC=0` 且不存在 `refs/heads/skill/<nom>` 的；不可达或已被占用不是可执行选项 |

对「TOUT」的回答：先用互斥选项和确切的仓库、文件清单重述一次。若第二次仍回答「TOUT」，不要再提第三个问题：执行推荐组合，在报告中明确声明，并排除未列出或不可逆的动作（push、删除、重写历史）。仅当 `git init` 本来就在已确认选项中时才可执行。已观察案例（2026-10-26）：连续两次「TOUT」→ Skill 本地仓库 + 在公开仓库本地克隆的 `main` 上提交，不创建重复的专用分支，也不推送。下一条关于无关公开仓库的规则优先：绝不推送到 `main`，绝不把用户级 Skill 提交到无关公开仓库。

仅在明确同意后才执行 `git init`。不要修改 Git 配置：只读取 `git config user.name` 与 `git config user.email`，不要改写。绝不要把用户级 Skill 提交到无关公开仓库的 `main`。执行 `git init` 后，用 `git symbolic-ref --short HEAD` 读取实际指向的分支：在未出生的 HEAD 上，`git rev-parse --abbrev-ref HEAD` 会以 `fatal: ambiguous argument 'HEAD'` 失败；同时记录 `init.defaultBranch` 与邻近仓库的分支，不得静默重命名。根提交的 OID 顺序是固定的：`git add` 之后，`git rev-parse ":<chemin-relatif>"` 必须等于 `git hash-object --path=<chemin-relatif> <source>`；`HEAD:<chemin-relatif>` 只在首次提交后存在。**LOCAL-ONLY** 仓库没有 `origin`：不要询问 URL，也不要 push；这与「已有仓库缺少 `origin` → 询问 URL」是两种不同情况。已观察案例（2026-10-26）：Skill 目录不在任何仓库，初始化 → `INIT_EXIT=0`，`rev-parse --abbrev-ref HEAD` → `fatal: ambiguous argument 'HEAD'`，`symbolic-ref` → `refs/heads/master`；`git init` 后 `skill-file-qa` 仍为 `RESULT PASS`、`Files (2)`；根提交 `4b19c34`（2 个文件），索引与 `HEAD` 的 OID 2/2 MATCH，`autocrlf=true` 时出现 `LF will be replaced by CRLF the next time Git touches it`。已观察案例（2026-10-26）：目录不在仓库，`TOP_RC=128` 且无 `origin`；邻近 Skill 的 `branch -vv`/`remote -v` 与 `git ls-remote` → `Loulbak78920/ASTRO-QODE-ALMIZAN` 的 `skill/commit-skill-work` 与 `skill/mesure-cesium-133-geolocalisee`，`IMAM8MAHDI/qoder-skills` 为归档 `main`；`ls-remote` → `main`、`master`、`skill/commit-skill-work`；提出三个目标后用户选择专用分支；`git init`（`master`，`init.defaultBranch` 未设置）、`remote add`、manifest/QA/调用、根提交 `55e2989`（2 个文件，375 insertions）、把 `HEAD:refs/heads/skill/aligner-variantes-commande-skill` 推送到专用分支、`ls-remote` = HEAD = `55e29897…`、状态干净、`RESULT NONE`（28 个仓库）；随后观察到的上游状态：`master` 跟踪 `origin/skill/aligner-variantes-commande-skill`，但名称不同 —— 这是第 10 步现已禁止的歧义状态。

## 步骤 4 — 提交前验证

### 写入前：重新锚定已批准的方案

已批准的方案描述的是撰写时的文件，不是写入时的文件。判断是否仍在写入的证据是磁盘，不是会话状态：每次写入前重新采样目标，并与方案中记录的基线比较。要求 `size`、`mtime` 与 SHA-256 在至少 3 个间隔样本（≥ 6 秒）上完全一致；若目录仍在变化，改用 4 个样本、≥ 20 秒的窗口。`wait_chat_sessions`/`runtimeState` 只是辅助线索：超时停在 `running` 或助手文本，都不能证明发生过写入或没有写入。已观察（2026-10-26）：两次等待在 revision 95→105 时超时（`running`、`lastAssistantText=null`），而 3 个文件已稳定约 75 秒；反过来，同一回合中的「尚未写入」也可能出现在后续写入之前。磁盘稳定：不要因会话状态而阻塞；磁盘仍在变化：等待稳定窗口或冻结快照。为了在不把只读会话误认为作者的情况下指名写入者，用 `scripts/find_writers.py` 扫描会话 JSONL（`<racine-projets>/<projet>/*.jsonl`）：保留 `input.file_path` 指向 Skill 目录的 `tool_use` `Write`/`Edit`，按会话取最大 `timestamp`；`list_chat_sessions.updatedAt` 与 `runtimeState` 不能标示最后一次写入。归因只说明「谁在写」：是否继续仍由磁盘指纹决定。已观察（2026-10-26）：18:23:15（本地）的一次写入被归给 `49d435d9`，而它在 18:30:41 之前没有任何 `Write`/`Edit`；JSONL 显示 `87644a66` 写到 `17:26:48Z`，但其 `updatedAt` 停在 `17:22:01Z`。

```bash
stat -c '%s %y' "<fichier>"
sha256sum "<fichier>"
```

至少等待 2 秒后重复，要求输出完全相同。若大小、mtime 或 SHA-256 与基线不同，不要照搬方案：重新读取当前文件，按精确文本重新定位每个锚点（绝不用行号），再做最小 `Edit`。上下文压缩后恢复的文件片段、以及方案中引用的行号与摘录，都不等于磁盘现状：先重读当前文件，按精确文本重新锚定每个锚点，并在写入前重新测量 `description` 与正文行数。保留并原样采纳并发新增内容；写入前，依据当前字节而非会话消息，把方案的每个要点归入覆盖矩阵 `CURRENT`（已按原样存在）、`ALREADY_APPLIED`（已由其他字节覆盖）、`PARTIAL`（部分）、`ABSENT`（缺失）、`CONFLICT`（冲突），只编辑 `ABSENT` 与 `PARTIAL`，遇 `CONFLICT` 停止；不要恢复备份，也不要整文件重写。每次并发写入后，对最终字节重跑清单、对等、`skill-file-qa` 与实际调用：不得复用任何先前的 `PASS`。若锚点消失或与并发新增冲突，停止并询问，而非猜测。若此检查期间文件仍在变化，不要写入：等待稳定窗口，或采用「并发写入：验证冻结快照」一节。在旧基线上获得的验证已失效：更新 `SKILL.md` 前先计算正文行数（frontmatter 之后）；若已有 499 行（上限 500），把规则并入现有段落或表格单元格，绝不新增标题、表格行或清单项，再同步译本；同时用脚本（`len`）而非估算测量 frontmatter 的 `description`：新增或改写触发词前须 ≤ 1024 字符；超出时压缩冗余表述、不删除关键触发词，并逐轮重测；随后要求 `skill-file-qa` 显示 `PASS description: single line, N chars`，其中 N 等于最终文件（已观察 2026-10-26：四轮测量 1177 → 1067 → 1030 → 1021，QA `1021 chars`）；重新验证最终字节（若有译本则对等、`skill-file-qa`、SHA-256、实际调用）。已观察（2026-10-26）：合并一个段落并只新增一行表格，使 498 → 499 行，QA 9/0/0，对等 8/8。

已观察案例（2026-10-26）：方案基于 `SKILL.md` `8fc96497…`（28 077 B）与 `skill-zh.md` `1944a214…`；写入时 `SKILL.md` 为 `855b791a…`（28 112 B），`skill-zh.md` 为 `37c02eb5…`；重新读取后对当前文本做 5 次最小 `Edit`，保留并发新增；最终 `SKILL.md` `23d5ac1d…`（30 812 B）。未恢复任何备份，未整文件重写。已观察（2026-10-26）：步骤 10 的方案与 `9fbfe69a` 重叠（目标探测与 `main` 校验已写入，属 `ALREADY_APPLIED`）；只剩移除 `-u` 与通用 post-push 证明为 `ABSENT`；随后 `9944e101` 修改了步骤 11，使 `PASS` 失效，迫使重新 `diff` 并完整重跑，且未丢失两个会话的新增。

使用仓库文档指定的入口运行测试。本项目已观察到的是 `tests.test_suite_complete`（11 项测试）：

```bash
py -3 -m unittest tests.test_suite_complete
```

Skill 改动则对真实目录运行 `skill-file-qa`：

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<dossier-skill>" --workspace "<racine-espace>" --stable-seconds 2
```

提交前必须看到 `RESULT PASS`。记录真实结果。测试失败时不要提交：先修正。

`RESULT PASS` 不能证明包是干净的：验证器可能列出缓存并通过。已观察案例（2026-10-26）：执行 `py_compile` 检查后，`Files (4)` 中包含 `scripts/` 下的一个缓存 `.pyc` 文件，同时显示 `PASS layout: 4 file(s)` 和 `RESULT PASS`。提交前检查 `Files (N)` 行并运行：

```bash
find "<dossier-skill>" \( -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' \) -print
```

若输出非空，只删除本会话创建的缓存（`rm -rf "<dossier-skill>/scripts/__pycache__"`），然后重跑 `skill-file-qa`，并要求 `Files (N)` 与无缓存清单一致：

```bash
find "<dossier-skill>" -type f \( -name "SKILL.md" -o -path "*/scripts/*" -o -path "*/references/*" \) ! -path "*/__pycache__/*" ! -name "*.pyc" ! -name "*.pyo" | sort
```

对预先存在的缓存，先询问再删除。含缓存的 `PASS` 不能作为已暂存包的证明。若保留该缓存，不要为了令 `Files (N)` 与索引一致而删除它：在 Skill 之外、仓库之外冻结**不含缓存**的快照，在快照上运行 `skill-file-qa`（`Files (N)` = 包清单），证明 `instantané == live`，然后只暂存被修改的文件（步骤 4）。已观察案例（2026-10-26）：`scripts/` 下预先存在且未跟踪的 `__pycache__`，包内 3 个文件，修改 2 个；快照上 QA 为 `Files (3)`、`RESULT PASS` 9/0/0、`SNAPSHOT_MATCH`，索引 2/2 且 OID 等于源文件，提交后 `git status` 干净，仅余 `?? scripts/__pycache__/`。

`skill-file-qa` 的 `Fingerprint` 只覆盖 `SKILL.md`。已观察案例：两次修改 `scripts/inspect_git_state.py` 后，它仍为 `9901 bytes` 且 SHA-256 不变；只有修改 `SKILL.md` 后才变为 `9917 bytes`。因此提交前要记录所有资源的指纹：

```bash
find "<dossier-skill>" -type f \( -name "SKILL.md" -o -path "*/scripts/*" -o -path "*/references/*" \) ! -path "*/__pycache__/*" -print0 | xargs -0 sha256sum
```

任何验证之后的写入都会使先前证据失效，包括对 `SKILL.md`、脚本或译本的修正。已观察案例：一次成功调用之后，为让 `find` 结果确定而两次修改 `SKILL.md` 与译本，导致该调用证明的是旧版本；对等、`skill-file-qa`、指纹与实际调用必须对最终版本重跑。不能仅凭 `Fingerprint` 断言整个 Skill 完整。

基准清单必须在最后一次写入后立即保存到 **Skill 目录之外**，并在完成检查后重新比对。它覆盖 `SKILL.md`、`scripts/` 和 `references/`，排除缓存：

```bash
manifest="<chemin-hors-skill>/fingerprints-<nom-skill>.txt"
(
  cd "<dossier-skill>" || exit 2
  find . -type f \( -path './SKILL.md' -o -path './scripts/*' -o -path './references/*' \) \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) > "$manifest"
```

不要把该文件放进 Skill 目录：它会污染包内容；若放在 `references/` 或 `scripts/` 下，还会把自己算进清单。检查完成后重算同一列表，并要求 `diff` 为空：

```bash
(
  cd "<dossier-skill>" || exit 2
  find . -type f \( -path './SKILL.md' -o -path './scripts/*' -o -path './references/*' \) \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) | diff -u "$manifest" - || { echo "FAIL: écriture pendant la validation"; exit 1; }
```

清单中 `./SKILL.md` 的 SHA-256 必须等于 `skill-file-qa` 的 `Fingerprint (final)`；否则 QA 证明的不是当前版本。清单缺失或 `diff` 非空时，不得断言版本已验证。

最后一次写入之后，按以下顺序重跑，之后不得再修改：

1. 若存在译本，先跑翻译对等：

```bash
py -3 "<skills-root>/skill-doc-translation-parity/scripts/check_translation_parity.py" "<dossier-skill>/SKILL.md" "<dossier-skill>/references/<nom>-zh.md"
```

2. 扫描缓存，然后 `skill-file-qa`：必须 `RESULT PASS`，`Files (N)` 等于无缓存清单，且 `Fingerprint (final)` 等于清单中的 `./SKILL.md`。
3. 重算清单并要求 `diff` 为空（见上文）。
4. 实际调用该 Skill（步骤 11），然后重算清单并要求 `diff` 为空。

记录清单与最终指纹，并绑定到被验证版本。若在步骤 4 之后又发生写入，从步骤 1 重来。不得把最后写入之前获得的 PASS 当作当前文件的验证结果。对等检查是结构性的（代码块、表格、标题、清单、标识符、数字），不能证明译文的语义质量。若 `RESULT FAIL` 的唯一失败行是 `FAIL inline tokens: missing=[…]`，且源文件也已被修改，通常表示译本把受保护的标识符改写成了叙述文字（已观察：`$N` 被写成「该字面量」）；这既不是脚本故障，也不是部分范围。不要放宽检查，也不要修改源文件去迁就译本：在译句中恢复逐字相同的 token，然后从步骤 1 重来，依次重跑对等、`skill-file-qa`、Skill 外清单与实际调用。若 `FAIL` 包含 `extra=[…]`，或 `missing` 的差异涉及多处出现（同一 token 在多个章节引用，或译本增删了示例），不要只改一句：按脚本的精确规则（`INLINE_RE`，单行反引号内容、排除代码块、去除首尾空白）统计两个正文的 `Counter`，逐项补齐缺失出现，并改写多余出现所在的句子以恢复原计数（不删信息，也不改源文件），然后重跑对等。已观察：`branch -vv` 5 对 4、`remote -v` 2 对 1、`git ls-remote` 2 对 1、`skill/<nom>` 5 对 6；补三处、去一处后通过。QA 的 `RESULT PASS` 不能抵消该 `FAIL`。

### 部分范围：只改源文件、不改译本

若用户只授权源文件，不要为恢复对等而修改 `references/<nom>-zh.md`，也不要静默翻译。分别运行两项检查并分别报告：

- `skill-file-qa` 可能返回 `RESULT PASS`：它验证包的结构，不验证对等。
- `check_translation_parity.py` 将返回 `RESULT FAIL`；这是部分范围的预期结果，不是脚本故障。

详列实际差异（代码块数量、标题序列、清单项数量、缺失的标识符与数字），并结论：「源文件经 QA 验证，对等失败，包未验证」。绝不要把未经限定的 `RESULT PASS` 当作完整 Skill 的验证。可以为当前字节记录清单与指纹，但标注「仅源文件，对等待定」；实际调用证明的是源文件的运行时解析，不是对等。要消除差异，请先获得把改动同步到译本的授权，再重跑对等与 QA。若流程中途范围前提发生变化（原先排除的文件变为被引用，例如 `SKILL.md` 新增了引用），在 `git add` 前停止并重新确认。硬门禁：`skill-file-qa` 的 `Files (N)` 必须等于无缓存的包清单。完整提交时，该清单等于 `git diff --cached --name-only`；部分提交时，要求 `git diff --cached --name-only` 是该清单的子集，`git diff HEAD --name-only` 精确等于已暂存集合，`git status --porcelain=v1` 不显示包内其他非缓存文件，且每个索引 OID 等于 `git hash-object --path`。绝不要为了令 `Files (N)` 与索引一致而删除预先存在的缓存；应验证不含缓存的快照。

已观察案例（2026-10-26）：只更新源文件后，QA `RESULT PASS`（9/0，`Files (4)`，394 行，30 812 B，`23d5ac1d…`）；对等 `RESULT FAIL`（3 PASS / 5 FAIL：代码块 25 vs 23、多一个 H3、清单 21 vs 20、缺失标识符 `--allow-empty`、`778a547`、`HEAD`、`PASS`、`RESULT PASS`、`SKILL.md`、`c08c9461…` 与数字）；表格与 frontmatter PASS；未宣布包已验证；实际调用后清单 `MANIFEST_MATCH`。

### 并发写入：验证冻结快照

已观察案例（2026-10-26，11:54–12:04）：Skill 目录被其他会话至少改写六次；对等与 QA 两次失效，指纹清单的 `diff` 从未保持为空。对持续变化的目录反复重验不会收敛：应冻结不可变快照，完整验证，再归档这些确切的字节。

1. 等待稳定窗口：每 5 秒对 `SKILL.md` + `scripts/` + `references/` 的整体采样一次 SHA-256，要求连续 4 个样本相同（≥ 20 秒）。单次空 `diff` 不足以证明稳定。

```bash
stable=0; prev=""
while [ "$stable" -lt 3 ]; do
  cur=$(cd "<dossier-skill>" && find ./SKILL.md ./scripts ./references -type f \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum | sha256sum)
  [ "$cur" = "$prev" ] && stable=$((stable + 1)) || stable=0
  prev=$cur; echo "stable=$stable $cur"; sleep 5
done
```

2. 将 `SKILL.md`、`scripts/` 与 `references/`（排除缓存）精确复制到 Skill 之外、仓库之外的新目录：`<tmp>/snapshot-<AAAAMMJJ-HHMM>/<nom-skill>/`。不要复制 `.git` 或临时文件。

```bash
snap="<tmp>/snapshot-<AAAAMMJJ-HHMM>/<nom-skill>"
mkdir -p "$snap/scripts" "$snap/references"
cp "<dossier-skill>/SKILL.md" "$snap/"
cp "<dossier-skill>/scripts/"*.py "$snap/scripts/"
cp "<dossier-skill>/references/"*.md "$snap/references/"
```

3. 复制后立即证明 `instantané == live`：把 live 状态的清单保存在 Skill 目录之外，然后在快照内用相同相对路径计算并要求 `diff` 为空。复制不是原子操作：`diff` 非空时必须重做快照，而不是单独修正某个文件。

```bash
manifest="$(dirname "$snap")/fingerprints-<nom-skill>.txt"
(
  cd "<dossier-skill>" || exit 2
  find ./SKILL.md ./scripts ./references -type f \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) > "$manifest"
(
  cd "$snap" || exit 2
  find ./SKILL.md ./scripts ./references -type f \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) | diff -u "$manifest" - || { echo "FAIL: instantané != live"; exit 1; }
```

4. 在快照上运行整套闸门：用 `$snap` 替代 `<dossier-skill>`，依次跑对等、缓存扫描、`skill-file-qa --stable-seconds 2`。快照上的 QA 证明的是这些字节，不是活动目录。Skill 调用始终解析活动目录：只有 `live == instantané` 时才执行，并立即复比较。

5. 就在 `git add` 之前重跑 live 与清单的 `diff`。若非空，放弃快照并从步骤 1 重来；绝不复用针对其他状态的验证。

6. 归档并索引快照字节：把快照复制到 `.qoder/skills/<nom>`，用显式路径 `git add`，然后用快照文件（而非 live）计算 `git hash-object --path` 的预期 OID。

7. 提交并推送后，用 `C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py` 分别以 `--skill "<instantané>"` 和 `--skill "<dossier-skill>"` 运行；新 ref 必须为 `FRESH`，旧的 `STALE` 只报告、不重发。两次报告的差异说明提交后又发生了写入。

8. 若提交后 live 发生变化，这些字节属于另一会话：报告它们，不要吸收进提交，也不要改写快照。快照是证据；live 只是某一时刻的观察状态。用 JSONL 扫描指名写入者（步骤 4），绝不用 `updatedAt`/`runtimeState`。

暂存后（步骤 6）和提交后（步骤 7），用 OID 校验 blob 身份：索引 OID 必须等于源文件经 `git hash-object --path` 计算的结果，`HEAD` OID 必须等于索引 OID。`Fingerprint` 或干净的 `git status` 都不能证明该身份；只有在没有 eol 过滤器时才要求 SHA-256 字节相等（见步骤 6）。

注意：测试可能重写生成文件（已观察案例：`memoire_aq/` 下 5 个封存文件）。提交后单独处理，不要忽略。

## 步骤 5 — 审阅差异

```bash
git -C "<depot>" diff --stat
git -C "<depot>" diff -- "<chemin>"
git -C "<depot>" status --porcelain=v1
```

检查密钥、大体积二进制、缓存和范围外文件。行尾警告取决于 `core.autocrlf`：`CRLF will be replaced by LF`（入库规范化）与 `LF will be replaced by CRLF the next time Git touches it`（`autocrlf=true`）都属提示，但后者意味着下次检出会发生转换。校验 blob（步骤 6）并报告风险，不要重写仓库。

## 步骤 6 — 按显式路径暂存

### `git add` 前的指纹闸门

在步骤 4 的清单与当前状态一致之前，不得执行 `git add`：

```bash
(
  cd "<dossier-skill>" || exit 2
  find . -type f \( -path './SKILL.md' -o -path './scripts/*' -o -path './references/*' \) \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) | diff -u "<manifeste>" - || { echo "FAIL: écriture après validation — ne pas indexer"; exit 1; }
```

若 `diff` 非空，不得暂存：重跑对等、缓存扫描 + `skill-file-qa`、适用的测试和实际调用，然后重新记录清单。只重算 SHA-256 不能代替重新验证。`git add` 之后立即重复该检查：若 `diff` 再次非空，不得提交；重新验证后再执行 `git add`。下文校验的 OID 相等不能证明索引中的就是已验证版本。

```bash
git -C "<depot>" add -- "<chemin1>" "<chemin2>"
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --cached --stat
```

绝不使用 `git add -A`、`git add .` 或宽泛模式。按主题分组，并把重新生成的产物与代码改动分开。每次提交前核对已暂存清单。

随后逐文件校验实际写入索引的内容；一次只处理一个文件：

```bash
git -C "<depot>" config --show-origin --get core.autocrlf || echo "core.autocrlf: unset"
oid=$(git -C "<depot>" rev-parse ":<chemin-relatif-depot>")
[ -n "$oid" ] && git -C "<depot>" cat-file -e "$oid" || { echo "FAIL: blob absent"; exit 1; }
expected=$(git -C "<depot>" hash-object --path="<chemin-relatif-depot>" "<chemin-source>")
[ "$oid" = "$expected" ] || { echo "FAIL: OID indexe != source filtree"; exit 1; }
git -C "<depot>" cat-file blob "$oid" | sha256sum
sha256sum "<chemin-source>"
```

- `rev-parse ":<chemin-relatif-depot>"` 要求存在 stage 0 条目；OID 为空或 `cat-file -e` 失败时必须终止校验。
- OID 相等证明 Git 将按 `core.autocrlf` 与 `.gitattributes` 过滤后的源内容入库；这是主要校验。
- `core.autocrlf=true` 时两个 SHA-256 可能不同（源为 CRLF、blob 为 LF）：这是预期规范化，不是损坏。不要仅凭这一差异判定失败。
- `cat-file blob <oid>` 形式避开 `ref:chemin` 以及含 `/` 的 ref 的 MSYS 转换（已观察，未在所有 shell 中重跑）。
- 若 `core.autocrlf=true` 且源为 LF，blob 与源一致，但未来检出会写成 CRLF：如实报告。若要固定 `eol=lf`，经明确同意后建议 `.gitattributes`；不要修改 `core.autocrlf`，也不要重写仓库。管道会掩盖 `cat-file` 的失败：计算哈希前必须检查 OID 与 `cat-file -e`。

## 步骤 7 — 提交

```bash
git -C "<depot>" log --oneline -5
git -C "<depot>" commit -m "$(cat <<'EOF'
fix(physique): corriger les 20 etats S6
EOF
)"
```

沿用现有提交消息风格。一个提交只处理一个主题。不要使用 `--no-verify`，不要修改已发布的提交。提交后执行 `git -C "<depot>" status --porcelain=v1` 和 `git -C "<depot>" log -1 --stat`。根提交（此前没有 `HEAD`）在得出结论前先核对树：`git rev-parse "HEAD^{tree}"`、`git ls-tree -r HEAD`、`git ls-files -s` 与 `git hash-object --path` 必须与索引产生相同的 OID，然后立即重跑 `git status --porcelain=v1`；提交后的写入不属于该提交。首次提交前 `HEAD:<chemin-relatif>` 不存在：先用 `git rev-parse ":<chemin-relatif>"` 校验索引并等于 `git hash-object --path`，根提交后再校验 `HEAD:<chemin-relatif>`。

### 情况：本应有提交但 `git status` 为空

另一会话可能在我们操作期间创建了提交。不要创建空提交（`--allow-empty`），不要 amend，不要 reset。先确认 `HEAD` 是否已包含该工作：

```bash
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --stat
git -C "<depot>" log --oneline -5
git -C "<depot>" reflog -5
```

1. 把当前 SHA-256 与最后一次验证的 SHA-256（清单或已记录指纹）比较。若不同，旧 `PASS` 失效：在任何结论前，对当前字节重跑适用检查（有译本则跑对等、`skill-file-qa`、实际调用）。
2. 逐文件证明包含关系：`HEAD` 的 OID 必须等于过滤后源文件的 `hash-object --path` 结果。
3. 在 `HEAD` 中查找本次修改的唯一标记。OID 相等证明的是文件状态，不是提交作者；标记把内容与所述工作关联起来。

```bash
head_oid=$(git -C "<depot>" rev-parse "HEAD:<chemin-relatif-depot>")
src_oid=$(git -C "<depot>" hash-object --path="<chemin-relatif-depot>" "<chemin-source>")
[ "$head_oid" = "$src_oid" ] || { echo "FAIL: HEAD ne contient pas la source"; exit 1; }
git -C "<depot>" grep -F -n "<marqueur-unique>" HEAD -- "<chemin-relatif-depot>" \
  || { echo "FAIL: marqueur absent de HEAD"; exit 1; }
```

4. 若包含关系已证明，不要再为该工作提交：报告已有提交，并说明其消息可能描述的是另一会话的工作（比较 `reflog`、mtime 和消息）。若证明失败，排查（仓库错误、stash、部分提交）；不要伪造提交或 amend。

已观察案例（2026-10-26）：`SKILL.md` 验证时为 `c08c9461…`，当前为 `cc40b069…`；`status` 与 `diff` 为空；初始提交 `778a547` 于 11:54，之前 11:44–11:45 有并发写入；对当前字节重跑 `skill-file-qa` 得到 `RESULT PASS`；2 个文件的 `HEAD` OID 等于过滤后源文件；标记位于 L66/L141，脚本位于 L530。没有空提交，没有 amend；提交消息描述的是并发工作。

### 情况：审阅与提交之间 `HEAD` 前进

若在 `+N/−M` 的审阅与 QA PASS 之后，`git commit` 返回 `nothing to commit`，说明另一会话在验证期间创建了提交。不要 amend、reset、创建空提交，也不要重新执行 `git add`。

1. 提交前固定 `reviewed_oid=$(git -C "<depot>" rev-parse ":<chemin-relatif-depot>")`，并要求 `git hash-object --path="<chemin-relatif-depot>" "<chemin-source>"` 与它相等；记录已审阅的 diff（`git diff --cached --stat`）。
2. 失败后，将 `git -C "<depot>" rev-parse "HEAD:<chemin-relatif-depot>"` 与 `reviewed_oid` 比较，并在 `HEAD` 中核对唯一标记。`git show --stat HEAD` 相同只是线索，不是内容证明。OID 不同则停止，不要推送。
3. 若用户要求推送且 OID 相等，推送已有提交，不创建新提交也不 amend；执行 `git fetch origin` 后核对 `git rev-parse "origin/<branche>:<chemin-relatif-depot>"` 与 `git ls-remote origin "refs/heads/<branche>"`。`core.autocrlf=true` 时比较 OID，不要比较 SHA-256：2026-10-26 的案例中，`+9/−4`（`0b3ebce..4b71f23`），QA `RESULT PASS`，`INDEX_OID=WORKTREE_OID=4b71f23`，`git commit` 返回 `nothing to commit`，并发提交为 `70ccdd9`；`HEAD:SKILL.md=4b71f23` 是在推送后才比较的，而采纳证明必须早于推送；CRLF 源 `e46b8a92…` ≠ LF blob `3b3ff118…`。

```bash
git -C "<depot>" ls-tree -r HEAD -- "<chemin-relatif-depot>"
head_oid=$(git -C "<depot>" rev-parse "HEAD:<chemin-relatif-depot>")
```

校验已提交 blob 及其稳定性：`HEAD` 的 OID 必须与步骤 6 校验的 OID 一致。若 hook 可能在提交期间改动索引，用 `git hash-object --path` 重新比对 OID；存在 eol 过滤器时不要比较字节级 SHA-256。`scripts/run-fixture.sh` 在生产之外重放此情况的两个分支。

## 步骤 8 — 处理副作用

如果测试在提交后修改了文件，先检查 `git diff`，确认确实是重新生成，再创建独立的 `chore(...)` 提交。不要丢弃这些文件，也不要与功能提交混在一起。若文件与本任务无关，保持原样并如实报告。

## 步骤 9 — 检测已发布的过期归档

本地提交不会更新其他仓库中 `.qoder/skills/<nom>` 下的归档副本。最后一次提交后（包括步骤 8 的 `chore(...)` 提交），查找这些归档并与最终源码比较：

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py" \
  --skill "<dossier-skill>" \
  --search-root "<racine-espace>" \
  --search-root "C:/Users/Administrateur/.qoder/skills"
```

脚本只读，且属于 `commit-skill-work`，不属于被提交的 Skill：`<dossier-skill>` 可能只有 `SKILL.md`，所以上面的路径绝不能由 `<dossier-skill>/scripts/` 推导。它枚举仓库、包含 `.qoder/skills/<nom>` 的 ref，然后通过 `git hash-object --path` 将每个 blob 与源码比较（应用 eol 过滤器）。脚本不执行 `fetch`：`published` 仅表示本地存在 `refs/remotes/` ref，不表示已向服务器查询。

| 输出 | 含义 | 代码 |
|---|---|---|
| `RESULT NONE` | 未找到归档 | 0 |
| `RESULT FRESH` | 所有归档与源码一致 | 0 |
| `RESULT STALE` | 至少一个归档不同（`MISMATCH`、`MISSING` 或 `EXTRA`） | 1 |
| `RESULT FAIL` | 用法或环境无效 | 2 |

- `published` 指 `refs/remotes/` 下的 ref；`local` 仅指本地分支或标签。本地领先的归档（`[ahead 1]`）不算已发布。
- 与最终源码比较，而不是与提交差异比较：归档可能在提交前就已过期。在把原因归给当前提交前，先核对 `git log -1 --format='%h %s' -- ".qoder/skills/<nom>"`。由 `git init` 创建的 per-Skill 仓库会使 `Repositories` 从 N 变为 N+1，但仍为 `RESULT NONE`：脚本只查找 `<repo>/.qoder/skills/<nom>`，而该仓库把 `SKILL.md` 存放在根目录；这不是漏报归档（已观察：26 → 27）。在任何截断前先取退出码：`out=$(…); rc=$?; printf '%s\n' "$out" | tail -40`；`cmd | tail; echo $?` 取到的是 `tail` 的状态，不是脚本的（已观察：`ARCHIVE_EXIT=0`）。
- 此步骤中绝不复制、提交、合并、推送或删除归档。报告 `Archives : <ref> <commit> STALE (<n>/<N>)`，等待明确指令。重新发布是独立步骤（`publier-skill-qoder-vers-depot-git`），绝不自动执行。
- 已观察案例（2026-10-26）：相关修改成为提交 `3a47dab` 后，归档 `ddfd179` 变为过期，`3/3 MISMATCH`、`EXIT=1`；本 Skill 的归档 `96fd809` 在加入 `scripts/find_stale_archives.py` 前已有 `2/3` 文件不同。

## 步骤 10 — 仅在要求时推送

默认不推送。在报告中明确写「未推送」。

收到明确要求后：

```bash
git -C "<depot>" remote -v
git -C "<depot>" branch -vv
git -C "<depot>" ls-remote <url> "refs/heads/main" "refs/heads/skill/<nom>"
pushed_oid=$(git -C "<depot>" rev-parse HEAD)
git -C "<depot>" push origin "HEAD:refs/heads/skill/<nom>"
```

- 没有 remote：按步骤 3 发现并确认目标；执行 `git remote add` 前，用 `git ls-remote --heads <url>` 探测每个 URL：`RC` 非零或已存在 `refs/heads/skill/<nom>` 的候选不可用（询问，绝不强制）；`git remote add` 后，先记录 `git ls-remote origin refs/heads/main`，再 push `HEAD:refs/heads/skill/<nom>`，用 `branch -vv` 与 `ls-remote` 核对分支与 push 前固定的 `pushed_oid` 相等且 `refs/heads/main` 未变；若 `main` 已移动，报告并停止，不重推、不强制；不要未经同意推断 URL；`origin` 是共享仓库：推送专用分支 `skill/<nom>`，绝不推 `main`，绝不强制推送。已观察案例（2026-10-26）：远端 `main` 在 push 前后均为 `b66fdda`，push `a5095ce` 到 `skill/github-pr-create-merge-sans-gh`，`ls-remote` = `HEAD`。
- 不带 `-u` 推送：当本地分支为 `main` 或 `master` 时，`-u` 会让它跟踪 `origin/skill/<nom>`，使 `git pull`/`git push` 产生歧义（邻近 Skill 中观察到一致状态：`master [origin/skill/<nom>: gone]`、`master [origin/skill/<nom>: ahead 1]`）；仅当本地与远端分支名相同时才使用 `-u`。push 后重跑 `ls-remote`：要求已推送分支等于 push 前固定的 `pushed_oid`（push 后再 `rev-parse` 可能捕获并发提交），且 `main` 等于 push 前记录的基线；报告实际推送的分支。
- 「合并到 `main`」：若 `git merge-base origin/main HEAD` 返回 1（历史无共同祖先），不使用 `git merge --allow-unrelated-histories`，也不在本 worktree 中检出 `main`（它就是已安装的 Skill）。经明确同意应用内容时，按 `references/contenu-vers-main.md` 执行（索引 blob、树、基于 `origin/main` 的提交、fast-forward 推送、`ls-remote`、blob = 磁盘）。

## 步骤 11 — 验证已修改 Skill 的运行时可解析性

修改或提交 Skill 后，要证明运行时确实能解析它，而不仅是磁盘上存在：

1. 在最后一次写入之后，用 Skill 工具实际调用已修改的 Skill，尽量不带参数。若运行时返回基目录，必须与真正修改的目录一致，并且已加载内容必须包含最终版本的标志性规则：基目录只能证明绑定，不能证明注入正文已刷新；只有正文能判定版本。已观察案例（2026-10-26）：提交 `de7af23` 后，证明同时使用了基目录与两条新增规则（`GIT_CONFIG_COUNT=1`、`asserter d'abord`）；缓存正文不会包含它们。若之后又发生写入，先前调用不能作为证明。带参数调用时，注入层会在片段中把数字位置参数（第 1 至第 9 个）替换为参数文本——已观察第 1、2、3 个——并可能在正文末尾追加 `ARGUMENTS: …`；字面量 `$N`（字母 N）保持不变。这属于注入层替换，不是文件被改写。调用前后比较 `SKILL.md` 的 `stat`/`sha256sum` 与 `HEAD:SKILL.md` 的 OID；即使注入文本不同，也要求二者保持不变。已观察案例（2026-10-26）：`audit-recouvrement-skills-avant-creation` 提交 `c46cd75`（`200dd8b7…`/`baec727b…`），片段中的第 1、2、3 个参数被替换，磁盘与 `HEAD` 不变；本 Skill 带参数调用时 `$N` 保持原样，末尾追加 `ARGUMENTS: validation lecture seule uniquement ; ne rien committer ni modifier`，调用期间磁盘/`HEAD` 指纹不变。不要用 `$N` 作为验证替换行为的测试标记；加固片段请遵循 `harden-skill-argument-substitution`。公开片段优先使用具名变量；数字位置参数的转义方式尚未验证。对于动作型 Skill（例如 `github-pr-create-merge-sans-gh`），调用会注入其完整 playbook：只能把它当作解析证明（`base directory`、标志性内容、磁盘与 `HEAD` 指纹不变），不要执行其中任何步骤；真正的动作需要单独请求。已观察案例（2026-10-26）：提交 `0aebb4c` 后调用 `github-pr-create-merge-sans-gh`，注入了完整正文，`MANIFEST_MATCH_AFTER_INVOCATION`，`HEAD` 与 `git status` 不变，未发起任何 PR 调用。
2. 检查可能遮蔽用户级版本的同名目录；两个根都要查：

```bash
find "C:/Users/Administrateur/.qoder/skills" "<racine-espace>/.qoder/skills" -maxdepth 2 -type d -name "<nom-skill>" 2>/dev/null || true
```

某个根不存在时会被忽略；只看结果数量。预期只有一个结果：用户级根。项目级出现同名会遮蔽用户级 Skill；得出结论前先报告。

3. `/skills reload` 是界面命令，agent 无法执行：需要时请用户运行。实际调用成功比仅有文件或静态列表更有力。
4. 若调用失败或文件缺失，不要宣称 Skill 可用；如实报告失败。

## 错误与陷阱（已观察与预防性）

| 现象 | 原因 | 处理 |
|---|---|---|
| 根目录出现 `fatal: not a git repository` 且 `EXIT=128` | 项目根不是仓库 | 枚举 `.git`，再用 `git -C` 指向真实仓库；Skill 不在任何仓库时，读取邻近仓库的 `branch -vv`/`ls-remote` 发现约定并询问目标（LOCAL-ONLY、归档 `main`、或共享远程 + `skill/<nom>`） |
| `fatal: cannot change to '...ASTRO-Q°ODE_SYSTEME'` | 相对或非 ASCII 路径从另一个当前目录解析 | 用 `test -d` 确认，再传带引号的绝对路径 |
| `UnicodeEncodeError: 'charmap' codec ... cp1252` | Windows 控制台使用 cp1252 | 设置 `PYTHONIOENCODING=utf-8` 或输出 ASCII；清点脚本强制 UTF-8 |
| `warning: ... CRLF will be replaced by LF` 或 `LF will be replaced by CRLF ...` | 依据 `core.autocrlf` 的行尾规范化 | 仅提示；校验 blob（步骤 6）；`autocrlf=true` 时报告下次检出可能写成 CRLF |
| 状态中出现 `?? scripts/__pycache__/` | Python 导入缓存 | 排除；使用显式路径，经同意后加入 `.gitignore` |
| 一个仓库分支为 `master`，另一个为 `main`，或 `git init` 后出现 `fatal: ambiguous argument 'HEAD'` | 历史不同，或 HEAD 未出生（尚无提交） | 在未出生的 HEAD 上，用 `git symbolic-ref --short HEAD` 读取分支（`git rev-parse --abbrev-ref HEAD` 会失败）；`git add` 后用 `git rev-parse ":<chemin>"` = `git hash-object --path`，根提交后再用 `HEAD:<chemin>` |
| 测试在提交后重写封存文件 | 测试重新触发生成 | 审阅差异，再单独提交 `chore(...)` |
| 对范围问题回答「TOUT」 | 范围仍然模糊 | 给出确切的仓库与文件清单，在 `git add` 前请用户确认 |
| 重述后第二次回答「TOUT」 | 选项互斥 | 不再提第三个问题；执行推荐组合并声明，排除 push 与删除 |
| push 被拒（non-fast-forward 或历史无关），或候选 `ls-remote --heads` 失败 / 分支 `refs/heads/skill/<nom>` 已存在 | Skill 仓库与 `origin` 无关联、URL 不可达，或分支冲突 | 不推送、不强制；只读复探，选择有效目标或询问；推送专用分支 |
| `git merge-base origin/main HEAD` 为空（退出 1）的「merge to main」 | 历史无共同祖先；`main` 承载项目树 | 不合并（`--allow-unrelated-histories`），也不在本 worktree 中检出 `main`；经明确同意，按 `references/contenu-vers-main.md` 将内容应用到 `main` |
| 预期有提交却显示 `nothing to commit`，或 `status`/`diff` 为空 | 改动已被另一会话提交，或仓库选错 | 不创建空提交也不 amend；重新验证当前字节，用标记与 OID 证明包含关系，报告已有提交（步骤 7） |
| 已审阅 `+N/−M` 且 QA PASS 后 `git commit` 返回 `nothing to commit`，或 `git show --stat HEAD` 与已审阅 diff 相同但内容不同 | 另一会话在验证期间创建了提交；`--stat` 不证明内容 | 提交前固定 `reviewed_oid`；比较 `HEAD:<chemin>` 与 `hash-object --path` 到该 OID；相等且要求推送时，推送已有提交并核对远端 OID；否则不要推送 |
| 修改 `scripts/`/`references/` 后 `Fingerprint (final)` 不变，或清单中缺少该指纹 | 指纹只覆盖 `SKILL.md`，或 QA 证明的不是当前版本 | 重算资源文件的 SHA-256；重新验证并重新记录清单；不要据此认为没有变化 |
| 索引 blob 的 SHA-256 与源文件不同 | 预期 eol 过滤（`core.autocrlf`、`.gitattributes`）或文件选错 | 比较 OID（`hash-object --path` 与索引）；OID 相等时记录规范化，否则不要提交 |
| 已获得 PASS，随后又修改 `SKILL.md` 或译本 | 证明针对的版本已不存在 | 按顺序重跑对等、`skill-file-qa`、SHA-256 与实际调用，然后固定指纹 |
| `diff` 清单在 `git add` 前非空 | 验证后发生并发写入 | 不得暂存；重跑对等、QA、测试和实际调用，重新记录清单，再重复检查 |
| 每轮 `diff` 清单都非空，源文件每 10–30 秒被改写 | 另一会话持续重写目录 | 不要死循环：在 Skill 之外冻结快照，验证并归档其字节（步骤 4） |
| 对等与 QA 通过后第二次失效 | 证明针对的状态在检查期间已变化 | 使用不可变快照，并在 `git add` 前对 live 与清单跑 `diff`；任何差异都从步骤 1 重来 |
| 调用成功但 live 随后被修改，或注入正文在数字位置参数（第 1 至第 9 个）处显示参数值，或 `$N` 字面量保留且末尾追加 `ARGUMENTS: …` | 运行时解析活动目录；带参数调用会替换数字位置参数并追加 `ARGUMENTS: …`，但不改动 `$N` 字面量 | 调用后立即复比较 live == instantané，并要求调用前后 `SKILL.md`/`HEAD` OID 一致；参数替换不是写入，也不能用来测试 `$N`；否则该调用不能证明快照 |
| 根提交：`HEAD^{tree}`、`ls-tree -r HEAD`、`ls-files -s` 或 `hash-object --path` 不一致，或提交后 `status` 立即变化 | 此前没有 `HEAD`；hook 或提交期间发生写入 | 核对树与索引的 OID，然后立即重跑 `status`；不能只凭 `log -1 --stat` 下结论 |
| 清单缺失或被放进 Skill 目录 | 验证未留痕，或清单把自己算入 | 最后一次写入后把清单保存到 Skill 之外；否则从步骤 4 重来 |
| `RESULT PASS`，但 `Files (N)` 列出 `__pycache__/*.pyc` | 验证器不能证明没有缓存 | 只删除本会话创建的缓存，重跑 QA，要求 `Files (N)` 等于无缓存清单；若缓存预先存在且被保留，则验证无缓存快照 |
| 提交后归档出现 `MISMATCH`/`MISSING` | 归档副本未重新发布，或在提交前就已过期 | 报告 `STALE` 及 ref/commit；不要自动复制或推送 |
| `find_stale_archives.py` 退出码为 1，或归档只存在于本地 ref `[ahead 1]`，或 `git init` 后 `Repositories` +1 但为 `RESULT NONE` | 检测到过期归档（不是崩溃）、提交未推送，或 per-Skill 仓库没有 `.qoder/skills/<nom>` 路径 | 阅读报告（退出码 2 = 用法/环境）；标记 `local`，不要称为已发布；`cmd` 后接 `tail` 返回的是 `tail` 的状态：截断前先取 `rc=$?` |
| OID 为空或 `cat-file` 失败，但管道退出码为 0 | 路径未暂存、OID 多行，或缺少 `pipefail` | 先检查 `[ -n "$oid" ]` 与 `git cat-file -e`，再重跑 |
| 修改后的 Skill 未被解析或找不到 | 运行时索引未重载，或项目级同名遮蔽 | 调用该 Skill，检查两个根，再请用户执行 `/skills reload` |
| 方案已批准，但写入前大小/mtime/SHA-256 或行数不同；或会话等待超时而磁盘稳定 | 文件自规划后被重写；会话状态不是写入日志 | 重新采样、重读、按精确文本重新锚定、保留并发新增；不要恢复备份；按磁盘指纹判断活动，而不是 `runtimeState`；用 JSONL（`Write`/`Edit`）指名写入者，绝不用 `updatedAt`；任何编辑前先归类方案覆盖，只编辑 `ABSENT`/`PARTIAL`，每次并发写入后重跑所有门禁；重新验证最终字节 |
| 只更新源文件后 QA `RESULT PASS` 但对等 `RESULT FAIL` | 译本被有意保持不动（部分范围） | 分别报告 QA 与对等及差异；不得宣布包已验证；提出同步译本 |
| 流程中途范围前提变化，或 `Files (N)` QA ≠ 已暂存集合且未声明部分提交 | 决策基于过期状态（原先排除的文件变为被引用），或未声明部分提交 | 在 `git add` 前停止并重新确认；完整提交：`Files (N)` = `git diff --cached --name-only`；部分提交：已声明的子集、`git diff HEAD --name-only` = 索引且 `git status --porcelain=v1` 无包内其他非缓存文件；绝不删除预先存在的缓存 |
| 两个文件都已修改，但对等 `FAIL inline tokens: missing=[…]` 和/或 `extra=[…]` 处 `RESULT FAIL` | 译本把受保护的标识符改写成叙述文字，或全文出现次数不一致（token 在多个章节重复、译本增删示例；已观察：`$N` → 「该字面量」） | 不要放宽检查，也不要修改源文件；用 `INLINE_RE` 与 `Counter` 统计两个正文的多重集，逐项补缺并改写多余出现，再按顺序重跑对等、QA、清单与实际调用 |

## 最终检查清单

- [ ] 用绝对路径定位真实仓库，并读取分支。
- [ ] 在 Skill 目录初始化的仓库：确认 LOCAL-ONLY（无 origin、不 push；用 `git symbolic-ref --short HEAD` 读取分支，记录 `init.defaultBranch` 与邻近仓库），或发现共享远程（`branch -vv`/`ls-remote`）、确认目标、`git remote add`、推送 `skill/<nom>` 且 `ls-remote` = HEAD；与「仓库缺少 origin → 询问 URL」区分。
- [ ] 区分 SESSION 与 PREEXISTANT；既有改动已确认。
- [ ] 未使用 `git add -A` 或 `git add .`；使用显式路径。
- [ ] 已运行测试并记录结果；Skill 改动需 `RESULT PASS`；新的辅助脚本已与独立参考实现交叉核对（每会话最后 `timestamp` 与 `Write`/`Edit` 累计总数一致）并跑过负向矩阵。
- [ ] `skill-file-qa` 的 `Files (N)` 等于无缓存清单；测试或 `py_compile` 未留下 `__pycache__`/`*.pyc`；完整提交：`Files (N)` = `git diff --cached --name-only`；部分提交：`git diff --cached --name-only` ⊆ `Files (N)`、`git diff HEAD --name-only` = 已暂存集合且 `git status --porcelain=v1` 无包内其他非缓存文件；保留预先存在的缓存时，对无缓存快照跑 QA，绝不为了索引一致而删除缓存；若范围前提变化，`git add` 前重新确认。
- [ ] 已审阅差异；无密钥、大体积二进制或 `__pycache__`。
- [ ] 一个主题一个提交，消息与历史风格一致。
- [ ] 工作已被并发提交吸收：不创建空提交、不 amend；重新验证当前字节，用标记与 OID 证明包含关系，谨慎归属提交消息。
- [ ] 审阅与提交之间 `HEAD` 前进：提交前固定 `reviewed_oid`，推送前 `HEAD:<chemin>` 等于该 OID，推送已有提交且未新建提交或 amend，远端 OID 已核对。
- [ ] 根提交：首次提交前先用 `git rev-parse ":<chemin>"` = `git hash-object --path` 校验索引，提交后再校验 `HEAD:<chemin>`；`HEAD^{tree}`、`ls-tree -r HEAD`、`ls-files -s` 与 `hash-object --path` 已与索引核对，随后立即重跑 `status`。
- [ ] 提交后状态干净，或副作用已解释并单独提交。
- [ ] 最后一次提交后已检查邻近归档：`NONE`、`FRESH`，或报告了带 ref/commit 的 `STALE`。
- [ ] 未自动复制、提交或推送任何归档。
- [ ] 仅在要求时推送；候选已只读探测（`git ls-remote --heads <url>`：`RC=0`、目标分支不存在），远端 `main` 在 push 前后已记录且未变，remote、分支和哈希均已核对（`pushed_oid` 在 push 前固定并与 `ls-remote` 比对），仅当本地与远端分支名相同时才用 `-u`；无共同祖先时经 `references/contenu-vers-main.md` 将内容应用到 `main`，不检出也不合并。
- [ ] 已记录 `SKILL.md`、`scripts/` 与 `references/` 的 SHA-256；单独 `Fingerprint` 只覆盖 `SKILL.md`。
- [ ] 索引 blob 与 `HEAD` blob 均按 OID 与过滤后的源文件比对；SHA-256 差异已用 eol 过滤器解释。
- [ ] 最后一次写入之后，已按顺序重跑对等、`skill-file-qa`、SHA-256 与实际调用，并记录最终指纹；即使 QA 为 PASS，也不容忍缺失的 token。
- [ ] 最后一次写入后已将 SHA-256 清单保存到 Skill 之外；QA 的 `Fingerprint (final)` 等于清单中的 `./SKILL.md`。
- [ ] `git add` 前后清单 `diff` 均为空；验证与暂存之间没有写入。
- [ ] 清单差异通过完整重新验证处理，绝不用单纯重算 SHA-256 代替。
- [ ] 若源文件仍在变化：在 Skill 之外冻结快照，`instantané == live` 后再 `git add`，验证与归档都针对这些字节。
- [ ] 仅当 `live == instantané` 时才调用，并立即复比较。
- [ ] 已用 `--show-origin` 读取 `core.autocrlf`；已报告检出转换风险。
- [ ] 重复「TOUT」未再追问第三次，组合已声明。
- [ ] 已通过实际调用验证修改后的 Skill 可解析；若返回基目录须一致，且注入正文须包含最终版本的标志性规则（仅基目录不证明刷新）；无项目级/用户级同名遮蔽；若调用带参数，调用前后 `SKILL.md` 与 `HEAD` OID 一致（数字位置参数第 1 至第 9 个被替换、末尾追加 `ARGUMENTS: …`；`$N` 字面量不变；不是磁盘）；`/skills reload` 留给用户执行；动作型 Skill 的调用不执行其任何步骤。
- [ ] 方案已批准：写入前重新采样基线（大小/mtime/SHA-256）；按文本重读锚点；保留并发新增；未恢复任何备份；正文最多 499 行或已先行压缩；`description` 经脚本测量（≤ 1024 字符），`skill-file-qa` 的 N 等于最终文件；写入者经 JSONL 扫描（`Write`/`Edit`）确认，不用 `updatedAt`/`runtimeState`；方案覆盖已归类（`CURRENT`/`ALREADY_APPLIED`/`PARTIAL`/`ABSENT`/`CONFLICT`），仅编辑 `ABSENT`/`PARTIAL`，已采纳并发字节，未复用任何先前的 `PASS`。
- [ ] 部分范围（仅源文件）：译本保持不变；QA 与对等分别报告及差异；未宣布包已验证。

## 报告

```text
Dépôt : <chemin absolu> | Branche : <nom> | <LOCAL-ONLY|remote>
Commits : <hash court> <sujet>
Commit concurrent : aucun | <hash> inclus (OID+marqueur), message d'origine incertaine
Fichiers : <N> | Tests : <résultat>
Intégrité : blobs source <N>/<N> | autocrlf <valeur> | checkout <identique|converti>
Push : non effectué | <remote> <branche> <pushed_oid = hash distant> | main distant <avant>=<après> | main par contenu : aucun (<commit>)
Archives : aucune | <ref> <commit> <FRESH|STALE n/N> [published|local]
Gate : manifeste <n> fichiers | QA=manifeste <oui|non> | avant add <identique|écart> | après add <identique|écart> | Files (N)=inventaire <oui|non> | index=changements <oui|non> | arbre racine <réconcilié|N/A>
Instantané : aucun | <chemin> | live=instantané <oui|non> | gate <PASS/N/A>
Plan : baseline <sha> rééchantillonné <identique|écart> | ré-ancrage <n> édition(s) | couverture <CURRENT|ALREADY_APPLIED|PARTIAL|ABSENT|CONFLICT> | ajouts concurrents <préservés|aucun>
Périmètre : complet | source seule (traduction intacte, parité en attente)
Paquet : validé | non validé (source QA PASS, parité FAIL <n>)
Skill : <nom> | résolution : <base-dir ET contenu vérifié> | empreintes finales : <sha SKILL.md> <n scripts> <n references> (si un Skill est modifié)
Contrôles rejoués après la dernière écriture : parité <PASS|FAIL|N/A> | QA <PASS> | SHA-256 <n> | invocation <OK>
```

## 资源

- `scripts/inspect_git_state.py`：只读清点仓库、分支、状态、差异与 remote；ASCII 输出，退出码 0/1/2。
- `scripts/find_stale_archives.py`：只读检测邻近仓库中的 Skill 归档副本；将 blob OID 与源码比较，输出 `NONE`/`FRESH`/`STALE`；退出码 0（NONE/FRESH）、1（STALE）、2（用法/环境）。
- `scripts/run-fixture.sh`：一次性夹具，重放「采纳并发提交」与「拒绝 stat 相同但内容不同的提交」；只写入临时目录并删除；退出码 0（PASS）、1（FAIL）、2（用法/环境）。
- `references/skill-zh.md`：完整中文版本，需与法文版保持结构对等；对等规则见 `skill-doc-translation-parity`。
- `references/contenu-vers-main.md`：当 `git merge-base origin/main HEAD` 为空（历史无共同祖先）时向 `main` 应用内容；诊断、冻结、临时树、基于 `origin/main` 的提交、fast-forward 推送与 blob 核对；绝不检出 `main`，也不做 `--allow-unrelated-histories` 合并。
- `scripts/find_writers.py`：从会话 JSONL（`Write`/`Edit`、`input.file_path`）只读归因 Skill 的写入者；按会话输出最后一次写入；运行 `py -3 "C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_writers.py" --target "<dossier-skill>" --jsonl-dir "C:/Users/Administrateur/.qoder/projects/<projet>"`；退出码 0（找到）、1（没有）、2（用法/环境）。在把新的只读辅助脚本写入文档前，先用真实数据与独立参考实现交叉核对：每个会话的最后 `timestamp` 与 `Write`/`Edit` 累计总数都必须一致（仅核对时间不够）；再跑负向矩阵（空目录、无匹配、损坏 JSONL、无效 `--target`、`--max-files 0` 与 `1`）并确认无缓存；代码中把累计计数器与「最后写入」累加器分开（已观察缺陷：遇到更新 timestamp 时重置计数，`records 2` 而非 19 与 4）。
