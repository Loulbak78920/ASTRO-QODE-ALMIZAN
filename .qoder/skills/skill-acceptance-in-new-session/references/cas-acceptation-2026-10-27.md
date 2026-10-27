# Cas vérifié — acceptation d'un Skill dans une session indépendante (2026-10-27)

## Sources

- Session parente `4ce15155-ee0c-4859-8bbd-8c44384aa5b3`, tour « tester le skill dans une nouvelle session », horodatage message 2026-10-27T12:28:18.303Z.
- Session enfant `db72d65b-e96e-58e2-aa0d-611061b3d5d6`, titre « Test acceptation skill edit-skill-frontmatter-description », un seul tour, `hasMoreBefore: false`.
- Les deux sessions ont été relues par `read_chat_session` avec `includeToolOutputs` le 2026-10-27. Les messages sont en UTC ; les sorties d'outils portent l'heure locale (+0100).
- Cible du test : `edit-skill-frontmatter-description`, état 18 355 B, SHA-256 `37da07b60cf3512e74b8816bed4718bbf8091475df1bdeda03570747035e2c64`, 5 fichiers, QA `PASS` 9/0/0.

## Chronologie observée

| Heure | Événement |
|---|---|
| 12:28:18.303 | Le parent reçoit « tester le skill dans une nouvelle session » |
| 12:28:52.482 | Prompt enfant enregistré (session `db72d65b…`, aucun historique) |
| 12:28:54.519 | `skill_listing` de l'enfant : 98 Skills, préfixe 300 = 299 + ellipse, `is_initial: true` |
| 12:28:57.321 | Injection du Skill dans le JSONL enfant, ligne 14 |
| entre 12:28 et 12:31 | Deux `wait_chat_sessions` rendent `timeout` (révisions 23 puis 31, même `activeTurnId`, `pendingInteractionCount: 0`) |
| non horodaté | `turn_completed` (révision 39) ; lectures enfant aux révisions 33 et 42 |
| 12:31:37.529 | Message final du parent : « Callback de supervision reçu », rapport enfant déjà lu |

Le mode `supervise` et `timeoutMs: 60000` sont attestés dans le JSONL du projet (appels `mcp_call`, lignes 1003, 1008, 1013 et 1028) : `create_chat_session` reçoit `callbackMode: "supervise"`, et les trois `wait_chat_sessions` utilisent 60000 ms. Les deux premiers rendent `timeout` après 60,04 s et 60,47 s, le troisième `turn_completed` après 11,08 s. Ces arguments n'apparaissent pas dans les snapshots `read_chat_session`, qui ne les exposent pas.

## Prompt enfant (forme exécutée)

Le prompt contenait, dans cet ordre : identité du Skill et chemin d'installation ; contraintes absolues (lecture seule des racines skills, fixture sous `~/.qoder/tmp/skill-acceptance-<horodatage>`, aucun `git push`, aucune modification du clone partagé, aucun accès réseau ni secret, `py -3 -B`, `.py` temporaire au lieu de `py -3 -c`, ne rien corriger) ; procédure en 9 étapes ; contrôle d'intégrité par SHA-256 avant/après ; format de rapport ≤ 400 mots avec code de retour par étape et verdict.

L'étape 8 demandait de localiser le JSONL « le plus récemment modifié ». L'enfant a dû corriger cette consigne : le fichier le plus récent n'était pas le sien.

## Résultats de l'enfant

| Étape | Résultat mesuré |
|---|---|
| Chargement | « Launching skill: » seul ; injection prouvée à l'étape 8 |
| Fixture | copie de `inventory-installed-skills`, 13 093 B, SHA `24a67513…` |
| `inspect` | RC 0 — ligne 3, 934 car., `quote_style: "`, LF, sans BOM, corps 165 lignes |
| `anchors` | RC 1 attendu — ancre réelle `count: 1`, absente `count: 0`, `unique: false` |
| dry-run | RC 0 — `dry_run: true`, `new_len: 961`, SHA inchangé, aucun `.bak` |
| apply | RC 0 — 12 invariants vrais, SHA `1ddb5551…`, sauvegarde de SHA égal à l'original |
| restauration | SHA revenu à `24a67513…` |
| QA | PASS 9/0/0 aux trois états, `Files (2)` |
| propagation | RC 0 — `INJECTION_OK_LISTING_OK`, `dir_matches: true`, `body_matches: true`, `listing_status: ok`, `panel: unverified_manual` |
| nettoyage | répertoire supprimé, aucun `__pycache__` |

Deux codes de retour ont été écartés par l'enfant après vérification : `RC=2` provenait d'un `ls` final sur le dossier de sauvegarde absent en dry-run, et l'écart `description_len: 934` / `disk_description_chars: 963` séparait la fixture de l'installation.

## Identification du JSONL

Tri par mtime décroissant et comptage des lignes contenant `Base directory for this skill:` :

| mtime epoch | Session | Lignes d'injection |
|---|---|---|
| 1793104220.799 | `55f63550-7c8d-4f9e-b0a9-e73686cc2765` | 0 |
| 1793104217.682 | `db72d65b-e96e-58e2-aa0d-611061b3d5d6` | 4 |
| 1793104200.171 | `4ce15155-ee0c-4859-8bbd-8c44384aa5b3` | 6 |

Le fichier le plus récent appartenait à une autre session. Seul le comptage par session, recoupé avec l'ID fourni par `create_chat_session`, désigne le bon fichier.

## Contrôle indépendant du parent

- `SKILL.md` de l'installation : `37da07b6…`, 18 355 o, inchangé après le test.
- `__pycache__` : 0.
- Répertoires `skill-acceptance-*` résiduels : 0 (`temp_removed`).
- Aucune écriture du parent dans l'installation pendant le tour enfant.
- Archive `main` et installation restées identiques (`0cc95ec` au moment du test).

## Limites

- Branches d'erreur non exercées par ce protocole : candidat > 1024, sauvegarde interne au Skill, `--expect-sha256` incohérent, fins de ligne mixtes.
- Couche « panneau client » non vérifiée : `panel: unverified_manual`.
- Les valeurs ci-dessus proviennent des sorties d'outils des deux sessions ; aucune n'a été reprise d'un résumé tiers.
