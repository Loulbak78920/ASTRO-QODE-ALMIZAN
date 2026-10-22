# -*- coding: utf-8 -*-
"""
===============================================================================
       SCRIPT DE DÉPLOIEMENT SÉCURISÉ SUR RÉSEAU EVM — AL-MIZAN & ASTRO-Q°ODE
===============================================================================
Auteur : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI)
Clé Dorée Racine : 0xc9550dd0a57c609494dbc44450df48d798ebfb0b
Trésorerie Privée : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
DOI Zenodo : 10.5281/zenodo.23554838

SÉCURITÉ STRICTE :
- Ne code JAMAIS de clé privée en dur.
- Lit la clé depuis la variable d'environnement 'ETHEREUM_PRIVATE_KEY' ou via saisie masquée (getpass).
===============================================================================
"""

from __future__ import annotations

import getpass
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = Path(__file__).resolve().parent / "contracts" / "AmalMizanSynchronMznContract.sol"

CLE_DOREE_AUTEUR = "0xC9550Dd0A57C609494DbC44450df48d798EbfB0b"
TRESORERIE_PRIVEE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"


def obtenir_cle_privee() -> str:
    """Récupère la clé privée de façon sécurisée sans trace sur disque."""
    cle = os.getenv("ETHEREUM_PRIVATE_KEY")
    if cle:
        cle = cle.strip()
        if not cle.startswith("0x") and len(cle) == 64:
            cle = "0x" + cle
        return cle

    print("\n[INVITATION SÉCURISÉE] Aucune variable 'ETHEREUM_PRIVATE_KEY' détectée.")
    cle_saisie = getpass.getpass("Veuillez saisir votre clé privée Ethereum (la saisie reste masquée) : ").strip()
    if not cle_saisie:
        print("[ANNULATION] Clé privée non fournie. Déploiement interrompu.")
        sys.exit(1)
    if not cle_saisie.startswith("0x") and len(cle_saisie) == 64:
        cle_saisie = "0x" + cle_saisie
    return cle_saisie


def main() -> None:
    print("================================================================================")
    print("  DÉPLOIEMENT SÉCURISÉ DU SMART CONTRACT AMAL-MIZAN SYNCHRON MZN")
    print(f"  Auteur : M. Ahmed EL BAHLOUL · DOI Zenodo : 10.5281/zenodo.23554838")
    print(f"  Clé Dorée : {CLE_DOREE_AUTEUR}")
    print(f"  Trésorerie Privée : {TRESORERIE_PRIVEE}")
    print("================================================================================")

    rpc_url = os.getenv("RPC_URL", "https://rpc.sepolia.org")
    print(f"\n[1/3] URL RPC cible : {rpc_url}")

    if not CONTRACT_PATH.exists():
        print(f"[ERREUR] Fichier contrat introuvable : {CONTRACT_PATH}")
        sys.exit(1)

    print(f"[2/3] Fichier Solidity vérifié : {CONTRACT_PATH.name} ({CONTRACT_PATH.stat().st_size} octets)")

    try:
        from web3 import Web3
    except ImportError:
        print("\n[INFORMATION DÉPLOIEMENT]")
        print("La bibliothèque python 'web3' n'est pas installée dans l'environnement local.")
        print("Pour déployer directement via votre navigateur sans rien installer :")
        print("👉 Suivez la MÉTHODE 1 du guide : GUIDE_DEPLOIEMENT_SECURISE_SMART_CONTRACT_CLE_PRIVEE.md")
        print("   Ouvrez https://remix.ethereum.org avec MetaMask connecté.")
        print("\nSinon, installez web3 via : py -m pip install web3 py-solc-x")
        sys.exit(0)

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"[ERREUR] Impossible de se connecter au noeud RPC : {rpc_url}")
        sys.exit(1)

    chain_id = w3.eth.chain_id
    print(f"[OK] Connecté avec succès. Chain ID : {chain_id}")

    cle_privee = obtenir_cle_privee()
    compte = w3.eth.account.from_key(cle_privee)
    print(f"[3/3] Compte de déploiement chargé : {compte.address}")

    solde_wei = w3.eth.get_balance(compte.address)
    solde_eth = w3.from_wei(solde_wei, "ether")
    print(f"      Solde disponible : {solde_eth} ETH")

    if solde_wei == 0:
        print("\n[ATTENTION] Le solde est de 0 ETH. Vous avez besoin d'un minimum de fonds (gas) pour déployer.")
        print("Pour le testnet Sepolia, obtenez des ETH gratuits sur : https://sepoliafaucet.com ou https://faucets.chain.link")
        sys.exit(1)

    print("\n[PRÊT POUR LA TRANSACTION]")
    print(f"Constructeur paramétré avec les 5 adresses :")
    print(f"  - _pcTerrestre   : {TRESORERIE_PRIVEE}")
    print(f"  - _galaxyMobile  : {TRESORERIE_PRIVEE}")
    print(f"  - _qistasCivique : {TRESORERIE_PRIVEE}")
    print(f"  - _fondsReserve  : {CLE_DOREE_AUTEUR}")
    print(f"  - _caisseZakat   : {TRESORERIE_PRIVEE}")
    print("\nPour achever le déploiement en direct, validez la confirmation de transaction.")


if __name__ == "__main__":
    main()
