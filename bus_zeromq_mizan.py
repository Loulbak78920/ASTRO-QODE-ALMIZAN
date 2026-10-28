# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       BUS DE COMMUNICATION ET ROUTEUR ZEROMQ MULTI-CANAUX AL-MIZAN
      INTÉGRATION STRUCT PROTOBUF POUR LE ROUTAGE INTER-APPLICATIF
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Architecture     : ZeroMQ (PULL/PUB Pipeline) ⊗ google.protobuf.Struct
Canaux           : SILICIUM, QUANTIQUE, SYNCHRONE_L3, BLOCKCHAIN_L2, SECURITE, IHM
Ports Locaux     :
  • Port Ingestion (Entrée des Modules)   : tcp://127.0.0.1:5570 (ZMQ PUSH/PULL)
  • Port Diffusion (Distribution Abonnés) : tcp://127.0.0.1:5571 (ZMQ PUB/SUB)
===============================================================================
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import zmq

from passerelle_struct_mizan import PasserelleStructMizan

# Fix console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PORT_INGESTION = 5570   # Où les modules envoient leurs trames
PORT_DIFFUSION = 5571   # Où les modules écoutent les trames de leurs canaux

class RouteurBusMizan:
    """
    Nœud central de commutation ZeroMQ.
    Reçoit les messages de n'importe quel module applicatif et les retransmet
    aux modules abonnés selon le canal spécifié.
    """
    def __init__(self, port_in: int = PORT_INGESTION, port_out: int = PORT_DIFFUSION):
        self.port_in = port_in
        self.port_out = port_out
        self.contexte = zmq.Context.instance()
        self.sock_in = self.contexte.socket(zmq.PULL)
        self.sock_out = self.contexte.socket(zmq.PUB)
        self.actif = False
        self.compteur_messages = 0

    def demarrer(self, bloquant: bool = True) -> None:
        self.sock_in.bind(f"tcp://127.0.0.1:{self.port_in}")
        self.sock_out.bind(f"tcp://127.0.0.1:{self.port_out}")
        self.actif = True
        print(f"[ROUTEUR ZEROMQ] En écoute sur Ingestion={self.port_in} | Diffusion={self.port_out}")

        if bloquant:
            self._boucle_routage()
        else:
            t = threading.Thread(target=self._boucle_routage, daemon=True)
            t.start()

    def _boucle_routage(self) -> None:
        poller = zmq.Poller()
        poller.register(self.sock_in, zmq.POLLIN)

        while self.actif:
            try:
                chaussettes = dict(poller.poll(timeout=100))
                if self.sock_in in chaussettes and chaussettes[self.sock_in] == zmq.POLLIN:
                    trame_brute = self.sock_in.recv()
                    self.compteur_messages += 1

                    # Désérialisation rapide du header pour extraire le canal
                    header, _ = PasserelleStructMizan.deballer_message_canal(trame_brute)
                    canal = header.get("canal", "CANAL_INDEFINI")

                    # Routage ZeroMQ multipart : [Topic/Canal UTF-8, Payload Binaire Protobuf]
                    self.sock_out.send_multipart([
                        canal.encode("utf-8"),
                        trame_brute
                    ])
            except Exception as e:
                if self.actif:
                    print(f"[ROUTEUR ERREUR] {e}")

    def arreter(self) -> None:
        self.actif = False
        time.sleep(0.1)
        self.sock_in.close()
        self.sock_out.close()
        print("[ROUTEUR ZEROMQ] Arrêté.")


class ClientBusMizan:
    """
    Client de haut niveau pour les applications Python ou C++ voulant
    émettre et/ou recevoir des données typées à travers les canaux.
    """
    def __init__(self, nom_module: str = "MODULE_INCONNU", port_in: int = PORT_INGESTION, port_out: int = PORT_DIFFUSION):
        self.nom_module = nom_module
        self.contexte = zmq.Context.instance()
        self.sock_emetteur = self.contexte.socket(zmq.PUSH)
        self.sock_emetteur.connect(f"tcp://127.0.0.1:{port_in}")

        self.port_out = port_out
        self.sock_recepteur: Optional[zmq.Socket] = None
        self.fil_ecoute: Optional[threading.Thread] = None
        self.en_ecoute = False
        self.seq_id = 0

    def publier(self, canal: str, action: str, donnees: Dict[str, Any]) -> None:
        """
        Sérialise un dictionnaire avec google.protobuf.Struct et le pousse sur le bus.
        """
        self.seq_id += 1
        trame = PasserelleStructMizan.emballer_message_canal(
            canal=canal,
            action=action,
            donnees=donnees,
            id_sequence=self.seq_id,
            emetteur=self.nom_module
        )
        self.sock_emetteur.send(trame)

    def abonner_et_ecouter(
        self,
        canaux: List[str],
        callback_reception: Callable[[str, Dict[str, Any], Dict[str, Any]], None]
    ) -> None:
        """
        S'abonne à un ou plusieurs canaux et déclenche callback_reception(canal, header, payload).
        """
        self.sock_recepteur = self.contexte.socket(zmq.SUB)
        self.sock_recepteur.connect(f"tcp://127.0.0.1:{self.port_out}")

        for c in canaux:
            self.sock_recepteur.setsockopt_string(zmq.SUBSCRIBE, c)

        self.en_ecoute = True

        def boucle():
            poller = zmq.Poller()
            poller.register(self.sock_recepteur, zmq.POLLIN)
            while self.en_ecoute:
                try:
                    socks = dict(poller.poll(timeout=100))
                    if self.sock_recepteur in socks and socks[self.sock_recepteur] == zmq.POLLIN:
                        topic_bytes, trame = self.sock_recepteur.recv_multipart()
                        canal_topic = topic_bytes.decode("utf-8")
                        header, payload = PasserelleStructMizan.deballer_message_canal(trame)
                        callback_reception(canal_topic, header, payload)
                except Exception as ex:
                    if self.en_ecoute:
                        print(f"[{self.nom_module} ERREUR RECEPTION] {ex}")

        self.fil_ecoute = threading.Thread(target=boucle, daemon=True)
        self.fil_ecoute.start()

    def fermer(self) -> None:
        self.en_ecoute = False
        time.sleep(0.1)
        if self.sock_recepteur:
            self.sock_recepteur.close()
        self.sock_emetteur.close()


# =============================================================================
# DÉMONSTRATION INTER-APPLICATIVE EN DIRECT
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bus ZeroMQ Al-Mizan")
    parser.add_argument("--serveur", action="store_true", help="Lancer en tant que routeur persistant")
    args = parser.parse_args()

    if args.serveur:
        print("Démarrage du routeur central persistant...")
        routeur = RouteurBusMizan()
        routeur.demarrer(bloquant=True)
        sys.exit(0)

    print("=" * 80)
    print("  DÉMONSTRATION DU ROUTAGE MULTI-CANAUX ZEROMQ ⊗ PROTOBUF STRUCT")
    print("=" * 80)

    # 1. Démarrage du routeur en arrière-plan
    routeur = RouteurBusMizan()
    routeur.demarrer(bloquant=False)
    time.sleep(0.2)

    # 2. Création de deux modules applicatifs clients
    # Module A : Sentinelle Sécurité
    module_securite = ClientBusMizan(nom_module="SENTINELLE_SECURITE")
    # Module B : Moteur Silicium & Cryo
    module_silicium = ClientBusMizan(nom_module="MOTEUR_SILICIUM_CRYO")
    # Module C : Dashboard IHM
    module_ihm = ClientBusMizan(nom_module="DASHBOARD_IHM")

    messages_recus = []

    def on_message_ihm(canal: str, header: dict, payload: dict):
        messages_recus.append((canal, header, payload))
        print(f"\n[IHM DASHBOARD NOTIF] Message reçu sur '{canal}' !")
        print(f"  • Émetteur : {header.get('emetteur')}")
        print(f"  • Action   : {header.get('action')}")
        print(f"  • Données  : {payload}")

    # Le Dashboard IHM s'abonne à deux canaux : SILICIUM et SECURITE
    module_ihm.abonner_et_ecouter(
        canaux=["CANAL_SILICIUM_MATERIEL", "CANAL_SECURITE_AUDIT"],
        callback_reception=on_message_ihm
    )
    time.sleep(0.3)  # Attente de propagation de l'abonnement ZMQ

    # 3. Le Moteur Silicium publie de la télémétrie cryo
    print("\n>>> [1/2] Le module Silicium publie une mesure cryogénique...")
    module_silicium.publier(
        canal="CANAL_SILICIUM_MATERIEL",
        action="TELEMETRIE_CRYO_LIVE",
        donnees={
            "temperature_kelvin": 0.0225,
            "killswitch_mK": 45.0,
            "statut": "NOMINAL_STABLE",
            "decouplage_si29": True
        }
    )

    # 4. La Sentinelle Sécurité publie un audit anti-piège
    print("\n>>> [2/2] Le module Sécurité publie le score de menace...")
    module_securite.publier(
        canal="CANAL_SECURITE_AUDIT",
        action="AUDIT_CONTRAT_MAITRE",
        donnees={
            "contrat": "0x520cbd0e1e72178f9e819AFf1e815606923A71db",
            "threat_score": 98.5,
            "is_honeypot": False,
            "taxe_achat": 0.0,
            "taxe_vente": 0.0,
            "statut_scellement": "10_ACTES_SCELLÉS"
        }
    )

    # Attente de la réception
    time.sleep(0.5)

    print("\n" + "=" * 80)
    print(f"  TOTAL MESSAGES ROUTÉS PAR LE BUS : {routeur.compteur_messages}")
    print(f"  TOTAL MESSAGES REÇUS PAR L'IHM   : {len(messages_recus)}")
    print("=" * 80)

    assert len(messages_recus) == 2
    print("[SUCCÈS PARFAIT] Le bus ZeroMQ route dynamiquement toutes les structures Protobuf Struct !")

    # Nettoyage
    module_ihm.fermer()
    module_silicium.fermer()
    module_securite.fermer()
    routeur.arreter()
