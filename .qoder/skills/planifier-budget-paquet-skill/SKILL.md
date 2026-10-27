---
name: planifier-budget-paquet-skill
description: "在提出或修订 Skill 包方案前先做内容分栏与预算：每次必用的流程进 SKILL.md，证据、案例与查阅材料进 references，确定性重复代码进 scripts，输出物进 assets；给出分区行预算、正文与每个脚本及每个 reference 的硬上限、Files (N)、local 与 skill 引用计数、验收步骤和文件数影响表，并把文件数作为显式确认点。用户调整 references 或 scripts 的数量或范围时，按七项联动矩阵整份重算并重发方案，禁止局部改数；推荐数据里的计数必须从工具输出复算。用于新建 Skill 前的方案、references 数量调整、正文超预算、脚本压缩到上限后契约漂移、脚本重写后旧正负例作废、Files (N) 与 QA 预期不一致、方案只改一个数字、核心流程被放进 reference。覆盖审计交给 auditer-couverture-skill-avant-creation，写入安全交给 skill-update-concurrency-safe，断言措辞交给 verify-skill-doc-claims-before-edit，写入后验收交给 skill-file-qa，案例撰写交给 write-skill-evidence-case-study，计数溯源交给 audit-evidence-count-provenance，取码与判定语义交给 verifier-jugement-cli-par-fixtures，输出契约漂移交给 verifier-parite-doc-script-skill。中文触发：Skill 方案、内容分栏、行预算、references 数量、文件数、影响表、整份重发、脚本行数上限、脚本压缩后重跑、管道吞码、输出顺序漂移、方案调整。"
---

# Skill 包预算与分栏规划

## 概述

在提出或修订 Skill 包方案时，先决定每块内容放哪里、每个文件值多少行、包里有几个文件，再把完整方案交给用户确认。方案一旦被改数，整份重算重发。

## 何时使用 / 不适用

使用：

- 收到 create 或 update Skill 的任务，准备先出方案；
- 用户要求调整 references、scripts 的数量或范围；
- 方案里的 Files (N)、local references、正文行数与验收步骤互相矛盾；
- 推荐 JSON 或二手摘要给出计数，需要确认能否写进方案。

不适用时按表委派：

| 情况 | 交给 |
|---|---|
| 先审计已安装 Skill 是否已覆盖 | `auditer-couverture-skill-avant-creation` |
| 方案已确认，需要并发安全地写入 | `skill-update-concurrency-safe` |
| 要把来源观察写成断言并选措辞 | `verify-skill-doc-claims-before-edit` |
| 写入后的结构、引用与指纹验收 | `skill-file-qa` |
| 案例或证据档案需要独立成文 | `write-skill-evidence-case-study` |
| 怀疑计数被跨文档污染 | `audit-evidence-count-provenance` |
| 取返回码、判定字段语义或 A/B 并排对比 | `verifier-jugement-cli-par-fixtures` |
| 文档声明的输出键或顺序与脚本实际不符 | `verifier-parite-doc-script-skill` |

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
6. 验收步骤：逐文件回读与哈希；脚本逐个 selftest，退出码不经管道直取；
7. 文件数决策点：默认方案、备选方案、影响表；
8. 「尚未写入任何文件」声明。

预算规则：

- 正文给硬上限，不写「约 200 行」；写入后用校验器实测。
- 每个分区给行预算，合计不超过正文上限。
- 脚本与每个 reference 各自给硬上限；上限过紧时压缩会先删掉已承诺的选项，压缩后必须把 `--help` 与文档里的脚本契约重新对齐。
- 脚本重写（压缩、删选项、改输出顺序）后，先前正负例结果全部作废，整套夹具重跑；报告只引用重写后的数值。
- 取退出码不经管道：重定向到文件或直接捕获，管道会让 `$?` 变成末段命令的状态。
- 验收步骤必须能逐项映射到磁盘事实，不能只写「跑 QA」。

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

## 流程 0–6

0. 读来源会话与目标现状：两级 skills 根是否已有同名目录，目标目录是否存在、是否稳定；方案确认后目录才出现则停写，交 `adopt-concurrent-duplicate-skill`，不覆盖。
1. 覆盖审计：把推荐主张交给 `auditer-couverture-skill-avant-creation`，COVERED 改更新，ABSENT 才新建。
2. 分栏：逐块判断内容去处，写出反模式检查。
3. 定预算与文件数：正文、每个脚本与每个 reference 的硬上限、分区预算、Files (N)、QA 预期、验收步骤。
4. 出方案：含文件数影响表与「尚未写入」，等待用户确认。
5. 确认后写入：并发安全交给 `skill-update-concurrency-safe`。
6. 按预算验收：跑 `skill-file-qa`，逐项对账方案与磁盘；报告偏差，不达标不宣称成功。

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
- 这些历史数字只在该时点成立，引用前先复算。

## 失败模式

| 现象 | 原因 | 处理 |
|---|---|---|
| 只改了 Files (N) | 把文件数当孤立字段 | 按七项矩阵整份重算 |
| 核心矩阵放进 reference | 误判「按需加载」 | 上移进正文 |
| `local references: 0 checked` 被当成没有断链 | 没有可检引用 | 有引用时补负向控制 |
| 裸路径引用静默 PASS | 校验器只抽取反引号与链接 | 写成反引号形式 |
| 预算写「约 200 行」 | 没有硬上限 | 给上限并实测 |
| 从推荐 JSON 抄计数 | 二手数字未复算 | 回到工具输出 |
| 方案未声明未写入 | 用户无法判断状态 | 每版方案都声明 |
| 文件数没有备选 | 用户无法调整 | 附影响表 |
| 方案确认后目标目录出现 | 并发写入 | 停写，交 `adopt-concurrent-duplicate-skill`，不覆盖 |
| 脚本上限压得太紧 | 压缩时删掉契约里的选项 | 留余量；压缩后重核 `--help` 与文档 |
| 脚本重写后仍引用旧正负例数值 | 旧结果属于旧版本 | 整套重跑，只报重写后数值 |
| 管道取码得到 rc=0 | `$?` 是末段命令的状态 | 重定向或直接捕获 |

## 完成清单

- [ ] 分栏表每块都有去处与理由。
- [ ] 包树与 Files (N) 一致，没有空目录或多余文档。
- [ ] local references 与 skill references 的计数来自实跑。
- [ ] 正文有硬上限，分区预算合计不超限。
- [ ] 验收步骤逐文件、逐脚本可执行。
- [ ] 每个脚本与每个 reference 都有硬上限。
- [ ] 脚本被重写或压缩后整套正负例已重跑，`--help` 与文档契约已重核，报告只引用重写后数值。
- [ ] 验收命令的退出码未经管道。
- [ ] 文件数决策点含备选与影响表。
- [ ] 改数时整份重发，没有局部改数。
- [ ] 计数来自工具输出，二手的已标 UNVERIFIED。
- [ ] 方案声明「尚未写入任何文件」。
- [ ] 写入后 QA PASS，并报告方案与磁盘的偏差。

## 资源

- 本 Skill 只有 SKILL.md，无 scripts、references、assets。
- 来源会话：`fe52b619`（方案迭代与校验器夹具）、`ede0647e`（原始采样与 QA 输出）、`fce75d3f`（1→0 reference 重算与本包写入）。
- 委派见「何时使用 / 不适用」表。
