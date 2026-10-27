---
name: windows-python-utf8-skill-scripts
description: "编写与验收 Skill 内置 Python 脚本的 Windows 交付流程：入口用 sys.stdout.reconfigure 或 PYTHONIOENCODING=utf-8 固定 UTF-8 输出，或改用 ensure_ascii=True 的 ASCII JSON；退出码约定 0/1/2，先运行后取码且不经管道；用 ast.parse 做语法检查避免 __pycache__；在真实产物上运行，并用合成负例断言 FAIL 与非零退出；交付前扫描缓存，并分别记录 SKILL.md 与 scripts/references 的哈希。用于 Windows 控制台 cp1252、UnicodeEncodeError、中文输出乱码或崩溃、json.dumps(ensure_ascii=False) 编码失败、管道吞掉退出码、PIPESTATUS、py_compile 生成缓存、Skill 校验器只覆盖 SKILL.md 指纹、修改脚本后未重跑负例等场景；不替代 skill-file-qa 的结构验收、参考夹具重放或 Git 提交流程。"
---

# Windows 下的 Skill Python 脚本：UTF-8 输出与写后验收

## 目标

在 Windows（Git Bash、控制台默认 cp1252）编写和验收 Skill 自带的 Python 脚本：输出不因编码崩溃，退出码真实可读，语法检查不留下 `__pycache__`，并用真实产物与合成负例证明失败分支确实失败。

## 适用范围与边界

适用：

- `scripts/` 下会被文档直接调用或由代理执行的 Python 脚本；
- 需要输出中文、审计发现或 JSON 的校验器、生成器、审计脚本；
- 交付前需要证明失败分支真的返回非零退出码的脚本。

不适用：

- 已由框架保证输出编码的 GUI、HTTP 服务或库；
- 只读复用的第三方脚本（先审计契约，不要顺手改）；
- 纯 Bash/PowerShell 脚本；
- Skill 结构、frontmatter、引用与指纹验收（交给 `skill-file-qa`）。

静态检查只证明字面量输出不太可能因编码崩溃，不证明输出内容正确。真实产物运行必须单独记录。

## 输出契约

二选一，不要混用到无法判断：

1. 入口重配置 UTF-8，适合需要中文或非 ASCII 文本的脚本：

```python
import sys

def configure_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

configure_stdout()
print("中文输出 OK")
```

调用方同时设置 `PYTHONIOENCODING=utf-8`：环境变量覆盖解释器启动阶段，`reconfigure` 覆盖脚本入口之后的写入。两者都做，脚本在缺少任一保护时仍能工作。

2. ASCII 转义输出，适合机器读取的 JSON：

```python
import json

payload = {"result": "通过", "count": 3}
print(json.dumps(payload, ensure_ascii=True))
```

- `ensure_ascii=False` 只有在确认 stdout 是 UTF-8 时才安全；在 cp1252 控制台会触发 `UnicodeEncodeError`。
- 不要依赖控制台默认编码，也不要把“在我机器上能显示”当作契约。

## 退出码契约

- `0`：通过，无发现。
- `1`：发现、断言失败或校验不通过。
- `2`：用法错误、参数缺失或环境不可用。

`argparse` 的用法错误默认退出 2；脚本自身的 `main()` 返回整数，并用 `raise SystemExit(main())` 传递。不要把“输入文件缺失”随手记成 1：先看脚本契约，用法/环境类错误保持 2，调用方才不会把配置问题误判为数据问题。

## 先运行，后取码，不经管道

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/check_script_hygiene.py . > checker.out 2>&1
rc=$?
echo "CHECKER_RC=$rc"
```

管道会吞掉真实退出码：

```bash
py -3 scripts/check_script_hygiene.py . | cat > /dev/null
status=("${PIPESTATUS[@]}")
echo "first=${status[0]} second=${status[1]}"
```

- 必须在执行任何其他命令前复制 `PIPESTATUS`，否则读到的是下一条命令的状态。
- 需要过滤输出时，先重定向到文件，再对文件 grep；不要对管道 grep 后取 `$?`。
- 在报告里同时写命令、退出码和关键输出行，不只写“失败”。

## 语法检查不留缓存

```python
import ast
from pathlib import Path

path = Path("scripts/check_script_hygiene.py")
ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
print("AST_OK")
```

- `py_compile` 和 `compileall` 会写 `__pycache__` 与 `.pyc`；实测同一环境下 `ast.parse` 后没有缓存，`py_compile` 后出现 1 个 `__pycache__` 目录和 1 个 `.pyc`。
- 必须使用编译类工具时，设置 `PYTHONDONTWRITEBYTECODE=1`，或把 `PYTHONPYCACHEPREFIX` 指向系统临时目录，并在交付前扫描。

## 写后验收顺序

1. 静态检查。在 Skill 根目录运行：

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/check_script_hygiene.py .
```

要求 `RESULT PASS` 且没有 `FAIL` 行；`WARN` 逐条判断，不能当作已通过。

2. 真实产物。用实际 Skill 目录、真实快照或真实生成物运行，不用手写小样替代；记录命令、真实输入、预期、实测与退出码。

3. 合成负例。至少覆盖：

   - 非法语法 → `FAIL syntax-error`，退出 1；
   - 非 ASCII 字面量直达 stdout 且无保护 → `FAIL non-ascii-output`，退出 1；
   - `json.dumps(ensure_ascii=False)` 直达 stdout 且无保护 → `FAIL json-ensure-ascii-false`，退出 1；
   - 目录缺失或缺少 `scripts/` → 退出 2。

   负例放在 `~/.qoder/tmp` 的独立目录，每例只破坏一个不变量；结束后只删除这个目录。

4. 编码契约运行。在 `PYTHONIOENCODING=cp1252` 下运行受保护脚本，应为退出 0 且中文输出正确；无保护脚本应为退出 1 并出现 `UnicodeEncodeError`。这只证明编码契约，不证明真实数据正确。

5. 缓存扫描与清理：

```bash
find . \( -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' \) -print
```

只删除本次创建或本次测试产生的缓存；先前已存在的缓存先确认来源。

6. 分别记录哈希。`SKILL.md`、`scripts/`、`references/` 分别计算 SHA-256、size 与 mtime，并双采样确认稳定。校验器的 Fingerprint 只覆盖 `SKILL.md`，不能外推到脚本或参考文件。

## 静态检查器的契约

`py -3 scripts/check_script_hygiene.py <skill-dir> [--json]`

- 只读：不导入、不执行脚本，不写目标目录；只扫描 `scripts/**/*.py`。
- 检查：UTF-8 解码、`ast` 语法、stdout/stderr 调用的字面量非 ASCII、`json.dumps(ensure_ascii=False)` 的输出归宿、`py_compile`/`compileall` 风险、缓存存在。
- 退出码：0 无 `FAIL`，1 存在 `FAIL`，2 用法或环境错误。
- `--json` 输出 ASCII JSON，便于代理解析。
- 摘要按文件计数，不按发现行计数；`warn` 包含 `cache-present` 的 1 条。同一文件有多条发现时，`fail` 仍只计 1。
- 启发式边界：动态拼接、变量间接、logging、第三方封装、先写文件再由别的程序打印，都不在覆盖内；`WARN` 不等于 `FAIL`。

## 与现有 Skill 的分工

| 需求 | 使用 |
|---|---|
| Skill 结构、frontmatter、引用、指纹 | `skill-file-qa` |
| 参考文件中的夹具复跑 | `replay-skill-reference-fixtures` |
| 依赖脚本契约与管道吞码 | `audit-skill-tool-contracts` |
| 并发写入与最小编辑 | `skill-update-concurrency-safe` |
| CSV/HTML 交付验收 | `verifier-livrables-csv-html-windows-fr` |
| Git 提交与忽略缓存 | `commit-skill-work` |
| 包完整性与过期归档 | `skill-package-integrity-audit` |

## 常见错误

| 症状 | 原因 | 动作 |
|---|---|---|
| `UnicodeEncodeError: 'charmap' codec` | 控制台默认 cp1252，脚本直接打印非 ASCII | 入口重配置 UTF-8，调用方设置 `PYTHONIOENCODING=utf-8`，或改 ASCII 转义 |
| `json.dumps` 输出在 cp1252 崩溃 | `ensure_ascii=False` 且 stdout 未重配置 | 改 `ensure_ascii=True` 或先重配置 stdout |
| 所有命令都返回 0 | 退出码在管道或 `cat` 之后读取 | 先运行后取码，或复制 `PIPESTATUS` |
| Skill 校验 PASS 但出现缓存 | 校验器只报告布局通过，未禁止缓存 | 单独扫描并删除本次缓存后重跑 |
| 改了 `scripts/` 但指纹没变 | 校验器 Fingerprint 只覆盖 `SKILL.md` | 分别计算脚本与参考文件哈希 |
| 负例没有失败 | 只检查输出文本，没断言退出码 | 同时断言 `FAIL` 关键词与退出码 1/2 |
| 静态检查 PASS 就宣布可用 | 静态检查不执行脚本 | 再跑真实产物与契约运行 |

## 完成检查

- [ ] 入口重配置 stdout/stderr，或所有输出做 ASCII 转义。
- [ ] `main()` 返回 0/1/2，并用 `raise SystemExit(main())`。
- [ ] 命令先运行后取码，未经过管道。
- [ ] 语法检查使用 `ast.parse`，或已重定向缓存并扫描。
- [ ] 静态检查器在真实 Skill 上 `RESULT PASS`，`WARN` 已解释。
- [ ] 真实产物运行记录了命令、输入、预期、实测与退出码。
- [ ] 合成负例覆盖 `FAIL` 与退出码 1，以及用法错误退出 2，夹具已清理。
- [ ] 缓存扫描为空，或已删除本次创建的缓存。
- [ ] `SKILL.md`、`scripts`、`references` 分别记录 SHA-256、size 与 mtime。
- [ ] 报告区分已实测、仅静态检查与未触发分支。

## 资源

- `scripts/check_script_hygiene.py`：本 Skill 的只读静态检查器。
- `references/cas-windows-python-utf8-2026-10-26.md`：来源会话的逐字证据、脚本修正、负例与本 Skill 的实测记录。
