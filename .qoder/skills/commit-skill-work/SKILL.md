---
name: commit-skill-work
description: "Committer modifications de Skill ou dépôts imbriqués (Windows) : localiser le vrai dépôt, séparer SESSION et préexistant, tests + skill-file-qa, paquet sans __pycache__ malgré PASS, empreintes de toutes les ressources (Fingerprint = SKILL.md), ajout par chemins explicites, artefacts régénérés séparés, push seulement sur demande, résolution runtime par invocation ; rejouer parité, QA, SHA-256 et invocation après écriture ; archives obsolètes signalées sans republication. Pour « commit », « git commit », commit concurrent, `nothing to commit`, HEAD avancé entre revue et commit, Skill hors dépôt, init + remote partagé + branche skill/<nom>, LOCAL-ONLY, commit racine, prémisse de périmètre changée, activité par empreintes disque, __pycache__, OID blob/source, core.autocrlf=true, résolution runtime sans /skills reload. 中文触发：提交 Skill、git commit、嵌套仓库、并发提交、nothing to commit、审阅后 HEAD 前进、默认不 push、重载验证、运行时可解析性、文件指纹、索引 blob 校验、autocrlf、最终写入后重验、QA PASS 含缓存、归档过期不重发、LOCAL-ONLY、init+共享远程 skill/<nom>、根提交、范围前提变化、按指纹判活动。"
---

# Committer les modifications d'un Skill ou d'un dépôt imbriqué

## Objectif

Identifier le dépôt qui contient réellement les fichiers modifiés, committer uniquement le périmètre voulu et ne jamais pousser sans demande explicite. La racine du projet n'est pas forcément un dépôt : les dépôts utiles sont souvent imbriqués ou propres à un Skill.

## Déclencheurs

- demande « commit », « git commit », « versionne ce Skill » ;
- Skill utilisateur sous le dossier user-level des skills, hors de tout dépôt ;
- plusieurs dépôts imbriqués et périmètre ambigu ;
- tests qui réécrivent des fichiers générés après le commit ;
- demande de push, de « merge dans `main` » sans ancêtre commun, ou dépôt de Skill sans `origin` ;
- vérification de l'OID blob/source, ou avertissement `core.autocrlf` ;
- revalidation après une écriture tardive de `SKILL.md`, d'un script ou de la traduction ;
- `skill-file-qa` renvoie `RESULT PASS` alors que `Files (N)` contient un cache ;
- archive du Skill présente dans un autre dépôt après le commit ;
- `git status` vide alors qu'un commit est attendu (commit créé par une autre session) ;
- écriture concurrente entre la validation et le `git add`, ou manifeste d'empreintes divergent ;
- écritures concurrentes persistantes (source change encore toutes les 10–30 s pendant la validation), plan approuvé dont taille/mtime/SHA-256/lignes ont changé depuis la planification, ou plan approuvé déjà partiellement appliqué par une autre session ;
- dépôt local initialisé pour un Skill hors dépôt (LOCAL-ONLY), commit racine, ou prémisse de périmètre qui change en cours de flux ;
- mise à jour de la seule source, traduction laissée intacte (parité attendue en échec).

## Étape 1 — Localiser le dépôt réel

Partir d'un chemin absolu, toujours entre guillemets :

```bash
git -C "<chemin absolu>" rev-parse --show-toplevel
```

- `EXIT=128` avec `fatal: not a git repository` : ce dossier n'est pas un dépôt. Ne pas en déduire que la racine du projet l'est.
- Un chemin relatif ou non ASCII peut être résolu depuis un autre répertoire courant. Vérifier d'abord `test -d "<chemin>"`, puis passer le chemin absolu. Cas observé : `ASTRO-Q°ODE_SYSTEME` a échoué avec `fatal: cannot change to ...`.
- Énumérer les candidats quand la racine n'est pas un dépôt :

```bash
find "<racine>" -maxdepth 3 -name .git -type d
find "C:/Users/Administrateur/.qoder/skills" -maxdepth 2 -name .git -type d
```

- Inventaire en lecture seule, sortie ASCII, codes 0/1/2 :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/inspect_git_state.py" "<racine>" "C:/Users/Administrateur/.qoder/skills"
```

Le script interroge `rev-parse`, `status`, `diff`, `log` et `remote` sans modifier l'index, et signale les caches non suivis. Le script appartient à `commit-skill-work`, pas au Skill commité : `<dossier-skill>` peut ne contenir que `SKILL.md`. Le chemin doit rester absolu et pointer vers ce Skill ; depuis la racine du projet, `scripts/inspect_git_state.py` échoue avec `can't open file` (code 2).

## Étape 2 — Classer les changements

```bash
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --stat
git -C "<depot>" log --oneline -5
git -C "<depot>" ls-files --error-unmatch -- "<chemin>"
```

Classer chaque chemin en trois catégories : **SESSION** (produit par le travail en cours), **PREEXISTANT** (déjà modifié avant la session), **INCERTAIN**. Ne jamais inclure silencieusement un chemin PREEXISTANT ou INCERTAIN : demander confirmation avec la liste exacte. Ne pas inclure `__pycache__`, les fichiers `.pyc` ni les artefacts temporaires.

## Étape 3 — Choisir le dépôt cible

| Situation | Action |
|---|---|
| Dossier Skill hors de tout dépôt | proposer trois cibles mutuellement exclusives : (a) **LOCAL-ONLY** (aucun origin, aucun push) ; (b) dépôt existant ou archive `main` via `publier-skill-qoder-vers-depot-git` ; (c) init + remote partagé : lire `branch -vv`/`remote -v` des Skills voisins et `git ls-remote`, proposer les cibles, puis après accord `git init`, `git remote add`, push `skill/<nom>` ; ne pas présumer LOCAL-ONLY |
| Dossier situé dans un dépôt imbriqué | utiliser ce dépôt et confirmer avec `ls-files --error-unmatch` |
| Plusieurs dépôts touchés | un commit par dépôt et par sujet |
| Modifications préexistantes non liées | demander avant de les inclure |
| Dépôt de Skill avec `origin` partagé | pousser une branche dédiée `skill/<nom>`, jamais `main` sans accord ; un contenu vers `main` sans ancêtre commun suit `references/contenu-vers-main.md` |
| Dépôt sans `origin` | distinguer LOCAL-ONLY voulu de « remote partagé à découvrir » : `branch -vv`/`remote -v` des Skills voisins et `git ls-remote` révèlent la convention (`skill/<nom>` par Skill) ; avant de proposer une cible, sonder chaque URL candidate en lecture seule avec `git ls-remote --heads <url>` : ne retenir que `RC=0` et l'absence de `refs/heads/skill/<nom>` ; un candidat injoignable ou déjà occupé n'est pas une option exécutable ; demander la cible, ne pas deviner l'URL |

Réponse « TOUT » : reformuler une première fois avec des options mutuellement exclusives et la liste exacte des dépôts et fichiers. Si la deuxième réponse est encore « TOUT », ne pas poser une troisième question : exécuter la combinaison recommandée, la déclarer explicitement dans le rapport, et exclure toute action non listée ou non réversible (push, suppression, réécriture). `git init` reste possible seulement s'il figurait dans les options confirmées. Cas observé (2026-10-26) : deux « TOUT » successifs → dépôt local du Skill + commit sur `main` d'un clone local du dépôt public, sans branche dédiée redondante et sans push. La règle suivante sur les dépôts publics sans rapport reste prioritaire : aucun push vers `main`, aucun commit d'un Skill utilisateur dans un dépôt public sans rapport.

N'exécuter `git init` qu'après accord explicite. Ne pas modifier la configuration Git : vérifier `git config user.name` et `git config user.email`, sans les réécrire. Ne jamais committer un Skill utilisateur dans la branche `main` d'un dépôt public sans rapport. Après `git init`, lire la branche réellement pointée avec `git symbolic-ref --short HEAD` : sur un HEAD non né, `git rev-parse --abbrev-ref HEAD` échoue avec `fatal: ambiguous argument 'HEAD'` ; consigner aussi `init.defaultBranch` et la branche des dépôts voisins, sans renommer silencieusement. Pour un commit racine, l'ordre des OID est imposé : après `git add`, `git rev-parse ":<chemin-relatif>"` doit égaler `git hash-object --path=<chemin-relatif> <source>` ; `HEAD:<chemin-relatif>` n'existe qu'après le premier commit. Un dépôt **LOCAL-ONLY** n'a pas d'`origin` : ne pas demander d'URL et ne pas pousser ; c'est un cas distinct de « dépôt existant sans `origin` → demander l'URL ». Cas observé (2026-10-26) : dossier hors dépôt, `git init` → `INIT_EXIT=0`, `rev-parse --abbrev-ref HEAD` → `fatal: ambiguous argument 'HEAD'`, `symbolic-ref` → `refs/heads/master` ; `skill-file-qa` après init toujours `RESULT PASS`, `Files (2)` ; root commit `4b19c34` (2 fichiers), OID index et `HEAD` 2/2 MATCH, `autocrlf=true` avec `LF will be replaced by CRLF the next time Git touches it`. Cas observé (2026-10-26) : dossier hors dépôt, `TOP_RC=128` sans `origin` ; `branch -vv` des Skills voisins → `Loulbak78920/ASTRO-QODE-ALMIZAN` avec `skill/commit-skill-work` et `skill/mesure-cesium-133-geolocalisee`, `IMAM8MAHDI/qoder-skills` en archive `main` ; `ls-remote` → `main`, `master`, `skill/commit-skill-work` ; trois cibles proposées, l'utilisateur choisit la branche dédiée ; `git init` (`master`, `init.defaultBranch` non défini), `remote add`, manifeste/QA/invocation, root commit `55e2989` (2 fichiers, 375 insertions), push de `HEAD:refs/heads/skill/aligner-variantes-commande-skill` vers la branche dédiée, `ls-remote` = HEAD = `55e29897…`, statut propre, `RESULT NONE` (28 dépôts) ; upstream constaté ensuite : `master` suit `origin/skill/aligner-variantes-commande-skill` bien que les noms diffèrent — état ambigu que l'Étape 10 interdit désormais.

## Étape 4 — Vérifier avant de committer

### Avant d'écrire : ré-ancrer un plan approuvé

Un plan approuvé décrit le fichier au moment de sa rédaction, pas au moment de l'écriture. La preuve d'inactivité est le disque, pas l'état de session : avant chaque écriture, rééchantillonner la cible et la comparer au baseline consigné dans le plan. Exiger `size`, `mtime` et SHA-256 identiques sur ≥ 3 échantillons espacés (≥ 6 s), et 4 échantillons sur ≥ 20 s si le dossier bouge encore. `wait_chat_sessions`/`runtimeState` sont des indices auxiliaires : un timeout à `running` ou un texte d'assistant ne prouve ni écriture ni inactivité. Cas observé (2026-10-26) : deux attentes expirées à revision 95→105 (`running`, `lastAssistantText=null`) alors que 3 fichiers étaient stables depuis ~75 s ; inversement, un « rien écrit » peut précéder des écritures du même tour. Disque stable : ne pas bloquer sur l'état de session ; disque mobile : attendre ou geler un instantané. Pour nommer l'écrivain sans confondre une session en lecture avec l'auteur, scanner les JSONL de session (`<racine-projets>/<projet>/*.jsonl`) avec `scripts/find_writers.py` : retenir les `tool_use` `Write`/`Edit` dont `input.file_path` pointe dans le dossier du Skill, puis prendre le `timestamp` maximal par session ; `list_chat_sessions.updatedAt` et `runtimeState` ne datent pas la dernière écriture. L'attribution ne dit que *qui* écrit : la décision de continuer reste fondée sur les empreintes disque. Cas observé (2026-10-26) : écriture de 18:23:15 (locale) attribuée à `49d435d9`, sans aucun `Write`/`Edit` avant 18:30:41 ; les JSONL donnent `87644a66` jusqu'à `17:26:48Z`, alors que son `updatedAt` était figé à `17:22:01Z`.

```bash
stat -c '%s %y' "<fichier>"
sha256sum "<fichier>"
```

Répéter après au moins 2 secondes et exiger des sorties identiques. Si la taille, le mtime ou le SHA-256 diffèrent du baseline, ne pas appliquer le plan tel quel : relire le fichier courant, retrouver chaque ancre par son texte exact (jamais par un numéro de ligne), puis appliquer des `Edit` minimaux. Un extrait de fichier restauré après une compaction de contexte n'est pas le disque : ses numéros de ligne et son texte peuvent être périmés ; relire le fichier courant et ré-ancrer par texte exact avant de remesurer `description` et lignes du corps. Préserver les ajouts concurrents et les adopter sans reformulation ; avant d'éditer, classer chaque point du plan d'après les octets courants, jamais d'après un message de session, dans la matrice de couverture `CURRENT` (déjà présent à l'identique), `ALREADY_APPLIED` (couvert par d'autres octets), `PARTIAL` (partiel), `ABSENT` (manquant), `CONFLICT` (contredit) ; n'éditer que `ABSENT` et `PARTIAL` et s'arrêter sur `CONFLICT` ; ne pas restaurer une sauvegarde ni réécrire le fichier entier. Après chaque écriture concurrente, rejouer le manifeste, la parité, `skill-file-qa` et l'invocation sur les octets finaux : aucun `PASS` antérieur n'est réutilisable. Si une ancre a disparu ou entre en conflit avec un ajout concurrent, s'arrêter et demander au lieu de deviner. Si le fichier bouge encore pendant cette vérification, ne pas écrire : attendre une fenêtre stable ou appliquer la section « Écriture concurrente : valider un instantané gelé ». La validation obtenue sur l'ancien baseline est caduque : pour une mise à jour de `SKILL.md`, compter d'abord les lignes du corps (après le frontmatter) ; à 499 lignes (limite 500), fusionner la règle dans un paragraphe ou une cellule existants, jamais dans un nouveau titre, une ligne de tableau ou un élément de checklist, puis répliquer la règle dans la traduction ; mesurer aussi la `description` du frontmatter par script (`len`), jamais à l'estimation, avant d'ajouter ou de reformuler des déclencheurs : ≤ 1024 caractères ; au-delà, compresser les formulations redondantes sans supprimer de déclencheur clé et remesurer à chaque passe ; exiger ensuite que `skill-file-qa` affiche `PASS description: single line, N chars` avec le N du fichier final (mesures observées le 2026-10-26 : 1177 → 1067 → 1030 → 1021 en quatre passes, QA `1021 chars`) ; revalider les octets finaux (parité si traduction, `skill-file-qa`, SHA-256, invocation). Cas observé (2026-10-26) : 498 → 499 lignes par fusion d'un paragraphe et ajout d'une seule ligne de tableau, QA 9/0/0, parité 8/8.

Cas observé (2026-10-26) : plan établi sur `SKILL.md` `8fc96497…` (28 077 B) et `skill-zh.md` `1944a214…` ; à l'écriture, `SKILL.md` était `855b791a…` (28 112 B) et `skill-zh.md` `37c02eb5…` ; relecture puis 5 `Edit` minimaux sur le texte courant, ajouts concurrents conservés ; état final `SKILL.md` `23d5ac1d…` (30 812 B). Aucune sauvegarde restaurée, aucune réécriture intégrale. Cas observé (2026-10-26) : le plan de l'Étape 10 recoupait `9fbfe69a` (sonde de cible et contrôle de `main` déjà écrits, donc `ALREADY_APPLIED`) ; seuls le retrait de `-u` et la preuve générique post-push restaient `ABSENT` ; `9944e101` a ensuite modifié l'Étape 11, invalidant le `PASS` et imposant un `diff` puis un rejeu complet, sans perdre les ajouts des deux sessions.

Lancer la suite du dépôt avec son entrée documentée. Dans ce projet, la suite observée est `tests.test_suite_complete` (11 tests) :

```bash
py -3 -m unittest tests.test_suite_complete
```

Pour un Skill, lancer `skill-file-qa` sur le dossier réel :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<dossier-skill>" --workspace "<racine-espace>" --stable-seconds 2
```

Exiger la sortie `RESULT PASS` avant de committer. Consigner les résultats réels. Avant de citer une session comme preuve ou d'affirmer qu'elle a commité ou poussé, consigner à l'instant du snapshot son `runtimeState`, sa `revision` et le dernier tour de l'assistant : `error`/`failed` ou tour vide signifie que la demande n'a pas été exécutée dans ce tour ; ne pas conclure depuis le texte utilisateur ni depuis la présence des fichiers, mais prouver l'arrivée du travail par `log`/`status`/OID et attribuer le commit à la session qui a écrit (scan JSONL). Cas observé (2026-10-26) : `commit these two files` s'est terminé `failed` sans texte ni outil ; le commit concurrent `ea5da2b` contenait déjà la modification. Une sortie `read_chat_session` tronquée est persistée sur disque : la relire avec `py -3` et `PYTHONIOENCODING=utf-8` (sans cela, un premier passage a échoué en `cp1252`). Ne pas committer si un test échoue : corriger d'abord. Une réécriture d'un « Cas observé » est une preuve, pas une reformulation libre : vérifier d'abord le dépôt cité (`config`, `branch -vv`, `log`, `ls-remote`) ; ne jamais présenter comme jamais lancée une commande réellement exécutée (`push -u` réécrit en « push sans `-u` » alors que l'upstream enregistré pointe ailleurs) ; retirer seulement la commande ou le paramètre en cause, conserver le résultat vérifiable et le qualifier d'état désormais interdit ; répliquer dans la traduction, rejouer parité (identifiants et nombres changent), QA, manifeste et invocation, puis prouver `grep -c "<token>"` = 0 dans les deux fichiers.

`RESULT PASS` ne prouve pas que le paquet est propre : le validateur peut lister un cache et passer. Cas observé (2026-10-26) : après un contrôle `py_compile`, `Files (4)` incluait un fichier `.pyc` de cache dans `scripts/`, avec `PASS layout: 4 file(s)` et `RESULT PASS`. Avant de committer, inspecter la ligne `Files (N)` et lancer :

```bash
find "<dossier-skill>" \( -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' \) -print
```

Si la sortie n'est pas vide, supprimer uniquement les caches créés par la session (`rm -rf "<dossier-skill>/scripts/__pycache__"`), puis relancer `skill-file-qa` et exiger que `Files (N)` corresponde à l'inventaire sans cache :

```bash
find "<dossier-skill>" -type f \( -name "SKILL.md" -o -path "*/scripts/*" -o -path "*/references/*" \) ! -path "*/__pycache__/*" ! -name "*.pyc" ! -name "*.pyo" | sort
```

Pour un cache préexistant, demander avant de le supprimer. Un `PASS` obtenu avec un cache dans la liste ne vaut pas pour le paquet stagé. S'il est conservé, ne pas le supprimer pour faire coïncider `Files (N)` avec l'index : figer un instantané hors du Skill et du dépôt **sans cache**, y lancer `skill-file-qa` (`Files (N)` = inventaire du paquet), prouver `instantané == live`, puis n'indexer que les fichiers modifiés (Étape 4). Cas observé (2026-10-26) : cache `__pycache__` préexistant non suivi sous `scripts/`, paquet de 3 fichiers, 2 fichiers modifiés ; QA sur instantané `Files (3)`, `RESULT PASS` 9/0/0, `SNAPSHOT_MATCH`, index 2/2 d'OID égaux à la source, `git status` post-commit propre hors `?? scripts/__pycache__/`.

Le `Fingerprint` de `skill-file-qa` ne couvre que `SKILL.md`. Cas observé : après deux modifications de `scripts/inspect_git_state.py`, il est resté à `9901 bytes` avec le même SHA-256 ; seul un changement de `SKILL.md` l'a fait passer à `9917 bytes`. Relever donc les empreintes de toutes les ressources avant de committer :

```bash
find "<dossier-skill>" -type f \( -name "SKILL.md" -o -path "*/scripts/*" -o -path "*/references/*" \) ! -path "*/__pycache__/*" -print0 | xargs -0 sha256sum
```

Toute écriture postérieure à une validation annule la preuve, y compris une correction de `SKILL.md`, d'un script ou de la traduction. Cas observé : une invocation réussie, puis deux corrections de `SKILL.md` et de la traduction pour rendre `find` déterministe, ont rendu cette preuve obsolète ; parité, `skill-file-qa`, empreintes et invocation ont dû être rejoués sur la version finale. Ne pas conclure à l'intégrité du Skill à partir du seul `Fingerprint`.

Le manifeste de référence est enregistré **hors du dossier du Skill** immédiatement après la dernière écriture, puis comparé après les contrôles. Il couvre `SKILL.md`, `scripts/` et `references/` à l'exclusion des caches :

```bash
manifest="<chemin-hors-skill>/fingerprints-<nom-skill>.txt"
(
  cd "<dossier-skill>" || exit 2
  find . -type f \( -path './SKILL.md' -o -path './scripts/*' -o -path './references/*' \) \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) > "$manifest"
```

Ne pas placer ce fichier dans le dossier du Skill : il polluerait le paquet et, sous `references/` ou `scripts/`, s'auto-inclurait. Après les contrôles, recalculer la même liste et exiger un `diff` vide :

```bash
(
  cd "<dossier-skill>" || exit 2
  find . -type f \( -path './SKILL.md' -o -path './scripts/*' -o -path './references/*' \) \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) | diff -u "$manifest" - || { echo "FAIL: écriture pendant la validation"; exit 1; }
```

Le SHA-256 de `./SKILL.md` dans le manifeste doit égaler le `Fingerprint (final)` de `skill-file-qa` ; sinon QA ne porte pas sur cette version. Un manifeste absent ou un `diff` non vide interdit de conclure à une version validée.

Après la dernière écriture, rejouer les contrôles dans cet ordre, puis ne plus rien modifier :

1. Parité de traduction, si une traduction existe :

```bash
py -3 "<skills-root>/skill-doc-translation-parity/scripts/check_translation_parity.py" "<dossier-skill>/SKILL.md" "<dossier-skill>/references/<nom>-zh.md"
```

2. Scan des caches, puis `skill-file-qa` : exiger `RESULT PASS`, `Files (N)` égal à l'inventaire sans cache, et le `Fingerprint (final)` égal au `./SKILL.md` du manifeste.
3. Recalculer le manifeste et exiger un `diff` vide (voir ci-dessus).
4. Invocation réelle du Skill (Étape 11), puis recalculer le manifeste et exiger un `diff` vide.

Consigner le manifeste et les empreintes finales, puis les associer à la version validée. Une écriture après l'étape 4 impose de reprendre à l'étape 1. Ne jamais présenter un PASS obtenu avant la dernière écriture comme la validation du fichier actuel. La parité est structurelle (blocs de code, tableaux, titres, listes, identifiants, nombres) et ne prouve pas la qualité sémantique de la traduction. Un `RESULT FAIL` dont la seule ligne en échec est `FAIL inline tokens: missing=[…]`, alors que la source a aussi été modifiée, signale en général un identifiant protégé reformulé en prose dans la traduction (cas observé : `$N` remplacé par « ce littéral ») ; ce n'est ni une panne du script ni le périmètre partiel. Ne pas affaiblir le contrôle, ne pas modifier la source pour la faire correspondre : restaurer le token exact dans la phrase traduite, puis reprendre à l'étape 1 et rejouer parité, `skill-file-qa`, manifeste hors Skill et invocation. Si le `FAIL` inclut `extra=[…]` ou si les écarts de `missing` portent sur plusieurs occurrences (token cité dans plusieurs sections, exemple ajouté ou supprimé), ne pas corriger une seule phrase : extraire les tokens des deux corps avec la règle exacte du script (`INLINE_RE`, contenu entre backticks hors blocs de code, espaces retirés), compter leur `Counter`, puis ajouter chaque occurrence manquante et ramener chaque occurrence excédentaire au nombre de la source en reformulant la phrase en trop, sans modifier la source ; rejouer la parité. Cas observé : `branch -vv` 5 vs 4, `remote -v` 2 vs 1, `git ls-remote` 2 vs 1, `skill/<nom>` 5 vs 6 ; trois ajouts et une occurrence excédentaire retirée. Un `RESULT PASS` de QA ne compense pas ce `FAIL`.

### Périmètre partiel : source seule, traduction non modifiée

Si l'utilisateur n'autorise que le fichier source, ne pas modifier `references/<nom>-zh.md` pour rétablir la parité et ne pas traduire silencieusement. Lancer les deux contrôles et les rapporter séparément :

- `skill-file-qa` peut renvoyer `RESULT PASS` : il valide la structure du paquet, pas la parité.
- `check_translation_parity.py` renverra `RESULT FAIL` ; c'est le résultat attendu du périmètre partiel, pas une panne du script.

Détailler les écarts réels (nombre de blocs de code, séquence de titres, nombre d'éléments de checklist, identifiants et nombres manquants) et conclure : « source validée par QA, parité en échec, paquet non validé ». Ne jamais présenter un `RESULT PASS` non qualifié comme la validation du Skill complet. Un manifeste et des empreintes peuvent être consignés pour les octets courants, mais les étiqueter « source seule, parité en attente » ; l'invocation prouve la résolution runtime de la source, pas la parité. Pour clore l'écart, demander l'autorisation de répliquer les changements dans la traduction, puis rejouer parité et QA. Si la prémisse du périmètre change en cours de flux (un fichier d'abord exclu devient référencé, par exemple une nouvelle référence ajoutée à `SKILL.md`), s'arrêter et reconfirmer avant `git add`. Porte dure : `Files (N)` de `skill-file-qa` doit égaler l'inventaire du paquet sans cache après changement, jamais le seul ensemble indexé. Un commit est complet quand, après `git add`, `git diff --cached --name-only` égale `git diff HEAD --name-only` et que `git diff --name-only` est vide hors cache, puis qu'après le commit `git status --porcelain=v1` ne montre aucun fichier du paquet hors cache ; `Files (N)` n'égale l'index que si tous les fichiers du paquet ont changé, et une suppression indexée est déclarée. Pour un commit partiel déclaré (des changements du paquet restent hors du commit), `git diff --cached --name-only` est un sous-ensemble strict de `git diff HEAD --name-only` et `git status --porcelain=v1` liste les changements restants déclarés. Dans les deux cas, aucune indexation de chemin hors paquet et chaque OID indexé égale `git hash-object --path`. Ne jamais indexer un fichier inchangé pour faire coïncider `Files (N)` avec l'index, ni supprimer un cache préexistant ; valider l'instantané sans cache.

Cas observé (2026-10-26) : après mise à jour de la seule source, QA `RESULT PASS` (9/0, `Files (4)`, 394 lignes, 30 812 B, `23d5ac1d…`) ; parité `RESULT FAIL` (3 PASS / 5 FAIL : blocs 25 vs 23, H3 supplémentaire, checklist 21 vs 20, identifiants `--allow-empty`, `778a547`, `HEAD`, `PASS`, `RESULT PASS`, `SKILL.md`, `c08c9461…` et nombres manquants) ; tables et frontmatter PASS ; paquet non déclaré validé ; manifeste `MANIFEST_MATCH` après invocation.

Après l'ajout (Étape 6) puis le commit (Étape 7), vérifier l'identité des blobs par OID : l'OID indexé doit égaler `git hash-object --path` de la source, et l'OID de `HEAD` doit égaler celui de l'index. Un `Fingerprint` ou un `git status` propre ne prouve pas cette identité ; l'égalité SHA-256 octet à octet n'est attendue que sans filtre eol (voir Étape 6).

Attention : la suite peut réécrire des fichiers générés (cas observé : 5 sceaux dans `memoire_aq/`). Les traiter après le commit, pas les ignorer.

### Écriture concurrente : valider un instantané gelé

Cas observé (2026-10-26, 11:54–12:04) : le dossier du Skill a été réécrit au moins six fois par d'autres sessions ; parité et QA ont été invalidées deux fois, et le `diff` du manifeste n'est jamais resté vide. Revalider en boucle le dossier vivant ne converge pas : figer un instantané immuable, le valider entièrement, puis archiver exactement ces octets.

1. Attendre une fenêtre stable : échantillonner toutes les 5 s le SHA-256 de l'ensemble `SKILL.md` + `scripts/` + `references/` et exiger 4 échantillons identiques consécutifs (≥ 20 s). Un `diff` vide isolé ne suffit pas.

```bash
stable=0; prev=""
while [ "$stable" -lt 3 ]; do
  cur=$(cd "<dossier-skill>" && find ./SKILL.md ./scripts ./references -type f \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum | sha256sum)
  [ "$cur" = "$prev" ] && stable=$((stable + 1)) || stable=0
  prev=$cur; echo "stable=$stable $cur"; sleep 5
done
```

2. Copier exactement `SKILL.md`, `scripts/` et `references/` (sans cache) vers un dossier neuf hors du Skill et hors du dépôt : `<tmp>/snapshot-<AAAAMMJJ-HHMM>/<nom-skill>/`. Ne pas copier `.git` ni les fichiers temporaires.

```bash
snap="<tmp>/snapshot-<AAAAMMJJ-HHMM>/<nom-skill>"
mkdir -p "$snap/scripts" "$snap/references"
cp "<dossier-skill>/SKILL.md" "$snap/"
cp "<dossier-skill>/scripts/"*.py "$snap/scripts/"
cp "<dossier-skill>/references/"*.md "$snap/references/"
```

3. Prouver `instantané == live` immédiatement après la copie : enregistrer le manifeste de l'état live hors du dossier du Skill, puis exiger un `diff` vide avec les mêmes chemins relatifs calculés dans l'instantané. La copie n'est pas atomique : un `diff` non vide impose de refaire l'instantané, pas de corriger un fichier isolé.

```bash
manifest="$(dirname "$snap")/fingerprints-<nom-skill>.txt"
(
  cd "<dossier-skill>" || exit 2
  find ./SKILL.md ./scripts ./references -type f \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) > "$manifest"
(
  cd "$snap" || exit 2
  find ./SKILL.md ./scripts ./references -type f \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) | diff -u "$manifest" - || { echo "FAIL: instantané != live"; exit 1; }
```

4. Exécuter toute la porte sur l'instantané, avec `$snap` à la place de `<dossier-skill>` : parité, scan des caches, `skill-file-qa --stable-seconds 2`. QA sur l'instantané prouve ces octets, pas le dossier vivant. L'invocation du Skill résout toujours le dossier live : ne l'exécuter que si `live == instantané`, puis recomparer immédiatement.

5. Juste avant `git add`, rejouer le `diff` live vs manifeste. S'il n'est pas vide, abandonner l'instantané et reprendre à l'étape 1 ; ne jamais réutiliser une validation portant sur un autre état.

6. Archiver et indexer les octets de l'instantané : recopier l'instantané vers `.qoder/skills/<nom>`, `git add` par chemins explicites, puis calculer l'OID attendu avec `git hash-object --path` sur le fichier de l'instantané, pas sur le live.

7. Après le commit et le push, lancer `C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py` avec `--skill "<instantané>"` puis `--skill "<dossier-skill>"` ; la nouvelle ref doit être `FRESH`, les anciennes `STALE` sont signalées sans republication. Un écart entre les deux rapports signale une écriture postérieure au commit.

8. Si le live a changé après le commit, ces octets appartiennent à une autre session : les signaler, ne pas les absorber dans le commit ni réécrire l'instantané. L'instantané est la preuve ; le live n'est qu'un état observé. Nommer l'écrivain par le scan JSONL (Étape 4), jamais par `updatedAt`/`runtimeState`.

## Étape 5 — Relire le diff

```bash
git -C "<depot>" diff --stat
git -C "<depot>" diff -- "<chemin>"
git -C "<depot>" status --porcelain=v1
```

Chercher secrets, binaires volumineux, caches et fichiers hors périmètre. Les avertissements de fin de ligne dépendent de `core.autocrlf` : `CRLF will be replaced by LF` (normalisation à l'entrée) et `LF will be replaced by CRLF the next time Git touches it` (`autocrlf=true`) sont informatifs, mais le second annonce une conversion au prochain checkout. Vérifier les blobs (Étape 6) et signaler le risque sans réécrire le dépôt.

## Étape 6 — Ajouter par lots explicites

### Contrôle d'empreinte avant `git add`

Aucun `git add` avant que le manifeste de l'Étape 4 soit identique à l'état courant :

```bash
(
  cd "<dossier-skill>" || exit 2
  find . -type f \( -path './SKILL.md' -o -path './scripts/*' -o -path './references/*' \) \
    ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '*.pyo' -print0 \
    | sort -z | xargs -0 sha256sum
) | diff -u "<manifeste>" - || { echo "FAIL: écriture après validation — ne pas indexer"; exit 1; }
```

Si le `diff` n'est pas vide, ne pas indexer : rejouer parité, scan des caches + `skill-file-qa`, tests applicables et invocation, puis réenregistrer le manifeste. Un simple recalcul de SHA-256 ne remplace pas la revalidation. Répéter le contrôle juste après `git add` : si le `diff` n'est plus vide, ne pas committer ; revalider puis refaire `git add`. L'égalité d'OID vérifiée ci-dessous ne prouve pas que l'index contient la version validée.

```bash
git -C "<depot>" add -- "<chemin1>" "<chemin2>"
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --cached --stat
```

Ne jamais utiliser `git add -A`, `git add .` ni un motif large. Grouper par sujet et séparer les artefacts régénérés du changement de code. Vérifier la liste indexée avant chaque commit.

Vérifier ensuite le contenu réellement indexé, un seul fichier à la fois :

```bash
git -C "<depot>" config --show-origin --get core.autocrlf || echo "core.autocrlf: unset"
oid=$(git -C "<depot>" rev-parse ":<chemin-relatif-depot>")
[ -n "$oid" ] && git -C "<depot>" cat-file -e "$oid" || { echo "FAIL: blob absent"; exit 1; }
expected=$(git -C "<depot>" hash-object --path="<chemin-relatif-depot>" "<chemin-source>")
[ "$oid" = "$expected" ] || { echo "FAIL: OID indexe != source filtree"; exit 1; }
git -C "<depot>" cat-file blob "$oid" | sha256sum
sha256sum "<chemin-source>"
```

- `rev-parse ":<chemin-relatif-depot>"` exige une entrée en stage 0 ; un OID vide ou un `cat-file -e` en échec doit arrêter la vérification.
- L'égalité d'OID prouve que Git stockera la source telle que filtrée par `core.autocrlf` et `.gitattributes` ; c'est le contrôle principal.
- Les SHA-256 affichés peuvent différer avec `core.autocrlf=true` (source CRLF, blob LF) : c'est une normalisation attendue, pas une corruption. Ne pas conclure à un échec sur cette seule différence.
- La forme `cat-file blob <oid>` évite `ref:chemin` et la conversion MSYS des refs contenant `/` (observé, non rejoué dans tous les shells).
- Si `core.autocrlf=true` et que la source est LF, le blob est identique mais un futur checkout écrira CRLF : le signaler. Pour figer `eol=lf`, proposer un `.gitattributes` avec accord explicite ; ne pas modifier `core.autocrlf` ni réécrire le dépôt. Un pipeline masque l'échec de `cat-file` : toujours tester l'OID et `cat-file -e` avant de hacher.

## Étape 7 — Committer

```bash
git -C "<depot>" log --oneline -5
git -C "<depot>" commit -m "$(cat <<'EOF'
fix(physique): corriger les 20 etats S6
EOF
)"
```

Reprendre le style des messages existants. Un commit par sujet. Exception : si une autre session a entrelacé ses hunks avec les nôtres dans un fichier du périmètre, ne pas découper le fichier ni committer un blob différent des octets validés : adopter l'intégralité des octets, rejouer fenêtre stable, parité, `skill-file-qa`, manifeste et invocation, puis créer un seul commit dont le message d'une ligne couvre les deux thèmes et citer la session écrivaine dans le rapport ; les fichiers réécrits par une session sur un thème différent restent hors du commit et le périmètre partiel fichier est déclaré (`git diff --cached --name-only` ⊂ `git diff HEAD --name-only`). Cas observé (2026-10-26) : `9247c943` a écrit `SKILL.md` et `skill-zh.md` à 23:00:52–53 (22:00:52Z, mtime concordant) pendant la validation ; le manifeste pré-`git add` ne captait que `contenu-vers-main.md` (`8062e550`, 21:57:47Z), mais QA a révélé `SKILL.md` (66900 B, `821f8d8c…`) ; les règles entrelacées ont été adoptées ensemble dans `2917d32` (2 fichiers, +12/−12, message d'une ligne couvrant les deux thèmes), `contenu-vers-main.md` exclu et déclaré. Ne pas utiliser `--no-verify`, ne pas amender un commit déjà publié. Après le commit, exécuter `git -C "<depot>" status --porcelain=v1` et `git -C "<depot>" log -1 --stat`. La complétude se prouve par un `git status --porcelain=v1` vide hors cache dans le paquet, pas par `Files (N)` = index : un paquet de 4 fichiers dont 3 changent donne `Files (4)` et un commit de 3 fichiers (cas `f8d23ba`, 2026-10-26). Pour un commit racine (aucun `HEAD` antérieur), réconcilier l'arbre avant de conclure : `git rev-parse "HEAD^{tree}"`, `git ls-tree -r HEAD`, `git ls-files -s` et `git hash-object --path` doivent produire les mêmes OID que l'index, puis relancer immédiatement `git status --porcelain=v1` ; une écriture post-commit reste hors du commit. Avant le premier commit, `HEAD:<chemin-relatif>` n'existe pas : valider l'index avec `git rev-parse ":<chemin-relatif>"` égal à `git hash-object --path`, puis `HEAD:<chemin-relatif>` après le commit racine.

### Cas : `git status` vide alors qu'un commit est attendu

Une autre session peut avoir créé le commit pendant la nôtre. Ne pas créer de commit vide (`--allow-empty`), ne pas amender, ne pas réinitialiser. Établir si `HEAD` contient déjà le travail :

```bash
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --stat
git -C "<depot>" log --oneline -5
git -C "<depot>" reflog -5
```

1. Comparer les SHA-256 courants au dernier SHA-256 validé (manifeste ou empreinte consignée). S'ils diffèrent, l'ancien `PASS` ne vaut plus : rejouer les contrôles applicables (parité si traduction, `skill-file-qa`, invocation) sur les octets courants avant toute conclusion.
2. Prouver l'inclusion fichier par fichier : l'OID de `HEAD` doit égaler le `hash-object --path` de la source filtrée.
3. Chercher dans `HEAD` un marqueur unique de la modification de la session. L'égalité d'OID prouve l'état du fichier, pas l'auteur du commit ; le marqueur relie le contenu au travail décrit.

```bash
head_oid=$(git -C "<depot>" rev-parse "HEAD:<chemin-relatif-depot>")
src_oid=$(git -C "<depot>" hash-object --path="<chemin-relatif-depot>" "<chemin-source>")
[ "$head_oid" = "$src_oid" ] || { echo "FAIL: HEAD ne contient pas la source"; exit 1; }
git -C "<depot>" grep -F -n "<marqueur-unique>" HEAD -- "<chemin-relatif-depot>" \
  || { echo "FAIL: marqueur absent de HEAD"; exit 1; }
```

4. Si l'inclusion est prouvée, ne rien committer pour ce travail : rapporter le commit existant et préciser que son message peut décrire le travail d'une autre session (comparer `reflog`, mtime et message). Si elle échoue, investiguer (mauvais dépôt, stash, commit partiel) ; ne pas fabriquer de commit ni amender.

Cas observé (2026-10-26) : `SKILL.md` validé à `c08c9461…` puis courant à `cc40b069…` ; `status` et `diff` vides ; commit initial `778a547` à 11:54 après des écritures concurrentes à 11:44–11:45 ; `skill-file-qa` rejoué `RESULT PASS` sur les octets courants ; OID `HEAD` égal à la source filtrée pour les 2 fichiers ; marqueurs en L66/L141 et script L530. Aucun commit vide, aucun amend ; le message du commit décrivait le travail concurrent.

### Cas : `HEAD` avance entre la revue et le commit

Si `git commit` retourne `nothing to commit` après une revue `+N/−M` et une QA PASS, une autre session a créé le commit pendant la validation. Ne pas amender, réinitialiser, créer un commit vide ni relancer `git add`.

1. Avant de committer, figer `reviewed_oid=$(git -C "<depot>" rev-parse ":<chemin-relatif-depot>")` et exiger que `git hash-object --path="<chemin-relatif-depot>" "<chemin-source>"` soit égal ; consigner le diff relu (`git diff --cached --stat`).
2. Après l'échec, comparer `git -C "<depot>" rev-parse "HEAD:<chemin-relatif-depot>"` à `reviewed_oid`, puis vérifier un marqueur unique dans `HEAD`. Un `git show --stat HEAD` identique est un indice, pas une preuve de contenu. Si l'OID diffère, arrêter et ne pas pousser.
3. Si l'utilisateur a demandé le push et que l'OID est égal, pousser le commit existant sans nouveau commit ni amend, puis après `git fetch origin` vérifier `git rev-parse "origin/<branche>:<chemin-relatif-depot>"` et `git ls-remote origin "refs/heads/<branche>"`. Avec `core.autocrlf=true`, comparer les OID, pas les SHA-256 : cas observé le 2026-10-26, `+9/−4` (`0b3ebce..4b71f23`), QA `RESULT PASS`, `INDEX_OID=WORKTREE_OID=4b71f23`, `git commit` → `nothing to commit`, commit concurrent `70ccdd9` ; `HEAD:SKILL.md=4b71f23` n'a été comparé qu'après le push, alors que la preuve d'adoption doit précéder le push ; source CRLF `e46b8a92…` ≠ blob LF `3b3ff118…`.

```bash
git -C "<depot>" ls-tree -r HEAD -- "<chemin-relatif-depot>"
head_oid=$(git -C "<depot>" rev-parse "HEAD:<chemin-relatif-depot>")
```

Vérifier les blobs commités et leur stabilité : l'OID de `HEAD` doit égaler celui vérifié à l'Étape 6. Si un hook a pu modifier l'index pendant le commit, refaire la comparaison d'OID avec `git hash-object --path` ; ne pas comparer SHA-256 octet à octet quand un filtre eol s'applique. Le harnais `scripts/run-fixture.sh` rejoue les deux branches de ce cas hors production.

## Étape 8 — Traiter les effets de bord

Si les tests ont modifié des fichiers après le commit, examiner `git diff`, confirmer qu'il s'agit bien d'une régénération, puis créer un commit séparé de type `chore(...)`. Ne pas jeter ces fichiers et ne pas les mélanger au commit fonctionnel. Si les fichiers sont sans rapport, les laisser intacts et le signaler.

## Étape 9 — Détecter une archive publiée devenue obsolète

Un commit local ne met à jour aucune copie archivée sous `.qoder/skills/<nom>` dans un autre dépôt. Après le dernier commit (y compris un `chore(...)` de l'Étape 8), chercher ces archives et les comparer au source final :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_stale_archives.py" \
  --skill "<dossier-skill>" \
  --search-root "<racine-espace>" \
  --search-root "C:/Users/Administrateur/.qoder/skills"
```

Le script est en lecture seule et appartient à `commit-skill-work`, pas au Skill commité : `<dossier-skill>` peut ne contenir que `SKILL.md`, donc le chemin ci-dessus ne se déduit jamais de `<dossier-skill>/scripts/`. Il énumère les dépôts, les refs qui contiennent `.qoder/skills/<nom>`, puis compare chaque blob au source via `git hash-object --path` (filtres eol appliqués). Il ne fait aucun `fetch` : `published` signifie qu'une ref `refs/remotes/` existe localement, pas que le serveur a été interrogé.

| Sortie | Sens | Code |
|---|---|---|
| `RESULT NONE` | aucune archive trouvée | 0 |
| `RESULT FRESH` | toutes les archives sont identiques au source | 0 |
| `RESULT STALE` | au moins une archive diffère (`MISMATCH`, `MISSING` ou `EXTRA`) | 1 |
| `RESULT FAIL` | usage ou environnement invalide | 2 |

- `published` désigne une ref sous `refs/remotes/` ; `local` une branche ou un tag local seulement. Une archive locale en avance (`[ahead 1]`) n'est pas publiée.
- Comparer au source final, pas au diff du commit : une archive peut déjà être obsolète avant le commit. Vérifier `git log -1 --format='%h %s' -- ".qoder/skills/<nom>"` avant d'attribuer la cause au commit courant. Un dépôt per-Skill créé par `git init` fait passer `Repositories` de N à N+1 mais reste `RESULT NONE` : le script ne cherche que `<repo>/.qoder/skills/<nom>`, or ce dépôt stocke `SKILL.md` à sa racine ; ce n'est pas une archive manquée (cas observé : 26 → 27). Capturer le code avant toute troncature : `out=$(…); rc=$?; printf '%s\n' "$out" | tail -40` ; `cmd | tail; echo $?` mesure `tail`, pas le script (cas observé : `ARCHIVE_EXIT=0`).
- Ne jamais recopier, committer, fusionner, pousser ni supprimer l'archive dans cette étape. Signaler `Archives : <ref> <commit> STALE (<n>/<N>)` et attendre une instruction explicite. La republication est une étape séparée (`publier-skill-qoder-vers-depot-git`), jamais automatique.
- Cas observé (2026-10-26) : les modifications devenues le commit `3a47dab` ont rendu l'archive `ddfd179` obsolète, `3/3 MISMATCH`, `EXIT=1` ; l'archive `96fd809` de ce Skill différait déjà sur `2/3` fichiers avant l'ajout de `scripts/find_stale_archives.py`.

## Étape 10 — Pousser seulement sur demande

Par défaut, ne pas pousser. Indiquer explicitement « non poussé » dans le rapport.

Sur demande explicite :

```bash
git -C "<depot>" remote -v
git -C "<depot>" branch -vv
git -C "<depot>" ls-remote <url> "refs/heads/main" "refs/heads/skill/<nom>"
pushed_oid=$(git -C "<depot>" rev-parse HEAD)
git -C "<depot>" push origin "HEAD:refs/heads/skill/<nom>"
```

- Sans remote : appliquer l'Étape 3 (découverte des conventions, cible confirmée) ; avant `git remote add`, sonder chaque URL avec `git ls-remote --heads <url>` : un `RC` non nul ou un `refs/heads/skill/<nom>` déjà présent disqualifie la cible (demander, ne jamais forcer) ; après `git remote add`, relever `git ls-remote origin refs/heads/main` avant le push, puis pousser `HEAD:refs/heads/skill/<nom>` et vérifier que le `ls-remote` de la branche égale le `pushed_oid` figé avant le push et que `refs/heads/main` est inchangé ; si `main` a bougé, le signaler et s'arrêter sans re-push ni force ; ne jamais déduire une URL sans accord ; avec un `origin` partagé : branche dédiée, jamais `main`, jamais de force push. Cas observé (2026-10-26) : `main` distant `b66fdda` avant et après, push `a5095ce` sur `skill/github-pr-create-merge-sans-gh`, `ls-remote` = `HEAD`.
- Pousser sans `-u` : avec une branche locale `main` ou `master`, `-u` la ferait suivre `origin/skill/<nom>` et rendrait `git pull`/`git push` ambigus (état cohérent observé chez des Skills voisins : `master [origin/skill/<nom>: gone]`, `master [origin/skill/<nom>: ahead 1]`) ; n'utiliser `-u` que si les noms locaux et distants coïncident. Relancer le `ls-remote` après le push : exiger que la branche poussée égale le `pushed_oid` figé avant le push (un `rev-parse` postérieur capterait un commit concurrent) et que `main` égale la base relevée avant le push ; signaler la branche réellement poussée.
- « Merge dans `main` » : si `git merge-base origin/main HEAD` sort 1 (histoires sans ancêtre commun), ne pas utiliser `git merge --allow-unrelated-histories` ni extraire `main` dans ce worktree (il est le Skill installé). Sur accord explicite pour le contenu, suivre `references/contenu-vers-main.md` (blob indexé, arbre, commit sur `origin/main`, push fast-forward, `ls-remote`, blobs = disque).

## Étape 11 — Vérifier la résolution runtime du Skill modifié

Après avoir modifié ou commité un Skill, prouver qu'il est réellement résolu par le runtime, et pas seulement présent sur disque :

1. Invoquer le Skill modifié avec l'outil Skill, après la dernière écriture, sans argument si possible. Un répertoire de base renvoyé doit correspondre au dossier réellement modifié, et le contenu chargé doit toujours contenir une règle distinctive de la version finale : le base-dir prouve la liaison, pas la fraîcheur du corps injecté ; seul le contenu tranche. Cas observé (2026-10-26) : après le commit `de7af23`, la preuve a combiné le base-dir et les deux lignes nouvelles (`GIT_CONFIG_COUNT=1`, `asserter d'abord`) ; un corps en cache les aurait omises. Une invocation antérieure à une écriture ultérieure ne prouve rien. Avec des arguments, la couche d'injection remplace les paramètres positionnels numériques (du 1er au 9e) dans un extrait — observé pour les 1er, 2e et 3e — et peut ajouter en fin de corps `ARGUMENTS: …` ; le jeton littéral `$N` (lettre N) reste inchangé. C'est une substitution d'injection, pas une réécriture du fichier. Comparer `stat`/`sha256sum` de `SKILL.md` et l'OID `HEAD:SKILL.md` avant et après l'invocation ; exiger qu'ils restent identiques, même si le texte injecté diffère. Cas observés (2026-10-26) : `audit-recouvrement-skills-avant-creation` commité `c46cd75` (`200dd8b7…`/`baec727b…`), les 1er, 2e et 3e paramètres remplacés dans l'extrait, disque et `HEAD` intacts ; invocation de ce Skill avec arguments, `$N` conservé et `ARGUMENTS: validation lecture seule uniquement ; ne rien committer ni modifier` ajouté, empreintes disque/`HEAD` inchangées pendant l'appel. Ne pas utiliser `$N` comme marqueur de test d'une substitution ; pour durcir les extraits, suivre `harden-skill-argument-substitution`. Pour les extraits publiés, préférer des variables nommées ; l'échappement des paramètres positionnels n'a pas été vérifié. Pour un Skill d'action (ex. `github-pr-create-merge-sans-gh`), l'invocation injecte tout son playbook : ne l'utiliser que comme preuve de résolution (`base directory`, contenu distinctif, empreintes disque et `HEAD` inchangées) et n'exécuter aucune de ses étapes ; une action réelle exige une demande distincte. Cas observé (2026-10-26) : invocation de `github-pr-create-merge-sans-gh` après le commit `0aebb4c`, corps complet injecté, `MANIFEST_MATCH_AFTER_INVOCATION`, `HEAD` et `git status` inchangés, aucun appel PR.
2. Chercher une homonymie qui masquerait la version utilisateur ; les deux racines sont à vérifier :

```bash
find "C:/Users/Administrateur/.qoder/skills" "<racine-espace>/.qoder/skills" -maxdepth 2 -type d -name "<nom-skill>" 2>/dev/null || true
```

Un root absent est ignoré ; seul le nombre de résultats compte. Un seul résultat attendu : la racine utilisateur. Un doublon côté projet masque le Skill utilisateur ; le signaler avant de conclure.

3. `/skills reload` est une commande d'interface que l'agent ne peut pas exécuter : demander à l'utilisateur de la lancer si nécessaire. Une invocation réussie est une preuve plus forte que la seule présence des fichiers ou qu'une liste statique.
4. Si l'invocation échoue ou si les fichiers manquent, ne pas annoncer le Skill comme disponible ; rapporter l'échec.

## Erreurs et pièges (observés et préventifs)

| Symptôme | Cause | Action |
|---|---|---|
| `fatal: not a git repository` avec `EXIT=128` à la racine | la racine du projet n'est pas un dépôt | énumérer les `.git`, puis utiliser `git -C` sur le vrai dépôt ; pour un Skill hors dépôt, découvrir les remotes/conventions des Skills voisins (`branch -vv`, `ls-remote`) et demander la cible (LOCAL-ONLY, archive `main`, ou remote partagé + `skill/<nom>`) |
| `fatal: cannot change to '...ASTRO-Q°ODE_SYSTEME'` | chemin relatif ou non ASCII résolu depuis un autre répertoire courant | vérifier avec `test -d`, puis passer un chemin absolu entre guillemets |
| `UnicodeEncodeError: 'charmap' codec ... cp1252` | console Windows en cp1252 | forcer `PYTHONIOENCODING=utf-8` ou sortir en ASCII ; le script d'inventaire force l'UTF-8 |
| `warning: ... CRLF will be replaced by LF` ou `LF will be replaced by CRLF ...` | normalisation des fins de ligne selon `core.autocrlf` | informationnel ; vérifier les blobs (Étape 6) ; avec `autocrlf=true`, signaler que le prochain checkout peut écrire CRLF |
| `?? scripts/__pycache__/` dans le statut | imports Python | exclure ; ajouter des chemins explicites, ou `.gitignore` après accord |
| branche `master` sur un dépôt, `main` sur un autre, ou `fatal: ambiguous argument 'HEAD'` après `git init` | historiques différents, ou HEAD non né (aucun commit) | sur un HEAD non né, lire `git symbolic-ref --short HEAD` (car `git rev-parse --abbrev-ref HEAD` échoue) ; après `git add`, exiger `git rev-parse ":<chemin>"` = `git hash-object --path`, puis `HEAD:<chemin>` après le root commit |
| tests qui réécrivent des fichiers scellés après le commit | génération relancée par les tests | relire le diff, puis commit `chore(...)` séparé |
| réponse « TOUT » à une question de périmètre | le périmètre reste ambigu | proposer la liste exacte des dépôts et fichiers, la faire confirmer avant `git add` |
| deuxième réponse « TOUT » après reformulation | options mutuellement exclusives | ne pas poser une troisième question ; exécuter la combinaison recommandée, la déclarer, exclure push et suppression |
| push rejeté (non-fast-forward ou historiques sans rapport), ou candidat `ls-remote --heads` en échec / branche `refs/heads/skill/<nom>` déjà présente | dépôt de Skill sans lien avec `origin`, URL injoignable, ou collision de branche | ne pas pousser ni forcer ; re-sonder en lecture seule, choisir une cible valide ou demander ; pousser une branche dédiée |
| « merge to main » avec `git merge-base origin/main HEAD` vide (exit 1) | histoires sans ancêtre commun ; `main` porte l'arbre projet | ne pas fusionner (`--allow-unrelated-histories`) ni extraire `main` dans ce worktree ; sur accord explicite, appliquer le contenu à `main` via `references/contenu-vers-main.md` |
| `nothing to commit` ou `status`/`diff` vides alors qu'un commit est attendu | changements déjà commités par une autre session, ou mauvais dépôt | ne pas créer de commit vide ni amender ; revalider les octets courants, prouver l'inclusion par marqueur et OID, rapporter le commit existant (Étape 7) |
| `git commit` retourne `nothing to commit` après une revue `+N/−M` et une QA PASS, ou `git show --stat HEAD` identique mais contenu différent | commit créé par une autre session pendant la validation ; `--stat` ne prouve pas le contenu | geler `reviewed_oid` avant le commit ; comparer `HEAD:<chemin>` et `hash-object --path` à cet OID ; si égal et push demandé, pousser le commit existant et vérifier l'OID distant ; sinon ne pas pousser |
| `Fingerprint (final)` inchangé après modification de `scripts/`/`references/`, ou absent du manifeste | le fingerprint ne couvre que `SKILL.md`, ou QA ne porte pas sur la version courante | recalculer les SHA-256 des ressources ; revalider et réenregistrer le manifeste ; ne pas conclure que rien n'a changé |
| SHA-256 du blob d'index différent de la source | filtre eol attendu (`core.autocrlf`, `.gitattributes`) ou mauvais fichier | comparer les OID (`hash-object --path` vs index) ; si les OID sont égaux, consigner la normalisation ; sinon ne pas committer |
| PASS obtenu, puis `SKILL.md` ou la traduction réédité | la preuve porte sur une version qui n'existe plus | rejouer parité, `skill-file-qa`, SHA-256 et invocation dans cet ordre, puis figer les empreintes |
| `diff` du manifeste non vide avant `git add` | écriture concurrente après la validation | ne pas indexer ; rejouer parité, QA, tests et invocation, réenregistrer le manifeste, puis recommencer le contrôle |
| `diff` du manifeste non vide à chaque passe, source modifiée toutes les 10–30 s | une autre session réécrit le dossier sans s'arrêter | ne pas boucler : figer un instantané hors du Skill, le valider, archiver ses octets (Étape 4) |
| parité et QA réussies puis invalidées une deuxième fois | la preuve porte sur un état qui a changé pendant les contrôles | instantané immuable, `diff` live vs manifeste juste avant `git add` ; repartir de l'étape 1 au moindre écart |
| invocation réussie mais live modifié juste après, ou corps injecté affichant la valeur d'un argument à la place d'un paramètre numérique (1er à 9e), ou `$N` littéral conservé avec `ARGUMENTS: …` ajouté | le runtime résout le dossier live ; une invocation avec arguments substitue les paramètres numériques et ajoute `ARGUMENTS: …`, sans toucher le `$N` littéral | recomparer live == instantané immédiatement après l'invocation, et exiger `SKILL.md`/OID `HEAD` identiques avant/après ; une substitution d'arguments n'est pas une écriture et ne doit pas servir de test de `$N` ; sinon l'invocation ne prouve pas l'instantané |
| commit racine : `HEAD^{tree}`, `ls-tree -r HEAD`, `ls-files -s` ou `hash-object --path` divergents, ou `status` modifié juste après le commit | pas de `HEAD` antérieur ; hook ou écriture pendant le commit | réconcilier les OID de l'arbre et de l'index, puis relancer `status` immédiatement ; ne pas conclure sur `log -1 --stat` seul |
| manifeste absent ou placé dans le dossier du Skill | validation non tracée, ou manifeste auto-inclus | enregistrer le manifeste hors du Skill après la dernière écriture ; sinon reprendre l'Étape 4 |
| `RESULT PASS` mais `Files (N)` liste `__pycache__/*.pyc` | le validateur ne prouve pas l'absence de caches | supprimer les caches créés par la session, relancer QA, exiger `Files (N)` égal à l'inventaire sans cache ; si le cache est préexistant et conservé, valider l'instantané sans cache |
| archive `MISMATCH`/`MISSING` après le commit | copie archivée non republiée, ou déjà obsolète avant le commit | signaler `STALE` avec ref/commit ; ne pas recopier ni pousser automatiquement |
| `find_stale_archives.py` sort en 1, ou archive trouvée seulement sur une ref locale `[ahead 1]`, ou `Repositories` +1 après `git init` avec `RESULT NONE` | archive obsolète (pas un crash), commit non poussé, ou dépôt per-Skill sans chemin `.qoder/skills/<nom>` | lire le rapport (sortie 2 = usage/environnement) ; marquer `local`, ne pas la présenter comme publiée ; `cmd` suivie de `tail` renvoie le statut de `tail` : capturer `rc=$?` avant de tronquer |
| OID vide ou `cat-file` en échec mais pipeline à 0 | chemin non indexé, OID multiple, ou `pipefail` absent | tester `[ -n "$oid" ]` et `git cat-file -e`, puis relancer |
| Skill modifié non résolu ou introuvable | index runtime non rechargé, ou homonyme projet qui masque | invoquer le Skill, vérifier les deux racines, puis demander `/skills reload` à l'utilisateur |
| plan approuvé, mais taille/mtime/SHA-256 ou lignes différents avant écriture ; ou attente de session expirée alors que le disque est stable | fichier réécrit depuis la planification ; l'état de session n'est pas un journal d'écriture | rééchantillonner, relire, ré-ancrer par texte exact, préserver les ajouts concurrents ; ne pas restaurer de sauvegarde ; juger l'activité par les empreintes disque, pas `runtimeState` ; nommer l'écrivain par les JSONL (`Write`/`Edit`), jamais par `updatedAt` ; classer la couverture du plan avant toute édition et n'éditer que les points `ABSENT`/`PARTIAL`, puis rejouer toutes les portes après chaque écriture concurrente ; revalider les octets finaux |
| `RESULT PASS` QA mais parité `RESULT FAIL` après mise à jour de la seule source | traduction volontairement intacte (périmètre partiel) | rapporter QA et parité séparément avec les écarts ; ne pas déclarer le paquet validé ; proposer le miroir |
| prémisse de périmètre changée en cours de flux, ou `Files (N)` QA ≠ inventaire sans cache, ou index ≠ `git diff HEAD --name-only` sans commit partiel déclaré | décision prise sur un état périmé (fichier d'abord exclu devenu référencé), ou commit partiel non déclaré, ou hunks d'une autre session entrelacés dans un fichier du périmètre | s'arrêter et reconfirmer avant `git add` ; commit complet : index = `git diff HEAD --name-only`, `git diff --name-only` vide hors cache, puis `git status --porcelain=v1` post-commit vide hors cache ; `Files (N)` = inventaire sans cache, sur-ensemble de l'index et égal seulement si tous les fichiers ont changé ; commit partiel déclaré : index ⊂ `git diff HEAD --name-only`, changements restants listés ; hunks concurrents inséparables dans un même fichier : adopter les octets entiers, rejouer toutes les portes, un seul message d'une ligne couvrant les deux thèmes et session écrivaine citée, sans découper les hunks ni restaurer la version antérieure ; jamais indexer un fichier inchangé ni supprimer un cache préexistant |
| parité `RESULT FAIL` avec `FAIL inline tokens: missing=[…]` et/ou `extra=[…]` alors que les deux fichiers ont été modifiés | identifiant protégé reformulé en prose dans la traduction, ou multiplicité globale différente (token répété dans plusieurs sections, exemple ajouté ou supprimé ; cas observé : `$N` → « ce littéral ») | ne pas affaiblir le contrôle ni modifier la source ; compter les multiplicités des deux corps avec `INLINE_RE` et `Counter`, ajouter chaque occurrence manquante et reformuler chaque occurrence excédentaire, puis rejouer parité, QA, manifeste et invocation |

## Checklist finale

- [ ] Dépôt réel localisé par chemin absolu, branche lue.
- [ ] Dépôt initialisé hors dépôt : soit LOCAL-ONLY confirmé (aucun origin ni push, branche lue avec `git symbolic-ref --short HEAD`, `init.defaultBranch` et dépôts voisins consignés), soit remote partagé découvert (`branch -vv`/`ls-remote`), cible confirmée, `git remote add`, branche `skill/<nom>` poussée et `ls-remote` = HEAD ; distinct de « dépôt existant sans origin → demander l'URL ».
- [ ] Changements SESSION et PREEXISTANT séparés ; préexistants confirmés.
- [ ] Aucun `git add -A` ni `git add .` ; chemins explicites.
- [ ] Tests exécutés et résultats consignés ; `RESULT PASS` si un Skill change ; nouveau script d'aide recoupé avec une référence indépendante (même dernier `timestamp` et même total `Write`/`Edit` par session) et matrice négative passée.
- [ ] `skill-file-qa` : `Files (N)` égal à l'inventaire sans cache après changement ; aucun `__pycache__`/`*.pyc` créé par les tests ou `py_compile` ; commit complet : index = `git diff HEAD --name-only`, `git diff --name-only` vide hors cache, puis `git status --porcelain=v1` post-commit vide hors cache ; `Files (N)` = index seulement si tous les fichiers ont changé ; commit partiel déclaré : index ⊂ `git diff HEAD --name-only`, changements restants listés ; cache préexistant conservé → QA sur instantané sans cache, jamais de suppression pour faire coïncider l'index ; si la prémisse change, reconfirmer avant `git add`.
- [ ] Diff relu ; aucun secret, binaire volumineux ni `__pycache__`.
- [ ] Un commit par sujet, message aligné sur l'historique ; hunks concurrents inséparables dans un même fichier : octets entiers adoptés, portes rejouées, un seul message d'une ligne couvrant les deux thèmes, session écrivaine citée.
- [ ] Travail déjà absorbé par un commit concurrent : aucun commit vide, aucun amend ; octets courants revalidés, inclusion prouvée par marqueur et OID, message attribué avec prudence.
- [ ] `HEAD` avancé entre la revue et le commit : `reviewed_oid` figé avant le commit, `HEAD:<chemin>` égal à cet OID avant le push, commit existant poussé sans nouveau commit ni amend, OID distant vérifié.
- [ ] Commit racine : index validé par `git rev-parse ":<chemin>"` = `git hash-object --path` avant le premier commit, puis `HEAD:<chemin>` ; `HEAD^{tree}`, `ls-tree -r HEAD`, `ls-files -s` et `hash-object --path` réconciliés avec l'index, puis `status` relancé immédiatement.
- [ ] Statut post-commit propre, ou effets de bord expliqués et commités.
- [ ] Archives voisines vérifiées après le dernier commit : `NONE`, `FRESH`, ou `STALE` signalée avec ref/commit.
- [ ] Aucune archive recopiée, commitée ni poussée automatiquement.
- [ ] Push uniquement sur demande ; candidats sondés en lecture seule (`git ls-remote --heads <url>` : `RC=0`, branche cible absente), `main` distant relevé avant/après et inchangé, remote, branche et hash vérifiés (`pushed_oid` figé avant le push et comparé au `ls-remote`), `-u` seulement si les noms locaux et distants coïncident ; contenu vers `main` sans ancêtre commun via `references/contenu-vers-main.md`, sans checkout ni fusion.
- [ ] Empreintes SHA-256 de `SKILL.md`, `scripts/` et `references/` relevées ; le `Fingerprint` seul ne couvre que `SKILL.md`.
- [ ] Blobs d'index et blobs `HEAD` comparés par OID à la source filtrée ; écart SHA-256 expliqué par un filtre eol si applicable.
- [ ] Après la dernière écriture : parité, `skill-file-qa`, SHA-256 et invocation rejoués dans cet ordre ; empreintes finales consignées ; aucun token manquant toléré même si QA est PASS.
- [ ] Manifeste SHA-256 enregistré hors du Skill après la dernière écriture ; `Fingerprint (final)` de QA égal au `./SKILL.md` du manifeste.
- [ ] `diff` du manifeste vide avant et après `git add` ; aucune écriture entre validation et indexation.
- [ ] Écart de manifeste traité par revalidation complète, jamais par un simple recalcul de SHA-256.
- [ ] Si la source bouge encore : instantané figé hors du Skill, `instantané == live` avant `git add`, validation et archive portant sur ces octets.
- [ ] Invocation faite seulement si `live == instantané`, avec recomparaison immédiate.
- [ ] `core.autocrlf` lu avec `--show-origin` ; risque de conversion au checkout signalé.
- [ ] Réponse « TOUT » répétée traitée sans troisième question, combinaison déclarée.
- [ ] Skill modifié résolu par invocation réelle ; base-dir (si renvoyé) exact ET règle distinctive de la version finale dans le corps injecté (le base-dir seul ne prouve pas la fraîcheur) ; aucune homonymie projet/utilisateur ; si l'invocation utilise des arguments, `SKILL.md` et l'OID `HEAD` identiques avant/après (paramètres numériques 1er à 9e substitués et `ARGUMENTS: …` ajouté côté injection ; `$N` littéral inchangé ; pas le disque) ; `/skills reload` laissé à l'utilisateur ; une invocation de Skill d'action ne déclenche aucune de ses étapes.
- [ ] Plan approuvé : baseline (taille/mtime/SHA-256) rééchantillonné avant écriture ; ancres relues par texte ; ajouts concurrents préservés ; aucune sauvegarde restaurée ; corps à 499 lignes maximum ou compactage préalable ; `description` mesurée par script (≤ 1024 caractères), N de `skill-file-qa` égal au fichier final ; écrivain identifié par scan JSONL (`Write`/`Edit`), pas par `updatedAt`/`runtimeState` ; couverture du plan classée (`CURRENT`/`ALREADY_APPLIED`/`PARTIAL`/`ABSENT`/`CONFLICT`), seuls `ABSENT`/`PARTIAL` édités, octets concurrents adoptés, aucun `PASS` antérieur réutilisé.
- [ ] Périmètre partiel (source seule) : traduction intacte ; QA et parité rapportés séparément avec écarts ; paquet non déclaré validé.

## Rapport

```text
Dépôt : <chemin absolu> | Branche : <nom> | <LOCAL-ONLY|remote>
Commits : <hash court> <sujet>
Commit concurrent : aucun | <hash> inclus (OID+marqueur), message d'origine incertaine | écrivain <session> | message couvrant <n> thème(s)
Fichiers : <N> | Tests : <résultat>
Intégrité : blobs source <N>/<N> | autocrlf <valeur> | checkout <identique|converti>
Push : non effectué | <remote> <branche> <pushed_oid = hash distant> | main distant <avant>=<après> | main par contenu : aucun (<commit>)
Archives : aucune | <ref> <commit> <FRESH|STALE n/N> [published|local]
Gate : manifeste <n> fichiers | QA=manifeste <oui|non> | avant add <identique|écart> | après add <identique|écart> | Files (N)=inventaire <oui|non> | index=changements <oui|non> | post-commit <vide|écart> | arbre racine <réconcilié|N/A>
Instantané : aucun | <chemin> | live=instantané <oui|non> | gate <PASS/N/A>
Plan : baseline <sha> rééchantillonné <identique|écart> | ré-ancrage <n> édition(s) | couverture <CURRENT|ALREADY_APPLIED|PARTIAL|ABSENT|CONFLICT> | ajouts concurrents <préservés|aucun>
Périmètre : complet | source seule (traduction intacte, parité en attente)
Paquet : validé | non validé (source QA PASS, parité FAIL <n>)
Skill : <nom> | résolution : <base-dir ET contenu vérifié> | empreintes finales : <sha SKILL.md> <n scripts> <n references> (si un Skill est modifié)
Contrôles rejoués après la dernière écriture : parité <PASS|FAIL|N/A> | QA <PASS> | SHA-256 <n> | invocation <OK>
```

## Ressources

- `scripts/inspect_git_state.py` : inventaire lecture seule des dépôts, branches, statuts, diffs et remotes ; sortie ASCII, codes 0/1/2.
- `scripts/find_stale_archives.py` : détection lecture seule des copies archivées du Skill dans les dépôts voisins ; compare les OID des blobs au source et signale `NONE`/`FRESH`/`STALE` ; codes 0 (NONE/FRESH), 1 (STALE), 2 (usage/environnement).
- `scripts/run-fixture.sh` : harnais jetable rejouant l'adoption d'un commit concurrent et le rejet d'un commit au stat identique mais au contenu différent ; n'écrit que dans un répertoire temporaire et le supprime ; codes 0 (PASS), 1 (FAIL), 2 (usage/environnement).
- `references/skill-zh.md` : version chinoise complète, à maintenir structurellement parallèle ; les règles de parité sont décrites par `skill-doc-translation-parity`.
- `references/contenu-vers-main.md` : application du contenu à `main` quand `git merge-base origin/main HEAD` est vide (histoires sans ancêtre commun) ; diagnostic, gel, arbre temporaire, commit sur `origin/main`, push fast-forward, vérification des blobs ; jamais de checkout de `main` ni de fusion `--allow-unrelated-histories`.
- `scripts/find_writers.py` : attribution en lecture seule de l'écrivain d'un Skill depuis les JSONL de session (`Write`/`Edit`, `input.file_path`) ; affiche la dernière écriture par session ; lancer `py -3 "C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_writers.py" --target "<dossier-skill>" --jsonl-dir "C:/Users/Administrateur/.qoder/projects/<projet>"` ; codes 0 (trouvé), 1 (aucun), 2 (usage/environnement). Avant de documenter un nouveau script d'aide en lecture seule, le recouper avec une implémentation de référence indépendante sur des données réelles : exiger le même dernier `timestamp` par session et le même total cumulé de `Write`/`Edit` (l'heure seule ne suffit pas), puis passer la matrice négative (répertoire vide, aucun match, JSONL corrompu, `--target` invalide, `--max-files 0` puis `1`) et vérifier l'absence de cache ; séparer dans le code le compteur cumulé de l'accumulateur « dernière écriture » (défaut observé : compteur remis à zéro sur un timestamp plus récent → `records 2` au lieu de 19 et 4).
