# 案例 — 2026-10-27，Skill 交付前的两处返工

来源会话：`d4a167f0-3f80-4741-ac33-654e589cd3cc`（会话标题「创建并发技能补全」）。
JSONL：`C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\d4a167f0-3f80-4741-ac33-654e589cd3cc.jsonl`。
被写的包：`C:\Users\Administrateur\.qoder\skills\completer-skill-concurrent-delta`。

快照绑定：2 184 887 B、458 行、`mtime=2026-10-27T15:47:40+01:00`、SHA-256 `b4c7f35d707c0c4f6d9085aa3df713c5ed11a7bf609b219240f43cc330df3fdf`。以下行号只对该快照成立；会话续写后须按文本重新定位，不得沿用行号。

`read_chat_session` 快照只给出摘要式助手文本（`revision: 11`、`hasMoreBefore: false`），
因此本文的命令、输出与原文全部取自 JSONL 的 `tool_use` / `tool_result` 配对，未采用摘要转述。

时间：会话消息为 UTC；shell 与 `validate_skill.py` 输出为本地 `+01:00`。

## 1. 时间线

| 时刻 | 事件 | 证据 |
|---|---|---|
| `14:22:42.107Z` | 用户要求新建该 Skill，并调用 `read_chat_session` 核实来源 | 来源会话第 1 条用户消息 |
| `15:27:10+01:00`（`14:27:10Z`） | `SKILL.md` 已落盘，随后才测 description | JSONL 行 155（Write）、171（fingerprint `mtime=2026-10-27T15:27:10+01:00`） |
| 同上 | `DESC_LEN 1389`，QA `FAIL description: 1389 chars exceeds 1024` | JSONL 行 171（`validate_skill.py:466`） |
| 同日 | 候选 description 实测 `1096`，再压缩到 `1011`，由 Edit 写回 | JSONL 行 179、184；写入行 187 |
| `15:28:05+01:00` | `PASS description: single line, 1011 chars`，`9 pass, 0 fail, 0 warn` | JSONL 行 203 |
| 同日 | 回读 `SKILL.md` 与参考，发现法文转述，改为中文原文 | JSONL 行 206–218（Read 与结果、发现） |
| 同日 | 两处 Edit 写回原文 `等待的 ChatSession 不存在` | JSONL 行 219、225 |
| `15:28:29+01:00` | 最终 QA：`RESULT PASS`，18 516 B，`a334b419…` | JSONL 行 232 |

关键顺序：**QA 在 15:28:05 已经 PASS，但散文错误仍在**；错误是第 3 步「回读」发现的，不是 QA 发现的。

## 2. description 计数

| 阶段 | 值 | 结论 |
|---|---|---|
| 首次写盘 | 1389 | `FAIL`，validator 仅在 `len > 1024` 时报错 |
| 候选一 | 1096 | 仍超限，未写入 |
| 候选二（最终） | 1011 | `PASS description: single line, 1011 chars` |

## 3. 两处更正的原文

| 位置 | 更正前 | 更正后 | 来源 |
|---|---|---|---|
| 参考时间线（时刻列） | `14:11:2x` | `avant 14:11:33` | JSONL 行 192 |
| SKILL.md | `deux annotations lues en authentifié à 14:11:22Z` | `deux annotations lues en authentifié avant 14:11:33Z` | JSONL 行 196 |
| 参考正文 | `« la ChatSession attendue n'existe pas »` | `« 等待的 ChatSession 不存在 »` | JSONL 行 219 |
| SKILL.md | `(« ChatSession introuvable »)` | `(« 等待的 ChatSession 不存在 »)` | JSONL 行 225 |

法文转述的成因是凭语义重写工具报错，而不是复制 `tool_result`；两处分布在两个文件，只改一处会让两个文件的计数出现 0 与 1 的不一致。

## 4. 最终验收原文

```text
PASS description: single line, 1011 chars
PASS body: 218 lines (< 500)
PASS local references: 2 checked
PASS skill references: 9 checked
Fingerprint (final): 18516 bytes | mtime=2026-10-27T15:28:29+01:00 | sha256=a334b41960e27c51c098b43cc6de163a2b30ec39b1f8465beaf864b43d969b18
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
QA_RC=0
--- ASSERTIONS ---
SKILL.md 18516 a334b41960e27c51c098b43cc6de163a2b30ec39b1f8465beaf864b43d969b18
references/cas-2026-10-27-publier-workflow.md 7088 9f48d96b9de9114d49d21f91be15ea8e370b74bfaff9800d137ab7a87ce6d0eb
ERR_MSG_IN_SKILL 1
ERR_MSG_IN_REF 1
OLD_PARAPHRASE 0
ASTRO_REF 2 4
```

断言含义：原文在两个文件各 1 次，旧转述合计 0 次；两个文件的哈希分别记录，因为 validator 的 fingerprint 只覆盖 `SKILL.md`。

## 5. 限制

- 最终哈希只对 `2026-10-27` 这次快照成立；包后续被改则失效，不得引用为当前状态。
- 行号绑定到文首列出的 JSONL 快照；该会话在引用写入后继续追加记录，早期行号已整体后移（例如 `DESC_LEN 1389` 由 170 移至 171），复核时按文本搜索而不是沿用旧号。
- 该会话第 2 个用户回合「重载 Skill 并验证运行时绑定」在读取时仍 `streaming`（`activeTurnId: 614503dc-…`），本文不采用其任何结论。
- 本次未验证运行时绑定或重载；「已创建」不等于「已注入最新正文」。
- 来源会话的推荐 JSON 指向 `completer-skill-concurrent-delta`，本文只提取其中的写作契约教训，不复述其业务结论。
