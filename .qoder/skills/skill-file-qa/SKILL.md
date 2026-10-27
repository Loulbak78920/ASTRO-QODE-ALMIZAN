---
name: skill-file-qa
description: "在创建或更新 Skill 后对 SKILL.md 做写入后验收：用 PyYAML 严格解析 frontmatter（description 或其他纯量含「冒号+空格」时必须加引号）、校验 name 与目录一致、单行 description、正文行数、文件清单、本地引用与跨 Skill 引用（反引号中的已安装 Skill 名须解析到用户级/项目级 skills 目录且目标 SKILL.md 存在），抽取 Python/JS 代码块做语法检查，校验前后等待文件稳定并复核 size/mtime/SHA-256 指纹（并发写入或等待超时则失败），并对真实产物实跑文档中的验收片段；当目标 Skill 自带 CLI 验证器时，用临时副本逐项破坏不变量，断言退出码 0/1/2、严格警告与外部资源开关，清理副本并用 SHA-256 证明原件未变。用于 Skill 创建或更新后的交付前检查、Skill 未出现在可用列表、frontmatter 解析失败、跨 Skill 引用失效、验证器负向测试未覆盖、Windows 只读夹具导致 rmtree 报 WinError 5，或需要区分已验证项与未触发分支、参考文档快照过时、references 与 SKILL.md 不一致、围栏代码块未配对时；全部测试与真实运行结束后仍须双采样 SKILL.md 并与 validator 的 Fingerprint (final) 比对，变化时旧 PASS 作废、合并重跑，只引用最终稳定版本哈希；参考文档记录了 SKILL.md 的行数、字节或哈希时，最终门要重算比对并回改失真项，复核围栏配对与标题，references 自身最终哈希只写入报告。"
---

# SKILL.md 写入后验收

## 目标

在 Skill 创建或更新后，检查磁盘上的真实文件，而不是依赖写入成功的提示。先做可复现的静态校验，再用真实产物运行文档中的验收片段；目标 Skill 带 CLI 验证器时，再做临时副本负向测试。最后区分已验证、仅静态检查、未触发分支。

## 工作流

### 1. 读取实物

读取 `<skill-dir>/SKILL.md`，并列出目录内全部文件。确认目录名、文件数量和正文，而不是凭记忆描述。

写入后不要立刻验收。若同一 Skill 可能被并发流程改写，先用校验器等待文件稳定；读取后再写文件会使前面的检查失效。报告必须记录实际读取版本的 SHA-256。

### 2. 运行结构校验

本 Skill 的校验脚本位于其安装目录的 `scripts/validate_skill.py`。从该目录执行：

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

### 3. 真实产物验收

静态检查不能证明行为正确。对文档中的每一条验收断言：

1. 找出可执行断言：行数、计数、字节、DOM 节点、返回码等，必须有明确预期值。
2. 使用真实输入（真实生成的 CSV/HTML、真实 Skill 目录），不用手写假数据替代。
3. 用 Write 把非平凡片段写入临时 `.py` 或 `.js` 文件再执行；不要把含反引号、引号的代码内联进 Bash。
4. 记录命令、真实输入、预期、实测；数字不一致时先调查，不修改预期来迁就结果。
5. 浏览器类验收按项目现有流程执行；截图不可用时只做结构校验，并明确说明。

不要自动执行与验收无关的文档片段，尤其是删除、上传、发布、安装或访问生产环境的命令。

### 4. 随附验证器负向测试

仅当目标 Skill 自带 CLI 验证器，且验证器声明了退出码/开关契约时执行；否则在报告中写“不适用/未触发”。本节针对目标 Skill 的项目验证器，不替代本 Skill 的静态校验；静态校验器自身的回归自测交给 `skill-validator-selftest`。

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

详细 harness 模板、来源会话已验证的 14 个用例、字节级夹具与完整性耦合和跨 Skill 引用自测边界见 `references/validator-negative-tests.md`。

### 5. 全部测试后的最终指纹门

校验器打印 `Fingerprint (final)` 只证明它自己的运行窗口内没有写入。第 3、4 步以及任何真实运行都发生在校验之后，期间仍可能有并发写入。全部测试结束后、写报告之前：

1. 对 SKILL.md 间隔至少 2 秒连续双采样，记录 size、mtime_ns 与 SHA-256；size 与 SHA-256 必须一致，仅 mtime 变化但字节相同不算失败。
2. 与本次校验器的 `Fingerprint (final)` 比对 size 与 SHA-256，不能只比本次双采样的两次。
3. 一致：该哈希是报告唯一可引用的版本，进入第 6 步。
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

### 6. 报告

用下表汇总，不要把“语法通过”写成“运行通过”：

| 检查 | 方式 | 真实输入 | 预期 | 实测 | 结论 |
|---|---|---|---|---|---|
| frontmatter | PyYAML | 实际 SKILL.md | 可解析且 name 一致 | 见输出 | 已验证 |
| 跨 Skill 引用 | validate_skill.py 名称解析 | 实际 SKILL.md 反引号 | 目标 SKILL.md 存在 | N checked 或 0 found | 已验证或未触发 |
| 验证器正向 | 目标 CLI | 真实产物 | 退出 0、无 FAIL | 见输出 | 已验证或未触发 |
| 验证器负向 | 临时副本 | 每例一个破坏 | 按契约 0/1/2 | 见输出 | 已验证或未触发 |
| 原件完整性 | SHA-256 | 验证器读取的项目文件 | 前后一致 | 见输出 | 已验证或未触发 |
| 稳定性 | validate_skill.py 等待窗口 | 实际 SKILL.md | 窗口内 size/mtime/SHA-256 不变 | 见 Stability 行 | 已验证或未触发 |
| 指纹复核 | SHA-256 起止比对 | 实际 SKILL.md | 起始 = 最终 | 见 Fingerprint 行 | 已验证 |
| 代码块 | ast.parse / node --check | 实际代码块 | 全部可解析 | 见输出 | 仅静态 |
| 最终指纹门 | 全部测试后双采样，对比 validator final | 实际 SKILL.md | 两次一致且等于 final | 见输出 | 已验证或未触发 |
| references 自洽性 | 重算行数/字节/哈希 + 围栏配对 | 实际 references | 记录值 = 最终值 | 见输出 | 已验证或未触发 |
| 验收断言 | 实际运行 | 真实产物 | 文档预期值 | 实测值 | 已验证或未触发 |

`Stability` 行显示等待时长；`Fingerprint (start)` 与 `Fingerprint (final)` 的 SHA-256 必须一致。只记录其中一个不算复核。这两行只覆盖校验器运行期间；第 5 步的最终指纹门才覆盖此后的夹具与真实运行，报告引用的是最终门确认的版本。

`local references: 0 checked` 只说明没有 Markdown 链接或可识别的路径引用，不代表跨 Skill 引用已检查；两项分开记录。

负向用例只写“验证器通过”不算完成；必须记录每例的退出码、关键输出和临时副本清理。`0` 退出但输出含 FAIL 视为失败。

在表后列出未触发分支，例如“Node 未安装，JS 块未检查”“错误路径未构造”“截图失败分支未复现”。没有运行过的分支不得标为已验证。

references 自身最终哈希只能出现在报告中，不能写进 references；参考文档记录 SKILL.md 的最终值可以，但必须在 SKILL.md 最后一次修改之后重算。未执行第 7 条时标“未触发”，不得写“已验证”。

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

- 默认 `--stable-seconds 2`：校验器连续观察到 size、mtime_ns、SHA-256 不变后才开始检查；`--stability-timeout 30` 控制最长等待，超时以 exit 1 结束。
- 校验结束前重新读取 SKILL.md 并打印 `Fingerprint (final)`。size 或 SHA-256 与起始值不同 → `FAIL fingerprint: SKILL.md changed during validation`，必须重跑；仅 mtime 变化但字节相同不算失败。
- `--stable-seconds 0` 只跳过等待，仍保留起止指纹比对；不要用它掩盖正在写入的文件。
- 报告必须写出实际起始/最终 SHA-256 和 mtime；无法给出时说明原因，不能宣称通过。
- 校验器不写目标 Skill 目录；如果验收期间有别的流程写入，最终指纹会暴露变化，但无法判断哪个版本是权威版本，只能等写入结束后重跑。
- 校验器内的起止指纹只覆盖它自己的运行窗口。真实产物验收、负向夹具和真实运行都在校验之后，必须在全部结束后再执行第 5 步的最终指纹门；只有与 `Fingerprint (final)` 一致的最终哈希才能写进报告。来源会话 `a48efc65`（2026-10-26）的 9,622 B 版本在 PASS 后被另一会话改写为 11,122 B，直到最终双采样才发现；完整案例见 `references/validator-negative-tests.md`。

### EOL 切换与并发写入的区分

原始 size/SHA-256 变化不一定是并发内容写入：Windows 的 `core.autocrlf=true` 会在 checkout 时把 LF 写成 CRLF，内容不变但字节数增加。满足以下三条才判为 EOL-only：

1. 两次采样（或 worktree 与 HEAD blob）做 `replace(b"\r\n", b"\n")` 后 SHA-256 相等。
2. 字节差的绝对值等于换行数 `data.count(b"\n")`，方向与 LF→CRLF（增加）或 CRLF→LF（减少）一致。
3. Git 状态：`core.autocrlf` 为 `true`，`git ls-files --eol` 显示 `i/lf w/crlf`，`git status` 与 `git diff` 无内容差异。`git reflog` 若有 checkout、merge 或 fast-forward 可作补充佐证，但 `git checkout -- <path>` 恢复单个文件不移动 HEAD，reflog 可能没有记录，不能因缺少 reflog 而否定 EOL-only。

满足时判为行尾切换，不是并发写入：不要用 `git checkout --`、`git restore` 或重写文件来回退行尾；记录原始与 LF 归一化的 size/SHA-256。若校验器窗口内发生过这次写入，仍在稳定版本上重跑；最终报告引用当前稳定文件的原始哈希，跨行尾比较用归一化哈希。

不满足时按并发内容写入处理：停止、完整重读、保留新增内容、合并后重跑，不覆盖。

边界：只对整文件统一转换成立；部分行转换或混合行尾不满足等式，不自动判为 EOL-only。非 Git 目录只能用两次采样判定，结论标为“EOL-only（推断）”，不标“已验证”。同内容重写与行尾切换无法区分，但处理相同（不覆盖）。

手动预检（可选）：

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

边界：该检查只验证“名称能解析到本地已安装 Skill 且目标 SKILL.md 存在”。未安装的 Skill、CLI 内置或插件 Skill、拼写错误无法与普通反引号 token 区分，不会自动报错；需要时人工核对加载器或安装位置，不得把 `0 found` 当作已验证。

## Windows 环境注意事项

- `python` 和 `python3` 可能指向 Microsoft Store 别名；先运行 `--version` 验证。可用时优先 `py -3`。
- Python 控制台可能是 cp1252。校验脚本的输出保持 ASCII；动态内容用 `backslashreplace` 处理，避免校验本身因 `UnicodeEncodeError` 崩溃。
- 默认 Skill 根是 `~/.qoder/skills` 和 `<workspace>/.qoder/skills`；不要写死盘符，非标准安装用 `--skills-root`。
- 内联 Bash 脚本中的反引号会截断命令。非平凡校验一律先 Write 到临时文件，再执行并清理。
- 夹具中的只读文件（例如 `VERROU.json`，权限 `-r--r--r--`）会被 `copytree` 或 `copy2` 原样复制。清理前必须对副本 `chmod(0o666)`，复制时用 `copy_function=shutil.copyfile`，否则 `rmtree` 报 `PermissionError [WinError 5]`。
- 临时文件只放在系统临时目录，验证完成后删除。

## 完成检查

- [ ] 读取了实际 SKILL.md 和文件清单。
- [ ] PyYAML 成功解析 frontmatter，name 与目录一致，description 单行且长度合规。
- [ ] 正文 <500 行，无 TODO，无多余 README 或 CHANGELOG。
- [ ] 本地引用和 bundled scripts 均存在。
- [ ] 跨 Skill 引用已解析，目标 SKILL.md 存在；`0 found` 有明确说明。
- [ ] Python/JS 代码块已检查，或明确标注未检查原因。
- [ ] 至少一条验收断言已在真实产物上运行。
- [ ] 目标 Skill 若带 CLI 验证器，至少覆盖成功、校验失败、输入/用法错误三类退出码；不适用时说明原因。
- [ ] 负向用例只改临时副本，逐例恢复；原件 SHA-256 前后一致。
- [ ] 内容夹具按字节改写；目标验证器同时校验完整性时，副本的完整性字段已重算，失败只命中目标门。
- [ ] 目标验证器的开关（如 `--strict-warnings`、`--allow-external`）两侧行为均验证，或标注未触发。
- [ ] 日期/mtime 敏感用例已固定时钟或动态推导预期。
- [ ] 临时目录已清理，报告列出负向用例和未触发分支。
- [ ] Windows 只读夹具已用 copyfile 复制并在 rmtree 前 chmod，清理无 WinError 5。
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
- [ ] 未把文件存在当作 Skill 已加载；必要时提示 `/skills reload`。
