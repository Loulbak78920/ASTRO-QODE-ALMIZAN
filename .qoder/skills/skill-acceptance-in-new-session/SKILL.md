---
name: skill-acceptance-in-new-session
description: "Faire accepter un Skill installé par une session Qoder indépendante : rédiger un prompt auto-suffisant avec une nonce unique, interdisant toute écriture sous les racines skills et imposant une fixture copiée hors installation (dossier égal au name), lancer create_chat_session en callbackMode supervise, suivre par callback puis des wait_chat_sessions bornés et read_chat_session (turnLimit 1, includeToolOutputs), puis refaire côté parent le contrôle d'intégrité (SHA-256, fichiers, __pycache__, résidu de fixture) et rendre un verdict qui sépare le mesuré du rapporté. Pièges figés : JSONL enfant localisé par nonce puis ID, seules injections isMeta, jamais le mtime, code de retour parasite, deux timeouts non concluants, valeur inventée. Utiliser pour tester un Skill dans une nouvelle session ou revérifier un rapport enfant. 中文触发：新会话验收、子会话测试 Skill、独立会话报告、注入条数定位 JSONL、父会话复验。English: acceptance test in a new session, delegate a skill test to an independent conversation, verify child session report."
---

# Accepter un Skill dans une session indépendante

## Objectif

Faire exécuter la procédure d'un Skill installé par une session Qoder sans historique, sur une fixture jetable, puis vérifier côté parent que le rapport de l'enfant est exact et que l'installation n'a pas bougé.

## Quand l'utiliser

- l'utilisateur demande « tester le Skill dans une nouvelle session » ou une acceptation par un tiers ;
- un rapport de session enfant doit être revérifié avant d'être présenté comme acquis ;
- on veut prouver que la doc d'un Skill est suivie par un agent qui ne l'a jamais lu.

## Quand ne pas l'utiliser

| Situation | Renvoi |
|---|---|
| prouver le binding d'une injection dans la session courante | `verify-skill-runtime-binding` |
| prouver que le corps injecté est la dernière version disque | `verify-injected-skill-body-freshness` |
| tester un harnais de publication hors production | `tester-publication-isolee-skill` |
| contrôle statique après écriture | `skill-file-qa` |
| rejouer des fixtures documentées d'une référence | `replay-skill-reference-fixtures` |
| cible en cours d'écriture par une autre session | `audit-skill-during-live-creation` |
| écriture concurrente dans le paquet | `skill-update-concurrency-safe` |

## Règles non négociables

1. L'installation est en lecture seule : aucune écriture sous une racine skills, ni par le parent ni par l'enfant.
2. Toute étape destructive se fait sur une copie sous `~/.qoder/tmp/acceptance-<horodatage>/`, hors installation.
3. Le nom du dossier de fixture reste égal au `name` du frontmatter, sinon `skill-file-qa` échoue sur « name matches directory ».
4. Le prompt enfant est auto-suffisant : la session enfant ne reçoit aucun historique. Ne jamais lui demander de créer une autre session.
5. Le prompt interdit : écriture dans les racines skills, `git push`, modification du clone partagé, accès réseau, secrets, correction du Skill.
6. Le parent ne modifie pas l'installation pendant le test ; toute écriture invaliderait la baseline de l'enfant.
7. `create_chat_session` prouve la création et le dispatch, jamais la fin du travail.
8. Une session enfant peut dépasser deux attentes de 60 s sans prompt de permission : suivre par callback `supervise`, ne pas conclure d'un timeout.
9. Le JSONL de l'enfant se localise par la nonce inscrite dans le prompt — l'enfant ne connaît pas son `sessionId` — puis, côté parent, par l'ID de session ; jamais par le mtime (le fichier le plus récent est souvent une autre session). Une injection authentique est un message `user` avec `isMeta` contenant « Base directory for this skill: » : un `grep -c` brut est auto-référentiel, car le prompt, le raisonnement et les motifs de recherche citent la phrase.
10. Un code de retour mesuré sur une commande accessoire (un `ls` final) n'est pas le code de retour de l'étape.
11. Le rapport enfant est une pièce à conviction, pas une preuve : le parent refait l'empreinte, la liste de fichiers et le scan `__pycache__`.
12. Le verdict sépare explicitement « mesuré par le parent », « rapporté par l'enfant » et « non exécuté ».

## Procédure

### 0. Préflight

Figer l'empreinte de l'installation et la QA de référence avant de créer quoi que ce soit.

```bash
SKILL_DIR="$HOME/.qoder/skills/<skill-name>"
TMP="$HOME/.qoder/tmp/acceptance-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$TMP"
SNAP_TOOL="$HOME/.qoder/skills/skill-acceptance-in-new-session/scripts/acceptance_snapshot.py"
py -3 -B "$SNAP_TOOL" snapshot "$SKILL_DIR" > "$TMP/snapshot-before.json"; echo "snapshot_rc=$?"
py -3 -B "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$SKILL_DIR" --workspace "$PWD"
```

Consigner : `skill_sha256`, `file_count`, liste des fichiers, `pycache_count` (attendu 0), `RESULT` de la QA. Vérifier aussi qu'aucun Skill de même nom n'est installé au niveau projet.

### 1. Rédiger le prompt enfant

Copier ce modèle et remplacer les valeurs entre chevrons. Générer une nonce unique (`ACCEPTANCE-NONCE-<horodatage>-<4 hex>`) et l'inscrire dans le prompt : elle permet à l'enfant comme au parent de retrouver le bon JSONL. Le bloc de contraintes et le format de rapport sont ceux qui ont produit un rapport exploitable.

```text
Test d'acceptation indépendant du Skill installé `<skill-name>` (installation : <chemin absolu de l'installation>).
Nonce d'identification de cette session : `<NONCE>` — recopie-la telle quelle dans tes recherches.
Tu dois l'utiliser tel que documenté et vérifier que le comportement réel correspond à sa doc, SANS modifier l'installation.

CONTRAINTES ABSOLUES
- N'écris jamais dans <racine skills> : lecture seule. Tous les essais se font dans un répertoire jetable <TMP>/fixture.
- Aucun git push, aucune modification des clones partagés, aucun accès réseau, aucun secret.
- Windows/Git Bash : utiliser `py -3 -B` (jamais `python`). Pour du Python inline contenant des chemins Windows,
  écrire un .py temporaire hors du Skill au lieu de `py -3 -c`.
- Ne corrige rien dans le Skill : tu observes et tu signales.

PROCÉDURE
1. Charge le Skill `<skill-name>` via l'outil Skill, puis suis son SKILL.md.
2. Fixture : copie <skill de référence> vers <TMP>/fixture/<nom-copie> ; le nom du dossier doit rester égal au `name`.
3. <étape 1 propre au Skill, commande exacte>
4. <étape 2 propre au Skill, commande exacte>
5. <étape destructive, avec sauvegarde hors Skill, puis restauration>
6. Lance skill-file-qa sur la copie : `py -3 -B <validate_skill.py> <copie> --workspace <ton cwd>`.
7. Propagation : tu ne connais pas ton `sessionId`. Localise TON JSONL par la seule nonce `<NONCE>`
   (`grep -l <NONCE> <projets>/*.jsonl`), jamais par le mtime. Compte ensuite les injections authentiques :
   les messages `user` avec `isMeta` contenant « Base directory for this skill: » ; un `grep -c` brut est
   auto-référentiel, car le prompt et tes propres motifs citent la phrase. Puis lance le contrôle de
   propagation du Skill s'il existe, sinon écris « propagation non exécutée » avec la raison et ces deux
   mesures (chemin du JSONL, injections authentiques).
8. Supprime ton répertoire jetable et vérifie qu'aucun __pycache__ ni .pyc n'a été créé dans l'installation.

CONTRÔLE D'INTÉGRITÉ
Relève le SHA-256 de <SKILL.md de l'installation> avant et après : il doit rester <sha attendu>.

RAPPORT FINAL (≤ 400 mots, en français)
- Une ligne par étape : PASS/FAIL, code de retour exact de l'étape, champs JSON clés observés.
- Tout écart entre la doc du Skill et le comportement réel (option, code de retour, clé de sortie, verdict).
- Verdict global ACCEPTÉ / ACCEPTÉ AVEC RÉSERVES / REFUSÉ, et l'état final de l'installation (SHA-256).
N'invente aucune valeur : si une étape n'a pas pu être exécutée, écris-la comme non exécutée et explique pourquoi.
```

### 2. Créer la session enfant

Lire les schémas avec `mcp_get` pour `mcp__builtin__create_chat_session`, puis créer la session avec `callbackMode: "supervise"` et le prompt complet. Consigner le `sessionId` retourné.

### 3. Suivre sans bloquer

Le callback `supervise` notifie la fin de tour ; des `wait_chat_sessions` de 60 s au plus servent de filet. Deux `timeout` consécutifs n'autorisent pas à conclure : la fin peut n'arriver qu'à l'appel suivant (mesuré : 60,04 s puis 60,47 s en `timeout`, `turn_completed` au troisième appel après 11,08 s). Entre deux attentes, `read_chat_session` avec `turnLimit: 1` et `includeToolOutputs: true` donne la progression et le rapport. Un `timeout` renvoie `runtimeState: running` avec un `activeTurnId` non nul : il travaille encore, et `pendingInteractionCount: 0` écarte seulement une demande de permission en attente.

Ne pas créer une seconde session pendant qu'une autre tourne. Ne pas interrompre sauf écriture hors fixture : dans ce cas `stop_chat_session` et verdict REFUSÉ.

### 4. Lire le rapport enfant

Exiger une ligne par étape avec le code de retour de l'étape. Rejeter comme non prouvée toute valeur sans commande associée. Un écart doc/comportement doit citer l'option, le code ou la clé en cause.

### 5. Contrôle indépendant du parent

```bash
py -3 -B "$SNAP_TOOL" compare "$SKILL_DIR" --baseline "$TMP/snapshot-before.json" \
  --expect-skill-sha <sha attendu>; echo "compare_rc=$?"
find "$SKILL_DIR" -name __pycache__ -o -name '*.pyc' | wc -l
ls -d "$HOME/.qoder/tmp"/acceptance-* 2>/dev/null | wc -l
```

`compare` : code 0 = SAME, 1 = CHANGED (fichiers ajoutés/retirés/modifiés, `__pycache__` apparu ou SHA attendu faux), 2 = erreur d'environnement. Un `CHANGED` interdit le verdict ACCEPTÉ.

### 6. Verdict

| Verdict | Conditions |
|---|---|
| ACCEPTÉ | toutes les étapes PASS ou non exécutées avec raison valable ; `compare` SAME ; zéro `__pycache__` ; fixture supprimée ; écarts doc listés |
| ACCEPTÉ AVEC RÉSERVES | branches d'erreur non exercées, écart doc mineur, ou couche non mesurée (panneau client) |
| REFUSÉ | comportement contredisant la doc, installation modifiée, valeur inventée, écriture hors fixture |

### 7. Nettoyage

Supprimer `$TMP` et vérifier l'absence de résidu `acceptance-*`. Supprimer les `__pycache__` créés, uniquement s'ils sont imputables à ce test.

## Contrat des outils MCP

| Outil | Ce qu'il prouve | Ce qu'il ne prouve pas |
|---|---|---|
| `create_chat_session` | création et dispatch, `sessionId` valide | que le travail est fait |
| `wait_chat_sessions` | fin de tour, état `ready`/`waiting-user`, `activeTurnId` | l'acceptation du travail |
| `read_chat_session` | messages, révisions, sorties d'outils bornées | le contenu d'un tour futur ou tronqué |

Contraintes de `wait_chat_sessions` : `sessionIds` accepte 1 à 8 conversations mais jamais la session courante, refusée explicitement car son tour ne pourrait pas se terminer ; `timeoutMs` va de 0 à 60000, avec 30000 par défaut ; `needs_attention` signale une décision humaine à remonter, sans y répondre à sa place.

## Pièges vérifiés

| Piège | Fait observé | Réflexe |
|---|---|---|
| JSONL choisi par mtime | le plus récent (`55f63550…`) avait 0 injection ; la session enfant (`db72d65b…`) en avait 4, le parent 6 | filtrer par nonce (enfant) ou ID (parent), puis compter les seules injections `isMeta` |
| nom de fixture différent du `name` | `skill-file-qa` échoue sur « name matches directory » | copier en conservant le nom du dossier |
| code de retour d'une commande accessoire | un `ls` sur un dossier de sauvegarde absent a rendu `RC=2` après un dry-run réussi | demander le code de l'étape, pas du script entier |
| dry-run sans dossier de sauvegarde | le dossier `--backup-dir` n'est créé qu'avec `--apply` | ne pas conclure à un échec |
| « Launching skill » seul | ne contient ni chemin ni corps | renvoyer à `verify-skill-runtime-binding` |
| deux attentes insuffisantes | deux `timeout` consécutifs (60,04 s et 60,47 s), `pendingInteractionCount: 0`, puis `turn_completed` au troisième appel après 11,08 s | garder des attentes de 60 s comme filet et ne jamais conclure d'un timeout |
| injections comptées par `grep` brut | 1 injection authentique (`isMeta`) mais 19 lignes contenant la phrase, dont le prompt, le raisonnement et les motifs de recherche | compter les messages `user` avec `isMeta`, pas les occurrences brutes |
| compteurs enfant divergents | 4 sentinelles mais 5 lignes `grep`, dont 1 dans la description | demander la réconciliation, pas un écart doc |
| fixture contre installation | `description_len: 934` (copie) contre `disk_description_chars: 963` (installation) | préciser le chemin mesuré dans chaque étape |

## Checklist finale

- [ ] Préflight consigné : SHA-256, `file_count`, `pycache_count`, RESULT de QA.
- [ ] Prompt enfant relu : nonce inscrite, contraintes absolues, chemin de fixture, `py -3 -B`, interdiction d'écrire dans les racines skills.
- [ ] `create_chat_session` en `supervise`, `sessionId` consigné.
- [ ] Progression suivie sans conclure d'un timeout ; aucune seconde session créée.
- [ ] JSONL enfant retrouvé par la nonce, injections authentiques comptées en `isMeta`.
- [ ] Rapport enfant lu avec codes de retour par étape ; valeurs inventées écartées.
- [ ] `compare` SAME avec le SHA attendu ; zéro `__pycache__`.
- [ ] Fixture supprimée, résidus `acceptance-*` absents.
- [ ] Verdict et écarts consignés, en séparant mesuré et rapporté.

## Ressources

- `scripts/acceptance_snapshot.py` : `snapshot` / `compare`, JSON ASCII, codes 0/1/2, lecture seule.
- `references/cas-acceptation-2026-10-27.md` : chronologie, prompt utilisé, résultats enfant, comptes d'injections.

## Skills liés

`skill-file-qa`, `verify-skill-runtime-binding`, `verify-injected-skill-body-freshness`, `audit-skill-during-live-creation`, `skill-update-concurrency-safe`, `tester-publication-isolee-skill`, `replay-skill-reference-fixtures`, `write-skill-evidence-case-study`.
