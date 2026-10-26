# 参考夹具漂移案例：dependency-script-contract-reaudit（2026-10-26）

日期：2026-10-26（Europe/Paris，UTC+1）。以下数字、哈希与输出是当天事实，不是永久保证；依赖脚本或目标 Skill 变化后必须重跑。

## 来源与环境

- 方案来源会话 6e0f13d3-db4c-4e3f-bea7-36611df4ca81：revision 35，runtimeState ready，hasMoreBefore false；只有 2 条消息（任务与只读方案），没有写入。本 Skill 目录在方案确认期间由另一流程创建（SKILL.md 12:23:43，参考文件 12:23:54），随后按 update 流程核验。
- 证据会话 484dd08b-df03-40b3-a174-a469bac21a9b：revision 49，runtimeState ready，hasMoreBefore false；可见用户回合 2 个（初始任务、「确认按此方案执行」），没有内容纠正。
- 该会话内嵌读取了上游会话 6d8bf6ea-6293-4ccd-9f5b-b6471e8157b5（revision 10）。本案例没有单独重读上游原文，上游溯源以目标 Skill 参考文件的记载为准。
- 本案的可执行夹具位于 dependency-script-contract-reaudit 的参考文件 contrat-find-stale-archives.md 的「复跑夹具」；本文只保留漂移对照与结论，不复制第二份夹具。
- 复核环境：Windows Git Bash、py -3（Python 3.14.7）、git 2.52.0、sha256sum 可用。复跑时使用 py -3，因为本机 python 是 Microsoft Store 存根。

## 目标与并发创建

目标 Skill 为 dependency-script-contract-reaudit。会话开始时目录不存在；12:13:06 由另一流程创建，随后间隔 3 秒双采样稳定：

```text
2026-10-26 12:13:06  7,804 B  SKILL.md                    fba2054ceacd...
2026-10-26 12:13:06  4,949 B  参考文件 contrat-find-stale-archives.md  b5d47523...
```

因此实际动作是 update，不是覆盖式 create。写入前再次双采样，确认未被改写后才编辑。

## 记录与夹具的矛盾

参考文件记录的 EXTRA 用例：

```text
=== EXTRA ===
  STALE 2 anomalie(s) sur 2 fichier(s) source
  MISMATCH scripts/a.py archive=b917a726c93f source=d0e0fd661801
  EXTRA    scripts/extra.txt absent de la source
RESULT STALE
EXIT=1
```

同一文件的夹具却先制造 STALE，再把源文件复位：

```bash
printf 'VALUE=2\n' > "$TMP/src/probe/scripts/a.py"
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo"

printf 'VALUE=1\n' > "$TMP/src/probe/scripts/a.py"   # 复位
printf 'extra\n' > "$TMP/repo/.qoder/skills/probe/scripts/extra.txt"
git -C "$TMP/repo" add .
git -C "$TMP/repo" -c user.name=audit -c user.email=audit@example.invalid commit -qm "extra"
```

归档中的 a.py 仍为 VALUE=1；复位后源文件与归档相同，只可能剩 EXTRA 一条异常。

## 首次重放（原样，未修改夹具）

```text
  STALE 1 anomalie(s) sur 2 fichier(s) source
  EXTRA    scripts/extra.txt absent de la source
RESULT STALE
EXTRA_EXIT=1
```

摘录只有 1 条异常且没有 MISMATCH，与记录的 2 条不一致。这一步证明矛盾来自夹具与记录的漂移，而不是被测脚本。

## 修正

删除 EXTRA 前的复位，保持 STALE 用例留下的 VALUE=2，并加一行注释：

```bash
# 源文件保持 VALUE=2，使 EXTRA 用例同时出现 MISMATCH 与 EXTRA，与来源实测的 2 条异常一致
printf 'extra\n' > "$TMP/repo/.qoder/skills/probe/scripts/extra.txt"
```

记录块保持不变；参考文件补充 2026-10-26 的复核说明与删除理由。

## 修正后完整重放

从干净的临时目录重建夹具后，逐项断言如下（blob 与 commit 每次不同，未参与断言）：

| 用例 | 期望退出码 | 关键输出 | 实测 |
|---|---|---|---|
| HELP | 0 | 五个参数 | 符合 |
| FRESH | 0 | `RESULT FRESH` | 符合 |
| STALE | 1 | `RESULT STALE` + `MISMATCH` | 符合 |
| EXTRA | 1 | `STALE 2 anomalie` + `MISMATCH` + `EXTRA` | 符合 |
| NONE（不匹配 dest） | 0 | `RESULT NONE` | 符合 |
| PARTIAL（无效 repo） | 2 | `FAIL environment` + 部分结果 + `RESULT FAIL` | 符合 |
| PUBLISHED | 1 | `[published]` 标签 | 符合 |
| USAGE（缺 repo/root） | 2 | `FAIL usage` | 符合 |
| MAX DEPTH 0 | 2 | `FAIL usage` | 符合 |
| 缺 SKILL.md | 2 | `FAIL usage` | 符合 |
| `..` dest | 2 | `invalid --dest` | 符合 |
| 非 Git 目录 | 0 | `NOTE not a repository` + `Repositories 0` + `RESULT NONE` | 符合 |

## 退出码被管道吞掉

修正后的第一次复跑，输出内容正确，但所有用例都打印 EXIT=0，包括用法错误应为 2 的用例。原因是退出码在管道或 `cat` 之后才读取，拿到的是最后一个命令的状态。改为「运行、立即保存退出码、再过滤」后，才得到上表结果。该陷阱上游文档已经警告过，第一次复跑仍然踩中，说明断言必须与内容分开采集。

## --dest 边界（同一会话实测）

| 输入 | 结果 | 结论 |
|---|---|---|
| `.qoder/skills/absent`（有效但不匹配） | `RESULT NONE` / 0 | 假阴性，不等于 FRESH |
| `../escape` | `FAIL usage: invalid --dest` / 2 | 已验证 |
| `C:/abs` | 被接受，`RESULT NONE` / 0 | Windows 绝对路径未被拒绝 |
| `/` | 被 MSYS 改写为安装路径（观测到 C:/Program Files/Git），`RESULT NONE` / 0 | 未下结论 |
| 空字符串 | 按默认 dest，`FRESH 2/2` / 0 | 已验证 |
| 存在的非 Git 目录 | `NOTE not a repository` + `Repositories 0` + `NONE` / 0 | 与路径不存在不同 |
| 不存在的 `--repo` | `FAIL environment` + 部分结果 + `FAIL` / 2 | 环境错误优先 |

## 非确定性字段

- commit ID：c2c78bfc…、dc3a391b…、7dcdcbcf…、f2ea06eb… 等每次不同。
- blob 前缀：archive 与 source 的值在不同运行间变化（source 曾为 d0e0fd66…、16ccf682…、64fc8a7a…）；本案例不推断根因。
- 临时路径与 mtime 每次不同。

断言只使用 `RESULT` 行、退出码、异常类型（MISMATCH/EXTRA）、标签（published/local）与计数。

## 连带发现

复跑通过后，完整重读还发现两处非夹具问题：第 1 步的 grep 仍写死绝对路径；第 5 步「旧哈希零命中」与参考文件的历史差异段冲突。两处均按最小编辑修正。说明重放通过不等于文档内部自洽，仍需完整读取全文。

## 最终产物（当天的历史证据）

- 修正后 SKILL.md 8,239 B，SHA-256 17abe9dc…；参考文件 6,118 B，7ce7ced9…；skill-file-qa 报告 9 PASS / 0 FAIL / 0 WARN。
- 依赖脚本 find_stale_archives.py 在复审计期间为 eb3ccb61…（9,887 B，12:00:20）；本流程未修改它。
- 上述哈希只是 2026-10-26 的快照；再次使用前必须重新采样。

## 覆盖边界

- 在 Windows Git Bash、py -3、git 可用时验证；其他 shell 需调整。
- 未覆盖：`/` dest 的最终结论、符号链接、超过 50 个仓库的截断、夹具未包含的业务正确性。
- 本案例证明的是「记录可由夹具复现」，不是被测脚本在所有环境下都正确。
