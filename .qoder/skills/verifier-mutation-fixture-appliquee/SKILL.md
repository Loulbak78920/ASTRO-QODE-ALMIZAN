---
name: verifier-mutation-fixture-appliquee
description: "在运行任何由文本替换得到的变异副本之前，先证明变异确实写入磁盘：断言旧串命中恰为 1、新串出现、副本 SHA-256 与原件不同，再运行变异体并要求出现预期 FAIL 与非零退出码；副本未改一律判 NOT_APPLIED，已改但全绿判 INERT，不得当作复现。解决 JSON→shell→Python 三层转义把反斜杠 n 变成真实换行导致的 0 命中与假全绿，首选从源文件按锚点提取整行转 hex，次选 chr(39)/chr(92) 构造；含只读清理与原件指纹复核。用于变异夹具空转、副本哈希未变、命中 0、变异后仍全绿、sed 跨行替换失效、三引号 SyntaxError、需要证明变异已生效。中文触发：变异未生效、副本未改、命中 0、假全绿、空转变异、三层转义、变异门禁；English: mutation not applied, copy hash unchanged, zero match, green mutant, escaping layers, mutation gate; Français: mutation non appliquée, empreinte de la copie inchangée, zéro occurrence, mutant vert, échappement."
---

# 变异夹具已应用门禁

## 目标与边界

变异体的结果只有在证明「替换已写入副本」之后才可解释。本 Skill 提供运行前的三断言门禁、四态判定、转义安全的 needle 构造与只读清理。

- 只负责证明与应用：不设计变异体（用 `develop-skill-static-checker` 或 `skill-validator-selftest`）、不重放既有夹具（用 `replay-skill-reference-fixtures`）、不验收 Skill 包（用 `skill-file-qa`）、不实现双快照分流夹具（用 `tester-fixture-triage-snapshots`）、不做工具契约能力探针（用 `audit-skill-tool-contracts`，其 §6 已要求「先证明变异生效」）。
- 适用于任何语言、任何「复制文件 → 字符串替换 → 运行」式变异；真实目标始终只读。

## 不可协商规则

1. 只在副本上变异：副本建在 `~/.qoder/tmp/<name>.<mktemp 随机>/`，真实目标不得写入。
2. 运行前三断言全部成立才可继续：
   - 旧串命中数恰为 `1`；
   - 替换后新串命中数至少为 `1`；
   - 副本 SHA-256 与原件不同。
   任一失败即 `NOT_APPLIED`，后续输出全部作废。
3. 副本已改但运行全绿：判 `INERT`，不得称「复现」或「验证通过」；先确认断言是否覆盖该行为。
4. 变异副本无法解析（`bash -n` 失败、Python `SyntaxError`）或退出码不符预期：判 `INVALID_MUTANT`，不计为复现。
5. 结束必须删除副本并确认不存在，并复核原件 size、mtime、SHA-256 未变。
6. 禁止用 `sed` 做跨行替换；禁止在命令里裸写含反斜杠的 needle。
7. 副本父目录必须已存在（用 `mktemp -d` 创建）；脚本不创建任何父目录，避免路径别名把副本写到预期之外的位置。
8. 失败即停：`apply_mutation.py` 成功后才运行副本，命令用 `&&` 或 `set -euo pipefail` 串联；运行变异体本身前先 `set +e` 再取 `$?`。来源第 2 轮中 Python `AssertionError` 之后命令仍继续，最终 `rc=0`，全绿被误读。

## 第 1 步 — 记录基线

```bash
TARGET="$HOME/.qoder/skills/<skill-name>"
SRC="$TARGET/scripts/<fixture>.sh"
find "$TARGET" -type f -printf '%P|%s|%T@\n' | sort
sha256sum "$SRC"
```

## 第 2 步 — 从磁盘取 needle，不手写转义

按唯一 ASCII 锚点提取整行并转 hex；命令中不出现反斜杠：

```bash
HEX=$(PYTHONIOENCODING=utf-8 py -3 - "$SRC" <<'PY'
import pathlib, sys
lines = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
cand = [l for l in lines if "maxdepth 1" in l and "-printf" in l]
assert len(cand) == 1, "anchor not unique"
print(cand[0].strip().encode("utf-8").hex())
PY
)
```

锚点必须唯一；`assert` 失败即换锚点，不得放宽为多个候选。若只替换行内片段，先确认该片段在整文件中唯一，再单独转 hex。

## 第 3 步 — 应用并证明

```bash
MUT=$(mktemp -d "$HOME/.qoder/tmp/mut.XXXXXX")
py -3 "$HOME/.qoder/skills/verifier-mutation-fixture-appliquee/scripts/apply_mutation.py" \
  --source "$SRC" --dest "$MUT/mutant.sh" \
  --old-hex "$HEX" --new-text 'ls -A "$1"'
```

脚本只写 `--dest`，并在写盘前完成命中数断言。拒绝规则：`dest` 等于 `source`（含硬链接、符号链接、大小写与尾斜杠别名）→ `dest_equals_source`；`dest` 已存在 → `dest_exists`；`dest` 的父目录不存在 → `dest_parent_missing`（脚本不创建父目录）；以 `/c/...` 或 `/cygdrive/c/...` 传入的参数由脚本规范为盘符路径。写盘后复核 `dest` 与 `source` 不是同一文件、`source` 哈希未变。必须看到：

```
OLD_OCCURS 1
NEW_OCCURS 1
CHANGED yes
RESULT MUTATION_APPLIED
```

任一行缺失或脚本 rc 非 0 → 停止，不得运行副本。

## 第 4 步 — 运行并解释

```bash
bash -n "$MUT/mutant.sh"; echo "BASHN_RC=$?"
bash "$MUT/mutant.sh" >"$MUT/out.txt" 2>&1; RC=$?
echo "RUN_RC=$RC"
grep -c '^FAIL' "$MUT/out.txt"
grep -E '^(FAIL|RESULT|GATE)' "$MUT/out.txt"
```

退出码必须在管道或过滤之前取。

| 观察 | 判定 | 动作 |
|---|---|---|
| 副本哈希等于原件，或 `OLD_OCCURS != 1` | `NOT_APPLIED` | 结果作废；换 needle 构造后重做 |
| 副本已改，运行全绿且 `rc=0` | `INERT` | 不得称复现；检查断言是否覆盖该变异 |
| 副本已改，出现预期 FAIL 且 `rc` 非零 | `CONFIRMED` | 记录 FAIL 名称、计数与 `rc` |
| 副本已改，但语法错误或 `rc` 不符预期 | `INVALID_MUTANT` | 重新构造，不计入复现 |
| 原件 size/mtime/SHA-256 变化 | `TARGET_DRIFT` | 立即停止，调查写入者 |

## 第 5 步 — 清理

```bash
rm -rf "$MUT"
[ -e "$MUT" ] && echo MUT_REMAINS || echo MUT_ABSENT
find "$HOME/.qoder/tmp" -maxdepth 1 -name '<name>.*' -printf '%f\n'
sha256sum "$SRC"
```

最后的 `sha256sum` 必须与第 1 步一致。

## 三层转义（实测）

needle 要经过工具调用 JSON、shell heredoc、目标语言字面量三层。裸写含反斜杠的字符串常在中间层被折叠成真实换行，且不报错：

- 2026-10-27 实测：naive needle 长 `43` 字符且含真实换行，命中 `0`；`chr(92)` 构造长 `44` 字符（反斜杠 + n），命中 `1`。
- 同一轮用 `r'''...'%f\n'''''` 直接触发 `SyntaxError: unterminated string literal`。
- 结论：优先「从磁盘取行 → hex」；无法避免构造时用 `q = chr(39); bs = chr(92)`，并在写盘前断言命中数与哈希。
- 静默失败的特征是「副本哈希不变 + 结果全绿」；看到全绿先查哈希，不要先怀疑被测对象。

## 报告模板

| 项 | 值 |
|---|---|
| 源文件 / 副本 | 绝对路径 |
| 变异 | 旧片段 → 新片段（一句话） |
| 命中 / 新串 / 哈希变化 | `OLD_OCCURS`、`NEW_OCCURS`、`CHANGED` |
| 运行 | `RUN_RC`、FAIL 名称与计数、`RESULT`/`GATE` |
| 判定 | `CONFIRMED` / `NOT_APPLIED` / `INERT` / `INVALID_MUTANT` |
| 清理 | `MUT_ABSENT`、残留扫描结果 |
| 原件 | 前后 size/mtime/SHA-256 一致 |

## 已验证案例

来源会话 `8be73dee-f4c3-4730-ad1d-d0f46041c317` 连续 2 次静默空转、1 次 `SyntaxError`，加入命中数与哈希断言后才发现；改用 `chr(92)` 才复现 `ls -A` 的 `.git` 误判与绝对键的 6 项 FAIL。详见 [references/cas-2026-10-27-mutation-escape.md](references/cas-2026-10-27-mutation-escape.md)。

## 资源

- [scripts/apply_mutation.py](scripts/apply_mutation.py)：单次精确替换，写盘前断言命中恰为 1，写后复核哈希已改变。
- [references/cas-2026-10-27-mutation-escape.md](references/cas-2026-10-27-mutation-escape.md)：四轮原始命令与输出、根因复现与证据分级。
