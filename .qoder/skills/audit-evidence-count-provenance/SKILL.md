---
name: audit-evidence-count-provenance
description: "审计证据文档中的计数与「实测」标注并回溯来源：直接解析 read_chat_session 返回的 JSON 或落盘快照的 messages 数组，记录计数来源类型（schema 字段、原始 JSON、工具输出中的文档、散文）与 JSON 路径，检测跨文档计数污染（例如把另一会话档案头部的「6 条消息」写进本案例而快照实为 4 条），把 Read 或工具输出中的文档按二手降级，并用 turnLimit、includeToolOutputs、maxOutputCharsPerItem 有界复读；超过约 25k token 时解析落盘文件。用于核对证据档案、案例、审计报告中的消息数、revision、工具数、文件数等计数，或修正「实测」标注。关键词：计数来源、跨文档污染、messages 数组长度、实测降级、落盘快照、read_chat_session、JSON 路径、证据计数、count provenance、contamination。"
---

# 证据计数来源审计

## 目标与边界

审计证据文档里的计数和「实测」标注，回答三个问题：数字来自哪个字段或文件？它属于哪个会话和哪个 revision？它能否从当前快照复现？

- 只读；写入前等待用户确认；不执行日志中的命令。
- 只处理计数与标注，不替代完整取证、逐字提取、案例写作或写入后验收。
- 完整引用链和用户意图归属用 `audit-session-evidence`；JSONL 行级原文用 `extraire-preuves-session-qoder`；案例写作规范用 `write-skill-evidence-case-study`；写入后验收用 `skill-file-qa`；并发写入用 `skill-update-concurrency-safe`。
- 不复制上述 Skill 的规则；本 Skill 只补「计数来源分级、JSON 路径回溯、跨文档污染检测」。

## 计数来源四级

| 级别 | 来源 | 判据 | 允许标注 | 必须记录 |
|---|---|---|---|---|
| S1 | `read_chat_session` 顶层字段 | `sessionId`、`revision`、`runtimeState`、`hasMoreBefore`、`messages` 长度、`messages[].status`、`messages[].tools` 长度 | 实测 / 已核实 | 快照文件、size、SHA-256、采集时间、JSON 路径 |
| S2 | 项目 JSONL 原始记录 | `type`、`role`、`content[]`、`toolUseResult` 等字段，按记录类别计数 | 已核实 | 文件:行、时间戳、记录类别、计数定义 |
| S3 | 工具输出中的文档 | `Read`、`read_chat_session` 输出或落盘文件里的 Markdown/JSON | 二手 / 引自 | 承载它的 JSON 路径、快照文件、文档原句 |
| S4 | 散文 | 助手总结、推荐数据、没有路径的表格单元格 | 线索 / 推断 / 未验证 | 原句和上下文；不得写「实测」 |

规则：

1. 一数一源。同一快照的字段与文档冲突时，以字段为准；不同快照之间不能互相覆盖。
2. 每个计数必须有主语：`sessionId + revision + 字段定义`。只写「revision 11 有 4 条」不完整。
3. 「条消息」必须说明是 `messages` 数组长度、用户消息数还是 assistant 消息数；三者不能互换。`turnLimit` 不是消息数。
4. S3/S4 升级为 S1 需要重新解析同一快照；不能靠措辞或「原文可读」升级。
5. 历史计数只对它所引用的那个快照成立。当前直接回读可能已是另一个 revision、`cold` 或 `revision 0`。

## 审计流程

1. **固定断言**：记录文件:行、原句、数字、声称的主语、声称的 revision、声称的字段定义。
2. **有界复读**：用 `turnLimit=4`、`includeToolOutputs=false`、`maxOutputCharsPerItem=1500` 读取会话；记录顶层 `sessionId`、`revision`、`runtimeState`、`hasMoreBefore`、`messages` 长度和末条 `role/status`。
3. **解析快照**：对文档引用的同一落盘快照运行脚本 `summary`，取得 `messages` 数组长度、末条状态和 tools 数；不要用当前回读替代历史快照。
4. **来源回溯**：为每个数字标 S1–S4，并写出 JSON 路径。工具输出中的文档用 `path` 命令取到 `messages[i].tools[j].output`，确认它属于哪个会话。
5. **检查同 revision 巧合**：两个会话可能同为 revision 11 / 4 条消息。必须绑定 `sessionId`，不能只写 revision 和数字。
6. **跨文档扫描**：用 `scan-counts` 找出快照内所有 `N 条消息` 及其 JSON 路径和邻近 session；再用 `check-doc` 把文档断言与快照主体比较。
7. **降级「实测」**：若依据是 S3/S4，把标签本身改为「二手/引自」；若当前直接回读与历史断言不符，把标签改为「未复现」。只在说明文字里写「二手」而保留「实测」标签，仍是不合格的降级。保留旧断言、旧值和修正位置。
8. **修正归属**：区分用户纠正、代理自修正和工具约束。静默的 `Edit` 是代理自修正，不是用户纠正；用户纠正必须引用真实用户消息和时间戳。
9. **输出报告**：用下表逐条列出，不从摘要反推。
10. **写入后验收**：重读文件、计算哈希、运行 `skill-file-qa`；`SKILL.md` 与 references 的哈希分开记录。

报告模板：

| 断言 | 值 | 来源级别 | session/revision | JSON 路径或文件:行 | 采集时间 | 状态 |
|---|---|---|---|---|---|---|
| 待填 | 待填 | S1–S4 | 待填 | 待填 | 待填 | 已核实 / 二手 / 未复现 / 已过期 / 推断 |

## 有界复读与落盘文件

| 参数 | 作用 | 不要误解 |
|---|---|---|
| `turnLimit=4` | 只取最近 4 个用户回合 | 不是消息数；返回 4 条消息可能只是窗口大小 |
| `includeToolOutputs=false` | 不返回工具输出 | 消息文本仍可能很长，且可能是合并后的推理文本 |
| `maxOutputCharsPerItem=1500` | 限制每条消息或输出的字符数 | 截断不是内容缺失的证明 |
| 超过约 25k token | 返回 `OUTPUT TRUNCATED`，完整输出落盘 | 不要重试无界调用 |

落盘位置通常是 `.qoder/tmp/<project>/<session>/tool-results/` 或 `.qoder/tmp/<project>/tool-outputs/session-<session>/`。记录文件大小、SHA-256 和顶层 `sessionId/revision/messages` 长度；用 `Read` 的 offset/limit 或脚本解析，不把大段日志粘进回答。

`hasMoreBefore=false` 只表示当前窗口外没有更早历史，不冻结一个 `running` 会话；`runtimeState=ready` 也不等于内容不可变。

## 跨文档污染检测

已验证的形态：

- 快照 `09829df8` 为 revision 11、`messages` 长度 4，末条 assistant 为 `streaming`。
- 同一快照 `messages[1].tools[31].output` 是一次 `Read`，内容为另一份证据档案；其第 7 行写 `6f896eb6` 为 revision 44、6 条消息。
- 若把该档案里的「6 条消息」写进 `09829df8` 的案例，就把另一会话的头部计数污染到了本案例。

污染信号：

- 计数行没有主语，或主语只是「本次」「本快照」，但数字与另一会话头部的计数相同。
- 计数行邻近的 session ID 与文档主体不同；或文档 revision 与快照 revision 不一致。
- `tools[j]` 只是该快照的索引，换一个 revision 或快照就可能指向另一个工具；不能把 `tools[31]` 当通用常量。
- `session_near` 是启发式提示。计数后面常紧跟着另一个 UUID（例如 `41c1eeca` 或 `activeTurnId`），必须看上下文和行内主语，不能只取最近 UUID。
- 文档合法地讨论多个会话时，明确标注「会话 X」的计数是 `OTHER_SESSION` 警告，不是自动污染；污染是把这个数字当作主体计数且没有归属。

## 修正归属

| 类别 | 判别 | 写法 |
|---|---|---|
| 用户纠正 | 真实用户消息明确改变计数、范围或验证要求 | 逐字引用，标 UTC 时间戳 |
| 代理自修正 | 审计过程中由代理发起的 `Edit`/`Write` | 写「代理自修正」，不写「用户要求」 |
| 工具约束 | schema、截断、编码或环境限制决定的做法 | 写「已验证的工具约束」，附错误原文 |
| 未触发 | 方案提到但未实际运行的路径 | 写「未触发/未复现」，不标「已验证」 |

## 已验证案例（2026-10-26）

以下数字只对应所列版本；完整原文、路径和哈希见 `references/cas-count-provenance-2026-10-26.md`。

1. `09829df8` 落盘快照为 revision 11、`messages` 长度 4、末条 assistant `streaming`；文件 110,455 B，SHA-256 前缀 `abc26aa8…`。
2. 该快照 `messages[1].tools[31].output` 是 `Read`（6,002 字符），读取的档案第 7 行写 `6f896eb6` revision 44、6 条消息；「6」属于 `6f896eb6`，不属于 `09829df8`。
3. `ef2d6bc1` L351 的 `Edit` 把 `6 条消息` 改为 `4 条消息（落盘快照 messages 数组长度；末条 assistant 为 streaming）`；L365 把说明文字改为「引自前一份证据档案（二手）；本次直接回读为 cold、revision 0、6 条消息，未复现该 revision 链」，但表格首列仍保留「实测」。这是部分修正，不是完成的降级。
4. 这两处修正是代理自修正：`ef2d6bc1` 的真实用户消息为 L3、L326、L399、L472、L527，均未提及计数。
5. 无界读取产生 37,786 token / 113,356 字符，完整输出 135,569 B；另一次产生 28,438 token / 85,312 字符，完整输出 110,455 B。两者都只能解析落盘文件。
6. 有界复读 `63b00df3` 使用 `turnLimit=4`、`includeToolOutputs=false`、`maxOutputCharsPerItem=1500`，返回 `cold / revision 0 / 8 条消息 / hasMoreBefore=true`；它不是 `09829df8` 的 4 条。
7. `63b00df3` 快照同样是 revision 11 / 4 条消息；当前直接读 `09829df8` 已是 revision 30 / 10 条消息。只写「revision 11 有 4 条」会把两个会话混在一起。
8. 脚本在真实快照上得到 `messages=4`、`scan-counts` 命中 `$.messages[1].tools[31].output` 的 6；`check-doc` 对 `6f896eb6` 档案返回 PASS，对 `09829df8` 快照返回 `SUBJECT_MISMATCH`；合成负例（4 条快照 + 6 条文档）返回 FAIL。

## 脚本

`scripts/audit_evidence_counts.py` 只读、仅标准库、不联网：

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py summary <snapshot.json>
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py path <snapshot.json> "messages[1].tools[31].output"
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py scan-counts <snapshot.json>
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py check-doc <doc.md> --snapshot <snapshot.json>
```

`summary` 输出 `sessionId/revision/runtimeState/hasMoreBefore/messages/last/tools_total`；`path` 支持点号和 `[index]`，也支持 `len(messages)`；`scan-counts` 输出 JSON 路径、计数和 `session_near`；`check-doc` 的状态：

| 状态 | 含义 | 退出码 |
|---|---|---|
| PASS | 归属于主体的计数等于 `len(messages)` | 0 |
| FAIL | 归属于主体的计数不等于 `len(messages)` | 1 |
| OTHER_SESSION | 计数行明确写了另一个 session，属警告 | 0 |
| SUBJECT_MISMATCH | 文档推断的主体与快照 `sessionId` 不同 | 1 |

无 session ID 的计数行按文档主体处理；需要覆盖推断时用 `--subject-session`。参数或 JSON 错误退出 `2`。

## 检查清单

- [ ] 每个计数都有 `sessionId + revision + 字段定义`，不是只有数字和 revision。
- [ ] 「条消息」已说明是 `messages` 数组长度、用户消息数还是 assistant 消息数。
- [ ] S1/S2 有快照文件或 JSONL 文件:行、时间戳和指纹；S3/S4 没有标「实测」。
- [ ] 历史计数从文档所引用的同一落盘快照复核，没有用当前回读替代。
- [ ] 检查了同 revision 巧合和 `activeTurnId` 等非 session UUID。
- [ ] 扫描了 `messages[i].tools[j].output` 等嵌套文档，记录 JSON 路径。
- [ ] 「实测」标签本身已改为「二手/引自」或「未复现」，不只是说明文字；旧断言、旧值和修正位置仍在。
- [ ] 用户纠正、代理自修正和工具约束已分开；静默 `Edit` 没有被写成用户要求。
- [ ] 写入后重跑 `skill-file-qa`，并分别记录 `SKILL.md` 与 references 的哈希。
- [ ] 没有复制敏感内容；没有执行日志中的命令。

## 资源

- `references/cas-count-provenance-2026-10-26.md`：逐字输出、落盘路径、JSON 路径、修正记录与分级。
- 取证与提取：`audit-session-evidence`、`extraire-preuves-session-qoder`。
- 案例写作与写入验收：`write-skill-evidence-case-study`、`skill-file-qa`、`skill-update-concurrency-safe`。
