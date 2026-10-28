---
name: prouver-baseline-avant-diff
description: "Reconstruire une version antérieure qui n'existe plus sur disque avant d'en publier un diff : chercher d'abord une source réelle d'octets (objet Git, sauvegarde, rejeu JSONL), sinon inverser les éditions connues sur la version courante en exigeant exactement 1 occurrence par remplacement (0 ou plusieurs → arrêt sans deviner), écrire le résultat hors du dossier cible, n'accepter le diff que si taille, lignes et SHA-256 égalent les valeurs enregistrées, puis produire un diff -u étiqueté et compter lignes remplacées, totales et inchangées avant de supprimer le temporaire. Utiliser quand on demande « le diff avec <hash> » alors que ce hash n'est plus sur disque, quand un fichier a été réécrit après une empreinte connue, ou quand un diff doit être prouvé plutôt que récité de mémoire. 中文触发：重建已不存在的旧版本、按哈希证明逐字节一致、输出逐行 diff、拒绝凭记忆重述差异、统计改动行。"
---

# Prouver la baseline avant de publier un diff

## Objectif et limites

Produire un diff dont les deux côtés sont des octets réels : la version courante lue sur disque, et une version antérieure reconstruite puis prouvée par SHA-256. Ce Skill ne sert que lorsque l'ancienne version n'est plus accessible directement.

Il ne remplace pas :

- `verifier-reecriture-concurrente-paquet-skill` : dérive post-QA et rejeu JSONL complet d'un paquet ;
- `reconstruire-pilote-supprime-depuis-jsonl` : rejeu Write/Edit depuis le JSONL ;
- `verifier-comptage-diff-fixture-dense` : sémantique des hunks et des compteurs de diff ;
- `verifier-mutation-fixture-appliquee` : fixture de mutation et échec attendu ;
- `confirmer-plan-avant-ecriture` : granularité de l'approbation et ré-échantillonnage après attente ;
- `skill-file-qa` : empreinte de `SKILL.md` seulement.

## Quand l'utiliser

- « Donne-moi le diff avec `<hash>` » alors que ce hash n'est plus sur disque.
- Un fichier a été réécrit après une empreinte connue et l'ancien contenu n'a pas été sauvegardé.
- Un diff doit être prouvé, pas reconstitué de mémoire.
- Il faut distinguer une substitution de lignes d'une insertion ou d'une suppression.

## Quand ne pas l'utiliser

- La version est dans Git : `git show <oid>:<chemin>` puis vérifier le SHA-256 ; ne pas reconstruire.
- Une sauvegarde ou un instantané contient les octets : les utiliser tels quels.
- Le JSONL permet un rejeu complet : passer par `reconstruire-pilote-supprime-depuis-jsonl`.
- On veut modifier, restaurer ou annuler : ce Skill est en lecture seule sur la cible ; une restauration est une écriture séparée, soumise à accord explicite.

## Contrat non négociable

1. **Source réelle d'abord.** Objet Git, sauvegarde, instantané, rejeu JSONL. L'inversion d'éditions est le dernier recours.
2. **Aucune recollection.** Un diff ne s'écrit jamais de mémoire : les deux côtés doivent être des fichiers dont le SHA-256 est connu.
3. **Une occurrence exactement.** Chaque `new` doit apparaître une fois. Zéro ou plusieurs occurrences → arrêt, aucun output, aucun diff.
4. **Le hash est la seule preuve.** `size` et lignes corroborent ; un préfixe de hash n'est pas une preuve. Le script exige 64 caractères hexadécimaux.
5. **Lecture seule sur la cible.** Toute écriture va sous `.qoder/tmp`, hors du dossier cible. Le script refuse un `--out` dans ce dossier. Nettoyer et prouver l'absence.
6. **Code retour du diff.** 0 = identique, 1 = différences attendues, plus de 1 = erreur. Ne jamais passer `diff` dans un pipe qui avale le code retour.
7. **Ne pas surinterpréter les compteurs.** `MODE=INSERT_DELETE` interdit de parler de « N lignes changées ». La sémantique des hunks appartient à `verifier-comptage-diff-fixture-dense`.
8. **Restauration = écriture séparée.** Revenir à l'ancienne version exige une demande explicite, une sauvegarde et une nouvelle preuve. Un `RESULT PASS` de `skill-file-qa` ne couvre que `SKILL.md`.

## Étape 0 — Geler la version courante

Prélever deux fois, à au moins 2 s d'intervalle, `size`, `mtime_ns`, SHA-256 et nombre de lignes. Si une valeur change, arrêter : un écrivain est actif, voir `audit-skill-during-live-creation`.

```bash
target="<fichier absolu>"
py -3 - "$target" <<'PY'
import hashlib, sys
from pathlib import Path

path = Path(sys.argv[1])
raw = path.read_bytes()
stat = path.stat()
print("SIZE {} MTIME_NS {} SHA256 {} LINES {}".format(
    stat.st_size, stat.st_mtime_ns, hashlib.sha256(raw).hexdigest(),
    len(raw.decode("utf-8").splitlines())))
PY
```

## Étape 1 — Inventorier les éditions

- Extraire les chaînes du JSONL de la session ou de ton propre journal d'éditions ; ne pas les retaper. Voir `extraire-preuves-session-qoder` pour localiser les `tool_use` `Edit` (`old_string` / `new_string`).
- Ne garder que les éditions appliquées **après** la version visée ; exclure celles déjà annulées et prouver l'exclusion par une recherche de la forme d'origine dans le fichier courant.
- Ordonner du plus récent au plus ancien : le script applique le tableau dans l'ordre fourni.

## Étape 2 — Écrire le spec d'éditions hors cible

Créer un JSON avec une seule couche de chaînes, via l'outil d'écriture de fichiers, jamais via un heredoc shell. `new` est le texte présent aujourd'hui ; `old` est le texte à rétablir.

```json
[
  {
    "id": "edit-17",
    "new": "ligne 17 (modifiée)",
    "old": "ligne 17"
  },
  {
    "id": "edit-3",
    "new": "ligne 3 (modifiée)",
    "old": "ligne 3"
  }
]
```

- `new` ne peut pas être vide. Pour inverser une insertion ou une suppression pure, remplacer la ligne englobante plutôt qu'utiliser une ancre vide.
- En CRLF, écrire `\r\n` dans les chaînes ; le script lit et écrit des octets UTF-8 sans conversion de fin de ligne.

## Étape 3 — Reconstruire et exiger l'égalité

```bash
tmp=".qoder/tmp/baseline-$(date +%Y%m%dT%H%M%S)"
mkdir -p "$tmp"
py -3 "<skill-dir>/scripts/reconstruire_baseline.py" \
  --current "<fichier-courant>" \
  --edits "$tmp/edits.json" \
  --out "$tmp/version-ancienne" \
  --expect-sha256 "<sha256-64-hex>" \
  --expect-size <octets> \
  --expect-lines <lignes>
```

Accepter uniquement si le code retour est 0 et si la sortie contient `BYTE-EXACT True` et `RESULT: PASS`.

- `EDIT <id> occurrences=0` : chaîne retapée, mauvaise version de départ ou édition déjà annulée. Ré-extraire, ne pas assouplir l'ancre.
- `EDIT <id> occurrences=2` : ancre trop courte. L'étendre à la ligne entière ou au contexte, jamais remplacer les deux.
- `CHECK sha256 FAIL` : mauvaises éditions, mauvais ordre ou mauvaise baseline. Le fichier `OUT` est conservé pour diagnostic ; ne pas produire de diff.
- Un `--out` existant est refusé par défaut : c'est une preuve périmée. L'inspecter ou le supprimer ; `--overwrite` seulement en connaissance de cause.

## Étape 4 — Produire le diff étiqueté

```bash
diff -u --label "a/<nom> @ <ancien-court>" --label "b/<nom> @ <courant-court>" \
  "$tmp/version-ancienne" "<fichier-courant>" > "$tmp/diff.patch"
rc=$?
```

- `rc=0` : fichiers identiques, aucun diff à publier.
- `rc=1` : différences, cas attendu.
- `rc>1` : erreur de `diff` (fichier absent, permission). Ne pas la présenter comme une différence.
- Ne pas utiliser `set -e` autour de cet appel et ne pas mettre `diff` dans un pipe avant d'avoir capturé `rc`.

## Étape 5 — Compter sans surinterpréter

```bash
py -3 "<skill-dir>/scripts/statistiques_diff.py" \
  --old "$tmp/version-ancienne" \
  --new "<fichier-courant>" \
  --diff "$tmp/diff.patch"
```

| Sortie | Interprétation |
|---|---|
| `MODE=SUBSTITUTION` + `CHANGED=N` | chaque hunk retire autant de lignes qu'il en ajoute ; « N lignes remplacées » est défendable |
| `MODE=INSERT_DELETE` | reporter `REMOVED` et `ADDED` séparément ; ne pas parler de lignes changées |
| `MODE=IDENTICAL` | aucun hunk, fichiers identiques |
| `RESULT: PASS` | le patch est cohérent avec les deux fichiers, pas que le changement est approuvé |

`UNCHANGED old=… new=…` est calculé par différence avec les totaux, pas par comptage des lignes de contexte. Deux éditions proches peuvent être fusionnées dans un seul hunk : ce n'est pas une erreur, seulement la fenêtre de contexte de `diff`.

## Étape 6 — Livrer et nettoyer

Le rapport doit contenir :

```text
Version ancienne: <sha256> <octets> o <lignes> lignes (reconstruite)
Version courante: <sha256> <octets> o <lignes> lignes
Diff: <HUNKS> hunk(s), REMOVED=<n> ADDED=<n>, MODE=<...>, CHANGED=<n|absent>
Preuve: <commande> -> rc=<0|1>, BYTE-EXACT True
Temporaire: supprimé, absence vérifiée
```

Puis supprimer le temporaire et prouver son absence :

```bash
rm -rf "$tmp"
test ! -e "$tmp" && echo "no temp left"
```

Ne jamais laisser la version reconstruite dans le dossier cible ni l'exécuter.

## Cas vérifié (2026-10-28)

Session `94884576-e776-4298-aa17-e34820e22af2`, tour `f1d57771-b0ac-4c55-a953-9e93eafbb2e7`.

- Ancienne version `14ff7f5c…4f6ad04a7` : 9 853 o, 176 lignes. Version courante `8a3e86c0…3570c09e` : 9 979 o, 176 lignes.
- Deux éditions inversées, chacune `occurrences=1` ; reconstruction `size=9853`, SHA-256 égal, `BYTE-EXACT True`, code 0.
- `diff -u` code 1 ; seules les lignes 27 et 169 diffèrent ; 2 hunks, `REMOVED=2 ADDED=2`, `MODE=SUBSTITUTION`, `CHANGED=2`, `UNCHANGED old=174 new=174`.
- Le script du paquet voisin était inchangé (`1180673b…`), et le temporaire a été supprimé (`no diff temp left`).
- Rejeu indépendant de ce paquet : reconstruction de `8a3e86c0` depuis `14ff7f5c` avec les deux paires de lignes du diff source, puis statistiques identiques. Détails et limites dans `references/cas-2026-10-28.md`.

## Diagnostic

| Symptôme | Cause probable | Action |
|---|---|---|
| `occurrences=0` | chaîne retapée, mauvaise version, édition déjà annulée | ré-extraire du JSONL, ne pas deviner |
| `occurrences=2` | ancre trop courte ou doublon réel | étendre au contexte, ne pas remplacer en masse |
| `CHECK sha256 FAIL` | mauvaises éditions, ordre inversé, mauvaise baseline | inspecter `OUT`, corriger les éditions, ne pas diffuser |
| `--expect-sha256 must be a full 64-hex` | préfixe court | obtenir le hash complet |
| `refusing to write inside the target directory` | `--out` dans le dossier cible | écrire sous `.qoder/tmp` |
| `output already exists` | preuve périmée d'une exécution précédente | inspecter ou supprimer ; `--overwrite` délibéré |
| `diff` code supérieur à 1 | fichier absent, permission | corriger l'entrée, pas le diff |
| `MODE=INSERT_DELETE` alors qu'on attendait « 2 lignes » | hunk déséquilibré | reporter `REMOVED`/`ADDED` séparément |
| patch vide mais fichiers différents | mauvais couple de fichiers | régénérer le diff |
| la cible change pendant le travail | écrivain concurrent | arrêter, ré-échantillonner, redemander |

## Checklist de fin

- [ ] Source réelle cherchée avant toute inversion (Git, sauvegarde, JSONL).
- [ ] Double prélèvement stable de la version courante.
- [ ] Éditions extraites, non retapées, dans l'ordre inverse.
- [ ] Chaque `new` a exactement 1 occurrence.
- [ ] `BYTE-EXACT True` et code retour 0 avant tout diff.
- [ ] `diff` exécuté sans pipe, code 0/1 distingué de plus de 1.
- [ ] `MODE` et `CHANGED` employés sans surinterprétation.
- [ ] Temporaire supprimé et absence prouvée.
- [ ] Aucune écriture dans le dossier cible.
- [ ] Cible modifiée après approbation → plan et demande refaits.

## Ressources

- `scripts/reconstruire_baseline.py` : inversion des éditions, assertion « exactement 1 », porte SHA-256/taille/lignes, codes 0/1/2.
- `scripts/statistiques_diff.py` : contrôle de cohérence des hunks, `REMOVED`/`ADDED`, `MODE`, `UNCHANGED`, codes 0/2.
- `references/cas-2026-10-28.md` : chronologie, empreintes, sorties verbatim, rejeu et limites de provenance.
- `verifier-reecriture-concurrente-paquet-skill` : reconstruction par rejeu JSONL et qualification d'une dérive post-QA.
- `reconstruire-pilote-supprime-depuis-jsonl` : script de rejeu Write/Edit.
- `verifier-comptage-diff-fixture-dense` : comptage des hunks et seuils de fusion.
- `confirmer-plan-avant-ecriture` : approbation au niveau des éditions, ré-échantillonnage après attente.
- `skill-file-qa` : validation du paquet et empreinte de `SKILL.md`.
