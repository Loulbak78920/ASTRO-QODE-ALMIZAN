# 来源会话证据 — 806cc849（2026-10-26）

## 0. 边界

- 本文件只记录快照、JSONL 与工具输出中可复核的字段和原文。
- 消息时间戳为 UTC；文件 mtime 为本地时间（UTC+01:00）。
- 推荐 JSON 的 `summary`/`rationale` 属待审计声明，不当作独立事实。
- 未执行来源会话中的写入、提交、推送或安装命令。

## 1. 快照与指纹

| 对象 | 大小 | mtime（本地） | SHA-256 |
|---|---|---|---|
| `builtin_read_chat_session_6b27b1441815.txt` | 173,394 B | 2026-10-26T18:46:27.759+01:00 | `6b27b1441815ae4e04ec577f08b02d787d717b5ff26c4e63c35ba7823e24279d` |
| `806cc849….jsonl`（最终复核） | 2,756,080 B | 2026-10-26T18:55:50.716+01:00 | `8d3e444a61c0bedc7b85bb70dde89eaa3eea86a8cc83fc76b887011dcdc9f6ec` |
| 更新前 `SKILL.md` | 14,861 B | 2026-10-26T18:34:00.960+01:00 | `4c85fc8a34a3cbbac7a3114446bc692ed1fe2d0992897d4d9250cc91fd8b24b3` |

快照路径：

- `C:\Users\Administrateur\.qoder\tmp\C--Users-Administrateur-Desktop-IMAM8MAHDI\dd0b0f71-b0f6-453e-b62a-221792c6bc63\tool-results\builtin_read_chat_session_6b27b1441815.txt`
- `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\806cc849-0d65-4e8d-8222-c814cf235e04.jsonl`

快照字段：`sessionId=806cc849-0d65-4e8d-8222-c814cf235e04`、`title=更新 GitHub PR Skill`、`revision=14`、`runtimeState=waiting-user`、`activeTurnId=7eefd177-36fb-4adc-b64d-ff904944bb62`、`pendingInteractionCount=1`、`hasMoreBefore=false`、`messages=6`。

JSONL 为追加写入：本会话在 18:49:15 首次读到 2,396,054 B，18:55:50 复核为 2,756,080 B / 702 行。第 1 节只把最终复核值当完整快照。

## 2. 时间线

| # | 行 | 角色 | 时间（UTC） | 事实 |
|---|---|---|---|---|
| 0 | 3 | user | 17:29:47.368 | 初始任务；推荐 `github-pr-create-merge-sans-gh` / `update`；推荐切片 914 字符 |
| 1 | 156 | user | 17:35:10.285 | 「按此方案执行」 |
| 2 | 202 | assistant | 17:36:41.601 | Bash 用 `--recommendation-json <(printf ...)` |
| 3 | 206 | tool_result | 17:36:44.336 | `sha256sum` 输出 `d7a96a63…`；`py -3` 读 `/proc/110/fd/63` 失败；`RESULT FAIL`、`EXIT=2`、`AUDIT_EXIT=2` |
| 4 | 251 | tool_result | 17:38:10.053 | 写入手抄对象 `rec-github-pr-oid.json` |
| 5 | 256 | tool_result | 17:38:16.809 | `HASH_RAW acaa62a3…`、`HASH_NOTRAIL 677fe336…`；文件审计 `RESULT PASS`、`EXIT=0` |
| 6 | 260/262 | assistant/tool_result | 17:38:23.745 / 17:38:24.173 | 提取尝试 1 → `NOT_FOUND` |
| 7 | 272/274 | assistant/tool_result | 17:38:32.893 / 17:38:33.445 | 提取尝试 2 → `SyntaxError: unterminated string literal`（`elif ch == '\'`） |
| 8 | 277/279 | assistant/tool_result | 17:38:38.380 / 17:38:38.759 | 提取尝试 3 → `SyntaxError: invalid syntax`（`raw + b chr(10)`） |
| 9 | 283/285 | assistant/tool_result | 17:38:43.782 / 17:38:44.104 | 写入 `extract_rec.py` |
| 10 | 287/289 | assistant/tool_result | 17:38:48.263 / 17:38:49.119 | `EXACT_CHARS 914`、`EXACT_SHA256 677fe336…`、`SHA256_WITH_LF acaa62a3…`、`FIELDS_OK True` |
| 11 | 292/294 | assistant/tool_result | 17:38:53.346 / 17:38:54.358 | 文件审计 `RESULT PASS`、`EXIT=0`、`AUDIT_EXIT=0` |
| 12 | 297 | assistant | 17:39:03.714 | 前置报告：914 字节、`677fe336…`、审计 PASS |
| 13 | 493 | assistant | 17:44:41.391 | 报告更新完成 |
| 14 | 500 | user | 17:46:04.847 | 「运行完整测试套件」；快照时最终 assistant 仍为 `streaming` |

## 3. 失败原文与传输方式

第 206 行原文（节选）：

```text
d7a96a636b7c9b228230c35910bcfb380d3cb8f6b8335cd717411b43f0ba8f3b *-
ERROR="cannot read recommendation /proc/110/fd/63: [Errno 2] No such file or directory: '\\\\proc\\\\110\\\\fd\\\\63'"
RESULT FAIL
EXIT=2
AUDIT_EXIT=2
```

来源会话中 `--recommendation-json` 的调用清单：

| 行 | 传输方式 | 结果 |
|---|---|---|
| 202 | 进程替换 `<(...)` | `EXIT=2`，结构检查前失败 |
| 254 | 临时文件路径 | `RESULT PASS`、`EXIT=0` |
| 292 | 临时文件路径 | `RESULT PASS`、`EXIT=0` |
| — | stdin（`-`） | 0 次调用 |

## 4. 冻结哈希

| 对象 | 字符数 | SHA-256（无尾随 LF） | SHA-256（带尾随 LF） |
|---|---|---|---|
| JSONL 第 3 行原切片 | 914 | `677fe3362f6cf9014f1929598e399eb29752b4b2780354cc146eaccd547b45a5` | `acaa62a397bac3bc6fb46744874efd672311f233f130920b004b56b38193dc84` |
| 本会话推荐切片（dd0b0f71 第 3 行） | 1,085 | `5dec622a781aad8724b9400d6830dcb5a772e20180e9988b90091776a71c332a` | `946eeb86c1100f1ae96c4f94cff4b9cbe09de4f10ca38e8c12e2d1015af15a14` |

- 914 字符的对象正文 UTF-8 为 1,755 字节；冻结脚本的 `OUT_BYTES` 按字节计，`JSON_CHARS` 按字符计。
- 手抄副本的 `d7a96a63…` 只有前缀，完整值与生成方式未落盘；它与上表两个哈希都不相等。
- 本会话用 `scripts/freeze_recommendation.py --line 3` 对来源 JSONL 独立重算，得到相同的 914 / `677fe336…` / `acaa62a3…`。

## 5. 声明分类

| 推荐声明 | 分类 | 证据与边界 |
|---|---|---|
| 进程替换生成 `/proc/<pid>/fd/N`，原生 Python 打不开 | `SUPPORTED` | 第 202/206 行原文；本会话复现 `/proc/1146/fd/63` + `EXIT=2` |
| 失败点在结构检查之前 | `SUPPORTED` | 输出无 `REC_*` 字段；`EXIT=2` 来自 `load_json` 失败 |
| 「改走 stdin 后同一命令 `RESULT PASS`、`EXIT=0`」 | `CONTRADICTED`（来源历史） | 来源 3 次调用为 1 次进程替换 + 2 次文件，0 次 stdin；stdin 路径本身在 dd0b0f71 实测 PASS/0，但不证明来源执行过 |
| 原切片 914 字符、`677fe336…`、带 LF `acaa62a3…` | `SUPPORTED` | 第 289 行输出；本会话独立冻结一致 |
| 手抄副本 `d7a96a63…` 与原文不同 | `SUPPORTED`（差异）/ `UNKNOWN`（成因） | 与 677/acaa 不等；前缀来自第 206 行，完整哈希缺失 |
| 「从本会话 JSONL 第 3 行」提取同一对象 | `SUPPORTED` | 第 3 行为 17:29:47.368Z 的用户任务；`--line 3` 复算一致 |
| 更新前 SKILL.md 只写 stdin、无进程替换警告、无 JSONL 冻结步骤 | `SUPPORTED`（基线） | 基线 14,861 B / `4c85fc8a…`；脚本节仅一行「推荐 JSON 从标准输入读取」 |

## 6. 本会话独立复核（dd0b0f71）

- 冻结：`JSON_CHARS=1085`、`SHA256_NO_LF=5dec622a…`、`SHA256_WITH_LF=946eeb86…`、`OUT_BYTES=1755`，`RESULT PASS`、`EXIT=0`。
- stdin 审计：`RESULT PASS`、`EXIT=0`；同文件审计：`RESULT PASS`、`EXIT=0`；两种传输结论一致。
- 负例：无候选 → `EXIT=1`；缺 `rationale` → `MISSING_FIELDS="rationale"`、`EXIT=1`；`--expect-sha256 deadbeef` → `EXIT=1`；`--out` 指向 Skill 内部 → `EXIT=2`；`summary` 含 `{braces}` → 提取成功、`EXIT=0`。
- 进程替换复现：`ERROR="cannot read recommendation /proc/1146/fd/63…"`、`RESULT FAIL`、`EXIT=2`。
- 快照会话摘要：`revision=14`、`waiting-user`、`activeTurn=7eefd177…`、`pending=1`、`messages=6`、成功写工具 20、`Bash` 51、`mcp_call` 6、最终 assistant `streaming`、`DELIVERY_INCOMPLETE=false`、`ZERO_WRITE=false`。
- 目标写入扫描：702 行 JSONL 中 `verify-skill-recommendation-claims` 的 `Write`/`Edit` 命中 0；最后写入为 `~/.qoder/tmp/verify-github-pr-*/` 与 `github-pr-create-merge-sans-gh`。

## 7. 未验证与限制

- 手抄副本 `d7a96a63…` 的完整哈希、字节构成与差异原因未确定。
- 快照只有 6 条消息（`hasMoreBefore=false` 为该窗口值）；完整历史来自 702 行 JSONL，未再用 `read_chat_session` 复核全部内容。
- 来源会话未定稿：快照时 `waiting-user` 且 `activeTurnId` 非空，最终 assistant 为 `streaming`；本会话按 `CAVEAT_SOURCE_ACTIVE` 继续，不声称来源已完成。
- 未验证运行时注入、Git 提交或推送；目标 Skill 目录没有 `.git`。
- 审计输出的 `SESSION_*` 计数来自 6 条消息的快照窗口，不代表完整会话的计数。
- 推荐 JSON 的 `summary`/`rationale` 本身不可信，本文件只对照来源证据分类，不以其自证。

## 8. 复现命令

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/freeze_recommendation.py \
  --session-jsonl "C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/806cc849-0d65-4e8d-8222-c814cf235e04.jsonl" \
  --line 3
```

- 期望：`JSON_CHARS=914`、`SHA256_NO_LF="677fe336…"`、`SHA256_WITH_LF="acaa62a3…"`、`RESULT PASS`、`EXIT=0`。

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/audit_recommendation.py \
  --recommendation-json - \
  --session "C:/Users/Administrateur/.qoder/tmp/C--Users-Administrateur-Desktop-IMAM8MAHDI/dd0b0f71-b0f6-453e-b62a-221792c6bc63/tool-results/builtin_read_chat_session_6b27b1441815.txt" \
  --target-dir "C:/Users/Administrateur/.qoder/skills/verify-skill-recommendation-claims" \
  --skills-root "C:/Users/Administrateur/.qoder/skills" < "<rec.json>"
```

- `<rec.json>` 为 `freeze_recommendation.py --out` 产生的 Skill 目录外文件；文件哈希须等于 `SHA256_NO_LF`。
- 若改用 `<(printf ...)`，预期 `EXIT=2`：该失败只证明传输路径不可用，不证明推荐内容无效。
