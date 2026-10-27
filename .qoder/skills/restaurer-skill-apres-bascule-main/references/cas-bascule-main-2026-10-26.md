# Cas — bascule sur `main` puis restauration du Skill (2026-10-26)

## Provenance

- Session source principale : `2c0b2667-e511-4ceb-bffd-35da387ef7c0`, snapshot `revision 59`, `runtimeState=ready`, `hasMoreBefore=false`, 12 tours (24 messages), lu le 2026-10-26 vers 18:45 +01:00.
- Session parallèle : `8627a51e-b148-4690-9f79-42c204bc799b` (4 messages, `ready`, `hasMoreBefore=false`), lue intégralement le 2026-10-26 vers 18:52 +01:00. Elle visait le même Skill et a exécuté deux harnais indépendants (racines et commits différents) : `RESULT PASS`, 46 assertions, 0 échec. Son premier essai a échoué sur `orphan-commit warning missing` parce que la fixture conservait la branche `master` : d'où la règle « l'absence de l'avertissement ne prouve rien ». Elle n'a écrit aucun fichier dans le dossier cible ; ses résultats sont repris ici comme confirmation indépendante, pas comme source du contenu.
- Toutes les heures `Z` proviennent des messages ; les dates Git sont en `+01:00`.

## Chronologie vérifiée

| Heure (UTC) | Événement | Preuve |
|---|---|---|
| 17:33:50 | upstream de `master` détaché, branche locale supprimée, HEAD détaché sur `6a270df`, racine avec `SKILL.md`, `references/`, `.gitattributes` | sortie `git branch -vv`, `ls` |
| 17:34:47 | `git branch --track main origin/main` crée `main` sans bascule ; `main = origin/main = 2d013354…` ; HEAD reste `6a270df…` ; SHA-256 inchangés | `branch 'main' set up to track 'origin/main'.` + `MAIN`/`HEAD`/`FILES` |
| 17:35:19 | `git switch main` rc=0 ; avertissement `leaving 3 commits behind` ; le worktree est réécrit | sortie `SWITCH` et `AFTER` |
| 17:35:19 | racine = `SKILL.md` + `scripts` ; `SKILL.md` racine = `verify-skill-runtime-binding` ; `references/` et `.gitattributes` absents | `---ROOT---`, `---ROOT_HEAD---`, `---GITATTR---` |
| 17:35:19 | archive extraite en `i/lf w/crlf` ; SHA-256 `a256da71…` / `48c0ba5d…` ≠ empreintes validées | `---EOL---`, `---ARCHIVE_HASHES---` |
| 17:36:19 | `ls-tree` donne les blobs `6470a525…` / `f319a3ea…` ; après écriture racine : SHA-256 `1d21612d…` / `c6000172…`, CR=0, frontmatter correct | `SKILL_OID=`, `---HASHES---`, `---EOL---`, `---HEAD_LINES---` |
| 17:36:19 | statut après restauration : ` M SKILL.md` et `?? references/` | `---STATUS---` |
| 17:37:46 | branche `restore/skill-adopt-concurrent-duplicate-skill`, ajout explicite, OID index = OID attendus, commit `f8cd548b…` | `---OIDS---`, sortie commit |
| 17:39:18 | `git reflog expire --expire-unreachable=now --all` puis `git gc --prune=now` ; 6 commits orphelins supprimés, `fsck` rc=0 | `--- orphan lookups ---`, `GONE` |

Empreintes datées :

| Objet | Valeur |
|---|---|
| `SKILL.md` validé | `1d21612d0c6a833561c974c279511c24e9824fabef1e8c84a76bdabd3acf3133` |
| `references/preuves-session.md` validé | `c600017211e1976bf3d6af642082f43f136998bfe12a8ba4cda25ec574fabee3` |
| copie CRLF après bascule | `a256da719aebbe6109435337d195f93a4f850c4c96d01897852468559bb3cbfb` / `48c0ba5d282b40a78bb2d0d3f77eb7189983aeb7d7b49401ccbce23d67cd0fc2` |
| blob `SKILL.md` sur `main` | `6470a52525afe50444181362259a6aac6683dcad` |
| blob `references/preuves-session.md` sur `main` | `f319a3ea6e9f96759a3cc7693066828771128026` |
| blob `.gitattributes` (commit orphelin) | `c8950c1f1fb583eb1aa4ce93fc24f997064130f4` |
| `main` / `origin/main` | `2d013354002370f241d14fa263829fb41221e8c0` |
| HEAD avant bascule | `6a270df986eb234b335979abccd838cfa29e0e67` |
| commit de restauration | `f8cd548b2eb6bdf60f2f88e7daa5a82f5cd8ec36` |

## Extrait verbatim de la bascule

```text
Your branch is up to date with 'origin/main'.
Warning: you are leaving 3 commits behind, not connected to
any of your branches:

  6a270df docs(skill): 补充共享参考合并与潜在写入者规则
  b27ec86 chore(skill): forcer les fins de ligne LF
  4b19c34 docs(skill): 补充多写入者归因与验收计数不变量
...
Switched to branch 'main'
SWITCH_EXIT=0
```

```text
---ROOT---
SKILL.md
scripts
---ARCHIVE_HASHES---
a256da71… *.qoder/skills/<nom>/SKILL.md
48c0ba5d… *.qoder/skills/<nom>/references/preuves-session.md
---GITATTR---
ABSENT
```

## Harnais de rejeu (exécuté le 2026-10-26, hors production)

Deux cas indépendants sous `~/.qoder/tmp`, chacun avec un origin nu, un `main` de type monorepo et un dépôt Skill à histoire sans ancêtre commun :

- cas A « detached » : HEAD détaché, aucune branche locale, aucun commit de secours ;
- cas B « rescue » : branche `rescue/skill` créée avant la bascule.

Commande centrale exercée :

```bash
git branch --track main origin/main
git switch main
read -r _mode _type oid _path <<< "$(git ls-tree main -- ".qoder/skills/<nom>/SKILL.md")"
[ -n "$oid" ] && [ "$(git cat-file -t "$oid")" = blob ] || { echo "FAIL: blob introuvable"; exit 1; }
git cat-file blob "$oid" > SKILL.md
```

Résultat : `RESULT=PASS pass=80 fail=0` (26 assertions pour A, 54 pour B), `CLEAN=PASS`. Ce harnais extrayait l'OID par `ls-tree` + `awk` ; la forme livrée ci-dessus (`ls-tree` + `read -r`, sans variable positionnelle) est couverte séparément par 25 assertions (voir « Observation tardive »).

Assertions couvertes : création de `main` sans modification de HEAD ni des SHA-256 ; `main = origin/main` ; bascule rc=0 ; racine remplacée par l'autre Skill ; `references/` et `.gitattributes` absents ; archive présente ; `i/lf w/crlf` ; SHA-256 et CR de l'archive différents ; avertissement `leaving 1 commit behind` présent en A et absent en B (la branche `rescue/` référence l'ancien HEAD) ; restauration SHA-256 exacte, CR=0, frontmatter correct ; statut ` M SKILL.md` + `?? references/` ; blob `.gitattributes` encore résoluble ; restauration de `.gitattributes` fidèle en B.

Correction de harnais : la première exécution a produit 4 échecs parce que l'archive de `main` avait été écrite avec un texte différent du fichier validé. Le défaut venait du harnais, pas de la procédure ; après alignement des octets, 80/80 passent. Ce détail est conservé pour éviter de prendre un hash attendu pour acquis.

Limites : le harnais ne teste pas un `origin/main` qui avance pendant l'opération, ni un dépôt shallow, ni un worktree multiple. `git show main:<chemin>` n'a pas été rejoué dans le harnais ; la préférence pour `ls-tree` + `cat-file blob` vise la sélection exacte du blob et l'évitement de `ref:chemin`, pas l'échec systématique de `git show`.

## Statut des affirmations

| Affirmation | Statut | Base |
|---|---|---|
| `--track` crée `main` sans basculer | vérifié | sortie 17:34:47 |
| la bascule remplace le `SKILL.md` racine et supprime `references/`, `.gitattributes` | vérifié | sortie 17:35:19 |
| `i/lf w/crlf` explique l'écart de SHA-256, blobs inchangés | vérifié | `ls-files --eol` + OID `main` égaux aux empreintes |
| restauration par `ls-tree` + `cat-file blob` redonne les octets validés | vérifié par harnais | 2 cas, 80 assertions |
| défaut : laisser la restauration non commitée | vérifié | statut 17:36:19 avant la demande de commit |
| `.gitattributes` a été restauré dans la session source | **faux** | il est resté absent (`GITATTR ABSENT` après restauration) |
| `leaving N commits behind` est un contrôle d'intégrité | **faux** | il disparaît si une branche référence l'ancien HEAD (cas B) |
| `reflog expire` + `gc` permettent un ménage sans perte | **faux** | 6 commits et 2 versions intermédiaires détruits |
| un merge en avance rapide reconvertit le worktree en CRLF sans changer les blobs | vérifié | sortie 17:44:29 |
| Git peut interpréter un renommage et déplacer le contenu lors d'un merge | vérifié | sorties 17:45:44 à 17:47:22 |
| comportement après le snapshot (autres dépôts, autres sessions) | non vérifié | non observé |

## Différences avec la recommandation automatique

- Elle annonçait une restauration « verbatim » par `cat-file blob` : la commande n'était pas dans la sortie de session, elle a été établie par le harnais.
- Elle ne mentionnait pas que `.gitattributes` restait absent dans la session source.
- Elle ne mentionnait pas le `gc` destructif ni la perte de commits locaux.
- Elle présentait la bascule comme le point de départ ; la branche `rescue/` ajoutée ici est une amélioration justifiée par la perte observée, pas une étape reproduite.

## Observation tardive — substitution d'argument (2026-10-26)

Un appel de contrôle avec trois jetons d'arguments a injecté `awk '{print exécuter}'` à la place de l'expression attendue qui imprimait le troisième champ : le moteur d'arguments remplace les variables positionnelles numériques du corps injecté par les arguments de l'appel. Le disque était intact (SHA-256 `f1c9a162…` avant et après), donc la substitution est un rendu à l'exécution, pas une écriture.

Quatre formes d'extraction ont été utilisées ou envisagées. `ls-tree` + `awk` a servi au harnais à 80 assertions, mais contenait une variable positionnelle numérique, donc substituable à l'appel. `cut -d' ' -f3` a été écarté : `ls-tree` sépare l'OID du chemin par une tabulation, donc ce champ vaut `oid<TAB>chemin` et casse `cat-file blob`. `git rev-parse --verify "main:<chemin>"` a fonctionné (fixture dédiée : `RESULT=PASS pass=19 fail=0`), mais divergeait de l'Étape 1 et du piège `ref:chemin` du même paquet. La forme livrée est donc `git ls-tree` + `read -r` dans des variables nommées, sans variable positionnelle numérique : elle reste alignée sur l'Étape 1, ne dépend pas de `ref:chemin`, et sa fixture donne `RESULT=PASS pass=25 fail=0` — OID à 40 hexadécimaux, type `blob`, octets identiques au blob attendu, CR=0, statut ` M SKILL.md` + `?? references/`, chemin absent → OID vide, garde rc=1 sans fichier créé.

Le harnais à 80 assertions ci-dessus reste valable pour la bascule, le statut et la fidélité des octets, mais il extrayait l'OID par `ls-tree` + `awk` ; l'extraction livrée est couverte par la fixture à 25 assertions, pas par ces 80. La session parallèle `8627a51e` apporte une mesure indépendante supplémentaire : 46 assertions, 0 échec, sur deux racines et deux commits différents.

## Observations post-restauration (2026-10-26, 17:44–17:47 UTC)

- 17:44:05 : demande de fusionner `restore/skill-adopt-concurrent-duplicate-skill` dans `main`. 17:44:29 : fast-forward `2d01335..f8cd548`, sans conflit (`SKILL.md` 606 lignes modifiées, `references/preuves-session.md` 517 lignes ajoutées). Les blobs racine restent `6470a525…` / `f319a3ea…`, mais les SHA-256 disque repassent à `a256da71…` / `48c0ba5d…` : la fusion réécrit le worktree et `core.autocrlf=true` reconvertit en CRLF.
- 17:45:27 : `push main to origin`. Le remote avait avancé de 5 commits (`3a9f519`) ; le push direct est rejeté. La première fusion automatique a interprété le renommage upstream `SKILL.md → .qoder/skills/verify-skill-runtime-binding/SKILL.md` et placé le contenu dans l'archive verify en supprimant la racine.
- Correction : fusion refaite avec `merge.renames=false`, conflit `modify/delete` résolu en conservant le `SKILL.md` racine, archive verify restaurée (`7a1c3120…`). `skill-file-qa` : `RESULT PASS` (10 pass, 0 fail, 10 warns de layout attendus). Push `3a9f519..8be9806`, `main` à jour et racine distante inchangée (`6470a525…` / `f319a3ea…`).
- 17:47:39 : branche `restore/skill-adopt-concurrent-duplicate-skill` supprimée (`f8cd548`, déjà fusionnée) ; elle n'avait jamais été poussée.
- Conséquence : l'état sain se juge sur l'OID de blob, pas sur le SHA-256 disque. Un merge, comme un checkout, peut faire diverger le disque sans modifier l'arbre ; et un merge peut déplacer du contenu via une détection de renommage, donc l'arbre doit être vérifié avant de conclure.

## Règles de réutilisation

- Les OID, SHA-256, tailles et chemins ci-dessus sont des observations datées, pas des constantes.
- Toujours comparer les octets du blob aux empreintes d'un `skill-file-qa` antérieur ; sans référence, s'arrêter.
- Ne pas déduire l'intégrité de `git status` ni de l'absence d'avertissement Git.
- Ne pas exécuter de ménage de refs tant que la restauration n'est pas commitée ou poussée.
- Un harnais doit d'abord reproduire les octets validés ; sinon ses échecs accusent à tort la procédure.
