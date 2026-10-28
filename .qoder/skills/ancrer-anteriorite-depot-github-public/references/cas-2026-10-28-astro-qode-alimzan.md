# Cas vérifié : premier commit publié de fichiers sur GitHub

## Source de l'observation

- Session Qoder `634ab589-ab76-46f9-b4c7-1e6d6767200e`, tour `c5cfb450-068e-4a27-aea3-ff70e3f38566` (2026-10-28).
- Journal : `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\634ab589-ab76-46f9-b4c7-1e6d6767200e.jsonl`.
- Version citée : 918 lignes, 2 109 229 octets, SHA-256 `11a5e9d61b00700574cbb561a1d2a6369dd768a123a8dc5edf43d7a3c48b8bbb`, mtime `2026-10-28T11:59:21Z` (UTC).
- `read_chat_session` a renvoyé un message assistant de synthèse (`messageStream=thinking`) et non les sorties brutes. Les preuves ci-dessous viennent des couples `tool_use` / `tool_result` du journal, appariés par identifiant d'appel. Les numéros de ligne ne sont valables que pour le SHA ci-dessus : le fichier de session peut s'allonger après coup.

## Dépôt observé

| Champ | Valeur | Horloge |
|---|---|---|
| Dépôt | `Loulbak78920/ASTRO-QODE-ALMIZAN` | — |
| Visibilité | `public` | serveur GitHub |
| `created_at` | `2026-10-22T07:04:32Z` | serveur GitHub |
| Premier commit de l'historique | `e6bc5fd0cbf8290b4eb2481c9f388096d97b528d` | API |
| Date du premier commit | `2026-10-22T06:48:48Z` | client Git |
| Nombre total de commits | 213 | API |

La date du premier commit précède de 15 min 44 s la création du dépôt par GitHub. C'est la démonstration la plus directe que la date de commit est déclarative et ne peut pas être présentée comme un horodatage indépendant.

## Faux négatif initial : 0 fichier sur 5

La première version du script prenait l'arbre du commit le plus ancien (`e6bc5fd0…`, 116 entrées) pour l'inventaire publié. Sortie exacte (ligne 461) :

```text
Depot public: 213 commits, cree 2026-10-22T07:04:32Z, 0/5 fichiers suivis publies, 0 identiques. Coherence: PARTIEL
```

Cause : les cinq fichiers suivis ont été ajoutés dans des commits postérieurs. L'arbre du premier commit ne contient que `CITATION.cff`, `NOTICE.txt`, `.zenodo.json`, l'acte d'identité, le contrat 50/50 et les dossiers Zenodo ; ni le contrat Solidity, ni le livre blanc, ni la calculatrice.

Correction : interroger `commits?path=` pour chaque fichier et prendre le **dernier élément** de la liste. Résultat par chemin (ligne 469) :

```text
contracts/AmalMizanSynchronMznContract_VERIF_BASESCAN.sol -> 1 commits, plus ancien 39e8c4e3873d 2026-10-22T14:38:27Z
contracts/AmalMizanSynchronMznContract.sol -> 4 commits, plus ancien afc9b14cc74b 2026-10-22T07:35:26Z
LIVRE_BLANC_ALMIZAN_ASTRO_QODE_MZN_WHITEPAPER.md -> 1 commits, plus ancien 96da10be3b3e 2026-10-22T08:37:12Z
calculatrice_mizan.py -> 1 commits, plus ancien 6cdebf1e7d92 2026-10-25T18:31:14Z
test_calculatrice_mizan.py -> 1 commits, plus ancien 6cdebf1e7d92 2026-10-25T18:31:14Z
```

## Résultat après correction

Sortie exacte de la version corrigée (ligne 483) :

```text
Depot public: 213 commits, cree 2026-10-22T07:04:32Z. 10/10 fichiers publies, 3 identiques a la copie locale. Contrat publie avant deploiement: True. Verdict: ANCRAGE_PUBLIC_ETABLI
```

Le passage de 5 à 10 fichiers suivis explique `10/10` : la seconde version suit aussi `CITATION.cff`, `NOTICE.txt`, `.zenodo.json`, l'acte d'identité et le contrat 50/50, publiés au premier commit.

Détail par fichier (ligne 488 ; empreintes abrégées à 12 caractères, valeurs telles qu'affichées) :

| Chemin publié | Date client | SHA-256 publié | SHA-256 local | Identique |
|---|---|---|---|---|
| `CITATION.cff` | `2026-10-22T06:48:48Z` | `73e6e3353e2d` | `73e6e3353e2d` | oui, octets |
| `NOTICE.txt` | `2026-10-22T06:48:48Z` | `f3cdeca98157` | `49b386aae215` | non |
| `.zenodo.json` | `2026-10-22T06:48:48Z` | `4b698cdd3017` | `b5c21fc787db` | non |
| `IDENTITE_COMPLETE_AUTEUR_SOUVERAIN.json` | `2026-10-22T06:48:48Z` | `adeb7ca79705` | `f51481af01f2` | non |
| `CONTRAT_COMMERCIAL_50_50.md` | `2026-10-22T06:48:48Z` | `1f37567d92de` | `24e33096f8bf` | non |
| `contracts/AmalMizanSynchronMznContract.sol` | `2026-10-22T07:35:26Z` | `3f8864a9c873` | `23a5fa76d611` | non |
| `contracts/AmalMizanSynchronMznContract_VERIF_BASESCAN.sol` | `2026-10-22T14:38:27Z` | `23a5fa76d611` | `23a5fa76d611` | oui, octets |
| `LIVRE_BLANC_ALMIZAN_ASTRO_QODE_MZN_WHITEPAPER.md` | `2026-10-22T08:37:12Z` | `ebfec7926206` | `14077f9c5a6e` | non |
| `calculatrice_mizan.py` | `2026-10-25T18:31:14Z` | `b58cc410ef39` | `2511ebb95628` | non |
| `test_calculatrice_mizan.py` | `2026-10-25T18:31:14Z` | `41ed3b821ba3` | `41ed3b821ba3` | oui, octets |

Lecture : la copie locale actuelle du contrat (`23a5fa76…`) est identique à la copie publiée `VERIF_BASESCAN` du `2026-10-22T14:38:27Z`, pas à la version publiée à `07:35:26Z`. L'égalité est vérifiée ; en déduire que le fichier local a été remplacé par la copie de vérification est une **inférence**, non un fait observé.

## Second incident : nom de copie locale erroné

La première version corrigée cherchait `COFFRE…/05_CONTRAT_SMART_CONTRACT_SCELLE_AmalMizanSynchronMznContract.sol`. Le fichier réel s'appelle `05_CODE_SOURCE_SMART_CONTRACT_SCELLE_AmalMizanSynchronMznContract.sol` (listing du coffre, ligne 494). Le rapport indiquait une copie locale absente, ce qui pouvait être lu à tort comme une divergence. Après correction du mappage (ligne 501), le fichier est comparé et `10/10` est atteint.

## Reproduction avec le script livré

Exécutions réelles du 2026-10-28, dépôt ci-dessus, sans jeton :

```bash
py -3 scripts/verifier_anteriorite_depot.py \
  --depot Loulbak78920/ASTRO-QODE-ALMIZAN \
  --fichier "CITATION.cff=<workspace>/CITATION.cff" \
  --fichier "contracts/AmalMizanSynchronMznContract.sol=<workspace>/COFFRE_FORT_NUMERIQUE_DIGIPOSTE_AHMED_EL_BAHLOUL/05_CODE_SOURCE_SMART_CONTRACT_SCELLE_AmalMizanSynchronMznContract.sol" \
  --sortie <dossier>
```

Extrait mesuré :

```text
COMMITS_TOTAL=213
COMMIT_PLUS_ANCIEN=e6bc5fd0cbf8290b4eb2481c9f388096d97b528d
DATE_PLUS_ANCIEN_CLIENT=2026-10-22T06:48:48Z
FICHIER=CITATION.cff
COMMIT=e6bc5fd0cbf8290b4eb2481c9f388096d97b528d
IDENTIQUE_OCTETS=True
FICHIER=contracts/AmalMizanSynchronMznContract.sol
COMMIT=afc9b14cc74b9be236318dc1ead0c43a91ad0af9
IDENTIQUE_OCTETS=False
VERDICT=ANCRAGE_PUBLIE_PARTIEL
```

Code de retour `1`, cohérent avec la divergence du contrat.

| Cas | Résultat mesuré | Code de retour |
|---|---|---|
| `CITATION.cff` seul, copie locale intacte | `IDENTIQUE_OCTETS=True`, `VERDICT=ANCRAGE_PUBLIE_ETABLI` | `0` |
| Copie locale de `CITATION.cff` convertie en CRLF | `IDENTIQUE_OCTETS=False`, `IDENTIQUE_HORS_CRLF=True`, `VERDICT=ANCRAGE_PUBLIE_PARTIEL` | `1` |
| Dépôt inexistant `Loulbak78920/definitely-not-a-repo-xyz` | `ERREUR=HTTP_404_SUR_https://api.github.com/repos/...` | `2` |

La copie CRLF fait 3 217 octets et `a85f1f58…` ; la version LF fait 3 154 octets et `73e6e335…`. Le second verdict hors CRLF distingue donc bien une simple conversion de fins de ligne d'une divergence de contenu.

## Qualification des affirmations

| Affirmation | Statut | Preuve |
|---|---|---|
| `CITATION.cff` est publié tel quel depuis le commit `e6bc5fd0…` | ÉTABLI | brut au SHA, SHA-256 identique |
| Le contrat `AmalMizanSynchronMznContract.sol` est publié depuis `afc9b14c…` | ÉTABLI | `commits?path=`, brut au SHA |
| La version publiée du contrat diffère de la copie locale actuelle | ÉTABLI | SHA-256 `3f8864a9…` contre `23a5fa76…` |
| Le contrat publié le `2026-10-22T07:35:26Z` précède le déploiement du `2026-10-22T10:21:59Z` | ÉTABLI pour les valeurs, **INFÉRÉ** pour la portée | les deux dates viennent de sources distinctes ; la date de commit reste déclarative |
| La copie locale du contrat provient de la publication `VERIF_BASESCAN` | INFÉRÉ | égalité d'empreintes, pas d'historique de copie |
| Le dépôt appartient à l'auteur déclaré | NON ÉTABLI | ce Skill ne vérifie pas l'identité du compte |
| La date de commit est un horodatage indépendant | FAUX | commit `06:48:48Z` antérieur à `created_at` `07:04:32Z` |
| Les versions locales postérieures dérivent des versions publiées | NON VÉRIFIÉ | aucune comparaison de lignée dans ce cas |

## Limites confirmées par ce cas

- Un premier commit n'est pas un inventaire : il faut interroger chaque chemin.
- Un total de 100 commits peut être une page, pas l'historique : ici 213 commits sur 3 pages.
- Une empreinte identique prouve l'identité du contenu, jamais l'identité de l'auteur ni la date.
- Un nom de fichier local approximatif produit un faux « absent », distinct d'une divergence.
- GitHub peut réécrire l'historique, supprimer le dépôt ou le rendre privé : chaque relevé doit être daté et rejoué.
