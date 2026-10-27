---
name: verifier-reparer-ressource-skill
description: "Vérifier une ressource qu'un Skill déclare manquante avant de la recréer : ré-inventorier le disque avec double échantillon size/mtime/SHA-256, exécuter la ressource sur une fixture dont les clés sont copiées de l'artefact réel, imposer une assertion d'extraction positive (extraits = entrées, sans signature = 0), appliquer un correctif minimal en synchronisant code et modèle documentaire, re-prouver en lecture seule sur les données réelles, puis valider et nettoyer les fixtures. Utiliser quand une synthèse antérieure affirme un fichier absent ou un dossier de scripts vide, quand un extracteur renvoie zéro signature sur des données non vides, quand le schéma réel change de noms de clés, ou quand une correction doit être prouvée sans modifier les données. 中文触发：声称文件缺失、资源缺失、重新盘点、并发创建、陈旧结论、脚本为空、参考文件不存在、抽取结果为空、签名为0、真实键名、最小修复、只读复证、夹具清理。Ne remplace pas l'audit de contrat pur, la sécurité d'écriture concurrente, le rejeu de fixtures documentées ni l'acceptation statique."
---

# Vérifier et réparer une ressource déclarée manquante

## Objectif et frontière

Un constat « fichier absent » vieillit vite quand plusieurs sessions travaillent sur le même Skill. Ce Skill impose de re-prouver l'absence sur le disque, puis, si la ressource existe, de l'exécuter sur une fixture dérivée d'un artefact réel et d'exiger une extraction positive avant de conclure quoi que ce soit.

- Ne jamais recréer une ressource sur la foi d'une synthèse, d'un plan ou d'un ticket antérieur.
- Présente : auditer et corriger. Absente après re-inventaire : rapporter, sans substitut silencieux.
- Ne pas modifier les données réelles pour faire passer une assertion.
- Frontières : audit de contrat pur → `audit-skill-tool-contracts` ; écriture concurrente → `skill-update-concurrency-safe` ; rejeu de fixtures déjà documentées → `replay-skill-reference-fixtures` ; acceptation statique → `skill-file-qa`.

## Quand utiliser

- Une synthèse antérieure affirme « fichier absent », « dossier de scripts vide » ou « référence manquante ».
- Un extracteur renvoie zéro signature, zéro ligne ou zéro élément alors que la source est non vide.
- Le schéma réel emploie d'autres noms de clés que ceux codés dans l'outil.
- Une correction doit être prouvée sur les données réelles sans les modifier.
- 中文触发：声称文件缺失、资源缺失、重新盘点、并发创建、陈旧结论、脚本为空、参考文件不存在、抽取结果为空、签名为0、真实键名、最小修复、只读复证、夹具清理。

## Contrat non négociable

1. **Ré-inventorier avant toute recréation.** Le disque et les horodatages décident, pas le rapport précédent. Une ressource écrite après ce rapport invalide la prémisse.
2. **Double échantillon.** Enregistrer size, mtime et SHA-256 deux fois, à au moins deux secondes d'intervalle. Toute différence arrête le travail : reprendre avec `skill-update-concurrency-safe`.
3. **Présente = audit, jamais création.** Ne pas écraser un contenu concurrent ; conserver les ajouts d'autres sessions et ne recréer aucun fichier existant.
4. **Absente après re-inventaire = rapport.** Indiquer le chemin et la déclaration d'origine ; ne pas fabriquer de remplaçant ni écrire « vérifié ».
5. **Fixture dérivée du réel.** Copier les entrées, ou au minimum les noms de clés, d'un artefact réel. Une fixture inventée ne prouve que la cohérence de l'hypothèse avec elle-même.
6. **Porte d'assertion positive.** Exiger extraits = entrées, sans signature = 0 et distribution sommable à la longueur. Un run sans exception n'est pas une preuve.
7. **Correctif minimal et synchrone.** Corriger la couche désignée par la preuve (alias, mapping, modèle documentaire) et répliquer la même règle dans toutes les copies. Ajouter la ligne de piège observée.
8. **Suite complète.** Relancer toutes les assertions, pas un sous-ensemble ; comparer TOTAL, ÉCHECS et le code de sortie avant/après.
9. **Re-preuve en lecture seule.** Repasser l'outil sur les données réelles sans les modifier. Les compteurs sont des observations datées, pas des constantes : un écrivain externe peut les faire dériver.
10. **Accepter, nettoyer, rapporter.** `skill-file-qa` PASS, suppression du seul dossier temporaire créé par cette session, aucun cache, hashes séparés pour `SKILL.md` et les références, niveaux vérifié / inféré / non vérifié.

## Procédure

### 1. Re-inventaire daté

Comparer les mtimes avec la date du rapport qui affirmait l'absence.

```bash
SKILL="$HOME/.qoder/skills/<skill-name>"
find "$SKILL" -type f -printf '%P %s %TY-%Tm-%Td %TH:%TM:%TS\n' | sort
find "$SKILL" -type f -exec sha256sum {} + | sort
sleep 2
find "$SKILL" -type f -printf '%P %s %TY-%Tm-%Td %TH:%TM:%TS\n' | sort
find "$SKILL" -type f -exec sha256sum {} + | sort
grep -n "scripts\|references" "$SKILL/SKILL.md" | head -40
```

Deux échantillons identiques autorisent la suite. Une ressource apparue après le rapport corrige la prémisse : passer à l'audit, pas à la création.

### 2. Sonder le schéma réel

Avant d'écrire une fixture, afficher les clés d'une entrée réelle. Ne jamais les deviner.

```bash
PYTHONIOENCODING=utf-8 py -3 - "<real-artifact.json>" <<'PY'
import json, sys
from pathlib import Path
doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
entries = doc["journal"] if isinstance(doc, dict) else doc
print("longueur", len(entries))
print("cles", list(entries[-1]))
PY
```

Consigner les noms exacts. Un alias absent ici explique souvent une extraction vide.

### 3. Fixture et assertion positive

Construire la fixture dans `.qoder/tmp/reparer-ressource-<UTC>/` et y copier des entrées réelles. Lancer l'outil avec sortie et code de sortie séparés, puis vérifier l'extraction :

```python
import json, sys
snap = json.load(open(sys.argv[1], encoding="utf-8"))
# adapter le chemin au schéma de l'outil
liste = snap["cibles"]["<cible>"]["listes"]["journal"]
assert len(liste["signatures"]) == liste["longueur"], liste
assert liste["sans_signature"] == 0, liste
assert sum(liste["distribution"].values()) == liste["longueur"], liste
print("EXTRACTION_POSITIVE", liste["longueur"], "signatures")
```

- Chaque assertion affiche PASS ou FAIL avec la valeur fautive ; la suite compte TOTAL et ÉCHECS.
- Une assertion négative isolée peut venir de la fixture : vérifier son état avant d'accuser l'outil.
- Une extraction vide sur une source non vide est un défaut, pas une absence de changement.

### 4. Correctif minimal et suite complète

Corriger la couche désignée, puis répliquer la règle partout :

```bash
grep -rn "<cle_reelle>" "$SKILL" --include="*.py" --include="*.md"
PYTHONDONTWRITEBYTECODE=1 find "$SKILL" -name "*.py" -exec py -3 -m py_compile {} +
```

Lancer ensuite la suite entière et exiger zéro échec et code 0. Enregistrer les hashes avant/après ; ne pas élargir le périmètre au-delà du correctif prouvé.

Si le défaut est une cécité d'extraction, prouver la causalité par A/B sur la même fixture : une copie temporaire sans le correctif doit produire l'échec observé, la version corrigée doit localiser les éléments perdus. Les deux versions peuvent finir avec le même code de sortie ; la différence doit porter sur ce qui est détecté.

### 5. Re-preuve réelle et clôture

1. Prendre un instantané de la cible réelle, exécuter l'outil, comparer : la comparaison doit rendre un résultat OK.
2. Noter les compteurs avec l'heure ; préciser que les données réelles peuvent être réécrites par un autre processus.
3. Valider le paquet :

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "$HOME/.qoder/skills/<skill-name>" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" \
  --skills-root "$HOME/.qoder/skills"
```

4. Supprimer uniquement le dossier temporaire de cette session ; vérifier l'absence de cache et de résidu.
5. Enregistrer séparément les hashes de `SKILL.md` et des références : le PASS du validateur ne couvre que `SKILL.md`.

## Décision

| Situation | Action |
|---|---|
| Absente au premier constat, présente au re-inventaire | Corriger la prémisse, auditer, ne pas créer ; noter mtime et hash |
| Fichiers différents entre les deux échantillons | Arrêter ; reprendre avec `skill-update-concurrency-safe` |
| Ressource présente mais l'outil ne démarre pas | Audit de contrat ; pas de fixture |
| Fixture verte, extraction vide | Défaut réel ; interdire la conclusion « aucun changement » |
| Une assertion négative isolée | Vérifier l'état de la fixture avant d'accuser l'outil |
| Défaut confirmé | Correctif minimal, synchronisation documentaire, suite complète |
| Seule la documentation dérive | Corriger la documentation ; ne pas toucher au code |
| Données réelles qui bougent pendant la preuve | Rapporter l'observation datée, sans constante |
| Toujours absente après double inventaire | Rapporter ; aucun remplaçant silencieux ; pas de « vérifié » |

## Rapport

- Ouvrir par « prémisse corrigée » quand c'est le cas : ancien constat, mtime et hash qui le contredisent.
- Trois niveaux : vérifié (sortie, code de sortie, hash), inféré (mtimes cohérents sans auteur identifié), non vérifié (non exécuté ou environnement absent).
- Ne jamais écrire « corrigé » ou « validé » sans la sortie qui le prouve.

## Cas vérifié

Le 2026-10-26, la cible était `verifier-effets-de-bord-verification-lecture-seule`. Détail et preuves dans `references/cas-ressource-manquante-2026-10-26.md`.

1. La demande « répare les fichiers manquants » reposait sur un constat périmé : les deux fichiers étaient sur le disque, écrits à 13:19 (+01:00), et le `SKILL.md` avait été réécrit à 13:29. Aucun fichier n'a été recréé.
2. Double échantillon identique avant édition : script 29 725 B (`be2b86b4…`), protocole 15 240 B (`fc2618d6…`).
3. La suite de fixtures a échoué uniquement sur l'extraction vide (`signatures: {}`, `sans_signature: 100`), pas sur des défauts indépendants.
4. Cause : alias incomplets ; le journal réel utilise `horodatage_iso` et `chemin_fichier`.
5. Après correctif d'alias dans le script et dans le modèle de la référence, la suite complète est repassée à zéro échec et code 0.
6. Re-preuve en lecture seule : toutes les entrées (100) ont une signature, aucune sans signature ; la comparaison a rendu un résultat OK ; `skill-file-qa` PASS ; fixtures supprimées, aucun cache.
7. Un contrôle A/B sur la même fixture a reproduit l'échec avec une copie sans les alias et a localisé les entrées évincées avec la version corrigée.
8. Limite : les données réelles étaient encore réécrites par un processus externe ; les compteurs sont des observations datées.

## Ressources

- `references/cas-ressource-manquante-2026-10-26.md` : chronologie, sorties verbatim, hashes complets, niveaux de preuve et état disque actuel.
- `audit-skill-tool-contracts` : contrat d'un outil avant de s'y fier.
- `skill-update-concurrency-safe` : double échantillon et écriture sans écrasement.
- `replay-skill-reference-fixtures` : rejeu d'une fixture déjà documentée.
- `skill-file-qa` : acceptation statique après écriture.
