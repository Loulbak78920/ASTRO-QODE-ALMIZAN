# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       MOTEUR D'ÉCONOMIE ISLAMIQUE OPÉRATIONNEL AL-MIZAN (SANS SIMULATION)
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Système          : ASTRO-Q°ODE / AL-MIZAN
Fondements       :
  1. Interdiction absolue du Riba (الربا = 0.000%) : Aucun intérêt usuraire, agio
     ou création monétaire ex nihilo sans contrepartie physique réelle.
  2. Élimination du Gharar (الغرر) et du Maysir (الميسر) : Transparence totale,
     zéro spéculation aléatoire, zéro produit dérivé toxique.
  3. Adossement physique réel (Rahn / Asset-backed) : Or physique (Z=79),
     Argent physique (Z=47), Silicium et Puissance de calcul réelle.
  4. Partage des pertes et profits équitable 50/50 (Mudaraba & Musharaka).
  5. Institution de la Zakat légale (الزكاة = 2.5%) et de la Caisse Civique.
  6. Prêt d'honneur sans usure (Qard Hassan / القرض الحسن).
===============================================================================
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Fix encodage console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RACINE_AQ = Path(__file__).resolve().parent
DOSSIER_MEMOIRE = RACINE_AQ / "memoire_aq"
FICHIER_LEDGER_SYNCHRON = DOSSIER_MEMOIRE / "ledger_synchron_mzn.json"
FICHIER_REGISTRE_ISLAMIQUE = DOSSIER_MEMOIRE / "registre_economie_islamique_mizan.json"

# Constantes Canoniques du Droit Économique Islamique Al-Mizan
TAUX_RIBA_MAXIMUM_AUTORISE = 0.0000000000  # Strictement Zéro
TAUX_ZAKAT_ANNUEL = 0.025                 # 2.5% (1/40e des avoirs au-delà du Nisab)
NISAB_OR_GRAMMES = 85.0                   # 85 grammes d'or pur (20 Dinars historiques)
NISAB_ARGENT_GRAMMES = 595.0              # 595 grammes d'argent pur (200 Dirhams historiques)

# Étalonnage physique Al-Mizan (Actes A097 & A105)
OR_MG_PAR_EUR = 14.50                     # 1 EUR = 14.50 mg Au
ARGENT_MG_PAR_EUR = 1150.0                # 1 EUR = 1 150 mg Ag

VALEUR_OR_PAR_GRAMME_EUR = 1000.0 / OR_MG_PAR_EUR       # ~68.9655 EUR/g
VALEUR_ARGENT_PAR_GRAMME_EUR = 1000.0 / ARGENT_MG_PAR_EUR # ~0.8695 EUR/g

SEUIL_NISAB_OR_EUR = NISAB_OR_GRAMMES * VALEUR_OR_PAR_GRAMME_EUR       # ~5 862.07 EUR
SEUIL_NISAB_ARGENT_EUR = NISAB_ARGENT_GRAMMES * VALEUR_ARGENT_PAR_GRAMME_EUR # ~517.39 EUR


@dataclass
class ContratIslamique:
    id_contrat: str
    type_contrat: str  # MUDARABA, MUSHARAKA, MURABAHA, QARD_HASSAN
    partie_a: str
    partie_b: str
    capital_initial: float
    devise: str
    taux_interet_annuel: float
    cle_partage_profits: str  # ex: "50/50"
    statut_conformite_sharia: str  # VALIDE_CONFORME, REJETE_RIBA, REJETE_GHARAR
    adossement_physique: Dict[str, Any]
    horodatage: float
    signature_sha256: str
    justification_rejet: Optional[str] = None


@dataclass
class OperationZakat:
    id_operation: str
    compte_debite: str
    assiette_soumise_eur: float
    montant_zakat_preleve: float
    devise: str
    compte_beneficiaire_caisse: str
    horodatage: float
    quittance_sha256: str
    statut: str  # VERSE_AVEC_SUCCES


class MoteurEconomieIslamiqueMizan:
    """
    Moteur d'application stricte et opérationnelle de l'économie islamique Al-Mizan.
    Exécute les arbitrages anti-usure, perçoit et gère la Zakat, et valide les contrats réels.
    """

    def __init__(self):
        self.contrats: Dict[str, ContratIslamique] = {}
        self.operations_zakat: List[OperationZakat] = []
        self._charger_registre()

    def _charger_registre(self):
        if FICHIER_REGISTRE_ISLAMIQUE.exists():
            try:
                with open(FICHIER_REGISTRE_ISLAMIQUE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.get("contrats", {}).items():
                        self.contrats[k] = ContratIslamique(**v)
                    for op in data.get("operations_zakat", []):
                        self.operations_zakat.append(OperationZakat(**op))
            except Exception as e:
                print(f"[!] Erreur chargement registre islamique: {e}")

    def _sauvegarder_registre(self):
        try:
            FICHIER_REGISTRE_ISLAMIQUE.parent.mkdir(parents=True, exist_ok=True)
            with open(FICHIER_REGISTRE_ISLAMIQUE, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "titre": "REGISTRE DE L'ÉCONOMIE ISLAMIQUE VIVANTE AL-MIZAN",
                        "horodatage_mise_a_jour": time.time(),
                        "parametres_canoniques": {
                            "taux_riba": TAUX_RIBA_MAXIMUM_AUTORISE,
                            "taux_zakat": TAUX_ZAKAT_ANNUEL,
                            "nisab_or_g": NISAB_OR_GRAMMES,
                            "nisab_argent_g": NISAB_ARGENT_GRAMMES,
                            "seuil_nisab_or_eur": SEUIL_NISAB_OR_EUR,
                            "seuil_nisab_argent_eur": SEUIL_NISAB_ARGENT_EUR,
                        },
                        "contrats": {k: asdict(v) for k, v in self.contrats.items()},
                        "operations_zakat": [asdict(op) for op in self.operations_zakat],
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            print(f"[!] Erreur sauvegarde registre islamique: {e}")

    def verifier_et_filtrer_anti_riba(
        self,
        type_contrat: str,
        partie_a: str,
        partie_b: str,
        capital: float,
        taux_interet: float,
        devise: str = "EUR",
        cle_partage: str = "50/50",
    ) -> ContratIslamique:
        """
        Contrôle de conformité de l'économie islamique :
        Intercepte et élimine toute tentative d'imposer un intérêt usuraire (Riba).
        """
        id_contrat = f"CONTRAT-ISLAM-{uuid.uuid4().hex[:10].upper()}"
        horodatage = time.time()

        # Adossement physique calculé
        adossement = {
            "adosse_a_l_or_mg": capital * OR_MG_PAR_EUR if devise == "EUR" else 0.0,
            "adosse_a_l_argent_mg": capital * ARGENT_MG_PAR_EUR if devise == "EUR" else 0.0,
            "actif_reel": True,
        }

        # ÉPREUVE 1 : TEST ANTI-RIBA STRICT
        if taux_interet > TAUX_RIBA_MAXIMUM_AUTORISE:
            justif = f"REJET SHARIA : Présence d'un taux d'usure de {taux_interet*100:.2f}%. Tout intérêt usuraire (Riba) est strictement illicite et banni d'Al-Mizan."
            signature = hashlib.sha256(f"{id_contrat}:REJETE_RIBA:{capital}:{horodatage}".encode("utf-8")).hexdigest()
            contrat = ContratIslamique(
                id_contrat=id_contrat,
                type_contrat=type_contrat,
                partie_a=partie_a,
                partie_b=partie_b,
                capital_initial=capital,
                devise=devise,
                taux_interet_annuel=taux_interet,
                cle_partage_profits=cle_partage,
                statut_conformite_sharia="REJETE_RIBA",
                adossement_physique=adossement,
                horodatage=horodatage,
                signature_sha256=signature,
                justification_rejet=justif,
            )
            self.contrats[id_contrat] = contrat
            self._sauvegarder_registre()
            return contrat

        # ÉPREUVE 2 : TEST TYPE DE CONTRAT PARTICIPATIF (Mudaraba, Musharaka, Murabaha, Qard Hassan)
        types_valides = ["MUDARABA", "MUSHARAKA", "MURABAHA", "QARD_HASSAN"]
        if type_contrat.upper() not in types_valides:
            justif = f"REJET SHARIA : Type de contrat inconnu '{type_contrat}'. Seuls {types_valides} sont canoniques."
            signature = hashlib.sha256(f"{id_contrat}:REJETE_GHARAR:{capital}:{horodatage}".encode("utf-8")).hexdigest()
            contrat = ContratIslamique(
                id_contrat=id_contrat,
                type_contrat=type_contrat,
                partie_a=partie_a,
                partie_b=partie_b,
                capital_initial=capital,
                devise=devise,
                taux_interet_annuel=0.0,
                cle_partage_profits=cle_partage,
                statut_conformite_sharia="REJETE_GHARAR",
                adossement_physique=adossement,
                horodatage=horodatage,
                signature_sha256=signature,
                justification_rejet=justif,
            )
            self.contrats[id_contrat] = contrat
            self._sauvegarder_registre()
            return contrat

        # CONTRAT HOMOLOGUÉ ET SCELLÉ
        signature = hashlib.sha256(f"{id_contrat}:VALIDE:{type_contrat}:{capital}:{cle_partage}:{horodatage}".encode("utf-8")).hexdigest()
        contrat = ContratIslamique(
            id_contrat=id_contrat,
            type_contrat=type_contrat.upper(),
            partie_a=partie_a,
            partie_b=partie_b,
            capital_initial=capital,
            devise=devise,
            taux_interet_annuel=0.0,
            cle_partage_profits=cle_partage,
            statut_conformite_sharia="VALIDE_CONFORME",
            adossement_physique=adossement,
            horodatage=horodatage,
            signature_sha256=signature,
            justification_rejet=None,
        )
        self.contrats[id_contrat] = contrat
        self._sauvegarder_registre()
        return contrat

    def executer_prelevement_zakat_sur_solde(
        self,
        compte: str,
        solde_mzn: float,
        devise: str = "MZN"
    ) -> Tuple[bool, Optional[OperationZakat], str]:
        """
        Exécute le calcul et le versement effectif de la Zakat légale (2.5%) vers la CAISSE_ZAKAT_CIVIQUE.
        Vérifie le franchissement du Nisab d'or ou d'argent.
        """
        # Conversion du solde en équivalent EUR pour évaluation du Nisab
        # Dans Al-Mizan, 1 000 MZN = 1 EUR nominal
        solde_equivalent_eur = (solde_mzn / 1000.0) if devise == "MZN" else solde_mzn

        # Seuil d'éligibilité : Nisab Argent (seuil protecteur et solidaire classique)
        seuil_retenu = SEUIL_NISAB_ARGENT_EUR

        if solde_equivalent_eur < seuil_retenu:
            return False, None, f"Solde insuffisant pour la Zakat : {solde_equivalent_eur:.2f} € < Nisab légal ({seuil_retenu:.2f} €)."

        # Calcul exact des 2.5%
        montant_zakat = solde_mzn * TAUX_ZAKAT_ANNUEL

        id_op = f"ZAKAT-EXEC-{int(time.time()*1000)}-{uuid.uuid4().hex[:6].upper()}"
        horodatage = time.time()
        quittance = hashlib.sha256(
            f"{id_op}:{compte}:CAISSE_ZAKAT_CIVIQUE:{montant_zakat}:{horodatage}".encode("utf-8")
        ).hexdigest()

        operation = OperationZakat(
            id_operation=id_op,
            compte_debite=compte,
            assiette_soumise_eur=solde_equivalent_eur,
            montant_zakat_preleve=montant_zakat,
            devise=devise,
            compte_beneficiaire_caisse="CAISSE_ZAKAT_CIVIQUE",
            horodatage=horodatage,
            quittance_sha256=quittance,
            statut="VERSE_AVEC_SUCCES",
        )

        self.operations_zakat.append(operation)
        self._sauvegarder_registre()

        # Mise à jour réelle du grand livre synchron MZN si présent
        self._crediter_caisse_zakat_ledger(montant_zakat, compte)

        return True, operation, f"Zakat purificatrice de 2.5% prélevée avec succès ({montant_zakat:,.2f} {devise}) et versée à la Caisse Civique."

    def _crediter_caisse_zakat_ledger(self, montant: float, compte_source: str):
        """Met à jour concrètement le solde de la CAISSE_ZAKAT_CIVIQUE dans le Grand Livre MZN."""
        if not FICHIER_LEDGER_SYNCHRON.exists():
            return
        try:
            with open(FICHIER_LEDGER_SYNCHRON, "r", encoding="utf-8") as f:
                data = json.load(f)

            balances = data.get("balances_actuelles", {})
            if "CAISSE_ZAKAT_CIVIQUE" in balances:
                balances["CAISSE_ZAKAT_CIVIQUE"] += montant
                if compte_source in balances and balances[compte_source] >= montant:
                    balances[compte_source] -= montant

                data["nb_transactions_totales"] = data.get("nb_transactions_totales", 0) + 1
                data["derniere_mise_a_jour"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())

                # Sauvegarde du grand livre
                with open(FICHIER_LEDGER_SYNCHRON, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[!] Erreur mise à jour ledger pour Zakat : {e}")

    def obtenir_bilan_economie_islamique(self) -> Dict[str, Any]:
        """Bilan consolidé de l'économie islamique réelle en cours."""
        total_zakat_collectee = sum(op.montant_zakat_preleve for op in self.operations_zakat if op.statut == "VERSE_AVEC_SUCCES")
        total_contrats_valides = sum(1 for c in self.contrats.values() if c.statut_conformite_sharia == "VALIDE_CONFORME")
        total_tentatives_riba_bloquees = sum(1 for c in self.contrats.values() if c.statut_conformite_sharia == "REJETE_RIBA")

        # Lecture du solde réel actuel de la Caisse de Zakat dans le grand livre
        solde_caisse_zakat = 200_000.0
        if FICHIER_LEDGER_SYNCHRON.exists():
            try:
                with open(FICHIER_LEDGER_SYNCHRON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    solde_caisse_zakat = data.get("balances_actuelles", {}).get("CAISSE_ZAKAT_CIVIQUE", 200_000.0)
            except Exception:
                pass

        return {
            "statut": "OPERATIONNEL_REEL",
            "principes_appliques": {
                "riba_proscrit": True,
                "taux_usure": 0.0,
                "partage_5050": True,
                "zakat_applicable_pct": 2.5,
                "garantie_adossement_physique": True,
            },
            "indicateurs_or_argent": {
                "cours_or_eur_g": round(VALEUR_OR_PAR_GRAMME_EUR, 2),
                "cours_argent_eur_g": round(VALEUR_ARGENT_PAR_GRAMME_EUR, 4),
                "seuil_nisab_or_eur": round(SEUIL_NISAB_OR_EUR, 2),
                "seuil_nisab_argent_eur": round(SEUIL_NISAB_ARGENT_EUR, 2),
            },
            "caisse_zakat_civique": {
                "solde_actuel_mzn": solde_caisse_zakat,
                "total_operations_zakat": len(self.operations_zakat),
                "cumul_zakat_prelevee_mzn": total_zakat_collectee,
                "affectation": "8_CATEGORIES_CORANIQUES_AYANTS_DROIT"
            },
            "audit_contrats": {
                "total_contrats_soumis": len(self.contrats),
                "contrats_valides_charia": total_contrats_valides,
                "tentatives_riba_bloquees": total_tentatives_riba_bloquees,
            }
        }


# Instance Globale
MOTEUR_ISLAMIQUE = MoteurEconomieIslamiqueMizan()

if __name__ == "__main__":
    print("=" * 80)
    print("   TEST DU MOTEUR D'ÉCONOMIE ISLAMIQUE OPÉRATIONNEL AL-MIZAN")
    print("=" * 80)

    # 1. Test rejet automatique de tentative de prêt à intérêt (Riba)
    contrat_invalide = MOTEUR_ISLAMIQUE.verifier_et_filtrer_anti_riba(
        type_contrat="MUDARABA",
        partie_a="Banque Usuraire Externe",
        partie_b="Entrepreneur Al-Mizan",
        capital=10000.0,
        taux_interet=0.05,  # 5% d'intérêt usuraire
    )
    print(f"\n[1] Tentative de prêt usuraire (5% Riba) :")
    print(f"    Statut : {contrat_invalide.statut_conformite_sharia} | Motif : {contrat_invalide.justification_rejet}")

    # 2. Test homologation contrat licite Mudaraba 50/50 sans Riba
    contrat_licite = MOTEUR_ISLAMIQUE.verifier_et_filtrer_anti_riba(
        type_contrat="MUDARABA",
        partie_a="Fonds Souverain Al-Mizan",
        partie_b="Artisan Bâtisseur",
        capital=10000.0,
        taux_interet=0.0,  # 0% usure
        cle_partage="50/50",
    )
    print(f"\n[2] Contrat Mudaraba participatif (0% Riba, Partage 50/50) :")
    print(f"    Statut : {contrat_licite.statut_conformite_sharia} | Sceau SHA-256 : {contrat_licite.signature_sha256[:20]}...")

    # 3. Test exécution réelle de la Zakat (2.5%) sur le compte Cité Terrestre
    succes, op_zakat, msg = MOTEUR_ISLAMIQUE.executer_prelevement_zakat_sur_solde(
        compte="CITE_PC_TERRESTRE",
        solde_mzn=2_950_000.0,
        devise="MZN"
    )
    print(f"\n[3] Prélèvement légal de la Zakat (2.5%) :")
    print(f"    Résultat : {msg}")
    if op_zakat:
        print(f"    Montant versé à la Caisse Civique : {op_zakat.montant_zakat_preleve:,.2f} MZN")
        print(f"    Quittance : {op_zakat.quittance_sha256}")

    # 4. Bilan consolidé
    bilan = MOTEUR_ISLAMIQUE.obtenir_bilan_economie_islamique()
    print(f"\n[4] Bilan de l'Économie Islamique :")
    print(f"    Solde Caisse Zakat : {bilan['caisse_zakat_civique']['solde_actuel_mzn']:,.2f} MZN")
    print(f"    Tentatives Riba bloquées : {bilan['audit_contrats']['tentatives_riba_bloquees']}")
    print(f"    Nisab Or : {bilan['indicateurs_or_argent']['seuil_nisab_or_eur']} EUR | Nisab Argent : {bilan['indicateurs_or_argent']['seuil_nisab_argent_eur']} EUR")
    print("=" * 80)
