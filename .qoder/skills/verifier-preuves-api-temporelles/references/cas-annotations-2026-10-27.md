# Cas vérifié — annotations GitHub, 2026-10-27

Sources : session source `55f63550-7c8d-4f9e-b0a9-e73686cc2765` (« Mettre à jour le site web ») et session de build `25295b18-37c8-499a-ab8d-af0543cefc86` (« 创建 GitHub Actions 诊断技能 »). Les instants sont en UTC, lus dans les horodatages des messages et des sorties d'outils. Les snapshots `read_chat_session` ont été recoupés avec les JSONL du projet, puis les appariements `tool_use` / `tool_result` ont été vérifiés avant citation. Dépôt concerné : `Loulbak78920/ASTRO-QODE-ALMIZAN`.

## Contexte

Le workflow V5.1 a été poussé (`30062f8..8fdba83`). Le run `40517379722` est resté sans étape : créé `2026-10-27T14:02:27Z`, clos `14:07:23Z`, job/check-run `122234451770`, `steps=0`. La question était de savoir pourquoi aucun runner n'avait démarré et de citer le message exact, sans se contenter d'une inférence.

## Observations

| Instant UTC | Session | Surface et mode d'auth | Requête | Réponse observée |
|---|---|---|---|---|
| 14:10:22.191Z | source | API annotations, anonyme | `GET /repos/.../check-runs/122234451770/annotations` | `HTTP 200`, corps `[\n\n]`, `len=0` |
| 14:10:36.406Z (analysé 14:11:09.949Z) | source | page HTML du job `122234451770` | `GET https://github.com/.../actions/runs/40517379722/job/122234451770` | `HTTP 200`, 195 312 octets ; `annotation 0`, `not started 0`, `locked 0` |
| 14:10:51.416Z | source | logs du job, jeton | `GET /repos/.../actions/jobs/122234451770/logs` | `302` puis blob `404`, `<Code>BlobNotFound</Code>` |
| 14:11:02.387Z | source | page HTML du job legacy `122188150730` | `GET https://github.com/.../actions/runs/40503886141/job/122188150730` | `HTTP 200` ; phrase « account is locked due to a billing issue » présente |
| 14:11:16.029Z | source | API check-runs du commit, jeton | `GET /repos/.../commits/8fdba83.../check-runs` | `HTTP 200` ; 1 check-run ; `output.annotations_count = 2` |
| 14:11:21.217Z | source | API annotations, jeton | `GET /repos/.../check-runs/122234451770/annotations` | `HTTP 200` ; `COUNT 2` (facturation + avis Ubuntu 26) |
| 14:17:56.304Z | build | API annotations, anonyme (script) | même endpoint | `ANNOTATIONS_ANON_HTTP 200`, `ANNOTATIONS_ANON_COUNT 2` |
| 14:17:56.304Z | build | API annotations, jeton (script) | même endpoint | `ANNOTATIONS_COUNT 2`, `CLASS NO_STEPS_CAUSE_PROVEN`, exit `0` |
| 14:18:15.090Z | build | API annotations, anonyme (curl indépendant) | même endpoint | `HTTP=200`, `BYTES=787` |
| 14:18:15.090Z | build | page HTML du job `122234451770` | même URL de job | `HTTP=200`, `BYTES=196726` ; `account is locked :: 1`, `not started :: 1`, `billing issue :: 1` |
| 14:18:30.774Z | build | relecture des deux JSON sauvegardés | fichiers locaux | `COUNT 2`, `ANNOT_COUNT 2` |
| 14:18:37.897Z | build | test négatif `--anonymous` | script du Skill voisin | `AUTH no`, `ANNOTATIONS_COUNT 2`, `EXIT=0` |
| 14:18:50.352Z | build | run avec étapes, anonyme | `actions/checkout` run `40332958637` | `STEPS 5`, `EXIT=1` |
| 14:23:18.057Z | build | rejeu de la commande documentée | script du Skill voisin | exit `0`, `ANNOTATIONS_ANON_COUNT 2`, `ANNOTATIONS_COUNT 2` |

## Retard observé

- Annotations anonymes : `[]` à `14:10:22Z`, `2` à `14:17:56Z` → **7 min 34 s**.
- Page du même job : 0 occurrence à `14:10:36Z`, 1 occurrence à `14:18:15Z` → environ **7 min 39 s**.
- Aucune borne supérieure n'est prouvée : une seule fenêtre a été observée, sur un seul dépôt. Le Skill ne doit pas annoncer une durée générale.

## Rejeu de validation (14:29–14:30Z)

Rejeu effectué en lecture seule après la rédaction du Skill :

| Instant UTC | Surface | Résultat |
|---|---|---|
| `14:29:21Z` | API annotations, anonyme | `HTTP 200`, 921 octets, `COUNT 2`, niveaux `failure` et `notice` ; SHA-256 du corps `f335d0ee…` |
| `14:30:03Z` | API annotations, jeton | `HTTP 200`, 921 octets, `COUNT 2`, même SHA-256 `f335d0ee…` que la lecture anonyme |
| `14:29:27Z` | page du job `122234451770` | `HTTP 200`, 196 752 octets ; `account is locked :: 1`, `not started :: 1`, `billing issue :: 1` |
| `14:29:27Z` | horloge du poste | `UTC=14:29:27Z`, `LOCAL=15:29:28+0100` |

Verdict : `IDENTIQUE` avec les observations de `14:17:56Z` (API) et `14:18:15Z` (page). Écarts : 684,7 s pour l'API, 665,9 s pour la page. Les lectures anonyme et authentifiée, séparées de 42 s, ont rendu le même digest : à cet instant, l'auth n'ajoutait rien. Cela ne prouve pas que l'auth n'a jamais d'effet, seulement qu'elle n'en avait pas à `14:29–14:30Z`. L'ensemble prouve l'absence de changement sur environ 11 min, pas une stabilité permanente.

## Le confond temporel à ne pas répéter

Le `annotations_count = 2` authentifié a été lu à `14:11:16Z`, soit **53,8 s après** le `[]` anonyme de `14:10:22Z`. Ces deux lectures ne sont pas simultanées. On ne peut donc pas conclure que l'écart provenait du mode d'authentification : il peut être entièrement temporel. La re-sonde anonyme à `14:17:56Z` a tranché en faveur de la propagation.

La donnée de recommandation reçue pour cette tâche indiquait « 14:10Z » puis « 15:18Z ». La seconde valeur est une heure **locale** (`UTC+1`) : `15:18` local = `14:18Z`. L'observation de la page à `14:18:15Z` est réelle ; seule l'étiquette de fuseau était fausse.

## Test négatif invalidé

Le plan de build prévoyait : `--anonymous` → `NO_STEPS_CAUSE_UNPROVEN`, exit `1`. La prémisse était l'observation `[]` de la session source. Au build, la même surface renvoyait 2 annotations ; le test a rendu exit `0` et `CLASS NO_STEPS_CAUSE_PROVEN`. Le test est `INVALIDE`, pas « réussi autrement ».

| Test | Prémisse | Résultat au build | Statut | Remplacement |
|---|---|---|---|---|
| `--anonymous` → exit 1 | annotations anonymes vides | exit 0, cause prouvée | `INVALIDE` | conserver comme test positif du comportement observé |
| dépôt invalide → exit 2 | aucune | `ERROR REPO_INVALID`, exit 2 | `EXECUTE` | conserver |
| run inexistant → exit 2 | aucune | `FETCH run http 404`, exit 2 | `EXECUTE` | conserver |
| run démarré → exit 1 | aucune | `STEPS 5`, `RUN_HAS_STEPS`, exit 1 | `EXECUTE` | nommer la branche |

## Registre des branches

```text
BRANCHE NO_STEPS_CAUSE_PROVEN      exit 0  EXECUTE        (14:17:56Z, 14:23:18Z)
BRANCHE RUN_HAS_STEPS              exit 1  EXECUTE        (14:18:50Z, actions/checkout 40332958637)
BRANCHE API_ERROR                  exit 2  EXECUTE        (14:18:37Z, dépôt invalide et run 404)
BRANCHE NO_STEPS_CAUSE_UNPROVEN    exit 1  NON_DECLENCHE  (lecture du code seulement)
```

Le code de sortie `1` a bien été exercé, mais par `RUN_HAS_STEPS`. La branche `NO_STEPS_CAUSE_UNPROVEN` n'a jamais été déclenchée sur données réelles. Un rapport qui dit seulement « tests 0/1/2 verts » laisse croire le contraire.

## Correction utilisateur et rejeu

À `14:23:12.836Z`, l'utilisateur a demandé : « run the documented command again ». Le rejeu à `14:23:18.057Z` a rendu exit `0`, `ANNOTATIONS_ANON_COUNT 2`, `ANNOTATIONS_COUNT 2`, `CLASS NO_STEPS_CAUSE_PROVEN`. Les empreintes du paquet voisin sont restées `c91ddabb…dd5ea` (`SKILL.md`) et `18bd03c2…f7746` (`scripts/diagnostiquer_run.py`) à `14:23:26.612Z` : le rejeu n'a pas modifié le Skill. Seules les copies de preuve de `~/.qoder/tmp/diag-40517379722/` ont été réécrites.

## Contre-exemple de datation

Le Skill voisin `diagnostiquer-run-github-actions-sans-logs` présente, dans `SKILL.md` et dans sa référence, une ligne `~15:18` sous l'en-tête « Heure UTC ». La session montre que `15:18` est l'heure locale du poste (`UTC+1`), soit `14:18Z`. L'observation de la page est confirmée à `14:18:15Z` ; c'est l'étiquette qui est fausse. Ce paquet n'est pas modifié dans cette tâche : la leçon est reprise ici comme règle de datation.

## Non vérifié

- Aucun rerun n'a été lancé ; la régularisation de la facturation n'a pas été observée.
- La raison interne du retard (propagation GitHub, cache, autre) n'est pas prouvée ; seule la variation horodatée est constatée.
- Aucune borne générale du retard : un seul cas, un seul dépôt.
- Les droits exacts du jeton Git Credential Manager ne sont pas audités ; l'accès aux check-runs a répondu `200`, rien de plus.
- La page a été relue à `14:29:27Z` (identique) ; aucune observation au-delà de cette fenêtre.
- La page du job `122234451770` était vide à `14:10:36Z`, mais la page du job legacy `122188150730` contenait déjà la phrase : ne pas généraliser d'un job à l'autre.
- Le `annotations_count = 2` authentifié et le `[]` anonyme sont séparés de 53,8 s : l'effet propre de l'authentification n'est pas isolé.

## Commandes de reproduction (lecture seule)

Sonde anonyme, horodatage UTC avant et après :

```bash
URL="https://api.github.com/repos/<owner>/<repo>/check-runs/<check_id>/annotations"
OUT="$HOME/.qoder/tmp/sonde-$(date -u +%Y%m%dT%H%M%SZ).json"
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl -sS --max-redirs 0 -D "$OUT.headers" -o "$OUT" \
  -w 'HTTP=%{http_code} BYTES=%{size_download}\n' \
  -H 'Accept: application/vnd.github+json' "$URL"
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "T0=$T0 T1=$T1"
py -3 -B -c "import json,hashlib,sys; b=open(sys.argv[1],'rb').read(); d=json.loads(b); print('SHA256',hashlib.sha256(b).hexdigest()); print('TYPE',type(d).__name__); print('COUNT',len(d) if isinstance(d,(list,dict)) else 'n/a')" "$(cygpath -w "$OUT")"
```

Sonde authentifiée, sans afficher le jeton :

```bash
TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill 2>/dev/null | sed -n 's/^password=//p')
curl -sS --max-redirs 0 -H "Authorization: Bearer $TOKEN" -H 'Accept: application/vnd.github+json' "$URL"
```

Le jeton n'est jamais écrit dans `$OUT`, dans un en-tête sauvegardé ou dans le rapport.
