#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validateur en lecture seule du tableau maitre sequentiel unifie.

Sortie stdout en ASCII pur (console Windows cp1252).
Code retour 0 si aucun echec dur, 1 sinon.
"""

from __future__ import annotations

import argparse
import ast
import csv
import importlib.util
import json
import re
import sys
from collections import defaultdict
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

DEFAULT_ROOT = Path(r"C:\Users\Administrateur\Desktop\IMAM8MAHDI")
CSV_NAME = "TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv"
HTML_NAME = "TABLEAU_MAITRE_SEQUENTIEL_UNIFIE_IMAM8MAHDI.html"
GEN_REL = Path("ASTRO-Q°ODE_SYSTEME") / "generer_tableau_maitre_sequentiel.py"
LIB_REL = Path("ASTRO-Q°ODE_SYSTEME") / "bibliotheques" / "lib_physique.py"
LOCK_REL = Path("ASTRO-Q°ODE_SYSTEME") / "horloge_noyau" / "VERROU.json"

COLONNES = [
    "SEQ",
    "STRATE",
    "CODE",
    "FAMILLE_LOGIQUE",
    "ELEMENT",
    "ROLE_DESCRIPTION",
    "INTERACTION_MATIERE",
    "CYCLE_TERRE",
    "CYCLE_LUNE",
    "CYCLE_SOLEIL",
    "COUCHE_QUANTIQUE_BIO",
    "VALEUR_SCELLEE",
    "SOURCE",
]

EXPECTED_MAGNITUDES = {"40": 40, "313": 313, "63": 63}
EXPECTED_COUNTS = {"40": 4, "313": 7, "63": 9}
S6_ORIGIN_CODE = "ÉT-S-00"
DOC_RANGE_RE = re.compile("SEQ\\s+001\\s*[-\u2013]\\s*(\\d+)")
DATE_RE = re.compile(r"Généré le (\d{4}-\d{2}-\d{2})")


def _safe(value: object) -> str:
    return str(value).encode("ascii", "replace").decode("ascii")


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def ok(self, label: str, detail: str = "") -> None:
        print("[OK] " + _safe(label) + ((" : " + _safe(detail)) if detail else ""))

    def warn(self, label: str, detail: str = "") -> None:
        self.warnings.append(label + ((" : " + detail) if detail else ""))
        print("[WARN] " + _safe(label) + ((" : " + _safe(detail)) if detail else ""))

    def fail(self, label: str, detail: str = "") -> None:
        self.failures.append(label + ((" : " + detail) if detail else ""))
        print("[FAIL] " + _safe(label) + ((" : " + _safe(detail)) if detail else ""))


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_tbody = False
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None
        self.rows: list[list[str]] = []
        self.badges = 0
        self.th = 0
        self.option_values: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.current_row = []
        elif tag == "td" and self.current_row is not None:
            self.current_cell = []
        elif tag == "th":
            self.th += 1
        elif tag == "span" and "badge" in attributes.get("class", "").split():
            self.badges += 1
        elif tag == "option":
            self.option_values.append(attributes.get("value", ""))
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self.current_cell is not None:
            if self.current_row is not None:
                self.current_row.append("".join(self.current_cell))
            self.current_cell = None
        elif tag == "tr" and self.current_row is not None:
            self.rows.append(self.current_row)
            self.current_row = None
        elif tag == "tbody":
            self.in_tbody = False
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self.current_cell is not None:
            self.current_cell.append(data)
        if self._in_title:
            self.title += data


def _normalize(value: object) -> str:
    return " ".join(str(value).split())


def _load_csv(path: Path, report: Report) -> list[dict[str, str]] | None:
    raw = path.read_bytes()
    if not raw.startswith(b"\xef\xbb\xbf"):
        report.fail("CSV BOM", "BOM UTF-8 absent (attendu EF BB BF)")
    else:
        report.ok("CSV BOM", "UTF-8 BOM present")

    first_line = raw.split(b"\n", 1)[0].rstrip(b"\r").decode("utf-8-sig")
    if ";" not in first_line:
        report.fail("CSV separateur", "point-virgule absent de l'en-tete")
    elif "," in first_line:
        report.fail("CSV separateur", "virgule presente dans l'en-tete")
    else:
        report.ok("CSV separateur", "point-virgule, sans virgule")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        fields = reader.fieldnames
        if fields != COLONNES:
            report.fail(
                "CSV colonnes",
                f"attendu {len(COLONNES)}, observe {len(fields) if fields else 0}",
            )
            return None
        rows = list(reader)

    if not rows:
        report.fail("CSV contenu", "aucune ligne de donnees")
        return None
    if any(None in row for row in rows):
        report.fail("CSV colonnes", "au moins une ligne a un nombre de champs incorrect")
        return None

    report.ok("CSV colonnes", f"13 colonnes, {len(rows)} lignes")

    missing_core = []
    for row in rows:
        for column in ("SEQ", "STRATE", "CODE", "ELEMENT", "ROLE_DESCRIPTION", "SOURCE"):
            if not (row.get(column) or "").strip():
                missing_core.append((row.get("SEQ", "?"), column))
    if missing_core:
        report.fail(
            "CSV champs obligatoires",
            f"{len(missing_core)} cellule(s) vide(s), ex. {missing_core[0]}",
        )

    expected_seq = [f"{index:03d}" for index in range(1, len(rows) + 1)]
    observed_seq = [row["SEQ"] for row in rows]
    if observed_seq != expected_seq:
        first = next(
            (
                index
                for index, (observed, expected) in enumerate(
                    zip(observed_seq, expected_seq), 1
                )
                if observed != expected
            ),
            min(len(observed_seq), len(expected_seq)) + 1,
        )
        observed_value = observed_seq[first - 1] if first <= len(observed_seq) else "absent"
        expected_value = expected_seq[first - 1] if first <= len(expected_seq) else "absent"
        report.fail(
            "SEQ continue",
            f"premier ecart ligne {first}: observe {observed_value}, attendu {expected_value}",
        )
    else:
        report.ok("SEQ continue", f"001-{len(rows):03d}")

    strata: list[str] = []
    closed: set[str] = set()
    previous: str | None = None
    contiguous = True
    for row in rows:
        current = row["STRATE"]
        if current != previous:
            if current in closed:
                report.fail(
                    "Strates contigues",
                    f"strate {current} reapparait apres un autre bloc",
                )
                contiguous = False
            if previous is not None:
                closed.add(previous)
            strata.append(current)
            previous = current
    if contiguous:
        report.ok("Strates contigues", f"{len(strata)} blocs")

    return rows


def _load_expected_s6(lib_path: Path, report: Report) -> dict[str, list[int]] | None:
    if not lib_path.is_file():
        report.fail("lib_physique", f"absent: {lib_path}")
        return None
    try:
        spec = importlib.util.spec_from_file_location(
            "lib_physique_tableau_validator", lib_path
        )
        if spec is None or spec.loader is None:
            raise ImportError("specification importable introuvable")
        module = importlib.util.module_from_spec(spec)
        # dataclasses resout __module__ via sys.modules pendant l'execution.
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        repartir = getattr(module, "_repartir_somme_unique")
    except Exception as exc:
        report.fail("lib_physique import", f"{type(exc).__name__}: {exc}")
        return None
    try:
        return {
            "40": list(repartir(4 * 10, 4)),
            "313": list(repartir(3 * 100, 3))
            + list(repartir(1 * 10, 1))
            + list(repartir(3 * 1, 3)),
            "63": list(repartir(6 * 10, 6)) + list(repartir(3 * 1, 3)),
        }
    except Exception as exc:
        report.fail("lib_physique calcul", f"{type(exc).__name__}: {exc}")
        return None


def _check_s6(rows: list[dict[str, str]], lib_path: Path, report: Report) -> None:
    s6 = [row for row in rows if row["STRATE"].startswith("S6")]
    if not s6:
        report.fail("S6", "aucune ligne S6")
        return

    observed: dict[str, list[int]] = defaultdict(list)
    state_observed: dict[str, list[int]] = defaultdict(list)
    origin_value: int | None = None
    origin_magnitude: str | None = None
    for row in s6:
        match = re.search(r"/\s*magnitude\s+(\d+)\s*$", row["VALEUR_SCELLEE"])
        if not match:
            report.fail("S6 format", f"SEQ {row['SEQ']}: {row['VALEUR_SCELLEE']}")
            return
        try:
            value = int(row["VALEUR_SCELLEE"].split(" ", 1)[0])
        except ValueError:
            report.fail("S6 valeur", f"SEQ {row['SEQ']}: {row['VALEUR_SCELLEE']}")
            return
        magnitude = match.group(1)
        observed[magnitude].append(value)
        if row["CODE"] == S6_ORIGIN_CODE:
            if origin_value is not None:
                report.fail("S6 origine", f"{S6_ORIGIN_CODE} apparait plusieurs fois")
            origin_value = value
            origin_magnitude = magnitude
        else:
            state_observed[magnitude].append(value)

    if origin_value is None:
        report.fail("S6 origine", f"ligne {S6_ORIGIN_CODE} absente")
    elif origin_magnitude != "40":
        report.fail(
            "S6 origine",
            f"{S6_ORIGIN_CODE} magnitude {origin_magnitude}, attendu 40",
        )
    elif origin_value != 0:
        report.fail("S6 origine", f"{S6_ORIGIN_CODE} valeur {origin_value}, attendu 0")
    else:
        report.ok("S6 origine", f"{S6_ORIGIN_CODE} = 0 (hors 4 etats)")

    sums = {magnitude: sum(values) for magnitude, values in observed.items()}
    if sums != EXPECTED_MAGNITUDES:
        report.fail("S6 sommes", f"observe {sums}, attendu {EXPECTED_MAGNITUDES}")
    else:
        report.ok("S6 sommes", "40/313/63")

    expected = _load_expected_s6(lib_path, report)
    if expected is None:
        return
    for magnitude in EXPECTED_MAGNITUDES:
        got = sorted(state_observed.get(magnitude, []))
        want = sorted(expected[magnitude])
        if got != want:
            report.fail(
                "S6 distribution",
                f"magnitude {magnitude}: observe {got}, attendu {want}",
            )
        else:
            report.ok(
                "S6 distribution",
                f"magnitude {magnitude} identique a lib_physique ({len(want)} valeurs)",
            )

    counts = {magnitude: len(values) for magnitude, values in state_observed.items()}
    if any(counts.get(magnitude, 0) != count for magnitude, count in EXPECTED_COUNTS.items()):
        report.fail(
            "S6 comptes",
            f"observe {counts}, attendu {EXPECTED_COUNTS} (+ origine 0)",
        )
    else:
        report.ok("S6 comptes", "4/7/9 + origine 0")
    report.ok(
        "S6 lignes",
        f"{len(s6)} lignes, etats 40/313/63 = "
        f"{counts.get('40', 0)}/{counts.get('313', 0)}/{counts.get('63', 0)} + origine",
    )


def _check_generator(path: Path, rows: list[dict[str, str]], report: Report) -> None:
    if not path.is_file():
        report.fail("Generateur", f"absent: {path}")
        return
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as exc:
        report.fail("Generateur lecture", f"{type(exc).__name__}: {exc}")
        return

    assignments: dict[str, ast.expr] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            assignments[node.targets[0].id] = node.value

    colonnes_node = assignments.get("COLONNES")
    if colonnes_node is None:
        report.fail("Generateur COLONNES", "affectation introuvable")
    else:
        try:
            columns = ast.literal_eval(colonnes_node)
        except Exception:
            report.fail("Generateur COLONNES", "valeur non litterale")
        else:
            if columns != COLONNES:
                report.fail(
                    "Generateur COLONNES",
                    f"observe {len(columns)} colonnes, attendu {len(COLONNES)}",
                )
            else:
                report.ok("Generateur COLONNES", "13 colonnes identiques")

    functions = {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    for name in ("add", "_repartir_somme_unique"):
        if name in functions:
            report.ok("Generateur fonction", name)
        else:
            report.fail("Generateur fonction", f"{name} absente")

    strata = list(dict.fromkeys(row["STRATE"] for row in rows))
    color_node = assignments.get("COULEURS_STRATE")
    if color_node is None:
        report.warn("Generateur couleurs", "COULEURS_STRATE introuvable")
    else:
        try:
            colors = ast.literal_eval(color_node)
        except Exception:
            report.warn("Generateur couleurs", "COULEURS_STRATE non litterale")
        else:
            missing = [stratum for stratum in strata if stratum not in colors]
            if missing:
                labels = [stratum.split("·")[0].strip() for stratum in missing]
                report.warn(
                    "Generateur couleurs",
                    f"{len(missing)} strate(s) sans couleur explicite: "
                    + ", ".join(labels[:8])
                    + (", ..." if len(labels) > 8 else ""),
                )
            else:
                report.ok("Generateur couleurs", f"{len(strata)} strates couvertes")

    docstring = ast.get_docstring(tree) or ""
    match = DOC_RANGE_RE.search(docstring)
    if match and int(match.group(1)) != len(rows):
        report.warn(
            "Generateur docstring",
            f"SEQ 001-{match.group(1)} alors que N={len(rows)}",
        )
    elif match:
        report.ok("Generateur docstring", f"plage SEQ 001-{len(rows)}")

    hardcoded: list[str] = []
    for name, index in (("MATIERE_14", 4), ("TERRE_EXTRA", 3), ("LUNE_EXTRA", 3)):
        node = assignments.get(name)
        if not isinstance(node, (ast.List, ast.Tuple)):
            continue
        for element in node.elts:
            if not isinstance(element, ast.Tuple) or len(element.elts) <= index:
                continue
            value = element.elts[index]
            if (
                isinstance(value, ast.Constant)
                and isinstance(value.value, int)
                and value.value != 0
            ):
                hardcoded.append(name)
                break
    if hardcoded:
        report.warn(
            "Generateur valeurs en dur",
            ", ".join(sorted(set(hardcoded)))
            + " contiennent des entiers litteraux non nuls",
        )
    else:
        report.ok(
            "Generateur valeurs derivees",
            "aucun entier litteral non nul dans les tables d'etats",
        )


def _check_lock(path: Path, report: Report) -> None:
    if not path.is_file():
        report.fail("A137", f"absent: {path}")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        report.fail("A137 lecture", f"{type(exc).__name__}: {exc}")
        return

    ok = True
    if data.get("verrouille") is not True:
        report.fail("A137 verrou", "verrouille != true")
        ok = False
    for key in ("ecriture", "modification", "troncature"):
        if data.get(key) is not False:
            report.fail("A137 politique", f"{key} != false")
            ok = False
    if ok:
        report.ok("A137", "lecture/execution autorisees, ecriture interdite")


def _check_html(path: Path, rows: list[dict[str, str]], report: Report) -> None:
    if not path.is_file():
        report.fail("HTML", f"absent: {path}")
        return
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        report.fail("HTML lecture", f"{type(exc).__name__}: {exc}")
        return

    parser = TableParser()
    parser.feed(text)
    strata = list(dict.fromkeys(row["STRATE"] for row in rows))

    if len(parser.rows) != len(rows):
        report.fail("HTML lignes", f"observe {len(parser.rows)}, attendu {len(rows)}")
    else:
        report.ok("HTML lignes", str(len(rows)))

    bad_shape = [
        index
        for index, row in enumerate(parser.rows, 1)
        if len(row) != len(COLONNES)
    ]
    if bad_shape:
        report.fail(
            "HTML cellules",
            f"lignes avec != 13 cellules: {bad_shape[:5]}",
        )
    else:
        report.ok("HTML cellules", "13 cellules par ligne")

    mismatches: list[tuple[int, str]] = []
    if len(parser.rows) == len(rows) and not bad_shape:
        for row_index, (html_row, csv_row) in enumerate(zip(parser.rows, rows), 1):
            for column_index, column in enumerate(COLONNES):
                if _normalize(html_row[column_index]) != _normalize(csv_row[column]):
                    mismatches.append((row_index, column))
                    if len(mismatches) >= 5:
                        break
            if len(mismatches) >= 5:
                break
    if mismatches:
        report.fail(
            "HTML contenu",
            "premiers ecarts (ligne, colonne): "
            + ", ".join(f"({index},{column})" for index, column in mismatches),
        )
    elif len(parser.rows) == len(rows) and not bad_shape:
        report.ok("HTML contenu", "identique au CSV, toutes cellules")

    if parser.th != len(COLONNES):
        report.fail(
            "HTML en-tete",
            f"observe {parser.th} th, attendu {len(COLONNES)}",
        )
    else:
        report.ok("HTML en-tete", "13 colonnes")

    if parser.badges != len(strata):
        report.fail("HTML badges", f"observe {parser.badges}, attendu {len(strata)}")
    else:
        report.ok("HTML badges", str(len(strata)))

    option_values = {value for value in parser.option_values if value}
    if len(parser.option_values) != len(strata) + 1:
        report.fail(
            "HTML options",
            f"observe {len(parser.option_values)}, attendu {len(strata) + 1} "
            "(placeholder inclus)",
        )
    elif option_values != set(strata):
        missing = sorted(set(strata) - option_values)
        extra = sorted(option_values - set(strata))
        report.fail(
            "HTML options",
            f"valeurs manquantes={missing[:3]}, extra={extra[:3]}",
        )
    else:
        report.ok("HTML options", f"{len(strata)} strates + placeholder")

    if "TABLEAU MAÎTRE SÉQUENTIEL UNIFIÉ" not in parser.title:
        report.fail("HTML titre", "titre attendu absent")
    else:
        report.ok("HTML titre", "TABLEAU MAITRE SEQUENTIEL UNIFIE")

    if parser.rows and parser.rows[-1]:
        last_seq = _normalize(parser.rows[-1][0])
        expected_seq = f"{len(rows):03d}"
        if last_seq != expected_seq:
            report.fail(
                "HTML derniere SEQ",
                f"observe {last_seq}, attendu {expected_seq}",
            )
        else:
            report.ok("HTML derniere SEQ", last_seq)

    match = DATE_RE.search(text)
    if not match:
        report.warn("HTML date", "date de generation introuvable")
    elif match.group(1) != date.today().isoformat():
        report.warn(
            "HTML date",
            f"date {match.group(1)} != aujourd'hui {date.today().isoformat()}",
        )
    else:
        report.ok("HTML date", match.group(1))


def validate(root: Path, report: Report) -> None:
    csv_path = root / CSV_NAME
    html_path = root / HTML_NAME
    gen_path = root / GEN_REL
    lib_path = root / LIB_REL
    lock_path = root / LOCK_REL

    for label, path in (("CSV", csv_path), ("HTML", html_path)):
        if not path.is_file():
            report.fail(label, f"absent: {path}")
    if not csv_path.is_file() or not html_path.is_file():
        return

    rows = _load_csv(csv_path, report)
    if rows is None:
        return

    _check_s6(rows, lib_path, report)
    _check_generator(gen_path, rows, report)
    _check_lock(lock_path, report)
    _check_html(html_path, rows, report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Valider le tableau maitre sequentiel unifie (lecture seule)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Racine du depot IMAM8MAHDI",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Traiter les avertissements comme des echecs",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Afficher la trace en cas d'erreur inattendue",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    print("== TABLEAU MAITRE SEQUENTIEL - VALIDATION (lecture seule) ==")
    print("ROOT: " + _safe(root))

    report = Report()
    try:
        validate(root, report)
    except Exception as exc:
        report.fail("Execution", f"{type(exc).__name__}: {exc}")
        if args.debug:
            import traceback

            traceback.print_exc()

    print("")
    if report.failures:
        print(
            f"RESULT: FAIL ({len(report.failures)} echec(s), "
            f"{len(report.warnings)} avertissement(s))"
        )
        return 1
    if args.strict and report.warnings:
        print(f"RESULT: FAIL strict ({len(report.warnings)} avertissement(s))")
        return 1
    print(f"RESULT: OK ({len(report.warnings)} avertissement(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
