#!/usr/bin/env python3
"""Auto-test isole de instantane_effets_de_bord.py.

Rejoue les contrats documentes sur des fixtures jetables, puis compare le
script courant a une copie privee des alias de schema. Ne lit ni n'ecrit le
memoire_aq reel. La sortie est ASCII pour rester lisible sur une console
Windows non UTF-8.

Codes de sortie :
  0  tous les controles passent
  1  au moins un controle echoue
  2  environnement invalide, script introuvable ou exception non geree

Usage :
  py -3 scripts/tester_instantane.py
  py -3 scripts/tester_instantane.py --script <autre copie> --garder
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
DEFAULT_SCRIPT = SCRIPT_DIR / "instantane_effets_de_bord.py"

TOTAL = 0
ECHECS = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global TOTAL, ECHECS
    TOTAL += 1
    if condition:
        print(f"[OK] {label}")
        return
    ECHECS += 1
    print(f"[ECHEC] {label}")
    if detail:
        extrait = detail.strip().replace("\r", "")
        if len(extrait) > 1600:
            extrait = extrait[:1600] + " ..."
        print("  " + extrait.replace("\n", "\n  "))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def make_entry(index: int) -> dict[str, Any]:
    return {
        "chemin_fichier": (
            "C:\\Users\\Administrateur\\Desktop\\IMAM8MAHDI\\"
            f"module_{index:03d}.py"
        ),
        "lignes_totales": 10 + index,
        "arbre_ast_valide": True,
        "respect_bride_mizan": True,
        "respect_anti_riba": True,
        "respect_killswitch_cryo": True,
        "detecte_fragmentation": False,
        "score_harmonie_100": 90.0 + (index % 10),
        "empreinte_sha256": hashlib.sha256(
            f"module-{index}".encode("utf-8")
        ).hexdigest(),
        "recommandations_harmonisation": [],
        "horodatage_iso": f"2026-10-26T12:{index // 60:02d}:{index % 60:02d}Z",
    }


def make_journal(entrees: int) -> dict[str, Any]:
    return {
        "agent": "AGENT_CODE_HARMONISATEUR_AL_MIZAN",
        "date_creation_iso": "2026-10-26T12:00:00Z",
        "total_fichiers_harmonises": entrees,
        "journal": [make_entry(index) for index in range(entrees)],
    }


def make_index(sceaux: int) -> dict[str, Any]:
    contenu = {}
    for index in range(sceaux):
        nom = chr(ord("a") + index)
        cle = nom * 64
        contenu[cle] = {
            "timestamp": f"2026-10-26T12:00:0{index}",
            "empreinte_sha256": cle,
            "chemin": f"memoire_aq/seal_{nom}.json",
        }
    return {
        "sceaux": contenu,
        "derniere_mise_a_jour": "2026-10-26T12:00:00",
        "nb_sceaux": sceaux,
        "qubit_physique_local": {},
        "completude_pourcent": 100.0,
    }


def make_bloc(index: int) -> dict[str, Any]:
    return {
        "height": 250 + index,
        "timestamp_utc": (
            f"2026-10-26T12:{index // 60:02d}:{index % 60:02d}.{index:06d}+00:00"
        ),
        "kernel_dt": 1.5,
        "prev_hash": hashlib.sha256(f"prev-{index}".encode("utf-8")).hexdigest()[:60],
        "bloc_hash": hashlib.sha256(f"bloc-{index}".encode("utf-8")).hexdigest()[:60],
        "latence_sync_ref_ms": 2.9,
        "transactions": [],
        "sceaux": [],
        "invariants": {"mizan": 0.5, "epsilon": 0.02},
    }


def make_ledger(blocs: int) -> dict[str, Any]:
    return {
        "nom": "LEDGER_SYNCHRON_AL_MIZAN",
        "auteur": "AL-MIZAN",
        "blocs": [make_bloc(index) for index in range(blocs)],
        "nb_blocs": blocs,
        "derniere_mise_a_jour": "2026-10-26T12:00:00+00:00",
    }


def make_fixture(root: Path) -> Path:
    fixture = root / "memoire_aq"
    fixture.mkdir(parents=True)
    write_json(fixture / "index_sceaux_astro_qode.json", make_index(2))
    write_json(
        fixture / "almizan_journal_agent_de_code.json",
        make_journal(100),
    )
    write_json(fixture / "seal_a.json", {"nom": "a", "payload": "alpha"})
    write_json(fixture / "seal_b.json", {"nom": "b", "payload": "beta"})
    return fixture


def run_script(script: Path, args: list[str]) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [sys.executable, "-B", str(script), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        env=env,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def snapshot(
    script: Path,
    cible: Path,
    sortie: Path,
    sauvegarder: Path | None = None,
    stabilite: str = "0",
    force: bool = False,
) -> tuple[int, str]:
    args = [
        "instantane",
        "--cible",
        str(cible),
        "--recursif",
        "--stabilite",
        stabilite,
        "--sortie",
        str(sortie),
    ]
    if sauvegarder is not None:
        args.extend(["--sauvegarder", str(sauvegarder)])
    if force:
        args.append("--force")
    return run_script(script, args)


def comparer(
    script: Path,
    instantane: Path,
    stabilite: str = "0",
    max_exemples: int | None = None,
) -> tuple[int, str]:
    args = [
        "comparer",
        "--instantane",
        str(instantane),
        "--stabilite",
        stabilite,
    ]
    if max_exemples is not None:
        args.extend(["--max-exemples", str(max_exemples)])
    return run_script(script, args)


def journal_resume(data: Any) -> dict[str, Any]:
    try:
        fichiers = data["cibles"][0]["fichiers"]
        return fichiers["almizan_journal_agent_de_code.json"]["json_resume"][
            "listes"
        ]["journal"]
    except (KeyError, IndexError, TypeError):
        return {}


def index_resume(data: Any) -> dict[str, Any]:
    try:
        fichiers = data["cibles"][0]["fichiers"]
        return fichiers["index_sceaux_astro_qode.json"]["json_resume"]
    except (KeyError, IndexError, TypeError):
        return {}


def ledger_resume(data: Any) -> dict[str, Any]:
    try:
        fichiers = data["cibles"][0]["fichiers"]
        return fichiers["ledger_synchron_mzn.json"]["json_resume"]["listes"][
            "blocs"
        ]
    except (KeyError, IndexError, TypeError):
        return {}


def signatures_count(resume: dict[str, Any]) -> int:
    signatures = resume.get("signatures")
    if not isinstance(signatures, dict):
        return 0
    return sum(int(valeur) for valeur in signatures.values())


def make_old_copy(source: Path, destination: Path) -> bool:
    text = source.read_text(encoding="utf-8")
    anciens_ts = (
        'TS_KEYS = ("horodatage", "horodatage_utc", "timestamp", '
        '"date", "ts")'
    )
    anciens_fichiers = (
        'FILE_KEYS = ("fichier", "file", "chemin", "path", "nom_fichier")'
    )
    nouveau, n_ts = re.subn(
        r"^TS_KEYS\s*=\s*\([^)]*\)",
        anciens_ts,
        text,
        count=1,
        flags=re.MULTILINE,
    )
    nouveau, n_fichiers = re.subn(
        r"^FILE_KEYS\s*=\s*\([^)]*\)",
        anciens_fichiers,
        nouveau,
        count=1,
        flags=re.MULTILINE,
    )
    if n_ts != 1 or n_fichiers != 1:
        raise RuntimeError("lignes TS_KEYS/FILE_KEYS introuvables ou multiples")
    destination.write_text(nouveau, encoding="utf-8")
    return hashlib.sha256(nouveau.encode("utf-8")).hexdigest() != hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def start_writer(path: Path, stop: threading.Event) -> threading.Thread:
    def boucle() -> None:
        compteur = 0
        while not stop.is_set():
            try:
                path.write_text(
                    f"{time.time_ns()}-{compteur}\n",
                    encoding="utf-8",
                )
            except OSError:
                pass
            compteur += 1
            stop.wait(0.03)

    thread = threading.Thread(target=boucle, daemon=True)
    thread.start()
    return thread


def test_snapshot_and_backup(script: Path, tmp: Path) -> None:
    case = tmp / "cas_base"
    fixture = make_fixture(case)
    sortie = case / "instantane_avant.json"
    sauvegarde = case / "avant"
    rc, out = snapshot(script, fixture, sortie, sauvegarde, stabilite="0.2")
    check("instantane exit 0", rc == 0, out)
    check("instantane RESULT OK", "RESULT: OK" in out, out)
    data = read_json(sortie) if sortie.exists() else {}
    check("instantane version 1", data.get("version") == 1, str(data)[:800])
    check("instantane stable", data.get("stable") is True, str(data)[:800])
    fichiers = {}
    try:
        fichiers = data["cibles"][0]["fichiers"]
    except (KeyError, IndexError, TypeError):
        pass
    check("instantane 4 fichiers", len(fichiers) == 4, str(fichiers)[:800])
    check(
        "instantane taille mtime sha256",
        bool(fichiers)
        and all(
            meta.get("taille") is not None
            and meta.get("mtime_ns") is not None
            and bool(meta.get("sha256"))
            for meta in fichiers.values()
        ),
        str(fichiers)[:800],
    )
    journal = journal_resume(data)
    check(
        "journal longueur 100",
        journal.get("longueur") == 100,
        str(journal)[:800],
    )
    check(
        "journal 100 signatures",
        signatures_count(journal) == 100,
        str(journal)[:800],
    )
    check(
        "journal sans_signature 0",
        journal.get("sans_signature") == 0,
        str(journal)[:800],
    )
    check("journal empreinte", bool(journal.get("empreinte")), str(journal)[:800])
    index = index_resume(data)
    try:
        nombre_sceaux = index["dict_cles"]["sceaux"]["nombre"]
    except (KeyError, TypeError):
        nombre_sceaux = None
    check("index sceaux 2", nombre_sceaux == 2, str(index)[:800])
    try:
        nb_sceaux = index["scalaires"]["nb_sceaux"]
    except (KeyError, TypeError):
        nb_sceaux = None
    check("index nb_sceaux 2", nb_sceaux == 2, str(index)[:800])
    manifeste_path = sauvegarde / "manifest_avant.json"
    manifeste = read_json(manifeste_path) if manifeste_path.exists() else {}
    manifeste_fichiers = manifeste.get("fichiers", [])
    check(
        "manifeste 4 fichiers",
        len(manifeste_fichiers) == 4,
        str(manifeste)[:800],
    )
    correspondances = all(
        any(
            entree.get("relpath") == relatif
            and entree.get("sha256") == meta.get("sha256")
            for entree in manifeste_fichiers
        )
        for relatif, meta in fichiers.items()
        if meta.get("sha256")
    )
    check(
        "manifeste empreintes concordantes",
        bool(fichiers) and correspondances,
        str(manifeste)[:800],
    )


def test_cli_guards(script: Path, tmp: Path) -> None:
    case = tmp / "cas_guards"
    fixture = make_fixture(case)
    sortie = case / "snap.json"
    rc, out = snapshot(script, fixture, sortie, stabilite="0")
    check("garde instantane de base", rc == 0, out)
    rc, out = run_script(
        script,
        [
            "instantane",
            "--cible",
            str(fixture),
            "--recursif",
            "--sortie",
            str(case / "interdit.json"),
            "--sauvegarder",
            str(fixture / "backup"),
        ],
    )
    check("sauvegarde dans la cible refusee", rc == 2, out)
    check(
        "message sauvegarde dans la cible",
        "ne doit pas etre dans la cible" in out,
        out,
    )
    rc, out = run_script(
        script,
        [
            "instantane",
            "--cible",
            str(fixture),
            "--recursif",
            "--sortie",
            str(sortie),
        ],
    )
    check("ecrasement sans --force refuse", rc == 2, out)
    rc, out = run_script(
        script,
        [
            "instantane",
            "--cible",
            str(fixture),
            "--recursif",
            "--sortie",
            str(sortie),
            "--force",
        ],
    )
    check("ecrasement avec --force accepte", rc == 0, out)
    rc, out = run_script(
        script,
        [
            "instantane",
            "--cible",
            str(fixture),
            "--sortie",
            str(case / "negatif.json"),
            "--stabilite",
            "-1",
        ],
    )
    check("stabilite negative refusee", rc == 2, out)


def test_index_schema(script: Path, tmp: Path) -> None:
    case = tmp / "cas_index"
    fixture = make_fixture(case)
    sortie = case / "snap.json"
    rc, out = snapshot(script, fixture, sortie, stabilite="0")
    check("index instantane de base", rc == 0, out)
    index_path = fixture / "index_sceaux_astro_qode.json"
    index = read_json(index_path)
    nouvelle_cle = "c" * 64
    index["sceaux"][nouvelle_cle] = {
        "timestamp": "2026-10-26T12:00:09",
        "empreinte_sha256": nouvelle_cle,
        "chemin": "memoire_aq/seal_c.json",
    }
    index["nb_sceaux"] = 3
    write_json(index_path, index)
    rc, out = comparer(script, sortie)
    check("index ajout de cle exit 1", rc == 1, out)
    check(
        "index ajout de cle signale",
        "AJOUTE" in out and nouvelle_cle in out,
        out,
    )
    check(
        "index scalaire nb_sceaux signale",
        "nb_sceaux = 2 -> 3" in out,
        out,
    )


def test_files(script: Path, tmp: Path) -> None:
    case = tmp / "cas_fichiers"
    fixture = make_fixture(case)
    sortie = case / "snap.json"
    rc, out = snapshot(script, fixture, sortie, stabilite="0")
    check("fichiers instantane de base", rc == 0, out)
    write_json(fixture / "seal_c.json", {"nom": "c", "payload": "gamma"})
    rc, out = comparer(script, sortie)
    check("fichier ajoute exit 1", rc == 1, out)
    check(
        "fichier ajoute signale",
        "AJOUTE" in out and "seal_c.json" in out,
        out,
    )
    sortie2 = case / "snap2.json"
    rc, out = snapshot(script, fixture, sortie2, stabilite="0")
    check("fichiers second instantane", rc == 0, out)
    (fixture / "seal_b.json").unlink()
    rc, out = comparer(script, sortie2)
    check("fichier supprime exit 1", rc == 1, out)
    check(
        "fichier supprime signale",
        "SUPPRIME" in out and "seal_b.json" in out,
        out,
    )


def test_rewrite_identical(script: Path, tmp: Path) -> None:
    case = tmp / "cas_reecriture"
    fixture = make_fixture(case)
    sortie = case / "snap.json"
    rc, out = snapshot(script, fixture, sortie, stabilite="0")
    check("reecriture instantane de base", rc == 0, out)
    cible = fixture / "seal_a.json"
    stat = cible.stat()
    os.utime(
        cible,
        ns=(stat.st_atime_ns + 1_000_000_000, stat.st_mtime_ns + 1_000_000_000),
    )
    rc, out = comparer(script, sortie)
    check("reecriture identique exit 0", rc == 0, out)
    check("reecriture identique signalee", "REECRIT-IDENTIQUE" in out, out)
    check("reecriture result OK", "RESULT: OK" in out, out)


def test_eviction(script: Path, tmp: Path) -> None:
    case = tmp / "cas_eviction"
    fixture = make_fixture(case)
    sortie = case / "snap.json"
    rc, out = snapshot(script, fixture, sortie, stabilite="0")
    check("eviction instantane de base", rc == 0, out)
    journal_path = fixture / "almizan_journal_agent_de_code.json"
    texte_original = journal_path.read_text(encoding="utf-8")
    donnees = read_json(journal_path)
    entrees = donnees["journal"]
    debut = len(entrees)
    entrees.extend(make_entry(debut + index) for index in range(5))
    donnees["journal"] = entrees[-100:]
    donnees["total_fichiers_harmonises"] = len(donnees["journal"])
    write_json(journal_path, donnees)
    rc, out = comparer(script, sortie, max_exemples=2)
    check("eviction exit 1", rc == 1, out)
    check(
        "eviction 5 entrees disparues",
        "[ATTENTION]" in out and "5 entree(s) disparue(s)" in out,
        out,
    )
    check(
        "eviction longueur inchangee",
        "longueur inchangee: eviction possible" in out,
        out,
    )
    check(
        "eviction 5 entrees ajoutees",
        "[AJOUTE]" in out and "5 entree(s) dans journal" in out,
        out,
    )
    check(
        "eviction signatures anciennes nommees",
        "module_000.py" in out and "module_001.py" in out,
        out,
    )
    check("eviction max-exemples tronque", "+3" in out, out)
    journal_path.write_text(texte_original, encoding="utf-8")
    rc, out = comparer(script, sortie)
    check(
        "eviction restauree exit 0",
        rc == 0 and "RESULT: OK" in out,
        out,
    )


def test_ledger_eviction(script: Path, tmp: Path) -> None:
    case = tmp / "cas_ledger"
    fixture = make_fixture(case)
    ledger_path = fixture / "ledger_synchron_mzn.json"
    write_json(ledger_path, make_ledger(100))
    sortie = case / "snap.json"
    rc, out = snapshot(script, fixture, sortie, stabilite="0")
    check("ledger instantane exit 0", rc == 0, out)
    donnees_snapshot = read_json(sortie) if sortie.exists() else {}
    resume = ledger_resume(donnees_snapshot)
    check(
        "ledger 100 signatures timestamp_utc",
        signatures_count(resume) == 100,
        str(resume)[:800],
    )
    check(
        "ledger 0 sans signature",
        resume.get("sans_signature") == 0,
        str(resume)[:800],
    )
    ancien = case / "instantane_sans_alias.py"
    check(
        "ledger copie negative modifiee",
        make_old_copy(script, ancien),
        "la copie negative est identique au script courant",
    )
    ancienne_sortie = case / "snap_ancien.json"
    rc, out = snapshot(ancien, fixture, ancienne_sortie, stabilite="0")
    anciennes_donnees = (
        read_json(ancienne_sortie) if ancienne_sortie.exists() else {}
    )
    check(
        "ledger copie negative 0 signature",
        signatures_count(ledger_resume(anciennes_donnees)) == 0,
        str(ledger_resume(anciennes_donnees))[:800],
    )
    original = ledger_path.read_text(encoding="utf-8")
    donnees = read_json(ledger_path)
    blocs = donnees["blocs"]
    debut = len(blocs)
    blocs.extend(make_bloc(debut + index) for index in range(5))
    donnees["blocs"] = blocs[-100:]
    donnees["nb_blocs"] = 105
    write_json(ledger_path, donnees)
    rc, out = comparer(script, sortie, max_exemples=2)
    check("ledger eviction exit 1", rc == 1, out)
    check(
        "ledger 5 blocs disparus",
        "[ATTENTION]" in out and "5 entree(s) disparue(s) dans blocs" in out,
        out,
    )
    check(
        "ledger longueur inchangee",
        "longueur inchangee: eviction possible" in out,
        out,
    )
    rc, out = comparer(ancien, ancienne_sortie)
    check("ledger copie negative ignore l'eviction", "[ATTENTION]" not in out, out)
    ledger_path.write_text(original, encoding="utf-8")
    rc, out = comparer(script, sortie)
    check(
        "ledger restaure exit 0",
        rc == 0 and "RESULT: OK" in out,
        out,
    )


def test_absent(script: Path, tmp: Path) -> None:
    case = tmp / "cas_absent"
    absent = case / "absent"
    sortie = case / "snap.json"
    rc, out = snapshot(script, absent, sortie, stabilite="0")
    check("cible absente instantane exit 0", rc == 0, out)
    data = read_json(sortie) if sortie.exists() else {}
    try:
        existe = data["cibles"][0]["existe"]
    except (KeyError, IndexError, TypeError):
        existe = None
    check("cible absente enregistree", existe is False, str(data)[:800])
    absent.mkdir(parents=True)
    (absent / "nouveau.txt").write_text("x\n", encoding="utf-8")
    rc, out = comparer(script, sortie)
    check("cible apparue exit 1", rc == 1, out)
    check(
        "cible apparue signalee",
        "AJOUTE" in out and "cible" in out,
        out,
    )


def test_corrupt(script: Path, tmp: Path) -> None:
    case = tmp / "cas_corrompu"
    fixture = make_fixture(case)
    invalide = case / "invalide.json"
    invalide.write_text("{pas du json", encoding="utf-8")
    rc, out = comparer(script, invalide)
    check("instantane illisible exit 2", rc == 2, out)
    check("instantane illisible message", "instantane illisible" in out, out)
    version = case / "version.json"
    write_json(version, {"version": 999})
    rc, out = comparer(script, version)
    check("version inconnue exit 2", rc == 2, out)
    instable = case / "instable.json"
    write_json(
        instable,
        {
            "version": 1,
            "stable": False,
            "cibles": [
                {
                    "chemin": str(fixture),
                    "recursif": True,
                    "fichiers": {},
                }
            ],
        },
    )
    rc, out = comparer(script, instable)
    check("instantane instable refuse", rc == 2, out)
    check("instantane instable message", "instable" in out.lower(), out)


def test_unstable(script: Path, tmp: Path) -> None:
    case = tmp / "cas_instable"
    fixture = make_fixture(case)
    bruit = fixture / "bruit.txt"
    bruit.write_text("0\n", encoding="utf-8")
    arret = threading.Event()
    ecrivain = start_writer(bruit, arret)
    try:
        rc, out = snapshot(
            script,
            fixture,
            case / "snap_instable.json",
            stabilite="0.6",
        )
    finally:
        arret.set()
        ecrivain.join(timeout=5)
    check("ecrivain concurrent instantane exit 2", rc == 2, out)
    check("ecrivain concurrent RESULT INSTABLE", "RESULT: INSTABLE" in out, out)
    sortie_stable = case / "snap_stable.json"
    rc, out = snapshot(script, fixture, sortie_stable, stabilite="0")
    check("instantane stable de reference", rc == 0, out)
    arret2 = threading.Event()
    ecrivain2 = start_writer(bruit, arret2)
    try:
        rc, out = comparer(script, sortie_stable, stabilite="0.6")
    finally:
        arret2.set()
        ecrivain2.join(timeout=5)
    check("ecrivain concurrent comparer exit 2", rc == 2, out)
    check("ecrivain concurrent comparer INSTABLE", "RESULT: INSTABLE" in out, out)


def test_ab(script: Path, tmp: Path) -> None:
    case = tmp / "cas_ab"
    fixture = make_fixture(case)
    ancien = case / "instantane_sans_alias.py"
    check(
        "copie negative modifiee",
        make_old_copy(script, ancien),
        "la copie negative est identique au script courant",
    )
    ancienne_sortie = case / "snap_ancien.json"
    rc, out = snapshot(ancien, fixture, ancienne_sortie, stabilite="0")
    check("copie negative instantane exit 0", rc == 0, out)
    anciennes_donnees = (
        read_json(ancienne_sortie) if ancienne_sortie.exists() else {}
    )
    ancien_journal = journal_resume(anciennes_donnees)
    check(
        "copie negative 0 signature",
        signatures_count(ancien_journal) == 0,
        str(ancien_journal)[:800],
    )
    check(
        "copie negative 100 sans signature",
        ancien_journal.get("sans_signature") == 100,
        str(ancien_journal)[:800],
    )
    courante_sortie = case / "snap_courant.json"
    rc, out = snapshot(script, fixture, courante_sortie, stabilite="0")
    check("script courant instantane exit 0", rc == 0, out)
    courantes_donnees = (
        read_json(courante_sortie) if courante_sortie.exists() else {}
    )
    courant_journal = journal_resume(courantes_donnees)
    check(
        "script courant 100 signatures",
        signatures_count(courant_journal) == 100,
        str(courant_journal)[:800],
    )
    check(
        "script courant 0 sans signature",
        courant_journal.get("sans_signature") == 0,
        str(courant_journal)[:800],
    )
    journal_path = fixture / "almizan_journal_agent_de_code.json"
    donnees = read_json(journal_path)
    entrees = donnees["journal"]
    debut = len(entrees)
    entrees.extend(make_entry(debut + index) for index in range(5))
    donnees["journal"] = entrees[-100:]
    donnees["total_fichiers_harmonises"] = len(donnees["journal"])
    write_json(journal_path, donnees)
    rc, out = comparer(ancien, ancienne_sortie)
    check(
        "copie negative ne signale pas l'eviction",
        "[ATTENTION]" not in out,
        out,
    )
    check(
        "copie negative contenu change seulement",
        "contenu de la liste journal change (signatures identiques)" in out,
        out,
    )
    rc, out = comparer(script, courante_sortie)
    check(
        "script courant signale l'eviction",
        "[ATTENTION]" in out and "5 entree(s) disparue(s)" in out,
        out,
    )
    check(
        "script courant conserve le nombre d'ajouts",
        "[AJOUTE]" in out and "5 entree(s) dans journal" in out,
        out,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Auto-test isole de instantane_effets_de_bord.py ; "
            "ne touche pas au memoire_aq reel."
        )
    )
    parser.add_argument(
        "--script",
        default=str(DEFAULT_SCRIPT),
        help="script a tester (defaut: instantane_effets_de_bord.py voisin)",
    )
    parser.add_argument(
        "--tmp-root",
        default=None,
        help="racine des fixtures jetables (defaut: repertoire temporaire)",
    )
    parser.add_argument(
        "--garder",
        action="store_true",
        help="conserver la fixture si au moins un controle echoue",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    global TOTAL, ECHECS
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, OSError):
        pass
    args = build_parser().parse_args(argv)
    script = Path(args.script).expanduser().resolve()
    if not script.is_file():
        print(f"[ERREUR] script introuvable: {script}")
        return 2
    tmp = Path(
        tempfile.mkdtemp(
            prefix="verifier-effets-selftest-",
            dir=args.tmp_root,
        )
    )
    print(f"[INFO] fixture: {tmp}")
    print(f"[INFO] script: {script}")
    try:
        test_snapshot_and_backup(script, tmp)
        test_cli_guards(script, tmp)
        test_index_schema(script, tmp)
        test_files(script, tmp)
        test_rewrite_identical(script, tmp)
        test_eviction(script, tmp)
        test_ledger_eviction(script, tmp)
        test_absent(script, tmp)
        test_corrupt(script, tmp)
        test_unstable(script, tmp)
        test_ab(script, tmp)
    except Exception as exc:
        TOTAL += 1
        ECHECS += 1
        print(f"[ECHEC] exception non geree: {type(exc).__name__}: {exc}")
    finally:
        if args.garder and ECHECS:
            print(f"[INFO] fixture conservee: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    check(
        "fixture supprimee sans residu",
        not tmp.exists() or (args.garder and ECHECS > 0),
        str(tmp),
    )
    check(
        "aucun __pycache__ dans le Skill",
        not any(SKILL_ROOT.rglob("__pycache__")),
        str(SKILL_ROOT),
    )
    check(
        "aucun .pyc dans le Skill",
        not any(SKILL_ROOT.rglob("*.pyc")),
        str(SKILL_ROOT),
    )
    print(f"RESULT: TOTAL={TOTAL} ECHECS={ECHECS}")
    return 0 if ECHECS == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(2)
    except Exception as exc:
        print(f"[ERREUR] {type(exc).__name__}: {exc}")
        sys.exit(2)
