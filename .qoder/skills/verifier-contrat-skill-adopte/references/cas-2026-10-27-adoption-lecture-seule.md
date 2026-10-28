# 案例：并发产出包的只读验收（2026-10-27）

## 来源

- 验收会话：`ede0647e-2808-429d-bf43-27d0782aafd6`（标题「创建修复契约 Skill」）。读取时 `runtimeState=ready`、`revision=52`、`hasMoreBefore=false`，返回 1 个用户回合与 1 个助手回合；用户在 `AskUserQuestion` 中选择「只读保留并验收（推荐）」。
- 被验收包的写入者：`f38c2627-432b-4f25-a08e-86c5129f4b14`（标题「创建合同修复技能」）。验收期间 `runtimeState=running`；本文件写作前的最后一次读取（14:11 +0100）仍为 `running`，`activeTurnId=d99e071c-43a3-400e-9a59-1739041f022e`，`revision=31`。
- 被验收包：`reparer-contrat-sortie-skill`；其文档讲述的外部目标：`inventory-installed-skills`。
- 时间：正文未注明时区者为本地 `+0100`。

## 时点记录

| 时点 | 事件 |
|---|---|
| 14:03:39 | 目标目录出现，早于验收方首次 `ls` 约 12 秒 |
| 14:04:02 | `SKILL.md` 12 588 B |
| 14:04:25 | `references/cas-2026-10-27-contrat-sortie.md` 5 556 B |
| 14:04:38 | `references/harnais-repasse.md` 3 880 B |
| 14:05:05 | `SKILL.md` → 12 604 B（仍在变化） |
| 14:05:40–41 | 定稿：`SKILL.md` 12 605 B，案例 5 561 B |
| 14:05:53–14:06:11 | 5 次采样同一树指纹 `fb888c32958880d8d4830eb0744c35418248ab646c1658deb7ebfd6e88946649`，`STABLE after 16s` |
| 14:06 | `skill-file-qa`：`RESULT PASS`、9 pass / 0 fail / 0 warn、`Files (3)`、body 179、description 767 字符、本地引用 2、跨 Skill 引用 6、`python=0 js=0 skipped=3`、RC 0 |
| 14:07:40 | 复核哈希与 QA 指纹一致，未再变化 |

14:07:40 的完整哈希：

| 文件 | 大小 | SHA-256 |
|---|---|---|
| `SKILL.md` | 12 605 B | `9babc1f1f42a9d136e583f810a361d3466c1c2e69da79880b844a49cf2f13232` |
| `references/cas-2026-10-27-contrat-sortie.md` | 5 561 B | `03bcd092ceac21f781ec454eccfb823429d87b85cb4259e5df7087f21a2fdea8` |
| `references/harnais-repasse.md` | 3 880 B | `01c9ae4b5bb5dc6a4dcf56e91fe17de979f0473cfc5623f14d4955ad45951d79` |

## 夹具与复放

夹具根：`rep-contract-verify-20261027T1407`。包副本与 `inventory-installed-skills` 副本同放在 `fixture/`，脚本哈希 `262998a35c11a7e0c89688d539a48b8d79230cc5af394b1ef4fb4c9bab8a5936` 与安装目录一致。

| 运行 | RC | 关键输出 |
|---|---|---|
| `--format json` 枚举 | 0 | 顶层 12 键；`skills[]` 10 键；`drift=null` |
| md 模式 `--snapshot` | 0 | `snapshot written` 1 次；文件 979 B |
| 同根 `--compare` | 0 | drift 段 1 次、`stability:` 0 次、`- no drift detected` 1 次 |
| 异根 `--compare`（首次） | **2** | `ERROR: project root must differ from the user root: ...\empty-root` |
| 异根 `--compare`（两个不同空根） | 0 | `added: 0`、`removed: 1`、`unchanged: 0`、`- removed: user/inventory-installed-skills` |
| JSON + `--snapshot` | 0 | `snapshot written` 0 次，文件已生成 979 B |
| 单调用同时 `--snapshot --compare` | 2 | `ERROR: cannot read snapshot: [Errno 2] ...` |

首次异根复放把同一空目录同时传给 `--user-root` 与 `--project-root`，脚本拒绝并要求两个根不同。这是**夹具构造错误**，不是文档未复现；改为 `empty-root` 与 `empty-root-2` 后才得到假漂移且 RC 0。

案例文件把快照记为 939 B，本次复放观测为 979 B。字节数随根路径长度变化，只能作观测，不能写成契约。

14 项断言全部为 TRUE：

```text
JSON_TOP12_TRUE  SKILLS_KEYS10_TRUE  SKILLS_NO_PLAIN_DESC_TRUE  DRIFT_NULL_TRUE
SNAPSHOT_KEYS7_TRUE  STABILITY_ZERO_TRUE
CONTROL_DRIFT_HEADER_TRUE  CONTROL_COUNTS_TRUE  CONTROL_NO_DRIFT_TRUE
CROSS_FALSE_DRIFT_RC0_TRUE  CROSS_REMOVED1_TRUE  CROSS_UNCHANGED0_TRUE
JSON_SNAP_NO_HINT_TRUE  JSON_SNAP_FILE_TRUE
```

`STABILITY_ZERO_TRUE` 与三个 `CONTROL_*_TRUE` 在同一断言脚本内产生，零出现有正对照支撑。

## 时效与覆盖

- 案例称目标 Skill 修复后为 `f11285448017c28bca799ade27352e43f945e8dfe4017ae3fd2352f4067a70c1`（15 985 B、body 182）；验收时磁盘为 `b878d015c3e54c15a40ebfe601a83a97b574dbd082c16464bd0f63ab556144ea`（17 368 B、192 行）。引用值出现 1 次，磁盘现值出现 0 次 → STALE。
- QA 报 `python=0`，但该包 references 中的 Python 模板单独编译得到 `PY_BLOCK_COMPILES=True`。校验器的代码块检查不覆盖 references。
- 夹具清理得到 `BASE_REMOVED=TRUE`，安装目录与目标目录均无缓存。

## 后续漂移（14:10:58 复观察）

本 Skill 写作期间再次复核：

| 文件 | 14:10:58 状态 |
|---|---|
| 被验收包 `SKILL.md` | 12 722 B、183 行、`89c789a0f1c9ca97b364d5a06f800a48d72ff256601760ab5a174ad4faf9e601` |
| 被验收包案例 | 5 927 B、`0a9713cdcd8fa50b83a4e1d7707f32c4e1059d14e163288c92530e57ab5c1f20` |
| 被验收包 harness | 4 001 B、`600a7f9b302148aca4ab1425846e7bcc95eab2d9672702989169bf52da5f7503` |
| `inventory-installed-skills/SKILL.md` | 17 368 B、`ef84d4189167a4f33664d00337523e429d6e11d0a5f3fd2340207b18bfd9ce28`、mtime 14:07:48 |

被验收包已把 `b878d015…` 写成「现为」，但 14:07:48 起磁盘已是 `ef84d418…`。带「现为」的表述在快速变化的包里仍会立即过期，因此本 Skill 只接受带时点观测。

## 分级

- 已核实：上表中的时点、各次 RC 与输出、14 个令牌、QA 计数、全部哈希，均来自会话工具输出或本次落盘重算。
- 人工推断：14:10 的改写与本次只读验收的发现相关；未读到该会话的对应回合，不能断言因果。
- 未验证：其他操作系统与 shell、写入者的最终终态、被验收包脚本层是否会补根一致性防护。

## 边界

- 本案例证明「静止 → 冻结 → 外部目标复制 → 复放 → 时效观测 → 清理」这条只读链路可执行，不证明被验收包的契约设计正确。
- 键集、错误串与令牌属于 `inventory-installed-skills` 的实测值，换目标必须重测。
- 文中的哈希只对标注时点有效；引用前先重算。
