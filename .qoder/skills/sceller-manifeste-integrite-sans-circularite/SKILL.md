---
name: sceller-manifeste-integrite-sans-circularite
description: "Sceller un manifeste d'intégrité SHA-256/Merkle sans circularité : cartographier les fichiers scellés et les artefacts dérivés qui affichent la racine (pages générées, résumé, API), exclure ces derniers du scellement, écrire d'abord les fichiers couverts (tests), régénérer après tout ajout, puis vérifier que la racine recalculée concorde entre manifeste, résumé et pages et qu'aucun fichier ajouté n'échappe au manifeste. Utiliser quand un manifeste référence un fichier avant sa création, quand une page affiche la racine Merkle qu'elle est censée prouver, quand la vérification répond OK alors que des fichiers manquent, ou quand deux générations successives donnent des racines différentes. 中文触发：封存完整性清单、根被页面嵌入、循环哈希、清单漏文件、重签后根不一致。English: seal an integrity manifest without circularity, Merkle root embedded in generated pages, stale manifest, extra-file detection, idempotent resealing."
---

# Sceller un manifeste d'intégrité sans circularité

## Quand utiliser

- Un manifeste SHA-256 ou Merkle couvre un ensemble de fichiers, et certains artefacts générés affichent sa racine.
- Un glob de scellement désigne un fichier qui n'existe pas encore (test, page, export).
- La vérification répond OK alors que des fichiers couverts ont été ajoutés après le scellement.
- Deux générations successives, sans modification entre elles, produisent des racines différentes.
- L'utilisateur veut une preuve d'intégrité reproductible, pas une preuve d'antériorité légale.

## Ne pas utiliser

| Besoin réel | Skill à utiliser |
|---|---|
| Publier un dossier public caviardé avec manifeste auto-exclu et gel après publication | `publier-preuves-anteriorite-caviardees` |
| Valider la structure, les références et les empreintes d'un paquet Skill | `skill-file-qa` |
| Ancrer la racine hors ligne (OpenTimestamps, DOI, dépôt) | Hors périmètre : le manifeste seul ne date rien d'opposable |

## Vocabulaire et invariant

- **Scellé** : fichier haché dans le manifeste. Il ne doit dépendre d'aucun artefact dérivé.
- **Dérivé** : artefact produit après ou à partir du scellement (pages, résumé, exports, rendu Markdown).
- **Porteur de racine** : tout fichier qui contient la racine en clair, y compris le manifeste lui-même.

Invariant : la racine `R = H(contenu scellé)`. Si un fichier scellé contient `R`, alors écrire `R` change ce fichier, donc change `R`. Il n'existe pas de point fixe exploitable ; réessayer en boucle ne converge pas. La seule solution stable est d'**exclure tout porteur de racine de l'ensemble scellé**, puis de sceller ses entrées et son générateur.

Corollaire : l'ordre compte. On écrit les sources, on génère les dérivés, on scelle une fois, puis on vérifie. Un dérivé scellé après coup réintroduit la boucle.

## Étape 1 — Cartographier trois ensembles

Repérer d'abord les porteurs de racine, avant de choisir les globs :

```bash
grep -rIl "racine_merkle\|merkle_root\|integrity_root" <dossiers-publics>
grep -rn "construire_manifeste\|write_manifest\|seal" <dossiers-sources>
```

Classer chaque fichier :

| Artefact | Sceller ? | Raison |
|---|---|---|
| Code source, contrats, tests, actes, documentation, pages statiques sans racine | Oui | Détermine le contenu prouvé |
| Générateur de pages, module de scellement | Oui | Détermine la racine et les dérivés |
| Manifeste JSON et son rendu Markdown | Non | Il est la racine ; il s'exclut lui-même |
| Résumé JSON, exports d'API, sitemap qui citent la racine | Non | Contiennent la racine |
| Pages générées affichant la racine | Non | Contiennent la racine |
| Dossiers de sortie, caches, builds, secrets | Non | Bruit, données sensibles ou artefacts recalculés |

## Étape 2 — Trancher la circularité

1. Si un porteur de racine doit être publié, le publier **à côté** du manifeste et vérifier qu'il affiche la même racine. Ne jamais le sceller.
2. Remplacer tout glob trop large du type `*.html` par une liste explicite de pages stables qui n'affichent pas la racine.
3. Sceller à la place le générateur et les données d'entrée : le tiers peut recalculer la page et donc la racine.
4. Ne jamais « hacher la page, y injecter la racine, re-hacher » : le second hash invalide le premier.

## Étape 3 — Fixer l'ensemble scellé et l'ordre

- Glob explicites, tri stable par chemin en minuscules, exclusions de secrets, caches, sorties et copies.
- Lister le fichier de test même avant sa création, mais vérifier qu'il existe au moment du scellement final : un glob ignore silencieusement un fichier absent.
- Séquence imposée :
  1. écrire et corriger tous les fichiers couverts, tests compris ;
  2. générer les dérivés (pages, résumé) ;
  3. sceller une seule fois, après la dernière écriture source ;
  4. vérifier ;
  5. régénérer une seconde fois et comparer racine et compteur.

## Étape 4 — Sceller

- Feuille : SHA-256 des octets du fichier. Racine : trier les feuilles, hacher les paires, dupliquer la dernière feuille si le niveau est impair.
- Écrire le manifeste et son rendu hors de l'ensemble scellé, dans un dossier de sortie exclu.
- `mtime` est informatif seulement : il est forgeable. Ne pas le présenter comme une date opposable.

## Étape 5 — Vérifier quatre choses, pas une

Utiliser le script fourni, qui ajoute le contrôle des fichiers ajoutés. Lancer depuis la racine du périmètre scellé, avec des chemins relatifs :

```bash
cd <racine-projet>
SK=<dossier-skill>
py -3 -B "$SK/scripts/verifier_manifeste_sans_circularite.py" \
  --manifest resultats/.../manifeste.json --racine . \
  --glob "contracts/*.sol" --glob "tests/*.py" \
  --porteur-de-racine resultats/.../manifeste.json \
  --porteur-de-racine resultats/.../MANIFESTE.md \
  --porteur-de-racine resultats/.../resume.json \
  --porteur-de-racine web/.../page-qui-affiche-la-racine.html
```

Remplacer `<racine-projet>` par la racine du périmètre scellé, `<dossier-skill>` par le dossier de ce Skill et chaque `...` par le chemin réel ; les valeurs effectivement utilisées figurent dans le cas vérifié.

Trois gestes non facultatifs :

1. **Dériver les `--glob` de la constante du module de scellement, ne pas les retaper.** Reprendre la liste de globs du module de scellement du projet (sur AL-Mizan : la constante `GLOBS_SELECTIONNES` du module `manifeste_anteriorite.py`, 16 motifs) et en émettre un `--glob` par entrée. Une liste retapée peut omettre un motif : les fichiers ajoutés sous ce motif échappent au contrôle `EXTRA` et la vérification répond `OK`.
2. **Passer aussi le manifeste et son rendu Markdown en `--porteur-de-racine`.** Le manifeste JSON n'est pas scellé mais il affiche la racine : déclaré porteur, il est contrôlé comme les pages et le résumé ; omis, le fichier qui porte la preuve échappe au contrôle `MATCH`/`PORTEUR_SCELLE`.
3. **`py -3 -B`** : le vérificateur n'écrit rien, et `-B` garantit qu'aucun `.pyc` n'apparaît dans l'arborescence scellée.

Contrôles exigés :

1. **Empreintes** : chaque fichier listé existe et son SHA-256 correspond.
2. **Racine** : la racine recalculée est égale à la racine déclarée.
3. **Complétude** : aucun fichier couvert par les globs ne manque (`EXTRA`), aucun fichier listé n'a disparu (`ABSENT`).
4. **Cohérence et circularité** : chaque porteur affiche la racine déclarée, et aucun porteur n'est scellé (`PORTEUR_SCELLE`).

Sortie attendue sur un ensemble sain : `FILES n`, `RACINE_CALCULEE` égale à `RACINE_MANIFESTE`, chaque porteur `MATCH`, puis `RESULT OK` et code 0.

Prouver ensuite que la vérification n'a rien écrit :

- SHA-256 du manifeste relevé avant le lancement, comparé après : identique.
- Aucun `.pyc` nouveau : `find . -name "*.pyc" -newermt "<instant du lancement>"` vide.
- `git status --porcelain` vide **uniquement si** la racine est un dépôt Git. Hors dépôt, `git status` échoue (code 128) et `2>/dev/null` rend une sortie vide qui ressemble à un état propre : trancher d'abord avec `git rev-parse --is-inside-work-tree`, sinon s'abstenir et s'appuyer sur l'empreinte du manifeste.

Un vérificateur qui n'itère que les fichiers listés répond `OK` sur un manifeste périmé : il ne voit jamais les fichiers ajoutés. Le contrôle `EXTRA` est indispensable.

## Étape 6 — Écrire des tests qui ne mentent pas

- Vérifier le manifeste **stocké**, pas un manifeste régénéré dans le test : régénérer puis vérifier masque toute péremption.
- Asserter le format de la racine, la présence du fichier de test dans la liste, et l'absence des porteurs de racine.
- Asserter les deux générations successives : même compteur et même racine.
- Tester le vérificateur lui-même hors du dépôt : fichier modifié, fichier ajouté, porteur scellé, racine divergente, fichier absent.
- Ne pas écrire de fichier de test dans le dépôt pendant la vérification : une fixture laissée derrière devient un `EXTRA` au prochain scellement.

## Étape 7 — Après tout ajout

- Tout fichier couvert ajouté ou modifié impose une régénération par le générateur, jamais une édition manuelle du manifeste.
- Régénérer deux fois de suite sans modification : racine et compteur doivent être identiques.
- Si la racine bouge entre deux passages, un artefact dérivé est encore scellé, ou un fichier change à chaque génération (horodatage, tri non déterministe, ordre de dictionnaire).

## Pièges

| Piège | Conséquence | Parade | Cas vérifié |
|---|---|---|---|
| Glob `web_cloud/*.html` incluant les pages qui affichent la racine | La racine ne se stabilise jamais | Liste explicite des pages stables | Trois pages retirées 24 s après la première écriture |
| Manifeste listant un test avant sa création | Glob silencieux, compteur incomplet | Écrire le test puis resceller ; contrôler le compteur | 149 fichiers après rescellement |
| Vérificateur qui ne parcourt que la liste | `OK` malgré des fichiers ajoutés | Contrôle `EXTRA` par globs | Ajouté par le script fourni |
| Test qui régénère avant de vérifier | Péremption invisible | Vérifier le manifeste stocké | Constat de lecture du code, pas un échec reproduit |
| Deux générations, deux racines | Dérivé scellé ou sortie non déterministe | Exclure le porteur, trier les chemins | Racines 18ef… puis 5705… puis 9e47… pendant la construction |
| `mtime` présenté comme preuve de date | Surpromesse | Ancrer la racine hors ligne | Non opposable |
| `git status --porcelain 2>/dev/null` hors dépôt Git | Sortie vide lue comme « aucune écriture », alors que git échoue en 128 | `git rev-parse --is-inside-work-tree` d'abord ; sinon empreinte du manifeste + `find` des `.pyc` | `ASTRO-Q°ODE_SYSTEME` n'est pas un dépôt : rc 128 mesuré le 2026-10-28 |
| Édition manuelle du manifeste | Racine incohérente | Toujours régénérer | — |
| Fichier absent jamais signalé | Manifeste incomplet présenté comme complet | `ABSENT` + compteur | — |

## Modèle de rapport

| Section | Contenu exigé |
|---|---|
| Scellé | Nombre de fichiers, racine, horodatage UTC, chemin du manifeste |
| Dérivé | Chemins des porteurs et verdict de concordance de racine |
| Contrôles | Empreintes, racine recalculée, `EXTRA`/`ABSENT`, `PORTEUR_SCELLE` |
| Idempotence | Deux générations : compteur et racine identiques |
| Limites | `mtime` non opposable, ancrage externe non effectué, état de la session source |

## Ressources

- `scripts/verifier_manifeste_sans_circularite.py` — contrôles 1 à 4 ; sortie ASCII, codes 0 (OK), 1 (FAIL), 2 (entrée inutilisable).
- `references/cas-oeuvre-universelle-2026-10-27.md` — cas réel : chronologie, racines successives, 149 fichiers, empreintes et limites.
- Après écriture du paquet, valider avec `skill-file-qa`.
