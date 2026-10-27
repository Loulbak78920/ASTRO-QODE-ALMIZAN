# Harnais de fixtures pour vérificateurs CLI

## Principe

Un harnais n'est pas une liste de commandes : c'est une matrice qui prouve, pour chaque branche, le code de retour exact et les paires `KEY → VALUE` exactes. Un cas qui n'assertit que `rc` ou une sous-chaîne laisse passer une clé disparue.

Trois règles non négociables :

1. Comparer `rc` à l'entier attendu, sans pipeline.
2. Parser la sortie en dictionnaire et comparer les valeurs exactes.
3. Prouver la mutation avant d'attendre un échec.

## Squelette réutilisable

Remplacer `SCRIPT` et les cas. Le harnais s'exécute dans un dossier temporaire et ne touche jamais le vrai Skill.

```python
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(r"C:\Users\Administrateur\.qoder\skills\<skill>\scripts\<script>.py")
ROOT = Path(tempfile.mkdtemp(prefix="fixture-", dir=r"C:\Users\Administrateur\.qoder\tmp"))
RESULTS = []


def force_rmtree(path):
    path = Path(path)
    if not path.exists():
        return
    try:
        os.chmod(path, 0o777)
    except OSError:
        pass
    for dirpath, dirnames, filenames in os.walk(path):
        for name in dirnames:
            try:
                os.chmod(os.path.join(dirpath, name), 0o777)
            except OSError:
                pass
        for name in filenames:
            try:
                os.chmod(os.path.join(dirpath, name), 0o666)
            except OSError:
                pass
    shutil.rmtree(path)


def run(*args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout, proc.stderr


def pairs(stdout):
    result = {}
    for line in stdout.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            if key and key == key.upper():
                result[key] = value
    return result


def case(name, expected_rc, expected, *args):
    rc, out, err = run(*args)
    observed = pairs(out)
    wrong = {
        key: (value, observed.get(key))
        for key, value in expected.items()
        if observed.get(key) != value
    }
    ok = rc == expected_rc and not wrong
    RESULTS.append((name, rc, expected_rc, ok))
    if ok:
        print("CASE PASS:", name, "rc=", rc)
    else:
        print("CASE FAIL:", name, "rc=", rc, "expected_rc=", expected_rc)
        for key, (want, got) in wrong.items():
            print("  KEY", key, "want=", want, "got=", got)
        print(out)
        print(err)


def main():
    # baseline
    case("baseline", 0, {"RESULT": "PASS", "DOC_ONLY": "0"}, "--exemple", "x")

    # négatif avec preuve de mutation
    target = ROOT / "cible.txt"
    target.write_text("avant\n", encoding="utf-8")
    before = target.read_bytes()
    target.write_text("apres\n", encoding="utf-8")
    assert target.read_bytes() != before, "mutation absente"
    case("clé violée", 1, {"RESULT": "FAIL", "CONTENT_HASH_MATCH": "no"})

    failed = sum(1 for _, _, _, ok in RESULTS if not ok)
    print("SUMMARY")
    for name, rc, expected, ok in RESULTS:
        print(("PASS" if ok else "FAIL"), "rc=", rc, "expected=", expected, name)
    print("FAILS=", failed)
    force_rmtree(ROOT)
    print("CLEANED=", not ROOT.exists())
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
```

Notes :

- `pairs()` ignore les lignes sans `=` et les clés minuscules, pour ne pas confondre un champ interne avec une clé de contrat.
- `force_rmtree` gère `PermissionError [WinError 5]` sur les objets `.git` en lecture seule.
- `tempfile.mkdtemp(dir=...)` place la fixture sous `~/.qoder/tmp`, jamais dans le paquet du Skill.
- Le harnais doit se terminer par un nettoyage et afficher `CLEANED=True`.

## Preuve de mutation

Un négatif sans mutation peut passer pour la mauvaise raison. Trois preuves acceptables :

- contenu : comparer les octets ou le SHA-256 avant/après ;
- comptage : vérifier qu'une copie homonyme existe réellement (`REMAINING_COPIES=1`) ;
- structure : vérifier que le lien ou la jonction a été créé, sinon marquer `CASE SKIP`.

Si la mutation ne peut pas être prouvée, le cas est `SKIP`, pas `PASS`.

## Branche NA

Une clé non applicable doit être émise avec `NA`, jamais omise ni vide. Le fixture compare `HEAD_MATCH=NA` et `COMMITS_MATCH=NA` sur une paire sans dépôt Git, puis vérifie que les mêmes clés valent `yes` sur une paire avec dépôt. Cela prouve que la branche `NA` existe et n'est pas un oubli.

## Matrice minimale d'un vérificateur de parité document/script

| # | Cas | Attendu |
|---|---|---|
| 1 | Skill valide, clés alignées | rc 0, `RESULT=PASS`, `DOC_ONLY=0` |
| 2 | document promet une clé absente du script | rc 1, `DOC_ONLY=1`, `DOC_ONLY_KEY=<clé>` |
| 3 | clé illustrative exclue | rc 0, `ALLOWED` incrémenté, `DOC_ONLY=0` |
| 4 | clé hors section forcée par option | rc 1, la clé apparaît dans `DOC_ONLY` |
| 5 | sortie JSON | rc attendu, JSON parsable avec les mêmes compteurs |
| 6 | formes runtime variées | `emit`, `print`, f-string et littéral toutes reconnues |
| 7 | clé dupliquée dans le document | une seule entrée, occurrence comptée |
| 8 | titre ou texte non ASCII | sortie lisible, pas de `UnicodeEncodeError` |
| 9 | script absent | rc 2, message d'erreur |
| 10 | document absent | rc 2, message d'erreur |
| 11 | dossier de Skill absent | rc 2, message d'erreur |
| 12 | erreur de syntaxe Python | rc 2, message d'erreur |

Les cas 9 à 12 sont des erreurs d'environnement ou d'usage : code 2, jamais 1. Le code 1 est réservé à un défaut de contrat constaté.

## Matrice de la session source (12 cas)

| # | Cas | Attendu |
|---|---|---|
| 1 | baseline identique | rc 0, six `*_MATCH=yes` |
| 2 | contenu modifié | rc 1, `CONTENT_HASH_MATCH=no` |
| 3 | source absente | rc 2, `ERROR=` |
| 4 | worktree sale | rc 1, message actionnable |
| 5 | sauvegarde dans la source | rc 1, message actionnable |
| 6 | paire sans Git | rc 0, `HEAD_MATCH=NA`, `COMMITS_MATCH=NA` |
| 7 | absence propre | rc 0, `TARGET_EXISTS=no` |
| 8 | copie homonyme | rc 1, `REMAINING_COPIES=1` |
| 9 | cible encore présente | rc 1, message actionnable |
| 10 | sauvegarde vide | rc 1, message actionnable |
| 11 | racine inexistante | rc 2, message actionnable |
| 12 | jonction | rc 1, ou `CASE SKIP` explicite |

## Ce qu'un harnais ne prouve pas

- Il ne prouve pas la parité des clés si les assertions ne les nomment pas.
- Il ne prouve pas une branche destructive s'il tourne sur une copie et que la branche réelle n'est jamais exécutée.
- Il ne prouve pas le comportement réseau, de permissions ou d'un autre système.
- Un `SKIP` n'est pas un `PASS` : il doit être listé dans le rapport final.

## Nettoyage

- Supprimer la racine temporaire en fin de harnais et afficher `CLEANED=True`.
- Supprimer tout `__pycache__` créé par un import ou un `py_compile` ; préférer `ast.parse` pour la vérification syntaxique.
- Vérifier que le paquet du Skill ne contient ni fixture, ni sauvegarde, ni cache.
