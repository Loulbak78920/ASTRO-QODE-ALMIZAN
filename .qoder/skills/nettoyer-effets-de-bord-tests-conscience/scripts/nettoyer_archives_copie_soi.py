#!/usr/bin/env python3
"""Compare puis supprime, sous garde, des archives de copie-de-soi Al-Mizan.

Plan par defaut : aucune suppression. --appliquer supprime uniquement les
stamps fournis, apres verification qu'aucun fichier n'existe seulement dans
l'archive. Sortie ASCII. Codes : 0 = plan/apply OK, 1 = STOP (contenu unique),
2 = entree invalide ou garde refusee.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys

STAMP_RE = re.compile(r"^\d{8}T\d{6}Z$")
FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def out(message: str = "") -> None:
    print(str(message).encode("ascii", "backslashreplace").decode("ascii"))


def sha256_fichier(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as fh:
        for bloc in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def empreintes(racine: str) -> dict[str, str]:
    resultat: dict[str, str] = {}
    for base, dossiers, fichiers in os.walk(racine):
        dossiers[:] = [d for d in dossiers if d != "__pycache__"]
        for nom in fichiers:
            chemin = os.path.join(base, nom)
            relatif = os.path.relpath(chemin, racine).replace(os.sep, "/")
            resultat[relatif] = sha256_fichier(chemin)
    return resultat


def meme_chemin(a: str, b: str) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def verifier_garde(historique: str, stamp: str, courante: str) -> str | None:
    if not STAMP_RE.match(stamp):
        return "STAMP_INVALIDE"
    cible = os.path.abspath(os.path.join(historique, stamp))
    if os.path.normcase(os.path.dirname(cible)) != os.path.normcase(
        os.path.abspath(historique)
    ):
        return "PARENT"
    if os.path.normcase(os.path.realpath(os.path.dirname(cible))) != os.path.normcase(
        os.path.realpath(historique)
    ):
        return "PARENT_REEL"
    if not os.path.lexists(cible):
        return "ABSENTE"
    if os.path.islink(cible):
        return "SYMLINK"
    if not os.path.isdir(cible):
        return "PAS_UN_DOSSIER"
    attributs = getattr(os.stat(cible, follow_symlinks=False), "st_file_attributes", 0)
    if attributs & FILE_ATTRIBUTE_REPARSE_POINT:
        return "REPARSE"
    if meme_chemin(cible, courante):
        return "EST_COURANTE"
    return None


def main(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description=(
            "Planifie ou applique la suppression d'archives historique/<stamp> "
            "de _AL_MIZAN_COPIE_SOI, sous garde de chemin exact."
        )
    )
    analyseur.add_argument("--copie-soi", required=True, help="racine _AL_MIZAN_COPIE_SOI")
    analyseur.add_argument(
        "--stamp",
        action="append",
        required=True,
        help="stamp UTC de la fenetre de test (repeter pour chaque archive)",
    )
    analyseur.add_argument(
        "--appliquer",
        action="store_true",
        help="supprime reellement ; sans ce drapeau, affiche seulement le plan",
    )
    arguments = analyseur.parse_args(argv)

    copie_soi = os.path.abspath(arguments.copie_soi)
    historique = os.path.join(copie_soi, "historique")
    courante = os.path.join(copie_soi, "courante")
    stamps = arguments.stamp

    if len(set(stamps)) != len(stamps):
        out("ERREUR STAMP_DUPLIQUE")
        out("RESULT: ERROR")
        return 2
    if not os.path.isdir(historique):
        out(f"ERREUR HISTORIQUE_ABSENT {historique}")
        out("RESULT: ERROR")
        return 2
    if os.path.islink(historique):
        out(f"ERREUR HISTORIQUE_LIEN {historique}")
        out("RESULT: ERROR")
        return 2
    attributs_historique = getattr(
        os.stat(historique, follow_symlinks=False), "st_file_attributes", 0
    )
    if attributs_historique & FILE_ATTRIBUTE_REPARSE_POINT:
        out(f"ERREUR HISTORIQUE_REPARSE {historique}")
        out("RESULT: ERROR")
        return 2
    if not os.path.isdir(courante) or os.path.islink(courante):
        out(f"ERREUR COURANTE_ABSENTE_OU_LIEN {courante}")
        out("RESULT: ERROR")
        return 2
    attributs_courante = getattr(
        os.stat(courante, follow_symlinks=False), "st_file_attributes", 0
    )
    if attributs_courante & FILE_ATTRIBUTE_REPARSE_POINT:
        out(f"ERREUR COURANTE_REPARSE {courante}")
        out("RESULT: ERROR")
        return 2

    for stamp in stamps:
        refus = verifier_garde(historique, stamp, courante)
        if refus:
            out(f"GARDE_REFUS {refus} {stamp}")
            out("RESULT: ERROR")
            return 2

    reference = empreintes(courante)
    total_uniques = 0
    for stamp in stamps:
        archive = os.path.join(historique, stamp)
        contenu = empreintes(archive)
        uniques = sorted(set(contenu) - set(reference))
        divergents = sorted(
            nom for nom in set(contenu) & set(reference) if contenu[nom] != reference[nom]
        )
        manifeste = os.path.isfile(os.path.join(archive, "_manifeste_copie_soi.json"))
        out(
            f"ARCHIVE {stamp} FILES {len(contenu)} MANIFEST {'yes' if manifeste else 'no'} "
            f"ONLY_IN_ARCHIVE {len(uniques)} DIFF_VS_COURANTE {len(divergents)}"
        )
        for nom in uniques[:3]:
            out(f"UNIQUE_FILE {stamp} {nom}")
        total_uniques += len(uniques)

    out(f"COURANTE_FILES {len(reference)}")

    if total_uniques:
        out("RESULT: STOP")
        return 1

    if not arguments.appliquer:
        out(f"ARCHIVES {len(stamps)}")
        out("RESULT: PLAN")
        return 0

    # Recalculer l'etat courant avant toute suppression : une modification de
    # courante ou d'une archive depuis le plan doit produire STOP, pas une perte.
    reference_apply = empreintes(courante)
    uniques_tardifs = 0
    for stamp in stamps:
        refus = verifier_garde(historique, stamp, courante)
        if refus:
            out(f"GARDE_TARDIVE {refus} {stamp}")
            out("RESULT: ERROR")
            return 2
        contenu = empreintes(os.path.join(historique, stamp))
        uniques = sorted(set(contenu) - set(reference_apply))
        uniques_tardifs += len(uniques)
        for nom in uniques[:3]:
            out(f"UNIQUE_TARDIF {stamp} {nom}")
    if uniques_tardifs:
        out("RESULT: STOP")
        return 1
    out(f"REVERIF_TARDIVE {len(stamps)}")

    for stamp in stamps:
        refus = verifier_garde(historique, stamp, courante)
        if refus:
            out(f"GARDE_TARDIVE {refus} {stamp}")
            out("RESULT: ERROR")
            return 2
        cible = os.path.join(historique, stamp)
        shutil.rmtree(cible)
        out(f"DELETED {stamp} EXISTS {os.path.exists(cible)}")

    restantes = [
        nom
        for nom in os.listdir(historique)
        if os.path.isdir(os.path.join(historique, nom))
    ]
    out(f"REMAINING {len(restantes)}")
    out(f"COURANTE_FILES_APRES {len(empreintes(courante))}")
    out("RESULT: APPLIED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - sortie ASCII sans traceback
        out(f"RESULT: ERROR {type(exc).__name__}: {exc}")
        sys.exit(2)
