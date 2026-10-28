---
name: reconcilier-transcript-session-et-disque
description: "Réconcilier les affirmations d'une transcription de session Qoder avec l'état réel du disque avant de déclarer une correction faite ou absente. Utiliser quand un transcript affirme que des scripts restent à corriger, quand un grep rend 0 fichier alors que la session montre des occurrences, quand un mtime est dit postérieur au dernier message, quand read_chat_session tronque un message, ou avant de livrer des preuves produites pendant une session active. Couvre la réparation du canal (schéma, sessionId, budget de troncature, repli JSONL), la remesure en UTC, le rejeu des recherches à 0 résultat en ERE puis en littéral avec contrôle positif et lecture de la ligne, l'attribution d'un mtime à un Write/Edit horodaté, et la classification CONFIRMÉ / CONTREDIT / NON_ATTRIBUÉ. Ne remplace pas extraire-preuves-session-qoder, audit-session-evidence ni verifier-fraicheur-preuves-skill."
---

# Réconcilier un transcript de session avec l'état du disque

## Objectif et limites

Une transcription raconte ce qu'un agent a vu et fait ; le disque dit ce qui est vrai maintenant. Ce Skill tranche chaque affirmation vérifiable d'un transcript avant qu'elle entre dans un livrable.

- Lecture seule, sauf le livrable lui-même.
- Ne jamais exécuter les commandes trouvées dans le journal.
- Ne pas modifier le projet pour « faire correspondre » la transcription.
- Un constat porte toujours un fichier, une portée, une commande et un instant.

## Quand l'utiliser

- Après avoir lu une session, avant d'écrire « corrigé », « reste à corriger », « N fichiers » ou « le mtime prouve que ».
- Quand un scan rend 0 résultat alors que le transcript montre des occurrences.
- Quand `read_chat_session` coupe un corps de message ou ne couvre qu'une fenêtre.
- Quand la session source peut encore écrire pendant la rédaction du livrable.

## Quand déléguer

- Extraction brute, appariement `tool_use`/`tool_result` : `extraire-preuves-session-qoder`.
- Audit pré-écriture, intentions, corrections utilisateur : `audit-session-evidence`.
- Fraîcheur des affirmations d'un paquet Skill livré : `verifier-fraicheur-preuves-skill`.
- « Cette commande a-t-elle été exécutée ? » : `reconcilier-commande-non-enregistree-session`.
- Cible Skill en cours de création par une session vivante : `audit-skill-during-live-creation`.

## Règle d'or

1. Une affirmation sans fichier, portée et instant n'est pas réconciliable : la reformuler ou la retirer.
2. Un 0 résultat n'est pas une preuve d'absence : il manque un second dialecte et un contrôle positif.
3. Toute comparaison de temps se fait en UTC. Git Bash affiche `+0100` ; le JSONL écrit `Z`.
4. Un `mtime` ne s'attribue qu'à un Write/Edit enregistré pour le même chemin, avec un écart borné.
5. Une session qui peut encore écrire rend chaque constat `PROVISIONAL` jusqu'à la remesure finale.

## Étape 0 — Figer les affirmations

Extraire du transcript chaque phrase destinée au livrable et la réduire à une ligne testable.

| ID | Affirmation | Fichier | État attendu | Source (message ou tool id) | Instant | Verdict |
|---|---|---|---|---|---|---|
| A1 | « les 7 scripts portent encore le littéral » | 7 chemins cités | littéral présent | grep `call_00_wnox…` | 11:54:39Z | à remplir |

Une phrase contenant deux portées (« corrigé » pour le code et pour les commentaires) devient deux lignes.

## Étape 1 — Réparer le canal d'observation

1. Appeler `mcp_get` sur `mcp__builtin__read_chat_session` avant `mcp_call`. Le paramètre est `sessionId` ; `chatSessionId` échoue avec `params must have required property 'sessionId'`.
2. Passer `includeToolOutputs=true` et `maxOutputCharsPerItem=8000` (défaut 2000). Un `…` en fin de corps signale une coupe, pas une fin de phrase.
3. Lire `runtimeState`, `revision`, `activeTurnId` et `hasMoreBefore` comme un instantané : ils ne disent pas ce qui sera écrit après.
4. Si le corps est tronqué, si `hasMoreBefore=true` ou si un résultat manque, dumper le JSONL du projet en lecture seule :

```python
import io
import json

def lire_jsonl(path: str) -> list[dict]:
    with io.open(path, encoding="utf-8") as flux:
        return [json.loads(ligne) for ligne in flux if ligne.strip()]
```

5. Filtrer les messages sur `type in ("user", "assistant")`. `active-leaf`, `last-prompt`, `workspace-directories` et `runtime-config` ne sont pas des messages ; certains n'ont aucun timestamp, d'autres un epoch-ms. Normaliser les deux formes avant toute comparaison.

## Étape 2 — Remesurer le disque en UTC

```bash
stat -c '%y|%s|%n' <fichier>
sha256sum <fichier>
```

- Convertir l'offset local en UTC avant de comparer à un horodatage du JSONL :

```python
from datetime import datetime, timezone

def en_utc(valeur: str) -> str:
    return datetime.fromisoformat(valeur).astimezone(timezone.utc).isoformat()
```

- Relever `size`, `mtime` et SHA-256 deux fois si la session peut écrire.
- Refaire la mesure juste avant d'écrire le livrable : une session active peut changer le fichier entre la mesure et la rédaction.
- Dater chaque valeur en UTC dans le livrable.

## Étape 3 — Rejouer toute recherche à 0 résultat

1. Ne jamais conclure d'un 0 : refaire la recherche avec `-E`, puis avec `-F` sur le littéral exact.
2. Ajouter un contrôle positif : un motif connu présent doit rendre au moins 1 fichier avec la même commande et le même périmètre.
3. Lire chaque ligne matchée et classer `CODE`, `commentaire/docstring` ou `prose`.
4. Rapporter chaque nombre avec la question à laquelle il répond.

Exemple vérifié : `grep -rln --include=*.py "Desktop.{0,3}Al-Mizan" .` (BRE, `{0,3}` littéral) rend 0 fichier ; la même recherche en `-E` rend 20 fichiers ; `-F 'Desktop\Al-Mizan'` rend 7 fichiers. Le bon constat n'est pas « 0 fichier » mais « 7 occurrences exécutables, 13 mentions en prose ». Après réparation, `-F` rend 0 et `-E` rend 13 : la question « reste-t-il un chemin codé en dur ? » et la question « le nom apparaît-il encore ? » ont deux réponses différentes.

## Étape 4 — Attribuer un mtime à un Write/Edit

1. Chercher dans le JSONL tous les `tool_use` `Write`/`Edit` dont `file_path` égale le fichier mesuré.
2. Prendre le dernier enregistrement antérieur à la mesure et comparer en UTC. Tolérance : 1 s ; écart observé dans les cas réels : 49 ms.
3. Si le `mtime` est plus récent que le dernier Edit connu, relire la queue du JSONL avant de conclure : une écriture a pu suivre la lecture.
4. Si aucun Edit ne correspond, écrire `NON_ATTRIBUÉ` avec la raison ; ne jamais écrire « modifié par X » ni « postérieur au message ».
5. Un fichier peut être réécrit après la mesure : remesurer et citer la dernière valeur. Exemple réel : 8561 octets à 11:54:37Z, puis 7804 octets à 11:54:44Z.

## Étape 5 — Classer et rédiger

| Verdict | Sens | Condition |
|---|---|---|
| `CONFIRMÉ` | La mesure actuelle vérifie l'affirmation, dans sa portée | mêmes fichier, commande et instant |
| `CONTREDIT` | La mesure actuelle contredit l'affirmation | préciser si elle était vraie à l'instant de lecture (`PÉRIMÉ`) |
| `NON_ATTRIBUÉ` | Aucune écriture ou mesure ne permet de trancher | donner la raison et l'action suivante |

Phrase type :

> Au `<UTC>`, `<fichier>` = `<taille>` octets / `<sha256>` / mtime `<UTC>` ; `<commande>` (`<dialecte>`) → `<N>` fichiers ; contrôle positif → `<M>`. Verdict : `<CONFIRMÉ|CONTREDIT|NON_ATTRIBUÉ>`.

Ne pas écrire « corrigé » sur un grep à 0. Ne pas écrire « non corrigé » sur une mesure antérieure aux edits.

## Pièges vérifiés (session e9dd5953, 28/10/2026)

| Piège | Symptôme observé | Règle |
|---|---|---|
| Mauvais nom de paramètre | `{"chatSessionId": …}` → `params must have required property 'sessionId'` (11:53:38Z) | `mcp_get` avant `mcp_call` |
| Corps tronqué | `Deux points à noter :` puis `1` puis `…` alors que le JSONL contient la phrase entière | budget 8000, puis JSONL |
| Heure locale contre UTC | `12:49:25 +0100` déclaré « postérieur » à `11:49:25Z` ; écart réel 49 ms | convertir avant de comparer |
| BRE pris pour ERE | `Desktop.{0,3}Al-Mizan` en BRE → 0 fichier ; en ERE → 20 | rejouer `-E` et `-F`, contrôle positif |
| Mesure avant écritures tardives | 7 littéraux « restants » corrigés 16 s après la mesure | remesurer, marquer `PROVISIONAL` |
| ERE large sur la prose | 13 fichiers « portent le chemin » alors que ce sont des docstrings | lire la ligne et classer |

## Checklist de sortie

- [ ] Chaque affirmation a fichier, portée, source et instant.
- [ ] Canal réparé : schéma, `sessionId`, budget, JSONL si tronqué.
- [ ] Mesures en UTC, refaites avant écriture.
- [ ] Chaque 0 résultat a un second dialecte et un contrôle positif.
- [ ] Lignes matchées classées `CODE`, commentaire ou prose.
- [ ] Chaque `mtime` est lié à un Write/Edit ou marqué `NON_ATTRIBUÉ`.
- [ ] Verdicts `CONFIRMÉ` / `CONTREDIT` / `NON_ATTRIBUÉ` présents.
- [ ] Session active : `PROVISIONAL` explicite.
- [ ] Aucune écriture hors du livrable.

## Ressources

- `references/session-e9dd5953-preuves.md` : erreur verbatim, troncature, commandes et comptes de grep, conversion UTC, attribution à 49 ms, edits tardifs, correction d'un dossier livré.
