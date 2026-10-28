#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evaluer un modele de qualification en logique ternaire de Kleene.

Le modele JSON contient des predicats (VRAI, FAUX, INDETERMINE) et des regles
composees de ET, OU, NON et de parentheses. Une regle peut referencer une autre
regle : l'evaluation est recursive, avec detection de cycle. Un fait non prouve
reste INDETERMINE ; il n'est jamais converti en VRAI.

Codes de retour :
  0  modele evalue, et toutes les regles --exiger valent VRAI
  1  erreur d'evaluation (atome inconnu, syntaxe, cycle) ou regle --exiger non VRAI
  2  fichier absent, JSON invalide ou schema incomplet
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

VRAI, FAUX, INDETERMINE = "VRAI", "FAUX", "INDETERMINE"
VALEURS = {VRAI, FAUX, INDETERMINE}


def forcer_utf8() -> None:
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def maintenant_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def et(*valeurs: str) -> str:
    if FAUX in valeurs:
        return FAUX
    if INDETERMINE in valeurs:
        return INDETERMINE
    return VRAI


def ou(*valeurs: str) -> str:
    if VRAI in valeurs:
        return VRAI
    if INDETERMINE in valeurs:
        return INDETERMINE
    return FAUX


def non(valeur: str) -> str:
    return {VRAI: FAUX, FAUX: VRAI, INDETERMINE: INDETERMINE}[valeur]


class ErreurModele(Exception):
    pass


class Parseur:
    """Parseur recursif descendant : OU < ET < NON < atome."""

    def __init__(self, jetons: list[str], resoudre: Callable[[str], str]):
        self.jetons = jetons
        self.resoudre = resoudre
        self.position = 0

    def sommet(self) -> str:
        return self.ou()

    def ou(self) -> str:
        valeur = self.et()
        while self.present("OU"):
            self.consommer()
            valeur = ou(valeur, self.et())
        return valeur

    def et(self) -> str:
        valeur = self.non_terme()
        while self.present("ET"):
            self.consommer()
            valeur = et(valeur, self.non_terme())
        return valeur

    def non_terme(self) -> str:
        if self.present("NON"):
            self.consommer()
            return non(self.non_terme())
        return self.atome()

    def atome(self) -> str:
        if self.present("("):
            self.consommer()
            valeur = self.ou()
            self.attendre(")")
            return valeur
        jeton = self.consommer()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", jeton):
            raise ErreurModele(f"atome inattendu : {jeton}")
        return self.resoudre(jeton)

    def present(self, jeton: str) -> bool:
        return self.position < len(self.jetons) and self.jetons[self.position] == jeton

    def consommer(self) -> str:
        if self.position >= len(self.jetons):
            raise ErreurModele("expression tronquee")
        jeton = self.jetons[self.position]
        self.position += 1
        return jeton

    def attendre(self, jeton: str) -> None:
        if self.consommer() != jeton:
            raise ErreurModele(f"jeton {jeton} attendu")

    def termine(self) -> bool:
        return self.position == len(self.jetons)


def jetons(expression: str) -> list[str]:
    return re.findall(r"\(|\)|[A-Z][A-Z0-9_]*", str(expression).upper())


class Evaluateur:
    def __init__(self, modele: dict[str, Any]):
        self.predicats = {p["id"]: p for p in modele["predicats"]}
        self.regles = {r["id"]: r for r in modele["regles"]}
        self.cache: dict[str, str] = {}
        self.erreurs: dict[str, str] = {}
        for ident, predicat in self.predicats.items():
            if predicat.get("valeur") not in VALEURS:
                raise ErreurModele(f"valeur invalide pour {ident} : {predicat.get('valeur')!r}")

    def valeur(self, jeton: str, pile: frozenset[str]) -> str:
        if jeton in self.predicats:
            return self.predicats[jeton]["valeur"]
        if jeton in self.regles:
            return self.regle(jeton, pile)
        raise ErreurModele(f"predicat ou regle inconnu : {jeton}")

    def regle(self, ident: str, pile: frozenset[str]) -> str:
        if ident in self.cache:
            return self.cache[ident]
        if ident in pile:
            raise ErreurModele(f"cycle de regles : {ident}")
        expression = self.regles[ident].get("expression")
        if not expression:
            raise ErreurModele(f"regle {ident} sans expression")
        parseur = Parseur(jetons(expression), lambda j: self.valeur(j, pile | {ident}))
        valeur = parseur.sommet()
        if not parseur.termine():
            raise ErreurModele(f"jetons non consommes dans {ident}")
        self.cache[ident] = valeur
        return valeur

    def evaluer_tout(self) -> dict[str, str]:
        for ident in self.regles:
            try:
                self.regle(ident, frozenset())
            except ErreurModele as erreur:
                self.erreurs[ident] = str(erreur)
                self.cache[ident] = INDETERMINE
        return dict(self.cache)


def feuilles(expression: str, regles: dict[str, Any], vus: set[str] | None = None) -> list[str]:
    vus = vus or set()
    resultat: list[str] = []
    for jeton in jetons(expression):
        if jeton in {"ET", "OU", "NON", "(", ")"}:
            continue
        regle = regles.get(jeton)
        if regle is None:
            resultat.append(jeton)
        elif jeton not in vus:
            vus.add(jeton)
            resultat.extend(feuilles(regle["expression"], regles, vus))
        else:
            resultat.append(jeton)
    return resultat


def charger(chemin: Path) -> dict[str, Any]:
    modele = json.loads(chemin.read_text(encoding="utf-8"))
    if not isinstance(modele, dict) or not isinstance(modele.get("predicats"), list) or not isinstance(modele.get("regles"), list):
        raise ErreurModele("schema attendu : predicats[] et regles[]")
    identifiants = [p.get("id") for p in modele["predicats"]] + [r.get("id") for r in modele["regles"]]
    if any(not identifiant for identifiant in identifiants):
        raise ErreurModele("chaque predicat et regle doit avoir un id")
    if len(set(identifiants)) != len(identifiants):
        raise ErreurModele("ids dupliques entre predicats et regles")
    return modele


def ecrire_json(chemin: Path, donnees: Any) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="\n") as flux:
        json.dump(donnees, flux, indent=1, ensure_ascii=False)
        flux.write("\n")


def ecrire_texte(chemin: Path, texte: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="\n") as flux:
        flux.write(texte if texte.endswith("\n") else texte + "\n")


def rapport_markdown(sortie: dict[str, Any]) -> str:
    lignes = [
        "# Evaluation ternaire du modele",
        "",
        f"- Genere le : **{sortie['genere_le']}**",
        f"- Modele : `{sortie['modele']}`",
        "- Logique : Kleene (ET, OU, NON) ; un fait non prouve reste INDETERMINE.",
        "",
        "## Predicats",
        "",
        "| ID | Libelle | Valeur | Base legale |",
        "|---|---|---|---|",
    ]
    for p in sortie["predicats"]:
        lignes.append(f"| {p['id']} | {p.get('libelle', '')} | `{p['valeur']}` | {p.get('base_legale', '')} |")
    lignes += ["", "## Regles", "", "| ID | Libelle | Expression | Valeur | Couverture |", "|---|---|---|---|---|"]
    for r in sortie["regles"]:
        lignes.append(
            f"| {r['id']} | {r.get('libelle', '')} | `{r['expression']}` | `{r['valeur']}` | {r['couverture_pct']} % |"
        )
    lignes += ["", "## Portee", ""]
    lignes.append("La couverture mesure la part de predicats de base tenus pour VRAIS.")
    lignes.append("Elle ne mesure ni la force d'une preuve ni l'appreciation du juge.")
    if sortie["erreurs"]:
        lignes += ["", "## Erreurs d'evaluation", ""]
        for ident, message in sortie["erreurs"].items():
            lignes.append(f"- `{ident}` : {message}")
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    forcer_utf8()
    p = argparse.ArgumentParser(description="Evaluer un modele de qualification en logique ternaire.")
    p.add_argument("--modele", required=True, help="modele JSON (predicats, regles)")
    p.add_argument("--out-json", help="rapport JSON")
    p.add_argument("--out-md", help="rapport Markdown")
    p.add_argument("--exiger", action="append", default=[], help="regle qui doit valoir VRAI (repetable)")
    args = p.parse_args(argv)

    chemin = Path(args.modele)
    if not chemin.exists():
        print(f"ERREUR modele absent : {chemin}")
        return 2
    try:
        modele = charger(chemin)
        evaluateur = Evaluateur(modele)
        resultats = evaluateur.evaluer_tout()
    except (OSError, json.JSONDecodeError, KeyError, ErreurModele) as erreur:
        print(f"ERREUR modele : {erreur}")
        return 2

    details = []
    for regle in modele["regles"]:
        base = {p: evaluateur.predicats[p]["valeur"] for p in feuilles(regle["expression"], evaluateur.regles) if p in evaluateur.predicats}
        compte = {v: sum(1 for x in base.values() if x == v) for v in (VRAI, FAUX, INDETERMINE)}
        total = sum(compte.values())
        details.append(
            {
                "id": regle["id"],
                "libelle": regle.get("libelle", ""),
                "expression": regle["expression"],
                "base_legale": regle.get("base_legale", ""),
                "valeur": resultats.get(regle["id"], INDETERMINE),
                "predicats_de_base": base,
                "termes_refutes": [k for k, v in base.items() if v == FAUX],
                "termes_indetermines": [k for k, v in base.items() if v == INDETERMINE],
                "compte": compte,
                "couverture_pct": round(100 * compte[VRAI] / total, 1) if total else 0.0,
            }
        )

    sortie = {
        "genere_le": maintenant_utc(),
        "modele": str(chemin),
        "logique": "Kleene ternaire (ET/OU/NON)",
        "predicats": modele["predicats"],
        "regles": details,
        "resultats": resultats,
        "erreurs": evaluateur.erreurs,
        "regles_exigees": args.exiger,
    }
    if args.exiger:
        sortie["gate"] = {ident: resultats.get(ident, INDETERMINE) for ident in args.exiger}
        sortie["gate_remplie"] = all(valeur == VRAI for valeur in sortie["gate"].values())
    if args.out_json:
        ecrire_json(Path(args.out_json), sortie)
    if args.out_md:
        ecrire_texte(Path(args.out_md), rapport_markdown(sortie))

    print(f"REGLES: {len(details)} evaluees")
    print("RESULTATS: " + " ".join(f"{ident}={resultats.get(ident, INDETERMINE)}" for ident in resultats))
    if evaluateur.erreurs:
        for ident, message in evaluateur.erreurs.items():
            print(f"ERREUR REGLE {ident}: {message}")
    if args.exiger:
        for ident in args.exiger:
            print(f"GATE {ident}: {resultats.get(ident, INDETERMINE)}")
    if evaluateur.erreurs:
        print("RESULTAT: ERREUR_MODELE")
        return 1
    if args.exiger and not sortie["gate_remplie"]:
        print("RESULTAT: GATE_NON_REMPLIE")
        return 1
    print("RESULTAT: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
