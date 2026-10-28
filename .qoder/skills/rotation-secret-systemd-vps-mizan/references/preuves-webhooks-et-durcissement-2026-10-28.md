# Cas vérifié : rotation de `MIZAN_WEBHOOK_SECRET` et durcissement des artefacts (2026-10-28)

Rotation HMAC exécutée en production sur `www.al-mizan.world`, puis retrait de l'ancienne valeur des artefacts de déploiement. Ce document ne contient **aucune valeur de secret** : uniquement longueurs, empreintes `sha256[:8]`, codes HTTP, chemins, modes et horodatages UTC.

Les chemins projet cités ici sont relatifs à `ASTRO-Q°ODE_SYSTEME/` (eux-mêmes relatifs à la racine du dépôt `IMAM8MAHDI`).

## Contexte

- Service : `al-mizan-api-vps` (systemd), port 8095, exposé via nginx.
- Variable : `MIZAN_WEBHOOK_SECRET`, utilisée pour signer en HMAC-SHA256 les webhooks sortants.
- Valeur de repli codée en dur avant rotation : empreinte sha8 `ee9faafa` (révoquée depuis, puis retirée du code le 2026-10-28 ; valeur non reportée ici).
- Outil : `deploiement_vps/rotation_secret_webhooks.py` (plan par défaut, `--verifier` en lecture seule, `--appliquer` avec retour arrière).
- Autorisation : demandée et accordée pour ce secret uniquement ; la rotation de la clé Bearer a fait l'objet d'une autorisation distincte.

## Chronologie (UTC)

| Heure | Événement |
| :--- | :--- |
| 00:27:36 | demande de rotation de `MIZAN_VPS_API_KEY` (secret distinct) |
| 00:31:23 | rotation de la clé Bearer (`sha8 97986987`), hors périmètre de ce document |
| 00:34:56 | demande de rotation de `MIZAN_WEBHOOK_SECRET` |
| 00:38:53 | `--appliquer` : préflight, sauvegarde, réécriture, redémarrage, contrôles |
| 00:40:57 | l'utilisateur redemande la rotation de la clé Bearer ; `--verifier` montre qu'elle est déjà faite ; aucune seconde rotation |

## État initial observé

Relevé `--verifier` avant rotation :

| Clé | Valeur |
| :--- | :--- |
| `ETAT` | `active` |
| `SECRET_LEN` | 24 |
| `SECRET_SHA8` | `ee9faafa` |
| `SECRET_DEFAUT` | `OUI` |
| `LIGNES_SECRET` | 1 |
| `ENV_FILE` | `ABSENT` |
| `ABONNES` | 0 |
| `SUDO` | `OK` |
| `SECRET_LOCAL` | `ABSENTE` |
| `RESULT` / rc | `A REVOIR` / 1 |

`A REVOIR` est ici l'état normal d'un secret encore égal à la valeur de repli : l'outil signale que la condition de sortie n'est pas remplie. Ce n'est pas une erreur d'exécution.

Abonnés webhook vus par la passerelle :

```json
{"succes":true,"total_webhooks_inscrits":0,"abonnements":[],"derniers_evenements_emis":[]}
```

## Application (`--appliquer`, rc 0, 00:38:53Z)

| Élément | Valeur observée |
| :--- | :--- |
| abonnés au moment du préflight | 0 |
| nouveau secret | 64 caractères URL-safe |
| `sha256[:8]` nouveau | `920cce39` |
| sauvegarde d'unité | `/etc/systemd/system/al-mizan-api-vps.service.bak-20261028T003853Z` |
| fichier d'environnement | `/opt/al-mizan/…/secrets/mizan_webhook_secret.env`, 86 octets, `600 ubuntu:ubuntu` |
| secret local | `secrets/mizan_webhook_secret.key`, 64 octets |
| ACL locale (Windows) | héritée : Système, Administrateurs, Administrateur |
| service après `restart` | `active` |

Contrôles après redémarrage :

| Contrôle | Valeur |
| :--- | :--- |
| `SECRET_LEN` / `SECRET_SHA8` | 64 / `920cce39` |
| `SECRET_DEFAUT` | `NON` |
| `LIGNES_SECRET` | 1 |
| `ENV_FILE` | `PRESENT` |
| `ABONNES` | 0 |
| `SECRET_LOCAL` | `SYNCHRONISEE (sha8 920cce39)` |
| `RESULT` / rc | `OK` / 0 |
| `GET /api/v1/sante` | 200 |
| `/`, `/oeuvre-universelle`, `/oeuvre-universelle/ar`, `/api/v1/comptes/statut_public` | 200 |
| sonde de la clé Bearer | 400, `sha8 97986987` (inchangée) |

L'extrait de journal consulté après redémarrage ne contenait aucune ligne d'erreur. La preuve du nouveau secret est **environnementale** (`sha8` + `SECRET_DEFAUT NON`) : aucune route ne valide une signature entrante, donc aucun code HTTP ne peut la prouver.

## Durcissement des artefacts

Sans ces changements, le déploiement suivant aurait réécrit l'ancienne valeur.

| Artefact | Changement vérifié |
| :--- | :--- |
| `deploiement_vps/systemd/al-mizan-api-vps.service:11-12` | deux `EnvironmentFile=-…/secrets/*.env`, aucune valeur |
| `deploiement_vps/demarrer_passerelle_vps.sh:16-24` | plus de `${VAR:-valeur}` ; environnement, sinon `secrets/*.key`, sinon routes fermées |
| `deploiement_vps/injecter_et_deployer.py:56` | `secret_webhooks()` lit `secrets/mizan_webhook_secret.key` |
| `deploiement_vps/injecter_et_deployer.py:168-169` | unité générée : `{CLE_API}` / `{SECRET_HOOKS}`, pas de littéral |
| `deploiement_vps/deploiement_automatique_ovh.py:62` | même helper `secret_webhooks()` |
| `deploiement_vps/deploiement_automatique_ovh.py:189-190` | idem, placeholders |
| `docs/EXPLOITATION_VPS.md:447-451` | outil, procédure et rotation datée documentés |

Preuve de parité des deux générateurs avec le service, exécutée sans afficher la valeur (2026-10-28, `py -3 -B`, rc 0) :

```text
A 64 920cce39
B 64 920cce39
```

## Défauts résiduels et limites

- ~~`passerelle_api_vps_mizan.py:90` retombait encore sur la valeur de repli si la variable manquait.~~ Résolu le 2026-10-28 en local (voir « Retrait du repli » ci-dessous) : accesseur à échec fermé, aucune valeur dans le code. Lot non déployé en production à la date de rédaction.
- ~~L'unité **live** porte toujours une ligne `Environment=MIZAN_WEBHOOK_SECRET=…`~~ : état observé à 00:47:05Z, dépassé par la migration `EnvironmentFile=` de 00:52:20Z (`ENVFILE=2`, `LEGACY=0`, sauvegarde `.bak-20261028T005220Z`).
- L'unité **live** garde `EnvironmentFile=-…/mizan_webhook_secret.env` avec tiret ; le template du dépôt est passé au 2026-10-28 à un fichier obligatoire, mais ce durcissement n'est pas déployé.
- Les abonnements webhook sont tenus en mémoire et disparaissent au redémarrage. `0 abonné` prouve qu'aucun abonné n'était enregistré dans cette instance, pas qu'aucun client externe ne détient l'ancien secret.
- Aucune preuve qu'un intégrateur externe ait été prévenu : il n'y en avait aucun d'inscrit.
- La rotation ne retire pas l'ancienne valeur des transcripts et sauvegardes déjà produits ; elle la révoque seulement.
- Le `.bak-20261028T003853Z` de l'unité contient l'ancienne valeur, en 644 : elle est révoquée, mais le fichier ne doit pas être déplacé ni publié.
- `py_compile` a laissé des `.pyc` (`rotation_cle_api_vps`, `rotation_secret_webhooks`) malgré `-B` ; ils ont été supprimés. `deploiement_vps/__pycache__` contient encore deux `.pyc` antérieurs (`charger_credentials_ovh`, `deploy_tetrade_evm`), non créés par cette rotation.
- La documentation annonçait d'abord un 200 attendu avec le nouveau jeton ; le contrôle réel est 400 (jeton accepté, action inconnue). L'écart a été corrigé dans `docs/EXPLOITATION_VPS.md` §10.

## Retrait du repli (2026-10-28, local, non déployé)

Décision : **échec fermé** — aucune valeur de repli, refus de démarrer sans `MIZAN_WEBHOOK_SECRET`. Déclenchée par la préparation d'archivage public du présent Skill : la valeur de repli, encore active dans le code, aurait été publiée telle quelle.

Modifications, toutes locales (`ASTRO-Q°ODE_SYSTEME/`) :

| Fichier | Changement |
| :--- | :--- |
| `passerelle_api_vps_mizan.py` | `secret_webhooks_requis()` remplace la constante à valeur de repli ; appelée à la signature et avant le démarrage (`SystemExit` + `Démarrage refusé`) |
| `orchestrateur_unifie_4_demarches.py` | importe et utilise `secret_webhooks_requis()` pour la signature témoin |
| `deploiement_vps/rotation_secret_webhooks.py` | `SECRET_DEFAUT` (valeur littérale) remplacé par `EMPREINTE_SECRET_DEFAUT_SHA8 = "ee9faafa"`, comparaison faite sur `SECRET_SHA8` du processus ; constante `LIGNE_ENVFILE` non utilisée supprimée |
| `deploiement_vps/systemd/al-mizan-api-vps.service` | `EnvironmentFile=` du secret webhooks sans `-` (obligatoire) ; celui de la clé d'API reste optionnel |
| `deploiement_vps/injecter_et_deployer.py`, `deploiement_vps/deploiement_automatique_ovh.py` | unité embarquée alignée : `EnvironmentFile=` du secret webhooks sans `-`, sinon un déploiement réintroduirait le démarrage tolérant |
| `docs/EXPLOITATION_VPS.md` | §5 et §10 : repli retiré, échec fermé, lot non déployé |
| `tests/test_passerelle_api_vps.py`, `tests/test_sas_biometrique_souverain.py`, `tests/test_suite_complete.py` | secret de test propre à chaque module (`os.environ.setdefault`), les routes émettrices signent désormais réellement |

Contrôles exécutés :

```text
env -u MIZAN_WEBHOOK_SECRET py -3 passerelle_api_vps_mizan.py --port 8199
  -> [ERREUR] Démarrage refusé : MIZAN_WEBHOOK_SECRET absent ... ; EXIT=1
secret_webhooks_requis() sans variable        -> RuntimeError
secret_webhooks_requis() avec 64 caractères   -> bytes, longueur 64
tests.test_passerelle_api_vps                 -> 11 tests, OK
tests.test_sas_biometrique_souverain          -> 5 tests, OK
tests.test_comptes_http_mizan + test_qubit_http_mizan + test_site_public_mizan -> 17 tests, OK
test_suite_complete ... test_30_passerelle_api_rest_et_webhooks_vps -> 1 test, OK
```

Empreintes `SHA-256` complètes au 2026-10-28T03:16:51Z :

| Fichier | Octets | SHA-256 |
| :--- | ---: | :--- |
| `passerelle_api_vps_mizan.py` | 102 727 | `27781f6ad8bf52e893d15012230d5d069cfe5add8324293f75aedb499dc48462` |
| `orchestrateur_unifie_4_demarches.py` | 14 499 | `0d3b5726d9bfabbdadae7a066e1a56a36332fa6623bac7a3a77a534e421a8e18` |
| `deploiement_vps/rotation_secret_webhooks.py` | 13 391 | `dc936e8f6f9bf13a6e2b71c978f0208f08efab0e24a5bab747886e11c3cbb1eb` |
| `deploiement_vps/systemd/al-mizan-api-vps.service` | 721 | `3a39affee7e8473122519ee50abe338f6282999595e140315bf2fff9d7a4cca8` |
| `deploiement_vps/injecter_et_deployer.py` | 8 697 | `d3903be3df87aaa31d0ec220fa4ff04b3de105246e837bfbeeb5a33748cb0e6f` |
| `deploiement_vps/deploiement_automatique_ovh.py` | 9 896 | `3fb03117eb3c190660bac7f2d948b6d67a2d08c9d325b8a50e1a670f288a7b98` |
| `docs/EXPLOITATION_VPS.md` | 27 121 | `7cafac544ffe7f612d4f3fb30ac808d5358320719990f4eaaa6de77af5118694` |

Limites à énoncer : la production n'a reçu ni le code ni le template ; tant qu'elle n'est pas redéployée, son processus courant conserve l'ancien comportement (repli présent dans le fichier déployé). Le retrait du repli ne révoque rien de plus : le secret tourné le 2026-10-28T00:38:53Z reste le secret en service.

## Reproductibilité

SHA-256 calculés le 2026-10-28T00:47:05Z sur les fichiers cités — instantané **antérieur** au retrait du repli (03:16:51Z) ; pour l'état courant de `rotation_secret_webhooks.py`, du template d'unité, des deux générateurs, de `passerelle_api_vps_mizan.py` et de `docs/EXPLOITATION_VPS.md`, utiliser la table de la section précédente :

| Fichier | Octets | SHA-256 |
| :--- | ---: | :--- |
| `deploiement_vps/rotation_secret_webhooks.py` | 12 215 | `fd26fa793662b1aaf4527616ab425dbc52b1a5ee708268e7b332ccd3bbe2d409` |
| `deploiement_vps/systemd/al-mizan-api-vps.service` | 724 | `a740944b0885e4ad5b82859649402548f0525776c4fe3c5fd0d3e5320ce4359c` |
| `deploiement_vps/demarrer_passerelle_vps.sh` | 1 225 | `e9fabdc1c11084d8c1c0df65561e72e79bf6e54efef2dfb88e8260e944ffa279` |
| `deploiement_vps/injecter_et_deployer.py` | 7 623 | `b1fbcf212d7b3f0465e45a353af83ae6103bd70a9b0b9a3c8fb181832cc1d922` |
| `deploiement_vps/deploiement_automatique_ovh.py` | 8 752 | `0809cbd76da964521adebe7eb23a27a43e2f80101ca684d4ec782e72e07be0fc` |
| `passerelle_api_vps_mizan.py` | 102 141 | `7944197bb683a60a1f986d1bbaad1bee82539cd93f9f333edb44c7fee5fa86fd` |
| `docs/EXPLOITATION_VPS.md` | 25 495 | `4721dba3feb3d5ea0441f8afac7687157aafc372e2c92907ab38fbc9af8796d8` |

Si l'un de ces fichiers change, revérifier le nombre de lignes `Environment=`, la présence d'un repli et la parité des helpers avant de se fier à ce cas.

## Assainissement

Aucune valeur n'est reportée ici, y compris sous forme d'extrait. Les seules données conservées sont : longueurs (24, 64, 86), empreintes `sha256[:8]`, codes HTTP, chemins, modes, propriétaires et horodatages.
