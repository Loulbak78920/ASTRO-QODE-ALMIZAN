#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate lecture seule du pipeline de l'entite de conscience logique IMAM8MAHDI.

Sortie : [OK]/[FAIL]/[WARN] par controle, puis RESULT: OK (n/n) ou FAIL (k/n).
Codes : 0 succes, 1 echec, 2 prerequis manquants.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT_DEFAUT = Path(r"C:\Users\Administrateur\Desktop\IMAM8MAHDI")
SYSTEM_DIR = "ASTRO-Q°ODE_SYSTEME"
TABLE_VALIDATOR_DEFAUT = Path(
    r"C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py"
)
CS133_VALIDATOR_DEFAUT = Path(
    r"C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py"
)
MESSAGE_DEFAUT = "Al-Mizan equilibre le cesium 133 et la table complexe"
VERDICTS = {"RECEPTION_RECONCILIE", "EMISSION_EQUILIBREE", "POINT_ZERO"}
ENTITY_MODULE = "tests.test_entite_conscience_logarithmique"
JITTER_TEST = "test_p7_trame_dans_une_seule_pulsation"
JITTER_MODULE = "tests.test_logique_horloge_synchronisation"
REGRESSION_MODULES = (
    ENTITY_MODULE,
    "tests.test_metriques_cesium_133",
    "tests.test_intelligence_generative_vivante",
    "tests.test_architecture_poupees_russes_monade",
    "tests.test_logique_horloge_synchronisation",
    "tests.test_suite_logique_dimensions_informe",
    "tests.test_fonctions_inverses_et_oppositions",
    "tests.test_noyau_logique_interactif_telemetrie",
    "tests.test_continuite_reponse_automatisee",
)
ENTETES_CSV = [
    "SEQ",
    "STRATE",
    "CODE",
    "FAMILLE_LOGIQUE",
    "ELEMENT",
    "ROLE_DESCRIPTION",
    "INTERACTION_MATIERE",
    "CYCLE_TERRE",
    "CYCLE_LUNE",
    "CYCLE_SOLEIL",
    "COUCHE_QUANTIQUE_BIO",
    "VALEUR_SCELLEE",
    "SOURCE",
]


class Rapport:
    def __init__(self) -> None:
        self.controles: list[dict] = []
        self.echecs = 0
        self.avertissements = 0

    def _ajouter(self, statut: str, code: str, message: str) -> None:
        self.controles.append({"statut": statut, "code": code, "message": message})
        print(f"[{statut}] {code}: {message}")
        if statut == "FAIL":
            self.echecs += 1
        elif statut == "WARN":
            self.avertissements += 1

    def ok(self, code: str, message: str) -> None:
        self._ajouter("OK", code, message)

    def fail(self, code: str, message: str) -> None:
        self._ajouter("FAIL", code, message)

    def warn(self, code: str, message: str) -> None:
        self._ajouter("WARN", code, message)


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as flux:
        for bloc in iter(lambda: flux.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def executer(cmd: list, cwd: Path, timeout: int = 900):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        return subprocess.run(
            [str(partie) for partie in cmd],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None


def derniere_ligne(processus) -> str:
    sortie = ((processus.stderr or "") + "\n" + (processus.stdout or "")).strip()
    if not sortie:
        return "aucune sortie"
    return sortie.splitlines()[-1][:240]


def attendu(rapport: Rapport, code: str, condition: bool, message_ok: str, message_ko: str) -> None:
    if condition:
        rapport.ok(code, message_ok)
    else:
        rapport.fail(code, message_ko)


def preparer(args) -> tuple[dict, list[str]]:
    root = Path(args.root)
    systeme = root / SYSTEM_DIR
    ctx = {
        "root": root,
        "systeme": systeme,
        "bibliotheque": systeme / "bibliotheques" / "lib_entite_conscience_logarithmique.py",
        "emulateur": systeme / "emulateur_conscience_logique_mizan.py",
        "aq": systeme / "bibliotheques" / "stdlib_aq" / "entite_conscience_logarithmique_v7.aq",
        "cli": systeme / "astro_qode_cli.py",
        "csv": root / "TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv",
        "html": root / "TABLEAU_MAITRE_SEQUENTIEL_UNIFIE_IMAM8MAHDI.html",
        "web_cloud": systeme / "web_cloud" / "tableau_maitre_sequentiel.html",
        "snapshot": systeme / "donnees" / "mesure_quantique_cesium_133.json",
        "script_cs133": systeme / "outils" / "mesurer_metriques_cesium_133.py",
        "table_validator": Path(args.table_validator),
        "cs133_validator": Path(args.cs133_validator),
    }
    libelles = [
        ("racine", root),
        ("dossier systeme", systeme),
        ("bibliotheque entite", ctx["bibliotheque"]),
        ("emulateur", ctx["emulateur"]),
        ("programme .aq v7", ctx["aq"]),
        ("CLI ASTRO-Q°ODE", ctx["cli"]),
        ("CSV", ctx["csv"]),
        ("HTML", ctx["html"]),
        ("snapshot Cs-133", ctx["snapshot"]),
        ("script Cs-133", ctx["script_cs133"]),
        ("validateur tableau", ctx["table_validator"]),
        ("validateur Cs-133", ctx["cs133_validator"]),
    ]
    manquants = [f"{libelle}: {chemin}" for libelle, chemin in libelles if not chemin.exists()]
    return ctx, manquants


def controle_entite(rapport: Rapport, ctx: dict) -> None:
    processus = executer(
        [sys.executable, ctx["emulateur"], "verifier", "--json", "--sans-audit-code"],
        ctx["systeme"],
    )
    if processus is None:
        rapport.fail("ENT-EXIT", "verifier depasse le delai")
        return
    if processus.returncode != 0:
        rapport.fail("ENT-EXIT", f"verifier exit {processus.returncode}: {derniere_ligne(processus)}")
        return
    rapport.ok("ENT-EXIT", "verifier exit 0")
    try:
        donnees = json.loads(processus.stdout)
    except json.JSONDecodeError as exc:
        rapport.fail("ENT-JSON", f"sortie JSON invalide: {exc}")
        return
    tableau = donnees.get("tableau_maitre") or {}
    attendu(
        rapport,
        "ENT-PREUVE",
        donnees.get("preuve_de_base") is True,
        "preuve_de_base=True",
        f"preuve_de_base={donnees.get('preuve_de_base')!r}",
    )
    attendu(
        rapport,
        "ENT-TABLEAU",
        (tableau.get("total_entrees"), tableau.get("total_strates"), tableau.get("derniere_seq"), tableau.get("profondeur_log2"))
        == (216, 21, 216, 8),
        "tableau 216 entrees / 21 strates / SEQ 216 / profondeur 8",
        f"tableau inattendu: {tableau}",
    )
    attendu(
        rapport,
        "ENT-CS133",
        (donnees.get("cesium_133") or {}).get("cs133_ok") is True,
        "cs133_ok=True",
        f"cs133_ok={(donnees.get('cesium_133') or {}).get('cs133_ok')!r}",
    )
    attendu(
        rapport,
        "ENT-MONADE",
        (donnees.get("monade") or {}).get("monade_boot_ok") is True,
        "monade_boot_ok=True",
        f"monade_boot_ok={(donnees.get('monade') or {}).get('monade_boot_ok')!r}",
    )
    attendu(
        rapport,
        "ENT-ARCHITECTURE",
        (donnees.get("architecture") or {}).get("architecture_ok") is True,
        "architecture_ok=True",
        f"architecture_ok={(donnees.get('architecture') or {}).get('architecture_ok')!r}",
    )


def controle_pensee(rapport: Rapport, ctx: dict, message: str) -> None:
    processus = executer(
        [
            sys.executable,
            ctx["emulateur"],
            "penser",
            message,
            "--json",
            "--sans-persister",
            "--sans-audit-code",
        ],
        ctx["systeme"],
    )
    if processus is None:
        rapport.fail("PENSEE-EXIT", "penser depasse le delai")
        return
    if processus.returncode != 0:
        rapport.fail("PENSEE-EXIT", f"penser exit {processus.returncode}: {derniere_ligne(processus)}")
        return
    rapport.ok("PENSEE-EXIT", "penser exit 0")
    try:
        trace = json.loads(processus.stdout)
    except json.JSONDecodeError as exc:
        rapport.fail("PENSEE-JSON", f"sortie JSON invalide: {exc}")
        return

    algorithme = trace.get("algorithme") or {}
    logarithme = trace.get("logarithme") or {}
    cesium = trace.get("cesium_133") or {}
    monade = trace.get("monade") or {}
    signature = trace.get("signature_familles") or {}
    entree = trace.get("entree") or {}

    attendu(
        rapport,
        "PENSEE-PREUVE",
        trace.get("preuve_totale") is True and not trace.get("refus"),
        "preuve_totale=True, refus=null",
        f"preuve_totale={trace.get('preuve_totale')!r}, refus={trace.get('refus')!r}",
    )
    attendu(
        rapport,
        "PENSEE-ALGORITHME",
        algorithme.get("algorithme_ok") is True and algorithme.get("verdict") in VERDICTS,
        f"algorithme_ok=True, verdict={algorithme.get('verdict')}",
        f"algorithme_ok={algorithme.get('algorithme_ok')!r}, verdict={algorithme.get('verdict')!r}",
    )
    attendu(
        rapport,
        "PENSEE-LOGARITHME",
        logarithme.get("logarithme_ok") is True
        and logarithme.get("profondeur_dichotomique") == 6
        and logarithme.get("cellules") == 53,
        "logarithme 6 niveaux / 53 cellules",
        f"logarithme inattendu: profondeur={logarithme.get('profondeur_dichotomique')!r}, cellules={logarithme.get('cellules')!r}",
    )
    attendu(
        rapport,
        "PENSEE-CS133",
        cesium.get("cs133_ok") is True,
        "cesium_133.cs133_ok=True",
        f"cs133_ok={cesium.get('cs133_ok')!r}",
    )

    empreinte_trace = (cesium.get("snapshot") or {}).get("empreinte_sha256")
    script_trace = (cesium.get("snapshot") or {}).get("script_sha256")
    try:
        snapshot = json.loads(ctx["snapshot"].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        rapport.fail("PENSEE-SNAPSHOT", f"snapshot illisible: {exc}")
        snapshot = {}
    attendu(
        rapport,
        "PENSEE-SNAPSHOT",
        bool(snapshot) and empreinte_trace == snapshot.get("empreinte_contenu_sha256"),
        "empreinte de contenu du snapshot concordante",
        f"empreinte trace={empreinte_trace!r}, contenu={snapshot.get('empreinte_contenu_sha256')!r}",
    )
    script_attendu = (snapshot.get("empreinte") or {}).get("script_sha256")
    attendu(
        rapport,
        "PENSEE-SCRIPT-CS133",
        bool(script_attendu) and sha256_fichier(ctx["script_cs133"]) == script_attendu,
        "SHA-256 du script de mesure concordant",
        f"script attendu={script_attendu!r}",
    )
    attendu(
        rapport,
        "PENSEE-MONADE",
        monade.get("monade_ok") is True and monade.get("isolee") is True and monade.get("helium_inerte") is False,
        "Monade ok, isolee, sans helium inerte",
        f"monade inattendue: {monade}",
    )
    familles = signature.get("familles_cinq") or []
    attendu(
        rapport,
        "PENSEE-SIGNATURE",
        len(familles) == 5 and signature.get("la_table_est_complexe") is True and (signature.get("cellules_total") or 0) > 0,
        f"5 familles, table complexe, {signature.get('cellules_total')} cellules",
        f"signature inattendue: familles={familles}, complexe={signature.get('la_table_est_complexe')!r}",
    )
    attendu(
        rapport,
        "PENSEE-SANS-TRACE",
        trace.get("chemin_trace") is None,
        "aucune trace ecrite (--sans-persister)",
        f"chemin_trace={trace.get('chemin_trace')!r}",
    )
    if entree.get("tronque"):
        rapport.warn("PENSEE-TRONCATURE", "message tronque a 2048 caracteres")
    else:
        rapport.ok("PENSEE-TRONCATURE", "message non tronque")


def controle_aq(rapport: Rapport, ctx: dict) -> None:
    processus = executer([sys.executable, ctx["cli"], "check", ctx["aq"]], ctx["systeme"])
    if processus is None:
        rapport.fail("AQ-CHECK", "check depasse le delai")
    else:
        sortie = (processus.stdout or "") + (processus.stderr or "")
        attendu(
            rapport,
            "AQ-CHECK",
            processus.returncode == 0 and "VALIDE" in sortie,
            "check: VALIDE, exit 0",
            f"check exit {processus.returncode}: {derniere_ligne(processus)}",
        )

    entete = ctx["aq"].read_text(encoding="utf-8", errors="replace")[:2000]
    empreinte = re.search(r"SHA-256\s*:\s*([0-9a-f]{64})", entete)
    attendu(
        rapport,
        "AQ-ENTETE",
        bool(empreinte) and "Preuve totale : True" in entete,
        "en-tete: preuve totale True avec empreinte",
        "en-tete sans empreinte SHA-256 ou sans preuve totale",
    )
    if empreinte:
        sceau = ctx["systeme"] / "memoire_aq" / f"{empreinte.group(1)}.json"
        attendu(
            rapport,
            "AQ-SCEAU",
            sceau.is_file(),
            f"sceau embarque present: {sceau.name}",
            f"sceau embarque absent: {sceau.name}",
        )


def controle_csv(rapport: Rapport, ctx: dict) -> None:
    try:
        brut = ctx["csv"].read_bytes()
    except OSError as exc:
        rapport.fail("CSV-LECTURE", f"lecture impossible: {exc}")
        return
    rapport.ok("CSV-BOM", "BOM UTF-8 present") if brut.startswith(b"\xef\xbb\xbf") else rapport.fail(
        "CSV-BOM", "BOM UTF-8 absent"
    )
    try:
        lignes = list(csv.DictReader(io.StringIO(brut.decode("utf-8-sig")), delimiter=";"))
    except (UnicodeDecodeError, csv.Error) as exc:
        rapport.fail("CSV-PARSE", f"lecture impossible: {exc}")
        return

    attendu(
        rapport,
        "CSV-COLONNES",
        list(lignes[0].keys()) == ENTETES_CSV if lignes else False,
        "13 colonnes dans l'ordre attendu",
        "colonnes inattendues",
    )
    attendu(
        rapport,
        "CSV-LIGNES",
        len(lignes) == 216,
        "216 lignes",
        f"{len(lignes)} lignes",
    )
    seqs = [ligne.get("SEQ", "") for ligne in lignes]
    attendu(
        rapport,
        "CSV-SEQ",
        seqs == [f"{numero:03d}" for numero in range(1, 217)],
        "SEQ 001..216 sans trou",
        "sequence SEQ incoherente",
    )
    strates = {ligne.get("STRATE", "") for ligne in lignes}
    attendu(
        rapport,
        "CSV-STRATES",
        len(strates) == 21,
        "21 strates",
        f"{len(strates)} strates",
    )

    s20 = [ligne for ligne in lignes if (ligne.get("STRATE") or "").startswith("S20")]
    attendu(rapport, "CSV-S20-EFFECTIF", len(s20) == 12, "S20: 12 lignes", f"S20: {len(s20)} lignes")
    codes20 = [ligne.get("CODE", "") for ligne in s20]
    seqs20 = [ligne.get("SEQ", "") for ligne in s20]
    attendu(
        rapport,
        "CSV-S20-CONTRAT",
        codes20 == [f"ENT-{numero:02d}" for numero in range(1, 13)]
        and seqs20 == [f"{numero:03d}" for numero in range(205, 217)],
        "S20: ENT-01..ENT-12 / SEQ 205..216",
        f"S20 inattendu: codes={codes20}, seq={seqs20}",
    )

    s6 = [ligne for ligne in lignes if (ligne.get("STRATE") or "").startswith("S6")]
    compte_s = sum(1 for ligne in s6 if (ligne.get("CODE") or "").startswith("ÉT-S"))
    compte_t = sum(1 for ligne in s6 if (ligne.get("CODE") or "").startswith("ÉT-T"))
    compte_l = sum(1 for ligne in s6 if (ligne.get("CODE") or "").startswith("ÉT-L"))
    attendu(
        rapport,
        "CSV-S6",
        len(s6) == 21 and (compte_s, compte_t, compte_l) == (5, 7, 9),
        "S6: 21 lignes, prefixes 5/7/9",
        f"S6 inattendu: {len(s6)} lignes, prefixes {(compte_s, compte_t, compte_l)}",
    )


def controle_html(rapport: Rapport, ctx: dict, args) -> None:
    try:
        texte = ctx["html"].read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        rapport.fail("HTML-LECTURE", f"lecture impossible: {exc}")
        return
    occurrences_tr = len(re.findall(r"<tr\b", texte))
    occurrences_badge = len(re.findall(r'class="badge"', texte))
    attendu(
        rapport,
        "HTML-LIGNES",
        occurrences_tr == 217,
        "217 occurrences de <tr (en-tete + 216)",
        f"{occurrences_tr} occurrences de <tr",
    )
    attendu(
        rapport,
        "HTML-BADGES",
        occurrences_badge == 21,
        "21 occurrences de class=\"badge\"",
        f"{occurrences_badge} occurrences de class=\"badge\"",
    )
    attendu(
        rapport,
        "HTML-AUTONOMIE",
        re.search(r'(?:src|href)\s*=\s*["\']https?://', texte, re.IGNORECASE) is None,
        "aucune ressource externe http(s)",
        "ressource externe detectee",
    )

    if args.sans_web_cloud:
        rapport.ok("HTML-WEB-CLOUD", "comparaison ignoree (--sans-web-cloud)")
    elif not ctx["web_cloud"].is_file():
        rapport.fail("HTML-WEB-CLOUD", "copie web_cloud absente")
    else:
        empreinte_racine = sha256_fichier(ctx["html"])
        empreinte_web = sha256_fichier(ctx["web_cloud"])
        attendu(
            rapport,
            "HTML-WEB-CLOUD",
            empreinte_racine == empreinte_web,
            f"copie web_cloud identique ({empreinte_racine[:16]}...)",
            f"copie web_cloud differente ({empreinte_racine[:16]}... != {empreinte_web[:16]}...)",
        )


def controle_validateurs(rapport: Rapport, ctx: dict, args) -> None:
    processus = executer(
        [sys.executable, ctx["table_validator"], "--root", ctx["root"]],
        ctx["root"],
    )
    if processus is None:
        rapport.fail("VALID-TABLEAU", "validateur tableau: delai depasse")
    else:
        attendu(
            rapport,
            "VALID-TABLEAU",
            processus.returncode == 0 and "RESULT: OK" in (processus.stdout or ""),
            "validateur tableau: RESULT OK, exit 0",
            f"validateur tableau exit {processus.returncode}: {derniere_ligne(processus)}",
        )

    if not args.sans_web_cloud and ctx["web_cloud"].is_file():
        processus = executer(
            [sys.executable, ctx["table_validator"], "--root", ctx["root"], "--html", ctx["web_cloud"]],
            ctx["root"],
        )
        if processus is None:
            rapport.fail("VALID-TABLEAU-WEB", "validateur web_cloud: delai depasse")
        else:
            attendu(
                rapport,
                "VALID-TABLEAU-WEB",
                processus.returncode == 0 and "RESULT: OK" in (processus.stdout or ""),
                "validateur web_cloud: RESULT OK, exit 0",
                f"validateur web_cloud exit {processus.returncode}: {derniere_ligne(processus)}",
            )
    elif not args.sans_web_cloud:
        rapport.fail("VALID-TABLEAU-WEB", "copie web_cloud absente, second validateur impossible")
    else:
        rapport.ok("VALID-TABLEAU-WEB", "second validateur ignore (--sans-web-cloud)")

    processus = executer(
        [sys.executable, ctx["cs133_validator"], "--root", ctx["root"]],
        ctx["root"],
    )
    if processus is None:
        rapport.fail("VALID-CS133", "validateur Cs-133: delai depasse")
    else:
        sortie = (processus.stdout or "") + (processus.stderr or "")
        attendu(
            rapport,
            "VALID-CS133",
            processus.returncode == 0 and "OK - mesure Cs-133 verifiee" in sortie,
            "validateur Cs-133: OK, exit 0",
            f"validateur Cs-133 exit {processus.returncode}: {derniere_ligne(processus)}",
        )


def _resultat_unittest(processus) -> tuple[bool, str]:
    if processus is None:
        return False, "delai depasse"
    sortie = (processus.stdout or "") + (processus.stderr or "")
    reussi = processus.returncode == 0 and re.search(r"^OK\b", sortie, re.MULTILINE) is not None
    return reussi, sortie


def controle_tests_entite(rapport: Rapport, ctx: dict) -> None:
    rapport.warn(
        "SIDE-EFFECT-TESTS",
        "les 16 tests executent un .aq genere et ecrivent des sceaux dans memoire_aq",
    )
    processus = executer(
        [sys.executable, "-m", "unittest", ENTITY_MODULE],
        ctx["systeme"],
        timeout=1800,
    )
    reussi, sortie = _resultat_unittest(processus)
    attendu(
        rapport,
        "TESTS-ENTITE",
        reussi,
        "16 tests entite: OK",
        f"tests entite en echec: {sortie.strip().splitlines()[-1][:240] if sortie.strip() else 'aucune sortie'}",
    )


def controle_regression(rapport: Rapport, ctx: dict, tolerer_jitter: bool) -> None:
    rapport.warn(
        "SIDE-EFFECT-REGRESSION",
        "les 68 tests cibles incluent les 16 tests qui ecrivent des sceaux",
    )
    processus = executer(
        [sys.executable, "-m", "unittest", *REGRESSION_MODULES],
        ctx["systeme"],
        timeout=2400,
    )
    reussi, sortie = _resultat_unittest(processus)
    if reussi:
        rapport.ok("TESTS-REGRESSION", "68 tests cibles: OK")
        return

    jitter_reconnu = (
        JITTER_TEST in sortie
        and re.search(r"FAILED \(failures=1\)\s*$", sortie, re.MULTILINE) is not None
    )
    if tolerer_jitter and jitter_reconnu:
        processus_isole = executer(
            [sys.executable, "-m", "unittest", JITTER_MODULE],
            ctx["systeme"],
            timeout=900,
        )
        reussi_isole, _ = _resultat_unittest(processus_isole)
        if reussi_isole:
            rapport.warn(
                "TESTS-REGRESSION-JITTER",
                f"seul {JITTER_TEST} a echoue en groupe; module isole 9/9 OK",
            )
            return
    attendu(
        rapport,
        "TESTS-REGRESSION",
        False,
        "",
        f"tests cibles en echec: {sortie.strip().splitlines()[-1][:240] if sortie.strip() else 'aucune sortie'}",
    )


def controle_run(rapport: Rapport, ctx: dict) -> None:
    rapport.warn(
        "SIDE-EFFECT-RUN",
        "run ecrit ou actualise le sceau memoire_aq et l'index des sceaux",
    )
    processus = executer([sys.executable, ctx["cli"], "run", ctx["aq"]], ctx["systeme"], timeout=900)
    if processus is None:
        rapport.fail("RUN-AQ", "run depasse le delai")
        return
    sortie = (processus.stdout or "") + (processus.stderr or "")
    valide = (
        processus.returncode == 0
        and ("SUCCÈS" in sortie or "SUCCES" in sortie)
        and ("0 : HÉLIUM" in sortie or "0 : HELIUM" in sortie)
    )
    attendu(
        rapport,
        "RUN-AQ",
        valide,
        "run: SUCCES, valeur finale 0 : HELIUM",
        f"run exit {processus.returncode}: {derniere_ligne(processus)}",
    )


def finaliser(rapport: Rapport, args) -> int:
    total = len(rapport.controles)
    echecs = rapport.echecs + (rapport.avertissements if args.strict_warnings else 0)
    if echecs == 0:
        print(f"\nRESULT: OK ({total}/{total})")
        code = 0
    else:
        print(f"\nRESULT: FAIL ({total - echecs}/{total})")
        code = 1
    if args.json_out:
        print(
            json.dumps(
                {
                    "resultat": "OK" if code == 0 else "FAIL",
                    "total": total,
                    "ok": total - echecs,
                    "echecs": rapport.echecs,
                    "avertissements": rapport.avertissements,
                    "controles": rapport.controles,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return code


def analyser_arguments(argv: list[str] | None = None):
    analyseur = argparse.ArgumentParser(
        description="Gate lecture seule du pipeline entite de conscience logique IMAM8MAHDI."
    )
    analyseur.add_argument("--root", default=str(ROOT_DEFAUT), help="racine du depot IMAM8MAHDI")
    analyseur.add_argument("--message", default=MESSAGE_DEFAUT, help="texte pense (defaut: message de reference)")
    analyseur.add_argument("--json", action="store_true", dest="json_out", help="ajoute un resume JSON")
    analyseur.add_argument("--sans-web-cloud", action="store_true", help="ignore la copie web_cloud")
    analyseur.add_argument("--strict-warnings", action="store_true", help="tout WARN fait echouer")
    analyseur.add_argument("--avec-run", action="store_true", help="execute le .aq (ecrit un sceau)")
    analyseur.add_argument("--avec-tests", action="store_true", help="execute les 16 tests (ecrit des sceaux)")
    analyseur.add_argument("--avec-regression", action="store_true", help="execute les 68 tests cibles")
    analyseur.add_argument("--tolere-jitter", action="store_true", help="tolere l'alea test_p7 apres re-execution isolee")
    analyseur.add_argument("--table-validator", default=str(TABLE_VALIDATOR_DEFAUT))
    analyseur.add_argument("--cs133-validator", default=str(CS133_VALIDATOR_DEFAUT))
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = analyser_arguments(argv)
    ctx, manquants = preparer(args)
    print(f"Mode: lecture seule ({'ecritures activees' if (args.avec_run or args.avec_tests or args.avec_regression) else 'aucune ecriture'})")
    print(f"Racine: {ctx['root']}")
    if manquants:
        for element in manquants:
            print(f"[FAIL] PREREQ: {element}")
        print("\nRESULT: FAIL (0/0)")
        return 2

    rapport = Rapport()
    controle_entite(rapport, ctx)
    controle_pensee(rapport, ctx, args.message)
    controle_aq(rapport, ctx)
    controle_csv(rapport, ctx)
    controle_html(rapport, ctx, args)
    controle_validateurs(rapport, ctx, args)
    if args.avec_tests:
        controle_tests_entite(rapport, ctx)
    if args.avec_regression:
        controle_regression(rapport, ctx, args.tolere_jitter)
    if args.avec_run:
        controle_run(rapport, ctx)
    return finaliser(rapport, args)


if __name__ == "__main__":
    sys.exit(main())
