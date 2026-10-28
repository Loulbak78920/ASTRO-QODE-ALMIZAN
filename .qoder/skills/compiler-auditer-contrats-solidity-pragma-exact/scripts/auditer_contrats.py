#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit statique de contrats Solidity avant livraison.

Controle le pragma exact, les retraits et les motifs de destruction.
Sortie ASCII uniquement. Codes : 0 PASS, 1 FAIL, 2 USAGE, 3 REVIEW.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PRAGMA = re.compile(r"pragma\s+solidity\s+([^;]+);")
FUNCTION_START = re.compile(r"\bfunction\s+([A-Za-z_]\w*)\s*\(")
WITHDRAW_NAME = re.compile(
    r"\bfunction\s+(retrait\w*|retirer\w*|withdraw\w*|recuper\w*|recover\w*|"
    r"sweep\w*|drain\w*|purge\w*|prelev\w*)\s*\(",
    re.IGNORECASE,
)
OWNER_GUARD = re.compile(
    r"(onlyOwner|seulementProprietaire|onlyAdmin|seulementAdmin|"
    r"\bowner\b|proprietaire|admin)",
    re.IGNORECASE,
)
FORBIDDEN = (
    (re.compile(r"\bselfdestruct\s*\("), "SELFDESTRUCT"),
    (re.compile(r"\bsuicide\s*\("), "SUICIDE"),
    (re.compile(r"\.delegatecall\s*\("), "DELEGATECALL"),
    (re.compile(r"\btx\.origin\b"), "TX_ORIGIN"),
    (
        re.compile(
            r"\b(private\s+key|mnemonic|seed\s+phrase|phrase\s+de\s+r[eé]cup[eé]ration)\b",
            re.IGNORECASE,
        ),
        "SECRET_WORD",
    ),
)
PRAGMA_OPERATOR = re.compile(r"[\^~<>]|=")


def out(line: str = "") -> None:
    print(line.encode("ascii", "backslashreplace").decode("ascii"))


def iter_functions(text: str):
    """Yield (name, line, header, body) for every function with a body."""
    for match in FUNCTION_START.finditer(text):
        name = match.group(1)
        index = match.end() - 1
        depth = 0
        while index < len(text):
            char = text[index]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    index += 1
                    break
            index += 1
        cursor = index
        while cursor < len(text) and text[cursor] not in "{;":
            cursor += 1
        if cursor >= len(text) or text[cursor] == ";":
            continue
        header = text[match.start():cursor]
        depth = 0
        end = cursor
        while end < len(text):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    end += 1
                    break
            end += 1
        body = text[cursor:end]
        line = text.count("\n", 0, match.start()) + 1
        yield name, line, header, body


def collect_files(args: argparse.Namespace) -> list[Path]:
    if args.fichiers:
        files = [Path(item) for item in args.fichiers]
    else:
        root = Path(args.dossier)
        if not root.is_dir():
            raise FileNotFoundError(f"dossier introuvable: {root}")
        files = sorted(root.glob("*.sol"))
    if not files:
        raise FileNotFoundError("aucun fichier .sol")
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError("fichier introuvable: " + ", ".join(missing))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit statique Solidity, sortie ASCII.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fichiers", nargs="+", help="fichiers .sol a auditer")
    source.add_argument("--dossier", help="dossier contenant les .sol (niveau racine)")
    parser.add_argument("--pragma", required=True, help="version exacte attendue, ex. 0.8.24")
    parser.add_argument(
        "--revu",
        action="append",
        default=[],
        metavar="FONCTION",
        help="candidat de retrait dont le corps a ete lu et juge non proprietaire",
    )
    args = parser.parse_args()

    try:
        files = collect_files(args)
    except FileNotFoundError as error:
        out("RESULT USAGE")
        out(f"ERREUR={error}")
        return 2

    failures: list[str] = []
    reviews: list[str] = []
    details: list[str] = []
    seen_functions: set[str] = set()
    exact = 0
    payable_total = 0
    owner_hits = 0
    candidates_total = 0
    reviewed_total = 0
    forbidden_hits = 0

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            out("RESULT USAGE")
            out(f"ERREUR={path.name}: {error}")
            return 2

        pragmas = PRAGMA.findall(text)
        if not pragmas:
            failures.append(f"PRAGMA_ABSENT={path.name}")
        else:
            spec = pragmas[0].strip()
            if PRAGMA_OPERATOR.search(spec):
                failures.append(f"PRAGMA_NON_EXACT={path.name}:{spec}")
            elif spec != args.pragma:
                failures.append(f"PRAGMA_DIFFERENT={path.name}:{spec}!={args.pragma}")
            else:
                exact += 1

        for pattern, label in FORBIDDEN:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                forbidden_hits += 1
                failures.append(f"INTERDIT={label}:{path.name}:{line}")

        for name, line, header, body in iter_functions(text):
            seen_functions.add(name)
            if re.search(r"\bpayable\b", header):
                payable_total += 1
                details.append(f"- {path.name}:{line} {name} PAYABLE")
            if not WITHDRAW_NAME.search(f"function {name}("):
                continue
            candidates_total += 1
            if OWNER_GUARD.search(header) or OWNER_GUARD.search(body):
                owner_hits += 1
                failures.append(f"RETRAIT_PROPRIETAIRE={path.name}:{line}:{name}")
            elif name in args.revu:
                reviewed_total += 1
                reviews.append(f"- {path.name}:{line} {name} CANDIDAT_REVU")
            else:
                reviews.append(f"- {path.name}:{line} {name} A_RELIRE")
                failures.append(f"CANDIDAT_NON_REVU={path.name}:{line}:{name}")

    unknown = sorted(set(args.revu) - seen_functions)
    if unknown:
        out("RESULT USAGE")
        out("ERREUR=revu_inconnu:" + ",".join(unknown))
        return 2

    unreviewed = [item for item in failures if item.startswith("CANDIDAT_NON_REVU=")]
    hard = [item for item in failures if not item.startswith("CANDIDAT_NON_REVU=")]

    if hard:
        out("RESULT FAIL")
    elif unreviewed:
        out("RESULT REVIEW")
    else:
        out("RESULT PASS")

    out(f"FICHIERS={len(files)}")
    out(f"PRAGMA={args.pragma}")
    out(f"PRAGMA_EXACT={exact}/{len(files)}")
    out(f"RETRAIT_PROPRIETAIRE={owner_hits}")
    out(f"CANDIDATS_RETRAIT={candidates_total}")
    out(f"CANDIDATS_REVUS={reviewed_total}")
    out(f"CANDIDATS_A_RELIRE={candidates_total - owner_hits - reviewed_total}")
    out(f"PAYABLE={payable_total}")
    out(f"INTERDITS={forbidden_hits}")

    for item in details + reviews:
        out(item)
    for item in failures:
        out(item)

    if hard:
        return 1
    if unreviewed:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
