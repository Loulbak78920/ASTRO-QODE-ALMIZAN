# -*- coding: utf-8 -*-
"""Prouver un harnais de mutation sur un oracle jetable.

Usage :
    py -3 jouer_oracle.py --harnais CHEMIN/prouver_gardes.py [--garder] [--delai 120]

Le harnais doit emettre des lignes « CAS <nom> <VERDICT> exit=... garde=... »
et une ligne « RESULT: PASS|FAIL ». Le script genere hors du Skill un faux
verificateur a trois gardes et quatre fichiers de cas, execute le harnais une
fois par fichier, puis exige cinq verdicts : POSITIF_OK, GARDE_DECLENCHE,
NON_APPLIQUE, MAUVAISE_RAISON et POSITIF_CASSE. GARDE_VACUE n'est pas couvert
ici : il exige une sonde manuelle, voir SKILL.md etape 5.

Sortie : lignes KEY=VAL, RESULT: PASS|FAIL. Exit 0 conforme, 1 ecart, 2 usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

VERDICTS = (
    "POSITIF_OK",
    "GARDE_DECLENCHE",
    "GARDE_VACUE",
    "NON_APPLIQUE",
    "MAUVAISE_RAISON",
    "POSITIF_CASSE",
    "ERREUR_EXECUTION",
)
VERDICTS_ATTENDUS = {
    "POSITIF_OK",
    "GARDE_DECLENCHE",
    "NON_APPLIQUE",
    "MAUVAISE_RAISON",
    "POSITIF_CASSE",
}
MOTIF_CAS = re.compile(r"^CAS (\S+) (\S+) exit=(\S+) garde=(\S+)$")

TOY = '''# -*- coding: utf-8 -*-
from pathlib import Path
import sys


def cible(argument):
    chemin = Path(argument)
    return chemin / "toy.txt" if chemin.is_dir() else chemin


def main():
    lignes = []
    for brute in cible(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        ligne = brute.strip()
        if ligne and not ligne.startswith("#"):
            lignes.append(ligne)
    texte = "\\n".join(lignes)

    fautifs = {}
    if "ALPHA" not in texte:
        fautifs["alpha"] = "ALPHA absent"
    if "BETA" in texte:
        fautifs["beta"] = "BETA interdit"
    if "GAMMA=ok" not in texte:
        fautifs["gamma"] = "GAMMA non ok"

    for nom in ("alpha", "beta", "gamma"):
        if nom in fautifs:
            print("GARDE FAIL " + nom)
            print("  DETAIL " + fautifs[nom])
        else:
            print("GARDE ok " + nom)

    if fautifs:
        print("RESULT: FAIL controles=3 echecs=" + str(len(fautifs)))
        return 1
    print("RESULT: PASS controles=3 echecs=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

TOY_NAIF = '''# -*- coding: utf-8 -*-
from pathlib import Path
import sys

_ = Path(sys.argv[1]).read_text(encoding="utf-8")
print("GARDE ok alpha")
print("RESULT: PASS controles=1 echecs=0")
'''

ATTENDUS = {
    "ok": {
        "rc": 0,
        "result": "RESULT: PASS",
        "verdicts": {"POSITIF_OK": 1, "GARDE_DECLENCHE": 3},
        "contient": [],
    },
    "non_applique": {
        "rc": 1,
        "result": "RESULT: FAIL",
        "verdicts": {"POSITIF_OK": 1, "NON_APPLIQUE": 1},
        "contient": ["CAUSE occurrences=0"],
    },
    "mauvaise": {
        "rc": 1,
        "result": "RESULT: FAIL",
        "verdicts": {"POSITIF_OK": 1, "MAUVAISE_RAISON": 1},
        "contient": ["DETAIL_OBSERVE DETAIL ALPHA absent"],
    },
    "convention": {
        "rc": 1,
        "result": "RESULT: FAIL",
        "verdicts": {"POSITIF_CASSE": 1, "MAUVAISE_RAISON": 1},
        "contient": ["SORTIE "],
    },
}


def empreinte(chemin):
    resume = hashlib.sha256()
    with chemin.open("rb") as flux:
        for bloc in iter(lambda: flux.read(1 << 20), b""):
            resume.update(bloc)
    return resume.hexdigest()


def construire(racine):
    oracle = racine / "oracle"
    oracle.mkdir()
    (oracle / "toy.txt").write_text(
        "ALPHA\nGAMMA=ok\n# BETA interdit\n", encoding="utf-8"
    )
    (oracle / "toy_verifier.py").write_text(TOY, encoding="utf-8")
    (oracle / "toy_naif.py").write_text(TOY_NAIF, encoding="utf-8")
    return oracle


def cas_texte(nom, garde, ancien, nouveau, detail):
    return {
        "nom": nom,
        "garde": garde,
        "fichier": "toy.txt",
        "ancien": ancien,
        "nouveau": nouveau,
        "detail": detail,
    }


def configurations(oracle):
    toy = str(oracle / "toy_verifier.py")
    naif = str(oracle / "toy_naif.py")
    source = str(oracle)
    positif = {"nom": "positif", "type": "positif"}
    commun = {"source": source, "arguments": ["{cible}"]}
    return [
        (
            "ok",
            {
                "verificateur": toy,
                "gardes": ["alpha", "beta", "gamma"],
                "cas": [
                    positif,
                    cas_texte("alpha", "alpha", "ALPHA", "ALFX", "ALPHA absent"),
                    cas_texte(
                        "beta", "beta", "GAMMA=ok", "GAMMA=ok\nBETA", "BETA interdit"
                    ),
                    cas_texte("gamma", "gamma", "GAMMA=ok", "GAMMA=ko", "GAMMA non ok"),
                ],
                **commun,
            },
        ),
        (
            "non_applique",
            {
                "verificateur": toy,
                "gardes": ["alpha"],
                "cas": [
                    positif,
                    cas_texte("ancre_absente", "alpha", "ABSENT", "X", "ALPHA absent"),
                ],
                **commun,
            },
        ),
        (
            "mauvaise",
            {
                "verificateur": toy,
                "gardes": ["alpha"],
                "cas": [
                    positif,
                    cas_texte(
                        "mauvais_detail", "alpha", "ALPHA", "ALFX", "BETA interdit"
                    ),
                ],
                **commun,
            },
        ),
        (
            "convention",
            {
                "verificateur": naif,
                "gardes": ["alpha"],
                "cas": [
                    positif,
                    cas_texte("alpha", "alpha", "ALPHA", "ALFX", "ALPHA absent"),
                ],
                **commun,
            },
        ),
    ]


def resume(compte):
    morceaux = [
        f"{verdict}={compte[verdict]}" for verdict in VERDICTS if compte.get(verdict)
    ]
    return ",".join(morceaux) if morceaux else "-"


def cas_lignes(sortie):
    trouves = []
    for brute in sortie.splitlines():
        morceau = MOTIF_CAS.match(brute.strip())
        if morceau:
            trouves.append(morceau.groups())
    return trouves


def examiner(attendu, rc, sortie):
    ecarts = []
    if rc != attendu["rc"]:
        ecarts.append(f"rc={rc} attendu={attendu['rc']}")
    resultats = [
        ligne.strip()
        for ligne in sortie.splitlines()
        if ligne.strip().startswith("RESULT:")
    ]
    if not resultats or not resultats[0].startswith(attendu["result"]):
        ecarts.append("resultat=" + (resultats[0] if resultats else "absent"))
    compte = Counter(verdict for _, verdict, _, _ in cas_lignes(sortie))
    for verdict, nombre in attendu["verdicts"].items():
        if compte.get(verdict, 0) != nombre:
            ecarts.append(f"{verdict}={compte.get(verdict, 0)} attendu={nombre}")
    for verdict in compte:
        if verdict not in attendu["verdicts"]:
            ecarts.append(f"verdict_inattendu={verdict}")
    for fragment in attendu["contient"]:
        if fragment not in sortie:
            ecarts.append(f"absent={fragment!r}")
    for fragment in ("COUVERTURE ok", "FIXTURES ABSENTES"):
        if fragment not in sortie:
            ecarts.append(f"absent={fragment!r}")
    if "SOURCE_DRIFT" in sortie:
        ecarts.append("source_drift")
    return compte, ecarts


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parseur = argparse.ArgumentParser(
        description="Prouver un harnais de mutation sur un oracle jetable."
    )
    parseur.add_argument("--harnais", required=True, help="script du harnais a prouver")
    parseur.add_argument(
        "--garder", action="store_true", help="conserver l'oracle pour diagnostic"
    )
    parseur.add_argument(
        "--delai", type=float, default=120.0, help="delai par execution en secondes"
    )
    arguments = parseur.parse_args(argv)

    harnais = Path(arguments.harnais).expanduser().resolve()
    if not harnais.is_file():
        print(f"ERREUR harnais introuvable : {harnais}")
        return 2

    avant = empreinte(harnais)
    print(f"HARNAIS {harnais} sha256={avant[:12]}")

    base = Path.home() / ".qoder" / "tmp"
    base.mkdir(parents=True, exist_ok=True)
    racine = Path(tempfile.mkdtemp(prefix="prouver-harnais.", dir=str(base)))
    print(f"ORACLE {racine}")

    comptes = {}
    ecarts_total = []
    tentatives = 0
    try:
        oracle = construire(racine)
        for nom, config in configurations(oracle):
            tentatives += 1
            chemin_cases = racine / f"{nom}.json"
            chemin_cases.write_text(
                json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            if harnais.suffix.lower() == ".py":
                commande = [sys.executable, str(harnais), "--cases", str(chemin_cases)]
            else:
                commande = [str(harnais), "--cases", str(chemin_cases)]
            try:
                processus = subprocess.run(
                    commande,
                    cwd=str(racine),
                    capture_output=True,
                    timeout=arguments.delai,
                )
                rc = processus.returncode
                sortie = (processus.stdout + processus.stderr).decode(
                    "utf-8", "replace"
                )
            except subprocess.TimeoutExpired:
                print(f"RUN {nom} TIMEOUT delai={arguments.delai:.0f}s")
                ecarts_total.append(f"{nom}: timeout")
                continue
            except OSError as erreur:
                print(f"RUN {nom} ERREUR {erreur}")
                ecarts_total.append(f"{nom}: {erreur}")
                continue

            compte, ecarts = examiner(ATTENDUS[nom], rc, sortie)
            comptes[nom] = compte
            etat = "CONFORME" if not ecarts else "ECART"
            print(
                f"RUN {nom} rc={rc} verdicts={resume(compte)} "
                f"attendu={resume(ATTENDUS[nom]['verdicts'])} etat={etat}"
            )
            if ecarts:
                ecarts_total.extend(f"{nom}: {ecart}" for ecart in ecarts)
                for ecart in ecarts:
                    print(f"  ECART {ecart}")
                for brute in sortie.splitlines()[-8:]:
                    print(f"  BRUT {brute.rstrip()}")
    finally:
        if arguments.garder:
            print(f"ORACLE_CONSERVE {racine}")
        else:
            shutil.rmtree(racine, ignore_errors=True)
            print(
                "ORACLE_ABSENT" if not racine.exists() else f"ORACLE_RESTANT {racine}"
            )

    ok = not ecarts_total
    apres = empreinte(harnais)
    if apres != avant:
        print(f"HARNAIS_DRIFT sha256_apres={apres[:12]}")
        ok = False
    vus = sorted({verdict for compte in comptes.values() for verdict in compte})
    if ok and VERDICTS_ATTENDUS <= set(vus):
        print(f"RESULT: PASS runs={tentatives} verdicts={len(vus)}")
        return 0
    print(
        f"RESULT: FAIL runs={tentatives} verdicts={len(vus)} ecarts={len(ecarts_total)}"
    )
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("ERREUR interrompu")
        sys.exit(2)
    except Exception as erreur:  # noqa: BLE001 - sortie sans traceback
        print(f"ERREUR {type(erreur).__name__}: {erreur}")
        sys.exit(2)
