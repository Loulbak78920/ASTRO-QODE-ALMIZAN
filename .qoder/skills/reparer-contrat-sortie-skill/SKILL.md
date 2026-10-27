---
name: reparer-contrat-sortie-skill
description: "当独立验收报告指出某个 Skill 的 SKILL.md 所记录的输出契约（示例格式块、JSON 键集、退出码、产物文件）与脚本实际行为不符时，在安装目录外复制夹具逐条复放并修复文档：用实测 stdout 原文替换虚构示例，对「声称存在却从未输出」的项用零出现断言加同块正对照（真实存在的段必须出现至少 1 次），把退出码 0 下的假漂移或假结果单列为偏差，把同秒、时序等无法观测的结论降级为人工推断并标注；默认只改 SKILL.md 与 references，脚本哈希保持前后一致，写入后跑 skill-file-qa 并按更新后的文档命令逐字复放、清理夹具、记录最终指纹。不替代 KEY=VALUE 契约核对（verifier-parite-doc-script-skill）、写入前断言分级（verify-skill-doc-claims-before-edit）、既有参考夹具重放（replay-skill-reference-fixtures）或结构验收（skill-file-qa）。中文触发：验收报告、文档与脚本输出不一致、虚构示例、JSON 键集、CLI 选项未文档化、报告行序、detail 行、退出码 0、假漂移、合成夹具、自检 DOC_KEYS/MATCHED、修复后复放；English: acceptance report, doc vs script divergence, documented output contract, zero-occurrence assertion, doc-only fix, replay after fix; Français: rapport d'acceptation, écart documentation/script, contrat de sortie, correction documentaire, rejeu après correction."
---

# 输出契约偏差的文档修复

## 何时使用

- 独立验收会话或报告给出「文档与实测不符」，verdict 为 ACCEPTÉ AVEC RÉSERVES / REFUSÉ，且问题限于文档；
- 文档的示例块、JSON 键集、退出码或产物文件名与实际 stdout 不一致；
- 需要只改文档、不动脚本，把契约修回可复放的状态。

不适用：

- KEY=VALUE 令牌的抽取与存在性核对：`verifier-parite-doc-script-skill`；
- 写入前的断言分级与措辞校准：`verify-skill-doc-claims-before-edit`；
- references 中已有夹具的重放：`replay-skill-reference-fixtures`；
- 结构、引用与指纹验收：`skill-file-qa`；
- 脚本本身缺少键或退出码错误：本 Skill 默认不改脚本，需用户单独决策。

## 核心规则

1. **安装只读。** 夹具复制到 `$HOME/.qoder/tmp/<nonce>/fixture/<同名目录>`，另建空根目录；用 `py -3 -B`；不接触 git 与网络。副本目录名必须与 Skill 相同，否则副本上的 `skill-file-qa` 会报 name 不符。
2. **先冻结再动手。** 记录目标 `SKILL.md` 与脚本目录的 size/mtime/SHA-256，并跑一次基线 `skill-file-qa`；没有基线就无法区分既有失败与本次引入。
3. **偏差台账逐字抄验收报告。** 一条偏差一行：文档原句（文件:行）、实测命令、RC、stdout 原文、类别、修复位置。台账为空则不编辑。
4. **一条偏差一次运行。** 不把多条偏差塞进同一命令；RC 在管道之前取得，避免被 `tail`/`head` 覆盖。
5. **零次出现必须有正对照。** 同一块断言代码里先证明一个真实存在的段出现 ≥1 次，才允许把 0 次写成「从不输出」；正对照失败说明断言本身失效，不是通过。
6. **示例逐字来自实测。** 删除所有手写或「示意」行；时间戳、路径等可变字段保留一次真实取样并注明「换环境须重测」。
7. **退出码 0 不等于契约正确。** 假漂移、假 `removed`、空结果配 RC=0 都算偏差，必须写进失败模式，不得因 RC=0 放过。
8. **不可观测就降级。** 同秒窗口、时序、并发等没有直接观测到的结论写成人工推断并写明依据，不得写「已验证」。
9. **默认只改文档。** 补校验、改退出码等脚本变更由用户单独决定；修改前后脚本 SHA-256 必须一致。
10. **复放按更新后的文档。** 命令从改后的 `SKILL.md` 逐字复制执行，不用记忆或旧稿；断言输出 `<检查名>_TRUE|FALSE` 令牌，不靠人眼比对。
11. **报告分级。** 已复现 / 仅正对照覆盖 / 人工推断 / 未执行；夹具清理、无 `__pycache__`、最终指纹齐全才算完成。

## 偏差分类

| 类别 | 定义 | 本案例实例 | 修复动作 |
|---|---|---|---|
| A 声称存在但从未输出 | 文档展示一段脚本从不打印的输出 | `stability: … \| window: <1 s` | 删除虚构段，改为实测 drift 段 |
| B 行为存在但未文档化 | 模式、键集、CLI 选项、报告行序、detail 行格式或文件结构未写 | JSON 模式 12 个顶层键；`skills[]` 无 description 正文（案例 1）；`--json`/`--doc`/`--script` 三选项、11 个计数字段顺序、5 类 detail 行（案例 2） | 新增小节：选项、行序、detail 格式与键集全部来自实测 |
| C 示例缺参导致假结果 | 示例命令省略参数，照抄复跑得到错误结论 | 异根 compare 得到 `removed: 1`、RC=0 | 文档规定同一组根；写入失败模式 |
| D 产物与提示不一致 | 文件已生成但不打印提示，或反之 | JSON + `--snapshot` 无提示行，文件 939 B（本案例夹具；换根后字节数不同，须重测，本机复测得 979 B） | 写明条件分支；复放同时断言提示次数与文件存在 |

## 流程

### 0. 冻结与基线

```bash
SKILL_CIBLE="C:/Users/Administrateur/.qoder/skills/nom-du-skill"
sha256sum "$SKILL_CIBLE/SKILL.md"
find "$SKILL_CIBLE/scripts" -name "*.py" -exec sha256sum {} + 2>/dev/null
wc -l "$SKILL_CIBLE/SKILL.md"
py -3 -B "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$SKILL_CIBLE" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" --stable-seconds 2 --stability-timeout 30
```

目标 Skill 没有脚本目录时只记录 `SKILL.md`。基线已 FAIL 的先记录，不把本次写入后的 FAIL 归因于新内容。

### 1. 建偏差台账

| ID | 文档原句（文件:行） | 实测命令 | RC | stdout 原文 | 类别 | 修复位置 |
|---|---|---|---|---|---|---|
| A1 | … | … | 0 | … | A | 输出契约 |

验收报告里的每条「écart」都要有对应行；报告没说、但复放中自己发现的偏差另起一行（本案例的 D 类即属此类），并注明发现步骤。

### 2. 复制夹具

```bash
BASE="$HOME/.qoder/tmp/rep-contract-$(date +%Y%m%dT%H%M%S)-$$"
mkdir -p "$BASE/fixture" "$BASE/empty-root" "$BASE/out"
cp -r "$SKILL_CIBLE" "$BASE/fixture/"
```

所有根参数都指向 `$BASE` 内的目录，绝不指向真实用户根，避免把真树差异混进断言。

### 3. 逐条复现

- 每条命令单独执行，保存完整 stdout/stderr 到 `$BASE/out/<ID>.log`，同时记 RC；
- 用副本里的脚本路径，不直接在安装目录执行；
- A 类：在同一断言脚本里同时输出正对照与零出现两项（模板见 `references/harnais-repasse.md`）；
- B 类分五步取证，不把「一个 JSON 键集」当成全部：
  - 键集：打印 `sorted(doc)` 与 `sorted(items[0])`，与文档列出的键做整体集合比较；
  - 选项：跑 `--help`，用 `--[a-z][a-z-]+` 抽出旗标集合，与文档选项表比较；文档提到的选项 0 命中即未文档化；
  - 行序：把计数字段按行取成有序列表（`SKILL` 到 `OUT_OF_SCOPE`）与文档块逐行比较，末尾须为 `RESULT`；集合相同而顺序不同也算偏差；
  - detail 行：按前缀分类 `DOC_ONLY_KEY`/`RUNTIME_ONLY_KEY`/`ALLOWED_KEY`/`OUT_OF_SCOPE_KEY`，断言出现在计数字段之后、`RESULT` 之前并匹配该类格式；用法或环境错误时只发 `ERROR` 且无 `RESULT`；
  - 无失败分支：在 `$BASE` 建最小合成包触发，不改目标脚本。文档写 `GHOST_KEY` 而脚本只发 `REAL_KEY` → `DOC_ONLY=1`、RC=1；文档不提名脚本 → `SCOPE_FALLBACK_ALL=yes`。抽取只认围栏块与行内代码中的大写 `KEY=VALUE`，JSON 小写键不计入。
- C 类：同根与异根各跑一次，记录两次 RC 与计数，证明假漂移可在 RC=0 下出现；
- D 类：`grep -c` 提示行加 `test -f` 产物，两项同时记录。

复现失败（未重现）时改台账，不要为了凑结论删断言。

### 4. 最小编辑

按以下顺序用 Edit 修改，不整文件重写：

1. 删除虚构示例，替换为实测块，保留原围栏语言与缩进；
2. 补未文档化模式的小节：顶层键、条目键、null 形态、产物文件键子集；
3. 示例命令补全必需参数，并注明「必须原样重传同一组」；
4. 失败模式表补行：假漂移、找不到承诺行、JSON 无正文、无提示行；
5. 验收清单补项：根一致性、零出现加正对照、按新文档复放；
6. 每改一处复查 `wc -l`，正文保持 < 500 行，不重排无关段落；
7. frontmatter `description` 只在触发条件本身变化时改；
8. 脚本一行不动；确需改脚本时停下问用户。

### 5. 写入后结构验收

- 双采样后跑 `skill-file-qa`，要求稳定指纹上的 `RESULT PASS`；
- 记录 `Files (N)`、body 行数、description 字符数、`SKILL.md` 新哈希；
- 回读改动行，确认措辞与台账级别一致；
- 文档措辞会被校验器当作引用解析：反引号里的资源目录名（scripts/、references/、assets/）必须真实存在，否则 `FAIL local reference not found`；目标无该目录时写成「脚本目录」等普通措辞，不为过 QA 删掉真实存在的路径引用。该规则对本文档自身同样生效，写说明时也不要反引号包裹裸目录名；
- 回读表格：实测输出含竖线时，单元格内必须写成 `\|`；校验器不解析 Markdown 表格，断表仍报 PASS，只能靠回读，按未转义竖线切分后列数须与表头一致；
- QA 之后文件若再变化，旧 PASS 作废。

### 6. 按新文档复放

从更新后的 `SKILL.md` 逐字复制命令，在 `$BASE` 内执行。至少覆盖下表；每项打印 `<检查名>_TRUE|FALSE`，任一 FALSE 即修复无效：

| 检查 | 断言 |
|---|---|
| JSON 顶层键 | 集合与文档列出的完全相等 |
| `skills[]` | 无 description 正文，只有 `description_sha256`/`desc_chars` |
| 无 compare 时的 drift | 为 `null` |
| 快照文件 | 顶层键等于文档所列 7 键 |
| md 模式快照 | `snapshot written:` 出现 1 次 |
| JSON + 快照 | 提示 0 次且文件存在 |
| 正常 compare | 段头、计数行、`- no drift detected` 逐字匹配 |
| 异根 compare | 复现假漂移且 RC=0（证明文档警告成立，不是期望行为） |
| 单调用同时 snapshot 加 compare | RC=2 且错误串匹配 |
| `stability:` | 出现 0 次，且同块正对照命中 |
| CLI 选项 | `--help` 旗标集合等于文档选项表 |
| 报告行序 | 计数字段按文档顺序逐行相等（列表比较，不是集合），`RESULT` 在末位 |
| detail 行 | 前缀、位置（计数字段之后、`RESULT` 之前）与格式匹配；`ERROR` 单发时无 `RESULT` |
| 合成夹具 | GHOST 包 RC=1 且 `DOC_ONLY=1`；无名脚本包 `SCOPE_FALLBACK_ALL=yes` |
| 自检四元组 | `DOC_KEYS`/`MATCHED`/`DOC_ONLY`/`RUNTIME_ONLY` 修复前后各记一次，并解释方向 |

未观测到的分支（例如同秒窗口）不写成已验证，在报告里单列。

### 7. 触发自检（可选）

- 用 Skill 工具触发被修复的 Skill，以注入正文（不是工具返回的 `Launching skill` 行）为判定依据：须含本次新写入的哨兵，且磁盘哈希仍等于步骤 5 记录值；
- 注入仍是旧正文时停止写入并查并发写入者；绑定与新鲜度的完整取证委派 `verify-skill-runtime-binding`、`verify-injected-skill-body-freshness`。

### 8. 清理与报告

- 删除 `$BASE`；他人或父会话的文件（如 `snapshot-before.json`）不属本次创建，不得删除；
- 检查安装目录与被调用 Skill 目录无 `__pycache__`/`.pyc`；
- 重取哈希：脚本必须与步骤 0 相同，`SKILL.md` 记录新旧两值；
- 报告分四类：已复现 / 仅正对照覆盖 / 人工推断 / 未执行。

## 输出契约示例

以下为本案例（`inventory-installed-skills`，2026-10-27）实测原文；换目标 Skill 时必须重新测量，不得照抄。

```text
## Drift vs snapshot (2026-10-27T13:53:54+01:00)
added: 0 | removed: 0 | moved: 0 | description changed: 0 | content changed: 0 | unchanged: 1
- no drift detected
```

- JSON 顶层键（12）：format, generated_at, user_root, project_root, counts, skills, anomalies, duplicates, builtin, groups, group_errors, drift；
- `skills[]`（10）：dir, root, path, name, description_sha256, desc_chars, size, mtime_ns, sha256, has_skill_md；
- 快照文件顶层键（7）：format, generated_at, user_root, project_root, counts, skills, anomalies；
- 异根假漂移：`added: 0 | removed: 1 | … | unchanged: 0` 加 `- removed: user/<name>`，RC=0；
- 错误原文：`ERROR: cannot read snapshot: [Errno 2] No such file or directory: '<path>'`，RC=2；
- 同秒窗口只由两次 `generated` 相同推出，脚本不打印 `stability:` 行；该结论属人工推断。

## 失败模式

| 现象 | 原因 | 处理 |
|---|---|---|
| 文档有 `stability:` 行，脚本从不打印 | 示例是手写的 | 删示例，改引实测 drift 段；零出现加正对照 |
| 照抄示例得到 `removed: 1` 且 RC=0 | 示例省略了根参数，快照记根但对比不校验 | 文档规定同一组根必须原样重传；把假漂移写进失败模式 |
| JSON 模式键集无记录 | 只测了 md 模式 | 新增 JSON 小节，键集来自实测并标明案例 |
| JSON + `--snapshot` 无提示行 | 提示只在 md 模式打印 | 文档写明；复放断言「0 次提示 + 文件存在」 |
| 一次调用同时传 snapshot 与 compare 得 RC=2 | 先读对比文件后写快照 | 文档禁止此写法并给出实测错误串 |
| QA 通过但示例仍错 | 只做了结构验收 | QA 后按新文档逐字复放 |
| 复放断言全 TRUE 但修复无效 | 断言用子串或依赖旧稿 | 改为键集/计数/原文精确比较，命令从新文档复制 |
| QA 报 `local reference not found`，路径是资源目录 | 文档用反引号包了裸目录名，校验器按本地引用查存在性 | 改成「脚本目录」等普通措辞；不要为此删掉真实存在的路径引用 |
| 表格渲染错位或列数不齐，但 QA PASS | 单元格内竖线未转义，校验器不解析 Markdown 表格 | 回读并按未转义竖线切分核对列数；实测输出的竖线写成 `\|` |
| 补文档后自检 `DOC_ONLY>0`、RC=1 | 在命名脚本的章节写了脚本从不发出的 UPPERCASE 占位键 | 只用真实运行时键；JSON 小写键不参与抽取，`GHOST_KEY` 类占位只留给合成夹具 |
| 文档键集正确但段头顺序不符 | 只比较集合，未比较行序 | 用有序列表比较计数字段，`RESULT` 固定末位 |
| 目标没有可触发的失败分支 | 现有用例全 PASS，`DOC_ONLY` 恒为 0 | 建最小合成包（多余键 / 不提脚本名）触发，不改目标脚本 |
| `MATCHED` 上升、`RUNTIME_ONLY` 归零被当成回归 | 把覆盖改善误读为行为变化 | 记录四元组并写明方向：补文档提高覆盖，失败分支才是回归 |
| 修复后脚本哈希变化 | 顺手改了脚本 | 回退脚本改动；脚本变更需用户单独决定 |
| 夹具删除了父会话文件 | 清理范围过大 | 只删本次 `$BASE`，他人文件先确认归属 |

## 验收清单

- [ ] 台账逐字对应验收报告的每条偏差，编号可追溯。
- [ ] 夹具在安装目录外，目录名与 Skill 相同，根全部指向夹具。
- [ ] A 类偏差有零出现断言与同块正对照。
- [ ] C 类偏差有 RC=0 的假结果实测。
- [ ] 示例块逐字来自实测 stdout，无手写示意行。
- [ ] 不可观测结论标为人工推断。
- [ ] 仅改 `SKILL.md`/references，脚本 SHA-256 前后一致。
- [ ] `skill-file-qa` 在稳定指纹上 PASS，body < 500。
- [ ] 文档无反引号裸目录名；表格单元格内竖线已转义，列数与表头一致。
- [ ] 按新文档复放全部 `_TRUE`，未观测分支单列。
- [ ] B 类已覆盖 CLI 选项、报告行序、detail 位置与合成夹具负向分支（适用时）。
- [ ] 补文档只用真实键；`DOC_KEYS`/`MATCHED`/`DOC_ONLY`/`RUNTIME_ONLY` 前后四元组已记录并解释。
- [ ] （可选）触发自检：注入正文含新哨兵，磁盘哈希与步骤 5 一致。
- [ ] 无 `__pycache__`/`.pyc`/夹具残留，最终哈希已记录。

## 资源

- `references/cas-2026-10-27-contrat-sortie.md`：来源会话、四类偏差原文、两个案例（库存 Skill 与 verifier 端到端）、复放令牌与时点指纹（含后续改写覆盖记录）。
- `references/harnais-repasse.md`：零出现加正对照、键集比较、多行报告（段头顺序、detail 位置）、选项清单、合成夹具、RC 捕获与清理的骨架。
- 相关 Skill：`skill-file-qa`、`verifier-parite-doc-script-skill`、`verify-skill-doc-claims-before-edit`、`replay-skill-reference-fixtures`、`verify-skill-runtime-binding`、`verify-injected-skill-body-freshness`、`skill-update-concurrency-safe`。
