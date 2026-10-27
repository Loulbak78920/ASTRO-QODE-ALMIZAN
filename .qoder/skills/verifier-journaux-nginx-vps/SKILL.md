---
name: verifier-journaux-nginx-vps
description: "Lecture et triage des journaux nginx d'un VPS par SSH/sudo — agréger statuts, chemins et IP sur une fenêtre UTC, séparer le trafic de vérification des scans de bots, et corréler les 5xx avec error.log. Utiliser pour confirmer qu'un déploiement est pris en compte, vérifier la disparition de 404 après un correctif, expliquer un 502 isolé ou qualifier un volume de scans (.env, .git, xmlrpc.php, wp-admin)."
---

# Vérifier les journaux nginx d'un VPS

## Vue d'ensemble

Lire en lecture seule `/var/log/nginx/access.log` et `error.log` sur le VPS OVH par SSH/sudo, agréger sur **une seule fenêtre UTC**, puis trier les entrées en trois classes : trafic de vérification, scans automatisés, incidents réels. Le rapport ne conclut que sur la fenêtre lue.

## Quand l'utiliser

- Confirmer qu'un déploiement est pris en compte : les requêtes attendues apparaissent-elles à l'heure annoncée ?
- Vérifier qu'un 404 a disparu après correctif (`/favicon.ico`, alias de route).
- Expliquer un 5xx isolé en le corrélant à `error.log`.
- Qualifier un volume de 404/400 : scan de robots ou vrai manque côté site.

Ne pas utiliser pour modifier nginx, déployer, ou lire des journaux applicatifs. Pour la chaîne de déploiement, l'étape 6 de `deployer-site-sans-dol-vps` renvoie ici.

## Prérequis

| Élément | Valeur |
|---|---|
| Interpréteur | `py -3` (l'alias `python` du Store échoue), `PYTHONIOENCODING=utf-8` |
| Dépendance | `paramiko` 5.1.0 |
| Secrets | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\secrets\ovh_vps_ssh.json` |
| Chargeur | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\deploiement_vps\charger_credentials_ovh.py` (`hote_user_mdp()`) |

Le mot de passe ne circule que sur stdin de `sudo -S -p ''`. Ne jamais l'afficher, le journaliser ou l'écrire dans le dépôt.

## Procédure

### 1. Fixer la fenêtre et l'objectif avant de lire

Écrire d'emblée : l'objectif mesurable (« aucun 404 sur `/favicon.ico` depuis 01:55:31 UTC »), la fenêtre UTC et le nombre de lignes visées. Sans cela, les compteurs sont interprétés à l'envers.

Les journaux sont en **UTC** (`+0000`) alors que la machine est en heure locale : convertir, et libeller UTC dans le rapport.

### 2. Lire et agréger en une passe

```bash
cd /c/Users/Administrateur/Desktop/IMAM8MAHDI
# adapter la date à la fenêtre visée (UTC)
PYTHONIOENCODING=utf-8 py -3 "C:\Users\Administrateur\.qoder\skills\verifier-journaux-nginx-vps\scripts\lire_journaux_nginx.py" \
  --lignes 2000 --depuis "27/Oct/2026:00:00:00"
```

Options utiles :

| Option | Effet |
|---|---|
| `--depuis "27/Oct/2026:01:55:31"` | filtre la fenêtre sur l'horodatage parsé (UTC par défaut), pas sur une chaîne |
| `--apres "27/Oct/2026:01:55:31"` | coupe après déploiement : ne compte que les requêtes à partir de cet instant (`APRES`, `404_APRES`) |
| `--route "/favicon.ico"` | chronologie exacte d'un chemin dans la fenêtre (`ROUTE_REQUETES`, ordre chronologique) |
| `--chemin "/api/"` | restreint à un chemin (regex) |
| `--journal /var/log/nginx/access.log.1` | journal tourné (`access.log` peut commencer à 00:02 après rotation) |
| `--fichier-local copie.log` | analyse hors ligne, sans SSH |
| `--erreurs-fichier copie_error.log` | avec `--fichier-local` : analyse `error.log` local (interprétations et total upstream) |
| `--json` | sortie JSON (mêmes champs, plus `404`, `apres`, `route`, `erreurs`) au lieu des blocs |
| `--sans-erreurs` | n'interroge pas `error.log` |
| `--racine <chemin>` | racine `ASTRO-Q°ODE_SYSTEME` si `MIZAN_RACINE` n'est pas défini |

Le script sort un bloc `CLÉ=VALEUR` : `RESULTAT`, `LIGNES_RETOURNEES`, `LIGNES_PARSEES`, `IGNOREES`, `METHODES_NON_STANDARD`, `FENETRE_TOTALE`, `LIGNES_ANALYSEES`, `FENETRE_ANALYSEE`, `STATUTS`, `SOMME_STATUTS`, `SOMME_OK`, `IP_DISTINCTES`, `TOP_IP`, `TOP_CHEMINS`, `5XX`, `CANDIDATS_VERIFICATION`, `CANDIDATS_SCAN`, `404_TOTAL`, `404_CLASSES` (`scan` / `vrai_manque_candidat` / `inconnu`), `404_TOP_SCAN`, `404_TOP_VRAI_MANQUE`, `404_TOP_INCONNU`, `IPS_CLOUDFLARE`, `ERREURS_INTERPRETATIONS`, `APRES`, `404_APRES`, `ROUTE`, `ROUTE_REQUETES`, `AVERTISSEMENTS`, `ERROR_LOG`.

`TOP_IP` est en une ligne par adresse, séparateur **tabulation** (`IP\tN`) : les adresses IPv6 contiennent des espaces dans les formats à colonnes fixes, une tabulation reste découpable par `cut -f`.

`--json` renvoie un objet avec les mêmes mesures (`somme_ok`, `quatre_cent_quatre.classes`, `apres.404`, `route.requetes`, `erreurs.interpretations`) ; code retour `0` si cohérent, `3` sinon. Les dates illisibles donnent `2` (`ERREUR_FENETRE`, `ERREUR_APRES`), un fichier absent `1`.

Exiger `RESULTAT=PASS` et `SOMME_OK=OUI` avant toute conclusion. Si `IGNOREES > 0`, inspecter `EXEMPLES_IGNOREES` : un format de ligne non prévu fausse la répartition.

### 3. Trier les entrées en trois classes

| Classe | Signatures observées | Conclusion |
|---|---|---|
| Vérification | IPv6 de la machine de test, UA `Python-urllib/3.14`, `curl/8.17.0` | confirme les tests ; ne compte pas comme trafic visiteur |
| Scan de bots | `/xmlrpc.php`, `.env`, `.git/config`, `.aws/credentials`, `.docker/`, `.claude/`, `/wp-admin/install.php` | rejet correct, pas un incident ; origine souvent masquée par Cloudflare |
| Incident réel | 5xx, 404 sur un chemin servi par le site, 400 hors tests négatifs | à corréler avec `error.log` avant d'annoncer |

Un 301 n'est pas un succès : `/favicon.ico` peut répondre 301 puis 404 sur la cible. Compter le statut final.

Le script classe les 404 pour trancher sans jugement manuel : `scan` (signatures `.env`, `.git`, `xmlrpc.php`, `wp-admin`, `wp-content`, `phpmyadmin`, extensions `.php/.sql/.bak`…), `vrai_manque_candidat` (ressource statique du site : `.ico`, `.css`, `.js`, `.svg`, `/assets/`…), `inconnu`. Un candidat « vrai manque » n'est un incident qu'après vérification que le site devait servir ce chemin ; l'inconnu se lit ligne à ligne.

### 4. Rapporter

Structure attendue :

1. fenêtre UTC exacte et nombre de lignes analysées ;
2. tableau des requêtes de vérification (heure, méthode, chemin, statut, taille) ;
3. répartition des statuts avec la somme contrôlée ;
4. explication de chaque anomalie, séparément : scan, incident transitoire, vrai manque ;
5. limite explicite : « aucun 404 observé dans la fenêtre », jamais « aucun 404 ».

Pour une vérification après déploiement, livrer le couple `--depuis <déploiement>` et `--apres <déploiement>` : `APRES_TOTAL` (volume reçu) et `404_APRES` (statut final sur les chemins visés), avec `--route /favicon.ico` pour la chronologie exacte. Un `404_APRES=0` ne vaut que pour la fenêtre lue.

Pour un 5xx, citer la ligne `error.log` correspondante (ex. `upstream prematurely closed connection`), puis l'appel suivant qui a réussi. `ERREURS_INTERPRETATIONS` sépare déjà « coupé avant les en-têtes » (crash ou timeout applicatif) de « coupure pendant le corps » (client qui interrompt un gros fichier) — lire le sens, puis confirmer avec les appels voisins. Un 502 unique non reproduit est transitoire, pas un incident en cours.

## Pièges vérifiés

1. **Ne jamais mélanger deux fenêtres.** Dans la session source, la répartition annoncée additionnait `200 × 98` (fenêtre de 299 lignes) et `301/400/401/404/502` (fenêtre de 815 lignes) : somme 752 au lieu de 815. Recouper `SOMME(statuts) == LIGNES_ANALYSEES`.
2. **Les lignes non reconnues sont silencieuses.** Un `tail -n 300` a rendu 299 lignes parsées : au moins une ligne (requête `"-"` ou ligne partielle en cours d'écriture) échappe à un motif exigeant `[A-Z]+`. Le script les compte (`IGNOREES`, `METHODES_NON_STANDARD`) au lieu de les perdre.
3. **Comparer des dates parsées, pas des chaînes.** `"01/Oct/..." >= "30/Sep/..."` est faux en comparaison lexicographique ; seuls les horodatages `datetime` donnent l'ordre réel.
4. **UTC, toujours.** L'heure des journaux et celle de la machine diffèrent ; l'utilisateur raisonne en UTC.
5. **Cloudflare masque l'origine.** Les 300 requêtes `/xmlrpc.php` se répartissaient sur deux IP Cloudflare (150/150) : ne pas attribuer le scan au visiteur de ces IP.
6. **Rotation.** Un `access.log` peut commencer à 00:02:40 ; pour une fenêtre plus large, lire `access.log.1` séparément, sans additionner des fenêtres.
7. **`error.log` tranche le 5xx.** Deux `upstream prematurely closed` au total : un 502 `POST /api/v1/dialogue` non reproduit, et une coupure client sur un téléchargement de 4,85 Mo — normal.
8. **Le trafic de test pollue les 400.** Les 400 sur `/api/v1/cyber/auditer` étaient des tests négatifs anti-SSRF, avec des 200 sur les cibles valides : le garde-fou fonctionne, ce n'est pas une régression.
9. **Git Bash réécrit les chemins Unix.** `--route "/favicon.ico"` arrive au script en `C:/Program Files/Git/favicon.ico` (MSYS convertit tout argument commençant par `/` en chemin Windows sous le préfixe d'installation Git) : sans correction, `ROUTE_REQUETES=0` alors que les lignes existent. Le script retire ce préfixe sur `--route`, `--chemin`, `--journal` ; ailleurs, utiliser `MSYS_NO_PATHCONV=1`. La réécriture est silencieuse — vérifier que `ROUTE=` affiche bien le chemin attendu.

## Checklist de sortie

- [ ] fenêtre UTC et objectif écrits avant lecture ;
- [ ] `RESULTAT=PASS` et `SOMME_OK=OUI` ;
- [ ] `IGNOREES` examiné ;
- [ ] `404_CLASSES` lu : scans séparés des `vrai_manque_candidat` et des `inconnu` ;
- [ ] chaque 5xx corrélé à `error.log` (`ERREURS_INTERPRETATIONS`) ;
- [ ] requêtes de vérification identifiées et listées ;
- [ ] après déploiement : `APRES`, `404_APRES` et `ROUTE` cités si demandés ;
- [ ] `IPS_CLOUDFLARE` signalé quand l'origine est masquée ;
- [ ] limite de fenêtre énoncée ;
- [ ] aucun secret affiché.

## Ressources

- `scripts/lire_journaux_nginx.py` — lecture SSH/sudo ou fichier local, une passe, contrôle de somme, triage automatique.
- `references/cas-verifie-2026-10-27.md` — cas réel, chiffres exacts et provenance de chaque constat.
