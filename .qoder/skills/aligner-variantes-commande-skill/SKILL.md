---
name: aligner-variantes-commande-skill
description: "Réconcilier les variantes d'une même commande dans un paquet Skill après une réparation partielle : inventorier chaque mention normative (description, étapes, tableau des pièges, checklist, modèle de rapport, references), construire une matrice de preuves indiquant quelle forme a réellement été exercée par une fixture et combien d'assertions la couvrent, choisir une forme canonique unique cohérente avec les étapes voisines et le tableau des pièges, puis synchroniser toutes les mentions et rejouer l'extrait verbatim avec un scan octet par octet des variables positionnelles. Utiliser quand deux commandes du même paquet se contredisent, quand une correction n'a touché qu'une section, quand des comptes d'assertions différents (80/19/25/46) sont mélangés, ou avant livraison. 中文触发：同一个 Skill 内命令写法不一致、只改一处留下旧写法、description 与步骤或陷阱表矛盾、夹具断言数混用、逐字重放与字节级扫描。English: reconcile command variants, partial fix drift, canonical command form, fixture assertion counts, verbatim snippet replay, byte-level positional scan."
---

# Aligner les variantes d'une commande dans un paquet Skill

## Objectif

Quand une commande est « réparée » dans une seule section, les autres mentions gardent l'ancienne forme. Le paquet devient auto-contradictoire : la description, l'étape, le tableau des pièges et les references décrivent des procédures différentes pour le même geste. Ce Skill inventorie ces mentions, établit quelle forme a réellement été exercée par une fixture, choisit une forme canonique unique, synchronise tout le paquet, puis rejoue l'extrait verbatim.

## Portée et délégations

Ce Skill possède la réconciliation **document ↔ document** à l'intérieur d'un même paquet.

Ne pas l'utiliser pour :

- deux tâches différentes qui emploient légitimement deux commandes différentes ;
- la parité document ↔ sorties d'un script : `verifier-parite-doc-script-skill` ;
- la survie des références inter-Skills : `verify-cross-skill-reference-liveness` ;
- le rejeu d'un fixture déjà consigné dans une reference : `replay-skill-reference-fixtures` ;
- la réécriture complète des variables positionnelles et les fixtures de mutation : `harden-skill-argument-substitution` ;
- la stabilité et les écritures concurrentes : `skill-update-concurrency-safe` ;
- la validation structurelle : `skill-file-qa` ;
- le commit et le push : `commit-skill-work`.

## Modèle mental

- Un PASS de `skill-file-qa` valide la structure, pas la cohérence entre sections.
- Un compte d'assertions appartient à la forme exacte exercée, pas à une forme voisine.
- « Ça fonctionne » ne suffit pas : la cohérence avec les étapes adjacentes et le tableau des pièges fait partie de la correction.
- Une réparation partielle déplace la dérive au lieu de la supprimer : la section éditée change, les autres restent.
- Un inventaire à zéro `HIT` ne prouve pas l'absence de dérive tant qu'un contrôle positif n'a pas montré que le scan détecte une dérive connue.
- Une mention historique d'une forme écartée est acceptable si elle est explicitement étiquetée ; la même forme présentée comme procédure est une dérive.
- Un scan shell du signe dollar suivi d'un chiffre est lui-même soumis à la substitution et aux niveaux d'échappement : seuls les octets comptent.

## Règles non négociables

1. Prendre la preuve en lecture seule avant toute écriture : `size`, `mtime`, SHA-256, deux échantillons espacés. Si un fichier change, s'arrêter et passer à `skill-update-concurrency-safe`.
2. Inventorier toutes les mentions avant de choisir ; ne pas éditer de mémoire.
3. Remplir la matrice de preuves ; chaque variante reçoit un statut `FIXTURE_VERIFIED`, `SOURCE_REPORTED`, `STRUCTURALLY_BROKEN` ou `UNTESTED`, avec le compte exact et ce que les assertions couvrent.
4. Ne jamais transférer un compte d'assertions d'une forme à une autre.
5. Choisir la forme canonique dans cet ordre : octets validés par une fixture ; cohérence avec les étapes voisines et le tableau des pièges ; absence de variable positionnelle numérique ; absence de dépendance à une syntaxe ambiguë de type référence à deux-points. En cas d'égalité, retenir la forme déjà majoritaire dans les mentions normatives et consigner l'arbitrage.
6. Synchroniser toutes les mentions normatives : description, étapes, tableau des pièges, checklist, modèle de rapport, references. Mettre à jour aussi les comptes et la provenance.
7. Ne pas affaiblir une assertion ni supprimer une promesse documentée pour faire passer un fixture.
8. Extraire l'extrait à rejouer depuis le disque, par plage de lignes, avec le SHA-256 du fichier source ; ne jamais le recopier depuis le corps injecté.
9. Classer un échec avant d'accuser la procédure : défaut du fixture ou de l'assertion, puis défaut de la procédure. Prouver d'abord que le fixture reproduit les octets validés.
10. Le scan des variables positionnelles se fait au niveau octet et doit rendre zéro. Un `grep` shell n'est pas une preuve.
11. Ne pas committer ni pousser ; déléguer. Distinguer dans le rapport ce qui est vérifié, rapporté par une source ou non vérifié.
12. Avant d'accepter un inventaire nul, prouver que le scan détecte une dérive connue (étape 1bis). Un motif présent dans les deux formes, comme `ls-tree`, ne discrimine pas.

## Procédure

### Étape 0 — Figer la cible

```bash
SKILL_CIBLE="C:/Users/Administrateur/.qoder/skills/<nom>"
stat -c '%s %y' "$SKILL_CIBLE/SKILL.md" "$SKILL_CIBLE"/references/*.md
sha256sum "$SKILL_CIBLE/SKILL.md" "$SKILL_CIBLE"/references/*.md
git -C "$SKILL_CIBLE" rev-parse "HEAD:SKILL.md" 2>/dev/null || true
```

Refaire les deux relevés à quelques secondes d'intervalle. Toute différence arrête la procédure.

### Étape 1 — Inventorier les mentions

Passer toutes les formes candidates comme arguments ; le script ci-dessous est un heredoc en lecture seule. La variable `CIBLE` permet de rejouer le même bloc sur le paquet synthétique de l'étape 1bis.

```bash
CIBLE="$SKILL_CIBLE"
py -3 - "$CIBLE" "ls-tree" "rev-parse --verify" "read -r" <<'PY'
import sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')
skill = pathlib.Path(sys.argv[1]); patterns = sys.argv[2:]
if not (skill/'SKILL.md').is_file():
    print(f'MISSING SKILL.md: {skill}')
    raise SystemExit(2)
if not patterns:
    print('USAGE: <dossier-skill> <motif> [motif ...]')
    raise SystemExit(2)
files = [skill/'SKILL.md'] + sorted((skill/'references').rglob('*.md'))
print(f'FILES={len(files)}')
section = ''; fence = False
for path in files:
    for no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        s = line.lstrip()
        if s.startswith('```') or s.startswith('~~~'):
            fence = not fence
            continue
        if not fence and s.startswith('#'):
            section = s.lstrip('#').strip()
        for pat in patterns:
            if pat in line:
                print(f'HIT file={path.relative_to(skill).as_posix()} line={no} fence={fence} section={section!r} pattern={pat!r}')
PY
```

- Inclure les mentions en prose, dans les tableaux, les blocs de code et les references.
- Le comptage se fait par forme et par emplacement ; une même ligne peut contenir deux formes.
- Les arguments du scan énumèrent volontairement les formes candidates : ce sont des motifs de recherche, pas des commandes à exécuter.
- Au moins un motif est obligatoire : sans motif, le script sort en code 2 au lieu d'afficher un inventaire vide.
- `FILES=` et chaque `HIT` sont examinés ; un inventaire sans aucun `HIT` n'est pas une preuve d'absence, c'est un signal pour vérifier les motifs et exécuter le contrôle positif de l'étape 1bis.
- Un fichier non UTF-8 arrête le scan : le signaler, ne pas le réécrire.
- Le script ne juge pas : chaque `HIT` doit être classé `normatif`, `historique`, `liste de motifs` ou `fixture de contrôle` à l'étape 2.

### Étape 1bis — Contrôle positif du scan (DRIFT → ALIGNED)

Un `HIT` nul ne prouve rien tant que le scan n'a pas détecté une dérive connue. Monter un paquet synthétique, l'inventorier, puis l'aligner et réinventorier.

```bash
TMP_DRIFT="$(mktemp -d "$HOME/.qoder/tmp/aligner-drift.XXXXXX")" || exit 1
mkdir -p "$TMP_DRIFT/pkg/references"
# Phase DRIFT
printf '%s\n' '# Démo' 'description: git rev-parse --verify "main:SKILL.md"' 'étape: git rev-parse --verify "main:references/x.md"' > "$TMP_DRIFT/pkg/SKILL.md"
printf '%s\n' '# Cas' 'ancienne: git rev-parse --verify "main:references/y.md"' > "$TMP_DRIFT/pkg/references/cas.md"
CIBLE="$TMP_DRIFT/pkg"
# Rejouer le bloc de l'étape 1 avec « rev-parse --verify » et « read -r ».
# DRIFT : exiger au moins un HIT sur « rev-parse --verify ».
# Phase ALIGNED
printf '%s\n' '# Démo' 'canonique: read -r _mode _type oid _path <<< "$(git ls-tree main -- "SKILL.md")"' > "$TMP_DRIFT/pkg/SKILL.md"
printf '%s\n' '# Cas' 'canonique: git ls-tree main -- "references/x.md"' > "$TMP_DRIFT/pkg/references/cas.md"
# Rejouer le bloc de l'étape 1 : exiger 0 HIT sur « rev-parse --verify » et au moins un HIT sur « read -r ».
rm -rf "$TMP_DRIFT"
```

- Choisir un motif **discriminant**, présent seulement dans la forme écartée. `ls-tree` ne discrimine pas : il apparaît aussi dans la forme canonique. Utiliser par exemple `rev-parse --verify` ou `cut -d' '`.
- Consigner `DRIFT_OLD_HITS`, `ALIGNED_OLD_HITS` et `ALIGNED_CANONICAL_HITS`. Exiger `DRIFT_OLD_HITS >= 1`, `ALIGNED_OLD_HITS = 0` et `ALIGNED_CANONICAL_HITS >= 1`.
- Rejouer aussi les gardes de l'étape 1 : sans motif, code 2 ; cible sans `SKILL.md`, code 2.
- Un motif qui rend 0 `HIT` en DRIFT ne détecte aucune dérive : le remplacer avant de conclure.
- Le paquet synthétique n'a pas de section historique : après alignement, le total de la forme écartée doit être 0. Dans le paquet réel, les mentions historiques, la liste d'arguments du scan et le fixture de contrôle restent attendues ; l'exigence y est **0 `HIT` normatif**, pas 0 `HIT` total.
- Supprimer le paquet synthétique après le contrôle.

### Étape 2 — Construire la matrice de preuves

| Variante | Emplacements | Exercée par | Assertions | Couverture réelle | Incompatibilité | Statut |
|---|---|---|---|---|---|---|

- `FIXTURE_VERIFIED` : un fixture a réellement exécuté cette forme et ses assertions couvrent les octets, le statut ou la garde revendiqués.
- `SOURCE_REPORTED` : une session l'a rapporté sans que le fixture soit disponible ; ne pas le présenter comme vérifié ici.
- `STRUCTURALLY_BROKEN` : la forme ne peut pas produire le résultat attendu pour une raison démontrable.
- `UNTESTED` : aucune exécution connue.
- Un fixture qui extrait l'OID avec une autre forme ne valide pas la forme livrée : les comptes restent séparés.
- Consigner aussi ce que le fixture ne couvre pas (chemin absent, type non `blob`, CR, forme du statut).

### Étape 3 — Choisir la forme canonique

Appliquer l'ordre de la règle 5. Écrire la décision en une ligne : forme retenue, formes écartées, raison principale de chaque rejet. Si deux formes sont défendables, préférer celle qui demande le moins de changements normatifs et consigner l'arbitrage.

### Étape 4 — Synchroniser toutes les mentions

Parcourir dans cet ordre :

1. `description` du frontmatter ;
2. objectif et règles ;
3. étapes et blocs de commandes ;
4. tableau des erreurs et pièges ;
5. checklist ;
6. modèle de rapport ;
7. references et comptes d'assertions.

- Réutiliser le scan de l'étape 1 après chaque groupe de modifications.
- La forme canonique doit apparaître dans toutes les mentions normatives ; les formes écartées ne peuvent apparaître que dans une section explicitement historique, dans le tableau des pièges comme symptôme, ou dans la liste d'arguments du scan comme motifs de recherche, ou dans le fixture de contrôle de l'étape 1bis comme contre-exemple.
- Classer chaque `HIT` restant en `normatif`, `historique`, `liste de motifs` ou `fixture de contrôle` ; exiger 0 `HIT` normatif, pas 0 `HIT` total. Un total nul peut venir d'un motif absent : le contrôle positif de l'étape 1bis doit avoir réussi.
- Mettre à jour les comptes dans le même passage : un total global qui additionne des fixtures différents est faux.
- Ne pas réécrire les passages sans rapport avec la variante.

### Étape 5 — Rejouer l'extrait canonique

1. Relever la plage de lignes du bloc canonique et le SHA-256 du fichier source.
2. Extraire par plage, sans recopie manuelle :

```bash
start="<début>"; end="<fin>"
snippet="$(mktemp "$HOME/.qoder/tmp/variante.XXXXXX")" || exit 1
sed -n "${start},${end}p" "$SKILL_CIBLE/SKILL.md" > "$snippet"
sha256sum "$SKILL_CIBLE/SKILL.md"
```

La plage `115–122` du cas du 2026-10-26 est une observation datée du paquet cible, pas une constante : relire la plage sur le disque avant extraction.

3. Remplacer les placeholders par des valeurs concrètes dans le fixture, pas dans le paquet.
4. Monter un fixture jetable sous `~/.qoder/tmp` qui reproduit l'état d'entrée décrit par le paquet.
5. Assertions minimales :
   - l'OID fait 40 hexadécimaux et `git cat-file -t` vaut `blob` ;
   - les octets restaurés ont le SHA-256 attendu, pas seulement un fichier non vide ;
   - le compteur de CR vaut 0 ;
   - le statut par défaut vaut ` M SKILL.md` et `?? references/` ; avec `-uall`, le fichier exact apparaît ;
   - un chemin absent donne un OID vide, la garde retourne le code d'échec et aucun fichier n'est créé.
6. Compter les assertions, exiger zéro échec, puis supprimer le fixture.

Si un cas échoue : vérifier d'abord que le fixture contient bien les octets validés et que l'assertion compare les bonnes références. Un fixture qui attend un fichier là où Git replie un répertoire, ou qui compare `HEAD` à une référence de reflog (`main@{0}`), mesure autre chose que l'état attendu.

### Étape 6 — Scanner les variables positionnelles au niveau octet

```bash
py -3 - "$SKILL_CIBLE" <<'PY'
import sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')
root = pathlib.Path(sys.argv[1]); D = ord(chr(36)); total = 0
for path in [root/'SKILL.md'] + sorted((root/'references').rglob('*.md')):
    data = path.read_bytes()
    print(f'FILE={path.relative_to(root).as_posix()} bytes={len(data)} CR={data.count(bytes([13]))}')
    for no, line in enumerate(data.split(b'\n'), 1):
        for col, byte in enumerate(line, 1):
            nxt = line[col:col+1]; nxt2 = line[col+1:col+2]
            if byte == D and (nxt.isdigit() or (nxt == b'{' and nxt2.isdigit())):
                total += 1
                ctx = line[max(0, col-30):col+30].decode('utf-8', 'replace')
                print(f'POSVAR file={path.relative_to(root).as_posix()} line={no} col={col} context={ctx!r}')
print(f'POSVAR_TOTAL={total}')
raise SystemExit(0 if total == 0 else 1)
PY
```

- Le scan couvre le signe dollar suivi d'un chiffre et le signe dollar suivi d'une accolade puis d'un chiffre.
- Le même passage rapporte `bytes` et `CR` par fichier : exiger `CR=0` pour chaque fichier, en plus de `POSVAR_TOTAL=0`.
- Un `grep` shell peut rendre des faux positifs : dans un contexte à arguments, une référence positionnelle en guillemets doubles est remplacée par le texte de l'argument, et un identifiant de session contenant des chiffres est alors « trouvé ». Les niveaux d'échappement produisent aussi des faux négatifs. Reclasser toute sortie shell avec ce scan.
- Zéro hit est obligatoire ; un hit réel se corrige avec `harden-skill-argument-substitution`.

### Étape 7 — Valider et rapporter

```bash
QA_DIR="$HOME/.qoder/skills/skill-file-qa"
py -3 "$QA_DIR/scripts/validate_skill.py" "$SKILL_CIBLE" --workspace "<racine-workspace>" --stable-seconds 2 --stability-timeout 30
```

- Refaire le scan de l'étape 1 : la forme canonique dans toutes les mentions normatives, les autres seulement en historique.
- Rappeler le résultat du contrôle positif de l'étape 1bis (`DRIFT_OLD_HITS`, `ALIGNED_OLD_HITS=0`, `ALIGNED_CANONICAL_HITS>=1`) ; sans lui, le scan de la cible n'est pas probant.
- Classer chaque `HIT` restant ; un `HIT` historique, un argument de scan ou une ligne du fixture de contrôle n'est pas une dérive.
- Refaire le scan octet : `POSVAR_TOTAL=0` et `CR=0` pour chaque fichier.
- Vérifier les références inter-Skills avec `verify-cross-skill-reference-liveness`.
- Enregistrer séparément les SHA-256 de `SKILL.md`, des references et des scripts éventuels : le validateur ne couvre que `SKILL.md`.
- Supprimer les fixtures et tout `__pycache__` créé par la session.
- Rapport : forme canonique, matrice, mentions synchronisées, résultat du rejeu avec le compte d'assertions, scan octet, résultat QA, empreintes, et ce qui reste non vérifié.

## Erreurs et pièges

| Symptôme | Cause | Action |
|---|---|---|
| `skill-file-qa` PASS mais la description et l'étape 5 se contredisent | le validateur structurel ne compare pas les sections | inventaire + matrice + synchronisation |
| le compte de 80 assertions est invoqué pour la forme livrée | le harnais à 80 extrayait l'OID avec une autre forme | garder le compte sur la forme exercée ; exiger le fixture de la forme livrée |
| `cut -d' '` renvoie un OID suivi du chemin | la sortie sépare l'OID du chemin par une tabulation | ne pas découper sur l'espace ; préférer la forme canonique vérifiée |
| une forme fonctionne mais contredit l'étape 1 et le tableau des pièges | elle a été validée isolément | la cohérence interne fait partie du choix canonique |
| un `grep` shell trouve un identifiant de session | substitution d'argument ou niveaux d'échappement | reclasser avec le scan octet |
| le premier fixture échoue sur une assertion | assertion du reviewer erronée, par exemple comparaison à une référence de reflog | corriger le fixture et le rejouer avant d'accuser la procédure |
| le statut rend `?? references/` au lieu du fichier | Git replie un répertoire non suivi | ne pas le traiter comme un échec ; vérifier la forme enregistrée et `-uall` |
| le fixture échoue car l'archive de test diffère du fichier validé | défaut du fixture | aligner les octets, puis rejouer ; ne pas changer le hash attendu |
| un fichier restauré est vide | redirection avant vérification de l'OID | tester OID non vide et type `blob` avant d'écrire |
| la restauration passe mais le SHA-256 diffère | conversion de fin de ligne | comparer les octets du blob et compter les CR |
| une forme écartée réapparaît dans une étape | réparation partielle | resynchroniser toutes les mentions |
| une forme écartée apparaît seulement dans la section historique | trace volontaire | acceptable si elle est étiquetée et non présentée comme procédure |
| un scan à 0 `HIT` est présenté comme preuve d'absence | aucun contrôle positif ; motif erroné ou trop large | exécuter l'étape 1bis ; un 0 `HIT` sans contrôle n'est pas recevable |
| `ls-tree` est utilisé comme motif discriminant | il apparaît aussi dans la forme canonique | choisir un motif propre à la forme écartée (`rev-parse --verify`, `cut -d' '`) |
| des `HIT` historiques ou du fixture sont comptés comme dérive | le paquet contient une matrice, la liste de motifs et un contre-exemple | classer normatif / historique / liste de motifs / fixture de contrôle ; exiger 0 `HIT` normatif |
| un fichier change pendant l'édition | autre session | s'arrêter et passer à `skill-update-concurrency-safe` |
| l'inventaire rend `FILES=` sans aucun `HIT` | aucun motif fourni ou motifs obsolètes | relancer avec au moins un motif ; sans motif le script sort en code 2 |

## Checklist

- [ ] Baseline gelée et stable (size, mtime, SHA-256, OID HEAD si dépôt).
- [ ] Toutes les mentions inventoriées, y compris prose, tableaux et references.
- [ ] Inventaire lancé avec au moins un motif ; `FILES=` et `HIT` examinés, code de sortie 0.
- [ ] Chaque `HIT` classé `normatif` / `historique` / `liste de motifs` / `fixture de contrôle` ; 0 `HIT` normatif.
- [ ] Motif discriminant choisi ; `ls-tree` seul n'est pas accepté comme discriminant.
- [ ] Contrôle positif DRIFT→ALIGNED exécuté : `DRIFT_OLD_HITS>=1`, `ALIGNED_OLD_HITS=0`, `ALIGNED_CANONICAL_HITS>=1`, gardes rc=2.
- [ ] Matrice remplie avec statut et compte exact par forme.
- [ ] Forme canonique choisie selon l'ordre de priorité et arbitrage consigné.
- [ ] Description, étapes, pièges, checklist, rapport et references synchronisés.
- [ ] Comptes d'assertions mis à jour et non additionnés entre fixtures.
- [ ] Extrait canonique rejoué depuis le disque, zéro échec, assertions minimales couvertes.
- [ ] Scan octet : `POSVAR_TOTAL=0` et `CR=0` pour chaque fichier.
- [ ] `skill-file-qa` PASS ; références inter-Skills vérifiées.
- [ ] Empreintes finales enregistrées ; fixtures et caches supprimés.
- [ ] Rien de commité ni poussé ; délégations explicites.

## Rapport

```text
Cible : <dossier> | baseline <sha256> | stable=<oui|non>
Forme canonique : <forme> | écartées : <forme:raison>, ...
Mentions : description=<n> étapes=<n> pièges=<n> checklist=<n> rapport=<n> references=<n>
Contrôle positif : DRIFT_OLD=<n> ALIGNED_OLD=0 ALIGNED_CANON>=1 | gardes rc=2
Rejeu : extrait lignes <a>-<b> | source <sha256> | pass=<n> fail=<n>
Scan octet : POSVAR_TOTAL=<n> | CR=<n par fichier>
QA : <RESULT> | références inter-Skills : <état>
Empreintes : SKILL.md <sha256> | references <sha256> | scripts <sha256|aucun>
Non vérifié : <liste>
```

## Ressources

- `references/cas-alignement-variantes-2026-10-26.md` : cas source, matrice des quatre formes (80/19/25/46/11 assertions), corrections de harnais, reproduction du faux positif shell, contrôle positif synthétique DRIFT→ALIGNED (3/0/1), vérification de création et limites.
