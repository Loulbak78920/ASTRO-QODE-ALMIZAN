# Preuves — lot statique 4D, passerelle locale fail-closed et absence de générateur distant (29/10/2026)

## Source

| Élément | Valeur |
| :--- | :--- |
| Session | `0375742e-d274-484f-a479-2ef1eb31e0cf`, titre « 创建结果中性化 Skill » |
| Tour utile | 2026-10-29T15:04:18.084Z, demande « 修复这 4 条公式的残留 » |
| Autorisation de déploiement | réponse d'interaction « Deployer maintenant (Recommandé) » |
| Lecture | 2026-10-29, `turnLimit = 20`, `includeToolOutputs = true`, `runtimeState = cold`, `activeTurnId = null`, `revision = 0`, `hasMoreBefore = false` |
| Sorties | `read_chat_session` renvoie les sorties d'outils, pas les entrées (commandes). La valeur `local-test-only` vient de la recommandation de mise à jour, pas d'une entrée d'outil relue ici. |

Les heures des messages sont en UTC ; les sorties d'outils sont horodatées par le système local (+0100). Le premier tour de la session concerne un autre Skill ; le déploiement 4D appartient au second tour.

## 1. Passerelle locale : fail-closed et port résiduel

Le code local refuse de démarrer sans `MIZAN_WEBHOOK_SECRET` (`passerelle_api_vps_mizan.py:90-97` et `:2184-2187`, relu le 29/10/2026) :

```text
[ERREUR] Démarrage refusé : MIZAN_WEBHOOK_SECRET absent : signature des webhooks impossible.
```

Constat sur le port 18095 :

```text
TCP    0.0.0.0:18095          0.0.0.0:0              LISTENING       10668
```

Les quatre routes 4D répondaient 404 sur ce port, avec le corps `{"succes": false, "erreur": "Route GET introuvable"}`, alors que la source courante les déclare (`passerelle_api_vps_mizan.py:154-159`). Le nouveau processus avait déjà quitté sur le refus de démarrage : le 404 ne pouvait pas venir de la nouvelle version. L'attribution au PID 10668 est forte (port tenu + nouveau processus sorti) mais non instrumentée : le code chargé par 10668 n'a pas été interrogé.

Validation sur un autre port (18096), avec un secret factice :

```text
/quatrieme-dimension         200 text/html; charset=utf-8 29930
/quatrieme-dimension/en      200 text/html; charset=utf-8 28985
/quatrieme-dimension/ar      200 text/html; charset=utf-8 31408
/quatrieme-dimension.json    200 application/json; charset=utf-8 14881
/4d                          200 text/html; charset=utf-8 29930
```

Arrêt : `pid=14824`, `killed`. Les sorties capturées contiennent aussi une phase `000` (connexion non établie) avant la phase 200 ; seule la phase 200 est retenue comme preuve de service. Les tailles sont celles servies (LF), pas celles des fichiers locaux (CRLF).

## 2. Déploiement du lot (4 fichiers)

| Contrôle | Valeur observée |
| :--- | :--- |
| Sauvegarde | `/opt/al-mizan/sauvegardes/lot-20261029-151121/sauvegarde.tar.gz`, 4 fichiers, sha `25a127ac5120a78e6eaa78ce1aa7377673e2eb0fd633f6c8f58df8f11adc7e90` |
| Modes | `ubuntu:ubuntu 666` pour les quatre fichiers |
| Hashes distants = locaux | `840465dd…` (fr), `db43ccfa…` (en), `803956e6…` (ar), `49ec7172…` (json) |
| `.py` dans le lot | aucun ; pas de redémarrage ; service `active` |
| Routes locales après installation | 4D : 200 (29930, 28985, 31408, 14881) |

## 3. Absence de générateur ou de planificateur distant

```text
--- find moteur ---
(vide)
--- cron utilisateur ---
(vide)
--- services/cron citant le generateur ---
(vide)
```

Le listing distant de `oeuvre_universelle/` contient `generer_page_oeuvre.py`, `generer_page_riemann.py`, `manifeste_anteriorite.py`, `modeles_reference.py`, `registre_problemes_monde.py` et `riemann_verification.py` ; aucun `quatrieme_dimension.py` ni `generer_page_quatrieme_dimension.py`. Les timers listés étaient `sysstat-collect`, `fwupd-refresh`, `certbot`, `apt-daily`, `update-notifier-download`, `systemd-tmpfiles-clean`, `motd-news`, `dpkg-db-backup` et `logrotate`.

La conclusion vaut pour cet état daté : aucun générateur installé, aucun cron utilisateur/root cité, aucun timer de génération. Un générateur installé plus tard, ou une exécution manuelle, rouvre la question. La session source a constaté le cron utilisateur vide et l'absence de service/cron citant le générateur ; la lecture explicite de `crontab -l -u root` et de chaque fichier `/etc/cron*` appartient à la commande ajoutée au SKILL.md, pas à une sortie de cette session.

## 4. Égalité de contenu

| Fichier | Brut | LF normalisé | SHA public | SHA local |
| :--- | :--- | :--- | :--- | :--- |
| `quatrieme_dimension.html` | DIFF | EGAL | `949fd0ff…` | `840465dd…` |
| `quatrieme_dimension_en.html` | DIFF | EGAL | `7c7c497c…` | `db43ccfa…` |
| `quatrieme_dimension_ar.html` | DIFF | EGAL | `8ebb6c5b…` | `803956e6…` |
| `quatrieme_dimension_resultats.json` | EGAL | EGAL | `49ec7172…` | `49ec7172…` |

Le JSON est identique en brut ; les HTML ne le sont qu'après normalisation CRLF → LF (invariant 9, §8).

## 5. Journaux nginx

Fenêtre `SINCE 29/Oct/2026:14:52`, 175 lignes : 0 réponse 5xx, 0 404 sur `quatrieme`, 28 réponses 200 sur ces routes (dont 6 `/quatrieme-dimension`, 6 `/ar`, 5 `/en`, 5 `.json`, 2 `/`, 2 `resultats.json`, 2 `quatrieme_dimension`). Les 119 autres 404 ne sont pas attribués.

## Limites

- Les commandes exactes ne sont pas capturées ; seules les sorties le sont. La valeur du secret factice est rapportée par la recommandation, pas relue dans une sortie.
- Le code du PID 10668 n'a pas été interrogé : l'attribution du 404 est une inférence par possession du port et sortie du nouveau processus.
- « Aucune réécriture » est un instantané du 29/10/2026 ; il ne couvre ni `at`/`anacron`, ni une exécution manuelle ultérieure.
- Les 119 autres 404 des journaux ne sont pas triés.
