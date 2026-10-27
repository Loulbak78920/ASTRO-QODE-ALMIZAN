#!/usr/bin/env python3
"""Rend un rapport Markdown en HTML autonome, sans dependance externe.

Usage : py -3 -B rendre_md.py <entree.md> [sortie.html] [--check k=v,k=v]
Codes : 0 = OK, 1 = controle structurel en echec, 2 = usage ou E/S.
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*```([A-Za-z0-9_+-]*)\s*$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
UL = re.compile(r"^\s*[-*+]\s+(.*)$")
OL = re.compile(r"^\s*\d+[.)]\s+(.*)$")
HR = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")
TABLE_SEP = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
CODE_SPAN = re.compile(r"`([^`\n]+)`")
PLACEHOLDER = re.compile(r"\x00(\d+)\x00")
CJK = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef]")

COUNT_KEYS = ("h1", "h2", "table", "ul", "ol", "li", "pre", "code_inline")


def ascii_sur(valeur: object) -> str:
    """Empeche toute UnicodeEncodeError sur une console cp1252."""
    return str(valeur).encode("ascii", "backslashreplace").decode("ascii")


def masquer_code(texte: str, reserve: list[str]) -> str:
    """Extrait les spans inline avant analyse : protege |, *, < et **."""
    def remplacer(m: re.Match[str]) -> str:
        reserve.append(m.group(1))
        return f"\x00{len(reserve) - 1}\x00"

    return CODE_SPAN.sub(remplacer, texte)


def inline(texte: str, reserve: list[str] | None = None) -> str:
    reserve = reserve if reserve is not None else []
    if not PLACEHOLDER.search(texte):
        texte = masquer_code(texte, reserve)
    echappe = html.escape(texte, quote=False)
    echappe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", echappe)
    echappe = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", echappe)
    echappe = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        echappe,
    )

    def restaurer(m: re.Match[str]) -> str:
        contenu = reserve[int(m.group(1))]
        return f"<code>{html.escape(contenu, quote=False)}</code>"

    return PLACEHOLDER.sub(restaurer, echappe)


def joindre(gauche: str, droite: str) -> str:
    if gauche and droite and CJK.match(gauche[-1]) and CJK.match(droite[0]):
        return gauche + droite
    return f"{gauche} {droite}"


def debut_de_bloc(lignes: list[str], i: int) -> bool:
    ligne = lignes[i]
    if not ligne.strip():
        return True
    if FENCE.match(ligne) or HEADING.match(ligne) or UL.match(ligne) or OL.match(ligne):
        return True
    if HR.match(ligne):
        return True
    return "|" in ligne and i + 1 < len(lignes) and bool(TABLE_SEP.match(lignes[i + 1]))


def cellules(ligne: str, reserve: list[str]) -> list[str]:
    masque = masquer_code(ligne.strip(), reserve)
    return [c.strip() for c in masque.strip().strip("|").split("|")]


def rendre(markdown: str) -> tuple[str, str]:
    lignes = markdown.splitlines()
    blocs: list[str] = []
    titre = ""
    i = 0
    n = len(lignes)
    while i < n:
        ligne = lignes[i]
        if not ligne.strip():
            i += 1
            continue

        m = FENCE.match(ligne)
        if m:
            langage = m.group(1) or "text"
            i += 1
            code: list[str] = []
            while i < n and not FENCE.match(lignes[i]):
                code.append(lignes[i])
                i += 1
            i += 1
            blocs.append(
                f'<pre><code class="language-{html.escape(langage, quote=True)}">'
                f"{html.escape(chr(10).join(code), quote=False)}</code></pre>"
            )
            continue

        m = HEADING.match(ligne)
        if m:
            niveau = len(m.group(1))
            texte = inline(m.group(2))
            if niveau == 1 and not titre:
                titre = html.unescape(re.sub(r"<[^>]+>", "", texte)).strip()
            blocs.append(f"<h{niveau}>{texte}</h{niveau}>")
            i += 1
            continue

        if HR.match(ligne):
            blocs.append("<hr>")
            i += 1
            continue

        if "|" in ligne and i + 1 < n and TABLE_SEP.match(lignes[i + 1]):
            reserve: list[str] = []
            entetes = cellules(ligne, reserve)
            i += 2
            corps: list[list[str]] = []
            while i < n and lignes[i].strip() and "|" in lignes[i]:
                corps.append(cellules(lignes[i], reserve))
                i += 1
            tete = "".join(f"<th>{inline(c, reserve)}</th>" for c in entetes)
            rangees = "".join(
                "<tr>"
                + "".join(f"<td>{inline(c, reserve)}</td>" for c in r)
                + "</tr>"
                for r in corps
            )
            blocs.append(
                f"<table><thead><tr>{tete}</tr></thead><tbody>{rangees}</tbody></table>"
            )
            continue

        if UL.match(ligne) or OL.match(ligne):
            motif = UL if UL.match(ligne) else OL
            balise = "ul" if motif is UL else "ol"
            elements: list[str] = []
            while i < n:
                mm = motif.match(lignes[i])
                if not mm:
                    break
                elements.append(f"<li>{inline(mm.group(1))}</li>")
                i += 1
            blocs.append(f"<{balise}>" + "".join(elements) + f"</{balise}>")
            continue

        paragraphe = ligne.strip()
        i += 1
        while i < n and not debut_de_bloc(lignes, i):
            paragraphe = joindre(paragraphe, lignes[i].strip())
            i += 1
        blocs.append(f"<p>{inline(paragraphe)}</p>")

    if not titre:
        titre = "Rapport"
    return "\n".join(blocs), titre


TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<style>
  body {{ font-family: "Segoe UI", "Noto Sans CJK SC", Arial, sans-serif;
         max-width: 880px; margin: 2em auto; padding: 0 1.2em;
         line-height: 1.55; color: #1f2328; }}
  h1 {{ font-size: 1.8em; border-bottom: 2px solid #d0d7de; padding-bottom: .3em; }}
  h2 {{ font-size: 1.35em; margin-top: 1.6em; border-bottom: 1px solid #e5e9ef; padding-bottom: .2em; }}
  h3 {{ font-size: 1.15em; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size: .95em; }}
  th, td {{ border: 1px solid #c9d1d9; padding: .45em .6em; vertical-align: top; }}
  th {{ background: #f6f8fa; text-align: left; }}
  code {{ background: #f0f2f4; padding: .1em .3em; border-radius: 3px;
          font-family: Consolas, "Courier New", monospace; font-size: .92em; }}
  pre {{ background: #f6f8fa; border: 1px solid #d0d7de; padding: .8em 1em; overflow-x: auto; }}
  pre code {{ background: none; padding: 0; font-size: .9em; }}
  @media print {{
    @page {{ size: A4; margin: 16mm; }}
    body {{ max-width: none; margin: 0; padding: 0; font-size: 11pt; }}
    h1, h2, h3 {{ page-break-after: avoid; }}
    table, pre, tr, li {{ page-break-inside: avoid; }}
    a {{ color: inherit; text-decoration: none; }}
  }}
</style>
</head>
<body>
{corps}
</body>
</html>
"""


def compter(contenu: str) -> dict[str, int]:
    return {
        "h1": contenu.count("<h1"),
        "h2": contenu.count("<h2"),
        "table": contenu.count("<table"),
        "ul": contenu.count("<ul"),
        "ol": contenu.count("<ol"),
        "li": contenu.count("<li"),
        "pre": contenu.count("<pre"),
        "code_inline": contenu.count("<code>"),
        "backticks": contenu.count("`"),
        "pipe_lines": sum(
            1 for ligne in contenu.splitlines() if ligne.strip().startswith("|")
        ),
    }


def lire_controles(valeur: str) -> dict[str, int]:
    controles: dict[str, int] = {}
    for morceau in valeur.split(","):
        if not morceau.strip():
            continue
        cle, sep, brut = morceau.partition("=")
        cle = cle.strip()
        if not sep or cle not in COUNT_KEYS:
            raise ValueError(f"controle inconnu: {morceau!r}")
        controles[cle] = int(brut.strip())
    return controles


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    analyseur = argparse.ArgumentParser(description=__doc__)
    analyseur.add_argument("entree", type=Path)
    analyseur.add_argument("sortie", type=Path, nargs="?")
    analyseur.add_argument("--check", default="", help="attentes, ex. h1=1,h2=7,table=2")
    args = analyseur.parse_args()

    try:
        controles = lire_controles(args.check)
    except ValueError as exc:
        print(f"ERROR check={ascii_sur(exc)}")
        return 2

    if not args.entree.is_file():
        print(f"ERROR entree_absente={ascii_sur(args.entree)}")
        return 2
    sortie = args.sortie or args.entree.with_suffix(".html")

    try:
        source = args.entree.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"ERROR lecture={ascii_sur(exc)}")
        return 2

    corps, titre = rendre(source)
    contenu = TEMPLATE.format(titre=html.escape(titre), corps=corps)
    try:
        sortie.parent.mkdir(parents=True, exist_ok=True)
        sortie.write_text(contenu, encoding="utf-8", newline="\n")
    except OSError as exc:
        print(f"ERROR ecriture={ascii_sur(exc)}")
        return 2

    mesures = compter(contenu)
    print(f"OK {ascii_sur(sortie)} {len(contenu.encode('utf-8'))} octets")
    print("COUNTS " + " ".join(f"{k}={mesures[k]}" for k in COUNT_KEYS))
    print(f"CLEAN backticks={mesures['backticks']} pipe_lines={mesures['pipe_lines']}")

    echec = False
    for cle, attendu in controles.items():
        if mesures[cle] != attendu:
            print(f"CHECK_FAIL {cle} expected={attendu} actual={mesures[cle]}")
            echec = True
    if mesures["backticks"] or mesures["pipe_lines"]:
        print("CHECK_FAIL marqueurs_markdown_residuels=1")
        echec = True
    print("RESULT=" + ("FAIL" if echec else "PASS"))
    return 1 if echec else 0


if __name__ == "__main__":
    raise SystemExit(main())
