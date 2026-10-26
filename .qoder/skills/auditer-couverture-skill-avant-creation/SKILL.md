---
name: auditer-couverture-skill-avant-creation
description: "在采纳「新建 Skill」推荐或开始写 SKILL.md 前，先审计已安装能力是否已覆盖：冻结推荐中的能力声明与否证句，枚举用户级与项目级全部 Skill 根，从 summary/rationale 提取高区分度能力 token（命令旗标、输出键、错误串、函数名、环境变量及中英法同义词），用只读脚本跨 SKILL.md、references 与 scripts 检索，再逐条读取规范条款与实现函数，判定 COVERED/PARTIAL/ABSENT/CONFLICT/UNSTABLE 并记录 file:line 与文件哈希；COVERED 改为更新现有 Skill，PARTIAL 收窄新 Skill 范围并写「不用于」与委派边界，ABSENT 才新建，CONFLICT 停止并列双方原文；方案定稿前与写入前各做一次全根快照，审计对象指纹变化时先采样至稳定，否则结论标 STALE；同时用磁盘命中反证推荐 rationale 的「现有 Skill 均未覆盖」。用于自动推荐 action=create、推荐声称若干 Skill 未覆盖、按记忆只查几个相邻 Skill、只 grep SKILL.md 漏掉 scripts 中的门禁、把提及当覆盖、创建前决定新建还是更新、避免近重复 Skill。English: audit capability coverage before creating a skill, installed skills overlap, avoid duplicate skill, grep rules and scripts, coverage matrix, file:line evidence. Français: auditer la couverture des compétences avant de créer un Skill, chevauchement entre Skills, matrice de couverture. 不替代并发重复接管（adopt-concurrent-duplicate-skill）、推荐声明与来源会话对账（verify-skill-recommendation-claims）、清单计数（inventory-installed-skills）、写入后验收（skill-file-qa）。"
---

# 创建前的能力覆盖审计

## 目标与边界

在写新 Skill 之前，用磁盘证据回答一个问题：**现有已安装 Skill 是否已经覆盖这项能力**。命中不是结论，必须同时读到规范条款与实现；只命中文档、没有断言或分支，只能判 `PARTIAL`。

本 Skill 证明：枚举是否完整、token 命中了哪些文件、每个命中是条款还是实现、覆盖判定与新建/更新决策是否一致。它**不**证明来源会话里的声明真实（交给 `verify-skill-recommendation-claims`），不处理同名目录并发接管（交给 `adopt-concurrent-duplicate-skill`），不负责 Skill 数量口径（交给 `inventory-installed-skills`），也不替代写入后的 `skill-file-qa`。

## 何时使用

- 自动推荐 JSON 带 `action=create`，尤其 rationale 含「现有 X/Y 未覆盖」「均未设独立门禁」「只讲设计」。
- 已经按记忆挑了几个相邻 Skill，准备据此下结论。
- 只 grep 了 `SKILL.md`，没有检查 `references/` 或 `scripts/`。
- 命中一个 Skill，但不确定是「提及」还是「承重门禁」。
- 创建前需要决定：新建、收窄后新建，还是更新现有。

不用于：目标目录已出现（转 `adopt-concurrent-duplicate-skill`）；目标中途出现后的活性分级（转 `audit-skill-during-live-creation`）；只数数量（转 `inventory-installed-skills`）；写入后格式验收（转 `skill-file-qa`）。

## 不可协商规则

1. **全量枚举，以磁盘为准。** 枚举用户级与项目级所有含 `SKILL.md` 的目录，不信任加载列表、description 或记忆；内置/插件只作声明，不进入磁盘命中统计。
2. **三层都扫。** `SKILL.md`、`references/**`、`scripts/**`。门禁常在脚本里：`audit-skill-tool-contracts` 的 `before == after` 就在其 `audit_contracts.py`，只扫文档必漏。
3. **提及不等于覆盖。** 每个命中读两处：规范条款（规则、步骤、表格）与实现（函数、断言、CLI 分支）。命中分三级：只提到关键词、有规则但没有可执行步骤、完整流程与验收；只有第三级可判 `COVERED`，第二级最多 `PARTIAL`。只有条款没有实现、或只有实现没有条款，同样判 `PARTIAL`，因为另一代理不会照做。
4. **推荐是线索，不是证据。** rationale 的否定句必须被磁盘命中反证；不得用推荐自证，也不得把「推荐说四个 Skill 都没覆盖」当成已枚举。
5. **多语同义词。** 中文、英文、法文、缩写、旧名都要检索。0 命中先换同义词，再判 `ABSENT`。
6. **版本绑定。** 记录 `file:line`、文件 SHA-256、枚举时间。行号只在记录的哈希窗口内有效。
7. **只读。** 审计本身不写任何 Skill 目录；快照只写 `~/.qoder/tmp` 并在用后删除；不产生 `__pycache__`。
8. **并发标记。** 命中包正在被写入时判 `UNSTABLE`，不作为最终覆盖结论。
9. **决策先于写入。** `COVERED` 不得新建；`PARTIAL` 必须收窄并写委派；只有 `ABSENT` 才进入 `skill-creator` 的 create。
10. **历史 Skill 不可得时不臆造。** 先找本地备份、删除记录与会话 JSONL 中的 Write/Edit；能恢复的版本按字节数与 SHA-256 核对后保留有效规则，取不到的才标 `UNVERIFIED`，只保留可核实的名称、能力与最后观察到的路径/大小。
11. **不复制第二份事实源。** 已覆盖的规则只在正文写一句用途与 Skill 名，不复制步骤；同一规则只保留一个属主。
12. **两次全根快照。** 方案定稿前与写入前各枚举一次两个 skills 根，记录目标 `SKILL.md` 的 size、mtime、SHA-256；两次 diff 为空才沿用矩阵，出现新增或变化先按 0c 稳定并重跑矩阵。
13. **指纹未稳不定案。** 审计对象在初读后变化时，至少连续 3 次采样一致才算稳定；未稳定前矩阵标 `STALE`，不得据此选择 create/update；超时仍变化则停写并报告 `CHANGING`。
14. **基线已存在不等于并发。** 基线时已存在、且属主与指纹可核实并一致的目标按 update 处理；指纹一致但属主/来源冲突或无法核实，标 `UNVERIFIED` 交用户；只有审计期间新出现或基线后指纹变化才进入稳定门禁与接管判断。
15. **声明资源先于委派。** 对新出现或刚修改的相邻 Skill，交叉引用其脚本或参考文件前先核对具名文件是否存在、目录是否为空、是否仍在变化；缺失时只引用思路、不调用脚本，并在矩阵标 `UNVERIFIED`。
16. **来源断言独立复跑。** 来源会话的退出码、计数、URL 等关键断言若只有二手摘要，标 `UNVERIFIED` 并只读复跑无害分支；复跑 `skill-file-qa` 用位置参数，要求 `RESULT PASS`、rc=0、`skill references: N checked` 与 `Files (N)` 的 N 精确匹配；`0 found`/`0 checked` 是假 PASS（`--skill` 会被 argparse 缩写为 `--skills-root`）。

## 流程

围栏示例只用具名变量。带参数调用时，注入层会把正文中的位置变量替换成实参文本（磁盘不变）；复跑以磁盘原文为准。

### 0. 基线与两次快照

```bash
snap() {
  for root in "$HOME/.qoder/skills" "<workspace>/.qoder/skills"; do
    [ -d "$root" ] || continue
    find "$root" -mindepth 2 -maxdepth 2 -name SKILL.md -print0 |
      while IFS= read -r -d '' f; do
        printf '%s|%s|%s|%s\n' "$f" "$(stat -c '%s' "$f")" \
          "$(stat -c '%y' "$f")" "$(sha256sum "$f" | cut -d' ' -f1)"
      done
  done | sort
}
snap > "$HOME/.qoder/tmp/snap-plan.txt"    # 方案定稿前
snap > "$HOME/.qoder/tmp/snap-pre.txt"     # 用户确认后、写入前
diff -u "$HOME/.qoder/tmp/snap-plan.txt" "$HOME/.qoder/tmp/snap-pre.txt" || true
```

- `diff` 为空：沿用第一次矩阵。
- 出现新增或变化：先按 0c 稳定，再读其当前 `SKILL.md` 并重跑矩阵；声明资源按规则 15 核对。
- 目标从不存在变为存在，或基线指纹变化：冻结写入；稳定后仍属职责重合再转 `adopt-concurrent-duplicate-skill`。
- 目标基线已存在且两次指纹一致：按 update 继续，不转 adopt。
- 快照只写 `~/.qoder/tmp`，用后删除并确认不存在。

### 0c. 稳定性门禁

1. 对相关文件记录 size、mtime、SHA-256；至少连续 3 次采样一致才算 `STABLE`。
2. 未稳定时矩阵标 `STALE`，不得进入决策。
3. 稳定后完整重读 `SKILL.md`、references 与 scripts，重跑矩阵；`file:line` 只取稳定版本。
4. 会话状态按 `audit-skill-during-live-creation` 记录；cold 不排除其他写入者，仍以指纹为准。
5. 超时仍变化：停写，报告 `CHANGING` 与采样记录。

### 1. 冻结能力声明

从推荐 JSON 抄出 `skillName`、`summary`、`rationale`，把否定句拆成可检验的能力声明：

- `C1`：现有 Skill 未把「变异已应用」设为独立运行前门禁。
- `C2`：现有 Skill 只讲变异设计，没有断言副本已改变。
- `C3`：现有 Skill 没有跨全部已安装 Skill 的能力覆盖枚举。

每条声明写清主语与范围。来源真实性交给 `verify-skill-recommendation-claims`；本步骤只负责把「未覆盖」变成可 grep、可读代码的句子。

### 2. 枚举全部 Skill 根

```bash
SKILL_DIR="$HOME/.qoder/skills/auditer-couverture-skill-avant-creation"
PYTHONIOENCODING=utf-8 py -3 "$SKILL_DIR/scripts/audit_coverage.py" --list-skills
```

期望输出 `SKILLS <n> (user=<u> project=<p>)`，且 `n=u+p`。项目级根默认取当前工作区最近的 `.qoder/skills`；不存在时显示 `project=none`。若 `n` 与磁盘 `find` 数不一致，先停下查根，不要继续判定。

### 3. 提取能力 token

选 3–8 个高区分度 token，优先：

- 输出键/断言词：`OLD_OCCURS`、`COPIES_CHANGED`、`mutation ineffective`。
- 命令旗标/参数：`--anchor`、`--old-hex`、`--yes`。
- 错误串/状态词：`NOT_APPLIED`、`INERT`、`TARGET_DRIFT`。
- 函数/变量名：`apply_mutation`、`before == after`。
- 领域名词及同义词：`变异` / `mutation` / `mutant`；`覆盖` / `couverture` / `coverage`。

避免 `skill`、`脚本`、`--help` 这类泛词。中文两字词可以保留；ASCII 两字词（如 `ls`）会被脚本拒绝。

### 4. 跨文件检索

```bash
PYTHONIOENCODING=utf-8 py -3 "$SKILL_DIR/scripts/audit_coverage.py" \
  --token "before == after" --token "mutation ineffective" \
  --token 变异 --token 覆盖
```

读取输出中的 `TOKEN ... occurrences=... skills=...` 与 `HIT skill|file|line|text`。

- `WARN TOKEN_NO_HIT` 只说明该写法未命中；换同义词再查，不能直接判 `ABSENT`。
- `WARN TOKEN_TOO_GENERIC` 说明 token 太泛；收紧到断言、旗标或函数名后再查。
- `RESULT PARTIAL` 表示有文件读失败；先解决读取问题，再下结论。

### 5. 读上下文并判定

对每个命中 Skill，读规范条款与实现函数，填矩阵：

| 能力声明 | Skill | 规范条款 | 实现 | 判定 | 增量与动作 |
|---|---|---|---|---|---|
| C1 变异已应用门禁 | audit-skill-tool-contracts | SKILL.md:35（规则 8） | scripts/audit_contracts.py:1127-1128 | COVERED | 无增量，只写交叉引用 |
| C2 只讲设计无断言 | 某 Skill | SKILL.md:... | 无 | PARTIAL | 新 Skill 补可执行检索与判定 |
| C3 全量覆盖枚举 | 无 | 无 | 无 | ABSENT | 写入本 Skill 流程 |
| C4 两 Skill 说法冲突 | A / B | A:... / B:... | 相反断言 | CONFLICT | 停止，列原文交用户 |

每行摘录关键原文；`file:line` 只在记录的文件哈希窗口内有效。

判定口径：

- `COVERED`：条款 + 实现都在，输入形态与范围相同，另一代理照做会得到同一门禁。
- `PARTIAL`：只提及、只有一侧、范围更窄或更宽、输入形态不同，或依赖未审计的外部工具。
- `ABSENT`（旧称 `GAP`）：全量根 + 同义词检索后仍无命中，或命中与声明无关。
- `CONFLICT`：两个已安装 Skill 的规则相反或各自维护同一事实；停止，列原文与 `file:line`，不擅自选边。
- `UNSTABLE`：命中包正在并发写入；按 `audit-skill-during-live-creation` 的指纹与写入者证据处理。

### 6. 决策

| 覆盖结论 | 决策 |
|---|---|
| 任一 `COVERED` | 不新建；改为更新现有 Skill，保留其有效规则 |
| 仅 `PARTIAL` | 收窄新 Skill：只写真实增量，写「不用于」与委派边界 |
| 全部 `ABSENT` | 可以新建，且只写真实增量 |
| 存在 `CONFLICT` | 停止；列出冲突双方原文与 `file:line`，交用户决定 |
| 存在 `UNVERIFIED` | 先补读或复跑；不得把「还没找到」当成 `ABSENT` |
| 存在 `UNSTABLE` | 等待稳定或只读保留；不得把中间态当最终结论 |

收窄新建的最低要求：description 说明只补增量；正文开头写「不用于」；已覆盖规则只给一句用途加 Skill 名；属主变化时只改引用，不维护两份正文。

### 7. 写进方案并等确认

报告至少包含：两个根与计数、两次快照的 diff、token 与命中、覆盖矩阵与增量、决策、委派，以及已读/已复跑/二手/未验证四类证据。方案确认前不写目标目录，并明确写「尚未写入任何文件」。

### 8. 写入前复查

核对目标目录与两份快照一致：基线不存在且仍不存在才 create；基线已存在且指纹一致按 update；新出现或指纹变化按 0c 稳定后重跑矩阵，仍属职责重合再转 `adopt-concurrent-duplicate-skill`。写入流程交给 `skill-creator`，写后验收交给 `skill-file-qa`。写入后重跑矩阵：已覆盖规则是否只以交叉引用出现，是否复制了兄弟 Skill 的步骤；源断言按规则 16 复跑，`0 found` 不作证据。

## 失败模式

| 症状 | 原因 | 处理 |
|---|---|---|
| 方案声称「四个 Skill 均未覆盖」 | 按记忆挑列表，未全量枚举 | 重跑 `--list-skills`，与磁盘总数对账 |
| grep 0 命中就判 `ABSENT` | 只搜英文或只搜 `SKILL.md` | 加中法同义词，扫 `references/` 与 `scripts/` |
| 命中 `SKILL.md` 就判 `COVERED` | 只读文档，未读实现 | 打开脚本找断言或分支；无实现降为 `PARTIAL` |
| 推荐 rationale 的否定句被照抄 | 用推荐自证 | 用磁盘命中逐句反证，标 SUPPORTED/CONTRADICTED |
| 历史同名 Skill 不在根 | 被删除或迁移 | 先查本地备份、删除记录、会话 JSONL 与归档仓库；恢复版核对哈希，取不到才标 `UNVERIFIED` |
| 命中包正在变化 | 并发写入 | 判 `UNSTABLE`，等待稳定后重跑 |
| `TOKEN_TOO_GENERIC` | token 太泛 | 换成断言、旗标、函数名或错误串 |
| 方案定稿后、写入前出现新的相邻 Skill | 只做了一次枚举 | 立即做第二次全根快照与 diff，重跑矩阵 |
| 初读的相邻 Skill 数秒后行数/字节变化 | 审计期间仍有写入者 | 旧矩阵标 `STALE`，连续采样稳定后重读并重跑 |
| 相邻 Skill 正文声明脚本，磁盘只有 `SKILL.md` | 只看文档，未查声明资源 | 按规则 15 核对；缺失时只引思路，标 `UNVERIFIED` |
| 基线已存在却被当成并发 | 只看存在性，未比指纹与属主 | 指纹与属主都一致按 update；冲突标 `UNVERIFIED` |
| 校验器 PASS 但 `skill references: 0 found` | `--skill` 被缩写为 `--skills-root` | 用位置参数，要求计数精确匹配 |
| 矩阵全绿但关键主张未复跑 | 把二手摘要当证据 | 标 `UNVERIFIED`，补读或补跑 |
| 同一规则写进第二个 Skill | 未指定唯一属主 | 保留一个属主，其余改交叉引用 |
| 带参数调用后片段显示实参文本 | 注入层替换位置变量，磁盘未变 | 以磁盘原文为准，示例只用具名变量 |

## 已验证案例（2026-10-27）

- 会话 77e56b5c 用 `grep -rln "变异" --include=SKILL.md` 跨全部 Skill 检索，命中 `audit-skill-tool-contracts`；再读 SKILL.md:35 与其 `audit_contracts.py` 的 1127-1128 行，据此把它负责的通用变异门禁让出，只保留夹具变异质量门禁。
- 上一会话 7bc3b7ac 实际检查了 5 个 Skill（`skill-validator-selftest`、`develop-skill-static-checker`、`replay-skill-reference-fixtures`、`valider-harnais-fixture-windows-msys`、`tester-fixture-triage-snapshots`），漏掉 `audit-skill-tool-contracts`；推荐 JSON 写「四个」→ 计数不准确，但「漏查重叠」的实质成立。
- 本 Skill 创建前对 68 个用户级 + 2 个项目级 Skill 做实跑（最终复核时为 69+2，期间新增 1 个）：`inventory-installed-skills`、`adopt-concurrent-duplicate-skill`、`verify-skill-recommendation-claims` 均判 `PARTIAL`，全量 token 检索 + 五态判定的门禁判 `ABSENT`，故新建并窄化为本流程。
- 历史 audit-recouvrement-skills-avant-creation 的最终版（369 行、34,040 B、SHA-256 `2b86cf43…`）已从归档仓库逐字恢复并核对哈希；本 Skill 保留其两次快照、`STALE` 稳定门禁、`CONFLICT`、声明资源与来源复跑等规则，细节见案例文件。

细节、哈希、限制与未验证项见 `references/cas-2026-10-27-couverture.md`。

## 验收

- [ ] `--list-skills` 的 `n` 等于磁盘 `SKILL.md` 数，且 `n=u+p`。
- [ ] 每条能力声明至少一个 token；每个 token 有命中，或记录了同义词复查。
- [ ] 每个 `COVERED/PARTIAL` 都有规范条款 + 实现（或明确缺失）两栏。
- [ ] 矩阵含 `file:line`，并记录被引文件 SHA-256。
- [ ] 决策与覆盖结论一致；`COVERED` 未新建。
- [ ] 方案定稿前与写入前各做过一次全根快照，并记录了 diff。
- [ ] 未稳定对象已标 `STALE`；稳定后重读全文并重跑矩阵。
- [ ] 已覆盖规则只以交叉引用出现，未复制兄弟 Skill 的步骤。
- [ ] `CONFLICT` 已停止并列出双方原文，未擅自选边。
- [ ] 源断言已复跑，`0 found`/`0 checked` 未当作证据。
- [ ] 写入前目标目录状态与两份快照一致；出现或变化已按 0c 处理。
- [ ] 报告区分已核实、推断、未验证。

## 资源

- `scripts/audit_coverage.py`：只读枚举 + 跨文件 token 检索 + 矩阵骨架。`--help` 查看参数；`RESULT OK|PARTIAL` 退出码 0，用法/环境错误 2。默认忽略大小写，支持 `--regex`、`--format json`、`--list-skills`。
- `references/cas-2026-10-27-couverture.md`：来源会话、5 个已查 Skill、规则与实现行号、历史 Skill 的两版恢复过程与哈希、脚本实测、限制。
- 委派：数量口径 → `inventory-installed-skills`；推荐声明与来源对账 → `verify-skill-recommendation-claims`；并发重复接管 → `adopt-concurrent-duplicate-skill`；写后验收 → `skill-file-qa`。
