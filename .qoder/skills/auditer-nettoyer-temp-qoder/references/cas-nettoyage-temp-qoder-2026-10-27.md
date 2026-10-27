# Qoder 临时目录清理案例证据（2026-10-27）

案例日期：2026-10-27（UTC）
来源会话：`e4b7c222-3dad-4ee8-8e92-2670c97e43b4`（标题「创建管理员账户技能」；清理发生在此会话末段，不在会话开头）
时区：会话消息与工具调用时间戳为 UTC（带 `Z` 或工具输出中的 `date -u`）；文件 mtime 为本地时间 Europe/Paris（UTC+1，带 `+01:00`）

## 来源读取记录

| 项 | 值 |
|---|---|
| 读取方式 | `read_chat_session`，`turnLimit=20`、`includeToolOutputs=true`、`maxOutputCharsPerItem=3000` |
| 返回规模 | 约 36,441 token / 109,321 字符，MCP 工具截断并落盘 |
| runtimeState | `cold` |
| activeTurnId | `null` |
| queuedTurnCount | `0` |
| pendingInteractionCount | `0` |
| revision | `0` |
| hasMoreBefore | `false` |
| 消息数 | 18（`messages` 数组；无更早窗口） |

落盘快照（临时产物，可能被后续清理）：

`C:/Users/Administrateur/.qoder/tmp/C--Users-Administrateur-Desktop-IMAM8MAHDI/3c861dde-5275-40e4-95f8-2f430a4c8ebb/tool-results/builtin_read_chat_session_d85aff0c9024.txt`

工具输出只包含工具 `output`，不包含 `Write` / `Bash` 的输入。为核对归属脚本的真实代码，本次另行解析了项目原始 JSONL 中的工具调用输入；脚本全文见下文「脚本与命令证据」。

## 被引用产物指纹（完整 SHA-256）

| 产物 | size | mtime（+01:00） | sha256 |
|---|---|---|---|
| 来源会话 JSONL | 1,436,370 B | 2026-10-27T10:43:03.781373200+01:00 | `72cfcab70f67c29c7923f1a780a4ea07f5031dab6580bdc50488f06704beb7b4` |
| `read_chat_session` 落盘快照 | 114,711 B | 2026-10-27T11:17:54.398139500+01:00 | `d85aff0c90247f521fb1bd9181b5d41e1fcde49f54d3299b7096f7ad03f46ce3` |

JSONL 会随会话继续推进而增长；上表哈希只绑定采样点，不代表当前磁盘状态。落盘快照本身位于 `~/.qoder/tmp`，可能被同一清理流程删除。

## 清理段用户回合

| 时间（UTC） | 用户原文 | 性质 |
|---|---|---|
| 2026-10-27T05:32:04Z | `移到 .qoder/snapshots/ 下` | 纠正快照位置：从 `.qoder/skills/` 移到 `.qoder/snapshots/` |
| 2026-10-27T05:32:38Z | `清理 .qoder/tmp 下的旧快照` | 新请求：项目 `.qoder/tmp` 快照清理 |
| 2026-10-27T05:33:56Z | `继续清理其他不需要的临时文件` | 范围追加：扩展到用户级 `~/.qoder/tmp` |

清理段没有用户对技术方法的否定或改写。边界匹配与顶层 `continue` 两处问题都是代理自查后改道；用户只纠正了快照保存位置，并追加了清理范围。

## 时间线（UTC）

| 时间 | 事件 | 证据 |
|---|---|---|
| 05:32:38 | 用户要求清理项目 `.qoder/tmp` 旧快照 | 消息原文 |
| 05:32–05:33 | 枚举项目 tmp 与 `.qoder/snapshots`；比对两份快照哈希；复制 03:31 快照并校验；删除 tmp 副本与 `.last-inventory-snap` | 工具输出 |
| 05:33:56 | 用户追加「继续清理其他不需要的临时文件」 | 消息原文 |
| 05:34:08 | 基线：`~/.qoder/tmp` 89M；项目 `.qoder/tmp` 1.3M；Git 2.52.0；Python 3.14.7 | 工具输出 |
| 05:34:29 | 用户级盘点首跑：`RESULT PARTIAL`、entries=201、size=3.2M、`ENTRY_LIMIT 200`、`truncated=yes` | 工具输出 |
| 05:34–05:35 | 用户级完整盘点：2,554 条目、84.8M、204 顶层；项目级：176 条目、943.0K、23 顶层 | 工具输出 |
| 05:38:14 | 归属扫描 `NOW`；扫描 303 个会话；APP 2、NO_REF 0、OLD_REF 170、ACTIVE_REF 55 | 工具输出 |
| 05:38–05:41 | 新鲜度筛选：CAND 159 / 5,638,421 B；KEEP_RECENT 26；KEEP_ACTIVEREF 40 | 工具输出 |
| 05:41 前后 | `AskUserQuestion` 回答：「删除 159 项陈旧产物（推荐）」 | 工具输出 |
| 09:41:26–09:41:55 | 删除脚本执行：159 项 `GONE`，无 `SKIP`/`STILL` | 工具输出 `START`/`END` |
| 09:42:05 | 用户级盘点复跑：`RESULT OK`、1,754 条目、80.5M、`nested_git=2`、`pyc_files=1` | 工具输出 |
| 09:42:47 | 末次 sentinel 扫描：0；应用缓存 79,669,842 B；删除生成脚本 | 工具输出 |

候选生成（05:38Z）与删除执行（09:41Z）间隔约 4 小时。这段时间内没有重新计算引用新鲜度；删除脚本只复查条目 mtime。详见「边界与未覆盖」。

## 1. 项目快照：先备份、校验、再删 tmp 副本

项目 `.qoder/tmp` 中有两份快照：

| 快照 | size | sha256 | 处理 |
|---|---|---|---|
| `skills-snapshot-20261027T062631-4833.json` | 42,483 B | `9b8ebe95fc92150670c0ef6ef77c248bf3153be94bd7d407f7e1b448137a9de1` | 与 `.qoder/snapshots` 保留副本逐字节一致，直接删除 tmp 副本 |
| `skills-snapshot-20261027T033159-1798.json` | 40,845 B | `f67676a13c56b4dceff8e3e2b0b4abcfec0d67df22f8333098c9c1838828a20e` | tmp 中无备份，先复制到 `.qoder/snapshots`，校验哈希相同后再删除 tmp 副本 |

实际输出：

```text
9b8ebe95fc92150670c0ef6ef77c248bf3153be94bd7d407f7e1b448137a9de1 *tmp/skills-snapshot-20261027T062631-4833.json
9b8ebe95fc92150670c0ef6ef77c248bf3153be94bd7d407f7e1b448137a9de1 *snapshots/skills-snapshot-20261027T062631-4833.json
f67676a13c56b4dceff8e3e2b0b4abcfec0d67df22f8333098c9c1838828a20e *tmp/skills-snapshot-20261027T033159-1798.json
--- pointer ---
.qoder/tmp/skills-snapshot-20261027T062631-4833.json
```

复制并校验后：

```text
f67676a13c56b4dceff8e3e2b0b4abcfec0d67df22f8333098c9c1838828a20e *snapshots/skills-snapshot-20261027T033159-1798.json
40845 snapshots/skills-snapshot-20261027T033159-1798.json
42483 snapshots/skills-snapshot-20261027T062631-4833.json
--- tmp remaining json/pointer ---
(none)
```

`.last-inventory-snap` 指向已删的 06:26 快照，一并删除。两份保留快照均可解析：

```text
snapshots\skills-snapshot-20261027T033159-1798.json {'user': 73, 'project': 2, 'local': 75}
snapshots\skills-snapshot-20261027T062631-4833.json {'user': 76, 'project': 2, 'local': 78}
```

结论：项目快照不是普通临时垃圾；不可复现的那份必须先复制到 `.qoder/snapshots` 并用 SHA-256 证明副本一致，再删除 tmp 副本。`.qoder/snapshots` 中的副本不进入待删清单。

## 2. 两个根的只读盘点

用户级 `~/.qoder/tmp`：

```text
TOTALS {'entries': 2554, 'dirs': 992, 'files': 1562, 'others': 0, 'size_bytes': 88918549, 'size_human': '84.8M', 'top_entries': 204}
MARKERS {'nested_git': 11, 'sentinel_dirs': 1, 'pycache_dirs': 0, 'pyc_files': 1}
```

项目级 `<workspace>/.qoder/tmp`：

```text
TOTALS {'entries': 176, 'dirs': 45, 'files': 131, 'others': 0, 'size_bytes': 965630, 'size_human': '943.0K', 'top_entries': 23}
MARKERS {'nested_git': 0, 'sentinel_dirs': 0, 'pycache_dirs': 1, 'pyc_files': 1}
```

应用托管缓存 `C--Users-Administrateur-Desktop-IMAM8MAHDI` 为 77,532,320 B（约 77.5 MB），在用户级与项目级 tmp 中都存在同名条目；默认保留。

首跑用户级盘点使用 `--entry-limit 200`，得到：

```text
RESULT PARTIAL
TOTALS entries=201 dirs=65 files=135 others=0 size_bytes=3374658 size=3.2M top_entries=200
MARKERS nested_git=0 sentinel_dirs=0 pycache_dirs=0 pyc_files=0 errors=0 truncated=yes
```

`PARTIAL` 与 `truncated=yes` 说明统计只覆盖已扫描的 200 个条目；3.2M 不是完整体积。提高 limit 后才得到 84.8M。不要把截断结果当作删除基线。

嵌套仓库与 sentinel：

```text
nested_git: [{'path': 'C--Users-Administrateur-Desktop-IMAM8MAHDI\\inspect-qoder-skills\\.git', 'kind': 'dir'}, ..., {'path': 'refs-fixture-manual\\wt\\.git', 'kind': 'file'}]
sentinel: ['lf-clone-remote-gitattributes\\system-commandline-sentinel-files']
pycache: [] ['backup-verifier-journaux-nginx-20261027\\__pycache__-scripts\\lire_journaux_nginx.cpython-314.pyc']
```

## 3. 归属扫描：单遍读取、逐名右边界

会话 JSONL 位于 `~/.qoder/projects/*/*.jsonl`。首轮脚本使用一条 alternation：

```python
uniq = sorted(set(names))
pat = re.compile("|".join(re.escape(n) for n in uniq))
...
found = set(m.group(0) for m in pat.finditer(text))
```

缺陷：正则按左到右尝试 alternatives，短前缀先命中，带时间戳的长兄弟被吞掉。例如 `C--Users-Administrateur` 与 `C--Users-Administrateur-Desktop-IMAM8MAHDI`、`commit-skill-work-20261026` 与 `commit-skill-work-20261026T173025Z`。首轮输出：

```text
SCANNED 301 CANDIDATES 227
```

同一批候选的引用数出现前缀膨胀，无法直接用于删除。第二轮改为逐名 pattern，并加右边界：

```python
names = sorted({n for _, n in cands}, key=len, reverse=True)
pats = {n: re.compile(re.escape(n) + r"(?![A-Za-z0-9._\-])") for n in names}
...
for n, p in pats.items():
    if p.search(text):
        hits[n].add(sid)
```

第二轮输出：

```text
SCANNED 303
NOW 2026-10-27T06:38:14.764043+01:00 scanned 303
APP: [('C--Users-Administrateur', 25), ('C--Users-Administrateur-Desktop-IMAM8MAHDI', 77550904)]
== NO_REF n=0 bytes=0 ==
== OLD_REF n=170 bytes=6527111 ==
== ACTIVE_REF n=55 bytes=6024723 ==
```

要点：

- `SCANNED 303` 是排除当前会话 `e4b7c222` 后的数量；计数开始时 `~/.qoder/projects` 下有 302 个 JSONL，扫描期间另一会话新建了 1 个，所以两次计数不同。两个数字都只对采样时刻有效。
- 单遍是指每个 JSONL 只读取一次；不是对 227 个名字各跑一次 `grep`。在 441 MB 语料上逐名 `grep` 的 I/O 代价不可行。
- 右边界修复了前缀膨胀，但**没有左边界**。短名仍可能在更长 token 的尾部命中；本案例没有量化这类误命中，正文把它列为限制而不是「完全精确」。
- `NO_REF n=0`：227 个候选中没有一个是「无其他会话引用」的。若坚持「有引用就保留」，几乎无法清理；这正是必须叠加引用新鲜度的原因。
- `newest_ref_age_h` 由引用会话 JSONL 的 mtime 计算；负值表示该会话在扫描开始后仍写入，例如 `newest=-0.01h`，应按活跃处理。

## 4. 新鲜度筛选

筛选代码：

```python
its = [it for it in d['items'] if not (it['root'] == 'user' and it['name'].startswith('C--Users-Administrateur'))]
cand = [it for it in its if it['age_h'] >= 6 and it['newest_ref_age_h'] is not None and it['newest_ref_age_h'] >= 3]
keep_age = [it for it in its if it['age_h'] < 6]
keep_ref = [it for it in its if it['age_h'] >= 6 and (it['newest_ref_age_h'] is None or it['newest_ref_age_h'] < 3)]
```

输出：

```text
CAND n=159 bytes=5638421 (5.64 MB)
KEEP_RECENT n=26 bytes=1790019
KEEP_ACTIVEREF n=40 bytes=5123394
```

分桶核对：

| 桶 | 数量 | 字节 | 判据 |
|---|---|---|---|
| APP-MANAGED | 2 | 77.5 MB | 应用缓存，保留 |
| RECENT | 26 | 1,790,019 | 条目 `age_h < 6` |
| ACTIVE-REF | 40（另有 15 个 RECENT 也属 ACTIVE_REF） | 5,123,394 | `newest_ref_age_h < 3` |
| STALE-REF（候选） | 159 | 5,638,421 | `age_h >= 6` 且 `newest_ref_age_h >= 3` |
| 合计 | 227 | — | 2 + 26 + 40 + 159 |

候选明细：

```text
cand total 159 bytes 5638421
dirs 45 bytes 3981571
files 114 bytes 1656850
user 149 project 10
```

159 项按名称族的分布：

```text
commit-skill-work-   n= 22   786227 B
fingerprints-        n= 17     6659 B
QA/qualify-          n= 26    94152 B
diag-                n= 16    94909 B
snapshot-            n=  4   385347 B
session extraction   n= 18  2650286 B
fixtures/clones      n= 11   193522 B
backups              n=  5   105756 B
project QA logs      n=  5     5739 B
misc                 n= 35  1315824 B
total n=159 5638421 B
```

`age_h >= 6` 与 `newest_ref_age_h >= 3` 是本案使用的启发式阈值，不是通用契约。它们只说明「条目较旧且引用会话文件较久未写入」，不证明会话已结束，也不证明条目无人使用。

## 5. 删除脚本：顶层 `continue` 是运行时陷阱

首版生成器输出了顶层 `continue`：

```bash
N='commit-skill-work-backup-20261026T173025Z'
X="$U/$N"
if [ -z "$N" ] || [ ! -e "$X" ]; then echo "SKIP $N"; continue; fi
if [ $(( (NOW - $(stat -c %Y "$X")) / 3600 )) -lt 6 ]; then echo "SKIPRECENT $N"; continue; fi
chmod -R u+w "$X" 2>/dev/null; rm -rf -- "$X"
```

这不是合法循环上下文。代理发现后改用逐项 `if/else`：

```bash
N='...'
X="$U/$N"
if [ -n "$N" ] && [ -e "$X" ] && [ $(( (NOW - $(stat -c %Y "$X")) / 3600 )) -ge 6 ]; then
  chmod -R u+w "$X" 2>/dev/null; rm -rf -- "$X"
  if [ -e "$X" ]; then echo "STILL $N"; else echo "GONE $N 99248"; fi
else
  echo "SKIP $N"
fi
```

生成后校验：

```text
ok 159
SYNTAX_OK
159
```

执行结果：

```text
RC=0
      1 END
    159 GONE
      1 START
START 2026-10-27T09:41:26Z
END 2026-10-27T09:41:55Z
```

`grep -v '^GONE'` 只输出 `START`/`END`，说明没有 `SKIP`、`STILL` 或其他行。删除前合计 5,638,421 B。

### 本次更新独立复核顶层 `continue`（2026-10-27）

在 `%TEMP%` 构造最小脚本：

```bash
#!/usr/bin/env bash
set -u
if [ -z "" ]; then echo SKIP; continue; fi
echo AFTER
```

结果：

```text
SYNTAX_RC=0
RUN_RC=0
--- stdout ---
SKIP
AFTER
--- stderr ---
cont.sh: line 3: continue: only meaningful in a `for', `while', or `until' loop
```

结论：`bash -n` 返回 0，`continue` 不阻止后续命令；`SKIP` 打印后仍然执行 `AFTER`。因此 `bash -n` 只能证明语法，不能证明守卫有效。生成删除脚本后必须检查控制流（if/else），或在夹具上验证 `SKIP` 分支确实不删除。

## 6. 删除后复查

```text
--- sentinels ---
--- deleted-name residue ---
GONE lf-clone-remote-gitattributes
GONE crlf-probe-dev
GONE crlf-mut
GONE refs-fixture-manual
GONE qualify-skill-test-20261026T1605
GONE fixture-commit-root-22339
GONE find-stale-test-blez0hd0
GONE snapshot-20261026-1831
GONE skill-backups
GONE session-9fbfe69a-diff
GONE skill-audit-entite
--- project tmp ---
total 55
...
```

用户级盘点复跑：

```text
RESULT OK
TOTALS entries=1754 dirs=749 files=1005 others=0 size_bytes=84419869 size=80.5M top_entries=55
MARKERS nested_git=2 sentinel_dirs=0 pycache_dirs=0 pyc_files=1 errors=0 truncated=no
```

末次 sentinel 扫描：

```text
--- final sentinel scan 2026-10-27T09:42:47Z ---
0
--- app dir current bytes ---
79669842
script removed
```

对比：

| 指标 | 删除前 | 删除后 |
|---|---|---|
| 用户级 tmp 总量 | 84.8 MB | 80.5 MB |
| 应用缓存 | 77.6 MB | 79.7 MB |
| 嵌套 Git | 11 | 2（剩余两个在应用缓存内） |
| sentinel | 1（在已删夹具内） | 0（首次与末次扫描均为 0） |
| 项目 tmp 条目 | 23 顶层 | 13 顶层 |
| 删除条目 | 159 项 | 全部 `GONE` |

应用缓存在删除期间继续增长，因此 84.8→80.5 MB 不是「删除量」的净效果；删除量以脚本日志的 5,638,421 B 为准。

另一会话在期间新建了 `55f63550-extract`，未触碰。项目 tmp 剩余 13 项包括应用缓存、仍有近期引用的 `audit-contracts-*`、`contract_audit`、`correction_s6_20261026`、`site_audit`、`skill-staged-delivery-backup-20261026`、`adopt-qa-baseline.log` 与三份 `fingerprints-*`。

清理过程中发现 3 个 `__pycache__`（`github-pr-create-merge-sans-gh/scripts` 使该仓库显示 `?? scripts/__pycache__/`，另两个在非 Git 的 Skill 目录），不是本会话生成（全程使用 `py -3 -B`），未删除，代理在报告中询问用户是否一并清掉。

## 用户纠正归属

| 时间（UTC） | 用户原文 | 性质 |
|---|---|---|
| 05:32:04 | `移到 .qoder/snapshots/ 下` | 纠正快照保存位置，不是清理方法 |
| 05:32:38 | `清理 .qoder/tmp 下的旧快照` | 新请求 |
| 05:33:56 | `继续清理其他不需要的临时文件` | 范围追加 |

没有用户对「单遍扫描」「右边界」「顶层 continue」的纠正。前两项是代理自查；第三项是代理发现首版脚本后自行重生成。不要把这些写成用户纠正。

## 分级

| 结论 | 分级 | 依据 |
|---|---|---|
| 两份项目快照的哈希与保留副本一致 | 已核实 | 工具输出逐行哈希 |
| 03:31 快照在删除前已复制并可解析 | 已核实 | 复制后哈希相同、两份 JSON 均解析出计数 |
| 用户级 2,554 条目 / 84.8 MB | 已核实 | 完整盘点 `TOTALS` |
| 项目级 176 条目 / 943.0 KB | 已核实 | 项目根盘点 `TOTALS` |
| 首跑 PARTIAL 是 `--entry-limit 200` 导致 | 已核实 | 输出含 `ENTRY_LIMIT 200` 与 `truncated=yes` |
| 227 个候选、159 项 / 5,638,421 B | 已核实 | 筛选输出 |
| 首轮无边界 alternation 导致前缀膨胀 | 已核实 | 两版脚本代码与 `SCANNED 301` → `SCANNED 303` 重跑 |
| 单遍读取 441 MB / 303 会话 | 已核实 | 文件清单与 `SCANNED 303` |
| 顶层 `continue` 被 `bash -n` 放过 | 已核实 | 本次更新最小夹具：SYNTAX_RC=0、运行时 stderr、后续命令仍执行 |
| 159 项全部删除且无 SKIP/STILL | 已核实 | 日志统计 159 GONE、1 START、1 END |
| 删除脚本在删除瞬间复查条目 mtime | 已核实 | 生成脚本含 `stat -c %Y` 与 6h 守卫 |
| 删除时未重算引用新鲜度 | 已核实 | 候选生成 05:38Z，删除 09:41Z；脚本只查条目 mtime |
| 引用会话 `runtimeState` 未核实 | 已核实（未执行） | 只用 JSONL mtime 作代理 |
| GCM sentinel 由 Git Credential Manager 重建 | 未验证 | 本案唯一 sentinel 随夹具删除，未观察到重建，也未主动复现 |
| 6h/3h 阈值可推广 | 未验证 | 本案启发式；会话状态与文件用途未逐一核实 |
| 右边界匹配完全精确 | 不成立 | 左侧无边界；短名仍可在更长 token 尾部命中 |
| 删除后其他会话不再引用 | 未验证 | 只证明路径消失，不证明会话状态 |

## 边界与未覆盖

1. **只做了右边界**：`(?![A-Za-z0-9._-])` 修复前缀膨胀，但不约束左侧。候选名应保持可区分；不要把「引用了同名子串」当作「引用了该条目」。
2. **引用新鲜度是候选生成时的快照**：05:38Z 生成候选，09:41Z 才执行；4 小时间隔内没有重跑归属。`stat -c %Y` 只复查条目本身的 mtime，不复查引用会话。长时间等待确认后应重跑 Step 2，或把接近 3h 阈值的条目改判为 ACTIVE-REF。
3. **mtime 不是会话状态**：JSONL 写入只证明会话文件在动，不证明会话已结束；未调用 `list_chat_sessions` 核实 `runtimeState`。
4. **GCM 重建未复现**：本案 sentinel 1 个，位于已删的 `lf-clone-remote-gitattributes` 内；删除后首次与末次扫描均为 0。没有制造「删除后 GCM 重建」的第二次观测。
5. **阈值是启发式**：6h/3h 来自本案；不是 Qoder 的契约，也不适用于所有工作流。更保守时应提高阈值。
6. **计数会漂移**：JSONL 计数 302→303，删除期间另一会话新建 `55f63550-extract`，应用缓存 77.6→79.7 MB。所有数字只绑定采样时刻。
7. **扫描时长未记录**：只知道单遍读取 441 MB，未记录墙钟时间；不能据此承诺性能。
8. **项目快照目录未被盘点脚本覆盖**：`inventorier_tmp_qoder.py` 的 `--root` 指向 tmp；`.qoder/snapshots` 需单独 `ls`、哈希与 JSON 解析检查。
9. **应用缓存与删除量不可直接相减**：总量 84.8→80.5 MB，但应用缓存同期增长；删除量以脚本日志 5,638,421 B 为准。
10. **`__pycache__` 未处理**：清理中发现的 3 个缓存不在本 Skill 内，也不是本次导入生成；未删除，等待用户决定。

## 脚本与命令证据

### v1：无边界 alternation（有缺陷）

```python
uniq = sorted(set(names))
pat = re.compile("|".join(re.escape(n) for n in uniq))
hits = {n: set() for n in uniq}
...
found = set(m.group(0) for m in pat.finditer(text))
for n in found:
    hits[n].add(sid)
```

### v2：逐名右边界 + 会话 mtime

```python
names = sorted({n for _, n in cands}, key=len, reverse=True)
pats = {n: re.compile(re.escape(n) + r"(?![A-Za-z0-9._\-])") for n in names}
...
act[sid] = datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone()
if sid == SELF:
    continue
...
for n, p in pats.items():
    if p.search(text):
        hits[n].add(sid)
...
"newest_ref_age_h": round((NOW - newest_ref).total_seconds() / 3600, 2) if newest_ref else None,
```

### 候选筛选

```python
its = [it for it in d['items'] if not (it['root'] == 'user' and it['name'].startswith('C--Users-Administrateur'))]
cand = [it for it in its if it['age_h'] >= 6 and it['newest_ref_age_h'] is not None and it['newest_ref_age_h'] >= 3]
keep_age = [it for it in its if it['age_h'] < 6]
keep_ref = [it for it in its if it['age_h'] >= 6 and (it['newest_ref_age_h'] is None or it['newest_ref_age_h'] < 3)]
```

### 删除脚本生成

```python
for it in c:
    base = '$U' if it['root'] == 'user' else '$P'
    L.append('N=' + q(it['name']))
    L.append('X="%s/$N"' % base)
    L.append('if [ -n "$N" ] && [ -e "$X" ] && [ $(( (NOW - $(stat -c %Y "$X")) / 3600 )) -ge 6 ]; then')
    if it['is_dir']:
        L.append('  chmod -R u+w "$X" 2>/dev/null; rm -rf -- "$X"')
    else:
        L.append('  chmod u+w "$X" 2>/dev/null; rm -f -- "$X"')
    L.append('  if [ -e "$X" ]; then echo "STILL $N"; else echo "GONE $N %d"; fi' % it['size'])
    L.append('else')
    L.append('  echo "SKIP $N"')
    L.append('fi')
```

生成器使用 `$U="$HOME/.qoder/tmp"` 与 `$P="C:/Users/Administrateur/Desktop/IMAM8MAHDI/.qoder/tmp"`。在可复用流程中应把 `$P` 换成显式的 `$PROJECT_TMP`，不要硬编码某个工作区。

### 执行与统计

```bash
bash -n "$TEMP/tmp-qoder-delete-159.sh" && echo SYNTAX_OK
bash "$TEMP/tmp-qoder-delete-159.sh" > "$TEMP/tmp-qoder-delete-159.log" 2>&1
awk '{print $1}' "$TEMP/tmp-qoder-delete-159.log" | sort | uniq -c
grep -v '^GONE' "$TEMP/tmp-qoder-delete-159.log"
```

产物：

```text
%TEMP%/tmp-qoder-delete-159.sh       43,779 B
%TEMP%/tmp-qoder-delete-159.log       6,555 B
%TEMP%/tmp-qoder-deletion-candidates.json  17,303 B
```

脚本在末次 sentinel 扫描后被删除；日志与候选 JSON 保留，作为逐项 `GONE` 与字节数的证据。
