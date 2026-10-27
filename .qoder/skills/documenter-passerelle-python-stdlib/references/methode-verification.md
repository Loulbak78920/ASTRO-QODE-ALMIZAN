# Méthode de vérification d'une documentation de passerelle

Chaîne reproductible pour documenter une passerelle HTTP Python sans framework
(`http.server`, `urllib`, `json`) dont chaque route, exemple et affirmation doit
correspondre au code réellement exécuté.

## 0. Règle de preuve

Hiérarchie des sources, de la plus forte à la plus faible :

1. sortie réelle d'un test ou d'une requête exécutée ;
2. code source du routeur et des modules appelés ;
3. réponse HTTP en lecture seule sur l'environnement cible ;
4. documentation existante.

Une affirmation publiée reçoit une étiquette explicite : `opérationnel`
(observé), `simulé` (émulation logicielle), `spécifié` (paramètre de
conception, non certifié) ou `déclaré · non vérifié` (adresse, partenariat,
liquidité). Un chiffre sans source reproductible et sans date de vérification
ne doit pas entrer dans la documentation.

Par défaut, tout est en lecture seule. Ne pas déployer, redémarrer un service,
modifier la configuration du serveur ou écrire hors du dépôt documentaire sans
demande explicite. La publication du site et la vérification des journaux ont
leurs propres Skills ; cette méthode s'arrête à `docs/`.

## 1. Cadrer avant d'écrire

```bash
cd <racine_systeme>
ls -la
py -3 --version
```

Identifier et noter :

- le point d'entrée de la passerelle et le port d'écoute ;
- le dossier des pages servies et celui des tests ;
- la commande de test réellement utilisable ;
- l'emplacement des secrets (présence seulement, jamais le contenu) ;
- les documents déjà présents, pour ne pas les dupliquer.

Sur Windows, utiliser `py -3` : l'alias `python` peut renvoyer l'erreur du
Microsoft Store. Vérifier l'interpréteur avant toute affirmation de version.

## 2. Extraire les routes, alias compris

```bash
py -3 scripts/inventorier_routes.py <passerelle.py> \
  --doc <docs/API_*.md> [--json]
```

Le script analyse l'AST, sans démarrer le serveur :

- il détecte la variable affectée depuis `.path` (par défaut `chemin`) ;
- il lit les comparaisons `chemin in [...]`, `chemin == "..."` et les `or` ;
- il compte chaque motif unique par méthode (`GET`, `POST`, etc.) ;
- il vérifie la couverture d'un ou plusieurs Markdown via les jetons en code
  inline, requête et ancre retirées.

Sortie attendue : `routes uniques`, détail par méthode, `routes absentes du
doc`, puis `RESULT OK` ou `RESULT FAIL`. Codes : `0` succès, `1` couverture
incomplète ou aucune route, `2` entrée illisible.

Ne jamais déduire une URL publique du nom de fichier : une page servie par
`/livre-blanc` peut s'appeler `livre_blanc_almizan.html`. Seule la table de
routage fait foi.

Si le total diffère d'une mesure antérieure, expliquer l'écart par un ajout ou
un retrait réel de route, puis mettre à jour le document. Ne pas modifier le
nombre attendu pour faire passer le contrôle.

## 3. Exécuter les tests avant de rédiger

```bash
py -3 -m unittest <module_de_test> -v
```

Lire la trace complète, pas seulement le nombre d'échecs. Classer chaque
échec avant de corriger :

| Symptôme | Cause fréquente | Correction minimale |
| :--- | :--- | :--- |
| `UnboundLocalError: cannot access local variable 'asdict'` | import local dans une fonction qui utilise aussi l'import global | supprimer l'import local, garder l'import module |
| `NameError: name 'shutil' is not defined` | module utilisé mais non importé | ajouter l'import au niveau module |
| test d'authentification qui n'échoue pas | branche qui accepte toute requête si une session serveur existe | supprimer la branche, exiger un jeton |
| `TypeError` sur un mot-clé | `code=` au lieu de `statut_code=` | aligner sur la signature réelle |

Corriger la source, pas le test. Relancer la suite complète. Une suite verte
est la condition d'entrée de la rédaction. Ne pas documenter un comportement
observé seulement dans un test rouge.

## 4. Rédiger quatre documents

| Document | Contenu | Public |
| :--- | :--- | :--- |
| `docs/README.md` | index, démarrage rapide, règle de vérité, état de rédaction | tout développeur |
| `docs/ARCHITECTURE_ET_DEVELOPPEMENT.md` | cartographie, installation, tests, conventions, dette | développeur |
| `docs/API_*.md` | toutes les routes et alias, charges utiles, auth, erreurs, signature | intégrateur |
| `docs/EXPLOITATION_*.md` | topologie, secrets, service, reverse proxy, sauvegarde, rollback | exploitation |

Règles de rédaction :

- une ligne par route, alias dans la même ligne ou la colonne voisine ;
- un exemple par famille de route, avec une réponse réelle ou clairement
  étiquetée comme illustrative ;
- aucune valeur numérique recopiée sans source et sans date ;
- les limites (matériel absent, référentiel visé non certifié, absence de
  garantie financière) figurent dans le document, pas seulement dans un
  avertissement oral.

## 5. Valider la documentation

```bash
py -3 scripts/verifier_doc.py --gateway <passerelle.py> \
  --docs <dossier_docs> --root <racine_systeme>
```

Contrôles bloquants :

- fences de code équilibrées ;
- liens Markdown locaux résolus (relatifs au document ou à `--root`) ;
- blocs Python compilables (`--skip-python` pour désactiver) ;
- toutes les routes de la passerelle présentes dans le corpus
  (`--allow-missing` pour tolérer un manque pendant une rédaction partielle).

Sortie attendue : `routes uniques`, `routes absentes du corpus: 0`, une ligne
par document, puis `RESULT PASS`. Codes : `0` succès, `1` au moins un défaut,
`2` entrée ou argument invalide.

Relancer les tests après toute correction de code. Pour une vérification en
direct, rester en lecture seule et comparer les octets avec prudence : un
serveur qui lit les fichiers en mode texte UTF-8 renvoie du LF alors que le
fichier Windows contient du CRLF. Comparer les SHA-256 après normalisation des
fins de ligne, et écrire dans le rapport « identique hors CRLF→LF », pas
« identique octet par octet ».

## 6. Rapport final

| Contrôle | Commande ou source | Attendu | Mesuré | Conclusion |
| :--- | :--- | :--- | :--- | :--- |
| Routes uniques | `inventorier_routes.py` | N stable et expliqué | | |
| Couverture | `--doc` ou `verifier_doc.py` | 0 absente | | |
| Tests | `unittest -v` | N/N OK | | |
| Liens locaux | `verifier_doc.py` | 0 absent | | |
| Fences / Python | `verifier_doc.py` | équilibrées, compilables | | |
| Affirmations | étiquetage | chaque claim tracée | | |
| Effets de bord | `git status` ou équivalent | aucun hors docs | | |

Distinguer explicitement « vérifié par exécution », « vérifié statiquement » et
« non déclenché ». Ne pas écrire « validé » pour un contrôle qui n'a pas tourné.
