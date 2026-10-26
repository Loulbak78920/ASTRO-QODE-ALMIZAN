# 案例：变异副本未真正应用（2026-10-27）

## 1. 来源

- 会话：`8be73dee-f4c3-4730-ad1d-d0f46041c317`，标题「创建快照分流测试夹具 Skill」。
- 读取：`runtimeState=cold`、`revision=0`、`hasMoreBefore=false`、2 条消息（1 条用户、1 条助手；助手回合含 35 次工具调用）。
- 原始 JSONL：`C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\8be73dee-f4c3-4730-ad1d-d0f46041c317.jsonl`，804 899 字节。
- 相关行：变异命令在第 150、156、167、174 行；对应输出在第 152、158、169、176 行。
- 背景：该会话以只读方式采纳并发会话写出的 `tester-fixture-triage-snapshots`，随后在临时副本上独立复跑变异，以证明其断言不是空转。
- 用户决定：`AskUserQuestion` 选择「等待并只读验收（推荐）」。本案例的变异失败均由代理自查发现，不是用户纠正。

## 2. 四轮记录

| 轮次 | JSONL 行 | 构造 | 观察 | 判定 |
|---|---|---|---|---|
| 1 | 150 | B 用 `sed 's\|files_at_top() {\n\|&\|'`，跨行永不命中；C 用双反斜杠 Python replace | B、C 均 `12/12`、`GATE PASS`、rc=0 | 静默空转 |
| 2 | 156 | 普通引号 needle | `B_OLD_OCCURS 0 C_OLD_OCCURS 0`，`AssertionError: B target not unique`；随后仍运行，仍 `12/12` rc=0 | 静默空转 |
| 3 | 167 | 原始三引号 needle | `SyntaxError: unterminated string literal`；三份哈希相同 | 构造无效 |
| 4 | 174 | `q = chr(39); bs = chr(92)` | `B_OLD_OCCURS 1 C_OLD_OCCURS 1`、`COPIES_CHANGED yes`、三哈希不同 | 真正生效 |

第 1 轮原始输出：

```
== MUT A (EXPECTED=13) ==
RC=1
RESULT PASS=12 FAIL=0 TOTAL=12 EXPECTED=13
GATE FAIL
== MUT B (ls -A) ==
RC=0
RESULT PASS=12 FAIL=0 TOTAL=12 EXPECTED=12
GATE PASS
== MUT C (absolute key) ==
RC=0
0
RESULT PASS=12 FAIL=0 TOTAL=12 EXPECTED=12
GATE PASS
```

第 2 轮原始输出（节选）：

```
B_OLD_OCCURS 0 C_OLD_OCCURS 0
Traceback (most recent call last):
  File "<stdin>", line 9, in <module>
AssertionError: B target not unique
ORIG_HASH 9026e86d66eace67
== MUT B (ls -A) ==
RC=0
RESULT PASS=12 FAIL=0 TOTAL=12 EXPECTED=12
GATE PASS
```

第 3 轮原始输出（节选）：

```
  File "<stdin>", line 4
    old_b = r'''find "$1" -maxdepth 1 -type f -printf '%f\n''''
                                                              ^
SyntaxError: unterminated string literal (detected at line 4)
ORIG_HASH 9026e86d66eace67
B_HASH 9026e86d66eace67
C_HASH 9026e86d66eace67
```

第 4 轮原始输出：

```
B_OLD_OCCURS 1 C_OLD_OCCURS 1
COPIES_CHANGED yes
ORIG 9026e86d66eace67  B 23026771131e5dea  C cfeedb57acd52f87
== MUT B (ls -A) ==
RC=1
FAIL clean.git_metadata_ignored | expected=[SKILL.md ] actual=[.git SKILL.md ]
RESULT PASS=11 FAIL=1 TOTAL=12 EXPECTED=12
GATE FAIL
== MUT C (absolute key) ==
RC=1
FAIL state.update_diff_roots | expected=[UPDATE] actual=[CREATE]
FAIL state.update_mtime | expected=[UPDATE] actual=[CREATE]
FAIL state.appeared | expected=[ADOPT_RACE_APPEARED] actual=[CREATE]
FAIL state.changed | expected=[ADOPT_RACE_CHANGED] actual=[CREATE]
FAIL state.vanished | expected=[VANISHED] actual=[CREATE]
FAIL state.changed_same_size | expected=[ADOPT_RACE_CHANGED] actual=[CREATE]
RESULT PASS=6 FAIL=6 TOTAL=12 EXPECTED=12
GATE FAIL
== CLEAN ==
MUT_ABSENT
== RESIDUE ==
== TARGET ==
SKILL.md|13313|1793055655.6531406000
references/cas-2026-10-26-triage-fixture.md|8105|1793055785.2052507000
scripts/selftest_triage_snapshot.sh|5962|1793055685.6578487000
```

## 3. 根因（已独立复现）

源脚本中 `files_at_top` 的目标片段在磁盘上是反斜杠 + `n`（位于单引号内，共 2 个字符）。naive needle 到达 Python 时却含真实换行（`chr(10)`）：

```
LEN2 43 LEN4 44 EQUAL False
COUNT2 0 COUNT4 1
REPR2 'find "$1" -maxdepth 1 -type f -printf \'%f\n\''
REPR4 'find "$1" -maxdepth 1 -type f -printf \'%f\\n\''
SCRIPT LINE ['  find "$1" -maxdepth 1 -type f -printf \'%f\\n\' | LC_ALL=C sort | tr \'\\n\' \' \'']
CLEANED
```

- 复现日期：2026-10-27；目录：`~/.qoder/tmp/needle-probe`；结束后删除并确认 `CLEANED`。
- 链路：工具调用 JSON → shell heredoc → Python 字面量。`<<'PY'` 只阻止 shell 展开，阻止不了上层 JSON 折叠。
- `chr(39)`/`chr(92)` 绕过所有字面量解析；`r'''...'%f\n'''''` 因结尾 5 个引号触发 `SyntaxError`。
- 静默失败的可观测特征：副本哈希不变、结果全绿、rc=0。加入「命中数恰为 1」与「副本哈希已变」断言后立刻暴露。
- 注意：JSONL 保存的 `tool_use` 输入是折叠前的 44 字符形式（对该原文求值可得到磁盘命中 1）；实际执行的 43 字符换行形式由「命中 0」反推，并在 `needle-probe` 独立复现，未抓取执行时的层间字节。

## 4. 生效后的结果

- B（`ls -A`）：1 项 FAIL，`actual=[.git SKILL.md ]`，`RESULT PASS=11 FAIL=1 TOTAL=12`，rc=1。
- C（绝对键）：6 项 FAIL，四态退化为 `CREATE`，`RESULT PASS=6 FAIL=6 TOTAL=12`，rc=1。
- 目标三文件 sha256 与第 1 轮 `TARGET HASHES` 一致，第 2–4 轮 `%P|%s|%T@` 指纹相同（见第 4 轮 `TARGET` 段）；复核时磁盘仍为 `13313/8105/5962`。
- 本夹具的断言设计不在本文件重复，见 `tester-fixture-triage-snapshots`。

## 5. 证据分级

| 结论 | 级别 | 依据 |
|---|---|---|
| 四轮命令与输出 | 已核实 | 命令 150/156/167/174、输出 152/158/169/176 行原文 |
| 目标指纹未变 | 已核实 | 第 4 轮 `TARGET` 与第 2/3 轮 `TARGET UNCHANGED` 相同；三文件 sha256 与第 1 轮 `TARGET HASHES` 相同 |
| 43/44 字符与命中 0/1 | 已核实 | 2026-10-27 在 `~/.qoder/tmp/needle-probe` 复现并删除 |
| 折叠发生在 JSON 层 | 推断 | 由 needle 长度与行为反推，未抓取层间字节 |
| PowerShell/cmd 或其他平台同症状 | 未验证 | 未执行 |

## 6. 清理

- 第 1–4 轮副本 `triage-mut*` 均已删除并确认 `MUT_ABSENT`，无 `triage-fixture.*` 残留。
- 本案例的 `needle-probe` 已删除并确认 `CLEANED`。
- 未修改、未提交、未推送真实目标。

## 7. 补充案例：路径别名与未转换的 `/c/...` 形式（2026-10-27，本机复现）

旧守卫未拒绝一种未被 MSYS 转换的 `/c/...` 形式：该形式原样到达原生 Python 后，`Path('/c/...').resolve()` 得到 `C:\c\...`（2026-10-27 实测 `Path('/c/Users/Administrateur')` → `'\\c\\Users\\Administrateur'`，`resolve()` → `C:\c\Users\Administrateur`）；`dest.exists()` 为 False、`resolve()` 与源不同，旧脚本的 `mkdir(parents=True)` 便在 `C:\c\...` 建树并写入，仍打印 `MUTATION_APPLIED`，而真实源文件未变。诊断记录中同一命令的 `DST_ARG` 保留 `/c/.../`、`SRC_ARG` 已是 `C:/...`。

原始诊断输出：

```text
SRC_ARG   'C:/Users/Administrateur/.qoder/tmp/dup3.SGg3E9/s.sh'
DST_ARG   '/c/Users/Administrateur/.qoder/tmp/dup3.SGg3E9/s.sh/'
DST_RESOLVE 'C:\\c\\Users\\Administrateur\\.qoder\\tmp\\dup3.SGg3E9\\s.sh'
DST_EXISTS False
SAME_ERR FileNotFoundError 3
WRITE_ERR FileNotFoundError None
```

误写位置（已删除）：`C:\c\Users\Administrateur\.qoder\tmp\dup2.04qi4b\s.sh`，5898 B；清空空目录后 `/c/c` 不存在（`C_DRIVE_ROOT_ABSENT`）。

修复后的拒绝矩阵（每项均 rc=2，源文件 SHA-256 不变）：

| 输入 | reason |
|---|---|
| 同一绝对路径 | `dest_equals_source` |
| 绝对源 + 相对 dest（cwd 为源目录） | `dest_equals_source` |
| `sub/../s.sh` | `dest_equals_source` |
| 大小写变体 `S.SH` | `dest_equals_source` |
| 尾斜杠 `s.sh/` | `dest_equals_source` |
| 硬链接 | `dest_equals_source` |
| 已存在的其他文件 | `dest_exists`（内容未动） |
| 父目录不存在 | `dest_parent_missing` |

修复内容：`/c/...` 与 `/cygdrive/c/...` 规范为盘符路径；先 `samefile` 再 `resolve` 比较；要求父目录已存在、不再创建父目录；写后复核不是同一文件且源哈希未变。修复后经 Python subprocess 绕过 MSYS 转换复核：`C:/.../s.sh/` 与 `/c/.../s.sh` 均返回 `dest_equals_source` rc=2，源文件 SHA-256 未变。

证据级别：误写位置与 `Path('/c/...')` 的解析结果为已核实（本机输出）；`/cygdrive/c/...` 规范化已实跑复核（应用成功、同一文件被拒）；「尾斜杠导致未转换」不成立（2026-10-27 实测 `MSYS_NO_PATHCONV`/`MSYS2_ARG_CONV_EXCL` 均未设置时，带尾斜杠的 `/c/Users/Administrateur/` 仍被转换为 `C:/Users/Administrateur/`），那次未转换的调用条件未取证，判为推断；其他 shell 或平台未验证。
