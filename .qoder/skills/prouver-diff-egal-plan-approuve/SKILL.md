---
name: prouver-diff-egal-plan-approuve
description: "Preuve post-exécution qu'un diff réel égale la liste approuvée : relire la baseline enregistrée avant écriture (instantane_cible.py --enregistrer --copie), localiser les octets de référence sous <copie>/files/<rel> et jamais <copie>/<rel> (sinon diff rc=2), produire diff -u et distinguer rc 0/1/2, compter les blocs avec diff -U0 sans confondre fusion de hunks et édition manquante, prouver ID par ID que le nouveau texte est présent et l'original absent, confirmer par --comparer que seuls les fichiers annoncés sont CHANGED et que les autres sont CURRENT, puis valider avec validate_skill.py et trois échantillons size/mtime/SHA-256. Utiliser après avoir appliqué une liste E1..En approuvée, pour répondre « prouve que tu n'as changé que ça », ou quand un diff échoue en rc=2. 中文触发：证明只改了批准的几处、执行后 diff 对账、副本目录布局、diff rc=2、hunk 数不等于改动数、未涉及文件应 CURRENT、写入后哈希稳定性。English: post-write diff proof, approved list reconciliation, baseline copy layout, hunk count, per-file CHANGED/CURRENT, stability re-sample."
---

# Prouver que le diff égale le plan approuvé

## Objectif

Après avoir appliqué une liste d'éditions approuvée, produire une preuve reproductible que le disque ne contient **que** ces éditions. Le contrôle ne repose ni sur la mémoire de l'agent ni sur un diff relu à l'œil : il compare les octets enregistrés **avant** écriture aux octets actuels, puis attribue chaque différence à un ID approuvé.

## Quand l'utiliser

- Une liste `E1..En` a été approuvée puis appliquée ; il faut répondre « prouve que tu n'as changé que ça ».
- Un diff vient d'échouer avec `rc=2` ou semble vide alors que des éditions ont été faites.
- Il faut dire quels fichiers ont bougé sans relire tout l'arbre.
- Plusieurs sessions travaillent dans le même dossier et il faut distinguer les éditions approuvées des écritures étrangères.

## Quand ne pas l'utiliser

- Aucune baseline n'a été enregistrée avant écriture : les octets de référence n'existent plus → `prouver-baseline-avant-diff` (reconstruction), pas ce Skill.
- Rien n'est encore approuvé ni écrit : c'est le passage de `confirmer-plan-avant-ecriture`.
- Le but est de vérifier la sémantique d'un compteur de hunks sur une fixture dense → `verifier-comptage-diff-fixture-dense`.

## Vocabulaire

| Terme | Sens | Piège |
|---|---|---|
| Baseline | JSON `size`/`mtime_ns`/`sha256` par fichier, écrit avant les éditions | Un hash seul ne restaure rien |
| Copie de référence | Octets sauvegardés par `--copie` | Ils vivent sous `<copie>/files/<rel>`, pas sous `<copie>/<rel>` |
| Bloc (`hunk`) | Groupe contigu de lignes modifiées dans un diff | Deux éditions proches peuvent fusionner en un bloc |
| Liste approuvée | IDs `E1..En` avec fichier:ligne, original → nouveau, compte | Un ID = une édition localisée |

## Étape 0 — Réunir les trois artefacts

Il faut la liste approuvée, le JSON de baseline et la copie d'octets. Le script s'appelle `instantane_cible.py` et appartient au Skill `confirmer-plan-avant-ecriture` ; ne pas le réécrire ici.

```bash
# rappel : exécuté AVANT les éditions
py -3 "<confirmer-skill>/scripts/instantane_cible.py" \
  --racine "<cible>" \
  --enregistrer "<baseline.json>" \
  --copie "<copie>"
```

Si `--copie` n'a pas été utilisé, arrêter : sans octets de référence, le diff contre l'état actuel ne prouve rien. Basculer vers `prouver-baseline-avant-diff`.

## Étape 1 — Localiser la copie de référence

La copie est écrite sous `<copie>/files/<chemin relatif>`. Ne jamais supposer `<copie>/<chemin relatif>`.

```bash
find "<copie>" -type f
sha256sum "<copie>/files/SKILL.md"
```

- Le fichier doit exister sous `files/`. Sinon, la baseline n'a pas copié les octets : arrêter, ne pas diffuser un diff contre un chemin vide.
- Le SHA-256 du fichier copié doit égaler celui de la baseline. S'il diffère, la copie est corrompue ou la baseline est d'un autre état : arrêter.

## Étape 2 — Produire le diff

```bash
diff -u "<copie>/files/SKILL.md" "<cible>/SKILL.md"
echo "rc=$?"
```

| rc | Sens | Suite |
|---|---|---|
| 0 | Aucune différence | Les éditions annoncées sont absentes, ou le mauvais fichier est comparé : ne pas conclure « rien à signaler » |
| 1 | Différences présentes | Cas attendu après application ; passer à l'étape 3 |
| 2 | Comparaison impossible (chemin, option, permission) | **Ne signifie pas « aucune différence »** : corriger le chemin puis recommencer |

Un `diff` en `rc=2` ne prouve rien et ne doit jamais être rapporté comme un diff vide. Ne pas faire passer `diff` dans un pipe avant de lire `$?` : le code retour serait celui de la dernière commande du pipe (`head`, `grep`), pas celui de `diff`.

## Étape 3 — Attribuer chaque différence à un ID

Compter les blocs sans contexte :

```bash
diff -U0 "<copie>/files/SKILL.md" "<cible>/SKILL.md" | grep -c '^@@'
```

Le nombre de blocs est un **minorant** du nombre d'éditions : `diff -u` fusionne deux modifications séparées de six lignes inchangées ou moins, et `diff -U0` fusionne encore des modifications contiguës. Ne pas conclure « il manque une édition » ni « il y a une édition de trop » sur ce seul chiffre.

Prouver chaque ID séparément, avec des chaînes fixes. Pour un remplacement de ligne entière, tester la ligne complète (`-x`) :

```bash
grep -Fc  -- "<nouveau texte>" "<cible>/SKILL.md"   # attendu : le compte annoncé
grep -Fxc -- "<texte original>" "<cible>/SKILL.md"  # attendu : 0 pour une ligne remplacée
```

`grep` renvoie 1 quand le compte est 0 : lire la valeur affichée, pas le code retour. Pour une substitution partielle (« ligne2 » → « ligne2 APPROUVE »), `<texte original>` reste présent comme sous-chaîne et un `grep -Fc` le compte encore : comparer des lignes entières ou choisir un fragment absent du nouveau texte.

Puis compter les lignes réellement modifiées :

```bash
diff -U0 "<copie>/files/SKILL.md" "<cible>/SKILL.md" | grep -c '^[-+][^-+]'
```

Une substitution compte pour 2 lignes (une retirée, une ajoutée). Une édition qui ne produit aucune ligne modifiée (no-op) n'apparaît pas dans le diff : la déclarer « non prouvée par diff », pas « appliquée ».

## Étape 4 — Vérifier l'ensemble des fichiers touchés

```bash
py -3 "<confirmer-skill>/scripts/instantane_cible.py" \
  --racine "<cible>" \
  --comparer "<baseline.json>"
```

| Ligne | Sens | Verdict |
|---|---|---|
| `… CURRENT` | fichier identique à la baseline | attendu pour tout fichier hors liste |
| `… CHANGED fields=size,mtime_ns,sha256` | contenu et/ou métadonnées ont bougé | attendu uniquement pour les fichiers approuvés |
| `… CHANGED fields=mtime_ns` | contenu identique, seule la date a bougé | pas une édition ; le SHA-256 prouve le contenu |
| `… ADDED` / `… REMOVED` | fichier apparu ou disparu | `hors périmètre` sauf mention explicite dans la liste approuvée |

`rc=0 / RESULT: UNCHANGED` contredit un diff non vide : les deux contrôles ne portent pas sur la même cible, ou le diff venait d'un autre état. Recommencer, ne pas choisir le résultat qui arrange.

## Étape 5 — Clore par la validation et la stabilité

Si la cible est un Skill, lancer le validateur statique du Skill `skill-file-qa` :

```bash
py -3 "<skill-file-qa>/scripts/validate_skill.py" "<cible>"
```

Puis échantillonner trois fois la taille et le SHA-256 du fichier écrit, à quelques secondes d'intervalle. Une variation entre deux échantillons signale une écriture concurrente : reprendre à l'étape 1, attribuer l'écriture, et ne pas déclarer `PASS`.

## Rapport

```text
APPROVED=<n> editions / <f> fichiers
DIFF_RC=<0|1|2>
HUNKS=<n> (-U0)
CHANGED_LINES=<n>
FILES_CHANGED=<liste>
FILES_CURRENT=<n>
UNEXPECTED=<n> [IDs ou chemins]
QA=<PASS|FAIL|N/A>
STABLE=<yes|no>
RESULT=<PASS|FAIL>
```

`RESULT: PASS` exige : `DIFF_RC=1`, chaque ID prouvé (nouveau présent, original absent, compte exact), `FILES_CHANGED` exactement l'ensemble approuvé, `UNEXPECTED=0`, `STABLE=yes`, `QA≠FAIL`. Sinon écrire `FAIL` et l'écart constaté.

## Cas vérifié — session 6b24a8c5, 2026-10-28

| Fait | Valeur observée |
|---|---|
| Liste approuvée | 2 éditions, 1 fichier : `SKILL.md:139` et insertion après `:48` |
| Baseline | `SKILL.md` 9 857 o / `433833d5…` ; script `0b1ddd6d…` |
| Premier diff | chemin `<copie>/SKILL.md` → `No such file or directory`, `diff rc=2` |
| Layout réel | `<copie>/files/SKILL.md` (trouvé par `find`) |
| Diff correct | `rc=1`, 2 hunks, 2 blocs attribués aux 2 IDs |
| `--comparer` | `SKILL.md CHANGED`, script `CURRENT`, `RESULT: CHANGED`, rc=1 |
| Après écriture | `SKILL.md` 10 177 o / `61a2f000…` |
| Validation | 9 pass, 0 fail, 0 warn, `RESULT PASS` |
| Stabilité | trois échantillons identiques entre 11:28:55 et 11:29:02 |
| Rejeu hors installation (2026-10-28) | `diff` dans un pipe → `$?` = 0 malgré un chemin absent ; `grep -Fc "ligne2"` = 1 sur « ligne2 APPROUVE » |

La leçon n'est pas « le diff a échoué » mais « `rc=2` dit que la comparaison n'a pas eu lieu ». Le premier chemin venait d'une hypothèse sur la layout, pas d'une observation.

## Limites

- Ce Skill ne juge pas la pertinence du plan : un plan approuvé peut être mauvais.
- Il suppose que la baseline a été prise **avant** les éditions ; sinon, voir `prouver-baseline-avant-diff`.
- Il ne remplace ni `confirmer-plan-avant-ecriture` (approbation et écriture), ni `verifier-comptage-diff-fixture-dense` (sémantique du compteur), ni `skill-file-qa` (validation statique), ni `skill-update-concurrency-safe` (écriture concurrente).
- Un `diff` vide prouve que la cible comparée n'a pas changé, pas que les éditions annoncées ont été appliquées.
