# 复放断言骨架（零出现、正对照、键集、RC）

本文件是模板，不随本 Skill 自动执行；复用时复制到 `$BASE`，按目标脚本改写参数。`skill-file-qa` 只检查 `SKILL.md` 的代码块，不覆盖 references。2026-10-27 对两个 Python 块的实测范围：第一块的 `run`/`check`/`keyset` 在拼装执行中被使用，`zero_with_control`、`file_keyset`、`prompt_and_artifact` 未触发；第二块（多行报告与合成夹具）在安装目录外对 `verifier-parite-doc-script-skill` 副本实跑，16 项令牌全为 `_TRUE`。其余函数仍属未运行模板。

## 结构

```text
$BASE/
├── fixture/<同名 Skill>/        目标包副本
├── empty-root/                  空的项目根
├── snap/                        快照文件输出
├── out/                         每条偏差的 stdout/stderr 与 RC
├── check.py                     断言脚本（复制本模板后改写）
└── repro.sh                     逐条命令与 RC 捕获
```

## 断言脚本模板

```python
"""Assertions de rejeu pour un contrat de sortie documente."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(os.environ["BASE"])
SCRIPT = Path(os.environ["TARGET_SCRIPT"])
OUT = BASE / "out"
OUT.mkdir(parents=True, exist_ok=True)
PY = [sys.executable, "-B"]


def run(extra, log):
    proc = subprocess.run(
        PY + [str(SCRIPT)] + extra,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    body = proc.stdout + "\n--- stderr ---\n" + proc.stderr
    (OUT / (log + ".txt")).write_text(body, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def check(name, ok):
    print(name + ("_TRUE" if ok else "_FALSE"))
    return bool(ok)


def zero_with_control(text, absent, present):
    positive = len(re.findall(present, text))
    zero = len(re.findall(absent, text))
    ok_positive = check("POSITIVE_CONTROL", positive >= 1)
    ok_zero = check("ZERO_OCCURRENCE", zero == 0)
    return ok_positive and ok_zero


def keyset(text, expected):
    try:
        doc = json.loads(text)
    except ValueError:
        return check("JSON_KEYS", False)
    return check("JSON_KEYS", sorted(doc) == sorted(expected))


def file_keyset(path, expected):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return check("SNAPSHOT_KEYS", sorted(doc) == sorted(expected))


def prompt_and_artifact(text, prompt, artifact):
    count = len(re.findall(prompt, text))
    exists = Path(artifact).is_file()
    ok_prompt = check("PROMPT_ZERO", count == 0)
    ok_file = check("ARTIFACT_EXISTS", exists)
    return ok_prompt and ok_file
```

## 面向多行报告的断言（2026-10-27 增加）

用于行式报告（计数字段 + detail 行 + `RESULT`）与选项表。片段于 2026-10-27 在安装目录外对 `verifier-parite-doc-script-skill` 副本与两个合成包实跑通过；换目标须改写 `HEADER_KEYS` 与选项表。

```python
HEADER_KEYS = ["SKILL", "DOCS", "SCRIPTS", "SCOPE_FALLBACK_ALL", "DOC_KEYS",
               "RUNTIME_KEYS", "MATCHED", "DOC_ONLY", "RUNTIME_ONLY",
               "ALLOWED", "OUT_OF_SCOPE"]
DETAIL_RE = re.compile(r"^(DOC_ONLY_KEY|RUNTIME_ONLY_KEY|ALLOWED_KEY|OUT_OF_SCOPE_KEY)=")


def header_order(text):
    got = [line.split("=", 1)[0] for line in text.splitlines()[:len(HEADER_KEYS)]]
    return check("HEADER_ORDER", got == HEADER_KEYS)


def detail_layout(text):
    lines = text.splitlines()
    result_at = [index for index, line in enumerate(lines) if line.startswith("RESULT=")]
    if len(result_at) != 1:
        return check("DETAIL_LAYOUT", False)
    cut = result_at[0]
    head = lines[:len(HEADER_KEYS)]
    detail = lines[len(HEADER_KEYS):cut]
    ok_pos = check("DETAIL_AFTER_HEADERS", not any(DETAIL_RE.match(x) for x in head))
    ok_fmt = check("DETAIL_FORMAT", all(DETAIL_RE.match(x) for x in detail))
    ok_tail = check("RESULT_LAST", not any(DETAIL_RE.match(x) for x in lines[cut + 1:]))
    return ok_pos and ok_fmt and ok_tail


def option_flags(help_text):
    return sorted(set(re.findall(r"--[a-z][a-z-]+", help_text)))


def selfcheck_tuple(text):
    wanted = ("DOC_KEYS", "MATCHED", "DOC_ONLY", "RUNTIME_ONLY")
    values = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep and key in wanted:
            values[key] = int(value)
    return values


def make_synthetic(base, name, doc_lines, script_body):
    root = Path(base) / name
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_text("\n".join(doc_lines) + "\n", encoding="utf-8")
    (root / "scripts" / "emit.py").write_text(script_body, encoding="utf-8")
    return root


FENCE = "`" * 3
GHOST_DOC = ["# Synthetic", "", "## Script", "",
             "Le script `scripts/emit.py` imprime le contrat.", "",
             FENCE + "text", "REAL_KEY=1", "GHOST_KEY=2", FENCE]
NOSCRIPT_DOC = ["# Synthetic", "", "## Contrat", "",
                FENCE + "text", "REAL_KEY=1", FENCE]
make_synthetic(BASE, "synthetic-skill", GHOST_DOC, 'print("REAL_KEY=1")\n')
make_synthetic(BASE, "synthetic-noscript-name", NOSCRIPT_DOC, 'print("REAL_KEY=1")\n')
```

## 使用要点

- **RC 在管道之前取。** 用 `cmd > out/x.log 2>&1; echo "RC=$?"`，不要 `cmd | tail`。
- **零出现必须配正对照。** `zero_with_control` 先要求 `present` 命中 ≥1 次；正对照为 FALSE 时，`ZERO_OCCURRENCE` 不构成证据。
- **正则要转义。** 段头、`|`、`(` 等括号在正则里有意义，用 `re.escape` 包裹字面量。
- **键集比较用集合。** 文档列出的键写成列表，与 `sorted(doc)` 整体比较，不用 `in` 逐个子串判断。
- **产物与提示同时断言。** 「无提示」只有在文件确实存在时才有意义，否则是空断言。
- **两条命令独立执行。** `--snapshot` 与 `--compare` 分两次调用、同一字面路径、同一组根；一次调用同时传两者属于负向用例，期望 RC=2。
- **异根对比是负向控制。** 期望复现假漂移且 RC=0，用来证明文档警告成立，不是期望行为。
- **段头用有序列表。** 集合相同不算通过；detail 只允许位于计数字段与 `RESULT` 之间，`RESULT` 必须唯一且在末位。
- **选项以 `--help` 为准。** 文档提到而旗标集合 0 命中即偏差；`--help` 自身是 argparse 内置项，不计入文档选项表。
- **无失败分支时用合成包。** 多一个脚本不发的 `GHOST_KEY` 得到 `DOC_ONLY=1`/RC=1；文档不提名脚本得到 `SCOPE_FALLBACK_ALL=yes`。不改目标脚本来制造分支。
- **抽取边界。** 只扫围栏块与行内代码中的大写 `KEY=VALUE`；JSON 小写键不计入，所以 JSON 键集要单独用 `keyset` 比较。
- **自检看方向。** 补文档后 `MATCHED` 上升、`RUNTIME_ONLY` 下降是覆盖改善；`DOC_ONLY` 上升、RC=1 才是新偏差。

## 调用示例

```bash
BASE="$HOME/.qoder/tmp/rep-contract-20261027T140000-demo"
mkdir -p "$BASE/out" "$BASE/snap"
export BASE
export TARGET_SCRIPT="$BASE/fixture/nom-du-skill/scripts/script.py"
py -3 -B "$BASE/check.py"
```

## 收尾

- 只删除本次 `$BASE`；父会话或其他会话的文件不属本次创建，先确认归属。
- 检查安装目录与所有被调用 Skill 目录无 `__pycache__`/`.pyc`（`-B` 已抑制，仍要复查）。
- 复查目标脚本 SHA-256 与步骤 0 相同；`SKILL.md` 记录新旧两值。
