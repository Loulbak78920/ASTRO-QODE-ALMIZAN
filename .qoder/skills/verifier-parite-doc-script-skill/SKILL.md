---
name: verifier-parite-doc-script-skill
description: "Vérifier la parité entre la documentation d'un Skill et le comportement réel de son script CLI après un PASS de skill-file-qa : extraire tous les jetons KEY=VALUE, codes de retour et assertions d'acceptation promis par SKILL.md et references, énumérer les clés réellement émises par le script (emit/print/argparse), construire des fixtures positives et négatives par branche et vérifier l'existence et la valeur de chaque clé (pas seulement le code de retour), puis corriger le script ou la documentation et rejouer fixtures, skill-file-qa et empreintes finales. Utiliser quand un QA 9 PASS/0 FAIL laisse des clés documentées absentes, quand les fixtures n'assertent que le rc, quand un mode NA n'est pas couvert, ou avant de livrer un Skill avec vérificateur CLI. 中文触发：文档承诺的键不存在、SKILL.md 与脚本输出不一致、KEY=VALUE 契约、QA 全 PASS 仍漏检、负向夹具只断言退出码、NA 分支、修复脚本后重跑、最终指纹。"
---

# Parité entre la documentation d'un Skill et les sorties de son script

## Portée

Appliquer ce Skill à un Skill qui embarque un vérificateur, un contrôleur ou un générateur CLI et dont le `SKILL.md` ou les `references` promettent des sorties observables : clés de forme `clé=valeur`, `RESULT PASS/FAIL`, codes de retour, valeurs `yes`/`no`/`NA`.

Ne pas l'utiliser pour :

- la structure, le frontmatter, les références ou les empreintes : `skill-file-qa` ;
- le contrat d'un script appartenant à un autre Skill : `audit-skill-tool-contracts` ;
- la ré-audit d'une dépendance après changement de hash : `dependency-script-contract-reaudit` ;
- le rejeu d'un fixture déjà consigné dans une référence : `replay-skill-reference-fixtures` ;
- l'auto-test d'un validateur statique : `skill-validator-selftest`.

## Règle centrale

Un PASS structurel ne prouve pas le contrat. Chaque clé documentée doit être observée au moins une fois, avec la valeur attendue pour la branche exécutée ; un fixture qui ne vérifie que le code de retour ne détecte pas une clé disparue. Si la clé disparaît, le fixture doit échouer.

Corollaire : ne jamais supprimer une promesse du document pour faire passer le script. Si le script doit produire la clé, ajouter la clé et l'utiliser dans la décision ; si le document est faux, corriger le document.

## Étape 0 — Délimiter et figer

1. Identifier le dossier du Skill cible, le ou les scripts concernés, les modes (`compare`, `absent`, etc.) et les documents qui décrivent le contrat.
2. Relever `size`, `mtime_ns` et SHA-256 de chaque document et script avant toute exécution.
3. S'arrêter si un fichier change pendant la lecture : une autre session écrit. Attendre une version stable, puis repartir du nouveau baseline.
4. Ne pas exécuter les branches destructives du script cible. Les fixtures se font sur des copies jetables sous `~/.qoder/tmp`.

## Étape 1 — Extraire le contrat documenté

Depuis le dossier de ce Skill :

```bash
SKILL_CIBLE="C:/Users/Administrateur/.qoder/skills/nom-du-skill"
py -3 "$HOME/.qoder/skills/verifier-parite-doc-script-skill/scripts/verifier_parite_cles.py" \
  --skill "$SKILL_CIBLE"
```

Le script est en lecture seule. Il examine `SKILL.md` et `references/**/*.md`, extrait les jetons `clé=valeur` des blocs de code et du code inline, puis les compare aux clés réellement émises par les scripts (`emit("SCOPE_FALLBACK_ALL", …)`, `print("RESULT=…")`, f-strings).

Construire ensuite un tableau manuel :

| Clé | Valeurs documentées | Branche | Normative ou illustrative | Source |
|---|---|---|---|---|

- Une clé est normative si le document demande de l'attendre ou de la vérifier.
- Une clé illustrative (exemple historique, sortie d'un autre outil) doit être passée à `--allow-key` et justifiée dans le rapport.
- Les clés doivent être dans des backticks ou un bloc de code pour être extraites. Une clé seulement en prose ou dans un tableau sans backticks est invisible pour l'outil : la corriger dans le document.
- Le script ne juge que la présence. Les valeurs et les codes de retour sont vérifiés par les fixtures de l'étape 3.

### Auto-contrôle du paquet

Appliquer d'abord le vérificateur à ce Skill lui-même, avec `--skill` pointant sur son propre dossier. Un PASS n'est significatif que si des jetons ont réellement été comparés :

- viser `DOC_KEYS>0`, `MATCHED=DOC_KEYS`, `DOC_ONLY=0` ;
- un `DOC_KEYS=0` avec `RESULT=PASS` est un PASS vide : aucun jeton en portée n'a été comparé, il ne prouve pas la parité ;
- un `DOC_ONLY_KEY` sur un placeholder méta (forme `clé=valeur` écrite en majuscules, ou `print("clé=…")`) signifie que l'exemple est lu comme une clé promise : écrire les placeholders en minuscules et garder les vraies clés en majuscules entre backticks ;
- ne jamais supprimer une promesse documentée pour faire baisser `DOC_ONLY` ;
- la section qui nomme `scripts/verifier_parite_cles.py` doit citer les en-têtes réellement émis, sinon `MATCHED` reste à 0 malgré un document fourni ;
- rejouer cet auto-contrôle après toute modification de `SKILL.md` ou des `references` : un ajout de prose peut créer un faux jeton ou déplacer une clé hors de la section du script.

## Étape 2 — Énumérer le contrat runtime

Lire la source du script et relever :

- les appels `emit("DOC_ONLY", …)` et les `print("RESULT=…")` ;
- les constantes de code de retour (`EXIT_PASS`, `EXIT_FAIL`, `EXIT_USAGE`) ;
- les options `argparse` et leur mode d'erreur ;
- les branches qui produisent `NA` ou qui omettent une clé.

Le rapport de `scripts/verifier_parite_cles.py` émet ses en-têtes avant le détail : `SCOPE_FALLBACK_ALL=no|yes`, `DOC_KEYS=<n>`, `MATCHED=<n>`, `DOC_ONLY=<n>`, `RUNTIME_ONLY=<n>`, `RESULT=PASS|FAIL`. Il sépare :

| Ensemble | Signification | Décision |
|---|---|---|
| `MATCHED` | clé documentée et émise | conserver |
| `DOC_ONLY` | documentée mais jamais émise | défaut : corriger le script ou le document |
| `RUNTIME_ONLY` | émise mais non documentée | champ interne acceptable, ou ajouter au contrat |
| `OUT_OF_SCOPE` | documentée hors section du script | vérifier qu'il ne s'agit pas d'une vraie clé de contrat |
| `ALLOWED` | illustrative, exclue volontairement | justifier dans le rapport |

`DOC_ONLY` non vide ⇒ `RESULT FAIL`, code 1. `RUNTIME_ONLY` est informatif et ne fait pas échouer. Si une vraie clé tombe dans `OUT_OF_SCOPE`, déplacer la clé dans la section qui nomme le script, ou forcer l'inclusion avec `--scope-key`.

## Étape 3 — Fixtures par branche

Chaque cas vérifie le code de retour et des paires exactes, pas une sous-chaîne isolée. Le minimum :

| # | Branche | Attendu |
|---|---|---|
| 1 | baseline valide | rc 0, `RESULT=PASS`, toutes les clés positives avec leur valeur |
| 2 | chaque invariant violé | rc 1, la clé concernée passe à `no`, message localisable |
| 3 | usage ou environnement invalide | rc 2, `ERROR=` non vide |
| 4 | clé non applicable | `clé=NA`, jamais clé absente ou valeur vide |
| 5 | mode après action (si le script en a un) | rc et clés propres à ce mode |
| 6 | lien symbolique ou jonction | rc 1, ou `CASE SKIP` explicite si la création est impossible |
| 7 | preuve de mutation | le fixture a réellement changé la cible (hash ou comptage avant/après) |

Règles d'assertion :

- comparer `rc` à l'entier exact ;
- parser la sortie en dictionnaire `KEY → VALUE` et comparer la valeur exacte ;
- si `rc=0`, aucune ligne `FAIL` ; si `rc=1` ou `2`, au moins un message actionnable ;
- pour chaque négatif, prouver la mutation avant d'attendre l'échec : sinon le cas peut passer sans rien tester ;
- capturer la sortie de chaque branche dans un fichier pour le rapport ;
- sur Windows, utiliser `py -3`, ne pas prendre le code à travers un pipeline, et prévoir un `force_rmtree` avec `chmod` pour les objets `.git` en lecture seule.

Le modèle complet, avec `force_rmtree`, preuve de mutation et les 12 cas de la session source, est dans `references/harnais-fixtures.md`.

## Étape 4 — Exécuter et trier

1. Lancer la matrice complète sur des copies jetables ; ne pas lancer les branches destructives sur le vrai Skill.
2. Relever pour chaque cas : commande, entrée, rc réel, paires attendues, paires observées.
3. Relancer le vérificateur de parité après toute correction du script.
4. Classer chaque écart :
   - clé documentée absente de la source : `DOC_ONLY` ;
   - clé présente mais absente de la branche : fixture manquante ou branche qui omet la clé ;
   - valeur différente : comportement ou attente erronée, à investiguer ;
   - `NA` remplacé par une omission : contrat incomplet.

## Étape 5 — Corriger sans affaiblir

- Script incomplet : calculer la clé, l'émettre et l'inclure dans la condition de succès. Une clé seulement affichée mais absente de la décision laisse passer un faux PASS.
- Document faux : corriger le document, pas le script. Si la clé est réellement illustrative, l'exclure avec `--allow-key` et l'expliquer.
- Ne jamais modifier une valeur attendue pour qu'elle corresponde à une sortie suspecte.
- Mettre à jour dans le même passage : le script, la liste d'acceptation du document et les paires attendues du fixture. Ajouter la clé manquante au fixture comme assertion de régression.
- Rejouer toute la matrice, pas seulement le cas corrigé. Une correction peut casser une autre branche.

## Étape 6 — Rejouer et sceller

1. Matrice complète : `FAILS=0`, aucun `CASE SKIP` non justifié.
2. Vérificateur de parité : `DOC_ONLY=0`, `RESULT=PASS`, code 0.
3. Auto-contrôle du paquet après toute modification de `SKILL.md` ou des `references` : `DOC_KEYS>0`, `MATCHED=DOC_KEYS`, `DOC_ONLY=0`. Un PASS avec `DOC_KEYS=0` est vide et ne compte pas.
4. `skill-file-qa` : `RESULT PASS`. Rappel : ce PASS ne prouve pas la parité des clés ; il valide la structure, les références et les empreintes.
5. Porte de fingerprint finale : double échantillonnage de `SKILL.md`, comparaison avec le `Fingerprint (final)` du validateur. Enregistrer séparément les SHA-256 de `SKILL.md`, des `references` et du script, car le validateur ne couvre que `SKILL.md`.
6. Supprimer les fixtures et les caches `__pycache__` créés par la session. Ne pas laisser de harnais dans le paquet du Skill.
7. Rapporter les branches non déclenchées (jonction indisponible, branche destructive non exécutée, etc.) sans les présenter comme vérifiées.

## Tableau des erreurs

| Symptôme | Cause | Action |
|---|---|---|
| `skill-file-qa` passe alors qu'une clé documentée manque | le validateur statique ne compare pas le document aux sorties | lancer le vérificateur de parité, puis les fixtures |
| 12 fixtures passent mais une clé est absente | les cas n'assertent que `rc` ou un seul texte | comparer les paires exactes `clé=valeur` |
| `DOC_ONLY=0` mais la branche n'émet pas la clé | le vérificateur lit la source, pas l'exécution | ajouter un fixture pour cette branche |
| `OUT_OF_SCOPE` contient une vraie clé | la section ne nomme pas le script | déplacer la clé dans la section de contrat ou `--scope-key` |
| `RUNTIME_ONLY` très large | champs internes ou journalisation | décider : documenter ou accepter comme interne |
| `clé=NA` absent sur un cas non applicable | branche qui omet la clé au lieu d'émettre `NA` | émettre `NA` explicitement |
| un négatif passe comme le baseline | la mutation n'a pas eu lieu | assertir le hash ou le comptage avant/après |
| `PermissionError [WinError 5]` au nettoyage | objets `.git` en lecture seule | `force_rmtree` avec `chmod` |
| code de retour toujours 0 | code capturé à travers un pipeline | exécuter, puis lire `$?` ou `returncode` |
| clé documentée non extraite | clé en prose ou sans backticks | la placer dans un bloc de code ou des backticks |
| `--allow-key` masque un vrai défaut | clé illustrative déclarée à tort | justifier chaque exclusion dans le rapport |
| `DOC_KEYS=0` avec `RESULT=PASS` | aucun jeton en portée, ou auto-contrôle lancé sur un document qui ne nomme pas le script | documenter les en-têtes réels dans la section du script, puis exiger `MATCHED` non nul |
| `DOC_ONLY` sur un placeholder méta | un exemple de forme `clé=valeur` écrit en majuscules est extrait comme clé promise | passer le placeholder en minuscules, garder les vraies clés en majuscules |

## Checklist

- [ ] Documents et scripts figés (hash) avant les tests.
- [ ] Toutes les clés documentées extraites, illustratives justifiées.
- [ ] Toutes les clés runtime énumérées, `RUNTIME_ONLY` trié.
- [ ] `DOC_ONLY=0` ou chaque clé restante corrigée.
- [ ] Un fixture par code de retour documenté (0, 1, 2).
- [ ] Chaque négatif a une preuve de mutation.
- [ ] La branche `NA` est couverte.
- [ ] Les valeurs sont comparées exactement, pas seulement `rc`.
- [ ] Script, liste d'acceptation et fixture mis à jour ensemble.
- [ ] Auto-contrôle du paquet non vide : `DOC_KEYS>0`, `MATCHED=DOC_KEYS`, `DOC_ONLY=0`.
- [ ] `skill-file-qa` PASS et empreintes finales enregistrées.
- [ ] Aucun `__pycache__`, fixture ou backup dans le paquet.

## Ressources

- `references/cas-verifie-2026-10-26.md` : preuves de la session source, 3 PASS de QA avec le défaut, remède, empreintes finales et auto-contrôle du paquet (session 05dfc264).
- `references/harnais-fixtures.md` : modèle de harnais, `force_rmtree`, preuve de mutation et 12 cas.
- `scripts/verifier_parite_cles.py` : vérificateur de présence document/runtime, lecture seule, codes 0/1/2.
