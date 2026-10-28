#!/usr/bin/env python3
"""Preparation et qualification d'un dossier public de preuves d'anteriorite.

Sortie ASCII uniquement, codes 0 (OK) / 1 (ecart) / 2 (usage ou entree absente).

Sous-commandes :
  manifeste --dossier DIR
      Ecrit .gitattributes ("* -text") si absent, puis
      05_EMPREINTES/MANIFESTE_SHA256.json en s'excluant lui-meme.

  scan --dossier DIR --tokens-file FICHIER [--exempt REL:TOKEN]... [--skip REL]...
      Cherche les jetons interdits dans les fichiers texte. Une exemption n'est
      acceptee que si toutes ses occurrences sont dans des chaines hexadecimales.

  absence --dossier DIR --needle TEXTE...
      Compte un texte sensible en clair et encode en hexadecimal (ascii -> hex).

  dois --out FICHIER.json DOI...
      Interroge doi.org puis zenodo.org avec reprises et qualifie chaque DOI.

Exemples :
  py -3 preparer_publication.py manifeste --dossier "C:/tmp/preuves"
  py -3 preparer_publication.py scan --dossier "C:/tmp/preuves" --tokens-file tokens.txt
  py -3 preparer_publication.py absence --dossier "C:/tmp/preuves" --needle "JJ/MM/AAAA"
  py -3 preparer_publication.py dois --out "C:/tmp/preuves/04_PREUVES_EXTERNES/RAPPORT_VERIFICATION_DOIS.json" 10.5281/zenodo.23554838
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SKIP_DIRS = {".git", "__pycache__"}
MANIFEST_REL = "05_EMPREINTES/MANIFESTE_SHA256.json"
HEX_RUN = re.compile(r"[0-9a-fA-F]{16,}")
MAX_BYTES = 4 << 20
TEXT_EXT = {".md", ".json", ".cff", ".bib", ".ris", ".txt", ".py", ".yml", ".yaml", ".toml"}


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root, skipped=()):
    skipped = set(skipped)
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".pyc"):
                continue
            rel = os.path.relpath(os.path.join(base, name), root).replace(os.sep, "/")
            if rel in skipped:
                continue
            yield rel


def read_text(path):
    if os.path.getsize(path) > MAX_BYTES:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, OSError):
        return None


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def cmd_manifeste(args):
    root = os.path.abspath(args.dossier)
    if not os.path.isdir(root):
        print("DOSSIER_ABSENT %s" % args.dossier.replace(os.sep, "/"))
        return 2

    gitattributes = os.path.join(root, ".gitattributes")
    if not os.path.isfile(gitattributes):
        write_text(gitattributes, "* -text\n")
        print("GITATTRIBUTES_WRITTEN * -text")
    else:
        with open(gitattributes, encoding="utf-8") as f:
            content = f.read()
        if "* -text" in content:
            print("GITATTRIBUTES_PRESENT * -text")
        else:
            print("GITATTRIBUTES_NO_RULE %s" % ".gitattributes")
            return 1

    entries = []
    for rel in iter_files(root, skipped=(MANIFEST_REL,)):
        path = os.path.join(root, *rel.split("/"))
        entries.append({"chemin": rel, "octets": os.path.getsize(path),
                        "sha256": sha256_file(path)})
    entries.sort(key=lambda e: e["chemin"])
    listing = "".join("%s  %s\n" % (e["sha256"], e["chemin"]) for e in entries)
    manifest = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "algorithme": "SHA-256",
        "portee": "tous les fichiers du depot sauf ce manifeste",
        "nb_fichiers": len(entries),
        "empreinte_liste": sha256_bytes(listing.encode("utf-8")),
        "fichiers": entries,
    }
    manifest_path = os.path.join(root, *MANIFEST_REL.split("/"))
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("FILES %d" % len(entries))
    print("MANIFEST_SHA256 %s" % sha256_file(manifest_path))
    print("RESULT OK")
    return 0


def _parse_exempt(values):
    pairs = set()
    for item in values:
        rel, sep, token = item.partition(":")
        if not sep or not rel or not token:
            raise ValueError("exemption attendue REL:TOKEN, recu %r" % item)
        pairs.add((rel, token))
    return pairs


def cmd_scan(args):
    root = os.path.abspath(args.dossier)
    if not os.path.isdir(root):
        print("DOSSIER_ABSENT %s" % args.dossier.replace(os.sep, "/"))
        return 2
    try:
        exempt = _parse_exempt(args.exempt)
    except ValueError as exc:
        print("USAGE %s" % exc)
        return 2

    with open(args.tokens_file, encoding="utf-8") as f:
        tokens = [line.strip() for line in f
                  if line.strip() and not line.lstrip().startswith("#")]
    if not tokens:
        print("TOKENS_VIDES %s" % args.tokens_file.replace(os.sep, "/"))
        return 2

    problems = []
    exempt_seen = set()
    scanned = 0
    for rel in iter_files(root, skipped=args.skip):
        path = os.path.join(root, *rel.split("/"))
        if os.path.splitext(path)[1].lower() not in TEXT_EXT:
            continue
        text = read_text(path)
        if text is None:
            continue
        scanned += 1
        outside = HEX_RUN.sub("", text)
        for token in tokens:
            total = text.count(token)
            if not total:
                continue
            bare = outside.count(token)
            if (rel, token) in exempt:
                exempt_seen.add((rel, token))
                print("EXEMPT %s token=%s occurrences=%d hex_only=%s"
                      % (rel, token, total, "yes" if bare == 0 else "no"))
                if bare:
                    problems.append("%s: exemption refusee, %d occurrence(s) hors hexadecimal"
                                    % (rel, bare))
                continue
            line_no = next(i for i, line in enumerate(text.splitlines(), 1) if token in line)
            excerpt = text.splitlines()[line_no - 1].strip()[:160]
            print("HIT %s:%d token=%s :: %s" % (rel, line_no, token, excerpt))
            problems.append("%s:%d %s" % (rel, line_no, token))

    for rel, token in sorted(exempt - exempt_seen):
        print("EXEMPT_UNUSED %s token=%s" % (rel, token))

    print("SCANNED %d" % scanned)
    if problems:
        print("REDACTION_PROBLEMS %d" % len(problems))
        return 1
    print("REDACTION_OK")
    return 0


def cmd_absence(args):
    root = os.path.abspath(args.dossier)
    if not os.path.isdir(root):
        print("DOSSIER_ABSENT %s" % args.dossier.replace(os.sep, "/"))
        return 2

    found = 0
    per_needle = {needle: 0 for needle in args.needle}
    scanned = 0
    for rel in iter_files(root):
        path = os.path.join(root, *rel.split("/"))
        if os.path.splitext(path)[1].lower() not in TEXT_EXT:
            continue
        text = read_text(path)
        if text is None:
            continue
        scanned += 1
        lowered = text.lower()
        for needle in args.needle:
            raw = text.count(needle)
            encoded = needle.encode("utf-8").hex()
            hex_hits = lowered.count(encoded)
            if raw:
                line_no = next(i for i, line in enumerate(text.splitlines(), 1) if needle in line)
                print("PRESENT %s:%d %r" % (rel, line_no, needle))
                found += 1
                per_needle[needle] += 1
            if hex_hits:
                print("PRESENT_HEX %s %r %s" % (rel, needle, encoded))
                found += 1
                per_needle[needle] += 1
    for needle in args.needle:
        print("NEEDLE %r raw_or_hex_found=%s"
              % (needle, "yes" if per_needle[needle] else "no"))
    print("SCANNED %d" % scanned)
    if found:
        print("ABSENCE_FAIL")
        return 1
    print("ABSENCE_OK")
    return 0


def _http_json(url, tries=3):
    headers = {"User-Agent": "Mozilla/5.0 (preuves-anteriorite; verification)"}
    last = {"url": url, "http_status": None, "body": None}
    for attempt in range(tries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", "replace")
                body = json.loads(raw) if raw.strip().startswith(("{", "[")) else raw[:2000]
                last = {"url": url, "http_status": resp.status, "body": body}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            try:
                body = json.loads(raw)
            except ValueError:
                body = raw[:2000]
            last = {"url": url, "http_status": exc.code, "body": body}
        except Exception as exc:  # reseau, DNS, TLS
            last = {"url": url, "http_status": None, "body": None, "error": str(exc)[:200]}
        if last.get("http_status") in (200, 404, 410):
            return last
        if attempt + 1 < tries:
            time.sleep(2)
    return last


def cmd_dois(args):
    report = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "GET https://doi.org/api/handles/<doi> puis GET https://zenodo.org/api/records/<id>",
        "checks": [],
    }
    for doi in args.doi:
        handle = _http_json("https://doi.org/api/handles/" + urllib.parse.quote(doi, safe="/"))
        record_id = doi.rsplit(".", 1)[-1]
        zenodo = _http_json("https://zenodo.org/api/records/" + record_id)
        h_status = handle.get("http_status")
        h_code = handle["body"].get("responseCode") if isinstance(handle.get("body"), dict) else None
        z_status = zenodo.get("http_status")
        if h_status == 404 and h_code == 100:
            verdict = "NON_EXISTANT_404"
        elif h_status == 200 and h_code == 1 and z_status == 200:
            verdict = "RESOLU"
        elif z_status == 410:
            verdict = "ENREGISTREMENT_SUPPRIME_410"
        else:
            verdict = "INDETERMINE_AU_RELEVE"
        report["checks"].append({
            "doi": doi,
            "doi_handle_http": h_status,
            "doi_handle_response_code": h_code,
            "doi_handle_error": handle.get("error"),
            "zenodo_record_http": z_status,
            "zenodo_record_error": zenodo.get("error"),
            "verdict": verdict,
        })
        print("DOI %s handle=%s zenodo=%s %s" % (doi, h_status, z_status, verdict))

    if args.out:
        write_text(os.path.abspath(args.out),
                   json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print("REPORT %s" % args.out.replace(os.sep, "/"))
    print("RESULT OK")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Outils du dossier de preuves d'anteriorite.")
    sub = parser.add_subparsers(dest="commande", required=True)

    p_manifest = sub.add_parser("manifeste", help=".gitattributes + manifeste SHA-256")
    p_manifest.add_argument("--dossier", required=True)
    p_manifest.set_defaults(func=cmd_manifeste)

    p_scan = sub.add_parser("scan", help="cherche les jetons interdits")
    p_scan.add_argument("--dossier", required=True)
    p_scan.add_argument("--tokens-file", required=True)
    p_scan.add_argument("--exempt", action="append", default=[], metavar="REL:TOKEN")
    p_scan.add_argument("--skip", action="append", default=[], metavar="REL")
    p_scan.set_defaults(func=cmd_scan)

    p_abs = sub.add_parser("absence", help="texte absent en clair et en hexadecimal")
    p_abs.add_argument("--dossier", required=True)
    p_abs.add_argument("--needle", action="append", required=True, metavar="TEXTE")
    p_abs.set_defaults(func=cmd_absence)

    p_doi = sub.add_parser("dois", help="qualifie des DOIs")
    p_doi.add_argument("doi", nargs="+")
    p_doi.add_argument("--out")
    p_doi.set_defaults(func=cmd_dois)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="ascii", errors="backslashreplace")
    sys.exit(main())
