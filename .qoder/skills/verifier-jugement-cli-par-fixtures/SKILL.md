---
name: verifier-jugement-cli-par-fixtures
description: "在把某个依赖 CLI 的返回码或判定字段语义写进 SKILL.md 前，先用同一批字节级夹具对两个工具做 A/B：夹具建在 Skill 目录外，先断言落盘字节符合预期（BOM、空值、边界值、多行、缺文件、非 UTF-8、混合 EOL、尾随空格、重复键、引号内字面量与转义写法），用 subprocess 直接取返回码且不经管道，再把依赖工具与真正的验收工具（如 validate_skill.py）并排跑同一用例，逐项记录 rc、判定字段与结论，把分歧写成文档结论并指定权威工具与各 rc 类别；夹具目录名须满足验收工具自身的规则（hyphen-case），否则 FAIL 会归因到夹具而不是被查属性。用于两个工具对同一输入结论不一致、guard 只测量不判定、rc=1 与 rc=2 混用、同一工具 inspect 与 replace 分歧、文档写入了未实测的判定语义、需要排除夹具构造错误。不用于管道吞码与 Windows 编码（windows-python-utf8-skill-scripts）、转义折叠与变异未生效（verifier-mutation-fixture-appliquee）、单工具契约审计（audit-skill-tool-contracts）、文档与自身脚本对等（verifier-parite-doc-script-skill）、夹具重放（replay-skill-reference-fixtures）或写入后验收（skill-file-qa）。关键词：判定一致性、双工具 A/B、rc 类别、夹具归因、字节断言、权威工具；English: CLI verdict parity, dual-tool fixtures, exit-code classes, fixture attribution, authoritative validator."
---

# 依赖 CLI 判定一致性：双工具夹具 A/B

## 目标与边界

把「某工具会拒绝/接受某输入」「rc=2 表示环境错误」写进 SKILL.md 之前，用同一批字节级夹具并排运行依赖工具与真正的验收工具，把 SAME / DIVERGENT 逐行测出来，再指定权威工具与每个工具的 rc 类别。判定语义只能按实测行书写，不能按 `--help`、字段名或上一次会话的印象书写。

- 只读审计两个工具；夹具放 Skill 目录外，不修改被审工具。
- 结论必须绑定两个脚本的 SHA-256 与本次运行时间。
- 不用于：管道吞码与 Windows 编码 → `windows-python-utf8-skill-scripts`；转义折叠、变异未生效 → `verifier-mutation-fixture-appliquee`；单工具契约与一次负向探针 → `audit-skill-tool-contracts`；文档与自身脚本对等 → `verifier-parite-doc-script-skill`；既有夹具重放 → `replay-skill-reference-fixtures`；写入前声明台账 → `verify-skill-doc-claims-before-edit`；写入后格式验收 → `skill-file-qa`；非 ASCII 字节断言 → `verifier-unicode-fichiers-windows`。

## 何时使用

- 两个工具对同一输入给出不同结论：PASS vs FAIL、rc 0 vs 2。
- 正要写「工具 X 拒绝 Y」或「rc=2 表示环境错误」这类句子。
- 某字段只测量不判定（超限时仍 `ok: true`），容易被当成通过。
- 同一工具的子命令自相矛盾（`inspect` 通过、`replace` 拒绝）。
- 夹具 FAIL 可能来自夹具自身（名字、布局），而不是被查属性。

## 不可协商规则

1. **一组夹具，两个工具。** 同一字节、同一参数形态、同一工作目录；不要给两个工具各写一套夹具。
2. **先证明夹具字节。** 用 `bytes`/hex 构造；对制表符、反斜杠、BOM、CRLF、非 UTF-8 先记 SHA-256 并用 `od -c` 确认。夹具不是想测的字节，就没测任何东西。
3. **直取返回码。** `subprocess.run(...).returncode` 或运行后立刻保存 `$?`；禁止 `cmd | head; echo $?`。
4. **判定不是 rc。** `RESULT`/判定文本、判定字段、rc 分三列记录；`rc=0` 与 `ok=true` 可以和 FAIL 同时出现。
5. **夹具必须可归因。** 目录名与 frontmatter `name` 都是 hyphen-case 且彼此相等；否则验收器先因自身规则 FAIL，该行不能算作被查属性的证据。
6. **分歧必须有权威。** 每个 DIVERGENT 行写明哪个工具治理该属性、为什么；「两个都对」不是结论。
7. **没有行就不写。** 文档只能写本次矩阵里测到的行，并绑定两个工具的哈希。

## 第 0 步 — 冻结两个工具

- 记录两个脚本的路径、大小、mtime、SHA-256。
- 读源码中的退出码常量（如 `EXIT_FAIL = 1`、`EXIT_ENV = 2`），不要从 `--help` 推断。
- 标出哪些输出是「测量」、哪些是「判定」：只测量的工具在超限时仍可能 `ok: true`、`rc=0`。
- 记录验收工具的 `RESULT` 行格式，以及 FAIL 时它自己的 rc。

## 第 1 步 — 按属性声明夹具矩阵

先写属性，不写期望输出（按输出反推矩阵是循环论证）：

| 属性 | 夹具形态 |
|---|---|
| 空值 | `description: ""` |
| 边界 | 上限-1 / 上限 / 上限+1 |
| 多行 | 值跨 3 行 |
| 缺文件 | 目录内无 `SKILL.md` |
| 非法 UTF-8 | 值含 `\xff` 字节 |
| 混合 EOL | CRLF 与 LF 混用 |
| BOM | 文件头 `EF BB BF` |
| 尾随内容 | 值后空格、`# 注释` |
| 重复键 | 两个 `description` 键 |
| 引号内字面量 | 真制表符、`#` |
| 引号内转义 | 字面反斜杠 `t`、字面反斜杠 `uXXXX` |
| 引号外控制符 | 裸制表符 |

复制此表并加两列：工具 A 期望、工具 B 期望；未知就留空，不要猜。

## 第 2 步 — 字节级构造与归因

- 全部用字节写入；需要非 ASCII 时从已有文件取行或转 hex，不在命令里手写多层转义。
- 风险夹具写后立即 `sha256sum` 与 `od -c`：真制表符显示为 `\t`，字面反斜杠显示为单独的 `\` 后跟 `t`；两者必须分开确认。
- 夹具目录名 = `name` = hyphen-case；除被查属性外，其余字段保持一个合法包的最小形态。
- 放 `~/.qoder/tmp/<任务>/fixtures/<case>/`；结束后只删本任务目录。

## 第 3 步 — 直取返回码

```python
p = subprocess.run([sys.executable, "-B", tool, *args],
                   capture_output=True,
                   env=dict(os.environ, PYTHONIOENCODING="utf-8"))
rc = p.returncode
```

- 保存 stdout 最后一行 JSON 或 `RESULT` 行；不要只留 rc。
- 管道只用于人类阅读；取码必须在管道之前完成。
- 控制台编码只影响显示，不得参与判定。

## 第 4 步 — 并排判定与分类

| 列 | 内容 |
|---|---|
| 用例 | 属性名 |
| 字节 | sha256 前缀 / `od -c` 关键片段 |
| 工具 A | rc、判定字段、结论 |
| 工具 B | rc、`RESULT`/结论 |
| 分类 | SAME / DIVERGENT |
| 权威 | 该属性归谁；理由 |

至少区分四种分类：

- `DIVERGENT_VERDICT`：一方 PASS、一方 FAIL。
- `DIVERGENT_RC`：结论同向但 rc 类别不同。
- `DIVERGENT_FIELD`：同一工具内部字段不同源（长度取末键、行号指首键）。
- `UNATTRIBUTED`：夹具自身不合规；修好前不写进文档。

rc 类别按工具分别记录；不要把一个工具的「2 = 环境」移植到另一个工具。

## 第 5 步 — 写入文档并绑定哈希

- 只写第 4 步测到的行：谁治理哪个属性、每个工具的 rc 类别、只测量的字段、不支持或未覆盖的属性。
- 写入后重跑整个矩阵，再回读文档：旧措辞计数必须为 0，新结论计数至少 1。
- 跑 `skill-file-qa`；分别记录两个工具与文档的 SHA-256。

## 决策表

| 情形 | 动作 |
|---|---|
| 两工具结论相反 | 判 DIVERGENT；按验收工具治理写文档，并注明依赖工具的行为 |
| `rc=0` 但输出 FAIL | 记录 rc 与结论分离；不得写「返回 0 即通过」 |
| 只测量工具报 `ok: true` | 检查判定字段（如 `over_limit`、`remaining`），不把 `ok` 当结论 |
| 同工具子命令矛盾 | 分别记录 `inspect` 与 `replace`；文档写清哪条路径拒绝 |
| 夹具名不符验收器规则 | 先修目录名与 `name`；该行在修复前为 UNATTRIBUTED |
| 夹具字节与预期不符 | 停止；用 hex 或 `od -c` 重建；不得改期望迁就夹具 |
| 验收工具 PASS 而依赖工具拒绝 | 写「验收器允许、编辑工具拒绝」，不写「输入非法」 |
| 两个工具都未覆盖该属性 | 标注 UNOBSERVED；不得推断 |

## 完成检查

- [ ] 两个工具的 SHA-256、rc 常量与判定字段已从源码确认。
- [ ] 夹具矩阵按属性声明，未按工具输出反推。
- [ ] 风险夹具已用 sha256 与 `od -c` 证明字节。
- [ ] rc 直取，未经过管道。
- [ ] 每个 FAIL 都能归因到被查属性（目录名、`name`、最小合法包）。
- [ ] 分歧表完整，每个 DIVERGENT 有权威与理由。
- [ ] 文档结论逐行对应实测行，并绑定两个工具哈希。
- [ ] 写入后重跑矩阵；`skill-file-qa` PASS；分文件哈希；无 `__pycache__`。

## 资源

- `references/cas-2026-10-27-guard-vs-validate-skill.md`：14 行主表、8 行 `replace` 对照、三处构造陷阱与最终落盘结论。
- 被审 guard 的归属：`edit-skill-frontmatter-description`。
- 委派：`windows-python-utf8-skill-scripts`、`verifier-mutation-fixture-appliquee`、`audit-skill-tool-contracts`、`verifier-parite-doc-script-skill`、`replay-skill-reference-fixtures`、`verify-skill-doc-claims-before-edit`、`verifier-unicode-fichiers-windows`、`skill-file-qa`。
