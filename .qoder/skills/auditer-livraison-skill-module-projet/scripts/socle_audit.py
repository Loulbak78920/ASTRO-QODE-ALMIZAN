# -*- coding: utf-8 -*-
"""Socle reutilisable d'un audit de livraison en lecture seule.

Fournit une sortie ASCII, un chargeur de module tolerant aux dataclasses,
des empreintes SHA-256, un instantane des caches bytecode et un compteur
de controles avec codes de retour 0 (PASS), 1 (FAIL), 2 (environnement).

Verifier le socle lui-meme (repertoire temporaire, aucun fichier du projet) :

    py -3 -B scripts/socle_audit.py --autotest
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# A poser avant tout import de module projet : interdit l'ecriture de __pycache__.
sys.dont_write_bytecode = True

CODE_PASS = 0
CODE_FAIL = 1
CODE_ENV = 2

FIXTURE = '''from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Parametres:
    duree_s: float = 20e-9
    libelle: str = "Q\\u00b0ODE"


def valeur() -> float:
    return Parametres().duree_s
'''

CHARGEUR_SANS_SYS_MODULES = '''import importlib.util
import sys

spec = importlib.util.spec_from_file_location("fixture_audit", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print("OK", module.valeur())
'''

CHARGEUR_AVEC_SYS_MODULES = '''import importlib.util
import sys

spec = importlib.util.spec_from_file_location("fixture_audit", sys.argv[1])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
print("OK", module.valeur())
'''


def ligne_ascii(texte: str) -> str:
    """Convertit une ligne en ASCII imprimable (non-ASCII -> \\uXXXX / \\xb0)."""
    return str(texte).encode("ascii", "backslashreplace").decode("ascii")


def ecrire(texte: str = "") -> None:
    sys.stdout.write(ligne_ascii(texte) + "\n")
    sys.stdout.flush()


def sha256(chemin: Path) -> str:
    return hashlib.sha256(Path(chemin).read_bytes()).hexdigest()


def charger_module(chemin: Path, nom: str = "module_projet_audit"):
    """Importe un fichier .py hors paquet, compatible annotations differees.

    dataclasses._is_type lit sys.modules[cls.__module__].__dict__ des qu'une
    annotation est une chaine (from __future__ import annotations). Sans
    enregistrement prealable, l'execution leve AttributeError sur None.
    """
    chemin = Path(chemin)
    spec = importlib.util.spec_from_file_location(nom, chemin)
    if spec is None or spec.loader is None:
        raise ImportError("specification de module introuvable: " + chemin.name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(nom, None)
        raise
    return module


def instantane_caches(racine: Path) -> tuple[int, str]:
    """Compte des .pyc et empreinte de la liste triee, sous une racine."""
    racine = Path(racine)
    pyc = sorted(p.relative_to(racine).as_posix() for p in racine.rglob("*.pyc"))
    dossiers = sorted(
        p.relative_to(racine).as_posix() for p in racine.rglob("__pycache__") if p.is_dir()
    )
    contenu = "\n".join(pyc + ["--"] + dossiers)
    return len(pyc), hashlib.sha256(contenu.encode("utf-8")).hexdigest()


def racine_par_defaut(
    marqueur: str,
    variable_env: str | None = None,
    sous_dossier: str | None = None,
) -> Path | None:
    """Cherche le dossier contenant `marqueur` (cwd, parent, sous-dossier)."""
    candidats: list[Path] = []
    if variable_env:
        valeur = os.environ.get(variable_env)
        if valeur:
            candidats.append(Path(valeur))
    ici = Path.cwd()
    for base in (ici, ici.parent):
        candidats.append(base)
        if sous_dossier:
            candidats.append(base / sous_dossier)
    for candidat in candidats:
        if (candidat / marqueur).is_file():
            return candidat
    return None


class Resultat:
    """Compteur de controles : une ligne OK/FAIL par controle, RESULT final."""

    def __init__(self) -> None:
        self.total = 0
        self.echecs = 0

    def ok(self, message: str) -> None:
        self.total += 1
        ecrire("OK   " + message)

    def fail(self, message: str) -> None:
        self.total += 1
        self.echecs += 1
        ecrire("FAIL " + message)

    def resume(self) -> int:
        if self.echecs:
            ecrire(f"RESULT FAIL ({self.echecs}/{self.total} controles en echec)")
            return CODE_FAIL
        ecrire(f"RESULT PASS ({self.total} controles)")
        return CODE_PASS


def _executer_enfant(script: str, chemin_module: Path, dossier: Path) -> subprocess.CompletedProcess:
    fichier = dossier / "chargeur.py"
    fichier.write_text(script, encoding="utf-8")
    env = dict(os.environ)
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    return subprocess.run(
        [sys.executable, str(fichier), str(chemin_module)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=60,
    )


def _pyc(racine: Path) -> list[str]:
    return sorted(p.as_posix() for p in Path(racine).rglob("*.pyc"))


def autotest() -> int:
    resultat = Resultat()
    try:
        with tempfile.TemporaryDirectory(prefix="socle-audit-") as brut:
            dossier = Path(brut)
            projet = dossier / "projet"
            projet.mkdir()
            module = projet / "mod.py"
            module.write_text(FIXTURE, encoding="utf-8")

            sans = _executer_enfant(CHARGEUR_SANS_SYS_MODULES, module, dossier)
            if sans.returncode != 0:
                resultat.ok(f"temoin: sans sys.modules -> rc={sans.returncode}")
            else:
                resultat.fail("temoin: sans sys.modules devrait echouer")
            if "AttributeError" in sans.stderr:
                resultat.ok("temoin: AttributeError observe")
            else:
                resultat.fail("temoin: AttributeError absent en stderr")

            shutil.rmtree(projet / "__pycache__", ignore_errors=True)

            avec = _executer_enfant(CHARGEUR_AVEC_SYS_MODULES, module, dossier)
            if avec.returncode == 0:
                resultat.ok("chargeur enregistre: rc=0")
            else:
                resultat.fail("chargeur enregistre: rc=" + str(avec.returncode))
            pyc_avec = _pyc(projet)
            if len(pyc_avec) == 1:
                resultat.ok("sans garde: 1 .pyc ecrit (garde necessaire)")
            else:
                resultat.fail(f"sans garde: {len(pyc_avec)} .pyc au lieu de 1")

            shutil.rmtree(projet / "__pycache__", ignore_errors=True)

            avant = instantane_caches(projet)
            charge = charger_module(module, "socle_audit_fixture")
            apres = instantane_caches(projet)
            if abs(charge.valeur() - 20e-9) < 1e-18:
                resultat.ok("module charge en processus: valeur attendue")
            else:
                resultat.fail("module charge en processus: valeur inattendue")
            if avant == apres and apres[0] == 0:
                resultat.ok("garde active: aucun .pyc ajoute (avant=apres)")
            else:
                resultat.fail(f"garde inactive: avant={avant} apres={apres}")

            echappee = ligne_ascii("Q\u00b0ODE \u2212")
            if all(ord(c) < 128 for c in echappee) and "\\xb0" in echappee:
                resultat.ok("sortie ASCII: non-ASCII echappe")
            else:
                resultat.fail("sortie ASCII: caractere non echappe")

            with contextlib.redirect_stdout(io.StringIO()):
                passant = Resultat()
                passant.ok("x")
                code_pass = passant.resume()
                en_echec = Resultat()
                en_echec.fail("y")
                code_fail = en_echec.resume()
            if (code_pass, code_fail) == (CODE_PASS, CODE_FAIL):
                resultat.ok("codes de retour: 0 pour PASS, 1 pour FAIL")
            else:
                resultat.fail(f"codes de retour: {code_pass}/{code_fail}")
    except (OSError, subprocess.SubprocessError) as erreur:
        ecrire("ERREUR environnement: " + type(erreur).__name__)
        return CODE_ENV
    return resultat.resume()


def main(argv: list[str] | None = None) -> int:
    parseur = argparse.ArgumentParser(
        description="Socle d'audit de livraison en lecture seule (autotest du socle)."
    )
    parseur.add_argument(
        "--autotest",
        action="store_true",
        help="verifie le socle dans un repertoire temporaire",
    )
    args = parseur.parse_args(argv)
    if args.autotest:
        return autotest()
    parseur.error("aucune action demandee (utiliser --autotest)")
    return CODE_ENV


if __name__ == "__main__":
    sys.exit(main())
