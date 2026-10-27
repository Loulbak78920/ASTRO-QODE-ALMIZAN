# Cas vérifié — acceptation du garde et de la propagation (2026-10-27)

## Sources

- Session `db72d65b-e96e-58e2-aa0d-611061b3d5d6` (« Test acceptation skill edit-skill-frontmatter-description »), lue le 2026-10-27 : `runtimeState=ready`, `revision=46`, `hasMoreBefore=false`.
- Session `4ce15155-ee0c-4859-8bbd-8c44384aa5b3` : cas de propagation déjà consigné dans [cas-propagation-reload-2026-10-27.md](cas-propagation-reload-2026-10-27.md).
- Les valeurs ci-dessous proviennent des sorties d'outils de la session ou de vérifications indépendantes en lecture seule exécutées le 2026-10-27 ; aucune n'est reprise d'un résumé tiers.

## Intégrité de l'installation

| Élément | Valeur observée |
|---|---|
| `SKILL.md` avant l'acceptation | 18 355 B, SHA-256 `37da07b60cf3512e74b8816bed4718bbf8091475df1bdeda03570747035e2c64` |
| description | 963 caractères, ligne 3, style `"`, LF, sans BOM |
| corps | 267 lignes mesurées par `inspect` avant la présente mise à jour |
| Après l'acceptation | SHA-256 et taille identiques ; aucun `__pycache__`/`.pyc` |

L'acceptation n'a rien écrit dans l'installation : toutes les opérations d'écriture ont eu lieu dans une copie jetable.

## Fixture et invariants

| Étape | Valeur observée |
|---|---|
| Copie | `inventory-installed-skills`, dossier = `name`, 13 093 B, SHA-256 `24a675137f77bcb7a53340584a1ba717c9cc30e0a34fc63a2b35a1ae34218b67` |
| `inspect` | ligne 3, `description_len` 934, `remaining` 90, `quote_style` `"`, `eol` LF, `bom` false, corps 165 lignes, `Files (2)` |
| Ancre réelle | `count: 1` |
| Ancre absente | `count: 0`, `unique: false`, `error: each anchor must occur exactly once`, code 1 |
| Candidat | 961 points de code, 1 769 B, une ligne |
| Dry-run | code 0, `dry_run: true`, `changed: true`, `new_len` 961, `status: would-apply`, SHA-256 inchangé, aucun `.bak`, aucun dossier de sauvegarde |
| Apply | code 0, `status: applied`, SHA-256 après `1ddb5551829ae710332aa653ea65b58d2b32dd2ca8bf5c03550a8a1e70372611` |
| Invariants | 12 sur 12 à `true`, aucune restauration |
| Sauvegarde | `SKILL.md.20261027T122949Z.bak`, 13 093 B, SHA-256 égal à l'original |
| Diff indépendant | 169 lignes avant et après, seule la ligne physique 3 diffère, autres lignes identiques octet pour octet |
| Restauration | SHA-256 revenu à `24a67513…`, taille 13 093 B |

## QA aux trois états

| État | Résultat | Comptes | Files | description | corps |
|---|---|---|---|---|---|
| Référence | `RESULT PASS`, code 0 | 9 pass, 0 fail, 0 warn | (2) | 934 | 165 |
| Appliqué | `RESULT PASS`, code 0 | 9 pass, 0 fail, 0 warn | (2) | 961 | 165 |
| Restauré | `RESULT PASS`, code 0 | 9 pass, 0 fail, 0 warn | (2) | 934 | 165 |

L'empreinte est restée stable pendant chaque validation ; aucun WARN n'apparaît sur cette fixture.

## Propagation

| Élément | Valeur observée |
|---|---|
| JSONL | `db72d65b-e96e-58e2-aa0d-611061b3d5d6.jsonl` |
| Injection | ligne 14, `2026-10-27T12:28:57.321Z`, première ligne = dossier résolu de l'installation |
| Corps injecté | 16 834 caractères après `strip()`, SHA-256 `3cccd267ecd6434473f8f2d7a6ff2d164cf3952be1b5b7c6871bc06177d09d61` |
| Corps disque | 16 836 caractères bruts, 16 834 après `strip()`, même SHA-256 |
| `dir_matches` / `body_matches` | `true` / `true` |
| Sentinelles | `attachement` 3, `panneau client` 4 |
| Listing | `2026-10-27T12:28:54.519Z`, `isInitial: true`, `skillCount` 98, segment 300, préfixe commun 299, ellipse |
| `listing_status` | `ok` |
| `panel` | `unverified_manual` |
| `verdict` | `INJECTION_OK_LISTING_OK`, code 0 |

## Choix de la session

Le JSONL au `mtime` le plus récent n'était pas la session où le Skill avait été invoqué.

| JSONL | Observation |
|---|---|
| `a973aeef…` | le plus récent lors du contrôle indépendant ; 0 injection |
| `55f63550…` | le plus récent pendant l'acceptation ; 0 injection ; `check` code 2 |
| `4ce15155…` | 1 injection exacte |
| `db72d65b…` | 1 injection exacte ; `check` code 0, `INJECTION_OK_LISTING_OK` |

La session source comptait les lignes contenant l'en-tête toutes compétences confondues (4 pour `db72d65b…`, 6 pour `4ce15155…`). Le critère de sélection est plus strict : `type: user`, `isMeta: true`, `message.content` chaîne commençant par l'en-tête, et première ligne égale au dossier résolu du Skill.

## Longueurs : cibles distinctes

| Mesure | Cible | Valeur |
|---|---|---|
| `inspect description_len` | fixture `inventory-installed-skills` | 934 |
| `check disk_description_chars` | installation `edit-skill-frontmatter-description` | 963 |

Ces deux valeurs ne mesurent pas le même fichier : aucun écart à signaler. Une comparaison de longueurs n'est valide qu'entre deux mesures de la même cible.

## Code de retour masqué

Le dry-run du garde a renvoyé 0. Le compound affichait 2 parce que le `ls` final visait le dossier de sauvegarde, que le dry-run ne crée pas. Le code du garde doit être lu immédiatement (`rc=$?`) ou la commande lancée seule.

## Statuts

| Affirmation | Statut |
|---|---|
| Installation inchangée pendant l'acceptation | observé |
| Dry-run sans écriture, sans `.bak` | observé et reproduit |
| 12 invariants après apply | observé |
| Restauration depuis `.bak` avec SHA identique | observé |
| QA PASS aux trois états | observé |
| Injection exacte et hash du corps normalisé | observé et reproduit |
| Listing à 299 + ellipse | observé et reproduit |
| JSONL le plus récent sans injection | observé et reproduit |
| Écart 934 / 963 dû à deux cibles | observé |
| Panneau client rafraîchi | non vérifié ; action manuelle |

## Règles de réutilisation

- Choisir le JSONL par injection exacte du dossier résolu ; ne jamais se fier au `mtime`.
- Exécuter le dry-run et l'apply sur une copie dont le nom de dossier égale `name` ; garder la sauvegarde hors du Skill.
- Lire le code de retour juste après chaque sous-commande ; ne pas le déduire du dernier maillon d'un compound.
- Comparer les longueurs uniquement sur la même cible.
- Prouver une restauration par l'égalité du SHA-256 avec l'original, pas par l'absence d'erreur.
- Sur une copie hors dépôt, remplacer `git diff` par un diff ligne à ligne en Python hors du Skill.
- Ne pas annoncer un rafraîchissement du panneau client : cette couche reste manuelle.
