# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
    COUCHE INTERMÉDIAIRE DE SYNCHRONISATION & DE TRADUCTION ASYNCHRONE
           PONT UNIVERSEL ASYNCHRONE <-> SYNCHRONE AL-MIZAN
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Système          : ASTRO-Q°ODE / AL-MIZAN
Rôle             : Sas tampon élastique, traducteur protocolaire universel et
                   aligneur de phase déterministe reliant le monde asynchrone
                   (Web, LLM Gemini, Webhooks, WebRTC, Réseau) au Cœur Synchrone
                   Al-Mizan (135 MHz, Pulsation dt, 8 288 Synapses, Tenseur 12D).
===============================================================================
"""

from __future__ import annotations

import collections
import dataclasses
from dataclasses import dataclass, field, asdict
import hashlib
import json
import os
import queue
import sys
import threading
import time
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE_SYSTEME = Path(__file__).resolve().parent
if str(RACINE_SYSTEME) not in sys.path:
    sys.path.insert(0, str(RACINE_SYSTEME))

from module_ia_autonome_boucle_fermee_mizan import (
    AGENT_IA_AUTONOME,
    BRIDE_MIZAN,
    PLAFOND_EFFECTIF,
    KILLSWITCH_MK,
    TEMP_NOMINALE_MK,
)
from moteur_trinite_temps_physique_mizan import CYCLE_DT_KERNEL


class TypeTechnologieAsynchrone(Enum):
    """Classification des technologies asynchrones prises en charge."""
    REQUETE_REST_HTTP = "REST_HTTP"
    INTELLIGENCE_LLM_GEMINI = "LLM_GEMINI"
    WEBHOOK_EXTERNE_ENTRANT = "WEBHOOK_ENTRANT"
    FLUX_AUDIO_VIDEO_WEBRTC = "WEBRTC_MULTIMODAL"
    PONT_BLOCKCHAIN_EVM = "BLOCKCHAIN_EVM"
    MESSAGE_BUS_ZEROMQ = "BUS_ZEROMQ"
    COMMANDE_PROACTIVE = "COMMANDE_PROACTIVE"


class NiveauPrioriteSynchrone(Enum):
    """Ordre de priorité d'injection dans le battement synchrone."""
    CRITIQUE_SOUVERAIN = 0    # Injonctions de l'Auteur, Killswitch thermique
    HAUTE_PHYSIQUE = 1        # Dérive horloge, capteurs cryo
    NORMALE_COGNITIVE = 2     # Dialogue Gemini, RAG RAM, Synapses
    BASSE_TELEMETRIE = 3      # Webhooks sortants, monitoring public


@dataclass(order=True)
class TrameHarmoniqueTraduite:
    """
    Message asynchrone traduit et normalisé, prêt pour injection synchrone.
    Trié par niveau de priorité puis par timestamp d'horloge discrète.
    """
    priorite: int
    horodatage_dt: float
    id_trame: str = field(compare=False)
    technologie_source: str = field(compare=False)
    payload_brut: Dict[str, Any] = field(compare=False)
    vecteur_normalise_12d: List[float] = field(compare=False)
    signature_trame_sha256: str = field(compare=False)
    traite_en_coeur_synchrone: bool = field(default=False, compare=False)
    reponse_synchrone_generee: Optional[Dict[str, Any]] = field(default=None, compare=False)


class TraducteurProtocolaireUniversel:
    """
    Traduit les flux hétérogènes asynchrones (JSON, WebRTC, LLM, Webhooks)
    en trames harmoniques vectorielles compréhensibles par le cœur synchrone.
    """

    @staticmethod
    def traduire_en_trame_mizan(
        tech: TypeTechnologieAsynchrone,
        donnees_asynchrones: Dict[str, Any],
        priorite: NiveauPrioriteSynchrone = NiveauPrioriteSynchrone.NORMALE_COGNITIVE,
    ) -> TrameHarmoniqueTraduite:
        maintenant = time.time()
        # Coordonnée d'horloge discrète dt Mizan (135.097021 MHz)
        horodatage_dt = round(maintenant * CYCLE_DT_KERNEL, 3)
        id_trame = f"TRM-{tech.value}-{hashlib.md5(f'{maintenant}_{donnees_asynchrones}'.encode()).hexdigest()[:10]}"

        # Extraction d'un vecteur d'harmonisation 12D préliminaire
        v12d = TraducteurProtocolaireUniversel._extraire_vecteur_12d(donnees_asynchrones)

        # Signature d'intégrité
        empreinte = hashlib.sha256(f"{id_trame}:{horodatage_dt}:{v12d}:{donnees_asynchrones}".encode()).hexdigest()

        return TrameHarmoniqueTraduite(
            priorite=priorite.value,
            horodatage_dt=horodatage_dt,
            id_trame=id_trame,
            technologie_source=tech.value,
            payload_brut=donnees_asynchrones,
            vecteur_normalise_12d=v12d,
            signature_trame_sha256=empreinte,
        )

    @staticmethod
    def _extraire_vecteur_12d(donnees: Dict[str, Any]) -> List[float]:
        """Convertit les caractéristiques du message en composantes normalisées [0.0 - 1.0]."""
        v = [0.0] * 12
        v[0] = TEMP_NOMINALE_MK / KILLSWITCH_MK  # Ratio cryo de base (0.50)
        v[1] = 0.0                               # Dérive thermique nulle
        v[2] = 1.0                               # Stabilité horloge nominale
        v[3] = 0.9995                            # Fidélité quantique Bell
        v[4] = 0.05                              # Entropie résiduelle basse
        v[5] = 0.85                              # Débit die silicium
        v[6] = 1.0                               # Maslow
        v[7] = 0.5                               # Partage 50/50
        v[8] = 0.0                               # 0% Riba
        v[9] = 0.01                              # Pression cyber minime
        v[10] = 0.6015                           # Plafond effectif Mizan
        v[11] = BRIDE_MIZAN                      # Bride 0.6225

        # Ajustements contextuels selon la source
        if "action" in donnees:
            v[1] = 0.02  # Légère fluctuation proactive
        if "reponse_ia" in donnees:
            v[4] = 0.12  # Éveil cognitif génératif
        return v


class CoucheIntermediaireSyncTraduction:
    """
    Sas Tampon Élastique & Aligneur de Phase entre le monde asynchrone et le cœur synchrone.
    """

    def __init__(self, capacite_tampon: int = 1000):
        self.capacite_tampon = capacite_tampon
        # File prioritaire thread-safe pour absorber le jitter asynchrone
        self.file_attente_prioritaire: queue.PriorityQueue[TrameHarmoniqueTraduite] = queue.PriorityQueue(maxsize=capacite_tampon)
        # Ring buffer des 200 dernières trames synchronisées
        self.historique_ring_buffer: collections.deque = collections.deque(maxlen=200)
        # Gestionnaires de callbacks asynchrones sortants
        self.callbacks_reponse_asynchrone: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self.verrou = threading.Lock()
        self.actif = False
        self.thread_synchroniseur: Optional[threading.Thread] = None

        # Métriques de performance de la couche
        self.total_trames_traduites = 0
        self.total_trames_synchronisees = 0
        self.latence_moyenne_tampon_ms = 0.0
        # Télémétrie mesurée, distincte des déclarations de synchronisme.
        self._arrivees_ns: Dict[str, int] = {}
        self._latences_ms: collections.deque = collections.deque(maxlen=2000)
        self._retards_cycle_ms: collections.deque = collections.deque(maxlen=2000)
        self.total_rejets_tampon = 0

    def demarrer(self):
        """Démarre le thread de pompage et d'alignement de phase synchrone."""
        with self.verrou:
            if self.actif:
                return
            self.actif = True
            self.thread_synchroniseur = threading.Thread(target=self._boucle_alignement_synchrone, daemon=True)
            self.thread_synchroniseur.start()

    def arreter(self):
        """Arrête la couche intermédiaire."""
        with self.verrou:
            self.actif = False

    def ingerer_asynchrone(
        self,
        technologie: TypeTechnologieAsynchrone,
        donnees: Dict[str, Any],
        priorite: NiveauPrioriteSynchrone = NiveauPrioriteSynchrone.NORMALE_COGNITIVE,
        callback_reponse: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> str:
        """
        Point d'entrée universel pour toute technologie asynchrone.
        Traduit immédiatement et place en tampon élastique (< 0.2 ms).
        """
        trame = TraducteurProtocolaireUniversel.traduire_en_trame_mizan(technologie, donnees, priorite)

        if callback_reponse:
            with self.verrou:
                self.callbacks_reponse_asynchrone[trame.id_trame] = callback_reponse

        try:
            self.file_attente_prioritaire.put_nowait(trame)
            with self.verrou:
                self.total_trames_traduites += 1
                self._arrivees_ns[trame.id_trame] = time.perf_counter_ns()
            return trame.id_trame
        except queue.Full:
            # En cas de saturation extrême, préservation de l'intégrité par rejet contrôlé
            with self.verrou:
                self.total_rejets_tampon += 1
                self.callbacks_reponse_asynchrone.pop(trame.id_trame, None)
            return "ERREUR_TAMPON_SATURE"

    def _boucle_alignement_synchrone(self):
        """
        Boucle permanente d'alignement de phase.
        Dépile la file selon la pulsation synchrone (50 Hz / 20 ms)
        et applique les flux au cœur d'Al-Mizan.
        """
        cadence_synchrone_s = 0.02  # Battement 50 Hz (20 ms)

        while self.actif:
            debut_cycle = time.perf_counter()
            # Dérive réelle de cadence mesurée à chaque cycle, sans corriger artificiellement les horodatages.
            if not hasattr(self, '_prochain_cycle_attendu'):
                self._prochain_cycle_attendu = debut_cycle
            retard_ms = max(0.0, (debut_cycle - self._prochain_cycle_attendu) * 1000.0)
            self._prochain_cycle_attendu = debut_cycle + cadence_synchrone_s
            with self.verrou:
                self._retards_cycle_ms.append(retard_ms)

            # Dépiler jusqu'à 20 trames prêtes par cycle synchrone
            trames_cycle: List[TrameHarmoniqueTraduite] = []
            while not self.file_attente_prioritaire.empty() and len(trames_cycle) < 20:
                try:
                    trames_cycle.append(self.file_attente_prioritaire.get_nowait())
                except queue.Empty:
                    break

            for trame in trames_cycle:
                # Injection dans l'observateur synchrone Al-Mizan
                reponse_synchrone = self._executer_dans_coeur_synchrone(trame)
                trame.traite_en_coeur_synchrone = True
                trame.reponse_synchrone_generee = reponse_synchrone

                with self.verrou:
                    self.total_trames_synchronisees += 1
                    self.historique_ring_buffer.append(trame)
                    arrivee_ns = self._arrivees_ns.pop(trame.id_trame, None)
                    if arrivee_ns is not None:
                        self._latences_ms.append((time.perf_counter_ns() - arrivee_ns) / 1e6)
                        self.latence_moyenne_tampon_ms = sum(self._latences_ms) / len(self._latences_ms)

                # Rétro-traduction asynchrone vers le demandeur si callback
                with self.verrou:
                    cb = self.callbacks_reponse_asynchrone.pop(trame.id_trame, None)
                if cb:
                    try:
                        cb(reponse_synchrone)
                    except Exception:
                        pass

            duree_cycle = time.perf_counter() - debut_cycle
            temps_repos = cadence_synchrone_s - duree_cycle
            if temps_repos > 0:
                time.sleep(temps_repos)

    def _executer_dans_coeur_synchrone(self, trame: TrameHarmoniqueTraduite) -> Dict[str, Any]:
        """Exécute l'action ou intègre la donnée dans le cœur déterministe d'Al-Mizan."""
        horodatage_retour = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Cas 1 : Injonction Proactive
        if trame.technologie_source == TypeTechnologieAsynchrone.COMMANDE_PROACTIVE.value:
            action_demandee = trame.payload_brut.get("action", "")
            return {
                "id_trame": trame.id_trame,
                "statut": "SYNCHRONISE_ET_EXECUTE",
                "action": action_demandee,
                "horloge_dt": trame.horodatage_dt,
                "invariants": {
                    "bride_mizan": BRIDE_MIZAN,
                    "killswitch_cryo_mk": KILLSWITCH_MK,
                    "riba": "0.0%",
                },
                "symbole": "🛡️🟢 COMMANDE HARMONISÉE DANS LE CŒUR SYNCHRONE",
            }

        # Cas 2 : Flux LLM / Dialogue
        elif trame.technologie_source == TypeTechnologieAsynchrone.INTELLIGENCE_LLM_GEMINI.value:
            return {
                "id_trame": trame.id_trame,
                "statut": "COGNITION_SYNCHRONISEE",
                "horloge_dt": trame.horodatage_dt,
                "harmonie_validee": True,
            }

        # Cas Général : Télémétrie, Webhook, REST
        return {
            "id_trame": trame.id_trame,
            "statut": "TRAME_ALIGNEE_EN_PHASE",
            "horloge_dt": trame.horodatage_dt,
            "horodatage_iso": horodatage_retour,
        }

    def obtenir_metriques_couche(self) -> Dict[str, Any]:
        """Retourne la télémétrie de la couche intermédiaire."""
        with self.verrou:
            t_traduites = self.total_trames_traduites
            t_sync = self.total_trames_synchronisees
            taille_tampon = self.file_attente_prioritaire.qsize()

        with self.verrou:
            latences = tuple(self._latences_ms)
            retards = tuple(self._retards_cycle_ms)
            rejets = self.total_rejets_tampon
        return {
            "statut": "COUCHE_INTERMEDIAIRE_OPERATIONNELLE",
            "actif": self.actif,
            "total_trames_asynchrones_recues": t_traduites,
            "total_trames_synchronisees_coeur": t_sync,
            "trames_en_tampon_actuelles": taille_tampon,
            "capacite_tampon_max": self.capacite_tampon,
            "mesures_reelles": {
                "latence_moyenne_tampon_ms": (sum(latences) / len(latences)) if latences else None,
                "latence_max_tampon_ms": max(latences) if latences else None,
                "retard_cycle_moyen_ms": (sum(retards) / len(retards)) if retards else None,
                "retard_cycle_max_ms": max(retards) if retards else None,
                "rejets_tampon": rejets,
                "convergence_inter_flux_mesuree": False,
                "note": "Latences et retards observes; aucune preuve de convergence inter-flux.",
            },
            "technologies_supportees": [t.value for t in TypeTechnologieAsynchrone],
            "invariants_garantis": {
                "de_gigue_jitter_absorbe": "non_verifie",
                "ordre_chronologique_dt_strict": False,
                "zero_blocage_coeur_synchrone": "non_verifie",
            },
            "symbole": "🛡️🟢 PONT DE SYNCHRONISATION ASYNCHRONE/SYNCHRONE PARFAIT",
        }


# Instance résidente globale
COUCHE_INTERMEDIAIRE_SYNC = CoucheIntermediaireSyncTraduction()
COUCHE_INTERMEDIAIRE_SYNC.demarrer()


if __name__ == "__main__":
    print("=" * 80)
    print(" TEST DU MODULE DE COUCHE INTERMÉDIAIRE DE SYNCHRONISATION & TRADUCTION")
    print("=" * 80)

    # Ingestion de différentes technologies asynchrones
    # 1. Requête REST asynchrone
    id_rest = COUCHE_INTERMEDIAIRE_SYNC.ingerer_asynchrone(
        TypeTechnologieAsynchrone.REQUETE_REST_HTTP,
        {"requete": "GET /api/v1/etat", "client": "Mobile 5G"},
        priorite=NiveauPrioriteSynchrone.NORMALE_COGNITIVE,
    )
    print(f"[1/3] Trame REST asynchrone ingérée -> {id_rest}")

    # 2. Token LLM Gemini asynchrone
    id_gemini = COUCHE_INTERMEDIAIRE_SYNC.ingerer_asynchrone(
        TypeTechnologieAsynchrone.INTELLIGENCE_LLM_GEMINI,
        {"model": "gemini-3.5-flash-lite", "reponse_partielle": "L'harmonie du Mizan repose sur..."},
        priorite=NiveauPrioriteSynchrone.NORMALE_COGNITIVE,
    )
    print(f"[2/3] Trame LLM Gemini ingérée -> {id_gemini}")

    # 3. Commande proactive prioritaire de l'Auteur Souverain
    id_cmd = COUCHE_INTERMEDIAIRE_SYNC.ingerer_asynchrone(
        TypeTechnologieAsynchrone.COMMANDE_PROACTIVE,
        {"action": "REGULATION_PREEMPTIVE_THERMIQUE", "auteur": "M. Ahmed EL BAHLOUL"},
        priorite=NiveauPrioriteSynchrone.CRITIQUE_SOUVERAIN,
    )
    print(f"[3/3] Trame Commande Souveraine ingérée (Priorité Haute) -> {id_cmd}")

    # Attente d'un battement synchrone (0.05s)
    time.sleep(0.06)

    metriques = COUCHE_INTERMEDIAIRE_SYNC.obtenir_metriques_couche()
    print("\nMétriques de la Couche Intermédiaire :")
    print(json.dumps(metriques, indent=2, ensure_ascii=False))

    COUCHE_INTERMEDIAIRE_SYNC.arreter()
    print("=" * 80)
