# 案例：输出契约偏差的文档修复（2026-10-27）

## 来源

- 主会话：`39a147b6-295f-455f-93d4-a13b6c657601`（标题「更新库存技能文档」）。读取时 `hasMoreBefore=false`、`revision=72`、`runtimeState=running`、`activeTurnId=b2a735c3-546b-43a9-bebd-14b536a34d13`（该回合为「执行 /skills reload」，属观察时点状态）。
- 验收会话：`03ce5a9c-923c-510c-a849-e614d27e5c47`（标题「Test d'acceptation du Skill」）。读取时 `runtimeState=cold`、`hasMoreBefore=false`；1 个用户回合、11 次工具调用。
- 目标 Skill：`inventory-installed-skills`，安装于 `C:\Users\Administrateur\.qoder\skills\inventory-installed-skills`。
- 验收 prompt 明确：安装目录只读、夹具放 `~/.qoder/tmp/acceptance-20261027T124534Z`、`py -3 -B`、不修正只报告、报告须给出 ACCEPTÉ / ACCEPTÉ AVEC RÉSERVES / REFUSÉ。

## 验收结论（逐字要点，2026-10-27T12:46Z 写入）

- 8 步全部 PASS；`skill-file-qa` 为 PASS / 9 pass / 0 fail / 0 warn / Files (2)。
- 两个错误分支均 RC=2，消息 `ERROR: cannot read snapshot: [Errno 2] No such file or directory`。
- 偏差（文档层）：
  - 文档承诺 `stability: t1 -> t2 | unchanged: N | no drift`，脚本实际打印 `## Drift vs snapshot (t1)`、`added: 0 | … | unchanged: 1`、`- no drift detected`；同秒 `window: <1 s` 未被观测。
  - `--format json` 下 description 不以明文出现，只有 `description_sha256` 与 `desc_chars`。
  - 返回码、`counts`/`skills` 键、exit 2 分支「conformes」。
- 结论：**ACCEPTÉ AVEC RÉSERVES**（仅文档）；安装 `SKILL.md` SHA-256 前后均为 `24a67513…8b67`。

## 主会话复现（夹具在安装目录外，已删除）

全部命令使用 `py -3`，夹具根 `evidence-20261027-inv`，输出为工具结果原文摘录。

| # | 运行 | 结果 |
|---|---|---|
| 1 | `--format json` 枚举 | RC=0；12 个顶层键；`skills[0]` 10 键，无 description 正文；`drift=null` |
| 2 | md 模式 `--snapshot` | RC=0；`snapshot written: …\s.json` |
| 3 | 同根 `--compare` | RC=0；`## Drift vs snapshot (2026-10-27T13:53:54+01:00)`；`added: 0 \| removed: 0 \| moved: 0 \| description changed: 0 \| content changed: 0 \| unchanged: 1`；`- no drift detected` |
| 4 | 异根 `--compare` | RC=0；`removed: 1`、`unchanged: 0`、`- removed: user/inventory-installed-skills`（会话输出仅保留尾部，前段被截断，不补写） |
| 5 | JSON + `--snapshot` | `snapshot written` 出现 0 次（`grep_rc=1`），文件已生成 939 B |
| 6 | JSON + `--compare` | 顶层 12 键；`drift` 含 `snapshot_generated_at`、`old_counts`、`new_counts`、`added`、`removed`、`moved`、`description_changed`、`content_changed`、`unchanged` |
| 7 | 快照文件 | 顶层 7 键：`format`、`generated_at`、`user_root`、`project_root`、`counts`、`skills`、`anomalies` |
| 8 | 单调用同时 `--snapshot --compare` | RC=2；`ERROR: cannot read snapshot: [Errno 2] No such file or directory: '…\\both.json'` |

第 5 项与第 8 项不在验收报告的偏差列表中：第 5 项由主会话自行发现，第 8 项用于确认原有文档警告仍成立。

## 用户裁决

主会话以 AskUserQuestion 询问「是否按方案执行？脚本层根校验是否一并加？」，答复为 **「仅改 SKILL.md（推荐）」**。因此脚本未改，根不一致的假漂移以文档规则与失败模式呈现，而非退出码防护。

## 修复范围

- 仅 `SKILL.md`；`description` 未改（934 字符，触发条件未变）。
- 改动内容：规则 6/7（drift 段为唯一稳定性证据；同一组根必须重传）、第 1/3 节示例与注释、输出契约改为实测 drift 块、新增 JSON 小节、失败模式加 4 行、验收清单加 2 条。

## 写入后验证

- `skill-file-qa`：PASS，9 pass / 0 fail / 0 warn，Files (2)，body 182 行。
- 按更新后文档在隔离夹具 `replay-20261027-inv` 复放，令牌输出：
  `JSON_KEYS_OK`、`SKILL_KEYS_OK`、`DRIFT_NULL_OK`、`DRIFT_HEADER_TRUE`、`DRIFT_COUNTS_TRUE`、`NO_DRIFT_LINE_TRUE`、`NO_STABILITY_LINE_TRUE`、`SNAPSHOT_KEYS_OK`、`JSON_NO_HINT_FILE_OK`、`MISMATCH_FALSE_DRIFT_CONFIRMED`。
- 退出码：正常 snapshot 0、compare 0、异根 compare 0（假漂移）、JSON+快照 0 且无提示、单调用双模式 2。
- 清理：两个夹具目录均不存在；安装目录无 `__pycache__`/`.pyc`。

## 第二案例：`verifier-parite-doc-script-skill` 端到端修复（2026-10-27T13:08–13:11Z）

来源：会话 `f38c2627…` 的端到端回合；目标安装于 `C:\Users\Administrateur\.qoder\skills\verifier-parite-doc-script-skill`。同回合工具输出列出 `~/.qoder/tmp/rep-contract-edit-backup-20261027T1410`，其中 `SKILL.md` 为 `9babc1f1f42a9d136e583f810a361d3466c1c2e69da79880b844a49cf2f13232`（12 605 B，本包创建后的时点副本）；该目录现已不存在。

| 文件 | 基线（修复前） | 修复后 |
|---|---|---|
| `SKILL.md` | `8eb7ce8cb1e90aaf5ad4e8415fac5d198c44db980606d457770f3a4d03e64936`（13 685 B，174 行） | `15892fe6d5bcb73b9b5cc863ddbdfb6b6747c12fb6ddbf9704ba4858bc9f24f3`（15 660 B，204 行；2026-10-27 本会话复核仍为该值） |
| `scripts/verifier_parite_cles.py` | `59871b7917b0e8c79b6004f4f565c078d66775cf4922e48d530483b74c405380`（11 270 B） | 未变 |
| `references/cas-verifie-2026-10-26.md` | `aa5ee06dffce018124b736e6b74937196d91c908aa3ed75bb18dd80d28a38274` | 未变 |
| `references/harnais-fixtures.md` | `6ef01c3a24e1a3ae9a8dec88c5ed5ebd8b2f089617dca2837eb2027f087d00f1` | 未变 |

三类 B 偏差（会话实测）：

- 文档全文 0 命中 `--json`；实测输出 12 键对象（`allowed`、`doc_keys`、`doc_only`、`docs`、`matched`、`out_of_scope`、`result`、`runtime_keys`、`runtime_only`、`scope_fallback_all`、`scripts`、`skill`），`DOC_ONLY` 非空时 `result=FAIL` 且 RC=1；
- `--doc`/`--script` 未文档化；限定后 `DOCS=1`、`SCRIPTS=1`、`OUT_OF_SCOPE` 33→5，`DOC_KEYS` 不变；
- 文档只列 6 个字段；实发 11 个计数字段（`SKILL`、`DOCS`、`SCRIPTS`、`SCOPE_FALLBACK_ALL`、`DOC_KEYS`、`RUNTIME_KEYS`、`MATCHED`、`DOC_ONLY`、`RUNTIME_ONLY`、`ALLOWED`、`OUT_OF_SCOPE`）+ 5 类 detail 行（`DOC_ONLY_KEY`、`RUNTIME_ONLY_KEY`、`ALLOWED_KEY`、`OUT_OF_SCOPE_KEY`、`ERROR`）+ 末尾 `RESULT`。

2026-10-27 本会话在安装目录外副本上复测（`py -3 -B`，md 模式 RC=0）：`DOC_KEYS=17`、`RUNTIME_KEYS=17`、`MATCHED=17`、`DOC_ONLY=0`、`RUNTIME_ONLY=0`、`OUT_OF_SCOPE=33`；`--json` 12 键且 `result=PASS`；`--help` 旗标 7 个（`--allow-key`、`--doc`、`--help`、`--json`、`--scope-key`、`--script`、`--skill`）。修复前自检为 `DOC_KEYS=6`、`MATCHED=6`、`RUNTIME_ONLY=11`：补文档提高覆盖、`RUNTIME_ONLY` 归零，不是回归。

合成夹具（同一副本，RC 与计数均为实测）：

- `synthetic-skill`：代码块写 `REAL_KEY=1` 与 `GHOST_KEY=2`，脚本只 `print("REAL_KEY=1")` → RC=1，`DOC_KEYS=2`、`MATCHED=1`、`DOC_ONLY=1`，`DOC_ONLY_KEY=GHOST_KEY | occurrences=1 | first=<SKILL.md:9> | section=Script`；
- `synthetic-noscript-name`：`SKILL.md` 不提名脚本 → `SCOPE_FALLBACK_ALL=yes`、RC=0、`RESULT=PASS`。

会话内按改后文档复放 36 项断言全部 `_TRUE`（段头顺序、detail 位置与格式、JSON 键集、GHOST 分支原文、限定选项、fallback、用法错误 RC=2），`FALSE_COUNT=0`。

边界：以上数值只对 `15892fe6…` 这个版本成立；目标版本变化后先重测，不照抄。`ALLOWED_KEY` 分支在会话内未实际触发，仅存在性覆盖。

## 指纹（安装目录）

| 文件 | 修复前 | 修复后 |
|---|---|---|
| SKILL.md | `24a675137f77bcb7a53340584a1ba717c9cc30e0a34fc63a2b35a1ae34218b67`（13093 B，2026-10-27 00:14:58 +0100） | `f11285448017c28bca799ade27352e43f945e8dfe4017ae3fd2352f4067a70c1`（15985 B，2026-10-27 13:56:13 +0100） |
| scripts/inventory_skills.py | `262998a35c11a7e0c89688d539a48b8d79230cc5af394b1ef4fb4c9bab8a5936`（17949 B） | 未变 |

上表是 2026-10-27 13:56:13 的时点记录，不是当前状态：14:00:25 另一会话再次改写该文件，现为 `b878d015c3e54c15a40ebfe601a83a97b574dbd082c16464bd0f63ab556144ea`（17 368 B，192 行）；脚本仍为 `262998a35c…`（17 949 B）。上文「body 182 行」同样只对该时点成立。引用「修复后」哈希前先重测当前值。

## 已核实 / 推断 / 未验证

- 已核实：上表 8 项运行、RC、键集、复放令牌、两个文件哈希与 QA 计数，均来自会话工具输出。
- 人工推断：两次 `generated` 相同（同秒）时的 `window < 1 s`；脚本时间戳精度为秒，未直接观测到同秒实例。
- 未验证：并发会话写入窗口、其他操作系统或 shell、脚本层的根一致性防护（用户选择不加）。

## 边界

- 本案例只证明「文档修复 + 复放」流程，不证明脚本行为正确或契约设计合理。
- 案例中的键集与错误串属于 `inventory-installed-skills` 的实测值；换目标 Skill 必须重测，不能照搬。
