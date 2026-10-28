---
name: rotation-cle-api-service-systemd
description: "Faire tourner un secret porté par Environment= ou EnvironmentFile= d'une unité systemd (clé d'API, jeton Bearer) sans couper les routes : inventaire des consommateurs et des valeurs par défaut, sonde authentifiée sans effet de bord (401 = jeton refusé, 400 = jeton accepté avec action inconnue), lecture de la clé réellement chargée dans /proc/<MainPID>/environ réduite à longueur et sha8, sauvegarde puis réécriture de l'unité, fichier d'environnement 600, daemon-reload et restart, preuves ancien refusé et nouveau accepté, retour arrière automatique, audit des drop-ins .service.d, puis retrait du secret des modèles copiables et des scripts de démarrage. Utiliser après exposition d'une clé (transcript, argv, unité 644), pour une rotation planifiée, ou quand un déploiement réintroduit une ancienne valeur. 不中断路由轮换 systemd 服务 Environment= 携带的 API 密钥。"
---

# Rotation d'une clé d'API portée par une unité systemd

## Portée

Faire tourner un secret qu'un service systemd reçoit par `Environment=` ou `EnvironmentFile=` (clé Bearer, jeton d'API), prouver que l'ancien est refusé et le nouveau accepté, et laisser cohérents l'unité installée, le fichier d'environnement, le fichier de secrets local et les modèles copiables — sans jamais afficher la valeur.

Hors portée : mot de passe SSH/sudo (`rotation-mot-de-passe-vps-sans-fuite`), secret HMAC de webhooks (même mécanique, preuve différente), déploiement de pages (`deployer-site-sans-dol-vps`), logs nginx (`verifier-journaux-nginx-vps`). Une rotation d'un secret ne couvre pas les autres : ne pas annoncer « rotations terminées ».

## 1. Invariants

1. **Aucune valeur en sortie.** Ni stdout, ni stderr, ni argv, ni fichier temporaire conservé, ni journal, ni transcript. Rapporter longueur et `sha256[:8]` uniquement. Relire chaque commande en se demandant ce que le transcript montrera si elle échoue.
2. **Le secret n'est jamais dans une ligne de commande.** Envoyer les scripts distants encodés en base64 et transmettre la nouvelle valeur par SFTP ; ne pas écrire `export CLE=<valeur>` ni `<valeur> | bash`. Un `echo` en erreur suffit à exposer la clé.
3. **`sudo -n` uniquement** sur un hôte NOPASSWD. Ne jamais piper le mot de passe du compte : il serait consommé comme commande par `bash -s` et réaffiché.
4. **Une preuve est une sortie observée.** 401 sur l'ancien jeton et 400 sur le nouveau, mesurés après redémarrage. Un timeout, une erreur TLS ou DNS est **INCONCLUSIF** : il ne prouve ni acceptation ni révocation.
5. **Fermeture par défaut.** Une variable absente doit fermer les routes (401), pas retomber sur une valeur par défaut. Chercher et supprimer les replis avant de tourner.
6. **Confirmation humaine avant l'écriture en production.** Un accord pour une rotation ne couvre pas la suivante ni un autre secret.
7. **Une rotation ne nettoie pas une fuite.** L'ancienne valeur reste dans les transcripts et sauvegardes déjà produites ; on la révoque, on ne l'archive pas.

## 2. Inventorier avant de toucher

```bash
grep -rn "<VARIABLE>" <depot>                 # qui lit la variable, tests compris
grep -rn "Environment=<VARIABLE>=" <depot>     # valeurs écrites en dur
grep -rn "<nom-du-fichier-modele>.service" <depot>   # qui copie le modèle sur l'unité live
```

Relever : l'unité installée (`systemctl cat <unit>`), son utilisateur réel, le nombre de lignes `Environment=` pour cette variable, l'existence d'un `EnvironmentFile=`, la présence d'une valeur par défaut dans le code et dans le script de démarrage, et les clients externes du jeton. Lire le code de la route protégée : l'ordre exact « authentification puis validation de la requête » conditionne la sonde du §3.

## 3. Sonde d'authentification sûre

Choisir une route qui vérifie le jeton **avant** tout effet de bord, puis envoyer une requête volontairement invalide :

```text
POST <route-protégée>  Authorization: Bearer <jeton>
corps : {"action": "<ACTION_INCONNUE>"}
```

| Code | Signification | Usage |
| :--- | :--- | :--- |
| 401 | jeton absent, différent ou refusé | prouve la révocation de l'ancien |
| 400 | jeton accepté, requête invalide, aucun effet | prouve le chargement du nouveau |
| 200 | action valide exécutée | ne jamais utiliser comme sonde |
| timeout, TLS, DNS | INCONCLUSIF | ne prouve rien ; réessayer |

Vérifier dans le code que le 400 est renvoyé **après** le contrôle du jeton et **avant** l'ingestion ou l'écriture. Si l'application renvoie 400 avant d'authentifier, la sonde ment. Prévoir des tentatives bornées, puis conclure « INDISPONIBLE », jamais « refusé ».

## 4. Lire la clé réellement chargée

```bash
pid=$(systemctl show -p MainPID --value <unit>)
sudo -n cat /proc/$pid/environ | tr '\0' '\n' | sed -n 's/^<VARIABLE>=//p' | \
  { IFS= read -r k; printf 'LEN=%s SHA8=' "${#k}"; printf %s "$k" | sha256sum | cut -c1-8; }
```

- `/proc/<pid>/environ` exige root ou le propriétaire du processus.
- Ne pas utiliser `systemctl show -p Environment` : la sortie contient la valeur.
- Exiger exactement une ligne pour la variable ; zéro ou deux justifient un arrêt.
- Comparer ce sha8 avant et après : la preuve porte sur la clé chargée, pas sur le fichier écrit.

## 5. Appliquer la rotation

### 5.1 Préflight (lecture seule)

Service `active`, `sudo -n true` rc 0, une seule ligne `Environment=<VARIABLE>=`, clé chargée lisible, sonde courante **400**, mode plan par défaut sans écriture, `--verifier` strictement en lecture. Refuser si l'un manque.

### 5.2 Sauvegarde et réécriture

```text
cp -a <unit> <unit>.bak-<UTC>
install -o root -g root -m 644 <nouvelle-unité> <unit>
install -o <user-service> -g <user-service> -m 600 <env> <env-file>
systemctl daemon-reload && systemctl restart <unit>
```

- Remplacer **une seule** ligne `Environment=<VARIABLE>=` ; refuser si le compte n'est pas exactement 1.
- Écrire aussi `EnvironmentFile=-<chemin>/secrets/<secret>.env` (ligne `VARIABLE=valeur`) pour que le porteur survive à une recopie du modèle.
- `restart`, pas `reload` : un rechargement ne relit pas l'environnement.
- Attendre `is-active` = `active`, puis une sonde de santé applicative.

### 5.3 Preuves après redémarrage

1. sha8 de la clé chargée = sha8 de la nouvelle clé ;
2. ancienne clé : **401** sur toutes les routes protégées ;
3. nouvelle clé : **400** sur la route de sonde ;
4. pages publiques : 200 ;
5. fichier de secrets local réécrit, même sha8, sans retour à la ligne parasite ;
6. journal sans « clé absente » après redémarrage.

### 5.4 Retour arrière

En cas d'échec à n'importe quelle étape : restaurer l'unité depuis le `.bak-<UTC>`, restaurer le fichier d'environnement (ou le supprimer s'il n'existait pas), restaurer ou supprimer la clé locale, `daemon-reload` + `restart`, attendre `active`, puis re-sonder l'ancienne clé (400 attendu). Distinguer deux codes : retour arrière réussi et état sain (1) ; retour arrière impossible ou service non sain (2) — dans ce cas, arrêter et alerter.

## 6. Piège de régression : les modèles copiables

Un modèle d'unité qui contient la valeur en dur annule la rotation au déploiement suivant, car plusieurs scripts le recopient sur l'unité live. Chercher tous les copieurs, pas seulement le modèle :

- `ASTRO-Q°ODE_SYSTEME/deploiement_vps/deployer_vers_vps.py` (ligne 62 au 2026-10-28) ;
- `ASTRO-Q°ODE_SYSTEME/orchestrateur_unifie_4_demarches.py` (ligne 169) ;
- l'extrait d'installation affiché par la passerelle elle-même.

Le modèle doit porter `EnvironmentFile=-…/secrets/<secret>.env`, sans valeur. **Nuance vérifiée** : recopier le modèle recopie aussi `User=`, `Group=` et `After=` ; dans ce projet le modèle dit `almizan` et l'unité installée `ubuntu`. Avant tout `cp`, comparer `systemctl cat <unit>` au modèle et ne migrer que les lignes d'environnement, ou réconcilier l'utilisateur explicitement. Un générateur d'unité (bootstrap, injection) qui écrit `Environment=<VARIABLE>={CLE}` reproduit le même défaut : le convertir ou le documenter.

## 7. Audit des drop-ins

```bash
ls -la /etc/systemd/system/<unit>.service.d/
journalctl -u <unit> --since "-2h" | grep -i "Assignment outside of section"
```

Un secret collé dans un `.conf` de drop-in est **ignoré** par systemd (ligne hors section, message ci-dessus) et reste lisible en 644. Il faut :

1. sauvegarder le fichier en `600 root` hors de `/etc/systemd/system` ;
2. le supprimer (ou le compléter avec une section `[Service]` valide si son contenu est utile) ;
3. `daemon-reload` **sans** redémarrer le service ;
4. re-vérifier `is-active` et re-sonder la clé.

Si la chaîne peut être un identifiant, la considérer comme exposée et la révoquer partout où elle sert encore.

## 8. Hygiène du secret

- Unité installée : `Environment=` reste lisible en 644 par tout utilisateur local ; c'est une limite connue. Le porteur durable doit être un `EnvironmentFile=` en 600 appartenant à l'utilisateur du service.
- Fichier d'environnement : une ligne, mode 600, propriétaire du service, sans commentaire.
- Clé locale : écriture atomique (`<fichier>.tmp` puis `replace`) dans un dossier dont l'ACL est déjà restreinte ; sous Windows, l'ACL héritée se vérifie avec `icacls`. Pas de nouvelle ligne si le consommateur lit le fichier tel quel.
- Chercher l'ancienne valeur partout après coup (`grep -rn`), y compris docs, tests et sauvegardes ; la révocation prime sur le nettoyage.

## 9. Critères de sortie observables

- [ ] service `active` après `restart`, santé 200 ;
- [ ] sha8 chargé = sha8 nouveau, une seule ligne de variable ;
- [ ] ancienne clé 401 sur chaque route protégée, nouvelle 400 ;
- [ ] fichier d'environnement 600, propriétaire du service ;
- [ ] fichier local synchronisé, aucun `.tmp` résiduel ;
- [ ] sauvegarde d'unité `.bak-<UTC>` listée ;
- [ ] aucun drop-in contenant un secret, aucun message « Assignment outside of section » ;
- [ ] aucun modèle ni script de démarrage avec la valeur en dur ;
- [ ] rapport final en longueur + sha8 + codes HTTP, sans valeur.

## 10. Pièges

- **Sonde métier** : un 200 exécute l'action. Toujours une action invalide sur une route protégée.
- **400 avant authentification** : la sonde devient un faux positif ; vérifier l'ordre dans le code.
- **`Environment=` et variables** : systemd ne développe pas `$VAR` dans cette ligne ; pas d'indirection.
- **`reload`** ne recharge pas l'environnement ; **`restart`** oui, avec une brève coupure à annoncer.
- **`EnvironmentFile` sans tiret** : un fichier absent empêche le démarrage ; avec `-`, le service démarre sans clé et les routes se ferment — vérifier le journal.
- **Sauvegarde d'unité** : le `.bak` hérite 644 et contient l'ancienne clé ; elle est révoquée, mais ne pas la déplacer ailleurs.
- **Recopie du modèle** : elle change aussi `User=`/`Group=` (voir §6).
- **Valeur par défaut résiduelle** dans le script de démarrage ou le code : elle réactive l'ancien secret ; la supprimer avant de tourner.
- **Clients non inventoriés** : la rotation casse tout client encore porteur de l'ancien jeton ; le déclarer comme risque, pas comme succès.
- **Drop-in ignoré** : l'absence d'erreur de démarrage ne prouve pas l'absence de secret dans `.d/`.

## 11. Ressources

- Cas vérifié (états, codes, chemins, limites) : `references/cas-rotation-cle-api-mizan-2026-10-28.md`.
- Implémentation de référence dans ce projet : `ASTRO-Q°ODE_SYSTEME/deploiement_vps/rotation_cle_api_vps.py` (plan, `--verifier`, `--appliquer`, rollback).
- Modèle d'unité migré : `ASTRO-Q°ODE_SYSTEME/deploiement_vps/systemd/al-mizan-api-vps.service`.
- Procédure d'exploitation : `ASTRO-Q°ODE_SYSTEME/docs/EXPLOITATION_VPS.md` (§10).
- Validation d'un Skill après écriture : `skill-file-qa`.
