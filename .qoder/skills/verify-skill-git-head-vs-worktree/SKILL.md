---
name: verify-skill-git-head-vs-worktree
description: "只读对账一个 Skill 目录的 Git HEAD 与工作区：定位真实仓库根与 .git 形态，用 HEAD 树、索引和 hash-object --path 的 OID 逐文件判定 SAME/WORKTREE_ONLY/STAGED_ONLY/UNTRACKED/DELETED，报告仓库出现时间、HEAD 时间与 autocrlf 行尾风险，核对 HEAD 指针（HEAD 文件、symbolic-ref、目标 ref、commit/tree、reflog、shallow、worktree）并独立报告 HEAD_POINTER 判定，可用 --expect-sha256 绑定 QA 指纹到 HEAD blob；需要看内容时，把 HEAD blob 导出到仓库外做字节比对、有界 diff 与结构审计（frontmatter、name 与真实目录、description、正文行数、围栏、占位符），并分段展示提交补丁；全程不 add/commit/init/checkout，删除 .git 前必须停下。用于 QA 已 PASS 但 HEAD 早于编辑、目录中途出现 .git、区分已验证磁盘与已提交状态、status 干净但不确定是否同一版、git diff 只警告 LF→CRLF、提交前只想确认范围、验证 HEAD 指针或排查 detached/shallow/多 worktree、要求检查提交内容或补丁时；中文触发：HEAD 与工作区、HEAD 指针、symbolic-ref、detached HEAD、shallow clone、worktree 列表、reflog 与 HEAD 不一致、未提交修改、仓库中途出现、HEAD 早于编辑、指纹绑定、只读对账、已提交内容、提交补丁；English: HEAD vs worktree, HEAD pointer, detached HEAD, symbolic-ref, shallow clone, worktree list, reflog vs HEAD, uncommitted skill changes, repo appeared mid-task, bind QA fingerprint to commit, verify committed content, blob diff, inspect commit patch."
---

# Skill 目录的 HEAD 与工作区只读对账

## 目标

回答六个可分开的问题，不把它们的答案混为一谈：

1. 这个目录是否被 Git 覆盖，仓库是什么时候出现的？
2. HEAD 指针本身是否有效（符号引用、目标 ref、对象类型、树、reflog、shallow、worktree）？
3. 磁盘上每个包文件的内容是否等于 HEAD（以及索引）？
4. `skill-file-qa` 当时记录的 SHA-256，是否绑定到某个 HEAD blob？
5. 提交进去的字节是否可读、结构是否合法、与磁盘文本差在哪？
6. 指定提交的补丁能否分段查看而不刷屏？

## 何时使用

- `skill-file-qa` 已 `RESULT PASS`，但 HEAD 提交时间早于最后一次编辑。
- 验收或接管途中，目录里突然出现 `.git`。
- 需要区分「已验证的磁盘字节」与「已提交状态」。
- 并发会话可能已提交、检出或重置出另一版。
- 用户要求提交前，只想确认变更范围。
- `git status` 干净，但不确定干净的是不是自己验证的那一版。
- `git diff` 只打印 `LF will be replaced by CRLF`，需要判断算不算改动。
- 用户要求「验证 HEAD 指针」，或怀疑 detached HEAD、shallow clone、多 worktree、reflog 与 HEAD 不一致。
- 用户要求「检查提交进去的文件内容」「看提交的文件是什么」「对比 HEAD 与磁盘文本」。
- 需要把 HEAD blob 导出后交给 `skill-file-qa` 或引用扫描，而不是只看 OID。
- 需要分段查看提交补丁，避免一次打印数百行。
- 中文触发：HEAD 与工作区、HEAD 指针、symbolic-ref、detached HEAD、shallow clone、worktree 列表、reflog 与 HEAD 不一致、未提交修改、仓库中途出现、HEAD 早于编辑、指纹绑定、只读对账、干净 status 是否可信、已提交内容、提交进去的文本、cat-file blob、提交补丁、diff 退出码、导出目录。
- English triggers: HEAD vs worktree, HEAD pointer, detached HEAD, symbolic-ref, shallow clone, worktree list, reflog vs HEAD, uncommitted Skill changes, repo appeared mid-task, bind QA fingerprint to commit, is my verified file committed, verify committed file content, cat-file blob diff, inspect commit patch, segmented diff.

## 不适用与交接

| 需求 | 交给 |
|---|---|
| 真正提交、暂存、推送 | `commit-skill-work` |
| 锁定 LF、决定 `.gitattributes` 放哪 | `lock-lf-endings-skill-repo` |
| 判定依赖脚本行为来自 HEAD 还是工作区 | `qualify-dependency-behavior-provenance` |
| 包清单、缓存、过期归档 | `skill-package-integrity-audit` |
| 并发重写取证与版本重建 | `verifier-reecriture-concurrente-paquet-skill` |
| 接管他人已生成的同职责 Skill | `adopt-concurrent-duplicate-skill` |
| 运行时实际解析到哪个目录 | `verify-skill-runtime-binding` |

## 硬规则

1. **只读。** 脚本只用管道/只读命令（`rev-parse`、`rev-list`、`symbolic-ref`、`for-each-ref`、`reflog`、`worktree list`、`ls-tree`、`ls-files`、`hash-object`、`cat-file`、`log`、`config --get-all`），不调用 `status`/`diff`，不写 ref、索引或工作区。
2. **手写 `status`/`diff` 必须把 `--no-optional-locks` 放在子命令之前**（它是全局选项）：`git -C "<root>" --no-optional-locks status --porcelain=v1`。放在子命令之后会得到 ``error: unknown option `no-optional-locks'`` 与退出码 129。实测普通 `git status`/`git diff` 在需要刷新 stat 时**可能**重写 `.git/index`（touch-only 场景已复现，内容变化场景未复现），因此要么避免这两个命令，要么加该选项，并在运行前后比对 `size`、`mtime_ns` 与 SHA-256。
3. 不执行 `add`、`commit`、`init`、`config` 写操作、`checkout`、`restore`、`clean`、`stash`；不删除 `.git`；不 push。
4. 提交只能由用户明确要求，并转 `commit-skill-work`。
5. **OID 判内容，SHA-256 判字节。** `status` 与 mtime 只是提示。
6. `warning: LF will be replaced by CRLF` 是「下次 touch 会转换」的预测，不是当前差异。
7. 仓库中途出现时，先冻结写盘、完成对账；不覆盖并发产物。文件被并发改写时转 `verifier-reecriture-concurrente-paquet-skill`。
8. **指针与工作区分开判定。** `RECONCILED` 不证明 HEAD 是分支、是 commit 或 reflog 一致；`HEAD_POINTER: OK` 也不证明磁盘内容等于 HEAD。两个结论必须分别报告。
9. 指针异常时只读报告：不用 `checkout` 修 detached HEAD，不 `update-ref`，不写 reflog，不删除 `.git`。由用户决定下一步。
10. **内容导出必须落在仓库外。** 默认写到 `%TEMP%`；拒绝 `--out` 在仓库或 Skill 目录内。默认删除导出目录，`--keep` 只用于把内容交给下游校验，不得写回仓库。
11. **`diff` 先取退出码，`git show` 先判非零。** `diff` 返回 `0` 相同、`1` 有差异、`2` 出错；禁止 `diff ... && echo SAME`，它会把「不同」和「失败」都吞成静默。`git show` 成功即 `0`，非零表示对象或路径不可读，不要与「有差异」混淆。
12. **语义校验不重复实现。** 字节与结构预检由 `audit_head_content.py` 回答；完整语义、代码块语法与引用存活分别交给 `skill-file-qa` 与 `verify-cross-skill-reference-liveness`。

## 步骤

### 1. 定位仓库边界

```bash
git -C "<skill-dir>" rev-parse --show-toplevel
git -C "<skill-dir>" rev-parse --show-prefix
git -C "<skill-dir>" rev-parse --absolute-git-dir
```

- `exit 128` + `fatal: not a git repository`：结论是 `NO_REPO`。这不是异常，也不授权 `git init`。
- 根 `.git` 是**文件**时表示 linked worktree 或 submodule，`GIT_DIR` 可能在工作区之外；先报告形态，再继续。脚本会把 Skill 根下的 `.git` 文件排除在包文件之外，不把它算成 `UNTRACKED`。
- `--show-prefix` 给出 Skill 目录到仓库根的相对前缀（如 `skill/`）。之后所有仓库级命令都在仓库根执行，路径按该前缀折算。
- Skill 目录只是仓库子目录时，只对账该前缀内的文件，不把仓库其他内容算进包。

### 2. 建立 HEAD 与时间证据

```bash
git -C "<root>" rev-parse HEAD
git -C "<root>" log -1 --format='%H%x1f%cI%x1f%ct%x1f%s'
git -C "<root>" rev-list --max-parents=0 HEAD
git -C "<root>" rev-parse --git-path logs/HEAD
```

- `HEAD` 无提交（unborn）时报 `NO_COMMITS`，所有包文件都算未提交。
- 仓库出现时间与首次提交时间是两个量：`.git`/`.git/HEAD` 的创建时间（Windows 为 creation time）是初始化提示；reflog 首行与根提交的 committer 时间（`%cI`）是首次提交时间。案例中初始化 `16:38:54`、根提交 `16:39:24`，`16:39:11` 只是对象目录写入。**不要把首次提交时间当成仓库出现时间，也不要用「我什么时候注意到」当证据**。
- `.git` 的 mtime 会随任何 ref/索引更新变化，不能当创建时间。
- 文件 mtime 只用于排序提示，不能证明内容：复制或归档可保留旧 mtime，`status` 干净也不证明提交发生在验证之后。

### 3. 核对 HEAD 指针（独立于工作区对账）

工作区对账只回答「磁盘内容 == HEAD 树」。先确认指针本身：

```bash
git -C "<root>" rev-parse --git-path HEAD
# 读取该文件：符号引用为 `ref: refs/heads/<branch>`，detached 时为 40/64 位 OID
git -C "<root>" symbolic-ref -q HEAD
git -C "<root>" rev-parse HEAD 'HEAD^{commit}' 'HEAD^{tree}'
git -C "<root>" rev-parse --verify 'refs/heads/<branch>^{commit}'
git -C "<root>" cat-file -t HEAD
git -C "<root>" for-each-ref --format='%(refname) %(objectname) %(objecttype)' refs/heads
git -C "<root>" ls-tree -r HEAD
git -C "<root>" reflog -1 --format='%H %gd %gs' HEAD
git -C "<root>" rev-parse --is-shallow-repository
git -C "<root>" worktree list --porcelain
```

- 用 `--git-path HEAD` 定位，不要硬编码 `<root>/.git/HEAD`：linked worktree 的 HEAD 在 `.git/worktrees/<name>/HEAD`，根 `.git` 可能是文件。
- **`HEAD` 与 `refs/heads/<branch>` 相等，在稳定状态下是同一引用的重复读取，单独相等不是强证据。** 它只能发现读取跨越并发 ref 更新，或引用损坏。强证据是：`symbolic-ref` 成功、`cat-file -t HEAD` = `commit`、`HEAD^{tree}`/`ls-tree` 可读、reflog 末条等于 HEAD。
- reflog 被禁用或删除时，如实报 `unavailable`，不要用 `HEAD@{0}` 猜测。

| HEAD_POINTER | 条件 | 含义与动作 |
|---|---|---|
| `OK` | 符号引用指向存在的分支引用（通常是 `refs/heads/*`），HEAD 可解析，`cat-file -t` = `commit` | 指针有效；继续内容对账 |
| `DETACHED` | `.git/HEAD` 是 OID，或 `symbolic-ref` 失败 | HEAD 有效但不在分支上；报告「不在 <branch>」；不自行 checkout |
| `REF_MISMATCH` | 符号引用目标缺失，或目标 OID ≠ HEAD | 可能读取跨越 ref 更新或引用损坏；停止声明「已在 <branch> 提交」 |
| `OBJECT_INVALID` | `cat-file -t HEAD` 失败或不是 `commit` | 分支指向 tree/tag/blob 或对象损坏；停止对账，不写 ref |
| `UNBORN` | 有符号引用但 HEAD 无提交 | 等价 `NO_COMMITS`；全部包文件未提交 |

判定优先级：`UNBORN`（无 HEAD 提交）→ `OBJECT_INVALID`（HEAD 不是 commit）→ `DETACHED`（无符号引用）→ `REF_MISMATCH`（目标缺失或 OID 不等）→ `OK`。T7 同时出现目标缺失与 tree 对象，按 `OBJECT_INVALID` 报。

附加标记（不改变 `HEAD_POINTER`，但必须报告）：

| 标记 | 条件 | 含义 |
|---|---|---|
| `REFLOG_LATEST_MISMATCH` | reflog 末条 OID ≠ HEAD | 指针可解析，但 reflog 证据不可信；检查手工改 ref、复制 `.git` 或 reflog 未更新 |
| `SHALLOW_REPO` | `--is-shallow-repository` = `true` | 根提交与历史不完整；`ROOT_COMMIT`/reflog 首行只能当边界证据 |
| `MULTIPLE_WORKTREES` | `worktree list --porcelain` 多于一个 | 索引按 worktree 分开；先确认当前 `GIT_DIR`/`--show-toplevel` 属于哪一个 |
| `HEAD_DETACHED` | 同 `DETACHED` | 在 `FLAG` 区重复提示，便于只读日志筛选 |

- `HEAD_POINTER` 与 `FLAG` 行都以脚本实际输出为准；本表是判定语义，不是额外的写操作。
- shallow 不自动让指针失效：shallow 仓库的 HEAD 仍可指向有效 commit，但根提交不是真实根。

### 4. 逐文件对账

每个包文件同时取三个 OID，再分类：

| 来源 | 命令 | 含义 |
|---|---|---|
| HEAD | `git -C "<root>" rev-parse "HEAD:<repo-rel>"` | 已提交内容 |
| 索引 | `git -C "<root>" ls-files -s -- "<repo-rel>"` | 已暂存内容 |
| 工作区 | `git -C "<root>" hash-object --path="<repo-rel>" "<abs-file>"` | 当前磁盘内容（按属性过滤） |

| 状态 | 含义 | 是否算未对账 |
|---|---|---|
| `SAME` | 三者内容一致 | 否 |
| `WORKTREE_ONLY` | 磁盘改了，未暂存 | 是 |
| `STAGED_ONLY` | 索引改了，未提交 | 是 |
| `BOTH` | 暂存与工作区都改了 | 是 |
| `UNTRACKED` | HEAD 与索引都没有 | 是 |
| `DELETED_ON_DISK` | HEAD 有，磁盘没有 | 是 |
| `DELETED_IN_INDEX` | 索引已删，磁盘仍有 | 是 |
| `CONFLICT` | 未合并索引项 | 是 |
| `IGNORED` | 被 `.gitignore` 排除（如 `__pycache__`） | 否，单列 |

- `hash-object --path` 会按 `core.autocrlf` 和 `.gitattributes` 过滤，因此它等于索引/HEAD 的 OID 只证明**内容**相同。
- 缓存不算内容差异，但也不该混进包清单；转 `skill-package-integrity-audit`。
- 输出过长时用 `--max-divergent`；不要用管道吞掉退出码。

### 5. 把 QA 指纹绑定到 HEAD

`skill-file-qa` 的 `Fingerprint`（size + SHA-256）只描述**当时磁盘**，不描述提交。重跑它也不能补上这一层。把记录值传进来：

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/verify-skill-git-head-vs-worktree/scripts/head_vs_worktree.py" \
  "<skill-dir>" \
  --expect-sha256 "SKILL.md=<64-hex-from-qa>"
```

| 绑定结果 | 含义 |
|---|---|
| `MATCH_BYTES` | HEAD blob 字节等于记录值 |
| `MATCH_CONTENT_EOL_DIFF` | 内容 OID 相同，但 blob 与磁盘字节不同（检出归一化） |
| `NOT_AT_HEAD` | 记录值对应的内容不在 HEAD（典型：编辑未提交，或并发提交换了版本） |
| `DISK_CHANGED_SINCE_EXPECT` | 磁盘已不是 QA 时的那一版；下一行 `HEAD:` 继续回答记录值是否在 HEAD |
| `HEAD: HEAD_MATCH_BYTES` | 附加行：记录值的字节等于 HEAD blob（即使磁盘已变） |
| `HEAD: HEAD_MISMATCH` | 附加行：记录值既不在当前磁盘也不在 HEAD |
| `FILE_MISSING` / `UNKNOWN_FILE` | 路径缺失或不属于该包；`FILE_MISSING` 同样附带 `HEAD:` 行 |

**核心判据：`status` 干净只证明「此刻磁盘 == HEAD」，不证明「我验证过的那一版 == HEAD」。** 并发提交或 `checkout` 可以把两者一起换掉，所以必须用记录值对 OID。

### 6. 行尾与 autocrlf

```bash
git -C "<root>" config --show-origin --get-all core.autocrlf
git -C "<root>" ls-files --eol
```

- 必须用 `--show-origin --get-all`：局部 `.git/config` 未设置时，值可能来自系统或全局配置。实测一次案例中值来自 `file:C:/Program Files/Git/etc/gitconfig=true`，而仓库 config 里根本没有该项。
- `--get-all` 可能返回多行（system → global → local/worktree）；**最后一条是有效值**，`AUTOCRLF_TRUE` 只看它。局部 `false` 覆盖全局 `true` 时不应报风险，但仍要打印全部来源行。
- `i/lf w/lf attr/` 且 `attr` 为空：当前快照是 LF，但没有仓库级规则；在 `autocrlf=true` 下**未来 checkout 仍可能写 CRLF**。
- 同一内容可能出现 `SAME` + `EOL_BYTE_DIFF`：以 OID 判内容，以字节哈希判「QA 记录的是哪次检出」。
- 要真正锁死行尾，转 `lock-lf-endings-skill-repo`；本 Skill 不改属性、不改 config。

### 7. 判定与报告

脚本退出码：`0` 已对账，`1` 未对账（含 `NO_REPO`、`NO_COMMITS`），`2` 用法或环境错误。

| 判定 | 含义 | 下一步 |
|---|---|---|
| `RECONCILED` | 全部包文件内容等于 HEAD，无未跟踪项 | 可声明「磁盘已验证版本 = 提交 `<oid>`」 |
| `WORKTREE_DIVERGES` | 有未暂存编辑、删除或两者兼有 | 停止声明已提交；按需转 `commit-skill-work` |
| `STAGED_ONLY` | 已暂存未提交 | 同上，别把暂存当已提交 |
| `UNTRACKED_PRESENT` | 包内有 HEAD 之外的文件 | 与用户决定 add / ignore / 删除 |
| `NO_COMMITS` | 仓库存在但没有提交 | 无提交可对账 |
| `NO_REPO` | 不在任何工作树内 | 无事可对账；未经同意不初始化 |
| `EXPECT_MISMATCH` | 记录指纹不在 HEAD | 旧 PASS 不适用于当前提交 |

报告模板：

```text
Repo    : <root> | <branch> | HEAD <oid> (<committer time>)
Pointer : HEAD_POINTER=<OK|DETACHED|REF_MISMATCH|OBJECT_INVALID|UNBORN> | symbolic=<ref|DETACHED>
          target=<MATCH|MISMATCH|MISSING|UNBORN> | object=<commit|...> | tree=<oid> entries=<n>
          reflog=<MATCH|MISMATCH|unavailable> | shallow=<true|false|unknown> | worktrees=<n>
Origin  : created hint <t> | first HEAD update <t> | root commit <oid> <t>
Package : <N> files | divergent <M> | ignored <K>
Files   : <STATE> <path> head=<oid> work=<oid> disk=<sha256>
Binding : <path> <MATCH_BYTES|MATCH_CONTENT_EOL_DIFF|NOT_AT_HEAD|...>
EOL     : autocrlf=<origin>=<value> | <i/.. w/.. attr/..>
Index   : INDEX_UNCHANGED <True|False> | size=<n> mtime_ns=<n> sha256=<hex>
Verdict : <worktree verdict> (exit <0|1|2>) ; pointer reported separately above
Next    : nothing | commit-skill-work on explicit request | ...
```

`Verdict` 只回答工作区；`Pointer` 单独回答指针。二者不一致时（例如 `RECONCILED` + `DETACHED`）必须并列报告，不能只报一个。脚本退出码仍只由工作区判定驱动，唯一例外是 `HEAD_OBJECT_INVALID`（无法可靠对账，退出 1）。

### 8. 核对已提交内容（字节、结构、差异）

§4–§6 只回答「OID/字节是否相同」，不回答「提交进去的文本是否可读、结构是否合法、差在哪」。需要看内容时：

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/verify-skill-git-head-vs-worktree/scripts/audit_head_content.py" \
  "<skill-dir>" [--path "SKILL.md"]... [--keep] [--strict-lf] [--no-diff] [--max-diff-lines 200]
```

- 脚本把 `git cat-file blob HEAD:<repo-rel>` 写到仓库外的临时目录（默认 `%TEMP%/audit-head-content-` 加提交前缀与进程号，其下按 Skill 目录名分级）。`--out` 落在仓库或 Skill 目录内会被拒绝（退出 2）；目录非空也拒绝，避免覆盖旧内容。
- 默认审计前缀内全部 HEAD blob；`--path` 只选指定文件（相对 Skill 目录）。路径不在 HEAD 报 `PATH_NOT_AT_HEAD`，gitlink 报 `GITLINK_UNSUPPORTED`。
- 逐文件状态：`BYTES_EQUAL`、`BYTES_DIFFER`、`MISSING_ON_DISK`；磁盘多出的文件单列 `EXTRA_ON_DISK`（提示，不单独判失败）。
- `SKILL.md` 结构审计：frontmatter 分隔符与 YAML、`name` 与**真实** Skill 目录名（不是导出目录）、description 单行且 ≤1024、正文行数 <500、唯一 H1、围栏配对、代码围栏外的未完成标记（脚本 `FAIL_MARKERS` 里的四个大写词）与尖括号模板占位符。
- 字节审计：BOM、UTF-8 严格解码、CRLF、Tab、控制字符、尾随空白、末行换行。CRLF/Tab/尾随空白默认 WARN；`--strict-lf` 把 CRLF 升级为 FAIL。
- 文本 diff 有界（`--max-diff-lines` 默认 200，`--context` 默认 3）；二进制或非 UTF-8 跳过并标注。
- 退出码：`0` = `CONTENT_OK`；`1` = `CONTENT_OK_DISK_DIFFERS` 或 `CONTENT_FAIL`；`2` = `CONTENT_ERROR`（用法/环境）。
- 默认删除导出目录，输出 `CLEANED: True`。需要交给下游时加 `--keep`，用打印出的 `KEPT:` 路径运行 `skill-file-qa`；不要把导出目录写回仓库。
- 引用存活不在本脚本内判定：交给 `verify-cross-skill-reference-liveness`，代码字面量用 `--ignore`（案例中 merge-base、waiting-user 两个词是误报）。
- **不要用 `diff -u ... && echo SAME`**：有差异时 `diff` 退出 1，出错时 2，`&&` 会把两者都吞掉；先取 `rc=$?` 再判断。

### 9. 分段展示提交补丁

```bash
git -C "<root>" show --stat --oneline --no-color <oid>
git -C "<root>" show --no-color --format=fuller <oid> > "$out/<oid12>.patch"
wc -l -c "$out/<oid12>.patch"
sed -n '1,40p' "$out/<oid12>.patch"
```

- 先看 `--stat` 的文件数与增删行数，再决定是否导出全文；补丁写到仓库外，结束删除（源会话漏删过补丁目录）。
- 分段读取：头部（commit/author/日期/stat）、每个文件 hunk 的起点、尾部；不要一次打印数百行。
- `git show` 只读；不 checkout、不 cherry-pick、不应用补丁。
- 补丁证明的是提交内容，不是磁盘当前内容；磁盘差异仍由 §4/§5 与 §8 回答。

## 命令

对账脚本（绝对路径，Windows 用 `py -3`）：

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/verify-skill-git-head-vs-worktree/scripts/head_vs_worktree.py" \
  "<skill-dir>" [--expect-sha256 "REL=<hex>"]... [--verbose] [--max-divergent 300]
```

内容审计脚本（导出、diff、结构）：

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/verify-skill-git-head-vs-worktree/scripts/audit_head_content.py" \
  "<skill-dir>" [--path "REL"]... [--out "<outside-repo-dir>"] [--keep] [--strict-lf] \
  [--no-diff] [--context 3] [--max-diff-lines 200] [--max-files 400]
```

手工回退（脚本缺失时逐条执行，保持顺序）：

```bash
git -C "<skill-dir>" rev-parse --show-toplevel
git -C "<skill-dir>" rev-parse --show-prefix
git -C "<root>" rev-parse HEAD
git -C "<root>" log -1 --format='%H %cI %s'
git -C "<root>" rev-list --max-parents=0 HEAD
git -C "<root>" rev-parse --git-path HEAD
git -C "<root>" symbolic-ref -q HEAD
git -C "<root>" rev-parse 'HEAD^{tree}' 'refs/heads/<branch>^{commit}'
git -C "<root>" cat-file -t HEAD
git -C "<root>" for-each-ref --format='%(refname) %(objectname) %(objecttype)' refs/heads
git -C "<root>" reflog -1 --format='%H %gd %gs' HEAD
git -C "<root>" rev-parse --is-shallow-repository
git -C "<root>" worktree list --porcelain
git -C "<root>" --no-optional-locks status --porcelain=v1 --untracked-files=all
git -C "<root>" --no-optional-locks diff --stat
git -C "<root>" ls-tree -r HEAD
git -C "<root>" ls-files -s
git -C "<root>" ls-files -o --exclude-standard
git -C "<root>" hash-object --path="<repo-rel>" "<abs-file>"
git -C "<root>" rev-parse "HEAD:<repo-rel>"
git -C "<root>" cat-file blob "HEAD:<repo-rel>" | sha256sum
git -C "<root>" cat-file blob "HEAD:<repo-rel>" > "$out/<rel>"
git -C "<root>" show --stat --oneline --no-color <oid>
git -C "<root>" show --no-color --format=fuller <oid> > "$out/<oid12>.patch"
git -C "<root>" config --show-origin --get-all core.autocrlf
git -C "<root>" ls-files --eol
```

手工导出后必须比较：

```bash
diff -u "$out/<rel>" "<abs-file>"
rc=$?
printf 'DIFF_RC=%s\n' "$rc"
```

先取退出码再判断，不要经管道；`cat-file` 前先确认 `rev-parse` 的 OID 非空。`diff` 的 `0/1/2` 分别是相同、有差异、出错。

## 错误对照

| 现象 | 原因 | 动作 |
|---|---|---|
| `fatal: not a git repository` | 目录不在工作树内 | 报 `NO_REPO`；未经同意不 `git init` |
| 仓库存在但 `HEAD` unborn | 只 init 未提交 | 报 `NO_COMMITS`，全部文件列未跟踪 |
| `warning: LF will be replaced by CRLF` | `core.autocrlf=true` 的预测 | 不算 diff；用 `--eol` 与 OID 判断 |
| `status` 干净但绑定 `NOT_AT_HEAD` | 并发提交/检出换了版本 | 以绑定结果为准，重新验证 |
| `Files (N)` 与包文件数不一致 | `.git` 与忽略项不计入 QA 清单 | 单独报告 `.git` 形态与 ignored 文件 |
| 普通 `status`/`diff` 后 `.git/index` mtime 变化 | Git 在 stat 过期时刷新并写索引（条件性，不总是发生） | 把全局 `--no-optional-locks` 放在子命令前复跑，并如实说明 |
| ``error: unknown option `no-optional-locks'``，退出码 129 | 选项放在了子命令之后 | 改为 `git -C "<root>" --no-optional-locks status ...` |
| `INDEX_UNCHANGED: False` | 运行期间索引被并发进程改写，或命令触发了刷新 | 停止声明只读；记录前后 size/mtime_ns/SHA-256 并排查并发进程 |
| `GIT_DIR` 在 Skill 目录外 | linked worktree / submodule | 报告路径与形态，不假定索引位置 |
| `.git/HEAD` 是 OID，或 `symbolic-ref` 失败 | detached HEAD | 报 `DETACHED`；不 checkout、不改 ref |
| `POINTER_TARGET` 为 `MISSING`/`MISMATCH` | 引用损坏，或读取跨越并发 ref 更新 | 报 `REF_MISMATCH`；复读一次确认；不写 ref |
| `cat-file -t HEAD` 不是 `commit` | 分支指向 tree/tag/blob 或对象损坏 | 停止对账，报 `OBJECT_INVALID` |
| `POINTER_SHALLOW: true` | shallow clone | 根提交/reflog 首行只当边界；历史不可用 |
| `POINTER_WORKTREES` 大于 1 | 多 worktree | 确认当前 `GIT_DIR` 与索引属于哪一个，不混用 |
| `POINTER_REFLOG_LATEST: unavailable` | reflog 被禁用、删除或不可读 | 指针仍可判定；reflog 标为不可用 |
| `POINTER_REFLOG_LATEST` 与 HEAD 不一致 | 手工改 ref、复制 `.git`、reflog 未更新 | 报 `REFLOG_LATEST_MISMATCH`；以 OID 为准 |
| `PATH_NOT_AT_HEAD` | `--path` 指向的路径不在 HEAD 树内 | 用 `ls-tree -r HEAD` 核对；不要改 ref |
| `GITLINK_UNSUPPORTED` | 选中路径是 submodule gitlink | 报 unsupported，不递归 |
| `--out must be outside`，退出 2 | 导出目录在仓库或 Skill 目录内 | 改用 `%TEMP%` 新目录 |
| `extraction directory is not empty` | 复用了旧导出目录 | 换新路径或先清理 |
| `CHECK FAIL name_dir_mismatch` 但名字看似正确 | 用导出临时目录名比了 `name` | 用真实 Skill 目录名；导出目录名不应参与比较 |
| 引用扫描把 merge-base/waiting-user 报 `MISSING` | 代码字面量被当成 Skill 名 | 加 `--ignore`；不要改文档 |
| `diff` 退出 1 被当成命令失败 | 把「有差异」当「出错」 | 先取 `rc`；`0` 相同、`1` 差异、`2` 出错 |
| 补丁导出目录残留 | 只清理了内容目录 | 两个目录都清理并检查 `%TEMP%` |
| `CONTENT_FAIL` 但磁盘字节相同 | 结构问题（frontmatter/name/description/占位符） | 看 `CHECK FAIL` 行；不要只盯 diff |
| 输出被截断 | 差异文件过多 | 提高 `--max-divergent` 或按状态分组 |

## 检查清单

- [ ] 记录了仓库根、前缀、`.git` 形态与 `HEAD` OID。
- [ ] 记录了根提交、reflog 首行与末条、`.git/HEAD` ctime，并注明证据强度。
- [ ] 记录了 `.git/HEAD` 内容、`symbolic-ref`、目标 ref、对象类型与树，并给出独立 `HEAD_POINTER`。
- [ ] `DETACHED`/`REF_MISMATCH`/`OBJECT_INVALID`/`UNBORN` 与 shallow、多 worktree、reflog 不一致均已单列；未用工作区 `RECONCILED` 代替指针判定。
- [ ] 每个包文件都有状态；`IGNORED` 单列，未混入差异数。
- [ ] 每条 QA 指纹都绑定到 HEAD，或明确标为未提交。
- [ ] 记录了 `core.autocrlf` 来源与 `ls-files --eol`。
- [ ] 判定与退出码一致；未把暂存、干净 status 或 QA PASS 说成已提交。
- [ ] 需要看内容时，HEAD blob 已导出到仓库外，且 `CLEANED: True` 或明确 `KEPT`。
- [ ] 结构审计的 `dir_match` 用的是真实 Skill 目录名，不是导出目录。
- [ ] `diff` 退出码 `0/1/2` 已区分，未用 `&&` 吞掉差异或错误。
- [ ] 补丁分段查看，导出文件已清理。
- [ ] 未执行 add/commit/init/checkout，未删除 `.git`，未 push。
- [ ] 声称只读时，脚本输出 `INDEX_UNCHANGED: True`，且 size、mtime_ns、SHA-256 前后一致。

## 资源

- `scripts/head_vs_worktree.py`：只读对账脚本，OID 矩阵 + 指纹绑定（含磁盘变化后的 HEAD 绑定）+ HEAD 指针块（`POINTER_*`/`HEAD_POINTER`）+ 行尾风险 + 运行前后 `.git/index` 快照，退出码 0/1/2。
- `scripts/audit_head_content.py`：只读内容审计脚本，把 HEAD blob 导出到仓库外，做字节比对、有界 unified diff、frontmatter/name/description/正文行数/围栏/占位符检查与字节审计；`--keep` 供 `skill-file-qa` 接手，默认清理，退出码 0/1/2。
- `references/cas-git-head-vs-worktree-2026-10-26.md`：来源会话逐字证据、时间线、夹具矩阵（F1–F17、T1–T8、F18–F30）、HEAD 指针案例（§9）、内容审计案例（§11）与未验证边界。
