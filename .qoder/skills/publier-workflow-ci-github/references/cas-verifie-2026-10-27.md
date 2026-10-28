# Cas vérifié — publication du workflow V5.1 (2026-10-27)

Source : session `55f63550-7c8d-4f9e-b0a9-e73686cc2765`, tours « Pousse le workflow V5.1 sur GitHub » puis « regarder les logs du run 40517379722 », « prépare le changement pour épingler ubuntu-24.04 », « pousse le changement sur main » et « vérifie le résultat du run 40519167697 ». Les faits ci-dessous viennent des sorties d'outils de la session.

## Résultat

| Élément | Valeur |
|---|---|
| Dépôt / branche | `Loulbak78920/ASTRO-QODE-ALMIZAN`, `main` |
| Avant / après | `30062f8` → `8fdba83` (fast-forward, sans force) |
| Commit | `8fdba83` — `ci: publier le workflow V5.1 (garde-fous et suites conditionnelles)` |
| Fichier | `.github/workflows/ci_astro_qode.yml` uniquement, 32 insertions / 7 suppressions |
| Octets locaux | 1703, SHA-256 `56d2c2318e71205241dfe0c899b83e7508be334cf7259735ce9d00b45d100aae` |
| Octets distants | identiques (raw.githubusercontent, même SHA-256) |
| Run | `40517379722`, job `122234451770`, 0 étape exécutée |
| Verdict CI | **non verte** : aucun runner n'a démarré |

## Déroulé reproductible

1. **Préflight.** Fichier local : 1703 octets, SHA-256 `56d2c231…d100aae`. `git ls-remote` : `main = 30062f8`, `master = fe57c7c`, plus des branches `skill/*`, `merge/*` et des refs `pull/*`. `main` est la cible ; `master` existe mais n'est pas la branche publiée.
2. **Clone isolé.** `git clone --depth 1 --branch main` dans `~/.qoder/tmp/push-v5-1-workflow`, avec `GIT_TERMINAL_PROMPT=0`. `HEAD = 30062f8`. Le clone contient un seul workflow, V5.0, 870 octets.
3. **Contenu public.** 391 fichiers suivis. `tests/` contient `__init__.py` et `test_suite_complete.py` ; `tests/test_contrat_intelligent_v2.py` et `tests/test_comptes_http_mizan.py` sont **ABSENT**.
4. **Copie minimale.** Un seul fichier modifié (`M .github/workflows/ci_astro_qode.yml`), diff 32/7. `.gitattributes` : `* text=auto eol=lf`. Le workflow est UTF-8, sans BOM.
5. **Structure YAML.** Nom V5.1, déclencheurs `push`, `pull_request`, `workflow_dispatch`, 9 étapes, `permissions: {contents: read}`, `timeout-minutes: 20`, deux étapes gardées par `hashFiles`. PyYAML lit la clé `on:` comme le booléen `True` : le script de contrôle doit tester `d.get("on")` **et** `d.get(True)`.
6. **Préflight local des étapes non gardées**, dans le clone :
   - `python astro_qode_cli.py test` → 11 tests, `OK`, RC=0 (12,861 s)
   - `python astro_qode_cli.py unisson` → RC=0
   - `python astro_qode_cli.py qasm BELL` → RC=0
   - `python astro_qode_cli.py seal --verify` → RC=0
7. **Effets de bord.** Après ces exécutions, `git status` listait cinq fichiers suivis modifiés : `memoire_aq/dashboard_astro_qode.html`, `index_sceaux_astro_qode.json`, `sceau_bloc_synchron_mzn_v6.json`, `sceau_matrice_unisson_or_argent_v5.json`, `sceau_suite_logique_v4.json`. Leur diff (5721 octets) a été sauvegardé hors du clone, puis `git checkout -- memoire_aq` les a restaurés. Seul le workflow a été indexé (`git diff --cached --stat` : 1 fichier).
8. **Commit et push.** `git push origin main` → `30062f8..8fdba83  main -> main`, `PUSH_RC=0`.
9. **Preuve distante.** `git ls-remote … refs/heads/main` → `8fdba837224200b2ba5cc117e36e8cd85c1de670`. Téléchargement du fichier brut : SHA-256 `56d2c231…d100aae`, identique au local ; `grep -c 'V5.1'` = 1.
10. **Sondage du run.** À 14:02:27Z, run `40517379722` `queued`, job `122234451770` `queued`, 0 étape. Le message exact de facturation n'est pas accessible anonymement ; il est lu en authentifié (voir Limites).

## Corrections de parcours

### C1 — L'exécution locale réécrit des fichiers suivis

Les commandes CI exécutées dans le clone ont modifié des artefacts versionnés (`memoire_aq/`). Sans `git status` après le préflight, ces modifications seraient parties dans le commit. Règle retenue : exécuter les étapes **avant** le commit, puis relire `git status`, sauvegarder le diff des chemins réécrits, `git checkout --` ces chemins, et n'indexer que le chemin explicite du workflow.

### C2 — `/tmp` du shell n'est pas lisible par `py -3`

`curl -o /tmp/run40517379722.html` a réussi, puis `py -3` a échoué :

```
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/run40517379722.html'
```

Git Bash résout `/tmp` vers son propre répertoire temporaire ; Python Windows interprète `/tmp/...` comme `\tmp\...` sur le lecteur courant. Correctif appliqué : écrire dans `C:/Users/<user>/.qoder/tmp/ci-run-40517379722/` (chemin visible des deux côtés) ou convertir avec `cygpath -w`.

### C3 — Un run `queued` à 0 étape ne prouve ni un YAML valide ni un YAML invalide

Le run est resté `queued` plusieurs minutes, puis est passé à `completed/failure` à 14:07:23Z. À 14:10Z, l'API montrait le run `completed/failure` et le job encore `queued`, 0 étape. À 15:13 local (+01:00), le job était `completed/failure`, toujours 0 étape. Aucune étape n'a jamais été exécutée : la panne est au niveau de la planification, pas du contenu du workflow. La conclusion « CI réparée » est interdite tant qu'aucune étape n'a démarré.

## Limites observées

- **Message de facturation : lisible seulement en authentifié.** En anonyme, `/actions/runs/40517379722/logs` renvoie HTTP 403 (« Must have admin rights to Repository. »), les annotations publiques sont `[]` (HTTP 200) et la page du run est rendue en JavaScript : un `grep` sur 196 384 octets de HTML n'a trouvé que des drapeaux de fonctionnalités. Avec le jeton du gestionnaire d'identifiants, `GET /repos/.../commits/8fdba83/check-runs` puis `GET /repos/.../check-runs/122234451770/annotations` renvoient 2 annotations : `failure` « The job was not started because your account is locked due to a billing issue. » et `notice` « The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026. » (actions/runner-images#14748). C'est une preuve directe ; sans cette lecture, l'attribution reste une inférence.
- **Aucune CI verte observée** sur ce dépôt à cette date.

## Seconde publication — épinglage du runner (`21f0ba2`)

Après le premier push, le fichier du workspace a été modifié : 1782 octets, SHA-256 `b8135c5a750b22651582a7721dccb15b6a28823ef35d5e4af9cd05337216d6bf`, `runs-on: ubuntu-24.04` plus une ligne de commentaire. Ce n'était pas une simple dérive : le changement a été préparé puis poussé le même jour, sur demande explicite.

| Élément | Valeur |
|---|---|
| Avant / après | `8fdba83` → `21f0ba2`, fast-forward, sans force |
| Commit | `ci: épingler le runner sur ubuntu-24.04` |
| Diff | 1 fichier, 2 insertions / 1 suppression |
| YAML | 9 étapes, 3 déclencheurs, `contents: read`, `timeout-minutes: 20` |
| Octets | 1782, SHA-256 `b8135c5a…d6bf`, identiques au blob du commit |
| Run | `40519167697`, job `122241175505`, `completed/failure` en 5 s (14:14:08Z → 14:14:13Z), 0 étape |

Piège rencontré : juste après le push, `raw.githubusercontent.com` servait encore l'ancien blob (`56d2c231…`, cache CDN). La preuve correcte est le blob **au commit** via l'API, ou `git show HEAD:…` dans le clone — jamais le fichier vivant du workspace, qui peut différer sans que le push soit en cause.

Signal utile : l'annotation `notice` sur la migration `ubuntu-latest` a disparu du run `40519167697` (il ne reste que le message de facturation), ce qui prouve que GitHub a bien évalué `runs-on: ubuntu-24.04`. Le verrou de facturation, lui, est inchangé : le job échoue en 5 s avec 0 étape.

## Rejeu des contrôles avec le script du Skill (2026-10-27, 15:13 local, +01:00)

```text
refs  --repo Loulbak78920/ASTRO-QODE-ALMIZAN --branch main
OID 8fdba837224200b2ba5cc117e36e8cd85c1de670

guards --dir <clone> --workflow .github/workflows/ci_astro_qode.yml
GUARD 51 tests/test_contrat_intelligent_v2.py ABSENT
GUARD 55 tests/test_comptes_http_mizan.py ABSENT

raw --repo … --path .github/workflows/ci_astro_qode.yml --local <copie du clone>
REMOTE_SHA256 56d2c2318e71205241dfe0c899b83e7508be334cf7259735ce9d00b45d100aae
LOCAL_SHA256  56d2c2318e71205241dfe0c899b83e7508be334cf7259735ce9d00b45d100aae
RESULT MATCH

run --repo Loulbak78920/ASTRO-QODE-ALMIZAN --run-id 40517379722
RUN 40517379722 … 8fdba83 completed failure
JOB 122234451770 test-and-verify completed failure STEPS 0
CLASS COMPLETED_NO_STEPS
```

Contrôles négatifs exécutés : `raw` contre un autre fichier local → `RESULT MISMATCH`, RC=1 ; `refs` sur une branche inexistante → `MISSING_BRANCH`, RC=1.

### Rejeu après la seconde publication (2026-10-27, 15:18 local, +01:00)

```text
refs --repo Loulbak78920/ASTRO-QODE-ALMIZAN --branch main
OID 21f0ba2047e3298a6a162afbfe07cb08f27d103c
REF refs/heads/main

run --repo Loulbak78920/ASTRO-QODE-ALMIZAN --run-id 40519167697
RUN 40519167697 … 21f0ba2 completed failure
CREATED 2026-10-27T14:14:08Z   UPDATED 2026-10-27T14:14:13Z
JOB 122241175505 test-and-verify completed failure STEPS 0
CLASS COMPLETED_NO_STEPS
```

Les deux commandes sont sorties en RC=0. L'OID de `main` a donc changé de `8fdba83` à `21f0ba2` entre les deux rejeux : comparer un OID mémorisé sans le redater produit un faux écart.
