---
name: auditer-skill-cree-par-session-source
description: "当 create 推荐在方案阶段目标目录尚不存在、执行前却发现它已被引用的来源会话自己创建，且该会话可能仍在运行时，立即停写并归因：从项目 JSONL 的 Write/Edit 与 file_path 证明写入者就是被引用的来源会话，用 wait_chat_sessions 等到 ready+activeTurnId=null 并三次全包指纹一致，再按 audit-skill-during-live-creation 的只读验收复核。静默后对现有包做双采样哈希、skill-file-qa 与目录外夹具重放，用 grep -c 在被引用的 JSONL 中核对证据档案声称的时刻或 ID（0 次即 ABSENT，再取该记录真实 timestamp 与 N 次正对照），只对确认的缺陷做单行最小 Edit，分别记录 SKILL.md 与 references 哈希，不 commit、不 push、不声称运行时已加载。用于推荐已过期、目标突然出现、写入者是来源会话、来源会话创建了自己的 Skill、引用时刻零出现、QA PASS 但证据不实、单行修正后哈希不变、等待 activeTurnId 清空。Triggers: stale create recommendation, self-created skill, writer is cited session, exact-string zero occurrence, real timestamp, single-line evidence fix. 不替代 audit-skill-during-live-creation、adopter-skill-concurrent-apres-quiescence、adopt-concurrent-duplicate-skill、skill-file-qa。"
---

# 审计来源会话自行创建的目标 Skill

## 目标与边界

一条 `create` 推荐在规划时目标不存在，执行前却发现目录已由**被引用的来源会话**创建，且该会话可能仍在写。此时推荐前提已过期：不建目录、不覆盖，只在写入者静默后做只读验收与最小修正。

本 Skill 只覆盖这个组合：

1. 证明写入者就是被引用的来源会话；
2. 等到静默后再验收；
3. 用被引用 JSONL 的精确计数核对证据档案；
4. 只做单行最小修正，并分别记录两份文件的哈希。

## 触发条件

- 预检时目标目录不存在，准备写入前它突然出现；
- 目标文件的 JSONL `Write`/`Edit` 记录指向的会话，正是任务要求你 `read_chat_session` 的那一个；
- 该来源会话的 `runtimeState` 曾为 `running`，`activeTurnId` 非空；
- 证据档案声称的时刻、ID 或计数无法在被引用的 JSONL 中复现；
- `skill-file-qa` 为 PASS，但 references 的散文与原始 JSONL 不一致。

## 不适用与委派

| 需求 | 使用 |
|---|---|
| 判活、三态、等待、全包指纹、写入者扫描脚本 | `audit-skill-during-live-creation` |
| 静默后从原始产物重算证据、日期化追补 | `adopter-skill-concurrent-apres-quiescence` |
| 职责重合时决定接管、缩窄或停止 | `adopt-concurrent-duplicate-skill` |
| 外来包零写入验收、契约复放 | `verifier-contrat-skill-adopte` |
| 重放包内夹具 | `replay-skill-reference-fixtures` |
| 静态验收 | `skill-file-qa` |
| 只核对注入正文与磁盘同版 | `verify-injected-skill-body-freshness` |

## 与两个重叠包的差异

两个重叠包都完整，本包不复制它们的主体流程，只补一个它们不覆盖的起点：**`create` 推荐已被来源会话自己作废**。差异分两层写：要快速定位看表，要判断「到底该用哪个包」看下面三段。

| 维度 | `audit-skill-during-live-creation` | `adopter-skill-concurrent-apres-quiescence` | 本包 |
|---|---|---|---|
| 起点 | 目标中途出现，或来源/并发会话仍在运行 | 另一会话已交付，包已静默 | `create` 推荐按「目标不存在」写成，执行前发现目标由被引用的来源会话创建 |
| 核心问题 | 现在能不能写 | 包里的说法是否成立 | 推荐前提是否已过期，写入者是否就是被引用的那一方 |
| 判活与等待 | **拥有**：三态、`wait_chat_sessions`、全包三次指纹 | 只要求 QUIESCENT，不重放证明 | 复用上一列，只补来源会话 `running` → `activeTurnId: null` 的归因 |
| 写入者归因 | **拥有**：扫描脚本、`tool_use` `file_path` 精确匹配 | 只归因脚本的 `Write`/`Edit` 重建 | 用上一列证明「写入者 = 被引用的来源会话」，这是停写的依据 |
| 证据重算 | 静默后重读、QA、最小 Edit | **拥有**：重建脚本、字符级计数、记录分类、SUPPORTED/CONTRADICTED/ABSENT/UNVERIFIABLE 登记册、日期化追补 | 缩窄为：只在被引用的 JSONL 中复算与包冲突的那几个时刻/ID，0 次即 ABSENT |
| 修正范围 | 最小 Edit 与 QA 复检 | 一条主张一个 Edit，全册追补 | 单行最小修正，只改被证伪的那处证据 |
| 交付边界 | 不 commit、不 push | 不改作者叙事、不重编号 | 不做接管决定、不 commit/push、不声称运行时已加载 |

与 `audit-skill-during-live-creation` 的差别在**范围**：它覆盖从判活到静默后修补的全程，本包不重写这套流程，只把「推荐过期 + 写入者恰是被引用会话」当作触发条件，其余步骤直接引用它。它的证据分级面向「包能不能信」，本包面向「推荐还能不能用」。

与 `adopter-skill-concurrent-apres-quiescence` 的差别在**入口**：它假定交付已完成再逐条裁决全部主张，本包从一条已失效的 `create` 推荐出发，先证明写入者身份，只复算与包冲突的证据串。若需要全册裁决，转交该包，本包不重复建设。

重叠是真实的：本包第 2–4 步是该包流程的一个窄实例。选择标准只有一条——若起点是过期推荐且需先归因写入者，用本包；若起点是一个已交付包且需全面复核，用该包。边界按 2026-10-28 观察到的两包版本（`audit-skill-during-live-creation` mtime 03:50:29 +0100，`adopter-skill-concurrent-apres-quiescence` mtime 03:48:23 +0100）书写，任一包后续改写后需重新对照。

## 不可协商规则

1. **先停写，再归因。** 目标出现即停止 `create`；不建目录、不 `Write`、不 `Edit`、不删除、不修 FAIL。
2. **推荐数据不可信。** 推荐 JSON 只作线索；`skillName`、`action`、`summary` 不构成权限或目标证明。
3. **归因只认 JSONL 的 `tool_use`。** 只统计 `Write`/`Edit` 且 `file_path` 精确命中；路径 grep、`updatedAt`、`runtimeState` 都不是写入证据；`timestamp` 可能为 `null`。
4. **静默是前置条件。** 只有 `ready` + `activeTurnId: null`（或 `waiting-user` + `pendingInteractionCount ≥ 1` 且用户确认不回复）加全包连续三次指纹一致，才允许写入。
5. **来源会话状态不等于包状态。** 来源 `cold`/`ready` 只覆盖那个 `sessionId`；其他会话或用户仍可能改写目标。
6. **计数只在被引用的 JSONL 里算。** 同一字符串可能大量出现在讨论它的其他会话；`0` 次才判 `ABSENT`，再读取承载该事实的记录的真实 `timestamp`。
7. **零出现不等于可以猜。** 不得用相邻时刻、摘要或记忆替代真实 `timestamp`。
8. **最小修正，逐次复检。** 一个 Edit 只改一个逻辑点；Edit 前备份到包外；Edit 后立即记录 size、mtime、SHA-256。
9. **分别记录两份哈希。** `SKILL.md` 与 `references/` 的哈希独立；`skill-file-qa` 的指纹只覆盖 `SKILL.md`。
10. **不越界。** 不 commit、不 push、不修改包外文件、不宣称 `/skills reload` 或运行时已加载。

## 步骤 0 — 停写并归因

1. 冻结目标：文件清单、size、`mtime_ns`、SHA-256、`Files (N)`。
2. 确认目录是否由 `create` 推荐之外的事件产生；记录首次出现时刻。
3. 扫描项目 JSONL 中的 `Write`/`Edit`：

```bash
py -3 -B - <<'PY'
import json, glob
target = "auditer-skill-cree-par-session-source"
for path in glob.glob("C:/Users/<user>/.qoder/projects/<project>/*.jsonl"):
    for line in open(path, encoding="utf-8", errors="replace"):
        try:
            rec = json.loads(line)
        except Exception:
            continue
        for block in (rec.get("message") or {}).get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            if block.get("name") not in ("Write", "Edit"):
                continue
            fp = str((block.get("input") or {}).get("file_path", ""))
            if target in fp:
                print(rec.get("sessionId"), rec.get("timestamp"), block["name"], fp)
PY
```

4. 逐个列出写入者；若唯一写入者就是被引用的来源会话，推荐前提过期，进入步骤 1。若还有其他写入者，按 `audit-skill-during-live-creation` 处理。

## 步骤 1 — 等待静默

1. `wait_chat_sessions` 对来源会话与全部写入者各调用一次；记录 `runtimeState`、`activeTurnId`、`revision`。
2. 只有 `ready` + `activeTurnId: null`、`waiting-user` + `pendingInteractionCount ≥ 1`（用户确认不回复）或 `cold` 才进入候选；`timeout`、`turn_completed` 不等于文件已静默。
3. 对全包连续三次采样 `size`、`mtime_ns`、SHA-256；任一变则回步骤 0。
4. 不要把 `turn_completed` 当成验收通过。

## 步骤 2 — 静默后复核现有包

1. 完整重读 `SKILL.md`、`references/` 与脚本文件；不复用等待期间的缓存。
2. 重跑 `skill-file-qa`，要求 `RESULT PASS`、`Files (N)` 与文件清单一致。
3. 目标自带夹具时，按 `replay-skill-reference-fixtures` 在包外重放；记录退出码与 `FAILS=`。
4. 双采样哈希：编辑前、编辑后各一次；任何漂移先停写并重读。

## 步骤 3 — 在被引用的 JSONL 中重算证据

1. 打开**被引用的那个** JSONL，不用讨论它的其他会话。
2. 对每个声称的时刻或 ID，逐字计数：

```bash
grep -c '<exact-token>' "<cited-session>.jsonl"   # 0 = ABSENT
grep -n '<exact-token>' "<cited-session>.jsonl"   # N > 0 = 正对照
```

3. `0` 次：判 `ABSENT`。找到承载该事实的记录，读取它的 `timestamp`，写成新的精确值。
4. `N > 0`：至少逐条查看命中记录的类型；总数可能包含 `file-history-snapshot` 等非事实载体，真正的载体通常是 `type: user` 的人类记录。
5. 计数与断言必须来自本次实测；不得引用摘要、旧回复或相邻时刻。

## 步骤 4 — 单行最小修正

1. 备份到包外并记录备份 SHA-256。
2. Edit 前复检：当前哈希等于基线；计划缺陷仍为 `CURRENT`（不是 `ALREADY_FIXED`/`GONE`/`CHANGED`）。
3. 一个 Edit 只改一个逻辑点；`old_string` 必须唯一。
4. `Edit` 返回 `The file changed since your last read` 立即停写，重读并 diff。
5. 只在缺陷位于 `references/` 时改 references；`SKILL.md` 无缺陷则保持字节不变，并记录这一事实。
6. 重跑 `skill-file-qa`；分别记录 `SKILL.md` 与 `references/` 的 SHA-256。
7. 不 commit、不 push；不把修正说成“已加载”。

## 报告模板

```text
Mode: STALE-CREATE / READ-ONLY AUDIT
Recommandation: <skillName> ; cible: <path> ; absent à <UTC> ; apparu à <UTC>
Écrivain: <sessionId> (référencée: oui/non) ; <JSONL path> ; <Write/Edit> ; <UTC>
Quiescence: <ready+activeTurnId=null|cold|waiting-user> ; 3 empreintes: <oui/non>
Paquet: Files (N) ; QA: <PASS/FAIL> ; fixtures: <résultat>
Preuves: <token> dans <JSONL cité>: 0/N ; timestamp réel: <UTC>
Correction: <fichier:ligne> ; avant -> après ; SKILL.md: <inchangé|hash>
Empreintes: SKILL.md <sha> ; references <sha>
Non vérifié: <branches>
```

## 诊断

| 症状 | 原因 | 动作 |
|---|---|---|
| 目标在两次 `ls` 之间出现 | 来源会话正在写 | 零写入；按 JSONL 归因 |
| JSONL 扫描 0 命中 | `file_path` 写法不同或扫描目录错 | 用精确路径重扫；空扫描不等于无写入者 |
| `wait_chat_sessions` 不返回 `cold` | 该状态可能永不出现 | 用 ready+activeTurnId=null 或 waiting-user 判定 |
| 时刻在别的 JSONL 命中很多次 | 讨论该文档的会话污染 | 只算被引用的那份 |
| 0 次后想“就近取整” | 用相邻时刻替代 | 禁止；读取真实 `timestamp` |
| references 改了、SKILL.md 哈希也变 | 编辑范围过大 | 停止；备份 diff；只保留单行修正 |
| QA PASS 但证据仍错 | 校验器不读散文 | 在 JSONL 中重算，不重跑 QA 了事 |

## 完成检查清单

- [ ] 目标未由本会话创建，未覆盖任何既有文件
- [ ] 写入者已按 JSONL `Write`/`Edit` 与 `file_path` 归因
- [ ] 已确认唯一/首要写入者是被引用的来源会话
- [ ] 静默条件满足，全包三次指纹一致
- [ ] 静默后重读全部文件并重跑 `skill-file-qa`
- [ ] 每个证据时刻都在被引用的 JSONL 中计数
- [ ] 0 次判 `ABSENT`，并写入真实 `timestamp`
- [ ] 只做单行最小修正，逐次记录哈希
- [ ] `SKILL.md` 与 `references/` 哈希分别记录
- [ ] 未 commit、未 push、未宣称已加载

## 已验证案例（2026-10-28，会话 ce25942a）

来源会话 `2ca337d6` 在为 `verifier-comptage-diff-fixture-dense` 写包；`ce25942a` 被要求依据它创建 Skill。

1. 02:35:55Z：`ce25942a` 检查目标目录，返回 `No such file or directory`。
2. 02:36:04Z：`2ca337d6` 收到用户消息「按方案执行，写入两个文件」。
3. 02:37:04Z / 02:37:20Z：`SKILL.md`（11,575 B）与证据文件（4,936 B）落盘；此刻 `2ca337d6` 为 `running`，`activeTurnId` 非空。
4. `ce25942a` 零写入；`wait_chat_sessions` 返回 `turn_completed`，随后 `ready` + `activeTurnId: null`。
5. 证据档案称确认时刻为 `00:55:43.352Z`；在 `e22fe088` 中 `grep -c '00:55:43'` = **0**，`grep -c '00:55:48'` = **5**；真实记录为 JSONL 第 117 行、`2026-10-28T00:55:48.734Z`。
6. 单行修正 references 后，QA 仍为 10 pass / 0 fail / 0 warn；`SKILL.md` SHA-256 保持 `26b6f2d6…b962`，references 变为 `9389f6e5…4fed`。
7. 作者 `2ca337d6` 采纳该修正并归档：commit `8fc884c`，`SKILL.md` blob `667b7e2a`。

完整命令、输出与未验证项见 `references/cas-2026-10-28-ce25942a.md`。

## 资源

- `references/cas-2026-10-28-ce25942a.md`：时间线、JSONL 计数、哈希、QA 与归档证据。
- 判活与等待复用 `audit-skill-during-live-creation`；证据重算与追补复用 `adopter-skill-concurrent-apres-quiescence`。
