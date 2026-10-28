# Cas 2026-10-27 — désinfection du paquet `publier-preuves-anteriorite-caviardees`

## Portée et source

- Session source : `f6ffa50f-f0e5-4f65-8d5d-7b90b1e31400`, lue par `read_chat_session` : 4 messages, `runtimeState=cold`, `revision=0`, `hasMoreBefore=false`.
- Objet : un paquet Skill venait d'être créé pour enseigner le caviardage d'un dossier public ; il recopiait lui-même des valeurs réelles dans ses exemples.
- **Aucune correction utilisateur** dans cette session. La seconde passe est une décision de l'agent après relecture du paquet : ne pas la présenter comme une consigne reçue.

## Ce qui avait fuité — catégories, sans valeurs

- Fichiers touchés : `SKILL.md`, les deux références, la docstring d'un script.
- Catégories : date de naissance au format ISO et au format français, commune, département, code postal, coordonnées GPS.
- Origine : les exemples avaient été recopiés d'un dossier réel, y compris dans des blocs de code et des tableaux.
- Le paquet a été construit pour retirer ces valeurs d'un dossier publié, puis les a reproduites dans sa propre documentation.

## Passe de désinfection

- Compteurs relevés par l'outil de la session : **11 clés supprimées**, **58 règles de remplacement**, **9 jetons interdits**. Les valeurs ne sont pas conservées dans ce document.
- Quatre passes ont été nécessaires avant la preuve d'absence. Résidus traités : date ISO et date française remplacées séparément, préposition « à » devant un pays, ville puis département remplacés séparément, parenthèse orpheline, clé de lieu résiduelle en YAML/CFF, doubles espaces, cellule de tableau vidée.
- Les ancres cryptographiques publiques (hash, transaction, ABI) ont été conservées : leurs suites hexadécimales peuvent contenir par coïncidence une année ou un nombre, sans être une donnée personnelle. Deux fragments publics sont restés, intacts et documentés.
- Preuve d'absence : sortie `AUCUN_JETON_EN_CLAIR` après les remplacements. Aucune valeur n'a été réaffichée dans la sortie de contrôle.

## Empreintes de la version scellée

Validation statique, deux passages le même jour (heures locales, +01:00) :

| Passage | Heure | `SKILL.md` | SHA-256 |
|---|---|---|---|
| Avant désinfection | 14:15:29 | 18 007 B | `c749692cd571d43bbb9f7e0e6b18a8c36f9338efa2cea8691d4e79b210e34630` |
| Après désinfection | 14:24:36 | 18 117 B | `725747d1350a97b03c4d8d17c930f9d725bbcb67cdefcc249ebeefe925abbe3e` |

Les deux passages affichaient `RESULT PASS` (10 pass, 0 fail). Le second est la version citée comme preuve de la désinfection.

Empreintes du paquet à 14:24:36 (+01:00) :

| Fichier | Octets | SHA-256 |
|---|---:|---|
| `SKILL.md` | 18 117 | `725747d1…5abbe3e` |
| `references/caviardage-et-empreintes.md` | 11 777 | `26415b66…8279da9d` |
| `references/cas-preuves-2026-10-27.md` | 9 955 | `092464f2…95422080` |
| `scripts/preparer_publication.py` | 12 387 | `8913ad72…920512fb` |
| `scripts/verifier_empreintes.py` | 3 078 | `76de8c0e…7c1e2f66` |

## Correction de provenance des hachages

Deux valeurs avaient été confondues dans la documentation :

| Valeur | Ce qu'elle couvre | Valeur observée |
|---|---|---|
| `empreinte_liste` du manifeste publié | la concaténation `sha256  chemin` des entrées | `ab6d393c475f7e463e06b75818b7b3e927056d246e1e49d5b1f7648e9aa30452` |
| SHA-256 du fichier manifeste publié | ses 7 345 octets | `ed0287e12e94e103363230269cc8668ef15ad7a8c7893e7a2b9929e41105e6d9` |

- `.gitattributes` du dépôt publié faisait **8 octets**, pas 10.
- La confusion venait d'un rapport qui présentait `ab6d393c…` comme « le hash du manifeste » alors qu'il s'agit de l'empreinte de la liste.
- Règle retenue : toujours calculer séparément le fichier et `empreinte_liste`, et joindre la taille du fichier.

## Recontrôle du paquet courant

- Au relevé du **2026-10-27 à 14:43:41 +01:00**, trois fichiers du paquet avaient changé depuis 14:24 : `SKILL.md` (18 255 B, `83a2eb5b…`), `references/cas-preuves-2026-10-27.md` (9 966 B, `5aa39421…`) et `scripts/preparer_publication.py` (12 549 B, `acf2c831…`), avec des mtimes à 14:40.
- `references/caviardage-et-empreintes.md` et `scripts/verifier_empreintes.py` étaient inchangés.
- Une autre session a donc modifié le paquet après la preuve. **Les empreintes de la section précédente ne décrivent plus le paquet courant** ; elles restent la preuve de la version scellée à 14:24:36.
- Aucun dépôt Git n'est présent dans le répertoire du Skill (`NO_GIT`) : la modification n'est pas attribuable par un commit.

## Limites

- Les options exactes du `grep` de contrôle initial n'ont pas été restituées par `read_chat_session` : le mécanisme est documenté, la commande littérale reste **non vérifiée**.
- Le cas ne documente ni commit ni push ; aucune opération Git n'est attestée dans les sorties lues.
- La preuve `AUCUN_JETON_EN_CLAIR` est liée à la version de 14:24:36. Le paquet ayant changé à 14:40, elle ne peut pas être réutilisée telle quelle pour la version courante.
- Ce document ne contient aucune valeur retirée : il ne permet pas de reconstruire les données d'origine.
- Les compteurs 11 / 58 / 9 sont des sorties d'outil conservées dans la session ; ils ne sont pas recalculés ici.

## Enseignements

- Un paquet qui enseigne le caviardage peut republier ce qu'il retire : la relecture doit porter sur ses propres exemples.
- Un scan de paquet doit rester sûr dans les logs : masquer les valeurs par un index, pas les afficher dans `HIT` ou `NEEDLE`.
- Une occurrence dans une suite hexadécimale n'est pas une donnée personnelle : la conserver et la qualifier, sans exemption de fichier entier.
- La provenance d'un hash se vérifie : fichier manifeste et `empreinte_liste` ne sont pas interchangeables.
- Une preuve d'absence sans test négatif est vacante : il faut planter un jeton synthétique et exiger un échec.
