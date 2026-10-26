---
name: verifier-citations-lignes-skill
description: "在写入或修改 Skill 后，逐条核对「目标文件 + 行号」引用指向的内容是否仍与引用处的主张一致：解析相对路径、Skill 名、file:// 与绝对路径，读取被引行，用引用处的期望短语比对，输出 MATCH、DRIFT（含 now_at）、MISSING、READ、AMBIGUOUS，并记录引用文档与被引文件的 SHA-256；行号只在记录的哈希窗口内有效，DRIFT 先报告、经确认后最小改行号。用于引用行号漂移、目标 Skill 被改写后旧行号失效、跨 Skill 行号引用、证据档案中的 file:line、审计报告引用复核、QA 已 PASS 但引用内容已变。不替代 skill-file-qa 的存在性与格式检查、verify-cross-skill-reference-liveness 的名称存活检查、verifier-fraicheur-preuves-skill 的哈希新鲜度检查。English: skill citation line verification, stale line numbers, drift detection, file:line audit. Français: vérification des citations ligne, dérive de numéro de ligne."
---

# 校验 Skill 中的行号引用

## 目标与边界

Skill、证据档案或审计报告里的 `path:line` 引用会随目标文件被其他会话改写而指向别的句子。`skill-file-qa` 只检查引用名称能否解析、文件是否存在；它不读被引行，也不比对内容。本 Skill 用只读脚本把「引用处的主张」与「被引行当前文本」逐条对照，并记录两侧哈希。

不替代以下属主：

- `skill-file-qa`：frontmatter、布局、名称与文件存在性、代码块语法、指纹；
- `verify-cross-skill-reference-liveness`：反引号中的 Skill 名称是否存活；
- `verifier-fraicheur-preuves-skill`：尺寸、mtime、哈希是否过期；
- `skill-update-concurrency-safe`：写入期间的并发与双采样；
- `replay-skill-reference-fixtures`：复跑参考文件中的夹具；
- `audit-session-evidence`：来源会话取证。

本 Skill 只读引用文档与被引文件；唯一允许的写入是用户确认后的最小行号修正。

## 何时使用

- SKILL.md、references 或审计报告含 `path:line` 引用，且目标文件可能已被其他会话改写；
- 交付前要证明矩阵、证据表、错误表中的行号仍然成立；
- 引用跨 Skill，例如 `skill-name` SKILL.md:<line>；
- 要复现「QA PASS 但引用内容已漂移」。

## 何时不用

- 只需检查引用名称或文件是否存在：用 `skill-file-qa`；
- 需要重建旧版本、复跑夹具：用对应的重建或回放 Skill；
- 目标文件仍在被写入：先按 `skill-update-concurrency-safe` 等稳定；
- 引用不是行号形式（只有文件名或章节标题）：本脚本不适用，人工核对。

## 不可协商规则

1. 期望短语必须来自**引用处的主张**（矩阵行、规则句、证据表），不能从被引行反抄，否则是循环论证。
2. 打印了被引行不等于验证；没有期望的引用是 `READ`，不是通过。
3. 行号只在记录的 SHA-256 窗口内有效；出现 `HASH_CHANGED` 或 `unstable>0` 时本次结论作废，必须重跑。
4. `MATCH` 只证明指定范围**包含**期望短语；不证明整段语义、引用位置恰当或来源可信。
5. `DRIFT` 先报告 `text_moved` / `text_not_found` 与 `now_at`；经确认后才最小改行号。命中多处时不得盲选第一处。
6. `MISSING` 先区分 `file_not_found` 与 `line_out_of_range`；不猜路径、不新建被引文件。
7. `AMBIGUOUS` 表示同名 Skill 存在于多个根；必须显式指定根，不默认取第一个。
8. 不修改被引文件，不改其他 Skill 的内容。
9. 脚本输出不替代 `skill-file-qa`；交付前两者都要跑。
10. 没有实际运行就写「未验证」；失败时不得宣称通过。

## 支持的引用形式

| 形式 | 示例（`<line>` 为占位符） | 解析方式 |
|---|---|---|
| 相对路径 | `./target.md:<line>` / `references/x.md:<line>` | 先引用文档目录，再 workspace |
| 相对片段 | `references/x.md#L<line>` | 同上 |
| file URL | `file:///C:/.../x.md#L<line>` | 绝对路径；前导 `/C:` 会被修正 |
| Windows 绝对路径 | `C:/.../x.md:<line>` | 直接读取 |
| Skill 路径 | `skill-name/SKILL.md:<line>` | 在给定的 skills 根中查找 |
| Skill 简写 | `skill-name` SKILL.md:<line> | 仅当该名称已安装 |

范围写成 `:<start>-<end>`，也接受 `#L<start>-L<end>`。

不识别裸文件名（没有 `./`、`../` 或目录前缀，如 `x.md:12`），这是有意跳过，避免把时间或版本号当引用。围栏代码块**不会**被剥离，只有反引号会被替换为空格；因此示例应使用 `<line>` 占位，或确保示例路径真实存在并为其写期望。

## 流程

### 0. 基线

记录引用文档与每个被引文件的 size、mtime_ns、SHA-256，确认两次采样稳定；有并发写入先停下。脚本运行时会在末尾输出被引文件的 `HASH` 行，可直接作为基线。

### 1. 枚举引用

先不带期望运行，得到清单；`READ` 表示「已读到但未验证」：

```bash
py -3 scripts/verifier_citations.py <doc-or-skill-dir> \
  --workspace <workspace-root> \
  --skills-root <user-skills-root>
```

### 2. 写期望

为每条要验证的引用逐字复制 `cite`（保留 `./`、`#`、范围端点），`contains` 从引用处的主张摘取唯一、可定位的短语：

```json
[
  {"cite": "./references/exemple.md:<line>", "contains": "该主张的关键短语"},
  {"cite": "skill-name/SKILL.md:<line>", "contains": "被引用规则的关键短语"}
]
```

### 3. 运行

```bash
py -3 scripts/verifier_citations.py <doc-or-skill-dir> \
  --workspace <workspace-root> \
  --skills-root <user-skills-root> \
  --expect-file <expectations.json> \
  --max-text 200
```

保存完整输出。退出码：0 PASS，1 FAIL，2 用法或环境错误（含被引文件不可读）。`--strict` 把 `READ` 与零引用也计为失败；`--ignore-case` 仅用于大小写差异已被确认无害的场景。

### 4. 分诊

- `MATCH`：记录对应 `HASH` 行的 SHA-256，行号与该哈希绑定。
- `DRIFT`：记录 `now_at`；不要立即改。
- `MISSING`：看 `file_not_found` 还是 `line_out_of_range total=N`。
- `AMBIGUOUS`：读 `candidates`，显式指定根。
- `READ`：未写期望，不是通过。
- `NOT_IN_DOC`：期望与正文 cite 不一致，逐字核对。

### 5. DRIFT 处置

1. 报告旧行号、`now_at`、当前哈希，等待用户确认。
2. 确认后只改引用行的行号或范围，不改其他 Skill 的内容。
3. 重跑；`now_at` 有多处时逐个打印候选行，禁止选第一处了事。
4. 期望短语本身已过时（目标规则被改写）：改写引用主张或降级为历史说明，不保留失效引用。

### 6. 写入后复验

- 重跑脚本：`not_in_doc=0`、`unstable=0`、无 `HASH_CHANGED`、`RESULT PASS`。
- 再跑 `skill-file-qa`（位置参数），要求 `RESULT PASS`、退出码 0。
- 分别记录 SKILL.md、references、scripts 的哈希；QA 指纹只覆盖 SKILL.md。

## 状态表

| 状态 | 含义 | 动作 |
|---|---|---|
| MATCH | 指定范围内含期望短语 | 记录哈希，人工复核引用是否恰当 |
| DRIFT | 不含；`now_at` 为启发式候选行 | 报告，确认后最小改行号 |
| MISSING | 文件不存在或行号越界 | 区分原因；不猜路径 |
| READ | 无期望 | 补期望，或标「未验证」 |
| AMBIGUOUS | 同名 Skill 存在于多个根 | 显式 `--skills-root` |
| UNREADABLE | 读取或解码失败 | 退出 2；报告「未检查」 |
| NOT_IN_DOC | 期望没有对应引用 | 核对 cite 是否逐字一致 |
| HASH_CHANGED | 运行期间文件变化 | 结论作废，重跑 |

## 错误表

| 症状 | 根因 | 动作 |
|---|---|---|
| `file:///C:/...` 解析成 `/C:/...` | 未剥离 URL 前导斜杠 | 本脚本已修正；自建解析时去 `file://` 与 `/C:` |
| `./x.md:<line>` 未被列出 | 裸文件名被有意跳过 | 加 `./` 或目录前缀 |
| `NOT_IN_DOC` | cite 与正文不完全一致（空格、反引号、范围） | 逐字复制 cite |
| 同一路径多条引用期望错配 | 期望按行号重叠、先到先得 | 让范围不重叠或合并期望 |
| `AMBIGUOUS` | 用户级与项目级存在同名 Skill | 显式 `--skills-root` |
| 中文输出崩溃 `UnicodeEncodeError: cp1252` | 控制台编码 | 设 `PYTHONIOENCODING=utf-8`；脚本已 reconfigure |
| 只读断言显示文件变了 | before/after 哈希清单把自己算进去 | 排除清单与日志文件 |
| 围栏示例被当引用 | 脚本不剥离围栏 | 示例用 `<line>` 占位 |
| 行号对但语义不对 | `MATCH` 只做子串包含 | 人工复核引用主张是否恰当 |

## 完成清单

- [ ] 引用文档与被引文件都有基线哈希，采样稳定。
- [ ] 每条要验证的引用都有来自引用处的 `contains`，未从被引行反抄。
- [ ] 脚本实际运行，完整输出已保存。
- [ ] `not_in_doc=0`、`unstable=0`、无 `HASH_CHANGED`。
- [ ] 所有 DRIFT / MISSING / AMBIGUOUS 都有处置记录；改行号经用户确认。
- [ ] 未修改其他 Skill，未新建被引文件。
- [ ] `skill-file-qa` 已运行且 `RESULT PASS`、退出码 0。
- [ ] 三类文件哈希分别记录；报告区分已验证与未验证。

## 报告模板

```text
DOC / DOC_SHA256
BASE <file> size mtime_ns sha256
CITATION ... status=... detail=... now_at=...
SUMMARY total=... match=... drift=... missing=... read=... ambiguous=... not_in_doc=... unstable=...
RESULT / EXIT
处置：<确认人、时间、最小改动>
未验证：<项或「无」>
```

## 资源

- `scripts/verifier_citations.py`：只读校验器；支持 `--strict`、`--ignore-case`、`--max-text`。
- `references/cas-2026-10-26.md`：来源会话事实、真实漂移案例、夹具矩阵、只读证明与限制。

## 来源与证据

2026-10-26 会话 `dd18d4e9-2ba3-488d-af7b-2d58f2220ebf`（快照 revision 0、cold、2 条消息）创建了历史名称 audit-recouvrement-skills-avant-creation（当前不在用户级或项目级 skills 根）。该 Skill 当时 195 行、12,741 B、SHA-256 `50eea72e…`；5 条 `file:line` 引用被逐行打印并人工比对，`skill-file-qa` 为 9 PASS / 0 FAIL / 0 WARN、`Files (1)`、8 个跨 Skill 引用。该会话没有写入失败，也没有用户纠正；失败仅有目标目录不存在导致的 `ls` 退出 2，以及 cp1252 控制台崩溃。

2026-10-27 复核：该产物目录已不存在。`skill-file-qa` 的 SKILL.md 当前 SHA-256 `4226b3d4…`，同一句跨 Skill 规则从 2026-10-26 的第 144 行移到第 182 行，第 144 行现在是指纹规则；`skill-file-qa` 仍在同一份文件上给出 PASS，说明存在性与格式校验无法发现内容漂移。本 Skill 的 4 条现行引用经脚本实测 MATCH：`tester-publication-isolee-skill` SKILL.md:144、`skill-update-concurrency-safe` SKILL.md:35、`audit-session-evidence` SKILL.md:138、`skill-file-qa` SKILL.md:182；旧行号以 DRIFT 复现（`now_at=L36,L182`）。完整哈希、夹具矩阵与限制见 `references/cas-2026-10-26.md`。
