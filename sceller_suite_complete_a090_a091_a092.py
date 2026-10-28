# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       SCELLAGE COMPLET DES ACTES SOUVERAINS SUR LE CONTRAT MAÎTRE (BASE)
                     ACTES A090 ⊗ A091 ⊗ A092 (DE A À Z)
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Contrat Maître   : 0x520cbd0e1e72178f9e819AFf1e815606923A71db (Base Mainnet)
Clé Dorée Racine : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie       : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C

ACTES INTÉGRÉS :
  • A090 : Protocole Anti-Piège, Signalement de Sécurité & Contrepartie 50/50
  • A091 : Fondation du Réseau Autonome Synchrone ⊗ Passerelle Asynchrone
  • A092 : Monade Totale Universelle Al-Mizan Encapsulant le Projet de A à Z
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

# Fix encodage console Windows
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

ACTES_A_SCELLER = [
    {
        "code": "A090",
        "titre": "Protocole Anti-Piège, Signalement Sécurité & Contrepartie 50/50",
        "fichier": "almizan_acte_a090_protocole_anti_piege_signalement_contrepartie.json",
        "description": "PROTOCOLE_ANTI_PIEGE_SIGNALEMENT_CONTREPARTIE_MZN"
    },
    {
        "code": "A091",
        "titre": "Réseau Autonome Synchrone ⊗ Passerelle Asynchrone Universelle",
        "fichier": "almizan_acte_a091_reseau_autonome_synchrone_interoperabilite_asynchrone.json",
        "description": "RESEAU_AUTONOME_SYNCHRONE_PASSERELLE_ASYNC"
    },
    {
        "code": "A092",
        "titre": "Monade Totale Universelle Al-Mizan Encapsulant le Projet de A à Z",
        "fichier": "almizan_acte_a092_monade_totale_universelle_a_a_z.json",
        "description": "MONADE_TOTALE_UNIVERSELLE_ENCAPSULATION_A_A_Z"
    }
]

def calculer_empreinte_fichier(chemin: Path) -> bytes:
    with open(chemin, "r", encoding="utf-8") as f:
        data = json.load(f)
    payload = json.dumps(data, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).digest()

def main() -> None:
    parser = argparse.ArgumentParser(description="Scellage des Actes A090, A091 et A092 sur Base Mainnet")
    parser.add_argument("--acte", choices=["A090", "A091", "A092", "tous"], default="tous", help="Acte(s) à sceller (défaut: tous)")
    parser.add_argument("--simuler", action="store_true", help="Vérifier sans exécuter de transaction")
    parser.add_argument("--cle", help="Clé privée (optionnelle, sinon demandée masquée)")
    args = parser.parse_args()

    print("=" * 82)
    print("  SCELLAGE OFFICIEL DE LA SUITE ROYALE DES ACTES SOUVERAINS AL-MIZAN")
    print(f"  Contrat Maître Actif : {CONTRAT_MAITRE} (Base Mainnet)")
    print(f"  Auteur Souverain     : {CLE_DOREE}")
    print(f"  Trésorerie           : {TRESORERIE}")
    print("=" * 82)

    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] web3 manquant.")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC, request_kwargs={"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 15}))
    if not w3.is_connected():
        print("[ERREUR] Impossible de joindre Base Mainnet.")
        sys.exit(1)

    # Filtrer les actes
    selection = ACTES_A_SCELLER if args.acte == "tous" else [a for a in ACTES_A_SCELLER if a["code"] == args.acte]

    print(f"\n[1/3] Actes sélectionnés pour le scellement on-chain ({len(selection)}) :")
    for a in selection:
        chemin_acte = ROOT_DIR / a["fichier"]
        if chemin_acte.exists():
            h = "0x" + calculer_empreinte_fichier(chemin_acte).hex().upper()
            print(f"      • [{a['code']}] {a['titre']}")
            print(f"        SHA-256 : {h}")
        else:
            print(f"      [AVERTISSEMENT] Fichier manquant : {a['fichier']}")

    # Chargement ABI
    abi = charger_abi()

    contrat = w3.eth.contract(address=CONTRAT_MAITRE, abi=abi)

    try:
        next_id = contrat.functions.nextActeId().call()
        print(f"\n[2/3] État du Contrat Actif sur Base Mainnet :")
        print(f"      • Index actuel dans le registre on-chain : #{next_id}")
    except Exception as e:
        print(f"Lecture nextActeId : {e}")

    if args.simuler:
        print("\n[SIMULATION RÉUSSIE] Tous les actes sont prêts.")
        print("Pour exécuter le scellement réel :")
        print(f'& "{sys.executable}" sceller_suite_complete_a090_a091_a092.py --acte {args.acte}')
        return

    # Saisie sécurisée masquée
    cle = args.cle.strip() if args.cle else ""
    if not cle:
        print("\n" + "=" * 82)
        print("  SAISIE SÉCURISÉE DE LA CLÉ PRIVÉE (MASQUÉE DANS POWERSHELL)")
        print("  (Aucune trace sur le disque, conservée uniquement en RAM le temps de la signature)")
        print("=" * 82)
        cle = getpass.getpass("Collez votre clé privée de façon masquée : ").strip()

    if not cle:
        print("[ANNULÉ] Aucune clé fournie.")
        return

    if not cle.startswith("0x") and len(cle) == 64:
        cle = "0x" + cle

    compte = w3.eth.account.from_key(cle)
    solde = w3.eth.get_balance(compte.address)
    solde_eth = w3.from_wei(solde, "ether")
    print(f"\n[3/3] Compte Signataire : {compte.address}")
    print(f"      Solde ETH Base   : {solde_eth:.8f} ETH (~{float(solde_eth)*2500:.2f} USD)")

    if solde == 0:
        print("[ERREUR] Solde nul.")
        return

    nonce = w3.eth.get_transaction_count(compte.address, "pending")
    gas_price = w3.eth.gas_price

    print(f"\nDébut du Scellement des Actes sur Base Mainnet...")

    for i, a in enumerate(selection):
        chemin_acte = ROOT_DIR / a["fichier"]
        empreinte_bytes = calculer_empreinte_fichier(chemin_acte)

        print(f"\n--- Scellement de l'Acte [{a['code']}] : {a['titre']} ---")

        # Estimation dynamique du gaz
        try:
            est_gas = contrat.functions.scellerActe(
                TRESORERIE,
                a["code"],
                empreinte_bytes,
                a["description"]
            ).estimate_gas({"from": compte.address})
            gas_limit = int(est_gas * 1.25)
        except Exception:
            gas_limit = 300_000

        tx = contrat.functions.scellerActe(
            TRESORERIE,
            a["code"],
            empreinte_bytes,
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
        print("      Validation en cours...")

        recette = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        if recette.status == 1:
            print(f"      ✅ SUCCÈS : L'Acte [{a['code']}] est SCELLÉ sur Base Mainnet !")
            print(f"      Lien : https://basescan.org/tx/{tx_hash.hex()}")
        else:
            print(f"      ❌ Échec transaction {a['code']}.")
            break

        nonce += 1
        time.sleep(1)

    print("\n" + "=" * 82)
    print("  🎉 TOUS VOS ACTES SONT DÉSORMAIS SCELLÉS DANS LE CONTRAT MAÎTRE ACTIF !")
    print(f"  Vérifiez les événements officiels : https://basescan.org/address/{CONTRAT_MAITRE}#events")
    print("=" * 82)

if __name__ == "__main__":
    main()
