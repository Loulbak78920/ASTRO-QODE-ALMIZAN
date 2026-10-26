---
name: github-pr-create-merge-sans-gh
description: "Créer/fusionner une PR GitHub sans gh ni navigateur, via Git Credential Manager et l'API REST : probe, garde d'ancêtre commun, reconstruction depuis la base, mise à jour d'une archive existante du même Skill (frontmatter identique, aucun fichier base-only), baseline sur les OID du HEAD source, création idempotente, contrôle des fichiers et des blobs, fusion rebase, vérification post-fusion ; une dérive live non commitée est attribuée (find_writers, runtimeState) et seulement rapportée, jamais absorbée. Utiliser pour « gh absent », « créer une PR », « pas d'origin », « No common ancestor », « branche orpheline », « reconstruire depuis main », « archive obsolète », « PR ne publie que HEAD », « vérifier les fichiers de la PR », « merge PR to main », « rebase merge », « mergeable », « base a avancé », « BLOB_MISMATCH », « écriture concurrente », « live drift ». 中文触发：无 gh、无 origin、创建 PR、共同祖先 404、孤儿分支、从 main 重建、陈旧归档更新、PR 只发布 HEAD、核对 PR 文件、合并 PR 到 main、rebase 合并、mergeable 轮询、base 前进、BLOB_MISMATCH、并发写入、未提交漂移。"
---

# Créer et fusionner une pull request GitHub sans gh

## Portée

Ce Skill couvre github.com, avec un jeton déjà stocké par un credential helper Git. Il prend aussi en charge un dépôt local sans `origin` via une URL explicite et des refs temporaires locales. Une branche à historique racine indépendant ne peut pas former de PR : elle doit être reconstruite depuis la base, sans fusionner les deux historiques. Une archive déjà présente sous `$PREFIXE` n'est pas nécessairement un conflit : si le frontmatter `name` désigne le même Skill et qu'aucun fichier n'existe uniquement dans la base, elle est mise à jour. La PR publie les octets du HEAD du dépôt source, pas ceux du worktree live ; une dérive non commitée est rapportée, jamais absorbée. Il ne couvre pas GitHub Enterprise, la création de jetons, la connexion au navigateur, le contournement des protections de branche, le force push, ni la republication automatique après divergence des sources.

## Autorisations et actions irréversibles

- Sonde et lecture : libres.
- Création de PR : uniquement sur demande explicite.
- Fusion : uniquement sur demande explicite, avec la branche cible confirmée. Si l'utilisateur demande seulement de créer la PR, s'arrêter après l'étape 3 bis et donner l'URL.
- Ne jamais pousser directement sur `main` pour contourner la PR ; ne jamais faire de force push ; ne pas supprimer la branche de travail sans instruction.
- Reconstruire une branche de livraison et pousser ce nouveau head fait partie d'une demande explicite de création de PR. Ne jamais réécrire, fusionner ni supprimer la branche orpheline ; ne jamais fusionner deux historiques sans ancêtre commun.
- Mettre à jour une archive existante du même Skill fait partie de la demande de création de PR. Ne jamais supprimer un fichier présent uniquement dans la base ; s'arrêter et demander. Ne pas réécrire le dépôt source ni absorber ses modifications non commitées.
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

- Ne jamais écrire de jeton dollar-chiffre (variable positionnelle) dans un bloc de commande : lors d'un appel avec arguments, le CLI le remplace dans le corps injecté. Cas vérifié le 2026-10-26 : le jeton de numéro de champ d'un `awk` de l'étape 2 a été injecté avec `PR` à la place. Pour extraire le SHA d'un `ls-remote`, utiliser `cut -f1` (deux champs tabulés). Pour extraire un OID de `ls-tree`, utiliser `--format='%(objectname)'` : le champ 3 de `cut -f3` n'existe pas dans la sortie par défaut `<mode> <type> <oid>\t<chemin>`. Les variables nommées (`$BRANCH`, `$PREFIXE`) ne sont pas concernées par la substitution.

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
SOURCE_TOP="$(git -C "$SOURCE" rev-parse --show-toplevel 2>/dev/null || true)"
SOURCE_PREFIX="$(git -C "$SOURCE" rev-parse --show-prefix 2>/dev/null || true)"
if [ -n "$SOURCE_TOP" ] && [ -z "$SOURCE_PREFIX" ]; then
  SOURCE_HEAD="$(git -C "$SOURCE" rev-parse HEAD)"
  git -C "$SOURCE" status --porcelain -- SKILL.md references scripts | grep -v '__pycache__' | grep -v '\.pyc$' > "$TMP/source.status" || true
  if [ -s "$TMP/source.status" ]; then sed 's/^/SOURCE_DIRTY /' "$TMP/source.status"; echo SOURCE_DIRTY_STOP; exit 2; fi
  git -C "$SOURCE" ls-tree -r --format='%(objectname) %(path)' HEAD -- SKILL.md references scripts > "$TMP/head.oids"
  git -C "$SOURCE" ls-tree -r --name-only HEAD -- SKILL.md references scripts | sort > "$TMP/src.rel"
else
  SOURCE_HEAD=""
  echo SOURCE_NOT_GIT
  ( cd "$SOURCE" && { echo SKILL.md; find references scripts -type f ! -path '*/__pycache__/*' ! -name '*.pyc' 2>/dev/null; } | sort ) > "$TMP/src.rel"
fi
printf 'SOURCE_HEAD=%s\n' "${SOURCE_HEAD:-NONE}"
[ -f "$TMP/head.oids" ] || : > "$TMP/head.oids"

MAIN_FILES="$(git -C "$TMP/repo" ls-tree -r --name-only HEAD -- "$PREFIXE")"
if [ -z "$MAIN_FILES" ]; then
  echo PREFIX_ABSENT
  ARCHIVE_MODE=create
else
  MAIN_NAME_OID="$(git -C "$TMP/repo" ls-tree -r --format='%(objectname)' HEAD -- "$PREFIXE/SKILL.md")"
  n="$(printf '%s\n' "$MAIN_NAME_OID" | grep -c . || true)"
  if [ "$n" -ne 1 ]; then echo "MAIN_SKILL_INVALID count=$n"; exit 2; fi
  MAIN_NAME="$(git -C "$TMP/repo" cat-file blob "$MAIN_NAME_OID" | sed -n 's/^name:[[:space:]]*//p' | head -1 | tr -d '\r')"
  SRC_NAME="$(sed -n 's/^name:[[:space:]]*//p' "$SOURCE/SKILL.md" | head -1 | tr -d '\r')"
  printf 'MAIN_NAME=%s\nSRC_NAME=%s\n' "$MAIN_NAME" "$SRC_NAME"
  printf '%s\n' "$MAIN_FILES" | sed "s|^$PREFIXE/||" | sort > "$TMP/main.rel"
  comm -23 "$TMP/main.rel" "$TMP/src.rel" > "$TMP/main.only"
  sed 's/^/MAIN_ONLY /' "$TMP/main.only"
  if [ "$MAIN_NAME" != "$SRC_NAME" ]; then echo DIFF_SKILL; exit 2; fi
  if [ -s "$TMP/main.only" ]; then echo MAIN_ONLY_STOP; exit 2; fi
  echo ARCHIVE_UPDATE
  ARCHIVE_MODE=update
fi

mkdir -p "$TMP/repo/$PREFIXE"
cp "$SOURCE/SKILL.md" "$TMP/repo/$PREFIXE/SKILL.md"
[ -d "$SOURCE/references" ] && cp -R "$SOURCE/references" "$TMP/repo/$PREFIXE/"
[ -d "$SOURCE/scripts" ] && cp -R "$SOURCE/scripts" "$TMP/repo/$PREFIXE/"
find "$TMP/repo/$PREFIXE" -name '__pycache__' -type d -prune -exec rm -rf {} +
find "$TMP/repo/$PREFIXE" -name '*.pyc' -delete
```

- Ne copier que `SKILL.md`, `references/` et `scripts/` ; ni cache, ni fichier de travail, ni contenu hors du préfixe.
- `PREFIX_ABSENT` crée l'archive ; `ARCHIVE_UPDATE` met à jour une archive du même Skill : `MAIN_NAME` doit égaler `SRC_NAME`, `MAIN_ONLY` être vide. `DIFF_SKILL` (nom différent) et `MAIN_ONLY_STOP` (fichiers base-only) imposent l'arrêt ; ne jamais supprimer sans instruction.
- Ne pas retirer `tr -d '\r'` de l'extraction de `name:` : un checkout Windows en `core.autocrlf=true` livre `SKILL.md` en CRLF, et un outil qui préserve le CR produirait `demo\r` ≠ `demo`, donc un faux `DIFF_SKILL`. Garde couverte par la fixture du 2026-10-26 (section `45b55bd2` de l'evidence) mais non prouvée porteuse sous Git Bash ; ne pas la retirer en simplifiant le `sed`.
- Rejouer cette garde avec `py -3 "$SKILL/scripts/fixture_archive_guard.py"` : le script extrait ce bloc de `SKILL.md`, force `core.autocrlf=true` avec `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=core.autocrlf` et `GIT_CONFIG_VALUE_0=true`, produit le CRLF par `rm SKILL.md && git checkout -- .` (jamais par réécriture d'octets : cache stat périmé, `git status` affiche ` M` alors que `git diff --quiet` sort 0, `git update-index --refresh` ne corrige pas, `git add` est une écriture), et couvre `ARCHIVE_UPDATE`, `DIFF_SKILL`, `MAIN_ONLY_STOP` et `SOURCE_DIRTY_STOP`.
- Pour la garde `name:`, asserter d'abord `rc=0` et `ARCHIVE_UPDATE` dans la même sortie, puis l'absence de `DIFF_SKILL` : un arrêt précoce sur `SOURCE_DIRTY_STOP` rend l'assertion « pas de `DIFF_SKILL` » vide.
- `SOURCE_DIRTY_STOP` : le périmètre source contient des modifications non commitées. S'arrêter et demander ; la PR ne publie que le HEAD commité.
- `SOURCE_NOT_GIT` : `$SOURCE` n'est pas la racine d'un dépôt Git (ou en est un sous-dossier). Pas de baseline HEAD ; le mode live reste possible avec échantillonnage de stabilité, mais la comparaison PR/HEAD de l'étape 3 bis est indisponible.
- Si aucun `PRECEDENT` n'apparaît, ne pas inventer un préfixe : utiliser le layout de la base et demander confirmation avant de copier. Le clone `$TMP/probe` est en lecture seule (`--no-checkout`) ; il est supprimé avec `$TMP`.

Comparer la copie aux octets commités de la source, fichier par fichier :

```bash
if [ -n "$SOURCE_HEAD" ]; then
  bad=0
  while read -r oid rel; do
    dst_oid="$(git -C "$TMP/repo" hash-object --path="$rel" "$TMP/repo/$PREFIXE/$rel")"
    if [ "$dst_oid" = "$oid" ]; then echo "COPY_MATCH_HEAD $rel $oid"; else echo "COPY_MISMATCH_HEAD $rel head=$oid got=$dst_oid"; bad=$((bad + 1)); fi
  done < "$TMP/head.oids"
  [ "$bad" -eq 0 ] && echo COPY_MATCH || echo COPY_MISMATCH
else
  ( cd "$SOURCE" && find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' -print0 | sort -z | xargs -0 sha256sum ) > "$TMP/src.sha"
  ( cd "$TMP/repo/$PREFIXE" && find . -type f -print0 | sort -z | xargs -0 sha256sum ) > "$TMP/dst.sha"
  diff "$TMP/src.sha" "$TMP/dst.sha" && echo COPY_MATCH || echo COPY_MISMATCH
fi
```

- `COPY_MISMATCH` : ne pas committer ; expliquer l'écart.
- En mode HEAD, la référence est le blob commité (`COPY_MATCH_HEAD`), pas le fichier live : une modification non commitée après la copie est traitée comme dérive à l'étape 3 bis. En mode live, exiger deux échantillons `size`/`mtime`/SHA-256 identiques depuis la copie, sinon recommencer.

Publier la branche de livraison :

```bash
git -C "$TMP/repo" switch -c "merge/skill-$NOM"
git -C "$TMP/repo" add "$PREFIXE"
git -C "$TMP/repo" status --short
MSG="docs(skill): $([ "$ARCHIVE_MODE" = update ] && echo actualiser || echo archiver) $NOM"
git -C "$TMP/repo" commit -m "$MSG"
git -C "$TMP/repo" push "$REMOTE_URL" "merge/skill-$NOM:merge/skill-$NOM"
BRANCH="merge/skill-$NOM"
HEAD_SHA="$(git -C "$TMP/repo" rev-parse HEAD)"
REMOTE_HEAD="$(git -C "$TMP/repo" ls-remote "$REMOTE_URL" "refs/heads/$BRANCH" | cut -f1)"
printf 'HEAD_SHA=%s\nREMOTE_HEAD=%s\n' "$HEAD_SHA" "$REMOTE_HEAD"
[ "$REMOTE_HEAD" = "$HEAD_SHA" ] && echo HEAD_SYNC || echo HEAD_MISMATCH
git -C "$TMP/repo" ls-tree -r --name-only HEAD -- "$PREFIXE"
```

- `git add` explicite : jamais `git add -A`. Vérifier `status --short` avant de committer.
- En `ARCHIVE_UPDATE`, `status --short` doit montrer `M` ou `A` sous `$PREFIXE` ; aucun `D`, sinon arrêt.
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
LISTE="$(mktemp)"
git -C "$TMP/repo" ls-tree -r --name-only HEAD -- "$PREFIXE" > "$LISTE"
bad=0
drift=0
while IFS= read -r f; do
  rel="${f#"$PREFIXE"/}"
  oid="$(git -C "$TMP/repo" ls-tree -r --format='%(objectname)' HEAD -- "$f")"
  n="$(printf '%s\n' "$oid" | grep -c . || true)"
  if [ "$n" -ne 1 ]; then echo "OID_INVALID $rel count=$n"; bad=$((bad + 1)); continue; fi
  if [ -n "${SOURCE_HEAD:-}" ]; then
    head_oid="$(git -C "$SOURCE" ls-tree -r --format='%(objectname)' HEAD -- "$rel")"
    hn="$(printf '%s\n' "$head_oid" | grep -c . || true)"
    if [ "$hn" -ne 1 ]; then echo "HEAD_OID_INVALID $rel count=$hn"; bad=$((bad + 1)); continue; fi
    if [ "$oid" = "$head_oid" ]; then echo "BLOB_MATCH_HEAD $rel $oid"; else echo "BLOB_MISMATCH_HEAD $rel published=$oid head=$head_oid"; bad=$((bad + 1)); fi
    if [ -f "$SOURCE/$rel" ]; then
      pub="$(git -C "$TMP/repo" cat-file blob "$oid" | sha256sum | cut -d' ' -f1)"
      live="$(sha256sum < "$SOURCE/$rel" | cut -d' ' -f1)"
      [ "$pub" = "$live" ] || { echo "LIVE_DRIFT $rel published=$pub live=$live"; drift=$((drift + 1)); }
    else
      echo "LIVE_MISSING $rel"; drift=$((drift + 1))
    fi
  else
    if [ ! -f "$SOURCE/$rel" ]; then echo "SRC_MISSING $rel"; bad=$((bad + 1)); continue; fi
    pub="$(git -C "$TMP/repo" cat-file blob "$oid" | sha256sum | cut -d' ' -f1)"
    src="$(sha256sum < "$SOURCE/$rel" | cut -d' ' -f1)"
    if [ "$pub" = "$src" ]; then echo "BLOB_MATCH $rel $pub"; else echo "BLOB_MISMATCH $rel published=$pub source=$src"; bad=$((bad + 1)); fi
  fi
done < "$LISTE"
rm -f "$LISTE"
[ "$bad" -eq 0 ] && echo BLOBS_OK || echo "BLOBS_FAIL bad=$bad"
printf 'LIVE_DRIFT_COUNT=%s\n' "$drift"
```

- Attendu : chaque `FILE` est `added` avec deletions `-0` en création, ou `modified`/`added` en `ARCHIVE_UPDATE` ; son chemin commence par `$PREFIXE` ; aucun `removed` (aucune suppression dans ce flux) ; `FILES n` égale le nombre de fichiers modifiés ou ajoutés par la copie (création : tous ; mise à jour : seulement les changements, donc moins que l'archive ; cas PR #4 : 2 vs 7), tandis que `BLOBS_OK` couvre tous les fichiers sous `$PREFIXE`.
- `BLOBS_OK` exige un `BLOB_MATCH_HEAD` (ou `BLOB_MATCH` sans HEAD) par fichier de l'archive sous `$PREFIXE` (ex. 7), pas seulement par fichier changé de la PR (ex. 2). `OID_INVALID`/`HEAD_OID_INVALID count=0` signifie que l'extraction a échoué, pas que le blob est vide : ne pas passer `cat-file`.
- `BLOB_MISMATCH_HEAD` compare les OID Git de la PR et du HEAD source ; c'est le contrôle bloquant. Il ne dépend ni du worktree, ni de `core.autocrlf`.
- `LIVE_DRIFT` signale que le fichier source non commité diffère du blob publié ; `LIVE_DRIFT_COUNT` compte ces fichiers. Une dérive live seule laisse `BLOBS_OK`, mais annonce que `main` ne contiendra pas ces octets.
- `PR_FILES changed=` doit égaler `FILES n` (fichiers changés, pas le total de l'archive) ; sinon `FILES_MISMATCH` et arrêt.
- Vérifier que `PR_BASE` est `$BASE`, que le head SHA égale `REMOTE_HEAD` et que `PR_MERGEABLE` est `true` ou `null` (en calcul).
- `HEAD_SYNC` a établi que le commit poussé est celui du clone ; ces blobs sont donc ceux du distant. Sous `core.autocrlf=true`, l'avertissement `LF will be replaced by CRLF` concerne la copie de travail, pas le blob : comparer les OID et SHA-256 des blobs.
- Un `BLOBS_FAIL`, un fichier sans source, ou toute surprise (fichier hors préfixe, suppression, binaire, nombre différent) : ne pas fusionner ; rapporter, et ne fermer la PR que sur instruction explicite.
- Si l'utilisateur n'a demandé que la création, s'arrêter après cette vérification.
- Nettoyer ensuite `$TMP`, les refs `refs/qoder-tmp/base|head` et tout fichier de corps temporaire ; en cas de fusion demandée, conserver `$TMP` (dont `$TMP/head.oids`) jusqu'à l'étape 5. Ne pas supprimer la branche orpheline ni la branche de livraison sans instruction.

### Attribuer une dérive live

Si `LIVE_DRIFT_COUNT` n'est pas 0, identifier l'écrivain avant de conclure. Ne jamais committer ces octets dans la PR ni les recopier après coup : la PR reste alignée sur `SOURCE_HEAD`.

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/commit-skill-work/scripts/find_writers.py" \
  --target "$SOURCE" \
  --jsonl-dir "C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI"
```

- Sortie : une ligne `SESSION <id> | last <horodatage> | <outil> | <fichier> | records <n>` par écrivain, puis `RESULT FOUND n session(s)`. Puis `read_chat_session` sur la session la plus récente : relever `runtimeState`, `activeTurnId`, `revision`.
- `runtimeState=ready` (ou `waiting-user`) avec une intention explicite de ne pas committer (« A : seulement mettre à jour et vérifier ») : rapporter la dérive et continuer ; l'écart est assumé.
- `runtimeState=running`, `activeTurnId` non nul, intention inconnue, ou `LIVE_MISSING` (fichier live disparu alors que HEAD le contient) : s'arrêter avant fusion. Ne pas absorber l'écriture, ne pas committer à la place de l'autre session.
- Deux échantillons stables à l'étape 2 bis ne prouvent pas l'absence d'un écrivain futur ; `find_writers` et l'état de session font foi.

## Étape 4 — Fusionner

Uniquement après instruction explicite de fusion et confirmation de la branche cible.

```bash
py -3 "$SKILL/scripts/github_pr_api.py" merge \
  --repo "$REPO" --pr "$N" --method rebase --yes
```

- `merge` exige `--yes` et refuse avant tout appel réseau sans ce drapeau.
- Ne pas fusionner après `BLOBS_FAIL` : la PR ne publie pas les octets attendus.
- Une dérive live seule (`LIVE_DRIFT_COUNT` non nul, `BLOBS_OK`) ne bloque pas si l'écrivain est `ready` avec une intention explicite de ne pas committer ; le rapport doit alors dire que `main` ne contiendra pas ces octets live.
- Conserver `$TMP` et `$TMP/head.oids` jusqu'à l'étape 5 : ils servent de référence après fusion.
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
oids="$(git -C "$DEPOT" ls-tree -r --format='%(objectname)' origin/main -- "$PREFIXE")"
printf 'OID_COUNT=%s\n' "$(printf '%s\n' "$oids" | grep -c . || true)"
if [ -z "$oids" ]; then
  echo OID_LIST_EMPTY
else
  for oid in $oids; do
    git -C "$DEPOT" cat-file blob "$oid" | sha256sum
  done
fi
git -C "$DEPOT" ls-tree -r --name-only origin/main -- "$PREFIXE" > "$TMP/main.rel.liste"
bad=0
while IFS= read -r f; do
  rel="${f#"$PREFIXE"/}"
  merged="$(git -C "$DEPOT" ls-tree -r --format='%(objectname)' origin/main -- "$f")"
  head_oid=""
  while read -r oid path; do [ "$path" = "$rel" ] && head_oid="$oid"; done < "$TMP/head.oids"
  [ -n "$head_oid" ] || head_oid="$(git -C "$TMP/repo" ls-tree -r --format='%(objectname)' HEAD -- "$PREFIXE/$rel")"
  if [ -n "$head_oid" ] && [ "$merged" = "$head_oid" ]; then echo "MERGED_BLOB_MATCH $rel $merged"; else echo "MERGED_BLOB_MISMATCH $rel merged=$merged head=$head_oid"; bad=$((bad + 1)); fi
done < "$TMP/main.rel.liste"
[ "$bad" -eq 0 ] && echo MERGED_BLOBS_OK || echo "MERGED_BLOBS_FAIL bad=$bad"
git -C "$DEPOT" merge --ff-only origin/main
git -C "$DEPOT" diff --name-status "$HEAD_PR" origin/main -- "$PREFIXE"
```

- Immédiatement après la fusion, comparer le SHA de fusion de l'API, `origin/main`, `ls-remote` et le fast-forward local : ils doivent désigner le même commit. Si `main` a avancé depuis, le SHA de fusion doit être un ancêtre de `origin/main`, pas nécessairement la tête.
- Recalculer les SHA-256 des blobs distants, puis comparer chaque OID fusionné aux OID du HEAD source enregistrés dans `$TMP/head.oids` ; sans baseline HEAD (`SOURCE_NOT_GIT`, fichier vide) la référence est le blob du head de PR. `MERGED_BLOBS_OK` est requis ; comparer au worktree live serait faux.
- Si `LIVE_DRIFT_COUNT` était non nul à l'étape 3 bis, ces octets live ne sont pas dans `main` : le rapport doit le dire explicitement. Ne pas les publier après coup sans nouvelle instruction.
- `OID_COUNT` doit égaler le nombre de fichiers attendus sous `$PREFIXE` ; `OID_LIST_EMPTY` signifie qu'aucun blob n'a été lu et que la preuve est vide.
- Le diff limité au préfixe entre le head de PR et `origin/main` doit être vide après une fusion rebase.
- Vérifier que le worktree est propre et que la branche locale est à jour avec `git status -sb`.
- Sans `origin`, faire `git -C "$DEPOT" fetch "$REMOTE_URL" "+refs/heads/$BASE:refs/qoder-tmp/base"` et remplacer `origin/main` par `refs/qoder-tmp/base` dans les commandes ci-dessus ; supprimer la ref après contrôle.
- Si le dépôt contient un vérificateur d'archive, utiliser `publier-skill-qoder-vers-depot-git` et son script `verifier_archive_skill.py` en mode `--from remote`.

## Étape 6 — Traiter une divergence des sources après fusion

Un `MISMATCH` du vérificateur ne prouve pas une corruption de l'archive. Il peut signaler une écriture concurrente dans les fichiers source.

```bash
oids="$(git -C "$DEPOT" ls-tree -r --format='%(objectname)' origin/main -- "$CHEMIN")"
n="$(printf '%s\n' "$oids" | grep -c . || true)"
printf 'OID_COUNT=%s\n' "$n"
if [ "$n" -ne 1 ]; then
  echo "OID_INVALID $CHEMIN count=$n"
else
  oid="$oids"
  git -C "$DEPOT" cat-file blob "$oid" > /tmp/publie
  sha256sum /tmp/publie "$SOURCE/$CHEMIN"
  stat -c '%y %s %n' "$SOURCE/$CHEMIN"
  for i in 1 2 3; do sha256sum "$SOURCE/$CHEMIN"; stat -c '%y %s' "$SOURCE/$CHEMIN"; sleep 2; done
fi
```

- Vérifier que `OID_COUNT` vaut exactement 1 ; `count=0` signifie un chemin absent ou une extraction vide, `count>1` un chemin ambigu. Dans les deux cas, ne pas lire de blob et s'arrêter. Ne pas utiliser `git show "origin/main:$CHEMIN"` sous Git Bash : MSYS réécrit l'argument en `origin\main;...` et Git répond `ambiguous argument`. Extraire l'OID puis lire le blob évite cette conversion.
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
| `PREFIX_ABSENT`, ou base sans `.qoder/skills/$NOM` | Archive absente | Créer l'archive (`ARCHIVE_MODE=create`) |
| `ARCHIVE_UPDATE` | Archive existante du même Skill, sans fichier base-only | Actualiser, sans s'arrêter sur la seule présence du préfixe |
| `DIFF_SKILL` | Le `name` du frontmatter de la base diffère de la source | Ne pas écraser un Skill homonyme ; arrêter |
| `DIFF_SKILL` sur un checkout Windows | `SKILL.md` du worktree en CRLF (`core.autocrlf=true`) : l'extraction de `name:` peut garder un `\r` alors que le blob de base est en LF | Conserver `tr -d '\r'` sur `MAIN_NAME` et `SRC_NAME` ; ne pas le retirer. Sous Git Bash, `sed` retire déjà le CR : garde portable, couverte par la fixture mais non prouvée porteuse. |
| `MAIN_ONLY_STOP` | La base contient des fichiers absents de la source | Ne jamais supprimer ; arrêter et demander |
| `SOURCE_DIRTY_STOP` | Le périmètre source a des modifications non commitées | Arrêter ; la PR ne publie que le HEAD commité |
| `SOURCE_NOT_GIT` | `$SOURCE` n'est pas la racine d'un dépôt Git | Pas de baseline HEAD ; comparaison live seulement |
| `awk '{print PR}'` ou `awk '{print <argument>}'` dans le corps injecté | Le CLI substitue les jetons dollar-chiffre par les arguments positionnels | Ne pas copier le bloc ; utiliser `cut -f1` pour `ls-remote`, `--format='%(objectname)'` pour un OID de `ls-tree`, ou des variables nommées (voir Étape 0) |
| `BLOB_MISMATCH_HEAD` après push | Un blob de la PR diffère du HEAD source | Ne pas fusionner ; comparer les OID `cat-file`/`ls-tree` |
| `BLOB_MISMATCH` (sans HEAD) après push | Le blob poussé diffère du fichier source live | Ne pas fusionner ; comparer `cat-file blob` et la source |
| `LIVE_DRIFT` avec `BLOBS_OK` | Le fichier live a changé après le dernier commit | Attribuer avec `find_writers` et `read_chat_session` ; ne pas absorber ces octets |
| `find_writers` : session `running`, `activeTurnId` non nul | Écrivain encore actif | S'arrêter avant fusion ; ne pas committer à sa place |
| `fatal: Not a valid object name`, puis SHA-256 `e3b0c442…` (flux vide) | `cut -f3` appliqué à la sortie par défaut de `ls-tree` : la ligne est `<mode> <type> <oid>\t<chemin>`, il n'y a pas de 3e champ tabulé | Extraire l'OID avec `git ls-tree -r --format='%(objectname)'` ; exiger exactement un OID non vide avant `cat-file` |
| Head absent de `ls-remote` | Branche non poussée | S'arrêter ; ne pas pousser silencieusement |
| `ahead_by=0` ou `total_commits=0` | Aucun commit entre base et head | Vérifier la branche ; ne pas créer de PR |
| `FILES_MISMATCH`, ou `FILES n` inférieur au nombre de fichiers de l'archive en `ARCHIVE_UPDATE` | Confusion entre fichiers changés et total de l'archive, mauvaise base ou copie sale | Comparer `FILES n` à `PR_FILES changed`, pas au total ; exiger un blob par fichier de l'archive ; ne pas fusionner sur un vrai écart |
| Refs `refs/qoder-tmp/*` restantes | Nettoyage omis | `git update-ref -d` ; ne pas supprimer la branche orpheline |
| Dossier `system-commandline-sentinel-files` recréé | Effet de bord du credential helper | Supprimer uniquement ce dossier, sans toucher la config |
| `PR_CREATE_FAIL 422` | Aucun commit entre base et head, ou head inconnu | Vérifier la branche poussée et la base |
| `mergeable` reste `null` | Calcul GitHub en cours | Réessayer plus tard ; ne pas forcer |
| `mergeable=false` | Conflit ou base incompatible | Arrêter ; résoudre explicitement |
| `rebase` refusé | Méthode désactivée ou conflit | Demander ; ne pas basculer silencieusement |
| 405 / 409 à la fusion | Protection de branche, checks requis, conflit | Rapporter ; ne pas contourner |
| `VERIFY_MATCH false` après une fusion réussie | `main` a avancé après la fusion | Vérifier que le SHA de fusion est un ancêtre de `origin/main` |
| `MISMATCH` après fusion | Source modifiée après la copie | Échantillonner hash et mtime ; distinguer dérive et corruption |
| `git show "origin/main:chemin"` renvoie `ambiguous argument 'origin\main;...'` | MSYS réécrit `ref:chemin` sous Git Bash | Extraire l'OID avec `git ls-tree -r --format='%(objectname)'`, puis `cat-file blob "$oid"` |
| Tour interrompu | Session ou outil interrompu | Relire l'état réel ; ne pas déclarer la fusion ou la republication réussie |

## Ressources

- `scripts/github_pr_api.py` : `probe`, `compare`, `files`, `status` en lecture seule ; `create` et `merge` exigent `--yes`. `compare` expose le statut, le merge-base et les fichiers ; `files` pagine les fichiers de la PR et compare leur nombre à `changed_files`.
- `scripts/fixture_archive_guard.py` : fixture jetable (réseau local `file://` uniquement) qui extrait le bloc de l'étape 2 bis de `SKILL.md`, vérifie `core.autocrlf=true` et un checkout réel en `w/crlf`, puis asserte `ARCHIVE_UPDATE`/`DIFF_SKILL`/`MAIN_ONLY_STOP`/`SOURCE_DIRTY_STOP` ; `RESULT PASS=n FAIL=m`, rc 0/1/2 ; `--skill-md` permet un test de mutation hors du dépôt.
- `references/evidence-2026-10-26.md` : preuves datées des sessions `ffc7150a`, `324c8787`, `52ce9bcb`, `2c0b2667`, `c0032f4e`, `b5dc7bbb` et `45b55bd2`, dépôt sans `origin`, histoires non reliées, branche de livraison reconstruite, PR sans ancêtre commun d'origine, substitution des variables positionnelles dans le corps injecté, layout et préfixe de livraison, mise à jour d'une archive existante du même Skill, écart `FILES n` (fichiers changés) vs total de l'archive et fusion non exécutée (PR #4), baseline sur les OID du HEAD source, dérive live et attribution des écrivains, vérification des blobs poussés, extraction d'OID `ls-tree` (`cut -f3` vide, `--format='%(objectname)'`), fusion rebase et contrôle post-fusion, vérifications locales des branches du script et des étapes 2/5/6, conversion MSYS de `ref:chemin`, garde CRLF du `name:` en checkout Windows, et limites non exécutées.
- Skills liés : `publier-skill-qoder-vers-depot-git` pour l'archivage, la reconstruction et le vérificateur ; `skill-file-qa` pour la validation d'un Skill ; `commit-skill-work` pour le commit local, la séparation des changements et son script `find_writers.py` (attribution des écrivains) ; `harden-skill-argument-substitution` pour auditer les variables positionnelles d'un Skill.

## Limites

- github.com uniquement ; l'API GitHub Enterprise n'est pas gérée.
- PR depuis un fork ou entre dépôts différents non gérée ; la reconstruction suppose que `$BASE` et le head sont dans `$REMOTE_URL`.
- `compare` peut plafonner la liste des fichiers ; la portée locale à trois points et `files` après création restent les contrôles de référence.
- La reconstruction est décrite pour un paquet de Skill sous `.qoder/skills/$NOM` ; un autre type de dépôt exige une portée adaptée.
- La fusion d'une branche reconstruite a été exécutée le 2026-10-26 (PR #2, `merge --method rebase`, SHA `08ca045c320edc847b564fdeed3a4fd92ab3c57e`) et vérifiée après fusion ; voir `references/evidence-2026-10-26.md`.
- L'extraction d'OID `ls-tree` a échoué le 2026-10-26 dans la session `2c0b2667` (`cut -f3` vide, `fatal: Not a valid object name`, SHA-256 de flux vide) ; la forme `--format='%(objectname)'` avec assertion d'un OID unique a été utilisée pour vérifier puis fusionner la PR #3 d'IMAM8MAHDI/qoder-skills (`2d013354002370f241d14fa263829fb41221e8c0`).
- Le 2026-10-26, la session `c0032f4e` a actualisé une archive existante du même Skill et créé la PR #3 du dépôt ASTRO (`ARCHIVE_UPDATE`, 7/7 `BLOB_MATCH_HEAD`), sans fusion : la vérification post-fusion de ce cas n'est pas exécutée. Dans la même session, une dérive live a produit `BLOBS_FAIL bad=2` contre les fichiers live alors que la PR correspondait au HEAD 7/7 ; elle a été attribuée à une session `ready` déclarant ne pas committer. Le cas d'un écrivain `running` et les branches `DIFF_SKILL`/`MAIN_ONLY_STOP`/`SOURCE_DIRTY_STOP` n'ont pas été déclenchés par une PR réelle ; ils l'ont été en fixture jetable le 2026-10-26 (48/48, dont un checkout CRLF), et la garde `tr -d '\r'` n'y a pas été prouvée porteuse, MSYS `sed` retirant déjà le CR.
- Le 2026-10-26, la session `b5dc7bbb` a créé la PR #4 du dépôt ASTRO pour `commit-skill-work` (`ARCHIVE_UPDATE` : 2 fichiers `modified +2/-2`, `FILES 2`, archive de 7 fichiers, 7/7 `RESULT PASS`). Le tour final « merge PR #4 with squash » a échoué sans appel d'outil : la fusion squash n'est pas exécutée ni vérifiée, et `main` restait `24d9ac2` à la fin du tour de création.
- Enregistrer `$TMP/head.oids` avant toute copie est une règle de durcissement : la session `c0032f4e` n'établit pas que l'enregistrement a eu lieu avant la création de la PR, seulement que la comparaison PR/HEAD a conclu 7/7.
- Sans `origin`, les vérifications locales passent par `refs/qoder-tmp/*` ; ces refs sont temporaires et doivent être supprimées après contrôle.
- Aucune création de jeton, aucun flux OAuth, aucune automatisation de connexion navigateur.
- Aucun contournement de protection de branche, de checks requis ou de politique de fusion ; aucune fusion d'histoires non reliées.
- Aucune fusion automatique : `--yes` est une confirmation technique, pas une autorisation à la place de l'utilisateur.
