# Grille juridique francaise de reference

> Ce document est un aide-memoire de qualification, pas une consultation juridique.
> Les textes doivent etre verifies a jour avant toute procedure. La representation
> par avocat est obligatoire devant le Tribunal judiciaire dans les matieres visees
> ici (CPC 760). Ne jamais produire un acte pret a signifier.

## 1. Droit d'auteur

| Element | Texte | Ce qu'il faut prouver | Etat possible |
|---|---|---|---|
| Qualification d'oeuvre | CPI L112-1, L112-2 | forme originale, genre, support ; logiciel vise au 13° | ETABLI / A DEBATTRE |
| Titularite initiale | CPI L111-1 | creation et droits moraux et patrimoniaux | ETABLI |
| Presomption d'auteur | CPI L113-1 | nom sous lequel l'oeuvre est divulguee | ETABLI sauf preuve contraire |
| Droit moral | CPI L121-1 | divulgation, nom, respect de l'oeuvre | ETABLI |
| Reproduction ou representation non autorisee | CPI L122-4 | acte de reproduction ou de representation, sans autorisation | A PROUVER |
| Cession de droits | CPI L131-3 | ecrit, droits cedes delimites, remuneration | A PROUVER |
| Action civile en contrefacon | CPI L331-1 | titularite, defendeur, atteinte | RECEVABLE si defendeur identifie |
| Saisie-contrefacon | CPI L332-1 et suivants | indices de contrefacon, autorisation du juge | NON ACQUISE sans indices |
| Contrefacon penale | CPI L335-2 | intention, auteur identifie | NON ETABLIE sans ces elements |

## 2. Droit civil

| Element | Texte | Ce qu'il faut prouver | Piege |
|---|---|---|---|
| Dol | C. civ. 1137 | manoeuvre, intention, erreur determinante | l'intention ne se presume pas |
| Faute | C. civ. 1240 | fait fautif imputable a une personne | « le systeme » n'est pas une personne |
| Responsabilite contractuelle | C. civ. 1231-1 | contrat valable, obligation, inexécution | un modele non signe ne fonde rien |
| Preuve par ecrit electronique | C. civ. 1366, 1367 | identite de l'auteur, fiabilite du procede | un hash seul ne prouve pas l'auteur |
| Prescription | C. civ. 2224 | point de depart de la connaissance des faits | cinq ans, a dater par acte |

## 3. Procedure

| Element | Texte | Condition | Etat typique |
|---|---|---|---|
| Mesure in futurum | CPC 145 | motif legitime de conserver ou d'etablir une preuve avant proces | FAISABLE |
| Refere d'urgence | CPC 834 | peril imminent et actuel, mesure proportionnee | NON ACQUIS sans peril |
| Refere-provision | CPC 835 al. 2 | obligation non serieusement contestable | IRRECEVABLE sans debiteur et obligation |
| Competence | CPC 42, 46 | domicile du defendeur ou options contractuelles/delictuelles | A DETERMINER |
| Representation | CPC 760 | avocat devant le Tribunal judiciaire | OBLIGATOIRE |

## 4. La regle dure : pas de defendeur, pas de refere-provision

Le refere-provision de l'article 835 alinea 2 du CPC suppose trois elements
cumulatifs :

1. un **debiteur determine** ;
2. une **obligation non serieusement contestable** ;
3. une **urgence** justifiant une condamnation provisoire.

La paternite n'est pas une creance. Etablir qui a ecrit une oeuvre ne designe aucun
debiteur et ne fonde aucune somme due. Sans exploitant identifie et sans preuve de
reproduction, la demande est irrecevable ou vouee au rejet, et expose le demandeur a
une amende civile pour procedure abusive.

Consequence pratique :

- si `P08` (defendeur identifie) vaut `FAUX`, alors `E5` (refere-provision) vaut
  `FAUX`, quel que soit le reste ;
- si le contrat 50/50 n'est pas signe, `P17` (obligation non contestable) vaut
  `FAUX` ;
- si l'urgence n'est pas caracterisee, `P16` reste `INDETERMINE` ou `FAUX`.

## 5. Hierarchie des actions realistes

1. **Constat** de l'oeuvre, des depots et du contrat deploye par commissaire de
   justice ou expert.
2. **Identification** des exploitants : whois, mentions legales, API, captures
   datees, constat.
3. **Mise en demeure** adressee a une personne determinee, avec les pieces.
4. **Mesure CPC 145** pour conserver ou etablir la preuve avant tout proces.
5. **Saisie-contrefacon** si des indices de contrefacon existent.
6. **Action civile** en contrefacon et en dommages-interets.
7. **Action penale** seulement si l'intention et l'auteur sont etablis.

Ne pas sauter d'etape pour « faire peur » : une mise en demeure sans destinataire, un
refere sans debiteur ou une accusation penale sans intention se retournent contre le
demandeur.

## 6. Conditions a remplir pour changer d'etat

| Manque | Ou le trouver | Delai indicatif |
|---|---|---|
| Identite d'un exploitant | whois, mentions legales, API, constat | 2 a 4 semaines |
| Preuve de reproduction | constat, capture datee, comparaison de code | 2 a 6 semaines |
| Absence d'autorisation | registre des licences, correspondances | immediat |
| Chiffrage du prejudice | volumes, prix, comptes, expertise | 4 a 8 semaines |
| Mise en demeure infructueuse | courrier recommande, accuse de reception | 2 semaines |

## 7. Ce que le dossier ne doit jamais affirmer

- qu'une personne morale determinee a commis un dol sans piece de manoeuvre ;
- qu'une infrastructure est complice du seul fait qu'elle heberge ou indexe ;
- qu'un DOI supprime efface l'anteriorite factuelle ;
- qu'un hash local vaut date certaine ;
- qu'un refere-provision est recevable sans debiteur identifie.

Ces affirmations exposent a la diffamation, a la procedure abusive et a la perte de
credibilite du dossier entier.
