#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verification lecture seule de la mesure Cs-133 geolocalisee et du verrou S19.

Ne modifie aucun fichier. Sortie ASCII. Codes de retour :
  0 = toutes les verifications passent
  1 = echec de verification
  2 = fichier ou dependance manquant
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

ROOT_DEFAUT = Path(r"C:\Users\Administrateur\Desktop\IMAM8MAHDI")
SYSTEME_REL = Path("ASTRO-Q°ODE_SYSTEME")
SNAPSHOT_REL = SYSTEME_REL / "donnees" / "mesure_quantique_cesium_133.json"
SCRIPT_REL = SYSTEME_REL / "outils" / "mesurer_metriques_cesium_133.py"
CSV_REL = Path("TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv")
HTML_REL = Path("TABLEAU_MAITRE_SEQUENTIEL_UNIFIE_IMAM8MAHDI.html")


class Echec(Exception):
    """Echec de verification."""


class Dependance(Echec):
    """Dependance ou fichier indispensable manquant."""


def _ascii(valeur: object) -> str:
    return str(valeur).encode("ascii", "replace").decode("ascii")


def _chemin(valeur: str | None, racine: Path, defaut: Path) -> Path:
    if valeur is None:
        return (racine / defaut).resolve()
    chemin = Path(valeur)
    if not chemin.is_absolute():
        chemin = racine / chemin
    return chemin.resolve()


def _charger(systeme: Path) -> tuple[Any, Any]:
    if not systeme.is_dir():
        raise Dependance(f"systeme introuvable: {systeme}")
    if str(systeme) not in sys.path:
        sys.path.insert(0, str(systeme))
    try:
        from bibliotheques.lib_cesium_133 import (  # type: ignore
            verifier_snapshot_cesium_133,
        )
        from horloge_noyau.architecture_informe_couche_matiere_table_mizan import (  # type: ignore
            confirmer_harmonie_et_prouver_justesse,
        )
    except Exception as exc:
        raise Dependance(
            f"import des modules du systeme: {type(exc).__name__}: {exc}"
        ) from exc
    return verifier_snapshot_cesium_133, confirmer_harmonie_et_prouver_justesse


def _verifier_snapshot(
    verifier: Any, snapshot: Path, script: Path
) -> dict[str, Any]:
    try:
        data = verifier(snapshot, script)
    except Exception as exc:
        raise Echec(f"snapshot: {type(exc).__name__}: {exc}") from exc
    if not isinstance(data, dict):
        raise Echec("snapshot: objet JSON attendu")

    if data.get("schema") != "MESURE_QUANTIQUE_CESIUM_133/v1":
        raise Echec(f"snapshot: schema inattendu {data.get('schema')!r}")
    if data.get("preuve_totale") is not True:
        raise Echec("snapshot: preuve_totale absente ou fausse")

    contenu = data.get("empreinte_contenu_sha256")
    empreinte = data.get("empreinte") or {}
    script_sha = empreinte.get("script_sha256")
    for label, valeur in (("contenu", contenu), ("script", script_sha)):
        if not isinstance(valeur, str) or len(valeur) != 64:
            raise Echec(f"snapshot: hash {label} absent ou invalide")

    validation = data.get("validation_monade") or {}
    architecture = validation.get("architecture") or {}
    couches = architecture.get("couches_ok") or {}
    if len(couches) != 9:
        raise Echec(f"architecture stockee: {len(couches)} couches au lieu de 9")
    if not all(couches.values()):
        manquantes = sorted(
            cle for cle, ok in couches.items() if not ok
        )
        raise Echec(
            "architecture stockee: couches fausses " + ", ".join(manquantes)
        )
    if architecture.get("preuve_ensemble_juste") is not True:
        raise Echec("architecture stockee: preuve_ensemble_juste absente")

    metriques = validation.get("metriques") or {}
    if metriques.get("controles_total") != 23:
        raise Echec(
            "metriques: total de controles inattendu "
            f"{metriques.get('controles_total')!r}"
        )
    if metriques.get("controles_ok") != 23:
        raise Echec(
            "metriques: controles satisfaits "
            f"{metriques.get('controles_ok')!r}/23"
        )
    if metriques.get("monade_juste") is not True:
        raise Echec("metriques: monade_juste absent ou faux")
    if metriques.get("isolee") is not True:
        raise Echec("metriques: monade non isolee")
    if metriques.get("etat_helium") is not False:
        raise Echec("metriques: monade en etat HELIUM")
    if metriques.get("valeur_finale") != "SCEAU_MONADE_CS133":
        raise Echec(
            "metriques: jeton final inattendu "
            f"{metriques.get('valeur_finale')!r}"
        )
    return data


def _verifier_architecture_live(confirmer: Any) -> tuple[int, int]:
    try:
        verdict = confirmer()
    except Exception as exc:
        raise Echec(
            f"architecture live: {type(exc).__name__}: {exc}"
        ) from exc
    couches = getattr(verdict, "couches_ok", {}) or {}
    total = len(couches)
    ok = sum(1 for valeur in couches.values() if valeur)
    if total != 9:
        raise Echec(f"architecture live: {total} couches au lieu de 9")
    if ok != total:
        manquantes = sorted(cle for cle, val in couches.items() if not val)
        raise Echec(
            "architecture live: couches fausses " + ", ".join(manquantes)
        )
    if not getattr(verdict, "confirmer_harmonie", False):
        raise Echec("architecture live: harmonie non confirmee")
    if not getattr(verdict, "monade_juste", False):
        raise Echec("architecture live: monade non juste")
    if not getattr(verdict, "preuve_ensemble_juste", False):
        raise Echec("architecture live: preuve d'ensemble absente")
    return ok, total


def _verifier_s19(
    data: dict[str, Any], csv_path: Path, html_path: Path
) -> tuple[int, int, int, int]:
    for label, chemin in (("CSV", csv_path), ("HTML", html_path)):
        if not chemin.is_file():
            raise Dependance(f"{label} introuvable: {chemin}")
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as fichier:
            lecteur = csv.DictReader(fichier, delimiter=";")
            champs = list(lecteur.fieldnames or [])
            lignes = list(lecteur)
    except Exception as exc:
        raise Echec(f"CSV: {type(exc).__name__}: {exc}") from exc

    requis = {"STRATE", "CODE", "SEQ", "SOURCE", "VALEUR_SCELLEE"}
    manquants = requis - set(champs)
    if manquants:
        raise Echec(
            "CSV: colonnes manquantes " + ", ".join(sorted(manquants))
        )

    s19 = [
        ligne
        for ligne in lignes
        if str(ligne.get("STRATE") or "").startswith("S19")
    ]
    if len(s19) != 19:
        raise Echec(f"S19: {len(s19)} lignes au lieu de 19")

    codes = [str(ligne.get("CODE") or "") for ligne in s19]
    attendus = [f"CS-{index:02d}" for index in range(1, 20)]
    if codes != attendus:
        raise Echec("S19: codes inattendus " + ", ".join(codes))

    try:
        sequences = [int(str(ligne.get("SEQ") or "")) for ligne in s19]
    except ValueError as exc:
        raise Echec(f"S19: SEQ non entiere ({exc})") from exc
    if sequences != list(range(sequences[0], sequences[0] + 19)):
        raise Echec("S19: SEQ non contigues " + str(sequences))

    hash_contenu = data["empreinte_contenu_sha256"][:16]
    hash_script = data["empreinte"]["script_sha256"][:16]
    for ligne in s19:
        if hash_contenu not in str(ligne.get("SOURCE") or ""):
            raise Echec(
                f"S19 {ligne.get('CODE')}: SOURCE sans le hash de snapshot courant"
            )
    if hash_script not in str(s19[-1].get("SOURCE") or ""):
        raise Echec("S19 CS-19: SOURCE sans le hash du script courant")

    if "PREUVE ARCHITECTURE = 9/9" not in str(
        s19[-2].get("VALEUR_SCELLEE") or ""
    ):
        raise Echec("S19 CS-18: preuve d'architecture 9/9 absente")
    dernier = str(s19[-1].get("VALEUR_SCELLEE") or "")
    for attendu in ("PREUVE TOTALE = true", "SCEAU_MONADE_CS133"):
        if attendu not in dernier:
            raise Echec(f"S19 CS-19: '{attendu}' absent")

    try:
        html = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise Echec(f"HTML: {type(exc).__name__}: {exc}") from exc
    if "S19" not in html or "CS-19" not in html:
        raise Echec("HTML: marqueurs S19/CS-19 absents")

    strates = {str(ligne.get("STRATE") or "") for ligne in lignes}
    return len(lignes), len(strates), sequences[0], sequences[-1]


def _afficher(
    data: dict[str, Any],
    snapshot: Path,
    live: tuple[int, int],
    table: tuple[int, int, int, int] | None,
) -> None:
    metriques = data.get("metriques") or {}
    position = metriques.get("position") or {}
    temps = data.get("temps") or {}
    validation = data.get("validation_monade") or {}
    architecture = validation.get("architecture") or {}
    couches = architecture.get("couches_ok") or {}
    met = validation.get("metriques") or {}

    latitude = float(position.get("latitude_deg"))
    longitude = float(position.get("longitude_deg"))
    altitude = float(position.get("altitude_m"))
    ecart = float(position.get("altitude_spread_m") or 0.0)
    precision_m = float(position.get("horizontal_accuracy_m") or 0.0)
    latitude_dir = "N" if latitude >= 0.0 else "S"
    longitude_dir = "E" if longitude >= 0.0 else "W"

    precision_s = temps.get("precision_windows_s")
    if (
        isinstance(precision_s, (int, float))
        and not isinstance(precision_s, bool)
        and precision_s > 0.0
    ):
        precision_txt = f"{float(precision_s) * 1e9:.3f} ns"
    else:
        precision_txt = "absente"

    stockees_ok = sum(1 for valeur in couches.values() if valeur)
    print("OK - mesure Cs-133 verifiee")
    print(f"snapshot {_ascii(snapshot)}")
    print(
        "contenu "
        f"{data['empreinte_contenu_sha256'][:16]}... | script "
        f"{data['empreinte']['script_sha256'][:16]}..."
    )
    print(
        f"preuve_totale {data.get('preuve_totale')} | "
        f"Monade metriques {met.get('controles_ok')}/{met.get('controles_total')} | "
        f"architecture stockee {stockees_ok}/{len(couches)} | "
        f"architecture live {live[0]}/{live[1]}"
    )
    print(
        f"position {abs(latitude):.5f} {latitude_dir} "
        f"{abs(longitude):.5f} {longitude_dir} +/-{precision_m:.0f} m | "
        f"altitude {altitude:.1f} m (ecart SRTM {ecart:.1f} m)"
    )
    print(
        f"temps {temps.get('utc', 'n/a')} | {temps.get('fuseau', 'n/a')} | "
        f"w32tm {precision_txt}"
    )
    if table is None:
        print("tableau non verifie (--snapshot-only)")
    else:
        print(
            f"tableau {table[0]} entrees / {table[1]} strates | "
            f"S19 19 lignes CS-01..CS-19 | SEQ {table[2]}-{table[3]}"
        )
        print("HTML present | marqueurs S19/CS-19 presents")
    print(f"limites {len(data.get('limites') or [])} (voir le snapshot)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verification lecture seule de la mesure Cs-133 geolocalisee "
            "et du verrou S19."
        )
    )
    parser.add_argument("--root", default=str(ROOT_DEFAUT))
    parser.add_argument("--snapshot")
    parser.add_argument("--script")
    parser.add_argument("--csv")
    parser.add_argument("--html")
    parser.add_argument(
        "--snapshot-only",
        action="store_true",
        help="verifie le snapshot et la Monade, sans CSV ni HTML",
    )
    args = parser.parse_args(argv)

    racine = Path(args.root).expanduser().resolve()
    systeme = racine / SYSTEME_REL
    snapshot = _chemin(args.snapshot, racine, SNAPSHOT_REL)
    script = _chemin(args.script, racine, SCRIPT_REL)
    csv_path = _chemin(args.csv, racine, CSV_REL)
    html_path = _chemin(args.html, racine, HTML_REL)

    for label, chemin in (("snapshot", snapshot), ("script", script)):
        if not chemin.is_file():
            print(f"[FAIL] {label} introuvable: {_ascii(chemin)}")
            return 2
    if not args.snapshot_only:
        for label, chemin in (("CSV", csv_path), ("HTML", html_path)):
            if not chemin.is_file():
                print(f"[FAIL] {label} introuvable: {_ascii(chemin)}")
                return 2

    try:
        verifier, confirmer = _charger(systeme)
    except Dependance as exc:
        print(f"[FAIL] {_ascii(exc)}")
        return 2

    try:
        data = _verifier_snapshot(verifier, snapshot, script)
        live = _verifier_architecture_live(confirmer)
        table = None
        if not args.snapshot_only:
            table = _verifier_s19(data, csv_path, html_path)
    except Echec as exc:
        print(f"[FAIL] {_ascii(exc)}")
        return 1
    except Exception as exc:
        print(f"[FAIL] {type(exc).__name__}: {_ascii(exc)}")
        return 1

    try:
        _afficher(data, snapshot, live, table)
    except Exception as exc:
        print(f"[FAIL] affichage: {type(exc).__name__}: {_ascii(exc)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
