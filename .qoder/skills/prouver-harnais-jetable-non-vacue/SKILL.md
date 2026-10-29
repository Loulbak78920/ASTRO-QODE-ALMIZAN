---
name: prouver-harnais-jetable-non-vacue
description: "Prouver un harnais de mutation avant le premier rejeu réel : construire hors du Skill un faux vérificateur à trois gardes et une fixture, exiger POSITIF_OK, GARDE_DECLENCHE, NON_APPLIQUE, MAUVAISE_RAISON et POSITIF_CASSE avec les codes de sortie attendus, reproduire l'échec de convention d'appel (fichier contre répertoire), exiger la sortie brute sous SORTIE, puis vérifier la suppression des fixtures et l'empreinte du harnais. Un mutant vert n'est pas une preuve : GARDE_VACUE reste une sonde manuelle qui distingue une mutation inerte (commentaire exclu) d'un garde vacu. Utiliser quand un POSITIF_CASSE n'affiche aucun détail, quand tous les négatifs rendent MAUVAISE_RAISON, ou quand un mutant vert est présenté comme un succès. 中文触发：可丢弃 oracle、判定分支覆盖、目录与文件调用约定、原位惰性变异、绿色变异误判、原始输出缺失、夹具清理与哈希。English: prove a mutation harness on a disposable oracle, verdict-branch coverage, directory-versus-file convention, inert mutation, harness fingerprint."
---

# Prouver un harnais de test sur un oracle jetable

## Objectif

Un harnais qui juge un autre outil n'est pas prouvé par les PASS qu'il rend sur le vrai outil : rien ne dit que ses branches de verdict s'exécutent, ni qu'il lit l'entrée qu'il croit lire. Ce Skill le place d'abord face à un faux vérificateur minimal, dont chaque défaut produit un verdict connu, puis seulement il autorise le rejeu réel.

## Frontière avec les autres Skills

| Besoin | Skill |
|---|---|
| Prouver que chaque garde du vrai vérificateur se déclenche | `prouver-garde-statique-non-vacue` |
| Prouver qu'une mutation a bien été écrite sur la copie | `verifier-mutation-fixture-appliquee` |
| Tester le validateur de paquets Skill avec sa suite fixe | `skill-validator-selftest` |
| Développer un nouveau vérificateur et sa matrice de fixtures | `develop-skill-static-checker` |
| Passer la porte d'acceptation d'un harnais de fixture Windows | `valider-harnais-fixture-windows-msys` |
| Rejouer des fixtures documentées | `replay-skill-reference-fixtures` |
| Prouver le harnais qui juge les gardes | ce Skill |

Ce Skill ne modifie ni le harnais ni le vérificateur audité. Un correctif se fait dans une édition séparée, validée par `skill-file-qa`.

## Invariants

1. **Un harnais non exercé n'est pas un harnais.** Un PASS sur le vrai outil ne prouve aucune branche de verdict.
2. **L'oracle suit la convention d'appel du harnais.** Le harnais copie la source puis transmet la copie : si la source est un répertoire, le vérificateur reçoit un répertoire.
3. **Chaque verdict du contrat doit être observé.** Le script couvre cinq verdicts ; `GARDE_VACUE` reste une sonde manuelle (étape 5) et n'est pas prouvé par un PASS du script.
4. **Un écart doit être lisible.** Sans sortie brute, `POSITIF_CASSE` est opaque ; le harnais doit afficher les dernières lignes de l'outil jugé.
5. **Vert n'est pas valide.** Un mutant vert peut être une mutation inerte (région exclue par le vérificateur) ou un garde vacu. Trancher par la région mutée et par ce que le garde lit réellement.
6. **Le rejeu réel ne commence qu'après PASS de l'oracle.** Le vrai cas ne sert pas à découvrir que le harnais est cassé.
7. **Fixtures hors installation, originaux en lecture seule.** Supprimer les copies, revérifier les empreintes du harnais et des sources.

## Étape 1 — Construire l'oracle

Le script écrit l'oracle dans `~/.qoder/tmp/prouver-harnais.*` :

- `toy.txt` : `ALPHA`, `GAMMA=ok`, puis `# BETA interdit` en commentaire.
- `toy_verifier.py` : résout un répertoire vers `toy.txt`, ignore les lignes `#`, applique trois gardes `alpha` (ALPHA présent), `beta` (BETA interdit), `gamma` (GAMMA=ok), et imprime `GARDE ok|FAIL`, `DETAIL`, `RESULT:`.
- `toy_naif.py` : lit son argument comme un fichier. Il reproduit l'échec de convention observé sur le vrai harnais.

L'oracle reste volontairement minuscule : il ne teste pas le domaine, il teste le harnais.

## Étape 2 — Matrice des cas

| Cas | Attendu | rc |
|---|---|---|
| `ok` | `POSITIF_OK` + 3 `GARDE_DECLENCHE` | 0 |
| `non_applique` | `POSITIF_OK` + `NON_APPLIQUE` | 1 |
| `mauvaise` | `POSITIF_OK` + `MAUVAISE_RAISON` | 1 |
| `convention` | `POSITIF_CASSE` + `MAUVAISE_RAISON`, avec `SORTIE` non vide | 1 |

Chaque exécution doit aussi afficher `COUVERTURE ok` et `FIXTURES ABSENTES`, et ne jamais afficher `SOURCE_DRIFT`.

## Étape 3 — Exécuter

```bash
py -3 scripts/jouer_oracle.py --harnais "C:/Users/Administrateur/.qoder/skills/prouver-garde-statique-non-vacue/scripts/prouver_gardes.py"
```

Sortie observée le 2026-10-29 :

```text
HARNAIS C:\Users\Administrateur\.qoder\skills\prouver-garde-statique-non-vacue\scripts\prouver_gardes.py sha256=99c0e9dbd381
ORACLE C:\Users\Administrateur\.qoder\tmp\prouver-harnais.i171f9fx
RUN ok rc=0 verdicts=POSITIF_OK=1,GARDE_DECLENCHE=3 attendu=POSITIF_OK=1,GARDE_DECLENCHE=3 etat=CONFORME
RUN non_applique rc=1 verdicts=POSITIF_OK=1,NON_APPLIQUE=1 attendu=POSITIF_OK=1,NON_APPLIQUE=1 etat=CONFORME
RUN mauvaise rc=1 verdicts=POSITIF_OK=1,MAUVAISE_RAISON=1 attendu=POSITIF_OK=1,MAUVAISE_RAISON=1 etat=CONFORME
RUN convention rc=1 verdicts=MAUVAISE_RAISON=1,POSITIF_CASSE=1 attendu=MAUVAISE_RAISON=1,POSITIF_CASSE=1 etat=CONFORME
ORACLE_ABSENT
RESULT: PASS runs=4 verdicts=5
```

`--garder` conserve l'oracle pour inspection ; sans lui, le script supprime son répertoire et l'annonce par `ORACLE_ABSENT`.

## Étape 4 — Lire un écart

| Symptôme | Cause probable | Action |
|---|---|---|
| `POSITIF_CASSE` et tous les négatifs en `MAUVAISE_RAISON` | le vérificateur d'oracle lit la copie comme un fichier alors que le harnais passe un répertoire | corriger l'oracle, pas le harnais ; vérifier que `SORTIE` nomme l'erreur |
| `NON_APPLIQUE` | ancre absente ou présente plusieurs fois, empreinte inchangée | changer d'ancre ; aucune conclusion sur le harnais |
| `MAUVAISE_RAISON` | exit 1 mais `DETAIL` attendu absent | comparer `DETAIL_ATTENDU` et `DETAIL_OBSERVE`, le harnais échoue pour autre chose |
| `verdict_inattendu` | verdict hors contrat | lire le protocole du harnais, ne pas l'ignorer |
| `absent='SORTIE '` | la branche de diagnostic positive ne s'exécute pas | rétablir l'affichage brut avant de conclure |

Les huit lignes `BRUT` en cas d'écart sont un extrait ; relancer avec `--garder` pour l'oracle complet.

## Étape 5 — Sonde verte (`GARDE_VACUE`, hors script)

Le script ne produit pas `GARDE_VACUE`. Pour prouver cette branche, muter à la main une région que le vérificateur correct exclut volontairement, par exemple l'exemple `<html lang=".." dir="..">` d'un commentaire d'en-tête :

- sortie verte et `GARDE_VACUE` du harnais : mutation inerte attendue, pas un succès du garde ; exiger `GARDE_OBSERVE` montrant l'entrée réellement lue (`lang=fr` par exemple) ;
- sortie toujours verte après une mutation dans une région active : garde réellement vacu, à diagnostiquer comme un défaut du vérificateur.

Le harnais installé ne connaît pas de verdict attendu : toute mutation verte produit un `RESULT: FAIL` global. L'interprétation est donc manuelle et doit être écrite dans le rapport, jamais déduite du seul code de sortie.

## Étape 6 — Rejeu réel, nettoyage et scellé

Après un PASS de l'oracle seulement :

1. Rejouer les cas réels avec `prouver-garde-statique-non-vacue`.
2. Supprimer les fixtures et confirmer leur absence.
3. Recalculer le SHA-256 du harnais, des sources et des fixtures : identiques au relevé initial.
4. Si le harnais appartient à un Skill, relancer `skill-file-qa` après toute correction ; ne pas l'éditer dans ce flux.

## Rapport

| Élément | Valeur |
|---|---|
| Harnais | chemin, SHA-256 avant et après |
| Oracle | répertoire, cas, verdicts observés |
| Convention | fichier ou répertoire, erreur brute le cas échéant |
| Verdicts | cinq couverts par le script, `GARDE_VACUE` manuel |
| Nettoyage | `ORACLE_ABSENT`, fixtures du harnais absentes |
| Limites | branches non exercées, protocole du harnais |

## Ressources

- [scripts/jouer_oracle.py](scripts/jouer_oracle.py) : oracle généré, quatre cas, assertions et nettoyage.
- [references/cas-harnais-prouver-gardes-2026-10-29.md](references/cas-harnais-prouver-gardes-2026-10-29.md) : preuves verbatim, corrections et limites.
