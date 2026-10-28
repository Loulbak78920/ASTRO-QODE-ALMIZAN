#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comparateur d'integrite LECTURE SEULE : arbre live vs arbre de reference.

Aucun import du paquet audite, aucune ecriture, aucun bytecode. La sortie est
ASCII stricte (console Windows cp1252/cp850). Le perimetre et les zones sont
decrits par un plan JSON ; aucun chemin propre au projet n'est code en dur.

Etats d'un fichier :
  SAME          live et reference ont le meme SHA-256
  DIFF          les deux existent, mais le contenu differe
  ABSENT_LIVE   present dans la reference, absent du live (perte)
  ABSENT_REF    present dans le live, absent de la reference (nouveau)
  UNREADABLE    lecture impossible (fichier verrouille, permission, etc.)

Politique par zone :
  blocking      un DIFF est une DERIVE (bloquante)
  churn         un DIFF est un CHURN (attendu, non bloquant par defaut)

Codes de sortie :
  0  OK, ou CHURN seul en mode non strict
  1  PERTE (ABSENT_LIVE dans n'importe quelle zone) ou DERIVE
  2  usage, plan invalide, racine absente, journal explicite absent,
     ou fichier illisible

Precedence : PERTE > DERIVE > CHURN > OK. Un fichier illisible produit
d'abord ERROR (2), car l'integrite ne peut pas etre certifiee.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


class PlanError(Exception):
    """Erreur d'usage ou d'environnement, code de sortie 2."""


def emit(texte: str) -> None:
    """Sortie ASCII stricte : la console Windows cp1252 ne doit rien casser."""
    sys.stdout.write(texte.encode("ascii", "backslashreplace").decode("ascii") + "\n")


def _sha256(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(65536), b""):
            h.update(bloc)
    return h.hexdigest()


def _mtime_iso(chemin: Path) -> str:
    try:
        return datetime.fromtimestamp(
            chemin.stat().st_mtime, timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
    except OSError:
        return "NA"


def _match(rel: str, motif: str) -> bool:
    if motif == "**":
        return True
    if fnmatch.fnmatchcase(rel, motif):
        return True
    if motif.startswith("**/") and fnmatch.fnmatchcase(rel, motif[3:]):
        return True
    return False


def _filtre(rel: str, include: list[str], exclude_globs: list[str]) -> bool:
    if exclude_globs and any(_match(rel, m) for m in exclude_globs):
        return False
    if include and not any(_match(rel, m) for m in include):
        return False
    return True


def _resoudre(base: Path, brut: str) -> Path:
    p = Path(brut)
    return p if p.is_absolute() else base / p


def _lister(
    root: Path,
    include: list[str],
    exclude_dirs: set[str],
    exclude_globs: list[str],
) -> dict[str, Path]:
    if not root.is_dir():
        raise PlanError(f"racine_absente={root}")
    out: dict[str, Path] = {}
    for dossier, sous_dirs, fichiers in os.walk(root):
        sous_dirs[:] = sorted(d for d in sous_dirs if d not in exclude_dirs)
        base = Path(dossier)
        for nom in sorted(fichiers):
            p = base / nom
            rel = p.relative_to(root).as_posix()
            if _filtre(rel, include, exclude_globs):
                out[rel] = p
    return out


def _charger_plan(chemin: Path) -> dict:
    try:
        data = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PlanError(f"plan_illisible={chemin} ({type(exc).__name__})")
    if not isinstance(data, dict):
        raise PlanError("plan_non_objet")

    zones = data.get("zones")
    if not isinstance(zones, list) or not zones:
        raise PlanError("zones_absentes")
    noms: set[str] = set()
    for zone in zones:
        if not isinstance(zone, dict):
            raise PlanError("zone_non_objet")
        nom = zone.get("name")
        if not isinstance(nom, str) or not nom:
            raise PlanError("zone_sans_nom")
        if nom in noms:
            raise PlanError(f"zone_dupliquee={nom}")
        noms.add(nom)

        if not isinstance(zone.get("live_root"), str) or not zone["live_root"]:
            raise PlanError(f"live_root_invalide={nom}")
        refs = zone.get("ref_roots")
        if (
            not isinstance(refs, list)
            or not refs
            or not all(isinstance(x, str) and x for x in refs)
        ):
            raise PlanError(f"ref_roots_invalides={nom}")
        policy = zone.get("policy", "blocking")
        if policy not in ("blocking", "churn"):
            raise PlanError(f"policy_invalide={nom}")
        zone["policy"] = policy

        for cle in ("include", "exclude_dirs", "exclude_globs"):
            valeur = zone.get(cle, [])
            if not isinstance(valeur, list) or not all(
                isinstance(x, str) for x in valeur
            ):
                raise PlanError(f"{cle}_invalide={nom}")
            zone[cle] = valeur

    journal = data.get("journal")
    if journal is not None:
        if not isinstance(journal, dict):
            raise PlanError("journal_non_objet")
        if "path" in journal and not isinstance(journal["path"], str):
            raise PlanError("journal_path_invalide")
        for cle in ("key_field", "phase_field", "phase_value", "ok_field"):
            if cle in journal and not isinstance(journal[cle], str):
                raise PlanError(f"journal_{cle}_invalide")
        if "churn_prefixes" in journal:
            prefixes = journal["churn_prefixes"]
            if not isinstance(prefixes, list) or not all(
                isinstance(x, str) for x in prefixes
            ):
                raise PlanError("journal_churn_prefixes_invalides")
    return data


def _selectionne(zone: str, cle: str, only: list[str]) -> bool:
    if not only:
        return True
    return any(
        valeur == cle
        or valeur == f"{zone}:{cle}"
        or valeur == f"{zone}/{cle}"
        for valeur in only
    )


def _evenements_journal(
    chemin: Path,
    lignes: int,
    depuis: str | None,
    cfg: dict,
) -> list[dict]:
    """Lit uniquement la queue du journal ; ignore les lignes invalides."""
    if not chemin.is_file():
        return []
    taille = chemin.stat().st_size
    fenetre = min(taille, max(65536, lignes * 512))
    with chemin.open("rb") as f:
        f.seek(taille - fenetre)
        brut = f.read()
    textes = brut.decode("utf-8", errors="replace").splitlines()
    if fenetre < taille and textes:
        textes = textes[1:]  # premiere ligne possiblement tronquee

    champ_cle = cfg.get("key_field", "cle")
    champ_phase = cfg.get("phase_field", "phase")
    phase_valeur = cfg.get("phase_value", "guerison")
    champ_ok = cfg.get("ok_field", "ok")

    evenements: list[dict] = []
    for ligne in textes:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            ev = json.loads(ligne)
        except (ValueError, TypeError):
            continue
        if not isinstance(ev, dict):
            continue
        if ev.get(champ_phase) != phase_valeur or not ev.get(champ_ok):
            continue
        if depuis and str(ev.get("t", "")) < depuis:
            continue
        evenements.append(ev)
    return evenements


def _resultat_zone(zone: dict, base: Path, only: list[str], tout: bool) -> dict:
    nom = zone["name"]
    policy = zone["policy"]
    live_root = _resoudre(base, zone["live_root"])
    ref_roots = [_resoudre(base, r) for r in zone["ref_roots"]]

    live_files = _lister(
        live_root, zone["include"], set(zone["exclude_dirs"]), zone["exclude_globs"]
    )
    ref_files: dict[str, Path] = {}
    refs_existantes = 0
    for ref_root in ref_roots:
        if not ref_root.is_dir():
            continue
        refs_existantes += 1
        for cle, chemin in _lister(
            ref_root,
            zone["include"],
            set(zone["exclude_dirs"]),
            zone["exclude_globs"],
        ).items():
            ref_files.setdefault(cle, chemin)
    if refs_existantes == 0:
        raise PlanError(f"ref_absente={nom}")

    cles = sorted(set(live_files) | set(ref_files))
    cibles = [c for c in cles if _selectionne(nom, c, only)]

    items: list[dict] = []
    for cle in cibles:
        live = live_files.get(cle)
        ref = ref_files.get(cle)
        item = {
            "cle": cle,
            "zone": nom,
            "policy": policy,
            "etat": "",
            "sha_live": "NA",
            "sha_ref": "NA",
            "mtime_live": "NA",
            "mtime_ref": "NA",
            "erreur": "NA",
        }
        if ref is None:
            item["etat"] = "ABSENT_REF"
            try:
                item["sha_live"] = _sha256(live)  # type: ignore[arg-type]
                item["mtime_live"] = _mtime_iso(live)  # type: ignore[arg-type]
            except OSError as exc:
                item["etat"] = "UNREADABLE"
                item["erreur"] = type(exc).__name__
        elif live is None:
            item["etat"] = "ABSENT_LIVE"
            try:
                item["sha_ref"] = _sha256(ref)
                item["mtime_ref"] = _mtime_iso(ref)
            except OSError as exc:
                item["etat"] = "UNREADABLE"
                item["erreur"] = type(exc).__name__
        else:
            try:
                sha_live = _sha256(live)
                sha_ref = _sha256(ref)
                item["sha_live"] = sha_live
                item["sha_ref"] = sha_ref
                item["mtime_live"] = _mtime_iso(live)
                item["mtime_ref"] = _mtime_iso(ref)
                item["etat"] = "SAME" if sha_live == sha_ref else "DIFF"
            except OSError as exc:
                item["etat"] = "UNREADABLE"
                item["erreur"] = type(exc).__name__
        items.append(item)

    return {"zone": nom, "policy": policy, "cibles": cibles, "items": items}


def _ligne_item(item: dict) -> str:
    etat = item["etat"]
    if etat == "SAME":
        return f"CLE={item['cle']} ETAT=SAME ZONE={item['zone']}"
    if etat == "UNREADABLE":
        return (
            f"CLE={item['cle']} ETAT=UNREADABLE ZONE={item['zone']} "
            f"ERREUR={item['erreur']}"
        )
    suffixe = ""
    if etat == "ABSENT_REF":
        suffixe = " (nouveau, absent de la reference)"
    return (
        f"CLE={item['cle']} ETAT={etat} ZONE={item['zone']} "
        f"SHA_LIVE={item['sha_live'][:16]} SHA_REF={item['sha_ref'][:16]} "
        f"MTIME_LIVE={item['mtime_live']} MTIME_REF={item['mtime_ref']}"
        f"{suffixe}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Comparer un arbre live et un arbre de reference (lecture seule)."
    )
    ap.add_argument("--plan", required=True, help="plan JSON des zones")
    ap.add_argument("--base", default=os.getcwd(), help="base des chemins relatifs")
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="cle, zone:cle ou zone/cle a verifier (repetable)",
    )
    ap.add_argument("--all", action="store_true", help="afficher aussi SAME et ABSENT_REF")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="traiter le CHURN des zones churn comme bloquant",
    )
    ap.add_argument("--journal", default=None, help="journal JSONL explicite")
    ap.add_argument(
        "--journal-lines",
        type=int,
        default=0,
        help="lire les N derniers evenements du journal",
    )
    ap.add_argument("--since", default=None, help="borne UTC 'YYYY-MM-DDTHH:MM:SSZ'")
    args = ap.parse_args()

    if args.journal_lines < 0:
        emit("RESULT USAGE journal_lines_negatif")
        return 2

    base = Path(os.path.abspath(args.base))
    plan_chemin = _resoudre(base, args.plan)
    try:
        plan = _charger_plan(plan_chemin)
        resultats = [
            _resultat_zone(zone, base, args.only, args.all) for zone in plan["zones"]
        ]
        if args.only and sum(len(r["cibles"]) for r in resultats) == 0:
            raise PlanError("only_sans_correspondance")
    except PlanError as exc:
        emit(f"RESULT USAGE {exc}")
        return 2

    n_same = n_nouveaux = n_diffs = n_pertes = n_illisibles = 0
    n_derives = n_churn = 0
    for resultat in resultats:
        z_same = z_nouveaux = z_diffs = z_pertes = z_illisibles = 0
        for item in resultat["items"]:
            etat = item["etat"]
            if etat == "SAME":
                z_same += 1
                if args.all:
                    emit(_ligne_item(item))
            elif etat == "ABSENT_REF":
                z_nouveaux += 1
                if args.all:
                    emit(_ligne_item(item))
            elif etat == "ABSENT_LIVE":
                z_pertes += 1
                n_pertes += 1
                emit(_ligne_item(item))
            elif etat == "DIFF":
                z_diffs += 1
                n_diffs += 1
                if resultat["policy"] == "churn":
                    n_churn += 1
                else:
                    n_derives += 1
                emit(_ligne_item(item))
            elif etat == "UNREADABLE":
                z_illisibles += 1
                n_illisibles += 1
                emit(_ligne_item(item))
        n_same += z_same
        n_nouveaux += z_nouveaux
        emit(
            f"ZONE={resultat['zone']} POLICY={resultat['policy']} "
            f"VERIFIES={len(resultat['cibles'])} SAME={z_same} "
            f"NOUVEAUX={z_nouveaux} DIFFS={z_diffs} PERTES={z_pertes} "
            f"ILLISIBLES={z_illisibles}"
        )

    verifies = sum(len(r["cibles"]) for r in resultats)
    emit(
        f"VERIFIES={verifies} SAME={n_same} NOUVEAUX={n_nouveaux} "
        f"ECARTS={n_diffs + n_pertes} PERTES={n_pertes} DERIVES={n_derives} "
        f"CHURN={n_churn} ILLISIBLES={n_illisibles}"
    )

    journal_cfg = dict(plan.get("journal") or {})
    journal_brut = args.journal or journal_cfg.get("path")
    if args.journal:
        journal_cfg["path"] = args.journal
    if args.journal_lines > 0 and not journal_brut:
        emit("RESULT USAGE journal_non_configure")
        return 2
    if args.journal_lines > 0:
        journal_chemin = _resoudre(base, str(journal_brut))
        if not journal_chemin.is_file():
            if args.journal:
                emit(f"RESULT USAGE journal_absent={journal_chemin}")
                return 2
            emit(f"JOURNAL_ABSENT={journal_chemin}")
        else:
            evenements = _evenements_journal(
                journal_chemin, args.journal_lines, args.since, journal_cfg
            )
            prefixes = journal_cfg.get("churn_prefixes", ["actes/", "memoire_aq/"])
            champ_cle = journal_cfg.get("key_field", "cle")
            code = [
                ev
                for ev in evenements
                if not str(ev.get(champ_cle, "")).startswith(tuple(prefixes))
            ]
            emit(
                f"JOURNAL_EVENEMENTS={len(evenements)} "
                f"JOURNAL_CODE_EVENEMENTS={len(code)} "
                f"SINCE={args.since or 'TOUT'}"
            )
            for ev in evenements[-args.journal_lines :]:
                emit(
                    f"EVENEMENT t={ev.get('t')} cle={ev.get(champ_cle)} "
                    f"type={ev.get('type_alteration', ev.get('type', 'NA'))}"
                )
            for ev in code[-args.journal_lines :]:
                emit(f"EVENEMENT_CODE t={ev.get('t')} cle={ev.get(champ_cle)}")

    if n_illisibles:
        emit(f"RESULT ERROR unreadable={n_illisibles}")
        return 2
    if n_pertes:
        emit(f"RESULT PERTE {n_pertes} (fichier absent du live, sera restaure)")
        return 1
    if n_derives or (args.strict and n_churn):
        total = n_derives + (n_churn if args.strict else 0)
        emit(f"RESULT DERIVE {total} code={n_derives} churn={n_churn}")
        return 1
    if n_churn:
        emit(f"RESULT CHURN {n_churn} (zones declarees churn ; code integre)")
        return 0
    emit("RESULT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
