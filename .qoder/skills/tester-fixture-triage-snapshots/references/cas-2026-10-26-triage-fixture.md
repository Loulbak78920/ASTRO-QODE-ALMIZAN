# 案例：plan/pre 双快照分流夹具

## 1. 来源

- 会话：`e506f79c-3510-4634-a1da-934252ade330`，标题“更新审计回收技能”。
- 读取：16 条消息、7 个用户回合、`runtimeState=cold`、`revision=0`、`hasMoreBefore=false`。
- 原始 JSONL：`C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\e506f79c-3510-4634-a1da-934252ade330.jsonl`，387 行。
- 相关工具输出：消息 9 的第 11、12、15、17 项；对应 JSONL 行 203–246（0 基）。
- 该会话更新的 `audit-recouvrement-skills-avant-creation` 当前已不在磁盘。本文件只保留夹具证据，不把它当作可解析的交叉引用。

## 2. 初始夹具的关键片段

快照比较：

```bash
snap() {
  [ -d "$1" ] || return 0
  find "$1" -mindepth 2 -maxdepth 2 -name SKILL.md -print0 |
    while IFS= read -r -d '' f; do
      printf '%s|%s|%s\n' "$(dirname "$f")" "$(stat -c '%s' "$f")" "$(sha256sum "$f" | cut -d' ' -f1)"
    done | sort
}
state_of() {
  pl=$(snap "$2" | grep "/$1|" || true)
  pr=$(snap "$3" | grep "/$1|" || true)
  # ... CREATE / APPEARED / VANISHED / UPDATE / CHANGED
}
```

清理断言：

```bash
rm -rf "$WORK"; rm -f "$HOME/.qoder/tmp/selftest-verify-20261026.sh"
clean=yes
[ -e "$WORK" ] && clean=no
[ -e "$HOME/.qoder/tmp/selftest-verify-20261026.sh" ] && clean=no
[ "$(ls -A "$TARGET" | sort | tr '\n' ' ')" = "SKILL.md " ] || clean=no
```

末尾门禁：

```bash
[ "$FAIL" = 0 ] && [ "$PASS" = 16 ]
```

## 3. 三轮实跑

### 3.1 首轮：15 PASS / 2 FAIL / rc=1

```text
FAIL state UPDATE | expected=[UPDATE] actual=[ADOPT_RACE_CHANGED]
PASS state ADOPT_RACE_APPEARED
PASS state ADOPT_RACE_CHANGED
PASS state CREATE
...
FAIL fixture and script removed, target clean | expected=[yes] actual=[no]

RESULT PASS=15 FAIL=2 TOTAL=17
SCRIPT_RC=1
```

### 3.2 诊断

```text
total 52
drwxr-xr-x 1 Administrateur 197121 0 ... .
drwxr-xr-x 1 Administrateur 197121 0 ... ..
drwxr-xr-x 1 Administrateur 197121 0 ... .git
-rw-r--r-- 1 Administrateur 197121 26064 ... SKILL.md
---work---
ls: cannot access '/c/Users/Administrateur/.qoder/tmp/selftest-verify': No such file or directory
---ScriptExists---
-rwxr-xr-x ... /c/Users/Administrateur/.qoder/tmp/selftest-verify-20261026.sh
```

目标目录是 Git 仓库，`ls -A` 返回 `.git SKILL.md `，与期望的 `SKILL.md ` 不相等。脚本文件仍在，是因为首轮运行前已移除“脚本自删”分支；它不是洁净失败的原因，随后由调用方删除。

### 3.3 修复后第二轮：17/17 但 rc=1

```text
PASS state UPDATE
...
PASS fixture and script removed, target clean

RESULT PASS=17 FAIL=0 TOTAL=17
SCRIPT_RC=1
```

原因：断言已从 16 条增到 17 条，末尾仍写 `[ "$PASS" = 16 ]`。

### 3.4 修正计数后第三轮：17/17、rc=0

```text
PASS state UPDATE
...
PASS fixture and script removed, target clean

RESULT PASS=17 FAIL=0 TOTAL=17
SCRIPT_RC=0
```

清理与目标指纹：

```text
ABSENT /c/Users/Administrateur/.qoder/tmp/overlap-audit.9h95nnfp
ABSENT /c/Users/Administrateur/.qoder/tmp/selftest-verify-20261026.sh
ABSENT /c/Users/Administrateur/.qoder/tmp/selftest-verify
---target---
989e62c29d67b91e545ff6ee27a9e049969f3e6cf167fb7cebf3b30c6b335591 */c/.../SKILL.md
size=26064 mtime=2026-10-26 15:37:38.314697100 +0100
```

## 4. 根因与修复

### 4.1 同内容异根被判为 `ADOPT_RACE_CHANGED`

初始快照行包含绝对目录：

```text
C:\...\triage-fixture\plan\alpha|123|abc...
C:\...\triage-fixture\pre\alpha|123|abc...
```

`grep "/alpha|"` 选中了两行，但两行整体不相等，于是落到 `ADOPT_RACE_CHANGED`。内容、size、SHA 都相同，差异只在绝对根。

修复：比较前剥离第一个 `|` 之前的路径字段。

```bash
pl=$(snap "$2" | grep "/$1|" | sed 's|^[^|]*||' || true)
pr=$(snap "$3" | grep "/$1|" | sed 's|^[^|]*||' || true)
```

新 Skill 采用更强的写法：`snap` 直接输出相对路径作为键，`state_of` 用 `awk -F'|' '$1 == k'` 精确取行，既不含绝对根，也不做子串匹配。

### 4.2 `.git` 被当作残留

修复：只检查顶层普通文件，忽略目录。

```bash
[ "$(find "$TARGET" -maxdepth 1 -type f -printf '%f\n' | sort | tr '\n' ' ')" = "SKILL.md " ] || clean=no
```

新 Skill 把这条抽成 `files_at_top()`，并用一个含 `.git/` 的合成目标和一个含 `extra.txt` 的合成目标分别验证“忽略元数据”和“发现真实残留”。

### 4.3 全绿但 `rc=1`

修复：

```diff
-[ "$FAIL" = 0 ] && [ "$PASS" = 16 ]
+[ "$FAIL" = 0 ] && [ "$PASS" = 17 ]
```

这只是把第二个硬编码数字改对，仍是两个事实源。新 Skill 要求只在开头计算一次 `EXPECTED`，末尾同时检查 `PASS`、`TOTAL`、`FAIL`，并在失败时打印 `GATE FAIL` 与全部计数。

## 5. 证据分类

| 结论 | 分类 | 依据 |
|---|---|---|
| 首轮 15/2、第二轮 17/17 但 rc=1、第三轮 17/17 rc=0 | 已核实 | 来源工具输出原文 |
| 目标含 `.git`，`ls -A` 导致洁净失败 | 已核实 | 诊断目录列表 + 修复后通过 |
| 绝对根路径导致 `UPDATE` 被判 `CHANGED` | 由修复前后对照支持 | 剥离路径后同一断言通过；来源未做独立单变量 A/B |
| mtime 单独变化不应判 `CHANGED` | 来源未测 | 新脚本以“同内容异 mtime”断言验证 |
| 同 size 异 SHA 应判 `CHANGED` | 来源未测 | 新脚本以“同 size 异内容”断言验证 |
| 校验器五形态 | 来源已测，但不在本 Skill 范围 | 归 `valider-harnais-fixture-windows-msys`、`skill-file-qa` |

## 6. 边界

- 来源夹具的 17 项断言包含 7 项校验器形态检查；本 Skill 不复制这些检查，只固化双快照分流、Git 洁净、计数门禁和目标只读。
- 来源脚本用 `%y`（人类可读 mtime）比较目标元数据；新脚本用 `%Y`（epoch 秒），减少格式差异。该改动由新脚本实测。
- 来源的目标 Skill 已不在磁盘；不要把 `audit-recouvrement-skills-avant-creation` 写成当前可解析引用。
- 未验证：真实并发写入、生产目标、非 Git Bash 环境的 `find -printf`/`stat -c` 可移植性。

## 7. 本 Skill 写入时的复跑

见下方“复跑结果”一节；只有实际执行并记录的结果才算已验证。

### 复跑结果

**时间与环境**：2026-10-27，Windows 10.0.26200，Git Bash；脚本只用 bash 与 coreutils（`find`、`stat`、`sha256sum`、`mktemp`）。

**语法**：`bash -n scripts/selftest_triage_snapshot.sh` → rc 0。

**正向三轮**：

```text
RUN 1   RESULT PASS=12 FAIL=0 TOTAL=12 EXPECTED=12   GATE PASS   rc=0
RUN 2   RESULT PASS=12 FAIL=0 TOTAL=12 EXPECTED=12   GATE PASS   rc=0
TARGET  RESULT PASS=14 FAIL=0 TOTAL=14 EXPECTED=14   GATE PASS   rc=0
```

`TARGET` 使用本 Skill 目录自身；`target.sha_unchanged` 与 `target.size_mtime_unchanged` 均通过。

**变异测试**（临时副本，运行后删除）：

| 变异 | 实际输出 | 结论 |
|---|---|---|
| `EXPECTED=12` 改为 13 | 12 行全 PASS，`RESULT PASS=12 FAIL=0 TOTAL=12 EXPECTED=13`，`GATE FAIL`，rc=1 | 计数门禁非空转 |
| `snap` 的键改为绝对路径 | 6 项 FAIL（`UPDATE`/`APPEARED`/`CHANGED`/`VANISHED` 均变为 `CREATE`），`GATE FAIL`，rc=1 | 异根断言能拒收绝对键。本 Skill 用精确键匹配，症状是 `CREATE`；来源的 grep 写法症状是 `ADOPT_RACE_CHANGED` |
| `files_at_top` 改为 `ls -A` | `clean.git_metadata_ignored` FAIL，`actual=[.git SKILL.md ]`，`GATE FAIL`，rc=1 | 复现来源的 `.git` 误判 |

**残留**：三轮正向与三轮变异产生的 `triage-fixture.*` 均被脚本删除；三个临时变异脚本已删除并逐项确认不存在。

**指纹**（本节写入前）：

- `SKILL.md`：13 313 B，SHA-256 `9cdcac5a57d4660f3069bc69ca35aa9005370ccb9069716b9a3bb547418b4280`。
- `scripts/selftest_triage_snapshot.sh`：5 962 B，SHA-256 `9026e86d66eace6787381f18010f67aee71529c9b8c2da2765d5a4a547919623`。

**边界**：以上只覆盖本机 Git Bash；未验证真实并发、生产目标、非 Git Bash 环境的 `find -printf`/`stat -c` 可移植性。
