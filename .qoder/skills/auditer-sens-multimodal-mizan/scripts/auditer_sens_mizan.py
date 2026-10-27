#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read-only audit of Al-Mizan multimodal senses.

Default mode writes nothing: inventory, route presence, static signals.
Opt-in modes:
  --sondes      real camera/mic capture, STT, spectrum, vision, touch probes
  --production  public GET routes + benign SAS challenge (never /sas/valider)
  --parite      read-only sha256sum comparison over SSH (paramiko)
  --tests       targeted unittest run; the SAS tests may write memoire_aq state

Exit codes: 0 expected, 1 anomaly, 2 environment error.
Output is ASCII-only and never prints a secret value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

RACINE_DEFAUT = Path(r"C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME")

MODULES = [
    "module_sas_biometrique_souverain.py",
    "moteur_voix_serveur_hybride_mizan.py",
    "moteur_acoustique_harmonique_horloge_mizan.py",
    "moteur_spectre_ecoute_harmonique_mizan.py",
    "module_dialogue_vocal_continu_mizan.py",
    "passerelle_api_vps_mizan.py",
    "conscience_logique/reconnaissance_pleniere_couche.py",
    "conscience_logique/vision_couche.py",
    "conscience_logique/brancher_sens.py",
    "conscience_logique/capteurs_vibrations_physiques.py",
]

ROUTES = [
    "/api/v1/voix",
    "/api/v1/voix/acoustique",
    "/api/v1/voix/transcrire",
    "/api/v1/ecoute/spectre",
    "/api/v1/auth/statut_session",
    "/api/v1/auth/sas_biometrique/challenge",
    "/api/v1/auth/sas_biometrique/valider",
]

SIGNATURES = {
    "moteur_reel": r"whisper|vosk|mediapipe|face_recognition|insightface|deepface|webrtcvad|torchaudio|librosa|speech_recognition|dlib|arcface|facenet",
    "facteur_client": r"visage_detecte|score_vivacite_liveness|signature_materielle_passkey|phrase_prononcee",
    "constante_spectre": r"-18\.5|energie_basses|energie_mediums|energie_aigus",
    "cle_par_defaut": r"CLE_API_VPS_DEFAUT|mizan_vps_souverain_secret|cle_secrete_souveraine",
    "session_sans_jeton": r"est_session_souveraine_active\(\s*\"\"\s*\)|est_session_souveraine_active\(\s*''\s*\)",
    "verification_presence": r"verifier_preuve_pleniere|empreinte_verif_seule",
}

URLS_GET = [
    "https://www.al-mizan.world/api/v1/voix",
    "https://www.al-mizan.world/api/v1/voix/acoustique",
    "https://www.al-mizan.world/api/v1/ecoute/spectre",
    "https://www.al-mizan.world/api/v1/auth/statut_session",
    "https://www.al-mizan.world/api/v1/etat",
]

URL_CHALLENGE = "https://www.al-mizan.world/api/v1/auth/sas_biometrique/challenge"


def ascii_(value: object) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=True, default=str)
    else:
        text = str(value)
    return text.encode("ascii", "backslashreplace").decode("ascii")


def emit(key: str, value: object = "") -> None:
    print(f"{key}={ascii_(value)}", flush=True)


def titre(text: str) -> None:
    print("", flush=True)
    print(f"== {ascii_(text)} ==", flush=True)


def trouver_racine(arg: str | None) -> Path:
    candidats = []
    if arg:
        candidats.append(Path(arg))
    candidats.append(RACINE_DEFAUT)
    candidats.append(Path(r"C:\Users\Administrateur\Desktop\IMAM8MAHDI"))
    for candidat in candidats:
        if (candidat / "passerelle_api_vps_mizan.py").is_file():
            return candidat
    emit("ERREUR", "racine introuvable: passerelle_api_vps_mizan.py absent")
    raise SystemExit(2)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as flux:
        for bloc in iter(lambda: flux.read(1 << 20), b""):
            digest.update(bloc)
    return digest.hexdigest()


def inventaire(racine: Path) -> int:
    titre("inventaire")
    manquants = 0
    for relatif in MODULES:
        chemin = racine / relatif
        if not chemin.is_file():
            emit("MODULE", f"{relatif} PRESENT=non")
            manquants += 1
            continue
        emit("MODULE", f"{relatif} PRESENT=oui SHA256={sha256(chemin)} OCTETS={chemin.stat().st_size}")
    emit("MODULES_TOTAL", f"{len(MODULES)} MANQUANTS={manquants}")
    return 1 if manquants else 0


def routes(racine: Path) -> int:
    titre("routes")
    passerelle = (racine / "passerelle_api_vps_mizan.py").read_text(encoding="utf-8", errors="replace")
    absentes = 0
    for route in ROUTES:
        present = route in passerelle
        emit("ROUTE", f"{route} PRESENTE={'oui' if present else 'non'}")
        if not present:
            absentes += 1
    emit("ROUTES_TOTAL", f"{len(ROUTES)} ABSENTES={absentes}")
    # A partially renamed route set is not an automatic failure; the agent must inspect.
    return 0


def classification(racine: Path) -> int:
    titre("signaux_statiques")
    for categorie, motif in SIGNATURES.items():
        regex = re.compile(motif, re.IGNORECASE)
        encontres = 0
        for relatif in MODULES:
            chemin = racine / relatif
            if not chemin.is_file():
                continue
            for numero, ligne in enumerate(chemin.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if regex.search(ligne):
                    encontres += 1
                    if encontres <= 4:
                        extrait = ligne.strip()
                        if len(extrait) > 110:
                            extrait = extrait[:110] + "..."
                        emit("SIGNAL", f"{categorie} {relatif}:{numero} {extrait}")
        if encontres == 0:
            emit("SIGNAL", f"{categorie} AUCUN")
        emit("SIGNAL_TOTAL", f"{categorie} {encontres}")
    return 0


def sondes(racine: Path) -> int:
    titre("sondes_locales")
    sys.path.insert(0, str(racine))
    try:
        import importlib

        rec = importlib.import_module("conscience_logique.reconnaissance_pleniere_couche")
        cam = rec.capturer_visage_camera()
        emit("CAMERA", {
            "accessible": cam.get("accessible"),
            "capturee": cam.get("capturee"),
            "empreinte_sha256": (cam.get("empreinte_sha256") or "")[:16],
            "octets_hashes": cam.get("octets_hashes"),
            "flux_brut_stocke": cam.get("flux_brut_stocke"),
            "erreur": cam.get("erreur"),
        })
        mic = rec.capturer_voix_micro(1.5)
        emit("MICRO", {
            "accessible": mic.get("accessible"),
            "capturee": mic.get("capturee"),
            "octets_hashes": mic.get("octets_hashes"),
            "rms": mic.get("rms"),
            "parole_probable": mic.get("parole_probable"),
            "flux_brut_stocke": mic.get("flux_brut_stocke"),
        })

        voix = importlib.import_module("moteur_voix_serveur_hybride_mizan")
        silence = b"\x00" * 32000
        bruit = os.urandom(32000)
        r1 = voix.MOTEUR_VOIX_HYBRIDE.transcrire_audio_binaire(silence, "wav")
        r2 = voix.MOTEUR_VOIX_HYBRIDE.transcrire_audio_binaire(bruit, "webm")
        identiques = r1.texte_transcrit == r2.texte_transcrit
        emit("STT", {
            "texte_silence": r1.texte_transcrit,
            "texte_bruit": r2.texte_transcrit,
            "textes_identiques": identiques,
            "mode_silence": r1.mode_calcul_utilise,
            "mode_bruit": r2.mode_calcul_utilise,
            "latence_silence_ms": r1.latence_ms,
            "latence_bruit_ms": r2.latence_ms,
        })
        if not r1.texte_transcrit and not r2.texte_transcrit:
            emit("VERDICT_STT", "desactive_ou_vide_non_concluant")
        elif identiques:
            emit("VERDICT_STT", "simule_texte_constant")
        else:
            emit("VERDICT_STT", "a_verifier")

        spectre = importlib.import_module("moteur_spectre_ecoute_harmonique_mizan")
        s1 = spectre.MOTEUR_SPECTRE_ECOUTE.analyser_flux_spectral()
        s2 = spectre.MOTEUR_SPECTRE_ECOUTE.analyser_flux_spectral(70.0, 20.0, 10.0, 95.0)
        bandes1 = (s1.energie_basses_terre_pct, s1.energie_mediums_lune_pct, s1.energie_aigus_soleil_pct)
        bandes2 = (s2.energie_basses_terre_pct, s2.energie_mediums_lune_pct, s2.energie_aigus_soleil_pct)
        emit("SPECTRE", {
            "db_defaut": s1.energie_globale_db,
            "db_signal": s2.energie_globale_db,
            "bandes_defaut": bandes1,
            "bandes_signal": bandes2,
        })
        emit("VERDICT_SPECTRE", "simule_db_figee" if s1.energie_globale_db == s2.energie_globale_db else "a_verifier")

        vision = importlib.import_module("conscience_logique.vision_couche")
        lecture = vision.VisionCouche().lire_pour_comprendre("")
        corps = lecture.get("lecture") or {}
        emit("VISION", {
            "formes": corps.get("formes"),
            "gestes": corps.get("gestes"),
            "integrable_doctrine": corps.get("integrable_doctrine"),
            "flux_brut_stocke": corps.get("flux_brut_stocke"),
        })
        emit("VERDICT_VISION", "gabarit_non_analyseur")

        brancher = importlib.import_module("conscience_logique.brancher_sens")
        toucher = brancher.BrancheurSens().activer_toucher_capteurs()
        capteurs = toucher.get("capteurs") or {}
        thermique = capteurs.get("thermique") or {}
        phi = (toucher.get("equation_resolue") or {}).get("Phi") or {}
        emit("TOUCHER", {
            "souris": (capteurs.get("souris") or {}).get("ok"),
            "clavier": (capteurs.get("clavier") or {}).get("ok"),
            "thermique_raw": thermique.get("raw"),
            "thermique_c": thermique.get("temp_c"),
            "phi": phi,
        })
        temp = thermique.get("temp_c")
        if isinstance(temp, (int, float)) and temp < -100:
            emit("VERDICT_THERMIQUE", "conversion_suspecte")
        else:
            emit("VERDICT_THERMIQUE", "a_verifier")
    except Exception as exc:  # noqa: BLE001 - report environment failure, not crash
        emit("ERREUR_SONDES", f"{type(exc).__name__}: {exc}")
        return 2
    emit("RESULT_SONDES", "EXECUTE")
    return 0


def production() -> int:
    titre("production_lecture_seule")
    anomalies = 0
    for url in URLS_GET:
        try:
            with urllib.request.urlopen(url, timeout=15) as reponse:
                statut = reponse.getcode()
                corps = reponse.read(200000).decode("utf-8", "replace")
            emit("GET", f"{url} HTTP={statut}")
            if statut != 200:
                anomalies += 1
            try:
                donnees = json.loads(corps)
                if url.endswith("/spectre"):
                    emit("EXTRAIT", {"url": url, "spectre": donnees.get("spectre_ecoute")})
                elif url.endswith("/statut_session"):
                    emit("EXTRAIT", {
                        "url": url,
                        "est_souverain": donnees.get("est_souverain"),
                        "mode": donnees.get("mode"),
                        "session": bool(donnees.get("session")),
                    })
                elif url.endswith("/etat"):
                    tenseur = donnees.get("tenseur_12d") or {}
                    marqueurs = sum(
                        corps.lower().count(mot) for mot in ("simul", "fictif", "capteur", "reel")
                    )
                    emit("EXTRAIT", {
                        "url": url,
                        "temperature_cryo_mk": tenseur.get("temperature_cryo_mk"),
                        "fidelite_quantique_bell": tenseur.get("fidelite_quantique_bell"),
                        "marqueurs_simulation": marqueurs,
                    })
            except json.JSONDecodeError:
                emit("EXTRAIT", {"url": url, "json": "invalide"})
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            emit("GET", f"{url} ERREUR={type(exc).__name__}")
            anomalies += 1

    try:
        requete = urllib.request.Request(
            URL_CHALLENGE,
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(requete, timeout=15) as reponse:
            statut = reponse.getcode()
            donnees = json.loads(reponse.read(200000).decode("utf-8", "replace"))
        emit("POST_CHALLENGE", {
            "HTTP": statut,
            "id_defi": donnees.get("id_defi"),
            "ip_source": donnees.get("ip_source"),
        })
        if statut != 200:
            anomalies += 1
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        emit("POST_CHALLENGE", f"ERREUR={type(exc).__name__}")
        anomalies += 1

    emit("INTERDIT_RAPPEL", "/sas/valider jamais appele en production")
    emit("RESULT_PRODUCTION", "OK" if anomalies == 0 else "ANOMALIE")
    return 1 if anomalies else 0


def parite(racine: Path) -> int:
    titre("parite_local_vps")
    try:
        import paramiko
        from deploiement_vps.charger_credentials_ovh import charger_credentials_ovh
    except Exception as exc:  # noqa: BLE001
        emit("ERREUR_PARITE", f"dependance absente: {type(exc).__name__}")
        return 2

    try:
        identifiants = charger_credentials_ovh()
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            identifiants["hote"],
            username=identifiants["user"],
            password=identifiants["mot_de_passe_ssh"],
            timeout=25,
            look_for_keys=False,
            allow_agent=False,
        )
    except Exception as exc:  # noqa: BLE001
        emit("ERREUR_PARITE", f"connexion: {type(exc).__name__}")
        return 2

    try:
        liste = " ".join("'" + relatif + "'" for relatif in MODULES)
        commande = (
            "cd '/opt/al-mizan/ASTRO-Q°ODE_SYSTEME' && sha256sum " + liste + " 2>&1; echo '---'; "
            "systemctl is-active al-mizan-api-vps; "
            "systemctl show al-mizan-api-vps -p NRestarts --value"
        )
        _, sortie, _ = client.exec_command(commande, timeout=60)
        lignes = sortie.read().decode("utf-8", "replace").splitlines()
    finally:
        client.close()

    distants = {}
    for ligne in lignes:
        morceaux = ligne.split()
        if len(morceaux) == 2 and re.fullmatch(r"[0-9a-f]{64}", morceaux[0]):
            distants[morceaux[1].lstrip("*")] = morceaux[0]

    divergences = 0
    for relatif in MODULES:
        local = racine / relatif
        local_hash = sha256(local) if local.is_file() else "ABSENT"
        distant_hash = distants.get(relatif, "ABSENT")
        egal = local_hash == distant_hash
        if not egal:
            divergences += 1
        emit("FICHIER", f"{relatif} LOCAL={local_hash[:16]} DISTANT={distant_hash[:16]} EGAL={'oui' if egal else 'non'}")

    reste = [ligne for ligne in lignes if ligne and not re.fullmatch(r"[0-9a-f]{64}\s+\S+", ligne)]
    for ligne in reste:
        if ligne.strip() and ligne.strip() != "---":
            emit("SERVICE", ligne.strip())
    emit("RESULT_PARITE", "OK" if divergences == 0 else "DIVERGENCE")
    return 1 if divergences else 0


def tests(racine: Path) -> int:
    titre("tests_cibles")
    commande = [
        sys.executable,
        "-B",
        "-m",
        "unittest",
        "tests.test_passerelle_api_vps",
        "tests.test_comptes_http_mizan",
        "tests.test_site_public_mizan",
        "tests.test_sas_biometrique_souverain",
    ]
    try:
        resultat = subprocess.run(
            commande,
            cwd=str(racine),
            capture_output=True,
            text=True,
            timeout=600,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        emit("ERREUR_TESTS", "timeout 600s")
        return 2
    motif = re.compile(r"^(OK|FAILED|Ran |ERROR:|FAIL:)")
    for ligne in (resultat.stdout + "\n" + resultat.stderr).splitlines():
        if motif.match(ligne.strip()):
            emit("TEST", ligne.strip())
    emit("RESULT_TESTS", "OK" if resultat.returncode == 0 else "ECHEC")
    return 0 if resultat.returncode == 0 else 1


def main() -> int:
    parseur = argparse.ArgumentParser(description="Audit read-only des sens multimodaux Al-Mizan.")
    parseur.add_argument("--racine", help="racine ASTRO-Q-ODE_SYSTEME (defaut: Desktop/IMAM8MAHDI)")
    parseur.add_argument("--sondes", action="store_true", help="sondes camera/micro/STT/spectre/vision/toucher")
    parseur.add_argument("--production", action="store_true", help="GET publics + challenge SAS (jamais valider)")
    parseur.add_argument("--parite", action="store_true", help="comparaison SHA-256 locale/VPS en lecture seule")
    parseur.add_argument("--tests", action="store_true", help="suite ciblee (peut ecrire memoire_aq)")
    arguments = parseur.parse_args()

    racine = trouver_racine(arguments.racine)
    emit("RACINE", racine)
    emit("MODE", {
        "sondes": arguments.sondes,
        "production": arguments.production,
        "parite": arguments.parite,
        "tests": arguments.tests,
    })

    code = inventaire(racine)
    code = max(code, routes(racine))
    code = max(code, classification(racine))
    if arguments.sondes:
        code = max(code, sondes(racine))
    if arguments.production:
        code = max(code, production())
    if arguments.parite:
        code = max(code, parite(racine))
    if arguments.tests:
        code = max(code, tests(racine))

    emit("RESULT", "PASS" if code == 0 else ("ENV" if code == 2 else "ANOMALIE"))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
