---
name: diagnostiquer-wait-chat-sessions-introuvable
description: "当 wait_chat_sessions 对 read_chat_session 仍可读取的会话返回 is_error「等待的 ChatSession 不存在：<id>」时，把该错误判为观察通道故障而不是会话已结束：用 read_chat_session 记录 runtimeState、activeTurnId、queuedTurnCount、pendingInteractionCount、revision 与 hasMoreBefore，先排除「目标就是当前会话」的自排除解释，再用连续 4 次、间隔 6 秒的全文件 size/mtime/SHA-256 指纹门禁判断采样窗口内是否仍有写入；只有 cold 且 activeTurnId=null 与指纹一致同时成立才采纳现有字节或做最小 Edit，写入者仍活动时零写入并报告 STOP；不把稳定当结束、不跨状态或跨 turnLimit 比较 revision 与 hasMoreBefore、不把循环末尾命令的退出码当门禁结果。通道失效或快照只剩人工回合时，证据只从被引用的项目 JSONL 取：仅在 <sessionId>.jsonl 中按精确 token 计数（0=ABSENT），N>0 按顶层 type 分组，只有 type=user 且 origin.kind=human、humanInput 非空、timestamp 非空、无 tool_result 的记录是事实载体；file-history-snapshot 顶层 timestamp 与 sessionId 为 null，snapshot.timestamp 只重复同一时刻，不计入；引用写路径、行号与 SHA-256。用于 wait 返回不存在、等待立即失败、read 可读而 wait 不可观察、cold 不出现、冷快照只有一条消息、grep 计数 5 实为 1 条、token 仅在讨论会话中大量命中、并发写入者门禁、STOP 判定等场景；不替代目标出现后的活性分级（audit-skill-during-live-creation）、来源更新采纳（adopt-source-session-update）、全册证据裁决（adopter-skill-concurrent-apres-quiescence）或通用采样（skill-update-concurrency-safe）。"
---

# 诊断 wait_chat_sessions 的「不存在」错误

## 目标

区分两种完全不同的状态：观察通道失效，和会话已经结束。`wait_chat_sessions` 报「等待的 ChatSession 不存在」时，只能得出「这个通道不能观察该会话」，不能得出「该会话已结束」，更不能据此写入它正在写的文件。本 Skill 给出替代证据链，并规定唯一的写入门槛。

## 何时使用

- `wait_chat_sessions` 返回 `is_error`，文本为 `等待的 ChatSession 不存在：<id>`；
- 同一 `sessionId` 的 `read_chat_session` 仍能返回快照（`running`、`ready`、`cold` 均可）；
- 等待应立即返回，而目标看起来仍在写文件；
- 需要决定「现在能不能编辑目标目录」。

不适用：wait 正常返回 `timeout`、`turn_completed`、`needs_attention`，见 `audit-skill-during-live-creation`；已确认要采纳来源会话的改动，见 `adopt-source-session-update`；只做通用双采样，见 `skill-update-concurrency-safe`。

## 不可协商约束

1. **wait 的错误是通道故障，不是终点。** `is_error` 加「不存在」不等于 `cold`，不等于回合结束，不等于可以写入。
2. **活性以 `read_chat_session` 为准。** 记录 `runtimeState`、`activeTurnId`、`queuedTurnCount`、`pendingInteractionCount`、`revision`、`hasMoreBefore`、`turnLimit`、`status`；缺一项就不能判 `QUIESCENT`。
3. **先排除自排除。** wait 明确禁止包含当前会话。只有目标 ID 等于当前会话，`not found` 才可能只是自排除；用快照里的用户回合（消息 id 与文本）与当前回合比对，不凭直觉。
4. **稳定不等于结束。** 连续 4 次指纹一致只说明采样窗口内没有写入；它不能替代 `runtimeState`。
5. **写入门槛是合取。** 只有 `cold` 加 `activeTurnId: null` 加连续 4 次指纹一致同时成立，才允许采纳现有字节或做最小 Edit。任一不满足，零写入并报告 `STOP`。
6. **字段不可跨窗口比较。** `revision` 会在状态切换时回落（实测 `running` 21 到 `cold` 0）；`hasMoreBefore` 随 `turnLimit` 变化（实测 `turnLimit` 2 到 1 时 false 到 true）。同一 `turnLimit` 的连续读取才有比较意义。
7. **退出码必须显式。** 不要在命令末尾放测试表达式：`[ "$i" -lt 4 ] && sleep 6` 会让整个循环以 1 结束，把「稳定」误报成「失败」。用 `scripts/attendre_stabilite.py` 的 0/1/2，或显式 `exit 0`。
8. **观察通道恢复后交回既有流程。** 写入许可后，仍按 `audit-skill-during-live-creation` 的活性三态与 `skill-file-qa` 的验收执行；本 Skill 不重新定义它们。

## 诊断流程

### 1. 固定参数复现并记录

```text
mcp_get  wait_chat_sessions, read_chat_session   # 先核对实时 schema
mcp_call wait_chat_sessions {sessionIds:[<id>], timeoutMs:<与失败时相同>}
mcp_call read_chat_session  {sessionId:<id>, turnLimit:<固定值>, includeToolOutputs:false}
```

先按失败时的参数复现（本案例为 `timeoutMs: 60000`）。只想立即取状态时可用 `timeoutMs: 0`，但要如实记录它返回的是错误还是状态快照，不假定两者等价。

记录：错误原文、`is_error`、调用到返回的耗时（立即返回还是等到超时）、快照全部状态字段。

### 2. 判定错误类别

| 观察 | 判定 | 动作 |
|---|---|---|
| 立即 `is_error`，文本含「不存在」或 `not found` | `CHANNEL_DOWN` | 进入第 4 步替代门禁；零写入 |
| 等到 `timeoutMs` 才返回 `timeout` | `WAIT_TIMEOUT` | 走 `audit-skill-during-live-creation` |
| 目标 ID 与当前会话相同 | `SELF_EXCLUDED` | 换一个观察对象；本错误无信息量 |
| `read_chat_session` 也报未知会话 | `UNKNOWN_SESSION` | 核对 ID；不猜状态 |
| 快照 `cold` 加 `activeTurnId: null` | `ENDED_CONFIRMED` | 仍需指纹门禁：可能有其他写入者 |

### 3. 排除自排除

从快照 `messages` 取最近用户回合的 `id` 与 `text`，与当前会话的用户回合比对。若目标快照里出现当前回合，说明 ID 指向自己；否则 `not found` 是通道问题。不要用「wait 禁止自包含」直接推断目标就是自己。

### 4. 替代门禁：全文件指纹

```bash
py -3 -B scripts/attendre_stabilite.py "<目录>" --samples 4 --interval 6
echo "GATE_RC=$?"
```

- `0`：采样窗口内全文件（相对路径、size、mtime_ns、SHA-256）连续一致；
- `1`：有文件变化、出现或消失（含采样中读取失败）；
- `2`：用法或环境错误（目录不存在、参数非法）。

输出为纯 ASCII，可直接放进报告；`-B` 避免缓存。采样期间出现 `*.tmp.*`、锁文件或备份文件时，该轮作废并重采。mtime 纳入指纹，因此内容不变但被重写也会报 `CHANGED`。

### 4bis. 替代证据：项目 JSONL（只读）

`wait` 报「不存在」而 `read_chat_session` 仍返回 `cold` 时，快照可能只有人工回合：实测 `ce25942a` 为 `cold`、`revision 0`、`hasMoreBefore=false`、仅 1 条消息，而它的 JSONL 有 211 行、86 条 assistant、35 次 `tool_use`。**快照没有工具证据，不等于会话没有证据。**

1. 日志本体是项目目录下的 `<sessionId>.jsonl`，完整路径：

```text
C:\Users\<user>\.qoder\projects\<project-slug>\<sessionId>.jsonl
```

同名 `<sessionId>/` 文件夹（`state.json`、`compression-v2`）不是日志；`items` 是加密值，不要解码或引用。

2. 读取前冻结字节数、行数、mtime、SHA-256；读取后再算一次，任一变化就重新计数。
3. 只在**被引用**的 JSONL 里对精确 token 计数（`raw.count(token)` 或 `grep -F -c`）；`0` 判 `ABSENT`。
4. `N > 0` 时逐行取顶层 `type` 分组后再报数；总数不是证据。
5. 事实载体是 `type=user`、`message.role=user`、`origin.kind=human`、`humanInput.text` 非空、`timestamp` 非空、无 `tool_result` 的记录。`file-history-snapshot` 不是载体：顶层 `timestamp` 与 `sessionId` 均为 `null`，`snapshot.timestamp` 只是重复被快照消息的时刻。
6. 用讨论该文档的会话作反例：`00:55:43` 在 `ce25942a` 中命中 46 次、在 `e22fe088` 中 0 次；`00:55:48` 分别为 45 与 5。计错文件会虚高。
7. 引用写成 JSONL 路径 + 命中行号 + 字节数 + SHA-256，并给出载体记录的真实 `timestamp`；不要写「会话说」。
8. 本 Skill 只取证；改写包时转 `auditer-skill-cree-par-session-source`（单条证据修正）或 `adopter-skill-concurrent-apres-quiescence`（全册裁决）。

### 5. 回到会话状态作最终判定

| 快照状态 | 判定 | 写入 |
|---|---|---|
| `running` 或 `opening`，或 `activeTurnId` 非空 | `RUNNING` | 禁止；报告 `STOP` |
| `waiting-user` 且 `pendingInteractionCount ≥ 1` | `PAUSED` | 未确认不回复前禁止 |
| `ready` 加 `activeTurnId: null` 加指纹一致 | `QUIESCENT` | 仍需确认无其他写入者；按既有 Skill 处理 |
| `cold` 加 `activeTurnId: null` 加指纹一致 | `ENDED_CONFIRMED` | 允许采纳或最小 Edit |
| 状态字段缺失或自相矛盾 | `UNKNOWN` | 禁止；补采一次后仍缺失即 `STOP` |

### 6. 采纳或停止

- 采纳：重读全部文件，按最新字节定位缺陷，记录 size、mtime、SHA-256；只改缺口。
- 停止：报告 `STOP`，写明触发条件（哪个字段、第几次采样、哪个文件变了）与下一次检查时间。
- 写入后重跑 `skill-file-qa`，分别记录 `SKILL.md` 与参考文件的哈希；静态 PASS 不证明内容正确。

## 症状、原因、动作

| 症状 | 原因 | 动作 |
|---|---|---|
| wait 116 ms 返回「不存在」，read 仍 `running` | 观察通道不覆盖该会话 | 判 `CHANNEL_DOWN`；改用指纹门禁，不判结束 |
| wait 一直不返回 `cold` | `cold` 不是必经状态 | 用 `runtimeState` 与 `activeTurnId` 判活；`cold` 只作写入条件之一 |
| 4 次采样一致，但会话仍 `streaming` | 采样窗口可能落在两次写入之间；本案例稳定后另行确认 `cold` | 继续等待；稳定不等于结束 |
| 门禁命令 `Exit code 1` 但四行指纹相同 | 末尾测试表达式为假 | 改用显式退出码；不要把 rc 当结论 |
| `running` 时 `revision` 21，`cold` 时 0 | 状态切换重算 | 不跨状态比较 `revision` |
| `turnLimit` 2 到 1 后 `hasMoreBefore` false 到 true | 窗口大小改变 | 固定 `turnLimit` 再比较 |
| `cold` 后目标仍在变 | `cold` 只覆盖该会话 | 按其他写入者未知处理；继续采样 |
| 把 wait 错误当成「会话已删除」 | 未对照 read | 删除该结论；未验证的假设不入报告 |
| grep 计数 5，载体只有 1 条 | 4 条 `file-history-snapshot` 的 `snapshot.timestamp` 重复同一时刻 | 按顶层 `type` 分组；不要把 5 当事实条数 |
| 快照只有 1 条消息，JSONL 却有工具调用 | 快照只含人工回合，工具结果不在 `messages` | 用 JSONL 取证；不要判 `ABSENT` |
| 同一 token 在别的会话命中几十次 | 计到了讨论该文档的会话 | 只算被引用 JSONL，并给出两边对照数 |
| 命中行 `timestamp: null` | `file-history-snapshot` 无顶层时间 | 读它指向的人工记录的真实 `timestamp` |

## 报告模板

```text
CHANNEL: wait_chat_sessions -> is_error after <ms> ms: <原文>
SNAPSHOT: runtimeState=<...> activeTurnId=<...> revision=<...> hasMoreBefore=<...> turnLimit=<...>
SELF_EXCLUSION: ruled_out | possible (<依据>)
GATE: samples=4 interval=6s rc=<0|1|2> fingerprint=<12 hex>
DECISION: STOP | QUIESCENT | ENDED_CONFIRMED
WRITES: none | <files + sha256>
```

## 完成检查

- [ ] 记录了 wait 的错误原文与返回耗时，而不是只记「失败」。
- [ ] 同一 `sessionId` 的 `read_chat_session` 快照已记录全部状态字段与 `turnLimit`。
- [ ] 自排除解释已被证实或排除，并写明依据。
- [ ] 门禁结果为显式 0/1/2，没有把循环末尾表达式当结果。
- [ ] 写入前同时满足 `cold`、`activeTurnId: null`、连续 4 次一致。
- [ ] 报告区分 `CHANNEL_DOWN` 与 `ENDED_CONFIRMED`，未把前者写成后者。
- [ ] 未验证的假设（如 wait 的注册或工作区范围）标为未验证。
- [ ] 通道失效后已定位 `<sessionId>.jsonl` 本体，并与同名伴生文件夹区分。
- [ ] 计数前后记录字节、行数、mtime、SHA-256；只统计被引用文件。
- [ ] `N > 0` 已按顶层 `type` 分组，`file-history-snapshot` 未计入事实载体。
- [ ] 证据以 JSONL 路径 + 行号 + SHA-256 引用，未引用活会话。
- [ ] 写入后已重跑 `skill-file-qa` 并记录实际哈希。

## Provenance

- 来源会话 `e0d40f60-65c4-48f7-b589-fde72f210d2a`，2026-10-26T23:08:22Z 的用户回合（消息 `75b70544…`）。
- 23:15:14.210Z 调用 wait（`timeoutMs: 60000`），23:15:14.326Z 返回 `is_error`「等待的 ChatSession 不存在：`c7e3d5d5-efcd-4b9f-b9a6-c5d6e25c51ef`」；同目标 read 快照为 `running`、`revision 21`。
- 替代门禁：23:15:21.680Z 到 23:15:41.511Z，4 次采样、间隔 6 秒，指纹一致；rc=1 来自末尾 `[ "$i" -lt 4 ]` 为假。
- 23:15:46.878Z 读取为 `cold`、`activeTurnId=null`、`revision 0`、`hasMoreBefore=true`；随后才做 2 次最小 Edit，副本验收为 9 pass、0 fail、0 warn（`QA_RC=0`）。
- 逐字原文、命令与分类见 `references/cas-wait-introuvable-2026-10-27.md`。

### 通道失效后的 JSONL 取证（2026-10-28）

- 来源会话 `6135cdd8` 核实时，`wait_chat_sessions(ce25942a, timeoutMs 0)` 返回 `is_error`「等待的 ChatSession 不存在：ce25942a-4f7e-4720-909e-d0b81976ebe5」；`read_chat_session(ce25942a, turnLimit 2)` 为 `cold`、`revision 0`、`hasMoreBefore=false`、1 条消息，其 JSONL 有 211 行。
- 被引用的 `e22fe088` JSONL：1,493,251 B、408 行、SHA-256 `856799b5…269d`；`00:55:43` 0 次，`00:55:48` 5 次 = 第 117 行 `type=user`（`2026-10-28T00:55:48.734Z`，`origin.kind=human`，`humanInput.text=确认按上述 3 文件方案执行`）+ 第 140/175/280/293 行 `file-history-snapshot`（顶层 `timestamp=null`，`snapshot.timestamp` 重复同一时刻）。
- 对照：`ce25942a` JSONL 789,233 B、211 行；`00:55:43` 46 次、`00:55:48` 45 次。
- 命令、输出与未验证项见 `references/cas-jsonl-2026-10-28.md`。
