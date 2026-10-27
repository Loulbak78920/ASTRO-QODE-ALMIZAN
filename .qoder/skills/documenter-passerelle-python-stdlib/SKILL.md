---
name: documenter-passerelle-python-stdlib
description: "Documenter ou mettre à jour la documentation technique d'une passerelle HTTP Python sans framework (http.server, urllib, json) : inventorier le dépôt et les points d'entrée, extraire exhaustivement les routes et alias, exécuter les tests réels, corriger à la source les défauts révélés, rédiger index, architecture, référence API et runbook, puis valider liens, blocs de code, couverture des routes et étiquetage honnête opérationnel/simulé/spécifié. Utiliser pour documenter une API Python stdlib, vérifier qu'une documentation ne décrit pas un comportement faux, couvrir toutes les routes d'une passerelle, auditer docs/ après un changement de routeur, ou préparer une référence API et un runbook sans framework. English triggers: document Python stdlib HTTP gateway, verify API docs against routes, route coverage check, docs/ audit."
---

# Documenter une passerelle Python stdlib

## Portée

Produire ou maintenir la documentation technique d'une passerelle HTTP écrite
avec la bibliothèque standard (`http.server`, `urllib`, `json`), dans un
dossier `docs/` : index, architecture, référence API, exploitation.

Inclus : inventaire du dépôt, extraction des routes, exécution des tests,
correction minimale des défauts révélés, rédaction et validation des documents.

Exclu : déploiement, redémarrage de service, configuration du reverse proxy,
publication du site, analyse des journaux. Ces tâches relèvent de
`deployer-site-sans-dol-vps` et `verifier-journaux-nginx-vps`. Ce Skill
s'arrête à `docs/` et reste en lecture seule sur le reste du dépôt, sauf
correction de code explicitement demandée.

## Règle de vérité

Chaque affirmation publiée reçoit une étiquette : `opérationnel` (observé),
`simulé` (émulation logicielle), `spécifié` (paramètre de conception, non
certifié) ou `déclaré · non vérifié` (adresse, partenariat, liquidité).

Ordre de preuve : sortie de test ou de requête > code du routeur > réponse HTTP
en lecture seule > documentation existante. Un chiffre sans source et sans date
de vérification n'entre pas dans le document.

## 1. Cadrer

```bash
cd <racine_systeme>
ls -la
py -3 --version
```

Noter le point d'entrée, le port, le dossier des pages servies, la commande de
test et la présence des secrets (jamais leur contenu). Sur Windows, utiliser
`py -3` : l'alias `python` peut renvoyer l'erreur du Microsoft Store.

Lire les documents existants avant d'en créer un nouveau. Ne pas dupliquer un
runbook ou un livre blanc déjà présent.

## 2. Extraire les routes

```bash
py -3 <skill>/scripts/inventorier_routes.py <passerelle.py> \
  --doc <docs/API_*.md> [--json] [--allow-missing]
```

Le script analyse l'AST sans démarrer le serveur. Il détecte la variable issue
de `.path`, lit `chemin in [...]`, `chemin == "..."` et les `or`, compte chaque
motif unique par méthode et vérifie la couverture des Markdown.

Codes de sortie : `0` succès, `1` couverture incomplète ou aucune route, `2`
entrée illisible. Sortie attendue : `routes uniques`, détail par méthode,
`routes absentes du doc`, `RESULT OK`.

Ne jamais déduire une URL du nom de fichier : `/livre-blanc` peut servir
`livre_blanc_almizan.html`. Seule la table de routage fait foi.

Un écart de total avec une mesure antérieure s'explique par un ajout ou un
retrait réel, daté. Ne pas ajuster le nombre attendu pour faire passer le
contrôle ; vérifier si une route a été ajoutée (par exemple un favicon).

## 3. Exécuter les tests avant de rédiger

```bash
py -3 -m unittest <module_de_test> -v
```

Lire la trace complète. Corriger la source, jamais l'attendu du test. Relancer
la suite complète. Une suite verte est la condition d'entrée de la rédaction.

Pièges vérifiés, détaillés dans
[`references/methode-verification.md`](references/methode-verification.md) :

- import local qui masque un import global (`asdict`) et provoque
  `UnboundLocalError` dans toute la fonction ;
- module utilisé mais non importé (`shutil`) ;
- branche d'authentification qui accepte toute requête si une session serveur
  existe ;
- mot-clé d'erreur erroné (`code=` au lieu de `statut_code=`) ;
- comparaison octet par octet qui échoue à cause des CRLF alors que le contenu
  est identique après normalisation.

## 4. Rédiger les quatre documents

Documents à produire dans le dossier `docs/` du système cible :

| Document | Contenu | Public |
| :--- | :--- | :--- |
| `README.md` | index, démarrage rapide, règle de vérité, état | tout développeur |
| `ARCHITECTURE_ET_DEVELOPPEMENT.md` | cartographie, installation, tests, conventions, dette | développeur |
| `API_<sujet>.md` | toutes les routes et alias, charges utiles, auth, erreurs, signature | intégrateur |
| `EXPLOITATION_<sujet>.md` | topologie, secrets, service, proxy, sauvegarde, rollback | exploitation |

Règles : une ligne par route avec ses alias ; un exemple par famille, réel ou
clairement illustratif ; aucune valeur recopiée sans source ni date ; les
limites matérielles et réglementaires inscrites dans le document.

## 5. Valider

```bash
py -3 <skill>/scripts/verifier_doc.py --gateway <passerelle.py> \
  --docs <dossier_docs> --root <racine_systeme> [--skip-python] [--allow-missing]
```

Contrôles bloquants : fences équilibrées, liens locaux résolus, blocs Python
compilables, toutes les routes présentes. Sortie attendue : `routes absentes du
corpus: 0`, une ligne par document, `RESULT PASS`. Codes : `0` succès, `1`
défaut, `2` argument ou entrée invalide.

Relancer les tests après toute correction de code. En vérification directe,
rester en lecture seule et comparer les SHA-256 après normalisation CRLF→LF,
puis écrire « identique hors CRLF→LF », pas « identique octet par octet ».

## 6. Rapporter

| Contrôle | Source | Attendu | Mesuré | Conclusion |
| :--- | :--- | :--- | :--- | :--- |
| Routes uniques | `inventorier_routes.py` | total stable et expliqué | | |
| Couverture | `--doc` ou `verifier_doc.py` | 0 absente | | |
| Tests | `unittest -v` | N/N OK | | |
| Liens / fences / Python | `verifier_doc.py` | 0 absent, équilibré, compilable | | |
| Affirmations | étiquetage | chaque claim tracée | | |
| Effets de bord | `git status` ou équivalent | aucun hors docs | | |

Distinguer « vérifié par exécution », « vérifié statiquement » et « non
déclenché ». Ne pas écrire « validé » pour un contrôle qui n'a pas tourné.

## Ressources

- [`scripts/inventorier_routes.py`](scripts/inventorier_routes.py) — extraction
  AST, alias, couverture documentaire, sortie JSON.
- [`scripts/verifier_doc.py`](scripts/verifier_doc.py) — fences, liens, blocs
  Python, couverture des routes.
- [`references/methode-verification.md`](references/methode-verification.md) —
  séquence complète, commandes et pièges.
- [`references/cas-astro-qode-2026-10-27.md`](references/cas-astro-qode-2026-10-27.md)
  — cas réel : 4 défauts, 4 documents, 94 puis 95 routes, limites de preuve.

Après création ou mise à jour du paquet, lancer `skill-file-qa` pour la
validation statique et consigner les empreintes réelles.
