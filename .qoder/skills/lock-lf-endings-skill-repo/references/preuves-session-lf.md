# 来源会话与逐字复跑证据

## 来源

- Qoder 来源会话：`484dd08b-df03-40b3-a174-a469bac21a9b`（2026-10-26）。
- 执行复验会话：`b601b664-d780-4f12-8ac1-019c55232294`（2026-10-26T12:30Z 与 12:36Z）。该会话实际调用本 Skill 写入根 `.gitattributes`、提交、克隆验证并切换到 `.git/info/attributes`；证据见“执行复验”一节。
- 后续实测会话：`ef2d6bc1-abb7-49b0-b0ef-ccfdeafa4754`（2026-10-26T14:35:32Z，本地 15:35 +01:00）。该轮在 `write-skill-evidence-case-study` 写入根 `.gitattributes`、提交并做克隆验证；证据见“后续观察”。
- 未跟踪属性文件与 cp1252 输出：会话 `ae97a7bf-2013-4366-b5ed-20d659cc2808`（2026-10-26T15:25Z–15:28Z）。该轮在 `diagnostiquer-push-github-depot-absent` 写入根 `.gitattributes`；证据见“未跟踪属性文件与 cp1252 输出”。
- 新增属性文件 OID 与 pass 数：会话 `ae0ac1d8-95e7-4da0-a623-7bab048275a3`（2026-10-26T17:13Z）。该轮在 `adopt-concurrent-duplicate-skill` 按根方案执行；证据见“新增属性文件 OID 与 QA pass 数”。
- 参考仓库：`C:\Users\Administrateur\.qoder\skills\dependency-script-contract-reaudit`。
- 工具版本：`git version 2.52.0.windows.1`；Python `3.14.7`（用 `py -3` 调用）。
- 系统 Git 配置：`file:C:/Program Files/Git/etc/gitconfig` → `core.autocrlf=true`。
- 本文件记录来源会话证据、并发创建时的复验、执行会话与后续实测的复验。各轮分开标注，不把复验写成来源会话的原话。
- 2026-10-26 接管后改为纯文档交付：只保留 SKILL.md 与本文，不随附脚本；复跑命令改为内联形式，历史复验数据保持原样。

## 初始状态

两个已跟踪文件在工作区已经是 LF，但没有任何属性：

```text
$ git ls-files --eol
i/lf    w/lf    attr/                 	SKILL.md
i/lf    w/lf    attr/                 	references/contrat-find-stale-archives.md
```

| 文件 | 大小 | SHA-256 | blob OID |
|---|---:|---|---|
| `SKILL.md` | 8239 B | `17abe9dcab7869be30c71ee5ab3897aba3f5dac5e86bb70fe44017d31309f8ff` | `7c31ec8a9cc23a6798e1df9c58c406ceb751ab87` |
| `references/contrat-find-stale-archives.md` | 6118 B | `7ce7ced9a81d9db6762bd813af71b352a107024e6b0fb25627da8310e6c27a9d` | `272825425cf1aced577ab1cb891166c468a09f1c` |

此时 `w/lf` 只说明当前工作区是 LF；`core.autocrlf=true` 仍会在下一次 checkout 写入 CRLF。

## 方案 A：根 `.gitattributes`

写入内容（95 B）：

```gitattributes
# 仓库与工作区统一使用 LF，覆盖系统的 core.autocrlf=true。
* text=auto eol=lf
```

- SHA-256：`ee5e05fe66360bb3b3fc6c056c54a65f668ea49be8e8e087b18bcda28ede3f2b`
- blob OID：`c8950c1f1fb583eb1aa4ce93fc24f997064130f4`
- `git check-attr text eol`：三个文件均为 `text: auto`、`eol: lf`。
- `git ls-files --eol`：三个文件均为 `i/lf w/lf attr/text=auto eol=lf`。
- `git add --renormalize` 没有产生额外文件改动；两个 Markdown 文件的 blob OID 保持 `7c31ec8a…`、`27282542…`。
- 在 `core.autocrlf=true` 下全新克隆：三个文件均为 `w/lf`；字节检查：

```text
SKILL.md: bytes=8239 CR=0 LF=136
references/contrat-find-stale-archives.md: bytes=6118 CR=0 LF=146
.gitattributes: bytes=95 CR=0 LF=2
```

- `skill-file-qa`：`RESULT PASS`，9 pass / 0 fail / 1 warn，`Files (3)`；警告为 `layout: unexpected file '.gitattributes'`。
- `check_package_manifest.py`：`RESULT FAIL`，`All files: 3 | Clean: 3 | Caches: 0 | Unexpected: 1`，`UNEXPECTED .gitattributes`，退出 1。
- 2026-10-26 后续观察：本机工作区版脚本已允许 `.gitattributes`，同一根方案实测为 PASS；上述 FAIL 属于当时脚本版本，原文保留，见“后续观察：manifest 白名单变化”。
- 提交：`fa59e09d030d259b214cc542afe34c62798ed57d`，父提交 `f993fc726ac2934c50cd912efd02ff71df974216`，标题 `chore(skill): forcer les fins de ligne LF`。

## 方案 B：`.git/info/attributes`

删除根文件，把同一规则写入 `.git/info/attributes`（95 B）：

```gitattributes
# 本仓库工作区统一使用 LF，覆盖系统的 core.autocrlf=true。
* text=auto eol=lf
```

- SHA-256：`3433308a8b1360f5e8499cfa3da9094566988da8d162a857509d2a751823f972`
- `git check-attr`：两个文件均为 `text: auto`、`eol: lf`。
- `git ls-files --eol`：两个文件均为 `i/lf w/lf attr/text=auto eol=lf`。
- 实际检出探针：`git -c core.autocrlf=true checkout-index -a --prefix=<tmp>/`，输出：

```text
SKILL.md: bytes=8239 CR=0 LF=136
references/contrat-find-stale-archives.md: bytes=6118 CR=0 LF=146
```

- `skill-file-qa`：`RESULT PASS`，9 pass / 0 fail / 0 warn，`Files (2)`。
- `check_package_manifest.py`：`RESULT PASS`，`All files: 2 | Clean: 2 | Caches: 0 | Unexpected: 0`，退出 0。来源会话这次没有传 `--qa-log`，因此显示 `QA Files (N): NOT CHECKED`；这不等于计数不匹配。
- 提交：`96ca6f9157cde61e5b9f29aab1fef039203466c6`，父提交 `fa59e09d030d259b214cc542afe34c62798ed57d`，标题 `chore(skill): deplacer les fins de ligne LF vers .git/info/attributes`，变更 1 个文件、删除 2 行。
- 工作区干净；两个 Markdown 文件 SHA-256 未变；仓库没有 remote，未推送。

## 执行复验（会话 b601b664，2026-10-26）

目标仓库：`C:\Users\Administrateur\.qoder\skills\commit-skill-work`（4 个文件，HEAD `695dea2`）。用户请求逐字为 `add .gitattributes to enforce LF line endings`，没有要求提交。

### 根方案（12:30Z）

- 初始：`core.autocrlf` 本地/全局未设，系统 `file:C:/Program Files/Git/etc/gitconfig` 为 `true`；4 个文件均 `i/lf w/lf attr/`。
- 写入根 `.gitattributes`（95 B，SHA-256 `ee5e05fe66360bb3b3fc6c056c54a65f668ea49be8e8e087b18bcda28ede3f2b`）；`git status` 为 `?? .gitattributes`。
- `git check-attr`：4 个文件均 `text: auto`、`eol: lf`；`git ls-files --eol`：4 个文件均 `i/lf w/lf attr/text=auto eol=lf`。
- `git add --renormalize` 后 4 个 blob OID 未变：`071099e8…`、`c71b41e2…`、`6b1f8406…`、`8f073ab9…`。
- worktree 字节：`SKILL.md` 40343 B、`references/skill-zh.md` 34042 B、两个脚本 9887 / 6329 B，CR 均为 0；`checkout-index` 探针（`core.autocrlf=true`）同样 CR=0，`cleanup=0`。
- `skill-file-qa`：`RESULT PASS`，9 pass / 0 fail / 1 warn，`Files (5)`；警告为 `layout: unexpected file '.gitattributes'`。
- `check_package_manifest.py`：`RESULT FAIL`，`All files: 5 | Clean: 5 | Caches: 0 | Unexpected: 1`，`UNEXPECTED .gitattributes`，退出 1。
- 提交 `b6cd6ee chore(skill): forcer les fins de ligne LF`（父 `695dea2`）。**用户没有明确授权提交**，这是流程缺口，不是用户纠正。
- 克隆探针在提交之后才执行：`git -c core.autocrlf=true clone` 后 5 个文件均 `i/lf w/lf attr/text=auto eol=lf`、CR=0；`SKILL.md` 两侧 SHA-256 均为 `f6e033ddf8a4d60dfa49cc57fa71dbef1e5c7af2d5264ae64949d8eef13a4c8d`。
- 克隆清理先用了 `py -3 -c "import shutil,sys; shutil.rmtree(sys.argv[1])"`，失败：

```text
PermissionError: [WinError 5] Accès refusé: '.../lf-clone-commit-skill-work\\.git\\objects\\07\\1099e86832da7d6e03a91f6fc35b857cc7024b'
cleanup=1
```

- 改用 `chmod -R u+w "$TMP" && rm -rf "$TMP"`：`cleanup=0`、`REMOVED`；`.gitattributes` 的 SHA-256 仍为 `ee5e05fe…`。

### 本地方案（12:36Z）

- 用户逐字请求：`switch to .git/info/attributes`。
- 写入 `.git/info/attributes`（95 B，同一规则，注释改为“本仓库”）；删除根文件并提交 `e7af50a chore(skill): deplacer les fins de ligne LF vers .git/info/attributes`。这次提交同样没有明确的提交授权。
- 属性仍生效：4 个文件均 `text: auto`、`eol: lf`、`i/lf w/lf attr/text=auto eol=lf`；blob OID 未变。
- `checkout-index` 探针：CR=0，`cleanup=0`。
- `skill-file-qa`：`RESULT PASS`，9 pass / 0 fail / 0 warn，`Files (4)`。
- `check_package_manifest.py`：`RESULT PASS`，`All files: 4 | Clean: 4 | Caches: 0 | Unexpected: 0`、`QA Files (N): MATCH`，退出 0。
- `.git/info/attributes` 按设计不被跟踪（`git ls-files --error-unmatch` 退出 1），工作区干净，未推送。

### 结论

- 根方案的克隆探针必须在提交后运行；文件只在工作区时克隆不带规则，不能用克隆结果判断成败。
- Windows 上克隆的 `.git/objects` 是只读的，`shutil.rmtree` 会失败；清理统一用 `chmod -R u+w` + `rm -rf`，并以 `test -e` 复核。
- “添加文件”不等于“授权提交”；未授权时保持未跟踪，报告 `clone proof: pending`。

## `grep` 陷阱的原始证据

在同一工作区先执行了 `grep -c $'\r'`，输出被误当成 CRLF 行数：

```text
136 SKILL.md
146 references/contrat-find-stale-archives.md
2 .gitattributes
```

这些数字其实是文件总行数。Git Bash 把 `$'\r'` 剥成了空模式，`grep` 匹配了每一行。改用 Python 字节计数后：

```text
SKILL.md: bytes=8239 CR=0 LF=136
references/contrat-find-stale-archives.md: bytes=6118 CR=0 LF=146
.gitattributes: bytes=95 CR=0 LF=2
```

结论：不要用 `grep` 统计 CR；用 `data.count(b"\r")` 或 `git ls-files --eol`。

## 自包含夹具（本次复验，2026-10-26）

目的：证明 `checkout-index` 探针能区分“没有规则”与“有规则”，而不是只看 `w/lf`。

```bash
BASE="$HOME/.qoder/tmp/lf-fixture"
mkdir -p "$BASE/repo" "$BASE/out1" "$BASE/out2"
cd "$BASE/repo"
git init -q
git config core.autocrlf true
printf 'alpha\nbeta\n' > file.txt
git add file.txt
git ls-files --eol
git -c core.autocrlf=true checkout-index -a --prefix="$BASE/out1/"
printf '* text=auto eol=lf\n' > .git/info/attributes
git ls-files --eol
git -c core.autocrlf=true checkout-index -a --prefix="$BASE/out2/"
```

实测：

```text
# 无属性
i/lf    w/lf    attr/                 	file.txt

# 写入 .git/info/attributes 后
i/lf    w/lf    attr/text=auto eol=lf 	file.txt

out1: bytes=13 CR=2 LF=2
out2: bytes=11 CR=0 LF=2
```

解释：

- 无属性时，索引是 LF，但探针在 `core.autocrlf=true` 下写出 CRLF（13 B，CR=2）。
- 写入 `.git/info/attributes` 后，同一探针写出 LF（11 B，CR=0）。
- 所以 `w/lf` 不是未来检出的证据；必须实际检出并统计字节。

清理：只删除本次创建的 `$BASE`，并确认路径不存在。

## 复跑命令

本 Skill 不随附脚本；用内联命令复验。逐文件字节统计：

```bash
git -C "<repo>" ls-files -z | while IFS= read -r -d '' rel; do
  py -3 -c 'from pathlib import Path; import sys; d=Path(sys.argv[1]).read_bytes(); print(sys.argv[2], "bytes=%d CR=%d LF=%d" % (len(d), d.count(b"\r"), d.count(b"\n")))' \
    "<repo>/$rel" "$rel"
done
```

真实检出探针（本地方案用，只证明本副本）：

```bash
TMP="<temp>/lf-probe"
rm -rf "$TMP"
mkdir -p "$TMP"
git -C "<repo>" -c core.autocrlf=true checkout-index -a --prefix="$TMP/"
git -C "<repo>" ls-files -z | while IFS= read -r -d '' rel; do
  py -3 -c 'from pathlib import Path; import sys; d=Path(sys.argv[1]).read_bytes(); print(sys.argv[2], "bytes=%d CR=%d LF=%d" % (len(d), d.count(b"\r"), d.count(b"\n")))' \
    "$TMP/$rel" "$rel"
done
chmod -R u+w "$TMP" && rm -rf "$TMP"
test -e "$TMP" && echo "STILL_EXISTS" || echo "REMOVED"
```

根方案额外做克隆验证（必须在提交后）：

```bash
git -C "<repo>" cat-file -e HEAD:.gitattributes
TMP="<temp>/clone"
rm -rf "$TMP"
git -c core.autocrlf=true clone "<repo>" "$TMP"
test -f "$TMP/.gitattributes" && echo "ATTR_PRESENT" || echo "MISSING_ATTR_IN_CLONE"
git -C "$TMP" ls-files --eol
chmod -R u+w "$TMP" && rm -rf "$TMP"
test -e "$TMP" && echo "STILL_EXISTS" || echo "REMOVED"
```

未提交时跳过克隆验证，报告 `clone proof: pending`。本地方案不要用克隆证明 LF；克隆不包含 `.git/info/attributes`。

## 后续观察：manifest 白名单变化（2026-10-26）

会话 `ef2d6bc1` 于 2026-10-26T14:35:32Z（本地 15:35 +01:00）在 `C:\Users\Administrateur\.qoder\skills\write-skill-evidence-case-study` 按根方案写入 `.gitattributes`：

- 文件 95 B，SHA-256 `ee5e05fe66360bb3b3fc6c056c54a65f668ea49be8e8e087b18bcda28ede3f2b`，blob OID `c8950c1f1fb583eb1aa4ce93fc24f997064130f4`；提交 `d420ccb chore(skill): forcer les fins de ligne LF`。
- `skill-file-qa`：`Files (3): .gitattributes, SKILL.md, references/cas-live-creation-2026-10-26.md`，`9 pass / 0 fail / 1 warn`，`RESULT PASS`，`QA_EXIT=0`；WARN 为 `layout: unexpected file '.gitattributes'`。
- `check_package_manifest.py`：`All files: 3 | Clean: 3 | Caches: 0 | Unexpected: 0`，`QA Files (N): 3 | MATCH on-disk total 3`，`RESULT PASS`，`MANIFEST_EXIT=0`。
- 克隆（`git -c core.autocrlf=true clone`）：`CLONE_EXIT=0`、`ATTR_PRESENT`、3 个文件均 `i/lf w/lf attr/text=auto eol=lf`、CR=0，两侧 `SKILL.md` 与 reference 的 SHA-256 一致；临时目录 `REMOVED`。

原因：该轮使用的工作区脚本含未提交改动：

```diff
 ALLOWED_DIRS = {"scripts", "references", "assets"}
+ALLOWED_FILES = {"SKILL.md", ".gitattributes"}
...
-        if rel == "SKILL.md":
+        if rel in ALLOWED_FILES:
```

`git -C .../skill-package-integrity-audit status --short` 显示 `M scripts/check_package_manifest.py`；HEAD `7a39419` 的版本只跳过 `SKILL.md`，没有 `ALLOWED_FILES`，所以旧版本仍会把根 `.gitattributes` 报成 `UNEXPECTED` 并退出 1。

2026-10-26 对 `lock-lf-endings-skill-repo` 自身复跑（同一未提交脚本）：`Files (3)`、`9 pass / 0 fail / 1 warn`、`RESULT PASS`；manifest `All files: 3 | Clean: 3 | Unexpected: 0`、`RESULT PASS`、`MANIFEST_EXIT=0`。

结论：根方案的 manifest 结果不是固定值，取决于已安装脚本的允许清单与版本；必须实跑并报告实际输出与退出码。`ALLOWED_FILES` 是另一个 Skill 的工作区改动，不属于本 Skill，也不应被本 Skill 修改或当作稳定契约。

## 未跟踪属性文件与 cp1252 输出（会话 ae97a7bf，2026-10-26）

- 目标仓库：`C:\Users\Administrateur\.qoder\skills\diagnostiquer-push-github-depot-absent`；HEAD `02450cd`；两个已跟踪文件；系统 `core.autocrlf=true`，local/global 未设置。
- 写入根 `.gitattributes`（95 B，SHA-256 `ee5e05fe66360bb3b3fc6c056c54a65f668ea49be8e8e087b18bcda28ede3f2b`）后，`git ls-files` 字节循环只输出 `SKILL.md` 与 `scripts/probe_github_repo.py`；未提交的属性文件不在枚举内。
- 同一命令内先用 `print(repr(d.decode('utf-8')))` 打印内容，结果退出 1：

```text
bytes=95 CR=0 LF=2 BOM=False
Traceback (most recent call last):
  ...
UnicodeEncodeError: 'charmap' codec can't encode characters in position 3-12: character maps to <undefined>
```

- 字节行已打印；失败发生在输出中文注释时，不是文件内容或字节统计错误。
- 改为 `print(d.decode('utf-8').encode('unicode_escape').decode('ascii'))` 后退出 0：

```text
bytes=95 CR=0 LF=2 BOM=False
# \u4ed3\u5e93\u4e0e\u5de5\u4f5c\u533a\u7edf\u4e00\u4f7f\u7528 LF\uff0c\u8986\u76d6\u7cfb\u7edf\u7684 core.autocrlf=true\u3002\n* text=auto eol=lf\n
```

- 2026-10-26 对本 Skill 自身的 95 B `.gitattributes` 复跑：`repr` 路线退出 1（position 3-12）；`unicode_escape` 路线退出 0；`PYTHONIOENCODING=utf-8` 路线退出 0。
- 该轮其余步骤按 SKILL.md 通过：`git add --renormalize` 后两个 blob OID 未变（`ece89aa0…`、`0db9aaf5…`）；`skill-file-qa` `RESULT PASS`（9 pass / 0 fail / 1 warn，`Files (3)`）；manifest `RESULT PASS`（`Unexpected 0`，退出 0）；提交 `58539df chore(skill): forcer les fins de ligne LF`；克隆（`core.autocrlf=true`）中 3 个文件均 `i/lf w/lf attr/text=auto eol=lf`、CR=0，SHA-256 与源一致。
- 结论：属性文件在 `git add` 前必须单独核对；内容输出用 ASCII 转义，不能直接打印中文或 `repr` 结果。

## HEAD 指针与工作区对账（会话 324c8787，2026-10-26）

- 仓库根同时是本 Skill 根：`C:\Users\Administrateur\.qoder\skills\lock-lf-endings-skill-repo`；仓库创建提示 `2026-10-26T13:30:19+01:00`，根提交 `42bedae79696c99fb6c1e3dd9778105b44c0e36a`（`2026-10-26T13:30:52+01:00`）。
- `.git/HEAD` 内容为 `ref: refs/heads/main`；`git symbolic-ref HEAD` 返回 `refs/heads/main`；`git for-each-ref refs/heads` 只有 `refs/heads/main 76a011d63f1abe62daae0d6ec6246cbd49966822 commit`。
- `HEAD`、`HEAD^{commit}` 与 `refs/heads/main` 三个写法都解析到 `76a011d63f1abe62daae0d6ec6246cbd49966822`；提交标题 `fix(skill): controler les octets de .gitattributes avant commit`，提交时间 `2026-10-26T16:40:57+01:00`。
- `HEAD^{tree}` 为 `7ff48892085917771fcc7b954e13f89da5e08383`；`git ls-tree -r HEAD`：

```text
100644 blob c8950c1f1fb583eb1aa4ce93fc24f997064130f4	.gitattributes
100644 blob 523e9cd608924582c2f59af8f457c44d5d2ce3d4	SKILL.md
100644 blob 6b4818170a63241a343ec8c7f5670be29d8c57e0	references/preuves-session-lf.md
```

- reflog 顶部：`HEAD@{0}` = `76a011d`、`HEAD@{1}` = `e6a6e5f`、`HEAD@{2}` = `a388c24`；`git rev-parse --is-shallow-repository` 为 `false`；只有一个工作树，位于 Skill 根并检出 `refs/heads/main`。
- `verify-skill-git-head-vs-worktree` 带 `--expect-sha256` 执行，把 `SKILL.md=d7aa51b70ef970c87fb6d4aaf451b4e6aa964ae15b3e63feb1aa8ec5cfe4ac8c` 与 `references/preuves-session-lf.md=cc8ff90d724c0fabcd7b9f361332f2bf524480ce7c82c83b6ff25525d1d55ad4` 绑定到 HEAD blob：`FILES: 3`、`DIVERGENT: 0`、`IGNORED: 0`，两个期望文件均 `MATCH_BYTES`，`FLAG: AUTOCRLF_TRUE`、`VERDICT: RECONCILED`、`RESULT RECONCILED`，退出 0。
- 同一工具报告索引未被改动：`INDEX size=348 mtime_ns=1793029257773789800 sha256=648d7bb82f9957b19ea06f229dd0d3a8d0e577a98cb21cf2ab3639728faedf8d`、`INDEX_UNCHANGED: True`；该脚本只读，不执行 `add`、`commit` 或 `checkout`。
- 对账时 `core.autocrlf=true`（来源 `file:C:/Program Files/Git/etc/gitconfig`），三个受跟踪文件仍全部 `MATCH_BYTES`，说明 LF 由已提交的根 `.gitattributes` 保住，而不是靠本机 Git 配置。
- 结论：QA 指纹绑定的磁盘版本就是提交 `76a011d` 的树；HEAD 指向 `refs/heads/main`（非分离头指针），三个受跟踪文件相对 HEAD 无字节分歧。

## 新增属性文件 OID 与 QA pass 数（会话 ae0ac1d8，2026-10-26）

- 目标仓库：`C:\Users\Administrateur\.qoder\skills\adopt-concurrent-duplicate-skill`；分支 `master`；起始 HEAD `4b19c34`（`docs(skill): 补充多写入者归因与验收计数不变量`）。
- 用户请求逐字为 `加 .gitattributes 固定 LF`；`core.autocrlf` 仅系统级 `file:C:/Program Files/Git/etc/gitconfig` 为 `true`，local/global 未设置。
- 初始两个已跟踪文件：`SKILL.md` blob `27a5f096…`、SHA-256 `0e71fcd0…`（25619 B）；`references/preuves-session.md` blob `1710514a…`、SHA-256 `000c7fd2…`（22666 B）。
- 写入根 `.gitattributes`（95 B，`CR=0 LF=2 BOM=False`）；`git check-attr` 为 `text: auto` / `eol: lf`；`--renormalize` 后两个已跟踪 blob 未变。
- `skill-file-qa`：`Files (3)`，`WARN layout: unexpected file '.gitattributes'`，`Summary: 10 pass, 0 fail, 1 warn`，`RESULT PASS`，`QA_EXIT=0`。该目标的 `adopt-concurrent-duplicate-skill/SKILL.md:154` 含 Python 围栏代码块；本 Skill 不含同类块，同一校验器为 9 pass。pass 数随包内容变化，不是固定契约。
- `check_package_manifest.py`：`All files: 3 | Clean: 3 | Caches: 0 | Unexpected: 0`，`QA Files (N): 3 | MATCH on-disk total 3`，`RESULT PASS`，`MANIFEST_EXIT=0`。
- 用户经询问授权提交（`提交 .gitattributes（推荐）`）。执行 `git add -- .gitattributes` 后，索引 OID 检查输出：

```text
index=:/.gitattributes expected=c8950c1f1fb583eb1aa4ce93fc24f997064130f4 MISMATCH
```

- 该检查没有阻止提交：`b27ec86 chore(skill): forcer les fins de ligne LF`（完整提交 `b27ec861c29058f30cbb6e2dc9cd7b5c51bef537`，父 `4b19c34`，1 个文件、2 行新增）。
- 提交后改用正确写法复核，`index`、`HEAD`、`hash-object` 三者为同一 OID：

```text
.gitattributes index=c8950c1f1fb583eb1aa4ce93fc24f997064130f4 HEAD=c8950c1f1fb583eb1aa4ce93fc24f997064130f4 source=c8950c1f1fb583eb1aa4ce93fc24f997064130f4 MATCH
SKILL.md index=27a5f09644559ba72d370b8c0c78fafab6ee23b7 HEAD=27a5f09644559ba72d370b8c0c78fafab6ee23b7 source=27a5f09644559ba72d370b8c0c78fafab6ee23b7 MATCH
references/preuves-session.md index=1710514a7fe94fb299d5df4e916f45c94ee4e1d6 HEAD=1710514a7fe94fb299d5df4e916f45c94ee4e1d6 source=1710514a7fe94fb299d5df4e916f45c94ee4e1d6 MATCH
```

- 克隆验证（`git -c core.autocrlf=true clone`）：`CLONE_EXIT=0`、`ATTR_PRESENT`，3 个文件均 `i/lf w/lf attr/text=auto eol=lf`；字节 `.gitattributes 95 CR=0 LF=2`、`SKILL.md 25619 CR=0 LF=268`、`references/preuves-session.md 22666 CR=0 LF=462`；两侧 `SKILL.md` 与 reference 的 SHA-256 一致；`CLONE_REMOVED`。
- `.git/info/attributes` 不存在，工作区干净，无缓存，未执行推送。
- 2026-10-26 本次更新复核（临时夹具）：`git rev-parse --verify :/.gitattributes` 返回 `fatal: Needed a single revision`（退出 128）；`:.gitattributes`、`:./.gitattributes` 与 `git hash-object --path=.gitattributes` 返回同一 OID。`:/` 不是索引路径写法；失败结果若被脚本原样打印，会形成假 MISMATCH。
- 本文件既有的 9 pass 记录保持原样，是各自轮次的实测值；不要据此把 9 写成固定预期。

## 限制与边界

- `skill-file-qa` 的 pass 数随包内容变化：含 Python 围栏代码块时会多一条 `python blocks` 通过项；只断言 PASS、0 fail、WARN 与 Files，不写死 pass 数。
- 索引 OID 必须用 `:` 或 `:./` 取；`:/` 是提交消息检索语法，本机实测失败（退出 128），失败结果被原样打印时会形成假 MISMATCH。
- `.git/info/attributes` 只保护当前工作副本；克隆、复制到别处或发布归档后规则消失，`core.autocrlf=true` 可能重新带出 CRLF。
- 根 `.gitattributes` 只有提交后才随克隆分发；文件未进入 HEAD 时只对当前工作区与索引生效，克隆和归档都不含规则。
- Windows 上克隆目录内的 `.git/objects` 为只读；清理前必须 `chmod -R u+w`，且只作用于临时目录。
- 根 `.gitattributes` 会随仓库分发；manifest 是否报 `UNEXPECTED` 取决于脚本版本：HEAD `7a39419` 会把根文件报成 `UNEXPECTED` 并返回 1，2026-10-26 本机工作区版含 `.gitattributes` 允许项则为 PASS（见“后续观察”）。放宽白名单属于修改另一个 Skill，需要单独授权。
- 来源仓库历史保留了 `fa59e09`（新增根文件）与 `96ca6f9`（删除根文件）这一对提交；压缩历史需要改写提交，来源会话没有执行。
- 来源会话没有 remote，也没有推送；本 Skill 的复验同样不执行 fetch、push 或 remote 变更。
- `git ls-files --eol` 的 `w/lf` 是当前快照；`i/lf` 只说明索引内容。两者都不能单独证明下一次 checkout。
- 二进制、符号链接和子模块不适用 LF 策略；用 `git check-attr text` 的 `-text` 识别并跳过，不计入文本文件的锁定判定。
