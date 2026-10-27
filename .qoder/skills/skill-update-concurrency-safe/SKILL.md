---
name: skill-update-concurrency-safe
description: "在创建或更新 Skill 包时防止并发写入覆盖：检查目标目录并分流 create/update，用 size、mtime、SHA-256 双采样确认文件稳定，读取真实 SKILL.md 与 references，优先最小 Edit；整文件重写前备份到 .qoder/tmp，保留并合并并发新增内容，同步参考文件；写入后重跑 skill-file-qa，双语或带翻译参考时再跑对等校验，最后重读并记录哈希。用于目标目录突然出现、编辑期间文件反复变化、create 命中已有同名 Skill、上一轮写入失败、更新含 references 的 Skill，或验证期间文件再次变化；静态校验只覆盖 SKILL.md 代码块，含 .pyc 的文件数仍可能 PASS。关键词：并发写入、稳定性采样、写入前备份、create 不覆盖、最小编辑、双重校验、运行时注入、哈希复核、脚本行为回归、正例与反例套件、退出码断言、cp1252、__pycache__、本地引用误判、反引号目录、local reference、QA 重跑、校验器探针。"
---

# 并发安全的 Skill 创建与更新

## 何时使用与边界

在创建或更新 Skill 包时使用，尤其是以下情况：

- 目标目录在确认方案后突然出现；
- 编辑期间 `SKILL.md` 的 size、mtime 或 SHA-256 反复变化；
- create 命中已有同名 Skill，需要切换到 update；
- 上一轮写入失败或中断，需要重新确认磁盘状态；
- Skill 含 references、翻译版或脚本，修改后需要同步。
- 静态校验 PASS 但随附脚本未被语法检查，或文件清单出现 `.pyc`。

本 Skill 只负责并发安全与写入顺序，不替代以下流程：

- 来源会话核实：使用 `audit-session-evidence`；
- frontmatter、引用、代码块等静态验收细节：使用 `skill-file-qa`；
- canonical/legacy 共存迁移：使用 `skill-canonical-migration`；
- 两种语言的完整结构对等：使用 `bilingual-skill-parity`；
- Skill 内容本身的编写规范：使用 `skill-creator`。

## 核心原则

1. 以磁盘实物为准，不以写入成功提示、上一轮摘要或加载列表为准。
2. create 不覆盖已有同名 Skill；目标存在时一律先读后改。
3. 稳定性采样只是快照，不是锁。写入前必须重新采样，写入后必须复核。
4. 更新已有 Skill 优先使用最小 `Edit`；整文件 `Write` 仅用于必要的结构重写，且必须先备份并逐条合并并发内容。
5. 并发进程新增的翻译、参考文件或规则必须保留，不因“重复”或“计划外”而删除。
6. 没有重读实际文件、没有校验器结果、没有稳定哈希时，不宣称创建或更新成功。
7. 新建前先搜索已安装 Skill 的 description 与正文；同能力已存在时优先更新，不创建触发词相同的重复 Skill。
8. 结构校验通过不等于行为正确。修改 scripts 目录中的脚本后，必须做语法校验、真实样本正例与独立反例套件，并记录退出码。

## 0. 预检与 create/update 分流

检查用户级和项目级 skills 根中的目标路径：

```bash
target="$HOME/.qoder/skills/<skill-name>"
if [ -e "$target" ]; then
  echo "UPDATE: target already exists"
else
  echo "CREATE: target absent"
fi
```

- 目录与 `SKILL.md` 都存在：进入 update。先列出并读取现有文件，保留仍有效规则，再提出最小修改。
- 目录存在但 `SKILL.md` 缺失：视为上一轮 create 中断或并发写入的中间态；先按第 1 节采样目录，等待 `SKILL.md` 出现并稳定。确认没有写入者后，才在 `test ! -e "$target/SKILL.md"` 保护下创建；不得把空目录当作普通 update 读取。
- 目标不存在：进入 create。检查加载列表中是否已出现同名 Skill；若已出现但路径不存在，先调查安装位置，不盲目创建。
- create 时使用不带 `-p` 的 `mkdir`，让“目录已存在”直接失败，避免静默复用并发目录：

```bash
target="$HOME/.qoder/skills/<skill-name>"
mkdir "$target" || { echo "RACE: target appeared"; exit 1; }
test ! -e "$target/SKILL.md" || { echo "RACE: SKILL.md appeared"; exit 1; }
```

- `mkdir` 成功后、写入 `SKILL.md` 前再次检查文件是否存在。若已出现，停止 create，转为 update 并重新读取。
- 不使用 `mkdir -p` 创建目标 Skill 目录。

## 1. 稳定性采样

至少记录 `size`、完整 `mtime` 和 SHA-256。两次采样只能作为最低门槛；已知有并发写入时，要求连续多个哈希一致后再继续。

```bash
f="$target/SKILL.md"
stat -c '%s bytes | %y' "$f"
sha256sum "$f"
sleep 2
stat -c '%s bytes | %y' "$f"
sha256sum "$f"
```

需要等待不稳定文件时，使用有上限的循环：

```bash
f="$target/SKILL.md"
last=""
same=0
for i in $(seq 1 10); do
  cur=$(sha256sum "$f" | cut -d' ' -f1)
  printf '%s | %s bytes | %s\n' "$(date '+%H:%M:%S')" "$(stat -c '%s' "$f")" "${cur:0:16}"
  if [ "$cur" = "$last" ]; then
    same=$((same + 1))
  else
    same=0
    last="$cur"
  fi
  if [ "$same" -ge 2 ]; then
    echo "STABLE: 3 identical hashes"
    break
  fi
  sleep 2
done
```

- `same >= 2` 表示连续 3 次哈希一致，作为默认稳定条件。
- 已知有持续写入时，把阈值提高到 `same >= 3` 或 `same >= 4`，并保持循环上限。
- 约 20 秒内仍不稳定时停止，报告“文件仍在被并发写入”，不要覆盖。
- 记录目录内全部文件的基线，不只记录 `SKILL.md`：

```bash
find "$target" -maxdepth 3 -type f -exec sha256sum {} + | sort
```

- 基线写入系统临时目录或审计文件，不写入 Skill 目录。

## 2. 读取真实内容

1. 列出目录内全部文件，确认是否有 references、翻译文件、脚本或 assets。
2. 完整读取 `SKILL.md` 的 frontmatter 和正文，不只看摘要。
3. 读取与本次修改相关的 references、翻译文件和脚本；记录各自的基线哈希。
4. 对照当前需求，区分“仍有效规则”“需要修改的规则”“并发新增内容”。
5. 在第一次编辑前再次采样目标文件；哈希与读取时不同，则放弃当前修改计划，重新读取。

## 3. 最小 Edit 与写入前备份

- 更新已有 Skill 优先使用最小 `Edit`；只有结构重写（例如把双语正文合并为单一文件、批量迁移章节）才允许整文件 `Write`，并必须先完成 3.1 的备份。
- 使用 `Edit`，提供足够上下文，使 `old_string` 唯一；一次只做一个逻辑修改。
- `old_string` 未找到或不再唯一，说明文件已变化：重新读取，不要用更宽泛的替换强行命中。
- 遇到与并发内容冲突的修改，先备份当前版本，再合并到最小 `Edit` 中；无法安全合并时停止并报告，不以整文件写入强推。
- 不删除并发进程新增的翻译、参考文件、脚本或规则。
- 不顺手重排、重写或“整理”无关内容；只改本次确认的规则。
- 一个文件修改完成后重新读取并计算哈希；编辑下一个文件前，重新核对它的基线哈希。

### 3.1 写入前备份与目录复核

整文件重写前必须备份；最小 `Edit` 也建议先备份，成本很低。备份必须放在 Skill 目录之外：

```bash
root="$HOME/.qoder/tmp/<project>/skill-backup"
mkdir -p "$root"
backup="$root/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$backup" || { echo "BACKUP EXISTS: choose another name"; exit 1; }
cp -a "$target/SKILL.md" "$backup/SKILL.pre-write.md"
if [ -d "$target/references" ]; then cp -a "$target/references" "$backup/references"; fi
if [ -d "$target/scripts" ]; then cp -a "$target/scripts" "$backup/scripts"; fi
find "$backup" -type f -exec sha256sum {} + | sort
```

- `mkdir -p` 只用于备份根，不用于目标 Skill 目录本身。
- 使用 UTC 时间戳；目录已存在时追加序号或随机后缀，禁止覆盖或删除旧备份。
- 备份后再次采样当前文件；哈希与备份不一致时，说明备份期间又被写入，重新备份并读取。
- 写入前重新扫描目标目录；若出现基线中没有的翻译、参考文件或脚本，先读取并合并其独有规则，不得以“计划外”或“重复”为由删除。
- 写入后把备份与新文件对照：抽查备份中的唯一标题、错误原文、路径和命令是否仍存在；缺失时恢复并重新合并，不能以“校验器通过”代替内容比对。

## 4. 同步 references 与翻译版

- 修改 `SKILL.md` 后，在 references 目录搜索同一规则的唯一短语：

```bash
grep -R -n --exclude-dir=.git -- "<unique phrase>" "$target/references" 2>/dev/null || true
```

- 找到对应内容时，对翻译版或参考版做等价的最小 `Edit`。
- 代码块、命令、路径、工具名和错误原文保持不翻译；只翻译说明文字。
- 并发进程新增的参考文件必须保留，不得以“计划中没有”为由删除。
- 需要两种语言的完整结构对等时，改用 `bilingual-skill-parity`；本 Skill 只同步本次改动涉及的规则。

## 5. 写入后验证

### 5.1 重读实物

```bash
sha256sum "$target/SKILL.md"
find "$target" -maxdepth 3 -type f -printf '%P | %s bytes\n' | sort
```

- 确认目标修改存在且只出现一次。
- 确认并发新增内容仍在。
- 确认目录中没有多出 README、CHANGELOG 或临时文件。
- 记录写入后的哈希；如果与编辑后立即取得的哈希不同，说明又有写入，停止并重新读取。

### 5.2 运行结构校验

```bash
QA="$HOME/.qoder/skills/skill-file-qa"
py -3 "$QA/scripts/validate_skill.py" "$target" \
  --workspace "<workspace-root>" \
  --stable-seconds 2 \
  --stability-timeout 30
```

- Windows 上先验证解释器：`python --version` 若提示 Microsoft Store，改用 `py -3`。
- 退出码 0：无 FAIL；仍需阅读并记录 WARN。
- 退出码 1：存在 FAIL；修复后重跑，不能宣称通过。
- 退出码 2：用法或环境错误；检查路径、解释器和 `--workspace`。
- `--workspace` 必须是实际 workspace 根；`$PWD` 仅在从该根运行时才等价，不要假定当前目录。
- 校验器报告文件在校验期间变化时，不复用旧结果；重新读取稳定版本后重跑。
- 记录实际 PASS、FAIL、WARN 数量和关键输出，不复制历史数字。
- 必须同时读取 `Files (n)` 与 `Code blocks: python=N js=N skipped=M`，不能只看 `RESULT PASS`。
- `validate_skill.py` 只提取并解析 `SKILL.md` 内的 Python/JS 代码块，不读取 `scripts` 目录。技能含 `.py` 脚本却显示 `python=0` 时，脚本语法尚未验证。
- 文件清单由 `rglob` 生成，`scripts` 下 `__pycache__` 里的 `.pyc` 会计入 `Files (n)`；`scripts` 是允许目录，因此布局仍可能 PASS。PASS 不代表目录干净。
- 指纹只覆盖 `SKILL.md`；脚本被改写不会触发 “fingerprint changed”。脚本需按 5.4 单独校验。
- 校验器会把全文（包括围栏代码块内）反引号包裹、以 scripts、references 或 assets 加结尾斜杠开头的 token 当作本地引用；本 Skill 没有对应目录时即报 `local reference not found`。裸目录、缓存目录和指向其他 Skill 的脚本路径都会命中。
- 路径规范化会去掉点斜杠前缀，因此点斜杠加 scripts 结尾斜杠与裸目录写法等价；以 `$`、`/`、`~` 开头，或含空格、`*`、尖括号的 token 会被忽略。
- 安全写法：「`scripts` 目录」、`$target/scripts/*`、`$QA/scripts/validate_skill.py`；不要把目录名或别家脚本路径单独放进反引号。围栏块内只有裸路径（无反引号）免检，块内再套反引号仍会被扫描。
- 并发写入者新增的同类文字同样会触发 FAIL；文件每次变化（含并发改写）后必须重跑 QA，不能沿用旧 PASS。
- 不确定某种写法是否会被当作本地引用时，不采信自动推荐或“围栏代码块豁免”之类未经实测的结论；在 Skill 目录之外建临时探针实测：

```bash
PROBE=$(mktemp -d "$HOME/.qoder/tmp/ref-probe.XXXXXX")
mkdir "$PROBE/skill" "$PROBE/workspace"
# 在 $PROBE/skill/SKILL.md 放入候选 token；frontmatter 的 name 必须为 skill，与目录同名
py -3 "$QA/scripts/validate_skill.py" "$PROBE/skill" \
  --workspace "$PROBE/workspace" --stable-seconds 0
```

- 以 `FAIL local reference not found: '<token>'` 原文判定：出现即该写法会被扫描，只有未出现才能写进正文。探针的 `RESULT FAIL` 是预期结果，不是目标 Skill 的结论。
- 围栏代码块是否豁免必须由探针回答；`check_refs` 接收全文，实测中围栏内反引号 token 仍会命中。
- 探针放在 Skill 目录之外，用后删除；删除后确认目标目录没有新增文件，失败 token 不复制进正文。

实际输出示例（失败行不含反引号，放在围栏内不会被扫描）：

```text
FAIL local reference not found: 'scripts/'
FAIL local reference not found: 'scripts/__pycache__/'
```

### 5.3 双语或参考文件对等校验

存在两种语言正文、翻译版或 references 镜像时，写入后还必须运行：

```bash
PARITY="$HOME/.qoder/skills/bilingual-skill-parity"
py -3 "$PARITY/scripts/check_bilingual_parity.py" "$target"
```

- 使用 `py -3`；不要假定 `python` 可用。
- 对等校验与 `skill-file-qa` 必须在同一稳定指纹上通过；任一失败都不得宣称完成。
- 对等失败若表现为另一侧缺少内联词、数字或清单项，先检查该侧 mtime 是否仍在变化；可能只是并发进程尚未同步。等待稳定后重跑，不覆盖或删除对方内容。
- 单语 Skill 没有翻译版时，明确写“对等校验：不适用”，不要伪造 PASS。

### 5.4 修改脚本后的行为回归

本次改动涉及 Skill 的 scripts 目录时，`skill-file-qa` 即使 PASS 也不代表脚本可用：它只解析 `SKILL.md` 内的代码块，不读取 scripts 目录，也不执行脚本。必须单独验证语法与行为。

1. **语法校验。** 优先用解析而非导入，避免生成 `__pycache__`：

```bash
py -3 -c "import ast,sys,pathlib; ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))" "$target/scripts/<script>.py"
```

若必须用 `py -3 -m py_compile "$target/scripts/<script>.py"`，它会在 `scripts` 下的 `__pycache__` 写入 `.pyc`；这是构建产物，不是脚本内容，完成后按第 5 步删除并复核。

2. **真实样本正例。** 用实际数据或真实文件对运行脚本，记录退出码和 PASS 数量（例：两对真实译本各 8 PASS / 0 FAIL、`EXIT=0`）。只用合成夹具不足以证明真实输入可用。除预期字段外，还要记录每个受关注列表的 `longueur`、`signatures` 合计、`sans_signature`、`distribution`，以及顶层计数器（如 `total_fichiers_harmonises`、`nb_blocs`）。`longueur > 0` 且 `sans_signature == longueur` 说明别名或模式不匹配：停止并读取真实条目键，不能当作噪声或“无变化”；只检查一个列表或一个字段不足以证明正例。
3. **独立反例套件。** 每个用例使用 Skill 目录之外的独立临时目录，逐项断言退出码 `0`、`1` 或 `2`，输出 `[OK]` 或 `[MISMATCH]`，最后输出 `SUMMARY: n/n passed`。至少覆盖本次修改针对的每个维度及其边界。
4. **A/B 变异负向对照。** 当本次修复能定位到具体常量或分支时，复制当前脚本到 Skill 目录之外，只回退本次修复的常量或分支，用同一夹具比较当前脚本与副本；无法构造单变量副本时，明确写“A/B 不适用”并说明理由。副本运行前必须同时满足三项前置条件：每处替换恰好命中 1 次、副本 SHA-256 与原脚本不同、`ast.parse` 副本通过。前两项通过仍可能留下语法损坏，不能省略解析。多行括号元组使用整元组匹配或 AST 定位，禁止用只匹配首行的 `^CONST\s*=.*$`：

```python
import ast, hashlib, re
from pathlib import Path

source = Path(script).read_text(encoding="utf-8")
copy, replaced = re.subn(
    r"^TS_KEYS\s*=\s*\([^)]*\)",
    old_tuple,
    source,
    count=1,
    flags=re.MULTILINE,
)
assert replaced == 1
assert hashlib.sha256(copy.encode("utf-8")).digest() != hashlib.sha256(source.encode("utf-8")).digest()
ast.parse(copy)
```

用同一夹具、同一参数和同一环境分别运行当前脚本与副本，各跑两次：副本必须在预期断言或业务退出码上失败（记录退出码与关键输出），当前脚本必须通过同一断言；副本若只报 SyntaxError、路径或环境错误，A/B 无效。两次结果一致才算确定性。删除副本与夹具，不把失败 token 留在 Skill 目录。
5. **清理与复核。** 先确认缓存里只有 `.pyc`，再删除；交付前确认 Skill 目录没有 `__pycache__`、`.pyc`、临时夹具或测试输出：

```bash
cache="$target/scripts/__pycache__"
if [ -d "$cache" ]; then
  extra=$(find "$cache" -type f ! -name '*.pyc' -print)
  test -z "$extra" || { printf '%s\n' "$extra"; echo "UNEXPECTED FILES: not removing"; exit 1; }
  rm -r "$cache"
fi
find "$target" \( -name __pycache__ -o -name '*.pyc' \) -print
```

删除后重跑 5.2 的 `validate_skill.py`，确认最终 `Files (n)` 与预期一致：例如技能只有 `SKILL.md` 和 1 个脚本时应为 `Files (2)`，而不是清理前的 `Files (3)`。

- 修改后只跑 `skill-file-qa` 仍 PASS，不能证明旧缺陷已修复；必须看到反例从失败变为通过，并看到正例仍通过。
- 反例的期望退出码来自脚本契约（0 通过 / 1 业务失败 / 2 用法或环境错误），不能为了让用例通过而改期望值。
- 脚本行为验证与 `skill-file-qa`、对等校验必须在同一稳定指纹上完成。

### 5.5 文件与加载状态

- 文件存在于磁盘不等于 Skill 已加载。列表未刷新时提示 `/skills reload` 或重启会话。
- 若目标是 create，确认最终目录和文件确实存在；若目标是 update，确认原有文件未被整文件覆盖。
- `qoder` CLI 可能不存在，`/skills reload` 无法执行；此时直接调用一次目标 Skill，核对注入内容是否包含本次新增的唯一标题或清单项。注入成功只证明正文可加载，列表刷新仍需重启会话。
- 注入测试后再次计算哈希；若文件在调用期间又被改写，以磁盘最终稳定版本为准重跑校验，不能把注入时的旧版本结论当成最终结论。

## 6. 已验证故障与处理

| 现象 | 原因 | 处理 |
|---|---|---|
| 预检时目标不存在，写入前突然出现 | 并发进程创建了同名 Skill | 停止 create，读取现有内容，转为 update；不覆盖 |
| 目录已存在但 `SKILL.md` 尚未出现 | 上一轮 create 中断，或另一进程刚创建目录 | 先采样并等待文件出现并稳定；确认无写入者后，用 `test ! -e` 保护创建；不当作普通 update |
| 读取后 size、mtime 或哈希变化 | 并发写入仍在进行 | 放弃当前修改计划，重新采样并读取；保留新内容 |
| `old_string` 找不到或不唯一 | 文件已被并发修改 | 重新读取并重新定位；不要用宽泛替换或整文件写入强推 |
| `python` 提示 Microsoft Store 或找不到 | `python` 是 Store 存根 | 使用 `py -3`；先运行 `py -3 --version` 验证 |
| 校验器退出 2 | 路径、解释器或 `--workspace` 参数错误 | 使用绝对脚本路径和实际 workspace 根重跑 |
| 并发进程新增中文参考或翻译文件 | 另一流程正在完善 Skill | 保留文件；搜索并同步本次规则；不要当作重复删除 |
| 上一轮 assistant 状态为失败或中断 | 写入可能未发生，也可能只完成一部分 | 先重读磁盘和哈希，不假设上轮修改已落盘 |
| 校验期间哈希再次变化 | 校验器检测到并发写入 | 重新等待稳定并重跑；不得使用旧 PASS 结论 |
| 对等校验失败，另一侧缺少内联词、数字或清单项 | 并发进程尚未同步该侧 | 检查 mtime，等待稳定后重跑两项校验；不覆盖或删除并发内容 |
| 整文件重写后发现旧规则缺失 | 未先备份或未逐条合并 | 从 `.qoder/tmp/.../skill-backup/` 恢复，按备份逐条合并后重写 |
| 备份目录已存在 | 同一秒内重复备份或并发写入 | 追加序号或随机后缀；禁止覆盖旧备份 |
| `qoder: command not found` | CLI reload 不可用 | 直接调用 Skill 验证注入；列表刷新需重启会话 |
| 改脚本后只跑 `skill-file-qa` 仍 PASS，旧缺陷未被发现 | QA 只检查 `SKILL.md`，不读取或执行 scripts 目录 | 用真实样本正例 + 独立反例套件验证退出码 0/1/2 |
| 控制台打印非 ASCII 触发 `UnicodeEncodeError`（cp1252/charmap） | Windows 控制台代码页不是 UTF-8，不是文件损坏 | 脚本输出保持 ASCII 或用 `backslashreplace`；临时命令设 `PYTHONUTF8=1` 或加 `-X utf8`；不要据 traceback 判定文件编码损坏 |
| Skill 目录出现 `__pycache__` 或 `.pyc` | `py_compile`、导入或运行脚本生成 | 改用 `ast.parse` 校验，或交付前删除并用 `find` 复核 |
| 校验器显示 `Code blocks: python=0`，但技能含 `scripts` 下的 `.py` 脚本 | `validate_skill.py` 只解析 `SKILL.md` 围栏，不读取脚本目录 | 单独运行 `ast.parse` 或 `py_compile`；`RESULT PASS` 不能替代脚本语法检查 |
| 校验报告 `Files (n)` 含 `.pyc`，仍 `PASS layout` | `scripts` 是允许目录，布局检查不排除构建产物；指纹只覆盖 `SKILL.md` | 对照预期清单；删除 `__pycache__` 后重跑，确认文件数回到预期 |
| QA 报 `local reference not found`，引用名是 scripts、references 或 assets 的裸目录 | 反引号中的裸目录 token 被当作本地引用；点斜杠前缀会被归一化后同样命中 | 改为「`scripts` 目录」或 `$target/scripts/*`；围栏内反引号仍会被扫描；修正后重跑 |
| 并发写入后 QA 再次 FAIL 同类引用 | 校验器扫描全文，新增段落同样计入；文件已变化 | 等稳定、重读全文并修正所有同类 token，再重跑；不要只修自己写的那处 |
| 多行常量用 `^CONST\s*=.*$` 回退 | 只替换首行，副本保留元组剩余行；替换计数为 1、哈希也变化，但 `ast.parse` 报 `IndentationError` 或 `SyntaxError` | 用 `^CONST\s*=\s*\([^)]*\)` 匹配整个括号元组或用 AST；副本运行前必须 `ast.parse` |
| 真实样本出现 `0 条识别 / N 条` | 另一类同构列表（如 ledger 的 `blocs`）使用不在别名中的 `timestamp_utc`，100 条全部无签名；顶层计数 `nb_blocs` 远大于保留长度 | 检查所有受关注列表的签名、无签名、分布与顶层计数器；这是同类缺陷信号，停止并核对真实键，不能当作噪声 |
| 新增断言后文档仍写旧的 `TOTAL=` | 断言从 70 增到 80，但 `SKILL.md`、协议、案例仍写 `TOTAL=70` | 新增断言后 grep 整个包的 `TOTAL=`，同步所有出现处；重跑后以实际输出为准 |

## 7. 报告模板

```text
模式：CREATE / UPDATE
目标：<绝对路径>
备份：<备份目录；不适用时写明>
文件：<文件列表>
写入前哈希：<sha256>
写入后哈希：<sha256>
稳定性：<采样次数、连续一致次数、是否超时>
校验器：EXIT <0/1/2>；<n> PASS / <n> FAIL / <n> WARN
脚本语法：<ast.parse / py_compile；EXIT；__pycache__ 已清理 | 不适用>
A/B 变异：<副本哈希已变；ast.parse 通过；副本 EXIT=<n>/<失败断言>；当前 EXIT=0/<通过断言>；连跑 2 次一致 | 不适用>
真实样本计数器：<列表：longueur/签名/无签名/顶层计数；0/N 已停止 | 不适用>
校验器覆盖：<Code blocks: python=N js=N；Files (n) 与预期一致 | 未核对>
本地引用：<n checked 或全部解析成功 | FAIL: <token>>
对等校验：EXIT <0/1/2>；<n> PASS / <n> FAIL / 不适用
文件清单：<仅预期文件 | 发现多余文件>
加载状态：<已出现 | /skills reload 后确认 | 需重启会话 | 未验证>
限制：<未触发分支、仍存在的并发写入、未验证内容>
```

- 没有实际重读和校验时，写明“尚未写入”或“写入未验证”。
- 并发写入未停止时，写明“文件仍不稳定”，不给出成功结论。
- 不把“语法通过”写成“运行通过”，不把“文件存在”写成“Skill 已加载”。

## 8. 完成检查清单

- [ ] 已检查目标路径与用户级、项目级 skills 根。
- [ ] create 使用不带 `-p` 的 `mkdir`，没有覆盖同名 Skill。
- [ ] 已记录 size、mtime、SHA-256；不稳定时有有上限的等待，不无限循环。
- [ ] 已读取真实 `SKILL.md`、references、翻译版和相关脚本。
- [ ] 优先使用最小 `Edit`；整文件重写已按 3.1 备份，且并发新增内容全部保留。
- [ ] 整文件重写前已备份到 `.qoder/tmp/.../skill-backup/`，并记录全部备份文件的 SHA-256。
- [ ] 写入前已重新扫描目录，并合并并发新增的翻译、参考文件或脚本。
- [ ] references 或翻译版中的对应规则已同步。
- [ ] 使用 `py -3` 运行 `skill-file-qa`，记录真实退出码和 PASS/FAIL/WARN。
- [ ] 双语或翻译版已运行对等校验；单语时明确标注不适用。
- [ ] 写入后重读文件并记录哈希；哈希在验证结束时仍稳定。
- [ ] 目录中只有预期文件，没有 README、CHANGELOG 或临时文件。
- [ ] 运行时注入已核验，或明确标注未验证/需重启会话。
- [ ] 报告区分已验证、未触发和仍不稳定的部分；必要时提示 `/skills reload` 或重启会话。
- [ ] 修改过 scripts 目录时，已做语法校验、真实样本正例与独立反例套件，并记录各用例退出码。
- [ ] 修改脚本后做了 A/B 变异：副本每处替换恰好命中 1 次、SHA-256 已变、`ast.parse` 通过；副本在预期断言失败、当前脚本通过，整套连跑两次一致。
- [ ] 回退多行常量时使用整元组匹配或 AST，没有用只匹配首行的 `^CONST\s*=.*$`。
- [ ] 真实样本正例检查了所有受关注列表的长度、签名、无签名、分布与顶层计数器；没有把 `0 条识别 / N 条` 当作噪声。
- [ ] 新增或删除断言后，已 grep 并同步包内所有 `TOTAL=` 或断言数文档。
- [ ] 已读 `Code blocks: python=N` 与 `Files (n)`，未把 `python=0` 或含 `.pyc` 的 `RESULT PASS` 当作脚本已验证、目录干净。
- [ ] QA 的 local references 行显示 0 checked 或全部解析成功，没有 `local reference not found`。
- [ ] 文件每次变化（含并发新增）后都重跑了 QA；正文反引号中没有裸 scripts、references、assets 目录 token。
- [ ] 需要确认新写法的引用行为时，已用 Skill 目录之外的临时探针实测，探针已删除。
- [ ] 删除 `__pycache__` 后已重跑 `skill-file-qa`，最终 `Files (n)` 与预期一致。
- [ ] Skill 目录没有 `__pycache__`、`.pyc`、临时夹具或测试输出。
- [ ] Windows 控制台输出非 ASCII 时已改用 ASCII/`backslashreplace` 或 UTF-8 模式，未把编码错误当作文件损坏。

## 已验证案例（2026-10-25）

来源会话 11bb73ef 在创建 `validation-navigateur-par-repli` 时，目标目录先不存在，确认后已被并发进程创建为 7,971 字节；随后文件依次变为 11,950、7,036、7,410、7,548、7,670、7,969 字节。更新阶段在确认双采样稳定后，只用 2 次 `Edit` 修改 `SKILL.md`、2 次同步中文参考，`skill-file-qa` 报告 9 PASS / 0 FAIL / 0 WARN，最终文件为 8,572 字节、中文参考 6,264 字节。之后该 Skill 又被并发改写，说明这些数字只是历史证据，不能当作当前状态。

补充案例（来源会话 273649ee，2026-10-25）：`validation-navigateur-par-repli` 在 18:43–19:25 被多个会话反复改写。19:02 版本为 `SKILL.md` 8,572 字节（SHA-256 `71b0b137…`）+ 其 references 目录下的 zh-CN.md 6,264 字节（`ab62253e…`）；代理先把两者备份到 `.qoder/tmp/.../validation-skill-backup/20261025T180849Z/`，再写入双语版 17,680 字节，`check_bilingual_parity.py` 报告 4 PASS，`validate_skill.py` 报告 9 PASS。随后文件又变为 18,747 → 22,207 字节；代理多次等待连续 3 次相同哈希，在 22,207 字节版本（`cf7816d8…`）上对等校验 4 PASS、`validate_skill.py` 10 PASS。期间对等校验曾因中文侧尚未同步而失败，等待并发写入补齐后重跑通过；环境中 `qoder` CLI 不存在，无法执行 `/skills reload`，改用直接调用 Skill 验证注入，列表刷新需重启会话。以上数字是历史证据，不表示当前状态。

同一环境中 `python` 为 Microsoft Store 存根，`py -3` 为可用的 Python 3.14.7。来源会话没有用户对工具用法的纠正；等待稳定、保留并发新增内容、写入后复核哈希，都是从并发与环境约束中验证出的做法。

补充案例（来源会话 88ac4133，2026-10-26）：更新 `skill-doc-translation-parity` 时，7 次 `Edit` 修改其 `check_translation_parity.py`，修复 4 个误通过/误报缺口。验证顺序为：`ast` 语法通过 → 两对真实译本各 8 PASS / 0 FAIL、`EXIT=0` → 21 个独立反例 `SUMMARY: 21/21 passed`（含波浪线围栏、四反引号、无前导竖线表格、清单状态翻转，退出码 0/1/2 全部按契约断言）→ `find` 复核无 `__pycache__` → `skill-file-qa` 9 PASS / 0 FAIL / 0 WARN。期间一次临时 Bash 用 Python 打印中文触发 `UnicodeEncodeError`（`cp1252.py`），属控制台编码问题，文件本身完好；这是 `skill-file-qa` 与对等校验都不覆盖的环节。以上数字是历史证据，不表示当前状态。

补充案例（来源会话 5d29d989，2026-10-26）：更新 `extraire-preuves-session-qoder` 时，10:18:32Z 的 `py -3 -m py_compile scripts/extract_session_evidence.py` 通过，并在 `scripts` 下的 `__pycache__` 生成 `extract_session_evidence.cpython-314.pyc`。10:19:32Z 的 `validate_skill.py` 报告 `Files (3)`（含该 `.pyc`）、`Code blocks: python=0 js=0 skipped=2`、9 PASS / 0 FAIL / 0 WARN、`RESULT PASS`：`.pyc` 未导致失败，脚本语法也未被检查。10:19:46Z 删除 `__pycache__` 后重跑，文件清单回到 `Files (2)`，同为 9 PASS。最终 `SKILL.md` 为 14,910 字节（`f64d60ae…`）、脚本为 23,988 字节（`4bba88b3…`）。该会话两条人类消息为任务说明与「确认，执行写入。」，无用户纠正；先 `py_compile`、再清理并复验是代理自行改道。以上数字是历史证据，不表示当前状态。

补充案例（来源会话 72fc9467，2026-10-26）：为本 Skill 增加脚本行为回归与 cp1252 条目时，`skill-file-qa` 两轮报 `FAIL local reference not found`：首轮为 'scripts/' 与 'scripts/check_translation_parity.py'（代理新增文字），第二轮为 'scripts/' 与 'scripts/__pycache__/'（并发新增的 5.2、5.4 与故障表文字）。修正 3 处以上措辞后最终 `PASS local references: 0 checked`、9 PASS / 0 FAIL / 0 WARN。文件期间从 20,734 → 23,176 → 24,060 → 24,102 字节，且一次 `old_string` 未命中，说明必须等稳定后重读并重跑。Skill 目录之外的临时探针确认：裸目录、scripts/foo.py、references/guide.md、assets/logo.png 均 FAIL；以 `$`、`/`、`~` 开头或含 `*`、空格的 token，「`scripts` 目录」写法均不触发；围栏代码块内的反引号 token 仍会被扫描，只有裸路径不受影响。以上数字是历史证据，不表示当前状态。

补充案例（来源会话 a4ed000e，2026-10-26）：为 `verifier-effets-de-bord-verification-lecture-seule` 增加回归自检时，首次 70 项中 1 项因 `--max-exemples 2` 截断 `module_004.py` 而误判，修正断言后 70/70 连续两次通过；A/B 副本回退 `TS_KEYS`/`FILE_KEYS` 后为 0 签名 / 100 无签名且不报挤掉，当前脚本为 100 / 0 并正确报 5 条被挤出（A/B 11/11 通过）；真实数据发现 ledger 的 `blocs` 100 条全部无签名（`timestamp_utc` 不在别名中，`nb_blocs=350`），补别名与 10 项 ledger 断言后 80/80 连续两次通过；文档中两处 `TOTAL=70` 同步为 80；QA 为 9 PASS / 0 FAIL / 0 WARN、`Files (5)`、body 173 行、`SKILL.md` `9130744f…` 校验期间未变。多行常量的旧正则在会话快照中没有保留报错原文，但机制已实测：`^TS_KEYS\s*=.*$` 命中 1 次且哈希变化后仍报 `IndentationError`，整元组正则 `ast.parse` 通过。以上数字是历史证据，不表示当前状态。
