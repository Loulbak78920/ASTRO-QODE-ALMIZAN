---
name: lock-lf-endings-skill-repo
description: "在 Windows（core.autocrlf=true）下为 Skill 的 Git 仓库锁定 LF 行尾：先审计 core.autocrlf 与 git ls-files --eol，再在根 .gitattributes（随克隆分发；manifest 结果取决于已安装脚本版本，须实跑，QA 通常留 1 条 WARN）与 .git/info/attributes（仅当前副本生效、两项审计可保持 PASS 且 0 WARN，但不随克隆分发）之间选择，用 git add --renormalize 证明已跟踪 blob 未变，分别用全新克隆或 git checkout-index 做字节级 CR=0 验证，独立提交并报告取舍。用于 Skill 仓库出现 CRLF、SHA-256 因 checkout 漂移、需要固定 LF、要决定属性文件放哪里、或校验器因 .gitattributes 报 WARN/UNEXPECTED 时；中文触发：锁定 LF、行尾、CRLF、autocrlf、.gitattributes、.git/info/attributes。"
---

# 为 Skill 的 Git 仓库锁定 LF 行尾

## 交付范围（2026-10-26）

本版本只交付本 SKILL.md 与 `references/preuves-session-lf.md`。所有检查都使用 `git` 与 `py -3` 的内联命令，不依赖、也不随附辅助脚本；目录中若出现未在本文件登记的脚本，视为范围外文件，不是本 Skill 的已验证组成部分。

## 目标

在 Windows 且 `core.autocrlf=true` 的环境中，把 Skill 仓库的行尾策略固定为 LF，并用字节级证据证明当前工作区、索引和实际检出都没有 CR。属性文件放在根 `.gitattributes` 还是 `.git/info/attributes` 有明确取舍，必须显式选择并向用户报告。

## 适用与不适用

适用：

- Skill 仓库在 `core.autocrlf=true` 下检出，担心下次 checkout 把 LF 变成 CRLF，导致文件 SHA-256 漂移。
- 需要决定行尾规则放在根 `.gitattributes` 还是本地的 `.git/info/attributes`。
- `skill-file-qa` 因 `.gitattributes` 报 WARN，或需要判断 `check_package_manifest.py` 是否把根 `.gitattributes` 报成 `UNEXPECTED` / `RESULT FAIL`（取决于已安装脚本版本）。
- 需要提交一次独立的行尾策略变更，并保留可复跑的验证证据。

不适用：

- 非 Git 目录，或只想临时改一次文件编码。
- 修改全局或系统 Git 配置；本 Skill 只锁定单个仓库。
- 改写已发布的 Git 历史、压缩提交或强推。
- 放宽另一个 Skill 的包审计白名单；那需要单独指令。

## 不可协商约束

1. 只写入选定的属性文件；不要手工重写 `SKILL.md`、脚本或参考文件来“修正”行尾。
2. 不改 `core.autocrlf` 的全局/系统值，不运行 `git config --global`。
3. 不用 `git add -A` 或 `git add .`；只添加明确路径。
4. 提交前先分清本次改动与预先存在的改动；出现意外脏文件时停止并报告，不擅自 stash、reset 或 checkout。
5. 不推送、不新建 remote。提交需要用户明确授权；根方案的克隆分发依赖属性文件进入 HEAD，未获授权时不要为了跑探针而自行提交，改为报告 `clone proof: pending`。完整提交门禁见 `commit-skill-work`。
6. 必须实跑两项审计并如实报告实际输出与退出码。根 `.gitattributes` 是否触发 `UNEXPECTED` / `FAIL` 取决于已安装脚本版本，不能预设，也不能把 FAIL 说成“只是警告”。
7. 不得用 `grep -c $'\r'` 证明没有 CRLF；Git Bash 会把 CR 剥成空模式，输出的是总行数。只用字节计数或 `git ls-files --eol`。
8. `.git/info/attributes` 永不提交；它是本地文件，不会随克隆或归档分发。

## 工作流

### Step 0 基线与稳定性

```bash
REPO="<repo>"
git -C "$REPO" rev-parse --show-toplevel
git -C "$REPO" rev-parse --absolute-git-dir
git -C "$REPO" status --short
git -C "$REPO" log -1 --oneline
git -C "$REPO" config --local --show-origin --get core.autocrlf
git -C "$REPO" config --global --show-origin --get core.autocrlf
git -C "$REPO" config --system --show-origin --get core.autocrlf
git -C "$REPO" ls-files --eol
git -C "$REPO" ls-files -s
sha256sum "$REPO/SKILL.md"
```

- `--get` 在值未设置时退出 1，这是正常结果，不是命令失败。
- 记录仓库根、git-dir、HEAD、`core.autocrlf` 三个作用域及来源、已跟踪文件清单、blob OID、文件大小与 SHA-256。
- 若工作区有与行尾无关的改动，停止并报告；不要用破坏性命令清理。
- `git ls-files --eol` 的 `w/lf` 只是当前快照，不证明下一次 checkout 仍是 LF。

### Step 1 选择属性文件位置

| 位置 | 是否随克隆分发 | `skill-file-qa` | `check_package_manifest.py` | 何时选择 |
|---|---|---|---|---|
| 根 `.gitattributes` | 是（提交后） | PASS + 1 WARN（unexpected file） | 实跑为准：允许清单含 `.gitattributes` 时 PASS / `Unexpected 0` / 退出 0；旧版或 HEAD 版报 `UNEXPECTED .gitattributes` / 退出 1 | 克隆、发布或归档后也必须保持 LF |
| `.git/info/attributes` | 否，仅当前副本 | PASS，0 warn | PASS，`Unexpected 0`（不依赖允许清单版本） | 需要两项审计全绿，且不要求克隆分发 |

决策规则：

- 按分发需求选择，不预设审计结果：仓库会被克隆、发布或归档，选根文件；只保护当前副本且要求 0 WARN，选 `.git/info/attributes`。
- 选定后必须实跑 Step 5 的两项审计并报告实际输出。根文件的 manifest 结果会随脚本版本变化（2026-10-26 本机工作区版为 PASS，HEAD `7a39419` 为 FAIL），不得照抄旧结论。
- 不要为了根 `.gitattributes` 去放宽 `check_package_manifest.py` 的白名单；那是修改另一个 Skill，需要独立授权。
- 根方案的分发效果以提交为前提：文件只在工作区、未进入 HEAD 时，克隆和归档都不含规则；未获提交授权时只能做本机验证。
- 两个文件同时存在时，`.git/info/attributes` 的优先级更高；不要保留互相冲突的规则，切换时删除另一个。

### Step 2 写入规则

内容固定为两行：

```gitattributes
# 仓库与工作区统一使用 LF，覆盖系统的 core.autocrlf=true。
* text=auto eol=lf
```

- 根方案写入 `<repo>/.gitattributes`；本地方案写入 `<repo>/.git/info/attributes`。
- 用 Write 工具写入，不要用 `echo`、`printf` 或 shell 重定向，避免 BOM、编码和多余空行。
- 规则行是必需的；注释可保留。`*` 覆盖所有路径，`text=auto` 让 Git 继续识别二进制，`eol=lf` 固定检出为 LF。
- 不要追加 `-text` 或按扩展名的例外规则，除非包内确有需要单独处理的二进制文件。

写入后立即核对属性文件本身。它尚未入库，Step 4 的 `git ls-files` 循环不会列出它：

```bash
ATTR="<repo>/.gitattributes"   # 本地方案：路径与标签都改为 .git/info/attributes
py -3 -c 'from pathlib import Path; import sys; d=Path(sys.argv[1]).read_bytes(); print(sys.argv[2], "bytes=%d CR=%d LF=%d BOM=%s" % (len(d), d.count(b"\r"), d.count(b"\n"), d.startswith(b"\xef\xbb\xbf"))); print(d.decode("utf-8").encode("unicode_escape").decode("ascii"))' "$ATTR" ".gitattributes"
```

- 期望 `bytes=95 CR=0 LF=2 BOM=False`；ASCII 转义内容应显示注释行和 `* text=auto eol=lf`。
- 输出必须保持 ASCII。Windows 控制台为 cp1252 时，`print(repr(d.decode("utf-8")))` 会因中文注释抛 `UnicodeEncodeError` 并以 1 退出；改用 `encode("unicode_escape").decode("ascii")`，或给进程设 `PYTHONIOENCODING=utf-8`。
- 文件缺失、`BOM=True`、`CR>0`、`LF` 不是 2，或内容不是两行时停止，修正后再继续；不要带着错误属性文件去 renormalize 或提交。

### Step 3 确认生效与 blob 不变性

```bash
git -C "$REPO" ls-files -z | xargs -0 -r git -C "$REPO" check-attr text eol --
git -C "$REPO" ls-files --eol
git -C "$REPO" ls-files -s
git -C "$REPO" add --renormalize -- <explicit tracked text paths>
git -C "$REPO" ls-files -s
```

- 期望 `text: auto`、`eol: lf`，以及 `i/lf w/lf attr/text=auto eol=lf`。
- `--renormalize` 只限定到包内文本路径；有无关文件时不要用 `.`。
- 前后比较 `git ls-files -s` 的 blob OID。OID 变化说明发生了内容归一化，不只是新增属性；停止并检查 diff，取得明确同意后再提交。
- 上面的 OID 比较只覆盖已跟踪文件；新增的根 `.gitattributes` 尚未入库，暂存后按 Step 6 单独核对索引 OID。
- 若工作区原本就是 CRLF，`--renormalize` 可能只改索引，不改工作区；确认工作区干净或已备份后，再对明确路径执行 `git checkout --`。绝不用它丢弃本地改动。
- 本地方案不应产生任何已跟踪改动；`git status` 只应显示预先存在的改动或空。

### Step 4 字节级验证（提交前）

先做只读字节检查：对每个已跟踪文件统计 CR/LF。二进制文件（`git check-attr` 显示 `-text`）不纳入 LF 判定。

```bash
git -C "$REPO" ls-files -z | while IFS= read -r -d '' rel; do
  py -3 -c 'from pathlib import Path; import sys; d=Path(sys.argv[1]).read_bytes(); print(sys.argv[2], "bytes=%d CR=%d LF=%d" % (len(d), d.count(b"\r"), d.count(b"\n")))' \
    "$REPO/$rel" "$rel"
done
```

再做真实检出探针：把索引写进系统临时目录，显式带上 `core.autocrlf=true`，然后逐个统计 CR。

```bash
TMP="<temp>/lf-probe"
rm -rf "$TMP"
mkdir -p "$TMP"
git -C "$REPO" -c core.autocrlf=true checkout-index -a --prefix="$TMP/"
git -C "$REPO" ls-files -z | while IFS= read -r -d '' rel; do
  py -3 -c 'from pathlib import Path; import sys; d=Path(sys.argv[1]).read_bytes(); print(sys.argv[2], "bytes=%d CR=%d LF=%d" % (len(d), d.count(b"\r"), d.count(b"\n")))' \
    "$TMP/$rel" "$rel"
done
chmod -R u+w "$TMP" && rm -rf "$TMP"
test -e "$TMP" && echo "STILL_EXISTS" || echo "REMOVED"
```

- 清理只用 `chmod -R u+w "$TMP"` 后的 `rm -rf`，并只作用于临时目录；不要对源仓库执行 `chmod`。
- 已验证：无属性且 `core.autocrlf=true` 时探针得到 `CR=2`；写入 `text=auto eol=lf` 后 `CR=0`。探针证明的是当前索引在本机的检出结果，不证明克隆行为。
- 根方案的克隆分发验证移到 Step 7：克隆只继承 HEAD 中的属性文件，文件未提交时克隆不带规则，因此这一步必须在提交之后执行。
- 本地方案不能用克隆证明 LF：克隆不带 `.git/info/attributes`，在 `core.autocrlf=true` 下可能得到 CRLF。这是预期限制，必须报告，不要偷偷补根文件。
- 本地方案用 `checkout-index` 证明当前仓库的检出仍是 LF；它证明的是本副本，不是克隆行为。
- `git ls-files` 与 `checkout-index` 只覆盖已跟踪文件；刚写入且未提交的 `.gitattributes`（或 `.git/info/attributes`）不在上面的循环里。必须先用 Step 2 的自检核对属性文件；提交后由 Step 7 的克隆探针把它计入。
- 任何时候都用字节计数，例如 `data.count(b"\r")`；不要用 `grep -c $'\r'`。

### Step 5 运行包审计

把 QA 日志保存在包外，例如临时目录：

```bash
TMPLOG="<temp>/qa.log"
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<skill-dir>" \
  --workspace "<workspace-root>" --stable-seconds 2 > "$TMPLOG" 2>&1
grep -E "^Files \(|^Summary:|^RESULT " "$TMPLOG"
py -3 "$HOME/.qoder/skills/skill-package-integrity-audit/scripts/check_package_manifest.py" \
  "<skill-dir>" --qa-log "$TMPLOG"
```

预期结果：

| 方案 | `skill-file-qa` | `check_package_manifest.py` |
|---|---|---|
| 根 `.gitattributes` | PASS；恰好 1 条 `layout` WARN；`Files (N+1)`；pass 数不固定 | 双分支：允许清单含 `.gitattributes` → PASS，`Unexpected 0`，退出 0；否则 `UNEXPECTED .gitattributes`，退出 1 |
| `.git/info/attributes` | PASS，0 warn；`Files (N)`；pass 数不固定 | PASS，Clean N，Unexpected 0，`QA Files (N): MATCH` |

- WARN 来自 `validate_skill.py` 的 `check_layout` 对根目录非 `SKILL.md` 文件的既有规则，不是属性文件内容错误。
- `pass` 数不是固定契约：校验器会给含 Python 围栏代码块的目标多记一条 `python blocks` 通过项。2026-10-26 本 Skill 实测 9 pass，`adopt-concurrent-duplicate-skill`（含 Python 代码块）实测 10 pass，均为 `RESULT PASS`。只断言 `RESULT PASS`、`0 fail`、恰好 1 条 `layout` WARN（根方案）与 `Files (N+1)`；不要照抄 pass 数。
- manifest 的 `Unexpected` 由脚本的允许清单决定：2026-10-26 本机工作区版含 `ALLOWED_FILES = {"SKILL.md", ".gitattributes"}`，HEAD `7a39419` 不含。运行前不要假设，直接看输出。
- manifest 实际 FAIL 时，不要静默删除根文件；要么经用户同意切换到本地方案，要么明确接受例外。
- 不要修改 `check_package_manifest.py` 或其他审计脚本来“修复”结果。

### Step 6 授权与独立提交

根方案的克隆分发依赖文件进入 HEAD，所以提交前先取得明确授权，例如询问：“根文件只有提交后才会随克隆分发；是否授权提交 `.gitattributes`？”

已授权：

```bash
git -C "$REPO" add -- .gitattributes
IDX=$(git -C "$REPO" rev-parse --verify :.gitattributes)
HASH=$(git -C "$REPO" hash-object --path=.gitattributes "$REPO/.gitattributes")
printf 'index=%s hash=%s\n' "$IDX" "$HASH"
test "$IDX" = "$HASH" && echo ATTR_OID_MATCH || echo ATTR_OID_MISMATCH
```

- 只有 `ATTR_OID_MATCH` 才能继续提交。`IDX` 为空、不是 40 位十六进制或与 `HASH` 不同，都按失败处理：先看 `git diff --cached -- .gitattributes` 与 Step 2 的字节核对，不要提交。
- 索引路径必须写 `:.gitattributes` 或 `:./.gitattributes`。`:/` 是提交消息检索语法，不是索引路径；本机实测 `git rev-parse --verify :/.gitattributes` 返回 `fatal: Needed a single revision`（退出 128），来源会话的检查把它显示成字面量 `:/.gitattributes`，造成假 MISMATCH。
- `hash-object` 带 `--path=.gitattributes`，让过滤规则按该路径查找；不要改用未指定路径的哈希来替代索引语义。
- 把 `add`、OID 核对与 `commit` 分成独立命令；来源会话在打印 MISMATCH 后仍创建了提交，不能重演。
- 通过后提交并复核：

```bash
git -C "$REPO" commit -m "chore(skill): forcer les fins de ligne LF"
git -C "$REPO" rev-parse --verify HEAD:.gitattributes
git -C "$REPO" status --short
git -C "$REPO" log -2 --oneline
```

- `HEAD:.gitattributes` 必须等于提交前的 `IDX`；不等或缺失时停止并报告。

未授权（包括用户只说“添加文件”）：不 `git add`、不 commit，也不为了跑 OID 核对而暂存文件；文件保持未跟踪，按 Step 5 完成审计，并在报告中写 `Commit: none (awaiting authorization)` 与 `clone proof: pending`。不要用临时克隆里自行提交来替代源仓库提交：那只能证明规则文本生效，不能证明源仓库会分发它。

从根方案切换到本地方案时，同样先取得提交授权。已授权：

```bash
git -C "$REPO" rm -- .gitattributes
git -C "$REPO" commit -m "chore(skill): deplacer les fins de ligne LF vers .git/info/attributes"
```

未授权时只删除文件（`rm -- .gitattributes`），保留未提交状态并如实报告。

- 本地方案本身没有可提交的规则文件；不要尝试 `git add .git/info/attributes`，它在 `.git` 内，不会被版本化。
- 一个提交只做一件事；不把行尾变更与其他修改混在一起；不推送。
- 提交后检查 `git status --short` 与 `git log -2`，确认只包含预期变更。

### Step 7 克隆分发验证（仅根方案，提交后）

前置：属性文件必须在 HEAD 中。未提交时跳过本步，报告 `clone proof: pending`。

```bash
git -C "$REPO" cat-file -e HEAD:.gitattributes
TMP="<temp>/clone"
rm -rf "$TMP"
git -c core.autocrlf=true clone "$REPO" "$TMP"
test -f "$TMP/.gitattributes" && echo "ATTR_PRESENT" || echo "MISSING_ATTR_IN_CLONE"
git -C "$TMP" ls-files --eol
git -C "$TMP" ls-files -z | while IFS= read -r -d '' rel; do
  py -3 -c 'from pathlib import Path; import sys; d=Path(sys.argv[1]).read_bytes(); print(sys.argv[2], "bytes=%d CR=%d LF=%d" % (len(d), d.count(b"\r"), d.count(b"\n")))' \
    "$TMP/$rel" "$rel"
done
sha256sum "$REPO/SKILL.md" "$TMP/SKILL.md"
chmod -R u+w "$TMP" && rm -rf "$TMP"
test -e "$TMP" && echo "STILL_EXISTS" || echo "REMOVED"
```

- 期望克隆内所有文件 `i/lf w/lf attr/text=auto eol=lf`，CR=0，大小和 SHA-256 与源一致。
- 克隆里没有 `.gitattributes` 或 attr 列为空，说明文件未提交，不是规则失效；停止并报告，不要改口说“已分发”。
- `git clone` 在 Windows 上把 `.git/objects` 写成只读，`shutil.rmtree` 会抛 `PermissionError [WinError 5]`。清理必须先 `chmod -R u+w "$TMP"` 再 `rm -rf`，并用 `test -e` 确认；只对临时目录 chmod。
- 本地方案不做本步；见 Step 4 的限制说明。

### Step 8 报告

```text
Repo        : <absolute path> | Branch: <branch> | HEAD: <hash>
Placement   : root .gitattributes | .git/info/attributes
autocrlf    : effective=<v> local=<v> global=<v> system=<v> (origins)
Files       : <N> tracked | attr=text=auto,eol=lf | index=lf | worktree=lf | CR=0
Blob OIDs   : tracked before=<...> after=<...> (unchanged | changed) | .gitattributes index=hash=<...> (MATCH | MISMATCH | pending)
Probe       : clone(post-commit) | checkout-index | CR=0 | cleanup=OK | pending (not committed)
Audit       : QA <PASS/FAIL> <p/f/w> Files (<N>) | manifest <PASS/FAIL> Unexpected <n> exit=<n>
Commits     : <hash> <subject> | none (awaiting authorization)
Distribution: yes (root) | no (info)
Push        : none
```

## 陷阱

| 现象 | 原因 | 处理 |
|---|---|---|
| `grep -c $'\r'` 输出 136、146、2 | Git Bash 把 CR 剥成空模式，统计的是总行数 | 用 `py -3` 字节计数或 `git ls-files --eol` 复核 |
| `git ls-files --eol` 显示 `w/lf`，但下次检出变 CRLF | `core.autocrlf=true` 在 checkout 时转换 | 用 `checkout-index` 探针或全新克隆验证实际检出 |
| 根 `.gitattributes` 的 manifest 结果与旧记录不一致 | 审计脚本版本不同：允许清单是否包含 `.gitattributes` | 实跑并报告实际输出；旧版报 `UNEXPECTED`/FAIL，含允许项的新版可 PASS；不要照抄历史结论，也不要改脚本 |
| 本地属性规则在克隆中消失 | `.git/info/attributes` 不随仓库分发 | 报告“仅本副本”；需要分发时改用根文件 |
| 根文件与 info 文件规则冲突 | 两个属性源同时存在 | 删除其中一个；info 优先级更高 |
| `git add --renormalize .` 改到无关文件 | 范围过大 | 只列包内文本路径，并比较 blob OID |
| 工作区仍有 CRLF | 只改了索引，未重新检出 | 确认干净或已备份后，对明确路径 `git checkout --` |
| 把全局 `core.autocrlf=false` 当作锁定 | 改的是用户环境，不是仓库策略，且影响其他仓库 | 不改全局；用仓库属性锁定 |
| `python` 命令失败或弹 Microsoft Store | Windows 别名 | 使用 `py -3` |
| 二进制文件被计入 CR 统计 | 图片、归档等文件本来就可能含 CR | 用 `git check-attr text` 的 `-text` 或 NUL 检测跳过，只判定文本文件 |
| `shutil.rmtree` 抛 `PermissionError: [WinError 5] ...\.git\objects\...` | `git clone` 在 Windows 生成只读对象文件 | 先 `chmod -R u+w "$TMP"` 再 `rm -rf "$TMP"`，`test -e` 确认；只作用于临时目录 |
| 克隆内没有 `.gitattributes`，或 attr 列为空 | 文件只在工作区，未进入 HEAD | 不判定规则失效；取得提交授权后提交，再重跑 Step 7；未授权则标 pending |
| 为了跑克隆探针而直接提交 | 把“添加文件”误当成提交授权 | 先询问；未授权保持未跟踪并报告 pending |
| `print(repr(d.decode('utf-8')))` 抛 `UnicodeEncodeError: 'charmap' codec can't encode characters in position 3-12`，退出 1 | Windows 控制台为 cp1252，无法输出中文注释 | 改用 `d.decode('utf-8').encode('unicode_escape').decode('ascii')` 只输出 ASCII；或设 `PYTHONIOENCODING=utf-8` |
| `git ls-files` 字节循环没有列出刚写入的 `.gitattributes` | `ls-files` 只枚举已跟踪文件，属性文件尚未 `git add` | 先用 Step 2 单独核对属性文件；提交后再用 `ls-files` 与克隆验证 |
| 暂存后用 `:/...` 取索引 OID，得到字面量或 `fatal: Needed a single revision`，与 `hash-object` 不符 | `:/<text>` 是提交消息检索语法，不是索引路径 | 改用 `:.gitattributes` 或 `:./.gitattributes`，并与 `git hash-object --path=.gitattributes` 对照；非 40 位十六进制即失败 |
| 照抄 `9 pass`，换了目标包后实际是 `10 pass` | `skill-file-qa` 会给含 Python 围栏代码块的目标多记一条 `python blocks` 通过项 | 只断言 `RESULT PASS`、0 fail、恰好 1 条 layout WARN 与 `Files (N+1)`；pass 数按实际输出记录 |

## 完成检查

- [ ] 已记录仓库根、git-dir、HEAD、工作区状态和 `core.autocrlf` 三个作用域来源。
- [ ] 已明确选择根 `.gitattributes` 或 `.git/info/attributes`，并向用户报告分发/审计取舍。
- [ ] 属性文件只有两行规则，UTF-8、无 BOM，规则为 `* text=auto eol=lf`。
- [ ] 属性文件自身已按字节核对（`CR=0`、`LF=2`、`BOM=False`，ASCII 转义内容正确），未依赖 `git ls-files` 覆盖未跟踪文件。
- [ ] 已用 `git check-attr` 与 `git ls-files --eol` 确认 `text=auto`、`eol=lf`、`i/lf w/lf`。
- [ ] `git add --renormalize` 限定到包内路径，前后 blob OID 未变，或变化已解释并获同意。
- [ ] 暂存后用 `:.gitattributes`（或 `:./.gitattributes`）取索引 OID，与 `git hash-object --path=.gitattributes` 一致；未使用 `:/` 形式，也未把字面量或空值当作 OID。
- [ ] 字节计数 CR=0；未使用 `grep -c $'\r'` 作为证据。
- [ ] 根方案在获得明确授权并提交后，才用全新克隆验证 CR=0；未授权时报告 `clone proof: pending`，未自行提交。
- [ ] 本地方案已用 `checkout-index` 验证，并说明不能证明克隆。
- [ ] 已运行 `skill-file-qa` 与 `check_package_manifest.py`，并按实际输出报告 WARN/FAIL、manifest 退出码与 QA pass 数；没有把 `9 pass` 写成固定预期。
- [ ] 已取得授权并独立提交，或明确说明未提交（`awaiting authorization`）/仅本地；未推送。
- [ ] 临时克隆和临时检出目录已删除；克隆目录先 `chmod -R u+w`，并用 `test -e` 确认不存在。

## 资源

- `references/preuves-session-lf.md`：来源会话与原执行会话的逐字命令、真实输出、提交与哈希、两种放置的审计差异、Windows 克隆清理失败与修复、`grep` 陷阱、自包含夹具、暂存后 `:/` 假 MISMATCH 与 QA pass 数差异、2026-10-26 manifest 白名单变化的后续观察与限制。
- 本版本不随附脚本；字节统计与 `checkout-index` 探针的内联命令见 Step 4。
- 依赖：`skill-file-qa` 提供 `C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py`；`skill-package-integrity-audit` 提供 `C:/Users/Administrateur/.qoder/skills/skill-package-integrity-audit/scripts/check_package_manifest.py`；提交门禁见 `commit-skill-work`。
- 该 manifest 脚本的 `.gitattributes` 允许项在 2026-10-26 本机为未提交改动（HEAD `7a39419` 不含）；审计前先看脚本状态与实际输出，不要把它当作稳定契约。
