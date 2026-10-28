# Preuves — session 026949af (28/10/2026)

Source : conversation `026949af-b05f-4dc2-8655-0b52096810f8` (« Erreur fichier ABI manquant »), lue via `read_chat_session` (`turnLimit=6`, `hasMoreBefore=false`, 8 messages, 4 tours utilisateur). Messages en UTC ; vérifications disque en heure locale (+01:00).

## 1. Panne initiale (11:47:51 UTC)

```
File "...\ASTRO-Q°ODE_SYSTEME\valider_et_sceller_tout_one_click.py", line 121, in main
    with open(chemin_abi, "r", encoding="utf-8") as f:
FileNotFoundError: [Errno 2] No such file or directory:
'C:\\Users\\Administrateur\\Desktop\\Al-Mizan\\chaine\\contracts\\AmalMizanSynchronMznContract.json'
```

Littéral d'origine : `chemin_abi = r"C:\Users\Administrateur\Desktop\Al-Mizan\chaine\contracts\AmalMizanSynchronMznContract.json"`. Le dossier `Desktop\Al-Mizan` n'existait plus.

## 2. Premier correctif faux, échec par rejeu

Candidats placés sous la racine du projet uniquement :

```python
RACINE_PROJET = Path(__file__).resolve().parent.parent
CANDIDATS_ABI = (
    RACINE_PROJET / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI" / "contracts" / "AmalMizanSynchronMznContract.json",
    RACINE_PROJET / "GITHUB_DEPOT_PUBLIC_IMAM8MAHDI" / "contracts" / "build" / "AmalMizanSynchronMznContract.json",
)
```

Rejeu `--simuler` :

```
FileNotFoundError: ABI AmalMizanSynchronMznContract introuvable. Chemins testés :
  C:\Users\Administrateur\Desktop\IMAM8MAHDI\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI\contracts\AmalMizanSynchronMznContract.json
  C:\Users\Administrateur\Desktop\IMAM8MAHDI\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI\contracts\build\AmalMizanSynchronMznContract.json
```

L'artefact vit chez le voisin, `RACINE_PROJET.parent`, pas sous la racine du projet.

## 3. Correction de périmètre (11:53:21 UTC)

Message utilisateur : « Corrige d'abord tous les chemins ABI codés en dur ».

Réponse : création de `resolution_abi_mizan.py` et rebranchement des 8 fichiers suivants sur `charger_abi` :

| Fichier | Import | Appel |
|---|---|---|
| `valider_et_sceller_tout_one_click.py` | 31 | 122 |
| `sceller_tout_en_un_coup_maitre.py` | 36 | 114 |
| `sceller_suite_complete_a090_a091_a092.py` | 32 | 114 |
| `sceller_completude_100_pourcent_monade_a092.py` | 32 | 94 |
| `sceller_acte_a094_unification_l1_l2_l3_l4.py` | 28 | 79 |
| `sceller_acte_a093_bassin_accueil_universel.py` | 28 | 79 |
| `sceller_acte_a090_anti_piege.py` | 29 | 95 |
| `passerelle_ancrage_blockchain.py` | 34 | 127 |

Cas particulier conservé : `sceller_acte_a090_anti_piege.py` basculait sur une ABI minimale via `os.path.exists` ; le repli est déclenché par `FileNotFoundError`.

## 4. État disque au 28/10/2026 13:04 +01:00 (revérifié pour ce Skill)

- `ASTRO-Q°ODE_SYSTEME/resolution_abi_mizan.py` : 1386 octets, 4 candidats (local `contracts/`, local `contracts/build/`, voisin `contracts/`, voisin `contracts/build/`), `chemin_abi()` et `charger_abi()`.
- `grep -rln "resolution_abi_mizan" --include=*.py` : 8 fichiers.
- `grep -rnF 'Desktop\Al-Mizan\chaine\contracts' --include=*.py` : 0 occurrence.
- `deploiement_vps/deploy_evm_reseau.py` : 6 candidats (lignes 132-146), aucun import du module partagé.
- `ASTRO-Q°ODE_SYSTEME/memoire_aq` : 192 fichiers.

## 5. Vérifications annoncées au tour de 11:53 (texte de réponse, sortie brute partiellement couverte)

- `py_compile` OK sur 9 fichiers (module + 8 consommateurs).
- Six scripts `sceller_*` en `--simuler` : rc=0, `nextActeId` = #12, aucun accès à la clé privée.
- ABI résolue : 70 entrées, sélecteur `0xea76d981` pour `scellerActe(address,string,bytes32,string)` présent sur Base (chain 8453, bloc 53199416).
- `memoire_aq` inchangé : 192 fichiers, même empreinte.

Niveau de preuve : les compteurs disque du §4 sont rejoués ; les rc de simulation et le sélecteur sont des affirmations de session, non rejouées ici. Le bloc 53199416 est daté et a avancé lors d'un rejeu ultérieur (voir `verifier-abi-locale-contrat-deploye`).

## 6. Outil de déploiement autonome (11:58:36 UTC)

Message utilisateur : « Corrige deploy_evm_reseau.py pour trouver l'artefact en local ».

Décision : ne pas importer le module partagé, car le script est copié seul sur le VPS. Candidats dans l'ordre : `<script>/contracts/`, `<script>/contracts/build/`, `ASTRO-Q°ODE_SYSTEME/contracts/`, `.../build/`, voisin `contracts/`, voisin `contracts/build/`.

- `py_compile` OK ; résolution locale : 70 entrées ABI, bytecode 22 580 caractères, préfixe `0x` ajouté en aval (ligne 250).
- Fixture positive (copie hors projet, `contracts/` local) : `abi entries: 70 bytecode len: 22580`, `rc=0` — priorité locale préservée.
- Fixture négative : `[ERREUR] Artefact compilé AmalMizanSynchronMznContract.json introuvable. Chemins testés :` suivi des six chemins, `rc=1`.
- Premier essai de fixture : `ModuleNotFoundError: No module named 'deploy_evm_reseau'` avant toute assertion ; reprise en important le fichier par son chemin absolu. Les deux fixtures ont été supprimées (`ls -d ../.qoder/tmp/abi_fixture_*` : aucune).

## 7. Commit non abouti (12:00:07 UTC)

Message utilisateur : « Commit ces changements ».

- `IMAM8MAHDI` n'est pas un dépôt Git : `fatal: not a git repository (or any of the parent directories): .git`.
- Seul `ASTRO-QODE-IMAM8MAHDI/.git` existe ; `GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` est sur `main` (`479f62e`, `[origin/main]`), `git status` vide.
- Le dernier outil du tour était encore `running` à la lecture ; aucun résultat de commit n'est affirmé.

## 8. Limites

- La session était `runtimeState=running` (`activeTurnId=dd3fd973…`, `revision=13`) à la lecture : les tours postérieurs au commit ne sont pas couverts.
- Les numéros de ligne du §3 proviennent de la réponse de session et peuvent avoir dérivé depuis.
- Aucune correction de masse des mentions `Desktop\Al-Mizan` dans les docstrings, guides `.md` ou `.bat` n'est incluse ni affirmée.
