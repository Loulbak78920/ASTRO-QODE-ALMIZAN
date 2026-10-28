---
name: reparer-chemin-artefact-absolu-script-python
description: "Réparer un script Python qui échoue sur un chemin absolu mort vers un artefact (ABI JSON, données, configuration) après renommage ou déplacement du projet. Utiliser sur un FileNotFoundError citant un dossier qui n'existe plus (ex. Desktop/Al-Mizan), sur un chemin codé en dur dans `chemin_abi`, `ABI_CONTRAT_PATH` ou un open(), et avant tout rejeu qui enverrait une transaction ou écraserait un fichier. Couvre la localisation de l'artefact réel hors workspace, la résolution par candidats relatifs à `__file__`, le rejeu en dry-run, le renvoi de la preuve on-chain à `verifier-abi-locale-contrat-deploye` (SHA-256 pour un artefact non contractuel) et le recensement des autres scripts portant le même littéral. Si plusieurs scripts doivent être corrigés, utiliser `centraliser-resolution-artefact-python`."
---

# Réparer un chemin d'artefact absolu mort dans un script Python

## Quand l'utiliser

- Un script Python lève `FileNotFoundError` sur un chemin absolu dont le dossier n'existe plus.
- L'utilisateur colle un traceback ou une sortie console sans question explicite : le correctif attendu est de rendre le script exécutable.
- Avant tout rejeu d'un script qui peut demander une clé privée, envoyer une transaction ou écraser un fichier.

## Règle d'or

Ne jamais supposer où se trouve l'artefact. Trois preuves avant de conclure : chemin mort constaté, artefact réel localisé, rejeu dry-run vert. Un dry-run vert ne prouve pas que l'artefact est le bon.

## Étape 1 — Lire le point de chargement

1. Repérer dans le traceback le fichier et la ligne du `open()` / `json.load()` qui échoue.
2. Lire la fonction qui construit ce chemin : constante globale, variable locale ou variable d'environnement.
3. Relire le chemin **dans le source**, pas dans la console : sous Windows en cp1252, `ASTRO-Q°ODE_SYSTEME` s'affiche `ASTRO-Q�ODE_SYSTEME` dans le traceback.

## Étape 2 — Prouver que le chemin est mort, puis localiser l'artefact

```bash
ls -la "<chemin exact du traceback>"          # doit échouer
cd <parent réel du projet>                     # souvent le Bureau, pas la racine du projet
find . -iname "<nom_artefact>" 2>/dev/null    # hors workspace inclus
```

- Chercher le nom de base depuis le dossier parent : l'artefact peut vivre dans un dépôt voisin, hors du workspace.
- Si plusieurs copies existent (ex. `contracts/` et `contracts/build/`), comparer taille et SHA-256, et retenir celle qui correspond au build ciblé.
- Ne pas copier l'artefact dans l'arbre du projet sans accord : un chemin vers un dépôt voisin est un montage valide.

## Étape 3 — Résoudre par candidats relatifs à `__file__`

Remplacer le littéral par une résolution par candidats, du local vers le voisin, avec une erreur qui liste les chemins testés :

```python
from pathlib import Path

RACINE_PROJET = Path(__file__).resolve().parent.parent  # profondeur à vérifier, pas à copier
CANDIDATS_ARTEFACT = (
    RACINE_PROJET / "<sous_dossier>" / "contracts" / "build" / "Artefact.json",
    RACINE_PROJET.parent / "<depot_voisin>" / "contracts" / "Artefact.json",
    RACINE_PROJET.parent / "<depot_voisin>" / "contracts" / "build" / "Artefact.json",
)

def charger_artefact() -> list:
    for chemin in CANDIDATS_ARTEFACT:
        if chemin.is_file():
            with open(chemin, "r", encoding="utf-8") as f:
                return json.load(f)["abi"]
    cherches = "\n  ".join(str(c) for c in CANDIDATS_ARTEFACT)
    raise FileNotFoundError(f"Artefact introuvable. Chemins testés :\n  {cherches}")
```

Contraintes : aucun littéral absolu restant ; l'ordre des candidats est explicite ; l'échec cite tous les chemins ; pas de duplication de l'artefact dans le projet.

## Étape 4 — Rejeu en dry-run

1. Ouvrir le bloc `argparse` et identifier le drapeau de simulation (`--simuler`, `--simulate`, `--dry-run`). S'il n'existe pas, s'arrêter et demander : ne pas lancer le mode réel.
2. Lire la branche du drapeau avant de l'exécuter (elle doit sortir avant la demande de clé et l'envoi).
3. Rejouer depuis le dossier du script, avec le code de sortie :

```bash
cd <dossier_script> && py -3 <script>.py --simuler; echo "rc=$?"
```

4. Si l'échec persiste avec la liste des candidats, la liste est fausse : revenir à l'étape 2. Ne pas élargir les candidats au hasard.

## Étape 5 — Faire prouver la conformité de l'artefact

Un dry-run vert prouve seulement que le fichier se charge. Pour une ABI de contrat, ne pas recalculer le sélecteur ici : invoquer `verifier-abi-locale-contrat-deploye` avec le chemin réellement résolu, la signature exacte de l'appel, l'adresse du contrat et le nombre d'entrées attendu. Lire son `RESULT PASS`, puis consigner `SELECTOR`, `CHAIN` et `BLOCK` au moment de la requête.

Pour un artefact non contractuel (données, configuration), comparer son SHA-256 à la valeur attendue ou au manifeste. Verdict `ABSENT` ou `RESULT FAIL` : ne pas exécuter le mode réel.

## Étape 6 — Recenser les autres consommateurs du littéral

```bash
grep -rnF '<littéral exact>' --include=*.py .
grep -rnE --include=*.py '<variantes : chemin_abi|ABI_CONTRAT_PATH|nom_artefact>'
```

- Rapporter la liste des scripts touchés ; si la demande couvre plusieurs scripts, basculer sur `centraliser-resolution-artefact-python`. Ne corriger en masse qu'une fois cette bascule faite.
- Distinguer les vrais chargements d'artefact des occurrences du dossier mort dans des `.md`, `.bat` ou registres JSON.

## Pièges vérifiés (session 026949af, 28/10/2026)

| Piège | Conséquence constatée |
|---|---|
| Supposer l'artefact sous la racine du projet | 1er correctif avec 2 candidats sous `RACINE_PROJET` → rejeu encore en `FileNotFoundError` |
| Chercher uniquement dans le workspace | l'artefact réel était dans le dépôt voisin `Desktop/GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` |
| Conclure après un dry-run vert | le dry-run ne construit aucune transaction ; une ABI d'un autre build passerait |
| Lancer le script sans dry-run | demande la clé privée et envoie une transaction mainnet irréversible |
| Console cp1252 | chemins accentués illisibles dans le traceback (`°` → `�`) |
| Corriger un seul script | 7 autres scripts portaient le même littéral mort |

## Checklist de sortie

- [ ] Chemin mort constaté (`ls` en échec)
- [ ] Artefact réel localisé (chemin absolu, taille)
- [ ] Aucun littéral absolu restant dans le script corrigé
- [ ] L'erreur liste les candidats testés
- [ ] Rejeu dry-run vert, `rc=0`
- [ ] Conformité déléguée à `verifier-abi-locale-contrat-deploye` : `RESULT PASS`, `SELECTOR`, `CHAIN` et `BLOCK` consignés (SHA-256 si artefact non contractuel)
- [ ] Autres consommateurs recensés et signalés
- [ ] Aucune action irréversible exécutée sans accord

## Resources

- `references/session-026949af-preuves.md` — erreur verbatim, échec du premier correctif, sortie du dry-run et du contrôle de sélecteur, inventaire des scripts restants, empreintes.
