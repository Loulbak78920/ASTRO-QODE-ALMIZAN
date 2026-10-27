# -*- coding: utf-8 -*-
"""Lecture en lecture seule des journaux nginx d'un VPS (SSH/sudo) ou d'une copie locale.

Une seule passe d'agrégation sur une seule fenêtre ; la somme des statuts est
comparée au nombre de lignes analysées. Le mot de passe n'est jamais affiché.
"""

from __future__ import annotations

import argparse
import importlib.util
import ipaddress
import json
import os
import re
import shlex
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

FORMAT_DATE = "%d/%b/%Y:%H:%M:%S %z"
CHEMIN_ACCESS = "/var/log/nginx/access.log"
CHEMIN_ERROR = "/var/log/nginx/error.log"
METHODES_STANDARD = {
    "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "CONNECT", "TRACE",
}

MOTIF_LIGNE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<date>[^\]]+)\] '
    r'"(?P<requete>[^"]*)" '
    r'(?P<statut>\d{3}) (?P<taille>\S+)'
    r'(?: "(?P<referent>[^"]*)" "(?P<ua>[^"]*)")?'
)
UA_VERIFICATION = re.compile(
    r"python-urllib|python-requests|curl/|wget/|httpie|go-http-client", re.IGNORECASE
)
CHEMIN_SCAN = re.compile(
    r"\.env|\.git|\.aws|\.docker|\.claude|\.cursor|\.amplifyrc|\.boto|"
    r"xmlrpc\.php|wp-admin|wp-login|/sdk/weblanguage",
    re.IGNORECASE,
)

SIGNATURES_SCAN_EXTRA = (
    "wp-content/",
    "wp-includes",
    "phpmyadmin",
    "/cgi-bin/",
    "/server-status",
    "boaform",
    "hnap1",
    "gponform",
    "autodiscover",
    "solr/",
    "vendor/phpunit",
    "aws-exports.js",
    "runtime-config.js",
    "env-config.js",
    "app.config.js",
    "netrc",
    "npmrc",
    "s3cfg",
    "composer.json",
    "appsettings.",
    "dockerfile",
    "_profiler",
    "auth.json",
)
EXTENSIONS_SCAN = (".php", ".asp", ".aspx", ".jsp", ".cgi", ".ini", ".bak", ".old", ".sql")
EXTENSIONS_ASSET = (
    ".ico", ".css", ".js", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif",
    ".woff", ".woff2", ".ttf", ".map", ".mp4", ".webmanifest",
)

PLAGES_CLOUDFLARE = (
    "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22", "104.16.0.0/13",
    "104.24.0.0/14", "108.162.192.0/18", "131.0.72.0/22", "141.101.64.0/18",
    "162.158.0.0/15", "172.64.0.0/13", "173.245.48.0/20", "188.114.96.0/20",
    "190.93.240.0/20", "197.234.240.0/22", "198.41.128.0/17",
)
RESEAUX_CLOUDFLARE = tuple(ipaddress.ip_network(plage) for plage in PLAGES_CLOUDFLARE)

MOTIF_MSYS = re.compile(r"^[A-Za-z]:[\\/](?:[^\\/]+[\\/])*?Git[\\/](.*)$", re.IGNORECASE)

INTERPRETATIONS_ERREUR = (
    (
        "upstream prematurely closed connection while reading response header",
        "upstream coupé avant les en-têtes (crash ou timeout applicatif) — vérifier si la route repasse en 200",
    ),
    (
        "upstream prematurely closed connection while reading upstream",
        "coupure pendant le corps — souvent un client qui interrompt un gros fichier (/video)",
    ),
    ("upstream timed out", "timeout upstream — vérifier la charge de al-mizan-api-vps"),
    ("no live upstreams", "aucun upstream disponible — service applicatif arrêté ?"),
    ("connect() failed", "connexion upstream refusée — port 8095 injoignable"),
    ("client intended to send too large body", "corps client au-delà de client_max_body_size (50M)"),
    ("SSL_do_handshake", "échec de négociation TLS"),
    ("worker_connections are not enough", "saturation des workers nginx"),
)


def analyser_date(texte: str) -> datetime | None:
    try:
        return datetime.strptime(texte, FORMAT_DATE)
    except ValueError:
        return None


def analyser_date_souple(texte: str) -> datetime | None:
    valeur = texte.strip()
    if not re.search(r"[+-]\d{4}$", valeur):
        valeur += " +0000"
    return analyser_date(valeur)


def classer_404(chemin: str) -> str:
    bas = chemin.lower()
    if (
        CHEMIN_SCAN.search(bas)
        or any(sig in bas for sig in SIGNATURES_SCAN_EXTRA)
        or bas.endswith(EXTENSIONS_SCAN)
    ):
        return "scan"
    if bas.endswith(EXTENSIONS_ASSET):
        return "vrai_manque_candidat"
    return "inconnu"


def est_cloudflare(ip: str) -> bool:
    try:
        adresse = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(adresse in reseau for reseau in RESEAUX_CLOUDFLARE)


def normaliser_chemin_msys(valeur: str | None) -> str | None:
    """Git Bash réécrit `/favicon.ico` en `C:/Program Files/Git/favicon.ico`.

    Le préfixe d'installation Git n'est jamais un chemin serveur : le retirer
    restitue le chemin Unix voulu. Les chemins Windows réels sont inchangés.
    """
    if not valeur:
        return valeur
    trouve = MOTIF_MSYS.match(valeur.strip())
    if not trouve:
        return valeur
    return "/" + trouve.group(1).replace("\\", "/")


def interpreter_erreurs(journal_error: str | None) -> dict | None:
    if not journal_error:
        return None
    total = None
    lignes = []
    for ligne in journal_error.splitlines():
        if ligne.startswith("UPSTREAM_FERME_TOTAL="):
            total = ligne.split("=", 1)[1].strip() or None
            continue
        if "upstream" in ligne.lower():
            lignes.append(ligne.strip())
    interpretations = Counter()
    for motif, sens in INTERPRETATIONS_ERREUR:
        compte = sum(1 for ligne in lignes if motif in ligne)
        if compte:
            interpretations[sens] = compte
    return {
        "total_upstream": total,
        "interpretations": dict(interpretations),
        "dernieres": lignes[-5:],
    }


def charger_identifiants(racine: Path) -> tuple[str, str, str, str]:
    """Retourne (hote, user, mot_de_passe, origine) sans afficher le mot de passe."""
    chargeur = racine / "deploiement_vps" / "charger_credentials_ovh.py"
    if chargeur.is_file():
        spec = importlib.util.spec_from_file_location("charger_credentials_ovh", chargeur)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        hote, user, mdp = module.hote_user_mdp()
        return str(hote), str(user), str(mdp), "deploiement_vps.charger_credentials_ovh"

    chemin = Path(
        os.environ.get("MIZAN_OVH_SECRETS_PATH")
        or (racine / "secrets" / "ovh_vps_ssh.json")
    )
    if not chemin.is_file():
        raise RuntimeError(f"secrets introuvables ({chemin}) et chargeur projet absent")
    data = json.loads(chemin.read_text(encoding="utf-8"))
    manquantes = [c for c in ("hote", "user", "mot_de_passe_ssh") if not data.get(c)]
    if manquantes:
        raise RuntimeError(f"cles manquantes dans {chemin.name} : {', '.join(manquantes)}")
    return str(data["hote"]), str(data["user"]), str(data["mot_de_passe_ssh"]), "secrets/ovh_vps_ssh.json"


def executer(client, commande: str, mot_de_passe: str, sudo: bool = True) -> tuple[int, str, str]:
    if sudo:
        commande = "sudo -S -p '' bash -c " + shlex.quote(commande)
    stdin, stdout, stderr = client.exec_command(commande, timeout=60)
    if sudo:
        stdin.write(mot_de_passe + "\n")
        stdin.flush()
    sortie = stdout.read().decode("utf-8", "replace")
    erreur = stderr.read().decode("utf-8", "replace")
    return stdout.channel.recv_exit_status(), sortie, erreur


def analyser(texte: str) -> tuple[list[dict], list[str]]:
    entrees: list[dict] = []
    ignorees: list[str] = []
    for ligne in texte.splitlines():
        if not ligne.strip():
            continue
        trouve = MOTIF_LIGNE.match(ligne)
        if not trouve:
            ignorees.append(ligne)
            continue
        donnees = trouve.groupdict()
        horodatage = analyser_date(donnees["date"])
        if horodatage is None:
            ignorees.append(ligne)
            continue
        methode, _, reste = donnees["requete"].partition(" ")
        donnees["methode"] = methode or "-"
        donnees["chemin"] = reste.split(" ")[0] if reste else "-"
        donnees["dt"] = horodatage
        donnees["ua"] = donnees.get("ua") or ""
        entrees.append(donnees)
    return entrees, ignorees


def fenetre(lignes: list[dict]) -> str:
    if not lignes:
        return "AUCUNE"
    debut = min(e["dt"] for e in lignes)
    fin = max(e["dt"] for e in lignes)
    return f"{debut.strftime(FORMAT_DATE)} -> {fin.strftime(FORMAT_DATE)}"


def afficher_rapport(
    source: str,
    origine: str,
    lignes_retournees: int,
    entrees: list[dict],
    ignorees: list[str],
    retenues: list[dict],
    filtre: str,
    journal_error: str | None,
    apres: datetime | None = None,
    route_nom: str | None = None,
    sortie_json: bool = False,
) -> int:
    statuts = Counter(e["statut"] for e in retenues)
    somme = sum(statuts.values())
    coherent = somme == len(retenues)
    fenetre_analyse = fenetre(retenues)
    total_fenetre = fenetre(entrees)
    non_standard = [e for e in entrees if e["methode"] not in METHODES_STANDARD]
    verification = [e for e in retenues if UA_VERIFICATION.search(e["ua"])]
    scans = [e for e in retenues if CHEMIN_SCAN.search(e["chemin"])]
    erreurs_5xx = [e for e in retenues if e["statut"].startswith("5")]

    retenues_404 = [e for e in retenues if e["statut"] == "404"]
    chemins_404 = Counter(e["chemin"].split("?")[0] for e in retenues_404)
    compteurs_404: dict[str, Counter] = {
        "scan": Counter(),
        "vrai_manque_candidat": Counter(),
        "inconnu": Counter(),
    }
    for chemin, compte in chemins_404.items():
        compteurs_404[classer_404(chemin)][chemin] = compte
    classes_404 = Counter({classe: sum(c.values()) for classe, c in compteurs_404.items() if c})
    tops_404 = {
        classe: [[chemin, n] for chemin, n in compteur.most_common(10)]
        for classe, compteur in compteurs_404.items()
    }
    ips_cloudflare = sorted({e["ip"] for e in retenues if est_cloudflare(e["ip"])})
    erreurs_analyse = interpreter_erreurs(journal_error)

    apres_donnees = None
    if apres is not None:
        retenues_apres = [e for e in retenues if e["dt"] >= apres]
        statuts_apres = Counter(e["statut"] for e in retenues_apres)
        apres_donnees = {
            "instant": apres.strftime(FORMAT_DATE),
            "total": len(retenues_apres),
            "statuts": dict(sorted(statuts_apres.items())),
            "404": statuts_apres.get("404", 0),
            "top_404": Counter(
                e["chemin"].split("?")[0]
                for e in retenues_apres
                if e["statut"] == "404"
            ).most_common(10),
        }

    route_donnees = None
    if route_nom:
        route_donnees = [
            {
                "date": e["date"],
                "statut": e["statut"],
                "taille": e["taille"],
                "ua": e["ua"],
            }
            for e in retenues
            if e["chemin"].split("?")[0] == route_nom
        ][-40:]

    avertissements: list[str] = []
    if ignorees:
        avertissements.append(
            f"{len(ignorees)} ligne(s) non parsée(s) : première ligne tronquée par tail ou format inattendu."
        )
    if ips_cloudflare:
        avertissements.append(
            f"{len(ips_cloudflare)} IP d'edge Cloudflare : l'IP réelle du visiteur n'est pas dans le format combined."
        )
    if retenues and classes_404.get("scan", 0) / len(retenues) > 0.5:
        avertissements.append(
            f"{classes_404['scan'] / len(retenues):.0%} des requêtes sont des 404 de scan : bruit de robots, pas un incident."
        )
    if not retenues:
        avertissements.append(
            "Aucune requête dans la fenêtre : élargir --lignes ou vérifier --depuis (UTC)."
        )

    donnees = {
        "resultat": "PASS" if coherent else "ECHEC",
        "source": source,
        "origine": origine,
        "lignes_retournees": lignes_retournees,
        "lignes_parsees": len(entrees),
        "ignorees": len(ignorees),
        "methodes_non_standard": len(non_standard),
        "fenetre_totale": total_fenetre,
        "filtre": filtre,
        "lignes_analysees": len(retenues),
        "fenetre_analysee": fenetre_analyse,
        "statuts": dict(sorted(statuts.items())),
        "somme_statuts": somme,
        "somme_ok": coherent,
        "ip_distinctes": len({e["ip"] for e in retenues}),
        "top_ip": Counter(e["ip"] for e in retenues).most_common(8),
        "top_chemins": Counter(e["chemin"].split("?")[0] for e in retenues).most_common(10),
        "cinq_xx": [
            {cle: e[cle] for cle in ("date", "ip", "methode", "chemin", "statut", "ua")}
            for e in erreurs_5xx[:20]
        ],
        "candidats_verification": {
            "total": len(verification),
            "top": Counter(e["chemin"].split("?")[0] for e in verification).most_common(5),
        },
        "candidats_scan": {
            "total": len(scans),
            "top": Counter(e["chemin"].split("?")[0] for e in scans).most_common(5),
        },
        "quatre_cent_quatre": {
            "total": len(retenues_404),
            "classes": dict(classes_404),
            "top_scan": tops_404["scan"],
            "top_vrai_manque_candidat": tops_404["vrai_manque_candidat"],
            "top_inconnu": tops_404["inconnu"],
        },
        "ips_cloudflare": ips_cloudflare,
        "erreurs": erreurs_analyse,
        "apres": apres_donnees,
        "route": {"nom": route_nom, "requetes": route_donnees} if route_nom else None,
        "avertissements": avertissements,
        "exemples_ignorees": [ligne[:160] for ligne in ignorees[:3]],
    }

    if sortie_json:
        print(json.dumps(donnees, ensure_ascii=False, indent=2))
        return 0 if coherent else 3

    print(f"RESULTAT={'PASS' if coherent else 'ECHEC'}")
    print(f"SOURCE={source}")
    print(f"SOURCE_IDENTIFIANTS={origine}")
    print(f"LIGNES_RETOURNEES={lignes_retournees}")
    print(f"LIGNES_PARSEES={len(entrees)}")
    print(f"IGNOREES={len(ignorees)}")
    print(f"METHODES_NON_STANDARD={len(non_standard)}")
    print(f"FENETRE_TOTALE={total_fenetre}")
    print(f"FILTRE={filtre}")
    print(f"LIGNES_ANALYSEES={len(retenues)}")
    print(f"FENETRE_ANALYSEE={fenetre_analyse}")
    print("STATUTS=" + (", ".join(f"{c}:{n}" for c, n in sorted(statuts.items())) or "AUCUN"))
    print(f"SOMME_STATUTS={somme}")
    print(f"SOMME_OK={'OUI' if coherent else 'NON'}")
    print(f"IP_DISTINCTES={len({e['ip'] for e in retenues})}")
    print("TOP_IP=")
    for ip, n in donnees["top_ip"]:
        print(f"  {ip}\t{n}")
    if not donnees["top_ip"]:
        print("  AUCUNE")

    print("TOP_CHEMINS=")
    chemins = Counter(e["chemin"].split("?")[0] for e in retenues)
    for chemin, n in chemins.most_common(10):
        print(f"  {n:5d}  {chemin}")

    print(f"5XX={len(erreurs_5xx)}")
    for e in erreurs_5xx[:20]:
        print(f"  {e['date']} {e['ip']} {e['methode']} {e['chemin']} -> {e['statut']} ua={e['ua'][:50]}")

    print(f"CANDIDATS_VERIFICATION={len(verification)}")
    for chemin, n in Counter(e["chemin"].split("?")[0] for e in verification).most_common(5):
        print(f"  {n:5d}  {chemin}")
    print(f"CANDIDATS_SCAN={len(scans)}")
    for chemin, n in Counter(e["chemin"].split("?")[0] for e in scans).most_common(5):
        print(f"  {n:5d}  {chemin}")

    print(f"404_TOTAL={donnees['quatre_cent_quatre']['total']}")
    print(
        "404_CLASSES="
        + (", ".join(f"{c}:{n}" for c, n in sorted(classes_404.items())) or "AUCUNE")
    )
    for etiquette, cle in (
        ("404_TOP_SCAN", "top_scan"),
        ("404_TOP_VRAI_MANQUE", "top_vrai_manque_candidat"),
        ("404_TOP_INCONNU", "top_inconnu"),
    ):
        if donnees["quatre_cent_quatre"][cle]:
            print(f"{etiquette}=")
            for chemin, n in donnees["quatre_cent_quatre"][cle]:
                print(f"  {n:5d}  {chemin}")

    print(f"IPS_CLOUDFLARE={len(ips_cloudflare)}")
    if erreurs_analyse and erreurs_analyse["interpretations"]:
        print("ERREURS_INTERPRETATIONS=")
        for sens, n in erreurs_analyse["interpretations"].items():
            print(f"  {n:5d}  {sens}")

    if apres_donnees is not None:
        print(f"APRES={apres_donnees['instant']}")
        print(f"APRES_TOTAL={apres_donnees['total']}")
        print(
            "APRES_STATUTS="
            + (
                ", ".join(f"{c}:{n}" for c, n in apres_donnees["statuts"].items())
                or "AUCUN"
            )
        )
        print(f"404_APRES={apres_donnees['404']}")
        if apres_donnees["top_404"]:
            print("APRES_TOP_404=")
            for chemin, n in apres_donnees["top_404"]:
                print(f"  {n:5d}  {chemin}")

    if route_donnees is not None:
        print(f"ROUTE={route_nom}")
        print(f"ROUTE_REQUETES={len(route_donnees)}")
        for d in route_donnees:
            print(f"  {d['date']} -> {d['statut']} ({d['taille']} o) ua={d['ua'][:50]}")

    if avertissements:
        print("AVERTISSEMENTS=")
        for avertissement in avertissements:
            print(f"  - {avertissement}")

    if ignorees:
        print("EXEMPLES_IGNOREES=")
        for ligne in ignorees[:3]:
            print("  " + ligne[:160])

    if journal_error is not None:
        print("ERROR_LOG=")
        for ligne in journal_error.strip().splitlines():
            print("  " + ligne)

    return 0 if coherent else 3


def principal(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Lire et agréger les journaux nginx (lecture seule)."
    )
    analyseur.add_argument("--lignes", type=int, default=2000, help="nombre de lignes lues (défaut 2000)")
    analyseur.add_argument("--fichier-local", help="analyser une copie locale au lieu de SSH")
    analyseur.add_argument("--depuis", help='début de fenêtre, ex. "27/Oct/2026:01:55:31" (UTC par défaut)')
    analyseur.add_argument("--apres", help='ne compter que les requêtes après cet instant, ex. "27/Oct/2026:01:55:31"')
    analyseur.add_argument("--route", help="chronologie d'un chemin exact, ex. /favicon.ico")
    analyseur.add_argument("--erreurs-fichier", help="error.log local (mode --fichier-local)")
    analyseur.add_argument("--json", action="store_true", help="sortie JSON au lieu des blocs CLÉ=VALEUR")
    analyseur.add_argument("--chemin", help="regex de filtre sur le chemin de la requête")
    analyseur.add_argument("--journal", default=CHEMIN_ACCESS, help="chemin distant du journal d'accès")
    analyseur.add_argument("--sans-erreurs", action="store_true", help="ne pas lire error.log")
    analyseur.add_argument("--erreurs-lignes", type=int, default=20, help="lignes de error.log (défaut 20)")
    analyseur.add_argument("--racine", help="racine ASTRO-Q°ODE_SYSTEME (sinon MIZAN_RACINE)")
    arguments = analyseur.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    arguments.route = normaliser_chemin_msys(arguments.route)
    arguments.chemin = normaliser_chemin_msys(arguments.chemin)
    arguments.journal = normaliser_chemin_msys(arguments.journal)

    depuis = None
    if arguments.depuis:
        depuis = analyser_date_souple(arguments.depuis)
        if depuis is None:
            print("RESULTAT=ECHEC")
            print(f"ERREUR_FENETRE=illisible ({arguments.depuis})")
            return 2

    apres = None
    if arguments.apres:
        apres = analyser_date_souple(arguments.apres)
        if apres is None:
            print("RESULTAT=ECHEC")
            print(f"ERREUR_APRES=illisible ({arguments.apres})")
            return 2

    if arguments.fichier_local:
        try:
            texte = Path(arguments.fichier_local).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print("RESULTAT=ECHEC")
            print(f"ERREUR_LECTURE={exc}")
            return 1
        journal_error = None
        if arguments.erreurs_fichier:
            try:
                brut = Path(arguments.erreurs_fichier).read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError as exc:
                print("RESULTAT=ECHEC")
                print(f"ERREUR_LECTURE_ERREURS={exc}")
                return 1
            journal_error = (
                f"UPSTREAM_FERME_TOTAL="
                f"{brut.count('upstream prematurely closed')}\n{brut.strip()}"
            )
        entrees, ignorees = analyser(texte)
        retenues = filtrer(entrees, depuis, arguments.chemin)
        filtre = f"depuis={arguments.depuis or '-'} chemin={arguments.chemin or '-'}"
        return afficher_rapport(
            "fichier", "aucun", len(texte.splitlines()), entrees, ignorees, retenues, filtre,
            journal_error, apres, arguments.route, arguments.json,
        )

    racine = Path(arguments.racine) if arguments.racine else None
    if racine is None:
        env = os.environ.get("MIZAN_RACINE")
        if env:
            racine = Path(env)
        else:
            candidats = [
                Path.cwd() / "ASTRO-Q°ODE_SYSTEME",
                Path(r"C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"),
            ]
            racine = next((c for c in candidats if c.is_dir()), candidats[-1])

    try:
        hote, utilisateur, mot_de_passe, origine = charger_identifiants(racine)
    except Exception as exc:  # message sans secret : le chargeur ne renvoie pas le mot de passe
        print("RESULTAT=ECHEC")
        print(f"ERREUR_IDENTIFIANTS={type(exc).__name__}: {exc}")
        return 1

    try:
        import paramiko
    except ImportError:
        print("RESULTAT=ECHEC")
        print("ERREUR_DEPENDANCE=paramiko absent (py -3 -m pip install paramiko)")
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hote, username=utilisateur, password=mot_de_passe,
            timeout=25, banner_timeout=25, auth_timeout=25,
        )
        code, texte, erreur = executer(client, f"tail -n {arguments.lignes} {arguments.journal}", mot_de_passe)
        if code != 0:
            print("RESULTAT=ECHEC")
            print(f"ERREUR_SSH_CODE={code}")
            print(f"ERREUR_SSH_DETAIL={erreur.strip()[:300]}")
            return 1

        journal_error = None
        if not arguments.sans_erreurs:
            commande = (
                "printf '###COMPTE###\\n'; "
                f"grep -c 'upstream prematurely closed' {CHEMIN_ERROR} 2>/dev/null || true; "
                "printf '###FIN###\\n'; "
                f"tail -n {arguments.erreurs_lignes} {CHEMIN_ERROR} 2>/dev/null || true"
            )
            _, brut, _ = executer(client, commande, mot_de_passe)
            compte, _, reste = brut.partition("###FIN###")
            compte = compte.replace("###COMPTE###", "").strip().splitlines()
            journal_error = (
                f"UPSTREAM_FERME_TOTAL={compte[-1] if compte else 'inconnu'}\n" + reste.strip()
            )
    finally:
        client.close()

    entrees, ignorees = analyser(texte)
    retenues = filtrer(entrees, depuis, arguments.chemin)
    filtre = f"depuis={arguments.depuis or '-'} chemin={arguments.chemin or '-'}"
    return afficher_rapport(
        "ssh", origine, len(texte.splitlines()), entrees, ignorees, retenues, filtre,
        journal_error, apres, arguments.route, arguments.json,
    )


def filtrer(entrees: list[dict], depuis: datetime | None, chemin: str | None) -> list[dict]:
    retenues = entrees
    if depuis is not None:
        retenues = [e for e in retenues if e["dt"] >= depuis]
    if chemin:
        motif = re.compile(chemin)
        retenues = [e for e in retenues if motif.search(e["chemin"])]
    return retenues


if __name__ == "__main__":
    raise SystemExit(principal())
