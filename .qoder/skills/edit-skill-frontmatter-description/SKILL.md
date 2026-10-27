---
name: edit-skill-frontmatter-description
description: "Modifier ou compresser la description d'un SKILL.md proche de 1024 caractères, ajouter ou raccourcir des déclencheurs : inspecter le YAML, simuler chaque ancre sur la valeur parsée (1 occurrence exacte), sauvegarder hors du Skill, remplacer la seule ligne en gardant CRLF, BOM et style de citation, re-parser name, longueur, corps et diff, puis skill-file-qa PASS sur empreinte stable sans nouveau WARN ; vérifier la propagation : Base directory, SHA-256 du corps injecté égal au disque, entrée skill_listing préfixe + ellipse si rechargement, panneau client manuel. Utiliser pour description à 1018, ancre à 0, Edit file changed, WARN de layout, reload skills, 注入正文核对. 中文触发：修改 description、压缩描述、新增触发词、1024 上限、锚点预演、保留 CRLF、目录外备份、YAML 复解析、WARN 基线、skill_listing、description 传播。English: rewrite skill description, 1024 limit, anchor preflight, preserve EOL and quote style, re-parse frontmatter, baseline warn diff, verify injected body and skill listing propagation."
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
14. La propagation se prouve par couches séparées : injection de l'appel, attachement `skill_listing`, panneau client. Une couche non mesurée reste « non vérifiée ».
15. Une entrée de liste sans description avant rechargement est normale ; ne jamais écrire dans `SKILL.md` pour forcer un rechargement.
16. Le JSONL de session se choisit par la ligne d'injection exacte de ce Skill (première ligne égale au dossier résolu), jamais par le `mtime` le plus récent : un fichier récent peut ne contenir aucune injection.
17. Deux longueurs ne se comparent que si elles mesurent le même fichier : `inspect description_len` et `check disk_description_chars` portent sur la cible passée en argument.

## Procédure

Variables utilisées ci-dessous :

```bash
SKILLS_ROOT="$HOME/.qoder/skills"
SKILL_DIR="$SKILLS_ROOT/example-skill"
GUARD="$SKILLS_ROOT/edit-skill-frontmatter-description/scripts/description_guard.py"
PROPAGATION="$SKILLS_ROOT/edit-skill-frontmatter-description/scripts/propagation_check.py"
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

Copier les ancres depuis la valeur parsée, jamais de mémoire : la ponctuation fait partie de l'ancre. Un code de sortie 1 signifie qu'au moins une ancre n'apparaît pas exactement une fois ; abandonner le `Edit` partiel et remplacer la ligne entière à l'étape 5. Capturer le code juste après l'appel (`rc=$?`) ou lancer la commande seule : un `ls` ou un `sha256sum` ajouté au même compound écrase `$?`.

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

Exiger `"dry_run": true`, `"changed": true`, `"new_len"` ≤ 1024, puis recalculer le SHA-256 du fichier pour prouver qu'aucun octet n'a été écrit. Lire le code de retour du garde immédiatement : le dry-run renvoie 0, ne crée ni dossier de sauvegarde ni `.bak` ; un `ls` final sur `--backup-dir` échoue en 2 et masque ce 0.

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

La QA définit le nombre de lignes du corps comme `len(body.splitlines())` après le `---` fermant ; le script utilise la même définition. Sur une copie hors dépôt, les commandes `git` ci-dessus ne produisent rien : utiliser le diff ligne à ligne de la recette d'acceptation.

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

### 9. Vérifier la propagation de la description

Un agent ne peut pas exécuter `/skills reload`. Trois couches distinctes, jamais interchangeables :

| Couche | Preuve | Ce qu'elle ne prouve pas |
|---|---|---|
| Injection à l'appel | message `user`, `isMeta: true`, contenu commençant par `Base directory for this skill:` | le panneau client |
| Liste de Skills | attachement `skill_listing` (`isInitial: true`) du JSONL de session | que le client a rafraîchi |
| Panneau client | action utilisateur | non vérifiable par l'agent |

1. Échantillonner `size`, `mtime_ns` et SHA-256 de `SKILL.md` avant et après l'appel : un appel en lecture seule ne doit rien écrire.
2. Appeler le Skill en lecture seule ; le résultat de l'outil ne contient que `Launching skill:` suivi du nom, sans chemin ni corps.
3. Dans `~/.qoder/projects/$PROJECT_DIR/$SESSION_ID.jsonl`, ne retenir que les messages `type: user`, `isMeta: true`, dont le contenu est une chaîne commençant exactement par `Base directory for this skill:`. Un filtre par sous-chaîne est faux : des sorties d'outils citent la même chaîne plus loin.
4. Exiger que la première ligne déclarée égale le dossier résolu du Skill.
5. Extraire le corps injecté (texte après la première ligne vide), retirer un éventuel bloc final `ARGUMENTS:` ajouté quand le Skill est appelé avec des arguments, puis `strip()` les deux côtés ; comparer son SHA-256 à celui du corps disque `strip()`. Annoncer « identique après normalisation », jamais « octet pour octet » : les longueurs brutes diffèrent (11 807 vs 11 808 dans le cas vérifié).
6. Compter 2 ou 3 fragments du nouveau corps ; exiger ≥ 1 chacun et expliquer tout compte supérieur à 1.
7. Si un `skill_listing` postérieur au `mtime` existe, retrouver l'entrée de liste commençant par `-` puis le nom du Skill, suivie de `: ` et de la description : segment de 300 caractères finissant par `…`, dont les 299 premiers égalent les 299 premiers du disque. Si le dernier attachement précède l'écriture, écrire « liste non vérifiée ».
8. Conclure par « panneau client non vérifié, rafraîchissement manuel » et ne plus écrire dans `SKILL.md` pendant cette phase.

#### 9.0 Identifier la session

`SESSION_ID` ne se déduit ni du JSONL le plus récent ni d'une recherche de sous-chaîne. Pour chaque `~/.qoder/projects/$PROJECT_DIR/*.jsonl`, parser chaque ligne en JSON et compter les messages `type: user`, `isMeta: true`, dont `message.content` est une chaîne commençant exactement par `Base directory for this skill:` et dont la première ligne vaut le dossier résolu du Skill. Retenir le fichier avec au moins une injection ; si plusieurs en ont, prendre celle dont l'horodatage d'injection est le plus récent et le consigner. Écrire le compteur dans un `.py` temporaire hors du Skill, jamais dans un `py -3 -c` contenant un chemin Windows.

Cas vérifié : le JSONL alors le plus récent (`55f63550…`) comptait 0 injection de ce Skill et `check` y renvoie le code 2 `no injection record found` ; `db72d65b…` en comptait au moins une et a produit `INJECTION_OK_LISTING_OK`. Consigner les `mtime` et les comptes par fichier avant de choisir.

Renseigner `PROJECT_DIR` et `SESSION_ID`, puis exécuter le vérificateur :

```bash
SESSION_JSONL="$HOME/.qoder/projects/$PROJECT_DIR/$SESSION_ID.jsonl"
py -3 -B "$PROPAGATION" check "$SKILL_DIR" \
  --session-jsonl "$SESSION_JSONL" \
  --sentinel "fragment 1" --sentinel "fragment 2"
```

Le script exécute les étapes 3 à 7 et renvoie `verdict` : `INJECTION_OK_LISTING_OK`, `INJECTION_OK_LISTING_UNVERIFIED`, `INJECTION_OK_LISTING_MISMATCH` (code 1 : un listing frais contredit la description) ou `FAIL`. Une couche non mesurée reste `unverified` ; `panel` vaut toujours `unverified_manual`.

### 10. Rapport

Consigner : mode, ancienne et nouvelle longueur, ligne, style de citation, EOL, BOM, chemin de sauvegarde, SHA-256 avant/après, comptes QA et nouvel ensemble de WARN, puis le verdict de propagation de l'étape 9.

## Recette d'acceptation sur copie

Exécuter une fois après toute modification du garde ou de la procédure, dans `$HOME/.qoder/tmp/skill-acceptance-<horodatage>/`, sans écrire dans l'installation.

1. Copier un Skill de référence (par exemple `inventory-installed-skills`) en gardant le nom du dossier égal au `name` ; relever `size` et SHA-256 de sa `SKILL.md`.
2. `inspect` la copie ; noter `description_line`, `description_len`, `quote_style`, `eol`, `bom`, `body_lines`.
3. `anchors --require-unique` avec une ancre copiée de la valeur parsée et une ancre absente : exiger `count: 1` / `count: 0` et le code 1 ; abandonner le remplacement partiel.
4. Rédiger un candidat d'une ligne hors du Skill. En dry-run : code 0, `status: would-apply`, SHA-256 inchangé, aucun `.bak`, aucun dossier de sauvegarde.
5. `replace --apply --backup-dir` hors du Skill : `status: applied`, les 12 invariants à `true`, sauvegarde de SHA-256 égal à l'original.
6. Vérifier indépendamment dans un `.py` hors du Skill : même nombre de lignes, seule la ligne de description diffère, autres lignes identiques octet pour octet. `git diff` ne prouve rien sur une copie hors dépôt.
7. Restaurer depuis le `.bak` et exiger un SHA-256 égal à l'original ; lancer `skill-file-qa` avant, après apply et après restauration (mêmes compteurs, `Files (N)` stable).
8. Supprimer le répertoire jetable et vérifier qu'aucun `__pycache__`/`.pyc` n'existe dans l'installation, dont le SHA-256 doit être inchangé.

## Contrat du script

Sortie JSON ASCII échappée, sans traceback. Exécuter avec `py -3 -B` pour éviter `__pycache__`.

| Commande | Entrées | Effet | Codes |
|---|---|---|---|
| `inspect <dir>` | `SKILL.md` unique | lit et mesure, aucune écriture | 0 lisible et éditable ; 1 structure non prise en charge ; 2 environnement |
| `anchors <dir>` | `--anchor` répétable, `--require-unique` | compte chaque ancre sur la description parsée | 0 ; 1 si `--require-unique` et un compte ≠ 1 ; 2 environnement |
| `replace <dir>` | `--candidate-file`, `--backup-dir`, `--apply`, `--expect-sha256` | dry-run par défaut ; écriture ciblée avec sauvegarde et invariants | 0 ; 1 candidat ou invariant ; 2 environnement, EOL mixte, sauvegarde interne, SHA inattendu |
| `check <dir>` | `--session-jsonl` requis, `--sentinel` requis et répétable, `--injection-timestamp` | relit le JSONL, compare injection, corps normalisé et listings ; aucune écriture | 0 injection conforme sans contradiction ; 1 écart ; 2 JSONL absent, aucune injection, sentinelle manquante ou usage |

`replace` refuse : candidat multiligne, vide ou > 1024 ; caractère de contrôle ; valeur qui ne fait pas l'aller-retour dans le style de citation existant ; description multiligne ou clé non top-level ; ligne de description non canonique (commentaire ou contenu supplémentaire) ; sauvegarde dans le Skill.

`disk_description_chars` compte la description parsée de la cible `check` ; ne le comparer qu'à `inspect description_len` sur le même dossier. Un `--session-jsonl` sans injection de ce Skill donne le code 2, pas un verdict. Un dry-run n'écrit ni dossier de sauvegarde ni `.bak` ; capturer son code avant toute autre commande.

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
| `py -3 -c` inline (Git Bash) | chemin Windows dans des guillemets doubles : `SyntaxError: (unicode error) 'unicodeescape' ... position 33-34` | écrire un `.py` temporaire hors du Skill puis lancer `py -3 -B` |
| Entrée de liste sans description | 36 caractères, nom seul à 12:03:43 et 12:04:29 ; description seulement à 12:05:08.952Z | comparer les horodatages au `mtime` ; normal avant rechargement |
| Filtre par sous-chaîne sur `Base directory` | 5 faux positifs dans les sorties d'outils et les scripts de vérification | exiger `type: user`, `isMeta: true` et `startswith` |
| Hash du corps injecté | 11 807 vs 11 808 caractères bruts mais hachages égaux | `strip()` des deux côtés et déclarer la normalisation |
| Appel avec arguments | 16 542 caractères et SHA `7107c5d4…` pour un corps disque à jour : l'injection ajoute 63 caractères `\n\nARGUMENTS: …` | retirer le bloc `ARGUMENTS:` avant le hash (le script le fait) ; ou appeler sans argument |
| JSONL le plus récent | `55f63550…` (alors mtime max) sans injection ; `db72d65b…` en contenait | compter les injections exactes par fichier ; ne pas trier par `mtime` |
| Longueurs croisées | `inspect` 934 sur la fixture, `check` 963 sur l'installation : aucune incohérence | comparer deux mesures du même fichier |
| Code de retour masqué | dry-run à 0, compound affiché à 2 par le `ls` final | lancer le garde seul ou `rc=$?` juste après |
| `git diff` sur une copie | copie hors dépôt : aucune sortie, aucune preuve | diff ligne à ligne en Python hors du Skill |

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
- [ ] Appel lecture seule après écriture ; injection `isMeta` avec dossier exact et hash du corps normalisé égal.
- [ ] Statut de la liste consigné (préfixe 299 + ellipse, ou « non vérifiée ») ; panneau client déclaré manuel.
- [ ] Session choisie par injection exacte, pas par `mtime` ; comptes par fichier consignés.
- [ ] Code de retour de chaque sous-commande capturé juste après l'appel.
- [ ] Longueurs comparées sur la même cible uniquement.
- [ ] Recette d'acceptation exécutée sur copie : dry-run sans octet, invariants, restauration SHA = original, QA aux trois états.
- [ ] Aucun `__pycache__`/`.pyc`, aucun autre Skill modifié.

## Ressources

- [scripts/description_guard.py](scripts/description_guard.py) — `inspect`, `anchors`, `replace` ; dry-run par défaut, sauvegarde externe, invariants et restauration.
- [scripts/propagation_check.py](scripts/propagation_check.py) — `check` : injection, corps normalisé, `skill_listing` ; lecture seule, verdict explicite.
- [references/cas-description-1018-vers-1004.md](references/cas-description-1018-vers-1004.md) — cas vérifié du 2026-10-27, preuves et statuts.
- [references/cas-propagation-reload-2026-10-27.md](references/cas-propagation-reload-2026-10-27.md) — cas vérifié : injection 12:04:32.702Z, `eb2a411c…`, 299 + ellipse.
- [references/cas-acceptation-2026-10-27.md](references/cas-acceptation-2026-10-27.md) — recette exécutée de bout en bout : fixture 934, dry-run 961 sans écriture, restauration SHA identique, QA 9/0/0.

## Skills liés

- `skill-file-qa` : validation statique et empreinte stable.
- `skill-update-concurrency-safe` : concurrence, sauvegardes et édition minimale.
- `bilingual-skill-parity` : parité après modification d'un Skill bilingue.
- `verifier-unicode-fichiers-windows` : assertions exactes sur du texte non ASCII.
- `verify-skill-runtime-binding` : preuve générique du dossier réellement chargé.
- `verify-injected-skill-body-freshness` : fraîcheur du corps injecté lors d'un rechargement. Ici, seule la propagation de la description est traitée ; ces deux Skills restent la référence pour les preuves génériques.
