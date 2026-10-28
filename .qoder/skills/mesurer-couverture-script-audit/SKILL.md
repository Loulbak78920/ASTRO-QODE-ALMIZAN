---
name: mesurer-couverture-script-audit
description: "Mesurer la couverture réelle d'un script d'audit en lecture seule avant de lire son verdict vert comme une preuve d'absence : extraire du code la liste blanche d'extensions, les dossiers ignorés, le plafond de taille, la valeur unique recherchée, le nom de temporaire et la table rc ; construire hors Skill une fixture jetable avec contrôle positif puis fuites cachées (extension non listée, plafond, dossier ignoré, UTF-16, .tmp) ; exécuter chaque cas séparément, rc hors pipe, et asserter l'absence du secret sur stdout et stderr ; classer fichiers=0 avec RESULT OK comme succès à vide, « 20 affichées sur 46 » comme troncature ; corriger le script ou documenter sans changer son hash, puis rejouer skill-file-qa et vérifier chaque citation fichier et ligne. Utiliser avant de déclarer « aucun secret », « aucune écriture » ou « aucun résidu » sur la foi d'un RESULT OK, ou quand un audit vert coexiste avec une fuite connue. 在信任只读扫描脚本的绿色结果前，实测其覆盖边界（白名单扩展名、忽略目录、大小上限、唯一检索值、临时文件名、rc 映射），用隐藏泄露夹具区分空转通过与真实覆盖。"
---

# Mesurer la couverture réelle d'un script d'audit

## Portée

Établir **par mesure** ce qu'un script d'audit ou de scan en lecture seule ne regarde pas, puis corriger la documentation qui s'appuyait sur son résultat vert.

Hors portée, à déléguer : parité entre doc et CLI (`verifier-parite-doc-script-skill`), A/B du sens des rc entre deux outils (`verifier-jugement-cli-par-fixtures`), existence et arguments d'un script de dépendance (`audit-skill-tool-contracts`), rejeu d'une fixture déjà documentée (`replay-skill-reference-fixtures`), effets de bord d'une vérification dite en lecture seule (`verifier-effets-de-bord-verification-lecture-seule`), forme du paquet (`skill-file-qa`). Ce Skill mesure un périmètre ; il ne valide pas la mise en forme.

## 1. Invariants

1. Un verdict vert signifie seulement : « dans les N fichiers que le script a bien voulu lire, l'unique valeur recherchée n'apparaît pas ». Il ne signifie jamais « aucun secret », « aucune écriture », « aucun résidu ».
2. Un cas caché qui rend **vert** est le résultat attendu : c'est la mesure de la limite, pas une panne du harnais.
3. Le contrôle positif passe **avant** les cas cachés. Sans lui, un vert ne distingue pas « script limité » de « fixture mal construite ».
4. Fixture hors du dossier du Skill, dans un répertoire jetable ; suppression prouvée par un before/after d'existence.
5. Le secret factice ne doit apparaître ni sur stdout ni sur stderr ; l'asserter par recherche exacte, pas à l'œil.
6. Chaque cas tourne séparément ; le rc est lu hors pipe.
7. On ne documente que ce qui a été mesuré. Le reste est classé INFERRED avec la ligne de code.

## 2. Étape 1 — Extraire la portée du code

Chercher dans le script, jamais dans sa documentation :

| À extraire | Formes typiques | Question posée |
|---|---|---|
| Liste blanche d'extensions | liste de suffixes, `endswith`, `suffix in` | quels fichiers ne sont jamais ouverts |
| Dossiers ignorés | ensemble de noms, `rglob` + `continue` | quelles arborescences sont absentes |
| Plafond de taille | `MAX`, `2_000_000`, `stat().st_size` | quel fichier est sauté, et avec ou sans compteur |
| Valeur recherchée | `needle`, `in texte`, `re.compile` | quelle variante du secret échappe |
| Décodage | `read_bytes().decode(..., "ignore")` | quel encodage devient illisible |
| Nom de temporaire | `with_suffix(... + ".tmp")` | quels résidus ne sont pas contrôlés |
| Table rc | `return 0/1/2`, listes `fails` / `avertissements` | quel constat ne change pas le rc |
| Plafond d'affichage | `max-findings`, `[:20]`, `tronque` | ce qui est compté sans être montré |

Produire le tableau « Limite | Code (fichier, ligne) | Conséquence » **avant** la moindre exécution : il est le plan de la matrice de fixtures.

## 3. Étape 2 — Construire la fixture

Racine via `mktemp -d`. Deux racines quand c'est possible : une normale, une dont un composant du chemin figure dans la liste des dossiers ignorés (par exemple `.qoder`). La seconde attrape la comparaison sur composants **absolus**, qui vide le scan entier.

Une racine par cas, pour que les cas ne se contaminent pas :

| Cas | Contenu | Lecture d'un résultat |
|---|---|---|
| A contrôle positif | secret dans un fichier de la liste blanche | doit être rouge, occurrence localisée |
| B fuites cachées | secret dans une extension non listée, dans un fichier au-dessus du plafond, dans un dossier ignoré | **vert = trois angles morts mesurés** |
| C témoin | secret dans un petit fichier de la liste blanche | doit être rouge |
| D résidu | fichier de secrets suivi de `.tmp` | doit être rouge |
| E encodage | secret en UTF-16 | vert = décodeur aveugle |
| F plafond d'affichage | plus d'occurrences que le défaut | total exact, lignes montrées incomplètes |
| G chemin ignoré | racine sous `.qoder` | rouge attendu ; vert = bug de composants absolus |

Squelette d'exécution, une racine par cas :

```bash
FI=$(mktemp -d "${TMPDIR:-/tmp}/cov-audit-XXXXXX")
S='FAKE-MDP-COUVERTURE-2026'
SCAN=/chemin/vers/le/script_audite.py
mkdir -p "$FI/A/secrets"
printf '{"hote":"h","user":"u","mot_de_passe_ssh":"%s"}' "$S" > "$FI/A/secrets/ovh.json"
printf 'ligne 1\n%s\n' "$S" > "$FI/A/notes.md"

out=$(mktemp); err=$(mktemp)
PYTHONIOENCODING=utf-8 py -3 -B "$SCAN" --secrets "$FI/A/secrets/ovh.json" --racine "$FI/A" >"$out" 2>"$err"
rc=$?
cat "$out"; [ -s "$err" ] && cat "$err"
echo "rc=$rc"
grep -qF "$S" "$out" "$err" && echo "FUITE_DANS_LA_SORTIE" || echo "secret_in_output=False"
```

Pour le cas B, dimensionner le fichier à plafond + 99 999 octets, pas plafond + 1 : une marge évite l'ambiguïté entre `<=` et `<`.

Pour rejouer la matrice sans réécrire le harnais, `scripts/rejouer_matrice.py --matrice <json>` crée une racine par cas hors du Skill, lit le rc hors pipe, vérifie `contient` / `absent`, censure le secret et échoue s'il apparaît sur stdout ou stderr. Le schéma est dans l'en-tête du script ; la clé `base` place les racines sous un composant ignoré (`.qoder`) pour le cas G.

## 4. Étape 3 — Lire les résultats

- `fichiers=0` avec verdict vert : **succès à vide**. Jamais une preuve d'absence ; c'est un signal d'arrêt à instruire.
- `fichiers=N>0` ne démontre pas la couverture des cas B et E : seuls B et E le font.
- Un compteur sans effet sur le rc (avertissement, anti-modèle) ne rend pas le verdict « propre » ; le citer séparément.
- Affichage tronqué : écrire « 20 affichées sur 46 ». Ne jamais convertir un total en contenu : « 46 fois sudo -S » est faux si 26 lignes n'ont pas été lues.
- Lire la table rc, pas seulement le code de sortie : quel constat produit 1, lequel produit 0, lequel produit 2.
- Un cas caché vert prouve l'angle mort ; il ne prouve pas que la même limite se manifeste en production. Cette extrapolation reste INFERRED.

## 5. Étape 4 — Corriger le script ou documenter la limite

| Constat | Action | Preuve attendue |
|---|---|---|
| Bug de périmètre (comparaison sur composants absolus, filtre inversé) | corriger le script, rejouer tout le harnais | avant : cas fautifs verts ; après : tous rouges, harnais 0 échec, nouveau SHA-256 |
| Limite de conception assumée | ne pas toucher au script ; documenter | SHA-256 du script identique avant et après |
| Filtre sans compteur | documenter, sans inventer de taux de couverture | ligne de code citée |

Ne pas mélanger les deux dans une même modification : un hash de script qui change doit correspondre à un correctif, pas à une reformulation.

## 6. Étape 5 — Modifier la documentation au minimum

- Corriger le critère de sortie qui s'appuyait sur le verdict seul : exiger la conjonction du verdict **et** d'un périmètre non vide (`fichiers=N>0`).
- Mettre les sorties verbatim dans une référence datée, pas dans le corps du SKILL.md.
- Classer chaque affirmation : REPRODUCED (sortie obtenue dans la session, avec le SHA-256 des octets exécutés), INFERRED (lecture de code, non exercée), UNVERIFIED.
- Une référence est liée à des octets : si le script change, la mesure est à refaire et l'ancienne référence à dater.

## 7. Étape 6 — Vérifier et nettoyer

```bash
py -3 -B /chemin/vers/validate_skill.py /chemin/vers/le/paquet   # RESULT PASS attendu
sha256sum SKILL.md references/*.md scripts/*.py                   # empreintes par fichier
```

Puis : recalculer les citations « fichier + ligne » du paquet (MATCH / DRIFT), supprimer la fixture et prouver sa disparition, vérifier l'absence de `__pycache__`, `.pyc` et `.tmp` résiduels.

## 8. Pièges

| Piège | Symptôme observé | Correctif |
|---|---|---|
| Fixture sous un composant ignoré, script comparant les composants absolus | `fichiers=0` et verdict vert alors que le secret est présent | racine hors liste + cas G dédié qui doit être rouge |
| Contrôle positif absent | on documente une limite peut-être inexistante | cas A rouge exigé avant tout cas caché |
| rc lu dans un pipe | rc toujours 0 | redirections séparées puis `rc=$?` |
| Le scanner imprime le secret qu'il cherche | la preuve devient la fuite | `grep -F` exact sur stdout et stderr, échec bloquant |
| Fichier de test juste au-dessus du plafond | cas ambigu si la comparaison est inclusive | marge de 99 999 octets |
| Total tronqué promu en vérité | « 46 fois … » alors que 20 lignes seulement sont lisibles | écrire « affichées sur » |
| Référence réutilisée après modification du script | mesure périmée attachée à d'autres octets | comparer le SHA-256 avant de citer |
| Fixture laissée dans le projet | fausse les scans suivants, et le nettoyage n'est pas prouvé | suppression + before/after d'existence |
| Windows : alias `python` du Store, console cp1252 | rc 49, sortie illisible | `py -3 -B`, `PYTHONIOENCODING=utf-8` |

## 9. Cas vérifié

`references/cas-2026-10-28-scan-secrets.md` : cas A à G exécutés le 2026-10-28 contre `auditer_secrets_locaux.py` (6 555 octets, SHA-256 `128f1695…`), plus le premier run réel 698 fichiers / 0 fuite / 46 anti-modèles, et le bug de composants absolus corrigé le même jour.

## Ressources

- `references/cas-2026-10-28-scan-secrets.md` — sorties verbatim, table des limites avec lignes de code, classement REPRODUCED / INFERRED, et ce que la mesure ne prouve pas.
- `scripts/rejouer_matrice.py` — rejoue une matrice JSON de fixtures : une racine par cas, rc hors pipe, `contient` / `absent`, censure de la sortie et échec si le secret fuit.
