# Cas vérifié — visibilité de la description dans la liste (2026-10-28)

## Sources

- Session `717fdc90-978c-426d-ba7f-5a63fa3f92c7` (« 更新可复用技能 »), lue le 2026-10-28 : `revision=11`, `runtimeState=running`, `hasMoreBefore=true`. Le Skill édité était `planifier-budget-paquet-skill` ; la leçon est générique et porte sur l'édition de description.
- Sessions d'acceptation : `71cf2953-6ada-5cac-a449-a2ae5dbc6db2` (avant correction) et `60aaaa72-085a-5582-adfc-adbc821bf741` (après correction).
- Rejeu indépendant le 2026-10-28 depuis la session d'édition de `edit-skill-frontmatter-description` avec le `listing` installé.

## Échec observé — description de 1000 caractères

| Élément | Valeur |
|---|---|
| `SKILL.md` | 22 991 B, `mtime=2026-10-28T01:38:27+01:00`, SHA-256 `00dfa64b23d4c69320e540519a74739801f103a093e8e39a2ce5577027355413` |
| description | 1000 caractères, ligne 3 |
| Plan A | première différence au caractère **309** ; `visible_299_covers_diff=False` |
| Entrée de liste | segment de 299 caractères + `…`, `prefix_match=True` |

Quatre déclencheurs ajoutés en queue comptaient 0 dans l'entrée de liste et 1 sur le disque : `同一会话二次调用`, `旧注入记录`, `自指提示词的计数作废`, `验收分级`. La session `71cf2953` a conclu `ACCEPTANCE FAIL` pour cette unique raison : le préfixe visible était identique au disque, mais les déclencheurs de queue n'étaient ni affichés ni prouvés indexés.

Le test « quel Skill choisirais-tu » n'a pas aidé : la session a choisi `verify-injected-skill-body-freshness` alors que la cible était `planifier-budget-paquet-skill`. Ce résultat ne distingue pas « index non rafraîchi » de « déclencheur hors fenêtre » : poids faible, jamais une preuve.

## Correction — description de 1007 caractères

| Élément | Valeur |
|---|---|
| `SKILL.md` | 22 962 B, `mtime=2026-10-28T01:51:43+01:00`, SHA-256 `c784c60644bce9d6fad469708049c6ab0af88f2b8fb1b49842977cdaa7b22717` |
| description | 1007 caractères, ligne 3, seule ligne modifiée (`differing_lines=[3]`, 248 lignes, corps 244) |
| Sauvegarde | `SKILL.md.20261028T005143Z.bak`, SHA-256 `00dfa64b…` |
| QA | `RESULT PASS`, 9 pass / 0 fail / 0 warn, `NO_NEW_WARN` |

Positions mesurées, toutes dans la fenêtre de 299 :

| Déclencheur | Position | Fin |
|---|---|---|
| `清单截断` | 95 | 99 |
| `自污染` | 111 | 114 |
| `同一会话二次调用` | 115 | 123 |
| `旧注入记录` | 124 | 129 |
| `验收分级` | 130 | 134 |

`清单截断` comptait 2 occurrences dans la description de 1007 caractères : c'est pourquoi `visibility` exige `count == 1` au lieu de retenir la première position.

## Entrée fraîche sans `/skills reload`

| Élément | Valeur |
|---|---|
| Écriture | `00:51:43Z` (`01:51:43+01:00`) |
| Session ouverte après | `60aaaa72-…`, prompt `00:52:11.145Z` |
| Attachement `skill_listing` | `2026-10-28T00:52:15.683Z`, soit ~33 s après l'écriture |
| Champs | `is_initial=true`, `skill_count=125`, `common_prefix_chars=299`, `prefix_matches=true`, `ends_with_ellipsis=true`, `desc_segment_chars=300` |
| Verdict | `LISTING_OK`, code 0, `injection: unverified`, `panel: unverified_manual` |

Le rejeu du 2026-10-28 sur le JSONL de `60aaaa72` rend les mêmes valeurs (`entries_total=1`, `entries_fresh=1`, `latest_timestamp=2026-10-28T00:52:15.683Z`). La session d'édition, ouverte avant l'écriture, ne peut pas servir de preuve : son attachement est antérieur au `mtime` et `listing` l'écarte comme périmé.

## Statuts

| Affirmation | Statut |
|---|---|
| Une description de 1000 caractères n'affiche que 299 caractères + `…` dans la liste | observé deux fois (sessions `71cf2953` et `60aaaa72`) |
| Un déclencheur de queue est invisible pour le modèle | observé côté liste ; conséquence sur la sélection non prouvée |
| La limite de 299 caractères est un contrat stable du client | non vérifié ; borne empirique, à remesurer après mise à jour du client |
| Une session ouverte après l'écriture fournit un `isInitial` frais | observé (`00:52:15.683Z` > `00:51:43Z`), rejoué le 2026-10-28 |
| Le test « quel Skill choisirais-tu » a un pouvoir de décision | infirmé : choix d'un autre Skill du même domaine |
| Le panneau client est rafraîchi | non vérifié ; action manuelle |

## Règles de réutilisation

- Mesurer chaque déclencheur critique avec `visibility` : `count == 1` et `end ≤ 270` ; un doublon ne localise rien.
- Ne pas conclure « liste périmée » quand la queue manque : c'est la troncature. Déplacer le déclencheur, ne pas réécrire `SKILL.md` pour forcer un rechargement.
- Pour une entrée fraîche, préférer une session ouverte après l'écriture, avec un prompt en lecture seule ; exiger `isInitial` et un horodatage postérieur au `mtime`.
- Consigner la borne de 299 caractères comme une observation datée, pas comme un contrat garanti.
- Un choix de Skill par le modèle est un indice de poids faible dès que plusieurs Skills du même domaine concourent.
