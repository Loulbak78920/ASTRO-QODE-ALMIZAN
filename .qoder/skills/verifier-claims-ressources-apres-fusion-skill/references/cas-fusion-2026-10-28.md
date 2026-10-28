# Cas — fusion concurrente et fausse référence (2026-10-28)

## Sources

- Session `f1a9b558-b663-4e1c-9e64-4e44620a3ac2`, titre « 更新布局测量 Skill », tour `3edb4df1-9021-4ead-8d17-5825e592d8b1` : sorties d'outils utilisées ci-dessous. `runtimeState` vaut `running` à chaque lecture.
- Session concurrente `632937de-e8d5-45c1-b253-8f3e93830d04`, titre « 创建布局测量 Skill », `running` pendant le constat.
- Relevés directs en lecture seule le 2026-10-28 entre 12:05:32 et 12:05:42 +0100, sur `mesurer-layout-avec-harnais-iframe`.
- Les heures des messages de session sont en UTC ; les sorties d'outils et les mtime sont locales (+0100).

## 1. Chaîne d'empreintes de `SKILL.md`

| Instant | Taille | SHA-256 | Auteur |
|---|---:|---|---|
| avant mise à jour | 12 870 | `f83870ecc0dcf6d122a66852eb715b0b229a1b23156d61ad918efe03e66c993e` | session f1a9b558 |
| après 9 éditions | 14 404 | `22f09615de3b6284468e2fa997f8593dd4fc46a03da292f1e1f9772a00db28dc` | f1a9b558 |
| après 2 éditions de plus | 15 951 | `aa65bd33256597bef850e40d7b8b96893845e0bf17f8633ddb926ba8111841c9` | f1a9b558 |
| fusion en cours | — | `3fa2ab577dacfa9131ba249c00454bd12914eec9692428bbffd2a1e940cab908` | 632937de |
| fusion en cours | 16 448 | `ac5fe84f9d8c6cd9c4710b8e435c854e75ea63f41a3fab0296213c23a2e49663` | 632937de |
| fusion stabilisée | 16 703 | `426c3935b29a31d308d0dc0d2df088389e94d9b0a693d127a19bdaff8ba20cad` | 632937de |
| alignement final | 16 741 | `02ed5f57576120e7f5e4cea6da70ed2937bb7daa2369da96117356208ccd177f` | f1a9b558 (12:03:43) |

Les deux premières empreintes correspondent à des états que la session f1a9b558 a elle-même relevés. Les empreintes `3fa2ab57…` et `ac5fe84f…` proviennent de relevés intercalés ; `426c3935…` est l'état stable de 11:52:17 à 11:53:02, puis à 12:02:06.

## 2. Sorties du validateur

Avant la fusion, avec trois fichiers :

```text
Fingerprint (start): 14404 bytes | mtime=2026-10-28T11:50:48+01:00 | sha256=22f09615…
Files (3): SKILL.md, references/cas-verifie-hub-ponts.md, references/modeles-harnais.md
PASS local references: 2 checked
Summary: 10 pass, 0 fail, 0 warn
RESULT PASS
```

Après l'ajout du script `capturer_cdp.mjs` :

```text
Fingerprint (start): 16703 bytes | mtime=2026-10-28T11:52:17+01:00 | sha256=426c3935…
Files (4): SKILL.md, references/cas-verifie-hub-ponts.md, references/modeles-harnais.md, scripts/capturer_cdp.mjs
PASS local references: 3 checked
Summary: 10 pass, 0 fail, 0 warn
RESULT PASS
```

`local references: 2 checked` puis `3 checked` compte des chemins résolus. Aucune ligne du validateur ne porte sur le contenu des fichiers cités.

## 3. Marqueurs personnels

Extrait de la sortie de comptage après la fusion :

```text
--- markers SKILL.md ---
1
2
1
118:| `--window-size=1024` ... | repli CDP |
147:- `references/modeles-harnais.md` — ... repli CDP.
148:- `references/cas-verifie-hub-ponts.md` — ... repli CDP et largeurs exactes, limites.
--- markers references ---
1
1
1
references/modeles-harnais.md:0
references/cas-verifie-hub-ponts.md:0
No matches found
```

Les trois marqueurs personnels sont présents avec les multiplicités attendues (1, 2, 1). Les lignes 147-148 annoncent « repli CDP » dans les deux références, où le comptage donne `0` à cet instant (état `426c3935…`, 16 703 o).

## 4. Le négatif était transitoire

- 11:52 : `repli CDP` = 0 dans `references/modeles-harnais.md` et 0 dans `references/cas-verifie-hub-ponts.md`.
- 12:02:06 : le propriétaire a ajouté le contenu ; comptage de `CDP` = 7 et 5 occurrences. `SKILL.md` n'a pas bougé (`426c3935…`).
- 12:03:43 : `SKILL.md` passe à `02ed5f57…` (16 741 o) ; les lignes 147-148 gagnent « en-tête et chevauchement » et « auto-test ».
- 12:05:42, relevé direct : `grep -c "CDP"` donne 3 lignes dans `modeles-harnais.md` et 5 lignes dans `cas-verifie-hub-ponts.md` ; `grep -n "Repli CDP"` donne un titre dans chaque fichier (`## 7. Repli CDP…`, `## E. Repli CDP…`) ; `repli CDP` en minuscules reste à **0** dans les deux, casse oblige. Empreintes `bd9ec84a…` (12 368 o) et `e5a9ecb7…` (16 494 o).

À 12:05, l'affirmation est soutenue si le jeton est copié depuis le fichier cité (`Repli CDP`), et fausse si le jeton est copié depuis la ligne d'affirmation (`repli CDP`). Aucune édition n'a été nécessaire côté f1a9b558 ; les deux lignes ont été alignées par la session propriétaire.

## 5. Verdicts

| Instant | Verdict | Justification |
|---|---|---|
| 11:52 | `INDETERMINE` (`CLAIM_EMPTY` `PROVISIONAL`) | deux thèmes annoncés absents, mais la session 632937de écrit encore |
| 12:02 | `COHERENT` | contenu CDP présent, `SKILL.md` inchangé depuis 11:52 |
| éditer à 11:52 | rejeté | aurait dupliqué un travail en cours ou supprimé une affirmation devenue correcte |

Leçon de casse : un jeton repris de la phrase d'affirmation peut rester à 0 alors que le contenu existe. Le jeton se copie dans le fichier cité, pas dans la ligne qui l'annonce.

## Limites

- L'état de 11:52 n'est pas reproductible depuis le disque courant : les références ont été réécrites après. Les valeurs de la section 3 viennent des sorties d'outils de la session, pas d'un rejeu indépendant.
- Le comptage de la session (« 7 », « 5 ») et le `grep -c` du relevé direct (« 3 », « 5 ») ne mesurent pas la même chose : occurrences contre lignes contenant le motif. Ne pas les comparer sans le dire.
- La casse change le résultat : « repli CDP » reste à 0 même quand le contenu « Repli CDP » existe. Un zéro ne condamne que la chaîne exacte testée.
- Le cas démontre un négatif transitoire, pas un défaut permanent du paquet ni du validateur.
- Aucune conclusion n'est tirée sur les sessions postérieures à 12:05 ; la session f1a9b558 était encore `running`.
- Le cas ne prouve pas que toute la prose des références est exacte : seuls les jetons comptés le sont.
- Les heures UTC des messages et les heures locales des outils ne sont pas converties entre elles.
