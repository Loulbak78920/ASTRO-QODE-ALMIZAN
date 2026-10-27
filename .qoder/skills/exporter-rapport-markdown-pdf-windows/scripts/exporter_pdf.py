#!/usr/bin/env python3
"""Exporte un HTML local en PDF via Chrome headless, puis verifie le PDF.

Usage : py -3 -B exporter_pdf.py <entree.html> <sortie.pdf>
        [--chrome CHEMIN] [--min-chars N] [--timeout S]
Codes : 0 = PASS, 1 = verification en echec, 2 = usage ou environnement.
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

PAGE_OBJ = re.compile(rb"/Type\s*/Page\b")
COUNT = re.compile(rb"/Count\s+(\d+)")


def ascii_sur(valeur: object) -> str:
    return str(valeur).encode("ascii", "backslashreplace").decode("ascii")


def candidats_chrome() -> list[Path]:
    vus: list[Path] = []
    for variable in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(variable)
        if base:
            vus.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
    if os.name == "nt":
        try:
            import winreg

            sous_cle = (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
            )
            for ruche in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for vue in (0, winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
                    try:
                        with winreg.OpenKey(
                            ruche, sous_cle, 0, winreg.KEY_READ | vue
                        ) as cle:
                            chemin, _ = winreg.QueryValueEx(cle, None)
                    except OSError:
                        continue
                    if chemin:
                        vus.append(Path(str(chemin).strip('"')))
        except ImportError:
            pass
    uniques: list[Path] = []
    for chemin in vus:
        if chemin not in uniques:
            uniques.append(chemin)
    return uniques


def trouver_chrome(explicite: str | None) -> Path | None:
    if explicite:
        chemin = Path(explicite)
        return chemin if chemin.is_file() else None
    for chemin in candidats_chrome():
        if chemin.is_file():
            return chemin
    return None


def exporter(chrome: Path, html: Path, pdf: Path, timeout: int) -> tuple[int, str]:
    commande = [
        str(chrome),
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf}",
        html.as_uri(),
    ]
    try:
        resultat = subprocess.run(
            commande, capture_output=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    except OSError as exc:
        return 2, str(exc)
    sortie = (resultat.stderr or b"").decode("utf-8", "replace").strip()
    return resultat.returncode, sortie


def verifier(pdf: Path, min_chars: int) -> tuple[bool, dict[str, int], list[str]]:
    donnees = pdf.read_bytes()
    anomalies: list[str] = []
    entete = donnees[:8].decode("ascii", "replace")
    if not donnees.startswith(b"%PDF-"):
        anomalies.append("entete")
    if b"%%EOF" not in donnees[-2048:]:
        anomalies.append("queue")
    pages_obj = len(PAGE_OBJ.findall(donnees))
    compteurs = [int(v) for v in COUNT.findall(donnees)]
    mesures = {
        "octets": len(donnees),
        "entete": entete,
        "queue_eof": int(b"%%EOF" in donnees[-2048:]),
        "pages_obj": pages_obj,
        "count": compteurs[0] if compteurs else -1,
        "pages_pypdf": -1,
        "chars_p1": -1,
    }
    if len(donnees) < 1000:
        anomalies.append("taille")

    try:
        import pypdf
    except ImportError:
        anomalies.append("pypdf_absent")
        return False, mesures, anomalies

    logging.getLogger("pypdf").setLevel(logging.ERROR)
    try:
        lecteur = pypdf.PdfReader(str(pdf))
        mesures["pages_pypdf"] = len(lecteur.pages)
        if lecteur.pages:
            texte = lecteur.pages[0].extract_text() or ""
            mesures["chars_p1"] = len(texte.strip())
    except Exception:
        anomalies.append("pypdf_lecture")
        return False, mesures, anomalies

    if mesures["pages_pypdf"] < 1:
        anomalies.append("aucune_page")
    if mesures["chars_p1"] < min_chars:
        anomalies.append("texte_insuffisant")
    return not anomalies, mesures, anomalies


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("entree", type=Path)
    analyseur.add_argument("sortie", type=Path)
    analyseur.add_argument("--chrome", default=None)
    analyseur.add_argument("--min-chars", type=int, default=1)
    analyseur.add_argument("--timeout", type=int, default=180)
    args = analyseur.parse_args()

    if not args.entree.is_file():
        print(f"ERROR html_absent={ascii_sur(args.entree)}")
        return 2
    chrome = trouver_chrome(args.chrome)
    if chrome is None:
        print("ERROR chrome_introuvable=1")
        return 2

    pdf = args.sortie
    try:
        pdf.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR dossier_sortie={ascii_sur(exc)}")
        return 2
    if pdf.exists():
        print("OVERWRITE=1")
        try:
            pdf.unlink()
        except OSError as exc:
            print(f"ERROR suppression={ascii_sur(exc)}")
            return 2

    code, trace = exporter(chrome, args.entree.resolve(), pdf.resolve(), args.timeout)
    print(f"CHROME={ascii_sur(chrome)}")
    print(f"PDF={ascii_sur(pdf)}")
    print(f"CHROME_RC={code}")
    if code != 0 or not pdf.is_file():
        if trace:
            print(f"CHROME_STDERR={ascii_sur(trace[-400:])}")
        print("RESULT=FAIL")
        return 1

    ok, mesures, anomalies = verifier(pdf, args.min_chars)
    print(f"PDF_BYTES={mesures['octets']}")
    print(f"HEADER={ascii_sur(mesures['entete'])}")
    print(f"TAIL_EOF={mesures['queue_eof']}")
    print(f"PAGE_OBJ={mesures['pages_obj']}")
    print(f"COUNT={mesures['count']}")
    if "pypdf_absent" in anomalies:
        print("ERROR pypdf=absent (installer pypdf)")
        print("RESULT=FAIL")
        return 2
    print(f"PYPDF_PAGES={mesures['pages_pypdf']}")
    print(f"P1_CHARS={mesures['chars_p1']}")
    if anomalies:
        print("ANOMALIES=" + ",".join(anomalies))
        print("RESULT=FAIL")
        return 1
    print("RESULT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
