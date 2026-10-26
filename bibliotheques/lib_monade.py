# -*- coding: utf-8 -*-
"""
Couche 4B : Bibliothèque de la Monade Suprême (`specification_monade_astro_q°ode.pdf` — V2.0)
=============================================================================================
Implémente fidèlement l'Atome Logique Ultime de l'Astro-Code V2.0 :
- Concept métaphysique (Leibniz) & biologique (Noyau Cellulaire / ADN) :
  Unité substance fondamentale close (« sans fenêtres ») réconciliant l'esprit immuable
  du code (`MECQUOIS`) et l'exécution biologique impérative (`MEDINOIS`).
- Perception interne immuable de l'Univers :
  `omega_MONAD_SOUL = [dx U dy U dz]` (Reflet parfait des 3 cycles temporels).
- Structure fonctionnelle :
  * `MonadeSupreme.unit(valeur)` (`Monad(v)` / `return`) : Encapsulation d'un signal dans la membrane.
  * `monade.bind(fn)` (`>>=`) : Opérateur de transcription polymérase sans effet de bord.
  * `monade.isoler()` (`(( monade ))`) : Verrouillage membranaire absolu.
  * Ramasse-miettes cellulaire (Apoptose / Réparation ADN) : En cas de mutation, erreur ou
    violation de gouvernance (`¿`), retour immédiat à `Monad(0 : HÉLIUM)`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, FrozenSet, Generic, List, TypeVar, Union

from .lib_physique import LES_14_FORMES, FormeMatiereCode
from .lib_temporelle import CLOCK_DT_KERNEL, CLOCK_DX_SOLEIL, CLOCK_DY_LUNE, CLOCK_DZ_TERRE

T = TypeVar("T")
U = TypeVar("U")


# ==============================================================================
# 1. ÂME IMMUABLE DE LA MONADE (`omega_MONAD_SOUL = [dx U dy U dz]`)
# ==============================================================================

@dataclass(frozen=True)
class AmeMonadiqueUniverselle:
    """
    Représente `omega_MONAD_SOUL = [dx U dy U dz]`, le reflet parfait et immuable
    des 3 cycles temporels logé au cœur de chaque Monade cellulaire.
    """
    dx_soleil: float = CLOCK_DX_SOLEIL
    dy_lune: float = CLOCK_DY_LUNE
    dz_terre: float = CLOCK_DZ_TERRE
    dt_kernel: float = CLOCK_DT_KERNEL
    ensemble_cycles: FrozenSet[float] = field(
        default_factory=lambda: frozenset({CLOCK_DX_SOLEIL, CLOCK_DY_LUNE, CLOCK_DZ_TERRE})
    )

    def gouverne(self, signal_valeur: object) -> bool:
        """
        Vérifie la relation d'inclusion large `(signal_thermique ⊃ omega_MONAD_SOUL)` :
        Dans la sémantique Astro-Code V2.0, un signal est en résonance légitime avec l'âme
        monadique s'il n'est pas corrompu et si son échelon thermique appartient au domaine
        harmonique [-9 ; +9] ou aux constantes d'horloge.
        """
        if signal_valeur is None:
            return False
        if isinstance(signal_valeur, str) and "CORROMPU" in signal_valeur.upper():
            return False
        if isinstance(signal_valeur, (int, float)):
            return -9.0 <= float(signal_valeur) <= CLOCK_DT_KERNEL
        return True

    def __repr__(self) -> str:
        return f"[dx({self.dx_soleil}) ∪ dy({self.dy_lune}) ∪ dz({self.dz_terre}) => dt={self.dt_kernel}]"


OMEGA_MONAD_SOUL = AmeMonadiqueUniverselle()


# ==============================================================================
# 2. LA MONADE SUPRÊME (`Monad<T>`)
# ==============================================================================

class MonadeSupreme(Generic[T]):
    """
    Implémentation officielle de `Monad<T>` pour Astro-Code V2.0.
    Possède :
    - Une valeur interne encapsulée (`_valeur`)
    - Le miroir universel `omega_MONAD_SOUL`
    - L'état d'isolation membranaire `(( ... ))`
    - Un journal de transcription ARN polymérase (`>>=`)
    """

    ETAT_HELIUM_INERTE = "0 : HÉLIUM"

    def __init__(
        self,
        valeur: Union[T, str] = ETAT_HELIUM_INERTE,
        isolee: bool = False,
        historique_transcriptions: List[str] | None = None,
    ) -> None:
        self._valeur: Union[T, str] = valeur
        self._ame: AmeMonadiqueUniverselle = OMEGA_MONAD_SOUL
        self._isolee: bool = isolee
        self._historique: List[str] = list(historique_transcriptions or ["INIT:Monad"])

    @classmethod
    def unit(cls, valeur: T) -> "MonadeSupreme[T]":
        """Constructeur monadique `return / unit` : injecte un signal de Niveau 1 dans la membrane."""
        return cls(valeur=valeur, isolee=False, historique_transcriptions=[f"UNIT({valeur})"])

    @classmethod
    def helium_inerte(cls) -> "MonadeSupreme[str]":
        """Retourne la Monade stabilisée à l'Origine Inerte `Monad(0 : HÉLIUM)`."""
        return cls(
            valeur=cls.ETAT_HELIUM_INERTE,
            isolee=True,
            historique_transcriptions=["APOPTOSE_RETOUR(0 : HÉLIUM)"],
        )

    @property
    def valeur_interne(self) -> Union[T, str]:
        """Lecture contemplative de la substance interne (sans effet de bord)."""
        return self._valeur

    @property
    def est_isolee(self) -> bool:
        """Indique si la Monade est scellée par double parenthèse `(( monade ))`."""
        return self._isolee

    @property
    def est_helium_inerte(self) -> bool:
        """Vérifie si la Monade est à l'état fondamental `0 : HÉLIUM`."""
        if isinstance(self._valeur, str) and ("HÉLIUM" in self._valeur.upper() or "HELIUM" in self._valeur.upper()):
            return True
        return False

    @property
    def ame_universelle(self) -> AmeMonadiqueUniverselle:
        return self._ame

    @property
    def historique_transcriptions(self) -> List[str]:
        return list(self._historique)

    def isoler(self) -> "MonadeSupreme[T]":
        """Applique l'isolation absolue `(( alpha_cell_monad ))` (membrane nucléaire étanche)."""
        nouveau_hist = self._historique + ["ISOLATION_ABSOLUE(( ))"]
        return MonadeSupreme(
            valeur=self._valeur,
            isolee=True,
            historique_transcriptions=nouveau_hist,
        )

    def bind(self, fonction_transcription: Callable[[Union[T, str]], object]) -> "MonadeSupreme[object]":
        """
        Opérateur de Transcription Monadique `>>=` (Le BIND Harmonique / ARN Polymérase).
        Exécute `fonction_transcription` sur la substance interne sans briser l'encapsulation.
        En cas d'exception ou de corruption génétique (`¿`), déclenche automatiquement
        le ramasse-miettes cellulaire et retourne `Monad(0 : HÉLIUM)`.
        """
        try:
            resultat = fonction_transcription(self._valeur)
            nouveau_hist = self._historique + [f"BIND(>>=) -> {resultat}"]
            if isinstance(resultat, MonadeSupreme):
                return MonadeSupreme(
                    valeur=resultat.valeur_interne,
                    isolee=self._isolee or resultat.est_isolee,
                    historique_transcriptions=nouveau_hist,
                )
            return MonadeSupreme(
                valeur=resultat,
                isolee=self._isolee,
                historique_transcriptions=nouveau_hist,
            )
        except Exception as exc:
            hist_erreur = self._historique + [f"EXCEPTION_CATCH(¿:{exc}) -> 0 : HÉLIUM"]
            return MonadeSupreme(
                valeur=self.ETAT_HELIUM_INERTE,
                isolee=True,
                historique_transcriptions=hist_erreur,
            )

    def __rshift__(self, fonction_transcription: Callable[[Union[T, str]], object]) -> "MonadeSupreme[object]":
        """Permet d'utiliser `monade >> fonction` en Python natif comme équivalent de `>>=`."""
        return self.bind(fonction_transcription)

    def forme_matiere_associee(self) -> FormeMatiereCode:
        """Détermine laquelle des 14 Formes de la Matière du Code correspond à l'état courant."""
        if self.est_helium_inerte:
            return LES_14_FORMES[0]
        if isinstance(self._valeur, (int, float)):
            idx = abs(int(round(float(self._valeur)))) % 14
            return LES_14_FORMES[idx]
        return LES_14_FORMES[4]  # F4: Plasma Cœur de Fusion (superposition complexe)

    def __eq__(self, autre: object) -> bool:
        if not isinstance(autre, MonadeSupreme):
            return False
        return self._valeur == autre._valeur and self._isolee == autre._isolee

    def __repr__(self) -> str:
        enveloppe_g = "((" if self._isolee else "("
        enveloppe_d = "))" if self._isolee else ")"
        return f"Monad{enveloppe_g}{self._valeur}{enveloppe_d}"
