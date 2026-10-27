# 案例档案：Skill 静态检查器的矩阵式验收（2026-10-26）

本文件记录 develop-skill-static-checker 的来源、失败原文、修复过程、实测输出与交付指纹。结论分为三类：

- **已核实**：来自本次实际命令输出或落盘文件。
- **推断**：由已核实事实推出，但没有单独命令直接证明。
- **未验证**：本轮没有执行或没有覆盖。

## 1. 来源会话

| 项目 | 值 |
| --- | --- |
| 会话 ID | `420efacb-b65b-42e4-81e9-03ff0e762982` |
| 标题 | 创建 Windows Python UTF-8 Skill |
| 项目 | `C:\Users\Administrateur\Desktop\IMAM8MAHDI` |
| 原始 JSONL | `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\420efacb-b65b-42e4-81e9-03ff0e762982.jsonl` |
| JSONL size | 1,728,885 B |
| JSONL mtime | 2026-10-26 16:17:33.420501000 +01:00 |
| JSONL SHA-256 | `f04807e7ce3ca15481da91074611b32426c3f4cad29767074045471e4acb9e63` |
| revision | 121 |
| runtimeState | ready |
| hasMoreBefore | false |
| 工具调用 | 97 次 |

**已核实**：该会话只有 1 条人类文本消息和 1 次 AskUserQuestion 选择（选择「完整包（推荐）」）。没有用户纠正。检查器的所有变化都由夹具失败驱动，不是用户改稿。

**已核实**：推荐数据中「用户纠正」「失败原因」等主张不能直接当作会话事实；本档案只采用 JSONL 与工具输出中可复核的字段。

## 2. 来源会话中的检查器

被审计和被修正的参考实现：

| 项目 | 值 |
| --- | --- |
| 路径 | `C:\Users\Administrateur\.qoder\skills\windows-python-utf8-skill-scripts\scripts\check_script_hygiene.py` |
| size | 11,292 B |
| mtime | 2026-10-26 16:09:57.333279 +01:00 |
| SHA-256 | `c6f612b5126bd9a48f5c10acec155fbd9032824310e63d891cf3d0ef45523986` |

该检查器只读扫描 `<skill-dir>/scripts/**/*.py`，CLI 为：

```text
<checker> <skill-dir> [--json]
```

输出契约：

```text
SUMMARY scripts=8 pass=3 fail=3 warn=2
RESULT FAIL
WARN cache-present 1 file(s): scripts/__pycache__/dummy.pyc
ERROR: scripts directory not found: ...
```

**已核实**：错误行带 ASCII 冒号 `ERROR:`。这正是首轮矩阵误写断言的原因，见第 4 节。

## 3. 来源会话中的失败与修复

### 3.1 调用名未解包 `ast.Call`

初始 `call_name()` 只处理 `ast.Name` 与 `ast.Attribute`，遇到 `ast.Call` 返回空串。

**已核实**的调试输出：

```text
CALL name=''
output_calls []
```

**已核实**的首次检查器运行摘要：

```text
SUMMARY scripts=8 pass=6 fail=1 warn=1
CASES_FAILURES=3
```

预期是 `scripts=8 pass=3 fail=3 warn=2`。`bad_print`、`bad_json`、`warn_json` 三类夹具因此漏报。

修复：

```python
def call_name(node):
    if isinstance(node, ast.Call):
        node = node.func
```

### 3.2 helper 与链式 `.encode` 被误判

`inside_output()` 原来在 `json.dumps` 值节点上检查 helper，而不是在输出祖先上检查；同时用 `call_name(child).endswith(".encode")` 判断方法，链式 `str(value).encode(...)` 会返回空串，导致 `good_json_helper.py` 被误判 FAIL。

修复要点：

1. 引入 `output_ancestor()`，向上找到真正的输出调用。
2. 在输出祖先上调用 `calls_ascii_helper()`。
3. 新增 `method_name()`，改用 `method_name(child) != "encode"`。

### 3.3 检测器自身生成缓存

**已核实**：用 import 方式探测检查器时生成：

```text
scripts/__pycache__/check_script_hygiene.cpython-314.pyc
18,976 B
```

已清理。矩阵因此坚持用子进程运行检查器，不使用 import。

### 3.4 缓存计数文档错误

**已核实**：`py_compile` 后实测 `CACHE_AFTER_COMPILE=2`：

```text
./__pycache__
./__pycache__/safe_utf8.cpython-314.pyc
```

文档原写「生成 1 个」，已修正为「1 个目录和 1 个 `.pyc`」。

## 4. 矩阵验收结果

矩阵脚本：[scripts/checker_matrix.py](../scripts/checker_matrix.py)

### 4.1 首跑失败

**已核实**的首跑输出（`matrix_run1.out`）：

```text
CASE no_scripts FAIL rc=2 want=2
  missing token: ERROR scripts directory not found
CASE missing FAIL rc=2 want=2
  missing token: ERROR skill directory not found
SUMMARY cases=12 failures=2 real=0
RESULT FAIL
EXIT=1
```

原因：断言漏写冒号。检查器实际输出 `ERROR: ...`。修正断言后重跑。

### 4.2 12/12 通过

**已核实**（`matrix_run2.out`）：

```text
CASE pass_only PASS rc=0
CASE all PASS rc=1
CASE warn_only PASS rc=0
CASE edge_bad PASS rc=1
CASE edge_good PASS rc=0
CASE cache PASS rc=0
CASE empty PASS rc=0
CASE no_scripts PASS rc=2
CASE missing PASS rc=2
CASE bad_encoding PASS rc=1
CASE json_contract PASS rc=1
CASE help PASS rc=0
SIDE_EFFECTS PASS
SUMMARY cases=12 failures=0 real=0
RESULT PASS
CLEANUP OK
EXIT=0
```

### 4.3 自测与变异体

**已核实**（`matrix_selftest.out`）：

```text
SELFTEST PASS cases=12 caught=12
CLEANUP OK
EXIT=0
```

**已核实**（`matrix_mutant_call.out`）：移除 `ast.Call` 解包后：

```text
SUMMARY cases=12 failures=5 real=0
RESULT FAIL
EXIT=1
```

失败用例为 `all`、`warn_only`、`edge_bad`、`edge_good`、`json_contract`，与预期一致。

**已核实**（`matrix_mutant_encode.out`）：恢复链式 `.encode` 旧判断后：

```text
CASE edge_good FAIL rc=1 want=0
  missing token: WARN json-ensure-ascii-false
  missing token: SUMMARY scripts=3 pass=2 fail=0 warn=1
SUMMARY cases=12 failures=1 real=0
RESULT FAIL
EXIT=1
```

只有 `edge_good` 失败，说明该夹具确实锁定了链式 encode 判断。

**说明**：`matrix_*.out` 是生成时的会话临时输出，已随临时目录清理；以上代码块是当时的逐字摘录，独立复跑命令见第 8 节。

## 5. 真实 Skill 测量

**已核实**（`matrix_real.out`，与 12 项夹具同次运行；12 个 `CASE` 行全部 `PASS`，此处只摘录真实 Skill 行）：

```text
REAL windows-python-utf8-skill-scripts rc=0 result=PASS summary=scripts=1 pass=1 fail=0 warn=0 warn_lines=0
REAL skill-file-qa rc=0 result=PASS summary=scripts=1 pass=1 fail=0 warn=0 warn_lines=0
REAL audit-session-evidence rc=0 result=PASS summary=scripts=1 pass=0 fail=0 warn=1 warn_lines=3
REAL   WARN json-ensure-ascii-false L54 ensure_ascii=False outside a detected stdout call; verify the sink encoding
REAL   WARN json-ensure-ascii-false L103 ensure_ascii=False outside a detected stdout call; verify the sink encoding
REAL   WARN json-ensure-ascii-false L101 ensure_ascii=False outside a detected stdout call; verify the sink encoding
SIDE_EFFECTS PASS
SUMMARY cases=12 failures=0 real=3
RESULT PASS
CLEANUP OK
EXIT=0
```

### 5.1 WARN 人工复核

**已核实**：`audit-session-evidence/scripts/audit_session.py` 的三个位置都是 `json.dumps(..., ensure_ascii=False)` 的返回值，不是直接 stdout：

- L54：`flatten_content()` 返回给调用方。
- L101：`format_value()` 的内部变量赋值。
- L103：`format_value()` 的返回值。

**已核实**：3 条 WARN 属于同一文件，摘要是 `warn=1`，符合按文件计数的契约。

**推断**：这些是保守型 WARN，不是缺陷；如果要把它们变成 PASS，需要增加 helper 返回值归宿的数据流分析，本轮不做。

## 6. 当前交付指纹

**已核实**（写入后用 size、mtime、SHA-256 双采样）：

| 文件 | size | SHA-256 |
| --- | --- | --- |
| `SKILL.md` | 9,552 B | `230e7377101cf6cfcbe5dbb630624b7fb605f33aa92bd2fce6034ee938ce0e4b` |
| `scripts/checker_matrix.py` | 17,776 B | `56da149c6f9c34e4865b2596863a4c8dcda34e58fc8e1506cf7cf6edf354760f` |
| `references/cas-static-checker-2026-10-26.md` | 本文件 | 由交付报告记录，避免自指 |

`SKILL.md` 的 mtime 为 2026-10-26T16:39:43+01:00。结构验收记录为 `Files (3)`、正文 156 行、description 320 字符、9 pass / 0 fail / 0 warn。

矩阵脚本的 mtime 为 2026-10-26T16:30:50.363607+01:00。

**说明**：本文件不写入自身哈希，因为写入哈希会改变文件内容。最终哈希由交付报告记录。

## 7. 边界与未验证项

- **已核实**：矩阵验证的是检查器的输出契约、夹具行为与只读性，不验证被扫描脚本的运行时语义。
- **已核实**：矩阵只运行了 3 个真实 Skill，不能代表全部已安装 Skill。
- **未验证**：非 UTF-8 控制台（例如强制 cp1252）下的实际显示效果；本轮统一设置 `PYTHONIOENCODING=utf-8`。
- **未验证**：Python 3.8 及更早版本；本轮解释器为 Windows 上的 `py -3`（cpython-314 缓存名）。
- **未验证**：检查器对 symlink、junction、超大文件与循环目录的行为。
- **未验证**：并发写入 Skill 目录时的稳定性；本轮运行前后清单一致，但没有并发写入者。
- **推断**：`SIDE_EFFECTS PASS` 只证明夹具目录与检查器父目录没有变化，不证明系统其他位置没有副作用。

## 8. 复跑命令

```bash
cd C:/Users/Administrateur/.qoder/skills/develop-skill-static-checker
PYTHONIOENCODING=utf-8 py -3 scripts/checker_matrix.py \
  --checker C:/Users/Administrateur/.qoder/skills/windows-python-utf8-skill-scripts/scripts/check_script_hygiene.py \
  --real-skill C:/Users/Administrateur/.qoder/skills/windows-python-utf8-skill-scripts \
  --real-skill C:/Users/Administrateur/.qoder/skills/skill-file-qa \
  --real-skill C:/Users/Administrateur/.qoder/skills/audit-session-evidence
```

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/checker_matrix.py --selftest
```

退出码应先运行后读取，不经管道。矩阵的 `EXIT=` 行与进程退出码必须一致。
