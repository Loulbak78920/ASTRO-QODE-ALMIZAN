---
name: auditer-runbook-production-skill
description: "Auditer avant exécution ou réutilisation un Skill ou runbook qui écrit en production : inventorier chaque écriture avec sa cible et son état préalable, détecter l'écrasement d'un secret ou d'une ressource existante, refuser les chown/chmod récursifs non prouvés, exiger une preuve négative falsifiable pour chaque affirmation « vérifié », imposer l'ACL juste après l'écriture du secret, puis réviser au minimum et rejouer skill-file-qa avec empreintes. Utiliser pour relire un runbook de production, vérifier la sûreté d'un Skill d'administration, auditer un chown -R, un écrasement de secret ou une révocation de session non prouvée. 用于执行前审计会写入生产的 runbook、检查写操作影响范围、秘密覆盖与权限范围。不用于执行生产操作、结构验收或单条断言分级。"
---

# 生产 Runbook 执行前安全审计

## 目标与边界

审计对象是**会写入生产**的 Skill 或 runbook：SSH 命令、数据库写入、账号创建、权限变更、秘密文件、服务重启。在采纳、复用或执行前，逐条定位写操作及其目标，判断是否覆盖现有资源、是否可逆、权限范围是否超出证据，以及每个「已验证」结论是否有可证伪的负向检查。

本 Skill 只做只读审计与最小修订。它**不执行**被审计 runbook 的生产步骤，不替代 `skill-file-qa` 的结构验收，也不替代 `verify-skill-doc-claims-before-edit` 的单条断言分级。

## 何时使用

- 采纳或复用另一会话生成的 runbook，尤其是账号、秘密、权限、数据库类操作。
- `skill-file-qa` 已 PASS，但仍需判断「照做会不会破坏生产」。
- 报告出现「已验证」「已吊销」「根因是…」「已生效」等强措辞。
- 准备把 runbook 交给他人或另一会话执行。

## 何时不用

- 只查结构、frontmatter、引用、语法、指纹：用 `skill-file-qa`。
- 只校准单条断言的证据级别与措辞：用 `verify-skill-doc-claims-before-edit`。
- 新建前判断能力是否已被现有 Skill 覆盖：用 `auditer-couverture-skill-avant-creation`。
- 同名 Skill 被并发创建、需要决定接管或缩窄：用 `adopt-concurrent-duplicate-skill`。
- 执行部署本身：用 `deployer-site-sans-dol-vps`。
- 编写或验收 Python 脚本的 UTF-8 与退出码：用 `windows-python-utf8-skill-scripts`。

## 不可协商规则

1. **只读审计。** 除目标 Skill 的最小 Edit 外，不执行任何 SSH、部署、登录、账号创建或权限变更。需要生产核验时另行取得授权，并把结果标为「本会话实测」。
2. **每个写操作必须绑定位置、命令、目标与执行前状态。** 目标状态未知时，结论只能是「未验证」，不能是「安全」。
3. **静态 QA PASS 不是安全证明。** 2026-10-27 的案例中，10 项 PASS 的包仍含 5 个生产风险。
4. **不读取、不打印、不复制秘密值。** 只读存在性、大小、所有者与 ACL；报告中不出现口令，泄漏扫描只报计数。
5. **「已验证」必须配一个可证伪的负向检查。** 没有负向检查的结论降级为「未验证」或「按顺序推断」。
6. **默认最小修订。** 保留现有有效规则；不为未经测试的生产写操作新增自动化脚本。
7. **区分观测与推断。** 只写看到了什么；因果解释单独标注为推断。
8. **并发即停。** 审计期间目标文件出现 size、mtime、SHA-256 变化或新写入者时，停止编辑并重新取基线；并发处理交给 `adopt-concurrent-duplicate-skill`。

## 第 0 步 — 预检与基线

```bash
SKILL_DIR="C:/Users/Administrateur/.qoder/skills/<nom>"
sha256sum "$SKILL_DIR/SKILL.md" "$SKILL_DIR"/references/*.md
wc -l "$SKILL_DIR/SKILL.md"
py -3 -B "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$SKILL_DIR" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" --stable-seconds 2 --stability-timeout 30
```

记录文件清单、字节数、行数、SHA-256、QA 结果与观察时点（UTC 和本地偏移）。若目标可能被并发修改，间隔至少 2 秒采样三次；有变化则重取基线。明确本轮允许修改的文件，不顺手改相邻 Skill。

## 第 1 步 — 写操作清单

逐段读正文与 references，把所有会产生副作用的动作列成表。扫描器只做第一遍提示：

```bash
PYTHONIOENCODING=utf-8 py -3 -B "<ce-skill>/scripts/scan_production_writes.py" "<runbook-dir>"
```

| ID | 位置 | 命令或动作 | 目标 | 执行前状态 | 可逆性 |
|---|---|---|---|---|---|
| W1 | SKILL.md:行号 | `chown …` | 路径 | 需先观测 | 是/否 |

必须覆盖五类：

- **远程写入**：SSH 命令、CLI 创建账号、`systemctl restart`。
- **文件写入**：secret JSON、配置、备份、临时文件。
- **权限与所有权**：`chown`、`chmod`、`icacls`、`install -d`。
- **数据库与状态**：INSERT、DELETE、事务、缓存。
- **网络副作用**：登录、登出、邮件、外部 API。

不要把读取写成写入；也不要漏掉写在散文里的动作，例如「把 JSON 写到 secrets 目录」。

## 第 2 步 — 覆盖与爆炸半径

对每条写操作回答：

1. 目标已存在吗？存在时是否被覆盖？重点检查 secret、配置、备份、账号。
2. 覆盖失败会留下什么？例如 secret 与数据库不一致、半写文件。
3. 范围是否超出证据？只为修一个目录却使用递归权限命令。
4. 顺序是否安全？权限收紧是否发生在写入之后。
5. 失败路径是否回滚或可重试？重试会不会重复创建。

判定三级：

- **BLOCKED**：会覆盖现有秘密或凭据、递归改权限、不可逆删除、无授权生产写。
- **REQUIRES-GUARD**：有覆盖可能但可用「先判定存在性」消除，或失败后需人工处置。
- **BOUNDED**：目标明确、前置状态可观测、失败可回滚。

## 第 3 步 — 秘密与权限

- 秘密只走 stdin：`--mot-de-passe-stdin`。here-string 可以接受，因为 CLI 会 `rstrip`，但秘密本身不得含换行。
- 禁止把秘密放进命令行参数、export 后再 `set -x`、`ssh -v`、日志或错误输出。
- 禁止盲目 `echo "$MDP" | sudo -S`：案例中它曾把口令带进错误输出。先跑 `sudo -n true`；不通过则 `ssh -t` 交互输入。
- 写入前先判断目标是否存在；已存在时**只验证、不重写**。每个账号一个 secret 文件；秘密丢失时不得创建重复账号。
- 写完立即收紧 ACL，例如 `icacls … /inheritance:r /grant:r`；不要留到最后一节，最后一节只复核。
- 权限变更按最小范围：非递归 `chown` 加 `install -d`；先用 `find … ! -user <service-user>` 列出偏差。

## 第 4 步 — 让「已验证」可证伪

为每个成功声明配一个负向检查：

| 声明 | 需要的观测 | 负向检查 |
|---|---|---|
| 账号已创建 | 创建 rc=0，计数增加 | 重试应返回 `COMPTE_EXISTANT` 且不新增 |
| 管理员路由可用 | 带会话 200 | 匿名或无会话 401 |
| 会话已吊销 | 登出 200 | 旧 cookie 再请求受保护路由应 401 |
| 秘密已收紧 | ACL 单主体、无继承 | 从 `ls` 看不出来，必须用 `icacls` |
| 权限修复已生效 | 新属主与模式 | 服务成功写入一次，或列出剩余 `! -user` |

没有执行负向检查时，写「未验证」，不写「已吊销」「已生效」。

## 第 5 步 — 最小修订

- 先记录基线；只改风险所在行，不重排、不整文件重写。
- 把存在性判定放到写操作之前：账号是否存在、secret 是否存在。
- 把 ACL 移到 secret 写入之后立即执行。
- 删除无证据的递归权限命令，改成可列举的最小命令。
- 把「已吊销」「根因是」改为观测事实，并补「未验证」标注。
- 同步更新 pitfalls 表、最终 checklist 与 references 中的同一断言。
- 不新增未测试的生产自动化；若新增只读扫描器，必须给出正例、反例与退出码证据。

## 第 6 步 — 复验与报告

```bash
py -3 -B "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<runbook-dir>" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" --stable-seconds 2 --stability-timeout 30
sha256sum "<runbook-dir>/SKILL.md" "<runbook-dir>"/references/*.md
```

- 记录 QA 的 PASS/FAIL/WARN、Files (N)、body 行数、起止指纹。
- references 不计入校验器指纹，必须单独记录。
- 对修订后的文本重跑扫描器；对 secret 值做泄漏扫描，只报命中计数。
- 报告分四块：已核实、最小修订、未验证（尤其未执行的生产步骤）、观察时点与哈希。

## 报告模板

| Sévérité | 条件 | 处置 |
|---|---|---|
| BLOQUANT | 覆盖现有 secret、递归 chown/chmod、不可逆删除、未授权写 | 停止，先改 runbook |
| À CORRIGER | ACL 滞后、缺负向检查、因果越界 | 最小修订后复验 |
| ACCEPTABLE AVEC LIMITES | 只读审计，未执行生产核验 | 列明未验证项 |
| PROPRE | 每条写有目标、前置状态与负向检查 | 可交付执行 |

报告中的风险表至少包含：ID、位置、写操作、目标与前置状态、风险、判定、最小修订。

## 已验证案例（2026-10-27，会话 421c7f08）

- 目标 `administrer-comptes-production-mizan` 在审计开始时被并发会话写入；本会话没有 create，改为只读审计并做最小修订。
- 发现并修订 5 点：secret 覆盖、`chown -R`、无 401 的吊销声明、ACL 滞后、笔误与因果推断。
- 修订后 QA 10 PASS；随后另一会话并发合入 CLI 预检，最终 `SKILL.md` 17,287 B `d021b593…f0d01`，references 10,294 B `6b1366ea…3daf`，2026-10-27T09:41:38Z 复测一致。
- 未验证：该会话未执行 SSH、创建、登录或 401 复验；401 是写入 runbook 的规定，不是当时的实测。

详见 `references/cas-2026-10-27-audit-admin.md`。

## 错误与陷阱

| 陷阱 | 后果 | 对策 |
|---|---|---|
| 把 10 项 PASS 当安全 | 5 个生产风险漏过 | 先跑第 1–4 步，再看 QA |
| 只读代码，不读散文中的写操作 | 漏掉「把 JSON 写到 secrets」 | 扫描器加人工逐段 |
| 先写 secret 再判断账号是否存在 | 覆盖现有凭据 | 判定前置，已存在只验证 |
| 用 `chown -R` 图省事 | 改掉 600 备份的属主 | 非递归加 `find ! -user` |
| ACL 留到最后一节 | 继承 ACL 窗口 | 写完立即 `icacls` |
| 登出 200 当吊销 | 旧会话仍可用 | 旧 cookie 必须 401 |
| 相对路径引用 secret 文件 | QA 把 `secrets/…` 当 Skill 内文件而 FAIL | 用绝对路径或路径变量 |
| 并发会话中途改包 | 报告哈希失效 | 记录时点，三次采样 |

## 完成检查

- [ ] 写操作清单覆盖远程、文件、权限、数据库、网络。
- [ ] 每条写有目标与执行前状态；未知项标「未验证」。
- [ ] 无覆盖现有 secret；每个账号独立 secret；丢失时不建重复。
- [ ] 无递归权限命令；ACL 紧跟写入。
- [ ] 每个「已验证」有负向检查；未执行的不写「已…」。
- [ ] 最小修订，pitfalls、checklist、references 同步。
- [ ] QA 与指纹已记录；references 单独哈希；观察时点明确。
- [ ] 报告写明未执行的生产步骤与限制。

## 资源

- `scripts/scan_production_writes.py` — 只读第一遍扫描，检查高风险写模式；不是安全证明。
- `references/cas-2026-10-27-audit-admin.md` — 来源会话、5 个风险、哈希、未验证项。
