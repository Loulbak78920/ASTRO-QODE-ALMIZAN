# -*- coding: utf-8 -*-
"""Rejoue une matrice de fixtures pour un script d'audit en lecture seule.

Chaque cas cree sa propre racine jetable hors du dossier du Skill, ecrit les
fichiers demandes, execute la commande une seule fois avec le code de retour lu
hors pipe, puis verifie rc, lignes attendues et lignes interdites. Echec si le
secret factice apparait dans stdout ou stderr ; la sortie affichee est censuree.

Usage :
    py -3 -B rejouer_matrice.py --matrice <matrice.json> [--garder] [--max-lignes N]

Schema de la matrice (JSON UTF-8) :
{
  "secret": "FAKE-...",
  "script": "C:/.../script_audite.py",
  "cas": [
    {
      "nom": "A",
      "fichiers": {
        "notes.md": "ligne 1\\n{secret}\\n",
        "gros.py": {"octets": 2099999},
        "enc.py": {"texte": "x=1\\n{secret}\\n", "encodage": "utf-16"}
      },
      "secrets": "secrets/ovh.json",
      "commande": ["py", "-3", "-B", "{script}", "--secrets", "{secrets}", "--racine", "{racine}"],
      "attendu_rc": 1,
      "contient": ["FUITE total=1", "FUITE notes.md:2"],
      "absent": ["RESULT OK"]
    }
  ]
}

Placeholders : {racine}, {secrets}, {script}, {secret}.
"base" (optionnel) cree les racines sous ce repertoire au lieu du temporaire
systeme : indispensable pour un cas dont le chemin doit contenir un composant
ignore (par exemple .qoder).
"secrets" designe le fichier de secrets relatif a la racine ; absent, il vaut
secrets/ovh.json et est cree avec les cles minimales si "fichiers" ne le fournit
pas. "contient" et "absent" portent sur stdout ; le secret est teste sur
stdout + stderr. Sortie : PASS/FAIL par cas, puis MATRICE cas=N echecs=M ;
rc 0 si aucun echec, 1 sinon, 2 sur matrice invalide.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SECRETS_DEFAUT = "secrets/ovh.json"


def _ecrire(chemin: Path, valeur, secret: str) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(valeur, str):
        chemin.write_bytes(valeur.replace("{secret}", secret).encode("utf-8"))
        return
    if not isinstance(valeur, dict):
        raise ValueError(f"valeur de fichier invalide: {chemin}")
    if "octets" in valeur:
        taille = int(valeur["octets"])
        marqueur = (secret + "\n").encode("utf-8")
        if taille < len(marqueur):
            raise ValueError(f"octets trop petit pour le secret: {chemin}")
        chemin.write_bytes(b"#" * (taille - len(marqueur)) + marqueur)
        return
    texte = str(valeur.get("texte", "")).replace("{secret}", secret)
    chemin.write_bytes(texte.encode(str(valeur.get("encodage", "utf-8"))))


def _secrets_par_defaut(secret: str) -> str:
    return json.dumps(
        {
            "hote": "h",
            "user": "u",
            "mot_de_passe_ssh": secret,
            "mot_de_passe_permanent": secret,
            "mot_de_passe_temporaire": "",
        }
    )


def _substituer(jeton: str, valeurs: dict) -> str:
    for cle, valeur in valeurs.items():
        jeton = jeton.replace("{" + cle + "}", valeur)
    return jeton


def rejouer(matrice: Path, garder: bool, max_lignes: int) -> int:
    donnees = json.loads(matrice.read_text(encoding="utf-8"))
    secret = str(donnees.get("secret") or "")
    if not secret:
        print("MATRICE INVALIDE: cle 'secret' absente")
        return 2
    script = Path(str(donnees.get("script") or ""))
    if not script.is_file():
        print(f"MATRICE INVALIDE: script absent: {script}")
        return 2
    cas = donnees.get("cas") or []
    if not isinstance(cas, list) or not cas:
        print("MATRICE INVALIDE: 'cas' vide")
        return 2

    empreinte = hashlib.sha256(script.read_bytes()).hexdigest()
    print(f"SCRIPT {script} sha256={empreinte}")
    parent = Path(str(donnees["base"])) if donnees.get("base") else None
    if parent is not None and not parent.is_dir():
        print(f"MATRICE INVALIDE: base absente: {parent}")
        return 2
    base = Path(tempfile.mkdtemp(prefix="cov-matrice-", dir=str(parent) if parent else None))
    print(f"BASE {base}")

    echecs_total = 0
    try:
        for index, cas_i in enumerate(cas, start=1):
            nom = str(cas_i.get("nom") or f"cas{index}")
            racine = base / f"{index:02d}-{nom}"
            racine.mkdir(parents=True, exist_ok=True)
            secrets_rel = str(cas_i.get("secrets") or SECRETS_DEFAUT)
            fichiers = cas_i.get("fichiers") or {}
            for rel, valeur in fichiers.items():
                _ecrire(racine / rel, valeur, secret)
            if secrets_rel not in fichiers and not (racine / secrets_rel).exists():
                _ecrire(racine / secrets_rel, _secrets_par_defaut(secret), secret)

            valeurs = {
                "racine": str(racine),
                "secrets": str(racine / secrets_rel),
                "script": str(script),
                "secret": secret,
            }
            commande = [_substituer(str(j), valeurs) for j in cas_i.get("commande") or []]
            if not commande:
                print(f"MATRICE INVALIDE: cas {nom} sans 'commande'")
                return 2

            essai = subprocess.run(
                commande,
                cwd=str(racine),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            sortie = essai.stdout or ""
            erreurs = essai.stderr or ""
            fuite = secret in sortie or secret in erreurs
            echecs = []
            attendu = cas_i.get("attendu_rc")
            if attendu is not None and essai.returncode != int(attendu):
                echecs.append(f"rc={essai.returncode} attendu={int(attendu)}")
            if fuite:
                echecs.append("SECRET_DANS_LA_SORTIE")
            for attendue in cas_i.get("contient") or []:
                if str(attendue) not in sortie:
                    echecs.append(f"manque: {attendue}")
            for interdite in cas_i.get("absent") or []:
                if str(interdite) in sortie:
                    echecs.append(f"interdit present: {interdite}")

            etat = "PASS" if not echecs else "FAIL"
            print(f"{etat} cas={nom} rc={essai.returncode}")
            for message in echecs:
                print(f"  {message}")
            if fuite:
                print("  sortie non affichee: le secret y figure")
            else:
                for ligne in sortie.replace(secret, "<secret>").splitlines()[:max_lignes]:
                    print(f"  | {ligne}")
                if len(sortie.splitlines()) > max_lignes:
                    print(f"  | ... ({len(sortie.splitlines()) - max_lignes} lignes de plus)")
                if erreurs.strip():
                    for ligne in erreurs.replace(secret, "<secret>").splitlines()[:max_lignes]:
                        print(f"  ! {ligne}")
            echecs_total += 1 if echecs else 0
    finally:
        if garder:
            print(f"CONSERVE {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)
            print(f"NETTOYE {base} existe={base.exists()}")

    print(f"MATRICE cas={len(cas)} echecs={echecs_total}")
    return 0 if echecs_total == 0 else 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parseur = argparse.ArgumentParser(description="Rejouer une matrice de fixtures de couverture.")
    parseur.add_argument("--matrice", required=True, type=Path)
    parseur.add_argument("--garder", action="store_true", help="conserver la base de fixtures")
    parseur.add_argument("--max-lignes", type=int, default=40, help="lignes de sortie affichees par cas")
    args = parseur.parse_args()
    if args.max_lignes < 1:
        print("usage: --max-lignes doit etre >= 1")
        return 2
    try:
        return rejouer(args.matrice, args.garder, args.max_lignes)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"MATRICE INVALIDE: {type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
