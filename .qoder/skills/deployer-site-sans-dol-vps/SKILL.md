---
name: deployer-site-sans-dol-vps
description: "Mettre à jour sans dolosif le site public al-mizan.world sur le VPS OVH : recenser les routes réellement servies par la passerelle, requalifier chaque allégation en opérationnel, simulé ou spécifié, valider en local les pages et le JavaScript inline, déployer une archive ciblée web_cloud et modules modifiés, appliquer des en-têtes nginx avec sauvegarde et retour arrière, puis vérifier le site en direct et dans les journaux. Utiliser pour corriger, publier ou vérifier www.al-mizan.world, le portail Al-Mizan, la passerelle VPS, une page du site ou une déclaration publique de l'écosystème."
---

# Publier une mise à jour véridique du site Al-Mizan

## Portée

Ce flux couvre la chaîne complète : audit des déclarations, correction des pages et des générateurs, validation locale, déploiement ciblé sur le VPS OVH, en-têtes nginx, puis vérification en direct. Il ne couvre ni la rédaction documentaire (`docs/`), ni le Tableau Maître, ni les sceaux mémoire.

## 1. Invariants

1. **Aucune allégation sans preuve reproductible.** Chaque affirmation affichée reçoit une étiquette : `opérationnel` (observé en direct), `simulé` (émulation logicielle), `spécifié` (paramètre de conception), ou `déclaré · non vérifié` (adresse, partenariat, liquidité).
2. **Corriger la source, pas seulement la page.** Les textes du dialogue et les compteurs sont souvent régénérés par des modules Python. Si le générateur garde l'ancienne formulation, la page la réintroduit.
3. **Toute écriture en production est réversible.** Sauvegarde horodatée avant remplacement, test de la configuration, chemin de restauration noté dans le rapport final.
4. **Demander confirmation avant le premier déploiement** d'un lot non trivial. Un accord une fois donné ne vaut pas pour les lots suivants.
5. **Secrets** : passer par `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\deploiement_vps\charger_credentials_ovh.py` (`hote_user_mdp()`), mot de passe uniquement via stdin de `sudo -S`. Ne jamais afficher, journaliser ni copier le secret dans un fichier du dépôt.
6. **La vérité des routes vient du code de la passerelle**, jamais du contenu du répertoire `web_cloud`.

## 2. Repères

Vérifier ces valeurs sur disque et sur le VPS avant de s'en servir ; elles peuvent avoir changé.

| Élément | Valeur constatée le 27/10/2026 |
| :--- | :--- |
| Source locale | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME` |
| Racine sur le VPS | `/opt/al-mizan/ASTRO-Q°ODE_SYSTEME` |
| Service applicatif | `al-mizan-api-vps` (systemd), joignable sur `127.0.0.1:8095` |
| Site nginx | `/etc/nginx/sites-available/al-mizan`, lié depuis `sites-enabled/al-mizan` |
| Credentials | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\secrets\ovh_vps_ssh.json` via `hote_user_mdp()` |
| Table des routes | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\docs\API_PASSERELLE_VPS.md` |
| Pages statiques | `web_cloud/*.html`, relues à chaque requête (aucun cache applicatif) |

## 3. Étape 1 — Recenser les routes réellement servies

Extraire les routes du routeur, puis les confronter à la production.

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
grep -n 'chemin in \[' passerelle_api_vps_mizan.py
grep -n 'def do_GET' -A 20 passerelle_api_vps_mizan.py
```

```bash
for p in / /tableau /livre-blanc /ponts /poupees /console /mentions-legales /video /unifie /favicon.ico /robots.txt /sitemap.xml; do
  printf '%-18s ' "$p"
  curl -sS -o /dev/null -w '%{http_code} %{content_type} %{size_download}\n' --max-time 20 "https://www.al-mizan.world$p"
done
```

Pièges constatés :

- `/unifie` et `/panneau` sont **générés en mémoire** : aucun fichier `unifie.html` n'existe.
- `/video` sert un MP4 (`web_cloud/al_mizan_promotion_youtube_1080p.mp4`), pas une page.
- Tous les accès directs du type `/livre_blanc_almizan.html` ou `/hub_ponts_synchrones.html` répondent **404** : seuls les alias de la table de routage fonctionnent. Ne jamais déduire une URL publique du nom de fichier.
- Le sitemap doit donc être construit depuis la table des routes, en `https://www.al-mizan.world/...`, et `robots.txt` doit exclure `/api/`, `/webhook/`, `/unifie`.

## 4. Étape 2 — Auditer puis requalifier chaque allégation

Construire un tableau `allégation → preuve → étiquette` avant toute réécriture. Contrôles qui ont réellement tranché :

| Allégation | Contrôle | Constat |
| :--- | :--- | :--- |
| DOI `10.5281/zenodo.23554838` | `https://doi.org/api/handles/<doi>`, Zenodo, DataCite | ne résout pas (handle 404) ; `23479740` et `23288947` résolvent |
| « QPU cryogénique 22,5 mK » | `module_diagnostic_materiel_et_realite.py` | `qubit_physique_local = False` → `QPU émulé logiciel`, température = paramètre de simulation |
| Pool Uniswap | adresse Basescan | adresse existe, liquidité non vérifiée → `adresse déclarée · non vérifiée` |
| « 185 lignes / 19 strates », « 61 modules » | recalcul sur `TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv` et comptage des `.py` | 216 lignes, 21 strates, 75 modules |
| « 95,41/100 », « 8 288 synapses », « 100 % », « INVIOLABLE » | recherche de source reproductible | aucune → retirer ou reformuler en simulation étiquetée |
| « ISO / NIST / CIS » | certificat | aucun → `référentiel visé, non certifié` |
| « propulsé par Gemini », « fragmentation nulle » | `noyau_logique_interactif_ia.py`, `moteur_intelligence_generative_vivante.py`, `agent_de_code_harmonisateur_mizan.py` | formulations codées en dur dans les générateurs, à corriger à la source |

Dispositifs éditoriaux à poser : bandeau de transparence, section `#transparence` listant les limites, métriques étiquetées, mentions légales complètes (directeur de publication, transfert éventuel vers un LLM externe, cookies, absence de conseil en investissement, jeton sans promesse de rendement ni de liquidité).

Après réécriture, rechercher les résidus avant de valider :

```bash
grep -rn "185\|19 strates\|61 modules\|95\.41\|8 ?288\|INVIOLABLE\|100 ?%" web_cloud/*.html
```

## 5. Étape 3 — Valider en local

### 5.1 Python

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
PYTHONIOENCODING=utf-8 py -3 -m py_compile passerelle_api_vps_mizan.py noyau_logique_interactif_ia.py moteur_intelligence_generative_vivante.py agent_de_code_harmonisateur_mizan.py
PYTHONIOENCODING=utf-8 py -3 -m unittest tests.test_passerelle_api_vps -v
```

Quand une reformulation véridique casse un test qui assertait l'ancienne phrase (constaté avec « millikelvins »), corriger l'assertion vers le nouveau texte honnête, jamais l'inverse. Rejouer la suite complète et citer le décompte réellement observé.

### 5.2 JavaScript inline

Le premier bloc `<script>` d'une page peut être du JSON-LD : `new Function` y échoue avec `Unexpected token ':'`. Filtrer sur `type`, puis compiler le reste.

```bash
node -e "
const fs=require('fs');
const html=fs.readFileSync('ASTRO-Q°ODE_SYSTEME/web_cloud/portail_public_al_mizan.html','utf8');
const m=[...html.matchAll(/<script(?![^>]*src=)([^>]*)>([\s\S]*?)<\/script>/g)];
let n=0;
for (const x of m) {
  if (/ld\+json/.test(x[1])) { try { JSON.parse(x[2]); console.log('json-ld OK'); } catch(e) { console.log('json-ld ERR', e.message); } continue; }
  try { new Function(x[2]); n++; } catch(e) { console.log('script ERR', e.message); }
}
console.log('scripts JS inline valides:', n);
const ids=[...html.matchAll(/\bid=\"([^\"]+)\"/g)].map(x=>x[1]);
console.log('ids dupliques:', [...new Set(ids.filter((v,i)=>ids.indexOf(v)!==i))]);
"
```

### 5.3 Passerelle locale

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
nohup env PYTHONIOENCODING=utf-8 py -3 passerelle_api_vps_mizan.py --port 18095 > ./.qoder_tmp_gw.log 2>&1 &
sleep 4
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18095/api/v1/sante
```

Utiliser `18095` pour les tests d'API afin d'ignorer une instance déjà présente. N'utiliser `8095` que si un passage navigateur exige le port exact et qu'il est libre. Arrêter ensuite :

```bash
pid=$(netstat -ano | grep ":18095" | grep LISTENING | awk '{print $5}' | head -1)
if [ -n "$pid" ]; then taskkill //F //PID "$pid"; fi
```

Contrôles navigateur : ouvrir chaque route, relever les messages de console, vérifier un élément de preuve par page (identifiant de métrique, bannière, nombre de scénarios simulés). Une page qui s'affiche sans erreur de console ne prouve pas son contenu : contrôler aussi le texte.

### 5.4 Anti-SSRF

L'endpoint d'audit ne doit accepter que `http`/`https` sur 80/443 vers des IP publiques. Tester les refus, pas seulement le succès :

```bash
PYTHONIOENCODING=utf-8 py -3 -c "
from passerelle_api_vps_mizan import valider_cible_audit_publique as v
for u in ['http://127.0.0.1:8095/','http://localhost/','http://169.254.169.254/','http://10.0.0.1/','http://[::1]/','http://[::ffff:127.0.0.1]/','ftp://example.com/','https://example.com:8443/','https://user:pass@example.com/','http://100.64.0.1/']:
    print(u, v(u))
"
```

Attendu : refus pour chaque variante privée, loopback, link-local, port non standard et schéma non http(s).

## 6. Étape 4 — Déployer une archive ciblée

**Ne pas réutiliser `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\deploiement_vps\mettre_a_jour_site_web_ovh.py` tel quel** : il archive tous les `*.py` de la racine. Construire une archive limitée à `web_cloud` (hors `.mp4` et `__pycache__`) et aux modules modifiés.

```python
from pathlib import Path
import tarfile

RACINE = Path(r"C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME")
MODULES = ["passerelle_api_vps_mizan.py", "noyau_logique_interactif_ia.py",
           "moteur_intelligence_generative_vivante.py", "agent_de_code_harmonisateur_mizan.py"]
ARCHIVE = Path("./.qoder_tmp_site.tar.gz")

with tarfile.open(ARCHIVE, "w:gz") as tar:
    for nom in MODULES:
        tar.add(RACINE / nom, arcname=nom)
    for f in (RACINE / "web_cloud").rglob("*"):
        if f.is_file() and "__pycache__" not in f.parts and f.suffix not in (".pyc", ".mp4"):
            tar.add(f, arcname=str(f.relative_to(RACINE)).replace("\\", "/"))
print(ARCHIVE, ARCHIVE.stat().st_size)
```

Transfert et installation distante (paramiko, `sftp.put` vers `/tmp`, puis commande unique) :

```bash
set -e
mkdir -p "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME"
tar -xzf /tmp/al_mizan_update.tar.gz -C "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME"
chown -R ubuntu:ubuntu "/opt/al-mizan/ASTRO-Q°ODE_SYSTEME"
rm -f /tmp/al_mizan_update.tar.gz
systemctl restart al-mizan-api-vps
sleep 4
systemctl is-active al-mizan-api-vps
systemctl is-active nginx
curl -s -o /dev/null -w "portail=%{http_code} " http://127.0.0.1:8095/
curl -s -o /dev/null -w "livre=%{http_code}\n" http://127.0.0.1:8095/livre-blanc
```

Exécuter via `sudo -S bash -c '<commande>'` en écrivant le mot de passe sur stdin.

Pour un correctif d'un seul fichier, comparer avant d'écraser : télécharger la version distante, produire un `difflib.unified_diff`, relever `stat -c '%U %G %a'` sur le fichier distant, sauvegarder en `<fichier>.bak-<horodatage>`, puis réinstaller avec **ces** valeurs — constaté `ubuntu ubuntu 666` pour la passerelle et `644` pour `favicon.ico`. Ne pas imposer `644` par défaut : la passerelle tourne avec un mode plus ouvert. Redémarrer, puis vérifier l'égalité SHA-256 local/distant : un 200 public ne prouve pas que le fichier servi est celui qui vient d'être envoyé.

```bash
ts=$(date +%Y%m%d-%H%M%S)
read -r u g m <<<"$(stat -c '%U %G %a' "$FICHIER")"
cp -a "$FICHIER" "$FICHIER.bak-$ts" && install -o "$u" -g "$g" -m "$m" "$TMP" "$FICHIER" && rm -f "$TMP"
systemctl restart al-mizan-api-vps
sha256sum "$FICHIER"
```

Retour arrière : réinstaller `"$FICHIER.bak-<ts>"` avec les mêmes `-o`/`-g`/`-m`, redémarrer, revérifier le hash et les routes. Relever le SHA-256 de la sauvegarde au moment où elle est créée : sans ce hash, une restauration ne prouve rien.

Nettoyer l'archive temporaire locale et distante à la fin ; noter le chemin de sauvegarde dans le rapport.

### Contrôles après redémarrage

`systemctl is-active` peut répondre `active` alors que la nouvelle route échoue : contrôler les statuts, les types et l'authentification.

```bash
for p in /api/v1/webhooks /api/v1/unifie /api/v1/audit/paiements /api/v1/sante / /video; do
  curl -s -o /dev/null -w "$p %{http_code} %{content_type}\n" "http://127.0.0.1:8095$p"
done
curl -s -o /dev/null -w "sans_jeton %{http_code}\n" -X POST -H 'Content-Type: application/json' -d '{}' http://127.0.0.1:8095/api/v1/commande
```

Attendus constatés : les six routes en 200, `/video` en `video/mp4`, et `POST /api/v1/commande` sans jeton en **401**. Avec le jeton et une action inexistante, la réponse est **400** (`Action inconnue`) : c'est ainsi qu'on vérifie l'authentification sans déclencher de commande réelle. Côté public, contrôler `/video`, les six en-têtes de sécurité sur `/` et, si un favicon est déployé, `200 image/x-icon`, `Cache-Control: public, max-age=604800` et les quatre premiers octets `00 00 01 00`.

## 7. Étape 5 — En-têtes nginx avec retour arrière

Modifier uniquement le bloc `server` du site, jamais la configuration TLS générée par Certbot.

1. Lire le fichier vivant par SFTP.
2. Si `Strict-Transport-Security` est déjà présent, s'arrêter (opération idempotente).
3. Insérer les en-têtes après un ancrage stable (`client_max_body_size 50M;`). Si l'ancrage manque, abandonner au lieu de deviner.
4. `cp -a <site> <site>.bak-AAAAMMJJ`, puis `install -m 644 -o root -g root`.
5. `nginx -t` ; en cas d'échec, restaurer la sauvegarde et ne pas recharger.
6. `systemctl reload nginx` seulement si `nginx -t` passe.

Bloc appliqué (HSTS, nosniff, X-Frame-Options, Referrer-Policy, Permissions-Policy, CSP autorisant scripts et styles inline ainsi que les polices Google). Vérifier ensuite les en-têtes réellement servis et le score d'auto-audit du site (50 → 98/100 lors de la session).

## 8. Étape 6 — Vérifier en direct

- **Égalité de contenu** : pour chaque route, télécharger, calculer SHA-256 et comparer au fichier local. Les pages lues en mode texte par la passerelle diffèrent en brut (CRLF Windows → LF) : normaliser avant de conclure, et dire explicitement quelles routes sont identiques en brut et lesquelles seulement après normalisation.
- **Routes** : tous les statuts 200 attendus, favicon `image/x-icon`, aucun 404 sur les alias.
- **En-têtes** : les six en-têtes présents sur `/`.
- **Dialogue** : réponse fonctionnelle et honnête (aucun matériel quantique physique revendiqué).
- **Console** : scénarios simulés générés, aucune erreur JavaScript.
- **Journaux** : déléguer à `verifier-journaux-nginx-vps` (fenêtre datée, statuts, dernier 404, scans de robots distingués des incidents). Ne conclure « aucun 404 » qu'avec une fenêtre temporelle explicite.

Rapport final : tableau `changement → preuve → étiquette`, sauvegardes disponibles, commande de restauration, et liste explicite de ce qui reste non vérifié.

## 9. Pièges Windows constatés

- **Chemin contenant `°`** : `cd ".../ASTRO-Q*ODE_SYSTEME"` échoue en `No such file or directory` alors que le chemin littéral fonctionne. Utiliser le chemin exact, ou les outils Read/Glob.
- **Console cp1252** : imprimer du texte accentué ou des caractères de cadre lève `UnicodeEncodeError`. Exporter `PYTHONIOENCODING=utf-8` ; pour inspecter des caractères exacts, afficher `ligne.encode('unicode_escape').decode('ascii')`.
- **`/tmp` non partagé** : un fichier créé par `curl -o /tmp/x.json` n'est pas vu par un processus Python qui ouvre `/tmp/x.json` (`FileNotFoundError`). Écrire les temporaires dans le workspace (`./.qoder_tmp_x.json`) et les supprimer.
- **Art ASCII** : les espaces de tête sont significatifs. Afficher les lignes exactes avant toute édition et copier la sous-chaîne depuis la sortie, sans la retaper.
- **Port occupé** : une instance précédente reste à l'écoute. Identifier le PID (`netstat -ano | grep ":PORT" | grep LISTENING`) puis `taskkill //F //PID`.
- **Interpréteur** : utiliser `py -3` ; l'alias Microsoft Store de `python` peut échouer.
- **`$USER` sous sudo** : dans `sudo -S bash -c '...'`, `$USER` vaut l'utilisateur cible (`root`), pas `ubuntu`. Écrire l'utilisateur applicatif en clair et vérifier avec `stat -c '%U %G %a'`.
- **Horodatage de sauvegarde** : le calculer sur le serveur (`date +%Y%m%d-%H%M%S`), pas avec l'horloge locale, pour que le nom `.bak-<ts>` se situe dans les journaux du VPS.
- **Paramiko** : sur une commande bavarde, lire `stdout`/`stderr` avant `recv_exit_status()`. Les scripts de la session appelaient `recv_exit_status()` d'abord et ne passaient que parce que la sortie restait courte.
- **Nettoyage** : supprimer le temporaire `/tmp` dans la même commande que l'installation et la copie distante du workspace (`./.qoder/tmp/remote_*.py`) après le diff.

## Ressources

- `references/preuves-session-2026-10-27.md` — commandes, sorties et horodatages de la session d'origine, avec distinction vérifié / non vérifié.
- `verifier-journaux-nginx-vps` — tri des journaux nginx (délégation de l'étape 6).
- `skill-file-qa` — validation post-écriture de ce Skill (frontmatter, références, blocs de code).
