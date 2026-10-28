---
name: deployer-site-sans-dol-vps
description: "Mettre à jour sans dolosif le site public al-mizan.world sur le VPS OVH : recenser les routes réellement servies par la passerelle, requalifier chaque allégation en opérationnel, simulé ou spécifié, valider en local les pages et le JavaScript inline, déployer un lot cohérent de pages et de JSON d'API (ex. œuvre universelle), un lot mixte de fichiers existants et nouveaux, ou une archive ciblée web_cloud et modules modifiés, appliquer des en-têtes nginx avec sauvegarde et retour arrière, puis vérifier le site en direct et dans les journaux, y compris un triage de journaux illisible sans sudo. Utiliser pour corriger, publier ou vérifier www.al-mizan.world, le portail Al-Mizan, la passerelle VPS, une page du site, l'œuvre universelle ou une déclaration publique de l'écosystème."
---

# Publier une mise à jour véridique du site Al-Mizan

## Portée

Ce flux couvre la chaîne complète : audit des déclarations, correction des pages et des générateurs, validation locale, déploiement ciblé sur le VPS OVH, en-têtes nginx, puis vérification en direct. Il ne couvre ni la rédaction documentaire (`docs/`), ni le Tableau Maître, ni les sceaux mémoire.

## 1. Invariants

1. **Aucune allégation sans preuve reproductible.** Chaque affirmation affichée reçoit une étiquette : `opérationnel` (observé en direct), `simulé` (émulation logicielle), `spécifié` (paramètre de conception), ou `déclaré · non vérifié` (adresse, partenariat, liquidité).
2. **Corriger la source, pas seulement la page.** Les textes du dialogue et les compteurs sont souvent régénérés par des modules Python. Si le générateur garde l'ancienne formulation, la page la réintroduit.
3. **Toute écriture en production est réversible — et la réversibilité se prouve avant d'écrire.** Sauvegarde horodatée dont l'existence est vérifiée : archive non vide, `BACKUP_FICHIERS > 0`, SHA-256 relevé et `tar -tzf` recoupé avec la liste. Un compte nul arrête l'opération avant toute extraction. Chemin de restauration noté dans le rapport final.
4. **Demander confirmation avant le premier déploiement** d'un lot non trivial. Un accord une fois donné ne vaut pas pour les lots suivants.
5. **Secrets et sudo** : passer par `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\deploiement_vps\charger_credentials_ovh.py` (`hote_user_mdp()`). Sur ce VPS, `ubuntu` dispose de sudo NOPASSWD (`sudo -n true` → 0 constaté le 28/10/2026 ; à revérifier à chaque session) : exécuter les commandes privilégiées avec `sudo -n`, sans stdin. Ne jamais envoyer le mot de passe à `sudo -S` avec `bash -s` : il est exécuté comme une commande et recraché dans stderr. Ne jamais afficher, journaliser ni copier le secret dans un fichier du dépôt.
6. **La vérité des routes vient du code de la passerelle**, jamais du contenu du répertoire `web_cloud`.
7. **Un lot page + API est atomique.** Une page publique et les JSON consommés par son API (ex. `oeuvre-universelle` : 3 pages + `resume.json` + `manifeste_anteriorite.json`) se déploient avec la même sauvegarde et la même vérification. Déployer une seule page crée une divergence entre ce que lit l'utilisateur et ce que renvoie l'API.
8. **Un journal vide ou illisible est INCONCLUSIF.** Une lecture sans sudo peut rendre `LINES 0` avec un code 0 et un stderr vide ; ce n'est pas une preuve d'absence de 5xx. Lire les journaux avec `sudo -n` et ne conclure qu'avec une fenêtre et un décompte lisibles.
9. **Une liste de chemins traversant Windows → VPS est en LF.** L'écrire en octets (`write_bytes`, jointure `b"\n"`), jamais avec `write_text` qui traduit en `\r\n` sous Windows ; côté distant, retirer un `\r` final avant tout usage. Une liste corrompue produit une sauvegarde vide, pas une erreur visible.
10. **L'ordre tests → génération → déploiement est imposé, et une seule racine Merkle doit coïncider partout.** La suite œuvre rescelle le manifeste sans réécrire les pages ; lancée après génération, elle laisse les pages sur l'ancienne racine. `--verifier` reste vert car il compare les hachages des fichiers au manifeste stocké. Exiger la même racine dans les trois pages, `resume.json`, le manifeste et l'API.

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
| Lot œuvre universelle | `web_cloud/oeuvre_universelle{,_en,_ar}.html` + `resultats/oeuvre_universelle/{resume,manifeste_anteriorite}.json` ; routes `/oeuvre-universelle[/en\|/ar]` et `/api/v1/oeuvre-universelle[/manifeste]` |

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
LISTE = Path("./.qoder_tmp_liste.txt")

noms = list(MODULES)
for f in (RACINE / "web_cloud").rglob("*"):
    if f.is_file() and "__pycache__" not in f.parts and f.suffix not in (".pyc", ".mp4"):
        noms.append(str(f.relative_to(RACINE)).replace("\\", "/"))

with tarfile.open(ARCHIVE, "w:gz") as tar:
    for nom in noms:
        tar.add(RACINE / nom, arcname=nom)
LISTE.write_bytes(("\n".join(noms) + "\n").encode("utf-8"))
print(ARCHIVE, ARCHIVE.stat().st_size, "fichiers", len(noms))
```

Transférer l'archive et la liste (`sftp.put` vers `/tmp/al_mizan_update.tar.gz` et `/tmp/al_mizan_liste.txt`) via paramiko. `write_bytes` est obligatoire : `write_text` produit des `\r\n` sous Windows (invariant 9).

**Phase A — sauvegarde.** Remplacer `23` par le compte imprimé localement, puis exécuter via `sudo -n bash -c '<commande>'` :

```bash
set -euo pipefail
RACINE=/opt/al-mizan/ASTRO-Q°ODE_SYSTEME
TS=$(date +%Y%m%d-%H%M%S)
DEST=/opt/al-mizan/sauvegardes/lot-$TS
LISTE=/tmp/al_mizan_liste.txt
ATTENDU=23
mkdir -p "$DEST"

test "$(tr -cd '\r' < "$LISTE" | wc -c)" -eq 0 || { echo "STOP liste CRLF"; exit 2; }
test "$(wc -l < "$LISTE")" -eq "$ATTENDU" || { echo "STOP liste incomplete"; exit 2; }

: > "$DEST/FICHIERS"
: > /tmp/al_mizan_modes.txt
while IFS= read -r f; do
  f=${f%$'\r'}
  [ -n "$f" ] || continue
  if [ -e "$RACINE/$f" ]; then
    printf '%s\n' "$f" >> "$DEST/FICHIERS"
    stat -c '%n|%U|%G|%a' "$RACINE/$f" >> /tmp/al_mizan_modes.txt
  fi
done < "$LISTE"

BACKUP_FICHIERS=$(wc -l < "$DEST/FICHIERS")
if [ "$BACKUP_FICHIERS" -eq 0 ]; then
  echo "STOP sauvegarde vide : liste corrompue ou lot purement additif"
  exit 3
fi
tar -czf "$DEST/sauvegarde.tar.gz" -C "$RACINE" -T "$DEST/FICHIERS"
test "$(tar -tzf "$DEST/sauvegarde.tar.gz" | wc -l)" -eq "$BACKUP_FICHIERS"
echo "BACKUP $DEST/sauvegarde.tar.gz"
echo "BACKUP_FICHIERS $BACKUP_FICHIERS"
sha256sum "$DEST/sauvegarde.tar.gz"
cat /tmp/al_mizan_modes.txt
```

Un lot purement additif rend `BACKUP_FICHIERS 0` : ce compte seul ne prouve pas que la liste est saine. Prouver par `stat` qu'aucun chemin n'existe et traiter l'ajout comme un cas distinct ; sinon arrêter.

**Phase B — extraction.** Exporter le `TS` imprimé par la phase A (le bloc refuse de tourner sans lui) ; la phase refuse d'écrire si la sauvegarde ou la table des modes n'est pas vérifiable :

```bash
set -euo pipefail
RACINE=/opt/al-mizan/ASTRO-Q°ODE_SYSTEME
: "${TS:?reprendre le TS imprime par la phase A}"
DEST=/opt/al-mizan/sauvegardes/lot-$TS
test -s "$DEST/sauvegarde.tar.gz" || { echo "STOP sauvegarde absente"; exit 4; }
test "$(wc -l < "$DEST/FICHIERS")" -gt 0 || { echo "STOP manifeste vide"; exit 4; }
test "$(tar -tzf "$DEST/sauvegarde.tar.gz" | wc -l)" -eq "$(wc -l < "$DEST/FICHIERS")"
test -f /tmp/al_mizan_modes.txt || { echo "STOP table des modes absente (phase A)"; exit 5; }
test "$(wc -l < /tmp/al_mizan_modes.txt)" -eq "$(wc -l < "$DEST/FICHIERS")" || { echo "STOP table des modes incoherente"; exit 5; }

tar -tzf /tmp/al_mizan_update.tar.gz > /tmp/al_mizan_extraits.txt
: > /tmp/al_mizan_plan_modes.txt
while IFS= read -r f; do
  ligne=$(grep -F "/$f|" /tmp/al_mizan_modes.txt | head -1 || true)
  if [ -n "$ligne" ]; then
    u=$(echo "$ligne" | cut -d'|' -f2); g=$(echo "$ligne" | cut -d'|' -f3); m=$(echo "$ligne" | cut -d'|' -f4)
  else
    e=${f##*.}
    ref=$(find "$RACINE/$(dirname "$f")" -maxdepth 1 -type f -name "*.$e" ! -name "$(basename "$f")" | head -1 || true)
    u=ubuntu; g=ubuntu
    if [ -n "$ref" ]; then m=$(stat -c '%a' "$ref"); else case "$e" in html) m=666;; *) m=644;; esac; fi
  fi
  printf '%s|%s|%s|%s\n' "$f" "$u" "$g" "$m" >> /tmp/al_mizan_plan_modes.txt
done < /tmp/al_mizan_extraits.txt

tar -xzf /tmp/al_mizan_update.tar.gz -C "$RACINE"
while IFS='|' read -r f u g m; do
  chown "$u:$g" "$RACINE/$f" && chmod "$m" "$RACINE/$f"
done < /tmp/al_mizan_plan_modes.txt
(cd "$RACINE" && xargs -d '\n' stat -c '%n|%U|%G|%a' < /tmp/al_mizan_extraits.txt)
if grep -q '\.py$' /tmp/al_mizan_extraits.txt; then
  systemctl restart al-mizan-api-vps
  sleep 4
  systemctl is-active al-mizan-api-vps
fi
rm -f /tmp/al_mizan_update.tar.gz /tmp/al_mizan_extraits.txt /tmp/al_mizan_modes.txt /tmp/al_mizan_plan_modes.txt
systemctl is-active nginx
curl -s -o /dev/null -w "portail=%{http_code} " http://127.0.0.1:8095/
curl -s -o /dev/null -w "livre=%{http_code}\n" http://127.0.0.1:8095/livre-blanc
```

Le `chown`/`chmod` ne couvre que les chemins extraits : un `chown -R` sur la racine changerait aussi les fichiers hors lot. Ne redémarrer que si la liste contient un `.py` ; les pages et JSON sont relus à chaque requête.

### Lot mixte — fichiers existants et nouveaux

Un lot peut mêler des fichiers déjà présents et des ajouts (constaté le 28/10/2026 : 19 fichiers, `BACKUP_FICHIERS 13`, 6 nouveaux). La phase A relève `stat -c '%n|%U|%G|%a'` pour chaque fichier existant ; la phase B décide **avant** extraction, applique après, puis imprime les modes obtenus.

Règles de décision, dans cet ordre :

1. Chemin présent dans `/tmp/al_mizan_modes.txt` : reprendre `u`, `g`, `m` relevés.
2. Chemin nouveau : `ubuntu:ubuntu` et mode d'un frère de même extension dans le même répertoire (page HTML → page sœur, `.json`/`.md` → voisin de même extension, `.py` → `.py` voisin) ; à défaut `644`, et `666` pour un `.html`.
3. `%n` rend un chemin absolu : le nom est précédé de `/` et suivi de `|`. Utiliser `grep -F "/$f|"` ; `grep "|$f"` et `grep '|…$'` ne matchent jamais (reproduit : 0, 0, 1, 1 sur les quatre formes).

Le tar produit sous Windows stocke `666` et `uid/gid 0/0` pour chaque membre : sans `chmod`, les JSON `644` redeviennent `666 root:root`. Le `stat` final est la seule preuve des modes installés — le lot du 28/10 a appliqué un défaut unique (le 666 de la page sœur) aux six nouveaux fichiers et n'a pas imprimé ces modes : ne pas reconduire ce défaut sans le prouver.

Si une extraction a eu lieu sans sauvegarde exploitable, ne pas présenter les `.bak-*` voisins comme une restauration exacte : les copier dans un dossier daté avec une `NOTICE.txt` indiquant la date, les fichiers concernés et le fait que ces octets ne sont pas nécessairement ceux qui précédaient l'écrasement.

Pour un correctif d'un seul fichier, comparer avant d'écraser : télécharger la version distante, produire un `difflib.unified_diff`, relever `stat -c '%U %G %a'` sur le fichier distant, sauvegarder en `<fichier>.bak-<horodatage>`, puis réinstaller avec **ces** valeurs — constaté `ubuntu ubuntu 666` pour la passerelle et les pages HTML de l'œuvre, `644` pour `favicon.ico` et les deux JSON de l'œuvre. Ne pas imposer `644` par défaut : la passerelle tourne avec un mode plus ouvert. Redémarrer, puis vérifier l'égalité SHA-256 local/distant : un 200 public ne prouve pas que le fichier servi est celui qui vient d'être envoyé.

```bash
ts=$(date +%Y%m%d-%H%M%S)
read -r u g m <<<"$(stat -c '%U %G %a' "$FICHIER")"
cp -a "$FICHIER" "$FICHIER.bak-$ts" && install -o "$u" -g "$g" -m "$m" "$TMP" "$FICHIER" && rm -f "$TMP"
systemctl restart al-mizan-api-vps
sha256sum "$FICHIER"
```

Retour arrière : réinstaller `"$FICHIER.bak-<ts>"` avec les mêmes `-o`/`-g`/`-m`, redémarrer, revérifier le hash et les routes. Relever le SHA-256 de la sauvegarde au moment où elle est créée : sans ce hash, une restauration ne prouve rien.

Nettoyer l'archive temporaire locale et distante à la fin ; noter le chemin de sauvegarde dans le rapport.

### Lot cohérent page + API — exemple `oeuvre-universelle`

Une demande « redéployer la page » peut couvrir cinq fichiers. Lire le routeur avant de choisir. Chemins depuis la racine du workspace :

| Route | Fichier |
| :--- | :--- |
| `/oeuvre-universelle`, `/oeuvre-universelle/` | `ASTRO-Q°ODE_SYSTEME/web_cloud/oeuvre_universelle.html` |
| `/oeuvre-universelle/en` | `ASTRO-Q°ODE_SYSTEME/web_cloud/oeuvre_universelle_en.html` |
| `/oeuvre-universelle/ar` | `ASTRO-Q°ODE_SYSTEME/web_cloud/oeuvre_universelle_ar.html` |
| `/api/v1/oeuvre-universelle` | `ASTRO-Q°ODE_SYSTEME/resultats/oeuvre_universelle/resume.json` |
| `/api/v1/oeuvre-universelle/manifeste` | `ASTRO-Q°ODE_SYSTEME/resultats/oeuvre_universelle/manifeste_anteriorite.json` |

Déployer les cinq avec la même sauvegarde horodatée et vérifier les cinq routes. Ne pas se limiter à la page demandée : la page et l'API afficheraient des estampilles différentes.

Ces fichiers sont relus à chaque requête (`_servir_page_web_cloud` ouvre le HTML ; le handler API ouvre les JSON). **Aucun redémarrage n'est nécessaire** après leur installation ; ne redémarrer que si un `.py` a changé.

La génération officielle (`py -3 oeuvre_universelle/generer_page_oeuvre.py`) scelle le manifeste puis réécrit les trois pages. Même quand la racine Merkle reste identique, les pages changent parce qu'elles affichent `genere_le_utc`, `nb_fichiers` et `octets_total`. Après toute régénération, redéployer les trois pages et les deux JSON ; sinon la page publique reste antérieure au manifeste.

**Ordre imposé : tests → `generer_page_oeuvre.py` → déploiement.** `tests.test_oeuvre_universelle` appelle `construire_manifeste(ecrire=True)` (ligne 198) : lancée après la génération, la suite rescelle le manifeste sans réécrire les pages. Constaté le 28/10 : pages portant `e6bf222e…` (générées à 00:37:32Z) alors que le manifeste stocké valait `43b0bf0a…` ; `--verifier` répondait `ok: true` parce qu'il compare les hachages des fichiers au manifeste stocké (`verifier_manifeste`, `ASTRO-Q°ODE_SYSTEME/oeuvre_universelle/manifeste_anteriorite.py:182-201`), pas la racine embarquée dans les pages. Après tout essai de test qui rescelle, régénérer avant d'envoyer.

Depuis la racine `ASTRO-Q°ODE_SYSTEME`, vérifier avant l'envoi que chaque page et `resume.json` portent une ligne contenant la racine, puis après l'envoi que l'API renvoie la même (enveloppe `{"succes": …, "manifeste": {…}}`) :

```bash
ROOT=$(PYTHONIOENCODING=utf-8 py -3 -c "import json;print(json.load(open('resultats/oeuvre_universelle/manifeste_anteriorite.json',encoding='utf-8'))['racine_merkle_sha256'])")
for f in web_cloud/oeuvre_universelle.html web_cloud/oeuvre_universelle_en.html web_cloud/oeuvre_universelle_ar.html; do
  printf '%s %s\n' "$f" "$(grep -c "$ROOT" "$f")"
done
grep -c "$ROOT" resultats/oeuvre_universelle/resume.json
curl -s https://www.al-mizan.world/api/v1/oeuvre-universelle/manifeste \
  | PYTHONIOENCODING=utf-8 py -3 -c "import json,sys;m=json.load(sys.stdin)['manifeste'];print(m['racine_merkle_sha256'],m['nb_fichiers'])"
```

Attendu : `1` pour chaque fichier local, puis la même racine et le même compte via l'API (156 fichiers lors du lot du 28/10).

Modes constatés : `ubuntu:ubuntu 666` pour les pages, `644` pour les deux JSON. Lire `stat -c '%U %G %a'` et réinstaller avec les valeurs lues.

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
- **Journaux** : déléguer le tri à `verifier-journaux-nginx-vps`, mais contrôler d'abord la lisibilité. `ls -l /var/log/nginx/access.log` montre `640 www-data:adm` ; sans sudo, `wc -l` répond `Permission denied` et un `tail | awk` peut rendre `LINES 0` avec un code 0 et un stderr vide. Ce n'est pas « 0 réponse 5xx » : marquer `INCONCLUSIF`, puis lire avec `sudo -n` après avoir vérifié `sudo -n true` → 0 (invariant 5) ; aucune saisie de mot de passe. Ne conclure qu'avec la fenêtre `SINCE …`, `LINES n`, le nombre de 5xx et de 404 ; un 404 isolé de robot (`/wp-admin/install.php`) n'est pas une régression du site.
- **Parité trilingue** : dériver les motifs du HTML produit, pas de l'intention. Les alternates sont en guillemets simples (`rel='alternate' hreflang=`), et `count("class='langue")` compte aussi `class='langues'` (4 au lieu de 3) : soustraire `class='langues'` ou ancrer `langue on'`. Un contrôle écrit en guillemets doubles a rendu 4 faux FAIL sur des pages conformes (28/10).

Rapport final : tableau `changement → preuve → étiquette`, sauvegardes disponibles, commande de restauration, et liste explicite de ce qui reste non vérifié.

## 9. Pièges Windows constatés

- **Chemin contenant `°`** : `cd ".../ASTRO-Q*ODE_SYSTEME"` échoue en `No such file or directory` alors que le chemin littéral fonctionne. Utiliser le chemin exact, ou les outils Read/Glob.
- **Console cp1252** : imprimer du texte accentué ou des caractères de cadre lève `UnicodeEncodeError`. Exporter `PYTHONIOENCODING=utf-8` ; pour inspecter des caractères exacts, afficher `ligne.encode('unicode_escape').decode('ascii')`.
- **Code Python inline multiligne** : `py -3 -c "..."` avec apostrophes, `\n` et `%d` mélangés produit `SyntaxError: unterminated string literal` (constaté deux fois). Écrire le script dans `.qoder/tmp/*.py` avec Write, l'exécuter, puis supprimer le fichier.
- **`/tmp` non partagé** : un fichier créé par `curl -o /tmp/x.json` n'est pas vu par un processus Python qui ouvre `/tmp/x.json` (`FileNotFoundError`). Écrire les temporaires dans le workspace (`./.qoder_tmp_x.json`) et les supprimer.
- **Art ASCII** : les espaces de tête sont significatifs. Afficher les lignes exactes avant toute édition et copier la sous-chaîne depuis la sortie, sans la retaper.
- **Port occupé** : une instance précédente reste à l'écoute. Identifier le PID (`netstat -ano | grep ":PORT" | grep LISTENING`) puis `taskkill //F //PID`.
- **Interpréteur** : utiliser `py -3` ; l'alias Microsoft Store de `python` peut échouer.
- **`$USER` sous sudo** : dans `sudo -n bash -c '...'`, `$USER` vaut l'utilisateur cible (`root`), pas `ubuntu`. Écrire l'utilisateur applicatif en clair et vérifier avec `stat -c '%U %G %a'`.
- **Journaux `640 www-data:adm`** : sans sudo, `LINES 0` est un faux négatif, pas une absence de 5xx ; voir §8.
- **Liste de fichiers CRLF** : une liste écrite par `Path.write_text` sous Windows arrive avec `\r\n`. La boucle distante `while read` garde le `\r` : `chown: cannot access 'passerelle_api_vps_mizan.py'$'\r'` ; la sauvegarde copie 0 fichier (archive de 159 octets), puis l'extraction écrase quand même les fichiers existants. Constaté le 28/10/2026 : 20 fichiers extraits, dont 8 écrasés sans sauvegarde exploitable. Écrire avec `write_bytes` et retirer `\r` côté distant.
- **Horodatage de sauvegarde** : le calculer sur le serveur (`date +%Y%m%d-%H%M%S`), pas avec l'horloge locale, pour que le nom `.bak-<ts>` se situe dans les journaux du VPS.
- **Paramiko** : sur une commande bavarde, lire `stdout`/`stderr` avant `recv_exit_status()`. Les scripts de la session appelaient `recv_exit_status()` d'abord et ne passaient que parce que la sortie restait courte.
- **Carte de modes `stat`** : `%n` rend le chemin absolu ; dans `/tmp/al_mizan_modes.txt`, le nom est précédé de `/` et suivi de `|`. `grep "|$f"` ne matche pas → `grep -F "/$f|"` (sonde locale sur les quatre formes : 0, 0, 1, 1).
- **Enveloppe de l'API manifeste** : la réponse est `{"succes": …, "manifeste": {…}}` ; `mj["racine_merkle_sha256"]` lève `KeyError` (constaté 28/10). Lire `mj["manifeste"]["racine_merkle_sha256"]`.
- **Nettoyage** : supprimer le temporaire `/tmp` dans la même commande que l'installation et la copie distante du workspace (`./.qoder/tmp/remote_*.py`) après le diff.

## Ressources

- `references/preuves-session-2026-10-27.md` — commandes, sorties et horodatages de la session d'origine, avec distinction vérifié / non vérifié.
- `references/preuves-redeploiement-oeuvre-2026-10-27.md` — redéploiement du lot œuvre universelle (5 fichiers), journaux `640 www-data:adm`, faux négatif `LINES 0`, absence de redémarrage et limites.
- `references/preuves-echec-sauvegarde-2026-10-28.md` — échec de sauvegarde par liste CRLF sur le lot Riemann : `BACKUP_FICHIERS 0`, archive de 159 octets, 8 fichiers écrasés en `root:root`, réparation et limites.
- `references/preuves-lot-mixte-riemann-2026-10-28.md` — lot mixte de 19 fichiers (13 existants, 6 nouveaux) : carte des modes, piège `grep`, boucle de modes rejouée en fixture avec ses gardes, ordre tests → génération et double racine Merkle, faux FAIL de parité trilingue, sonde tar Windows et limites.
- `verifier-journaux-nginx-vps` — tri des journaux nginx (délégation de l'étape 6).
- `skill-file-qa` — validation post-écriture de ce Skill (frontmatter, références, blocs de code).
