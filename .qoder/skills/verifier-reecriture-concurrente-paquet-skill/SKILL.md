---
name: verifier-reecriture-concurrente-paquet-skill
description: "Après un RESULT PASS de skill-file-qa, certifier a posteriori un paquet Skill : empreintes size/mtime_ns/SHA-256 de tous les fichiers avant et après, détection de réécriture concurrente, reconstruction des versions antérieures depuis le JSONL jusqu'à égalité SHA-256 exacte, diff et attribution (correctif légitime conservé, régression signalée), audit de la version exacte du test tiers qui a échoué, re-test indépendant hors paquet, puis QA finale après quiescence et rapport daté FINAL/PROVISIONAL. Utiliser quand la QA est verte mais qu'un fichier a changé après, quand un test tiers échoue alors que le harnais a été modifié, ou quand il faut prouver quel contenu était livré avant une réécriture. 中文触发：QA 绿灯后漂移、Skill 包并发重写、全包指纹、JSONL 重放到哈希相等、diff 定性、合法修复保留、第三方测试版本审计、假测试、独立复测、日期化清单、FINAL/PROVISIONAL。"
---

# Vérifier une réécriture concurrente d'un paquet Skill

## Objectif et limites

Un `RESULT PASS` de `skill-file-qa` ne gèle pas le paquet : le validateur compare les empreintes de `SKILL.md` seulement, et `Files (N)` n'est qu'un inventaire. Ce Skill couvre l'après-QA : constater qu'un autre fichier a été réécrit, reconstruire la version antérieure depuis le JSONL, qualifier le delta, auditer le test qui a échoué, puis re-certifier le paquet après quiescence.

Il ne remplace pas :

- `audit-skill-during-live-creation` : écrivain encore actif, zéro écriture, attente du froid ;
- `skill-update-concurrency-safe` : sauvegarde, écriture minimale, fusion des ajouts concurrents ;
- `skill-package-integrity-audit` : caches, manifeste `Files (N)`, archives obsolètes ;
- `reconstruire-pilote-supprime-depuis-jsonl` : rejeu Write/Edit ; ce Skill réutilise son script et ajoute la porte d'égalité SHA-256 ;
- `replay-skill-reference-fixtures` : rejeu d'une fixture documentée ;
- `audit-session-evidence` et `extraire-preuves-session-qoder` : inventaire brut et attribution d'intention ;
- `write-skill-evidence-case-study` : rédaction et versionnement de l'archive de preuve.

## Déclencheurs

- la QA est `PASS`, mais un fichier autre que `SKILL.md` a un mtime ou un SHA-256 postérieur ;
- un test tiers échoue, puis son harnais est modifié avant qu'on ait conclu ;
- il faut prouver quel contenu était livré avant une réécriture ;
- un diff montre un delta inconnu dans une référence ou un script ;
- le rapport doit distinguer FINAL et PROVISIONAL fichier par fichier.

## Contrat non négociable

1. **La QA verte ne gèle rien.** Le validateur appelle `finish_fingerprint(skill_md, ...)` : seules les empreintes de `SKILL.md` sont comparées avant et après. Un `PASS` ne prouve rien sur les références ni sur les scripts.
2. **Baseline complète.** Enregistrer pour chaque fichier le chemin relatif, `size`, `mtime_ns` et SHA-256. Exclure `.git`, `__pycache__` et `*.pyc` du contenu, mais les compter à part. Sans baseline antérieure, l'état d'avant est **inconnu**, pas « inchangé ».
3. **Écrivain actif = zéro écriture.** Si la session écrit encore, ne pas modifier le paquet ; passer à `audit-skill-during-live-creation` et attendre le froid.
4. **Égalité stricte.** Une version antérieure n'est « reconstruite » que si le SHA-256 du dump égale la baseline. Le script de rejeu n'a pas de coupure temporelle : il rejoue la chaîne finale de la session. Un écart donne « inconnu », jamais « probablement ».
5. **Diff avant attribution.** Classer chaque hunk en correctif légitime ou régression. Un correctif concurrent légitime se conserve ; on ne rétablit pas l'ancienne version sans autorisation explicite et sauvegarde hors paquet.
6. **Un test qui échoue n'est pas une preuve.** Auditer la version exacte du test qui a produit l'échec (taille, mtime, SHA-256, reconstruction JSONL si nécessaire). Si le harnais a changé, le verdict est périmé. Ne jamais modifier l'attendu pour faire passer.
7. **Re-test hors paquet.** Copier le paquet ou construire une fixture hors du paquet ; ne pas modifier le paquet ; ne pas laisser de cache ; vérifier que la cible n'a pas changé (hash avant/après).
8. **Quiescence et grades.** Trois échantillons complets identiques, espacés d'au moins 2 s, avant la QA finale. Chaque constat est FINAL ou PROVISIONAL ; un seul PROVISIONAL interdit le FINAL global.
9. **Lecture seule par défaut.** Ne jamais exécuter un fichier reconstruit. Toute écriture dans le paquet exige une autorisation explicite et une sauvegarde hors paquet.

## Étape 0 — Geler et établir la baseline complète

1. Vérifier que le paquet existe et relever la liste réelle des fichiers. Noter aussi la présence de `.git`, des caches et des fichiers non suivis.
2. Prendre un instantané complet hors du paquet, par exemple sous `.qoder/tmp/<projet>/skill-drift-<horodatage>/` :

```bash
target="C:/Users/<user>/.qoder/skills/<skill>"
out=".qoder/tmp/<projet>/skill-drift-$(date +%Y%m%dT%H%M%S)"
mkdir -p "$out"
py -3 - "$target" "$out/baseline.json" <<'PY'
import hashlib, json, sys
from pathlib import Path

target, out = Path(sys.argv[1]), Path(sys.argv[2])
rows = []
for path in sorted(target.rglob("*")):
    if not path.is_file():
        continue
    rel = path.relative_to(target).as_posix()
    if rel.startswith(".git/") or "__pycache__" in rel or rel.endswith(".pyc"):
        continue
    stat = path.stat()
    rows.append({
        "path": rel,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    })
out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(f"BASELINE files={len(rows)} -> {out}")
PY
```

3. Échantillonner deux fois à au moins 2 s d'intervalle. Si les empreintes changent, arrêter et passer au Skill de création en direct.
4. Chercher une baseline antérieure à la QA. Si elle existe, elle seule permet de parler de dérive. Sinon, marquer l'état d'avant comme inconnu et conserver la baseline actuelle pour la suite.

## Étape 1 — Détecter la dérive et qualifier l'activité

Comparer la baseline et l'instantané post-QA fichier par fichier :

| Observation | Qualification |
|---|---|
| même SHA-256, même taille | `UNCHANGED` |
| même SHA-256, mtime différent | `REECRIT-IDENTIQUE` : pas de dérive de contenu |
| SHA-256 différent | `MODIFIE` |
| présent avant, absent après | `SUPPRIME` |
| absent avant, présent après | `AJOUTE` |

- Un `REECRIT-IDENTIQUE` se signale mais ne justifie pas un rollback.
- Si les changements continuent, vérifier l'activité de l'écrivain. Tant qu'il est actif, ne rien écrire.
- Si le paquet est stable, passer à la reconstruction. La stabilité ne prouve pas l'identité de l'auteur.

## Étape 2 — Reconstruire la version antérieure depuis le JSONL

1. Localiser le JSONL de la session qui a écrit la baseline, sous `.qoder/projects/<projet>/<sessionId>.jsonl`. Relever taille, nombre de lignes, mtime et SHA-256 avant et après lecture.
2. Vérifier le contrat du script de rejeu de `reconstruire-pilote-supprime-depuis-jsonl` : chemins exacts, options `--expect-*`, `--dump`, codes 0/1/2.
3. Rejouer vers un répertoire temporaire, jamais vers le paquet :

```bash
py -3 "<dossier-du-skill-de-reconstruction>/scripts/rejouer_pilote_jsonl.py" \
  --jsonl "<session>.jsonl" \
  --file "<chemin-absolu-du-fichier>" \
  --expect-writes <n> --expect-edits <n> \
  --dump "<tmp>/version-anterieure.py"
```

4. Comparer le SHA-256 du dump à la baseline. **Égalité exacte = seule preuve.** Sinon, diagnostiquer :
   - la session contient des éditions postérieures à la baseline et le script n'a pas de coupure ;
   - mauvaise session ou plusieurs chemins pour le même basename ;
   - événements en sidechain ignorés ;
   - outil non supporté, `EDIT MISS` ou `EDIT AMBIGUOUS` ;
   - différence de fin de ligne.
5. Si un cas empêche la reconstruction, écrire « version antérieure inconnue ». Ne pas exécuter le dump.

## Étape 3 — Diffuser et attribuer

- Comparer le dump à la version courante avec un diff unifié.
- Classer chaque hunk : correctif légitime (alias, schéma réel, correction documentaire) ou régression (règle supprimée, seuil affaibli, garde retirée, référence cassée).
- Un correctif légitime se conserve. Si la documentation du paquet doit refléter le nouveau comportement, la mettre à jour après vérification, sans annuler le correctif.
- Une régression se signale avec ses lignes. Ne la corriger qu'avec autorisation explicite, après sauvegarde, puis relancer QA et tests.
- Enregistrer les hunks, les lignes et la décision. Ne pas résumer par « changement mineur ».

## Étape 4 — Auditer la version exacte du test tiers

1. Identifier le harnais qui a produit le résultat : taille, mtime, SHA-256, fichier de sortie et horodatage.
2. Si le harnais a été modifié après l'échec, le verdict est périmé. Auditer la version qui a réellement échoué, pas la version courante.
3. Si cette version a été écrasée, la reconstruire depuis le JSONL de son auteur et vérifier sa logique. Sans reconstruction ni empreinte indépendante, marquer le verdict `PROVISIONAL` ou `INVALID`.
4. Distinguer bug du test et bug du produit. Un test qui compare une version à un instantané pris sur une version antérieure est faux, même s'il échoue de façon reproductible.
5. Ne pas ajuster l'attendu pour obtenir un `PASS`. Corriger le test dans une copie isolée, enregistrer l'ancien et le nouveau hash, puis rejouer.

## Étape 5 — Re-tester hors paquet

- Copier le paquet dans `.qoder/tmp/...` ou construire une fixture qui n'écrit que dans le temporaire.
- Lancer les tests avec `py -3 -B` quand c'est possible, pour éviter les caches.
- Assertions minimales :
  - le hash de la cible avant et après le test est identique ;
  - les cas positifs et négatifs sont exécutés ;
  - les codes de sortie 0/1/2 sont distingués ;
  - aucun `__pycache__` ni `.pyc` n'apparaît dans le paquet.
- Si le test écrit dans le paquet, arrêter et isoler avant de conclure.

## Étape 6 — QA finale et rapport daté

1. Attendre trois échantillons complets identiques, espacés d'au moins 2 s. Si un écrivain est encore actif, ne pas lancer la QA finale.
2. Relancer `skill-file-qa` sur le paquet final. Exiger `RESULT PASS` et un code 0, puis rappeler que la stabilité ne couvre que `SKILL.md`.
3. Relancer le harnais indépendant sur la copie finale.
4. Enregistrer séparément les empreintes de `SKILL.md` et de chaque référence ou script. Un `PASS` de la QA ne les couvre pas.
5. Produire un rapport daté avec le manifeste N fichiers, la baseline, la version courante, la reconstruction, le diff, les versions de test, le re-test et les grades.
6. Si un seul élément reste `PROVISIONAL`, le rapport global ne porte pas `FINAL`.

## Diagnostic

| Symptôme | Cause probable | Action |
|---|---|---|
| QA `PASS` mais un script ou une référence a changé | empreinte limitée à `SKILL.md` | baseline complète et constat explicite |
| Le dump n'a pas le hash de la baseline | éditions postérieures dans la même session, sans coupure | choisir la session qui s'arrête à la baseline, sinon « inconnu » |
| `EDIT MISS` ou `EDIT AMBIGUOUS` | l'historique ne rejoue pas exactement | arrêter, ne pas deviner |
| Le harnais a changé depuis l'échec | verdict périmé | auditer la version exacte et rejouer |
| Le test passe mais la cible a changé | test non isolé | invalider le test, isoler |
| `.git` ou un cache entre dans l'empreinte | faux positif de dérive | exclure et compter à part |
| mtime change, hash identique | réécriture identique | pas de rollback |
| Le paquet change encore | écrivain actif | zéro écriture, attendre |
| Aucune baseline avant la QA | état antérieur non observé | écrire « inconnu » |
| Le rapport ne peut pas nommer l'auteur | aucune preuve d'écriture | écrire « auteur non identifié » |

## Modèle de rapport

```text
Mode: POST-QA / ADOPTED
Paquet: <chemin absolu>
Date: <AAAA-MM-JJ HH:MM:SS +fuseau>
Sessions: <IDs examinés ; auteur du drift: identifié | non identifié>
Baseline: <horodatage> ; <N> fichiers ; <empreintes>
Courant: <horodatage> ; <N> fichiers ; <empreintes>
Dérive: <fichier: baseline -> courant ; UNCHANGED | REECRIT-IDENTIQUE | MODIFIE | AJOUTE | SUPPRIME>
Reconstruction: <JSONL taille/lignes/hash ; Write/Edit ; hash du dump ; égalité oui/non>
Diff: <hunks, lignes, correctif conservé ou régression signalée>
Tests: <version ancienne hash -> résultat ; version courante hash -> résultat>
Re-test: <hors paquet ; N/N ; cible inchangée ; aucun cache>
QA finale: <PASS/FAIL ; portée SKILL.md seulement>
Grades: <élément -> FINAL | PROVISIONAL>
Limites: <pas de baseline, pas de coupure, auteur inconnu, outil non supporté>
```

## Cas vérifié (2026-10-26)

Le paquet `verifier-effets-de-bord-verification-lecture-seule` avait 4 fichiers. La QA était `PASS` 9/0/0, mais deux fichiers ont changé après. Les preuves complètes sont dans `references/cas-reecriture-2026-10-26.md`.

1. `SKILL.md` : 15 154 B (`6d755440…`, 13:29:08+01:00), inchangé pendant l'incident.
2. Baseline : script 29 725 B (`be2b86b4…`) et protocole 15 240 B (`fc2618d6…`).
3. Dérive : script 29 761 B (`a5007118…`, 13:35:36) et protocole 15 676 B (`1de3f4ed…`, 13:36:15).
4. Rejeu du JSONL (2 494 566 B, 765 lignes, `aa21d323…`) : 1 Write + 4 Edit -> `be2b86b4…` ; 1 Write + 1 Edit -> `fc2618d6…` ; égalité exacte.
5. Diff : alias `horodatage_iso` et `chemin_fichier`, plus une ligne de piège ; correctif légitime conservé.
6. Ancien harnais tiers 12 159 B (`2fb80d0b…`, snap2) -> 35/37 ; harnais courant 12 374 B (`73ff7c5c…`, snap3) -> 38/38 ; ancien verdict périmé.
7. Harnais indépendant : 22/22, cible inchangée, aucun cache.
8. QA finale : `PASS` 9/0/0 ; seules les empreintes de `SKILL.md` sont comparées, les références et scripts sont hashés séparément.
9. Auteur du drift non identifié parmi les sessions examinées ; aucun Write/Edit du paquet dans ad2dd331 ou 7f7ab757 après 12:19Z. Le cas ne l'attribue pas.

## Checklist de fin

- [ ] Baseline complète hors paquet, avec size, `mtime_ns` et SHA-256.
- [ ] `.git`, caches et fichiers non suivis traités séparément.
- [ ] Dérive qualifiée fichier par fichier, `REECRIT-IDENTIQUE` distingué de `MODIFIE`.
- [ ] Version antérieure reconstruite seulement après égalité SHA-256 exacte.
- [ ] Diff classé et correctif légitime conservé.
- [ ] Version exacte du test en échec auditée ; ancien verdict invalidé si le harnais a changé.
- [ ] Re-test hors paquet, cible inchangée, aucun cache.
- [ ] Trois échantillons stables avant la QA finale.
- [ ] `SKILL.md` et références hashés séparément.
- [ ] Rapport daté avec grades FINAL/PROVISIONAL et limites.
- [ ] Auteur non prouvé laissé « non identifié ».

## Ressources

- `references/cas-reecriture-2026-10-26.md` : timeline, empreintes complètes, diff, versions de test et limites.
- `reconstruire-pilote-supprime-depuis-jsonl` : script de rejeu Write/Edit, réutilisé sans duplication.
- `audit-skill-during-live-creation` : activité de l'écrivain et attente du froid.
- `skill-update-concurrency-safe` : sauvegarde et écriture minimale.
- `skill-package-integrity-audit` : caches, manifeste et archives.
- `replay-skill-reference-fixtures` : rejeu d'une fixture documentée.
- `audit-session-evidence` et `extraire-preuves-session-qoder` : preuves de session.
- `write-skill-evidence-case-study` : rédaction et versionnement de l'archive.
