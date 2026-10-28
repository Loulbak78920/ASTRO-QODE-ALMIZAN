#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comparer un bytecode deploye a une source recompilee (lecture seule).

Deux modes :
  onchain  : lit eth_getTransactionReceipt et eth_getCode, recompile la source
             avec solc en standard-json, compare le runtime deploye au runtime
             recompile, puis separe les differences de code de l'auxdata CBOR et
             des valeurs immuables injectees au deploiement.
  fichiers : compare deux fichiers hex de runtime deja captures, sans reseau ni
             compilateur (rejeu hors ligne d'un instantane).

Le verdict ne porte que sur le code executable : le suffixe auxdata CBOR
(empreinte IPFS, version solc) est retire avant comparaison, apres masquage des
valeurs immuables. Deux blocs dont seul l'auxdata differe sont CORRESPONDANCE_FORTE.

Codes de retour :
  0  IDENTIQUE ou CORRESPONDANCE_FORTE (et artefact coherent s'il est fourni)
  1  CORRESPONDANCE_PARTIELLE, DIVERGENCE ou artefact incoherent
  2  entree invalide, reseau indisponible, transaction echouee ou code vide
  3  compilation impossible

Aucun fichier n'est ecrit sauf --out. Aucune cle, aucun secret n'est requis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALPHABET_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
RE_SOLC = re.compile(r"^solc@[0-9]+\.[0-9]+\.[0-9]+$")


def forcer_utf8() -> None:
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def maintenant_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def hex_propre(valeur: str) -> str:
    texte = re.sub(r"\s+", "", valeur or "").lower()
    if texte.startswith("0x"):
        texte = texte[2:]
    if not texte:
        raise ValueError("bytecode vide")
    if len(texte) % 2:
        raise ValueError("longueur hexadecimale impaire")
    if not re.fullmatch(r"[0-9a-f]+", texte):
        raise ValueError("caracteres non hexadecimaux")
    return texte


def lire_hex(chemin: Path) -> str:
    return hex_propre(chemin.read_text(encoding="utf-8", errors="replace"))


def rpc(url: str, methode: str, params: list[Any], timeout: int) -> Any:
    corps = json.dumps({"jsonrpc": "2.0", "id": 1, "method": methode, "params": params}).encode()
    requete = urllib.request.Request(
        url,
        data=corps,
        headers={"Content-Type": "application/json", "User-Agent": "dossier-paternite/2.0"},
        method="POST",
    )
    with urllib.request.urlopen(requete, timeout=timeout) as reponse:
        charge = json.loads(reponse.read().decode("utf-8"))
    if "error" in charge:
        raise RuntimeError(charge["error"])
    return charge["result"]


def base58(octets: bytes) -> str:
    n = int.from_bytes(octets, "big")
    sortie = ""
    while n:
        n, reste = divmod(n, 58)
        sortie = ALPHABET_B58[reste] + sortie
    for octet in octets:
        if octet != 0:
            break
        sortie = "1" + sortie
    return sortie


def extraire_auxdata(hex_code: str) -> dict[str, Any]:
    """Extraire l'empreinte IPFS et la version solc de l'auxdata CBOR."""
    texte = hex_code.lower()
    resultat: dict[str, Any] = {"ipfs_hex": None, "cid_v0": None, "compilateur": None}
    trouve = re.search(r"a2646970667358221220([0-9a-f]{64})", texte)
    if trouve:
        resultat["ipfs_hex"] = trouve.group(1)
        resultat["cid_v0"] = base58(b"\x12\x20" + bytes.fromhex(trouve.group(1)))
    version = re.search(r"64736f6c6343([0-9a-f]{6})", texte)
    if version:
        v = version.group(1)
        resultat["compilateur"] = f"{int(v[0:2], 16)}.{int(v[2:4], 16)}.{int(v[4:6], 16)}"
    return resultat


def comparer(a: str, b: str) -> dict[str, Any]:
    prefixe = 0
    while prefixe < min(len(a), len(b)) and a[prefixe] == b[prefixe]:
        prefixe += 1
    differences = [i for i in range(min(len(a), len(b))) if a[i] != b[i]]
    return {
        "longueur_a_octets": len(a) // 2,
        "longueur_b_octets": len(b) // 2,
        "prefixe_commun_octets": prefixe // 2,
        "pourcentage_prefixe": round(prefixe / max(1, min(len(a), len(b))) * 100, 2),
        "nb_caracteres_differents": len(differences) + abs(len(a) - len(b)),
        "premiere_difference": differences[0] if differences else None,
        "derniere_difference": differences[-1] if differences else None,
        "egal": a == b,
    }


def couper_auxdata(hex_code: str) -> tuple[str, str]:
    """Separer (code executable, suffixe auxdata) ; suffixe vide si le CBOR est absent.

    Solidity termine le runtime par une carte CBOR dont les deux derniers octets
    donnent sa longueur. Sans ce marqueur, tout le bloc est du code.
    """
    if len(hex_code) < 6:
        return hex_code, ""
    try:
        longueur = int(hex_code[-4:], 16)
    except ValueError:
        return hex_code, ""
    if longueur <= 0 or longueur + 2 > len(hex_code) // 2:
        return hex_code, ""
    debut = len(hex_code) - (longueur + 2) * 2
    if hex_code[debut:debut + 2] not in {"a1", "a2", "a3", "a4"}:
        return hex_code, ""
    return hex_code[:debut], hex_code[debut:]


def adresses_propres(adresses: list[str]) -> list[str]:
    sortie = []
    for adresse in adresses:
        propre = adresse.lower().strip()
        if propre.startswith("0x"):
            propre = propre[2:]
        if not re.fullmatch(r"[0-9a-f]{40}", propre):
            raise ValueError(f"adresse immuable invalide : {adresse}")
        sortie.append(propre)
    return sortie


def masquer(hex_code: str, adresses: list[str]) -> str:
    """Neutraliser les valeurs immuables injectees au deploiement."""
    sortie = hex_code
    for adresse in adresses:
        sortie = sortie.replace("0" * 24 + adresse, "0" * 64)
        sortie = sortie.replace(adresse, "0" * 40)
    return sortie


def compiler(source: Path, solc: str, runs: int, optimiseur: bool, contrat: str | None, timeout: int) -> dict[str, Any]:
    if not RE_SOLC.fullmatch(solc):
        return {"ok": False, "erreur": f"version solc non conforme : {solc} (attendu solc@x.y.z)"}
    contenu = source.read_text(encoding="utf-8")
    entree = {
        "language": "Solidity",
        "sources": {"Source.sol": {"content": contenu}},
        "settings": {
            "optimizer": {"enabled": optimiseur, "runs": runs},
            "outputSelection": {"*": {"*": ["evm.bytecode.object", "evm.deployedBytecode.object"]}},
        },
    }
    commande = f"npx --yes {solc} --standard-json"
    try:
        proc = subprocess.run(
            commande,
            input=json.dumps(entree),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "erreur": f"compilation interrompue apres {timeout} s"}
    brut = proc.stdout or ""
    if "{" not in brut:
        return {"ok": False, "erreur": (proc.stderr or brut)[:2000]}
    try:
        charge = json.loads(brut[brut.index("{"):])
    except json.JSONDecodeError as erreur:
        return {"ok": False, "erreur": f"JSON solc illisible : {erreur}"}
    if "contracts" not in charge:
        messages = [e.get("formattedMessage") or e.get("message") for e in charge.get("errors", [])]
        return {"ok": False, "erreur": " | ".join(m for m in messages if m)[:2000]}
    candidats: dict[str, dict[str, Any]] = {}
    for fichier, contrats in charge["contracts"].items():
        for nom, corps in contrats.items():
            evm = corps.get("evm", {})
            runtime = (evm.get("deployedBytecode") or {}).get("object") or ""
            if not runtime:
                continue
            if contrat and nom != contrat:
                continue
            candidats[f"{fichier}:{nom}"] = evm
    if not candidats:
        return {"ok": False, "erreur": f"aucun contrat avec bytecode deploye (filtre : {contrat or 'aucun'})"}
    if len(candidats) > 1:
        return {"ok": False, "erreur": "plusieurs contrats : preciser --contrat parmi " + ", ".join(sorted(k.split(":")[1] for k in candidats))}
    evm = next(iter(candidats.values()))
    return {
        "ok": True,
        "creation": str((evm.get("bytecode") or {}).get("object") or "").lower(),
        "runtime": str((evm.get("deployedBytecode") or {}).get("object") or "").lower(),
        "command": commande,
    }


def verdict_runtime(comparaison_brute: dict[str, Any], executable: dict[str, Any]) -> str:
    if comparaison_brute["egal"]:
        return "IDENTIQUE"
    if executable["egal"]:
        return "CORRESPONDANCE_FORTE"
    if executable["pourcentage_prefixe"] >= 90:
        return "CORRESPONDANCE_PARTIELLE"
    return "DIVERGENCE"


def ecrire_json(chemin: Path, donnees: Any) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with chemin.open("w", encoding="utf-8", newline="\n") as flux:
        json.dump(donnees, flux, indent=1, ensure_ascii=False)
        flux.write("\n")


def mode_fichiers(args: argparse.Namespace) -> int:
    if not args.actuel or not args.compile:
        print("ERREUR --mode fichiers exige --actuel et --compile")
        return 2
    try:
        actuel = lire_hex(Path(args.actuel))
        compile_hex = lire_hex(Path(args.compile))
        adresses = adresses_propres(args.immutable or [])
    except (OSError, ValueError) as erreur:
        print(f"ERREUR {erreur}")
        return 2
    brut = comparer(compile_hex, actuel)
    masque = comparer(masquer(compile_hex, adresses), masquer(actuel, adresses))
    code_compile, aux_compile = couper_auxdata(masquer(compile_hex, adresses))
    code_actuel, aux_actuel = couper_auxdata(masquer(actuel, adresses))
    executable = comparer(code_compile, code_actuel)
    verdict = verdict_runtime(brut, executable)
    resultat = {
        "genere_le": maintenant_utc(),
        "mode": "fichiers",
        "actuel": str(args.actuel),
        "compile": str(args.compile),
        "adresses_masquees": adresses,
        "auxdata_actuel": extraire_auxdata(actuel),
        "auxdata_compile": extraire_auxdata(compile_hex),
        "auxdata_octets": {"actuel": len(aux_actuel) // 2, "compile": len(aux_compile) // 2},
        "comparaison_brute": brut,
        "comparaison_masquee": masque,
        "comparaison_code_executable": executable,
        "verdict": verdict,
    }
    if args.out:
        ecrire_json(Path(args.out), resultat)
    print(f"MODE: fichiers")
    print(f"RUNTIME: actuel {brut['longueur_b_octets']} octets, compile {brut['longueur_a_octets']} octets")
    print(f"DIFFERENCES: brut {brut['nb_caracteres_differents']} car., masque {masque['nb_caracteres_differents']} car.")
    print(f"CODE EXECUTABLE: {executable['nb_caracteres_differents']} car. differents, prefixe {executable['pourcentage_prefixe']}%")
    print(f"VERDICT: {verdict}")
    return 0 if verdict in {"IDENTIQUE", "CORRESPONDANCE_FORTE"} else 1


def mode_onchain(args: argparse.Namespace) -> int:
    manquants = [nom for nom in ("source", "rpc", "address", "tx", "solc") if not getattr(args, nom)]
    if manquants:
        print("ERREUR --mode onchain exige " + ", ".join("--" + m for m in manquants))
        return 2
    try:
        adresses = adresses_propres(args.immutable or [])
    except ValueError as erreur:
        print(f"ERREUR {erreur}")
        return 2
    resultat: dict[str, Any] = {
        "genere_le": maintenant_utc(),
        "mode": "onchain",
        "rpc": args.rpc,
        "adresse": args.address,
        "transaction": args.tx,
    }
    try:
        recu = rpc(args.rpc, "eth_getTransactionReceipt", [args.tx], args.timeout)
        code = rpc(args.rpc, "eth_getCode", [args.address, "latest"], args.timeout)
        chaine = int(rpc(args.rpc, "eth_chainId", [], args.timeout), 16)
    except Exception as erreur:  # noqa: BLE001
        print(f"ERREUR reseau : {erreur}")
        return 2
    if not recu:
        print("ERREUR transaction introuvable sur ce RPC")
        return 2
    if recu.get("status") != "0x1":
        print(f"ERREUR transaction non reussie : statut {recu.get('status')}")
        return 2
    code_hex = (code or "").lower()
    if not code_hex.startswith("0x") or len(code_hex) <= 2:
        print("ERREUR code on-chain vide a cette adresse")
        return 2
    code_hex = code_hex[2:]

    horodatage = 0
    source_horodatage = "receipt"
    bloc_hash = None
    try:
        horodatage = int(recu.get("blockTimestamp") or "0x0", 16)
    except ValueError:
        horodatage = 0
    if not horodatage:
        try:
            bloc = rpc(args.rpc, "eth_getBlockByNumber", [recu.get("blockNumber"), False], args.timeout)
            horodatage = int((bloc or {}).get("timestamp") or "0x0", 16)
            bloc_hash = (bloc or {}).get("hash")
            source_horodatage = "bloc"
        except Exception:  # noqa: BLE001
            source_horodatage = "indisponible"

    compilation = compiler(
        Path(args.source), args.solc, args.optimizer_runs, not args.no_optimizer, args.contrat, args.timeout
    )
    resultat["reseau"] = {"chaine_id": chaine}
    resultat["transaction_recue"] = {
        "statut": recu.get("status"),
        "bloc": int(recu.get("blockNumber") or "0x0", 16),
        "horodatage_utc": datetime.fromtimestamp(horodatage, timezone.utc).replace(microsecond=0).isoformat()
        if horodatage
        else None,
        "source_horodatage": source_horodatage,
        "bloc_hash": bloc_hash,
        "de": recu.get("from"),
        "contrat": recu.get("contractAddress"),
    }
    if args.bloc is not None:
        resultat["bloc_attendu"] = args.bloc
        resultat["bloc_concorde"] = resultat["transaction_recue"]["bloc"] == args.bloc
        if not resultat["bloc_concorde"]:
            print("ERREUR bloc de deploiement different de --bloc")
            return 1
    resultat["code_onchain"] = {
        "longueur_octets": len(code_hex) // 2,
        "sha256": hashlib.sha256(bytes.fromhex(code_hex)).hexdigest(),
        "auxdata": extraire_auxdata(code_hex),
    }
    resultat["source"] = {
        "chemin": str(args.source),
        "sha256": hashlib.sha256(Path(args.source).read_bytes()).hexdigest(),
    }
    resultat["compilation"] = {"ok": compilation.get("ok", False), "solc": args.solc, "optimiseur": not args.no_optimizer, "runs": args.optimizer_runs}
    if not compilation.get("ok"):
        resultat["compilation"]["erreur"] = compilation.get("erreur")
        if args.out:
            ecrire_json(Path(args.out), resultat)
        print("ERREUR compilation : " + str(compilation.get("erreur"))[:500])
        return 3

    creation = compilation["creation"]
    runtime = compilation["runtime"]
    brut = comparer(runtime, code_hex)
    masque = comparer(masquer(runtime, adresses), masquer(code_hex, adresses))
    code_runtime, aux_runtime = couper_auxdata(masquer(runtime, adresses))
    code_onchain, aux_onchain = couper_auxdata(masquer(code_hex, adresses))
    executable = comparer(code_runtime, code_onchain)
    verdict = verdict_runtime(brut, executable)
    resultat["compilation"]["longueur_creation_octets"] = len(creation) // 2
    resultat["compilation"]["longueur_runtime_octets"] = len(runtime) // 2
    resultat["compilation"]["auxdata"] = extraire_auxdata(creation)
    resultat["adresses_masquees"] = adresses
    resultat["auxdata_octets"] = {"onchain": len(aux_onchain) // 2, "compile": len(aux_runtime) // 2}
    resultat["comparaison_brute"] = brut
    resultat["comparaison_masquee"] = masque
    resultat["comparaison_code_executable"] = executable
    resultat["verdict"] = verdict

    if args.artifact:
        try:
            artefact = json.loads(Path(args.artifact).read_text(encoding="utf-8"))
            creation_artefact = hex_propre(str(artefact.get(args.artifact_key, "")))
            cmp_art = comparer(creation, creation_artefact)
            aux_art = extraire_auxdata(creation_artefact)
            resultat["artefact"] = {
                "chemin": str(args.artifact),
                "cle": args.artifact_key,
                "sha256_fichier": hashlib.sha256(Path(args.artifact).read_bytes()).hexdigest(),
                "comparaison": cmp_art,
                "auxdata": aux_art,
                "digest_identique_onchain": bool(
                    aux_art.get("ipfs_hex") and aux_art.get("ipfs_hex") == resultat["code_onchain"]["auxdata"].get("ipfs_hex")
                ),
            }
        except (OSError, ValueError, json.JSONDecodeError) as erreur:
            resultat["artefact"] = {"erreur": str(erreur)}
            print(f"ERREUR artefact : {erreur}")
            return 2

    if args.out:
        ecrire_json(Path(args.out), resultat)
    print(f"MODE: onchain")
    print(f"RESEAU: chaine {chaine}")
    print(
        "TX: statut {} bloc {} horodatage {} (source {})".format(
            recu.get("status"),
            resultat["transaction_recue"]["bloc"],
            resultat["transaction_recue"]["horodatage_utc"],
            source_horodatage,
        )
    )
    print(f"RUNTIME: on-chain {resultat['code_onchain']['longueur_octets']} octets, compile {len(runtime) // 2} octets")
    print(f"AUXDATA on-chain: compilateur {resultat['code_onchain']['auxdata'].get('compilateur')}, ipfs {resultat['code_onchain']['auxdata'].get('ipfs_hex')}")
    print(f"MASQUAGE: {len(adresses)} adresse(s) immuable(s)")
    print(f"DIFFERENCES: brut {brut['nb_caracteres_differents']} car., masque {masque['nb_caracteres_differents']} car.")
    print(f"CODE EXECUTABLE: {executable['nb_caracteres_differents']} car. differents, prefixe {executable['pourcentage_prefixe']}%")
    if "artefact" in resultat and "comparaison" in resultat["artefact"]:
        cmp_art = resultat["artefact"]["comparaison"]
        print(
            "ARTEFACT: {} caracteres differents, digest on-chain identique: {}".format(
                cmp_art["nb_caracteres_differents"], resultat["artefact"]["digest_identique_onchain"]
            )
        )
    print(f"VERDICT: {verdict}")

    if verdict in {"IDENTIQUE", "CORRESPONDANCE_FORTE"}:
        if "artefact" in resultat and "comparaison" in resultat["artefact"]:
            cmp_art = resultat["artefact"]["comparaison"]
            coherent = cmp_art["egal"] or cmp_art["nb_caracteres_differents"] <= 64
            if not coherent:
                print("ATTENTION artefact incoherent avec la source recompilee")
                return 1
        return 0
    return 1


def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Comparer un bytecode deploye a une source recompilee (lecture seule)."
    )
    p.add_argument("--mode", choices=["onchain", "fichiers"], default="onchain")
    p.add_argument("--source", help="source Solidity")
    p.add_argument("--rpc", help="URL JSON-RPC")
    p.add_argument("--address", help="adresse du contrat")
    p.add_argument("--tx", help="transaction de deploiement")
    p.add_argument("--solc", help="version epinglee, forme solc@x.y.z")
    p.add_argument("--contrat", help="nom du contrat si plusieurs")
    p.add_argument("--artifact", help="artefact JSON (bytecode de creation)")
    p.add_argument("--artifact-key", default="bytecode", help="cle du bytecode dans l'artefact")
    p.add_argument("--immutable", action="append", default=[], help="adresse immuable a masquer (repetable)")
    p.add_argument("--bloc", type=int, help="bloc de deploiement attendu")
    p.add_argument("--optimizer-runs", type=int, default=200)
    p.add_argument("--no-optimizer", action="store_true")
    p.add_argument("--timeout", type=int, default=300)
    p.add_argument("--out", help="fichier JSON de sortie")
    p.add_argument("--actuel", help="mode fichiers : hex runtime deploye")
    p.add_argument("--compile", help="mode fichiers : hex runtime recompile")
    return p


def main(argv: list[str] | None = None) -> int:
    forcer_utf8()
    args = construire_parseur().parse_args(argv)
    if args.mode == "fichiers":
        return mode_fichiers(args)
    return mode_onchain(args)


if __name__ == "__main__":
    raise SystemExit(main())
