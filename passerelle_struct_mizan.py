# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       PASSERELLE DE SÉRIALISATION / DÉSÉRIALISATION UNIVERSELLE
                 INTÉGRATION GOOGLE.PROTOBUF.STRUCT
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Architecture     : ZeroMQ + Protocol Buffers (Python ⊗ C++)
Rôle             : Sérialisation binaire dynamique de dictionnaires arbitraires
                   pour tous les canaux applicatifs sans modification du socle.
===============================================================================
"""

from __future__ import annotations

import time
from typing import Any, Dict, Tuple
from google.protobuf.struct_pb2 import Struct, Value
from google.protobuf.json_format import MessageToDict, ParseDict

class PasserelleStructMizan:
    """
    Module haute performance pour la conversion bidirectionnelle entre
    dictionnaires natifs et structures binaires Google Protobuf Struct.
    """

    @staticmethod
    def dict_vers_struct(d: Dict[str, Any]) -> Struct:
        """
        Convertit un dictionnaire Python (incluant listes, nombres, sous-dicts)
        en un objet google.protobuf.Struct.
        """
        s = Struct()
        s.update(d)
        return s

    @staticmethod
    def struct_vers_dict(s: Struct) -> Dict[str, Any]:
        """
        Convertit un google.protobuf.Struct en dictionnaire Python natif.
        """
        return MessageToDict(s)

    @classmethod
    def serialiser_dict_en_octets(cls, d: Dict[str, Any]) -> bytes:
        """
        Sérialise un dictionnaire Python directement en flux binaire Protobuf.
        Parfait pour l'injection directe dans les trames ZeroMQ.
        """
        s = cls.dict_vers_struct(d)
        return s.SerializeToString()

    @classmethod
    def deserialiser_octets_en_dict(cls, payload_binaire: bytes) -> Dict[str, Any]:
        """
        Reconstitue le dictionnaire Python original à partir d'un flux binaire Protobuf.
        """
        s = Struct()
        s.ParseFromString(payload_binaire)
        return cls.struct_vers_dict(s)

    @classmethod
    def emballer_message_canal(
        cls,
        canal: str,
        action: str,
        donnees: Dict[str, Any],
        id_sequence: int = 1,
        emetteur: str = "PYTHON_NOEUD_MZN"
    ) -> bytes:
        """
        Emballe un message complet de canal avec son en-tête et son dictionnaire
        dynamique de données, sérialisé en binaire pour ZeroMQ.
        """
        enveloppe = {
            "_header": {
                "id_sequence": id_sequence,
                "horloge_ts": time.time(),
                "canal": canal,
                "action": action,
                "emetteur": emetteur
            },
            "payload": donnees
        }
        return cls.serialiser_dict_en_octets(enveloppe)

    @classmethod
    def deballer_message_canal(cls, payload_binaire: bytes) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Désérialise une trame binaire ZeroMQ et retourne le couple (header, payload).
        """
        contenu = cls.deserialiser_octets_en_dict(payload_binaire)
        header = contenu.get("_header", {})
        payload = contenu.get("payload", {})
        return header, payload


# =============================================================================
# AUTO-TEST ET VALIDATION DU MODULE
# =============================================================================
if __name__ == "__main__":
    print("=" * 75)
    print("  TEST DU MODULE PASSERELLE GOOGLE.PROTOBUF.STRUCT POUR ZEROMQ")
    print("=" * 75)

    test_data = {
        "domaine": "SILICIUM",
        "temperature_mK": 22.5,
        "frequence_pompage_ghz": 5.42,
        "mode_cpmg": True,
        "invariants": {
            "C": 313,
            "bride_mizan": 0.6225,
            "ligne_reference": 0.1220,
            "riba_taux": 0.0
        },
        "vecteurs_pesee": [0.6225, 0.1220, 0.0210, 0.2400],
        "domaines_ouverts": ["QUANTIQUE", "BLOCKCHAIN", "IHM", "SECURITE"]
    }

    # 1. Sérialisation
    t0 = time.perf_counter()
    binaire = PasserelleStructMizan.emballer_message_canal(
        canal="CANAL_SILICIUM_MATERIEL",
        action="CONFIGURER_PULSE_CPMG",
        donnees=test_data,
        id_sequence=42
    )
    t_ser = (time.perf_counter() - t0) * 1e6

    print(f"[1] Sérialisation réussie : {len(binaire)} octets générés en {t_ser:.1f} µs")

    # 2. Désérialisation
    t1 = time.perf_counter()
    header, payload_recu = PasserelleStructMizan.deballer_message_canal(binaire)
    t_deser = (time.perf_counter() - t1) * 1e6

    print(f"[2] Désérialisation réussie en {t_deser:.1f} µs")
    print(f"    • Canal Reçu    : {header.get('canal')}")
    print(f"    • Action Reçue  : {header.get('action')}")
    print(f"    • Séquence ID   : {header.get('id_sequence')}")
    print(f"    • Température   : {payload_recu.get('temperature_mK')} mK")
    print(f"    • Bride Mizan   : {payload_recu.get('invariants', {}).get('bride_mizan')}")
    print(f"    • Vecteurs      : {payload_recu.get('vecteurs_pesee')}")

    # Vérification d'intégrité
    assert payload_recu["invariants"]["bride_mizan"] == 0.6225
    assert len(payload_recu["vecteurs_pesee"]) == 4
    print("\n[SUCCÈS TOTAL] Intégrité vérifiée à 100% avec google.protobuf.Struct !")
    print("=" * 75)
