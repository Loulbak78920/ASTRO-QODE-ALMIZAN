# -*- coding: utf-8 -*-
"""
Machine Virtuelle Biomécanique d'ASTRO-Q°ODE (V1.0 & V2.0)
==========================================================
Coordonne l'exécution matérielle et ontologique du code :
- Registre Immuable `MECQUOIS` (scellé par le Doigt 4 Auriculaire : `omega_*`)
- Mémoire Vive `MEDINOIS` (pointée par le Doigt 1 Index : `alpha_*` et l'Axe Alpha scapulaire)
- Horloge Centrale du Kernel (`dx`, `dy`, `dz`, `dt`) cadencée dans le Bras / Avant-bras
- Routeur Spatial de l'Omoplate (Axes Alpha, Bêta Sandbox `(( ))`, Gamma Bus Photon)
- Ancrage Neutre Stable du Doigt 0 Pouce (`0 : HÉLIUM` / `return 0`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from bibliotheques.lib_anatomie import MatriceScapulaire, PipelineCinqDoigts
from bibliotheques.lib_almizan_extension import (
    COMBLE_CIBLE,
    CONSTANTE_MECQUOISE_C,
    CONSTANTE_MEDINOISE_M,
    EPSILON,
    GARDE_FOUS_ALMIZAN,
    JAUGE_AIR,
    LIGNE_REF,
    MIZAN,
    PLAFOND_EFFECTIF,
    PRODUIT_MEDINOIS,
    RMS,
    TRIPLE_CYCLE,
)
from bibliotheques.lib_monade import OMEGA_MONAD_SOUL, MonadeSupreme
from bibliotheques.lib_physique import LES_14_FORMES, FormeMatiereCode, obtenir_forme_matiere
from bibliotheques.lib_temporelle import (
    CLOCK_DT_KERNEL,
    CLOCK_DX_SOLEIL,
    CLOCK_DY_LUNE,
    CLOCK_DZ_TERRE,
    HorlogeKernelTemporelle,
)
from .runtime_values import EnsembleContexte, EtatHeliumInerte, SignalKelvin


class ViolationImmuabiliteMecquoise(Exception):
    """Levée lorsqu'un bloc tente de réécrire une constante globale `omega_*` déjà scellée."""


class DissolutionSeuilInfinie(Exception):
    """Levée lorsqu'une forme dépasse l'Index 13 (Seuil d'Infinie)."""


@dataclass
class TraceInstructionVM:
    """Enregistre l'exécution d'une instruction sur l'axe biomécanique."""
    numero: int
    paradigme: str
    doigt_sollicite: str
    operation: str
    cible: str
    valeur_resultante: str
    dt_cumule: float


class MachineVirtuelleBiomecanique:
    """
    Machine Virtuelle holistique exécutant les instructions ASTRO-Q°ODE.
    """

    def __init__(self) -> None:
        self.horloge = HorlogeKernelTemporelle()
        self.omoplate = MatriceScapulaire()
        self.pipeline_doigts = PipelineCinqDoigts(self.omoplate)

        # Registre ontologique immuable (MECQUOIS : omega_*)
        self.registre_mecquois: Dict[str, object] = {}

        # Mémoire vive législative (MEDINOIS : alpha_*)
        self.memoire_medinoise: Dict[str, object] = {}

        # Constantes temporelles et universelles pré-chargées
        self.environnement_systeme: Dict[str, object] = {
            "dx": CLOCK_DX_SOLEIL,
            "dy": CLOCK_DY_LUNE,
            "dz": CLOCK_DZ_TERRE,
            "dt": CLOCK_DT_KERNEL,
            "CLOCK_DX_SOLEIL": CLOCK_DX_SOLEIL,
            "CLOCK_DY_LUNE": CLOCK_DY_LUNE,
            "CLOCK_DZ_TERRE": CLOCK_DZ_TERRE,
            "CLOCK_DT_KERNEL": CLOCK_DT_KERNEL,
            "omega_MONAD_SOUL": EnsembleContexte.depuis_sequence(
                [CLOCK_DX_SOLEIL, CLOCK_DY_LUNE, CLOCK_DZ_TERRE]
            ),
            "HELIUM": EtatHeliumInerte(),
            # Constantes et invariants Al-Mizan (Couche 5 V3.0)
            "MIZAN": MIZAN,
            "LIGNE": LIGNE_REF,
            "LIGNE_REF": LIGNE_REF,
            "RMS": RMS,
            "EPSILON": EPSILON,
            "PLAFOND_EFFECTIF": PLAFOND_EFFECTIF,
            "COMBLE_CIBLE": COMBLE_CIBLE,
            "C_MECQUOIS": CONSTANTE_MECQUOISE_C,
            "M_MEDINOIS": CONSTANTE_MEDINOISE_M,
            "JAUGE_AIR": JAUGE_AIR,
            "PRODUIT_MEDINOIS": PRODUIT_MEDINOIS,
            "TRIPLE": TRIPLE_CYCLE,
        }

        self.forme_active: FormeMatiereCode = LES_14_FORMES[0]
        self.sorties_console: List[str] = []
        self.traces_vm: List[TraceInstructionVM] = []
        self.derniere_valeur: object = EtatHeliumInerte()

    def configurer_horloge(self, nom: str, valeur: float) -> None:
        """Applique une directive `SET CLOCK_... = ...`."""
        self.environnement_systeme[nom] = valeur
        if nom == "CLOCK_DX_SOLEIL":
            self.horloge.dx_max = valeur
            self.environnement_systeme["dx"] = valeur
        elif nom == "CLOCK_DY_LUNE":
            self.horloge.dy_max = valeur
            self.environnement_systeme["dy"] = valeur
        elif nom == "CLOCK_DZ_TERRE":
            self.horloge.dz_max = valeur
            self.environnement_systeme["dz"] = valeur
        elif nom == "CLOCK_DT_KERNEL":
            self.horloge.dt_max = valeur
            self.environnement_systeme["dt"] = valeur
            self.pipeline_doigts.cadence_bras_dt = valeur

    def sceller_constante_mecquoise(self, nom: str, valeur: object) -> None:
        """
        Scelle une constante globale `omega_*` dans le namespace `MECQUOIS`
        via le Doigt 4 (Auriculaire — Verrou Symétrique).
        """
        if nom in self.registre_mecquois:
            raise ViolationImmuabiliteMecquoise(
                f"Propriété IMMUABLE violée : la constante '{nom}' est déjà scellée dans MECQUOIS."
            )
        self.registre_mecquois[nom] = valeur
        self.pipeline_doigts.verrouiller_constante_auriculaire(nom, valeur)
        self.horloge.consommer_tick("MECQUOIS", cout=1.0, operation=f"SCELLER {nom}")
        self._enregistrer_trace(
            paradigme="MECQUOIS",
            doigt="Doigt 4 (Auriculaire)",
            operation="SCELLEMENT_OMEGA",
            cible=nom,
            valeur=valeur,
        )

    def affecter_variable_medinoise(self, nom: str, valeur: object, forcee: bool = False) -> None:
        """
        Affecte une variable locale `alpha_*` dans le namespace `MEDINOIS`
        via le Doigt 1 (Index — Pointeur de Signal) et ajuste l'Axe Alpha de l'Omoplate.
        """
        if nom.startswith("omega_") or nom in self.registre_mecquois:
            raise ViolationImmuabiliteMecquoise(
                f"Impossible de réécrire la constante globale immuable '{nom}' dans MEDINOIS."
            )

        self.memoire_medinoise[nom] = valeur
        self.pipeline_doigts.pointer_signal_index(nom, valeur)
        if forcee:
            self.pipeline_doigts.forcer_energie_majeur(f"{nom} = {valeur}")

        # Mise à jour de la Forme de Matière active selon la valeur
        if isinstance(valeur, EtatHeliumInerte) or (isinstance(valeur, SignalKelvin) and valeur.est_nul_helium):
            self.forme_active = LES_14_FORMES[0]
        elif isinstance(valeur, SignalKelvin):
            self.forme_active = valeur.forme_matiere()
        elif isinstance(valeur, MonadeSupreme):
            self.forme_active = valeur.forme_matiere_associee()
        elif isinstance(valeur, FormeMatiereCode):
            self.forme_active = valeur

        self.horloge.consommer_tick("MEDINOIS", cout=1.5 if forcee else 1.0, operation=f"AFFECTER {nom}")
        self.derniere_valeur = valeur
        self._enregistrer_trace(
            paradigme="MEDINOIS",
            doigt="Doigt 2 (Majeur)" if forcee else "Doigt 1 (Index)",
            operation="AFFECTATION_ALPHA",
            cible=nom,
            valeur=valeur,
        )

    def lire_symbole(self, nom: str, portee_locale: Optional[Dict[str, object]] = None) -> object:
        """Résout un identifiant dans la portée lambda, la mémoire Médinoise, le registre Mecquois ou le système."""
        if portee_locale and nom in portee_locale:
            return portee_locale[nom]
        if nom in self.memoire_medinoise:
            return self.memoire_medinoise[nom]
        if nom in self.registre_mecquois:
            return self.registre_mecquois[nom]
        if nom in self.environnement_systeme:
            return self.environnement_systeme[nom]
        raise KeyError(f"Symbole '{nom}' non déclaré dans MECQUOIS ni dans MEDINOIS.")

    def purger_vers_helium(self, raison: str = "return 0") -> EtatHeliumInerte:
        """
        Active le Doigt 0 (Pouce — Ancre Neutre Stable) :
        Ramène l'Omoplate et la Forme active à `0 : HÉLIUM`.
        """
        self.pipeline_doigts.ancrer_pouce_helium()
        self.forme_active = LES_14_FORMES[0]
        etat = EtatHeliumInerte()
        self.derniere_valeur = etat
        self._enregistrer_trace(
            paradigme="REPOS_ABSOLU",
            doigt="Doigt 0 (Pouce)",
            operation=f"ANCRAGE_HELIUM ({raison})",
            cible="SYSTEME",
            valeur=etat,
        )
        return etat

    def _enregistrer_trace(
        self,
        paradigme: str,
        doigt: str,
        operation: str,
        cible: str,
        valeur: object,
    ) -> None:
        self.traces_vm.append(
            TraceInstructionVM(
                numero=len(self.traces_vm) + 1,
                paradigme=paradigme,
                doigt_sollicite=doigt,
                operation=operation,
                cible=cible,
                valeur_resultante=repr(valeur),
                dt_cumule=round(self.horloge.dt_consomme, 4),
            )
        )

    def rapport_etat_complet(self) -> Dict[str, object]:
        """Retourne une photographie complète de la Machine Virtuelle Biomécanique."""
        return {
            "forme_matiere_active": {
                "index": self.forme_active.index,
                "code": self.forme_active.code_court,
                "nom": self.forme_active.nom_complet,
                "paradigme": self.forme_active.paradigme,
            },
            "registre_mecquois_immuable": {k: repr(v) for k, v in self.registre_mecquois.items()},
            "memoire_medinoise_active": {k: repr(v) for k, v in self.memoire_medinoise.items()},
            "horloge_kernel": self.horloge.rapport_repartition(),
            "matrice_scapulaire": self.omoplate.etat_resume(),
            "pipeline_anatomique": self.pipeline_doigts.tableau_pipeline_complet(),
            "sorties_console": list(self.sorties_console),
            "nb_instructions_tracees": len(self.traces_vm),
        }
