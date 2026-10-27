#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only validator for the IMAM8MAHDI master sequential table.

Exit codes:
  0 = no hard failure (warnings allowed unless --strict-warnings)
  1 = contract violation
  2 = missing or unreadable input file

Console output is ASCII only (Windows cp1252). Checked files stay UTF-8.
"""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import re
import sys
from collections import defaultdict
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable

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
CORE_COLUMNS = (
    "SEQ",
    "STRATE",
    "CODE",
    "FAMILLE_LOGIQUE",
    "ELEMENT",
    "ROLE_DESCRIPTION",
    "VALEUR_SCELLEE",
    "SOURCE",
)
ADD_PARAMS = [
    "strate",
    "code",
    "famille",
    "element",
    "role",
    "matiere",
    "terre",
    "lune",
    "soleil",
    "quantique_bio",
    "valeur",
    "source",
]
MAGNITUDE_SUM = {"40": 40, "313": 313, "63": 63}
MAGNITUDE_COUNT = {"40": 4, "313": 7, "63": 9}
MAGNITUDE_BY_CODE = (("ÉT-S", "40"), ("ÉT-T", "313"), ("ÉT-L", "63"))
S6_ORIGIN_CODE = "ÉT-S-00"
DOC_RANGE_RE = re.compile(r"SEQ\s+001\s*[–-]\s*(\d+)")
DATE_RE = re.compile(r"Généré le (\d{4}-\d{2}-\d{2})")
SUBTITLE_RE = re.compile(
    r"Séquence stricte\s+001\s*[–-]\s*(\d+)\s*·\s*(\d+)\s+strates"
)
STRATE_RE = re.compile(r"^S(\d+)\s*·\s*\S")
MAGNITUDE_RE = re.compile(r"/\s*magnitude\s+(\d+)\s*$")
RESOURCE_TAG_RE = re.compile(
    r"<(script|link|img|iframe|source|video|audio|embed|object|base|"
    r"input|track|use|image)\b([^>]*)>",
    re.I | re.S,
)
RESOURCE_ATTR_RE = re.compile(
    r"\b(src|href|data|srcset|poster|style)\s*=\s*([\"'])(.*?)\2",
    re.I | re.S,
)
STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.I | re.S)
STYLE_ATTR_RE = re.compile(r"\bstyle\s*=\s*([\"'])(.*?)\1", re.I | re.S)
CSS_IMPORT_RE = re.compile(r"@import\b[^;{}]*", re.I)
CSS_URL_RE = re.compile(r"url\(\s*([\"']?)(.*?)\1\s*\)", re.I | re.S)


class InputError(RuntimeError):
    pass


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


class MasterTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_master = False
        self.in_tbody = False
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None
        self.rows: list[list[str]] = []
        self.badges = 0
        self.th = 0
        self.option_values: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and attributes.get("id") == "master":
            self.in_master = True
        elif tag == "tbody" and self.in_master:
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.current_row = []
        elif tag == "td" and self.current_row is not None:
            self.current_cell = []
        elif tag == "th" and self.in_master:
            self.th += 1
        elif tag == "span" and "badge" in (attributes.get("class") or "").split():
            self.badges += 1
        elif tag == "option":
            self.option_values.append(attributes.get("value") or "")
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
        elif tag == "tbody" and self.in_master:
            self.in_tbody = False
        elif tag == "table" and self.in_master:
            self.in_master = False
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


def _strate_number(label: str) -> int | None:
    match = STRATE_RE.match(label)
    return int(match.group(1)) if match else None


def _resolve(value: Path | None, root: Path, default: Path) -> Path:
    if value is None:
        return (root / default).resolve()
    return (value if value.is_absolute() else root / value).resolve()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"{path}: {exc}") from exc


def _require_inputs(paths: dict[str, Path]) -> None:
    missing = [f"{label}={path}" for label, path in paths.items() if not path.is_file()]
    if missing:
        raise InputError("fichier(s) absent(s): " + ", ".join(missing))


def _extract_function(path: Path, name: str) -> Callable[..., Any]:
    tree = ast.parse(_read_text(path))
    node = next(
        (
            item
            for item in tree.body
            if isinstance(item, ast.FunctionDef) and item.name == name
        ),
        None,
    )
    if node is None:
        raise LookupError(f"fonction {name} introuvable")
    header = ast.parse(
        "from __future__ import annotations\n"
        "from typing import Any, Dict, List, Optional\n"
    )
    module = ast.Module(body=header.body + [node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, Any] = {"__name__": "validator_extract"}
    exec(compile(module, str(path), "exec"), namespace)
    function = namespace.get(name)
    if not callable(function):
        raise TypeError(f"{name} n'est pas appelable")
    return function


def _load_csv(path: Path, report: Report) -> list[dict[str, str]] | None:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputError(f"{path}: {exc}") from exc

    if not raw.startswith(b"\xef\xbb\xbf"):
        report.fail("CSV BOM", "BOM UTF-8 absent (attendu EF BB BF)")
    else:
        report.ok("CSV BOM", "UTF-8 BOM present")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        report.fail("CSV encodage", f"UTF-8 invalide: {exc}")
        return None

    lines = text.splitlines()
    header = lines[0] if lines else ""
    if ";" not in header:
        report.fail("CSV separateur", "point-virgule absent de l'en-tete")
    elif "," in header:
        report.fail("CSV separateur", "virgule presente dans l'en-tete")
    else:
        report.ok("CSV separateur", "point-virgule, sans virgule")

    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";")
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

    bad_rows = [
        line
        for line, row in enumerate(rows, 2)
        if None in row or any(row.get(column) is None for column in COLONNES)
    ]
    if bad_rows:
        report.fail(
            "CSV champs",
            f"lignes a nombre de champs incorrect: {bad_rows[:5]}",
        )
        return None
    report.ok("CSV colonnes", f"13 colonnes, {len(rows)} lignes")

    missing: list[tuple[str, str]] = []
    for row in rows:
        for column in CORE_COLUMNS:
            if not (row.get(column) or "").strip():
                missing.append((row.get("SEQ", "?"), column))
    if missing:
        report.fail(
            "CSV champs obligatoires",
            f"{len(missing)} cellule(s) vide(s), ex. {missing[0]}",
        )
    else:
        report.ok("CSV champs obligatoires", f"{len(CORE_COLUMNS)} colonnes remplies")

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
        observed_value = (
            observed_seq[first - 1] if first <= len(observed_seq) else "absent"
        )
        expected_value = (
            expected_seq[first - 1] if first <= len(expected_seq) else "absent"
        )
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

    numbers: list[int] = []
    format_ok = True
    for stratum in strata:
        number = _strate_number(stratum)
        if number is None:
            report.fail("Strate format", f"libelle sans prefixe S<n>: {stratum}")
            format_ok = False
        else:
            numbers.append(number)
    if format_ok:
        expected_numbers = list(range(len(numbers)))
        if numbers != expected_numbers:
            report.fail(
                "Strates numerotation",
                f"attendu S0..S{len(numbers) - 1}, observe {numbers}",
            )
        else:
            report.ok("Strates numerotation", f"S0..S{len(numbers) - 1}")

    return rows


def _check_s6(
    rows: list[dict[str, str]],
    lib_fn: Callable[..., Any] | None,
    report: Report,
) -> None:
    s6 = [row for row in rows if _strate_number(row["STRATE"]) == 6]
    if not s6:
        report.fail("S6", "aucune ligne S6")
        return

    observed: dict[str, list[int]] = defaultdict(list)
    state_observed: dict[str, list[int]] = defaultdict(list)
    origin_value: int | None = None
    origin_magnitude: str | None = None
    malformed = False
    for row in s6:
        match = MAGNITUDE_RE.search(row["VALEUR_SCELLEE"])
        if not match:
            report.fail(
                "S6 format",
                f"SEQ {row['SEQ']}: magnitude absente de {row['VALEUR_SCELLEE']}",
            )
            malformed = True
            continue
        magnitude = match.group(1)
        if magnitude not in MAGNITUDE_SUM:
            report.fail(
                "S6 magnitude",
                f"SEQ {row['SEQ']}: magnitude inconnue {magnitude}",
            )
            malformed = True
            continue
        head = row["VALEUR_SCELLEE"].split("/", 1)[0].strip()
        try:
            value = int(head)
        except ValueError:
            report.fail(
                "S6 valeur",
                f"SEQ {row['SEQ']}: valeur non entiere {head}",
            )
            malformed = True
            continue
        if value < 0:
            report.fail("S6 valeur", f"SEQ {row['SEQ']}: valeur negative {value}")
        prefix = next(
            (item for item, _ in MAGNITUDE_BY_CODE if row["CODE"].startswith(item)),
            None,
        )
        if prefix is None:
            report.fail("S6 code", f"SEQ {row['SEQ']}: prefixe de code inconnu")
        elif dict(MAGNITUDE_BY_CODE)[prefix] != magnitude:
            report.fail(
                "S6 code",
                f"SEQ {row['SEQ']}: {row['CODE']} incompatible avec magnitude {magnitude}",
            )
        if "lib_physique.py" not in row["SOURCE"]:
            report.fail(
                "S6 source",
                f"SEQ {row['SEQ']}: source scellee absente ({row['SOURCE']})",
            )
        observed[magnitude].append(value)
        if row["CODE"] == S6_ORIGIN_CODE:
            if origin_value is not None:
                report.fail(
                    "S6 origine",
                    f"{S6_ORIGIN_CODE} apparait plusieurs fois",
                )
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
        report.fail(
            "S6 origine",
            f"{S6_ORIGIN_CODE} valeur {origin_value}, attendu 0",
        )
    else:
        report.ok("S6 origine", f"{S6_ORIGIN_CODE} = 0 (hors 4 etats)")

    counts = {magnitude: len(values) for magnitude, values in state_observed.items()}
    sums = {magnitude: sum(values) for magnitude, values in observed.items()}
    if sums != MAGNITUDE_SUM:
        report.fail(
            "S6 sommes",
            f"observe {sums}, attendu {MAGNITUDE_SUM}",
        )
    else:
        report.ok("S6 sommes", "40/313/63")
    if any(counts.get(magnitude, 0) != count for magnitude, count in MAGNITUDE_COUNT.items()):
        report.fail(
            "S6 comptes",
            f"observe {counts}, attendu {MAGNITUDE_COUNT} (+ origine 0)",
        )
    else:
        report.ok("S6 comptes", "4/7/9 + origine 0")
    report.ok(
        "S6 lignes",
        f"{len(s6)} lignes, etats 40/313/63 = "
        f"{counts.get('40', 0)}/{counts.get('313', 0)}/{counts.get('63', 0)} + origine",
    )

    if lib_fn is None:
        return
    if malformed:
        report.warn("S6 distribution", "non comparee: valeurs S6 mal formees")
        return

    try:
        expected = {
            "40": list(lib_fn(4 * 10, 4)),
            "313": list(lib_fn(3 * 100, 3))
            + list(lib_fn(1 * 10, 1))
            + list(lib_fn(3 * 1, 3)),
            "63": list(lib_fn(6 * 10, 6)) + list(lib_fn(3 * 1, 3)),
        }
    except Exception as exc:
        report.fail("S6 lib", f"calcul impossible: {type(exc).__name__}: {exc}")
        return

    for magnitude, values in expected.items():
        if (
            len(values) != MAGNITUDE_COUNT[magnitude]
            or sum(values) != MAGNITUDE_SUM[magnitude]
        ):
            report.fail(
                "S6 formule",
                f"magnitude {magnitude}: {len(values)} valeurs, somme {sum(values)}",
            )
            return

    for magnitude in ("40", "313", "63"):
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


def _check_generator(
    path: Path,
    rows: list[dict[str, str]],
    lib_fn: Callable[..., Any] | None,
    report: Report,
) -> None:
    try:
        source = _read_text(path)
        tree = ast.parse(source)
    except InputError:
        raise
    except Exception as exc:
        report.fail("Generateur lecture", f"{type(exc).__name__}: {exc}")
        return

    assignments: dict[str, ast.expr] = {}
    functions: dict[str, ast.FunctionDef] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            assignments[node.targets[0].id] = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.value is not None
        ):
            assignments[node.target.id] = node.value
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = node

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

    add_node = functions.get("add")
    if add_node is None:
        report.fail("Generateur add", "fonction absente")
    else:
        params = [arg.arg for arg in add_node.args.args]
        if (
            params != ADD_PARAMS
            or add_node.args.vararg is not None
            or add_node.args.kwarg is not None
            or add_node.args.kwonlyargs
        ):
            report.fail(
                "Generateur add",
                f"parametres observes: {params}",
            )
        else:
            report.ok("Generateur add", "12 parametres attendus")
        add_source = ast.get_source_segment(source, add_node) or ""
        if "len(ROWS)" in add_source and "03d" in add_source and "SEQ" in add_source:
            report.ok("Generateur SEQ", "add() numerote automatiquement")
        else:
            report.fail(
                "Generateur SEQ",
                "add() ne contient pas la numerotation len(ROWS) + 03d",
            )

    manual_seq: list[int] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "add"
            and any(keyword.arg == "SEQ" for keyword in node.keywords)
        ):
            manual_seq.append(node.lineno)
    if manual_seq:
        report.fail(
            "Generateur SEQ manuelle",
            f"SEQ passe a add() aux lignes {manual_seq[:5]}",
        )
    else:
        report.ok("Generateur SEQ manuelle", "aucun SEQ passe a add()")

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
            if not isinstance(colors, dict):
                report.warn("Generateur couleurs", "COULEURS_STRATE n'est pas un dict")
            else:
                missing = [stratum for stratum in strata if stratum not in colors]
                extra = [key for key in colors if key not in strata]
                if missing:
                    labels = [stratum.split("·")[0].strip() for stratum in missing]
                    report.warn(
                        "Generateur couleurs",
                        f"{len(missing)} strate(s) sans couleur explicite: "
                        + ", ".join(labels[:8])
                        + (", ..." if len(labels) > 8 else ""),
                    )
                if extra:
                    report.warn(
                        "Generateur couleurs",
                        f"{len(extra)} couleur(s) sans strate: "
                        + ", ".join(str(key) for key in extra[:8]),
                    )
                if not missing and not extra:
                    report.ok("Generateur couleurs", f"{len(strata)} strates couvertes")

    docstring = ast.get_docstring(tree) or ""
    match = DOC_RANGE_RE.search(docstring)
    if not match:
        report.warn("Generateur docstring", "plage SEQ 001-N introuvable")
    elif int(match.group(1)) != len(rows):
        report.warn(
            "Generateur docstring",
            f"SEQ 001-{match.group(1)} alors que N={len(rows)}",
        )
    else:
        report.ok("Generateur docstring", f"plage SEQ 001-{len(rows)}")

    date_node = assignments.get("DATE_GENERATION")
    if date_node is None:
        report.warn("Generateur date", "DATE_GENERATION introuvable")
    else:
        segment = ast.get_source_segment(source, date_node) or ""
        if "date.today" in segment and "isoformat" in segment:
            report.ok("Generateur date", "DATE_GENERATION dynamique")
        else:
            report.warn(
                "Generateur date",
                f"DATE_GENERATION non dynamique: {segment[:60]}",
            )

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
                and not isinstance(value.value, bool)
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

    if "_repartir_somme_unique" not in functions:
        report.fail("Generateur fonction", "_repartir_somme_unique absente")
    elif lib_fn is None:
        report.warn(
            "Parite algorithme",
            "non comparee: lib_physique indisponible",
        )
    else:
        try:
            generated_fn = _extract_function(path, "_repartir_somme_unique")
        except Exception as exc:
            report.fail(
                "Generateur fonction",
                f"_repartir_somme_unique: {type(exc).__name__}: {exc}",
            )
        else:
            cases = [
                (0, 0),
                (1, 1),
                (40, 4),
                (300, 3),
                (10, 1),
                (3, 3),
                (60, 6),
                (63, 9),
                (313, 7),
                (1000, 10),
                (2, 3),
                (5, 4),
                (7, 2),
            ]
            for total, count in cases:
                try:
                    got = generated_fn(total, count)
                    want = lib_fn(total, count)
                except Exception as exc:
                    report.fail(
                        "Parite algorithme",
                        f"cas ({total},{count}): {type(exc).__name__}: {exc}",
                    )
                    break
                if got != want:
                    report.fail(
                        "Parite algorithme",
                        f"cas ({total},{count}): generateur={got}, lib={want}",
                    )
                    break
            else:
                report.ok(
                    "Parite algorithme",
                    f"_repartir_somme_unique identique sur {len(cases)} cas",
                )


def _check_lock(path: Path, report: Report) -> None:
    try:
        data = json.loads(_read_text(path))
    except InputError:
        raise
    except Exception as exc:
        report.fail("A137 lecture", f"{type(exc).__name__}: {exc}")
        return
    if not isinstance(data, dict):
        report.fail("A137 structure", "objet JSON attendu")
        return

    ok = True
    if data.get("verrouille") is not True:
        report.fail("A137 verrou", "verrouille != true")
        ok = False
    for key in ("lecture", "execution"):
        if data.get(key) is not True:
            report.fail("A137 politique", f"{key} != true")
            ok = False
    for key in ("ecriture", "modification", "troncature"):
        if data.get(key) is not False:
            report.fail("A137 politique", f"{key} != false")
            ok = False
    if ok:
        report.ok("A137", "lecture/execution autorisees, ecriture interdite")


def _self_contained(url: str) -> bool:
    value = url.strip()
    if not value:
        return True
    return value.lower().startswith(
        ("data:", "#", "javascript:", "mailto:", "tel:", "about:")
    )


def _css_urls(text: str) -> list[str]:
    urls: list[str] = []
    for match in CSS_URL_RE.finditer(text):
        url = (match.group(2) or "").strip()
        if url:
            urls.append(url)
    return urls


def _external_resources(text: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for tag, attrs in RESOURCE_TAG_RE.findall(text):
        tag_lower = tag.lower()
        if tag_lower == "base":
            findings.append(("base", "(declaration)"))
            continue
        for match in RESOURCE_ATTR_RE.finditer(attrs):
            attribute = match.group(1).lower()
            value = match.group(3).strip()
            if not value:
                continue
            if attribute == "style":
                for url in _css_urls(value):
                    if not _self_contained(url):
                        findings.append((f"{tag_lower}[style]", url))
            elif attribute == "srcset":
                for candidate in value.split(","):
                    url = candidate.strip().split()[0] if candidate.strip() else ""
                    if url and not _self_contained(url):
                        findings.append((f"{tag_lower}[srcset]", url))
            elif not _self_contained(value):
                findings.append((f"{tag_lower}[{attribute}]", value))

    for match in STYLE_ATTR_RE.finditer(text):
        for url in _css_urls(match.group(2)):
            if not _self_contained(url):
                findings.append(("style[attr]", url))

    for block in STYLE_BLOCK_RE.findall(text):
        for match in CSS_IMPORT_RE.finditer(block):
            chunk = match.group(0)
            url_match = re.search(r"url\(\s*[\"']?([^\"')]+)", chunk, re.I)
            if not url_match:
                url_match = re.search(r"[\"']([^\"']+)[\"']", chunk)
            if url_match:
                url = url_match.group(1).strip()
                if url and not _self_contained(url):
                    findings.append(("css[@import]", url))
        for url in _css_urls(block):
            if not _self_contained(url):
                findings.append(("css[url]", url))

    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str]] = []
    for item in findings:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _check_html(
    path: Path,
    rows: list[dict[str, str]],
    report: Report,
    allow_external: bool,
) -> None:
    try:
        text = _read_text(path)
    except InputError:
        raise
    except Exception as exc:
        report.fail("HTML lecture", f"{type(exc).__name__}: {exc}")
        return

    parser = MasterTableParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:
        report.fail("HTML analyse", f"{type(exc).__name__}: {exc}")
        return

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
    if not parser.rows:
        report.fail("HTML cellules", "aucune ligne de donnees")
    elif bad_shape:
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
    else:
        report.fail("HTML derniere SEQ", "aucune ligne exploitable")

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

    subtitle = SUBTITLE_RE.search(text)
    if not subtitle:
        report.warn("HTML sous-titre", "sequence/strates introuvable")
    elif int(subtitle.group(1)) != len(rows) or int(subtitle.group(2)) != len(strata):
        report.fail(
            "HTML sous-titre",
            f"observe {subtitle.group(1)} entrees / {subtitle.group(2)} strates, "
            f"attendu {len(rows)} / {len(strata)}",
        )
    else:
        report.ok("HTML sous-titre", f"{len(rows)} entrees / {len(strata)} strates")

    findings = _external_resources(text)
    if findings:
        detail = "; ".join(f"{tag}={url}" for tag, url in findings[:3])
        if allow_external:
            report.warn(
                "HTML autonomie",
                f"{len(findings)} ressource(s) externe(s) toleree(s): {detail}",
            )
        else:
            report.fail(
                "HTML autonomie",
                f"{len(findings)} ressource(s) externe(s): {detail}",
            )
    else:
        report.ok("HTML autonomie", "aucune ressource externe")


def validate(
    paths: dict[str, Path],
    report: Report,
    allow_external: bool,
) -> None:
    rows = _load_csv(paths["csv"], report)
    if rows is None:
        return

    lib_fn: Callable[..., Any] | None
    try:
        lib_fn = _extract_function(paths["lib"], "_repartir_somme_unique")
    except InputError:
        raise
    except Exception as exc:
        report.fail("S6 lib", f"{type(exc).__name__}: {exc}")
        lib_fn = None

    _check_s6(rows, lib_fn, report)
    _check_generator(paths["generator"], rows, lib_fn, report)
    _check_lock(paths["lock"], report)
    _check_html(paths["html"], rows, report, allow_external)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the IMAM8MAHDI master sequential table (read-only)."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Repository root (default: IMAM8MAHDI desktop folder).",
    )
    parser.add_argument("--csv", type=Path, help="CSV path (default: root/CSV_NAME).")
    parser.add_argument("--html", type=Path, help="HTML path (default: root/HTML_NAME).")
    parser.add_argument(
        "--generator", type=Path, help="Generator path (default: root/GEN_REL)."
    )
    parser.add_argument("--lib", type=Path, help="lib_physique path (default: root/LIB_REL).")
    parser.add_argument("--lock", type=Path, help="A137 lock path (default: root/LOCK_REL).")
    parser.add_argument(
        "--allow-external",
        action="store_true",
        help="Allow external HTML resources (warning instead of failure).",
    )
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Treat warnings as failures.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print the traceback on unexpected errors.",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    paths = {
        "csv": _resolve(args.csv, root, Path(CSV_NAME)),
        "html": _resolve(args.html, root, Path(HTML_NAME)),
        "generator": _resolve(args.generator, root, GEN_REL),
        "lib": _resolve(args.lib, root, LIB_REL),
        "lock": _resolve(args.lock, root, LOCK_REL),
    }

    print("== TABLEAU MAITRE SEQUENTIEL - VALIDATION (lecture seule) ==")
    print("ROOT : " + _safe(root))
    for label, path in paths.items():
        print(f"{label.upper():9s}: {_safe(path)}")

    report = Report()
    try:
        _require_inputs(paths)
        validate(paths, report, args.allow_external)
    except InputError as exc:
        print("[FAIL] Entree : " + _safe(exc))
        print("RESULT: FAIL (entree manquante ou illisible)")
        return 2
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
    if args.strict_warnings and report.warnings:
        print(f"RESULT: FAIL strict ({len(report.warnings)} avertissement(s))")
        return 1
    print(f"RESULT: OK ({len(report.warnings)} avertissement(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
