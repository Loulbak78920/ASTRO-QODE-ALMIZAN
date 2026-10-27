---
name: develop-skill-static-checker
description: 开发、修正并回归测试 Skill 自带的只读 Python 静态检查器，用 AST 判定输出编码、JSON ensure_ascii 归宿、语法、缓存与 CLI 契约，建立 12 项单变量夹具、变异体和真实 Skill 矩阵，验证 0/1/2 退出码与无副作用；用于新建检查器、排查漏报误报、矩阵自测、变异测试、pycache 清理和 Windows UTF-8 输出验收。English triggers develop skill static checker, fixture matrix, mutant test, read-only Python checker, AST output sink, cache cleanup.
---

# 开发 Skill 静态检查器

本 Skill 提供一套可复用的验收骨架 [scripts/checker_matrix.py](scripts/checker_matrix.py)，用于开发或修正 Skill 自带的只读 Python 静态检查器。骨架不替代检查器本身：它只负责用夹具、变异体和真实 Skill 证明检查器的行为符合契约。

## 适用场景

- 为一个 Skill 新增只读 Python 静态检查器，需要定义输出编码、缓存、语法与用法检查。
- 检查器已存在但出现漏报、误报、崩溃或退出码不稳定。
- 需要证明夹具矩阵不是空转（stub 检查器会被抓到）。
- 需要在一组真实 Skill 上运行检查器，并人工复核 WARN。
- 需要验证检查过程不修改目标文件、不留下 `__pycache__`。

## 不适用边界

- 只验收 Skill 包的 frontmatter、引用、文件清单与指纹时，使用已安装的 skill-file-qa 流程，不用本骨架。
- 只逐字重放别人已记录的夹具时，使用 replay-skill-reference-fixtures 流程。
- 只审计依赖脚本的 CLI 契约或哈希变化时，使用 audit-skill-tool-contracts 或 dependency-script-contract-reaudit 流程。
- 修改 Windows 控制台 UTF-8 输出契约与随包脚本交付时，参考 windows-python-utf8-skill-scripts 的规则。

## 核心契约

检查器与矩阵都必须满足以下约定：

| 项目 | 契约 |
| --- | --- |
| 目标目录 | 只读；不得修改 `scripts/` 下的任何文件 |
| 标准输出 | UTF-8；`--json` 时必须是纯 ASCII 且可被 `json.loads` 解析 |
| 退出码 0 | 没有 FAIL；WARN 不改变退出码 |
| 退出码 1 | 至少一条 FAIL；无 traceback |
| 退出码 2 | 用法错误或环境错误，例如目录不存在、参数缺失 |
| 摘要粒度 | `SUMMARY scripts=N pass=N fail=N warn=N` 按文件计数，不按发现行计数 |
| 缓存 | 检查过程不得新增 `__pycache__` 或 `.pyc`；已存在的缓存以 WARN 报告 |

`warn` 的计数规则：每个含 WARN 的文件计 1 次；`cache-present` 额外计 1 次。因此 3 个脚本各 1 条 WARN 时是 `warn=3`，同一文件 3 条 WARN 仍只计 1 次再加缓存条目。

## 工作流

### 1. 读取现状并划定边界

1. 先读取目标 Skill 的 SKILL.md、现有脚本和 references，确认是否已有检查器。
2. 列出检查器需要回答的问题：哪些写法必须 FAIL，哪些只能 WARN，哪些是合法写法。
3. 明确检查器只做静态分析，不执行目标脚本，不导入目标模块。

### 2. 实现检查器

1. 用 `ast.parse` 读取源码，避免 `py_compile` 或 `compileall` 生成缓存。
2. 用 `path.read_text(encoding="utf-8")` 读取，捕获 `UnicodeDecodeError` 并转成 `FAIL invalid-utf8`。
3. 语法错误转成 `FAIL syntax-error`，不要抛出 traceback。
4. 每个文件只输出一条结果摘要，所有发现行按文件聚合后再计数。
5. 入口调用 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`；JSON 模式使用 `ensure_ascii=True`。
6. 参数解析失败或目录缺失时返回 2，并输出 `ERROR: ...`（错误行带 ASCII 冒号）。

### 3. AST 规则

不要只看 `ast.Name` 节点，也不要只检查字符串常量：

1. 识别调用名时先解包 `ast.Call`：`call_name(node)` 遇到 `ast.Call` 要取 `node.func`，否则 `print(...)` 会得到空串。
2. 识别方法名时单独处理 `ast.Attribute`：`method_name(child) == "encode"`，避免链式 `str(value).encode("ascii", "backslashreplace")` 因 `call_name` 返回空串而漏判。
3. 判断输出归宿时看输出祖先，而不是值节点：`output_ancestor(node)` 向上找最近的 `print`、`sys.stdout.write` 或 `sys.stdout` 调用。
4. 区分 stdout 与非 stdout sink：变量中转、文件写入、helper 返回值都不等于直接输出到 stdout。
5. `json.dumps(..., ensure_ascii=False)` 直接进入 stdout 时 FAIL；经变量中转或写入文件时 WARN。
6. `py_compile.compile`、`compileall` 出现时报告 `WARN cache-risk`，不要执行它们。
7. 已存在的 `__pycache__` 与 `.pyc` 报告 `WARN cache-present`，不要删除它们。

### 4. 建立夹具矩阵

矩阵默认包含 12 个单变量用例，覆盖正例、反例、边界、环境错误与 JSON 契约：

| 用例 | 预期 rc | 关键断言 |
| --- | --- | --- |
| `pass_only` | 0 | 3 个合法脚本全部 PASS，无 FAIL |
| `all` | 1 | 8 个脚本，3 FAIL、3 PASS、2 WARN |
| `warn_only` | 0 | 仅 WARN 时仍 PASS |
| `edge_bad` | 1 | f-string、`sys.stdout.write`、`print(..., end=...)` 共 3 条 FAIL |
| `edge_good` | 0 | UTF-8 重配置、链式 encode helper、文件 sink 均不误报 |
| `cache` | 0 | 已有 `.pyc` 时 `WARN cache-present` 且 `warn=1` |
| `empty` | 0 | `scripts` 为空时 `scripts=0` |
| `no_scripts` | 2 | `ERROR: scripts directory not found` |
| `missing` | 2 | `ERROR: skill directory not found` |
| `bad_encoding` | 1 | 非法 UTF-8 与 `FAIL invalid-utf8` |
| `json_contract` | 1 | 纯 ASCII JSON，summary 为 8/3/3/2，caches 为空 |
| `help` | 0 | `--help` 输出 `usage:`，不构建夹具 |

运行矩阵：

```bash
cd C:/Users/Administrateur/.qoder/skills/develop-skill-static-checker
PYTHONIOENCODING=utf-8 py -3 scripts/checker_matrix.py \
  --checker C:/Users/Administrateur/.qoder/skills/windows-python-utf8-skill-scripts/scripts/check_script_hygiene.py
```

选中某个用例排查时，复制该用例的源码到临时目录，只改一个变量，然后单独运行检查器。一次只验证一个假设，避免多个改动互相掩盖。

### 5. 变异测试与自测

矩阵必须证明不是空转。在系统临时目录复制检查器后准备两个变异体，分别破坏一项关键识别（绝不修改真实 Skill 的脚本）：

1. 移除 `call_name` 中的 `ast.Call` 解包，矩阵应出现 5 个用例失败。
2. 恢复链式 `.encode` 的旧判断，矩阵应至少让 `edge_good` 失败。

再运行骨架自测：

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/checker_matrix.py --selftest
```

预期输出 `SELFTEST PASS cases=12 caught=12`。若 stub 检查器也全部通过，说明矩阵断言失效，先修矩阵。

### 6. 在真实 Skill 上运行

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/checker_matrix.py \
  --checker <checker.py> \
  --real-skill C:/Users/Administrateur/.qoder/skills/windows-python-utf8-skill-scripts \
  --real-skill C:/Users/Administrateur/.qoder/skills/skill-file-qa \
  --real-skill C:/Users/Administrateur/.qoder/skills/audit-session-evidence
```

真实 Skill 的 `RESULT FAIL` 不自动算矩阵失败，但必须逐条调查。WARN 需要人工复核其归宿是否真的是 stdout；变量中转、helper 返回值和文件写入通常属于可接受的误报。

### 7. 文档与清理

1. 把来源会话、失败原文、修复前后摘要、变异体结果和真实 Skill 结果写入 references。
2. 用 skill-file-qa 流程做结构验收，记录 `Files (N)`、正文行数和指纹。
3. 删除本次产生的 `__pycache__`、`.pyc`、临时夹具和变异体副本。
4. 分别记录 SKILL.md、检查器与矩阵脚本的 size、mtime 和 SHA-256，双采样确认不再变化。

## 常见错误

| 现象 | 原因 | 修正 |
| --- | --- | --- |
| `print(...)` 识别不到 | `call_name` 未解包 `ast.Call` | 先取 `node.func` |
| 链式 `.encode` 漏检 | 用 `call_name` 判断方法调用 | 增加 `method_name` 处理 `ast.Attribute` |
| helper 中的 `json.dumps` 被误判 FAIL | 在值节点而不是输出祖先上判断 | 用 `output_ancestor` 找真正的输出调用 |
| 同一文件多条 WARN 导致计数偏大 | 按发现行计数 | 每个文件只计 1 次 |
| 检测脚本生成 `__pycache__` | 用 import 方式加载检查器 | 用子进程运行，或加 `-B` |
| 文档写 `py_compile` 生成 1 个文件 | 只数 `.pyc` | 实测为 1 个目录加 1 个 `.pyc` |
| 目录缺失时返回 1 | 把环境错误当成检查失败 | 用法或环境错误统一返回 2 |
| `--json` 含非 ASCII | 使用了 `ensure_ascii=False` | JSON 模式改为 `ensure_ascii=True` |

## 验收清单

- [ ] 矩阵 12/12 通过，退出码 0。
- [ ] `--selftest` 输出 `caught=12`。
- [ ] 两个变异体分别被矩阵抓到，失败数量与预期一致。
- [ ] 至少 3 个真实 Skill 运行完成，WARN 已人工复核。
- [ ] `SIDE_EFFECTS PASS`，目标 `scripts/` 的清单前后一致。
- [ ] 目标 Skill 与实际工具目录均无新增 `__pycache__` 或 `.pyc`。
- [ ] JSON 模式输出纯 ASCII，summary 与 RESULT 字段可解析。
- [ ] 文档中的命令在 Windows Git Bash 下可复跑，退出码先运行后取，不经管道。

## 资源

- [scripts/checker_matrix.py](scripts/checker_matrix.py)：12 项夹具矩阵、变异体自测、真实 Skill 扫描与副作用检查。
- [references/cas-static-checker-2026-10-26.md](references/cas-static-checker-2026-10-26.md)：来源会话、失败原文、修复、实测输出与文件指纹。
