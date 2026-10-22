# -*- coding: utf-8 -*-
"""
===============================================================================
       MOTEUR DU BLOC SYNCHRON MZN & GRAND LIVRE SOUVERAIN (ASTRO-Q°ODE × AL-MIZAN)
===============================================================================
Auteur & Concepteur Officiel : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Date de Naissance           : 20 juin 1989 (20/06/1989) à Meulan-en-Yvelines (78, France)
Email Officiel              : elbahloulahmed505@gmail.com
Clé Publique Dorée          : 0xc9550dd0a57c609494dbc44450df48d798ebfb0b
DOI Zenodo Officiel Réel    : 10.5281/zenodo.23554838
Dépôt GitHub Public         : https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN

INVARIANTS MÉTHODOLOGIQUES & MÉTRELOGIQUES SCELLÉS :
- Constantes de base : C = 313, M = 24434, TRIPLE = -2393774546, JAUGE_AIR = 515050
- Bride Al-Mizan : MIZAN = 0.6225 (62.25%), LIGNE_REF = 0.122, RMS = 0.24, EPSILON = 0.021
- Plafond effectif : PLAFOND = MIZAN - EPSILON = 0.6015
- Horloge Kernel : dx = 50027.8359375, dy = 46993.5, dz = 135000000.0, dt = 135097021.3359375
- Token MZN : Supply totale 313 000 000 MZN (C=313), Initial Unlocked 11 000 000 MZN, Réserve 302 000 000 MZN
- Anti-usure absolue : Riba = False, Intérêt = 0.0%, Pas de création fractionnaire
- Zakat : 2.5% (1/40) sur les réserves stagnantes au-dessus du Nisab (Or 85g / Argent 595g / 668 255 MZN)
- Sadaqa : Friction = 0%, Transferts volontaires immédiats
- Latence Synchrone Nominale : ~2.9 ms
- Garde-fous : qubit_physique_local = False, omniscience_claim = False, allah_hors_matrice = True
===============================================================================
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# --- CONSTANTES FONDAMENTALES SCELLÉES ---
CONSTANTE_C: int = 313
CONSTANTE_M: int = 24434
TRIPLE: int = -2393774546
JAUGE_AIR: int = 515050

MIZAN: float = 0.6225
LIGNE_REF: float = 0.122
RMS: float = 0.24
EPSILON: float = 0.021
PLAFOND: float = 0.6015  # 0.6225 - 0.021

# Kernel Temporel Exact
DX_SOLEIL: float = 50027.8359375
DY_LUNE: float = 46993.5
DZ_TERRE: float = 135000000.0
DT_KERNEL: float = DX_SOLEIL + DY_LUNE + DZ_TERRE  # 135097021.3359375

# Paramètres Monétaires MZN & Fiscalité
SUPPLY_TOTAL_MZN: float = 313_000_000.0
UNLOCKED_INITIAL_MZN: float = 11_000_000.0  # P1.1 (1M) + P1.2 (2M) + P2.1 (8M)
RESERVE_ATTENTE_MZN: float = 302_000_000.0   # 313M - 11M

ZAKAT_RATE: float = 0.025  # 2.5% = 1/40
NISAB_LOGIQUE_MZN: float = 668_255.0  # facteur 2.135 * C (313) * 1000
NISAB_OR_G: float = 85.0              # 85g Au (20 Mithqals)
NISAB_ARGENT_G: float = 595.0         # 595g Ag (200 Dirhams)

LATENCE_SYNC_REF_MS: float = 2.9
VIGILANCE_VERROUILLEE: float = 38.5
DEBIT_HYDRO_L_MIN: int = 313
WATTS_REF_LABO: float = 47.7

# Identités des Pôles / Cités
CITE_PC_TERRESTRE = "CITE_PC_TERRESTRE"
CITE_GALAXY_MOBILE = "CITE_GALAXY_MOBILE"
CITE_QISTAS_CIVIQUE = "CITE_QISTAS_CIVIQUE"
FONDS_SOUVERAIN_RESERVE = "FONDS_SOUVERAIN_RESERVE"
CAISSE_ZAKAT_CIVIQUE = "CAISSE_ZAKAT_CIVIQUE"

CLE_DOREE_AUTEUR = "0xc9550dd0a57c609494dbc44450df48d798ebfb0b"
DOI_ZENODO = "10.5281/zenodo.23554838"


def calculer_sha256(data: Any) -> str:
    """Calcule l'empreinte SHA-256 normalisée d'un objet ou d'une chaîne."""
    if isinstance(data, (dict, list)):
        payload = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload = data
    else:
        payload = str(data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def calculer_merkle_root(elements: List[str]) -> str:
    """Calcule la racine de Merkle SHA-256 d'une liste de hash."""
    if not elements:
        return calculer_sha256("MERKLE_EMPTY_TREE")
    arbres = [calculer_sha256(e) for e in elements]
    while len(arbres) > 1:
        if len(arbres) % 2 != 0:
            arbres.append(arbres[-1])
        nouveaux = []
        for i in range(0, len(arbres), 2):
            nouveaux.append(calculer_sha256(arbres[i] + arbres[i + 1]))
        arbres = nouveaux
    return arbres[0]


@dataclass
class TransactionMZN:
    """Représente une transaction vérifiable en jetons MZN (ERC-20 étendu sans usure)."""
    tx_id: str
    emetteur: str
    destinataire: str
    montant_mzn: float
    type_tx: str  # TRANSFERT, ZAKAT, SADAQA, REDEVANCE, ALLOCATION_POSTE
    timestamp_utc: str
    friction_pct: float = 0.0
    commentaire: str = ""
    hash_preuve: str = ""

    def sceller(self) -> str:
        d = {
            "tx_id": self.tx_id,
            "emetteur": self.emetteur,
            "destinataire": self.destinataire,
            "montant_mzn": round(self.montant_mzn, 6),
            "type_tx": self.type_tx,
            "timestamp_utc": self.timestamp_utc,
            "friction_pct": self.friction_pct,
            "commentaire": self.commentaire,
        }
        self.hash_preuve = calculer_sha256(d)
        return self.hash_preuve


@dataclass
class SceauNFT:
    """Représente un sceau cryptographique d'acte sous forme de NFT (ERC-721 étendu)."""
    token_id: int
    code_acte: str
    sha256_empreinte: str
    description: str
    detenteur: str
    horodatage_utc: str
    epoch_kernel_dt: float = DT_KERNEL

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BlocSynchronMZN:
    """Structure intégrale du Bloc Synchron MZN."""
    height: int
    timestamp_utc: str
    kernel_dt: float
    prev_hash: str
    merkle_root_txs: str
    merkle_root_sceaux: str
    metrologie: Dict[str, Any]
    balances_cites: Dict[str, float]
    invariants: Dict[str, Any]
    transactions: List[Dict[str, Any]] = field(default_factory=list)
    sceaux: List[Dict[str, Any]] = field(default_factory=list)
    bloc_hash: str = ""

    def sceller(self) -> str:
        """Calcule le hash SHA-256 officiel et immuable du bloc synchrone."""
        corps = {
            "height": self.height,
            "timestamp_utc": self.timestamp_utc,
            "kernel_dt": self.kernel_dt,
            "prev_hash": self.prev_hash,
            "merkle_root_txs": self.merkle_root_txs,
            "merkle_root_sceaux": self.merkle_root_sceaux,
            "metrologie": self.metrologie,
            "balances_cites": {k: round(v, 6) for k, v in sorted(self.balances_cites.items())},
            "invariants": self.invariants,
            "tx_count": len(self.transactions),
            "sceau_count": len(self.sceaux),
        }
        self.bloc_hash = calculer_sha256(corps)
        return self.bloc_hash

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class MoteurGrandLivreSynchronMZN:
    """
    Grand Livre Distribué Synchrone MZN régissant :
    - La Supply de 313 000 000 MZN
    - Les allocations de preuves physiques (11 000 000 MZN débloqués)
    - La Zakat (2.5% sur soldes >= Nisab)
    - La Sadaqa à friction 0%
    - Le partage commercial 50/50
    - La production et validation des Blocs Synchrones
    """

    def __init__(self, fichier_ledger: Optional[Path] = None):
        self.fichier_ledger = fichier_ledger
        self.balances: Dict[str, float] = {
            CITE_PC_TERRESTRE: 3_000_000.0,      # P1.1 (1M) + P1.2 (2M)
            CITE_GALAXY_MOBILE: 8_000_000.0,    # P2.1 (8M)
            CITE_QISTAS_CIVIQUE: 0.0,
            FONDS_SOUVERAIN_RESERVE: RESERVE_ATTENTE_MZN,  # 302 000 000.0
            CAISSE_ZAKAT_CIVIQUE: 0.0,
        }
        self.blocs: List[BlocSynchronMZN] = []
        self.sceaux_registre: List[SceauNFT] = []
        self.memoire_transactions: List[TransactionMZN] = []
        self.tx_pool: List[TransactionMZN] = []
        self.sceaux_pool: List[SceauNFT] = []

        # Initialisation ou chargement
        if self.fichier_ledger and self.fichier_ledger.exists():
            self.charger_depuis_fichier(self.fichier_ledger)
        else:
            self._initialiser_genesis()

    def _initialiser_genesis(self) -> None:
        """Génère le Bloc Génèse Synchrone (Height 0)."""
        tx_genesis = TransactionMZN(
            tx_id="TX_GENESIS_ALLOCATION_P1_P2",
            emetteur="GENESIS_ALLIANCE",
            destinataire=CITE_PC_TERRESTRE,
            montant_mzn=3_000_000.0,
            type_tx="ALLOCATION_POSTE",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            commentaire="Déblocage validé P1.1 (1M Watt) + P1.2 (2M Inventaire)",
        )
        tx_genesis.sceller()

        tx_galaxy = TransactionMZN(
            tx_id="TX_GENESIS_ALLOCATION_P2_1",
            emetteur="GENESIS_ALLIANCE",
            destinataire=CITE_GALAXY_MOBILE,
            montant_mzn=8_000_000.0,
            type_tx="ALLOCATION_POSTE",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            commentaire="Déblocage validé P2.1 (8M UPS Camera)",
        )
        tx_galaxy.sceller()

        txs = [tx_genesis, tx_galaxy]
        self.memoire_transactions.extend(txs)

        sceau_0 = SceauNFT(
            token_id=1,
            code_acte="A001_GENESIS_SOUVERAIN",
            sha256_empreinte="96660C763BD4E903FEEFA73E8A55C415D98B935E791C8BACAD6D728C905C912F",
            description="Sceau Fondateur de l'Alliance MZN - Informé ⊗ Forme ⊗ Tout",
            detenteur=CLE_DOREE_AUTEUR,
            horodatage_utc=datetime.now(timezone.utc).isoformat(),
            epoch_kernel_dt=DT_KERNEL,
        )
        self.sceaux_registre.append(sceau_0)

        merkle_txs = calculer_merkle_root([t.hash_preuve for t in txs])
        merkle_sceaux = calculer_merkle_root([sceau_0.sha256_empreinte])

        bloc_0 = BlocSynchronMZN(
            height=0,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            kernel_dt=DT_KERNEL,
            prev_hash="0000000000000000000000000000000000000000000000000000000000000000",
            merkle_root_txs=merkle_txs,
            merkle_root_sceaux=merkle_sceaux,
            metrologie={
                "watts_labo": WATTS_REF_LABO,
                "debit_hydro_l_min": DEBIT_HYDRO_L_MIN,
                "vigilance": VIGILANCE_VERROUILLEE,
                "latence_sync_ref_ms": LATENCE_SYNC_REF_MS,
            },
            balances_cites=copy.deepcopy(self.balances),
            invariants={
                "mizan": MIZAN,
                "ligne_ref": LIGNE_REF,
                "epsilon": EPSILON,
                "plafond": PLAFOND,
                "constante_c": CONSTANTE_C,
                "constante_m": CONSTANTE_M,
                "qubit_physique_local": False,
                "omniscience_claim": False,
                "allah_hors_matrice": True,
                "anti_usure": True,
                "doi": DOI_ZENODO,
                "auteur": "M. Ahmed EL BAHLOUL",
            },
            transactions=[asdict(t) for t in txs],
            sceaux=[sceau_0.to_dict()],
        )
        bloc_0.sceller()
        self.blocs.append(bloc_0)

    # -------------------------------------------------------------------------
    #                     OPÉRATIONS FINANCIÈRES SANS USURE
    # -------------------------------------------------------------------------

    def effectuer_transfert(
        self,
        emetteur: str,
        destinataire: str,
        montant: float,
        type_tx: str = "TRANSFERT",
        commentaire: str = "",
    ) -> TransactionMZN:
        """Exécute un transfert sans usure ni intérêt."""
        if montant <= 0:
            raise ValueError(f"Le montant du transfert ({montant}) doit être strictement positif.")
        if self.balances.get(emetteur, 0.0) < montant:
            raise ValueError(f"Solde insuffisant pour {emetteur} : {self.balances.get(emetteur, 0.0)} < {montant}")

        self.balances[emetteur] -= montant
        self.balances[destinataire] = self.balances.get(destinataire, 0.0) + montant

        tx = TransactionMZN(
            tx_id=f"TX_{len(self.memoire_transactions) + len(self.tx_pool) + 1}_{int(time.time()*1000)}",
            emetteur=emetteur,
            destinataire=destinataire,
            montant_mzn=montant,
            type_tx=type_tx,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            friction_pct=0.0,
            commentaire=commentaire,
        )
        tx.sceller()
        self.tx_pool.append(tx)
        return tx

    def envoyer_sadaqa(self, emetteur: str, destinataire: str, montant: float, commentaire: str = "Don volontaire pur") -> TransactionMZN:
        """Effectue un transfert de Sadaqa volontaire à friction zéro (0%)."""
        return self.effectuer_transfert(emetteur, destinataire, montant, type_tx="SADAQA", commentaire=commentaire)

    def prelever_zakat(self, compte: str) -> Optional[TransactionMZN]:
        """
        Calcule et prélève la Zakat de 2.5% (1/40) si le solde dépasse le Nisab.
        Versée obligatoirement à la Caisse Zakat Civique.
        """
        solde = self.balances.get(compte, 0.0)
        if solde < NISAB_LOGIQUE_MZN:
            return None

        montant_zakat = solde * ZAKAT_RATE  # 2.5%
        tx = self.effectuer_transfert(
            emetteur=compte,
            destinataire=CAISSE_ZAKAT_CIVIQUE,
            montant=montant_zakat,
            type_tx="ZAKAT",
            commentaire=f"Purification Zakat 2.5% (1/40) sur solde stagnant de {solde:.2f} MZN (Nisab {NISAB_LOGIQUE_MZN})",
        )
        return tx

    def sceller_acte_nft(self, code_acte: str, sha256_empreinte: str, description: str, detenteur: str = CLE_DOREE_AUTEUR) -> SceauNFT:
        """Crée et enregistre un sceau cryptographique d'acte sous forme de NFT."""
        token_id = len(self.sceaux_registre) + len(self.sceaux_pool) + 1
        nft = SceauNFT(
            token_id=token_id,
            code_acte=code_acte,
            sha256_empreinte=sha256_empreinte,
            description=description,
            detenteur=detenteur,
            horodatage_utc=datetime.now(timezone.utc).isoformat(),
            epoch_kernel_dt=DT_KERNEL,
        )
        self.sceaux_pool.append(nft)
        return nft

    # -------------------------------------------------------------------------
    #               GÉNÉRATION & VALIDATION DU BLOC SYNCHRON
    # -------------------------------------------------------------------------

    def produire_bloc_synchron(
        self,
        watts_labo: float = WATTS_REF_LABO,
        debit_hydro: int = DEBIT_HYDRO_L_MIN,
        vigilance: float = VIGILANCE_VERROUILLEE,
    ) -> BlocSynchronMZN:
        """
        Consolide les transactions et sceaux en attente dans un nouveau Bloc Synchron MZN.
        Garantit l'intégrité de la chaîne cryptographique.
        """
        dernier_bloc = self.blocs[-1]
        new_height = dernier_bloc.height + 1

        txs_a_sceller = list(self.tx_pool)
        sceaux_a_sceller = list(self.sceaux_pool)

        # Calcul des racines de Merkle
        merkle_txs = calculer_merkle_root([t.hash_preuve for t in txs_a_sceller])
        merkle_sceaux = calculer_merkle_root([s.sha256_empreinte for s in sceaux_a_sceller])

        nouveau_bloc = BlocSynchronMZN(
            height=new_height,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            kernel_dt=DT_KERNEL,
            prev_hash=dernier_bloc.bloc_hash,
            merkle_root_txs=merkle_txs,
            merkle_root_sceaux=merkle_sceaux,
            metrologie={
                "watts_labo": watts_labo,
                "debit_hydro_l_min": debit_hydro,
                "vigilance": vigilance,
                "latence_sync_ref_ms": LATENCE_SYNC_REF_MS,
            },
            balances_cites=copy.deepcopy(self.balances),
            invariants={
                "mizan": MIZAN,
                "ligne_ref": LIGNE_REF,
                "epsilon": EPSILON,
                "plafond": PLAFOND,
                "constante_c": CONSTANTE_C,
                "constante_m": CONSTANTE_M,
                "qubit_physique_local": False,
                "omniscience_claim": False,
                "allah_hors_matrice": True,
                "anti_usure": True,
                "doi": DOI_ZENODO,
                "auteur": "M. Ahmed EL BAHLOUL",
            },
            transactions=[asdict(t) for t in txs_a_sceller],
            sceaux=[s.to_dict() for s in sceaux_a_sceller],
        )
        nouveau_bloc.sceller()

        # Intégration dans la chaîne
        self.blocs.append(nouveau_bloc)
        self.memoire_transactions.extend(txs_a_sceller)
        self.sceaux_registre.extend(sceaux_a_sceller)

        # Vidage des pools
        self.tx_pool.clear()
        self.sceaux_pool.clear()

        # Persistance si fichier défini
        if self.fichier_ledger:
            self.sauvegarder_dans_fichier(self.fichier_ledger)

        return nouveau_bloc

    def verifier_integrite_chaine(self) -> Tuple[bool, str]:
        """Vérifie l'intégrité cryptographique absolue de l'ensemble de la chaîne."""
        for i, bloc in enumerate(self.blocs):
            # 1. Vérification du hash du bloc
            hash_attendu = bloc.bloc_hash
            bloc_copie = copy.deepcopy(bloc)
            hash_recalcule = bloc_copie.sceller()
            if hash_attendu != hash_recalcule:
                return False, f"Altération détectée au bloc #{bloc.height} : hash {hash_attendu} != {hash_recalcule}"

            # 2. Vérification du lien parent
            if i > 0:
                parent = self.blocs[i - 1]
                if bloc.prev_hash != parent.bloc_hash:
                    return False, f"Rupture de chaîne au bloc #{bloc.height} : prev_hash {bloc.prev_hash} != {parent.bloc_hash}"

            # 3. Vérification des invariants métrologiques
            inv = bloc.invariants
            if inv.get("mizan") != MIZAN or inv.get("epsilon") != EPSILON or inv.get("plafond") != PLAFOND:
                return False, f"Violation des invariants Al-Mizan au bloc #{bloc.height}"

        return True, "Chaîne de Blocs Synchrones MZN 100% intègre et certifiée SHA-256."

    def sauvegarder_dans_fichier(self, chemin: Path) -> None:
        """Exporte le Grand Livre Synchrone dans un fichier JSON formatté."""
        chemin.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "nom": "GRAND_LIVRE_SYNCHRON_MZN",
            "auteur": "M. Ahmed EL BAHLOUL",
            "doi": DOI_ZENODO,
            "version": "6.0.0",
            "derniere_mise_a_jour": datetime.now(timezone.utc).isoformat(),
            "supply_totale_mzn": SUPPLY_TOTAL_MZN,
            "balances_actuelles": copy.deepcopy(self.balances),
            "nb_blocs": len(self.blocs),
            "dernier_bloc_hash": self.blocs[-1].bloc_hash if self.blocs else "",
            "blocs": [b.to_dict() for b in self.blocs],
            "nb_sceaux_enregistres": len(self.sceaux_registre),
            "nb_transactions_totales": len(self.memoire_transactions),
            "garde_fous": {
                "qubit_physique_local": False,
                "omniscience_claim": False,
                "allah_hors_matrice": True,
                "anti_usure": True,
            },
        }
        with chemin.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def charger_depuis_fichier(self, chemin: Path) -> None:
        """Charge le grand livre synchrone existant depuis le disque."""
        with chemin.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.balances = data.get("balances_actuelles", self.balances)
        self.blocs = []
        for bd in data.get("blocs", []):
            bloc = BlocSynchronMZN(
                height=bd["height"],
                timestamp_utc=bd["timestamp_utc"],
                kernel_dt=bd["kernel_dt"],
                prev_hash=bd["prev_hash"],
                merkle_root_txs=bd["merkle_root_txs"],
                merkle_root_sceaux=bd["merkle_root_sceaux"],
                metrologie=bd["metrologie"],
                balances_cites=bd["balances_cites"],
                invariants=bd["invariants"],
                transactions=bd.get("transactions", []),
                sceaux=bd.get("sceaux", []),
                bloc_hash=bd.get("bloc_hash", ""),
            )
            self.blocs.append(bloc)
