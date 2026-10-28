# -*- coding: utf-8 -*-
"""Audit local et lecture seule d'un fichier de secrets VPS et de son projet.

Ne se connecte a aucun hote, n'ecrit aucun fichier et n'affiche jamais le secret.
Codes de retour : 0 aucun FAIL, 1 au moins un FAIL, 2 erreur d'usage.

Usage :
    py -3 -B auditer_secrets_locaux.py --secrets <json> [--racine <dir>] [--max-findings N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

CLES_REQUISES = ("hote", "user", "mot_de_passe_ssh")
TAILLE_MAX_FICHIER = 2_000_000
DOSSIERS_IGNORES = {".git", "__pycache__", "node_modules", ".venv", "venv", ".qoder", ".mypy_cache"}
EXTENSIONS = {
    ".py", ".sh", ".bash", ".ps1", ".bat", ".cmd", ".md", ".txt", ".json", ".yml",
    ".yaml", ".toml", ".ini", ".cfg", ".conf", ".service", ".env", ".js", ".ts",
    ".html", ".php", ".rb", ".pl", ".go", ".rs", ".bak", ".old", ".orig", ".save",
}
MOTIFS_ANTIPATTERN = (
    (re.compile(r"\bsudo\s+-S\b"), "sudo -S"),
    (re.compile(r"\bbash\s+-s\b"), "bash -s"),
)


def _est_analyse(chemin: Path, exclu: Path) -> bool:
    if chemin.resolve() == exclu.resolve():
        return False
    if chemin.suffix.lower() in EXTENSIONS or chemin.name.startswith(".env"):
        try:
            return chemin.stat().st_size <= TAILLE_MAX_FICHIER
        except OSError:
            return False
    return False


def _fichiers(racine: Path, exclu: Path) -> List[Path]:
    resultat: List[Path] = []
    for chemin in racine.rglob("*"):
        try:
            parents = chemin.relative_to(racine).parts[:-1]
        except ValueError:
            parents = chemin.parts[:-1]
        if any(part in DOSSIERS_IGNORES for part in parents):
            continue
        if not chemin.is_file():
            continue
        if _est_analyse(chemin, exclu):
            resultat.append(chemin)
    return resultat


def analyser(secrets: Path, racine: Path, max_findings: int) -> int:
    fails: List[str] = []
    avertissements: List[str] = []

    print(f"SECRETS {secrets}")
    if not secrets.is_file():
        print(f"FICHIER absent=oui")
        print("RESULT FAIL")
        return 1
    try:
        donnees = json.loads(secrets.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FICHIER json=invalide ({type(exc).__name__})")
        print("RESULT FAIL")
        return 1
    if not isinstance(donnees, dict):
        print("FICHIER json=invalide (objet attendu)")
        print("RESULT FAIL")
        return 1
    print("FICHIER json=ok")

    manquantes = [c for c in CLES_REQUISES if not str(donnees.get(c) or "").strip()]
    if manquantes:
        fails.append("cles manquantes: " + ",".join(manquantes))
        print("CLES manquantes=" + ",".join(manquantes))
    else:
        print("CLES manquantes=aucune")

    mdp = str(donnees.get("mot_de_passe_ssh") or "")
    temporaire = str(donnees.get("mot_de_passe_temporaire") or "")
    permanent = str(donnees.get("mot_de_passe_permanent") or "")

    if temporaire:
        avertissements.append("mot_de_passe_temporaire non vide")
        print("TEMPORAIRE non_vide=oui")
    else:
        print("TEMPORAIRE non_vide=non")

    if permanent and mdp and permanent != mdp:
        avertissements.append("mot_de_passe_permanent != mot_de_passe_ssh")
        print("PERMANENT coherent=non")
    else:
        print("PERMANENT coherent=oui")

    residu = secrets.with_suffix(secrets.suffix + ".tmp")
    if residu.exists():
        fails.append(f"residu .tmp: {residu.name}")
        print(f"RESIDU tmp={residu.name}")
    else:
        print("RESIDU tmp=aucun")

    if not racine.is_dir():
        fails.append(f"racine absente: {racine}")
        print(f"SCAN racine=absente fichiers=0")
        fichiers: List[Path] = []
    else:
        fichiers = _fichiers(racine, secrets)
        print(f"SCAN racine=ok fichiers={len(fichiers)}")

    fuites: List[Tuple[Path, int]] = []
    antipatrons: List[Tuple[Path, int, str]] = []
    if mdp:
        for chemin in fichiers:
            try:
                texte = chemin.read_bytes().decode("utf-8", "ignore")
            except OSError:
                continue
            if mdp in texte:
                for numero, ligne in enumerate(texte.splitlines(), start=1):
                    if mdp in ligne:
                        fuites.append((chemin, numero))
            for motif, nom in MOTIFS_ANTIPATTERN:
                for numero, ligne in enumerate(texte.splitlines(), start=1):
                    if motif.search(ligne):
                        antipatrons.append((chemin, numero, nom))

    def _rel(chemin: Path) -> str:
        try:
            return str(chemin.relative_to(racine))
        except ValueError:
            return str(chemin)

    print(f"FUITE total={len(fuites)}")
    for chemin, numero in fuites[:max_findings]:
        print(f"  FUITE {_rel(chemin)}:{numero}")
    if len(fuites) > max_findings:
        print(f"  FUITE ... tronque ({len(fuites) - max_findings} de plus)")
    if fuites:
        fails.append(f"secret hors du fichier de secrets: {len(fuites)} occurrence(s)")

    print(f"ANTIPATTERN total={len(antipatrons)}")
    for chemin, numero, nom in antipatrons[:max_findings]:
        print(f"  ANTIPATTERN {_rel(chemin)}:{numero} {nom}")
    if len(antipatrons) > max_findings:
        print(f"  ANTIPATTERN ... tronque ({len(antipatrons) - max_findings} de plus)")

    for message in avertissements:
        print(f"AVERTISSEMENT {message}")

    if fails:
        for message in fails:
            print(f"FAIL {message}")
        print("RESULT FAIL")
        return 1
    print("RESULT OK")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Audit local en lecture seule du fichier de secrets VPS.")
    p.add_argument("--secrets", type=Path, required=True, help="fichier JSON de secrets")
    p.add_argument("--racine", type=Path, default=None, help="racine a scanner (defaut : parent du parent des secrets)")
    p.add_argument("--max-findings", type=int, default=20, help="nombre de lignes affichees par categorie")
    a = p.parse_args()

    racine = a.racine or (a.secrets.resolve().parent.parent)
    if a.max_findings < 1:
        print("usage: --max-findings doit etre >= 1")
        return 2
    return analyser(a.secrets, racine, a.max_findings)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
