---
name: reparer-paquet-skill-echecs-qa
description: "Réparer un paquet Skill après un échec de skill-file-qa sans affaiblir le validateur : classer chaque FAIL, corriger la cause réelle — référence locale prise pour un chemin du projet cible, racine de workspace imbriquée ou multi-racine, jeton réellement faux, cache __pycache__ créé par l'import d'un script frère, ou commande d'acceptation qui ne s'exécute pas depuis le cwd documenté — puis relancer la QA et réexécuter les scripts sur l'artefact réel. Utiliser quand validate_skill.py renvoie RESULT FAIL, « local reference not found » sur un chemin du dépôt documenté alors que le fichier existe sous une racine imbriquée, un fichier .pyc ou un dossier __pycache__ apparu dans Files (N), un Files (N) inattendu, un PASS qui ne prouve pas l'exécution d'une commande de script depuis la racine projet, ou quand un second passage QA doit être prouvé après correction. 中文触发：skill-file-qa 失败修复、本地引用找不到、反引号里的项目路径、嵌套根或多根 workspace、--workspace 选错、验收命令依赖当前目录、__pycache__ 污染、脚本导入生成缓存、修复后重跑校验。"
---

# Réparer un paquet Skill après un échec QA

## Portée

Réparer trois échecs récurrents de `skill-file-qa` sur un paquet qui livre des scripts — références locales, cache bytecode, commandes d'acceptation dépendantes du cwd — puis prouver la réparation par un second passage et par une réexécution réelle. Ce Skill ne rédige pas le paquet, ne le commite pas et ne le publie pas.

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
7. Un seul `--workspace` par passage : vérifier l'existence de chaque jeton sous la racine candidate avant de changer la racine.
8. Un PASS statique ne prouve pas qu'une commande documentée s'exécute depuis le cwd annoncé (section C).

## Boucle de réparation

### 1. Relire la sortie complète

Noter `Fingerprint (start)`, `Files (N)`, `Summary`, `RESULT` et `EXIT`, puis copier la ligne FAIL exacte avec son jeton. Ne pas résumer de mémoire : la même session peut avoir produit plusieurs passages.

### 2. Classer avant de réparer

| Symptôme | Cause probable | Suite |
| :--- | :--- | :--- |
| `FAIL local reference not found` sur un chemin du projet cible | chemin relatif au dépôt documenté, résolu contre le paquet puis le workspace | section A |
| `FAIL local reference not found` alors que les fichiers existent sous une racine imbriquée | `--workspace` pointe sur la racine Qoder au lieu de la racine des chemins | section A.2 |
| `.pyc` ou dossier `__pycache__` dans `Files (N)` | import d'un module voisin au premier lancement | section B |
| PASS mais la commande documentée échoue depuis le cwd annoncé | jeton de script résolu par la QA contre le dossier du Skill, par le shell contre le cwd | section C |
| FAIL `fingerprint: changed during validation` | écriture concurrente pendant le passage | `skill-update-concurrency-safe`, puis repasser la QA |
| FAIL frontmatter, name, description, body ou layout | défaut structurel, hors périmètre | `skill-file-qa`, ne pas improviser |

### 3. Réparer une cause à la fois

Une seule cause par passe : deux corrections simultanées empêchent d'attribuer le prochain FAIL. Si une correction échoue, revenir à l'état précédent avant d'en tenter une autre.

### 4. Relancer la QA

```bash
QA="$HOME/.qoder/skills/skill-file-qa"
py -3 "$QA/scripts/validate_skill.py" "<skill-dir>" \
  --workspace "<racine des chemins documentés>" --stable-seconds 2 --stability-timeout 30
```

Exiger `RESULT PASS`, `EXIT=0`, `0 fail`. Lire aussi `Files (N)` et `local references: N checked` : un PASS ne prouve ni la propreté du dossier ni la justesse des références.

### 5. Réexécuter les scripts réels

La QA statique ne prouve pas le comportement. Relancer chaque script du paquet sur l'artefact réel et retrouver la sortie attendue (`RESULT` propre au script, code de retour, compteurs). Une régression ici annule le PASS.

### 6. Gate final

- Double échantillonner `SKILL.md` (size, mtime, SHA-256) et le comparer au `Fingerprint (final)` du validateur ; toute écriture ultérieure invalide le PASS.
- Lister le paquet et confirmer l'absence de `.pyc` et de `__pycache__`.
- Consigner l'empreinte finale de `SKILL.md` dans le rapport. Ne jamais inscrire l'empreinte du fichier de preuves dans ce fichier : écrire `—` et la raison, l'empreinte finale allant dans le rapport.
- Toute édition postérieure au PASS, même d'une référence, impose de recalculer les empreintes, de corriger les valeurs périmées dans les références et de relancer la QA.
- Consigner les sorties réelles ; ne jamais recopier des nombres d'une session antérieure.

## A. Référence locale prise pour un chemin du projet cible

### A.1 Règle vérifiée du validateur

`collect_refs` lit tout le `SKILL.md`, blocs de code compris. Un jeton entre backticks devient une référence locale s'il commence par les préfixes de ressources (scripts, references, assets, chacun suivi d'une barre oblique) ou s'il contient une barre oblique et se termine par une extension connue. Les liens Markdown sont aussi comptés. La résolution essaie le dossier du Skill, puis la racine du workspace.

Conséquence : un chemin du type dossier-document/fichier.md, copié depuis le dépôt documenté, échoue sur les deux racines. Vérifié :

```text
docs/README.md                         -> FAIL local reference not found
docs/ARCHITECTURE_ET_DEVELOPPEMENT.md  -> FAIL local reference not found
README.md                              -> accepté (nom nu, aucune barre oblique)
```

Sonde du 27/10/2026 (fixture jetable, hors racines de Skills) :

| Forme | Résultat |
| :--- | :--- |
| jeton dossier-fichier.py en prose | vérifié |
| même jeton backtické dans un bloc de code | vérifié |
| lien Markdown dans un bloc de code | vérifié |
| jeton commençant par `$`, `C:`, `/`, `~` ou `..` | ignoré |
| texte nu dans un bloc, sans backticks ni lien | ignoré |

Retirer les backticks pour faire passer la QA supprime la vérification : la forme doit alors être déclarée non vérifiée.

Seul `SKILL.md` est scanné : un jeton fautif dans une référence ne produit pas de FAIL, mais doit être corrigé pour rester cohérent avec le paquet.

### A.2 Trier : racine d'abord, jeton ensuite

Pour chaque FAIL, avant toute réécriture :

1. Tester le jeton sous le dossier du Skill, puis sous chaque racine candidate : `ls "<racine>/<jeton>"` ou `find "<racine>" -path "*/<jeton>" -print`.
2. Tous les jetons existent sous une seule racine projet : changer `--workspace` et ne pas réécrire les jetons. Cas vérifié : neuf FAIL → un seul.
3. Le jeton n'existe nulle part, mais un fichier de même nom existe ailleurs : corriger le jeton seul. Cas vérifié : un FAIL → zéro.
4. Le fichier est créé à l'exécution (plan, acte, cache) : ne pas le présenter comme existant ; nom nu, placeholder, ou forme `$VAR/...`, et déclarer la référence non vérifiée.
5. Deux racines réelles : un seul `--workspace` par passage. Choisir la racine qui maximise les jetons vérifiés, réécrire les autres en `$VAR/...`, et l'écrire dans le rapport. Un `../` ne convient pas : il est ignoré par le validateur.
6. Une seule cause par passe, puis relancer.

### A.3 Correctifs, du plus sûr au plus fragile

1. Changer la racine `--workspace` quand les fichiers existent réellement sous une autre racine : le jeton reste vérifié.
2. Corriger le jeton quand le fichier existe ailleurs sous un autre chemin relatif.
3. Écrire le nom de fichier nu dans le tableau des documents à produire : `README.md`, `ARCHITECTURE_ET_DEVELOPPEMENT.md`. C'est la forme validée sur le cas documenter-passerelle.
4. Utiliser un placeholder avec chevrons, du type `<dossier>/<sujet>.md` : les chevrons font rejeter le jeton.
5. Préfixer par une variable, du type `$RACINE_PROJET/<fichier>` : un jeton commençant par `$` est ignoré.
6. Si le fichier existe réellement dans le paquet, garder le chemin relatif : il se résout dans le dossier du Skill.

Ne pas se contenter de supprimer le jeton : la documentation doit continuer à nommer le fichier concerné. Les formes 3 à 5 ne sont pas vérifiées statiquement (nom nu sans barre oblique, chevrons, variable) ; la forme 6 reste vérifiée. Toute forme non vérifiée doit être signalée comme telle.

### A.4 Sonde reproductible

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

Sonde de racine imbriquée, même principe :

```bash
PROBE=$(mktemp -d "$HOME/.qoder/tmp/ref-root.XXXXXX")
mkdir -p "$PROBE/skill" "$PROBE/parent/systeme/pkg"
: > "$PROBE/parent/systeme/pkg/x.py"
PROBE_TOKEN="pkg/x.py"
{
  printf -- '---\nname: skill\ndescription: "Probe."\n---\n\n'
  printf 'Token : `%s`\n' "$PROBE_TOKEN"
} > "$PROBE/skill/SKILL.md"
QA="$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py"
py -3 "$QA" "$PROBE/skill" --workspace "$PROBE/parent" --stable-seconds 0   # FAIL attendu
py -3 "$QA" "$PROBE/skill" --workspace "$PROBE/parent/systeme" --stable-seconds 0   # PASS attendu
chmod -R u+w "$PROBE"; rm -rf "$PROBE"
```

La seconde racine est celle des chemins documentés, pas la racine Qoder.

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

## C. Commande d'acceptation qui dépend du cwd

### Mécanisme

Un bloc `bash` qui commence par `cd "$R"` puis lance un script via `scripts/<script>.py` : la QA résout le jeton contre le dossier du Skill, où le dossier scripts existe, et PASS ; le shell le résout contre `$R` et échoue. Vérifié sur deux occurrences, corrigées après un PASS 9/0/0.

### Correctif

Rendre la commande indépendante du cwd, sans figer un nom d'utilisateur :

```bash
py -3 -B "$HOME/.qoder/skills/<nom-du-skill>/scripts/<script>.py"
```

Si le script est appelé plusieurs fois dans le bloc :

```bash
SKILL_DIR="$HOME/.qoder/skills/<nom-du-skill>"
py -3 -B "$SKILL_DIR/scripts/<script>.py"
```

Un chemin `C:/Users/<utilisateur>/...` fonctionne mais fige la machine ; `skill-file-qa` demande d'éviter les chemins personnels.

### Preuve

Lancer la commande depuis un répertoire sans rapport, de préférence celui du bloc documenté, et exiger le code de retour attendu. Un PASS de la QA ne remplace pas cette preuve.

### Limite

Les formes `$HOME/...` et les chemins absolus sont ignorés par le validateur : leur existence n'est plus vérifiée statiquement. Le rapport doit le dire.

## Erreurs à ne pas commettre

| Erreur | Effet | Correctif |
| :--- | :--- | :--- |
| Modifier le validateur ou ses attendus | masque le défaut, fausse tous les passages suivants | revenir au validateur d'origine |
| Garde bytecode placée après l'import frère | le cache est écrit avant la garde | déplacer la garde |
| Remplacer un chemin du projet par un autre chemin également faux | même FAIL, cause intacte | vérifier l'existence du nouveau chemin avant de l'écrire |
| Changer `--workspace` sans vérifier que les jetons y existent | même FAIL, autre racine | triage A.2, racine d'abord |
| Laisser un jeton de script relatif dans un bloc exécuté depuis la racine projet | QA PASS, commande cassée | section C, chemin indépendant du cwd |
| Inscrire l'empreinte du fichier de preuves dans lui-même | valeur impossible, fichier instable | `—` + raison, empreinte dans le rapport |
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
- [ ] Racine `--workspace` choisie après vérification d'existence de chaque jeton ; une seule cause par passage.
- [ ] Commande documentée réexécutée depuis le cwd annoncé, code de retour attendu.
- [ ] Aucune auto-empreinte dans le fichier de preuves ; empreinte finale de `SKILL.md` dans le rapport.

## Preuves

Les incidents, leurs sorties exactes, les empreintes et les re-mesures indépendantes sont consignés dans :

- [cas documenter-passerelle du 27/10/2026](references/cas-documenter-passerelle-2026-10-27.md) — références locales prises pour des documents à produire, cache bytecode.
- [cas observateur-triniter du 27/10/2026](references/cas-triniter-2026-10-27.md) — racine imbriquée, jeton faux, commande dépendante du cwd, auto-empreinte et règles de scannage par sonde.
