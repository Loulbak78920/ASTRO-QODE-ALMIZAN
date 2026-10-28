#!/usr/bin/env python3
"""Estime hors ligne le cout en requetes d'un run de script interrogeant l'API GitHub.

Formule : 1 requete de metadonnees de depot + pages de commits (ceil(commits/per_page))
+ pages de commits par chemin, pour chaque chemin demande.

Sortie ASCII KEY=VALUE, un couple par ligne, pour rester lisible sous cp1252.
Codes de retour : 0 = le run tient dans BUDGET - RESERVE (ou aucune contrainte),
3 = il ne tient pas, 2 = argument invalide.
"""
import argparse
import math
import sys


def pages(entrees, par_page):
    return max(1, math.ceil(entrees / par_page))


def main():
    p = argparse.ArgumentParser(
        description="Cout en requetes d'un run CLI GitHub avant de consommer le quota.",
        epilog="Exemple : --commits 213 --fichiers 1 --budget 9 --reserve 1",
    )
    p.add_argument("--commits", type=int, required=True, help="nombre total de commits du depot")
    p.add_argument("--fichiers", type=int, default=1, help="chemins interroges (commits?path=)")
    p.add_argument("--commits-par-chemin", type=int, default=1, help="commits touchant chaque chemin")
    p.add_argument("--per-page", type=int, default=100, help="taille de page demandee par le script")
    p.add_argument("--budget", type=int, help="quota restant releve (requetes)")
    p.add_argument("--reserve", type=int, default=0, help="requetes a ne pas depenser (test negatif)")
    a = p.parse_args()

    if min(a.commits, a.fichiers, a.commits_par_chemin, a.per_page) < 1:
        print("ERREUR=BORNES_POSITIVES_ATTENDUES")
        return 2
    if (a.budget is not None and a.budget < 0) or a.reserve < 0:
        print("ERREUR=BUDGET_OU_RESERVE_NEGATIF")
        return 2

    req_commits = pages(a.commits, a.per_page)
    req_chemins = sum(pages(a.commits_par_chemin, a.per_page) for _ in range(a.fichiers))
    cout = 1 + req_commits + req_chemins

    print("PER_PAGE={}".format(a.per_page))
    print("PAGES_COMMITS={}".format(req_commits))
    print("REQUETES_CHEMINS={}".format(req_chemins))
    print("COUT_REQUETES={}".format(cout))

    if a.budget is None:
        return 0

    disponible = a.budget - a.reserve
    reliquat = disponible - cout
    print("BUDGET_RESTANT={}".format(a.budget))
    print("RESERVE={}".format(a.reserve))
    print("DISPONIBLE={}".format(disponible))
    print("RELIQUAT={}".format(reliquat))
    print("TIENT={}".format("OUI" if reliquat >= 0 else "NON"))
    return 0 if reliquat >= 0 else 3


if __name__ == "__main__":
    sys.exit(main())
