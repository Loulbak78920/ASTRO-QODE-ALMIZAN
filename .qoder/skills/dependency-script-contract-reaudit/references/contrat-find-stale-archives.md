# find_stale_archives.py 契约复审计证据

日期：2026-10-26（Europe/Paris，UTC+1）。以下值都是当天事实，不是永久保证。

## 来源与核实

- 本 Skill 的方案来源会话 `6d8bf6ea-6293-4ccd-9f5b-b6471e8157b5`：revision 10；用户纠正「将文档改为中文」，因此正文为中文。
- 证据链来源会话 `4cbd2cf3-5cd0-44b9-a2bf-6798a40bbfa6`：revision 37，`runtimeState: ready`，`hasMoreBefore: false`。
- 会话可见用户回合没有针对哈希或契约的内容纠正；失败原因是复测粒度不足，而不是命令执行错误。
- 依赖脚本由 `commit-skill-work` 提供，绝对路径：`C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py`。

## 哈希前后差异

```text
9d0ef62980dfd19f7f49c71a10e9daef0d22e8f0aaa1cc2d6a319b646114fcfa  9869 B  2026-10-26 11:52:49
eb3ccb616626456de47ca2d6be84d8267915538dbba5b9f27af8aff772fbe883  9887 B  2026-10-26 12:00:20
```

脚本在复审计期间被另一会话修改。新版本在 `main()` 中收集 `env_error`，并在 STALE 判定前检查：

```text
if env_error:
    print("NOTE: resultats partiels, voir les lignes FAIL ci-dessus.")
    print("RESULT FAIL")
    return 2
```

因此“任一仓库路径无效”优先于“另一仓库 STALE”。只重跑一个 FRESH/STALE 用例无法发现这类优先级变化。

2026-10-26 复核：依赖仍为 `eb3ccb61…`；按下方修正后的夹具实跑全部用例，结果与记录一致。

## 来源会话实测

临时仓库夹具（源目录名 `probe`，默认 `--dest` 为 `.qoder/skills/probe`）：

```text
=== HELP ===
--skill SKILL
--search-root SEARCH_ROOT
--repo REPO
--dest DEST
--max-depth MAX_DEPTH
HELP_EXIT=0

=== FRESH ===
ARCHIVE master (c2c78bfcb7e9 archive probe) [local]
  FRESH 2/2 fichiers identiques
RESULT FRESH
EXIT=0

=== STALE ===
  MISMATCH scripts/a.py archive=b917a726c93f source=d0e0fd661801
NOTE: aucune archive n'a ete modifiee, commitee ni poussee.
RESULT STALE
EXIT=1

=== EXTRA ===
  STALE 2 anomalie(s) sur 2 fichier(s) source
  MISMATCH scripts/a.py archive=b917a726c93f source=d0e0fd661801
  EXTRA    scripts/extra.txt absent de la source
RESULT STALE
EXIT=1

=== NONE (--dest erroné) ===
RESULT NONE
EXIT=0

=== USAGE (sans --repo/--search-root) ===
FAIL usage: provide --search-root or --repo
RESULT FAIL
EXIT=2

=== PARTIAL ENV ERROR ===
  MISMATCH scripts/a.py archive=b917a726c93f source=d0e0fd661801
  EXTRA    scripts/extra.txt absent de la source
NOTE: resultats partiels, voir les lignes FAIL ci-dessus.
RESULT FAIL
EXIT=2

=== MAX DEPTH 0 ===
FAIL usage: --max-depth must be >= 1
RESULT FAIL
EXIT=2

=== PUBLISHED ===
ARCHIVE master, origin/main (0b7409e87df6 extra) [published]
```

## 复跑夹具

```bash
TMP=".qoder/tmp/dependency-contract-reaudit-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TMP/src/probe/scripts" "$TMP/repo"
printf '# probe\n' > "$TMP/src/probe/SKILL.md"
printf 'VALUE=1\n' > "$TMP/src/probe/scripts/a.py"
git init -q "$TMP/repo"
mkdir -p "$TMP/repo/.qoder/skills"
cp -r "$TMP/src/probe" "$TMP/repo/.qoder/skills/probe"
git -C "$TMP/repo" add .
git -C "$TMP/repo" -c user.name=audit -c user.email=audit@example.invalid commit -qm "archive probe"

DEP="$HOME/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py"

py -3 "$DEP" --help; echo "HELP_EXIT=$?"
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo"; echo "FRESH_EXIT=$?"

printf 'VALUE=2\n' > "$TMP/src/probe/scripts/a.py"
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo"; echo "STALE_EXIT=$?"

# 源文件保持 VALUE=2，使 EXTRA 用例同时出现 MISMATCH 与 EXTRA，与来源实测的 2 条异常一致
printf 'extra\n' > "$TMP/repo/.qoder/skills/probe/scripts/extra.txt"
git -C "$TMP/repo" add .
git -C "$TMP/repo" -c user.name=audit -c user.email=audit@example.invalid commit -qm "extra"
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo"; echo "EXTRA_EXIT=$?"

py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo" --dest .qoder/skills/absent; echo "NONE_EXIT=$?"

printf 'VALUE=3\n' > "$TMP/src/probe/scripts/a.py"
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo" --repo "$TMP/absent"; echo "PARTIAL_EXIT=$?"

git -C "$TMP/repo" update-ref refs/remotes/origin/main HEAD
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo" | grep '^ARCHIVE'

py -3 "$DEP" --skill "$TMP/src/probe"; echo "USAGE_EXIT=$?"
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo" --max-depth 0; echo "DEPTH_EXIT=$?"
mkdir -p "$TMP/empty"
py -3 "$DEP" --skill "$TMP/empty" --repo "$TMP/repo"; echo "NOSKILL_EXIT=$?"

py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/repo" --dest "../escape"; echo "BADDEST_EXIT=$?"
mkdir -p "$TMP/plain"
py -3 "$DEP" --skill "$TMP/src/probe" --repo "$TMP/plain"; echo "NONREPO_EXIT=$?"

rm -rf "$TMP"
```

2026-10-26 复核：原夹具在 EXTRA 前把 `a.py` 复位为 `VALUE=1`，实跑得到 `STALE 1`（仅 `EXTRA`），与来源实测的 2 条异常不一致；因此删除该复位。blob 前缀与提交 ID 每次运行都会变化；断言只看 `RESULT`、退出码和异常类型（`MISMATCH`/`EXTRA`），不比对 blob 值。

## 覆盖边界

- 在 Windows Git Bash、`py -3`、git 可用的环境中验证；其他 shell 需调整。
- 已验证：`--dest ../escape` → `FAIL usage`/2；存在的非 Git 目录 → `NOTE not a repository` + `Repositories 0` + `NONE`/0；不存在的 `--repo` → `FAIL environment` + 部分结果 + `FAIL`/2。
- 已知边界：Windows 绝对 `--dest`（如 `C:/abs`）不被拒绝，按相对路径查询并返回 `NONE`/0；`--dest /` 在 Git Bash 会被 MSYS 改写（观测为 `C:/Program Files/Git`），未下结论；符号链接与超过 50 个仓库的截断未覆盖。
- `RESULT NONE` 只覆盖被查询的仓库，不是全局保证。
- 哈希是 2026-10-26 的日期事实；脚本再次变化时必须从第 1 步重跑。
- 本流程不证明脚本的业务正确性，只证明当前 CLI 契约与文档一致。
- 固定哈希位置可能随文档更新而增加；每次复审计前用 grep 重新枚举，不依赖本文件列出的历史位置。
