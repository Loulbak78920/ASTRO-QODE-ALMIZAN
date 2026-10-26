# Cs-133 测量契约与限制

> 本文是 [contrat-mesure-et-limites.md](contrat-mesure-et-limites.md) 的完整中文译本，法文原版为权威版本。数字、哈希、路径与标识符保持原文。

2026-10-26 验证的参考快照。测量值是有日期的；只有结构与证明的不变量是永久的。新测量会改变哈希和数值：接受后更新基线。

## 1. 测量链

| 步骤 | 文件 | 作用 |
|---|---|---|
| 采集 | `ASTRO-Q°ODE_SYSTEME/outils/mesurer_metriques_cesium_133.py` | Windows 位置、系统时间、时区、`w32tm`、DEM 海拔、重算、双重证明、快照 |
| 计算 | `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_cesium_133.py` | SI/CODATA 常数、WGS84、GMST IAU 1982、23 项控制、Monade、快照验证 |
| 证明 | `ASTRO-Q°ODE_SYSTEME/donnees/mesure_quantique_cesium_133.json` | 带哈希的 JSON 快照、`preuve_totale`、限制 |
| 集成 | `ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py` | S19 层、`verifier_snapshot_cesium_133` + `confirmer_harmonie_et_prouver_justesse`，证明不完整时拒绝 |
| 测试 | `ASTRO-Q°ODE_SYSTEME/tests/test_metriques_cesium_133.py` | 公式、封存快照、篡改拒绝、9 个层、CSV 中的 S19 |

采集器不测量量子相位：它根据位置、时刻和常数计算指标。相对论偏移是相对于指定参考计算出来的，不是通过干涉测量得到的。

## 2. 快照与哈希

顶层键：

```text
schema, genere_le_utc, methode, temps, position, constantes,
metriques, validation_monade, preuve_totale, limites, empreinte,
empreinte_contenu_sha256
```

- `schema`：`MESURE_QUANTIQUE_CESIUM_133/v1`。
- `empreinte_contenu_sha256`：除自身之外所有字段的规范化 JSON 的 SHA-256。
- 规范化 JSON：`json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)`。
- `empreinte.script_sha256`：测量脚本字节的 SHA-256。
- `verifier_snapshot_cesium_133(snapshot, script)` 控制：模式、内容指纹、脚本指纹（若提供）、重算 23 项控制、与存储控制一致、重算单子判决、存储的架构证明、`preuve_totale=True`。

后果：

- 手动修改快照会破坏 `empreinte_contenu_sha256`。
- 修改测量脚本会破坏 `script_sha256`，即使快照本身完好。
- 两种情况唯一合规的修复都是重新测量；永远不要改写哈希。

## 3. 指标的 23 项控制

| # | 控制 | 验证内容 |
|---|---|---|
| 1 | `atome_cs133` | Z=55, N=78, A=133，自旋 7/2，F=3 与 F=4 能级 |
| 2 | `frequence_si` | ν₀ 精确为 9 192 631 770 Hz |
| 3 | `energie_coherente` | E = hν₀ |
| 4 | `energie_ev_coherente` | E 的 eV 值 = E / e |
| 5 | `temperature_coherente` | T = E / k_B |
| 6 | `temperature_mk_coherente` | T 的 mK 值 = T × 1000 |
| 7 | `longueur_onde_coherente` | λ = c / ν₀ |
| 8 | `longueur_onde_mm_coherente` | λ 的 mm 值 = λ × 1000 |
| 9 | `impulsion_coherente` | p = h / λ |
| 10 | `recul_coherent` | ν_rec = hν₀² / (2mc²), E_rec = hν_rec |
| 11 | `position_valide` | 纬度 −90..90，经度 −180..180，精度 ≥ 0 |
| 12 | `altitude_valide` | 海拔 −500..9000 m，差值 ≥ 0 |
| 13 | `sources_valides` | 地理定位与海拔来源非空 |
| 14 | `gravite_valide` | 9,0..10,0 m/s² |
| 15 | `rayon_valide` | 6,3..6,5 Mm |
| 16 | `rotation_valide` | 速度 0..500 m/s，参考速度 ≥ 0 |
| 17 | `dilatation_gravitationnelle_coherente` | g·h/c²，符号与每 24 h 周期数 |
| 18 | `dilatation_cinetique_coherente` | v²/(2c²)，符号与每 24 h 周期数 |
| 19 | `dilatation_locale_coherente` | 重力 − (v² − v_ref²)/(2c²) |
| 20 | `dilatation_totale_coherente` | −GM/(r c²) − 动能项 |
| 21 | `temps_sideral_valide` | GMST/LAST 在 0..360°，LAST 小时数 = 度数/15 |
| 22 | `cycles_valides` | `unix_ns` 为整数且 > 0，时长 0..86 400 s，周期数 = ν₀ × 时长，不确定度 > 0 |
| 23 | `horodatage_valide` | UTC、本地时间与时区非空，偏移 −12 h..+14 h |

重要保护：若结构不可读或 `nu0 <= 0`，验证器在任何除法前返回 `{"structure_valide": False}`。强制 `frequence_hz = 0` 的测试必须产生 HÉLIUM 单子，而不是 `ZeroDivisionError`。

## 4. 架构的 9 个层

`confirmer_harmonie_et_prouver_justesse()` 返回 `couches_ok`：

| # | 层 | 验证内容 |
|---|---|---|
| 1 | `①_informe_quatre_familles` | 计算四个家族 + M=24434 分解 |
| 2 | `②_etats_de_matiere` | 极性 ±313 与锚点 M=24434 |
| 3 | `③_complexe_point_zero` | COMPLEXE = LA TABLE = 零点 |
| 4 | `④_q_degre_derives_table` | Q° 由 LA TABLE 派生，而非 313/24434 |
| 5 | `cycles_trinite_calcules_depuis_zero` | 从零计算 dx/dy/dz/dt，dt 总和一致，域 −9..+9 |
| 6 | `trajectoire_zero_expansion` | 零 → 完整膨胀的轨迹 |
| 7 | `horloge_deduite_du_noyau` | 时钟由同一核心推导，无任意值 |
| 8 | `sync_cinq_familles` | 物质 ↔ 五家族同步，M=24434，COMPLEXE = 表 |
| 9 | `⑤_monade_juste` | `unit` + `isoler` + 灵魂治理 + 有效的 HÉLIUM 后备 |

整体证明要求 `monade_juste` 与 9 个层全为真。生成器还要求快照中存储的证明为真。

## 5. Monade 链

```text
engagement = empreinte_contenu(metriques)
monade = MonadeSupreme.unit(engagement).bind(_valider_et_sceller).isoler()
jeton attendu = SCEAU_MONADE_CS133
```

- `_valider_et_sceller` 在任一控制失败时抛出异常；`bind` 捕获异常并返回隔离的 `0 : HÉLIUM`。
- `monade_juste` 要求：预期令牌、`est_isolee`、非 HÉLIUM，以及 `OMEGA_MONAD_SOUL.gouverne(jeton)`。
- 只 bind 一次。第二次 bind 会作用于结果（可能是 HÉLIUM），无法修复任何东西。
- 快照存储 `validation_monade.metriques`（控制、判决、历史）与 `validation_monade.architecture`（9 个层的判决）。

## 6. 已验证基线

2026-10-25T23:25:24.555975Z 的快照，2026-10-26 验证：

| 元素 | 值 |
|---|---|
| 内容哈希 | `8fb08b28d390796192d5cf738f3e6e09cb59d5c2321a7b861f746cb8d2c3016b` |
| 脚本哈希 | `bfb95373f1557874be30c510667fd8348e5f05fcd959efcdc57fc538d0248da0` |
| UTC / 本地时间 | `2026-10-25T23:25:24.555975Z` / `2026-10-26T00:25:24.555975+01:00` |
| 时区 / 偏移 | `Romance Standard Time` / `+3600 s` |
| 位置 | `45.044766577161575 N`、`5.039379914878178 E`，水平精度 143 m |
| 海拔 | 153,0 m（Open-Meteo），SRTM30m 控制 157,0 m，差值 4,0 m |
| `w32tm` | 来源 `time.windows.com,0x9`，精度 119,209 ns |
| Python 分辨率 | 15,625 ms；使用的不确定度 = max = 15,625 ms |
| 跃迁 | ν₀ 9 192 631 770 Hz；E 6,091102297113866e-24 J（38,0177 µeV）；T 441,1767434817876 mK；λ 32,61225571749406 mm |
| 反冲 | ν_rec 1,4114726315157167e-6 Hz；E_rec 9,352516671228239e-40 J |
| WGS84 重力 | 9,805766130413133 m/s²；地心半径 6 367 625,834832317 m |
| 膨胀 | 引力项 +1,6692890939018852e-14；动能项 6,028278557180383e-13；本地/海平面 1,666401898995543e-14；总/无穷远 −6,970991601083279e-10 |
| 每 24 h 周期数 | 引力项 +13,258218203640274；动能项 −478,79203665438274；本地/海平面 +13,235286849086672；总/无穷远 −553 666,3965549042 |
| GMST / LAST | 25,71241535898298° / 30,75179527386116°（2,0501196849240775 h） |
| 自午夜起的周期数 | 775 164 592 245 089,8 ± 143 634 871,4 |
| Monade | 指标 23/23，架构 9/9，`preuve_totale=true` |
| 表格 | 204 条 / 20 层；S19 19 行 `CS-01..CS-19`，SEQ 186–204 |

此基线用于回归。它不是物理常数：新测量会改变位置、时间、周期数、哈希，从而改变 S19 行。

## 7. 生成器中的 S19 集成

- S19：`S19 · Césium-133 géolocalisé (métriques quantiques mesurées)`。
- 19 条 `CS-01..CS-19`：原子、跃迁、SI 定义、换算、反冲、位置、大地测量、相对论、时间戳、恒星时、周期数、双重证明。
- 生成器调用 `verifier_snapshot_cesium_133(snapshot, script)`，然后调用 `confirmer_harmonie_et_prouver_justesse()`。若缺少证明：`RuntimeError: S19 refusee: preuve Monade incomplete (snapshot ou architecture)`。
- 不要混淆的块：
  - `_H = snapshot["metriques"]["temps"]`：计算中使用的时间。
  - `_H_SYS = snapshot["temps"]`：完整系统块，含 `w32tm`、`resolution_python_s`、`precision_windows_s`、`incertitude_utilisee_s`。
  - `_P_SYS = snapshot["position"]`：完整位置块，含 `details_altitude`。
- SRTM 控制：`_P_SYS["details_altitude"]["opentopodata_srtm30m"]["elevation_m"]`；不要在 `metriques.position` 中查找。
- `_SOURCE` 含 `donnees/mesure_quantique_cesium_133.json · SHA-256 <16 premiers caractères>…`。CS-19 还含 `script SHA-256 <16 premiers caractères>…`。
- 所有 S19 行均由快照派生。不要编辑 CSV 或 HTML；重新生成。

## 8. 决策树

| 症状 | 诊断 | 操作 |
|---|---|---|
| `empreinte de contenu invalide` | 快照被修改或损坏 | 恢复有效副本；否则重新测量 |
| `script de mesure modifie depuis la mesure` | 测量后脚本被修改 | 用当前版本重新测量；不要编辑哈希 |
| 一项或多项 23/23 控制为假 | 公式、位置、时间或来源不一致 | 阅读控制名称；修正原因；重新测量 |
| 一个 9/9 层为假 | 封存架构发生漂移 | 检查 `couches_ok`；不要重新生成表格；请求决定 |
| `monade_juste=false`, `etat_helium=true` | 至少一项控制失败 | 诊断控制；修正后重新测量 |
| `S19 refusee` | 快照或架构证明不完整 | 重新验证快照与 9 个层；不要绕过 |
| 位置不可用 | Windows 权限或提供程序 | 允许定位；否则显式覆盖并声明 |
| 海拔不可用 | 网络或 DEM API | 提供 `--altitude`；否则使用有效的 Windows 海拔；否则失败 |
| `w32tm` 不可用 | 服务或权限 | 继续使用 Python 分辨率；声明缺少 NTP 轨迹 |
| S19 的 `SOURCE` 没有新哈希 | 表格未重新生成 | 运行生成器 |
| `UnicodeEncodeError` | cp1252 控制台 | ASCII 输出；`py -3.12` |

## 9. 诚实限制

复述这五条限制：

1. Wi-Fi/蜂窝定位：精度由 Windows 提供，不是经认证的 GPS。
2. DEM 正高：未建模大地水准面；报告来源之间的差值（例如 153 m 与 157 m）。
3. 系统时钟不是经认证的 TAI/UTC；Windows NTP 同步由 `w32tm` 记录。
4. 量子相位未被测量：只计算周期数与理论偏移。
5. 相对论偏移是相对于指定参考计算的，不是通过干涉测量得到的。

不要把计算值变成实验测量。不要把位置或海拔覆盖值说成地理定位。

## 10. 维护

- 在测量被接受且表格重新生成后：更新基线（§ 6）、哈希、S19 计数与验证日期。
- 若 23 项控制、9 个层、快照模式或 S19 行数变化：同时更新 `SKILL.md`、本文档和 `scripts/verifier_mesure_cesium.py`。
- 每次编辑 Skill 后：运行 `skill-file-qa` 并要求 `RESULT PASS` 且 0 FAIL。
- 没有验证器、测试和表格验证器的实际输出，永远不要宣称测量或重新生成成功。
