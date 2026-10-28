# Cas vérifié — description seule, Skill non appelé (2026-10-27)

## Sources

- Session `c6fcec56-a27c-49fb-9db7-1207f56a0d34` (« 创建可复用 Skill »), lue le 2026-10-27 : `runtimeState=cold`, `revision=0`, `hasMoreBefore=true`. Seul le dernier tour (« 压缩 SKILL.md 的 description », 13:23:22.720Z) concerne ce cas.
- Cible éditée : `adopt-concurrent-duplicate-skill`, dont le dossier d'installation est une racine d'archive (`.gitattributes`, `.qoder/skills/*`).
- Les valeurs de cette fiche proviennent des sorties d'outils de la session ; les contrôles marqués « reproduit » ont été refaits le 2026-10-27 avec les scripts installés.

## Édition observée

| Élément | Avant | Après |
|---|---|---|
| `SKILL.md` | 38,217 B, SHA-256 `3881287a4099b1b2065b37945d39a64bbe2f5bbb64049c2506599dcf0a603712` | 37,773 B, SHA-256 `8e6f1641b2282cca4073cad45f07d1c9d61b0faf465e5af37e0d3f04da2dab32` |
| description | 1004 caractères, ligne 3 | 834 caractères, ligne 3 |
| style / EOL / BOM | `"`, CRLF 341, aucun BOM | inchangés |
| corps | 337 lignes | 337 lignes |

- Dry-run : `status: would-apply`, `old_len 1004`, `new_len 834`, `remaining 190`, `sha256_before 3881287a…`, aucun octet écrit.
- Apply : `status: applied`, `restored` absent ; sauvegarde `SKILL.md.20261027T132532Z.bak` de SHA-256 `3881287a…`, identique à l'original.
- Diff structurel : 341 lignes avant et après, seule la ligne 3 diffère ; CRLF 341/341, aucun LF isolé, aucun BOM.

## Deux cibles de QA

| Cible | Fichiers | Comptes | Résultat |
|---|---|---|---|
| Racine d'archive | `Files (15)` (`.gitattributes`, 14 fichiers sous `.qoder/skills/...`) | 10 pass, 0 fail, 13 warn | `RESULT PASS`, code 0, `WARN_SETS_IDENTICAL` |
| Fixture à 2 fichiers | `Files (2)` (`SKILL.md`, `references/preuves-session.md`) | 10 pass, 0 fail, 0 warn | `RESULT PASS`, code 0 |

Les 13 WARN de la racine sont des WARN de layout dus aux fichiers préexistants de l'archive. Ils ne sont pas causés par l'édition et ne se comparent jamais aux 0 WARN de la fixture : la comparaison avant/après n'est valide que sur la même cible. Le nombre de WARN préexistants n'est pas fixe (10 observés dans un cas antérieur, 13 ici).

## Couche liste seule

Le Skill édité n'a pas été appelé : `check` ne peut produire ni injection ni hash de corps. Trois lectures successives ont été nécessaires.

| Essai | Lecture | Résultat |
|---|---|---|
| 1 | `message.content` | 0 entrée : les enregistrements de liste ont `message: null` |
| 2 | `attachment.content`, dernières entrées dans l'ordre du glob | 1697 entrées ; les dernières lues dataient du 2026-10-26 (15:13:05.004Z, 12:11:33.088Z, 12:12:00.171Z, 12:12:46.743Z), préfixe 299 à 0 |
| 3 | `attachment.content`, tri par `record['timestamp']` | 1699 entrées ; plus récente 2026-10-27T13:27:17.759Z ; 13 postérieures à l'écriture ; 299 premiers identiques |

Re-scan indépendant du 2026-10-27 : 1703 entrées, plus récente 2026-10-27T13:29:31.108Z, 17 postérieures à l'écriture. La session d'édition elle-même portait une entrée fraîche à 13:25:46.611Z, segment de 300 caractères finissant par `…`, 299 premiers identiques au disque.

Un enregistrement de liste expose les clés `content`, `isInitial`, `names`, `skillCount`, `type` sous `attachment`. L'ordre du glob n'est pas chronologique : sans tri par timestamp, une entrée ancienne peut être prise pour la plus récente.

## `check` sans injection de ce Skill

| Moment | Commande | Sortie observée |
|---|---|---|
| Avant correctif | `check adopt… --session-jsonl c6fcec56….jsonl --sentinel "RESULT PASS"` | `FAIL`, code 1 : l'injection choisie était celle de `edit-skill-frontmatter-description` (13:23:38.392Z), `declared_base_dir` étranger |
| Après correctif | même commande | code 2, `no injection record found for this Skill`, `injection_records_total: 3`, `injection_records_for_skill: 0` |
| Contrôle positif | `check edit-skill-frontmatter-description …` sur la même session | `INJECTION_OK_LISTING_OK`, code 0 |

Le script filtre désormais les injections par `same_dir(declared_base_dir, skill_dir)` avant `pick_injection`. Une session qui ne contient que l'injection d'un autre Skill n'est pas une preuve d'injection pour la cible ; elle ne doit pas produire un `FAIL` trompeur.

## Sauvegarde et clé `backup`

La sortie `replace --apply` expose `backup` (chemin complet) et `backup_dir` ; la clé `backup_path` n'existe pas. Un lecteur qui interroge `backup_path` obtient `None` alors que la sauvegarde existe. Contrôle reproduit sur une fixture : `backup` = `…\backup\SKILL.md.20261027T133018Z.bak`, `backup_path` = `None`. Lire `backup` ou lister `--backup-dir` ; ne pas conclure à l'absence de sauvegarde.

## Statuts

| Affirmation | Statut |
|---|---|
| 1004 → 834, hashes et tailles ci-dessus | observé dans les sorties d'outils |
| Sauvegarde de SHA-256 égal à l'original | observé |
| QA racine 15 fichiers / 13 WARN, fixture 2 fichiers / 0 WARN | observé ; fixture reproduite le 2026-10-27 |
| WARN dus à des fichiers préexistants de l'archive | observé (liste des WARN) |
| 1699 entrées et 13 postérieures au moment de la session | observé |
| 1703 entrées et 17 postérieures au re-scan | observé le 2026-10-27 |
| `check` rendait `FAIL` avec une injection étrangère avant correctif | observé |
| `check` rend 2 sans injection de ce Skill après correctif | observé |
| Panneau client rafraîchi | non vérifié ; action manuelle |

## Règles de réutilisation

- Pour une édition de description seule, ne pas appeler le Skill : utiliser `listing` et déclarer l'injection `unverified`.
- Lire `attachment.content`, jamais `message.content` ; trier toutes les entrées par timestamp avant de choisir la plus récente.
- Exiger un segment de 300 caractères finissant par `…` dont les 299 premiers égalent le disque, ou l'égalité complète.
- Distinguer les deux cibles de QA et ne comparer les WARN que sur la même cible ; le compte de WARN préexistants varie avec le contenu de l'archive.
- Lire le chemin de sauvegarde dans `backup`, pas dans `backup_path`.
- Sans injection de la cible, attendre le code 2 ; une injection étrangère ne doit jamais être acceptée comme preuve.
