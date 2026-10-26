---
name: nettoyer-branches-refs-git
description: "Inventorier, classer et supprimer sans risque les branches obsolètes d'un dépôt Git partagé, puis distinguer les refs orphelines des objets inaccessibles et élaguer ces derniers : merge-base --is-ancestor, rev-list --count, inspection du contenu unique, capture des tips, suppression distante puis locale, vérification de main, pseudo-refs, verrous, worktrees, reflog expire --expire-unreachable=now --all puis gc --prune=now et fsck. Utiliser pour « supprimer les branches obsolètes », « nettoyer les refs orphelines », élaguer des commits inaccessibles, upstream gone, branche non fusionnée refusée par git branch -d, gc qui ne supprime rien, dépôt partagé avec sessions concurrentes. 中文触发：清理过期分支、删除远程分支、清理孤立 ref、不可达对象、reflog 过期、gc 无效、共享仓库并发操作。"
---

# Nettoyer branches et refs d'un dépôt Git partagé

## Objectif

Réduire le bruit dans un dépôt Git sans perdre de travail : inventorier les refs, classer les branches, supprimer seulement celles qui sont prouvées obsolètes, puis traiter séparément les refs cassées et les objets inaccessibles. La suppression d'une branche est réversible tant que son tip est consigné ; l'élagage des objets ne l'est pas.

## Déclencheurs

- « supprimer les branches obsolètes », « nettoyer les refs orphelines » ;
- branches `skill/*`, `merge/*` ou `archive/*` accumulées après des publications ;
- upstream `[gone]`, branche locale dont la distante a été supprimée ;
- `git branch -d` refuse une branche « not fully merged » ;
- `git gc --prune=now` réussit mais `git fsck` montre encore des objets inaccessibles ;
- dépôt partagé : une autre session peut changer HEAD, créer des commits ou pousser pendant l'opération.

## Règles non négociables

1. **Lire avant d'écrire.** Inventaire en lecture seule, puis liste explicite des cibles. Aucune suppression par motif, boucle ou `xargs`.
2. **Consigner chaque tip complet** avant toute suppression, avec commande de restauration.
3. **Ne jamais faire de checkout pour supprimer.** Utiliser `git -C "<dépôt>"` et nommer les branches ; la branche courante d'une autre session ne doit pas bouger.
4. **Distante d'abord, locale ensuite.** Si le push de suppression échoue, ne pas supprimer la locale.
5. **`-d` par défaut, `-D` seulement après inspection.** `-D` contourne le contrôle de fusion : il exige `rev-list --count` et `show --stat` sur le contenu unique.
6. **Confirmation explicite avant tout élagage irréversible.** Lister les commits, leur date, leur sujet et l'effet de la perte. Sans accord, s'arrêter au diagnostic.
7. **Ne pas confondre** ref orpheline (ref qui ne résout pas ou suivi distant périmé) et objet inaccessible (commit/arbre/blob sans ref).
8. **Ne pas toucher** aux branches actives, aux worktrees d'autres sessions, aux tags de release, ni à une branche sans rapport.

## Étape 0 — Figer la scène

### Relever l'état initial

```bash
R="<chemin absolu du dépôt>"
git -C "$R" rev-parse --show-toplevel
git -C "$R" rev-parse --abbrev-ref HEAD
git -C "$R" rev-parse HEAD
git -C "$R" status --porcelain=v1
git -C "$R" worktree list
git -C "$R" log --oneline -3
```

### Ce qu'il faut noter

Noter : branche courante, OID de `main`, OID de HEAD, worktrees, état du répertoire de travail. Si le dépôt est partagé, considérer que ces valeurs peuvent changer à tout moment et les réinventorier après chaque action.

## Étape 1 — Inventorier les refs

### Script en lecture seule

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/nettoyer-branches-refs-git/scripts/inspect_refs_state.py" "$R"
```

Si le Skill est installé ailleurs, remplacer le préfixe de ce chemin par le dossier réel du Skill.

Le script est en lecture seule : il ne fetche pas, ne modifie ni index ni refs. Il affiche par dépôt la branche courante, le statut, les worktrees, les branches locales et distantes avec leur ascendance par rapport à `main`, les upstream `[gone]`, les pseudo-refs, les verrous, les anomalies `fsck` et les objets inaccessibles. Codes de sortie : `0` lecture complète, `2` au moins un chemin invalide (`RESULT PARTIAL` si d'autres dépôts ont été lus).

### Balayage multi-dépôts

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/nettoyer-branches-refs-git/scripts/inspect_refs_state.py" \
  --discover "<racine-workspace>" \
  --discover "C:/Users/Administrateur/.qoder/skills"
```

### Équivalent manuel

Si le fetch est accepté :

```bash
git -C "$R" fetch origin --prune
git -C "$R" branch -vv
git -C "$R" branch -r
for b in <branche1> <branche2>; do
  if git -C "$R" merge-base --is-ancestor "$b" main; then a="contenue"; else a="NON-contenue"; fi
  echo "$b $a uniques=$(git -C "$R" rev-list --count "main..$b")"
done
```

`fetch --prune` met à jour les refs de suivi et peut supprimer `origin/<branche>` localement. L'annoncer. Sans fetch, un upstream `[gone]` peut être périmé.

## Étape 2 — Classer et inspecter le contenu unique

### Classer les branches

| Classe | Critère | Décision |
|---|---|---|
| ACTIVE | HEAD, worktree, session en cours, commits uniques non archivés | conserver |
| CONTENUE | `merge-base --is-ancestor` vrai, `rev-list --count main..b` = 0 | candidate |
| REMPLACÉE | commits uniques, mais contenu déjà présent dans `main` | candidate après preuve |
| SANS RAPPORT | autre Skill, autre projet, tag de release | conserver |

### Prouver le contenu unique

Inspecter chaque candidate :

```bash
git -C "$R" show --stat --oneline <tip> | head -20
git -C "$R" ls-tree -r --name-only <tip> -- <chemin>
git -C "$R" diff --stat main..<branche>
git -C "$R" rev-list --count main..<branche>
```

Une branche « REMPLACÉE » doit être prouvée : mêmes chemins et même contenu que `main`, ou archive explicitement dépassée. Un diff non vide n'est pas une preuve d'obsolescence.

## Étape 3 — Confirmer et consigner les tips

### Consigner les tips

```bash
mkdir -p "C:/Users/Administrateur/.qoder/tmp"
for b in <branche1> <branche2>; do
  printf '%s %s\n' "$b" "$(git -C "$R" rev-parse "$b")"
done | tee "C:/Users/Administrateur/.qoder/tmp/tips-<date>.txt"
```

### Obtenir l'accord explicite

Présenter à l'utilisateur : branches distantes supprimées, branches locales supprimées, branches conservées, tips complets, et le fait que l'élagage ultérieur rendra ces tips irrécupérables. Attendre un accord explicite.

### Restaurer un tip

Tant que les objets existent :

```bash
git -C "$R" branch <nom> <tip>
git -C "$R" push origin <tip>:refs/heads/<nom>
```

## Étape 4 — Supprimer les branches

### Ordre des suppressions

```bash
git -C "$R" push origin --delete <branche1> <branche2>
git -C "$R" branch -d <branche1> <branche2>
```

### Cas particuliers

- `-d` peut refuser une branche pourtant contenue dans `main` : Git la compare aussi à son upstream. Cas reproduit en fixture — branche créée avec `--track origin/main`, fusionnée dans `main` local mais pas encore poussée : `warning: not deleting branch ... that is not yet merged to 'refs/remotes/origin/main', even though it is merged to HEAD` puis `error: the branch ... is not fully merged`, code 1. Pousser `main` d'abord ; sinon `-D` seulement après `rev-list --count main..b` et `show --stat` sur le contenu unique.
- Ne jamais supprimer la branche courante ni une branche cochée dans un worktree : Git le refuse, ne pas forcer.
- Si le push échoue (droits, réseau, branche déjà absente), s'arrêter, `fetch --prune`, réinventorier. Une branche déjà supprimée par une autre session n'est pas une erreur de suppression, mais elle doit être vérifiée.
- Cas observé : suppression pendant qu'une autre session commitait ; `git -C` et des noms explicites ont évité de toucher sa branche.

## Étape 5 — Vérifier après suppression

### Commandes de vérification

```bash
git -C "$R" fetch origin --prune
git -C "$R" branch -vv
git -C "$R" branch -r
git -C "$R" ls-remote --heads origin
git -C "$R" rev-parse main origin/main
git -C "$R" status --porcelain=v1
git -C "$R" reflog -5 --date=iso
```

### Contrôles attendus

- cibles absentes en local et sur le distant ;
- branches conservées toujours présentes ;
- worktrees intacts ;
- `main` égal à son OID initial **ou** descendant de celui-ci : `git -C "$R" merge-base --is-ancestor <main-avant> main`. Un `main` non descendant signale une réécriture par un tiers : s'arrêter.
- une avance de `origin/main` pendant l'opération est un mouvement concurrent, pas un échec : identifier l'auteur du commit dans le reflog et vérifier son contenu.

## Étape 6 — Diagnostiquer les refs résiduelles

### Commandes de diagnostic

```bash
G="$(git -C "$R" rev-parse --absolute-git-dir)"
C="$(git -C "$R" rev-parse --git-common-dir)"
case "$C" in [A-Za-z]:/*|/*) ;; *) C="$R/$C" ;; esac
git -C "$R" for-each-ref --format='%(refname) %(objectname:short) %(upstream:track)'
git -C "$R" worktree list
git -C "$R" fsck --full --no-reflogs
for f in ORIG_HEAD MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD BISECT_START AUTO_MERGE; do
  [ -f "$G/$f" ] && echo "pseudo-ref $f"
done
find "$G" "$C" -name '*.lock' -print | sort -u
git -C "$R" for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads | grep '\[gone\]' || true
```

`G` est le répertoire Git du worktree courant, `C` le répertoire commun. `packed-refs` et les verrous de refs vivent dans `C` ; `index.lock` et les pseudo-refs dans `G`. Un worktree lié a un `.git` fichier : ne pas supposer que `G` est le dossier `.git` du dépôt principal.

### Interpréter les constats

| Constat | Interprétation | Action |
|---|---|---|
| `for-each-ref` échoue, `fsck` dit `unable to resolve` / `missing` | ref cassée | restaurer la cible si possible ; supprimer la ref seulement avec accord |
| upstream `[gone]` | la distante a été supprimée | vérifier le contenu, puis supprimer la locale si obsolète |
| `ORIG_HEAD` ou autre pseudo-ref périmée | trace d'une opération passée | retirer seulement si sa cible est atteignable ailleurs |
| `.lock` présent | opération en cours ou verrou résiduel | chercher le processus ; ne pas supprimer à l'aveugle |
| branche dans `worktree list` | utilisée par un autre répertoire | ne pas supprimer ; retirer le worktree seulement avec accord |
| `refs/stash`, `refs/notes`, `refs/replace`, `refs/original` | refs intentionnelles | ne pas supprimer sans connaître leur propriétaire |
| répertoires vides sous `.git/refs` | résidus inoffensifs | ignorer |
| `fsck` liste `dangling commit/tree/blob` | objets inaccessibles, pas des refs orphelines | étape 7 |
| `remote prune` renvoie `Repository not found` | URL ou authentification du remote, pas une corruption | corriger le remote, ne pas toucher aux refs |

Si toutes les refs résolvent, le rapport doit le dire : « aucune ref orpheline ». Ne pas fabriquer une suppression pour répondre à la demande.

## Étape 7 — Élaguer les objets inaccessibles

### Avant d'élaguer

Préconditions : accord explicite, tips consignés, aucune session active dans le dépôt, répertoire de travail propre. Signaler à part tout commit inaccessible qui ressemble à une release, un tag ou une publication (date, sujet, DOI) : il ne doit pas disparaître dans une liste de résidus ordinaires.

### Commandes d'élagage

```bash
G="$(git -C "$R" rev-parse --absolute-git-dir)"
git -C "$R" rev-parse HEAD
git -C "$R" for-each-ref --format='%(refname) %(objectname)' > "C:/Users/Administrateur/.qoder/tmp/refs-avant-<date>.txt"
git -C "$R" count-objects -vH

# Optionnel : retirer une pseudo-ref périmée identifiée à l'étape 6
rm -f "$G/ORIG_HEAD"

git -C "$R" reflog expire --expire-unreachable=now --all
git -C "$R" gc --prune=now
```

### Vérifier l'élagage

```bash
git -C "$R" fsck --full --no-reflogs --unreachable
git -C "$R" fsck --full
git -C "$R" count-objects -vH
for c in <tip1> <tip2>; do
  git -C "$R" cat-file -e "$c" 2>/dev/null && echo "$c PRESENT" || echo "$c absent"
done
```

Attendu : zéro ligne `unreachable`, `fsck --full` sans erreur, tips absents, branche courante, `main` et worktrees inchangés.

**Piège vérifié :** `git gc --prune=now` seul peut sortir avec le code 0 tout en laissant les objets inaccessibles, car les reflogs les retiennent. Cas observé : premier `gc` sans effet, puis `reflog expire --expire-unreachable=now --all` + `gc --prune=now` → 437 → 416 objets, 0 inaccessible, `fsck` code 0. Ne pas conclure à l'échec de `gc` avant d'avoir expiré les reflogs.

### Irréversibilité

L'élagage est irréversible : après lui, `git branch <nom> <tip>` ne restaure plus rien. Un tag ou une branche distante encore présente maintient l'objet accessible ; le retrait d'un tag de release est une opération distincte et plus destructrice, à confirmer séparément.

## Table des erreurs observées

| Symptôme | Cause | Réponse |
|---|---|---|
| `gc --prune=now` laisse des `unreachable` | reflogs retiennent les commits | `reflog expire --expire-unreachable=now --all` puis `gc` |
| `branch -d` refuse « not fully merged » | upstream (`refs/remotes/origin/main`) ne contient pas la branche, ou commits uniques | vérifier `rev-list --count main..b` et `show --stat` ; pousser `main` si la branche est déjà fusionnée, sinon `-D` confirmé |
| HEAD ou branche courante change en cours d'opération | session concurrente | `git -C`, réinventaire, ne pas checkout |
| `main` avance après la suppression | commit/push concurrent | vérifier l'ascendance et le contenu, ne pas reset |
| `fsck` montre des `dangling commit` | objets inaccessibles | étape 7, avec accord |
| `push --delete` échoue | droits, réseau, ref déjà absente | arrêter, `fetch --prune`, vérifier le distant |
| verrou `.lock` inattendu | opération concurrente ou crash | identifier le processus, ne pas supprimer sans preuve |
| suppression d'une branche de worktree refusée | branche cochée ailleurs | retirer le worktree avec accord, puis supprimer |
| branche supprimée réapparaît | une autre session l'a repoussée | coordonner, ne pas boucler |
| `Repository not found` sur un remote | URL ou authentification | corriger le remote, ne pas toucher aux refs |

## Checklist finale

- [ ] inventaire en lecture seule exécuté et rapporté ;
- [ ] classes ACTIVE / CONTENUE / REMPLACÉE / SANS RAPPORT justifiées ;
- [ ] tips complets consignés et restauration documentée ;
- [ ] accord explicite avant suppression et avant élagage ;
- [ ] suppression distante puis locale, cibles nommées une à une ;
- [ ] branches conservées, worktrees et `main` vérifiés (égal ou descendant) ;
- [ ] refs cassées et upstream `[gone]` traités séparément des objets inaccessibles ;
- [ ] reflogs expirés avant `gc`, `fsck` sans erreur, zéro `unreachable` ;
- [ ] rapport distinguant ce qui a été supprimé, conservé et rendu irrécupérable.

## Ressources

- `scripts/inspect_refs_state.py` — inventaire multi-dépôts en lecture seule, sortie UTF-8, codes 0/2 ; `packed-refs` et verrous sont lus dans le répertoire Git commun, y compris pour un worktree lié.
- `references/preuves-nettoyage-2026-10-26.md` — commandes et sorties vérifiées de la session source, y compris l'échec du premier `gc` et les mouvements concurrents.
