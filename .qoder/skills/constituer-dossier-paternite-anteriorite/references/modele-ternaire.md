# Modele ternaire de qualification

La qualification juridique se fait en logique de Kleene a trois etats. Un fait non
prouve vaut `INDETERMINE` : il n'est jamais converti en `VRAI` pour faire aboutir une
conclusion.

## 1. Tables de verite

`ET` :

| ET | VRAI | FAUX | INDETERMINE |
|---|---|---|---|
| VRAI | VRAI | FAUX | INDETERMINE |
| FAUX | FAUX | FAUX | FAUX |
| INDETERMINE | INDETERMINE | FAUX | INDETERMINE |

`OU` :

| OU | VRAI | FAUX | INDETERMINE |
|---|---|---|---|
| VRAI | VRAI | VRAI | VRAI |
| FAUX | VRAI | FAUX | INDETERMINE |
| INDETERMINE | VRAI | INDETERMINE | INDETERMINE |

`NON` : `VRAI` devient `FAUX`, `FAUX` devient `VRAI`, `INDETERMINE` reste
`INDETERMINE`.

Consequence : une seule condition refutee suffit a refuter une conjonction. Une
condition indeterminee ne refute pas ; elle empeche de conclure.

## 2. Schema JSON

```json
{
  "version": "1.0",
  "predicats": [
    {
      "id": "P08",
      "libelle": "Defendeur identifie",
      "valeur": "FAUX",
      "base_legale": "CPC 42, 46",
      "preuves": [],
      "commentaire": "Aucune personne designee avec une preuve de reproduction."
    }
  ],
  "regles": [
    {
      "id": "E5",
      "libelle": "Refere-provision",
      "expression": "P16 ET P17 ET P08",
      "base_legale": "CPC 835 al. 2",
      "consequence": "Condamnation provisionnelle au paiement d'une somme."
    }
  ]
}
```

Contraintes :

- chaque `id` est unique, en majuscules, chiffres et underscore ;
- chaque `valeur` de predicat vaut exactement `VRAI`, `FAUX` ou `INDETERMINE` ;
- seuls les operateurs `ET`, `OU`, `NON` et les parentheses sont acceptes ;
- une regle peut referencer une autre regle ; l'evaluateur resout les dependances
  recursivement et signale les cycles ;
- l'ordre des regles dans le fichier n'a pas d'importance.

## 3. Regles de reference

| ID | Regle | Forme | Ce qu'elle exige |
|---|---|---|---|
| E1 | Titularite | `P01 ET P02 ET (P03 OU P04)` | oeuvres identifiees, auteur identifie, une date certaine |
| E2 | Paternite opposable | `P01 ET P02 ET P07 ET (P03 OU P04)` | titularite et presomption d'auteur corroborees par un ancrage tiers |
| E3 | Contrefacon civile | `E2 ET P08 ET (P09 OU P10) ET P11` | paternite, defendeur, reproduction ou acces, absence d'autorisation |
| E4 | Dol | `P12 ET P13 ET P14` | manoeuvre, intention, erreur determinante |
| E5 | Refere-provision | `P16 ET P17 ET P08` | urgence, obligation non contestable, debiteur determine |
| E6 | Mesure in futurum | `P20 ET P19` | motif legitime et preuves exposees a alteration |
| E7 | Saisie-contrefacon | `E2 ET P18` | paternite et indices de contrefacon |
| E8 | Contrefacon penale | `E3 ET P13` | contrefacon civile et intention |
| E9 | Action non prescrite | `P22` | point de depart de la prescription connu |

Adapter les identifiants et les textes au dossier, mais conserver la structure : une
condition manquante doit apparaitre comme un terme `FAUX` ou `INDETERMINE`, pas etre
supprimee de l'expression.

## 4. Porte d'acceptation

Le script accepte `--exiger E2` (repetable). Il retourne 0 seulement si toutes les
regles exigees valent `VRAI`. Sans `--exiger`, il retourne 0 si le modele a pu etre
evalue.

Codes de retour :

| Code | Signification |
|---|---|
| 0 | modele evalue, portes remplies |
| 1 | atome inconnu, syntaxe, cycle, ou porte non remplie |
| 2 | fichier absent, JSON invalide, schema incomplet |

Une porte non remplie n'est pas une erreur technique : c'est le resultat honnete du
modele. Le rapport doit l'ecrire comme un constat, pas comme un echec de script.

## 5. Predicats a ne pas oublier

- `P05` : date certaine par DOI enregistre. Un DOI non enregistre ou supprime rend ce
  predicat `FAUX` ; il ne rend pas l'oeuvre inexistante.
- `P08` : defendeur identifie. Sans nom et sans preuve de reproduction, `FAUX`.
  « La cybernetique mondiale » ou « les infrastructures » ne sont pas des personnes
  juridiques.
- `P09` / `P10` : reproduction identifiee et similitude. Une oeuvre publique est
  accessible, mais l'acces possible ne prouve pas la copie.
- `P11` : absence d'autorisation. Elle suppose un exploitant identifie.
- `P12` a `P14` : dol. L'intention ne se presume pas.
- `P15` : prejudice chiffre. Sans volumes, prix ou comptes, `FAUX`.
- `P16` : urgence. Une alteration de preuve est un risque probatoire, pas
  necessairement une urgence au fond.
- `P17` : obligation non serieusement contestable. Un contrat non signe ne la fonde
  pas.
- `P19` / `P20` : preuves exposees et motif legitime de conservation, base de la
  mesure CPC 145.

## 6. Couverture

La couverture affichee est la part de predicats de base tenus pour `VRAI`. Elle ne
mesure ni la force d'un temoignage, ni la credibilite d'une expertise, ni
l'appreciation souveraine du juge. Un taux de 100 % sur des predicats mal qualifies
reste un mauvais dossier.

Regle de redaction : toute conclusion affichee doit citer les predicats qui la
fondent et ceux qui la refutent ou la laissent indeterminee.

## 7. Exemple de sortie attendue

```text
REGLES: 9 evaluees
RESULTATS: E1=VRAI E2=VRAI E3=FAUX E4=INDETERMINE E5=FAUX E6=VRAI E7=INDETERMINE E8=FAUX E9=VRAI
GATE E2: VRAI
RESULTAT: OK
```

Dans cet exemple, la paternite est etablie, mais la contrefacon est refutee par
l'absence de defendeur (`P08=FAUX`) et le refere-provision est irrecevable
(`E5=FAUX`). La mesure CPC 145 reste faisable (`E6=VRAI`).
