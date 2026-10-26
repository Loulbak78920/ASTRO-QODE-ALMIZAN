---
name: github-pr-create-merge-sans-gh
description: "Créer/fusionner une PR GitHub sans gh ni navigateur, via Git Credential Manager (git credential fill) et l'API REST : probe lecture seule, garde d'ancêtre commun (compare 404, branche orpheline), reconstruction depuis la base, recalcul après fetch (origin/main ou URL explicite, merge-base, diff 3 points), création idempotente, contrôle des fichiers de la PR, attente de mergeable, fusion rebase prioritaire, puis SHA de fusion, main distant, fast-forward et blobs. Après fusion, si les sources divergent, échantillonner SHA-256/mtime sans rollback ni republication non demandée. Utiliser pour « gh absent », « créer une PR », « pas d'origin », « No common ancestor », « branche orpheline », « reconstruire depuis main », « vérifier les fichiers de la PR », « merge PR to main », « rebase merge », « mergeable », « base a avancé », « MISMATCH après fusion », « écriture concurrente ». 中文触发：无 gh、无 origin、创建 PR、共同祖先 404、孤儿分支、从 main 重建、核对 PR 文件、合并 PR 到 main、rebase 合并、mergeable 轮询、base 前进、合并后 MISMATCH、并发写入。"
---

# Créer et fusionner une pull request GitHub sans gh

## Portée

Ce Skill couvre github.com, avec un jeton déjà stocké par un credential helper Git. Il prend aussi en charge un dépôt local sans `origin` via une URL explicite et des refs temporaires locales. Une branche à historique racine indépendant ne peut pas former de PR : elle doit être reconstruite depuis la base, sans fusionner les deux historiques. Il ne couvre pas GitHub Enterprise, la création de jetons, la connexion au navigateur, le contournement des protections de branche, le force push, ni la republication automatique après divergence des sources.

## Autorisations et actions irréversibles

- Sonde et lecture : libres.
- Création de PR : uniquement sur demande explicite.
- Fusion : uniquement sur demande explicite, avec la branche cible confirmée. Si l'utilisateur demande seulement de créer la PR, s'arrêter après l'étape 3 bis et donner l'URL.
- Ne jamais pousser directement sur `main` pour contourner la PR ; ne jamais faire de force push ; ne pas supprimer la branche de travail sans instruction.
- Reconstruire une branche de livraison et pousser ce nouveau head fait partie d'une demande explicite de création de PR. Ne jamais réécrire, fusionner ni supprimer la branche orpheline ; ne jamais fusionner deux historiques sans ancêtre commun.
- Une fusion modifie un état partagé. En cas d'ambiguïté sur la cible, demander avant d'agir.

## Sécurité des identifiants

- Lire le jeton avec `git credential fill` (lecture seule). Ne pas utiliser `git credential approve` ni `reject`, et ne pas modifier la configuration Git.
- Le jeton reste en mémoire : jamais affiché, jamais écrit sur disque, jamais passé en argument de commande.
- Ne pas saisir d'identifiants dans le navigateur. Une page de connexion GitHub prouve seulement que la session navigateur n'est pas authentifiée ; elle ne bloque pas l'API.
- Si le credential helper échoue, s'arrêter. Ne pas demander à l'utilisateur de coller un jeton dans la conversation.
- Le script n'imprime que le nom d'utilisateur et des statuts non secrets.

## Étape 0 — Constater l'environnement

Définir une fois les variables des étapes suivantes ; remplacer chaque valeur entre `<...>`. `SKILL` pointe vers le dossier local du Skill et doit être adapté après un déplacement. `REMOTE_URL` est l'URL HTTPS du dépôt distant, même si `DEPOT` n'a pas d'`origin`. Les étapes 5 et 6 restent centrées sur `main` ; pour une autre base, remplacer `main` par `$BASE` et vérifier la branche locale avant le fast-forward.

```bash
SKILL="C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh"
DEPOT="<chemin-absolu-du-depot>"
REPO="<owner/repo>"
REMOTE_URL="<url-https-du-depot>"
NOM="<nom-du-skill>"
BASE="main"
BRANCH="<branche-head>"
PREFIXE="<chemin-relatif-du-perimetre>"
BASE_AVANT="<sha-origin/main-avant-la-pr>"
HEAD_PR="<sha-du-head-de-pr>"
BODY="<fichier-utf8-du-corps-de-pr>"
N="<numero-de-pr>"
CHEMIN="<chemin-relatif-dans-le-depot>"
SOURCE="<dossier-source-du-skill>"
```

Ne pas laisser ces variables vides : `py -3 "$SKILL/..."` ou `git -C "$DEPOT"` s'exécuterait sur un chemin vide. `REMOTE_URL` doit être sur github.com et désigner le même dépôt que `REPO` ; si une seule URL SSH est disponible, vérifier qu'elle pointe vers le même dépôt sans changer de protocole silencieusement.

- Ne jamais écrire de jeton dollar-chiffre (variable positionnelle) dans un bloc de commande : lors d'un appel avec arguments, le CLI le remplace dans le corps injecté. Cas vérifié le 2026-10-26 : le jeton de numéro de champ d'un `awk` de l'étape 2 a été injecté avec `PR` à la place. Utiliser `cut -f1`/`cut -f3` ou des variables nommées (`$BRANCH`, `$PREFIXE`) ; ces dernières ne sont pas concernées.

```bash
command -v gh || true
git config --get credential.helper || true
git -C "$DEPOT" remote -v
ORIGIN_URL="$(git -C "$DEPOT" remote get-url origin 2>/dev/null || true)"
printf 'ORIGIN_URL=%s\n' "${ORIGIN_URL:-NONE}"
printf 'REMOTE_URL=%s\n' "$REMOTE_URL"
git -C "$DEPOT" status -sb
git -C "$DEPOT" branch --show-current
```

- `error: No such remote 'origin'` n'est pas un échec d'authentification : le dépôt local n'a pas d'`origin`. Utiliser `REMOTE_URL` et ne pas ajouter de remote ni modifier la configuration Git.
- Si `ORIGIN_URL` existe et diffère de `REMOTE_URL`, s'arrêter : le dépôt local et la cible de la PR ne sont pas le même.
- `NOM` doit être un nom de dossier simple (`A-Za-z0-9._-`) ; sinon s'arrêter avant toute copie ou création de branche.
- Extraire `owner/repo` de `REMOTE_URL` et vérifier qu'il correspond à `REPO`.
- Si `gh` est absent, utiliser `scripts/github_pr_api.py` ; ne pas installer `gh` sans demande.
- Relever le head : branche locale et SHA. Si le worktree est sale, ne pas committer ni pousser implicitement ; la PR ne doit contenir que les commits déjà poussés.
- Un dépôt local peut être une copie de travail sans remote, tandis que la PR vise un dépôt distant identifié par `REMOTE_URL`.

## Étape 1 — Sonder l'API en lecture seule

```bash
py -3 "$SKILL/scripts/github_pr_api.py" probe --repo "$REPO" --head "$BRANCH"
git -C "$DEPOT" ls-remote "$REMOTE_URL" "refs/heads/$BRANCH"
```

Sortie attendue : `CREDENTIAL_USER`, `REPO`, `PERMISSIONS`, `MERGE_METHODS`, `OPEN_PRS`.

- Arrêter si `push=false`, ou si l'API renvoie 401/403.
- Noter si `rebase=true`. Si `rebase=false`, ne pas supposer qu'une fusion rebase est possible : demander la méthode.
- Si `ls-remote` ne renvoie aucun SHA pour `refs/heads/$BRANCH`, le head n'est pas sur le distant : s'arrêter, ne pas pousser silencieusement.
- Si une PR ouverte existe déjà pour ce head, la réutiliser ; ne pas créer de doublon.
- `probe` ne prouve ni l'ancêtre commun ni la portée ; ces contrôles sont dans l'étape 2.

## Étape 2 — Vérifier l'ancêtre commun et recalculer la portée

Résoudre la base et le head sans supposer qu'`origin` existe : le dépôt local peut n'avoir aucun remote.

```bash
if [ -n "${ORIGIN_URL:-}" ]; then
  git -C "$DEPOT" fetch origin
  BASE_SHA="$(git -C "$DEPOT" rev-parse "origin/$BASE")"
  HEAD_SHA="$(git -C "$DEPOT" rev-parse "origin/$BRANCH")"
else
  git -C "$DEPOT" fetch "$REMOTE_URL" \
    "+refs/heads/$BASE:refs/qoder-tmp/base" \
    "+refs/heads/$BRANCH:refs/qoder-tmp/head"
  BASE_SHA="$(git -C "$DEPOT" rev-parse refs/qoder-tmp/base)"
  HEAD_SHA="$(git -C "$DEPOT" rev-parse refs/qoder-tmp/head)"
fi
REMOTE_HEAD="$(git -C "$DEPOT" ls-remote "$REMOTE_URL" "refs/heads/$BRANCH" | cut -f1)"
printf 'BASE_SHA=%s\nHEAD_SHA=%s\nREMOTE_HEAD=%s\n' "$BASE_SHA" "$HEAD_SHA" "$REMOTE_HEAD"
[ -n "$REMOTE_HEAD" ] && [ "$REMOTE_HEAD" = "$HEAD_SHA" ] && echo HEAD_SYNC || echo HEAD_MISMATCH
```

- `HEAD_MISMATCH` : le head local n'est pas celui du distant. S'arrêter ; ne pas pousser sans instruction.
- Si `BASE_SHA` ou `HEAD_SHA` est vide, le fetch ou la résolution a échoué : s'arrêter et expliquer.
- Le `+` ne concerne que les refs locales `refs/qoder-tmp/*` ; il ne réécrit aucune branche distante.

Puis le garde d'ancêtre commun, en local :

```bash
git -C "$DEPOT" merge-base "$BASE_SHA" "$HEAD_SHA"
printf 'MERGE_BASE_EXIT=%s\n' "$?"
```

- Sortie 0 : histoires reliées, continuer.
- Sortie 1 avec sortie vide : aucun ancêtre commun → **Étape 2 bis**, ne pas créer de PR.
- Autre code : objet ou dépendance manquant, s'arrêter et expliquer.

Confirmer côté API, car `merge-base` local ne garantit pas que GitHub accepte la comparaison :

```bash
py -3 "$SKILL/scripts/github_pr_api.py" compare --repo "$REPO" --base "$BASE" --head "$BRANCH"
```

- Attendu : `COMPARE status=... ahead=N behind=N`, `MERGE_BASE <sha>` non vide, `FILES n`.
- `COMPARE_FAIL status=404` avec `No common ancestor` : histoires non reliées → **Étape 2 bis**.
- `ahead_by=0` ou `total_commits=0` : aucun commit entre base et head ; vérifier la branche, ne pas créer de PR.
- `FILES n` peut être plafonné par l'API ; le diff local fait foi pour la portée.

Délimiter la portée réelle :

```bash
git -C "$DEPOT" diff --stat "$BASE_SHA...$HEAD_SHA"
git -C "$DEPOT" diff --name-status "$BASE_SHA...$HEAD_SHA"
git -C "$DEPOT" log --oneline "$BASE_SHA..$HEAD_SHA"
```

- La base peut avoir avancé depuis la préparation : recalculer à chaque fetch. Cas vérifié : `origin/main` avait avancé de `3a4732a` à `ddfd179` tandis que le merge-base restait `3a4732a`.
- Le diff à trois points compare le merge-base au head ; c'est lui qui délimite la portée de la PR.
- Vérifier que seuls les fichiers attendus apparaissent. Toute surprise (fichier supplémentaire, suppression, binaire) impose un arrêt et une explication.
- Consigner base distante, merge-base, head SHA et liste des fichiers.

## Étape 2 bis — Reconstruire une branche de livraison depuis la base

À exécuter uniquement si le garde de l'étape 2 a signalé l'absence d'ancêtre commun. Une PR ne peut pas être ouverte entre deux histoires non reliées, même si les fichiers sont identiques.

- Ne pas fusionner les histoires (`--allow-unrelated-histories` interdit ici), ne pas réécrire ni supprimer la branche orpheline.
- Travailler dans un clone isolé de `$BASE` : la copie de travail peut être sur la branche orpheline, sale, ou occupée.

```bash
TMP="$(mktemp -d)"
git clone --quiet --branch "$BASE" --single-branch "$REMOTE_URL" "$TMP/repo"

# Lecture seule : layout de la base et précédent de livraison
git -C "$TMP/repo" ls-tree --name-only HEAD
git -C "$TMP/repo" ls-tree -r --name-only HEAD -- .qoder/skills | head -20 || true
git clone --quiet --filter=blob:none --no-checkout "$REMOTE_URL" "$TMP/probe"
for b in $(git -C "$TMP/probe" for-each-ref --format='%(refname:short)' 'refs/remotes/origin/merge/skill-*'); do
  echo "PRECEDENT $b"
  git -C "$TMP/probe" ls-tree -r --name-only "$b" | head -20
done

PREFIXE=".qoder/skills/$NOM"
if [ -n "$(git -C "$TMP/repo" ls-tree -r --name-only HEAD -- "$PREFIXE")" ]; then
  echo PREFIX_EXISTS; exit 2
fi
mkdir -p "$TMP/repo/$PREFIXE"
cp "$SOURCE/SKILL.md" "$TMP/repo/$PREFIXE/SKILL.md"
[ -d "$SOURCE/references" ] && cp -R "$SOURCE/references" "$TMP/repo/$PREFIXE/"
[ -d "$SOURCE/scripts" ] && cp -R "$SOURCE/scripts" "$TMP/repo/$PREFIXE/"
find "$TMP/repo/$PREFIXE" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$TMP/repo/$PREFIXE" -name '*.pyc' -delete
```

- Ne copier que `SKILL.md`, `references/` et `scripts/` ; ni cache, ni fichier de travail, ni contenu hors du préfixe.
- Le dossier de destination doit être neuf sur cette branche ; la commande `PREFIX_EXISTS` vérifie que `$BASE` ne contient pas déjà `.qoder/skills/$NOM`. Si elle s'affiche, s'arrêter et demander.
- Si aucun `PRECEDENT` n'apparaît, ne pas inventer un préfixe : utiliser le layout de la base et demander confirmation avant de copier.
- Le clone `$TMP/probe` est en lecture seule (`--no-checkout`) ; il est supprimé avec `$TMP`.

Comparer la copie à la source, fichier par fichier :

```bash
( cd "$SOURCE" && find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum ) > "$TMP/src.sha"
( cd "$TMP/repo/$PREFIXE" && find . -type f -print0 | sort -z | xargs -0 sha256sum ) > "$TMP/dst.sha"
diff "$TMP/src.sha" "$TMP/dst.sha" && echo COPY_MATCH || echo COPY_MISMATCH
```

- `COPY_MISMATCH` : ne pas committer ; expliquer l'écart.

Publier la branche de livraison :

```bash
git -C "$TMP/repo" switch -c "merge/skill-$NOM"
git -C "$TMP/repo" add "$PREFIXE"
git -C "$TMP/repo" status --short
git -C "$TMP/repo" commit -m "docs(skill): archiver $NOM"
git -C "$TMP/repo" push "$REMOTE_URL" "merge/skill-$NOM:merge/skill-$NOM"
BRANCH="merge/skill-$NOM"
HEAD_SHA="$(git -C "$TMP/repo" rev-parse HEAD)"
REMOTE_HEAD="$(git -C "$TMP/repo" ls-remote "$REMOTE_URL" "refs/heads/$BRANCH" | cut -f1)"
printf 'HEAD_SHA=%s\nREMOTE_HEAD=%s\n' "$HEAD_SHA" "$REMOTE_HEAD"
[ "$REMOTE_HEAD" = "$HEAD_SHA" ] && echo HEAD_SYNC || echo HEAD_MISMATCH
git -C "$TMP/repo" ls-tree -r --name-only HEAD -- "$PREFIXE"
```

- `git add` explicite : jamais `git add -A`. Vérifier `status --short` avant de committer.
- Si la branche `merge/skill-$NOM` existe déjà, ne pas forcer : choisir un suffixe ou demander.
- `HEAD_MISMATCH` : le push n'a pas publié le commit attendu ; s'arrêter sans créer de PR.
- La liste `ls-tree` doit égaler les fichiers copiés ; un fichier supplémentaire ou manquant impose un arrêt.
- La branche orpheline d'origine reste intacte sur le distant.
- Relancer le garde `compare` de l'étape 2 sur `$BRANCH` avant l'étape 3 : `MERGE_BASE` doit être non vide.
- Conserver `$TMP` jusqu'à la vérification de la PR, puis supprimer le clone et les refs `refs/qoder-tmp/*` si elles ont été créées.

## Étape 3 — Créer la PR

Préparer un corps UTF-8 dans un fichier temporaire : résumé, portée exacte, validations exécutées, mention explicite de ce qui n'a pas été testé.

```bash
py -3 "$SKILL/scripts/github_pr_api.py" create \
  --repo "$REPO" --head "$BRANCH" --base "$BASE" \
  --title "Titre de la PR" --body-file "$BODY" --yes
```

- `create` exige `--yes` et refuse avant tout appel réseau sans ce drapeau.
- La commande est idempotente : une PR ouverte pour le même head est réutilisée (`PR_EXISTING`).
- Relever `N` depuis `PR_CREATED` ou `PR_EXISTING`, puis consigner numéro, URL, head SHA, base et état `open`.
- La création seule ne suffit pas : contrôler la portée réelle à l'étape 3 bis avant de conclure.

## Étape 3 bis — Vérifier la portée de la PR créée

```bash
py -3 "$SKILL/scripts/github_pr_api.py" files --repo "$REPO" --pr "$N"
py -3 "$SKILL/scripts/github_pr_api.py" status --repo "$REPO" --pr "$N"
```

```bash
git -C "$TMP/repo" ls-tree -r --name-only HEAD -- "$PREFIXE" | while IFS= read -r f; do
  rel="${f#"$PREFIXE"/}"
  oid="$(git -C "$TMP/repo" ls-tree -r HEAD -- "$f" | cut -f3)"
  pub="$(git -C "$TMP/repo" cat-file blob "$oid" | sha256sum | cut -d' ' -f1)"
  src="$(sha256sum "$SOURCE/$rel" | cut -d' ' -f1)"
  [ "$pub" = "$src" ] && echo "BLOB_MATCH $rel $pub" || echo "BLOB_MISMATCH $rel published=$pub source=$src"
done
```

- Attendu : chaque `FILE` est `added`, son chemin commence par `$PREFIXE`, `-0`, et `FILES n` égale le nombre de fichiers copiés.
- `PR_FILES changed=` doit égaler `FILES n` ; sinon `FILES_MISMATCH` et arrêt.
- Vérifier que `PR_BASE` est `$BASE`, que le head SHA égale `REMOTE_HEAD` et que `PR_MERGEABLE` est `true` ou `null` (en calcul).
- `HEAD_SYNC` a établi que le commit poussé est celui du clone ; ces blobs sont donc ceux du distant.
- Sous `core.autocrlf=true`, `git add` peut afficher `LF will be replaced by CRLF` : cet avertissement concerne la copie de travail du clone, pas le blob. Comparer les SHA-256 des blobs, pas des fichiers du clone.
- Un `BLOB_MISMATCH` ou un fichier sans source : ne pas fusionner ; rapporter l'écart.
- Toute surprise (fichier hors préfixe, suppression, binaire, nombre différent) : ne pas fusionner, rapporter, et ne fermer la PR que sur instruction explicite.
- Si l'utilisateur n'a demandé que la création, s'arrêter après cette vérification.
- Nettoyer ensuite `$TMP`, les refs `refs/qoder-tmp/base|head` et tout fichier de corps temporaire ; ne pas supprimer la branche orpheline ni la branche de livraison sans instruction.

## Étape 4 — Fusionner

Uniquement après instruction explicite de fusion et confirmation de la branche cible.

```bash
py -3 "$SKILL/scripts/github_pr_api.py" merge \
  --repo "$REPO" --pr "$N" --method rebase --yes
```

- `merge` exige `--yes` et refuse avant tout appel réseau sans ce drapeau.
- Le script interroge `mergeable` jusqu'à 15 fois à 2 secondes d'intervalle. `null` persistant ou `false` : abandon, sans contournement.
- La méthode par défaut est `rebase` ; elle produit un historique linéaire. Le script ne bascule pas silencieusement vers `merge`. Pour utiliser `merge` ou `squash`, le décider explicitement et le déclarer dans le rapport.
- Sortie attendue : `MERGE_REBASE status=200 merged=True`, puis `PR_FINAL`, `REMOTE_MAIN` et `VERIFY_MATCH true`.
- En cas de 405/409 (protection de branche, conflit, checks requis) : rapporter le message et s'arrêter. Ne pas désactiver une protection ni forcer.

## Étape 5 — Vérifier après fusion

```bash
git -C "$DEPOT" fetch origin
git -C "$DEPOT" rev-parse origin/main
git -C "$DEPOT" ls-remote origin refs/heads/main
git -C "$DEPOT" log --oneline -3 origin/main
git -C "$DEPOT" diff --name-status "$BASE_AVANT"..origin/main
git -C "$DEPOT" ls-tree -r origin/main -- "$PREFIXE"
for oid in $(git -C "$DEPOT" ls-tree -r origin/main -- "$PREFIXE" | cut -f3); do
  git -C "$DEPOT" cat-file blob "$oid" | sha256sum
done
git -C "$DEPOT" merge --ff-only origin/main
git -C "$DEPOT" diff --name-status "$HEAD_PR" origin/main -- "$PREFIXE"
```

- Immédiatement après la fusion, comparer le SHA de fusion de l'API, `origin/main`, `ls-remote` et le fast-forward local : ils doivent désigner le même commit. Si `main` a avancé depuis, le SHA de fusion doit être un ancêtre de `origin/main`, pas nécessairement la tête.
- Recalculer les SHA-256 des blobs distants et les comparer aux empreintes validées avant la PR.
- Le diff limité au préfixe entre le head de PR et `origin/main` doit être vide après une fusion rebase.
- Vérifier que le worktree est propre et que la branche locale est à jour avec `git status -sb`.
- Sans `origin`, faire `git -C "$DEPOT" fetch "$REMOTE_URL" "+refs/heads/$BASE:refs/qoder-tmp/base"` et remplacer `origin/main` par `refs/qoder-tmp/base` dans les commandes ci-dessus ; supprimer la ref après contrôle.
- Si le dépôt contient un vérificateur d'archive, utiliser `publier-skill-qoder-vers-depot-git` et son script `verifier_archive_skill.py` en mode `--from remote`.

## Étape 6 — Traiter une divergence des sources après fusion

Un `MISMATCH` du vérificateur ne prouve pas une corruption de l'archive. Il peut signaler une écriture concurrente dans les fichiers source.

```bash
oid=$(git -C "$DEPOT" ls-tree -r origin/main -- "$CHEMIN" | cut -f3)
git -C "$DEPOT" cat-file blob "$oid" > /tmp/publie
sha256sum /tmp/publie "$SOURCE/$CHEMIN"
stat -c '%y %s %n' "$SOURCE/$CHEMIN"
for i in 1 2 3; do sha256sum "$SOURCE/$CHEMIN"; stat -c '%y %s' "$SOURCE/$CHEMIN"; sleep 2; done
```

- Vérifier que `oid` est non vide et désigne un seul fichier ; sinon le chemin est absent ou ambigu. Ne pas utiliser `git show "origin/main:$CHEMIN"` sous Git Bash : MSYS réécrit l'argument en `origin\main;...` et Git répond `ambiguous argument`. Extraire l'OID puis lire le blob évite cette conversion.
- Comparer le blob publié au fichier source, puis les mtime. Trois échantillons identiques à 2 secondes d'intervalle établissent la stabilité.
- Si les blobs publiés correspondent à la version validée et que les sources ont changé après la copie : conclure à une dérive des sources, pas à un échec de fusion.
- Ne pas restaurer, écraser ou republier les sources sans instruction explicite. Ne pas pousser ces changements dans le cadre de la PR déjà fusionnée.
- Si les sources changent encore pendant l'échantillonnage, s'arrêter et rapporter ; ne pas figer un état instable.
- La republication après dérive est un flux distinct (branche temporaire, validation, nouvelle PR) ; elle n'est pas couverte par ce Skill et n'a pas été validée dans la session source.

## Échecs fréquents

| Symptôme | Cause probable | Action |
|---|---|---|
| `command -v gh` vide | CLI absent | Utiliser l'API et le credential helper |
| Page GitHub de connexion | Session navigateur non authentifiée | Ne pas saisir d'identifiants ; passer par l'API |
| 401 / 403 | Jeton absent, expiré ou permissions insuffisantes | Arrêter ; ne pas deviner un autre jeton |
| `error: No such remote 'origin'` | Dépôt local sans remote | Utiliser `REMOTE_URL` et `refs/qoder-tmp/*` ; ne pas modifier la config Git |
| `merge-base` sortie 1, ou `compare` 404 `No common ancestor` | Histoires non reliées, branche orpheline | Ne pas créer de PR ; étape 2 bis |
| `PREFIX_EXISTS`, ou base contient déjà `.qoder/skills/$NOM` | Skill homonyme ou conflit de portée | S'arrêter et demander ; ne pas écraser |
| `awk '{print PR}'` ou `awk '{print <argument>}'` dans le corps injecté | Le CLI substitue les jetons dollar-chiffre par les arguments positionnels | Ne pas copier le bloc ; utiliser `cut -f1`/`cut -f3` ou des variables nommées (voir Étape 0) |
| `BLOB_MISMATCH` après push | Le blob poussé diffère de la source | Ne pas fusionner ; comparer `cat-file blob` et la source |
| Head absent de `ls-remote` | Branche non poussée | S'arrêter ; ne pas pousser silencieusement |
| `ahead_by=0` ou `total_commits=0` | Aucun commit entre base et head | Vérifier la branche ; ne pas créer de PR |
| `FILES_MISMATCH` ou fichier hors préfixe après création | Mauvaise base, copie sale ou portée incorrecte | Ne pas fusionner ; rapporter |
| Refs `refs/qoder-tmp/*` restantes | Nettoyage omis | `git update-ref -d` ; ne pas supprimer la branche orpheline |
| Dossier `system-commandline-sentinel-files` recréé | Effet de bord du credential helper | Supprimer uniquement ce dossier, sans toucher la config |
| `PR_CREATE_FAIL 422` | Aucun commit entre base et head, ou head inconnu | Vérifier la branche poussée et la base |
| `mergeable` reste `null` | Calcul GitHub en cours | Réessayer plus tard ; ne pas forcer |
| `mergeable=false` | Conflit ou base incompatible | Arrêter ; résoudre explicitement |
| `rebase` refusé | Méthode désactivée ou conflit | Demander ; ne pas basculer silencieusement |
| 405 / 409 à la fusion | Protection de branche, checks requis, conflit | Rapporter ; ne pas contourner |
| `VERIFY_MATCH false` après une fusion réussie | `main` a avancé après la fusion | Vérifier que le SHA de fusion est un ancêtre de `origin/main` |
| `MISMATCH` après fusion | Source modifiée après la copie | Échantillonner hash et mtime ; distinguer dérive et corruption |
| `git show "origin/main:chemin"` renvoie `ambiguous argument 'origin\main;...'` | MSYS réécrit `ref:chemin` sous Git Bash | Extraire l'OID avec `ls-tree -r`, puis `cat-file blob "$oid"` |
| Tour interrompu | Session ou outil interrompu | Relire l'état réel ; ne pas déclarer la fusion ou la republication réussie |

## Ressources

- `scripts/github_pr_api.py` : `probe`, `compare`, `files`, `status` en lecture seule ; `create` et `merge` exigent `--yes`. `compare` expose le statut, le merge-base et les fichiers ; `files` pagine les fichiers de la PR et compare leur nombre à `changed_files`.
- `references/evidence-2026-10-26.md` : preuves datées des sessions `ffc7150a`, `324c8787` et `52ce9bcb`, dépôt sans `origin`, histoires non reliées, branche de livraison reconstruite, PR sans ancêtre commun d'origine, substitution des variables positionnelles dans le corps injecté, layout et préfixe de livraison, vérification des blobs poussés, fusion rebase et contrôle post-fusion, vérifications locales des branches du script et des étapes 2/5/6, conversion MSYS de `ref:chemin`, et limites non exécutées.
- Skills liés : `publier-skill-qoder-vers-depot-git` pour l'archivage, la reconstruction et le vérificateur ; `skill-file-qa` pour la validation d'un Skill ; `commit-skill-work` pour le commit local et la séparation des changements ; `harden-skill-argument-substitution` pour auditer les variables positionnelles d'un Skill.

## Limites

- github.com uniquement ; l'API GitHub Enterprise n'est pas gérée.
- PR depuis un fork ou entre dépôts différents non gérée ; la reconstruction suppose que `$BASE` et le head sont dans `$REMOTE_URL`.
- `compare` peut plafonner la liste des fichiers ; la portée locale à trois points et `files` après création restent les contrôles de référence.
- La reconstruction est décrite pour un paquet de Skill sous `.qoder/skills/$NOM` ; un autre type de dépôt exige une portée adaptée.
- La fusion d'une branche reconstruite a été exécutée le 2026-10-26 (PR #2, `merge --method rebase`, SHA `08ca045c320edc847b564fdeed3a4fd92ab3c57e`) et vérifiée après fusion ; voir `references/evidence-2026-10-26.md`.
- Sans `origin`, les vérifications locales passent par `refs/qoder-tmp/*` ; ces refs sont temporaires et doivent être supprimées après contrôle.
- Aucune création de jeton, aucun flux OAuth, aucune automatisation de connexion navigateur.
- Aucun contournement de protection de branche, de checks requis ou de politique de fusion ; aucune fusion d'histoires non reliées.
- Aucune fusion automatique : `--yes` est une confirmation technique, pas une autorisation à la place de l'utilisateur.
