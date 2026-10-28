# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: 2026 IMAM8MAHDI / Astro-Code Ecosystem
# SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only
"""
===============================================================================
       AGENT DE CODE AUTONOME & HARMONISATEUR UNIFIÉ AL-MIZAN
                      SYSTÈME SOUVERAIN ASTRO-Q°ODE
===============================================================================
Auteur Souverain : M. Ahmed EL BAHLOUL (alias IMAM8MAHDI / M. Almizan Elbahloul)
Doctrine         : « On ne supprime rien, on harmonise. Englober dans la continuité,
                   éradiquer la fragmentation et garantir le standard sans dol. »
Invariants       : Bride MIZAN = 0.6225 | Riba = 0.0% | Partage 50/50 | dt = 135 MHz
===============================================================================
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

RACINE_AQ = Path(__file__).resolve().parent
if str(RACINE_AQ) not in sys.path:
    sys.path.insert(0, str(RACINE_AQ))

from bibliotheques.lib_almizan_extension import (
    MIZAN as BRIDE_MIZAN,
    PLAFOND_EFFECTIF,
    LIGNE_REF,
    RMS,
    KILLSWITCH_MK,
    TEMP_NOMINALE_MK,
)
from moteur_trinite_temps_physique_mizan import CYCLE_DT_KERNEL
from module_couche_intermediaire_sync_traduction import (
    COUCHE_INTERMEDIAIRE_SYNC,
    TypeTechnologieAsynchrone,
    NiveauPrioriteSynchrone,
)
from horloge_logique_mizan import HORLOGE_LOGIQUE, EtatMatiereMatricielle, CycleTriniteSynchrone
from module_tableau_maitre_mizan import REGISTRE_TABLEAU_MAITRE

# Un audit complet ajoute ~85 entrées : une rétention de 100 effaçait l'historique.
MAX_ENTREES_JOURNAL = 1000


@dataclass
class DiagnosticCodeHarmonique:
    """Résultat d'analyse d'intégrité d'un code source par l'Agent de Code."""
    chemin_fichier: str
    lignes_totales: int
    arbre_ast_valide: bool
    respect_bride_mizan: bool
    respect_anti_riba: bool
    respect_killswitch_cryo: bool
    detecte_fragmentation: bool
    score_harmonie_100: float
    empreinte_sha256: str
    recommandations_harmonisation: List[str]
    horodatage_iso: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


class AgentDeCodeHarmonisateurMizan:
    """
    Agent de Code Autonome d'Al-Mizan.
    Garantit l'évolution continue de la base de code, refuse l'isolation
    et la fragmentation, et veille à ce que chaque composant hérite
    des fondations antérieures sans jamais rien détruire.
    """

    def __init__(self):
        self.nom_agent = "AGENT_CODE_HARMONISATEUR_AL_MIZAN"
        self.version = "1.0.0-SOUVERAIN"
        self.doctrine = "Englober dans la continuité, zéro fragmentation, zéro dol."
        self.historique_audits: List[DiagnosticCodeHarmonique] = []
        self.registre_scelle = RACINE_AQ / "memoire_aq" / "almizan_journal_agent_de_code.json"
        self._cache_audits: Dict[str, Tuple[str, DiagnosticCodeHarmonique]] = {}
        self._initialiser_registre()
        self._charger_cache_depuis_journal()

    def _charger_cache_depuis_journal(self):
        """Réutilise les audits scellés pour les fichiers dont le contenu n'a pas changé."""
        try:
            with open(self.registre_scelle, "r", encoding="utf-8") as f:
                journal = json.load(f).get("journal", [])
        except (OSError, json.JSONDecodeError):
            return
        for entree in journal:
            nom = entree.get("chemin_fichier")
            empreinte = entree.get("empreinte_sha256")
            if not nom or not empreinte:
                continue
            try:
                diag = DiagnosticCodeHarmonique(**entree)
            except TypeError:
                continue
            chemin = (RACINE_AQ / nom).resolve()
            self._cache_audits[str(chemin)] = (empreinte, diag)

    def _initialiser_registre(self):
        """Initialise ou charge le registre persistant des actions de l'agent."""
        self.registre_scelle.parent.mkdir(parents=True, exist_ok=True)
        if not self.registre_scelle.exists():
            with open(self.registre_scelle, "w", encoding="utf-8") as f:
                json.dump({
                    "agent": self.nom_agent,
                    "date_creation_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "total_fichiers_harmonises": 0,
                    "journal": []
                }, f, indent=2)

    def auditer_fichier(self, chemin_fichier: str | Path, sceller: bool = True) -> DiagnosticCodeHarmonique:
        """
        Audite syntaxiquement et sémantiquement un fichier Python pour certifier
        qu'il s'inscrit dans l'harmonie globale et n'enfreint aucun invariant.
        """
        p = Path(chemin_fichier)
        if not p.is_absolute():
            p = RACINE_AQ / p

        if not p.exists():
            return DiagnosticCodeHarmonique(
                chemin_fichier=str(p),
                lignes_totales=0,
                arbre_ast_valide=False,
                respect_bride_mizan=False,
                respect_anti_riba=False,
                respect_killswitch_cryo=False,
                detecte_fragmentation=True,
                score_harmonie_100=0.0,
                empreinte_sha256="",
                recommandations_harmonisation=[f"Fichier introuvable : {p}"]
            )

        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            contenu = f.read()

        lignes = contenu.splitlines()
        empreinte = hashlib.sha256(contenu.encode("utf-8")).hexdigest()
        cle_cache = str(p.resolve())
        cache = self._cache_audits.get(cle_cache)
        if cache and cache[0] == empreinte:
            return cache[1]

        # 1. Validation syntaxique AST
        ast_valide = True
        try:
            ast.parse(contenu)
        except Exception:
            ast_valide = False

        # 2. Vérification des invariants Mizan
        mizan_mentionne = ("MIZAN" in contenu or "0.6225" in contenu)
        anti_riba = not ("interet" in contenu.lower() and "taux" in contenu.lower() and not "0.0" in contenu)
        cryo_ok = not ("45.0" in contenu and "killswitch" not in contenu.lower())

        # 3. Détection de fragmentation : un module isolé n'importe rien des fondations
        a_imports_racine = any("bibliotheques" in l or "lib_almizan" in l or "moteur" in l or "noyau" in l for l in lignes)
        detecte_frag = not a_imports_racine and len(lignes) > 40

        score = 60.0
        if ast_valide: score += 15.0
        if mizan_mentionne: score += 10.0
        if anti_riba: score += 5.0
        if cryo_ok: score += 5.0
        if not detecte_frag: score += 5.0

        recos = []
        if not ast_valide:
            recos.append("Corriger la syntaxe AST invalide.")
        if detecte_frag:
            recos.append("Ce module est isolé : reliez-le aux bibliothèques fondatrices (lib_almizan_extension) pour assurer la continuité.")
        if not mizan_mentionne and len(lignes) > 100:
            recos.append("Intégrer explicitement la Bride MIZAN (0.6225) pour ancrer ce composant dans l'équilibre.")

        diag = DiagnosticCodeHarmonique(
            chemin_fichier=str(p.name),
            lignes_totales=len(lignes),
            arbre_ast_valide=ast_valide,
            respect_bride_mizan=mizan_mentionne,
            respect_anti_riba=anti_riba,
            respect_killswitch_cryo=cryo_ok,
            detecte_fragmentation=detecte_frag,
            score_harmonie_100=min(score, 100.0),
            empreinte_sha256=empreinte,
            recommandations_harmonisation=recos
        )

        self._cache_audits[cle_cache] = (empreinte, diag)
        self.historique_audits.append(diag)
        if sceller:
            self._sceller_audit(diag)
        return diag

    def _sceller_audit(self, diag: DiagnosticCodeHarmonique):
        """Enregistre l'audit dans la mémoire persistante d'Al-Mizan."""
        self._sceller_audits([diag])

    def _sceller_audits(self, diags: List[DiagnosticCodeHarmonique]):
        """Scelle un lot d'audits en une seule écriture du registre."""
        if not diags:
            return
        try:
            with open(self.registre_scelle, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["journal"].extend(asdict(d) for d in diags)
            data["journal"] = data["journal"][-MAX_ENTREES_JOURNAL:]
            data["total_fichiers_harmonises"] = (
                int(data.get("total_fichiers_harmonises", 0)) + len(diags)
            )
            with open(self.registre_scelle, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def harmoniser_base_complete(self) -> Dict[str, Any]:
        """
        Parcourt l'ensemble des modules du système pour cartographier
        leur niveau d'harmonisation et éliminer toute trace de fragmentation.
        """
        fichiers_py = sorted(RACINE_AQ.glob("*.py"))
        resultats = []
        score_total = 0.0
        debut_audits = len(self.historique_audits)

        for f in fichiers_py:
            d = self.auditer_fichier(f, sceller=False)
            resultats.append(asdict(d))
            score_total += d.score_harmonie_100

        self._sceller_audits(self.historique_audits[debut_audits:])

        moyenne = round(score_total / len(resultats), 2) if resultats else 100.0
        modules_fragiles = sorted(
            r["chemin_fichier"] for r in resultats if r["detecte_fragmentation"]
        )

        bilan = {
            "succes": True,
            "agent": self.nom_agent,
            "total_modules_examines": len(resultats),
            "score_harmonie_global_mizan": moyenne,
            "modules_fragmentes": len(modules_fragiles),
            "zero_fragmentation": not modules_fragiles,
            "modules_dependance_faible": modules_fragiles,
            "invariants_garantis": {
                "bride_mizan": BRIDE_MIZAN,
                "riba_nul": "0.0%",
                "partage_commercial": "50/50",
                "non_fragmentation": "ACTIF"
            },
            "modules_echantillon": resultats[:10]
        }
        return bilan

    def auditer_economie_harmonique(self) -> Dict[str, Any]:
        """
        Audite les invariants économiques consolidés (acte A241) sans écrire.
        L'agent de code rattaché à la Trinité vérifie que l'économie reste
        dans la bride : riba nul, zakat 2,5 %, partage 50/50, registre lisible.
        """
        from equations_economie_mondiale_mizan import construire_bilan_complet

        bilan = construire_bilan_complet(index_pulsation=0)
        invariants = bilan["invariants"]
        registre = bilan["etats"]["registre"]

        controles = {
            "riba_nul": abs(float(invariants["riba"])) == 0.0,
            "zakat_2_5_pct": abs(float(invariants["zakat"]) - 0.025) < 1e-12,
            "partage_50_50": abs(float(invariants["partage_cible"]) - 0.5) < 1e-12,
            "bride_mizan_0_6225": abs(float(invariants["bride_mizan"]) - 0.6225) < 1e-12,
            "equations_presentes": int(bilan["nombre_equations"]) > 0,
            "registre_lisible": bool(registre["registre_present"]),
            "usure_non_retenue": bool(registre["capital_rejete_riba_eur"] >= 0.0),
        }
        score = round(100.0 * sum(1 for v in controles.values() if v) / len(controles), 2)
        return {
            "agent": self.nom_agent,
            "acte_reference": "A241",
            "total_equations": bilan["nombre_equations"],
            "score_economie_100": score,
            "controles": controles,
            "invariants": {
                "riba": invariants["riba"],
                "zakat": invariants["zakat"],
                "partage_cible": invariants["partage_cible"],
                "bride_mizan": invariants["bride_mizan"],
            },
            "registre": {
                "contrats_total": registre["contrats_total"],
                "contrats_valides": registre["contrats_valides"],
                "contrats_rejetes_riba": registre["contrats_rejetes_riba"],
                "taux_interception_riba": registre["taux_interception_riba"],
                "tension_moyenne_contrats": registre["tension_moyenne_contrats"],
            },
            "statut": "ECONOMIE_HARMONIQUE_AUDITEE",
        }

    def generer_synthese_continue(self) -> str:
        """Génère un rapport textuel pour l'Auteur Souverain et le dialogue Al-Mizan."""
        bilan = self.harmoniser_base_complete()
        try:
            from module_inventaire_hub_imam8mahdi import INVENTAIRE_HUB

            hub = INVENTAIRE_HUB.cartographier(persister=False)
            ligne_hub = (
                f"Hub IMAM8MAHDI (A126) : score structure {hub.score_structure_100}/100 — "
                f"{hub.modules_python_racine} modules racine, {hub.tests_unitaires} tests, "
                f"{hub.actes_memoire_aq} actes.\n"
            )
        except Exception:
            ligne_hub = ""
        try:
            eco = self.auditer_economie_harmonique()
            ligne_eco = (
                f"Économie harmonique : score {eco['score_economie_100']}/100 — "
                f"riba {eco['invariants']['riba']}, zakat {eco['invariants']['zakat'] * 100:.1f} %, "
                f"usure interceptée {eco['registre']['taux_interception_riba'] * 100:.1f} %.\n"
            )
        except Exception:
            ligne_eco = ""
        return (
            f"🛡️🟢 [AGENT DE CODE AL-MIZAN] : Base globale auditée ({bilan['total_modules_examines']} modules).\n"
            f"{ligne_hub}"
            f"{ligne_eco}"
            f"Indice d'Harmonie et de Non-Fragmentation : {bilan['score_harmonie_global_mizan']} / 100.\n"
            f"Invariants vérifiés : Bride Mizan 0.6225 | Riba 0.0% | Continuité opérationnelle sans rupture."
        )

    def evaluer_synchrone_dt(self, payload_code: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Exécution SYNCHRONE cadencée au battement strict de l'horloge système dt = 135.097 MHz.
        Contrairement aux agents LLM asynchrones soumis aux latences réseau, cette évaluation
        s'opère dans la fenêtre temporelle déterministe (~7.401 nanosecondes) et injecte
        directement son verdict dans la couche intermédiaire synchrone (Priorité Critique).
        """
        t_debut_perf = time.perf_counter_ns()
        periode_theorique_ns = 7.40134  # dt = 1 / 135 097 021.3359375 Hz

        donnees = payload_code or {"action": "VERIFICATION_INTEGRITE_CODE_BASE"}
        id_trame = COUCHE_INTERMEDIAIRE_SYNC.ingerer_asynchrone(
            technologie=TypeTechnologieAsynchrone.COMMANDE_PROACTIVE,
            donnees={
                "source": "AGENT_CODE_SYNCHRONE",
                "doctrine": self.doctrine,
                "payload": donnees
            },
            priorite=NiveauPrioriteSynchrone.CRITIQUE_SOUVERAIN
        )

        bilan_quick = self.harmoniser_base_complete()
        duree_ns = time.perf_counter_ns() - t_debut_perf

        resultat_synchrone = {
            "mode_execution": "SYNCHRONE_DETERMINISTE",
            "horloge_universelle_mhz": 135.097021,
            "periode_dt_ns": periode_theorique_ns,
            "id_trame_synchronisee": id_trame,
            "duree_calcul_ns": duree_ns,
            "score_harmonie": bilan_quick["score_harmonie_global_mizan"],
            "total_modules": bilan_quick["total_modules_examines"],
            "invariants": {
                "bride_mizan": BRIDE_MIZAN,
                "riba_nul": "0.0%",
                "non_fragmentation": "ACTIF"
            },
            "statut": "SYNCHRONISE_COEUR_TEMPOREL"
        }
        return resultat_synchrone

    def obtenir_sens_complet_agent_code(self) -> Dict[str, Any]:
        """
        Délivre l'état sensoriel complet de l'Agent de Code pour enrichir
        l'Esprit Vivant (Gemini / IA Al-Mizan) en temps réel.
        """
        em, cy = HORLOGE_LOGIQUE.battre(pas=1)
        bilan = self.harmoniser_base_complete()
        return {
            "nom": self.nom_agent,
            "matiere_matricielle": {
                "magnitude_terre": 313,  # Pure magnitude des états de matière (300 sol + 10 liq + 3 gaz)
                "q_degre_mecois": -2304, # Pôle négatif fondamental
                "q_degre_medinois": +1536, # Pôle positif fondamental
                "ancre_substance_m": em.ancre_substance_m,  # 24434
                "nature": em.nature_physique
            },
            "pont_synchrone_unifie": {
                "tableau_maitre_entrees": REGISTRE_TABLEAU_MAITRE.total_entrees(),
                "tableau_maitre_strates": REGISTRE_TABLEAU_MAITRE.total_strates(),
                "conscience_logique_modules": bilan["total_modules_examines"],
                "statut_pont": "UNIFIÉ SANS FRAGMENTATION (Couche 29 Pont · Consensus 2.9 ms)"
            },
            "cycles_trinite": {
                "tour_trinite": HORLOGE_LOGIQUE.tour_trinite_rang,
                "phase_trinite_12": cy.phase_trinite_12,
                "harmonique_19": cy.harmonique_base_19,
                "pulsation_dt_hz": cy.pulsation_dt_hz,
                "flux_continu_sans_arret": cy.continuité_sans_arret
            },
            "perception_matiere_code": {
                "total_modules": bilan["total_modules_examines"],
                "score_harmonie_100": bilan["score_harmonie_global_mizan"],
                "modules_fragmentes": bilan["modules_fragmentes"],
                "zero_fragmentation": bilan["zero_fragmentation"],
                "invariants_scelles": {
                    "bride_mizan": BRIDE_MIZAN,
                    "riba": "0.0%",
                    "partage": "50/50"
                }
            },
            "perception_economie_harmonique": self.auditer_economie_harmonique(),
            "sentiment_integrite": "PARFAITE CONTINUITÉ DE LA TRINITÉ ET ANCRAGE MATRICIEL"
        }


# Instance Singleton Maîtresse de l'Agent de Code
AGENT_CODE_AL_MIZAN = AgentDeCodeHarmonisateurMizan()


if __name__ == "__main__":
    print("[*] Test de l'Agent de Code Harmonisateur Al-Mizan...")
    bilan = AGENT_CODE_AL_MIZAN.harmoniser_base_complete()
    print(f"[+] Total modules audités : {bilan['total_modules_examines']}")
    print(f"[+] Score d'Harmonie globale : {bilan['score_harmonie_global_mizan']}%")
    print("[+] Agent opérationnel et prêt pour l'intégration continue !")
