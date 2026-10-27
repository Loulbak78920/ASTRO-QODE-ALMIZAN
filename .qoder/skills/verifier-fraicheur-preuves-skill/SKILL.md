---
name: verifier-fraicheur-preuves-skill
description: "Vérifier la fraîcheur des preuves d'un Skill avant livraison : recalculer size, mtime_ns et SHA-256 des fichiers cités, classer chaque affirmation « courante / inchangée / N fichiers » en CONFIRME, PERIME, ABSENT ou INDETERMINE, ajouter une observation datée §N sans réécrire l'historique, synchroniser la section « cas vérifié » du SKILL.md et marquer PROVISIONAL tant que le paquet audité peut changer ; terminer par des hashes séparés et skill-file-qa. Utiliser avant commit, publication ou remise d'un Skill avec archive de preuve, quand une QA est PASS mais qu'une référence présente encore des valeurs comme courantes, ou quand une session a proposé une mise à jour sans l'exécuter. 中文触发：Skill 证据新鲜度、引用哈希过期、当前值复核、§N 追加、快照时点同步、PROVISIONAL、交付前门禁、QA 只覆盖 SKILL.md、历史不改写。"
---

# Vérifier la fraîcheur des preuves d'un Skill avant livraison

## Objectif et limites

Un Skill peut être livré avec des références qui affirment qu'une empreinte, une taille, une date ou un nombre de fichiers est « courant ». Ces valeurs sont datées : elles peuvent expirer sans qu'aucun test ne le signale. `skill-file-qa` ne compare que les empreintes de `SKILL.md` ; il ne vérifie pas les affirmations de ses références.

Ce Skill est une porte de livraison. Il inventorie les affirmations de l'archive, les recalcule sur disque, ajoute une observation datée sans réécrire l'historique, synchronise la section « cas vérifié » du `SKILL.md`, puis hashe séparément et relance la QA.

Il ne remplace pas :

- `verifier-reecriture-concurrente-paquet-skill` : certification d'une dérive de paquet après QA, reconstruction JSONL, diff et re-test ; l'utiliser si le paquet a déjà dérivé et qu'il faut prouver l'ancienne version.
- `write-skill-evidence-case-study` : rédaction et versionnement de l'archive de preuve ; ce Skill ne fait qu'ajouter une observation datée et synchroniser le cas.
- `skill-update-concurrency-safe` : sauvegarde, écriture minimale et double échantillonnage avant modification.
- `audit-skill-during-live-creation` : écrivain encore actif, zéro écriture et attente du froid.
- `adopt-concurrent-duplicate-skill` : décision de reprise, de portée réduite ou de conservation en lecture seule.
- `skill-package-integrity-audit` : caches, manifeste `Files (N)` et archives obsolètes.
- `extraire-preuves-session-qoder` : fraîcheur d'un snapshot de session ; objet différent.
- `skill-file-qa` : validation statique ; sa porte d'empreinte ne couvre que `SKILL.md`.

## Quand utiliser

- Avant un commit, une publication ou une remise de Skill qui contient une archive de preuve.
- L'archive a été écrite plus tôt et le paquet audité a pu changer depuis.
- La QA est `PASS`, mais une référence dit encore « courant », « inchangé », `FINAL` ou « N fichiers ».
- Une session a proposé une mise à jour de l'archive sans l'exécuter.
- Un fichier est apparu, `Files (N)` a changé ou le grade `FINAL` doit être réexaminé.
- 中文触发：Skill 证据新鲜度、引用哈希过期、当前值复核、§N 追加、快照时点同步、PROVISIONAL、交付前门禁、QA 只覆盖 SKILL.md、历史不改写。

## Quand ne pas utiliser

- Le paquet est encore écrit par une autre session : appliquer d'abord `audit-skill-during-live-creation`.
- Il faut décider si un Skill concurrent doit être repris : appliquer d'abord `adopt-concurrent-duplicate-skill`.
- Il faut reconstruire une version antérieure, qualifier un diff ou rejouer un test tiers : appliquer `verifier-reecriture-concurrente-paquet-skill`.
- Il faut seulement vérifier les caches et les archives publiées : appliquer `skill-package-integrity-audit`.

## Contrat non négociable

1. **Une affirmation n'est pas un fait.** « Courant », « inchangé », `FINAL`, « N fichiers » et toute empreinte présentée comme actuelle sont des hypothèses à recalculer.
2. **Le disque décide.** Recalculer `size`, `mtime_ns` et SHA-256. Sans baseline, écrire `INDETERMINE` ou « inconnu », jamais « inchangé ».
3. **L'historique est append-only.** Ne pas réécrire une section § ancienne. Ajouter `## N. Constat postérieur (date)` et conserver les valeurs et phrases d'origine. Une affirmation fausse se corrige par une nouvelle observation qui cite l'ancienne et la contre-preuve.
4. **Synchronisation minimale du `SKILL.md`.** Dans la section « cas vérifié », remplacer « courant » par « à la date de l'archive », ajouter un pointeur vers §N et la règle de revérification. Ne pas modifier les étapes opérationnelles tant qu'elles ne sont pas contredites.
5. **Deux axes de grade.** `FINAL` qualifie une mesure reproductible à son horodatage après échantillons stables. `PROVISIONAL` signifie que la valeur ne peut pas être présentée comme actuelle : écrivain actif, auteur inconnu, paquet encore modifié ou baseline absente. Une mesure `FINAL` expire quand même.
6. **Aucune attribution sans preuve.** Écrire « auteur non identifié » tant qu'aucun Write/Edit ne relie l'écriture à une session. Ne pas déduire l'auteur d'un mtime.
7. **Hashes séparés.** La QA ne couvre que `SKILL.md` ; après écriture, hasher séparément `SKILL.md` et chaque référence ou script, avec taille et `mtime_ns`.
8. **Lecture seule sur le paquet audité.** Ne pas y écrire, ne pas exécuter ses scripts, ne pas laisser de cache. Toute écriture dans le paquet livré exige une autorisation explicite et une sauvegarde hors paquet.

## Étape 0 — Inventaire daté des affirmations

1. Lire le `SKILL.md` livré et toutes ses références. Relever pour chaque affirmation : fichier cible, ligne, valeur annoncée (taille, hash, mtime, nombre de fichiers, grade) et formulation exacte.
2. Séparer les affirmations d'état (à recalculer) des règles et leçons (à conserver). Une phrase comme « quatre fichiers n'ont pas changé » est une affirmation d'état, même si elle est vraie dans une fenêtre d'échantillonnage.
3. Relever l'heure d'écriture de l'archive et sa fenêtre d'échantillonnage. Une stabilité de 2 s ne prouve que ces 2 s.
4. Prendre un instantané hors des paquets, par exemple sous `.qoder/tmp/<projet>/fraicheur-<horodatage>/`. Ne pas écrire dans le paquet audité ni dans le Skill livré avant l'étape 2.
5. Vérifier aussi `Files (N)` et la liste réelle : fichiers suivis, non suivis, `.git`, `__pycache__`, `*.pyc`.

## Étape 1 — Recalculer et classer

Calculer les empreintes sur disque, sans modifier les fichiers :

```bash
target="C:/Users/<user>/.qoder/skills/<skill>"
py -3 - "$target" <<'PY'
import hashlib, sys
from pathlib import Path

target = Path(sys.argv[1])
for path in sorted(target.rglob("*")):
    rel = path.relative_to(target).as_posix()
    if not path.is_file() or rel.startswith(".git/") or "__pycache__" in rel or rel.endswith(".pyc"):
        continue
    data = path.read_bytes()
    print(f"{rel}|{len(data)}|{path.stat().st_mtime_ns}|{hashlib.sha256(data).hexdigest()}")
PY
```

Comparer chaque affirmation à la mesure :

| Classement | Condition |
|---|---|
| `CONFIRME` | taille et SHA-256 égaux à la valeur annoncée, à l'horodatage de la mesure |
| `REECRIT-IDENTIQUE` | SHA-256 égal, `mtime_ns` différent |
| `PERIME` | taille ou SHA-256 différent |
| `ABSENT` | fichier annoncé introuvable |
| `INDETERMINE` | baseline absente, valeur non mesurable ou affirmation trop vague |

Pour `N fichiers`, compter les fichiers de contenu en excluant `.git`, `__pycache__` et `*.pyc`, puis distinguer suivis et non suivis. Un ajout de fichier est `AJOUTE`, pas `MODIFIE` ; ne pas confondre les deux dans le rapport.

Ne pas conclure « inchangé » à partir d'une courte fenêtre. Écrire la fenêtre exacte et la date de la mesure.

## Étape 2 — Ajouter une observation datée §N

1. Si une valeur est `PERIME`, `ABSENT` ou `INDETERMINE`, ou si l'archive est réutilisée pour une livraison, ajouter une nouvelle section à la fin de la référence :

```markdown
## N. Constat postérieur (AAAA-MM-JJ, après rédaction)

- Mesure : AAAA-MM-JJ HH:MM:SS +fuseau, commande ou outil.
- `chemin` : annoncé <taille / hash / mtime> ; mesuré <taille / hash / mtime> ; verdict <...>.
- Grade : FINAL pour la mesure à cet horodatage ; PROVISIONAL comme valeur « courante ».
- Auteur : non identifié / identifié par <preuve Write/Edit>.
- Limites : <fenêtre d'échantillonnage, fichier non suivi, session active, autre>.
```

2. Conserver les sections précédentes intactes. Si une ancienne phrase était vraie seulement dans une fenêtre, le dire dans §N au lieu de la réécrire.
3. Si tout est `CONFIRME`, une courte §N « aucune dérive observée » avec la méthode, la fenêtre et l'horodatage suffit. Elle date la vérification pour le prochain lecteur.
4. Si le paquet audité change encore ou si l'auteur n'est pas prouvé, écrire `PROVISIONAL` et ne pas écrire `FINAL` global. Attendre le froid ou rendre la limite explicite.

## Étape 3 — Synchroniser la section « cas vérifié » du SKILL.md

1. Remplacer les mentions « courant » ou « actuel » par « à la date de l'archive (AAAA-MM-JJ HH:MM +fuseau) ».
2. Ajouter un pointeur vers la nouvelle observation, par exemple « voir §N de l'archive ».
3. Ajouter ou renforcer la règle : toute empreinte, taille ou date citée dans une référence n'est valable qu'à son horodatage et doit être revérifiée avant réutilisation.
4. Ne pas changer les étapes, les contrats ou les seuils du Skill si la mesure ne les contredit pas. Une correction documentaire ne doit pas réécrire l'histoire de l'incident.
5. Si la section dit « 4 fichiers » et que l'archive en documente 5, pointer vers §N et laisser l'archive décrire l'ajout ; ne pas modifier silencieusement le nombre dans l'ancienne section.

## Étape 4 — Hashes séparés, double échantillon et QA

1. Après écriture, relever séparément `size`, `mtime_ns` et SHA-256 de `SKILL.md` et de chaque référence ou script.
2. Échantillonner deux fois à au moins 2 s d'intervalle. Si les empreintes changent, relire et s'arrêter si le fichier reste instable.
3. Lancer la QA statique :

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "<skill-dir>" --workspace "<workspace>" --stable-seconds 2 --stability-timeout 30
```

4. Exiger `RESULT PASS` et un code 0. Rappeler que la QA ne couvre que `SKILL.md` : elle ne prouve pas la fraîcheur des références.
5. Vérifier les références locales et les noms de Skills cités ; supprimer uniquement les caches créés par cette session. Ne pas supprimer les fichiers d'une autre session.
6. Consigner dans le rapport : affirmations, mesures, verdicts, §N ajoutée, section synchronisée, hashes séparés, QA et limites.

## Diagnostic

| Symptôme | Cause probable | Action |
|---|---|---|
| QA `PASS` mais une référence est fausse | l'empreinte ne couvre que `SKILL.md` | appliquer ce Skill et hasher séparément |
| « Inchangé » après une fenêtre de 2 s | la fenêtre n'est pas l'état final | ajouter §N avec la fenêtre et la nouvelle mesure |
| Un fichier apparaît après l'archive | `Files (N)` est un inventaire daté | compter, classer `AJOUTE`, ajouter §N |
| Une valeur diffère de l'archive | dérive ou mesure erronée | classer `PERIME`, conserver l'ancienne valeur, mesurer deux fois |
| Auteur inconnu | aucune preuve Write/Edit | écrire « non identifié », ne pas deviner |
| Paquet encore modifié | écrivain actif | zéro écriture sur le paquet audité, `PROVISIONAL` |
| Aucun hash ni aucune taille annoncés | affirmation non mesurable | `INDETERMINE`, demander une baseline |
| SHA-256 égal mais mtime différent | réécriture identique | `REECRIT-IDENTIQUE`, pas de rollback |
| La référence dit « 4 fichiers » et le disque en a 5 | phrase liée à une fenêtre | §N et pointeur, pas de réécriture silencieuse |
| QA relancée mais références non hashées | portée de la QA mal comprise | hashes séparés avant de conclure |

## Cas vérifié (2026-10-26)

L'archive de `verifier-reecriture-concurrente-paquet-skill` a été écrite à 14:00:17+01:00. Sa §13 affirmait que les quatre fichiers documentés n'avaient pas changé, sur la foi d'échantillons pris entre 13:59:59 et 14:00:04. La session source a mesuré à 14:02:47+01:00 :

| Fichier | Archive | Mesure à 14:02:47 | Verdict |
|---|---|---|---|
| `SKILL.md` du paquet audité | 15 154 B / `6d755440…` / 13:29:08 | 16 025 B / `79862dc9…` / 14:02:32 | `PERIME` |
| references/protocole-restauration.md | 15 676 B / `1de3f4ed…` / 13:36:15 | 18 767 B / `d88e1fb2…` / 14:00:56 | `PERIME` |
| scripts/tester_instantane.py | 24 235 B / `6184122e…` / 13:58:50 | identique | `CONFIRME` |
| references/cas-entite-2026-10-26.md | 9 792 B / `bf4a778a…` / 13:29:35 | identique | `CONFIRME` |
| scripts/instantane_effets_de_bord.py | 29 761 B / `a5007118…` / 13:35:36 | identique | `CONFIRME` |

À 15:25:42+01:00, une seconde mesure indépendante a trouvé les cinq fichiers de contenu différents de l'archive et un `git status` avec quatre fichiers suivis modifiés et un fichier non suivi. La valeur « quatre fichiers inchangés » n'était donc vraie que dans la fenêtre d'échantillonnage ; les nouvelles valeurs sont `PROVISIONAL` comme valeurs « courantes » et l'auteur reste non identifié.

La session source avait proposé une mise à jour minimale (section « cas vérifié », introduction de l'archive, §13 et §14) mais ne l'a pas exécutée. Le paquet livré est resté avec `SKILL.md` à `f6fb7518…` et l'archive à `f3b21836…` ; une QA relancée ici donne `PASS` 9/0/0, `Files (2)`, ce qui confirme que la QA ne détecte pas l'archive périmée. Le détail, les hashes complets, les commandes et les limites sont dans `references/cas-fraicheur-2026-10-26.md`.

## Checklist de fin

- [ ] Toutes les affirmations « courant / inchangé / N fichiers / FINAL » sont listées avec fichier et ligne.
- [ ] `size`, `mtime_ns` et SHA-256 recalculés ; chaque affirmation classée.
- [ ] Baseline absente traitée comme `INDETERMINE`, jamais comme « inchangé ».
- [ ] §N ajoutée sans réécrire les sections précédentes.
- [ ] Section « cas vérifié » datée, pointée vers §N, règle de revérification ajoutée.
- [ ] Auteur non deviné ; « non identifié » si aucune preuve Write/Edit.
- [ ] `PROVISIONAL` tant que le paquet peut changer ; `FINAL` seulement pour une mesure datée et stable.
- [ ] Hashes séparés pour `SKILL.md` et chaque référence ou script.
- [ ] Double échantillon à 2 s ; aucun cache laissé dans le paquet livré.
- [ ] `skill-file-qa` `PASS` / code 0 ; portée limitée à `SKILL.md` rappelée.
- [ ] Rapport daté avec verdicts, grades et limites.

## Ressources

- `references/cas-fraicheur-2026-10-26.md` : chronologie, affirmations, mesures 14:02 et 15:25, verdicts, commandes et limites.
- `verifier-reecriture-concurrente-paquet-skill` : dérive de paquet après QA, reconstruction JSONL, diff et re-test.
- `write-skill-evidence-case-study` : rédaction, datation et versionnement de l'archive.
- `skill-update-concurrency-safe` : double échantillonnage, sauvegarde et écriture minimale.
- `audit-skill-during-live-creation` : écrivain actif, zéro écriture, attente du froid.
- `adopt-concurrent-duplicate-skill` : reprise et décision de portée.
- `skill-package-integrity-audit` : caches, `Files (N)` et archives obsolètes.
- `extraire-preuves-session-qoder` : fraîcheur d'un snapshot de session.
- `skill-file-qa` : validation statique et empreinte limitée à `SKILL.md`.
