# 验证器负向测试参考

## 适用范围

本参考适用于目标 Skill 自带的 CLI 验证器：验证器读取真实项目文件，按契约返回退出码，并可能提供 `--strict-warnings`、`--allow-external` 等开关。它不用于本 Skill 的静态校验器 `scripts/validate_skill.py`；后者的回归自测交给 `skill-validator-selftest`。

## 安全规则

- 只改系统临时目录中的副本；不改项目文件、目标 Skill 或本 Skill。
- 只运行验证器，不运行生成器、迁移脚本或其他可能写文件的命令。
- 验证器必须支持显式路径参数（如 `--root`、`--csv`、`--html`）；若它硬编码真实项目根目录，停止，不要用负向测试触碰原件。
- 优先复制验证器本身并在副本上运行；若运行原验证器，先确认它只读且不会写自身目录。
- 用 `TemporaryDirectory` 或 `finally` 清理；确认临时目录不存在。
- Windows 上夹具可能含只读文件（如 `VERROU.json`）。复制用 `shutil.copyfile`，或 `copytree(..., copy_function=shutil.copyfile)`，避免继承只读位；清理前对所有副本文件 `chmod(0o666)`，否则 `rmtree` 抛 `PermissionError [WinError 5]`。
- 运行前后对验证器读取的全部项目文件做 SHA-256 比对；只在本次运行开始时取基线，不复用旧会话哈希。

## 用例矩阵

用常见的 0/1/2 契约表示成功、校验失败、输入/用法错误；目标验证器使用其他约定时按它的文档断言。

| 用例 | 破坏方式 | 预期 |
|---|---|---|
| 基线 | 不改 | 0，无 FAIL |
| 断号/重复唯一键 | 改一行 SEQ 或唯一键 | 1，指出第一个断点 |
| 派生值/分布错误 | 改一个汇总或分布值 | 1 |
| 内容不一致 | 只改 CSV 或 HTML 一边的一个单元格 | 1 |
| 输入缺失/不可读 | 删除或锁定一个输入文件 | 2 |
| 外部资源 | 注入一个外链资源 | 默认 1；`--allow-external` 时 0 + WARN |
| 仅警告 | 过期日期、旧 docstring、硬编码派生值 | 默认 0 + WARN；`--strict-warnings` 时 1 |
| 算法漂移 | 让验证器与参考实现产生不同结果 | 1 |

每个用例只制造一个缺陷；级联缺陷要分别断言，不能放宽为“有 FAIL 就行”。

## Python 模板

```python
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_writable(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_file():
            path.chmod(0o666)


def run(validator: Path, root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(validator), "--root", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )


def case(
    validator: Path,
    source: Path,
    mutate,
    expected: int,
    *args: str,
    fragments: tuple[str, ...] = (),
) -> None:
    with tempfile.TemporaryDirectory(prefix="validator-negative-") as tmp:
        work = Path(tmp) / "work"
        shutil.copytree(source, work, copy_function=shutil.copyfile)
        make_writable(work)
        mutate(work)
        result = run(validator, work, *args)
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode != expected:
            raise SystemExit(
                f"exit {result.returncode} != {expected}\n{ascii_text(output)}"
            )
        for fragment in fragments:
            if fragment not in output:
                raise SystemExit(
                    f"missing fragment: {fragment!r}\n{ascii_text(output)}"
                )
        if expected == 0 and "FAIL" in output:
            raise SystemExit("exit 0 but output contains FAIL")
```

说明：

- `source` 只放验证器读取的输入，保留相对路径；不要复制整个仓库。
- `mutate(work)` 必须只改副本中的一个不变量。
- 复制必须用 `copy_function=shutil.copyfile` 并调用 `make_writable(work)`；默认 `copy2`/`copytree` 保留只读位，清理时报 `PermissionError [WinError 5]`。若某个用例故意把副本文件设为只读，退出 `with` 前先恢复可写，否则 `TemporaryDirectory` 清理也会失败。
- 不要用可被 `python -O` 关闭的 `assert` 作为唯一断言；用显式分支或 `SystemExit`。
- 输出可能含非 ASCII 时先转义，避免 cp1252 控制台崩溃。
- 日期/mtime 用例用 `datetime.date.today()` 推导过期日期，复制后显式 `os.utime` 设置 mtime，不要硬编码某一天。
- Windows 上用 `py -3` 运行；`python` 可能是 Microsoft Store 别名。

## 字节级夹具与完整性耦合（已验证）

来源：会话 `3bf92c7b-23d2-4480-a92f-ab30f1f19e94`（2026-10-27），目标验证器为 `livrer-contrat-solidity-et-portefeuille-non-custodial` 的 `scripts/verifier_artefact.py`（6,403 B / `4ab4a2ff…`）。该回合没有用户纠正；代理自检发现夹具未隔离目标门后改道。

首轮“禁止模式”负例用文本模式改写源码，并把禁止模式源的 SHA-256 写进副本 artefact。退出码 rc=1 本来就正确，但两个门同时失败：

```text
=== interdit rc=1
FAIL artefact perime : source a1db38de4988da50 != artefact 6af02d0b19233f08
FAIL motif interdit present : selfdestruct
RESULT FAIL (2)
```

按字节重建夹具并重算副本 artefact 的 `source_sha256` 后，同一用例只命中目标门：

```text
CRLF dans la source : 0
sha interdite 6af02d0b19233f08
INTERDIT rc=1
OK   fraicheur : source 6af02d0b19233f08
FAIL motif interdit present : selfdestruct
RESULT FAIL (1)
```

本次用同一验证器在系统临时目录复现（真实 source `38f6e03a…` 与 artefact 副本，只读原件）：

| 情形 | 夹具 | 实测 |
|---|---|---|
| 基线 | 未改 | rc=0，`RESULT PASS`，`fraicheur : source 38f6e03a…` |
| A 字节变异，未重算完整性 | 源末尾按字节追加 `selfdestruct(` | rc=1，`FAIL (2)`：`artefact perime` + `motif interdit` |
| B 字节变异，重算完整性 | 同上 + 副本 `source_sha256` 改为新哈希 | rc=1，`FAIL (1)`：仅 `motif interdit`，`OK fraicheur` |
| C 文本模式往返，内容不变 | `read_text`/`write_text` 原文件 | 20,154 B → 20,661 B（+507 = 507 个换行，CRLF 0 → 507），哈希改变，rc=1 `artefact perime` |

操作顺序：

- 内容夹具一律按字节读写。文本模式在 Windows 会把 `\n` 翻成 `\r\n`；C 的字节差正好等于换行数，目标缺陷之外的漂移足以让完整性门先失败。
- 验证器同时校验完整性（源码哈希、字节数、行数）时，先写内容，再在副本中重算这些字段；A→B 的差别就是这一步。
- 断言 rc 之外还要断言“只命中目标门”：完整性项 OK、FAIL 条数等于预期、`RESULT FAIL (N)` 的 N 与失败门数一致。`rc=1` 伴随两条 FAIL 不算隔离。
- “变异确实写入副本”由 `verifier-mutation-fixture-appliquee` 负责；本节只规定内容夹具的字节模式与完整性字段同步。

证据分级：会话中的两段输出、`a1db38de`/`6af02d0b` 哈希与 `CRLF dans la source : 0` 来自工具结果，已核实；文本模式导致字节漂移是代理自述，快照未包含工具输入中的字面 `read_bytes`/`write_bytes` 调用，具体函数名为推断；A/B/C 三种情形为本次实跑复现，临时目录已清理。

## 来源会话已验证的 14 个用例

来源：会话 `4958a992-f36f-4d91-8ade-0826edb1ec6e`（2026-10-25），目标验证器为 `tableau-maitre-sequentiel` 的 `verifier_tableau_maitre.py`。脚本输出 `ALL NEGATIVE CASES PASSED`，随后清理临时目录。具体值（SEQ、S6 40/313/63、182 行）属于该目标 Skill，不是通用不变量；目标验证器版本变化后要重新确认预期。关键输出为摘要。

| 用例 | 破坏 | 预期退出 | 实测退出 | 关键输出 |
|---|---|---|---|---|
| base_copy | 无 | 0 | 0 | OK, 0 warning |
| seq_gap | CSV 第 5 行 SEQ=999 | 1 | 1 | 第一个断点 999 vs 005 |
| s6_distribution | 改 S6 分布 | 1 | 1 | magnitude 40 分布不符 |
| external_resource | HTML 注入外链脚本 | 1 | 1 | 1 external resource |
| external_allowed | 同上 + `--allow-external` | 0 | 0 | WARN, 1 warning |
| html_mismatch | 只改 HTML 一个单元格 | 1 | 1 | (83, ELEMENT) |
| missing_html | 删除 HTML | 2 | 2 | 输入文件缺失 |
| date_warning | 日期改为昨天 | 0 | 0 | WARN date mismatch |
| date_strict | 同上 + `--strict-warnings` | 1 | 1 | FAIL strict |
| docstring_warning | docstring 旧范围 | 0 | 0 | WARN SEQ 001-155 vs 182 |
| docstring_strict | 同上 + `--strict-warnings` | 1 | 1 | FAIL strict |
| parity_failure | 破坏算法等价性 | 1 | 1 | 分布不同 |
| hardcoded_s6_warning | 硬编码派生值 | 0 | 0 | WARN hardcoded |
| hardcoded_s6_strict | 同上 + `--strict-warnings` | 1 | 1 | FAIL strict |

## Windows 只读夹具（已验证）

`shutil.copytree` 默认使用 `copy2`，会保留源文件的只读属性。夹具中只要有一个只读文件（例如 `horloge_noyau/VERROU.json`，权限 `-r--r--r--`），复制后的副本就无法被 `rmtree` 删除。来源会话实测：

```text
PermissionError: [WinError 5] Accès refusé:
...\Temp\qa_tableau_q582jiri\case\ASTRO-Q°ODE_SYSTEME\horloge_noyau\VERROU.json
```

会话 `5e1598ad-b589-48fc-883a-8357b3ec2113`，JSONL L2431→L2433，2026-10-26T09:53:20Z。基线已通过，`reset()` 调用 `shutil.rmtree(case)` 时失败；Bash 工具状态为 OK，但输出以 `EXIT=1` 结束，不能只看工具状态。

已验证的修复（同会话 L2436，09:53:26Z）：复制改用 `shutil.copyfile`，`reset()` 在删除前和复制后都对副本文件执行 `chmod(0o666)`：

```python
def reset() -> Path:
    case = tmp_path / "case"
    if case.exists():
        make_writable(case)
        shutil.rmtree(case)
    shutil.copytree(pristine, case, copy_function=shutil.copyfile)
    make_writable(case)
    return case
```

修复后重跑同一 harness：10 个用例全部符合预期，`originals_intact=True`，临时目录已清理（同会话 L2440→L2447）。该规则与具体验证器无关，任何只读夹具文件都适用。

## 静态校验器自测边界

`skill-validator-selftest` 覆盖 `scripts/validate_skill.py` 的 0/1/2、frontmatter、名称、description、正文、引用、布局、代码块、编码、自指、依赖缺失和用法错误。它默认不覆盖跨 Skill 引用：修改相关代码时，手动构造一个“目录存在但缺 SKILL.md”的反引号名称，确认 exit 1；不存在的名称会被静默跳过，不能当作已验证。

它也不覆盖稳定性等待与起止指纹：修改相关代码时，手动制造并发写入，或用 `--stable-seconds 2 --stability-timeout 1` 触发超时，确认 exit 1 及 `FAIL stability` 或 `FAIL fingerprint`；正常 Skill 用默认等待运行，确认 `Fingerprint (start)` 与 `Fingerprint (final)` 的 SHA-256 相同。

## 哈希基线

```python
import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root: Path, files: list[str]) -> dict[str, str]:
    return {rel: sha256(root / rel) for rel in files}


def changed(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(
        rel for rel in before.keys() | after.keys() if before.get(rel) != after.get(rel)
    )
```

至少覆盖验证器读取的项目文件：生成器、参考库、锁文件、CSV、HTML；如果验证器读取其他输入，一并加入。原件哈希变化时停止并报告。

## 最终指纹门（已验证）

来源：会话 `a48efc65-fec8-4c6f-9ae5-0c8f8a2adc6d`（2026-10-26），目标为 `inventory-installed-skills` 的 SKILL.md。时间均为本地时间（UTC+01:00）。

| 时间 | 事件 | size | SHA-256 |
|---|---|---|---|
| 15:24:52 | validator 起止指纹一致，9 PASS / 0 FAIL，`RESULT PASS` | 9,622 B | `5ea4afac…` |
| 15:25:33 | 真实枚举与快照对比完成，`EXIT=0` | — | — |
| 15:25:37 | 另一会话写入；检查输出 `matches validator final: False` | 11,122 B | `e0f6d0e0…` |
| 15:25:47 | 重读合并并发新增后重跑 validator，9 PASS | 11,330 B | `8a42a7aa…` |
| mtime 15:25:47 | 最终双采样多次一致，`expected final: True` | 11,330 B | `8a42a7aa…` |

结论：validator 的起止指纹只证明它自己的运行窗口内未变；夹具和真实运行都发生在其后，必须等全部结束再做最终门。发现变化时旧 PASS 作废，完整重读、保留并发新增内容、确认本次修改仍在，再对合并版本重跑，只引用最终稳定版本。该会话最终保留了另一会话追加的规则 7/8，并在 11,330 B 上重新验收。

## 参考文档自洽性复核（已验证）

来源：会话 `de42a6f1-6872-4864-a837-494e5daa819e`（2026-10-26，revision 140），目标为 `verify-skill-git-head-vs-worktree`。时间均为 UTC+01:00。该回合没有用户纠正；漂移是代理在最终复核时自己发现的。

| 时间 | 事件 | SKILL.md | 参考文档 |
|---|---|---|---|
| 18:00:35 | 记录写入前快照：SKILL.md 与参考文档的当时值 | 20,803 B | 15,273 B / `2a0f4f2e…` |
| 其后 | 参考文档追加 §9/§10，正文写入“更新后 `SKILL.md` 为 296 行、正文 293 行”；此时 SKILL.md 确为 296 行 | 20,803 B / 296 行 | 574 行 |
| 18:02:23 | SKILL.md 两处措辞修改后重跑 validator：`RESULT PASS`，9 项检查无 FAIL | 21,232 B / 298 行 / `2068bad7…` | 未同步，仍写 296 行 |
| 其后 | 检索 references 中的旧快照：实际 `298 SKILL.md`，命中参考文档第 447、455 行的“296 行” | — | 需回改 |
| 修复后 | 3 次 Edit 回改快照；复核输出 `FENCES_EVEN True`（56 个围栏）、`HAS_9_10 True`、`FINAL_HASH_IN_REF True` | 21,232 B | 31,666 B / `7566dd4d…` |

要点：

- validator 的 `RESULT PASS` 与 `Fingerprint (final)` 只描述 SKILL.md。参考文档中“最终 N 行 / N B / SHA-256”不会被任何现有检查比对；SKILL.md 在参考文档写入后再改，记录即失真。本案例的表格本来标注为“追加前快照”是正确的，失真的是正文那句带“更新后”的最终表述。
- 修复顺序：SKILL.md 冻结 → 重算行数、字节、哈希 → 检索 references 中的同类记录 → 只回改失真项 → 复核围栏配对与章节 → 重新记录两边最终指纹。
- 自指边界：参考文档不能包含自身最终 SHA-256（写入即改变哈希），也不能在自身内部声明自身“最终行数”。本案例把 references 的最终哈希留在交付报告中，参考文档只记录 SKILL.md 的最终值。
- 结构检查的最小集：围栏总数必须为偶数且每块有闭合围栏；标题层级不能因追加而断裂；SKILL.md 资源清单中的文件必须存在（`validate_skill.py` 已覆盖本地引用）。
- 结论分级：上述时间、数值与检查输出为已验证；围栏与标题检查是人工复核，不是脚本断言。未验证：没有构造“围栏缺失”“标题断裂”“记录值正确但绑定旧版本”的负向夹具。

## EOL 切换与并发写入（已验证）

来源：会话 `13d0993e-26ba-49ae-b99a-efe3a002a20f`（2026-10-26，revision 31），目标为 `verify-skill-runtime-binding`。时间均为 UTC。

| 时间 | 事件 | SKILL.md | 脚本 |
|---|---|---|---|
| 15:11 前 | 上一会话 85b68db0 基线（LF） | 28,204 B / `c9e8ee7c…` | 17,741 B / `308a938e…` |
| 15:14:52 | checkout 到 `main` + fast-forward | — | — |
| 15:14:57 | 预检发现 worktree 变大 | 28,516 B / `0b4f768c…` | 18,221 B / `47825dfa…` |
| 同上 | HEAD blob | 28,204 B | 17,741 B |
| 同上 | LF 归一化 | 28,204 B / `c9e8ee7c…` | 17,741 B / `308a938e…` |
| 同上 | 字节差 / 换行数 | +312 / 312 | +480 / 480 |

佐证：`core.autocrlf=true`；`git ls-files --eol` 两个文件均为 `i/lf w/crlf`；`git status` 与 `git diff` 无内容差异；reflog 显示 `checkout: moving from skill/verify-skill-runtime-binding to main` 与 `merge … Fast-forward`。LF 归一化哈希与编辑前基线完全一致，判为行尾切换而非并发写入；代理未回退、未覆盖，直接编辑。编辑后 SKILL.md 为 30,659 B（CRLF）/ 30,336 B（LF，`786d2e23…`）。reflog 只是补充佐证：`git checkout -- <path>` 恢复单个文件不移动 HEAD，可能没有记录，不能以 reflog 缺失否定 EOL-only。

边界：该等式只对整文件统一转换成立；部分行转换或混合行尾不满足，不能自动判为 EOL-only。非 Git 目录只能用两次采样判定，结论标为“EOL-only（推断）”。同内容重写与行尾切换无法区分，但处理相同（不覆盖）。校验器仍按原始字节判定变化；EOL 判别是分诊，不是放宽指纹门。
