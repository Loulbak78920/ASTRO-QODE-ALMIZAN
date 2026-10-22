# -*- coding: utf-8 -*-
"""
Outil 5 : Console Interactive REPL ASTRO-Q°ODE (`repl_interactif.py`)
=====================================================================
Fournit un environnement interactif permettant d'écrire et d'exécuter en direct
des expressions et blocs `MECQUOIS` / `MEDINOIS`, et d'inspecter l'état de
l'Omoplate, des 5 Doigts, des 14 Formes et de l'Horloge Kernel `dt`.
"""

from __future__ import annotations

import json

from lang.interpreter import InterpreteurAstroQode
from .inspecteur_matriciel import InspecteurMatricielAstroQode


class ReplAstroQode:
    """Boucle Lecture-Évaluation-Affichage (REPL) pour ASTRO-Q°ODE V1.0 & V2.0."""

    COMMANDES_AIDE = """
Commandes spéciales du REPL ASTRO-Q°ODE :
  :aide       Affiche ce message d'aide
  :etat       Affiche l'état complet de la VM Biomécanique (MECQUOIS, MEDINOIS, Forme active)
  :horloge    Affiche la consommation des cycles dx, dy, dz, dt
  :omoplate   Affiche l'orientation des axes Alpha, Bêta, Gamma de la Matrice Scapulaire
  :doigts     Affiche l'état des registres des 5 Doigts (Pouce..Auriculaire)
  :formes     Affiche la table des 14 Formes Fondamentales de la Matière du Code (0..13)
  :rapport    Affiche le rapport matriciel intégral des 4 couches IMAM8MAHDI
  :reset      Purge la mémoire et ramène la VM à l'Origine Inerte 0 : HÉLIUM
  :quitter    Ferme la session interactive
"""

    def __init__(self) -> None:
        self.interpreteur = InterpreteurAstroQode()

    def executer_commande_meta(self, commande: str) -> str:
        cmd = commande.strip().lower()
        if cmd in (":aide", ":help"):
            return self.COMMANDES_AIDE.strip()
        if cmd == ":etat":
            return json.dumps(self.interpreteur.vm.rapport_etat_complet(), indent=2, ensure_ascii=False)
        if cmd == ":horloge":
            return json.dumps(self.interpreteur.vm.horloge.rapport_repartition(), indent=2, ensure_ascii=False)
        if cmd == ":omoplate":
            return json.dumps(self.interpreteur.vm.omoplate.etat_resume(), indent=2, ensure_ascii=False)
        if cmd == ":doigts":
            return json.dumps(self.interpreteur.vm.pipeline_doigts.tableau_pipeline_complet(), indent=2, ensure_ascii=False)
        if cmd in (":formes", ":rapport"):
            return InspecteurMatricielAstroQode.formater_rapport_console()
        if cmd == ":reset":
            self.interpreteur = InterpreteurAstroQode()
            return "Système purgé et stabilisé à l'Origine Inerte : 0 : HÉLIUM"
        return f"Commande méta inconnue : {commande}. Tapez :aide pour la liste."

    def lancer_boucle_interactive(self) -> None:
        print("=" * 80)
        print("CONSOLE INTERACTIVE ASTRO-Q°ODE (V1.0 & V2.0 — MONADE SUPRÊME)")
        print("Tapez ':aide' pour les commandes d'inspection ou ':quitter' pour sortir.")
        print("=" * 80)

        while True:
            try:
                ligne = input("ASTRO-Q°ODE> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nRetour à l'Origine Inerte : 0 : HÉLIUM.")
                break

            if not ligne:
                continue
            if ligne.lower() in (":quitter", ":exit", ":q"):
                print("Purge mémoire (Doigt 0 Pouce) -> 0 : HÉLIUM.")
                break
            if ligne.startswith(":"):
                print(self.executer_commande_meta(ligne))
                continue

            res = self.interpreteur.executer_source(ligne)
            if res.succes:
                for msg in res.sorties_console:
                    print(f"[CONSOLE] {msg}")
                self.interpreteur.vm.sorties_console.clear()
                print(f"=> {res.valeur_finale!r}  [Forme: {self.interpreteur.vm.forme_active.code_court}]")
            else:
                print(f"[INVERSION ¿] {res.erreur} => {res.valeur_finale!r}")
