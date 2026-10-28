# 证据档案：会话 c106ed2c（2026-10-27）

来源会话 `c106ed2c-d071-4c42-8de8-ff33e0860acd`，标题「创建官方验证技能」。本档案支撑 SKILL.md 新增的「内联快照落地」步骤与「同 revision 多份快照」诊断行。消息时间为 UTC，文件 mtime 为本地 `+01:00`。

## 本会话读取的来源快照

| 项 | 值 |
|---|---|
| 读取参数 | `turnLimit=20`、`includeToolOutputs=false`、`maxOutputCharsPerItem=4000` |
| `runtimeState` | `running` |
| `activeTurnId` | `a6c628de-dabc-4e88-b6b9-f58dbd9d91a2` |
| `revision` | 11 |
| `pendingInteractionCount` | 0 |
| `hasMoreBefore` | `false` |
| `messages` | 4（user / assistant / user / assistant） |
| 最终用户消息 | 「Valider le plan et procéder à la création des 3 fichiers」 |
| 最终 assistant | `streaming`、104 字符，`Bash` 19、`mcp_call` 2、成功写工具 0 |

该次调用只返回内联 JSON，结果中没有文件路径；`toolUseResult` 字符串 8,421 字符，以 UTF-8 写出为 9,279 B。

## 来源会话内的做法（c106ed2c JSONL）

| 行 | 工具 | 内容 | 结果 |
|---|---|---|---|
| 52 | `mcp_call` | `read_chat_session` 读 `0d4a13d8-1297-4e11-a60d-047168464b21` | 内联 JSON，无路径 |
| 54 | user / `toolUseResult` | 同一 JSON 字符串，20,672 字符 | 与 `message` 内 `tool_result` 文本逐字相等（实测） |
| 57 | `mcp_call` | 同一来源 `turnLimit=1`、`includeToolOutputs=true`、`maxOutputCharsPerItem=8000` | 第二份快照 |
| 60 | user / `toolUseResult` | rev 39 / 2 msgs / 38,316 字符 | 与第 54 行同 revision，选错风险 |
| 96 | `Bash` | 扫描含来源 sessionId 与 `read_chat_session` 的条目 | 定位候选 |
| 101 | `Bash` | `splitlines()[53]` → `json.loads` → `json.dump(ensure_ascii=False, indent=1)` 写 `~/.qoder/tmp/attester-validation-audit/session-0d4a13d8-turn20.json` | `TYPE str`、`REV 39`、`STATE ready`、`MSGS 10`、`OUT 26290` |
| 106 | `Bash` | `audit_recommendation.py --recommendation-json - --session <落地文件> --target-dir ...`，推荐 JSON 经 stdin | `SESSION_REVISION=39`、`SESSION_MESSAGES=10`、`RESULT PASS`、`EXIT=0` |

落盘文件现为 26,290 B，`SHA-256 1ec03c14…`；10 条消息角色交替。该文件是重序列化产物，与第 54 行的 20,672 字符不再字节对应。

## 本会话独立复跑

- 定位：扫描本会话 JSONL `52f51413-1eba-4518-962e-29a3eb2ed03c.jsonl`，匹配 `toolUseResult` 中的来源 `sessionId`，得到 `line=39`（未按固定行号）。
- 原样写出：`toolUseResult` 9,279 B，`SHA256=b64b67eb…`；文件哈希与字符串字节哈希相同。
- 字段核对：`sessionId=c106ed2c…`、`revision=11`、`runtimeState=running`、`activeTurnId=a6c628de…`、`messages=4`、`hasMoreBefore=false`，与本次读取一致。
- 推荐冻结：本会话 JSONL `line=3`，1,624 字符，`SHA256_NO_LF=5bbbc27e…`、`SHA256_WITH_LF=22da296d…`；`--out` 文件 1,675 B，哈希等于 `no_lf`。
- 审计（推荐经 stdin，快照经文件）：
  - `TARGET_EXISTS=true`、`ACTION_CONFLICT=NONE`、`SCOPE=INSIDE`、`DUPLICATE_ROOTS=none`、`INSTRUCTION_RISK=none`
  - `SESSION_REVISION=11`、`SESSION_MESSAGES=4`、`SESSION_RUNTIME_STATE="running"`、`SESSION_FINAL_ASSISTANT_STATUS="streaming"`、`SESSION_ZERO_WRITE=true`
  - `RESULT PASS`、`EXIT=0`

## 选择陷阱

- 来源会话对同一来源有两次读取：第 54 行 rev 39 / 10 msgs / 20,672 字符；第 60 行 rev 39 / 2 msgs / 38,316 字符。二者 revision 相同，`includeToolOutputs` 与 `turnLimit` 不同。
- 只按 `sessionId + revision` 取「最后一条」会选到第 60 行，审计将报 `SESSION_MESSAGES=2`，与要审的 10 条窗口不符；按「最大」也会选错。
- 因此选择条件是 `sessionId` + `revision` + 本次读取的 `messages` 长度（或 `turnLimit`）；无法唯一匹配时重新读取。

## 限制

- 来源使用固定行号 `line=54` 与 `json.dump(indent=1)`；前者随 JSONL 增长漂移，后者改变字节。通用步骤不复制这两点。
- 来源读取时 `runtimeState=running`，活动回合写 `attester-validation-officielle-skill`，不是本 Skill；本条只证明方法可复跑，不证明来源交付完成（`CAVEAT_SOURCE_ACTIVE`）。
- 快照是读取时刻的状态；来源后来完成该回合不改变已落地快照。审计输出的 `SESSION_*` 只属于该快照。
- `toolUseResult` 缺失、非字符串、非法 JSON 或被截断时停止，不修补 JSON；改做新鲜读取或跳过脚本。
- 未复核 `attester-validation-officielle-skill` 的创建与 QA 状态，非本任务范围。

## 指纹（写入前）

| 文件 | 字节 | SHA-256 |
|---|---|---|
| `SKILL.md` | 29,168 | `0152cdb7a2fbd0e9d7be3c64fedf9df1e4481b4ed577a7dbb393a34622b44397` |
| `references/preuves-session-806cc849.md` | 9,182 | `ae7ba530563eb571e2720b33d80d1a0835f685c12f9748ef43decffedbf6758a` |
| `references/preuves-session-d4a03af8.md` | 8,541 | `ac1222aad1915567f11d2ab5ba379f627c4b952e7fe4e27a4041efea51f1814b` |
| `references/preuves-session-e421cc5c.md` | 8,696 | `b02089ecdb4a884e64bbe34198c577339ca0b2f9d08ba3c2fa664f72db39e264` |
| `scripts/audit_recommendation.py` | 14,745 | `c4666b1d670574e1c289d2b781a75d478257a2d750b2871c0c1cc3f1dbfe724d` |
| `scripts/freeze_recommendation.py` | 8,409 | `75841bf8e15ff60223c2ce834d1ea56b29dfee25a491fb386e255dcb4c3d7aae` |
| 本会话临时快照（Skill 根之外，验证后已清理） | 9,279 | `b64b67eb2909b2f43431c6fbd3508ea180b8934d0f8165ec9cbccce5ea31ee25` |
| 来源落盘快照（Skill 根之外） | 26,290 | `1ec03c148ea361073886a5765289793ef4c1ab42c657d54e6165de8ce9f3d841` |
