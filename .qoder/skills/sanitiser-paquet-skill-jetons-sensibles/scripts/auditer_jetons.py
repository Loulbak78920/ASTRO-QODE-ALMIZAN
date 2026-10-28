#!/usr/bin/env python3
"""Audit en lecture seule des jetons personnels d'un paquet Skill.

N'affiche jamais la valeur d'un jeton, ni le contenu d'un fichier, ni le
chemin du fichier de jetons. Les chemins sont masques par <token#k>.
Sortie ASCII : les caracteres non ASCII sont echappes en \\xNN.

Codes de retour : 0 aucun jeton hors hexadecimal, 1 jeton en clair ou
encode ou present dans un chemin, 2 usage ou entree absente/vide.
"""

import argparse
import os
import re
import sys

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
TEXT_EXT = {
    ".md", ".json", ".cff", ".bib", ".ris", ".txt", ".py", ".js", ".yml",
    ".yaml", ".toml", ".html", ".css", ".csv", ".sh", ".ps1", ".bat",
    ".cfg", ".ini",
}
SPECIAL_NAMES = {".gitattributes", ".gitignore", "LICENSE", "NOTICE", "COPYING"}
HEX_RUN = re.compile(r"[0-9a-fA-F]{16,}")


def load_tokens(path):
    if path == "-":
        raw = sys.stdin.buffer.read().decode("utf-8-sig", "replace")
    else:
        if not os.path.isfile(path):
            return None
        with open(path, encoding="utf-8-sig", errors="replace") as handle:
            raw = handle.read()
    seen = set()
    tokens = []
    for line in raw.splitlines():
        token = line.strip()
        if not token or token.startswith("#"):
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        tokens.append(token)
    return tokens


def iter_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name not in SPECIAL_NAMES and os.path.splitext(name)[1].lower() not in TEXT_EXT:
                continue
            path = os.path.join(dirpath, name)
            if os.path.islink(path) or not os.path.isfile(path):
                continue
            yield path


def mask_path(rel, tokens):
    order = sorted(range(len(tokens)), key=lambda i: len(tokens[i]), reverse=True)
    for index in order:
        rel = re.sub(re.escape(tokens[index]), "<token#%d>" % (index + 1),
                     rel, flags=re.IGNORECASE)
    return rel


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(
        description="Audit masque des jetons personnels d'un paquet Skill.")
    parser.add_argument("--dossier", required=True)
    parser.add_argument("--tokens-file", required=True,
                        help="fichier de jetons, un par ligne ; '-' pour stdin")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.dossier)
    if not os.path.isdir(root):
        print("DOSSIER_ABSENT")
        return 2

    tokens = load_tokens(args.tokens_file)
    if tokens is None:
        print("TOKENS_FILE_ABSENT")
        return 2
    if not tokens:
        print("TOKENS_VIDES")
        return 2

    per_token = [
        {"clear": 0, "encoded": 0, "hex_only": 0, "path": 0}
        for _ in tokens
    ]
    scanned = 0
    leaks = 0

    for path in iter_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        scanned += 1
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                lines = handle.readlines()
        except OSError:
            lines = []
        rel_lower = rel.lower()
        masked = mask_path(rel, tokens)
        file_leak = False

        for index, token in enumerate(tokens):
            token_lower = token.lower()
            encoded = token.encode("utf-8").hex() if len(token) >= 4 else ""
            clear_lines = encoded_lines = hex_lines = 0
            first_clear = first_encoded = first_hex = None
            for number, line in enumerate(lines, 1):
                outside = HEX_RUN.sub("", line).lower()
                lowered = line.lower()
                if token_lower in outside:
                    clear_lines += 1
                    if first_clear is None:
                        first_clear = number
                elif encoded and encoded in lowered:
                    encoded_lines += 1
                    if first_encoded is None:
                        first_encoded = number
                elif token_lower in lowered:
                    hex_lines += 1
                    if first_hex is None:
                        first_hex = number

            path_hit = token_lower in rel_lower
            if clear_lines:
                print("CLEAR %s token#%d lines=%d first=%d"
                      % (masked, index + 1, clear_lines, first_clear))
                per_token[index]["clear"] += 1
                file_leak = True
            elif encoded_lines:
                print("ENCODED %s token#%d lines=%d first=%d"
                      % (masked, index + 1, encoded_lines, first_encoded))
                per_token[index]["encoded"] += 1
                file_leak = True
            elif hex_lines:
                print("HEX_ONLY %s token#%d lines=%d first=%d"
                      % (masked, index + 1, hex_lines, first_hex))
                per_token[index]["hex_only"] += 1
            if path_hit:
                print("PATH_JETON %s token#%d" % (masked, index + 1))
                per_token[index]["path"] += 1
                file_leak = True

        if file_leak:
            leaks += 1

    for index, counts in enumerate(per_token):
        print("SUMMARY token#%d clear=%d encoded=%d hex_only=%d path=%d"
              % (index + 1, counts["clear"], counts["encoded"],
                 counts["hex_only"], counts["path"]))

    print("TOKENS %d" % len(tokens))
    print("SCANNED %d" % scanned)
    if leaks:
        print("JETONS_EN_CLAIR %d" % leaks)
        print("RESULT FAIL")
        return 1
    print("AUCUN_JETON_EN_CLAIR")
    print("RESULT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
