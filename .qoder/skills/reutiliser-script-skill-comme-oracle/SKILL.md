---
name: reutiliser-script-skill-comme-oracle
description: "Réutiliser le script d'un Skill installé (validateur, générateur, collecteur) comme oracle sans laisser de résidu : auditer d'abord son contrat réel, l'importer via importlib avec `sys.dont_write_bytecode = True` avant l'exécution du module cible (ou `py -3 -B`), asserter la parité entre une collecte recopiée et la fonction de l'oracle avec rc 2 en cas de divergence, prendre un instantané des `__pycache__` et `.pyc` avant et après, ne supprimer que les caches nouveaux (chemin absent avant, horodatage postérieur au départ), rejouer pour prouver l'absence de recréation, et reproduire par fixture A/B toute conclusion seulement déduite quand l'échec n'a jamais été observé. Utiliser avant de recopier les regex d'un autre Skill, après l'apparition d'un cache chez un Skill tiers, ou quand un FAIL rapporté n'a pas été observé. 中文触发：把已安装 Skill 的脚本当 oracle 复用、importlib 导入产生 __pycache__、sys.dont_write_bytecode、与校验器函数断言一致性、缓存残留证明、A/B 夹具复现未观测失败。"
---

# Réutiliser le script d'un Skill installé comme oracle

## Portée

Utiliser un script déjà installé — validateur, générateur, collecteur — comme référence exécutable : importer ses fonctions plutôt que recopier ses expressions régulières, puis prouver que ce réemploi ne laisse aucun cache Python chez le Skill dépendant.

Ce Skill ne remplace pas :

| Besoin | Skill |
| :--- | :--- |
| Auditer le contrat du script avant de promettre son réemploi | `audit-skill-tool-contracts` |
| Savoir si le comportement observé vient du HEAD ou du worktree | `qualify-dependency-behavior-provenance` |
| Import sûr d'un module projet (dataclasses, `sys.modules`) | `auditer-livraison-skill-module-projet` |
| Retirer un cache après coup, auditer l'intégrité du paquet | `skill-package-integrity-audit` |
| Effets de bord autres que les caches (journaux, index, sceaux) | `verifier-effets-de-bord-verification-lecture-seule` |
| Validation statique finale du paquet | `skill-file-qa` |

## Invariants

1. **La garde précède l'exécution du script dépendant.** `sys.dont_write_bytecode = True` doit être posé avant `exec_module` du module cible. Posée après, elle n'a aucun effet : le cache est déjà écrit.
2. **Deux mécanismes, pas un.** La garde couvre le module importé ; `py -3 -B` couvre aussi les interpréteurs enfants. Garder les deux.
3. **Un cache préexistant n'est pas à nous.** Seul un fichier absent avant l'exécution, sous `__pycache__`, avec un horodatage postérieur au départ, peut être supprimé.
4. **La parité se prouve.** Une logique recopiée de l'oracle est comparée à la fonction de l'oracle ; toute divergence est une erreur d'environnement (rc 2), pas un échec de contenu.
5. **Le réemploi n'est pas « lecture seule » par décret.** Instantané avant, exécution, instantané après. Un `RESULT PASS` sans instantané ne prouve rien sur les écritures.
6. **Une conclusion non observée se reproduit.** « Aurait produit un FAIL » ne s'écrit pas ; on construit la fixture qui le produit et on cite sa sortie.
7. **L'oracle installé fait foi.** Ne pas recopier ses regex ni ses seuils : les importer, et refuser en rc 2 si l'API attendue manque.

## 1. Auditer le contrat de l'oracle

Avant toute promesse de réemploi : le fichier existe, l'API attendue est là, la forme d'entrée correspond, le code de retour et l'encodage de sortie sont utilisables. Consigner l'empreinte du script utilisé — taille, SHA-256 — car les conclusions valent pour cette empreinte. La méthode d'audit et la provenance HEAD ou worktree sont dans `audit-skill-tool-contracts` et `qualify-dependency-behavior-provenance`.

## 2. Importer sans bytecode

**Import de fonctions**, le mode le plus utile : aucune duplication de regex, donc aucune dérive.

```python
import importlib.util
import sys
from pathlib import Path

sys.dont_write_bytecode = True

REQUIRED_API = ("normalize_ref", "collect_refs")

spec = importlib.util.spec_from_file_location("oracle_dep", Path(sys.argv[1]))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
missing = [name for name in REQUIRED_API if not hasattr(module, name)]
if missing:
    raise SystemExit(f"API changed, missing: {', '.join(missing)}")
```

Un nom de module unique évite de masquer une installation réelle. Pour un module à `dataclasses`, enregistrer l'entrée `sys.modules` avant `exec_module` : voir `auditer-livraison-skill-module-projet`.

**Exécution en sous-processus** : lancer l'oracle par `py -3 -B` et mesurer les caches avec le harnais. C'est le mode à retenir quand l'oracle n'expose que des fonctions internes ou une CLI.

## 3. Asserter la parité

Si une partie de la collecte est recopiée — par exemple pour classer des jetons que l'oracle ignore en silence — comparer l'ensemble obtenu à celui de l'oracle sur le même texte :

```python
expected = set(module.collect_refs(text))
if set(counted) != expected:
    raise RuntimeError(
        f"contract mismatch: extra={sorted(set(counted) - expected)} "
        f"absent={sorted(expected - set(counted))}"
    )
```

Traduire cette erreur en rc 2 : l'outil ne peut pas répondre, il ne dit pas que le paquet est mauvais. La branche ne se déclenche jamais tant que l'oracle est inchangé ; elle se déclenche à sa mise à jour, ce qui est exactement son rôle.

La parité est sans objet quand aucune logique n'est recopiée : appeler les fonctions de l'oracle suffit, et vaut mieux qu'une comparaison.

## 4. Prouver zéro nouveau résidu

Le harnais prend un instantané des `__pycache__` et des `.pyc` sous le Skill dépendant, exécute la commande, compare, puis peut nettoyer et rejouer.

```bash
py -3 "$HOME/.qoder/skills/reutiliser-script-skill-comme-oracle/scripts/oracle_sans_residu.py" \
  --dependance "<dossier-skill-dependant>" --nettoyer --rejouer \
  -- py -3 "<script-consommateur>" "<argument>"
```

Tout ce qui suit `--` est la commande oracle, sans réinterprétation par le harnais.

| Sortie | Sens |
| :--- | :--- |
| `AVANT files=N dirs=N` | base de comparaison ; attendu `0` sur un Skill propre |
| `NEW …` / `NEW_DIR …` | cache créé par cette exécution |
| `REMOVED …` / `REMOVED_DIR …` | supprimés, car nouveaux et horodatés après le départ |
| `KEPT_DIR …` | dossier non vide : un cache préexistant y demeure |
| `PROOF=NO_RECREATION` | le rejeu n'a rien recréé : la garde fonctionne |
| `PROOF=RECREATED` | le rejeu recrée le cache : le consommateur n'a pas de garde |
| `NEW_RESIDUE=NONE` | aucun nouveau cache à la fin |
| rc 2 | usage ou environnement ; rien n'a été observé |

Sans `--rejouer`, le harnais constate mais ne prouve pas la garde. Il refuse en rc 2 si `PYTHONDONTWRITEBYTECODE` est hérité : l'observation serait vide et un PASS ne prouverait rien.

Un cache antérieur n'est jamais attribué à la session : depuis un dossier déjà pollué, `--nettoyer` ne supprime rien et affiche `NEW (none)`. Partir d'une base propre.

## 5. Reproduire une conclusion déduite

Une conclusion non observée dans la source se transforme en fixture, hors de toute racine de Skills :

1. Copier l'oracle, jamais modifier l'original.
2. Construire le cas positif et le cas négatif, avec la mutation réellement appliquée et vérifiée.
3. Exécuter l'oracle et le consommateur sur la même fixture, relever les deux codes de retour.
4. Consigner la sortie littérale, puis purger la fixture.
5. Si les deux outils ne s'accordent pas, c'est une divergence à expliquer, pas un résultat.

## Pièges vérifiés

| Symptôme | Cause | Correctif |
| :--- | :--- | :--- |
| `__pycache__` malgré la garde | garde posée après `exec_module`, ou seulement dans un interpréteur enfant | garde en tête de fichier, plus `py -3 -B` |
| `PROOF=NO_RECREATION` avec un cache présent | base de départ déjà polluée, cache non attribuable | partir d'une base propre ; le harnais ne retire pas l'ancien |
| observation vide, PASS suspect | `PYTHONDONTWRITEBYTECODE` hérité | désactiver la variable ; le harnais refuse en rc 2 |
| empreinte du `.pyc` différente entre deux fixtures | le chemin source est encodé dans le code | détecter par chemin, pas par empreinte du cache |
| FAIL du consommateur non reproduit | conclusion déduite, jamais observée | fixture A/B, sortie citée |
| rc 1 confondu avec rc 2 | échec de contenu et erreur d'environnement mélangés | rc 2 = outil incapable de répondre (API, divergence, variable) |
| `python` renvoie le code 49 | alias Microsoft Store | `py -3` |
| traceback illisible sur console cp1252 | sortie brute non échappée | échappement ASCII ligne par ligne |

## Critères de sortie

- Le script oracle existe, son empreinte est relevée, l'API attendue est présente.
- `ORACLE_RC=0` pour le consommateur.
- `PROOF=NO_RECREATION` et `NEW_RESIDUE=NONE` sur une base propre.
- La parité est soit sans objet, soit vérifiée sur fixtures.
- Chaque conclusion déduite est accompagnée de la fixture qui la reproduit et de sa sortie.
- L'empreinte du script oracle est inchangée entre le début et la fin.
- Les fixtures sont hors des racines de Skills et purgées.

## Ressources

- `scripts/oracle_sans_residu.py` : instantané, nettoyage attribué, rejeu, rc 0/1/2.
- `references/cas-qualifier-validateur-2026-10-28.md` : cas daté, sorties réelles, statut de chaque affirmation.
