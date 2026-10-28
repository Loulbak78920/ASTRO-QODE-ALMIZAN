---
name: diagnostiquer-run-github-actions-sans-logs
description: "Diagnostiquer un run GitHub Actions qui n'a jamais démarré et dont aucun log n'existe : constater le job resté queued à 0 étape et le run completed/failure, prouver l'absence de log (403 anonyme, puis 302 et BlobNotFound avec jeton) au lieu de la déduire d'une erreur HTTP, lire output.annotations_count sur le check-run du commit puis /check-runs/{id}/annotations pour obtenir le texte exact de la cause, tenir compte du retard de propagation des annotations sur les surfaces publiques, et conclure sans jamais annoncer une CI réparée. Pour « pourquoi ce run n'a pas démarré », run bloqué 0 étape, aucun log, account is locked due to a billing issue, check-run annotations, page de job React vide. 中文：GitHub Actions 运行从未启动、0 步骤、无日志、计费锁定、check-run 注释、注释延迟。English: Actions run never started, zero steps, no logs, billing lock, check-run annotations, late propagation."
---

# Diagnostiquer un run GitHub Actions sans logs

## Portée

Un run qui n'a exécuté aucune étape : job encore `queued`, ou run `completed/failure` en quelques secondes avec `steps: []`. Il n'existe alors aucun log à lire, et le message d'erreur ne se trouve que dans les annotations du check-run (ou dans l'état du compte).

Non couvert : publier ou réparer le workflow (`publier-workflow-ci-github`), un push refusé (`diagnostiquer-push-github-depot-absent`), et l'analyse d'un run qui a réellement démarré (lire ses étapes et ses logs).

## Règles non négociables

1. **Aucune cause nommée sans texte d'annotation lu.** Un job à 0 étape prouve qu'aucun runner n'a été attribué, pas la raison.
2. **Ne jamais écrire « CI verte » ou « CI réparée ».** Un blocage externe laisse la CI non exécutée ; seul un run avec au moins une étape exécutée peut être qualifié.
3. **Lire `output.annotations_count` avant les annotations.** Un `0` ou une liste vide n'autorise aucune conclusion : voir la propagation ci-dessous.
4. **Ne jamais afficher le jeton.** Lecture via `git credential fill`, jamais de `echo` du mot de passe.
5. **Lecture seule.** Pas de rerun, pas de push, pas de modification de workflow sans demande explicite de l'utilisateur.

## 1. Constater le symptôme

```bash
cd ~/.qoder/skills/diagnostiquer-run-github-actions-sans-logs
py -3 -B scripts/diagnostiquer_run.py run \
  --repo <owner>/<name> --run-id <run-id> \
  --out-dir "$HOME/.qoder/tmp/diag-<run-id>"
```

Sortie à interpréter (valeurs observées le 2026-10-27 sur le run 40517379722) :

```text
RUN 40517379722 ... 8fdba83 completed failure
JOB 122234451770 test-and-verify completed failure STEPS 0 STARTED ... COMPLETED ...
LOGS_HTTP 302 (token)
LOGS_BLOB_HTTP 404
LOGS_BLOB_CODE BlobNotFound
LOGS_BLOB absent
CHECK 122234451770 test-and-verify completed failure ANNOTATIONS_COUNT 2
ANNOTATION 1 failure The job was not started because your account is locked due to a billing issue.
CAUSE_HINT billing_lock
CLASS NO_STEPS_CAUSE_PROVEN
```

- `STEPS 0` sur chaque job : aucun runner n'a dispatché d'étape.
- Un run clos quelques secondes après sa création, avec un job `completed` sans étape, est le symptôme d'un blocage de planification, pas d'une erreur YAML.
- `--out-dir` conserve `run.json`, `jobs.json`, `checks.json`, `annotations.json` comme copies de preuve ; aucun jeton n'y est écrit.

## 2. Prouver l'absence de log

L'absence de log doit être établie, pas supposée :

| Observation | Sens | Piège |
|---|---|---|
| `LOGS_HTTP 403` sans jeton | Accès refusé, on ne sait rien du blob | Un 403 n'est pas une absence de log |
| `LOGS_HTTP 302` puis `LOGS_BLOB_HTTP 404` + `BlobNotFound` | Le blob n'existe pas : aucun log n'a été écrit | C'est la preuve ; un 404 sur le blob n'est pas une panne d'API |
| `LOGS_BLOB zip-present` | Des logs existent | Basculer sur la lecture des étapes, ne pas poursuivre ce diagnostic |

La redirection 302 pointe une URL de stockage signée et temporaire. Lire seulement les premiers octets : un vrai archive n'a pas à être téléchargé.

## 3. Lire la cause sur le check-run

Endpoints utilisés (tous en lecture) :

| But | Endpoint | Sans jeton | Avec jeton |
|---|---|---|---|
| Run | `/repos/{o}/{r}/actions/runs/{id}` | 200 si dépôt public | 200 |
| Jobs + étapes | `/repos/{o}/{r}/actions/runs/{id}/jobs` | 200 si public | 200 |
| Check-runs du commit | `/repos/{o}/{r}/commits/{sha}/check-runs` | 200 si public | 200 |
| Annotations | `/repos/{o}/{r}/check-runs/{check_id}/annotations` | variable | variable |
| Logs d'un job | `/repos/{o}/{r}/actions/jobs/{job_id}/logs` | 403 | 302 → blob |
| Facturation personnelle | `/users/{user}/settings/billing/actions` | 404 | 404 |

- Le check-run d'un job Actions porte le **même identifiant** que le job (observé : `122234451770`) ; en cas d'écart, faire correspondre sur le nom.
- La clé utile est `output.annotations_count` et son `annotations_url`, puis le tableau d'annotations : `annotation_level`, `message`.
- Ne pas scraper la page de job : l'interface est rendue côté client et son contenu varie dans le temps.
- L'endpoint de facturation personnelle renvoie 404 : il ne prouve rien et ne doit pas servir de preuve.

### Propagation des annotations

Les annotations ne sont pas visibles partout au même instant. Cas observé le 2026-10-27 :

| Heure UTC | Check-run authentifié | Annotations anonymes | Page de job publique |
|---|---|---|---|
| ~14:10 | `annotations_count = 2` | `[]` (HTTP 200) | 0 occurrence du message |
| ~15:18 | 2 | 2 | message présent |

Règle : une surface publique vide **n'est pas** une preuve d'absence d'annotation. Relire plus tard, et avec le jeton sur le check-run, avant de conclure. Le script émet `ANNOTATIONS_ANON_NOTE` quand les deux lectures divergent.

## 4. Qualifier le résultat

| `CLASS` | Code | Sens | Action |
|---|---|---|---|
| `NO_STEPS_CAUSE_PROVEN` | 0 | Texte d'annotation lu | Citer le message tel quel ; `CAUSE_HINT billing_lock` désigne un blocage de compte externe, ni le YAML ni le code ne sont en cause |
| `NO_STEPS_CAUSE_UNPROVEN` | 1 | Aucune étape, aucune annotation lisible | Relire le check-run plus tard et avec jeton ; ne nommer aucune cause |
| `RUN_HAS_STEPS` | 1 | Un runner a exécuté des étapes | Lire les étapes et logs ; ce n'est plus le cas d'usage de ce Skill |
| `API_ERROR` | 2 | Usage, dépôt, run ou API | Corriger l'appel ; ne rien conclure sur la CI |

Le champ `CAUSE_HINT` vaut `billing_lock` uniquement si le texte contient `account is locked due to a billing issue` ; `no-runner-reason` si le texte commence par « not started » sans cette phrase ; `other` sinon. Citer le message, jamais le seul indice.

## 5. Corrélation secondaire : le run évalue-t-il bien le YAML attendu ?

Le contenu exact publié se prouve par le blob du commit et son SHA-256 (`publier-workflow-ci-github`). Les annotations peuvent seulement corroborer, par différence d'ensemble :

- Run `8fdba83` (workflow avec `ubuntu-latest`) : 2 annotations, dont l'avis de migration vers Ubuntu 26.
- Run `21f0ba2` (runner épinglé `ubuntu-24.04`) : 1 seule annotation, l'avis a disparu.

Une annotation absente ne prouve rien si la propagation est en cours : traiter cette corrélation comme secondaire, jamais comme preuve principale du contenu.

## 6. Rapport

```text
RUN <id> <status>/<conclusion> sha=<7> <créé> → <maj>
JOB <id> steps=0 (aucun runner attribué)
LOGS absent (anonyme 403 ; jeton 302 → BlobNotFound)
ANNOTATIONS <n> (check-run déclare <n> ; anonyme <n>)
CAUSE PROUVÉE : <message exact, entre guillemets>
NON PROUVÉ : <ce qui reste hors de portée>
SUITE : après régularisation, relancer puis vérifier un run avec ≥ 1 étape exécutée
```

À éviter : « la CI est réparée », « le workflow fonctionne », « il suffit de » sans preuve. Un run non démarré ne valide aucun contenu de workflow.

## Pièges Windows

- `python` peut être l'alias Microsoft Store ; utiliser `py -3`.
- `--out-dir "$HOME/.qoder/tmp/..."` : un chemin `/c/...` (MSYS) n'est pas lisible par `py -3` et produit `FileNotFoundError`. Pour relire une copie, convertir avec `cygpath -w`, sa préférence d'exécution restant `py -3 -B`.
- La console cp1252 affiche les accents en `\xb0` ou `?` dans la sortie du script : c'est un échappement ASCII volontaire, pas une corruption du fichier.
- `urllib` suit les redirections par défaut : pour distinguer 403, 302 et 404, elle doit être désactivée sur l'appel de logs.
- L'URL signée du blob expire et n'accepte pas le jeton de l'API : ne pas la conserver comme preuve permanente.

## Ressources

- `scripts/diagnostiquer_run.py` — diagnostic lecture seule : état du run et des jobs, disponibilité du blob de log, check-run, annotations, classification. Codes 0/1/2 ; options `--repo`, `--run-id`, `--anonymous`, `--out-dir`.
- `references/cas-verifie-2026-10-27.md` — preuves du cas réel, valeurs exactes, propagation observée et limites non vérifiées.
