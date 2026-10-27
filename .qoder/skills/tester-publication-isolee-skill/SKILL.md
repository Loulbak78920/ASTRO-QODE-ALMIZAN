---
name: tester-publication-isolee-skill
description: "Tester hors production la publication isolée d'un Skill vers un dépôt Git (étape 0b de publier-skill-qoder-vers-depot-git) : monter une fixture jetable sous ~/.qoder/tmp avec un origin nu local, un clone source occupé et sale sur une branche non main, et un clone isolé ; vérifier la copie de 3 fichiers, les SHA-256, le commit, la reproduction du faux STOP_HEAD par hash abrégé, les gardes complets STOP_BRANCH/STOP_DIRTY/STOP_ORIGIN, la récupération après avance de origin/main, le fast-forward, le push local, la vérification des blobs distants, le nettoyage à préfixe contrôlé et l'immutabilité du clone source. Utiliser avant de modifier l'étape 0b ou ses gardes, pour reproduire l'échec autocrlf, l'erreur de chemin de copie, ou prouver qu'un harnais de publication n'est pas à vide. 中文触发：隔离发布测试、一次性夹具、本地裸仓库、非 main 脏工作区、短哈希误停、STOP_BRANCH、STOP_DIRTY、STOP_ORIGIN、远端推进恢复、fast-forward、远端 blob 校验、前缀校验清理、源克隆未被触碰。"
---

# Tester la publication isolée d'un Skill dans un dépôt Git

## État livré (2026-10-26)

Les trois fichiers existent : `SKILL.md`, `scripts/tester_publication_isolee.py` et `references/preuves-fixture.md`. Le harnais a rendu `RESULT PASS`, code 0, deux fois de suite avec des hashes différents, une fois avec `--keep`, et sort en 2 sur un `--verifier` absent sans créer de fixture. Aucun résidu n'est resté. Les preuves datées et les échecs observés sont dans `references/preuves-fixture.md`.

Un `RESULT PASS` ne couvre que le flux exécuté dans la fixture locale ; il ne prouve ni un dépôt réel, ni un remote réseau, ni la sûreté d'un push.

## Objectif

Exécuter hors production le flux de publication isolée de l'étape 0b de `publier-skill-qoder-vers-depot-git` dans une fixture jetable : un origin nu local, un clone « source » occupé et sale sur une branche non `main`, un second clone pour faire avancer le remote, puis un clone isolé. Le harnais doit prouver par des assertions exactes que la copie, les gardes, la récupération, le push local, la vérification distante et le nettoyage se comportent comme documenté, sans toucher au clone source.

Le pilote temporaire de la session source avait été supprimé (`leftovers_rc=2`), mais son contenu reste reconstituable depuis le JSONL de la session (un `Write` et 7 `Edit`, 567 lignes finales). Il documente l'ordre des étapes observé ; le harnais livré est une implémentation Python distincte, vérifiée deux fois. Voir `references/preuves-fixture.md`.

## Quand l'utiliser

- Avant de modifier l'étape 0b, les gardes de merge/push ou le nettoyage de `publier-skill-qoder-vers-depot-git`.
- Reproduire le faux `STOP_HEAD` causé par un hash abrégé comparé à un hash complet.
- Vérifier `STOP_BRANCH`, `STOP_DIRTY` et `STOP_ORIGIN` sans toucher un dépôt réel.
- Reproduire l'échec `core.autocrlf`, l'erreur de chemin de copie et l'échec `file:///` causé par `MSYS_NO_PATHCONV`.
- Prouver qu'un harnais de publication n'est pas à vide, via le garde à hash abrégé et le refus de nettoyage.

Ne pas utiliser pour : publier réellement un Skill, tester un dépôt de production, pousser vers un hôte réseau, prouver la sûreté d'un push réel, ou tester uniquement un garde de dérive (voir `tester-garde-derive-git`). Un `PASS` de ce harnais ne prouve que le flux exécuté dans la fixture.

## Contrat non négociable

1. **Fixture jetable uniquement** : tout se passe sous `$HOME/.qoder/tmp`. Jamais un dépôt de travail, jamais un chemin fourni par l'utilisateur comme cible de test.
2. **Aucun réseau** : le remote est un `file://` vers l'origin nu temporaire. Aucun clone, fetch ou push vers un hôte distant.
3. **Clone isolé fidèle** : créer le clone avec `git clone --branch main --single-branch`. Ne jamais écrire `core.autocrlf` dans ce clone après le clonage : le système est à `true` et le passer à `false` marque les fichiers LF comme modifiés (échec observé). L'identité de commit se passe par `-c user.name=... -c user.email=... -c commit.gpgsign=false`, sans `git config` persistant ; le harnais vérifie l'absence de `core.autocrlf`, `user.name` et `user.email` locaux dans ce clone.
4. **Clone source en lecture seule après la baseline** : le harnais construit d'abord le clone occupé, puis enregistre son état. Ensuite, n'y exécuter que `rev-parse`, `status`, `remote get-url`, `cat-file -e` et des lectures de fichiers. Aucun `fetch`, `switch`, `merge`, `stash`, `clean`, `add`, `commit`, `push` ni suppression.
5. **Hashes complets** : les gardes comparent les sorties complètes de `rev-parse` (40 caractères en SHA-1). Un hash abrégé doit produire le faux `STOP_HEAD` attendu, jamais un `CONTINUE`.
6. **Assertions exactes** : comparer le code de retour, le token complet, le hash complet, puis l'état des refs et du worktree après chaque garde. Un garde doit rester en lecture seule ; seul le fetch de la vérification distante met à jour `origin/main`.
7. **Vérificateur réel en lecture seule** : réutiliser `verifier_archive_skill.py` de `publier-skill-qoder-vers-depot-git`, exiger `RESULT PASS` et un `OK` par fichier, sans modifier ce script.
8. **Nettoyage vérifié** : refuser tout chemin hors du préfixe `publish-fake-skill.*` sous `$HOME/.qoder/tmp`, supprimer le clone isolé seulement après ce contrôle, puis vérifier son absence. La fixture est supprimée dans `finally`, sauf `--keep`.
9. **Codes de retour réservés** : le harnais sort en 0 (PASS), 1 (FAIL), 2 (usage ou environnement). Sortie ASCII, sans traceback brut.
10. **Pas de PASS recyclé** : chaque exécution crée de nouveaux hashes. Ne jamais réutiliser la sortie d'une session antérieure comme preuve.

## Fichiers

| Fichier | État | Rôle |
|---|---|---|
| `SKILL.md` | présent | Contrat, procédure et limites |
| `scripts/tester_publication_isolee.py` | présent, vérifié | Harnais end-to-end de la fixture |
| `references/preuves-fixture.md` | présent | Sorties observées, échecs, provenance et limites |

Le harnais exige Windows et `git` dans le `PATH`. Il n'appelle pas `bash` ni `cygpath` : les gardes et le contrôle de nettoyage sont simulés en Python.

## CLI

```bash
py -3 "<dossier-skill>/scripts/tester_publication_isolee.py"
py -3 "<dossier-skill>/scripts/tester_publication_isolee.py" --verifier "<chemin>"
py -3 "<dossier-skill>/scripts/tester_publication_isolee.py" --keep
```

- `--verifier` : chemin du vérificateur réel. Par défaut, celui de `publier-skill-qoder-vers-depot-git`. Un chemin absent affiche `ERROR verifier not found: <chemin>` et sort en 2 avant toute création de fixture.
- `--keep` : affiche `KEEP fixture root: <chemin>` et ne supprime pas la racine. Le clone isolé peut déjà avoir été supprimé par le contrôle de nettoyage. Supprimer la racine soi-même ensuite.

## Procédure

### 1. Test de référence

```bash
py -3 "<dossier-skill>/scripts/tester_publication_isolee.py"
```

Attendre `RESULT PASS`, code 0. Extrait réel (hashes variables à chaque exécution) :

```text
Fixture root: <chemin temporaire>
Verifier: <chemin du vérificateur>
Verifier sha256: <hash>
STEP 0 original clone occupied and dirty
  M base.txt | ?? untracked.txt
  ok isolated branch: 'main'
  ok isolated HEAD == origin/main: '<hash>'
  ok isolated clean:
  ok copied files: ['SKILL.md', 'references/note.md', 'scripts/tool.py']
  ok no cache in archive: []
  ok verifier worktree rc=0 PASS (3/3 OK)
STEP 5 commit <hash>
  ok short-hash false stop: rc=1 STOP_HEAD head=<7 caracteres>
  ok short-hash guard: refs unchanged
  ok branch-drift token: rc=1 STOP_BRANCH branch=main
  ok dirty token: rc=1 STOP_DIRTY
  ok origin-drift token: rc=1 STOP_ORIGIN origin=<hash>
STEP recovery: align main, recreate branch, recopy, recommit
STEP 5b recovery commit <hash>
  ok full pre-merge guard: rc=0 CONTINUE
  ok fast-forward
  ok push line
  ok remote verifier rc=0 PASS (3/3 OK)
  ok cleanup refusal rc=1 REFUS
  ok cleanup accepted rc=0 REMOVED
  ok original status: 'M base.txt\n?? untracked.txt'
CHECK original clone untouched and new commit absent
CLEANUP root and isolated clone absent
RESULT PASS isolated publication flow (clone, SHA-256, guards, ff, push, remote verify, cleanup)
```

Le harnais vérifie en plus que le clone isolé n'a aucune configuration locale (`core.autocrlf`, `user.name`, `user.email`), que les refs et le worktree ne bougent pas après chaque garde en échec, que le fichier sale survit au garde `STOP_DIRTY`, et que le commit publié est absent du clone source.

### 2. Contrôles négatifs intégrés

Le harnais contient deux contrôles négatifs :

- le garde à hash abrégé rend `STOP_HEAD`, code 1, et laisse les refs et le worktree inchangés ;
- le nettoyage refuse d'abord la racine de la fixture (`REFUS`), puis accepte le clone isolé (`REMOVED`).

Si l'un rend `CONTINUE` ou accepte le mauvais chemin, le harnais est à vide ou trop permissif : corriger le harnais, pas l'attendu.

### 3. Diagnostic

Utiliser `--keep`, lire `KEEP fixture root`, inspecter les refs et les reflogs, puis supprimer soi-même la racine. Ne pas laisser de répertoire `isolated-publish-*` ou `publish-fake-skill.*` après le diagnostic.

### 4. Rapport

```text
Skill : tester-publication-isolee-skill | harnais vérifié le <date>
Fixture : <chemin> | supprimée oui/non
Vérificateur : <chemin> | sha256 <hash>
Clone source : branche/HEAD/origin/main locaux, statut, hashes de fichiers inchangés | nouveau commit absent
Copie : 3 fichiers | SHA-256 worktree et distant PASS/FAIL
Gardes : STOP_HEAD abrégé reproduit | STOP_BRANCH/STOP_DIRTY/STOP_ORIGIN
Reprise : fast-forward | push | blobs distants
Nettoyage : REFUS puis REMOVED | racine et clone absents
Portée : fixture locale Windows uniquement ; dépôt réel, réseau et concurrence non testés
```

## Échecs observés et correctifs (2026-10-26)

Ces échecs proviennent du pilote de la session source ou de l'adaptation du harnais ; aucun ne conclut sur un dépôt réel.

| Symptôme | Cause | Correctif appliqué |
|---|---|---|
| `TypeError: rev() takes 2 positional arguments but 3 were given` | l'assistant de hash n'accepte qu'un argument après le dépôt | accepter `*args` : `rev(repo, *args)` |
| `FAIL isolated clean: expected '', got 'M base.txt'` | `core.autocrlf=true` au niveau système ; le passer à `false` après le clone marque les fichiers LF comme modifiés | ne pas écrire `core.autocrlf` dans le clone isolé ; le harnais vérifie son absence |
| `FAIL copied files: expected [...], got ['fake-skill/...']` | chemin relatif résolu depuis le dossier parent du Skill | normaliser avec `Path.relative_to(source)` et asserter les 3 chemins exacts |
| `FAIL git clone rc=128: fatal: '/C:/...' does not appear to be a git repository` | le wrapper git force `MSYS_NO_PATHCONV=1` et `MSYS2_ARG_CONV_EXCL='*'` ; dans cet environnement, `file:///C:/` est résolu en `/C:/` | construire l'URL avec `"file://" + path.resolve().as_posix()`, soit `file://C:/…` (deux barres) ; `file:///C:/…` ne convient pas ici |
| `ERROR verifier not found` code 2 | chemin `--verifier` absent | passer un chemin absolu existant ; aucune fixture n'est créée |
| `STOP_HEAD` juste après le commit alors que `HEAD` est correct | hash abrégé comparé à un hash complet | comparer les sorties complètes de `rev-parse` |
| nettoyage accepté sur un chemin inattendu | préfixe trop large | limiter à `publish-fake-skill.*` sous `$HOME/.qoder/tmp` |
| `WinError 5` pendant la suppression | objets Git en lecture seule sous Windows | `chmod` inscriptible avant `rmtree`, puis vérifier l'absence |
| push rejeté | le remote a avancé ou la base est périmée | ne jamais forcer ; relire `HEAD..origin/main` et demander |

## Provenance et limites

- **Observé** (session `c4fcd88c-4b53-4843-a74c-f4a901244e96`, 2026-10-26) : forme de la fixture, copie de 3 fichiers, `RESULT PASS` du vérificateur, faux `STOP_HEAD` par hash abrégé, `STOP_BRANCH`/`STOP_DIRTY`/`STOP_ORIGIN`, reprise après avance de `origin/main`, fast-forward, push local, vérification distante, refus puis acceptation du nettoyage, clone source inchangé.
- **Reconstituable, non livré** : le pilote d'origine se rejoue depuis le JSONL de la session source (un `Write` de 22 064 caractères, 7 `Edit`, 567 lignes finales). Il n'a pas été récupéré sur disque et ne fait pas partie de ce paquet.
- **Livré et vérifié** : harnais Python, gardes simulés en Python, nettoyage par contrôle de préfixe, CLI `--verifier`/`--keep`, deux `RESULT PASS` consécutifs avec des hashes différents, un `RESULT PASS` avec `--keep`, un `--verifier` absent sortant en 2.
- **Non prouvé** : un dépôt réel, un remote réseau, le consentement utilisateur, l'exécution littérale des extraits bash de la Skill de publication, une concurrence réelle entre sessions. Le harnais exige Windows et `git` dans le `PATH`.

## Définition de terminé

- [x] `SKILL.md` présent, frontmatter valide, description sur une ligne.
- [x] Harnais créé et `py -3 -m py_compile` sans erreur.
- [x] Référence de preuves créée, avec faits datés et frontière observé/reconstruit.
- [x] Test de référence `RESULT PASS`, code 0, exécuté deux fois avec des hashes différents.
- [x] Contrôles négatifs : `STOP_HEAD` abrégé et refus de nettoyage observés.
- [x] Aucun résidu `isolated-publish-*` ou `publish-fake-skill.*` après exécution.
- [x] Clone source inchangé : branche, `HEAD`, `origin/main`, statut, hashes de fichiers, absence du nouveau commit.
- [x] `skill-file-qa` rend `RESULT PASS` sur les trois fichiers.
- [x] Aucun commit ni push sans instruction explicite.

## Ressources

- `scripts/tester_publication_isolee.py` — harnais : origin nu, clone source occupé, second clone, clone isolé, gardes, reprise, push local, vérification distante, nettoyage.
- `references/preuves-fixture.md` — sorties observées et mesurées, échecs, frontière observé/reconstruit et limites.
- `publier-skill-qoder-vers-depot-git` : flux 0b, gardes de merge/push et vérificateur réel.
- `tester-garde-derive-git` : test isolé d'un garde de dérive seul, sans flux de publication.
- `skill-file-qa` : validation statique de ce Skill.
