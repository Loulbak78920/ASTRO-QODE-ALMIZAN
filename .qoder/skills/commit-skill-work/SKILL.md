---
name: commit-skill-work
description: "Committer des modifications de Skill ou de dépôts imbriqués sur Windows : localiser le vrai dépôt avec git -C <dir> rev-parse --show-toplevel, séparer les changements de la session des modifications préexistantes, lancer les tests et skill-file-qa, relever les empreintes des ressources car son Fingerprint ne couvre que SKILL.md, ajouter par chemins explicites, séparer les artefacts régénérés par les tests, puis ne pousser que sur demande explicite et vérifier la résolution runtime du Skill modifié par une invocation réelle. Utiliser pour toute demande « commit », « git commit », versionner un Skill utilisateur hors dépôt, choisir entre dépôts imbriqués, traiter __pycache__ ou fichiers générés, pousser un dépôt de Skill sans origin, ou vérifier qu'un Skill modifié est réellement résolu sans pouvoir exécuter /skills reload. 中文触发：提交 Skill、git commit、嵌套仓库、显式暂存、测试生成物、默认不 push、重载验证、运行时可解析性、辅助文件指纹。"
---

# Committer les modifications d'un Skill ou d'un dépôt imbriqué

## Objectif

Identifier le dépôt qui contient réellement les fichiers modifiés, committer uniquement le périmètre voulu et ne jamais pousser sans demande explicite. La racine du projet n'est pas forcément un dépôt : les dépôts utiles sont souvent imbriqués ou propres à un Skill.

## Déclencheurs

- demande « commit », « git commit », « versionne ce Skill » ;
- Skill utilisateur sous le dossier user-level des skills, hors de tout dépôt ;
- plusieurs dépôts imbriqués et périmètre ambigu ;
- tests qui réécrivent des fichiers générés après le commit ;
- demande de push, ou dépôt de Skill sans `origin`.

## Étape 1 — Localiser le dépôt réel

Partir d'un chemin absolu, toujours entre guillemets :

```bash
git -C "<chemin absolu>" rev-parse --show-toplevel
```

- `EXIT=128` avec `fatal: not a git repository` : ce dossier n'est pas un dépôt. Ne pas en déduire que la racine du projet l'est.
- Un chemin relatif ou non ASCII peut être résolu depuis un autre répertoire courant. Vérifier d'abord `test -d "<chemin>"`, puis passer le chemin absolu. Cas observé : `ASTRO-Q°ODE_SYSTEME` a échoué avec `fatal: cannot change to ...`.
- Énumérer les candidats quand la racine n'est pas un dépôt :

```bash
find "<racine>" -maxdepth 3 -name .git -type d
find "C:/Users/Administrateur/.qoder/skills" -maxdepth 2 -name .git -type d
```

- Inventaire en lecture seule, sortie ASCII, codes 0/1/2 :

```bash
py -3 scripts/inspect_git_state.py "<racine>" "C:/Users/Administrateur/.qoder/skills"
```

Le script interroge `rev-parse`, `status`, `diff`, `log` et `remote` sans modifier l'index, et signale les caches non suivis.

## Étape 2 — Classer les changements

```bash
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --stat
git -C "<depot>" log --oneline -5
git -C "<depot>" ls-files --error-unmatch -- "<chemin>"
```

Classer chaque chemin en trois catégories : **SESSION** (produit par le travail en cours), **PREEXISTANT** (déjà modifié avant la session), **INCERTAIN**. Ne jamais inclure silencieusement un chemin PREEXISTANT ou INCERTAIN : demander confirmation avec la liste exacte. Ne pas inclure `__pycache__`, les fichiers `.pyc` ni les artefacts temporaires.

## Étape 3 — Choisir le dépôt cible

| Situation | Action |
|---|---|
| Dossier Skill hors de tout dépôt | demander : initialiser un dépôt dans le dossier du Skill, laisser non commité, ou viser un dépôt existant |
| Dossier situé dans un dépôt imbriqué | utiliser ce dépôt et confirmer avec `ls-files --error-unmatch` |
| Plusieurs dépôts touchés | un commit par dépôt et par sujet |
| Modifications préexistantes non liées | demander avant de les inclure |
| Dépôt de Skill avec `origin` partagé | pousser une branche dédiée `skill/<nom>`, jamais `main` sans accord |
| Dépôt sans `origin` | demander l'URL ; ne pas deviner |

N'exécuter `git init` qu'après accord explicite. Ne pas modifier la configuration Git : vérifier `git config user.name` et `git config user.email`, sans les réécrire. Ne jamais committer un Skill utilisateur dans la branche `main` d'un dépôt public sans rapport.

## Étape 4 — Vérifier avant de committer

Lancer la suite du dépôt avec son entrée documentée. Dans ce projet, la suite observée est `tests.test_suite_complete` (11 tests) :

```bash
py -3 -m unittest tests.test_suite_complete
```

Pour un Skill, lancer `skill-file-qa` sur le dossier réel :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<dossier-skill>" --workspace "<racine-espace>" --stable-seconds 2
```

Exiger la sortie `RESULT PASS` avant de committer. Consigner les résultats réels. Ne pas committer si un test échoue : corriger d'abord.

Le `Fingerprint` de `skill-file-qa` ne couvre que `SKILL.md`. Cas observé : après deux modifications de `scripts/inspect_git_state.py`, il est resté à `9901 bytes` avec le même SHA-256 ; seul un changement de `SKILL.md` l'a fait passer à `9917 bytes`. Relever donc les empreintes de toutes les ressources avant de committer :

```bash
find "<dossier-skill>" -type f \( -name "SKILL.md" -o -path "*/scripts/*" -o -path "*/references/*" \) ! -path "*/__pycache__/*" -print0 | xargs -0 sha256sum
```

Si un fichier auxiliaire change après la validation, relancer `skill-file-qa` et recalculer. Ne pas conclure à l'intégrité du Skill à partir du seul `Fingerprint`.

Attention : la suite peut réécrire des fichiers générés (cas observé : 5 sceaux dans `memoire_aq/`). Les traiter après le commit, pas les ignorer.

## Étape 5 — Relire le diff

```bash
git -C "<depot>" diff --stat
git -C "<depot>" diff -- "<chemin>"
git -C "<depot>" status --porcelain=v1
```

Chercher secrets, binaires volumineux, caches et fichiers hors périmètre. Les avertissements `warning: ... CRLF will be replaced by LF` sont informatifs, pas des erreurs : les signaler sans les corriger par une réécriture globale.

## Étape 6 — Ajouter par lots explicites

```bash
git -C "<depot>" add -- "<chemin1>" "<chemin2>"
git -C "<depot>" status --porcelain=v1
git -C "<depot>" diff --cached --stat
```

Ne jamais utiliser `git add -A`, `git add .` ni un motif large. Grouper par sujet et séparer les artefacts régénérés du changement de code. Vérifier la liste indexée avant chaque commit.

## Étape 7 — Committer

```bash
git -C "<depot>" log --oneline -5
git -C "<depot>" commit -m "$(cat <<'EOF'
fix(physique): corriger les 20 etats S6
EOF
)"
```

Reprendre le style des messages existants. Un commit par sujet. Ne pas utiliser `--no-verify`, ne pas amender un commit déjà publié. Après le commit, exécuter `git -C "<depot>" status --porcelain=v1` et `git -C "<depot>" log -1 --stat`.

## Étape 8 — Traiter les effets de bord

Si les tests ont modifié des fichiers après le commit, examiner `git diff`, confirmer qu'il s'agit bien d'une régénération, puis créer un commit séparé de type `chore(...)`. Ne pas jeter ces fichiers et ne pas les mélanger au commit fonctionnel. Si les fichiers sont sans rapport, les laisser intacts et le signaler.

## Étape 9 — Pousser seulement sur demande

Par défaut, ne pas pousser. Indiquer explicitement « non poussé » dans le rapport.

Sur demande explicite :

```bash
git -C "<depot>" remote -v
git -C "<depot>" branch -vv
git -C "<depot>" push -u origin "HEAD:refs/heads/skill/<nom>"
```

- Sans remote : demander l'URL, ne pas la déduire d'un autre dépôt.
- Avec un `origin` partagé : pousser une branche dédiée, jamais `main`, jamais de force push.
- Après le push, comparer local et distant :

```bash
git -C "<depot>" rev-parse HEAD
git -C "<depot>" ls-remote origin "refs/heads/<branche>"
```

Le hash distant doit correspondre au hash local. Signaler la branche réellement poussée : un push `HEAD:refs/heads/<branche>` peut laisser la branche locale suivre un nom différent.

## Étape 10 — Vérifier la résolution runtime du Skill modifié

Après avoir modifié ou commité un Skill, prouver qu'il est réellement résolu par le runtime, et pas seulement présent sur disque :

1. Invoquer le Skill modifié avec l'outil Skill. Un chargement réussi retourne son répertoire de base ; il doit correspondre au dossier réellement modifié.
2. Chercher une homonymie qui masquerait la version utilisateur ; les deux racines sont à vérifier :

```bash
find "C:/Users/Administrateur/.qoder/skills" "<racine-espace>/.qoder/skills" -maxdepth 2 -type d -name "<nom-skill>" 2>/dev/null || true
```

Un root absent est ignoré ; seul le nombre de résultats compte. Un seul résultat attendu : la racine utilisateur. Un doublon côté projet masque le Skill utilisateur ; le signaler avant de conclure.

3. `/skills reload` est une commande d'interface que l'agent ne peut pas exécuter : demander à l'utilisateur de la lancer si nécessaire. Une invocation réussie est une preuve plus forte que la seule présence des fichiers ou qu'une liste statique.
4. Si l'invocation échoue ou si les fichiers manquent, ne pas annoncer le Skill comme disponible ; rapporter l'échec.

## Erreurs et pièges (observés et préventifs)

| Symptôme | Cause | Action |
|---|---|---|
| `fatal: not a git repository` avec `EXIT=128` à la racine | la racine du projet n'est pas un dépôt | énumérer les `.git`, puis utiliser `git -C` sur le vrai dépôt |
| `fatal: cannot change to '...ASTRO-Q°ODE_SYSTEME'` | chemin relatif ou non ASCII résolu depuis un autre répertoire courant | vérifier avec `test -d`, puis passer un chemin absolu entre guillemets |
| `UnicodeEncodeError: 'charmap' codec ... cp1252` | console Windows en cp1252 | forcer `PYTHONIOENCODING=utf-8` ou sortir en ASCII ; le script d'inventaire force l'UTF-8 |
| `warning: ... CRLF will be replaced by LF` | normalisation des fins de ligne | informationnel ; ne pas réécrire tout le dépôt |
| `?? scripts/__pycache__/` dans le statut | imports Python | exclure ; ajouter des chemins explicites, ou `.gitignore` après accord |
| branche `master` sur un dépôt, `main` sur un autre | historiques différents | lire `rev-parse --abbrev-ref HEAD` ; ne rien supposer |
| tests qui réécrivent des fichiers scellés après le commit | génération relancée par les tests | relire le diff, puis commit `chore(...)` séparé |
| réponse « TOUT » à une question de périmètre | le périmètre reste ambigu | proposer la liste exacte des dépôts et fichiers, la faire confirmer avant `git add` |
| push rejeté (non-fast-forward ou historiques sans rapport) | dépôt de Skill sans lien avec `origin` | pousser une branche dédiée ; ne jamais forcer |
| `nothing to commit` alors qu'un commit est attendu | changements déjà commités ou mauvais dépôt | vérifier `git log` et `git status` dans le dépôt réel |
| `Fingerprint (final)` inchangé après modification de `scripts/` ou `references/` | le fingerprint ne couvre que `SKILL.md` | recalculer les SHA-256 des ressources ; ne pas conclure que rien n'a changé |
| Skill modifié non résolu ou introuvable | index runtime non rechargé, ou homonyme projet qui masque | invoquer le Skill, vérifier les deux racines, puis demander `/skills reload` à l'utilisateur |

## Checklist finale

- [ ] Dépôt réel localisé par chemin absolu, branche lue.
- [ ] Changements SESSION et PREEXISTANT séparés ; préexistants confirmés.
- [ ] Aucun `git add -A` ni `git add .` ; chemins explicites.
- [ ] Tests exécutés et résultats consignés ; `RESULT PASS` si un Skill change.
- [ ] Diff relu ; aucun secret, binaire volumineux ni `__pycache__`.
- [ ] Un commit par sujet, message aligné sur l'historique.
- [ ] Statut post-commit propre, ou effets de bord expliqués et commités.
- [ ] Push uniquement sur demande ; remote, branche et hash vérifiés.
- [ ] Empreintes SHA-256 de `SKILL.md`, `scripts/` et `references/` relevées ; le `Fingerprint` seul ne couvre que `SKILL.md`.
- [ ] Skill modifié résolu par invocation réelle ; aucune homonymie projet/utilisateur ; `/skills reload` laissé à l'utilisateur.

## Rapport

```text
Dépôt : <chemin absolu> | Branche : <nom>
Commits : <hash court> <sujet>
Fichiers : <N> | Tests : <résultat>
Push : non effectué | <remote> <branche> <hash distant>
Skill : <nom> | résolution : <base-dir> | empreintes : <sha SKILL.md> <n scripts> <n references> (si un Skill est modifié)
```

## Ressources

- `scripts/inspect_git_state.py` : inventaire lecture seule des dépôts, branches, statuts, diffs et remotes ; sortie ASCII, codes 0/1/2.
- `references/skill-zh.md` : version chinoise complète, à maintenir structurellement parallèle ; les règles de parité sont décrites par `skill-doc-translation-parity`.
