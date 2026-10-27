---
name: edit-skill-frontmatter-description
description: "Modifier ou compresser la description d'un SKILL.md proche de 1024 caractères, ajouter des déclencheurs ou raccourcir les anciens : inspecter le YAML et mesurer la longueur, préalablement simuler chaque ancre sur la description réelle et exiger exactement une occurrence, sauvegarder hors du dossier du Skill, ne remplacer que la ligne de description en conservant CRLF, BOM et style de citation, puis re-parser et vérifier name, longueur, nombre de lignes du corps et plage de diff, enfin exécuter skill-file-qa et exiger RESULT PASS sur une empreinte stable avec zéro nouveau WARN par rapport à la référence. Utiliser pour description à 1018 caractères, candidat 1139 refusé, ancre sans correspondance, Edit signalant file changed, attribution des WARN de layout. 中文触发：修改 description、压缩描述、新增触发词、1024 上限、锚点预演、保留 CRLF、目录外备份、YAML 复解析、WARN 基线。English: rewrite skill description, 1024 limit, anchor preflight, preserve EOL and quote style, re-parse frontmatter, baseline warn diff."
---

# Éditer la description d'un frontmatter de Skill

## Objectif

Remplacer uniquement la valeur `description` d'un `SKILL.md` lorsque la limite de 1024 caractères approche ou que les déclencheurs doivent changer, avec des invariants vérifiables sur les octets, le YAML et le diff.

## Quand l'utiliser

- la description approche 1024 caractères (par exemple 1018) et il faut ajouter ou compresser des déclencheurs ;
- un remplacement partiel par ancres risque d'échouer sur la ponctuation ;
- `Edit` signale `The file changed since your last read` ;
- il faut conserver CRLF, BOM et style de citation d'un fichier Windows ;
- il faut prouver qu'une seule ligne a changé et que la QA ne gagne aucun WARN.

## Quand ne pas l'utiliser

| Situation | Renvoi |
|---|---|
| description multiligne, flow mapping ou style YAML exotique | corriger la structure manuellement ; le script refuse |
| fins de ligne mixtes | normaliser le fichier avant toute écriture |
| réécriture complète du frontmatter | hors périmètre |
| mise à jour concurrente du paquet | `skill-update-concurrency-safe` |
| contrôle statique final | `skill-file-qa` |
| parité bilingue après la modification | `bilingual-skill-parity` |
| assertion exacte de texte non ASCII | `verifier-unicode-fichiers-windows` |

## Règles non négociables

1. Mesurer avant d'écrire : `inspect` donne la ligne, la longueur, le style de citation et les fins de ligne.
2. Un candidat tient sur une seule ligne, sans CR/LF ni caractère de contrôle, et `len()` ≤ 1024 (points de code, pas octets).
3. Toute ancre de remplacement partiel doit apparaître exactement une fois. Un compte de 0 ou ≥ 2 interdit le `Edit` partiel.
4. Si une ancre échoue, remplacer la ligne de description entière, jamais élargir l'ancre.
5. Pour une description longue (≥ 500 caractères), ne pas utiliser `Edit` : passer par `replace`.
6. Sauvegarde obligatoire hors du dossier du Skill, avec SHA-256 identique à l'original.
7. Seule la ligne de description change ; les autres octets du frontmatter et du corps restent identiques.
8. Conserver le style de fin de ligne, la présence de BOM et le style de citation ; refuser les fins de ligne mixtes.
9. Après écriture, re-parser et vérifier name, autres clés, octets du corps, nombre de lignes et plage de diff.
10. La QA doit tourner sur une empreinte stable et le nouvel ensemble de WARN doit être vide par rapport à la référence.
11. Un PASS de QA ne couvre que l'empreinte mesurée : après toute écriture ultérieure, relancer.
12. `file changed` ou un SHA-256 inattendu impose l'arrêt, la relecture et la reprise ; jamais de remplacement forcé.
13. Enregistrer séparément les SHA-256 de `SKILL.md` et de chaque référence modifiée.

## Procédure

Variables utilisées ci-dessous :

```bash
SKILLS_ROOT="$HOME/.qoder/skills"
SKILL_DIR="$SKILLS_ROOT/example-skill"
GUARD="$SKILLS_ROOT/edit-skill-frontmatter-description/scripts/description_guard.py"
CANDIDATE="$HOME/.qoder/tmp/desc-candidates/candidate.txt"
BACKUP_DIR="$HOME/.qoder/tmp/skill-backup/example-skill"
```

### 0. Référence et QA de départ

Enregistrer `size`, `mtime`, SHA-256 et l'ensemble trié des WARN avant toute modification :

```bash
sha256sum "$SKILL_DIR/SKILL.md"
py -3 -B "$SKILLS_ROOT/skill-file-qa/scripts/validate_skill.py" "$SKILL_DIR" \
  --workspace "$PWD" | tee "$HOME/.qoder/tmp/qa-before.txt"
```

Un PASS de départ n'est pas obligatoire, mais les WARN existants deviennent la référence. Ne pas attribuer à cette édition un WARN déjà présent.

### 1. Mesurer

```bash
py -3 -B "$GUARD" inspect "$SKILL_DIR"
```

Lire au minimum `description_line`, `description_len`, `remaining`, `quote_style`, `eol`, `bom`, `body_lines` et `sha256`. La ligne est en base 1 ; le script convertit les marques PyYAML (base 0 dans le frontmatter) vers le numéro physique.

### 2. Rédiger les candidats

Écrire chaque candidat dans un fichier hors du dossier du Skill, une seule ligne, puis mesurer :

```bash
mkdir -p "$(dirname "$CANDIDATE")"
py -3 -B -c "import io,sys; s=io.open(sys.argv[1],encoding='utf-8').read().rstrip('\r\n'); print(len(s), 1024-len(s))" "$CANDIDATE"
```

Conserver les longueurs dans le rapport. Un candidat à 1139 est refusé ; 1016, 1008 et 1004 passent. Ne jamais écrire le candidat dans `$SKILL_DIR`.

### 3. Préflight des ancres

Pour un remplacement partiel :

```bash
py -3 -B "$GUARD" anchors "$SKILL_DIR" \
  --anchor "premier fragment exact" \
  --anchor "second fragment exact" \
  --require-unique
```

Copier les ancres depuis la valeur parsée, jamais de mémoire : la ponctuation fait partie de l'ancre. Un code de sortie 1 signifie qu'au moins une ancre n'apparaît pas exactement une fois ; abandonner le `Edit` partiel et remplacer la ligne entière à l'étape 5.

### 4. Sauvegarde

`replace --apply` exige `--backup-dir` hors du dossier du Skill, écrit `SKILL.md.<UTC>.bak` et vérifie le SHA-256. Ne jamais placer la sauvegarde dans le Skill : elle entrerait dans le décompte de fichiers de la QA.

Équivalent manuel :

```bash
mkdir -p "$BACKUP_DIR"
cp -a "$SKILL_DIR/SKILL.md" "$BACKUP_DIR/SKILL.md.$(date -u +%Y%m%dT%H%M%SZ).bak"
sha256sum "$SKILL_DIR/SKILL.md" "$BACKUP_DIR"/*.bak
```

### 5. Dry-run

```bash
py -3 -B "$GUARD" replace "$SKILL_DIR" \
  --candidate-file "$CANDIDATE" \
  --backup-dir "$BACKUP_DIR"
```

Exiger `"dry_run": true`, `"changed": true`, `"new_len"` ≤ 1024, puis recalculer le SHA-256 du fichier pour prouver qu'aucun octet n'a été écrit.

### 6. Apply

```bash
sha_before=$(sha256sum "$SKILL_DIR/SKILL.md" | cut -d' ' -f1)
py -3 -B "$GUARD" replace "$SKILL_DIR" \
  --candidate-file "$CANDIDATE" \
  --backup-dir "$BACKUP_DIR" \
  --expect-sha256 "$sha_before" \
  --apply
```

Le script re-vérifie le SHA-256 immédiatement avant l'écriture, sauvegarde, écrit de façon atomique, re-parse puis restaure les octets d'origine si un invariant échoue. Un résultat `"restored": true` est un échec : diagnostiquer avant de réessayer.

### 7. Vérification structurelle indépendante

```bash
py -3 -B "$GUARD" inspect "$SKILL_DIR"
sha256sum "$SKILL_DIR/SKILL.md" "$BACKUP_DIR"/*.bak
git -C "$SKILL_DIR" diff --stat -- SKILL.md 2>/dev/null || true
git -C "$SKILL_DIR" diff --unified=0 -- SKILL.md 2>/dev/null || true
```

Confirmer :

- `name` inchangé et longueur de description égale à celle du candidat ;
- nombre de lignes du corps inchangé pour une édition limitée à la description ;
- diff limité à la ligne de description ;
- comptes CRLF/LF et présence de BOM inchangés.

La QA définit le nombre de lignes du corps comme `len(body.splitlines())` après le `---` fermant ; le script utilise la même définition.

### 8. QA et attribution des WARN

```bash
py -3 -B "$SKILLS_ROOT/skill-file-qa/scripts/validate_skill.py" "$SKILL_DIR" \
  --workspace "$PWD" | tee "$HOME/.qoder/tmp/qa-after.txt"
diff <(grep '^WARN' "$HOME/.qoder/tmp/qa-before.txt" | sort) \
     <(grep '^WARN' "$HOME/.qoder/tmp/qa-after.txt" | sort) || true
```

- Exiger `RESULT PASS`, code de sortie 0 et empreinte stable.
- Le nouvel ensemble de WARN doit être vide ; un simple décompte identique ne suffit pas.
- Dans le cas de référence, les 10 WARN viennent d'un `.gitattributes` et d'archives `.qoder/skills/...` déjà présents ; ils ne sont pas causés par l'édition.
- Si le corps a aussi été édité, le nombre de lignes peut légitimement changer ; limiter l'invariant « corps identique » à l'étape de description seule.

### 9. Rapport

Consigner : mode, ancienne et nouvelle longueur, ligne, style de citation, EOL, BOM, chemin de sauvegarde, SHA-256 avant/après, comptes QA et nouvel ensemble de WARN.

Propagation : un agent ne peut pas exécuter `/skills reload` ; le rafraîchissement du panneau client reste manuel. La pièce jointe de liste de Skills dans le JSONL de session peut être comparée à la description sur disque, mais elle ne prouve que la couche liste.

## Contrat du script

Sortie JSON ASCII échappée, sans traceback. Exécuter avec `py -3 -B` pour éviter `__pycache__`.

| Commande | Entrées | Effet | Codes |
|---|---|---|---|
| `inspect <dir>` | `SKILL.md` unique | lit et mesure, aucune écriture | 0 lisible et éditable ; 1 structure non prise en charge ; 2 environnement |
| `anchors <dir>` | `--anchor` répétable, `--require-unique` | compte chaque ancre sur la description parsée | 0 ; 1 si `--require-unique` et un compte ≠ 1 ; 2 environnement |
| `replace <dir>` | `--candidate-file`, `--backup-dir`, `--apply`, `--expect-sha256` | dry-run par défaut ; écriture ciblée avec sauvegarde et invariants | 0 ; 1 candidat ou invariant ; 2 environnement, EOL mixte, sauvegarde interne, SHA inattendu |

`replace` refuse : candidat multiligne, vide ou > 1024 ; caractère de contrôle ; valeur qui ne fait pas l'aller-retour dans le style de citation existant ; description multiligne ou clé non top-level ; ligne de description non canonique (commentaire ou contenu supplémentaire) ; sauvegarde dans le Skill.

## Pièges vérifiés

| Piège | Symptôme observé | Réaction |
|---|---|---|
| Ancre copiée de mémoire | `最终三方哈希；用于` et `cleanup pending."` comptent 0 ; le texte réel utilise « 。 » et une virgule | compter sur la valeur parsée ; abandonner le partiel |
| Candidat non mesuré | 1139 caractères, refusé par la limite 1024 | mesurer avant l'écriture |
| Marques PyYAML | `desc lines [2]` pour la troisième ligne physique | base 0 dans le frontmatter, base 1 dans le rapport |
| `Edit` concurrent | `The file changed since your last read` | arrêter, relire, re-sampler |
| CRLF | une lecture en mode texte universel réécrit les fins de ligne | lire les octets et découper en conservant les fins de ligne |
| Style de citation | guillemets doubles, simples ou plain ont des échappements différents | conserver le style ; refuser si l'aller-retour échoue |
| BOM | préservé par le script, mais la QA échoue si `SKILL.md` commence par un BOM | rapporter ; ne pas retirer silencieusement |
| Console Windows | `UnicodeEncodeError` en cp1252 sur du texte non ASCII | sortie JSON `ensure_ascii=True` |
| Nombre de lignes | 308 lignes au moment du remplacement, 337 après des éditions de corps dans la même session | limiter l'invariant à l'étape description seule |
| WARN de layout | 10 WARN préexistants dus à `.gitattributes` et aux archives `.qoder/skills/...` | comparer les ensembles, pas seulement les comptes |
| Longueur | `len()` compte les points de code, pas les octets UTF-8 | ne pas utiliser la taille du fichier |

## Checklist finale

- [ ] `inspect` exécuté avant toute écriture ; ligne, longueur, style, EOL et BOM enregistrés.
- [ ] Chaque ancre compte exactement 1, ou le remplacement partiel a été abandonné.
- [ ] Candidat sur une ligne, ≤ 1024 points de code, style de citation compatible.
- [ ] Sauvegarde hors du dossier du Skill et SHA-256 identique.
- [ ] Dry-run sans modification d'octet.
- [ ] Apply avec `--expect-sha256`, invariants tous vrais, aucune restauration.
- [ ] Diff limité à la ligne de description ; corps et autres clés identiques.
- [ ] QA `RESULT PASS` sur empreinte stable, zéro nouveau WARN.
- [ ] SHA-256 de `SKILL.md` et des références enregistrés séparément.
- [ ] Aucun `__pycache__`/`.pyc`, aucun autre Skill modifié.

## Ressources

- [scripts/description_guard.py](scripts/description_guard.py) — `inspect`, `anchors`, `replace` ; dry-run par défaut, sauvegarde externe, invariants et restauration.
- [references/cas-description-1018-vers-1004.md](references/cas-description-1018-vers-1004.md) — cas vérifié du 2026-10-27, preuves et statuts.

## Skills liés

- `skill-file-qa` : validation statique et empreinte stable.
- `skill-update-concurrency-safe` : concurrence, sauvegardes et édition minimale.
- `bilingual-skill-parity` : parité après modification d'un Skill bilingue.
- `verifier-unicode-fichiers-windows` : assertions exactes sur du texte non ASCII.
