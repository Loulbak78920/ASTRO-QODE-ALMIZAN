---
name: reconcilier-commande-non-enregistree-session
description: "Réconcilier une commande qui semble absente d'une session Qoder avant de la traiter comme non exécutée : un motif à 0 occurrence dans le dump read_chat_session ne prouve rien, car ce canal ne transporte que les noms, statuts et sorties d'outils, jamais les entrées. Compter séparément dump, tool_use.input, tool_result et prose, relire l'entrée complète dans le JSONL par tool_use id, reconstruire le numéro de ligne <stdin> d'un script heredoc et l'aligner sur les tracebacks. Sans JSONL, lire l'empreinte de sortie — frame stdlib contre frame nue, [Errno 13] Permission denied contre [WinError 5] Accès refusé, décalage de lignes entre deux tours — et classer INFÉRÉ, jamais ABSENT ni REPRODUIT. Ne promouvoir en REPRODUIT que par une fixture %TEMP% hors installation, qui prouve le mécanisme et non l'exécution ; déléguer l'ACL à diagnostiquer-verrou-acl-windows. 关键词：命令未记录、read_chat_session、JSONL、tool_use input、0 occurrence、traceback 行号、证据分级。"
---

# Réconcilier une commande non enregistrée

## Vue d'ensemble

Un motif absent du dump de session n'est pas une commande non exécutée : `read_chat_session` ne transporte pas les entrées d'outils. Ce Skill compte chaque canal séparément, relit l'appel réel dans le JSONL, reconstruit le numéro de ligne `<stdin>` d'un script heredoc et aligne les tracebacks sur la version du script qui a tourné.

## Déclencheurs

- `grep` d'une commande (`chmod`, `icacls`, `rm`, `curl`…) rend **0** dans le dump, alors qu'une sortie d'outil suppose son exécution.
- Un audit conclut « la recommandation est fausse » ou « l'agent a menti » à partir d'un comptage 0.
- Un traceback est cité sans que la commande qui l'a produit soit visible.
- Deux rendus de la même erreur coexistent : `[Errno 13] Permission denied` et `[WinError 5] Accès refusé`.
- Une affirmation doit passer de « inférée » à « vérifiée » sans changer de preuve.

## 1. Trois canaux, trois portées

| Canal | Contenu | Ce qu'un 0 y prouve |
| :--- | :--- | :--- |
| `read_chat_session` (MCP) | messages, et un tableau `tools[]` de `{name, status, output}` | rien sur les commandes : les entrées n'y sont pas |
| `<sessionId>.jsonl` | `tool_use {name, input}`, `tool_result`, `toolUseResult`, messages | absence réelle dans les entrées enregistrées |
| `.qoder/tmp/<slug>/<sessionId>/tool-results/*.txt` | sorties longues complètes | rien sur les entrées |

Les messages d'assistant contiennent aussi le motif (narration, bilan) : un comptage global sur le JSONL mélange prose et entrées et ne vaut pas mieux qu'un `grep` sur le dump. Compter par canal.

Un `tool_use.input` porte lui aussi de la prose : `content` d'un `Write`, `old_string`/`new_string` d'un `Edit`, champs `description`. Un comptage brut y attrape du texte rédigé ; seule la lecture de `command` identifie une commande. Cas mesuré : `attrib` rend 11 occurrences dans les entrées pour **une seule** commande exécutée.

Avant toute conclusion, appliquer la règle de `extraire-preuves-session-qoder` §1 : l'absence dans le snapshot est une lacune, pas une preuve d'absence.

## 2. Compter par canal

Depuis le dossier de ce Skill, lecture seule :

```bash
py -3 -B scripts/reconcilier_commande.py CHEMIN_JSONL --pattern "os.chmod" --dump CHEMIN_DUMP
```

Sortie stable, ASCII : `DUMP … count=N`, `INPUT_OCCURRENCES`, `CALLS_WITH`, `RESULT_OCCURRENCES`, puis une ligne `CALL` par appel contenant le motif, une ligne `TRACEBACK` par traceback, une ligne `PAIR` par traceback `<stdin>` apparié à son appel, et `VERDICT INPUT_RECORDED` (rc 0) ou `NOT_IN_INPUTS` (rc 10). `ERROR` + rc 2 pour un argument ou un fichier invalide. `--json` émet les mêmes champs plus les empreintes.

`CALL … stdin_lines=33,38` donne la position dans le corps heredoc, numérotée comme Python voit `<stdin>` ; `NA` pour un `py -c` (pas de fichier stdin reconstituable). `PAIR … statement=…` affiche la ligne du script **tel qu'exécuté** : c'est la pièce qui relie un traceback à une version précise du code. `pattern=miss` sur un `PAIR` signale le plus souvent une version antérieure du script, ou un autre heredoc du même appel — vérifier le décalage et le contexte, pas l'absence.

`CHEMIN_JSONL` désigne le JSONL de la session, `CHEMIN_DUMP` la sortie archivée de `read_chat_session`. Sans dump, omettre `--dump` : les comptages d'entrées et la réconciliation des lignes restent valables.

Relever avant et après : octets, mtime et SHA-256 du JSONL et du dump. Le script ne modifie rien.

## 3. Relire l'appel

Lire `input.command` en entier pour l'`id` relevé : ne jamais citer un résumé tronqué. Pour l'appariement `tool_use`/`tool_result`, les clés complètes d'un `Edit` et les angles morts de `--grep`, utiliser `extraire-preuves-session-qoder`.

Un motif cherché dans un résultat tronqué ne prouve rien non plus : relire le fichier `tool-results/` complet quand la sortie porte `OUTPUT TRUNCATED`.

## 4. Sans JSONL : empreinte de sortie

Quand l'entrée n'est plus disponible, trois indices concordants autorisent une inférence — jamais un constat :

| Indice | Lecture |
| :--- | :--- |
| forme du traceback | frames stdlib (`pathlib`, `shutil`) ⇒ appel médié par une API ; frame **nue** à `<stdin>` ⇒ appel direct, souvent `os.chmod`, `os.remove`, `os.rename` |
| rendu de l'erreur | `[Errno 13] Permission denied` = errno formaté par Python, `winerror` absent ; `[WinError 5] Accès refusé` = message de l'OS transmis tel quel, `winerror=5` |
| lignes entre tours | mêmes scripts recopiés de tour en tour : la ligne citée se décale des lignes insérées ; reconstruire chaque version avant d'attribuer |

Classer **INFÉRÉ**, y compris quand les trois indices concordent. Une fixture peut ensuite promouvoir le **mécanisme** en REPRODUIT ; elle ne prouve pas que cette commande a tourné.

Les accents des sorties enregistrées peuvent être déjà corrompus (`U+FFFD`, `?`) par la console : chercher des fragments ASCII (`WinError 5`), jamais la fin accentuée du message.

## 5. Ce qu'une fixture achète

- Hors installation, sous `%TEMP%`, propriétaire = compte courant ; jamais sur le chemin de production.
- Reproduire le refus, mesurer `errno`/`winerror`, puis **nettoyer dans l'ordre** : retirer l'ACE, remettre l'attribut inscriptible, supprimer le dossier.
- Pour un verrou ACL, suivre `diagnostiquer-verrou-acl-windows` : son dossier de preuves contient les résultats mesurés (attribut `R` seul corrigé par `chmod`, `chmod` refusé sous `DENY`, `attrib -R` sortant rc 0 sans effet, `rmtree` en `WinError 5` tant que `R` reste posé). Ne pas recréer une fixture avec `WDAC`/`WO` : l'indélébilité n'est qu'inférée, pas mesurée ici.

## 6. Statuts de preuve

| Statut | Condition |
| :--- | :--- |
| VÉRIFIÉ | `tool_use.input` lu dans le JSONL, avec ligne et SHA-256 du fichier |
| REPRODUIT | mécanisme obtenu en fixture, dans le même environnement |
| INFÉRÉ | empreinte de sortie seulement (§4) |
| ABSENT | motif cherché dans les trois canaux, 0 partout — y compris dans les entrées |
| NON VÉRIFIÉ | ni entrée, ni fixture, ni empreinte exploitable |

Formuler la limite à côté de la preuve : « entrée lue dans le JSONL ligne N (SHA-256 …) ; absente en tant que commande du dump `read_chat_session` ». Ne jamais présenter une commande reconstruite comme une citation du dump.

## 7. Anti-patrons

| Geste | Pourquoi il échoue |
| :--- | :--- |
| conclure « jamais exécuté » depuis un `grep` 0 sur le dump | le canal ne porte pas les entrées |
| compter sur le JSONL entier sans séparer prose et entrées | la narration cite la commande qu'elle décrit |
| citer une commande reconstruite entre guillemets de citation | fabrique une preuve qui n'existe pas |
| promouvoir INFÉRÉ → REPRODUIT par une fixture | la fixture prouve le mécanisme, pas l'exécution |
| attribuer un traceback à la version courante du script | le numéro de ligne a bougé entre les tours |
| conclure depuis une sortie `OUTPUT TRUNCATED` | le fichier `tool-results/` complet peut contenir le motif |
| fixture `DENY` incluant `WDAC`/`WO` | nettoyage impossible sans `takeown` |

## 8. Vérification

```bash
py -3 -B scripts/reconcilier_commande.py CHEMIN_JSONL --pattern "os.chmod" --dump CHEMIN_DUMP
```

Attendu sur la session de référence (JSONL 2 151 156 octets, 595 lignes) :

```text
DUMP … count=0
INPUT_OCCURRENCES 2 CALLS_WITH 1
CALL line=358 tool=Bash … stdin_lines=33,38 occurrences=2
TRACEBACK result_line=349 … stdin_line=32 frames=stdlib error=PermissionError: [Errno 13] …
TRACEBACK result_line=360 … stdin_line=33 frames=none error=PermissionError: [WinError 5] …
PAIR result_line=349 call_line=347 stdin_line=32 pattern=miss statement=p.write_bytes(new.encode("utf-8"))
PAIR result_line=360 call_line=358 stdin_line=33 pattern=hit statement=os.chmod(p, stat.S_IWRITE)
VERDICT INPUT_RECORDED
```

Attendu en contrôle inverse, `--pattern "takeown"` : `count=2` dans le dump, `INPUT_OCCURRENCES 0`, `VERDICT NOT_IN_INPUTS`, rc 10. Un motif inconnu rend le même verdict sans ligne `CALL`.

Le bloc ci-dessus est un extrait : le script émet aussi les `TRACEBACK` 339, 378 et 384 (plus 438, `kind=string`) et les `PAIR` 339, 378 et 384, qui ne portent pas le motif. La référence les liste tous — ne pas conclure à une dérive devant ces lignes supplémentaires.

## Ressources

- [scripts/reconcilier_commande.py](scripts/reconcilier_commande.py) — comptage par canal, reconstruction `<stdin>`, appariement traceback/appel, rc 0/10/2.
- [references/cas-commande-chmod-2026-10-28.md](references/cas-commande-chmod-2026-10-28.md) — preuves verbatim, comptages comparés, réconciliation des lignes et limites.
- Skills voisins : `extraire-preuves-session-qoder` (extraction, appariement, troncature), `diagnostiquer-verrou-acl-windows` (mécanique ACL et fixture).
