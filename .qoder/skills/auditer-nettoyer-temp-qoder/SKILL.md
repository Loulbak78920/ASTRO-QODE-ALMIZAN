---
name: auditer-nettoyer-temp-qoder
description: "盘点并安全清理 Qoder 临时目录：清点 `~/.qoder/tmp` 与项目 `<workspace>/.qoder/tmp` 的目录、文件与嵌套 Git 克隆，按 `~/.qoder/projects` 下的会话 JSONL 单遍扫描并排除当前会话，用右边界匹配与引用新鲜度（条目 ≥6h 且最后提及 ≥3h，mtime 仅作回退）筛出候选，只删除经用户确认的显式路径，删除前 `chmod -R u+w` 与 `stat -c %Y` 复查，删除后检查 sentinel、`__pycache__` 与嵌套仓库；不可复现快照先复制到 `.qoder/snapshots` 并校验 SHA-256。用于「清理临时目录」「删除临时克隆」「检查其他临时目录残留」「清理证据文件和日志」「清理项目 .qoder/tmp」「快照备份」「大规模归属检索」「sentinel 重建」「pycache 残留」等请求；不适用于删除项目源码、Skill 安装目录、应用托管的 tool-results 缓存或其他会话仍在使用的克隆。"
---

# 盘点并安全清理 Qoder 临时目录

## 交付范围

本版本交付本文件、`references/cas-nettoyage-temp-qoder-2026-10-26.md`、`references/cas-nettoyage-temp-qoder-2026-10-27.md` 与只读盘点脚本 `scripts/inventorier_tmp_qoder.py`（2026-10-26 用夹具与真实 `~/.qoder/tmp` 验证；2026-10-27 在用户级与项目级 `.qoder/tmp` 上复跑，见两份参考档案）。归属扫描、候选筛选与删除脚本使用 Git Bash 内联命令与 `py -3 -B`；目录中出现未在本文件登记的文件，视为范围外，不是本 Skill 的已验证组成部分。

## 目标

在 Windows（Git Bash）与 Qoder 环境中，把 `~/.qoder/tmp` 与项目 `<workspace>/.qoder/tmp` 的残留清点清楚、判定归属与引用新鲜度，经用户确认后只删除明确路径；不可复现的项目快照先备份到 `.qoder/snapshots` 并校验哈希。删除后处理两类副作用：Git Credential Manager 的 .NET 组件在原路径重建 sentinel 目录（推断，未做进程级观测；见参考档案分级），以及导入脚本产生的 `__pycache__`。

## 适用与不适用

适用：

- 用户要求「删除临时克隆」「清理临时目录」「检查其他临时目录是否有残留」「清理证据文件和日志」。
- 用户级 `~/.qoder/tmp` 或项目 `<workspace>/.qoder/tmp` 占用偏大，或出现 Git 克隆、夹具、sentinel 目录。
- 项目 `.qoder/tmp` 中的快照需要归档到 `<workspace>/.qoder/snapshots`，再清理 tmp 副本。
- 候选量大（数百个顶层条目、数亿字节 JSONL），需要单遍归属扫描与引用新鲜度筛除。
- 会话结束前收尾，需要区分本会话产物、共享证据与其他会话的克隆。

不适用：

- 删除项目源码、`.qoder` 配置或 `.qoder/skills` 安装目录；项目侧只允许 `.qoder/tmp` 与 `.qoder/snapshots` 的临时/快照路径。
- 把 `.qoder/snapshots` 中保留的快照当作临时垃圾；只有用户明确点名该快照时才纳入。
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
10. 大规模归属必须用单遍读取 JSONL 的扫描；禁止对每个候选名单独 `grep` 全量 JSONL。名称匹配至少加右边界 `(?![A-Za-z0-9._-])`，否则前缀相同的长名会被短名吞掉、引用数虚高。右边界不约束左侧，短名仍可能在更长 token 的尾部命中；候选名应保持可区分，并在报告中注明这一限制。
11. 引用新鲜度以「最后提及」为准：按行时间戳取每个候选的最后提及，缺可用 `timestamp` 时回退该会话 JSONL 的 mtime 并标 `last_mention_src=mtime`。最后提及仍不等于会话已结束或条目已无人使用；不得据此宣称「其他会话不再引用」。会话未注册（`wait_chat_sessions` 报不存在）时只说明会话状态 UNKNOWN，条目仍按最后提及 age 归入 ACTIVE-REF 或 STALE-REF，不要当成 cold。
12. 删除脚本禁止使用顶层 `continue`。`bash -n` 对顶层 `continue` 返回 0，但运行时会报 `continue: only meaningful in a 'for', 'while', or 'until' loop` 且不会跳过后续删除命令；必须改写成逐项 `if/else`，并在执行前检查生成结构或在小夹具上验证 `SKIP` 分支。`bash -n` 只证明语法，不证明控制流。
13. 项目快照不可复现时，先复制到 `<workspace>/.qoder/snapshots` 并用 SHA-256 证明副本一致、JSON 可解析，才可删除 `.qoder/tmp` 中的副本；`.qoder/snapshots` 默认不删。
14. 候选清单是生成时刻的快照；用户确认与执行间隔较长时，重新运行归属扫描或把 `last_mention_age_h` 接近阈值的条目改判为 ACTIVE-REF。删除脚本的 `stat -c %Y` 只复查条目本身，不复查引用会话。

## 工作流

### Step 0 基线与范围

```bash
USER_TMP="$HOME/.qoder/tmp"
WORKSPACE="REPLACE_WITH_WORKSPACE_ROOT"
PROJECT_TMP="$WORKSPACE/.qoder/tmp"
SNAPSHOTS="$WORKSPACE/.qoder/snapshots"
date -u +%Y-%m-%dT%H:%M:%SZ
[ -d "$USER_TMP" ] && du -sh "$USER_TMP" || echo "USER_TMP_MISSING"
[ -d "$PROJECT_TMP" ] && du -sh "$PROJECT_TMP" || echo "PROJECT_TMP_MISSING"
[ -d "$SNAPSHOTS" ] && du -sh "$SNAPSHOTS" || echo "SNAPSHOTS_MISSING"
git --version
py -3 --version
echo "PROJECT_JSONL_ROOT=$HOME/.qoder/projects"
```

记录用户请求的范围（只清本会话，还是全部）、是否允许删除共享证据、是否有其他会话正在运行。未给范围时按「仅本会话产物」处理，并明确报告这一默认。`WORKSPACE` 必须显式写成项目根，不要从子目录推断；项目侧只处理 `.qoder/tmp` 与 `.qoder/snapshots`，不触碰源码。

### Step 1 只读清点

先运行只读盘点脚本，得到可复现的顶层清单、嵌套 `.git`、sentinel 与缓存计数：

```bash
SKILL_DIR="$HOME/.qoder/skills/auditer-nettoyer-temp-qoder"
USER_TMP="$HOME/.qoder/tmp"
PROJECT_TMP="REPLACE_WITH_WORKSPACE_ROOT/.qoder/tmp"
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$USER_TMP" --max-depth 5 --recent-minutes 60 --entry-limit 5000
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$USER_TMP" --max-depth 5 --json --entry-limit 5000 > "$HOME/AppData/Local/Temp/tmp-qoder-inventory-user.json"
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$PROJECT_TMP" --max-depth 5 --recent-minutes 60 --entry-limit 5000
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$PROJECT_TMP" --max-depth 5 --json --entry-limit 5000 > "$HOME/AppData/Local/Temp/tmp-qoder-inventory-project.json"
```

- 退出码 `0` 表示 `RESULT OK` 或 `RESULT PARTIAL`；`2` 表示 `RESULT FAIL`（根目录不存在、不是目录、不可读，或参数错误）。
- `RESULT PARTIAL` 且 `truncated=yes` 时，`TOTALS` 只覆盖已扫描的条目，体积可能被严重低估（2026-10-27 首跑用 `--entry-limit 200` 得到 3.2M，完整值是 84.8M）。提高 `--entry-limit` 重跑后再用这些数字做基线，不要拿截断结果当完整清单。
- 项目 `.qoder/tmp` 通常很小，但同样要枚举；其中的 `<编码项目名>/` 是应用缓存，默认保留。两个根都要分别记录顶层条目、size、mtime 与标记。
- 输出含 `TOTALS`、`MARKERS`、每个顶层条目的 size/mtime/age/recent/empty 与标记计数，以及 `NESTED_GIT`、`SENTINEL_DIRS`、`PYCACHE` 明细；`--json` 输出 ASCII JSON，便于落盘比对。`--max-depth` 只限制标记扫描深度（size 始终递归统计），`.git` 目录或文件都记入 `nested_git`。
- 脚本只读，不判定归属、不删除；`UNKNOWN`、共享证据与活跃会话仍按 Step 2、Step 3 处理。目录可能在扫描期间变化，计数只对本次运行有效。
- 文本模式在 cp1252 控制台下把无法编码的文件名输出为 `\uXXXX` 转义，JSON 模式始终为 ASCII；需要可读原名时用 `ls` 复核。

列出顶层条目、大小、修改时间与标记。不要凭名字推断内容；脚本已输出这些字段，下列片段用于人工复核：

```bash
BASE="$HOME/.qoder/tmp"
for p in "$BASE"/*; do
  [ -e "$p" ] || continue
  printf '%-5s %-55s %-8s %s\n' "$([ -d "$p" ] && echo DIR || echo FILE)" "$(basename "$p")" "$(du -sh "$p" 2>/dev/null | cut -f1)" "$(stat -c '%y' "$p" 2>/dev/null | cut -d. -f1)"
done
find "$BASE" -maxdepth 5 \( -type d -name .git -o -type f -name .git \) 2>/dev/null | sed "s|$BASE/||"
find "$BASE" -maxdepth 4 -type d -name system-commandline-sentinel-files 2>/dev/null
find "$HOME/.qoder/skills" -type d -name __pycache__ 2>/dev/null | head -20
```

对候选逐项记录：类型、size、mtime（带时区）、是否含 `.git`、是否为空、是否有嵌套 `.git`。夹具常在子目录里带 `.git`，要同时枚举目录与文件两种形态。

### Step 2 归属与新鲜度判定

会话 JSONL 位于 `~/.qoder/projects/<编码后的项目名>/<sessionId>.jsonl`。候选来自两个根的顶层条目。先用唯一探针找出当前会话自己的 JSONL（不先排除会把每个候选都算成 SHARED）：

```bash
cd "$HOME/.qoder/projects" || exit 1
SELF_PROBE="selfref-$(date +%s)-$$"
echo "SELF_PROBE=$SELF_PROBE"
# 下一次工具调用再执行：
grep -F -l -- "$SELF_PROBE" */*.jsonl 2>/dev/null
```

命中的文件就是当前会话；把它的 sessionId 传给下文的 `SELF`。

不要对每个候选名单独 `grep` 全量 JSONL：候选可达数百个、JSONL 可达数亿字节。用一次只读 Python 扫描，每个文件只读取一次，并对每个候选名做右边界匹配：

```bash
py -3 -B - <<'PY'
import datetime, glob, io, json, os, re, sys

USER_TMP = os.path.join(os.environ["USERPROFILE"], ".qoder", "tmp")
PROJECT_TMP = r"REPLACE_WITH_WORKSPACE_ROOT/.qoder/tmp"
PROJECTS = os.path.join(os.environ["USERPROFILE"], ".qoder", "projects")
SELF = "REPLACE_WITH_SELF_SESSION_ID"

if "REPLACE_WITH_WORKSPACE_ROOT" in PROJECT_TMP:
    print("PROJECT_TMP_NOT_SET", file=sys.stderr)
    sys.exit(2)
if not SELF or SELF.startswith("REPLACE_"):
    print("SELF_SESSION_NOT_SET", file=sys.stderr)
    sys.exit(2)

def top(root):
    return [(root, n) for n in sorted(os.listdir(root))]

cands = []
for label, root in (("user", USER_TMP), ("project", PROJECT_TMP)):
    if os.path.isdir(root):
        cands.extend((label, root, n) for n in sorted(os.listdir(root)))
names = sorted({n for _, _, n in cands}, key=len, reverse=True)
pats = {n: re.compile(re.escape(n) + r"(?![A-Za-z0-9._\-])") for n in names}

now = datetime.datetime.now().astimezone()
act = {}
hits = {n: set() for n in names}
last = {}
scanned = 0
for path in glob.glob(os.path.join(PROJECTS, "*", "*.jsonl")):
    sid = os.path.basename(path)[:-6]
    act[sid] = datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone()
    if sid == SELF:
        continue
    scanned += 1
    try:
        with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                hit = [n for n, pat in pats.items() if pat.search(line)]
                if not hit:
                    continue
                when, src = act[sid], "mtime"
                try:
                    raw = json.loads(line)["timestamp"]
                    when = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone() if isinstance(raw, str) else datetime.datetime.fromtimestamp(raw / 1000).astimezone()
                    src = "ts"
                except (ValueError, KeyError, AttributeError, TypeError, OSError):
                    pass
                for n in hit:
                    hits[n].add(sid)
                    if n not in last or when > last[n][0]:
                        last[n] = (when, sid, src)
    except OSError as e:
        print("READ_ERR", sid, e, file=sys.stderr)

def dsize(p):
    try:
        if os.path.isdir(p):
            total = 0
            for dp, _, fn in os.walk(p):
                for f in fn:
                    try:
                        total += os.path.getsize(os.path.join(dp, f))
                    except OSError:
                        pass
            return total
        return os.path.getsize(p)
    except OSError:
        return -1

out = []
for label, root, n in cands:
    p = os.path.join(root, n)
    try:
        st = os.stat(p)
    except OSError as e:
        print("STAT_ERR", label, n, e, file=sys.stderr)
        continue
    refs = sorted(hits[n])
    lastm = last.get(n)
    out.append({
        "root": label,
        "name": n,
        "is_dir": os.path.isdir(p),
        "size": dsize(p),
        "mtime": datetime.datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(),
        "age_h": round((now - datetime.datetime.fromtimestamp(st.st_mtime).astimezone()).total_seconds() / 3600, 2),
        "ref_count": len(refs),
        "refs": refs,
        "last_mention_age_h": round((now - lastm[0]).total_seconds() / 3600, 2) if lastm else None,
        "last_mention_sid": lastm[1] if lastm else None,
        "last_mention_src": lastm[2] if lastm else None,
    })

out_path = os.path.join(os.environ.get("TEMP") or os.environ.get("TMP") or ".", "tmp-qoder-attribution.json")
with io.open(out_path, "w", encoding="ascii") as fh:
    json.dump({"now": now.isoformat(), "scanned": scanned, "self": SELF, "items": out}, fh, ensure_ascii=True, indent=1)
print("SCANNED", scanned, "CANDIDATES", len(out), "OUT", out_path)
PY
```

- 该片段只读 JSONL 与目录，只在 `%TEMP%` 下写 `tmp-qoder-attribution.json`；不删除任何条目。未替换占位符时以退出码 2 结束。
- `SELF` 必须是上一步探针命中的 sessionId；`PROJECT_TMP` 必须是实际工作区。两个占位符未替换时，前者会把自身计入引用，后者会扫描错误的根。
- 匹配使用右边界 `(?![A-Za-z0-9._-])`，修复前缀膨胀；但**左侧不设边界**，短名仍可能在更长 token 的尾部命中。候选名应保持可区分；不要把它说成完全精确匹配。不要用 `"|".join(names)` 的单条 alternation：正则按左到右尝试 alternatives，短前缀会先命中，带时间戳的长兄弟被吞掉，引用数虚高。逐名 `search` 并加右边界。
- `last_mention_age_h` 取自命中行的时间戳（`last_mention_src=ts`）；该行没有可用 `timestamp` 时回退会话 JSONL 的 mtime（`last_mention_src=mtime`）；mtime 只会让条目显得更新，是上界，不能据此放宽 3h 阈值。为负通常表示会话在扫描开始后仍在写入，按活跃处理。必须同时报 `last_mention_sid`：审计报告本身列出候选名也会重置最后提及，反复清点会把条目重新判成 ACTIVE-REF。案例或报告中的 `last_mention_age_h` 与 `last_mention_sid` 必须能由 JSONL 命中行复核；改写旧数字前回到原始工具输出或命中行重算，不沿用上下文摘要或上一份报告。
- 会话未注册（`wait_chat_sessions` 报「ChatSession 不存在」）只说明会话状态 UNKNOWN；条目仍按 `last_mention_age_h` 归类（本次两条 0.52h/2.14h 属 ACTIVE-REF），不要当成 cold。要确认注册情况用 `list_chat_sessions` 的 `limit`/`cursor` 分页。
- `ref_count=0` 在大语料中可能很少（2026-10-27 的 227 个候选中为 0 个），但绝大多数条目至少被一个其他会话提到。因此「有引用就保留」在大会话量下会导致无法清理，必须叠加新鲜度维度。引用只证明「被提到」，不证明会话仍在使用，也不证明会话已结束。
- 需要区分二阶提及时，读取每个命中会话的首条记录时间；删除之后才开始的会话只转述名称，不计入 SHARED。该判断仍不证明会话状态。
- 对疑似克隆，用 `git -C <path>/repo status -sb` 看分支与上游，用 `ls -la` 看 mtime。干净、跟踪 `origin/main` 且最近更新的克隆按「其他会话正在使用」处理。

归属判定仍按下表；新鲜度维度只决定 `SHARED` 是否可进入候选，不改变归属：

| 分类 | 判据 | 默认动作 |
|---|---|---|
| APP-MANAGED | `tmp/<编码项目名>/`、`.last-skill-*`、`%TEMP%/qoder-*` | 不触碰，除非用户明确要求 |
| OTHER-SESSION | 引用会话不含当前会话，或克隆最近更新并跟踪上游 | 不触碰 |
| SHARED | 至少一个其他会话引用（不含当前会话；删除之后才开始的 Skill 创建/审计会话只转述该名称，属于二阶提及，不计入） | 保留；用户确认具体路径后才可进入候选 |
| CURRENT | 排除当前会话 JSONL 后，无其他会话引用，且非 APP-MANAGED | 列入待删清单 |
| UNKNOWN | 无引用、无清晰大小/时间线索 | 保留并报告，不猜 |

新鲜度维度（叠加在归属之后）：

| 桶 | 判据 | 默认动作 |
|---|---|---|
| RECENT | 条目 `age_h < 6` | 保留（近 6h 内修改） |
| ACTIVE-REF | `last_mention_age_h < 3`（含负值） | 保留（仍有近期提及） |
| STALE-REF | `age_h >= 6` 且 `last_mention_age_h >= 3`，且非 APP-MANAGED | 可进入候选；仍需用户确认精确路径 |

6h/3h 是本案使用的启发式阈值，不是通用契约。用户要求更保守时提高阈值；接近阈值的条目按 ACTIVE-REF 处理。

判定顺序固定为 `APP-MANAGED` → `OTHER-SESSION` → `ACTIVE-REF`/`RECENT` → `SHARED`/`STALE-REF` → `CURRENT` → `UNKNOWN`。应用托管目录即使只被当前会话引用，也不进入待删清单。

### Step 3 生成确认清单

从 `tmp-qoder-attribution.json` 读回候选，按归属与新鲜度分桶，输出表格：

| 根 | 路径 | 类型/size | mtime / age_h | 引用数 | 最后提及 age_h / sid | 分类 | 建议动作 |
|---|---|---|---|---|---|---|---|

请用户确认**精确清单**，不要把「顺便清掉其他残留」打包进同一句。共享证据、UNKNOWN 与接近阈值的条目必须单独列出并单独确认。

- 机器可读 JSON 不是用户确认；确认必须是用户对新列出的路径逐项或整体明确答复。
- 若用户只说「清理全部」，仍然先列出清单并等待确认；把会删除的每一项显式写出。
- 待确认清单里同时写出「将保留」的类别与数量（APP-MANAGED、RECENT、ACTIVE-REF、OTHER-SESSION、UNKNOWN），避免用户误以为未列出的条目也会被删除。

### Step 4 删除确认项

少量条目可用内联循环（`continue` 在循环内是合法的）。目录与文件分开，使用字面路径与 `--`：

```bash
BASE="$HOME/.qoder/tmp"
for n in "confirmed-dir-a" "confirmed-dir-b"; do
  P="$BASE/$n"
  if [ -z "$n" ] || [ ! -e "$P" ]; then echo "SKIP $n"; continue; fi
  chmod -R u+w "$P" 2>/dev/null
  rm -rf -- "$P"
  if [ -e "$P" ]; then echo "STILL $n"; else echo "GONE $n"; fi
done
```

候选达数十个以上时，先生成显式路径清单，再用**逐项 `if/else`** 的脚本执行（不要用顶层 `continue`）：

```bash
LIST="$HOME/AppData/Local/Temp/tmp-qoder-delete-list.txt"   # 每行 "<root>|<name>"
LOG="$HOME/AppData/Local/Temp/tmp-qoder-delete.log"
SCRIPT="$HOME/AppData/Local/Temp/tmp-qoder-delete.sh"
export LIST

{
  echo '#!/usr/bin/env bash'
  echo 'USER_TMP="$HOME/.qoder/tmp"'
  echo 'PROJECT_TMP="REPLACE_WITH_WORKSPACE_ROOT/.qoder/tmp"'
  echo 'while IFS="|" read -r root name; do'
  echo '  [ -n "$root" ] || continue'          # 循环内 continue 合法
  echo '  if [ "$root" = "user" ]; then P="$USER_TMP/$name"; elif [ "$root" = "project" ]; then P="$PROJECT_TMP/$name"; else echo "SKIP_BAD_ROOT $root $name"; continue; fi'
  echo '  if [ -z "$name" ] || [ ! -e "$P" ]; then'
  echo '    echo "SKIP $root $name"'
  echo '  else'
  echo '    BEFORE=$(stat -c %Y "$P" 2>/dev/null)'
  echo '    if [ -d "$P" ]; then chmod -R u+w "$P" 2>/dev/null; rm -rf -- "$P"; else rm -f -- "$P"; fi'
  echo '    if [ -e "$P" ]; then echo "STILL $root $name"; else echo "GONE $root $name $BEFORE"; fi'
  echo '  fi'
  echo 'done < "$LIST"'
} > "$SCRIPT"

if bash -n "$SCRIPT"; then
  bash "$SCRIPT" | tee "$LOG"
else
  echo "SYNTAX_FAIL_ABORT"
fi
grep -nE '^\s*continue\s*$' "$SCRIPT" && echo "TOP_LEVEL_CONTINUE_SUSPECT" || echo "NO_TOP_LEVEL_CONTINUE"
```

- 在轻量夹具上先跑一次 `SKIP` 分支：确认不存在的条目只打印 `SKIP` 且不影响后续条目。`bash -n` 只证明语法，不证明控制流。
- `stat -c %Y` 记录删除前的 mtime（epoch 秒），用来证明删除的是确认清单里的那一版；它不复查引用会话。
- 日志与脚本保留到 Step 5 全部复查结束；不要在同一步删除用于定位的路径文件。
- 删除前再确认 `root` 只有 `user`/`project` 两种取值，未知取值直接 `SKIP` 并报告。项目侧只允许 `.qoder/tmp` 下的路径；`.qoder/snapshots` 不进入删除清单。

### Step 5 删除后复查

1. sentinel 复查（两个根都要扫）：

```bash
USER_TMP="$HOME/.qoder/tmp"
PROJECT_TMP="REPLACE_WITH_WORKSPACE_ROOT/.qoder/tmp"
find "$USER_TMP" "$PROJECT_TMP" -maxdepth 4 -type d -name system-commandline-sentinel-files 2>/dev/null
```

如果 sentinel 在已删克隆的原路径重新出现，只删除该目录：

```bash
BASE="REPLACE_WITH_ROOT_THAT_HELD_THE_DELETED_DIR"
DELETED_DIR="REPLACE_WITH_DELETED_DIR_NAME"
S="$BASE/$DELETED_DIR/system-commandline-sentinel-files"
find "$S" -maxdepth 1 2>/dev/null
du -sh "$S" 2>/dev/null
chmod -R u+w "$S" 2>/dev/null
rm -rf -- "$S"
[ -e "$S" ] && echo "STILL_SENTINEL" || echo "SENTINEL_GONE"
```

只删 sentinel 目录本身，不动父目录、配置或其他克隆。把 `BASE` 与 `DELETED_DIR` 换成实际值，不要照抄占位符。完成其他复查后再扫一次，因为重建可能发生在首次扫描之后。

2. 命名残留复查：

```bash
USER_TMP="$HOME/.qoder/tmp"
PREFIX="lock-lf"
if [ -n "$PREFIX" ]; then
  ls -d "$USER_TMP/$PREFIX"* 2>/dev/null || echo "NO_${PREFIX}_LEFTOVER"
else
  echo "PREFIX_EMPTY"
fi
```

3. 快照副本完整性（删除过项目快照时才需要）：

```bash
SNAPSHOTS="REPLACE_WITH_WORKSPACE_ROOT/.qoder/snapshots"
ls -l "$SNAPSHOTS"
sha256sum "$SNAPSHOTS"/*.json 2>/dev/null
py -3 -B -c "import glob,json,sys; fs=glob.glob(sys.argv[1]); assert fs; [json.load(open(p, encoding='utf-8')) for p in fs]; print('SNAPSHOTS_JSON_OK', len(fs))" "$SNAPSHOTS/*.json"
```

`sha256sum` 必须与删除前记录的副本哈希一致，JSON 必须可解析；任一项失败说明备份不可用，不得声称快照已安全归档。`.qoder/snapshots` 中的文件默认保留，不进入后续清理。

4. 导入缓存与源仓库：

```bash
SKILL_DIR="$HOME/.qoder/skills/REPLACE_WITH_SKILL_DIR_NAME"
find "$SKILL_DIR" \( -type d -name __pycache__ -o -type f -name '*.pyc' \) 2>/dev/null
git -C "$SKILL_DIR" status -sb
git -C "$SKILL_DIR" log -1 --oneline
```

把 `SKILL_DIR` 换成实际 Skill 目录。只删除本次导入生成的缓存，然后复核 `git status -sb` 首行为 `## main` 且无未提交项。后续导入可用 `py -3 -B` 或 `PYTHONDONTWRITEBYTECODE=1` 预防；来源会话只验证了删除结果，未验证这两个参数。

5. 最终清点：重新运行 Step 1 的顶层清单（两个根），与删除前快照对比，确认只有确认项消失、没有未确认的新增条目被牵连：

```bash
USER_TMP="$HOME/.qoder/tmp"
PROJECT_TMP="REPLACE_WITH_WORKSPACE_ROOT/.qoder/tmp"
SKILL_DIR="$HOME/.qoder/skills/auditer-nettoyer-temp-qoder"
echo "USER_TMP=$(du -sh "$USER_TMP" 2>/dev/null | cut -f1)"
echo "PROJECT_TMP=$(du -sh "$PROJECT_TMP" 2>/dev/null | cut -f1)"
echo "SNAPSHOTS=$(du -sh "REPLACE_WITH_WORKSPACE_ROOT/.qoder/snapshots" 2>/dev/null | cut -f1)"
echo "NESTED_GIT_DIR=$(find "$USER_TMP" "$PROJECT_TMP" -maxdepth 5 -type d -name .git 2>/dev/null | wc -l)"
echo "NESTED_GIT_FILE=$(find "$USER_TMP" "$PROJECT_TMP" -maxdepth 5 -type f -name .git 2>/dev/null | wc -l)"
echo "SENTINELS=$(find "$USER_TMP" "$PROJECT_TMP" -maxdepth 4 -type d -name system-commandline-sentinel-files 2>/dev/null | wc -l)"
find "$USER_TMP" "$PROJECT_TMP" -maxdepth 3 -type d -name __pycache__ 2>/dev/null
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$USER_TMP" --max-depth 5 --json --entry-limit 5000 > "$HOME/AppData/Local/Temp/tmp-qoder-after-user.json"
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$PROJECT_TMP" --max-depth 5 --json --entry-limit 5000 > "$HOME/AppData/Local/Temp/tmp-qoder-after-project.json"
```

对照要点：

- 总量下降应大致等于确认删除的字节数；差额来自其他会话的并发写入或应用缓存增长，报告里要说明，不要把差值算成删除量。
- 嵌套 Git 数量下降只反映被删的克隆；剩余克隆若位于应用托管缓存或其他会话目录，保留并列出。
- 执行期间出现的**新增条目**（其他会话创建）不在确认清单内，未触碰；在报告中单列。
- 应用托管缓存（`tmp/<编码项目名>/`）的体积变化不属于本次删除效果。

### Step 6 报告

用表格汇总：

| 根 | 项 | 类型/size | age_h | 引用数 | 最后提及 age_h / sid | 分类 | 动作 | 复查结果 |
|---|---|---|---|---|---|---|---|---|

报告必须写明：

- 已删除并复查消失的精确路径，以及删除前记录的 `stat -c %Y`；`SKIP`/`STILL` 项单列并说明原因。
- GCM sentinel 是否在原路径重建、如何二次删除、最后一次扫描时刻（两个根）。
- 已确认保留的条目及理由（应用托管、其他会话、ACTIVE-REF、RECENT、UNKNOWN）；保留类别的合计数量。
- 快照备份结果：副本路径、SHA-256、JSON 解析结果（如涉及）。
- 删除前后总量、应用缓存体积变化、嵌套 Git 数量变化、新增未触碰条目。
- 未验证项：引用会话的实时 `runtimeState` 未逐个检查（只用了 JSONL mtime 代理）、GCM 重建未主动复现、右边界只约束右侧。

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
| `%TEMP%` 的 `qoder-*-cwd` 或 `tmp/<编码项目名>` 达数十 MB | Qoder 内部工作目录标记；tool-results 会话缓存 | 应用托管，默认保留，不按「临时垃圾」删除 |
| 嵌套克隆位于 `fixture/repo/.git` | 夹具目录结构 | 用 `maxdepth 5` 枚举，按整个夹具目录判断归属 |
| `find -type d -name .git` 少于脚本的 `nested_git` | worktree 或子模块的 `.git` 是文件 | 同时用 `-type f -name .git`，或直接采信脚本的 `nested_git`；目录计数为 0 不等于没有嵌套仓库 |
| 删除共享证据后其他会话证据链断裂 | 多个会话引用同一文件 | 默认保留；用户点名后才删，并在报告中注明 |
| 删除后仍能 `ls` 到同名路径 | 只删了子目录或被重建 | 检查父目录、sentinel 与 mtime，不要只看一次 `rm` 退出码 |
| 短名条目引用数虚高（例如 `name-1` 命中 `name-10`） | 无右边界，前缀互吞 | 加 `(?![A-Za-z0-9._-])`；仍不约束左侧，报告注明 |
| 用 `"|".join(names)` 的 alternation 匹配 | 正则按左到右尝试，短前缀先命中长兄弟 | 逐名 `search` 并加右边界 |
| `ref_count=0` 的条目为 0 个，导致无法清理 | 「有引用就保留」在数百个候选下等价于全部保留 | 叠加新鲜度维度（条目 ≥6h 且最后提及 ≥3h） |
| 删除脚本打印 `continue: only meaningful in a 'for', 'while', or 'until' loop` 但仍继续执行 | 顶层 `continue`；`bash -n` 返回 0 | 改成逐项 `if/else`；在夹具上验证 `SKIP` 分支 |
| `last_mention_age_h` 为负数 | 通常是该会话在扫描开始后仍写入 | 按活跃处理（ACTIVE-REF），不进入候选 |
| `wait_chat_sessions` 报「ChatSession 不存在」 | 该会话未注册，状态不可查 | 用 `list_chat_sessions` 的 `cursor` 分页确认；仍查不到只把会话状态记 UNKNOWN，条目仍按最后提及 age 归类，不要当成 cold |
| 清点一次后报告列出的候选都变成 ACTIVE-REF；改写案例时 age/sid 与原始输出不符 | 审计报告本身列出候选名，重置了最后提及；上下文摘要或上一份报告提供二手 age/sid | 报告必须打印 `last_mention_sid`，区分「真实使用」与「报告转述」；改写案例数字前从 JSONL 命中行重算 age 与 sid，不沿用摘要或旧报告 |
| `du -sh` 与 `size_bytes` 不一致（922.1K vs 819.1K，1.2M vs 952K） | 前者是磁盘分配大小，后者是表观字节数 | 基线统一用一个口径，报告中注明差异来源 |
| 删掉 `.qoder/tmp` 中的快照后无法复现 | 快照是唯一副本 | 先复制到 `.qoder/snapshots`，校验 SHA-256 与 JSON，再删 tmp 副本 |
| 把 `<workspace>/.qoder/tmp` 当作用户级 `~/.qoder/tmp` 的别名 | 两个根路径不同，删除目标不同 | Step 0 显式设定 `USER_TMP`/`PROJECT_TMP`，删除脚本按 `root` 分派 |
| `RESULT PARTIAL` 时体积远小于 `du -sh` | `--entry-limit` 截断，TOTALS 只覆盖已扫描条目 | 提高 `--entry-limit`（本例 200 → 5000）重跑，再取基线 |
| 误删 `.qoder/snapshots` 中的归档 | 把它当成 tmp 垃圾 | 项目侧只处理 `.qoder/tmp`；`.qoder/snapshots` 默认保留 |

## 已验证案例

### 2026-10-26 克隆 / sentinel / 共享证据

来源会话 `324c8787-9642-4d4e-a16c-2cf4834fb20c`，完整引文与指纹见 `references/cas-nettoyage-temp-qoder-2026-10-26.md`。

1. 16:16:00Z 删除克隆 `pr-lock-lf.4v1Pgv`；16:20:10Z 同一路径出现 4.0K 的 `system-commandline-sentinel-files`，内含 `git-credential-manager` 的 .NET 组件；16:20:24Z 只删该目录后复查无其他 sentinel。
2. 16:24:57Z 按 basename 检索 JSONL：`live-audit-lock-lf` 被 5 个会话引用；`publish-hsas.C2cx6c` 被 5 个会话提到，且是干净克隆并跟踪 `origin/main`，未触碰。
3. 16:24:37Z 在 `github-pr-create-merge-sans-gh` 的 scripts 目录发现 `__pycache__`，`git status` 为 `?? scripts/__pycache__/`；16:25:13Z 删除后恢复为空。
4. 16:33:46Z 删除 7 个确认的 lock-lf 证据与日志，全部 `GONE`，`*lock-lf*` 残留 `NONE`，源仓库仍 `## main`；16:42:29Z 后出现的克隆 `pr-lock-lf-update.1793032871` 也删除，输出 `NO_PR_OR_SENTINEL_RESIDUE`。
5. 16:56Z 只读盘点脚本在真实 `~/.qoder/tmp` 返回 `RESULT OK`：102 顶层 / 1869 条目 / 54.3M / `nested_git=16`，sentinel 与缓存均为 0；夹具另覆盖 `.git` 文件、非 ASCII 文件名与退出码 2。边界：`qa-lf-20261026.log` 未纳入那次检索；未逐个核验引用会话实时状态；GCM 重建未主动复现。

### 2026-10-27 大规模归属、最后提及与项目快照

来源会话 `e4b7c222-3dad-4ee8-8e92-2670c97e43b4` 与 `4c86bebd-4ce4-460b-9038-884f8f91c737`，完整引文与指纹见 `references/cas-nettoyage-temp-qoder-2026-10-27.md`。

1. 基线（`e4b7c222`）：用户级 2,554 条目 / 84.8M / 204 顶层；项目级 176 条目 / 943.0K / 23 顶层；`nested_git=11`、sentinel 1、`pyc` 1。首跑 `--entry-limit 200` 得 `PARTIAL` 且只报 3.2M，说明截断会严重低估体积。
2. 单遍扫描 303 个 JSONL（排除自身）、227 个候选：`NO_REF=0`、`OLD_REF=170`、`ACTIVE_REF=55`、候选 159 个；只按「有引用就保留」会让 159 个全部误判为共享。删除脚本第一版在顶层用 `continue`：`bash -n` 返回 0，运行时报 `continue: only meaningful in a 'for', 'while', or 'until' loop` 且不跳过后续条目；改写为逐项 `if/else` 后，159 个显式路径（user 149 + project 10）全部 `GONE`，无 `SKIP`/`STILL`，运行 09:41:26Z–09:41:55Z。
3. 复查（`e4b7c222`）：总量 84.8M → 80.5M（应用缓存同期 77.6M → 79.7M，另一会话仍在写入）；`nested_git` 11 → 2（剩余在应用托管缓存内）；sentinel 0；项目 tmp 剩 13 项；执行期间新建的 `55f63550-extract/` 未触碰。
4. 12:33–12:38Z（`4c86bebd`）：文件 mtime 代理把 13 行候选全算成 `-0.0`/`-0.01`；改按行 `timestamp` 取最后提及后得到 2.14h（sid `3c861dde`）与 0.52h（sid `fdb57827`）。这两个会话未注册，`wait_chat_sessions` 报「ChatSession 不存在」，会话状态记 UNKNOWN，条目仍按 2.14h/0.52h 判 ACTIVE-REF。用户确认后 6 个路径 `GONE`（epoch 已记录）、7 项保留；项目 `.qoder/tmp` 922.1K/1.2M → 819.1K/952K，顶层 13 → 7；新增的 `acceptance-helpers-20261027`、`porte_skill.sh`、`qa-edit-skill-after.txt` 未触碰。
5. 报告重置：12:38:15Z 的报告列出这些名称；12:57:57Z 独立复跑（`SCANNED 334 CANDIDATES 28`）时，6 个幸存旧条目里 5 个回到 0.33h、`contract_audit` 为 0.11h，sid 均为 `4c86bebd`；项目缓存 -0.01h（sid `d4a03af8`，另一会话仍在写入），所以报告必须带 `last_mention_sid`。边界：只加右边界；未逐个查 `runtimeState`；GCM 重建未主动复现。

## 验收片段

以下片段只读，不执行删除：

```bash
USER_TMP="$HOME/.qoder/tmp"
PROJECT_TMP="REPLACE_WITH_WORKSPACE_ROOT/.qoder/tmp"
SKILL_DIR="$HOME/.qoder/skills/auditer-nettoyer-temp-qoder"
[ -d "$USER_TMP" ] && echo "USER_TMP_OK" || echo "USER_TMP_MISSING"
[ -d "$PROJECT_TMP" ] && echo "PROJECT_TMP_OK" || echo "PROJECT_TMP_MISSING"
echo "SENTINELS=$(find "$USER_TMP" "$PROJECT_TMP" -maxdepth 4 -type d -name system-commandline-sentinel-files 2>/dev/null | wc -l)"
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$USER_TMP" --max-depth 5 --recent-minutes 60 --entry-limit 5000 | sed -n '1,10p'
py -3 -B "$SKILL_DIR/scripts/inventorier_tmp_qoder.py" --root "$PROJECT_TMP" --max-depth 5 --recent-minutes 60 --entry-limit 5000 | sed -n '1,10p'
```

预期两个 `_OK`；`SENTINELS` 可能非零（其他克隆也可能有），必须解释而不是直接删除；脚本的 `MARKERS nested_git` 同时包含 `.git` 目录与文件，不要与只数目录的 `find` 结果直接比较；这些值随夹具创建与清理变化，只作清点基线，不是待删数量。脚本应打印 `RESULT OK` 或 `RESULT PARTIAL` 并以退出码 0 结束；出现 `PARTIAL` 时先读 `ERRORS`，并提高 `--entry-limit` 重跑。

## 资源

- `references/cas-nettoyage-temp-qoder-2026-10-26.md`：来源会话时间线、逐字输出、指纹与分级，以及脚本增量的夹具与真实运行记录。
- `references/cas-nettoyage-temp-qoder-2026-10-27.md`：项目快照归档、单遍归属扫描（303 会话 / 227 候选 / 159 删除）、顶层 `continue` 缺陷、最后提及与未注册会话（第二来源 `4c86bebd`）、删除前后对比与分级边界。
- `scripts/inventorier_tmp_qoder.py`：只读盘点脚本（`--root`、`--max-depth`、`--recent-minutes`、`--entry-limit`、`--json`；退出码 0/2），输出顶层 size/mtime/recent、嵌套 `.git`（目录与文件）、sentinel 与 `__pycache__`/`.pyc` 计数。
- `skill-package-integrity-audit`：只读审计 Skill 包内缓存与归档。
- `audit-session-evidence`：会话证据链与来源核实方法。
- `extraire-preuves-session-qoder`：从项目 JSONL 提取可复核证据。
- `github-pr-create-merge-sans-gh`：PR 流程、`refs/qoder-tmp/*` 与 sentinel 陷阱。
- `nettoyer-branches-refs-git`：分支与 refs 清理。
- `skill-file-qa`：写入后的静态验收与指纹。
