---
name: verify-skill-runtime-binding
description: "只读验证 Skill 被移动、复制或安装后，运行时实际解析到的目录是否等于预期位置：按磁盘（新目录存在、旧目录消失）、根与同名（用户级与项目级枚举、项目级遮蔽）、运行时（调用 Skill 后按首行 Base directory for this skill 定位注入消息，不按相邻位置取，再规范化比较）三层取证；新建或刚安装的 Skill 先直接只读调用，失败才提示重载；工具结果只有 Launching skill 不含路径；用量计数、日志、会话技能清单、UI 与静态校验不能替代注入行；代理不能执行 /skills reload 或 /skills list；带空格写法纠正一次后，重复出现不再纠正，改用新 BINDING 复验并报告，不声称已 reload。用于移动后验证、安装后不生效、加载到旧路径、用户级与项目级同名、技能面板滞后、/ skills reload 带空格、base directory 缺失、注入行不紧邻工具结果、路径大小写与分隔符不一致；并核对同一次注入正文逐字包含最后一次写入新增的 1–2 个唯一短语或规则标题，路径与哈希未变不能替代正文已刷新，缺失判 UNVERIFIED。中文触发补充：确认加载的是最新正文、重载后是否生效、注入的是旧正文、内容哨兵、注入记录取证、ARGUMENTS 尾行、会话 ID 混淆、最新 JSONL 是别的会话、要求 /skills list 确认加载结果；English triggers: verify injected skill body, stale skill content after reload, content sentinel, locate Skill injection record in session JSONL, read_chat_session missing injected body, newest JSONL belongs to another session；注入记录取证：read_chat_session 可能不含 isMeta 注入正文，项目最新 .jsonl 可能是并发会话，须按会话 ID 或调用 nonce 绑定 tool_use → tool_result → 注入记录，核对末章节与 ARGUMENTS 尾行排除截断，命中 0 或多文件判 UNVERIFIED"
---

# 验证 Skill 的运行时路径绑定

## 目标与边界

证明当前会话调用某个文件系统安装的 Skill 时，运行时实际解析到的目录等于预期位置，且本次注入正文绑定到被验证的版本（并发改写时用 HEAD 导出、调用前快照或经调用前后哈希固定的 live）。输出 L1、L2、L3a（路径）、L3b（正文）证据与 PASS / FAIL / UNVERIFIED 判定，并记录注入记录在当前会话 JSONL 中的行号与调用绑定关系；明确哪些观察不能替代运行时证据。

不替代：移动或复制流程（本项目项目级 Skill skill-absolute-path-references，仅本项目可见；其他项目可跳过）；位置叙述审计（`relocate-self-documenting-skill`）；磁盘清单与计数（`inventory-installed-skills`）；静态验收（`skill-file-qa`）；提交时检查（`commit-skill-work`）；并发写入保护（`skill-update-concurrency-safe`）；注入正文新鲜度的完整复验（`verify-injected-skill-body-freshness`：版本定界、写入者归因、静默后复调用）；对外发布。

## 何时使用

- Skill 被移动、复制或安装后，用户问“是否生效”“是否出现在列表”。
- 实际加载到了旧路径，或项目级与用户级存在同名副本。
- 用户要求 reload 并验证列表，但代理只能验证运行时解析。
- 用户在 reload 后要求确认“加载的是最新正文”，或被要求执行 `/skills list` 确认加载结果。
- 用户连续多次发送带空格的 `/ skills reload`（面板或列表刷新诉求）：格式纠正一次即可，随后直接做新 `BINDING` 的只读复验。
- 路径正确、调用前后哈希未变，但怀疑运行时注入的是旧正文或注入被截断。
- 注入首行缺失，或路径大小写、分隔符看起来不一致。
- 需要解释为什么 `skill-usage.json`、日志或 UI 不能作为路径证据。
- `read_chat_session` 只返回对话回合，看不到 `Base directory` 注入正文。
- 项目目录中最新修改的 `.jsonl` 属于另一个并发会话，或不确定哪个文件是当前会话。
- 需要把注入正文与本次调用的 args 唯一绑定，排除旧调用、其他会话与助手总结。
- 未执行 reload，但需要判断本次注入是否包含调用前最新磁盘正文；完整并发窗口验证见 `verify-injected-skill-body-freshness`。
- 验证期间 SKILL.md 正被另一会话改写，需要把哨兵与 `--disk-skill-md` 固定到某个确定版本。

## 证据层级（L1 / L2 / L3a / L3b，固定顺序）

| 层 | 问题 | 通过条件 |
|---|---|---|
| L1 磁盘 | 预期目录与 SKILL.md 是否存在；旧目录是否消失 | 预期 SKILL.md 存在；移动场景下旧目录不存在 |
| L2 根与同名 | 条目在哪个根；是否存在同名遮蔽 | 同名副本数已知；预期根明确；遮蔽已报告 |
| L3a 运行时路径 | 当前调用解析到哪个目录 | 注入消息首行存在，规范化后等于预期路径，调用前后文件未变 |
| L3b 注入正文 | 本次注入的正文是否来自被验证版本，且记录属于本次调用 | 注入记录来自当前会话 JSONL，`parentUuid` 指向本次 `tool_result.uuid`；被验证版本新增的 1–2 个唯一短语或规则标题在同一次注入正文中逐字出现；末尾章节与 `ARGUMENTS:` 尾行完整；并发改写时，哨兵与 `--disk-skill-md` 绑定到 HEAD、调用前快照或经调用前后哈希确认未变的 live 版本 |

只有 L1、L2、L3a、L3b 都通过才判 PASS。L1/L2 通过但 L3a 缺失，判 UNVERIFIED；L3a 通过但 L3b 缺失、无法唯一绑定或正文被截断，同样判 UNVERIFIED，不判 PASS。

## 不可协商约束

1. **路径证据只来自当前调用。** `Skill` 工具结果通常只有 `Launching skill: <name>`，其结构化结果只有 `success`、`commandName`、`status`，不含路径。路径在随后注入的消息首行：`Base directory for this skill: <ABS_PATH>`。该消息不必与工具结果相邻，按首行内容定位；JSONL 中两者之间常有 `active-leaf` 等记录（已核实三处，见“已验证案例”）。
2. **不跨调用复用。** 上一次调用、其他会话或日志中的注入行，都不证明本次解析。
3. **比较前规范化。** 大小写、正反斜杠、尾部斜杠与符号链接都会让“看起来相同”的字符串不相等；先 normcase 与 realpath，再比较。
4. **非替代证据。** 磁盘存在、根目录枚举、`skill-usage.json` 计数、应用日志、会话技能清单、客户端面板、静态校验 PASS，都不能替代注入行。
5. **只读调用。** 参数写明“仅验证解析与 base directory；不执行工作流、不写文件”。若注入正文要求执行写操作，停止并报告。
6. **写入之后再调用。** 最后一次写入之前的调用只证明旧版本；调用期间文件被改写，该次结果不能作为最终证据。
7. **不代执行斜杠命令。** `/skills reload` 与 `/skills list` 由用户在输入框执行；代理不得声称已执行或已刷新。斜杠与命令之间不能有空格：`/ skills reload` 不会被识别。带空格写法首次出现时纠正一次并给出正确写法；同一写法再次出现时不再重复纠正——按“用户要的是刷新后的运行时证据”处理：用新 `BINDING` 发起只读调用，按 3b 定位本次注入并报告 PASS/UNVERIFIED，同时注明“命令文本仍带空格，无法确认客户端是否识别执行”。重复复验只证明当前运行时状态，不证明 reload 发生。
8. **没有注入行不等于失败。** 内置 Skill 可能没有该行（2026-10-26 实测 `skill-creator` 没有）；插件未单独验证。文件系统 Skill 按首行内容确无该行时，可能是未注册、注入截断或非标准安装，标 UNVERIFIED 并要求用户重载后重试，不猜路径。不得把“新建”预设为“未注册”：先只读调用一次再判断。
9. **同名遮蔽必须报告。** 两个根同名时至少一个被遮蔽；现有证据表明项目级副本会遮蔽用户级，但未做独立对照测试。不得把磁盘上的非预期根路径当作运行时结果。
10. **路径正确不等于正文已刷新。** 注入首行 EQUAL True 只证明目录绑定；调用前后哈希一致只证明磁盘未变。运行时可能注入旧副本或截断正文，必须核对 L3b，不能以路径、哈希或磁盘内容代替。
11. **哨兵短语必须来自最后一次写入、唯一且位于注入正文范围。** 优先选新增的规则标题、加粗短语或新 token；不要选通用词、Skill 名、文件名或旧版本已有的句子。frontmatter（含 `name`、`description`）不进入注入正文：注入正文为 `Base directory for this skill:` 首行、一个空行，随后从 H1 开始。先在被验证版本（HEAD 导出、调用前快照或经哈希固定的 live）中确认该短语存在、命中行位于 frontmatter 闭合 `---` 之后并记录行号，再到同一次注入正文中逐字查找。只出现在 description 的短语在注入正文中必然 count 0，此时改选正文短语，不得据此判定旧正文或要求重载。最后一次写入若只是删除或改写，选新措辞。复现 frontmatter-only 负向分支时，选正文 0 次的 description 短语，并先用 `SENTINEL_SCOPE` 确认 `body -`；不要在正文逐字复写该短语，否则它会变成正文命中。
12. **注入正文只从当前会话 JSONL 取证。** `read_chat_session` 的对话窗口可能不含 isMeta 注入记录（2026-10-26 实测 85b68db0 返回 6 条消息，无 L191 注入）；项目目录最新的 `.jsonl` 可能是并发会话（同一时刻 `e506f79c` 比当前 `85b68db0` 新）。先由会话 ID 或调用 nonce 唯一确定文件，再按 `tool_use → tool_result → 注入记录` 链绑定；助手总结、其他会话与旧记录都不是证据。
13. **无法唯一绑定就判 UNVERIFIED。** 并发会话使用相同 args 时，在 args 末尾加唯一 `BINDING=<token>`；扫描命中 0 个或多个文件、注入记录 `parentUuid` 不指向本次 `tool_result.uuid`、或存在多条候选时，停止并报告，不按最新文件猜。
14. **并发改写时 PASS 必须绑定版本。** 优先冻结：已提交版本用 `git show HEAD:SKILL.md` 导出；未提交的最新版本在调用前复制到 Skill 目录外的快照，记录 size、mtime、SHA-256。哨兵与 `--disk-skill-md` 都指向该冻结版本。若直接使用 live 文件，必须记录调用前后 size、mtime、SHA-256 并在报告中证明调用窗口内未变；调用后 live 哈希变化时，该结果不算当前版本证据。若同时要求“最新版”结论，转 `verify-injected-skill-body-freshness` 做静默与复调用。

## 步骤

### 0. 确认预期位置

从用户指令或磁盘确认：Skill 名、预期根（用户级或项目级）、预期绝对目录、是否发生移动。记录预期 SKILL.md 的 size、mtime 与 SHA-256。

### 1. L1 磁盘

```bash
test -f "<expected-skill-dir>/SKILL.md" && echo EXPECTED_SKILL_MD EXISTS || echo EXPECTED_SKILL_MD MISSING
sha256sum "<expected-skill-dir>/SKILL.md"
test -d "<old-skill-dir>" && echo OLD_PRESENT || echo OLD_ABSENT
```

预期 SKILL.md 缺失即 FAIL，不再进入运行时层。移动场景下旧目录仍存在，报告移动未完成或存在第二份副本。

### 2. L2 根与同名

优先运行 `inventory-installed-skills` 的只读枚举，取得用户级与项目级计数、同名副本与异常项；计数只取同一次运行。需要最小化检查时：

```bash
find "<user-skills-root>" "<project-skills-root>" -maxdepth 2 -type d -name "<skill-name>" 2>/dev/null
```

- 结果 0 个：未安装或名字不符，判 FAIL 或 UNVERIFIED，不能进入 L3 并宣称 PASS。
- 结果 1 个：记录它属于哪个根。
- 结果 2 个：同名遮蔽，报告两个绝对路径；预期位置必须写明，运行结果落在另一个根即 FAIL。

### 3. L3 运行时

新建或刚安装的 Skill 也直接发起只读调用，不要先等重载：已核实写入后约 41 秒即可解析（2026-10-26，会话 2b9c94c1）。只有调用失败或按首行内容确无注入行时，才提示用户重载。

在最后一次写入之后调用目标 Skill，并在 args 末尾加唯一绑定标记（并发会话存在时必需）：

```text
Skill(skill="<skill-name>", args="仅验证运行时解析、base directory 与注入正文；不要执行该 Skill 的工作流，不要写文件。BINDING=<UTC时间戳>-<4位随机>")
```

记录四样东西：

1. 绑定标记 `BINDING=<token>` 与完整 args 原文。
2. 工具结果原文（通常只有 `Launching skill: <name>`，没有路径）。
3. 注入消息首行，逐字复制，不凭记忆重写；不要用 `read_chat_session` 的对话窗口代替，它可能不含 isMeta 注入记录。
4. 调用前后目标 SKILL.md 的 SHA-256。

工具结果后的第一条记录不一定是注入消息；两者之间可能夹有 `active-leaf` 等记录。按 3b 的记录链定位，不要把相邻消息当作注入行，也不要因此判 UNVERIFIED。

`skill-usage.json` 的 usageCount 会因调用增加，但它只证明调用发生，不证明解析到哪里。

### 3b. 注入正文取证与哨兵

写入后从被验证版本选 1–2 个“该次写入才出现”的短语，先在磁盘确认并记录行号。无并发改写时可直接用 live 文件；有并发改写时优先按下面的快照/HEAD 导出冻结版本，若确认调用窗口内 live 未变，也可用 live 并记录调用前后哈希：

```bash
grep -n -F "<sentinel-phrase>" "<verified-skill-md>"
```

确认命中行号大于 frontmatter 闭合 `---` 的行号（本文件当前为 L4）。命中只在 description 或其他 frontmatter 行，说明哨兵取错范围：改选正文短语后重跑，不要求重载。脚本的 `SENTINEL_SCOPE`（需提供 `--disk-skill-md`）会分别列出正文与 frontmatter 命中行：短语只在 frontmatter 时脚本报 `sentinel only in frontmatter`；短语在正文也有命中、但注入正文 count 0 时脚本报 `sentinel missing`。两者都先改选哨兵。

复现 frontmatter-only 负向分支（断言 `sentinel only in frontmatter`）时，改用正文 0 次的 description 短语（如 English triggers 段中的一条），先用 `SENTINEL_SCOPE` 确认 `body -`；不要在正文逐字复写该短语，否则它会变成正文命中，脚本改报 `sentinel missing`。revision 31 案例中的旧哨兵即因被案例复写而失效。

**并发改写时冻结被验证版本。** 验证期间可能被另一会话改写；不要在会变动的 live 文件上边读边选哨兵。已提交版本用 HEAD 导出，未提交的最新版本在调用前复制到 Skill 目录外的快照：

```bash
git -C "<skill-dir>" rev-parse HEAD
git -C "<skill-dir>" show HEAD:SKILL.md > "<tmp>/SKILL.head.md"
cp "<expected-skill-dir>/SKILL.md" "<tmp>/SKILL.precall.md"
sha256sum "<tmp>/SKILL.head.md" "<tmp>/SKILL.precall.md"
stat -c '%s %y' "<tmp>/SKILL.precall.md"
grep -n -F "<head-sentinel>" "<tmp>/SKILL.head.md"
grep -n -F "<fresh-sentinel>" "<tmp>/SKILL.precall.md"
```

- 验证已提交版本时，哨兵、`SENTINEL_SCOPE` 与 `--disk-skill-md` 全部指向 HEAD 导出。
- 验证“调用前最新磁盘正文”时，指向调用前快照，并记录其 size、mtime、SHA-256；快照必须放在 Skill 目录外，避免成为新的 live 文件。
- 选两个哨兵：一个 HEAD 版本已有的稳定短语（证明注入至少包含 HEAD），一个只在被验证版本新增的短语（证明注入包含该版本）。
- 磁盘行号以被验证文件为准，可能不同于 live 文件；报告写明是 HEAD、快照还是 live。
- 用 live 时必须给出调用前与调用后的 size 与 SHA-256，二者一致才算同一版本；不一致就改冻结版本重跑。
- 案例中的短语一旦被正文复写，就不再是“该版本独有”，换新短语，不要复用。

**历史注入回放与版本重建。** 回放已提交版本的历史注入时，先以历史采样的 size 与 SHA-256 判断当时工作区行尾，不要按当前 `core.autocrlf` 猜测。若历史工作区是 CRLF 而 `git show "<commit>:SKILL.md"` 导出的是 LF blob，直接拿导出文件作 `--disk-skill-md` 会因 size 与末行校验不符而失败：

```bash
git -C "<skill-dir>" show "<commit>:SKILL.md" > "<tmp>/SKILL.blob.md"
py -3 -c 'import hashlib,sys
b=open(sys.argv[1],"rb").read()
assert b.count(b"\r\n")==0, "blob already CRLF"
c=b.replace(b"\n",b"\r\n")
open(sys.argv[2],"wb").write(c)
print("BLOB",len(b),"WORKTREE",len(c),"LF",b.count(b"\n"))
print("SHA256",hashlib.sha256(c).hexdigest())' "<tmp>/SKILL.blob.md" "<tmp>/SKILL.worktree.md"
test "$(stat -c %s "<tmp>/SKILL.worktree.md")" = "<historical-size>"
test "$(sha256sum "<tmp>/SKILL.worktree.md" | cut -d' ' -f1)" = "<historical-sha256>"
```

- 历史采样就是 LF 时直接用导出文件，不换算；blob 已含 CRLF 时不要二次转换。
- 换算后的 size 与 SHA-256 必须等于历史采样值；不等判 UNVERIFIED，不调整哨兵去迁就。
- `--disk-skill-md` 必须指向该重建副本，不能指向当前 live；哨兵唯一性与行号都以副本为准。
- 回放旧注入时用旧会话的 `--jsonl` 与当次 nonce/args，不新增 `Skill` 调用，也不按最新文件猜；`RESULT PASS` 只证明历史注入与被重建版本一致，不证明当前 live 或 reload 状态。

不要按 mtime 选 JSONL，也不要用 `read_chat_session` 的对话窗口或助手总结代替注入原文。用只读脚本在当前会话 JSONL 中按记录链定位：

```bash
py -3 "<skill-dir>/scripts/locate_injection.py" \
  --scan-dir "<project-session-dir>" \
  --skill "<skill-name>" \
  --nonce "<token>" \
  --sentinel "<phrase-1>" --sentinel "<phrase-2>" \
  --disk-skill-md "<verified-skill-md>" \
  --expect-base "<expected-skill-dir>"
```

已有会话文件时可把 `--scan-dir` 换成 `--jsonl "<file>.jsonl"`。`<verified-skill-md>` 是 HEAD 导出、调用前快照或 live 文件，必须与选哨兵的文件是同一个。脚本只读，要求：

- `Skill` tool_use 的 args 含唯一 nonce；扫描命中恰好一个文件、一个调用。
- `tool_result.tool_use_id` 等于该 tool_use id，注入记录 `isMeta` 为 true 且 `parentUuid` 等于 `tool_result.uuid`。
- 注入正文以被验证版本的最后一个 `## ` 章节和 `ARGUMENTS: <完整 args>` 结尾；缺尾、停在中间或字符数明显偏小都判截断。
- 每个哨兵短语在注入正文全文逐字出现；只在磁盘、`Read` 回显、校验输出或计划文本中出现不算。
- `RESULT PASS` 才继续；`RESULT FAIL` 表示路径不符；`RESULT UNVERIFIED` 表示找不到、0/多命中、绑定失败、截断或哨兵缺失，请用户输入无空格的 `/skills reload` 后重试。

脚本不可用时，用 inline Python 按 `tool_use.id → tool_result.uuid → injection.parentUuid` 查找，禁止用最新文件；无法唯一绑定判 UNVERIFIED。不要沿用上一版的哨兵，每次从被验证版本重新选。

### 3c. 未 reload 的正文新鲜度（可选观测）

用户没有执行 reload、但要求判断“注入的是不是调用前最新正文”时，在 3b 之后追加这一步。它只产出单次观测，不证明 reload 语义：

1. 调用前记录 live SKILL.md 的 size、mtime、SHA-256，并复制到 Skill 目录外的快照（第 3b 的 `SKILL.precall.md`）。
2. 从快照选一个“调用前最新写入才出现”的短语，确认它在正文且 `SENTINEL_SCOPE` 为 `body`，同时保留一个 HEAD 稳定短语作下界。
3. 发起带新 nonce 的只读调用，按 3b 定位注入记录，记录本次与上一次注入的字符数（仅辅助）。
4. 核对新版本哨兵 present、HEAD 哨兵 present、`ARGUMENTS:` 尾行完整；调用后再次采样 live 哈希。
5. 只有“新版本哨兵 present + 版本边界清楚 + 调用前后 live 哈希一致”才写 `FRESHNESS OBSERVED`；否则写 `UNVERIFIED (freshness)`，不写“已刷新”。

同一会话无 reload 的只读调用曾注入调用前最新磁盘正文（2026-10-26，15:07Z→15:28Z，见案例），但这是单一会话、无对照 reload 的观测。并发写入窗口、版本定界与写入者归因转 `verify-injected-skill-body-freshness`；不得据此声称 `/skills reload` 已生效或客户端已刷新。

### 4. 规范化比较

把注入首行中的路径原文作为 observed，预期目录作为 expected：

```bash
py -3 -c 'import os,sys
o=os.path.normcase(os.path.realpath(sys.argv[1]))
e=os.path.normcase(os.path.realpath(sys.argv[2]))
print("OBSERVED",o)
print("EXPECTED",e)
print("EQUAL",o==e)' \
"<observed-path>" "<expected-skill-dir>"
```

再判断落在哪个根：

```bash
py -3 -c 'import os,sys
p=os.path.normcase(os.path.realpath(sys.argv[1]))
for label,root in (("USER",sys.argv[2]),("PROJECT",sys.argv[3])):
    r=os.path.normcase(os.path.realpath(root))
    print(label, p==r or p.startswith(r+os.sep))' \
"<observed-path>" "<user-skills-root>" "<project-skills-root>"
```

`EQUAL True`、落在预期根、哈希未变，且 L3b 的绑定、哨兵与尾行均通过，才具备 PASS 条件。`EQUAL False` 时同时打印两个规范化值，先排除大小写、斜杠与尾斜杠差异，再判 FAIL。

### 5. 判定

| 判定 | 条件 |
|---|---|
| PASS | L1 通过；L2 同名状态已知且无意外遮蔽；L3a 注入首行存在且 EQUAL True；L3b 注入记录来自当前会话 JSONL、与本次调用绑定、末尾章节与 `ARGUMENTS:` 尾行完整、被验证版本的哨兵短语逐字 present；预期根匹配；调用前后 live 哈希一致；并发改写时哨兵与脚本绑定到 HEAD、快照或经调用前后哈希确认未变的 live 版本 |
| FAIL | 注入路径指向旧位置、另一个根或无关目录；预期目录缺失；同名遮蔽导致落到非预期根 |
| UNVERIFIED | 调用失败、Skill 未注册、按首行内容找不到注入消息、注入被截断、注入记录无法唯一绑定、0/多文件命中、L3b 哨兵缺失或无法取得正文全文、内置 Skill 无该行、调用期间文件被改写、哨兵或 `--disk-skill-md` 指向的版本与报告版本不一致、无法确认规范化结果 |

路径正确但 L3b 缺失、绑定失败或正文被截断时判 UNVERIFIED，不判 FAIL：现有证据无法区分“运行时缓存旧正文”与“注入截断”。报告必须写出实际观测值、预期值、注入记录行号、哨兵短语与未验证项；不得用“应该已生效”或“列表里有”替代。

## 非替代证据

| 观察 | 能证明 | 为什么不够 |
|---|---|---|
| `Launching skill: <name>` | 运行时接受了调用 | 不含路径 |
| 结构化结果的 success / commandName / status | 加载状态 | 不含路径 |
| `skill-usage.json` 的 usageCount 与 lastUsedAt | 发生过调用 | 不记录解析目录；字段只有计数与时间 |
| 应用日志或 session JSONL 中的注入行 | 某次会话、某个时刻 | 可能来自其他会话或旧路径，不是当前调用 |
| 当前会话技能清单 | 名称可发现；会话内会刷新（已核实新建后出现） | 只有名字，没有绝对路径，不证明本次解析 |
| 客户端面板或侧边栏 | 展示状态 | 客户端缓存；代理既不能读也不能刷新 |
| 两个 skills 根的磁盘枚举 | 安装位置 | 静态布局；运行时可能被同名遮蔽 |
| 注入首行 EQUAL True | 目录绑定正确 | 不证明注入正文是最后一次写入的版本 |
| 调用前后 SKILL.md 哈希一致 | 磁盘文件未变 | 不证明运行时注入的正文已刷新 |
| 被验证版本（HEAD 导出、调用前快照或经哈希固定的 live）含新短语 | 该版本存在 | 不证明本次注入包含该短语 |
| 调用前快照的 size / mtime / SHA-256 | 冻结了某一版本 | 快照存在不等于运行时注入了它 |
| 调用后 live 哈希变化 | 期间发生了并发改写 | 不能把该次调用算作当前 live 版本的证据 |
| `read_chat_session` 的对话窗口 | 对话回合 | 可能不含 isMeta 注入记录（实测 6 条消息无注入） |
| 项目目录最新的 `.jsonl` | mtime 最新 | 可能是并发会话（`e506f79c` 比 `85b68db0` 新） |
| 助手总结中的注入首行或哨兵 | 模型曾读过 | 不是注入原文；必须回到 JSONL |
| 注入正文字符数 | 传输规模 | 字符数不等于磁盘字节数，不能直接比较；也不能用字符数推断版本 |
| `skill-file-qa` RESULT PASS | 结构与引用合法 | 不检查运行时解析 |

## 诊断

| 症状 | 原因 | 动作 |
|---|---|---|
| 工具结果只有 `Launching skill` | 设计如此 | 按首行内容定位注入消息，不要在工具结果里找路径 |
| 工具结果后第一条记录不是 `Base directory` | 记录之间夹有 `active-leaf` 等消息；JSONL 记录与客户端消息流不是一一对应 | 继续按首行内容查找；不取相邻消息，不据此判 UNVERIFIED |
| 新建或刚安装的 Skill 立即调用 | 同会话可能已可解析（写入后约 41 秒实测） | 先只读调用；成功即取证；失败或确无注入行才提示重载 |
| 文件系统 Skill 按内容确无注入消息 | 未注册、注入截断或非标准安装 | 标 UNVERIFIED；请用户输入无空格的 `/skills reload` 后重试 |
| 内置或插件 Skill 没有注入首行 | 内置不保证该行 | 内置已实测无该行；标 UNVERIFIED 或 N/A，不判 FAIL，不猜路径 |
| 注入路径仍是旧目录 | 运行时索引未更新 | 判 FAIL；请用户重载后重试，不宣称已刷新 |
| 磁盘看到两个同名目录 | 项目级遮蔽用户级 | 报告两个路径；预期根必须明确；结果与预期根不符即 FAIL |
| 两个路径“看起来一样”但 EQUAL False | 大小写、正反斜杠、尾斜杠或 realpath 差异 | 打印规范化值逐项比较 |
| 调用后 live 哈希变化 | 调用期间被并发改写 | 该次调用只对旧版本成立；报告“PASS 版本 = X；当前 = Y”，需要最新版结论时转 `verify-injected-skill-body-freshness` |
| 调用发生在最后一次写入之前 | 证明的是旧内容 | 写入后重新调用，不复用旧结果 |
| 验证期间 live 文件继续变化，哨兵行号漂移 | 在会变动的文件上边读边选哨兵 | 改用 HEAD 导出或调用前快照；哨兵与 `--disk-skill-md` 同指该版本 |
| 哨兵在 live 命中，注入 missing，稍后 live 也变了 | 哨兵与脚本指向不同版本，或选择窗口跨越了写入 | 冻结 HEAD/快照后重跑；不判旧正文，也不直接判 FAIL |
| 无 reload 但注入含调用前最新正文 | 单次只读调用恰好读取了最新磁盘版本 | 写 `FRESHNESS OBSERVED`（单会话观测），不写“reload 已生效”；完整并发窗口验证转 `verify-injected-skill-body-freshness` |
| 案例短语不再独有 | 案例正文复写了该短语 | 换新短语；不要复用案例短语做版本分界 |
| usageCount 增加但没有注入行 | 计数不是路径证据 | 标 UNVERIFIED，继续找注入行 |
| 首次收到 `/ skills reload` | 斜杠与命令之间有空格 | 纠正一次并给出 `/skills reload`；不代执行 |
| 同一带空格写法再次出现 | 用户要的是刷新后的运行时证据，而不是第二次格式纠正 | 停止纠正；用新 `BINDING` 复验 L3a/L3b 并报告，注明无法确认客户端是否执行 |
| UI 仍显示旧路径但 EQUAL True | 客户端展示层缓存 | 报告运行时已绑定；面板刷新未由代理验证 |
| 日志里有注入行但当前调用没有 | 日志含其他会话或旧记录 | 只信当前调用的注入消息 |
| 路径 EQUAL True、哈希未变，但注入正文没有新短语 | 运行时注入旧副本或正文被截断 | 判 UNVERIFIED；请用户输入无空格 `/skills reload` 后重试，不用路径代替 |
| reload 后只报告 EQUAL True | 模板缺少正文项 | 增加 L3b，报告短语、磁盘行号与 present/missing |
| 注入正文只读到开头 | 正文长、记录截断或注入截断 | 在全文检索哨兵；无法取得全文则 UNVERIFIED |
| 哨兵短语在旧版本也有 | 选了通用词或旧句 | 改选最后一次写入新增的唯一短语，先核对磁盘行号 |
| 哨兵 count 0，但磁盘命中只在 L3 description | 选了 frontmatter 中的短语；注入正文不含 YAML | 改选正文（frontmatter 闭合之后）新增短语并重跑脚本；不据此判旧正文或要求 reload |
| 断言 `sentinel only in frontmatter` 却得到 `sentinel missing` | 候选短语已在正文出现（常见于案例逐字复写） | 用 `SENTINEL_SCOPE` 确认 `body` 非空；改选正文 0 次的 description 短语，不修改脚本 |
| `read_chat_session` 看不到 `Base directory` 或注入正文 | 注入记录是 isMeta，对话窗口只含对话回合 | 用脚本回查当前会话 JSONL，不把窗口当证据 |
| 项目目录最新 `.jsonl` 不是当前会话 | 并发会话同时写入 | 用会话 ID 或 nonce 定位，不按 mtime |
| 多个 JSONL 都命中同一调用 | 并发或重复调用 | 用唯一 nonce；0/多命中判 UNVERIFIED |
| 注入正文比磁盘小很多 | 字符数 vs 字节数；或截断 | 长度只作辅助；检查末章节与 `ARGUMENTS:` 尾行 |
| `git show <commit>:SKILL.md` 比历史工作区小 | 仓库以 LF 存 blob，Windows 工作区按 `core.autocrlf=true` 检出为 CRLF（每行 +1 B） | 按 LF→CRLF 重建当时字节，核对 size 与 SHA-256 等于历史采样值，再作 `--disk-skill-md` 回放；不要用 LF 导出直接判哨兵缺失或截断 |
| 注入缺 `ARGUMENTS:` 尾行 | 截断、无 args 或非标准注入 | 有 args 时尾行必须匹配；缺失判 UNVERIFIED |
| 脚本报 `INJECTION NOT FOUND` | `parentUuid` 链不匹配、文件错误或未注册 | 检查 `tool_result` 与 `sessionId`，不改用最新文件 |
| 被要求执行 `/skills list` | 客户端命令，代理不能执行 | 说明后改用 L3a + L3b 取证，不声称已执行 |

## 已验证案例（2026-10-26/27）

来源会话 42a40382：

- 工具结果只有 `Launching skill: skill-absolute-path-references`（JSONL:480），结构化结果只有 success、commandName、status。
- 注入消息首行为 `Base directory for this skill: C:\Users\Administrateur\Desktop\IMAM8MAHDI\.qoder\skills\skill-absolute-path-references`（JSONL:482）；工具结果 480 与注入 482 之间夹有 481 `active-leaf`。

来源会话 1ee3848f 的“验证运行时绑定”回合：

- 规范化比较 EQUAL True；项目级 True、用户级 False；调用前后 SKILL.md 15,199 B、SHA-256 `c9b7f194…681320` 一致；usageCount 3→4 仅作调用辅助证据；判定 PASS。

本次实测（2026-10-26）：

- 用户级 `inventory-installed-skills` 的注入首行为 `Base directory for this skill: C:\Users\Administrateur\.qoder\skills\inventory-installed-skills`。
- 内置 `skill-creator` 的注入没有该首行。
- 42a40382 JSONL:316 的用户输入 `/ skills reload` 与 JSONL:320 的回复：斜杠与命令之间有空格时不被识别，代理也不能代执行。

本 Skill 自身（用户级，2026-10-26）：

- 创建会话 2b9c94c1 写入并完成 L3（JSONL:113/142/152/153），1ee3848f 最终报告 PASS（JSONL:302）：创建版本 13,262 B、SHA-256 `428ae219…eedea892`（编辑前）；注入首行 `Base directory for this skill: C:\Users\Administrateur\.qoder\skills\verify-skill-runtime-binding`；EQUAL True；USER True、PROJECT False；usageCount 1→2。
- 创建后未重载即可解析：13:02:27Z 写入；13:02:46Z `skill_listing` 已含该 Skill；13:03:08Z 调用成功（约 41 秒）；1ee3848f 13:03:49Z 跨会话同样直接加载（JSONL:286/288）。
- 注入消息不与工具结果相邻：2b9c94c1 144→145（`active-leaf`）→146；1ee3848f 286→287→288；与 42a40382 合计三处。三处区间均无 `<system-reminder>`，故按首行内容定位；system-reminder 插入未核实，不写入规则。

来源会话 a48efc65（2026-10-26，revision 27）：

- 14:33:43Z 用户执行 `/skills reload`（代理不能代执行）；14:34:54Z 要求执行 `/skills list` 确认加载结果；代理说明不能执行，改用本 Skill 的运行时绑定验证。
- JSONL 253 `Skill(inventory-installed-skills)` 14:36:22.185Z；255 `Launching skill: inventory-installed-skills`；257 注入首行为 `Base directory for this skill: C:\Users\Administrateur\.qoder\skills\inventory-installed-skills`，同一正文逐字含规则 6/7/8 标题 `无早期快照时自证稳定`、`快照路径唯一`、`活树异常可瞬变`。
- JSONL 263：EQUAL True、USER True、PROJECT False；目标 SKILL.md 11,330 B、SHA-256 `8a42a7aa…` 调用前后一致。JSONL 268 报告 PASS，并在模板外补充“运行时注入的正文已包含更新后的规则 6/7/8，确认加载的是最终合并版”。
- 目标版本最后一次写入为 15:25:47+01:00（11,330 B / `8a42a7aa…`）。该回合说明：路径与哈希之外，正文短语是确认最终版已注入的直接证据；而当时模板没有该项，结论依赖模板外补充。

未验证：`/skills reload` 的实际刷新行为、客户端面板滞后机制、插件 Skill 的注入形式、所有文件系统 Skill 是否都注入该行。正文新鲜度：2026-10-26 同一会话 15:07Z→15:28Z（14,643→17,273 字符，未执行 reload）显示只读调用注入了调用前最新磁盘版本（32,408 B，调用时未暂存）；这是单一会话、无对照 reload 的观测，完整并发窗口验证见 `verify-injected-skill-body-freshness`。

来源会话 85b68db0 revision 12（2026-10-26；上一版本，`hasMoreBefore: false`）：

- 14:42:04.639Z `Skill` 调用（JSONL 187，tool_use id `call_00_qSygRc80UZ0p7oFxiJnc5423`，args 为只读验证）；189 `Launching skill` tool_result；190 `active-leaf`；191 注入 `isMeta: true`，14:42:04.854Z，正文 10,789 字符。
- 191 首行为 `Base directory for this skill: C:\Users\Administrateur\.qoder\skills\verify-skill-runtime-binding`；末行为 `ARGUMENTS: 仅验证运行时解析、base directory 与注入正文；不要执行该 Skill 的工作流，不要写文件。`；`路径正确不等于正文已刷新` 与 `注入正文哨兵` 各出现 2 次；判定 PASS。
- 注入记录 191 的 `parentUuid` 等于 189 的 `uuid`；189 的 `tool_use_id` 等于 187 的 tool_use id；该链是脚本绑定的依据。
- 同一时刻项目目录最新的 JSONL 是 `e506f79c`（另一并发会话），当前会话文件是 `85b68db0`；按 mtime 会选错。
- 回读 `read_chat_session(85b68db0, turnLimit=20)` 返回 6 条对话消息，不含 L191 注入；注入正文只能从 JSONL 取得。
- 来源扫描按短语命中 7 条，其中 L71（计划文本）、L158（Read 回显）、L181（校验输出）是假阳性；必须按 `Base directory`、`isMeta` 与调用链过滤。
- 磁盘 21,244 B / SHA-256 `0ac073c6…` 调用前后一致；EQUAL True；USER True；PROJECT False。
- a48efc65 的 253→255→257 为同一记录链（257 的 `parentUuid` = 255 的 `uuid`），脚本已作为第二个正例。

同一会话 revision 31（2026-10-26，28,204 B 版本）：

- 15:07:01.250Z 调用（JSONL 571，args 含 `BINDING=20261026T1607Z-4f2a`）→ 573 `tool_result`（uuid `6fc8d9ec…`）→ 575 注入（`isMeta: true`，14,643 字符；首行正确、`ARGUMENTS:` 尾行匹配、`TRUNCATION False`）。
- 首轮哨兵选了 `注入记录取证`：当时磁盘（28,204 B 版本）只在 L3（description/frontmatter）出现，注入正文 count 0，脚本 `RESULT UNVERIFIED`、exit 1。这是哨兵范围错误，不是旧正文。**本条案例写入正文后（写入时 L269），该短语在正文也命中；现在按本案例复跑旧注入 85b68db0 L575 只会得到 `sentinel missing`（`SENTINEL_SCOPE` body 非空），不再是 `sentinel only in frontmatter`。**
- 复测改用正文 L103 `注入正文取证与哨兵` 与 L52 `无法唯一绑定就判 UNVERIFIED`，各 count 1，`RESULT PASS`、exit 0。
- 2026-10-26 复验（当时 30,659 B 磁盘 + 上述旧注入）：description-only 短语（English triggers 段）→ `SENTINEL_SCOPE` body `-` / frontmatter [3]，`sentinel only in frontmatter`，exit 1；正文两短语 → count 1，`RESULT PASS`，exit 0。复现该负向分支须另选正文 0 次的 description 短语，不要复用本条旧哨兵。
- 注入正文前两行为 `Base directory…` 与空行，第三行为 H1 `# 验证 Skill 的运行时路径绑定`；frontmatter 的 `name`/`description` 不进入注入正文（本回合按 0/1/1 逐条核实）。
- 磁盘 28,204 B（LF）/ SHA-256 `c9e8ee7c…`；EQUAL True；USER True；PROJECT False。

来源会话 85b68db0 的无 reload 正文新鲜度观测（2026-10-26，revision 32）：

- 15:07:01.250Z 调用（JSONL 571，`BINDING=20261026T1607Z-4f2a`）→ 573 `tool_result`（uuid `6fc8d9ec…`）→ 575 注入（`isMeta: true`，14,643 字符），对应 28,204 B 版本。
- 15:27:31.034Z 调用前采样（JSONL 863）：live SKILL.md 32,408 B / SHA-256 `e46b8a92…` / mtime 16:27:00.310+01:00；`git status` 为 `M SKILL.md`，HEAD `bdf775b`（16:22:41+01:00）。
- 15:27:53Z 对 HEAD 导出 grep（JSONL 869，行号为 `bdf775b` 版本）：`SENTINEL_SCOPE` 命中 L111、L317；`28,204 B 版本` 命中 0。后者是未提交 32,408 B 版本新增的正文短语，可作版本分界。
- 15:28:13.649Z 再次只读调用（JSONL 873，`BINDING=20261026T1531Z-7c3e`）→ 875 `tool_result`（uuid `6fc144de-65c6-43d0-93e8-c42ba9d044c3`）→ 877 注入（`isMeta: true`，17,273 字符）。
- 15:28:27Z 以 live SKILL.md 作 `--disk-skill-md` 跑脚本（JSONL 883，行号为 32,408 B 版本）：`SENTINEL_SCOPE` 正文命中 [50,111,113,217,272,274,307,322]、count 8；`当时磁盘（28,204 B 版本）` 正文 L272、count 1；`BINDING` 两项 True、`TRUNCATION False`、`ARGUMENTS:` 尾行匹配、`RESULT PASS`、exit 0（JSONL 885）。扫描 173 个 JSONL，命中 1 个文件、1 个调用。
- 调用前后 live 均为 32,408 B / `e46b8a92…`（JSONL 863/891），mtime 不变，`DISK_CHARS 17,846`；真实用户文本在 L560–880 之间没有 `/skills reload`（L320 是压缩摘要，不是用户命令）。
- 该版本随后以 `70ccdd9`（16:31:09+01:00）提交：blob 32,080 B（LF）/ worktree 32,408 B（CRLF）；`bdf775b:SKILL.md` 中 `28,204 B 版本` 命中 0，`70ccdd9:SKILL.md` 命中 1。说明调用时注入的是调用前最新、当时未提交的 live 正文。
- 限制：单一会话、无对照 reload；调用窗口内无并发写入（前后哈希一致），但该版本由另一会话写入。字符数只作辅助，版本判断依据是版本分界短语。不能据此断言 reload 语义或所有 Skill 都按调用读取最新磁盘正文；完整并发窗口验证见 `verify-injected-skill-body-freshness`。`当时磁盘（28,204 B 版本）` 已被本条与上一条案例复写，不再独有，后续换新哨兵。

来源会话 c6aa9268（2026-10-26/27，revision 140，`hasMoreBefore: true`）：

- 23:45:26.542Z（JSONL 752）用户“输入 /skills reload 刷新面板”；代理说明不能代执行。23:45:39.312Z、23:45:48.578Z、23:45:56.144Z（JSONL 761/770/779）用户连续三次发送 `/ skills reload`（斜杠后带空格）。
- 761 与 770 之后的两轮回复只重复“斜杠后有空格、不会被识别”，未发起任何工具调用（761–779 之间唯一的 tool_use 是 783 的 Bash 预调用哈希）。
- 第三次（779）之后改用新 `BINDING=20261026T2346Z-30770` 复验：787 `tool_use`（`call_00_ET_aOmYjCp927SHYK973tMD0281`）→ 789 `tool_result`（uuid `36af8bf7…`）→ 791 注入（`isMeta: true`，9,606 字符，`parentUuid` = 789 uuid）。
- 791 首行为 `Base directory for this skill: C:\Users\Administrateur\.qoder\skills\auditer-couverture-skill-avant-creation`；`EQUAL True`、USER True / PROJECT False；末行为 `ARGUMENTS: … BINDING=20261026T2346Z-30770`；哨兵「指纹未稳不定案」（正文 L38）与「来源断言独立复跑」（L41）各 count 1；`TRUNCATION False`；`RESULT PASS`、exit 0。
- 调用前后目标 SKILL.md 均 18,568 B / SHA-256 `4804c25b…b20038`，mtime `00:40:13 +0100` 未变；本次注入 9,606 字符与刷新前 L727 注入相同，说明运行时状态未变，不证明客户端识别并执行了带空格命令。
- 教训：首次纠正后同一写法再次出现时，再纠正一次没有任何证据产出；应直接改用复验并注明“无法确认客户端是否执行”。

## 报告模板

```text
Skill : <name>
预期 : <expected-skill-dir>（<user|project> 根）
L1 磁盘 : SKILL.md <exists|missing>；旧目录 <absent|present>
L2 根 : 同名副本 N 个；<root>；遮蔽 <yes|no>
L3 工具结果 : <verbatim，通常只有 Launching skill>
L3 注入首行 : <verbatim first line>
L3 注入记录 : <session>.jsonl:<line> isMeta <ts> chars <n>；绑定 <yes|no>；尾行 <ok|missing>
L3 取证 : <script RESULT>；候选文件 <n>；末章节 <present|missing>
L3 内容哨兵 : "<phrase>"（<HEAD|快照|live> 正文 L<n>，非 frontmatter） -> <present|missing>；可选第二条
L3 版本 : <HEAD:commit|precall-snapshot|live> <size> <sha256>；调用后 <same|changed>
L3 新鲜度 : prior <chars> -> current <chars>；new-version sentinel <present|missing>；reload <no|yes|unknown>；<FRESHNESS OBSERVED|UNVERIFIED (freshness)|n/a>
比较 : OBSERVED <normalized>；EXPECTED <normalized>；EQUAL <True|False>
范围 : USER <True|False>；PROJECT <True|False>
哈希 : <size> <sha256 before> -> <after>
辅助 : usageCount <before> -> <after>（不是路径证据）
判定 : <PASS|FAIL|UNVERIFIED>
未验证 : <reload 行为 / 面板刷新 / 其他>
```

## 完成检查清单

- [ ] 已确认预期目录、预期根与最后一次写入时间。
- [ ] L1 已记录 SKILL.md 存在性与哈希，旧目录状态已报告。
- [ ] L2 已用同一次枚举确认同名副本数与所在根。
- [ ] L3 在最后一次写入之后调用，参数限定只读；新建 Skill 也先直接调用，未预设需重载。
- [ ] 已按首行内容定位注入消息，未取工具结果后的第一条记录。
- [ ] 已逐字记录注入消息首行，未把工具结果当路径。
- [ ] 已从被验证版本选取 1–2 个唯一短语，并确认磁盘行号位于正文（frontmatter 闭合之后），未选只出现在 description 的短语。
- [ ] 已记录被验证版本的来源（HEAD / 调用前快照 / live）与 size、SHA-256；哨兵与 `--disk-skill-md` 同指该版本。
- [ ] 使用 live 时已证明调用前后 size 与 SHA-256 一致；不一致时改冻结版本重跑。
- [ ] 复现 frontmatter-only 负向分支时，已确认候选短语的 `SENTINEL_SCOPE` 为 `body -`，且未在正文逐字复写该短语。
- [ ] 已在同一次注入正文全文逐字核对短语，记录 present/missing，未用路径、哈希或磁盘内容代替。
- [ ] 已显式确定当前会话 JSONL，未按 mtime 取最新文件。
- [ ] 已用 nonce 或 args 将注入记录绑定到本次 `tool_use → tool_result` 链；0/多命中时判 UNVERIFIED。
- [ ] 已核对注入末章节与 `ARGUMENTS:` 尾行，未用字符数与磁盘字节数直接比较。
- [ ] 来源会话证据已回查其 JSONL，未引用助手总结。
- [ ] 已用 normcase 与 realpath 比较，并判断落在哪个根。
- [ ] 调用前后哈希一致，或已说明并发改写及 PASS 对应的版本。
- [ ] 若回答“注入的是不是最新正文”，已区分 `FRESHNESS OBSERVED`（单会话观测）与 reload 语义，未宣称 reload 已生效。
- [ ] 哨兵缺失时判 UNVERIFIED 并提示无空格 `/skills reload`，未判 PASS。
- [ ] 判定使用 PASS、FAIL、UNVERIFIED 三态，未用计数、日志、UI 或静态校验替代。
- [ ] 未执行也未声称执行 `/skills reload` 或 `/skills list`；需要时提示无空格写法。
- [ ] 带空格命令只纠正一次；同一写法再次出现时已改用新 `BINDING` 复验，未重复纠正，也未声称 reload 已执行。
- [ ] 报告列出未验证项。

## 资源

- `scripts/locate_injection.py`：只读定位当前会话 JSONL 中的 Skill 注入记录，按 nonce/args 绑定 `tool_use → tool_result → injection`，核对首行、末章节、`ARGUMENTS:` 尾行与哨兵，并用 `SENTINEL_SCOPE` 区分哨兵命中的正文与 frontmatter 行；`--disk-skill-md` 可指向 live 文件、`git show HEAD:SKILL.md` 导出或调用前快照，并发改写时应指向被验证版本；`--help` 查看参数。
- `inventory-installed-skills`：用户级与项目级枚举、同名与漂移计数。
- `relocate-self-documenting-skill`：移动后的位置叙述审计与可见性分层。
- 项目级 Skill skill-absolute-path-references（仅本项目可见）：移动流程、前缀替换、哈希保持与存在性检查；其他项目可跳过。
- `commit-skill-work`：提交后的运行时解析检查。
- `skill-update-concurrency-safe`：写入稳定性、注入测试与并发哈希复核。
- `skill-file-qa`：结构、本地引用与跨 Skill 引用校验。
- `verify-injected-skill-body-freshness`：注入正文是否为磁盘最新版本、版本定界与写入者归因；路径与调用绑定仍以本 Skill 为准。
