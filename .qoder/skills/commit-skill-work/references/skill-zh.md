# 提交 Skill 或嵌套仓库的改动

## 目标

定位真正包含被修改文件的仓库，只提交预期范围，且在没有明确要求时绝不推送。项目根目录不一定是仓库：有用的仓库通常是嵌套的，或每个 Skill 各自一个仓库。

## 触发条件

- 提出「commit」「git commit」「把这个 Skill 版本化」；
- 用户级 skills 目录下的 Skill 不在任何仓库中；
- 存在多个嵌套仓库且范围不明确；
- 测试在提交后重写了生成文件；
- 要求 push，或 Skill 仓库没有 `origin`；
- 核对 blob/源文件 OID，或出现 `core.autocrlf` 警告；
- `SKILL.md`、脚本或译本在验证后才被写入，需要重新验收；
- `skill-file-qa` 返回 `RESULT PASS`，但 `Files (N)` 中含缓存；
- 提交后其他仓库中存在该 Skill 的归档；
- 验证与 `git add` 之间发生并发写入，或指纹清单不一致。

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
py -3 "<dossier-skill>/scripts/inspect_git_state.py" "<racine>" "C:/Users/Administrateur/.qoder/skills"
```

该脚本调用 `rev-parse`、`status`、`diff`、`log` 和 `remote`，不修改索引，并标出未跟踪的缓存目录。脚本路径必须保持绝对：从项目根执行 `scripts/inspect_git_state.py` 会因 `can't open file` 失败（退出码 2）。

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
| Skill 目录不在任何仓库中 | 询问：在 Skill 目录初始化仓库、保持未提交，还是指向已有仓库 |
| 目录位于嵌套仓库内 | 使用该仓库，并用 `ls-files --error-unmatch` 确认 |
| 多个仓库都有改动 | 每个仓库、每个主题各自提交 |
| 存在无关的既有改动 | 纳入前先询问 |
| Skill 仓库的 `origin` 是共享仓库 | 推送到专用分支 `skill/<nom>`，未经同意绝不推 `main` |
| 仓库没有 `origin` | 询问 URL；不要猜测 |

对「TOUT」的回答：先用互斥选项和确切的仓库、文件清单重述一次。若第二次仍回答「TOUT」，不要再提第三个问题：执行推荐组合，在报告中明确声明，并排除未列出或不可逆的动作（push、删除、重写历史）。仅当 `git init` 本来就在已确认选项中时才可执行。已观察案例（2026-10-26）：连续两次「TOUT」→ Skill 本地仓库 + 在公开仓库本地克隆的 `main` 上提交，不创建重复的专用分支，也不推送。下一条关于无关公开仓库的规则优先：绝不推送到 `main`，绝不把用户级 Skill 提交到无关公开仓库。

仅在明确同意后才执行 `git init`。不要修改 Git 配置：只读取 `git config user.name` 与 `git config user.email`，不要改写。绝不要把用户级 Skill 提交到无关公开仓库的 `main`。

## 步骤 4 — 提交前验证

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

对预先存在的缓存，先询问再删除。含缓存的 `PASS` 不能作为已暂存包的证明。

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

记录清单与最终指纹，并绑定到被验证版本。若在步骤 4 之后又发生写入，从步骤 1 重来。不得把最后写入之前获得的 PASS 当作当前文件的验证结果。对等检查是结构性的（代码块、表格、标题、清单、标识符、数字），不能证明译文的语义质量。

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

沿用现有提交消息风格。一个提交只处理一个主题。不要使用 `--no-verify`，不要修改已发布的提交。提交后执行 `git -C "<depot>" status --porcelain=v1` 和 `git -C "<depot>" log -1 --stat`。

校验已提交 blob 及其稳定性：

```bash
git -C "<depot>" ls-tree -r HEAD -- "<chemin-relatif-depot>"
head_oid=$(git -C "<depot>" rev-parse "HEAD:<chemin-relatif-depot>")
```

`HEAD` 的 OID 必须与步骤 6 校验的 OID 一致。若 hook 可能在提交期间改动索引，用 `git hash-object --path` 重新比对 OID；存在 eol 过滤器时不要比较字节级 SHA-256。

## 步骤 8 — 处理副作用

如果测试在提交后修改了文件，先检查 `git diff`，确认确实是重新生成，再创建独立的 `chore(...)` 提交。不要丢弃这些文件，也不要与功能提交混在一起。若文件与本任务无关，保持原样并如实报告。

## 步骤 9 — 检测已发布的过期归档

本地提交不会更新其他仓库中 `.qoder/skills/<nom>` 下的归档副本。最后一次提交后（包括步骤 8 的 `chore(...)` 提交），查找这些归档并与最终源码比较：

```bash
py -3 "<dossier-skill>/scripts/find_stale_archives.py" \
  --skill "<dossier-skill>" \
  --search-root "<racine-espace>" \
  --search-root "C:/Users/Administrateur/.qoder/skills"
```

脚本只读。它枚举仓库、包含 `.qoder/skills/<nom>` 的 ref，然后通过 `git hash-object --path` 将每个 blob 与源码比较（应用 eol 过滤器）。脚本不执行 `fetch`：`published` 仅表示本地存在 `refs/remotes/` ref，不表示已向服务器查询。

| 输出 | 含义 | 代码 |
|---|---|---|
| `RESULT NONE` | 未找到归档 | 0 |
| `RESULT FRESH` | 所有归档与源码一致 | 0 |
| `RESULT STALE` | 至少一个归档不同（`MISMATCH`、`MISSING` 或 `EXTRA`） | 1 |
| `RESULT FAIL` | 用法或环境无效 | 2 |

- `published` 指 `refs/remotes/` 下的 ref；`local` 仅指本地分支或标签。本地领先的归档（`[ahead 1]`）不算已发布。
- 与最终源码比较，而不是与提交差异比较：归档可能在提交前就已过期。在把原因归给当前提交前，先核对 `git log -1 --format='%h %s' -- ".qoder/skills/<nom>"`。
- 此步骤中绝不复制、提交、合并、推送或删除归档。报告 `Archives : <ref> <commit> STALE (<n>/<N>)`，等待明确指令。重新发布是独立步骤（`publier-skill-qoder-vers-depot-git`），绝不自动执行。
- 已观察案例（2026-10-26）：相关修改成为提交 `3a47dab` 后，归档 `ddfd179` 变为过期，`3/3 MISMATCH`、`EXIT=1`；本 Skill 的归档 `96fd809` 在加入 `scripts/find_stale_archives.py` 前已有 `2/3` 文件不同。

## 步骤 10 — 仅在要求时推送

默认不推送。在报告中明确写「未推送」。

收到明确要求后：

```bash
git -C "<depot>" remote -v
git -C "<depot>" branch -vv
git -C "<depot>" push -u origin "HEAD:refs/heads/skill/<nom>"
```

- 没有 remote：询问 URL，不要从其他仓库推断。
- `origin` 是共享仓库：推送专用分支，绝不推 `main`，绝不强制推送。
- 推送后比较本地与远端：

```bash
git -C "<depot>" rev-parse HEAD
git -C "<depot>" ls-remote origin "refs/heads/<branche>"
```

远端哈希必须等于本地哈希。报告实际推送的分支：`HEAD:refs/heads/<branche>` 可能让本地分支跟踪一个不同名称的远端分支。

## 步骤 11 — 验证已修改 Skill 的运行时可解析性

修改或提交 Skill 后，要证明运行时确实能解析它，而不仅是磁盘上存在：

1. 在最后一次写入之后，用 Skill 工具实际调用已修改的 Skill。若运行时返回基目录，必须与真正修改的目录一致；否则要求已加载内容包含最终版本的标志性规则。若之后又发生写入，先前调用不能作为证明。
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
| 根目录出现 `fatal: not a git repository` 且 `EXIT=128` | 项目根不是仓库 | 枚举 `.git`，再用 `git -C` 指向真实仓库 |
| `fatal: cannot change to '...ASTRO-Q°ODE_SYSTEME'` | 相对或非 ASCII 路径从另一个当前目录解析 | 用 `test -d` 确认，再传带引号的绝对路径 |
| `UnicodeEncodeError: 'charmap' codec ... cp1252` | Windows 控制台使用 cp1252 | 设置 `PYTHONIOENCODING=utf-8` 或输出 ASCII；清点脚本强制 UTF-8 |
| `warning: ... CRLF will be replaced by LF` 或 `LF will be replaced by CRLF ...` | 依据 `core.autocrlf` 的行尾规范化 | 仅提示；校验 blob（步骤 6）；`autocrlf=true` 时报告下次检出可能写成 CRLF |
| 状态中出现 `?? scripts/__pycache__/` | Python 导入缓存 | 排除；使用显式路径，经同意后加入 `.gitignore` |
| 一个仓库分支为 `master`，另一个为 `main` | 历史不同 | 读取 `rev-parse --abbrev-ref HEAD`；不要假设 |
| 测试在提交后重写封存文件 | 测试重新触发生成 | 审阅差异，再单独提交 `chore(...)` |
| 对范围问题回答「TOUT」 | 范围仍然模糊 | 给出确切的仓库与文件清单，在 `git add` 前请用户确认 |
| 重述后第二次回答「TOUT」 | 选项互斥 | 不再提第三个问题；执行推荐组合并声明，排除 push 与删除 |
| push 被拒（non-fast-forward 或历史无关） | Skill 仓库与 `origin` 无关联 | 推送专用分支；绝不强制 |
| 预期有提交却显示 `nothing to commit` | 已提交或仓库选错 | 在真实仓库中核对 `git log` 与 `git status` |
| 修改 `scripts/` 或 `references/` 后 `Fingerprint (final)` 不变 | 指纹只覆盖 `SKILL.md` | 重算资源文件的 SHA-256；不要据此认为没有变化 |
| 索引 blob 的 SHA-256 与源文件不同 | 预期 eol 过滤（`core.autocrlf`、`.gitattributes`）或文件选错 | 比较 OID（`hash-object --path` 与索引）；OID 相等时记录规范化，否则不要提交 |
| 已获得 PASS，随后又修改 `SKILL.md` 或译本 | 证明针对的版本已不存在 | 按顺序重跑对等、`skill-file-qa`、SHA-256 与实际调用，然后固定指纹 |
| `diff` 清单在 `git add` 前非空 | 验证后发生并发写入 | 不得暂存；重跑对等、QA、测试和实际调用，重新记录清单，再重复检查 |
| 清单中缺少 QA 的 `Fingerprint (final)` | QA 证明的不是当前版本 | 不得提交；重新验证并重新记录清单 |
| 清单缺失或被放进 Skill 目录 | 验证未留痕，或清单把自己算入 | 最后一次写入后把清单保存到 Skill 之外；否则从步骤 4 重来 |
| `RESULT PASS`，但 `Files (N)` 列出 `__pycache__/*.pyc` | 验证器不能证明没有缓存 | 只删除本会话创建的缓存，重跑 QA，要求 `Files (N)` 等于无缓存清单 |
| 提交后归档出现 `MISMATCH`/`MISSING` | 归档副本未重新发布，或在提交前就已过期 | 报告 `STALE` 及 ref/commit；不要自动复制或推送 |
| `find_stale_archives.py` 退出码为 1 | 检测到过期归档，不是崩溃 | 阅读报告；退出码 2 表示用法/环境错误 |
| 仅在本地 ref `[ahead 1]` 上找到归档 | 提交未推送 | 标记为 `local`，不要称为已发布 |
| OID 为空或 `cat-file` 失败，但管道退出码为 0 | 路径未暂存、OID 多行，或缺少 `pipefail` | 先检查 `[ -n "$oid" ]` 与 `git cat-file -e`，再重跑 |
| 修改后的 Skill 未被解析或找不到 | 运行时索引未重载，或项目级同名遮蔽 | 调用该 Skill，检查两个根，再请用户执行 `/skills reload` |

## 最终检查清单

- [ ] 用绝对路径定位真实仓库，并读取分支。
- [ ] 区分 SESSION 与 PREEXISTANT；既有改动已确认。
- [ ] 未使用 `git add -A` 或 `git add .`；使用显式路径。
- [ ] 已运行测试并记录结果；Skill 改动需 `RESULT PASS`。
- [ ] `skill-file-qa` 的 `Files (N)` 等于无缓存清单；测试或 `py_compile` 未留下 `__pycache__`/`*.pyc`。
- [ ] 已审阅差异；无密钥、大体积二进制或 `__pycache__`。
- [ ] 一个主题一个提交，消息与历史风格一致。
- [ ] 提交后状态干净，或副作用已解释并单独提交。
- [ ] 最后一次提交后已检查邻近归档：`NONE`、`FRESH`，或报告了带 ref/commit 的 `STALE`。
- [ ] 未自动复制、提交或推送任何归档。
- [ ] 仅在要求时推送；remote、分支和哈希均已核对。
- [ ] 已记录 `SKILL.md`、`scripts/` 与 `references/` 的 SHA-256；单独 `Fingerprint` 只覆盖 `SKILL.md`。
- [ ] 索引 blob 与 `HEAD` blob 均按 OID 与过滤后的源文件比对；SHA-256 差异已用 eol 过滤器解释。
- [ ] 最后一次写入之后，已按顺序重跑对等、`skill-file-qa`、SHA-256 与实际调用，并记录最终指纹。
- [ ] 最后一次写入后已将 SHA-256 清单保存到 Skill 之外；QA 的 `Fingerprint (final)` 等于清单中的 `./SKILL.md`。
- [ ] `git add` 前后清单 `diff` 均为空；验证与暂存之间没有写入。
- [ ] 清单差异通过完整重新验证处理，绝不用单纯重算 SHA-256 代替。
- [ ] 已用 `--show-origin` 读取 `core.autocrlf`；已报告检出转换风险。
- [ ] 重复「TOUT」未再追问第三次，组合已声明。
- [ ] 已通过实际调用验证修改后的 Skill 可解析；无项目级/用户级同名遮蔽；`/skills reload` 留给用户执行。

## 报告

```text
Dépôt : <chemin absolu> | Branche : <nom>
Commits : <hash court> <sujet>
Fichiers : <N> | Tests : <résultat>
Intégrité : blobs source <N>/<N> | autocrlf <valeur> | checkout <identique|converti>
Push : non effectué | <remote> <branche> <hash distant>
Archives : aucune | <ref> <commit> <FRESH|STALE n/N> [published|local]
Gate : manifeste <n> fichiers | QA=manifeste <oui|non> | avant add <identique|écart> | après add <identique|écart>
Skill : <nom> | résolution : <base-dir|contenu vérifié> | empreintes finales : <sha SKILL.md> <n scripts> <n references> (si un Skill est modifié)
Contrôles rejoués après la dernière écriture : parité <PASS/N/A> | QA <PASS> | SHA-256 <n> | invocation <OK>
```

## 资源

- `scripts/inspect_git_state.py`：只读清点仓库、分支、状态、差异与 remote；ASCII 输出，退出码 0/1/2。
- `scripts/find_stale_archives.py`：只读检测邻近仓库中的 Skill 归档副本；将 blob OID 与源码比较，输出 `NONE`/`FRESH`/`STALE`；退出码 0（NONE/FRESH）、1（STALE）、2（用法/环境）。
- `references/skill-zh.md`：完整中文版本，需与法文版保持结构对等；对等规则见 `skill-doc-translation-parity`。
