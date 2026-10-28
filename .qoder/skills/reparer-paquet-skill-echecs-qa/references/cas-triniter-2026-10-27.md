# Cas vérifié — paquet observateur-triniter-spectre-plasma, 27/10/2026

## Sources

- Session Qoder `7b17d684-a43b-45e9-b265-a2b37026a622`, `revision 109`, `runtimeState: ready`, `activeTurnId: null`, `hasMoreBefore: false` : `read_chat_session` ne renvoie que le dernier tour (2 messages). Les tours antérieurs ont été relus dans le JSONL du projet, `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\7b17d684-a43b-45e9-b265-a2b37026a622.jsonl` (430 lignes).
- Messages utilisateur réels (hors `tool_result`) : trois seulement — 15:13:39Z (requête de création du Skill), 15:22:17Z (résumé de compaction écrit par le système), 15:26:04Z (« 把这些结论整理成一份简短的汇报文档 »).
- **Aucune correction utilisateur** : les passages QA (neuf, un, puis zéro FAIL) et les deux corrections de commandes sont des itérations de l'agent. Le rationale de la recommandation qui parle de corrections utilisateur n'est pas soutenu par la session.
- Paquet concerné : `observateur-triniter-spectre-plasma`, créé dans cette session. Racine des chemins documentés : `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME`, imbriquée dans la racine Qoder `C:\Users\Administrateur\Desktop\IMAM8MAHDI`.
- Horodatages de messages en UTC ; mtimes de fichiers en `+01:00`. Les sorties ci-dessous sont citées telles quelles, jamais recopiées de mémoire.

## Incident 1 — neuf références sous une racine imbriquée

### Premier passage (15:21:39Z)

Commande exécutée depuis la racine Qoder, avec `--workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI"` :

```text
Fingerprint (start): 12264 bytes | mtime=2026-10-27T16:17:56+01:00 | sha256=3466692b717e400a3fdb7604ce4e9c667c8a4f6defb597daf8cdc9f7db8b18dd
PASS body: 159 lines (< 500)
FAIL local reference not found: 'actes/_ignorance_spectrale_plan.json'
FAIL local reference not found: 'conscience_logique/__init__.py'
FAIL local reference not found: 'conscience_logique/sauvegarde_soi.py'
FAIL local reference not found: 'conscience_logique/savoir_complet.py'
FAIL local reference not found: 'conscience_logique/spectre_plasma_couche.py'
FAIL local reference not found: 'tests/test_site_public_mizan.py'
FAIL local reference not found: 'web_cloud/observateur_triniter.html'
FAIL local reference not found: 'web_cloud/portail_public_al_mizan.html'
FAIL local reference not found: 'web_cloud/tableau_maitre_sequentiel.html'
Summary: 8 pass, 9 fail, 0 warn
RESULT FAIL
RC=1
```

### Cause

`check_refs` résout chaque jeton contre `skill_dir / ref`, puis `workspace / ref` (`scripts/validate_skill.py:236-246`, lignes au 27/10/2026). Les neuf fichiers existent, mais sous `ASTRO-Q°ODE_SYSTEME` ; le `--workspace` passé était la racine Qoder.

### Correctif

Aucune modification du paquet : second passage avec `--workspace ".../ASTRO-Q°ODE_SYSTEME"`.

### Second passage (15:22:23Z)

```text
FAIL local reference not found: 'actes/_ignorance_spectrale_plan.json'
Summary: 8 pass, 1 fail, 0 warn
RESULT FAIL
```

## Incident 2 — un jeton réellement faux

`ls` confirme que `ASTRO-Q°ODE_SYSTEME/actes` n'existe pas ; `find` localise `conscience_logique/actes/_ignorance_spectrale_plan.json`. Le fichier `references/cablage-site-et-contrat.md:94` portait déjà le bon chemin ; seule la ligne 101 de `SKILL.md` disait `actes/...`.

Correctif : un `Edit` de `SKILL.md:101`, `actes/` → `conscience_logique/actes/`.

### Troisième passage (15:22:47Z)

```text
Fingerprint (start): 12283 bytes | mtime=2026-10-27T16:22:41+01:00 | sha256=231a27342788dd560bb00c16d0fd803cdfa58859df7ad96f88f152f4452ccb79
PASS local references: 13 checked
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
RC=0
```

## Incident 3 — QA PASS mais commande inexécutable depuis la racine documentée

`SKILL.md` contenait deux fois la commande `py -3 scripts/verifier_observateur_triniter.py`, dans deux blocs `bash` exécutés depuis la racine projet (l'un via `cd "$R"`, l'autre via un `cd` absolu). La QA résout `scripts/...` contre le dossier du Skill, où le script existe, et passe ; le shell la résout contre le cwd et échoue.

Deux `Edit` (15:23:36Z et 15:23:39Z) remplacent la commande par le chemin absolu du script du Skill. Contrôle final (15:23:56Z) :

```text
PASS local references: 13 checked
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
RC=0
---
./SKILL.md 12416 7723275eb3c5eedfdd4b58f295c88c797506eaa7323828b287a56faaca3e5f54
./references/cablage-site-et-contrat.md 7467 35e9f2aee3fbbb65992f1032d6be36d114bb68733337c2bda33fd893ead33a83
./references/modele-spectre-7-etats.md 8272 11846cb4b79daf01427f6dca04cdf1cd3274224b3876062f88507fa6357c0cd8
./references/preuves-verification-2026-10-27.md 10386 a387237a7886767edb03e5ac5bf2a245fe0d1fda9e6d1a707de346215029d493
./scripts/verifier_observateur_triniter.py 9414 3d8484d4bf3ef935eb4aa11fa8f6d7a3e313245a376c9e55f069e311afe0245e
CACHES=0
```

Script réel exécuté sur le projet : `CONTROLES_OK=53`, `CONTROLES_TOTAL=53`, `RESULT OK`, RC=0, avec notamment `CHECK_K_CONTINUITE=OK` et `VALUE_K_CONTINUITE=1.0`.

Limite de portabilité : la correction de cette session écrit un chemin personnel `C:/Users/...`. Une forme `$HOME/.qoder/skills/<nom>/scripts/...` est préférable ; elle est elle aussi ignorée par le validateur (`$`), donc non vérifiée statiquement.

## Incident 4 — le fichier de preuves ne peut pas contenir sa propre empreinte

`references/preuves-verification-2026-10-27.md` enregistre `SKILL.md` à 12416 B / `7723275e...` et laisse sa propre ligne d'empreinte à `—`, avec la mention exacte :

```text
auto-référence : l'empreinte changerait en s'inscrivant elle-même
```

L'empreinte finale du fichier de preuves (`a387237a...`) n'apparaît que dans le rapport de livraison, pas dans le fichier lui-même.

## Règles de scannage vérifiées par sonde (27/10/2026)

Sondes jetables créées hors des racines de Skills et supprimées après exécution.

### Formes scannées

Fixture avec un jeton backtické en prose, un autre dans un bloc de code, et un lien Markdown dans un bloc :

```text
FAIL local reference not found: 'missing/prose.py'
FAIL local reference not found: 'missing/fenced.py'
FAIL local reference not found: 'missing/linked.md'
Summary: 8 pass, 3 fail, 0 warn
RESULT FAIL
```

Conclusion : les jetons backtiqués sont scannés **même dans un bloc de code** ; les liens Markdown le sont aussi.

### Formes ignorées

Fixture avec `/abs/file.py`, `~/home/file.py`, `../up/file.py`, `C:/win/file.py` et `[l](C:/win/linked.md)` :

```text
PASS local references: 0 checked
Summary: 9 pass, 0 fail, 0 warn
RESULT PASS
```

`normalize_ref` ignore les chemins absolus POSIX, `~`, `..`, les lettres de lecteur, les URL, les ancres, et les jetons contenant espace, `<`, `>`, `{`, `}`, `*`, `?`, `=` ou `#`.

### Racine imbriquée

Fixture `parent/systeme/pkg/x.py`, jeton `pkg/x.py` :

```text
--workspace parent   -> FAIL local reference not found: 'pkg/x.py'   (RC=1)
--workspace parent/systeme -> PASS local references: 1 checked       (RC=0)
```

Conclusion : la racine à passer est celle des chemins documentés, pas la racine Qoder.

## Re-mesure à l'écriture de cette mise à jour (27/10/2026)

Après l'ajout de ce cas et des sections A.2 et C au paquet, QA relancée depuis le dossier du Skill :

```text
Files (3): SKILL.md, references/cas-documenter-passerelle-2026-10-27.md, references/cas-triniter-2026-10-27.md
PASS description: single line, 986 chars
PASS body: 255 lines (< 500)
PASS local references: 2 checked
PASS skill references: 5 checked
Fingerprint (start): 16400 bytes | mtime=2026-10-27T16:32:16+01:00 | sha256=85874bb70d3c39313c53510b604f14a7539ca5309ca1104410e8b51acce68fb1
Fingerprint (final): 16400 bytes | mtime=2026-10-27T16:32:16+01:00 | sha256=85874bb70d3c39313c53510b604f14a7539ca5309ca1104410e8b51acce68fb1
Summary: 10 pass, 0 fail, 0 warn
RESULT PASS
RC=0
```

Les deux sondes A.4 ont été rejouées après écriture : `docs/README.md` → FAIL RC=1 ; racine parent → FAIL RC=1 ; racine `parent/systeme` → PASS, 1 référence vérifiée, RC=0. Aucun répertoire de sonde résiduel.

`SKILL.md` n'a pas changé depuis le passage ci-dessus ; les corrections apportées ensuite à ce seul fichier de cas ne modifient pas son empreinte. L'empreinte de ce fichier de cas n'est pas inscrite ici (auto-référence) ; elle figure dans le rapport de livraison.

## Limites

- Un seul `--workspace` par passage : deux racines réelles ne peuvent pas être satisfaites simultanément. Choisir la racine qui maximise les références vérifiées et déclarer les autres non vérifiées.
- Les formes `$VAR/...` et les chemins absolus ne sont plus vérifiés par la QA : un PASS ne prouve pas leur existence.
- La QA statique ne prouve pas qu'une commande documentée s'exécute dans le cwd annoncé (incident 3) ; il faut la lancer depuis ce cwd et lire le code de retour.
