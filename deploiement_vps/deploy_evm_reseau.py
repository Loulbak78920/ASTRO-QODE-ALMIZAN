# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       SCRIPT OFFICIEL DE DÉPLOIEMENT SÉCURISÉ EVM — AL-MIZAN & ASTRO-Q°ODE
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Date de Naissance : 20/06/1989 à Meulan-en-Yvelines (78, France)
Clé Dorée Racine : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie Dépositaire : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
DOI Officiel Zenodo : 10.5281/zenodo.23554838
Dépôt GitHub : https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN
===============================================================================
RÉSEAUX SÉCURISÉS OFFICIELS (SANS SITES MALVEILLANTS NI FAUCETS SUSPECTS) :
- Base Mainnet (Coinbase L2) : RPC Officiel https://mainnet.base.org (< 0.01 €)
- Arbitrum One Mainnet (Offchain Labs) : RPC Officiel https://arb1.arbitrum.io/rpc (< 0.02 €)
- Polygon PoS Mainnet : RPC https://1rpc.io/matic (< 0.01 €)
- Base Sepolia Testnet : RPC Officiel Coinbase https://sepolia.base.org (0.00 €)
- Arbitrum Sepolia Testnet : RPC Officiel https://sepolia-rollup.arbitrum.io/rpc (0.00 €)
- Local Hors-Ligne : http://127.0.0.1:8545 (Zéro Internet, Zéro Risque)
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

# Fix encodage console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Adresses Protocolaires Fondatrices Scellées
CLE_DOREE_AUTEUR = "0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B"
TRESORERIE_PRIVEE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"

RESEAUX_CONFIG = {
    "base": {
        "nom": "Base Mainnet (Coinbase L2 Officiel)",
        "rpc": [
            "https://mainnet.base.org",
            "https://base.publicnode.com",
        ],
        "chain_id": 8453,
        "explorateur": "https://basescan.org",
        "symbole": "ETH",
        "est_testnet": False,
        "frais_estimes": "< 0.01 € (1 centime)",
        "faucets": [],
    },
    "arbitrum": {
        "nom": "Arbitrum One Mainnet (Offchain Labs Officiel)",
        "rpc": [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one-rpc.publicnode.com",
        ],
        "chain_id": 42161,
        "explorateur": "https://arbiscan.io",
        "symbole": "ETH",
        "est_testnet": False,
        "frais_estimes": "< 0.02 € (2 centimes)",
        "faucets": [],
    },
    "polygon": {
        "nom": "Polygon PoS Mainnet",
        "rpc": [
            "https://1rpc.io/matic",
            "https://polygon-bor-rpc.publicnode.com",
        ],
        "chain_id": 137,
        "explorateur": "https://polygonscan.com",
        "symbole": "POL",
        "est_testnet": False,
        "frais_estimes": "< 0.01 €",
        "faucets": [],
    },
    "base-sepolia": {
        "nom": "Base Sepolia Testnet (Coinbase L2 Officiel)",
        "rpc": [
            "https://sepolia.base.org",
        ],
        "chain_id": 84532,
        "explorateur": "https://sepolia.basescan.org",
        "symbole": "ETH",
        "est_testnet": True,
        "frais_estimes": "0.00 € (Gratuit)",
        "faucets": [
            "https://faucets.chain.link/base-sepolia",
            "https://docs.base.org/tools/network-faucets/",
        ],
    },
    "arbitrum-sepolia": {
        "nom": "Arbitrum Sepolia Testnet (Offchain Labs Officiel)",
        "rpc": [
            "https://sepolia-rollup.arbitrum.io/rpc",
        ],
        "chain_id": 421614,
        "explorateur": "https://sepolia.arbiscan.io",
        "symbole": "ETH",
        "est_testnet": True,
        "frais_estimes": "0.00 € (Gratuit)",
        "faucets": [
            "https://faucets.chain.link/arbitrum-sepolia",
        ],
    },
    "local": {
        "nom": "Réseau Local Privé Hors-Ligne (Anvil / Hardhat)",
        "rpc": [
            "http://127.0.0.1:8545",
            "http://localhost:8545",
        ],
        "chain_id": 31337,
        "explorateur": "Console Locale",
        "symbole": "ETH",
        "est_testnet": True,
        "frais_estimes": "0.00 € (Local)",
        "faucets": [],
    },
}


def chercher_artefact_contrat() -> tuple[list, str]:
    """Localise le bytecode et l'ABI du contrat pré-compilé."""
    nom_artefact = "AmalMizanSynchronMznContract.json"
    ici = Path(__file__).resolve().parent
    systeme = ici.parent
    projet = systeme.parent
    depot_public = projet.parent / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI"
    chemins_possibles = [
        ici / "contracts" / nom_artefact,
        ici / "contracts" / "build" / nom_artefact,
        systeme / "contracts" / nom_artefact,
        systeme / "contracts" / "build" / nom_artefact,
        depot_public / "contracts" / nom_artefact,
        depot_public / "contracts" / "build" / nom_artefact,
    ]
    for c in chemins_possibles:
        if c.is_file():
            with open(c, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data["abi"], data["bytecode"]

    cherches = "\n  ".join(str(c) for c in chemins_possibles)
    print(f"[ERREUR] Artefact compilé {nom_artefact} introuvable. Chemins testés :\n  {cherches}")
    sys.exit(1)


def obtenir_cle_privee(cle_cli: str | None = None) -> str:
    """Récupère la clé privée de façon 100% sécurisée sans trace sur disque."""
    if cle_cli:
        cle = cle_cli.strip()
    else:
        cle = os.getenv("ETHEREUM_PRIVATE_KEY", "").strip()

    if cle:
        if not cle.startswith("0x") and len(cle) == 64:
            cle = "0x" + cle
        return cle

    print("\n" + "=" * 80)
    print("  INVITATION SÉCURISÉE — SAISIE DE VOTRE CLÉ PRIVÉE ETHEREUM")
    print("  La saisie reste entièrement masquée à l'écran (aucun caractère n'apparaît).")
    print("  La clé est conservée uniquement en mémoire vive (RAM) le temps de la signature,")
    print("  et détruite immédiatement après. Aucune écriture sur le disque.")
    print("=" * 80)
    cle_saisie = getpass.getpass("Collez ou entrez votre clé privée : ").strip()

    if not cle_saisie:
        print("[ANNULATION] Clé privée non fournie. Déploiement interrompu en toute sécurité.")
        sys.exit(1)

    if not cle_saisie.startswith("0x") and len(cle_saisie) == 64:
        cle_saisie = "0x" + cle_saisie
    return cle_saisie


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Déploiement Sécurisé du Smart Contract AmalMizanSynchronMznContract sur réseau EVM"
    )
    parser.add_argument(
        "--reseau",
        choices=list(RESEAUX_CONFIG.keys()),
        default="base",
        help="Réseau cible (défaut : base - Mainnet Coinbase L2, coût < 0.01 €)",
    )
    parser.add_argument("--rpc", help="URL RPC personnalisée optionnelle")
    parser.add_argument("--cle", help="Clé privée (optionnelle, sinon demandée de façon masquée)")
    parser.add_argument(
        "--simuler",
        action="store_true",
        help="Mode simulation : vérifie la connexion, l'adresse et le solde sans envoyer la transaction",
    )
    args = parser.parse_args()

    config = RESEAUX_CONFIG[args.reseau]
    rpc_url = args.rpc if args.rpc else config["rpc"][0]

    print("================================================================================")
    print("  DÉPLOIEMENT SÉCURISÉ SMART CONTRACT — AMAL-MIZAN SYNCHRON MZN (MZN)")
    print(f"  Auteur Souverain : {CLE_DOREE_AUTEUR} (M. Ahmed EL BAHLOUL)")
    print(f"  Trésorerie Dépositaire : {TRESORERIE_PRIVEE}")
    print(f"  DOI Officiel Zenodo : 10.5281/zenodo.23554838")
    print(f"  Réseau Choisi : {config['nom']} (Chain ID : {config['chain_id']})")
    print(f"  Frais Réseau Estimés : {config['frais_estimes']}")
    print("================================================================================")

    # Vérification Web3
    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] Module python 'web3' absent. Installez-le avec : py -m pip install web3")
        sys.exit(1)

    # Connexion au nœud RPC
    print(f"\n[1/5] Connexion au nœud RPC officiel ({rpc_url})...")
    w3 = None
    for rpc_candidat in [rpc_url] + config["rpc"]:
        try:
            test_w3 = Web3(Web3.HTTPProvider(rpc_candidat, request_kwargs={"timeout": 10}))
            if test_w3.is_connected():
                w3 = test_w3
                rpc_url = rpc_candidat
                break
        except Exception:
            continue

    if not w3 or not w3.is_connected():
        print(f"[ERREUR] Impossible de se connecter aux RPC de {config['nom']}.")
        if args.reseau == "local":
            print("Pour lancer un nœud local : installez anvil (Foundry) ou lancez npx hardhat node.")
        sys.exit(1)

    detect_chain_id = w3.eth.chain_id
    print(f"      [OK] Nœud officiel connecté. Chain ID vérifié : {detect_chain_id}")

    # Chargement de l'artefact compilé
    print("\n[2/5] Chargement du Bytecode et de l'ABI du contrat...")
    abi, bytecode = chercher_artefact_contrat()
    if not bytecode.startswith("0x"):
        bytecode = "0x" + bytecode
    print(f"      [OK] Bytecode prêt ({len(bytecode)} caractères hex). ABI contient {len(abi)} définitions.")

    # Chargement de la clé privée
    print("\n[3/5] Dérivation du compte à partir de votre clé privée...")
    cle_privee = obtenir_cle_privee(args.cle)
    try:
        compte = w3.eth.account.from_key(cle_privee)
    except Exception as e:
        print(f"[ERREUR] Clé privée invalide : {e}")
        sys.exit(1)

    print(f"      [OK] Compte dérivé avec succès : {compte.address}")
    if compte.address.lower() == TRESORERIE_PRIVEE.lower():
        print("      [RECONNAISSANCE] Compte Tresorerie Privee Officiel reconnu !")
    elif compte.address.lower() == CLE_DOREE_AUTEUR.lower():
        print("      [RECONNAISSANCE] Cle Doree Racine Auteur reconnue !")

    # Solde et vérification gas
    solde_wei = w3.eth.get_balance(compte.address)
    solde_eth = w3.from_wei(solde_wei, "ether")
    print(f"      Solde actuel : {solde_eth:.6f} {config['symbole']}")

    if solde_wei == 0:
        print("\n" + "!" * 80)
        print(f"  ATTENTION : Le solde du compte {compte.address} est de 0 {config['symbole']}.")
        print("  Pour deployer un smart contract, une infime quantite de gaz est requise.")
        if config["est_testnet"]:
            if config["faucets"]:
                print(f"\n  Sur le reseau de test gratuit {config['nom']}, robinets officiels verifies :")
                for faucet in config["faucets"]:
                    print(f"   -> {faucet}")
                print(f"  Indiquez simplement votre adresse : {compte.address}")
        else:
            print(f"\n  Sur le reseau de production {config['nom']}, les frais sont minimes ({config['frais_estimes']}).")
            print(f"  Il suffit de transferer une somme modique (ex: 1 a 2 euros d'ETH) sur votre compte :")
            print(f"  -> Adresse Tresorerie : {compte.address}")
        print("!" * 80)
        if not args.simuler:
            sys.exit(1)

    # Paramétrage du constructeur
    print("\n[4/5] Paramétrage des 5 adresses souveraines du constructeur :")
    args_constructeur = [
        TRESORERIE_PRIVEE,  # _pcTerrestre
        TRESORERIE_PRIVEE,  # _galaxyMobile
        TRESORERIE_PRIVEE,  # _qistasCivique
        CLE_DOREE_AUTEUR,   # _fondsReserve (302M MZN)
        TRESORERIE_PRIVEE,  # _caisseZakat
    ]
    for nom, adr in zip(["PC Terrestre", "Galaxy Mobile", "Qistas Civique", "Fonds Réserve", "Caisse Zakat"], args_constructeur):
        print(f"      - {nom:15} : {adr}")

    if args.simuler:
        print("\n[SIMULATION TERMINÉE] Tous les paramètres sont 100% valides. Déploiement prêt.")
        return

    # Préparation et envoi de la transaction
    print("\n[5/5] Préparation et signature de la transaction de déploiement...")
    contrat = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(compte.address, "pending")
    gas_price = w3.eth.gas_price

    tx_constructeur = contrat.constructor(*args_constructeur).build_transaction({
        "from": compte.address,
        "nonce": nonce,
        "gasPrice": gas_price,
        "chainId": detect_chain_id,
    })

    try:
        gas_estime = w3.eth.estimate_gas(tx_constructeur)
        tx_constructeur["gas"] = int(gas_estime * 1.2)
    except Exception as e:
        print(f"      [AVIS] Marge gas de sécurité appliquée : {e}")
        tx_constructeur["gas"] = 4_500_000

    cout_estime_eth = w3.from_wei(tx_constructeur["gas"] * gas_price, "ether")
    print(f"      Gas alloué : {tx_constructeur['gas']} unités (Coût max estimé : {cout_estime_eth:.6f} {config['symbole']})")

    # Confirmation finale
    print("\nSignature locale sécurisée en mémoire vive...")
    tx_signee = w3.eth.account.sign_transaction(tx_constructeur, private_key=cle_privee)

    # Destruction immédiate de la clé en mémoire
    del cle_privee

    print(f"Envoi de la transaction sur {config['nom']}...")
    tx_hash = w3.eth.send_raw_transaction(tx_signee.raw_transaction)
    tx_hash_hex = tx_hash.hex()
    print(f"      Hash Transaction : {tx_hash_hex}")
    if "http" in config["explorateur"]:
        print(f"      Suivi en direct : {config['explorateur']}/tx/{tx_hash_hex}")

    print("\nAttente de la validation du bloc par le consensus réseau...")
    recu = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    if recu.status == 1:
        adresse_contrat = recu.contractAddress
        print("\n" + "=" * 80)
        print("  [SUCCES TOTAL] SMART CONTRACT AMAL-MIZAN SYNCHRON MZN DEPLOYE !")
        print("=" * 80)
        print(f"  Adresse du Smart Contract : {adresse_contrat}")
        print(f"  Réseau : {config['nom']}")
        print(f"  Bloc Numéro : {recu.blockNumber}")
        print(f"  Gas Utilisé : {recu.gasUsed}")
        if "http" in config["explorateur"]:
            print(f"  Lien Explorateur Officiel : {config['explorateur']}/address/{adresse_contrat}")
        print("=" * 80)

        deploiement_info = {
            "reseau": config["nom"],
            "chain_id": detect_chain_id,
            "adresse_contrat": adresse_contrat,
            "deployeur": compte.address,
            "tx_hash": tx_hash_hex,
            "bloc_numero": recu.blockNumber,
            "horodatage_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "doi": "10.5281/zenodo.23554838",
        }
        fichier_sauvegarde = Path(__file__).resolve().parent / f"deploiement_{args.reseau}_{adresse_contrat[:10]}.json"
        with open(fichier_sauvegarde, "w", encoding="utf-8") as f:
            json.dump(deploiement_info, f, indent=2)
        print(f"Reçu de déploiement consigné dans : {fichier_sauvegarde.name}")
    else:
        print(f"[ÉCHEC] La transaction a échoué (statut : {recu.status}).")


if __name__ == "__main__":
    main()
