---
name: bilingual-skill-parity
description: "Créer ou mettre à jour un SKILL.md bilingue avec deux versions complètes et strictement parallèles (français et chinois) : mêmes sections, tableaux d'erreurs, blocs de code, listes de contrôle et faits partagés, frontmatter unique inchangé, aucune section résumée ; valider la parité avec scripts/check_bilingual_parity.py puis skill-file-qa. Utiliser dès qu'un Skill doit être livré en deux langues, qu'une section « 速查 » ou « quick reference » remplace la deuxième langue, ou qu'il faut corriger une divergence de structure entre versions. 用于双语 Skill 的完整对等编写、中文速查替换与双语结构校验。"
---

# Parité bilingue des Skills / 双语 Skill 完整性

> Ce Skill ne s'applique que lorsqu'un livrable bilingue est demandé. Un Skill monolingue reste valide. / 本 Skill 仅在明确要求双语交付时生效；单语 Skill 仍然合法。

## Quand l'utiliser

Créer ou mettre à jour un `SKILL.md` livré dans deux langues, ou corriger une version dont la deuxième langue n'est qu'un résumé. Utiliser aussi lorsqu'une section `中文速查` remplace la version complète, ou lorsque les sections, tables ou blocs de code divergent entre les langues.

Ne pas utiliser pour traduire un document ordinaire, pour un Skill d'une seule langue, ni pour remplacer la vérification de format : charger `skill-file-qa` après la présente procédure.

## Règles de parité

- **Deux versions complètes.** Chaque langue contient toutes les règles, pas un résumé. Une section `中文速查` n'est jamais une deuxième version acceptable.
- **Même plan.** Les deux versions ont 8 sections dans le même ordre. Les titres sont traduits ; le niveau et l'ordre restent alignés.
- **Mêmes tables.** Même nombre de tables, de colonnes et de lignes. La table d'erreurs conserve toutes ses lignes.
- **Mêmes blocs de code.** Même nombre, même langage de fence, contenu identique. Ne pas traduire les identifiants, commandes, chemins, erreurs ni sélecteurs.
- **Mêmes listes de contrôle.** Même nombre d'items ; chaque action reste présente.
- **Mêmes faits.** Chiffres, chemins, noms d'outils et messages d'erreur identiques. Normaliser les séparateurs : `25 000` et `25,000` désignent la même valeur.
- **Un seul frontmatter.** Le bloc `---` initial reste unique. `name` ne change pas ; `description` reste sur une ligne, ≤ 1024 caractères, et est citée si elle contient « deux-points + espace ».
- **Longueur.** Le corps de `SKILL.md` fait moins de 500 lignes. Si les deux versions complètes dépassent cette limite, s'arrêter et proposer un découpage `references` ; ne pas résumer la deuxième langue.

## Procédure

- **Lire l'existant.** Lire le `SKILL.md` réel et lister les fichiers. Relever le frontmatter, les 8 sections, les tables, les blocs de code et les listes de contrôle. Ne pas partir d'un souvenir ni d'un résumé.
- **Construire la carte de parité.** Pour chaque section, noter le nombre de tables et de lignes, de blocs de code, d'items de checklist et les fragments en ligne protégés. La version principale sert de référence.
- **Écrire la version principale complète.** Si le Skill existe, conserver toutes les règles encore valides. Corriger les faits et les exemples avant de dupliquer.
- **Écrire la deuxième langue en entier.** Traduire section par section, sans fusionner ni supprimer. Conserver les mêmes tables, blocs de code, items et fragments protégés.
- **Laisser le frontmatter intact.** Ne pas dupliquer `---`, `name` ou `description`. Si un déclencheur dans la deuxième langue est nécessaire, l'ajouter dans la même valeur `description`, sur une ligne.
- **Appliquer le gabarit.** Utiliser un seul titre H1, les sections principales en H2, puis le séparateur « ## Version chinoise complète / 完整中文版 » et les sections secondaires en H3.
- **Valider.** Exécuter `scripts/check_bilingual_parity.py`, puis `skill-file-qa`. Relire le fichier réel après correction.

```text
# Titre bilingue / 双语标题
## Section principale
...
## Version chinoise complète / 完整中文版
### Section secondaire
...
```

## Échecs vérifiés et action

Cas observés et correction attendue. La table doit rester identique en nombre de lignes et de colonnes dans les deux langues.

| Symptôme observé | Cause | Action |
|---|---|---|
| `中文速查` ne contient que 7 points alors que la version complète a 8 sections | la deuxième langue a été résumée | remplacer par 8 sections complètes, puis relancer `scripts/check_bilingual_parity.py` |
| deux blocs `---` ou deux clés `name` et `description` | frontmatter dupliqué | garder un seul frontmatter, `name` inchangé, `description` sur une ligne |
| 8 sections dans une langue, 7 dans l'autre | section omise ou fusionnée | aligner l'ordre et le nombre de sections |
| `py -3` ou `SKILL.md` traduit dans un bloc de code | code localisé par erreur | garder le code identique ; traduire seulement la prose autour |
| 4 lignes dans la table d'erreurs françaises, 3 en chinois | ligne de tableau omise | conserver le même nombre de lignes et de colonnes |
| `25 000` et `25,000` comparés comme deux valeurs différentes | séparateurs numériques non normalisés | normaliser les séparateurs avant la comparaison |
| plus de 500 lignes dans `SKILL.md` | deux versions complètes trop longues | s'arrêter et proposer un découpage `references` ; ne pas résumer la deuxième langue |
| le runtime n'affiche que la première langue | injection tronquée | vérifier le fichier, essayer `/skills reload`, puis découper la version complète dans `references` |

## Vérification automatique

Depuis le dossier du Skill :

```bash
py -3 scripts/check_bilingual_parity.py .
```

Le script lit `SKILL.md`, ne l'exécute pas, et vérifie :

- frontmatter unique, `name` aligné sur le dossier, `description` sur une ligne et ≤ 1024 caractères ;
- corps < 500 lignes ;
- 8 sections alignées, tables et lignes, blocs de code et listes de contrôle ;
- fragments en ligne et nombres normalisés ;
- absence de deuxième version résumée.

Codes de sortie : 0 = aucun FAIL, 1 = au moins un FAIL, 2 = usage ou environnement. `skill-file-qa` reste la porte de vérification du format et de la syntaxe ; ce script ajoute seulement la parité.

## Limites

- Le script vérifie la structure, pas la qualité de la traduction, l'exactitude des faits ni le rendu runtime.
- Un fichier conforme ne prouve pas que le runtime injecte les deux versions ; si seule la première langue apparaît, vérifier le fichier, essayer `/skills reload`, puis envisager un découpage `references`.
- Une divergence de sens peut subsister malgré une structure identique : relire les deux versions.

## Rapport

Indiquer séparément :

- **Parité structurelle** : sections, tables, blocs de code, listes et fragments protégés, avec le nombre de contrôles reçus et attendus.
- **Qualité de traduction** : non vérifiée par le script ; relecture humaine effectuée ou non.
- **Runtime** : versions effectivement chargées ; ne pas confondre fichier valide et Skill chargé.
- **Statut** : PASS ou FAIL du script et de `skill-file-qa`, sans remplacer un FAIL par une conclusion optimiste.

## Checklist finale

- [ ] Le besoin bilingue est explicite ; un Skill monolingue n'est pas concerné.
- [ ] La deuxième langue est une version complète, pas `中文速查`.
- [ ] Les deux versions ont 8 sections dans le même ordre.
- [ ] Les tables ont le même nombre de lignes et de colonnes.
- [ ] Les blocs de code sont identiques, y compris `py -3` et `SKILL.md`.
- [ ] Les listes de contrôle ont le même nombre d'items.
- [ ] Les fragments en ligne et les nombres sont alignés.
- [ ] Le frontmatter est unique ; `name` et `description` restent valides.
- [ ] `scripts/check_bilingual_parity.py` et `skill-file-qa` passent.
- [ ] Le corps fait moins de 500 lignes, ou un découpage `references` a été validé.

## Version chinoise complète / 完整中文版

### 何时使用

创建或更新以两种语言交付的 `SKILL.md`，或修正第二种语言只是摘要的版本。当 `中文速查` 取代完整版本，或两种语言的章节、表格、代码块出现分歧时，也使用本 Skill。

不要用于翻译普通文档、单一语言的 Skill，也不要用来替代格式验收：完成本流程后加载 `skill-file-qa`。

### 对等规则

- **两个完整版本。** 每种语言都包含全部规则，而不是摘要。`中文速查` 永远不能作为可接受的第二版本。
- **同一结构。** 两个版本都有 8 节，顺序相同。标题可以翻译；层级与顺序保持一致。
- **相同表格。** 表格数量、列数和行数相同。错误表保留所有行。
- **相同代码块。** 数量相同、围栏语言相同、内容一致。不要翻译标识符、命令、路径、错误文本或选择器。
- **相同检查清单。** 条目数量相同；每个动作都保留。
- **相同事实。** 数字、路径、工具名和错误消息一致。归一化分隔符：`25 000` 与 `25,000` 表示同一数值。
- **只有一个 frontmatter。** 开头的 `---` 块保持唯一。`name` 不变；`description` 保持一行，≤ 1024 字符，并在包含“冒号+空格”时加引号。
- **长度。** `SKILL.md` 正文少于 500 行。如果两个完整版本超过此限制，停止并提议拆分到 `references`；不要摘要第二种语言。

### 操作流程

- **读取现有内容。** 读取真实的 `SKILL.md` 并列出文件。记录 frontmatter、8 节、表格、代码块和检查清单。不要凭记忆或摘要开始。
- **建立对等清单。** 对每一节记录表格数与行数、代码块数、检查清单条目数以及受保护的内联片段。以主语言版本为基准。
- **完整编写主语言版本。** 如果 Skill 已存在，保留所有仍然有效的规则。在复制前先修正事实和示例。
- **完整编写第二种语言。** 逐节翻译，不合并、不删除。保留相同的表格、代码块、条目和受保护片段。
- **保持 frontmatter 不变。** 不要重复 `---`、`name` 或 `description`。如果第二种语言需要触发词，将其加入同一个 `description` 值，并保持一行。
- **套用模板。** 只用一个 H1 标题，主语言章节用 H2，然后使用「## Version chinoise complète / 完整中文版」分隔，第二语言章节用 H3。
- **验证。** 运行 `scripts/check_bilingual_parity.py`，再运行 `skill-file-qa`。修正后重新读取真实文件。

```text
# Titre bilingue / 双语标题
## Section principale
...
## Version chinoise complète / 完整中文版
### Section secondaire
...
```

### 已验证失败与处理

已观察案例与预期修正。两种语言中的表格必须保持相同的行数和列数。

| 观察到的症状 | 原因 | 处理 |
|---|---|---|
| `中文速查` 只有 7 条，而完整版有 8 节 | 第二种语言被摘要化 | 替换为 8 个完整章节，然后重新运行 `scripts/check_bilingual_parity.py` |
| 两个 `---` 块，或重复的 `name` 与 `description` 键 | frontmatter 重复 | 只保留一个 frontmatter，`name` 不变，`description` 保持一行 |
| 一种语言有 8 节，另一种只有 7 节 | 章节遗漏或合并 | 对齐顺序和章节数量 |
| 代码块中的 `py -3` 或 `SKILL.md` 被翻译 | 错误地本地化代码 | 保持代码一致，只翻译周围的说明 |
| 法语错误表有 4 行，中文错误表只有 3 行 | 表格行遗漏 | 保持相同的行数和列数 |
| `25 000` 与 `25,000` 被当成两个不同值 | 数字分隔符未归一化 | 比较前归一化分隔符 |
| `SKILL.md` 超过 500 行 | 两个完整版本过长 | 停止并提议拆分到 `references`；不要摘要第二种语言 |
| 运行时只显示第一种语言 | 注入被截断 | 核对文件，尝试 `/skills reload`，然后把完整版本拆到 `references` |

### 自动校验

在 Skill 目录中执行：

```bash
py -3 scripts/check_bilingual_parity.py .
```

脚本只读取 `SKILL.md`，不执行其中的代码，并检查：

- 只有一个 frontmatter，`name` 与目录一致，`description` 单行且 ≤ 1024 字符；
- 正文 < 500 行；
- 8 节对齐，表格与行数、代码块和检查清单一致；
- 内联片段与归一化数字一致；
- 不存在被摘要化的第二版本。

退出码：0 = 无 FAIL，1 = 至少一个 FAIL，2 = 用法或环境错误。`skill-file-qa` 仍是格式与语法验收关口；本脚本只增加对等检查。

### 限制

- 脚本只检查结构，不检查翻译质量、事实准确性或运行时呈现。
- 文件通过校验不代表运行时同时注入两个版本；如果只出现第一种语言，核对文件，尝试 `/skills reload`，再考虑拆分到 `references`。
- 即使结构一致，语义仍可能偏离：必须人工复读两个版本。

### 报告

分别说明：

- **结构对等**：章节、表格、代码块、清单和受保护片段，以及实际与预期的检查数量。
- **翻译质量**：脚本不验证；说明是否进行了人工复读。
- **运行时**：实际加载了哪些版本；不要把文件有效等同于 Skill 已加载。
- **状态**：脚本与 `skill-file-qa` 的 PASS 或 FAIL，不得用乐观结论替代 FAIL。

### 最终检查清单

- [ ] 双语需求已明确；单语 Skill 不在范围内。
- [ ] 第二种语言是完整版本，不是 `中文速查`。
- [ ] 两个版本都有 8 节，顺序相同。
- [ ] 表格的行数和列数一致。
- [ ] 代码块一致，包括 `py -3` 与 `SKILL.md`。
- [ ] 检查清单的条目数量一致。
- [ ] 内联片段与数字对齐。
- [ ] frontmatter 唯一；`name` 与 `description` 仍然有效。
- [ ] `scripts/check_bilingual_parity.py` 与 `skill-file-qa` 通过。
- [ ] 正文少于 500 行，或已验证 `references` 拆分方案。
