---
name: verifier-comptage-diff-fixture-dense
description: "在把 diff 计数写进 SKILL.md 前，先在密夹具上证明它是实测值：在安装目录外构造带合法 frontmatter 的源文件，至少两个改变块之间只隔 1 至 6 行未改行（不超过 diff 的上下文窗口），再加一个 old == new 的无效果替换，然后对照脚本计数器、`diff -u` 与 `diff -U0` 的 hunk 数，按实测语义归因差异（间距不超过 6 行即合并、连续改动算一个块），最后把文档改成与脚本契约一致的写法，绝不放宽阈值或修改夹具去凑数。用于 CHANGED 与 hunk 数不一致、diff -u 合并两个改动、计数单位不明、发布前声称实测、no-op 替换被计入 APPLY、稀疏夹具掩盖缺陷。Vérifier qu'un compteur de diff (plages, hunks, lignes, occurrences) annoncé dans un SKILL.md provient d'une fixture dense : deux blocs modifiés séparés de 1 à 6 lignes inchangées, plus une substitution sans effet, relevé du compteur du script, de `diff -u` et de `diff -U0`, correction de la doc vers la variante qui égale le contrat, jamais le seuil. English: diff hunk count, changed ranges, dense fixture, no-op substitution, -U0 versus -u, count claim, CHANGED mismatch."
---

# Vérifier un compteur de diff sur une fixture dense

## Objectif

Prouver, avant de l'écrire dans un `SKILL.md`, qu'un compteur de diff — nombre de plages, de hunks, de lignes changées ou d'occurrences — est le résultat d'une mesure reproductible et non d'une déduction, et que le mot employé par la documentation correspond au contrat réel de l'outil.

## Quand l'utiliser

- une documentation affirme `CHANGED n`, « n hunks », « n lignes changées » ou un nombre d'occurrences sans dire comment il a été obtenu ;
- `diff -u` et `diff -U0` ne donnent pas le même nombre de hunks sur le même couple de fichiers ;
- le compteur annoncé égale le nombre d'edits appliqués alors que certains edits ne changent aucun octet ;
- une vérification faite sur des changements éloignés passe, mais la même affirmation échoue dès que les changements se rapprochent ;
- il faut arbitrer entre corriger la documentation et changer le seuil ou la fixture.

## Quand ne pas l'utiliser

| Situation | Renvoi |
|---|---|
| comparer clé par clé la doc et les sorties du CLI | `verifier-parite-doc-script-skill` |
| assembler un lot d'edits dans un SKILL.md | `appliquer-lot-edits-skill-script-assertions` |
| prouver qu'une mutation de test a bien été écrite | `verifier-mutation-fixture-appliquee` |
| rejouer une fixture déjà consignée | `replay-skill-reference-fixtures` |
| compter messages, revisions ou fichiers dans une preuve de session | `audit-evidence-count-provenance` |
| écriture concurrente du paquet pendant l'opération | `skill-update-concurrency-safe` |
| contrôle statique après écriture | `skill-file-qa` |

## Règles non négociables

1. Un compteur sans unité n'est pas vérifiable : écrire `plages`, `hunks`, `lignes` ou `occurrences`, jamais un nombre nu.
2. La mesure se fait sur une fixture créée hors du dossier du Skill, jamais sur le fichier installé qu'on est en train de décrire.
3. La fixture contient au moins deux blocs modifiés séparés de 1 à 6 lignes inchangées. Au-delà de 6, `diff -u` ne peut plus fusionner et la mesure ne distingue plus « plage » de « hunk ».
4. La fixture contient au moins une substitution sans effet (`old == new`, ou un remplacement qui restaure les mêmes octets) : un compteur qui compte les applications au lieu des changements doit être démasqué.
5. La fixture satisfait les prérequis de l'outil. Un outil qui parse un frontmatter refuse un fichier texte nu : adapter la fixture, pas l'assertion.
6. Le SHA-256 de la source est relevé avant et après la mesure ; toute modification de la source invalide la mesure.
7. Trois nombres sont relevés : le compteur de l'outil, les hunks de `diff -u`, les hunks de `diff -U0`. Un seul nombre n'est pas une preuve.
8. `diff -u` (contexte 3) fusionne deux blocs séparés par au plus 6 lignes inchangées, soit `2 × contexte`. `diff -U0` ne fusionne que des lignes contiguës. Le seuil mesuré n'est pas « strictement moins de 6 ».
9. Un compteur de plages compte des blocs de lignes contiguës, pas des edits : deux edits sur des lignes voisines produisent une seule plage.
10. Si la documentation dit « hunks » alors que le compteur vaut le nombre de plages, la documentation doit imposer `diff -U0`. Ni le seuil ni la fixture ne sont modifiés pour faire coïncider les nombres.
11. Toute correction de la documentation est rejouée sur la même fixture. Une mesure n'est valide que pour la version du script et l'empreinte de la doc mesurées.
12. Fixtures supprimées après la mesure ; aucun `__pycache__` ni fichier temporaire ne reste dans le dossier du Skill.

## Procédure

Variables utilisées ci-dessous :

```bash
SKILLS_ROOT="$HOME/.qoder/skills"
SKILL_DIR="$SKILLS_ROOT/verifier-comptage-diff-fixture-dense"
TOOL="$SKILLS_ROOT/appliquer-lot-edits-skill-script-assertions/scripts/assembler.py"
DOC="$SKILLS_ROOT/<skill-cible>/SKILL.md"
WORK="$HOME/.qoder/tmp/comptage-diff/<skill-cible>"
```

### 0. Figer le sujet mesuré

```bash
sha256sum "$TOOL" "$DOC"
diff --version | head -1
```

La conclusion ne vaut que pour ces octets et cette implémentation de `diff`. La fusion des hunks est une propriété de l'outil de diff, pas du script mesuré.

### 1. Nommer l'unité revendiquée

Recopier la phrase exacte de la documentation :

- « le nombre de hunks doit égaler `CHANGED` » → unité attendue : hunks ;
- « 5 plages modifiées » → unité attendue : plages.

Une phrase qui ne nomme aucune unité est déjà un défaut à corriger, indépendamment de la mesure.

### 2. Construire la fixture dense

```bash
mkdir -p "$WORK"
py -3 - "$WORK/source.md" <<'PY'
import sys
from pathlib import Path
lines = ["---", "name: probe", "description: probe", "---", "", "# Titre", ""]
lines += ["L%02d" % i for i in range(1, 61)]
Path(sys.argv[1]).write_bytes(("\n".join(lines) + "\n").encode())
PY
```

Avec ce préambule, `Lnn` occupe la ligne `7 + nn` : `L05` → 12, `L10` → 17, `L30` → 37.

Spec pour l'outil d'exemple (`EDITS` de l'assembleur) :

```python
EDITS = [
    ("exact", "bloc-1", "L05", "L05 change"),
    ("exact", "bloc-2", "L10", "L10 change"),
    ("exact", "sans-effet", "L30", "L30"),
]
```

Les deux blocs réels sont séparés par 4 lignes inchangées (`L06` à `L09`), donc dans la fenêtre de `diff -u`. Le troisième edit applique `L30` sur `L30` : zéro octet changé. Pour un autre outil, reproduire la même géométrie dans son propre format de spec.

### 3. Exécuter l'outil et relever son compteur

```bash
py -3 -B "$TOOL" --source "$WORK/source.md" --out "$WORK/draft.md" \
  --spec "$WORK/spec.py" --body-max 500 --desc-max 1024 | tee "$WORK/tool.txt"
grep -E '^(APPLY|CHANGED|CHANGED_RANGES|RESULT)' "$WORK/tool.txt"
```

Sur cet exemple, la sortie attendue est trois `APPLY`, `CHANGED 2` avec deux plages (lignes 12 et 17) et `RESULT OK`. Un `RESULT FAIL` signifie que la fixture n'a pas atteint l'outil : corriger la fixture, pas le compteur.

### 4. Relever les deux comptages de diff

```bash
diff -u  "$WORK/source.md" "$WORK/draft.md" > "$WORK/u3.diff" || true
diff -U0 "$WORK/source.md" "$WORK/draft.md" > "$WORK/u0.diff" || true
printf 'hunks_u3=%s hunks_u0=%s changed_lines=%s\n' \
  "$(grep -c '^@@' "$WORK/u3.diff")" \
  "$(grep -c '^@@' "$WORK/u0.diff")" \
  "$(grep -c '^[-+][^-+]' "$WORK/u0.diff")"
sha256sum "$WORK/source.md"
```

Sur cet exemple : `hunks_u3=1`, `hunks_u0=2`, `changed_lines=4`, et la source garde le SHA-256 du début. `grep -c '^[-+][^-+]'` exclut les en-têtes de fichier.

### 5. Attribuer chaque écart

| Observation | Cause mesurée | Conclusion |
|---|---|---|
| `CHANGED` égal à `hunks_u0` et supérieur à `hunks_u3` | `diff -u` a fusionné des blocs séparés d'au plus 6 lignes | le compteur est un nombre de plages ; la doc doit prescrire `-U0` |
| `CHANGED` égal au nombre d'`APPLY` alors qu'un edit est sans effet | le compteur compte les applications | le compteur ne mesure pas les changements ; corriger le script ou la doc |
| `CHANGED` inférieur au nombre d'edits, égal à `hunks_u0` | edits sur lignes contiguës fusionnés en une plage | comportement normal ; ne pas écrire « une plage par edit » |
| `CHANGED` différent de `hunks_u0` sans edit sans effet | désaccord réel | arrêter : relire la sortie complète de l'outil, ne pas ajuster la doc |

### 6. Corriger la doc et rejouer

Remplacer, dans la documentation, la formulation fausse par celle qui égale le contrat mesuré. Exemple : « le nombre de hunks doit égaler `CHANGED` » devient « le nombre de hunks de `diff -U0` doit égaler `CHANGED` ; `diff -u` sert à lire le contexte ».

Si le compteur lui-même est en cause, la correction appartient au script, pas au texte. Dans les deux cas, rejouer la procédure complète depuis l'étape 3 sur la même fixture et consigner les trois nombres.

### 7. Nettoyer et rapporter

```bash
rm -rf "$WORK"
find "$SKILL_DIR" -name '__pycache__' -o -name '*.pyc'
```

`find` doit ne rien rendre. Renseigner le modèle de rapport ci-dessous avec les valeurs mesurées, pas avec les valeurs attendues.

## Échecs fréquents

| Symptôme | Cause | Action |
|---|---|---|
| `CHANGED 5` mais `hunks=4` avec `diff -u` | deux blocs distants de moins de 6 lignes inchangées ont été fusionnés | compter avec `-U0`, puis corriger la doc |
| `APPLY 2` et `CHANGED 1` | un edit était sans effet | comportement correct ; le consigner comme cas de contrôle |
| `FAIL frontmatter: first line is not ---` | fixture texte sans frontmatter | ajouter les quatre lignes de frontmatter |
| `diff: ... No such file or directory` | l'outil a refusé la fixture, aucun draft n'a été écrit | lire le `FAIL`, corriger la fixture ; ne pas compter 0 comme un résultat |
| deux edits voisins donnent `CHANGED 1` | blocs contigus fusionnés en une plage | normal ; ne pas conclure à un bug |
| `hunks_u3` égal à `hunks_u0` | aucun bloc sous la fenêtre de contexte | la fixture n'est pas dense ; rapprocher les changements |
| `RESULT OK` mais `CHANGED` nul | tous les edits étaient sans effet | la fixture ne mesure rien ; ajouter deux blocs réels |

## Limites

- La mesure porte sur l'implémentation de `diff` utilisée : GNU diffutils 3.12 pour les chiffres cités dans la référence.
- Les compteurs d'occurrences ne passent pas par `diff` : la densité se remplace par un cas où l'occurrence est dupliquée et par un cas où elle est absente.
- Le Skill prouve le nombre et son unité, pas la vérité de la prose qui l'entoure.
- Comportement non mesuré sur des fixtures CRLF, BOM, fichier vide ou diff binaire.

## Ressources

- `references/evidence-2026-10-28.md` : session source, sorties verbatim des deux pièges, mesure du seuil de fusion, cas sans effet, prérequis de frontmatter.

## Modèle de rapport

```
Sujet: <skill>/<script> | SHA-256 outil <hash> | SHA-256 doc <hash>
Unité revendiquée: <plages|hunks|lignes|occurrences> | phrase: "<citation>"
Fixture: source <n> lignes | gap <1-6> | no-op <label> | SHA-256 source <hash> (inchangé: oui|non)
Outil: APPLY <n> | CHANGED <n> | CHANGED_RANGES <...>
Diff: hunks_u3 <n> | hunks_u0 <n> | changed_lines <n> | diff <version>
Verdict: <doc correcte|doc corrigée vers -U0|script à corriger|mesure invalide>
Rejeu: <identique|écart>
Non vérifié: <liste>
```
