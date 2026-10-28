# Cas vérifié : retrait du repli HMAC et fermeture par défaut (2026-10-28)

Ce document ne recopie **aucune valeur de secret** : uniquement des longueurs, des empreintes `sha256[:8]`, des chemins, des codes de sortie et des horodatages UTC. Il documente un cas réel pour calibrer le Skill, pas une procédure à rejouer sans relire l'état courant.

## 1. Déclencheur

L'archivage de `rotation-secret-systemd-vps-mizan` avait donné `RESULT PASS` (9 pass, 0 fail, 0 warn, 2 fichiers). Avant copie vers un dépôt **public**, un scan de secrets masqué a révélé que :

- la référence `preuves-webhooks-et-durcissement-2026-10-28.md:3` affirmait « ne contient **aucune valeur de secret** : uniquement longueurs, empreintes `sha256[:8]` » ;
- la ligne 11 du même fichier, la description et le corps du `SKILL.md` citaient pourtant la valeur de repli historique ;
- cette valeur était **encore active** dans le code : avant correction, `passerelle_api_vps_mizan.py` portait `os.environ.get("MIZAN_WEBHOOK_SECRET", "<valeur>")` (ligne 90 à l'époque), et `deploiement_vps/rotation_secret_webhooks.py` la conservait dans `SECRET_DEFAUT`.

Conséquence : si `MIZAN_WEBHOOK_SECRET` manquait, la passerelle signait les webhooks avec une valeur publiée. La QA statique ne couvre pas ce risque.

## 2. Décisions

| Horodatage | Décision |
| :--- | :--- |
| avant 02:56Z | Archiver ou non malgré la fuite : **pause d'archivage, retrait du repli d'abord** |
| avant 03:15Z | Comportement sans variable : **fail-closed, refus au démarrage** |

L'archivage n'a repris qu'après le retrait et l'assainissement du paquet.

## 3. Fichiers modifiés et empreintes

Empreintes relevées le 2026-10-28 (après les edits, avant archivage) et **revérifiées identiques** lors de la rédaction de ce Skill :

| Fichier (relatif à `ASTRO-Q°ODE_SYSTEME/`) | Octets | SHA-256 |
| :--- | ---: | :--- |
| `passerelle_api_vps_mizan.py` | 102 727 | `27781f6ad8bf52e893d15012230d5d069cfe5add8324293f75aedb499dc48462` |
| `orchestrateur_unifie_4_demarches.py` | 14 499 | `0d3b5726d9bfabbdadae7a066e1a56a36332fa6623bac7a3a77a534e421a8e18` |
| `deploiement_vps/rotation_secret_webhooks.py` | 13 391 | `dc936e8f6f9bf13a6e2b71c978f0208f08efab0e24a5bab747886e11c3cbb1eb` |
| `deploiement_vps/systemd/al-mizan-api-vps.service` | 721 | `3a39affee7e8473122519ee50abe338f6282999595e140315bf2fff9d7a4cca8` |
| `deploiement_vps/injecter_et_deployer.py` | 8 697 | `d3903be3df87aaa31d0ec220fa4ff04b3de105246e837bfbeeb5a33748cb0e6f` |
| `deploiement_vps/deploiement_automatique_ovh.py` | 9 896 | `3fb03117eb3c190660bac7f2d948b6d67a2d08c9d325b8a50e1a670f288a7b98` |
| `docs/EXPLOITATION_VPS.md` | 27 121 | `7cafac544ffe7f612d4f3fb30ac808d5358320719990f4eaaa6de77af5118694` |
| `tests/test_passerelle_api_vps.py` | 10 405 | `d9ffe26c8e6fccbbc5dc2bf69d98d7bb5a36e68d7b7bc11e5c11bc331d1bf6d7` |
| `tests/test_sas_biometrique_souverain.py` | 8 858 | `c021b43298002f721cf628fd5161b44613cdfe9eaa944e7916af9eba87a73b9e` |
| `tests/test_suite_complete.py` | 60 743 | `8c478e92d398e635814965dc55b9e98c8b590c62b255e42ac05b1f105ede9704` |

Si l'un de ces fichiers change, revérifier le comportement avant de citer ce cas.

## 4. Ce qui a changé

1. **Accesseur** `secret_webhooks_requis()` remplace la constante de module. Il lit la variable, la `strip`, lève `RuntimeError` si vide, et rend `bytes`. Appelé à la signature (`passerelle_api_vps_mizan.py:378`) et au démarrage (`:2115`).
2. **Démarrage** : `SystemExit("[ERREUR] Démarrage refusé : ...")` avant la création du serveur.
3. **Orchestrateur** : import de la fonction, appel à la place de la constante pour la signature témoin.
4. **Outil de rotation** : `EMPREINTE_SECRET_DEFAUT_SHA8 = "ee9faafa"` remplace la valeur ; `SECRET_DEFAUT` compare `SECRET_SHA8`.
5. **Template d'unité** : `EnvironmentFile=` du secret webhooks sans `-` ; celle de la clé d'API reste optionnelle avec `-`.
6. **Deux générateurs** (`injecter_et_deployer.py`, `deploiement_automatique_ovh.py`) : même ligne rendue obligatoire dans leur copie embarquée.
7. **Tests** : `tests/test_passerelle_api_vps.py`, `tests/test_sas_biometrique_souverain.py` et `tests/test_suite_complete.py` posent un secret propre au module via `os.environ.setdefault`, avant l'import du service.
8. **Documentation** : `docs/EXPLOITATION_VPS.md` §5 et §10 remplacent la valeur par le sha8 et précisent « non déployé ».

## 5. Preuves observées

Compilation et accesseur (sortie masquée, aucune valeur) :

```text
COMPILE_OK
ABSENT: REFUS -> MIZAN_WEBHOOK_SECRET absent : signature des webhooks impossible.
PRESENT: type= bytes len= 64
```

Démarrage sans variable :

```text
[ERREUR] Démarrage refusé : MIZAN_WEBHOOK_SECRET absent : signature des webhooks impossible.
EXIT=1
```

Tests après ajout des secrets de test :

| Périmètre | Résultat |
| :--- | :--- |
| Passerelle | 11 tests OK |
| Sas biométrique | 5 tests OK |
| Comptes + qubit + site | 17 tests OK |
| `test_30` de la suite complète | 1 test OK |

Paquet `rotation-secret-systemd-vps-mizan` assaini : `RESULT PASS` 9/0/0, description 958 caractères, corps 180 lignes, 0 littéral restant, sha8 `ee9faafa` seul conservé. Archivage : commit `b07ea6e`, parent `d991535`, 2 fichiers, 358 insertions ; blobs distants `2ad764da` et `0a7d49cb` identiques à la source.

## 6. Écarts et erreurs constatés

- **`NameError: name 'os' is not defined`** dans `tests/test_sas_biometrique_souverain.py` juste après l'ajout du `setdefault` : le module n'importait pas `os`. Corrigé par un `import os`.
- **Le template seul ne suffit pas** : le template a été rendu obligatoire, mais la vérification suivante montrait encore `EnvironmentFile=-...mizan_webhook_secret.env` dans les **deux générateurs** ; ils ont dû être alignés à leur tour.
- **La phrase « aucune valeur de secret »** était fausse dans la référence et dans la description du Skill. Le validateur ne la contrôle pas ; seule une lecture ligne par ligne l'a établie.
- **Le 500 n'a pas été journalisé** dans cette session. Le code déduit le comportement : l'accesseur lève, la route `except Exception` répond 500. À ne pas présenter comme une observation.
- **Un module sans route émettrice passe sans secret** : les 17 tests comptes/qubit/site ont passé sans `MIZAN_WEBHOOK_SECRET`. Ce n'est pas une preuve de couverture.

## 7. Limites du cas

- **Non déployé** : la production a conservé son unité avec `-` et son processus a continué d'utiliser l'ancien repli jusqu'à un déploiement, qui exige une autorisation distincte.
- L'unité **live** gardait une ligne `Environment=MIZAN_WEBHOOK_SECRET=` (644) en plus du fichier d'environnement ; la migration de l'unité live n'était pas incluse.
- L'ancienne valeur reste dans les transcripts et les sauvegardes `.bak-20261028T003853Z` ; elle a été révoquée, pas effacée.
- Les valeurs de test (`secret_test_webhooks_*`) sont des fixtures, sans rapport avec la production.
- Le sha8 `ee9faafa` est un indicateur stable, pas une preuve de révocation.
