# Protocole de sauvegarde, quarantaine et restauration

Ce document détaille l'étape 5 du Skill. Il s'applique à tout état modifié par une vérification prétendue « lecture seule » : index de sceaux, journal d'audit plafonné, traces, fichiers générés.

## 1. Règles de sûreté

1. **Prendre l'instantané avant toute exécution.** Sans état de référence, une éviction ou une perte est inconnue, même si la longueur d'une liste est plausible.
2. **Sauvegarder avant de restaurer.** La sauvegarde contient les fichiers et un manifeste avec taille, `mtime_ns` et SHA-256. Un fichier sauvegardé après l'incident ne contient pas les entrées déjà évincées.
3. **Déplacer, ne pas supprimer.** Les fichiers ajoutés vont en quarantaine. Les clés ou entrées ajoutées sont retirées du fichier actif ; une copie reste disponible.
4. **Restaurer des valeurs connues, pas des compteurs recalculés.** `nb_sceaux`, `derniere_mise_a_jour` et `total_fichiers_harmonises` proviennent de l'état de référence. On vérifie ensuite leur cohérence avec le contenu ; on ne les déduit pas silencieusement de `len(...)`.
5. **Ne jamais reconstruire une entrée perdue par imitation.** Si une signature ancienne a disparu et qu'aucune sauvegarde ne la contient, écrire « perte avérée » ou « perte inconnue » ; ne pas inventer une entrée plausible.
6. **Stabiliser les écrivains.** Une restauration peut être réécrite en quelques secondes par un audit de masse, une tâche planifiée ou un autre agent. Sans arrêt des écrivains, la restauration est provisoire.

## 2. Étape A — figer l'état avant l'exécution

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\instantane_effets_de_bord.py" instantane \
  --cible "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\memoire_aq" \
  --recursif --stabilite 0.5 \
  --sortie "C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas\instantane_avant.json" \
  --sauvegarder "C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas\avant"
```

Contrôles :

- Code 0 et `RESULT: OK`.
- `manifest_avant.json` contient chaque fichier avec son SHA-256.
- Les empreintes du manifeste correspondent à celles de l'instantané. Le script le vérifie et marque l'instantané instable en cas d'écart.
- Le répertoire de sauvegarde ne doit pas être à l'intérieur de la cible : le script refuse ce cas.

Si l'instantané est marqué instable, il ne sert pas de référence : un écrivain est actif. Identifier le processus ou la tâche, puis recommencer après l'avoir arrêté avec l'accord de l'utilisateur.

## 3. Étape B — classer les artefacts

| Type d'artefact | Exemple | Restauration |
|---|---|---|
| Fichier immuable ajouté | `memoire_aq\<empreinte>.json` | Déplacer vers la quarantaine ; vérifier qu'aucune clé d'index ne le référence. |
| Dictionnaire de registre | `index_sceaux_astro_qode.json`, clé `sceaux` | Retirer uniquement les clés ajoutées ; restaurer les scalaires depuis l'état connu ; vérifier les références. |
| Liste plafonnée | `almizan_journal_agent_de_code.json`, clé `journal` | Retirer uniquement les entrées ajoutées par signature ; jamais `[-N:]` ; restaurer `total_fichiers_harmonises` depuis l'état connu. |
| Trace persistée | `memoire_aq\entite_conscience_logarithmique\trace_*.json` | Déplacer vers la quarantaine si la trace n'existait pas avant. |
| Livrable généré | CSV et HTML du tableau maître | Régénérer depuis la source avec le générateur officiel, puis valider. Ne pas éditer à la main. |
| Champ scalaire | `derniere_mise_a_jour`, `nb_sceaux`, `total_fichiers_harmonises` | Restaurer la valeur de l'état connu ; vérifier ensuite la cohérence, sans recalcul silencieux. |

Un champ `audit_actif=false` ou `persister=false` ne prouve pas l'absence d'écriture : il décrit un chemin interne. Le système de fichiers fait foi.

## 4. Étape C — mettre en quarantaine

Créer un répertoire hors de la cible, par exemple `C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas\quarantaine`, puis déplacer les fichiers ajoutés. Conserver leur chemin d'origine dans un manifeste.

```python
from pathlib import Path
import hashlib
import json
import shutil


def empreinte(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def mettre_en_quarantaine(fichiers: list[Path], quarantaine: Path) -> dict:
    quarantaine.mkdir(parents=True, exist_ok=True)
    deplaces = []
    for source in fichiers:
        if not source.is_file():
            continue
        destination = quarantaine / source.name
        if destination.exists():
            raise FileExistsError(destination)
        shutil.move(str(source), str(destination))
        deplaces.append(
            {
                "origine": str(source),
                "quarantaine": str(destination),
                "sha256": empreinte(destination),
            }
        )
    manifeste = {"fichiers": deplaces}
    (quarantaine / "manifeste_quarantaine.json").write_text(
        json.dumps(manifeste, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifeste
```

Ne pas utiliser `unlink()` ni `rmtree()` pour « nettoyer ». Un fichier en quarantaine reste la seule copie d'un sceau peut-être référencé ailleurs.

## 5. Étape D — restaurer un dictionnaire de registre

Le fichier de référence est `index_sceaux_astro_qode.json`. Les clés de `sceaux` sont des empreintes ; les scalaires `nb_sceaux` et `derniere_mise_a_jour` ont une valeur connue.

Schéma de premier niveau observé le 2026-10-26 : `sceaux` (dictionnaire), `derniere_mise_a_jour` (chaîne ISO), `nb_sceaux` (entier), `qubit_physique_local`, `completude_pourcent`. Relire le fichier réel avant de conclure : ces clés peuvent évoluer.

```python
from pathlib import Path
import json
import os


def ecrire_json_atomique(chemin: Path, donnees: dict) -> None:
    temporaire = chemin.with_name(chemin.name + f".tmp-{os.getpid()}")
    temporaire.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporaire, chemin)


def restaurer_registre(
    chemin: Path,
    cles_ajoutees: list[str],
    nb_sceaux_connu: int,
    derniere_mise_a_jour_connue: str,
) -> dict:
    donnees = json.loads(chemin.read_text(encoding="utf-8-sig"))
    sceaux = donnees.get("sceaux")
    if not isinstance(sceaux, dict):
        raise ValueError("clé 'sceaux' absente ou invalide")
    for cle in cles_ajoutees:
        sceaux.pop(cle, None)
    donnees["nb_sceaux"] = nb_sceaux_connu
    donnees["derniere_mise_a_jour"] = derniere_mise_a_jour_connue
    if len(sceaux) != nb_sceaux_connu:
        raise ValueError(
            f"incohérence: {len(sceaux)} clés pour nb_sceaux={nb_sceaux_connu}"
        )
    ecrire_json_atomique(chemin, donnees)
    return donnees
```

Points importants :

- `cles_ajoutees` vient de la comparaison d'instantanés, pas d'une supposition.
- On ne réécrit pas les clés existantes ; on ne « normalise » pas tout le dictionnaire.
- Si `len(sceaux)` ne correspond pas à l'état connu, s'arrêter : une clé légitime a peut-être été retirée, ou une clé ajoutée manque à la liste.
- Le formatage peut changer le SHA-256 du fichier. La preuve porte alors sur le contenu sémantique et les invariants, pas sur l'égalité d'octets. Si une copie de sauvegarde antérieure existe, la recopier est préférable pour retrouver les octets exacts.

## 6. Étape D bis — restaurer une liste plafonnée

Le journal `almizan_journal_agent_de_code.json` est une liste sous la clé `journal`. Un plafond `[-100:]` peut laisser la longueur à 100 tout en ayant évincé des entrées. La restauration doit retirer les entrées ajoutées par **signature** (horodatage + fichier), avec un compteur pour les doublons. La même méthode vaut pour `blocs` du ledger, dont la signature est l'horodatage seul (6.1).

### 6.1 Pré-contrôle du schéma réel

Ne jamais supposer les noms de clés. Le 2026-10-26, les 100/100 entrées du journal réel utilisaient le schéma suivant, défini par `DiagnosticCodeHarmonique` dans `ASTRO-Q°ODE_SYSTEME\agent_de_code_harmonisateur_mizan.py` (lignes 48–61) :

| Niveau | Clés et types observés |
|---|---|
| Racine | `agent` (str), `date_creation_iso` (str), `total_fichiers_harmonises` (int), `journal` (list) |
| Entrée `journal[]` | `chemin_fichier` (str), `lignes_totales` (int), `arbre_ast_valide` (bool), `respect_bride_mizan` (bool), `respect_anti_riba` (bool), `respect_killswitch_cryo` (bool), `detecte_fragmentation` (bool), `score_harmonie_100` (float), `empreinte_sha256` (str), `recommandations_harmonisation` (list), `horodatage_iso` (str) |
| Index | `sceaux` (dict), `derniere_mise_a_jour` (str), `nb_sceaux` (int), `qubit_physique_local`, `completude_pourcent` |
| Racine du ledger | `nom`, `auteur`, `doi`, `version`, `blocs` (list), `nb_blocs` (int cumulatif), `nb_sceaux_enregistres`, `nb_transactions_totales`, `dernier_bloc_hash`, `balances_actuelles`, `supply_totale_mzn`, `garde_fous`, `derniere_mise_a_jour` |
| Entrée `blocs[]` | `height` (int), `timestamp_utc` (str), `kernel_dt`, `prev_hash` (str), `bloc_hash` (str), `latence_sync_ref_ms`, `transactions` (list), `sceaux` (list), `invariants` (dict) |

La racine est écrite aux lignes 103–111 du même fichier ; l'ajout et le plafond `data["journal"][-100:]` aux lignes 207–210.

Le ledger `ledger_synchron_mzn.json` est lui aussi plafonné : `ASTRO-Q°ODE_SYSTEME\noeud_reseau_synchrone_al_mizan.py`, ligne 118, applique `self.data["blocs"] = self.data["blocs"][-100:]` puis incrémente `nb_blocs`. Les blocs ne portent pas de chemin de fichier : leur signature est l'horodatage seul (`timestamp_utc`), unique dans le fichier observé (100 blocs, 100 horodatages distincts). `nb_blocs` est cumulatif — observé à 350 pour 100 blocs conservés — et ne doit jamais être restauré à `len(blocs)`.

**Contrôle préalable, en lecture seule :**

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
py -3 -c "import json; p=r'ASTRO-Q°ODE_SYSTEME\memoire_aq\almizan_journal_agent_de_code.json'; d=json.load(open(p, encoding='utf-8-sig')); e=d['journal'][0]; print('cles:', sorted(e)); print('alias_ok:', {'horodatage_iso','chemin_fichier'} <= set(e))"
```

Après un instantané, vérifier aussi le résumé produit :

```python
import json
from pathlib import Path

d = json.loads(Path(r"C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas\instantane_avant.json").read_text(encoding="utf-8-sig"))
r = d["cibles"][0]["fichiers"]["almizan_journal_agent_de_code.json"]["json_resume"]["listes"]["journal"]
print("longueur", r["longueur"], "signatures", sum(r["signatures"].values()), "sans", r["sans_signature"])
```

**Règle d'arrêt :** si une liste censée porter un horodatage a `longueur > 0` et `sans_signature == longueur`, les alias ne correspondent pas au schéma réel. Arrêter la comparaison, lister les clés d'une entrée réelle et corriger les alias ; ne jamais conclure « aucune éviction » ni « aucun changement » dans cet état. Une liste sans horodatage ni fichier (des chaînes simples) reste légitimement sans signature : la traiter comme non attribuable par signature, sans la confondre avec un schéma cassé.

Le contrôle de non-régression de ces alias est dans `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\tester_instantane.py`. Il rejoue le schéma réel, l'éviction à longueur constante et une copie négative sans alias :

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\tester_instantane.py"
```

Attendre `RESULT: TOTAL=80 ECHECS=0` et le code de sortie 0. Le script travaille dans un répertoire temporaire et ne touche pas au `memoire_aq` réel.

```python
from collections import Counter
from pathlib import Path
import json
import os


def signature(entree: object) -> str | None:
    if not isinstance(entree, dict):
        return None
    horodatage = None
    for cle in ("horodatage_iso", "horodatage", "horodatage_utc", "timestamp", "timestamp_utc", "date", "ts"):
        if entree.get(cle) is not None:
            horodatage = str(entree[cle])
            break
    fichier = None
    for cle in ("chemin_fichier", "fichier", "file", "chemin", "path", "nom_fichier"):
        if entree.get(cle) is not None:
            fichier = str(entree[cle])
            break
    if horodatage is None and fichier is None:
        return None
    return f"{horodatage or ''}|{fichier or ''}"


def restaurer_journal(
    chemin: Path,
    signatures_ajoutees: list[str],
    total_connu: int,
) -> dict:
    donnees = json.loads(chemin.read_text(encoding="utf-8-sig"))
    journal = donnees.get("journal")
    if not isinstance(journal, list):
        raise ValueError("clé 'journal' absente ou invalide")
    a_retirer = Counter(signatures_ajoutees)
    garde = []
    for entree in journal:
        sig = signature(entree)
        if sig is not None and a_retirer[sig] > 0:
            a_retirer[sig] -= 1
            continue
        garde.append(entree)
    if any(a_retirer.values()):
        raise ValueError("signatures à retirer introuvables dans le journal actif")
    donnees["journal"] = garde
    donnees["total_fichiers_harmonises"] = total_connu
    if len(garde) != total_connu:
        raise ValueError(f"incohérence: {len(garde)} entrées pour total={total_connu}")
    temporaire = chemin.with_name(chemin.name + f".tmp-{os.getpid()}")
    temporaire.write_text(
        json.dumps(donnees, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporaire, chemin)
    return donnees
```

Règles :

- Ne jamais écrire `donnees["journal"] = journal[-N:]` ni fixer la longueur à une valeur attendue.
- `total_fichiers_harmonises` est recalculé par le code d'audit comme `len(journal)`. Ce n'est pas un total cumulatif. Le restaurer à une valeur historique est une déclaration sur l'état attendu, pas une reconstruction des entrées perdues.
- Si des signatures anciennes ont disparu et ne sont pas dans la sauvegarde, la perte est avérée. Le fichier actif ne les contient plus ; on ne peut pas les recréer sans source.
- Si des doublons partagent la même signature, retirer « le bon » nombre est sémantiquement équivalent, mais l'entrée exacte retirée n'est pas distinguable. L'indiquer dans le manifeste.

## 7. Étape E — vérifier après restauration

1. **Comparer à l'instantané avant** : les fichiers restaurés doivent avoir le même SHA-256, ou un SHA différent avec un contenu sémantiquement équivalent et des invariants vérifiés. Une réécriture identique (`mtime` changé, SHA identique) est signalée.
2. **Vérifier les références** : chaque clé de `sceaux` pointe vers un fichier existant ; chaque fichier scellé attendu est référencé ; les JSON restent parsables.
3. **Vérifier les compteurs** : `nb_sceaux == len(sceaux)`, `total_fichiers_harmonises == len(journal)`, `derniere_mise_a_jour` égale à la valeur connue. Une incohérence est un échec, pas un avertissement.
4. **Attendre puis re-instantanéer** : attendre 5 à 30 secondes, prendre un second instantané et le comparer au premier. Si l'état bouge, un écrivain est actif ; la restauration est provisoire.
5. **Valider en lecture seule** : chaque validateur doit lui-même être précédé d'un instantané. Un validateur qui écrit un sceau n'est pas lecture seule.

```bash
# Exemple de second contrôle après un délai
py -3 "C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\instantane_effets_de_bord.py" instantane \
  --cible "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\memoire_aq" \
  --recursif --stabilite 0.5 \
  --sortie "C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas\instantane_apres.json" \
  --sauvegarder "C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas\apres"

py -3 "C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\instantane_effets_de_bord.py" comparer \
  --instantane "C:\Users\Administrateur\.qoder\tmp\effets-de-bord\cas\instantane_apres.json" \
  --stabilite 0.3
```

`--stabilite` sur `comparer` refait la lecture après le délai et refuse de conclure si l'état bouge encore.

## 8. Manifeste de restauration

Écrire un manifeste même quand la restauration réussit. Il doit permettre à un tiers de distinguer « restauré », « partiellement restauré », « réécrit après restauration » et « perte inconnue ou avérée ».

```json
{
  "horodatage": "2026-10-26T13:02:46",
  "cibles": [
    "C:\\Users\\Administrateur\\Desktop\\IMAM8MAHDI\\ASTRO-Q°ODE_SYSTEME\\memoire_aq"
  ],
  "reference": "instantane_avant.json",
  "avant": {
    "index": {"taille": 5257, "sha256": "bb17522f..."},
    "journal": {"taille": 60804, "sha256": "e8ae4031...", "entrees": 100}
  },
  "apres": {
    "index": {"taille": 4473, "sha256": "69bdba80...", "sceaux": 12},
    "journal": {"taille": 60285, "sha256": "3b980e9c...", "entrees": 99}
  },
  "actions": [
    "suppression des clés d'index ajoutées",
    "suppression de l'entrée de journal ajoutée",
    "déplacement de deux sceaux en quarantaine"
  ],
  "quarantaine": [
    "C:\\Users\\Administrateur\\.qoder\\tmp\\effets-de-bord\\cas\\quarantaine"
  ],
  "incertitude": "éviction antérieure inconnue faute d'instantané avant l'incident",
  "reussite": "partielle"
}
```

Le champ `reussite` vaut `complete`, `partielle`, `provisoire` ou `echec`. « Provisoire » signifie qu'une réécriture post-restauration a été observée ou qu'un écrivain n'a pas été arrêté.

## 9. Pièges vérifiés

| Piège | Conséquence | Remède |
|---|---|---|
| Supposer les noms de clés des entrées | Le journal réel utilise `horodatage_iso` et `chemin_fichier`, le ledger `timestamp_utc` sans fichier ; avec des alias incomplets, toutes les entrées sont « sans signature » et une éviction reste invisible. | Vérifier le schéma sur une entrée réelle avant de conclure (6.1) ; si `sans_signature == longueur`, arrêter et corriger les alias ; rejouer le tester de non-régression. Les alias supportés incluent `horodatage_iso`, `horodatage`, `timestamp`, `timestamp_utc` et `chemin_fichier`, `fichier`, `chemin`. |
| Confondre `nb_blocs` du ledger avec `len(blocs)` | `nb_blocs` est cumulatif (observé 350 pour 100 blocs conservés) ; le ramener à la longueur de la fenêtre efface l'historique. | Restaurer `nb_blocs` depuis l'état de référence, puis vérifier séparément `len(blocs)`. |
| Conclure d'une longueur égale | Une liste plafonnée à 100 peut avoir évincé 75 entrées. | Comparer les signatures et leurs multiplicités. |
| Recalculer `nb_sceaux = len(sceaux)` | Masque une clé manquante ou une clé ajoutée non listée. | Restaurer la valeur connue puis vérifier l'égalité. |
| Traiter `total_fichiers_harmonises` comme un total cumulatif | Le champ vaut `len(journal)` : il ne compte que la fenêtre conservée. | Le nommer comme compteur de fenêtre dans le rapport. |
| Se fier à `audit_actif=false` | Un autre chemin ou un autre processus peut écrire. | Comparer les fichiers et les `mtime`. |
| Supprimer les nouveaux sceaux | Perte irréversible si un index ou un rapport les référence. | Quarantaine avec manifeste. |
| Restaurer sans arrêter l'audit de masse | Réécriture en quelques secondes, éviction de dizaines d'entrées. | Stabiliser, puis re-instantanéer après délai. |
| Comparer des dates UTC et locales | Décalage d'une heure dans la chronologie. | Préciser le fuseau ; stocker l'ISO 8601 avec `Z` ou offset. |
| Utiliser `python` du Microsoft Store | Code de sortie 49, aucune exécution. | Utiliser `py -3` ou `py -3.12`. |
| Rediriger la sortie vers `/tmp` depuis Git Bash | Python natif ne voit pas le chemin MSYS. | Utiliser un chemin Windows sous `C:\Users\...\.qoder\tmp`. |

## 10. Cas de référence

Le cas complet, avec les empreintes avant/après, les deux scénarios d'éviction et la réécriture post-restauration, est dans `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\references\cas-entite-2026-10-26.md`.
