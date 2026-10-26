---
name: verifier-unicode-fichiers-windows
description: "在 Windows（Git Bash、Python 3.14、ANSI 代码页 cp1252）上逐字断言文件是否包含某段非 ASCII 文本：标记必须从 Edit 或 Write 的原文、Read 输出复制并以 ASCII 转义书写，不得凭记忆重打；任一计数为 0 时先用 grep -n、Read 或字节指纹独立复核，再判断是内容缺失还是标记写错；把控制台重音变成 U+FFFD 视为输出侧证据损坏而非文件损坏，断言通道保持纯 ASCII；用负向控制标记证明断言不空转；在临时副本上运行 validate_skill.py 时目录名必须等于 name。用于验证 Edit 或 Write 是否生效、中文字符或重音未找到、count 0、控制台乱码、heredoc 源码编码、误判内容缺失、FAIL name 掩盖真正断言等场景；不替代 skill-file-qa 的结构验收、windows-python-utf8-skill-scripts 的输出契约或 audit-session-evidence 的来源取证。"
---

# 在 Windows 上验证文件中的非 ASCII 文本

## 目标

证明某个非 ASCII 片段确实存在于文件中（或确实缺失），并且报告里的每个「命中/未命中」都能被独立复核。核心不是让控制台正确显示重音，而是让断言在编码、复制和显示三个环节都不产生假阴性。

## 何时使用

- Edit 或 Write 之后，要确认新增的重音字母、中文或全角标点真的落盘。
- 计数返回 0，需要区分「写入失败」与「标记写错了一个字」。
- 控制台输出出现 U+FFFD、`?` 或乱码，怀疑文件或编码被破坏。
- 用 `py -3 - <<'PY'`、`py -3 -c` 或 heredoc 做一次性断言。
- 在临时副本上运行 `validate_skill.py`，要确认失败原因不是目录名。

不适用：

- Skill 结构、frontmatter、引用与指纹验收：使用 `skill-file-qa`。
- Skill 脚本的 stdout 契约与退出码：使用 `windows-python-utf8-skill-scripts`。
- CSV/HTML 交付物验收：使用 `verifier-livrables-csv-html-windows-fr`。
- 来源会话证据审计：使用 `audit-session-evidence`。

## 核心规则

1. **标记必须复制，不能重打。** 从 Edit 的 `new_string`、Write 的内容或 Read 输出中复制；需要写进命令或文档时，使用 ASCII 转义（`\u00e9`、`\u4e2d`），让拼写和字符数可审。
2. **计数 0 只说明「用这个标记没找到」。** 它不是内容缺失的证据，必须换独立通道复核后才能下结论。
3. **至少两条独立通道，且输入形态不同。** 例如 Python 转义计数 + `grep -nF` 行号 + `Read` 指定区域 + 字节指纹。
4. **断言通道输出纯 ASCII。** 打印计数、`ascii(marker)` 和行号；不要靠控制台显示重音来判断。
5. **负向控制不可省。** 同一命令对一个人为变异的标记必须返回 0；否则断言可能恒真。
6. **输出乱码与文件损坏分开报告。** stdout 的 cp1252 字节被按 UTF-8 捕获会显示为 U+FFFD，文件本身可能完全正确。
7. **输入侧不要凭 `chcp` 推断。** Python 源码默认按 UTF-8 解析；cp1252 编码的源码会报 `SyntaxError: Non-UTF-8 code`，不会静默变乱码。`chcp` 显示 850 时 Python 的 `sys.stdin.encoding` 仍可能是 cp1252。
8. **副本目录名必须等于 `name`。** 在临时副本上运行 `validate_skill.py` 时，否则 `FAIL name` 会掩盖你真正想测的断言。

## 通道 A：ASCII 转义计数（Python）

```bash
py -3 -B -c 'from pathlib import Path; t = Path(r"<fichier>").read_text(encoding="utf-8"); m = "Cible cr\u00e9\u00e9e"; print("COUNT", t.count(m), "MARKER", ascii(m))'
```

- `<fichier>` 换成实际路径；Shell 单引号让 `\u00e9` 原样传给 Python。
- 输出 `MARKER 'Cible cr\xe9\xe9e'`：标记的转义与长度直接可审，漏一个 `\u00e9` 会立刻看出来。
- `-B` 避免写 `__pycache__`；不要用 `py_compile` 做临时校验。

## 通道 B：原文匹配与行号（Git Bash）

```bash
grep -nF 'Cible créée' '<fichier>'; echo "GREP_RC=$?"
```

- 仅在标记是从工具输出原样粘贴时使用；手打会把同一个拼写错误复制到第二通道。
- 无匹配时 `GREP_RC=1`。这不代表内容缺失，回到通道 A 并用 Read 看该区域。

## 通道 C：字节与区域确认

```bash
stat -c '%s | %y' '<fichier>'; sha256sum '<fichier>'; wc -l '<fichier>'
```

- 用 Read 读取通道 B 命中的行号附近，确认整行与上下文，而不只是子串。
- 需要看原始字节时：`od -c '<fichier>' | head`。UTF-8 的 `é` 显示为 `303 251`，单个 `351` 说明该文件是 cp1252 编码。

## 副本验收（校验器）

```bash
N=$(sed -n 's/^name: *//p' SKILL.md | head -1)
D="$HOME/.qoder/tmp/qa/$N"
mkdir -p "$D/references" && cp SKILL.md "$D/" && cp references/*.md "$D/references/" 2>/dev/null
py -3 -B "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$D"; echo "QA_RC=$?"
```

- 从 Skill 根目录运行。副本目录名取自 frontmatter 的 `name`，必须写成 `qa/<name>`；否则先得到 `FAIL name`，真正被测的断言根本没跑。
- 本机实测：`RESULT PASS`、9 pass / 0 fail / 0 warn、`QA_RC=0`；目录名不符时 `RESULT FAIL`、`QA_RC=1`；缺参数时 `QA_RC=2`。
- 校验器自报只读（`Validator: read-only`），不修改 Skill 文件；它只验证结构与引用，不验证断言内容。

## 流程

1. 取得标记原文：复制，不重打。
2. 转成 ASCII 转义，先打印 `ascii(m)` 自检。
3. 运行通道 A 计数，再运行通道 B 取行号。
4. 两者不一致时，先怀疑标记，不要先怀疑文件：用 Read 读出该行逐字比对。
5. 运行负向控制：变异一个字符（多一个重音、少一个字母）的标记必须为 0。
6. 记录 size、mtime、SHA-256，并在报告中写明：方法、标记的 ASCII 形式、行号、计数、用于确认的通道。

## 症状、原因、动作

| 症状 | 原因 | 动作 |
|---|---|---|
| 通道 A 为 0，但 `grep -nF` 命中 | 标记手抄漏字或多字（源案例：`créée` 写成 `crée`） | 用命中的整行重新取标记；改标记，不改文件 |
| 输出显示 `cr` 加 U+FFFD，但计数为 1 | stdout 是 cp1252，被按 UTF-8 捕获 | 保持断言输出 ASCII；文件字节用 `sha256sum` 与 `od -c` 核对；不要报告文件损坏 |
| 两条通道都为 0 | 内容确实不在，或写到了别的路径 | 复查 Edit 结果与实际路径（副本、符号链接、未保存的缓冲区） |
| `SyntaxError: Non-UTF-8 code starting with '\xe9'` | 源码文件或 stdin 是 cp1252 编码 | 源码另存为 UTF-8，或改用纯 ASCII 转义字面量 |
| 所有标记都命中，包括不该存在的 | 断言恒真：空标记、把 `-f` 当固定串、正则元字符 | 加负向控制；确认标记非空且使用 `grep -F` |
| `validate_skill.py` 在副本上 `FAIL name` | 临时目录名与 frontmatter 的 `name` 不一致 | 目录改成与 `name` 同名后重跑 |
| 校验 PASS 但断言没跑过 | 只做了结构校验 | 单独运行通道 A/B，并把输出贴进报告 |

## 已验证案例（2026-10-27 复现）

源会话 `f0fb0e02-dce6-49e7-84a7-dac4eae7e589`（2026-10-26）中，一条 `py -3 - <<'PY'` 命令对文件里的 `Cible créée` 返回 `count 0`，同时输出显示 `cr` 后跟 U+FFFD，看起来像编码损坏。复核原始命令发现，被比较的标记只有 1 个 `\u00e9`（`Cible cr\u00e9e`），而文件是 2 个：**计数 0 是正确的，错的是标记**。

本机复现（Python 3.14.7，`chcp` 为 850，`sys.stdin.encoding` 与 `sys.stdout.encoding` 均为 cp1252）：

- 错标记 → `COUNT 0`；正确标记 → `COUNT 1`；`grep -nF` 命中第 1 行。
- stdin 源码含字面 `créée` 时 `LEN 11`、`ascii='Cible cr\xe9\xe9e'`：源码按 UTF-8 解析，未被 cp1252 破坏。
- cp1252 编码的源码 → `SyntaxError: Non-UTF-8 code starting with '\xe9'`，退出码 1。
- 副本目录名为 `wrong-name` 时 → `FAIL name: 'skill-staged-delivery' does not match directory 'wrong-name'`，`RESULT FAIL`，退出码 1。

未验证：其他 Python 版本、其他 ANSI 代码页、PowerShell 调用形态、管道与重定向组合下的 `-c` 参数传递。

## 完成检查

- [ ] 标记来自工具输出或文件，不是凭记忆输入。
- [ ] 命令中打印了 `ascii(marker)`，转义与字符数可见。
- [ ] 至少两条独立通道的结果已记录，且一致。
- [ ] 负向控制标记返回 0。
- [ ] 断言通道输出为纯 ASCII，没有依赖控制台显示重音。
- [ ] 字节级 size、mtime、SHA-256 已记录。
- [ ] 副本上的校验器失败已排除 `FAIL name` 干扰。
- [ ] 报告区分已复现、已否证与未验证。

## Provenance

- 来源会话：`f0fb0e02-dce6-49e7-84a7-dac4eae7e589`，2026-10-26T12:07:10Z 回合，`cold`、`revision 0`、`hasMoreBefore=false`，仅 1 个用户回合，无用户纠正。
- 该会话唯一的工具失败即上文案例；自动建议把 `count 0` 归因于 heredoc 源码按 cp1252 解码，2026-10-27 的复现否证了该归因，真实原因是标记少一个 `\u00e9`。
- 复现命令、原始输出与分类见 `references/cas-faux-negatif-unicode-2026-10-27.md`。
