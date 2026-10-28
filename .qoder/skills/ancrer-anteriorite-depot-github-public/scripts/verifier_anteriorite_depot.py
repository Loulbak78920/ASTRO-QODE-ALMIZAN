# -*- coding: utf-8 -*-
"""Ancrage d'anteriorite : premier commit publie d'un chemin et empreintes des octets servis.

Deux horloges sont distinguees :
  - serveur : created_at / pushed_at du depot, etablis par GitHub ;
  - client  : date de commit declaree par l'auteur du commit.
Le script etablit qu'un contenu est publie a un commit donne. Il n'etablit pas
un horodatage independant : la date de commit reste declarative.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos"
BRUT = "https://raw.githubusercontent.com"
UA = "anteriorite-depot-github/1.0"


class Echec(Exception):
    """Erreur d'acces a l'API ou au brut : le verdict n'est pas prononcable."""


def entetes(brut: bool = False) -> dict:
    valeurs = {"User-Agent": UA}
    jeton = os.environ.get("GITHUB_TOKEN")
    if jeton:
        valeurs["Authorization"] = "Bearer " + jeton
    if not brut:
        valeurs["Accept"] = "application/vnd.github+json"
    return valeurs


def requete(url: str, brut: bool = False) -> bytes:
    try:
        demande = urllib.request.Request(url, headers=entetes(brut))
        with urllib.request.urlopen(demande, timeout=40) as reponse:
            return reponse.read()
    except urllib.error.HTTPError as erreur:
        reste = erreur.headers.get("X-RateLimit-Remaining") if erreur.headers else None
        if erreur.code in (403, 429) and reste == "0":
            raise Echec(f"LIMITE_API_HTTP_{erreur.code}") from erreur
        raise Echec(f"HTTP_{erreur.code}_SUR_{url}") from erreur
    except urllib.error.URLError as erreur:
        raise Echec(f"RESEAU_{erreur.reason}") from erreur


def json_de(octets: bytes):
    return json.loads(octets.decode("utf-8"))


def ecrire_octets(dossier: Path, nom: str, octets: bytes) -> dict:
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / nom
    chemin.write_bytes(octets)
    return {
        "chemin": str(chemin),
        "sha256": hashlib.sha256(octets).hexdigest(),
        "taille_octets": len(octets),
    }


def nom_sur(texte: str) -> str:
    autorises = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    return "".join(c if c in autorises else "_" for c in texte)[:120]


def normaliser_lf(octets: bytes) -> bytes:
    return octets.replace(b"\r\n", b"\n")


def historique(depot: str, sortie: Path) -> list:
    commits, page = [], 1
    while True:
        octets = requete(f"{API}/{depot}/commits?per_page=100&page={page}")
        lot = json_de(octets)
        if not isinstance(lot, list):
            raise Echec("HISTORIQUE_NON_LISTE")
        ecrire_octets(sortie / "snapshots", f"github_commits_page_{page}.json", octets)
        commits.extend(lot)
        if len(lot) < 100:
            return commits
        page += 1
        if page > 100:
            raise Echec("HISTORIQUE_TROP_LONG")


def premier_commit_du_chemin(depot: str, chemin: str, sortie: Path, index: int):
    base = f"{API}/{depot}/commits?path={urllib.parse.quote(chemin)}&per_page=100"
    dernier, page = None, 1
    while True:
        octets = requete(f"{base}&page={page}")
        lot = json_de(octets)
        if not isinstance(lot, list):
            raise Echec("HISTORIQUE_CHEMIN_NON_LISTE")
        ecrire_octets(sortie / "snapshots", f"chemin_{index}_page_{page}.json", octets)
        if lot:
            dernier = lot[-1]
        if len(lot) < 100:
            return dernier
        page += 1
        if page > 100:
            raise Echec("HISTORIQUE_CHEMIN_TROP_LONG")


def comparer(local: Path | None, distant: bytes) -> dict:
    if local is None:
        return {"copie_locale": None, "copie_locale_presente": False}
    if not local.is_file():
        return {"copie_locale": str(local), "copie_locale_presente": False}
    octets_locaux = local.read_bytes()
    return {
        "copie_locale": str(local),
        "copie_locale_presente": True,
        "sha256_local": hashlib.sha256(octets_locaux).hexdigest(),
        "taille_locale": len(octets_locaux),
        "identique_octets": octets_locaux == distant,
        "identique_hors_crlf": normaliser_lf(octets_locaux) == normaliser_lf(distant),
    }


def analyser_fichier(depot: str, chemin: str, local: Path | None, sortie: Path, index: int) -> dict:
    commit = premier_commit_du_chemin(depot, chemin, sortie, index)
    if commit is None:
        return {
            "chemin_publie": chemin,
            "publie": False,
            "copie_locale": str(local) if local else None,
            "copie_locale_presente": bool(local and local.is_file()),
        }

    sha = commit["sha"]
    url_brut = f"{BRUT}/{depot}/{sha}/{urllib.parse.quote(chemin)}"
    octets = requete(url_brut, brut=True)
    publication = ecrire_octets(
        sortie / "publications", f"{sha[:8]}__{index:02d}__{nom_sur(chemin)}", octets
    )
    donnees_commit = commit.get("commit", {})
    return {
        "chemin_publie": chemin,
        "publie": True,
        "commit": sha,
        "date_client_committer": donnees_commit.get("committer", {}).get("date"),
        "date_client_auteur": donnees_commit.get("author", {}).get("date"),
        "message": (donnees_commit.get("message") or "").splitlines()[0][:160],
        "url_brut": url_brut,
        "sha256_publie": hashlib.sha256(octets).hexdigest(),
        "taille_publiee": len(octets),
        "publication_conservee": publication,
        **comparer(local, octets),
    }


def verdict(fichiers: list, visibilite: str) -> tuple:
    if visibilite != "public":
        return "NON_ETABLI", "DEPOT_NON_PUBLIC"
    publies = [f for f in fichiers if f.get("publie")]
    if not publies:
        return "NON_ETABLI", "AUCUN_FICHIER_PUBLIE"
    exacts = [f for f in publies if f.get("identique_octets") is True]
    if len(publies) == len(fichiers) and len(exacts) == len(fichiers):
        return "ANCRAGE_PUBLIE_ETABLI", "TOUS_PUBLIES_ET_IDENTIQUES"
    return "ANCRAGE_PUBLIE_PARTIEL", "DIVERGENCE_OU_FICHIER_MANQUANT"


def afficher(depot: dict, commits: list, fichiers: list, sortie: Path, resultat: dict) -> None:
    print(f"DEPOT={resultat['depot']['nom']}")
    print(f"VISIBILITE={resultat['depot']['visibilite']}")
    print(f"CREE_LE_SERVEUR={resultat['depot']['cree_le_serveur']}")
    print(f"POUSSE_LE_SERVEUR={resultat['depot']['pousse_le_serveur']}")
    print(f"COMMITS_TOTAL={len(commits)}")
    if commits:
        print(f"COMMIT_PLUS_ANCIEN={commits[-1]['sha']}")
        print(f"DATE_PLUS_ANCIEN_CLIENT={commits[-1]['commit']['committer']['date']}")

    for fichier in fichiers:
        print(f"FICHIER={fichier['chemin_publie']}")
        print(f"PUBLIE={fichier.get('publie')}")
        if fichier.get("publie"):
            print(f"COMMIT={fichier['commit']}")
            print(f"DATE_CLIENT={fichier.get('date_client_committer')}")
        print(f"COPIE_LOCALE={fichier.get('copie_locale') or 'ABSENTE'}")
        for cle in ("identique_octets", "identique_hors_crlf"):
            valeur = fichier.get(cle)
            print(f"{cle.upper()}={'NA' if valeur is None else valeur}")
        print(f"SHA256_PUBLIE={fichier.get('sha256_publie') or '-'}")
        print(f"SHA256_LOCAL={fichier.get('sha256_local') or '-'}")

    print(f"SORTIE={sortie}")
    print(f"VERDICT={resultat['verdict']}")
    print(f"RAISON={resultat['raison']}")
    print("NOTE_HORLOGES=dates_client_declaratives_created_at_et_pushed_at_serveur")


def main(argv: list | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Premier commit publie d'un chemin et comparaison octet a octet."
    )
    analyseur.add_argument("--depot", required=True, help="owner/repo du depot public")
    analyseur.add_argument(
        "--fichier",
        action="append",
        required=True,
        metavar="CHEMIN[=COPIE_LOCALE]",
        help="chemin publie, suivi optionnellement de la copie locale apres =",
    )
    analyseur.add_argument(
        "--sortie", default="verification_anteriorite", help="dossier des preuves"
    )
    options = analyseur.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    sortie = Path(options.sortie).resolve()
    try:
        octets_depot = requete(f"{API}/{options.depot}")
        depot = json_de(octets_depot)
        ecrire_octets(sortie / "snapshots", "github_depot.json", octets_depot)

        commits = historique(options.depot, sortie)
        fichiers = []
        for index, specification in enumerate(options.fichier, 1):
            chemin, _, local = specification.partition("=")
            chemin = chemin.strip()
            copie = Path(local).resolve() if local.strip() else None
            fichiers.append(analyser_fichier(options.depot, chemin, copie, sortie, index))

        visibilite = depot.get("visibility") or ("public" if not depot.get("private") else "private")
        nom_verdict, raison = verdict(fichiers, visibilite)
        resultat = {
            "genere_le": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "depot": {
                "nom": options.depot,
                "url": f"https://github.com/{options.depot}",
                "visibilite": visibilite,
                "cree_le_serveur": depot.get("created_at"),
                "pousse_le_serveur": depot.get("pushed_at"),
                "branche_par_defaut": depot.get("default_branch"),
            },
            "commits": {
                "total": len(commits),
                "plus_recent": {
                    "sha": commits[0]["sha"],
                    "date_client": commits[0]["commit"]["committer"]["date"],
                } if commits else None,
                "plus_ancien": {
                    "sha": commits[-1]["sha"],
                    "date_client": commits[-1]["commit"]["committer"]["date"],
                } if commits else None,
            },
            "fichiers": fichiers,
            "verdict": nom_verdict,
            "raison": raison,
            "note_horloges": (
                "Les dates de commit sont declarees par le client Git. Seuls created_at, "
                "pushed_at et la disponibilite du brut au SHA sont etablis par GitHub. "
                "Aucun horodatage independant n'est produit par ce script."
            ),
        }
        ecrire_octets(
            sortie,
            "anteriorite.json",
            json.dumps(resultat, ensure_ascii=False, indent=2).encode("utf-8"),
        )
        afficher(depot, commits, fichiers, sortie, resultat)
        return 0 if nom_verdict == "ANCRAGE_PUBLIE_ETABLI" else 1
    except Echec as erreur:
        print(f"ERREUR={erreur}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
