---
name: inventory-installed-skills
description: "只读盘点已安装 Skill：枚举用户级与项目级 skills 根，用 PyYAML 解析每个 SKILL.md 的 name 与 description，标记缺失 SKILL.md、frontmatter/YAML 错误、目录名与 name 不一致、跨根同名，按用户级/项目级/CLI 内置或插件分列精确计数，并用会话早期快照对比报告新增、移除、跨根移动与 description 改写。用于“列出当前所有已安装 Skill”“一共有多少个 Skill”“用户级完整清单”“某个 Skill 现在在用户级还是项目级”“回答期间 Skill 有没有变化”等请求；计数必须来自同一次枚举，分组合计必须等于本地总数，内置/插件不得计入本地总数。不替代规则覆盖审计（历史名称 audit-recouvrement-skills-avant-creation，当前未安装）、单 Skill 写后验收（skill-file-qa）、创建途中的实时验收（audit-skill-during-live-creation）或包完整性审计（skill-package-integrity-audit）。中文触发：已安装 Skill 清单、Skill 数量、用户级、项目级、盘点、移动、描述改写；English: list installed skills, skill inventory, count skills, moved skill, description drift; Français: inventaire des Skills, liste des Skills installés, Skills déplacés. 没有会话早期快照时，在回答窗口内先 --snapshot 再立即 --compare，并报告两次 generated 与 unchanged；出现 drift 时以第二次枚举为准。快照名必须唯一（时间戳或会话 ID）并在 --compare 复用同一路径；活树异常需短间隔重跑，仅单次出现的标为临时。分支 B 须保留快照运行的完整 stdout 作为公布清单；两次 generated 同秒时标注窗口不足 1 秒，必要时 60–120 秒后复比。"
---

# 已安装 Skill 只读盘点

## 何时使用

- 用户要求列出当前所有已安装 Skill、只报数量、要用户级或项目级的完整清单；
- 需要确认某个 Skill 现在位于用户级还是项目级；
- 上一轮清单出现分组数与总数对不上，需要一次算清；
- 会话期间可能有并发会话创建、移动或改写 Skill，回答前要确认清单是否变化。

不适用：判断两个 Skill 职责是否重合（历史名称 audit-recouvrement-skills-avant-creation 当前不在用户级/项目级 skills 根，不再可用）；单个 Skill 的写后验收用 `skill-file-qa`；目标目录在创建途中出现用 `audit-skill-during-live-creation`；包归档完整性用 `skill-package-integrity-audit`。

## 核心规则

1. **计数只来自一次枚举。** 总数、分组数、清单必须来自同一次脚本运行；不要用会话早期的名单配当前总数。
2. **两种来源分开。** 文件系统只有用户级与项目级；CLI 内置/插件来自当前会话的可用 Skill 列表，标注「不在文件系统」，绝不计入本地总数。
3. **计数单位。** 含 `SKILL.md` 的目录。无 `SKILL.md` 的目录只进异常段、不计入 `count`；有 `SKILL.md` 但解析失败仍计入 `count`，同时进异常段。
4. **分组是展示层。** 分组合计必须等于本地总数；不满足时脚本退出码为 1，此时不得输出分组结论。
5. **回答前重跑。** 早先快照只用于漂移对比，不用于输出成员名单。
6. **无早期快照时自证稳定。** 回答前先 `--snapshot` 再立即 `--compare`，两次必须是独立调用；保留并公布快照那次运行的完整 stdout（含清单与计数），不要只留时间戳、丢弃 stdout 或改用更早名单。稳定性证据只来自 compare 输出的 `## Drift vs snapshot` 段：脚本不打印 `stability:` 行，`unchanged` 与 `no drift detected` 只在该段。无漂移结论只覆盖两次 `generated` 之间；两次相同（同一秒）时人工写成「稳定窗口 < 1 秒」。出现 drift 时以 compare 那次运行的清单为准并说明。
7. **快照路径唯一且根一致。** `--snapshot` 用带时间戳或会话 ID 的文件名，`--compare` 复用同一字面路径；不要用固定共享名（如 `skills-snapshot.json`、`skills-snapshot-live.json`）。并发会话会写同一路径，覆盖后对比可能退化为自我比较。同一组 `--user-root`/`--project-root` 必须同时传给两次调用：快照会记录这两个根，但 compare 不校验，根不一致只会产出假 `removed`/`added`，且退出码仍为 0。
8. **活树异常可瞬变。** 仅单次运行出现的异常先标为「临时/可能正在创建或改写」，间隔 60–120 秒重跑；两次都存在才写成结论，并保留两次运行的 `generated` 时间戳。

## 流程

### 1. 会话早期先落快照（推荐）

在项目根执行，把当前清单写到两个 skills 根之外（例如项目 `.qoder/tmp`，该目录必须已存在）。脚本只校验目标文件的父目录存在，不会拒绝写在 skills 根内的路径——「两个根之外」是使用约定，需自行遵守。文件名必须唯一，包含时间戳或会话 ID：

```bash
SNAP=".qoder/tmp/skills-snapshot-$(date +%Y%m%dT%H%M%S)-$$.json"
py -3 "$HOME/.qoder/skills/inventory-installed-skills/scripts/inventory_skills.py" --snapshot "$SNAP"
```

记下脚本在 md 模式打印的 `snapshot written:` 路径；JSON 模式不打印该行，以传入的字面路径为准。第 3 步必须复用同一字面路径，不要换成固定名或另一次会话的快照。若用了 `--user-root`/`--project-root`，记下这组值，第 3 步原样重传。

### 2. 回答前枚举

仍在项目根执行。脚本默认用户级 `~/.qoder/skills`，项目级取当前目录向上最近的 `.qoder/skills`：

```bash
py -3 "$HOME/.qoder/skills/inventory-installed-skills/scripts/inventory_skills.py"
```

不要在 Skill 安装目录里运行：那里向上找不到项目级根。项目根不在当前目录树时用 `--project-root` 指定。内置/插件名称从当前会话的可用 Skill 列表抄入 `--builtin`，逗号分隔；只传当前确实存在的那些，不要估算数量：

```bash
py -3 "$HOME/.qoder/skills/inventory-installed-skills/scripts/inventory_skills.py" --builtin "skill-creator,imagegen,qoder-canvas:canvas,collaboration:skills"
```

### 3. 回答前证明稳定（两个分支）

**A. 会话早期落过快照**：只跑对比，清单仍取第 2 步的枚举；`--compare` 用第 1 步记录的那个唯一路径，并原样带上同一组 `--user-root`/`--project-root`（第 1 步用了自定义根时）。

```bash
SNAP=".qoder/tmp/skills-snapshot-20261026T135935.json"   # 替换为第 1 步实际路径
py -3 "$HOME/.qoder/skills/inventory-installed-skills/scripts/inventory_skills.py" --compare "$SNAP"
```

**B. 没有早期快照**：在回答窗口内先写快照、再立即对比，两次独立调用，两次传同一组根（自定义根要写全，默认根可省略）。公布清单与计数取快照那次运行（它的 `generated` 是稳定窗口起点），不要用更早的名单配对比结论。两次 `generated` 相同（脚本只到秒）时，稳定窗口按 < 1 秒报告，不能当作更长稳定期；需要更长窗口时记录该字面路径，间隔 60–120 秒再跑一次 `--compare`。

```bash
SNAP=".qoder/tmp/skills-snapshot-$(date +%Y%m%dT%H%M%S)-$$.json"
# 自定义根时，下面两条命令都要带同一组 --user-root/--project-root
py -3 "$HOME/.qoder/skills/inventory-installed-skills/scripts/inventory_skills.py" --snapshot "$SNAP"
py -3 "$HOME/.qoder/skills/inventory-installed-skills/scripts/inventory_skills.py" --compare "$SNAP"
```

两条命令在同一 shell 中执行，让 `$SNAP` 指向同一路径；跨回合时改用记录下来的字面路径。两段输出按顺序出现：第一段是快照运行，第二段是 compare；保留并公布第一段的完整 stdout（含清单与计数），稳定性证据取第二段的 `## Drift vs snapshot` 段（脚本不打印 `stability:` 行）。不要把第一段重定向到 `/dev/null`、只保留退出码或用更早名单补位。

不要在一次调用里同时传 `--snapshot` 与 `--compare` 来比较刚写的文件：脚本先读对比文件、后写快照，文件不存在会以 `exit 2` 结束，存在则比较的是旧内容。

输出新增、移除、跨根移动、description 改写（按 `description_sha256`）与正文变化。报告两次 `generated` 和 drift 段的 `unchanged` 数；drift 非零时改用 compare 那次运行的清单，并逐条列出变化。

### 4. 需要主题分组时

写一个 JSON 映射再传入 `--groups`：

```json
{"Skill 工程与元技能": ["skill-file-qa", "skill-update-concurrency-safe"], "项目领域": ["tableau-maitre-sequentiel"]}
```

脚本校验未知名称、重复归属与漏项。通过时打印一级标题 `## Groups (validated: N assigned = M local total)`（N = 已分配条数，M = 本地总数；`assigned` 只出现在这一行），主题名按字母序排列。失败时打印 `## Groups (INVALID)`，逐条列入 `## Group errors`，退出码为 1。

## 输出契约

数字直接抄脚本输出，不手算、不合并两次运行的名单。下面的示例是传了 `--builtin` 的形态；未传 `--builtin`（默认）时，`built-in/plugin (declared, not on disk): N` 行与 `## Built-in / plugin (declared, N)` 段整体省略，不要据此报缺行或缺段；数字仅示意，以本次运行为准：

```text
=== skill inventory ===
generated: 2026-10-26T14:10:00+01:00
user root: C:\Users\Administrateur\.qoder\skills | count: 35
project root: C:\Users\Administrateur\Desktop\IMAM8MAHDI\.qoder\skills | count: 2
local total: 37 = 35 user + 2 project
built-in/plugin (declared, not on disk): 15
duplicates across roots: none
anomalies: 0

## User-level (35)
- ...

## Project-level (2)
- ...

## Built-in / plugin (declared, 15)
- ...

## Anomalies
none
```

用了回答窗口快照（分支 B）时，上面的清单块必须原样来自快照那次运行的 stdout，并原样附上 compare 那次运行的 drift 段：

```text
## Drift vs snapshot (2026-10-26T13:57:27+01:00)
added: 0 | removed: 0 | moved: 0 | description changed: 0 | content changed: 0 | unchanged: 43
- no drift detected
```

脚本没有 `stability:` 行。上报时可用一句话概括，但须注明是你按两次 `generated` 计算的，例如 `stability: 13:57:27 -> 13:57:28 | unchanged: 43 | no drift`。两次 `generated` 相同（同秒）时写 `window: <1 s`，不能改写成「数分钟内无变化」。需要更长窗口时用同一路径间隔 60–120 秒再 `--compare`，并同时报告新的 `generated`。

`exit 0` 只表示无结构异常且分组校验通过，不表示无漂移；必须读 `## Drift vs snapshot` 段。

回答时保留 `local total = user + project` 这一行；分别给用户级与项目级清单；内置/插件单列并注明来源；有异常时逐条列出，不省略。为区分临时异常而重跑时，写出两次 `generated` 时间戳；仅单次出现的异常标为「临时/可能正在创建或改写」，不写成已安装清单的结论。

## JSON 输出（`--format json`）

顶层键：`format`、`generated_at`、`user_root`、`project_root`、`counts`（`user`/`project`/`local`）、`skills`、`anomalies`、`duplicates`、`builtin`、`groups`、`group_errors`、`drift`。

- `skills[]`：`dir`、`root`、`path`、`name`、`description_sha256`、`desc_chars`、`size`、`mtime_ns`、`sha256`、`has_skill_md`；**不含 description 正文**，需要全文时读对应 `path`。
- `drift`：未用 `--compare` 时为 `null`；否则含 `snapshot_generated_at`、`old_counts`、`new_counts`、`added`、`removed`、`moved`、`description_changed`、`content_changed`、`unchanged`。
- JSON 模式下 `--snapshot` 不打印 `snapshot written:`，以传入的字面路径为准。
- 快照文件本身只有 `format`、`generated_at`、`user_root`、`project_root`、`counts`、`skills`、`anomalies`，不含 `duplicates`、`builtin`、`groups`、`drift`。

## 失败模式

| 现象 | 原因 | 处理 |
|---|---|---|
| 分组合计与总数不一致 | 名单来自旧快照 | 用同一次 `--groups` 运行重新生成，不改数字 |
| 找不到独立的 `assigned = local total` 行 | 它只出现在标题 `## Groups (validated: …)` 内；失败时改为 `## Groups (INVALID)` + `## Group errors` | 读标题行或 `## Group errors`，不要另造计数行 |
| 用户级数量正确但清单混入项目级 Skill | 目录已跨根移动 | 报告 `moved`，按脚本的 `root` 分列 |
| 内置/插件被算进本地总数 | 把会话列表当成文件系统 | 用 `--builtin` 单列，本地总数只加 user + project |
| 输出没有 built-in 行或 Built-in 段 | 未传 `--builtin`（默认） | 属正常形态；需要内置清单时传 `--builtin`，否则不要报缺行 |
| 目录存在却没出现在清单 | 缺 `SKILL.md` | 看异常段 `missing-skill-md`，不计入 `count` |
| description 长度没变但内容变了 | 并发改写 | 脚本比较 `description_sha256`，按 `description changed` 报告 |
| 两次运行计数不同 | 期间有并发写入 | 重跑并记录两次时间；仍不同就同时报告两个状态 |
| 快照用了固定共享名 | 多个会话写同一路径 | 换带时间戳或会话 ID 的唯一名，`--compare` 复用同一路径 |
| 快照被写进 skills 根 | 脚本只校验父目录存在，不拦截根内路径 | 自行选 `.qoder/tmp` 等根外路径；已写错则删除该文件并用唯一名重写 |
| 对比报出大量 `removed`/`added` 但文件未动 | 两次调用用了不同的 `--user-root`/`--project-root`；脚本不校验快照记录的根 | 用同一组根重跑 compare，自定义根两次都写全 |
| 异常只在一次运行出现 | 并发创建或改写中的临时状态 | 间隔 60–120 秒重跑；两次都存在才写成结论，单次标「临时」 |
| 无早期快照却声称「期间没有变化」 | 只跑了枚举 | 在回答窗口内先 `--snapshot` 再 `--compare`，报告两次 `generated` |
| 单次同时传 `--snapshot --compare` 得到 `exit 2` 或比较的是旧名单 | 脚本先比较后写快照 | 拆成两次独立调用，先写后比 |
| 对比显示 unchanged 但公布的是更早的清单 | 清单与快照不是同一次运行，或快照运行的 stdout 未被保留 | 保留并公布快照那次运行的完整 stdout；丢失时重做 snapshot→compare，不要用更早名单补位 |
| 两次 `generated` 相同却按较长窗口表述 | 脚本时间只到秒，同秒即窗口 < 1 秒 | 写 `window: <1 s`；需要更长窗口时间隔 60–120 秒再 `--compare` |
| drift 非零但退出码为 0 | 漂移不影响退出码 | 读 `## Drift vs snapshot` 段，按变化类型报告并用第二次枚举出清单 |
| 输出里找不到 `stability:` 行 | 脚本不打印该行，只有 `## Drift vs snapshot` 段 | 读 drift 段；人工 stability 行须注明由两次 `generated` 计算 |
| JSON 里没有 description 文本 | 仅输出 `description_sha256` 与 `desc_chars` | 读 `skills[].path`，或改用 md 模式 |
| JSON + `--snapshot` 没有 `snapshot written:` | 该行只在 md 模式打印 | 以传入路径为准，检查文件是否生成 |
| 项目级清单为空 | 当前目录树没有 `.qoder/skills` | 用 `--project-root` 指向真实根，不要臆造 0 |

## 退出码

- `0`：无异常且分组校验通过；
- `1`：存在结构异常或分组校验失败（输出仍然完整，异常段可见）；
- `2`：用法或环境错误（根不存在、PyYAML 缺失、快照/分组文件不可读、快照目录不存在）。

## 验收

- [ ] `local total` 等于 user + project，且与清单条数一致；
- [ ] 内置/插件单列且未计入本地总数；
- [ ] 未传 `--builtin` 时没有误报缺 built-in 行或段；
- [ ] groups 输出使用标题 `## Groups (validated: …)`；INVALID 时已读 `## Group errors`；
- [ ] 有异常时已逐条报告，没有把解析失败说成「全部正常」；
- [ ] 用了快照时已报告漂移，未运行对比时未声称「没有变化」；
- [ ] 无早期快照时已完成 snapshot→compare，并报告两次 `generated` 与 `unchanged`；
- [ ] 快照那次运行的完整 stdout 已保留并作为公布清单，未被重定向丢弃；
- [ ] 公布清单来自快照那次运行，未用更早名单冒充稳定窗口；
- [ ] 两次 `generated` 相同时已标注窗口 < 1 秒，或已间隔 60–120 秒复比；
- [ ] 快照名唯一（含时间戳或会话 ID），`--compare` 与 `--snapshot` 使用同一路径；
- [ ] 快照写在两个 skills 根之外（脚本不强制，需自行确认）；
- [ ] `--snapshot` 与 `--compare` 使用同一组根（自定义根时两次都显式重传）；
- [ ] compare 的 `## Drift vs snapshot` 段已原样附上；若写了 `stability:` 行，已注明由两次 `generated` 计算而非脚本输出；
- [ ] 异常经过短间隔重跑确认；仅单次出现的已标为临时并附两次 `generated`；
- [ ] 报告包含实际运行时间，便于下次比较。

## Resources

- `scripts/inventory_skills.py`：只读枚举、frontmatter 解析、快照与漂移对比；`--format json` 输出机器可读清单。依赖 PyYAML。正常调用不写任何文件；只有显式 `--snapshot` 会写指定 JSON。
