#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pose les deux lignes SPDX dans des fichiers Python sans toucher aux autres octets.

L'insertion est idempotente : un fichier qui porte deja l'identifiant vise est
ignore. Les fins de ligne et l'absence de BOM sont preservees ; un fichier BOM,
mixte ou non UTF-8 est refuse plutot que reecrit. Le texte modifie est valide par
ast.parse avant tout ecriture.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

COOKIE_RE = re.compile(r"^#.*coding[:=]\s*[-\w.]+")
LICENSE_TAG = "SPDX-License-Identifier:"
COPYRIGHT_TAG = "SPDX-FileCopyrightText:"
EXPR_RE = re.compile(r"^[A-Za-z0-9.+-]+((?: OR | AND | WITH )[A-Za-z0-9.+-]+)*$")
DEFAULT_EXCLUDES = (".git", "__pycache__", ".qoder")


def ascii_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


class Refus(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def detect_eol(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n")
    if crlf and lf != crlf:
        raise Refus("mixed_eol")
    return "\r\n" if crlf else "\n"


def read_parts(path: Path) -> tuple[list[str], str, bool]:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        raise Refus("bom")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise Refus("not_utf8")
    eol = detect_eol(data)
    if not text:
        return [], eol, True
    tail = text.endswith(eol)
    parts = text.split(eol)
    if tail:
        parts.pop()
    return parts, eol, tail


def render(parts: list[str], eol: str, tail: bool) -> str:
    return eol.join(parts) + (eol if tail and parts else "")


def anchor_index(parts: list[str]) -> int:
    start = 1 if parts and parts[0].startswith("#!") else 0
    for index in range(0, min(8, len(parts))):
        if COOKIE_RE.match(parts[index]):
            if index > 1:
                raise Refus("cookie_too_deep")
            return index + 1
    return start


def tag_value(parts: list[str], tag: str) -> tuple[int, str] | None:
    for index, line in enumerate(parts[:8]):
        stripped = line.strip()
        if stripped.startswith("#") and tag in stripped:
            return index, stripped.split(tag, 1)[1].strip()
    return None


def ast_gate(text: str, path: Path, suffix: str) -> None:
    if suffix != ".py":
        return
    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        raise Refus(f"ast_error:{exc.lineno}:{ascii_text(exc.msg)}")


def plan_file(path: Path, args: argparse.Namespace) -> tuple[str, str | None]:
    parts, eol, tail = read_parts(path)
    current = tag_value(parts, LICENSE_TAG)
    if current is not None:
        index, value = current
        if value == args.licence:
            if tag_value(parts, COPYRIGHT_TAG) is None:
                parts.insert(index, f"# {COPYRIGHT_TAG} {args.titulaire}")
                return "ADD_COPYRIGHT", render(parts, eol, tail)
            return "SKIPPED", None
        if not args.remplacer:
            return "DIFFERS", None
        parts[index] = parts[index].replace(value, args.licence)
        return "SWITCHED", render(parts, eol, tail)
    index = anchor_index(parts)
    header = [
        f"# {COPYRIGHT_TAG} {args.titulaire}",
        f"# {LICENSE_TAG} {args.licence}",
    ]
    parts[index:index] = header
    return "CHANGED", render(parts, eol, tail)


def collect_files(root: Path, extensions: list[str], excludes: list[str]) -> list[Path]:
    blocked = set(excludes)
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in extensions:
            continue
        if any(part in blocked for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return files


def validate_args(args: argparse.Namespace) -> int:
    if not args.racine.is_dir():
        print(f"FAIL  root not found: {ascii_text(args.racine)}")
        return 2
    if not EXPR_RE.match(args.licence):
        print(f"FAIL  invalid SPDX expression: {ascii_text(args.licence)}")
        return 2
    if not args.titulaire.strip() or "\n" in args.titulaire or "\r" in args.titulaire:
        print("FAIL  invalid copyright holder (empty or multiline)")
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Insert idempotent SPDX headers without rewriting other bytes."
    )
    parser.add_argument("--racine", required=True, type=Path)
    parser.add_argument("--licence", required=True)
    parser.add_argument("--titulaire", required=True)
    parser.add_argument("--extension", action="append", default=None)
    parser.add_argument("--exclure", action="append", default=None)
    parser.add_argument("--appliquer", action="store_true")
    parser.add_argument("--remplacer", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    args.extension = args.extension or [".py"]
    args.exclure = list(DEFAULT_EXCLUDES) + list(args.exclure or [])

    if validate_args(args) != 0:
        print("RC=2")
        return 2

    mode = "apply" if args.appliquer else "dry-run"
    print(f"ROOT {ascii_text(args.racine.resolve())}")
    print(f"LICENCE {ascii_text(args.licence)}")
    print(f"MODE {mode}")

    counts = {"CHANGED": 0, "ADD_COPYRIGHT": 0, "SWITCHED": 0,
              "SKIPPED": 0, "DIFFERS": 0, "REFUSED": 0}
    ast_ok = 0
    refused = 0
    for path in collect_files(args.racine, args.extension, args.exclure):
        rel = ascii_text(path.relative_to(args.racine).as_posix())
        try:
            action, text = plan_file(path, args)
            if text is not None:
                ast_gate(text, path, path.suffix)
                ast_ok += 1
                if args.appliquer:
                    payload = text.encode("utf-8")
                    path.write_bytes(payload)
                    if path.read_bytes() != payload:
                        raise Refus("write_mismatch")
                    print(f"{action} {rel}")
                else:
                    print(f"WOULD_{action} {rel}")
            else:
                print(f"{action} {rel}")
        except Refus as exc:
            refused += 1
            print(f"REFUSED {rel} {exc.reason}")
            continue
        except OSError as exc:
            refused += 1
            print(f"REFUSED {rel} io_error:{ascii_text(exc.strerror or exc)}")
            continue
        counts[action] += 1
        if args.verbose and action in ("SKIPPED", "DIFFERS"):
            print(f"  detail {rel} {action}")

    changed = counts["CHANGED"] + counts["ADD_COPYRIGHT"] + counts["SWITCHED"]
    print(f"TOTAL {sum(counts.values()) + refused}")
    print(f"CHANGED {changed} SKIPPED {counts['SKIPPED']} "
          f"DIFFERS {counts['DIFFERS']} REFUSED {refused}")
    print(f"AST_OK {ast_ok}")
    verdict = "PASS" if refused == 0 and counts["DIFFERS"] == 0 else "FAIL"
    print(f"RESULT {verdict}")
    print(f"RC={0 if verdict == 'PASS' else 1}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
