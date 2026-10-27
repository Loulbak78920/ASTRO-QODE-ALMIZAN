# 全量回归记录（2026-10-26）

- 被测代码提交：`6208b00`（`main`），工作树干净
- 环境：Windows，`py -3`，`PYTHONIOENCODING=utf-8`
- 结果：46 项检查通过，0 项失败（`RESULT REGRESSION PASS`）
- 说明：原始日志位于临时目录，运行后已清理；本文件是汇总记录，不包含原始日志。

## 分组结果

| 组 | 检查 | 结果 |
|---|---|---|
| 包验收 | `skill-file-qa` | 9 pass / 0 fail / 1 warn；`RESULT PASS` |
| 自审 | `audit --help-probe` | 4 pass / 0 fail；exit 0 |
| 形态断言 | `total=1`；`two-files` 正例；`two-files` 反例 | exit 0；0；1 |
| 未验证分支 | 子命令表 `--expect` | exit 3，`RESULT UNVERIFIED` |
| 用法错误 | `--expect` 缺 `--help-probe` | exit 2 |
| 结构基线 | `compare` 同源 | exit 0 |
| 结构变异 | 7 种 `--kind` | 全部检出；`mutate` exit 0 |
| 替换模式 | 成功并清理；`--keep`；目标缺失；缺 `--with`；散文漂移；`--expect-exit 2` | 0；0；2；2；1；0 |
| 确定性模式 | 超时；忽略漂移；缺 `{target}`；source=out；尾随 argv；模式冲突 | 2；1；2；2；2；2 |
| 输入错误 | `compare` 缺文件 | exit 2 |
| 完整性 | 源文件与译本 SHA-256 | 运行前后一致 |

`skill-file-qa` 的唯一 warn 是 `WARN layout: unexpected file '.gitattributes'`；该文件是仓库元数据，不是 Skill 内容。

## 变异覆盖

`heading`、`table`、`code`、`language`、`checklist`、`inline`、`number` 七种变异均由 `compare` 在对应维度检出；`checklist` 输出为规范的 `[x]` 翻转。

## 复现命令

```bash
py -3 scripts/audit_contracts.py mutate <source.md> --out <copy.md> \
  --kind <kind> \
  --validator 'py -3 scripts/audit_contracts.py compare <source.md> {target}'

py -3 scripts/audit_contracts.py mutate --copy <translation.md> \
  --replace "<old>" --with "<new>" --workdir <dir> -- \
  py -3 scripts/audit_contracts.py compare <source.md> "{mutated}"
```

## 指纹

| 文件 | 字节 | SHA-256 |
|---|---|---|
| `SKILL.md` | 13,114 | `edc8c587fab1e7e798b2a7978049924912dc63ff1305408edd7915bc120eb83f` |
| `references/contract-audit.md` | 15,767 | `9afbe2066a94e9b1f4e577f8ae04491315d5063b50452bc20ae657d711c98af5` |
| `scripts/audit_contracts.py` | 48,916 | `3e0dddfa6c9d227b964fd063cb4b10806a41a83284e42b4cec484bf0145b0572` |
| `.gitattributes` | 19 | `d60f352d0db1404c70afb4bb8b2ca3fd1c610572aa40720e8a0b7baa7885418c` |

## 覆盖边界

- 结构检查与变异检测不覆盖散文语义；散文漂移仍返回校验器 0，`mutate` 按预期报 exit 1。
- 本记录只证明上述 46 项检查；不替代 `skill-validator-selftest` 的系统性反例回归。
