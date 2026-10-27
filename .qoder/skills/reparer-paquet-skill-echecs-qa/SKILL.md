---
name: reparer-paquet-skill-echecs-qa
description: "Réparer un paquet Skill après un échec de skill-file-qa sans affaiblir le validateur : classer chaque FAIL, corriger la cause réelle — référence locale prise pour un chemin du projet cible, ou cache __pycache__ créé par l'import d'un script frère — puis relancer la QA et réexécuter les scripts sur l'artefact réel. Utiliser quand validate_skill.py renvoie RESULT FAIL, « local reference not found » sur un chemin du dépôt documenté, un fichier .pyc ou un dossier __pycache__ apparu dans Files (N), un Files (N) inattendu, ou quand un second passage QA doit être prouvé après correction. 中文触发：skill-file-qa 失败修复、本地引用找不到、反引号里的项目路径、__pycache__ 污染、脚本导入生成缓存、修复后重跑校验。"
---

# Réparer un paquet Skill après un échec QA

## Portée

Réparer deux échecs récurrents de `skill-file-qa` sur un paquet qui livre des scripts, puis prouver la réparation par un second passage et par une réexécution réelle. Ce Skill ne rédige pas le paquet, ne le commite pas et ne le publie pas.

Déléguer sans dupliquer :

| Besoin | Skill |
| :--- | :--- |
| Lancer la QA et connaître la portée exacte du validateur | `skill-file-qa` |
| Prouver la provenance d'un cache, établir le manifeste Files (N) | `skill-package-integrity-audit` |
| Hygiène générale des scripts Windows : sortie UTF-8, codes de retour, cache | `windows-python-utf8-skill-scripts` |
| Sonde de jetons et écritures concurrentes | `skill-update-concurrency-safe` |
| Rédiger les documents du projet cible | `documenter-passerelle-python-stdlib` |

## Invariants

1. Ne jamais modifier le validateur, ses constantes ni les attendus PASS/FAIL : la réparation se fait dans le Skill ciblé.
2. Ne supprimer qu'un cache dont la provenance est attribuée à la session courante ; jamais un cache préexistant.
3. Corriger la cause, pas la sortie brute : un jeton problématique supprimé sans remplacement utile fait perdre l'information documentaire.
4. Un correctif n'est acquis qu'après : second passage QA sur un fichier stable, réexécution du script sur l'artefact réel, contrôle d'absence de cache.
5. Sur Windows, utiliser `py -3` ; l'alias `python` peut être le stub Microsoft Store.
6. La règle de référence s'applique au fichier entier, blocs de code compris : corriger la prose ne suffit pas.

## Boucle de réparation

### 1. Relire la sortie complète

Noter `Fingerprint (start)`, `Files (N)`, `Summary`, `RESULT` et `EXIT`, puis copier la ligne FAIL exacte avec son jeton. Ne pas résumer de mémoire : la même session peut avoir produit plusieurs passages.

### 2. Classer avant de réparer

| Symptôme | Cause probable | Suite |
| :--- | :--- | :--- |
| `FAIL local reference not found` sur un chemin du projet cible | chemin relatif au dépôt documenté, résolu contre le paquet puis le workspace | section A |
| `.pyc` ou dossier `__pycache__` dans `Files (N)` | import d'un module voisin au premier lancement | section B |
| FAIL `fingerprint: changed during validation` | écriture concurrente pendant le passage | `skill-update-concurrency-safe`, puis repasser la QA |
| FAIL frontmatter, name, description, body ou layout | défaut structurel, hors périmètre | `skill-file-qa`, ne pas improviser |

### 3. Réparer une cause à la fois

Une seule cause par passe : deux corrections simultanées empêchent d'attribuer le prochain FAIL. Si une correction échoue, revenir à l'état précédent avant d'en tenter une autre.

### 4. Relancer la QA

```bash
QA="$HOME/.qoder/skills/skill-file-qa"
py -3 "$QA/scripts/validate_skill.py" "<skill-dir>" \
  --workspace "<workspace-root>" --stable-seconds 2 --stability-timeout 30
```

Exiger `RESULT PASS`, `EXIT=0`, `0 fail`. Lire aussi `Files (N)` et `local references: N checked` : un PASS ne prouve ni la propreté du dossier ni la justesse des références.

### 5. Réexécuter les scripts réels

La QA statique ne prouve pas le comportement. Relancer chaque script du paquet sur l'artefact réel et retrouver la sortie attendue (`RESULT` propre au script, code de retour, compteurs). Une régression ici annule le PASS.

### 6. Gate final

- Double échantillonner `SKILL.md` (size, mtime, SHA-256) et le comparer au `Fingerprint (final)` du validateur ; toute écriture ultérieure invalide le PASS.
- Lister le paquet et confirmer l'absence de `.pyc` et de `__pycache__`.
- Consigner les sorties réelles ; ne jamais recopier des nombres d'une session antérieure.

## A. Référence locale prise pour un chemin du projet cible

### Règle vérifiée du validateur

`collect_refs` lit tout le `SKILL.md`, blocs de code compris. Un jeton entre backticks devient une référence locale s'il commence par les préfixes de ressources (scripts, references, assets, chacun suivi d'une barre oblique) ou s'il contient une barre oblique et se termine par une extension connue. La résolution essaie le dossier du Skill, puis la racine du workspace.

Conséquence : un chemin du type dossier-document/fichier.md, copié depuis le dépôt documenté, échoue sur les deux racines. Vérifié :

```text
docs/README.md                         -> FAIL local reference not found
docs/ARCHITECTURE_ET_DEVELOPPEMENT.md  -> FAIL local reference not found
README.md                              -> accepté (nom nu, aucune barre oblique)
```

### Correctifs, du plus sûr au plus fragile

1. Écrire le nom de fichier nu dans le tableau des documents à produire : `README.md`, `ARCHITECTURE_ET_DEVELOPPEMENT.md`. C'est la forme validée sur le cas réel.
2. Utiliser un placeholder avec chevrons, du type `<dossier>/<sujet>.md` : les chevrons font rejeter le jeton.
3. Préfixer par une variable, du type `$RACINE_PROJET/<fichier>` : un jeton commençant par `$` est ignoré.
4. Si le fichier existe réellement dans le paquet, garder le chemin relatif : il se résout dans le dossier du Skill.

Ne pas se contenter de supprimer le jeton : la documentation doit continuer à nommer le fichier concerné.

### Sonde reproductible

Hors du dossier du Skill, dans un répertoire temporaire :

```bash
PROBE=$(mktemp -d "$HOME/.qoder/tmp/ref-probe.XXXXXX")
mkdir -p "$PROBE/skill" "$PROBE/workspace"
PROBE_TOKEN="docs/README.md"
{
  printf -- '---\nname: skill\ndescription: "Probe."\n---\n\n'
  printf 'Token : `%s`\n' "$PROBE_TOKEN"
} > "$PROBE/skill/SKILL.md"
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "$PROBE/skill" --workspace "$PROBE/workspace" --stable-seconds 0
chmod -R u+w "$PROBE"; rm -rf "$PROBE"
```

Le `RESULT FAIL` de la sonde est le résultat attendu : il prouve que la forme testée est scannée. Le jeton est construit par variable pour que la présente procédure ne contienne elle-même aucun jeton interdit. Ne jamais copier le jeton fautif tel quel dans le Skill cible.

## B. Cache bytecode créé par un import frère

### Mécanisme

Un script du paquet qui importe un module voisin (par exemple `from inventorier_routes import extraire_routes`) écrit un dossier `__pycache__` et un `.pyc` dans le dossier du module voisin, dès le premier import. Le validateur compte tous les fichiers hors `.git`, donc `Files (N)` augmente alors que le layout peut rester PASS.

### Correctif : garde avant l'import

```python
import sys

sys.dont_write_bytecode = True

from inventorier_routes import extraire_routes
```

Placement impératif : après `import sys` et **avant** l'import du module voisin. Placée après, la garde arrive trop tard, le cache est déjà écrit.

Alternatives moins durables : lancer avec `-B`, ou exporter `PYTHONDONTWRITEBYTECODE=1`. Elles ne protègent que les invocations qui les portent ; la garde dans le script protège tous les consommateurs.

### Suppression et preuve

1. Lister précisément, puis faire attribuer la provenance à la session avant toute suppression (politique de `skill-package-integrity-audit`).
2. `chmod -R u+w` sur le cache, puis supprimer le dossier listé.
3. Vérifier l'absence :

```bash
find "<skill-dir>" \( -name "__pycache__" -o -name "*.pyc" \) -print
```

4. Relancer le script réel : si le cache réapparaît, la garde est absente ou mal placée. Corriger, puis recommencer.
5. Relancer la QA : `Files (N)` doit diminuer du nombre de fichiers supprimés.

## Erreurs à ne pas commettre

| Erreur | Effet | Correctif |
| :--- | :--- | :--- |
| Modifier le validateur ou ses attendus | masque le défaut, fausse tous les passages suivants | revenir au validateur d'origine |
| Garde bytecode placée après l'import frère | le cache est écrit avant la garde | déplacer la garde |
| Remplacer un chemin du projet par un autre chemin du projet | même FAIL, cause intacte | nom nu ou placeholder |
| Supprimer un cache préexistant non attribué | destruction de l'état d'autrui | attribuer avant de supprimer |
| Conclure sur la QA sans réexécuter les scripts | PASS statique, comportement non prouvé | étape 5 |
| Recopier les chiffres d'un cas antérieur | rapport faux | lire la sortie courante |

## Checklist de sortie

- [ ] Second passage : `RESULT PASS`, `EXIT=0`, `0 fail`.
- [ ] `Files (N)` attendu, sans `.pyc` ni `__pycache__`.
- [ ] `local references: N checked` sans FAIL, jetons remplacés par une forme lisible.
- [ ] Chaque script réexécuté sur l'artefact réel, sortie attendue retrouvée.
- [ ] Sonde temporaire supprimée ; aucun jeton fautif introduit dans le paquet.
- [ ] Empreinte `SKILL.md` double-échantillonnée, égale au `Fingerprint (final)`.

## Preuves

Les deux incidents, leurs sorties exactes, les empreintes et les re-mesures indépendantes sont consignés dans [cas documenter-passerelle du 27/10/2026](references/cas-documenter-passerelle-2026-10-27.md).
