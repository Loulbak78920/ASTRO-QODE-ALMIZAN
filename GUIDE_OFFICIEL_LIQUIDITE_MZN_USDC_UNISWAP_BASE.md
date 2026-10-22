# GUIDE OFFICIEL AL-MIZAN : PAIRE DE LIQUIDITÉ MZN / USDC SUR UNISWAP V3 (BASE MAINNET)
## CONFIGURATION CLAIRE, SIMPLE ET SÉCURISÉE EN DOLLARS/EUROS STABLES

---

**Auteur Souverain & Créateur** : M. Ahmed EL BAHLOUL (`IMAM8MAHDI` / `Loulbak78920`)  
**Smart Contract MZN Déployé** : [`0x520cbd0e1e72178f9e819AFf1e815606923A71db`](https://basescan.org/address/0x520cbd0e1e72178f9e819AFf1e815606923A71db)  
**Contrat USDC Natif Circle sur Base** : [`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`](https://basescan.org/token/0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)  
**Réseau** : **Base Mainnet (Coinbase L2)**  
**Date d'Émission** : 22 Octobre 2026 — Acte Scellé A085  

---

## 🌟 POURQUOI LE CHOIX DE L'USDC EST EXCELLENT POUR AL-MIZAN

1. **Stabilité et Transparence Totale** :  
   L'USDC est garanti 1:1 par des dollars réels sous régulation officielle Circle. Contrairement à l'ETH dont le cours varie chaque minute, **1 USDC vaut toujours 1 Dollar US** (~0,92 €).
2. **Lisibilité du Prix pour Tous** :  
   Fixer le prix initial en USDC permet à chacun de savoir exactement combien vaut 1 MZN en monnaie réelle, sans calculs complexes de fractions d'ETH.
3. **Protection de la Trésorerie** :  
   Vous disposez actuellement de **0,38 USDC** et de **8 000 000 MZN**. En déposant seulement **0,10 USDC** et **100 MZN**, vous ouvrez le marché mondial tout en gardant **99,998% de vos jetons en sécurité absolue**.

---

## ⚠️ RÈGLE TECHNIQUE CRUCIALE : LE GAZ RÉSEAU EN ETH SUR BASE

> [!IMPORTANT]
> **Sur la blockchain Base, les frais de carburant réseau (le gaz) sont TOUJOURS prélevés en ETH**, même si la transaction concerne des USDC ou des MZN !
>
> - **Votre solde actuel en USDC** : `0,382566 USDC` (largement suffisant pour le dépôt initial).
> - **Votre solde actuel en ETH** : `0,00000115 ETH` (~0,003 $).
>
> **Conséquence pratique dans MetaMask** :
> Pour signer les autorisations (Approve USDC, Approve MZN, et Création du pool), MetaMask vérifie que vous avez une réserve de gaz. Si MetaMask affiche un bouton grisé ou un message en rouge *"Solde insuffisant pour payer les frais de gaz réseau"*, **il suffit de transférer une goutte minime d'ETH (ex: 0.0005 ETH, soit environ 1,20 €) sur votre adresse Base `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C`**.

---

## 🔗 LIEN DIRECT PRÉ-CONFIGURÉ UNISWAP V3 (MZN / USDC SUR BASE)

Cliquez directement sur ce lien sécurisé officiel qui charge automatiquement les bons contrats sur le réseau Base :

👉 **[https://app.uniswap.org/positions/add/new?chain=base&currencyA=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&currencyB=0x520cbd0e1e72178f9e819aff1e815606923a71db](https://app.uniswap.org/positions/add/new?chain=base&currencyA=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913&currencyB=0x520cbd0e1e72178f9e819aff1e815606923a71db)**

*(Si Uniswap affiche un avertissement "Ce jeton n'apparaît pas sur les listes actives", cochez "Je comprends" : c'est parfaitement normal pour un nouveau contrat souverain).*

---

## ⚙️ LES 4 ÉTAPES EXACTES SUR L'ÉCRAN UNISWAP

### 1. Sélectionner le Palier de Frais (Fee Tier)
- Cliquez sur **« Modifier le palier »** (ou *Select Fee Tier*).
- Choisissez : **`0.3%`** (Palier standard très recommandé pour USDC/tokens) ou **`1.0%`**.

### 2. Définir le Prix de Départ (Starting Price)
Uniswap vous demande le ratio de départ :
- **Si la case affiche « MZN par USDC »** :  
  Tapez : **`1000`**  
  *(Signification : 1 USDC = 1 000 MZN, ce qui donne **1 MZN = 0,001 $**, soit un dixième de centime).*
  *(Si vous préférez 1 MZN = 1 centime, tapez `100`).*
- **Si la case affiche « USDC par MZN »** :  
  Tapez : **`0.001`** (ou `0.01`).

### 3. Sélectionner la Fourchette de Prix (Price Range)
- Cliquez sur le bouton : **« Fourchette Complète »** (*Full Range*) ou **Large**.
- Cochez *"Je comprends"* pour valider que le pool couvrira l'ensemble des échanges.

### 4. Saisir les Montants du Dépôt
- Dans la case **USDC** : Tapez **`0.10`** (ou `0.20`).
- La case **MZN** va se calculer automatiquement : elle affichera **`100`** (ou `200` MZN).
- *(Vérifiez que l'interrupteur éventuel "Ajouter en tant que..." est désactivé si présent).*

### 5. Valider dans MetaMask
- Faites défiler la page vers le bas avec la molette de votre souris.
- Cliquez sur **« Approuver USDC »** -> Validez dans MetaMask (coût : ~0,0000003 ETH).
- Cliquez sur **« Approuver MZN »** -> Validez dans MetaMask (coût : ~0,0000003 ETH).
- Cliquez sur **« Aperçu »** puis **« Ajouter »** -> Validez dans MetaMask.

---

## 🛡️ RÉCAPITULATIF DES ADRESSES OFFICIELLES SCELLÉES

| Rôle | Adresse Blockchain sur Base Mainnet |
| :--- | :--- |
| **Smart Contract MZN** | `0x520cbd0e1e72178f9e819AFf1e815606923A71db` |
| **Jeton USDC Officiel (Circle)** | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` |
| **Trésorerie Auteur (Ahmed EL BAHLOUL)** | `0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C` |
| **Réserve Souveraine (Clé Dorée)** | `0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B` |
