---
name: confirmer-plan-avant-ecriture
description: "Passage pour « propose un plan, attends ma confirmation, puis exécute » : figer l'état cible (fichiers, size, mtime_ns, SHA-256), rédiger le plan en liste d'éditions numérotées (ID, fichier:ligne, original → nouveau, nombre exact), dont chaque option de question couvre exactement le périmètre autorisé — jamais « corriger 2 endroits » quand 3 sont prévus ; un choix de route n'autorise que la route ; après toute attente (session concurrente, build), ré-échantillonner et, si la cible a changé, ré-établir le plan et redemander ; exécuter uniquement les ID approuvés, s'arrêter sur dérive d'ancre ; réconcilier 1:1 approuvé et exécuté, marquer tout surplus « non approuvé », garder un point de retour. Utiliser quand une confirmation avant écriture est exigée ou qu'un choix multiple risque de compresser les modifications. 中文触发：先方案后执行、等待确认、批准清单、选项文本、等待后目标变化、重新请示、超出批准范围、回退点、路线不等于批准。关键词：approval gate, plan-first, authorized scope, option fidelity, re-approval after wait, rollback point."
---

# Confirmer le plan avant d'écrire

## Objectif

Une instruction du type « propose un plan, attends ma confirmation, puis exécute » ouvre un **passage de validation**, pas une étape de communication. Ce Skill le rend vérifiable : ce qui est approuvé est écrit noir sur blanc, l'exécution s'y limite, et l'écart est mesuré après coup.

## Quand l'utiliser

- « 先提出方案，等待我确认后再执行 », « montre-moi le diff avant d'écrire », « ne touche à rien avant mon accord ».
- Le plan dépend d'un état qui peut changer pendant l'attente : session concurrente, tâche longue, build, déploiement.
- Une question à choix multiples porte sur des modifications et son libellé risque de résumer « corriger 2 endroits » alors que l'exécution en prévoit 3.
- Après une attente, il faut décider si l'on reprend le plan ou si l'on repart du nouvel état.

## Quand ne pas l'utiliser

- L'utilisateur a donné une autorisation durable et explicite (AGENTS.md/QODER.md) : suivre cette autorisation, pas ce rituel.
- Aucune écriture n'est prévue : une revue ou un rapport n'a pas besoin de porte.
- Le choix porte sur une orientation sans écriture (nommer un fichier, choisir une source) : c'est une question, pas une approbation.

## Vocabulaire

| Terme | Sens | Ce qu'il n'autorise pas |
|---|---|---|
| Plan | Liste numérotée d'éditions avec ID, fichier:ligne, original → nouveau, nombre exact | Une intention générale (« corriger les incohérences ») |
| Choix de route | Sélection d'une démarche (« attendre la session concurrente ») | Les éditions que la route rendra nécessaires |
| Autorisation | Réponse explicite qui reprend le périmètre du plan | Une réponse à une autre question |
| Liste approuvée | Les ID couverts par l'autorisation | Les ID « évidents » ajoutés en cours de route |
| Liste exécutée | Les éditions réellement appliquées | Ce que le plan prévoyait |

## Étape 0 — Figer l'état cible avant de proposer

Un plan sans état de référence ne peut être ni rejoué ni comparé. Avant de rédiger, enregistrer les fichiers, `size`, `mtime_ns` et `sha256` ; copier les octets si un retour arrière doit être possible hors Git.

Remplacer `<skill-dir>` par le dossier d'installation de ce Skill, `<cible>` par le dossier concerné, `<baseline.json>` et `<copie>` par des chemins sous `.qoder/tmp` ; la copie doit être **hors** de `<cible>`.

```bash
py -3 "<skill-dir>/scripts/instantane_cible.py" \
  --racine "<cible>" \
  --enregistrer "<baseline.json>" \
  --copie "<copie>"
```

Sortie : `SNAPSHOT … files=N`, une ligne `FILE` par fichier, `RESULT: RECORDED`, rc 0. Ne pas continuer si rc ≠ 0.

Conserver les octets (`--copie`) : un hash seul ne restaure rien. Dans la session 94884576, la baseline `14ff7f5c…` n'avait pas été copiée ; le retour arrière a dû être reconstruit en inversant les éditions, puis prouvé par égalité de hash avant production du diff.

## Étape 1 — Rédiger le plan comme une liste d'éditions

Chaque édition reçoit un ID stable (`E1`, `E2`…) et une ligne de tableau :

| ID | Fichier:ligne | Original → nouveau | Compte |
|---|---|---|---|
| E1 | `SKILL.md:27` | « 28 440 o » → « 28 440 o à la découverte, 29 409 o après layout » | 1 |
| E2 | `SKILL.md:169` | mesure inférée → mesures réelles 781 px et 566 px | 1 |

Règles :

- Annoncer le total : « N éditions, F fichiers touchés, aucune autre écriture ».
- Un ID = une édition localisée. Ne pas regrouper sous « corriger 2 endroits » ce qui produira 3 remplacements.
- Écrire l'original **verbatim** et le nouveau texte complet ; une paraphrase ne permet pas de vérifier l'ancre.
- Lister séparément les fichiers seulement lus, les scripts exécutés et les artefacts supprimés.
- Lister explicitement le **hors périmètre** : fichiers et zones qui ne seront ni modifiés, ni créés, ni supprimés. « Aucune autre écriture » ne suffit pas quand un fichier voisin est plausible.
- Une édition qui dépend d'une découverte à venir (« si le script manque, le réécrire ») reste **conditionnelle** : elle ne s'exécute qu'après un second passage, avec son propre plan.

## Étape 2 — Poser la question sans compresser

Le texte de chaque option doit couvrir exactement le périmètre qu'elle autorise.

- Option qui autorise un plan : renvoyer au plan **intégral** présent dans le même message et reprendre ses chiffres (« créer les 2 fichiers E1–E2, aucune autre écriture »).
- Option qui n'autorise qu'une route : le dire (« attendre la session, puis me représenter le plan »). Elle n'autorise aucune édition.
- Interdit : « corriger 2 endroits » quand le plan en compte 3 ; « appliquer les corrections » sans total ; « OK » sans objet.
- Si le plan ne tient pas dans une option, ne pas le résumer : poser la question de route, puis, la route choisie, présenter le plan et attendre une seconde confirmation.

Un choix de route n'est pas une approbation de plan. La réponse à une question antérieure ne couvre pas les éditions découvertes après elle.

## Étape 3 — Attendre, puis re-vérifier l'état

Toute attente (session concurrente, tâche longue, build) invalide l'hypothèse « la cible est celle du plan ». À la fin de l'attente, comparer avant de reprendre :

```bash
py -3 "<skill-dir>/scripts/instantane_cible.py" \
  --racine "<cible>" \
  --comparer "<baseline.json>"
```

- rc 0 / `RESULT: UNCHANGED` : le plan reste valable ; exécuter les ID approuvés.
- rc 1 / `CHANGED` : lire les lignes `CHANGED`, `ADDED`, `REMOVED`. **Ne pas exécuter le plan.** Relire les fichiers réels, ré-établir la liste d'éditions sur les nouveaux octets, puis redemander.
- rc 2 : la comparaison n'a pas eu lieu ; traiter comme une attente non concluante, pas comme un feu vert.

Ne pas interpréter `turn_completed`, `ready` ou un silence comme une autorisation. L'attente prouve seulement que rien n'écrit plus ; elle ne prouve ni que la cible est inchangée, ni que le plan est approuvé.

## Étape 4 — Exécuter exactement les ID approuvés

- Avant chaque édition, vérifier que l'ancre existe et correspond à l'original du plan.
- `Edit` à 0 occurrence, fichier modifié depuis la lecture ou contenu inattendu : **arrêter**, rapporter, ne pas improviser une ancre voisine.
- Ne pas corriger au passage une incohérence découverte pendant l'exécution : la consigner comme proposition `E(n+1)` non approuvée.
- Un fichier non listé dans le plan n'est ni créé, ni modifié, ni supprimé.

## Étape 5 — Réconcilier 1:1 et garder un point de retour

Comparer la liste approuvée et le diff réel, ID par ID :

| Contrôle | Attendu |
|---|---|
| Nombre d'éditions | exécuté = approuvé |
| Fichiers touchés | sous-ensemble exact de la liste |
| Surplus | chaque édition hors liste étiquetée `non approuvé` |
| Point de retour | hash et octets d'avant écriture disponibles |

Un surplus, même correct et même petit, reste `non approuvé` : le proposer (garder ou retirer), pas le déclarer inclus. Pour retirer un surplus, restaurer les octets du point de retour et vérifier le hash ; ne pas « re-corriger à l'envers » à l'aveugle.

## Étape 6 — Ouvrir la porte de chargement sur la version livrée

Un PASS de `skill-file-qa` vaut pour une empreinte, pas pour le fichier. Après l'exécution, lier chaque PASS au couple `size` + `sha256` qu'il a validé, puis prouver que ces octets sont ceux que le runtime charge.

1. `QA_VERSION=<size>/<sha256>` : relever l'empreinte au moment du PASS. Un PASS sans empreinte est une affirmation, pas une preuve.
2. Appeler le Skill livré en lecture seule avec un jeton `BINDING` unique, puis comparer le corps injecté au corps du disque : retirer le frontmatter et une éventuelle ligne vide de tête, puis exiger égalité de longueur et de SHA-256. `isMeta` est au niveau supérieur de l'enregistrement JSONL, pas dans `message` ; une console cp1252 peut faire échouer la comparaison — reconfigure la sortie avant de conclure.
3. Écrire `LOADED=YES` seulement si la comparaison est exacte et si l'empreinte du disque n'a pas bougé entre l'appel et la comparaison.
4. Si le disque ne porte pas `QA_VERSION`, ou si une écriture tierce apparaît après la livraison, l'ancien PASS est **périmé** : attribuer l'écriture par le `file_path` exact des `Write`/`Edit` du JSONL, jamais par `runtimeState`, rejouer la QA sur les nouveaux octets, puis rouvrir la porte. Ne pas écraser le contenu concurrent.

La mécanique d'injection, de `BINDING`, de bornage de version et d'attribution d'écrivain appartient à `verify-injected-skill-body-freshness` (`scan_skill_writers.py`) et à `verify-skill-runtime-binding` (`locate_injection.py`) ; cette étape n'en garde que la porte, les champs de rapport et la règle d'arrêt. Un chargement réussi ne prouve pas que la version livrée est correcte, seulement que les octets comparés sont ceux qui se chargent.

## Étape 7 — Rapport

```text
PLAN_ID=<identifiant du message contenant le plan>
APPROVED=<n> editions / <f> fichiers
TARGET_STATE=<UNCHANGED|CHANGED> (comparaison avant execution)
EXECUTED=<n> editions / <f> fichiers
UNAPPROVED=<n> [IDs]
REVERTED=<n> [IDs]
ROLLBACK=<sha256 avant ecriture | copie>
QA_VERSION=<size>/<sha256> de la version validee
LOADED=<YES|NO> (<size>/<sha256> de la version injectee)
POST_DELIVERY_DRIFT=<NONE|n ecritures (session, jsonl:line, UTC) -> QA rejouee sur <sha256>>
RESULT=<PASS|FAIL>
```

`RESULT: PASS` exige `EXECUTED - REVERTED = APPROVED`, `UNAPPROVED=0`, `TARGET_STATE=UNCHANGED`, `QA_VERSION` égal à l'empreinte courante et `LOADED=YES`. `POST_DELIVERY_DRIFT` doit valoir `NONE`, ou nommer les écritures et la QA rejouée sur la nouvelle empreinte. Sinon écrire `FAIL` et l'écart.

## Cas vérifié — session 94884576

| Fait | Valeur observée |
|---|---|
| Option présentée | « 等它静默后补缺口（推荐） », description « 修正 2 处措辞 » |
| Éditions réellement appliquées | 3 ; la troisième ajoutait « commentaires HTML » à `SKILL.md:134` |
| État au moment du plan | `SKILL.md` 9 308 o, `verifier_prototype.py` absent |
| État après l'attente | `SKILL.md` 9 853 o, script 9 778 o — plan jamais ré-établi |
| Correction utilisateur | « 解释为什么跳过确认流程直接执行 » (« explique pourquoi tu as sauté le processus de confirmation et exécuté directement ») |
| Retour arrière | 3e édition retirée → 9 979 B / `8a3e86c0…` ; puis les 2 autres retirées sur « 撤回这两行 » (« retire ces deux lignes ») → 9 853 B / `14ff7f5c…`, QA PASS |

Le défaut n'était pas l'absence de question, mais une question dont le texte autorisait moins que l'exécution, et une reprise après attente sans nouveau plan.

## Cas vérifié — session 8c34eae4 (livraison puis écriture tierce)

| Fait | Valeur observée |
|---|---|
| QA de livraison | `SKILL.md` 9 623 B / `1e642132…`, 11:24:48 +01:00 |
| Écritures après livraison | 4 `Edit` : `29873d2c` 10:26:28Z et 10:26:31Z ; `6b24a8c5` 10:28:15Z et 10:28:22Z |
| État au chargement | 10 177 B / `61a2f000…` ; le PASS de livraison ne couvre plus ces octets |
| Appel en lecture seule | `Launching skill: confirmer-plan-avant-ecriture`, base directory attendu |
| Comparaison brute | `EXACT_MATCH False`, premier écart à 0 ; 8 543 car. injectés contre 8 545 au disque (frontmatter + ligne vide de tête) ; un libellé accentué lève `UnicodeEncodeError` cp1252 |
| Comparaison normalisée | 8 543 car. et `902a94bf…` des deux côtés ; `isMeta` au niveau supérieur de l'enregistrement JSONL |
| Suite | `LOADED=YES` pour 10 177 B ; PASS de 9 623 B déclaré périmé ; QA rejouée sur 10 177 B (rapport de session : 9 pass, 0 fail, 0 warn) |

Le défaut n'était ni l'écriture ni le chargement, mais un PASS attaché à une version qui n'était plus celle du disque. Un chargement réussi ne vaut que pour l'empreinte comparée.

## Limites

- Ce Skill ne juge pas le contenu du plan : un plan approuvé peut être mauvais.
- Il ne remplace ni `skill-update-concurrency-safe` (écriture concurrente), ni `adopt-concurrent-duplicate-skill` (décision de reprise), ni `skill-file-qa` (validation statique).
- Une comparaison `UNCHANGED` ne prouve pas que le plan est complet, seulement que la cible n'a pas bougé.
- Le mécanisme d'injection, de `BINDING`, de bornage de version et d'attribution d'écrivain appartient à `verify-injected-skill-body-freshness` et à `verify-skill-runtime-binding` ; ce Skill n'en garde que la porte, les champs de rapport et la règle d'arrêt.
- Un `LOADED=YES` ne prouve pas que les octets livrés sont corrects, seulement que ce sont eux qui se chargent ; une écriture tierce pendant le chargement se traite selon `audit-skill-during-live-creation`.
