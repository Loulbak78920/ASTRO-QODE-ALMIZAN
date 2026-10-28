---
name: verifier-preuves-api-temporelles
description: "Réconcilier une preuve d'API observée en session avec son état au build : figer chaque observation (UTC, URL exacte, auth, statut, compteur), rejouer la sonde en lecture seule, comparer par surface et par instant, classer IDENTIQUE / DIVERGENCE_TARDIVE / TRANSIENTE / INDETERMINEE / NON_REJOUEE, remplacer toute règle catégorique (auth vs anonyme, vide, présent) par un modèle de propagation daté, réécrire les tests négatifs dont la prémisse a changé et consigner les branches déclenchées ou non. Pour preuve de session périmée, annotations vides puis présentes, page sans puis avec message, surfaces lues à des instants différents, test --anonymous au mauvais code, heure locale confondue avec UTC, retard d'une API tierce. 中文：UTC 冻结来源证据，复跑只读探针，按接口面与时刻比较，把认证/匿名、空/存在等绝对规则改写为带时间的传播模型，重写前提失效的负向测试并登记分支；触发同上。English: reconcile stale API evidence with build-time state, replay read-only, compare by surface and instant, date propagation, rewrite invalidated negative tests, log branches; triggers as above."
---

# Vérifier des preuves d'API temporelles

## Objectif et portée

Une observation faite dans une session (`HTTP 200`, `[]`, page sans message) n'est pas une propriété permanente d'une API. Ce Skill transforme une preuve datée en règle datée : rejouer la même sonde au moment de la rédaction, comparer par surface et par instant, puis réécrire les règles et les tests qui reposaient sur l'ancien état.

Couvert : API tierce, interface rendue côté client, index de recherche, cache, webhook, tout résultat dont la visibilité peut retarder.

Non couvert :

- un fixture déterministe à rejouer à l'identique → `replay-skill-reference-fixtures` ;
- la seule classification d'une affirmation avant écriture → `verify-skill-doc-claims-before-edit` ;
- la fraîcheur des hashes, tailles et comptes de fichiers d'un paquet → `verifier-fraicheur-preuves-skill` ;
- le diagnostic GitHub Actions lui-même → `diagnostiquer-run-github-actions-sans-logs`.

## Quand utiliser

- Une sortie d'outil de session doit devenir une règle de `SKILL.md` ou d'une référence.
- La même requête rend un résultat différent au moment du build.
- Une règle « anonyme vs authentifié », « vide » ou « présent » a été inférée de lectures non simultanées.
- Un test négatif prévu ne rend plus le code de sortie attendu.
- Un rapport ou une référence mélange une heure locale et une heure UTC.

## Vocabulaire

**Observation (`OBS`)** : un enregistrement indivisible de `{instant UTC, surface, mode d'auth, requête exacte, statut HTTP, digest du corps, compteur extrait, extrait brut}`.

**Surface** : couple endpoint exact + couche interrogée (API anonyme, API authentifiée, HTML/UI, cache). `/check-runs/{id}/annotations` et `/commits/{sha}/check-runs` sont deux surfaces différentes.

**Prémisse** : observation sur laquelle reposent une règle ou un test. Si la prémisse change, la règle et le test changent avec elle.

## Règles dures

1. **Pas d'observation sans UTC, requête exacte et mode d'auth.** Un texte de narration n'est pas une sortie d'outil : le classer `DOCUMENTEE`, jamais `REPRODUITE`.
2. **Deux surfaces vues à des instants différents ne sont pas simultanées.** Consigner l'écart `Δ` avant toute comparaison.
3. **Rejouer avant d'écrire.** Sans rejeu, l'affirmation reste `NON_REJOUEE` et datée ; elle n'est pas « courante ».
4. **Une divergence ne désigne pas un gagnant.** Elle impose un modèle daté, pas le remplacement silencieux d'une valeur par l'autre.
5. **`HTTP 200` + `[]` signifie « rien de visible sur cette surface à cet instant »**, pas « absent ».
6. **Toute règle catégorique issue d'une observation est provisoire.** La version stable est datée et adossée à au moins deux observations.
7. **Un test dont la prémisse a changé est `INVALIDE`.** S'il n'a pas été exécuté, il est `NON_DECLENCHE` ; il n'est jamais « couvert ».
8. **Exit code couvert ≠ branche couverte.** Nommer la branche qui a rendu le code.
9. **Lecture seule, sans secret.** Aucun jeton dans un fichier, une sortie ou un rapport ; aucune redirection suivie avec un en-tête `Authorization`.

## Procédure

### 1. Figer la preuve source

Extraire du snapshot ou du JSONL : `sessionId`, horodatage, nom d'outil, entrée exacte, sortie exacte. Remplir une ligne par observation, jamais une ligne par conclusion.

```text
OBS_SOURCE 2026-10-27T14:10:22Z | api-anon | GET /repos/<o>/<r>/check-runs/<id>/annotations | 200 | [] | len=0
OBS_SOURCE 2026-10-27T14:11:16Z | api-auth | GET /repos/<o>/<r>/commits/<sha>/check-runs | 200 | 1 check-run | annotations_count=2
```

Vérifier sur la sortie brute, pas sur le résumé : un `count` recopié d'une narration est `DOCUMENTE`. Si le snapshot est tronqué, parser le JSONL du projet et apparier `tool_use` / `tool_result` avant de citer.

### 2. Rejouer la même sonde

Rejouer à l'identique : même URL, mêmes paramètres, même mode d'auth. Capturer l'instant **avant et après** la requête, en UTC.

```bash
URL="https://api.github.com/repos/<owner>/<repo>/check-runs/<id>/annotations"
OUT="$HOME/.qoder/tmp/sonde-$(date -u +%Y%m%dT%H%M%SZ).json"
T0=$(date -u +%Y-%m-%dT%H:%M:%SZ)
curl -sS --max-redirs 0 -D "$OUT.headers" -o "$OUT" \
  -w 'HTTP=%{http_code} BYTES=%{size_download}\n' \
  -H 'Accept: application/vnd.github+json' "$URL"
T1=$(date -u +%Y-%m-%dT%H:%M:%SZ)
echo "T0=$T0 T1=$T1"
py -3 -B -c "import json,hashlib,sys; b=open(sys.argv[1],'rb').read(); d=json.loads(b); print('SHA256',hashlib.sha256(b).hexdigest()); print('TYPE',type(d).__name__); print('COUNT',len(d) if isinstance(d,(list,dict)) else 'n/a')" "$(cygpath -w "$OUT")"
```

- `--max-redirs 0` empêche de suivre une redirection : un `3xx` n'est pas la réponse finale, et suivre peut envoyer `Authorization` vers un autre hôte.
- Pour une surface authentifiée, lire le jeton via `git credential fill` et le passer directement à `curl` ; ne jamais l'afficher.
- Refaire la sonde au moins deux fois, à quelques minutes d'intervalle, avant de déclarer un état stable.
- Ne pas généraliser d'une surface à l'autre : re-sonder chaque surface que la règle prétend décrire.

### 3. Comparer et classer

Calculer `Δ = T2 − T1` et comparer uniquement des observations de même surface et de même mode d'auth.

| Verdict | Condition | Conséquence |
|---|---|---|
| `IDENTIQUE` | même surface/auth, même statut et même digest (ou même compteur) | La preuve source reste vraie à `T2`, mais reste datée |
| `DIVERGENCE_TARDIVE` | `T2 > T1`, un élément caché est devenu visible | Modéliser un retard de propagation ; ne pas déclarer la source fausse |
| `DIVERGENCE_TRANSIENTE` | `T2 < T1`, ou retour à l'état initial sur ≥ 2 rejeux | Modéliser une fenêtre (cache, rollback, index) ; aucune règle permanente |
| `INDETERMINEE` | URL, auth ou paramètres différents ; erreur ; timeout ; `3xx` non suivi | Aucune conclusion ; corriger la sonde ou renoncer |
| `NON_REJOUEE` | pas d'accès réseau ou de jeton | L'affirmation reste datée ; ne jamais la présenter comme actuelle |

Un écart d'état entre deux surfaces lues à `T1` et `T2` ne prouve pas un effet de permission : il peut être entièrement temporel. Consigner `Δ` même quand il est court.

### 4. Requalifier la règle

Remplacer chaque règle catégorique par une phrase qui reste vraie à toutes les observations.

| À éviter | À écrire |
|---|---|
| « L'API anonyme ne renvoie pas les annotations » | « À 14:10:22Z, l'API anonyme renvoyait `[]` ; à 14:17:56Z, elle renvoyait 2. Retard observé sur ce cas : 7 min 34 s ; aucune borne générale n'est prouvée. » |
| « La page n'affiche pas le message » | « Page du job `<id>` à 14:11:09Z : 0 occurrence ; à 14:18:15Z : 1 occurrence. » |
| « Toujours », « jamais », « vide » sans date | « Au dernier rejeu `T2`, sur la surface `S`, avec l'auth `A` : `<valeur>` » |

La règle durable est celle qui explique les deux observations, par exemple : « une surface publique vide n'est pas une preuve d'absence ; relire plus tard et avec le jeton avant de conclure ». Elle ne prétend pas connaître la durée du retard.

### 5. Re-dériver les tests et les branches

Reprendre chaque test prévu et nommer sa prémisse. Un changement d'observation invalide le test, même si un autre test rend le même code de sortie.

| Test | Prémisse | Observation au build | Statut | Remplacement |
|---|---|---|---|---|
| `--anonymous` → exit 1 | annotations anonymes vides | 2 annotations → exit 0 | `INVALIDE` | garder le comportement observé comme test positif ; chercher une entrée réelle pour la branche |
| dépôt invalide → exit 2 | aucune | exit 2 | `EXECUTE` | conserver |
| run avec étapes → exit 1 | aucune | exit 1, branche `RUN_HAS_STEPS` | `EXECUTE` | nommer la branche, pas seulement le code |

Tenir un registre explicite :

```text
BRANCHE NO_STEPS_CAUSE_PROVEN      exit 0  EXECUTE
BRANCHE RUN_HAS_STEPS              exit 1  EXECUTE
BRANCHE API_ERROR                  exit 2  EXECUTE
BRANCHE NO_STEPS_CAUSE_UNPROVEN    exit 1  NON_DECLENCHE  (lecture du code seulement)
```

Règles :

- Ne pas modifier l'entrée pour forcer l'ancien résultat ; consigner le nouveau comportement.
- Un `exit 1` obtenu par une autre branche ne couvre pas la branche attendue.
- Si aucune entrée réelle ne déclenche une branche, écrire `NON_DECLENCHE` et s'appuyer sur la lecture du code, pas sur le code de sortie.

### 6. Écrire le paquet

- `SKILL.md` : règles durables, procédure, modèle de rapport. Les valeurs datées vont dans la référence.
- `references/` : table complète des observations, commandes, extraits bruts, section « non vérifié », écart de fuseau éventuel.
- Ne pas recopier l'horodatage d'un Skill voisin : le recalculer en UTC. Si un voisin porte une étiquette de fuseau fausse, le citer factuellement comme contre-exemple sans modifier son paquet, sauf demande explicite.
- Ne pas écrire de hash de ses propres fichiers dans sa référence : les empreintes finales vont dans le rapport de livraison.

### 7. Rejouer et rapporter

Rejouer la commande documentée après écriture. Si le résultat diffère de la référence, revenir à l'étape 3 ; ne pas ajuster le texte pour qu'il colle silencieusement.

```text
OBS_SOURCE <UTC> <surface> <auth> <url> -> <statut> <compteur/digest>
OBS_BUILD  <UTC> <surface> <auth> <url> -> <statut> <compteur/digest> DELTA <secondes>
VERDICT <IDENTIQUE|DIVERGENCE_TARDIVE|DIVERGENCE_TRANSIENTE|INDETERMINEE|NON_REJOUEE>
REGLE_DATE <phrase vraie aux deux observations>
TESTS <nom> <VALIDE|INVALIDE|NON_DECLENCHE|EXECUTE> <code/branche>
BRANCHES <branche> <code> <EXECUTE|LECTURE_SEULE|NON_DECLENCHE>
NON_VERIFIE <ce qui reste hors de portée>
```

## Cas de référence

`references/cas-annotations-2026-10-27.md` — annotations GitHub : `[]` anonyme à 14:10:22Z, 2 à 14:17:56Z, `annotations_count=2` authentifié lu 54 s après le `[]` ; page sans message puis avec à 14:18:15Z ; test `--anonymous` attendu exit 1 mais obtenu exit 0 ; branche `NO_STEPS_CAUSE_UNPROVEN` non déclenchée ; étiquette `15:18 UTC` d'un Skill voisin en réalité locale (`14:18Z`).

## Pièges

- **Heure locale vs UTC.** `date` sans `-u`, `ls -la` et les journaux locaux affichent `UTC+1` ici : `15:18` local = `14:18Z`. N'étiqueter UTC qu'après `date -u`.
- **Confond temporel.** Une lecture anonyme à `T1` et une lecture authentifiée à `T2` ne prouvent pas un effet de permission.
- **`200` + `[]`.** Réponse valide et ambiguë : elle ne dit rien sur l'existence future de l'élément.
- **UI rendue côté client.** Compter des chaînes exactes (`account is locked`, `not started`) et le faire par identifiant de job ; le payload peut être générique ou différé.
- **Redirections.** Un `3xx` n'est pas la réponse finale ; suivre une redirection peut fuiter le jeton. Utiliser `--max-redirs 0` et lire `Location`.
- **Cache/CDN.** Deux rejeux espacés valent mieux qu'un seul ; ne pas conclure d'une variation unique.
- **Surface différente.** Un check-run, une liste de check-runs et une page HTML ne sont pas interchangeables.
- **Windows.** Utiliser `py -3` (l'alias Microsoft Store échoue), `cygpath -w` pour un chemin lu par Python, et se méfier des accents affichés en cp1252.
- **Secret.** Ne jamais écrire le jeton dans `--out-dir`, un journal ou une réponse.

## Ressources

- `references/cas-annotations-2026-10-27.md` — preuves horodatées, commandes, extraits, test invalidé, registre de branches, non-vérifiés.
