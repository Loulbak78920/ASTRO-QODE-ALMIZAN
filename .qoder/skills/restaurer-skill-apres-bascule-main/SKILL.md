---
name: restaurer-skill-apres-bascule-main
description: "Réparer un Skill installé dont le dossier est un dépôt Git et dont main porte l'arbre du monorepo : créer main en suivant origin/main sans basculer, sécuriser HEAD, basculer avec git switch main, constater la réécriture du worktree (SKILL.md racine remplacé par un autre Skill, references/ et .gitattributes disparus, i/lf w/crlf et SHA-256 différents des blobs validés à cause de core.autocrlf), puis restaurer chaque fichier racine depuis les blobs LF de main via ls-tree et cat-file blob, vérifier SHA-256, CR=0 et frontmatter, laisser les changements non commités, déléguer commit/QA/runtime. Utiliser pour basculer sur main, git switch main dans un dossier Skill, restaurer les fichiers du Skill à la racine, Skill cassé après checkout, main monorepo, leaving N commits behind, CRLF après checkout, .gitattributes disparu. 中文触发：Skill 目录切换 main 后被换掉、恢复 Skill 根文件、checkout 后 references 消失、CRLF 导致哈希漂移、main 是 monorepo。English: restore skill after main checkout."
---

# Réparer un Skill après bascule sur `main`

## Objectif

Quand le dossier d'installation d'un Skill est lui-même un dépôt Git et que `main` porte l'arbre du projet (Skill archivé sous `.qoder/skills/<nom>/`), `git switch main` réécrit tout le worktree. Le Skill installé devient alors un autre Skill. Cette procédure constate la casse, restaure les fichiers racine à l'octet près depuis les blobs de `main`, et laisse un état vérifiable sans commit ni push implicite.

## Déclencheurs

- L'utilisateur demande de basculer sur `main`, ou de restaurer les fichiers du Skill à la racine après une bascule.
- Le `SKILL.md` racine porte un `name` différent du nom du dossier.
- `references/` ou `.gitattributes` ont disparu après un checkout, alors que `git status` est propre.
- `git ls-files --eol` affiche `i/lf w/crlf` et les SHA-256 locaux diffèrent des valeurs validées.
- `main` contient l'arbre du monorepo et le Skill n'existe que sous `.qoder/skills/<nom>/`.

## Modèle mental

- `main` décrit le projet ; le Skill installé à la racine est une vue locale distincte.
- `git switch main` remplace le contenu du dossier, il ne « met pas à jour » le Skill.
- Un `git status` propre prouve seulement que le worktree correspond à `main` ; il ne prouve pas que le Skill est intact.
- Les blobs de `main` peuvent être corrects alors que les fichiers extraits ne le sont pas : `core.autocrlf=true` convertit LF en CRLF au checkout, donc SHA-256 disque ≠ SHA-256 du blob.
- La copie présente sous `.qoder/skills/<nom>/` après la bascule est elle aussi convertie en CRLF : elle n'est pas une source byte-exacte.
- Les commits locaux non poussés ne sont retenus que par HEAD ou le reflog s'ils ne sont référencés par aucune branche ; un `gc` peut les détruire.
- Un merge ou un pull en avance rapide réécrit le worktree comme un checkout : les SHA-256 disque peuvent revenir aux valeurs CRLF alors que les OID de blobs et l'arbre n'ont pas changé. Ne pas relancer la restauration sur la seule différence de hash.

## Règles non négociables

1. Prendre la preuve en lecture seule avant toute écriture ; la bascule exige un accord explicite.
2. Identifier la source de vérité (blob de `main` ou blob du HEAD local) et comparer les octets, pas les fichiers du worktree.
3. Ne jamais utiliser `git checkout .`, `git reset --hard`, ni `git checkout main -- <chemin>` pour réparer : ces commandes réappliquent le filtre de fin de ligne.
4. Restaurer uniquement par écriture des octets d'un blob (`git cat-file blob <oid> > <fichier>`).
5. Ne pas committer ni pousser sans demande ; un commit de restauration se fait sur une branche dédiée, jamais directement sur `main`.
6. Ne pas exécuter `git reflog expire --expire-unreachable=now --all` ni `git gc --prune=now` avant que la restauration soit commitée ou poussée. Cas observé : six commits, dont trois uniquement locaux, ont été détruits ainsi.
7. `.gitattributes` n'est restauré qu'avec accord explicite ; sans lui, un futur checkout reconvertira en CRLF.
8. Distinguer dans le rapport ce qui est observé, ce qui est déduit et ce qui reste non vérifié.

## Procédure

### Étape 0 — Prendre la preuve (lecture seule)

```bash
cd "<dossier-skill>"
git rev-parse --show-toplevel
git status -sb
git branch -vv
git remote -v
git config --get core.autocrlf || echo "core.autocrlf: unset"
git rev-parse HEAD
git for-each-ref --format='%(refname:short)' refs/heads/
git rev-parse --verify "HEAD:.gitattributes" 2>/dev/null || echo "GITATTR_ABSENT"
sha256sum SKILL.md references/* 2>/dev/null
```

Le shell peut revenir à un autre répertoire entre deux appels : refaire le `cd` ou employer `git -C "<dossier-skill>"` à chaque commande.

Consigner : racine réelle du dépôt, HEAD, branches, `core.autocrlf`, OID de `.gitattributes`, SHA-256 de chaque fichier, et les empreintes validées par un `skill-file-qa` antérieur. Sans empreinte de référence, s'arrêter : il n'y a rien à comparer.

### Étape 1 — Choisir la source de restauration

```bash
# blob de l'archive sur main
git ls-tree main -- ".qoder/skills/<nom>/SKILL.md"
# ou blob du HEAD local, si les octets validés y sont encore
git ls-tree HEAD -- "SKILL.md"
# comparer les octets du blob aux empreintes validées
git cat-file blob "<oid>" | sha256sum
```

- Si `main` contient les octets validés, c'est la source préférée.
- Sinon, utiliser le blob du HEAD local s'il correspond aux empreintes.
- Si aucun ne correspond, s'arrêter et demander la source ; ne pas « réparer » avec la copie CRLF.

### Étape 2 — Créer `main` sans basculer

```bash
git fetch origin
git branch --track main origin/main
git rev-parse main origin/main
```

`git branch --track` crée la branche sans toucher au worktree. Vérifier que `main` et `origin/main` ont le même OID, et que HEAD, les fichiers et `.gitattributes` sont inchangés. C'est le seul moment sûr pour relever l'OID de `.gitattributes`.

### Étape 3 — Sécuriser puis basculer

```bash
git branch rescue/<nom> HEAD     # si HEAD porte des commits non poussés
git status --porcelain           # doit être vide
git switch main; echo "SWITCH_EXIT=$?"
```

- Le worktree doit être propre ; sinon s'arrêter.
- L'avertissement `leaving N commits behind` n'apparaît que si les anciens commits ne sont référencés par aucune branche. Sa présence prouve un risque ; son absence ne prouve rien (la branche `rescue/` le fait disparaître par construction).
- Consigner l'ancien OID de HEAD et le tip de `rescue/<nom>`.

### Étape 4 — Constater la casse

```bash
git rev-parse --abbrev-ref HEAD
ls -A
sed -n '1,3p' SKILL.md
git ls-files --eol -- ".qoder/skills/<nom>/SKILL.md"
git status --porcelain
sha256sum ".qoder/skills/<nom>/SKILL.md"
```

Attendu dans le cas visé : branche `main` ; racine contenant le `SKILL.md` d'un autre Skill et d'éventuels répertoires de scripts ; `references/` et `.gitattributes` absents ; archive présente sous `.qoder/skills/<nom>/` ; `i/lf w/crlf` ; SHA-256 de l'archive différent de l'empreinte validée et nombre de CR positif.

### Étape 5 — Restaurer depuis les blobs

```bash
read -r _mode _type oid _path <<< "$(git ls-tree main -- ".qoder/skills/<nom>/SKILL.md")"
[ -n "$oid" ] && [ "$(git cat-file -t "$oid")" = blob ] || { echo "FAIL: blob introuvable"; exit 1; }
git cat-file blob "$oid" > SKILL.md

mkdir -p references
read -r _mode_ref _type_ref oid_ref _path_ref <<< "$(git ls-tree main -- ".qoder/skills/<nom>/references/<fichier>.md")"
[ -n "$oid_ref" ] && [ "$(git cat-file -t "$oid_ref")" = blob ] || { echo "FAIL: blob introuvable"; exit 1; }
git cat-file blob "$oid_ref" > "references/<fichier>.md"
```

Contrôles immédiats :

```bash
sha256sum SKILL.md "references/<fichier>.md"
tr -cd '\r' < SKILL.md | wc -c
tr -cd '\r' < "references/<fichier>.md" | wc -c
sed -n '1,3p' SKILL.md
git status --porcelain
```

- Les SHA-256 doivent égaler les empreintes validées et les compteurs de CR valoir `0`.
- Le `name` du frontmatter doit égaler le nom du dossier.
- `git status` doit montrer `M SKILL.md` et `?? references/` (plus `?? .gitattributes` si restauré).
- Ne pas recopier l'archive imbriquée : elle est en CRLF.
- Ne pas utiliser `git checkout main -- <chemin>` : le filtre réapplique CRLF.
- Lister les fichiers ajoutés par `main` qui ne font pas partie du Skill et les signaler ; ne rien supprimer sans accord.

### Étape 5 bis — Variante scriptée (dry-run par défaut)

`scripts/restaurer_archive.py` applique la même règle sans shell : il lit chaque fichier par `git cat-file blob`, refuse les chemins non sûrs, les cibles symboliques et les caches, puis classe l'état (`SAME`, `EOL_ONLY`, `MISSING`, `DIFF`).

```bash
py -3 scripts/restaurer_archive.py --repo "<racine-dépôt>" --skill "<nom>" --ref main          # dry-run
py -3 scripts/restaurer_archive.py --repo "<racine-dépôt>" --skill "<nom>" --ref main --apply  # écrit
```

- Dry-run par défaut ; `--apply` écrit en atomique (`os.replace`) puis relit chaque fichier.
- Ne touche ni l'index, ni les branches, ni HEAD ; ne commite ni ne pousse.
- Codes de sortie : `0` succès, `1` refus ou vérification échouée, `2` usage ou environnement.
- `RESULT DRY_RUN_OK ... would_change=<n>` précède l'écriture ; `RESULT APPLIED_OK ... changed=<n> verified=<n>` la suit.
- `--repo` doit être la racine exacte du dépôt et l'archive doit contenir `SKILL.md`.
- Le script ne remplace pas les contrôles d'empreintes : comparer les `sha256=` affichés aux valeurs validées avant `--apply`.

### Étape 6 — `.gitattributes` (sur autorisation)

```bash
git cat-file blob "<attr_oid>" > .gitattributes
sha256sum .gitattributes
git check-attr -a SKILL.md
```

- Restaurer seulement si l'utilisateur accepte, et seulement depuis l'OID relevé à l'étape 0 ou 2.
- Avant tout ménage de refs, sauvegarder le contenu du blob : après un `gc`, un OID non référencé peut disparaître.
- Pour figer durablement les fins de ligne, passer ensuite par `lock-lf-endings-skill-repo` plutôt que d'improviser.

### Étape 7 — État final et rapport

État attendu par défaut : branche `main`, restauration non commitée, `.gitattributes` absent sauf autorisation, les scripts de `main` toujours présents. Rapporter : ancien HEAD, branche `rescue/`, OID de `main`, OID des blobs, SHA-256 avant/après, compteurs CR, fichiers hors périmètre, et statut de `.gitattributes`.

### Étape 8 — Validation et remise

- Si un commit est demandé, créer la branche depuis `main` et ajouter les fichiers par chemin explicite :

```bash
git switch -c restore/<nom>
git add -- SKILL.md references/<fichier>.md
git ls-files -s -- SKILL.md references/<fichier>.md
git ls-tree main -- ".qoder/skills/<nom>/SKILL.md" ".qoder/skills/<nom>/references/<fichier>.md"
git rev-parse main origin/main
```

- L'OID indexé (deuxième colonne de `ls-files -s`) doit égaler l'OID du blob de `main` pour chaque fichier.
- Après le commit, comparer `git ls-tree HEAD -- <chemins>` aux OID de `main`, puis vérifier que `main` et `origin/main` n'ont pas bougé.
- Ne jamais committer sur `main` ni pousser sans demande. L'avertissement `LF will be replaced by CRLF` est attendu avec `core.autocrlf=true` et ne signale pas une corruption de l'index.
- Remettre la livraison à `commit-skill-work`.
- Valider le paquet avec `skill-file-qa` ; vérifier la liaison runtime avec `verify-skill-runtime-binding` ; pour l'écart HEAD/worktree, utiliser `verify-skill-git-head-vs-worktree`.
- Pour tout ménage de reflog, `gc` ou branches, remettre à `nettoyer-branches-refs-git` et attendre que la restauration soit poussée.

## Erreurs et pièges

| Symptôme | Cause | Action |
|---|---|---|
| `git status` propre mais `SKILL.md` racine est un autre Skill | `git switch main` a réécrit tout le worktree | ne pas se fier au statut ; restaurer depuis les blobs |
| `i/lf w/crlf` et SHA-256 différent de l'empreinte validée | `core.autocrlf=true` convertit au checkout | comparer les octets du blob ; restaurer en LF |
| `leaving N commits behind` absent | les anciens commits sont encore référencés (branche `rescue/`) | ce n'est pas un échec ; vérifier le tip de la branche |
| commits locaux introuvables après la bascule | aucune branche ne les référence ; seul le reflog les retient | créer une branche `rescue/` avant la bascule ; ne pas lancer `gc` |
| `.gitattributes` absent après la bascule | il n'était pas sur `main` | le restaurer depuis son OID avec accord, sinon signaler la reconversion future |
| l'archive imbriquée a un SHA-256 différent | extraite par checkout, donc CRLF | ne jamais la recopier à la racine |
| après un merge ou un pull en avance rapide, les SHA-256 disque reviennent aux valeurs CRLF | la mise à jour réécrit le worktree et réapplique le filtre EOL | comparer les OID de blobs ; si l'arbre est inchangé, ne pas restaurer |
| un merge place le contenu dans `.qoder/skills/<nom>/` et supprime la racine | Git interprète un renommage `SKILL.md → .qoder/skills/<autre>/SKILL.md` | refaire la fusion avec `merge.renames=false` et résoudre le `modify/delete` en gardant la racine |
| `git checkout main -- <chemin>` « répare » puis re-convertit | le filtre eol s'applique | utiliser `git cat-file blob` |
| commit de restauration sur `main` | bascule + réparation dans la même branche | créer `restore/<nom>` et livrer par PR |
| `origin/main` a avancé | autre session ou livraison concurrente | `git fetch` et recommencer la comparaison ; ne pas forcer |
| le code injecté diffère du disque (un mot des arguments apparaît à la place d'un champ) | une variable positionnelle numérique littérale dans le paquet est substituée par le N-ième argument à l'appel | n'en employer aucune : `git ls-tree` + `read -r` dans des variables nommées ; vérifier par un appel avec arguments |
| `oid` vide ou `cat-file` échoue, `SKILL.md` finit vide | le chemin n'existe pas sur `main` et `ls-tree` ne renvoie rien | conserver `test -n "$oid"` et `cat-file -t` = `blob` avant toute redirection |

## Checklist finale

- [ ] Empreintes validées et OID des blobs consignés avant écriture.
- [ ] `main` créé avec suivi, sans bascule, et égal à `origin/main`.
- [ ] Branche `rescue/` créée si HEAD portait des commits non poussés.
- [ ] Worktree propre avant `git switch main` ; code de retour et avertissement consignés.
- [ ] Casse constatée : root `SKILL.md`, `references/`, `.gitattributes`, `ls-files --eol`.
- [ ] Fichiers restaurés depuis les blobs, SHA-256 égaux, CR=0, frontmatter correct.
- [ ] `.gitattributes` restauré seulement avec accord, sinon signalé.
- [ ] Si `scripts/restaurer_archive.py` est utilisé : `RESULT ... OK` obtenu et `sha256=` comparés aux empreintes validées avant `--apply`.
- [ ] Aucun `gc`/`reflog expire` exécuté avant commit ou push de la restauration.
- [ ] `skill-file-qa` PASS sur un paquet stable ; liaison runtime vérifiée.

## Rapport

```text
Racine : <repo> | HEAD initial <oid> | rescue/<nom> <tip|absente>
main : <oid> = origin/main <oid> | bascule rc=<code>
Casse : root name=<autre> | references=<absent|present> | gitattributes=<absent|present> | eol=<i/lf w/crlf>
Blobs : SKILL.md <oid> | references/<fichier>.md <oid>
Restauration : SKILL.md <sha256> CR=<n> | references/<fichier>.md <sha256> CR=<n>
Statut : <M ... / ?? ...> | commit : <aucun|branche/commit> | push : <aucun|ref>
Validation : skill-file-qa <RESULT> | runtime <état> | non vérifié : <liste>
```

## Ressources

- `scripts/restaurer_archive.py` : restauration scriptée dry-run/apply depuis l'archive, écriture atomique, garde de chemins et exclusion des caches ; n'écrit jamais l'index, les branches ni HEAD.
- `references/cas-bascule-main-2026-10-26.md` : session source, sorties verbatim, OID/SHA-256 datés, résultat des harnais (80 assertions sur la bascule, 25 sur l'extraction d'OID livrée, 46 pour la session parallèle), observations post-restauration, limites et différence avec les recommandations.
