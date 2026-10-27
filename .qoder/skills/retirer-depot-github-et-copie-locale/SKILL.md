---
name: retirer-depot-github-et-copie-locale
description: "Retirer un dépôt GitHub et/ou sa copie locale sans ambiguïté : décomposer « fermer le dépôt » en archivage GitHub (archived=true), suppression définitive, simple détachement d'origin ou aucune action, et « supprimer le dossier de travail » en cible explicite (dossier Skill, workspace projet) avec sauvegarde hors cible puis suppression sous garde de chemin exact. Vérifier archived/private/default_branch par PATCH puis GET, sauvegarder tout le dossier avec .git dans ~/.qoder/tmp, contrôler nombre de fichiers, SHA-256 de SKILL.md, HEAD et propreté Git, puis prouver l'absence après suppression et l'absence de copie homonyme dans les deux racines skills. Utiliser pour « 关闭这个仓库 », « 归档仓库 », « 删除远程仓库 », « 解除 origin », « 删除本地工作区目录 », « 删除 Skill 目录 », « 清理备份目录 », GitHub archived=true, PATCH /repos, delete_repo, rm -rf guard, /skills reload, archive push 403. 中文触发：关闭仓库、归档 GitHub 仓库、永久删除远程仓库、仅解除 origin、删除本地工作区、删除 Skill 目录、备份后删除、清理备份目录、删除后同名残留、运行时技能列表未刷新。"
---

# Retirer un dépôt GitHub et/ou sa copie locale

## Portée

Ce Skill traite deux demandes courtes qui recouvrent plusieurs actions :

- « fermer ce dépôt » : archiver le dépôt distant, le supprimer définitivement, détacher seulement l'`origin` local, ou ne rien faire ;
- « supprimer le dossier de travail local » : dossier Skill, workspace projet, ou autre chemin explicite, avec sauvegarde préalable ou suppression directe.

La règle centrale : **aucune action irréversible avant une réponse explicite**. Ne jamais interpréter « fermer » comme « supprimer », ni « dossier de travail » comme un chemin deviné.

Ce Skill ne remplace pas les Skills voisins :

- `diagnostiquer-push-github-depot-absent` pour un push ou un remote absent ;
- `commit-skill-work` pour un commit ou un push ordinaire ;
- `nettoyer-branches-refs-git` pour les branches et les refs ;
- `publier-skill-qoder-vers-depot-git` pour publier une copie de Skill dans un dépôt.

## Étape 0 — Figer les faits avant de poser les questions

Collecter en lecture seule, et noter les valeurs réellement observées :

- dépôt distant : `owner/repo`, visibilité, branche par défaut, état `archived` actuel, remote local ;
- copie locale : chemin absolu, `git rev-parse HEAD`, `git status --porcelain=v1`, `git remote -v` ;
- nature de la cible : dossier sous `~/.qoder/skills`, dossier sous `<workspace>/.qoder/skills`, workspace projet, ou autre ;
- les deux racines skills à scanner après suppression ;
- si la cible est un Skill, taille, `mtime` et SHA-256 de `SKILL.md` avant toute écriture.

S'arrêter et demander si l'un de ces cas apparaît :

- la cible est `/`, `$HOME`, `~/.qoder`, `~/.qoder/skills`, ou la racine du workspace ;
- la cible est un lien symbolique ou une jonction ;
- la cible contient des sous-modules ou des worktrees Git ;
- le worktree est sale (`git status --porcelain=v1` non vide) ;
- une autre session écrit encore dans la cible.

## Étape 1 — Décomposer la demande en une seule AskUserQuestion

Poser au plus trois questions dans un seul appel, pour éviter d'enchaîner les confirmations :

1. **Action distante** : archiver (recommandé) / supprimer définitivement / détacher `origin` / aucune action.
2. **Cible locale** : aucune / dossier Skill / workspace projet / autre chemin explicitement fourni.
3. **Mode de suppression**, seulement si une cible locale est choisie : sauvegarder puis supprimer (recommandé) / supprimer directement.

Contraintes de formulation :

- pour la suppression définitive, écrire « irréversible » et demander ensuite le nom complet `owner/repo` ;
- pour le workspace projet, prévenir qu'il peut contenir d'autres travaux et exiger le chemin absolu exact ;
- ne pas exécuter l'action pendant la question ; consigner les réponses dans le rapport final.

## Étape 2 — Archiver le dépôt distant

Utiliser le jeton déjà stocké par Git Credential Manager, sans jamais l'afficher :

```bash
DEPOT="$DEPOT_CONFIRME"
cred=$(printf 'protocol=https\nhost=github.com\n\n' | GIT_TERMINAL_PROMPT=0 git -c credential.interactive=never credential fill 2>/dev/null)
pass=$(printf '%s\n' "$cred" | sed -n 's/^password=//p')
unset cred
resp=$(curl -s -w '\n__HTTP__%{http_code}' -X PATCH \
  -H "Authorization: Bearer $pass" \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/$DEPOT" \
  -d '{"archived":true}')
unset pass
printf '%s' "$resp" | py -3 -c "import sys,json; raw=sys.stdin.read(); body,_,tail=raw.rpartition('__HTTP__'); print('ARCHIVE_HTTP='+tail.strip()); d=json.loads(body); print('FULL_NAME='+str(d.get('full_name'))); print('ARCHIVED='+str(d.get('archived'))); print('PRIVATE='+str(d.get('private'))); print('MESSAGE='+str(d.get('message')))"
```

Puis relire l'état et la branche, sans écriture :

```bash
cred=$(printf 'protocol=https\nhost=github.com\n\n' | GIT_TERMINAL_PROMPT=0 git -c credential.interactive=never credential fill 2>/dev/null)
pass=$(printf '%s\n' "$cred" | sed -n 's/^password=//p')
unset cred
resp=$(curl -s -w '\n__HTTP__%{http_code}' \
  -H "Authorization: Bearer $pass" \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/$DEPOT")
unset pass
printf '%s' "$resp" | py -3 -c "import sys,json; raw=sys.stdin.read(); body,_,tail=raw.rpartition('__HTTP__'); print('GET_HTTP='+tail.strip()); d=json.loads(body); print('ARCHIVED='+str(d.get('archived'))); print('PRIVATE='+str(d.get('private'))); print('DEFAULT_BRANCH='+str(d.get('default_branch')))"
GIT_TERMINAL_PROMPT=0 git -C "$CIBLE" ls-remote origin "refs/heads/$BRANCHE"
printf 'LSREMOTE_EXIT=%s\n' "$?"
git -C "$CIBLE" status --porcelain=v1
git -C "$CIBLE" rev-parse HEAD
```

Critères d'acceptation :

| Contrôle | Attendu |
|---|---|
| `PATCH` | HTTP 200, `ARCHIVED=True`, `FULL_NAME` attendu |
| `GET` | HTTP 200, `ARCHIVED=True`, `PRIVATE` inchangé, `DEFAULT_BRANCH` attendu |
| `ls-remote` | `LSREMOTE_EXIT=0`, la référence reste lisible |
| local | `HEAD` inchangé, worktree toujours propre |

Si l'un de ces contrôles échoue, s'arrêter : ne pas supprimer la copie locale pour « compenser ». Un dépôt archivé est en lecture seule ; un push y échouera. Ne pas utiliser le succès d'un push comme preuve d'archivage. Pour revenir en arrière, refaire un `PATCH` avec `{"archived":false}` et vérifier par `GET`.

Le cas source n'a pas testé le code exact d'un push refusé ; le Skill ne doit donc pas affirmer « 403 » comme un fait mesuré, seulement comme comportement attendu d'un dépôt en lecture seule.

## Étape 3 — Supprimer définitivement le dépôt distant

Branche non exécutée dans le cas source ; l'appliquer seulement si l'utilisateur l'a explicitement choisie.

1. Vérifier que le jeton possède le scope `delete_repo`. Le scope `repo`, suffisant pour archiver, ne suffit pas pour supprimer un dépôt.
2. Exiger la saisie exacte de `owner/repo` et la comparer à la valeur figée.
3. Appeler `DELETE https://api.github.com/repos/$DEPOT` et attendre HTTP 204.
4. Relire avec `GET` et attendre HTTP 404.
5. Ne pas supprimer la copie locale dans la même étape : c'est un choix séparé.

Si le scope manque, s'arrêter et demander un jeton adapté. Ne pas tenter un contournement.

## Étape 4 — Détacher seulement l'origin local

Branche non exécutée dans le cas source. Après confirmation :

```bash
git -C "$CIBLE" remote remove origin
git -C "$CIBLE" remote -v
git -C "$CIBLE" status --porcelain=v1
git -C "$CIBLE" rev-parse HEAD
```

`git remote -v` doit être vide. Les commits locaux restent intacts ; le dépôt distant n'est pas modifié.

## Étape 5 — Sauvegarder puis supprimer la copie locale

### 5.1 Résoudre et garder la cible

- chemin absolu, existant, dossier, ni lien symbolique ni jonction ;
- refuser `/`, `$HOME`, `~/.qoder`, `~/.qoder/skills`, la racine du workspace, et tout ancêtre de la sauvegarde ;
- refuser les sous-modules et worktrees ; demander au lieu de supposer qu'une copie simple est complète ;
- si la cible est un dépôt Git, exiger `git status --porcelain=v1` vide. Une sauvegarde ne prouve pas le contenu non commité : demander un commit ou un stash avant de continuer.

Noter `NOM` (nom du dossier), `HEAD`, le nombre de commits et le SHA-256 de `SKILL.md` s'il existe.

### 5.2 Copier tout le dossier, y compris `.git`

```bash
CIBLE="C:/Users/Administrateur/.qoder/skills/nom-du-skill"
NOM="$(basename "$CIBLE")"
SAUVEGARDE="$HOME/.qoder/tmp/${NOM}-deleted-$(date -u +%Y%m%dT%H%M%SZ)"
[ -e "$SAUVEGARDE" ] && { echo "BACKUP_EXISTS=yes"; exit 1; }
mkdir -p "$SAUVEGARDE"
cp -a "$CIBLE/." "$SAUVEGARDE/"
printf 'COPY_EXIT=%s\n' "$?"
```

Le `/.` est important : il copie aussi les fichiers cachés, dont `.git`. Ne pas utiliser `mv` comme sauvegarde : un déplacement ne constitue pas une copie indépendante.

### 5.3 Vérifier la sauvegarde avant de supprimer

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/retirer-depot-github-et-copie-locale/scripts/verifier_copie_locale.py" \
  --source "$CIBLE" --backup "$SAUVEGARDE"
```

Attendre `RESULT PASS` et :

- `FILES_MATCH=yes`, avec `SRC_FILES_ALL` = `BAK_FILES_ALL` (fichiers cachés et `.git` compris) ;
- `CONTENT_HASH_MATCH=yes` (contenu hors `.git`) ;
- `SKILL_SHA256_MATCH=yes` si `SKILL.md` existe ;
- `GIT_PRESENT_MATCH=yes`, puis `HEAD_MATCH=yes` et `COMMITS_MATCH=yes` pour un dépôt Git ;
- `SRC_STATUS_CLEAN=yes` et `BAK_STATUS_CLEAN=yes`.

Si un contrôle échoue, ne pas supprimer. Recopier ou s'arrêter et demander.

### 5.4 Supprimer sous garde de chemin exact

La garde est une seconde barrière, pas la confirmation. Le chemin doit être exactement celui que l'utilisateur a validé.

```bash
CIBLE_ATTENDU="C:/Users/Administrateur/.qoder/skills/nom-du-skill"
case "$CIBLE" in
  "$CIBLE_ATTENDU")
    rm -rf "$CIBLE" && echo "DELETE_EXIT=0" || echo "DELETE_EXIT=1"
    ;;
  *)
    echo "GUARD_FAIL: unexpected target"
    exit 1
    ;;
esac
[ -e "$CIBLE" ] && echo "EXISTS=yes" || echo "EXISTS=no"
```

Ne jamais assouplir la garde avec un joker, une variable non validée ou un chemin reconstruit après coup.

### 5.5 Prouver l'absence et l'intégrité de la sauvegarde

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/retirer-depot-github-et-copie-locale/scripts/verifier_copie_locale.py" \
  --backup "$SAUVEGARDE" \
  --expect-absent "$CIBLE" \
  --name "$NOM" \
  --skills-root "$HOME/.qoder/skills" \
  --skills-root "$WORKSPACE/.qoder/skills"
```

Ne passer que les racines qui existent : une racine explicite absente est traitée comme une erreur d'usage (exit 2). Si une racine n'existe pas, l'omettre et le noter dans le rapport.

Attendre `RESULT PASS`, `TARGET_EXISTS=no`, `REMAINING_COPIES=0`, et une sauvegarde encore lisible. Vérifier aussi :

```bash
git -C "$SAUVEGARDE" rev-parse HEAD
git -C "$SAUVEGARDE" status --porcelain=v1
```

Si une copie homonyme subsiste dans une autre racine, la signaler sans la supprimer : elle peut appartenir à une autre installation ou à une autre session.

### 5.6 Cas du workspace projet

Branche non exécutée dans le cas source. Elle est plus risquée :

- exiger la saisie du chemin absolu complet et le comparer ;
- refuser les racines et les dossiers système ;
- vérifier qu'aucune session n'écrit encore ;
- sauvegarder hors du workspace, dans `~/.qoder/tmp`, avant toute suppression ;
- appliquer les mêmes contrôles de fichiers, de hash et d'absence ;
- documenter la restauration avant de supprimer.

## Étape 6 — Nettoyer les sauvegardes

Ne supprimer que le chemin exact de la sauvegarde, après une confirmation séparée. Avant de supprimer, lister les dossiers voisins qui partagent le préfixe :

```bash
find "$HOME/.qoder/tmp" -maxdepth 1 -type d -name "${NOM}-*" -printf '%f\n' | sort
```

Ces dossiers peuvent appartenir à une autre session. Les lister et demander ; ne jamais les balayer par préfixe. Utiliser une garde de chemin exact, puis vérifier `EXISTS=no` et `REMAINING_COUNT=0` pour la cible exacte.

Si l'utilisateur demande explicitement de nettoyer les autres dossiers, inspecter leur contenu d'abord et obtenir une instruction nominative.

## Étape 7 — Cache runtime de la liste des Skills

La liste des Skills de la session peut encore afficher un Skill supprimé : c'est un cache runtime. Vérifier d'abord l'absence sur disque, puis exécuter `/skills reload`. Ne pas conclure que la suppression a échoué parce que la liste affiche encore l'ancien nom.

## Tableau des échecs

| Symptôme | Cause probable | Action |
|---|---|---|
| `PATCH` 401/403/404 | jeton absent, scope insuffisant, mauvais `owner/repo` | s'arrêter ; ne pas supprimer le local |
| `GET` renvoie `ARCHIVED=False` après le PATCH | écriture non appliquée ou mauvaise cible | s'arrêter et relire |
| `BACKUP_EXISTS=yes` | sauvegarde du même nom déjà présente | choisir un autre nom ; ne pas écraser |
| `SRC_FILES_ALL` différent de `BAK_FILES_ALL` | copie incomplète, `.git` omis, écriture concurrente | ne pas supprimer ; recopier |
| `CONTENT_HASH_MATCH=no` | fichier modifié pendant la copie | ne pas supprimer ; relire et recommencer |
| `SKILL_SHA256_MATCH=no` | `SKILL.md` différent dans la sauvegarde | ne pas supprimer |
| `HEAD_MATCH=no` | `.git` incomplet ou copie partielle | ne pas supprimer |
| worktree sale | modifications non commitées | demander commit/stash ; ne pas supprimer |
| `GUARD_FAIL` | chemin différent de la cible confirmée | s'arrêter ; ne jamais contourner |
| `REMAINING_COPIES>0` après suppression | autre installation ou copie de travail | signaler ; ne pas supprimer sans instruction |
| liste des Skills encore visible | cache runtime | vérifier le disque, puis `/skills reload` |
| push refusé après archivage | dépôt archivé en lecture seule | désarchiver avant de pousser ; comportement attendu, non mesuré dans le cas source |
| sous-module, worktree ou lien | copie non triviale | s'arrêter et demander |

## Checklist de clôture

- [ ] Les réponses de l'`AskUserQuestion` sont consignées.
- [ ] L'état distant a été figé avant l'action.
- [ ] `PATCH` et `GET` concordent sur `archived`, `private` et `default_branch`.
- [ ] La cible locale exacte et sa nature sont confirmées.
- [ ] Le worktree est propre, ou l'opération est arrêtée.
- [ ] La sauvegarde est hors cible et contient `.git`.
- [ ] Nombre de fichiers, hash de contenu, hash de `SKILL.md`, `HEAD` et propreté concordent.
- [ ] La suppression a utilisé la garde de chemin exact.
- [ ] `EXISTS=no` et `REMAINING_COPIES=0` sont prouvés.
- [ ] La sauvegarde reste lisible et la restauration est documentée.
- [ ] Le nettoyage des sauvegardes n'a visé que le chemin exact autorisé.
- [ ] La note `/skills reload` est fournie.
- [ ] Les branches non exécutées sont signalées comme non vérifiées.

## Ressources

- `scripts/verifier_copie_locale.py` : vérificateur en lecture seule ; compare source et sauvegarde, puis vérifie l'absence et les copies homonymes. Il ne supprime jamais rien.
- `references/cas-verifie-2026-10-26.md` : transcription du cas source, commandes observées, valeurs vérifiées et branches non exécutées.
