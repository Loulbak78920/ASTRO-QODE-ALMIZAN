# Preuves — session 026949af (28/10/2026)

Source : conversation `026949af-b05f-4dc2-8655-0b52096810f8` (« Erreur fichier ABI manquant »), lue via `read_chat_session` puis depuis le JSONL du projet. Messages de la session en UTC ; `mtime` disque en heure locale (+01:00).

## 1. Panne initiale (11:47 UTC)

```
File "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\valider_et_sceller_tout_one_click.py", line 121, in main
    with open(chemin_abi, "r", encoding="utf-8") as f:
FileNotFoundError: [Errno 2] No such file or directory:
'C:\\Users\\Administrateur\\Desktop\\Al-Mizan\\chaine\\contracts\\AmalMizanSynchronMznContract.json'
```

L'original était un littéral absolu : `chemin_abi = r"C:\Users\Administrateur\Desktop\Al-Mizan\chaine\contracts\AmalMizanSynchronMznContract.json"`.

## 2. Chemin mort confirmé, artefact réel localisé

```
ls: cannot access 'C:/Users/Administrateur/Desktop/Al-Mizan': No such file or directory
```

Recherche depuis `Desktop` (parent du projet) :

```
./GITHUB_DEPOT_PUBLIC_IMAM8MAHDI/contracts/AmalMizanSynchronMznContract.json
./GITHUB_DEPOT_PUBLIC_IMAM8MAHDI/contracts/build/AmalMizanSynchronMznContract.json
```

Les deux copies font 50918 octets (`ls -la`, 11:48). `find . -iname "AmalMizanSynchronMznContract*"` dans `IMAM8MAHDI` ne rend que des `.sol` : aucune copie de l'ABI dans l'arbre du projet.

## 3. Premier correctif faux, échec constaté par rejeu

Candidats placés sous la racine du projet uniquement :

```python
RACINE_PROJET = Path(__file__).resolve().parent.parent
CANDIDATS_ABI = (
    RACINE_PROJET / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI" / "contracts" / "AmalMizanSynchronMznContract.json",
    RACINE_PROJET / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI" / "contracts" / "build" / "AmalMizanSynchronMznContract.json",
)
```

Rejeu `py -3 valider_et_sceller_tout_one_click.py --simuler` :

```
FileNotFoundError: ABI AmalMizanSynchronMznContract introuvable. Chemins testés :
  C:\Users\Administrateur\Desktop\IMAM8MAHDI\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI\contracts\AmalMizanSynchronMznContract.json
  C:\Users\Administrateur\Desktop\IMAM8MAHDI\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI\contracts\build\AmalMizanSynchronMznContract.json
```

L'erreur listant les chemins a rendu l'échec immédiatement diagnosticable (l'artefact est chez le voisin, `RACINE_PROJET.parent`).

## 4. Correctif final (mesuré le 2026-10-28 à 12:02:25Z, rejoué à 12:06Z)

Le chargeur a ensuite été extrait dans `ASTRO-Q°ODE_SYSTEME/resolution_abi_mizan.py` (Write 11:54:40.885Z) ; le script principal importe `charger_abi` (ligne 31) et l'appelle ligne 122. Candidats effectifs :

```python
NOM_ARTEFACT = "AmalMizanSynchronMznContract.json"
RACINE_SYSTEME = Path(__file__).resolve().parent
RACINE_PROJET = RACINE_SYSTEME.parent

CANDIDATS = (
    RACINE_SYSTEME / "contracts" / NOM_ARTEFACT,
    RACINE_SYSTEME / "contracts" / "build" / NOM_ARTEFACT,
    RACINE_PROJET.parent / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI" / "contracts" / NOM_ARTEFACT,
    RACINE_PROJET.parent / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI" / "contracts" / "build" / NOM_ARTEFACT,
)
```

- `valider_et_sceller_tout_one_click.py` : 7804 octets, 180 lignes LF, SHA-256 `70a8c716ae5aa788ac0e64639fbda624e0d8bafe53bffed1b59a0712998cbdfe`, `mtime` 2026-10-28 12:54:44.575 +0100 = 11:54:44.575Z.
- `resolution_abi_mizan.py` : 1386 octets, SHA-256 `d44391572f387bbcef7824594b0dbdee22faf898965bd0eda9892b48f675dc5d`, `mtime` 12:54:40.889 +0100 = 11:54:40.889Z.
- Attribution : Edits du script principal enregistrés à 11:54:44.526Z (écart 49 ms) ; Write du helper à 11:54:40.885Z (écart 4 ms).
- État antérieur : 8561 octets / `2a9e3fcc4b7b77478f346918de48abb7b34835f873b3ffc59fa09414103d37af` / `mtime` 12:49:25.114 +0100, attribué à l'Edit de 11:49:25.163Z (écart 49 ms) ; il portait le chargeur inline, remplacé le 2026-10-28 à 11:54:44Z.

## 5. Rejeu dry-run et conformité de l'artefact

```
[SIMULATION RÉUSSIE] Tout est calibré et prêt à être scellé dans le contrat actif.
Pour exécuter réellement : py valider_et_sceller_tout_one_click.py
```

Contrôle sélecteur (11:49 UTC) :

```
selector scellerActe(address,string,bytes32,string) 0xea76d981
code len 18688
PRESENT
chain 8453 bloc 53199416
```

`--simuler` sort avant la demande de clé privée (`valider_et_sceller_tout_one_click.py`, lignes 126-129) ; sans ce drapeau, le script signe et envoie une transaction réelle sur Base Mainnet.

## 6. Scripts qui portaient le littéral mort (inventaire du 2026-10-28 11:54:39Z, réparés de 11:54:55Z à 11:55:14Z)

| Fichier | Ligne |
|---|---|
| `passerelle_ancrage_blockchain.py` | 51 (`ABI_CONTRAT_PATH`) |
| `sceller_acte_a090_anti_piege.py` | 92 |
| `sceller_acte_a093_bassin_accueil_universel.py` | 77 |
| `sceller_acte_a094_unification_l1_l2_l3_l4.py` | 77 |
| `sceller_completude_100_pourcent_monade_a092.py` | 92 |
| `sceller_suite_complete_a090_a091_a092.py` | 112 |
| `sceller_tout_en_un_coup_maitre.py` | 112 |

Commande d'inventaire : `grep -rnF 'Desktop\Al-Mizan' --include=*.py .` dans `ASTRO-Q°ODE_SYSTEME`.

L'utilisateur a demandé « Corrige d'abord tous les chemins ABI codés en dur » à 11:53 UTC. Les sept scripts ont été réparés entre 11:54:55Z et 11:55:14Z et importent chacun `resolution_abi_mizan` (un import par fichier, vérifié). Contrôle du 2026-10-28 à 12:02:25Z, rejoué à 12:06Z : `grep -rlnF --include=*.py 'Desktop\Al-Mizan' .` rend 0 fichier ; le contrôle positif `resolution_abi_mizan` en rend 8 (les sept scripts et le script principal).

## 7. Limites de ces preuves

- La session 026949af a continué après la lecture initiale : Write/Edit jusqu'à 11:59:04.483Z, puis un tour « Commit ces changements » à 12:00:07.880Z. Au 2026-10-28T12:06Z elle est `ready` (`activeTurnId: null`, `revision: 55`). Ses constats restent `PROVISIONAL`.
- Les empreintes ci-dessus valent pour le 28/10/2026 ; tout fichier modifié depuis invalide les numéros de ligne.
