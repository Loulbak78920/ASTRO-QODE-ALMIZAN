---
name: verify-skill-command-blocks-fixture
description: "Rejouer les blocs bash d'un SKILL.md dans une fixture Git jetable avant de les livrer : extraire chaque bloc verbatim par ancre unique, vérifier son SHA-256, construire un dépôt main + origin/main avec une source indépendante, exécuter les chemins succès et échec (source absente, dérive, préfixe inconnu, chemin ambigu), puis tester une rustine candidate en A/B dans la fixture sans modifier le Skill installé. Utiliser quand skill-file-qa affiche Code blocks … skipped=N, quand un snippet a produit fatal: Not a valid object name ou le SHA-256 de flux vide e3b0c442…, quand un bloc n'a été testé qu'à la racine du dépôt, ou avant de modifier un Skill dont les blocs bash portent des invariants de comptage, de chemin ou de ref. 中文触发：验证 SKILL.md 代码块、逐字提取、围栏块、夹具 A/B、candidate patch、skipped=、空 OID、路径拼接、origin/main、负向路径。"
---

# Vérifier les blocs bash d'un SKILL.md dans une fixture

## Objectif

`skill-file-qa` analyse Python et JavaScript, puis affiche `Code blocks: ... skipped=N` : un `RESULT PASS` ne dit rien des blocs bash. Ce Skill exécute chaque bloc **verbatim** dans une fixture Git jetable, vérifie les chemins nominaux et les chemins d'échec, puis teste une rustine candidate en A/B. La fixture prouve un comportement local ; elle ne prouve ni un dépôt réel, ni le réseau, ni une concurrence réelle.

## Quand l'utiliser

- Après avoir modifié des blocs bash d'un `SKILL.md`, avant livraison.
- Quand la QA affiche `skipped=N` ou quand un bloc n'a jamais été exécuté.
- Quand un snippet a produit `fatal: Not a valid object name`, un OID vide ou `e3b0c442…` (SHA-256 du flux vide).
- Quand un bloc passe à la racine du dépôt mais doit fonctionner sous un préfixe imbriqué.
- Avant d'appliquer une correction à un bloc qui manipule des comptages, des refs ou des chemins.

Ne pas utiliser pour : rejouer un fixture documenté dans `references/` (voir `replay-skill-reference-fixtures`), valider un harnais comme porte d'acceptation (voir `valider-harnais-fixture-windows-msys`), comparer des jetons documentés à la sortie d'un script (voir `verifier-parite-doc-script-skill`), ou tester un dépôt réel / le réseau.

## Règles non négociables

1. **Skill installé en lecture seule.** Toutes les écritures vont sous `$HOME/.qoder/tmp/skill-blocks-<unique>/`. Ne pas modifier, committer ou pousser le Skill pendant la vérification.
2. **Extraction par ancre unique.** Chaque bloc est identifié par une sous-chaîne qui n'apparaît que dans un bloc. Exiger exactement 1 correspondance ; enregistrer le SHA-256 du `SKILL.md`, le nombre de lignes et le SHA-256 du bloc.
3. **Premier passage verbatim.** Exécuter le bloc tel qu'extrait, sans le corriger. Un échec doit être observé avant toute rustine.
4. **Fixture `main` + `origin/main`.** Vérifier `git rev-parse --verify origin/main` avant d'exécuter un bloc qui utilise cette ref. Un seed sur `master` ne produit pas `origin/main`.
5. **Source indépendante du dépôt.** `SOURCE` est l'arborescence source du Skill (par exemple `$ROOT/src`), pas la racine du dépôt. Utiliser un préfixe imbriqué (`.qoder/skills/demo`) : un bloc qui passe à la racine peut échouer sous préfixe.
6. **Codes de sortie sans pipeline.** Lancer le bloc, affecter `RC=$?` immédiatement, puis filtrer. Ne jamais lire `$?` après un `grep`, `tee` ou `cat`.
7. **Au moins un chemin négatif par bloc.** Un passage nominal seul est incomplet. Couvrir, selon le bloc : source absente, dérive, préfixe inconnu, chemin absent, chemin ambigu (répertoire), OID vide.
8. **Rustine candidate uniquement dans la fixture.** Compter les remplacements, préserver les invariants (garde d'OID, tokens), comparer non patché vs patché. Si la rustine passe, le défaut est dans le bloc ; ne pas modifier le Skill installé sans instruction explicite.
9. **Nettoyage attribué.** Supprimer uniquement la racine créée par cette exécution et `/tmp/publie`. Vérifier `$HOME/.qoder/tmp` pour le préfixe ; ne jamais supprimer le dossier d'une autre session.
10. **Rapport honnête.** Séparer QA statique et exécution des blocs. Ne pas recycler un ancien PASS. Distinguer « re-vérifié », « observé dans la source » et « non exécuté ».

## Étape 0 — Préflight

```bash
TARGET="$HOME/.qoder/skills/<skill-name>"
SKILL_MD="$TARGET/SKILL.md"
sha256sum "$SKILL_MD"
grep -c '^```bash' "$SKILL_MD" || true
find "$TARGET" \( -name __pycache__ -o -name '*.pyc' \) -print
```

Enregistrer la QA de référence, notamment `Code blocks: ... skipped=N` :

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$TARGET" \
  --workspace "$PWD" --stable-seconds 2 --stability-timeout 30
```

Exiger `RESULT PASS` et noter `Files (N)`. La QA ne lit ni n'exécute les blocs bash : `skipped=N` est la raison d'être de ce Skill.

## Étape 1 — Extraire les blocs

Créer la racine jetable et choisir une ancre par bloc. L'ancre est une ligne finale distinctive, pas un mot présent dans plusieurs blocs.

```bash
ROOT="$(mktemp -d "$HOME/.qoder/tmp/skill-blocks-XXXXXX")"
mkdir -p "$ROOT/blocks" "$ROOT/src/references" "$ROOT/src/scripts"
py -3 "$HOME/.qoder/skills/verify-skill-command-blocks-fixture/scripts/extract_bash_blocks.py" \
  "$SKILL_MD" --out-dir "$ROOT/blocks" \
  --anchor 'step3bis=echo BLOBS_OK || echo "BLOBS_FAIL bad=$bad"' \
  --anchor 'step5=echo OID_LIST_EMPTY' \
  --anchor 'step6=cat-file blob "$oid" > /tmp/publie' \
  | tee "$ROOT/extract.out"
```

Attendu :

```text
BLOCK_COUNT=<n>
SKILL_SHA256=<hash>
EXTRACT_OK step3bis lines=28 sha256=...
EXTRACT_OK step5 lines=17 sha256=...
EXTRACT_OK step6 lines=12 sha256=...
EXTRACT_RESULT=PASS
```

Exiger `EXTRACT_RESULT=PASS` et exactement un `EXTRACT_OK` par ancre. Si `EXTRACT_FAIL name matches=N` avec `N` différent de 1, choisir une ancre plus longue ; ne pas éditer le fichier extrait. L'extraction lit en mode texte (fins de ligne normalisées) et écrit LF ; le hash couvre le bloc plus un saut de ligne final.

## Étape 2 — Construire la fixture

```bash
SRC="$ROOT/src"; PREFIXE=".qoder/skills/demo"
SEED="$ROOT/seed"; REPO="$ROOT/repo"; DEPOT="$ROOT/depot"; ORIGIN="$ROOT/origin.git"
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
git -C "$REPO" rev-parse --verify origin/main
```

Pourquoi cette forme :

- `-b main` évite le cas observé d'un seed sur `master` sans `origin/main` ;
- `seed` contient un commit de base puis un commit avec le préfixe ;
- `repo` représente l'état après PR ; `depot` est remis au commit de base pour que l'étape de fusion ait un fast-forward à faire ;
- `SOURCE=$SRC` est une arborescence source indépendante. La remplacer par `$REPO` masque les défauts de composition de chemins : le cas source a passé 20/20 avec `SOURCE="$REPO"`, puis échoué 2 fois sur 29 avec `SOURCE="$ROOT/src"`.

## Étape 3 — Exécuter les blocs non patchés

Helpers minimaux :

```bash
PASS=0; FAIL=0
pass() { PASS=$((PASS + 1)); echo "PASS $1"; }
fail() { FAIL=$((FAIL + 1)); echo "FAIL $1 exp=[$2] got=[$3]"; }
eq() { if [ "$2" = "$3" ]; then pass "$1"; else fail "$1" "$2" "$3"; fi; }
contains() { case "$3" in *"$2"*) pass "$1" ;; *) fail "$1" "$2" "<absent>" ;; esac; }
lacks() { case "$3" in *"$2"*) fail "$1" "$2" "<présent>" ;; *) pass "$1" ;; esac; }
```

Exécuter un bloc en capturant sortie et code :

```bash
OUT3="$(TMP="$ROOT" PREFIXE="$PREFIXE" SOURCE="$SRC" bash "$ROOT/blocks/step3bis.sh" 2>&1)"; RC3=$?
```

Affecter `RC3` immédiatement. Un pipe après l'appel remplacerait le code du bloc par celui du filtre.

Assertions minimales, à adapter aux tokens du bloc :

- **Champs bruts** : la sortie par défaut de `ls-tree` contient `<mode> <type> <oid>\t<path>` (2 champs tabulés) ; `cut -f3` sur cette sortie est vide ; `--format='%(objectname)'` rend 40 caractères ; `cat-file blob ""` rend `fatal: Not a valid object name` et le SHA-256 du flux vide `e3b0c442…`.
- **Nominal** : jeton de succès attendu, nombre de `BLOB_MATCH`, `OID_COUNT`, lignes de hash, aucun `BLOB_MISMATCH` ni `OID_INVALID`, code de sortie attendu.
- **Négatifs** : dérive de la source → `BLOB_MISMATCH` + `BLOBS_FAIL` ; source absente → `SRC_MISSING` ; préfixe inconnu → `OID_COUNT=0` + `OID_LIST_EMPTY` ; chemin absent → `OID_INVALID count=0` ; chemin répertoire → `OID_INVALID count>1` ; aucun blob écrit quand l'OID est invalide.
- **Effets de bord** : supprimer `/tmp/publie` avant et après ; vérifier que la source et la copie de travail n'ont pas changé.

Exemple de garde sur une liste vide :

```bash
OID_MISS="$(git -C "$REPO" ls-tree -r --format='%(objectname)' HEAD -- "$PREFIXE/NOPE")"
eq guard_missing_file_count 0 "$(printf '%s\n' "$OID_MISS" | grep -c . || true)"
OID_DIR="$(git -C "$REPO" ls-tree -r --format='%(objectname)' HEAD -- "$PREFIXE")"
eq guard_directory_count 3 "$(printf '%s\n' "$OID_DIR" | grep -c . || true)"
```

`BLOBS_OK` peut être un faux vert si la liste de fichiers est vide : toujours asserter le nombre attendu de fichiers en plus du jeton.

Premier passage : exécuter le bloc extrait **sans rustine**. Si les échecs viennent de la fixture (mauvaise branche, `origin/main` absent, variable mal nommée), corriger la fixture et relancer. Si le bloc contredit son invariant documenté, classer le défaut comme défaut de bloc.

## Étape 4 — Classer l'échec

| Symptôme | Cause | Action |
|---|---|---|
| `EXTRACT_FAIL name matches=0` ou `2` | ancre absente ou non unique | allonger l'ancre ; ne pas éditer le bloc |
| `origin/main` absent | seed créé sur `master` ou clone sans branche | `git init -b main` / `git branch -M main`, puis revérifier `origin/main` |
| `fatal: Not a valid object name` + `e3b0c442…` | `ls-tree` filtré par `cut -f3` : le champ 3 n'existe pas dans la sortie par défaut | utiliser `--format='%(objectname)'` et exiger un OID non vide avant `cat-file` |
| `sha256sum: ... No such file` dans un bloc de vérification | `CHEMIN` relatif au dépôt concaténé à `$SOURCE` qui est une source indépendante | calculer `rel="${CHEMIN#"$PREFIXE"/}"` et utiliser `$SOURCE/$rel` ; ne pas confondre avec la garde d'OID |
| `No such file` ×N sur le bloc candidat, bloc d'origine échouant autrement | variable helper (`$PREFIXE`) non exportée à l'invocation du bloc | ajouter `PREFIXE="$PREFIXE"` dans l'environnement de l'appel ; défaut de harnais, pas de bloc |
| `BLOBS_OK` avec zéro `BLOB_MATCH` | liste vide ; le jeton est vacuously true | asserter le nombre de fichiers attendu |
| Passe à la racine, échoue sous `.qoder/skills/demo` | composition de chemins non testée | conserver le préfixe imbriqué ; ne pas aplatir la fixture |
| `No such file` seulement aux échantillons 2/3 | dérive concurrente de la source | arrêter, rapporter ; ne pas figer un état instable |
| QA `PASS` mais bloc rouge | la QA ignore les blocs bash (`skipped=N`) | exécuter ce Skill ; le PASS statique ne couvre pas l'exécution |
| `M` ou bruit CRLF dans le dépôt | `core.autocrlf` du poste | comparer les blobs, pas la copie de travail ; `core.autocrlf false` dans la fixture |
| `/tmp/publie` reste après le test | effet de bord global codé dans le bloc | supprimer avant/après ; ne pas le laisser |
| `python` rend 49 ou ouvre le Store | alias Microsoft Store | utiliser `py -3` |

## Étape 5 — A/B de la rustine candidate

Copier le bloc et appliquer une modification minimale **dans la fixture** :

```bash
cp "$ROOT/blocks/step6.sh" "$ROOT/blocks/step6_candidate.sh"
py -3 - "$ROOT/blocks/step6.sh" "$ROOT/blocks/step6_candidate.sh" <<'PY'
import pathlib, sys
src, dst = map(pathlib.Path, sys.argv[1:3])
body = src.read_text(encoding="utf-8")
before = body.count('"$SOURCE/$CHEMIN"')
patched = body.replace(
    '  oid="$oids"\n',
    '  oid="$oids"\n  rel="${CHEMIN#"$PREFIXE"/}"\n',
).replace('"$SOURCE/$CHEMIN"', '"$SOURCE/$rel"')
assert before == 4, before
assert patched.count('"$SOURCE/$CHEMIN"') == 0
assert 'rel="${CHEMIN#"$PREFIXE"/}"' in patched
assert 'OID_INVALID $CHEMIN count=$n' in patched
dst.write_text(patched, encoding="utf-8", newline="\n")
print(f"PATCH_APPLIED replacements={before}")
PY
sha256sum "$ROOT/blocks/step6.sh" "$ROOT/blocks/step6_candidate.sh"
```

Exécuter le candidat seul, puis le copier sur le bloc d'origine (`cp "$ROOT/blocks/step6_candidate.sh" "$ROOT/blocks/step6.sh"`) et lancer le harnais complet. Sans cette copie, le harnais rejoue le bloc d'origine. Attendu dans le cas source :

```text
non patché : 27 PASS / 2 FAIL
FAIL step6_hash_lines exp=[5] got=[1]
FAIL step6_stat_lines exp=[4] got=[0]
candidat   : 5 lignes de hash, 4 lignes de stat, 0 erreur de chemin
patché     : 30 PASS / 0 FAIL
```

Règles :

- Compter les remplacements et asserter les invariants (garde d'OID conservée, aucun `$SOURCE/$CHEMIN` restant) avant d'exécuter.
- Exporter dans l'environnement du bloc toutes les variables qu'il lit (`PREFIXE`, `TMP`, `SOURCE`), même si le bloc d'origine n'en avait pas besoin : un `No such file` en série sur le candidat est d'abord un défaut de harnais.
- La rustine n'est valide que pour le hash de bloc enregistré. Si le bloc change, réextraire et redériver la rustine.
- Ne pas appliquer la rustine au Skill installé dans cette étape. Vérifier `sha256sum "$SKILL_MD"` et `git -C "$TARGET" status --porcelain` avant/après : ils doivent être identiques.
- Si le candidat passe et le bloc d'origine échoue, le défaut est dans le bloc, pas dans la fixture. Le rapport doit le dire, sans prétendre que le Skill est corrigé.

## Étape 6 — QA, nettoyage, rapport

QA statique du Skill cible :

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "$TARGET" \
  --workspace "$PWD" --stable-seconds 2 --stability-timeout 30
```

Exiger `RESULT PASS`, `Files (N)` exact, et noter `Code blocks: python=... js=... skipped=N`. La QA ne remplace pas l'exécution des blocs.

Nettoyage :

```bash
chmod -R u+w "$ROOT" 2>/dev/null; rm -rf "$ROOT"; rm -f /tmp/publie
test ! -e "$ROOT" && echo NO_FIXTURE_LEFT
test ! -e /tmp/publie && echo NO_PUBLIE
sha256sum "$SKILL_MD"
find "$TARGET" \( -name __pycache__ -o -name '*.pyc' \) -print
```

Ne supprimer que `$ROOT` de cette exécution. Si `$HOME/.qoder/tmp` contient un autre dossier du même préfixe, l'attribuer avant toute suppression ; ne pas toucher au dossier d'une autre session.

Rapport :

```text
Skill        : <chemin> | SKILL.md sha256 <hash>
Blocs        : extraits <n>/<N> | ancres <...> | hashes <...>
Fixture      : <root> | origin/main <sha> | base <sha> | head <sha>
Exécution    : <n> PASS / <n> FAIL | <bloc> EXIT <n>
Négatifs     : source absente <...> | dérive <...> | préfixe inconnu <...> | chemin ambigu <...>
A/B          : original <hash> -> candidat <hash> | non patché <n>/<N> | patché <n>/<N>
Skill modifié: non | sha256 avant/après <...>
QA statique  : RESULT PASS | skipped=<n> (ne couvre pas les blocs bash)
Nettoyage    : <root> supprimé | /tmp/publie absent | résidus <...>
Portée       : fixture locale ; dépôt réel, réseau, concurrence non testés
```

## Checklist de livraison

- [ ] QA de référence exécutée ; `skipped=N` enregistré.
- [ ] Chaque bloc extrait par ancre unique (exactement 1 correspondance), avec lignes et SHA-256.
- [ ] Fixture avec `main` et `origin/main` vérifiés ; source indépendante et préfixe imbriqué.
- [ ] Bloc non patché exécuté verbatim ; chemins nominal et négatif couverts.
- [ ] Échecs classés (bloc / fixture / environnement) avant toute correction.
- [ ] Rustine candidate testée uniquement dans la fixture ; compteurs et invariants assertés.
- [ ] Skill installé inchangé (`sha256sum`, `git status`) ; aucun commit ni push.
- [ ] QA statique `RESULT PASS` avec `skipped=N`, rapportée séparément.
- [ ] Fixture et `/tmp/publie` supprimés ; aucun `__pycache__`.
- [ ] Rapport distinguant re-vérifié, observé et non exécuté.

## Ressources

- `scripts/extract_bash_blocks.py` : extraction par ancre unique, contrôle des correspondances, SHA-256 et nombres de lignes.
- `references/cas-github-pr-2026-10-26.md` : cas vérifié 20/20 (faux vert), 27/29, candidat, 30/30, QA `skipped=16`, Skill installé non modifié.

## Skills liés

- `skill-file-qa` : validation statique et manifeste `Files (N)` ; ne lit pas les blocs bash.
- `replay-skill-reference-fixtures` : rejouer des fixtures documentés dans `references/`.
- `valider-harnais-fixture-windows-msys` : porte d'acceptation d'un harnais déjà écrit.
- `verifier-parite-doc-script-skill` : parité entre jetons documentés et sortie de script.
- `github-pr-create-merge-sans-gh` : Skill cible du cas de référence.
- `skill-update-concurrency-safe` : écriture concurrente et double échantillonnage.
- `probe-cli-args-beyond-msys-rewrite` : argv réécrit par MSYS.
