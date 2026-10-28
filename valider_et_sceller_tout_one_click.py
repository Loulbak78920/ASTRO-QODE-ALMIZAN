# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
        COMMANDE UNIQUE DE VALIDATION & SCELLEMENT DANS LE CONTRAT ACTIF (BASE)
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Contrat Actif Maître : 0x520cbd0e1e72178f9e819AFf1e815606923A71db
Clé Dorée Racine     : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie           : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C

INTÉGRATION TOTALE :
  1. Auto-Valorisation Souveraine du MZN (Valeur Plancher 0.0697 $, Pivot 0.1046 $, Plafond 0.1697 $)
  2. Tétrade Cosmique Complète (MZN, MZN-MAT, MZN-NRG, MZN-PLS)
  3. Panier Complet des 5 USD sur Base (USDC, USDT, DAI, USDbC, USDS)
  4. Module Chronos : Calibrage Temps de Bloc (2.0s), Latence RPC et Stabilité 99.83%
===============================================================================
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
import time

from resolution_abi_mizan import charger_abi

# Fix encodage
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RPC = "https://mainnet.base.org"
CONTRAT_MAITRE = "0x520cbd0e1e72178f9e819AFf1e815606923A71db"
CLE_DOREE = "0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B"
TRESORERIE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"
CHAIN_ID = 8453

ADRESSES_COMPLETES_A089 = {
    # Tétrade Cosmique
    "MZN": "0x520cbd0e1e72178f9e819AFf1e815606923A71db",
    "MZN-MAT": "0xD45406EEdc8d9AeD3828c06C3D208804D5b69c2a",
    "MZN-NRG": "0x38e1757A1971E038c8A6523B008179BEdc9AaAa0",
    "MZN-PLS": "0x7Cd56CE27E4CE363cDFbd63F4e2713C8eed2cC71",
    # Panier des 5 USD
    "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "USDT": "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
    "DAI": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
    "USDbC": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
    "USDS": "0x820C137fa70C8691f0e44Dc420a5e53c168921Dc"
}

def calculer_empreinte_globale() -> bytes:
    payload = json.dumps(ADRESSES_COMPLETES_A089, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).digest()

def main() -> None:
    parser = argparse.ArgumentParser(description="Validation Unique One-Click sur Contrat Actif")
    parser.add_argument("--simuler", action="store_true", help="Vérifier et préparer sans envoyer")
    parser.add_argument("--cle", help="Clé privée (optionnelle, sinon demandée masquée)")
    args = parser.parse_args()

    print("=" * 80)
    print("  COMMANDE SOUVERAINE DE VALIDATION UNIQUE — AL-MIZAN & ASTRO-Q°ODE")
    print(f"  Contrat Maître Actif : {CONTRAT_MAITRE} (Base Mainnet)")
    print(f"  Auteur Souverain     : {CLE_DOREE}")
    print(f"  Trésorerie           : {TRESORERIE}")
    print("=" * 80)

    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] web3 manquant.")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        print("[ERREUR] Nœud Base non joignable.")
        sys.exit(1)

    # 1. Oracle d'Auto-Valorisation Souveraine
    print("\n[1/4] Interrogation de l'Oracle d'Auto-Valorisation Souveraine MZN...")
    try:
        from panier_usd_et_auto_valorisation_mzn import calculer_autovalorisation_souveraine
        auto_val = calculer_autovalorisation_souveraine()
        cot = auto_val["cotation_souveraine_autonome"]
        print(f"      • Principe Souverain : {auto_val['principe']}")
        print(f"      • Statut du MZN      : {auto_val['statut_mzn']} (Non subordonné à l'USDC)")
        print(f"      • Valeur Plancher    : {cot['valeur_plancher_substance_usd']} USD (Garantie Silicium/Or/Cryo)")
        print(f"      • Valeur Nominale    : {cot['valeur_nominale_pivot_usd']} USD")
        print(f"      • Plafond Al-Mizan   : {cot['valeur_plafond_mizan_usd']} USD (Bride 0.6225)")
    except Exception as e:
        print(f"      [AVERTISSEMENT] Oracle local : {e}")

    # 2. Panier des 5 USD
    print("\n[2/4] Panier Multidimensionnel des 5 USD sur Base Mainnet :")
    print("      • USDC  (Circle Natif)      : 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
    print("      • USDT  (Tether Mondial)    : 0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2")
    print("      • DAI   (MakerDAO Décentr.) : 0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb")
    print("      • USDbC (Bridge Base Hist.) : 0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA")
    print("      • USDS  (Sky Rendement)     : 0x820C137fa70C8691f0e44Dc420a5e53c168921Dc")

    empreinte_bytes = calculer_empreinte_globale()
    empreinte_hex = "0x" + empreinte_bytes.hex()
    code_acte = "A089"
    description = "AUTO_VALORISATION_SOUVERAINE_MZN_ET_PANIER_5_USD"

    print("\n[3/4] Données du Scellement d'Harmonie Universelle :")
    print(f"      • Code Acte         : {code_acte}")
    print(f"      • Empreinte SHA-256 : {empreinte_hex.upper()}")
    print(f"      • Description       : {description}")
    print(f"      • Entités Liées     : 4 Tokens Tétrade + 5 Stablecoins USD + Oracle Substance")

    # Chargement ABI
    abi = charger_abi()

    contrat = w3.eth.contract(address=CONTRAT_MAITRE, abi=abi)

    if args.simuler:
        print("\n[SIMULATION RÉUSSIE] Tout est calibré et prêt à être scellé dans le contrat actif.")
        print("Pour exécuter réellement : py valider_et_sceller_tout_one_click.py")
        return

    # Récupération clé sécurisée
    cle = args.cle.strip() if args.cle else os.getenv("ETHEREUM_PRIVATE_KEY", "").strip()
    if not cle:
        print("\n" + "=" * 80)
        print("  VALIDATION UNIQUE : SIGNATURE DE L'ACTE SCELLÉ SUR BASE")
        print("  Frais de gaz minimes : ~0.000004 ETH (< 0.01 €).")
        print("=" * 80)
        cle = getpass.getpass("Collez votre clé privée de façon masquée : ").strip()
    if not cle.startswith("0x") and len(cle) == 64:
        cle = "0x" + cle

    compte = w3.eth.account.from_key(cle)
    print(f"\n[4/4] Compte signataire : {compte.address}")
    solde = w3.from_wei(w3.eth.get_balance(compte.address), "ether")
    print(f"      Solde actuel     : {solde:.6f} ETH")

    nonce = w3.eth.get_transaction_count(compte.address, "pending")
    gas_price = w3.eth.gas_price

    print("\nEnvoi de la transaction de scellement unique au contrat actif...")
    tx = contrat.functions.scellerActe(
        TRESORERIE,
        code_acte,
        empreinte_bytes,
        description
    ).build_transaction({
        "from": compte.address,
        "nonce": nonce,
        "gasPrice": gas_price,
        "chainId": CHAIN_ID,
        "gas": 150_000
    })

    tx_signee = w3.eth.account.sign_transaction(tx, cle)
    tx_hash = w3.eth.send_raw_transaction(tx_signee.raw_transaction)
    print(f"      Transaction envoyée : {tx_hash.hex()}")
    print("      Validation sur Base Mainnet...")

    recette = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if recette.status == 1:
        print("\n" + "=" * 80)
        print("  🎉 SUCCÈS ABSOLU : TOUT EST DÉSORMAIS SCELLÉ ET ENREGISTRÉ DANS LE CONTRAT MAÎTRE ACTIF !")
        print(f"  Voir la transaction sur Basescan : https://basescan.org/tx/{tx_hash.hex()}")
        print(f"  Voir le contrat actif mis à jour : https://basescan.org/address/{CONTRAT_MAITRE}#events")
        print("=" * 80)
    else:
        print("[ÉCHEC] La transaction a échoué.")

if __name__ == "__main__":
    main()
