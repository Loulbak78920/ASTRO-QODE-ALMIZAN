# -*- coding: utf-8 -*-
"""
Couche 4A : Bibliothèque Anatomique & Biomécanique (`.ASTRO-Q°ODE`)
===================================================================
Implémente fidèlement :
1. `matrice_scapulaire_astro_q°ode.pdf` : L'Omoplate (Scapula) comme routeur spatial flottant à 3 axes :
   - Axe Alpha (Élévation / Dépression) : Ajustement de l'adresse de mémoire vive (`alpha_x`).
   - Axe Bêta  (Protraction / Rétraction) : Contrôle d'isolement sémantique et pare-feu sandbox `(( ))`.
   - Axe Gamma (Rotation Sonnette) : Routage instantané des flux via le bus Photon (Lumière).
   - Origine 0 (`0 : HÉLIUM`) : Point de repos stable et libération de mémoire (`return 0`).
2. `axe_execution_astro_q°ode.pdf` : Le pipeline d'exécution du membre supérieur :
   - Omoplate (Scapula) -> Bras / Avant-bras (horloge `dt`) -> 5 Doigts de la main :
     * Doigt 0 (Pouce)       : Ancre Neutre Stable (`0 : HÉLIUM` / `return 0`) — Zéro Absolu / Inerte.
     * Doigt 1 (Index)       : Pointeur de Signal (`alpha_x`, `[-9;+9]`) — `MECQUOIS` (Essence).
     * Doigt 2 (Majeur)      : Forçage d'Énergie (`??`, intensité max) — `MECQUOIS` (Énergie).
     * Doigt 3 (Annulaire)   : Liaison Contextuelle (`∪`, `⊃`, `⊂`) — `MEDINOIS` (Loi / Action).
     * Doigt 4 (Auriculaire) : Verrou Symétrique (`omega_X` / `;`) — `MEDINOIS` (Méta-Logique).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .lib_informe import MatriceLogiqueComplexe
from .lib_temporelle import CLOCK_DT_KERNEL


# ==============================================================================
# 1. LA MATRICE SCAPULAIRE (OMOPLATE — ROUTEUR SPATIAL À 3 AXES)
# ==============================================================================

@dataclass
class AxeScapulaire:
    """Représente un axe biomécanique de l'Omoplate (Scapula)."""
    code: str
    mouvement_anatomique: str
    role_compilateur: str
    valeur_courante: float = 0.0
    etat_actif: str = "REPOS_HELIUM"


class MatriceScapulaire:
    """
    Interface flottante et routeur spatial à 3 axes du compilateur ASTRO-CODE.
    Oriente les variables locales, active le pare-feu `(( ))` et route les signaux
    sur le bus Photon.
    """

    def __init__(self) -> None:
        self.axe_alpha = AxeScapulaire(
            code="ALPHA",
            mouvement_anatomique="Élévation / Dépression",
            role_compilateur="Ajustement de l'adresse de mémoire vive (alpha_a .. alpha_s sur [-9;+9])",
        )
        self.axe_beta = AxeScapulaire(
            code="BETA",
            mouvement_anatomique="Protraction / Rétraction",
            role_compilateur="Contrôle d'isolement sémantique et bac à sable (( ))",
        )
        self.axe_gamma = AxeScapulaire(
            code="GAMMA",
            mouvement_anatomique="Rotation Sonnette",
            role_compilateur="Routage instantané des flux via le bus Photon (Lumière)",
        )
        self.profondeur_sandbox: int = 0
        self.flux_photon_actifs: int = 0
        self.journal_routage: List[Dict[str, object]] = []

    def orienter_adresse_alpha(self, identifiant_variable: str, echelon_thermique: float = 0.0) -> int:
        """
        Ajuste l'Axe Alpha (Élévation/Dépression) sur l'adresse associée à `alpha_x`.
        Retourne la coordonnée [-9 ; +9] résolue.
        """
        coord = MatriceLogiqueComplexe.chiffre_depuis_identifiant(identifiant_variable)
        if coord is None:
            coord = max(-9, min(9, int(round(echelon_thermique))))
        self.axe_alpha.valeur_courante = float(coord)
        self.axe_alpha.etat_actif = (
            "ELEVATION" if coord > 0 else ("DEPRESSION" if coord < 0 else "NEUTRE_J")
        )
        self.journal_routage.append({
            "axe": "ALPHA",
            "variable": identifiant_variable,
            "coordonnee": coord,
            "mouvement": self.axe_alpha.etat_actif,
        })
        return coord

    def activer_sandbox_beta(self, niveau_imbrication: int = 1) -> None:
        """Active le pare-feu d'isolation sémantique `( ... )` ou `(( ... ))` sur l'Axe Bêta."""
        self.profondeur_sandbox += niveau_imbrication
        self.axe_beta.valeur_courante = float(self.profondeur_sandbox)
        self.axe_beta.etat_actif = (
            "ISOLATION_MONADIQUE_TOTALE" if self.profondeur_sandbox >= 2
            else ("SANDBOX_ACTIVE" if self.profondeur_sandbox == 1 else "OUVERT")
        )
        self.journal_routage.append({
            "axe": "BETA",
            "profondeur_sandbox": self.profondeur_sandbox,
            "etat": self.axe_beta.etat_actif,
        })

    def relacher_sandbox_beta(self, niveau_imbrication: int = 1) -> None:
        """Relâche un niveau de conteneur sandbox sur l'Axe Bêta."""
        self.profondeur_sandbox = max(0, self.profondeur_sandbox - niveau_imbrication)
        self.axe_beta.valeur_courante = float(self.profondeur_sandbox)
        self.axe_beta.etat_actif = (
            "ISOLATION_MONADIQUE_TOTALE" if self.profondeur_sandbox >= 2
            else ("SANDBOX_ACTIVE" if self.profondeur_sandbox == 1 else "OUVERT")
        )

    def router_bus_photon_gamma(self, source: str, destination: str, energie_joules: float = 1.0) -> Dict[str, object]:
        """Effectue une rotation sonnette sur l'Axe Gamma pour router un flux sur le bus Photon."""
        self.flux_photon_actifs += 1
        self.axe_gamma.valeur_courante = float(energie_joules)
        self.axe_gamma.etat_actif = f"BUS_PHOTON_{source}_VERS_{destination}"
        entree = {
            "axe": "GAMMA",
            "flux_id": self.flux_photon_actifs,
            "source": source,
            "destination": destination,
            "energie_I_joules": energie_joules,
        }
        self.journal_routage.append(entree)
        return entree

    def retour_origine_helium(self) -> None:
        """Ramène l'Omoplate à l'Origine 0 (`0 : HÉLIUM` — repos absolu et libération mémoire)."""
        self.axe_alpha.valeur_courante = 0.0
        self.axe_alpha.etat_actif = "0 : HÉLIUM"
        self.axe_beta.valeur_courante = 0.0
        self.axe_beta.etat_actif = "0 : HÉLIUM"
        self.axe_gamma.valeur_courante = 0.0
        self.axe_gamma.etat_actif = "0 : HÉLIUM"
        self.profondeur_sandbox = 0

    def etat_resume(self) -> Dict[str, object]:
        return {
            "origine": "0 : HÉLIUM",
            "axe_alpha": {
                "mouvement": self.axe_alpha.mouvement_anatomique,
                "valeur": self.axe_alpha.valeur_courante,
                "etat": self.axe_alpha.etat_actif,
            },
            "axe_beta": {
                "mouvement": self.axe_beta.mouvement_anatomique,
                "profondeur_sandbox": self.profondeur_sandbox,
                "etat": self.axe_beta.etat_actif,
            },
            "axe_gamma": {
                "mouvement": self.axe_gamma.mouvement_anatomique,
                "flux_photon_total": self.flux_photon_actifs,
                "etat": self.axe_gamma.etat_actif,
            },
        }


# ==============================================================================
# 2. LE PIPELINE D'EXÉCUTION DES 5 DOIGTS (`axe_execution_astro_q°ode.pdf`)
# ==============================================================================

@dataclass
class SegmentDoigt:
    """Modélise l'un des 5 doigts de la main d'exécution ASTRO-CODE."""
    index_doigt: int
    nom_anatomique: str
    role_systeme: str
    symbole_associe: str
    fonction_principale: str
    paradigme_associe: str
    registre_courant: object = None
    activations: int = 0

    def activer(self, valeur: object) -> None:
        self.registre_courant = valeur
        self.activations += 1


class PipelineCinqDoigts:
    """
    Unifie l'Omoplate (Scapula), le Bras (Pipeline cadencé par `dt`) et les 5 Doigts de la main.
    """

    def __init__(self, matrice_scapulaire: Optional[MatriceScapulaire] = None) -> None:
        self.omoplate = matrice_scapulaire or MatriceScapulaire()
        self.cadence_bras_dt: float = CLOCK_DT_KERNEL
        self.doigts: Dict[int, SegmentDoigt] = {
            0: SegmentDoigt(
                index_doigt=0,
                nom_anatomique="Pouce (Doigt 0)",
                role_systeme="Ancre Neutre Stable",
                symbole_associe="0 : HÉLIUM / return 0",
                fonction_principale="Purge mémoire et clôture absolue",
                paradigme_associe="Zéro Absolu / Inerte",
                registre_courant="0 : HÉLIUM",
            ),
            1: SegmentDoigt(
                index_doigt=1,
                nom_anatomique="Index (Doigt 1)",
                role_systeme="Pointeur de Signal",
                symbole_associe="alpha_x (Minuscules)",
                fonction_principale="Sélection et pointage discrets [-9;+9]",
                paradigme_associe="MECQUOIS (Essence)",
            ),
            2: SegmentDoigt(
                index_doigt=2,
                nom_anatomique="Majeur (Doigt 2)",
                role_systeme="Forçage d'Énergie",
                symbole_associe="?? (Intensité max)",
                fonction_principale="Injection de puissance et priorité absolue",
                paradigme_associe="MECQUOIS (Énergie)",
            ),
            3: SegmentDoigt(
                index_doigt=3,
                nom_anatomique="Annulaire (Doigt 3)",
                role_systeme="Liaison Contextuelle",
                symbole_associe="Union (∪) / Incl (⊃)",
                fonction_principale="Calculs topologiques et gouvernance",
                paradigme_associe="MEDINOIS (Loi/Action)",
            ),
            4: SegmentDoigt(
                index_doigt=4,
                nom_anatomique="Auriculaire (Doigt 4)",
                role_systeme="Verrou Symétrique",
                symbole_associe="omega_X / ;",
                fonction_principale="Ancrage des constantes et fin de ligne",
                paradigme_associe="MEDINOIS (Meta-Logique)",
            ),
        }

    def pointer_signal_index(self, nom_variable: str, valeur: object) -> None:
        """Doigt 1 (Index) : Sélectionne une variable locale `alpha_x` et oriente l'Axe Alpha."""
        self.omoplate.orienter_adresse_alpha(nom_variable)
        self.doigts[1].activer(f"{nom_variable}={valeur}")

    def forcer_energie_majeur(self, expression_description: str) -> None:
        """Doigt 2 (Majeur) : Active le modificateur de force `??` (priorité absolue)."""
        self.omoplate.router_bus_photon_gamma("MAJEUR_FORCE", expression_description, energie_joules=9.0)
        self.doigts[2].activer(f"??({expression_description})")

    def lier_contexte_annulaire(self, operateur: str, gauche: object, droite: object) -> None:
        """Doigt 3 (Annulaire) : Exécute une opération relationnelle ou ensembliste (`∪`, `⊃`, `⊂`)."""
        self.doigts[3].activer(f"{gauche} {operateur} {droite}")

    def verrouiller_constante_auriculaire(self, nom_constante: str, valeur: object) -> None:
        """Doigt 4 (Auriculaire) : Scelle une constante globale `omega_X`."""
        self.doigts[4].activer(f"{nom_constante}={valeur}")

    def ancrer_pouce_helium(self) -> str:
        """Doigt 0 (Pouce) : Purge la mémoire vive et ramène le système à `0 : HÉLIUM`."""
        self.omoplate.retour_origine_helium()
        self.doigts[0].activer("0 : HÉLIUM")
        return "0 : HÉLIUM"

    def tableau_pipeline_complet(self) -> List[Dict[str, object]]:
        """Retourne l'état complet des 7 segments anatomiques (Omoplate, Bras, 5 Doigts)."""
        lignes: List[Dict[str, object]] = [
            {
                "segment": "Omoplate (Scapula)",
                "role_systeme": "Routeur / Pivot Flottant",
                "symbole": "Axes alpha, beta, gamma",
                "fonction": "Alignement d'adresses et pare-feu (( ))",
                "paradigme": "Flottant / Amortisseur",
                "etat": self.omoplate.etat_resume(),
            },
            {
                "segment": "Bras / Avant-bras",
                "role_systeme": "Pipeline de Données",
                "symbole": f"Horloge maîtresse dt = {self.cadence_bras_dt}",
                "fonction": "Transmission d'instructions synchrone",
                "paradigme": "Linéaire temporel",
                "etat": "SYNCHRONE",
            },
        ]
        for idx in range(5):
            d = self.doigts[idx]
            lignes.append({
                "segment": d.nom_anatomique,
                "role_systeme": d.role_systeme,
                "symbole": d.symbole_associe,
                "fonction": d.fonction_principale,
                "paradigme": d.paradigme_associe,
                "registre_courant": d.registre_courant,
                "activations": d.activations,
            })
        return lignes
