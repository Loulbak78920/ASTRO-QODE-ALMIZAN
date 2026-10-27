---
name: audit-skill-during-live-creation
description: "在创建或更新 Skill 时发现目标目录中途出现、来源或并发会话仍在运行，立即停止 create 并转为只读验收：用 read_chat_session 记录 runtimeState、activeTurnId、revision 与 hasMoreBefore；wait_chat_sessions 可能永不返回 cold，只有 timeout(running)、turn_completed(ready)、needs_attention(waiting-user)，因此用 ready+activeTurnId=null 或 waiting-user+pendingInteractionCount≥1 加全包连续三次指纹判定 QUIESCENT/PAUSED/RUNNING；从项目 JSONL 的 Write/Edit 按精确 file_path 归因全部写入者，空扫描不等于无写入者；采样只证明安静，不证明包完整；把 validator 的 FAIL local reference、PASS fingerprint、夹具 FAILS=0 与文档计数分级为 FINAL/PROVISIONAL/INVALID；静默后重读全部文件、重跑 skill-file-qa，先把计划缺陷对最新字节重定位（CURRENT/ALREADY_FIXED/GONE/CHANGED），再用最新 Files(N) 做最小 Edit，绝不覆盖并发写入方。用于目标目录规划后出现、两次采样一致但 references 仍为空、包中途从 2 文件增至 3 文件、计划补丁基于旧字节、JSONL 扫描 0 命中、waiting-user 暂停、cold 缺失、目标哈希仍在变、Edit 返回 changed since last read、采样 mtime 早于上次采样等场景；不替代一般并发写入（skill-update-concurrency-safe）、职责重合接管决策（adopt-concurrent-duplicate-skill）或来源证据提取（audit-session-evidence）。关键词：实时创建、写入者归因、wait_chat_sessions、QUIESCENT、PAUSED、全包指纹、补丁重定位、Files(N)、changed since last read。"
---

# 实时创建中的只读验收

## 目标与边界

本 Skill 处理一个窄场景：你被要求创建或更新 Skill，目标目录在任务中途出现，而创建它的会话可能仍在写入。它补的不是并发写入机制本身，而是**活性判定、证据分级、静默后重跑**这三步。

- 不替代 `skill-update-concurrency-safe`：采样、备份、最小 Edit、QA 重跑的通用机制以它为准。
- 不替代 `adopt-concurrent-duplicate-skill`：发现职责重合、需要用户在几个选项中决策时，转它。
- 不替代 `audit-session-evidence`：来源会话的完整取证与原始日志核对仍用它。
- 不新建脚本：判活复用 `verify-injected-skill-body-freshness` 的只读写入者扫描脚本，目录快照用 `find` 与 `sha256sum`，最终验收用 `skill-file-qa`。

## 触发条件

- 预检时目标不存在，准备写入前目录突然出现；
- 两次采样 size、mtime、SHA-256 一致，但目录里声明的参考文件仍缺失或子目录仍为空；
- 校验器的 FAIL/PASS 或夹具的 `FAILS=0` 只对较早版本成立；
- 来源会话的 `revision` 在多次读取之间递增；
- 写入目录的是别的会话，你无法确认它是否已经结束；
- 用户要求“先验收”“接管”“顺手把 FAIL 修掉”；
- 已获授权更新后，目标在两个 `Edit` 之间继续变化；
- 来源会话已 `cold` 或 `waiting-user`，但目标哈希或 mtime 仍在变；
- `wait_chat_sessions` 始终不返回 `cold`，只有 `timeout`/`turn_completed`/`needs_attention`；
- 同一包可能有多个写入者，或等待期间新增了 references/scripts；
- 计划中的补丁基于旧字节，行号、字节数或 `Files (N)` 已变。

## 不可协商约束

1. 先判活性，再判稳定。哈希一致只说明采样窗口内没有写入，不说明写入者已结束。
2. 写入者仍在运行时零写入：不建目录、不 `Write`、不 `Edit`、不删除、不修补任何 FAIL。
3. 证据必须分级。活版本的观测值只能是 PROVISIONAL；只有 QUIESCENT/PAUSED 确认后重跑的结果才能写成 FINAL。
4. 只对最终版本做最小 Edit；并发写入方新增的标题、参考文件与计数一律保留。
5. 静默后必须重读全部文件并重跑校验与夹具；不复用旧 PASS，也不复用旧 FAIL。
6. 没有 FINAL 证据时，报告写“暂定/未验证”，不写“已创建/已修复/已通过”。
7. 来源会话 `cold`/`ready` 只覆盖被读取的那个 `sessionId`；写入者是否仍在写，以目标文件的连续指纹为准，不以会话状态推断。

## 第 0 步 — 判定写入者活性

### 0.1 核对工具契约

先 `mcp_get` 取实时 schema，不要假定参数名。本机实测：

- `read_chat_session` 必填 `sessionId`；传 `session_id` 会报 `params must have required property 'sessionId'`。
- 可用 `includeToolOutputs: true`、`turnLimit`（1–20）、`maxOutputCharsPerItem`（200–8000）。
- 返回超过约 25k token 会落盘到 `.qoder/tmp/.../tool-results/`；此时读该文件，不要反复重试同一调用。

### 0.2 记录活性字段

每次读取记录：

```text
runtimeState  = running | opening | ready | waiting-user | cold（cold 可能不出现）
activeTurnId  = <id | null>
revision      = <n>
hasMoreBefore = true | false
pendingInteractionCount = <n>
最后一条 assistant 的工具状态与正文
```

判定规则：

- `runtimeState: running` 且 `activeTurnId` 非空 → RUNNING，不可编辑。
- `runtimeState: opening` → 会话正在启动，按 RUNNING 处理，等它进入明确状态。
- 间隔数秒再次读取，`revision` 递增 → 写入仍在推进；即使文件哈希暂时不变也一样。
- `runtimeState: ready` 且 `activeTurnId: null` → 当前无活动回合；仍须全包连续三次指纹一致才算 QUIESCENT。
- `runtimeState: waiting-user` 且 `pendingInteractionCount ≥ 1` → PAUSED：回合停在等人回复，当前不写，但用户一回复就会恢复写入；未确认用户不会回复时，不要把它当 cold。
- 读不到来源会话时，用目标目录的 mtime 范围、JSONL 写入记录与短时间内新增文件推断；推断不出时按“写入者未知”处理，继续等待。

### 0.3 等到结束（不假定 cold 会出现）

- 一次性检查用 `wait_chat_sessions` 的 `timeoutMs: 0`；能建立监督关系时优先 supervise。
- `outcome` 只描述这次等待的结果，不表示目标工作已被接受。本机实测可能出现且仅出现：
  - `timeout` + `runtimeState: running`：仍在跑，revision 继续递增；
  - `turn_completed` + `runtimeState: ready` + `activeTurnId: null`：当前回合结束；
  - `needs_attention` + `runtimeState: waiting-user` + `pendingInteractionCount ≥ 1`：停在等人回复。
- `cold` 可能始终不出现，不能把它当作唯一终点。用以下三态判定：
  - `RUNNING`：任一写入者 running/opening，或 revision 递增，或目标指纹在变 → 零写入。
  - `QUIESCENT`：`ready` + `activeTurnId: null` + 全包连续三次指纹一致（间隔 ≥2 秒，建议总窗口 ≥5 秒）。
  - `PAUSED`：`waiting-user` + `pendingInteractionCount ≥ 1` + 全包指纹稳定。当前不写，但用户回复即可恢复；未确认用户不会回复时，按潜在写入者处理，不宣称 cold。
- `wait` 返回的 `revision: 0` 不是“没有写过”；它只是该次返回的状态值。把最后一次 `read_chat_session` 的 revision 单独记录。
- 即使看到 `cold`，仍要重新读取目录并做三次全包采样；会话结束不等于最后一笔写入已落盘。
- `cold` 或 `ready` 都不排除其他写入者：其他会话、后台代理或用户手动编辑都可能继续改写目标。任何一次指纹变化都回到 RUNNING 判定。

### 0.4 归因全部写入者（全包）

不要只读取一个可疑会话就下结论。对项目 JSONL 中所有 Write/Edit 的 `file_path` 做精确匹配，覆盖 `SKILL.md`、references 与 scripts。复用已有的只读脚本；它虽以 SKILL.md 命名，但按精确路径匹配，可用于包内任意单个文件：

```bash
py -3 -B "$HOME/.qoder/skills/verify-injected-skill-body-freshness/scripts/scan_skill_writers.py" \
  --scan-dir "$HOME/.qoder/projects/<encoded-project>" \
  --target "<absolute-path-to-file>" --include-results
```

- 脚本一次只接受一个精确 `--target`；包里有几个文件就运行几次。
- 退出码：0 = 有命中，1 = 无命中，2 = 参数或环境错误。无命中不等于无写入者，先看 `FILES: N scanned` 是否大于 0。
- 使用绝对 `--scan-dir`。Bash 每次调用都会重置 cwd，前一次 `cd` 不会保留；`*/*.jsonl` 可能静默展开为 0 个文件。空输出加 0 文件是扫描失败，不是“没有写入者”。
- 归因分级：`CONFIRMED`（成功的 Write/Edit 命中，附 sessionId、JSONL 行号、时间）；`ATTEMPTED`（命中但 tool_result 为 ERROR，写入未生效）；`INFERRED`（只有 runtimeState、updatedAt 或正文提及）；`UNKNOWN`（没有扫描覆盖，或目标可能被外部编辑器改写）。
- 多写入者时逐个列出，并分别记录最后一次成功写入时间；最后变为 `ready` 的会话不等于唯一写入者。
- 只要任一文件仍有 `CONFIRMED`/`ATTEMPTED` 写入者处于 RUNNING，或扫描未能证明覆盖，就保持零写入。

## 第 1 步 — 冻结写入

- 立即停止 create：不建目录、不写任何文件。
- 记录目标首次出现时间、目录内全部文件的 mtime 范围、当前清单（含空目录）。
- 基线写到 Skill 目录之外，例如 `.qoder/tmp/<project>/live-audit/`。
- 不把“缺 reference 的 FAIL”当成待修缺陷；它很可能只是写入者还没写到那一步。
- 如果之前已经建过目录或文件，只撤回本会话创建的部分，不改动写入者的文件。

## 第 2 步 — 快照与完整性（辅助证据）

```bash
target="/c/Users/<user>/.qoder/skills/<skill-name>"
find "$target" -maxdepth 3 -printf '%P | %s bytes | %TY-%Tm-%Td %TH:%TM:%TS\n' | sort
find "$target" -maxdepth 3 -type f -exec sha256sum {} + | sort
find "$target" -type d -empty
```

- 至少采样两次，间隔不小于 2 秒；报告连续一致的次数。
- 空子目录是“尚未写完”的信号，不是“没有参考文件”。
- 从 `SKILL.md` 抽出全部本地引用，逐个检查是否落盘；缺失项标记为 PROVISIONAL，而不是缺陷。
- 结论只有两种：`QUIET`（采样窗口内无变化）或 `CHANGING`。`QUIET` 不能升级为 `FINAL`，除非活性判定为 QUIESCENT/PAUSED。

## 第 3 步 — 证据分级

| 观察 | 分级 | 理由 | 允许动作 |
|---|---|---|---|
| 两次采样哈希一致，参考子目录为空 | INSUFFICIENT | 采样窗口落在两次写入之间，包不完整 | 继续等待，不改文件 |
| `FAIL local reference not found` | PROVISIONAL | 引用已写、文件未落盘 | 不修补；静默后重跑 |
| `PASS fingerprint: unchanged during validation` | PROVISIONAL | 指纹只覆盖 SKILL.md，不代表全包 | 仍需全目录采样与静默确认 |
| 活版本上的 `RESULT PASS` | PROVISIONAL | 通过的是瞬间版本 | 不写成事实 |
| 夹具 `FAILS=0`，但 before/after 哈希不同 | PROVISIONAL 或 INVALID | 断言未覆盖“运行期间文件未变” | 静默后重放，并注明漂移 |
| 文档里的字节数、行数、哈希 | PROVISIONAL | 随写入者推进而变 | 静默后逐项复核 |
| QUIESCENT/PAUSED 加全目录连续三次一致加重跑 PASS | FINAL | 活性与稳定性同时满足 | 可作为结论 |

把分级写进报告，不要只写“校验通过/失败”。

## 第 4 步 — 静默后重跑与补丁重定位

0. 在首次 Edit 前，把计划中的每个缺陷对当前字节逐条重定位：`CURRENT`（仍存在，附精确引文或行号）、`ALREADY_FIXED`（当前版本已修）、`GONE`（现象不再出现）、`CHANGED`（现象变了）。任何一条不是 `CURRENT`，先更新计划；不要按旧行号、旧字节数或旧的 `Files (N)` 编辑。等待期间包可能从 2 文件增至 3 文件。
1. 确认 QUIESCENT（`ready` + `activeTurnId: null` + 全包三次一致）或 PAUSED（`waiting-user` + `pendingInteractionCount ≥ 1` + 全包稳定，且用户确认不会回复）；`cold` 出现时同样要三次采样。
2. 重新列出并完整读取 `SKILL.md`、references、脚本，包括等待期间新增的文件；不用之前缓存的版本。
3. 重跑静态验收：

```bash
py -3 "C:/Users/<user>/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$target" \
  --workspace "C:/Users/<user>/Desktop/<project>" --stable-seconds 2 --stability-timeout 30
```

4. 目标 Skill 自带夹具时，按 `replay-skill-reference-fixtures` 重放；记录每条退出码与 `FAILS=`。
5. 把文档中的每个数字与实测对照；不一致时先判断是文档陈旧还是实现变化，再决定改哪一边。
6. 以上全部在同一稳定指纹上成立，才把结论标为 FINAL。

## 第 5 步 — 最小修补（仅在获授权后）

- 以静默版本为基线，先备份到 Skill 目录之外，并为备份记录 SHA-256。
- 首次 `Edit` 前复检：目标当前哈希必须等于基线，连续三次采样一致，且每条计划缺陷仍为 `CURRENT`；不一致就回到第 0 步判活或第 4 步重定位。
- 用最小 `Edit`，一次一个逻辑修改；`old_string` 未命中就重读，不扩大替换范围。
- 采样必须在工具返回之后进行，并记录采样时刻；若新样本的 mtime 早于上一次样本的采样时刻，说明读到的是陈旧状态，重新采样，不要据此判定写入失败或成功。
- 每次 `Edit` 返回后、下一次 `Edit` 前都要复检：记录新的 size、mtime、SHA-256，并与上一次编辑后的预期指纹比较；同时记录 `(tool_use_id, before_sha, after_sha, sampled_at)`。禁止连续多次 `Edit` 而不复检。
- `Edit` 返回 `The file changed since your last read` 是停写信号，不是“已成功所以继续”的许可：立即停止写入，完整读取最新版本，与最近一次备份 diff，列出并发改动并保留，再决定是否继续。
- 目标哈希或 mtime 在两次复检之间变化：立即停写，读取最新全文，与最近备份 diff；确认并发改动已保留后，重新从第 3 步分级。
- 保留写入者的新增段落、参考文件与计数；不因“计划中没有”而删除。
- 补丁涉及 references 时，按同一短语同步。
- 补丁后重跑第 4 步；没有新的稳定 PASS 不宣称修复。

## 报告模板

```text
模式: LIVE-AUDIT（零写入） / ADOPTED（获授权后接管）
目标: <绝对路径>
首次出现: <时间>；当前 mtime 范围: <...>
写入者: <按文件列出 CONFIRMED/ATTEMPTED/INFERRED | 未知>
活性: RUNNING / QUIESCENT / PAUSED / UNKNOWN；依据: <字段、revision 与全包指纹>
采样: <次数>；连续一致: <n>；结论: QUIET / CHANGING
完整性: <文件清单>；<空目录与缺失引用>
分级: <每项观察 -> FINAL / PROVISIONAL / INVALID>
旧结论: <FAIL/PASS、FAILS=0 分别对应哪个版本>
最终重跑: <skill-file-qa 结果、夹具结果、稳定指纹>
写入: <无 | 最小 Edit 列表与前后哈希>
未验证: <未触发分支、仍不确定的内容>
```

## 诊断

| 症状 | 原因 | 动作 |
|---|---|---|
| 预检不存在，写入前出现 | 并发会话创建 | 停写，进入第 0 步判活 |
| 两次采样一致，但参考子目录为空 | 采样窗口落在两次写入之间 | 继续等待；不把“稳定”当“完整” |
| validator 报缺 reference，同时 PASS fingerprint | 引用先写、文件后写；指纹只覆盖 SKILL.md | 标 PROVISIONAL，不修补 |
| `runtimeState: ready` 但文件仍在变 | 回合结束但后处理未完成 | 继续采样到连续三次一致 |
| `wait_chat_sessions` 返回 revision 0 | 该字段是本次返回的状态值 | 用最后一次读取的 revision 判断推进 |
| `wait_chat_sessions` 多次只返回 timeout/turn_completed/needs_attention | `cold` 不是必经状态 | 用 RUNNING/QUIESCENT/PAUSED 三态判定 |
| `waiting-user` 且 `pendingInteractionCount ≥ 1` | 回合暂停等人回复，回复即恢复写入 | 全包稳定且用户确认不回复才可按 PAUSED 编辑；否则继续等 |
| 所有候选的 JSONL 扫描都 0 命中 | cwd 被重置、glob 未展开或扫描目录错 | 用绝对 `--scan-dir`，断言 `files_scanned > 0`；0 文件是扫描失败 |
| 计划中的 `old_string` 不再命中或行号漂移 | 等待期间包被扩展（如 2→3 文件） | 重读并对每条缺陷重定位；用最新 `Files (N)` |
| `Edit` 返回成功但 mtime 早于上次采样 | 采样发生在编辑前或时间戳顺序倒挂 | 以工具返回后的新采样为准，按时间排序，不据此判失败 |
| 同一文件有多个 session 的 Write/Edit | 多写入者 | 逐个归因；最后 `ready` 的会话不等于唯一写入者 |
| 来源会话 `cold`，目标哈希仍变 | cold 只覆盖该会话，其他写入者仍在写 | 按写入者未知处理；零写入，继续采样 |
| `Edit` 返回 changed since last read | 首次读取后版本已被并发改写 | 立即停写，读完最新全文并与最近备份 diff |
| 夹具 `FAILS=0`，参考文件哈希却变了 | 夹具未断言运行期间文件不变 | 静默后重放；不引用这次 `FAILS=0` |
| 静默后 validator 仍 FAIL | 可能是真实缺陷，不是中间态 | 完整读取后判断；获授权再最小修 |
| 会话快照被截断落盘 | 返回超过 token 上限 | 读 `.qoder/tmp/.../tool-results/` 的实际文件 |
| 用户要求“顺手修一下” | 活写入者仍在写 | 拒绝写入；说明静默后重跑，需授权再接管 |

## 完成检查清单

- [ ] 已用 `mcp_get` 核对 `read_chat_session` 与 `wait_chat_sessions` 的实时参数。
- [ ] 已记录 `runtimeState`、`activeTurnId`、`revision`、`hasMoreBefore`，并二次读取比较 revision。
- [ ] 已记录 `wait_chat_sessions` 的实际 outcome 集合；没有把 `cold` 当唯一终点。
- [ ] 写入者活跃期间目标目录零写入，未修补任何中间态 FAIL。
- [ ] 已采样全目录（含空目录），并区分 QUIET 与完整。
- [ ] 已按 `SKILL.md`、references、scripts 逐个扫描 JSONL Write/Edit，并断言 `files_scanned > 0`。
- [ ] 多写入者已逐个列出；未把最后 `ready` 的会话当成唯一写入者。
- [ ] 每项旧结论已标注对应版本与 FINAL/PROVISIONAL/INVALID。
- [ ] 首次 `Edit` 前已把每条计划缺陷对最新字节重定位（CURRENT/ALREADY_FIXED/GONE/CHANGED），并用最新 `Files (N)`。
- [ ] 静默后已完整重读、重跑校验与夹具，并在同一稳定指纹上取得 FINAL。
- [ ] 已区分“来源会话 cold”与“写入者 cold”，cold 或 waiting-user 后仍至少三次采样目标。
- [ ] 每次 `Edit` 之间已复检指纹；采样都在工具返回后并按时间排序；遇到 `changed since last read` 已停写并 diff。
- [ ] 若做了补丁：已备份、最小 Edit、保留并发内容、补丁后重跑。
- [ ] 报告未把 PROVISIONAL 写成已通过，未把文件存在写成 Skill 已加载。

## 已验证案例（2026-10-26，会话 6f896eb6）

目标是 `probe-cli-args-beyond-msys-rewrite`，由另一会话 41c1eeca 创建。以下为实际读到的输出，完整引文见 `references/preuves-session.md`。

1. 12:27 同一命令中，`ls` 先报目标不存在，随后又列出了目标内的 `print_argv.py`（位于其 scripts 子目录）：目录在两次命令之间出现。
2. 来源会话读取为 `runtimeState: running`、`activeTurnId: 778965d0…`，revision 从 10 递增到 17、20、25；最后一条 assistant 正文写着“Creating the directory and the script first”。
3. 12:28:07 脚本 75 B、12:28:17 缓存 386 B、12:28:33 `SKILL.md` 8830 B（sha `8a7361cc…`）依次落盘；12:28:41 与 12:28:45 两次采样完全一致，但参考子目录为空。
4. 该版本上 `validate_skill.py` 为 8 PASS / 1 FAIL：`FAIL local reference not found: 'references/msys-argv-probe.md'`，同时 `PASS fingerprint: unchanged during validation`。这证明“校验期间未变”与“包已完整”是两件事。
5. 12:29:38 参考文件 8871 B 出现；12:31:08 `SKILL.md` 8896 B（`8b9e882f…`）、参考 9006 B（`fa72f092…`），三次采样一致，validator 9 PASS / 0 FAIL。
6. 12:31 起运行的夹具报 `FAILS=0`，但同一输出里参考文件由 `f328fbe9…` 变为 `fa72f092…`，运行期间仍被改写。
7. 用户两次回复“选 A，开始执行”后，`wait_chat_sessions` 返回 `outcome: idle`、`runtimeState: cold`、`revision: 0`。
8. 冷后三次稳定采样，validator PASS；随后只做 3 组最小 Edit（共 5 次调用）：PowerShell 引用形式的限定、`MSYS2_ARG_CONV_EXCL='/'` 仅作诊断、补上直接来源会话与归因。最终 `SKILL.md` 9221 B（`44aaa342…`）。

这组数字只是历史证据，不表示当前状态。

## 已验证案例（2026-10-26，会话 19c5cba9）

目标是 `verify-skill-runtime-binding`，创建者会话 2b9c94c1 已 `cold`。用户授权两处最小更新后，文件仍被其他写入者推进：

1. 15:24:30 备份时 13,262 B，sha `428ae219…`，mtime 14:02:27。
2. 随后连续 3 次 `Edit` 全部成功；第一次返回 `The file changed since your last read…`。
3. 15:24:58 目标 14,389 B，sha `c22b8246…`；diff 显示 description 被并发改写。
4. 15:25:23 再变为 `dd9de37d…`。
5. 创建者会话最后活动在 14:03（本地），15:25:42 读取为 `runtimeState: cold`、`activeTurnId: null`、`revision: 0`；而 15:24:58–15:25:28 的写入来自其他写入者：来源 cold 不排除其他写入者。
6. 15:25:28 起 15,396 B、sha `35a87ee9…`，连续三次采样一致；最终 validator PASS。

教训：若在第一次 `Edit` 的 `changed since last read` 后就停写并 diff，两次额外 `Edit` 就不会落在活版本上。完整引文见 `references/preuves-session.md`。

## 已验证案例（2026-10-26，会话 52ce9bcb）

目标 `auditer-nettoyer-temp-qoder` 由会话 `a32c772d` 并发创建。用户选择「等结束后最小修复」，本会话在写入者活跃期间零写入。

1. 16:45:06–16:47:20Z，`a32c772d` 写入 `SKILL.md` 与参考文件并做 4 次 `Edit`；16:47:18Z 的 QA 为 PASS，但参考文件在 16:47:37Z 又被改写，所以该 PASS 只能标 PROVISIONAL。
2. `wait_chat_sessions` 依次返回 `timeout`（running，revision 12）、`timeout`（running，revision 18）、`turn_completed`（ready，revision 23）；之后对 `a55b50cd` 返回 `turn_completed`（ready，revision 24/31），对 `80685b8f` 返回 `needs_attention`（waiting-user，`pendingInteractionCount: 1`，revision 22/34），对 `464ffdea` 返回 `turn_completed`（ready，revision 109）。整个会话没有出现 `cold`。
3. 用 `scan_skill_writers.py` 复扫项目 JSONL：同一 `SKILL.md` 有 5 个写入者、25 次 Write/Edit（`a32c772d`、`a55b50cd`、`80685b8f`、`464ffdea`、`52ce9bcb`），其中 `80685b8f` 在 16:51:19Z 有一次 ERROR；参考文件另有 4 个写入者、7 次命中，脚本文件由 `464ffdea` 写入 6 次。最后变为 `ready` 的 `a32c772d` 不是唯一写入者。
4. 计划中的两处缺陷基于 15,237 B / 2 文件；等待期间包变为 18,131 B / 3 文件（新增 `inventorier_tmp_qoder.py` 脚本，14,299 B），参考文件 21,030 B。最终补丁改为对 18,131 B 版本重定位后执行。
5. 17:03:03–17:03:20Z 本会话做 4 次最小 `Edit`；18,838 B 版本 QA 为 3 文件 `RESULT PASS`；提交 `a56b906` 只含 `SKILL.md`，6 行新增、2 行删除，工作区与 HEAD blob 均为 `1732fd66…`。
6. 另一次引用检索因 Bash 调用重置 cwd，`*/*.jsonl` 对 4 个候选都命中 0；改用绝对路径后同一候选命中 11–14。空扫描不能当「无写入者」。

完整引文见 `references/preuves-session.md`。

## 资源

- `references/preuves-session.md`：逐字证据、采样输出、分级判定与会话时间线。
