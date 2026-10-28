---
name: centraliser-resolution-artefact-python
description: "Centraliser la résolution d'un artefact (ABI JSON, bytecode, configuration) codé en dur dans plusieurs scripts Python : inventaire exhaustif des consommateurs, module unique fondé sur `__file__`, rebranchement de chaque appelant, puis échelle de vérification (compilation, modes simulation avec stdin fermé, empreinte des effets de bord, ABI et bytecode, fixtures positive et négative). Utiliser quand l'utilisateur demande de corriger tous les chemins d'un même artefact, de créer un module de résolution partagé, ou quand plusieurs scripts portent le même chemin mort. Couvre l'exception d'autonomie d'un outil de déploiement copié seul sur un VPS. Pour un script unique, utiliser `reparer-chemin-artefact-absolu-script-python` ; pour la preuve ABI contre le contrat déployé, utiliser `verifier-abi-locale-contrat-deploye`."
---

# Centraliser la résolution d'un artefact partagé par plusieurs scripts Python

## Quand l'utiliser

- L'utilisateur demande de corriger **tous** les chemins d'un même artefact, pas un seul.
- Plusieurs scripts portent le même littéral mort ou le même motif de chargement.
- Un artefact est chargé par N CLI et doit être résolu depuis l'emplacement du code.
- Après une réparation locale, l'utilisateur demande de centraliser ou d'étendre aux autres scripts.

## Quand ne pas l'utiliser

- **Un seul script** : c'est `reparer-chemin-artefact-absolu-script-python`.
- **Prouver l'ABI contre le contrat déployé** : c'est `verifier-abi-locale-contrat-deploye`.
- **Mentions dans des `.md`, `.bat` ou docstrings uniquement** : correction documentaire, sans module.

## Règle d'or

L'inventaire précède l'édition, et chaque rebranchement est compilé avant le suivant. Un consommateur qui peut être copié seul (bundle VPS, dossier aplati) ne doit pas importer le module partagé.

## Étape 1 — Inventaire exhaustif avant toute écriture

```bash
grep -rnF '<littéral exact>' --include=*.py .
grep -rnE --include=*.py 'chemin_abi|ABI_CONTRAT_PATH|chemin_contrat|\["abi"\]|\["bytecode"\]'
grep -rnF '<littéral exact>' --include=*.md --include=*.bat --include=*.txt .
```

- Figer la liste des consommateurs avant d'éditer quoi que ce soit.
- Séparer les vrais chargements d'artefact des simples mentions dans des docstrings, guides ou scripts `.bat`.
- Compter les occurrences : ce nombre devient l'assertion finale (imports attendus, littéraux résiduels = 0).
- Ne pas chercher uniquement le littéral exact : un second script peut construire le même chemin par morceaux.

## Étape 2 — Classer l'autonomie de chaque consommateur

| Type de consommateur | Traitement |
|---|---|
| CLI du même arbre, exécuté sur place | importe le module partagé |
| Outil de déploiement copié seul (VPS, bundle plat) | garde sa propre liste de candidats, **sans import** |
| Script d'un sous-dossier (`deploiement_vps/`) | vérifier que le module est sur `sys.path`, sinon import cassé |
| Documentation, `.bat`, docstrings | hors périmètre, ne pas éditer sans demande |

Un outil destiné à être copié seul échoue à l'import si le module partagé n'est pas dans le bundle : `ModuleNotFoundError` avant toute résolution. C'est un choix de conception, pas un oubli.

## Étape 3 — Créer le module unique

Avant d'écrire, vérifier que le module n'existe pas déjà et que le dossier cible existe réellement.

```python
from pathlib import Path
import json

NOM_ARTEFACT = "<Artefact>.json"
RACINE_SYSTEME = Path(__file__).resolve().parent
RACINE_PROJET = RACINE_SYSTEME.parent

CANDIDATS = (
    RACINE_SYSTEME / "contracts" / NOM_ARTEFACT,
    RACINE_SYSTEME / "contracts" / "build" / NOM_ARTEFACT,
    RACINE_PROJET.parent / "<depot_voisin>" / "contracts" / NOM_ARTEFACT,
    RACINE_PROJET.parent / "<depot_voisin>" / "contracts" / "build" / NOM_ARTEFACT,
)

def chemin_abi() -> Path:
    for candidat in CANDIDATS:
        if candidat.is_file():
            return candidat
    cherches = "\n  ".join(str(c) for c in CANDIDATS)
    raise FileNotFoundError(f"{NOM_ARTEFACT} introuvable. Chemins testés :\n  {cherches}")

def charger_abi() -> list:
    with open(chemin_abi(), "r", encoding="utf-8") as f:
        return json.load(f)["abi"]
```

Contraintes : aucun littéral absolu, ordre des candidats explicite, échec citant tous les chemins, artefact non dupliqué dans l'arbre du projet, nom de module unique.

## Étape 4 — Rebrancher chaque consommateur

1. Remplacer le littéral **et** l'ouverture (`open` + `json.load`) par `from <module> import charger_abi`.
2. Vérifier l'importabilité depuis le dossier réel d'exécution, pas depuis la racine du projet.
3. Préserver les replis existants. Un script qui utilisait `os.path.exists` pour basculer sur une ABI minimale doit désormais intercepter `FileNotFoundError` ; ne jamais avaler les autres exceptions.
4. Compiler chaque fichier après édition, puis passer au suivant.
5. Terminer par l'assertion : `grep -rnF '<littéral>' --include=*.py .` rend 0.

Rapporter un tableau `fichier → ligne d'import → ligne d'appel` : c'est la preuve du rebranchement, pas le nombre de messages de succès.

## Étape 5 — Échelle de vérification

Aucun niveau ne suffit seul. Les exécuter dans cet ordre.

1. **Compilation** : `py -3 -m py_compile <fichiers>` sur tous les fichiers touchés, module compris.
2. **Simulation de chaque CLI**, stdin fermé, code de sortie capturé :

```bash
cd <dossier_script> && py -3 <script>.py --simuler < /dev/null; echo "rc=$?"
```

   Lire le bloc `argparse` avant : `--simuler` doit sortir avant toute demande de clé ou envoi. Sans drapeau de simulation, s'arrêter et demander — ne jamais lancer le mode réel pour « voir ».
3. **Empreinte des effets de bord** : compter les fichiers et hacher le répertoire que les scripts écrivent, avant et après.

```bash
find <repertoire_effets> -type f | sort | xargs -r md5sum > /tmp/avant.md5
```

   Un compte identique et des empreintes identiques valent preuve d'absence d'écriture. Tout delta doit être attribué, sinon la vérification est incomplète.
4. **Preuve de résolution** : afficher le chemin réellement retenu, le nombre d'entrées ABI et la taille du bytecode. Pour un contrat déployé, déléguer à `verifier-abi-locale-contrat-deploye` (sélecteur, `CHAIN`, `BLOCK`) au lieu de recopier son contrôle.
5. **Assertions de couverture** : littéral résiduel = 0 ; nombre d'importeurs = nombre inventorié ; aucun fichier non traité.

Un dry-run vert ne prouve ni l'identité de l'artefact ni l'absence d'effets de bord.

## Étape 6 — Fixtures positive et négative

Créer les fixtures hors de l'installation du Skill, sous `<projet>/.qoder/tmp/`, et les supprimer après.

- **Positive** : un `contracts/` local dans la copie fixture doit gagner sur le dépôt voisin. C'est la preuve que la priorité VPS est préservée.
- **Négative** : sans artefact, le script doit sortir avec `rc=1` et lister tous les chemins testés.

Piège vérifié : un fixture importé par nom depuis un dossier absent de `sys.path` échoue en `ModuleNotFoundError: No module named 'deploy_evm_reseau'` avant toute assertion de résolution. Importer le fichier par son chemin absolu, ou se placer dans son dossier, puis seulement conclure.

## Étape 7 — Frontières et rapport

- Lister les consommateurs volontairement non traités (docs, `.bat`, docstrings) au lieu de les modifier en silence.
- Pour un commit demandé, localiser d'abord le vrai dépôt : la racine du projet peut ne pas être un dépôt Git, seul un sous-dossier l'être.
- Ne jamais annoncer un commit terminé si la commande est encore en cours d'exécution ; lire son code de sortie.

## Pièges vérifiés (session 026949af, 28/10/2026)

| Piège | Conséquence constatée |
|---|---|
| Supposer l'artefact sous la racine du projet | premier correctif avec 2 candidats internes → encore `FileNotFoundError` |
| Corriger seulement le script du traceback | 7 autres scripts portaient le même littéral mort |
| Router un outil de déploiement par le module partagé | import cassé dès que seul son dossier est copié |
| Conclure après `--simuler` | ne prouve ni l'ABI déployée ni l'absence d'écriture |
| Ignorer les effets de bord | `memoire_aq` doit rester à 192 fichiers, même empreinte |
| Fixture hors `sys.path` | `ModuleNotFoundError` avant la moindre assertion |
| Croire le commit fait | session encore `running`, dernier outil en cours |

## Checklist de sortie

- [ ] Liste des consommateurs figée avant édition
- [ ] Chaque consommateur classé (module partagé ou autonome)
- [ ] Module unique créé, aucun littéral absolu, erreur citant tous les chemins
- [ ] Tous les consommateurs prévus rebranchés, replis préservés
- [ ] `py_compile` vert sur tous les fichiers touchés
- [ ] Chaque CLI rejouée en simulation, `rc=0`, stdin fermé
- [ ] Effets de bord identiques avant/après (compte et empreintes)
- [ ] Résolution réelle affichée, ABI et bytecode cohérents
- [ ] Fixtures positive et négative vertes, puis supprimées
- [ ] Littéral résiduel = 0, importeurs = inventaire
- [ ] Aucune action irréversible exécutée sans accord

## Resources

- `references/session-026949af-centralisation.md` — chiffres vérifiés sur disque, sorties de session, échec du premier fixture, limites de preuve.
