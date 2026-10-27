# Cas vérifié — description 1018 → 1004 (2026-10-27)

## Sources

- Session `31261187-98b3-4e8e-bbb1-9130e53b0815` (« 更新并发重复 Skill »), lue le 2026-10-27 : `runtimeState=cold`, `hasMoreBefore=false`, 6 messages.
- Session `d46562df-075e-46eb-9a6a-11b844fd7b63`, lue le 2026-10-27 : une demande et une proposition complète, aucune écriture.
- Les chiffres ci-dessous proviennent des sorties d'outils de `31261187` et de son rapport final ; ils ne sont pas repris d'un résumé tiers.

## Chronologie observée (UTC)

| Heure | Événement |
|---|---|
| 10:32:03 | Demande initiale ; la cible est `adopt-concurrent-duplicate-skill` |
| 10:36:22 | L'utilisateur répond « 确认，按此方案执行 » |
| 10:36:27–10:36:32 | Trois échantillons stables : SKILL.md 33,008 B `54528881…` ; references 31,463 B `a1511a45…` |
| 10:37 | Préflight des ancres, sauvegarde (`...20261027-1037.bak`), remplacement de la ligne de description |
| 10:38:02 | mtime final observé de `SKILL.md` (11:38:02 +01:00) après les éditions de corps |
| 10:40:13 | L'utilisateur demande « reload skills 并验证新 description 生效 » |
| 10:40:56 | Horodatage cité par le rapport final pour la pièce jointe de liste passée à la nouvelle description |

Le remplacement de description et les éditions de corps sont deux étapes distinctes : les invariants « corps identique » ne valent que pour la première.

## Référence de départ

| Élément | Valeur observée |
|---|---|
| SKILL.md | 33,008 B, SHA-256 `54528881db72c80d0e2129f9cab5cf152d4675884b8d6a4be6c950a2258539af` |
| references/preuves-session.md | 31,463 B, SHA-256 `a1511a45e098794b70e0ecf9293c934ab9488616959c1f79508bd6a5717fa545` |
| description | 1018 caractères, une ligne |
| corps | 308 lignes au moment du remplacement de description |

## Préflight des ancres

Sortie observée, dans l'ordre :

| Ancre | Occurrences |
|---|---|
| `把「接管现有 / 缩窄后新建并存 / 停止 / 只读保留 / 明确分工」` | 1 |
| `选择保持现状时只读保留：记录创建者与全部写入者、首次时间，双采样 size、mt` | 1 |
| `选择缩窄后新建时冻结重合包全部哈希、写清委派边界、复查目标仍不存在、只归因新目标` | 1 |
| `最终三方哈希；用于` | 0 |
| `编辑期间反复 file changed、Edit 返回 0 occurrence` | 1 |
| `、夹具清理报 WinError 5 或 WinError 32。中文触发：` | 1 |
| `、三方哈希、RESULT PASS 复核。关键词：` | 1 |
| `cleanup pending."` | 0 |

Deux ancres à 0 ont imposé l'abandon du remplacement partiel. Le texte réel contenait « 。 » au lieu de « ； » et une virgule au lieu du point avant le guillemet. La mémoire de l'agent n'est pas une source fiable pour la ponctuation.

## Candidats mesurés

| Candidat | Longueur | Décision |
|---|---|---|
| 1 | 1016 | acceptable mais insuffisant pour les nouveaux déclencheurs |
| 2 | 1008 | acceptable |
| 3 | 1139 | refusé, dépasse 1024 |
| 4 | 1004 | retenu |

## Remplacement programmatique

Sortie observée :

```text
orig sha 54528881db72c80d0e2129f9cab5cf152d4675884b8d6a4be6c950a2258539af
desc lines [2]
name adopt-concurrent-duplicate-skill desclen 1004 bodylines 308
bak C:\Users\Administrateur\.qoder\tmp\adopt-concurrent-duplicate-skill-SKILL.md.20261027-1037.bak 33008
```

- `desc lines [2]` est un index 0 dans le frontmatter ; la ligne physique est la troisième (base 1).
- La sauvegarde est hors du dossier du Skill, 33,008 B, identique à l'original.
- Le premier `Edit` a retourné : `The file changed since your last read. Your edit was applied to the current contents`. L'édition a été appliquée, mais l'avertissement impose une relecture avant toute conclusion.

## QA finale

| Élément | Valeur observée |
|---|---|
| Résultat | `RESULT PASS`, code de sortie 0 |
| Comptes | 10 pass, 0 fail, 10 warn |
| Fichiers | `Files (12)` |
| description | une ligne, 1004 caractères |
| corps | 337 lignes à la QA finale |
| SKILL.md | 38,217 B, SHA-256 `3881287a4099b1b2065b37945d39a64bbe2f5bbb64049c2506599dcf0a603712` |
| references/preuves-session.md | 39,622 B, SHA-256 `2ff754fe9d62fb4d47d710bb484ef7984368e237333a94d877677f32bee82854` |

Les 10 WARN sont des WARN de layout : `.gitattributes` et des archives `.qoder/skills/...` déjà présentes. Aucun fichier n'a été ajouté par cette édition. La différence 308 → 337 vient des éditions de corps postérieures au remplacement de description, pas de la ligne `description`.

## Propagation

Le troisième tour a comparé la description sur disque aux pièces jointes de liste de Skills de la session :

- la pièce jointe de 10:32:05 portait l'ancienne version ;
- celle de 10:37:27 portait la nouvelle ;
- celle de 10:40:56 concordait sur les 299 premiers caractères, le 300e étant une ellipse.

L'agent ne peut pas exécuter `/skills reload` ; le rafraîchissement du panneau client reste manuel. Cette preuve couvre la couche liste de la session, pas le panneau client.

## Statuts

| Affirmation | Statut |
|---|---|
| Cible absente avant création du présent Skill | observé |
| Baseline 1018 / 308 / 33,008 B | observé |
| 8 ancres, 2 à zéro | observé |
| Candidats 1016 / 1008 / 1139 / 1004 | observé |
| Sauvegarde externe de 33,008 B | observé |
| `file changed` au premier `Edit` | observé |
| QA 10 / 0 / 10, PASS | observé |
| WARN dus à des fichiers préexistants | observé dans le rapport et la liste des WARN |
| Marques PyYAML en base 0 dans le frontmatter | déduit de `desc lines [2]` pour la troisième ligne physique |
| Liste d'attachements passée à la nouvelle version | rapporté par le rapport final du troisième tour ; le JSONL n'a pas été rouvert indépendamment ici |
| Panneau client rafraîchi | non vérifié ; action manuelle de l'utilisateur |

## Règles de réutilisation

- Mesurer les candidats avant l'écriture ; 1139 est refusé par la limite, pas par le style.
- Compter chaque ancre sur la valeur parsée ; 0 ou ≥ 2 interdit le `Edit` partiel.
- Pour une description longue, remplacer la ligne entière plutôt que d'élargir une ancre.
- Sauvegarder hors du Skill et vérifier le SHA-256 de la sauvegarde.
- Re-parser après écriture : name, autres clés, octets du corps, EOL, BOM, ligne modifiée.
- Limiter l'invariant de corps à l'étape description ; les éditions de corps ultérieures changent légitimement le compte.
- Comparer les ensembles de WARN, pas seulement leurs nombres.
- Sortir du JSON ASCII sur une console cp1252 ; un `print` direct de texte non ASCII lève `UnicodeEncodeError`.
- Enregistrer séparément les hashes de SKILL.md et des références.
