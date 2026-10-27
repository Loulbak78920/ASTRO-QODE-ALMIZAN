# 工具契约审计参考

本文件是 `audit-skill-tool-contracts` 的详细契约、负向测试协议、决策表、真实案例与报告模板。SKILL.md 只保留执行主线；需要判断分支、设计负向测试或写报告时读本文件。

## 契约维度

| 维度 | 检查方式 | 失败含义 |
|---|---|---|
| 存在性 | 解析 `SKILL.md` 反引号或 Markdown 链接中以 `scripts/`、`references/`、`assets/` 开头且带文件名的路径，逐个查磁盘 | 文档承诺的文件不存在，或并发创建尚未完成 |
| 入口 | 记录解释器、工作目录与调用形式（`py -3`、`python`、`node`） | 文档命令在当前环境无法启动 |
| 参数元数 | 运行 `--help`，解析 `usage:` 中的必需/可选位置参数 | 传入的参数个数与工具接受的不一致 |
| 输入形态 | 与预期断言比较：`dir`/`file`、`two-files` 及可选性变体 | 单文件双语、独立译本双文件、目录扫描被混用 |
| 退出码 | 直接运行并读取 `$?`，不经管道 | 管道返回的是 `head`/`grep` 的状态，掩盖失败 |
| 输出编码 | 固定 `PYTHONIOENCODING=utf-8`；脚本输出应为 ASCII 或可转义 | Windows 控制台 cp1252 下打印中文崩溃 |
| 只读性 | 默认只跑 `--help`；不执行脚本的无参数分支 | 探测动作本身写入或改写了文件 |
| 文档一致性 | 对比 SKILL.md 的命令行、参数名、退出码与实际 `--help` | 文档与实物漂移，按文档调用即失败 |
| 检测能力 | 在副本上做一个真实变异，断言变异生效，再运行校验器读取退出码 | 正例 PASS 只证明当前输入通过，不证明工具能发现漂移 |

## 审计命令

```bash
py -3 scripts/audit_contracts.py audit <skill-dir|skill-name> \
  [--skills-root DIR]... [--help-probe] [--expect REL=SHAPE] [--timeout 10]
py -3 scripts/audit_contracts.py compare <source.md> <translation.md> [--max-report 10]
py -3 scripts/audit_contracts.py mutate --copy <file> --replace <old> --with <new> \
  [--occurrence N] [--expect-exit 1] [--workdir DIR] [--keep] [--timeout 60] \
  -- <validator> [args...]
py -3 scripts/audit_contracts.py mutate <source.md> --out <copy.md> --kind <kind> \
  --validator '<command with {target}>' [--expect-exit 1] [--timeout 60]
```

- `audit` 默认只读：列出声明资源、存在性、大小与 SHA-256；目标可以是目录或已安装 Skill 名，`--skills-root` 扩展名称搜索根。`--expect` 必须与 `--help-probe` 同用，否则退出码 `2`。它不自动跟进被引用 Skill；需要对每个被引用 Skill 单独 `audit`。声明的路径必须是具名文件；具名路径是目录会判 FAIL，裸目录不进入清单。
- `--help-probe` 会对每个存在的 `.py` 声明运行一次 `--help`。这会执行脚本顶层代码，只对本地可信 Skill 使用。
- `--expect REL=SHAPE` 断言声明脚本的位置参数形态：`two-files` 要求两个必需文件参数；`dir`/`file` 是 `total=1` 别名（恰好一个位置参数），并校验 `--help` 的目录/文件描述；`optional-dir`/`required-dir`/`one-file` 精确区分可选性；`required=N,optional=M` 只断言分项元数，`total=N` 只断言位置参数总数。
- 可变参数写法（`paths [paths ...]`）与子命令表（`{audit,compare}`）无法推导元数，结果为 UNVERIFIED（退出码 `3`），不是通过。
- `compare` 是回退工具：6 项结构对比，不判断译文语义。
- `mutate` 替换模式：把 `--copy` 复制到临时目录，精确替换一处，断言副本 SHA-256 改变，再运行校验器；命令中的 `{mutated}` 替换为副本路径，未提供时自动追加。默认期望校验器退出 `1`，可用 `--expect-exit` 覆盖。
- `mutate` 确定性模式：`--kind`（`heading`/`table`/`code`/`language`/`checklist`/`inline`/`number`）生成结构变异，断言对应维度确实改变，再运行 `--validator`；`{target}` 替换为副本路径，校验器以 `--out` 所在目录为工作目录。`--validator` 经 `shlex.split(posix=True)` 拆分，Windows 路径请用正斜杠，避免反斜杠被当作转义。
- `mutate` 两种模式都不写原文件，并在变异前后核对原文件哈希。替换模式复制到 `--workdir`（默认 `.qoder/tmp/negative`，相对当前目录），默认清理副本，`--keep` 保留并打印路径；确定性模式写入 `--out`，不自动清理，由调用者负责清理。
- 输出为 ASCII（非 ASCII 以 `\xNN` 或 `\uNNNN` 转义），最后一行固定 `RESULT PASS|FAIL|UNVERIFIED|ERROR`（`ERROR` 对应退出码 `2`）。
- 退出码：`audit`/`compare` 为 `0` 通过、`1` 发现缺口或对等失败、`2` 用法或环境错误、`3` 仅有未验证项；`mutate` 为 `0` 变异生效且校验器返回预期非零、`1` 变异生效但校验器返回 0 或其他码、变异未生效或源文件在运行中被改、`2` 用法/环境/目标未命中/超时。
- 推断参数时不要用 `cmd | head; echo $?` 读退出码；直接运行后再读 `$?`。

## 检测能力负向测试

正例 `RESULT PASS` 只证明当前输入通过，不证明工具能发现漂移。报告某校验器「可用」前，至少做一次真实变异。

| 步骤 | 要求 |
|---|---|
| 1. 副本 | 在 `.qoder/tmp/<session>/negative/` 复制输入；原文件不改 |
| 2. 变异点 | 选结构性、可精确定位的项：围栏语言、代码块文本、反引号标识符、数字、表格列数、标题层级 |
| 3. 断言生效 | 记录变异前后 SHA-256，或断言精确出现次数；未改变就停止，不得把 PASS 当结论 |
| 4. 退出码 | 直接运行校验器；期望失败分支返回 `1`（或工具声明的失败码），且输出有可辨识的失败项 |
| 5. 仍 PASS | 判定该工具不覆盖此类漂移；换工具、回退或标注覆盖边界 |
| 6. 清理 | 删除副本；需要复查时保留并写明路径 |

```bash
py -3 scripts/audit_contracts.py mutate \
  --copy "<translation.md>" \
  --replace "<old>" --with "<new>" --occurrence 1 \
  --workdir ".qoder/tmp/<session>/negative" --keep \
  -- py -3 "<validator.py>" "<source.md>" "{mutated}"
```

`mutate` 先复制再精确替换；`{mutated}` 由副本路径替换。它断言副本哈希改变，并检查原文件哈希未变。退出码 `0` 表示变异生效且校验器返回预期非零；`1` 表示变异生效但校验器返回其他码，或变异未生效、源文件被改动；`2` 表示用法、环境、目标未命中或超时。

确定性模式示例：`mutate <source.md> --out <copy.md> --kind table --validator 'py -3 <validator.py> "<source.md>" {target}'`。`--kind` 会同时断言对应结构维度确实改变，避免忘记检查变异是否命中。

变异点优先级：代码块语言或内容最容易稳定命中；数字与反引号标识符次之；标题与表格适合检测结构漂移。不要只用散文，因为结构检查器不会检查散文语义。

## 决策表

| 情形 | 判据 | 动作 | 报告里必须写 |
|---|---|---|---|
| 声明脚本缺失 | 路径存在性为假 | 不调用该工具；找替代或回退；不改他人 Skill | 缺失路径、声明出处、替代方案 |
| `scripts/` 为空且 Skill 刚出现 | 目录为空、mtime 很近、SKILL.md 已声明脚本 | 视为并发创建中；本次不依赖；稍后重试可选 | 「未验证，疑似并发创建」 |
| 参数元数不符 | `usage` 的必需参数个数与预期不同 | 不按预期调用；换工具或回退 | 实际 `usage`、预期元数、退出码 |
| 输入形态不符 | 需要两个文件，工具只接受目录/单文件 | 换匹配的工具；无匹配则回退 | 「形态不符：单文件双语 vs 双文件译本」 |
| `--help` 无 `usage` | 输出中没有 `usage:` | 标记 UNVERIFIED（退出码 `3`）；手工读脚本；不得断言元数 | 「未验证元数」 |
| 探测超时或崩溃 | 超时、非零且无帮助文本 | 记录退出码；不重试成环 | 命令、超时值、原始错误 |
| 仅 Skill 名能解析 | `skill-file-qa` 只确认 `SKILL.md` 存在 | 用本 Skill 的 `audit` 直接审计该 Skill | 「名字已解析，但工具契约另行审计」 |
| 文档与实物矛盾 | 文档命令与 `--help` 不一致 | 以实物为准；报告漂移 | 文档原文、实际 `usage` |
| 声明的是裸目录 | 路径以 `scripts/`、`references/`、`assets/` 结尾且无文件名 | 不进入文件清单；检查其中具名文件是否另行声明 | 目录路径、未被校验的说明 |
| 负向测试仍 PASS | 副本确实改变但校验器退出 0 | 判定不覆盖该类漂移；换工具、回退或标注覆盖边界 | 变异点、前后哈希、退出码、未覆盖项 |
| 变异未生效 | 哈希或精确计数未变 | 停止；修正变异点；不得把 PASS 当结论 | 变异命令、目标出现次数 |

## 已知案例（2026-10-26）

来源会话 `d77e784b`（`commit-skill-work` 的创建过程）出现了两次契约与预期不符。

| 事件 | 证据 |
|---|---|
| 方案承诺用 `bilingual-skill-parity` 校验 `SKILL.md` + `references/skill-zh.md` | 会话内语言选项描述与计划原文都写「用 bilingual-skill-parity 校验结构对等」 |
| 该工具只能校验单文件双语 | `--help` 只有 `[skill_dir]`；`bilingual-skill-parity/SKILL.md` 第 34 行要求在同一个文件内用 `## Version chinoise complète / 完整中文版` 分隔两种语言 |
| 改用 `skill-doc-translation-parity` 时脚本目录为空 | 同会话目录输出：`scripts/` 无文件，`references/` 仅有 `translation-contract.md`，而 `SKILL.md` 已声明 `scripts/check_translation_parity.py` |
| 代理明确改道且未改他人 Skill | 原文：「对等脚本目录为空（该 Skill 似在并发创建中），我不改动它，改用只读结构对比脚本核验。」 |
| 回退脚本完成 6 项对比 | 临时文件在 `.qoder/tmp/<session>/check_parity.py`；输出标题 16、表格 2、代码块 12、清单 8、内联标识符 33、数字 11，`RESULT PASS`，退出 0 |
| 写入后验收未暴露缺口 | `skill-file-qa` 为 9 pass / 0 fail；跨 Skill 引用检查只判断目标 `SKILL.md` 是否存在（`validate_skill.py:300-308`） |
| 当前复核（2026-10-26） | `bilingual-skill-parity` 仍只接受单目录，无参数退出 2；`skill-doc-translation-parity` 的脚本已存在，接受 `source translation`，缺文件退出 2、内容不等退出 1 |

本次对同一事实做了可复现断言：

```bash
py -3 scripts/audit_contracts.py audit "<skills>/bilingual-skill-parity" \
  --help-probe --expect scripts/check_bilingual_parity.py=two-files
# OBSERVED ...: required=0 optional=1 kinds=[dir]
# FAIL expect arity ...: expected 2 required/0 optional, observed 0 required/1 optional
# RESULT FAIL, exit 1

py -3 scripts/audit_contracts.py audit "<skills>/skill-doc-translation-parity" \
  --help-probe --expect scripts/check_translation_parity.py=two-files
# OBSERVED ...: required=2 optional=0 kinds=[file, file]
# RESULT PASS, exit 0
```

同一会话还有两个 Windows 陷阱：

- `cmd | head; echo $?` 得到 `head` 的退出码。先前的探测因此打印了假的 `exit=0`；直接运行时两个脚本无参数均为 `2`。
- 控制台非 UTF-8 时打印中文会 `UnicodeEncodeError`。审计器固定输出 ASCII，并在探测子进程设置 `PYTHONIOENCODING=utf-8`。

### 检测能力负向测试案例（`7d622d2c`，2026-10-26）

来源会话第 7 轮审计 `skill-doc-translation-parity/scripts/check_translation_parity.py`（15665 bytes，SHA-256 `1d8a1e4e…`），输入为 `commit-skill-work/SKILL.md`（`156a9b74…`）与 `references/skill-zh.md`（`f9d726be…`）。

| 步骤 | 结果 |
|---|---|
| 正例基线 | `8 pass, 0 fail`、`RESULT PASS`、退出 0 |
| 变异 A：围栏语言 `bash` → `sh` | `FAIL code block: block 1 language 'bash' != 'sh'`、`7 pass, 1 fail`、退出 1 |
| 首次数字变异（`mut-b`） | 仍 `RESULT PASS`、退出 0；同轮随后匹配输出为 0 / `No matches found`，与目标标记未命中、副本未改变一致 |
| 修正变异：`` `9901 bytes` `` → `` `9902 bytes` `` | `FAIL inline tokens: missing=['9901 bytes'] extra=['9902 bytes']`、退出 1 |
| 译本末尾追加 `DRIFT_MARKER` | 仍 `RESULT PASS`、退出 0 |

结论：该检查器覆盖代码块、表格、标题、清单、反引号标识符、数字等结构项；不覆盖散文语义。正例 PASS + 一个真实结构变异失败，才是「当前输入通过且工具具备该类检测能力」的最小证据。首次数字变异是典型的假 PASS：变异没有命中目标，副本没有改变，校验器当然通过。

## 只读回退协议

1. 确认原声明工具不可用：缺失、形态不符或参数不符，并有命令与退出码为证。
2. 不修改被审计 Skill，也不把回退脚本写进对方目录；临时脚本放 `.qoder/tmp/<session>/`。
3. 用 `compare` 做 6 项结构对比：标题层级序列、表格行列、代码块（语言与内容逐字）、清单项数、内联标识符多重集、数字多重集。
4. 报告里把结果标为「回退验证」，并写「不是原声明工具的检查」。
5. 列出未覆盖项：语义质量（含在译本末尾追加纯文本段落）、纯文本项目符号、未加反引号的声明、HTML 结构、链接可达性。
6. 不得写成「已用 `bilingual-skill-parity` / `skill-doc-translation-parity` 验证通过」。

`compare` 的规范化规则：代码块的语言与内容逐字比较（`splitlines` 抹平换行风格，但保留行尾空白）；标题只比较层级序列；表格比较行数与每行列数；清单比较勾选状态多重集；内联标识符与数字按多重集比较，64 位十六进制整体记作 `sha256:` 标记；先屏蔽围栏代码块再统计标题、表格与清单。

## 报告模板

```text
契约审计: <skill-name> | <skill-dir>
声明工具: <相对路径> | SKILL.md sha256=<hash>
实际契约: usage="<usage>" | 必需=[...] 可选=[...] | 退出码=<n>
断言: 预期 <SHAPE> | 实际 required=<n> optional=<n> kinds=[...] | PASS|FAIL|UNVERIFIED
缺口: <缺失 / 形态不符 / 参数不符 / 无 usage / 并发创建中>
负向测试: <变异点> | 变异生效=<yes/no> | 工具退出码=<n> | 期望=<n> | 失败项=<...>
覆盖边界: <结构项 / 未覆盖的散文语义>
回退: <compare 的 6 项结果；明确写「回退，不是原声明工具」>
未验证: <语义质量 / 未声明资源 / 未执行分支>
级别: 已验证 | 回退验证 | 未验证 | 阻塞
```

## 边界与局限

- 只识别反引号与 Markdown 链接中以 `scripts/`、`references/`、`assets/` 开头且带文件名的声明；裸目录与正文里裸写的路径不检查。
- `--help` 会执行脚本顶层代码；不用于不可信来源，也不自动执行无参数分支。
- 只探测 Python 脚本；Node、Bash 需要人工核对 `--help` 或源码。
- `audit` 不递归、不执行被引用 Skill 的脚本；需要对每个被引用 Skill 逐个单独审计。
- 不判断译文语义质量；那是人工通读的职责。
- 结构对等 PASS 不代表译文语义正确；在译本末尾追加纯文本行不会被 `compare` 或 `check_translation_parity.py` 发现（2026-10-26 实测）。
- 本 Skill 只做一次负向能力探针；系统性反例回归用 `skill-validator-selftest`。
- `mutate` 会运行调用者给出的本地校验器命令；不要对不可信命令使用，也不要把副本路径写成原文件路径。
- 不替代 `skill-file-qa` 的写入后验收，也不替代 `audit-session-evidence` 的来源会话核实。
- 结构对等的权威工具是 `skill-doc-translation-parity`；`compare` 只在对方不可用时作回退。
