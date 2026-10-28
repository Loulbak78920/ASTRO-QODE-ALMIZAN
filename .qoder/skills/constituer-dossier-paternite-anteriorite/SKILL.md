---
name: constituer-dossier-paternite-anteriorite
description: "Constituer un dossier de paternité et d'antériorité opposable pour des œuvres numériques : inventaire en lecture seule, comparaison du bytecode Solidity on-chain après masquage des valeurs immuables, modèle de qualification en logique ternaire de Kleene, scellement SHA-256/Merkle non circulaire, ancrages tiers (dépôt public, blockchain, DOI, IPFS) et grille juridique française. Utiliser quand on demande de prouver qu'on est l'auteur, de dater une œuvre avant un dépôt ou un déploiement, de vérifier qu'un code on-chain correspond à une source, de préparer une mesure d'instruction CPC 145 ou de refuser un référé-provision faute de défendeur. 作者身份取证、作品在先性证明、链上合约与源码比对、证据封存、法国知识产权诉讼前置评估、区块链时间戳与第三方锚点；authorship evidence, on-chain bytecode verification, provenance dossier, evidence sealing, French IP legal grid, prior-art anchoring."
---

# Constituer un dossier de paternité et d'antériorité

Produire un corpus de preuves technique et juridiquement honnête : ce qui est établi,
ce qui reste indéterminé, et ce qu'il est possible de demander à un juge aujourd'hui.

## 1. Quand utiliser ce Skill

- « Prouver que je suis l'auteur de ce code / de ce texte avant telle date. »
- « Ce contrat déployé correspond-il à ma source ? »
- « Constituer un dossier de preuves avant un litige. »
- « Puis-je demander une provision, un référé, une saisie-contrefaçon ? »

Ne pas l'utiliser pour rédiger une assignation, pour qualifier un tiers de contrefacteur
sans pièce, ni pour produire une preuve qui n'existe pas.

## 2. Arborescence cible

```text
<dossier>/
  DOSSIER/     documents juridiques et récit
  PREUVES/     mesures : inventaire, vérification, ancrages, instantanés
  DONNEES/     modèle formel éditable (JSON)
  SCEAU/       manifeste Merkle + sommes SHA-256
  OUTILS/      scripts et lanceur
```

Le corpus source est **en lecture seule**. Toute sortie va dans `PREUVES/`, `DONNEES/`,
`DOSSIER/` ou `SCEAU/`. Ne jamais écrire dans l'arborescence inventoriée.

`SCEAU/` n'est pas produit par un script de ce Skill : la théorie et l'outil de
scellement sont délégués à `sceller-manifeste-integrite-sans-circularite`, qui doit
être lu avant l'étape 8.

## 3. Invariants non négociables

1. **Aucune preuve inventée.** Un fait non observé est `INDETERMINE`, jamais `VRAI`.
2. **Aucun tiers nommé** comme auteur d'une atteinte sans pièce vérifiable : constat,
   capture datée, reproduction localisée, similitude mesurée.
3. **Deux horloges distinctes.** `created_at`/`pushed_at` d'un serveur et horodatage
   de bloc sont des dates serveur ; `commit.committer.date` est déclarée par le client.
   Ne jamais présenter une date client comme une date certaine.
4. **Un hash local ne date rien.** Il prouve l'intégrité, pas l'antériorité. Seul un
   ancrage externe (serveur tiers, chaîne, registrar) date.
5. **Comparaison brute du bytecode interdite.** Masquer les valeurs immuables avant de
   conclure ; nommer `CORRESPONDANCE_FORTE` quand seule l'auxdata diffère.
6. **Sceller après avoir tout écrit**, en excluant `SCEAU/` et les caches, sinon
   circularité.
7. **Pas de défendeur identifié → pas de référé-provision.** La mesure 145 reste ouverte.
8. **Les documents produits ne sont pas une consultation juridique.** Le dire dans le
   dossier et dans la réponse.
9. **Anonymiser par défaut** : pas de nom, date de naissance, adresse, clé privée,
   adresse de portefeuille, adresse de contrat ni DOI dans les modèles réutilisables.
10. **Regénérer puis resceller**, jamais l'inverse. Un ajout après scellement est une
    divergence, même si les fichiers scellés sont intacts.

## 4. Chaîne en huit étapes et ses gates

| # | Étape | Sortie | Gate |
|---|---|---|---|
| 1 | Inventorier les pièces (lecture seule, SHA-256, taille, mtime) | PREUVES/inventaire.json | 0 pièce `MANQUANT`, 0 `DIVERGENCE` non expliquée |
| 2 | Vérifier le contrat (recompilation + on-chain) | PREUVES/verification_contrat.json | code exécutable identique ou `CORRESPONDANCE_FORTE` |
| 3 | Vérifier les ancrages publics (GitHub, DOI, IPFS, site) | PREUVES/ancrages_publics.json | horloges serveur consignées |
| 4 | Vérifier le dépôt public fichier par fichier | PREUVES/depot_public.json | publication antérieure au déploiement |
| 5 | Renseigner le modèle ternaire | DONNEES/modele_paternite.json | aucune règle bloquante vide |
| 6 | Évaluer le modèle et les gates | PREUVES/evaluation.json | `--exiger E2` = VRAI |
| 7 | Générer les documents | `DOSSIER/*.md` | chaque chiffre renvoie à une preuve |
| 8 | Sceller puis vérifier (délégué) | `SCEAU/` | intégrité confirmée après génération |

Ordre imposé : les documents sont générés **après** les mesures, et scellés **après**
génération. Une valeur recopiée à la main dans un document doit exister dans un JSON
de `PREUVES/`.

### Étape 1 — inventaire

```bat
py -3 scripts\inventaire_preuves.py --source <racine-source> ^
  --pieces DONNEES\pieces.json --manifest <manifeste.json> ^
  --out-json PREUVES\inventaire.json --out-md PREUVES\RAPPORT_INTEGRITE.md
```

Le script recalcule SHA-256, taille et mtime sans jamais écrire dans la racine
source. Il confronte chaque pièce aux empreintes déclarées dans `pieces.json` et
dans les manifestes passés en `--manifest`.

Chaque pièce porte : identifiant, chemin, SHA-256, taille, mtime, date déclarée si elle
existe. Classer en `CONCORDE` (déclaré = mesuré), `DIVERGENCE` (déclaré ≠ mesuré),
`NON_DECLARE` (fichier sans déclaration), `MANQUANT` (déclaré sans fichier) et
`NON_VERIFIABLE` (chemin hors racine ou empreinte déclarée illisible).
Détail du schéma et des anomalies dans `references/inventaire-et-dossier.md`.

### Étape 2 — contrat

```bat
py -3 scripts\comparer_bytecode.py --mode onchain ^
  --source <source.sol> --rpc <url-json-rpc> --tx <hash-de-deploiement> ^
  --solc solc@0.8.37 --artifact <artifact.json> ^
  --immutable <adresse-1> --immutable <adresse-2> --out PREUVES\verification_contrat.json
```

Mode hors ligne, sans réseau :

```bat
py -3 scripts\comparer_bytecode.py --mode fichiers ^
  --actuel <runtime-deploye.hex> --compile <runtime-recompile.hex> ^
  --immutable <adresse-1>
```

### Étape 3-4 — ancrages

Les ancrages publics et le dépôt GitHub fichier par fichier sont couverts par
`ancrer-anteriorite-depot-github-public` : déléguer plutôt que réimplémenter. Ce Skill
consomme ses JSON et n'exige que trois champs : `created_at` serveur, date de commit
par fichier, `sha256` distant.

### Étape 5-6 — modèle ternaire

```bat
py -3 scripts\evaluer_modele.py --modele DONNEES\modele_paternite.json ^
  --out-json PREUVES\evaluation.json --out-md PREUVES\evaluation.md --exiger E2
```

Codes de retour : `0` évalué et gates VRAI, `1` erreur d'évaluation ou gate non
remplie, `2` modèle absent ou schéma invalide. Ne jamais convertir un `INDETERMINE`
en `VRAI` pour faire passer un gate : changer la pièce, pas la valeur. Tables de
vérité et schéma : `references/modele-ternaire.md`.

### Étape 8 — scellement (délégué)

Aucun script de scellement n'est maintenu ici : exécuter la procédure de
`sceller-manifeste-integrite-sans-circularite` sur `<dossier>`, en excluant `SCEAU/`
et les caches, puis relancer sa vérification. Les deux règles restent propres à ce
Skill : sceller **après** génération des documents, et traiter tout fichier ajouté
après scellement comme une divergence, même si les fichiers scellés sont intacts.

Ne pas recopier ni réimplémenter ici le format du manifeste : lire la Skill déléguée
et suivre son contrat de sortie.

## 5. Contrat des trois scripts

| Script | Entrées | Sortie machine | Codes |
|---|---|---|---|
| `scripts/inventaire_preuves.py` | `--source`, `--pieces`, `--manifest`, `--manifest-cle`, `--out-json`, `--out-md` | `CONCORDE=… DIVERGENCE=… NON_DECLARE=… MANQUANT=… NON_VERIFIABLE=…`, puis `RESULT OK\|FAIL` | 0 aucune contradiction, 1 divergence/manquant/non vérifiable, 2 entrée |
| `scripts/comparer_bytecode.py` | `--mode`, `--source` ou `--actuel`/`--compile`, `--rpc`, `--tx`, `--solc`, `--artifact`, `--immutable`, `--out` | JSON avec `verdict`, `comparaison_code_executable` | 0 conforme, 1 divergence, 2 entrée/réseau, 3 compilation |
| `scripts/evaluer_modele.py` | `--modele`, `--exiger`, `--out-json`, `--out-md` | `REGLES:` puis `RESULTATS:` puis `RESULTAT:` | 0 OK, 1 gate/erreur, 2 schéma |

Les trois scripts sont en bibliothèque standard Python uniquement. Sous Windows,
appeler `py -3`, jamais `python` nu (stub Microsoft Store). Poser
`PYTHONIOENCODING=utf-8` et `PYTHONUTF8=1` avant un lanceur, et garder les statuts
machine en ASCII.

## 6. Décision juridique immédiate

| Situation constatée | Ce qui est possible | Ce qui ne l'est pas |
|---|---|---|
| Paternité établie, aucun exploitant identifié | mesure d'instruction in futurum (CPC 145) | référé-provision, saisie-contrefaçon |
| Exploitant identifié + reproduction documentée | mise en demeure, puis action en contrefaçon | qualification pénale sans intention |
| Contrat 50/50 non signé | modèle de régularisation | créance certaine, provision |
| Archive altérée après scellement | conservation et constat de preuves | urgence de droit au fond |
| Aucun préjudice chiffré | constat, expertise | dommages-intérêts chiffrés |

Règle dure : sans défendeur déterminé et sans obligation non sérieusement contestable,
le référé-provision est irrecevable. La grille complète, les bases légales et la liste
des assertions interdites sont dans `references/grille-juridique-fr.md`.

## 7. Délégations

Ce Skill ne duplique pas les suivants :

- `sceller-manifeste-integrite-sans-circularite` — scellement SHA-256/Merkle, exclusions
  et vérification. Ce Skill ne fournit plus d'outil de scellement : il délègue l'étape 8
  et n'en garde que les deux règles d'ordre (sceller après génération, détecter les ajouts).
- `publier-preuves-anteriorite-caviardees` — publication caviardée des preuves.
- `ancrer-anteriorite-depot-github-public` — ancrage commit par commit sur dépôt public.
- `compiler-auditer-contrats-solidity-pragma-exact` — compilation à pragma exact.
- `requalifier-preuves-calcul-fini` — requalification honnête d'une « preuve » calculatoire.

En cas de recouvrement, lire la Skill adjacente et déléguer la partie qu'elle couvre
mieux ; ne pas recopier son contenu ici.

## 8. Pièges à ne pas répéter

Résumé ; chaque entrée est détaillée avec sa preuve dans `references/pieges-verifies.md`.

- `solcjs` n'accepte pas `--bin-runtime` : compiler en `--standard-json`.
- Le reçu de transaction ne garantit pas `blockTimestamp` : repli sur le bloc, et
  consigner que le repli a servi.
- Bytecode brut ≈ 20 % de préfixe commun sur un contrat identique : masquer les
  immuables avant de comparer.
- GitHub sans jeton : 404 = privé **ou** inexistant, jamais « absent ».
- Zenodo : 200 enregistré, 410 supprimé (pierre tombale datée), 404 non enregistré.
- Un portail IPFS muet ne prouve pas l'absence de contenu.
- Un manifeste daté avant le mtime de ses fichiers a été complété après coup.

## 9. Vérification finale avant de livrer

1. `py_compile` sur les trois scripts.
2. Fixture hors du Skill pour l'inventaire : pièce concordante (0), un octet muté (1),
   pièce manquante (1), chemin hors racine (1), manifeste absent (2).
3. `--exiger` sur une règle VRAI (0) et sur une règle FAUX (1).
4. Comparaison `--mode fichiers` avec deux adresses immuables : brut différent, code
   exécutable identique, verdict `CORRESPONDANCE_FORTE` (0) ; un octet changé dans le
   code donne `DIVERGENCE` (1).
5. Chaque chiffre d'un document existe dans un JSON de `PREUVES/`.
6. Le dossier scellé ne contient aucun `__pycache__`, aucun brouillon, aucun secret.
7. Énoncer explicitement ce qui reste non prouvé : originalité, copie par un tiers,
   intention dolosive, préjudice chiffré.

Le cas de référence anonymisé, avec les valeurs exactes attendues, est dans
`references/cas-mizan-2026-10-28.md`.

## 10. Limites

Un dossier de ce type établit une **chaîne de cohérence** : pièces, identité, dates,
intégrité, antériorité. Il ne remplace ni une expertise d'originalité, ni un constat
d'huissier, ni une décision de justice. La qualification finale appartient au juge.
