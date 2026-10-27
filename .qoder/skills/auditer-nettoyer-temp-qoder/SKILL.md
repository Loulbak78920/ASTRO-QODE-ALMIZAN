---
name: auditer-nettoyer-temp-qoder
description: "盘点并安全清理 Qoder 临时目录：清点 `~/.qoder/tmp` 的目录、文件与嵌套 Git 克隆，按 `~/.qoder/projects` 下的会话 JSONL 引用判断归属并避开活跃会话，只删除经用户确认的显式路径，删除前 `chmod -R u+w`，删除后复查 Git Credential Manager 是否在原路径重建 `system-commandline-sentinel-files`、扫描脚本导入产生的 `__pycache__`，最后确认无残留且相关仓库干净。用于「清理临时目录」「删除临时克隆」「检查其他临时目录残留」「清理证据文件和日志」「.qoder/tmp 占用」「sentinel 重建」「pycache 残留」等请求；不适用于删除项目工作区、应用托管的 tool-results 缓存或其他会话仍在使用的克隆。"
---

# 盘点并安全清理 Qoder 临时目录

## 交付范围

本版本交付本文件、`references/cas-nettoyage-temp-qoder-2026-10-26.md` 与只读盘点脚本 `scripts/inventorier_tmp_qoder.py`（2026-10-26 用夹具与真实 `~/.qoder/tmp` 验证，见参考档案）。其余步骤使用 Git Bash 内联命令与 `py -3`；目录中出现未在本文件登记的文件，视为范围外，不是本 Skill 的已验证组成部分。

## 目标

在 Windows（Git Bash）与 Qoder 环境中，把 `~/.qoder/tmp` 的残留清点清楚、判定归属，经用户确认后只删除明确路径，并处理两类删除后的副作用：Git Credential Manager 的 .NET 组件在原路径重建 sentinel 目录（推断，未做进程级观测；见参考档案分级），以及导入脚本产生的 `__pycache__`。

## 适用与不适用

适用：

- 用户要求「删除临时克隆」「清理临时目录」「检查其他临时目录是否有残留」「清理证据文件和日志」。
- `.qoder/tmp` 占用偏大，或出现 Git 克隆、夹具、sentinel 目录。
- 会话结束前收尾，需要区分本会话产物、共享证据与其他会话的克隆。

不适用：

- 删除项目工作区文件或 Skill 安装目录；本 Skill 只删除确认过的临时路径与本次导入产生的缓存。
- 清理应用托管的缓存：`~/.qoder/tmp/<编码后的项目名>/`（tool-results）、`.last-skill-*` 指针、`%TEMP%/qoder-*-cwd`、`qoder-cli-error-*.json`。默认保留；只有用户明确点名时才纳入，并单独说明风险。
- 其他会话正在使用的克隆或缓存；共享证据默认保留。
- Git 分支与 refs 清理：使用 `nettoyer-branches-refs-git`。
- PR 流程内的仓库清理与 sentinel 处理：参见 `github-pr-create-merge-sans-gh`。

## 不可协商约束

1. 先只读清点，再生成待删清单，用户确认后才删除；不得边清点边删。
2. 删除只用显式路径循环；禁止 `rm -rf "$BASE"/*`、`find -delete` 或任何未确认的通配符删除。
3. 删除变量必须非空且目标存在；不要用 `TMP="$(cat path.txt)"` 后直接 `rm -rf "$TMP"`。来源会话的早期写法在删除克隆的同一命令里删掉了路径文件，事后无法复核；后续改用字面路径并先做存在性判断。
4. 删除目录前执行 `chmod -R u+w`，删除后逐项用 `[ -e ]` 复查并输出 `GONE` 或 `STILL`。
5. 默认保留：`~/.qoder/tmp/<编码项目名>/`、`.last-skill-*`、`%TEMP%/qoder-*`、其他会话的克隆/缓存、无归属证据的条目。
6. 共享证据（除当前会话外仍被任何会话 JSONL 引用）只在用户明确点名该范围后才删除。引用数只证明「被提到」，不证明可删，也不证明会话已结束；当前会话自己的 JSONL 也会记录候选名，统计时必须排除。
7. 不修改全局或系统 Git 配置，不对任何仓库执行 `stash`、`reset`、`checkout`。删除临时克隆时不要触碰源仓库的 refs；PR 流程的 `refs/qoder-tmp/*` 由对应 Skill 处理。
8. 删除后必须复查 sentinel 与 `__pycache__`；未复查不得宣称「无残留」。
9. 报告区分「已删除并复查」「已确认保留」「未知/未触碰」；不要把「路径已消失」说成「所有会话不再引用」。

## 工作流

### Step 0 基线与范围

```bash
BASE="$HOME/.qoder/tmp"
date -u +%Y-%m-%dT%H:%M:%SZ
[ -d "$BASE" ] && du -sh "$BASE" || echo "BASE_MISSING"
git --version
py -3 --version
echo "PROJECT_JSONL_ROOT=$HOME/.qoder/projects"
```

记录用户请求的范围（只清本会话，还是全部）、是否允许删除共享证据、是否有其他会话正在运行。未给范围时按「仅本会话产物」处理，并明确报告这一默认。

### Step 1 只读清点

先运行只读盘点脚本，得到可复现的顶层清单、嵌套 `.git`、sentinel 与缓存计数：

```bash
SKILL_DIR="$HOME/.qoder/skills/auditer-nettoyer-temp-qoder"
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$HOME/.qoder/tmp" --max-depth 5 --recent-minutes 60
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$HOME/.qoder/tmp" --max-depth 5 --json > "$HOME/AppData/Local/Temp/tmp-qoder-inventory.json"
```

- 退出码 `0` 表示 `RESULT OK` 或 `RESULT PARTIAL`；`2` 表示 `RESULT FAIL`（根目录不存在、不是目录、不可读，或参数错误）。
- 输出含 `TOTALS`、`MARKERS`、每个顶层条目的 size/mtime/age/recent/empty 与标记计数，以及 `NESTED_GIT`、`SENTINEL_DIRS`、`PYCACHE` 明细；`--json` 输出 ASCII JSON，便于落盘比对。
- `--max-depth` 只限制标记扫描深度，size 始终递归统计。`.git` 可能是目录（普通克隆）也可能是文件（worktree/子模块），脚本都记入 `nested_git`；不要把 `find -type d -name .git` 的 0 当作没有嵌套仓库。
- 脚本只读，不判定归属、不删除；`UNKNOWN`、共享证据与活跃会话仍按 Step 2、Step 3 处理。目录可能在扫描期间变化，计数只对本次运行有效。
- 文本模式在 cp1252 控制台下把无法编码的文件名输出为 `\uXXXX` 转义，JSON 模式始终为 ASCII；需要可读原名时用 `ls` 复核。

列出顶层条目、大小、修改时间与标记。不要凭名字推断内容。

```bash
BASE="$HOME/.qoder/tmp"
for p in "$BASE"/*; do
  [ -e "$p" ] || continue
  t=FILE; [ -d "$p" ] && t=DIR
  s=$(du -sh "$p" 2>/dev/null | cut -f1)
  m=$(stat -c '%y' "$p" 2>/dev/null | cut -d. -f1)
  tag=""
  [ -d "$p/.git" ] && tag="$tag GIT_CLONE"
  [ -d "$p" ] && [ -z "$(ls -A "$p" 2>/dev/null)" ] && tag="$tag EMPTY"
  printf '%-6s %-55s %-8s %s%s\n' "$t" "$(basename "$p")" "$s" "$m" "$tag"
done
```

枚举嵌套仓库（夹具常在子目录里带 `.git`）：

```bash
find "$BASE" -maxdepth 5 -type d -name .git 2>/dev/null | sed "s|$BASE/||"
```

单独枚举 sentinel 与缓存：

```bash
find "$BASE" -maxdepth 4 -type d -name system-commandline-sentinel-files 2>/dev/null
find "$HOME/.qoder/skills" -type d -name __pycache__ 2>/dev/null | head -20
```

对候选逐项记录：类型、size、mtime（带时区）、是否含 `.git`、是否为空、是否有嵌套 `.git`。

### Step 2 归属判定

会话 JSONL 位于 `~/.qoder/projects/<编码后的项目名>/<sessionId>.jsonl`。用条目的 **basename** 做固定字符串检索，覆盖所有项目：

```bash
cd "$HOME/.qoder/projects" || exit 1
for name in "candidate-dir" "candidate-file.log"; do
  echo "--- $name ---"
  hits=$(grep -F -l -- "$name" */*.jsonl 2>/dev/null)
  echo "$hits" | sed '/^$/d'
  echo "COUNT=$(echo "$hits" | sed '/^$/d' | wc -l)"
done
```

判定规则：

- 只用 basename，因为 JSONL 里的绝对路径可能使用正斜杠、反斜杠或不同大小写。
- 不要用 `| head` 截断检索结果：引用数只对采样时刻有效，但截断会让计数永久偏小；需要限制显示时，先保存完整命中清单再另做截断。
- 检索结果只说明「被引用」。需要判断会话是否活跃时，用内置 MCP 工具 `list_chat_sessions` 查 `runtimeState` 与更新时间；`runtimeState` 不是写入日志，不能证明空闲，也不能证明某个回合已结束。
- 对疑似克隆，用 `git -C <path>/repo status -sb` 看分支与上游，用 `ls -la` 看 mtime。干净、跟踪 `origin/main` 且最近更新的克隆按「其他会话正在使用」处理。
- 先排除当前会话自己的 JSONL：你检索时，当前会话的记录也会写入候选名，不排除会把每个候选都算成 SHARED。用唯一探针识别自身文件：先在一次工具调用中输出 `SELF_PROBE="selfref-$(date +%s)-$$"`，再在下一次调用中执行 `grep -F -l -- "$SELF_PROBE" */*.jsonl`；命中的文件就是当前会话的 JSONL，从引用计数中排除。
- 判定顺序固定为 `APP-MANAGED` → `OTHER-SESSION` → `SHARED` → `CURRENT` → `UNKNOWN`。应用托管目录即使只被当前会话引用，也不进入待删清单。

| 分类 | 判据 | 默认动作 |
|---|---|---|
| APP-MANAGED | `tmp/<编码项目名>/`、`.last-skill-*`、`%TEMP%/qoder-*` | 不触碰，除非用户明确要求 |
| OTHER-SESSION | 引用会话不含当前会话，或克隆最近更新并跟踪上游 | 不触碰 |
| SHARED | 至少一个其他会话引用（不计当前会话；删除之后才开始的 Skill 创建/审计会话只转述该名称，属于二阶提及，不计入） | 保留；用户点名后才删 |
| CURRENT | 排除当前会话 JSONL 后，无其他会话引用，且非 APP-MANAGED | 列入待删清单 |
| UNKNOWN | 无引用、无清晰大小/时间线索 | 保留并报告，不猜 |

### Step 3 生成确认清单

输出表格：路径、类型/size、引用会话数、分类、建议动作。请用户确认**精确清单**，不要把「顺便清掉其他残留」打包进同一句。共享证据与 UNKNOWN 项必须单独列出并单独确认。

若用户只说「清理全部」，仍然先列出清单并等待确认；把会删除的每一项显式写出。

### Step 4 删除确认项

目录与文件分开循环，使用字面路径与 `--`：

```bash
BASE="$HOME/.qoder/tmp"
for n in "confirmed-dir-a" "confirmed-dir-b"; do
  P="$BASE/$n"
  if [ -z "$n" ] || [ ! -e "$P" ]; then echo "SKIP $n"; continue; fi
  chmod -R u+w "$P" 2>/dev/null
  rm -rf -- "$P"
  if [ -e "$P" ]; then echo "STILL $n"; else echo "GONE $n"; fi
done

for n in "confirmed-file-a.log" "confirmed-file-b.txt"; do
  P="$BASE/$n"
  if [ -z "$n" ] || [ ! -e "$P" ]; then echo "SKIP $n"; continue; fi
  rm -f -- "$P"
  if [ -e "$P" ]; then echo "STILL $n"; else echo "GONE $n"; fi
done
```

不要在同一步里删除用于定位的 path 文件，直到所有删除与复查完成。

### Step 5 删除后复查

1. sentinel 复查：

```bash
BASE="$HOME/.qoder/tmp"
find "$BASE" -maxdepth 4 -type d -name system-commandline-sentinel-files 2>/dev/null
```

如果 sentinel 在已删克隆的原路径重新出现，只删除该目录：

```bash
DELETED_DIR="REPLACE_WITH_DELETED_DIR_NAME"
S="$BASE/$DELETED_DIR/system-commandline-sentinel-files"
find "$S" -maxdepth 1 2>/dev/null
du -sh "$S" 2>/dev/null
chmod -R u+w "$S" 2>/dev/null
rm -rf -- "$S"
[ -e "$S" ] && echo "STILL_SENTINEL" || echo "SENTINEL_GONE"
```

只删 sentinel 目录本身，不动父目录、配置或其他克隆。把 `DELETED_DIR` 换成实际已删目录名，不要照抄占位符。完成其他复查后再扫一次，因为重建可能发生在首次扫描之后。

2. 命名残留复查：

```bash
PREFIX="lock-lf"
if [ -n "$PREFIX" ]; then
  ls -d "$BASE/$PREFIX"* 2>/dev/null || echo "NO_${PREFIX}_LEFTOVER"
else
  echo "PREFIX_EMPTY"
fi
```

3. 导入产生的缓存：

```bash
SKILL_DIR="$HOME/.qoder/skills/REPLACE_WITH_SKILL_DIR_NAME"
find "$SKILL_DIR" \( -type d -name __pycache__ -o -type f -name '*.pyc' \) 2>/dev/null
git -C "$SKILL_DIR" status --porcelain
```

把 `SKILL_DIR` 换成实际 Skill 目录。只删除本次导入生成的缓存，然后复核 `git status --porcelain` 为空。后续导入可用 `py -3 -B` 或 `PYTHONDONTWRITEBYTECODE=1` 预防；来源会话未验证这两个参数，只验证了删除结果。

4. 源仓库未受影响：

```bash
git -C "$SKILL_DIR" status -sb
git -C "$SKILL_DIR" log -1 --oneline
```

5. 最终清点：重新运行 Step 1 的顶层清单，对照删除前的快照，确认只有确认项消失。

### Step 6 报告

用表格汇总：

| 项 | 类型/size | JSONL 引用 | 分类 | 动作 | 复查结果 |
|---|---|---|---|---|---|

报告必须写明：

- 已删除并复查消失的精确路径。
- GCM sentinel 是否在原路径重建、如何二次删除、最后一次扫描时刻。
- 已确认保留的条目及理由（其他会话、应用托管、共享证据、UNKNOWN）。
- 未验证项（例如未检查各会话的实时写入状态、未主动复现 GCM 重建）。

## 陷阱与处理

| 现象 | 原因 | 处理 |
|---|---|---|
| 删除克隆后同一路径又出现 `system-commandline-sentinel-files` | Git Credential Manager 的 .NET 组件在调用后重建（推断；未做进程级观测） | 只删除该目录并再次扫描；「已删过一次」不能作为跳过复查的理由 |
| 删除后出现 `?? scripts/__pycache__/` | `py -3` 导入 Skill 脚本时写入字节码 | 只删除该缓存，复核仓库干净；后续用 `py -3 -B` |
| `rm -rf "$TMP"` 后找不到路径文件 | 路径来自文件，且在同一条命令中被删除 | 使用字面路径；先断言非空且存在；保留定位文件到复查结束 |
| `du -sh` 或 `stat -c` 报错 | 在 Windows 原生 cmd 或 PowerShell 中执行 | 用 Git Bash；不要用 PowerShell 解析输出 |
| JSONL 检索漏掉其他项目 | 只在当前项目目录执行 `grep` | 在 `~/.qoder/projects` 下检索 `*/*.jsonl` |
| 引用数为 1 但条目仍被使用 | 引用数不等于会话状态，也可能只被间接提到 | 查 `list_chat_sessions`；仍不确定就保留并报告 |
| 每个候选都被算成 SHARED | 当前会话自己的 JSONL 也记录了候选名 | 用唯一探针找出自身 JSONL，并从引用计数排除 |
| 引用会话数持续增长（本案 `live-audit-lock-lf` 从 5 涨到 14） | 16:33:46Z 删除后新建的 9 个 Skill 创建/审计会话在文档里转述该名称，属于二阶提及 | 先看每个命中会话的首条记录时间：删除之后才开始的会话单列为二阶提及，不计入 SHARED；报告写明计数时刻 |
| `%TEMP%` 中有大量 `qoder-*-cwd` | Qoder 内部工作目录标记 | 应用托管，默认保留 |
| `tmp/<编码项目名>` 达数十 MB | tool-results 会话缓存，由应用管理 | 不按「临时垃圾」删除 |
| 嵌套克隆位于 `fixture/repo/.git` | 夹具目录结构 | 用 `maxdepth 5` 枚举，按整个夹具目录判断归属 |
| `find -type d -name .git` 少于脚本的 `nested_git` | worktree 或子模块的 `.git` 是文件 | 同时用 `-type f -name .git`，或直接采信脚本的 `nested_git`；目录计数为 0 不等于没有嵌套仓库 |
| 删除共享证据后其他会话证据链断裂 | 多个会话引用同一文件 | 默认保留；用户点名后才删，并在报告中注明 |
| 删除后仍能 `ls` 到同名路径 | 只删了子目录或被重建 | 检查父目录、sentinel 与 mtime，不要只看一次 `rm` 退出码 |

## 已验证案例（2026-10-26）

来源会话 `324c8787-9642-4d4e-a16c-2cf4834fb20c`，完整引文与指纹见 `references/cas-nettoyage-temp-qoder-2026-10-26.md`。

1. 16:16:00Z 删除克隆 `pr-lock-lf.4v1Pgv`，输出 `TMP_REMOVED`；到 16:20:10Z 同一路径出现 4.0K 的 `system-commandline-sentinel-files`，内含 `dotnet-suggest-registration-git-credential-manager, Version=2.6.1.0...`。
2. 16:20:24Z 第二次删除该目录，输出 `RM_EXIT=0` 与 `REMOVED`；随即扫描未发现其他 sentinel。
3. 16:24:57Z 按 basename 检索 JSONL：`live-audit-lock-lf` 被 5 个会话引用；16:44Z 的补充复核显示 `publish-hsas.C2cx6c` 被 5 个会话提到，且是干净克隆并跟踪 `origin/main`，未触碰。
4. 16:24:37Z 在 `github-pr-create-merge-sans-gh` 的 scripts 目录发现 `__pycache__`，`git status` 显示 `?? scripts/__pycache__/`；16:25:13Z 删除后状态恢复为空。
5. 16:33:46Z 删除 7 个经用户确认的 lock-lf 证据与日志，全部输出 `GONE`，`*lock-lf*` 残留为 `NONE`，源仓库仍为 `## main`。
6. 16:42:29Z 又删除一个后出现的克隆 `pr-lock-lf-update.1793032871`，输出 `REMOVED` 与 `NO_PR_OR_SENTINEL_RESIDUE`。
7. 边界：归属检索覆盖了 7 个待删项中的 6 个，`qa-lf-20261026.log` 未纳入那次 `grep`；删除时未逐个核验引用会话的实时写入状态；GCM 重建未被主动复现。
8. 16:56Z 只读盘点脚本在真实 `~/.qoder/tmp` 上返回 `RESULT OK`：102 个顶层条目、1869 个条目、54.3M、16 个 `nested_git`（14 个目录 + 2 个文件）；sentinel、`__pycache__` 与 `.pyc` 均为 0，与 `find` 交叉计数一致。同一脚本在夹具上覆盖空目录、`.git` 文件、sentinel、`.pyc` 与非 ASCII 文件名，并以退出码 2 覆盖根目录缺失、文件当根目录与非法参数。

## 验收片段

以下片段只读，不执行删除：

```bash
BASE="$HOME/.qoder/tmp"
[ -d "$BASE" ] && echo "BASE_OK" || echo "BASE_MISSING"
echo "SENTINELS=$(find "$BASE" -maxdepth 4 -type d -name system-commandline-sentinel-files 2>/dev/null | wc -l)"
echo "NESTED_GIT=$(find "$BASE" -maxdepth 5 -type d -name .git 2>/dev/null | wc -l)"
py -3 -B "$HOME/.qoder/skills/auditer-nettoyer-temp-qoder/scripts/inventorier_tmp_qoder.py" --root "$BASE" --max-depth 5 --recent-minutes 60 | sed -n '1,10p'
```

预期 `BASE_OK`；`SENTINELS` 可能非零（其他克隆也可能有），必须解释而不是直接删除；`NESTED_GIT` 只数 `.git` 目录，脚本的 `MARKERS nested_git` 同时包含 `.git` 文件，两者口径不同；这些值随夹具创建与清理变化，只作清点基线，不是待删数量。脚本应打印 `RESULT OK` 或 `RESULT PARTIAL` 并以退出码 0 结束；出现 `PARTIAL` 时先读 `ERRORS`。

## 资源

- `references/cas-nettoyage-temp-qoder-2026-10-26.md`：来源会话时间线、逐字输出、指纹与分级，以及脚本增量的夹具与真实运行记录。
- `scripts/inventorier_tmp_qoder.py`：只读盘点脚本（`--root`、`--max-depth`、`--recent-minutes`、`--entry-limit`、`--json`；退出码 0/2），输出顶层 size/mtime/recent、嵌套 `.git`（目录与文件）、sentinel 与 `__pycache__`/`.pyc` 计数。
- `skill-package-integrity-audit`：只读审计 Skill 包内缓存与归档。
- `audit-session-evidence`：会话证据链与来源核实方法。
- `extraire-preuves-session-qoder`：从项目 JSONL 提取可复核证据。
- `github-pr-create-merge-sans-gh`：PR 流程、`refs/qoder-tmp/*` 与 sentinel 陷阱。
- `nettoyer-branches-refs-git`：分支与 refs 清理。
- `skill-file-qa`：写入后的静态验收与指纹。
