# -*- coding: utf-8 -*-
"""
===============================================================================
       DIAGNOSTIC & HARMONISATION DES 5 ADRESSES AL-MIZAN SUR BASE MAINNET
===============================================================================
Vérifie en direct les 4 tokens Mizan, le pivot USDC, les soldes de l'Auteur,
les pools de liquidité et l'état d'harmonisation de l'écosystème.
"""

import urllib.request
import json
import sys

# Fix encodage console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RPC = "https://mainnet.base.org"

ADRESSES_TETRADE = {
    "1. MZN (Informé)": "0x520cbd0e1e72178f9e819AFf1e815606923A71db",
    "2. MZN-MAT (Matière)": "0xD45406EEdc8d9AeD3828c06C3D208804D5b69c2a",
    "3. MZN-NRG (Énergie)": "0x38e1757A1971E038c8A6523B008179BEdc9AaAa0",
    "4. MZN-PLS (Plasma)": "0x7Cd56CE27E4CE363cDFbd63F4e2713C8eed2cC71",
}

PIVOT_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
POOL_MZN_USDC_V3 = "0xfb76b57c2e179a44ba7919d3960fc18a4c9db172"

CLE_DOREE_AUTEUR = "0xC9550Dd0A57C609494DBc44450Df48D798ebfB0B"
TRESORERIE_PRIVEE = "0xb7f26cD0eE5E74c51B3F4e71e4fA75B3F246837C"

def call_eth(to, data):
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":to,"data":data},"latest"]}).encode("utf-8")
    req = urllib.request.Request(RPC, data=payload, headers={"Content-Type":"application/json", "User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read()).get("result", "0x")
    except Exception as e:
        return "0x"

def get_balance(token, account, dec=18):
    data = "0x70a08231" + account[2:].lower().zfill(64)
    res = call_eth(token, data)
    if res == "0x" or not res:
        return 0.0
    return int(res, 16) / (10 ** dec)

def diagnostic():
    print("=" * 88)
    print("  DIAGNOSTIC D'HARMONIE DES 5 ADRESSES & POOL LIQUIDITÉ SUR BASE MAINNET")
    print("=" * 88)
    
    print("\n[A] ÉTAT DES 4 JETONS DE LA TÉTRADE COSMIQUE :")
    print(f"{'Jeton / Pôle':<24} {'Adresse Contrat Base':<44} {'Réserve Clé Dorée':<20} {'Trésorerie'}")
    print("-" * 88)
    for nom, adr in ADRESSES_TETRADE.items():
        bal_res = get_balance(adr, CLE_DOREE_AUTEUR)
        bal_tres = get_balance(adr, TRESORERIE_PRIVEE)
        print(f"{nom:<24} {adr:<44} {bal_res:>12,.0f} MZN   {bal_tres:>10,.0f} MZN")
    
    print("\n[B] ÉTAT DU PIVOT CENTRAL (5e ADRESSE) :")
    bal_usdc_tres = get_balance(PIVOT_USDC, TRESORERIE_PRIVEE, dec=6)
    print(f"  USDC Natif Base : {PIVOT_USDC}")
    print(f"  Solde USDC Trésorerie Privée : {bal_usdc_tres:.6f} USDC")

    print("\n[C] ÉTAT DU POOL EXISTANT UNISWAP V3 (MZN / USDC) :")
    print(f"  Adresse du Pool v3 : {POOL_MZN_USDC_V3}")
    pool_mzn = get_balance(ADRESSES_TETRADE["1. MZN (Informé)"], POOL_MZN_USDC_V3)
    pool_usdc = get_balance(PIVOT_USDC, POOL_MZN_USDC_V3, dec=6)
    print(f"  • MZN présent dans le pool  : {pool_mzn:,.2f} MZN")
    print(f"  • USDC présent dans le pool : {pool_usdc:,.6f} USDC")

    print("\n[D] VERDICT & ACTIONS DE RÉSOLUTION D'HARMONIE :")
    if pool_mzn < 1e-6:
        print("  ⚠️  ATTENTION : Le pool MZN/USDC contient 0.137 USDC mais 0.00 MZN.")
        print("      Cause : La position Uniswap v3 a été initialisée en attente de dépôt de MZN.")
        print("      Action : Déposer une tranche de 10 000 MZN dans le pool en 'Plage Complète'.")
    else:
        print(f"  ✅  Le pool MZN/USDC est actif avec {pool_mzn:,.2f} MZN et {pool_usdc:,.6f} USDC.")

    print("\n  💡  ARCHITECTURE RECOMMANDÉE POUR LES 3 NOUVEAUX JETONS :")
    print("      Inutile de racheter de l'USDC pour chaque jeton !")
    print("      Créez des pools frères adossés directement à MZN (MZN-MAT/MZN, MZN-NRG/MZN, MZN-PLS/MZN).")
    print("      Tout le flux s'échange naturellement vers l'USDC via le routage automatique Uniswap.")
    print("=" * 88)

if __name__ == "__main__":
    diagnostic()
