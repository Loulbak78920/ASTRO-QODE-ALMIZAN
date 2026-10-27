#!/usr/bin/env python3
"""Double-reading gate for a cheap observable.

Runs two strictly identical listings (same root, motif, exclusions and
cutoff) separated by a fixed interval, then reports timing, set equality
and a falsifiable verdict.

Read-only with respect to the observed tree: writes only the two list
files under --sortie, and refuses a --sortie located inside --racine.
Exit codes: 0 stable lists, 1 different lists, 2 usage or environment error.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import stat
import sys
import time
from datetime import datetime

FORMAT_COUPURE = "%Y-%m-%d %H:%M:%S %z"
MAX_LIGNES_DIFF = 20


class ErreurPorte(Exception):
    pass


def ascii_texte(valeur: object) -> str:
    return str(valeur).encode("ascii", "backslashreplace").decode("ascii")


def analyser_coupure(valeur: str) -> datetime:
    try:
        coupure = datetime.strptime(valeur, FORMAT_COUPURE)
    except ValueError:
        raise ErreurPorte(
            "coupure invalide: attendu 'YYYY-MM-DD HH:MM:SS +HHMM' avec decalage explicite"
        )
    if coupure.tzinfo is None:
        raise ErreurPorte("coupure sans decalage horaire: refusee")
    return coupure


def est_reparse(chemin: str) -> bool:
    try:
        st = os.stat(chemin, follow_symlinks=False)
    except OSError:
        return True
    attributs = getattr(st, "st_file_attributes", 0)
    drapeau = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributs & drapeau) if drapeau else False


def relever(racine: str, motif: str, exclusions: set[str], seuil: float) -> list[str]:
    resultat: list[str] = []

    def erreur(exc: OSError) -> None:
        raise exc

    for dossier, sous_dossiers, fichiers in os.walk(
        racine, topdown=True, followlinks=False, onerror=erreur
    ):
        sous_dossiers[:] = [
            nom
            for nom in sous_dossiers
            if nom not in exclusions
            and not est_reparse(os.path.join(dossier, nom))
        ]
        for nom in fichiers:
            if not fnmatch.fnmatchcase(nom, motif):
                continue
            chemin = os.path.join(dossier, nom)
            try:
                st = os.stat(chemin, follow_symlinks=False)
            except OSError as exc:
                raise ErreurPorte(f"stat impossible: {chemin} ({exc})")
            if st.st_mtime > seuil:
                resultat.append(os.path.relpath(chemin, racine).replace(os.sep, "/"))
    resultat.sort()
    return resultat


def ecrire_liste(chemin: str, lignes: list[str]) -> str:
    contenu = "".join(ligne + "\n" for ligne in lignes)
    with open(chemin, "w", encoding="utf-8", newline="\n") as flux:
        flux.write(contenu)
    return hashlib.sha256(contenu.encode("utf-8")).hexdigest()


def construire_parseur() -> argparse.ArgumentParser:
    parseur = argparse.ArgumentParser(
        description="Porte a double releve: deux listes identiques separees d'un intervalle.",
        epilog=(
            "Sortie ASCII: LISTE_A, LISTE_B, ENSEMBLES_IDENTIQUES, COUT_A, COUT_B, "
            "ECART_DEBUTS, FENETRE, MARGE, SHA256_A/B, VERDICT. "
            "Code 0 = listes identiques, 1 = listes differentes, 2 = erreur."
        ),
    )
    parseur.add_argument("--racine", required=True, help="racine observee")
    parseur.add_argument(
        "--coupure",
        required=True,
        help="coupure mtime avec decalage obligatoire, ex. '2026-10-27 11:58:00 +0000'",
    )
    parseur.add_argument(
        "--intervalle",
        type=float,
        default=12.0,
        help="secondes entre la fin du releve A et le debut du releve B (defaut 12)",
    )
    parseur.add_argument(
        "--motif", default="*.py", help="motif de nom, sensible a la casse (defaut *.py)"
    )
    parseur.add_argument(
        "--exclure",
        action="append",
        default=[],
        help="nom de dossier exclu, repetable (__pycache__ toujours exclu)",
    )
    parseur.add_argument("--sortie", required=True, help="dossier des deux listes")
    parseur.add_argument(
        "--max-diff",
        type=int,
        default=MAX_LIGNES_DIFF,
        help=f"lignes +/- affichees au maximum (defaut {MAX_LIGNES_DIFF})",
    )
    return parseur


def executer(args: argparse.Namespace) -> int:
    racine = os.path.realpath(os.path.abspath(args.racine))
    sortie = os.path.realpath(os.path.abspath(args.sortie))
    if not os.path.isdir(racine):
        raise ErreurPorte(f"racine absente ou non repertoire: {racine}")
    try:
        commun = os.path.commonpath([racine, sortie])
        if os.path.normcase(commun) == os.path.normcase(racine):
            raise ErreurPorte("--sortie est dans --racine: la porte ecrirait dans l'arbre observe")
    except ValueError:
        pass
    coupure = analyser_coupure(args.coupure)
    if args.intervalle < 0:
        raise ErreurPorte("--intervalle doit etre >= 0")
    exclusions = {"__pycache__"} | set(args.exclure)
    os.makedirs(sortie, exist_ok=True)
    seuil = coupure.timestamp()

    debut = time.perf_counter()
    liste_a = relever(racine, args.motif, exclusions, seuil)
    cout_a = time.perf_counter() - debut

    time.sleep(args.intervalle)

    debut_b = time.perf_counter()
    liste_b = relever(racine, args.motif, exclusions, seuil)
    cout_b = time.perf_counter() - debut_b
    fin = time.perf_counter()

    sha_a = ecrire_liste(os.path.join(sortie, "releve_a.txt"), liste_a)
    sha_b = ecrire_liste(os.path.join(sortie, "releve_b.txt"), liste_b)

    identiques = liste_a == liste_b
    entres = sorted(set(liste_b) - set(liste_a))
    sortis = sorted(set(liste_a) - set(liste_b))
    marge = args.intervalle - max(cout_a, cout_b)

    print(f"RACINE={ascii_texte(racine)}")
    print(f"SORTIE={ascii_texte(sortie)}")
    print(f"COUPURE={coupure.strftime(FORMAT_COUPURE)}")
    print(f"MOTIF={ascii_texte(args.motif)}")
    print(f"EXCLUS={ascii_texte(','.join(sorted(exclusions)))}")
    print(f"INTERVALLE={args.intervalle:.2f}")
    print(f"COUT_A={cout_a:.2f}")
    print(f"COUT_B={cout_b:.2f}")
    print(f"LISTE_A={len(liste_a)}")
    print(f"LISTE_B={len(liste_b)}")
    print(f"ENSEMBLES_IDENTIQUES={'yes' if identiques else 'no'}")
    print(f"ENTRES={len(entres)}")
    print(f"SORTIS={len(sortis)}")
    for chemin in entres[: args.max_diff]:
        print("+ " + ascii_texte(chemin))
    for chemin in sortis[: args.max_diff]:
        print("- " + ascii_texte(chemin))
    print(f"ECART_DEBUTS={cout_a + args.intervalle:.2f}")
    print(f"FENETRE={fin - debut:.2f}")
    print(f"MARGE={marge:.2f}")
    print(f"SHA256_A={sha_a}")
    print(f"SHA256_B={sha_b}")
    if args.intervalle <= 0:
        print("AVERTISSEMENT=INTERVALLE_NUL")
    elif marge < 0:
        print("AVERTISSEMENT=INTERVALLE_SERRE")
    print(f"VERDICT={'LISTE_STABLE' if identiques else 'LISTE_INSTABLE'}")
    return 0 if identiques else 1


def main(argv: list[str] | None = None) -> int:
    args = construire_parseur().parse_args(argv)
    try:
        return executer(args)
    except ErreurPorte as exc:
        print("ERREUR: " + ascii_texte(exc), file=sys.stderr)
        return 2
    except OSError as exc:
        print("ERREUR: " + ascii_texte(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
