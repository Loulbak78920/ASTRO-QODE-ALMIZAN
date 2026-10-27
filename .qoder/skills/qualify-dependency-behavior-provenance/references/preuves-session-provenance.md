# 依赖行为来源判别的会话证据

## 来源与复核范围

- 主会话：`a6127096-ec1b-47db-9621-f195d0df19e3`（2026-10-26，标题「更新 gitattributes 技能」）。该会话核实了「脚本 PASS」的来源，更新 `lock-lf-endings-skill-repo` 为版本限定双分支，并提交 `e6a6e5f`。
- 上游会话：`ef2d6bc1-abb7-49b0-b0ef-ccfdeafa4754`（2026-10-26，标题「创建可复用 Skill 案例」）。其 14:35:32Z 用户轮次为 `add .gitattributes to enforce LF line endings`，在 `write-skill-evidence-case-study` 上产生本节引用的审计输出。
- 当前状态复核：2026-10-26（本机 +01:00），Git Bash、`git 2.52.0.windows.1`、Python 3.14（`py -3`）。
- 时区约定：消息时间用 UTC，工具输出时间用本机偏移 +01:00。
- 分级：**已核实** = 有可复核的命令输出；**源码推断** = 由 HEAD 与工作区源码差异推出但未执行 HEAD 版本；**未验证** = 未取得证据。

## 已核实：同一脚本产生两种结果

上游会话 `ef2d6bc1` 在 15:35 +01:00 对 `write-skill-evidence-case-study` 实跑，关键输出逐字为：

```text
Files (3): .gitattributes, SKILL.md, references/cas-live-creation-2026-10-26.md
WARN layout: unexpected file '.gitattributes'
Summary: 9 pass, 0 fail, 1 warn
RESULT PASS
```

```text
All files: 3 | Clean: 3 | Caches: 0 | Unexpected: 0
QA Files (N): 3 | MATCH on-disk total 3
RESULT PASS
MANIFEST_EXIT=0
```

同一脚本的 HEAD 版本会在根 `.gitattributes` 上报 `UNEXPECTED` 并退出 1，因为工作区 `git diff` 显示允许清单是未提交改动（同批取证中 `blame` 记录的工作区时间为 15:39 +01:00）：

```diff
 ALLOWED_DIRS = {"scripts", "references", "assets"}
+ALLOWED_FILES = {"SKILL.md", ".gitattributes"}
 ...
-        if rel == "SKILL.md":
+        if rel in ALLOWED_FILES:
```

```text
$ git blame -L 13,13 -- scripts/check_package_manifest.py
00000000 (Not Committed Yet 2026-10-26 15:39:27 +0100 13) ALLOWED_FILES = {"SKILL.md", ".gitattributes"}
^7a39419 (M. Ahmed Elbahloul 2026-10-26 12:08:02 +0100 12) ALLOWED_DIRS = {"scripts", "references", "assets"}
```

`00000000` + `Not Committed Yet` 是该行未提交的直接证据；`^7a39419` 说明相邻常量来自 HEAD。

## 源码推断：HEAD 版本的行为

`a6127096` 在 HEAD `7a39419` 上读取 HEAD 内容，输出中没有 `ALLOWED_FILES`：

```text
== HEAD version ALLOWED ==
12:ALLOWED_DIRS = {"scripts", "references", "assets"}
61:    unexpected: list[str] = []
66:        if len(parts) > 1 and parts[0] in ALLOWED_DIRS:
68:        unexpected.append(rel)
69:    return all_files, clean, caches, unexpected
```

本次创建复核在 HEAD `dd606de` 上执行：

```text
$ git show HEAD:scripts/check_package_manifest.py | grep -n "SKILL.md"
63:        if rel == "SKILL.md":
```

两版 HEAD 都没有 `ALLOWED_FILES`，只跳过 `SKILL.md`，因此会把根 `.gitattributes` 归入 `unexpected`，打印 `UNEXPECTED .gitattributes` 并返回 1。这是**源码推断**：没有执行 HEAD 版本，也没有在另一台机器复现。

## 本次创建复核（2026-10-26）

`skill-package-integrity-audit` 的 HEAD 已前进到 `dd606de`（`Require full dependency contract re-audit before updating hashes`），工作区仍为 `M scripts/check_package_manifest.py`。本次创建复核取得：

| 项目 | 值 |
|---|---|
| HEAD | `dd606de` |
| status | ` M scripts/check_package_manifest.py` |
| 工作区 SHA-256 | `04bb22b9a75c20a7c4de58d10afb2032838caa4668055e123f07f25381a72f6b` |
| 工作区 blob OID | `5746d00e14c918ec687f8d462d46eadabe4c4eb3` |
| HEAD blob OID | `2f43a27572e8f6e76d2a4f77d9c9610fd27edb59` |
| HEAD 内容 SHA-256 | `9091fe0a2b17ac5dbc7714ba772212f6e4a75fad6bba453db50f86975f85159e` |

- HEAD `dd606de` 的第 63 行仍为 `if rel == "SKILL.md":`，无 `ALLOWED_FILES`。
- 工作区第 13 行为 `ALLOWED_FILES = {"SKILL.md", ".gitattributes"}`。
- 结论：`WORKTREE_ONLY`。未提交改动跨越了一次新的 HEAD 提交仍然存在，说明「过了多久」不能替代来源判别。

## 决议与文档修改

`a6127096` 没有把上游 PASS 直接写成「当前脚本接受」，而是：

- 在 `lock-lf-endings-skill-repo` 的 description、适用条件、约束 6、Step 1 取舍表、Step 5 预期表、报告模板与陷阱表中改为版本限定双分支，并要求实跑与报告退出码。
- 在 `references/preuves-session-lf.md` 追加带日期的「后续观察」，保留旧 FAIL 记录原文并加前向指针。
- 提交 `e6a6e5f fix(skill): corriger l'audit manifest des fins de ligne LF`（2 文件，+44/−15），工作区干净；仓库无 remote，推送未执行。
- 复跑结果：QA `Files (3)`、`9 pass / 0 fail / 1 warn`、`RESULT PASS`；manifest `Unexpected: 0`、`RESULT PASS`、`MANIFEST_EXIT=0`（使用同一未提交脚本）。

## 未验证与限制

- 未执行 HEAD 版本：`UNEXPECTED`/退出 1 属源码推断，未在隔离副本复跑。
- 无 remote，也没有第二台机器或第二个克隆：「其他机器按 HEAD 复现」是设计推论，未实测。
- 依赖脚本的工作区改动可能在被引用前被提交、还原或再次修改；每次使用本 Skill 前必须重做 Step 0–2，不能沿用本文的 `WORKTREE_ONLY`。
- 未评估修改 `check_package_manifest.py` 白名单是否获得授权；本案例只把它当作外部事实读取。
- 上游会话的授权范围只覆盖「add .gitattributes」；主会话的提交由「提交并推送这些更改」授权，推送因无 remote 未完成。

## 可复用教训

1. 「当前脚本 PASS」可能是本机工作区的产物；写入文档前先看 `status`、`diff`、`show HEAD:` 与 `blame`。
2. 旧 FAIL 记录与当前 PASS 可以同时为真；用提交号与日期限定，不要删除任一侧。
3. 源码中缺少产生行为的分支，已足以否定 HEAD 能产生该行为；但应标为源码推断，直到真的执行 HEAD 版本。
4. 未提交改动可能跨越新的 HEAD 提交继续存在，因此时间流逝不构成提交来源的证据。

## 后续观察：独立复核与并发写入（2026-10-26）

本会话 `8bf351ff-0bfa-46f6-aeb5-eb8873808d0d` 在目标 Skill 已存在后做只读验收。追加本节之前，本会话未修改本包或依赖脚本；本次更新只包含本节追加与 `SKILL.md` 资源指针同步。

### 并发创建与归属

- 本会话开始时目标目录不存在；2026-10-26T15:58:09.830933+01:00 出现 `SKILL.md`（12344 B），15:58:22.608089+01:00 出现本文件初版（5653 B）。
- 写入者为会话 `3532d974-8dd9-4fde-9195-03abf7aa4333`：其 2026-10-26T14:55:50Z 给出创建方案，14:57:07Z 用户回复「确认按此方案创建新 Skill」，随后产生两份 `Write`。
- 本会话未覆盖同名 Skill，只做只读检查；写入者随后在 16:01:35.548747+01:00 将本文件更新到 6083 B，修正了 `7a39419` 与 `dd606de` 两版 HEAD 证据的归属：前者来自 `a6127096` 对 HEAD 内容的读取，后者是创建复核在 `dd606de` 上的新执行。
- 写入者于 2026-10-26T15:02:22Z 开始「test the skill with a sample file」，报告 `COMMITTED`、`WORKTREE_ONLY`、`UNKNOWN` 三类判定均有实测证据，夹具为 `C:\Users\Administrateur\.qoder\tmp\qualify-skill-test-20261026T1605`。该结果来自其会话报告，本会话未打开夹具或复跑，列为**未验证**。

### 依赖状态的独立确认

2026-10-26 15:57–16:02 +01:00 对 `skill-package-integrity-audit` 复跑只读取证：

- HEAD `dd606de974e0aeb13e186e412b21f60e088ad67a`；`status --short` 为 ` M scripts/check_package_manifest.py`。
- `git blame` 在 15:57:45 +01:00 仍显示 `00000000 (Not Committed Yet ... 13) ALLOWED_FILES = {"SKILL.md", ".gitattributes"}`；与创建会话在 15:39:27 +01:00 的 blame 相比，同一未提交行持续存在。
- HEAD 版本无 `ALLOWED_FILES`，第 63 行为 `if rel == "SKILL.md":`。
- 工作区 SHA-256 `04bb22b9a75c20a7c4de58d10afb2032838caa4668055e123f07f25381a72f6b`；HEAD 内容 SHA-256 `9091fe0a2b17ac5dbc7714ba772212f6e4a75fad6bba453db50f86975f85159e`。
- 判定：`WORKTREE_ONLY`，与上文一致；HEAD 行为仍是**源码推断**，未执行 HEAD 版本。

### 包验收（最终快照）

- 追加本节前的快照：`SKILL.md` 12344 B、`references/preuves-session-provenance.md` 6083 B；`CR=0`、无 BOM、无 `__pycache__`/`.pyc`。
- 稳定性：连续 4 次采样（约 8 秒）字节与 SHA-256 不变；校验器 2 秒稳定性检查通过。
- `skill-file-qa`：`Files (2)`、`9 pass / 0 fail / 0 warn`、`RESULT PASS`、`QA_EXIT=0`；description 单行 765 字符、正文 200 行、本地引用 1 个、跨 Skill 引用 8 个全部解析。
- `check_package_manifest.py`：`All files: 2 | Clean: 2 | Caches: 0 | Unexpected: 0`、`QA Files (N): 2 | MATCH`、`RESULT PASS`、`MANIFEST_EXIT=0`。
- 哈希（均为追加本节前）：`SKILL.md` `8418a3d22523a8d06076799676bcb670b3f36117fbf0cfc67c3a85043a68ce64`；本文件 `429ca4ba2c6c51799763e7aaf6fc39142ac376e47c81923afe4272f938dd9ed0`。

### 分级与限制

- **已核实**：并发出现时间、写入者与确认消息、依赖脚本 HEAD/status/blame/哈希、两项审计输出与退出码、文件哈希、CR/BOM、跨 Skill 引用解析。
- **未验证**：HEAD 版本的实际执行、另一台机器或克隆的复现、写入者样例夹具的测试结果（未由本会话复跑）。
- 本节只绑定 2026-10-26 16:01:35 +01:00 的包快照；若后续测试或编辑改变文件，必须重做 Step 0–2 与两项审计，不能沿用本节哈希。

## 后续观察：Step 3 归档字节漂移与夹具落盘（2026-10-26）

本节由 2026-10-26 更新会话追加。来源为创建/测试会话 `3532d974-8dd9-4fde-9195-03abf7aa4333`（8 条消息，revision 562，`hasMoreBefore=false`，`runtimeState=ready`，`activeTurnId=null`）的工具输出，以及本机对保留夹具 `C:/Users/Administrateur/.qoder/tmp/qualify-skill-test-20261026T1605` 的独立复跑。旧节原文不改；本节只追加。

### 来源会话与用户指令

| 时间（UTC） | 用户消息 | 结果 |
|---|---|---|
| 2026-10-26T14:55:50Z | 创建请求（推荐 action=create，来源会话 `a6127096-…`） | 代理提出创建方案 |
| 2026-10-26T14:57:07Z | 「确认按此方案创建新 Skill」 | 写入 SKILL.md 与本文件初版 |
| 2026-10-26T15:02:22Z | `test the skill with a sample file` | 建立样例夹具并实测三类判定 |
| 2026-10-26T15:04:11Z | `commit the sample test fixture` | 外层提交 `759a53c`、`0e7565c` |

- 没有纠正性指令。两处失败均为代理测试中自行发现的环境陷阱，不是用户纠正。
- 工具输出时间为本机 +01:00；消息时间为 UTC。

### 已核实：归档 EOL 漂移（Step 3）

保留夹具上的本机复跑（2026-10-26 16:10–16:12 +01:00），`core.autocrlf=true`、`git 2.52.0.windows.1`：

| 取法 | 大小 | CR | SHA-256 | 行为 |
|---|---:|---:|---|---|
| 内层 `git show HEAD:audit_sample.py` | 663 B | 0 | `e09e8f48b03d610b25881615305d630264ceeac914a81f0daee5af070c22d396` | `RESULT FAIL` / exit 1 |
| 内层 `git archive HEAD \| tar -xO` | 685 B | 22 | `8d03180fb8000b14ac45928fa40c1b2c5579743468d9497567dd6f03afc24135` | `RESULT FAIL` / exit 1 |
| 外层 `git show 759a53c:repo/audit_sample.py` | 681 B | 0 | `018c1de157690d572f2c0b977a81e15cfb8455d9efc3d10d091455e6f236d1c1` | `RESULT PASS` / exit 0 |
| 外层 `git archive 759a53c repo/audit_sample.py \| tar -xO` | 703 B | 22 | `42bfd9f171e9ac93c4181078a38ca695572ac388f4310a773b201e25ddee514e` | `RESULT PASS` / exit 0 |
| 外层 `git show HEAD:repo/audit_sample.py` | 681 B | 0 | `018c1de157690d572f2c0b977a81e15cfb8455d9efc3d10d091455e6f236d1c1` | `RESULT PASS` / exit 0 |
| 外层 `git archive HEAD repo/audit_sample.py \| tar -xO` | 681 B | 0 | `018c1de157690d572f2c0b977a81e15cfb8455d9efc3d10d091455e6f236d1c1` | `RESULT PASS` / exit 0 |

- 外层夹具的 `repo/audit_sample.py` 是**工作区内容**（`cacheinfo` 提交的 blob `cc54435aadd1b4a4a2d1a8d5bfe4f7ff22079bbe`），所以 PASS；内层 HEAD 的旧内容在夹具交接中只由 `repo.bundle` 保留（`c6cbedf`），所以 FAIL。两者不可混用。
- `759a53c` 不含夹具根 `.gitattributes`；`HEAD`（`0e7565c`）含 `* text=auto eol=lf`，因此外层归档恢复为 681 B / CR=0。
- 报告文件同样漂移：blob 1638 B / CR=0 / `3e39a9169da6cc4cb68c7d506d7aa517c9ea54931a3a47792d0049deac0f91d3`；`archive 759a53c` 1668 B / CR=30 / `783d3dbd4bb283604675aece483bc4fef25e5a30cbc35f80c619f37e6aa74312`；`archive HEAD` 恢复为 1638 B / CR=0 / `3e39a916…`。
- 漂移只改变副本字节，不改变该脚本行为：内层 archive 副本（685 B）与字节精确的 `git show` 副本（663 B）都输出 `UNEXPECTED .gitattributes` / `RESULT FAIL` / exit 1。
- 来源会话在 Step 3 用的是内层 `git archive HEAD`，当时 `head_snapshot/audit_sample.py` 为 685 B、`HEAD_EXIT=1`；该次运行的字节不是 HEAD blob，但行为结论与字节精确复跑一致。

### 已核实：`git hash-object` 不能做字节断言

本机探针（2026-10-26 16:13 +01:00），14 B / 2 行 CRLF 文件：

| 命令 | 输出 |
|---|---|
| `git hash-object file` | `223ca50d99502c4cf15a026d366965225e573961`（等于 LF 版本的 blob） |
| `git hash-object --no-filters file` | `b4e31d45a6a970c70dbc92b5b432f46b5d3386d6`（CRLF 原始字节） |
| `git hash-object --stdin < file` | `b4e31d45a6a970c70dbc92b5b432f46b5d3386d6` |

- `hash-object` 默认应用 `core.autocrlf` 归一化；“与 HEAD 一致”只证明内容一致，不证明字节一致。字节断言用 `sha256sum` 或 `--no-filters`。

### 已核实：Step 1 的内容判定

本机对保留夹具的干净克隆（`git clone repo`）复跑：

- `status` 为空；`git diff --quiet` 与 `git diff --cached --quiet` 均退出 0。
- 检出为 CRLF：685 B、CR=22、SHA-256 `8d03180f…`；`git hash-object --path=audit_sample.py` = `d378285903ec2c06596c915133e82907c34593d3` = `git rev-parse HEAD:audit_sample.py`（内容一致）。
- 同一克隆直接 `sha256sum` 与 `git show HEAD:` 的 `e09e8f48…` 不同；若按旧规则“工作区哈希必须等于 HEAD 内容哈希”会把 `COMMITTED` 误判为 `WORKTREE_ONLY`。新规则用 `hash-object --path` + `git diff` 判内容，用 `sha256sum` 只判字节。
- 保留的脏工作区 `hash-object --path` = `cc54435a…`，HEAD blob = `d378285…`，内容不同，正确判 `WORKTREE_ONLY`。

### 已核实：嵌套仓库暂存与 bundle（Step 7）

来源会话 15:04–15:06 +01:00：

- `git add -f repo/audit_sample.py` 返回 0，`git status --short` 仍为 `?? repo/`；外层已暂存 9 个普通文件，内层 `repo/` 未被加入。
- `BLOB=$(git hash-object -w repo/audit_sample.py)` → `cc54435aadd1b4a4a2d1a8d5bfe4f7ff22079bbe`；`git update-index --add --cacheinfo 100644,$BLOB,repo/audit_sample.py` 后 `ls-files -s` 显示 `100644 cc54435a… 0 repo/audit_sample.py`，内层仍为 ` M audit_sample.py`。
- `git -C repo bundle create repo.bundle HEAD`：bundle 含 `c6cbedf673172ef857f7c628b3ac21d7e719b317 refs/heads/main` 与同 OID 的 `HEAD`；文件 755 B。
- 外层提交 `759a53c42658b2b3aba3dee793f6f56bd7f10f67`（10 文件、86 insertions），`0e7565c`（短哈希，新增夹具根 `.gitattributes`）；外层 `status` 为空，内层 ` M` 保留。
- 新克隆复核（验证后已删除）：外层 `repo/audit_sample.py` 681 B / `018c1de1…`、`RAPPORT` 1638 B / `3e39a916…`，与工作区一致；快照侧 `Files: 2 | Unexpected: 0` / `RESULT PASS` / `SNAPSHOT_EXIT=0`；bundle HEAD 侧 `c6cbedf` / `UNEXPECTED .gitattributes` / `RESULT FAIL` / `HEAD_EXIT=1`。
- 本机独立探针（16:13–16:14 +01:00）：`git add -f inner/a.py` 返回 0、`status` 仍为 `?? inner/`；`git add -f inner` 暂存 `160000` gitlink；`git rm --cached inner` 因 “staged content different from both the file and the HEAD” 失败，`git rm --cached -f inner` 成功且内层 HEAD 不变；随后 `hash-object` + `cacheinfo` 成功（`100644 7d4290a1… 0 inner/a.py`）。
- 来源会话的工具输出没有逐字保留 `git add -f` 命令本身，只保留其后的 `?? repo/` 与代理说明；上述命令行为由本机探针独立确认。

### 已核实：三类判定与管道陷阱

保留夹具/本机复跑（2026-10-26 16:12–16:14 +01:00）：

| 判定/场景 | 证据 | 结果 | 退出码 |
|---|---|---|---|
| `COMMITTED`（干净克隆内层 HEAD） | `status` 为空、`diff`/`diff --cached` 均 0、`hash-object --path` 等于 HEAD blob `d378285…` | `RESULT FAIL`、`UNEXPECTED .gitattributes` | 1 |
| `WORKTREE_ONLY`（保留的 ` M` 工作区） | `git diff` 白名单变更、`blame` 为 `Not Committed Yet` | `RESULT PASS` | 0 |
| HEAD 版本（字节精确 `git show`） | 663 B / `e09e8f48…` / blob `d378285…` | `RESULT FAIL` | 1 |
| HEAD 版本（archive 副本） | 685 B / CR=22 / `8d03180f…` | `RESULT FAIL` | 1 |
| `UNKNOWN`（夹具根之外的副本） | `rev-parse --show-toplevel` rc 128 | `RESULT PASS` | 0 |
| 管道陷阱 | `... \| tail -1` 显示 `RESULT FAIL`，但 `PIPED_RC=0` | 直接执行 `DIRECT_EXIT=1` | 0 |

- 夹具内的 `loose/audit_sample.py` 在外层仓库初始化后已属于该仓库（`rev-parse` rc 0），不再复现 `UNKNOWN`；复跑时必须把副本放到夹具根之外的空目录。
- 来源会话的 `COMMITTED` 基线（编辑前，`status` 为空、工作区/HEAD 均为 `e09e8f48…`）为 `RESULT FAIL` / `DEP_EXIT=1`；本机干净克隆复跑得到同一行为。该基线的“工作区哈希等于 HEAD 内容哈希”在 CRLF 检出（如新克隆）上不成立，但内容判定成立。

### 分级与限制

- **已核实**：来源会话消息时间线、归档/`git show` 的大小与哈希、`.gitattributes` 提交前后的差异、嵌套仓库暂存与 bundle、外层提交、新克隆哈希与双侧退出码、三类判定、管道陷阱、`hash-object` 归一化、gitlink 恢复、Step 1 内容判定。
- **源码推断**：本节没有执行主案例 `check_package_manifest.py` 的 HEAD 版本；主案例的 `UNEXPECTED`/exit 1 仍是源码推断。本节证据只覆盖样例夹具。
- **未验证**：第二台机器或第二个克隆的跨机器复现；真实依赖脚本的归档漂移（只在样例夹具上实测）；夹具内 `loose/` 的原始 `UNKNOWN` 条件已不可按原样复现。
- 本节追加前的包快照：SKILL.md 12467 B / `32e72a48a4fb3488752785987a6778a6d1dbfd02ec54c8411fad28f5aaab58f5`；本文件 9612 B / `506227a98d697b13fcbcba8ebc08a3c6f5756d11d91def21ea89c6773bf89435`。写入后的哈希与两项审计结果见本节末尾的“本次更新验收”。
- 本节只绑定 2026-10-26 16:14 +01:00 左右的夹具与观察；夹具或依赖状态变化后必须重做 Step 0–2 与两项审计，不能沿用本节哈希。

### 本次更新验收（2026-10-26 16:26–16:29 +01:00）

写入后重跑两项审计与夹具验收，全部为本机实际输出：

```text
Validator: read-only (skill files are not modified)
Stability: unchanged for 2.0s after 2.1s
Fingerprint (start): 18744 bytes | mtime=2026-10-26T16:26:32+01:00 | sha256=d87c0139d51129884e6b675b1fff9d0b7eee836473c8a0c142aef40e224743db
Files (2): SKILL.md, references/preuves-session-provenance.md
PASS layout: 2 file(s), no extraneous documentation
PASS frontmatter: YAML parsed (PyYAML 6.0.1)
PASS name: 'qualify-dependency-behavior-provenance' matches directory
PASS description: single line, 765 chars
PASS body: 261 lines (< 500)
PASS content: no TODO markers
PASS local references: 1 checked
PASS skill references: 8 checked (audit-evidence-count-provenance, audit-skill-tool-contracts, dependency-script-contract-reaudit, +5)
PASS fingerprint: unchanged during validation
Code blocks: python=0 js=0 skipped=10
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
QA_EXIT=0
```

```text
Skill: qualify-dependency-behavior-provenance
All files: 2 | Clean: 2 | Caches: 0 | Unexpected: 0
QA Files (N): 2 | MATCH on-disk total 2
RESULT PASS
MANIFEST_EXIT=0
```

- 第一次 QA 为 `RESULT FAIL`（`8 pass, 1 fail`）：校验器把正文中的 `` `repo/dep.py` `` 当作本地引用，而该文件不存在于 Skill 目录或工作区。将说明文字改为 `` `$FX/repo/dep.py` ``（命令中实际使用的变量路径）后复跑通过；依赖脚本与夹具均未修改。
- 夹具验收复跑（临时克隆位于 `C:/Users/Administrateur/.qoder/tmp/qualify-accept-20261026T1628`，结束后已删除）：

| 检查 | 结果 |
|---|---|
| `git show 759a53c:repo/audit_sample.py` | 681 B / CR=0 / `018c1de1…` |
| `git archive 759a53c` + `tar -xO` | 703 B / CR=22 / `42bfd9f1…`（字节漂移，行为不变） |
| `git show HEAD:repo/audit_sample.py` | 681 B / CR=0 / `018c1de1…` |
| `git archive HEAD` + `tar -xO` | 681 B / CR=0 / `018c1de1…`（`.gitattributes` 已提交） |
| 外层克隆 `repo/audit_sample.py` | `CLONE_RC=0`、`status` 为空、两侧 SHA-256 均为 `018c1de1…` |
| 快照侧运行 | `Files: 2 \| Unexpected: 0`、`RESULT PASS`、`SNAPSHOT_EXIT=0` |
| bundle HEAD 克隆 | `HEAD_CLONE_RC=0`、`UNEXPECTED .gitattributes`、`RESULT FAIL`、`HEAD_EXIT=1` |
| 清理 | `REMOVED` / `BASE_REMOVED` |

- 本小节追加后的固定值：`SKILL.md` 18744 B、CR=0、SHA-256 `d87c0139d51129884e6b675b1fff9d0b7eee836473c8a0c142aef40e224743db`（与 QA 指纹一致，本小节未改 SKILL.md）。
- 本文件在追加本小节前为 18925 B、CR=0、SHA-256 `013969a70ed55230aa71e565bc2bc051eb50ad615cbfab2028dd41242f06d925`；追加后哈希必然变化，以磁盘重算为准。两个文件均无 BOM、无 `__pycache__`/`.pyc`。
- 两项审计的 PASS 只覆盖结构与引用；夹具验收覆盖 Step 3 与 Step 7 的命令形态。跨机器复现仍为**未验证**。
