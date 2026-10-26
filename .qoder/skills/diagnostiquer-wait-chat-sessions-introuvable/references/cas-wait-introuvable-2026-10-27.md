# 案例：wait_chat_sessions 返回「不存在」而 read_chat_session 仍可读

日期：2026-10-27（所有时间戳为 UTC，工具输出按原样转录）
来源会话：`e0d40f60-65c4-48f7-b589-fde72f210d2a`（标题「创建 Windows Unicode Skill」）
原始 JSONL：`C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/e0d40f60-65c4-48f7-b589-fde72f210d2a.jsonl`

本档案只记录第一个回合（用户消息 `75b70544…`，2026-10-26T23:08:22Z）。该会话在 23:19:56Z 又启动了「commit 并推送更新」回合，与本案例无关。

## 1. 失败的 wait 调用

JSONL 第 116 行（`tool_use`）：

```json
{"toolName":"mcp__builtin__wait_chat_sessions",
 "arguments":{"sessionIds":["c7e3d5d5-efcd-4b9f-b9a6-c5d6e25c51ef"],"timeoutMs":60000}}
```

第 118 行（`tool_result`，`is_error=true`）：

```text
等待的 ChatSession 不存在：c7e3d5d5-efcd-4b9f-b9a6-c5d6e25c51ef
```

时间：调用 23:15:14.210Z，返回 23:15:14.326Z，**116 ms**。请求的 `timeoutMs` 是 60000，但调用没有等待，也没有返回 `outcome`、`runtimeState` 或 `revision`。

同一 schema 的说明包含：「Never include the current conversation: it cannot finish while waiting on itself.」这是第 3 条「排除自排除」的依据。

## 2. 同目标的 read 快照

同一 `sessionId` 在失败前后均可读：

| 时间 | runtimeState | activeTurnId | revision | hasMoreBefore |
|---|---|---|---|---|
| 23:08:41Z（第 24 行） | `running` | `81b6060d-b86d-404b-83a5-62316de1e2be` | 10 | false |
| 23:09:20Z（第 62 行） | `running` | 同上 | 13 | false |
| 23:10:14Z（第 99 行） | `running` | 同上 | 21 | false |
| 23:15:46.878Z（第 133 行） | `cold` | `null` | 0 | true |

最后一行的读取参数为 `turnLimit: 1`；第 99 行的读取参数为 `turnLimit: 2`。因此 `hasMoreBefore` 由 false 变为 true **同时伴随窗口变化**，两者不可直接比较。`revision` 从 21 变为 0 发生在状态切换时，也不可跨状态比较。

冷快照的消息里只有两个用户回合：`87f20012…`（引用来源 `f0fb0e02…` 的模板）与 `81b6060d…`（「调整脚本形态，改为纯文档型」），不含当前会话的回合 `75b70544…`。

## 3. 自排除检查

当前会话的用户回合是 `75b70544…`，引用来源为 `c7e3d5d5…`；目标会话的用户回合是 `87f20012…` 与 `81b6060d…`。目标 ID 不是当前会话，因此 `not found` 不能由「wait 禁止自包含」解释。

分类：`INFERRED`。依据是快照消息 id 与文本的比对，不是工具直接给出的诊断。

## 4. 替代门禁（来源会话实际执行的命令）

JSONL 第 122 行，逐字：

```bash
T="C:/Users/Administrateur/.qoder/skills/verifier-unicode-fichiers-windows"; for i in 1 2 3 4; do F=$(find "$T" -type f -printf '%P|%s|%T@\n' 2>/dev/null | sort | tr '\n' ' '); S=$(find "$T" -type f -exec sha256sum {} \; 2>/dev/null | awk '{print substr($1,1,12)}' | sort | tr '\n' ','); echo "S$i $F| $S"; [ "$i" -lt 4 ] && sleep 6; done
```

第 124 行输出（`is_error=true`，`Exit code 1`）：

```text
S1 SKILL.md|8455|1793056176.9934685000 references/cas-faux-negatif-unicode-2026-10-27.md|5959|1793056203.6186144000 | 060aa2c02e6e,970cc5f28b0e,
S2 SKILL.md|8455|1793056176.9934685000 references/cas-faux-negatif-unicode-2026-10-27.md|5959|1793056203.6186144000 | 060aa2c02e6e,970cc5f28b0e,
S3 SKILL.md|8455|1793056176.9934685000 references/cas-faux-negatif-unicode-2026-10-27.md|5959|1793056203.6186144000 | 060aa2c02e6e,970cc5f28b0e,
S4 SKILL.md|8455|1793056176.9934685000 references/cas-faux-negatif-unicode-2026-10-27.md|5959|1793056203.6186144000 | 060aa2c02e6e,970cc5f28b0e,
```

- 四行指纹完全一致；时间 23:15:21.680Z 到 23:15:41.511Z，约 19.8 秒，与 4 次采样、间隔 6 秒一致。
- `Exit code 1` 来自循环末尾 `[ "$i" -lt 4 ]` 在 `i=4` 时为假，**不是门禁失败**。四行输出本身是「稳定」。
- 该输出只打印，不做断言；「稳定」的结论来自人工比对四行。`scripts/attendre_stabilite.py` 是本 Skill 的显式退出码实现，语义相同但不是本条命令。

## 5. 决定与写入

- 23:15:46.878Z 读取到 `cold`、`activeTurnId: null`。
- 23:17:14.769Z 与 23:17:38.529Z 才执行两次 `Edit`（`SKILL.md`、参考文件）。
- 在目录名等于 `name` 的副本上，`skill-file-qa` 为 9 pass、0 fail、0 warn，`QA_RC=0`。

写入发生在冷确认之后，而不是在 wait 失败之后，也不是在指纹稳定的当下。用户在此前的选择是「等停止后最小修正（推荐）」，无用户纠正。

## 6. 分类

- `REPRODUCED`：wait 立即返回 `is_error`「不存在」，同 ID 的 read 仍返回 `running` 与完整状态字段。
- `REPRODUCED`：文件指纹门禁在 4 次采样中一致；同一命令的 rc=1 可由末尾测试表达式复现。
- `DOCUMENTED`：`revision` 21 到 0、`hasMoreBefore` false 到 true，与状态切换、`turnLimit` 变化同时发生。
- `INFERRED`：`not found` 不是自排除，依据是快照用户回合与当前回合的 id/文本比对。
- `UNVERIFIED`：`not found` 的根因与作用范围（例如「只能观察已注册会话」假设）；冷状态下 wait 是否恢复；其他平台与其他版本的行为。
- `UNVERIFIED`：稳定采样期间来源会话的确切内部状态。四行一致只证明窗口内没有写入。

## 7. Control

本 Skill 写入时：

| 文件 | size | lines | SHA-256 |
|---|---|---|---|
| `SKILL.md` | 9975 | 130 | `e26a186e540d9b03432c5c858ecb4fe3c3717a271d578e893e4fdbce38e059b2` |
| `scripts/attendre_stabilite.py` | 3739 | 116 | `87a0467edb0bc560037db57fdb5903dc0a3ee1b722247d313fb1fa3c1972c7ba` |

脚本夹具实测（2026-10-27）：

```text
stable dir, 3 samples        -> RESULT STABLE, RC=0
append during sampling       -> RESULT CHANGED modified=1, MODIFIED 'a.txt', RC=1
create new file during run   -> RESULT CHANGED added=1, ADDED 'c.txt', RC=1
remove file during run       -> RESULT CHANGED removed=1, REMOVED 'b.txt', RC=1
non-ASCII file name change   -> MODIFIED '\xe9.txt', stdout non-ASCII bytes 0, RC=1
missing directory            -> ERROR directory not found, RC=2
--samples 1                  -> ERROR samples must be >= 2, RC=2
--interval -1                -> ERROR interval must be >= 0, RC=2
documented 4x6s command      -> RESULT STABLE, RC=0 (18 s)
__pycache__ / *.pyc          -> none
before/after stat            -> size and mtime unchanged
integration harness          -> 32 PASS / 0 FAIL
```

本文件自身的哈希在交付报告中记录，因为每次编辑都会改变它。
