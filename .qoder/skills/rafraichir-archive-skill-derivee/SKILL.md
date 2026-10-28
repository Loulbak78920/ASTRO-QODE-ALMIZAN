---
name: rafraichir-archive-skill-derivee
description: "Rafraîchir en lot des paquets Skill déjà archivés dont la source locale a dérivé : inventaire lecture seule en périmètre (SKILL.md, references/**, scripts/**, blob CRLF→LF contre git ls-tree origin/main), classification DIFF/MISSING/EXTRA, re-fetch jusqu'à deux inventaires identiques, quiescence (mtime, scan_skill_writers sur chaque fichier du delta, JSONL des auteurs, read_chat_session), skill-file-qa et scan de secrets masqué, puis publication de N paquets depuis un seul worktree lié, un commit par paquet gardé par HEAD^ == origin/main, et preuve à trois voies REST/ref/source. Utiliser pour « l'archive a dérivé », « republier les paquets modifiés », « rafraîchir les archives », « SCOPE_DRIFT », archivage en lot, plusieurs paquets désynchronisés. 中文触发：批量刷新归档、归档漂移、源已更新但归档未更新、重新发布过期归档、SCOPE_DRIFT、三路证明、偏差包。Ne pas utiliser pour une première publication ni pour un seul paquet sans inventaire (publier-skill-qoder-vers-depot-git)."
---

# Rafraîchir les paquets Skill dont l'archive a dérivé

Inventorier les paquets déjà archivés dont la source locale diffère de `origin/main`, écarter ceux qu'une autre session écrit encore, puis republier l'ensemble depuis un seul worktree lié avec un commit par paquet. Chaque étape laisse une preuve rejouable : inventaire, quiescence, QA, commit gardé, blobs distants.

## Quand l'utiliser

- Un lot de paquets déjà archivés a été enrichi localement (nouvelles références, SKILL.md retouché) et l'archive est en retard.
- L'utilisateur demande « republier les paquets modifiés », « rafraîchir l'archive », « refais un inventaire de dérive avant de publier ».
- Un rapport `FRESH`/`STALE` ou un `MISMATCH` `--from remote` désigne plusieurs paquets à resynchroniser.
- Après une série d'écritures par plusieurs sessions, avant de figer l'état publié.

Ne pas utiliser pour : une première publication ou un seul paquet nommé (voir `publier-skill-qoder-vers-depot-git`), un audit d'intégrité sans écriture (voir `skill-package-integrity-audit`), une revue de QA (voir `skill-file-qa`), une décision de takeover sur un paquet concurrent (voir `audit-skill-during-live-creation`).

## Contrat non négociable

1. **Lecture seule jusqu'à l'autorisation.** Aucune copie, aucun commit, aucun push avant l'accord explicite de l'utilisateur sur la liste et le périmètre du lot.
2. **Périmètre** : `SKILL.md`, `references/**`, `scripts/**`. Jamais `.git/`, `__pycache__/`, `*.pyc`, `.qoder/` imbriqué, ni le dossier source entier.
3. **Un commit par paquet** sur une seule branche de livraison, chemins explicites, message `docs(skill): actualiser l'archive <nom>`.
4. **Inventaire figé** : deux passes consécutives avec le même `ARCHIVE_REF` et la même liste de paquets. Un inventaire plus ancien que le dernier `fetch` ne sert pas de base.
5. **Quiescence avant copie** : mtime du paquet, attribution des écritures sur chaque fichier du delta, état des sessions auteures. Un paquet avec un écrivain actif sort du lot et est signalé.
6. **QA obligatoire** : `RESULT PASS` par paquet, plus un scan de secrets masqué. Aucune valeur de secret n'est affichée ni publiée.
7. **Un seul worktree lié** créé depuis `origin/main`. Le worktree principal et les branches d'une autre session ne sont jamais basculés, stashés, nettoyés ni supprimés.
8. **Gardes de publication** : `HEAD == origin/main` avant chaque paquet, index vide avant `git add`, tout le staging dans le paquet, `HEAD^ == origin/main` après commit, `origin/main` ancêtre, push ff-only, `HEAD == origin/main` après re-fetch.
9. **Preuve à trois voies** : `sha` REST == `git rev-parse origin/main:<chemin>` == `git hash-object --path <chemin> <fichier source>`. Le troisième opérande est toujours la source, jamais une copie du worktree d'archive.
10. **Aucune réécriture** : pas de force push, pas de rebase, pas de `reset --hard`, pas de `git config`.
11. **Autorisation bornée** : un paquet apparu pendant le lot n'est pas couvert ; il est signalé pour un tour suivant.
12. **Attribution** : un push ou un commit d'une autre session n'est jamais revendiqué. L'état final est constaté, pas corrigé.

## Procédure

Définir une fois les chemins, puis les réutiliser. Toujours passer les chemins absolus entre guillemets.

```bash
REPO="C:/Users/Administrateur/Desktop/GITHUB_DEPOT_PUBLIC_IMAM8MAHDI"
SRC="C:/Users/Administrateur/.qoder/skills"
SKILL="C:/Users/Administrateur/.qoder/skills/rafraichir-archive-skill-derivee"
SKILLS="C:/Users/Administrateur/.qoder/skills"
```

### 0. Préflight et baseline

```bash
git -C "$REPO" fetch origin --prune
git -C "$REPO" rev-parse origin/main main
git -C "$REPO" rev-parse --abbrev-ref HEAD
git -C "$REPO" status --porcelain=v1
git -C "$REPO" worktree list
git -C "$REPO" branch --list 'merge/skill-*'
git -C "$REPO" ls-tree -d --name-only origin/main -- .qoder/skills/ | wc -l
```

Consigner `origin/main`, la ref `main`, la branche et l'état du worktree principal, les worktrees, les branches `merge/skill-*`, le nombre de dossiers archivés. Si le worktree principal est sur une autre branche ou sale, ne rien y écrire : la livraison passe par un worktree lié. La ref `main` — pas `HEAD` — est la référence de l'état publié.

Si le chemin du clone est inconnu, le trouver par l'URL du remote, jamais par le nom du dossier.

### 1. Inventaire en périmètre

```bash
py -3 "$SKILL/scripts/scope_drift.py" --repo "$REPO" --src "$SRC" --ref origin/main
```

Sortie : `ARCHIVE_REF`, `SCOPE_DRIFT_PACKAGES`, `SCOPE_DRIFT_FILES diff/missing/extra`, `SCOPE_EXTRA_ONLY_PACKAGES`, `SCOPE_SAME_PACKAGES`, `LOCAL_ONLY_PACKAGES`, `ARCHIVE_ONLY_PACKAGES`, puis `DIFF`/`MISSING`/`EXTRA` par paquet. Codes : 0 aucune dérive, 1 dérive, 2 erreur. `--json` rend le même contenu en objet.

- `DIFF` et `MISSING` : l'archive est en retard ou incomplète.
- `EXTRA` : fichier local absent de l'archive. Un paquet dont le **seul** écart est `EXTRA` est compté dans `SCOPE_EXTRA_ONLY_PACKAGES` et reste un candidat à republier.
- `LOCAL_ONLY` : première publication, hors de ce Skill.
- `ARCHIVE_ONLY` : paquet archivé sans source locale. Ne rien supprimer ; le signaler.

### 2. Figer l'inventaire

Les autres sessions publient sur le même dépôt. Refaire `fetch` et l'inventaire jusqu'à obtenir deux passes identiques (même `ARCHIVE_REF`, même liste) :

```bash
git -C "$REPO" fetch origin --prune -q
py -3 "$SKILL/scripts/scope_drift.py" --repo "$REPO" --src "$SRC"
```

Un paquet qui disparaît de la liste entre deux passes a été republié par une autre session : le sortir du lot et le noter. Ne jamais publier depuis un inventaire dont la baseline a bougé.

### 3. Quiescence par paquet

Pour chaque paquet candidat, identifier la dernière écriture réelle, puis son auteur.

```bash
find "$SRC/<pkg>" -type f \
  ! -path '*/.git/*' ! -path '*/__pycache__/*' ! -path '*/.qoder/*' \
  -printf '%TY-%Tm-%TdT%TH:%TM:%TS %p\n' | sort | tail -1
```

Attribuer chaque fichier `DIFF`/`EXTRA` — pas seulement `SKILL.md` :

```bash
SD="C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI"
SCAN="C:/Users/Administrateur/.qoder/skills/verify-injected-skill-body-freshness/scripts/scan_skill_writers.py"
py -3 "$SCAN" --scan-dir "$SD" --target "$SRC/<pkg>/<rel>" --since "<ISO-8601 avant les écritures>" --json
```

`--target` accepte un chemin de fichier exact quelconque, même si l'aide parle de `SKILL.md` (comportement observé). La borne `--since` doit précéder les écritures mesurées : un `hits=0` obtenu avec une borne trop tardive ne prouve rien, l'abaisser et rejouer. Vérifier aussi le mtime des JSONL des sessions auteures dans `$SD`.

Pour une session encore vivante, lire son état :

```text
read_chat_session(<id>) -> runtimeState, activeTurnId, revision, pendingInteractionCount
```

`wait_chat_sessions` peut ne pas connaître une session lisible ; dans ce cas, répéter `read_chat_session` à intervalles et exiger des empreintes stables sur trois échantillons. Ne pas confondre silence et fin de tour.

Règles : tout paquet avec un écrivain actif est exclu et signalé ; un paquet dont la dernière écriture est ancienne et dont les JSONL d'auteurs n'ont plus bougé est quiescent ; ne pas attendre indéfiniment.

### 4. QA et scan de secrets

```bash
py -3 "$SKILLS/skill-file-qa/scripts/validate_skill.py" "$SRC/<pkg>" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" \
  --stable-seconds 4 --stability-timeout 45
```

Exiger `RESULT PASS`. Les `WARN layout` sont explicables quand le paquet contient un arbre `.qoder/` imbriqué (copie d'archive interne) : les compter, vérifier que `Files (N)` reste borné aux fichiers du paquet, et ne jamais supprimer cet arbre.

Scanner les secrets sans jamais imprimer de valeur : longue chaîne hexadécimale, base64, affectation de type secret, Bearer, UUID. Afficher le motif, le fichier, la ligne et une forme masquée `len + préfixe + suffixe`. Classer chaque correspondance : empreinte SHA-256 de fichier, empreinte de clé publique, identifiant de session ou valeur secrète. Une valeur secrète arrête le lot ; les empreintes et chemins sont acceptables.

### 5. Autorisation de lot

Présenter en une seule question : paquets retenus, fichiers par paquet (modifiés et nouveaux), résultats de quiescence et de QA, résumé du scan, nombre de commits, dépôt et branche. L'accord couvre ce lot exact et le push. Un paquet ou une écriture apparu après cette question impose une nouvelle autorisation.

### 6. Worktree de livraison

```bash
STAMP="$(date +%Y%m%dT%H%M%S)"
BRANCH="merge/skill-batch-$STAMP"
WT="$HOME/.qoder/tmp/skill-archive-batch-$STAMP"
git -C "$REPO" fetch origin --prune -q
BASE="$(git -C "$REPO" rev-parse origin/main)"
git -C "$REPO" show-ref --verify --quiet "refs/heads/$BRANCH" && { echo STOP_BRANCH; exit 1; }
git -C "$REPO" worktree add -b "$BRANCH" "$WT" "$BASE"
```

Une branche horodatée unique, créée depuis `origin/main`. Ne jamais réutiliser, déplacer ni supprimer une branche existante. Le worktree est un répertoire jetable sous `~/.qoder/tmp`.

### 7. Publication des N paquets

```bash
py -3 "$SKILL/scripts/publier_lot.py" \
  --repo "$REPO" --src "$SRC" --worktree "$WT" --branch "$BRANCH" \
  --packages "<p1,p2,...>"
```

Pour chaque paquet : copie du périmètre, preuve de stabilité de la source et d'identité de la copie, staging limité au paquet, commit, puis gardes `HEAD^ == origin/main`, ancêtre, push `HEAD:main`, re-fetch et `HEAD == origin/main`. `SKIP_EMPTY` signifie que l'archive était déjà identique. `--no-push` commite sans pousser pour une revue.

Un `STOP` (rc 2) arrête tout : `STOP_BASE` si `origin/main` a avancé, `STOP_SCOPE` si le staging sort du paquet, `STOP_GUARD` si le parent n'est plus `origin/main`, `STOP_CONCURRENT_WRITE` si la source a changé pendant la copie. Ne pas forcer ; diagnostiquer puis repartir d'un nouvel inventaire.

### 8. Preuves après push

```bash
for p in <p1> <p2>; do
  py -3 "$SKILLS/publier-skill-qoder-vers-depot-git/scripts/verifier_archive_skill.py" \
    --source "$SRC/$p" --repo "$REPO" --ref origin/main --from remote
done

py -3 "$SKILL/scripts/verifier_trois_voies.py" \
  --repo "$REPO" --src "$SRC" --ref origin/main \
  --package <p1> --package <p2> \
  --rest Loulbak78920/ASTRO-QODE-ALMIZAN

py -3 "$SKILL/scripts/scope_drift.py" --repo "$REPO" --src "$SRC"
```

Exiger : `RESULT PASS` par paquet, `TRIO_TOTAL = MATCH`, `MISMATCH 0`, `REST_TOTAL = TRIO_TOTAL` ou `REST_SKIPPED` explicite, puis `SCOPE_DRIFT_PACKAGES 0` sur tout l'inventaire. `verifier_archive_skill.py` compare des SHA-256 d'octets bruts : une source CRLF face à un blob LF rend un `MISMATCH` de normalisation, que `verifier_trois_voies.py` tranche par OID de blob. Le REST peut être anonyme sur un dépôt public, avec jeton sinon ; un 404 anonyme ne prouve pas un dépôt privé.

### 9. Nettoyage et état final

```bash
git -C "$REPO" worktree remove "$WT" --force
if [ -z "$(git -C "$REPO" status --porcelain=v1)" ] && \
   [ "$(git -C "$REPO" rev-parse --abbrev-ref HEAD)" = "main" ]; then
  git -C "$REPO" merge --ff-only origin/main
elif ! git -C "$REPO" worktree list --porcelain | grep -qx "branch refs/heads/main"; then
  git -C "$REPO" merge-base --is-ancestor main origin/main && \
    git -C "$REPO" branch -f main origin/main
else
  echo "MAIN_OCCUPIED : main non avancée, à signaler"
fi
git -C "$REPO" branch -d "$BRANCH"
git -C "$REPO" rev-parse main origin/main
git -C "$REPO" status --porcelain=v1
git -C "$REPO" ls-tree -d --name-only origin/main -- .qoder/skills/ | wc -l
```

La ref `main` doit égaler `origin/main`. Si `main` est extraite dans un worktree étranger, ne pas y toucher : signaler le retard. `branch -d` ne supprime que la branche de ce lot, et seulement si elle est contenue dans `origin/main`.

## Pièges vérifiés

| Symptôme | Cause | Correctif |
|---|---|---|
| `verifier_archive_skill.py` sort en 2 avec `--skill` | l'option est `--source` | relire `--help`, utiliser `--source` |
| des dizaines de `MISMATCH` REST alors que la ref est correcte | `hash-object` appliqué au fichier du worktree d'archive resté sur le commit précédent | hacher le fichier **source** avec `--path <chemin dépôt>` ; preuve à trois voies |
| `HEAD` diffère de `origin/main` alors que la ref `main` est à jour | le worktree principal est sur la branche d'une autre session | lire `git rev-parse main`, pas `HEAD` ; ne pas basculer |
| la liste de dérive rétrécit entre deux passes | une autre session a republié un paquet | re-`fetch`, re-hacher, figer sur deux passes identiques |
| `scan_skill_writers` rend `hits=0` | borne `--since` postérieure aux écritures | abaisser la borne, confirmer par mtime, rejouer |
| `wait_chat_sessions` répond que la session n'existe pas | canal d'observation en défaut, session pourtant lisible | répéter `read_chat_session` et exiger trois empreintes stables |
| `fatal: ambiguous argument 'origin\main;...'` | conversion MSYS d'un argument `ref:chemin` dans le shell | appeler git par subprocess, ou `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` |
| QA `Files (20)` et de nombreux `WARN layout` pour un paquet | le paquet source contient un arbre `.qoder/skills/` imbriqué | compter les fichiers du périmètre, expliquer les WARN, ne rien supprimer |
| push rejeté (non-fast-forward) | `origin/main` a avancé après le commit | `STOP`, attribuer, repartir du nouvel `origin/main` ; jamais de force |
| `branch -d` refusé | le commit n'est pas contenu dans `origin/main` | conserver la branche et la signaler |
| REST anonyme 404 | dépôt privé ou chemin absent | ne pas conclure ; utiliser un jeton ou marquer REST non vérifié |
| REST 200 mais `MISMATCH` | la source a changé après la publication | republier les octets finaux, rejouer la preuve |

## Définition de terminé

- [ ] Inventaire stabilisé sur deux passes identiques, `ARCHIVE_REF` consigné.
- [ ] Chaque paquet du lot quiescent : dernière écriture mesurée, auteurs attribués, sessions vivantes en `ready`/`activeTurnId: null` ou exclues.
- [ ] `skill-file-qa` `RESULT PASS` pour chaque paquet ; scan de secrets masqué, aucune valeur affichée.
- [ ] Autorisation de lot explicite (paquets, fichiers, dépôt, branche, push).
- [ ] Une seule branche horodatée, un seul worktree lié, worktree principal intact.
- [ ] Un commit par paquet, `HEAD^ == origin/main` à chaque fois, push ff-only, aucun `STOP` inexpliqué.
- [ ] `verifier_archive_skill.py --from remote` `RESULT PASS` par paquet.
- [ ] Preuve à trois voies : `TRIO_TOTAL = MATCH`, `MISMATCH 0`, REST vérifié ou explicitement non vérifié.
- [ ] Ré-inventaire : `SCOPE_DRIFT_PACKAGES 0` sur l'ensemble.
- [ ] `main` (la ref) = `origin/main`, worktree lié et branche supprimés, aucune branche d'une autre session touchée.
- [ ] Rapport : commits, fichiers, preuves, paquets apparus hors lot, réserves de visibilité REST.

## Rapport

```text
Archive : <repo> | origin/main <ancien>..<nouveau> | dossiers <n>
Inventaire : <N> paquets en dérive | <f> DIFF, <m> MISSING, <e> EXTRA | <s>/<t> identiques
Quiescence : <N> quiescents | exclu <pkg> (écrivain <id>, état <runtimeState>)
QA : <N>/<N> PASS | scan masqué : <motifs classés>
Lot : <N> paquets | <k> fichiers | branche merge/skill-batch-<stamp>
Commits : <hash1> <pkg1>, <hash2> <pkg2>, ...
Preuves : verifier remote <N>/<N> PASS | TRIO <N>/<N> | REST <N>/<N> ou non vérifié (<raison>)
État : main = origin/main = <hash> | worktree supprimé | branche supprimée
Hors lot : <paquets apparus ou actifs> | <aucun>
Réserve : sources CRLF normalisées | visibilité REST | autres clones
```

## Ressources

- `scripts/scope_drift.py` : inventaire lecture seule des paquets en dérive, OID de blob avec normalisation CRLF→LF, sortie texte ou JSON, codes 0/1/2.
- `scripts/publier_lot.py` : copie du périmètre dans un worktree lié, un commit par paquet, gardes `HEAD`/`HEAD^`/ancêtre, push ff-only, arrêt `STOP` sans réécriture.
- `scripts/verifier_trois_voies.py` : preuve REST == ref == source par `hash-object --path` du fichier source ; REST facultatif, jamais de valeur de jeton affichée.
- `references/cas-lot-2026-10-28.md` : cas observé (9→7 paquets, commits, 26/26, deux pièges majeurs), limites et rejeu de la fixture.
- `publier-skill-qoder-vers-depot-git` : mécanique d'une publication unitaire, worktree occupé, visibilité REST.
- `skill-file-qa` : validation statique ; `verify-injected-skill-body-freshness` : attribution des écritures.
- `skill-package-integrity-audit` : détection STALE en lecture seule, sans republication.
