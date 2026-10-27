---
name: dependency-script-contract-reaudit
description: "当复用的依赖脚本 SHA-256 变化时，在更新文档固定哈希前按完整 CLI 契约复审计：双采样 size/mtime/SHA-256，再逐项验证 --help、默认 --dest 的 FRESH、STALE/MISMATCH、EXTRA、不匹配 --dest 的 NONE、有效仓库与无效 --repo/--search-root 混合时的部分结果与 RESULT FAIL/退出码 2（环境错误优先于 STALE）、published/local 标签、usage 与 --max-depth 错误；全部通过后才同批更新所有固定哈希并记录旧→新差异，任一失败或脚本缺失即停止。用于依赖脚本哈希变化、固定哈希更新前、契约复测、--help 变化、退出码语义变化等场景；不替代首次契约审计、包完整性审计或写入后格式验收。"
---

# 依赖脚本契约复审计

## 目标

当另一个 Skill 提供的脚本被复用，且其 SHA-256 与文档中的固定值不一致时，先证明脚本稳定，再按完整 CLI 契约逐项复测；只有全部通过，才允许同批更新文档中的固定哈希。单跑一个 FRESH/STALE 用例不足以发现参数、退出码或优先级语义的变化。

## 触发条件

- 文档中的固定哈希与 `sha256sum` 结果不一致；
- 依赖脚本在会话期间被并发修改，或 size/mtime 变化；
- `--help`、退出码、`RESULT` 语义、标签或部分结果行为可能变化；
- 归档检测结果异常，怀疑依赖行为而非数据变化；
- 更新固定哈希前，需要可逐字复跑的验收记录。

## 不可协商规则

1. 以实物为准：只相信磁盘上的脚本与当前环境的实测输出。
2. 依赖脚本只读；不修改、不替换、不“修好”它。
3. 先双采样，再测试；脚本不稳定时停止。
4. 必须跑完整矩阵，不得只跑一个 FRESH/STALE 用例。
5. 任一用例输出或退出码不符、脚本缺失：停止，不更新任何固定哈希。
6. `STALE`（退出 1）是发现，`FAIL`（退出 2）是用法/环境错误；`NONE`（0）不等于 FRESH。
7. 多个仓库中任一 `--repo`/`--search-root` 无效时，环境错误优先：保留部分结果并返回 `RESULT FAIL`/2，即使另一仓库已 STALE。
8. 固定哈希只在全部通过且收到明确指令后更新，所有位置同批修改；不做部分更新。
9. 临时仓库只放在 `.qoder/tmp/dependency-contract-reaudit-<时间戳>/`，结束后只清理该目录。
10. 不提交、不推送、不修改被依赖 Skill 或其他 Skill。

## 第 1 步 — 定位依赖与固定哈希

```bash
DEP="$HOME/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py"
test -f "$DEP" || { echo "FAIL dependance absente"; exit 2; }
grep -rn "<ancien-hash>" "$HOME/.qoder/skills" --include="SKILL.md" --include="*.md"
```

记录旧哈希、size、mtime、日期，以及所有固定位置。位置不全时先补全，不要只改一处。

## 第 2 步 — 双采样

```bash
sha256sum "$DEP"; stat -c '%s %y' "$DEP"
sleep 2
sha256sum "$DEP"; stat -c '%s %y' "$DEP"
```

两次的 size 与 SHA-256 必须一致。不一致时重复一次；仍变化则停止并报告并发写入，参考 `skill-update-concurrency-safe`。不要用首次读取的哈希做后续结论。

## 第 3 步 — 完整契约矩阵

在隔离临时仓库中逐项执行，逐项记录实际输出与退出码。完整夹具与来源实测见 `references/contrat-find-stale-archives.md`。

| # | 用例 | 期望 |
|---|---|---|
| 1 | `--help` | 退出 0；出现 `--skill`、`--search-root`、`--repo`、`--dest`、`--max-depth` |
| 2 | 源目录名与归档目录一致，使用默认 `--dest` | `RESULT FRESH`，退出 0 |
| 3 | 修改源文件 | `RESULT STALE` + `MISMATCH`，退出 1 |
| 4 | 归档多出文件 | `EXTRA`，`RESULT STALE`，退出 1 |
| 5 | 有效但不匹配的 `--dest`（如 `.qoder/skills/absent`） | `RESULT NONE`，退出 0（假阴性，不代表 FRESH） |
| 6 | 有效仓库 + 无效 `--repo`/`--search-root` | 保留部分结果，`NOTE: resultats partiels`，`RESULT FAIL`，退出 2 |
| 7 | 仅本地分支 vs 存在 `refs/remotes/` | 分别标 `[local]` 与 `[published]` |
| 8 | 缺 `--repo`/`--search-root`、`--max-depth 0`、缺 `SKILL.md`、含 `..` 的 `--dest` | 退出 2 |

- 捕获退出码时不要经过管道；先运行，再取 `$?`。
- 默认 `--dest` 是 `.qoder/skills/<源目录名>`；源目录名与归档目录不一致会得到 `NONE`，不是契约失败。
- `NOTE not a repository` 表示路径存在但不是 Git 仓库，`Repositories` 为 0，结果可能是 `NONE`/0，不能当作 FRESH。
- 路径不存在时是 `FAIL environment` + `RESULT FAIL`/2，且保留其他仓库的部分结果；这与“存在但非 Git 目录”不同。

## 第 4 步 — 判定

| 结果 | 动作 |
|---|---|
| 8 项全部符合 | 可进入第 5 步；先报告实测值 |
| 任一输出或退出码不符 | 停止；报告用例、实际值、期望值；不更新哈希 |
| 脚本缺失或无法读取 | 停止；不依赖、不替换；报告缺失路径 |
| 双采样不稳定 | 停止；报告并发写入；稳定后从头重跑 |
| 发现新的合法语义 | 先更新本 Skill 的矩阵与参考文件，再重新全跑；不得先更新固定哈希 |

## 第 5 步 — 同批更新固定哈希（仅在明确指令下）

1. 列出所有固定位置；不得只改 `SKILL.md` 而留下参考文件中的旧值。
2. 记录旧哈希 → 新哈希、size、mtime、日期和被发现差异的用例。
3. 同批编辑所有位置。
4. 复查：旧哈希除标注为历史差异的段落外零命中；新哈希命中数等于预期位置数。

不要修改依赖脚本本身，也不要顺便修改无关文档。

## 第 6 步 — 验证与报告

对修改后的文档运行 `skill-file-qa`，要求 `RESULT PASS`、文件数符合预期、跨 Skill 引用全部解析。报告模板：

```text
依赖        : <绝对路径>
哈希        : <旧> -> <新> | size <旧> -> <新> | mtime <旧> -> <新>
双采样      : <一致/不一致> | 采样时间 <t1>, <t2>
契约矩阵    : 1..8 <通过/失败> | 失败项 <#>
标签/部分结果: published <n> | local <n> | partial env <PASS/FAIL>
固定哈希位置: <n> 处 | 同批更新 <是/否> | 旧哈希残留 <0/n>
验证        : skill-file-qa <PASS/FAIL> | 文档 SHA-256 <...>
```

## 错误与陷阱

| 症状 | 原因 | 动作 |
|---|---|---|
| 只重跑一个 FRESH/STALE 就更新哈希 | 复测粒度不足 | 跑完整矩阵 |
| `RESULT NONE` 被当作 FRESH | `--dest` 错误或仓库未覆盖 | 检查 `--dest` 与 `--repo` |
| 已有 STALE 却返回 FAIL/2 | 另一个路径无效，环境错误优先 | 保留部分结果；修正路径后重跑 |
| `STALE` 被当成崩溃 | 退出 1 是发现 | 读报告；退出 2 才是用法/环境错误 |
| 哈希在测试中途变化 | 依赖被并发修改 | 双采样后重跑；不稳定则停止 |
| `NOTE not a repository` 后得到 NONE | 路径存在但不是 Git 仓库 | 不作为 FRESH；换有效仓库或去掉该路径 |
| `FAIL environment: repository not found` | `--repo`/`--search-root` 路径不存在 | 修正路径；有部分结果时按 FAIL/2 处理 |
| 旧哈希仍被引用 | 只改了一处 | 同批更新并复查零命中 |

## 完成检查

- [ ] 依赖存在，旧哈希、size、mtime、日期已记录。
- [ ] 双采样一致；不一致时已停止或重跑。
- [ ] 8 项用例逐项实际运行，记录了输出与退出码。
- [ ] 失败、缺失或不稳定时没有更新任何哈希。
- [ ] 固定哈希位置已列全，同批更新，旧值除历史差异段外零命中。
- [ ] 修改后的文档通过 `skill-file-qa`。
- [ ] 未修改依赖脚本、未提交、未推送。
- [ ] 临时目录已清理。

## 资源

- `references/contrat-find-stale-archives.md`：完整临时仓库夹具、来源会话实测输出、`9d0ef629…`→`eb3ccb61…` 差异与覆盖边界。
- `audit-skill-tool-contracts`：首次使用前的契约审计与负向能力探针。
- `skill-package-integrity-audit`：包清洁度与归档 NONE/FRESH/STALE。
- `skill-update-concurrency-safe`：并发写入与稳定性检查。
- `skill-file-qa`：写入后的格式与引用验收。
