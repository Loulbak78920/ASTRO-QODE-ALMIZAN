# 证据 — 根目录旧布局迁移

本文件记录 2026-10-26 的来源会话、实际命令与输出、失败与纠正，以及同日对当前远端的补充观察。所有哈希、OID、计数和路径都是带日期的观测值，不是可复用常量。

## 1. 来源与读取范围

- 会话：`52ce9bcb-d076-4b0f-9cb8-ef3e35d75113`
- JSONL：`C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\52ce9bcb-d076-4b0f-9cb8-ef3e35d75113.jsonl`（1,252 行）
- `read_chat_session`：`turnLimit=20`、`includeToolOutputs=true`、`runtimeState=cold`、`activeTurnId=null`、`revision=0`、`hasMoreBefore=true`，快照含 30 条消息。
- 迁移回合：用户 `2026-10-26T17:38:44.214Z` 问“verify-skill-runtime-binding 的布局问题怎么修”；`17:40:16.946Z` 说“执行迁移并提交/推送”。工具调用集中在 `17:40:21Z`–`17:41:29Z`。
- 限制：快照只覆盖最近窗口；更早内容来自 JSONL 中的继续摘要，未读取完整 1,252 行。本文不声称覆盖会话全部历史。

## 2. 迁移前状态

仓库：`C:\Users\Administrateur\qoder-skills-main`，分支 `main`，`HEAD=3fa0460`，工作区干净，`HEAD=origin/main`。

根文件：

- `SKILL.md`：23,975 B；frontmatter `name: audit-skill-during-live-creation`。
- `references/preuves-session.md`：17,532 B。
- 根还有 `.gitattributes` 与 `.qoder/skills/` 下三个已迁移包。

根 QA（命令见第 5 节，对象为仓库根）：

```text
ROOT_QA_RC=1
Files (10): .gitattributes, ... SKILL.md, references/preuves-session.md
WARN layout: unexpected file '.gitattributes'
WARN layout: unexpected file '.qoder/skills/...'（共 7 条嵌套文件 WARN）
FAIL name: 'audit-skill-during-live-creation' does not match directory 'qoder-skills-main'
Summary: 8 pass, 1 fail, 8 warn
RESULT FAIL
```

同一命令对 `.qoder/skills/verify-skill-runtime-binding` 为：

```text
NESTED_QA_RC=0
Files (2): SKILL.md, scripts/locate_injection.py
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
```

## 3. 迁移命令与结果

迁移前 OID：

```text
100644 blob 39909164de38c336e07a15ee494d002c338b4ac3	SKILL.md
100644 blob de310c4d533437fb0743f3e4f41ffdc1d9eca68f	references/preuves-session.md
```

实际命令：

```bash
cd /c/Users/Administrateur/qoder-skills-main
mkdir -p .qoder/skills/audit-skill-during-live-creation/references
git mv SKILL.md .qoder/skills/audit-skill-during-live-creation/SKILL.md
git mv references/preuves-session.md .qoder/skills/audit-skill-during-live-creation/references/preuves-session.md
rmdir references 2>/dev/null
```

暂存结果：

```text
R  SKILL.md -> .qoder/skills/audit-skill-during-live-creation/SKILL.md
R  references/preuves-session.md -> .qoder/skills/audit-skill-during-live-creation/references/preuves-session.md

 SKILL.md => .qoder/skills/audit-skill-during-live-creation/SKILL.md       | 0
 .../audit-skill-during-live-creation/references}/preuves-session.md       | 0
 2 files changed, 0 insertions(+), 0 deletions(-)
```

迁移后索引 OID 未变：

```text
100644 39909164de38c336e07a15ee494d002c338b4ac3 0	.qoder/skills/audit-skill-during-live-creation/SKILL.md
100644 de310c4d533437fb0743f3e4f41ffdc1d9eca68f 0	.qoder/skills/audit-skill-during-live-creation/references/preuves-session.md
```

## 4. 验收、提交与推送

迁移包：

```text
QA_RC=0
Files (2): SKILL.md, references/preuves-session.md
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS

Skill: audit-skill-during-live-creation
All files: 2 | Clean: 2 | Caches: 0 | Unexpected: 0
QA Files (N): 2 | MATCH on-disk total 2
RESULT PASS
MANIFEST_RC=0
```

其余三个包复跑：

```text
verify-skill-runtime-binding rc=0 Files (2): SKILL.md, scripts/locate_injection.py | Summary: 9 pass, 0 fail, 0 warn | RESULT PASS
auditer-nettoyer-temp-qoder rc=0 Files (3): SKILL.md, references/cas-nettoyage-temp-qoder-2026-10-26.md, scripts/inventorier_tmp_qoder.py | Summary: 9 pass, 0 fail, 0 warn | RESULT PASS
adopt-concurrent-duplicate-skill rc=0 Files (2): SKILL.md, references/preuves-session.md | Summary: 10 pass, 0 fail, 0 warn | RESULT PASS
```

根检查与提交：

```text
ROOT_HAS_NO_SKILL
R  SKILL.md -> .qoder/skills/audit-skill-during-live-creation/SKILL.md
R  references/preuves-session.md -> .qoder/skills/audit-skill-during-live-creation/references/preuves-session.md

[main 3a9f519] docs(skill): archiver audit-skill-during-live-creation
 2 files changed, 0 insertions(+), 0 deletions(-)
 rename SKILL.md => .qoder/skills/audit-skill-during-live-creation/SKILL.md (100%)
 rename {references => .qoder/skills/audit-skill-during-live-creation/references}/preuves-session.md (100%)
```

推送与远端验证：

```text
To https://github.com/IMAM8MAHDI/qoder-skills.git
   3fa0460..3a9f519  main -> main
PUSH_RC=0

3a9f51909ada3fdeba91743ddfdb2b213a2d43f2	refs/heads/main
3a9f51909ada3fdeba91743ddfdb2b213a2d43f2
```

远端树：

```text
.gitattributes
.qoder/skills/adopt-concurrent-duplicate-skill/SKILL.md
.qoder/skills/adopt-concurrent-duplicate-skill/references/preuves-session.md
.qoder/skills/audit-skill-during-live-creation/SKILL.md
.qoder/skills/audit-skill-during-live-creation/references/preuves-session.md
.qoder/skills/auditer-nettoyer-temp-qoder/SKILL.md
.qoder/skills/auditer-nettoyer-temp-qoder/references/cas-nettoyage-temp-qoder-2026-10-26.md
.qoder/skills/auditer-nettoyer-temp-qoder/scripts/inventorier_tmp_qoder.py
.qoder/skills/verify-skill-runtime-binding/SKILL.md
.qoder/skills/verify-skill-runtime-binding/scripts/locate_injection.py
```

旧根路径检查：

```text
100644 blob c8950c1f...	.gitattributes
100644 blob 39909164...	.qoder/skills/audit-skill-during-live-creation/SKILL.md
100644 blob de310c4d...	.qoder/skills/audit-skill-during-live-creation/references/preuves-session.md
ROOT_LEFTOVER_RC=0
```

关键点：`git ls-tree origin/main -- SKILL.md references/preuves-session.md` 没有输出，但退出码仍是 0；判断根是否清空必须看输出，不能看 RC。来源会话随后用 `git ls-tree -r origin/main -- ...` 确认根只剩 `.gitattributes` 与 `.qoder/`。

## 5. 失败、纠正与用户选择

### 5.1 代理纠正了旧的包名结论

用户问“verify-skill-runtime-binding 的布局问题怎么修”。代理复查后写：“`verify-skill-runtime-binding` 本身的布局问题已经在 `main` 上修好了，现在 FAIL 的是仓库根目录另一只旧布局包。”根 `SKILL.md` 的实际 `name` 是 `audit-skill-during-live-creation`，不是 `verify-skill-runtime-binding`。

教训：目标名只从当前根 `SKILL.md` 的 frontmatter 读取；用户提到的名字、上一次会话的结论和旧报告都不能替代当前字节。

### 5.2 `git ls-tree -r -s` 不可用

实际输出：

```text
error: unknown switch `s'
usage: git ls-tree [<options>] <tree-ish> [<path>...]
```

随后改用 `git ls-files -s` 和 `git ls-tree -r`。Skill 中用 `git ls-tree -r` 或 `git ls-tree -r -l`。

### 5.3 中文内容经管道进入 Python 报 cp1252

实际命令：

```bash
head -c 600 SKILL.md | py -3 -c 'import sys; d=sys.stdin.buffer.read(); print(d.decode("utf-8", "replace"))'
```

实际错误：

```text
UnicodeEncodeError: 'charmap' codec can't encode characters ...
```

同一命令的前半段文件列表仍然输出，但退出码为 1。读取或比较含中文的内容时，使用 `PYTHONIOENCODING=utf-8`，或直接用 `sed`、`git cat-file`，不要把中文管道交给默认编码的 Python。

### 5.4 完成推送后用户再次要求 commit/push

用户 `2026-10-26T17:42:20.873Z` 执行 `commit -m "fix: standardize skills layout and enforce LF endings" && git push origin main`。实际状态：

```text
STATUS_RC=0
3a9f519 docs(skill): archiver audit-skill-during-live-creation
3fa0460 chore(skill): forcer les fins de ligne LF
3a9f51909ada3fdeba91743ddfdb2b213a2d43f2
3a9f51909ada3fdeba91743ddfdb2b213a2d43f2	refs/heads/main
```

工作区干净，`HEAD` 与 `origin/main` 都是 `3a9f519`，没有待提交内容。代理没有创建空提交，也没有改写已推送历史，而是让用户在“保持现状 / 压缩强推 / 空提交”之间选择。用户选择保持现状。

### 5.5 远端在推送期间前进

同一会话的 LF 提交推送时，远端在期间又前进了两次；代理重新 fetch、rebase 到最新 `main` 后推送成功，没有强推。迁移提交本身是在 fetch 后基于 `3a9f519` 的干净状态完成的。

### 5.6 未验证的推荐数据

自动推荐 JSON 称迁移前 manifest 报 `Unexpected`；本次读取窗口没有看到迁移前 manifest 的原始输出，因此 Skill 不把该说法写成已验证事实。只记录实际看到的：根 QA 为 8 pass / 1 fail / 8 warn；迁移后 manifest 为 `Unexpected 0`。

## 6. 2026-10-26 补充观察：根副本重新出现

对当前远端做只读 fetch 后：

```text
local HEAD        : 3a9f519
origin/main       : d4d8658
worktree          : clean
```

远端新增历史：

```text
d4d8658 docs(skill): actualiser l'archive lock-lf-endings-skill-repo
d22abcd docs(skill): consigner la verification HEAD du 2026-10-26
c818af6 docs(skill): archiver lock-lf-endings-skill-repo
8be9806 Merge origin/main into main
f8cd548 docs(skill): restaurer les fichiers du Skill à la racine
```

`f8cd548` 恢复了根 `SKILL.md` 与 `references/preuves-session.md`；`8be9806` 合并后它们进入远端 `main`。

远端根与嵌套副本逐 blob 相同：

```text
root   SKILL.md                      = 6470a52525afe50444181362259a6aac6683dcad
nested SKILL.md                      = 6470a52525afe50444181362259a6aac6683dcad
root   references/preuves-session.md = f319a3ea6e9f96759a3cc7693066828771128026
nested references/preuves-session.md = f319a3ea6e9f96759a3cc7693066828771128026
```

内容 SHA-256：

```text
6470a525...  1d21612d0c6a833561c974c279511c24e9824fabef1e8c84a76bdabd3acf3133
f319a3ea...  c600017211e1976bf3d6af642082f43f136998bfe12a8ba4cda25ec574fabee3
```

用 `git archive origin/main` 解到临时目录 `qoder-skills-main` 后，对根跑 QA：

```text
Files (14): .gitattributes, ... (+4)
WARN layout: unexpected file '.gitattributes'
WARN layout: unexpected file '.qoder/skills/...'（共 11 条嵌套文件 WARN）
FAIL name: 'adopt-concurrent-duplicate-skill' does not match directory 'qoder-skills-main'
Summary: 9 pass, 1 fail, 12 warn
RESULT FAIL
```

这是情况 B：目标 `.qoder/skills/adopt-concurrent-duplicate-skill/` 已存在，根副本与它逐 blob 相同。按本 Skill 的默认策略，只读报告并等待用户确认；不自动删除、不自动推送。临时 archive 已删除。

## 7. 当前状态的本地复核

在本地 `HEAD=3a9f519` 上复跑 4 个嵌套包：

```text
adopt-concurrent-duplicate-skill rc=0 Files (2) Summary: 10 pass, 0 fail, 0 warn RESULT PASS
audit-skill-during-live-creation rc=0 Files (2) Summary: 9 pass, 0 fail, 0 warn RESULT PASS
auditer-nettoyer-temp-qoder rc=0 Files (3) Summary: 9 pass, 0 fail, 0 warn RESULT PASS
verify-skill-runtime-binding rc=0 Files (2) Summary: 9 pass, 0 fail, 0 warn RESULT PASS
```

manifest 全部 `Unexpected 0`、`MATCH on-disk total N`、`RESULT PASS`；复跑前后 `git status --porcelain` 为空。远端 `d4d8658` 还包含 `lock-lf-endings-skill-repo`，本地 `3a9f519` 没有该包，因此没有对远端 5 个包全部复跑。

## 8. 未验证与边界

- 根包含 `scripts/` 或 `assets/` 的迁移未实测。
- 非 LF 仓库、`core.autocrlf=true` 导致 rename 显示为内容变化的场景未实测。
- 非 GitHub 远端、受保护分支、需要 PR 的仓库未实测。
- 远端 `d4d8658` 上 5 个包没有逐个跑 QA；只对根做了临时 archive QA。
- 来源会话完整 1,252 行未逐行读取；迁移回合与相邻工具输入/输出已逐字核对。
- 本文不把“迁移后根 QA 仍应 PASS”当作规则：根不再是 Skill 包，验收对象是 `.qoder/skills/<name>/`。

## 9. 本地夹具验证（2026-10-26）

在 `~/.qoder/tmp` 建一次性裸 origin 与临时克隆，仓库含一个嵌套包 `existing`、根包 `demo-skill`（`SKILL.md` + `references/note.md`）和根 `.gitattributes`。执行本 Skill 的迁移命令后：

```text
TARGET_EXISTS_BEFORE=no
R  SKILL.md -> .qoder/skills/demo-skill/SKILL.md
R  references/note.md -> .qoder/skills/demo-skill/references/note.md
 SKILL.md => .qoder/skills/demo-skill/SKILL.md               | 0
 {references => .qoder/skills/demo-skill/references}/note.md | 0
 2 files changed, 0 insertions(+), 0 deletions(-)
R100	SKILL.md	.qoder/skills/demo-skill/SKILL.md
R100	references/note.md	.qoder/skills/demo-skill/references/note.md
A_OIDS_UNCHANGED
A_QA_RC=0
Files (2): SKILL.md, references/note.md
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
A_MANIFEST_RC=0
All files: 2 | Clean: 2 | Caches: 0 | Unexpected: 0
QA Files (N): 2 | MATCH on-disk total 2
RESULT PASS
```

重复与冲突分支：

```text
B_ROOT_SKILL=7f010c00e513132ec8579d2664d354f4e9033c73 B_TARGET_SKILL=7f010c00e513132ec8579d2664d354f4e9033c73
B_ROOT_REF=796e90dba6761fd6e44aed9b91fa535a6fb42872 B_TARGET_REF=796e90dba6761fd6e44aed9b91fa535a6fb42872
B_IDENTICAL
B_TARGET_EXISTS

C_ROOT_SKILL=560c936d1f5d2eb372ea636f277d46b00aa97623 C_TARGET_SKILL=7f010c00e513132ec8579d2664d354f4e9033c73
C_DIFFERENT
```

负例：

```text
LS_TREE_S_RC=129
error: unknown switch `s'
usage: git ls-tree [<options>] <tree-ish> [<path>...]

EMPTY_PATH_RC=0 OUT=[]
```

夹具目录已 `chmod -R u+w` 后删除，`FIXTURE_REMOVED`；没有修改 `qoder-skills-main`，没有推送。该夹具只验证了 `SKILL.md` + 单层 `references/` 的迁移；`scripts/`、`assets/`、嵌套 references、非 LF 仓库仍未实测。
