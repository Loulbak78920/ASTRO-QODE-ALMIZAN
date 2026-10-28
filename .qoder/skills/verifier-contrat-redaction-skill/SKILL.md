---
name: verifier-contrat-redaction-skill
description: "在 Skill 草稿写完、宣称完成前执行一次只读的交付前自检：先对候选 frontmatter 用 PyYAML 实测 name、单行 description 与 1024 字符上限（超限在写入前压缩，不等 skill-file-qa 报 FAIL），再逐处核对引用的工具报错是否为 tool_result 原文，禁止用译文或转述冒充原文（原文非中文时保留原句并另行标注译文），把「14:11:2x」一类近似时刻改成可验证的界（avant/après HH:MM:SS）或删除，然后回读实际文件逐句对账（QA PASS 不检查散文语义），重跑 skill-file-qa，按文件分别记录 size/mtime/SHA-256（校验器指纹只覆盖 SKILL.md），并用旧转述计数为 0、原文计数至少 1 的正负断言证明修正真正落盘。用于新建 Skill 首次 QA 因 description 超限失败、参考文件引用工具报错、时间戳不可验证、写入后需要证明每处自纠已生效。不用于接近 1024 字符的既有描述压缩改写（edit-skill-frontmatter-description）、Windows 控制台编码导致的标记损坏（verifier-unicode-fichiers-windows）、包完整性清理（skill-package-integrity-audit）或脚本输出契约复放（reparer-contrat-sortie-skill）。"
---

# 交付前写作契约自检

## 目标与范围

Skill 草稿已落盘、准备宣称「已创建/已更新」之前，跑一道只读闸门，检查四类可证伪的写作事实：描述长度、引文是否为原文、时刻是否可验证、修正是否真正落盘。本 Skill 不判断业务逻辑，也不替代静态验收。

## 什么时候用

- 新建 Skill 首次 `skill-file-qa` 因 description 超限失败，或担心超限。
- 正文或 references 引用了工具报错、错误串、退出码。
- 时间线里出现近似时刻，例如 `14:11:2x`、`vers 14:11`。
- 写后改过引文、时间或措辞，需要证明每一处都生效。
- QA 已 PASS，但仍需证明散文与来源原文一致。

## 什么时候不用

- 既有描述接近 1024，只需压缩改写：`edit-skill-frontmatter-description`。
- 只是控制台编码或断言标记损坏：`verifier-unicode-fichiers-windows`。
- 包完整性、缓存与归档清理：`skill-package-integrity-audit`。
- 脚本输出契约与文档不一致：`reparer-contrat-sortie-skill`。
- 写入前的断言分级与最小 Edit：`verify-skill-doc-claims-before-edit`。

## 不可协商规则

1. **1024 在写入前实测。** 超限先压缩，不靠写后 QA 兜底。validator 只在 `len(description) > 1024` 时 FAIL，1024 本身合法。
2. **引号里的工具报错必须逐字。** 每处都要能在 `tool_result` 或项目 JSONL 中找到原句；找不到就写「未取到原文」，不得换成语义等价句。
3. **原文语言优先。** 原文为中文或其他语言时保留原句；译文另起一句并标注「译文」，不得用译文替代原句。
4. **近似时刻只写界或删除。** `14:11:2x` 一类写法不可复核；用相邻工具输出的时间戳构造 `avant HH:MM:SS` / `après HH:MM:SS`。
5. **QA PASS 不等于文字正确。** validator 不读散文；PASS 后仍须 Read 回读全文，并与台账逐句对账。
6. **修正必须被断言证明。** `--zero` 只用于应已不含旧措辞的交付正文：旧措辞计数 0、新原文计数至少 1，同一块内做负向控制；证据档案的「更正前」列保留旧措辞属合法命中，不得对其断言 0。非 ASCII 标记用 `\uXXXX` 书写。

## 第 0 步 — 写前测长

```bash
mkdir -p "$HOME/.qoder/tmp/redaction-<run>"
# 候选 description 写入 desc.txt：纯文本，或带 frontmatter 的文件
py -3 -B "$HOME/.qoder/skills/verifier-contrat-redaction-skill/scripts/verifier_redaction.py" \
  --desc-file "$HOME/.qoder/tmp/redaction-<run>/desc.txt"
```

- 要求 `DESC_OK yes` 且 `RESULT PASS`；记录实际 `DESC_LEN`。
- 整行加引号；纯量含「冒号+空格」时漏引号会让 YAML 解析失败。
- 压缩到 1024 以内再 Write，不要先写超限值再等 QA 报 `FAIL description: … exceeds 1024`。
- 记录最终值，不要引用被舍弃的中间值。

## 第 1 步 — 原文而非转述

取证顺序：

1. 本次会话 `tool_result` 的原文；
2. 项目 JSONL `.qoder/projects/<project>/<sessionId>.jsonl`，按 `tool_use.id` 与 `tool_result` 配对；
3. 落盘的工具输出文件；
4. 都取不到时写「未取到原文」，并列出尝试过的路径。

- 从来源复制，不凭记忆重打；重打会得到语义相同、字面不同的句子。
- 同一个错误同时出现在 SKILL.md 与 references 时两处都改；先 `grep -n` 定位全部位置。
- 例：法文 « la ChatSession attendue n'existe pas » 与 « ChatSession introuvable » 都应写回原文「等待的 ChatSession 不存在」。

## 第 2 步 — 时刻有界

- 禁止：`HH:MM:2x`、`HH:MM:xx`、`vers HH:MM`、`约 HH:MM`。
- 可复核写法：`avant 14:11:33`（取自随后一条工具输出的时间戳）、`après …`，或删除该行。
- 界必须指到一条能复核的工具输出，不能由「看起来差不多」推出。
- 计时标注时区：会话消息用 UTC，shell 输出用本地偏移。

## 第 3 步 — 回读对账

- 重跑 QA 之前先 Read 每个交付文件；`PASS` 不覆盖散文。
- 逐句对照台账：引号内文本、数字、时区、Skill 名、文件路径。
- 发现不一致先改原文再复跑；不要只改正文、不改 references。

## 第 4 步 — 复跑 QA 与逐文件指纹

```bash
py -3 -B "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" <skill-dir> \
  --skills-root "$HOME/.qoder/skills" --workspace <workspace-root>
echo "QA_RC=$?"
cd <skill-dir> && find . -type f -printf '%s %p\n' | sort
cd <skill-dir> && sha256sum SKILL.md references/*.md
```

- 要求稳定指纹上的 `RESULT PASS`；记录 `Files (N)`、body 行数与 PASS/FAIL/WARN 实际计数。
- 分开记录每个文件的 size 与 SHA-256：validator 的 fingerprint 只覆盖 `SKILL.md`。

## 第 5 步 — 正负断言

```bash
# 一般目标包：--zero 只对已更正的交付正文
py -3 -B "$HOME/.qoder/skills/verifier-contrat-redaction-skill/scripts/verifier_redaction.py" \
  --skill-dir <skill-dir> \
  --count "SKILL.md=\u7b49\u5f85\u7684 ChatSession \u4e0d\u5b58\u5728" \
  --count "references/<cas>.md=\u7b49\u5f85\u7684 ChatSession \u4e0d\u5b58\u5728" \
  --zero "<corrected-body>=<old-wording>"

# 仅当文档把被禁模式当反例引用（含本 Skill 自检）时，逐文件排除
py -3 -B "$HOME/.qoder/skills/verifier-contrat-redaction-skill/scripts/verifier_redaction.py" \
  --skill-dir <skill-dir> \
  --approx-exclude SKILL.md --approx-exclude "references/<cas>.md"
```

- `--count` 要求至少 1 次命中，`--zero` 要求 0 次；任一不满足退出码 1。
- `--zero` 只用于应已不含旧措辞的交付正文。证据档案的「更正前」列会合法保留旧措辞，对其断言 0 必然失败；改用 `--count` 证明新原文存在，并回读确认旧措辞只出现在该列。
- 标记从来源原文复制后写成 ASCII 转义，不凭记忆重打；零计数命中前先用 `grep -n` 或 Read 复核（方法见 `verifier-unicode-fichiers-windows`）。
- 同一命令带 `--skill-dir` 时顺带体检：`NAME_MATCH`、`DESC_LEN`、`BODY_LINES`、`APPROX_TIME_HITS`、`CACHE_HITS`。
- 文档把被禁模式当反例引用时，用 `--approx-exclude <rel>` 逐文件排除，并保留 `APPROX_TIME_SKIPPED` 输出；报告中列出每个被排除文件及理由，不得整体跳过扫描。
- 自检本 Skill 时，`SKILL.md` 与 `references/cas-*.md` 都引用了被禁模式，两者都要排除；旧转述的 `--zero` 不适用（正文示例与「更正前」列都合法包含），只跑 `--count` 并以回读核对。
- 结束前清理本次产生的 `__pycache__` / `.pyc`。

## 错误与陷阱

| 症状 | 原因 | 动作 |
|---|---|---|
| `FAIL description: 1389 chars exceeds 1024` | 先写后测 | 回到第 0 步，压缩后再写 |
| 写前测 1096、写后 1011 | 压缩了两轮 | 以最终写盘值为准，不引用中间值 |
| QA PASS 但仍有译文 | validator 不检查散文 | 第 3 步回读，正文与 references 一起改 |
| 时间线出现 `14:11:2x` | 用估读代替工具时戳 | 换成 `avant HH:MM:SS` 或删除 |
| 旧转述计数 0，原文计数也 0 | 标记写错或文件路径错 | `grep -n` 复核标记与路径，再重跑 |
| 修正只在一处生效 | 只改了 SKILL.md | 搜全部交付文件后重跑断言 |
| `ZERO file=references/... hits=1 ok=no` | 对证据档案的「更正前」列断言 0 | 改用 `--count` 新原文 + 回读；零断言只用于交付正文 |
| 报告写了「已重载」 | 未做运行时绑定取证 | 只写「已创建」；绑定验证交给 `verify-skill-runtime-binding` |

## 完成检查

- [ ] 候选 description 在写入前实测 ≤1024、单行、已加引号。
- [ ] 所有工具报错引文可在 `tool_result` 或 JSONL 中逐字找到。
- [ ] 非中文原文保留原句，译文单独标注。
- [ ] 时间线无近似时刻；每个界都能复核。
- [ ] 已 Read 回读全部交付文件并与台账对账。
- [ ] `skill-file-qa` 在稳定指纹上 `RESULT PASS`，记录了 `Files (N)`。
- [ ] 每个文件单独记录了 size 与 SHA-256。
- [ ] `--zero` 只作用于已更正的交付正文；证据档案「更正前」列的合法命中未被误判。
- [ ] 自检引用被禁模式的文档时逐文件 `--approx-exclude`，报告列出豁免文件与理由。
- [ ] 应更正的交付正文中旧措辞计数 0、新原文计数至少 1，脚本退出码 0。
- [ ] 无 `__pycache__` / `.pyc`；未声称重载或运行时绑定。

## 资源

- `references/cas-2026-10-27-completer-delta.md` — 来源会话逐字证据、计数、更正前后原文、最终指纹与限制。
- `scripts/verifier_redaction.py` — 只读检查：写前测长、包体检、正负计数。

## 相关 Skill

- `skill-file-qa` — 写后结构、引用、行数与指纹验收。
- `edit-skill-frontmatter-description` — 既有描述接近 1024 时的压缩改写。
- `verifier-unicode-fichiers-windows` — 非 ASCII 标记的断言方法与编码陷阱。
- `write-skill-evidence-case-study` — references 证据档案的分级与哈希规范。
- `verify-skill-doc-claims-before-edit` — 写入前的断言分级与最小 Edit。
- `skill-package-integrity-audit` — 缓存与归档清理。
- `verify-skill-runtime-binding` — 写入后的运行时绑定取证。
