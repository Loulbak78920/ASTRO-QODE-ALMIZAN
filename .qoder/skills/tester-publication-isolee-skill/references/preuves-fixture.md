# Preuves de la fixture de publication isolée

Faits datés du **2026-10-26**. Deux origines distinctes, jamais confondues :

- **Observé en session source** (`c4fcd88c-4b53-4843-a74c-f4a901244e96`) : un pilote temporaire a exécuté le flux, puis a été supprimé (`leftovers_rc=2`). Aucun fichier source n'a été récupéré sur disque ; son contenu reste reconstituable depuis le JSONL de la session (un `Write`, 7 `Edit`, 567 lignes finales) mais n'est pas livré.
- **Mesuré avec le harnais de cette Skill** : exécutions réelles du script reconstruit, sorties recopiées telles quelles.

## Environnement mesuré

| Élément | Valeur |
|---|---|
| OS | Windows 10.0.26200, Git Bash |
| Git | `git version 2.52.0.windows.1` |
| Python | `Python 3.14.7` via `py -3` |
| `core.autocrlf` système | `true` (`C:/Program Files/Git/etc/gitconfig`) |
| Remote de fixture | `file://` local, aucun réseau |
| Vérificateur | `verifier_archive_skill.py` de `publier-skill-qoder-vers-depot-git`, SHA-256 `d11f8864789d5f8627455c87b8b57554aaa5efa52bef5bf66ad66f9e6f5df1ed` (inchangé) |

## Faits observés en session source

Le pilote temporaire a produit, dans l'ordre : un clone source occupé et sale (`M base.txt` + `?? untracked.txt` sur une branche non `main`), un clone isolé propre sur `main`, la copie des 3 fichiers (`SKILL.md`, `references/note.md`, `scripts/tool.py`), `RESULT PASS` du vérificateur en mode worktree, un commit, un faux `STOP_HEAD` par hash abrégé, `STOP_BRANCH`/`STOP_DIRTY`/`STOP_ORIGIN`, une reprise après avance de `origin/main`, un fast-forward, un push local, 3/3 blobs distants conformes, un refus puis une acceptation du nettoyage, et un clone source inchangé.

Trois échecs du pilote, messages d'origine :

```text
TypeError: rev() takes 2 positional arguments but 3 were given
FAIL isolated clean: expected '', got 'M base.txt'
FAIL copied files: expected [...], got ['fake-skill/SKILL.md', ...]
```

Causes identifiées : helper de hash à un seul argument ; `core.autocrlf=true` système rendu explicite dans le clone isolé ; chemin relatif résolu depuis le dossier parent.

## Mesures du harnais reconstruit

### Exécution A — référence, `EXIT=0`

Commande : `py -3 "<skill>/scripts/tester_publication_isolee.py"`.
Les hashes de commit et de fixture changent à chaque exécution ; ils sont conservés ici pour montrer qu'il s'agit d'une exécution réelle, pas pour être comparés.

```text
Fixture root: C:\Users\Administrateur\.qoder\tmp\isolated-publish-hhf1x652
Verifier: C:\Users\Administrateur\.qoder\skills\publier-skill-qoder-vers-depot-git\scripts\verifier_archive_skill.py
Verifier sha256: d11f8864789d5f8627455c87b8b57554aaa5efa52bef5bf66ad66f9e6f5df1ed
STEP 0 original clone occupied and dirty
  M base.txt | ?? untracked.txt
  ok isolated branch: 'main'
  ok isolated HEAD == origin/main: '5f459f7bee30e08865d53f19bf95c738938802ce'
  ok isolated clean:
  isolated remote: file://C:/Users/Administrateur/.qoder/tmp/isolated-publish-hhf1x652/origin.git
  isolated clone: C:\Users\Administrateur\.qoder\tmp\publish-fake-skill.xj_6c4km\repo
  ok aligned HEAD == origin/main: '5f459f7bee30e08865d53f19bf95c738938802ce'
  ok merge branch: 'merge/skill-fake-skill'
  ok copy rc: 0
  ok copied files: ['SKILL.md', 'references/note.md', 'scripts/tool.py']
  ok no cache in archive: []
  ok verifier worktree rc=0 PASS (3/3 OK)
  ok commit files: ['.qoder/skills/fake-skill/SKILL.md', '.qoder/skills/fake-skill/references/note.md', '.qoder/skills/fake-skill/scripts/tool.py']
  ok after commit clean:
STEP 5 commit 07d2968c8aca9409d07cba144e7f1f5fb2a63cf2
  ok short-hash false stop: rc=1 STOP_HEAD head=07d2968
  ok short-hash guard: refs unchanged
  ok short-hash guard clean:
  ok branch-drift token: rc=1 STOP_BRANCH branch=main
  ok branch-drift guard: refs unchanged
  ok branch-drift guard clean:
  ok dirty token: rc=1 STOP_DIRTY
  ok dirty guard: refs unchanged
  ok worktree clean again clean:
  ok origin/main advanced: 6dbce8ebc1fde510fc6efdaff1e77b56f4863a12
  ok origin-drift token: rc=1 STOP_ORIGIN origin=6dbce8ebc1fde510fc6efdaff1e77b56f4863a12
  ok branch after origin drift: 'merge/skill-fake-skill'
  ok HEAD after origin drift: '07d2968c8aca9409d07cba144e7f1f5fb2a63cf2'
  ok origin updated by fetch: '6dbce8ebc1fde510fc6efdaff1e77b56f4863a12'
  ok origin-drift guard clean:
STEP recovery: align main, recreate branch, recopy, recommit
  ok main aligned: '6dbce8ebc1fde510fc6efdaff1e77b56f4863a12'
  ok recreated merge branch: 'merge/skill-fake-skill'
  ok recopied files: ['SKILL.md', 'references/note.md', 'scripts/tool.py']
  ok no cache after recovery: []
  ok verifier after recovery rc=0 PASS (3/3 OK)
  ok commit files: ['.qoder/skills/fake-skill/SKILL.md', '.qoder/skills/fake-skill/references/note.md', '.qoder/skills/fake-skill/scripts/tool.py']
  ok after commit clean:
STEP 5b recovery commit 3ba99d5e373c624b02fbf3a3496f9a5de888caca
  ok full pre-merge guard: rc=0 CONTINUE
  ok main before merge: '6dbce8ebc1fde510fc6efdaff1e77b56f4863a12'
  ok fast-forward
  ok main after ff: '3ba99d5e373c624b02fbf3a3496f9a5de888caca'
  ok branch after ff: 'main'
  ok status ahead 1
  ok pre-push guard: rc=0 CONTINUE
  ok push line
  ok remote main after push: '3ba99d5e373c624b02fbf3a3496f9a5de888caca'
  ok remote verifier rc=0 PASS (3/3 OK)
  ok branch deleted
  ok final branch: 'main'
  ok final status: ## main...origin/main
STEP 9 isolated clone ready for cleanup
  ok cleanup refusal rc=1 REFUS
  ok cleanup accepted rc=0 REMOVED
STEP 9b isolated clone removed by guarded rm -rf
  ok original branch: 'skill/occupied'
  ok original HEAD: '5f459f7bee30e08865d53f19bf95c738938802ce'
  ok original origin/main: '5f459f7bee30e08865d53f19bf95c738938802ce'
  ok original status: 'M base.txt\n?? untracked.txt'
  ok original modified file hash: '6b9608617965a556ae66c0b3c9b1a40a26eb8e11b2faf36293308603f4db60f2'
  ok original untracked file hash: '528eee7ba2c0adea12842fd3eab1088d4d8402d115182154b0baef559f2164f2'
  ok original local main: '5f459f7bee30e08865d53f19bf95c738938802ce'
  ok original local origin/main: '5f459f7bee30e08865d53f19bf95c738938802ce'
CHECK original clone untouched and new commit absent
CLEANUP root and isolated clone absent
RESULT PASS isolated publication flow (clone, SHA-256, guards, ff, push, remote verify, cleanup)
```

### Exécution B — seconde référence, `EXIT=0`, hashes différents

```text
Fixture root: C:\Users\Administrateur\.qoder\tmp\isolated-publish-fotyy40t
STEP 5 commit ef41a7de9df34ad84e12f9e1a344a6618fdd3a00
STEP 5b recovery commit 921b00d63612ec18eafd17411420f278a5f00c79
RESULT PASS isolated publication flow (clone, SHA-256, guards, ff, push, remote verify, cleanup)
```

Aucun commit ni hash de l'exécution A ne réapparaît : le `PASS` n'est pas recyclé.

### Contrôle négatif — vérificateur absent, `EXIT=2`

```text
ERROR verifier not found: C:\nope\verifier_archive_skill.py
```

Aucune fixture n'est créée avant ce contrôle.

### Contrôle négatif intégré — `--keep`, `EXIT=0`

```text
CLEANUP skipped (--keep)
KEEP fixture root: C:\Users\Administrateur\.qoder\tmp\isolated-publish-0mobca6o
RESULT PASS isolated publication flow (clone, SHA-256, guards, ff, push, remote verify, cleanup)
```

`--keep` conserve la racine de fixture (`origin.git`, `work`, `other`). Le clone isolé, lui, a déjà été supprimé par l'étape 9 gardée : `--keep` ne le restaure pas. La racine conservée a ensuite été supprimée manuellement après contrôle de préfixe (`removed ... exists_after False`).

## Échec de mise au point du harnais reconstruit

Première exécution du harnais, `EXIT=1` :

```text
FAIL git clone rc=128: fatal: '/C:/Users/Administrateur/.qoder/tmp/isolated-publish-urauj8p0/origin.git' does not appear to be a git repository
CLEANUP root and isolated clone absent
RESULT FAIL isolated publication flow
```

Cause : le harnais force `MSYS_NO_PATHCONV=1` pour neutraliser la conversion MSYS ; dans cet environnement, `Path.as_uri()` produit `file:///C:/…`, que Git résout en `/C:/…` au lieu de `C:/…`. Mesure isolée sous le même environnement :

```text
0 rc 128 file:///C:/Users/Administrateur/.qoder/tmp/uritest4.1358/o.git
  fatal: '/C:/Users/Administrateur/.qoder/tmp/uritest4.1358/o.git' does not appear to be a git repository
1 rc 0 file://C:/Users/Administrateur/.qoder/tmp/uritest4.1358/o.git
2 rc 0 C:/Users/Administrateur/.qoder/tmp/uritest4.1358/o.git
```

Correctif retenu : construire l'URL avec `"file://" + path.resolve().as_posix()`, soit `file://C:/…` (deux barres), qui reste un remote `file://` local. `file:///C:/…` fonctionne hors `MSYS_NO_PATHCONV=1`, mais pas dans le harnais.

## Champs stables et champs non déterministes

| Champ | Comparé | Remarque |
|---|---|---|
| `RESULT PASS` / `FAIL` | oui | ligne finale |
| Code de retour | oui | 0 PASS, 1 FAIL, 2 usage/environnement |
| Tokens `STOP_HEAD`, `STOP_BRANCH`, `STOP_DIRTY`, `STOP_ORIGIN`, `REFUS`, `REMOVED` | oui | comparaison de chaîne exacte |
| Nombre de fichiers copiés et de `OK` du vérificateur | oui | 3 et 3/3 |
| Lignes de statut `M base.txt` / `?? untracked.txt` | oui | forme exacte |
| Hashes de commit, hashes de fichiers, chemins de fixture | non | changent à chaque exécution ; conservés seulement comme trace |

## Limites

- Aucun dépôt réel, aucun remote réseau, aucune concurrence entre sessions n'a été testé.
- Le clone source de la fixture est local et volontairement sale sur une branche non `main` ; il ne reproduit pas un dépôt de production partagé.
- Un `RESULT PASS` ne couvre que le flux exécuté dans la fixture, pas la sûreté d'une publication réelle.
- Le harnais est une reconstruction : la session source avait supprimé son pilote avant cette Skill.

## Empreintes relevées le 2026-10-26

| Fichier | SHA-256 |
|---|---|
| `scripts/tester_publication_isolee.py` | `62c6bdf03cb8b98bec88d7aec6f5a89325d26b5172737ce37727d282738c9b9f` |
| `references/preuves-fixture.md` | non auto-référencé |
| `publier-skill-qoder-vers-depot-git/scripts/verifier_archive_skill.py` | `d11f8864789d5f8627455c87b8b57554aaa5efa52bef5bf66ad66f9e6f5df1ed` |
