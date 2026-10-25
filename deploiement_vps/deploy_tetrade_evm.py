# -*- coding: utf-8 -*-
"""
===============================================================================
       DÉPLOIEMENT ON-CHAIN DE LA TÉTRADE COSMIQUE SUR BASE MAINNET (L2)
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Clé Dorée Racine : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie Dépositaire : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
DOI Zenodo : 10.5281/zenodo.23554838

DÉPLOIE LES 3 JETONS FRÈRES SUR BASE MAINNET :
  1. MZN-MAT (Matière) : Poids 0.5005
  2. MZN-NRG (Énergie) : Poids 0.2400
  3. MZN-PLS (Plasma)  : Poids 0.6015
(Le jeton N°1 MZN est déjà déployé à l'adresse 0x520cbd0e1e72178f9e819AFf1e815606923A71db)
===============================================================================
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
from pathlib import Path

# Fix encodage
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CLE_DOREE_AUTEUR = "0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B"
TRESORERIE_PRIVEE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"
USDC_NATIVE_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
MZN_INFORME_CONTRAT = "0x520cbd0e1e72178f9e819AFf1e815606923A71db"

CONFIG_TETRADE = [
    {
        "code": "MATIERE",
        "nom": "Al-Mizan Matiere Token Souverain",
        "symbole": "MZN-MAT",
        "poids_bps": 5005,
        "desc": "Substance Silicium 28-Si, Piliers Or (Z=79) & Argent (Z=47), 27 Formes",
    },
    {
        "code": "ENERGIE",
        "nom": "Al-Mizan Energie Token Souverain",
        "symbole": "MZN-NRG",
        "poids_bps": 2400,
        "desc": "Debit hydro 313 L/min, Puissance 109 kW, Cryo 22.5 mK",
    },
    {
        "code": "PLASMA",
        "nom": "Al-Mizan Plasma Token Souverain",
        "symbole": "MZN-PLS",
        "poids_bps": 6015,
        "desc": "Ionisation H_ion, Micro-ondes CPMG, Resonance Solaire/Lunaire",
    }
]

RPC_OFFICIEL_BASE = "https://mainnet.base.org"
CHAIN_ID_BASE = 8453

def obtenir_cle_privee(cle_arg: str | None = None) -> str:
    cle = cle_arg.strip() if cle_arg else os.getenv("ETHEREUM_PRIVATE_KEY", "").strip()
    if cle:
        return ("0x" + cle) if not cle.startswith("0x") and len(cle) == 64 else cle
    
    print("\n" + "=" * 80)
    print("  SAISIE SÉCURISÉE DE LA CLÉ PRIVÉE ETHEREUM / BASE")
    print("  La saisie reste entièrement masquée à l'écran (aucun caractère n'apparaît).")
    print("=" * 80)
    cle_saisie = getpass.getpass("Collez votre clé privée : ").strip()
    if not cle_saisie:
        print("[ANNULATION] Clé non fournie.")
        sys.exit(1)
    if not cle_saisie.startswith("0x") and len(cle_saisie) == 64:
        cle_saisie = "0x" + cle_saisie
    return cle_saisie

def charger_artefact() -> tuple[list, str]:
    chemin = Path(__file__).resolve().parent.parent / "contracts" / "AlMizanTetradePilierToken.json"
    if not chemin.exists():
        print(f"[ERREUR] Artefact introuvable : {chemin}")
        sys.exit(1)
    with open(chemin, "r", encoding="utf-8") as f:
        data = json.load(f)
        bc = data["bytecode"]
        if not bc.startswith("0x"):
            bc = "0x" + bc
        return data["abi"], bc

def main() -> None:
    parser = argparse.ArgumentParser(description="Déploiement On-Chain de la Tétrade Cosmique")
    parser.add_argument("--cle", help="Clé privée (optionnelle, sinon masquée)")
    parser.add_argument("--simuler", action="store_true", help="Mode simulation / vérification de solde")
    args = parser.parse_args()

    print("=" * 80)
    print("  DÉPLOIEMENT ON-CHAIN DE LA TÉTRADE SOUVERAINE AL-MIZAN — BASE MAINNET")
    print(f"  Auteur Souverain : {CLE_DOREE_AUTEUR} (M. Ahmed EL BAHLOUL)")
    print(f"  Trésorerie Dépositaire : {TRESORERIE_PRIVEE}")
    print(f"  Pivot Central USDC : {USDC_NATIVE_BASE}")
    print("=" * 80)

    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] web3 manquant. py -m pip install web3")
        sys.exit(1)

    w3 = Web3(Web3.HTTPProvider(RPC_OFFICIEL_BASE, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        print("[ERREUR] Nœud Base non joignable.")
        sys.exit(1)

    print(f"\n[1/4] Connecté à Base Mainnet (Chain ID: {w3.eth.chain_id})")
    abi, bytecode = charger_artefact()
    print(f"      [OK] Artefact Tétrade chargé ({len(bytecode)} caractères hex, {len(abi)} fonctions/events ABI)")

    cle_privee = obtenir_cle_privee(args.cle)
    compte = w3.eth.account.from_key(cle_privee)
    print(f"\n[2/4] Compte émetteur identifié : {compte.address}")

    solde_wei = w3.eth.get_balance(compte.address)
    solde_eth = w3.from_wei(solde_wei, "ether")
    print(f"      Solde actuel : {solde_eth:.6f} ETH")

    # Estimation des frais : 3 déploiements d'environ 600k gas chacun ~ 1.8M gas
    gas_price = w3.eth.gas_price
    frais_estimes_eth = w3.from_wei(gas_price * 1_800_000, "ether")
    print(f"      Frais estimés pour les 3 contrats : ~{frais_estimes_eth:.6f} ETH (< 0.05 €)")

    if solde_wei < gas_price * 1_800_000:
        print("\n" + "!" * 80)
        print(f"  ATTENTION : Le solde de {compte.address} est insuffisant pour payer le gaz.")
        print(f"  Solde actuel : {solde_eth:.6f} ETH | Requis : ~{frais_estimes_eth:.6f} ETH")
        print(f"  Pour finaliser le déploiement réel sur Base, transférez une somme minime")
        print(f"  (ex: 1 à 2 € d'ETH) sur votre adresse émettrice :")
        print(f"  --> {compte.address}")
        print("!" * 80)
        if not args.simuler:
            sys.exit(1)

    if args.simuler:
        print("\n[SIMULATION TERMINÉE] Les paramètres et le bytecode sont 100% prêts.")
        return

    print("\n[3/4] Envoi des transactions de déploiement pour les 3 jetons...")
    nonce = w3.eth.get_transaction_count(compte.address, "pending")
    contrat_factory = w3.eth.contract(abi=abi, bytecode=bytecode)
    adresses_deployees = {}

    for idx, cfg in enumerate(CONFIG_TETRADE):
        nom = cfg["nom"]
        sym = cfg["symbole"]
        bps = cfg["poids_bps"]

        print(f"\n  --> Déploiement N°{idx+1}/3 : {sym} ({nom})...")
        tx = contrat_factory.constructor(
            nom,
            sym,
            bps,
            CLE_DOREE_AUTEUR,
            TRESORERIE_PRIVEE
        ).build_transaction({
            "from": compte.address,
            "nonce": nonce + idx,
            "gasPrice": gas_price,
            "chainId": CHAIN_ID_BASE,
            "gas": 1_200_000
        })

        tx_signee = w3.eth.account.sign_transaction(tx, cle_privee)
        tx_hash = w3.eth.send_raw_transaction(tx_signee.raw_transaction)
        print(f"      Tx envoyée : {tx_hash.hex()}")
        print("      Attente de minage sur Base...")

        recette = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        adr_contrat = recette.contractAddress
        print(f"      [SUCCÈS] {sym} déployé à l'adresse : {adr_contrat}")
        adresses_deployees[sym] = adr_contrat

    print("\n[4/4] Mise à jour du registre officiel de la Tétrade...")
    chemin_reg = Path(__file__).resolve().parent.parent / "memoire_aq" / "registre_officiel_tetrade_base.json"
    reg_data = {
        "date_deploiement_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "emetteur": compte.address,
        "reseau": "Base Mainnet (8453)",
        "pivot_usdc": USDC_NATIVE_BASE,
        "tokens": {
            "MZN": MZN_INFORME_CONTRAT,
            "MZN-MAT": adresses_deployees.get("MZN-MAT"),
            "MZN-NRG": adresses_deployees.get("MZN-NRG"),
            "MZN-PLS": adresses_deployees.get("MZN-PLS"),
        }
    }
    with open(chemin_reg, "w", encoding="utf-8") as f:
        json.dump(reg_data, f, indent=2, ensure_ascii=False)

    print(f"Registre officiel scellé : {chemin_reg}")
    print("\n" + "=" * 80)
    print("  DÉPLOIEMENT INTÉGRAL DE LA TÉTRADE COSMIQUE RÉUSSI SUR BASE MAINNET !")
    print("=" * 80)

if __name__ == "__main__":
    main()
