---
name: verifier-contrat-skill-adopte
description: "只读验收由其他会话或外部写入者产出的 Skill 包：先用连续全树指纹确认目录静止（默认 4 次相同采样，不用固定 sleep），冻结全包哈希并跑 skill-file-qa，再把该包与其文档所述的外部已安装目标 Skill 一并复制到临时夹具，按文档逐字复放输出契约（零出现必须配同块正对照、JSON 键集用集合比较、退出码先于管道、产物文件与提示同时断言），首次 RC≠0 先按夹具构造错误排查（同一路径双根、缺目录、副本名与 name 不符、缺参数），最后对 references 引用的哈希做带时点的时效对账并只清理本次夹具；目标目录零写入，写入者仍活跃时结论标 PROVISIONAL。中文触发：只读验收、并发产出的 Skill 包、采纳他人 Skill、外部目标契约、复放 RC=2、引用哈希过期、零写入报告；English: read-only acceptance, foreign skill package, external target contract, fixture construction error, stale evidence hash, provisional verdict; Français: acceptation en lecture seule, paquet produit par une autre session, contrat de sortie externe, erreur de fixture, preuve périmée. 不替代接管决策（adopt-concurrent-duplicate-skill）、写入者活性与归因（audit-skill-during-live-creation）、文档修复（reparer-contrat-sortie-skill）、KEY=VALUE 核对（verifier-parite-doc-script-skill）、包内夹具重放（replay-skill-reference-fixtures）、§N 追加（verifier-fraicheur-preuves-skill）。"
---

# 只读验收外部目标契约的 Skill 包

## 何时使用

- 一个 Skill 包由其他会话或外部写入者产出，要求只读验收，不得改动任何字节；
- 包的 SKILL.md 或 references 记录的输出契约（命令、JSON 键集、退出码、产物文件）针对另一个**已安装** Skill，而不是包内脚本；
- 需要给出 `ACCEPTÉ` / `ACCEPTÉ AVEC RÉSERVES` / `REFUSÉ`，并逐项标注证据等级。

不适用与委派：

| 需求 | 使用 |
|---|---|
| 接管、缩窄、停止、只读保留的决策 | `adopt-concurrent-duplicate-skill` |
| 写入者活性、JSONL 归因、QUIESCENT/PAUSED/RUNNING | `audit-skill-during-live-creation` |
| 验收后修复文档偏差 | `reparer-contrat-sortie-skill` |
| KEY=VALUE 令牌抽取与存在性核对 | `verifier-parite-doc-script-skill` |
| 包内自带夹具逐字重放 | `replay-skill-reference-fixtures` |
| 过期证据的 §N 追加与 PROVISIONAL 改写 | `verifier-fraicheur-preuves-skill` |
| 「只读」本身的副作用证明 | `verifier-effets-de-bord-verification-lecture-seule` |
| 结构、引用、指纹验收 | `skill-file-qa`（本 Skill 调用它） |

## 核心规则

1. **目标零写入。** 不建、不删、不改目标包内任何文件；所有副产物只放在 `$HOME/.qoder/tmp/<nonce>/`。
2. **静止先于阅读。** 全树指纹连续 4 次相同（默认 3 秒间隔）才算静止；不用固定 `sleep` 后单次采样。出现 `CHANGED` 或 RC 1 时写 `NOT_QUIESCENT` 并停止验收。
3. **快照即事实。** 在一次时点记录全部文件的 size/mtime_ns/SHA-256、QA 计数与 `Files (N)`；此后报告一律引用该时点，不写「当前」。
4. **副本同名。** 包副本目录名必须等于其 `name`，否则副本上的 `skill-file-qa` 会报 name 不符。
5. **外部目标一并复制。** 文档所述目标 Skill 不在包内；必须复制到 `$BASE/fixture/<target-name>`，并先核对它的冻结哈希。
6. **逐字复放。** 命令来自文档原文，不来自记忆或旧稿；一条偏差一次运行；RC 在管道之前取得。
7. **零出现必须有同块正对照。** 同一断言内先证明真实存在的段命中 ≥1 次，才允许把 0 次写成「从不输出」；正对照为 FALSE 时该断言作废。
8. **键集用集合比较。** 顶层、`skills[]`、快照文件分别断言，不用逐个 `in` 判断，不凭记忆列键。
9. **产物与提示同时断言。** 「无提示」只有文件确实存在时才有意义。
10. **不把环境相关值写成契约。** 快照字节数随根路径长度变化，时间戳与路径同理；只写不变量或带时点的观测。
11. **RC≠0 先查夹具。** 同一路径双根、缺目录、副本名不符、缺参数、相对路径解析，全部排除后才允许写契约失败。
12. **时效只做观测。** 重算 references 引用的哈希并按 CURRENT/STALE/ABSENT 分类；不改包、不追加 §N，只把结果写进验收报告。
13. **只清本次夹具。** 只删除本会话创建的 `$BASE`；父会话或他人的目录不属本次。
14. **活跃写入者 → PROVISIONAL。** 写入者仍 `running` 时，即使全部断言通过，结论也只能是临时性的。

## 流程

### 0. 确认来源与写入者

用 `read_chat_session` 记录 `runtimeState`、`activeTurnId`、`revision`、`hasMoreBefore`。写入者为 `running` 不阻止只读验收，但报告末尾必须写 `PROVISIONAL` 与观测时刻。

### 1. 判定静止

```bash
VCA="C:/Users/Administrateur/.qoder/skills/verifier-contrat-skill-adopte"
PKG="C:/Users/Administrateur/.qoder/skills/<nom-du-skill-a-accepter>"
py -3 -B "$VCA/scripts/verifier_contrat.py" arbre --racine "$PKG" \
  --echantillons 4 --intervalle 3
```

期望 4 个相同 `TREE_SHA256`、`STABLE=TRUE`、RC 0。RC 1 表示采样期间出现 `CHANGED`，RC 2 表示路径或参数错误。

### 2. 冻结包与基线

```bash
py -3 -B "$VCA/scripts/verifier_contrat.py" empreintes --racine "$PKG"
wc -l "$PKG/SKILL.md"
py -3 -B "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "$PKG" --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" \
  --stable-seconds 2 --stability-timeout 30
```

记录 `Files (N)`、body 行数、description 字符数、本地与跨 Skill 引用计数、`python=`/`js=`/`skipped=`、`Summary`、`RESULT`、RC 与 `Fingerprint (final)`。

校验器的代码块检查只覆盖 SKILL.md。references 里出现 Python 模板时 `python=0` 不代表没有代码；需要使用时自行编译该块，并注明是单独检查。

### 3. 建夹具（包含外部目标）

```bash
BASE="$HOME/.qoder/tmp/adoption-$(date +%Y%m%dT%H%M%S)-$$"
TARGET="<nom-du-skill-cible-externe>"
mkdir -p "$BASE/fixture" "$BASE/aux/root-a" "$BASE/aux/root-b" "$BASE/out"
cp -r "$PKG" "$BASE/fixture/$(basename "$PKG")"
cp -r "$HOME/.qoder/skills/$TARGET" "$BASE/fixture/$TARGET"
```

所有根参数都指向 `$BASE` 内；跨根负向控制必须使用两个不同目录（`root-a`、`root-b`），绝不能把同一路径同时传给两个根参数。

### 4. 建偏差台账

| ID | 文档位置 | 文档承诺 | 复放命令 | 断言 |
|---|---|---|---|---|
| A1 | SKILL.md 输出契约段 | 段头与计数行 | `--compare` | 零出现 + 正对照 |
| B1 | JSON 小节 | 12 个顶层键 | `--format json` | 集合相等 |
| C1 | 示例命令 | 无漂移且 RC 0 | 同根 compare | RC 与计数 |
| D1 | 产物说明 | 无提示但文件存在 | JSON + snapshot | 提示 0 次且文件存在 |

台账为空则不进入复放。文档没写、复放时自己发现的偏差另起一行并注明发现步骤。

### 5. 逐条复放

```bash
py -3 -B "$BASE/check.py" > "$BASE/out/A1.log" 2>&1; RC=$?; echo "RC=$RC"
```

断言脚本导入本 Skill 的辅助函数：

```python
import sys
sys.path.insert(0, r"C:\Users\Administrateur\.qoder\skills\verifier-contrat-skill-adopte\scripts")
from verifier_contrat import controle_zero, clefs, executer, jeton
```

- A 类：`controle_zero(texte, absent=..., present=..., prefixe="A1")`；
- B 类：`clefs(stdout, [...], prefixe="B1")`，快照文件先读全文再比较；
- C 类：`jeton("C1_RC", executer(cmd).returncode == 0)`，同根与异根各一次；
- D 类：`jeton("D1_FILE", Path(artifact).is_file())` 与提示次数为 0 同时成立。

### 6. RC≠0 先查夹具

| 顺序 | 症状 | 判定 |
|---|---|---|
| 1 | `must differ from` 且 RC 2 | 同一路径同时传给两个根 → 夹具错误 |
| 2 | `root not found` 且 RC 2 | 路径不存在或相对路径解析错 |
| 3 | QA 报 name 不符 | 副本目录名不等于 `name` |
| 4 | argparse usage 且 RC 2 | 缺参数或旗标拼错 |
| 5 | 行为依赖真实用户根 | 夹具未重定向，可能污染 |
| 6 | 以上全部排除 | 才写「文档未复现」 |

修正夹具后必须重跑整条命令并保留两次日志；不能只删掉失败记录。

### 7. 引用时效对账（只读）

```bash
grep -oE '[0-9a-f]{64}' "$PKG"/references/*.md | sort -u
sha256sum "$HOME/.qoder/skills/$TARGET/SKILL.md"
```

对每个被引哈希按 CURRENT / STALE / ABSENT 分类，并把「现为」式表述换算成带时点的观测（`YYYY-MM-DDTHH:MM±ZZ`）。不一致只写 RESERVE，不改包。

### 8. 报告与清理

报告包含：结论、快照时点与分别的文件哈希、QA 摘要、逐条复放 RC 与令牌、时效分类、零写入证明（前后指纹）、夹具清理与缓存检查、`PROVISIONAL` 标记。

若副本或被验收包在验收后再次变化，已有令牌只对快照时点成立；重跑前先回到第 1 步。

## 断言矩阵

| 类 | 文档承诺 | 必须断言 |
|---|---|---|
| A | 某段输出存在，或某段从不输出 | 零出现 + 同块正对照 |
| B | JSON 键集 | 集合相等，分别对顶层、数组元素、产物文件 |
| C | 退出码与计数 | RC 先于管道；假漂移也可是 RC 0 |
| D | 产物文件与提示 | 文件存在与提示次数同时断言 |
| E | 大小、时间戳、路径 | 不写成契约，只写带时点观测 |

## 失败模式

| 现象 | 误判 | 处理 |
|---|---|---|
| 首次复放 RC 2 | 文档没复现 | 先查双根同路径、缺目录、副本名、缺参数 |
| 包描述外部目标却未复制 | 得到 `removed: 1` 假漂移 | 复制目标到 `fixture/<target-name>` 再跑 |
| QA 报 `python=0` | 认为 references 无代码 | 单独编译 references 代码块并标注 |
| 引用值写成「现为」 | 交付即过期 | 改带时点观测并标 RESERVE |
| 把快照字节数写成契约 | 换环境即失败 | 只断言键集与结构 |
| 固定 `sleep` 后单次采样 | 误判静止 | 改用连续全树指纹 |
| 采样一致即认为包完整 | 漏掉空 references | 再读全文件并跑 QA |
| PASS 后包又被写 | 继续引用旧 PASS | 旧验收作废，回到第 1 步或标 PROVISIONAL |

## 完成检查

- [ ] 目标包前后哈希一致，零写入；
- [ ] 静止采样为 4 个相同树指纹，或已写 `NOT_QUIESCENT`；
- [ ] QA 在稳定指纹上 `RESULT PASS`，`Files (N)`、body、引用计数已记录；
- [ ] 包副本与外部目标副本都在 `$BASE/fixture`，目录名与 `name` 一致；
- [ ] 每条偏差都有 RC、日志路径与 `_TRUE|_FALSE` 令牌；
- [ ] 零出现断言均配有同块正对照；
- [ ] RC≠0 的用例已按第 6 节顺序排除夹具错误；
- [ ] references 引用哈希已分类并按带时点观测记录；
- [ ] 只删除本次 `$BASE`，目标与目标 Skill 无 `__pycache__`；
- [ ] 写入者仍活跃时报告标 `PROVISIONAL`。

## 资源

- `scripts/verifier_contrat.py`：`arbre`（全树稳定采样）、`empreintes`（size/mtime_ns/SHA-256）、`selftest`（含负向控制）；可导入 `controle_zero`、`clefs`、`executer`、`jeton`。输出 ASCII，退出码 0/1/2。
- `references/cas-2026-10-27-adoption-lecture-seule.md`：2026-10-27 的只读采纳案例，含 RC=2 夹具纠错、14 项令牌、过期哈希与后续漂移的时点记录。
