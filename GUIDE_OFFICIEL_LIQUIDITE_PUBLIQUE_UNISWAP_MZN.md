# GUIDE OFFICIEL AL-MIZAN : CRÉATION D'UNE LIQUIDITÉ PUBLIQUE SOUVERAINE SUR UNISWAP V3 (BASE MAINNET)
## COMMENT OUVRIR LE MARCHÉ PUBLIC POUR LE JETON MZN DE FAÇON ÉQUITABLE, SÉCURISÉE ET PROTÉGÉE

---

**Auteur Souverain & Créateur** : M. Ahmed EL BAHLOUL (`IMAM8MAHDI` / `Loulbak78920`)  
**Smart Contract Officiel Déployé** : [`0x520cbd0e1e72178f9e819AFf1e815606923A71db`](https://basescan.org/address/0x520cbd0e1e72178f9e819AFf1e815606923A71db)  
**Réseau** : **Base Mainnet (Coinbase Layer 2)**  
**DOI Officiel Zenodo** : `10.5281/zenodo.23554838`  
**Date d'Émission** : 22 Octobre 2026  

---

## ⚠️ LES 3 RÈGLES D'OR DE SÉCURITÉ D'AL-MIZAN (À LIRE ABSOLUMENT AVANT DE COMMENCER)

> [!IMPORTANT]
> 1. **RÈGLE N°1 : NE DÉPOSEZ JAMAIS TOUS VOS 8 MILLIONS DE MZN !**
>    - Si vous mettez 8 000 000 MZN avec seulement 5 ou 10 € d'ETH, un robot ou un spéculateur pourrait acheter la quasi-totalité de vos tokens pour une poignée d'euros.
>    - Déposez uniquement une **fraction initiale symbolique** (par exemple : **10 000 MZN** à **50 000 MZN**). Vous conservez ainsi **99.8% de votre trésorerie en sécurité**.
>
> 2. **RÈGLE N°2 : CHOISISSEZ LA PAIRE OFFICIELLE ETH / MZN**
>    - Sur le réseau Base, l'ETH est la monnaie reine. N'utilisez pas de faux tokens non officiels comme le BTCB déprécié.
>    - La paire **ETH / MZN** permet à quiconque sur Base d'échanger instantanément avec de l'Ethereum réel.
>
> 3. **RÈGLE N°3 : CHOISISSEZ LE PALIER DE FRAIS À 1% (OU 0.3%)**
>    - Ne choisissez **JAMAIS 0.01%** (ce palier est uniquement fait pour les stablecoins identiques comme USDC/USDT).
>    - Pour un nouveau jeton, sélectionnez **1%** (recommandé pour les paires émergentes) ou **0.3%**.

---

## 🔗 ÉTAPE 1 : OUVRIR LE LIEN OFFICIEL PRÉ-CONFIGURÉ PAR AL-MIZAN

Cliquez directement sur ce lien sécurisé qui sélectionne automatiquement le réseau **Base**, l'**ETH** natif et votre contrat **MZN** :

👉 **[https://app.uniswap.org/positions/add/new?chain=base&currencyA=ETH&currencyB=0x520cbd0e1e72178f9e819AFf1e815606923A71db](https://app.uniswap.org/positions/add/new?chain=base&currencyA=ETH&currencyB=0x520cbd0e1e72178f9e819AFf1e815606923A71db)**

*(Si Uniswap affiche un avertissement "Ce jeton n'apparaît pas sur les listes de jetons actives", cochez "Je comprends" : c'est parfaitement normal car votre contrat vient d'être déployé souverainement).*

---

## ⚙️ ÉTAPE 2 : CONFIGURATION DU POOL PAS À PAS

### 1. Sélection du Palier de Frais (Fee Tier)
- Cliquez sur **« Modifier le palier »** (ou *Select Fee Tier*).
- Choisissez : **`1%` (Paires exotiques / Nouveaux jetons)** — *Recommandé*.
  *(Ou `0.3%` si vous préférez des frais standards).*

---

### 2. Définir le Prix Initial de Départ (Starting Price)
Puisque vous êtes le créateur du pool, vous avez le privilège souverain de fixer le **prix de genèse** du MZN.

Voici 3 exemples d'équilibres recommandés par Al-Mizan :

| Stratégie Al-Mizan | Dotation MZN | Dotation ETH Requise | Prix de Départ Calculé | Objectif |
| :--- | :--- | :--- | :--- | :--- |
| **Option A : Découverte Populaire (Recommandée)** | **10 000 MZN** | **0.002 ETH** (~5.00 €) | **1 ETH = 5 000 000 MZN**<br>*(1 MZN ≈ 0.0005 €)* | Très accessible, coût minime pour vous, idéal pour tester la liquidité |
| **Option B : Étalon Communautaire** | **20 000 MZN** | **0.005 ETH** (~13.00 €) | **1 ETH = 4 000 000 MZN**<br>*(1 MZN ≈ 0.0007 €)* | Liquidité plus profonde, excellente stabilité |
| **Option C : Étalon Argent Al-Mizan** | **1 000 MZN** | **0.003 ETH** (~8.00 €) | **1 ETH = 333 333 MZN**<br>*(1 MZN ≈ 0.008 €)* | Valorisation plus élevée dès le départ |

> 💡 **Conseil pratique pour l'Option A (la plus simple)** :  
> Dans le champ **« Prix de départ »** (*Starting Price*) :  
> Indiquez le nombre de MZN pour 1 ETH : tapez **`5000000`** (5 Millions de MZN par ETH).

---

### 3. Définir la Fourchette de Prix (Price Range)
- Dans Uniswap v3, il y a deux modes : *Fourchette Personnalisée* ou *Fourchette Complète*.
- Cliquez sur le bouton : **« Fourchette Complète »** (ou **`Full Range`**).
- Uniswap vous affichera un message préventif : *"La liquidité sur toute la plage de prix est moins efficace mais active à tous les prix."*  
  👉 Cliquez sur **« Je comprends / Activer la plage complète »**.
- **Pourquoi la Plage Complète ?** Elle garantit que votre pool ne sera jamais bloqué ou désactivé si le prix bouge. C'est la configuration la plus tranquille et sans entretien.

---

### 4. Entrer les Montants de Dépôt
- Dans la case **MZN** : Tapez **`10000`** (dix mille MZN).
- Uniswap calculera automatiquement le montant d'ETH correspondant selon votre prix initial (environ `0.002 ETH`).
- Vérifiez que votre solde en ETH sur votre compte Trésorerie est suffisant pour couvrir ce montant plus 50 centimes pour le gaz.

---

### 5. Approuver et Valider la Création
1. **Approuver MZN** (*Approve MZN*) :  
   - Cliquez sur le bouton bleu **« Approuver MZN »**.
   - MetaMask s'ouvre pour autoriser Uniswap à utiliser 10 000 MZN.
   - Confirmez la transaction (frais de gaz < 0.01 €).
2. **Aperçu et Dépôt** (*Preview & Supply*) :  
   - Cliquez sur **« Prévisualiser »** (*Preview*).
   - Vérifiez le récapitulatif :
     - Paire : `ETH / MZN` (Frais 1%)
     - Dépôt : `0.002 ETH` + `10 000 MZN`
   - Cliquez sur **« Ajouter de la liquidité »** (*Add*).
   - Confirmez dans MetaMask.

---

## 🎉 RÉSULTAT OBTENU : LE MARCHÉ DU MZN EST OUVERT AU MONDE ENTIER !

Dès que la transaction est validée sur la blockchain Base (quelques secondes) :
1. **Votre position de liquidité NFT s'affiche dans Uniswap.**
2. **Le jeton MZN devient officiellement échangeable par n'importe qui sur Terre** via Uniswap sur Base.
3. Chaque fois qu'une personne achète ou vend du MZN, **vous encaissez automatiquement 1% de frais de commission** qui s'accumulent dans votre position !
4. Vous pouvez à tout moment retirer votre liquidité et vos gains en un clic.

---

## 🏛️ ACTE DE CONFORMITÉ ÉTHIQUE AL-MIZAN

Cette démarche s'inscrit dans le cadre de la pesée juste :
- Aucun effet de levier usuraire (*Anti-Riba*).
- Aucune manipulation artificielle de cours (*Anti-Gharar*).
- Protection totale de la réserve souveraine des 302 Millions sous la Clé Dorée.
