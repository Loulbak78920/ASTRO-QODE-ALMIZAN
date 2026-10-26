---
name: verifier-fixture-autocrlf-non-vacue
description: "Vérifier qu'un garde dépendant des fins de ligne (autocrlf, name:, DIFF_SKILL, SOURCE_DIRTY) est réellement exercé dans une fixture Git jetable sous Windows/Git Bash : hériter core.autocrlf=true via GIT_CONFIG_COUNT/KEY_0/VALUE_0, produire le CRLF par rm puis git checkout -- . (pas de réécriture brute : cache stat périmé), exécuter le bloc verbatim avec ses prérequis, ordonner rc → état atteint → artefacts → absence de signature d'erreur → absence du symptôme, exiger un contrôle négatif, et distinguer « garde présent » de « garde porteur » (MSYS sed retire déjà le CR ; bytes.strip() avale \\r ; seul lstrip le préserve). Utiliser quand une fixture Windows passe alors qu'un prérequis manque (comm: ... No such file avec rc=0), quand status affiche M mais git diff --quiet vaut 0, quand un A/B rend des valeurs identiques, ou avant de déclarer un garde CRLF vérifié. 中文触发：Windows 夹具、autocrlf、CRLF、行尾守卫、非空洞断言、stat 缓存、git checkout、comm 缺文件、strip 吞 CR、DIFF_SKILL、SOURCE_DIRTY。"
---

# Vérifier un garde CRLF dans une fixture fidèle

## Objectif

Une fixture Windows peut afficher `RESULT PASS` sans jamais exercer le chemin CRLF, et une assertion d'absence (« pas de `DIFF_SKILL` ») peut réussir parce que le bloc s'est arrêté trop tôt. Ce Skill fixe les conditions de fidélité (`core.autocrlf=true` réel, checkout réel) et l'ordre des assertions qui empêche un PASS vide. Il prouve un comportement local ; il ne prouve ni un dépôt de production, ni le réseau, ni un autre interpréteur que celui testé.

## Quand l'utiliser

- Un `SKILL.md` contient un garde lié aux fins de ligne : `tr -d '\r'`, `core.autocrlf`, extraction de `name:`, `DIFF_SKILL`, `SOURCE_DIRTY`.
- Une fixture passe, mais le chemin CRLF n'est peut-être pas atteint.
- `git status` affiche ` M` alors que `git diff --quiet` rend 0.
- `comm: ... No such file or directory` apparaît alors que le bloc rend 0.
- Il faut distinguer « le garde est présent dans le code » de « retirer le garde change le résultat ».
- Avant de déclarer vérifié un garde CRLF ou une branche `DIFF_SKILL`.

Ne pas utiliser pour : extraire et exécuter des blocs bash génériques (voir `verify-skill-command-blocks-fixture`), rejouer un fixture déjà documenté (voir `replay-skill-reference-fixtures`), valider un harnais comme porte d'acceptation (voir `valider-harnais-fixture-windows-msys`), verrouiller LF dans un dépôt (voir `lock-lf-endings-skill-repo`), ou tester une PR réelle.

## Règles non négociables

1. **Skill installé en lecture seule.** Toutes les écritures vont sous `$HOME/.qoder/tmp/fixture-autocrlf-<unique>/`. Ne pas modifier, committer ni pousser le Skill pendant la vérification.
2. **`autocrlf` explicite.** Exporter `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=core.autocrlf`, `GIT_CONFIG_VALUE_0=true`. Ne pas dépendre du réglage de l'hôte et ne jamais modifier les configurations globale ou système.
3. **CRLF par checkout réel.** Supprimer les fichiers suivis puis `git checkout -- .`. Ne jamais fabriquer le CRLF par réécriture d'octets : le cache stat devient périmé et `git status` signale ` M` alors que le contenu est identique.
4. **Bloc entier, verbatim.** Exécuter la totalité du bloc délimité, prérequis compris (`src.rel`, `main.rel`, `head.oids`…). Ne pas découper un sous-intervalle : c'est ainsi qu'un `comm` échoue sans faire échouer le script.
5. **Ordre d'assertion fixe** : code de retour → jeton d'état atteint → artefacts attendus → absence de signature d'erreur → absence du symptôme. Les assertions 3 à 5 sont vides si le bloc s'arrête avant l'état terminal.
6. **Positif et négatif obligatoires.** Cas nominal (`ARCHIVE_UPDATE`, rc=0) et contrôle négatif (`DIFF_SKILL`, rc=2) sur le même bloc, sans rustine.
7. **Présent n'est pas porteur.** Un garde est « porteur » seulement si l'enlever change le résultat sur une entrée qui préserve le CR. Nommer l'extracteur concerné ; ne pas généraliser à `sed` MSYS.
8. **Octets, pas `strip()`.** Pour prouver un CR final, utiliser `lstrip`/`rstrip`. `bytes.strip()` et `bytes.decode().strip()` suppriment `\r` et créent un faux négatif. Ne pas utiliser `grep -c $'\r'` sous Git Bash.
9. **Vocabulaire honnête.** `vérifié`, `vide`, `non exercé`, `bloqué` sont des résultats distincts. Un `RESULT PASS` de fixture ne prouve pas la production.
10. **Nettoyage attribué.** Supprimer uniquement le répertoire temporaire créé par cette vérification. Pas de commit, pas de push.

## Étape 0 — Préflight reproductible

Lancer le harnais fourni, qui ne touche à aucun Skill :

```bash
bash "$HOME/.qoder/skills/verifier-fixture-autocrlf-non-vacue/scripts/check_fixture_autocrlf.sh"
```

Attendu sur cette machine (git 2.52.0.windows.1, `core.autocrlf=true` en portée système) :

```text
CHECK env_override=PASS
CHECK checkout_eol_i_lf_w_crlf=PASS
CHECK raw_rewrite_status_M=PASS
CHECK raw_rewrite_diff_quiet_0=PASS
CHECK msys_sed_strips_cr=PASS
CHECK py_lstrip_preserves_cr=PASS
CHECK py_strip_eats_cr=PASS
SUMMARY PASS=12 FAIL=0 SKIP=0
RESULT PASS
```

Consigner aussi les portées de configuration, sans les modifier :

```bash
git --version
git config --get core.autocrlf || echo UNSET
git config --global --get core.autocrlf || echo UNSET
git config --system --get core.autocrlf || echo UNSET
py -3 --version
```

Si le harnais rend `RESULT FAIL`, l'environnement a dérivé (version de Git, portée de configuration, shell). Ne pas convertir cet échec en conclusion sur le garde : corriger la cause ou déclarer la vérification bloquée.

## Étape 1 — Fixture fidèle

Le dépôt de base doit être un vrai checkout CRLF ; la source doit rester en LF (c'est elle qui simule les fichiers écrits par un outil).

```bash
ROOT="$(mktemp -d "$HOME/.qoder/tmp/autocrlf-XXXXXX")" || exit 1
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.autocrlf GIT_CONFIG_VALUE_0=true
export GIT_AUTHOR_NAME=fixture GIT_AUTHOR_EMAIL=fixture@example.invalid
export GIT_COMMITTER_NAME=fixture GIT_COMMITTER_EMAIL=fixture@example.invalid
NOM=demo; PREFIXE=".qoder/skills/$NOM"; TMP="$ROOT/work"; SOURCE="$ROOT/source"
mkdir -p "$ROOT/seed/$PREFIXE/references" "$ROOT/seed/$PREFIXE/scripts" \
         "$SOURCE/references" "$SOURCE/scripts" "$TMP"

printf -- '---\nname: demo\ndescription: "x"\n---\n# demo\n' >"$SOURCE/SKILL.md"
printf 'a\n' >"$SOURCE/references/a.md"
printf 'x = 1\n' >"$SOURCE/scripts/x.py"
cp "$SOURCE/SKILL.md" "$ROOT/seed/$PREFIXE/SKILL.md"
cp -R "$SOURCE/references/." "$ROOT/seed/$PREFIXE/references/"
cp -R "$SOURCE/scripts/." "$ROOT/seed/$PREFIXE/scripts/"

git -C "$ROOT/seed" init -q -b main
git -C "$ROOT/seed" add -A
git -C "$ROOT/seed" commit -qm seed
git clone -q --bare "$ROOT/seed" "$ROOT/origin.git"
git clone -q "$ROOT/origin.git" "$TMP/repo"

git -C "$SOURCE" init -q -b main
git -C "$SOURCE" add -A
git -C "$SOURCE" commit -qm src

git -C "$TMP/repo" ls-files --eol -- "$PREFIXE/SKILL.md"
git -C "$TMP/repo" status --porcelain
git -C "$SOURCE" status --porcelain -- SKILL.md references scripts
```

Attendu : `i/lf    w/crlf  attr/   <prefixe>/SKILL.md`, puis deux sorties vides. Un ` M` ici signifie que le CRLF n'a pas été produit par Git : recommencer, ne pas corriger par `git add`.

Pour forcer un checkout neuf après une mutation, supprimer puis restaurer :

```bash
rm "$TMP/repo/$PREFIXE/SKILL.md"
git -C "$TMP/repo" checkout -- .
git -C "$TMP/repo" status --porcelain
```

## Étape 2 — Extraire et exécuter le bloc verbatim

Extraire le bloc entier par ses lignes de début et de fin, puis enregistrer son empreinte :

```bash
SKILL_MD="$HOME/.qoder/skills/<skill-name>/SKILL.md"
BLOCK="$ROOT/block.sh"
# Adapter start/end au bloc réel ; inclure toutes les lignes de prérequis.
PYTHONIOENCODING=utf-8 py -3 - "$SKILL_MD" "$BLOCK" <<'PY'
import hashlib, pathlib, sys
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
start = next(i for i, l in enumerate(src) if l.startswith("PREFIXE="))
mid   = next(i for i, l in enumerate(src) if l.startswith("MAIN_FILES="))
end   = next(i for i in range(mid + 1, len(src)) if src[i] == "fi")
block = "\n".join(src[start:end + 1]) + "\n"
pathlib.Path(sys.argv[2]).write_text(block, encoding="utf-8", newline="\n")
print("BLOCK_LINES=%d" % (end - start + 1))
print("BLOCK_SHA256=%s" % hashlib.sha256(block.encode()).hexdigest())
PY
```

Exécuter avec toutes les variables déclarées, en séparant stdout, stderr et code :

```bash
OUT="$(TMP="$TMP" SOURCE="$SOURCE" NOM="$NOM" bash "$BLOCK" 2>"$ROOT/block.err")"; RC=$?
```

Affecter `RC` immédiatement. Un pipe après l'appel remplacerait le code du bloc.

Si le bloc déclare un prérequis créé par une étape antérieure du `SKILL.md`, reproduire cette étape documentée ; ne pas inventer de valeur et ne pas retirer la ligne du bloc. Le prérequis manquant typique est `src.rel` : sans lui, `comm` échoue mais le script continue.

## Étape 3 — Assertions ordonnées

```bash
eq() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1 exp=[$2] got=[$3]"; fi; }
contains() { case "$3" in *"$2"*) echo "PASS $1" ;; *) echo "FAIL $1 absent [$2]" ;; esac; }
lacks() { case "$3" in *"$2"*) echo "FAIL $1 present [$2]" ;; *) echo "PASS $1" ;; esac; }
ERR="$(cat "$ROOT/block.err")"
eq        rc             "$RC" 0
contains  terminal       "$OUT" ARCHIVE_UPDATE
test -f   "$TMP/src.rel" && echo "PASS artifact src.rel"
lacks     stderr_comm    "$ERR" "comm:"
lacks     stderr_missing "$ERR" "No such file"
lacks     no_diff_skill  "$OUT" DIFF_SKILL
```

Ne pas inverser cet ordre. Dans le cas réel du 2026-10-26, un bloc réduit à 19 lignes (début `MAIN_FILES=`) a rendu `comm: .../src.rel: No such file`, `POS_RC=0`, `ARCHIVE_UPDATE` et aucune ligne `DIFF_SKILL` : les assertions `rc`, `terminal` et `no_diff_skill` passaient toutes. Seul le contrôle de `stderr` révélait le prérequis manquant. Le bloc complet de 36 lignes (début `PREFIXE=`) a rendu `ASSERT_POS_NO_COMM_ERR=OK`.

Contrôler aussi les artefacts attendus du bloc : `head.oids`, `main.rel`, `main.only`, `source.status`, `src.rel`. Un artefact absent rend l'assertion suivante vide.

## Étape 4 — Contrôle négatif

Sur le même bloc, sans rustine, rendre le `name` de la base différent de celui de la source :

```bash
sed -i 's/^name: demo$/name: other/' "$TMP/repo/$PREFIXE/SKILL.md"
git -C "$TMP/repo" add "$PREFIXE/SKILL.md"
git -C "$TMP/repo" commit -qm other
OUT_NEG="$(TMP="$TMP" SOURCE="$SOURCE" NOM="$NOM" bash "$BLOCK" 2>"$ROOT/neg.err")"; RC_NEG=$?
contains neg_terminal "$OUT_NEG" DIFF_SKILL
eq       neg_rc       "$RC_NEG" 2
```

Exiger le jeton **et** le code 2. Un jeton sans code, ou l'inverse, indique un `exit` mal placé.

## Étape 5 — « Présent » contre « porteur »

Le garde `tr -d '\r'` peut être présent et inutile pour l'extracteur utilisé. Sous Git Bash, `sed` retire déjà le CR : une démonstration A/B fondée sur `sed` est vide.

| Extracteur | CR final préservé | A/B valide |
|---|---|---|
| `sed -n 's/^name:[[:space:]]*//p'` (MSYS) | non, longueur 4 | non : les deux variantes rendent `demo` |
| Python binaire, `lstrip(b' ')` | oui, `b'demo\r'`, longueur 5 | oui |
| Python binaire, `strip()` | non, longueur 4 | non : faux négatif |

Preuve au niveau octet sur le checkout CRLF :

```bash
cd "$TMP/repo/$PREFIXE"
PYTHONIOENCODING=utf-8 py -3 -c '
b = open("SKILL.md", "rb").read().split(b"\n")[1].split(b":", 1)[1]
v = b.lstrip(b" ")
print("lstrip len=%d eq_demo=%s" % (len(v), v == b"demo"))
print("strip  len=%d eq_demo=%s" % (len(v.strip()), v.strip() == b"demo"))
g = v.decode().replace(chr(13), "")
print("guarded len=%d eq_demo=%s" % (len(g), g == "demo"))
'
```

Attendu : `lstrip len=5 eq_demo=False`, `strip len=4 eq_demo=True`, `guarded len=4 eq_demo=True`. Puis faire l'A/B : copier l'extraction dans deux variantes, retirer le garde de la seconde, et exiger que l'entrée préserve le CR (longueur 5) avant de conclure. Si l'entrée rend 4, marquer `vide` et ne pas conclure sur la nécessité du garde.

Formuler le résultat ainsi : « garde présent » (le code le contient), « porteur pour un extracteur qui préserve le CR » (A/B concluant), « non exercé sous `sed` MSYS » (A/B vide). Ne pas écrire « garde validé » sans préciser la classe d'extracteur.

## Étape 6 — Rapport et nettoyage

Classer chaque branche dans une seule catégorie : `vérifié` (exécuté, assertions ordonnées), `vide` (exécuté mais l'entrée ne distingue pas), `non exercé` (chemin jamais atteint), `bloqué` (environnement). Joindre : version de Git, portée de `core.autocrlf`, `BLOCK_LINES`, `BLOCK_SHA256`, `RC`, jetons, artefacts, signatures `stderr`.

Nettoyer uniquement le répertoire créé, puis vérifier l'absence de résidu :

```bash
rm -rf "$ROOT"
ls -d "$HOME/.qoder/tmp"/fixture-autocrlf-* 2>/dev/null | head
```

Enfin, valider statiquement le paquet du Skill modifié, sans modifier ses fichiers :

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "$HOME/.qoder/skills/<skill-name>"
```

Un `RESULT PASS` statique ne dit rien des blocs bash (`skipped=N`) : il ne remplace pas les étapes 2 à 5.

## Table des symptômes

| Symptôme | Cause | Action |
|---|---|---|
| `SOURCE_DIRTY  M ...` dans la variante CRLF | CRLF fabriqué par réécriture d'octets : cache stat périmé | Reconstruire le CRLF par `rm` + `git checkout -- .`, garder `SOURCE` en LF |
| `status` = ` M f.txt` mais `git diff --quiet` = 0 | Fichier réécrit hors Git ; l'index n'a pas été rafraîchi | Ne pas conclure à une dérive ; `git add` nettoie, mais la fixture doit éviter cet état |
| `update-index --refresh` rend 1, `needs update`, statut toujours ` M` | Même cache périmé | Ne pas utiliser `status` comme preuve de dérive après une réécriture brute |
| `comm: ... No such file or directory` avec `rc=0` | Bloc découpé : `src.rel` (ou un autre prérequis) n'a jamais été créé | Exécuter le bloc entier ; asserter l'absence de `comm:` sur `stderr` |
| Toutes les assertions passent, aucun artefact produit | Arrêt précoce : les assertions d'absence sont vides | Ajouter les artefacts et les signatures d'erreur avant l'absence du symptôme |
| `raw_len=4`, `STRIPPED_MATCH` | `sed` MSYS retire déjà le CR | A/B vide ; passer à une extraction binaire |
| `b'demo'` avec `strip()` | `strip()` supprime `\r` | Utiliser `lstrip(b' ')` ou `rstrip(b'\n')` puis contrôler le CR |
| Checkout en LF malgré `autocrlf=true` | Variable non exportée, ou configuration neutralisée dans la fixture | Exporter les trois variables `GIT_CONFIG_*` et recréer la fixture |
| `i/crlf` dans l'index | `autocrlf` absent au moment du `git add` | Recréer le dépôt avec l'environnement exporté ; ne pas corriger par `checkout` |
| `python` ouvre le Microsoft Store, code 49 | Alias Windows | Utiliser `py -3` |
| `UnicodeEncodeError: cp1252` | Sortie Python non ASCII sur console Windows | `PYTHONIOENCODING=utf-8`, sortie ASCII pour le harnais |
| QA `PASS` avec `skipped=N` | La QA statique ignore les blocs bash | Exécuter les étapes 2 à 5 ; voir `verify-skill-command-blocks-fixture` |
| `CLEANED=1` alors que le répertoire de fixture survit | `shutil.rmtree(ignore_errors=True)` échoue sans le dire sur des objets Git en lecture seule (`WinError 5`) | Rendre le nettoyage vérifiable : `chmod` puis réessai, sinon `RESIDUE`, `CLEANED=0`, code 1 |

## Ressources

- `scripts/check_fixture_autocrlf.sh` — préflight reproductible : héritage `autocrlf`, checkout CRLF propre, cache stat périmé, comportement de `sed` et de `lstrip`/`strip`. Sortie ASCII, `RESULT PASS/FAIL`, nettoie son propre répertoire.
- `scripts/crlf_guard_probe.py` — sonde déterministe (stdlib, ASCII) : isole `HOME` et la configuration globale, exporte `autocrlf`, commit LF puis `rm` + `git checkout -- .`, et émet `RAW_*`/`GUARDED_*` avec `RESULT PASS|FAIL|ERROR` et codes 0/1/2. Fixture sous `~/.qoder/tmp/fixture-autocrlf-probe-*` ; un nettoyage qui échoue (objets Git en lecture seule) émet `RESIDUE`, `CLEANED=0` et `REASON=CLEANUP_FAILED` avec code 1, plutôt que de prétendre avoir nettoyé ; `--keep` émet `KEPT` et `CLEANED=0`. Couverte par mutation (sans garde → FAIL 1 ; sans `autocrlf` → FAIL 1 ; sans `chmod` de nettoyage → `RESIDUE` + FAIL 1) ; elle ne remplace pas les étapes 2 à 5.
- `references/evidence-2026-10-26.md` — chaîne des sessions, correspondance des enregistrements, sorties brutes reproduites le 2026-10-26, et limites explicites.

## Skills liés

- `verify-skill-command-blocks-fixture` — extraction par ancre et exécution générique des blocs ; neutralise le CRLF, donc ne couvre pas cet axe.
- `valider-harnais-fixture-windows-msys` — porte d'acceptation d'un harnais (double exécution, contrôle négatif, résidus).
- `replay-skill-reference-fixtures` — rejeu de fixtures documentés.
- `lock-lf-endings-skill-repo` — verrouillage LF et preuve octet par octet de l'absence de CR.
- `skill-update-concurrency-safe` — stabilité et écritures concurrentes du paquet Skill.
- `skill-file-qa` — validation statique du `SKILL.md`.
