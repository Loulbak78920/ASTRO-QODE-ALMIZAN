---
name: skill-staged-delivery
description: "Livrer un Skill selon un sous-ensemble explicite demandé par l'utilisateur — SKILL.md seul, SKILL.md avec références, scripts différés ou exclus définitivement — sans surpromettre : écrire après le H1 les listes inclus, différés et exclus ; ne jamais présenter un exclu comme « à venir » ; réécrire en commandes autonomes vérifiées toute étape qui dépendait d'un script exclu ; déclarer que tout fichier non listé sous « inclus » est hors périmètre — ni livré, ni vérifié, ni preuve, ni modifié ou supprimé sans autorisation explicite du chemin — et n'inventorier les chemins que dans le rapport de session ; rapporter la composition de Files (n) sans attribuer un PASS à un exclu ; sur demande séparée, sauvegarder un exclu hors du Skill avec SHA-256 identique avant de supprimer le seul chemin nommé, puis relancer la QA ; distinguer périmètre réduit définitif (checklist close) et phase 2 des seuls fichiers différés. 中文触发：部分交付、只写文档和参考文件、不加脚本、永久排除脚本、范围外文件、范围外并发产物、QA Files 计数、内联命令替代脚本、正文依赖缺失、交付边界。"
---

# Livrer un Skill selon un sous-ensemble explicite (inclus, différés, exclus)

## Objectif

Permettre de livrer un Skill selon un sous-ensemble explicite sans surpromettre. Le périmètre a trois états : **inclus** (écrit et vérifié), **différé** (promis pour une phase 2), **exclu définitivement** (jamais fourni sans une nouvelle instruction). Un sous-ensemble peut être définitif : SKILL.md seul, ou SKILL.md avec ses références et aucun script.

Le corps de SKILL.md doit rester complet pour le périmètre annoncé. Une ressource exclue ne laisse pas d'étape orpheline : la procédure est réécrite en commandes autonomes et vérifiée, ou le périmètre est explicitement réduit. Un PASS statique ne devient jamais une validation fonctionnelle, et la présence d'un fichier hors périmètre ne valide rien.

## Quand l'utiliser

- L'utilisateur confirme un plan puis réduit le périmètre : « d'abord seulement SKILL.md », « seulement les documents et les références, sans script », « scripts et preuves plus tard », « ne touche que SKILL.md ».
- L'utilisateur exclut définitivement une catégorie de ressources (scripts, assets, traduction) au lieu de la différer.
- Un Skill existant ne doit être modifié que dans un sous-ensemble de ses fichiers, sans toucher aux autres.
- Une session s'arrête ou doit reprendre plus tard, et l'état partiel doit rester exact.
- La cible contient déjà des fichiers non demandés, notamment créés par une autre session.
- Un PASS statique risque d'être présenté à tort comme une validation fonctionnelle, ou étendu à un fichier hors périmètre.
- Le paquet doit rester utilisable sans tromper un futur agent sur les fichiers présents.

Ne pas utiliser pour :

- livrer un package complet en une seule étape ; suivre skill-creator (CLI intégré) ;
- sécuriser une écriture concurrente ou arbitrer create/update ; utiliser `skill-update-concurrency-safe` ;
- reprendre un dossier créé par une autre session et arbitrer un doublon ; utiliser `adopt-concurrent-duplicate-skill` ;
- attendre la fin d'un écrivain actif avant d'écrire ; utiliser `audit-skill-during-live-creation` ;
- détailler les contrôles frontmatter, références et empreintes ; utiliser `skill-file-qa` ;
- auditer les preuves d'une session source ; utiliser `audit-session-evidence` ;
- migrer un Skill canonique ou une couche de compatibilité ; utiliser `skill-canonical-migration`.

## Contrat non négociable

1. **Périmètre explicite.** Écrire les fichiers inclus, différés et exclus dans la déclaration de livraison et dans le rapport final. Ne pas laisser « plus tard » implicite et ne pas confondre un exclu avec un différé.
2. **Le sous-ensemble ne couvre que les ressources.** SKILL.md doit être complet pour le périmètre annoncé. Ne jamais différer une section, un contrat ou une procédure en invoquant la livraison partielle.
3. **Déclaration en tête de corps.** Placer la section d'état juste après le H1, avant l'objectif. Elle liste les fichiers inclus, les fichiers différés, les catégories exclues et la règle applicable aux fichiers non listés.
4. **Fichiers absents hors des références locales.** Les écrire en gras ou en texte simple avec la mention « à créer ». Ne pas les entourer d'accents graves comme chemins relatifs, ne pas créer de lien Markdown et ne pas produire de lien file:// vers un fichier absent. Une catégorie exclue s'écrit sans chemin.
5. **Interdiction d'exécution pour les différés.** Tant que des ressources différées manquent, ne pas exécuter la procédure du Skill, ne pas le présenter comme validé, testé ou prêt à l'emploi. Un périmètre réduit sans différé n'est pas bloqué : ses commandes autonomes peuvent être exécutées, mais le PASS statique reste distinct de cette exécution.
6. **Statique n'est pas fonctionnel.** Un PASS de `skill-file-qa` ne prouve ni l'exécution d'un script, ni le comportement du Skill, ni la validité d'un fichier hors périmètre. Le rapport doit dire « statique seulement », lister ce qui n'a pas été exécuté et qualifier la checklist.
7. **Aucun dossier vide ni fichier factice.** Ne pas créer un dossier scripts, references ou assets vide, ni un script ou une preuve « placeholder ». Un dossier vide n'est pas une livraison.
8. **create ne remplace jamais.** Si la cible existe, lire les fichiers réels, préserver les règles encore valides et faire une mise à jour minimale. La stabilité, la sauvegarde et l'arbitrage create/update relèvent de `skill-update-concurrency-safe`.
9. **La phase 2 ne concerne que les différés.** Ne pas anticiper leur création. À la phase 2, exécuter les vérifications réelles avant de convertir la déclaration. Un exclu ne s'ajoute pas en phase 2 sans une nouvelle instruction qui change le périmètre.
10. **Aucune publication implicite.** Écrire des fichiers n'est ni un commit ni un push. Ne pas committer ni pousser sans demande séparée.
11. **Trois états, pas deux.** Un exclu n'est ni « à créer » ni « en attente » : il est hors périmètre. Ne pas annoncer une phase 2 qui le fournirait.
12. **Clause générique, inventaire dans le rapport.** Dans SKILL.md, déclarer que tout fichier non listé sous « inclus » est hors périmètre. Ne pas y inscrire les chemins de ces fichiers : les inventorier dans le rapport de session avec taille et SHA-256. Après une suppression autorisée, la clause reste vraie ; seul le rapport change.
13. **Aucun fichier hors périmètre touché sans autorisation.** Ni modifié, ni supprimé, ni présenté comme preuve. Une suppression exige le chemin nommé par l'utilisateur, une sauvegarde hors du Skill avec SHA-256 identique, la suppression du seul chemin et du dossier vide, puis une nouvelle QA.
14. **Files (n) décrit le disque.** Il inclut les fichiers hors périmètre. Rapporter la composition ; ne jamais attribuer le PASS à un fichier exclu ni conclure que le package livré compte n fichiers sans le dire.

## Quatre situations

| Situation | Déclaration attendue | Points de vigilance |
|---|---|---|
| Nouveau Skill, SKILL.md seul, scripts et preuves différés | Livraison partielle provisoire | Futures ressources en gras « à créer » ; aucun dossier vide ; checklist en attente |
| Nouveau Skill, SKILL.md et références, scripts exclus définitivement | Livraison à périmètre réduit, définitive | Exclu = catégorie, pas chemin ; étapes dépendantes réécrites en commandes autonomes ; checklist close pour ce périmètre |
| Skill existant, modification limitée à un sous-ensemble | Périmètre partiel, pas package incomplet | Ne pas toucher aux autres fichiers ; si le nouveau texte dépend d'une ressource absente et incluse, la marquer « à créer » |
| Cible contenant déjà des fichiers hors périmètre | Livraison inchangée, inventaire séparé | Ne rien modifier ni supprimer ; clause générique dans SKILL.md, chemins et empreintes dans le rapport ; `Files (n)` plus grand que le nombre livré |

Dans tous les cas, la déclaration doit permettre à un autre agent de savoir immédiatement ce qui est exécutable, ce qui est différé et ce qui n'appartient pas au Skill. Un périmètre réduit définitif n'est pas une étape 1 : sa checklist est close pour ce périmètre, mais aucune ressource exclue n'est réputée vérifiée.

## Procédure — étape 1 : écrire le sous-ensemble demandé

### 1. Verrouiller le périmètre

- Citer la demande exacte de l'utilisateur, par exemple « seulement les documents et les références, sans script ».
- Écrire trois listes : inclus, différés, exclus définitivement. Si un plan plus large avait été confirmé puis réduit, retenir la dernière instruction et citer les deux.
- Ne pas promettre de phase 2 sans mot explicite (« plus tard », « ensuite », « pour l'instant »). À défaut, traiter la ressource comme exclue et l'écrire dans la déclaration.
- Si l'utilisateur n'a pas explicitement réduit le périmètre, ne pas appliquer ce Skill : livrer le package complet selon skill-creator.
- Décider si le périmètre est provisoire (au moins un différé) ou définitif (aucun différé).

### 2. Réécrire les dépendances exclues

Toute étape qui appelait une ressource exclue doit devenir autonome, sinon la déclaration est fausse.

- Inventorier les références résiduelles par recherche littérale, par exemple `grep -F` ou `rg -F`. Ne pas utiliser une expression avec un point échappé dans une classe de caractères : cela produit une erreur de parsing (constaté avec `\.py\b`).
- Remplacer chaque appel par des commandes autonomes, puis les exécuter sur la cible réelle en lecture seule. Consigner les sorties et les codes ; ne pas écrire « vérifié » pour une commande non exécutée.
- Dans un one-liner Bash, ne pas imbriquer de littéraux d'octets Python du type `b"\r"` ou `b"\n"` entre guillemets doubles : Git Bash les altère et Python lève une SyntaxError (constaté dans la session source). Utiliser `bytes([13])` et `bytes([10])`, ou un here-doc.
- Si une étape ne peut pas être rendue autonome de façon fiable, ne pas l'inventer : la retirer de la portée, la déclarer hors périmètre et le dire.
- Après réécriture, refaire la recherche littérale : aucune mention du fichier exclu ne doit rester.

### 3. Préflight de la cible

```bash
target="$HOME/.qoder/skills/<nom>"
if [ -e "$target" ]; then echo "UPDATE"; else echo "CREATE"; fi
find "$target" -maxdepth 3 -printf '%P | %s bytes\n' 2>/dev/null | sort
```

- Cible absente : créer le dossier avec mkdir sans -p, puis vérifier que SKILL.md n'apparaît pas entre-temps.
- Cible existante : lire SKILL.md et la liste réelle des fichiers ; ne modifier que le périmètre autorisé.
- Noter les fichiers hors périmètre (nom, taille, SHA-256, mtime) pour le rapport, pas pour le corps de SKILL.md.
- Si un autre processus écrit, ne pas écrire : suivre `skill-update-concurrency-safe` et `audit-skill-during-live-creation`. Ne pas écraser un fichier plus récent.

### 4. Écrire la déclaration de livraison

Modèle à placer juste après le H1 :

```text
## État de livraison (AAAA-MM-JJ)

Périmètre : **réduit** (sous-ensemble demandé par l'utilisateur).
Inclus : ce fichier et references/<fichier-existant>.md.
Exclus définitivement : scripts d'assistance. Aucune procédure ci-dessous ne les
appelle ; toutes les vérifications sont des commandes autonomes.
Différés : aucun.

Tout fichier présent dans ce dossier mais non listé sous « Inclus » est hors
périmètre : il n'est ni livré, ni vérifié, ni une preuve pour ce Skill, et il ne
doit être ni modifié ni supprimé sans autorisation explicite de son chemin. Sa
présence ne transforme pas un PASS statique en validation de ce fichier.
```

- Adapter les noms inclus : une référence existante peut rester entre accents graves ; un fichier à créer reste en gras avec « à créer ».
- Pour une catégorie exclue, écrire le type en texte simple (« scripts d'assistance »), sans chemin, sans accents graves, sans lien.
- Ne pas énumérer les fichiers hors périmètre dans SKILL.md. Leur inventaire concret va dans le rapport de session.
- Si au moins un fichier est différé, ajouter le bloc d'attente :

```text
Tant que les fichiers différés manquent :
- ne pas exécuter la procédure prévue pour eux ;
- ne pas présenter le Skill comme validé, testé ou prêt à l'emploi ;
- considérer leur absence comme un état de livraison attendu, pas comme un défaut.
```

- Si aucun fichier n'est différé, ne pas écrire d'attente : le périmètre est définitif et la checklist est close pour ce périmètre. Ne pas écrire non plus « ce Skill est complet » si des ressources sont exclues.
- Ne pas affirmer « aucun fichier hors périmètre » sans avoir listé le dossier.

### 5. N'écrire que le périmètre

- Ne créer que les fichiers inclus. Ne pas créer de dossier scripts, references ou assets vide.
- Ne pas écrire de placeholder, de README, de CHANGELOG ni de fichier de test.
- Si une commande future vers un fichier différé est nécessaire, la placer dans un bloc de code en texte simple, avec un chemin entre guillemets et un nom de fichier entre chevrons. Ne pas imbriquer d'accents graves.
- Ne modifier ni ne supprimer un fichier hors périmètre, même s'il semble inutile ou contredit la nouvelle portée.
- Après écriture, lister les fichiers réels du dossier et comparer avec la liste incluse. Signaler tout écart ; ne pas le corriger par une suppression non autorisée.

### 6. Vérifier statiquement

```bash
QA="$HOME/.qoder/skills/skill-file-qa"
py -3 "$QA/scripts/validate_skill.py" "$target" \
  --workspace "<racine-workspace>" \
  --stable-seconds 2 --stability-timeout 30
```

- Exiger exit 0, RESULT PASS et aucun FAIL. Lire les WARN au lieu de ne regarder que RESULT.
- Rapporter : Files (n), description sur une ligne et ≤1024 caractères, corps <500 lignes, local references, skill references, empreintes de début et de fin.
- Comparer Files (n) au nombre de fichiers inclus. Si n est plus grand, la différence est un fichier hors périmètre : décrire sa composition (nom, taille, SHA-256) dans le rapport. Ne pas attribuer ce PASS au fichier hors périmètre.
- `local references: 0 checked` est fréquent pour un SKILL.md seul. Ce n'est pas une preuve que le package est complet.
- Distinguer les deux compteurs : `local references` compte les liens et chemins locaux, `skill references` les noms de Skills installés. Un zéro sur l'un ne dit rien de l'autre ; lire les deux lignes avant de conclure « aucune référence ».
- Si le validateur signale une référence locale absente, vérifier d'abord si le fichier est inclus mais pas encore écrit. Pour un fichier à créer, retirer les accents graves ; pour un fichier hors périmètre, retirer son chemin du corps.
- Pour recouper le compte, `check_package_manifest.py` de `skill-package-integrity-audit` peut comparer `Files (n)` au disque avec `--qa-log`. Il audite aussi les caches et les fichiers inattendus ; il ne prouve pas l'exécution.
- Le contrôle des blocs de code ne prouve pas les scripts absents ni les commandes autonomes non exécutées. Ne pas le présenter comme une validation d'exécution.
- Si le fichier a changé pendant la validation, ne pas réutiliser l'ancien PASS : attendre la stabilité et relancer.

### 7. Rapport de fin d'étape 1

```text
Étape : sous-ensemble (provisoire | définitif)
Cible : <chemin absolu>
Périmètre :
  inclus : <fichiers>
  différés : <fichiers | aucun>
  exclus définitivement : <catégories | aucun>
Fichiers hors périmètre : <n> | <nom, taille, sha256> | non livrés, non vérifiés, non modifiés, non supprimés
Écrit : <fichiers> | <taille> octets | sha256 <hash> | <n> lignes
Commandes autonomes : <n> exécutées | codes <...>
QA : EXIT 0 | <n> PASS / 0 FAIL / <n> WARN | Files (<n>) dont <k> hors périmètre | local references <n> checked | skill references <n> résolues
Vérification fonctionnelle : <exécutée pour les commandes autonomes | non exécutée>
Checklist : <close pour ce périmètre | n éléments en attente (différés)>
Limite : PASS statique ; les fichiers exclus ne sont ni livrés ni validés
Suite : <aucune | attendre la demande explicite pour les différés>
```

- Ne pas écrire « Skill créé » sans qualifier le périmètre.
- Ne pas écrire « validé » ; écrire « PASS statique ».
- Ne pas masquer les fichiers non créés ni les fichiers hors périmètre dans une phrase vague : les nommer dans le rapport.
- Pour un périmètre définitif, écrire « checklist close pour ce périmètre », jamais « en attente ».

## Procédure — étape 2 : ajouter les seuls fichiers différés

### 1. Confirmer la demande

- Ne démarrer que sur une demande explicite : « crée le script et les preuves », « complète le package ».
- Ne traiter que les fichiers différés. Un fichier exclu ne s'ajoute pas ici : il faut une nouvelle instruction qui change le périmètre et la déclaration.
- Relire SKILL.md et vérifier sa stabilité avant modification.
- Reprendre la liste des fichiers différés ; ne pas en ajouter silencieusement.

### 2. Créer et vérifier les ressources

- Créer uniquement les fichiers du périmètre annoncé.
- Pour un script : vérifier la syntaxe, l'exécuter sur des entrées réelles, couvrir les contrôles négatifs et vérifier les codes de sortie. Les contrôles statiques et les codes de sortie d'un validateur CLI suivent `skill-file-qa`.
- Pour une référence de preuves : dater les observations, distinguer l'observé du reconstruit et ne pas inventer une sortie.
- Supprimer les caches, fixtures et sorties de test créés pendant la session. Vérifier qu'aucun résidu ne reste dans le dossier du Skill.

### 3. Aligner le disque sur le périmètre (uniquement sur autorisation)

Si l'utilisateur demande de retirer un fichier hors périmètre déjà présent :

- Exiger le chemin exact. Ne pas déduire « nettoie le dossier » comme une autorisation de supprimer.
- Copier le fichier hors du Skill, par exemple sous `.qoder/tmp`, et vérifier que la taille et le SHA-256 sont identiques à la source.
- Supprimer uniquement ce chemin, puis le dossier s'il est vide. Ne pas toucher aux autres fichiers.
- Relancer la QA et comparer `Files (n)` avant et après. Conserver la sauvegarde sauf demande contraire.
- Si la suppression échoue ou si un autre fichier apparaît, s'arrêter et rapporter ; ne pas employer `rm -rf` pour forcer.

### 4. Convertir la déclaration

- Si un différé a été livré, mettre à jour la liste : le fichier passe de « différés » à « inclus ».
- Si le périmètre reste réduit, ne pas écrire « complet » : écrire « définitif, aligné sur le disque » et retirer l'inventaire du fichier supprimé du rapport courant.
- Enregistrer les fichiers réellement créés comme références locales. Le validateur doit les résoudre.
- Retirer les mentions « à créer » devenues fausses. La clause générique sur les fichiers non listés reste.
- Si une vérification échoue, ne pas convertir : conserver l'état précédent et rapporter l'échec.

### 5. Revalider et rapporter

- Relancer `skill-file-qa` et exiger un nouveau PASS sur le fichier stable.
- Vérifier que Files (n) correspond au nombre réel de fichiers, que local references ne signale aucune référence absente et que les références inter-Skills sont résolues.
- Rapport :

```text
Étape : 2/2 — différés ajoutés | disque aligné sur le périmètre
Fichiers : <inclus> | <tailles et sha256>
Hors périmètre : <avant | après> | sauvegarde <chemin | aucune>
Exécution : <commande> | EXIT <0/1/2> | RESULT <...>
Contrôles négatifs : <n>/<n> | codes de sortie attendus
Nettoyage : <résidus absents>
QA : EXIT 0 | Files (n) | local references n checked | skill references n résolues
Limite : <ce qui n'a pas été testé>
```

- Ne pas déclarer une publication (commit ou push) sans demande séparée.

## Écriture des références selon l'étape

| Cas | Écriture correcte | Écriture interdite |
|---|---|---|
| Fichier inclus, déjà écrit | chemin réel, vérifié par le validateur | conserver « à créer » alors que le fichier existe |
| Fichier différé | **nom (à créer)**, en gras ou texte simple | chemin relatif entre accents graves, lien Markdown ou lien file:// vers un fichier absent |
| Catégorie exclue | texte simple, par exemple « scripts d'assistance » | chemin entre accents graves, lien, mention « à créer » |
| Fichier hors périmètre présent | clause générique dans SKILL.md ; nom et empreinte dans le rapport | énumération de chemins dans SKILL.md, référence locale, mention « livré » ou « vérifié » |

Le validateur ignore les jetons qui commencent par $, / ou ~, ceux qui contiennent des chevrons, des espaces ou des astérisques, et les liens dont la cible contient ://. Ne pas s'appuyer sur ces exceptions pour écrire un chemin réel : enregistrer le chemin exact et vérifier qu'il est résolu.

## Erreurs et correctifs

| Symptôme | Cause | Correctif |
|---|---|---|
| FAIL local reference not found en étape 1 | chemin à créer écrit entre accents graves | retirer les accents graves, écrire en gras « à créer », relancer la QA |
| RESULT PASS présenté comme validation du Skill | confusion entre statique et fonctionnel | rapport « statique seulement », checklist en attente, aucun mot « validé » |
| Dossier scripts vide | volonté de « préparer » la structure | supprimer le dossier vide ; ne créer que des fichiers réels |
| Lien file:// vers un fichier absent | plan rédigé comme si les fichiers existaient | supprimer le lien, marquer le fichier « à créer » ; le validateur ne détecte pas ce lien cassé |
| Étape 2 laisse « partielle » | conversion oubliée | remplacer la déclaration, enregistrer les références, relancer la QA |
| Étape 2 crée un fichier mais local references reste à zéro | chemin réel non enregistré | enregistrer le chemin, vérifier qu'il est résolu, relancer |
| SKILL.md change pendant la rédaction | autre session ou écriture concurrente | attendre la stabilité, relire, suivre `skill-update-concurrency-safe` |
| Cible créée par une autre session pendant le préflight | course entre deux sessions : le dossier existait vide, SKILL.md apparaît quelques secondes plus tard | ne pas écraser : relire les fichiers, repasser en update minimal, échantillonner la stabilité via `skill-update-concurrency-safe` |
| Files (n) inattendu après écriture | cache, fixture ou fichier hors périmètre | inventorier, retirer uniquement les artefacts de la session, relancer |
| Script créé mais non exécuté | confusion entre « écrit » et « vérifié » | exécuter, contrôles négatifs, rapporter les codes |
| Corps incomplet mais marqué partiel | mauvaise application du modèle | compléter SKILL.md ; le partiel ne couvre que les ressources optionnelles |
| Le corps appelle encore un fichier exclu | réécriture incomplète | remplacer par une commande autonome testée, ou réduire la portée ; rescanner en littéral |
| « scripts » annoncés « plus tard » alors qu'ils sont exclus | confusion différé/exclu | écrire « exclus définitivement » ; checklist close pour ce périmètre |
| Fichier hors périmètre nommé dans SKILL.md | inventaire durable d'un artefact concurrent | clause générique ; chemins et empreintes dans le rapport seul |
| Fichier hors périmètre supprimé sans autorisation | « nettoyer » interprété comme un ordre | s'arrêter ; exiger le chemin nommé et une sauvegarde préalable |
| QA Files (n) supérieur au nombre livré | fichier hors périmètre présent | décrire la composition ; ne pas attribuer le PASS à l'exclu |
| PASS présenté comme validation de l'exclu | confusion statique/périmètre | rapport explicite : non livré, non vérifié |
| SyntaxError sur un one-liner Python | `b"\n"` ou `b"\r"` altéré par Bash | `bytes([13])` / `bytes([10])` ou here-doc ; retester |
| Erreur de parsing d'une expression de recherche | point échappé dans une classe de caractères | recherche littérale `grep -F` / `rg -F` |
| « aucun fichier hors périmètre » faux | dossier non listé | lister avant d'écrire ; sinon ne rien affirmer |

## Checklist

### Sous-ensemble (étape 1)

- [ ] Trois listes écrites : inclus, différés, exclus définitivement.
- [ ] Aucune phase 2 promise pour un exclu.
- [ ] Cible préflightée ; create/update décidé ; aucun écrasement.
- [ ] Dépendances des exclus réécrites en commandes autonomes et exécutées en lecture seule.
- [ ] Aucune mention résiduelle d'un exclu après recherche littérale.
- [ ] Seuls les fichiers inclus écrits ; aucun dossier vide ni placeholder.
- [ ] Déclaration après le H1 : inclus, différés, exclus, clause générique sur les fichiers non listés.
- [ ] Aucun chemin hors périmètre dans SKILL.md ; aucun chemin à créer entre accents graves.
- [ ] Listing réel du dossier avant toute affirmation sur les fichiers hors périmètre.
- [ ] Fichiers hors périmètre ni modifiés ni supprimés ; inventaire avec taille et SHA-256 dans le rapport.
- [ ] `skill-file-qa` exécuté ; exit 0, PASS/FAIL/WARN, empreintes et composition de Files (n) lus.
- [ ] Rapport : périmètre, fichiers hors périmètre, commandes exécutées, statique seulement.
- [ ] Checklist close si le périmètre est définitif ; en attente seulement pour les différés.
- [ ] Aucune revendication de validation fonctionnelle ou de validation d'un exclu.
- [ ] Aucun commit ni push.

### Étape 2 — différés (si applicable)

- [ ] Demande explicite de l'utilisateur, limitée aux fichiers différés.
- [ ] Fichiers annoncés créés ; aucun fichier exclu ajouté.
- [ ] Script syntaxiquement valide et exécuté sur des entrées réelles.
- [ ] Contrôles négatifs exécutés ; codes de sortie exacts.
- [ ] Résidus et caches absents.
- [ ] Déclaration mise à jour ; mentions « à créer » retirées ; clause générique conservée.
- [ ] Références locales réelles enregistrées et résolues.
- [ ] `skill-file-qa` relancé ; Files (n) et local references cohérents.
- [ ] Rapport final distinguant exécuté, statique et non testé.
- [ ] Aucun commit ni push sans demande séparée.

### Suppression autorisée d'un fichier hors périmètre (si applicable)

- [ ] Chemin exact nommé par l'utilisateur.
- [ ] Sauvegarde hors du Skill ; taille et SHA-256 identiques.
- [ ] Seul le chemin nommé et le dossier vide supprimés ; autres fichiers intacts.
- [ ] QA relancée ; `Files (n-1)` ; rapport avant/après.
- [ ] Sauvegarde conservée sauf demande contraire.

## Ressources

Aucun script ni référence externe : ce Skill est volontairement un fichier unique. Les contrôles statiques sont délégués à `skill-file-qa`, la comparaison du manifeste à `skill-package-integrity-audit`, la stabilité d'écriture à `skill-update-concurrency-safe`, la reprise d'un dossier créé par une autre session à `adopt-concurrent-duplicate-skill`, l'attente d'un écrivain actif à `audit-skill-during-live-creation` et l'audit des preuves de session à `audit-session-evidence`.

## Provenance

- Session source : b8448766-bcf0-40dc-9ea5-9622f129877e, titre « 创建隔离发布测试技能 », revision 87, hasMoreBefore=false.
- Tour 8b264ed5 (2026-10-26T11:27:17Z) : l'utilisateur écrit « 先只更新 SKILL.md，脚本和证据稍后 ». L'assistant livre uniquement SKILL.md avec une section « État de livraison » partielle. `skill-file-qa` rend RESULT PASS, 9 PASS / 0 FAIL / 0 WARN, Files (1), description 913 caractères, corps 167 lignes, local references 0 checked et 3 références inter-Skills résolues. Le fichier fait 12 601 octets, sha256 3d6a071194d42790805af79ab235ccf59a72ae461ad95ca2caaab5f04eb9f953. Le rapport indique l'absence de preuve fonctionnelle et laisse la checklist en attente.
- Tour 1e9c48a1 (2026-10-26T11:29:49Z) : l'utilisateur demande « 创建测试脚本和证据文件 ». L'assistant crée le script et la référence, exécute le harnais, convertit la déclaration en livraison complète et relance `skill-file-qa` avec Files (3) et RESULT PASS. Le SKILL.md final fait 14 416 octets, sha256 264d6339aef8118442fb1be81b9a70710194fbb011584ddfb287ec1785248dbb ; le script fait 26 083 octets, sha256 62c6bdf03cb8b98bec88d7aec6f5a89325d26b5172737ce37727d282738c9b9f ; la preuve fait 10 170 octets, sha256 713508787f0dccfca57aef2f5638c1f907cd1ca739af2b1be5f61e2d9255ce5e.
- Aucune correction utilisateur dans cette source : il s'agit de deux ajustements de périmètre. Le plan initial de la session utilisait des liens file:// vers des fichiers inexistants ; ce Skill retient la règle corrigée : statut en gras ou texte simple, puis références réelles à l'étape 2.
- Contrôle du 2026-10-26 (session de mise à jour) : les chiffres et empreintes ci-dessus ont été relus dans la transcription source, et la QA a été reproduite sur l'état reçu du fichier (17 792 octets, sha256 99b0b789…55d6, Files (1), 9 PASS / 0 FAIL / 0 WARN, description 737 caractères, corps 232 lignes, local references 0 checked, 4 références inter-Skills résolues). Cet état avait été écrit par une session concurrente pendant la préparation ; il est resté stable avant les trois précisions ajoutées ici, puis la QA a été relancée.
- Session source complémentaire : 3677d3d4-c450-45c6-b00e-4f16329cce18, titre « 创建 LF 结尾锁定技能 », revision 18, hasMoreBefore=false, 2026-10-26. À la lecture, runtimeState=running et le tour ba84c0c0 était encore streaming : la demande de commit n'a pas de résultat confirmé dans l'instantané et n'est pas rapportée comme acquise.
- Tour ee7a741b (2026-10-26T12:08:58Z) : après un plan à trois fichiers, l'utilisateur écrit « 先只写文档和参考文件，不加脚本 ». Le dossier cible avait déjà été créé par une session concurrente avec un script. L'assistant a pris le disque comme base, modifié seulement SKILL.md et la référence, remplacé les appels au script par des commandes autonomes (comptage d'octets par fichier, sonde checkout-index) et déclaré les scripts hors périmètre sans les supprimer. QA : Files (3), 9 PASS / 0 FAIL / 0 WARN, description 475 caractères, corps 237 lignes, local references 1 checked, 3 références inter-Skills ; manifeste PASS 3/3 avec QA Files (3): MATCH. Empreintes : SKILL.md 14 301 B c1741e50…, référence 7 927 B 3162ae88…, script inchangé 13 244 B 33d6ca2c…. A/B hors du dossier : CR=2 sans attribut, CR=0 avec la règle info, info prioritaire sur la racine (eol: lf).
- Tour 26e1e81d (2026-10-26T12:22:54Z) : « 先备份再删除脚本 ». Sauvegarde sous .qoder/tmp/lock-lf-script-backup-20261026-132345 avec SHA-256 identique, suppression du script et du dossier scripts vide, QA Files (2) PASS, manifeste 2/2 PASS avec QA Files (2): MATCH ; les empreintes des deux fichiers livrés sont inchangées.
- Tour ba84c0c0 (2026-10-26T12:25:50Z) : « 提交这些变更 ». La cible n'était pas un dépôt Git ; l'utilisateur a répondu « 初始化并提交（推荐） ». L'instantané s'arrête pendant le streaming : aucun hash de commit n'est cité.
- Aucune correction de méthode dans cette source : deux ajustements de périmètre et une autorisation explicite de suppression. Le fichier hors périmètre n'a été supprimé qu'après cette autorisation et n'a jamais été compté comme livré ou vérifié.
- Contrôle du 2026-10-26 (session de mise à jour) : avant écriture, la cible était stable sur trois échantillons (18 903 octets, sha256 2e0a4853…, mtime inchangé), sans dossier vide, et les sessions identifiées comme liées à ce Skill étaient cold. QA reproduite : Files (1), 9 PASS / 0 FAIL / 0 WARN, description 737 caractères, corps 235 lignes, local references 0 checked, 4 références inter-Skills résolues. Aucun autre Skill n'a été modifié.
- Les chiffres et empreintes ci-dessus sont des preuves historiques de la session source ; ils ne décrivent pas l'état actuel de ce Skill.
