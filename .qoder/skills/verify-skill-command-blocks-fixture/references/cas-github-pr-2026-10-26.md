# Cas vérifié — github-pr-create-merge-sans-gh (2026-10-26)

## Contexte

- Session source : `806cc849-0d65-4e8d-8222-c814cf235e04`, titre « 更新 GitHub PR Skill ».
- Snapshot `read_chat_session` : `runtimeState=cold`, `revision=0`, 8 messages, `hasMoreBefore=false`.
- JSONL brut : `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\806cc849-0d65-4e8d-8222-c814cf235e04.jsonl`, 2 756 080 octets au moment de la lecture.
- Cible : `C:\Users\Administrateur\.qoder\skills\github-pr-create-merge-sans-gh`.
- Objectif : vérifier que les blocs bash des étapes 3 bis, 5 et 6 tiennent leurs invariants après la correction de l'extraction d'OID (`ls-tree --format='%(objectname)'`).
- Instructions utilisateur : « 按此方案执行 » (tour 2), « 运行完整测试套件 » (tour 4), « run full tests with patched fixture » (tour 6).

## 1. Extraction et empreintes

L'extraction a trouvé 16 blocs bash. Trois blocs ont été extraits par ancre unique :

| Nom | Ancre | Lignes | SHA-256 du bloc |
|---|---|---|---|
| `step3bis` | `echo BLOBS_OK \|\| echo "BLOBS_FAIL bad=$bad"` | 28 | `865a5a7c28433ee571a329dcba4cb7bd64fcaa5267cb9eadcda0ccb9c3f8581a` |
| `step5` | `echo OID_LIST_EMPTY` | 17 | `47db54c94ad023742073d6a59b8d472cfcbd1e90e23526da88b77c31a1db4f2b` |
| `step6` | `cat-file blob "$oid" > /tmp/publie` | 12 | `9dded8efbe870cea614f0e0f498a26e63f92e9b88d7515e09283f59f8721c028` |

Empreintes de référence :

```text
SKILL.md            28232 octets, 399 lignes (wc -l), sha256=2342cd456fc5519f5d9a8a8f6ae84e00ae116f01894409b6ebe20f61cf4334a1
references/evidence f6ec91f4656538d4e6a6079908748478da9d4afaf7b3f03c52dbad01bd0ac408
scripts/github_pr_api.py 16551 octets, sha256=cf3b6f345be724c1fef2631f9c4d138f0bb86a85e00dfb9f3424cb3d7cf098b8
Git HEAD            fbf5e7c ; worktree M SKILL.md + M references/evidence-2026-10-26.md
```

Le `SKILL.md` courant a été relu le 2026-10-26 : ces empreintes sont identiques à celles de la session source.

## 2. Pourquoi 20/20 était un faux vert

Le premier harnais, après la correction d'OID, a rendu **20 PASS / 0 FAIL**. Ses réglages masquaient le défaut :

- `SOURCE="$REPO"` pour l'étape 6 : `$SOURCE/$CHEMIN` devenait `$REPO/.qoder/skills/demo/SKILL.md`, qui existe dans le clone ;
- un seul dépôt et un seul clone, sans `origin/main` obligatoire ;
- pas de source indépendante, donc aucune séparation entre chemin relatif au dépôt et chemin relatif à la source.

Répartition des 20 assertions : A0 2, A1 2, B 2, C 2, D 2, E1 3, E2 2, F1 2, F2 2, F3 1.

Un `PASS` sur un chemin qui existe ne prouve pas que la composition de chemins est correcte.

## 3. Harnais complet non patché — 27/29

Le harnais complet sépare les racines :

```text
ROOT/
├── src/          # arborescence source indépendante (SKILL.md, references/, scripts/)
├── seed/         # dépôt avec commit de base + commit du préfixe
├── origin.git/   # clone nu
├── repo/         # clone à HEAD (état après PR)
├── depot/        # clone remis au commit de base (avant fusion)
└── blocks/       # blocs extraits
```

Réglages : `PREFIXE=".qoder/skills/demo"`, `SRC="$ROOT/src"`, `SEED="$ROOT/seed"`, `REPO="$ROOT/repo"`, `DEPOT="$ROOT/depot"`, `ORIGIN="$ROOT/origin.git"`.

Premier incident : le seed était initialisé sans branche explicite ; le dépôt par défaut était `master`, donc `origin/main` manquait. Correction : `git init -b main` / `git branch -M main`, puis `git -C "$REPO" rev-parse --verify origin/main`.

Résultat du bloc `step6` non patché :

```text
OID_COUNT=1
2b0f515475e9f05229281454ecd6477b5cbe15e8e2184b2d3ec8a94b6f72a0b6 */tmp/publie
sha256sum: '.../src/.qoder/skills/demo/SKILL.md': No such file or directory
stat: cannot stat '.../src/.qoder/skills/demo/SKILL.md': No such file or directory
...
FAIL step6_hash_lines exp=[5] got=[1]
FAIL step6_stat_lines exp=[4] got=[0]
RESULT PASS=27 FAIL=2
```

Cause : `CHEMIN` est relatif au dépôt (`.qoder/skills/demo/SKILL.md`), mais le bloc le concatène à `$SOURCE`, qui est l'arborescence source (`$ROOT/src`). Le fichier attendu serait `$ROOT/src/SKILL.md` ; le chemin `$ROOT/src/.qoder/skills/demo/SKILL.md` n'existe pas. La garde d'OID est correcte (`OID_COUNT=1`) ; c'est la composition de chemins qui est fausse.

Les 27 autres assertions passent, notamment :

- `raw_default_fields=2`, `old_cut_f3_empty`, `new_format_oid_len=40` ;
- `step3bis_blobs_ok`, 3 `BLOB_MATCH`, 0 mismatch, 0 `OID_INVALID` ;
- dérive → `BLOBS_FAIL bad=1` + 1 `BLOB_MISMATCH` ;
- source absente → `SRC_MISSING references/r.md` + `BLOBS_FAIL bad=1` ;
- `guard_missing_file_count=0`, `guard_directory_count=3` ;
- `step5_oid_count_3`, 3 lignes de hash, fast-forward, worktree propre, 3 ajouts, diff vide ;
- préfixe inconnu → `OID_COUNT=0` + `OID_LIST_EMPTY` ;
- `step6_single_oid`, blob identique à la source, `OID_INVALID count=0` pour un chemin absent, `OID_INVALID count=3` pour un répertoire, aucun `/tmp/publie` en cas d'OID invalide.

## 4. Rustine candidate — 30/30

Rustine appliquée uniquement au bloc extrait :

```diff
   oid="$oids"
+  rel="${CHEMIN#"$PREFIXE"/}"
   git -C "$DEPOT" cat-file blob "$oid" > /tmp/publie
-  sha256sum /tmp/publie "$SOURCE/$CHEMIN"
-  stat -c '%y %s %n' "$SOURCE/$CHEMIN"
-  for i in 1 2 3; do sha256sum "$SOURCE/$CHEMIN"; stat -c '%y %s' "$SOURCE/$CHEMIN"; sleep 2; done
+  sha256sum /tmp/publie "$SOURCE/$rel"
+  stat -c '%y %s %n' "$SOURCE/$rel"
+  for i in 1 2 3; do sha256sum "$SOURCE/$rel"; stat -c '%y %s' "$SOURCE/$rel"; sleep 2; done
```

Contrôles du patch avant exécution :

```text
PATCH_APPLIED replacements=4 original_sha256=9dded8efbe870cea614f0e0f498a26e63f92e9b88d7515e09283f59f8721c028
EXTRACT_OK step6 lines=13 sha256=19684c45e9417060e9c59e2f4e3a8e2d4252a4b77180e68873a01fdca50fe764
```

Résultat du candidat seul :

```text
CANDIDATE_EXIT=0
OID_COUNT=1
2b0f5154... */tmp/publie
2b0f5154... *.../src/SKILL.md
2026-10-26 18:50:45.581862200 +0100 11 .../src/SKILL.md
...
HASH_LINES=5
STAT_LINES=4
ERROR_LINES=0
```

Harnais complet patché : **30 PASS / 0 FAIL**. Les deux échecs disparaissent ; `step6_path_errors=0` est la 30e assertion. Le code de sortie du harnais est 0.

## 5. QA et état du Skill installé

QA statique sur le Skill cible :

```text
Files (3): SKILL.md, references/evidence-2026-10-26.md, scripts/github_pr_api.py
PASS frontmatter, name, description (1006 chars, single line), body (395 lines)
PASS local references: 4 checked
PASS skill references: 4 checked
Code blocks: python=0 js=0 skipped=16
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
```

`skipped=16` est la preuve que la QA n'a exécuté aucun bloc bash. Le `RESULT PASS` ne couvre pas les 29/30 assertions du harnais.

État après les tests :

```text
Git HEAD fbf5e7c
M SKILL.md
M references/evidence-2026-10-26.md
SKILL.md sha256=2342cd45...
scripts/github_pr_api.py sha256=cf3b6f34...
aucun /tmp/publie
aucun __pycache__
```

Le Skill installé n'a pas reçu la rustine : `SKILL.md` utilise encore `$SOURCE/$CHEMIN` aux lignes 341–343. La rustine n'a existé que dans le harnais supprimé. L'appliquer au Skill installé est une édition distincte, avec QA et nouveau harnais ; elle n'a pas été demandée dans la session source et n'a pas été faite ici.

## 6. Reproduction

Depuis Git Bash, avec le Skill cible inchangé :

```bash
TARGET="$HOME/.qoder/skills/github-pr-create-merge-sans-gh"
ROOT="$(mktemp -d "$HOME/.qoder/tmp/case-github-pr-XXXXXX")"
mkdir -p "$ROOT/blocks" "$ROOT/src/references" "$ROOT/src/scripts"
py -3 "$HOME/.qoder/skills/verify-skill-command-blocks-fixture/scripts/extract_bash_blocks.py" \
  "$TARGET/SKILL.md" --out-dir "$ROOT/blocks" \
  --anchor 'step3bis=echo BLOBS_OK || echo "BLOBS_FAIL bad=$bad"' \
  --anchor 'step5=echo OID_LIST_EMPTY' \
  --anchor 'step6=cat-file blob "$oid" > /tmp/publie'
```

Attendu : `BLOCK_COUNT=16`, `SKILL_SHA256=2342cd45...`, les trois `EXTRACT_OK` avec les hashes du tableau §1, `EXTRACT_RESULT=PASS`. Le harnais §7 construit lui-même la fixture (source, seed, origin, clones) ; il suffit d'avoir extrait les trois blocs dans `$ROOT/blocks`. Sans rustine : 27/29. Avec la rustine du §4 : 30/30. Vérifier `sha256sum "$TARGET/SKILL.md"` avant et après ; il doit rester `2342cd45...`.

## 7. Harnais complet (30 assertions)

Le harnais ci-dessous est celui de la course patchée. Avant de l'exécuter, placer le candidat dans `$ROOT/blocks/step6.sh` : `cp "$ROOT/blocks/step6_candidate.sh" "$ROOT/blocks/step6.sh"`. Exécuté sans cette copie, le harnais rejoue le bloc d'origine et rend 27 PASS / 3 FAIL (`step6_path_errors` compte 8 `No such file`). Pour la course non patchée, retirer la ligne `step6_path_errors` et utiliser le bloc `step6.sh` original ; on obtient 29 assertions et 27 PASS / 2 FAIL.

Les trois invocations de `step6` exportent `PREFIXE="$PREFIXE"` : le bloc patché calcule `rel="${CHEMIN#"$PREFIXE"/}"` et, sans cette variable, produit 8 `No such file` (27 PASS / 3 FAIL). C'est un défaut de harnais, pas du bloc ; le bloc d'origine ignore `PREFIXE` et n'est pas affecté.

```bash
#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
PASS=0
FAIL=0
pass() { PASS=$((PASS + 1)); echo "PASS $1"; }
fail() { FAIL=$((FAIL + 1)); echo "FAIL $1 exp=[$2] got=[$3]"; }
eq() {
  local name="$1" exp="$2" got="$3"
  if [ "$exp" = "$got" ]; then pass "$name"; else fail "$name" "$exp" "$got"; fi
}
contains() {
  local name="$1" needle="$2" hay="$3"
  case "$hay" in *"$needle"*) pass "$name" ;; *) fail "$name" "$needle" "<absent>" ;; esac
}
lacks() {
  local name="$1" needle="$2" hay="$3"
  case "$hay" in *"$needle"*) fail "$name" "$needle" "<present>" ;; *) pass "$name" ;; esac
}

SRC="$ROOT/src"
PREFIXE=".qoder/skills/demo"
SEED="$ROOT/seed"
REPO="$ROOT/repo"
DEPOT="$ROOT/depot"
ORIGIN="$ROOT/origin.git"

mkdir -p "$SRC/references" "$SRC/scripts"
printf 'demo skill\n' >"$SRC/SKILL.md"
printf 'ref\n' >"$SRC/references/r.md"
printf 'print(1)\n' >"$SRC/scripts/s.py"

git init -q -b main "$SEED"
git -C "$SEED" config user.name fixture
git -C "$SEED" config user.email fixture@example.invalid
git -C "$SEED" config core.autocrlf false
printf 'base\n' >"$SEED/README.md"
git -C "$SEED" add README.md
git -C "$SEED" commit -qm base
BASE_AVANT="$(git -C "$SEED" rev-parse HEAD)"
mkdir -p "$SEED/$PREFIXE"
cp "$SRC/SKILL.md" "$SEED/$PREFIXE/SKILL.md"
cp -R "$SRC/references" "$SEED/$PREFIXE/"
cp -R "$SRC/scripts" "$SEED/$PREFIXE/"
git -C "$SEED" add "$PREFIXE"
git -C "$SEED" commit -qm "add demo"
HEAD_PR="$(git -C "$SEED" rev-parse HEAD)"
git clone -q --bare "$SEED" "$ORIGIN"
git clone -q "$ORIGIN" "$REPO"
git clone -q "$ORIGIN" "$DEPOT"
git -C "$DEPOT" reset -q --hard "$BASE_AVANT"

RAW="$(git -C "$REPO" ls-tree -r HEAD -- "$PREFIXE/SKILL.md")"
TABS="$(printf '%s\n' "$RAW" | tr -cd '\t' | wc -c | tr -d ' ')"
eq raw_default_fields 2 "$((TABS + 1))"
OLD_LEN="$(printf '%s' "$(printf '%s\n' "$RAW" | cut -f3)" | wc -c | tr -d ' ')"
eq old_cut_f3_empty 0 "$OLD_LEN"
NEWOID="$(git -C "$REPO" ls-tree -r --format='%(objectname)' HEAD -- "$PREFIXE/SKILL.md")"
eq new_format_oid_len 40 "$(printf '%s' "$NEWOID" | wc -c | tr -d ' ')"

OUT3="$(TMP="$ROOT" PREFIXE="$PREFIXE" SOURCE="$SRC" bash "$ROOT/blocks/step3bis.sh" 2>&1)"
contains step3bis_blobs_ok BLOBS_OK "$OUT3"
eq step3bis_match_count 3 "$(printf '%s\n' "$OUT3" | grep -c '^BLOB_MATCH ')"
eq step3bis_mismatch_count 0 "$(printf '%s\n' "$OUT3" | grep -c '^BLOB_MISMATCH ')"
eq step3bis_oid_invalid_count 0 "$(printf '%s\n' "$OUT3" | grep -c '^OID_INVALID ')"

cp "$SRC/SKILL.md" "$ROOT/SKILL.bak"
printf 'drift\n' >>"$SRC/SKILL.md"
OUT3M="$(TMP="$ROOT" PREFIXE="$PREFIXE" SOURCE="$SRC" bash "$ROOT/blocks/step3bis.sh" 2>&1)"
contains step3bis_drift_fail "BLOBS_FAIL bad=1" "$OUT3M"
eq step3bis_drift_mismatch 1 "$(printf '%s\n' "$OUT3M" | grep -c '^BLOB_MISMATCH ')"
cp "$ROOT/SKILL.bak" "$SRC/SKILL.md"

mv "$SRC/references/r.md" "$ROOT/r.md.bak"
OUT3X="$(TMP="$ROOT" PREFIXE="$PREFIXE" SOURCE="$SRC" bash "$ROOT/blocks/step3bis.sh" 2>&1)"
contains step3bis_src_missing "SRC_MISSING references/r.md" "$OUT3X"
contains step3bis_src_missing_fail "BLOBS_FAIL bad=1" "$OUT3X"
mv "$ROOT/r.md.bak" "$SRC/references/r.md"

OID_MISS="$(git -C "$REPO" ls-tree -r --format='%(objectname)' HEAD -- "$PREFIXE/NOPE")"
eq guard_missing_file_count 0 "$(printf '%s\n' "$OID_MISS" | grep -c . || true)"
OID_DIR="$(git -C "$REPO" ls-tree -r --format='%(objectname)' HEAD -- "$PREFIXE")"
eq guard_directory_count 3 "$(printf '%s\n' "$OID_DIR" | grep -c . || true)"

OUT5="$(DEPOT="$DEPOT" PREFIXE="$PREFIXE" BASE_AVANT="$BASE_AVANT" HEAD_PR="$HEAD_PR" bash "$ROOT/blocks/step5.sh" 2>&1)"
contains step5_oid_count_3 "OID_COUNT=3" "$OUT5"
lacks step5_no_empty_list OID_LIST_EMPTY "$OUT5"
eq step5_hash_lines 3 "$(printf '%s\n' "$OUT5" | grep -cE '^[0-9a-f]{64} ')"
eq step5_ff_head "$HEAD_PR" "$(git -C "$DEPOT" rev-parse HEAD)"
eq step5_clean_worktree "" "$(git -C "$DEPOT" status --porcelain)"
eq step5_scope_diff_lines 3 "$(git -C "$DEPOT" diff --name-status "$BASE_AVANT"..origin/main | grep -c '^A')"
eq step5_headpr_diff_empty "" "$(git -C "$DEPOT" diff --name-status "$HEAD_PR" origin/main -- "$PREFIXE")"

OUT5N="$(DEPOT="$DEPOT" PREFIXE=".qoder/skills/nope" BASE_AVANT="$BASE_AVANT" HEAD_PR="$HEAD_PR" bash "$ROOT/blocks/step5.sh" 2>&1)"
contains step5_unknown_prefix_zero "OID_COUNT=0" "$OUT5N"
contains step5_unknown_prefix_empty OID_LIST_EMPTY "$OUT5N"

rm -f /tmp/publie
OUT6="$(DEPOT="$DEPOT" PREFIXE="$PREFIXE" CHEMIN="$PREFIXE/SKILL.md" SOURCE="$SRC" bash "$ROOT/blocks/step6.sh" 2>&1)"
contains step6_single_oid "OID_COUNT=1" "$OUT6"
eq step6_blob_file_match "$(sha256sum "$SRC/SKILL.md" | cut -d' ' -f1)" "$(sha256sum /tmp/publie | cut -d' ' -f1)"
eq step6_hash_lines 5 "$(printf '%s\n' "$OUT6" | grep -cE '^[0-9a-f]{64} ')"
eq step6_stat_lines 4 "$(printf '%s\n' "$OUT6" | grep -cE '^[0-9]{4}-[0-9]{2}-[0-9]{2} ')"
eq step6_path_errors 0 "$(printf '%s\n' "$OUT6" | grep -c 'No such file')"

rm -f /tmp/publie
OUT6M="$(DEPOT="$DEPOT" PREFIXE="$PREFIXE" CHEMIN="$PREFIXE/NOPE" SOURCE="$SRC" bash "$ROOT/blocks/step6.sh" 2>&1)"
contains step6_missing_invalid "OID_INVALID $PREFIXE/NOPE count=0" "$OUT6M"
if [ ! -e /tmp/publie ]; then pass step6_missing_no_blob; else fail step6_missing_no_blob; fi

OUT6D="$(DEPOT="$DEPOT" PREFIXE="$PREFIXE" CHEMIN="$PREFIXE" SOURCE="$SRC" bash "$ROOT/blocks/step6.sh" 2>&1)"
contains step6_directory_invalid "OID_INVALID $PREFIXE count=3" "$OUT6D"

rm -f /tmp/publie
echo "RESULT PASS=$PASS FAIL=$FAIL"
[ "$FAIL" -eq 0 ]
```

## 8. Portée et limites

- Vérifié : fixture locale, dépôt local, clones locaux, 29 puis 30 assertions, QA statique, absence de résidu, Skill installé inchangé.
- Non vérifié : un dépôt GitHub réel, un remote réseau, une concurrence réelle entre sessions, un push, l'application de la rustine au Skill installé.
- Le cas est épinglé à `SKILL.md` `2342cd45...` et au bloc `step6` `9dded8ef...`. Si l'un change, réextraire et redériver la rustine ; ne pas réutiliser les hashes ni le patch à l'aveugle.
- Le `RESULT PASS` de la QA (`skipped=16`) ne doit jamais être présenté comme une validation des blocs bash.
