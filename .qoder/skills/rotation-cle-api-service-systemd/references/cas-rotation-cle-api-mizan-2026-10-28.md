# Cas vérifié : rotation de `MIZAN_VPS_API_KEY` (production, 2026-10-28)

Rotation d'une clé Bearer portée par une unité systemd, exécutée et observée en production sur `www.al-mizan.world`. Ce document ne contient **aucune valeur de secret** : uniquement longueurs, empreintes `sha256[:8]`, codes HTTP, chemins, modes et horodatages UTC. Les affirmations sont séparées en « prouvé par une sortie observée » et « non vérifié ».

## Contexte

- Service : `al-mizan-api-vps`, passager du port 8095, exposé via nginx.
- Variable : `MIZAN_VPS_API_KEY`, lue à chaque requête par la passerelle.
- Routes protégées par le jeton : `POST /api/v1/action` et `POST /api/v1/commande`.
- Déclencheur : la clé de production était encore la valeur par défaut codée en dur dans l'unité et dans le script de démarrage ; elle figurait aussi dans des transcripts antérieurs.
- Outil utilisé : `deploiement_vps/rotation_cle_api_vps.py` (plan par défaut, `--verifier` en lecture seule, `--appliquer` avec retour arrière).
- Autorisation : confirmée explicitement par l'utilisateur pour cette rotation uniquement.

## Chronologie (UTC)

| Heure | Événement |
| :--- | :--- |
| 00:27:36 | demande de passage à la rotation de `MIZAN_VPS_API_KEY` |
| avant 00:31 | inventaire des lecteurs, préparation de l'outil, `--verifier` vert |
| 00:31:23 | `--appliquer` : préflight, sauvegarde, réécriture, `daemon-reload` + `restart`, preuves |
| 00:31:26 | première occurrence du message systemd « Assignment outside of section » |
| 00:31:28 | seconde occurrence du même message |
| 00:31:33 | sauvegarde puis suppression du drop-in invalide, `daemon-reload` seul |
| après | re-vérification `--verifier` : `RESULT OK` |

## État initial observé

| Contrôle | Valeur observée |
| :--- | :--- |
| `systemctl is-active` | `active` |
| longueur de la clé chargée | 31 caractères |
| `sha256[:8]` de la clé chargée | `5d3a4854` |
| lignes `Environment=MIZAN_VPS_API_KEY=` dans l'unité | 1 |
| `EnvironmentFile=` pour cette variable | absent |
| fichier `secrets/mizan_vps_api_key.key` en local | absent |
| `sudo -n true` | rc 0 |
| sonde avec la clé courante | **400** (authentifiée, action inconnue) |

Lecture de la clé chargée sans afficher sa valeur :

```bash
pid=$(systemctl show -p MainPID --value al-mizan-api-vps)
sudo -n cat /proc/$pid/environ | tr '\0' '\n' \
  | sed -n 's/^MIZAN_VPS_API_KEY=//p' \
  | { IFS= read -r k; printf 'LEN=%s SHA8=' "${#k}"; printf %s "$k" | sha256sum | cut -c1-8; }
```

## Sonde d'authentification : pourquoi 400 et pas 200

Dans `passerelle_api_vps_mizan.py`, l'authentification précède la lecture de l'action, et une action inconnue renvoie 400 **avant** l'ingestion. La sonde utilise donc :

```text
POST https://www.al-mizan.world/api/v1/action
Authorization: Bearer <jeton>
{"action": "PROBE_ROTATION"}
```

- 401 → jeton refusé ;
- 400 → jeton accepté, aucun effet de bord ;
- 200 → aurait exécuté une action réelle : inutilisable comme sonde.

## Résultat de l'application (rc 0)

| Élément | Valeur observée |
| :--- | :--- |
| nouvelle clé | 64 caractères URL-safe |
| `sha256[:8]` nouvelle | `97986987` |
| sha8 chargé après `restart` | `97986987` (identique → la clé en mémoire est la nouvelle) |
| sauvegarde d'unité | `/etc/systemd/system/al-mizan-api-vps.service.bak-20261028T003123Z` |
| fichier d'environnement | `…/secrets/mizan_vps_api_key.env`, 83 octets, `600 ubuntu:ubuntu` |
| clé locale | `secrets/mizan_vps_api_key.key`, 64 octets, sans retour à la ligne |
| ACL locale (Windows) | héritée : Système, Administrateurs, Administrateur |
| service après `restart` | `active` |

Preuves HTTP après redémarrage :

| Sonde | Ancienne clé | Nouvelle clé |
| :--- | :--- | :--- |
| `POST /api/v1/action` | **401** | **400** |
| `POST /api/v1/commande` | **401** | non rejoué |
| `GET /` | — | 200 |
| `GET /oeuvre-universelle` (fr/en/ar) | — | 200 |
| `GET /api/v1/sante` | — | 200 |

Le journal ne contenait plus de ligne « clé absente » après le redémarrage.

## Retrait des valeurs par défaut (cause de régression)

Sans ce nettoyage, le déploiement suivant aurait réintroduit l'ancienne clé :

- `deploiement_vps/systemd/al-mizan-api-vps.service` : la ligne `Environment=` contenant la valeur a été remplacée par deux `EnvironmentFile=-…/secrets/*.env` ; plus aucune valeur en dur.
- `deploiement_vps/demarrer_passerelle_vps.sh` : plus de valeur par défaut ; lecture de l'environnement, sinon des fichiers locaux, sinon routes fermées (401).
- `passerelle_api_vps_mizan.py` : lecture de `MIZAN_VPS_API_KEY` sans repli ; variable absente → refus.

Copieurs du modèle à surveiller : `deploiement_vps/deployer_vers_vps.py:62` et `orchestrateur_unifie_4_demarches.py:169` recopient le fichier modèle sur l'unité live.

**Nuance vérifiée** : le modèle porte `User=almizan` / `Group=almizan`, l'unité installée tourne sous `ubuntu`. Copier le modèle tel quel changerait l'utilisateur du service. Ne recopier que les lignes d'environnement, ou réconcilier l'utilisateur explicitement.

**Limite observée** : l'unité live est restée sur `Environment=` (644, lisible par tout utilisateur local). Le porteur `EnvironmentFile` en 600 existe et est chargé, mais la migration de l'unité live vers `EnvironmentFile` n'a pas été réalisée dans cette fenêtre ; elle reste à planifier.

## Drop-in invalide trouvé en production

Un fichier `/etc/systemd/system/al-mizan-api-vps.service.d/pythonpath.conf` contenait une chaîne de 21 octets, mode `644 root:root`, sans section `[Service]`. systemd l'ignorait en journalisant « Assignment outside of section » (00:31:26 et 00:31:28) : la valeur n'était donc pas chargée, mais restait lisible par tout utilisateur local.

Traitement appliqué :

1. copie vers `/opt/al-mizan/sauvegardes/pythonpath.conf.bak-20261028T003321Z`, mode `600 root` ;
2. suppression du drop-in ;
3. `daemon-reload` **sans** redémarrer le service ;
4. `is-active` → `active`, clé re-sondée → `RESULT OK`.

Conclusion : si la chaîne était un identifiant, elle doit être considérée comme exposée et révoquée partout où elle sert encore. L'absence d'erreur au démarrage ne prouve pas l'absence de secret dans `.d/`.

## Ce qui n'est pas prouvé

- Aucune preuve que tous les clients externes du jeton ont été migrés : la rotation casse tout client encore porteur de l'ancienne valeur.
- Aucune preuve de la migration de l'unité live vers `EnvironmentFile` (voir ci-dessus).
- La rotation ne retire pas l'ancienne valeur des transcripts et sauvegardes déjà produits ; elle la révoque seulement.
- `HMAC_SECRET_WEBHOOKS` est un autre secret, avec une autre preuve ; il a fait l'objet d'une rotation séparée (sha8 `920cce39`) et n'est pas couvert par ce Skill.
- `sshd` accepte toujours l'authentification par mot de passe ; sans lien avec cette rotation.

## Reproductibilité

Les affirmations ci-dessus sont liées à l'état des fichiers suivant (SHA-256 calculés le 2026-10-28 avant écriture de ce document) :

| Fichier | SHA-256 |
| :--- | :--- |
| `deploiement_vps/rotation_cle_api_vps.py` | `27f380a5a016295f38f0f9fa848bc1d7831547e4b20ca6f7293f8df3eb22f023` |
| `deploiement_vps/systemd/al-mizan-api-vps.service` | `a740944b…` (modèle migré vers `EnvironmentFile`) |
| `deploiement_vps/demarrer_passerelle_vps.sh` | `e9fabdc1…` |
| `deploiement_vps/deployer_vers_vps.py` | `cd806a2f…` |
| `orchestrateur_unifie_4_demarches.py` | `0fcd22ae…` |
| `passerelle_api_vps_mizan.py` | `7944197b…` |
| `docs/EXPLOITATION_VPS.md` | `4721dba3…` |

Si un de ces fichiers change, revérifier l'ordre « authentification avant validation », le nombre de lignes `Environment=` et les copieurs du modèle avant de se fier à ce cas.

## Assainissement

Aucune valeur n'a été reportée ici. Les seules données conservées sont : longueurs (31, 64, 83, 21), empreintes `sha256[:8]`, codes HTTP, chemins, modes, propriétaires et horodatages. Le mot de passe sudo et la valeur de l'ancienne clé ont été exclus, y compris sous forme d'extrait.
