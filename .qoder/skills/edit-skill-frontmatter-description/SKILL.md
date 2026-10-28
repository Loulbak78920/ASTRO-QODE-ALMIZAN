---
name: edit-skill-frontmatter-description
description: "Modifier ou compresser la description d'un SKILL.md proche de 1024 caractères. 触发：修改 description、压缩描述、新增触发词、可见性预算、299 字符、清单截断、写后新会话、1024 上限、锚点预演、保留 CRLF、YAML 复解析、WARN 基线、skill_listing、description 传播。Inspecter le YAML, vérifier chaque ancre (1 occurrence, sinon ligne entière), sauvegarder hors du Skill, remplacer la seule ligne en gardant CRLF, BOM et style de citation, re-parser name, longueur, diff, placer les déclencheurs critiques dans la fenêtre visible (fin ≤ 270), puis skill-file-qa PASS sur empreinte stable sans nouveau WARN ; vérifier la propagation par couches : Base directory, SHA-256 du corps injecté égal au disque, entrée skill_listing (préfixe 299 + ellipse ou session isInitial), panneau client manuel. Utiliser pour description à 1018, ancre à 0, Edit file changed, WARN de layout, reload, 注入正文核对. English: rewrite skill description, 1024 limit, anchor preflight, visible listing prefix, preserve EOL and quote style, baseline warn diff, verify injected body and listing propagation."
---

# Éditer la description d'un frontmatter de Skill

## Objectif

Remplacer uniquement la valeur `description` d'un `SKILL.md` lorsque la limite de 1024 caractères approche ou que les déclencheurs doivent changer, avec des invariants vérifiables sur les octets, le YAML et le diff.

## Quand l'utiliser

- la description approche 1024 caractères (par exemple 1018) et il faut ajouter ou compresser des déclencheurs ;
- un remplacement partiel par ancres risque d'échouer sur la ponctuation ;
- `Edit` signale `The file changed since your last read` ;
- il faut conserver CRLF, BOM et style de citation d'un fichier Windows ;
- il faut prouver qu'une seule ligne a changé et que la QA ne gagne aucun WARN ;
- un déclencheur ajouté en fin de description n'apparaît pas dans la liste du client : il doit être déplacé dans la fenêtre visible.

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
18. Une sortie JSON se relit avec l'outil Read ou avec un chemin passé en argument : un chemin littéral, Windows ou POSIX, écrit dans la chaîne de code de `py -3 -c` n'est pas converti par MSYS et échoue alors que le fichier existe.
19. La liste du client n'affiche qu'un préfixe de 299 caractères suivi de « … » : tout déclencheur critique doit finir au plus tard au caractère 270, et sa position se mesure par `visibility`, jamais à l'œil.
20. Une entrée de liste ne prouve l'état courant que si son horodatage est postérieur au `mtime` ; une session ouverte après l'écriture porte un attachement `isInitial` frais, ce qui dispense de `/skills reload`.
21. Un préfixe visible identique ne prouve pas que la description entière est indexée : un déclencheur au-delà de la fenêtre reste « invisible », jamais « mismatch ». Un test « quel Skill choisirais-tu » est un indice de poids faible, jamais une preuve.

## Procédure

Variables utilisées ci-dessous :

```bash
SKILLS_ROOT="$HOME/.qoder/skills"
SKILL_DIR="$SKILLS_ROOT/example-skill"
GUARD="$SKILLS_ROOT/edit-skill-frontmatter-description/scripts/description_guard.py"
PROPAGATION="$SKILLS_ROOT/edit-skill-frontmatter-description/scripts/propagation_check.py"
CANDIDATE="$HOME/.qoder/tmp/desc-candidates/candidate.txt"
BACKUP_DIR="$HOME/.qoder/tmp/skill-backup/example-skill"
QA_FIXTURE="$HOME/.qoder/tmp/skill-qa-fixture/example-skill"
```

### 0. Référence et QA de départ

Identifier d'abord la forme de `$SKILL_DIR` : Skill simple (`SKILL.md`, `references/`, `scripts/`) ou racine d'un clone d'archive (contient `.gitattributes` et `.qoder/skills/*`). Les deux se valident, mais pas sur la même cible de QA (étape 8).

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

### 2bis. Budget de visibilité

Le client n'affiche que les 299 premiers caractères de la description, suivis de « … ». Placer chaque déclencheur critique de sorte que `position + longueur ≤ 270`, puis le prouver :

```bash
py -3 -B "$GUARD" visibility "$SKILL_DIR" \
  --phrase "déclencheur 1" --phrase "déclencheur 2" \
  --window 299 --safe 270
```

- `count` doit valoir 1 pour chaque phrase : une formulation dupliquée ne localise rien.
- `end_pos ≤ 270` pour toutes : verdict `VISIBILITY_OK`, code 0.
- `within_window` vrai mais `within_safe` faux : `VISIBILITY_PARTIAL`, code 1 — déplacer le déclencheur, pas élargir la fenêtre.
- Phrase absente ou au-delà de 299 : `VISIBILITY_FAIL` — invisible pour le modèle même si la QA passe.
- Contrôle négatif obligatoire : une phrase placée après 270 doit faire échouer la commande.

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

Pour relire une sortie JSON comme `apply.json`, utiliser l'outil Read ou passer le chemin en argument :

```bash
py -3 -B -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); print(d['status'], d.get('restored'))" "$OUT/apply.json"
```

Un chemin POSIX (`/c/...`) écrit dans la chaîne de code produit `FileNotFoundError` alors que le fichier existe : MSYS ne convertit que les arguments.

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

Deux cibles possibles, jamais interchangeables :

| Cible | Commande | Ce qu'elle prouve | Observé |
|---|---|---|---|
| Installation | `validate_skill.py "$SKILL_DIR"` | layout réellement installé | Skill simple : `Files (6)`, 0 WARN ; racine d'archive : `Files (15)`, 13 WARN |
| Fixture à 2 fichiers | copie de `SKILL.md` et des références modifiées dans un dossier du même nom, hors du Skill | édition isolée, empreinte stable, zéro WARN ajouté | `Files (2)`, 0 WARN |

```bash
VALIDATOR="$SKILLS_ROOT/skill-file-qa/scripts/validate_skill.py"
# Installation : comparaison avant/après sur la même cible
py -3 -B "$VALIDATOR" "$SKILL_DIR" --workspace "$PWD" | tee "$HOME/.qoder/tmp/qa-after.txt"
diff <(grep '^WARN' "$HOME/.qoder/tmp/qa-before.txt" | sort) \
     <(grep '^WARN' "$HOME/.qoder/tmp/qa-after.txt" | sort) || true
# Fixture à 2 fichiers : contrôle isolé, sans diff avec la baseline d'installation
py -3 -B "$VALIDATOR" "$QA_FIXTURE" --workspace "$PWD"
```

- Exiger `RESULT PASS`, code de sortie 0 et empreinte stable sur la cible utilisée.
- Le nouvel ensemble de WARN doit être vide **par rapport à la même cible** ; un simple décompte identique ne suffit pas, et les 13 WARN de l'archive ne se comparent jamais aux 0 WARN de la fixture.
- Le nombre de WARN préexistants n'est pas fixe : il dépend du contenu de l'archive (10 puis 13 observés).
- Si `$SKILL_DIR` est une racine d'archive, lancer les deux QA et consigner les deux jeux ; la fixture ne remplace pas le layout réel.
- Si le corps a aussi été édité, le nombre de lignes peut légitimement changer ; limiter l'invariant « corps identique » à l'étape de description seule.

### 9. Vérifier la propagation de la description

Un agent ne peut pas exécuter `/skills reload`. Trois couches distinctes, jamais interchangeables :

| Couche | Preuve | Ce qu'elle ne prouve pas |
|---|---|---|
| Injection à l'appel | message `user`, `isMeta: true`, contenu commençant par `Base directory for this skill:` | le panneau client |
| Liste de Skills | attachement `skill_listing` (`isInitial: true`) du JSONL de session | que le client a rafraîchi |
| Panneau client | action utilisateur | non vérifiable par l'agent |

Utiliser les étapes 9.0 et `check` seulement si le Skill a été appelé. Pour une édition de description seule, passer à 9bis : l'appel injecte tout le corps (≈ 38 KB dans le cas vérifié) et n'est pas nécessaire.

1. Échantillonner `size`, `mtime_ns` et SHA-256 de `SKILL.md` avant et après l'appel : un appel en lecture seule ne doit rien écrire.
2. Appeler le Skill en lecture seule ; le résultat de l'outil ne contient que `Launching skill:` suivi du nom, sans chemin ni corps.
3. Dans `~/.qoder/projects/$PROJECT_DIR/$SESSION_ID.jsonl`, ne retenir que les messages `type: user`, `isMeta: true`, dont le contenu est une chaîne commençant exactement par `Base directory for this skill:`. Un filtre par sous-chaîne est faux : des sorties d'outils citent la même chaîne plus loin.
4. Exiger que la première ligne déclarée égale le dossier résolu du Skill.
5. Extraire le corps injecté (texte après la première ligne vide), retirer un éventuel bloc final `ARGUMENTS:` ajouté quand le Skill est appelé avec des arguments, puis `strip()` les deux côtés ; comparer son SHA-256 à celui du corps disque `strip()`. Annoncer « identique après normalisation », jamais « octet pour octet » : les longueurs brutes diffèrent (11 807 vs 11 808 dans le cas vérifié).
6. Compter 2 ou 3 fragments du nouveau corps ; exiger ≥ 1 chacun et expliquer tout compte supérieur à 1.
7. Si un `skill_listing` postérieur au `mtime` existe, retrouver l'entrée de liste commençant par `-` puis le nom du Skill, suivie de `: ` et de la description : segment de 300 caractères finissant par `…`, dont les 299 premiers égalent les 299 premiers du disque. Si le dernier attachement précède l'écriture, écrire « liste non vérifiée ».
8. Conclure par « panneau client non vérifié, rafraîchissement manuel » et ne plus écrire dans `SKILL.md` pendant cette phase.

#### 9.0 Identifier la session

`SESSION_ID` ne se déduit ni du JSONL le plus récent ni d'une recherche de sous-chaîne. Pour chaque `~/.qoder/projects/$PROJECT_DIR/*.jsonl`, parser chaque ligne en JSON et compter les messages `type: user`, `isMeta: true`, dont `message.content` est une chaîne commençant exactement par `Base directory for this skill:` et dont la première ligne vaut le dossier résolu du Skill. Retenir le fichier avec au moins une injection ; si plusieurs en ont, prendre celle dont l'horodatage d'injection est le plus récent et le consigner. Écrire le compteur dans un `.py` temporaire hors du Skill, ou passer le dossier en argument ; jamais un chemin littéral Windows ou POSIX dans la chaîne de code d'un `py -3 -c`.

Cas vérifié : le JSONL alors le plus récent (`55f63550…`) comptait 0 injection de ce Skill et `check` y renvoie le code 2 `no injection record found` ; `db72d65b…` en comptait au moins une et a produit `INJECTION_OK_LISTING_OK`. Consigner les `mtime` et les comptes par fichier avant de choisir.

Renseigner `PROJECT_DIR` et `SESSION_ID`, puis exécuter le vérificateur :

```bash
SESSION_JSONL="$HOME/.qoder/projects/$PROJECT_DIR/$SESSION_ID.jsonl"
py -3 -B "$PROPAGATION" check "$SKILL_DIR" \
  --session-jsonl "$SESSION_JSONL" \
  --sentinel "fragment 1" --sentinel "fragment 2"
```

Le script exécute les étapes 3 à 7 et renvoie `verdict` : `INJECTION_OK_LISTING_OK`, `INJECTION_OK_LISTING_UNVERIFIED`, `INJECTION_OK_LISTING_MISMATCH` (code 1 : un listing frais contredit la description) ou `FAIL`. Une couche non mesurée reste `unverified` ; `panel` vaut toujours `unverified_manual`.

#### 9bis. Description seule, Skill non appelé

Une modification de description ne justifie pas d'appeler le Skill. Dans ce mode, seule la couche liste est mesurable ; l'injection reste `unverified` et le panneau reste manuel.

```bash
py -3 -B "$PROPAGATION" listing "$SKILL_DIR" \
  --session-jsonl "$SESSION_JSONL"
```

- Lire `record['attachment']['content']` : un enregistrement de liste a `message: null` ; chercher dans `message.content` donne 0 entrée.
- Chercher la ligne exacte `- <name>: `, puis trier toutes les entrées par `record['timestamp']` (ISO ou epoch, millisecondes acceptées). L'ordre du glob n'est pas chronologique : des entrées du 2026-10-26 peuvent sortir en dernier et faire croire à un préfixe à 0.
- Ne retenir que les entrées postérieures au `mtime` de `SKILL.md` (ou `--after`) et exiger l'égalité complète, ou un segment de 300 caractères finissant par `…` dont les 299 premiers égalent le disque.
- Verdicts : `LISTING_OK`, `LISTING_UNVERIFIED` (aucune entrée fraîche, code 0) ou `LISTING_MISMATCH` (entrée fraîche contradictoire, code 1) ; `injection` vaut `unverified`, `panel` reste `unverified_manual`.
- Cas vérifié : re-scan indépendant de 1703 entrées, 17 postérieures à l'écriture (13 au moment de la session), la plus récente `2026-10-27T13:29:31.108Z`, segment de 300 + ellipse, 299 premiers identiques ; la session d'édition portait elle-même l'entrée `13:25:46.611Z`.

**Obtenir une entrée fraîche sans `/skills reload`.** L'agent ne peut pas recharger la liste. Si aucun `skill_listing` postérieur au `mtime` n'existe dans les JSONL connus, ouvrir une session indépendante en lecture seule : son attachement `isInitial` est construit à l'ouverture, donc après l'écriture. Passer son JSONL à `listing` (`--session-jsonl` est répétable) et exiger `entries_fresh ≥ 1`, `is_initial: true` et `latest_timestamp` > `mtime`. Cas vérifié : écriture à `00:51:43Z`, session ouverte à `00:52:15.683Z`, `LISTING_OK`, préfixe 299.

- `LISTING_OK` ne couvre que le préfixe affiché. Un déclencheur absent de l'entrée mais présent sur le disque est tronqué, pas périmé : le déclarer « invisible » et le déplacer (2bis), sans écrire dans `SKILL.md` pour forcer un rechargement.
- Un test qui demande à la session de choisir un Skill n'a pas de pouvoir de décision quand plusieurs Skills du même domaine concourent : poids faible, jamais une preuve à la place de l'attachement.

`check` exige une injection de **ce** Skill : sans appel, il renvoie 2 `no injection record found for this Skill`. Ne pas lui passer une session où seul un autre Skill a été appelé : avant le filtre par dossier, il sélectionnait l'injection étrangère et rendait `FAIL` (code 1) avec un `declared_base_dir` d'un autre Skill. Le script filtre désormais par `same_dir(declared_base_dir, skill_dir)` et expose `injection_records_total` / `injection_records_for_skill`.

### 10. Rapport

Consigner : mode, ancienne et nouvelle longueur, ligne, style de citation, EOL, BOM, clé `backup` (chemin complet), SHA-256 avant/après, comptes QA et nouvel ensemble de WARN par cible, positions `visibility` de chaque déclencheur critique, puis le verdict de propagation de l'étape 9 ou, en mode 9bis, le JSONL de la session fraîche avec l'horodatage `isInitial`, le verdict `LISTING_*` et `injection: unverified`.

## Recette d'acceptation sur copie

Exécuter une fois après toute modification du garde ou de la procédure, dans `$HOME/.qoder/tmp/skill-acceptance-<horodatage>/`, sans écrire dans l'installation.

1. Copier un Skill de référence (par exemple `inventory-installed-skills`) en gardant le nom du dossier égal au `name` ; relever `size` et SHA-256 de sa `SKILL.md`.
2. `inspect` la copie ; noter `description_line`, `description_len`, `quote_style`, `eol`, `bom`, `body_lines`.
3. `anchors --require-unique` avec une ancre copiée de la valeur parsée et une ancre absente : exiger `count: 1` / `count: 0` et le code 1 ; abandonner le remplacement partiel.
4. Rédiger un candidat d'une ligne hors du Skill. En dry-run : code 0, `status: would-apply`, SHA-256 inchangé, aucun `.bak`, aucun dossier de sauvegarde.
5. `replace --apply --backup-dir` hors du Skill : `status: applied`, les 12 invariants à `true`, sauvegarde de SHA-256 égal à l'original. Écrire la sortie dans `apply.json` et la relire avec l'outil Read ou en passant le chemin en argument : un chemin POSIX dans le code de `py -3 -c` échoue en `FileNotFoundError`.
6. Vérifier indépendamment dans un `.py` hors du Skill : même nombre de lignes, seule la ligne de description diffère, autres lignes identiques octet pour octet. `git diff` ne prouve rien sur une copie hors dépôt.
7. Restaurer depuis le `.bak` et exiger un SHA-256 égal à l'original ; lancer `skill-file-qa` avant, après apply et après restauration (mêmes compteurs, `Files (N)` stable).
8. Supprimer le répertoire jetable et vérifier qu'aucun `__pycache__`/`.pyc` n'existe dans l'installation, dont le SHA-256 doit être inchangé.
9. Tester `propagation_check.py` hors installation : `check` sur une session contenant l'injection d'un autre Skill doit renvoyer 2 (aucune injection de ce Skill) ; `listing` sur un JSONL jetable dont les entrées sont dans le désordre (une ancienne contradictoire, une fraîche conforme) doit renvoyer `LISTING_OK` ; avec `--after` postérieur, `LISTING_UNVERIFIED` ; avec une description fraîche différente, `LISTING_MISMATCH` (code 1). Vérifier `injection: "unverified"` et `panel: "unverified_manual"`.
10. Tester `visibility` sur une fixture dédiée hors installation (dossier = `name`, description `"Début" + 271 × "a" + "Fin"`) : `--phrase Début` → `VISIBILITY_OK` (code 0) ; `--phrase Fin` → `VISIBILITY_PARTIAL` (code 1, `end_pos` 279, `within_window` vrai, `within_safe` faux) ; une phrase absente ou dupliquée → `VISIBILITY_FAIL` (code 1). Aucune écriture, `__pycache__` absent.

## Contrat du script

Sortie JSON ASCII échappée, sans traceback. Exécuter avec `py -3 -B` pour éviter `__pycache__`.

| Commande | Entrées | Effet | Codes |
|---|---|---|---|
| `inspect <dir>` | `SKILL.md` unique | lit et mesure, aucune écriture | 0 lisible et éditable ; 1 structure non prise en charge ; 2 environnement |
| `anchors <dir>` | `--anchor` répétable, `--require-unique` | compte chaque ancre sur la description parsée | 0 ; 1 si `--require-unique` et un compte ≠ 1 ; 2 environnement |
| `visibility <dir>` | `--phrase` répétable, `--window` (défaut 299), `--safe` (défaut 270) | mesure `first_pos` / `end_pos` de chaque phrase ; aucune écriture | 0 toutes uniques et `end ≤ safe` ; 1 phrase absente, dupliquée ou hors fenêtre ; 2 environnement ou usage |
| `replace <dir>` | `--candidate-file`, `--backup-dir`, `--apply`, `--expect-sha256` | dry-run par défaut ; écriture ciblée avec sauvegarde et invariants | 0 ; 1 candidat ou invariant ; 2 environnement, EOL mixte, sauvegarde interne, SHA inattendu |
| `check <dir>` | `--session-jsonl` requis, `--sentinel` requis et répétable, `--injection-timestamp` | relit le JSONL, filtre les injections par dossier cible, compare injection, corps normalisé et listings ; aucune écriture | 0 injection conforme sans contradiction ; 1 écart ; 2 JSONL absent, aucune injection **de ce Skill**, sentinelle manquante ou usage |
| `listing <dir>` | `--session-jsonl` requis et répétable, `--after` ISO optionnel (défaut `mtime`) | lit les `skill_listing`, trie par timestamp, compare la description ; aucune écriture | 0 `LISTING_OK` ou `LISTING_UNVERIFIED` ; 1 `LISTING_MISMATCH` ; 2 JSONL absent ou usage |

`replace` refuse : candidat multiligne, vide ou > 1024 ; caractère de contrôle ; valeur qui ne fait pas l'aller-retour dans le style de citation existant ; description multiligne ou clé non top-level ; ligne de description non canonique (commentaire ou contenu supplémentaire) ; sauvegarde dans le Skill.

`disk_description_chars` compte la description parsée de la cible `check` ; ne le comparer qu'à `inspect description_len` sur le même dossier. Un `--session-jsonl` sans injection de ce Skill donne le code 2, pas un verdict. Un dry-run n'écrit ni dossier de sauvegarde ni `.bak` ; capturer son code avant toute autre commande. `listing` ne lit aucune injection : `injection` reste `unverified`, et un `--after` postérieur à toutes les entrées produit `LISTING_UNVERIFIED` (code 0).

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
| WARN de layout | 10 puis 13 WARN préexistants selon le contenu de l'archive (`.gitattributes`, `.qoder/skills/...`) | comparer les ensembles sur la même cible, pas seulement les comptes |
| Longueur | `len()` compte les points de code, pas les octets UTF-8 | ne pas utiliser la taille du fichier |
| `py -3 -c` inline (Git Bash), chemin Windows | littéral non brut dans des guillemets doubles : `SyntaxError: (unicode error) 'unicodeescape' ... position 33-34` | écrire un `.py` temporaire hors du Skill qui reçoit son chemin en argument, puis lancer `py -3 -B` |
| `py -3 -c` inline (Git Bash), chemin POSIX | `open(r'/c/Users/.../apply.json')` : `FileNotFoundError` alors que le fichier existe, code 1 | MSYS ne convertit que les arguments : passer le chemin en argv ou lire avec l'outil Read |
| Entrée de liste sans description | 36 caractères, nom seul à 12:03:43 et 12:04:29 ; description seulement à 12:05:08.952Z | comparer les horodatages au `mtime` ; normal avant rechargement |
| `message.content` sur une liste | 0 entrée alors que l'attachement existe | lire `attachment.content` ; `message` vaut `null` |
| Ordre du glob | les dernières entrées lues dataient du 2026-10-26, préfixe 299 à 0 | trier toutes les entrées par `record['timestamp']` |
| `backup_path` | `null` alors que la sauvegarde existe | la clé apply est `backup` (chemin complet) ; `backup_dir` donne le dossier |
| QA sur racine d'archive | `Files (15)` et 13 WARN contre `Files (2)` et 0 WARN sur la fixture | comparer les WARN sur la même cible ; le compte varie (10/13) |
| Injection étrangère | `check` rend `FAIL` avec un `declared_base_dir` d'un autre Skill | filtrer par dossier cible ; sans injection de ce Skill, attendre le code 2 |
| Filtre par sous-chaîne sur `Base directory` | 5 faux positifs dans les sorties d'outils et les scripts de vérification | exiger `type: user`, `isMeta: true` et `startswith` |
| Hash du corps injecté | 11 807 vs 11 808 caractères bruts mais hachages égaux | `strip()` des deux côtés et déclarer la normalisation |
| Appel avec arguments | 16 542 caractères et SHA `7107c5d4…` pour un corps disque à jour : l'injection ajoute 63 caractères `\n\nARGUMENTS: …` | retirer le bloc `ARGUMENTS:` avant le hash (le script le fait) ; ou appeler sans argument |
| JSONL le plus récent | `55f63550…` (alors mtime max) sans injection ; `db72d65b…` en contenait | compter les injections exactes par fichier ; ne pas trier par `mtime` |
| Longueurs croisées | `inspect` 934 sur la fixture, `check` 963 sur l'installation : aucune incohérence | comparer deux mesures du même fichier |
| Code de retour masqué | dry-run à 0, compound affiché à 2 par le `ls` final | lancer le garde seul ou `rc=$?` juste après |
| `git diff` sur une copie | copie hors dépôt : aucune sortie, aucune preuve | diff ligne à ligne en Python hors du Skill |
| Déclencheur en fin de description | 1000 caractères, modification à partir du caractère 309 : les 4 déclencheurs de queue comptent 0 dans la liste et 1 sur le disque | placer les déclencheurs critiques avant 270 (`visibility`) ; ne pas conclure à une liste périmée |
| Déclencheur dupliqué | `清单截断` compte 2 : la position de la première occurrence ne localise rien | exiger `count == 1` ; choisir une formulation unique |
| Test « quel Skill choisirais-tu » | la session a choisi `verify-injected-skill-body-freshness` alors que la cible était `planifier-budget-paquet-skill` | poids faible : la preuve est l'attachement `isInitial`, pas le choix du modèle |

## Checklist finale

- [ ] `inspect` exécuté avant toute écriture ; ligne, longueur, style, EOL et BOM enregistrés.
- [ ] Chaque ancre compte exactement 1, ou le remplacement partiel a été abandonné.
- [ ] Candidat sur une ligne, ≤ 1024 points de code, style de citation compatible.
- [ ] Sauvegarde hors du dossier du Skill, SHA-256 identique, chemin lu dans la clé `backup` de la sortie apply.
- [ ] Dry-run sans modification d'octet.
- [ ] Apply avec `--expect-sha256`, invariants tous vrais, aucune restauration.
- [ ] Diff limité à la ligne de description ; corps et autres clés identiques.
- [ ] QA `RESULT PASS` sur empreinte stable et zéro nouveau WARN **sur la même cible** ; si racine d'archive, racine et fixture à 2 fichiers consignées séparément.
- [ ] SHA-256 de `SKILL.md` et des références enregistrés séparément.
- [ ] Appel lecture seule après écriture ; injection `isMeta` avec dossier exact et hash du corps normalisé égal.
- [ ] Mode « Skill non appelé » : `listing` exécuté, `LISTING_OK` avec 299 + ellipse, `injection` déclarée non mesurée.
- [ ] `check` refusé (code 2) quand la session ne contient aucune injection de ce Skill ; aucune injection étrangère sélectionnée.
- [ ] Statut de la liste consigné (préfixe 299 + ellipse, ou « non vérifiée ») ; panneau client déclaré manuel.
- [ ] Session choisie par injection exacte, pas par `mtime` ; comptes par fichier consignés.
- [ ] Code de retour de chaque sous-commande capturé juste après l'appel.
- [ ] Sorties JSON relues via l'outil Read ou un chemin en argument ; aucun chemin littéral dans `py -3 -c`.
- [ ] Longueurs comparées sur la même cible uniquement.
- [ ] Chaque déclencheur critique mesuré par `visibility` : `count == 1` et `end ≤ 270` ; contrôle négatif exécuté.
- [ ] En mode 9bis, entrée `isInitial` postérieure au `mtime` obtenue (session fraîche au besoin) ou `LISTING_UNVERIFIED` déclaré.
- [ ] Déclencheur hors fenêtre déclaré « invisible », jamais `MISMATCH` ; test de choix de Skill marqué de poids faible.
- [ ] Recette d'acceptation exécutée sur copie : dry-run sans octet, invariants, restauration SHA = original, QA aux trois états.
- [ ] Aucun `__pycache__`/`.pyc`, aucun autre Skill modifié.

## Ressources

- [scripts/description_guard.py](scripts/description_guard.py) — `inspect`, `anchors`, `visibility`, `replace` ; dry-run par défaut, sauvegarde externe, invariants et restauration.
- [scripts/propagation_check.py](scripts/propagation_check.py) — `check` : injection filtrée par dossier, corps normalisé, `skill_listing` ; `listing` : couche liste seule, tri par timestamp ; lecture seule, verdict explicite.
- [references/cas-description-1018-vers-1004.md](references/cas-description-1018-vers-1004.md) — cas vérifié du 2026-10-27, preuves et statuts.
- [references/cas-propagation-reload-2026-10-27.md](references/cas-propagation-reload-2026-10-27.md) — cas vérifié : injection 12:04:32.702Z, `eb2a411c…`, 299 + ellipse.
- [references/cas-acceptation-2026-10-27.md](references/cas-acceptation-2026-10-27.md) — recette exécutée de bout en bout : fixture 934, dry-run 961 sans écriture, restauration SHA identique, QA 9/0/0.
- [references/cas-listing-sans-invocation-2026-10-27.md](references/cas-listing-sans-invocation-2026-10-27.md) — cas vérifié : 1004 → 834, QA racine d'archive 15/13 vs fixture 2/0, liste seule sans injection, `backup` vs `backup_path`.
- [references/cas-visibilite-299-2026-10-28.md](references/cas-visibilite-299-2026-10-28.md) — cas vérifié : 1000 → 1007, positions 95–130, session fraîche `isInitial` `00:52:15.683Z`, `LISTING_OK`.

## Skills liés

- `skill-file-qa` : validation statique et empreinte stable.
- `skill-update-concurrency-safe` : concurrence, sauvegardes et édition minimale.
- `bilingual-skill-parity` : parité après modification d'un Skill bilingue.
- `verifier-unicode-fichiers-windows` : assertions exactes sur du texte non ASCII.
- `verify-skill-runtime-binding` : preuve générique du dossier réellement chargé.
- `verify-injected-skill-body-freshness` : fraîcheur du corps injecté lors d'un rechargement. Ici, seule la propagation de la description est traitée ; ces deux Skills restent la référence pour les preuves génériques.
- `skill-acceptance-in-new-session` : prompt auto-suffisant et nonce pour une session indépendante ; utile quand l'entrée `isInitial` fraîche doit être obtenue sans écriture.
