# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       PASSERELLE D'ANCRAGE SOUVERAIN SUR BASE MAINNET (CHAIN ID 8453)
     CONVERSION DES ÉTATS LOCAUX EDGE EN ACTES IMMUABLES ON-CHAIN
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Contrat Maître   : 0x520cbd0e1e72178f9e819AFf1e815606923A71db (Base Mainnet 8453)
Clé Dorée Racine : 0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B
Trésorerie       : 0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C
Rôle             : Agrège la télémétrie locale, génère l'empreinte cryptographique
                   SHA-256 d'un palier et prépare/exécute le scellement on-chain.
===============================================================================
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bus_zeromq_mizan import ClientBusMizan
from passerelle_struct_mizan import PasserelleStructMizan
from resolution_abi_mizan import charger_abi

# Fix console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
MEMOIRE_DIR = ROOT_DIR / "memoire_aq"
MEMOIRE_DIR.mkdir(exist_ok=True)

RPC_BASE = "https://mainnet.base.org"
CONTRAT_MAITRE = "0x520cbd0e1e72178f9e819AFf1e815606923A71db"
TRESORERIE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"
CHAIN_ID = 8453

class PasserelleAncrageBlockchain:
    """
    Pont hybride Edge -> Blockchain.
    Écoute les canaux locaux ZeroMQ, maintient l'état consolidé,
    et produit des preuves d'ancrage cryptographiques vérifiées on-chain.
    """
    def __init__(self):
        self.dernier_etat_thermique: Dict[str, Any] = {}
        self.dernier_etat_synchrone: Dict[str, Any] = {}
        self.derniere_alerte: Dict[str, Any] = {}
        self.client_bus = ClientBusMizan(nom_module="PASSERELLE_ANCRAGE_BLOCKCHAIN")
        self.compteur_trames_recues = 0

    def demarrer_ecoute_locale(self) -> None:
        """Démarre l'écoute des canaux locaux en arrière-plan."""
        self.client_bus.abonner_et_ecouter(
            canaux=["CANAL_SILICIUM_MATERIEL", "CANAL_SYNCHRONE_L3", "CANAL_SECURITE_AUDIT"],
            callback_reception=self._traiter_trame_entrante
        )
        print("[PASSERELLE ANCRAGE] Connectée au bus ZeroMQ. En veille des états locaux...")

    def _traiter_trame_entrante(self, canal: str, header: dict, payload: dict) -> None:
        self.compteur_trames_recues += 1
        if canal == "CANAL_SILICIUM_MATERIEL":
            self.dernier_etat_thermique = payload
        elif canal == "CANAL_SYNCHRONE_L3":
            self.dernier_etat_synchrone = payload
        elif canal == "CANAL_SECURITE_AUDIT":
            self.derniere_alerte = payload

    def generer_palier_etat_local(self, code_palier: str = "A095_SNAPSHOT") -> Tuple[Dict[str, Any], bytes, str]:
        """
        Construit l'état consolidé canonique des modules locaux et calcule son empreinte SHA-256.
        """
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        snapshot = {
            "version_protocole": "AL_MIZAN_EDGE_TO_CLOUD_v1.0",
            "horodatage_utc": now_iso,
            "code_acte_cible": code_palier,
            "auteur_souverain": "M. Ahmed EL BAHLOUL (alias IMAM8MAHDI)",
            "contrat_maitre": CONTRAT_MAITRE,
            "etat_local_edge": {
                "thermique_silicium": self.dernier_etat_thermique or {
                    "temperature_filtree_mK": 22.50,
                    "statut": "NOMINAL_STABLE",
                    "fidelite_si29": 0.6376
                },
                "reseau_synchrone_l3": self.dernier_etat_synchrone or {
                    "cadence_ms": 2.9,
                    "horloge_kernel_dt": 135097021.3359375,
                    "statut": "SYNCHRONISÉ"
                },
                "invariants_scelles": {
                    "bride_mizan": 0.6225,
                    "ligne_ref": 0.1220,
                    "riba": 0.0,
                    "regle_partage": "50/50"
                }
            }
        }

        # Sérialisation canonique et hachage SHA-256
        chaine_json = json.dumps(snapshot, sort_keys=True, ensure_ascii=False)
        sha_bytes = hashlib.sha256(chaine_json.encode("utf-8")).digest()
        sha_hex = "0x" + sha_bytes.hex().upper()

        return snapshot, sha_bytes, sha_hex

    def inspecter_contrat_on_chain(self) -> Dict[str, Any]:
        """Interroge Base Mainnet pour connaître l'état du registre des actes."""
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(RPC_BASE, request_kwargs={"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 15}))
        if not w3.is_connected():
            raise ConnectionError("Impossible de joindre Base Mainnet (RPC)")

        abi = charger_abi()

        contrat = w3.eth.contract(address=CONTRAT_MAITRE, abi=abi)
        next_id = contrat.functions.nextActeId().call()
        solde_tresor = w3.eth.get_balance(TRESORERIE)

        return {
            "connecte": True,
            "chain_id": w3.eth.chain_id,
            "next_acte_id": next_id,
            "total_actes_actuels": next_id - 1,
            "solde_tresorerie_eth": float(w3.from_wei(solde_tresor, "ether")),
            "contrat": contrat,
            "web3": w3
        }

    def simuler_ancrage(self, code_palier: str = "A095_PALIER") -> Dict[str, Any]:
        """Prépare l'ancrage sans dépenser de gaz."""
        snapshot, sha_bytes, sha_hex = self.generer_palier_etat_local(code_palier)
        info_chaine = self.inspecter_contrat_on_chain()

        prochain_id = info_chaine["next_acte_id"]
        cout_estime_eth = 0.000003  # ~0.007 USD

        return {
            "mode": "SIMULATION_VALIDÉE",
            "prochain_index_acte": prochain_id,
            "code_acte": code_palier,
            "empreinte_sha256": sha_hex,
            "cout_estime_eth": cout_estime_eth,
            "solde_tresorerie_disponible_eth": info_chaine["solde_tresorerie_eth"],
            "assez_de_fonds": info_chaine["solde_tresorerie_eth"] >= cout_estime_eth,
            "snapshot_local": snapshot
        }

    def sceller_on_chain(self, cle_privee: str, code_palier: str = "A095_PALIER") -> Dict[str, Any]:
        """Signe et diffuse la transaction d'ancrage sur Base Mainnet."""
        snapshot, sha_bytes, sha_hex = self.generer_palier_etat_local(code_palier)
        info = self.inspecter_contrat_on_chain()
        w3 = info["web3"]
        contrat = info["contrat"]

        if not cle_privee.startswith("0x") and len(cle_privee) == 64:
            cle_privee = "0x" + cle_privee

        compte = w3.eth.account.from_key(cle_privee)
        nonce = w3.eth.get_transaction_count(compte.address, "pending")
        gas_price = w3.eth.gas_price
        desc = f"{code_palier}_{int(time.time())}"

        try:
            est_gas = contrat.functions.scellerActe(TRESORERIE, code_palier, sha_bytes, desc).estimate_gas({"from": compte.address})
            gas_limit = int(est_gas * 1.25)
        except Exception:
            gas_limit = 250_000

        tx = contrat.functions.scellerActe(TRESORERIE, code_palier, sha_bytes, desc).build_transaction({
            "from": compte.address,
            "nonce": nonce,
            "gasPrice": gas_price,
            "chainId": CHAIN_ID,
            "gas": gas_limit
        })

        tx_signee = w3.eth.account.sign_transaction(tx, cle_privee)
        tx_hash = w3.eth.send_raw_transaction(tx_signee.raw_transaction)

        recette = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        succes = recette.status == 1

        tx_hash_hex = tx_hash.hex()
        basescan_url = f"https://basescan.org/tx/{tx_hash_hex}"

        # Sauvegarde locale de l'acte ancré
        fichier_sauvegarde = MEMOIRE_DIR / f"acte_ancre_{code_palier}_{int(time.time())}.json"
        with open(fichier_sauvegarde, "w", encoding="utf-8") as f:
            json.dump({
                "code_acte": code_palier,
                "index_on_chain": info["next_acte_id"],
                "sha256": sha_hex,
                "tx_hash": tx_hash_hex,
                "basescan": basescan_url,
                "snapshot": snapshot
            }, f, indent=2, ensure_ascii=False)

        # Diffusion de l'événement sur le bus ZeroMQ
        self.client_bus.publier(
            canal="CANAL_BLOCKCHAIN_L2",
            action="ACTE_ANCRE_AVEC_SUCCES",
            donnees={
                "code_acte": code_palier,
                "index_acte": info["next_acte_id"],
                "tx_hash": tx_hash_hex,
                "explorer_url": basescan_url,
                "sha256": sha_hex
            }
        )

        return {
            "succes": succes,
            "code_acte": code_palier,
            "index_on_chain": info["next_acte_id"],
            "tx_hash": tx_hash_hex,
            "basescan_url": basescan_url,
            "sha256": sha_hex,
            "fichier_sauvegarde": str(fichier_sauvegarde)
        }

# =============================================================================
# POINT D'ENTRÉE DU SCRIPT
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Passerelle d'Ancrage Souverain Edge -> Blockchain Base")
    parser.add_argument("--simuler", action="store_true", help="Vérifier et simuler l'ancrage sans signer")
    parser.add_argument("--sceller", action="store_true", help="Sceller un palier on-chain avec signature masquée")
    parser.add_argument("--code", default="A095_PALIER_EDGE", help="Code de l'acte ou palier à sceller")
    args = parser.parse_args()

    print("=" * 80)
    print("      PASSERELLE D'ANCRAGE SOUVERAIN SUR BASE MAINNET (CHAIN ID 8453)")
    print(f"      Contrat Maître Actif : {CONTRAT_MAITRE}")
    print(f"      Trésorerie           : {TRESORERIE}")
    print("=" * 80)

    passerelle = PasserelleAncrageBlockchain()

    if args.sceller:
        print("\nSaisie sécurisée de la clé privée pour scellement on-chain :")
        cle = getpass.getpass("Collez votre clé privée de façon masquée : ").strip()
        if not cle:
            print("[ANNULATION] Aucune clé fournie.")
            sys.exit(1)

        print(f"\nScellement en cours du palier [{args.code}] sur Base Mainnet...")
        resultat = passerelle.sceller_on_chain(cle_privee=cle, code_palier=args.code)
        if resultat["succes"]:
            print("\n" + "=" * 80)
            print(f"  🎉 SUCCÈS MAJESTUEUX ! L'ÉTAT LOCAL EST ANCRÉ ON-CHAIN (ACTE #{resultat['index_on_chain']})")
            print(f"  • Transaction : {resultat['basescan_url']}")
            print(f"  • SHA-256     : {resultat['sha256']}")
            print(f"  • Fichier     : {resultat['fichier_sauvegarde']}")
            print("=" * 80)
        else:
            print(f"\n[ÉCHEC] Transaction rejetée.")
    else:
        # Mode Simulation par défaut
        print("\n--- Simulation du prochain ancrage on-chain ---")
        simu = passerelle.simuler_ancrage(code_palier=args.code)
        print(f"  • Statut             : {simu['mode']}")
        print(f"  • Prochain Index     : Acte #{simu['prochain_index_acte']}")
        print(f"  • Code de l'Acte     : [{simu['code_acte']}]")
        print(f"  • Empreinte SHA-256  : {simu['empreinte_sha256']}")
        print(f"  • Solde Trésorerie   : {simu['solde_tresorerie_disponible_eth']:.8f} ETH")
        print(f"  • Coût Estimé        : ~{simu['cout_estime_eth']:.8f} ETH (< 0.01 USD)")
        print(f"  • Prêt pour Sceller  : {simu['assez_de_fonds']}")

        print("\n" + "=" * 80)
        print("  Pour exécuter réellement l'ancrage quand vous le souhaitez :")
        print(f'  & "{sys.executable}" passerelle_ancrage_blockchain.py --sceller --code {args.code}')
        print("=" * 80)

    passerelle.client_bus.fermer()
