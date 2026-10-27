---
name: skill-repo-readme-placement
description: "当用户要求在 Skill 目录或 Skill 仓库根目录添加 README.md、CHANGELOG.md、INSTALLATION_GUIDE.md 或安装指南，或希望 GitHub 仓库首页出现展示文档时，先在临时副本上用真实校验器取证并出示布局 FAIL，再让用户在「保留并接受 RESULT FAIL / 移出 Skill 目录改用独立文档仓库或仓库 Description / 删除并提交以恢复 PASS」之间确认，最后对真实目录复跑 skill-file-qa、核对 Files (N)、RESULT、退出码、指纹与推送状态；用于 README 被 PROHIBITED_DOCS 判为 extraneous documentation、布局 8 pass 1 fail、删除 README 后恢复 9 pass、提交后 QA 失败、仓库根目录就是 Skill 根目录、CHANGELOG 或安装指南的同类冲突；不替代一般 QA（skill-file-qa）、提交流程（commit-skill-work）或发布流程（publier-skill-qoder-vers-depot-git）。"
---

# Skill 仓库展示文档的放置决策

## 目标与边界

处理「用户要求在 Skill 包根目录放 README、CHANGELOG 或安装指南」与「Skill 校验器禁止根级额外文档」之间的冲突：先在临时副本上取证，再让用户选择，最后复跑并如实报告。

本 Skill 不执行完整 QA、不代替提交流程、不发布仓库。QA 细节用 `skill-file-qa`，提交用 `commit-skill-work`，发布用 `publier-skill-qoder-vers-depot-git`。

## 1. 先读真实契约

不要凭记忆引用校验器文案。读取实际安装的校验器并记录路径、size、mtime、SHA-256：

```bash
VALIDATOR="$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py"
sha256sum "$VALIDATOR"
grep -n -E "ALLOWED_DIRS|PROHIBITED_DOCS|def check_layout" "$VALIDATOR"
```

然后逐行阅读 `check_layout`。截至 2026-10-25 的校验器（21,896 B，SHA-256 `1932ce48…6789d8`）行为是：

- `ALLOWED_DIRS = {"scripts", "references", "assets"}`；这些子目录内的文件不参与禁止名判断。
- `PROHIBITED_DOCS = {"README.md", "CHANGELOG.md", "INSTALLATION_GUIDE.md"}`，且只匹配**根级**文件。
- 根级禁止名 → `FAIL layout: extraneous documentation '<name>'`，退出码 1。
- 根级其他未知文件 → `WARN layout: unexpected file '<name>'`，同时仍输出 `PASS layout` 与 `RESULT PASS`，Summary 计 1 warn。

契约可能变化：常量、行号或退出码与上述不符时，以刚读到的实物为准，并停止使用本文的具体数字。

确认目标是 Skill 包，且仓库根就是 Skill 根：

```bash
test -f "$SKILL_DIR/SKILL.md" && echo "skill package"
git -C "$SKILL_DIR" rev-parse --show-toplevel
```

两者指向同一目录时，仓库根没有第二个可放 README 的位置；「放在仓库根但不在 Skill 根」不成立。

## 2. 区分用途

- 给 AI 或维护者看的使用说明：写入 `SKILL.md` 或 `references/`，不是仓库首页。
- 给 GitHub 访客看的展示文档：需要根级 `README.md`，与布局规则冲突。
- 两者都要：分别处理，不要用一份根级 README 冒充 Skill 资源。

在写任何真实文件前，先说明冲突，不要把「用户要求」当成绕过校验的理由。

## 3. 临时副本预检（不写真实包）

复制包内容（不含 `.git`）到临时目录，加入探针 README，运行真实校验器：

```bash
TMP_ROOT="$(mktemp -d)"
DEST="$TMP_ROOT/$(basename "$SKILL_DIR")"
mkdir -p "$DEST"
(cd "$SKILL_DIR" && tar --exclude=.git -cf - .) | (cd "$DEST" && tar -xf -)
printf '# Placement probe\n' > "$DEST/README.md"
py -3 "$VALIDATOR" "$DEST"
echo "RC=$?"
```

期望输出包含：

```text
FAIL layout: extraneous documentation 'README.md'
Summary: 8 pass, 1 fail, 0 warn
RESULT FAIL
RC=1
```

实际数字可能因校验项增减而变化；关键是该项 `FAIL` 与非零退出码。若没有出现，先排查常量是否变化、目标是否含 `SKILL.md`、副本是否包含其他根级禁止文件，不要继续按本文预期汇报。

每个探针都使用干净副本（或先移除上一个探针文件），并记录完整输出中的 `Files (N)`。`Files (N)` 必须等于布局行的 `file(s)` 计数，也必须等于副本实际文件数（基线文件数 + 本次新增数；基线本身为 0）；三者不一致时先修夹具或更正记录，不能只抄 `Summary`。

随后移除探针，确认基线，再清理临时目录：

```bash
rm "$DEST/README.md"
py -3 "$VALIDATOR" "$DEST"
echo "RC=$?"
rm -rf "$TMP_ROOT"
```

基线应为 `RESULT PASS`、退出码 0。清理前确认 `TMP_ROOT` 非空且位于系统临时目录；只删除本次 `mktemp -d` 创建的目录。

## 4. 出示三个选项

把预检原文、退出码和下列后果一起交给用户，等待明确选择：

| 选项 | 操作 | 结果 | 代价与限制 |
|---|---|---|---|
| A 保留 | 在真实包根目录写入并提交 README | QA 变成 `8 pass, 1 fail, 0 warn`、`RESULT FAIL`、退出码 1 | 后续任何报告不得称 PASS；提交、发布和交付说明都必须带上该 FAIL；包不再满足自身验收标准 |
| B 移出 | 放入独立文档仓库、上级目录，或改用 GitHub 仓库 Description | Skill 包保持 `9 pass, 0 fail` | 仓库首页没有 README，除非另有文档仓库；不要把它塞进 `references/` 来消 FAIL，那不是仓库首页，还会增加 Skill 上下文 |
| C 删除或回退 | `git rm README.md` 后新建提交；未提交的直接删除 | 恢复 `9 pass, 0 fail, 0 warn` | 已提交的历史仍保留该 blob；不擅自改写历史 |

补充规则：

- 未跟踪或未提交的 README 留在工作区同样会使 QA FAIL，不能静默保留。
- 用户选择 A 时，把 FAIL 写进交付报告，而不是描述成「仅布局提醒」。
- 用户选择 B 时，说明仓库首页仍为空；如需展示，使用仓库 Description 或独立文档仓库。
- 用户选择 C 且 README 曾推送过，默认追加删除提交；只有从未推送时才询问是否 amend 或改写，改写属于破坏性操作，需单独确认。

## 5. 确认与执行

- 会让真实包保留 FAIL，或要删除已跟踪文件时，先取得用户确认。
- 提交与推送只按用户指令执行；推送前用 `git status -sb` 与 `git log --oneline -3 origin/main` 核实本地领先或落后，不沿用旧结论。
- 提交按 `commit-skill-work` 的显式路径与指纹流程；发布按 `publier-skill-qoder-vers-depot-git`。
- 删除文件前查看 `git status`，确认没有其他未提交改动会被一并带走。

## 6. 复跑与取证

在真实目录上运行，不用临时副本的旧输出代替：

```bash
py -3 "$VALIDATOR" "$SKILL_DIR"
echo "RC=$?"
git -C "$SKILL_DIR" status -sb
git -C "$SKILL_DIR" log --oneline -3 origin/main
git -C "$SKILL_DIR" cat-file -e HEAD:README.md && echo "README PRESENT" || echo "README ABSENT"
git -C "$SKILL_DIR" ls-tree --name-only HEAD
```

必须记录：

- `Files (N)` 的完整清单、布局行、`Summary`、`RESULT`、退出码；`Files (N)` 与布局行的 `file(s)` 计数必须一致。
- `Fingerprint (start)` 与 `Fingerprint (final)`；校验器指纹只覆盖 `SKILL.md`，不覆盖 README。
- HEAD 树是否含 README、工作区是否干净、`origin/main` 是否已包含相关提交。
- 临时目录已删除，真实包内没有 README、CHANGELOG 或安装指南残留。

## 7. 禁止与失败处理

- 不得把 `RESULT FAIL` 说成 PASS，也不得省略布局行只报「其余通过」。
- 不得在未验证时宣称 GitHub 已展示 README；私有仓库在未登录浏览器中可能返回 404。
- 不得通过把文件改名为小写 `readme.md`、放入 `references/` 或加扩展名来规避布局检查；这些做法不解决展示需求，也会误导后续维护者。
- 校验器缺失、常量变化或目标缺 `SKILL.md` 时停止，报告实际观察，不猜测退出码。
- 历史改写、强推和删除分支不在本 Skill 的默认动作内；需要时先取得明确授权。

## 报告

| 项目 | 内容 |
|---|---|
| 请求 | 文件、目标路径、用途 |
| 契约 | 校验器路径、指纹、常量所在行、实际语义 |
| 预检 | 临时副本输出、`Files (N)`、布局行、Summary、退出码 |
| 决策 | A、B 或 C，以及用户确认依据 |
| 提交 | 提交号、是否已推送、`origin/main` 状态 |
| 最终 QA | `Files (N)`、布局行、Summary、RESULT、退出码 |
| 指纹 | SKILL.md 起止 size/mtime/SHA-256 |
| 历史 | README 是否仍在历史、是否改写 |
| 未验证 | 未执行的分支与原因 |

## 资源

- [references/cas-readme-placement-2026-10-26.md](references/cas-readme-placement-2026-10-26.md)：来源会话的实测输出、提交与 blob 哈希、校验器指纹，以及已核实、推断、未验证的分级记录。
