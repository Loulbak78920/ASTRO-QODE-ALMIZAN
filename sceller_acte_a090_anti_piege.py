# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       SCELLAGE SOUVERAIN DE L'ACTE A090 DANS LE CONTRAT INTELLIGENT MAÎTRE
===============================================================================
Projet : AL-MIZAN & ASTRO-Q°ODE (Base Mainnet 8453)
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Contrat Maître Actif : 0x520cbd0e1e72178f9e819AFf1e815606923A71db
Clé Dorée Racine     : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie           : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C

ACTE A090 :
  PROTOCOLE SOUVERAIN ANTI-PIÈGE & SERVICE DE SIGNALEMENT DE SÉCURITÉ
  AVEC CONTREPARTIE COMMERCIALE 50/50 ET PRIME MZN
===============================================================================
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys

from resolution_abi_mizan import charger_abi

# Configuration encodage console Windows
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

def charger_acte_a090() -> dict:
    chemin_local = os.path.join(os.path.dirname(__file__), "almizan_acte_a090_protocole_anti_piege_signalement_contrepartie.json")
    with open(chemin_local, "r", encoding="utf-8") as f:
        return json.load(f)

def calculer_empreinte_acte(acte: dict) -> bytes:
    payload = json.dumps(acte, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).digest()

def main() -> None:
    parser = argparse.ArgumentParser(description="Scellage Unique de l'Acte A090 dans le Contrat Maître Actif")
    parser.add_argument("--simuler", action="store_true", help="Vérifier la calibration sans signer de transaction")
    parser.add_argument("--cle", help="Clé privée (optionnelle, sinon demandée masquée sans fichier sur disque)")
    args = parser.parse_args()

    print("=" * 82)
    print("  SCELLEMENT SOUVERAIN DIRECT DANS LE CONTRAT INTELLIGENT DU PROJET")
    print(f"  Contrat Maître Actif : {CONTRAT_MAITRE} (Base Mainnet)")
    print(f"  Auteur Souverain     : {CLE_DOREE}")
    print(f"  Trésorerie           : {TRESORERIE}")
    print(f"  RPC Réseau Public    : {RPC}")
    print("=" * 82)

    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] Le paquet web3 est manquant.")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 15}))
    if not w3.is_connected():
        print("[ERREUR] Impossible de joindre le nœud public Base Mainnet.")
        sys.exit(1)

    acte = charger_acte_a090()
    code_acte = acte.get("code_acte", "A090")
    titre = acte.get("titre", "")
    description = "PROTOCOLE_ANTI_PIEGE_SIGNALEMENT_CONTREPARTIE_MZN"
    empreinte_bytes = calculer_empreinte_acte(acte)
    empreinte_hex = "0x" + empreinte_bytes.hex()

    print("\n[1/3] Acte Al-Mizan Prêt pour l'Intégration On-Chain :")
    print(f"      • Code Acte         : {code_acte}")
    print(f"      • Titre             : {titre}")
    print(f"      • Description       : {description}")
    print(f"      • Empreinte SHA-256 : {empreinte_hex.upper()}")
    print("      • Règle Commerciale : 50% Auteur / 50% Détecteur (Anti-Usure 0%)")
    print("      • Invariants Mizan  : Bride 0.6225 | Ligne Réf 0.122 | Plafond 0.6015")

    # Chargement de l'ABI officielle existante
    try:
        abi = charger_abi()
    except FileNotFoundError:
        # Fallback ABI minimale
        abi = [
            {"inputs":[{"internalType":"address","name":"destinataire","type":"address"},{"internalType":"string","name":"codeActe","type":"string"},{"internalType":"bytes32","name":"sha256Empreinte","type":"bytes32"},{"internalType":"string","name":"description","type":"string"}],"name":"scellerActe","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
            {"inputs":[],"name":"nextActeId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
        ]

    contrat = w3.eth.contract(address=CONTRAT_MAITRE, abi=abi)

    try:
        next_id = contrat.functions.nextActeId().call()
        print(f"\n[2/3] État du Contrat Actif on-chain :")
        print(f"      • Prochain Index d'Acte : #{next_id}")
    except Exception as e:
        print(f"[AVERTISSEMENT] Lecture nextActeId : {e}")

    if args.simuler:
        print("\n[SIMULATION RÉUSSIE] Toutes les données ont été extraites avec succès de la machine.")
        print("Pour exécuter la transaction de scellement sur Base Mainnet :")
        print(f'& "{sys.executable}" sceller_acte_a090_anti_piege.py')
        return

    # Saisie sécurisée de la clé privée sans aucun fichier .env
    cle = args.cle.strip() if args.cle else ""
    if not cle:
        print("\n" + "=" * 82)
        print("  VALIDATION DIRECTE SUR POWERSHELL : SAISIE SÉCURISÉE MASQUÉE")
        print("  (Aucune écriture sur le disque, 0 fichier .env, clé protégée en mémoire)")
        print("  Frais de gaz minimes : ~0.000004 ETH (< 0.01 €)")
        print("=" * 82)
        cle = getpass.getpass("Collez votre clé privée de façon masquée : ").strip()

    if not cle:
        print("[ANNULÉ] Aucune clé fournie.")
        return

    if not cle.startswith("0x") and len(cle) == 64:
        cle = "0x" + cle

    compte = w3.eth.account.from_key(cle)
    solde_eth = w3.from_wei(w3.eth.get_balance(compte.address), "ether")
    print(f"\n[3/3] Compte Signataire Détecté : {compte.address}")
    print(f"      Solde ETH sur Base        : {solde_eth:.6f} ETH")

    nonce = w3.eth.get_transaction_count(compte.address, "pending")
    gas_price = w3.eth.gas_price

    # Estimation dynamique du gaz avec marge de sécurité
    try:
        gas_estime = contrat.functions.scellerActe(
            TRESORERIE,
            code_acte,
            empreinte_bytes,
            description
        ).estimate_gas({"from": compte.address})
        gas_limit = int(gas_estime * 1.25)
    except Exception as e:
        gas_limit = 300_000

    print(f"      Gas Limit calibré : {gas_limit} (Estimation réelle : ~236 000)")
    cout_total = gas_limit * gas_price
    print(f"      Coût estimé tx    : {w3.from_wei(cout_total, 'ether'):.8f} ETH")

    if w3.eth.get_balance(compte.address) < cout_total:
        manque = cout_total - w3.eth.get_balance(compte.address)
        print(f"\n[ATTENTION] Solde insuffisant pour couvrir le gaz exact :")
        print(f"      Solde actuel : {w3.from_wei(w3.eth.get_balance(compte.address), 'ether'):.8f} ETH")
        print(f"      Requis       : {w3.from_wei(cout_total, 'ether'):.8f} ETH")
        print(f"      Il manque    : {w3.from_wei(manque, 'ether'):.8f} ETH (~0.002 €)")
        print(f"Envoyez une fraction infime d'ETH sur {compte.address} pour valider le scellement.")
        return

    print("\nEnvoi de la transaction de scellement au Contrat Maître MZN...")
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
        "gas": gas_limit
    })

    tx_signee = w3.eth.account.sign_transaction(tx, cle)
    tx_hash = w3.eth.send_raw_transaction(tx_signee.raw_transaction)
    print(f"      Transaction broadcastée : {tx_hash.hex()}")
    print("      Attente de validation sur Base Mainnet...")

    recette = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    if recette.status == 1:
        print("\n" + "=" * 82)
        print("  🎉 SUCCÈS ABSOLU : L'ACTE A090 EST MAINTENANT SCELLÉ DANS LE CONTRAT MAÎTRE ACTIF !")
        print(f"  • Transaction Basescan : https://basescan.org/tx/{tx_hash.hex()}")
        print(f"  • Événements du Contrat : https://basescan.org/address/{CONTRAT_MAITRE}#events")
        print("=" * 82)
    else:
        print("[ÉCHEC] La transaction a été rejetée sur la chaîne.")

if __name__ == "__main__":
    main()
