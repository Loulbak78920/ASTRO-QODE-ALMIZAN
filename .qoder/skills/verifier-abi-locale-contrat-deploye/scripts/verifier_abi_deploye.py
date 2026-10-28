#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prouve en lecture seule qu'un artefact ABI local correspond au contrat deploye.

Controles, dans l'ordre :
  1. artefact lisible, JSON valide, cle "abi" de type tableau ;
  2. signature analysee, types elementaires uniquement ;
  3. signature presente dans l'ABI avec des types d'entree identiques ;
  4. selecteur = 4 premiers octets du keccak-256 de la signature canonique ;
  5. eth_getCode renvoie un bytecode d'execution non vide ;
  6. chaine attendue respectee (--expect-chain) ;
  7. selecteur present dans le bytecode d'execution ;
  8. nombre d'entrees ABI egal a --expect-entries si fourni.

Aucune cle privee, aucune signature, aucune transaction : seuls eth_getCode,
eth_chainId et eth_blockNumber sont appeles.

Codes de sortie : 0 = PASS, 1 = controle echoue, 2 = usage, lecture ou RPC impossible.
La sortie est volontairement ASCII pour rester lisible sur une console Windows.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ADRESSE = re.compile(r"^0x[0-9a-fA-F]{40}$")
SIGNATURE = re.compile(r"^([A-Za-z_$][A-Za-z0-9_$]*)\((.*)\)$")
RPC_DEFAUT = "https://mainnet.base.org"
TYPE_TUPLE = re.compile(r"[()\[\]]")


def ascii_sur(message: str) -> str:
    return message.encode("ascii", "backslashreplace").decode("ascii")


class Rapport:
    def __init__(self) -> None:
        self.echecs = 0

    def ok(self, message: str) -> None:
        print("OK   " + ascii_sur(message))

    def echec(self, message: str) -> None:
        print("FAIL " + ascii_sur(message))
        self.echecs += 1


def construire_parseur() -> argparse.ArgumentParser:
    parseur = argparse.ArgumentParser(
        description="Prouve en lecture seule qu'une ABI locale correspond au contrat deploye.",
    )
    parseur.add_argument("--artifact", required=True, help="artefact JSON contenant la cle abi")
    parseur.add_argument("--address", required=True, help="adresse du contrat deploye (0x + 40 hex)")
    parseur.add_argument(
        "--signature",
        required=True,
        help='signature de la fonction cible, ex. "scellerActe(address,string,bytes32,string)"',
    )
    parseur.add_argument("--rpc", default=RPC_DEFAUT, help="URL JSON-RPC (defaut : %s)" % RPC_DEFAUT)
    parseur.add_argument(
        "--expect-chain",
        type=int,
        default=None,
        help="chain id attendu ; absent, la chaine observee est seulement consignee",
    )
    parseur.add_argument(
        "--expect-entries",
        type=int,
        default=None,
        help="nombre d'entrees ABI attendu, pour prouver que le fichier lu est complet",
    )
    parseur.add_argument("--timeout", type=int, default=20, help="delai RPC en secondes")
    return parseur


def keccak_256(donnees: bytes) -> bytes:
    try:
        from eth_utils import keccak
    except ImportError:
        try:
            from Crypto.Hash import keccak as keccak_crypto

            h = keccak_crypto.new(digest_bits=256)
            h.update(donnees)
            return h.digest()
        except ImportError:
            raise RuntimeError(
                "keccak-256 indisponible : installer eth-utils ou pycryptodome"
            )
    return keccak(donnees)


def decouper_types(interieur: str) -> list[str]:
    if not interieur.strip():
        return []
    types: list[str] = []
    profondeur = 0
    courant: list[str] = []
    for caractere in interieur:
        if caractere == "(":
            profondeur += 1
        elif caractere == ")":
            profondeur -= 1
            if profondeur < 0:
                raise ValueError("parentheses desequilibrees dans la signature")
        if caractere == "," and profondeur == 0:
            types.append("".join(courant).strip())
            courant = []
        else:
            courant.append(caractere)
    types.append("".join(courant).strip())
    if any(not t for t in types):
        raise ValueError("type vide dans la signature")
    return types


def appeler_rpc(url: str, methode: str, params: list, timeout: int) -> str:
    charge = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": methode, "params": params}
    ).encode("utf-8")
    requete = urllib.request.Request(
        url,
        data=charge,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(requete, timeout=timeout) as reponse:
            contenu = json.loads(reponse.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as erreur:
        raise RuntimeError("RPC %s injoignable : %s" % (methode, erreur))
    if "error" in contenu:
        raise RuntimeError("RPC %s en erreur : %s" % (methode, contenu["error"]))
    resultat = contenu.get("result")
    if not isinstance(resultat, str):
        raise RuntimeError("RPC %s : resultat absent ou non textuel" % methode)
    return resultat


def main(argv: list[str] | None = None) -> int:
    args = construire_parseur().parse_args(argv)

    if args.timeout <= 0:
        print("ERROR --timeout doit etre un entier positif")
        return 2
    if not ADRESSE.match(args.address):
        print("ERROR --address invalide : 0x suivi de 40 hexadecimaux attendu")
        return 2

    correspondance = SIGNATURE.match(args.signature.strip())
    if not correspondance:
        print("ERROR --signature invalide : forme nom(type1,type2) attendue")
        return 2
    nom = correspondance.group(1)
    try:
        types = decouper_types(correspondance.group(2))
    except ValueError as erreur:
        print("ERROR " + ascii_sur(str(erreur)))
        return 2
    if any(TYPE_TUPLE.search(t) for t in types):
        print("ERROR types tuple ou tableau non pris en charge : comparer components manuellement")
        return 2
    canonique = "%s(%s)" % (nom, ",".join(types))

    chemin = Path(args.artifact)
    try:
        artefact = json.loads(chemin.read_text(encoding="utf-8"))
    except OSError as erreur:
        print("ERROR lecture artefact impossible : %s" % ascii_sur(str(erreur)))
        return 2
    except json.JSONDecodeError as erreur:
        print("ERROR artefact JSON invalide : %s" % ascii_sur(str(erreur)))
        return 2
    if not isinstance(artefact, dict):
        print("ERROR artefact JSON : objet attendu")
        return 2

    rapport = Rapport()
    print("ABI=" + ascii_sur(str(chemin.resolve())))

    abi = artefact.get("abi")
    if not isinstance(abi, list):
        rapport.echec('cle "abi" absente ou non tableau')
        print("ABI_VALID=NO")
        print("RESULT FAIL (%d)" % rapport.echecs)
        return 1
    print("ABI_ENTRIES=%d" % len(abi))
    print("ABI_VALID=YES")

    fonctions = [
        e
        for e in abi
        if isinstance(e, dict)
        and e.get("type") == "function"
        and e.get("name") == nom
    ]
    correspondantes = [
        e
        for e in fonctions
        if [i.get("type") for i in e.get("inputs", []) if isinstance(i, dict)] == types
    ]
    print("FUNCTION=" + canonique)
    if correspondantes:
        print("IN_ABI=YES")
    else:
        print("IN_ABI=NO")
        if fonctions:
            rapport.echec(
                "signature absente de l'ABI ; surcharges presentes : %s"
                % ", ".join(
                    "%s(%s)"
                    % (
                        nom,
                        ",".join(str(i.get("type")) for i in e.get("inputs", [])),
                    )
                    for e in fonctions
                )
            )
        else:
            rapport.echec("aucune fonction nommee %s dans l'ABI" % nom)

    try:
        selecteur = "0x" + keccak_256(canonique.encode("utf-8"))[:4].hex()
    except RuntimeError as erreur:
        print("ERROR " + ascii_sur(str(erreur)))
        return 2
    print("SELECTOR=" + selecteur)

    try:
        code = appeler_rpc(args.rpc, "eth_getCode", [args.address, "latest"], args.timeout)
        chaine = int(appeler_rpc(args.rpc, "eth_chainId", [], args.timeout), 16)
        bloc = int(appeler_rpc(args.rpc, "eth_blockNumber", [], args.timeout), 16)
    except (RuntimeError, ValueError) as erreur:
        print("ERROR " + ascii_sur(str(erreur)))
        return 2

    print("CHAIN=%d" % chaine)
    print("BLOCK=%d" % bloc)

    if args.expect_chain is not None and chaine != args.expect_chain:
        rapport.echec("chaine %d, attendue %d" % (chaine, args.expect_chain))
    elif args.expect_chain is not None:
        rapport.ok("chaine attendue respectee (%d)" % chaine)
    else:
        print("WARN --expect-chain absent : chaine seulement consignee")

    if args.expect_entries is not None and len(abi) != args.expect_entries:
        rapport.echec("entrees ABI %d, attendues %d" % (len(abi), args.expect_entries))
    elif args.expect_entries is not None:
        rapport.ok("entrees ABI attendues respectees (%d)" % len(abi))

    if not code.startswith("0x"):
        rapport.echec("eth_getCode ne renvoie pas un hexadecimal 0x")
        octets = 0
    else:
        octets = (len(code) - 2) // 2
    print("CODE_BYTES=%d" % octets)

    if octets == 0:
        rapport.echec("aucun bytecode a cette adresse (compte ou contrat non deploye)")
        print("SELECTOR_IN_BYTECODE=ABSENT")
    elif selecteur[2:].lower() in code[2:].lower():
        print("SELECTOR_IN_BYTECODE=PRESENT")
        rapport.ok("selecteur %s present dans le bytecode deploye" % selecteur)
    else:
        print("SELECTOR_IN_BYTECODE=ABSENT")
        rapport.echec("selecteur %s absent du bytecode deploye" % selecteur)

    if rapport.echecs:
        print("RESULT FAIL (%d)" % rapport.echecs)
        return 1

    print("RESULT PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
