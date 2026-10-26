# 案例：创建前的能力覆盖审计（2026-10-27）

本文件记录 `auditer-couverture-skill-avant-creation` 的来源会话、覆盖判定、历史 Skill 恢复、脚本实测与限制。所有计数和哈希都是测量时刻的快照；复用时必须重新测量。

## 1. 结论

- 对全部已安装 Skill 做「全根枚举 + 三层 token 检索 + 条款/实现双读 + 五态判定 + 决策」的创建前门禁，在 2026-10-27 的磁盘上判 `ABSENT`，因此新建本 Skill。
- 四个相邻 Skill 分别判 `PARTIAL`、`PARTIAL`、`PARTIAL`、`REFERENCE`（只覆盖相邻门禁，不覆盖本流程）。
- 历史 audit-recouvrement-skills-avant-creation 的最终版已从归档仓库逐字恢复（34,040 B，369 行，SHA-256 `2b86cf437a58043356555219a4144cc95336ef7e71ca4e525a96cc99db69a104`）；本 Skill 保留其仍有效的规则，但不恢复旧名称。

## 2. 来源会话

### 2.1 会话 77e56b5c（本 Skill 的直接来源）

- `read_chat_session`：4 条消息、`revision=57`、`hasMoreBefore=false`、`runtimeState=running`；落盘 JSONL 逐行解析，用户回合时间 `2026-10-26T23:17:40.298Z`。
- 该会话按推荐处理 `verifier-mutation-fixture-appliquee`：读取来源会话、复核变异门禁、创建 Skill。它没有用户纠正；变异失败均由代理自查发现。
- 关键检索：`grep -rln "变异" --include=SKILL.md` 命中 `audit-skill-tool-contracts`（`SKILL.md` 与 `references/contract-audit.md`）；再读规则 8 与 `scripts/audit_contracts.py`，据此把通用变异门禁让出，只保留夹具变异质量门禁。
- 本 Skill 把这次「先查覆盖、再让出重叠」的动作通用化，并补上它当时没有做的全根枚举与矩阵。

### 2.2 会话 7bc3b7ac（被 77e56b5c 读取的上游）

- 读取时 `runtimeState=ready`、`revision=42`；97 行 JSONL，唯一人类消息在第 3 行；复读时 `runtimeState=error`。
- 实际检查了 5 个 Skill：`skill-validator-selftest`、`develop-skill-static-checker`、`replay-skill-reference-fixtures`、`valider-harnais-fixture-windows-msys`、`tester-fixture-triage-snapshots`；漏掉 `audit-skill-tool-contracts`。
- 推荐 JSON 写「四个」→ 计数不准确（5 个），但「漏查重叠」的实质成立。该错误说明：按记忆挑相邻 Skill 会漏掉真正承重的门禁。

## 3. 覆盖矩阵（测量时刻）

枚举：`SKILLS 71 (user=69 project=2)`；首次样本为 70（user=68 project=2），最终复核为 71，期间 user 根新增 1 个目录（身份未归因，同期多个目录 mtime 变化）。

| 能力声明 | Skill | 规范条款 | 实现 | 判定 | 依据与哈希 |
|---|---|---|---|---|---|
| D1 全根枚举 + 三层检索 + 五态判定 + 决策 | 无 | 无 | 无 | ABSENT | 判据 token 只在相邻 Skill 的不同语义中出现 |
| 已安装 Skill 清单与计数 | inventory-installed-skills | SKILL.md:3 明确「不替代规则覆盖审计」；SKILL.md:15 写历史名称不可用 | scripts/inventory_skills.py 只盘点 name/description | PARTIAL | SKILL.md `24a675137f77bcb7a53340584a1ba717c9cc30e0a34fc63a2b35a1ae34218b67`；脚本 `262998a35c11a7e0c89688d539a48b8d79230cc5af394b1ef4fb4c9bab8a5936` |
| 能力矩阵与「收窄后新建」 | adopt-concurrent-duplicate-skill | SKILL.md:126-129 能力矩阵、只写增量、委派边界 | 无独立检索脚本 | PARTIAL | 只在同名/职责重合目标已出现时触发，不是创建前全根审计；SKILL.md `54528881db72c80d0e2129f9cab5cf152d4675884b8d6a4be6c950a2258539af` |
| 推荐声明与来源会话对账 | verify-skill-recommendation-claims | SKILL.md:108-129 声明分类与决策 | 无全根能力检索 | PARTIAL | 对账推荐，不做跨 SKILL.md/references/scripts 的能力 token 搜索；SKILL.md `13771eb7a68c9600de83908b0ebe16cbf396eff550f89270b1f90ca6cc15f181` |
| 负向测试先证明变异生效 | audit-skill-tool-contracts | SKILL.md:35 规则 8 | scripts/audit_contracts.py:1127-1128、1231-1232 失败分支 | REFERENCE | 是工具契约门禁，不是覆盖审计；SKILL.md `edc8c587fab1e7e798b2a7978049924912dc63ff1305408edd7915bc120eb83f`；脚本 `3e0dddfa6c9d227b964fd063cb4b10806a41a83284e42b4cec484bf0145b0572` |
| 历史覆盖审计 Skill | audit-recouvrement-skills-avant-creation | 已删除；最终版已恢复 | 见第 4 节 | SUPERSEDED | 名称不写成当前可解析引用 |

### 3.1 token 命中（本文件落盘前，71 个 Skill）

下表测于 `SKILL.md` 与脚本已在盘、本 references 尚未落盘时。

| token | occurrences | skills | 说明 |
|---|---|---|---|
| `before == after` | 6 | 2 | 5 次在 audit-skill-tool-contracts，1 次在本 Skill |
| `mutation ineffective` | 5 | 2 | 同上 |
| `变异` | 104 | 8 | audit-skill-tool-contracts、develop-skill-static-checker、harden-skill-argument-substitution、skill-update-concurrency-safe、tester-fixture-triage-snapshots、verifier-mutation-fixture-appliquee、verifier-unicode-fichiers-windows、本 Skill |
| `覆盖` | 304 | 41 | `WARN TOKEN_TOO_GENERIC`，不能单独作判据 |
| `COVERED` | 12 | 3 | 本 Skill、verify-skill-doc-claims-before-edit（证据等级）、verify-skill-git-head-vs-worktree（英文 covered） |
| `能力矩阵` | 10 | 1 | 只有 adopt-concurrent-duplicate-skill |
| `覆盖审计` | 5 | 3 | 本 Skill、harden（历史名称见证）、inventory（声明不替代） |
| `capability coverage` | 3 | 1 | 只有本 Skill |
| `couverture` | 22 | 6 | 多为「测试覆盖/变体覆盖」，语义不同 |
| `ABSENT` | 436 | 53 | `WARN TOO_GENERIC`，不作判据 |

结论不是靠单个 token 的 0 命中断定，而是靠：全根枚举 + 对四个候选 Skill 的条款与实现双读 + `capability coverage` 只在本 Skill 命中。

**自引用污染**：本文件落盘后，上表每个 token 都会增加本 Skill 的自命中（每次编辑本文件仍会变化），因此复跑计数必然高于审计时刻，且不构成回归。自命中只影响计数，不改变 ABSENT 判定，因为判定依据是候选 Skill 的条款与实现双读，而不是全库总命中数。高区分度 token（如 `capability coverage`）的自命中正是本 Skill 存在后的预期结果，不能据此声称「审计前已覆盖」。

## 4. 历史 Skill 的恢复

### 4.1 首版（本地 JSONL）

- 来源会话 `dd18d4e9-2ba3-488d-af7b-2d58f2220ebf` 的 JSONL 第 120 行为一次 Write，`file_path` 指向历史目录的 `SKILL.md`。
- 提取结果：6,682 字符、12,741 字节、196 行、SHA-256 `50eea72e67d0ad5731f9ef5d37ff34c5ff95bcfbb19ba086243b30bbbfe8f5be`，与 `verifier-citations-lignes-skill/references/cas-2026-10-26.md:9` 记录一致。

### 4.2 最终版（归档仓库）

- 本地备份 `~/.qoder/tmp/audit-recouvrement-deleted-20261026T1700` 已被清理，2026-10-27 复查不存在。
- `harden-skill-argument-substitution/SKILL.md:14` 记录：该 Skill 于 2026-10-26 17:07 +01:00 仍存在（34,040 B），17:09 已不在用户级 skills 根。
- 归档仓库 `IMAM8MAHDI/audit-recouvrement-skills-avant-creation`：`ARCHIVED=True`、`PRIVATE=True`、默认分支 `skill/audit-recouvrement-skills-avant-creation`、HEAD `a010e3a967cb693750c04078ca143f4a0ab5ae3b`（来自 `retirer-depot-github-et-copie-locale` 的案例记录）。
- 未认证 raw URL 返回 404 属私有仓库的预期；本轮用 Git Credential Manager 的已存凭据做一次只读 API GET，仅取 `SKILL.md`，未打印凭据、未写入远端。
- 取回结果：34,040 字节、369 行、SHA-256 `2b86cf437a58043356555219a4144cc95336ef7e71ca4e525a96cc99db69a104`、blob `df0806566399001bd6d9a42c3cba5f504a4d8dcf`，与本地备份记录的哈希一致。
- 会话 `7f6f22fe` 的 10 次 Edit 无法在首版上重放（第一条 `old_string` 在首版出现 0 次），说明最终版包含其他会话的扩展；最终版以归档仓库为准。

### 4.3 保留与不复制

并入本 Skill 的规则：两次全根快照与 diff、`STALE` 稳定门禁、`CONFLICT` 停止、基线已存在不等于并发、声明资源先于委派、来源断言独立复跑、`0 found` 假 PASS、不复制第二份事实源、注入层位置变量提示。

未复制的细节：历史 Skill 的四态夹具矩阵、校验器五形态矩阵、22 行错误表、20 项完成清单与逐会话来源日志。按「不复制第二份事实源」，这些只保留在归档仓库中，本 Skill 不维护副本；需要时按 4.2 的仓库与分支取回。

## 5. 脚本实测（最终字节）

脚本：`scripts/audit_coverage.py`，SHA-256 `4c8a6326e2f9728b53403f22b0771469cbcf1c44fb2116f54eeb61fa52d2b217`。

| 用例 | 结果 |
|---|---|
| `--help` | rc=0 |
| `--list-skills` | `SKILLS 71 (user=69 project=2)`，与磁盘 `find` 的 69+2 一致；`RESULT OK` rc=0 |
| 正例 token（`before == after`、`mutation ineffective`、`变异`、`覆盖`） | rc=0；审计时刻计数见 3.1（落盘后含自命中，复跑会更高）；`覆盖` 触发 `TOKEN_TOO_GENERIC` |
| 负例 token（运行期生成，如 `NEG="ZZZ_NEG_$(date +%s)_$RANDOM"`） | 0 命中，`WARN TOKEN_NO_HIT`，`RESULT OK` rc=0；字面负例会被本文件自身命中，故必须运行期生成 |
| ASCII 短 token `ls` | rc=2，`ERROR: ASCII literal tokens shorter than 3 chars are too generic: ls` |
| 无 token | rc=2，`ERROR: provide at least one --token (or use --list-skills)` |
| `--format json` + `覆盖` | JSON 可解析；`result=OK`，71 个 Skill，命中数与 3.1 同源（含自命中） |
| `--regex 'before\s*==\s*after'` | rc=0，2 个 Skill（落盘后复测 8 次命中，含自命中） |
| 大小写：`--token "$(py -3 -c "print('mutation ineffective'.title())")"` | 默认忽略大小写，命中与全小写相同的 2 个 Skill |
| 大小写：同一 title-case token 加 `--case-sensitive` | 0 命中 + `TOKEN_NO_HIT`；磁盘只有全小写形式，对照成立且不依赖写入文件的字面量 |
| `--token 变异 --max-hits-per-skill 1` | 8 个命中 Skill 各 1 条，按 Skill 截断生效 |
| 无效 user root `C:/no/such` | rc=2，`ERROR: user root not found` |
| 只读性 | 运行前后 `audit-skill-tool-contracts` 的 SKILL.md 与脚本 SHA-256 不变；本 Skill 无 `__pycache__`/`.pyc` |

环境说明：首次 JSON 测试把输出写到 MSYS 的 `/tmp`，再用原生 `py -3` 打开同一路径失败（MSYS 与原生 Python 的路径映射不同）；改用工作区相对路径后通过。这是测试命令的问题，不是脚本缺陷。

## 6. 限制与证据分级

- **已核实**：两次枚举计数与磁盘一致；四个候选 Skill 的条款与实现行号；历史 Skill 两版的字节数与 SHA-256；脚本第 5 节各用例的退出码与输出；运行前后目标哈希不变。
- **推断**：首次样本 70 与最终 71 的差异为 1 个新增目录；最终样本中 `变异` 的 8 个 Skill 归因来自脚本输出。
- **未验证**：首次样本与最终样本之间新增目录的具体身份（同期多个目录 mtime 变化，未逐目录比对）；历史 Skill 的最终版在两次快照之间是否还有未归档的本地改动；`覆盖`/`ABSENT` 等泛词的 41/53 个命中未逐个人工阅读，判据依赖候选 Skill 双读与高区分度 token。
- 来源会话 77e56b5c 在审计期间仍活动，7bc3b7ac 复读为 `error`；本文件只引用已落盘内容，不把活性字段当作写入完成。
- `file:line` 只在第 3 节记录的哈希窗口内有效；被引 Skill 变更后先重测再复用。
- 归档仓库的读取是只读 GET；没有推送、修改、取消归档或删除任何远端内容。

## 7. 复跑

```bash
cd <workspace>
export PYTHONIOENCODING=utf-8
S="$HOME/.qoder/skills/auditer-couverture-skill-avant-creation/scripts/audit_coverage.py"
py -3 "$S" --list-skills
py -3 "$S" --token "before == after" --token "mutation ineffective" \
  --token 变异 --token 覆盖
NEG="ZZZ_NEG_$(date +%s)_$RANDOM"
py -3 "$S" --token "$NEG"
py -3 "$S" --token "覆盖" --format json
TITLE="$(py -3 -c "print('mutation ineffective'.title())")"
py -3 "$S" --token "$TITLE"
py -3 "$S" --token "$TITLE" --case-sensitive
py -3 "$S" --user-root "C:/no/such" --list-skills
```

预期：`SKILLS n (user=u project=p)` 且 `n=u+p`；正例 `RESULT OK` rc=0；`NEG` 0 命中且 rc=0；`TITLE` 默认有命中、加 `--case-sensitive` 后 0 命中；无效根 rc=2。计数随本 Skill 正文与 references 自引用变化，以当次输出为准。写入后验收用 `skill-file-qa` 的 `validate_skill.py <skill-dir> --workspace <workspace>`，要求 `Files (3)`、`RESULT PASS`、rc=0。
