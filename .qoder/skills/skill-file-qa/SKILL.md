---
name: skill-file-qa
description: "在创建或更新 Skill 后对 SKILL.md 做写入后验收：用 PyYAML 严格解析 frontmatter（description 或其他纯量含「冒号+空格」时必须加引号）、校验 name 与目录一致、单行 description、正文行数、文件清单、本地引用与跨 Skill 引用（反引号中的已安装 Skill 名须解析到用户级/项目级 skills 目录且目标 SKILL.md 存在），抽取 Python/JS 代码块做语法检查，校验前后等待文件稳定并复核 size/mtime/SHA-256 指纹（并发写入或等待超时则失败），并对真实产物实跑文档中的验收片段，按文档标注的工作目录逐条实跑 bash/sh 命令并记录占位符替换，不能把 skipped 当作已验证；当目标 Skill 自带 CLI 验证器时，用临时副本逐项破坏不变量，断言退出码 0/1/2、严格警告与外部资源开关，清理副本并用 SHA-256 证明原件未变。用于 Skill 创建或更新后的交付前检查、Skill 未出现在可用列表、frontmatter 解析失败、跨 Skill 引用失效、验证器负向测试未覆盖、Windows 只读夹具导致 rmtree 报 WinError 5，或需要区分已验证项与未触发分支、文档命令无法原样执行、占位符（如 SKILL_DIR）未说明替换方式、bash 块被跳过导致 PASS 未覆盖路径错误、参考文档快照过时、references 与 SKILL.md 不一致、围栏代码块未配对、验收前文件已被改写、PASS 的版本不是方案基线、基线哈希不一致时；全部测试与真实运行结束后仍须双采样 SKILL.md 并与 validator 的 Fingerprint (final) 比对，变化时旧 PASS 作废、合并重跑，只引用最终稳定版本哈希；验收开始前先与方案或写入时基线的 size/SHA-256 比对，不同则旧 PASS 作废并按 UTC 窗口归因写入者（含 ERROR 编辑）、区分本会话与外来会话，锚点消失或部分应用交 adopt-source-session-update；参考文档记录了 SKILL.md 的行数、字节或哈希时，最终门要重算比对并回改失真项，复核围栏配对与标题，references 自身最终哈希只写入报告。"
---

# SKILL.md 写入后验收

## 目标

在 Skill 创建或更新后，检查磁盘上的真实文件，而不是依赖写入成功的提示。先做可复现的静态校验，再用真实产物运行文档中的验收片段；目标 Skill 带 CLI 验证器时，再做临时副本负向测试。最后区分已验证、仅静态检查、未触发分支。

## 工作流

### 1. 绑定基线并读取实物

读取 `<skill-dir>/SKILL.md`，并列出目录内全部文件。确认目录名、文件数量和正文，而不是凭记忆描述。

写入后不要立刻验收。若同一 Skill 可能被并发流程改写，先用校验器等待文件稳定；读取后再写文件会使前面的检查失效。报告必须记录实际读取版本的 SHA-256。

开始验收前先绑定基线：取方案或最后一次写入时记录的 size 与 SHA-256，与当前文件比对。两者不同且不是行尾切换时，本次校验器的 PASS 不能作为该方案的验收结果，按「基线对比与写入者归因」处理，并写明旧 PASS 作废。

### 2. 运行结构校验

本 Skill 的校验脚本位于其安装目录的 `scripts/validate_skill.py`。从该目录执行；`<skill-dir>` 替换为目标 Skill 的绝对路径，`<workspace-root>` 替换为工作区根目录：

```bash
py -3 scripts/validate_skill.py <skill-dir> --workspace <workspace-root> \
  --stable-seconds 2 --stability-timeout 30
```

- Windows 上先确认解释器：`python --version` 若失败或提示 Microsoft Store，改用 `py -3`；不要假定 `python` 可用，也不要把个人绝对路径写进 Skill。
- 退出码：0 = 无 FAIL，1 = 有 FAIL（含稳定性等待超时或校验期间内容变化），2 = 用法或环境错误。
- 修复所有 FAIL 后再继续；WARN 表示未覆盖项，必须在报告中说明。
- 默认先等待 SKILL.md 在 2 秒内 size、mtime、SHA-256 完全不变，再读取；结束时重新计算并比对，内容变化立即 FAIL。已确认不会并发写入时可用 `--stable-seconds 0` 跳过等待，但仍保留起止指纹比对。
- 输出包含 `Fingerprint (start)` 和 `Fingerprint (final)`；报告中要写出实际 SHA-256，不能只写“文件存在”。
- 跨 Skill 引用默认在 `~/.qoder/skills` 与 `<workspace>/.qoder/skills` 中解析；非标准安装用可重复的 `--skills-root <dir>` 覆盖默认根，显式传入不存在的根是用法错误（exit 2）。

脚本检查：frontmatter 严格 YAML 解析、name 与目录一致、hyphen-case、单行 description ≤1024 字符、正文 <500 行、TODO、文件布局、本地引用存在性、跨 Skill 引用（正文反引号中的已安装 Skill 名 → 目标 SKILL.md 存在）、Python 代码块语法、JS 代码块语法、校验期间并发写入与起止指纹。它只读 Skill 文件，不写目标目录；JS 临时文件只写入系统临时目录并自动删除。

### 3. 文档命令可执行性

静态校验的 `skipped=N` 包含 bash/sh 块；`RESULT PASS` 不证明文档命令能运行。对 SKILL.md 与 references 中的每个 bash/sh 围栏块：

1. 分类为 `EXECUTED`（只读，或可在临时副本安全执行）、`ILLUSTRATIVE`（破坏性、需交互、缺真实产物）、`NOT_APPLICABLE`（非命令）。
2. 每条 `EXECUTED` 按块前标注的 cwd 原样执行，只替换已声明的占位符；记录 cwd、替换值、预期/实测退出码和关键输出。退出码直接捕获或用 `PIPESTATUS`，不让管道吞掉。
3. 占位符（`SKILL_DIR`、`PAGE.html`、`<skill-dir>`）必须在块前写出替换规则；没有规则的占位符是文档缺陷。文档只写规则，实际替换值记入报告，不把个人绝对路径写进 Skill。
4. cwd 必须写明；相对路径按该 cwd 解析。写成“项目根”但实际在子目录时必须改正。
5. 只读命令在真实环境执行；写、删、安装、上传、发布或访问生产环境的命令在临时副本执行，或标 `ILLUSTRATIVE` 并说明原因。不得为了跑通执行破坏性命令。
6. 失败时修命令、路径、cwd 或占位符，或把示例降级为 `text` 并注明不可执行；修完重跑，不要把失败的可执行块留在文档里。
7. 报告列出每条命令的 cwd、替换、退出码与结论；没有实跑的命令标“未验证”，不得用静态 PASS 代替。

### 4. 真实产物验收

静态检查不能证明行为正确。对文档中的每一条验收断言：

1. 找出可执行断言：行数、计数、字节、DOM 节点、返回码等，必须有明确预期值。
2. 使用真实输入（真实生成的 CSV/HTML、真实 Skill 目录），不用手写假数据替代。
3. 用 Write 把非平凡片段写入临时 `.py` 或 `.js` 文件再执行；不要把含反引号、引号的代码内联进 Bash。
4. 记录命令、真实输入、预期、实测；数字不一致时先调查，不修改预期来迁就结果。
5. 浏览器类验收按项目现有流程执行；截图不可用时只做结构校验，并明确说明。

不要自动执行与验收无关的文档片段，尤其是删除、上传、发布、安装或访问生产环境的命令。

### 5. 随附验证器负向测试

仅当目标 Skill 自带 CLI，且它声明了退出码、JSON 键集或开关契约时执行；没有任何契约时才在报告中写“不适用/未触发”。先分清两种形态：

- **项目验证器**：读取项目文件，可以破坏不变量；执行下面的 1–7 步。
- **仅声明契约的 CLI**：诊断、探测或审计工具，没有可复制的项目输入，“复制验证器 + 破坏夹具”不适用；但声明的退出码与输出契约仍要实测，见本节末尾。

不要用“不是项目验证器”把整个第 5 步标成不适用。本节不替代本 Skill 的静态校验；静态校验器自身的回归自测交给 `skill-validator-selftest`。

1. 先跑正向基线：用真实产物运行目标验证器，记录退出码、FAIL/WARN 数量和关键输出。基线不通过时先调查，不构造负向用例。
2. 复制到临时目录：把目标验证器及其读取的项目文件复制到系统临时目录，用显式 `--root`、`--csv`、`--html` 等参数指向副本。只改副本，不改原件；只运行验证器，不运行生成器或其他会写文件的脚本。
3. 每例只破坏一个不变量，并在用例之间恢复干净副本。下面用常见的 0/1/2 约定；目标验证器使用其他约定时按它的文档断言。至少覆盖：
   - 基线：退出 0，无 FAIL。
   - 断号或重复唯一键：退出 1，输出指出第一个断点。
   - 派生值或分布错误：退出 1。
   - CSV/HTML 单格不一致：退出 1。
   - 输入缺失或不可读：退出 2。
   - 外部资源：默认退出 1；有 `--allow-external` 时退出 0 + WARN。
   - 仅警告（过期日期、旧 docstring、硬编码派生值）：默认退出 0 + WARN；有 `--strict-warnings` 时退出 1。
   - 算法等价性破坏：退出 1。
   内容夹具按字节改写（`read_bytes`/`write_bytes`），不要用文本模式读写：编码或换行往返会改变字节，夹具就不再只破坏一个不变量。目标验证器同时校验输入完整性（源码 SHA-256、字节数、行数）时，内容夹具必须同步重算副本中的完整性字段；否则失败来自完整性门，目标门没有被隔离。
4. 逐例断言退出码精确相等，输出包含预期 FAIL/WARN 关键词，且失败只命中目标门：完整性项仍 OK，FAIL 条数与预期一致（如 `RESULT FAIL (1)`）；0 退出不得伴随 FAIL，1/2 必须给出可定位错误。日期/mtime 用例固定时钟或动态推导预期；复制后显式设置 mtime，避免复制时间造成假阴性或假阳性。
5. 用 `finally` 或 `TemporaryDirectory` 清理临时副本，并确认临时目录不存在。Windows 上夹具含只读文件（如 `VERROU.json`）时，`copytree` 或 `copy2` 会保留只读位，`rmtree` 抛 `PermissionError [WinError 5]`：复制时用 `copy_function=shutil.copyfile`，删除前对副本文件 `chmod(0o666)`，复制后再统一 `chmod(0o666)`。
6. 在运行开始时记录验证器读取的全部项目文件的 SHA-256，结束后重算比对；每次重新取基线，不复用旧会话哈希。原件哈希变化时停止并报告，不能宣称通过。
7. 在报告中列出负向用例表、退出码和未触发分支（例如目标验证器没有 `--strict-warnings`、Node 不可用、日期用例未固定）。

**仅声明契约的 CLI 的替代覆盖**（不满足 1–7 的前提时执行）：

1. 从 `--help`、代码或文档列出全部声明的退出码、JSON 键集与开关，逐个绑定到真实输入；每个声明的 rc 至少命中一次（成功、发现问题/拦截、用法错误各一），只测成功路径不算验证。
2. 用真实输入运行（例如真实的受限目录、真实文件），不要为通过而自造一个空目标。
3. 声明 `--json` 时，断言文档列出的全部键都存在，并断言内部字段不泄漏（例如给用法错误用的 `code` 不应出现在成功输出中）；“JSON 可解析”不等于契约满足。
4. 声明了解析分支（例如仅继承 ACE、仅属性、路径缺失）时，为每个分支在临时目录构造最小真实夹具，断言判定结果与 rc；只读代码推断不算。
5. 退出码直接捕获；管道会吞掉 rc，用 `PIPESTATUS` 或先重定向到文件再检查。
6. 结论写“已验证”或“部分适用（列出未覆盖的 rc/键/分支）”，不写“不适用”。

详细 harness 模板、来源会话已验证的 14 个用例、字节级夹具与完整性耦合和跨 Skill 引用自测边界见 `references/validator-negative-tests.md`。

### 6. 全部测试后的最终指纹门

校验器打印 `Fingerprint (final)` 只证明它自己的运行窗口内没有写入。第 3、4、5 步以及任何真实运行都发生在校验之后，期间仍可能有并发写入。全部测试结束后、写报告之前：

1. 对 SKILL.md 间隔至少 2 秒连续双采样，记录 size、mtime_ns 与 SHA-256；size 与 SHA-256 必须一致，仅 mtime 变化但字节相同不算失败。
2. 与本次校验器的 `Fingerprint (final)` 比对 size 与 SHA-256，不能只比本次双采样的两次。
3. 一致：该哈希是报告唯一可引用的版本，进入第 7 步。
4. 不一致：先按「EOL 切换与并发写入的区分」分类。仅行尾切换时不做合并或覆盖，记录原始与归一化哈希；若校验器窗口内发生过这次写入，在稳定版本上重跑。归一化哈希不同才按并发写入处理：本次 PASS 作废，完整重读 SKILL.md，保留并发新增内容，逐条确认本次预期修改仍在；不要覆盖、回退或“修回”对方内容。对合并后的版本重跑校验器，再执行本门禁。
5. 门禁之后若 SKILL.md 又发生写入（例如改错别字或补充规则），校验器结果与门禁一起作废，必须重跑；若只改 references 或 scripts，先重算该文件哈希，再执行第 7 条。
6. 报告写明旧 PASS 作废原因、变化前后的指纹与最终稳定版本，不能把“校验器曾 PASS”写成“当前版本已通过”。
7. **references 自洽性复核**（包内有 `references/` 时必做，否则报告标“未触发”）。在 SKILL.md 冻结之后执行：
   - 重算实际总行数、正文行数、字节、SHA-256 与 description 长度；在 `references/` 中检索已记录的同类值（`N 行`、`N B`、64 位十六进制、“最终”“更新后”“当前”），逐条比对。表格与正文同时记录时两处一起查。
   - 不一致时只改记录值，或把旧值明确标为“写入时快照，已被后续修改取代”；不得留下误导性的“最终”表述。改完再检索一次，确认没有第二处旧值。
   - 自指边界：references 不得记录自身最终 SHA-256 或最终行数（写入即改变哈希）；自身最终值写入报告或单独清单。“最终哈希由报告记录”是允许的写法。
   - 结构复核：围栏代码块成对（总数为偶数，且每块有闭合围栏）、标题层级完整、SKILL.md 资源清单列出的文件实际存在。围栏与标题是人工复核，不自动断言。
   - 复核后再改 references：重算该文件哈希；SKILL.md 的校验结果仍有效，但报告必须引用最终 references 哈希。若 SKILL.md 再改，整个最终门重跑。

该门的前 1–6 条只覆盖 SKILL.md；第 7 条覆盖 references 的快照与结构；scripts 与每个 references 的最终哈希都在报告中单独记录。

### 7. 报告

用下表汇总，不要把“语法通过”写成“运行通过”：

| 检查 | 方式 | 真实输入 | 预期 | 实测 | 结论 |
|---|---|---|---|---|---|
| frontmatter | PyYAML | 实际 SKILL.md | 可解析且 name 一致 | 见输出 | 已验证 |
| 跨 Skill 引用 | validate_skill.py 名称解析 | 实际 SKILL.md 反引号 | 目标 SKILL.md 存在 | N checked 或 0 found | 已验证或未触发 |
| 验证器正向 | 目标 CLI | 真实产物 | 退出 0、无 FAIL | 见输出 | 已验证或未触发 |
| 验证器负向 | 临时副本 | 每例一个破坏 | 按契约 0/1/2 | 见输出 | 已验证或未触发 |
| 原件完整性 | SHA-256 | 验证器读取的项目文件 | 前后一致 | 见输出 | 已验证或未触发 |
| 稳定性 | validate_skill.py 等待窗口 | 实际 SKILL.md | 窗口内 size/mtime/SHA-256 不变 | 见 Stability 行 | 已验证或未触发 |
| 基线对比 | 当前 size/SHA-256 vs 方案或写入时基线 | 实际 SKILL.md 与基线记录 | 相同；不同则旧 PASS 作废并归因 | 见输出 | 已验证或未触发（无基线） |
| 指纹复核 | SHA-256 起止比对 | 实际 SKILL.md | 起始 = 最终 | 见 Fingerprint 行 | 已验证 |
| 代码块 | ast.parse / node --check | 实际代码块 | 全部可解析 | 见输出 | 仅静态 |
| 文档命令 | 按标注 cwd 逐条实跑 | 实际 SKILL.md 与 references | 退出码与关键输出符合预期 | 见输出 | 已验证或未触发 |
| 最终指纹门 | 全部测试后双采样，对比 validator final | 实际 SKILL.md | 两次一致且等于 final | 见输出 | 已验证或未触发 |
| references 自洽性 | 重算行数/字节/哈希 + 围栏配对 | 实际 references | 记录值 = 最终值 | 见输出 | 已验证或未触发 |
| 注入正文 | 只读调用 + JSONL isMeta | 实际 SKILL.md 与当前会话 JSONL | 哨兵命中、去空行后正文相等、前后指纹一致 | 见输出 | 已验证或未触发 |
| 验收断言 | 实际运行 | 真实产物 | 文档预期值 | 实测值 | 已验证或未触发 |

`Stability` 行显示等待时长；`Fingerprint (start)` 与 `Fingerprint (final)` 的 SHA-256 必须一致。只记录其中一个不算复核。这两行只覆盖校验器运行期间；第 6 步的最终指纹门才覆盖此后的夹具与真实运行，报告引用的是最终门确认的版本。`基线对比` 行覆盖这两者之前：它证明验收对象就是方案对象；不一致时，其余各行只对另一个版本成立。

`local references: 0 checked` 只说明没有 Markdown 链接或可识别的路径引用，不代表跨 Skill 引用已检查；两项分开记录。

负向用例只写“验证器通过”不算完成；必须记录每例的退出码、关键输出和临时副本清理。`0` 退出但输出含 FAIL 视为失败。

在表后列出未触发分支，例如“Node 未安装，JS 块未检查”“错误路径未构造”“截图失败分支未复现”。没有运行过的分支不得标为已验证。

references 自身最终哈希只能出现在报告中，不能写进 references；参考文档记录 SKILL.md 的最终值可以，但必须在 SKILL.md 最后一次修改之后重算。未执行第 6 步第 7 条时标“未触发”，不得写“已验证”。

## Frontmatter 规则

- `description` 必须是单行字符串，≤1024 字符，同时写清“做什么”和“何时使用”。
- 纯量中出现 ASCII 冒号加空格时，整段加双引号。否则 PyYAML 报 `mapping values are not allowed here`，Skill 可能无法加载：

```yaml
# 错误：YAML 解析失败
description: Verify deliverables: CSV then HTML

# 正确
description: "Verify deliverables: CSV then HTML"
```

- `name` 使用 `^[a-z0-9-]+$`，且必须与 Skill 目录名完全一致。
- 不要用正则或手写 split 代替 YAML 解析；skill-creator 的检查清单不包含这一步。

## 并发写入与指纹复核

Skill 可能在验收期间被另一个流程改写。只比较最终读到的内容，会把旧版本的检查结果当成新版本。

三个窗口互不替代：基线到验收开始的比对（下一小节，唯一能发现「PASS 的版本不是方案版本」）；校验器运行窗口的 `Fingerprint (start)`/`(final)`；全部测试之后的第 6 步最终门。

- 默认 `--stable-seconds 2`：校验器连续观察到 size、mtime_ns、SHA-256 不变后才开始检查；`--stability-timeout 30` 控制最长等待，超时以 exit 1 结束。
- 校验结束前重新读取 SKILL.md 并打印 `Fingerprint (final)`。size 或 SHA-256 与起始值不同 → `FAIL fingerprint: SKILL.md changed during validation`，必须重跑；仅 mtime 变化但字节相同不算失败。
- `--stable-seconds 0` 只跳过等待，仍保留起止指纹比对；不要用它掩盖正在写入的文件。
- 报告必须写出实际起始/最终 SHA-256 和 mtime；无法给出时说明原因，不能宣称通过。
- 校验器不写目标 Skill 目录；如果验收期间有别的流程写入，最终指纹会暴露变化，但无法判断哪个版本是权威版本，只能等写入结束后重跑。
- 校验器内的起止指纹只覆盖它自己的运行窗口。真实产物验收、负向夹具和真实运行都在校验之后，必须在全部结束后再执行第 6 步的最终指纹门；只有与 `Fingerprint (final)` 一致的最终哈希才能写进报告。来源会话 `a48efc65`（2026-10-26）的 9,622 B 版本在 PASS 后被另一会话改写为 11,122 B，直到最终双采样才发现；完整案例见 `references/validator-negative-tests.md`。

### 基线对比与写入者归因

校验器与最终门都假定「验收的对象就是方案的对象」，这个假定可能已经失效。开始验收时：

1. **取基线。** 方案或最后一次写入时记录的 size 与 SHA-256，例如 validator 的 `Fingerprint (final)` 或双采样。没有基线时现场采样，并在报告中写「无基线，本次验收只覆盖当前版本」。
2. **比对当前文件。** size 与 SHA-256 都相同才继续。不同时先按下一小节判别：仅行尾切换则重设基线；EOL 归一化后仍不同就是内容写入。
3. **作废旧 PASS。** 内容写入意味着此前对该 Skill 的任何 PASS 都不是当前版本的结论。不要把「校验器 PASS」写成「方案版本已通过」，也不要沿用按旧行号写的方案锚点。
4. **归因写入者。** 用只读的 scan_skill_writers.py（在已安装的 `verify-injected-skill-body-freshness` 的 scripts 目录）扫描当前项目的会话 JSONL，窗口从基线 mtime 到当前时刻。`RESULT` 列标 `ERROR` 的编辑也要计入：它说明该会话尝试过但没有落地。

   `<scan-script>` = 该脚本的绝对路径；`<projects-dir>` = 当前项目在 `~/.qoder/projects` 下的会话目录；`<baseline-utc>` = 基线 mtime 换算后的 UTC 时刻（留几分钟余量）；`<skill-dir>` = 目标 Skill 的绝对路径。cwd 任意，全部用绝对路径。

   ```bash
   py -3 "<scan-script>" --scan-dir "<projects-dir>" --target "<skill-dir>/SKILL.md" \
     --since "<baseline-utc>" --include-results
   ```

5. **换算时区。** `--since`/`--until` 按 ISO-8601 解析，无偏移按 UTC；JSONL 时间戳是 UTC，validator 打印的 mtime 带本地偏移（如 `+01:00`）。把本地钟点直接写给 `--since` 会整体偏移并漏掉命中。实测同一目标：`--since 2026-10-28T01:00:00` 命中 0 条，`--since 2026-10-28T00:00:00Z` 命中 4 条。
6. **判读与应用。** 区分本会话与外来会话。外来写入即使没有触碰方案的锚点，也会改变行号与预算，方案必须在当前版本上重算；锚点消失或只应用了一部分时，先交 `adopt-source-session-update` 做逐项对账，再由 `planifier-budget-paquet-skill` 重算方案。
7. **重跑。** 在稳定版本上重跑校验器与第 6 步最终门，报告写明基线哈希、验收哈希、写入者会话 ID 与旧 PASS 作废原因。

来源会话 `717fdc90`（2026-10-28）：基线 `f271a5fa…` / 17,811 B，validator 对已换成的 `37ebf27c…` / 19,058 B 返回 `RESULT PASS`；随后文件又被第三个会话改写，4 个方案锚点消失。完整时间线见 `references/validator-negative-tests.md`。

### EOL 切换与并发写入的区分

原始 size/SHA-256 变化不一定是并发内容写入：Windows 的 `core.autocrlf=true` 会在 checkout 时把 LF 写成 CRLF，内容不变但字节数增加。满足以下三条才判为 EOL-only：

1. 两次采样（或 worktree 与 HEAD blob）做 `replace(b"\r\n", b"\n")` 后 SHA-256 相等。
2. 字节差的绝对值等于换行数 `data.count(b"\n")`，方向与 LF→CRLF（增加）或 CRLF→LF（减少）一致。
3. Git 状态：`core.autocrlf` 为 `true`，`git ls-files --eol` 显示 `i/lf w/crlf`，`git status` 与 `git diff` 无内容差异。`git reflog` 若有 checkout、merge 或 fast-forward 可作补充佐证，但 `git checkout -- <path>` 恢复单个文件不移动 HEAD，reflog 可能没有记录，不能因缺少 reflog 而否定 EOL-only。

满足时判为行尾切换，不是并发写入：不要用 `git checkout --`、`git restore` 或重写文件来回退行尾；记录原始与 LF 归一化的 size/SHA-256。若校验器窗口内发生过这次写入，仍在稳定版本上重跑；最终报告引用当前稳定文件的原始哈希，跨行尾比较用归一化哈希。

不满足时按并发内容写入处理：停止、完整重读、保留新增内容、合并后重跑，不覆盖。

边界：只对整文件统一转换成立；部分行转换或混合行尾不满足等式，不自动判为 EOL-only。非 Git 目录只能用两次采样判定，结论标为“EOL-only（推断）”，不标“已验证”。同内容重写与行尾切换无法区分，但处理相同（不覆盖）。

手动预检（可选）；把 `<skill-dir>` 替换为目标 Skill 的绝对路径后运行：

```python
from hashlib import sha256
from pathlib import Path

path = Path("<skill-dir>/SKILL.md")
data = path.read_bytes()
print(len(data), sha256(data).hexdigest())
```

同一指纹至少间隔 2 秒重复一次；两次一致再开始验收。校验期间出现写入时，即使最终内容正确，也必须以最终稳定版本重跑一遍。

## 代码块检查的边界

- 只语法检查标记为 `python`/`py` 和 `js`/`javascript` 的围栏代码块；其余语言跳过。
- `bash`/`sh`、`yaml`、`text` 等块不解析也不执行，计入 `skipped=N`；静态 PASS 不覆盖其中的路径、cwd 与占位符错误，必须按第 3 步逐条实跑。
- Python 用 `ast.parse`，不执行；JS 用 `node --check`，箭头函数按表达式包裹后检查。
- 语法检查通过不等于片段可运行，更不等于文档中的断言成立。真实产物验收必须单独做。
- 代码块含占位符时可能故意不可执行；若确属示意，改用 `text` 围栏或在正文说明，避免校验出现假阴性。

## 跨 Skill 引用

校验脚本把**正文反引号中、且与本地 skills 目录名完全一致**的 token 视为跨 Skill 引用。扫描排除 frontmatter 和围栏代码块，并跳过当前 Skill 自身。

默认解析根：

- 用户级：`~/.qoder/skills`
- 项目级：`<workspace>/.qoder/skills`

用 `--skills-root` 可覆盖默认根（可重复）；显式传入不存在的根会以 exit 2 失败。目标目录必须包含 `SKILL.md`，否则 FAIL。输出示例：

```text
PASS skill references: 2 checked (target-a, target-b)
PASS skill references: 1 resolved of 2 (target-a)
PASS skill references: 0 found (no installed skill names in backticks)
FAIL skill reference 'target-c': SKILL.md missing in C:\...\target-c
```

`local references` 只统计 Markdown 链接，以及带 scripts、references 或 assets 目录前缀、或含斜杠加已知扩展名的行内路径；反引号中的 Skill 名由 `skill references` 单独统计。`local references: 0 checked` 或 `skill references: 0 found` 都不等于“没有引用”，必须结合两项输出判断。

**外部项目路径不要写进反引号。** 该检查扫描整份 SKILL.md 的反引号 token，围栏代码块也不例外，并且不区分 Skill 内文件与所描述的外部仓库文件。把别的仓库里的相对路径写成带斜杠加已知扩展名的形式（如 `<projet>/manifeste_anteriorite.py`），若该路径既不在 Skill 目录、也不在 `--workspace` 下，就会得到：

```text
FAIL local reference not found: 'oeuvre_universelle/manifeste_anteriorite.py'
```

来源会话 `d8feaa8f`（2026-10-27）：首轮 8 pass / 1 fail，`RESULT FAIL` rc 1；去掉目录前缀、只留模块名后 9 pass / 0 fail。记录外部仓库文件时只写模块名或文件名（如 `manifeste_anteriorite.py`），完整路径写进 references/ 或报告；references 文件不参与该检查，因为校验器只扫描 SKILL.md 文本。因此本条的错误示例也不能用反引号包裹，真实 FAIL 原文放在 `text` 围栏里。

边界：该检查只验证“名称能解析到本地已安装 Skill 且目标 SKILL.md 存在”。未安装的 Skill、CLI 内置或插件 Skill、拼写错误无法与普通反引号 token 区分，不会自动报错；需要时人工核对加载器或安装位置，不得把 `0 found` 当作已验证。

## 重载后注入正文核对（仅在声称已加载时）

完成检查的最后一项要求不把文件存在当作已加载。只有报告要写“运行时已加载新版本”时才执行本节；否则在报告中标“未触发”。完整的新鲜度判定、版本定界与写入者归因交给 `verify-injected-skill-body-freshness`，路径与注入记录定位交给 `verify-skill-runtime-binding`。

1. **哨兵取自磁盘。** 用 `grep -n -F` 在 frontmatter 之后选一个本次写入才出现的标题或短语，记下行号。不要凭记忆写哨兵：来源会话 `7f2a11b0`（2026-10-27）先查记忆中的“文档命令逐条实跑”，磁盘与注入记录均 0 次；真实哨兵是标题 `### 3. 文档命令可执行性`，各 1 次。
2. **调用前后取指纹。** 记录 SKILL.md 的 size、mtime_ns、SHA-256；用只读 args 调用 Skill，末尾带唯一 `BINDING=<UTC>-<随机>` 标记，声明不执行工作流、不写文件；调用后重采，变化则判 UNVERIFIED。
3. **定位注入记录。** 在会话 JSONL 中同时用三个条件过滤：`isMeta=true`、含该 `BINDING`、含 `Base directory for this skill`；记录命中行号，不要取 `tool_use` 之后的紧邻行。同一 BINDING 会命中多条 assistant/tool_use 记录：来源会话 `5a5fca96`（2026-10-28）实测命中 5 条（L266/L268/L272/L275/L277），只有 L272 是 `isMeta=true` 注入；L268 与 L272 之间还隔着 active-leaf 与 `tool_result`，且 BINDING 加 Base directory 仍会命中 L275/L277。核对首行 `Base directory for this skill: <skill-dir>` 等于目标目录、正文含哨兵、末行仍为 `ARGUMENTS:` 尾行；缺尾行或出现截断标志时判 UNVERIFIED。注入文本 = Base directory 行 + 正文 + `ARGUMENTS:` 尾行，比较只用中间正文。
4. **双侧去空行再比较。** 注入正文与磁盘 frontmatter 之后的正文都先 `strip("\n")`：注入侧以换行开头，磁盘侧以空行开头，直接相等会误判 False，长度却可能完全相同。来源会话实测（对 `d085e59` 的 25,870 B 版本）：两侧原始均 12,203 字符，首差偏移 0，去空行后均为 12,201 字符且相等；同一注入正文与后续 26,993 B 版本比较为 False，证明结论只对比较时的版本成立。
5. **结论绑定版本。** 报告写明 Base directory、哨兵、截断迹象、调用前后 size/mtime_ns/SHA-256 与比较结果；文件随后再变，该结论只对当时的版本成立。

## Windows 环境注意事项

- `python` 和 `python3` 可能指向 Microsoft Store 别名；先运行 `--version` 验证。可用时优先 `py -3`。
- Python 控制台可能是 cp1252。校验脚本的输出保持 ASCII；动态内容用 `backslashreplace` 处理，避免校验本身因 `UnicodeEncodeError` 崩溃。
- 默认 Skill 根是 `~/.qoder/skills` 和 `<workspace>/.qoder/skills`；不要写死盘符，非标准安装用 `--skills-root`。
- 内联 Bash 脚本中的反引号会截断命令。非平凡校验一律先 Write 到临时文件，再执行并清理。
- Bash 工具的 heredoc 即使写成 `<<'PY'`，源码中的反斜杠也可能被折叠：`p.replace('\\\\','/')` 到达 Python 时只剩 `p.replace('\','/')`，报 `SyntaxError: unterminated string literal`。含反斜杠的脚本用 Write 写到临时 `.py` 再执行，或改用 `os.sep`/`PurePath` 避免字面反斜杠。
- 原生 `py -3` 读不到 MSYS 的 `/tmp`：Bash 的 `/tmp` 映射到 `%TEMP%`，Python 把 `/tmp/acl.json` 解析为不存在的 `C:\tmp\acl.json`，`open()` 报 `FileNotFoundError`。先用 `cygpath -w "$T"` 转成 Windows 路径，再作为 `sys.argv[1]` 传给 Python，或直接写到 `%TEMP%` 下的 Windows 路径。
- 夹具中的只读文件（例如 `VERROU.json`，权限 `-r--r--r--`）会被 `copytree` 或 `copy2` 原样复制。清理前必须对副本 `chmod(0o666)`，复制时用 `copy_function=shutil.copyfile`，否则 `rmtree` 报 `PermissionError [WinError 5]`。
- 临时文件只放在系统临时目录，验证完成后删除。

## 完成检查

- [ ] 读取了实际 SKILL.md 和文件清单。
- [ ] PyYAML 成功解析 frontmatter，name 与目录一致，description 单行且长度合规。
- [ ] 正文 <500 行，无 TODO，无多余 README 或 CHANGELOG。
- [ ] 本地引用和 bundled scripts 均存在。
- [ ] 正文反引号中没有外部仓库的项目相对路径（斜杠加已知扩展名会被当作本地引用）；外部文件只写模块名或文件名。
- [ ] 跨 Skill 引用已解析，目标 SKILL.md 存在；`0 found` 有明确说明。
- [ ] Python/JS 代码块已检查，或明确标注未检查原因。
- [ ] 至少一条验收断言已在真实产物上运行。
- [ ] 文档中每条安全可运行命令已按标注 cwd 实跑，记录 cwd、占位符替换、退出码与关键输出。
- [ ] 未执行的命令已标为示意并说明原因；没有把 `skipped=N` 当作已验证。
- [ ] 失败或含未说明占位符的命令已修正或降级为 `text`，复跑通过。
- [ ] 目标 Skill 若带 CLI 并声明退出码/JSON 契约，按契约覆盖成功、发现/拦截、输入/用法错误各类 rc 与 JSON 键集；仅声明契约的 CLI 没有项目夹具时仍逐个实测，结论写“已验证”或“部分适用”，只有无任何契约时才写“不适用”。
- [ ] 声明 `--json` 的 CLI 已断言完整键集合存在，且错误码字段（如 `code`）未泄漏到成功输出。
- [ ] 负向用例只改临时副本，逐例恢复；原件 SHA-256 前后一致。
- [ ] 内容夹具按字节改写；目标验证器同时校验完整性时，副本的完整性字段已重算，失败只命中目标门。
- [ ] 目标验证器的开关（如 `--strict-warnings`、`--allow-external`）两侧行为均验证，或标注未触发。
- [ ] 日期/mtime 敏感用例已固定时钟或动态推导预期。
- [ ] 临时目录已清理，报告列出负向用例和未触发分支。
- [ ] Windows 只读夹具已用 copyfile 复制并在 rmtree 前 chmod，清理无 WinError 5。
- [ ] 验收开始前已取方案或写入时的基线，并比对当前 size 与 SHA-256；不同且非 EOL 时旧 PASS 已作废，未把新版本 PASS 当作方案版本通过。
- [ ] 归因窗口已换算为 UTC（无偏移的 `--since` 按 UTC 解析），覆盖基线 mtime，`ERROR` 编辑也计入，并区分本会话与外来会话。
- [ ] 锚点消失或部分应用时已交 `adopt-source-session-update`，方案在当前版本上重算后才重跑。
- [ ] 校验前已确认 SKILL.md 稳定；报告记录起始/最终 SHA-256 与 mtime。
- [ ] 稳定性超时或校验期间内容变化时未宣称通过，已在稳定版本上重跑。
- [ ] 指纹变化时已做 EOL 判别：LF 归一化 SHA-256 一致且字节差等于换行数才判行尾切换；未回退、未覆盖；部分转换、非 Git 或同内容重写未标为已验证。
- [ ] 全部测试（真实产物、负向夹具与真实运行）结束后已做最终双采样，并与校验器 `Fingerprint (final)` 的 size 与 SHA-256 一致。
- [ ] 最终门发现并发写入时，已完整重读、保留新增内容、确认本次修改仍在并重跑校验器；报告声明旧 PASS 作废。
- [ ] 报告只引用最终稳定版本的 size 与 SHA-256；门禁之后没有未经复核的写入。
- [ ] 包内有 references 时，已重算 SKILL.md 行数、字节、SHA-256 与 description 长度，并逐条比对 references 中的记录值；失真项已回改或标注为旧快照。
- [ ] references 未包含自身最终哈希或最终行数；其最终 size 与 SHA-256 只出现在报告中。
- [ ] references 的围栏代码块成对、标题完整；复核后再改 references 时已重算其哈希。
- [ ] 修改 `scripts/validate_skill.py` 后，已覆盖 `--stable-seconds 0` 与默认等待分支（或标注未触发）。
- [ ] 若修改了 `scripts/validate_skill.py`，已用 `skill-validator-selftest` 回归；未修改时不得宣称静态校验器已验证。
- [ ] 报告区分已验证、静态检查和未触发分支。
- [ ] 报告声称运行时已加载新版本时，已做「重载后注入正文核对」，或标“未触发”。
- [ ] 哨兵取自磁盘 grep 结果（frontmatter 之后），未凭记忆；注入正文与磁盘正文双侧去空行后相等，并记录 Base directory、截断迹象与调用前后 size/mtime_ns/SHA-256。
- [ ] 未把文件存在当作 Skill 已加载；必要时提示 `/skills reload`。
