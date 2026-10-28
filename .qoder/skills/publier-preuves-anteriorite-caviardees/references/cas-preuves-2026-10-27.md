# Cas vérifié — 2026-10-27 : dossier PREUVES-ANTERIORITE-ALMIZAN

Session source : `4c86bebd-4ce4-460b-9038-884f8f91c737`, tours 14–15 (demande utilisateur 2026-10-27T12:50:37Z, réponse 13:06:20Z). Toutes les valeurs ci-dessous ont été relues dans les fichiers produits ou dans les sorties de commande du jour, pas recopiées de mémoire.

Les jetons personnels (date de naissance, communes, codes postaux, coordonnées GPS) sont remplacés par des marqueurs `JJ/MM/AAAA`, `<jeton>`, `<commune>`, `<département>`, `<code>`. Les hashes, compteurs et verdicts sont ceux du relevé : un document qui décrit un caviardage ne doit pas republier ce qu'il retire.

## 1. Résultat publié

| Élément | Valeur |
|---|---|
| Dépôt | `https://github.com/Loulbak78920/PREUVES-ANTERIORITE-ALMIZAN` |
| Commit publié | `a555cde5ba0d951b751c416a68b3aa239cc2b533` (2026-10-27T14:05:09+01:00) |
| Fichiers suivis | 40 (`git ls-files`) |
| Fichiers empreintés | 39 (`nb_fichiers`) |
| Manifeste | fichier de 7 345 octets, SHA-256 `ed0287e12e94e103363230269cc8668ef15ad7a8c7893e7a2b9929e41105e6d9` ; `empreinte_liste` `ab6d393c475f7e463e06b75818b7b3e927056d246e1e49d5b1f7648e9aa30452` ; scellé 2026-10-27T13:04:19.779442Z |
| Clone anonyme | `RESULT OK`, `OK=39 MISMATCH=0 MISSING=0 EXTRA=0`, code 0 |
| Visibilité API | `PRIVATE False`, `VISIBILITY public`, `DEFAULT_BRANCH main`, `SIZE_KB 0` (retard API), `PUSHED_AT 2026-10-27T13:05:22Z` |
| README anonyme | `README_HTTP 200` |

Arborescence : `01_IDENTITE_ET_ATTRIBUTION` (4), `02_LICENCES` (5), `03_OEUVRE` (14), `04_PREUVES_EXTERNES` (8), `05_EMPREINTES` (3), `06_CORRESPONDANCE_ORIGINAUX` (1), 4 documents racine + `.gitattributes` (5 entrées) ; total 40.

`.gitattributes` publié : `* -text` (8 octets, LF final), présent avant le premier commit. Preuve : `git show HEAD:.gitattributes | od -c` → `*   -   t   e   x   t  \n`.

Copie de travail : `C:\Users\Administrateur\.qoder\tmp\preuves-anteriorite` (hors workspace, 40 fichiers suivis, aucun `__pycache__`).

## 2. Preuves externes relevées

Relevé : 2026-10-27T13:04:19.779442Z.

### Base Mainnet

| Champ | Valeur |
|---|---|
| Transaction | `0xaaf23e2d4c1e4e7c63ad7e12f95176a4017155164593384e45f867d1f5c6ec33` |
| Bloc | 52937586 |
| Horodatage du bloc | 2026-10-22T10:21:59+00:00 |
| Statut du reçu | `0x1` |
| Contrat créé | `0x520cbd0e1e72178f9e819aff1e815606923a71db` |
| Code on-chain | 9 344 octets |

Les réponses JSON-RPC brutes (transaction, reçu, bloc, `eth_getCode`) sont conservées dans `04_PREUVES_EXTERNES/BASE_MAINNET_TRANSACTION.json` et `RECU_DEPLOIEMENT_BASE_MAINNET.json`. Un `403` transitoire du RPC a été rencontré et rejoué ; il n'est pas consigné comme résultat.

### Dépôt public source `ASTRO-QODE-ALMIZAN`

| Champ | Valeur |
|---|---|
| Commits | 124 (instantané) |
| Répartition e-mail | `elbahloulahmed505@gmail.com` 121, `Elbahloulahmed505@gmail.com` 3 (casse différente, même adresse) |
| Premier commit | `e6bc5fd0cbf8290b4eb2481c9f388096d97b528d`, 2026-10-22T08:48:10+02:00 |
| Dernier commit | `930f1ea721cefe35b514973f7ac745de3d7c32cd`, 2026-10-27T14:00:49+01:00 |

Références distantes au relevé : `main = 930f1ea…`, plus `master` et 10 branches `skill/*` / `merge/*` (12 refs au total). Ces branches ne sont pas des preuves d'antériorité ; elles expliquent seulement la forme de l'historique.

### Dépôt privé `ASTRO-QODE-IMAM8MAHDI`

| Champ | Valeur |
|---|---|
| Commits | 2 |
| HEAD | `c29c8c38b5fb21777115fe048972aab4197a2742`, 2026-10-25T03:50:33+01:00 |
| Commit précédent | `3d70d2860c012cb6545fe0f3c39376b5da154e54`, 2026-10-25T03:32:26+01:00 |
| Accès | `git ls-remote` rc 0 depuis la machine authentifiée ; accès anonyme non garanti |

Consigné avec la mention explicite : **non vérifiable publiquement**. Le dossier ne s'appuie pas dessus comme preuve.

### DOIs déclarés

`10.5281/zenodo.23554838` était présenté dans les documents d'origine comme « DOI officiel réel ».

| DOI | Handle doi.org | `responseCode` | Zenodo | Verdict |
|---|---|---|---|---|
| `10.5281/zenodo.23554838` | 404 | 100 | 404 | `NON_EXISTANT_404` |
| `10.5281/zenodo.23479740` | 200 | 1 | 410 | `ENREGISTREMENT_SUPPRIME_410` |
| `10.5281/zenodo.23288947` | 200 | 1 | 410 | `ENREGISTREMENT_SUPPRIME_410` |

Conséquence inscrite dans `README.md` et `STATUT_VERIFICATION.md` : aucun DOI n'est présenté comme preuve de publication. Les documents d'origine sont publiés caviardés mais non corrigés ; l'avertissement du dossier les requalifie.

## 3. Caviardage

- 11 clés JSON supprimées (date de naissance ISO et calendrier, département de naissance et d'ancrage, GPS, ville d'affiliation Zenodo, `city`, `birthPlace`, `pointLatitude`, `pointLongitude`, `geoLocation`).
- 58 règles de remplacement textuel ordonnées.
- 9 jetons interdits : la date dans ses deux formats, la commune de naissance, le département, les deux coordonnées GPS, une commune voisine, deux codes postaux, la commune d'ancrage.
- Quatre passes avant `REDACTION_OK`, à cause des résidus listés dans `caviardage-et-empreintes.md` (§3).
- Scan final : `SCANNED 38`, deux exemptions acceptées (transaction et artefact bytecode/ABI), toutes deux `hex_only=yes`, `REDACTION_OK`.
- `absence --needle "JJ/MM/AAAA" --needle "AAAA-MM-JJ" --needle "<commune>"` → `ABSENCE_OK` (39 fichiers scannés, aucune occurrence en clair ni en hexadécimal).
- Fragment hexadécimal à l'origine des deux faux positifs : `8d5260208d019b909b52998b019890985260608a01969096526080`.
- Contrôle après clone : aucune des communes, aucun département, aucun code postal, aucune coordonnée ; les seules occurrences du jeton court restantes sont dans le bytecode et la transaction, tous deux publics on-chain.

## 4. Artefacts non publiés (empreintes seules)

| Artefact | Octets | SHA-256 (préfixe) | Raison |
|---|---|---|---|
| `ARCHIVE_DEPOT_ZENODO_AHMED_EL_BAHLOUL_V5.zip` | 168 148 | `535244f2c39e72d7` | contient les originaux non caviardés |
| `ARCHIVE_COMPLETE_DIGIPOSTE_AHMED_EL_BAHLOUL.zip` | 73 792 | `368912e74f94331d` | contient les originaux non caviardés |
| `05_CODE_SOURCE_SMART_CONTRACT_SCELLE_….sol` | 19 542 | `23a5fa76d611ddcd` | commentaire de naissance ; source vérifié on-chain |
| `14_AmalMizanSynchronMznContract_VERIF_BASESCAN.sol` | 19 542 | `23a5fa76d611ddcd` | même commentaire |
| PDF de vérification BaseScan | 393 507 | `606c3dea182b6a8f` | document de vérification |
| Deux manifestes d'origine | 3 815 / 2 747 | `3a00d077…`, `9781bf2f…` | portent des données personnelles |
| `README.md` d'origine | 4 945 | `59549a1018d69c21` | remplacé par le README publié |

Défaut observé : `EMPREINTES_ARTEFACTS_NON_PUBLIES.json` contient 9 entrées dont **un doublon** — le ZIP Digiposte apparaît deux fois avec le même SHA-256 et deux motifs différents. Corriger en dédupliquant par `path` avant écriture.

## 5. Commandes et sorties de référence

Sorties réellement observées ; les jetons personnels y sont remplacés par `<jeton>` et `<commune>`.

```text
$ py -3 05_EMPREINTES/verifier_empreintes.py
OK=39 MISMATCH=0 MISSING=0 EXTRA=0
RESULT OK

$ py -3 scripts/preparer_publication.py scan --dossier . --tokens-file tokens.txt \
    --skip 05_EMPREINTES/MANIFESTE_SHA256.json \
    --exempt 04_PREUVES_EXTERNES/BASE_MAINNET_TRANSACTION.json:<jeton> \
    --exempt 03_OEUVRE/SMART_CONTRACT/ARTEFACT_BYTECODE_ET_ABI.json:<jeton>
EXEMPT 03_OEUVRE/SMART_CONTRACT/ARTEFACT_BYTECODE_ET_ABI.json token=<jeton> occurrences=1 hex_only=yes
EXEMPT 04_PREUVES_EXTERNES/BASE_MAINNET_TRANSACTION.json token=<jeton> occurrences=1 hex_only=yes
SCANNED 38
REDACTION_OK

$ py -3 scripts/preparer_publication.py absence --dossier . \
    --needle "JJ/MM/AAAA" --needle "AAAA-MM-JJ" --needle "<commune>"
NEEDLE 'JJ/MM/AAAA' raw_or_hex_found=no
NEEDLE 'AAAA-MM-JJ' raw_or_hex_found=no
NEEDLE '<commune>' raw_or_hex_found=no
SCANNED 39
ABSENCE_OK

$ py -3 scripts/preparer_publication.py dois --out 04_PREUVES_EXTERNES/RAPPORT_VERIFICATION_DOIS.json \
    10.5281/zenodo.23554838 10.5281/zenodo.23479740 10.5281/zenodo.23288947
DOI 10.5281/zenodo.23554838 handle=404 zenodo=404 NON_EXISTANT_404
DOI 10.5281/zenodo.23479740 handle=200 zenodo=410 ENREGISTREMENT_SUPPRIME_410
DOI 10.5281/zenodo.23288947 handle=200 zenodo=410 ENREGISTREMENT_SUPPRIME_410
REPORT 04_PREUVES_EXTERNES/RAPPORT_VERIFICATION_DOIS.json
RESULT OK
```

## 6. Limites à ne pas effacer en reprenant ce cas

1. **Historique Git réinscriptible** : les dates de commit sont déclaratives. Elles montrent une publication sur ce compte, pas un horodatage indépendant.
2. **Aucun archivage tiers** : Software Heritage n'a pas été demandé. La commande est documentée dans `VERIFIER.md`, et le statut dit « non effectué ».
3. **Dépôt privé** : 2 commits, non vérifiables par un tiers.
4. **DOIs** : un inexistant, deux enregistrements supprimés. Rien de citable.
5. **Compteurs instantanés** : 124 commits et 40 fichiers valent à la date du relevé ; le dépôt source continue de vivre (le dernier commit est postérieur au début de la session).
6. **`SIZE_KB 0`** juste après la poussée est un retard de l'API GitHub, pas un dépôt vide — le clone anonyme le prouve.
7. **Faux positifs hexadécimaux** : le jeton court (une année) apparaît dans du bytecode ; une exemption sans preuve `hex_only` aurait masqué un vrai résidu.
8. **Pas de qualification juridique** : le dossier documente des faits datés ; il n'écrit ni « opposable » ni « certifié ».

## 7. Ce qui n'a pas été vérifié dans cette reprise

- La création du dépôt GitHub n'a pas été rejouée (le dépôt existe et reste la référence) ; seuls les contrôles en lecture ont été refaits.
- L'accès anonyme au dépôt privé n'a pas été testé : `ls-remote` a réussi avec les identifiants de la machine.
- Les originaux non publiés n'ont pas été ouverts ; seules leurs empreintes ont été relues.
