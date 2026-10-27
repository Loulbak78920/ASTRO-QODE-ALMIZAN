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

Tri par mtime décroissant et comptage brut des lignes contenant `Base directory for this skill:` au moment du tri :

| mtime epoch | Session | Lignes contenant la phrase |
|---|---|---|
| 1793104220.799 | `55f63550-7c8d-4f9e-b0a9-e73686cc2765` | 0 |
| 1793104217.682 | `db72d65b-e96e-58e2-aa0d-611061b3d5d6` | 4 (5 après la fin du tour) |
| 1793104200.171 | `4ce15155-ee0c-4859-8bbd-8c44384aa5b3` | 6 (15 après la fin du tour) |

Le fichier le plus récent appartenait à une autre session. Seul le comptage par session, recoupé avec l'ID fourni par `create_chat_session`, désigne le bon fichier.

Recomptage après la fin des tours, en ne retenant que les enregistrements `type == "user"` avec `isMeta == true` : chaque JSONL ne contient qu'une injection authentique — `db72d65b…` 5 lignes brutes / 1 `isMeta`, `4ce15155…` 15 / 1, `03ce5a9c…` 19 / 1, `a973aeef…` 30 / 1. Les valeurs 4 et 6 du tableau sont des occurrences brutes relevées en cours de tour, pas des injections.

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

## Deuxième cas — `inventory-installed-skills` (même jour, autre session)

### Sources

- Session parente `6dcf818a-7b05-443d-acf0-948290b4738f`.
- Session enfant `573de6a4-8718-52b1-a718-c39affec8f40`, un seul tour, `callbackMode: supervise` ; `turn_completed` à 12:55:07.172Z (callback), dernière ligne du JSONL enfant 12:55:06.3Z.
- Cible : `inventory-installed-skills`, 13 093 B, SHA-256 `24a675137f77bcb7a53340584a1ba717c9cc30e0a34fc63a2b35a1ae34218b67`, 2 fichiers, QA `PASS` 9/0/0.

### Rapporté par l'enfant (9 étapes, toutes PASS)

| Étape | Valeur |
|---|---|
| Énumération | `local total: 85 = 83 user + 2 project`, `duplicates none`, `anomalies 0` |
| `--builtin` | 4 déclarés, hors total local |
| Branche B | snapshot 46 337 o, `unchanged: 85`, `no drift` |
| Échec documenté | `--snapshot` + `--compare` sur fichier absent : RC 2, rien écrit |
| Groups | RC 0 puis 1 : `## Groups (validated: 85 assigned = 85 local total)`, puis `unknown skill in group 'project-level': skill-qui-nexiste-pas` |
| QA sur copie | `PASS` 9/0/0, `Files (2)` |
| Propagation | non exécutée (aucun script de propagation dans la cible) |
| État final | SHA `24a67513…`, 0 `__pycache__` |

### Mesuré par le parent

- `compare` non pipé : `verdict: CHANGED`, RC 1, `modified: ["SKILL.md"]`, `pycache_added: []`.
- Attribution : la session `39a147b6-295f-455f-93d4-a13b6c657601` a fait 10 `Edit` sur `inventory-installed-skills/SKILL.md` entre 12:55:09.902Z et 12:56:13.803Z ; la somme de leurs deltas UTF-8 vaut +2 892 o, soit exactement 15 985 − 13 093, sans octet inexpliqué.
- Enfant : 0 `Write`/`Edit` vers l'installation ; son JSONL s'arrête 2,73 s avant la première écriture étrangère.
- Script de la cible inchangé : `262998a35c11a7e0c89688d539a48b8d79230cc5af394b1ef4fb4c9bab8a5936`.
- Nettoyage : TEMP supprimé, `acceptance-*` résiduels 0, `__pycache__` 0.

### Verdict

**ACCEPTÉ AVEC RÉSERVES** pour la version testée `24a67513…`. Le `CHANGED` interdit `ACCEPTÉ` ; l'attribution prouve que ni l'enfant ni le parent n'ont écrit dans l'installation, donc pas `REFUSÉ`.

### Réserves

1. Contrôle d'intégrité parent non concluant : réécriture tierce après la fenêtre enfant.
2. Quatre écarts doc ↔ réel, vérifiés dans `scripts/inventory_skills.py` de la cible : ligne `built-in/plugin` conditionnelle (`if builtin:` l. 286) ; titre `## Groups (validated: …)` au lieu de la formulation « assigned = local total » (l. 310) ; règle « snapshot hors racines skills » documentaire seule, seul `target.parent` étant testé (l. 406) ; comptage brut du marqueur instable dans un JSONL en écriture (4→7→15), un seul message commençant par le marqueur.
3. Branches d'erreur non exercées : `--project-root` invalide, PyYAML absent, fichier `--groups` illisible.
4. **Versionnage des deux côtés ; la contrainte `nonce` n'a pas été appliquée.**
   - a) Cible : la version testée `24a67513…` (13 093 o) a été remplacée sur disque par `f1128544…` (15 985 o, 186 lignes) par les 10 `Edit` de `39a147b6…`.
   - b) Protocole : `SKILL.md` de ce Skill est passé de `ebd54fc8…` (12 766 o, version réellement appliquée par ce run) à `77606422…` (14 159 o, 6 `Edit` de `a973aeef…` entre 12:58:19Z et 12:58:40Z, archivée au commit `930f1ea`), puis à **`0f1f11bc…` (16 447 o, mtime 2026-10-27T14:11:45+01:00)** après 14 `Edit` de `0d4a13d8…` entre 13:05:34Z et 13:11:45Z. Les états `9e8741ea…` (14 210 o), `9c7d0fcf…` (16 416 o) et `2721a0d7…` (16 438 o) n'étaient que des intermédiaires de cette série et ne doivent pas être cités comme état courant.
   - c) La version courante impose une nonce unique `ACCEPTANCE-NONCE-<horodatage>-<4 hex>` inscrite dans le prompt enfant, qui sert à localiser le JSONL de l'enfant — l'enfant ne connaît pas son `sessionId` — et à ne compter que les injections `isMeta`. Ce run a identifié le JSONL par `sessionId` et compté le marqueur brut, d'où l'instabilité relevée en réserve 2. **Le verdict valide le protocole sans nonce ; un run sous nonce reste à faire pour couvrir la version courante.** Le run `a973aeef…` (cas ci-dessous) a utilisé une nonce avec la version antérieure et a montré qu'elle ne suffit pas seule, car elle figure aussi dans le JSONL du parent ; la version courante n'a pas encore été rejouée.

## Cas du run sous nonce — `inventory-installed-skills` (12:45–12:52)

### Sources

- Session parente `a973aeef-bbbe-408d-b634-e1620fe583e8` ; enfant `03ce5a9c-923c-510c-a849-e614d27e5c47`, un seul tour, `callbackMode: supervise`.
- Nonce `ACCEPTANCE-NONCE-20261027T124546Z-9c1f`, répertoire `~/.qoder/tmp/acceptance-20261027T124534Z`.
- Cible : `inventory-installed-skills`, 13 093 o, SHA-256 `24a675137f77bcb7a53340584a1ba717c9cc30e0a34fc63a2b35a1ae34218b67`, 2 fichiers.

### Mesuré par le parent

- Attentes : `timeout` (révision 21, `pendingInteractionCount: 0`), `timeout` (révision 38, même `activeTurnId`), puis `turn_completed` au troisième appel (révision 48, `ready`, `activeTurnId: null`).
- JSONL enfant : 163 lignes ; 19 lignes contiennent la phrase, **1 seule est une injection authentique** (`type == "user"`, `isMeta == true`, ligne 15).
- La nonce figure dans le JSONL enfant **et** dans celui du parent rédacteur : l'enfant s'est distingué par la nonce et une commande propre à sa branche a, pas par la première correspondance.
- `snapshot-before.json` : 609 o, resté à la racine de `$TMP` après le nettoyage de l'enfant.
- `acceptance_snapshot.py compare` : SAME, code 0 ; `__pycache__` : 0.
- Écritures sous les racines skills attribuées à des sessions tierces (`f95bd156`, `a47d9532`, `6dcf818a`) ; l'enfant n'a rien écrit dans l'installation.

### Rapporté par l'enfant, requalifié par le parent

- Neuf étapes PASS, propagation non exécutée (aucun script de propagation dans la cible).
- Deux « écarts doc » signalés, tous deux **sans fondement** après lecture de la cible : la ligne `stability:` est une synthèse à rédiger par le répondant, pas une sortie du script. Aucun n'entre dans le verdict.

### Verdict

**ACCEPTÉ** pour la version testée `24a67513…`, les deux écarts enfant écartés après requalification. Ce run a motivé les corrections du protocole appliquées à 12:58 : nonce, comptage `isMeta` seul, et interdiction de conclure d'un timeout.
