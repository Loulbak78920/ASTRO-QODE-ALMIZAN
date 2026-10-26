---
name: mesure-cesium-133-geolocalisee
description: "重新测量、验证并封存 IMAM8MAHDI 的地理定位铯-133 量子指标：Windows 地理定位与时间、w32tm/cp850 解码、Open-Meteo 海拔与 SRTM30m 控制、WGS84 大地测量与 IAU 恒星时、SHA-256 快照与脚本指纹、Monade 9/9 + 23/23 双重证明，以及主表 S19 层的受保护重新生成。适用于任何 Cs-133 重测、快照或 Monade 证明验证、zoneinfo/w32tm/SRTM 诊断，或依赖 S19 的表格重新生成。中文触发：铯-133、地理定位、量子指标、快照校验、Monade 证明、主表 S19。"
---

> 本文是 [SKILL.md](../SKILL.md) 的完整中文译本，法文原版为权威版本。命令、路径、标识符与代码块保持原文。

# 地理定位铯-133 — 重测与证明

重新测量或审计已封存的 Cs-133 测量及其 S19 锁，不修改封存库，也不手动编辑交付物。相邻的 `tableau-maitre-sequentiel` Skill 仍是表格结构的权威；本 Skill 覆盖测量链、快照与 Monade 双重证明。

## 何时使用

- 根据本机位置与时间，重新测量 E、T、λ、反冲、WGS84 重力、相对论膨胀、GMST/LAST 以及 Cs-133 周期数。
- 验证现有快照：`empreinte_contenu_sha256`、`empreinte.script_sha256`、23/23 和 9/9。
- 诊断 `zoneinfo`、`w32tm`、Open-Meteo/SRTM、`KeyError`、`ZeroDivisionError` 或 `S19 refusee`。
- 在新测量后重新生成表格，使 S19 与快照保持一致。

不要用于修改物理公式、表格模式、S6 或 `horloge_noyau/`：请遵循 `tableau-maitre-sequentiel` 并请求明确决定。

## 不可协商的契约

1. **唯一来源**：`ASTRO-Q°ODE_SYSTEME/outils/mesurer_metriques_cesium_133.py` 负责采集与封存；`ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_cesium_133.py` 负责计算与验证；`ASTRO-Q°ODE_SYSTEME/donnees/mesure_quantique_cesium_133.json` 是证据。不要把公式复制到报告或临时脚本中。
2. **快照由生成器产生**：永远不要手动编辑 JSON。`empreinte_contenu_sha256` 覆盖不含该字段的规范化 JSON；`empreinte.script_sha256` 绑定测量脚本。脚本或内容的任何修改都会使旧快照失效：必须重新测量。
3. **双重证明**：需要 `valider_metriques_cesium_133` 的 23 项控制、`confirmer_harmonie_et_prouver_justesse` 的 9 个层，以及 `preuve_totale = true`。否则生成器拒绝 S19（`RuntimeError: S19 refusee`）；不得绕过。
4. **仅一次 bind**：`MonadeSupreme.unit(engagement).bind(_valider_et_sceller).isoler()`。失败时 bind 返回 `0 : HÉLIUM`；第二次 bind 会验证一个已降级的令牌。预期令牌为 `SCEAU_MONADE_CS133`。
5. **时间**：`time.time_ns()` + Windows 时区（`tzutil /g`）+ 本地偏移 + `w32tm /query /status`。不要使用 `zoneinfo`（本机缺少 tzdata）。子进程字节按 `utf-8`、`cp850`、`cp1252` 顺序解码。
6. **海拔**：以 Open-Meteo Elevation 为主，OpenTopoData SRTM30m 为控制；保留 `altitude_spread_m`。只有当 `vertical_accuracy > 0` 时，Windows 海拔才作为回退。`--latitude/--longitude` 或 `--altitude` 是覆盖值，不是地理定位。
7. **诚实限制**：永远不要把位置说成经认证的 GPS、把海拔说成已做大地水准面校正、把时钟说成经认证的 TAI/UTC、把量子相位说成已测量、或把相对论偏移说成干涉测量结果。报告中要复述快照的 5 条限制。
8. **写入**：不要向 `horloge_noyau/` 写入任何内容，未经明确决定不得修改 `lib_cesium_133.py`，永远不要手动编辑 CSV/HTML。只有采集器写入快照；只有生成器写入表格。

## 文件与命令

- 采集器：`ASTRO-Q°ODE_SYSTEME/outils/mesurer_metriques_cesium_133.py`
- 计算与验证：`ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_cesium_133.py`
- 快照：`ASTRO-Q°ODE_SYSTEME/donnees/mesure_quantique_cesium_133.json`
- 定向测试：`ASTRO-Q°ODE_SYSTEME/tests/test_metriques_cesium_133.py`
- 生成器：`ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py`
- 表格验证器：`C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py`

```bash
# Verification lecture seule du snapshot, des hashes, de la Monade et de S19
py -3.12 "C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"

# Re-mesure (ecrit le snapshot par defaut)
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3.12 outils/mesurer_metriques_cesium_133.py

# Tests cibles
py -3.12 -m unittest tests.test_metriques_cesium_133 -v

# Regeneration du tableau (verifie le snapshot et les 9 couches)
py -3.12 generer_tableau_maitre_sequentiel.py

# Validation structurelle du tableau
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

`py -3.12`（已验证 3.12.7）是仓库约定；`py -3` 在本机也可用。不要使用 Microsoft Store 的 `python` 别名。控制台消息保持 ASCII。

## 操作流程

### 0. 预检

1. 检查上述五个文件以及对 `horloge_noyau/` 的读取权限。
2. 运行只读验证器。若失败，先诊断，不要为了掩盖失败而重新生成表格。
3. 记录起始哈希和计数器，以便操作后比较。

### 1. 验证当前状态（只读）

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

期望 `OK - mesure Cs-133 verifiee`，并在输出中确认：23/23、存储 9/9 与实时 9/9、`preuve_totale True`、S19 19 行、哈希一致。同时运行定向测试。

### 2. 重新测量

1. 允许 Windows 定位（设置 > 隐私 > 位置），并确认提供程序返回 `Ready` / `Granted`。
2. 不带参数运行采集器，进行地理定位测量。
3. 若失败，明确选择回退方案并声明：
   - 位置不可用：`--latitude` + `--longitude`（覆盖值，非地理定位）；
   - 海拔不可用：`--altitude`（覆盖值）；
   - 无网络：`--no-network --altitude`。
4. 等待 `OK - Cesium-133 mesure geolocalisee`，然后记录新的哈希对、位置、海拔、SRTM 差值、时间以及 `w32tm` 精度。
5. 不要编辑生成的快照。

### 3. 验证新快照

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI" --snapshot-only
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3.12 -m unittest tests.test_metriques_cesium_133 -v
```

- 若出现 `script de mesure modifie`：测量后脚本发生了变化；用当前版本重新测量，不要改写哈希。
- 若 23/23 或 9/9 失败：不要重新生成表格；修正原因后重新测量。
- 将新值与物理预期（ν₀、E、T、λ、g）比较，并报告任何偏差。

### 4. 重新生成并验证表格

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3.12 generer_tableau_maitre_sequentiel.py
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

等待摘要 `OK - N entrees sequentielles - M strates`，然后运行正典验证器。确认 S19 仍为 19 行 `CS-01..CS-19`、SEQ 连续、CS-18 `PREUVE ARCHITECTURE = 9/9`、CS-19 `PREUVE TOTALE = true` + `SCEAU_MONADE_CS133`，并且 S19 的 `SOURCE` 携带新快照哈希（CS-19 还携带脚本哈希）。再次运行本 Skill 的验证器检查整体。

### 5. 报告

```text
Mesure Cs-133 : <date UTC> | <fuseau> | w32tm <precision ou absente>
Position : <lat> <N/S> <lon> <E/W> +/-<accuracy> m | altitude <m> (ecart SRTM <m>)
Hashes : contenu <12...> | script <12...>
Monade : metriques 23/23 | architecture 9/9 (stockee et live) | preuve_totale true
Tableau : N entrees / M strates | S19 19 lignes CS-01..CS-19 | SEQ <debut>-<fin>
Limites : 5 limites du snapshot reprises telles quelles
Fichiers : <chemins absolus>
Mesure / calcule / override : <distinguer explicitement>
```

### 6. 维护本 Skill

在一次测量被接受且表格重新生成后，对 `references/contrat-mesure-et-limites.md` 的基线做定向编辑，然后重新运行 `skill-file-qa`。不要整体重写 Skill。如果 23 项控制、9 个层、快照模式或 S19 行数发生变化，同时更新契约与验证器。

## 已观察到的陷阱

| 症状 | 原因 | 修正 |
|---|---|---|
| `ZoneInfo` 找不到 / `load_tzdata` 失败 | 本机缺少 tzdata | `tzutil /g` + `astimezone()`；不要把安装 tzdata 作为前置条件 |
| `w32tm` 无法读取或出现 `?` 字符 | 以 UTF-8 读取 Windows 控制台字节 | 按 `utf-8 → cp850 → cp1252` 解码；解析“Précision”行中的 `ns` |
| 生成器中出现 `KeyError: 'resolution_python_s'` | `_H` 指向 `metriques.temps`，值在 `snapshot.temps` | 使用 `_H_SYS['resolution_python_s']` |
| 缺少 SRTM 控制 | 读取了 `metriques.position` | 读取 `snapshot['position']['details_altitude']['opentopodata_srtm30m']['elevation_m']` |
| `ZeroDivisionError: float division by zero` | 在篡改指标测试中 `nu0 = 0` | 在任何除法前返回 `structure_valide=False`；测试应产生 HÉLIUM，而不是异常 |
| `RuntimeError: S19 refusee` | 快照或架构证明不完整 | 重新验证快照与 9 个层；不要绕过 |
| `snapshot: script de mesure modifie depuis la mesure` | 测量后脚本被修改 | 重新测量；永远不要编辑 `script_sha256` |
| `UnicodeEncodeError` cp1252 | `print()` 中包含箭头、上标或重音字符 | ASCII 输出、`_ascii`、`py -3.12` |
| 使用 `--no-network` 时出现 `altitude indisponible` | 没有海拔来源 | 提供 `--altitude` 或使用有效的 Windows 海拔；否则如实失败 |
| `w32tm` 不可用 | 服务或权限问题 | 继续使用 Python 分辨率，并声明缺少 NTP 精度 |
| S19 的 `SOURCE` 不含新哈希 | 测量后未重新生成表格 | 运行生成器；不要编辑 CSV/HTML |
| 手动修改了 S19 | 直接编辑交付物 | 通过重新生成恢复；S19 由快照派生 |

## 完成定义

- [ ] 验证器：内容与脚本哈希有效，23/23，存储与实时 9/9，`preuve_totale true`，无 HÉLIUM 状态。
- [ ] 定向测试通过（`tests.test_metriques_cesium_133`）。
- [ ] S19：19 行 `CS-01..CS-19`，SEQ 连续，CS-18/CS-19 证明齐全，`SOURCE` 与当前快照对齐。
- [ ] 正典表格验证器：0 失败；S6 仍为 40/313/63。
- [ ] 报告：区分实测 / 计算 / 覆盖值，复述 5 条限制，给出绝对路径。
- [ ] 未向 `horloge_noyau/` 写入，未手动编辑快照、CSV 或 HTML。
- [ ] 若修改了本 Skill：`skill-file-qa` 为 PASS 且 0 FAIL。

## 资源

- `scripts/verifier_mesure_cesium.py`：对快照、哈希、Monade 和 S19 的只读编排；ASCII 输出，退出码 0/1/2。
- `references/contrat-mesure-et-limites.md`：模式、23 项控制、9 个层、已验证基线、S19 集成、决策树与限制。
- `references/skill-zh.md` 与 `references/contrat-mesure-et-limites-zh.md`：完整中文译本；法文版为权威。
- `tableau-maitre-sequentiel`：正典验证器与表格结构契约。
- `skill-file-qa`：编辑本 Skill 后的结构 QA。
- `verifier-livrables-csv-html-windows-fr`：Windows 控制台、CSV BOM/`;`、HTML 检查。
- `validation-navigateur-par-repli`：可选的视觉检查及结构化回退。
