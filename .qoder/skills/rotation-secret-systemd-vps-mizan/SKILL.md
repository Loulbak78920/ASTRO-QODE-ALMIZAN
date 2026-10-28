---
name: rotation-secret-systemd-vps-mizan
description: "Faire tourner le secret HMAC des webhooks MIZAN_WEBHOOK_SECRET porté par l'unité systemd Al-Mizan sans casser les clients : inventaire des consommateurs, porte « zéro abonné » lue sur /api/v1/webhooks, préflight en lecture seule limité à longueur et sha256 tronqué, sauvegarde de l'unité en .bak-<UTC>, fichier d'environnement 600, remplacement d'une seule ligne Environment=, daemon-reload et restart, preuve que la valeur de repli historique a disparu, retour arrière automatique, puis durcissement des générateurs de déploiement et du script de démarrage pour qu'aucun déploiement ne réintroduise l'ancienne valeur. Complète rotation-cle-api-service-systemd, qui couvre la clé Bearer et la mécanique commune ; ne traite ni mot de passe SSH ni clé d'API. Utiliser pour tourner un secret HMAC de webhooks, vérifier qu'un secret systemd n'est plus la valeur par défaut, ou auditer les artefacts qui portent un ancien secret. 轮换 systemd 服务携带的 webhook HMAC 密钥。"
---

# Rotation d'un secret HMAC porté par une unité systemd

## Portée

Faire tourner `MIZAN_WEBHOOK_SECRET` sur le VPS Al-Mizan, prouver que le service charge bien autre chose que la valeur de repli, et empêcher qu'un déploiement ultérieur réintroduise l'ancienne valeur.

Ce Skill ne documente que le **delta** vérifié le 2026-10-28 pour le secret HMAC et la chaîne de durcissement. La mécanique commune est déjà couverte par `rotation-cle-api-service-systemd` et s'applique telle quelle :

| Mécanique commune | Où elle est décrite |
| :--- | :--- |
| Lecture de la variable réellement chargée dans `/proc/<MainPID>/environ` en longueur + sha8 | `rotation-cle-api-service-systemd` §4 |
| Sonde authentifiée 401/400 sans effet de bord | `rotation-cle-api-service-systemd` §3 — **ne s'applique pas au HMAC** (aucune route ne vérifie une signature entrante) |
| `.bak-<UTC>`, `install` avec propriétaire et mode, rollback rc 1/2 | `rotation-cle-api-service-systemd` §5 |
| Audit des drop-ins `.service.d/` | `rotation-cle-api-service-systemd` §7 |

Hors portée : mot de passe SSH/sudo (`rotation-mot-de-passe-vps-sans-fuite`), clé Bearer `MIZAN_VPS_API_KEY` (`rotation-cle-api-service-systemd`), déploiement de pages (`deployer-site-sans-dol-vps`), journaux nginx (`verifier-journaux-nginx-vps`). Un secret par rotation : ne jamais annoncer « rotations terminées » après un seul secret.

## 1. Invariants

1. **Aucune valeur en sortie.** Ni stdout, ni stderr, ni argv, ni journal, ni transcript. Rapporter longueur et `sha256[:8]` uniquement.
2. **Le secret n'est jamais dans une ligne de commande.** Les scripts distants partent en base64 ; la nouvelle valeur voyage par SFTP dans un fichier temporaire, puis `install`, puis suppression.
3. **`sudo -n` uniquement** sur un hôte NOPASSWD. Ne jamais piper le mot de passe du compte : `bash -s` l'exécuterait et le réafficherait.
4. **Zéro abonné webhook avant de tourner.** Un client inscrit vérifie les signatures avec l'ancien secret : sa vérification échouerait sans message visible côté serveur.
5. **Pas de sonde HTTP pour le HMAC.** Contrairement à la clé Bearer, aucune route publique ne valide une signature entrante. La preuve est lue dans l'environnement du processus : `SECRET_SHA8` nouveau et `SECRET_DEFAUT NON`. Ne pas inventer un 200 ou un 400 qui ne prouverait rien.
6. **La valeur de repli doit avoir disparu.** Une variable absente ne doit ramener aucune valeur historique : depuis le 2026-10-28, `passerelle_api_vps_mizan.py` refuse de démarrer sans `MIZAN_WEBHOOK_SECRET` (`secret_webhooks_requis()` lève une erreur). Le contrôle `SECRET_DEFAUT NON` reste le témoin : il compare l'empreinte du secret du processus à `ee9faafa`, sans que le dépôt porte la valeur.
7. **Confirmation humaine avant l'écriture en production.** Un accord pour un secret ne couvre ni le suivant ni un autre secret.
8. **Ne pas tourner deux fois.** Lancer `--verifier` d'abord ; si l'état est déjà vert (`64`, `NON`, `0`), le dire et s'arrêter.
9. **Une rotation ne nettoie pas une fuite.** L'ancienne valeur reste dans les transcripts et sauvegardes déjà produits ; on la révoque, on ne l'archive pas.

## 2. Inventorier avant de toucher

```bash
grep -rn "MIZAN_WEBHOOK_SECRET" <depot>
grep -rn "mizan_webhook_secret.key" <depot>
grep -rn "Environment=MIZAN_WEBHOOK_SECRET=" <depot>
```

Relever : l'unité installée (`systemctl cat al-mizan-api-vps`), son utilisateur réel, le nombre de lignes `Environment=` pour la variable, l'existence d'un `EnvironmentFile=`, l'absence de valeur de repli dans le code (le secret ne doit venir que de l'environnement), et les clients externes qui vérifient les signatures. Les tests portent leurs propres valeurs : ne pas les compter comme des consommateurs de production.

## 3. Porte « zéro abonné »

```bash
curl -s http://127.0.0.1:8095/api/v1/webhooks
```

Lire `total_webhooks_inscrits`. Tant qu'il n'est pas `0`, arrêter : soit désinscrire les abonnés, soit faire tourner leurs secrets d'abord.

Limite à énoncer : les abonnements sont tenus **en mémoire** et disparaissent au redémarrage. Le compteur prouve seulement qu'aucun abonné n'est enregistré dans cette instance ; il ne prouve pas qu'aucun client externe ne détient encore l'ancien secret. Le 2026-10-28, `0` abonné a été observé : aucun client n'a donc été invalidé.

## 4. Préflight en lecture seule

```bash
cd ASTRO-Q°ODE_SYSTEME
py -3 deploiement_vps/rotation_secret_webhooks.py --verifier
```

Clés attendues et lecture :

| Clé | Attendu avant rotation | Sens |
| :--- | :--- | :--- |
| `ETAT` | `active` | service en marche |
| `SECRET_LEN` | > 0 | secret lisible dans l'environnement du processus |
| `SECRET_SHA8` | empreinte du secret actuel | référence pour la comparaison après coup |
| `SECRET_DEFAUT` | `OUI` tant que l'ancienne valeur sert | doit devenir `NON` (comparaison sur `SECRET_SHA8` = `ee9faafa`) |
| `ENVFILE_HOOKS` | `1` | une seule ligne `EnvironmentFile=` vers le fichier du secret |
| `LIGNES_SECRET` | `0` | aucune ligne `Environment=` porteuse du secret |
| `ENV_FILE` | `ABSENT` ou `PRESENT` | état du fichier d'environnement |
| `ABONNES` | `0` | porte du §3 |
| `SUDO` | `OK` | `sudo -n` disponible |
| `SECRET_LOCAL` | `ABSENTE` ou `SYNCHRONISEE` | clé locale locale |

Avant rotation, `RESULT A REVOIR` et un code de sortie 1 sont **normaux** : l'outil signale que le processus porte encore l'ancienne valeur de repli. Ce n'est pas une panne.

Pour lire l'environnement sans passer par l'outil, la commande du Skill voisin (`rotation-cle-api-service-systemd` §4) s'applique en remplaçant le nom de variable. Ne jamais utiliser `systemctl show -p Environment` : la sortie contient la valeur.

## 5. Appliquer

```bash
cd ASTRO-Q°ODE_SYSTEME/deploiement_vps
py -3 rotation_secret_webhooks.py            # plan, aucune écriture
py -3 rotation_secret_webhooks.py --appliquer
```

`--appliquer` : préflight, refus si un abonné existe, génération d'un secret URL-safe de 64 caractères, `cp -a` de l'unité et de l'env en `.bak-<UTC>`, retrait des éventuelles lignes `Environment=MIZAN_WEBHOOK_SECRET=` legacy, écriture de `secrets/mizan_webhook_secret.env` (`600 ubuntu:ubuntu`), `daemon-reload` + `restart`, attente de `/api/v1/sante`, contrôle sha8 et `SECRET_DEFAUT`, écriture atomique de `secrets/mizan_webhook_secret.key`, puis retour arrière automatique en cas d'échec.

- `restart`, jamais `reload` : un rechargement ne relit pas l'environnement. Prévenir de la brève coupure.
- L'outil **exige** une ligne `EnvironmentFile=` vers le fichier du secret, écrit ce fichier et ne retire que d'éventuelles lignes `Environment=` legacy ; il ne crée ni ne modifie `EnvironmentFile=`. Si l'unité n'en a pas, le préflight s'arrête avant toute écriture.
- Code de retour 1 : échec, état restauré. Code 2 : retour arrière impossible ou service non sain — arrêter et alerter.

## 6. Preuves après redémarrage

| Contrôle | Attendu |
| :--- | :--- |
| `SECRET_LEN` / `SECRET_SHA8` | 64 / empreinte du nouveau secret |
| `SECRET_DEFAUT` | `NON` |
| `ABONNES` | `0` |
| `ETAT` | `active` |
| `GET /api/v1/sante` | 200 |
| Sonde de la clé Bearer | toujours 400 (la rotation HMAC ne doit rien casser) |
| Pages `/`, `/oeuvre-universelle`, `/ar` | 200 |
| `secrets/mizan_webhook_secret.key` | 64 octets, sans retour à la ligne, même sha8 |
| `.tmp` résiduelle | aucune |
| Journal après redémarrage | aucune erreur liée au secret |

La preuve est **environnementale**, pas applicative : on ne peut pas signer un webhook vers un abonné inexistant pour vérifier la nouvelle valeur.

## 7. Durcir la chaîne de déploiement

Sans cela, le prochain déploiement réécrit l'ancienne valeur. Vérifier chaque porteur :

| Artefact | Attendu |
| :--- | :--- |
| `ASTRO-Q°ODE_SYSTEME/deploiement_vps/systemd/al-mizan-api-vps.service` | `EnvironmentFile=-…/secrets/mizan_vps_api_key.env` (optionnel : routes protégées fermées) et `EnvironmentFile=…/mizan_webhook_secret.env` **sans tiret** (obligatoire : démarrage refusé si absent), aucune valeur |
| `ASTRO-Q°ODE_SYSTEME/deploiement_vps/demarrer_passerelle_vps.sh` | aucun `${VAR:-valeur}` ; environnement, sinon fichier `secrets/*.key`, sinon routes fermées |
| `ASTRO-Q°ODE_SYSTEME/deploiement_vps/injecter_et_deployer.py` | `secret_webhooks()` lit `secrets/mizan_webhook_secret.key` ; aucune valeur dans l'unité générée ; `EnvironmentFile=` du secret webhooks **sans `-`** |
| `ASTRO-Q°ODE_SYSTEME/deploiement_vps/deploiement_automatique_ovh.py` | idem |
| `ASTRO-Q°ODE_SYSTEME/passerelle_api_vps_mizan.py` | `secret_webhooks_requis()` lit `MIZAN_WEBHOOK_SECRET` et lève une erreur si elle manque ; aucune valeur de repli, refus de démarrer |

Preuve que les deux générateurs chargent le même secret que le service, sans l'afficher :

```bash
cd ASTRO-Q°ODE_SYSTEME/deploiement_vps
py -3 -B -c "import hashlib; from injecter_et_deployer import secret_webhooks as a; from deploiement_automatique_ovh import secret_webhooks as b; [(print(n, len(f()), hashlib.sha256(f().encode()).hexdigest()[:8])) for n,f in (('A',a),('B',b))]"
```

Attendu : deux lignes `A 64 <sha8>` / `B 64 <sha8>` identiques au `SECRET_SHA8` du service.

**Repli retiré, non déployé (2026-10-28)** : dans le dépôt local, `passerelle_api_vps_mizan.py` n'a plus aucune valeur de repli ; `secret_webhooks_requis()` refuse de signer et le processus refuse de démarrer sans `MIZAN_WEBHOOK_SECRET` (`Démarrage refusé`, code de sortie 1), l'orchestrateur unifié utilise le même accesseur, `rotation_secret_webhooks.py` ne garde que l'empreinte `ee9faafa` et le template d'unité rend l'`EnvironmentFile=` du secret obligatoire. La production n'a pas encore reçu ce lot : vérifier son état avant de conclure qu'un service tourne sans repli.

## 8. Tracer

- Consigner dans `ASTRO-Q°ODE_SYSTEME/docs/EXPLOITATION_VPS.md` §10 : UTC, longueur, sha8, chemin du `.bak-<UTC>`, nombre d'abonnés au moment de la rotation.
- Mettre à jour la mémoire projet : le secret est tourné, et l'éventuel repli restant comme son retrait local non déployé sont nommés.
- Énumérer séparément chaque secret ; ne pas clore les rotations voisines non faites.

## 9. Critères de sortie observables

- [ ] `--verifier` post-rotation : `RESULT OK`, rc 0 ;
- [ ] `SECRET_LEN 64`, `SECRET_SHA8` = nouveau, `SECRET_DEFAUT NON` ;
- [ ] `ABONNES 0` avant et après ;
- [ ] sauvegarde `.bak-<UTC>` de l'unité listée, non déplacée ;
- [ ] fichier d'environnement 600, propriétaire du service ;
- [ ] clé locale 64 octets, même sha8, aucun `.tmp` ;
- [ ] clé Bearer toujours acceptée (400), santé et pages en 200 ;
- [ ] aucun artefact de déploiement ne porte plus l'ancienne valeur ;
- [ ] démarrage refusé sans `MIZAN_WEBHOOK_SECRET` (contrôle négatif local) ;
- [ ] rapport final en longueur + sha8 + codes HTTP, sans valeur.

## 10. Pièges

| Piège | Effet | Correctif |
| :--- | :--- | :--- |
| Rotation avec des abonnés inscrits | leurs vérifications HMAC échouent sans erreur serveur | porte du §3, refus explicite de l'outil |
| Croire que `0 abonné` prouve l'absence de client externe | rotation « silencieuse » d'un intégrateur | déclarer la limite, prévenir les clients connus |
| Sonde HTTP inventée pour le HMAC | un 200 ne prouve rien sur le secret | preuve environnementale §6 |
| `EnvironmentFile=` sans tiret pour la clé d'API | un fichier absent bloque tout le service, secret webhooks compris | garder `-` pour la clé (routes fermées), l'enlever pour le secret webhooks |
| `EnvironmentFile=-` avec fichier absent (secret webhooks) | service démarré sans variable, signature HMAC impossible | template sans `-` + accesseur à échec fermé ; vérifier `SECRET_DEFAUT NON` |
| Unité live restée sur `Environment=` 644 | deux sources divergentes | même valeur des deux côtés jusqu'à migration |
| Recopie du modèle d'unité | change aussi `User=almizan`/`Group` alors que l'unité tourne sous `ubuntu` | ne recopier que les lignes d'environnement |
| Générateur de déploiement avec valeur en dur | l'ancien secret revient au bootstrap | helpers `secret_webhooks()` + placeholders |
| `py_compile` laisse un `.pyc` malgré `-B` | résidu dans le paquet | supprimer le `.pyc` créé, vérifier `__pycache__` |
| Imprimer le dict de préflight de l'outil voisin | `CLE_VALEUR` contient la clé d'API | n'imprimer que les clés nommées |
| `.bak` d'unité en 644 | contient l'ancien secret | révoqué, mais ne pas le déplacer |
| Relancer `--appliquer` sur un secret déjà tourné | redémarrage et `.bak` inutiles | `--verifier` d'abord, s'arrêter si vert |
| Secrets de test confondus avec la production | rotation inutile des fixtures | inventorier, ne pas toucher aux tests |

## 11. Ressources

- `references/preuves-webhooks-et-durcissement-2026-10-28.md` — chronologie, états observés, preuves, hashes des artefacts, limites.
- Outil éprouvé : `ASTRO-Q°ODE_SYSTEME/deploiement_vps/rotation_secret_webhooks.py` (plan, `--verifier`, `--appliquer`, rollback). Le réutiliser plutôt que d'en écrire un second.
- Validateur de Skill : `skill-file-qa`.
- Procédure d'exploitation : `ASTRO-Q°ODE_SYSTEME/docs/EXPLOITATION_VPS.md` §10.

## 12. Articulation avec les Skills voisins

- `rotation-cle-api-service-systemd` : clé Bearer et mécanique commune (sonde 401/400, `/proc`, `.bak`, rollback, drop-ins). Compléter ici sans dupliquer.
- `rotation-mot-de-passe-vps-sans-fuite` : mot de passe SSH/sudo, hors périmètre.
- `deployer-site-sans-dol-vps` : déploiements de pages et d'archives ; vérifier qu'un lot ne réintroduit pas d'ancienne valeur.
- `verifier-journaux-nginx-vps` : preuves de trafic après redémarrage.
