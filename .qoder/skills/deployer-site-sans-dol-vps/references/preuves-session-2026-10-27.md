# Preuves — session « Mettre à jour le site web » (27/10/2026)

Référence pour l'étape 1 (routes), l'étape 2 (allégations) et le déploiement. Chaque constat est relié à la commande et à la sortie observées. Les éléments non reproductibles sont marqués **non vérifié**.

## Source

| Élément | Valeur |
| :--- | :--- |
| Session | `55f63550-7c8d-4f9e-b0a9-e73686cc2765`, titre « Mettre à jour le site web » |
| État au moment de l'audit | `runtimeState = cold`, `revision = 0`, `activeTurnId = null` |
| Snapshot `read_chat_session` | 16 messages, `hasMoreBefore = true`, `turnLimit` 20 — ne couvre que les 8 dernières demandes |
| JSONL du projet | `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\55f63550-7c8d-4f9e-b0a9-e73686cc2765.jsonl`, 2 383 lignes, 5 030 131 octets |
| Demandes humaines | 9, de 00:45:57 UTC à 01:56:53 UTC le 27/10/2026 |

Les tours antérieurs au snapshot ont été lus dans le JSONL, pas dans le snapshot. Les heures ci-dessous proviennent des horodatages des messages ; les heures de journaux nginx sont en UTC.

## Demandes humaines (verbatim)

1. 00:45:57 — « mets a jour mon site web https://www.al-mizan.world/ sans dolosif et jusqu'a la complétude et l'harmonie »
2. 01:17:27 — « les modifications sont bien prises en compte sur le site »
3. 01:23:14 — « merci pour la vérification détaillée »
4. 01:37:40 — « commencer la rédaction de la documentation technique pour les développeurs »
5. 01:43:54 — « déployer les correctifs sur le VPS »
6. 01:46:40 — « Vérifier le fichier de log nginx pour confirmer les requêtes récentes »
7. 01:52:13 — « Générer un favicon.ico et ajouter la route 204 »
8. 01:56:14 — « Voir les logs nginx pour confirmer l'absence de 404 »
9. 01:56:53 — « Les 404 sont résolus, on peut considérer cette tâche comme terminée. »

La demande 1 contient toute la refonte ; c'est elle que le Skill encode. Les demandes 5 à 9 documentent le déploiement, la lecture des journaux et l'ajout du favicon. La seule interaction de confirmation est un `AskUserQuestion` avant le déploiement du favicon (réponse : « Oui, déployer »).

## Étape 1 — routes réellement servies

Commande (extrait de la session) :

```bash
for p in /comptoir_gre_a_gre.html /paiement_mobile.html /monitoring_cybersecurite.html \
         /orchestrateur_qcs_harmonie.html /ia_autonome_boucle_fermee.html \
         /reception_devises_fiat.html /enchere_personnalisee.html \
         /cartographie_poupees_1_a_27.html /hub_ponts_synchrones.html \
         /livre_blanc_almizan.html /mentions_legales.html \
         /tableau_maitre_sequentiel.html /console /unifie; do
  printf '%-42s ' "$p"
  curl -sS -o /dev/null -w '%{http_code}\n' --max-time 15 "https://www.al-mizan.world$p"
done
```

Sortie observée : les douze chemins `*.html` répondent **404** ; `/console` et `/unifie` répondent **200**. Conclusion : les URLs publiques sont les alias du routeur, pas les noms de fichiers.

Contrôles internes au VPS après déploiement :

```text
portail=200 livre=200 ponts=200 console=200 legal=200
```

Table des routes établie dans `docs/API_PASSERELLE_VPS.md` : `/` (portail), `/tableau`, `/livre-blanc`, `/ponts`, `/video` (MP4), `/poupees`, `/console`, `/mentions-legales`, `/robots.txt`, `/sitemap.xml`, `/favicon.ico`, `/unifie` (HTML généré en mémoire). Les autres pages du répertoire ne sont pas exposées.

## Étape 2 — allégations

### DOI

```text
10.5281/zenodo.23554838  -> handle introuvable (404 côté Handle, Zenodo et DataCite)
10.5281/zenodo.23479740  -> résout
10.5281/zenodo.23288947  -> résout
```

Le DOI non résolvable a été retiré du portail et du livre blanc ; celui conservé est `23479740`.

### Matériel

`module_diagnostic_materiel_et_realite.py` déclare `qubit_physique_local = False`. Les mentions « QPU cryogénique 22,5 mK » sont devenues « QPU émulé logiciel », la température et le consensus 2,9 ms étant requalifiés en paramètres de conception.

### Compteurs

| Affiché avant | Recalculé | Source |
| :--- | :--- | :--- |
| 185 lignes, 19 strates | 216 lignes, 21 strates | `TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv` (`SEQ` 001→216) |
| 61 modules | 75 | comptage des modules du système |
| 95,41/100, 8 288 synapses | aucune source reproductible | retirés ou reformulés |

### Générateurs

Les formulations « propulsé par Gemini », « fragmentation nulle » et les chiffres non prouvés étaient codés dans `noyau_logique_interactif_ia.py`, `moteur_intelligence_generative_vivante.py` et `agent_de_code_harmonisateur_mizan.py`. Les corriger dans la page seule ne suffisait pas : les routes régénèrent le texte.

## Étape 3 — validation locale

### JavaScript inline

```text
scripts inline: 2
script 0 ERR Unexpected token ':'
script 1 OK 29637
duplicate ids: []
section open/close: 4 4
```

`script 0` est le bloc JSON-LD : `new Function` ne peut pas le compiler. Il doit être analysé avec `JSON.parse`, pas compté comme une erreur JavaScript.

### Anti-SSRF

```text
https://www.al-mizan.world/        -> (True, '', '2607:5300:205:200::e809')
http://127.0.0.1:8095/             -> (False, 'Port non autorisé (80 ou 443 uniquement).', '')
http://localhost/                  -> (False, 'Cible non publique refusée (127.0.0.1).', '')
http://169.254.169.254/...         -> (False, 'Cible non publique refusée (169.254.169.254).', '')
http://10.0.0.1/                   -> (False, 'Cible non publique refusée (10.0.0.1).', '')
http://[::ffff:127.0.0.1]/         -> (False, 'Cible non publique refusée (::ffff:127.0.0.1).', '')
```

Les formes `http://2130706433/`, `http://0x7f000001/` et `http://0177.0.0.1/` échouent en résolution DNS (`getaddrinfo failed`) : refusées, mais pas par la règle IP — le noter tel quel dans un rapport.

Contrôle live sur l'API publique :

```text
https://www.al-mizan.world -> 200 score=50
http://127.0.0.1:80        -> 400 Cible refusée : Cible non publique refusée (127.0.0.1).
http://169.254.169.254     -> 400 Cible refusée : Cible non publique refusée (169.254.169.254).
```

## Étape 4 — déploiement

Archive ciblée : `web_cloud` (hors `.mp4`, hors `__pycache__`/`.pyc`) et quatre modules. Sortie du script :

```text
archive=al_mizan_update_sans_dol.tar.gz taille=4780.0 Ko
transfert=ok
exit= 0
active
active
portail=200 livre=200 ponts=200 console=200 legal=200
```

Le script `deploiement_vps/mettre_a_jour_site_web_ovh.py` n'a pas été réutilisé : il archive l'ensemble des `*.py` de la racine.

Correctif de passerelle déployé séparément : téléchargement de la version distante, `difflib.unified_diff` (seules les quatre corrections différaient), sauvegarde `.bak-<horodatage UTC>`, installation en conservant l'utilisateur, redémarrage, contrôles internes :

```text
/api/v1/webhooks -> 200, /api/v1/unifie -> 200, /api/v1/audit/paiements -> 200,
/video -> 200 video/mp4, POST /api/v1/commande sans jeton -> 401
```

### Correctifs d'un fichier — sorties observées

Deux déploiements unitaires, chacun avec diff, sauvegarde, hash et contrôles.

| Élément | Valeur observée |
| :--- | :--- |
| Version distante avant correctif | 62 880 o, SHA-256 `e67356da93863adf08aac96970a65d38f8f72a948e79e33d6800741d7bf3a2c7`, 1 302 lignes |
| Correctif local | SHA-256 `122acc22ce051124c028768017236c3677a2abb8c0dc1408a73add10268955e8` |
| Diff | 43 lignes, 4 corrections : import `shutil` ajouté, contournement de session retiré, `code=` → `statut_code=` (2 occurrences), import local `asdict` retiré |
| Propriétaire et mode lus avant installation | `ubuntu ubuntu 666` |
| Sauvegarde | `passerelle_api_vps_mizan.py.bak-20261027-014445` |
| Hash distant après installation | `122acc22…` (égal au local) |
| Contrôles internes | `webhooks=200 unifie=200 audit=200 sante=200 accueil=200 video=200/video/mp4 commande_sans_jeton=401` |

En-têtes publics et authentification, même passage :

```text
HSTS True / CSP True / XCTO nosniff / XFO SAMEORIGIN / Referrer strict-origin-when-cross-origin / Permissions True
commande sans jeton -> 401
commande avec jeton (action inconnue) -> 400 "Action inconnue"
/video public -> 200 video/mp4 3 554 562 octets
```

Second déploiement (favicon et route 204) :

| Élément | Valeur observée |
| :--- | :--- |
| Passerelle | `472dad9da4ca47a9eb0b8f154152347e79d40303efa5b9e53373054e9dccc595`, sauvegarde `.bak-20261027-015529` |
| Favicon | 8 377 o, `2f0aa19c6a5f912daafe5d77820bd74bf97e09b94765e98ea89ef6cc12426f5d`, `ubuntu ubuntu 644` |
| Interne | 200 `image/x-icon`, `Content-Length: 8377`, `Cache-Control: public, max-age=604800`, magic `00000100` |
| Public | 200 `image/x-icon` len=8377, idem avec `?v=20261027` |
| Smoke public | `/` 200, `/api/v1/sante` 200, `/api/v1/webhooks` 200, `/api/v1/unifie` 200, `/api/v1/audit/paiements` 200, `/favicon.ico` 200, POST sans jeton 401 |

Le premier script lisait `stat -c '%U %G %a'` ; le second a codé `666` pour la passerelle et `644` pour le favicon. Conserver la lecture `stat`, qui reste juste si le mode change.

## Étape 5 — nginx

```text
$ ls -l /etc/nginx/sites-enabled/
lrwxrwxrwx 1 root root 35 Oct 24 19:29 al-mizan -> /etc/nginx/sites-available/al-mizan

backup 0
install 0
nginx -t 0  nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
            nginx: configuration file /etc/nginx/nginx.conf test is successful
reload 0
```

En-têtes constatés en direct après rechargement : `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy`. Le fichier modifié est celui du site ; la configuration TLS de Certbot n'a pas été touchée. Score d'auto-audit : 50 avant, 98/100 après.

## Étape 6 — vérification en direct

Égalité de contenu (`/`, `/livre-blanc`, `/ponts`, `/console`, `/mentions-legales`, `/tableau`, `/robots.txt`, `/sitemap.xml`) : six routes identiques octet pour octet ; `/`, `/livre-blanc` et `/tableau` identiques après normalisation CRLF→LF, car la passerelle lit ces fichiers en mode texte.

Favicon après déploiement :

```text
/favicon.ico -> 200 image/x-icon len=8377
```

Journaux nginx, fenêtre 00:02 → 01:55:44 UTC, 836 requêtes : 12 requêtes sur `/favicon.ico`, dont 7 × 404 et 2 × 301 avant 01:14:40 UTC, puis 3 × 200 à partir de 01:55:32. Après 01:55:31 : 11 requêtes, 10 × 200, 1 × 401, aucun 404.

## Pièges Windows — sorties brutes

```text
wc: ASTRO-Q°ODE_SYSTEME/web_cloud/portail_public_al_mizan.html: No such file or directory
grep: ASTRO-Q°ODE_SYSTEME/web_cloud/serveur_cloud_ihm_mizan.py: No such file or directory
```

```text
/usr/bin/bash: line 1: cd: C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q*ODE_SYSTEME: No such file or directory
sha256sum: 'ASTRO*SYSTEME/passerelle_api_vps_mizan.py': No such file or directory
```

```text
File "…\encodings\cp1252.py", line 19, in encode
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 391
```

```text
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/dlg2.json'
```

Le fichier avait été écrit par `curl -o /tmp/dlg2.json` dans Git Bash ; le processus Python ne voyait pas le même chemin. Le passage suivant a écrit `./.qoder_tmp_dlg.json` dans le workspace.

## Points non vérifiés

- Le raisonnement de recommandation mentionnait un `Edit` échouant sur l'art ASCII à cause d'un espace de tête. Aucun résultat d'erreur `Edit` n'existe dans le JSONL : la séquence observée est un `repr` qui casse en cp1252, puis un affichage `unicode_escape` des lignes, puis des `Edit` réussis. Ne pas affirmer l'échec.
- Le décompte des tests a évolué au fil de la session (4/4 télémétrie, 8/8 passerelle, 10/10 après favicon). Citer le décompte de l'exécution réelle, pas un chiffre mémorisé.
- Aucun horodatage des commandes de déploiement n'apparaît dans les sorties ; seules les heures de journaux et des messages sont datées. Ne pas inventer de fenêtre.
- Le retour arrière n'a jamais été exécuté : les deux sauvegardes existent, mais aucune restauration n'a été testée en production.
- Le repli 204 du favicon n'est couvert que par un test unitaire (`test_09_favicon_absent_repond_204`), pas par une observation en production.
- Les scripts appelaient `recv_exit_status()` avant de lire les flux ; aucun blocage n'a été observé, la sortie restant courte. Le conseil de lire d'abord est une prévention, pas un incident constaté.
