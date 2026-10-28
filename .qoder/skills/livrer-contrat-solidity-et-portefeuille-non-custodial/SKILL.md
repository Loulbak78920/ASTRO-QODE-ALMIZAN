---
name: livrer-contrat-solidity-et-portefeuille-non-custodial
description: "Livrer un contrat Solidity avec un artefact compilé vérifié et une page portefeuille non-custodiale EIP-1193/EIP-6963. Couvre la compilation solc, la fraîcheur SHA-256 de l'artefact, l'endpoint d'artefact, l'encodage ABI manuel, la validation locale des règles métier, les tests statiques et HTTP, et la validation navigateur par fournisseur simulé. Utiliser pour compiler et publier un contrat, exposer ou vérifier un artefact, construire ou durcir une page de signature, ou prouver une livraison qui ne détient aucune clé."
---

# Livrer un contrat Solidity et un portefeuille non-custodial

## Quand l'utiliser

- Compiler un contrat `.sol`, figer un artefact (bytecode + ABI + empreinte), le publier derrière une route JSON.
- Construire ou durcir une page de signature qui prépare des transactions et les fait signer par un portefeuille EIP-1193.
- Prouver qu'une livraison ne détient, ne demande et ne stocke aucune clé, aucun mot de récupération.
- Revalider une chaîne déjà livrée : artefact périmé, bytecode trop gros, ABI incomplète, règle métier contournée côté page.

## Quand ne pas l'utiliser, et quoi répondre

- **Signature côté serveur, garde de clés, keystore hébergé** : refuser. Ce Skill ne couvre pas la custody ; le faire serait un changement de modèle de sécurité, pas une option.
- **Audit de sécurité formel** : hors périmètre. Un artefact frais et des tests statiques ne remplacent ni audit tiers ni bug bounty ; le dire explicitement.
- **Déploiement automatique** : interdit sans confirmation explicite. Le déploiement est une action à fort impact, signée par l'utilisateur.

## Règles non négociables

1. **Aucun secret** : pas de clé privée, mnémonique, keystore, ni dans la page, ni dans le serveur, ni dans les tests, ni dans les journaux. La page ne doit jamais les demander.
2. **Zéro stockage navigateur** pour le compte, la signature ou l'historique : ni `localStorage`, ni `sessionStorage`, ni cookie dédié. Journal en mémoire, perdu au rechargement.
3. **Toute écriture est préparée localement**, validée, confirmée, puis signée dans le portefeuille via `eth_sendTransaction`. Le serveur ne signe jamais.
4. **Honnêteté de l'état** : distinguer opérationnel / simulé / spécifié. Un contrat non déployé n'est ni « en production », ni « audité ». Un endpoint qui répond n'est pas une garantie de sécurité.
5. **Fraîcheur avant tout usage** : un artefact dont le SHA-256 de source ne correspond plus ne doit servir ni à l'affichage de confiance ni au déploiement.

## Étape 1 — Compiler et figer l'artefact

```bash
cd contracts
rm -rf build
npx --yes solc@0.8.24 --bin --abi --optimize --optimize-runs 200 -o build MonContrat.sol
```

- Fixer la version du compilateur ; la reporter dans l'artefact (`solc 0.8.24`), avec les options d'optimisation.
- Ne pas passer `--overwrite` à solcjs : l'option est inconnue, la commande sort en code 1 et produit `error: unknown option '--overwrite'`. Supprimer le dossier de sortie.
- Contrôler le code de retour **sans pipe trompeur**. `commande | head -50; echo $?` renvoie le statut de `head`, pas de `commande`. Utiliser `commande > sortie.txt 2>&1; rc=$?` ou `${PIPESTATUS[0]}`.

Artefact minimal, en JSON :

```json
{
  "contrat": "MonContrat",
  "compilateur": "solc 0.8.24",
  "optimiseur": {"enabled": true, "runs": 200},
  "source_sha256": "<64 hexadécimaux>",
  "bytecode_hex": "<hexadécimal sans 0x>",
  "bytecode_octets": 0,
  "limite_eip170_octets": 24576,
  "abi": []
}
```

- `source_sha256` se calcule sur les **octets** du `.sol`, pas sur une relecture texte réencodée : une lecture en mode texte peut normaliser CRLF ou CR isolé et changer l'empreinte.
- `bytecode_octets` = `len(bytecode_hex) // 2`.
- Viser une marge sous **24 576 octets** (EIP-170) ; un bytecode qui frôle la limite casse au premier ajout.

## Étape 2 — Vérifier avant de publier

Le script du paquet applique sept contrôles et sort en `0` (PASS), `1` (échec) ou `2` (usage ou lecture impossible) :

```bash
py -3 -B scripts/verifier_artefact.py \
  --source contracts/MonContrat.sol \
  --artifact contracts/MonContrat.artifact.json \
  --require proposerNouveauProprietaire --require accepterPropriete
```

- Exiger `RESULT PASS` et le code 0 **avant** de servir l'artefact ou de proposer un déploiement.
- Un `RESULT FAIL` n'est pas un avertissement : recompiler, puis relancer.
- Ajouter dans `--require` chaque fonction dont dépend la page (transfert, zakat, propriété, oracle).

## Étape 3 — Exposer l'artefact

Route JSON de lecture (exemple de forme) :

```json
{
  "succes": true,
  "statut": "source validée, non déployée",
  "artefact_a_jour": true,
  "avertissement": "Contrat non déployé. Le déploiement éventuel est signé par votre portefeuille ; ce site ne détient aucune clé privée.",
  "artefact": {"compilateur": "solc 0.8.24", "bytecode_octets": 0, "abi": []}
}
```

- `artefact_a_jour` se recalcule à chaque requête : `sha256(source) == artefact.source_sha256`.
- Prévoir un alias de route si des clients utilisent déjà l'autre orthographe (`artifact`), plutôt que de casser l'existant.
- `statut` doit rester explicitement « non déployé » tant qu'aucune adresse n'est publiée.
- **La page doit bloquer le déploiement quand `artefact_a_jour !== true`.** Afficher l'indicateur ne suffit pas : un bouton actif sur un artefact périmé déploie un bytecode qui ne correspond plus à la source relue.

## Étape 4 — Page portefeuille non-custodiale

### 4.1 Découverte du fournisseur

- Écouter `eip6963:announceProvider`, émettre `eip6963:requestProvider` au chargement.
- Repli sur `window.ethereum` ; s'il n'y a rien, afficher « portefeuille non détecté » et désactiver les actions.
- Ne charger aucune extension, aucun script tiers de portefeuille.

### 4.2 Connexion et réseau

- `eth_requestAccounts`, puis `eth_chainId` ; écouter `accountsChanged` et `chainChanged` pour réinitialiser l'état affiché.
- Pour changer de réseau, demander `wallet_switchEthereumChain` ; si le portefeuille renvoie 4902 (chaîne inconnue) ou -32603, proposer `wallet_addEthereumChain` avec les paramètres de la chaîne.
- Ne jamais supposer le réseau : revérifier `eth_chainId` juste avant l'envoi.

### 4.3 Lecture

- `eth_call` avec sélecteur + arguments encodés, `eth_getBalance`, `eth_getCode` pour vérifier qu'une adresse est bien un contrat.
- Afficher les valeurs lues avec leurs décimales réelles ; ne pas confondre wei et jetons.

### 4.4 Encodage ABI manuel

Si aucune bibliothèque n'est utilisée, encoder à la main et **tester les octets exacts** :

- Sélecteur = 4 premiers octets du keccak-256 de `nom(type1,type2)`.
- `address` : 20 octets minuscules, complétés à 32 à gauche.
- `uintN` : `BigInt`, hexadécimal complété à 32 octets à gauche.
- `intN` négatif : complément à deux sur 32 octets.
- `bool` : `0` ou `1` sur 32 octets.
- `string`/`bytes` : décalage dynamique, longueur, données UTF-8 complétées à un multiple de 32 ; plusieurs chaînes ⇒ décalages cumulatifs corrects.
- Montants décimaux : conversion par chaîne (`partie entière`, `fraction` complétée), jamais par `parseFloat` (perte de wei).

### 4.5 Validation locale avant signature

Rejeter **avant** toute estimation de gaz, avec un message précis :

- montant > 0 et convertible ; adresse conforme à `^0x[0-9a-fA-F]{40}$` ;
- règles métier du contrat (exemple : taux d'intérêt strictement 0, cohérence type/marge/part, cible de prélèvement consentie, propriété en deux étapes) ;
- cible d'une fonction de prélèvement limitée au compte connecté ou aux adresses autorisées ;
- mot de confirmation exact et sensible à la casse pour les actions irréversibles (déploiement, transfert de propriété).

Une règle métier vérifiée uniquement dans le contrat est insuffisante côté page : le contrat refusera, mais l'utilisateur aura signé une transaction vouée à l'échec.

### 4.6 Envoi

1. Vérifier la chaîne.
2. `eth_estimateGas` ; afficher destinataire, valeur, gaz estimé et calldata complet (ou tronqué avec le nombre d'octets pour un déploiement).
3. Exiger la case de consentement, plus le mot typé quand il est prévu.
4. `eth_sendTransaction` avec `from`, `to`, `data`, `value` ; la signature reste dans le portefeuille.
5. Écrire le statut dans un élément dédié à l'action ; journaliser en mémoire (émetteur, sélecteur, hash), jamais le contenu secret.
6. Déploiement : `to` absent, `data` = bytecode + arguments du constructeur, puis attente du reçu avec un nombre d'essais borné.

### 4.7 Preuve de contrôle

`personal_sign` d'un message horodaté (adresse, domaine, date), affichage de la signature, aucune transmission automatique. Cela prouve la possession du compte sans déplacer de fonds.

## Étape 5 — Tester

### Tests statiques du contrat

- fraîcheur de l'artefact (SHA source == `source_sha256`) ;
- `bytecode_octets == len(bytecode_hex)//2` et `< 24576` ;
- fonctions et événements essentiels présents dans l'ABI ;
- invariants numériques relus dans la source par expression régulière ;
- absence de `selfdestruct(`, `.delegatecall(`, `tx.origin`, `assembly`, littéral de 32 octets, mots `private key`/`mnemonic`/`seed phrase` ;
- aucune adresse `0x…{40}` codée en dur ;
- constructeur : rejet des adresses nulles, répartition initiale exacte.

### Tests HTTP

- routes de page en 200, endpoint d'artefact en JSON avec `artefact_a_jour`, alias fonctionnel ;
- la page ne contient ni `localStorage`, ni `sessionStorage` ;
- la page contient `personal_sign` et `eth_sendTransaction`, et la phrase de garantie non-custodiale.

### Validation navigateur par fournisseur simulé

Injecter un `window.ethereum` factice avant le chargement, puis vérifier dans la page réelle :

- calldata exact pour un transfert, une mise à jour d'oracle, une proposition de propriétaire ;
- rejet local du riba, d'une cible de prélèvement tierce, d'un mot typé incorrect ;
- aucune erreur console, pas de débordement horizontal.

Un test de calldata exact attrape les erreurs d'ordre d'arguments et de décalage dynamique qu'un simple « la transaction est partie » ne voit pas.

## Pièges vérifiés

| Piège | Conséquence | Correctif |
| :--- | :--- | :--- |
| `solcjs --overwrite` | code 1, `unknown option` | supprimer le dossier de sortie |
| `cmd \| head; echo $?` | code 0 malgré l'échec | `cmd > f 2>&1; rc=$?` ou `${PIPESTATUS[0]}` |
| SHA calculé après relecture texte | empreinte instable (CRLF/CR) | `read_bytes()` pour le SHA |
| `artefact_a_jour` affiché mais non appliqué | déploiement d'un bytecode périmé | désactiver le bouton si `!== true` |
| `<label>` imbriqué autour d'une case à cocher | double bascule au clic | conteneur `<div>` pour le champ booléen |
| `parseFloat` sur un montant | wei perdus, arrondi silencieux | conversion par chaîne |
| réseau supposé au chargement | envoi sur la mauvaise chaîne | revérifier `eth_chainId` avant envoi |
| secret affiché dans un journal ou une erreur | fuite irréversible | ne jamais journaliser le contenu signé |

## Checklist de livraison

- [ ] Compilation reproductible, version et options figées, code de retour contrôlé.
- [ ] Artefact frais, `bytecode_octets` cohérent, taille sous EIP-170.
- [ ] `verifier_artefact.py` sort en 0 avec les fonctions requises.
- [ ] Endpoint : `artefact_a_jour` calculé en direct, statut « non déployé » tant que c'est vrai.
- [ ] Page : aucune clé, aucun stockage navigateur, aucune extension chargée.
- [ ] Déploiement bloqué si l'artefact est périmé ; mot typé exigé.
- [ ] Calldata exact vérifié pour chaque action critique.
- [ ] Tests statiques, HTTP et navigateur exécutés ; résultats reportés sans exagération.
- [ ] Limites écrites : non déployé, non audité, oracle administratif, aucune garantie de rendement.

## Ressources

- `scripts/verifier_artefact.py` : contrôle source/artefact, code 0/1/2, sortie ASCII.
- `references/cas-verifie-almizan-v2.md` : cas réel Al-Mizan V2, commandes, empreintes, calldata exacts, écart connu sur `artefact_a_jour`, et limites.
