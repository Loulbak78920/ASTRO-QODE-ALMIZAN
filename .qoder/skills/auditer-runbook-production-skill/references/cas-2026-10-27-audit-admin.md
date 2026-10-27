# 案例：2026-10-27 生产管理员 runbook 审计

## 来源与观察时点

- 来源会话：`421c7f08-da31-4ddb-a2e0-1dc29e264103`，标题「创建 Mizan 管理员账户 Skill」。
- 读取参数：`turnLimit=20`、`includeToolOutputs=true`、`maxOutputCharsPerItem=8000`；`hasMoreBefore=false`。
- 读取时状态：`runtimeState=waiting-user`，`revision=68`，`activeTurnId=af954e84-9ef8-457a-89ec-bcaed2bf1310`，8 条消息。
- 复测文件时点：2026-10-27T09:41:38Z（本地 2026-10-27 10:41，UTC+1）。
- 审计对象：`C:\Users\Administrateur\.qoder\skills\administrer-comptes-production-mizan\`。

会话在读取时仍处于 `waiting-user`，挂起的用户任务是「提交并推送这些更改」。因此上述状态只代表读取时点；目标包之后可能继续变化。

## 过程事实

1. 会话开始时目标目录不存在，随后同名 Skill 被并发会话 `e4b7c222` 写入（`Write` 记录 05:24:36Z 与 05:24:53Z，按会话报告）。
2. `421c7f08` 没有执行 `create`，而是只读审计现有包，并向用户提出 P1–P5。
3. 用户确认 P1–P5 后，该会话做最小 Edit；随后 `c15b9ebe` 在 05:31:40–49Z 并发加入 CLI 契约预检与 §9，P1–P5 未被回退。
4. 用户要求 `reload skills`：代理无法执行 `/skills reload`，改用一次只读 Skill 调用并核对会话 JSONL 的注入记录（`2026-10-27T05:33:44.252Z`，首行 `Base directory for this skill: C:\Users\Administrateur\.qoder\skills\administrer-comptes-production-mizan`）。
5. 用户要求复跑 QA：合并版 `RESULT PASS`，10 pass / 0 fail / 0 warn，body 229 行，description 529 字符，Files (2)。

## 五个风险（审计时记录的行号属于修订前版本）

| ID | 修订前位置 | 问题 | 修订 |
|---|---|---|---|
| P1 | `SKILL.md:66-88` | 4.2 会覆盖现有 `administrateur_production_al_mizan.json`；4.3 按唯一性规则会对已存在的 `archonte` 返回 `COMPTE_EXISTANT`（推断，本次未执行），秘密文件与生产库不再匹配，等于丢失现有管理员凭据 | 4.1 先判定账号是否存在；已存在只做 4.5 验证，绝不重写 secret；新账号用独立 secret 文件；秘密丢失时不建重复账号 |
| P2 | `SKILL.md:109` | 建议 `chown -R`，但证据只支持改根目录属主并新建 `secrets/`；`-R` 会连带改掉 `root:root 600` 的备份 | 非递归 `chown` + `install -d`；`sudo -n true` 预检；`find … ! -user ubuntu` 列举；禁止盲发 sudo 密码 |
| P3 | `SKILL.md:128` | 「登出后会话已吊销」没有直接观测；只观测到登出 200 与登出前 1 个会话 | 增加负向复验：旧 cookie 再请求 `/comptes/moi` 应 401；未观测不得声称吊销 |
| P4 | `SKILL.md:132-142` | ACL 在 4.6 才收紧，4.2 写文件到 4.6 之间存在继承 ACL 窗口 | `icacls` 移到 secret 写完立即执行；4.6 只复核 |
| P5 | `references:97` 等 | `Petit-fils de vérification` 笔误；「chown 没以正确用户应用」是推断而非观测 | 改为 `Sortie de vérification`；改为可观测事实「extraction 后根目录为 root:root」 |

## 验收输出（会话原文摘要）

```
RESULT PASS   Summary: 10 pass, 0 fail, 0 warn   VALIDATOR_RC=0
Fingerprint (start) = (final): 17287 bytes | 2026-10-27T06:31:43+01:00
sha256=d021b593cf082ce52983b237408d86e8edcc01822e3f063bf5a0670d4baf0d01
Files (2): SKILL.md, references/preuves-session-2026-10-27.md
PASS body: 229 lines (< 500)
PASS description: single line, 529 chars
```

## 文件指纹

| 时点 | 文件 | 字节 | SHA-256 |
|---|---|---|---|
| P1–P5 修订后（已被并发更新取代） | `SKILL.md` | 16,218 | `8d90795257dfd12464f96b7afb96c807bd432dd839b9393a839286382f41425e` |
| 同上 | `references/preuves-session-2026-10-27.md` | 9,056 | `361d79ea9b79076d8b8fdab5a38c2f2ddf4f5f201d8f49f3929eee624d74e6be` |
| 合并后终态，2026-10-27T09:41:38Z 复测一致 | `SKILL.md` | 17,287 | `d021b593cf082ce52983b237408d86e8edcc01822e3f063bf5a0670d4baf0d01` |
| 同上 | `references/preuves-session-2026-10-27.md` | 10,294 | `6b1366eaef9e18776af8d524dc3f86e8415398e62c0a342b72344d2662a63daf` |

并发更新说明：同一路径在 05:28Z 与 05:31Z 之间被两个会话先后写入，旧哈希不能跨时点引用。审计报告必须把哈希绑定到观察时间。

## 未验证项

- 本会话未执行任何 SSH、生产账号创建、HTTPS 登录、登出或 401 复验；这些实测记录来自 runbook 证据档案所记载的更早创建会话，不是本会话复现。
- 401 负向检查是审计后写入 runbook 的规定，来源会话未执行它；因此「吊销已证明」在来源时点仍不成立。
- 未新增 `scripts/`，未 commit/push。
- 目标包在读取时仍可能被来源会话继续修改；上表哈希只在 09:41:38Z 窗口内有效。

## 可复用结论

1. `skill-file-qa` 的 10 项 PASS 只覆盖布局、frontmatter、引用、语法与指纹，不覆盖写操作的影响范围。
2. 覆盖秘密的写操作是最高风险，必须在写入前判定资源是否存在。
3. `chown -R` 是证据越界的典型：修一个目录不需要递归改整棵树。
4. 「已吊销」「已生效」只有在负向检查失败（或按预期返回 401）后才可写。
5. ACL 与写入的先后顺序是安全属性，不是风格问题。
6. 因果措辞（「因为 X 未应用」）若未仪器化，只能写成观测事实。
