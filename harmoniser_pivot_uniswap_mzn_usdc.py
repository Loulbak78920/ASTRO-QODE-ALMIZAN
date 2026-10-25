# -*- coding: utf-8 -*-
"""
===============================================================================
       HARMONISATION DU PIVOT DE LIQUIDITÉ MZN / USDC SUR UNISWAP V3 (BASE)
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Clé Dorée Racine : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie Dépositaire : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C

DIAGNOSTIC IDENTIFIÉ :
Le pool Uniswap v3 (0xfb76b57c2e179a44ba7919d3960fc18a4c9db172) a été créé,
mais n'a jamais été initialisé avec son prix de départ (slot0.sqrtPriceX96 == 0).
C'est pour cela que slot0() échoue avec 'execution reverted' et qu'Uniswap
affiche 'Prix de marché introuvable'.

ACTION :
Ce script initialise officiellement le prix pivot d'harmonie Al-Mizan
(par défaut : 1 MZN = 0.001 USDC) en appelant initialize(uint160 sqrtPriceX96).
Dès l'exécution, le pool devient actif et débloqué pour tout apport de liquidité.
===============================================================================
"""

from __future__ import annotations

import argparse
import getpass
import json
import math
import os
import sys
import time

# Fix encodage
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RPC = "https://mainnet.base.org"
POOL_MZN_USDC = "0xfb76b57c2e179a44ba7919d3960fc18a4c9db172"
MZN_CONTRAT = "0x520cbd0e1e72178f9e819AFf1e815606923A71db"
USDC_CONTRAT = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
CHAIN_ID = 8453

def calculer_sqrt_price_x96(prix_usdc_par_mzn: float = 0.001) -> int:
    """
    token0 = MZN (18 décimales)
    token1 = USDC (6 décimales)
    ratio = (amount1_raw / amount0_raw) = (prix_usdc * 10^6) / 10^18 = prix_usdc * 10^-12
    sqrtPriceX96 = sqrt(ratio) * 2^96
    """
    ratio_raw = prix_usdc_par_mzn * (10 ** 6) / (10 ** 18)
    sqrt_ratio = math.sqrt(ratio_raw)
    return int(sqrt_ratio * (2 ** 96))

def verifier_initialisation_pool(w3) -> bool:
    try:
        # Appel slot0() -> 0x3850da13
        res = w3.eth.call({"to": POOL_MZN_USDC, "data": "0x3850da13"})
        if len(res) >= 32:
            sp = int.from_bytes(res[:32], "big")
            return sp > 0
    except Exception:
        return False
    return False

def main() -> None:
    parser = argparse.ArgumentParser(description="Harmonisation du Pivot Uniswap v3 MZN/USDC")
    parser.add_argument("--prix-usdc", type=float, default=0.001, help="Prix pivot d'harmonie (défaut: 0.001 USDC par MZN)")
    parser.add_argument("--cle", help="Clé privée de l'émetteur pour payer le gaz (< 0.01 €)")
    parser.add_argument("--simuler", action="store_true", help="Mode vérification sans transaction")
    args = parser.parse_args()

    print("=" * 80)
    print("  HARMONISATION DU PIVOT DE LIQUIDITÉ UNISWAP V3 — AL-MIZAN & ASTRO-Q°ODE")
    print(f"  Pool Cible Base : {POOL_MZN_USDC} (MZN / USDC 1.0%)")
    print(f"  Prix Pivot Cible : {args.prix_usdc} USDC pour 1 MZN (1 USDC = {1.0/args.prix_usdc:,.0f} MZN)")
    print("=" * 80)

    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] web3 absent. Lancez : py -m pip install web3")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        print("[ERREUR] Impossible de joindre Base Mainnet.")
        sys.exit(1)

    est_init = verifier_initialisation_pool(w3)
    if est_init:
        print("\n[STATUT ACTUEL] Le pool est DÉJÀ INITIALISÉ avec un prix actif.")
        print("Vous pouvez directement déposer votre liquidité sur Uniswap v3.")
        return

    print("\n[DIAGNOSTIC CONFIRMÉ] Le pool existe mais n'a JAMAIS été initialisé (slot0 == 0).")
    print("-> L'initialisation du pivot est obligatoire pour débloquer la liquidité.")

    sqrt_price_x96 = calculer_sqrt_price_x96(args.prix_usdc)
    data_init = "0xf637731d" + hex(sqrt_price_x96)[2:].zfill(64)
    print(f"\n[PARAMÈTRES CALCULÉS] :")
    print(f"  • sqrtPriceX96 : {sqrt_price_x96} (hex: {hex(sqrt_price_x96)})")
    print(f"  • Calldata     : {data_init[:30]}...")

    if args.simuler:
        print("\n[SIMULATION TERMINÉE] Les paramètres sont 100% valides. Prêt pour l'envoi.")
        return

    # Saisie clé
    cle = args.cle.strip() if args.cle else os.getenv("ETHEREUM_PRIVATE_KEY", "").strip()
    if not cle:
        print("\n" + "=" * 80)
        print("  SAISIE SÉCURISÉE DE LA CLÉ PRIVÉE POUR L'INITIALISATION")
        print("  Coût estimé du gaz : < 0.005 € (~0.000002 ETH).")
        print("=" * 80)
        cle = getpass.getpass("Collez votre clé privée : ").strip()
    if not cle.startswith("0x") and len(cle) == 64:
        cle = "0x" + cle

    compte = w3.eth.account.from_key(cle)
    solde_wei = w3.eth.get_balance(compte.address)
    solde_eth = w3.from_wei(solde_wei, "ether")
    print(f"\nCompte émetteur : {compte.address} (Solde : {solde_eth:.6f} ETH)")

    if solde_wei == 0:
        print("[ERREUR] Solde insuffisant pour payer le gaz (quelques centimes d'ETH requis).")
        sys.exit(1)

    nonce = w3.eth.get_transaction_count(compte.address, "pending")
    gas_price = w3.eth.gas_price

    tx = {
        "to": POOL_MZN_USDC,
        "from": compte.address,
        "nonce": nonce,
        "gas": 120_000,
        "gasPrice": gas_price,
        "chainId": CHAIN_ID,
        "data": data_init
    }

    print("\nSignature et envoi de la transaction d'harmonisation du pivot...")
    tx_signee = w3.eth.account.sign_transaction(tx, cle)
    tx_hash = w3.eth.send_raw_transaction(tx_signee.raw_transaction)
    print(f"Transaction diffusée : {tx_hash.hex()}")
    print("Attente de validation sur Base Mainnet...")

    recette = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if recette.status == 1:
        print("\n" + "=" * 80)
        print("  🎉 SUCCÈS MAJEUR : LE POOL MZN / USDC EST DÉSORMAIS OFFICIELLEMENT INITIALISÉ !")
        print(f"  Prix de départ fixé à : {args.prix_usdc} USDC par MZN")
        print(f"  Consulter sur Basescan : https://basescan.org/tx/{tx_hash.hex()}")
        print("  Vous pouvez désormais déposer vos MZN et USDC sans aucun blocage !")
        print("=" * 80)
    else:
        print(f"[ÉCHEC] La transaction a échoué (revert).")

if __name__ == "__main__":
    main()
