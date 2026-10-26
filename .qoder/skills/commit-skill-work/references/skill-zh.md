# 提交 Skill 或嵌套仓库的改动

## 目标

定位真正包含被修改文件的仓库，只提交预期范围，且在没有明确要求时绝不推送。项目根目录不一定是仓库：有用的仓库通常是嵌套的，或每个 Skill 各自一个仓库。

## 触发条件

- 提出「commit」「git commit」「把这个 Skill 版本化」；
- 用户级 skills 目录下的 Skill 不在任何仓库中；
- 存在多个嵌套仓库且范围不明确；
- 测试在提交后重写了生成文件；
- 要求 push，或 Skill 仓库没有 `origin`。

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
py -3 scripts/inspect_git_state.py "<racine>" "C:/Users/Administrateur/.qoder/skills"
```

该脚本调用 `rev-parse`、`status`、`diff`、`log` 和 `remote`，不修改索引，并标出未跟踪的缓存目录。

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

`skill-file-qa` 的 `Fingerprint` 只覆盖 `SKILL.md`。已观察案例：两次修改 `scripts/inspect_git_state.py` 后，它仍为 `9901 bytes` 且 SHA-256 不变；只有修改 `SKILL.md` 后才变为 `9917 bytes`。因此提交前要记录所有资源的指纹：

```bash
find "<dossier-skill>" -type f \( -name "SKILL.md" -o -path "*/scripts/*" -o -path "*/references/*" \) ! -path "*/__pycache__/*" -print0 | xargs -0 sha256sum
```

若辅助文件在校验后发生变化，重新运行 `skill-file-qa` 并重算。不能仅凭 `Fingerprint` 断言整个 Skill 完整。

注意：测试可能重写生成文件（已观察案例：`memoire_aq/` 下 5 个封存文件）。提交后单独处理，不要忽略。

## 步骤 5 — 审阅差异

```bash
git -C "<depot>" diff --stat
git -C "<depot>" diff -- "<chemin>"
git -C "<depot>" status --porcelain=v1
```

检查密钥、大体积二进制、缓存和范围外文件。`warning: ... CRLF will be replaced by LF` 属于提示而非错误：如实说明，不要通过全局重写来"修复"。

## 步骤 6 — 按显式路径暂存

```bash
git -C "<depot>" add -- "<chemin1>" "<chemin2>"
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --cached --stat
```

绝不使用 `git add -A`、`git add .` 或宽泛模式。按主题分组，并把重新生成的产物与代码改动分开。每次提交前核对已暂存清单。

## 步骤 7 — 提交

```bash
git -C "<depot>" log --oneline -5
git -C "<depot>" commit -m "$(cat <<'EOF'
fix(physique): corriger les 20 etats S6
EOF
)"
```

沿用现有提交消息风格。一个提交只处理一个主题。不要使用 `--no-verify`，不要修改已发布的提交。提交后执行 `git -C "<depot>" status --porcelain=v1` 和 `git -C "<depot>" log -1 --stat`。

## 步骤 8 — 处理副作用

如果测试在提交后修改了文件，先检查 `git diff`，确认确实是重新生成，再创建独立的 `chore(...)` 提交。不要丢弃这些文件，也不要与功能提交混在一起。若文件与本任务无关，保持原样并如实报告。

## 步骤 9 — 仅在要求时推送

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

## 步骤 10 — 验证已修改 Skill 的运行时可解析性

修改或提交 Skill 后，要证明运行时确实能解析它，而不仅是磁盘上存在：

1. 用 Skill 工具实际调用已修改的 Skill。成功加载会返回其基目录，且必须与真正修改的目录一致。
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
| `warning: ... CRLF will be replaced by LF` | 行尾规范化 | 仅提示；不要重写整个仓库 |
| 状态中出现 `?? scripts/__pycache__/` | Python 导入缓存 | 排除；使用显式路径，经同意后加入 `.gitignore` |
| 一个仓库分支为 `master`，另一个为 `main` | 历史不同 | 读取 `rev-parse --abbrev-ref HEAD`；不要假设 |
| 测试在提交后重写封存文件 | 测试重新触发生成 | 审阅差异，再单独提交 `chore(...)` |
| 对范围问题回答「TOUT」 | 范围仍然模糊 | 给出确切的仓库与文件清单，在 `git add` 前请用户确认 |
| push 被拒（non-fast-forward 或历史无关） | Skill 仓库与 `origin` 无关联 | 推送专用分支；绝不强制 |
| 预期有提交却显示 `nothing to commit` | 已提交或仓库选错 | 在真实仓库中核对 `git log` 与 `git status` |
| 修改 `scripts/` 或 `references/` 后 `Fingerprint (final)` 不变 | 指纹只覆盖 `SKILL.md` | 重算资源文件的 SHA-256；不要据此认为没有变化 |
| 修改后的 Skill 未被解析或找不到 | 运行时索引未重载，或项目级同名遮蔽 | 调用该 Skill，检查两个根，再请用户执行 `/skills reload` |

## 最终检查清单

- [ ] 用绝对路径定位真实仓库，并读取分支。
- [ ] 区分 SESSION 与 PREEXISTANT；既有改动已确认。
- [ ] 未使用 `git add -A` 或 `git add .`；使用显式路径。
- [ ] 已运行测试并记录结果；Skill 改动需 `RESULT PASS`。
- [ ] 已审阅差异；无密钥、大体积二进制或 `__pycache__`。
- [ ] 一个主题一个提交，消息与历史风格一致。
- [ ] 提交后状态干净，或副作用已解释并单独提交。
- [ ] 仅在要求时推送；remote、分支和哈希均已核对。
- [ ] 已记录 `SKILL.md`、`scripts/` 与 `references/` 的 SHA-256；单独 `Fingerprint` 只覆盖 `SKILL.md`。
- [ ] 已通过实际调用验证修改后的 Skill 可解析；无项目级/用户级同名遮蔽；`/skills reload` 留给用户执行。

## 报告

```text
Dépôt : <chemin absolu> | Branche : <nom>
Commits : <hash court> <sujet>
Fichiers : <N> | Tests : <résultat>
Push : non effectué | <remote> <branche> <hash distant>
Skill : <nom> | résolution : <base-dir> | empreintes : <sha SKILL.md> <n scripts> <n references> (si un Skill est modifié)
```

## 资源

- `scripts/inspect_git_state.py`：只读清点仓库、分支、状态、差异与 remote；ASCII 输出，退出码 0/1/2。
- `references/skill-zh.md`：完整中文版本，需与法文版保持结构对等；对等规则见 `skill-doc-translation-parity`。
