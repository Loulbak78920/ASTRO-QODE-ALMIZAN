# 案例：并发初始化 `.git` 后，`skill-file-qa` PASS 仍不代表已提交

日期：2026-10-26。时区：会话消息为 UTC；工具输出与文件系统为 `+01:00`。本文只记录可复核的字段；结论分为 **已核实**、**推断**、**未验证**。

## 1. 来源与取证方式

- 来源会话：`41be4eb3-19bb-4d46-8882-c96eb3986f62`，标题「创建静态检查器技能」。
- 原始日志：`C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/41be4eb3-19bb-4d46-8882-c96eb3986f62.jsonl`，309 行（`user` 56、`assistant` 112、其余为 attachment/active-leaf 等）。
- `read_chat_session` 快照：`revision=12`、`hasMoreBefore=false`、`runtimeState=running`，只含 4 条消息，最后一条在 `15:42:32Z`；**不包含** 16:38 之后的事件。因此本档案以 JSONL 为准，快照只用于确认会话身份与活跃状态。
- 用户输入只有两条：创建 Skill 的请求（`15:28:07Z`）与「提交这些修改到 Git」（`15:42:48Z`）。提交发生在第二条之后，**不是代理自行提交**。

## 2. 时间线（本地 +01:00）

| 时间 | 事件 | 证据 |
|---|---|---|
| 16:29 | 并行会话创建目标 Skill 目录 | 会话文本 |
| 16:34:54 | `SKILL.md` 9,473 B 版本被 QA 采样 | validator `Fingerprint (start)` |
| 16:38:54 | `.git` 初始化（config/HEAD/description/hooks 同秒） | `.git` 文件 mtime |
| 16:39:24 | 根提交 `51bdca5 Add develop-skill-static-checker skill` | `git log -1 %cI`、reflog 首行 |
| 16:39:43 | 代理做最小编辑 → `SKILL.md` 9,552 B / `230e7377…` | Edit 结果 + 指纹 |
| 16:41:15 | `skill-file-qa` `RESULT PASS`、`Files (3)` | 9 pass / 0 fail / 0 warn |
| 16:41:32 | 代理发现 `.git`，`status` 显示两个 ` M` | 未提交 |
| 16:42:48 | 用户明确要求提交 | 用户消息 |
| 16:43:06 | 提交 `284dc90`，blob 与工作区 `MATCH` | 字节 9,552 / `230e7377…` |

## 3. 逐字证据

### 3.1 QA PASS 与提交状态无关（16:41:15）

```text
Fingerprint (start): 9552 bytes | mtime=2026-10-26T16:39:43+01:00 | sha256=230e7377101cf6cfcbe5dbb630624b7fb605f33aa92bd2fce6034ee938ce0e4b
Skill: develop-skill-static-checker
Files (3): SKILL.md, references/cas-static-checker-2026-10-26.md, scripts/checker_matrix.py
PASS layout: 3 file(s), no extraneous documentation
PASS fingerprint: unchanged during validation
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
```

`Files (3)` 不含 `.git`，整段输出没有出现任何提交号或分支名。此时 `.git` 已存在约 2 分 21 秒。

### 3.2 `.git` 在文件快照之后出现

```text
16:38:54.2289480000       73 .git/description
16:38:54.2314734000      478 .git/hooks/applypatch-msg.sample
...
16:38:54.2809726000      130 .git/config
16:38:54.2865888000       21 .git/HEAD
16:39:11.3612281000        0 .git/objects/35
```

仓库 `.git/config` 只有 `core.*` 默认项，**没有** `core.autocrlf`。

### 3.3 首提交与未提交编辑

```text
51bdca5 (HEAD -> main) Add develop-skill-static-checker skill
 M SKILL.md
 M references/cas-static-checker-2026-10-26.md
SKILL.md
references/cas-static-checker-2026-10-26.md
scripts/checker_matrix.py
```

首提交包含三文件（`1009 insertions`），但代理在 16:39:43 的编辑不在其中。

### 3.4 `git diff` 的 EOL 警告不是差异

```text
warning: in the working copy of 'SKILL.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'references/cas-static-checker-2026-10-26.md', LF will be replaced by CRLF the next time Git touches it
 SKILL.md                                    | 2 +-
 references/cas-static-checker-2026-10-26.md | 9 +++++----
 2 files changed, 6 insertions(+), 5 deletions(-)
```

同一时刻：

```text
i/lf    w/lf    attr/                 	SKILL.md
i/lf    w/lf    attr/                 	references/cas-static-checker-2026-10-26.md
i/lf    w/lf    attr/                 	scripts/checker_matrix.py
```

索引与工作区都是 LF，`attr` 列为空；警告描述的是 `core.autocrlf=true` 下的**未来**检出。本案的仓库配置没有该项，值来自系统配置（见 §4.2）。

### 3.5 明确要求提交后，blob 与工作区逐字节一致

```text
MATCH 9552 230e7377101cf6cfcbe5dbb630624b7fb605f33aa92bd2fce6034ee938ce0e4b SKILL.md
MATCH 9586 1886ccdfb0e6d986dc772853144bacac6b7b7fa80bf7fa2f1e527d8ddb5d2d7b references/cas-static-checker-2026-10-26.md
MATCH 17776 56da149c6f9c34e4865b2596863a4c8dcda34e58fc8e1506cf7cf6edf354760f scripts/checker_matrix.py
```

## 4. 纠正

### 4.1 「`.git` 16:39 后出现」不准确

代理当时的自述与文件系统不符：初始化是 `16:38:54`；`16:39:11` 只是对象目录写入；根提交的 committer 时间是 `16:39:24`（本次用 `git log -1 --format=%cI` 复测）。规则：仓库年龄用 reflog 首行、根提交时间与 `.git/HEAD` ctime 取证，不用「我注意到的时间」。

### 4.2 `core.autocrlf` 可能来自仓库之外

案例仓库的 `.git/config` 没有该项，但 `git diff` 打印了转换警告。夹具实测：

```text
$ git config --show-origin --get-all core.autocrlf
file:C:/Program Files/Git/etc/gitconfig	true
```

只看局部配置会把风险漏掉。

## 5. 夹具矩阵（本次创建 Skill 时实测）

全部在 `~/.qoder/tmp` 下的一次性仓库中执行，结束后删除；断言按退出码与关键输出行。F1–F14 为创建时实测；F15–F17 为同日后续审计补充（见 §8.3）。

| 编号 | 夹具 | 期望 | 实测 |
|---|---|---|---|
| F1 | 干净仓库 | `0` / `RECONCILED` | 通过 |
| F2 | 提交后编辑 | `1` / `WORKTREE_ONLY` + `HEAD_PREDATES_DISK` | 通过 |
| F3 | 编辑并 `git add` | `1` / `STAGED_ONLY` | 通过 |
| F4 | 未跟踪文件 | `1` / `UNTRACKED_PRESENT` | 通过 |
| F5 | 删除已跟踪文件 | `1` / `DELETED_ON_DISK` | 通过 |
| F6 | 仅 `__pycache__` 被忽略 | `0` / `RECONCILED` + `IGNORED` | 通过 |
| F7 | Skill 是仓库子目录 | `0` / `PREFIX: skill/`，`FILES: 2` | 通过 |
| F8 | 非仓库目录 | `1` / `NO_REPO` | 通过 |
| F9 | 目录不存在 | `2` | 通过 |
| F10 | 记录哈希错误 | `1` / `DISK_CHANGED_SINCE_EXPECT` | 通过 |
| F11 | 对未跟踪文件绑定 | `1` / `NOT_AT_HEAD` | 通过 |
| F12 | 只 `init` 未提交 | `1` / `NO_COMMITS` | 通过 |
| F13 | `autocrlf=true`，检出 CRLF | `0` / `EOL_BYTE_DIFF` + `MATCH_CONTENT_EOL_DIFF` | 通过 |
| F14 | 真实仓库运行脚本 | `.git/index` 的 `mtime_ns` 与 size 不变 | 通过 |
| F15 | linked worktree（根 `.git` 是文件） | `0` / `RECONCILED`，`FILES: 1`，无 `UNTRACKED .git` | 通过 |
| F16 | 提交后继续编辑，传入已提交字节的 SHA-256 | `1` / `DISK_CHANGED_SINCE_EXPECT` + `HEAD: HEAD_MATCH_BYTES` | 通过 |
| F17 | 运行前后 `.git/index` 快照（真实仓库 + F2/F12/F13/F15/F16） | 每次 `INDEX_UNCHANGED: True` | 通过 |

### 5.1 F2 逐字输出（节选）

```text
HEAD: 14e6ee87f607cb2e93992a87a828f2887d471365
HEAD_TIME: 2026-10-26T16:50:50+01:00
REFLOG_FIRST: 2026-10-26T16:50:50+01:00 (commit (initial): seed)
REPO_CREATED_HINT: 2026-10-26T16:50:49+01:00 (.git/HEAD ctime; Windows=creation, POSIX=inode change)

FILES: 1 (head=1, index=1, disk=1)
DIVERGENT: 1  RECONCILED_FILES: 0  IGNORED: 0
WORKTREE_ONLY SKILL.md head=78981922613b index=78981922613b work=61780798228d
  detail=unstaged edit on_disk=True disk_sha256=026382...9813f head_sha256=87428f...f25c7 eol=i/lf w/lf attr/ mtime=2026-10-26T16:50:52+01:00

FLAG: HEAD_PREDATES_DISK (HEAD commit is older than the newest package file: edits are uncommitted)
FLAG: AUTOCRLF_TRUE (a future checkout may rewrite line endings)
VERDICT: WORKTREE_DIVERGES
RESULT DIVERGES
```

### 5.2 F13 逐字输出（节选）

```text
SAME SKILL.md head=422c2b7ab3b3 work=422c2b7ab3b3 disk_sha256=58055bdc...a0cab eol=i/lf w/crlf attr/ (byte-diff vs blob)

EXPECT SKILL.md: MATCH_CONTENT_EOL_DIFF content_oid=422c2b7ab3b3 blob_sha256=911169dd...9a2

FLAG: EOL_BYTE_DIFF (content OIDs match but blob and worktree bytes differ; checkout normalization)
VERDICT: RECONCILED
RESULT RECONCILED
```

工作区文件 6 字节、CR=2；`hash-object --path` 仍等于 HEAD OID。**内容相同不等于字节相同**。

### 5.3 索引副作用与提交顺序（独立实测）

| 命令 | 是否重写 `.git/index` |
|---|---|
| `git status --porcelain` | 是 |
| `git --no-optional-locks status --porcelain` | 否 |
| `git diff --stat` | 是 |
| `git --no-optional-locks diff --stat` | 否 |
| `git diff --cached` / `--check`（带 `--no-optional-locks`） | 否 |
| `git ls-files -s` / `--eol` | 否 |
| `git rev-parse` / `show` / `cat-file` / `hash-object` / `log` | 否 |

上表是单次夹具结果，不能推广为「每次都会写」。本轮复测表明普通 `status`/`diff` 的写入是**条件性**的（仅 stat 过期时），见 §8.1。

另一个夹具：先编辑文件，再 `git init` + `git add -A` + `git commit`，得到 `status` 为空、但提交时间晚于文件 mtime。结论：**干净 status 不证明验证发生在提交之前**。

## 6. 结论分级

| 结论 | 级别 | 依据 |
|---|---|---|
| `.git` 在 16:38:54 初始化 | 已核实 | `.git/*` 同秒 mtime |
| 根提交 `51bdca5` 于 16:39:24 创建 | 已核实 | `%cI` + reflog 首行 |
| 代理编辑在首提交之后、未提交 | 已核实 | `status` 两行 ` M` + 时间线 |
| QA PASS 不覆盖提交状态 | 已核实 | `Files (3)` 与输出无提交号 |
| autocrlf 来自系统配置 | 已核实（夹具） | `--show-origin` 输出 |
| 普通 `status`/`diff` 重写索引 | 已核实（夹具） | 索引 `mtime_ns` 变化 |
| 同一结论的适用范围 | 已核实（补充） | 仅 stat 过期时发生；内容变化场景未复现，见 §8.1 |
| 内容 OID 相等而字节不等 | 已核实（夹具） | F13 输出 |
| 提交顺序可由 mtime 推断 | **推断** | mtime 可被复制/归档保留 |
| POSIX 上 `.git/HEAD` ctime 的语义 | 未验证 | 仅在 Windows 实测 |
| linked worktree 的 `.git` 文件与索引位置 | 已核实（夹具，见 §8.3） | F15 输出 |
| submodule 的索引位置 | 未验证 | 未构造 |
| 合并冲突、重命名、非 ASCII 路径 | 未验证 | 未构造对应夹具 |
| 脚本运行期间被并发改写 | 未验证 | 运行前后索引快照只能事后发现变化 |

## 7. 复跑

脚本：`scripts/head_vs_worktree.py`。真实仓库复跑：

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/verify-skill-git-head-vs-worktree/scripts/head_vs_worktree.py" \
  "C:/Users/Administrateur/.qoder/skills/develop-skill-static-checker" \
  --expect-sha256 "SKILL.md=230e7377101cf6cfcbe5dbb630624b7fb605f33aa92bd2fce6034ee938ce0e4b"
```

本案仓库在 `284dc90` 上仍可复现 `RECONCILED` 与 `MATCH_BYTES`；若仓库后续增加提交，该哈希可能不再等于 HEAD，这属于预期结果，不是脚本漂移。

夹具未保存为常驻脚本；上表的仓库构造与断言（`git init`、写入、`git add`、`git commit`、`git checkout --` 制造 CRLF）可逐项重建。本文件自身的 SHA-256 由交付报告记录，避免自指。

## 8. 同日后续审计（2026-10-26 17:01 +01:00）

本节是对交付包的第二轮只读验收，补充并限定前文。前文的原始测量保留不改；凡与本轮冲突处，以本节为准。

### 8.1 索引副作用是条件性的

§5.3 的表格记录的是该次夹具的结果，不能推广为「普通 `status`/`diff` 每次都会写索引」。本轮复测：

- touch-only（只改 mtime、不改内容）后执行普通 `git status --porcelain`，`.git/index` 的 `mtime_ns` 发生变化。
- 内容变化后执行普通 `status` 与 `git diff --stat`，多次运行均未复现索引重写。

因此 SKILL.md 的措辞从「都会重写」改为「在需要刷新 stat 时**可能**重写」。脚本仍完全不调用 `status`/`diff`，并新增运行前后 `size`、`mtime_ns`、SHA-256 快照，输出 `INDEX_UNCHANGED`。

### 8.2 `--no-optional-locks` 是全局选项

放在子命令之后会失败：

```text
$ git status --porcelain --no-optional-locks
error: unknown option `no-optional-locks'
（退出码 129）
```

正确位置：

```text
$ git -C "<root>" --no-optional-locks status --porcelain=v1
（退出码 0）
```

### 8.3 新增夹具 F15–F17

F15 逐字输出（节选，路径替换为 `<tmp>`）：

```text
GIT_DIR: <tmp>/f15-main/.git/worktrees/f15-linked [file (linked worktree/submodule)]
FILES: 1 (head=1, index=1, disk=1)
DIVERGENT: 0  RECONCILED_FILES: 1  IGNORED: 0
VERDICT: RECONCILED
INDEX: <tmp>/f15-main/.git/worktrees/f15-linked/index size=137 mtime_ns=... sha256=...
INDEX_UNCHANGED: True
```

该夹具同时复现 `FLAG: EOL_BYTE_DIFF`：全局 `core.autocrlf=true` 使 linked worktree 检出 CRLF，内容 OID 仍等于 HEAD。若脚本未排除根 `.git` 文件，包清单会变成 2 个文件并报 `UNTRACKED .git`；本轮输出为 `FILES: 1`，证明排除生效。

F16 逐字输出（节选，路径替换为 `<tmp>`）：

```text
EXPECT SKILL.md: DISK_CHANGED_SINCE_EXPECT expected=e4eb6585... disk=9b8c2813...
  HEAD: HEAD_MATCH_BYTES (head=5529cfca3d2b)
FLAG: HEAD_PREDATES_DISK (HEAD commit is older than the newest package file: edits are uncommitted)
VERDICT: WORKTREE_DIVERGES+EXPECT_MISMATCH
INDEX_UNCHANGED: True
```

判据：记录值等于 HEAD blob 字节、不等于当前磁盘字节，说明「QA 验证过的那一版已提交，但工作区随后又被改动」。反向夹具 F10（传入全零哈希）得到 `HEAD: HEAD_MISMATCH`，证明该行不是恒真。

F17 在真实仓库与 F2、F12、F13、F15、F16 上断言 `INDEX_UNCHANGED: True`；真实仓库输出：

```text
INDEX: C:\Users\Administrateur\.qoder\skills\develop-skill-static-checker\.git\index size=404 mtime_ns=1793029386736726500 sha256=437084dd8f657c89440a9658f2956344270a489287171f9abe51ca4093ac834a
INDEX_UNCHANGED: True
```

### 8.4 脚本行为变更（相对 §5）

- `walk_package()` 跳过 Skill 根下的 `.git` **文件**，不再把 linked worktree 的 `.git` 计入包文件。
- 新增 `snapshot_index()` / `describe_index()` / `finish()`：在任何树/索引读取之前与结束前各取一次索引快照，输出 `INDEX:` 与 `INDEX_UNCHANGED:`。
- `--expect-sha256` 在 `DISK_CHANGED_SINCE_EXPECT` 与 `FILE_MISSING` 时追加 `HEAD:` 行，独立回答记录值是否在 HEAD；不再因磁盘不匹配而停止回答该问题。
- `describe_head()` 只声明 `HEAD_MATCH_BYTES` 或 `HEAD_MISMATCH`：只有字节哈希能与 HEAD blob 直接比对；磁盘已变时无法仅凭 OID 推断记录值的行尾形态。

### 8.5 本轮验证范围

同一夹具矩阵共 42 条断言，全部通过：F2（未暂存编辑）、F3（已暂存）、F5（磁盘删除）、F4（未跟踪）、F6（仅缓存被忽略）、F8（非仓库）、F12（只 init）、F10（记录哈希错误）、F16（磁盘已变仍绑定 HEAD）、F15（linked worktree）、F13（CRLF 检出）。F1、F7、F9、F11、F14 未在本轮重跑，仍以 §5 的记录为准。

另有一项独立夹具（不计入 42 条）：提交后删除文件，再绑定已提交字节的 SHA-256，得到 `FILE_MISSING` + `HEAD: HEAD_MATCH_BYTES`、退出码 1、`INDEX_UNCHANGED: True`。

## 9. HEAD 指针案例（来源会话 324c8787，2026-10-26）

### 9.1 来源与样本

- 会话 `324c8787-9642-4d4e-a16c-2cf4834fb20c`，标题「更新 LF endings 技能」；被检查的仓库是 `C:/Users/Administrateur/.qoder/skills/lock-lf-endings-skill-repo`，不是本 Skill 自己的仓库。
- 用户原话（0-based `records[597]`，`2026-10-26T16:35:13Z` = `17:35:13+01:00`）：`验证 Skill 仓库的 HEAD 指针`。
- 下一轮用户消息（`records[636]`，`16:36:39Z`）是新请求「提交本次验证结果到日志」，不是对指针结论的纠正。该回合内没有用户纠正。
- 读取来源时 `read_chat_session` 快照为 `revision=14`、`hasMoreBefore=false`、`runtimeState=running`；写入本节前直接解析项目 JSONL，文件 847 行，`records[597]` 仍为该用户回合。会话在指针回合之后仍继续提交与 PR 操作，行数会继续增长，引用以记录序号与原文为准。
- 代理的处理顺序是：先跑本 Skill 的脚本做工作区对账，再手工补指针命令，最后单独读取 `.git/HEAD`。也就是说，当时的脚本本身还不检查指针。

以下 `<repo>` 代表 `C:/Users/Administrateur/.qoder/skills/lock-lf-endings-skill-repo`，`<skill>` 代表本 Skill 的安装目录；命令只为排版换行，参数与输出逐字。

### 9.2 脚本对账（指针检查之前）

```bash
py -3 "<skill>/scripts/head_vs_worktree.py" "<repo>" \
  --expect-sha256 "SKILL.md=d7aa51b70ef970c87fb6d4aaf451b4e6aa964ae15b3e63feb1aa8ec5cfe4ac8c" \
  --expect-sha256 "references/preuves-session-lf.md=cc8ff90d724c0fabcd7b9f361332f2bf524480ce7c82c83b6ff25525d1d55ad4"
```

关键输出（逐字）：

```text
HEAD: 76a011d63f1abe62daae0d6ec6246cbd49966822
HEAD_TIME: 2026-10-26T16:40:57+01:00
HEAD_SUBJECT: fix(skill): controler les octets de .gitattributes avant commit
AUTOCRLF: file:C:/Program Files/Git/etc/gitconfig=true

FILES: 3 (head=3, index=3, disk=3)
DIVERGENT: 0  RECONCILED_FILES: 3  IGNORED: 0

EXPECT SKILL.md: MATCH_BYTES (HEAD blob bytes == recorded SHA-256)
EXPECT references/preuves-session-lf.md: MATCH_BYTES (HEAD blob bytes == recorded SHA-256)

FLAG: AUTOCRLF_TRUE (a future checkout may rewrite line endings)
VERDICT: RECONCILED
RESULT RECONCILED
INDEX_UNCHANGED: True
EXIT=0
```

`RECONCILED` 只回答「三个包文件内容等于 HEAD」，没有回答 HEAD 是否是分支、是否指向 commit、reflog 是否一致。该回合剩下的问题必须另行取证。

### 9.3 手工指针证据（逐字）

```bash
R="<repo>"
git -C "$R" symbolic-ref HEAD
git -C "$R" rev-parse HEAD 'HEAD^{commit}' 'HEAD^{tree}'
git -C "$R" rev-parse refs/heads/main
git -C "$R" cat-file -t HEAD
git -C "$R" for-each-ref --format='%(refname) %(objectname) %(objecttype)' refs/heads
git -C "$R" ls-tree -r HEAD
git -C "$R" rev-parse --is-shallow-repository
git -C "$R" worktree list --porcelain
git -C "$R" reflog -3 --format='%H %gd %gs'
```

输出（逐字）：

```text
refs/heads/main
76a011d63f1abe62daae0d6ec6246cbd49966822
76a011d63f1abe62daae0d6ec6246cbd49966822
7ff48892085917771fcc7b954e13f89da5e08383
76a011d63f1abe62daae0d6ec6246cbd49966822
commit
refs/heads/main 76a011d63f1abe62daae0d6ec6246cbd49966822 commit
100644 blob c8950c1f1fb583eb1aa4ce93fc24f997064130f4	.gitattributes
100644 blob 523e9cd608924582c2f59af8f457c44d5d2ce3d4	SKILL.md
100644 blob 6b4818170a63241a343ec8c7f5670be29d8c57e0	references/preuves-session-lf.md
false
worktree <repo>
HEAD 76a011d63f1abe62daae0d6ec6246cbd49966822
branch refs/heads/main

76a011d63f1abe62daae0d6ec6246cbd49966822 HEAD@{0} commit: fix(skill): controler les octets de .gitattributes avant commit
e6a6e5f66e4817c92bd03957a1b67867e5c9a6b8 HEAD@{1} commit: fix(skill): corriger l'audit manifest des fins de ligne LF
a388c2489613b4b2eadc4d3ff418dce422dc8ff7 HEAD@{2} commit: feat(skill): encadrer le commit autorise et la verification post-commit
```

代理还打印了提交作者与提交时间；时间与脚本的 `HEAD_TIME` 一致，作者字段不在本档案复制。

### 9.4 `.git/HEAD` 的字节形态

Read 工具输出（行号由工具添加）：

```text
1	ref: refs/heads/main
2	
```

即文件内容为 `ref: refs/heads/main\n`，是符号引用，不是 detached 的裸 OID。该文件位于 `<repo>/.git/HEAD`；本轮不是 linked worktree，所以没有落在 `.git/worktrees/<name>/HEAD`。

### 9.5 判定与证据强度

| 结论 | 级别 | 依据 |
|---|---|---|
| 该回合时 HEAD 指向 `refs/heads/main` | 已核实 | `.git/HEAD` 原文 + `symbolic-ref` |
| HEAD 解析为 commit `76a011d`，树 `7ff4889`，3 个 blob 可读 | 已核实 | `rev-parse HEAD^{commit}`、`cat-file -t`、`ls-tree -r` |
| 目标分支 ref 当时等于 HEAD | 已核实，但**单独不构成强证据** | `rev-parse refs/heads/main`；稳定符号 HEAD 下这是同一次读取的另一种写法，只能发现并发移动或损坏 |
| reflog 末条与 HEAD 一致 | 已核实 | `HEAD@{0}` = `76a011d` |
| 非 shallow、单一 worktree | 已核实 | `--is-shallow-repository=false`、`worktree list` 一条 |
| 工作区 3 个文件等于 HEAD，两个指纹均 `MATCH_BYTES` | 已核实 | 脚本 `RESULT RECONCILED` |
| 「磁盘已验证版本就是提交 76a011d」 | 已核实（限定于该时刻） | 上述两项合取；17:40:46 后不成立，见 §9.6 |
| 脚本当时能独立给出 `HEAD_POINTER` | **不成立** | 当时脚本无指针块；判定来自手工命令与一次 Read |
| 指针与工作区是两个独立结论 | 设计原则，已由本轮实现验证 | §10 的 `HEAD_POINTER` 与 `RESULT` 分行；T7 显示指针失败会改变退出码 |

代理当时的结论句是：

```text
结论：HEAD 指针、目标分支引用、提交对象与工作区完全一致；磁盘已验证版本就是提交 `76a011d`。
```

该句在指针检查时刻（`17:35–17:36+01:00`）成立；`17:40:46+01:00` 的新提交 `9024d7d` 改变了 HEAD，使「就是 76a011d」过期。教训不是当时判断错误，而是**结论必须绑定到具体 commit**，并在下一次提交后重新绑定指纹。

### 9.6 同一文件在两个 commit 上的绑定漂移

用户要求把验证结果写入日志后，源会话向 `references/preuves-session-lf.md` 追加了 19 行并提交：

```text
9024d7d3229e8635832cbc7e5775268e649c5d1a 76a011d63f1abe62daae0d6ec6246cbd49966822 docs(skill): consigner la verification HEAD du 2026-10-26
```

- 追加前：`references/preuves-session-lf.md` 字节 SHA-256 = `cc8ff90d724c0fabcd7b9f361332f2bf524480ce7c82c83b6ff25525d1d55ad4`，blob `6b4818170a63...`，当时等于 HEAD。
- 追加后：磁盘字节 SHA-256 = `f4c5ac7d0eeafeb4facdfa9179fee5d8f8273ec5a7d90c6efc161b1fe8bc0bce`，blob `e011d55c2d2b...`，成为新 HEAD 的一部分。

用**旧**指纹在新 HEAD 上复跑：

```text
EXPECT references/preuves-session-lf.md: DISK_CHANGED_SINCE_EXPECT expected=cc8ff90d724c0fabcd7b9f361332f2bf524480ce7c82c83b6ff25525d1d55ad4 disk=f4c5ac7d0eeafeb4facdfa9179fee5d8f8273ec5a7d90c6efc161b1fe8bc0bce
  HEAD: HEAD_MISMATCH (head=e011d55c2d2b blob_sha256=f4c5ac7d0eeafeb4facdfa9179fee5d8f8273ec5a7d90c6efc161b1fe8bc0bce)
FLAG: AUTOCRLF_TRUE (the effective core.autocrlf may rewrite line endings on checkout)
VERDICT: EXPECT_MISMATCH
RESULT DIVERGES
```

用**当前**指纹复跑：

```text
EXPECT SKILL.md: MATCH_BYTES (HEAD blob bytes == recorded SHA-256)
EXPECT references/preuves-session-lf.md: MATCH_BYTES (HEAD blob bytes == recorded SHA-256)
VERDICT: RECONCILED
RESULT RECONCILED
INDEX_UNCHANGED: True
```

`HEAD: HEAD_MISMATCH` 在这里不是脚本漂移：旧指纹描述的是追加日志**之前**的版本，新提交把它换掉了。反过来，旧指纹的 `disk` 与新 HEAD 的 `blob_sha256` 都是 `f4c5ac7d...`，说明磁盘与 HEAD 一致，只是与记录值不一致。**QA 指纹只对产生它的那一版负责；提交后必须重新绑定。**

## 10. 本次更新与验证（2026-10-26 18:00 +01:00）

本节记录给本 Skill 增加 HEAD 指针判定后的验收。下表是追加 §9/§10 前的快照：

| 文件 | 字节 | SHA-256（前缀） |
|---|---|---|
| `SKILL.md` | 20,803 | `3bafbc864f990506044bb552116b387f6d1716ea2cb11985f98bd145e018a55e` |
| `scripts/head_vs_worktree.py` | 29,713 | `ab968c5a1071ae278b8cadece5e8bba13725f397b563a21c130fcecc5fdc8ba7` |
| `references/cas-git-head-vs-worktree-2026-10-26.md` | 15,273 | `2a0f4f2e76c9cd18f43c1a9ff26513192cb638d8964106e1ab4ce32916a457b4` |

追加本节后，`SKILL.md` 又做了两处措辞修正（只读命令清单、指针判定优先级），未改脚本或夹具。最终 `SKILL.md` 为 21,232 B、298 行（validator 正文 294 行）、SHA-256 `2068bad78a58405a2ab88f0de62436bdcfa62b2c15489414c96b77b1d77ec57b`；`name` 与目录一致；`description` 单行 876 字符。最终的 `skill-file-qa` 在修正后重跑，`RESULT PASS`、9 pass / 0 fail / 0 warn。`references` 的最终哈希由交付报告记录，避免自指。

### 10.1 变更内容

- `SKILL.md`：新增 §3「核对 HEAD 指针（独立于工作区对账）」；目标从三个问题扩为四个；硬规则新增第 8 条（指针与工作区必须分开报告）与第 9 条（指针异常也只读）；报告模板加入 `Pointer :` 行；错误对照与检查清单加入 detached、目标 ref 缺失/不一致、非 commit 对象、shallow、多 worktree、reflog 不可用/不一致；资源说明同步。
- `scripts/head_vs_worktree.py`：新增 `collect_pointer()` 与 `print_pointer()`，输出 `POINTER_HEAD_FILE`、`POINTER_HEAD_CONTENT`、`POINTER_SYMBOLIC_REF`、`POINTER_TARGET`、`POINTER_OBJECT`、`POINTER_TREE`、`POINTER_REFLOG_LATEST`、`POINTER_SHALLOW`、`POINTER_WORKTREES`、`HEAD_POINTER`；新增 `HEAD_DETACHED`、`SHALLOW_REPO`、`REFLOG_LATEST_MISMATCH`、`REFLOG_UNAVAILABLE`、`HEAD_REF_MISMATCH`、`MULTIPLE_WORKTREES` 标记。
- 退出码保持工作区驱动：`HEAD_POINTER` 为 `DETACHED`/`REF_MISMATCH`/`UNBORN` 时不改变对账退出码；只有 `HEAD_OBJECT_INVALID` 直接返回 1。
- 修正 `core.autocrlf` 的有效值判定：`--show-origin --get-all` 可能返回 system → global → local/worktree 多行，旧代码只要任意一行是 `true` 就报 `AUTOCRLF_TRUE`；现在只按最后一行（有效值）判断。该缺陷由 T1 夹具暴露：局部 `false` 覆盖全局 `true` 时曾被误报。

### 10.2 夹具矩阵

夹具根为 `C:/Users/Administrateur/.qoder/tmp/head-pointer-fixtures-20261026`，每个用例是独立的一次性仓库；结束后按记录删除。共 63 条断言，`CHECKS=63 FAILURES=0`。所有实际执行脚本的夹具（T1–T4、T6–T8）均断言 `INDEX_UNCHANGED: True`。

| 编号 | 构造 | 期望 | 实测 |
|---|---|---|---|
| T1 | 干净仓库，本地 `core.autocrlf=false` | `HEAD_POINTER: OK`、`RESULT RECONCILED`、`FLAG: NONE`、退出 0 | 通过 |
| T2 | `checkout --detach` | `HEAD_POINTER: DETACHED`、`FLAG: HEAD_DETACHED`、工作区仍 `RECONCILED`、退出 0 | 通过 |
| T3 | 从 `file://` 源 `clone --depth 1` | `POINTER_SHALLOW: true`、`FLAG: SHALLOW_REPO`、指针 `OK`、退出 0 | 通过 |
| T4 | 删除 `.git/logs` | `POINTER_REFLOG_LATEST: unavailable`、`FLAG: REFLOG_UNAVAILABLE`、指针仍 `OK`、退出 0 | 通过 |
| T5 | 单元级 `FakeGit`：HEAD `aaaa…`、目标 ref `bbbb…` | `HEAD_POINTER: REF_MISMATCH` | 通过；T5b 稳定目标为 `OK`、T5c reflog 不一致不改变指针判定、T5d detached、T5e object invalid |
| T6 | `git worktree add -b wt` | `GIT_DIR` 在 `.git/worktrees/...`；`POINTER_WORKTREES: 2`；`HEAD_POINTER: OK`；退出 0 | 通过 |
| T7 | 把 `refs/heads/main` 指向一个 tree 对象 | `POINTER_OBJECT: tree`、`HEAD_POINTER: OBJECT_INVALID`、`VERDICT: HEAD_OBJECT_INVALID`、`RESULT DIVERGES`、退出 1 | 通过 |
| T8 | `git init` 未提交 | `HEAD_POINTER: UNBORN`、`VERDICT: NO_COMMITS`、退出 1 | 通过 |

T6 逐字输出（节选，路径替换为 `<tmp>`）：

```text
GIT_DIR: <tmp>/T6-main/.git/worktrees/T6-linked [file (linked worktree/submodule)]
BRANCH: wt
HEAD: f78c1523db17d5c689e00e6e4f03c9170743d548
POINTER_HEAD_FILE: <tmp>/T6-main/.git/worktrees/T6-linked/HEAD
POINTER_HEAD_CONTENT: ref: refs/heads/wt
POINTER_SYMBOLIC_REF: refs/heads/wt
POINTER_TARGET: refs/heads/wt f78c1523db17 MATCH
POINTER_OBJECT: commit
POINTER_TREE: 53105bf7e554e0d217120693a20a9005e4e4761c entries=1
POINTER_REFLOG_LATEST: HEAD@{0} f78c1523db17 MATCH reset: moving to HEAD
POINTER_SHALLOW: false
POINTER_WORKTREES: 2 [<tmp>/T6-main ; <tmp>/T6-linked (current)]
HEAD_POINTER: OK
RESULT RECONCILED
INDEX_UNCHANGED: True
```

这条证明 `.git/HEAD` 的读取走的是 `rev-parse --git-path HEAD`，在 linked worktree 中会落到工作区专属目录，而不是仓库根的 `.git/HEAD`。

T7 逐字输出（节选，路径替换为 `<tmp>`）：

```text
HEAD: 53105bf7e554e0d217120693a20a9005e4e4761c
POINTER_HEAD_CONTENT: ref: refs/heads/main
POINTER_SYMBOLIC_REF: refs/heads/main
POINTER_TARGET: refs/heads/main - MISSING
POINTER_OBJECT: tree
POINTER_TREE: - entries=0
HEAD_POINTER: OBJECT_INVALID
VERDICT: HEAD_OBJECT_INVALID
RESULT DIVERGES
INDEX_UNCHANGED: True
```

T3 与 T8 的关键行：

```text
# T3
POINTER_SHALLOW: true
FLAG: SHALLOW_REPO (root commit and history are incomplete)
HEAD_POINTER: OK

# T8
POINTER_TARGET: refs/heads/main - UNBORN
POINTER_OBJECT: UNRESOLVED
HEAD_POINTER: UNBORN
VERDICT: NO_COMMITS
RESULT NO_COMMITS
```

### 10.3 真实仓库复跑

对象仍是 `lock-lf-endings-skill-repo`，当前 HEAD 已变为 `9024d7d`（`76a011d` 的子提交）。用当前指纹绑定：

```text
HEAD: 9024d7d3229e8635832cbc7e5775268e649c5d1a
POINTER_HEAD_FILE: C:\Users\Administrateur\.qoder\skills\lock-lf-endings-skill-repo\.git\HEAD
POINTER_HEAD_CONTENT: ref: refs/heads/main
POINTER_SYMBOLIC_REF: refs/heads/main
POINTER_TARGET: refs/heads/main 9024d7d3229e MATCH
POINTER_OBJECT: commit
POINTER_TREE: 1bdf9a20400e75fb708e9aa8410bc425c9f5911e entries=3
POINTER_REFLOG_LATEST: HEAD@{0} 9024d7d3229e MATCH commit: docs(skill): consigner la verification HEAD du 2026-10-26
POINTER_SHALLOW: false
POINTER_WORKTREES: 1 [C:/Users/Administrateur/.qoder/skills/lock-lf-endings-skill-repo (current)]
HEAD_POINTER: OK
HEAD_TIME: 2026-10-26T17:40:46+01:00
HEAD_SUBJECT: docs(skill): consigner la verification HEAD du 2026-10-26

FILES: 3 (head=3, index=3, disk=3)
DIVERGENT: 0  RECONCILED_FILES: 3  IGNORED: 0

EXPECT SKILL.md: MATCH_BYTES (HEAD blob bytes == recorded SHA-256)
EXPECT references/preuves-session-lf.md: MATCH_BYTES (HEAD blob bytes == recorded SHA-256)

FLAG: AUTOCRLF_TRUE (the effective core.autocrlf may rewrite line endings on checkout)
VERDICT: RECONCILED
RESULT RECONCILED
INDEX_UNCHANGED: True
```

这次直接运行的日志没有捕获 `EXIT=`；`RESULT RECONCILED` 分支在 §10.2 的夹具中实测退出 0。

### 10.4 未验证与限制

- `REF_MISMATCH` 只做了单元级验证。先尝试用 `git.bat` 包装器在真实仓库里制造目标 ref 漂移，但 Windows `CreateProcess` 优先解析 `git.exe` 而不是 `.bat`，包装器被绕过；随后改用 `FakeGit` 直接调用 `collect_pointer()`/`print_pointer()`。稳定的符号 HEAD 在没有并发移动或损坏时不会与目标 ref 分歧，因此端到端构造需要竞态或手工破坏 ref，本轮未做。
- 未构造：并发 ref 更新正好落在多条指针读取之间、submodule、reftable 后端、Git < 2.15（`--is-shallow-repository` 的引入版本）、HEAD 文件不可读、HEAD 文件含 CRLF 或额外空白、符号链接或大小写不同的 worktree 路径、网络 shallow clone、bare 仓库、`GIT_DIR` 环境变量覆盖。
- `HEAD_POINTER: OK` 只表示指针可解析、对象是 commit、树可读；不做 `git fsck`，不校验对象图完整性。
- 指针读取由多条 Git 命令组成，不是一次原子快照。若并发进程在两条命令之间更新 ref，可能出现瞬时不一致；遇到 `MISMATCH` 应复读一次再下结论。
- 索引只读性用 `size`、`mtime_ns`、SHA-256 前后比对；理论上并发写入者可以恢复相同的三个值，本轮未构造该情形。
- 仅在 Windows 10.0.26200 + Git for Windows 上实测；POSIX 上 `.git/HEAD` 的 ctime 语义未验证。

夹具目录在提取上述输出后删除；本 Skill 包只保留 `SKILL.md`、`references/` 与 `scripts/`，不保留 `__pycache__`、`.pyc` 或夹具脚本。

## 11. 已提交内容审计案例（来源会话 e421cc5c，2026-10-26 17:35 UTC）

### 11.1 来源与范围

- 会话：`e421cc5c-8930-455c-8c92-9be3a55d24d9`，落盘 JSONL 在写入本节时为 591 行（含工具结果与摘要行）。
- 触发消息：REC 237（1-based），`2026-10-26T17:35:19.164Z`，原文 `vérifier le contenu des fichiers commités`。
- 后续用户请求：17:38:31 `montrer le diff du commit 5c26375`；17:40:29 `voir le contenu du fichier SKILL.md`；17:41:14 `afficher les références dans SKILL.md`；17:42:32 `ouvrir preuves-session-ac90ec1e.md`；17:43:58 与 17:45:16 两次要求显示 SKILL.md；17:47:15 运行夹具；17:48:16 运行写入者归因脚本。
- 逐条核对用户消息，未发现纠正性语句；这些消息都是新的读取或展示请求。会话前半段（17:20–17:34）处理的是另一个 Skill（`commit-skill-work` / `adopt-source-session-update`），与本次内容审计的结论分开。
- 被审计仓库：`C:\Users\Administrateur\.qoder\skills\adopt-source-session-update`，根提交 `5c26375`，仅 2 个文件。

### 11.2 逐字证据

导出与 diff（REC 256/258）：

```text
DISK_EQUALS_HEAD_SKILL
DISK_EQUALS_HEAD_REF
  218 C:/Users/Administrateur/.qoder/tmp/verify-commit-content-adopt-source-session-update/SKILL.md
  134 C:/Users/Administrateur/.qoder/tmp/verify-commit-content-adopt-source-session-update/preuves-session-ac90ec1e.md
  352 total
16263 C:/Users/Administrateur/.qoder/tmp/verify-commit-content-adopt-source-session-update/SKILL.md
 6634 C:/Users/Administrateur/.qoder/tmp/verify-commit-content-adopt-source-session-update/preuves-session-ac90ec1e.md
22897 total
```

结构审计（REC 261/263，脚本在仓库外的临时副本上运行）：

```text
BOM: False
EOL_CRLF: False | REF_CRLF: False
FM_KEYS: ['name', 'description']
NAME: adopt-source-session-update | DIR_MATCH: False
DESC_LINES: 1 | DESC_CHARS: 621 | <=1024: True
BODY_LINES: 214 | <500: True
BODY_BYTES: 14952
H1: ['# 采纳来源会话已应用的 Skill 更新']
H2_COUNT: 13
H3_COUNT: 3
FENCE_LINES: 6 | BALANCED: True
CHECKLIST_ITEMS: 18
TABLE_ROWS: 25
TRAILING_WS_LINES: 0
LAST_CHAR_NEWLINE: True
PLACEHOLDER <skill-name>: lines [60]
REF_H2: 7
REF_CHECKLIST: 0
REF_FENCES: 0
REF_TRAILING_NEWLINE: True
```

`DIR_MATCH: False` 不是仓库内容错误：副本目录名是 `verify-commit-content-adopt-source-session-update`，而 frontmatter 是 `name: adopt-source-session-update`。修正方式是拿真实 Skill 目录名比较，而不是拿导出目录名比较。

交叉引用扫描（REC 266/268，扫描时剔除围栏代码块）：

```text
BACKTICK_TOKENS: 87 | SKILL_SHAPED: 11
  adopt-concurrent-duplicate-skill: OK
  audit-session-evidence: OK
  audit-skill-during-live-creation: OK
  bilingual-skill-parity: OK
  commit-skill-work: OK
  merge-base: MISSING
  skill-file-qa: OK
  skill-update-concurrency-safe: OK
  verifier-reecriture-concurrente-paquet-skill: OK
  verify-injected-skill-body-freshness: OK
  waiting-user: MISSING
MISSING_TOTAL: 2
LOCAL_REF_TOKENS: []
```

两个 `MISSING` 都是代码字面量，不是 Skill：`merge-base` 是 Git 子命令，`waiting-user` 是会话状态值。正确动作是给扫描器加 `--ignore`，不是改文档。

补丁展示（REC 299/304/318）：

```text
5c26375 feat(skill): ajouter le Skill adopt-source-session-update
 SKILL.md                               | 218 +++++++++++++++++++++++++++++++++
 references/preuves-session-ac90ec1e.md | 134 ++++++++++++++++++++++++++++
 2 files changed, 352 insertions(+)
---
  372 23907 C:/Users/Administrateur/.qoder/tmp/diff-5c26375/5c26375.patch
```

补丁 372 行、23,907 B，内容只有新增。写入本文件时 `C:\Users\Administrateur\.qoder\tmp\diff-5c26375\5c26375.patch` 仍存在；同一轮的 `verify-commit-content-adopt-source-session-update` 导出目录已不存在。这说明「导出后清理」必须把内容目录与补丁目录都算进去。

### 11.3 过程纠正

1. **`name` 只能与真实 Skill 目录名比较。** 用导出目录名比较会得到假的 `DIR_MATCH: False`；导出目录应保留 `<skill-name>/` 这一级，或明确标注「不参与比较」。
2. **代码字面量不是 Skill 引用。** `merge-base`、`waiting-user` 这类反引号 token 会被形状匹配命中；用 `--ignore` 排除，不修改正文。
3. **`diff ... && echo SAME` 会吞掉退出码。** 源会话命令是 `diff -u "$out/SKILL.md" "$target/SKILL.md" && echo "DISK_EQUALS_HEAD_SKILL"`；本例差异为 0 所以输出正确，但同一写法在差异为 1、错误为 2 时都会静默。正式脚本改为先取 `rc`，`0/1/2` 分别表示相同、有差异、出错。
4. **补丁目录要单独清理。** 内容导出目录删了，`diff-5c26375` 仍留下 23,907 B 的补丁。
5. **正文行数不含 frontmatter。** 文件总行 218，frontmatter 占 4 行（含两条 `---`），正文 214 行，与 QA 的 `BODY_LINES: 214` 一致。

### 11.4 推荐数据审计

- `action: update`、目标目录 `C:\Users\Administrateur\.qoder\skills\verify-skill-git-head-vs-worktree`、`skillName`：与既有目录一致，**SUPPORTED**。
- 「现有脚本只比较 OID」：**OVERSTATED**。`head_vs_worktree.py` 的 `--expect-sha256` 分支已经用 `cat-file blob` 读取 HEAD 字节并计算 SHA-256，`MATCH_BYTES` 就是字节级结论；它缺的不是字节，而是导出、文本 diff、结构审计、引用解析与分段补丁。
- 真实缺口：把提交内容导出到仓库外可读、与磁盘做有界 unified diff、对提交字节做结构与编码预检、把跨 Skill 引用交给专用扫描器、把 `git show` 补丁分段展示。新增脚本只补这五项，语义校验仍交给 `skill-file-qa`。

### 11.5 新脚本 `audit_head_content.py`

```text
audit_head_content.py SKILL_DIR [--path REL]... [--out OUT] [--keep]
  [--strict-lf] [--no-diff] [--context 3] [--max-diff-lines 200] [--max-files 400]
```

- 只读 Git：`rev-parse`、`ls-tree -r -z`、`cat-file blob`、`hash-object`；不调用 `status`/`diff`，不写 ref、索引或工作区。
- 导出目录默认在 `%TEMP%`，`--out` 落在仓库或 Skill 目录内直接 `CONTENT_ERROR`（退出 2）；非空目录也拒绝。
- 逐文件 `BYTES_EQUAL` / `BYTES_DIFFER` / `MISSING_ON_DISK`；磁盘多出的文件记 `EXTRA_ON_DISK` 与 `extra=`，不单独判失败。
- `SKILL.md` 结构检查：frontmatter 与 YAML、`name` 对真实目录、description 单行 ≤1024、正文 <500、唯一 H1、围栏配对、围栏外的未完成标记与占位符。
- 字节检查：BOM、UTF-8 严格解码、CRLF、Tab、控制字符、尾随空白、末行换行；CRLF 默认 WARN，`--strict-lf` 升级为 FAIL。
- diff 有界，超限打印 `(truncated)` 与 `diff truncated`；二进制或非 UTF-8 跳过。
- 结果：`CONTENT_OK` 退出 0；`CONTENT_OK_DISK_DIFFERS`、`CONTENT_FAIL` 退出 1；`CONTENT_ERROR` 退出 2。
- 默认 `CLEANED: True`；`--keep` 打印 `KEPT:` 路径供 `skill-file-qa` 接手。运行前后打印 `.git/index` 的 size/mtime_ns/SHA-256 与 `INDEX_UNCHANGED`。

### 11.6 夹具矩阵 F18–F30

在 `%TEMP%` 下为每个用例建立 `<case>/fixture-skill/`，`git init` 后提交，再调用脚本。首轮 7 项失败全部是夹具错误：目录名用 `f18-valid` 等，导致 `name_dir_mismatch`；F19 断言写成 `CONTENT_OK`；F25 的 QA 因同一目录名问题失败。修正夹具后复跑：

| 用例 | 构造 | 期望 | 结果 |
|---|---|---|---|
| F18 | 合法 SKILL.md + reference | 退出 0，`CONTENT_OK`，`equal=2`，结构行含 `body_lines=6`/`h1=1`/`dir_match=yes`，清理，索引不变 | 通过 |
| F19 | 提交后在工作区追加一行 | 退出 1，`CONTENT_OK_DISK_DIFFERS`，`BYTES_DIFFER`，diff 含新增行 | 通过 |
| F20 | frontmatter `name` 与目录不符 | 退出 1，`name_dir_mismatch`，`CONTENT_FAIL` | 通过 |
| F21 | BOM + CRLF + Tab + TODO + 无末行换行 | 退出 1；同时报 `bom_present`、`crlf_present`、`tab_present`、`placeholder_outside_fence`、`no_final_newline` | 通过 |
| F22 | `--path nope.md` | 退出 1，`PATH_NOT_AT_HEAD` | 通过 |
| F23 | 无 Git 仓库 | 退出 1，`VERDICT: NO_REPO` | 通过 |
| F24 | `--out` 指向仓库内 | 退出 2，`CONTENT_ERROR`，`--out must be outside` | 通过 |
| F25 | `--keep`，对 `KEPT:` 目录跑 `skill-file-qa` | 退出 0，打印 `KEPT:`，目录存在，QA `RESULT PASS`，手工清理成功 | 通过 |
| F26 | 磁盘多出未跟踪文件 | `EXTRA_ON_DISK notes.txt`，`extra=1`，不单独失败 | 通过 |
| F27 | 提交内容为 CRLF | 默认退出 0 + `CHECK WARN crlf_present`；`--strict-lf` 退出 1 + `CHECK FAIL crlf_present` | 通过 |
| F28 | `--max-diff-lines 5` | diff 输出含 `(truncated)` 与 `diff truncated` | 通过 |
| F29 | `--path references/note.md` | 退出 0，`FILES: 1 (selected)`，不输出 SKILL.md | 通过 |
| F30 | `--max-files 1` 但仓库有 2 个文件 | 退出 2，`exceed --max-files` | 通过 |

汇总：`CHECKS=35 FAILURES=0`、`FIXTURE_ROOT_CLEANED True`、`HARNESS_EXIT=0`。

### 11.7 真实仓库复跑（写入本节时）

```text
SKILL_DIR: C:\Users\Administrateur\.qoder\skills\adopt-source-session-update
REPO_ROOT: C:\Users\Administrateur\.qoder\skills\adopt-source-session-update
PREFIX: (skill dir is repo root)
HEAD: 5c263755c00466b5b65dbb2ad9cc409daf6df46d
HEAD_TIME: 2026-10-26T18:33:12+01:00
HEAD_SUBJECT: feat(skill): ajouter le Skill adopt-source-session-update
EXTRACT: C:\Users\ADMINI~1\AppData\Local\Temp\audit-head-content-5c263755c004-12808\adopt-source-session-update
FILES: 2 (selected) | head_blobs=2

FILE SKILL.md head=93938c8d9841 bytes=16263 disk=BYTES_EQUAL head_sha256=a2a25c43bc59c78a8643482d51a284fc91b07310112530edbcbdec1bccc9e32d disk_sha256=a2a25c43bc59c78a8643482d51a284fc91b07310112530edbcbdec1bccc9e32d
  STRUCT name=adopt-source-session-update dir_match=yes desc_lines=1 desc_chars=621 body_lines=214 h1=1 h2=13 h3=3 fences=6 checklist=18 tables=25
  BYTES bom=no crlf=0 tabs=0 trailing_ws=0 final_newline=yes

FILE references/preuves-session-ac90ec1e.md head=5b543e7adba1 bytes=6634 disk=BYTES_EQUAL head_sha256=6935814dbe00fcff6f4c36c208adf76f08e63286a7c7cc07f96611a973b3a415 disk_sha256=6935814dbe00fcff6f4c36c208adf76f08e63286a7c7cc07f96611a973b3a415
  BYTES bom=no crlf=0 tabs=0 trailing_ws=0 final_newline=yes

SUMMARY files=2 equal=2 differ=0 missing=0 extra=0 structural_fail=0 warnings=0
VERDICT: CONTENT_OK
RESULT CONTENT_OK

INDEX: C:\Users\Administrateur\.qoder\skills\adopt-source-session-update\.git\index size=276 mtime_ns=1793035992084266400 sha256=679b46b769212d2d6e37850e8f0de3a421097e42f1183689b7af4e97d8a8a922
INDEX_UNCHANGED: True
CLEANED: True
EXIT=0
```

### 11.8 未验证与限制

- 二进制或非 UTF-8 文件只标注跳过，未构造真实二进制用例；`diff` 的二进制分支未逐行验证。
- gitlink 只走了代码分支 `GITLINK_UNSUPPORTED`，未用真实 submodule 验证 `--path` 选中 gitlink 的完整输出。
- 未构造：PyYAML 缺失时的降级、`--out` 指向已存在的空目录、审计期间并发改写工作区、导出文件被占用导致清理失败、超过 `--max-files` 400 的树、bare 仓库、reftable 后端、shallow 仓库、detached HEAD 下的内容审计、`HEAD_OBJECT_INVALID`。
- 结构检查是文档级预检，不做语义判断；`skill-file-qa` 与引用扫描仍是独立门禁。
- `CLEANED: True` 只证明本次进程删除了自己创建的目录；不清理用户指定的 `--out` 父目录，也不清理 §9 的补丁目录。
- 仅在 Windows 10.0.26200 + Git for Windows + PyYAML 可用时实测。
