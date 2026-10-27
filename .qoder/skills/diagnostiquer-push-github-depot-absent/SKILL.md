---
name: diagnostiquer-push-github-depot-absent
description: "当 git push 或 git ls-remote 返回 Repository not found（通常 exit 128）时，先用 Git Credential Manager 的已存凭据经 GitHub REST 只读归因，区分仓库确实不存在、私有仓库无权、所有者或 URL 写错、令牌 scope 不足、组织限制与限流；所有者是占位符或不可访问（NO_VISIBILITY）时，只读枚举 /user/orgs、/user/memberships/orgs/{owner}、/orgs/{owner} 找出可建私有库的所有者，用“所有者+可见性”两问确认后探测新 URL、创建、git remote set-url 并推送专用分支；归因完成并经用户确认后才建库：读取 git credential fill 的 username 与 scopes、/user、/users/{owner}、/orgs/{owner}/repos、/user/repos，随后 POST /orgs/{owner}/repos 或 /user/repos，先改名本地分支再 push -u，核对完整 OID，并复查并发写入。禁止打印或落盘 token、静默替换 URL、回退 SSH、向 main 强推；404 不等于不存在。用于 GitHub Repository not found、gh 不存在、已存凭据仍 404、owner 是 user/my-org 占位、组织非成员、组织零仓库、创建私有仓库、推送专用分支、curl -o /tmp 后 py -3 读不到、push -u 后 master 跟踪异名分支、匿名 HTTPS 404、SSH 主机密钥或公钥失败。English triggers: Repository not found, repo missing vs no permission, placeholder owner, discover owner via /user/orgs, create private repo via REST without gh, set-url origin, push dedicated branch, cross-name upstream tracking, anonymous HTTPS 404, read-only GitHub repo probe."
---

# 诊断 GitHub 推送目标仓库缺失并创建私有仓库

## 目标与边界

当 `git push` 或 `git ls-remote` 以 `Repository not found` / `fatal: repository ... not found`（通常 exit 128）失败时，用已存凭据经 GitHub REST **只读**归因：目标仓库确实不存在、私有仓库无权、所有者或 URL 写错、令牌 scope 不足、组织限制或限流。只有归因达到 `ABSENT_CONFIRMED` 且用户明确确认后，才创建私有仓库，把既有提交推到**专用分支**，核对远端完整 OID，并检查推送后是否出现并发写入。

不替代：

- `github-pr-create-merge-sans-gh`：PR 创建与合并；本 Skill 不创建 PR。
- `publier-skill-qoder-vers-depot-git`：已有 `origin/main` 的发布或归档；本 Skill 处理 remote 尚不存在。
- `commit-skill-work`：本地提交与索引校验；本 Skill 从已有提交开始。
- `nettoyer-branches-refs-git`：分支与 ref 清理；本 Skill 不删除任何 ref。

## 何时使用

- `git push` / `git ls-remote` 返回 `remote: Repository not found.`，远程 URL 看起来正确。
- 机器上没有 `gh`，只能用 credential helper 与 REST。
- 已存凭据可用，但 HTTPS 仍然 404，无法判断是仓库缺失还是无权限。
- 匿名 `curl` / `ls-remote` 返回 404，但没有带凭据，无法区分缺失与私有仓库。
- 需要确认组织是否存在目标仓库、当前账号能否在该组织建私有库。
- 用户给出的 owner 是 `user`、`my-org`、`owner`、`org` 等占位符，或说“所有者用 X 试试”。
- 归因结果为 `NO_VISIBILITY`：组织存在但当前账号不是成员，或他人个人账号的 404。
- 需要在不猜 URL 的前提下，发现当前账号可建私有库的组织或本人账号。
- 用户要求“创建仓库后推送”“推送到一个新分支”。
- 已遇到 `curl -o /tmp/...` 后 `py -3` 报 `FileNotFoundError`。
- 推送后本地 `master` 跟踪了异名远端分支（`origin/skill/...`）。

## 404 的归因表

GitHub 对“不存在”和“无权访问私有仓库”都返回 404，因此 404 只是起点，不是结论。

| 分类 | 判定条件 | 动作 |
|---|---|---|
| `REPO_EXISTS` | `GET /repos/{owner}/{repo}` 返回 200 | 不建库；把 origin 指向该 URL 并推专用分支 |
| `ABSENT_CONFIRMED` | 404，且所有者是组织、成员 `role=admin`、`/orgs/{owner}/repos?type=all` 完整分页无同名；或所有者是本人且 `/user/repos?affiliation=owner` 完整分页无同名 | 请求用户确认后可建库 |
| `ABSENT_LIKELY` | 404，组织成员但非 admin，列表完整且无同名 | 请用户确认缺失或提供 admin 令牌；不自动建库 |
| `NO_VISIBILITY` | 404，所有者是他人个人账号、非组织成员、列表截断或类型未知 | 无法证明缺失；先运行 `--list-owners` 发现候选，再由用户确认 |
| `WRONG_OWNER` | 可见仓库中存在同名但 `owner` 不同 | 报告该 `full_name`，询问目标，不建同名库 |
| `NO_REPO_SCOPE` | 404，且经典令牌的 `X-OAuth-Scopes` 不含 `repo` | 停止；请用户更新令牌 |
| `AUTH_INVALID` | `GET /user` 非 200 | 停止；先修凭据 |
| `FORBIDDEN` | `GET /repos/...` 返回 403 且非限流 | 停止；申请权限，不建库 |
| `OWNER_NOT_FOUND` | `GET /users/{owner}` 返回 404 | 检查拼写；疑似占位符时运行 `--list-owners`，不猜账号 |
| `RATE_LIMITED` | 403 且 `X-RateLimit-Remaining: 0` | 等待配额重置，不作结论 |
| `INCONSISTENT` | 仓库出现在 `/user/repos`，但直接 GET 失败 | 检查令牌与仓库状态 |
| `NO_CREDENTIAL` | `git credential fill` 无 password | 停止；不要索取粘贴的 token |

`ABSENT_CONFIRMED` 仍需要用户确认；归因只回答“是否缺失”，不授权写入。

## 不可协商约束

1. **404 不等于不存在。** 未完成归因表之前，不得创建仓库，也不得宣称“仓库不存在”。
2. **建库必须用户确认。** 需要换所有者时，同一轮先用 AskUserQuestion 问所有者，再问可见性（私有、公开、用户自建、暂不推送）；发现结果不能代替确认；未收到选择就停止。
3. **不打印、不落盘 token。** 只输出 `TOKEN_PRESENT=yes` 与用户名；不写 `.git-credentials`、不写日志、不写报告、不放进提交。
4. **URL 只来自用户或用户确认后的发现结果。** 不猜测 `.git` 后缀、不拼接其他 Skill 的 origin、不把 HTTPS 换成 SSH 地址；不得静默把占位所有者替换成发现的账号或组织。
5. **不用 SSH 回退。** 如需诊断可做一次 `ssh -T git@github.com`；`Host key verification failed` 或 `Permission denied (publickey)` 后回到 HTTPS，不改 remote 为 SSH。临时 `known_hosts` 探测文件要删除。
6. **只推专用分支。** 不使用 `--force`，不推 `main`，不使用 `+refs/heads/main`；除非用户明确要求且是一次 fast-forward。
7. **分支同名先于 push。** 先 `git branch -m <branch>`，再 `push -u origin <branch>`；否则本地 `master` 会跟踪 `origin/<branch>` 这类异名上游。
8. **完整 OID 才算证据。** 比较本地 `HEAD` 与 `ls-remote` 的 40 位哈希；短哈希、推送成功提示、分支列表都不算。
9. **不静默提交并发写入。** 推送后出现的未跟踪文件或被改文件只报告，不加入提交，除非用户明确要求。
10. **确认前只读。** 建库前只做 `GET`；确认后的写入限于 `POST` 建库、`remote add`/`set-url`、`branch -m` 与 `git push`。

## 步骤

### 0. 固定输入与本地状态

记录：用户给出的 URL 原文、目标分支名、本地仓库路径、是否要求私有。推送前只读检查：

```bash
git -C "<depot>" rev-parse --show-toplevel
git -C "<depot>" rev-parse HEAD
git -C "<depot>" status --porcelain=v1
git -C "<depot>" ls-tree -r --name-only HEAD
git -C "<depot>" remote -v
```

- `origin` 已存在且指向别的 URL：停止并询问；只有第 5 步确认新所有者后才 `set-url`。
- 工作区有未提交改动：先说明哪些文件不会进入本次推送；不要替用户提交。
- 记录 `HEAD` 的完整 40 位 OID，后续远端核对以它为准。

### 1. 只读探测远端

```bash
GIT_TERMINAL_PROMPT=0 git -c credential.interactive=never ls-remote --heads "<URL>" 2>&1
printf 'LSREMOTE_EXIT=%s\n' "$?"
```

先运行、后取退出码，不要经过管道。`Repository not found` + exit 128 同时覆盖“缺失”和“私有仓库无权”，因此下一步必须查 API。

### 2. 读取已存凭据

```bash
cred=$(printf 'protocol=https\nhost=github.com\n\n' | GIT_TERMINAL_PROMPT=0 git -c credential.interactive=never credential fill 2>/dev/null)
user=$(printf '%s\n' "$cred" | sed -n 's/^username=//p')
pass=$(printf '%s\n' "$cred" | sed -n 's/^password=//p')
printf 'CREDENTIAL_USER=%s\nTOKEN_PRESENT=%s\n' "$user" "$([ -n "$pass" ] && echo yes || echo no)"
unset cred
```

- 只打印存在性，永不 `echo "$pass"`。
- password 为空即停止，不要请用户把令牌粘贴到对话里。
- `git credential-manager github list` 只能列账号名，不能代替 `fill` 取令牌。

### 3. 只读 REST 归因

优先运行随附脚本，它只用 `GET`，且不会输出 token：

```bash
py -3 -B "<skill-dir>/scripts/probe_github_repo.py" --url "<URL>"
```

退出码：`0` = `REPO_EXISTS` 或 `ABSENT_CONFIRMED`；`1` = 其余分类；`2` = URL 或环境错误。需要机器可读输出时加 `--json`。

手工探测时按下表取证据：

| 端点 | 用途 | 关键字段 |
|---|---|---|
| `GET /repos/{owner}/{repo}` | 存在性 | 200 / 404 / 403 |
| `GET /user` | 令牌身份 | `login` |
| 响应头 `X-OAuth-Scopes` | 经典令牌范围 | 是否含 `repo` |
| `GET /users/{owner}` | 所有者类型 | `type` = `Organization` / `User` |
| `GET /user/memberships/orgs/{owner}` | 组织成员身份 | `state`、`role` |
| `GET /orgs/{owner}` | 建库权限 | `members_can_create_private_repositories`、`plan.private_repos` |
| `GET /orgs/{owner}/repos?per_page=100&type=all` | 组织仓库全集 | `full_name`、`private` |
| `GET /user/repos?per_page=100&affiliation=owner,collaborator,organization_member` | 可见仓库 | `full_name`、`owner.login`、`private` |

手工 curl 时把响应体经 stdin 交给解析器，避免 `/tmp` 路径问题：

```bash
curl -s -w '\nHTTP=%{http_code}\n' \
  -H "Authorization: Bearer $pass" \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/{owner}/{repo}" \
| py -3 -c "import sys,json; raw=sys.stdin.read(); body,_,tail=raw.rpartition('HTTP='); print('HTTP=',tail.strip()); d=json.loads(body); print('MESSAGE=',d.get('message'))"
```

注意：

- `curl -o /tmp/x.json` 后由 `py -3`（原生 Windows Python）读取会 `FileNotFoundError`，因为 `/tmp` 是 MSYS 路径。改用 stdin，或先 `cygpath -w`。
- `X-OAuth-Scopes` 缺失不证明没有 scope；细粒度令牌通常不返回该头，此时靠 404/403 与仓库列表判断。
- 列表必须完整分页；脚本最多跟随 10 页，截断时 `LISTS_COMPLETE` 为 `false`，不得据此判 `ABSENT_CONFIRMED`。

### 4. 判定并停止

按“404 的归因表”给出唯一分类。以下情况停止，不建库：

- `AUTH_INVALID`、`NO_CREDENTIAL`、`NO_REPO_SCOPE`、`RATE_LIMITED`。
- `WRONG_OWNER`：先确认目标到底是哪一个仓库。
- `NO_VISIBILITY`：先进入 4b 发现候选所有者，再由用户确认；`ABSENT_LIKELY`：请用户确认缺失，或提供有权限的凭据。
- 列表截断、网络错误、响应无法解析。

建库前还要检查创建能力：组织要求 `state=active`，且 `role=admin` 或 `members_can_create_private_repositories=true`；同时 `total_private_repos` 未达到 `plan.private_repos`。个人所有者只允许在 `authed_login == owner` 时创建。

### 4b. 所有者不可用时只读发现

只在 `NO_VISIBILITY` 或所有者为已知占位符（`user`、`my-org`、`owner`、`org` 等）时进入；仍然是只读阶段。

```bash
py -3 -B "<skill-dir>/scripts/probe_github_repo.py" --list-owners
```

脚本只用 `GET`，输出当前账号、所属组织、membership 与建库权限；`--json` 输出同一结果。退出码：`0` = 至少一个候选所有者；`1` = 无候选或凭据无效；`2` = 用法、网络或 API 错误。手工查询的等价端点：

| 端点 | 用途 | 关键字段 |
|---|---|---|
| `GET /user/orgs?per_page=100` | 当前账号所属组织 | `login` |
| `GET /user/memberships/orgs/{org}` | 成员身份 | `state`、`role` |
| `GET /orgs/{org}` | 成员建私有库权限 | `members_can_create_private_repositories`、`plan.private_repos`、`total_private_repos` |
| `GET /user` | 本人个人所有者 | `login` |

规则：

- 候选只包括本人账号和 `/user/orgs` 列出的组织；不要枚举他人个人账号。
- `/user/orgs` 只列当前账号所属组织；某组织未出现不等于它不存在。
- 组织候选要求 `state=active`，且 `role=admin` 或 `members_can_create_private_repositories=true`，且私有库配额未满；不满足的只报告原因。
- 发现候选不等于授权。把候选（含权限与配额）交给用户，进入第 5 步两问确认；未确认前不建库、不改 origin。
- 不把 `/users/{owner}/repos` 当缺失证据；它只列公开仓库。

### 5. 请求用户确认

若第 4b 步发现了候选所有者，先问“仓库创建在哪个所有者下”，列出候选及其权限与配额，再问可见性：

1. 创建**私有**仓库并推送（推荐）。
2. 创建**公开**仓库并推送（内容将公开）。
3. 用户手动创建后再推送。
4. 暂不推送，保留本地提交与已配置的 origin。

问题里写明：旧 origin（若有）、所有者、仓库名、目标分支、将推送的完整 OID、`git ls-tree` 显示的文件数。没有回答就停在这里；发现的所有者必须经此确认，不能直接使用。

### 6. 创建仓库

组织所有者：

```bash
curl -s -w '\nCREATE_HTTP=%{http_code}\n' -X POST \
  -H "Authorization: Bearer $pass" \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/orgs/{owner}/repos" \
  -d '{"name":"{repo}","private":true,"description":"Qoder Skills"}'
```

- 个人所有者且 `authed_login == owner`：把 URL 换成 `https://api.github.com/user/repos`。
- 期望 `HTTP 201`，并核对 `full_name` 与 `private`。
- `422` 多为名称冲突或非法名称：重新归因，不要盲目重试；`403` 表示无权建库。
- 不发送 `auto_init`，保持空仓库，便于直接推送既有提交。

### 7. 配置 remote 并对齐分支名

```bash
git -C "<depot>" remote -v
if git -C "<depot>" remote get-url origin >/dev/null 2>&1; then
  GIT_TERMINAL_PROMPT=0 git -C "<depot>" ls-remote origin 2>&1
  printf 'OLD_REMOTE_EXIT=%s\n' "$?"
  # 仅当第 5 步已确认新所有者时，才执行下一行：
  # git -C "<depot>" remote set-url origin "<URL>"
else
  git -C "<depot>" remote add origin "<URL>"
fi
git -C "<depot>" rev-parse --abbrev-ref HEAD
git -C "<depot>" branch -m "<branch>"
GIT_TERMINAL_PROMPT=0 git -C "<depot>" -c credential.interactive=never push -u origin "<branch>"
printf 'PUSH_EXIT=%s\n' "$?"
```

- 顺序固定：**先改名，后 push**。若本地分支已叫 `<branch>`，跳过 `branch -m`。
- 改 origin 前记录旧 URL 与旧远端 OID；旧地址探测失败时写 `OLD_REMOTE_HEAD=none`。只有第 5 步已确认新所有者，才允许 `remote set-url`；否则停止并询问。
- 若 `origin` 已存在且指向用户确认的同一 URL，跳过 `remote add` 与 `set-url`。
- 若用户坚持保留不同本地名，改用 `HEAD:refs/heads/<branch>`，并在报告中写明本地分支跟踪的是异名远端分支。
- 不使用 `--force`；被拒时先 `ls-remote` 与 `fetch`，不要强推。

### 8. 推送后核对

```bash
git -C "<depot>" rev-parse HEAD
GIT_TERMINAL_PROMPT=0 git -C "<depot>" ls-remote origin "refs/heads/<branch>"
git -C "<depot>" ls-tree -r --name-only HEAD
```

本地 `HEAD` 与 `ls-remote` 第一列必须逐字相等（40 位）。再核对 `ls-tree` 只包含本次应推送的文件；出现意外的 `scripts/` 或缓存目录时先停下说明。

### 9. 推送后并发复查

```bash
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --stat
```

推送与核对之间可能有其他会话改写同一目录。出现新的未跟踪文件或 `SKILL.md` 被改时：

- 报告路径、大小、mtime、SHA-256 的变化。
- 明确“远端仍是旧提交”。
- 不提交、不改写、不强制推送，等用户指令。

## 陷阱与诊断

| 现象 | 原因 | 处置 |
|---|---|---|
| `Repository not found`，凭据有效 | 缺失或私有仓库无权，二者返回相同文案 | 走 REST 归因表，不猜 |
| 匿名 HTTPS（不带凭据）返回 404 | 未认证请求看不到私有仓库，404 只说明匿名不可见 | 不作缺失证据；改用 `git credential fill` 的凭据或走 REST 归因 |
| owner 是 `user`、`my-org` 等占位符 | URL 从未指向真实账号，`ls-remote` 仍 exit 128 | 判 `NO_VISIBILITY`；运行 `--list-owners` 发现候选，再由用户确认 |
| `my-org` 组织存在但 `MEMBERSHIP_STATE=N/A` | 当前账号不是该组织成员，不能建库 | 不判缺失；发现并确认可用所有者 |
| `/user/orgs` 未列出某组织 | 该端点只列当前账号所属组织 | 不据此断言组织不存在；只把列表当候选来源 |
| 发现候选后直接 `set-url` | 发现不等于授权；旧远端可能仍有提交 | 先两问确认，再记录旧 URL/OID 并 `set-url` |
| `git credential fill` 无 password | helper 未登录或禁用了交互 | 停止；请用户在本机完成登录 |
| `curl -o /tmp/x` 后 `py -3` 报 `FileNotFoundError` | MSYS `/tmp` 与原生 Windows Python 不互通 | 响应体走 stdin，或 `cygpath -w` |
| `branch 'master' set up to track 'origin/skill/...'` | 用 `HEAD:refs/heads/<branch>` 推送，本地名与远端名不同 | 推送前 `git branch -m <branch>` |
| SSH 报 `Host key verification failed` 或 `Permission denied (publickey)` | 主机密钥缺失或公钥未被接受 | 回到 HTTPS；不把 remote 改成 SSH |
| `POST` 返回 422 | 名称冲突、非法名称或组织策略 | 重新归因；不重试同一请求 |
| `POST` 返回 403 | 非 admin 且组织禁止成员建库，或配额已满 | 请管理员创建，或用已确认的个人账号 |
| `403` 且 `X-RateLimit-Remaining: 0` | 限流 | 等待重置，不作存在性结论 |
| `X-OAuth-Scopes` 缺失 | 细粒度令牌通常不返回该头 | 不据此判无权限 |
| 个人所有者的私有仓库看不到 | `/users/{owner}/repos` 只列公开仓库 | 判 `NO_VISIBILITY`；运行 `--list-owners` 后由用户确认 |
| 推送成功但远端哈希不同 | 推了别的分支或别的提交 | 用完整 OID 与 `refs/heads/<branch>` 重新核对 |

## 已验证案例（2026-10-26）

来源会话 `85b68db0-52a0-4a36-b46e-f34c4ef1a798`：JSONL 582 行，证据截至 15:07:20Z，`hasMoreBefore: false`。时间戳为工具调用记录中的 UTC。

| 时间 | 观察 |
|---|---|
| 14:56:22Z | `GIT_TERMINAL_PROMPT=0 git ls-remote --heads` → `remote: Repository not found.`、exit 128 |
| 14:57:09Z | `which gh` → 不在 PATH |
| 14:57:15Z | `git remote add origin` + `push -u origin HEAD:refs/heads/skill/verify-skill-runtime-binding` → `PUSH_EXIT=128` |
| 14:57:29Z | `git credential fill` → `CRED_USER=Loulbak78920`、`TOKEN_PRESENT=yes` |
| 14:57:44Z | `curl -o /tmp/qoder_repo_probe.json` 后 `py -3` 读取 → `FileNotFoundError`；改用 stdin 后成功 |
| 14:57:56Z | `GET /repos/IMAM8MAHDI/qoder-skills` → `HTTP=404`；`GET /user` → `LOGIN=Loulbak78920` |
| 14:58:11Z–14:58:50Z | SSH 直连 `git@github.com` → `Host key verification failed`、exit 255；`accept-new`、`StrictHostKeyChecking=no`、`UserKnownHostsFile=/dev/null` 均未绕过 |
| 14:58:57Z | 用 `ssh-keyscan` 的临时 known_hosts 重试 → `git@github.com: Permission denied (publickey)`、exit 255；临时文件已清理 |
| 14:59:05Z | `X-OAuth-Scopes: gist, repo, workflow`；`/user/orgs` → `ORG=IMAM8MAHDI` |
| 14:59:16Z | `/orgs/IMAM8MAHDI/repos?type=all` → `HTTP=200`、`ORG_REPO_COUNT=0` |
| 14:59:37Z | `members_can_create_private_repositories=true`；`/user/memberships/orgs/IMAM8MAHDI` → `state=active`、`role=admin` |
| 14:59:58Z | 用户选择“创建私有仓库并推送（推荐）” |
| 15:00:02Z | `POST /orgs/IMAM8MAHDI/repos` → `HTTP=201`、`FULL_NAME=IMAM8MAHDI/qoder-skills`、`PRIVATE=True` |
| 15:00:11Z | push 成功，`PUSH_EXIT=0`；提示 `branch 'master' set up to track 'origin/skill/verify-skill-runtime-binding'` |
| 15:00:20Z | `ls-remote` → `37d1cc7… refs/heads/skill/verify-skill-runtime-binding`，与本地 HEAD 一致；同一状态检查已见 `?? scripts/` |
| 15:00:42Z | `git branch -m master skill/verify-skill-runtime-binding` 后才同名跟踪 |
| 15:00:47Z | 并发写入确认：`SKILL.md` 21,905 B、`2f16adec…`、mtime 16:00:44 +01:00（代理未提交） |
| 15:03:59Z | 用户要求提交并发修改；15:06:17Z 另一轮用 `commit-skill-work` 成功提交 `eeff5e2` |

### 补充观测（2026-10-26，个人所有者分支）

创建本 Skill 后，在会话 `ad5d6df9-0fa2-4717-b34a-76be57e7773e` 中自 2026-10-26T15:11Z 起，用同一脚本对另外三个仓库做只读探测（均未创建或修改任何资源）：

| 仓库 | 所有者 | `REPO_HTTP` | 可见列表完整 | 分类 | 退出码 |
|---|---|---|---|---|---|
| `octocat/Hello-World` | 他人 User | 200 | true | `REPO_EXISTS` | 0 |
| `Loulbak78920/qoder-probe-absent-20261026` | 本人 User | 404 | true | `ABSENT_CONFIRMED` | 0 |
| `octocat/qoder-probe-absent-20261026` | 他人 User | 404 | true | `NO_VISIBILITY` | 1 |

这组观测把“个人所有者”分支从推断提升为实测：本人账号下 404 且 `/user/repos?affiliation=owner` 完整分页无同名时判 `ABSENT_CONFIRMED`；他人个人账号的 404 只判 `NO_VISIBILITY`，避免把无权访问误判为缺失。

### 补充观测（2026-10-26，占位所有者 → 发现并确认可用所有者）

来源会话 `cc18d99f-8233-40d3-bd8c-7398d42ea3a3`：快照 revision 12、`hasMoreBefore: false`；读取时 `runtimeState: running`，活跃回合是后续的浏览器查看，不影响本回合。快照包含工具输出但不含 Bash 命令原文，逐工具时间戳未暴露；下表时间取用户回合时间戳（UTC）。

| 时间 | 观察 |
|---|---|
| 15:41:51Z | 用户给出 `https://github.com/user/develop-skill-static-checker.git`；代理提示 `user` 像占位符 |
| 15:42:19Z | 用户要求 push；`ls-remote` → `remote: Repository not found.`、`RC=128`；未推送 |
| 15:43:41Z | 用户改口“所有者用 my-org 试试”；origin 更新为 `my-org` 后 `LS_REMOTE_RC=128` |
| 15:45:29Z | 用户要求“创建远程仓库并推送”；探测 `my-org` → `OWNER_TYPE=Organization`、`MEMBERSHIP_STATE=N/A`、`REPO_HTTP=404`、`CLASSIFICATION=NO_VISIBILITY`、`PROBE_RC=1` |
| 同一回合 | 只读发现 → `USER_ORGS_HTTP=200`、`USER_ORGS=IMAM8MAHDI`、`MEMBERSHIP_HTTP=200 STATE=active ROLE=admin`、`ORG_HTTP=200 PRIVATE_CREATE=True` |
| 同一回合 | AskUserQuestion 回答：“IMAM8MAHDI 组织（推荐）”“私有（推荐）” |
| 同一回合 | 探测 `IMAM8MAHDI/develop-skill-static-checker` → `MEMBERSHIP_STATE=active`、`ORG_REPO_COUNT=1`、`REPO_HTTP=404`、`CLASSIFICATION=ABSENT_CONFIRMED`、`PROBE_RC=0` |
| 同一回合 | `CREATE_HTTP=201`、`FULL_NAME=IMAM8MAHDI/develop-skill-static-checker`、`PRIVATE=True` |
| 同一回合 | origin 改为新 URL；`PUSH_EXIT=0`；`branch 'main' set up to track 'origin/main'` |
| 同一回合 | `LOCAL_HEAD=REMOTE_MAIN=284dc902bf54d89a0388a8ad67e14f346610cead`；远端 3 个文件；`STATUS_LINES=0` |

这段把“发现 → 两问确认 → 新 URL 归因 → 建库 → `set-url` → 推送 → OID/文件树/工作区核对”标为已实测。`my-org` 的 404 只判 `NO_VISIBILITY`，未判缺失。

本次更新后的只读复验（2026-10-26，UTC，独立于来源会话）：

| 命令 | 观察 | 退出码 |
|---|---|---|
| `--list-owners` | `AUTHED_LOGIN=Loulbak78920`、`ORG=IMAM8MAHDI`、`ROLE=admin`、`PRIVATE_CREATE=True`、`CAN_CREATE_PRIVATE=yes`、`OWNER_CANDIDATES` 含本人与组织 | 0 |
| `--list-owners --json` | 单个 JSON，`org_list_complete=true`，无 token 字段值 | 0 |
| `--url https://github.com/octocat/Hello-World.git` | `CLASSIFICATION=REPO_EXISTS`、`REPO_HTTP=200` | 0 |
| `--url https://github.com/my-org/qoder-discovery-probe-20261026.git` | `CLASSIFICATION=NO_VISIBILITY`、`NEXT` 含 `--list-owners` | 1 |
| 禁用 credential helper 后运行 `--list-owners` / `--url` | `CLASSIFICATION=NO_CREDENTIAL`、`TOKEN_PRESENT=no` | 1 |
| 无参数 / 同时给 `--url` 与 `--list-owners` | argparse 用法错误 | 2 |

复验只做 GET；未建库、未改 origin、未 push。复验时同名仓库已存在于 `IMAM8MAHDI`，所以 `my-org/develop-skill-static-checker` 现在判 `WRONG_OWNER`；来源会话 15:45:29Z 当时尚未建库，判 `NO_VISIBILITY`，两者不矛盾。

结论边界：

- 组织所有者、admin、经典令牌含 `repo` 的路径已实测。
- 个人所有者分支已实测：本人账号 404 判 `ABSENT_CONFIRMED`，他人个人账号 404 判 `NO_VISIBILITY`。
- 占位所有者/非成员组织的 `NO_VISIBILITY` → `/user/orgs` 发现 → 所有者+可见性两问 → 新 URL `ABSENT_CONFIRMED` → 建库 → `set-url` → 推送，已实测（会话 `cc18d99f-8233-40d3-bd8c-7398d42ea3a3`）。
- `--list-owners` 脚本模式已实跑（`LIST_RC=0`）；它只覆盖有凭据的本机账号。无凭据或经典令牌 scope 缺少 `repo` 时停止；细粒度令牌不返回 scope 头，按未知处理；非 admin 成员只报告原因。
- 细粒度令牌、非 admin 成员、`ABSENT_LIKELY` 分支未实测，按 GitHub 语义写成保守规则。
- 匿名 HTTPS 404 的排除规则按 GitHub 语义写成保守规则；本案例的仓库探测均使用已存凭据。
- 推送后的并发修改后来由另一轮通过 `commit-skill-work` 提交成功（`eeff5e2`）；该提交流程不在本 Skill 范围内，本 Skill 只要求报告、不提交。

## 报告模板

```text
URL          : <用户给出的原文>
所有者/仓库  : <owner>/<repo>（如经发现，注明“确认后替换”）
本地仓库     : <depot>
本地 HEAD    : <40 位 OID>
归因         : <CLASSIFICATION>
证据         : /repos=<http>; owner=<type>; membership=<state>/<role>
                org_repos=<n>; complete=<org>,<visible>; scopes=<...>
所有者发现   : <user/orgs=<...>; candidates=<...> / 不适用>
凭据         : user=<login>; token=<未显示>
确认         : owner=<...>; <private|public|manual|no push>（时间）
建库         : <HTTP 201 / 未执行>
旧 origin    : <URL / none>
旧远端 HEAD  : <40 位 OID / none>
Remote       : origin <URL>（set-url 时注明 old→new）
分支         : <branch>（本地与远端同名）
Push         : exit=<code>; local=<40>; remote=<40>; match=<yes|no>
推送内容     : <ls-tree 文件清单>
并发复查     : <status --porcelain 摘要 / 干净>
未验证       :
```

## 完成检查清单

- [ ] URL 与分支来自用户原文或用户确认后的发现结果，没有猜测或静默替换。
- [ ] 归因完成且分类唯一；404 没有被直接当作“不存在”。
- [ ] 占位所有者或 `NO_VISIBILITY` 时，先只读运行 `--list-owners`（或等价 GET）；未把 `/user/orgs` 缺席当组织不存在。
- [ ] 换所有者前收到用户对“所有者 + 可见性”的明确选择。
- [ ] 令牌只以 `TOKEN_PRESENT=yes` 出现，未打印、未写文件。
- [ ] 建库前收到用户对私有/公开/自建/不推送的明确选择。
- [ ] 建库响应为 201，`full_name` 与 `private` 符合确认内容。
- [ ] 改 origin 前记录旧 URL 与旧远端 OID；`set-url` 仅在确认后执行。
- [ ] 先 `branch -m` 后 `push -u`，本地与远端分支同名。
- [ ] 本地 HEAD 与 `ls-remote` 的 40 位 OID 相等。
- [ ] `ls-tree` 只包含预期文件，无缓存或未跟踪目录。
- [ ] 推送后已复查工作区；并发写入只报告未提交。
- [ ] 未使用 force，未推 main，未回退 SSH。

## 资源

- `scripts/probe_github_repo.py`：只读探测、归因与所有者发现，只用 `GET`，token 仅用于请求头。
  - 仓库归因：`py -3 -B scripts/probe_github_repo.py --url "https://github.com/{owner}/{repo}.git"`
  - 所有者发现：`py -3 -B scripts/probe_github_repo.py --list-owners`（查询 `/user`、`/user/orgs`、membership 与组织配额，不创建任何资源）
  - `--json` 输出单个 JSON 对象；`--timeout` 调整超时（默认 20 秒）；`--url` 与 `--list-owners` 互斥且必须二选一。
  - 退出码：0 = 已定性（存在或确认缺失）或至少一个候选所有者；1 = 未能定性、负结果或无候选；2 = URL、网络、环境或 API 错误。
- 相邻流程：PR 用 `github-pr-create-merge-sans-gh`；发布到 main 用 `publier-skill-qoder-vers-depot-git`；本地提交用 `commit-skill-work`；ref 清理用 `nettoyer-branches-refs-git`。
