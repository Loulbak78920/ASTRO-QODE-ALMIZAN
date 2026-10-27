---
name: harden-skill-argument-substitution
description: "当 Skill 的围栏示例或说明文字含数字位置变量、且该 Skill 可能被带参数调用时，先证明磁盘与 HEAD 未被改写，再全文扫描数字位置变量（含散文、表格与注释），把代码改用具名变量、说明改用 `$N`（N=1–9）指代，随后从磁盘逐字抽取片段，在临时夹具中按目标 Skill 记录的真实快照格式复跑，修正 `name|` 与 `name | size` 一类空格/格式差异，最后跑 `skill-file-qa` 并记录哈希；提交与推送交给 `commit-skill-work`，若另一会话已提交则核对 HEAD OID、blob SHA 与 `ls-remote` 后报告，不创建重复提交。用于带参数调用后注入正文显示实参、示例片段复跑全失败、说明文字再次触发替换、提交时发现 HEAD 已前进。中文触发：位置变量、参数替换、注入层失真、具名变量、夹具格式不匹配；English: positional argument substitution, injected body distortion, named variables, fenced example hardening; Français: substitution d'arguments, variables nommées, extrait injecté."
---

# 加固 Skill 的参数替换风险

## 目标与边界

当 Skill 可能被带参数调用时，运行时注入层会把正文中的数字位置变量替换成实参文本；磁盘和 HEAD 不变，但围栏示例与说明文字会失真，照着注入文本复跑会得到错误判据。本 Skill 负责把示例与说明改成不会被替换的写法，并用临时夹具证明片段语义未变。

- 只改目标 Skill 的 Markdown 正文与相关说明；不改脚本行为，不改被引用 Skill。
- 不替代以下属主：
  - 覆盖审计：使用当前已安装的覆盖审计 Skill；audit-recouvrement-skills-avant-creation 于 2026-10-26 17:07 +01:00 仍存在（34,040 B），17:09 核查时已不在用户级 skills 根，原因未核实；本 Skill 不恢复、不移动、不修改它
  - 并发写入与稳定性采样：`skill-update-concurrency-safe`
  - HEAD/工作区对账：`verify-skill-git-head-vs-worktree`
  - 记录型夹具重放：`replay-skill-reference-fixtures`
  - 结构验收：`skill-file-qa`
  - 提交、推送与并发提交：`commit-skill-work`
  - 目标在写入期间突然出现：`adopt-concurrent-duplicate-skill`
- 本 Skill 不拥有“重复提交”规则；遇到已提交状态只按 `commit-skill-work` 核对并报告。

## 不可协商规则

1. **先证版本，再改文字。** 读取目标 `SKILL.md`，记录 size、mtime、SHA-256；有 Git 时同时记录 `HEAD:<path>` OID 与 `git hash-object --path`。工作区与 HEAD 不一致时先停，按 `skill-update-concurrency-safe` 或 `verify-skill-git-head-vs-worktree` 处理。
2. **全文扫描，不只扫代码块。** 正文、表格、注释、说明文字都要扫；数字位置变量出现在散文里同样会被替换。
3. **代码用名，说明用 `$N`。** 围栏示例改用 `skill_name`、`plan_root`、`pre_root` 等具名变量；说明需要指代第 N 个参数时写 `$N`（N=1–9），不要写数字形式。
4. **不从注入正文抄片段。** 从磁盘按行号抽取，记录起止行与目标文件 SHA-256；注入正文只作症状证据，不作复跑输入。
5. **夹具按真实格式。** 目标 Skill 记录的快照格式是什么，夹具就输出什么；`name|size` 与 `name | size` 的差异会让 grep 全失败。
6. **正反两例都要跑。** 相同指纹必须判等；改动 pre 必须判不等；清理后目录必须不存在。只跑正例不算验证。
7. **失败先分类。** 先区分“片段逻辑错”与“夹具格式/断言错”；不得为让夹具通过而放宽断言。
8. **写后重读并扫描。** 位置变量扫描必须 0 命中；再跑 `skill-file-qa`，记录最终 size、mtime、SHA-256。
9. **提交与推送交给 `commit-skill-work`。** 若 HEAD 已前进或 `git commit` 返回 `nothing to commit`，按该 Skill 的并发提交分支核对，不创建空提交、不 amend、不 force push。
10. **未跑不宣称。** 没读过的文件、没跑过的夹具、没核对的远端，分别标“未读取 / 未运行 / 未核对”。

## 流程

### 0. 建立基线

```bash
TARGET="$HOME/.qoder/skills/<skill-name>"
git -C "$TARGET" rev-parse --show-toplevel 2>/dev/null || true
sha256sum "$TARGET/SKILL.md"
stat -c '%s %y' "$TARGET/SKILL.md"
git -C "$TARGET" rev-parse "HEAD:SKILL.md" 2>/dev/null || true
git -C "$TARGET" hash-object --path=SKILL.md "$TARGET/SKILL.md" 2>/dev/null || true
git -C "$TARGET" status --short
```

- 两次采样间隔至少 2 秒，一致才继续。
- `core.autocrlf=true` 时比较 OID，不要用 SHA-256 直接比工作区与 blob。
- 无 Git 或未提交：只记录文件指纹，并在报告中注明“无 HEAD 基线”。

### 1. 全文扫描

```bash
grep -nE '\$[1-9]|\$\{[1-9]\}' "$TARGET/SKILL.md" || true
```

- 同时扫描目标 Skill 的其他 Markdown、注释与帮助文本（如果本次改动涉及）。
- 输出行号后逐条读上下文；不要只替换围栏块。
- 0 命中不等于安全：检查 `eval`、`xargs`、`getopts` 等间接写法，必要时人工复核。

### 2. 改写成具名变量

下面是从目标 Skill 抽取的片段形态，`snap` 由目标 Skill 或夹具定义：

```bash
skill_name="example-skill"  # 换成待比较的 Skill 目录名
plan_root="$snap_dir/plan"
pre_root="$snap_dir/pre"
snap_root="$plan_root"
pl=$(snap | grep -E "/$skill_name[[:space:]]*[|]" | sed 's|^[^|]*||' || true)
snap_root="$pre_root"
pr=$(snap | grep -E "/$skill_name[[:space:]]*[|]" | sed 's|^[^|]*||' || true)
```

- 说明文字统一写 `$N`（N=1–9），不要写数字形式；这是本 Skill 最容易再次踩中的坑。
- 辅助函数也不要用位置参数；用 `snap_root` 这类具名全局。若目标片段必须原样调用 `snap "$root"`，把带位置参数的 `snap` 定义放进 `~/.qoder/tmp` 的临时脚本；临时脚本不在 Skill 正文中，不受注入层替换。不要把带位置参数的函数定义写回 `SKILL.md`。
- 改完立刻重跑第 1 步扫描，要求 0 命中。

### 3. 临时夹具复跑

在 `~/.qoder/tmp` 建一次性夹具，按目标 Skill 记录的真实格式输出快照。下面是本次验证过的格式 `dirname | size | mtime | sha`：

```bash
tmp="$(mktemp -d "$HOME/.qoder/tmp/arg-subst.XXXXXX")" || exit 1
fail=0
mkdir -p "$tmp/plan/example-skill" "$tmp/pre/example-skill" || exit 1
printf '%s\n' 'name: example-skill' > "$tmp/plan/example-skill/SKILL.md" || fail=1
cp -p "$tmp/plan/example-skill/SKILL.md" "$tmp/pre/example-skill/SKILL.md" || fail=1
touch -r "$tmp/plan/example-skill/SKILL.md" "$tmp/pre/example-skill/SKILL.md" || fail=1

snap_root=""
snap() {
  find "$snap_root" -mindepth 2 -maxdepth 2 -name SKILL.md -print0 |
    while IFS= read -r -d '' file; do
      printf '%s | %s | %s | %s\n' \
        "$(dirname "$file")" \
        "$(stat -c '%s' "$file")" \
        "$(stat -c '%y' "$file")" \
        "$(sha256sum "$file" | cut -d' ' -f1)"
    done | sort
}

skill_name="example-skill"
plan_root="$tmp/plan"
pre_root="$tmp/pre"
snap_root="$plan_root"
pl=$(snap | grep -E "/$skill_name[[:space:]]*[|]" | sed 's|^[^|]*||' || true)
snap_root="$pre_root"
pr=$(snap | grep -E "/$skill_name[[:space:]]*[|]" | sed 's|^[^|]*||' || true)

if [ -n "$pl" ] && [ "$pl" = "$pr" ]; then
  echo "CASE1 PASS identical"
else
  echo "CASE1 FAIL"
  fail=1
fi

printf 'mutation\n' >> "$pre_root/$skill_name/SKILL.md" || fail=1
snap_root="$pre_root"
pr2=$(snap | grep -E "/$skill_name[[:space:]]*[|]" | sed 's|^[^|]*||' || true)
if [ -n "$pl" ] && [ "$pl" != "$pr2" ]; then
  echo "CASE2 PASS mutation detected"
else
  echo "CASE2 FAIL"
  fail=1
fi

rm -rf "$tmp"
if [ ! -e "$tmp" ]; then
  echo "CLEANUP PASS absent"
else
  echo "CLEANUP FAIL present"
  fail=1
fi
echo "FIXTURE_RC=$fail"
exit "$fail"
```

- 脚本退出码与 `FIXTURE_RC` 一致；验收以退出码 0 为准。
- `cp -p` 加 `touch -r` 保证 plan 与 pre 的 size、mtime、SHA 相同；mutation 后必须三项都变。
- 只删除本次 `mktemp` 目录；不碰目标 Skill。
- 目标 Skill 的格式不是本次格式时，按它记录的格式重建夹具；先复现失败，再改断言或片段。

### 3.1 从磁盘抽取被改写的片段

记录起止行与目标文件 SHA-256，再抽取；不要从注入正文复制：

```bash
start="<起始行>"; end="<结束行>"
snippet="$(mktemp "$HOME/.qoder/tmp/arg-subst-snippet.XXXXXX")" || exit 1
sed -n "${start},${end}p" "$TARGET/SKILL.md" > "$snippet"
sha256sum "$TARGET/SKILL.md"
```

在夹具中先定义片段依赖（`snap`、`snap_dir` 等），再 `source "$snippet"`；片段不能独立运行时，不要用 `bash "$snippet"` 代替。验证完成后只删除该文件：

```bash
rm -f "$snippet"
```

### 4. 写后验收

```bash
grep -nE '\$[1-9]|\$\{[1-9]\}' "$TARGET/SKILL.md" || true
sha256sum "$TARGET/SKILL.md"
stat -c '%s %y' "$TARGET/SKILL.md"
QA_DIR="$HOME/.qoder/skills/skill-file-qa"
py -3 "$QA_DIR/scripts/validate_skill.py" "$TARGET" --workspace "<workspace-root>" --stable-seconds 2 --stability-timeout 30
```

- 位置变量扫描 0 命中。
- 用位置参数运行校验器，要求 `RESULT PASS`、rc=0、`Files (N)` 与预期一致、`skill references: N checked` 精确匹配；`0 found` 不算证据。
- 回读改动段落，确认说明、错误表、清单与正文一致。
- 记录最终 size、mtime、SHA-256。

### 5. 提交与推送（委派）

- 用户要求提交或推送时，加载并遵循 `commit-skill-work`。
- 若发现 HEAD 已前进、`git commit` 返回 `nothing to commit`，或工作区已干净：按该 Skill 的并发提交分支核对 `HEAD:<path>` OID、`hash-object --path`、唯一标记与 `ls-remote`；包含关系成立就报告现有 commit，不创建重复提交、不 amend、不 force push。
- 本次已验证案例：最终写入 `2b86cf43…` 后约一分钟，另一会话创建 `a010e3a` 并推送；`HEAD:SKILL.md` OID `df08065…` 与 `hash-object --path` 相等，`ls-remote` 与本地 HEAD 相等，故未重复提交。

## 错误表

| 症状 | 根因 | 动作 |
|---|---|---|
| 改完说明文字后扫描又出现命中 | 说明里写了数字位置变量 | 说明统一用 `$N`（N=1–9）；重跑扫描 |
| 夹具 `CASE1 FAIL pl= pr=`，正反例都空 | `grep "/$skill_name|"` 不匹配 `name | size` 格式 | 改 `grep -E "/$skill_name[[:space:]]*[|]"`；先复现再修 |
| 夹具全 PASS 但 `FIXTURE_RC=1` | 末尾 `fail` 未同步，或脚本未用 `fail` 退出 | 以退出码 0 验收；每条断言同步 `fail`，末尾 `exit "$fail"` |
| 注入正文显示实参，磁盘/HEAD 哈希未变 | 注入层替换，不是文件损坏 | 以磁盘原文复跑；不要按注入文本改文件 |
| 提交时 `nothing to commit` 或 HEAD 已前进 | 另一会话已提交或已推送 | 按 `commit-skill-work` 核对 OID、blob、marker、`ls-remote`；不重复提交 |
| `core.autocrlf=true` 下 SHA-256 不等 | 工作区 CRLF 与 blob LF 不同 | 比较 OID；记录行尾归一化 |
| 辅助函数内部仍有数字位置变量 | 只改了调用处，没改函数体 | 函数改用具名全局或临时脚本；全文重扫 |
| 只跑正例就宣称通过 | 未验证变异检测 | 必须跑 mutation 反例与清理断言 |

## 完成清单

- [ ] 目标文件写入前后均有 size、mtime、SHA-256；有 Git 时记录 HEAD OID。
- [ ] 全文（含散文、表格、注释）扫描数字位置变量 0 命中。
- [ ] 围栏示例只用具名变量；说明只用 `$N`（N=1–9）。
- [ ] 辅助函数与 `eval`、`xargs` 等间接写法已人工复核。
- [ ] 从磁盘按行号抽取片段，未从注入正文复制。
- [ ] 夹具按目标真实格式输出；正例、变异反例、清理三项均实跑通过，`FIXTURE_RC=0` 且脚本退出码 0。
- [ ] `skill-file-qa` 位置参数运行，`RESULT PASS`、rc=0、计数精确匹配。
- [ ] 最终 size、mtime、SHA-256 已记录。
- [ ] 提交与推送已委派 `commit-skill-work`；若已存在提交，已核对 OID、blob、`ls-remote`，未重复提交。
- [ ] 报告区分“已读取 / 已运行 / 仅来源报告 / 未验证”。

## 来源与证据

2026-10-26 会话 `7f6f22fe-9970-4d88-ae22-434c9ea38ac7`（读取时 revision 25、hasMoreBefore=false、runtimeState=ready；3 个用户回合：初始方案、“按此方案修改”、“提交并推送这些修改”）。该会话更新一个覆盖审计 Skill 的 §5（audit-recouvrement-skills-avant-creation；2026-10-26 17:07 +01:00 仍存在 34,040 B，17:09 核查时已不在用户级 skills 根，原因未核实；未恢复、未移动、未修改）：

- 第一次写入后，说明文字本身使用了数字位置变量，触发同一注入替换；随后改为 `$N`（N=1–9）。
- 从磁盘抽取片段首次实跑：`CASE1 FAIL pl= pr=`、`CASE2 FAIL`、`PASS=0 FAIL=2`、`FIXTURE_RC=1`；原因是 `grep "/$skill_name|"` 不匹配文档格式 `name | size`。改为 `grep -E "/$skill_name[[:space:]]*[|]"` 后 `CASE1 PASS`、`CASE2 PASS`、`PASS=2 FAIL=0`、`CLEANUP PASS absent`、`FIXTURE_RC=0`。
- 来源会话报告（本轮未复跑；该文件于 17:09 前从用户级 skills 根缺失）：最终文件 34,040 B / 368 行 / SHA-256 `2b86cf43…`；`skill-file-qa` 9 PASS / 0 FAIL / 0 WARN，13 checked，正文 364 行，description 1,017 字符，EXIT 0。本轮仅在 17:07 复核了 34,040 B，未复核行数与 QA 计数。
- 用户要求提交并推送时，发现另一会话已于 16:57:20 创建 `a010e3a` 并推送；工作区 SHA-256 `2b86cf43…` 等于 HEAD blob，`HEAD:SKILL.md` OID `df08065…` 等于 `hash-object --path`，`ls-remote` 等于本地 HEAD；未创建重复提交。

注入层替换的最初观察来自更早会话 `b37d7404` 的助手报告（提交 `c46cd75`），当时未保留原始注入正文快照；本 Skill 只把该观察作为机制证据，实际验证以磁盘、HEAD 与本次夹具为准。`$N` 的反斜杠转义写法未在本机验证，故本 Skill 只推荐具名变量与 `$N` 叙述，不宣称转义可用。
