# 证据 — 接管并发重复 Skill

本文件记录来源会话 `359acfd8-f31b-4501-ad8e-635c7f93d4fd`、`3677d3d4-c450-45c6-b00e-4f16329cce18`、`98d02ebd-929d-4176-a727-4b6ff3b11506`、`80685b8f-6be5-4af6-ba89-3c72605f79a7`、`464ffdea-e2ac-4a08-960e-2bb96aeca846` 与 `64bf38af-ac64-4088-b6c9-cf3dc7c19929` 的逐字工具输出与状态边界。第一例（接管并纠错）在下文各节；`3677d3d4`（接管后缩窄交付）、`98d02ebd`（只读保留）、`80685b8f`（多写入者接管与 QA 后重扫）、`464ffdea`（共享参考文件并发追加）与 `64bf38af`（缩窄后新建并存）分别在文末的补充证据与案例二至案例五。哈希、时间、行号和临时路径都是带日期的观测值，不是可复用常量。

## 会话链与快照边界

| 会话 | 角色 | 状态 |
|---|---|---|
| `359acfd8-f31b-4501-ad8e-635c7f93d4fd` | 本次来源：原计划创建 `skill-ref-absolute-path-migration`，规划期间发现 `skill-absolute-path-references`，改为接管并纠错 | revision 0，`hasMoreBefore: false`，2 条消息，1 个用户回合，54 次工具调用；助手正文在 8002 字符处截断 |
| `7aa93ddf-da58-4980-af69-77103562a90f` | 被接管 Skill 的上游证据来源；来源会话通过 `read_chat_session` 读取 | 本文件未直接重读该会话，仅引用来源会话的转述，不作为独立证据 |

读取限制：快照只返回 2 条消息；助手正文 8002 字符后被截断；本次读取将单条工具输出限制为 8000 字符。以下结论优先引用工具输出，而不是被截断的助手正文。

## 时间线与首次冲突（2026-10-26，文件 mtime 为 +01:00）

- 11:28:02Z：来源会话用户消息到达。随后的预检显示目标 `skill-ref-absolute-path-migration` 不存在。
- 规划阶段：目标目录不存在；用户通过 AskUserQuestion 选择“按方案创建（推荐）”与“中文（推荐）”。
- 12:32：并发生成 `skill-absolute-path-references` 目录。
- 12:33:24：`check_absolute_refs.py`（2730 bytes）。
- 12:34:01：`SKILL.md`（8384 bytes）。
- 12:34:57：`preuve-session.md`（4742 bytes）。
- 12:33–12:34 的复核仍显示目标 `skill-ref-absolute-path-migration` 不存在。
- 发现重合后，用户通过第二次 AskUserQuestion 改选“接管并完善现有（推荐）”；初次“按方案创建”的批准未被执行。

目标与并发 Skill 的预检输出：

```text
--- target ---
ls: cannot access 'C:/Users/Administrateur/.qoder/skills/skill-ref-absolute-path-migration': No such file or directory
--- similar skill ---
total 24
drwxr-xr-x 1 Administrateur 197121    0 Oct 26 12:34 .
drwxr-xr-x 1 Administrateur 197121    0 Oct 26 12:32 ..
-rw-r--r-- 1 Administrateur 197121 8384 Oct 26 12:34 SKILL.md
drwxr-xr-x 1 Administrateur 197121    0 Oct 26 12:32 references
drwxr-xr-x 1 Administrateur 197121    0 Oct 26 12:33 scripts
--- hashes ---
0926a36d134aaa8d2ae6526552e50b7ad56507a14acc29b72b33e5a1e1879881 *SKILL.md
./SKILL.md
./scripts/check_absolute_refs.py
```

稳定性采样与目标复核：

```text
2026-10-26 12:33:24.6402741000 2730 ./scripts/check_absolute_refs.py
2026-10-26 12:34:01.3111389000 8384 ./SKILL.md
2026-10-26 12:34:57.6918850000 4742 ./references/preuve-session.md
--- stability ---
0926a36d134aaa8d2ae6526552e50b7ad56507a14acc29b72b33e5a1e1879881 *SKILL.md
8dfd4da3cb95f11f6b6ed999f79bda625c6f9ce964c9b07e18890c4adb6bcbad *references/preuve-session.md
dca3852d2455daa6f0f9d836d6653afe81b5ba3933a887a55fe0c7b56bdbd28c *scripts/check_absolute_refs.py
--- target again ---
ls: cannot access 'C:/Users/Administrateur/.qoder/skills/skill-ref-absolute-path-migration': No such file or directory
```

## 用户决策

AskUserQuestion 的输出原文：

```text
Your questions have been answered: "发现职责高度重合的并发 Skill，如何处理？"="接管并完善现有（推荐）". You can now continue with these answers in mind.
```

这是本快照中唯一的接管授权。除初始任务消息外，没有其他自由文本用户消息；不得把该授权扩大为任意重写、删除或重命名。

## 接管基线

接管前的结构校验：

```text
Validator: read-only (skill files are not modified)
Stability: unchanged for 2.0s after 2.1s
Fingerprint (start): 8384 bytes | mtime=2026-10-26T12:34:01+01:00 | sha256=0926a36d134aaa8d2ae6526552e50b7ad56507a14acc29b72b33e5a1e1879881
Skill: skill-absolute-path-references
Files (3): SKILL.md, references/preuve-session.md, scripts/check_absolute_refs.py
PASS layout: 3 file(s), no extraneous documentation
PASS frontmatter: YAML parsed (PyYAML 6.0.1)
PASS name: 'skill-absolute-path-references' matches directory
PASS description: single line, 388 chars
PASS body: 128 lines (< 500)
PASS content: no TODO markers
PASS local references: 2 checked
PASS skill references: 3 checked (publier-skill-qoder-vers-depot-git, skill-file-qa, skill-update-concurrency-safe)
Fingerprint (final): 8384 bytes | mtime=2026-10-26T12:34:01+01:00 | sha256=0926a36d134aaa8d2ae6526552e50b7ad56507a14acc29b72b33e5a1e1879881
PASS fingerprint: unchanged during validation
Code blocks: python=0 js=0 skipped=4
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
VALIDATE_EXIT=0
```

对被接管 Skill 的脚本运行真实改造目标：

```text
Skill: C:\Users\Administrateur\.qoder\skills\tester-garde-derive-git
absolute refs: 3
EXISTS  C:\Users\Administrateur\.qoder\skills\tester-garde-derive-git\references\preuves-test.md
EXISTS  C:\Users\Administrateur\.qoder\skills\tester-garde-derive-git\scripts\garde_derive.py
EXISTS  C:\Users\Administrateur\.qoder\skills\tester-garde-derive-git\scripts\tester_garde_derive.py
missing: 0
RESULT PASS
ABS_CHECK_EXIT=0
```

## A/B 夹具与错误断言

背景：被接管 SKILL.md 曾写“校验器会先剥离围栏块”，并据此建议把示例放进围栏块。接管时在 `.qoder/tmp/abs-ref-audit-20261026-1239` 建两个夹具，只差“反引号”一个变量。

夹具 A：围栏内保留反引号。

```text
=== fence-backtick ===
FAIL local reference not found: 'scripts/absent.py'
Summary: 8 pass, 1 fail, 0 warn
RESULT FAIL
EXIT=1
```

夹具 B：围栏内同一路径去掉反引号。

```text
=== fence-plain ===
PASS local references: 0 checked
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
EXIT=0
```

结论：围栏块本身不为本地引用豁免；只有围栏内不加反引号才不被识别。修正落在被接管 SKILL.md 第 26 行约束与第 35 行事实节，并同步诊断表与证据状态表。

## 脚本负例契约

```text
=== missing absolute path ===
Skill: C:\Users\Administrateur\.qoder\tmp\abs-ref-audit-20261026-1239\missing-path
absolute refs: 1
MISSING C:\Users\Administrateur\.qoder\tmp\abs-ref-audit-20261026-1239\does-not-exist.md
missing: 1
RESULT FAIL
EXIT=1
=== missing SKILL.md ===
ERROR SKILL.md not found: C:\Users\Administrateur\.qoder\tmp\abs-ref-audit-20261026-1239\empty-dir\SKILL.md
EXIT=2
=== missing directory ===
ERROR skill directory not found: C:\Users\Administrateur\.qoder\tmp\abs-ref-audit-20261026-1239\no-such-dir
EXIT=2
=== no args ===
EXIT=2
```

## 并发写入与合并

第一次 Edit 的返回原文：

```text
Successfully modified file: C:\Users\Administrateur\.qoder\skills\skill-absolute-path-references\SKILL.md (1 replacements). The file changed since your last read. Your edit was applied to the current contents; read it before relying on surrounding changes you have not seen.
```

随后代理重读 SKILL.md；并发会话已把“三处通常形成六处替换”改为“同一目标通常出现 2–3 次，以实际清单为准”。证据文件在校验期间再次变化；代理等待稳定后重新读取，再追加“接管复核”表。并发新增的标题、计数表述与参考内容均保留，没有整文件覆盖。

## 最终验收

```text
Fingerprint (start): 8850 bytes | mtime=2026-10-26T12:38:38+01:00 | sha256=1c102fe53fcbab96e0895e2fcf6d1875853d48dd3cf1a39ed25194ecbc0eaf5a
Skill: skill-absolute-path-references
Files (3): SKILL.md, references/preuve-session.md, scripts/check_absolute_refs.py
PASS description: single line, 388 chars
PASS body: 128 lines (< 500)
PASS local references: 2 checked
PASS skill references: 3 checked (publier-skill-qoder-vers-depot-git, skill-file-qa, skill-update-concurrency-safe)
Fingerprint (final): 8850 bytes | mtime=2026-10-26T12:38:38+01:00 | sha256=1c102fe53fcbab96e0895e2fcf6d1875853d48dd3cf1a39ed25194ecbc0eaf5a
PASS fingerprint: unchanged during validation
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
VALIDATE_EXIT=0
```

最终哈希与清理：

```text
1c102fe53fcbab96e0895e2fcf6d1875853d48dd3cf1a39ed25194ecbc0eaf5a *SKILL.md
6c8a72ed68527e16827c87612762f0e569f7abcdaf9a59b09c725739c8b307a2 *references/preuve-session.md
dca3852d2455daa6f0f9d836d6653afe81b5ba3933a887a55fe0c7b56bdbd28c *scripts/check_absolute_refs.py
--- temp/cache ---
TEMP_ABSENT
CACHE_CHECK_DONE
```

2026-10-26 复核当前磁盘时，三个哈希与上述一致，`skill-file-qa` 仍为 `RESULT PASS`、9 pass / 0 fail / 0 warn、`Files (3)`。

## 三方哈希

| 版本 | SKILL.md | preuve-session.md | 脚本 |
|---|---|---|---|
| 接管前基线 | `0926a36d…` | `8dfd4da3…` | `dca3852d…` |
| 并发改写 | `ddbb24c5…`（被接管证据记录） | `b341d3c5…` 与 `60d76f9e…` 为中间版本 | `dca3852d…` |
| 最终 | `1c102fe5…` | `6c8a72ed…` | `dca3852d…` |

脚本哈希从始至终未变。SKILL.md 的三方哈希来自不同时间的磁盘观测，不是可复用常量。

## 状态划分

| 项目 | 状态 | 依据 |
|---|---|---|
| 目标目录在规划时不存在 | 已观测 | 两次 ls 输出 |
| 并发 Skill 于 12:32–12:34 出现 | 已观测 | 目录与文件 mtime |
| 用户选择接管 | 已观测 | AskUserQuestion 输出原文 |
| 文档的围栏块断言为假 | 已观测 | A/B 夹具输出与退出码 |
| 并发写入被保留并合并 | 已观测 | Edit 警告、重读、最终内容 |
| 最终 QA PASS 与哈希 | 已观测 | 工具输出与 2026-10-26 复核 |
| 原目标目录从未创建 | 已观测 | 接管后仍不存在 |
| 上游会话细节 | 转述 | 来源会话读取并总结；本文件未直接重读 |
| 其他版本或未来环境中的校验器行为 | 未验证 | 需重新建夹具实测 |

## 重新使用规则

- 不复制本文件的哈希、时间、行号或 PASS 数量；每次重新读取并运行。
- 接管不等于任意重写；只修正被实测反驳的断言，保留有效规则与并发内容。
- A/B 夹具放在 Skill 目录之外，结束后删除；失败输出不要以反引号形式写进 SKILL.md。
- 报告必须区分“接管”与“创建”，并注明未验证分支。

## 案例二 — 来源会话 98d02ebd（2026-10-26，只读保留）

来源会话：`98d02ebd-929d-4176-a727-4b6ff3b11506`（revision 11，6 条消息，hasMoreBefore=false，runtimeState=running）。
并发创建者：`efa8bcbd-363a-47c3-892f-93612a9db730`（首次读取 revision 26，后续 revision 41）。
目标：entite-conscience-logarithmique。会话开始时目标目录不存在；创建者在 13:04:58–13:06 写入 4 个文件。

### 失败与恢复

- read_chat_session 返回约 72,636 tokens（217,908 字符），超过 25,000 token 上限，落盘后分块读取。
- `python` 退出码 49，输出“Python est introuvable ... Microsoft Store”；改用 `py -3.12`。
- 打印中文触发 `UnicodeEncodeError: 'charmap' codec can't encode ...`（`cp1252.py`）；之后使用 `PYTHONIOENCODING=utf-8`，目标门禁另设 `PYTHONUTF8=1`。

### 用户决策

AskUserQuestion 原文：

```text
Your questions have been answered: "目标 Skill 已由并发会话创建，并通过我的独立只读验证。你希望我下一步怎么做？"="保持现状（推荐）".
```

### 独立只读验收

静态验收（skill-file-qa）：

```text
Skill: entite-conscience-logarithmique
Files (4): SKILL.md, references/contrat-preuves.md, references/pieges-runtime.md, scripts/verifier_pipeline_entite.py
PASS description: single line, 737 chars
PASS body: 205 lines (< 500)
PASS local references: 0 checked
PASS skill references: 2 checked (mesure-cesium-133-geolocalisee, tableau-maitre-sequentiel)
Fingerprint (final): 12534 bytes | mtime=2026-10-26T13:04:58+01:00 | sha256=ec42befc8d7b784c6d7d9412b07cf1fc9ccc74149889f312bed70de2f41cc67c
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
EXIT=0
```

目标自带默认只读门禁（摘要）：

```text
[OK] CSV-LIGNES: 216 lignes
[OK] CSV-S20-EFFECTIF: S20: 12 lignes
[OK] CSV-S20-CONTRAT: S20: ENT-01..ENT-12 / SEQ 205..216
[OK] HTML-LIGNES: 217 occurrences de <tr (en-tete + 216)
[OK] HTML-BADGES: 21 occurrences de class="badge"
[OK] HTML-WEB-CLOUD: copie web_cloud identique
[OK] VALID-TABLEAU: validateur tableau: RESULT OK, exit 0
RESULT: OK (35/35)
EXIT=0
```

文件指纹（13:10 双采样稳定）：

| 文件 | 大小 | SHA-256 前缀 |
|---|---:|---|
| SKILL.md | 12534 B | `ec42befc…` |
| references/contrat-preuves.md | 8564 B | `62792510…` |
| references/pieges-runtime.md | 6486 B | `9f1a291b…` |
| scripts/verifier_pipeline_entite.py | 25712 B | `e704997a…` |

### 边界

- 本会话对目标目录零写入；只运行静态验收与默认只读门禁。
- 未执行 `--avec-tests`、`--avec-regression`、`--avec-run`（会写 memoire_aq 封条）。
- 创建者会话当时仍在运行；若其继续写入，指纹与门禁需重跑。
- 后续两条用户消息是“列出测试用例”和“运行 68 个测试”，属于新任务，不是对只读流程的纠正。
- 以上哈希与 PASS 数量是 2026-10-26 的历史观测值，不表示目标 Skill 当前状态。

### 状态划分

| 项目 | 状态 | 依据 |
|---|---|---|
| 目标开始时不存在 | 已观测 | 预检输出 |
| 创建者写入 4 个文件 | 已观测 | 文件 mtime 与目录列表 |
| 读取超限后落盘分块读取 | 已观测 | MCP 截断提示与落盘路径 |
| python 退出 49 / cp1252 | 已观测 | 失败命令的退出码与 traceback |
| 用户选择保持现状 | 已观测 | AskUserQuestion 原文 |
| 静态验收 9/0/0 与门禁 35/35 | 已观测 | 工具输出 |
| 创建者之后是否再次写入 | 未验证 | 快照后未持续监视 |

## 补充证据 — 来源会话 3677d3d4（2026-10-26，接管后缩窄交付）

来源会话：`3677d3d4-c450-45c6-b00e-4f16329cce18`。本会话通过 `read_chat_session` 读取，并用项目原始 JSONL（读取时为 344 行）核对工具输出与用户消息；以下数值是 2026-10-26 的观测值。

目标：`lock-lf-endings-skill-repo`。接管基线为 3 个文件，目录不是 Git 仓库（`NO_GIT`）：

| 文件 | 大小 | SHA-256 前缀 |
|---|---:|---|
| SKILL.md | 13,479 B | `0ad1a483…` |
| references/preuves-session-lf.md | 7,082 B | `159b54f9…` |
| scripts/…（并发脚本） | 13,244 B | `33d6ca2c…` |

### 用户缩窄交付

用户原话（12:08:58Z）：

```text
先只写文档和参考文件，不加脚本
```

代理据此只改 SKILL.md 与 references，保留磁盘上的并发脚本，并在报告中把脚本契约测试列为范围外。`Files (N)` 仍把脚本计入，没有为了配合“只写文档”而删除或隐藏文件。

### A/B 夹具（行尾属性）

三组夹具只差属性来源，用于核对 `.gitattributes` 与 `.git/info/attributes` 的实际效果：

| 组 | 配置 | `git ls-files --eol` 输出 |
|---|---|---|
| A | 无属性文件 | `i/lf w/lf attr/ file.txt` |
| B | `.git/info/attributes` 含 `text=auto eol=lf` | `i/lf w/lf attr/text=auto eol=lf` |
| C | 优先级对照 | `text: auto` / `eol: lf` |

工作区字节数：

```text
outA: 13 bytes, CR=2, LF=2
outB: 11 bytes, CR=0, LF=2
outC: 11 bytes, CR=0, LF=2
```

结论：只有带属性的 B/C 组输出被规范为 LF；A 组保留 CR。该结论只适用于本机 Git 版本与这组夹具，换环境需重跑。

### 清理失败与恢复

首次清理夹具时失败，未谎称成功：

```text
WinError 5: ...repo\.git\objects\fb\bee861...
CLEANUP_FAIL
```

按序尝试：

```text
chmod -R u+w + rm -rf            -> STILL_PRESENT
shutil.rmtree(onexc=...)         -> WinError 32（repo 被进程占用）
PowerShell Remove-Item -Force    -> in use, PS_EXIT=1, PRESENT
```

占用释放后再次执行 `chmod -R u+w` 与 `rm -rf`：

```text
FIXTURE_REMOVED
```

判定依据是 `test -e` 为假，而不是上一条命令的退出码。

### 后续授权删除脚本

用户随后明确要求“先备份再删除脚本”（12:23:00Z）。代理在 Skill 目录之外备份并核对哈希后才删除：

```text
source script: 13,244 B | sha256 33d6ca2c…
backup:        13,244 B | sha256 33d6ca2c… | IDENTICAL True
after deletion: Files (2)
skill-file-qa: RESULT PASS
manifest:      2/2 PASS
```

这一步不是“缩窄交付”的默认动作：删除需要针对具体路径的单独授权，且必须先备份并核对哈希。

### 状态划分

| 项目 | 状态 | 依据 |
|---|---|---|
| 接管基线为 3 个文件且无 Git 仓库 | 已观测 | 哈希与 `NO_GIT` 输出 |
| 用户要求只写文档和参考文件 | 已观测 | 用户消息原文 |
| 代理保留脚本并标注范围外 | 已观测 | 最终文件清单与报告 |
| A/B 行尾差异 | 已观测 | `git ls-files --eol` 与字节计数 |
| WinError 5 / 32 与最终删除 | 已观测 | 清理命令输出与 `test -e` |
| 备份哈希一致后才删除脚本 | 已观测 | 哈希比较 `IDENTICAL True` |
| 其他 Git 版本或文件系统上的行尾行为 | 未验证 | 未跨环境重跑 |

### 重新使用规则

- 缩窄交付不等于获得删除授权；脚本保留，删除需具体路径授权、目录外备份与哈希核对。
- 清理失败按 WinError 类型处理，只有 `test -e` 为假才写“已清理”。
- A/B 结论受 Git 版本与属性文件位置影响，换环境重新实测。

## 案例三 — 来源会话 80685b8f（2026-10-26，多写入者接管与 QA 后重扫）

来源会话：`80685b8f-6be5-4af6-ba89-3c72605f79a7`。首次读取 revision 13（`runtimeState=running`），复核期间变为 revision 34（`waiting-user`，`pendingInteractionCount=1`）；项目 JSONL 从 293 行增长到 374 行。以下结论绑定 2026-10-26T17:01Z 的观测；之后未持续监视。

目标：`auditer-nettoyer-temp-qoder`（不是本 Skill）。创建者 `a32c772d`。用户唯一决策（AskUserQuestion 原文，16:49:20Z）：`"接管并完善现有（推荐）"`。本会话没有自由文本纠正；第二条用户消息“提交 Git 变更”（16:56:29Z）是后续任务。

### 写入者归因（UTC）

全量扫描 `~/.qoder/projects/*/*.jsonl`，按 `tool_use_id` 配对 `Write`/`Edit` 与 `tool_result`；只有成功结果计入“写入”。

| 会话 | 角色 | 成功写入 | 写入时间（UTC） | 依据 |
|---|---|---:|---|---|
| `a32c772d` | 创建者 | 9（2 Write + 7 Edit） | 16:45:06–16:48:37 | SKILL.md 与参考档案 |
| `a55b50cd` | 后续写入者 | 9（8 SKILL.md + 1 参考） | 16:51:01–16:52:26 | 与 80685b8f 的 Edit 重叠 |
| `80685b8f` | 本会话 | 3（1 失败 + 2 成功） | 16:51:19 / 16:55:08 / 16:55:17 | 失败 Edit 也留下 tool_use |
| `30f6f7bd` | 只读核查 | 0 | — | 零 Write/Edit，不是写入者 |
| `464ffdea` | 后续写入者 | 13（1 Write + 12 Edit） | 16:56:11–17:00:20 | 先脚本，后在 QA 之后改 SKILL.md 与参考 |

注意：上表时间来自 JSONL（UTC）；Windows 文件 mtime 是 +01:00，例如 17:52:24+01:00 对应 16:52:24Z。比较前必须换算。

### 关键事件与原文

- 16:51:19.337Z 的 Edit 失败原文：

```text
Error: Failed to edit, 0 occurrences found for old_string in C:\Users\Administrateur\.qoder\skills\auditer-nettoyer-temp-qoder\SKILL.md. Ensure you're not escaping content incorrectly and check whitespace, indentation, and context. Use Read tool to verify.
```

`a55b50cd` 已在 16:51:01、16:51:06、16:51:14、16:51:19.049 连续编辑同一文件。0 命中是并发信号；但文本本就不匹配也会返回 0 命中，需先查写入记录与当前哈希。

- `a32c772d` 在 16:49:45Z 已 `ready`（revision 35），16:51:51Z 又为 `running`（revision 18）；16:48:37Z 之后未再观察到它写该文件。revision 不是写入次数，也不保证单调。
- 16:54:04Z 来源会话称“全部写入者（`a32c772d`、`30f6f7bd`、`a55b50cd`）均 ready”；其中 `30f6f7bd` 从未写入，只是只读核查者。读者可能后来转为写者：`464ffdea` 在 16:49:20Z 的列表中还只是“只读核查”，16:56:11Z 起开始写脚本，16:58:22Z 起改写 SKILL.md。
- 16:49:01Z 验收片段：`nested_git_max1=0`、`nested_git_max5=5`；16:54:44Z 同一片段输出 `NESTED_GIT=16`。16:55:08Z 的 Edit 删除“当前实测 5”，改为“该值随夹具创建与清理变化”。
- 16:55:27Z `skill-file-qa`：`RESULT PASS`，9 pass / 0 fail / 0 warn，`Files (2)`，15,283 B，sha `3193a0c2…`。16:55:48Z 回读确认两处修订落地。
- 16:56:11Z–17:00:20Z `464ffdea` 新建脚本并改写 SKILL.md 与参考；17:01:44Z 的校验器输出显示目标已为 `Files (3)`、18,131 B、sha `d2064196…`。16:55 的 PASS 只对当时指纹有效。

### 与自动推荐数据的差异

自动推荐称“`a55b50cd` 与 `30f6f7bd` 又连续改写同一 SKILL.md（16:51–17:52）”。JSONL 只支持 `a55b50cd`（16:51:01–16:52:26Z）；`30f6f7bd` 零次 Write/Edit；`464ffdea` 才是 QA 之后继续写入的会话。推荐中的“16:51–17:52”混用了 UTC 与 +01:00。该陈述未写入 SKILL.md 规则；本文件保留反证。

### 状态划分

| 项目 | 状态 | 依据 |
|---|---|---|
| `a32c772d` 创建并写入 9 次 | 已观测 | tool_use/tool_result 配对 |
| `a55b50cd` 成功写入 9 次 | 已观测 | 同上 |
| `30f6f7bd` 不是写入者 | 已观测 | 零 Write/Edit |
| `464ffdea` 在 QA 后写入 | 已观测 | 16:56:11–17:00:20 记录 |
| Edit 0 命中 | 已观测 | 16:51:19 失败原文 |
| `NESTED_GIT` 5→16 | 已观测 | 16:49:01 与 16:54:44 输出 |
| 16:55 PASS 只对当时指纹有效 | 已观测 | 后续写入与 17:01 校验器输出 |
| 推荐称 `30f6f7bd` 改写 | 已反驳 | JSONL 零写入 |
| 来源会话之后的继续行为 | 未验证 | 会话仍运行，快照后未持续监视 |

### 重新使用规则

- 写入者表只统计成功的 Write/Edit；失败 Edit、只读命令和当前会话都要分开处理。
- `ready` 只表示回合结束；每次编辑前重扫，新写入者出现就重取基线。
- QA 后必须重扫；PASS 绑定指纹与扫描时刻，不覆盖之后的写入。
- 验收片段只写不变量或日期化观测；计数漂移不是契约。
- 自动推荐数据不是证据；与 JSONL 冲突时以 JSONL 为准，并记录反证。

## 案例四 — 来源会话 464ffdea（2026-10-26，共享参考文件的并发追加）

来源会话：`464ffdea-e2ac-4a08-960e-2bb96aeca846`。目标仍是 `auditer-nettoyer-temp-qoder`（不是本 Skill）。快照约 190k 字符，助手正文在 8,002 字符处截断；以下只引用 tool_use/tool_result 与文件观测，不引用被截断的叙述。

### 时间线（UTC）

| 时间 | 事件 | 依据 |
|---|---|---|
| 16:49:20Z | `464ffdea` 在会话列表中仍是只读核查 | 当时的列表输出 |
| 16:56:11Z | 首次成功写入（脚本） | JSONL 配对 |
| 16:58:22Z | 开始改写 SKILL.md | JSONL 配对 |
| 17:00:20.837Z | 追加共享参考文件 | Edit 记录 |
| 17:01:44Z | 校验器读到 `Files (3)`、18,131 B、sha `d2064196…` | 校验器输出 |

### 共享参考文件的追加顺序

同一文件 `auditer-nettoyer-temp-qoder/references/cas-nettoyage-temp-qoder-2026-10-26.md` 被三个会话先后追加：

| 会话 | 追加时间（UTC） | 追加后大小 |
|---|---|---:|
| `a55b50cd` | 16:52:15.811 | 15,434 B |
| `80685b8f` | 16:55:17.760 | 15,857 B |
| `464ffdea` | 17:00:20.837 | 21,030 B |

追加后文件为 21,030 B，mtime 18:00:19.588+01:00（=17:00:19Z），SHA-256 为 `d74833c491991fcc4404172c3997a410efc347be461b0a4ffa426496c095f746`。这些数字只对应 2026-10-26 的该文件，不是本 Skill 的常量。

关键点：`80685b8f` 在 16:55:27Z 的 `RESULT PASS` 只对它当时的 15,857 B 版本有效；`464ffdea` 在 QA 之后继续追加，使 PASS 过期。会话在 16:49Z 只是读者，16:56Z 起转为写者。

### 旧全文覆盖的风险

不同会话各自持有不同时间点读取的全文；若后写者用旧全文 Write，会丢掉先写者已追加的段落。来源会话中未观察到覆盖事故（三次追加均保留），因此“旧全文覆盖会丢失并发块”在来源证据中是推断，不是已观测事故；本 Skill 用目录外 A/B 夹具单独验证（见 SKILL.md 第 4 节第 7 条）。

### 与自动推荐数据的差异

- 推荐把该共享参考文件的并发追加描述成本 Skill 的 references；实际写入路径属于 `auditer-nettoyer-temp-qoder`。本 Skill 只采纳可迁移规则“写入前重读尾部并按当前尾部 Edit”，不复制该文件的证据。
- 首次按 `>= 2026-10-26T17:50Z` 过滤 JSONL 得到空集，因为 JSONL 用 UTC、工具输出用 +01:00；改用 16:45–17:10Z 后命中上述写入。时区必须先换算。

### 状态划分

| 项目 | 状态 | 依据 |
|---|---|---|
| `464ffdea` 成功写入 13 次 | 已观测 | tool_use/tool_result 配对 |
| 三个会话先后追加同一参考文件 | 已观测 | Edit 记录与 15,434 → 15,857 → 21,030 B |
| QA PASS 在后续追加后过期 | 已观测 | 16:55 的 PASS 与 17:00 的写入 |
| 旧全文覆盖会丢失并发块 | 推断 | 来源未发生覆盖事故；由追加顺序与大小推断 |
| 推荐把该文件归到本 Skill | 已反驳 | 实际路径属于 `auditer-nettoyer-temp-qoder` |
| `464ffdea` 之后是否继续写入 | 未验证 | 快照后未持续监视 |

### 重新使用规则

- 向被多个会话追加的 references 写入前，重读最后约 40 行，记录 size、mtime、SHA-256 与尾部锚点；只用 Edit 按当前尾部追加。
- 禁止用规划时读取的旧全文 Write 覆盖；写入后记录新哈希与新锚点，并保留其他会话的追加块。
- 仍有写入者 running 时，报告写“最终性未验证”；QA PASS 绑定扫描时刻与指纹。
- 自动推荐中的文件归属先核对路径；不把另一个 Skill 的证据搬进本 Skill。

## 案例五 — 来源会话 64bf38af（2026-10-26，缩窄后新建并存）

来源会话：`64bf38af-ac64-4088-b6c9-cf3dc7c19929`，标题「创建可复用 Skill 方案」。读取时 `runtimeState=running`、`revision=11`、`hasMoreBefore=false`，2 个用户回合；第二个回合「commit this skill」在读取时仍为 streaming，本案例未执行该回合。目标：`verify-skill-doc-claims-before-edit`（不是本 Skill）。

### 时间线与重合检测

- 目标初始不存在。
- `verifier-fixture-autocrlf-non-vacue` 在 22:20–22:23 出现。JSONL 路径扫描显示 `64d354ae` 对该包 SKILL.md、references 与 scripts 有 Write/Edit 记录，`001bd231` 在 22:23 编辑其 SKILL.md，读取时仍为 `running`。
- 本会话用能力矩阵确认 CRLF 夹具、非空断言顺序与“覆盖/承重”措辞已被该包覆盖；真实增量只剩“写入前声明台账 + 措辞校准 + 最小修改 + 基线 QA”。

### 用户决策

AskUserQuestion 原文：

```text
Your questions have been answered: "并行会话刚创建的 verifier-fixture-autocrlf-non-vacue 已覆盖本次建议的 CRLF 核心规则。目标目录不存在，接下来如何处理？"="缩窄后创建（推荐）". You can now continue with these answers in mind.
```

### 冻结与写入前复查

- 22:26:46 复查：`target_exists=no`。
- 重合包基线：`SKILL.md` 16,747 B，mtime `2026-10-26 22:23:50.816947000 +0100`，SHA-256 `bdb6b1a5…`。
- 本会话未修改重合包；其写入者 `001bd231` 在读取时仍运行，之后是否继续写入未持续监视。

### 委派边界

| 职责 | 归属 |
|---|---|
| CRLF 与 `autocrlf` 夹具、stat 缓存、非空断言顺序、présent vs porteur | `verifier-fixture-autocrlf-non-vacue` |
| 通用 bash 块提取与 A/B | `verify-skill-command-blocks-fixture` |
| 既有参考夹具重放 | `replay-skill-reference-fixtures` |
| 写入后结构、引用、行数与指纹验收 | `skill-file-qa` |
| 来源会话取证 | `audit-session-evidence` |
| references 证据档案三级写作 | `write-skill-evidence-case-study` |
| 并发采样、备份与最小 Edit | `skill-update-concurrency-safe` |

新 Skill 只在“什么时候不用”和资源表保留这些委派，不复制夹具与步骤。

### 写入者归因

- 目标路径只有本会话 `64bf38af` 的 Write/Edit：2 次 Write（SKILL.md、references）与 4 次 Edit（references）。
- 其他会话在项目 JSONL 中出现该词，但没有目标路径的 Write/Edit；不能据此算作新目标写入者。
- 当前会话单列；目标没有其他成功写入者。

### 验收与哈希

```text
Files (2): SKILL.md, references/evidence-2026-10-26.md
PASS description: single line, 466 chars
PASS body: 174 lines (< 500)
PASS local references: 1 checked
PASS skill references: 7 checked
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
```

- `SKILL.md`：11,577 B，SHA-256 `7cebe034…`。
- `references/evidence-2026-10-26.md`：最终 7,246 B，SHA-256 `6fa1cf89…`。
- 校验器指纹只覆盖 SKILL.md，因此 references 单独记录。
- 22:30:30 复查重合包 `SKILL.md`，仍为 `bdb6b1a5…`，未被本会话修改。

### 状态划分

| 项目 | 状态 | 依据 |
|---|---|---|
| 目标初始不存在 | 已观测 | 初始 `ls` 输出 |
| 重合包 22:20–22:23 出现 | 已观测 | 目录与文件 mtime |
| `64d354ae` 对重合包有 Write/Edit 记录 | 已观测 | JSONL 路径扫描 |
| `001bd231` 22:23 编辑且仍 running | 已观测 | JSONL 路径与 `list_chat_sessions` |
| 用户选择缩窄后创建 | 已观测 | AskUserQuestion 原文 |
| 写入前目标仍不存在 | 已观测 | `target_exists=no` |
| 新目标只有本会话写入 | 已观测 | 目标路径 Write/Edit 扫描 |
| 重合包写后未变 | 已观测 | 前后 SHA-256 一致 |
| 重合包写入者之后是否继续写入 | 未验证 | 22:24 后未持续监视 |
| 来源会话「commit this skill」回合 | 未验证 | 读取时仍在 streaming |

### 重新使用规则

- 缩窄后新建不是复制：先做能力矩阵，只写真实增量，把重合职责写成委派。
- 写入前冻结重合包全部文件哈希；写入后重算，变化即作废边界。
- 写入者扫描只统计新目标路径；重合包与临时文件写入者单列。
- QA 后分别记录 SKILL.md 与 references 哈希；不要用 SKILL.md 指纹代表整个包。
