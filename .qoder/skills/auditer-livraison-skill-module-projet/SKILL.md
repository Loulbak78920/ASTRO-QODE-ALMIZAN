---
name: auditer-livraison-skill-module-projet
description: "Écrire, prouver et empaqueter un audit de livraison en lecture seule pour un module Python de projet livré avec un Skill : contrat de sortie ASCII et codes 0/1/2, import sûr d'un module à dataclasses via importlib avec enregistrement sys.modules, preuve de non-écriture par instantané __pycache__, contrôles d'artefacts et d'empreintes SHA-256, fixtures racine réelle, copie falsifiée et racine absente, puis skill-file-qa avec --workspace pointé sur la sous-racine du projet. Utiliser quand un Skill doit fournir scripts/auditer_*.py, quand un audit doit être qualifié de read-only, quand l'import d'un module projet échoue en AttributeError dataclasses, quand validate_skill.py signale local reference not found sur des chemins du dépôt, ou quand une commande documentée échoue en rc=2 à cause d'une variable Bash non développée. 中文触发：只读交付审计脚本、importlib 导入 dataclass 模块、sys.modules 注册、__pycache__ 副作用、skill-file-qa --workspace、篡改副本 rc=1、无效根 rc=2、Bash 变量展开、审计报告诚实分级。"
---

# Audit de livraison en lecture seule pour un module de projet

## Portée

Produire le script d'audit qu'un Skill de domaine livre pour vérifier sa propre
livraison : recalcul des preuves logicielles, fraîcheur des artefacts par SHA-256,
complétude d'une liste de fichiers, présence des routes et pages, sans écrire dans
le projet.

Ce Skill ne remplace pas :

| Besoin | Skill |
| :--- | :--- |
| Acceptation statique du paquet (frontmatter, références, `Files (N)`) | `skill-file-qa` |
| Contrat UTF-8, cp1252 et codes 0/1/2 d'un script Windows | `windows-python-utf8-skill-scripts` |
| Preuve qu'une vérification dite read-only ne modifie pas d'état | `verifier-effets-de-bord-verification-lecture-seule` |
| Test d'un pré-contrôle CLI avec espions et compteurs d'appels | `tester-garde-cli-sans-effets-de-bord` |
| Vérificateur purement statique par AST, sans import du module | `develop-skill-static-checker` |
| Réparer un paquet après un échec de `skill-file-qa` | `reparer-paquet-skill-echecs-qa` |
| Écriture concurrente pendant la validation | `skill-update-concurrency-safe` |
| Faits et valeurs du domaine déjà audité | Skill de domaine, par exemple `qubit-logique-steane-preuves` |

Ne pas écrire un second audit de domaine quand le Skill de domaine en livre déjà un :
le compléter. Ne pas importer un module pour faire un contrôle purement textuel.

## Contrat non négociable

1. **Une ligne par contrôle** : `OK   <nom> <preuve>` ou `FAIL <nom> <attendu> != <obtenu>`.
2. **Fin de sortie** : `RESULT PASS (N controles)` ou `RESULT FAIL (k/N controles en echec)`.
3. **Codes** : 0 = aucun FAIL, 1 = au moins un FAIL, 2 = usage ou environnement
   (racine absente, module illisible, argument invalide). Aucun traceback.
4. **Sortie ASCII uniquement.** Passer chaque ligne par un échappeur ASCII.
5. **Lecture seule réelle** : aucun fichier projet créé, modifié ou supprimé, y compris
   les caches bytecode. Un artefact périmé est signalé, jamais régénéré par l'audit.
6. **Valeurs attendues exactes.** Compter des fichiers, comparer des empreintes, exiger
   une égalité. Une tolérance ou un `>=` doit être justifié par le domaine et documenté.
7. **Chaque contrôle doit pouvoir échouer.** Un contrôle dont aucune fixture ne fait
   varier le résultat est décoratif.

## Étape 1 — Définir les contrôles

Lister avant de coder, avec pour chacun le nom, la valeur attendue et la preuve lue :

| Contrôle | Attendu | Preuve |
| :--- | :--- | :--- |
| module | empreinte SHA-256 du fichier | fichier lu en octets |
| preuves | invariants recalculés par le module | appels aux fonctions de preuve |
| fraîcheur | `source.sha256 == sha256(module)` | artefact JSON de sortie |
| artefacts | N fichiers, tous présents | liste fermée de chemins relatifs |
| page et routes | marqueurs et alias présents | fichier HTML et source passerelle |
| sitemap | nombre exact d'URL | XML analysé |

Règles de conception :

- Fixer les invariants du domaine comme constantes lues, datées, indépendantes du module.
- Ne pas déduire une attente en réexécutant la même fonction qui produit l'artefact.
- Nommer les chemins relatifs depuis la racine du module, pas depuis le dépôt.

## Étape 2 — Importer le module sans effet de bord

Poser la garde **avant** le premier import de module projet :

```python
import importlib.util
import sys

sys.dont_write_bytecode = True


def charger_module(chemin, nom="module_projet_audit"):
    spec = importlib.util.spec_from_file_location(nom, chemin)
    if spec is None or spec.loader is None:
        raise ImportError("specification de module introuvable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    spec.loader.exec_module(module)
    return module
```

Pourquoi l'enregistrement est obligatoire : avec `from __future__ import annotations`,
toutes les annotations sont des chaînes ; `dataclasses._is_type` lit alors
`sys.modules[cls.__module__].__dict__`. Sans entrée dans `sys.modules`, l'audit meurt sur
`AttributeError: 'NoneType' object has no attribute '__dict__'`, parfois en rc=2.
Le déclencheur est l'annotation différée, pas `frozen=True` : la fixture du socle couvre
les deux formes.

- Lancer avec `py -3 -B` **et** garder `sys.dont_write_bytecode = True`. La garde Python
  suffit pour le module importé ; `-B` protège en plus tout interpréteur enfant.
- Choisir un nom unique : réutiliser le nom réel du module masque une installation.
- Si le module importe des voisins, ajouter sa racine à `sys.path` juste avant
  `exec_module` et la retirer dans un `finally`. Compter les caches avant et après, pas
  seulement à la fin.
- Ne pas importer le module avant d'avoir pris l'instantané initial des caches.

`scripts/socle_audit.py` fournit `charger_module`, `sha256`, `instantane_caches`,
`racine_par_defaut`, `Resultat` et `ecrire`, puis se vérifie lui-même :

```bash
py -3 -B "$HOME/.qoder/skills/auditer-livraison-skill-module-projet/scripts/socle_audit.py" --autotest
```

Attendu observé le 2026-10-27 : `RESULT PASS (8 controles)`, rc=0, stderr vide.

## Étape 3 — Prouver la non-écriture

1. Instantané avant l'import : nombre de `.pyc` et empreinte de la liste triée sous la racine.
2. Exécution complète de l'audit.
3. Instantané après : `(compte, empreinte)` doit être identique. Sinon FAIL en nommant
   les fichiers ajoutés.
4. Reprendre aussi les empreintes des artefacts lus : l'audit ne doit pas les réécrire.
5. Ne jamais supprimer un cache préexistant pour faire passer le contrôle : supprimer est
   une écriture, et l'utilisateur peut avoir un état à préserver. Rapporter, ne pas nettoyer.

```python
avant = instantane_caches(racine)
code = executer_controles(racine)
apres = instantane_caches(racine)
if avant != apres:
    resultat.fail(f"caches: {avant} -> {apres}")
else:
    resultat.ok(f"caches: {apres[0]} .pyc, liste inchangee")
```

Sur Windows, un fichier en lecture seule fait échouer `shutil.rmtree` en `WinError 5`
dans la fixture : `chmod -R u+w` le répertoire temporaire avant de le supprimer.

## Étape 4 — Trois contrôles négatifs obligatoires

La racine réelle ne prouve rien seule : elle peut passer parce que tous les contrôles
sont vides. Exécuter, dans cet ordre, avec des lignes d'affectation séparées.

```bash
AUDIT="$HOME/.qoder/skills/<skill-de-domaine>/scripts/auditer_livraison.py"
RACINE="C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B "$AUDIT" --racine "$RACINE"
```

| Cas | Attendu |
| :--- | :--- |
| racine réelle | `RESULT PASS (N controles)`, rc=0, N identique aux contrôles codés |
| détection par défaut | même résultat sans `--racine`, depuis le dossier du projet |
| copie falsifiée | rc=1, `RESULT FAIL (1/N)`, et le FAIL nomme le seul contrôle cassé |
| racine absente | rc=2, `ERREUR ... introuvable`, aucune trace Python |

Protocole de la copie falsifiée :

1. Copier la racine projet dans un répertoire temporaire, jamais modifier l'original.
2. Choisir un fichier que l'audit hache, modifier un octet, **recalculer son empreinte et
   vérifier qu'elle a changé** avant de lancer l'audit. Une mutation non appliquée produit
   un faux PASS ou un faux FAIL inexplicable.
3. Lancer l'audit sur la copie avec `--racine` explicite.
4. Exiger exactement 1 FAIL. Plus d'un FAIL signale une cascade, pas une preuve ciblée.
5. Supprimer la copie, puis comparer les empreintes de l'original à celles d'avant.

`--racine /` ou `--racine ""` doit tomber en rc=2, pas en rc=1 : distinguer l'erreur
d'environnement d'un échec de contenu.

## Étape 5 — Empaqueter et valider

1. **Rejouer les commandes documentées telles qu'écrites.** Une commande du SKILL.md qui
   échoue en rc=2 est un défaut de documentation, pas un détail d'environnement.
2. **Ne jamais préfixer une commande par une affectation utilisée dans ses arguments.**
   `VAR=... commande "$VAR/x"` développe `$VAR` avant l'affectation : le chemin devient
   la racine MSYS. Écrire l'affectation sur sa propre ligne.
3. **Références du projet dans le SKILL.md** : `skill-file-qa` résout un jeton entre
   backticks d'abord dans le dossier du Skill, puis dans `--workspace`. Si la
   documentation cite des chemins relatifs au module, pointer `--workspace` sur la
   sous-racine qui les contient, et l'inscrire dans la commande de QA. Sinon, écrire des
   noms de fichiers nus ou des jetons à chevrons.

```bash
QA="$HOME/.qoder/skills/skill-file-qa"
CIBLE="$HOME/.qoder/skills/<skill-de-domaine>"
WORKSPACE="C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 "$QA/scripts/validate_skill.py" "$CIBLE" \
  --workspace "$WORKSPACE" --stable-seconds 2 --stability-timeout 30
```

Exiger `RESULT PASS`, `0 fail`, le bon `Files (N)`, puis relancer l'autotest du socle et
les trois contrôles négatifs **après** la dernière écriture du paquet. Un PASS antérieur
à une écriture ne vaut plus.

## Étape 6 — Rapporter sans surpromettre

- Séparer : vérifié (sortie réelle citée), reproduit (fixture), non déclenché (branche
  non couverte).
- Donner les empreintes avec leur date d'observation, jamais comme des constantes durables.
- Un audit PASS prouve la cohérence de la livraison, pas la vérité scientifique du domaine.
- Un artefact périmé se répare par le générateur du domaine, exécuté par l'utilisateur ou
  par la procédure du Skill de domaine, pas par l'audit.

## Triage

| Symptôme | Cause | Correctif |
| :--- | :--- | :--- |
| `AttributeError: 'NoneType' object has no attribute '__dict__'` dans `dataclasses._is_type` | module exécuté sans entrée `sys.modules` | enregistrer avant `exec_module` |
| `__pycache__` ou `.pyc` apparu après l'audit | garde posée après l'import, ou absente | garde en tête de fichier, `py -3 -B` |
| `UnicodeEncodeError: 'charmap' codec` | sortie non-ASCII directe, `ensure_ascii=False` | échappeur ASCII sur chaque ligne |
| rc=2 avec un chemin sous `C:\Program Files\Git` | affectation inline non développée | affectation sur une ligne séparée |
| plusieurs `FAIL local reference not found` sur des chemins du module | `--workspace` trop haut dans l'arborescence | pointer la sous-racine, ou noms nus |
| la copie falsifiée renvoie PASS | mutation non appliquée ou audit lancé sur l'original | vérifier l'empreinte mutée et `--racine` |
| PASS sur la racine réelle après une régénération | contrôle de fraîcheur absent | lier artefact et module par SHA-256 |
| FAIL immédiat après une mise à jour | valeur attendue obsolète | re-mesurer et dater, ne pas relâcher |

## Ressources

- `scripts/socle_audit.py` — chargeur sûr, sortie ASCII, empreintes, instantané de caches,
  `Resultat` 0/1/2 ; `--autotest` prouve le socle en 8 contrôles.
- `references/pieges-verifies-2026-10-27.md` — preuves datées : trace `dataclasses`,
  caches avant/après, `workspace` A/B, expansion Bash, sorties de la session source.
