#!/usr/bin/env python3
"""Auto-test isole de nettoyer_archives_copie_soi.py (fixtures temporaires).

Sortie ASCII : PASS/FAIL par controle, puis RESULT: TOTAL=N ECHECS=M.
Code 0 si tous les controles executes passent, 1 sinon. Rien n'est conserve.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nettoyer_archives_copie_soi.py")
TOTAL = 0
ECHECS: list[str] = []
SORTIES: list[str] = []


def ecrire(chemin: str, texte: str) -> None:
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as fh:
        fh.write(texte)


def controle(nom: str, condition: bool, detail: str = "") -> None:
    global TOTAL
    TOTAL += 1
    if condition:
        print("PASS", nom)
    else:
        print("FAIL", nom, ascii(detail)[:300])
        ECHECS.append(nom)


def lancer(copie: str, stamps: list[str], appliquer: bool = False, extra: list[str] | None = None):
    arguments = [sys.executable, "-B", SCRIPT]
    if copie:
        arguments += ["--copie-soi", copie]
    for stamp in stamps:
        arguments += ["--stamp", stamp]
    if appliquer:
        arguments.append("--appliquer")
    if extra:
        arguments += extra
    processus = subprocess.run(
        arguments, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    SORTIES.append(processus.stdout)
    return processus


def construire(racine: str) -> str:
    copie = os.path.join(racine, "copie")
    courante = os.path.join(copie, "courante")
    historique = os.path.join(copie, "historique")
    ecrire(os.path.join(courante, "a.py"), "A\n")
    ecrire(os.path.join(courante, "sub", "b.py"), "B\n")
    ecrire(os.path.join(courante, "_manifeste_copie_soi.json"), "{}\n")
    for stamp in ("20261027T104230Z", "20261027T104541Z"):
        shutil.copytree(courante, os.path.join(historique, stamp))
    ecrire(os.path.join(historique, "20261027T104541Z", "a.py"), "A2\n")
    shutil.copytree(courante, os.path.join(historique, "20261027T104828Z"))
    ecrire(os.path.join(historique, "20261027T104828Z", "extra.py"), "X\n")
    shutil.copytree(courante, os.path.join(historique, "20260101T000000Z"))
    return copie


def main() -> int:
    racine = tempfile.mkdtemp(prefix="test_nettoyage_archives_")
    try:
        copie = construire(racine)
        sain = "20261027T104230Z"
        divergeant = "20261027T104541Z"
        unique = "20261027T104828Z"
        ancienne = "20260101T000000Z"

        plan = lancer(copie, [sain, divergeant])
        controle("plan_code_0", plan.returncode == 0, plan.stderr)
        controle("plan_resume", "RESULT: PLAN" in plan.stdout, plan.stdout)
        controle(
            "plan_diff_detecte",
            "ARCHIVE 20261027T104541Z" in plan.stdout and "DIFF_VS_COURANTE 1" in plan.stdout,
            plan.stdout,
        )
        controle(
            "plan_sans_suppression",
            os.path.isdir(os.path.join(copie, "historique", sain))
            and os.path.isdir(os.path.join(copie, "historique", divergeant)),
        )

        stop = lancer(copie, [sain, unique], appliquer=True)
        controle("unique_code_1", stop.returncode == 1, stop.stderr)
        controle("unique_resume", "RESULT: STOP" in stop.stdout, stop.stdout)
        controle(
            "unique_fichier_liste",
            "UNIQUE_FILE" in stop.stdout and "extra.py" in stop.stdout,
            stop.stdout,
        )
        controle(
            "unique_atomique_aucune_suppression",
            os.path.isdir(os.path.join(copie, "historique", sain))
            and os.path.isdir(os.path.join(copie, "historique", unique)),
            "une archive saine a ete supprimee malgre le STOP",
        )

        applique = lancer(copie, [sain, divergeant], appliquer=True)
        controle("apply_code_0", applique.returncode == 0, applique.stderr)
        controle("apply_resume", "RESULT: APPLIED" in applique.stdout, applique.stdout)
        controle(
            "apply_supprime_les_deux",
            not os.path.exists(os.path.join(copie, "historique", sain))
            and not os.path.exists(os.path.join(copie, "historique", divergeant)),
        )
        controle(
            "apply_conserve_courante_et_ancienne",
            os.path.isdir(os.path.join(copie, "courante"))
            and os.path.isdir(os.path.join(copie, "historique", ancienne)),
        )
        controle(
            "apply_compte_restantes",
            "REMAINING 2" in applique.stdout,
            applique.stdout,
        )
        controle(
            "apply_courante_intacte",
            "COURANTE_FILES_APRES 3" in applique.stdout,
            applique.stdout,
        )
        controle(
            "apply_reverif_tardive",
            "REVERIF_TARDIVE 2" in applique.stdout,
            applique.stdout,
        )

        manquante = lancer(copie, [sain])
        controle("archive_absente_code_2", manquante.returncode == 2, manquante.stderr)
        controle("archive_absente_resume", "RESULT: ERROR" in manquante.stdout, manquante.stdout)
        controle("archive_absente_garde", "ABSENTE" in manquante.stdout, manquante.stdout)

        format_invalide = lancer(copie, ["2026-10-27T104230Z"])
        controle("stamp_invalide_code_2", format_invalide.returncode == 2, format_invalide.stderr)

        doublon = lancer(copie, [ancienne, ancienne])
        controle("stamp_doublon_code_2", doublon.returncode == 2, doublon.stderr)
        controle("stamp_doublon_message", "STAMP_DUPLIQUE" in doublon.stdout, doublon.stdout)

        sans_stamp = lancer(copie, [])
        controle("sans_stamp_code_2", sans_stamp.returncode == 2, sans_stamp.stderr)

        fichier = os.path.join(copie, "historique", "20261027T888888Z")
        ecrire(fichier, "pas un dossier\n")
        pas_dossier = lancer(copie, ["20261027T888888Z"])
        controle("pas_un_dossier_code_2", pas_dossier.returncode == 2, pas_dossier.stderr)
        controle("pas_un_dossier_garde", "PAS_UN_DOSSIER" in pas_dossier.stdout, pas_dossier.stdout)
        os.remove(fichier)

        lien = os.path.join(copie, "historique", "20261027T999999Z")
        try:
            os.symlink(os.path.join(copie, "courante"), lien, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            print("SKIP symlink_indisponible", type(exc).__name__)
        else:
            refus_lien = lancer(copie, ["20261027T999999Z"])
            controle("symlink_code_2", refus_lien.returncode == 2, refus_lien.stderr)
            controle("symlink_garde", "SYMLINK" in refus_lien.stdout, refus_lien.stdout)
            os.remove(lien) if os.path.islink(lien) else None

        racine_hist_lien = os.path.join(racine, "copie_hist_lien")
        os.makedirs(os.path.join(racine_hist_lien, "courante"))
        lien_hist = os.path.join(racine_hist_lien, "historique")
        try:
            os.symlink(os.path.join(copie, "historique"), lien_hist, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            print("SKIP historique_symlink_indisponible", type(exc).__name__)
        else:
            refus_hist = lancer(racine_hist_lien, [ancienne])
            controle("historique_lien_code_2", refus_hist.returncode == 2, refus_hist.stderr)
            controle(
                "historique_lien_message",
                "HISTORIQUE_LIEN" in refus_hist.stdout,
                refus_hist.stdout,
            )
            os.remove(lien_hist)

        copie_sans_courante = os.path.join(racine, "copie_sans_courante")
        os.makedirs(os.path.join(copie_sans_courante, "historique", ancienne))
        sans_courante = lancer(copie_sans_courante, [ancienne])
        controle("courante_absente_code_2", sans_courante.returncode == 2, sans_courante.stderr)
        controle(
            "courante_absente_message",
            "COURANTE_ABSENTE_OU_LIEN" in sans_courante.stdout,
            sans_courante.stdout,
        )

        aide = lancer("", [], extra=["--help"])
        controle("help_code_0", aide.returncode == 0, aide.stderr)
        controle("help_usage", "usage" in aide.stdout.lower(), aide.stdout[:200])

        controle(
            "sortie_ascii",
            all(_est_ascii(texte) for texte in SORTIES),
            "sortie non ASCII detectee",
        )
        controle(
            "aucun_pycache",
            not os.path.exists(os.path.join(os.path.dirname(SCRIPT), "__pycache__")),
        )
    finally:
        shutil.rmtree(racine, ignore_errors=True)

    print(f"RESULT: TOTAL={TOTAL} ECHECS={len(ECHECS)}")
    if ECHECS:
        print("ECHECS: " + ", ".join(ECHECS))
        return 1
    return 0


def _est_ascii(texte: str) -> bool:
    try:
        texte.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


if __name__ == "__main__":
    sys.exit(main())
