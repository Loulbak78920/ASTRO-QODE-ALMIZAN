# MSYS 参数改写探针证据

日期：2026-10-26（Europe/Paris，UTC+1）。环境：Windows 10.0.26200，Git Bash 2.52.0.windows.1，Python 3.14.7。以下为当天事实，不是永久保证。

## 证据来源

- 本 Skill 的直接来源会话 `41c1eeca-e7e8-4b10-baa4-50151d05499e`：读取时 revision 25；用户在初次方案后追加「添加 argv 探针脚本」，探针脚本与本文档由此产生。
- 来源会话 `484dd08b-df03-40b3-a174-a469bac21a9b`：读取时 revision 49，`hasMoreBefore: false`。第 1 轮 tool 15 记录了 `=== DEST .. ===`、`=== DEST / ===`、`=== DEST C:/abs ===` 与 `=== DEST EMPTY STRING ===`。
- 该会话嵌套引用 `6d8bf6ea-6293-4ccd-9f5b-b6471e8157b5`：读取时 revision 27；用户纠正「将文档改为中文」。
- 来源会话只观察到 `/` 被改写为 `C:/Program Files/Git`，并标注「未下结论」。本文件的隔离对照、`cmd //c`、PowerShell 与探针脚本是 2026-10-26 的补充实测，不归因于来源会话。

## 来源会话原始输出

```text
=== DEST .. ===
FAIL usage: invalid --dest ../escape
RESULT FAIL
EXIT=2
=== DEST / ===
Skill source : C:\Users\Administrateur\Desktop\IMAM8MAHDI\.qoder\tmp\dcr-dest-2013\src\probe
Destination  : C:/Program Files/Git
Repositories : 1
Fichiers     : 2

RESULT NONE
EXIT=0
=== DEST C:/abs ===
Skill source : C:\Users\Administrateur\Desktop\IMAM8MAHDI\.qoder\tmp\dcr-dest-2013\src\probe
Destination  : C:/abs
Repositories : 1
Fichiers     : 2

RESULT NONE
EXIT=0
=== DEST EMPTY STRING ===
  FRESH 2/2 fichiers identiques

RESULT FRESH
EXIT=0
```

空字符串用例得到 `FRESH 2/2`，是程序自身行为；本文件不解释，也不归因于 MSYS。

## 本机复测：argv 矩阵

```bash
PROBE="$HOME/.qoder/skills/probe-cli-args-beyond-msys-rewrite/scripts/print_argv.py"
PROBE_WIN="$(cygpath -w "$PROBE")"

py -3 "$PROBE" --dest "/"
# ["--dest", "C:/Program Files/Git/"]

py -3 "$PROBE" --dest=/
# ["--dest=C:/Program Files/Git/"]

MSYS2_ARG_CONV_EXCL='*' py -3 "$PROBE_WIN" --dest "/"
# ["--dest", "/"]

MSYS_NO_PATHCONV=1 py -3 "$PROBE_WIN" --dest "/"
# ["--dest", "/"]

MSYS2_ARG_CONV_EXCL='--dest' py -3 "$PROBE" --dest "/"
# ["--dest", "C:/Program Files/Git/"]

py -3 "$PROBE" --dest "C:/abs" --dest "../escape" --dest "" --dest "/tmp/x"
# ["--dest", "C:/abs", "--dest", "../escape", "--dest", "", "--dest", "C:/Users/ADMINI~1/AppData/Local/Temp/x"]
```

`/tmp/x` 的临时目录名含 8.3 短名，随机器和配置变化；只断言它被改写，不比对具体临时路径。

原生 shell 与失败分支：

```bash
powershell -NoProfile -Command "py -3 '$PROBE_WIN' --dest /"
# ["--dest", "/"]

cmd //c py -3 "$PROBE_WIN" --dest /
# ["--dest", "C:/Program Files/Git/"]

MSYS2_ARG_CONV_EXCL='*' py -3 "$PROBE" --dest "/"
# can't open file 'C:\c\Users\...\print_argv.py': [Errno 2] No such file or directory
# EXIT=2
```

`cmd //c` 由 Git Bash 启动时，改写已在进入 cmd 前发生，因此不算隔离；从 Git Bash 外启动的 cmd 未验证。PowerShell 的上述 `-Command` 形式已验证；其他引用形式未验证。

## 本机复测：端到端

```text
=== 未隔离 ===
Destination  : C:/Program Files/Git
RESULT NONE
EXIT=0

=== 隔离后 ===
FAIL usage: invalid --dest /
RESULT FAIL
EXIT=2
```

未隔离的 `NONE/0` 不能证明 `/` 被接受；隔离后才看到用法错误。程序打印的 `Destination` 会去掉末尾斜杠，原始 argv 仍有末尾斜杠；两者不矛盾。

## 复跑夹具

在项目根目录执行。夹具只写 `.qoder/tmp/replay-fixtures-<UTC>/`，结束后删除该目录。若 Skill 安装在项目级，把 `$HOME/.qoder/skills` 换成项目的 `.qoder/skills`。

```bash
TMP=".qoder/tmp/replay-fixtures-$(date -u +%Y%m%dT%H%M%SZ)"
printf 'TMP=%s\n' "$TMP"
mkdir -p "$TMP/src/probe/scripts" "$TMP/repo/.qoder/skills" || exit 1
printf '# probe\n' > "$TMP/src/probe/SKILL.md" || exit 1
printf 'VALUE=1\n' > "$TMP/src/probe/scripts/a.py" || exit 1
git init -q "$TMP/repo" || exit 1
cp -r "$TMP/src/probe" "$TMP/repo/.qoder/skills/probe" || exit 1
git -C "$TMP/repo" add . >/dev/null 2>&1 || exit 1
git -C "$TMP/repo" -c user.name=audit -c user.email=audit@example.invalid commit -qm "archive probe" >/dev/null 2>&1 || exit 1

DEP="$HOME/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py"
PROBE="$HOME/.qoder/skills/probe-cli-args-beyond-msys-rewrite/scripts/print_argv.py"
test -f "$DEP" || { echo "FAIL dependency missing: $DEP"; exit 2; }
test -f "$PROBE" || { echo "FAIL probe missing: $PROBE"; exit 2; }
PROBE_WIN="$(cygpath -w "$PROBE")"
DEP_WIN="$(cygpath -w "$DEP")"
SRC_WIN="$(cygpath -w "$TMP/src/probe")"
REPO_WIN="$(cygpath -w "$TMP/repo")"

py -3 "$PROBE" --dest "/" > "$TMP/plain_argv.out" 2>&1
printf '%s' "$?" > "$TMP/plain_argv.code"
MSYS2_ARG_CONV_EXCL='*' py -3 "$PROBE_WIN" --dest "/" > "$TMP/isolated_argv.out" 2>&1
printf '%s' "$?" > "$TMP/isolated_argv.code"
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo" --dest "/" > "$TMP/plain_e2e.out" 2>&1
printf '%s' "$?" > "$TMP/plain_e2e.code"
MSYS2_ARG_CONV_EXCL='*' py -3 "$DEP_WIN" --skill "$SRC_WIN" --repo "$REPO_WIN" --dest "/" > "$TMP/isolated_e2e.out" 2>&1
printf '%s' "$?" > "$TMP/isolated_e2e.code"
MSYS2_ARG_CONV_EXCL='--dest' py -3 "$PROBE" --dest "/" > "$TMP/targeted_argv.out" 2>&1
printf '%s' "$?" > "$TMP/targeted_argv.code"
MSYS2_ARG_CONV_EXCL='*' py -3 "$PROBE" --dest "/" > "$TMP/posixpath_err.out" 2>&1
printf '%s' "$?" > "$TMP/posixpath_err.code"

FAILS=0
check() {
  name="$1"; want="$2"; pattern="$3"
  got="$(cat "$TMP/$name.code")"
  if [ "$got" = "$want" ] && grep -q -- "$pattern" "$TMP/$name.out"; then
    printf 'OK %s exit=%s contains %s\n' "$name" "$got" "$pattern"
  else
    printf 'MISMATCH %s want_exit=%s got_exit=%s pattern=%s\n' "$name" "$want" "$got" "$pattern"
    FAILS=$((FAILS + 1))
  fi
}

for n in plain_argv isolated_argv plain_e2e isolated_e2e targeted_argv posixpath_err; do
  printf '=== %s EXIT=%s ===\n' "$n" "$(cat "$TMP/$n.code")"
  grep -E '^(RESULT|FAIL|NOTE|Destination|ARCHIVE|\[)' "$TMP/$n.out" | tail -n 12
done

check plain_argv 0 'C:/Program Files/Git/'
check isolated_argv 0 '\["--dest", "/"\]'
check plain_e2e 0 '^RESULT NONE$'
check plain_e2e 0 'Destination  : C:/'
check isolated_e2e 2 'FAIL usage: invalid --dest /'
check isolated_e2e 2 '^RESULT FAIL$'
check targeted_argv 0 'C:/Program Files/Git/'
check posixpath_err 2 'No such file or directory'

bash -c 'false | cat >/dev/null; echo "PIPE_EXIT=$?"' > "$TMP/pipe.out" 2>&1
bash -c 'false; echo "DIRECT_EXIT=$?"' > "$TMP/direct.out" 2>&1
grep -q 'PIPE_EXIT=0' "$TMP/pipe.out" && echo 'OK pipe exit masked (0)' || { echo 'MISMATCH pipe exit'; FAILS=$((FAILS + 1)); }
grep -q 'DIRECT_EXIT=1' "$TMP/direct.out" && echo 'OK direct exit 1' || { echo 'MISMATCH direct exit'; FAILS=$((FAILS + 1)); }

printf 'FAILS=%s\n' "$FAILS"
rm -rf "$TMP"
[ "$FAILS" = 0 ]
```

预期：所有 `check` 行为 `OK`，最后两行 `OK pipe exit masked (0)`、`OK direct exit 1`，并输出 `FAILS=0`、退出 0。夹具的端到端断言绑定 2026-10-26 的依赖脚本行为；依赖变化时先按 `dependency-script-contract-reaudit` 复审计，不修改本记录来迁就新行为。

## 管道吞码

来源会话第 2 轮 tool 15 因过滤输出，出现 `STALE_EXIT=0`、`PARTIAL_EXIT=0` 等错误退出码；第 2 轮 tool 16 改为先运行、立即取码、再过滤后，得到 `STALE EXIT=1`、`PARTIAL EXIT=2`。本机最小复现：

```text
bash -c 'false | cat >/dev/null; echo "PIPE_EXIT=$?"'
PIPE_EXIT=0

bash -c 'false; echo "DIRECT_EXIT=$?"'
DIRECT_EXIT=1
```

退出码必须来自目标命令本身，不能来自管道末端的 `cat`、`head`、`grep` 或 `tail`。

## 覆盖边界与未解释

- 已验证：Git Bash 2.52.0.windows.1、Python 3.14.7、Windows 10.0.26200；`MSYS2_ARG_CONV_EXCL='*'`、`MSYS_NO_PATHCONV=1`、PowerShell `-Command` 的上述形式；`cmd //c` 从 Git Bash 启动仍被改写。
- `MSYS2_ARG_CONV_EXCL='/'` 能保留 `/`（排除匹配参数文本），但同时阻止 POSIX 脚本路径转换；实测探针以 POSIX 路径启动时得到 `can't open file 'C:\c\...'`/退出 2。只作诊断，不作推荐隔离。
- 未验证：从 Git Bash 外启动的 cmd；其他 Git for Windows/MSYS 版本；其他 shell；符号链接；网络路径；大小写或短路径对转换的影响。
- `C:/abs` 未被改写且程序返回 `NONE/0`；这不等于“接受”，程序内部归一化语义未复核。
- 隔离后 `/tmp/x` 到达脚本为 `/tmp/x`，脚本显示 `tmp/x` 并返回 `NONE/0`；这是程序自身归一化，不归因于 MSYS。
- `--dest ""` 在来源会话得到 `FRESH 2/2`；本文件不解释该程序行为，也不归因于 MSYS。
- Git 安装前缀（如 `C:/Program Files/Git/`）和临时目录映射随安装位置、版本与配置变化；复测时以本机 argv 为准。
- 本文件只证明参数到达程序的形式与一个目标程序的结果，不证明目标程序的业务正确性。

## 复跑断言

- 直接调用 `/`：argv 必须包含本机 Git 安装前缀，且不得据此断言 `/` 被接受。
- 隔离后 `/`：argv 必须精确为 `/`。
- 端到端：未隔离 `RESULT NONE`/0；隔离后 `FAIL usage: invalid --dest /`/2。
- 定向排除 `--dest`：仍为本机 Git 安装前缀。
- 隔离 + POSIX 脚本路径：必须失败并出现 `No such file or directory`。
- 管道：`false | cat` 的输出为 0，直接 `false` 的退出码为 1。
