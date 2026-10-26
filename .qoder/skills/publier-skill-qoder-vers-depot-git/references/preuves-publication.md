# Preuves de publication — archiver un Skill vers `main`

Transcription des sorties d'outils observées lors de la publication du 2026-10-26, complétée par une re-vérification indépendante le même jour. Les hashes et commits ci-dessous sont des faits datés, pas des constantes à réutiliser.

## Dépôts impliqués

| Élément | Rôle observé | Remote |
|---|---|---|
| Racine `C:\Users\Administrateur\Desktop\IMAM8MAHDI` | n'est pas un dépôt (`EXIT=128`, `fatal: not a git repository`) | — |
| `ASTRO-QODE-IMAM8MAHDI` | dépôt imbriqué, intact pendant l'opération | `https://github.com/Loulbak78920/ASTRO-QODE-IMAM8MAHDI.git` |
| `GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` | dépôt cible de la publication | `https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN.git` |
| `~/.qoder/skills/mesure-cesium-133-geolocalisee` | Skill source, dépôt local sans `origin` | — |

## Séquence observée

1. Commit du Skill local : `8739656` — `feat(skill): ajouter le playbook Cs-133 geolocalise`, 5 fichiers, 1 024 insertions, worktree propre.
2. Push du Skill sur le remote partagé, branche dédiée `skill/mesure-cesium-133-geolocalisee` ; HEAD distant `87396560c229b9ce656d5cef490dab9d55ac5f90`. Cette branche a une **racine indépendante** : aucun ancêtre commun avec `main` (`a1ee407` à ce moment).
3. Branche de fusion créée depuis `main` : `merge/skill-mesure-cesium-133-geolocalisee` sur `a1ee407`.
4. Copie des 5 fichiers vers `.qoder/skills/mesure-cesium-133-geolocalisee/`, puis comparaison SHA-256 source/copie :

```text
IDENTIQUE SKILL.md 69edd22d352c05870d5c7a33bfa210ec8f9bf9253fcb731e99fdd6445b5b575d
IDENTIQUE references/contrat-mesure-et-limites.md 18c969c4360728ebc41b4a3dca69b04d23d50dc325b37937c0d8bbb41bbb7197
IDENTIQUE references/contrat-mesure-et-limites-zh.md 8ceb3d152991470b096728255e8f78561bc8affb3b108a768fe9cc8aa1e54460
IDENTIQUE references/skill-zh.md 130fafbd476ce43b00f004e573500ed75f49bb602afdb560e77db7893e7122cd
IDENTIQUE scripts/verifier_mesure_cesium.py d820610b5b55508d9bf73e09726aa5e09ef6420c9af53c146e3f95572abc9c21
```

5. Commit `3a4732abfd8eee7d7c0303f399045d3ada1489a0` — `feat(skills): ajouter le Skill mesure-cesium-133-geolocalisee` ; parent `a1ee40740a58d95d378410a5d79932934caad31f` ; 5 fichiers ajoutés, 0 suppression, 1 024 insertions.
6. `main` avancé en fast-forward `a1ee407..3a4732a` (aucun merge commit), puis push :

```text
To https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN.git
   a1ee407..3a4732a  main -> main
```

7. `git ls-remote origin refs/heads/main` → `3a4732abfd8eee7d7c0303f399045d3ada1489a0`.
8. Blobs distants comparés à la source : 5/5 identiques après correction MSYS (voir ci-dessous).
9. Branche temporaire supprimée ; `main` propre et synchronisé.

## Échec MSYS reproduit

Premier contrôle des blobs `origin/main`, cinq fois de suite :

```text
fatal: ambiguous argument 'origin\main;.qoder\skills\mesure-cesium-133-geolocalisee\SKILL.md': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
MISMATCH SKILL.md
```

Cause : Git Bash convertit l'argument `origin/main:<chemin>` comme une liste de chemins Windows (`:` → `;`, `/` → `\`). Le résultat est `EXIT=128` et un `MISMATCH` sur tous les fichiers, alors que la copie est correcte.

Correctif vérifié deux fois sur le même poste :

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' git -C "<depot>" show "origin/main:<chemin>"
```

- sans les variables : `EXIT=128` ;
- avec les deux variables : `EXIT=0` et contenu du blob affiché.

Le script `scripts/verifier_archive_skill.py` contourne le problème : il appelle `git` par `subprocess` sans shell et force ces deux variables dans l'environnement enfant.

## Re-vérification indépendante (2026-10-26)

| Contrôle | Commande | Résultat |
|---|---|---|
| QA du Skill | `validate_skill.py` sur ce dossier | `RESULT PASS`, 9 pass / 0 fail / 0 warn |
| Archives distantes | `--source ~/.qoder/skills/mesure-cesium-133-geolocalisee --repo GITHUB_DEPOT_PUBLIC_IMAM8MAHDI --ref origin/main --from remote` | 5/5 `OK`, `RESULT PASS`, `EXIT=0` |
| Archives worktree | même commande `--from worktree` | 5/5 `OK`, `EXIT=0` ; `git status` vide |
| Destination erronée | `--dest .qoder/skills/inexistant --from remote` | 5 × `MISSING`, `RESULT FAIL`, `EXIT=1` |
| Arguments manquants | script sans argument | argparse, `EXIT=2` |

## Archivage non poussé (`ddfd179`)

Deuxième passage observé le 2026-10-26, sur le Skill `publier-skill-qoder-vers-depot-git` lui-même.

| Élément | Valeur observée |
|---|---|
| Commit d'archive | `ddfd179817b98964a980472a06f20e18bf542df9`, parent `3a4732abfd8eee7d7c0303f399045d3ada1489a0` |
| Fichiers | `SKILL.md` `21ed7b412853…`, `references/preuves-publication.md` `b8573e4ea521…`, `scripts/verifier_archive_skill.py` `f4ce464c0aba…` |
| Copie worktree | 3/3 `OK`, `RESULT PASS`, `EXIT=0` |
| `main` | `3a4732a..ddfd179` **Fast-forward**, `## main...origin/main [ahead 1]` |
| `origin/main` | resté `3a4732abfd8eee7d7c0303f399045d3ada1489a0` (aucun push) |

`git branch -d merge/skill-publier-skill-qoder-vers-depot-git` a échoué (`DELETE_EXIT=1`) alors que la branche et `main` pointaient sur `ddfd179` :

```text
warning: not deleting branch 'merge/skill-publier-skill-qoder-vers-depot-git' that is not yet merged to
         'refs/remotes/origin/main', even though it is merged to HEAD
error: the branch 'merge/skill-publier-skill-qoder-vers-depot-git' is not fully merged
```

Cause : la branche a été créée depuis `origin/main` et `-d` compare à `refs/remotes/origin/main`, qui ne contient pas le commit. Conserver la branche sans `-D` ; après le push, `-d` passe.

Le contrôle distant de l'étape 8 est alors impossible. Rejoué le même jour :

```text
--ref ddfd179 --from remote     → 3/3 OK, RESULT PASS, EXIT=0
--ref origin/main --from remote → 3 x MISSING, RESULT FAIL, EXIT=1
```

Le second résultat ne traduit pas une copie divergente : `origin/main` n'a pas été mis à jour. Sans push, marquer le contrôle distant comme non exécuté.

Ces hashes sont ceux du contenu archivé ce jour-là. Toute modification ultérieure du Skill rend `ddfd179` divergent (`MISMATCH`) jusqu'à une nouvelle publication : ce n'est pas une régression du script.

Cache : la copie de ce passage ne contenait que les 3 fichiers attendus (aucun `__pycache__`), et le `.gitignore` du dépôt ignore `__pycache__/` et `*.py[cod]`. Le risque reste réel pour un autre Skill ou un autre dépôt : l'ancien vérificateur ignorait les caches, d'où la copie fichier par fichier, l'assertion `find` et la détection `EXTRA`.

## Dérive d'état et archive périmée (2026-10-26)

Deux constats distincts, observés le même jour sur le même dépôt cible et rejoués en lecture seule.

### Archive périmée après modification de la source

| Moment | Commande | Résultat |
|---|---|---|
| Avant modification | `--ref ddfd179 --from remote` | 3/3 `OK`, `RESULT PASS`, `EXIT=0` |
| Après modification | même commande | 3 `MISMATCH`, `RESULT FAIL`, `EXIT=1` |
| Rejeu final, après retouches de documentation | même commande | 3 `MISMATCH`, `RESULT FAIL`, `EXIT=1` |

```text
MISMATCH SKILL.md                          source=b5100863… ddfd179=21ed7b41…
MISMATCH references/preuves-publication.md source=07bedd4e… ddfd179=b8573e4e…
MISMATCH scripts/verifier_archive_skill.py source=d11f8864… ddfd179=f4ce464c…
```

Le rejeu final compare `SKILL.md` `42540f13…` et le script `d11f8864…` à `ddfd179` (`21ed7b41…`, `f4ce464c…`) ; ce fichier de preuves avait également changé. `ddfd179` est l'archive d'un contenu antérieur ; après édition du Skill, l'écart est attendu jusqu'à une nouvelle publication. Ce n'est ni une régression du script ni une conversion MSYS : le script force `MSYS_NO_PATHCONV=1` et `MSYS2_ARG_CONV_EXCL='*'`.

### Branche et distant modifiés par une autre session

| Contrôle | Valeur observée |
|---|---|
| Première lecture | `HEAD c5b7f17`, branche `skill/commit-skill-work`, `main ddfd179`, `origin/main 3a4732a` |
| Reflog | `11:24:35 commit: feat(skills): ajouter le Skill commit-skill-work` (`c5b7f17`) ; `11:25:03 checkout: moving from skill/commit-skill-work to main` |
| Reflog `origin/main` | `11:26:44 update by push` (`ddfd179`) ; `11:32:09 fetch origin: fast-forward` (`96fd809`) |
| `origin/main` après | `96fd8093a55c203672be3205c9ec53fbd3d7693c` |
| Rejeu de contrôle | `main @ 96fd809`, reflog `11:33:16 merge origin/main: Fast-forward` |

Aucune commande `switch`, `commit`, `merge` ou `push` de cette session n'a visé ce dépôt public : seule la lecture du reflog permet d'attribuer le déplacement. Ne jamais présenter ces changements comme ceux de la session courante, ni les annuler avec `reset`/`checkout` sans instruction explicite.

Ces hashes et horodatages sont des faits datés, pas des constantes à réutiliser.

## Collision de branche et push externe (2026-10-26)

Troisième constat du même jour, sur le même dépôt cible. Il porte sur la publication du Skill `commit-skill-work` depuis une session Qoder, alors qu'une branche de fusion du même nom existait déjà.

| Élément | Valeur observée |
|---|---|
| Préflight | `main` propre, `HEAD=origin/main=2e16742f6a74d657ccdfedf5a65bc51dd6bcf5e9` |
| Branche déjà présente | `merge/skill-commit-skill-work` `3628f24` — `[origin/main: ahead 1, behind 4]` |
| Branche utilisée | `merge/skill-commit-skill-work-refresh-20261026`, créée depuis `origin/main` |
| Copie | 4/4 `OK`, `RESULT PASS`, aucun cache |
| Commit | `2dade6c23892d27a360bdfcd60a12fef9fe3928c`, 12:31:49 |
| Dérive | 12:31:51 `checkout: moving from merge/skill-commit-skill-work-refresh-20261026 to main` → `STOP_BRANCH`, `EXIT=1` |
| Fusion externe | 12:32:45 `merge 2dade6c: Fast-forward` |
| Push externe | 12:32:51 `update by push` dans le reflog `origin/main` ; aucun push lancé par cette session |
| Distant | `git ls-remote origin refs/heads/main` → `2dade6c23892d…` |
| Blobs distants | `--ref origin/main --from remote` → 4/4 `OK`, `RESULT PASS`, `EXIT=0` |
| Nettoyage | `Deleted branch merge/skill-commit-skill-work-refresh-20261026 (was 2dade6c)` |
| Hooks | `core.hooksPath` non défini ; aucun hook actif (`post-commit` absent) |

Le `STOP_BRANCH` n'était pas causé par un hook : le reflog montre un `checkout` externe deux secondes après le commit. La session n'a exécuté ni `switch main`, ni `merge`, ni `push` après ce garde ; elle a seulement lu `reflog`, `ls-remote` et les blobs.

Enseignements :

- un nom de branche `merge/skill-<nom>` peut déjà être occupé (`ahead 1, behind 4` ici) : le créer à nouveau échoue ; une variante horodatée évite de toucher la branche d'une autre session ;
- un `STOP_BRANCH` peut précéder un achèvement externe : le commit de cette session peut être fast-forwardé et poussé par un tiers sans aucune commande de cette session ;
- `branch -d` peut réussir sans push de cette session lorsque la branche est contenue dans `origin/main` ; le test `merge-base --is-ancestor` rend ce cas explicite ;
- le rapport doit distinguer `push oui`, `push non` et `push externe à HH:MM:SS`, ce dernier étant observé dans le reflog et non revendiqué.

Les hashes, branches et horodatages ci-dessus sont des faits datés, pas des constantes à réutiliser.

## Plusieurs clones du même remote et STALE résiduel (2026-10-26)

Quatrième constat du même jour : republication de l'archive du Skill `commit-skill-work` alors que deux clones du même remote coexistent, l'un sur `master` (source fonctionnelle), l'autre sur `main` (clone d'archive).

| Élément | Valeur observée |
|---|---|
| Remote commun | `https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN.git` |
| Clone d'archive retenu | `GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` — `main`, propre, `HEAD = origin/main = ls-remote = 2bc8412b94f3` |
| Source fonctionnelle | `~/.qoder/skills/commit-skill-work` — `master` `1327b2f`, `origin/main` `2bc8412b` ; non modifiée |
| Rapport d'archives | 9 groupes `ARCHIVE`, 4 dépôts, 3 refs distinctes ; 8 groupes entiers visibles, le neuvième est `nettoyer-branches-refs-git` `main, origin/main` |
| Branche créée | `merge/skill-commit-skill-work` sur `2bc8412b` |
| Copie | 7 fichiers, aucun cache ; `--from worktree` → `RESULT PASS 7/7` |
| Commit | `034b3c5` `docs(skill): actualiser l'archive commit-skill-work (1327b2f)`, 2 fichiers, 18+/18− |
| Index | OID `a6cccb20…` (`SKILL.md`) et `a978ab98…` (`references/skill-zh.md`) égaux à `git hash-object --path` |
| Fusion / push | `2bc8412..034b3c5` fast-forward puis `main -> main` |
| Distant | `LOCAL = ORIGIN = REMOTE = 034b3c5` ; `--ref origin/main --from remote` → `RESULT PASS 7/7` |
| Nettoyage | `Deleted branch merge/skill-commit-skill-work (was 034b3c5)` |
| Détecteur rejoué | archive cible `FRESH 7/7` ; verdict global `RESULT STALE`, `EXIT=1` |

Ancestralité vérifiée dans le clone retenu :

```text
966bac09bab4 (github-pr-create-merge-sans-gh origin/main)  ANCESTOR_OF_ORIGIN_MAIN
bf1c721f5501 (nettoyer-branches-refs-git main/origin/main) ANCESTOR_OF_ORIGIN_MAIN
da7ba1e33067 (origin/merge/skill-aligner-...)              NOT_ANCESTOR
00e7b3b47903 (origin/merge/skill-github-pr-...-231214)     NOT_ANCESTOR
```

Enseignements :

- le remote seul ne désigne pas la cible : plusieurs clones locaux du même remote existent, dont la source fonctionnelle sur `master` ; seule une lecture branche/`HEAD`/`ls-remote` qualifie un clone ;
- un `RESULT STALE` global peut subsister après une republication réussie : il agrège les refs `merge/*` (instantanés non ancêtres de `main`) et les `origin/main` d'autres clones (refs locales en retard, ancêtres de `main`). La preuve de succès est la ligne `FRESH N/N` de l'archive cible ;
- modifier ou fetcher ces refs hors périmètre reviendrait à réécrire l'état d'autres dépôts sans instruction.

Les hashes, horodatages et compteurs ci-dessus sont des faits datés, pas des constantes à réutiliser.

## Archivage en série et portée de l'autorisation de push (2026-10-26)

Cinquième constat du même jour, sur le même dépôt cible : trois archivages enchaînés dans une session Qoder, dont deux à cible non nommée.

| Élément | Valeur observée |
|---|---|
| Message utilisateur | `继续下一个 Skill 的归档流程`, 2026-10-26T23:47:49.358Z |
| Sortie de l'énumération | `USER=69 ARCHIVE=9`, 60 Skills utilisateur absents de l'archive, tri par `mtime` du `SKILL.md` (00:42:43 en tête) |
| Question posée | une seule, 23:48:09Z, `归档对象` — «下一个要归档到 ASTRO-QODE-ALMIZAN 的 Skill 是哪个？» ; recommandé = le plus récemment modifié, deux alternatives |
| Cible retenue | `verifier-mutation-fixture-appliquee`, `mtime` 2026-10-27 00:42:43, source 7 779 B `5db69c9f…` |
| QA | `RESULT PASS`, 9 pass / 0 fail / 0 warn, empreinte inchangée pendant la validation |
| Copie | 3 fichiers, `--from worktree` → `RESULT PASS 3/3` : `SKILL.md 5db69c9f…`, `references/cas-2026-10-27-mutation-escape.md 2a5169bd…`, `scripts/apply_mutation.py 40bd5f1a…` |
| Commit | `f546c7368b1156255b51a3ad9b1025831372434e` `feat(skills): ajouter le Skill verifier-mutation-fixture-appliquee`, 3 fichiers, 456 insertions |
| Fusion / push | `d1d47ae..f546c73` fast-forward puis `d1d47ae..f546c73  main -> main`, **sans nouvelle question de push** |
| Distant | `--ref origin/main --from remote` → `RESULT PASS 3/3` ; `Deleted branch merge/skill-verifier-mutation-fixture-appliquee (was f546c73)` |
| Tour suivant | `继续下一个`, 2026-10-26T23:50:02.549Z : sans aucune question ; premier de la liste `mtime` retenu (`inventory-installed-skills`, 00:14:58) |
| Seconde publication | 2 fichiers, commit `f91d3de`, push `f546c73..f91d3de`, `RESULT PASS 2/2` (`SKILL.md 24a67513…`, `scripts/inventory_skills.py 262998a3…`), branche supprimée |
| État final relu le 2026-10-27 | archive 11 entrées, `origin/main = f91d3de717aa7351008a668d9ff0c53739c4fb47` ; entre-temps `origin/main` a avancé à `ba73c0518fe5ebb30cb5c2051f019c00611c5e45` (13 entrées), sans commande de cette session |

Le tour précédent (`auditer-couverture-skill-avant-creation`, 23:46:19Z) avait posé une question de push explicite avant `3f2c9ab..d1d47ae`. Les deux tours suivants ont poussé sans la reposer : l'autorisation du premier push a été étendue implicitement à la série, sans que le contrat 6 ne tranche ce point. Le contrat 6 exige désormais une autorisation nommant le commit, ou un accord de lot explicite (dépôt, branche, périmètre).

Enseignements :

- la liste des Skills à archiver est un instantané : elle rétrécit à chaque publication et doit être recalculée avant chaque Skill ;
- le diff se fait sur le nom de dossier du clone d'archive, pas sur le frontmatter ; un Skill déjà archivé est une mise à jour, avec `MISMATCH` attendu à l'étape 8 tant qu'il n'est pas republié ;
- une question unique avec recommandation suffit pour choisir la cible ; une délégation explicite («继续») permet de prendre la plus récente, à condition d'annoncer son nom ;
- l'absence de correction par l'utilisateur ne vaut pas autorisation de push : seul un accord explicite, nommé ou de lot, compte.

Les compteurs, hashes, commits et horodatages ci-dessus sont des faits datés, pas des constantes à réutiliser.

## Réserve

La copie publiée est une **archive** : les chemins relatifs du Skill peuvent viser l'arborescence du projet principal, absente du dépôt public. Le Skill fonctionnel reste dans le dossier utilisateur. La branche distante indépendante `skill/mesure-cesium-133-geolocalisee` n'a pas été fusionnée et reste sur `origin` ; sa suppression éventuelle exige une instruction explicite.
