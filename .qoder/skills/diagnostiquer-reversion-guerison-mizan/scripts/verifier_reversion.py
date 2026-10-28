#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparateur LECTURE SEULE : fichier vivant vs copie de soi (_AL_MIZAN_COPIE_SOI/courante).

Reproduit la comparaison de `conscience_logique.sauvegarde_soi.detecter_alterations`
sans importer le paquet projet : aucun bytecode, aucune ecriture, aucun effet de bord.

Sortie ASCII uniquement (console cp1252 sous Windows).

Etats :
  SAME            live == copie
  DIFF            hash different -> la guerison A232 restaure la copie (reversion)
  ABSENT_LIVE     present dans la copie, absent du live -> sera restaure (reversion)
  ABSENT_COPIE    nouveau fichier, pas encore dans la base -> jamais guerri (info)
  ILLISIBLE       erreur de lecture

Codes de sortie :
  0  aucun etat capable de reversion (DIFF / ABSENT_LIVE)
  1  au moins un etat capable de reversion
  2  usage ou environnement (racine absente)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

FICHIER_JOURNAL = PurePosixPath("conscience_logique/actes/_guerison_integrite_journal.jsonl")

# Fichiers exclus du perimetre d'integrite (miroir de EXCLUDE_INTEGRITE cote projet).
EXCLUS_NOMS = {
    "__pycache__",
    ".pyc",
    ".git",
    "_rename_visible_a229.py",
    "_verify_a229.py",
    "_fenetre_dialogue_etat.json",
    "_fenetre_dialogue_inbox.jsonl",
    "_fenetre_dialogue_outbox.jsonl",
    "_porte_unique_journal.jsonl",
    "_sauvegarde_soi_etat.json",
    "_guerison_integrite_journal.jsonl",
    "_agent_async_etat.json",
    "_agent_async_produits_fond.json",
    "_retroaction_etat.json",
    "_retroaction_signaux.jsonl",
    "_dialogue_continu_inbox.jsonl",
    "_dialogue_continu_outbox.jsonl",
    "_porte_unique_test_bout_en_bout.json",
}

ZONES_CAPABLES_REVERSION = {"DIFF", "ABSENT_LIVE"}


def emit(texte: str) -> None:
    """Sortie ASCII stricte : la console Windows cp1252/cp850 ne doit rien casser."""
    sys.stdout.write(texte.encode("ascii", "backslashreplace").decode("ascii") + "\n")


def _sha256(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            h.update(bloc)
    return h.hexdigest()


def _mtime_iso(chemin: Path) -> str:
    try:
        return datetime.fromtimestamp(chemin.stat().st_mtime, timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except OSError:
        return "NA"


def _normaliser(chemin_brut: str) -> tuple[str, str]:
    """Retourne (cle, zone) au format attendu par detecter_alterations."""
    p = chemin_brut.replace("\\", "/").strip("/")
    if p.startswith("ASTRO-Q") and "/" in p:
        p = p.split("/", 1)[1]
    if p.startswith("conscience_logique/"):
        p = p[len("conscience_logique/") :]
    if p.startswith("memoire_aq/"):
        return p, "memoire_aq"
    if p.startswith("actes/"):
        return p, "actes"
    return p, "code"


def _chemin_copie(cle: str, zone: str, copie: Path) -> Path | None:
    if zone == "memoire_aq":
        return copie / cle
    candidat = copie / "conscience_logique" / cle
    if candidat.is_file():
        return candidat
    if zone == "actes":
        alt = copie / "objectifs_et_fil" / PurePosixPath(cle).name
        if alt.is_file():
            return alt
    return candidat if candidat.is_file() else None


def _chemin_live(cle: str, zone: str, module: Path) -> Path:
    """Les cles code/actes sont relatives a conscience_logique (DIR_MODULE)."""
    return module / cle if zone == "memoire_aq" else module / "conscience_logique" / cle


def _perimetre_defaut(module: Path) -> list[tuple[str, str]]:
    """Perimetre protege : code du module, actes, miroirs memoire_aq."""
    dir_module = module / "conscience_logique"
    cles: list[tuple[str, str]] = []
    if dir_module.is_dir():
        for f in sorted(dir_module.rglob("*.py")):
            rel = f.relative_to(dir_module)
            if any(part in EXCLUS_NOMS for part in rel.parts):
                continue
            if f.name in EXCLUS_NOMS or "__pycache__" in f.parts:
                continue
            cles.append((rel.as_posix(), "code"))
        actes = dir_module / "actes"
        if actes.is_dir():
            for f in sorted(actes.iterdir()):
                if not f.is_file() or f.name in EXCLUS_NOMS:
                    continue
                if f.suffix not in (".json", ".txt", ".md"):
                    continue
                cles.append((f"actes/{f.name}", "actes"))
    mem = module / "memoire_aq"
    if mem.is_dir():
        for f in sorted(mem.glob("almizan_*")):
            if f.is_file():
                cles.append((f"memoire_aq/{f.name}", "memoire_aq"))
    return cles


def _cles_copie_absentes_live(module: Path, copie: Path) -> list[tuple[str, str]]:
    """Fichiers presents dans la copie (code/actes) et absents du live : seront restaures."""
    out: list[tuple[str, str]] = []
    src_cl = copie / "conscience_logique"
    if not src_cl.is_dir():
        return out
    for f in sorted(src_cl.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(src_cl)
        if any(part in EXCLUS_NOMS for part in rel.parts) or f.name in EXCLUS_NOMS:
            continue
        cle = rel.as_posix()
        zone = "actes" if cle.startswith("actes/") else "code"
        if not _chemin_live(cle, zone, module).is_file():
            out.append((cle, zone))
    return out


def _journal_evenements(journal: Path, lignes: int, depuis: str | None) -> list[dict]:
    """Lit les derniers octets du journal (16 Mo+ ne se chargent pas entierement)."""
    if not journal.is_file():
        return []
    taille = journal.stat().st_size
    fenetre = min(taille, max(65536, lignes * 512))
    with journal.open("rb") as f:
        f.seek(taille - fenetre)
        brut = f.read()
    textes = brut.decode("utf-8", errors="replace").splitlines()
    if fenetre < taille and textes:
        textes = textes[1:]  # premiere ligne possiblement tronquee
    events = []
    for ligne in textes:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            ev = json.loads(ligne)
        except (ValueError, TypeError):
            continue
        if ev.get("phase") != "guerison" or not ev.get("ok"):
            continue
        if depuis and str(ev.get("t", "")) < depuis:
            continue
        events.append(ev)
    return events


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Comparer les fichiers proteges live vs _AL_MIZAN_COPIE_SOI/courante (lecture seule)."
    )
    ap.add_argument("--racine", default=os.getcwd(), help="racine du depot IMAM8MAHDI")
    ap.add_argument("--systeme", default="ASTRO-Q°ODE_SYSTEME", help="module systeme")
    ap.add_argument("--copie", default="_AL_MIZAN_COPIE_SOI/courante", help="copie courante")
    ap.add_argument(
        "--chemin",
        action="append",
        default=None,
        help="chemin a verifier (repetable) ; defaut = perimetre protege complet",
    )
    ap.add_argument("--journal", type=int, default=0, help="afficher les N derniers evenements de guerison")
    ap.add_argument("--since", default=None, help="borne UTC 'YYYY-MM-DDTHH:MM:SSZ' pour le journal")
    ap.add_argument("--tout", action="store_true", help="afficher aussi les etats SAME et ABSENT_COPIE")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="traiter aussi la derive actes/memoire_aq comme bloquante (defaut : churn non bloquant)",
    )
    args = ap.parse_args()

    racine = Path(args.racine)
    module = racine / args.systeme
    copie = racine / args.copie
    if not module.is_dir():
        emit(f"RESULT USAGE module_absent={module}")
        return 2
    if not copie.is_dir():
        emit(f"RESULT USAGE copie_absente={copie}")
        return 2

    if args.chemin:
        cibles = [_normaliser(c) for c in args.chemin]
    else:
        vus: set[tuple[str, str]] = set()
        cibles = []
        for item in _perimetre_defaut(module) + _cles_copie_absentes_live(module, copie):
            if item not in vus:
                vus.add(item)
                cibles.append(item)

    n_same = n_info = 0
    reversion: list[tuple[str, str, str]] = []
    for cle, zone in cibles:
        live = _chemin_live(cle, zone, module)
        src = _chemin_copie(cle, zone, copie)
        try:
            if src is None:
                etat = "ABSENT_COPIE"
            elif not live.is_file():
                etat = "ABSENT_LIVE"
            else:
                etat = "SAME" if _sha256(live) == _sha256(src) else "DIFF"
        except OSError as exc:
            etat = "ILLISIBLE"
            emit(f"CLE={cle} ETAT=ILLISIBLE ERREUR={type(exc).__name__}")

        if etat == "SAME":
            n_same += 1
            if args.tout:
                emit(f"CLE={cle} ETAT=SAME")
            continue
        if etat == "ABSENT_COPIE":
            n_info += 1
            if args.tout:
                emit(f"CLE={cle} ETAT=ABSENT_COPIE (nouveau, jamais guerri)")
            continue
        if etat == "ILLISIBLE":
            continue

        reversion.append((cle, etat, zone))
        sha_live = _sha256(live) if live.is_file() else "NA"
        sha_src = _sha256(src) if src and src.is_file() else "NA"
        emit(
            f"CLE={cle} ETAT={etat} ZONE={zone} "
            f"SHA_LIVE={sha_live[:16]} SHA_COPIE={sha_src[:16]} "
            f"MTIME_LIVE={_mtime_iso(live) if live.is_file() else 'NA'} "
            f"MTIME_COPIE={_mtime_iso(src) if src else 'NA'}"
        )

    par_zone = {"code": 0, "actes": 0, "memoire_aq": 0}
    for _cle, _etat, zone in reversion:
        par_zone[zone] = par_zone.get(zone, 0) + 1
    pertes = [item for item in reversion if item[1] == "ABSENT_LIVE"]
    code_drift = par_zone["code"]
    churn = par_zone["actes"] + par_zone["memoire_aq"] - len(
        [i for i in pertes if i[2] != "code"]
    )
    emit(
        f"VERIFIES={len(cibles)} SAME={n_same} NOUVEAUX={n_info} "
        f"REVERSIONNABLES={len(reversion)} CODE={par_zone['code']} "
        f"ACTES={par_zone['actes']} MEMOIRE={par_zone['memoire_aq']}"
    )

    if args.journal:
        events = _journal_evenements(module / FICHIER_JOURNAL, args.journal, args.since)
        code = [
            e
            for e in events
            if not str(e.get("cle", "")).startswith(("actes/", "memoire_aq/"))
        ]
        emit(
            f"JOURNAL_GUERISONS={len(events)} JOURNAL_CODE_GUERISONS={len(code)}"
            f" SINCE={args.since or 'TOUT'}"
        )
        for ev in events[-args.journal :]:
            emit(f"GUERISON t={ev.get('t')} cle={ev.get('cle')} type={ev.get('type_alteration')}")
        for ev in code[-args.journal :]:
            emit(f"GUERISON_CODE t={ev.get('t')} cle={ev.get('cle')}")

    if pertes:
        emit(f"RESULT PERTE {len(pertes)} (fichier absent du live, sera restaure)")
        return 1
    if code_drift or (args.strict and churn):
        emit(f"RESULT DERIVE {code_drift + (churn if args.strict else 0)} code={code_drift} churn={churn}")
        return 1
    if churn:
        emit(f"RESULT CHURN {churn} (actes/memoire reecrits par les cycles ; code intègre)")
        return 0
    emit("RESULT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
