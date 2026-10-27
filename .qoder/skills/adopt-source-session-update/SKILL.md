---
name: adopt-source-session-update
description: "当更新 Skill 的任务引用来源会话、且目标目录可能已被该来源或其他会话写入时，先只读比对来源计划与磁盘/HEAD：有界读取 read_chat_session 并记录 runtimeState、status、revision、失败空回合与用户重发；把每处计划改动映射为 CURRENT/ALREADY_APPLIED/PARTIAL/ABSENT/CONFLICT；扫描 JSONL 成功 Write/Edit 归因写入者，用 wait_chat_sessions 与两轮 4×5 秒全包采样守门；改动已就位时采纳现有字节而不重复应用，只对缺口做最小 Edit，写入者仍活动时零写入并报告 STOP；随后独立重跑 skill-file-qa、双语对等、Files(N) 与真实入口。用于来源会话已写好同一更新、确认方案后发现文件已变、计划锚点已存在、避免覆盖并发新增、部分应用、HEAD 未变但工作区已改、需要采纳加独立验收。不用于同名重复 Skill 的接管决策（改用 adopt-concurrent-duplicate-skill）、目标中途出现后的活性分级（audit-skill-during-live-creation）或通用采样机制（skill-update-concurrency-safe）。关键词：来源会话、采纳、已应用、锚点对账、部分应用、写入者门禁、4×5 秒采样、零写入、独立验收、STOP、ADOPT-GAP。"
---

# 采纳来源会话已应用的 Skill 更新

## 目标与边界

本 Skill 处理一个决策点：任务要求按来源会话更新 Skill，但目标目录可能已经由该来源会话或另一会话写入了同一批改动。先证明「计划是否已在磁盘/HEAD 上」，再决定采纳、补齐或停止；不重复应用，不覆盖并发新增。

不替代以下流程：

- `skill-update-concurrency-safe`：采样、备份、最小 Edit 与 QA 的通用机制；
- `audit-skill-during-live-creation`：RUNNING/QUIESCENT/PAUSED 活性判定与证据分级；
- `adopt-concurrent-duplicate-skill`：同名或职责重合 Skill 的接管决策；
- `verifier-reecriture-concurrente-paquet-skill`：QA 后漂移的 JSONL 重建；
- `audit-session-evidence`：来源会话的完整取证与原始日志核对；
- `skill-file-qa`、`bilingual-skill-parity`：写入后的静态与对等验收。

## 触发条件

- 任务明确引用一个来源会话，要求按其结论更新现有 Skill；
- 确认方案后，目标 `SKILL.md`、references 或脚本的 size、mtime 或 SHA-256 已变化；
- 计划中的唯一短语、标题或命令已在目标文件中出现；
- `git status` 已有未提交改动，或 `HEAD` 未变但工作区已改；
- 来源会话本身可能仍是写入者，或其他会话正在写同一个包；
- 用户要求「不要重复改」「先看是不是已经写好了」「采纳 + 验收」。

## 不可协商约束

1. **先只读，后决策。** 对账完成前不建目录、不写文件、不删除、不重命名。
2. **不重复应用。** 计划改动已是 `ALREADY_APPLIED` 时，采纳现有字节；不得为了「执行计划」再写一遍。
3. **不整文件重写。** 只对 `ABSENT` 或 `PARTIAL` 的缺口做最小 `Edit`；旧全文 `Write` 会覆盖并发新增。
4. **写入者活动时零写入。** 任一写入者处于 RUNNING，或全包采样未连续一致，报告 `STOP`。
5. **不复用他人的 PASS。** 来源会话或另一会话的 QA、对等、文件清单只能作为线索，最终结论必须在本会话重跑。
6. **区分证据等级。** 来源会话报告、二手摘要、本会话实测分开写；未执行的分支写「未验证」。
7. **采纳不等于验收。** 字节已就位只证明「不需要重写」，不证明格式、引用、双语或运行时正确。

## 第 0 步 — 有界读取来源会话

1. 先用 `mcp_get` 取 `read_chat_session` 的实时 schema；本机实测必填 `sessionId`，`turnLimit` 为 1–20，`includeToolOutputs` 默认 false，`maxOutputCharsPerItem` 为 200–8000。
2. 首次读取用 `turnLimit: 20`、`includeToolOutputs: false`；需要命令原文或错误时再开 `includeToolOutputs: true`。
3. 返回超过约 25k token 时会落盘到 `.qoder/tmp/.../tool-results/`；读该文件，不重复同一调用。
4. 记录 `runtimeState`、`activeTurnId`、`revision`、`hasMoreBefore`、`pendingInteractionCount`。
5. 逐回合记录：
   - 用户消息原文与时间；
   - assistant 回合 `status`（`completed` / `failed`）；
   - `failed` 且正文为空表示未执行，不等于已写入；
   - 用户重复同一句确认时，先判断是重发还是方法纠正；
   - 工具调用顺序，尤其是写文件、`Edit`、`git` 与 QA。
6. 把来源结论分成三类：`OBSERVED`（会话内读到的工具输出）、`REPORTED`（assistant 叙述或引用其他会话）、`UNVERIFIED`（没有输出支撑）。只有 `OBSERVED` 可以直接当基线。
7. 读取结束后写出「来源计划清单」：文件、锚点短语、预期改动、来源回合、证据等级。没有清单不进入对账。

## 第 1 步 — 来源计划与磁盘/HEAD 对账

### 1.1 记录当前状态

```bash
target="$HOME/.qoder/skills/<skill-name>"
cd "$target" 2>/dev/null && {
  git status --short
  git rev-parse --abbrev-ref HEAD
  git rev-parse HEAD
  git rev-parse origin/main 2>/dev/null || true
  git merge-base HEAD origin/main 2>/dev/null; echo "MERGE_BASE_EXIT=$?"
}
find "$target" -maxdepth 3 -type f -exec sha256sum {} + | sort
```

- `MERGE_BASE_EXIT=1` 且无输出表示无共同祖先；不要用 `git merge` 或 `--allow-unrelated-histories` 代替诊断。
- 记录每个文件的 size、完整 `mtime` 与 SHA-256；只记录 `SKILL.md` 不足以判断 references 与脚本。
- 区分「已安装副本」与「仓库工作区」：两者可能是不同目录。

### 1.2 逐条映射计划

对来源计划中的每处改动，取一个唯一短语（标题、命令、错误原文或计数句），在磁盘与 HEAD 上检索：

```bash
grep -RFn -- "$anchor" "$target" || true
git -C "$target" grep -n -F -- "$anchor" HEAD -- . 2>/dev/null || true
```

分类：

| 分类 | 判据 | 允许动作 |
|---|---|---|
| `CURRENT` | 锚点存在，且内容与计划一致 | 不写 |
| `ALREADY_APPLIED` | 整处改动已存在，行号可与来源基线不同 | 采纳；记录新行号 |
| `PARTIAL` | 同一改动只落了一部分，例如只改 `SKILL.md` 未同步中文 | 只补缺口 |
| `ABSENT` | 找不到锚点 | 静止后按计划最小新增 |
| `CONFLICT` | 锚点存在但语义被改成另一种规则 | 停止并报告，不覆盖 |

- 行号漂移不是命中依据；按唯一短语与上下文判断。
- 同步检查来源计划新增的参考文件、脚本与资源是否已落盘。
- 双语 Skill 要逐侧检查：法文存在不代表中文镜像存在。
- 对账结果写成表：`计划项 | 来源回合 | 磁盘位置 | HEAD 位置 | 分类 | 证据`。

### 1.3 来源基线不可得时

- 来源会话只给了摘要、没有原始输出：把计划项标 `UNVERIFIED`，只做存在性判断，不声称字节一致。
- 来源会话已 `cold` 但目标已变：以当前磁盘为唯一基线，来源计划只作为需求清单。
- 无法确定某处是否已应用：按 `CONFLICT` 处理，停止并报告。

## 第 2 步 — 写入者与稳定性闸门

本节复用 `audit-skill-during-live-creation` 的活性三态与 `skill-update-concurrency-safe` 的采样机制。

1. **归因写入者。** 对包内每个文件扫描项目 JSONL 的成功 `Write`/`Edit`，用 `tool_use_id` 与 tool_result 配对；失败的 `Edit` 只算 `ATTEMPTED`。可用 `verify-injected-skill-body-freshness` 的只读脚本，逐个 `--target` 运行；断言扫描文件数大于 0，空扫描不等于无写入者。
2. **等待。** 对每个写入者调用 `wait_chat_sessions`，记录 `outcome`、`runtimeState` 与 `revision`；`cold` 可能不出现，`ready` 不是终态。
3. **全包采样。** 对目录内全部文件计算聚合指纹（路径、size 与 SHA-256 排序后再哈希），两轮各 4 次、间隔 5 秒，要求连续 4 次一致。
4. **观察原子写。** 出现 `*.tmp.*`、锁文件或编辑器备份时，说明写入正在替换文件；该轮采样作废。
5. **判定。**
   - 任一写入者 RUNNING、`revision` 递增、聚合指纹变化或临时文件出现 → `STOP`，零写入，30–60 秒后重试，最多两轮。
   - `ready` 加 `activeTurnId: null` 加连续 4 次一致 → `QUIESCENT`。
   - `waiting-user` 加 `pendingInteractionCount ≥ 1` 加全包稳定 → `PAUSED`；未确认用户不会回复时按潜在写入者处理。
6. **每次 Edit 前复检。** 当前哈希必须等于决策时的基线；不一致就回到第 1 步重新对账，不沿用旧分类。

## 第 3 步 — 采纳决策

| 对账结果与闸门 | 决策 | 动作 |
|---|---|---|
| 全部 `CURRENT`/`ALREADY_APPLIED` 且 QUIESCENT/PAUSED | `ADOPT` | 零写入；直接进入独立验收 |
| 存在 `PARTIAL` 或 `ABSENT` 且 QUIESCENT/PAUSED | `ADOPT-GAP` | 备份后只对缺口做最小 `Edit`；不改已应用部分 |
| 存在 `ABSENT`，写入者曾报告但未落盘 | `REAPPLY` | 先确认是同一版本基线，再按计划新增 |
| 存在 `CONFLICT` | `STOP` | 报告冲突锚点与两侧内容，等待用户决定 |
| 任一写入者 RUNNING 或采样不一致 | `STOP` | 零写入；列出写入者、revision 与采样序列 |

- `ADOPT` 也必须向用户说明「本轮没有写入」，不要把采纳写成「已更新」。
- `ADOPT-GAP` 的缺口若涉及双语镜像，两侧必须同批修改；只改一侧会使对等校验失败。
- 不因为来源计划写了 7 处，就必须产生 7 次写入；已应用的数量要如实报告。
- 用户未确认前，`REAPPLY` 与任何覆盖 `CONFLICT` 的动作都不执行。

## 第 4 步 — 独立验收

1. **重读实物。** 完整读取 `SKILL.md`、相关 references、翻译版与脚本；记录 size、`mtime_ns` 与 SHA-256；确认 `M` 与 `??` 文件属于谁。
2. **静态验收。** 用 `py -3` 运行 `skill-file-qa`，要求稳定指纹上的 `RESULT PASS`；记录实际 PASS/FAIL/WARN、`Files (N)`、`Code blocks`、本地引用与跨 Skill 引用。
3. **双语对等。** 存在翻译版时运行 `bilingual-skill-parity`；单语明确写「不适用」。
4. **真实入口。** 按目标 Skill 的默认或只读模式运行一次；会写盘的 `--persist`、`run`、`--avec-*` 分支不执行。
5. **文件清单。** 对照来源计划与磁盘清单：新增文件是否都在、是否多出缓存或临时文件、`Files (N)` 是否与预期一致。
6. **加载状态。** 新写或重写的 Skill 可能不在当前加载列表；`Skill` 工具调用成功不等于列表已刷新。不能执行 `/skills reload` 时，报告「需重启会话或重载」，不宣称已加载。
7. **复检。** 验收结束后再次采样；QA 之后有写入则旧 PASS 作废，重跑第 2 至第 4 步。

## 报告模板

```text
模式: ADOPT（零写入） / ADOPT-GAP（最小 Edit） / REAPPLY / STOP
目标: <绝对路径>
来源会话: <sessionId>；runtimeState / revision / hasMoreBefore；消息数
来源证据: OBSERVED / REPORTED / UNVERIFIED 各多少条
计划清单: <N 项>
对账: CURRENT <n> / ALREADY_APPLIED <n> / PARTIAL <n> / ABSENT <n> / CONFLICT <n>
写入者: <sessionId、成功写入次数、wait 结果 | 未知>
采样: <轮数、次数、连续一致数、聚合指纹序列>
判定: QUIESCENT / PAUSED / RUNNING
采纳来源: <sessionId 或「另一会话，未独立读取」>
写入: <无 | 最小 Edit 列表与前后哈希>
独立验收: skill-file-qa EXIT + PASS/FAIL/WARN；Files (N)；对等 n/n 或不适用
加载状态: 已加载 / 需重载 / 未验证
未验证: <未执行分支与原因>
```

## 诊断

| 症状 | 原因 | 动作 |
|---|---|---|
| 计划中的锚点已存在 | 来源会话或另一会话已应用 | 标 `ALREADY_APPLIED`，采纳，不重复写 |
| 确认后文件又变了 | 并发写入仍在进行 | 回到第 2 步；不沿用旧分类 |
| assistant 回合 `failed` 且正文为空 | 该回合未执行 | 当作未写入；等用户重发或重新规划 |
| 用户连发两次「确认」 | 首次回合失败后的重发 | 不当作两次不同授权；核对实际写入 |
| 来源会话 `cold`，目标仍在变 | `cold` 只覆盖该会话 | 按写入者未知处理，继续采样 |
| `wait_chat_sessions` 永不返回 `cold` | 该状态不是必经 | 用 RUNNING/QUIESCENT/PAUSED 三态 |
| 采样中出现 `*.tmp.*` | 其他会话正在原子替换 | 该轮作废；等临时文件消失后重采 |
| `merge-base` 输出为空、退出 1 | 无共同祖先 | 用 plumbing 或只读对账；不用 `merge` 强合 |
| 只核对了 `SKILL.md` | 指纹与 QA 只覆盖主文件 | 全包记录哈希；逐文件对账 |
| 来源会话报告 QA PASS | 二手结果，可能对应旧版本 | 本会话重跑；不复制 PASS |
| 采纳后目录仍显示 `M` 或 `??` | 改动来自其他会话，未提交 | 如实报告工作区状态；提交需单独授权 |
| 新 Skill 不在加载列表 | 会话启动时注入 | 提示重载或重启，不伪造调用成功 |

## 完成检查清单

- [ ] 已用 `mcp_get` 核对 `read_chat_session` 的实时参数。
- [ ] 已记录来源会话的 `runtimeState`、`revision`、`hasMoreBefore`、消息数与回合状态。
- [ ] 已区分失败空回合、用户重发与方法纠正。
- [ ] 每条来源结论已标 `OBSERVED`/`REPORTED`/`UNVERIFIED`。
- [ ] 已写出「来源计划清单」，每项有唯一锚点。
- [ ] 已记录全包 size、mtime、SHA-256 与 `git status`/`HEAD`/`origin/main`。
- [ ] 每项改动已分类为 `CURRENT`/`ALREADY_APPLIED`/`PARTIAL`/`ABSENT`/`CONFLICT`。
- [ ] 已扫描 JSONL 成功写入并列出全部写入者；空扫描已判定为失败而非「无写入者」。
- [ ] 已执行 `wait_chat_sessions` 并记录 outcome 集合。
- [ ] 已做两轮 4×5 秒全包采样，并检查临时文件。
- [ ] 写入者活动或采样不一致时零写入，报告 `STOP`。
- [ ] `ADOPT` 时没有产生任何写入；`ADOPT-GAP` 时只改缺口。
- [ ] 写入前已备份到 Skill 目录之外（若发生写入）。
- [ ] 已独立重跑 `skill-file-qa` 并记录实际计数与 `Files (N)`。
- [ ] 双语已跑对等；单语标明不适用。
- [ ] 已核对新增参考文件与目录清洁度。
- [ ] 验收后再次采样；QA 后无新写入或已重跑。
- [ ] 报告区分已核实、来源报告、未验证与未执行分支。

## 已验证案例（2026-10-26，会话 ac90ec1e，PARTIAL）

任务要求按来源会话更新 `commit-skill-work`。规划阶段发现另一会话已在 18:09 写入同一批改动，7 个锚点均已就位；代理改为只读对账并计划只补 3 处，用户回复「确认方案 A」。随后并发闸门失败，最终零写入。

- 已核实：`SKILL.md` 48,527 B（`a4e70a69…`，正文 496/500 行）、中文镜像 41,360 B（`4ed59be3…`）、新增参考 12,168 B（`088a2f2f…`）；`HEAD=fe57c7c`、`origin/main=4f18419`、`merge-base` 为空；两轮 4×5 秒采样均未连续一致；写入者 `87644a66`（revision 38）与 `42187622`（revision 56）在两次 60 秒等待后仍为 `timeout + running`。
- 未执行：3 处补强与最终独立验收；原因是闸门未通过，而不是文件冲突。
- 完整时间线、逐字锚点与采样序列见 references 目录下的 `preuves-session-ac90ec1e.md`。数字是历史证据，不表示当前状态。

## 资源

- references 目录下的 `preuves-session-ac90ec1e.md`：会话字段、用户回合、对账锚点、闸门证据与限制。
- `skill-update-concurrency-safe`：采样、备份、最小 Edit 与 QA 的通用机制。
- `audit-skill-during-live-creation`：活性三态、写入者归因与证据分级。
- `adopt-concurrent-duplicate-skill`：同名或职责重合 Skill 的接管决策。
- `verifier-reecriture-concurrente-paquet-skill`：QA 后漂移与 JSONL 重建。
- `audit-session-evidence`：来源会话的完整取证。
- `skill-file-qa`、`bilingual-skill-parity`：静态与对等验收。
- `verify-injected-skill-body-freshness`：写入者扫描脚本与注入新鲜度。
