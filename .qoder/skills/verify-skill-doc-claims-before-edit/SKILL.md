---
name: verify-skill-doc-claims-before-edit
description: "在把来源会话或本地观察到的行为写进 SKILL.md 前，先把每条拟写断言登记为 REPRODUCED / COVERED / DOCUMENTED / INFERRED / UNVERIFIED，复现非显然的失败模式并设计非空断言，按证据选择「validée / couverte / 按顺序推断 / 未验证」的措辞，再在正文行数预算内做最小修改，先跑基线 QA 再写入并跑写入后 QA。用于来源会话结论、garde 措辞校准、fixture 覆盖与承重混淆、正文接近 500 行、需要最小 diff 的 Skill 更新；CRLF 夹具机制交给 verifier-fixture-autocrlf-non-vacue，既有夹具重放交给 replay-skill-reference-fixtures，写入后验收交给 skill-file-qa。中文触发：写入前证据台账、断言非空、fixture 覆盖不等于承重、Garde validée 改写、couverte、按代码顺序推断、基线 QA、body 行数预算、最小 Edit。"
---

# 写入前声明核验

## 目标

在修改 SKILL.md 之前，把“来源会话里发生了什么”转成可核对的声明台账，再决定每条断言能写到什么程度。本 Skill 只负责写入前的证据准入与措辞校准；它不提供 CRLF 夹具，也不替代写入后验收。

## 什么时候用

- 准备把来源会话、用户纠正或本地观察写成 SKILL.md 的确定结论。
- 结论会使用“已验证”“已覆盖”“必然”“会”等强度措辞。
- fixture 只执行了路径，尚未证明守卫“承重”。
- 正文接近 500 行，需要最小 diff。
- 同一职责可能已被并行创建的 Skill 覆盖，需要先划边界。

## 什么时候不用

- 只做重命名、移动或格式调整，没有新的行为断言。
- 已有领域夹具可直接调用：CRLF 与 `autocrlf` 用 `verifier-fixture-autocrlf-non-vacue`，通用 bash 块用 `verify-skill-command-blocks-fixture`，既有参考夹具用 `replay-skill-reference-fixtures`。
- 只缺写入后结构验收：用 `skill-file-qa`。
- 来源事实尚未取证：先用 `audit-session-evidence`。
- 需要撰写 references 证据档案：用 `write-skill-evidence-case-study`。

## 不可协商规则

1. **一条断言一句话。** 写明主体、输入、环境与预期结果；不要把多条观察合并成“已验证”。
2. **先分类，后措辞。** 每条拟写断言先落入五级证据之一（见第 3 步），再选择措辞。
3. **先复现，后写入。** 非显然的失败模式必须在 Skill 目录之外的一次性 fixture 中复现；不能只凭代码阅读或二手摘要写“已验证”。
4. **断言必须非空。** 顺序固定为：退出码 → 终端令牌 → 产物 → 无错误签名 → 无目标症状。前置产物缺失时，后两项的“缺席”是空洞的。
5. **覆盖不等于承重。** fixture 执行了路径，只能说明路径被覆盖；只有移除守卫会改变结果，才可写“承重”。
6. **措辞不越级。** `validée` 只用于被复现且断言非空的结论；`couverte` 用于路径已执行但承重未证明；仅由代码顺序或二手记录得出的写“按顺序推断”；未执行的写“未验证”。
7. **先跑基线验收。** 写入前记录 `skill-file-qa` 的真实 PASS/FAIL/WARN、body 行数、文件清单与 SHA-256；否则无法区分既有失败与本次引入。
8. **最小 Edit。** 只改目标断言所在行；不重排、不顺手整理、不整文件重写。body 必须保持 < 500 行。
9. **局部结论不上升为全局。** 报告写明 shell、Git 版本、extractor、fixture 与时间；一次 Git Bash 复现不等于生产或其他 shell。
10. **会话状态有时点。** 来源会话仍在运行时，记录的 revision 与状态只对读取时刻成立；写入前重读或明确标注观察时点。

## 第 0 步 — 预检

1. 确认目标目录与本轮允许写入的文件；不要顺手修改相邻 Skill。
2. 检查是否已有并行 Skill 覆盖同一职责；若有，先确定分工或停止创建。
3. 运行基线验收并记录指纹：

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" <skill-dir> \
  --workspace <workspace-root> --stable-seconds 2 --stability-timeout 30
sha256sum <skill-dir>/SKILL.md
wc -l <skill-dir>/SKILL.md
```

4. 若基线已有 FAIL，先记录，不把本次修改后的 FAIL 归因于新内容。
5. 若目标可能被并发写入，按 `skill-update-concurrency-safe` 采样；出现新写入者时停止并重取基线。

## 第 1 步 — 声明台账

把每条准备写入的句子放进台账，不先写正文：

| ID | 拟写断言 | 来源 | 已执行命令与输出 | 证据级别 | 允许措辞 | 写入位置 |
|---|---|---|---|---|---|---|
| C1 | 字节重写会留下过期 stat 缓存 | 会话 `0e4e48dd` | fixture：`diff --quiet=0`、`status=M`、`refresh=1` | REPRODUCED | vérifié dans Git Bash | 失败表 |
| C2 | 只断言无 `DIFF_SKILL` 会空洞通过 | 代码退出顺序 | 未直接复现 | DOCUMENTED | 按退出顺序推断 | 规则 |
| C3 | “Garde validée”超出证据 | 会话 diff | 已对照证据 | VERIFIED | couverte, non prouvée porteuse | 正文 |

台账为空时不要开始编辑：说明本轮没有新的行为断言。

## 第 2 步 — 复现与断言

- 在 `$HOME/.qoder/tmp/<unique>/` 建一次性 fixture，结束后只清理本目录。
- 只读对待已安装 Skill；不得在 Skill 目录内制造状态、修改索引或提交。
- 领域机制不要重写：CRLF 与 `autocrlf` 直接调用 `verifier-fixture-autocrlf-non-vacue` 的夹具与断言顺序。
- 记录命令、退出码、stdout、stderr、环境与清理结果；退出码要在管道之前取得。

最小断言骨架：

```bash
eq rc 0
contains terminal ARCHIVE_UPDATE
test -f "$TMP/artifact" && echo "PASS artifact"
lacks stderr "comm:"
lacks out DIFF_SKILL
```

- 若 fixture 提前退出，`rc` 可能仍为 0，终端令牌可能已出现，而症状缺席——这正是空洞通过。
- 若缺少 src.rel 一类前置产物，先补执行文档中的前置步骤，不要删除块内行。
- 负向控制与正向控制必须使用同一块代码；只改一个输入变量。

## 第 3 步 — 分类与措辞

| 级别 | 判定依据 | 允许措辞 | 禁止措辞 |
|---|---|---|---|
| REPRODUCED | 失败模式在 fixture 中真实发生，断言非空 | `vérifié dans <env>` | 外推到生产 |
| COVERED | 路径已执行，但未做移除守卫的 A/B | `couverte … non prouvée porteuse` | `validée` |
| DOCUMENTED | 来自代码退出顺序、日志或二手记录，未重放 | `按退出顺序推断` | `vérifié` |
| INFERRED | 由行为或文档逻辑推出，无执行证据 | `hypothèse` / `à confirmer` | `démontré` |
| UNVERIFIED | 未执行或环境不具备 | `non vérifié` | 任何确定语气 |

- `validée` 只用于 REPRODUCED 且承重已由 A/B 证明的守卫。
- `couverte` 必须同时写出未证明的部分，例如“sous Git Bash, non prouvée porteuse”。
- 同一断言在正文、失败表、Limites 与 evidence 中只能使用同一级别；改一处后按唯一短语搜索其余位置。

## 第 4 步 — 最小修改

1. 用 Edit 定位到台账中的写入位置；不要整文件 Write。
2. 正文改动只包含措辞校准或新增的必要规则；脚本和 references 不在必要时不改。
3. 每改一处，检查 body 行数：

```bash
wc -l <skill-dir>/SKILL.md
grep -n "<唯一短语>" <skill-dir>/SKILL.md
```

4. 若接近 500 行，优先压缩重复措辞，不删除证据或限制条件。
5. Edit 返回 0 命中或文件已变化时，先重读当前文件并查并发写入，不要重复旧编辑。

## 第 5 步 — 写入后验收

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" <skill-dir> \
  --workspace <workspace-root> --stable-seconds 2 --stability-timeout 30
sha256sum <skill-dir>/SKILL.md
```

- 要求稳定指纹上的 `RESULT PASS`；记录实际 PASS/FAIL/WARN、body 行数、`Files (N)` 与引用检查。
- 回读改动行，确认措辞与台账级别一致。
- 报告分别列出：已复现、仅覆盖、按顺序推断、未验证；不要把“覆盖”写成“承重”。
- 来源会话仍在运行时，写“观察时 revision=…, state=…”；不要写成最终状态。
- 未获授权不 commit、不 push、不修改其他 Skill。

## 已验证案例（2026-10-26，会话 `0e4e48dd`）

- **C1 REPRODUCED**：fixture 中先写入带 CRLF 的 `name: demo`，得到 `diff_quiet_rc=0`、`status: M f.txt`、`refresh_rc=1`、刷新后仍 ` M`；`rm f.txt && git checkout -- f.txt` 后为 `i/lf w/crlf` 且状态为空。
- **C2 DOCUMENTED**：源码中 `SOURCE_DIRTY_STOP` 早于 `DIFF_SKILL`；会话据此推断“只断言无 `DIFF_SKILL` 可能空洞通过”，但未直接构造该空洞通过的运行。因此只能写“按退出顺序推断”。
- **C3 VERIFIED**：`Garde validée` 被改为 `Garde couverte … mais non prouvée porteuse sous Git Bash`，与 evidence 的结论一致。
- 基线 QA 为 body 488、9 pass / 0 fail / 0 warn、SHA-256 `0bf71394…`；写入后 body 490、SHA-256 `364c52a5…`，仍 PASS。
- 未验证：完整 PR 流程、生产仓库、其他 shell 或 extractor；不得从本案例外推。

## 错误与陷阱

| 症状 | 原因 | 动作 |
|---|---|---|
| `status` 显示 ` M`，但 `git diff --quiet` 为 0 | 字节重写后 stat 缓存未刷新 | 用 `rm` + `git checkout -- .` 重建；不要用 `status` 证明漂移 |
| 所有断言通过，但没有产物 | fixture 提前退出，缺席断言为空 | 先断言产物与 stderr，再断言症状缺席 |
| 用 `validée` 描述只跑过路径的守卫 | 把覆盖当成承重 | 改为 `couverte … non prouvée porteuse` |
| body 达到或超过 500 行 | 新增规则未压缩 | 保留证据与限制，删重复措辞；重跑 QA |
| 未跑基线就写入 | 无法区分既有失败 | 先跑基线并记录指纹 |
| 来源会话 revision 已变化 | 读取窗口过期 | 重读或标注观察时点；不要写最终状态 |
| 并行 Skill 已覆盖同一规则 | 未做职责检查 | 停止写入，先确定归属或分工 |
| Edit 返回 0 命中 | 文本被并发改写或定位失配 | 查写入者、重读、重新定位，不重复旧编辑 |
| QA 后文件再次变化 | 并发写入 | 旧 PASS 作废，等待稳定后重跑 |

## 完成检查

- [ ] 台账覆盖本轮所有拟写断言。
- [ ] 非显然断言已复现，或明确标为未复现。
- [ ] 断言顺序包含退出码、终端令牌、产物与错误签名。
- [ ] 措辞与证据级别一致，未把覆盖写成承重。
- [ ] 写入前基线 QA 已记录。
- [ ] 只做最小 Edit，body < 500。
- [ ] 写入后 QA 在稳定指纹上 PASS。
- [ ] 已回读实际文件与改动行。
- [ ] 未修改相邻或并行 Skill。
- [ ] 未获授权未 commit、未 push。

## 资源

- `references/evidence-2026-10-26.md` — 来源会话逐字命令、输出、QA 指纹、证据分类与重合 Skill 归属。

## 相关 Skill

- `verifier-fixture-autocrlf-non-vacue` — CRLF 与 `autocrlf` 夹具机制及“present vs porteur”。
- `verify-skill-command-blocks-fixture` — 通用 bash 块提取与 A/B。
- `replay-skill-reference-fixtures` — 既有参考夹具重放。
- `skill-file-qa` — 写入后结构、引用、行数与指纹验收。
- `write-skill-evidence-case-study` — references 证据档案的三级写作规范。
- `skill-update-concurrency-safe` — 并发写入、采样与最小 Edit。
