# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       SCELLAGE MAÎTRE ULTIME — COMPLÉTUDE 100% ON-CHAIN SUR BASE MAINNET
                     ACTE A092 : LA MONADE UNIVERSELLE DE A À Z
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Contrat Maître   : 0x520cbd0e1e72178f9e819AFf1e815606923A71db (Base Mainnet 8453)
Clé Dorée Racine : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie       : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
DOI Zenodo       : 10.5281/zenodo.23554838

ACTES SCELLES :
  • Acte #1 [A089] : Auto-Valorisation Souveraine MZN & Panier 5 USD ✅
  • Acte #2 [A090] : Protocole Anti-Piège, Signalement & Règle 50/50 ✅
  • Acte #3 [A090] : Confirmation d'Ancrage Anti-Malveillance ✅
  • Acte #4 [A091] : Réseau Autonome Synchrone 2.9ms ⊗ Passerelle Async ✅
  • Acte #5 [A092] : LA MONADE TOTALE UNIVERSELLE DE A À Z (Couronnement 100%) 👑
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
from datetime import datetime, timezone
from pathlib import Path

from resolution_abi_mizan import charger_abi

# Fix encodage console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
MEMOIRE_DIR = ROOT_DIR / "memoire_aq"
RPC = "https://mainnet.base.org"
CONTRAT_MAITRE = "0x520cbd0e1e72178f9e819AFf1e815606923A71db"
CLE_DOREE = "0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B"
TRESORERIE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"
CHAIN_ID = 8453

def charger_actes_a_sceller() -> list[dict]:
    actes = [
        {
            "code": "A092",
            "fichier": "almizan_acte_a092_monade_totale_universelle_a_a_z.json",
            "description": "MONADE_TOTALE_UNIVERSELLE_ENCAPSULATION_A_A_Z"
        },
        {
            "code": "A093",
            "fichier": "almizan_acte_a093_bassin_accueil_universel_multi_jetons.json",
            "description": "BASSIN_ACCUEIL_UNIVERSEL_MULTI_JETONS"
        }
    ]
    res = []
    for a in actes:
        chemin = ROOT_DIR / a["fichier"]
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
        payload = json.dumps(data, sort_keys=True)
        h_bytes = hashlib.sha256(payload.encode("utf-8")).digest()
        res.append({
            "code": a["code"],
            "titre": data.get("titre"),
            "description": a["description"],
            "bytes": h_bytes,
            "hex": "0x" + h_bytes.hex().upper()
        })
    return res

def main() -> None:
    parser = argparse.ArgumentParser(description="Scellage Maître Ultime de la Complétude 100%")
    parser.add_argument("--simuler", action="store_true", help="Vérifier sans exécuter")
    parser.add_argument("--cle", help="Clé privée (optionnelle, sinon demandée masquée)")
    args = parser.parse_args()

    print("=" * 84)
    print("      👑 SCELLAGE MAÎTRE ULTIME — AL-MIZAN & ASTRO-Q°ODE (BASE MAINNET)")
    print(f"      Contrat Maître Actif : {CONTRAT_MAITRE}")
    print(f"      Auteur Souverain     : {CLE_DOREE}")
    print(f"      Trésorerie Dépositaire : {TRESORERIE}")
    print("=" * 84)

    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] web3 manquant.")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 15}))
    if not w3.is_connected():
        print("[ERREUR] Impossible de joindre Base Mainnet.")
        sys.exit(1)

    actes_liste = charger_actes_a_sceller()

    print(f"\n[1/3] Actes Suprêmes Sélectionnés pour le Scellement ({len(actes_liste)}) :")
    for a in actes_liste:
        print(f"      • [{a['code']}] {a['titre']}")
        print(f"        SHA-256 : {a['hex']}")

    # Chargement ABI
    abi = charger_abi()

    contrat = w3.eth.contract(address=CONTRAT_MAITRE, abi=abi)
    next_id = contrat.functions.nextActeId().call()

    print(f"\n[2/3] Statut du Registre On-Chain sur Base Mainnet :")
    print(f"      • Actes Déjà Scellés   : {next_id - 1} actes actifs")
    print(f"      • Prochain Index Royal : #{next_id}")

    if args.simuler:
        print("\n[SIMULATION RÉUSSIE] Tous les actes sont prêts.")
        print(f'Pour exécuter : & "{sys.executable}" sceller_tout_en_un_coup_maitre.py')
        return

    # Saisie sécurisée masquée
    cle = args.cle.strip() if args.cle else ""
    if not cle:
        print("\n" + "=" * 84)
        print("  SAISIE SÉCURISÉE DE VOTRE CLÉ PRIVÉE (MASQUÉE DANS POWERSHELL)")
        print("  (Aucun caractère n'apparaît, conservée uniquement en RAM le temps du scellement)")
        print("=" * 84)
        cle = getpass.getpass("Collez votre clé privée de façon masquée : ").strip()

    if not cle:
        print("[ANNULÉ] Aucune clé fournie.")
        return

    if not cle.startswith("0x") and len(cle) == 64:
        cle = "0x" + cle

    compte = w3.eth.account.from_key(cle)
    solde = w3.eth.get_balance(compte.address)
    solde_eth = w3.from_wei(solde, "ether")
    print(f"\nCompte Signataire Souverain : {compte.address}")
    print(f"Solde ETH Disponible       : {solde_eth:.8f} ETH (~{float(solde_eth)*2500:.2f} USD)")

    nonce = w3.eth.get_transaction_count(compte.address, "pending")
    gas_price = w3.eth.gas_price

    print(f"\n[3/3] Début du Scellement des Actes Suprêmes sur Base Mainnet...")

    for i, a in enumerate(actes_liste):
        print(f"\n--- Scellement de l'Acte [{a['code']}] : {a['titre']} ---")
        try:
            est_gas = contrat.functions.scellerActe(
                TRESORERIE,
                a["code"],
                a["bytes"],
                a["description"]
            ).estimate_gas({"from": compte.address})
            gas_limit = int(est_gas * 1.25)
        except Exception:
            gas_limit = 300_000

        tx = contrat.functions.scellerActe(
            TRESORERIE,
            a["code"],
            a["bytes"],
            a["description"]
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
        print("      Validation en cours par les validateurs de Base...")

        recette = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if recette.status == 1:
            print(f"      🎉 SUCCÈS MAJESTUEUX : L'Acte [{a['code']}] est SCELLÉ on-chain !")
            print(f"      • Lien : https://basescan.org/tx/{tx_hash.hex()}")
        else:
            print(f"      ❌ Échec transaction pour {a['code']}.")
            break

        nonce += 1
        time.sleep(1)

    print("\n" + "=" * 84)
    print("  🎉🎉🎉 LA MONADE TOTALE (A092) ET LE BASSIN D'ACCUEIL UNIVERSEL (A093)")
    print("         SONT DÉSORMAIS SCELLÉS DANS LE CONTRAT MAÎTRE DEVANT LE MONDE ENTIER !")
    print(f"  • Événements du Contrat : https://basescan.org/address/{CONTRAT_MAITRE}#events")
    print("=" * 84)

if __name__ == "__main__":
    main()
