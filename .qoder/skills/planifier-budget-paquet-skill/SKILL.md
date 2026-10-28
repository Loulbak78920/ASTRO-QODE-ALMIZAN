---
name: planifier-budget-paquet-skill
description: "在提出或修订 Skill 包方案前先做内容分栏与预算。触发：Skill 方案、references 数量、文件数、影响表、整份重发、行预算、脚本行数上限、管道吞码、输出顺序漂移、运行时绑定、清单截断、UNVERIFIED、自污染、同一会话二次调用、旧注入记录、验收分级、故障分级、主语混用、注入正文、索引刷新、推荐前提对账。每次必用的流程进 SKILL.md，证据、案例与查阅材料进 references，确定性重复代码进 scripts，输出物进 assets；给出分区行预算、正文与各脚本/reference 的硬上限、Files (N)、local/skill 引用计数、验收步骤和文件数影响表，文件数作为显式确认点。调整 references 或 scripts 数量时按七项矩阵整份重算重发，禁止局部改数；推荐计数须从工具输出复算，故障叙述先读原文再分三级，主语不同的句子不得互相反驳；写入后按项分级（正文注入≠索引刷新），清单截断标 UNVERIFIED，自指提示词的计数作废；注入记录按调用前行数绑定。用于新建前方案、正文超预算、脚本压缩到上限后契约漂移、脚本重写后旧正负例作废、Files (N) 与 QA 预期不一致、方案只改一个数字、核心流程被放进 reference、推荐故障叙述要写进案例、reload 后生效。覆盖审计交给 auditer-couverture-skill-avant-creation，写入安全交给 skill-update-concurrency-safe，断言措辞交给 verify-skill-doc-claims-before-edit，写入后验收交给 skill-file-qa，运行时绑定交给 verify-skill-runtime-binding，注入正文交给 verify-injected-skill-body-freshness，案例撰写交给 write-skill-evidence-case-study，计数溯源交给 audit-evidence-count-provenance，推荐声明分类交给 verify-skill-recommendation-claims，取码与判定语义交给 verifier-jugement-cli-par-fixtures，输出契约漂移交给 verifier-parite-doc-script-skill。"
---

# Skill 包预算与分栏规划

## 概述

在提出或修订 Skill 包方案时，先决定每块内容放哪里、每个文件值多少行、包里有几个文件，再把完整方案交给用户确认。方案一旦被改数，整份重算重发。

## 何时使用 / 不适用

使用：

- 收到 create 或 update Skill 的任务，准备先出方案；
- 用户要求调整 references、scripts 的数量或范围；
- 方案里的 Files (N)、local references、正文行数与验收步骤互相矛盾；
- 推荐 JSON 或二手摘要给出计数，需要确认能否写进方案；
- 推荐 `rationale` 描述了一次故障，准备写进案例或失败模式；
- 写入后要确认新正文或新触发词在运行时已生效，而不只是 QA PASS。

不适用时按表委派：

| 情况 | 交给 |
|---|---|
| 先审计已安装 Skill 是否已覆盖 | `auditer-couverture-skill-avant-creation` |
| 方案已确认，需要并发安全地写入 | `skill-update-concurrency-safe` |
| 要把来源观察写成断言并选措辞 | `verify-skill-doc-claims-before-edit` |
| 写入后的结构、引用与指纹验收 | `skill-file-qa` |
| description 候选串写入前测量与交付前自检 | `verifier-contrat-redaction-skill` |
| 既有 description 接近 1024、需要压缩改写 | `edit-skill-frontmatter-description` |
| 写入后要证明运行时解析到目标目录并注入了新正文 | `verify-skill-runtime-binding` |
| 怀疑注入的是旧快照、需要定位写入者 | `verify-injected-skill-body-freshness` |
| 案例或证据档案需要独立成文 | `write-skill-evidence-case-study` |
| 怀疑计数被跨文档污染 | `audit-evidence-count-provenance` |
| 推荐 JSON 的声明分类与主语核对 | `verify-skill-recommendation-claims` |
| 取返回码、判定字段语义或 A/B 并排对比 | `verifier-jugement-cli-par-fixtures` |
| 文档声明的输出键或顺序与脚本实际不符 | `verifier-parite-doc-script-skill` |
| 新会话 + nonce 的只读验收 | `skill-acceptance-in-new-session` |

本 Skill 只负责方案与预算，不替代覆盖审计、写入或写入后验收。

## 内容分栏规则

| 内容 | 去处 | 判据 |
|---|---|---|
| 每次调用都必须执行的规则、流程、检查 | SKILL.md 正文 | 删掉会导致任务失败 |
| 只在特定判断时才加载的证据、案例、长表、命令目录 | references | 删掉仍能执行，只在审计或校准时需要 |
| 会被反复改写且要求确定性的代码 | scripts | 手写易错，需要固定输出 |
| 只进入产出物的模板、图片、字体 | assets | 不进入上下文 |

- 默认最少文件数；0 个 references 合法，只有确实需要按需加载时才建。
- 案例优先压缩进正文；只有逐字证据会挤爆正文预算时才独立成 reference。
- 不建空目录，不建 README、CHANGELOG、安装指南。
- 反模式：把每次必用的矩阵放进 reference。来源会话的真实纠正就是把它上移进正文。

## 方案必备字段与预算

方案至少包含：

1. 目标、不适用与委派表；
2. 分栏表：每块内容 → 去处 → 理由；
3. 包树：每个文件一行，附行数预算；
4. Files (N) = 1 + references + scripts + assets；
5. QA 预期：Files (N)、local references R checked、skill references K checked、body ≤B（硬上限 500）、description 单行 ≤1024、RESULT；
6. 验收步骤：逐文件回读与哈希；脚本逐个 selftest，退出码不经管道直取；正文或 description 变更时补运行时绑定（流程第 7 步）；
7. 文件数决策点：默认方案、备选方案、影响表；
8. 「尚未写入任何文件」声明。

预算规则：

- 正文给硬上限，不写「约 200 行」；写入后用校验器实测。
- 每个分区给行预算，合计不超过正文上限。
- 脚本与每个 reference 各自给硬上限；上限过紧时压缩会先删掉已承诺的选项，压缩后必须把 `--help` 与文档里的脚本契约重新对齐。
- 脚本重写（压缩、删选项、改输出顺序）后，先前正负例结果全部作废，整套夹具重跑；报告只引用重写后的数值。
- 取退出码不经管道：重定向到文件或直接捕获，管道会让 `$?` 变成末段命令的状态。
- 验收步骤必须能逐项映射到磁盘事实，不能只写「跑 QA」。
- description 也先测后写：候选串在磁盘外实测单行、长度与「冒号+空格」，超 1024 先压缩再 Edit，不等校验器报超限；既有描述接近上限时的压缩交 `edit-skill-frontmatter-description`，交付前自检交 `verifier-contrat-redaction-skill`。

## 文件数决策点与影响表

把文件数作为显式确认点，不只给一个默认值：

| 方案 | Files | local refs | 正文预算 | 验收差异 |
|---|---|---|---|---|
| 仅 SKILL.md | 1 | 0 checked | 可容纳压缩案例 | 单文件哈希 + QA |
| 加 1 个 reference | 2 | 1 checked | 减去参考内容 | 回读 reference + 双哈希 + QA |
| 加 2 个 references | 3 | 2 checked | 再减 | 回读两个 reference + 三哈希 + QA |
| 每个脚本 | 每脚本 +1 | 不变 | 脚本另设硬上限 | 每个脚本 selftest + 正负例 |

每次调整都重算全行，不允许只改 Files (N)。

## 改数重算矩阵

用户改动 references、scripts 或 assets 的数量或范围时：

1. 冻结旧方案，逐项列出旧值；
2. 把要移动的内容映射到新去处，说明理由；
3. 重算七项：包树、Files (N)、local references、skill references、正文行预算、验收步骤、description 长度与 QA 预期；
4. 整份重发方案，附旧值 → 新值变更表；
5. 声明尚未写入，等待确认；
6. 若用户要求把每次必用的内容移进 reference，先指出「不读就漏」的风险，再按用户决定执行。

历史示例（当时用约数，后续方案改为硬上限）：2 refs / Files (4) / 正文约 200 行 → 1 ref / Files (3) / 正文约 240 行；再 → 0 ref / Files (1) / local 1→0 / 正文上限 250→280。

## 计数与实测纪律

- 推荐 JSON、助手散文、旧方案里的数字都不是证据。
- 每个计数在方案定稿前从工具输出复算：QA 输出行、采样输出行、文件枚举。
- 写进方案时给出复算来源与命令，不只给结论。
- 只有二手摘要时标 UNVERIFIED，不写成事实。
- 实例：推荐写「4 次采样、body 182」，原始输出是 `sample=0..4`（5 次）与 `body 179`。
- 怀疑跨文档污染时委派 `audit-evidence-count-provenance`。

## 推荐故障叙述的对账

推荐的 `summary` 与 `rationale` 不是证据。准备把其中的故障写进案例或失败模式前：

1. 读被批评对象的原文：目标文件的当时版本、来源方案或工具输出，不读推荐的转述。
2. 每条叙述写清主语与版本：目标 Skill 正文、来源方案、哪一次工具输出。
3. 分级：**已复现**（工具输出直接显示故障）、**预防性风险**（规则缺口为真、故障未发生）、**不成立**（原文与叙述相反）。只有已复现可以写成案例故障；预防性风险写进失败模式并注明未发生；不成立只报告，不写入。
4. 检查是否把两个主语合成一个命题，例如「本 Skill 正文没有脚本上限」与「来源方案已写 ≤200」互不否定。
5. 声明分类交给 `verify-skill-recommendation-claims`，措辞级别交给 `verify-skill-doc-claims-before-edit`。
6. 写入后逐句回读对账；QA PASS 只证明结构，不证明散文语义。

## 流程 0–7

0. 读来源会话与目标现状：两级 skills 根是否已有同名目录，目标目录是否存在、是否稳定；推荐中的故障叙述先按上节分级，再决定写进案例、失败模式还是只报告；方案确认后目录才出现则停写，交 `adopt-concurrent-duplicate-skill`，不覆盖。
1. 覆盖审计：把推荐主张交给 `auditer-couverture-skill-avant-creation`，COVERED 改更新，ABSENT 才新建。
2. 分栏：逐块判断内容去处，写出反模式检查。
3. 定预算与文件数：正文、每个脚本与每个 reference 的硬上限、分区预算、Files (N)、QA 预期、验收步骤。
4. 出方案：含文件数影响表与「尚未写入」，等待用户确认。
5. 确认后写入：并发安全交给 `skill-update-concurrency-safe`。
6. 按预算验收：跑 `skill-file-qa`，逐项对账方案与磁盘；报告偏差，不达标不宣称成功。
7. 运行时绑定：正文或 description 有改动时，QA PASS 只证明磁盘结构；按下一节取证（先记本会话 JSONL 行数，再只读调用）并逐项分级，把正文注入与 description 索引分开报告；索引层不可判时标 UNVERIFIED，不写成 PASS。

## 写入后运行时绑定（第 7 步）

QA PASS 只覆盖磁盘结构与引用。正文或 description 有改动时，另做四步取证：

1. 采样磁盘：size、mtime、SHA-256，记录调用前值。
2. 只读调用目标 Skill：注入首行须是 `Base directory for this skill: <目标绝对路径>`，正文须含本次新增的哨兵短语。
3. 绑定会话 JSONL 的注入记录：调用前记录本会话 JSONL 行数；调用后只接受行号大于该计数的新增记录，再核对 `type=user`、`isMeta=true`、首行 Base directory 与同一哨兵。
4. 调用后重新采样：指纹与调用前一致，才证明注入来自当前稳定文件而非旧快照。

同一会话多次调用会产生多条内容逐字相同的注入记录，仅按内容匹配会命中旧记录：来源 `42f275c5` 调用前 221 行，调用后同时命中 line 188 与 line 229，均为 8224 字符、3/3 哨兵。判定只用「行号大于调用前计数」，不写死具体行号；没有新增记录判 UNVERIFIED，不用旧记录补位。更强的唯一绑定（`tool_use → tool_result → parentUuid`）交给 `verify-skill-runtime-binding`。

报告时分开两件事：

- **正文注入**：以上证据能证明；报告须写出调用前行数、新增记录行号、哨兵命中数（n/n）与调用前后指纹一致。
- **description 索引**：由客户端负责。代理不能执行 `/skills reload`，也不能重启会话；只能请用户 reload 后在新会话复查，展示层文本不算证据。

具体流程交给 `verify-skill-runtime-binding` 与 `verify-injected-skill-body-freshness`；本 Skill 只规定何时做、报告哪些边界。

## 运行时验收的分级

代理不能执行 `/skills reload` 或重启会话；权威验收在新会话做，流程交给 `skill-acceptance-in-new-session`。逐项判定：

| 项 | PASS 判据 | 不满足时 |
|---|---|---|
| Base directory | 注入首行逐字等于目标路径 | FAIL |
| 正文哨兵 | 注入正文含本次新增短语 | FAIL |
| 文件指纹 | 调用前后 size/mtime/SHA-256 一致 | UNVERIFIED |
| description 索引 | 条目完整可见并逐字含新触发词 | 省略号截断 → UNVERIFIED |

- 结论按项写 PASS/FAIL/UNVERIFIED，整体只写 `ACCEPTANCE PASS` 或有唯一原因的 `ACCEPTANCE FAIL`；不写「触发词已生效」。
- 自污染：提示词本身含被断言字符串时，该会话 JSONL 计数作废；在不含该字符串的上下文重算，并用 description 尾部短语作负向控制（计数 0 与截断一致才算自洽）。
- Windows：`py -3` 先写 UTF-8 临时文件再 Read；解析 JSONL 前过滤 `timestamp` 类型，避免 `str`/`int` 排序失败。

## 已验证案例（压缩）

- 来源 `fe52b619`（2026-10-27T13:16Z 读取时 rev 14、8 条消息，`hasMoreBefore=false`；revision 字段会变，不写死）：v1 为 2 refs / Files (4) / 正文约 200 行。
- 用户「调整 references 数量后重新生成方案」后，v2 改为 1 ref / Files (3) / 正文约 240 行，并把复放矩阵与 RC 三角上移进正文。
- 用户「检查 references 数量是否满足要求」后，读校验器实现并跑夹具：0 ref → Files (1)、0 checked、PASS；1 个反引号引用 → 1 checked、PASS；断链 → FAIL、RC=1；裸路径 → 0 checked 且 PASS（静默）。
- 用户「按 1 个 reference 开始写入并执行验证」后才开始写入。
- 计数复算：上游 `ede0647e` 原始输出为 5 次采样（`sample=0..4`，`STABLE after 16s`）与 body 179；推荐写 4 次与 182。
- 本包落地：`fce75d3f` 把 1 ref 重算为 0 ref / Files (1)，经「执行写入并验证」后写入；实测 QA `Files (1)`、`local references: 0 checked`、PASS。
- 来源 `9948e777`（2026-10-28 读取：rev 12、2 条用户消息、`hasMoreBefore=false`）：方案已给脚本硬上限 ≤200 行；脚本 239 → 206 → 200 行，压到上限时计划契约里的 `--exclure` 未出现在最终 `--help`，而方案未要求压缩后重核契约。
- 同会话 239 行版与 200 行版各跑一次 7/7 夹具：重写后确实整套重跑，未见引用过期数字；「重写即作废旧结果」的规则缺口为真，故障属预防，不写成已发生。
- 同会话实测：`py -3 … | tail` 报 `EXIT=0`，直取后 `RC=2`；239 行版先输出 `RACINE_FICHIER`、200 行版先输出 `FILES`，与文档契约的偏差只有逐字复放才能发现。
- 来源 `5bcd33cf`（2026-10-28 读取：rev 10、最后消息 2026-10-27T23:36Z、`hasMoreBefore=false`、`runtimeState=running`）：推荐称本 Skill「只约束正文上限」，旧版确实如此（description 603 字符、预算规则只有正文、影响表只有 selftest）；`9948e777` 方案的 `≤ 200 行` 属于另一主语，不能反驳该句。239 行版与 200 行版各有 `SUMMARY 7 / 7`，重写后确已重跑；「过期数字」属预防性风险。
- 来源 `9eeb84f4`（2026-10-28 读取：rev 51、`hasMoreBefore=false`、`runtimeState=running`）：9 处 Edit 后 QA `9 pass / 0 fail`、`Files (1)`、body 181、description 888、skill refs 10；随后用户要求 reload，代理无该命令，临时拼出「磁盘采样 → 只读调用 → JSONL `line 266`（`type=user`、`isMeta=true`、Base directory 前缀）→ 调用后 `sha256` 不变」。正文注入有证据，description 索引仍待用户 reload 或重启；一次内联 Python 扫描因 `unicodeescape` 失败后改为独立脚本重跑。
- 流程当时止于第 6 步，该验证链属临时补做：规则缺口为真，误报未发生（预防性风险）；「被静默拉伸」不成立，reload 是用户明确要求。
- 来源 `42f275c5`（2026-10-28 读取：rev 13、3 条用户消息、`hasMoreBefore=false`、`runtimeState=running`）：description 候选串先在临时 Python 里实测，1039 与 1028 均超 1024，压缩到 1013 才 Edit；随后 QA `9 pass / 0 fail`、`Files (1)`、body 209、description 1013、skill refs 12。
- 此前预算规则只把 description 长度写成 QA 预期，没有写前门禁；该会话无用户纠正，属代理自纠，规则缺口为真。
- 来源 `9eeb84f4` 的后续回合（本次 `turnLimit=20` 读取 13 条消息、`hasMoreBefore=false`）：用户连续三轮要求 reload、重启、重启后验收；代理无该命令，改用新会话 `7e8e3732`（nonce `NONCE-RELOAD-20261028-7f3a`，只读零写入，29 行）。
- 该会话第 1 项索引 description 被截断在 `…主语不同的…` → UNVERIFIED；Base directory、4 个正文哨兵、指纹 PASS；`ACCEPTANCE FAIL` 仅因第 1 项。JSONL 复算 `推荐前提对账` 8、`故障分级` 7、`主语混用` 7，但提示词含三词，计数作废；description 尾部短语 0，与截断一致。
- 同会话 Windows 取证：内联 `py -3` 打印中文两次 `UnicodeEncodeError`（改 UTF-8 临时文件后成功），一次 `timestamp` 的 `str`/`int` 排序 `TypeError`（过滤后成功）。
- 来源 `42f275c5`（2026-10-28 读取：rev 73、`hasMoreBefore=false`、`runtimeState=ready`）：第 7 步首验得 line 188；用户「reload skills」再次只读调用，调用前 221 行，调用后同时命中 line 188 与 line 229（均 8224 字符、3/3 哨兵），磁盘 `f271a5fa…dfd1` 前后不变。旧规则「按内容匹配」无法区分两次注入（工具输出 2 条命中）；假 PASS 未发生，属预防性风险。
- 这些历史数字只在该时点成立，引用前先复算。

## 失败模式

| 现象 | 原因 | 处理 |
|---|---|---|
| 只改了 Files (N) | 把文件数当孤立字段 | 按七项矩阵整份重算 |
| 核心矩阵放进 reference | 误判「按需加载」 | 上移进正文 |
| `local references: 0 checked` 被当成没有断链 | 没有可检引用 | 有引用时补负向控制 |
| 裸路径引用静默 PASS | 校验器只抽取反引号与链接 | 写成反引号形式 |
| 预算写「约 200 行」 | 没有硬上限 | 给上限并实测 |
| description 写到超限才由校验器发现 | 候选串只在校验器里测 | 写入前先在磁盘外测量，超限先压缩 |
| 从推荐 JSON 抄计数 | 二手数字未复算 | 回到工具输出 |
| 直接采信推荐故障叙述 | 未读被批评原文就分级 | 预防性风险写成已发生；先读原文再分级 |
| 把两个主语合成一个命题 | 用来源方案的 ≤200 反驳本 Skill 正文缺失 | 逐条写主语与版本，分别判定 |
| 方案未声明未写入 | 用户无法判断状态 | 每版方案都声明 |
| 文件数没有备选 | 用户无法调整 | 附影响表 |
| 方案确认后目标目录出现 | 并发写入 | 停写，交 `adopt-concurrent-duplicate-skill`，不覆盖 |
| 脚本上限压得太紧 | 压缩时删掉契约里的选项 | 留余量；压缩后重核 `--help` 与文档 |
| 脚本重写后仍引用旧正负例数值 | 旧结果属于旧版本 | 整套重跑，只报重写后数值 |
| 管道取码得到 rc=0 | `$?` 是末段命令的状态 | 重定向或直接捕获 |
| 用 QA PASS 代替运行时生效 | 校验器只读磁盘 | 按第 7 步取证，分开报告正文与索引 |
| 同一会话二次调用后按内容匹配命中旧注入记录 | 新旧记录逐字相同 | 先记行数，只认新增行；无新增判 UNVERIFIED |
| 承诺执行 `/skills reload` 或重启会话 | 代理没有该命令 | 请用户执行，只用只读调用证明正文已注入 |
| 把展示层的 description 当作索引已刷新 | 展示层不等于客户端索引 | 以 reload 后新会话的触发结果为准 |
| 清单条目被截断仍报触发词 PASS | 把不可判当成已判 | 该层标 UNVERIFIED；整体只报已取证项 |
| 用验收提示词里的字符串当索引证据 | 提示词自污染 | 在不含该字符串的上下文重算，并用尾部短语作负向控制 |
| 内联 Python 扫 JSONL 报 `unicodeescape` | Windows 路径的 `\U` 被当作转义 | 写临时 `.py`，用 raw string 或 `os.path.join` |

## 完成清单

- [ ] 分栏表每块都有去处与理由。
- [ ] 包树与 Files (N) 一致，没有空目录或多余文档。
- [ ] local references 与 skill references 的计数来自实跑。
- [ ] 正文有硬上限，分区预算合计不超限。
- [ ] 验收步骤逐文件、逐脚本可执行。
- [ ] 每个脚本与每个 reference 都有硬上限。
- [ ] description 候选串已在写入前实测单行与长度，超 1024 时先压缩再 Edit。
- [ ] 脚本被重写或压缩后整套正负例已重跑，`--help` 与文档契约已重核，报告只引用重写后数值。
- [ ] 验收命令的退出码未经管道。
- [ ] 文件数决策点含备选与影响表。
- [ ] 改数时整份重发，没有局部改数。
- [ ] 推荐中的每条故障叙述已绑定主语、版本与原文，并分级为已复现、预防性风险或不成立。
- [ ] 回读已逐句对账，未用 QA PASS 代替语义核对。
- [ ] 计数来自工具输出，二手的已标 UNVERIFIED。
- [ ] 方案声明「尚未写入任何文件」。
- [ ] 写入后 QA PASS，并报告方案与磁盘的偏差。
- [ ] 正文或 description 变更后已按第 7 步取证，磁盘前后指纹一致。
- [ ] 注入记录按调用前行数绑定，报告了新记录行号、哨兵命中数与前后指纹。
- [ ] 报告已把正文注入与 description 索引分开，未承诺执行 reload。
- [ ] 运行时验收按项给 PASS/FAIL/UNVERIFIED；清单被截断时标 UNVERIFIED，未升格为 PASS。
- [ ] 自指字符串的计数已作废，并在不含该字符串的上下文重算。

## 资源

- 本 Skill 只有 SKILL.md，无 scripts、references、assets。
- 来源会话：`fe52b619`（方案迭代与校验器夹具）、`ede0647e`（原始采样与 QA 输出）、`fce75d3f`（1→0 reference 重算与本包写入）、`5bcd33cf`（推荐前提对账与主语分离）、`9eeb84f4`（写入后运行时绑定与 reload 边界）、`42f275c5`（写前 description 测量与 1013 收敛；第 7 步行数边界 line 188 / line 229）。
- 委派见「何时使用 / 不适用」表。
