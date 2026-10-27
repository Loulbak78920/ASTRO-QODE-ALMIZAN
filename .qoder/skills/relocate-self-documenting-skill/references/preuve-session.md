# 证据 — 会自述位置的 Skill 迁移审计

本文件记录来源会话中可复核的字段与逐字原文。哈希、行号和会话 revision 都是带日期的观测值，不是可复用常量。

## 会话链

| 会话 | 角色 | 状态 |
|---|---|---|
| `42a40382-1306-4555-b8b8-6679ee71c9ac` | 更新绝对路径 Skill、重载、把该 Skill 自身移到项目级并验证 | 2026-10-26 读取 revision 26，`hasMoreBefore: false`，`runtimeState: ready`，6 个用户回合 |
| `7aa93ddf-da58-4980-af69-77103562a90f` | 上游会话，首次记录 7 处前缀替换的移动 | 仅作为前缀流程的来源；本 Skill 不复述其证据 |

## 观测（2026-10-26，+0100）

### 1. 自移动与 0/0

12:42 用户指令：「move skill-absolute-path-references to project skills directory」。

- 旧位置：`C:\Users\Administrateur\.qoder\skills\skill-absolute-path-references`
- 新位置：`C:\Users\Administrateur\Desktop\IMAM8MAHDI\.qoder\skills\skill-absolute-path-references`
- 移动后旧目录 `OLD_ABSENT`；3 个文件哈希移动前后一致：SKILL.md `c9b7f194…`、证据 `343483aa…`、脚本 `dca3852d…`。
- 该 Skill 自身不含绝对路径：旧前缀 0 / 新前缀 0；没有执行前缀替换，SKILL.md 未改。

### 2. 0/0 之后的过期叙述

移动把证据文件中的这句话变成过期状态：

```text
2026-10-26 13:27–13:37 在用户级 Skill 上原地更新 SKILL.md 与本节证据，未移动本 Skill，未改脚本。
```

该句不含路径，前缀计数为 0，因此替换与计数步骤不会提示它。移动完成后的收尾编辑把它改为：

```text
2026-10-26 13:27–13:37 在用户级位置原地更新 SKILL.md 与本节证据，该轮未移动本 Skill、未改脚本。同日后续用户回合把本 Skill 本身移到项目级，见下节。
```

改写做了两件事：用「该轮」限定时间，并补一句当前状态。证据文件哈希 `343483aa…` → `f4f158f4…`；SKILL.md 仍为 `c9b7f194…`。

结论：0/0 只证明没有路径需要替换，不证明叙述仍然正确。

### 3. 斜杠命令与可见性

- 12:40 用户输入 `/ skills reload`（中间有空格）；未被识别为命令。代理说明该命令需由客户端执行，不能代跑。
- 12:41 用户输入 `/skills list`；代理同样无法执行，改为列出两个 skills 根目录。
- 12:46 用户要求「reload skills 并验证本 Skill 是否出现在项目级列表中」。代理实际触发 Skill 加载，返回 base directory 为项目级新路径；项目级列表 2 项；用户级无残留；本次会话的技能清单已包含该 Skill。
- 未验证：客户端面板是否刷新。磁盘与运行时解析已指向新路径，但 `/skills reload` 的实际行为未由代理独立验证。

## 状态划分

| 项目 | 状态 | 依据 |
|---|---|---|
| Skill 自身移到项目级且旧目录消失 | 已观测 | 12:42 回合输出 |
| 移动前后 3/3 哈希一致 | 已观测 | 移动后哈希与移动前逐项相同 |
| 旧/新前缀 0/0，无需替换 | 已观测 | 计数输出 |
| 「未移动本 Skill」在移动后成为过期叙述 | 已观测 | 原句与改写句的编辑原文（项目 JSONL） |
| 改写后证据哈希变化、SKILL.md 未变 | 已观测 | `343483aa…` → `f4f158f4…`；`c9b7f194…` 不变 |
| 代理不能执行 `/skills reload` 或 `/skills list` | 已观测 | 12:40、12:41 回合 |
| 运行时加载解析到项目级新路径 | 已观测 | 12:46 回合返回 base directory |
| 客户端面板已刷新 | 未验证 | 需要用户执行斜杠命令 |
| 复制到新位置的场景 | 未验证 | 来源会话只执行移动 |

## 脚本契约实测（2026-10-26，一次性夹具）

| 用例 | 实际输出 | 退出码 |
|---|---|---|
| `--help` | usage 文本 | 0 |
| 0/0 + 2 处位置叙述 | `NOTE 0/0`、`RESULT REVIEW`、2 条命中 | 0 |
| 字面前缀 2 处 + 旧目录存在 | `FAIL old prefix still present`、`FAIL old directory still exists` | 1 |
| 前缀写法不一致（`/c/...` 与 `C:/...`，禁用 MSYS 转换） | `WARN ... normalized matches`、`RESULT REVIEW` | 0 |
| 目录存在但无 SKILL.md | `ERROR SKILL.md not found` | 2 |
| 目录不存在 | `ERROR skill directory not found` | 2 |
| 只给 `--old-prefix` | `ERROR pass --old-prefix and --new-prefix together` | 2 |

夹具位于 `.qoder/tmp/relocation-audit-330/`，实测后已删除。夹具中的脚本文件含「用户级」字样但不进入叙述扫描，确认词表只扫描文档。

## 重新使用规则

- 不复制旧哈希、旧行号或旧 PASS；每次重新读取并重新运行。
- 0/0 时仍要审计范围陈述与时态陈述，不能以「无需替换」结案。
- 历史陈述必须限定轮次并补当前状态，否则按过期处理。
- 分类先于改写；`VALID` 与 `GENERIC` 保留。
- 斜杠命令交给用户执行；代理只报告磁盘与运行时解析结果。
