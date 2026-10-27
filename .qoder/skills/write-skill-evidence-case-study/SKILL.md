---
name: write-skill-evidence-case-study
description: "撰写 Skill 的「已验证案例」与 references 证据档案：只采用落盘快照中可复核的字段与原文，把结论分为已核实、推断、未验证；活性字段只证明会话在活动，不证明写入回合仍活动；推荐数据中未被快照证明的状态必须显式降级；时间标注时区，消息用 UTC、工具输出用本地偏移；正文哈希用前缀并绑定字节数与日期，证据档案用完整 SHA-256；写入后重跑 skill-file-qa，并分别记录目标 SKILL.md 与 references 的哈希，因为校验器指纹只覆盖 SKILL.md；校验命令必须替换为目标 Skill 路径，比较 hasMoreBefore 须固定 turnLimit，逐字命令从项目 JSONL 的 tool_use.input 与 tool_result 配对取得。用于补充案例、撰写 cas- 开头的证据文件、纠正二手摘要、区分暂定与最终结论、避免反引号把别家脚本路径误判为本地引用等场景；不替代来源取证（audit-session-evidence）、逐字提取（extraire-preuves-session-qoder）、并发写入（skill-update-concurrency-safe）或夹具重放（replay-skill-reference-fixtures）。关键词：已验证案例、证据档案、已核实、推断、未验证、UTC、本地时间、哈希前缀、版本绑定、推荐数据降级、references 命名、指纹只覆盖 SKILL.md、QA 重跑、local reference not found、turnLimit、hasMoreBefore、tool_use.input、目标路径。"
---

# 撰写 Skill 的已验证案例

## 目标与边界

把一次已验证的创建或更新过程写成两类产物：

1. `SKILL.md` 的「已验证案例」节：短，5–9 条，让读者不打开参考文件也能抓住事实链。
2. `references` 下的证据档案：长，保留逐字输出、失败版本、时间线与分级依据。

本 Skill 只负责**写作与版本绑定**，不替代以下流程：

- 来源会话取证与意图归属：`audit-session-evidence`；
- 截断会话的 JSONL 逐字提取：`extraire-preuves-session-qoder`；
- 写入后的静态验收：`skill-file-qa`；
- 并发写入、备份与最小 Edit：`skill-update-concurrency-safe`；
- 夹具重放：`replay-skill-reference-fixtures`；
- 实时创建中的活性分级：`audit-skill-during-live-creation`。

不新建脚本：证据来自快照、工具输出与磁盘文件，校验用现有 Skill。

## 触发条件

- 新 Skill 通过验收，需要把过程写成案例；
- 已有案例只有结论，没有可复核的数字；
- 推荐数据、二手摘要或上一轮报告含快照未证明的状态；
- references 里有实测输出，但说不清对应哪个版本；
- 用户要求“把这次的验证过程写成案例”或“补证据文件”。

## 不可协商约束

1. **只写可复核的字段与原文。** 每条事实必须能指到快照字段、工具输出原文或磁盘文件；指不到的降为推断或删除。
2. **活性字段只证明会话在活动。** `runtimeState: running` 加非空 `activeTurnId` 不证明写入回合仍在运行；先确认该回合对应用户请求。写入轮已 `completed` 时，不得写“写入者仍在写”。
3. **推荐数据是线索，不是证据。** 未被快照证明的状态必须显式写出“未证明、已降级”；不得静默采纳，也不得为了叙事顺畅删掉修正记录。
4. **时间必须带时区。** 消息时间戳为 UTC（带 `Z`），工具输出为本地偏移（如 `+01:00`）；同一表格不混用，换算时写明关系。
5. **哈希分两档。** 正文用 8 位前缀加字节数与版本时间；证据档案用完整 64 位。前缀不是可复算哈希，不得与完整值混写。
6. **写入后重跑 QA，并分开记录哈希。** validator 的 stability 与 fingerprint 只覆盖 `SKILL.md`；references 的哈希必须单独记录，`RESULT PASS` 不代表参考文件内容已校验。
7. **正文不把别家 Skill 的脚本路径单独放进反引号。** 校验器会把以 scripts、references、assets 加斜杠开头的反引号 token 当成本地引用；安全写法与探针方法见 `skill-update-concurrency-safe`。
8. **校验目标是案例对应的 Skill。** 第 6 步命令中的目录必须替换为目标 Skill；运行后核对 `Skill: <名称>` 与目标目录名一致、`Files (N)` 含该案例的 references。对正在写案例的本 Skill 运行得到 `RESULT PASS`，不能当作另一个 Skill 的结果。
9. **只在相同窗口下比较 `hasMoreBefore`。** `turnLimit`、`includeToolOutputs` 与 `maxOutputCharsPerItem` 是读取参数；`turnLimit=20` 的 `false` 与 `turnLimit=1` 的 `true` 不证明历史丢失。把窗口与值一起记录。
10. **工具输入不是快照字段。** `messages[].tools` 只有 `name` 与 `status`；逐字命令须从项目 JSONL 的 `tool_use.input` 取得，并按 `tool_use_id` 与 `tool_result` 配对。助手转述或输出中出现的命令只能算二手引用。

## 第 0 步 — 建立来源清单

| 字段 | 记录内容 | 用途 |
|---|---|---|
| `sessionId` | 来源会话 ID | 追溯与重读 |
| `revision` | 读取时的值；二次读取比较是否递增 | 判断结论是否过期 |
| `runtimeState` | running / ready / cold | 活性 |
| `activeTurnId` | ID 加该回合的用户请求原文 | 区分写入轮与后续轮 |
| `turnLimit` | 读取时传入的轮数 | 判断两次读取是否可比 |
| `includeToolOutputs` / `maxOutputCharsPerItem` | 读取时的值 | 复现内容边界 |
| `hasMoreBefore` | true / false，仅同一窗口可比 | 是否覆盖完整历史 |
| 落盘文件 | `.qoder/tmp/.../tool-results/` 的实际路径 | 逐字引用来源 |
| 被引用产物 | 路径、size、mtime、完整 SHA-256 | 版本绑定 |

- 记录读取时间；返回超过约 25k token 时读落盘文件，不反复重试同一调用。
- 不把 `messages[].text` 的合并推理文本当作工具输出原文。
- 同一会话在写作前后各读一次；`revision` 变化时重核受影响的事实。
- 两次读取的 `turnLimit` 或预算不同时，分别记录各自的值与 `hasMoreBefore`；不得写“历史丢失”或“历史已补全”。

## 第 1 步 — 提取逐字证据

- 只引用工具输出原文、错误行、退出码与文件指纹；引文取自落盘文件，不取自摘要。
- 每个数字绑定版本：`size`、`mtime` 与时区、`sha256` 前缀。
- 失败与成功都保留原文：`FAIL` 行、`PASS` 行、`EXIT=`。
- 不复制“已修复、已通过”的摘要措辞，除非有对应输出行。
- 命令原文不在 `read_chat_session` 快照的 `tools` 数组中；若快照正文或工具输出没有逐字给出，定位项目 JSONL：`.qoder/projects/<项目>/<sessionId>.jsonl`，收集 `message.content[].type == "tool_use"` 的 `id`、`name`、`input`，再按 `tool_use_id` 与 `tool_result` 配对。不要引用助手的转述。
- 命令若只是某次工具输出里被打印出来的文本，仍按“输出中的引用”处理，不能冒充 `tool_use.input`。

## 第 2 步 — 三级分级

| 分级 | 判据 | 案例中允许的动词 |
|---|---|---|
| 已核实 | 快照字段、工具输出原文或磁盘文件可直接复核 | “为、返回、落盘、报、退出” |
| 推断 | 多条线索一致，但没有直接记录 | “推断、很可能、未直接证明” |
| 未验证 | 未运行、未触发、环境不允许或缺少输出 | “未验证、未复现、未覆盖” |

- 一个事实只占一级；升级需要新证据，不靠措辞。
- 推荐数据中的状态默认按“未证明”处理，除非快照有对应字段。
- `SKILL.md` 的 `RESULT PASS` 只对当时版本的 `SKILL.md` 成立；参考文件另行分级。

## 第 3 步 — 决定放哪里

| 内容 | `SKILL.md` 案例 | references 证据档案 |
|---|---|---|
| 结论事实链 | 5–9 条，可独立读懂 | 可重复，但必须一致 |
| 逐字输出块 | 只留关键一行 | 完整保留 |
| 时间线 | 只留转折点 | 全量 |
| 失败版本与被取代值 | 一句提及 | 保留，不删历史 |
| 分级明细 | 指向档案 | 完整表格 |
| 更正记录 | 一句 | 原断言、实测、修正位置 |

- `SKILL.md` 末尾必须用反引号引用该档案的相对路径。
- 同一数字在 `SKILL.md` 只出现一次，避免多处漂移。

## 第 4 步 — references 命名

格式：`cas-<sujet>-<YYYY-MM-DD>.md`

| 组成 | 规则 |
|---|---|
| `cas-` | 固定前缀，表示不可变案例档案 |
| `<sujet>` | 小写 kebab-case、仅 ASCII、2–4 个词，描述案例主题 |
| `<YYYY-MM-DD>` | 案例发生日期（UTC），不是写入日期 |
| 扩展名 | `.md`；中文译本用 `cas-<sujet>-<YYYY-MM-DD>-zh.md` |

- 跨日案例取关键失败或结论日，并在文内说明时间范围。
- 一个案例一个文件，写入后视为不可变；新案例新增文件，不改旧文件。
- 必须更正旧文件时，追加 `## 更正（YYYY-MM-DD）` 段落并保留原文，不重写历史数字。
- 禁止：空格、大写、本地化日期、`latest` 或 `final` 后缀、README 或 CHANGELOG。
- 文件头写**被引用产物**的完整 SHA-256、size、mtime；本文件自身的哈希不写在文件内（自指会立刻失效），由写入后的报告与目录快照记录。
- `SKILL.md` 引用本 Skill 自己的 references 路径是合法本地引用；不要引用别家 Skill 的 references 或 scripts 相对路径。

## 第 5 步 — 写作规范

- 标题后写案例日期与时区；时间线表标题注明“本地时间”或“UTC”。
- 哈希写法：正文 `241b7594…` 加 `13212 B` 加 `13:41:42+01:00`；档案内用完整 64 位。
- 暂定结论不写“已通过”，只写“当时通过、仅对某版本成立”。
- 其他 Skill 的脚本写成“某 Skill 的 scripts 目录中的脚本”，不单独加反引号。
- 修正记录用三元组：原断言、实测输出、修正位置。
- 环境版本只在有输出时写；二手版本标注“二手”。

## 第 6 步 — 写入后验证

```bash
SKILL_CIBLE="C:/Users/Administrateur/.qoder/skills/REMPLACER-PAR-LE-SKILL-CIBLE"
[ -f "$SKILL_CIBLE/SKILL.md" ] || { echo "TARGET_MISSING"; exit 2; }
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "$SKILL_CIBLE" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" \
  --stable-seconds 2 --stability-timeout 30
```

1. 先替换 `SKILL_CIBLE`；不要对正在写案例的本 Skill 运行后把结果当成目标 Skill 的结果。
2. 要求 `RESULT PASS`，核对 `Skill:` 等于目标目录名、`Files (N)` 含本案例的 references、本地引用与跨 Skill 引用数。
3. 独立回读：无 BOM、YAML 可解析、`name` 与目录同名、description 单行、正文少于 500 行。
4. 分别对目标 `SKILL.md` 和每个 references 运行 `sha256sum`，记录 size 与 mtime；间隔数秒复采样确认稳定。validator 的 `Fingerprint` 只覆盖 `SKILL.md`，不覆盖 references。
5. 把案例中的每个数字与来源快照逐项对照；不一致时改文档，不改历史输出。
6. 确认目标目录没有 `__pycache__`、临时夹具或多余文档。
7. 若目标文件在 PASS 后再次变化，旧 PASS 只对旧哈希成立；重新运行并记录新哈希。

## 已验证案例（2026-10-26，会话 09829df8）

目标产物是 `audit-skill-during-live-creation`。以下为实际读到的输出，完整引文与指纹见 `references/cas-live-creation-2026-10-26.md`。

1. 初版 `SKILL.md` 13155 B（`793fb437…`）被 validator 判 `FAIL local reference not found`，8 PASS / 1 FAIL，`EXIT=1`；原因是正文把别家 Skill 的脚本路径单独放进了反引号。
2. 改为不带该前缀的叙述后，13180 B（`7e0ba929…`），9 PASS / 0 FAIL，`EXIT=0`。
3. 最终 `SKILL.md` 13212 B（`241b7594…`）在 13:41:42+01:00 取得 `RESULT PASS`；参考文件在 13:41:54 为 7876 B（`22eb8caa…`），13:42:25 变为 7909 B（`001fbb02…`），此后未再运行 validator。
4. 读取来源快照时 `runtimeState: running`，但其 `activeTurnId` 对应后续“列出当前所有已安装的 Skill”回合，创建轮已 `completed`；因此推荐数据中的“Edit running”未被快照证明，案例把它降为推断。
5. 结论：`SKILL.md` 的 PASS 与参考文件最终版不是同一时刻；两者的哈希必须分开记录。

这些数字只对应上述版本；参考档案文件头记录的是 13:51+01:00 的实测值，不代表当前磁盘状态。

## 诊断

| 症状 | 原因 | 动作 |
|---|---|---|
| validator 报 `local reference not found`，token 以 scripts 等开头 | 别家脚本路径被单独反引号 | 改叙述；按 `skill-update-concurrency-safe` 建探针确认 |
| 推荐数据称“仍在运行、Edit running” | 快照只有 `runtimeState` 等字段 | 记录 `activeTurnId` 对应请求，降级为推断 |
| 同一表格混用 `Z` 与 `+01:00` | 时区未分列 | 分列或写明换算 |
| 正文 8 位前缀被当成完整哈希 | 两档混写 | 补字节数与时间；档案用完整值 |
| validator PASS 后又改了 references | 指纹只覆盖 `SKILL.md` | 单独记录参考文件哈希，不宣称全包通过 |
| 案例数字与档案不一致 | 版本漂移 | 以原文为准改案例 |
| 新案例复用旧文件名 | 覆盖历史 | 按日期新建文件 |
| 文件内写自身 SHA-256 | 自指失效 | 只写被引用产物哈希，自身哈希放报告 |
| validator 报 `Skill: write-skill-evidence-case-study`，但案例属于另一个 Skill | 未替换 `SKILL_CIBLE` | 用目标路径重跑；核对 `Skill:` 与 `Files (N)` |
| `hasMoreBefore` 从 false 变 true | 两次读取的 `turnLimit` 不同 | 固定窗口重读，或并列记录两值 |
| 命令在快照中找不到 | `tools` 只有名称与状态 | 从项目 JSONL 的 `tool_use.input` 取得，按 `tool_use_id` 配对 |
| PASS 后目标文件哈希变化 | validator 只覆盖当时版本 | 重新运行并记录新哈希，不沿用旧 PASS |

## 完成检查清单

- [ ] 来源清单含 sessionId、revision、runtimeState、activeTurnId 与对应请求、turnLimit 与预算、hasMoreBefore、落盘路径。
- [ ] 每条事实有原文或指纹；推断与未验证已单独分级。
- [ ] 活性字段没有被写成“写入轮仍在运行”。
- [ ] 推荐数据中未证明的状态已显式降级并保留修正记录。
- [ ] 时间带时区，表格没有混用 UTC 与本地偏移。
- [ ] 正文前缀哈希含字节数与时间；档案使用完整 64 位。
- [ ] 文件名符合 `cas-<sujet>-<YYYY-MM-DD>.md`，日期为案例日 UTC。
- [ ] 没有把别家 Skill 的脚本路径单独放进反引号。
- [ ] 第 6 步使用目标 Skill 路径；validator 的 `Skill:` 与目录一致。
- [ ] 目标 `SKILL.md` 与 references 的哈希分别记录；PASS 只对应所验证版本。
- [ ] 只在相同 `turnLimit` 窗口下比较 `hasMoreBefore`。
- [ ] 逐字命令取自 JSONL 的 `tool_use.input`，并与 `tool_result` 按 ID 配对。
- [ ] 文档数字与来源快照逐项一致，当前磁盘状态已标注。

## 资源

- `references/cas-live-creation-2026-10-26.md`：逐字输出、最终文件指纹、分级与更正记录。
- 取证与提取：`audit-session-evidence`、`extraire-preuves-session-qoder`。
- 校验与写入：`skill-file-qa`、`skill-update-concurrency-safe`。
- 夹具与实时创建：`replay-skill-reference-fixtures`、`audit-skill-during-live-creation`。
