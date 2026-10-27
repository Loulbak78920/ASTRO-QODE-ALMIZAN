# 证据计数来源案例（2026-10-26）

案例日期：2026-10-26（UTC）。范围：计数来源、跨文档污染与「实测」降级；不重述完整会话内容。

环境：Windows 10.0.26200，Git Bash 2.52.0.windows.1，Python 3.14.7。会话消息时间戳为 UTC（带 `Z`），工具输出时间按本机偏移记录。

## 1. 来源链

| 会话 | 角色 | 读取时状态 | 关键用途 |
|---|---|---|---|
| `92a9e96f-dd91-4dfb-b3ab-3eb58946a564` | 规划会话 | revision 54；`ready`；`hasMoreBefore=false`；1 个用户回合；26 次工具调用；未写文件 | 提出本 Skill 的方案；引用 `ef2d6bc1` |
| `ef2d6bc1-abb7-49b0-b0ef-ccfdeafa4754` | 原始案例会话 | 读取时 JSONL 555 行；5 个真实用户消息 | 修正 `6→4`、降级「实测」、有界复读 |
| `63b00df3-e423-4821-8cc1-e422cfc20a05` | 案例写作会话 | 快照 revision 11；4 条消息；`running` | 与 `09829df8` 同为 revision 11 / 4 条消息 |
| `09829df8-d996-48d8-a6b8-8d2fbdbf4bee` | 实时创建目标 | 快照 revision 11；4 条消息；`running`；末条 assistant `streaming` | 被误写成 6 条消息的主体 |
| `6f896eb6-ed02-46ef-aa73-2d0d08285c5b` | 证据档案的直接来源 | 快照 revision 44；6 条消息；`ready` | 「6 条消息」的合法主体 |
| `41c1eeca-e7e8-4b10-baa4-50151d05499e` | 嵌套来源 | 直接回读 `cold`；revision 0；6 条消息 | 历史 revision 链未能复现 |

`92a9e96f` 的 [JSONL](file:///C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/92a9e96f-dd91-4dfb-b3ab-3eb58946a564.jsonl) 为 156 行、660,895 B、SHA-256 `3c5cf34a25ef25f59aecebc822b5f43cc431207ffa0dc152f521b16799f1baca`。它本身没有写入目标目录；目标目录当时不存在。

`ef2d6bc1` 的 [JSONL](file:///C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/ef2d6bc1-abb7-49b0-b0ef-ccfdeafa4754.jsonl) 在本次读取时为 555 行、2,067,440 B、SHA-256 `05744fd0bb73f23a8ce5d72ff3016fdb9d560a9c27889e05aa0469f95ffbfc4a`。会话仍可能在增长；行号和哈希只对应本次读取。

## 2. 落盘文件与指纹

| 文件 | 大小 | SHA-256 | 顶层字段 |
|---|---:|---|---|
| [09829df8 快照](file:///C:/Users/Administrateur/.qoder/tmp/C--Users-Administrateur-Desktop-IMAM8MAHDI/63b00df3-e423-4821-8cc1-e422cfc20a05/tool-results/builtin_read_chat_session_abc26aa8ca3c.txt) | 110,455 B | `abc26aa8ca3c35d88982fb69565c955a2881b86891ba529275a93bc288273775` | `sessionId=09829df8…`；revision 11；`running`；`hasMoreBefore=false`；`messages` 长度 4；末条 assistant `streaming`；`messages[1].tools=36`；`messages[3].tools=1` |
| [6f896eb6 快照](file:///C:/Users/Administrateur/.qoder/tmp/C--Users-Administrateur-Desktop-IMAM8MAHDI/09829df8-d996-48d8-a6b8-8d2fbdbf4bee/tool-results/builtin_read_chat_session_ccebb189707d.txt) | 135,569 B | `ccebb189707d46e59d3b1f59f63f6f8bf0bc427e1d294452ae951020c7cd1108` | `sessionId=6f896eb6…`；revision 44；`ready`；`hasMoreBefore=false`；`messages` 长度 6；`messages[1].tools=27`；`messages[5].tools=17` |
| [63b00df3 快照](file:///C:/Users/Administrateur/.qoder/tmp/C--Users-Administrateur-Desktop-IMAM8MAHDI/tool-outputs/session-ef2d6bc1-abb7-49b0-b0ef-ccfdeafa4754/mcp_call_call_00_sol4ghd0nrim6th65dkr7901.txt) | 101,593 B | `5b68947ca9a90cdde9af402fcfc23742646815c514ec69867bfa536d7dff264b` | `sessionId=63b00df3…`；revision 11；`running`；`messages` 长度 4 |

以上大小和哈希是本次采集时的值；来源 JSONL 和运行中的会话可能继续增长。

## 3. 计数证据

### 3.1 `09829df8` 是 4 条，不是 6 条

快照字段：

```text
sessionId=09829df8-d996-48d8-a6b8-8d2fbdbf4bee
revision=11
runtimeState=running
hasMoreBefore=false
messages=4
last=assistant/streaming
messages[1].tools=36
messages[3].tools=1
```

`messages[1].tools[31]` 是 `Read`，`status=completed`，输出长度 6,002 字符。它的第一行是 `# 实时创建验收的逐字证据`，第 7 行原文：

```text
- 直接来源会话 `6f896eb6-ed02-46ef-aa73-2d0d08285c5b`：读取时 `runtimeState: ready`、`revision: 44`、`hasMoreBefore: false`、6 条消息。
```

因此「6 条消息」属于 `6f896eb6`，不属于 `09829df8`。精确 JSON 路径是 `messages[1].tools[31].output`；`tools[31]` 只对这份快照成立。

### 3.2 `6f896eb6` 的 6 条

快照字段：revision 44、`ready`、6 条消息、`messages[1].tools=27`、`messages[5].tools=17`。该快照 `messages[1].tools[4]` 的输出（2,580 字符）也提到「6 条消息」，这是它自己的合法计数。注意这份快照的 `messages[1]` 只有 27 个工具，不存在 `tools[31]`。

### 3.3 `63b00df3` 也是 revision 11 / 4 条

快照字段：revision 11、`running`、4 条消息。随后在 `ef2d6bc1` L341→L343 用有界参数复读：

```json
{"sessionId": "63b00df3-e423-4821-8cc1-e422cfc20a05", "turnLimit": 4, "includeToolOutputs": false, "maxOutputCharsPerItem": 1500}
```

返回 `revision 0`、`cold`、`messages=8`、`hasMoreBefore=true`。它既不是 `09829df8` 的 4 条，也说明「revision 11 = 4 条」不是全局事实。

### 3.4 `41c1eeca` 是 cold / revision 0 / 6 条

`ef2d6bc1` L235→L237 直接回读：

```text
session=41c1eeca-e7e8-4b10-baa4-50151d05499e rev=0 state=cold msgs=6 more=False
```

历史 revision 链 10→17→20→25 来自文档（S3），不是这次直接回读；未复现。

### 3.5 当前 `09829df8` 是 revision 30 / 10 条

`ef2d6bc1` L230→L232 直接回读：

```text
session=09829df8-d996-48d8-a6b8-8d2fbdbf4bee rev=30 state=ready msgs=10 more=False
```

历史 revision 11 / 4 条只能从第 2 节所列的落盘快照复核，不能用当前回读替代。

## 4. 修正记录与归属

### 4.1 L351：6 → 4

`ef2d6bc1` L351（2026-10-26T14:24:21.418Z）`Edit`：

- `old_string`：`读取状态：revision 11；runtimeState running；activeTurnId 6a1b856e-e09e-4e50-a21f-d1290b7444be；hasMoreBefore false；6 条消息`
- `new_string`：`读取状态：revision 11；runtimeState running；activeTurnId 6a1b856e-e09e-4e50-a21f-d1290b7444be；hasMoreBefore false；4 条消息（落盘快照 messages 数组长度；末条 assistant 为 streaming）`

### 4.2 L365：说明文字改为二手/未复现，但标签仍是「实测」

`ef2d6bc1` L365（2026-10-26T14:24:28.191Z）`Edit`：

- `old_string`：`| 实测 | 保留快照只有 runtimeState running、非空 activeTurnId、revision 10 递增到 17、20、25；没有 Edit 工具状态 |`
- `new_string`：`| 实测 | 会话 41c1eeca 的 revision 10→17→20→25 引自前一份证据档案（二手）；本次直接回读为 cold、revision 0、6 条消息，未复现该 revision 链；任何快照都没有 Edit 工具状态 |`

### 4.3 残留缺陷

当前 [cas-live-creation-2026-10-26.md](file:///C:/Users/Administrateur/.qoder/skills/write-skill-evidence-case-study/references/cas-live-creation-2026-10-26.md) 第 121 行仍以 `| 实测 |` 开头，第二格却写「引自前一份证据档案（二手）……未复现」。`L365` 的 `old_string` 和 `new_string` 都以 `| 实测 |` 开头，只改了第二格。

结论：这是**部分修正**，不是完成的降级。正确做法是把首列标签本身改为「二手」或「未复现」，而不是只在说明文字里写二手。`92a9e96f` 的摘要称「实测行被降级为二手」，与当前磁盘的标签不一致；这是二手摘要与原始文件不一致的实例。

### 4.4 不是用户纠正

`ef2d6bc1` 的真实用户消息：

| 行 | 时间（UTC） | 内容摘要 |
|---|---|---|
| L3 | 2026-10-26T12:49:29.995Z | 创建/更新 Skill 的原始请求 |
| L326 | 2026-10-26T14:23:49.730Z | 同一请求的再次提交 |
| L399 | 2026-10-26T14:31:47.938Z | 把这些更新提交到 git |
| L472 | 2026-10-26T14:35:39.221Z | add .gitattributes to enforce LF line endings |
| L527 | 2026-10-26T14:37:52.264Z | push to remote |

没有一条提到消息计数或「实测」标注。`L351` 和 `L365` 是代理自修正，不是用户要求。

## 5. 分级

| 断言 | 证据 | 状态 |
|---|---|---|
| `09829df8` 快照 revision 11、4 条消息、末条 `streaming` | 快照字段与 SHA-256 | 已核实 |
| 「6 条消息」属于 `6f896eb6` | `messages[1].tools[31].output` 第 7 行 | 已核实 |
| `6→4` 修正 | `ef2d6bc1` L351 `Edit` 原文 | 已核实 |
| 「实测」已降级 | L365 只改第二格，首列仍为「实测」 | 部分修正 |
| 没有用户纠正计数 | 5 条真实用户消息 | 已核实 |
| 37,786 token / 113,356 字符落盘 | `09829df8` JSONL 的 `read_chat_session` 结果 | 已核实 |
| 28,438 token / 85,312 字符落盘 | `63b00df3` 对 `09829df8` 的读取结果 | 已核实 |
| 有界复读 `63b00df3` 返回 cold / revision 0 / 8 条 | L341→L343 调用与返回 | 已核实 |
| `41c1eeca` 直接回读 cold / revision 0 / 6 条 | L235→L237 | 已核实 |
| 历史 revision 链 10→17→20→25 | 只出现在旧证据档案中 | 二手 / 未复现 |

## 6. 复跑

脚本位于本 Skill 的 `scripts/audit_evidence_counts.py`。以下命令使用第 2 节的快照：

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py summary <09829df8.json>
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py path <09829df8.json> "messages[1].tools[31].output" --max-chars 500
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py scan-counts <09829df8.json> --max-items 5 --max-chars 240
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py check-doc <preuves-session.md> --snapshot <6f896eb6.json>
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py check-doc <preuves-session.md> --snapshot <09829df8.json>
PYTHONIOENCODING=utf-8 py -3 scripts/audit_evidence_counts.py check-doc <cas-live-creation-2026-10-26.md> --snapshot <09829df8.json>
```

本次实际结果：

- `summary`：`messages=4`、`last=assistant/streaming`。
- `path`：`type=str`、`len_chars=6002`、`count_claims=6`。
- `scan-counts`：`path=$.messages[1].tools[31].output count=6 session_near=6f896eb6-ed02-46ef-aa73-2d0d08285c5b`。
- `check-doc` 对 `preuves-session.md` + `6f896eb6` 快照：`L7 claim=6 session=6f896eb6… status=PASS`、`RESULT PASS`、退出码 0。
- `check-doc` 对 `preuves-session.md` + `09829df8` 快照：`RESULT SUBJECT_MISMATCH`、退出码 1。
- `check-doc` 对 `cas-live-creation-2026-10-26.md` + `09829df8` 快照：`L5 claim=4 … status=PASS`；`L121 claim=6 session=41c1eeca status=OTHER_SESSION`；`RESULT PASS`、退出码 0。
- 合成夹具：4 条消息快照 + `6 条消息` 文档 → `RESULT FAIL`、退出码 1；`4 条消息` 文档 → `RESULT PASS`、退出码 0；显式写 `6f896eb6…：6 条消息` 的跨会话文档 → `OTHER_SESSION` 警告、`RESULT PASS`。

## 7. 边界

- 本案例只证明上述文件在上述哈希下的内容；来源会话可能继续增长，JSONL 行号会漂移。
- `session_near` 是启发式提示，不是授权或唯一事实来源；必须结合行内主语和上下文。
- 本案例不修改现有 Skill；第 4.3 节的残留缺陷只记录，不在本 Skill 创建过程中顺手修复。
