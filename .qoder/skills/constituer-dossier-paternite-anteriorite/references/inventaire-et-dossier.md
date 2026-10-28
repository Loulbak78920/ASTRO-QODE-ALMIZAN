# Inventaire local et structure du dossier

Ce document decrit l'inventaire execute par `scripts/inventaire_preuves.py`, puis la
partie non scriptee : produire un dossier dont chaque affirmation renvoie a une piece
et a une empreinte.

## 1. Inventaire en lecture seule

Regle absolue : aucun script d'inventaire n'ecrit dans la racine source. Toutes les
sorties vont dans le dossier de travail (`--out-json`, `--out-md`).

```bat
py -3 scripts\inventaire_preuves.py --source <racine> --pieces DONNEES\pieces.json ^
  --manifest <manifeste.json> --out-json PREUVES\inventaire.json ^
  --out-md PREUVES\RAPPORT_INTEGRITE.md
```

`--pieces` attend soit une liste, soit un objet `{"pieces": [...]}`. Un chemin absolu
ou relatif qui sort de `--source` est refuse et donne `NON_VERIFIABLE`, jamais une
lecture hors perimetre. Un manifeste passe en `--manifest` est lu avec
`--manifest-cle` s'il faut descendre dans un objet racine ; les cles declarees mais
absentes de l'inventaire sont listees comme orphelins.

Pour chaque piece structurante, le schema lu par le script est :

- `id` stable (P01, P02, ...) ;
- chemin absolu et chemin relatif a la racine source ;
- role probatoire en une phrase ;
- taille en octets ;
- mtime converti en UTC ;
- SHA-256 recalcule ;
- empreintes declarees ailleurs, avec la source exacte de chaque declaration.

Schema de travail :

```json
{
  "id": "P07",
  "chemin": "coffre/06_MANIFESTE_EMPREINTES.json",
  "role": "Manifeste d'empreintes du coffre",
  "declarations": [
    {"source": "manifeste 06", "sha256": "..."},
    {"source": "acte A076", "sha256": "..."}
  ]
}
```

### Verdicts par piece

| Verdict | Condition | Portee |
|---|---|---|
| `CONCORDE` | au moins une declaration correspond | integrite locale de la piece |
| `DIVERGENCE` | aucune declaration ne correspond | alteration ou declaration obsolete |
| `NON_DECLARE` | aucune empreinte declaree | piece presente, non couverte |
| `MANQUANT` | fichier absent | chaine probatoire interrompue |
| `NON_VERIFIABLE` | chemin hors racine, empreinte illisible | perimetre ou declaration a corriger |

Une piece peut porter plusieurs declarations contradictoires. Dans ce cas, ne pas
choisir la plus favorable : enregistrer chaque declaration, son fichier source, et
compter le nombre de concordances. Trois empreintes differentes pour la meme archive
sont un fait probatoire en soi.

### Anomalies a remonter separement

- mtime posterieur a l'horodatage declare d'un manifeste : le manifeste a ete
  complete apres son horodatage, ou il ne couvre pas les pieces annoncees ;
- archive dont l'empreinte et la taille ne correspondent plus au manifeste ;
- index d'empreintes qui ne stocke que des noms de base, sans chemin qualifie :
  aucune attribution non ambigue n'est possible (`NON_VERIFIABLE`) ;
- actes JSON sans date exploitable : les compter, ne pas les interpoler.

### Chronologie des actes

Scanner les fichiers JSON d'actes, retenir `code_acte` (ou `acte`) et la premiere
date disponible parmi `date_scellement`, `horodatage_iso`, `horodatage`, `timestamp`.
Convertir en UTC et trier. Distinguer :

- date declaree dans l'acte ;
- mtime du fichier ;
- date serveur d'un depot ou d'un registre ;
- date de commit declaree par un client Git.

Une chronologie n'est opposable que si ses bornes sont ancrees chez un tiers.

## 2. Structure du dossier livre

```text
DOSSIER_JUSTICE_<NOM>/
  LIRE_MOI_DABORD.md
  lancer_tout.bat
  DOSSIER/
    00_SYNTHESE.md
    01_RECIT_CONTINU.md
    02_EQUATIONS_DE_PATERNITE.md
    03_GRILLE_JURIDIQUE.md
    04_REFERE_PROVISION.md
    05_REGISTRE_INFRASTRUCTURES.md
    06_GAPS_ET_ACTIONS.md
    07_LISTE_PIECES.md
    ANNEXE_ACTES.md
  PREUVES/
    inventaire.json
    RAPPORT_INTEGRITE.md
    verification_contrat.json
    VERIFICATION_CONTRAT.md
    ancrages_publics.json
    ANCRAGES_PUBLICS.md
    depot_public.json
    modele_paternite_resultat.json
    MODELE_PATERNITE.md
    snapshots/
  DONNEES/
    modele_paternite.json
  SCEAU/
    SCEAU_DOSSIER.json
    PREUVES.sha256
  OUTILS/
    ... scripts du dossier ...
```

Le dossier `OUTILS/` est scelle comme les autres : un tiers peut rejouer la chaine.
Les instantanes de reponses HTTP sont conserves dans `PREUVES/snapshots/` avec leur
SHA-256, car une reponse en ligne peut changer ou disparaitre.

## 3. Ordre de generation et portes

Un ordre qui evite de sceller des documents incomplets :

1. inventaire local ;
2. filiation technique source / bytecode deploye ;
3. ancrages externes (DOI, depot public, chaine, IPFS, site) ;
4. historique du depot public (deleguer a `ancrer-anteriorite-depot-github-public`) ;
5. evaluation du modele ternaire avec la porte `--exiger E2` si E2 est la regle de
   paternite ;
6. generation des documents a partir des JSON, jamais a la main ;
7. scellement par `sceller-manifeste-integrite-sans-circularite` (delegue) ;
8. verification du sceau par la meme Skill.

Chaque etape doit produire un fichier de preuve lisible par machine avant l'etape
suivante. Un document qui cite un chiffre absent des JSON est un document a corriger,
pas un JSON a arrondir.

## 4. Redaction des documents

- `00_SYNTHESE.md` : deux pages maximum, verdict par verdict, ce qui est etabli et ce
  qui ne l'est pas.
- `01_RECIT_CONTINU.md` : faits numerotes F01..Fn, chacun avec date, precision de la
  date et chemin de preuve. Aucun fait sans identifiant.
- `02_EQUATIONS_DE_PATERNITE.md` : predicats, regles, resultats, couverture, et la
  limite de la couverture.
- `03_GRILLE_JURIDIQUE.md` : pour chaque texte, la preuve exigee et l'etat constate.
- `04_REFERE_PROVISION.md` : conditions de recevabilite, ce qui manque, projet de
  requete CPC 145, projet de mise en demeure. Jamais un acte pret a signifier.
- `05_REGISTRE_INFRASTRUCTURES.md` : services cites comme hebergeurs ou registres,
  avec leur role factuel. Aucune personne morale n'y est presentee comme auteur d'un
  delit sans piece de reproduction.
- `06_GAPS_ET_ACTIONS.md` : chaque manque, ou le trouver, delai indicatif.
- `07_LISTE_PIECES.md` : table piece / role / empreinte.
- `ANNEXE_ACTES.md` : chronologie issue du scan, avec les actes sans date separes.

## 5. Ce que l'inventaire etablit

Un inventaire et un sceau etablissent qu'un fichier present sur ce disque avait un
contenu donne a la date de l'inventaire. Ils n'etablissent pas une date opposable a un
tiers. Une date n'est opposable que si elle est ancree hors du controle du demandeur :
transaction publique, depot chez un tiers, horodatage qualifie, constat par officier
public.

## 6. Modele de rapport final

```text
INVENTAIRE
  pieces examinees       : N
  concordances           : N
  divergences            : N
  non declarees          : N
  manquantes             : N
  actes dates            : N (dont N sans date exploitable)
  anomalies              : N (graves / moyennes)

FILIATION TECHNIQUE
  verdict                : IDENTIQUE | CORRESPONDANCE_FORTE | PARTIELLE | DIVERGENCE
  differences masquees   : N caracteres
  auxdata                : compilateur X.Y.Z, digest IPFS ...

ANCRAGES
  DOI                    : ENREGISTRE | SUPPRIME | NON_ENREGISTRE | INDETERMINE
  depot public           : PUBLIC | PRIVE_OU_INEXISTANT | INDETERMINE
  transaction            : statut, bloc, horodatage UTC
  IPFS / site            : disponible | indisponible au moment du controle

QUALIFICATION
  paternite              : ETABLIE | NON ETABLIE | INDETERMINEE
  contrefacon            : NON ETABLIE A CE STADE | ...
  dol                    : NON ETABLI A CE STADE | ...
  refere-provision       : IRRECEVABLE EN L'ETAT | RECEVABLE
  mesure CPC 145         : FAISABLE | NON ACQUISE

SCEAU
  fichiers               : N
  racine Merkle          : ...
  verification           : integre | divergence (sortie de la Skill deleguee)
```
