# 案例：description_guard.py 与 validate_skill.py 的判定一致性（2026-10-27）

## 工具与哈希

| 工具 | 路径 | SHA-256 | 大小 / mtime |
|---|---|---|---|
| 依赖判定工具 | `edit-skill-frontmatter-description/scripts/description_guard.py` | `9d09ed33f0770fe642aef4d674ebaaed83658cf0fd9a50f4da39429ee62be3e9` | 19 714 B / 2026-10-27 12:57:58 +01:00 |
| 验收工具 | `skill-file-qa/scripts/validate_skill.py` | `1932ce4840054675f0608616e05f9f2c55db5eb749255f6a30c4cfd46e6789d8` | 21 896 B / 2026-10-25 19:20:32 +01:00 |

环境：Windows 10，Python 3.14，夹具全部位于 `~/.qoder/tmp/jugement-parity-2026-10-27/fixtures/<case>/`，运行前设 `PYTHONIOENCODING=utf-8`，返回码由 `subprocess.run(...).returncode` 直取；`validate_skill.py` 固定加 `--stable-seconds 0 --stability-timeout 5`。下表 `validate_skill.py` 列引号内是 FAIL 行的 message 部分，不含 `FAIL` 级别前缀。夹具与临时脚本未随包保存。

## 来源会话

`de13148d-0c37-4677-ac6f-574b1cb5a513`，5 个用户回合，读取时 `cold` / `revision=0` / `hasMoreBefore=false`，无历史截断。

| 回合 | 内容 |
|---|---|
| 1 | 覆盖审计后更新 `verify-skill-recommendation-claims`（5 处 Edit），未新建目录 |
| 2 | 14 项断言验证新规则；发现 `inspect` 的 `ok` 只表示可解析 |
| 3 | 补写判定说明，QA `9 pass / 0 fail / 0 warn` |
| 4 | 8 个夹具并排运行两个工具，报告 6 处不一致；自纠「缺文件 rc=0」为管道假象 |
| 5 | 首轮夹具 1 FAIL，经 `od -c` 对账确认是文档措辞错；两次改写后 35 pass / 0 fail |

本案例的 14 行主表与 8 行 `replace` 对照是**本会话独立重跑**的结果，不是来源会话输出的转抄。

## 主表：`inspect` vs `validate_skill.py`

| 用例 | guard `inspect` | `validate_skill.py` | 分类 |
|---|---|---|---|
| empty | rc 0，`ok:true`，`len 0`，`over_limit:false` | rc 1，`description: missing, empty, or not a string` | DIVERGENT_VERDICT |
| bound-1024 | rc 0，`len 1024`，`over_limit:false` | rc 0，`RESULT PASS` | SAME |
| over-1025 | rc 0，`len 1025`，`over_limit:true`，`remaining:-1` | rc 1，`description: 1025 chars exceeds 1024` | DIVERGENT_VERDICT |
| multi | rc 1，`ok:false` | rc 1，`description: spans 3 lines` | SAME |
| missing | rc 2，`ok:false` | rc 2，`SKILL.md not found in <skill-dir>` | SAME |
| bad-utf8 | rc 2，`ok:false` | rc 1，`encoding: SKILL.md is not valid UTF-8 (<解码异常原文>)` | DIVERGENT_RC |
| mixed-eol | rc 2，`ok:false` | rc 0，`RESULT PASS` | DIVERGENT_VERDICT |
| trailing | rc 0，`len 3`，`over_limit:false` | rc 0，`RESULT PASS` | SAME（`replace` 拒绝，见次表） |
| comment | rc 0，`len 3` | rc 0，`RESULT PASS` | SAME（`replace` 拒绝） |
| dup | rc 0，`len 19`，`description_line 3` | rc 0，`RESULT PASS` | DIVERGENT_FIELD |
| bom | rc 0，`len 3` | rc 1，`frontmatter: SKILL.md starts with a UTF-8 BOM; frontmatter detection may fail` | DIVERGENT_VERDICT |
| tab-lit | rc 0，`len 3` | rc 0，`RESULT PASS` | SAME |
| tab-esc | rc 0，`len 3` | rc 0，`RESULT PASS` | SAME（`replace` 拒绝） |
| u-esc | rc 0，`len 4` | rc 0，`RESULT PASS` | SAME（`replace` 拒绝） |

结论：

- `inspect` 是**只测量**：空值、超限、BOM 都返回 `ok:true`、`rc=0`；只有多行与 YAML 解析失败等硬错误才 `ok:false`。
- `validate_skill.py` 是**判定**：空值、超限、BOM 均 FAIL。
- `mixed-eol` 两工具相反：编辑工具拒绝（rc 2），验收工具 PASS。文档若写「混合 EOL 被拒绝」，只对编辑工具成立。
- `bad-utf8` 结论同向、rc 类别不同：guard 2，验收器 1。

## `replace --dry-run` 对照

候选文件内容 `abc`（单行、无 BOM），默认 dry-run：

| 用例 | rc | 结果 |
|---|---|---|
| bound-1024 | 0 | `status=would-apply` |
| comment | 1 | `description line has extra content, comments, or non-canonical quoting; edit it manually once` |
| dup | 1 | 同上 |
| trailing | 1 | 同上 |
| tab-lit | 0 | `status=would-apply` |
| tab-esc | 1 | 同上 |
| u-esc | 1 | 同上 |
| bom（候选与现值相同） | 0 | `status=unchanged` |

BOM 的真实写入另行验证：把候选换成 `abcd` 并加 `--apply`，guard 返回 `status=applied`、`invariants.bom_preserved=true`，文件头仍为 `EF BB BF`；随后 `validate_skill.py` 仍 `FAIL frontmatter: … BOM`，`RESULT FAIL`、rc 1。即：编辑工具**保留**验收工具拒绝的属性。

由此得到三条路径级结论：

1. `inspect` 通过 ≠ 可写；`editable` 恒为 `true`，不构成可写证明。
2. `inspect` 通过 ≠ `replace` 接受：尾随空格/注释、重复键、引号内 YAML 转义在 `replace` 处 rc 1。
3. 引号内**真制表符**不被拒（`tab-lit` rc 0），被拒的是**字面反斜杠加 t** 与字面反斜杠加 `uXXXX`（`tab-esc`、`u-esc` rc 1）；引号外裸制表符是 YAML 解析错误，`inspect` 也 rc 1。

## rc 类别（按工具分别记录）

| 工具 | 0 | 1 | 2 |
|---|---|---|---|
| `description_guard.py` | 测量成功 | 不变量/YAML/多行/引号外控制符 | 缺 `SKILL.md`、非 UTF-8、混合 EOL、缺 PyYAML |
| `validate_skill.py` | `RESULT PASS` | `RESULT FAIL` | 缺 `SKILL.md`、校验器异常 |

不要把「rc 2 = 环境错误」从一个工具移植到另一个工具：`bad-utf8` 在 guard 是 2，在验收器是 1。

## 三处构造陷阱（来源会话）

### 1. 管道吞掉返回码

来源会话先报「缺文件时 rc=0」，后更正为 2：`… | head; echo $?` 取到的是 `head` 的状态。同一会话的夹具探针还留下 `RESULT FAIL` 与 `rc=0` 同屏的输出；本会话直取 `validate_skill.py` 的 FAIL 返回码为 1。

### 2. 转义折叠

来源会话想构造引号内**字面反斜杠加 t**，但多层 shell/heredoc 把反斜杠折叠成真制表符，导致「字面制表符被拒」的错误结论写进 SKILL.md。`od -c` 对账：真制表符显示 `a  \t   b`，字面反斜杠加 `t` 显示 `a   \   t   b`；当时文件里是前者。改用字节构造后，结论被改写两次：

- 引号内真制表符：接受（guard `replace` rc 0，验收器 PASS）；
- 字面反斜杠 `t` / `uXXXX`：`replace` rc 1；
- 尾随空格与行尾注释：`replace` rc 1。

原则：先证明夹具字节，再改文档；夹具 FAIL 先怀疑夹具。

### 3. 下划线夹具名

来源会话的夹具目录名含下划线（`tab_esc`、`u_esc`），`validate_skill.py` 先报 `FAIL name: 'tab_esc' is not lowercase hyphen-case`，使「验收器 PASS」断言以无关原因失败。改名为 `tab-esc`、`u-esc` 后归因恢复。本会话的 BOM 写入夹具也曾因目录名 `bom-apply` 与 `name: bom` 不一致而出现第二个无关 FAIL，修正后只剩 BOM 一条。

## 来源会话的最终落盘

- 目标文件 `verify-skill-recommendation-claims/SKILL.md`，写入 2 行判定说明（第 189–190 行）。
- 来源报告：QA `9 pass / 0 fail / 0 warn`、`RESULT PASS`、`Files (7)`、body 326 行、34 249 B、`001e7ba6…`；夹具 `35 pass / 0 fail`。
- 这些是来源会话的报告值，未在本会话重跑该 Skill 的 QA。

## 未验证与边界

- 只审计了上面两个工具的当前哈希；其他校验器未测。
- BOM 之外的 `--apply` 写入路径未验证；`replace` 的不变量输出（仅改描述行、保留 EOL）只在 BOM 案例中观察到。
- 未验证任何 Skill 的运行时注入；`skill-file-qa` 的 PASS 只覆盖静态结构。
