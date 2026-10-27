#!/usr/bin/env python3
"""Instantane et comparaison des effets de bord d'une verification.

Lecture seule vis-a-vis des cibles : le script ne lit que les fichiers cibles.
Il ecrit uniquement le fichier d'instantane, la sauvegarde demandee et son
manifeste. Aucun fichier cible n'est modifie, deplace ou supprime.

Codes de sortie :
  0  aucun changement de contenu (les reecritures identiques sont signalees)
  1  changement de contenu detecte
  2  erreur, instantane illisible ou etat instable
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

VERSION = 1
MAX_KEYS = 5000
TS_KEYS = (
    "horodatage_iso",
    "horodatage",
    "horodatage_utc",
    "timestamp",
    "timestamp_utc",
    "date",
    "ts",
)
FILE_KEYS = ("chemin_fichier", "fichier", "file", "chemin", "path", "nom_fichier")
HASH_KEYS = ("taille", "mtime_ns", "sha256")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for bloc in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(bloc)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def entry_timestamp(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    for cle in TS_KEYS:
        if entry.get(cle) is not None:
            return str(entry[cle])
    return None


def entry_file(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    for cle in FILE_KEYS:
        if entry.get(cle) is not None:
            return str(entry[cle])
    return None


def entry_signature(entry: Any) -> str | None:
    horodatage = entry_timestamp(entry)
    fichier = entry_file(entry)
    if horodatage is None and fichier is None:
        return None
    return f"{horodatage or ''}|{fichier or ''}"


def summarize_list(items: list[Any]) -> dict[str, Any]:
    signatures: Counter[str] = Counter()
    sans_signature = 0
    distribution: Counter[str] = Counter()
    for item in items:
        signature = entry_signature(item)
        if signature is None:
            sans_signature += 1
        else:
            signatures[signature] += 1
        horodatage = entry_timestamp(item)
        if horodatage is not None:
            distribution[horodatage] += 1
    return {
        "longueur": len(items),
        "signatures": dict(signatures),
        "sans_signature": sans_signature,
        "distribution": dict(distribution),
        "empreinte": sha256_json(items),
    }


def summarize_json(data: Any) -> dict[str, Any]:
    resume: dict[str, Any] = {
        "type_racine": type(data).__name__,
        "cles": [],
        "type_cles": {},
        "scalaires": {},
        "dict_cles": {},
        "listes": {},
    }
    if isinstance(data, dict):
        resume["cles"] = sorted(str(cle) for cle in data)
        for cle_brute, valeur in data.items():
            cle = str(cle_brute)
            resume["type_cles"][cle] = type(valeur).__name__
            if isinstance(valeur, dict):
                cles = sorted(str(item) for item in valeur)
                resume["dict_cles"][cle] = {
                    "nombre": len(cles),
                    "cles": cles[:MAX_KEYS],
                    "tronque": len(cles) > MAX_KEYS,
                }
            elif isinstance(valeur, list):
                resume["listes"][cle] = summarize_list(valeur)
            else:
                resume["scalaires"][cle] = valeur
    elif isinstance(data, list):
        resume["listes"]["$racine"] = summarize_list(data)
    else:
        resume["scalaires"]["$racine"] = data
    return resume


def resume_json(path: Path) -> dict[str, Any]:
    try:
        texte = path.read_text(encoding="utf-8-sig")
        return summarize_json(json.loads(texte))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"erreur": f"{type(exc).__name__}: {exc}"}


def iter_target_files(cible: Path, recursif: bool) -> Iterator[tuple[Path, Path]]:
    if cible.is_file():
        yield cible, Path(cible.name)
        return
    if recursif:
        for racine, _dossiers, fichiers in os.walk(cible):
            for nom in sorted(fichiers):
                chemin = Path(racine) / nom
                yield chemin, chemin.relative_to(cible)
    else:
        for chemin in sorted(cible.iterdir()):
            if chemin.is_file():
                yield chemin, Path(chemin.name)


def file_meta(path: Path) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "taille": None,
        "mtime_ns": None,
        "sha256": None,
        "lien_symbolique": path.is_symlink(),
    }
    try:
        stat = path.stat()
        meta["taille"] = stat.st_size
        meta["mtime_ns"] = stat.st_mtime_ns
        meta["sha256"] = sha256_file(path)
        if path.suffix.lower() == ".json":
            meta["json_resume"] = resume_json(path)
    except OSError as exc:
        meta["erreur"] = f"{type(exc).__name__}: {exc}"
    return meta


def scan_target(cible: Path, recursif: bool, exclusions: set[str]) -> dict[str, Any]:
    resultat: dict[str, Any] = {
        "chemin": str(cible),
        "existe": cible.exists(),
        "recursif": recursif,
        "fichiers": {},
    }
    if not cible.exists():
        return resultat
    if cible.is_file():
        if norm(cible) not in exclusions:
            resultat["fichiers"][cible.name] = file_meta(cible)
        return resultat
    for chemin, relatif in iter_target_files(cible, recursif):
        if norm(chemin) in exclusions:
            continue
        resultat["fichiers"][relatif.as_posix()] = file_meta(chemin)
    return resultat


def scan_errors(cibles: list[dict[str, Any]]) -> list[str]:
    erreurs = []
    for cible in cibles:
        for relatif, meta in cible.get("fichiers", {}).items():
            if "erreur" in meta:
                erreurs.append(f"{cible.get('chemin')}:{relatif}: {meta['erreur']}")
    return erreurs


def compare_scans(
    avant: list[dict[str, Any]], apres: list[dict[str, Any]]
) -> list[str]:
    differences = []
    for gauche, droite in zip(avant, apres):
        fichiers_gauche = gauche.get("fichiers", {})
        fichiers_droite = droite.get("fichiers", {})
        for relatif in sorted(set(fichiers_gauche) | set(fichiers_droite)):
            if relatif not in fichiers_gauche:
                differences.append(f"apparu: {relatif}")
            elif relatif not in fichiers_droite:
                differences.append(f"disparu: {relatif}")
            else:
                meta_gauche = fichiers_gauche[relatif]
                meta_droite = fichiers_droite[relatif]
                if any(
                    meta_gauche.get(cle) != meta_droite.get(cle)
                    for cle in HASH_KEYS
                ):
                    differences.append(f"change: {relatif}")
    return differences


def write_json_atomic(path: Path, data: Any, force: bool = True) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"le fichier existe deja: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporaire = path.with_name(path.name + f".tmp-{os.getpid()}")
    temporaire.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporaire, path)


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return (cleaned or "cible")[:60]


def backup_targets(
    cibles: list[dict[str, Any]], destination: Path
) -> dict[str, Any]:
    destination = destination.expanduser().resolve()
    for cible in cibles:
        chemin = Path(cible["chemin"])
        base = chemin if chemin.is_dir() else chemin.parent
        if destination == base or destination.is_relative_to(base):
            raise ValueError(
                f"le repertoire de sauvegarde ne doit pas etre dans la cible: {chemin}"
            )
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(
            f"le repertoire de sauvegarde existe deja et n'est pas vide: {destination}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    manifeste: dict[str, Any] = {
        "horodatage_utc": utc_now(),
        "cibles": [],
        "fichiers": [],
    }
    for index, cible in enumerate(cibles, 1):
        chemin = Path(cible["chemin"])
        entree: dict[str, Any] = {
            "chemin": str(chemin),
            "existe": chemin.exists(),
            "recursif": cible.get("recursif", True),
            "copie": None,
        }
        if chemin.exists():
            racine_copie = destination / f"cible_{index:02d}_{safe_name(chemin.name)}"
            entree["copie"] = str(racine_copie)
            for source, relatif in iter_target_files(
                chemin, bool(cible.get("recursif", True))
            ):
                copie = racine_copie / relatif
                copie.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, copie)
                empreinte_source = sha256_file(source)
                empreinte_copie = sha256_file(copie)
                if empreinte_source != empreinte_copie:
                    raise RuntimeError(f"copie incoherente: {source} -> {copie}")
                manifeste["fichiers"].append(
                    {
                        "cible_index": index,
                        "cible": str(chemin),
                        "relpath": relatif.as_posix(),
                        "taille": copie.stat().st_size,
                        "mtime_ns": copie.stat().st_mtime_ns,
                        "sha256": empreinte_copie,
                        "copie": str(copie),
                    }
                )
        manifeste["cibles"].append(entree)
    write_json_atomic(destination / "manifest_avant.json", manifeste)
    return manifeste


def verifier_sauvegarde(
    manifeste: dict[str, Any], instantane: list[dict[str, Any]]
) -> list[str]:
    incoherences = []
    for fichier in manifeste.get("fichiers", []):
        index = fichier.get("cible_index")
        if not isinstance(index, int) or not 1 <= index <= len(instantane):
            incoherences.append(f"index de cible invalide: {index}")
            continue
        meta = instantane[index - 1].get("fichiers", {}).get(fichier.get("relpath"))
        if meta is None:
            incoherences.append(f"absent de l'instantane: {fichier.get('relpath')}")
        elif meta.get("sha256") != fichier.get("sha256"):
            incoherences.append(
                f"empreinte differente: {fichier.get('relpath')}"
            )
    return incoherences


class Reporter:
    def __init__(self, max_exemples: int) -> None:
        self.changes = 0
        self.warnings = 0
        self.errors = 0
        self.max_exemples = max(1, max_exemples)

    def change(self, tag: str, message: str) -> None:
        self.changes += 1
        print(f"[{tag}] {message}")

    def attention(self, message: str) -> None:
        self.changes += 1
        print(f"[ATTENTION] {message}")

    def note(self, tag: str, message: str) -> None:
        self.warnings += 1
        print(f"[{tag}] {message}")

    def error(self, message: str) -> None:
        self.errors += 1
        print(f"[ERREUR] {message}")

    def exemple(self, valeurs: Iterable[str]) -> str:
        ordonnees = sorted(str(valeur) for valeur in valeurs)
        montres = ordonnees[: self.max_exemples]
        reste = len(ordonnees) - len(montres)
        texte = ", ".join(montres)
        if reste > 0:
            texte += f", +{reste}"
        return texte

    def exemple_compte(self, comptes: dict[str, int]) -> str:
        elements = [
            f"{signature} (x{compte})" if compte > 1 else signature
            for signature, compte in sorted(comptes.items())
        ]
        montres = elements[: self.max_exemples]
        reste = len(elements) - len(montres)
        texte = ", ".join(montres)
        if reste > 0:
            texte += f", +{reste}"
        return texte


def diff_list(
    relatif: str,
    cle: str,
    ancien: dict[str, Any],
    nouveau: dict[str, Any],
    reporter: Reporter,
) -> None:
    longueur_ancienne = ancien.get("longueur")
    longueur_nouvelle = nouveau.get("longueur")
    if longueur_ancienne != longueur_nouvelle:
        reporter.change(
            "MODIFIE",
            f"{relatif}: liste {cle} longueur {longueur_ancienne} -> {longueur_nouvelle}",
        )
    signatures_anciennes = Counter(ancien.get("signatures", {}))
    signatures_nouvelles = Counter(nouveau.get("signatures", {}))
    manquantes = {
        signature: signatures_anciennes[signature] - signatures_nouvelles.get(signature, 0)
        for signature in signatures_anciennes
        if signatures_anciennes[signature] > signatures_nouvelles.get(signature, 0)
    }
    ajoutees = {
        signature: signatures_nouvelles[signature] - signatures_anciennes.get(signature, 0)
        for signature in signatures_nouvelles
        if signatures_nouvelles[signature] > signatures_anciennes.get(signature, 0)
    }
    if manquantes:
        total = sum(manquantes.values())
        suffixe = (
            " (longueur inchangee: eviction possible)"
            if longueur_ancienne == longueur_nouvelle
            else ""
        )
        reporter.attention(
            f"{relatif}: {total} entree(s) disparue(s) dans {cle}{suffixe}: "
            f"{reporter.exemple_compte(manquantes)}"
        )
    if ajoutees:
        total = sum(ajoutees.values())
        reporter.change(
            "AJOUTE",
            f"{relatif}: {total} entree(s) dans {cle}: "
            f"{reporter.exemple_compte(ajoutees)}",
        )
    sans_ancien = ancien.get("sans_signature", 0)
    sans_nouveau = nouveau.get("sans_signature", 0)
    if sans_ancien != sans_nouveau:
        reporter.change(
            "MODIFIE",
            f"{relatif}: entrees sans signature dans {cle} "
            f"{sans_ancien} -> {sans_nouveau}",
        )
    if (
        longueur_ancienne == longueur_nouvelle
        and not manquantes
        and not ajoutees
        and sans_ancien == sans_nouveau
        and ancien.get("empreinte") != nouveau.get("empreinte")
    ):
        reporter.change(
            "MODIFIE",
            f"{relatif}: contenu de la liste {cle} change (signatures identiques)",
        )


def diff_json(
    relatif: str,
    ancien: dict[str, Any] | None,
    nouveau: dict[str, Any] | None,
    reporter: Reporter,
) -> None:
    if ancien is None or nouveau is None:
        return
    if "erreur" in ancien or "erreur" in nouveau:
        reporter.change("MODIFIE", f"{relatif}: resume JSON illisible avant ou apres")
        return
    avant = reporter.changes
    cles_anciennes = set(ancien.get("cles", []))
    cles_nouvelles = set(nouveau.get("cles", []))
    for cle in sorted(cles_nouvelles - cles_anciennes):
        reporter.change("AJOUTE", f"{relatif}: cle {cle}")
    for cle in sorted(cles_anciennes - cles_nouvelles):
        reporter.change("SUPPRIME", f"{relatif}: cle {cle}")
    types_anciens = ancien.get("type_cles", {})
    types_nouveaux = nouveau.get("type_cles", {})
    scalaires_anciens = ancien.get("scalaires", {})
    scalaires_nouveaux = nouveau.get("scalaires", {})
    dicts_anciens = ancien.get("dict_cles", {})
    dicts_nouveaux = nouveau.get("dict_cles", {})
    listes_anciennes = ancien.get("listes", {})
    listes_nouvelles = nouveau.get("listes", {})
    for cle in sorted(cles_anciennes & cles_nouvelles):
        if types_anciens.get(cle) != types_nouveaux.get(cle):
            reporter.change(
                "MODIFIE",
                f"{relatif}: type de {cle} {types_anciens.get(cle)} -> "
                f"{types_nouveaux.get(cle)}",
            )
            continue
        if cle in scalaires_anciens or cle in scalaires_nouveaux:
            valeur_ancienne = scalaires_anciens.get(cle, "<absent>")
            valeur_nouvelle = scalaires_nouveaux.get(cle, "<absent>")
            if valeur_ancienne != valeur_nouvelle:
                reporter.change(
                    "MODIFIE",
                    f"{relatif}: scalaire {cle} = {valeur_ancienne!r} -> "
                    f"{valeur_nouvelle!r}",
                )
        if cle in dicts_anciens or cle in dicts_nouveaux:
            ancien_dict = dicts_anciens.get(cle, {})
            nouveau_dict = dicts_nouveaux.get(cle, {})
            cles_dict_anciennes = set(ancien_dict.get("cles", []))
            cles_dict_nouvelles = set(nouveau_dict.get("cles", []))
            disparues = cles_dict_anciennes - cles_dict_nouvelles
            ajoutees = cles_dict_nouvelles - cles_dict_anciennes
            if disparues:
                reporter.attention(
                    f"{relatif}: {len(disparues)} cle(s) disparue(s) dans {cle}: "
                    f"{reporter.exemple(disparues)}"
                )
            if ajoutees:
                reporter.change(
                    "AJOUTE",
                    f"{relatif}: {len(ajoutees)} cle(s) dans {cle}: "
                    f"{reporter.exemple(ajoutees)}",
                )
            if (
                not disparues
                and not ajoutees
                and ancien_dict.get("nombre") != nouveau_dict.get("nombre")
            ):
                reporter.change(
                    "MODIFIE",
                    f"{relatif}: nombre de cles dans {cle} "
                    f"{ancien_dict.get('nombre')} -> {nouveau_dict.get('nombre')}",
                )
        if cle in listes_anciennes or cle in listes_nouvelles:
            diff_list(
                relatif,
                cle,
                listes_anciennes.get(cle, {}),
                listes_nouvelles.get(cle, {}),
                reporter,
            )
    if reporter.changes == avant:
        reporter.note(
            "INFO",
            f"{relatif}: SHA different mais resume JSON identique "
            "(changement hors resume)",
        )


def compare_target(
    ancien: dict[str, Any],
    nouveau: dict[str, Any],
    reporter: Reporter,
) -> None:
    chemin_ancien = ancien.get("chemin")
    chemin_nouveau = nouveau.get("chemin")
    if chemin_ancien and chemin_nouveau and norm(chemin_ancien) != norm(chemin_nouveau):
        reporter.note("INFO", f"cible remappee: {chemin_ancien} -> {chemin_nouveau}")
    if ancien.get("existe") != nouveau.get("existe"):
        tag = "AJOUTE" if nouveau.get("existe") else "SUPPRIME"
        reporter.change(tag, f"cible {chemin_nouveau}")
        return
    if not nouveau.get("existe"):
        return
    fichiers_anciens = ancien.get("fichiers", {})
    fichiers_nouveaux = nouveau.get("fichiers", {})
    for relatif in sorted(set(fichiers_anciens) - set(fichiers_nouveaux)):
        reporter.change("SUPPRIME", f"fichier {relatif}")
    for relatif in sorted(set(fichiers_nouveaux) - set(fichiers_anciens)):
        reporter.change("AJOUTE", f"fichier {relatif}")
    for relatif in sorted(set(fichiers_anciens) & set(fichiers_nouveaux)):
        meta_ancien = fichiers_anciens[relatif]
        meta_nouveau = fichiers_nouveaux[relatif]
        if "erreur" in meta_ancien:
            reporter.error(f"{relatif}: {meta_ancien['erreur']} (instantane)")
        if "erreur" in meta_nouveau:
            reporter.error(f"{relatif}: {meta_nouveau['erreur']} (actuel)")
        empreinte_ancienne = meta_ancien.get("sha256")
        empreinte_nouvelle = meta_nouveau.get("sha256")
        if not empreinte_ancienne or not empreinte_nouvelle:
            reporter.error(f"{relatif}: empreinte indisponible")
            continue
        if empreinte_ancienne != empreinte_nouvelle:
            reporter.change(
                "MODIFIE",
                f"fichier {relatif} ({meta_ancien.get('taille')} -> "
                f"{meta_nouveau.get('taille')} octets)",
            )
            if meta_ancien.get("json_resume") or meta_nouveau.get("json_resume"):
                diff_json(
                    relatif,
                    meta_ancien.get("json_resume"),
                    meta_nouveau.get("json_resume"),
                    reporter,
                )
        elif meta_ancien.get("mtime_ns") != meta_nouveau.get("mtime_ns"):
            reporter.note(
                "REECRIT-IDENTIQUE",
                f"fichier {relatif} (contenu identique, mtime change)",
            )


def cmd_instantane(args: argparse.Namespace) -> int:
    if args.stabilite < 0:
        print("[ERREUR] --stabilite doit etre >= 0")
        return 2
    cibles = [
        {
            "chemin": str(Path(chemin).expanduser().resolve()),
            "recursif": bool(args.recursif),
        }
        for chemin in args.cible
    ]
    sortie = Path(args.sortie).expanduser().resolve()
    exclusions = {norm(sortie)}
    instantane = [
        scan_target(Path(cible["chemin"]), cible["recursif"], exclusions)
        for cible in cibles
    ]
    erreurs = scan_errors(instantane)
    instabilite: list[str] = []
    stable = True
    if args.stabilite > 0:
        time.sleep(args.stabilite)
        second = [
            scan_target(Path(cible["chemin"]), cible["recursif"], exclusions)
            for cible in cibles
        ]
        instabilite = compare_scans(instantane, second)
        if instabilite:
            stable = False
            instantane = second
            erreurs = scan_errors(instantane)
    manifeste = None
    if args.sauvegarder:
        try:
            manifeste = backup_targets(cibles, Path(args.sauvegarder))
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"[ERREUR] sauvegarde impossible: {exc}")
            return 2
        incoherences = verifier_sauvegarde(manifeste, instantane)
        if incoherences:
            stable = False
            instabilite.extend(incoherences)
    donnees = {
        "version": VERSION,
        "outil": "instantane_effets_de_bord.py",
        "horodatage_utc": utc_now(),
        "stable": stable,
        "instabilite": instabilite,
        "cibles": instantane,
    }
    try:
        write_json_atomic(sortie, donnees, force=args.force)
    except (OSError, FileExistsError) as exc:
        print(f"[ERREUR] instantane non ecrit: {exc}")
        return 2
    total_fichiers = sum(len(cible.get("fichiers", {})) for cible in instantane)
    total_json = sum(
        1
        for cible in instantane
        for meta in cible.get("fichiers", {}).values()
        if "json_resume" in meta
    )
    print(f"[OK] instantane: {total_fichiers} fichier(s), {total_json} JSON")
    print(f"[OK] sortie: {sortie}")
    if manifeste is not None:
        copie = Path(args.sauvegarder).expanduser().resolve() / "manifest_avant.json"
        print(
            f"[OK] sauvegarde: {len(manifeste.get('fichiers', []))} fichier(s), "
            f"manifeste {copie}"
        )
    if stable and not erreurs:
        print("RESULT: OK")
        return 0
    if not stable:
        for detail in instabilite[:20]:
            print(f"[INSTABLE] {detail}")
        if len(instabilite) > 20:
            print(f"[INSTABLE] ... (+{len(instabilite) - 20})")
    for erreur in erreurs[:20]:
        print(f"[ERREUR] {erreur}")
    if len(erreurs) > 20:
        print(f"[ERREUR] ... (+{len(erreurs) - 20})")
    print("RESULT: INSTABLE" if not stable else "RESULT: ERREUR")
    return 2


def cmd_comparer(args: argparse.Namespace) -> int:
    if args.stabilite < 0:
        print("[ERREUR] --stabilite doit etre >= 0")
        return 2
    source = Path(args.instantane).expanduser().resolve()
    try:
        donnees = json.loads(source.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"[ERREUR] instantane illisible: {exc}")
        print("RESULT: ERREUR")
        return 2
    if not isinstance(donnees, dict) or donnees.get("version") != VERSION:
        print("[ERREUR] format d'instantane non reconnu")
        print("RESULT: ERREUR")
        return 2
    if donnees.get("stable") is False:
        print("[ERREUR] instantane de reference marque instable: comparaison refusee")
        print("RESULT: ERREUR")
        return 2
    cibles_anciennes = donnees.get("cibles")
    if not isinstance(cibles_anciennes, list) or not cibles_anciennes:
        print("[ERREUR] instantane sans cible")
        print("RESULT: ERREUR")
        return 2
    if args.cible:
        if len(args.cible) != len(cibles_anciennes):
            print("[ERREUR] le nombre de --cible ne correspond pas a l'instantane")
            print("RESULT: ERREUR")
            return 2
        specifications = [
            {
                "chemin": str(Path(chemin).expanduser().resolve()),
                "recursif": bool(cible.get("recursif", True)),
            }
            for chemin, cible in zip(args.cible, cibles_anciennes)
        ]
    else:
        specifications = [
            {
                "chemin": str(cible.get("chemin")),
                "recursif": bool(cible.get("recursif", True)),
            }
            for cible in cibles_anciennes
        ]
    exclusions = {norm(source)}
    cibles_nouvelles = [
        scan_target(Path(cible["chemin"]), cible["recursif"], exclusions)
        for cible in specifications
    ]
    if args.stabilite > 0:
        time.sleep(args.stabilite)
        second = [
            scan_target(Path(cible["chemin"]), cible["recursif"], exclusions)
            for cible in specifications
        ]
        instabilite = compare_scans(cibles_nouvelles, second)
        if instabilite:
            for detail in instabilite[:20]:
                print(f"[INSTABLE] {detail}")
            if len(instabilite) > 20:
                print(f"[INSTABLE] ... (+{len(instabilite) - 20})")
            print("RESULT: INSTABLE")
            return 2
        cibles_nouvelles = second
    reporter = Reporter(args.max_exemples)
    for ancien, nouveau in zip(cibles_anciennes, cibles_nouvelles):
        compare_target(ancien, nouveau, reporter)
    for erreur in scan_errors(cibles_nouvelles):
        reporter.error(erreur)
    if reporter.errors:
        print(
            f"RESULT: ERREUR ({reporter.errors} erreur(s), "
            f"{reporter.changes} changement(s))"
        )
        return 2
    if reporter.changes:
        print(
            f"RESULT: CHANGEMENTS ({reporter.changes} changement(s), "
            f"{reporter.warnings} avertissement(s))"
        )
        return 1
    if reporter.warnings:
        print(f"RESULT: OK ({reporter.warnings} avertissement(s))")
    else:
        print("RESULT: OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Instantane et comparaison en lecture seule des effets de bord. "
            "Les cibles ne sont jamais modifiees."
        )
    )
    sous = parser.add_subparsers(dest="commande", required=True)
    instantane = sous.add_parser(
        "instantane",
        help="enregistrer l'etat avant execution et, si demande, le sauvegarder",
    )
    instantane.add_argument(
        "--cible",
        action="append",
        required=True,
        help="fichier ou repertoire a observer ; repetable",
    )
    instantane.add_argument(
        "--recursif",
        action="store_true",
        help="parcourir les sous-repertoires de chaque cible",
    )
    instantane.add_argument(
        "--stabilite",
        type=float,
        default=0.0,
        help="delai en secondes avant une seconde lecture (0 = desactive)",
    )
    instantane.add_argument(
        "--sortie",
        required=True,
        help="fichier JSON d'instantane a ecrire",
    )
    instantane.add_argument(
        "--sauvegarder",
        help="repertoire de sauvegarde (hors des cibles) avec manifest_avant.json",
    )
    instantane.add_argument(
        "--force",
        action="store_true",
        help="ecraser un instantane existant",
    )
    comparer = sous.add_parser(
        "comparer",
        help="comparer l'etat actuel a un instantane",
    )
    comparer.add_argument(
        "--instantane",
        required=True,
        help="fichier JSON produit par la commande instantane",
    )
    comparer.add_argument(
        "--cible",
        action="append",
        help="remplacer une cible enregistree ; repetable, meme nombre",
    )
    comparer.add_argument(
        "--stabilite",
        type=float,
        default=0.0,
        help="delai en secondes avant une seconde lecture (0 = desactive)",
    )
    comparer.add_argument(
        "--max-exemples",
        type=int,
        default=5,
        help="nombre d'exemples affiches par categorie (defaut: 5)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
    args = build_parser().parse_args(argv)
    if args.commande == "instantane":
        return cmd_instantane(args)
    return cmd_comparer(args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
    except Exception as exc:
        print(f"[ERREUR] {type(exc).__name__}: {exc}")
        sys.exit(2)
