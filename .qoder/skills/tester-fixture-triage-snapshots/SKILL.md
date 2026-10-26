---
name: tester-fixture-triage-snapshots
description: "编写、运行或排查 plan/pre 双快照分流夹具：快照键用相对目录路径加 size 与 SHA-256，正确判定 UPDATE／ADOPT_RACE_APPEARED／ADOPT_RACE_CHANGED／CREATE／VANISHED；键中不得含绝对根路径或 mtime，否则同内容异根或仅时间戳变化会被误判 CHANGED；Git 仓库的洁净断言用 find -maxdepth 1 -type f 或排除 .git，不用 ls -A 把 .git 当残留；末尾门禁以单一 EXPECTED 同时约束 PASS、TOTAL 与 FAIL 并要求 rc=0，避免 17/17 全绿却因写死 16 返回 1；同时断言真实目标前后 SHA、size、mtime 不变，夹具删除后确认不存在。用于双快照夹具实现、同内容异根误判、.git 被当残留、全 PASS 但 rc=1、断言计数漂移、plan/pre 分流回归。中文触发：双快照、分流夹具、同内容异根、残留误判、断言计数、全绿 rc=1；English: dual snapshot fixture, triage fixture, false CHANGED, git metadata residue, expected assertion count, green but exit 1; Français: fixture de double instantané, faux CHANGED, résidu .git, compteur d'assertions, PASS mais code 1."
---

# 双快照分流夹具（plan/pre）

## 目标与边界

本 Skill 规定如何编写、运行和排查一个可丢弃的 plan/pre 双快照分流夹具：把两次目录快照归约为 `UPDATE`、`ADOPT_RACE_APPEARED`、`ADOPT_RACE_CHANGED`、`CREATE`，并用 `VANISHED` 守住目标消失。重点不是四态的定义，而是让夹具本身不产生假失败：同内容异根不得误判、Git 元数据不得当残留、全绿时计数门禁不得仍返回 1。

本 Skill 不替代：

- 通用夹具验收门禁（编译、双跑、负向控制、残留、QA）：`valider-harnais-fixture-windows-msys`
- 接管决策与写入者归因：`adopt-concurrent-duplicate-skill`
- 真实并发写入与稳定性采样：`skill-update-concurrency-safe`
- 写后静态验收：`skill-file-qa`

四态是本 Skill 的夹具契约；接管决策仍以 `adopt-concurrent-duplicate-skill` 为准，不在此复制其矩阵与冷却步骤。

## 何时使用

- 编写或修改 plan/pre 快照分类夹具。
- `UPDATE` 被误判为 `ADOPT_RACE_CHANGED`，尤其是同内容放在两个不同根下。
- 目标目录是 Git 仓库，洁净断言把 `.git` 当残留。
- 17/17 全绿但脚本 `rc=1`，或断言计数与末尾门禁不一致。
- 需要把真实目标的前后 SHA、size、mtime 固定为验收条件。

不适用：只需要四态的语义决策；只需要通用夹具验收；需要测试真实并发写入或生产目标。

## 不可协商规则

1. **夹具可丢弃。** 只写 `$HOME/.qoder/tmp/triage-fixture.XXXXXX`；不写 Skill 目录、不写真实目标；删除后确认不存在。
2. **键不含根与时间。** 快照键 = 相对目录路径 + size + SHA-256。不得含绝对根路径；mtime 只记录，不参与相等判断。
3. **场景隔离。** 每个场景独立的 plan/pre 根；键按精确字段匹配，不用子串 `grep`。
4. **UPDATE 必须异根。** `UPDATE` 场景要把同内容放在两个不同的绝对根下；否则测不出路径污染。
5. **四态加守卫。** `UPDATE`、`ADOPT_RACE_APPEARED`、`ADOPT_RACE_CHANGED`、`CREATE` 全覆盖；`VANISHED` 是守卫，不属于四态。
6. **洁净断言认识 Git。** 用 `find -maxdepth 1 -type f`，或排除 `.git` 后检查；禁止只用 `ls -A`。允许的顶层文件清单要显式写出（可能含 `.gitattributes`、`.gitignore`）。
7. **预期数单一来源。** 脚本开头算一次 `EXPECTED`；末尾同时检查 `PASS == EXPECTED`、`TOTAL == EXPECTED`、`FAIL == 0`，失败时打印全部计数并 `exit 1`。
8. **目标只读。** 真实目标前后 SHA、size、mtime 必须不变；用 `sha256sum` 与 `stat -c '%s|%Y'`。
9. **不自删脚本。** 不在 Windows 上让运行中的脚本删除自身；夹具由脚本删除，脚本本身由调用方管理。
10. **收集后门禁。** 用 `set -u`，不用 `set -e`；断言失败要继续收集，最后统一门禁。
11. **报告带计数。** 不能只列 PASS 行；必须给 `PASS/FAIL/TOTAL/EXPECTED` 与 `rc`。

## 快照与分流实现

### 1. 目录布局

```text
triage-fixture.XXXXXX/
├── update_diff/
│   ├── plan/u1/SKILL.md
│   └── pre/u1/SKILL.md
├── update_mtime/
│   ├── plan/u2/SKILL.md
│   └── pre/u2/SKILL.md
├── appeared/
│   ├── plan/              # 空
│   └── pre/a1/SKILL.md
├── changed/
│   ├── plan/c1/SKILL.md
│   └── pre/c1/SKILL.md
├── create/
│   ├── plan/              # 空
│   └── pre/               # 空
├── vanished/
│   ├── plan/v1/SKILL.md
│   └── pre/               # 空
├── same_size/
│   ├── plan/s1/SKILL.md
│   └── pre/s1/SKILL.md
├── clean-target/
│   ├── .git/              # 目录，不是残留
│   └── SKILL.md
└── dirty-target/
    ├── SKILL.md
    └── extra.txt
```

### 2. 快照函数

```bash
snap() {
  local root=${1%/}
  [ -d "$root" ] || return 0
  find "$root" -mindepth 2 -maxdepth 2 -name SKILL.md -print0 |
    while IFS= read -r -d '' f; do
      rel=${f#"$root"/}
      rel=${rel%/SKILL.md}
      printf '%s|%s|%s\n' "$rel" \
        "$(stat -c '%s' "$f")" \
        "$(sha256sum "$f" | cut -d' ' -f1)"
    done | LC_ALL=C sort
}
```

- `rel` 是相对路径，不含根；同内容异根得到同一行。
- 不写 mtime；时间戳变化不等于内容变化。需要审计时另存一份带 `%Y` 的报告，但不进入比较键。
- 同一根内相对路径唯一。若同一键出现多行，先修夹具布局，不要继续分类。

### 3. 分流函数

```bash
state_of() { # key plan_root pre_root
  local key=$1 pl pr
  pl=$(snap "$2" | awk -F'|' -v k="$key" '$1 == k')
  pr=$(snap "$3" | awk -F'|' -v k="$key" '$1 == k')
  if [ -z "$pl" ] && [ -z "$pr" ]; then
    printf 'CREATE\n'
  elif [ -z "$pl" ]; then
    printf 'ADOPT_RACE_APPEARED\n'
  elif [ -z "$pr" ]; then
    printf 'VANISHED\n'
  elif [ "$pl" = "$pr" ]; then
    printf 'UPDATE\n'
  else
    printf 'ADOPT_RACE_CHANGED\n'
  fi
}
```

- `awk -F'|' '$1 == k'` 精确匹配键，不用 `grep "/$key|"`。
- `VANISHED` 出现时冻结并交用户判断；不要把它当成 `ADOPT_RACE_CHANGED`。

### 4. 场景表

| 场景 | plan | pre | 期望 | 用途 |
|---|---|---|---|---|
| 同内容异根 | `u1`，body v1 | `u1`，body v1，不同绝对根 | `UPDATE` | 抓绝对路径污染 |
| 同内容异 mtime | `u2`，body v2 | `u2`，body v2，mtime 不同 | `UPDATE` | 抓 mtime 污染 |
| 首次快照后出现 | 无 `a1` | `a1` | `ADOPT_RACE_APPEARED` | 抓并发出现 |
| 内容变化 | `c1`，body v1 | `c1`，body v2-longer | `ADOPT_RACE_CHANGED` | 抓 size/SHA 变化 |
| 两次都不存在 | 无 `k1` | 无 `k1` | `CREATE` | 抓首次创建 |
| 目标消失 | `v1` | 无 `v1` | `VANISHED` | 守卫 |
| 同 size 异 SHA | `s1`，body 1111 | `s1`，body 2222 | `ADOPT_RACE_CHANGED` | 证明比较含 SHA |

`UPDATE` 与 `update_mtime` 两行必须放在不同的 plan/pre 根对；共用一个根对会把场景之间的文件混进比较。

### 5. 洁净检查

```bash
files_at_top() {
  find "$1" -maxdepth 1 -type f -printf '%f\n' | LC_ALL=C sort | tr '\n' ' '
}
```

- `clean-target` 含 `.git/` 与 `SKILL.md`：`files_at_top` 必须只返回 `SKILL.md `。
- `dirty-target` 含 `extra.txt`：返回值必须包含 `extra.txt`，断言才能发现残留。
- 不要用 `ls -A` 作为唯一检查；它会把 `.git` 计入，制造“未清理”假失败。
- 如果目标合法含 `.gitattributes`/`.gitignore`，把它们写进期望清单；不要放宽为“任意文件都不算残留”。

### 6. 计数门禁

```bash
EXPECTED=12
[ -n "${TARGET:-}" ] && EXPECTED=$((EXPECTED + 2))
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -ne 0 ] || [ "$PASS" -ne "$EXPECTED" ] || [ "$TOTAL" -ne "$EXPECTED" ]; then
  printf 'GATE FAIL: PASS=%s FAIL=%s TOTAL=%s EXPECTED=%s\n' \
    "$PASS" "$FAIL" "$TOTAL" "$EXPECTED"
  exit 1
fi
printf 'GATE PASS: PASS=%s FAIL=%s TOTAL=%s EXPECTED=%s\n' \
  "$PASS" "$FAIL" "$TOTAL" "$EXPECTED"
```

- `EXPECTED` 只在脚本开头算一次；末尾不再写第二个硬编码数字。
- 新增或删除断言时，同一次编辑里更新 `EXPECTED`。
- 全绿但 `EXPECTED` 不匹配时必须打印 `GATE FAIL` 并以 1 退出，不能只留下 `rc=1`。

## 最小断言集

核心 12 项（不传 `--target`）：

| # | 断言 | 期望 |
|---|---|---|
| 1 | `state.update_diff_roots` | `UPDATE` |
| 2 | `state.update_mtime` | `UPDATE` |
| 3 | `state.appeared` | `ADOPT_RACE_APPEARED` |
| 4 | `state.changed` | `ADOPT_RACE_CHANGED` |
| 5 | `state.create` | `CREATE` |
| 6 | `state.vanished` | `VANISHED` |
| 7 | `state.changed_same_size` | `ADOPT_RACE_CHANGED` |
| 8 | `precondition.mtime_differs` | `yes`（保证 #2 非空转） |
| 9 | `precondition.same_size` | `yes`（保证 #7 非空转） |
| 10 | `clean.git_metadata_ignored` | `SKILL.md ` |
| 11 | `clean.extra_file_detected` | 含 `extra.txt` |
| 12 | `cleanup.work_removed` | `yes` |

传入 `--target <skill-dir>` 时追加 2 项，`EXPECTED=14`：

| # | 断言 | 期望 |
|---|---|---|
| 13 | `target.sha_unchanged` | 前后相同 |
| 14 | `target.size_mtime_unchanged` | 前后相同 |

## 运行顺序

1. 记录目标基线（如果使用 `--target`）：`sha256sum "$TARGET/SKILL.md"`、`stat -c '%s|%Y'`。
2. 创建唯一 work dir：`mktemp -d "$HOME/.qoder/tmp/triage-fixture.XXXXXX"`。
3. 按场景表建 plan/pre 根与 `SKILL.md`；`UPDATE` 与 `update_mtime` 使用不同根对。
4. 跑四态与 `VANISHED` 断言。
5. 跑先决条件：mtime 确实不同、size 确实相同，避免 #2/#7 空转。
6. 跑 `.git` 洁净与额外文件断言。
7. 若传了 `--target`，在所有读写之后重新采样目标并断言不变。
8. 删除 work dir，确认不存在；不删除脚本自身。
9. 计算 `TOTAL`，跑计数门禁；要求 `rc=0`。
10. 报告 `PASS/FAIL/TOTAL/EXPECTED` 与 `rc`，不能只列 PASS 行。

如果夹具外围还要跑 `skill-file-qa`，用位置参数，并在校验器前后各采样一次目标；不要用 `--skill`（argparse 缩写为 `--skills-root`，可能 `0 found` 假 PASS）。通用夹具验收与校验器细节归 `valider-harnais-fixture-windows-msys`、`skill-file-qa`。

## 失败诊断表

| 症状 | 原因 | 动作 |
|---|---|---|
| `UPDATE` 实际为 `ADOPT_RACE_CHANGED` | 快照行含绝对根路径；同内容异根比较不相等 | 键改为相对路径；加“同内容异根”断言 |
| 仅 mtime 不同也判 `CHANGED` | 相等判断包含 mtime | 从比较键移除 mtime；mtime 只用于报告 |
| 目标目录明明干净却报残留 | `ls -A` 把 `.git` 或其它元数据计入 | 用 `find -maxdepth 1 -type f`，或排除 `.git` 并写清允许清单 |
| 所有断言 PASS 但脚本 `rc=1` | 末尾预期数写死且已漂移（如 17 项断言写 `-eq 16`） | 单一 `EXPECTED`；同时校验 PASS/TOTAL/FAIL；打印 `GATE FAIL` |
| 第一条断言失败后脚本立刻退出 | 使用了 `set -e` | 只用 `set -u`；用计数器收集全部断言，最后统一门禁 |
| `grep` 无命中导致脚本退出 | `set -e` 且没有 `|| true` | 用 `awk` 精确取行；或显式 `|| true` |
| 运行中的脚本删除自身失败 | Windows 文件锁 | 不让脚本自删；删除夹具目录，脚本由调用方管理 |
| `python` 以 49 退出 | Microsoft Store 别名 | 用 `py -3` |
| `UnicodeEncodeError`/`charmap` | 控制台代码页 | 输出保持 ASCII；需要非 ASCII 时设 `PYTHONIOENCODING=utf-8` |

## 完成清单

- [ ] 夹具只写 `$HOME/.qoder/tmp/triage-fixture.*`，真实目标零写入。
- [ ] 快照键为相对路径 + size + SHA-256，不含绝对根与 mtime。
- [ ] `UPDATE` 用两个不同绝对根的同内容文件实测。
- [ ] 四态与 `VANISHED` 全覆盖。
- [ ] `.git` 不计入残留；额外文件能被发现。
- [ ] 末尾 `EXPECTED` 单一来源，`PASS/TOTAL/FAIL` 同时匹配，`rc=0`。
- [ ] 目标前后 SHA/size/mtime 不变（如使用 `--target`）。
- [ ] 夹具删除并确认不存在；脚本未自删。
- [ ] 报告含 `PASS/FAIL/TOTAL/EXPECTED` 与 `rc`。

## 资源

- `scripts/selftest_triage_snapshot.sh`：12 项核心断言 + 可选 2 项目标断言；只写 `~/.qoder/tmp`。
- `references/cas-2026-10-26-triage-fixture.md`：来源会话 `e506f79c` 的失败输出、根因、三处修复与边界。

## 来源与边界

- 来源会话 `e506f79c-3510-4634-a1da-934252ade330`（读取时 16 条消息、7 个用户回合、`runtimeState=cold`、`revision=0`、`hasMoreBefore=false`）。
- 首轮夹具 `PASS=15 FAIL=2 TOTAL=17`、`rc=1`：`UPDATE` 被 `ADOPT_RACE_CHANGED` 顶替；目标洁净断言因 `ls -A` 计入 `.git` 失败。
- 第二轮 17/17 全绿仍 `rc=1`：末尾写死 `-eq 16`；改为 17 后第三轮 `rc=0`。
- 本 Skill 只固化“双快照分流夹具”的实现与门禁；来源夹具中的校验器五形态归 `valider-harnais-fixture-windows-msys` 与 `skill-file-qa`，不在此复制。
- 未验证：真实并发写入、生产目标、非 Git Bash 环境的 `find -printf`/`stat -c` 可移植性。
