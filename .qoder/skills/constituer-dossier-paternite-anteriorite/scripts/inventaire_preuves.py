#!/usr/bin/env python3
"""Contradictory inventory of evidence pieces (read-only).

Recomputes SHA-256, size and mtime for each declared piece, then confronts the
result with the hashes declared by the pieces file and by optional manifests.
The source tree is never modified: writes happen only in --out-json/--out-md.

Verdicts: CONCORDE, DIVERGENCE, NON_DECLARE, MANQUANT, NON_VERIFIABLE.
Exit codes: 0 no contradiction, 1 contradiction or missing piece, 2 input error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BLOC = 1 << 20
HEX64 = re.compile(r"^[0-9a-f]{64}$")

VERDICTS_BLOQUANTS = {"DIVERGENCE", "MANQUANT", "NON_VERIFIABLE"}


def ascii_text(valeur: object) -> str:
    return str(valeur).encode("ascii", "backslashreplace").decode("ascii")


def echec(message: str) -> int:
    print("ERREUR " + ascii_text(message))
    print("RESULT FAIL")
    return 2


def maintenant_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as flux:
        for bloc in iter(lambda: flux.read(BLOC), b""):
            h.update(bloc)
    return h.hexdigest()


def mtime_utc(chemin: Path) -> str:
    return (
        datetime.fromtimestamp(chemin.stat().st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


def normaliser_chemin(chemin: str) -> str:
    texte = str(chemin).strip().replace("\\", "/")
    while texte.startswith("./"):
        texte = texte[2:]
    return os.path.normcase(texte)


def normaliser_hash(valeur: object) -> Optional[str]:
    if not isinstance(valeur, str):
        return None
    texte = valeur.strip().lower()
    if texte.startswith("0x"):
        texte = texte[2:]
    return texte if HEX64.match(texte) else None


def declarer(destination: Dict[str, List[Dict[str, str]]], chemin: str, valeur: object, source: str) -> None:
    h = normaliser_hash(valeur)
    cle = normaliser_chemin(chemin)
    destination.setdefault(cle, [])
    if h is None:
        destination[cle].append({"source": source, "valeur": str(valeur), "invalide": "true"})
    else:
        destination[cle].append({"source": source, "valeur": h})


def collecter_manifeste(donnees: Any, source: str, sortie: Dict[str, List[Dict[str, str]]], cle: Optional[str], profondeur: int = 0) -> None:
    if cle is not None:
        if not isinstance(donnees, dict) or cle not in donnees:
            raise KeyError("cle de manifeste absente: " + cle)
        donnees = donnees[cle]
    if isinstance(donnees, dict):
        for k, v in donnees.items():
            if isinstance(v, dict) and profondeur < 3:
                collecter_manifeste(v, source, sortie, None, profondeur + 1)
                continue
            if isinstance(v, dict) and isinstance(v.get("sha256"), str):
                declarer(sortie, str(k), v["sha256"], source)
            elif isinstance(v, str):
                declarer(sortie, str(k), v, source)
    elif isinstance(donnees, list):
        for entree in donnees:
            if not isinstance(entree, dict):
                continue
            chemin = entree.get("chemin") or entree.get("path")
            valeur = entree.get("sha256") or entree.get("hash")
            if chemin and valeur:
                declarer(sortie, str(chemin), valeur, source)


def charger_manifestes(chemins: Iterable[str], cle: Optional[str]) -> Tuple[Dict[str, List[Dict[str, str]]], List[str]]:
    declarations: Dict[str, List[Dict[str, str]]] = {}
    sources: List[str] = []
    for brut in chemins:
        chemin = Path(brut).expanduser()
        if not chemin.is_file():
            raise FileNotFoundError("manifeste introuvable: " + str(chemin))
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
        collecter_manifeste(donnees, chemin.name, declarations, cle)
        sources.append(str(chemin))
    return declarations, sources


def resoudre(source: Path, chemin: str) -> Optional[Path]:
    candidat = Path(str(chemin))
    if not candidat.is_absolute():
        candidat = source / candidat
    try:
        resolu = candidat.resolve()
        resolu.relative_to(source)
    except (OSError, ValueError):
        return None
    return resolu


def declarations_piece(piece: Dict[str, Any]) -> List[Dict[str, str]]:
    sortie: List[Dict[str, str]] = []
    for cle in ("sha256_declare", "sha256", "hash_declare"):
        valeur = piece.get(cle)
        if isinstance(valeur, str):
            sortie.append({"source": "piece." + cle, "valeur": valeur})
        elif isinstance(valeur, list):
            for item in valeur:
                sortie.append({"source": "piece." + cle, "valeur": item})
    for item in piece.get("hash_declares") or []:
        if isinstance(item, str):
            sortie.append({"source": "piece.hash_declares", "valeur": item})
        elif isinstance(item, dict) and item.get("valeur"):
            sortie.append({"source": str(item.get("source") or "piece.hash_declares"), "valeur": item["valeur"]})
    valides: List[Dict[str, str]] = []
    for item in sortie:
        h = normaliser_hash(item["valeur"])
        if h is None:
            valides.append({"source": item["source"], "valeur": str(item["valeur"]), "invalide": "true"})
        else:
            valides.append({"source": item["source"], "valeur": h})
    return valides


def inventarier(pieces: List[Dict[str, Any]], source: Path, manifestes: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    resultats: List[Dict[str, Any]] = []
    anomalies: List[Dict[str, Any]] = []
    compteur = {v: 0 for v in ("CONCORDE", "DIVERGENCE", "NON_DECLARE", "MANQUANT", "NON_VERIFIABLE")}

    for index, piece in enumerate(pieces, start=1):
        pid = str(piece.get("id") or "P" + str(index).zfill(2))
        chemin_declare = str(piece.get("chemin") or piece.get("path") or "")
        entree: Dict[str, Any] = {
            "id": pid,
            "role": piece.get("role"),
            "chemin_declare": chemin_declare,
        }
        if not chemin_declare:
            entree.update({"verdict": "NON_VERIFIABLE", "detail": "chemin absent"})
            resultats.append(entree)
            compteur["NON_VERIFIABLE"] += 1
            anomalies.append({"id": pid, "verdict": "NON_VERIFIABLE", "gravite": "HAUTE", "detail": "chemin absent"})
            continue

        resolu = resoudre(source, chemin_declare)
        declarations = declarations_piece(piece)
        if resolu is not None:
            relatif = resolu.relative_to(source).as_posix()
            entree["chemin_relatif"] = relatif
            declarations += manifestes.get(normaliser_chemin(relatif), [])
        entree["hash_declares"] = declarations

        if resolu is None:
            entree.update({"verdict": "NON_VERIFIABLE", "detail": "hors de la racine source"})
        elif not resolu.exists():
            entree.update({"verdict": "MANQUANT", "detail": "fichier absent"})
        elif not resolu.is_file():
            entree.update({"verdict": "NON_VERIFIABLE", "detail": "n'est pas un fichier"})
        else:
            entree["taille_octets"] = resolu.stat().st_size
            entree["mtime_utc"] = mtime_utc(resolu)
            try:
                calcule = sha256_fichier(resolu)
            except OSError as erreur:
                entree.update({"verdict": "NON_VERIFIABLE", "detail": "lecture impossible: " + str(erreur)})
            else:
                entree["sha256"] = calcule
                if not declarations:
                    entree.update({"verdict": "NON_DECLARE", "detail": "aucune empreinte declaree"})
                elif any(d.get("invalide") for d in declarations):
                    entree.update({"verdict": "NON_VERIFIABLE", "detail": "empreinte declaree invalide"})
                elif all(d["valeur"] == calcule for d in declarations):
                    entree.update({"verdict": "CONCORDE", "detail": str(len(declarations)) + "/" + str(len(declarations)) + " declaration(s) concordent"})
                else:
                    divergentes = sorted({d["valeur"] for d in declarations if d["valeur"] != calcule})
                    entree.update({"verdict": "DIVERGENCE", "detail": "attendu: " + ", ".join(divergentes)})

        compteur[entree["verdict"]] += 1
        if entree["verdict"] in VERDICTS_BLOQUANTS:
            anomalies.append(
                {
                    "id": pid,
                    "verdict": entree["verdict"],
                    "gravite": "HAUTE" if entree["verdict"] == "DIVERGENCE" else "MOYENNE",
                    "detail": entree.get("detail"),
                    "chemin": entree.get("chemin_relatif") or chemin_declare,
                }
            )
        resultats.append(entree)

    connus = {normaliser_chemin(p.get("chemin_relatif") or p.get("chemin_declare") or "") for p in resultats}
    orphelins = sorted(cle for cle in manifestes if cle not in connus)
    for cle in orphelins:
        anomalies.append(
            {"id": "MANIFESTE", "verdict": "ORPHELIN", "gravite": "MOYENNE", "detail": "declare au manifeste, absent de l'inventaire", "chemin": cle}
        )

    return {"pieces": resultats, "anomalies": anomalies, "resume": {"pieces": len(resultats), **{k.lower(): v for k, v in compteur.items()}, "manifeste_orphelins": len(orphelins)}}


def rapport_markdown(inv: Dict[str, Any], source: Path) -> str:
    r = inv["resume"]
    lignes = [
        "# RAPPORT D'INTEGRITE DES PIECES",
        "",
        "- Genere le : " + inv["genere_le"],
        "- Racine source : " + str(source),
        "- Methode : SHA-256 recalcule, comparaison aux declarations.",
        "",
        "## Resume",
        "",
        "| Mesure | Valeur |",
        "|---|---|",
        "| Pieces inventoriees | " + str(r["pieces"]) + " |",
        "| Concordance | " + str(r["concorde"]) + " |",
        "| Divergence | " + str(r["divergence"]) + " |",
        "| Non declaree | " + str(r["non_declare"]) + " |",
        "| Manquante | " + str(r["manquant"]) + " |",
        "| Non verifiable | " + str(r["non_verifiable"]) + " |",
        "| Orphelins de manifeste | " + str(r["manifeste_orphelins"]) + " |",
        "",
        "## Pieces",
        "",
        "| ID | Verdict | Taille | SHA-256 | Chemin |",
        "|---|---|---|---|---|",
    ]
    for p in inv["pieces"]:
        lignes.append(
            "| {id} | {verdict} | {taille} | {sha} | {chemin} |".format(
                id=p.get("id"),
                verdict=p.get("verdict"),
                taille=p.get("taille_octets", ""),
                sha=(p.get("sha256") or "")[:16],
                chemin=p.get("chemin_relatif") or p.get("chemin_declare"),
            )
        )
    lignes += ["", "## Anomalies", ""]
    if inv["anomalies"]:
        for a in inv["anomalies"]:
            lignes.append("- [" + str(a["verdict"]) + "] " + str(a.get("id")) + " : " + str(a.get("detail")) + " (" + str(a.get("chemin")) + ")")
    else:
        lignes.append("Aucune anomalie bloquante.")
    lignes += ["", "Une piece NON_DECLARE n'est pas une contradiction : elle n'est simplement couverte par aucune empreinte declaree."]
    return "\n".join(lignes) + "\n"


def ecrire_json(chemin: Path, donnees: Any) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="\n") as flux:
        json.dump(donnees, flux, indent=1, ensure_ascii=False)
        flux.write("\n")


def ecrire_texte(chemin: Path, texte: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="\n") as flux:
        flux.write(texte)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Inventaire contradictoire en lecture seule.")
    p.add_argument("--source", required=True, help="racine du corpus (jamais modifiee)")
    p.add_argument("--pieces", required=True, help="JSON des pieces et de leurs empreintes declarees")
    p.add_argument("--manifest", action="append", default=[], help="manifeste JSON additionnel (repetable)")
    p.add_argument("--manifest-cle", help="cle racine a lire dans chaque manifeste")
    p.add_argument("--out-json", help="rapport JSON")
    p.add_argument("--out-md", help="rapport Markdown")
    args = p.parse_args(argv)

    source = Path(args.source).expanduser()
    if not source.is_dir():
        return echec("racine source introuvable: " + args.source)
    source = source.resolve()

    try:
        charge = json.loads(Path(args.pieces).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError) as erreur:
        return echec("pieces illisibles: " + str(erreur))
    pieces = charge.get("pieces") if isinstance(charge, dict) else charge
    if not isinstance(pieces, list) or not pieces:
        return echec("le fichier pieces doit contenir une liste non vide")

    try:
        manifestes, sources_manifestes = charger_manifestes(args.manifest, args.manifest_cle)
    except (OSError, ValueError, KeyError) as erreur:
        return echec("manifeste illisible: " + str(erreur))

    inventaire = inventarier(pieces, source, manifestes)
    inventaire.update(
        {
            "genere_le": maintenant_utc(),
            "source": str(source),
            "methode": "SHA-256 recalcule, comparaison aux declarations, lecture seule.",
            "manifestes": sources_manifestes,
        }
    )

    if args.out_json:
        ecrire_json(Path(args.out_json).expanduser(), inventaire)
    if args.out_md:
        ecrire_texte(Path(args.out_md).expanduser(), rapport_markdown(inventaire, source))

    r = inventaire["resume"]
    print("Inventaire: " + str(r["pieces"]) + " pieces")
    print(
        "CONCORDE=" + str(r["concorde"])
        + " DIVERGENCE=" + str(r["divergence"])
        + " NON_DECLARE=" + str(r["non_declare"])
        + " MANQUANT=" + str(r["manquant"])
        + " NON_VERIFIABLE=" + str(r["non_verifiable"])
        + " ORPHELINS=" + str(r["manifeste_orphelins"])
    )
    print("Anomalies: " + str(len(inventaire["anomalies"])))
    if args.out_json:
        print("RAPPORT: " + str(Path(args.out_json).expanduser().resolve()))
    bloquant = any(r[k] for k in ("divergence", "manquant", "non_verifiable"))
    print("RESULT " + ("FAIL" if bloquant else "OK"))
    return 1 if bloquant else 0


if __name__ == "__main__":
    raise SystemExit(main())
