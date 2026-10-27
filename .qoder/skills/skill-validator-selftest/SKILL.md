---
name: skill-validator-selftest
description: "对 Skill 静态校验器做回归自测：先跑正例，再为每项检查构造独立反例（未加引号的 YAML 冒号、name 与目录不一致、Python/JS 语法错误、缺失引用、多余 README、真实 TODO 标记、多行 description、BOM、非法 UTF-8、退出码 2），并显式验证文档自指误报（正文提到 TODO、<占位符> 被当作路径）和 PyYAML/Node 缺失降级，断言退出码、RESULT 行与关键输出，运行前后核对校验器与真实正例的 sha256/mtime，确认反空转 stub 已清理并清理临时目录。用于新建或修改 Skill 校验脚本后的自测、校验器漏报/误报排查，以及证明每条检查确实会失败；不用于验收单个 Skill 包本身。"
---

# Skill 校验器自测

## 目标与边界

验证技能校验器本身：正例必须通过，每个独立反例必须由对应检查拒绝，文档自指不得误报，依赖缺失必须清晰降级，退出码契约必须成立。

本 Skill 不验收单个 Skill 包；那一步使用 `skill-file-qa`。它也不执行 Skill 中的代码，只运行被测校验器。校验器通常是同级的 `skill-file-qa` 技能中的校验脚本，通过 `--validator` 指向实际路径，不要复制副本。本 Skill 的 harness 位于 `scripts/selftest_validator.py`。

## 工作流

1. 确认本 Skill 的 harness `scripts/selftest_validator.py` 存在并记录其 sha256；缺失时停止，不使用替代脚本。准备一个已知可通过的 Skill 包作为真实正例，并确认被测校验器的命令行契约：位置参数为 Skill 目录，支持 `--workspace`，退出码 0/1/2。
2. 运行前记录 `--validator` 与每个 `--positive-skill` 中 SKILL.md（以及被测校验器会读取的脚本）的绝对路径、size、mtime、sha256。
3. 从本 Skill 目录运行：

```bash
py -3 scripts/selftest_validator.py \
  --validator <path-to-validate_skill.py> \
  --positive-skill <known-good-skill-dir> \
  --workspace <skills-root>
```

4. 先检查基线 `pos-good`。基线失败时不要继续相信反例结果：PyYAML 缺失属于环境错误（harness 退出 2），其他基线失败属于断言失败（退出 1）。
5. `--positive-skill` 可重复，至少传入被测校验器自身所属的 Skill 包；再传入本次正在交付的 Skill 包。真实包失败说明校验器或包有回归，不能忽略。
6. 逐个查看反例：`PASS` 表示校验器按预期拒绝了缺陷；`FAIL` 表示断言不成立；`SKIP` 表示该分支未执行，**不得**写成已验证。
7. 全部通过后执行“反空转检查”并删除 stub；重算步骤 2 的指纹并逐项比对，任何变化都必须调查。最后按“报告”一节汇总；临时目录默认自动删除，排错时才用 `--keep` 保留。

## 用例覆盖

| 类别 | 代表性用例 | 期望 |
|---|---|---|
| 正例 | 合法 frontmatter、真实引用、Python/JS 代码块 | exit 0，RESULT PASS，0 个 FAIL |
| frontmatter | 未加引号的 `: `、缺 frontmatter、根节点为列表 | exit 1，解析或结构错误 |
| 名称 | name 与目录不一致、非法字符 | exit 1 |
| description | 折叠成多行、1025 字符；1024 字符边界 | 反例 exit 1；边界 exit 0 |
| 正文 | 500 行；499 行边界 | 反例 exit 1；边界 exit 0 |
| 引用与布局 | 缺失脚本引用、多余 README、意外文件 | 前两者 exit 1；意外文件 WARN 且 exit 0 |
| 内容 | 行首真实待办标记；正文只提到该词 | 前者 exit 1；后者 exit 0 |
| 代码块 | Python/JS 语法错误、未闭合围栏 | exit 1；Node 缺失时 JS 反例 SKIP |
| 编码 | BOM、非法 UTF-8 | exit 1 |
| 自指 | `<skill-dir>` 等占位符、正文提到 TODO 一词 | exit 0，不误报 |
| 降级 | `-S` 下 PyYAML 缺失；空 PATH 下 Node 缺失 | PyYAML exit 1 且无 traceback；Node WARN 且 exit 0 |
| 用法 | 缺 SKILL.md、缺 Skill 目录、缺 workspace | exit 2；详情中的 `fails=1` 属预期 |

## 断言纪律

- 不只断言退出码：同时检查 `RESULT PASS`/`RESULT FAIL`、关键输出片段，以及独立反例的 FAIL 行数。只返回 1 的校验器可能因为错误原因失败。
- 每个独立反例只制造一个缺陷，并期望恰好 1 个 FAIL。级联用例（例如缺 frontmatter）会有多个 FAIL，应分别断言，而不是放宽为“有 FAIL 就行”。
- 用法错误用例由校验器先打印 FAIL 再返回 2，因此 harness 详情会出现 `exit=2 fails=1` 且仍判 PASS；判定只看 exit 2、对应用法片段和无 Traceback，不要为这些用例设置 `fail_count=0`。
- 输出中不得出现 `Traceback`；依赖缺失必须是清晰的 FAIL/WARN。
- 不要通过删除用例、放宽片段或修改预期来迁就回归。校验器文案若有意的变更，集中更新 harness 顶部的期望值，并保留“检查仍会失败”的语义。
- 断言前先看真实输出；数字或文案不一致时先调查原因，再决定是修校验器还是修 fixture。

## 自指与降级

- 自指误报：文档正文提到 TODO 一词、或使用 `<skill-dir>` 这类占位符时，不得被当成未解决标记或真实路径。两个 fixture 必须 exit 0。
- PyYAML 缺失：用 `-S` 运行同一正例，期望 exit 1、输出包含 PyYAML 缺失信息、没有 traceback。若 `-S` 下仍能导入 YAML（例如 vendored），harness 标 SKIP，不得宣称已验证。
- Node 缺失：把 PATH 指向空临时目录后运行正例，期望 JS 块 WARN、exit 0。若校验器仍找到 Node，按失败或 SKIP 处理并说明，不能把 WARN 分支当成已覆盖。
- JS 语法反例依赖 Node；Node 不存在时该反例 SKIP，报告中必须单列。

## 反空转检查

如果所有反例都显示 PASS，仍需确认 harness 本身不是空转：

1. 在系统临时目录创建只打印 `RESULT PASS` 并返回 0 的 stub 校验器。
2. 用同一 harness 以 `--validator <stub>` 运行（无需真实正例），期望 `BASELINE FAIL`、`SELFTEST FAIL`、exit 1。
3. 记录 `STUB_HARNESS_EXIT=1`；随后删除 stub 并确认文件不存在。报告中写明 stub 路径、退出码和清理结果；不得把 stub 留在项目或 Skills 目录。
4. 若得到 `SELFTEST PASS`，说明基线断言或 fixture 失效，先修 harness，再修被测校验器。

## Windows 注意事项

- 使用 `py -3`；`python`/`python3` 可能是 Microsoft Store 别名。先运行 `--version` 确认。
- harness 输出保持 ASCII，避免 cp1252 控制台崩溃；路径通过 `backslashreplace` 处理。
- 非平凡命令写成脚本再执行，不要把含反引号或引号的代码内联进 Bash。
- 临时 fixture 只放在系统临时目录；默认删除，`--keep` 仅用于排错，报告中要说明保留了哪些文件。
- harness 只读被测校验器和 Skill 包，不修改它们；如果发现校验器写文件，按缺陷处理。

## 报告

| 项目 | 内容 |
|---|---|
| Harness | 绝对路径、size/mtime、sha256（运行前后一致） |
| 被测校验器 | 绝对路径、size/mtime、sha256（运行前后一致） |
| 完整性 | 被测校验器与每个真实正例的 SKILL.md（及被读取脚本）运行前/后 sha256、mtime；不一致已调查 |
| 基线 | exit code、RESULT、FAIL/WARN 计数 |
| 反例 | 逐个列出 PASS/FAIL，失败时给预期与实际 |
| 真实正例 | 各包的 exit code 与 FAIL/WARN 计数，指纹是否一致 |
| 降级 | PyYAML/Node 分支是已验证还是 SKIP |
| 反空转 | stub 路径、harness exit、`SELFTEST FAIL` 是否出现、stub 是否已删除 |
| 清理 | 临时目录已删除，或因 `--keep` 明确保留 |

未执行的 SKIP 分支、未安装的 Node、未复现的 PyYAML 缺失都必须列出；不要把“用例通过”写成“所有分支已验证”。

## 完成检查

- [ ] 已确认 `scripts/selftest_validator.py` 存在并记录其 sha256。
- [ ] `pos-good` 基线通过，0 个 FAIL。
- [ ] 每个独立反例按预期 exit 1，且 FAIL 行数符合预期。
- [ ] 两个自指用例 exit 0，无 TODO/占位符误报。
- [ ] PyYAML 缺失分支 exit 1 且无 traceback；Node 缺失分支 WARN 且 exit 0，或明确 SKIP。
- [ ] 三个用法错误用例 exit 2；`fails=1` 属预期，未按失败处理。
- [ ] 至少一个真实正例通过；失败已调查。
- [ ] 运行前后被测校验器与真实正例的 sha256/mtime 一致；不一致已调查。
- [ ] 反空转 stub 得到 `SELFTEST FAIL`/exit 1，随后删除并确认不存在。
- [ ] 临时目录已清理，或已说明 `--keep`。
- [ ] 报告区分已验证、SKIP 和未覆盖分支；被测文件指纹前后一致，未发现修改。
