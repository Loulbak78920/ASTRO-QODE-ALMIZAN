---
name: appliquer-lot-edits-skill-script-assertions
description: "Assembler un lot de modifications d'un SKILL.md par script à ancres uniques : inventaire des edits labellisés, sauvegarde et empreintes hors du Skill, brouillon généré avec assertion count==1 par ancre exacte, bornée par section ou par remplacement de section, arrêt avant écriture sur count=0 ou count>=2, diff réduit aux hunks attendus, budgets description et body recalculés, YAML et fences contrôlés, puis installation octet à octet avec SHA-256 égal et QA finale. Utiliser pour 10 edits ou plus dans un fichier proche de 500 lignes, FAIL label count=0, ancre consommée par une substitution antérieure, brouillon hors du Skill, hunk inattendu, dépassement de budget, CRLF et BOM. 中文触发：批量修改 SKILL.md、唯一锚点断言、count=0、顺序陷阱、草稿 diff、字节级安装、哈希相等、正文预算、description 1024、备份回滚。English: batch edit SKILL.md, unique anchor assertion, order trap, draft diff gate, byte-identical install, body budget."
---

# Appliquer un lot d'éditions à un SKILL.md par script

## Objectif

Appliquer dix éditions ou plus dans un `SKILL.md` sans perdre le contrôle : chaque ancre est vérifiée exactement une fois avant toute écriture, le résultat est d'abord un brouillon hors du Skill, le diff est inspecté, les budgets sont recalculés, et seule une copie octet à octet vérifiée remplace le fichier installé.

## Quand l'utiliser

- la mise à jour touche 10 edits ou plus, ou plusieurs sections d'un fichier proche de 500 lignes ;
- une édition manuelle a déjà échoué sur `The file changed since your last read` ou sur une ancre devenue introuvable ;
- une substitution antérieure a consommé le texte qu'une ancre ultérieure visait (piège d'ordre) ;
- il faut prouver que le diff ne contient que les hunks attendus, et que le budget `description`/`body` reste respecté ;
- le fichier est en CRLF, avec ou sans BOM, et les octets doivent être préservés.

## Quand ne pas l'utiliser

| Situation | Renvoi |
|---|---|
| une ou deux éditions indépendantes, ancres stables | `skill-update-concurrency-safe` (Edit minimal) |
| seule la ligne `description` change | `edit-skill-frontmatter-description` |
| le contenu à écrire n'est pas encore tranché | `verify-skill-doc-claims-before-edit` |
| il faut d'abord arbitrer la taille du paquet | `planifier-budget-paquet-skill` |
| contrôle statique final après écriture | `skill-file-qa` |
| d'autres sessions écrivent le même Skill pendant l'opération | `skill-update-concurrency-safe`, puis revenir ici |

## Règles non négociables

1. Le fichier source est ouvert en lecture seule ; le script n'écrit que le brouillon.
2. Toute ancre `exact` doit apparaître exactement une fois dans le texte entier ; `section` et `scoped` exigent un début et une fin uniques, dans cet ordre.
3. `count == 0` et `count >= 2` sont des échecs, pas des avertissements : aucun brouillon n'est écrit.
4. Une ancre qui échoue n'est jamais élargie ni reformulée à l'aveugle ; on relit le texte réel et on corrige la spec.
5. Les edits s'appliquent dans l'ordre de la liste : une substitution peut consommer le texte d'une ancre suivante. Les ancres sont écrites dans leur forme finale, pas dans leur forme d'origine.
6. Le brouillon vit hors du dossier du Skill ; un fichier temporaire dans le Skill fausse le décompte de fichiers de la QA.
7. Les fins de ligne mixtes et les fichiers CR seul sont refusés : le script s'arrête au chargement.
8. Le brouillon reprend l'EOL et le BOM de la source ; un passage en LF est un échec de conservation.
9. Le diff complet est lu avant installation, avec le nombre de hunks attendu ; `CHANGED_RANGES` localise, il ne prouve pas l'intention.
10. Les budgets `body` (< 500) et `description` (<= 1024, via PyYAML) sont des portes : dépassement = pas d'installation.
11. L'installation est une copie d'octets vérifiée par SHA-256 entre brouillon et fichier installé, jamais un `Write` de texte reformaté.
12. Après installation, la QA tourne sur l'empreinte installée ; une écriture ultérieure invalide ce PASS.
13. En cas d'écart après installation, la sauvegarde hors du Skill est la seule source de restauration.
14. Aucun PASS de QA ni aucune sortie `RESULT OK` ne prouve la justesse du diff ; c'est l'inventaire de l'étape 1 qui la porte.

## Procédure

Variables utilisées ci-dessous :

```bash
SKILLS_ROOT="$HOME/.qoder/skills"
SKILL_DIR="$SKILLS_ROOT/example-skill"
ASM="$SKILLS_ROOT/appliquer-lot-edits-skill-script-assertions/scripts/assembler.py"
WORK="$HOME/.qoder/tmp/lot-edits/<skill-name>"
SRC="$SKILL_DIR/SKILL.md"
SPEC="$WORK/spec.py"
DRAFT="$WORK/SKILL.draft.md"
```

### 0. Préflight

```bash
mkdir -p "$WORK"
test -f "$SRC" || { echo "MISSING source"; exit 2; }
sha256sum "$SRC"
stat -c '%s bytes | %y' "$SRC"
```

Le dossier `$WORK` est hors du Skill : backups, spec, brouillon et diff y restent. Si `$WORK` contient déjà un brouillon d'une tentative précédente, le supprimer avant de recommencer.

### 1. Inventaire des edits

Lister chaque changement sous forme `(type, label, ancres, texte)`, avec le label tel qu'il apparaîtra dans la sortie. Un label décrit l'intention (`rename-heading`, `fix-step5-anchor`), jamais un numéro d'ordre seul.

- `exact` : ancre unique dans tout le fichier.
- `section` : `START` et `END` uniques ; le texte strictement entre eux est remplacé, les deux bornes restent.
- `scoped` : mêmes bornes, puis une suite de remplacements ordonnés avec, pour chacun, le nombre d'occurrences attendu.

Compter les edits et vérifier que chaque texte remplacé existe réellement sur disque. Un edit sans ancre vérifiée n'entre pas dans la spec.

### 2. Sauvegarde et empreintes

```bash
BACKUP="$WORK/SKILL.before.md"
cp -a "$SRC" "$BACKUP"
sha256sum "$SRC" "$BACKUP"
find "$SKILL_DIR" -type f -exec sha256sum {} + | sort
```

La sauvegarde doit porter le même SHA-256 que la source. La liste complète des fichiers sert de référence pour repérer un ajout concurrent.

### 3. Écrire la spec

```python
EDITS = [
    ("exact", "rename-heading", "## Ancien titre", "## Nouveau titre"),
    ("scoped", "fix-order", "## Étape 5", "## Étape 6", [
        ('"$DEPOT"', '"$VERIF"', 3),
        ('git -C "$VERIF" merge', "git -C \"$VERIF\" merge --ff-only origin/main", 1),
    ]),
    ("section", "rewrite-step6", "## Étape 6", "## Échecs fréquents", "Nouveau contenu\n"),
]
```

La spec est un module Python chargé par `--spec` ; elle ne fait qu'exposer `EDITS`. Les ancres sont écrites en LF ; le script les normalise et restitue l'EOL de la source.

### 4. Préflight des ancres (brouillon sec)

```bash
py -3 -B "$ASM" --source "$SRC" --inspect
```

`LOAD`, `BODY`, `DESC`, `FENCES`, `H2` donnent l'état réel avant modification. Un `FAIL eol: mixed line endings` ici interdit toute la suite : normaliser le fichier est une décision séparée.

### 5. Assembler le brouillon

```bash
py -3 -B "$ASM" --source "$SRC" --out "$DRAFT" --spec "$SPEC" \
  --body-max 500 --desc-max 1024
```

Sortie attendue en cas de succès :

```
LOAD source=... bytes=... lines=... eol=... bom=...
SPEC edits=<n>
APPLY <label> (<kind>)
DRAFT out=... bytes=... lines=... eol=... bom=...
BODY n (< 500)
DESC n (<= 1024, ...)
FENCES n (even)
H2 n
CHANGED n
CHANGED_RANGES ...
RESULT OK
```

En cas d'échec : `FAIL <label>: <message>` puis `RESULT FAIL applied=k/total`, aucun brouillon écrit, code de sortie 1. Codes : 0 = OK, 1 = ancre ou budget, 2 = usage ou E/S (source illisible, spec invalide, sortie égale à la source).

### 6. Lire le diff

```bash
diff -U0 "$SRC" "$DRAFT" > "$WORK/diff.txt" || true
grep -c '^@@' "$WORK/diff.txt"
grep -c '^[-+][^-+]' "$WORK/diff.txt"
```

Avec `-U0`, chaque hunk correspond à une plage de `CHANGED_RANGES` : le nombre de hunks doit égaler `CHANGED`. `diff -u` sans `-U0` fusionne les changements séparés par au plus 6 lignes inchangées et produit donc moins de hunks : l'utiliser seulement pour lire le contexte, jamais pour compter. Chaque hunk doit correspondre à un edit inventorié ; un hunk de plus, ou un hunk qui touche une zone hors inventaire, arrête la procédure : relire le fichier, corriger la spec, régénérer. Les lignes `-`/`+` se comptent par `grep -c '^[-+][^-+]'`, qui exclut les en-têtes du diff.

### 7. Budgets et forme

```bash
py -3 -B "$ASM" --source "$DRAFT" --inspect
py -3 -B "$SKILLS_ROOT/skill-file-qa/scripts/validate_skill.py" "$SKILL_DIR" \
  --workspace "$PWD" | tee "$WORK/qa-before-install.txt"
```

Sur le brouillon : `BODY < 500`, `DESC <= 1024`, `FENCES` pair, aucun `FAIL`. La QA sur le dossier installé à ce stade décrit l'ancien fichier : elle sert de référence, pas de preuve.

### 8. Installation octet à octet

```bash
cp "$DRAFT" "$SRC"
sha256sum "$DRAFT" "$SRC"
py -3 -B "$SKILLS_ROOT/skill-file-qa/scripts/validate_skill.py" "$SKILL_DIR" \
  --workspace "$PWD" | tee "$WORK/qa-after.txt"
```

Le SHA-256 du brouillon et du fichier installé est identique ; la QA finale doit n'avoir aucun FAIL et son `Files (N)` doit rester celui attendu. En cas d'écart, restaurer depuis `$BACKUP` et recommencer, sans réécrire le brouillon à la main.

Nettoyage : supprimer `$WORK` après avoir noté les empreintes et les sorties ; conserver `$BACKUP` tant que la modification n'est pas validée par un tour ultérieur.

## Échecs fréquents

| Symptôme | Cause | Action |
|---|---|---|
| `FAIL <label>: count=0 expected=1` | l'ancre n'existe pas sous cette forme, ou a été consommée par un edit antérieur | relire le texte réel ; replacer la ligne du nouvel état, recompter |
| `FAIL <label>: start count=0 expected=1` ou `end count=0 expected=1` | borne de section introuvable | vérifier les deux titres, dans l'ordre |
| `FAIL <label>: count=18 expected=1` | ancre trop courte ou trop générique | allonger l'ancre avec le contexte voisin, jamais avec un motif plus large |
| `FAIL <label>: count=N expected=M` | `scoped` avec un compte prévu faux | recompter les occurrences dans la tranche, corriger `M`, ne pas élargir |
| `FAIL eol: mixed line endings` | fichier mêlant CRLF et LF | traiter la normalisation comme une décision explicite, hors de ce flux |
| `ERROR out must differ from source` | `--out` pointe sur la source | écrire dans `$WORK` |
| `FAIL budget: BODY 502 >= 500` | brouillon trop long | comprimer les edits, pas le seuil |
| `FAIL budget: DESC 1031 > 1024` | description surdimensionnée | compresser les déclencheurs avant de relancer |
| `RESULT OK` mais hunk inattendu | `CHANGED` ne valide pas l'intention | comparer chaque hunk à l'inventaire de l'étape 1 |
| `FENCES` impair | bloc de code ouvert par un edit | relire les edits qui touchent des fences, corriger, régénérer |
| `count=1` mais texte final faux | ancre correcte, remplacement mal écrit | relire le remplacement, pas l'ancre |

## Ressources

- `scripts/assembler.py` : assembleur (`--inspect`, `--self-test`, `--source`, `--out`, `--spec`, `--body-max`, `--desc-max`), contrat `EDITS` en tête de fichier ; `--self-test` couvre exact, section, scoped, ancre absente, ancre dupliquée, piège d'ordre, budget, EOL mixte, BOM conservé.
- `references/evidence-2026-10-28.md` : session source `0ffdb70b` — 498 lignes au départ, 23 remplacements `sub1` labellisés (dont un insère un bloc), échec `step5-merge2: count=0`, brouillon 500 lignes, QA 9 pass / 0 fail / 0 warn, chiffres et empreintes reprises ; cas « diff limité aux hunks attendus » revu manuellement.

## Limites

- Le script écrit le brouillon et s'arrête là : il n'installe pas, ne lance pas la QA, ne restaure pas.
- `CHANGED_RANGES` donne les plages modifiées, pas leur conformité ; l'équivalence aux hunks attendus reste une lecture humaine du diff.
- La conservation CRLF/BOM est vérifiée, pas la conservation des permissions ni des métadonnées du fichier.
- Le flux ne protège pas contre une écriture concurrente du Skill : préflight, sauvegarde et relecture finale restent nécessaires.
- Un fichier dont seule la description change relève du flux dédié, plus court ; ce Skill n'apporte rien de plus pour une ou deux ancres.
- Aucune garantie que le contenu rédigé est exact : les faits doivent avoir été vérifiés avant l'étape 3.

## Modèle de rapport

```
Skill: <skill-name>
Source: SHA-256 <hash> | <n> bytes | <n> lignes | EOL <LF|CRLF> | BOM <True|False>
Inventaire: <n> edits (exact=<n>, section=<n>, scoped=<n>)
Brouillon: SHA-256 <hash> | BODY <n> | DESC <n> | FENCES <n> (even) | CHANGED <n>
Diff: <n> hunks, attendus <n> — <conformes|écart: détail>
Installation: SHA-256 brouillon == installé : <oui|non>
QA: <pass> pass / <fail> fail / <warn> warn | Files (<n>) | Fingerprint <hash>
Restauration: <inutile|faite depuis $BACKUP>
Non vérifié: <liste>
```
