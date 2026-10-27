# Preuves datées — audit de livraison en lecture seule

Observations du 2026-10-27 sur Windows 10.0.26200, Git Bash, CPython 3.14
(`py -3`), console locale en cp1252. Les empreintes et numéros de ligne sont
datés : ils ne sont pas des constantes durables.

## 1. Session source

| Champ | Valeur |
| :--- | :--- |
| Identifiant | `d95a27a5-2a67-408a-b23b-f9d194a2232e` |
| Titre | 创建 Steane 逻辑量子比特 Skill |
| `runtimeState` | `opening` |
| `revision` | 3 |
| `hasMoreBefore` | `false` |
| Messages | 3 : demande (2026-10-27T03:51:40.841Z), tour assistant `completed` (03:51:40.935Z), `/skills reload` (03:58:01.605Z) |
| Outils du tour assistant | 53 appels indexés 0–52 |

Le tour a créé le Skill de domaine `qubit-logique-steane-preuves` et son audit
`scripts/auditer_livraison_qubit.py`. Les faits ci-dessous sont lus dans les
sorties d'outils enregistrées, pas reconstitués de mémoire.

## 2. Sorties de la session (verbatim)

### 2.1 Import sans `sys.modules` — outil 33

```text
== run (default detection from cwd) ==
ERREUR import module: AttributeError: 'NoneType' object has no attribute '__dict__'
rc=2
```

Même sortie : l'instantané « avant » ne liste que le nom de dossier
`['__pycache__']`, l'instantané « après » liste des fichiers `.pyc`. Les deux
inventaires n'ont pas la même forme : **le nombre de caches créés par ce premier
lancement n'est pas établi** (voir §4).

### 2.2 Sortie non-ASCII sur console cp1252 — outil 28

```text
Traceback (most recent call last):
  File "<string>", line 4, in <module>
    print('materiel', json.dumps(r['materiel'],ensure_ascii=False)[:600])
UnicodeEncodeError: 'charmap' codec can't encode ...
```

### 2.3 Garde active : caches inchangés — outil 35

```text
== before ==
pycache_count 115 list_sha 08212158f99c
== audit ==
OK   module 8c6c3d7ec242
OK   preuves: distance=3 poids_min=3 paulis=211 corrections=21
OK   resume: schema + hash 8c6c3d7ec242
OK   artefacts: 11/11
OK   page: /qubit-logique autonome
OK   routes: page + 3 alias API + 404
OK   sitemap: 13 URLs
RESULT PASS (7 controles)
rc=0
== after ==
pycache_count 115 list_sha 08212158f99c
```

Égalité stricte du compte **et** de l'empreinte de liste avant/après : aucun
cache ajouté ni retiré par l'audit corrigé.

### 2.4 Fixtures négatives — outil 36

```text
== fixture audit (hash mutated) ==
FAIL resume: hash resume 8c6c3d7ec242 != module 66233b432b34 (relancer --rapport)
RESULT FAIL (1/7 controles en echec)
rc=1
== missing root ==
ERREUR racine introuvable; passer --racine <ASTRO-Q\xb0ODE_SYSTEME>
rc=2
cleanup=OK
```

Un seul FAIL, sur le contrôle de fraîcheur visé : la mutation est ciblée.

### 2.5 Références locales au projet — outil 38

```text
PASS layout: 3 file(s), no extraneous documentation
FAIL local reference not found: 'docs/API_PASSERELLE_VPS.md'
FAIL local reference not found: 'docs/EXPLOITATION_VPS.md'
FAIL local reference not found: 'docs/QUBIT_LOGIQUE.md'
FAIL local reference not found: 'resultats/qubit_logique/resume.json'
FAIL local reference not found: 'tests/test_qubit_http_mizan.py'
FAIL local reference not found: 'tests/test_qubit_logique_mizan.py'
FAIL local reference not found: 'web_cloud/qubit_logique.html'
Summary: 8 pass, 7 fail, 0 warn
RESULT FAIL
rc=1
```

Le tour se termine ensuite sur un PASS à 9 références (outil 52). La valeur de
`--workspace` utilisée pour ce PASS n'est pas dans la sortie capturée du FAIL ;
le mécanisme est prouvé séparément en §3.3.

### 2.6 Commande documentée cassée — outil 43

```text
C:\...\python.exe: can't open file 'C:\\Program Files\\Git\\scripts\\auditer_livraison_qubit.py': [Errno 2] No such file or directory
rc=2
```

Le chemin MSYS racine montre une variable vide au moment du développement des
arguments. Le texte exact de la commande n'est pas capturé ; le mécanisme est
reproduit en §3.4.

## 3. Reproductions locales (2026-10-27, fiches nettoyées)

### 3.1 Annotations différées et `sys.modules`

Fixture `mod.py` :

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Parametres:
    duree_s: float = 20e-9


def valeur() -> float:
    return Parametres().duree_s
```

| Chargeur | Résultat |
| :--- | :--- |
| `spec_from_file_location` + `module_from_spec` + `exec_module` | `AttributeError` à `dataclasses.py:814` dans `_is_type` (`ns = sys.modules.get(cls.__module__).__dict__`), rc=1 |
| idem + `sys.modules[spec.name] = module` avant `exec_module` | `OK 2e-08`, rc=0 |
| `@dataclass` non gelé, mêmes annotations différées | même `AttributeError` |

Conclusion : le déclencheur est l'annotation sous forme de chaîne, pas `frozen`.
La ligne 814 est celle de CPython 3.14 ; elle varie selon la version.

### 3.2 Cache bytecode

| Scénario | `.pyc` créés |
| :--- | :--- |
| `sys.modules` enregistré, sans `-B`, sans garde | 1 |
| `sys.dont_write_bytecode = True`, sans `-B` | 0 |
| `-B`, sans garde Python | 0 |
| garde Python + `-B` (socle) | 0 |

La garde Python est le correctif effectif pour le module importé ; `-B` couvre en
plus un interpréteur enfant. Le socle vérifie les deux moitiés :

```text
OK   temoin: sans sys.modules -> rc=1
OK   temoin: AttributeError observe
OK   chargeur enregistre: rc=0
OK   sans garde: 1 .pyc ecrit (garde necessaire)
OK   module charge en processus: valeur attendue
OK   garde active: aucun .pyc ajoute (avant=apres)
OK   sortie ASCII: non-ASCII echappe
OK   codes de retour: 0 pour PASS, 1 pour FAIL
RESULT PASS (8 controles)
```

### 3.3 `--workspace` et références locales

Skill synthétique contenant le jeton d'un document du projet, avec le fichier
réel placé dans `<depot>/ASTRO-Q°ODE_SYSTEME/docs/` :

| `--workspace` | Sortie | Code |
| :--- | :--- | :--- |
| racine du dépôt | `FAIL local reference not found`, `Summary: 8 pass, 1 fail` | 1 |
| `<depot>/ASTRO-Q°ODE_SYSTEME` | `PASS local references: 2 checked`, `Summary: 9 pass, 0 fail` | 0 |

Le validateur essaie `skill_dir / ref` puis `workspace / ref` : la sous-racine
qui contient réellement les chemins documentés est celle à passer.

### 3.4 Affectation Bash inline

```bash
D=/tmp/xyz py -3 -c "print(argv)" "$D/x.py"   # -> C:/Program Files/Git/x.py
D=/tmp/xyz
py -3 -c "print(argv)" "$D/x.py"              # -> .../Temp/xyz/x.py
```

`$D` est développé par le shell avant que l'affectation ne s'applique : la
première forme produit un chemin à la racine MSYS. Correctif : deux lignes.

### 3.5 Console cp1252

Imprimer un JSON non-ASCII avec `py -3` a levé `UnicodeEncodeError: 'charmap'
codec` dans cette session de travail également. `PYTHONIOENCODING=utf-8` ou
`ensure_ascii=True`/échappeur ASCII corrige.

## 4. Ce qui n'est pas prouvé

- **Nombre de `.pyc` créés par le premier lancement (outil 33)** : inventaires de
  formes différentes, aucune conclusion de comptage. Seules les égalités
  avant/après de l'outil 35 et la reproduction §3.2 sont probantes.
- **Valeur de `--workspace` ayant produit les 7 FAIL** : la commande n'est pas
  capturée. La règle de résolution est lue dans le validateur et le mécanisme est
  reproduit en §3.3 ; l'attribution exacte du FAIL de session reste une inférence.
- **Texte exact de la commande Bash cassée (outil 43)** : seul le chemin résultant
  est capturé ; le mécanisme est reproduit, pas la ligne d'origine.
- **« il faut `-B` en plus de la garde »** : la reproduction montre que la garde
  Python suffit pour le module importé ; `-B` est une défense supplémentaire, pas
  une condition nécessaire.
- **« un module avec `@dataclass` échoue toujours »** : faux sans annotations
  différées. La condition est `from __future__ import annotations` (ou toute
  annotation chaîne), vérifiée en §3.1.

## 5. Classification

| Affirmation | Statut |
| :--- | :--- |
| `sys.modules` requis pour les dataclasses à annotations différées | reproduit |
| garde bytecode nécessaire, `-B` complémentaire | reproduit |
| `skill-file-qa` résout les références contre le workspace | reproduit |
| cp1252 casse une sortie non-ASCII | vérifié en session et reproduit |
| affectation inline vide la variable dans les arguments | reproduit |
| copie falsifiée rc=1 avec un seul FAIL, racine absente rc=2 | vérifié en session |
| nombre de caches créés au premier lancement | non prouvé |

## 6. Empreintes observées

Fin de session (outil 46, horodatage local +01:00) :

| Fichier | Taille | SHA-256 |
| :--- | ---: | :--- |
| `qubit-logique-steane-preuves/SKILL.md` | 9147 | `7d827f359425e1bcf943e7ff4d16aa9fb1813479d96996d4a6ecce12372cc58a` |

Relecture du disque après la session (2026-10-27, environ 05:00 local) :

| Fichier | Taille | SHA-256 |
| :--- | ---: | :--- |
| `qubit-logique-steane-preuves/SKILL.md` | 11113 | `9aea56446624597891a4d9c85a7e44005574c8cc0f64f53775b71df5fc374ea9` |
| `qubit-logique-steane-preuves/references/preuves-et-pieges.md` | 12804 | `053d94010e47528ca296597df4b7fd7a46bc59f6e813ee4244081ed5d7efe8fa` |
| `qubit-logique-steane-preuves/scripts/auditer_livraison_qubit.py` | 9585 | `763bb78f679dd31b590ef437bb5cc093f4f26de33fef0bb1852ab793bf0bea9f` |

Les tailles diffèrent de celles de la session : le Skill de domaine a été modifié
après le tour. Ces valeurs sont des observations datées, pas des attendus.
