---
name: probe-cli-args-beyond-msys-rewrite
description: "在 Git Bash/Windows 上用路径型参数（尤其以 / 开头的参数）探测 CLI 契约时，先隔离 MSYS 参数改写再判断接受或拒绝：用 scripts/print_argv.py 记录真实 argv，对照 Git Bash 直接调用、MSYS2_ARG_CONV_EXCL='*' 或 MSYS_NO_PATHCONV=1 加原生 Windows 路径、以及 PowerShell -Command；定向排除 --dest 无效，从 Git Bash 启动 cmd //c 仍被改写，隔离时未改原生路径会导致脚本找不到；退出码先运行后取，不经管道；用于 --dest /、/tmp/x、C:/Program Files/Git、NONE/0 假阴性、invalid --dest、参数被环境改写、管道吞退出码等场景；不替代完整契约复审计、依赖脚本复审计或包完整性审计。"
---

# Git Bash 参数改写下的 CLI 探针

## 目标与边界

Git Bash 的 MSYS 层可能在目标程序启动前改写路径型参数。未隔离时测到的可能是 Git 安装目录或 MSYS 临时目录，而不是字面参数；据此断言“接受/拒绝”会把环境行为误记成契约。本 Skill 用 argv 探针和端到端对照，把“环境改写”与“程序自身的接受/拒绝”分开。

- 只读探测，不修改被探测脚本。
- 不替代完整契约审计（`audit-skill-tool-contracts`）或依赖脚本复审计（`dependency-script-contract-reaudit`）。
- 不解释目标程序的业务逻辑，只记录参数到达程序的形式与程序输出。

## 触发条件

- 路径型参数以 `/` 开头（`/`、`/tmp/x`、`/c/...`），或输出出现 `C:/Program Files/Git`。
- 参数看起来被接受/拒绝，但不确定程序实际收到什么。
- 需要在 Git Bash 与隔离调用之间对照，或要复跑一次参数探针。
- 退出码为 0 但结果可疑（如 `NONE/0`），或命令经过管道。

## 不可协商规则

1. 先证明参数实际到达程序的形式（argv 或程序打印的路径），再判断接受/拒绝。
2. 未隔离时只记录“环境改写后的结果”，不得据此断言字面参数被接受或拒绝。
3. 隔离时同时改路径：`MSYS2_ARG_CONV_EXCL='*'` 或 `MSYS_NO_PATHCONV=1` 会停止所有参数转换；脚本路径和 `--skill`/`--repo`/`--dest` 等必须用 `cygpath -w` 或 `C:/...`。
4. 定向排除不隔离值：`MSYS2_ARG_CONV_EXCL='--dest'` 仍会把其值 `/` 改写；不要用它冒充隔离。
5. 从 Git Bash 启动的 `cmd //c` 仍被改写；PowerShell `-Command` 字符串形式仅在已验证的引用形式下保留 `/`；其他形式标“未验证”。
6. 退出码先运行后取 `$?`，不经管道或过滤；通用规则见 `audit-skill-tool-contracts`。
7. 只读；临时夹具放 `.qoder/tmp/` 下本次唯一的目录（如 `probe-cli-args-<时间戳>` 或 `replay-fixtures-<UTC>`），结束只清理该目录；不提交、不推送。
8. 报告区分“隔离后的字面结果 / 未隔离的环境改写结果 / 未验证分支”。

## 第 1 步 — 用 argv 探针记录真实参数

`scripts/print_argv.py` 只输出 `sys.argv[1:]` 的 JSON 数组，ASCII 安全，不做参数解释：

```bash
PROBE="$HOME/.qoder/skills/probe-cli-args-beyond-msys-rewrite/scripts/print_argv.py"
py -3 "$PROBE" --dest "/"
```

直接调用时，本机实测输出：

```text
["--dest", "C:/Program Files/Git/"]
```

这说明 `/` 没有到达程序。等号形式同样会被改写：

```bash
py -3 "$PROBE" --dest=/
# ["--dest=C:/Program Files/Git/"]
```

项目级安装时，把 `$HOME/.qoder/skills` 换成项目的 `.qoder/skills`。

## 第 2 步 — 隔离并复测 argv

隔离变量会停止**所有**参数转换，因此脚本路径必须改成原生形式：

```bash
PROBE_WIN="$(cygpath -w "$PROBE")"
MSYS2_ARG_CONV_EXCL='*' py -3 "$PROBE_WIN" --dest "/"
# ["--dest", "/"]

MSYS_NO_PATHCONV=1 py -3 "$PROBE_WIN" --dest "/"
# ["--dest", "/"]

# PowerShell 仅该 -Command 形式已验证；其他引用形式未验证
powershell -NoProfile -Command "py -3 '$PROBE_WIN' --dest /"
# ["--dest", "/"]
```

若隔离时仍用 POSIX 脚本路径，探针本身会启动失败：

```bash
MSYS2_ARG_CONV_EXCL='*' py -3 "$PROBE" --dest "/"
# can't open file 'C:\c\Users\...\print_argv.py'
```

隔离方式对照（本机 2026-10-26 实测）：

| 方式 | `--dest /` 的 argv | 是否隔离 | 备注 |
|---|---|---|---|
| Git Bash 直接调用 | `C:/Program Files/Git/` | 否 | 环境改写 |
| `MSYS2_ARG_CONV_EXCL='*'` + 原生脚本路径 | `/` | 是 | 所有路径参数需原生形式 |
| `MSYS_NO_PATHCONV=1` + 原生脚本路径 | `/` | 是 | 同上 |
| `MSYS2_ARG_CONV_EXCL='--dest'` | `C:/Program Files/Git/` | 否 | 排除的是参数名前缀，不是值 |
| `cmd //c`（从 Git Bash 启动） | `C:/Program Files/Git/` | 否 | 仍被改写 |
| PowerShell `-Command` | `/` | 是（该形式） | 参数写在命令字符串内 |

`MSYS2_ARG_CONV_EXCL='/'` 按参数文本匹配，能保留 `/`，但也会让 POSIX 脚本路径（`/c/...`）停止转换；只用于诊断，不作为隔离方法。

其他字面参数的观测：

| 字面参数 | 直接调用时 argv | 隔离后 argv | 说明 |
|---|---|---|---|
| `/` | `C:/Program Files/Git/` | `/` | Git 安装前缀 |
| `/tmp/x` | `C:/Users/.../AppData/Local/Temp/x` | `/tmp/x` | MSYS 临时目录 |
| `C:/abs` | `C:/abs` | `C:/abs` | 未被改写；不代表被接受 |
| `../escape` | `../escape` | `../escape` | 未被改写 |
| `""` | `""` | `""` | 未被改写 |

## 第 3 步 — 端到端复测

对同一目标程序分别做未隔离与隔离调用，记录程序打印的路径、`RESULT` 和退出码。完整夹具见 `references/msys-argv-probe.md`；下面假设 `$TMP` 是该夹具的临时目录，`$DEP` 是目标脚本。任何接受路径参数的 CLI 都可按同一方法对照。

```bash
# 未隔离
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo" --dest "/" ; echo "EXIT=$?"

# 隔离：所有路径参数用原生形式
DEP_WIN="$(cygpath -w "$DEP")"
SRC_WIN="$(cygpath -w "$TMP/src/probe")"
REPO_WIN="$(cygpath -w "$TMP/repo")"
MSYS2_ARG_CONV_EXCL='*' py -3 "$DEP_WIN" --skill "$SRC_WIN" --repo "$REPO_WIN" --dest "/" ; echo "EXIT=$?"
```

本机实测对照：

| 调用 | 程序看到 | 结果 | 退出码 |
|---|---|---|---|
| 未隔离 | `C:/Program Files/Git` | `RESULT NONE` | 0 |
| 隔离后 | 字面 `/` | `FAIL usage: invalid --dest /` | 2 |

未隔离的 `NONE/0` 不能证明 `/` 被接受；隔离后才看到真正的用法错误。

## 第 4 步 — 判定

| 情形 | 动作 |
|---|---|
| 未隔离与隔离结果一致 | 环境改写未影响该参数；可采用隔离结果 |
| 结果不一致 | 报告两种结果；契约结论只采用隔离后的字面结果，环境改写作为限制 |
| 隔离时脚本找不到 | 脚本路径未改原生形式；用 `cygpath -w` 后重跑 |
| 无法隔离（shell/版本限制） | 标“未验证”；不得断言接受或拒绝 |
| 退出码经管道 | 重新直接运行并取 `$?` |
| 程序自身归一化（如 `/tmp/x` → `tmp/x`） | 记录为程序行为，不归因于 MSYS |

## 错误与陷阱

| 症状 | 原因 | 动作 |
|---|---|---|
| `C:/Program Files/Git` 或 `C:/Program Files/Git/` | Git Bash 把 `/` 改写为安装前缀 | 隔离后重跑 |
| `can't open file 'C:\c\Users\...'` | 隔离变量也停止转换脚本路径 | 用 `cygpath -w` 或原生 `C:/...` |
| 定向排除后仍被改写 | 排除的是参数名前缀，不作用于其值 | 用 `'*'` 并改原生路径 |
| `cmd //c` 仍被改写 | cmd 由 Git Bash 启动，转换已发生 | 改用 PowerShell `-Command` 或隔离变量 |
| `NONE/0` 被当作接受 | 参数被改写为另一路径 | 隔离后复测 |
| `C:/abs` 返回 `NONE/0` | 未被改写不等于被接受 | 只记录“未拒绝”，不下契约结论 |
| 退出码 0 但输出显示失败 | 管道/过滤吞掉退出码 | 先运行，再取 `$?` |
| `/tmp/x` 变成 `C:/Users/.../Temp/x` | MSYS 临时目录映射 | 隔离后重跑 |

## 完成检查

- [ ] 用 `scripts/print_argv.py` 记录了未隔离的真实 argv。
- [ ] 至少用一种隔离方式（`MSYS2_ARG_CONV_EXCL='*'` 或 `MSYS_NO_PATHCONV=1`）记录字面 argv。
- [ ] 隔离时脚本路径和其他路径参数均为原生形式。
- [ ] 对目标程序做了未隔离与隔离的端到端对照，记录输出与退出码。
- [ ] 未把 `NONE/0` 或 `C:/abs` 未改写当作“接受”。
- [ ] 退出码未经管道；失败分支已重跑确认。
- [ ] 临时目录已清理；未修改被探测脚本；未提交、未推送。
- [ ] 报告区分隔离结果、环境改写结果和未验证分支。

## 资源

- `scripts/print_argv.py`：只输出 `sys.argv[1:]` 的 JSON 数组，ASCII 安全，不做参数解释。
- `references/msys-argv-probe.md`：来源会话证据、本机复测矩阵、完整夹具、管道吞码记录、覆盖边界。
- `dependency-script-contract-reaudit`：完整契约矩阵与哈希复审计；本 Skill 只补其 MSYS 边界。
- `audit-skill-tool-contracts`：首次契约审计、负向探针与退出码不经管道的通用规则。
- `publier-skill-qoder-vers-depot-git`：Git ref 含 `/` 的 MSYS 陷阱。
- `skill-file-qa`：写入后的格式与引用验收。
