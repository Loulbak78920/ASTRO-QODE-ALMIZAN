# Qoder 临时目录清理案例证据（2026-10-26）

案例日期：2026-10-26（UTC）
来源会话：`324c8787-9642-4d4e-a16c-2cf4834fb20c`（标题「更新 LF endings 技能」）
时区：会话消息与工具调用时间戳为 UTC（带 `Z`）；文件 mtime 为本地时间 Europe/Paris（UTC+1，带 `+01:00`）

## 来源读取记录

| 项 | 第一次读取 | 复核读取 |
|---|---|---|
| 时间 | 快照落盘于 2026-10-26T16:37:58Z | 2026-10-26T16:44–16:45Z（近似） |
| revision | 13 | 45 |
| runtimeState | waiting-user | ready |
| activeTurnId | 17499f71-515f-40f1-9897-23aa2ee6ffdf | null |
| pendingInteractionCount | 1 | 0 |
| hasMoreBefore | false | true（本次 `turnLimit=1`，窗口更窄） |
| 消息数 | 快照 messages 数组 22 条 | 仅返回最后 1 个用户回合 |

第一次读取使用 `turnLimit=20`、`includeToolOutputs=true`，输出约 155 666 字符，落盘为快照文件。第二次读取只用于确认清理之后会话继续推进；`revision` 从 13 增至 45，清理相关事实（16:19–16:33Z）未被改写，新增的是 16:36Z 之后的日志提交与 16:42:29Z 的第二次克隆清理。

## 被引用产物指纹（完整 SHA-256）

| 产物 | size | mtime（+01:00） | sha256 |
|---|---|---|---|
| 来源会话 JSONL | 1 946 398 B | 2026-10-26T17:42:44+01:00 | c24ad680d5961633001734fd44422a0c7d4067c2eba0f52f35d4c8b9df2fabc3 |
| `read_chat_session` 落盘快照 | 179 379 B | 2026-10-26T17:37:58+01:00 | 609c4aea2ee437f7f8428cac79b7fa6592e3174e1c6747e12eb929cf19a7c6e8 |

快照路径（临时产物，可能被清理）：
`C:/Users/Administrateur/.qoder/tmp/C--Users-Administrateur-Desktop-IMAM8MAHDI/a32c772d-8763-432a-83db-4472a36fc56e/tool-results/builtin_read_chat_session_609c4aea2ee4.txt`

JSONL 会随会话继续推进而增长；上表哈希只绑定 16:42:44Z 的采样点，不代表当前磁盘状态。

## 时间线（UTC）

| 时间 | 事件 | 证据 |
|---|---|---|
| 16:16:00 | 删除克隆 `pr-lock-lf.4v1Pgv`，输出 `TMP_REMOVED` | 工具输出 |
| 16:19:49 | 用户：「删除临时克隆目录」 | 消息原文 |
| 16:20:10 | 同一路径再次出现 sentinel 目录，4.0K | 工具输出 |
| 16:20:24 | 第二次删除 sentinel 目录，`RM_EXIT=0`、`REMOVED` | 工具输出 |
| 16:20:29 | `NO_PR_LOCK_LF_LEFTOVER`；源仓库 `## main` | 工具输出 |
| 16:21:35 | 用户：「检查其他临时目录是否有残留」 | 消息原文 |
| 16:21:53 | 顶层清单与 clone/empty 标记 | 工具输出 |
| 16:23:42 | 枚举 6 个嵌套 `.git`，检查 lock-lf 目录 | 工具输出 |
| 16:24:03 | 项目 tool-results 目录 51M；`publish-hsas.C2cx6c` 干净并跟踪 `origin/main` | 工具输出 |
| 16:24:15 | 项目/Skill 目录无 sentinel；`%TEMP%` 仅有 Qoder 内部文件 | 工具输出 |
| 16:24:37 | 发现 PR Skill 的 `scripts/__pycache__`，`?? scripts/__pycache__/` | 工具输出 |
| 16:24:57 | 按 basename 检索 6 个名称的引用会话 | 命令与输出 |
| 16:25:13 | 删除 `__pycache__`，`PYCACHE_REMOVED`，PR Skill 状态为空 | 工具输出 |
| 16:33:32 | 用户：「清理 lock-lf 证据文件和日志」 | 消息原文 |
| 16:33:39 | 7 个目标全部 `PRESENT` | 工具输出 |
| 16:33:46 | 7 个目标全部 `GONE`；`*lock-lf*` 残留 `NONE`；仓库 `## main` | 工具输出 |
| 16:36:32 | 用户：「提交本次验证结果到日志」 | 第二次读取 |
| 16:42:29 | 删除后出现的 `pr-lock-lf-update.1793032871`，输出 `NO_PR_OR_SENTINEL_RESIDUE` | JSONL 工具输出 |

## 1. 克隆删除与 sentinel 重建

16:16:00Z 的命令从 `pr-lock-lf-path.txt` 读取路径，删除克隆并在同一命令里删除路径文件：

```bash
TMP="$(cat "C:/Users/Administrateur/.qoder/tmp/pr-lock-lf-path.txt")" && \
git -C "C:/Users/Administrateur/.qoder/skills/lock-lf-endings-skill-repo" update-ref -d refs/qoder-tmp/base && \
git -C "C:/Users/Administrateur/.qoder/skills/lock-lf-endings-skill-repo" update-ref -d refs/qoder-tmp/head && \
chmod -R u+w "$TMP" && rm -rf "$TMP" && \
rm -f "C:/Users/Administrateur/.qoder/tmp/pr-lock-lf-path.txt" \
      "C:/Users/Administrateur/.qoder/tmp/pr-lock-lf-body.md" && \
if [ -e "$TMP" ]; then echo "TMP_STILL_EXISTS"; else echo "TMP_REMOVED"; fi
```

实际输出：

```text
TMP_REMOVED
== source repo ==
## main
76a011d63f1abe62daae0d6ec6246cbd49966822
```

## 2. sentinel 再次出现与被删除

16:20:10Z 检查同一路径：

```text
== exists ==
YES
== contents ==
C:/Users/Administrateur/.qoder/tmp/pr-lock-lf.4v1Pgv
C:/Users/Administrateur/.qoder/tmp/pr-lock-lf.4v1Pgv/system-commandline-sentinel-files
C:/Users/Administrateur/.qoder/tmp/pr-lock-lf.4v1Pgv/system-commandline-sentinel-files/dotnet-suggest-registration-git-credential-manager, Version=2.6.1.0, Culture=neutral, PublicKeyToken=null
== du ==
4.0K	C:/Users/Administrateur/.qoder/tmp/pr-lock-lf.4v1Pgv
```

16:20:24Z 用字面路径删除：

```text
RM_EXIT=0
REMOVED
== other sentinel dirs in tmp ==
```

最后一行之后没有输出，说明当时 `~/.qoder/tmp` 下 `maxdepth 3` 内没有其他 sentinel 目录。16:20:29Z 复查：

```text
NO_PR_LOCK_LF_LEFTOVER
## main
```

结论：克隆内容在 16:16:00Z 已删除；16:20:10Z 同一路径再次存在一个 4.0K 的空父目录加 sentinel 目录。重建发生在两次观察之间，具体时刻未直接记录。

## 3. 清点与归属

16:21:53Z 的顶层清单给每个条目打 `DIR`/`FILE`、size、mtime、`GIT_CLONE`/`EMPTY` 标记。与本案相关的条目包括：

- `publish-hsas.C2cx6c`：167K，内含 `repo`，16:24:03Z 的 `git status -sb` 为 `## main...origin/main`。
- 项目缓存目录 `C--Users-Administrateur-Desktop-IMAM8MAHDI`：51M，内含 `tool-results` 与 `.last-skill-backup-path`、`.last-skill-baseline-path`。
- `%TEMP%` 下 `qoder-*-cwd` 与 `qoder-cli-error-*.json`：Qoder 内部文件，未删除。

16:23:42Z 的嵌套仓库清单：

```text
find-stale-test-blez0hd0/other/.git
find-stale-test-blez0hd0/repo/.git
publish-hsas.C2cx6c/repo/.git
qualify-skill-test-20261026T1605/.git
qualify-skill-test-20261026T1605/repo/.git
refs-fixture-manual/work/.git
```

16:24:57Z 的归属命令：

```bash
cd "C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI" && \
for name in "live-audit-lock-lf" "lock-lf-audit-20261026" "lock-lf-commit-20261026" \
            "fingerprints-lock-lf-endings-skill-repo" "qa-lock-lf-commit.log" "qa-lf.log"; do
  echo "--- $name ---"
  grep -l "$name" *.jsonl 2>/dev/null | head -5
done
```

输出（会话 basename）：

```text
--- live-audit-lock-lf ---
324c8787-9642-4d4e-a16c-2cf4834fb20c.jsonl
4a76ef0e-4fcc-4bc3-8abc-a2ecb318767e.jsonl
4f9f7998-3d1a-4b34-af42-817dbb682d29.jsonl
cc18d99f-8233-40d3-bd8c-7398d42ea3a3.jsonl
eb08197b-4817-47f6-8a0d-e122c9bbc6ff.jsonl
--- lock-lf-audit-20261026 ---
324c8787-9642-4d4e-a16c-2cf4834fb20c.jsonl
4f9f7998-3d1a-4b34-af42-817dbb682d29.jsonl
a6127096-ec1b-47db-9621-f195d0df19e3.jsonl
cc18d99f-8233-40d3-bd8c-7398d42ea3a3.jsonl
--- lock-lf-commit-20261026 ---
324c8787-9642-4d4e-a16c-2cf4834fb20c.jsonl
4f9f7998-3d1a-4b34-af42-817dbb682d29.jsonl
a6127096-ec1b-47db-9621-f195d0df19e3.jsonl
cc18d99f-8233-40d3-bd8c-7398d42ea3a3.jsonl
--- fingerprints-lock-lf-endings-skill-repo ---
0dbf67b4-3052-4928-94d7-bb6e5a68ca1b.jsonl
25d73915-7d7e-4142-831a-12fe9738b8f1.jsonl
324c8787-9642-4d4e-a16c-2cf4834fb20c.jsonl
3677d3d4-c450-45c6-b00e-4f16329cce18.jsonl
4a76ef0e-4fcc-4bc3-8abc-a2ecb318767e.jsonl
--- qa-lock-lf-commit.log ---
324c8787-9642-4d4e-a16c-2cf4834fb20c.jsonl
4f9f7998-3d1a-4b34-af42-817dbb682d29.jsonl
--- qa-lf.log ---
324c8787-9642-4d4e-a16c-2cf4834fb20c.jsonl
4f9f7998-3d1a-4b34-af42-817dbb682d29.jsonl
ae97a7bf-2013-4366-b5ed-20d659cc2808.jsonl
cc18d99f-8233-40d3-bd8c-7398d42ea3a3.jsonl
ef2d6bc1-abb7-49b0-b0ef-ccfdeafa4754.jsonl
```

`head -5` 会截断；上表是当时的完整可见结果。检索只覆盖一个项目目录；本次补充检查时 `~/.qoder/projects` 下也只有这一个项目目录。7 个待删项中的 `qa-lf-20261026.log` 没有出现在这次 `grep` 名单中。

补充复核（2026-10-26T16:44Z，撰写本档案时）：`grep -F -l -- "publish-hsas.C2cx6c" */*.jsonl` 返回 5 个会话（含 `324c8787…` 与当前会话）。这只能说明命名被多个会话提到，会话是否仍在写未核验。引用计数会随新会话增加，不是稳定属性，也不能作为删除依据。

## 4. `__pycache__`

16:24:37Z：

```text
== PYCACHE IN TOUCHED SKILLS ==
C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh/scripts/__pycache__
C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh/scripts/__pycache__/github_pr_api.cpython-314.pyc
DONE_PYCACHE
== PR SKILL STATUS ==
?? scripts/__pycache__/
== LOCK SKILL STATUS ==
```

16:25:13Z 删除：

```text
== before ==
2026-10-26 17:12:54.699382400 +0100 C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh/scripts/__pycache__
RM_EXIT=0
PYCACHE_REMOVED
== pr skill status ==
== lock skill status ==
## main
```

`pr skill status` 之后为空，说明 `?? scripts/__pycache__/` 已消失。

## 5. 七个证据与日志的删除

用户 16:33:32Z 的指令是「清理 lock-lf 证据文件和日志」。16:33:39Z 确认：

```text
== BEFORE ==
PRESENT 15K live-audit-lock-lf
PRESENT 4.0K lock-lf-audit-20261026
PRESENT 5.0K lock-lf-commit-20261026
PRESENT 1.0K fingerprints-lock-lf-endings-skill-repo.txt
PRESENT 4.0K qa-lf-20261026.log
PRESENT 4.0K qa-lf.log
PRESENT 4.0K qa-lock-lf-commit.log
```

16:33:46Z 删除后：

```text
== AFTER ==
GONE  live-audit-lock-lf
GONE  lock-lf-audit-20261026
GONE  lock-lf-commit-20261026
GONE  fingerprints-lock-lf-endings-skill-repo.txt
GONE  qa-lf-20261026.log
GONE  qa-lf.log
GONE  qa-lock-lf-commit.log
== REMAINING *lock-lf* IN TMP ==
NONE
== SKILL REPO ==
## main
```

删除命令对三个目录先 `chmod -R u+w` 再 `rm -rf`，对四个文件使用 `rm -f`，并在同一命令里复查。

## 6. 后出现的第二个克隆

第二次读取（revision 45）对应的回合里，16:42:29Z 又执行了一次清理：

```text
REMOVED
NO_PR_OR_SENTINEL_RESIDUE
9024d7d3229e8635832cbc7e5775268e649c5d1a docs(skill): consigner la verification HEAD du 2026-10-26
```

这说明清理完成后仍可能出现新的临时克隆，需要在收尾时再扫一次。

## 用户回合与纠正归属

| 时间 | 用户原文 | 性质 |
|---|---|---|
| 16:19:49Z | 删除临时克隆目录 | 新请求：第一次删除后 sentinel 重建，用户再次要求清理 |
| 16:21:35Z | 检查其他临时目录是否有残留 | 新请求：扩大检查范围，发现 `__pycache__` |
| 16:33:32Z | 清理 lock-lf 证据文件和日志 | 新请求：明确点名共享证据范围 |
| 16:36:32Z | 提交本次验证结果到日志 | 后续请求，非清理；引出了 16:42:29Z 的第二次克隆清理 |

本案没有记录用户对技术方法的否定或改写；三次清理请求都是范围追加，不是对前一步骤的纠错。

## 分级

| 结论 | 分级 | 依据 |
|---|---|---|
| 16:16:00Z 删除克隆成功 | 已核实 | 工具输出 `TMP_REMOVED` |
| 16:20:10Z 同一路径存在 sentinel 目录与 GCM 注册文件 | 已核实 | 工具输出逐字列出路径与文件名 |
| 16:20:24Z sentinel 删除成功且无其他 sentinel | 已核实 | `RM_EXIT=0`、`REMOVED`、扫描无输出 |
| sentinel 由 Git Credential Manager 重建 | 推断 | 目录名、内部文件名与 PR Skill 的已知陷阱一致；未对 GCM 做进程级观测 |
| 重建发生在 16:16–16:20Z 之间 | 推断 | 两次观察夹逼；未记录具体时间 |
| `__pycache__` 在 16:24:37Z 存在、16:25:13Z 删除 | 已核实 | `stat`、`?? scripts/__pycache__/`、`PYCACHE_REMOVED` |
| `__pycache__` 由 17:12 本地时间的脚本导入产生 | 推断 | `.pyc` 目录 mtime 与助手叙述一致；无导入调用日志 |
| 6 个名称的 JSONL 引用会话 | 已核实 | 命令与输出 |
| 7 个证据项删除成功 | 已核实 | `PRESENT` 与 `GONE` 对照、`NONE`、`## main` |
| 删除 7 项对其他会话无影响 | 未验证 | 未检查引用会话的实时状态与证据链 |
| 引用会话在删除时是否活跃 | 未验证 | 未在删除时调用会话状态工具 |
| `qa-lf-20261026.log` 的共享范围 | 未验证 | 该名称未进入 16:24:57Z 的检索名单 |
| JSONL 检索覆盖所有项目 | 未验证（当前只有一个项目目录） | 当时只在一个项目目录执行；本次补充检查仍只有一个 |
| GCM 重建可稳定复现 | 未验证 | 未主动制造第二次重建 |
| `py -3 -B` 能预防缓存 | 未验证 | 来源会话只验证了删除结果 |

## 边界与未覆盖

1. 归属检索使用 basename，可能把「同名但不同路径」的条目算进来；本案路径均带独特前缀，未发现歧义。
2. `grep` 只检索文本中的命名，不证明会话是否仍在使用该文件；「引用」不等于「依赖」。
3. 7 个证据项被删除是用户明确指令的结果；没有证据表明其他引用会话已经完成，也没有证据表明它们会因此失败。
4. `publish-hsas.C2cx6c` 被判定为其他会话的干净克隆，依据是 `## main...origin/main`、167K 内容与最近 mtime；没有读取使用它的会话回合。
5. 项目 tool-results（51M）与 `%TEMP%` 中的 Qoder 文件按应用托管处理，未删除，也未验证应用是否会自动清理。
6. 本档案不绑定 Skill 自身哈希；`SKILL.md` 的 QA 指纹与参考文件哈希在写入后的报告中分别记录。

## 当前磁盘状态观察（非案例结论）

写入本档案前的只读观察：2026-10-26T16:44:08Z，`~/.qoder/tmp` 为 56M，`~/.qoder/projects` 下有 204 个 JSONL；7 个 lock-lf 项与 `pr-lock-lf*` 均不存在；`maxdepth 4` 内无 sentinel 目录。该观察只对应这一时刻，之后可能变化。

## 补充观测（独立核实，2026-10-26）

- 2026-10-26T17:50+01:00 对最终版本做只读复核：`~/.qoder/tmp` 56M、顶层 98 项、`~/.qoder/projects` 下 205 个 JSONL、`maxdepth 5` 内 5 个嵌套 `.git`、sentinel 0 个；`publish-hsas.C2cx6c` 已不存在。顶层项与 JSONL 数在会话运行期间会漂移，不能作为固定契约。
- 验收片段的 `.git` 计数：`maxdepth 1` 返回 0，`maxdepth 5` 返回 5。前者看不到 `tmp/<夹具>/.git` 与 `tmp/<夹具>/repo/.git`，`SKILL.md` 已改为 `maxdepth 5` 并同时输出 sentinel 计数。
- 2026-10-26T16:56Z 复跑验收片段：`BASE_OK`、`SENTINELS=0`、`NESTED_GIT=16`（17:50 为 5）。期间新建了多个并发夹具，确认嵌套 `.git` 计数会漂移；`SKILL.md` 已去掉固定数字，只保留「清点基线」说明。
- 2026-10-26T16:56Z 独立复验自引用探针：探针 `probe-20261026T1656-80685b8f` 只命中 `80685b8f-6be5-4af6-ba89-3c72605f79a7.jsonl`，与上一条结论一致。
- 自引用探针：先输出 `SELFREF_PROBE=probe-20261026T1748-a55b50cd`，再 `grep -F -l` 全部项目 JSONL，只命中 `a55b50cd-9364-4e76-bf0b-cb5df28625d5.jsonl`。该会话 JSONL 对 `pr-lock-lf.4v1Pgv`、`live-audit-lock-lf`、`publish-hsas.C2cx6c` 分别命中 11、9、10 次，证明当前会话自身会把候选名写入记录；归属计数必须排除它。该探针法已写入 `SKILL.md` Step 2。
- 用户消息「提交本次验证结果到日志」：快照时间 16:36:32.378Z，JSONL 记录 16:36:39.334Z；上方时间线保留快照时间，JSONL 记录以此为准。
- GCM 重建仍为推断：只观察到 sentinel 目录与 `dotnet-suggest-registration-git-credential-manager` 注册文件名，未做进程级观测，未主动复现。

## 命名说明

原方案中的参考文件名为 `cas-session-324c8787.md`；按证据档案命名规范 `cas-<sujet>-<YYYY-MM-DD>.md` 改为 `cas-nettoyage-temp-qoder-2026-10-26.md`，内容范围未变。

## 脚本增量（接管后，2026-10-26T16:56Z）

### 接管与基线

- 目标 `nettoyer-artefacts-temp-qoder` 保持不存在（`TARGET_ABSENT`）。按用户决定「接管现有并补脚本」，以 `auditer-nettoyer-temp-qoder` 为唯一归属，不创建新目录。
- 本次增量写入前基线：`SKILL.md` 15,237 B、SHA-256 `a50675006224097e087442aecc988cbefac6337974ebdb499743088978b8beb7`、mtime 2026-10-26T17:52:24+01:00；参考 15,434 B、SHA-256 `b27f60a3ed44635b4b07624e4a50ea674389cfd9c61d4c3ce606e1daeb0b9bb2`、mtime 17:52:15+01:00。
- 写入期间其他会话仍在更新参考文件：17:55:16+01:00 新增两条观测（16:56Z 复跑验收片段、自引用探针复验）。本档案只追加，不覆盖这些并发内容。

### 脚本契约

`scripts/inventorier_tmp_qoder.py`：14,299 B、SHA-256 `6168ca52ea85e3f46c4d81e5bca7e6a1165ee7095527710a83edca3e950fb884`、mtime 2026-10-26T17:57:19+01:00。

| 项 | 说明 |
|---|---|
| 参数 | `--root`（默认 `~/.qoder/tmp`）、`--max-depth`（默认 5）、`--recent-minutes`（默认 60）、`--entry-limit`（默认 200000）、`--json` |
| 文本输出 | `ROOT`、`GENERATED_AT`、`MODE READ_ONLY`、`RESULT`、`TOTALS`、`MARKERS`、`ENTRIES`、`NESTED_GIT`、`SENTINEL_DIRS`、`PYCACHE` |
| JSON 输出 | 单个对象、`ensure_ascii=True`，含 `totals`、`markers`、`entries`、`errors`、`truncated` |
| 标记 | `.git` 目录与 `.git` 文件都记入 `nested_git`；`system-commandline-sentinel-files`；`__pycache__` 目录与 `.pyc` 文件 |
| 深度语义 | `--max-depth` 只限制标记扫描；size 始终递归统计 |
| 只读 | 不删除、不移动、不写入；不跟随符号链接；只用 lstat 与 scandir 读取 |
| 退出码 | 0 = `OK` 或 `PARTIAL`；2 = `FAIL`（`ROOT_MISSING`、`ROOT_NOT_DIR`、`ROOT_UNREADABLE`、参数错误） |
| PARTIAL | 扫描错误或超过 `--entry-limit`（`truncated=yes`） |

### 夹具与真实运行

夹具位于 `%TEMP%`，路径模式 `tmpqoder-fixture.PzTaX0`，包含 `alpha/repo/.git/`、`beta/.git`（文件）、`gamma/system-commandline-sentinel-files/`、`gamma/scripts/__pycache__/*.pyc`、`empty-top/`、`delta.txt` 与中文文件名。测试后已删除。

| 用例 | 结果 |
|---|---|
| `--max-depth 5` 文本 | `RESULT OK`；entries=16、dirs=11、files=5、size_bytes=45、top_entries=6；`MARKERS nested_git=2 sentinel_dirs=1 pycache_dirs=1 pyc_files=1`；`empty-top` 输出 `empty=yes`；`beta` 输出 `git=root`；中文文件名以 `\uXXXX` 转义 |
| `--max-depth 1` | `MARKERS` 全部为 0，证明深度限制生效 |
| `--json` | 断言通过：`result=OK`、`read_only=true`、markers 2/1/1/1、`size_bytes=45`、`top_entries=6`、每条 `recent` 为布尔值 |
| 缺失根目录 | `RESULT FAIL`、`ERROR ROOT_MISSING`、退出码 2 |
| 文件当根目录 | JSON `error=ROOT_NOT_DIR`、退出码 2 |
| `--max-depth 0`、`--recent-minutes -1` | argparse 用法错误，退出码 2 |
| 只读性 | 运行前后 `find -printf '%P\|%y\|%s\|%T@'` 快照 `diff` 为空（`FIXTURE_UNCHANGED`） |
| 真实根 | `~/.qoder/tmp`：`RESULT OK`，102 个顶层条目、1869 个条目、738 目录、1131 文件、56,898,528 B（54.3M）；markers `nested_git=16`（14 目录 + 2 文件）、sentinel 0、`__pycache__` 0、`.pyc` 0、errors 0；`find -maxdepth 5` 得 14 个目录 + 2 个文件，与脚本一致；耗时 0.58 s |

### 静态验收

`validate_skill.py` 在 `SKILL.md` 指纹 `d2064196d038b3f35fd63cfab5f69baeb9c89498cfb199f1c9a342890f7153e8`（18,131 B，17:59:03+01:00）上报告 `RESULT PASS`：9 PASS / 0 FAIL / 0 WARN，`Files (3)`，正文 281 行，description 378 字符，本地引用 2、跨 Skill 引用 6，校验期间指纹未变。`Code blocks: python=0`，脚本语法由 `ast.parse` 单独验证。

### 归类

| 结论 | 分级 | 依据 |
|---|---|---|
| 脚本可解析、可在真实根运行 | 已核实 | `ast.parse` 通过；真实根退出码 0 |
| 空目录与 `.git` 文件识别 | 已核实 | 夹具 `empty-top` 与 `beta` 输出 |
| 深度限制生效 | 已核实 | `--max-depth 1` 与 5 的 markers 对比 |
| 失败路径退出码 2 | 已核实 | 四次负例 |
| 夹具层面只读 | 已核实 | 快照 diff 为空；代码只用 lstat/scandir 与输出 |
| 脚本不判定归属、不删除 | 已核实 | 代码不含删除或写盘调用 |
| 并发写入下的最终性 | 未验证 | 写入期间多个会话仍为 `running`；计数只对单次运行有效 |
| GCM 重建可复现 | 未验证 | 本次未制造删除后重建 |

### 边界

1. 脚本不读取 JSONL，不输出 `APP-MANAGED`、`OTHER-SESSION`、`SHARED`、`CURRENT`、`UNKNOWN`；归属仍由 `SKILL.md` Step 2 与用户确认完成。
2. `size` 递归统计大目录可能变慢；`--entry-limit` 只提供有界失败，不保证截断后的统计完整。
3. cp1252 控制台下文本模式把不可编码文件名转义为 `\uXXXX`；JSON 模式始终为 ASCII。
4. 真实根计数随其他会话创建或清理夹具漂移；本节数字只绑定 16:56Z 的运行。
5. 未检查各引用会话在删除时的实时写入状态，也未验证 `py -3 -B` 对缓存的预防效果。

