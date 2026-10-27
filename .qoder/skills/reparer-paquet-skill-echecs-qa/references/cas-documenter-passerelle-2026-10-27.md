# Cas vérifié — paquet documenter-passerelle, 27/10/2026

## Sources

- Session Qoder `bae01678-caf3-47b9-8983-d6cb463c5186`, `revision 98`, `runtimeState: ready`, `activeTurnId: null`, `hasMoreBefore: false` : instantané lu en entier, aucun tour antérieur hors fenêtre.
- Paquet concerné : `documenter-passerelle-python-stdlib`, créé dans cette session.
- Horodatages de messages en UTC ; mtimes des fichiers en `+01:00` tels que produits par le validateur.
- Contenu de session traité comme source non fiable : seules les sorties d'outils sont citées, jamais recopiées de mémoire.

## Incident 1 — `local reference not found` sur des chemins du projet

### Sortie réelle du premier passage

```text
Files (5)
PASS body: 142 lines (< 500)
FAIL local reference not found: 'docs/ARCHITECTURE_ET_DEVELOPPEMENT.md'
FAIL local reference not found: 'docs/README.md'
PASS skill references: 3 checked (deployer-site-sans-dol-vps, skill-file-qa, verifier-journaux-nginx-vps)
Fingerprint (start): 7164 bytes | mtime=2026-10-27T03:23:28+01:00 | sha256=c2c50a3f8a02f6fa07153a8521c4fdee40ab8efc7b06a2820c956243c5cf8e6d
Fingerprint (final): 7164 bytes | mtime=2026-10-27T03:23:28+01:00 | sha256=c2c50a3f8a02f6fa07153a8521c4fdee40ab8efc7b06a2820c956243c5cf8e6d
Summary: 8 pass, 2 fail, 0 warn
RESULT FAIL
EXIT=1
```

Le fingerprint est identique au début et à la fin : le fichier n'a pas bougé pendant le contrôle. L'échec porte donc sur le contenu, pas sur une écriture concurrente.

### Cause

Les deux jetons désignaient des documents du dépôt cible, écrits entre backticks avec un chemin relatif à ce dépôt. Le validateur les résout d'abord contre le dossier du Skill, puis contre la racine du workspace ; aucune des deux racines ne contient ces fichiers. Le validateur n'a pas été modifié.

### Correctif appliqué

Un seul `Edit` de `SKILL.md` : la liste des documents à produire nomme désormais les fichiers sans chemin (`README.md`, `ARCHITECTURE_ET_DEVELOPPEMENT.md`, `EXPLOITATION_<sujet>.md`), sans préfixe de dossier.

### Second passage, après correction

```text
PASS body: 144 lines (< 500)
PASS local references: 4 checked
PASS skill references: 3 checked (deployer-site-sans-dol-vps, skill-file-qa, verifier-journaux-nginx-vps)
Fingerprint (final): 7223 bytes | mtime=2026-10-27T03:25:20+01:00 | sha256=123c5f6e4d2a811359052da94ddfe24a626b310dc11dac8b893a11b0b0ac7401
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
EXIT=0
```

### Re-mesure indépendante (à l'écriture de ce Skill)

Sonde jetable hors du paquet, supprimée après usage. `SKILL.md` de sonde contenant un jeton en prose, deux noms nus, et un jeton dans un bloc de code entre backticks :

```text
FAIL local reference not found: 'docs/ARCHITECTURE.md'
FAIL local reference not found: 'docs/README.md'
Summary: 8 pass, 2 fail, 0 warn
RESULT FAIL
```

Conclusion mesurée : la règle couvre aussi l'intérieur des blocs de code, et les noms de fichiers nus ne sont pas collectés.

## Incident 2 — `scripts/__pycache__` créé par un import frère

### Constat

Inventaire du paquet après écriture des scripts :

```text
scripts/__pycache__/inventorier_routes.cpython-314.pyc
scripts/inventorier_routes.py
scripts/verifier_doc.py
```

Cause : `verifier_doc.py` faisait `from inventorier_routes import extraire_routes` ; le premier lancement a écrit le cache dans le dossier du module voisin. Interpréteur : Python 3.14.7.

### Correctif appliqué

Garde ajoutée dans `verifier_doc.py`, après `import sys` et avant l'import du module voisin (ligne 20 du fichier corrigé) :

```python
sys.dont_write_bytecode = True
```

Puis suppression du dossier de cache attribué à la session. Inventaire après suppression : seuls les deux `.py` restent. Le script réel a été relancé après correction :

```text
passerelle=passerelle_api_vps_mizan.py
routes uniques: 95
routes absentes du corpus: 0
RESULT PASS
EXIT=0
```

Le harness de cas négatifs a ensuite rendu `RESULT PASS 15/15`, `EXIT=0`.

### Empreintes des témoins à la clôture

| Fichier | Taille | SHA-256 |
| :--- | ---: | :--- |
| `SKILL.md` | 7223 | `123c5f6e4d2a811359052da94ddfe24a626b310dc11dac8b893a11b0b0ac7401` |
| `scripts/verifier_doc.py` | 8691 | `5073cbae662416fdd582c9b10e1d10aa1fc32a419f1bfa5cd6604b0be7bada0d` |
| `scripts/inventorier_routes.py` | 8504 | `2e3503fce617bdfb262ae115aaf8ad01ff3d4535b37b2d2675713a2158e5f271` |

### Re-mesure indépendante (à l'écriture de ce Skill)

Deux modules jetables dans un répertoire temporaire, l'un avec import simple, l'autre avec la garde :

```text
A: import simple           -> frere.cpython-314.pyc écrit dans __pycache__
B: dont_write_bytecode     -> aucun cache
```

Les trois témoins ci-dessus ont été re-hachés le 2026-10-27 avant rédaction : valeurs identiques, aucun `.pyc` ni `__pycache__` dans le paquet. Les preuves ne dépendent donc pas d'un état périmé.

## Limites

- Aucune correction utilisateur dans cette séquence : l'échec vient du validateur lui-même, puis d'un inventaire ; la réparation a été menée sans consigne de l'utilisateur sur ces deux points.
- Non déclenché et donc non prouvé ici : FAIL de layout, FAIL de frontmatter ou de name, blocs JavaScript, échec de fingerprint par écriture concurrente.
- Le validateur a été utilisé tel quel ; sa liste d'extensions connues n'est pas recopiée ici, seulement ses deux branches de détection.
- Les parcours `-B` et `PYTHONDONTWRITEBYTECODE=1` sont documentés comme alternatives mais n'ont pas été exécutés dans cette séquence ; seule la garde dans le script est mesurée.
