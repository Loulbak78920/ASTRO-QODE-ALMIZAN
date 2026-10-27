---
name: exporter-rapport-markdown-pdf-windows
description: "Transformer un rapport Markdown en aperçu HTML puis en PDF sur Windows : quand assoc .md/.pdf échoue et que start renvoie 0 sans fenêtre, ouvrir via Chrome ou VS Code ; rendre avec le script Python stdlib (titres, tableaux, listes ordonnées/désordonnées, code inline protégé) et un CSS A4 avec page-break-inside: avoid ; exporter par Chrome headless --print-to-pdf --no-pdf-header-footer ; puis vérifier %PDF-, %%EOF, /Type /Page, pages et texte extractible via pypdf avec sortie ASCII. Utiliser pour 把 Markdown 汇报导出为 PDF、生成浏览器预览、打开 .md 或 .pdf 无反应、文件关联缺失、UnicodeEncodeError cp1252、Chrome headless 导出或 PDF 页数与文本验收。"
---

# Exporter un rapport Markdown en HTML et PDF (Windows)

## Quand l'utiliser

- Un rapport `.md` doit être livré en aperçu lisible puis en PDF.
- `start fichier.md` renvoie 0 mais aucune fenêtre ne s'ouvre, ou `assoc .md` / `assoc .pdf` répond « Association de fichier introuvable ».
- Il faut une preuve reproductible que le PDF n'est pas vide et que son texte est extractible.
- Un rendu maison a déjà fusionné les listes ordonnées dans un paragraphe, ou un script Python a échoué en `UnicodeEncodeError` sur une console cp1252.

Ne pas l'utiliser pour du Markdown non fiable (le HTML produit n'est pas assaini), ni pour reproduire une mise en page Word à l'identique.

## Prérequis

- `py -3` : l'alias `python` de ce poste est un stub Microsoft Store et échoue.
- Google Chrome installé ; le script le découvre via les chemins connus et la base de registre `App Paths`.
- `pypdf` pour l'extraction de texte.

```bash
py -3 -c "import pypdf, sys; print('pypdf', pypdf.__version__, 'py', sys.version.split()[0])"
test -f "/c/Program Files/Google/Chrome/Application/chrome.exe" && echo chrome=ok
```

Installer `pypdf` si absent : `py -3 -m pip install pypdf`.

Définir une fois le dossier du Skill, puis exécuter les commandes depuis le dossier du rapport :

```bash
SKILL_DIR="$HOME/.qoder/skills/exporter-rapport-markdown-pdf-windows"
```

## Workflow

### 1. Confirmer l'entrée

Se placer dans le dossier du rapport, puis :

```bash
ls -l rapport.md
```

Lire le Markdown pour relever la structure attendue : nombre de H1/H2, tableaux, listes, blocs de code. Ces nombres servent d'assertions à l'étape 2.

### 2. Rendre le HTML et vérifier la structure

```bash
py -3 -B "$SKILL_DIR/scripts/rendre_md.py" rapport.md rapport.html \
  --check "h1=1,h2=7,table=2,ul=1,ol=1,li=8,pre=1"
```

Remplacer les valeurs par celles du rapport réel. Sortie attendue (tailles et compteurs dépendent du rapport ; les clés et `RESULT=PASS` sont stables) :

```text
OK rapport.html 5620 octets
COUNTS h1=1 h2=7 table=2 ul=1 ol=1 li=8 pre=1 code_inline=12
CLEAN backticks=0 pipe_lines=0
RESULT=PASS
```

- `li` compte toutes les entrées ; `ol` et `ul` comptent les groupes. Un rapport avec 3 étapes numérotées doit donner `ol` ≥ 1 et `li` ≥ 3.
- `backticks=0` et `pipe_lines=0` prouvent qu'aucun marqueur Markdown n'a fui dans le HTML.
- Si `ol=0` alors que la source contient `1.`, `2.`, `3.`, le détecteur de listes a échoué : ne pas exporter ce HTML, corriger le rendu d'abord.

Le script écrit de l'UTF-8, ajoute le CSS d'impression A4 et laisse intact le Markdown source.

### 3. Ouvrir l'aperçu dans Chrome

```bash
start chrome "file:///$(pwd -W)/rapport.html"
```

Ne jamais conclure depuis le code retour : `start` renvoie 0 même sans association. Confirmer par le titre de fenêtre :

```bash
powershell -NoProfile -Command "Get-Process chrome | Where-Object { \$_.MainWindowTitle } | Select-Object -ExpandProperty MainWindowTitle"
```

Repli si `start chrome` échoue : ouvrir le `.md` avec VS Code (`code --reuse-window rapport.md`, ou `Code.exe --reuse-window`), puis `Ctrl+Shift+V` pour l'aperçu Markdown natif. Le repli Chrome reste obligatoire pour le PDF.

### 4. Exporter le PDF

```bash
py -3 -B "$SKILL_DIR/scripts/exporter_pdf.py" rapport.html rapport.pdf --min-chars 200
```

Sortie attendue (clés stables, valeurs variables) :

```text
CHROME=C:\Program Files\Google\Chrome\Application\chrome.exe
PDF=rapport.pdf
CHROME_RC=0
PDF_BYTES=78978
HEADER=%PDF-1.4
TAIL_EOF=1
PAGE_OBJ=2
COUNT=2
PYPDF_PAGES=2
P1_CHARS=564
RESULT=PASS
```

- `--min-chars` est un plancher de sanity-check, pas une preuve de fidélité visuelle. L'ajuster au rapport ; 200 convient à une page de texte.
- `PAGE_OBJ` est un comptage brut d'objets `/Type /Page` ; `PYPDF_PAGES` fait foi. Un écart signale un PDF atypique, pas forcément une erreur.
- Le script supprime d'abord la cible existante et affiche `OVERWRITE=1` : le PDF validé est toujours celui de cette exécution.
- `--chrome CHEMIN` force un binaire ; `--timeout` (défaut 180 s) borne l'attente.

### 5. Ouvrir le PDF

```bash
start chrome "file:///$(pwd -W)/rapport.pdf"
```

Même piège d'association que pour `.md`. Vérifier le titre de fenêtre, ou se contenter des clés de l'étape 4 si l'ouverture n'est pas demandée.

### 6. Nettoyage

Conserver le `.md` et le `.pdf`. Si le HTML et une copie du script ont été créés dans `%TEMP%`, les supprimer uniquement après l'export validé, et confirmer que le dossier n'existe plus. Ne jamais placer de rapport dans un paquet Skill : `skill-file-qa` interdit les documents de type README/rapport à la racine d'un Skill.

## Codes retour et clés

| Script | 0 | 1 | 2 |
|---|---|---|---|
| `rendre_md.py` | HTML écrit, contrôles OK | `CHECK_FAIL` (structure ou marqueurs résiduels) | usage, entrée absente, E/S |
| `exporter_pdf.py` | PDF valide et texte extractible | Chrome en échec, PDF invalide, texte sous `--min-chars` | usage, HTML absent, Chrome introuvable, pypdf absent |

Clés d'échec : `ERROR entree_absente=`, `ERROR html_absent=`, `ERROR chrome_introuvable=1`, `OVERWRITE=1`, `ANOMALIES=entete,queue,taille,aucune_page,texte_insuffisant,pypdf_lecture`, `CHROME_RC=`, `CHROME_STDERR=`.

## Pièges vérifiés sur ce poste

| Symptôme | Cause mesurée | Action |
|---|---|---|
| `start` rc=0, aucune fenêtre | `.md` et `.pdf` sans association : `assoc` → « Association de fichier introuvable », rc=1 | `start chrome file:///...` ou VS Code ; ne pas réessayer `start` seul |
| `python` renvoie le code 49 | alias Microsoft Store | `py -3` |
| `UnicodeEncodeError: 'charmap' ... cp1252` | impression de texte chinois extrait du PDF | ne pas imprimer le texte ; les scripts sortent en ASCII, sinon `PYTHONIOENCODING=utf-8` |
| Étapes `1. 2. 3.` fusionnées dans un paragraphe | liste numérotée non reconnue avant l'accumulation du paragraphe | exiger `ol` et `li` via `--check` ; le rendu livré détecte les listes sans ligne vide préalable |
| `Cannot find module 'marked'` | dépendance Node absente | utiliser `rendre_md.py`, sans dépendance externe |
| En-tête/pied de page Chrome dans le PDF | option d'impression par défaut | `--no-pdf-header-footer` (déjà dans le script) |
| Tableau ou bloc de code coupé entre deux pages | pagination automatique | CSS print `page-break-inside: avoid` (déjà dans le gabarit) |
| PDF apparemment valide mais rc=1 | le script imprimait le texte CJK puis mourait en cp1252 après les contrôles | se fier aux clés `HEADER`, `TAIL_EOF`, `PYPDF_PAGES`, `P1_CHARS`, pas au seul code retour d'un one-liner |

## Limites

- Le rendu couvre titres, paragraphes, tableaux GFM simples, listes à un niveau, blocs de code, gras/italique, liens et code inline. Pas de listes imbriquées, citations, images, notes ni liens de référence.
- Les lignes douces sont jointes par un espace, sauf entre deux caractères CJK.
- La fidélité PDF dépend des polices installées ; le texte CJK exige une police système disponible.
- `--min-chars` prouve seulement qu'il existe du texte extractible, pas que la mise en page est correcte.

## Ressources

- `scripts/rendre_md.py` : Markdown → HTML autonome, comptage et assertions.
- `scripts/exporter_pdf.py` : Chrome headless, export et vérification PDF.
- `references/preuves-session-2026-10-27.md` : valeurs mesurées dans la session source et points non vérifiés.
- Skills liés : `skill-file-qa` (layout et validation), `windows-python-utf8-skill-scripts` (sortie UTF-8 Windows), `validation-navigateur-par-repli` (validation HTML sans capture), `verifier-livrables-csv-html-windows-fr` (contrôles cp1252 et livrables HTML).
