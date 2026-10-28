# Cas vérifié — Al-Mizan V2 et page portefeuille non-custodiale

Vérifications du 27/10/2026, sur le dépôt `ASTRO-Q°ODE_SYSTEME`.
Session source : `55f63550-7c8d-4f9e-b0a9-e73686cc2765`.
Les commandes marquées **REPRODUIT** ont été rejouées lors de la préparation de ce paquet ; celles marquées **DOCUMENTÉ** proviennent de la session source et n'ont pas été rejouées ici.

Fichiers concernés :

| Fichier | Rôle | Taille |
| :--- | :--- | :--- |
| `contracts/AlMizanV2Souverain.sol` | source du contrat | 507 lignes, 20 154 octets |
| `contracts/AlMizanV2Souverain.artifact.json` | artefact compilé | 9 970 octets de bytecode |
| `web_cloud/portefeuille_souverain.html` | page de signature | 1 327 lignes |
| `tests/test_contrat_intelligent_v2.py` | 9 tests statiques | 169 lignes |
| `tests/test_comptes_http_mizan.py` | tests HTTP, dont artefact et page | 362 lignes |
| `docs/CONTRAT_V2_ET_PORTEFEUILLE.md` | état et limites | 160 lignes |

---

## 1. Statut des preuves

| Élément | Statut | Preuve |
| :--- | :--- | :--- |
| Compilation reproductible | **REPRODUIT** | `solc 0.8.24`, code 0, bytecode identique à l'artefact |
| Fraîcheur de l'artefact | **REPRODUIT** | SHA-256 source = `38f6e03a…51c2` |
| Taille sous EIP-170 | **REPRODUIT** | 9 970 < 24 576 octets |
| Tests du contrat | **REPRODUIT** | 9 tests, `OK` |
| Tests HTTP | **REPRODUIT** | 6 tests, `OK` |
| `solcjs --overwrite` échoue | **REPRODUIT** | code 1, `error: unknown option '--overwrite'` |
| Script `verifier_artefact.py` | **REPRODUIT** | PASS + 5 échecs de contrôle + 1 erreur d'E/S |
| Calldata exacts dans le navigateur | **DOCUMENTÉ** | session source, fournisseur simulé |
| Rejet local du riba et du mot typé | **DOCUMENTÉ** | session source, messages exacts ci-dessous |
| `artefact_a_jour` non bloquant | **VÉRIFIÉ PAR LECTURE** | `portefeuille_souverain.html:1177-1204` |
| Déploiement sur une chaîne | **NON FAIT** | aucune adresse publiée |
| Audit tiers, exécution CI | **NON FAIT** | voir §7 |

---

## 2. Artefact

- Compilateur : `solc 0.8.24`, optimiseur activé, 200 runs.
- SHA-256 de la source : `38f6e03aceedf0010d1dc161a2aa121cc4a0e380ce39b7effa0ff6b0580951c2`.
- Bytecode : 9 970 octets (19 940 caractères hexadécimaux), limite 24 576.
- ABI : 65 fonctions, 15 événements, 14 erreurs, 1 constructeur à 4 arguments, `receive`.
- Clés de l'artefact : `contrat`, `compilateur`, `optimiseur`, `source_sha256`, `bytecode_hex`, `bytecode_octets`, `limite_eip170_octets`, `abi`.

Commande de compilation (sans `--overwrite`) :

```bash
cd contracts
rm -rf build
npx --yes solc@0.8.24 --bin --abi --optimize --optimize-runs 200 -o build AlMizanV2Souverain.sol
```

Résultat rejoué : code 0, deux fichiers `.bin` produits, `AlMizanV2Souverain_sol_AlMizanV2Souverain.bin` **identique octet pour octet** au `bytecode_hex` de l'artefact.

Échec de `--overwrite` (reproduit avec la commande exacte) :

```text
npx --yes solc@0.8.24 --bin --abi --optimize --optimize-runs 200 -o build --overwrite AlMizanV2Souverain.sol
code 1
error: unknown option '--overwrite'
```

La session source avait enregistré `EXIT=0` pour cette commande : le code venait de `head` dans un pipe, pas de solc. D'où la règle du paquet : rediriger avant de tester le code de retour.

---

## 3. Vérificateur du paquet

Sortie réelle sur la paire Al-Mizan (code 0) :

```text
OK   artefact lu : artefact.json
OK   source lue : source.sol (20154 octets)
OK   cles requises presentes
OK   bytecode hexadecimal : 9970 octets
OK   bytecode_octets coherent (9970)
OK   fraicheur : source 38f6e03aceedf001
OK   taille : 9970 <= 24576 octets
OK   abi : 65 fonctions
OK   fonctions ABI demandees presentes (4)
RESULT PASS
```

Cas négatifs exécutés sur des copies hors du paquet :

| Cas | Mutation réellement appliquée | Code | Message |
| :--- | :--- | ---: | :--- |
| source périmée | ajout d'un commentaire | 1 | `artefact perime` |
| longueur incohérente | `bytecode_hex` + `00` | 1 | `bytecode_octets declare 9970, longueur reelle 9971` |
| clé absente | suppression de `compilateur` | 1 | `cles manquantes : compilateur` |
| motif interdit | source + `selfdestruct(` , SHA de l'artefact recalculé | 1 | `motif interdit present : selfdestruct` |
| limite dépassée | `--limit 5000` | 1 | `bytecode 9970 octets > limite 5000` |
| source illisible | chemin inexistant | 2 | `ERROR lecture source impossible` |
| limite invalide | `--limit 0` | 2 | `ERROR --limit doit etre un entier positif` |

Le cas « motif interdit » a d'abord échoué sur la fraîcheur, parce que la réécriture en mode texte normalisait les fins de ligne ; il a été reconstruit en octets pour isoler réellement le contrôle de motif. C'est l'origine de la règle « SHA sur les octets » dans `SKILL.md`.

---

## 4. Tests du projet (REPRODUIT)

```bash
py -3 -B -m unittest tests.test_contrat_intelligent_v2   # 9 tests, OK
py -3 -B -m unittest tests.test_comptes_http_mizan       # 6 tests, OK
```

Les tests du contrat couvrent : fraîcheur, EIP-170, fonctions essentielles, invariants numériques, riba et consentement de zakat, propriété en deux étapes, motifs interdits, réserve/trésorerie, absence d'adresse en dur.

Les tests HTTP couvrent notamment l'endpoint d'artefact (`test_10`, ligne 329) et la page sans secret (`test_11`, ligne 349) : présence de `personal_sign` et `eth_sendTransaction`, absence de `localStorage` et `sessionStorage`.

---

## 5. Page portefeuille — structure

| Élément | Ligne |
| :--- | ---: |
| Table des sélecteurs `SEL` | 278 |
| `encTexte` (chaînes dynamiques) | 332 |
| `versWei` (conversion décimale) | 349 |
| Écoute `eip6963:announceProvider` | 404 |
| Émission `eip6963:requestProvider` | 419 |
| `wallet_switchEthereumChain` | 473 |
| Repli `wallet_addEthereumChain` | 477 |
| `signer` (envoi) | 811 |
| `eth_estimateGas` | 821 |
| `eth_sendTransaction` | 830 |
| Validation financement / riba | 962–974 |
| Mot typé `PROPRIETAIRE` | 983 |
| `personal_sign` | 1167 |
| `chargerArtefact` | 1177–1204 |
| Activation du bouton de déploiement | 1195 |
| `deployer` | 1214 |
| Mot typé `DEPLOYER` | 1246 |
| Calldata tronqué à l'affichage | 1247 |
| Envoi du déploiement | 1252 |

---

## 6. Calldata et rejets (DOCUMENTÉ, session source)

Fournisseur simulé injecté avant chargement, compte `0x1111…1111`, chaîne Base (8453).

| Action | Données observées |
| :--- | :--- |
| Transfert 1,5 MZN | `0xa9059cbb` + `0x2222…2222` + `0x14d1120d7b160000` (1,5 × 10¹⁸), `to` = jeton v1 `0x520c…A71db`, `value` 0 |
| Prix or/argent (6897, 87) | `0x6bbe4e8c` + `0x1af1` + `0x57` |
| Proposition de propriétaire | `0x80fb6fcd` + `0x6666…6666` |
| Riba non nul | `Le riba est refusé : le taux d'intérêt doit être 0.` |
| Mot typé incorrect | `Saisissez exactement « PROPRIETAIRE ».` |
| Zakat vers un tiers (v1) | `Refus de cet outil : la cible doit être votre compte connecté ou une adresse d'auteur. Le v1, lui, n'impose pas cette limite.` |

Contrôles navigateur associés : aucune erreur console, aucun débordement horizontal observé, bouton de déploiement sans effet tant que le portefeuille n'est pas connecté (`Connectez un portefeuille.`).

Ces valeurs n'ont pas été rejouées lors de la préparation du paquet : elles restent **documentées**, pas reproduites.

---

## 7. Écart connu — `artefact_a_jour` n'est pas bloquant

`chargerArtefact` lit la réponse, vérifie que le bytecode est hexadécimal, affiche le SHA-256 et le statut, puis active le bouton de déploiement (ligne 1195) **sans consulter `donnees.artefact_a_jour`**. Un artefact périmé reste donc déployable depuis cette page, alors que l'API signale déjà la péremption.

Correctif recommandé (règle imposée par `SKILL.md`) :

```js
$('btn-deployer').disabled = donnees.artefact_a_jour !== true;
if (donnees.artefact_a_jour !== true) {
    $('erreur-deploiement').textContent = 'Artefact périmé : recompilez avant de déployer.';
}
```

Tant que ce correctif n'est pas appliqué au projet, ne pas présenter la page comme bloquante sur ce point.

---

## 8. Contexte : jeton v1 déployé

Adresse Base : `0x520cbd0e1e72178f9e819AFf1e815606923A71db` (lecture seule, documentée dans `docs/CONTRAT_V2_ET_PORTEFEUILLE.md` §5).

- `preleverZakatAutomatique(address)` et `purgeKaffara(address,uint256)` sont publiques et sans consentement de la cible.
- Le contrat est immuable : pas de correctif sur place.
- La page limite les cibles au compte connecté ou aux adresses d'auteur, ce qui protège l'utilisateur de la page, pas les autres détenteurs.
- Le V2 répond à ce défaut par une allowance expresse (`payerZakatPour`) et un refus de tout taux d'intérêt.

---

## 9. Limites

- Le V2 n'est **pas déployé** : aucune adresse, aucun bytecode en production.
- Aucun audit tiers ; les tests statiques ne le remplacent pas.
- L'oracle or/argent est administratif et borné ; ce n'est pas un oracle décentralisé.
- La validation navigateur a utilisé un fournisseur simulé, pas un portefeuille réel.
- La CI GitHub Actions n'a jamais démarré (facturation du compte) ; les résultats ci-dessus sont locaux.
- Le jeton ne confère aucun droit de gouvernance ni garantie de rendement ou de parité métallique.
