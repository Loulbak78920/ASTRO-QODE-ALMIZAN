#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restaure les sceaux de `memoire_aq` créés par un test ou un `.aq run`.

Par défaut : simulation, aucune écriture. `--appliquer` écrit.
Le journal n'est modifié que si sa dernière entrée correspond exactement
à l'horodatage et au chemin fournis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

INDEX_NOM = "index_sceaux_astro_qode.json"
JOURNAL_NOM = "almizan_journal_agent_de_code.json"
TRACE_DIR = "entite_conscience_logarithmique"


def sortie_utf8() -> None:
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def date_locale(p: Path) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(p.stat().st_mtime))


def champ(entree: Any, nom: str) -> Any:
    return entree.get(nom) if isinstance(entree, dict) else None


def erreur(message: str) -> "Any":
    print(f"[ERREUR] {message}")
    print("RESULT: ERREUR")
    raise SystemExit(2)


def refus(message: str) -> "Any":
    print(f"[REFUS] {message}")
    print("RESULT: REFUS")
    raise SystemExit(1)


def charger_json(p: Path, role: str) -> Any:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return erreur(f"{role} illisible ({p}) : {exc}")


def ecrire_json(p: Path, donnees: Any, ensure_ascii: bool) -> None:
    texte = json.dumps(donnees, indent=2, ensure_ascii=ensure_ascii)
    tmp = p.with_name(p.name + ".tmp_restauration")
    tmp.write_text(texte, encoding="utf-8")
    os.replace(tmp, p)


def normaliser(nom: str) -> str:
    base = Path(nom).name
    if base.lower().endswith(".json"):
        base = base[:-5]
    if not base:
        refus("nom de sceau vide")
    return base


def decider_journal(aq: Path, chemin_atendu: str | None, horodatage_attendu: str | None) -> dict:
    if bool(chemin_atendu) != bool(horodatage_attendu):
        erreur("--journal-chemin et --journal-horodatage doivent être fournis ensemble")
    if not chemin_atendu and not horodatage_attendu:
        return {"etat": "ABSENT", "detail": "aucune condition journal fournie"}

    jr_p = aq / JOURNAL_NOM
    if not jr_p.is_file():
        erreur(f"journal introuvable : {jr_p}")
    donnees = charger_json(jr_p, "journal")
    journal = donnees.get("journal") if isinstance(donnees, dict) else None
    if not isinstance(journal, list) or not journal:
        return {"etat": "SAUTER", "detail": "journal vide ou absent"}
    derniere = journal[-1]
    horodatage_reel = str(champ(derniere, "horodatage_iso") or "")
    chemin_reel = str(champ(derniere, "chemin_fichier") or "")
    correspond = horodatage_reel == horodatage_attendu and chemin_atendu in chemin_reel
    return {
        "etat": "RETIRER" if correspond else "SAUTER",
        "detail": f"dernière entrée = {horodatage_reel} / {chemin_reel}",
        "entree": derniere,
    }


def construire_plan(aq: Path, cibles: list[str], args: argparse.Namespace) -> dict:
    if not aq.is_dir():
        erreur(f"répertoire memoire_aq introuvable : {aq}")
    idx_p = aq / INDEX_NOM
    if not idx_p.is_file():
        erreur(f"index introuvable : {idx_p}")

    index = charger_json(idx_p, "index")
    sceaux = index.get("sceaux") if isinstance(index, dict) else None
    if not isinstance(sceaux, dict):
        refus("index sans dictionnaire `sceaux`")

    for nom in cibles:
        if not (aq / f"{nom}.json").is_file():
            refus(f"sceau introuvable dans memoire_aq : {nom}.json")

    assoc: dict[str, str] = {}
    for nom in cibles:
        fichier = f"{nom}.json"
        trouve = nom if nom in sceaux else None
        if trouve is None:
            for cle, entree in sceaux.items():
                chemin = str(champ(entree, "chemin") or "")
                if chemin and Path(chemin).name == fichier:
                    trouve = cle
                    break
        if trouve is None:
            refus(f"aucune clé d'index ne correspond à {fichier}")
        if trouve in assoc and assoc[trouve] != nom:
            refus(f"clé {trouve} revendiquée par deux sceaux")
        assoc[trouve] = nom

    for cle, nom in assoc.items():
        chemin = str(champ(sceaux[cle], "chemin") or "")
        if chemin and Path(chemin).name != f"{nom}.json":
            refus(f"clé {cle} pointe vers {chemin}, pas vers {nom}.json")

    restants = {cle: valeur for cle, valeur in sceaux.items() if cle not in assoc}
    nb_apres = len(restants)
    horodatages = [str(champ(valeur, "timestamp") or "") for valeur in restants.values()]
    maj_apres = max((valeur for valeur in horodatages if valeur), default="")

    if args.attendu_nb is not None and args.attendu_nb != nb_apres:
        refus(f"nb_sceaux attendu {args.attendu_nb} mais calculé {nb_apres}")
    if args.attendu_maj is not None and args.attendu_maj != maj_apres:
        refus(f"derniere_mise_a_jour attendue {args.attendu_maj} mais calculée {maj_apres or '(aucune)'}")

    plan = {
        "cles": assoc,
        "nb_avant": len(sceaux),
        "nb_apres": nb_apres,
        "maj_apres": maj_apres,
        "journal": decider_journal(aq, args.journal_chemin, args.journal_horodatage),
    }

    incoherence = index.get("nb_sceaux") != len(sceaux)
    if incoherence:
        print(f"[ATTENTION] nb_sceaux={index.get('nb_sceaux')} incohérent avec {len(sceaux)} entrées ; calcul sur les entrées")

    print(f"[PLAN] index : {len(sceaux)} -> {nb_apres} sceaux ; derniere_mise_a_jour = {maj_apres or '(aucune)'}")
    for cle, nom in assoc.items():
        print(f"[PLAN] supprimer la clé {cle} (fichier {nom}.json)")
    for nom in cibles:
        print(f"[PLAN] mettre en quarantaine {nom}.json (déplacement, pas suppression)")
    journal = plan["journal"]
    if journal["etat"] == "RETIRER":
        print(f"[PLAN] journal : retirer la dernière entrée ({journal['detail']})")
    elif journal["etat"] == "SAUTER":
        print(f"[ATTENTION] journal non modifié : {journal['detail']} ne correspond pas à la condition")
    else:
        print("[PLAN] journal : aucune modification demandée")
    return plan


def verifier(aq: Path, cibles: list[str]) -> bool:
    ok = True
    idx_p = aq / INDEX_NOM
    if not idx_p.is_file():
        print(f"[ECHEC] index introuvable : {idx_p}")
        return False
    index = charger_json(idx_p, "index")
    sceaux = index.get("sceaux") if isinstance(index, dict) else None
    if not isinstance(sceaux, dict):
        print("[ECHEC] index sans dictionnaire `sceaux`")
        return False

    if index.get("nb_sceaux") != len(sceaux):
        print(f"[ECHEC] nb_sceaux={index.get('nb_sceaux')} != {len(sceaux)} entrées")
        ok = False
    else:
        print(f"[OK] nb_sceaux = {len(sceaux)} = nombre d'entrées")

    manquants = []
    for cle, entree in sceaux.items():
        chemin = str(champ(entree, "chemin") or "")
        if not chemin:
            continue
        try:
            if not Path(chemin).is_file():
                manquants.append(cle)
        except (OSError, ValueError):
            manquants.append(cle)
    print(f"[{'OK' if not manquants else 'ECHEC'}] références manquantes = {manquants}")
    ok = ok and not manquants

    presents = [nom for nom in cibles if (aq / f"{nom}.json").is_file()]
    print(f"[{'OK' if not presents else 'ECHEC'}] sceaux encore présents dans memoire_aq = {presents}")
    ok = ok and not presents

    trace = (aq / TRACE_DIR).is_dir()
    print(f"[INFO] répertoire de traces {TRACE_DIR} présent = {trace}")
    print(f"[INFO] fichiers JSON dans memoire_aq = {len(list(aq.glob('*.json')))}")
    print(f"[INFO] index sha256 = {sha256(idx_p)}")
    jr_p = aq / JOURNAL_NOM
    if jr_p.is_file():
        print(f"[INFO] journal sha256 = {sha256(jr_p)} ; mtime = {date_locale(jr_p)}")
        print("[ATTENTION] le journal n'est pas un témoin de lecture seule : un audit externe peut le réécrire en bloc.")
    print(f"[INFO] derniere_mise_a_jour = {index.get('derniere_mise_a_jour')}")
    return ok


def appliquer(aq: Path, plan: dict, cibles: list[str], quarantaine: Path) -> bool:
    if quarantaine.exists():
        refus(f"quarantaine déjà existante, choisir un autre chemin : {quarantaine}")

    idx_p = aq / INDEX_NOM
    jr_p = aq / JOURNAL_NOM
    sauvegarde = quarantaine / "sauvegarde"
    sauvegarde.mkdir(parents=True)

    fichiers = [idx_p]
    if jr_p.is_file():
        fichiers.append(jr_p)
    fichiers.extend(aq / f"{nom}.json" for nom in cibles)

    avant = {}
    for p in fichiers:
        avant[p.name] = {"sha256": sha256(p), "octets": p.stat().st_size, "mtime": date_locale(p)}
        shutil.copy2(p, sauvegarde / p.name)

    index = charger_json(idx_p, "index")
    for cle in plan["cles"]:
        index["sceaux"].pop(cle, None)
    index["nb_sceaux"] = len(index["sceaux"])
    index["derniere_mise_a_jour"] = plan["maj_apres"]
    ecrire_json(idx_p, index, ensure_ascii=False)

    journal_ecrit = False
    if plan["journal"]["etat"] == "RETIRER":
        journal = charger_json(jr_p, "journal")
        journal["journal"].pop()
        journal["total_fichiers_harmonises"] = len(journal["journal"])
        ecrire_json(jr_p, journal, ensure_ascii=True)
        journal_ecrit = True
        print(f"[OK] journal réduit à {len(journal['journal'])} entrées")
    else:
        print("[ATTENTION] journal non modifié (condition non satisfaite ou non fournie)")

    deplaces = {}
    for nom in cibles:
        source = aq / f"{nom}.json"
        cible = quarantaine / f"{nom}.json"
        shutil.move(str(source), str(cible))
        deplaces[nom] = {"chemin": str(cible), "sha256": sha256(cible)}
        print(f"[OK] sceau déplacé vers {cible}")

    apres = {}
    for p in [idx_p, jr_p]:
        if p.is_file():
            apres[p.name] = {"sha256": sha256(p), "octets": p.stat().st_size, "mtime": date_locale(p)}

    manifeste = {
        "horodatage": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "memoire_aq": str(aq),
        "sceaux_demandes": cibles,
        "cles_supprimees": plan["cles"],
        "nb_sceaux_avant": plan["nb_avant"],
        "nb_sceaux_apres": plan["nb_apres"],
        "derniere_mise_a_jour_apres": plan["maj_apres"],
        "journal": {
            "etat": plan["journal"]["etat"],
            "detail": plan["journal"]["detail"],
            "ecrit": journal_ecrit,
        },
        "fichiers_avant": avant,
        "fichiers_apres": apres,
        "quarantaine": deplaces,
        "sauvegarde": str(sauvegarde),
    }
    chemin_manifeste = quarantaine / "manifest_restauration.json"
    chemin_manifeste.write_text(json.dumps(manifeste, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] manifeste : {chemin_manifeste}")

    print("--- vérification post-restauration (lecture seule) ---")
    return verifier(aq, cibles)


def main() -> int:
    sortie_utf8()
    parser = argparse.ArgumentParser(
        description="Restaure les sceaux de memoire_aq créés par un test ou un .aq run (simulation par défaut)."
    )
    parser.add_argument("--memoire-aq", required=True, type=Path, help="répertoire memoire_aq à traiter")
    parser.add_argument("--sceau", action="append", default=[], help="nom ou fichier du sceau à restaurer (répétable)")
    parser.add_argument("--quarantaine", type=Path, help="répertoire de quarantaine (doit être absent)")
    parser.add_argument("--attendu-nb", type=int, help="nb_sceaux attendu APRÈS restauration")
    parser.add_argument("--attendu-maj", help="derniere_mise_a_jour attendue APRÈS restauration")
    parser.add_argument("--journal-chemin", help="sous-chaîne du chemin attendu dans la dernière entrée du journal")
    parser.add_argument("--journal-horodatage", help="horodatage_iso exact attendu dans la dernière entrée du journal")
    parser.add_argument("--appliquer", action="store_true", help="écrire les changements (sinon simulation)")
    parser.add_argument("--verifier-seulement", action="store_true", help="contrôle en lecture seule, aucune écriture")
    args = parser.parse_args()

    aq = args.memoire_aq
    cibles = [normaliser(nom) for nom in args.sceau]

    print(f"[MODE] {'vérification seule' if args.verifier_seulement else ('application' if args.appliquer else 'simulation')}")
    print(f"[CIBLE] {aq}")

    if args.verifier_seulement:
        if args.appliquer:
            erreur("--verifier-seulement est incompatible avec --appliquer")
        ok = verifier(aq, cibles)
        print("RESULT: OK" if ok else "RESULT: FAIL")
        return 0 if ok else 1

    if not cibles:
        erreur("fournir au moins un --sceau")

    plan = construire_plan(aq, cibles, args)
    if not args.appliquer:
        print("RESULT: PLAN")
        return 0

    quarantaine = args.quarantaine
    if quarantaine is None:
        quarantaine = Path.home() / ".qoder" / "tmp" / "restauration-sceaux" / time.strftime("%Y%m%d-%H%M%S")

    ok = appliquer(aq, plan, cibles, quarantaine)
    print("RESULT: OK" if ok else "RESULT: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
