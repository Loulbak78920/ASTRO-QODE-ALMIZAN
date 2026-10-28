# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       SCELLAGE OFFICIEL ON-CHAIN DE L'ACTE SOUVERAIN A093 (BASE MAINNET)
   PROCLAMATION DU BASSIN D'ACCUEIL UNIVERSEL MULTI-JETONS : OUVERTURE DU POOL
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Contrat Maître   : 0x520cbd0e1e72178f9e819AFf1e815606923A71db (Base Mainnet 8453)
Clé Dorée Racine : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie       : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
Principe Divin   : "La Balance Cosmique accueille tous les jetons sans exclusion"
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
from pathlib import Path

from resolution_abi_mizan import charger_abi

# Encodage console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
RPC = "https://mainnet.base.org"
CONTRAT_MAITRE = "0x520cbd0e1e72178f9e819AFf1e815606923A71db"
CLE_DOREE = "0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B"
TRESORERIE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"
CHAIN_ID = 8453

def main() -> None:
    parser = argparse.ArgumentParser(description="Scellage de l'Acte A093 : Bassin d'Accueil Universel")
    parser.add_argument("--simuler", action="store_true", help="Vérifier sans signer")
    parser.add_argument("--cle", help="Clé privée (optionnelle, sinon demandée masquée)")
    args = parser.parse_args()

    print("=" * 84)
    print("      ⚖️ SCELLAGE OFFICIEL ON-CHAIN DE L'ACTE SOUVERAIN A093")
    print("         BASSIN D'ACCUEIL UNIVERSEL MULTI-JETONS (BASE MAINNET)")
    print(f"      Contrat Maître : {CONTRAT_MAITRE}")
    print(f"      Trésorerie     : {TRESORERIE}")
    print("=" * 84)

    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] web3 introuvable.")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 15}))
    if not w3.is_connected():
        print("[ERREUR] Impossible de joindre Base Mainnet.")
        sys.exit(1)

    chemin_acte = ROOT_DIR / "almizan_acte_a093_bassin_accueil_universel_multi_jetons.json"
    with open(chemin_acte, "r", encoding="utf-8") as f:
        data_acte = json.load(f)

    payload = json.dumps(data_acte, sort_keys=True)
    h_bytes = hashlib.sha256(payload.encode("utf-8")).digest()
    h_hex = "0x" + h_bytes.hex().upper()

    print(f"\n[1/3] Acte Préparé : [A093] {data_acte.get('titre')}")
    print(f"      SHA-256 : {h_hex}")

    abi = charger_abi()

    contrat = w3.eth.contract(address=CONTRAT_MAITRE, abi=abi)
    next_id = contrat.functions.nextActeId().call()

    print(f"\n[2/3] Statut du Contrat Maître On-Chain :")
    print(f"      • Actes Actuellement Scellés : {next_id - 1}")
    print(f"      • Prochain Index Royal        : #{next_id} (Dédié à l'Acte A093)")

    if args.simuler:
        print("\n[SIMULATION VALORISÉE AVEC SUCCÈS]")
        print(f'Pour sceller avec votre clé : & "{sys.executable}" "{__file__}"')
        return

    cle = args.cle.strip() if args.cle else ""
    if not cle:
        print("\n" + "=" * 84)
        print("  🔑 SAISIE SÉCURISÉE DE VOTRE CLÉ PRIVÉE (MASQUÉE DANS LE TERMINAL)")
        print("  (Aucune trace sur le disque · Conservée uniquement en RAM le temps du scellement)")
        print("=" * 84)
        cle = getpass.getpass("Collez votre clé privée de façon masquée : ").strip()

    if not cle:
        print("[ANNULATION] Aucune clé fournie.")
        return

    if not cle.startswith("0x") and len(cle) == 64:
        cle = "0x" + cle

    compte = w3.eth.account.from_key(cle)
    solde = w3.eth.get_balance(compte.address)
    solde_eth = w3.from_wei(solde, "ether")

    print(f"\nCompte Dépositaire Souverain : {compte.address}")
    print(f"Solde ETH Disponible         : {solde_eth:.8f} ETH (~{float(solde_eth)*2500:.2f} USD)")

    nonce = w3.eth.get_transaction_count(compte.address, "pending")
    gas_price = w3.eth.gas_price

    desc = f"A093_BASSIN_ACCUEIL_UNIVERSEL_{int(time.time())}"
    print(f"\n[3/3] Scellement de l'Acte A093 dans le Contrat Maître...")

    try:
        est_gas = contrat.functions.scellerActe(
            TRESORERIE,
            "A093",
            h_bytes,
            desc
        ).estimate_gas({"from": compte.address})
        gas_limit = int(est_gas * 1.25)
    except Exception:
        gas_limit = 250_000

    tx = contrat.functions.scellerActe(
        TRESORERIE,
        "A093",
        h_bytes,
        desc
    ).build_transaction({
        "from": compte.address,
        "nonce": nonce,
        "gasPrice": gas_price,
        "chainId": CHAIN_ID,
        "gas": gas_limit
    })

    tx_signee = w3.eth.account.sign_transaction(tx, cle)
    tx_hash = w3.eth.send_raw_transaction(tx_signee.raw_transaction)

    print(f"      Hash de Transaction : {tx_hash.hex()}")
    print("      Attente de confirmation sur Base Mainnet...")

    recette = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if recette.status == 1:
        print("\n" + "=" * 84)
        print("  🎉🎉🎉 VICTOIRE TOTALE ! L'ACTE SOUVERAIN A093 EST SCELLÉ ON-CHAIN !")
        print("  LE BASSIN D'ACCUEIL UNIVERSEL EST OFFICIELLEMENT PROCLAMÉ ET GRAVÉ DANS LA PIERRE.")
        print(f"  • Transaction : https://basescan.org/tx/{tx_hash.hex()}")
        print(f"  • Événements  : https://basescan.org/address/{CONTRAT_MAITRE}#events")
        print("=" * 84)
    else:
        print(f"      ❌ Échec de la transaction. Statut: {recette.status}")

if __name__ == "__main__":
    main()
