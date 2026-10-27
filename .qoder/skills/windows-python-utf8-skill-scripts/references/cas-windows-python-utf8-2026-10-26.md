# 案例档案：Windows 下的 Python 输出编码与脚本验收（2026-10-26）

## 1. 来源与读取方式

- 来源会话：`2d03c16d-5f3b-453a-a785-7156205dc385`（创建审计证据技能）。
- 原始 JSONL：`C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\2d03c16d-5f3b-453a-a785-7156205dc385.jsonl`。
- 观测值：302 行，1,110,484 B，SHA-256 `3581a41bd2cfefa2f5fa31d7357203b9f33c5f9bbf40a460b7d51b691559291e`，mtime `2026-10-26 15:58:28 +01:00`。
- 读取方式：先用 `read_chat_session` 有界读取，再直接解析项目 JSONL；本档案的“第 N 行”都指 JSONL 行号，不是工具调用序号。

环境：Windows 10.0.26200，Git Bash 2.52.0.windows.1，Python 3.14.7，时区 Europe/Paris（UTC+1）。

## 2. 会话结构与“用户纠正”核查

- 真实人类消息只有 1 条：第 3 行的初始请求。
- 第 18 行是 `skill-creator` 注入的 Skill 正文，不是用户发言。
- 第 250 行是继续摘要（`type=user` 的 text），不是用户纠正。
- 结论：本会话**没有用户纠正**。后续脚本行为变化来自代理自查；不得写成“用户指出”或“用户要求”。

## 3. 失败现场：cp1252 控制台（第 60 行）

第 58 行的命令直接以 `py -3 - <<'PY'` 解析 JSONL 并打印中文摘要，未设置输出编码。第 60 行 tool_result 逐字如下（节选）：

```text
Exit code 1
file= C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\92a9e96f-dd91-4dfb-b3ab-3eb58946a564.jsonl
size= 660895 sha256= 3c5cf34a25ef25f5 mtime= 1793025468.3332765
lines= 156
Traceback (most recent call last):
  File "<stdin>", line 28, in <module>
  File "C:\Users\Administrateur\AppData\Local\Python\pythoncore-3.14-64\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode characters in position 37-51: character maps to <undefined>
```

诊断与修复：

- Windows 控制台/管道默认 cp1252；`print` 非 ASCII 文本在编码阶段失败。
- 第 65 行起的命令加 `PYTHONIOENCODING=utf-8`。
- 被审计脚本入口加入 `configure_stdout()`，对 `sys.stdout`/`sys.stderr` 调用 `reconfigure(encoding="utf-8", errors="replace")`。
- 这是当时被审计脚本的失败，不是本 Skill 的脚本；本 Skill 把同一契约写成通用规则。

## 4. 代理自查的三处修正

### 4.1 同一行重复计数（第 152 行 → 第 176 行）

- 第 152 行：`count_claims=6, 4`，`session_near=778965d0-ebd3-4d34-aafd-3908fb635ec6`。
- 第 176 行：`count_claims=6`，`session_near=41c1eeca-e7e8-4b10-baa4-50151d05499e`。
- 第 186 行修正：每条计数断言只用本行的 `session_ids(line)`；无行内会话时回退前 4 行，但仍要求该行带会话标签。
- 第 207 行修正：删除跨行回退，无行内会话时改用 `inferred`，避免把相邻行的无关会话算给当前断言。
- 第 197 行复跑：`scan-counts` 命中 `$.messages[1].tools[31].output count=6 session_near=6f896eb6-ed02-46ef-aa73-2d0d08285c5b`。

### 4.2 `activeTurnId` 被当成会话主语（第 179 行）

原 `nearest_session()` 取窗口内距离最近的 UUID，结果选中了 `activeTurnId: 778965d0...`。第 179 行替换为 `session_ids()`：

- 跳过前 30 个字符内出现 `activeTurnId` 且没有 `会话`/`sessionId` 的 UUID；
- 识别反引号中的 8 位短 ID，以及 `会话`/`session`/`sessionId` 前缀后的短 ID；
- `nearest_session()` 改为取断言前最近的已识别会话，没有则取之后最近的。

第 185 行的 `doc_subject()` 同步改用 `session_ids()`。第 184 行删除 `SHORT_ID_RE`，避免把普通 8 位十六进制词当会话。

注意：第 176 行显示的 `session_near=41c1eeca` 不是回归失败；该扫描窗口里最近的已标记会话确实是 41c1eeca。最终对目标快照的命中以第 197 行为准。

### 4.3 断言归属与负例

第 203 行的合成夹具（4 条消息快照）：

```text
===== bad.md RC=1 =====
L2 claim=6 session=09829df8-d996-48d8-a6b8-8d2fbdbf4bee status=FAIL
RESULT FAIL
===== good.md RC=0 =====
L2 claim=4 session=09829df8-d996-48d8-a6b8-8d2fbdbf4bee status=PASS
RESULT PASS
===== other.md RC=0 =====
L2 claim=6 session=6f896eb6-ed02-46ef-aa73-2d0d08285c5b status=OTHER_SESSION
L3 claim=4 session=6f896eb6-ed02-46ef-aa73-2d0d08285c5b status=OTHER_SESSION
warnings_other_session=2
RESULT PASS
FIXTURE_RESULT=PASS
fixture_removed=True
```

第 216 行回归 7/7 通过：

```text
PASS  scan session_near=6f896eb6
PASS  cas doc PASS + other session
PASS  preuves vs 6f896eb6 PASS
PASS  preuves vs 09829df8 SUBJECT_MISMATCH
PASS  bad doc FAIL
PASS  good doc PASS
PASS  other doc PASS + warning
FIXTURE_RESULT=PASS
```

## 5. 来源会话的产检验收（第 262 行）

被审计 Skill `audit-evidence-count-provenance` 的 `skill-file-qa` 输出：

```text
Files (3): SKILL.md, references/cas-count-provenance-2026-10-26.md, scripts/audit_evidence_counts.py
PASS layout: 3 file(s), no extraneous documentation
PASS description: single line, 424 chars
PASS body: 139 lines (< 500)
PASS local references: 2 checked
PASS skill references: 5 checked
Fingerprint (start): 12419 bytes | sha256=9836b6da6be4a12f60dc80a646471bc97f8a2dcd161bd35ed5a930b0b2d7c0bc
Fingerprint (final):  12419 bytes | sha256=9836b6da6be4a12f60dc80a646471bc97f8a2dcd161bd35ed5a930b0b2d7c0bc
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
EXIT=0
```

边界：这是**另一个 Skill** 的验收，不能用来证明本 Skill。它同时说明 `Fingerprint` 只覆盖 `SKILL.md`；脚本与参考文件当时另行记录（脚本 9,567 B `4b23e22d3d45cb12bbc6f9eeb7098a7da2d1951b22edd16428cc8f85312db807`，参考文件 11,173 B `a263d89875fda22222c7237fd5c79a3a0eab9dee3ef1d7046c40c3aa3a1c2395`）。

2026-10-26 复检：`audit_evidence_counts.py` 仍为 9,567 B、`4b23e22d...`；`skill-file-qa` 的 `validate_skill.py` 为 21,896 B、`1932ce4840054675f0608616e05f9f2c55db5eb749255f6a30c4cfd46e6789d8`。

## 6. 本 Skill 的静态检查器实测

夹具根：`C:\Users\Administrateur\.qoder\tmp\windows-python-utf8-skill-scripts-fixture-20261026T160800`（测试后删除）。

命令：

```bash
PYTHONIOENCODING=utf-8 py -3 scripts/check_script_hygiene.py <fixture>
```

| 夹具 | 退出码 | 摘要或关键行 |
|---|---|---|
| `audit-evidence-count-provenance`（真实 Skill） | 0 | `scripts=1 pass=0 fail=0 warn=1`；`WARN json-ensure-ascii-false L148`；`RESULT PASS` |
| `all` | 1 | `scripts=8 pass=3 fail=3 warn=2`；3 个 FAIL：`json-ensure-ascii-false`、`non-ascii-output`、`syntax-error`；`RESULT FAIL` |
| `pass_only` | 0 | `scripts=3 pass=3 fail=0 warn=0`；`RESULT PASS` |
| `warn_only` | 0 | `scripts=2 pass=0 fail=0 warn=2`；`RESULT PASS` |
| `cache` | 0 | `WARN cache-present 1 file(s): scripts/__pycache__/dummy.pyc`；`RESULT PASS` |
| `empty` | 0 | `scripts=0 pass=0 fail=0 warn=0`；`RESULT PASS` |
| `bad_encoding` | 1 | `FAIL invalid-utf8 L1 not valid UTF-8: invalid start byte` |
| 目录不存在 | 2 | `ERROR: skill directory not found` |
| 缺少 `scripts/` | 2 | `ERROR: scripts directory not found` |
| `all --json` | 1 | JSON 可解析，`summary={'scripts': 8, 'pass': 3, 'fail': 3, 'warn': 2}`，`result=FAIL` |

真实 Skill 的 `WARN` 是启发式结果：`json.dumps(..., ensure_ascii=False)` 的结果先赋给变量、再被打印，检查器看不到输出归宿；人工确认该脚本已 `reconfigure` stdout，因此判为可接受，而不是“已由静态检查证明安全”。

## 7. 本 Skill 的运行时与缓存实测

编码契约（`PYTHONIOENCODING=cp1252`）：

```text
SAFE_RC=0           # 入口 reconfigure 后输出：中文输出 OK
UNSAFE_RC=1         # UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-3
```

退出码与管道：

```text
DIRECT_RC=1
PIPE_STATUS_FIRST=1 PIPE_STATUS_SECOND=0
```

即：直接运行的脚本退出 1；经 `| cat` 后管道最后一条命令退出 0，真实退出码只在 `PIPESTATUS[0]`。

缓存：

```text
AST_RC=0
CACHE_AFTER_AST=0
COMPILE_RC=0
CACHE_AFTER_COMPILE=2   # ./__pycache__ 与 ./__pycache__/safe_utf8.cpython-314.pyc
CACHE_CLEANED=yes
```

结论：`ast.parse` 不产生字节码缓存；`py_compile` 会产生，交付前必须重定向或扫描清理。

## 8. 未覆盖与边界

- 只在 Windows 10.0.26200 + Git Bash + Python 3.14.7 实测；未覆盖 PowerShell、cmd、Linux、macOS 与 CI。
- 未覆盖 Python 3.10–3.13；`reconfigure` 存在但未逐一复跑。
- 静态检查器不检测动态拼接字符串、logging、第三方封装、写入文件后再由其他进程打印等路径。
- 只检查 `scripts/**/*.py`；不检查 JS、Bash、PowerShell。
- 运行时探针使用最小脚本，不证明所有真实 Skill 脚本的数据正确性。
- 来源会话的产检验收属于 `audit-evidence-count-provenance`；本 Skill 的最终验收以交付报告中的 `skill-file-qa` 输出与哈希为准。
