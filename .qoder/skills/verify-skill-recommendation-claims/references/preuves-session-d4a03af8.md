# 证据档案：会话 d4a03af8（2026-10-27）

来源会话 `d4a03af8-e000-40b8-881e-3d06a433eb50`，标题「创建可复用 Skill」。本档案支撑 SKILL.md 的三处新增规则：裸调用自取推荐、缓存快照新鲜度、`cold`/`revision=0` 复核。会话消息时间为 UTC，文件 mtime 为本地 `+01:00`。

## 快照

| 项 | 首次读取（本会话 14:07:48 本地 / 13:07:48Z） | 写前复读（约 14:10 本地，未落盘） | 验证期复读（14:13 本地，落盘） |
|---|---|---|---|
| `runtimeState` | `running` | `ready` | `running` |
| `revision` | 14 | 33 | 10 |
| `activeTurnId` | `fd343b85-0829-42c3-815e-67bfc41b39d9` | `null` | `f12979a2-b58a-437f-83de-aad83cc2c27d` |
| `pendingInteractionCount` | 0 | 0 | 0 |
| `hasMoreBefore` | `false`（`turnLimit=20`，窗口 12 条） | `true`（`turnLimit=2`，窗口 4 条） | `false`（`turnLimit=20`，窗口 18 条） |
| 最终回合 | `streaming`、正文 0 字符（"commit this change"） | completed（归档 commit、随后 `reload skills`） | `streaming`、正文 0 字符（"继续验证 inventory-installed-skills"） |

`revision` 不是单调计数器：同一会话在三次读取中为 14 → 33 → 10，其中 33 为 `ready`、10 为复启后的 `running`。跨读取只能比较时间，不能比较 revision 大小。

首次快照落盘：`C:\Users\Administrateur\.qoder\tmp\C--Users-Administrateur-Desktop-IMAM8MAHDI\00e06a34-7bc5-402a-8b1e-bbb0d81c4e96\tool-results\builtin_read_chat_session_7aacd7353bd6.txt`，147,827 B，14:07:48 本地；第三份落盘：同目录 `builtin_read_chat_session_5d77dc5de17e.txt`，201,398 字符，14:13 本地。

## 消息时间线（首次快照 12 条）

| # | role | UTC | status | tools |
|---|---|---|---|---|
| 0 | user | 12:44:57.993 | completed | —（首条任务 + `creer-skill-depuis-session-recommandee` 推荐 JSON） |
| 1 | assistant | 12:44:58.181 | completed | 47 个（`Skill`、`Bash`、`mcp_get`、`mcp_call`、`Read`、`Grep`、`Edit`、`AskUserQuestion`） |
| 2 | user | 12:59:21.480 | completed | —（`/skills reload`） |
| 3 | assistant | 12:59:21.480 | completed | `Read`、`Bash`、`Skill`、`Bash` |
| 4 | user | 13:02:58.395 | completed | —（`run the skill`） |
| 5 | assistant | 13:02:58.395 | completed | `Bash`、`Bash`、`mcp_get`、`mcp_call`、`Bash`、`Bash` |
| 6 | user | 13:04:35.066 | completed | —（`apply the one-line fix`） |
| 7 | assistant | 13:04:35.066 | completed | `Bash`、`Read`、`Edit`、`Edit`、`Bash` |
| 8 | user | 13:05:39.464 | completed | —（`/verify-skill-recommendation-claims`） |
| 9 | assistant | 13:05:39.464 | completed | `Skill`、`Bash`、`Bash`、`Bash`、`mcp_call` |
| 10 | user | 13:06:57.255 | completed | —（`commit this change`） |
| 11 | assistant | 13:06:57.255 | 首次读取时 `streaming`，正文 0；复读为 completed | 首次 `Read`、`Bash`、`Bash`；复读时 11 个 |

窗口内失败空回合 0、用户重发 0、成功写工具 8（`Edit`：`[1]` 6 次、`[7]` 2 次）。`SESSION_ZERO_WRITE=false`。

第三份快照扩到 18 条（`#0`–`#17`）：`[11]` 为完成态，新增 `[12]`/`[13]` `reload skills`、`[14]`/`[15]` `继续验证下一个技能`、`[16]`/`[17]` `继续验证 inventory-installed-skills`（`streaming`）。窗口不同，消息数不与前两份比较。

## 证据一：裸调用自取推荐

- `[4]` 与 `[8]` 都是裸调用，当前消息不含推荐 JSON；推荐对象来自本会话 JSONL `line=3`（`creer-skill-depuis-session-recommandee` / `create` / 1,351 字符）。
- `[5]` 报告：`冻结 line=3 chars=1351 no_lf=58534c2a… with_lf=ff6cb695…`，并写「执行完毕（只读，零写入）」。
- `[9]` 再次冻结同一行，tool 输出为 `JSON_CHARS=1351`、`SHA256_NO_LF="58534c2a5bb00a47fd44d49f0ed16fa5cda675ab3e4c6e983462d928d22cf5cd"`、`SHA256_WITH_LF="ff6cb695c6dd1389991cf69034c7cac60f60bc9aac232b5a565d2cf8cca65ffa"`，与 `[5]` 完全一致；报告末尾「尚未写入任何文件」。
- 结论：同一推荐在同一任务的多轮裸调用中可稳定复用同一行与双哈希；两轮均未写盘。

## 证据二：过期缓存快照

- `[9]` 原文：「`audit_recommendation.py` 未运行：唯一缓存的 `read_chat_session` 快照是 revision 12 / `running`（13:45），拿它做会话状态判定会误导」。
- tool 输出确认该缓存文件：79,716 B，mtime 13:45 本地，`sessionId a973aeef…`、`revision 12`、`runtime running`、`msgs 6`。
- 同一回合改为一次新鲜 `mcp_call`，返回 `runtimeState="cold"`、`revision=0`；报告据此写「来源会话现为 cold」。
- `audit_recommendation.py:232` 只把 `--session` 当作快照路径；`:339-343` 原样打印 `SESSION_REVISION`、`SESSION_RUNTIME_STATE`、`SESSION_ACTIVE_TURN` 等，不做新旧判断。因此「旧快照会误导」是可从代码推断的后果，本档案未实测一次错误判决。

## 证据三：cold / revision=0

- `[5]` 在 13:02Z 复读为 `a973aeef` revision 74 / `ready` / 最终回合 completed，据此把案例从 `PARTIAL` 建议改为 `FINAL`。
- `[7]` 应用该一行修改后跑 `skill-file-qa`：`RESULT PASS` 9/0/0、`Files (5)`、description 873、正文 265 行；新指纹 23,933 B / `4b5793b1e8d94980dcd4bec184f2c35c9cdb8970054625f41edac5356f38c06b`。
- `[9]` 复读同一会话为 `cold`、`revision=0`，并写「案例行记录的是 14:02 复读时的 revision=74 / ready，与 cold 不冲突，同属 FINAL」。cold 的 revision 0 不是历史回退。
- 因果边界：`FINAL` 的依据是 revision 74 / `ready`；cold 是升级后的复核，不是升级本身的依据。

## 本会话追加的只读复核

- 推荐冻结：本会话 `00e06a34…` JSONL `line=3`，985 字符，`SHA256_NO_LF=ac4e7f3cf3f1bc32884f0121d1a194c7a1173ec8ed32166a882b6d65dbd489b3`、`SHA256_WITH_LF=aad9b249183db4986c3f050760f2cf5d8d23fcff4eb01f6218a3ed749db81a19`；`--out` 文件 1,807 B，哈希等于 `no_lf`。
- `audit_recommendation.py`（`--session` 用首次快照）：`RESULT PASS`、`EXIT=0`；`TARGET_EXISTS=true`、`ACTION_CONFLICT=NONE`、`SCOPE=INSIDE`、`DUPLICATE_ROOTS=none`、`INSTRUCTION_RISK=none`；`SESSION_REVISION=14`、`SESSION_RUNTIME_STATE="running"`、`SESSION_FINAL_ASSISTANT_STATUS="streaming"`。
- 写前复读：`ready` / revision 33 / `activeTurnId=null`。最终回合自述归档到 `Loulbak78920/ASTRO-QODE-IMAM8MAHDI` 的 `a5f03a3`（5 文件包，`c29c8c3..a5f03a3`）。本会话未检查归档库，该提交与推送只作来源自述记录。
- 验证期复读：`running` / revision 10 / 活动回合 `f12979a2…`。同一会话三次读取的 revision 为 14 → 33 → 10，证明 revision 会随运行/复启重置，不能按大小判断新旧或回退。
- 更新后本地包为 6 文件，与 `a5f03a3` 中的 5 文件版本不同。

## 指纹

写入前：

| 文件 | 字节 | SHA-256 |
|---|---|---|
| `SKILL.md` | 23,933 | `4b5793b1e8d94980dcd4bec184f2c35c9cdb8970054625f41edac5356f38c06b` |
| `references/preuves-session-806cc849.md` | 9,182 | `ae7ba530563eb571e2720b33d80d1a0835f685c12f9748ef43decffedbf6758a` |
| `references/preuves-session-e421cc5c.md` | 8,696 | `b02089ecdb4a884e64bbe34198c577339ca0b2f9d08ba3c2fa664f72db39e264` |
| `scripts/audit_recommendation.py` | 14,745 | `c4666b1d670574e1c289d2b781a75d478257a2d750b2871c0c1cc3f1dbfe724d` |
| `scripts/freeze_recommendation.py` | 8,409 | `75841bf8e15ff60223c2ce834d1ea56b29dfee25a491fb386e255dcb4c3d7aae` |

写入后 `SKILL.md` 哈希见交付报告；两个脚本未改。

## 限制

- 首次快照 `hasMoreBefore=false`（`turnLimit=20`），复读 `hasMoreBefore=true`（`turnLimit=2`），验证期快照 `false`（`turnLimit=20`，18 条）；三者窗口不同，消息计数不可跨窗口比较。
- `revision` 非单调（14 → 33 → 10）；不能据大小判断快照新旧、活性或回退，只能用读取时间与文件 mtime。
- `[11]` 的归档、push 与 5 文件一致性为来源自述，未在本会话复核。
- 旧快照的「误导性判决」由脚本源码推断；本档案没有把旧快照喂给脚本做实测。
- 推荐原文「据此把案例改 FINAL」的因果被本档案收窄为「revision 74/ready 为升级依据，cold 为后续复核」。
- 来源会话在复读前还完成了一个 `reload skills` 回合（含 2 次成功 `Write`）；目标 `SKILL.md` 在写前复核（14:07 与 14:10）均为 23,933 B / `4b5793b1…`，未变，故这些写入未触及目标；14:12 起的变更是本会话的更新。
