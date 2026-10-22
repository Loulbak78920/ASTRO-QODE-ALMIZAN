# -*- coding: utf-8 -*-
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
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import time
from pathlib import Path

# Adresses Protocolaires Fondatrices Scellées
CLE_DOREE_AUTEUR = "0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B"
TRESORERIE_PRIVEE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"

RESEAUX_CONFIG = {
    "sepolia": {
        "nom": "Sepolia Testnet (Ethereum)",
        "rpc": [
            "https://ethereum-sepolia-rpc.publicnode.com",
            "https://1rpc.io/sepolia",
            "https://rpc.sepolia.org",
        ],
        "chain_id": 11155111,
        "explorateur": "https://sepolia.etherscan.io",
        "symbole": "SepoliaETH",
        "faucets": [
            "https://sepoliafaucet.com",
            "https://cloud.google.com/application/web3/faucet/ethereum/sepolia",
            "https://faucets.chain.link/sepolia",
        ],
    },
    "base": {
        "nom": "Base Mainnet (Coinbase L2)",
        "rpc": [
            "https://mainnet.base.org",
            "https://base-rpc.publicnode.com",
        ],
        "chain_id": 8453,
        "explorateur": "https://basescan.org",
        "symbole": "ETH",
        "faucets": [],
    },
    "arbitrum": {
        "nom": "Arbitrum One Mainnet (L2)",
        "rpc": [
            "https://arb1.arbitrum.io/rpc",
            "https://arbitrum-one-rpc.publicnode.com",
        ],
        "chain_id": 42161,
        "explorateur": "https://arbiscan.io",
        "symbole": "ETH",
        "faucets": [],
    },
    "polygon": {
        "nom": "Polygon PoS Mainnet",
        "rpc": [
            "https://polygon-rpc.com",
            "https://polygon-bor-rpc.publicnode.com",
        ],
        "chain_id": 137,
        "explorateur": "https://polygonscan.com",
        "symbole": "POL",
        "faucets": [],
    },
}


def chercher_artefact_contrat() -> tuple[list, str]:
    """Localise le bytecode et l'ABI du contrat pré-compilé."""
    chemins_possibles = [
        Path(__file__).resolve().parent / "contracts" / "build" / "AmalMizanSynchronMznContract.json",
        Path(__file__).resolve().parent.parent / "chaine" / "contracts" / "build" / "AmalMizanSynchronMznContract.json",
        Path(__file__).resolve().parent.parent / "contracts" / "build" / "AmalMizanSynchronMznContract.json",
    ]
    for c in chemins_possibles:
        if c.exists():
            with open(c, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data["abi"], data["bytecode"]

    # Recherche directe des fichiers .abi et .bin
    dirs = [
        Path(__file__).resolve().parent / "contracts" / "build",
        Path(__file__).resolve().parent.parent / "chaine" / "contracts" / "build",
    ]
    for d in dirs:
        if d.exists():
            bins = list(d.glob("*AmalMizanSynchronMznContract.bin"))
            abis = list(d.glob("*AmalMizanSynchronMznContract.abi"))
            if bins and abis:
                with open(abis[0], "r", encoding="utf-8") as fa:
                    abi = json.load(fa)
                with open(bins[0], "r", encoding="utf-8") as fb:
                    bytecode = fb.read().strip()
                return abi, bytecode

    print("[ERREUR] Artefact compilé AmalMizanSynchronMznContract.json introuvable.")
    print("Veuillez d'abord compiler le contrat avec : npx solc --abi --bin ...")
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
        choices=["sepolia", "base", "arbitrum", "polygon"],
        default="sepolia",
        help="Réseau cible (défaut : sepolia)",
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
    print("================================================================================")

    # Vérification Web3
    try:
        from web3 import Web3
    except ImportError:
        print("[ERREUR] Module python 'web3' absent. Installez-le avec : py -m pip install web3")
        sys.exit(1)

    # Connexion au nœud RPC
    print(f"\n[1/5] Connexion au nœud RPC : {rpc_url}...")
    w3 = None
    for rpc_candidat in [rpc_url] + config["rpc"]:
        try:
            test_w3 = Web3(Web3.HTTPProvider(rpc_candidat, request_kwargs={"timeout": 15}))
            if test_w3.is_connected():
                w3 = test_w3
                rpc_url = rpc_candidat
                break
        except Exception:
            continue

    if not w3 or not w3.is_connected():
        print(f"[ERREUR] Impossible de se connecter à aucun RPC pour {config['nom']}.")
        sys.exit(1)

    detect_chain_id = w3.eth.chain_id
    print(f"      [OK] Nœud connecté. Chain ID détecté : {detect_chain_id}")

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
        print("      🌟 RECONNAISSANCE : Compte Trésorerie Privée Officiel reconnu !")
    elif compte.address.lower() == CLE_DOREE_AUTEUR.lower():
        print("      👑 RECONNAISSANCE : Clé Dorée Racine Auteur reconnue !")

    # Solde et vérification gas
    solde_wei = w3.eth.get_balance(compte.address)
    solde_eth = w3.from_wei(solde_wei, "ether")
    print(f"      Solde actuel : {solde_eth:.6f} {config['symbole']}")

    if solde_wei == 0:
        print("\n" + "!" * 80)
        print(f"  ATTENTION : Le solde du compte {compte.address} est de 0 {config['symbole']}.")
        print("  Pour déployer un smart contract sur la blockchain, une infime quantité de gaz est requise.")
        if config["faucets"]:
            print(f"\n  Sur le réseau gratuit {config['nom']}, vous pouvez recevoir des fonds de test instantanément :")
            for faucet in config["faucets"]:
                print(f"   👉 {faucet}")
            print(f"\n  Indiquez simplement votre adresse : {compte.address}")
        else:
            print(f"  Veuillez approvisionner cette adresse d'au moins 0.001 {config['symbole']}.")
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
        tx_constructeur["gas"] = int(gas_estime * 1.2)  # Marge de 20%
    except Exception as e:
        print(f"      [AVIS] Estimation gas par défaut (marge de sécurité) : {e}")
        tx_constructeur["gas"] = 4_500_000

    cout_estime_eth = w3.from_wei(tx_constructeur["gas"] * gas_price, "ether")
    print(f"      Gas estimé : {tx_constructeur['gas']} unités (Coût max : {cout_estime_eth:.6f} {config['symbole']})")

    # Confirmation finale
    print("\nSignature locale hors-ligne...")
    tx_signee = w3.eth.account.sign_transaction(tx_constructeur, private_key=cle_privee)

    # Destruction de la clé en mémoire
    del cle_privee

    print("Envoi de la transaction sur le réseau...")
    tx_hash = w3.eth.send_raw_transaction(tx_signee.raw_transaction)
    tx_hash_hex = tx_hash.hex()
    print(f"      Hash de la Transaction : {tx_hash_hex}")
    print(f"      Suivi en direct : {config['explorateur']}/tx/{tx_hash_hex}")

    print("\nAttente de la confirmation du bloc par le consensus réseau...")
    recu = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    if recu.status == 1:
        adresse_contrat = recu.contractAddress
        print("\n" + "=" * 80)
        print("  🎉 SUCCÈS ABSOLU — SMART CONTRACT AMAL-MIZAN SYNCHRON MZN DÉPLOYÉ !")
        print("=" * 80)
        print(f"  Adresse du Smart Contract : {adresse_contrat}")
        print(f"  Bloc Numéro : {recu.blockNumber}")
        print(f"  Gas Utilisé : {recu.gasUsed}")
        print(f"  Lien Explorateur Officiel : {config['explorateur']}/address/{adresse_contrat}")
        print("=" * 80)

        # Enregistrement du reçu dans un fichier de déploiement local
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
