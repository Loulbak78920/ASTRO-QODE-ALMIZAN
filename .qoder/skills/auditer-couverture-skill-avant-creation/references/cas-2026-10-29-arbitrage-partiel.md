# Cas du 29/10/2026 — couverture partielle et arbitrage d'échéance

## Contexte

- Session source : `59fbebb1-0a59-4a79-8761-8d96b8a3aead`, projet `C--Users-Administrateur-Desktop-IMAM8MAHDI`, titre « 创建 Skill 先提方案 ».
- Snapshot au moment de la lecture : `runtimeState=cold`, `activeTurnId=null`, `revision=0`, `hasMoreBefore=false`, `queuedTurnCount=0`, `pendingInteractionCount=0`.
- Contenu humain : un seul message (la demande de création) et un seul arbitrage, rendu comme réponse à `AskUserQuestion`.
- Recommandation reçue : `action=create`, `skillName=rediger-skill-md-exemples-sans-faux-positifs`.
- Validateur utilisé pour les mesures : `skill-file-qa`, PyYAML 6.0.1, lecture seule.

## Ce que la session a établi

| Élément | Constat |
| :--- | :--- |
| Couverture | Quatre Skills installés couvrent l'essentiel : prédiction des références comptées, réparation des FAIL, citations inter-Skills, règle du PASS périmé |
| Delta réel | Une seule distinction manquait : citer un artefact, qui doit être vérifié, contre illustrer une forme, qui se réécrit en prose |
| Décision | Mise à jour du Skill de réparation, pas de création |
| Résultat | `reparer-paquet-skill-echecs-qa` : 18 159 octets, 4 fichiers, `RESULT PASS` 10/0/0 |

## Le critère qui a inversé la décision

La recommandation demandait un Skill de rédaction « avant écriture ». Or les deux FAIL qui ont motivé la règle se produisent pendant la QA, après écriture. À cet instant, le Skill proposé n'existe pas : il n'est pas sélectionnable. Le Skill chargé est celui de réparation, et c'est donc lui qui porte la règle.

Ce n'est pas une observation statistique mais une conséquence logique : un paquet non créé ne peut pas être chargé au moment du défaut. Le taux de couverture n'entre pas dans ce raisonnement.

## Arbitrage utilisateur

Texte conservé par la sortie de l'outil : « Update repair Skill (Recommended) ».

Limite : le snapshot ne conserve que le libellé choisi. Le jeu complet d'options — mise à jour, création, les deux, rapport seul — n'est pas observable ; il n'est donc pas prouvé que quatre options aient été proposées. L'instance établit un arbitrage explicite et le rejet de la création, rien de plus.

## Corrections apportées à la recommandation

- Elle affirmait que l'auditeur de couverture « ne fait que des statistiques ». C'est faux : sa table de décision et sa règle 9 traitaient déjà le choix création/mise à jour. La recommandation était donc `OVERSTATED`, pas `SUPPORTED`.
- La session source ne contient **aucune correction utilisateur**. L'unique intervention humaine est l'arbitrage ci-dessus ; le reste du raisonnement est une décision de l'assistant.

## Vérification indépendante (29/10/2026)

Réexécution de `reparer-paquet-skill-echecs-qa` depuis `C:/Users/Administrateur`, sans réutiliser le PASS de la session source :

```text
Fingerprint: 18159 bytes | mtime=2026-10-29T17:49:21+01:00
sha256=8b6313b293676bc2f5a511bf344411d25c67c902648a4d0ee0315f0c0f3d715e
References fingerprint: 3 file(s) | sha256=676e3c518f487d88bdabac364e305914b50ec1ff03074a05958e85d8026126dc
Files (4)
Summary: 10 pass, 0 fail, 0 warn
RESULT PASS
RC=0
```

Fichiers du paquet réparé, mesurés le même jour :

| Fichier | Octets | SHA-256 |
| :--- | ---: | :--- |
| SKILL.md | 18 159 | `8b6313b293676bc2f5a511bf344411d25c67c902648a4d0ee0315f0c0f3d715e` |
| references/cas-2026-10-28-42301ab5.md | 4 666 | `68032cec2b4bcb069ea4df47d209005c2acbd5fe323402fab5f1207e4affd3c2` |

## Limites

- Un seul cas. Il établit le critère et son effet sur une décision, pas sa fréquence.
- Les deux recommandations successives portaient sur le même validateur ; le critère n'a pas encore été exercé sur un Skill sans script ni sur une mise à jour concurrente.
- L'inscription du critère dans la règle 9 et la section 6bis est une correction documentaire : elle ne prouve pas qu'un autre agent l'appliquera. Seule une session indépendante le montrerait.
