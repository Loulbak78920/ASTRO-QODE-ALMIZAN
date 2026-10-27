---
name: verify-cross-skill-reference-liveness
description: "当写入或修改 Skill 后需要确认正文反引号中的跨 Skill 引用仍然存活时，先读取目标 SKILL.md 并记录指纹，再用只读脚本枚举全部反引号名称（含未进入 skill-file-qa registry 的未安装名称、围栏块名称与形状像 Skill 的未解析候选），分别核对用户级与项目级 skills 根；形状像 Skill 但未解析的名称先记为 CANDIDATE，属主引用必须用 --expect 声明才判 MISSING，普通 token 用 --ignore 排除，CLI 内置或插件名称用 --builtin 声明，最终 PASS 要求 MISSING、BROKEN、CANDIDATE 均为 0（退出码 0 PASS、1 FAIL 或 REVIEW、2 参数或环境错误）；MISSING 时先确认语境，再把属主引用降级为纯文本历史来源，不恢复、不移动、不修改其他 Skill；随后重跑扫描与 skill-file-qa，但不把其“N checked”当作引用存活证明。用于 QA 已 PASS 但交叉引用已消失、Skill 被并发删除或移动、历史来源与当前属主混淆、CLI 内置名称被误判为缺失、普通连字符 token 被误报为缺失。中文触发：跨 Skill 引用、引用存活、QA 假 PASS、N checked、候选引用、Skill 消失、历史来源；English: cross-skill reference liveness, missing skill reference, QA false PASS, N checked, candidate reference; Français: référence croisée, skill manquant, faux PASS, candidat non classé."
---

# 校验跨 Skill 引用的存活状态

## 目标与边界

`skill-file-qa` 的跨 Skill 引用检查只统计注册表中已存在的名称；未安装的名称会被静默跳过，围栏代码块也会先被剥离。因此 `RESULT PASS` 与 `N checked` 不能证明所有反引号中的属主引用仍然存活。

扫描器采用“候选—归类”门禁：形状像 Skill 但未解析的名称只记为 CANDIDATE，不直接判 MISSING。属主引用必须显式写入 `--expect`，普通 token 写入 `--ignore`，内置或插件名称写入 `--builtin`；仍有未归类候选时结果为 `RESULT REVIEW`。

扫描范围是整个 SKILL.md（含 frontmatter），只识别反引号内的名称。已安装或已在 `--builtin`、`--ignore`、`--expect` 声明的名称不受形状限制；未解析的单个单词、含大写或下划线的名称不会成为 CANDIDATE，无反引号写法也不会被枚举，这些都需要人工复核。

本 Skill 负责：

- 枚举目标 SKILL.md 正文反引号中的全部 Skill 名称；
- 同时核对用户级与项目级 skills 根；
- 对失效引用做最小处置，并在写入后复验。

不替代以下属主：

- 结构验收与指纹稳定性：`skill-file-qa`
- 完整安装清单与跨根盘点：`inventory-installed-skills`
- SHADOWED 的运行时解析：`verify-skill-runtime-binding`
- 写入期间并发变化：`skill-update-concurrency-safe`
- 目标在写入期间突然出现：`adopt-concurrent-duplicate-skill`
- 提交与推送：`commit-skill-work`

只改目标 Skill 的引用文字；不恢复、不移动、不重命名、不修改其他 Skill。

## 资源

- `scripts/scan_skill_refs.py`：只读扫描器，枚举反引号名称并按规则分类；不修改任何文件。
  - `--builtin`：当前会话存在、磁盘根中没有的 CLI 内置或插件名称。
  - `--expect`：声明为属主引用、必须解析到本地 Skill 的名称；仍未解析即 MISSING。
  - `--ignore`：已确认不是 Skill 的普通 token；已安装名称仍按 LIVE 处理，不能用来掩盖真实 Skill；与 `--expect` 重名时以 rc=2 拒绝。
  - 输出 `SUMMARY` 行与 `RESULT PASS / REVIEW / FAIL`；退出码 0 PASS、1 FAIL 或 REVIEW、2 参数或环境错误。

## 不可协商规则

1. **QA PASS 不等于引用存活。** `skill references: N checked` 只统计 registry 内名称；必须独立枚举全部反引号名称。
2. **枚举全部名称。** 包括未安装、只在围栏块中出现、与当前 Skill 同名、以及 CLI 内置或插件名称；不能只抄 QA 输出。
3. **双根核对。** 用户级与项目级都要查；项目级根缺失时明确记为“未检查”，不能当作 0。
4. **先候选，后归类。** 形状像 Skill 但未解析的名称只是 CANDIDATE，不等于 MISSING；必须逐条读行号后，把属主引用写入 `--expect`、普通 token 写入 `--ignore`、内置或插件名称写入 `--builtin`。NON_SKILL 与 IGNORED 只做记录；不要把“目录存在但缺 SKILL.md”当成未安装。
5. **内置名称不是缺失。** 当前会话可用 Skill 列表中的 CLI 内置或插件名称，通过 `--builtin` 传入；不要猜测列表，也不要用 `--ignore` 掩盖。
6. **MISSING 由 `--expect` 定义。** 只有声明为属主引用且仍未解析的名称才是 MISSING；示例、占位符或明确的外部能力改写为清晰说明，不自动删除。
7. **默认降级，不恢复。** 属主引用失效时改为纯文本历史来源，例如“历史名称某 Skill（当前不在用户级/项目级 skills 根）”；不创建缺失目录、不从备份恢复、不修改其他 Skill。
8. **不猜测改名。** 只有 Git、目录或来源会话证据支持时才把引用更正为新的 LIVE 名称；否则降级并记录未验证。
9. **写后重扫。** 剩余反引号属主引用必须是 LIVE、SHADOWED 或 BUILTIN；MISSING、BROKEN、CANDIDATE 必须为 0，且必须是 `RESULT PASS`、退出码 0；`RESULT REVIEW` 与 rc=1 不算通过。
10. **未跑不宣称。** 报告区分“已读取 / 已运行 / 仅来源报告 / 未验证”；没有实际扫描和 QA 输出就不宣称通过。

## 流程

### 0. 建立基线

```bash
TARGET="$HOME/.qoder/skills/<skill-name>"
sha256sum "$TARGET/SKILL.md"
stat -c '%s %y' "$TARGET/SKILL.md"
git -C "$TARGET" rev-parse "HEAD:SKILL.md" 2>/dev/null || true
git -C "$TARGET" hash-object --path=SKILL.md "$TARGET/SKILL.md" 2>/dev/null || true
git -C "$TARGET" status --short 2>/dev/null || true
```

- 两次采样间隔至少 2 秒，size、mtime、SHA-256 一致才继续。
- 写入期间目标目录突然出现或文件反复变化：停止写入，按 `skill-update-concurrency-safe` 或 `adopt-concurrent-duplicate-skill` 处理。
- 有 Git 时记录 HEAD OID；`core.autocrlf=true` 时比较 OID，不直接比较工作区 SHA-256 与 blob。

### 1. 运行只读扫描

第一遍不带 `--expect` 与 `--ignore`，让所有未解析的 Skill 形状名称以 CANDIDATE 暴露出来：

```bash
SCAN="$HOME/.qoder/skills/verify-cross-skill-reference-liveness/scripts/scan_skill_refs.py"
py -3 "$SCAN" "$TARGET" \
  --workspace "<workspace-root>" \
  --builtin "<builtin-1>,<builtin-2>"
```

- `--builtin` 只抄当前会话确实存在的 CLI 内置或插件名称；没有就省略。
- `RESULT REVIEW` 与退出码 1 表示仍有未归类候选，不是最终结论；逐个读 CANDIDATE 的行号后进入第 2 步。
- 没有 CANDIDATE 且 `RESULT PASS` 时才可直接作为通过证据。

归类后第二遍只声明已确认的属主引用与普通 token：

```bash
py -3 "$SCAN" "$TARGET" \
  --workspace "<workspace-root>" \
  --builtin "<builtin-1>,<builtin-2>" \
  --expect "<owner-ref-1>,<owner-ref-2>" \
  --ignore "<token-1>,<token-2>"
```

- 扫描器只读，不修改目标文件；退出码 0 表示 PASS，1 表示 FAIL（MISSING/BROKEN）或仍有 CANDIDATE，2 表示参数或环境错误（含 `--expect` 与 `--ignore` 重名、根不存在、SKILL.md 缺失或非法 UTF-8）。
- 看到 FAIL 或退出码 2 时先解决环境或归类问题，不要把“未检查”写成“通过”。

### 2. 逐项分类

| 状态 | 含义 | 动作 |
|---|---|---|
| LIVE | 至少一个根中存在同名目录且 SKILL.md 存在 | 保留引用；必要时回读目标 SKILL.md |
| SHADOWED | 两个根中都有同名 Skill | 保留引用；运行时解析交给 `verify-skill-runtime-binding`，不自行假定优先级 |
| BUILTIN | 名称在 `--builtin` 声明中，磁盘根中没有 | 保留引用；在报告中注明“内置或插件，未做磁盘核对” |
| CANDIDATE | 形状像 Skill，但两个根中都没有，且未在 `--builtin` 或 `--ignore` 中声明 | 逐条读行号：属主引用写入 `--expect`；普通 token 写入 `--ignore`；内置名称写入 `--builtin`；归类前不得判 MISSING，也不得直接忽略 |
| MISSING | 已在 `--expect` 声明为属主引用，但仍未解析 | 确认语境；属主引用降级为纯文本历史来源；示例或外部能力改写说明 |
| BROKEN | 目录存在但缺 SKILL.md | 不创建文件、不修改该目录；报告并交用户决定 |
| EXTERNAL | 带命名空间的插件或外部名称，未在 `--builtin` 声明 | 记录但不自动失败；确认来源，无法确认时改为纯文本说明 |
| FENCED | 只出现在围栏代码块中的失效或候选名称 | 不作为失败；确认是示例还是真实引用，必要时单独处理；围栏内已解析名称不会单独列出 |
| SELF | 与目标 Skill 同名 | 不是跨 Skill 引用；保留或按文档需要处理 |
| NON_SKILL | 自动识别的 UUID、日期或常见命令 token | 不作为 Skill 引用；保留输出以便复核 |
| IGNORED | 通过 `--ignore` 明确排除的非 Skill token | 记录排除理由；不要用它掩盖真实 Skill 名称 |

- 同一名称多处出现时，按所有行号逐条读上下文。
- 不要把普通文件、命令、参数、路径、占位符误判为 Skill；扫描器只自动识别 UUID、日期与内置命令 token 表，其余候选一律人工归类。
- SHADOWED 不等于错误；不要在未验证运行时解析的情况下删除或改写。
- CANDIDATE 只覆盖反引号内小写连字符名称；未解析的单个单词、含大写或下划线的名称、多词短语与无反引号写法不会被列出，需人工核对。

### 3. 处置 CANDIDATE 与 MISSING

- 先归类 CANDIDATE：确认是“当前属主 / 参见 / 不替代”这类引用就写入 `--expect`；确认是普通 token（路径片段、测试标签、占位符、格式名）就写入 `--ignore`；确认是当前会话内置或插件名称就写入 `--builtin`。
- 归类后重跑：`--expect` 中仍未解析的名称变成 MISSING；`--ignore` 中的名称变成 IGNORED，不再阻塞。
- 属主引用（MISSING）：把反引号去掉，改成纯文本历史来源，保留可搜索的名称与状态。例如：历史名称 audit-recouvrement-skills-avant-creation（当前不在用户级/项目级 skills 根）。
- 冗余或明确错误的引用：可删除；删除前确认同一信息在正文其他位置仍有记录。
- 示例或占位符：改为明确的非属主说明，或使用不会与真实 Skill 名称混淆的占位写法。
- 有证据的改名或移动：只把引用更正为已确认的 LIVE 名称；在报告中给出证据来源。
- 不恢复缺失 Skill；不修改其他 Skill；不根据名称相似度猜测。

### 4. 写后复验

```bash
py -3 "$SCAN" "$TARGET" --workspace "<workspace-root>" \
  --builtin "<builtin-1>,<builtin-2>" \
  --expect "<owner-ref-1>,<owner-ref-2>" \
  --ignore "<token-1>,<token-2>"
sha256sum "$TARGET/SKILL.md"
stat -c '%s %y' "$TARGET/SKILL.md"
QA_DIR="$HOME/.qoder/skills/skill-file-qa"
py -3 "$QA_DIR/scripts/validate_skill.py" "$TARGET" --workspace "<workspace-root>" --stable-seconds 2 --stability-timeout 30
```

- 扫描器：MISSING、BROKEN、CANDIDATE 均为 0、`RESULT PASS`、退出码 0；`RESULT REVIEW` 或 rc=1 不算通过。
- 每个 CANDIDATE 都要有明确归宿：`--expect`、`--ignore` 或 `--builtin`；报告列出逐个决定。
- QA：`RESULT PASS`、退出码 0、`Files (N)` 与预期一致、`local references` 与 `skill references` 计数精确匹配。
- 明确记录：`skill references: N checked` 只覆盖 registry 内名称；本次存活结论来自扫描器的全量枚举，不来自 N。
- 回读修改段落，确认历史来源说明、示例与错误表一致。
- 记录最终 size、mtime、SHA-256；有 Git 时记录 HEAD OID。

### 5. 报告与证据

报告至少包含：

- 目标文件与写入前后指纹；
- 扫描器完整输出或逐项表：名称、行号、状态、根、动作；
- 每个 CANDIDATE 的归类决定与理由（`--expect` / `--ignore` / `--builtin`）；
- 每个 MISSING 的语境判断与处置理由；
- QA 的 N checked 与扫描器候选总数的差异；
- 已读取、已运行、仅来源报告、未验证四类证据边界。

提交或推送不在本 Skill 范围内；用户要求时另行加载 `commit-skill-work`，不要在本 Skill 中自行提交。

## 错误表

| 症状 | 根因 | 动作 |
|---|---|---|
| QA 报 RESULT PASS 与 N checked，但引用已失效 | registry 只收集已安装名称，未安装名称被跳过 | 运行扫描器全量枚举；不要用 N 作存活证明 |
| 0 found 被当成“没有引用” | 没有反引号中的已安装名称 | 用扫描器区分“无候选”和“有候选但未解析” |
| CLI 内置名称被报 CANDIDATE | 未在 `--builtin` 声明 | 从当前会话列表抄入 `--builtin`；不要猜，也不要用 `--ignore` 掩盖 |
| 会话 ID、日期或常见 Git 子命令被归为 NON_SKILL | 扫描器按内置 token 表识别 | 确认不是真实 Skill 即可；未列入 token 表的命令会变成 CANDIDATE，确认后写入 `--ignore` |
| 目录存在但报 BROKEN | 目录缺 SKILL.md | 按 BROKEN 报告；不要创建 SKILL.md 修补他人 Skill |
| 围栏块中的示例名称出现在 FENCED | 扫描器只提示围栏内失效或候选名称 | 确认是示例后不作为失败；不要把示例改成真实引用 |
| 出现 `WARN unterminated fenced block` | 围栏未闭合，后续行被当作围栏内容，其中的失效引用只记 FENCED 不计数 | 先补全或删除围栏标记再重扫；有该 WARN 时不宣称存活 |
| 已安装 Skill 写入 `--ignore` 后仍显示 LIVE | registry 优先级高于 `--ignore` 与 `--expect` | 不要用 `--ignore` 掩盖真实 Skill；内置名称改用 `--builtin` 声明 |
| 普通连字符 token 被报 MISSING | 旧行为按形状直接判缺失 | 新脚本只报 CANDIDATE；确认非 Skill 后写入 `--ignore`，不要按缺失处置 |
| 出现 `RESULT REVIEW` 与 rc=1 | 仍有未归类 CANDIDATE | 逐条读行号：属主引用写 `--expect`，普通 token 写 `--ignore`，内置名称写 `--builtin`，再重跑 |
| SHADOWED 被当成缺失或错误 | 两个根中都有同名 Skill | 保留引用；运行时解析交给 `verify-skill-runtime-binding` |
| 自动恢复缺失 Skill | 把引用失效误当成需要修复缺失 Skill | 只改目标引用；不创建、不恢复、不修改其他 Skill |
| 猜测改名后引用再次失效 | 只按名称相似度替换 | 只有 Git、目录或会话证据支持才更正；否则降级 |
| N checked 与扫描器候选总数不一致 | 两个统计口径不同 | 分别报告 registry 计数与全量候选计数 |
| `--expect` 与 `--ignore` 出现同一名称 | 归类自相矛盾 | 脚本以 rc=2 拒绝；修正参数后重跑 |
| SKILL.md 非法 UTF-8、根不存在或无法枚举 | 读取或环境错误 | 脚本以 rc=2 退出；报告“未检查”，不要写成通过 |
| 单个单词、多词短语或无反引号引用未被列出 | 扫描器只识别反引号内的连字符名称 | 人工核对这类引用；不要把“没列出”当成“已存活” |
| 写入期间文件被并发改写 | 未做稳定性采样 | 按 `skill-update-concurrency-safe` 重做基线 |

## 完成清单

- [ ] 目标 SKILL.md 写入前后均有 size、mtime、SHA-256；有 Git 时记录 HEAD OID。
- [ ] 扫描器已运行，输出包含全部可识别的反引号候选与行号。
- [ ] 用户级与项目级根均已核对；缺失根明确记为未检查。
- [ ] 每个 CANDIDATE 都已逐条归类为 `--expect`、`--ignore` 或 `--builtin`，并记录理由。
- [ ] 每个 MISSING 都有语境判断与处置理由；属主引用已降级为纯文本历史来源。
- [ ] 剩余反引号属主引用均为 LIVE、SHADOWED 或 BUILTIN；MISSING、BROKEN、CANDIDATE 均为 0，且为 `RESULT PASS`、rc=0。
- [ ] CLI 内置或插件名称来自当前会话列表，未猜测，未用 `--ignore` 掩盖。
- [ ] 未恢复、未移动、未重命名、未修改其他 Skill。
- [ ] `skill-file-qa` 已运行：PASS、rc=0、计数已记录，且未把 N checked 当作存活证明。
- [ ] 最终指纹已记录；无缓存或临时残留。
- [ ] 报告区分“已读取 / 已运行 / 仅来源报告 / 未验证”。

## 来源与证据

2026-10-26 会话 bde94be6-4944-402a-844a-f8db1c06a286（读取时 revision 19；相关创建回合已完成，末尾 push to remote 回合失败，本 Skill 不使用其推送结论）。该会话创建 harden-skill-argument-substitution 后：

- `skill-file-qa` 输出 9 PASS / 0 FAIL / 0 WARN、6 checked、RESULT PASS、EXIT 0。
- 手工逐名核对发现历史名称 audit-recouvrement-skills-avant-creation 不在用户级 skills 根；其余 6 个 OK。
- 该引用改为纯文本历史来源后，QA 仍为 6 checked、PASS。
- 本会话 17:10 读取来源产物时为 13,308 B、203 行、SHA-256 debd9dbf…，与来源会话记录的最终值一致；17:21 再次读取时已变为 14,156 B、220 行、SHA-256 6a15ba72…，说明该产物在本次创建期间被并发改写。本 Skill 未修改它，也不把任一版本当作当前结论。

本会话另用一次性夹具复现并验证：

- 5 个反引号名称中，QA 只报 2 checked、PASS；未安装名称与 CLI 内置名称被静默跳过。
- 目录存在但缺 SKILL.md 会 FAIL，区别于完全未安装。
- 围栏块中的名称被 QA 忽略。
- 旧版脚本的夹具矩阵覆盖 LIVE、SHADOWED、BUILTIN、MISSING、BROKEN、EXTERNAL、FENCED、SELF、NON_SKILL、IGNORED，退出码 0、1、2 与只读性断言全部通过；临时目录已清理。
- 夹具已清理，未写任何真实 Skill。

本会话 2026-10-26 的更新轮复现并加固（脚本 SHA-256 524e40d69044643b5313ef4603d358031828cc395f0f5f3957cd7aa0c919115d，10,308 B）：

- 旧版“形状像 Skill 即 MISSING”规则扫描当时的 53 个用户级 Skill：16 个 rc=1；其中只有 3 个真的含失效属主引用（历史名称 audit-recouvrement-skills-avant-creation），其余 13 个仅因普通连字符 token 失败，例如 utf-8、my-org、checkout-index、packed-refs。
- 改为“候选—归类”门禁后，夹具矩阵 20 项断言全部通过：LIVE、SHADOWED、BUILTIN、BROKEN、EXTERNAL、SELF、NON_SKILL、CANDIDATE、IGNORED、FENCED；REVIEW rc=1、`--expect` MISSING rc=1、`--ignore` PASS rc=0、`--expect` 与 `--ignore` 重名 rc=2、根缺失 rc=2、SKILL.md 缺失 rc=2、非法 UTF-8 rc=2、围栏未闭合 WARN、双根同路径 WARN、夹具只读不变与临时目录清理。
- 当前 54 个用户级 Skill 实跑：36 PASS、18 REVIEW、0 FAIL、0 rc=2；18 个含候选的文件中，3 个含失效属主引用，其余 15 个只含普通 token 或内置名称（skill-creator 共出现在 5 个文件）。
- 真实目标只读验证：本 Skill 自身 6 LIVE、`RESULT PASS`、rc=0；harden-skill-argument-substitution 6 LIVE + 2 NON_SKILL、`RESULT PASS`、rc=0；inventory-installed-skills 3 LIVE + 2 CANDIDATE、`RESULT REVIEW`、rc=1；对其加 --expect audit-recouvrement-skills-avant-creation --ignore missing-skill-md 后为 1 MISSING + 1 IGNORED、`RESULT FAIL`、rc=1。以上均未修改其余 Skill。

证据边界：`skill-file-qa` 的 registry 过滤行为来自对 [validate_skill.py:270](file:///C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py#L270) 的读取与本会话夹具实跑；来源会话的 QA 计数来自其工具输出；上述 53/54 与夹具数字来自本会话的实际运行，未保留完整原始输出，只保留断言结果；历史 Skill 的恢复状态未验证，本 Skill 不执行恢复。
