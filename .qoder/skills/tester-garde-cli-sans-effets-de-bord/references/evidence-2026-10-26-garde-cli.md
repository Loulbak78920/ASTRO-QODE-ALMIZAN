# Preuves verifices — fixture A/B du 2026-10-26

## Source

- Session : `37a77c12-803a-4d48-9865-298d847ea879`.
- `read_chat_session` : revision 16, `runtimeState=running` au moment de la lecture.
- La sortie de l'outil depassait la limite de 25 000 jetons : elle a ete enregistree
  dans un fichier temporaire, puis relue integralement par tranches. Aucun contenu
  n'est reconstitue de memoire.
- JSONL brut correspondant :
  `C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/37a77c12-803a-4d48-9865-298d847ea879.jsonl`.
- La session etait encore active pendant la redaction : les branches executees apres
  la derniere lecture ne sont pas couvertes par ce document.

## Fails constates dans la session source

### 1. Un faux git.bat dans PATH n'est pas utilise

Un `git.bat` a ete place en tete de `PATH` pour repondre a `git credential fill`.
Sous Windows, `subprocess.run(["git", ...])` a resolu le vrai `git.exe` via
`CreateProcess` : le marqueur du faux binaire est reste a `B_CREDENTIAL_CALLED=no`.
Le vrai helper de credentials a donc ete appele (lecture seule, aucun jeton affiche).
Conclusion : un shim de type `.bat` dans `PATH` ne prouve rien sur les appels
`subprocess`.

### 2. L'espion en processus fonctionne

Le module cible a ete charge avec `importlib.util.spec_from_file_location`, puis
`subprocess.run` a ete remplace avant l'appel de l'entree. Resultat mesure :

```text
scenario sans --yes : GIT_CALLS=0  exit=2  TOKEN_LEAK=no
scenario avec --yes : GIT_CALLS=1  exit=2  TOKEN_LEAK=no
```

Les deux scenarios partagent le meme code de sortie : seul le compteur d'appels
distingue le refus reel d'un refus survenu apres lecture des credentials.

### 3. L'import direct a pollue le paquet

Importer le script voisin depuis son propre dossier a cree
`scripts/__pycache__/github_pr_api.cpython-314.pyc`. `skill-file-qa` a continue
d'afficher `RESULT PASS` avec `Files (4)`. Apres suppression du cache :
`Files (3)`, 9 pass / 0 fail / 0 warn. La validation statique ne suffit donc pas :
la fixture doit copier le script et interdire l'ecriture de bytecode.

## Fixture livree

- Script : `scripts/tester_garde_cli.py`.
- Empreinte au moment de la redaction :
  `4211960ec459f910567bca8ecc2ef74da2fd80804e65fa505f3dcd4899819e91`
  (21 073 octets, 554 lignes).
- Cible de reference : copie de `github_pr_api.py`, SHA-256
  `768ce189d42c3943dcfb8c7cae941a9fe1ae2e19d549e76a83bc4fcda15cf137`
  (12 966 octets), identique a la source avant et apres execution.

### Executions verifiees

Deux executions avec des identifiants fictifs differents (`owner/repo` puis
`owner/other`) ont donne 24 controles conformes et `RESULT PASS`, code de sortie 0.

```text
CHILD scenario=deny  exit=2 proc=0 git=0 net=0 urlopen=0 socket=0 import_proc=0 import_net=0 marker=yes leak=no
CHILD scenario=allow exit=2 proc=1 git=1 net=1 urlopen=1 socket=0 import_proc=0 import_net=0 marker=na  leak=no
EXEC git credential fill
EXCERPT CREDENTIAL_USER fixture-user | PULLS_FAIL status=0 body=NETWORK_FAIL fixture-network-blocked
SUMMARY checks=24 failed=0
RESULT PASS
CLEANUP removed=True
```

Controles negatifs reellement executes :

- mutation `--expect-deny-git 1` : `deny.proc` et `deny.git` en echec,
  `RESULT FAIL`, code de sortie 1, scenario autorise ignore ;
- script dont le corps de module appelle `Path.write_text` : refus de preflight
  `RESULT FAIL setup=effet-de-bord-au-import ['.write_text()']`, code 2 ;
- aucun `__pycache__` cree dans le dossier de la cible ni dans le repertoire
  jetable apres les executions conformes.

## Limites verifiees

- Le chemin de succes n'est pas teste : le reseau est bloque, donc le scenario
  autorise s'arrete sur `NETWORK_FAIL` avec le meme code 2 que le refus.
- Aucun identifiant, jeton ou appel reseau reel n'a ete utilise.
- Une seule cible a ete exercee (`github_pr_api.py`, sous-commande `create`).
- Les API `subprocess` autres que `run`, ainsi que `requests`/`httpx`/`aiohttp`,
  ne sont pas espionnees ; le preflight echoue par defaut dans ce cas.
- La fixture n'est pas un sandbox : les ecritures fichier et les appels systeme
  atteints a l'execution ne sont pas interceptes.
- Le comportement du faux `.bat` a ete observe sur cette machine Windows ; il n'est
  pas generalise a d'autres systemes.
