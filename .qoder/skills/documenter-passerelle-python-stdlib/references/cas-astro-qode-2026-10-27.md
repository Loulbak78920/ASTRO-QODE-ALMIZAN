# Cas vérifié — documentation ASTRO-Q°ODE × Al-Mizan

## Provenance

| Champ | Valeur |
| :--- | :--- |
| Session source | `55f63550-7c8d-4f9e-b0a9-e73686cc2765` |
| Titre | « Mettre à jour le site web » |
| Fenêtre lue | 20 derniers tours, `hasMoreBefore: true` (historique antérieur non lu) |
| État au moment de la lecture | `runtimeState: cold`, `activeTurnId: null`, `revision: 0` |
| Demande de documentation | 2026-10-27T01:37:39.827Z (UTC) |
| Portée | `ASTRO-Q°ODE_SYSTEME/`, documentation dans `docs/` |

Les horodatages de messages sont en UTC. Les affirmations ci-dessous sont
classées : **vérifié dans la session** (sortie d'outil citée), **revérifié lors
de la création du Skill** (commande relancée le 2026-10-27), ou **non revérifié**.

## Pipeline observé

| Étape | Action réelle | Résultat |
| :--- | :--- | :--- |
| 1 | Inventaire du dépôt, des points d'entrée, de `web_cloud/`, `tests/`, `bibliotheques/`, du dossier de secrets (présence) | périmètre établi, `git` absent à la racine |
| 2 | Extraction des routes par recherche `chemin in [` et lecture de `do_GET` / `do_POST` | motifs et alias recensés |
| 3 | Exécution de `py -3 -m unittest tests.test_passerelle_api_vps -v` | 8 tests, 1 échec, 1 erreur |
| 4 | Lecture des traces, correction minimale de la passerelle, relance | 8/8 OK |
| 5 | Rédaction de quatre documents dans `docs/` | README, architecture, API, exploitation |
| 6 | Vérification des fences, liens, compilation et couverture | 94 routes uniques, 0 absente, 0 lien cassé |
| 7 | Mise à jour du README du dépôt vers l'index `docs/` | pointeur ajouté |
| 8 | Plus tard : ajout de `/favicon.ico` et de son test | 10/10, documentation API mise à jour |

## Échecs initiaux et défauts réels

Sortie de test **vérifiée dans la session** :

- `FAIL: test_06_securite_commandes_authentification` —
  `AssertionError: HTTPError not raised` : `POST /api/v1/commande` répondait 200
  sans jeton.
- `ERROR: test_05_inscription_et_liste_webhooks` —
  `UnboundLocalError: cannot access local variable 'asdict'` à la ligne 587 de
  la passerelle, causé par un `from dataclasses import asdict` local à la ligne
  484 qui rendait `asdict` local à tout `do_GET`.

Défauts corrigés, **vérifiés dans la session** :

| Défaut | Effet | Correction |
| :--- | :--- | :--- |
| import local `asdict` dans `do_GET` | `UnboundLocalError` sur `/api/v1/webhooks` et `/api/v1/unifie` | suppression de l'import local |
| `shutil` utilisé pour `/video` mais non importé | `NameError` sur la route vidéo | `import shutil` au niveau module |
| authentification acceptant toute requête si une session souveraine existait côté serveur | contournement de l'authentification | suppression de la branche sans jeton |
| `code=` au lieu de `statut_code=` sur `/api/v1/audit/paiements` | `TypeError` sur les réponses d'erreur | mot-clé aligné |

Après correction : `Ran 8 tests ... OK` — **vérifié dans la session**.

## Documents produits

Mesures **vérifiées dans la session** au moment de la rédaction :

| Document | Lignes | Fences | Liens cassés |
| :--- | ---: | ---: | ---: |
| `docs/README.md` | 70 | 4 | 0 |
| `docs/ARCHITECTURE_ET_DEVELOPPEMENT.md` | 288 | 10 | 0 |
| `docs/API_PASSERELLE_VPS.md` | 338 puis 340 | 32 | 0 |
| `docs/EXPLOITATION_VPS.md` | 331 | 32 | 0 |

Compilation des exemples : `OK`. Couverture : **94 routes uniques, 0 absente**.

Règle de vérité inscrite dans l'index : toute affirmation publiée doit être
classée `opérationnelle`, `simulée` ou `spécifiée (non certifiée)`. Le serveur
est un VPS CPU ; aucun QPU, GPU de calcul ou capteur cryogénique physique n'est
présent.

## Revérification lors de la création du Skill (2026-10-27)

Commandes relancées sur les artefacts réels :

```bash
py -3 scripts/inventorier_routes.py <passerelle.py> --doc <docs/API_PASSERELLE_VPS.md>
py -3 scripts/verifier_doc.py --gateway <passerelle.py> --docs <docs> --root <racine_systeme>
```

Résultats **revérifiés** :

- `95` routes uniques : `GET 74`, `POST 21` ;
- `0` route absente du corpus ;
- `0` lien local absent ;
- fences `32 / 10 / 32 / 4`, blocs Python compilables ;
- `RESULT PASS`, code de sortie `0`.

Écart expliqué : la session mesurait `94` routes avant l'ajout ultérieur de
`/favicon.ico`. La route a ensuite été ajoutée (200 `image/x-icon`, repli 204,
asset de 8 377 octets, tests 10/10) et le tableau API mis à jour. `94 + 1 = 95`
— la différence est un ajout réel, pas une erreur d'extraction.

## Limites de cette preuve

- La fenêtre lue est partielle (`hasMoreBefore: true`) ; les tours antérieurs à
  01:17 UTC n'ont pas été examinés.
- Les numéros de ligne cités sont ceux du moment de la session ; le fichier a
  ensuite changé (ajout du favicon), donc ils peuvent avoir dérivé.
- Les empreintes de déploiement (`122acc22…`, `472dad9d…`, favicon `2f0aa19c…`)
  sont historiques et n'ont pas été revérifiées ici ; ce Skill ne redéploie pas.
- Les documents actuels peuvent différer de la version rédigée en session :
  toujours relancer les scripts avant de citer un compteur.
- Aucune correction utilisateur de la méthode documentaire n'est visible dans
  la fenêtre ; les demandes suivantes portent sur le déploiement, les journaux
  et le favicon.

## Règles réutilisables

1. Lire le code et exécuter les tests avant d'écrire une ligne de doc.
2. Un test rouge est une découverte : corriger la source, pas l'attendu.
3. Compter les routes par extraction, alias compris, jamais de mémoire.
4. Un écart de compteur s'explique par un changement réel, daté.
5. Séparer `docs/` (ce Skill) de la publication du site et des journaux, qui
   ont leurs propres Skills.
