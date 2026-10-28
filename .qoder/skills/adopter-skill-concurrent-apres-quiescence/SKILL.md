---
name: adopter-skill-concurrent-apres-quiescence
description: "Après quiescence d'un Skill livré par une autre session, recomputer les affirmations de son dossier de preuves depuis les artefacts bruts : reconstruire le script de l'auteur depuis les Write/Edit du JSONL et compter les points d'appel, compter une chaîne au caractère près (0 = ABSENT, puis timestamp réel), distinguer message humain, tool_result, injection et invite de continuation, confronter le bloc de sortie documenté au stdout réel. Classer SUPPORTED/CONTRADICTED/ABSENT/UNVERIFIABLE, sauvegarder hors paquet, éditer au minimum, dater la correction avec provenance, synchroniser SKILL.md et references, rejouer auto-test lié au hash, QA et fixtures hors paquet. 用于交付后复核证据计数、调用点数量、时刻零出现、输出示例缺行、QA PASS 但散文不实、摘要高报次数。Triggers: post-quiescence, JSONL re-derivation, Write/Edit reconstruction, call-site recount, exact-string occurrence, actual timestamp. 不替代 audit-skill-during-live-creation、adopt-concurrent-duplicate-skill、verifier-contrat-skill-adopte、completer-skill-concurrent-delta、reparer-contrat-sortie-skill。"
---

# Adopter un Skill concurrent après quiescence

## Objectif et périmètre

Un autre agent a livré un paquet : `skill-file-qa` est `PASS`, le dossier de preuves cite des chiffres, des heures et des sorties. La QA ne lit pas la prose et ne compare pas les références au JSONL. Ce Skill couvre un seul geste : **après quiescence, recomputer les affirmations du dossier de preuves depuis les artefacts bruts, puis corriger au minimum avec provenance**.

Ce Skill ne refait pas :

| Besoin | Skill |
|---|---|
| Attente, trois états, attribution des écritures | `audit-skill-during-live-creation` |
| Décision de reprendre, réduire ou conserver | `adopt-concurrent-duplicate-skill` |
| Acceptation en lecture seule, relecture de contrat | `verifier-contrat-skill-adopte` |
| Delta venu de tours postérieurs à la lecture de l'auteur | `completer-skill-concurrent-delta` |
| Réparation du contrat de sortie documenté | `reparer-contrat-sortie-skill` |
| Rejeu des fixtures du paquet | `replay-skill-reference-fixtures` |
| Fraîcheur par empreintes seulement | `verifier-fraicheur-preuves-skill` |
| Validation statique | `skill-file-qa` |

## Quand utiliser

- un paquet a été produit par une autre session et son dossier de preuves contient des compteurs, des heures ou des sorties « mesurées » ;
- la QA est `PASS` mais une affirmation ne se retrouve pas dans le JSONL cité ;
- un compteur d'appels ou de fichiers semble repris d'un résumé plutôt que recalculé ;
- une heure citée n'existe nulle part, ou seulement dans un autre fichier ;
- un bloc « sortie de succès » ne correspond pas au stdout conservé ;
- un résumé de session dit « N fois » ou « final » et la mesure dit autre chose.

Ne pas utiliser si l'écrivain peut encore écrire, s'il faut décider du sort du paquet, ou s'il suffit de vérifier des empreintes : déléguer d'abord.

## Contrat non négociable

1. **QUIESCENT d'abord.** Aucune écriture avant `ready` + `activeTurnId: null` et des échantillons complets identiques, ou `cold` et trois échantillons. La preuve et la gradation restent dans `audit-skill-during-live-creation` ; ce Skill les exige, il ne les rejoue pas.
2. **QA PASS ne prouve pas la prose.** `RESULT PASS` couvre structure, frontmatter, références et empreinte de `SKILL.md`. Il ne compare ni les chiffres, ni les heures, ni les blocs de sortie au JSONL.
3. **Un chiffre, une source, un sujet.** Chaque ligne du registre nomme `sessionId` + `revision` + définition (points d'appel, occurrences, messages humains, octets). « 23 appels » sans sujet est incomplet.
4. **Re-dériver avant de corriger.** On recalcule d'abord ; on décide ensuite si le défaut est dans le document ou dans l'implémentation. Un écart de mesure n'autorise pas à réécrire le script de l'auteur.
5. **La chaîne zéro ne vaut que dans le JSONL cité.** Deux JSONL peuvent contenir la même chaîne : 0 exemplaire dans celui que l'affirmation cite, 37 dans celui qui la discute. Compter dans le fichier de la session citée.
6. **Zéro = ABSENT, puis prendre l'heure réelle.** Une heure absente ne se « corrige » pas par une heure voisine : on lit le `timestamp` de l'enregistrement qui porte le fait.
7. **Reconstruire avant de compter.** Le script de l'auteur se relit depuis ses `Write` puis ses `Edit`, dans l'ordre ; chaque `old_string` doit exister exactement une fois ; on compte les occurrences, on soustrait les définitions.
8. **L'historique est append-only.** On conserve l'affirmation fausse, la valeur mesurée et la correction dans une section datée ; on ne réécrit pas le récit.
9. **Sauvegarde hors paquet, Edit minimal, contrôle après chaque écriture.** `old_string` unique, un sujet logique par Edit, empreinte après chaque Edit ; `The file changed since your last read` = arrêt.
10. **Auto-test lié au hash.** Un `SELFTEST 10/10` ne vaut que pour le hash du fichier exécuté. Si le script n'a pas changé, l'exécution antérieure reste valable : écrire l'heure et le hash, pas « rejoué à la fin ».
11. **Pas de FINAL sans rejeu.** Le paquet cible est revalidé sur ses propres contrôles, `skill-file-qa` et des fixtures hors paquet ; sinon rapport `PROVISIONAL`.

## Étape 0 — Porte d'entrée

- Confirmer QUIESCENT (déléguer la preuve), puis figer : liste des fichiers, taille, `mtime_ns`, SHA-256, `Files (N)` de la QA.
- Lire intégralement `SKILL.md`, les références et les scripts du paquet livré.
- Relever les affirmations candidates : chiffres, heures, « mesuré », « final », blocs de sortie, nombres de messages.

## Étape 1 — Registre d'affirmations

| Champ | Valeur |
|---|---|
| `ID` | A1, A2… |
| `EMPLACEMENT` | `references/<fichier>:<ligne>` ou `SKILL.md:<ligne>` |
| `TEXTE` | citation exacte, sans reformulation |
| `SUJET` | `sessionId` + `revision` + définition du champ |
| `SOURCE` | chemin du JSONL ou sortie d'outil conservée |
| `RE-DÉRIVATION` | commande ou extrait exact |
| `VERDICT` | SUPPORTED / CONTRADICTED / ABSENT / UNVERIFIABLE |
| `CORRECTION` | phrase exacte, ou « aucune » |

Règles : une affirmation par ligne ; `UNVERIFIABLE` n'est pas `SUPPORTED` ; `CONFLICT` (deux règles incompatibles) se présente à l'utilisateur, on ne tranche pas seul.

## Étape 2 — Re-dériver depuis les artefacts

### 2.1 Reconstruire le script de l'auteur

Collecter dans le JSONL les `tool_use` `Write`/`Edit` du fichier, dans l'ordre des enregistrements, appliquer les contenus, puis compter.

```python
import json

ops = []
for line in open(jsonl, encoding="utf-8"):
    rec = json.loads(line)
    for block in (rec.get("message") or {}).get("content") or []:
        if block.get("type") == "tool_use" and block.get("name") in ("Write", "Edit"):
            inp = block.get("input") or {}
            if str(inp.get("file_path", "")).endswith("simulate.py"):
                ops.append((rec.get("timestamp"), block["name"], inp))

text = ""
for ts, name, inp in ops:
    if name == "Write":
        text = inp["content"]
    else:
        assert text.count(inp["old_string"]) == 1, ts
        text = text.replace(inp["old_string"], inp["new_string"], 1)

print(text.count("sub1("), text.count("def sub1"))
```

Mesure du cas vérifié : 1 `Write` + 2 `Edit` donnent 24 occurrences de `sub1(` moins 1 définition, soit **23 appels**. Le document disait 25. Compter `sub1(` dans le JSONL entier donnait 27, mentions en prose comprises : il faut reconstruire le fichier.

### 2.2 Compter une chaîne au caractère près

```python
raw = open(jsonl, encoding="utf-8", errors="replace").read()
print(raw.count("00:32:11"), raw.count("00:32:16.728"))
```

Mesure : `0` et `1` dans le JSONL de la session citée. La même chaîne apparaît 37 fois dans un autre JSONL qui cite le document fautif. Ne jamais conclure depuis un autre fichier que celui cité.

### 2.3 Classer les enregistrements

- **message humain** : `role: user`, contenu qui n'est ni `[tool_result]`, ni une injection de Skill (`# Skill Creator`, `Base directory for this skill:`), ni une invite de continuation (`This session is being continued…`) ;
- **tool_result** : résultat d'outil, compté à part ;
- **invite de continuation** : comptée à part, ce n'est pas un tour humain.

Le cas vérifié contient 2 tours humains réels, 1 invite de continuation et 2 injections, et non « 2 messages » sans définition.

### 2.4 Confronter le bloc de sortie

Comparer le bloc documenté au stdout conservé, ligne par ligne. Mesure : le bloc omettait `SPEC edits=` et `H2`, présents dans le stdout. La réparation du contrat de sortie elle-même reste dans `reparer-contrat-sortie-skill`.

## Étape 3 — Correction minimale avec provenance

1. Sauvegarde hors du paquet ; empreinte de la sauvegarde.
2. Un `Edit` par affirmation : `references/` puis `SKILL.md` avec la même phrase.
3. Ajouter une section datée `## N. Recontrôle indépendant et corrections (AAAA-MM-JJ)` qui garde l'ancienne valeur, la nouvelle et la méthode.
4. Ne pas renommer, renuméroter ni « nettoyer » les sections de l'auteur.
5. Empreinte après chaque Edit ; toute dérive impose l'arrêt et la relecture.

## Étape 4 — Revalidation

1. Auto-test du paquet cible : exiger `SELFTEST 10/10` ou l'équivalent, `RC=0`, et associer le résultat au SHA-256 du script exécuté.
2. `skill-file-qa` sur le paquet : `RESULT PASS`, `Files (N)` attendu, description et corps inchangés hors correction.
3. Fixtures hors paquet : positif, ancre absente, CRLF+BOM ; vérifier que les sources n'ont pas bougé.
4. Empreintes séparées pour `SKILL.md`, les références et les scripts, caches supprimés, aucun `__pycache__`.
5. Ne pas revendiquer de rechargement ; un Skill modifié peut nécessiter `/skills reload`.

## Modèle de rapport

```text
Mode: EVIDENCE-ADJUDICATION (post-quiescence)
Paquet: <chemin> ; quiescence: <preuve> ; Files (N): <n>
Registre: SUPPORTED <n> / CONTRADICTED <n> / ABSENT <n> / UNVERIFIABLE <n>
Corrections: <fichier:ligne, avant -> après>
Auto-test: <sortie> ; script SHA-256: <hash> ; exécuté à <heure>
QA: <PASS/FAIL>, Files (N), description <n>, corps <n>
Fixtures: <positif / ancre absente / CRLF+BOM> -> <résultat>
Empreintes finales: SKILL.md <sha> ; references <sha> ; scripts <sha>
Non vérifié: <branches>
```

## Diagnostic

| Symptôme | Cause | Action |
|---|---|---|
| QA PASS, chiffre faux | le validateur ne lit pas la prose | re-dériver ; ne pas rejouer la QA en espérant |
| Compteur d'appels supérieur | repris d'un résumé | reconstruire `Write`+`Edit`, soustraire les définitions |
| Heure introuvable | mauvais JSONL ou heure inventée | compter dans la session citée, puis lire le `timestamp` |
| Résumé « N fois timeout » | agrégat approximatif | compter les `outcome` réels |
| Bloc de sortie incomplet | exemple réécrit à la main | diff ligne à ligne avec le stdout |
| `SELFTEST` cité comme final | exécution antérieure | lier sortie, heure et hash ; si le hash est inchangé, le dire |
| `UnicodeEncodeError` cp1252 | console Windows | `PYTHONIOENCODING=utf-8` |
| JSONL illisible en un appel | sortie supérieure à environ 25k tokens | lire le fichier déposé dans le répertoire temporaire |
| `Edit` à 0 occurrence | texte déjà corrigé | relire et vérifier `ALREADY_FIXED` avant de réessayer |

## Liste de contrôle

- [ ] quiescence prouvée, aucun écrivain actif
- [ ] registre complet, chaque ligne avec sujet et source
- [ ] zéro-occurrence comptée dans le JSONL cité
- [ ] script reconstruit, `assert count == 1` par Edit
- [ ] sauvegarde hors paquet
- [ ] un Edit par affirmation, empreinte après chaque Edit
- [ ] section datée, historique conservé
- [ ] `SKILL.md` et `references` synchronisés
- [ ] auto-test lié au hash, QA PASS, fixtures rejouées
- [ ] empreintes séparées, caches absents

## Cas vérifié (2026-10-28)

Le paquet `appliquer-lot-edits-skill-script-assertions`, livré par la session `e22fe088` après 7 attentes, avait une QA `10 pass / 0 fail / 0 warn` et trois défauts de prose : 25 au lieu de 23 appels, une heure absente, un bloc de sortie à deux lignes manquantes. Après correction : QA `10 pass / 0 fail / 0 warn`, `Files (3)`, `SKILL.md` 12 924 B, SHA-256 `ecaaf59b…`. Détails et bornes : `references/cas-2026-10-28.md`.

## Ressources

- `references/cas-2026-10-28.md` — chronologie, 7 attentes, empreintes, mesures, écarts et provenance.
