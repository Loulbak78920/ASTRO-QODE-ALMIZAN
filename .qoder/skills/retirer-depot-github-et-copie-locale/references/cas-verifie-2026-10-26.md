# Cas vérifié — retrait d'un dépôt GitHub et d'une copie locale

## Provenance

- Session source : `b37d7404-a496-420f-b3f0-8e6d620f72ce`, titre original « 创建可复用 Skill ».
- Lecture finale : `runtimeState=ready`, `revision=22`, `hasMoreBefore=true`, aucun tour actif.
- Journal brut : `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\b37d7404-a496-420f-b3f0-8e6d620f72ce.jsonl`.
- Une lecture antérieure (`revision=12`) était encore en `streaming` et montrait le nettoyage de sauvegarde inachevé. Les commandes exactes et l'état final viennent du JSONL et d'une relecture à `revision=22`.
- Les messages utilisateur sont horodatés en UTC. Les noms de sauvegarde observés (`T1700`) ne sont pas alignés sur l'UTC des messages (le tour correspondant est à 16:05Z) : les traiter comme heure locale, probablement UTC+1, et ne pas les utiliser comme preuve d'horodatage UTC.

## Demandes et choix de l'utilisateur

| Tour | Message | Choix |
|---|---|---|
| 2026-10-26T16:03:58Z | « 关闭这个仓库 » | Archivage du dépôt distant (recommandé) |
| 2026-10-26T16:05:14Z | « 删除本地工作区目录 » | Cible : dossier Skill ; mode : sauvegarder puis supprimer |
| 2026-10-26T16:08:16Z | « 清理备份目录 » | Suppression de la sauvegarde exacte, après liste des dossiers voisins |
| 2026-10-26T16:09:10Z | « 清理 tmp 下剩余的 audit-recouvrement 相关目录 » | Extension explicite du périmètre aux quatre dossiers listés |

Aucune correction explicite de l'utilisateur n'a été enregistrée. Les deux demandes courtes ont été décomposées par `AskUserQuestion` avant exécution.

## Faits vérifiés

### Archivage distant

- Dépôt : `IMAM8MAHDI/audit-recouvrement-skills-avant-creation`.
- `PATCH {"archived":true}` : `ARCHIVE_HTTP=200`, `ARCHIVED=True`, `PRIVATE=True`.
- `GET` de contrôle : `GET_HTTP=200`, `ARCHIVED=True`, `PRIVATE=True`, `DEFAULT_BRANCH=skill/audit-recouvrement-skills-avant-creation`.
- `git ls-remote origin refs/heads/skill/audit-recouvrement-skills-avant-creation` : `LSREMOTE_EXIT=0`, référence `a010e3a967cb693750c04078ca143f4a0ab5ae3b`.
- Copie locale : `HEAD=a010e3a967cb693750c04078ca143f4a0ab5ae3b`, `git status --porcelain=v1` vide.

### Sauvegarde et suppression locales

- Cible : `C:\Users\Administrateur\.qoder\skills\audit-recouvrement-skills-avant-creation`.
- Sauvegarde : `C:\Users\Administrateur\.qoder\tmp\audit-recouvrement-deleted-20261026T1700`.
- `COPY_EXIT=0`.
- Inventaire source et sauvegarde : `SRC_FILES=44`, `BAK_FILES=44` (fichiers `.git` compris).
- `SKILL.md` source et sauvegarde : `2b86cf437a58043356555219a4144cc95336ef7e71ca4e525a96cc99db69a104`.
- `HEAD` source et sauvegarde : `a010e3a967cb693750c04078ca143f4a0ab5ae3b`.
- Worktree source et sauvegarde : propre (`git status --porcelain=v1` vide).
- Deux commits dans la sauvegarde :
  - `a010e3a docs(skill): nommer les variables des exemples et documenter la substitution a l'injection`
  - `c46cd75 feat(skill): exiger une version stable avant la decision de recouvrement`
- Suppression : `DELETE_EXIT=0`, `EXISTS=no`.
- Scan des deux racines skills (`~/.qoder/skills` et `<workspace>/.qoder/skills`) : aucune copie homonyme.
- Sauvegarde après suppression : 44 fichiers, `SKILL.md` au même SHA-256, `HEAD` toujours lisible, worktree propre.

### Nettoyage des sauvegardes

- Première suppression : la sauvegarde exacte `audit-recouvrement-deleted-20261026T1700` (195K) ; `EXISTS=no`.
- Le rapport a ensuite listé, sans les supprimer, quatre dossiers voisins : deux sauvegardes `SKILL.pre-write.md` et deux manifestes de commit.
- Après instruction nominative de l'utilisateur, ces quatre dossiers ont été supprimés avec une garde de chemin exacte ; `REMAINING_COUNT=0` pour les motifs `audit-recouvrement*` et `commit-audit-recouvrement*`.

## Commandes observées

Les commandes ci-dessous sont transcrites du JSONL (`tool_use`). Les sorties sont dans les sections précédentes ; aucune valeur de jeton n'est reproduite.

### Archivage et contrôle

```bash
cred=$(printf 'protocol=https\nhost=github.com\n\n' | GIT_TERMINAL_PROMPT=0 git -c credential.interactive=never credential fill 2>/dev/null)
pass=$(printf '%s\n' "$cred" | sed -n 's/^password=//p')
unset cred
resp=$(curl -s -w '\n__HTTP__%{http_code}' -X PATCH \
  -H "Authorization: Bearer $pass" \
  -H 'Accept: application/vnd.github+json' \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/IMAM8MAHDI/audit-recouvrement-skills-avant-creation" \
  -d '{"archived":true}')
unset pass
printf '%s' "$resp" | py -3 -c "import sys,json; raw=sys.stdin.read(); body,_,tail=raw.rpartition('__HTTP__'); print('ARCHIVE_HTTP='+tail.strip()); d=json.loads(body); print('FULL_NAME='+str(d.get('full_name'))); print('ARCHIVED='+str(d.get('archived'))); print('PRIVATE='+str(d.get('private'))); print('MESSAGE='+str(d.get('message')))"
```

### Sauvegarde

```bash
D="C:/Users/Administrateur/.qoder/skills/audit-recouvrement-skills-avant-creation"
B="C:/Users/Administrateur/.qoder/tmp/audit-recouvrement-deleted-20261026T1700"
mkdir -p "$B"
cp -a "$D/." "$B/" && echo "COPY_EXIT=0" || echo "COPY_EXIT=1"
echo "--- source inventory"
( cd "$D" && find . -type f ! -path './.git/*' -print0 | sort -z | xargs -0 sha256sum )
echo "--- backup inventory"
( cd "$B" && find . -type f ! -path './.git/*' -print0 | sort -z | xargs -0 sha256sum )
echo "--- source HEAD/status"
git -C "$D" rev-parse HEAD
git -C "$D" status --porcelain=v1
echo "--- backup HEAD/status"
git -C "$B" rev-parse HEAD
git -C "$B" status --porcelain=v1
echo "--- counts"
echo "SRC_FILES=$(find "$D" -type f | wc -l)"
echo "BAK_FILES=$(find "$B" -type f | wc -l)"
```

### Suppression avec garde

```bash
D="C:/Users/Administrateur/.qoder/skills/audit-recouvrement-skills-avant-creation"
B="C:/Users/Administrateur/.qoder/tmp/audit-recouvrement-deleted-20261026T1700"
case "$D" in
  "C:/Users/Administrateur/.qoder/skills/audit-recouvrement-skills-avant-creation")
    rm -rf "$D" && echo "DELETE_EXIT=0" || echo "DELETE_EXIT=1"
    ;;
  *)
    echo "GUARD_FAIL: unexpected target"
    exit 1
    ;;
esac
[ -e "$D" ] && echo "EXISTS=yes" || echo "EXISTS=no"
echo "--- remaining copies"
find "C:/Users/Administrateur/.qoder/skills" "C:/Users/Administrateur/Desktop/IMAM8MAHDI/.qoder/skills" -maxdepth 2 -type d -name "audit-recouvrement-skills-avant-creation" 2>/dev/null
echo "--- backup verify"
echo "BAK_FILES=$(find "$B" -type f | wc -l)"
sha256sum "$B/SKILL.md"
git -C "$B" rev-parse HEAD
git -C "$B" status --porcelain=v1
git -C "$B" log --oneline -2
```

### Nettoyage des dossiers voisins

```bash
T="C:/Users/Administrateur/.qoder/tmp"
for d in \
  "$T"/audit-recouvrement-backup-20261026T153142Z \
  "$T"/audit-recouvrement-backup-20261026T165341Z \
  "$T"/commit-audit-recouvrement-20261026-2 \
  "$T"/commit-audit-recouvrement-20261026T1555Z; do
  case "$d" in
    "$T"/audit-recouvrement-backup-20261026T153142Z|"$T"/audit-recouvrement-backup-20261026T165341Z|"$T"/commit-audit-recouvrement-20261026-2|"$T"/commit-audit-recouvrement-20261026T1555Z)
      rm -rf "$d" && echo "REMOVED=$(basename "$d")" || echo "FAILED=$(basename "$d")"
      ;;
    *)
      echo "GUARD_FAIL=$d"
      exit 1
      ;;
  esac
done
find "$T" -maxdepth 1 \( -name "audit-recouvrement*" -o -name "commit-audit-recouvrement*" \) -printf '%y %f\n' | sort
echo "REMAINING_COUNT=$(find "$T" -maxdepth 1 \( -name "audit-recouvrement*" -o -name "commit-audit-recouvrement*" \) | wc -l)"
```

## Branches non exécutées ou non vérifiées

| Branche | État | Raison |
|---|---|---|
| Suppression définitive du dépôt distant | Non exécutée | L'utilisateur a choisi l'archivage. Le jeton observé avait le scope `repo`, insuffisant pour `DELETE /repos/...` qui exige `delete_repo`. |
| Détachement de l'`origin` local | Non exécuté | L'utilisateur a choisi l'archivage, pas le détachement. |
| Suppression du workspace projet | Non exécutée | L'utilisateur a choisi le dossier Skill ; le workspace projet n'a pas été touché. |
| `PATCH {"archived":false}` | Non exécuté | Aucune restauration demandée. |
| Push après archivage | Non mesuré | Le comportement attendu est un refus en lecture seule ; le code HTTP exact n'a pas été observé dans cette session. |
| `/skills reload` | Non mesuré | La note sur le cache runtime a été donnée, mais le rechargement n'a pas été exécuté ni vérifié. |
| Suppression d'un dossier non Git | Non exécutée | La cible était un dépôt Git simple avec `.git`. |
| Sous-modules, worktrees, liens | Non exécutés | La cible n'en contenait pas. |

## Leçons incorporées dans le Skill

1. Une demande courte comme « fermer » ou « supprimer le dossier » doit être décomposée avant toute action, avec les options irréversibles clairement étiquetées.
2. L'archivage se prouve par `PATCH` puis `GET` ; le `ls-remote` et le `HEAD` local complètent la preuve.
3. La sauvegarde doit inclure `.git` et être vérifiée par comptage, hash, `HEAD` et propreté avant la suppression.
4. La suppression doit rester sous garde de chemin exact ; une variable ou un joker ne remplace pas la confirmation.
5. Les dossiers voisins d'une sauvegarde ne sont pas des déchets : les lister et demander avant de les supprimer.
6. Après suppression, la liste des Skills de la session peut être un cache ; vérifier le disque avant de conclure.
