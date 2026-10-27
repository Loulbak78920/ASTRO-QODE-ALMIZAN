---
name: tester-garde-cli-sans-effets-de-bord
description: "Tester hors production le pré-contrôle d'un CLI (par exemple --yes) et la non-fuite d'un secret : copier le script cible dans une fixture jetable, importer son module dans un processus enfant lancé avec -B, remplacer subprocess.run, urllib.request.urlopen et socket par des espions, puis comparer en A/B le nombre exact d'appels git et réseau, les codes de sortie et les marqueurs, et vérifier qu'un jeton sentinelle n'apparaît ni dans stdout/stderr ni dans argv ; enfin contrôler l'absence de __pycache__ et relancer skill-file-qa. Utiliser pour prouver qu'un refus intervient avant toute lecture de credentials ou tout accès réseau, pour reproduire le cas Windows où un git.bat placé dans PATH n'est pas utilisé par subprocess.run, ou pour éviter un faux positif où deux scénarios partagent le même code de sortie. Ne couvre pas les chemins de succès réels, requests/http.client, ni un sandbox. 中文触发：CLI 前置门、--yes 拒绝、无副作用测试、进程内 spy、subprocess.run 替换、网络根阻断、调用次数断言、令牌不泄露、假 git.bat 失效、__pycache__ 污染、A/B 夹具、退出码相同。"
---

# Tester un pré-contrôle CLI sans effet de bord

## Portée

Prouver, hors production, qu'un refus (par exemple l'absence de `--yes`) intervient
**avant** toute lecture de credentials et tout accès réseau, et qu'aucun jeton fictif
ne fuit dans les sorties ou dans `argv`.

Le résultat attendu n'est pas seulement « le CLI a échoué » : c'est un nombre exact
d'appels sous-processus et réseau dans chaque scénario, un marqueur de refus, et un
compteur d'import à zéro.

Ce Skill ne remplace pas :

- `skill-file-qa` pour l'acceptation statique du paquet après écriture ;
- `skill-update-concurrency-safe` pour la stabilité des fichiers et le nettoyage des caches ;
- `valider-harnais-fixture-windows-msys` pour une fixture Git jetable et ses contrôles négatifs ;
- `audit-skill-tool-contracts` pour le contrat d'un outil réutilisé ;
- `adopt-concurrent-duplicate-skill` si une cible concurrente apparaît pendant le travail ;
- `github-pr-create-merge-sans-gh` pour le flux réel de création et fusion de PR.

## Quand utiliser

- Un CLI possède un drapeau de confirmation et l'on veut prouver que le refus précède
  `git credential fill`, `urlopen` ou un sous-processus.
- Deux scénarios A/B ont le même code de sortie et l'on doit distinguer le refus réel
  d'un échec survenu après des effets de bord.
- Un faux exécutable placé dans `PATH` n'a pas été appelé par `subprocess.run`.
- L'import direct d'un script voisin a créé un `__pycache__` dans son paquet.

Ne pas utiliser pour tester un chemin de succès réel, pour valider une API distante,
ou comme substitut à un sandbox.

## Contrat non négociable

1. **Lire la cible avant de la croire.** Vérifier dans le code que le `return` de refus
   précède l'appel à `credentials()` et à la fonction réseau. Un drapeau documenté ne
   prouve pas l'ordre.
2. **Copier le script cible** dans un répertoire jetable. Ne jamais importer depuis son
   dossier d'origine.
3. **Enfant avec `-B`** et `sys.dont_write_bytecode = True`. Vérifier ensuite l'absence
   de `__pycache__` dans le paquet cible.
4. **Espionner `subprocess.run` en processus.** Un shim `.bat` en tête de `PATH` n'est
   pas utilisé par `subprocess.run` sous Windows : il ne compte rien et peut laisser
   passer le vrai binaire.
5. **Espionner `urllib.request.urlopen` et `socket.socket` / `create_connection`.**
   Lever une erreur et incrémenter un compteur ; ne jamais joindre l'URL configurée.
6. **Compter tous les sous-processus**, puis distinguer `git`. Un total supérieur au
   nombre d'appels `git` signale une autre commande.
7. **Exiger un import inerte** : `import_proc = 0` et `import_net = 0`. Tout effet de
   bord au chargement du module est un échec de fixture.
8. **Un seul variable entre A/B** : les mêmes arguments, plus le drapeau de
   confirmation. Ne pas changer l'entrée, l'environnement ou la charge utile.
9. **Comparer des nombres exacts**, pas `>=`. Un `>=` masque les tentatives multiples,
   les retries et les appels supplémentaires.
10. **Refus d'abord.** Si le scénario refusé n'est pas conforme, ne pas exécuter le
    scénario autorisé : cela simulerait la lecture de credentials après un échec.
11. **Jeton sentinelle** absent de stdout, stderr et `argv`. Ne jamais imprimer le
    contenu brut des credentials ; l'extrait doit être assaini.
12. **Contrôle par mutation obligatoire** avant de faire confiance à un `PASS` :
    fausser une attente et exiger `RESULT FAIL` avec un code non nul.
13. **Ne pas confondre code 2 identique et refus prouvé.** Le refus se prouve par les
    compteurs et le marqueur, pas par le seul code de sortie.
14. **Nettoyer** le répertoire jetable et vérifier sa disparition ; conserver les
    empreintes SHA-256 avant/après de la cible.

## Étape 0 — Lire la cible et localiser la porte

```bash
grep -n -E "REFUS|--yes|def credentials|urlopen|subprocess\.run|def cmd_" \
  "C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh/scripts/github_pr_api.py"
```

Vérifier que la branche de refus revient avant `credentials()` et avant l'appel réseau.
Relever le marqueur exact (par exemple `CREATE_REFUSED`) et le code de sortie.

Si la porte est après les credentials, ce n'est pas un pré-contrôle : le documenter et
s'arrêter, ne pas adapter la fixture pour la faire passer.

## Étape 1 — Lancer la fixture A/B

Placer `--argv` en dernier : il consomme les arguments restants, y compris ceux qui
commencent par `--`.

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/tester-garde-cli-sans-effets-de-bord/scripts/tester_garde_cli.py" \
  --script "C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh/scripts/github_pr_api.py" \
  --deny-marker CREATE_REFUSED \
  --expect-allow-exit 2 \
  --argv create --repo owner/repo --head fixture-branch --base main --title Fixture
```

Le drapeau `--yes` est ajouté automatiquement au scénario autorisé. Pour un autre
drapeau, utiliser la forme avec signe égal, par exemple `--allow-flag=--force`.

Le script copie la cible, vérifie l'égalité SHA-256 source/copie, exécute le scénario
refusé, puis le scénario autorisé seulement si le premier est conforme, et supprime le
répertoire jetable dans `finally`.

## Étape 2 — Interpréter les preuves

Sortie conforme observée sur `github_pr_api.py` (sous-commande `create`) :

```text
CHILD scenario=deny  exit=2 proc=0 git=0 net=0 urlopen=0 socket=0 import_proc=0 import_net=0 marker=yes leak=no
CHILD scenario=allow exit=2 proc=1 git=1 net=1 urlopen=1 socket=0 import_proc=0 import_net=0 marker=na  leak=no
EXEC git credential fill
EXCERPT CREDENTIAL_USER fixture-user | PULLS_FAIL status=0 body=NETWORK_FAIL fixture-network-blocked
SUMMARY checks=24 failed=0
RESULT PASS
```

Les deux codes valent 2 : c'est normal quand le réseau est bloqué. La preuve est
`deny.git=0` / `deny.net=0` contre `allow.git=1` / `allow.net=1`, avec
`import_proc=0`, `import_net=0`, `marker=yes`, `leak=no`.

- `SKIP scenario=allow motif=refus-non-conforme` : corriger la porte, pas la fixture.
- `allow.exit=0` : ne pas conclure à un chemin de succès ; vérifier que le réseau a
  réellement été bloqué et que l'attente correspond à la cible.
- `phase=import` : effet de bord au chargement du module ; refuser ou déplacer le code.
- `deny.proc` ou `deny.git` non nul : le refus intervient après un sous-processus.

## Étape 3 — Contrôle par mutation

Relancer une fois avec une attente volontairement fausse :

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/tester-garde-cli-sans-effets-de-bord/scripts/tester_garde_cli.py" \
  --script "C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh/scripts/github_pr_api.py" \
  --deny-marker CREATE_REFUSED \
  --expect-allow-exit 2 \
  --expect-deny-git 1 \
  --argv create --repo owner/repo --head fixture-branch --base main --title Fixture
```

Attendu : `RESULT FAIL ['deny.proc', 'deny.git']`, code de sortie 1, scénario autorisé
ignoré. Si la mutation passe, les assertions sont vides et le `PASS` précédent ne vaut
rien.

## Étape 4 — Caches, résidus et acceptation statique

```bash
find "C:/Users/Administrateur/.qoder/skills/tester-garde-cli-sans-effets-de-bord" \
     "C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh/scripts" \
     -name "*.pyc" -o -name "__pycache__"
```

La sortie doit être vide. Puis relancer la validation statique et exiger le nombre de
fichiers attendu :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "C:/Users/Administrateur/.qoder/skills/tester-garde-cli-sans-effets-de-bord" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" \
  --skills-root "C:/Users/Administrateur/.qoder/skills" \
  --stable-seconds 2
```

Attendu : `Files (3)`, `RESULT PASS`. Un `Files (4)` accompagné d'un `PASS` signale un
cache `.pyc` : le supprimer et relancer, car la validation statique ne le refuse pas.

## Échecs fréquents

| Symptôme | Cause | Action |
|---|---|---|
| Le vrai `git` est appelé malgré le faux binaire | `subprocess.run` résout `git.exe`, pas le `.bat` du `PATH` | Importer et espionner `subprocess.run` en processus |
| `deny` et `allow` ont tous deux `exit=2` | Fin normale avec réseau bloqué | Comparer compteurs et marqueurs, pas les codes |
| `import_proc` ou `import_net` non nul | Le module agit au chargement | Refuser, ou déplacer l'effet dans l'entrée |
| `Files (4)` avec `RESULT PASS` | Import direct ayant écrit un `.pyc` | Copier la cible, `-B`, supprimer le cache, relancer |
| `leak=yes` | Credentials imprimés ou fichier relu | S'arrêter, ne pas coller la sortie, corriger la cible |
| `RESULT FAIL setup=api-non-espionnee` | `Popen`, `os.system` ou `requests` détecté | Ajouter l'espion ; `--allow-unsupported` seulement si l'entrée testée ne l'atteint pas |
| `RESULT FAIL setup=effet-de-bord-au-import` | Écriture au niveau module | Refuser la cible ou la corriger |
| `target.sha256` en échec | Écriture concurrente de la cible | Relire la cible, relancer, ne pas écraser |
| Mutation conforme | Assertions trop larges | Remplacer `>=` par une égalité exacte |

## Limites

- Le chemin de succès réel n'est pas testé : le réseau est bloqué et les credentials
  sont fictifs. Ne jamais l'affirmer validé.
- Seul `subprocess.run` est espionné ; `Popen`, `os.system` et les bibliothèques HTTP
  tierces sont refusés par le preflight, sauf dérogation explicite.
- La fixture n'est pas un sandbox : les écritures fichier et les appels système atteints
  à l'exécution ne sont pas interceptés.
- Le comportement du faux `.bat` a été observé sous Windows ; il n'est pas généralisé.
- Les preuves de la session source sont datées du 2026-10-26 ; la session était encore
  active, donc les branches postérieures ne sont pas couvertes.

## Ressources

- `scripts/tester_garde_cli.py` : fixture A/B exécutable, préflight AST, espions,
  assertions exactes, nettoyage et contrôle de cache.
- `references/evidence-2026-10-26-garde-cli.md` : faits vérifiés, sorties observées,
  contrôles négatifs et limites.
