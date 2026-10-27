---
name: verify-injected-skill-body-freshness
description: "验证 Skill 重新加载或只读调用后，本次注入正文是否为磁盘最新版本（并发写入窗口）：从当前磁盘最后一次写入选取哨兵，调用前后采样 size/mtime/SHA-256，最新哨兵缺失时用版本分界短语与标题行号偏移定界到具体旧版本，扫描候选会话 JSONL 的 Write/Edit 记录归因写入者（list_chat_sessions 的 runtimeState 与 updatedAt 不是写入日志），活写入者期间零写入，连续三次指纹一致后只读重新调用复验；普通只读调用可返回最新正文，不强制 /skills reload。用于“重新加载 skills 看看更新”、reload 后是否生效、注入的是旧正文、哨兵命中但版本落后、另一会话仍在改 SKILL.md、需要知道是哪个会话写的、磁盘 mtime 早于注入记录但内容仍缺失、把写入者误判为 running 会话、复验 PASS 只对旧版本成立；不替代 verify-skill-runtime-binding 的 L1–L3b 路径与注入绑定、skill-update-concurrency-safe 的写入安全、audit-skill-during-live-creation 的活写入者验收。English triggers: injected skill body freshness, reload did not show update, stale injected body, which session wrote SKILL.md, concurrent skill writer, version-bound skill injection, re-invoke after quiescence."
---

# 验证注入正文是否为磁盘最新版本

## 目标与边界

证明本次只读调用注入的 Skill 正文等于当前磁盘版本的正文；不等时，定界注入正文对应哪个旧版本，归因是否有其他会话仍在写入，等静默后重新只读调用复验。输出 L3a 路径、L3b 正文、注入版本、写入者状态、静默与复验证据，判定 PASS latest、UNVERIFIED latest 或 FAIL。

不替代：

- `verify-skill-runtime-binding`：L1 磁盘、L2 根与同名、L3a 路径、L3b 注入记录绑定与 `locate_injection.py`；本 Skill 复用它的结论与脚本。
- `skill-update-concurrency-safe`：备份、最小 Edit、QA 重跑与写入稳定性；本 Skill 不写目标文件。
- `audit-skill-during-live-creation`：活写入者期间的零写入验收与 FINAL/PROVISIONAL 分级。
- `verifier-reecriture-concurrente-paquet-skill`：QA PASS 之后的并发重写认证。
- `extraire-preuves-session-qoder`：会话 JSONL 的原始证据提取；本 Skill 只扫描写入记录与版本定界。

## 何时使用

- 用户说“重新加载 skills 看看更新”“reload 后是否生效”“注入的是不是最新正文”。
- 最新磁盘短语在注入正文中缺失，但旧版本短语仍在。
- 需要说明注入正文对应哪个旧版本，而不是笼统写“旧正文”。
- 另一个会话可能正在改同一个 SKILL.md；需要知道是哪个会话写的。
- `list_chat_sessions` 显示某会话 running，但不能确定它是否写过该文件。
- 复验 PASS 后文件又被改写，需要判断 PASS 对哪个版本成立。
- 用户输入的 `/ skills reload` 带空格，客户端没有执行。

## 不可协商约束

1. **最新以磁盘最后一次写入为准。** 哨兵必须取自该次写入；只取自己上一次写入的短语，只能证明“我的上一版可见”，不能证明“最新版可见”。
2. **mtime 顺序不等于注入内容。** 磁盘写入早于注入记录，或晚于调用，都不能单独证明注入是否包含它；只认注入正文逐字命中。
3. **缺失最新哨兵时先定界版本。** 选 1–2 个版本分界短语（新增表格行、结论句、章节标题），辅以标题行号偏移；报告“注入 = X 版本”，不写“可能是旧正文”。
4. **写入者归因不能只靠 `list_chat_sessions`。** `runtimeState` 与 `updatedAt` 不是写入日志：实际写入者可能是 `ready`，而 `running` 的会话并未写文件。必须扫描候选会话 JSONL 的 Write/Edit 记录，精确匹配路径与时间，才判 CONFIRMED；未命中判 UNKNOWN，不指名。
5. **活写入者期间零写入。** 不整文件重写、不删除、不提交、不回退并发内容；只报告。
6. **复验前要求静默。** 至少 3 次相同 size、mtime、SHA-256（间隔 ≥2 秒）；未静默时不得宣布 PASS latest。
7. **代理不能执行 `/skills reload`。** 可以提示用户输入无空格的 `/skills reload`，但先尝试静默后的只读调用；不要声称已重载。
8. **判定按版本。** L3a PASS 只证明路径；L3b PASS 只对报告中的 size 与 SHA-256 版本成立。文件再变，旧 PASS 失效。

## 步骤

### 0. 固定目标与当前版本

```bash
f="<skill-dir>/SKILL.md"
sha256sum "$f"
stat -c '%s bytes | %y' "$f"
wc -l < "$f"
```

记录预期目录、根（用户级或项目级）、size、mtime、SHA-256 与行数。若两次采样已经不同，先按第 5 步等静默，不要开始调用。

### 1. 从磁盘最后一次写入选哨兵

先确认磁盘“最后一次写入”是谁的内容：自己刚写的，还是并发会话写的。打开当前版本，选 1–2 个“该次写入才出现”的短语：新增章节标题、新增表格行、改写的结论句。用 `grep -n -F` 确认命中行号位于 frontmatter 闭合 `---` 之后；只出现在 description 的短语不会进入注入正文。

同时选 1 个旧版本短语作为下界，用来判断注入是否至少包含旧版本。例：最新哨兵是并发会话新增的结论句，旧哨兵是自己上一版已有的章节标题。

### 2. 只读调用并绑定注入

在最后一次写入之后发起只读调用，args 末尾加唯一绑定标记：

```text
Skill(skill="<skill-name>", args="仅核对 base directory 与最新注入正文；不执行该 Skill 的工作流，不写文件。BINDING=<UTC时间戳>-<4位随机>")
```

用 `verify-skill-runtime-binding` 的脚本定位本次注入记录：

```bash
py -3 "$HOME/.qoder/skills/verify-skill-runtime-binding/scripts/locate_injection.py" \
  --scan-dir "<project-session-dir>" \
  --skill "<skill-name>" \
  --nonce "<BINDING-token>" \
  --sentinel "<latest-sentinel>" --sentinel "<old-sentinel>" \
  --disk-skill-md "<skill-dir>/SKILL.md" \
  --expect-base "<skill-dir>"
```

记录注入记录文件与行号、首行、末行、字符数、每个哨兵的 count，以及调用后的 size、mtime、SHA-256。

- 最新哨兵 present 且调用前后指纹一致：PASS latest，仍要报告版本。
- 最新哨兵 missing，或调用后指纹变化：进入第 3 步。

### 3. 版本定界

不要只说“缺最新内容”。列出当前标题行号，与上一版本（来源会话、备份或上一次读取）对照：

```bash
grep -n '^##\|^###' "<skill-dir>/SKILL.md"
```

定位插入点：若某标题之后的标题统一后移 N 行，新增内容就在该标题与前一个标题之间。例：步骤 8 由 198→199、陷阱 221→222，说明步骤 7 内新增了 1 行；再用该行的唯一短语确认它是否在注入正文中。

用版本分界短语判定注入对应哪个磁盘版本，报告 `size / lines / mtime / SHA-256`。若注入包含旧版本表格行但不含新版本结论句，写“注入 = 19,769 B 版本”，不要写“16:15:38 之前”。

### 4. 归因写入者

先枚举候选会话：

```text
list_chat_sessions(limit=50)
```

记录每个候选的 `runtimeState`、`updatedAt` 与标题，但它们只是候选线索。扫描候选会话 JSONL 中对目标文件的 Write/Edit：

```bash
py -3 -B "$HOME/.qoder/skills/verify-injected-skill-body-freshness/scripts/scan_skill_writers.py" \
  --scan-dir "<project-session-dir>" \
  --target "<skill-dir>/SKILL.md" \
  --include-results
```

需要缩小窗口时加 `--since "<ISO>"` 或 `--until "<ISO>"`；需要机器可读输出时加 `--json`。脚本只读，输出 sessionId、JSONL 行号、时间、工具、old/new 长度与 tool_result 状态；退出码 0 = 有命中，1 = 无命中，2 = 参数或环境错误。

判定：

- **CONFIRMED**：Write/Edit 的 `file_path` 精确等于目标，tool_result 成功，时间与磁盘 mtime 或写入版本对应。报告 sessionId、JSONL 行号与时间。
- **INFERRED**：只有 running、updatedAt、内容引用等间接线索，没有任何写入记录。必须写明“推断，未确认”。
- **UNKNOWN**：没有命中，或目标可能由外部编辑器、其他项目目录的会话改写。不要指名。

`updatedAt` 可能早于文件 mtime；`runtimeState` 也可能在写入后变为 `ready`。两者都不能替代 Write/Edit 记录。

### 5. 等静默

对目标文件连续采样，至少 3 次相同指纹，间隔 ≥2 秒：

```bash
f="<skill-dir>/SKILL.md"
last=""; same=0
for i in $(seq 1 10); do
  cur=$(sha256sum "$f" | cut -d' ' -f1)
  printf '%s %s %s\n' "$(date '+%H:%M:%S')" "$(stat -c '%s' "$f")" "${cur:0:16}"
  if [ "$cur" = "$last" ]; then same=$((same + 1)); else same=0; last="$cur"; fi
  [ "$same" -ge 2 ] && { echo "STABLE"; break; }
  sleep 2
done
```

写入者仍在写时零写入，只报告。会话 `cold` 或 `ready` 都不排除其他写入者；以目标指纹为准。

### 6. 静默后重新只读调用

用新的 BINDING 再调用一次（不必等客户端 reload）：

```text
Skill(skill="<skill-name>", args="仅核对 base directory 与最新注入正文；不执行工作流，不写文件。BINDING=<新UTC时间戳>-<4位随机>")
```

重新运行第 2 步的 `locate_injection.py`，核对最新哨兵、末章节与 `ARGUMENTS:` 尾行，并在调用前后采样指纹。

- 最新哨兵 present、调用前后指纹一致：PASS latest。
- 仍 missing、注入被截断、绑定失败或文件又变：UNVERIFIED latest，写明注入版本与未验证项。
- 只有路径不符或落到别的 Skill：FAIL。

### 7. 报告

```text
Skill : <name>
L3a 路径 : <注入首行>；EQUAL <True|False>
L3b 哨兵 : latest "<phrase>"（磁盘 L<n>）-> <present|missing>
            old    "<phrase>"（磁盘 L<n>）-> <present|missing>
注入版本 : <size>/<lines>/<sha256>/<mtime>；依据 <version-boundary phrases>
磁盘当前 : <size>/<lines>/<sha256>/<mtime>
写入者   : CONFIRMED <session> <jsonl:line> <timestamp> | INFERRED <session> | UNKNOWN
静默     : <3 次一致 | 仍在变化；最后一次变化>
复验     : <新注入记录>；latest <present|missing>；调用前后指纹 <stable|changed>
判定     : PASS latest | UNVERIFIED latest（注入 = <version>）| FAIL <原因>
未验证   : <reload 行为 / 其他写入者 / 外部编辑器 / 截断>
```

## 诊断

| 症状 | 原因 | 动作 |
|---|---|---|
| 最新哨兵 missing，旧哨兵 present | 注入对应旧版本，或写入发生在注入之后 | 按第 3 步定界版本；静默后重新调用 |
| 磁盘 mtime 早于注入记录，但正文仍缺该版本内容 | mtime 不是内容快照时间；注入可能读取更早副本 | 用版本分界短语判断，不用时间排序 |
| 只核对自己上一版写入的哨兵就判 PASS | 证明的是自己的旧版可见 | 改选磁盘最后一次写入的短语，重跑 |
| `list_chat_sessions` 显示 running 会话 | running 只表示会话活跃，不是写入日志 | 扫描 JSONL；不要据此指名 |
| 实际写入者是 ready 会话 | 写入完成后状态已变 ready | 以 Write/Edit 记录与 mtime 为准 |
| 实际写入者 `updatedAt` 早于文件 mtime | updatedAt 不是逐工具调用的时间线 | 仍扫描其 JSONL，匹配 Edit 时间 |
| 扫描无命中 | 路径写法不同、其他项目目录、外部编辑器或已归档 | 用 `--json` 查命中；扩展 scan-dir；无法确认时 UNKNOWN |
| 用户输入 `/ skills reload` | 斜杠与命令之间有空格，未被执行 | 说明后先尝试静默 + 只读调用；需要时请用户输入无空格写法 |
| 最新哨兵 present，但调用后哈希变化 | 调用后又有写入，版本已推进 | 重新采样并再次调用；旧 PASS 只对旧版本成立 |
| 复验 PASS 的 size 已不是当前 size | PASS 绑定到旧版本 | 报告“PASS 版本 = X；当前 = Y”，重新复验 |
| 两个会话同时写 | 并发写入 | 零写入；报告两个写入者与各自区间；不复原 |
| 来源报告说“注入是某时间之前” | 可能差一个写入：注入恰好包含该时间版本 | 查该版本新增行是否在注入正文；用分界短语纠正 |
| 注入正文被截断 | 记录截断或注入截断 | 转 `verify-skill-runtime-binding` 的 L3b 尾行检查；判 UNVERIFIED |
| 哨兵只在 description | frontmatter 不进入注入正文 | 改选正文短语，不判旧正文 |
| 脚本退出 2 | 参数、路径或 scan-dir 错误 | 用绝对路径；先看 `--help` 与 stderr |

## 已验证案例（2026-10-26）

来源会话 `ad5d6df9-0fa2-4717-b34a-76be57e7773e`，读取时 revision 11、14 条消息、`hasMoreBefore: false`。以下为历史快照，不表示当前磁盘。

| 时间（UTC） | 观察 |
|---|---|
| 15:14:33 | 用户要求“重新加载 skills 看看更新”；代理不能执行 `/skills reload` |
| 15:15:40.438 | 第一次只读 `Skill` 调用 |
| 15:15:40.785 | 注入记录 `ad5d6df9.jsonl:246`，`isMeta: true`，12,542 字符；首行 base directory 正确，末行 `ARGUMENTS:` 完整 |
| 15:15:30 / 15:15:38 | 并发会话 `ae97a7bf` 两次 Edit；注入正文包含这两次改动（`JSONL 582 行`、`14:57:09Z` 表格行） |
| 15:16:16 / 15:16:22 / 15:16:26 | 同一会话再三次 Edit：会话 ID 与 15:11Z、结论边界改为已提交 `eeff5e2`、步骤 7 新增 `origin` 分支；注入正文均 missing |
| 15:15:38 | 磁盘 `SKILL.md` 19,769 B / 319 行 / SHA-256 `82a941e6…`；调用后采样 |
| 15:16:25 | 磁盘 20,043 B / 320 行 / SHA-256 `7a1e6ad2…`；再次采样 |
| 15:21:01 | 用户输入 `/ skills reload`（带空格），客户端未执行 |
| 15:21:25.446 | 第二次只读调用注入记录 `ad5d6df9.jsonl:348`，12,708 字符；三处新增全部 present；磁盘稳定在 20,043 B / `7a1e6ad2…` |

写入者归因（本次复核查实）：

- 实际写入者是 `ae97a7bf-2013-4366-b5ed-20d659cc2808`，JSONL 231/236/256/260/264 五次 Edit，时间 15:15:30.741、15:15:38.257、15:16:16.704、15:16:22.245、15:16:26.899，五次 tool_result 均成功；old/new 原文与三处改动逐字对应。
- 来源代理当时把写入者归给 `13d0993e`，理由是它 `running`、`updatedAt` 晚于本会话、且新增内容引用了本会话 ID。该归因错误：当时 `13d0993e` 的 `updatedAt` 是 15:14:57，早于 15:15:38 与 15:16:25 两次写入；实际写入者 `ae97a7bf` 当时是 `ready`。`runtimeState`、`updatedAt` 与内容引用都不是写入证据。
- 来源代理把注入版本说成“16:15:38 之前”，也不准确：注入正文逐字包含 15:15:30 与 15:15:38 两次 Edit 的产物，对应 19,769 B / 16:15:38 版本；它缺的是 15:16:16 之后的三处写入。
- 第二次普通只读调用（没有真实 reload）返回了 20,043 B 版本的最新正文，说明静默后重新调用可以复验；不要把“必须 reload”写成已验证结论。
- 本次复读时（16:27:11 +01:00）案例文件已变为 20,876 B / 325 行 / `4dfdce29…` / mtime 16:22:03，来自 `490230a9` 在 15:21:38–15:22:03 的五次 Edit。因此 15:21 的 PASS 只对 20,043 B 版本成立，当前版本需重新复验。

判定：第一次调用 L3a PASS；L3b 对 19,769 B 版本 PASS，对最新 20,043 B 版本 UNVERIFIED；静默后第二次调用 PASS latest（当时 20,043 B）。用户没有纠正代理，只提出“重新加载”和“继续执行诊断”；上述两处纠正是本次复核发现的。

## 完成检查清单

- [ ] 已记录目标目录、根、size、mtime、SHA-256 与行数。
- [ ] 哨兵取自磁盘最后一次写入，而不是只取自己上一次写入的短语。
- [ ] 已确认哨兵位于正文（frontmatter 闭合之后），并在注入正文逐字核对。
- [ ] 已记录注入记录文件、行号、首末行、字符数与哨兵 count。
- [ ] 最新哨兵缺失时已定界到具体版本（size/行数/mtime/哈希），没有写“可能旧”。
- [ ] 已用 `list_chat_sessions` 只做候选枚举，未据 running 或 updatedAt 指名写入者。
- [ ] 已扫描候选会话 JSONL 的 Write/Edit，匹配精确路径与时间；否则标 UNKNOWN。
- [ ] 活写入者期间零写入，未整文件重写、删除、提交或回退。
- [ ] 复验前至少 3 次指纹一致；未静默时没有宣布 PASS。
- [ ] 静默后用新的 BINDING 重新只读调用，并重跑注入定位脚本。
- [ ] PASS 写明了对应版本；文件再变时声明旧 PASS 失效。
- [ ] 未声称执行 `/skills reload`；需要时提示无空格写法。
- [ ] 报告列出了未验证项（reload 行为、外部编辑器、其他写入者、截断）。

## 资源

- `$HOME/.qoder/skills/verify-injected-skill-body-freshness/scripts/scan_skill_writers.py`：只读扫描会话 JSONL 中对指定 SKILL.md 的 Write/Edit，输出 sessionId、行号、时间、工具、old/new 长度与 tool_result 状态；`--since`、`--until`、`--json`、`--include-results`。
- `verify-skill-runtime-binding`：L1–L3b、注入记录绑定与 `locate_injection.py`；路径和正文的第一层取证以它为准。
- `skill-update-concurrency-safe`：写入稳定性、备份与最小 Edit；本 Skill 不写目标文件。
- `audit-skill-during-live-creation`：活写入者期间的零写入与冷后重跑。
- `verifier-reecriture-concurrente-paquet-skill`：QA PASS 后的并发重写认证。
- `list_chat_sessions`、`read_chat_session`：候选会话枚举与活性字段；不是写入日志。
