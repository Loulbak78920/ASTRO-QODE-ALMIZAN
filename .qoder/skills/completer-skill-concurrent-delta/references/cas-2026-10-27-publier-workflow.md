# Cas vérifié — 2026-10-27, `publier-workflow-ci-github`

Source : session `76bfddcf-c4ca-438f-ada7-3ff29f2a81f4` (23 tours humains).
Écrivain concurrent : session `b0d9ac95`, auteur du package `publier-workflow-ci-github`.
Package étendu : `C:\Users\Administrateur\.qoder\skills\publier-workflow-ci-github`.

Les heures de messages sont en UTC ; les heures de shell sont locales (`+01:00`) et converties ici.

## 1. Chronologie

| Heure (UTC) | Événement | Preuve |
|---|---|---|
| 14:10:05 | dernier `read_chat_session` de l'écrivain, `turnLimit: 20` | JSONL `b0d9ac95` |
| avant 14:11:33 | lecture authentifiée des annotations du job `122234451770` | sortie d'outil, synthèse à 14:11:33 |
| 14:11:32 | l'écrivain conclut à partir de 20 messages humains | JSONL `b0d9ac95` |
| 14:12:07 | tour humain 21 (décision sur la portée) | JSONL `76bfddcf` |
| 14:12:51 | écriture du script par l'écrivain | JSONL `b0d9ac95` |
| 14:13:47 | tour humain 22 | JSONL `76bfddcf` |
| 14:14:03 | écriture de la référence par l'écrivain | JSONL `b0d9ac95` |
| 14:14:05 | push `8fdba83..21f0ba2`, fast-forward | sortie git |
| 14:14:08 | run `40519167697` créé | API Actions |
| 14:14:13 | run clos `completed/failure`, 0 étape | API Actions |
| 14:14:26 | écriture de `SKILL.md` par l'écrivain | JSONL `b0d9ac95` |
| 14:14:39 | tour humain 23 | JSONL `76bfddcf` |
| 14:15:41 | dernier `Edit` de l'écrivain, sans relecture | JSONL `b0d9ac95` |

Conclusion : l'écrivain a écrit entre 14:12:51 et 14:15:41 sur la base d'une lecture de 14:10:05. Les tours 21 à 23 sont arrivés pendant cette fenêtre. La cause est un **instantané périmé**, pas une fenêtre tronquée au sens de la recommandation.

## 2. Registre d'écarts

| # | Affirmation du package | Provenance | Statut | Tour | Correction |
|---|---|---|---|---|---|
| 1 | « Message de facturation non lu dans ce run » ; les annotations publiques sont `[]` | `REPORTED` | `CONTRADICTED` | 20 | lecture authentifiée : 2 annotations, dont « The job was not started because your account is locked due to a billing issue. » |
| 2 | « Dérive post-publication » du fichier local, remote resté à 1703 octets / `56d2c231…` | `UNVERIFIED` | `CONTRADICTED` | 21–22 | seconde publication demandée, `8fdba83..21f0ba2`, épinglage `ubuntu-24.04`, blob distant `b8135c5a…` / 1782 octets |
| 3 | Avertissement `ubuntu-latest` → Ubuntu 26 | `CONFIRMED_BY_TOOL` | `SUPPORTED` | 20 | conservé, puis preuve que l'annotation disparaît au run suivant |
| 4 | Absence de CI verte | `CONFIRMED_BY_TOOL` | `SUPPORTED` | 20–23 | conservé après la seconde publication |

Aucune ligne `ABSENT` : l'utilisateur a choisi d'étendre le package existant, pas d'ajouter des sections.

## 3. Preuves des deux corrections

### 3.1 Annotations de facturation (remplace « non lu »)

```text
ANNOT HTTP=200 BYTES=421
COUNT 1
--- 1 failure
The job was not started because your account is locked due to a billing issue.
```

Sur le premier run, deux annotations avaient été lues :

```text
--- 1 failure
The job was not started because your account is locked due to a billing issue.
--- 2 notice
The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026.
```

Elles ne sont lisibles qu'avec le jeton du gestionnaire d'identifiants : en anonyme, `/annotations` renvoie `[]` et `/logs` renvoie HTTP 403.

### 3.2 Seconde publication (remplace « dérive »)

```text
[main 21f0ba2] ci: épingler le runner sur ubuntu-24.04
 1 file changed, 2 insertions(+), 1 deletion(-)
   8fdba83..21f0ba2  main -> main
PUSH_RC=0
```

Vérification du blob au commit, et non du CDN :

```text
CONTENTS HTTP=200
REMOTE_BLOB_SHA 2ed0ae26f5658fdcd0fc732da9c4c66795ba7b20
BYTES 1782
SHA256 b8135c5a750b22651582a7721dccb15b6a28823ef35d5e4af9cd05337216d6bf
```

Piège : juste après le push, `raw.githubusercontent.com` servait encore l'ancien blob `56d2c231…`. Une comparaison `raw` immédiate renvoie `MISMATCH` sans que le push soit en cause.

Run déclenché :

```text
RUN 40519167697 ASTRO-Q°ODE & Al-Mizan CI (V5.1) 21f0ba2 completed failure
CREATED 2026-10-27T14:14:08Z
UPDATED 2026-10-27T14:14:13Z
JOB 122241175505 test-and-verify completed failure STEPS 0
CLASS COMPLETED_NO_STEPS
```

L'annotation `notice` sur la migration `ubuntu-latest` a disparu de ce run : GitHub a bien évalué `runs-on: ubuntu-24.04`. Le verrou de facturation, lui, est inchangé.

## 4. Porte d'immobilité

1. `wait_chat_sessions` a échoué avec le message d'origine « 等待的 ChatSession 不存在 » ; aucun `cold` n'a été obtenu par cette voie.
2. Repli : `list_chat_sessions` a montré que l'écrivain n'était plus actif, puis `read_chat_session` a renvoyé `runtimeState` froid, `activeTurnId: null`, `revision: 0`.
3. Deux échantillons complets espacés de 6 secondes, identiques pour les trois fichiers du package.
4. Le `revision: 0` n'a pas été utilisé comme preuve de recul : c'est la valeur de la lecture.

## 5. Écritures appliquées

Six `Edit` au total, sans réécriture de fichier :

| Fichier | Nombre | Objet |
|---|---|---|
| `SKILL.md` | 2 | piège du CDN ; distinction preuve anonyme / authentifiée |
| `references/cas-verifie-2026-10-27.md` | 4 | limite de facturation corrigée ; section seconde publication ; rejeu daté |

Aucun script modifié : `scripts/verifier_publication_ci.py` est resté à `a55f63a3…`.

## 6. Validation finale

```text
Skill: publier-workflow-ci-github
Files (3): SKILL.md, references/cas-verifie-2026-10-27.md, scripts/verifier_publication_ci.py
PASS description: single line, 958 chars
PASS body: 192 lines (< 500)
PASS local references: 2 checked
PASS skill references: 3 checked
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
```

Contrôles en direct, en lecture seule :

```text
OID 21f0ba2047e3298a6a162afbfe07cb08f27d103c
REF refs/heads/main
RUN 40519167697 … completed failure
CLASS COMPLETED_NO_STEPS
```

Empreintes finales :

| Fichier | Octets | SHA-256 |
|---|---|---|
| `SKILL.md` | 10 440 | `c326f8bb6d15ff6dbd7625cf163d9b10950096d5749b4f633c60445e639abc48` |
| `references/cas-verifie-2026-10-27.md` | 9 192 | `fec42045518d2605ea82cd0e9f129ce8f090111b974a8d1fe6c6c3f7bc716010` |
| `scripts/verifier_publication_ci.py` | 8 579 | `a55f63a34471f51680ae6496c02c1080944f7ae0fe999528334497cf5eb32bf2` |

`__pycache__` créé par la validation a été supprimé ; le package est revenu à trois fichiers.

## 7. Limites et non-vérifié

- Aucune CI verte n'a été observée sur ce dépôt à cette date : le verrou de facturation empêche tout démarrage de job.
- Le run `40519167697` s'arrête en 5 secondes avec 0 étape ; conclure à une erreur de YAML serait faux.
- `raw.githubusercontent.com` n'est pas une preuve de contenu juste après un push.
- Aucun rechargement de Skill ni binding runtime n'a été vérifié ; cette revendication est restée absente du rapport final.
- Les heures de l'écrivain proviennent de son JSONL, pas de son propre résumé : un résumé d'assistant peut se tromper de diagnostic, comme ici avec « fenêtre tronquée ».
