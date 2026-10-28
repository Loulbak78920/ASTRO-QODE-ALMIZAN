#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quantifier une revendication de calcul fini sur les zeros de zeta.

Sortie ASCII uniquement (console Windows cp1252). Aucune dependance externe.
Le cout annonce est un ordre de grandeur deduit du nombre d'evaluations, jamais
une mesure de performance.
"""

from __future__ import annotations

import argparse
import json
import math
import sys

RECORDS = (
    {
        "source": "van de Lune, te Riele, Winter (1986)",
        "unite": "zeros",
        "valeur": 1.5e9,
        "note": "premiers zeros non triviaux verifies",
    },
    {
        "source": "Gourdon (2004)",
        "unite": "zeros",
        "valeur": 1e13,
        "note": "premiers zeros non triviaux, calcul non certifie en intervalle",
    },
    {
        "source": "Platt-Trudgian (2021)",
        "unite": "hauteur",
        "valeur": 3e12,
        "note": "arithmetique d'intervalle, zeros avec gamma <= T",
    },
)

T_MIN = 10.0
CIBLES = (10, 1_000, 10_000, 1_000_000, 1_000_000_000)


def zeros_lisses(t: float) -> float:
    x = t / (2.0 * math.pi)
    return x * (math.log(x) - 1.0) + 7.0 / 8.0


def hauteur_pour_zeros(n: float) -> float:
    lo, hi = T_MIN, 2.0 * T_MIN
    while zeros_lisses(hi) < n:
        hi *= 2.0
        if hi > 1e18:
            raise ValueError("cible hors du domaine numerique")
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if zeros_lisses(mid) < n:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _zeros_equivalents(record: dict) -> float:
    if record["unite"] == "zeros":
        return record["valeur"]
    return zeros_lisses(record["valeur"])


def _hauteur_equivalente(record: dict) -> float:
    if record["unite"] == "hauteur":
        return record["valeur"]
    return hauteur_pour_zeros(record["valeur"])


def couverture(zeros: float) -> dict | None:
    candidats = [r for r in RECORDS if _zeros_equivalents(r) >= zeros * (1 - 1e-9)]
    if not candidats:
        return None
    return min(candidats, key=_zeros_equivalents)


def classe_cout(evaluations: float) -> str:
    if evaluations <= 2e4:
        return "minutes a dizaines de minutes"
    if evaluations <= 1e6:
        return "jours"
    if evaluations <= 1e9:
        return "decennies a un siecle"
    return "hors de portee mono-machine"


def _fmt(value: float) -> str:
    return f"{value:.6g}"


def analyse(mode: str, requete: float) -> dict:
    if mode == "zeros":
        hauteur = hauteur_pour_zeros(requete)
        zeros = requete
    else:
        hauteur = requete
        zeros = zeros_lisses(requete)
    couv = couverture(zeros)
    return {
        "mode": mode,
        "valeur_demandee": requete,
        "hauteur_T": hauteur,
        "zeros_lisses_a_T": zeros,
        "evaluations_estimees": zeros,
        "classe_cout": classe_cout(zeros),
        "classe_cout_base": "ordre de grandeur, non mesure",
        "deja_publie": couv is not None,
        "couvert_par": None
        if couv is None
        else f"{couv['source']} ({_fmt(_zeros_equivalents(couv))} zeros)",
        "anteriorite_revendicable": "non",
    }


def _afficher(resultat: dict) -> None:
    for cle, valeur in resultat.items():
        if isinstance(valeur, bool):
            valeur = "oui" if valeur else "non"
        elif isinstance(valeur, float):
            valeur = _fmt(valeur)
        print(f"{cle}={valeur}")


def _table() -> None:
    print("zeros_cibles|hauteur_T|evaluations_estimees|deja_publie")
    for zeros in CIBLES:
        hauteur = hauteur_pour_zeros(zeros)
        couv = couverture(zeros)
        print(
            f"{_fmt(zeros)}|{_fmt(hauteur)}|{_fmt(zeros)}|"
            f"{'oui' if couv else 'non'}"
        )
    print("source|unite|valeur|zeros_equivalents|hauteur_equivalente")
    for record in RECORDS:
        print(
            f"{record['source']}|{record['unite']}|{_fmt(record['valeur'])}|"
            f"{_fmt(_zeros_equivalents(record))}|"
            f"{_fmt(_hauteur_equivalente(record))}"
        )


def _positif(texte: str) -> float:
    try:
        valeur = float(texte)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("valeur numerique attendue") from exc
    if not math.isfinite(valeur) or valeur <= 0:
        raise argparse.ArgumentTypeError("valeur finie > 0 attendue")
    return valeur


def main(argv: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(
        description="Chiffrer une revendication de calcul fini sur les zeros de zeta."
    )
    groupe = parseur.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--zeros", type=_positif, help="nombre de zeros vises (ex. 1e9)")
    groupe.add_argument("--hauteur", type=_positif, help="hauteur T visee (ex. 10000)")
    groupe.add_argument("--table", action="store_true", help="table des cibles et des records")
    parseur.add_argument("--json", action="store_true", help="sortie JSON (ASCII)")
    args = parseur.parse_args(argv)

    if args.table:
        _table()
        return 0

    if args.zeros is not None:
        if args.zeros < 1:
            print("ERREUR: le nombre de zeros doit etre >= 1", file=sys.stderr)
            return 2
        resultat = analyse("zeros", args.zeros)
    else:
        if args.hauteur < T_MIN:
            print(f"ERREUR: hauteur >= {T_MIN:g} attendue", file=sys.stderr)
            return 2
        resultat = analyse("hauteur", args.hauteur)

    if args.json:
        print(json.dumps(resultat, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        _afficher(resultat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
