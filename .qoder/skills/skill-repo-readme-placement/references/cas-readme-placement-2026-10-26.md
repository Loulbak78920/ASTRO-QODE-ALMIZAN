# 案例档案：Skill 根目录 README 的布局冲突（2026-10-26）

记录来源会话中的真实冲突、提交与回退，以及本轮在临时副本上复跑的七种布局分支。结论分为 **已核实**、**推断**、**未验证**。

## 1. 来源会话

| 项目 | 值 |
| --- | --- |
| 会话 ID | `cc18d99f-8233-40d3-bd8c-7398d42ea3a3` |
| 标题 | 创建静态检查器 Skill |
| 项目 | `C:\Users\Administrateur\Desktop\IMAM8MAHDI` |
| 原始 JSONL | `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\cc18d99f-8233-40d3-bd8c-7398d42ea3a3.jsonl` |
| 观测时刻 | 2026-10-26T17:20:10+01:00 |
| JSONL size | 2,343,772 B |
| JSONL SHA-256 | `9bc69db16842db5d383c6b585800871527f23c35872a4d2f80049bcbb5f0928f` |
| revision | 22 |
| runtimeState | ready |
| 快照消息数 | 26 |
| hasMoreBefore | false |

**已核实**：该 JSONL 在本次分析期间仍在增长（17:19 时为 2,328,387 B，17:20 时为 2,343,772 B），因此上面的 size 与 SHA-256 只是观测时刻的值，不得当作稳定指纹。可复核证据以 git 提交、blob 哈希和真实命令输出为准。

## 2. 请求与失败回合

| 时间（UTC） | 事件 | 级别 |
| --- | --- | --- |
| 2026-10-26T16:10:33.637Z | 用户发送「提交一个 README.md」 | 已核实（JSONL 用户记录） |
| 随后 | 一个 assistant 回合 `status=failed`、正文为空 | 已核实（会话快照） |
| 2026-10-26T16:11:19.595Z | 出现续接记录，正文含「This session is being continued from a previous conversation that ran out of context」 | 已核实（JSONL 记录） |
| 续接后 | 用户再次发送同一请求「提交一个 README.md」 | 已核实（快照第 22 条消息） |
| 更后 | 用户发送「delete README.md and re-run tests」 | 已核实（快照第 24 条消息） |

**推断**：第一次请求之所以没有完成，是因为会话上下文耗尽后进入压缩续接；续接记录只说明「ran out of context」，没有单独的错误堆栈被本轮检查。不要把它写成「工具报错」或「权限拒绝」。

## 3. 已核实的提交与 QA

README 产物：

| 项目 | 值 |
| --- | --- |
| 路径 | Skill 根目录下的 `README.md` |
| size | 2,273 B |
| SHA-256 | `851e8545fdb87a4aacfcd1a900d16d3dd66f10c913ce3efa522002178aa8f147` |
| 提交 | `173a3c0` Add README describing the checker and matrix usage |
| 删除提交 | `fa1fef0` Remove README to restore skill layout contract |

**已核实**：从 `173a3c0` 重新导出 blob 后，字节数为 2,273、SHA-256 与上表完全一致。

添加 README 后的真实 QA 输出（会话工具输出原文）：

```text
Files (4): README.md, SKILL.md, references/cas-static-checker-2026-10-26.md, scripts/checker_matrix.py
FAIL layout: extraneous documentation 'README.md'
Summary: 8 pass, 1 fail, 0 warn
RESULT FAIL
RC=1
```

删除 README 后的真实 QA 输出：

```text
Files (3): SKILL.md, references/cas-static-checker-2026-10-26.md, scripts/checker_matrix.py
PASS layout: 3 file(s), no extraneous documentation
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
RC=0
```

**已核实（2026-10-26T17:21+01:00 复查）**：仓库 `develop-skill-static-checker` 的 `origin/main` 已包含 `fa1fef0`、`173a3c0`、`284dc90`，本地与远端同步（ahead 0）；`HEAD` 树只有 SKILL.md、references、scripts；`git cat-file -e HEAD:README.md` 返回 `fatal: path 'README.md' does not exist in 'HEAD'`。对真实目录复跑 QA 仍为 `9 pass, 0 fail, 0 warn`、`RESULT PASS`、RC=0。

## 4. 校验器契约

| 项目 | 值 |
| --- | --- |
| 路径 | `C:\Users\Administrateur\.qoder\skills\skill-file-qa\scripts\validate_skill.py` |
| size | 21,896 B |
| mtime | 2026-10-25T19:20:32+01:00 |
| SHA-256 | `1932ce4840054675f0608616e05f9f2c55db5eb749255f6a30c4cfd46e6789d8` |

**已核实**：第 35–36 行为：

```python
ALLOWED_DIRS = {"scripts", "references", "assets"}
PROHIBITED_DOCS = {"README.md", "CHANGELOG.md", "INSTALLATION_GUIDE.md"}
```

`check_layout` 从第 175 行开始：允许目录内的文件直接跳过；根级禁止名判 FAIL；其余根级文件判 WARN，并且因为没有禁止文档仍会输出 `PASS layout`。

**已核实（2026-10-26 复核）**：在校验器指纹未变（21,896 B、`1932ce48…6789d8`，`check_layout` 仍在第 175 行）的情况下，分别构造根级 `CHANGELOG.md` 与 `INSTALLATION_GUIDE.md` 夹具；两者均输出 `FAIL layout: extraneous documentation '<name>'`、`Summary: 8 pass, 1 fail, 0 warn`、`RESULT FAIL`、RC=1。

行号会随校验器版本移动；引用前重新读取实物。

## 5. 本轮临时副本实测

把 `develop-skill-static-checker` 的包内容（不含 `.git`）复制到 `mktemp -d` 创建的临时目录，副本目录名与 Skill 名一致，再逐一改变一个变量并运行同一个校验器。真实包未被修改，结束后临时目录已删除。

| 探针 | 变更 | Files | 布局行 | Summary | RC |
| --- | --- | --- | --- | --- | --- |
| A 基线 | 无 | 3 | `PASS layout: 3 file(s)` | 9 pass, 0 fail, 0 warn | 0 |
| B 根级 README | 根目录加入 `README.md` | 4 | `FAIL layout: extraneous documentation 'README.md'` | 8 pass, 1 fail, 0 warn | 1 |
| C 子目录 README | references 子目录加入 `README.md` | 4 | `PASS layout: 4 file(s)` | 9 pass, 0 fail, 0 warn | 0 |
| D 根级未知文件 | 根目录加入 `NOTES.txt` | 4 | `WARN layout: unexpected file 'NOTES.txt'` 加 `PASS layout: 4 file(s)` | 9 pass, 0 fail, 1 warn | 0 |
| E 小写文件名 | 根目录加入 `readme.md` | 4 | `WARN layout: unexpected file 'readme.md'` 加 `PASS layout: 4 file(s)` | 9 pass, 0 fail, 1 warn | 0 |
| F 根级 CHANGELOG | 根目录加入 `CHANGELOG.md` | 4 | `FAIL layout: extraneous documentation 'CHANGELOG.md'` | 8 pass, 1 fail, 0 warn | 1 |
| G 根级安装指南 | 根目录加入 `INSTALLATION_GUIDE.md` | 4 | `FAIL layout: extraneous documentation 'INSTALLATION_GUIDE.md'` | 8 pass, 1 fail, 0 warn | 1 |

**已核实（2026-10-26T17:36+01:00 独立复跑）**：探针 E 此前记为 `Files 3`、`PASS layout: 3 file(s)`，与「基线 3 个文件 + 新增 1 个」及布局行自相矛盾；本次复跑为 `Files (4)`、`PASS layout: 4 file(s)`，已按实测更正。探针 F/G 在各自的干净副本上分别实测，均得到 `FAIL layout`、`Summary: 8 pass, 1 fail, 0 warn`、`RESULT FAIL`、RC=1。记录探针结果时，`Files (N)`、布局行的 `file(s)` 计数与副本实际文件数必须三者一致，不能只抄 `Summary`。

**已核实**：探针 B 的完整输出与来源会话一致，均包含 `FAIL layout`、`Summary: 8 pass, 1 fail, 0 warn`、`RESULT FAIL`、RC=1。

**已核实**：探针 C 说明 `references` 子目录中的 README 不触发布局 FAIL；但它不会成为 GitHub 仓库首页的 README，因此不能作为展示需求的替代方案，也不应用来「消掉」FAIL。

**已核实**：探针 D 中 WARN 与 `PASS layout` 同时出现，`RESULT PASS`、RC=0，说明根级未知文件只是警告；不要把它误读为禁止文档也会通过。

**已核实**：探针 E 说明大小写不同的 `readme.md` 不匹配禁止集合，只得到 WARN 与 PASS。这里只记录校验器行为，不构成改名规避的建议；SKILL.md 已明令禁止这种做法。

## 6. 结论分级

**已核实**

- 根级 `README.md` 使 QA 变为 8 pass、1 fail、`RESULT FAIL`、RC=1。
- 删除后恢复 9 pass、0 fail、`RESULT PASS`、RC=0。
- README blob 的字节数与 SHA-256 可从提交 `173a3c0` 复算。
- 当前 `origin/main` 已包含添加与删除两个提交，HEAD 树没有 README。
- 本轮探针 A–G 的实际计数与退出码；F/G 与 README 走同一 FAIL 分支。
- 探针 E 的计数已按 2026-10-26 复跑更正为 `Files 4`、`PASS layout: 4 file(s)`。
- 校验器常量、`check_layout` 行为与文件指纹。

**推断**

- 第一次请求失败与上下文耗尽的因果关系（续接记录支持，但没有单独错误记录）。
- 私有仓库在未登录浏览器中返回 404，导致「页面看不到 README」不能证明文件不存在（会话中有 404 现象，但本轮未重测）。

**未验证**

- 改用 GitHub 仓库 Description 或独立文档仓库的实际展示效果。
- 改写历史以彻底移除 README blob 的效果；本轮没有任何历史改写。
- 会话中报告的夹具矩阵 12/12、`SIDE_EFFECTS PASS`、`CLEANUP OK`：本轮未复跑该矩阵，只把它记为会话报告。
- 其他校验器版本、其他 Skill 包或其他操作系统上的行为。

## 7. 时间限定

会话当时助手称「本地 main 领先 origin/main，尚未推送」。这是**当时**的状态，不是现在的事实：复查时两个提交都已存在于 `origin/main`。任何报告都应重新运行 `git status -sb` 与 `git log --oneline origin/main`，不要复制旧结论。

## 8. 复用要点

1. 先在临时副本上制造 README 并运行真实校验器，取得 FAIL 原文，再和用户讨论；不要先污染真实包。
2. 把「保留并接受 FAIL」「移出 Skill 目录」「删除并提交」三种后果连同退出码一起说明。
3. 选择删除时新建提交，默认不改写已推送的历史；历史中的 blob 仍可通过提交号取回。
4. 最后在真实目录复跑 QA，记录 `Files (N)`、布局行、Summary、RESULT、RC 与指纹，并单独核对 HEAD 树与远端状态。
5. 记录探针结果时同时核对 `Files (N)`、布局行的 `file(s)` 计数与副本实际文件数，不能只抄 `Summary`。
