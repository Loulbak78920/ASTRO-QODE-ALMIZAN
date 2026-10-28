# Caviardage, exemptions et scellement SHA-256

Détail des étapes 3 à 5 du `SKILL.md`. Les valeurs citées proviennent de la session de référence du 2026-10-27 (`cas-preuves-2026-10-27.md`) ou des sorties de script rejouées ce jour-là.

## 1. Périmètre : ce qui part, ce qui reste

| Garder | Retirer | Pourquoi |
|---|---|---|
| Nom, alias, nationalité, e-mail | Date de naissance (ISO et française), calendrier | L'attribution et la licence reposent sur le nom et le contact, pas sur la date |
| Organisation, ancres cryptographiques (tx, hash, ABI) | Adresse, code postal, commune, département, GPS | Un domicile identifie et expose sans rien prouver de plus |
| Nationalité, pays | Ville d'affiliation Zenodo, `city`, `birthPlace`, `geoLocation`, `pointLatitude`, `pointLongitude` | Champs de métadonnées qui recopient le domicile |

Ne jamais retirer un élément qui porte une preuve : un hash tronqué ou une signature effacée transforme le dossier en récit.

## 2. Passe structurelle (JSON)

Un JSON se caviarde par clés, pas par motifs : `re.sub` sur du texte JSON peut casser les virgules, les guillemets ou l'ordre des champs.

Clés supprimées dans le cas de référence (11) :

```
date_naissance_iso  calendrier_naissance  departement_naissance
departement_ancrage  coordonnees_gps_<commune>  ville_affiliation_zenodo
city  birthPlace  pointLatitude  pointLongitude  geoLocation
```

La clé GPS réelle porte la commune en suffixe ; elle est masquée ici (`coordonnees_gps_<commune>`).

Contrat de la fonction de nettoyage :

```python
def scrub(value):
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if k not in DROP}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, str):
        for pattern, replacement in REPL:
            value = re.sub(pattern, replacement, value)
        return value
    return value
```

Points qui comptent :

- La récursion couvre les objets imbriqués (`authors[].affiliation`, `metadata.creators[]`) ; une suppression au premier niveau laisse les mêmes champs dans les sous-objets.
- La sérialisation finale se fait en `json.dumps(data, ensure_ascii=False, indent=2) + "\n"` : pas de BOM, UTF-8, fin de ligne finale.
- Les remplacements textuels s'appliquent aussi aux chaînes JSON, mais uniquement après le filtrage des clés ; l'ordre des règles est celui du tableau `REPL` (58 règles dans le cas de référence).
- Les clés vides laissées par la suppression (`{"geo": {}}`) sont acceptables ; en revanche une valeur devenue `"France"` sous une clé `city` est un résidu : supprimer la clé.

## 3. Passe textuelle (Markdown, CFF, BibTeX)

Règles ordonnées du plus spécifique au plus générique. Un remplacement générique appliqué en premier détruit le contexte nécessaire aux règles suivantes.

Exemples de règles réellement utilisées, dans l'ordre :

| Ordre | Motif | Remplacement |
|---|---|---|
| 1 | `<commune> (<département>, <code>, France)` | `France` |
| 2 | `né le JJ/MM/AAAA à <commune>` | `né le [caviarde] en France` |
| 3 | `\bJJ/MM/AAAA\b`, `\bAAAA-MM-JJ\b` | `[caviarde]` |
| 4 | `\b<commune>(-<extension>)?\b`, `\b<département>\b`, `\b<commune-2>\b` | `France` |
| 5 | `\(?(<code>|<code-2>|<code-3>)\d{3}\)?` dans un contexte d'adresse | supprimé |
| 6 | `France, [A-ZÉÈ][\w-]+, France` | `France` |
| 7 | `né le \[caviarde\] à \*\*France\*\*` | `né le [caviarde] en **France**` |
| 8 | `\[caviarde\] \(\[caviarde\]\)` | `[caviarde]` |
| 9 | ligne `city:` / `birthPlace:` / `geoLocation:` seule | ligne supprimée |
| 10 | `[ ]{2,}` hors blocs de code | un espace |

Les marqueurs `JJ/MM/AAAA`, `<commune>`, `<département>`, `<code>` remplacent ici les valeurs réelles, qui ne se recopient jamais dans la documentation d'un dossier caviardé.

Contrôles après écriture :

- Relire les lignes touchées **avec leur contexte** (`grep -n -C2`), pas seulement le diff : un tableau Markdown dont une cellule est vide reste syntaxiquement valide tout en étant faux.
- Vérifier les listes : une puce qui commence maintenant par `[caviarde]` signale une règle trop gourmande.
- Quatre passes ont été nécessaires dans le cas de référence avant `REDACTION_OK`.

### Catalogue des résidus observés

| Résidu | Cause | Correction |
|---|---|---|
| `(Coordonnées: )` | valeur GPS supprimée, parenthèse conservée | supprimer la parenthèse vide |
| `France, <département>, France` | ville puis département remplacés séparément | règle dédiée avant la règle générique |
| `né le [caviarde] à **France**` | préposition « à » devant un pays | réécrire « en **France** » |
| `[caviarde] ([caviarde])` | date ISO et date française remplacées séparément | règle de fusion |
| `city: "France"` | clé de lieu résiduelle en YAML/CFF | supprimer la ligne |
| doubles espaces | valeur retirée au milieu d'une phrase | normaliser `[ ]{2,}` |
| `France ()` | parenthèse orpheline après suppression d'une ville | supprimer la parenthèse |

## 4. Protocole d'exemption

Le scan cherche des jetons courts (une année, par exemple) jusque dans le bytecode. Une occurrence dans une chaîne hexadécimale n'est pas une donnée personnelle : c'est une coïncidence de chiffres. L'exemption doit donc être **prouvée**, pas déclarée.

Algorithme (implémenté dans `preparer_publication.py scan`) :

1. Lire le fichier texte.
2. Calculer `outside = re.sub(r"[0-9a-fA-F]{16,}", "", text)` : toute suite hexadécimale d'au moins 16 caractères disparaît.
3. Compter le jeton dans le texte brut (`total`) et dans `outside` (`bare`).
4. Si `bare == 0` : exemption acceptée, `EXEMPT <rel> token=<tok> occurrences=<total> hex_only=yes`.
5. Sinon : `hex_only=no`, l'occurrence est comptée comme problème, code 1.

Règles :

- Une exemption ne vaut que pour un couple **fichier + jeton**. Pas de wildcard, pas d'exemption de répertoire.
- Fichiers éligibles : artefacts publics et lisibles on-chain (transaction JSON-RPC, bytecode/ABI d'un contrat vérifié). Jamais un document d'identité, une licence, un README, un historique Git.
- Une exemption déclarée sans occurrence est signalée `EXEMPT_UNUSED` (code 0) : la retirer pour qu'aucune exemption ne dorme dans la documentation.
- Un jeton dont la seule présence est hexadécimale peut aussi être prouvé par `absence`, qui cherche la chaîne en clair **et** son encodage hexadécimal :

```bash
py -3 scripts/preparer_publication.py absence --dossier "<dossier>" \
  --needle "JJ/MM/AAAA" --needle "AAAA-MM-JJ" --needle "<commune>"
# NEEDLE 'AAAA-MM-JJ' raw_or_hex_found=no ... ABSENCE_OK
```

Les valeurs réelles se passent en argument à l'exécution ; elles ne s'écrivent ni dans le Skill, ni dans un fichier du dossier publié.

Le fragment hexadécimal qui déclenchait le faux positif dans le cas de référence :

```
8d5260208d019b909b52998b019890985260608a01969096526080
```

Décodé en ASCII, il ne contient ni date ni nom (0 correspondance) ; la preuve est consignée, l'exemption acceptée.

## 5. Manifeste et vérificateur

### Format du manifeste

`05_EMPREINTES/MANIFESTE_SHA256.json` :

```json
{
  "captured_at_utc": "2026-10-27T13:04:19.779442+00:00",
  "algorithme": "SHA-256",
  "portee": "tous les fichiers du depot sauf ce manifeste",
  "nb_fichiers": 39,
  "empreinte_liste": "<sha256 des lignes 'sha256  chemin'>",
  "fichiers": [
    {"chemin": ".gitattributes", "octets": 8, "sha256": "705fd4d6..."}
  ]
}
```

Propriétés :

- Le manifeste **s'exclut lui-même** ; sinon son hash change quand il s'écrit.
- `chemin` est relatif à la racine, séparateur `/`, trié.
- `empreinte_liste` est le SHA-256 de la concaténation `"%s  %s\n" % (sha256, chemin)` : il scelle l'ensemble en une valeur unique.
- `octets` permet de distinguer un contenu changé d'un fichier tronqué (`MISMATCH_SIZE`).
- `.git` et `__pycache__` sont ignorés.

### Contrat du vérificateur

`verifier_empreintes.py` est copié dans `05_EMPREINTES/` **avant** la génération du manifeste, donc il est lui-même empreinté. Il fonctionne sans argument depuis ce dossier (`root = dirname(__file__)`), ou avec `--dossier <racine>`.

| Sortie | Signification | Code |
|---|---|---|
| `OK=n MISMATCH=0 MISSING=0 EXTRA=0` puis `RESULT OK` | clone conforme | 0 |
| `MISMATCH <rel> attendu=… obtenu=…` | contenu modifié | 1 |
| `MISMATCH_SIZE <rel> attendu=… obtenu=…` | taille modifiée | 1 |
| `MISSING <rel>` | fichier absent | 1 |
| `EXTRA <rel>` | fichier non empreinté | 1 |
| `MANIFEST_ABSENT <rel>` | manifeste introuvable | 2 |
| `MANIFEST_VIDE <rel>` | manifeste sans entrée | 2 |

`EXTRA` est aussi un contrôle de complétude : un fichier ajouté après scellement (brouillon, `.env`, note) est signalé. Inversement, compter `git ls-files | wc -l` doit donner `nb_fichiers + 1` (le manifeste), ce qui attrape un fichier oublié avant scellement.

### Cycle de scellement

```bash
cp scripts/verifier_empreintes.py "<dossier>/05_EMPREINTES/"
py -3 scripts/preparer_publication.py manifeste --dossier "<dossier>"
py -3 scripts/verifier_empreintes.py --dossier "<dossier>"
```

`manifeste` écrit `.gitattributes` avec `* -text` s'il est absent (`GITATTRIBUTES_WRITTEN`), vérifie la règle s'il existe (`GITATTRIBUTES_PRESENT`, sinon `GITATTRIBUTES_NO_RULE` et code 1), puis écrit le manifeste. Sortie : `FILES n`, `MANIFEST_SHA256 <hex>`, `RESULT OK`.

Une seconde exécution change `captured_at_utc`, donc `MANIFEST_SHA256` : c'est attendu, et c'est pourquoi le manifeste se génère **une dernière fois** puis reste gelé. Ne jamais régénérer après publication.

## 6. `.gitattributes` et fins de ligne

Sans règle, un clone Windows avec `core.autocrlf=true` convertit les LF en CRLF : les fichiers sont intacts mais leurs octets changent, et le vérificateur renvoie `MISMATCH` sur tout le dossier.

```
* -text
```

- Écrire la règle **avant le premier commit** ; l'ajouter après coup ne protège pas les blobs déjà stockés.
- Preuve que la règle est dans l'objet publié : `git show HEAD:.gitattributes | od -c` → `*   -   t   e   x   t  \n`.
- Le fichier fait partie des fichiers empreintés ; il n'est pas exclus du manifeste.

## 7. Artefacts non publiés et correspondance

`05_EMPREINTES/EMPREINTES_ARTEFACTS_NON_PUBLIES.json` :

```json
{"captured_at_utc": "...", "artefacts": [
  {"path": "...zip", "bytes": 168148, "sha256": "...",
   "raison_non_publie": "archive ZIP (contient les originaux non caviardes)"}
]}
```

- Empreinte seule, jamais le contenu : ZIP d'originaux, source Solidity dont un commentaire porte la date de naissance, PDF.
- Ce fichier ne se vérifie pas par un tiers : il permet à l'auteur de rapprocher copies et originaux, et doit le dire.
- `06_CORRESPONDANCE_ORIGINAUX/TABLE_CORRESPONDANCE_CAVIARDAGE.json` liste les transformations (`"Date de naissance supprimee"`, etc.) et le couple fichier source / copie publiée. Il ne contient aucune valeur retirée.

## 8. Matrice de tests négatifs (rejouée)

| Mutation | Sortie attendue | Code |
|---|---|---|
| Ajouter un octet à un fichier | `MISMATCH` | 1 |
| Supprimer un fichier | `MISSING` | 1 |
| Ajouter un fichier | `EXTRA` | 1 |
| Planter un jeton en clair dans un README | `HIT README.md:<n>` + `REDACTION_PROBLEMS 1` | 1 |
| Exempter une occurrence en clair | `hex_only=no` + `REDACTION_PROBLEMS` | 1 |
| Manifeste absent | `MANIFEST_ABSENT` | 2 |
| Manifeste vide | `MANIFEST_VIDE` | 2 |
| Régénérer le manifeste | `MANIFEST_SHA256` différent | 0 |

Ces mutations ont été exécutées sur une copie jetable, pas sur le dossier publié. Un `RESULT OK` obtenu sans mutation négative ne prouve pas que le vérificateur détecte quoi que ce soit.
