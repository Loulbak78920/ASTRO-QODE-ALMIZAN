# Cas vérifié — run 40517379722, 2026-10-27

Source : session Qoder `55f63550-7c8d-4f9e-b0a9-e73686cc2765` (« Mettre à jour le site web »), tours du 2026-10-27 entre 14:00 et 14:14 UTC. Les valeurs ci-dessous proviennent des sorties d'outils de cette session, recoupées par des appels en lecture seule rejoués à ~15:18 UTC. Le dépôt est `Loulbak78920/ASTRO-QODE-ALMIZAN`.

## Contexte

Le workflow V5.1 a été poussé (`30062f8..8fdba83`), puis le runner épinglé (`8fdba83..21f0ba2`). Aucun des runs déclenchés n'a exécuté d'étape. La question posée était de confirmer le message d'erreur de facturation, le premier tour n'ayant produit qu'une inférence à partir du symptôme.

## Preuves du run 40517379722

| Observation | Valeur exacte |
|---|---|
| Run | `completed` / `failure`, créé `2026-10-27T14:02:27Z`, clos `14:07:23Z`, attempt 1 |
| Job / check-run | `122234451770` `test-and-verify`, `queued` puis `completed/failure`, `steps=0` |
| Logs anonymes | `/actions/jobs/122234451770/logs` → `403` « Must have admin rights to Repository. » |
| Logs authentifiés | `302` puis blob `404` `<Code>BlobNotFound</Code>` — aucun log n'a jamais été écrit |
| Page de job (React) à ~14:10Z | `annotation 0`, `not started 0`, `locked 0` |
| Annotations anonymes à ~14:10Z | HTTP `200`, tableau vide `[]` |
| Check-runs du commit `8fdba83` | 1 check-run, `output.annotations_count = 2` |
| Annotations authentifiées à ~14:10Z | 2 entrées, voir ci-dessous |
| Page legacy du job `122188150730` | la phrase de facturation est présente en HTML (recoupement) |
| `/users/.../settings/billing/actions` | `404` — inutilisable comme preuve |

Annotations lues (`annotations_url` du check-run) :

1. `failure` — `The job was not started because your account is locked due to a billing issue.`
2. `notice` — `"The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026. For more information, see https://github.com/actions/runner-images/issues/14748"`

Les deux annotations portent `path: .github`, `start_line: 1`, `end_line: 1` : le chemin n'est pas un fichier réel, ne pas l'utiliser pour localiser la cause.

## Propagation observée le même jour

| Heure UTC approx. | Check-run authentifié | Annotations anonymes | Page de job publique |
|---|---|---|---|
| 14:10 | `annotations_count = 2` | `[]` | message absent |
| 15:18 | 2 | 2 (`HTTP 200`) | message présent (`account is locked` ×1) |

Le même run, les mêmes annotations : seule la surface publique avait changé. Conséquence pour la procédure : ne pas traiter une réponse publique vide comme une preuve d'absence, et ne pas opposer « authentifié » à « anonyme » comme une règle fixe. La règle stable est de lire `output.annotations_count` puis les annotations, et de relire si le résultat est vide.

## Second run : détection du YAML réellement évalué

Run `40519167697` (sha `21f0ba2`, runner épinglé) : job `122241175505`, `steps=0`, absent de log, une seule annotation — la phrase de facturation. L'avis de migration Ubuntu 26, présent sur `8fdba83`, a disparu. C'est une corroboration que le workflow évalué est bien la version épinglée, mais elle reste secondaire : le contenu publié se prouve par le blob du commit.

## Tests du script de ce Skill

| Cas | Commande | Résultat |
|---|---|---|
| Run bloqué, jeton | `run --repo Loulbak78920/ASTRO-QODE-ALMIZAN --run-id 40517379722` | exit `0`, `ANNOTATIONS_COUNT 2`, `CAUSE_HINT billing_lock`, `LOGS_BLOB absent` |
| Run bloqué, anonyme | idem + `--anonymous` | exit `0`, `AUTH no`, `LOGS_BLOB forbidden-anonymous`, `ANNOTATIONS_COUNT 2` (état au 2026-10-27 ~15:18Z) |
| Run démarré | `run --repo actions/checkout --run-id 40332958637 --anonymous` | exit `1`, `STEPS 5`, `CLASS RUN_HAS_STEPS` |
| Dépôt invalide | `run --repo pasunrepo --run-id 1` | exit `2`, `ERROR REPO_INVALID` |
| Run inexistant | `run --repo Loulbak78920/ASTRO-QODE-ALMIZAN --run-id 1` | exit `2`, `ERROR FETCH run http 404 Not Found` |

La branche `NO_STEPS_CAUSE_UNPROVEN` (exit `1`) n'a pas pu être déclenchée sur données réelles : les runs disponibles avaient tous des annotations lisibles. Le code correspondant est couvert par lecture, pas par exécution.

## Limites et non-vérifié

- La régularisation de la facturation n'a pas été observée : on ne sait pas, dans ce cas, si un rerun démarre. Ne pas l'affirmer.
- Aucun rerun n'a été lancé : c'est une action partagée, elle exige une demande explicite.
- La visibilité des annotations anonymes a changé dans l'heure ; toute valeur « vide » ou « présente » doit être datée.
- Les droits exacts du jeton Git Credential Manager ne sont pas audités ; l'accès aux check-runs authentifiés a répondu `200`, rien de plus.
- Le run `40519167697` n'a pas été relu après `15:18Z` ; il n'est cité que pour la disparition de l'avis Ubuntu.
