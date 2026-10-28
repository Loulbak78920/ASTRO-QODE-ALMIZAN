# Cas : réutiliser un validateur installé comme oracle — 2026-10-28

Environnement : Windows 10.0.26200, Git Bash, Python 3.14 (`py -3`), console cp1252. §2 condense chaque sortie réelle sur une ligne, les segments séparés par « / » venant de lignes distinctes ; §3 recopie les sorties intégralement. Tout est en ASCII.

## 1. Fait déclencheur, session source

Session `3eef2a41-5a24-4a66-a44b-791dfbbb336a`, état `cold`, révision 0, un tour : création de `qualifier-chemins-references-skill`. L'oracle est le validateur installé `validate_skill.py` du Skill `skill-file-qa` : 21 896 octets, SHA-256 `1932ce4840054675f0608616e05f9f2c55db5eb749255f6a30c4cfd46e6789d8`.

L'import du validateur par `importlib` a créé un cache dans un Skill tiers :

```text
HIT C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/__pycache__
HIT C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/__pycache__/validate_skill.cpython-314.pyc
```

Correctif présent sur disque (relu le 2026-10-28), dans le script consommateur :

```text
13  # Importing the validator must not create __pycache__ inside another skill.
14  sys.dont_write_bytecode = True
```

La garde précède l'appel `exec_module` du module dépendant, pas l'import de la bibliothèque standard : c'est l'exécution du script cible qui écrit le cache.

**Suppression.** La commande ad hoc a d'abord affiché `removed=0` ; les contrôles suivants ne listaient plus de cache (listing de `skill-file-qa/scripts` sans `__pycache__`). La suppression elle-même n'est donc pas proprement prouvée dans la session : c'est précisément ce flou que le harnais décrit en §3 supprime.

## 2. Parité avec l'oracle sur quatre fixtures (session source)

Script consommateur et validateur réels exécutés côte à côte, fixtures hors de toute racine de Skills.

```text
##### VALIDATOR A   PASS local references: 2 checked / RESULT PASS / RC=0
##### QUALIFIER A   SUMMARY counted=2 resolved=2 missing=0 skipped=0 / QUALIFIER PASS / RC=0
##### VALIDATOR B   FAIL local reference not found: 'deploiement_vps/deployer_vers_vps.py' / RESULT FAIL / RC=1
##### QUALIFIER B   COUNTED deploiement_vps/deployer_vers_vps.py MISSING via span / QUALIFIER FAIL / RC=1
##### VALIDATOR C   FAIL local reference not found: 'absent.md' / RESULT FAIL / RC=1
##### QUALIFIER C   SKIPPED 8 ... / QUALIFIER FAIL / RC=1
##### VALIDATOR D   PASS local references: 1 checked / RESULT PASS / RC=0
##### QUALIFIER D   MANUAL references/doc.md:1 ... MISSING / QUALIFIER PASS / RC=0
```

A : préfixe projet correct, les deux outils passent. B : la même référence non préfixée échoue des deux côtés — c'est la fixture qui reproduit un FAIL que la session de création amont n'avait jamais observé. C : seul `absent.md` est compté, huit jetons sont ignorés en silence. D : le validateur passe alors qu'un chemin cité dans `references/` manque — limite de l'oracle, pas une parité.

La branche « divergence de contrat » (rc 2) est implémentée et citée, mais jamais déclenchée : les fonctions recopiées correspondaient à celles du validateur.

## 3. Harnais local (vérifié le 2026-10-28)

Fixture jetable `~/.qoder/tmp/oracle-fixture`, copie du validateur, deux consommateurs : `oracle_guard.py` (garde avant `exec_module`) et `oracle_plain.py` (sans garde). Fixture purgée après les essais.

### A — consommateur gardé, base propre

```text
DEPENDANCE C:\Users\Administrateur\.qoder\tmp\oracle-fixture\dep
AVANT files=0 dirs=0
COMMANDE py -3 C:/Users/Administrateur/.qoder/tmp/oracle-fixture/oracle_guard.py C:/Users/Administrateur/.qoder/tmp/oracle-fixture/dep/scripts/validate_skill.py
API_OK True
ORACLE_RC=0
APRES files=0 dirs=0
NEW (none)
PROOF=NOT_RUN
ORACLE_RC_FINAL=0
NEW_RESIDUE=NONE
RESULT PASS
RC=0
```

### B — consommateur sans garde

```text
DEPENDANCE C:\Users\Administrateur\.qoder\tmp\oracle-fixture\dep
AVANT files=0 dirs=0
COMMANDE py -3 C:/Users/Administrateur/.qoder/tmp/oracle-fixture/oracle_plain.py C:/Users/Administrateur/.qoder/tmp/oracle-fixture/dep/scripts/validate_skill.py
API_OK True
ORACLE_RC=0
APRES files=1 dirs=1
NEW scripts/__pycache__/validate_skill.cpython-314.pyc 39338 bytes mtime_ns=1793154218023291700 sha256=47dddb823fa0
NEW_DIR scripts/__pycache__
PROOF=NOT_RUN
ORACLE_RC_FINAL=0
NEW_RESIDUE=PRESENT
RESULT FAIL
RC=1
```

### C — sans garde, `--nettoyer --rejouer`

```text
DEPENDANCE C:\Users\Administrateur\.qoder\tmp\oracle-fixture\dep
AVANT files=0 dirs=0
COMMANDE py -3 C:/Users/Administrateur/.qoder/tmp/oracle-fixture/oracle_plain.py C:/Users/Administrateur/.qoder/tmp/oracle-fixture/dep/scripts/validate_skill.py
API_OK True
ORACLE_RC=0
APRES files=1 dirs=1
NEW scripts/__pycache__/validate_skill.cpython-314.pyc 39338 bytes mtime_ns=1793154219478316300 sha256=47dddb823fa0
NEW_DIR scripts/__pycache__
REMOVED scripts/__pycache__/validate_skill.cpython-314.pyc
REMOVED_DIR scripts/__pycache__
APRES_NETTOYAGE files=0 dirs=0
COMMANDE py -3 C:/Users/Administrateur/.qoder/tmp/oracle-fixture/oracle_plain.py C:/Users/Administrateur/.qoder/tmp/oracle-fixture/dep/scripts/validate_skill.py
API_OK True
ORACLE_RC=0
APRES_REJEU files=1 dirs=1
NEW_REJEU scripts/__pycache__/validate_skill.cpython-314.pyc 39338 bytes mtime_ns=1793154220513390300 sha256=47dddb823fa0
NEW_REJEU_DIR scripts/__pycache__
PROOF=RECREATED
ORACLE_RC_FINAL=0
NEW_RESIDUE=PRESENT
RESULT FAIL
RC=1
```

### D — gardé, `--nettoyer --rejouer`

```text
DEPENDANCE C:\Users\Administrateur\.qoder\tmp\oracle-fixture\dep
AVANT files=0 dirs=0
COMMANDE py -3 C:/Users/Administrateur/.qoder/tmp/oracle-fixture/oracle_guard.py C:/Users/Administrateur/.qoder/tmp/oracle-fixture/dep/scripts/validate_skill.py
API_OK True
ORACLE_RC=0
APRES files=0 dirs=0
NEW (none)
APRES_NETTOYAGE files=0 dirs=0
COMMANDE py -3 C:/Users/Administrateur/.qoder/tmp/oracle-fixture/oracle_guard.py C:/Users/Administrateur/.qoder/tmp/oracle-fixture/dep/scripts/validate_skill.py
API_OK True
ORACLE_RC=0
APRES_REJEU files=0 dirs=0
NEW_REJEU (none)
PROOF=NO_RECREATION
ORACLE_RC_FINAL=0
NEW_RESIDUE=NONE
RESULT PASS
RC=0
```

### E et F — refus d'environnement (rc 2)

```text
FAIL  dependency directory not found: ...\oracle-fixture\absent
RC=2
FAIL  PYTHONDONTWRITEBYTECODE is set; the observation would be vacuous
RC=2
```

Un cache préexistant n'est jamais attribué à la session : essai séparé, depuis un dossier contenant déjà un `.pyc`, `--nettoyer` ne supprime rien et affiche `NEW (none)`.

## 4. Statut des affirmations

| Affirmation | Statut |
| :--- | :--- |
| L'import du validateur crée un `.pyc` chez le Skill tiers | observé (session source) |
| La garde avant `exec_module` empêche le cache ; après, non | observé (session source, fixtures §3 A/B et contre-exemple local) |
| La suppression du cache par la session source est prouvée | **non** — `removed=0` puis cache absent ; séquence floue |
| La parité script/oracle tient sur 4 fixtures | observé (session source) |
| La branche de divergence (rc 2) s'exécute | **non exercée** — citée dans le code seulement |
| L'instantané avant/après et l'attribution par mtime | prescrit ici, vérifié en §3 |
| Le FAIL non préfixé a été observé lors de la création amont | **non** — reproduit par la fixture B |

## 5. Limites

- Le nom du cache dépend de l'interpréteur (`cpython-314` observe) : détecter par chemin `__pycache__` et suffixe `.pyc`, jamais par nom exact.
- Le SHA-256 du `.pyc` varie avec le chemin source encodé dans le code : il ne sert pas d'identité stable entre fixtures.
- `PYTHONDONTWRITEBYTECODE` hérité rend l'observation vide de sens ; le harnais refuse alors en rc 2.
- Le harnais ne couvre que les caches. Journaux, index ou sceaux écrits par l'oracle relèvent de `verifier-effets-de-bord-verification-lecture-seule`.
- `python` est l'alias Microsoft Store (code 49) ; utiliser `py -3`.
