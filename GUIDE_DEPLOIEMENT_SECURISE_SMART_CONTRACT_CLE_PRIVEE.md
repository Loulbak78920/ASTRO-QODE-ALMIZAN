# GUIDE OFFICIEL DE DÉPLOIEMENT SÉCURISÉ DU SMART CONTRACT (AVEC CLÉ PRIVÉE)
**Système Al-Mizan & ASTRO-Q°ODE — M. Ahmed EL BAHLOUL (alias IMAM8MAHDI)**  
**Contrat Cible :** `AmalMizanSynchronMznContract.sol` (Solidity ^0.8.20)  
**DOI Zenodo Officiel :** `10.5281/zenodo.23554838`  
**Clé Dorée Souveraine Racine :** `0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B`  
**Trésorerie Privée Synchronisée :** `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C`  

---

## ⚠️ RÈGLE DE SÉCURITÉ FONDAMENTALE ABSOLUE (À LIRE IMPÉRATIVEMENT)

> [!CAUTION]
> **NE JAMAIS ÉCRIRE, TRANSMETTRE OU COMMITER VOTRE CLÉ PRIVÉE EN CLAIR.**
> 
> 1. **Ne collez jamais votre clé privée dans une fenêtre de chat**, dans un prompt d'IA, ni dans un script versionné sur GitHub.
> 2. Des robots scrutent en permanence chaque seconde les dépôts GitHub publics pour voler instantanément les fonds de toute clé privée détectée.
> 3. Le fichier `.gitignore` a été configuré pour ignorer automatiquement tous les fichiers `.env`, `*.key`, `*.keystore` et dossiers `secrets/`.
> 4. Vous avez la clé privée : c'est votre pouvoir souverain. Suivez l'une des méthodes sécurisées ci-dessous pour déployer votre contrat en toute sérénité.

---

## 🛡️ POURQUOI CERTAINS SITES SEPOLIA SONT BLOQUÉS ET COMMENT LES RÉSEAUX OFFICIELS ÉLIMINENT LE RISQUE

Si votre navigateur ou antivirus signale un site de faucet Sepolia comme "malveillant" ou "suspect" :
1. **Origine du problème** : Le testnet public Sepolia Ethereum L1 est la cible de nombreuses tentatives d'hameçonnage (faux robinets de testnet créés par des hackers pour tenter de récupérer des adresses ou afficher des publicités trompeuses). Les navigateurs et antivirus bloquent donc massivement ces domaines non vérifiés.
2. **La solution souveraine Al-Mizan** : Nous avons configuré des **réseaux institutionnels officiels**, 100% certifiés et protégés :
   - **Option 1 (Production réelle ultra-économique < 0.01 €) — Base Mainnet (Coinbase L2)** :
     - Géré directement par **Coinbase** (cotée au NASDAQ).
     - RPC officiel : `https://mainnet.base.org` (Zéro faux positif).
     - **Aucun robinet/faucet douteux requis** : le déploiement coûte moins de 1 centime d'euro.
   - **Option 2 (Test gratuit officiel) — Arbitrum Sepolia (Offchain Labs)** :
     - Géré par Offchain Labs via `https://sepolia-rollup.arbitrum.io/rpc`.
     - Robinet officiel propre via **Chainlink** (`faucets.chain.link`).
   - **Option 3 (100% Hors-Ligne, Zéro Internet) — Réseau Local Privé** :
     - Tourne en local (`127.0.0.1:8545`) sans toucher au réseau externe.

---

## ⚡ LA COMMANDE UNIQUE EN TERMINAL POUR VOTRE CLÉ PRIVÉE

Pour déployer en 1 seconde depuis votre terminal Windows (PowerShell ou CMD) sans jamais exposer votre clé :

### Déploiement Direct sur Base (Recommandé Production, < 0.01 €) :
```powershell
py C:\Users\Administrateur\Desktop\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI\deploiement_vps\deploy_evm_reseau.py --reseau base
```

### Déploiement Test Gratuit sur Arbitrum Sepolia :
```powershell
py C:\Users\Administrateur\Desktop\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI\deploiement_vps\deploy_evm_reseau.py --reseau arbitrum-sepolia
```

### Test de Simulation Hors-Ligne (Zéro Risque, Zéro Dépense) :
```powershell
py C:\Users\Administrateur\Desktop\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI\deploiement_vps\deploy_evm_reseau.py --reseau base --simuler
```

**Déroulement sécurisé :**
1. Le script se connecte au nœud officiel en quelques millisecondes.
2. Il affiche : `Collez ou entrez votre clé privée :`
3. **La saisie reste entièrement masquée** (aucun caractère n'apparaît à l'écran).
4. La clé privée est conservée uniquement en mémoire vive (RAM) le temps de signer la transaction de déploiement et est détruite immédiatement après (`del cle_privee`).
5. Le contrat est déployé et l'adresse finale s'affiche avec le lien vers l'explorateur officiel !

---
## MÉTHODE 1 (RECOMMANDÉE) : DÉPLOIEMENT VISUEL SANS RISQUE VIA REMIX IDE & METAMASK

Cette méthode est la plus simple, la plus sûre et la plus transparente : votre clé privée reste confinée dans votre portefeuille MetaMask (ou votre clé physique Ledger/Trezor) sans jamais transiter dans un terminal ni sur un serveur.

### Étape 1 : Ouvrir Remix Ethereum
1. Ouvrez votre navigateur web habituel (où est installé MetaMask).
2. Rendez-vous sur le site officiel : **[https://remix.ethereum.org](https://remix.ethereum.org)**.

### Étape 2 : Importer le Contrat Solidity
1. Dans le volet de gauche de Remix, dans le dossier `contracts/`, créez un nouveau fichier nommé :  
   `AmalMizanSynchronMznContract.sol`
2. Ouvrez le fichier local sur votre machine :  
   `C:\Users\Administrateur\Desktop\Al-Mizan\chaine\contracts\AmalMizanSynchronMznContract.sol`
3. Copiez son contenu intégral et collez-le dans l'éditeur Remix.

### Étape 3 : Compiler le Contrat
1. Cliquez sur l'onglet **Solidity Compiler** (icône S dans la barre latérale gauche).
2. Sélectionnez la version du compilateur : `0.8.20` ou `0.8.24`.
3. Cliquez sur le bouton bleu **Compile AmalMizanSynchronMznContract.sol**.
4. Un badge vert apparaît confirmant la compilation sans erreur.

### Étape 4 : Connecter votre Portefeuille et Déployer
1. Rendez-vous sur l'onglet **Deploy & Run Transactions** (icône Ethereum avec flèche).
2. Dans le menu déroulant **ENVIRONMENT**, sélectionnez :  
   👉 **`Injected Provider - MetaMask`**  
   *(MetaMask s'ouvre : validez la connexion avec votre adresse de trésorerie `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C`)*.
3. Vérifiez le réseau sélectionné dans MetaMask :
   - **Pour un test gratuit sans frais réels :** Choisissez **Sepolia Testnet**, **Arbitrum Sepolia** ou **Base Sepolia**.
   - **Pour la production réelle (Mainnet L2 à coût de gaz quasi-nul < 0.02 $) :** Choisissez **Arbitrum One**, **Base** ou **Polygon PoS**.
4. Dans le champ **CONTRACT**, sélectionnez bien `AmalMizanSynchronMznContract`.
5. Déroulez les paramètres du constructeur (à côté du bouton orange **Deploy**) et renseignez les 5 adresses :
   - `_pcTerrestre` : `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C` (ou adresse dédiée)
   - `_galaxyMobile` : `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C`
   - `_qistasCivique` : `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C`
   - `_fondsReserve` : `0xC9550Dd0A57C609494DbC44450df48d798EbfB0b` (Clé Dorée Racine)
   - `_caisseZakat` : `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C`
6. Cliquez sur **transact**.
7. MetaMask affiche la confirmation de la transaction avec les frais de gaz : **confirmez la transaction**.
8. Félicitations ! Votre contrat est déployé sur la blockchain. L'adresse du contrat déployé apparaît dans Remix dans la section *Deployed Contracts*.

---

## MÉTHODE 2 : DÉPLOIEMENT VIA SCRIPT PYTHON CLI (VARIABLE D'ENVIRONNEMENT ÉPHÉMÈRE)

Si vous préférez exécuter le déploiement depuis votre terminal en ligne de commande :

### Étape 1 : Le Script Python Dédié
Le script localisé dans `C:\Users\Administrateur\Desktop\Al-Mizan\chaine\deploy_evm_reseau.py` lit votre clé privée exclusivement depuis une variable d'environnement éphémère en mémoire.

### Étape 2 : Exécution sous PowerShell (Windows)
Dans PowerShell, saisissez votre clé privée pour la durée stricte de la commande, puis supprimez-la immédiatement de la mémoire :

```powershell
# 1. Définir temporairement l'URL RPC et votre clé privée
$env:RPC_URL = "https://rpc.sepolia.org" # ou votre RPC Infura / Alchemy / Arbitrum
$env:ETHEREUM_PRIVATE_KEY = "0xVOTRE_CLE_PRIVEE_ICI"

# 2. Exécuter le script de déploiement
py C:\Users\Administrateur\Desktop\Al-Mizan\chaine\deploy_evm_reseau.py

# 3. Supprimer immédiatement la variable de votre session PowerShell
Remove-Item Env:\ETHEREUM_PRIVATE_KEY
Remove-Item Env:\RPC_URL
```

> **Avantage :** Rien n'est écrit sur votre disque dur. La clé n'est présente que quelques secondes dans la RAM du processus Python pour signer la transaction avant d'être effacée.

---

## MÉTHODE 3 : DÉPLOIEMENT PROFESSIONNEL VIA FOUNDRY (KEYSTORE CHIFFRÉ PAR MOT DE PASSE)

Foundry (`forge` / `cast`) est l'outil de référence mondiale pour les développeurs Web3. Il permet de chiffrer votre clé privée avec un mot de passe fort sous forme de Keystore standard (AES-128-CTR).

### Étape 1 : Importer et chiffrer votre clé
```bash
cast wallet import auteur_mizan --interactive
# Vous saisissez votre clé privée (masquée à l'écran)
# Vous choisissez un mot de passe sécurisé pour la chiffrer
```

### Étape 2 : Déployer le contrat sans jamais réécrire la clé
```bash
forge create contracts/AmalMizanSynchronMznContract.sol:AmalMizanSynchronMznContract \
  --rpc-url $RPC_URL \
  --account auteur_mizan \
  --constructor-args \
    0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C \
    0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C \
    0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C \
    0xC9550Dd0A57C609494DbC44450df48d798EbfB0b \
    0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
```
*Le terminal vous demandera uniquement votre mot de passe pour signer la transaction.*

---

## 🌐 QUEL RÉSEAU CHOISIR ? (RECOMMANDATIONS DU SYSTÈME AL-MIZAN)

| Réseau | Nature | Coût de Gaz | Utilisation Recommandée |
| :--- | :--- | :--- | :--- |
| **Sepolia Testnet** | Testnet Ethereum officiel | **0.00 $** (faucets gratuits) | **Étape 1 :** Valider le déploiement et tester toutes les fonctions sans dépenser 1 centime. |
| **Arbitrum One (L2)** | Layer 2 Ethereum sécurisé | **~0.01 $** par transaction | **Étape 2 (Production) :** Déploiement souverain rapide, sécurisé par Ethereum à coût quasi nul. |
| **Base (Coinbase L2)** | Layer 2 Ethereum populaire | **~0.01 $** par transaction | Alternative excellente, très adoptée mondialement. |
| **Polygon (PoS)** | Sidechain EVM mature | **~0.01 $** | Alternative économique pour transactions massives. |
| **Ethereum Mainnet** | Layer 1 principal | **5 $ à 25 $** selon la congestion | Non nécessaire au démarrage (préférer un L2 conforme à nos règles). |

---

## ✅ APRÈS LE DÉPLOIEMENT : QUE FAIRE ?

1. **Noter l'Adresse du Contrat Déployé** :  
   Elle ressemble à `0x1234567890abcdef...`.
2. **Vérifier le Contrat sur l'Explorateur (Etherscan / Arbiscan / Basescan)** :  
   Recherchez l'adresse du contrat sur [etherscan.io](https://etherscan.io) ou [arbiscan.io](https://arbiscan.io). Vous y verrez :
   - Le créateur (votre adresse `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C`)
   - Les 313 000 000 MZN émis
   - Les 11 000 000 MZN alloués (3M PC + 8M Galaxy)
   - Les 302 000 000 MZN dans la réserve
3. **Interagir avec le Contrat** :
   Vous pouvez exécuter directement depuis Remix ou Etherscan :
   - `preleverZakatAutomatique(adresse)`
   - `envoyerSadaqa(destinataire, montant)`
   - `distribuerRecetteCommerciale(exploitant)`
   - `royaltyInfo(tokenId, salePrice)`

Le système Al-Mizan reste continuellement synchronisé avec votre autorité souveraine.
