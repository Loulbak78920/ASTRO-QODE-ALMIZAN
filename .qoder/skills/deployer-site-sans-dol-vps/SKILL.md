---
name: deployer-site-sans-dol-vps
description: "Mettre à jour sans dolosif le site public al-mizan.world sur le VPS OVH : recenser les routes réellement servies par la passerelle, requalifier chaque allégation en opérationnel, simulé ou spécifié, valider en local les pages et le JavaScript inline, déployer un lot cohérent de pages et de JSON d'API (ex. œuvre universelle), un lot mixte de fichiers existants et nouveaux, ou une archive ciblée web_cloud et modules modifiés, appliquer des en-têtes nginx avec sauvegarde et retour arrière, puis vérifier le site en direct et dans les journaux, y compris un triage de journaux illisible sans sudo. Utiliser pour corriger, publier ou vérifier www.al-mizan.world, le portail Al-Mizan, la passerelle VPS, une page du site, l'œuvre universelle ou une déclaration publique de l'écosystème. Utiliser aussi avant de retoucher une page existante, pour vérifier quelle copie le routeur sert réellement."
---

# Publier une mise à jour véridique du site Al-Mizan

## Portée

Ce flux couvre la chaîne complète : audit des déclarations, correction des pages et des générateurs, validation locale, déploiement ciblé sur le VPS OVH, en-têtes nginx, puis vérification en direct. Il ne couvre ni la rédaction documentaire (`docs/`), ni le Tableau Maître, ni les sceaux mémoire.

## 1. Invariants

1. **Aucune allégation sans preuve reproductible.** Chaque affirmation affichée reçoit une étiquette : `opérationnel` (observé en direct), `simulé` (émulation logicielle), `spécifié` (paramètre de conception), ou `déclaré · non vérifié` (adresse, partenariat, liquidité).
2. **Corriger la source, pas seulement la page.** Les textes du dialogue et les compteurs sont souvent régénérés par des modules Python. Si le générateur garde l'ancienne formulation, la page la réintroduit.
3. **Toute écriture en production est réversible — et la réversibilité se prouve avant d'écrire.** Sauvegarde horodatée dont l'existence est vérifiée : archive non vide, `BACKUP_FICHIERS > 0`, SHA-256 relevé et `tar -tzf` recoupé avec la liste. Un compte nul arrête l'opération avant toute extraction. Chemin de restauration noté dans le rapport final.
4. **Demander confirmation avant le premier déploiement** d'un lot non trivial. Un accord une fois donné ne vaut pas pour les lots suivants.
5. **Secrets et sudo** : passer par `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\deploiement_vps\charger_credentials_ovh.py` (`hote_user_mdp()`). Sur ce VPS, `ubuntu` dispose de sudo NOPASSWD (`sudo -n true` → 0 constaté le 28/10/2026 ; à revérifier à chaque session) : exécuter les commandes privilégiées avec `sudo -n`, sans stdin. Ne jamais envoyer le mot de passe à `sudo -S` avec `bash -s` : il est exécuté comme une commande et recraché dans stderr. Ne jamais afficher, journaliser ni copier le secret dans un fichier du dépôt. **Transport d'un script multi-lignes** : `cli.exec_command("sudo -n bash -s")`, puis écrire le script sur `stdin`, appeler `stdin.channel.shutdown_write()`, lire `stdout`/`stderr`, et seulement ensuite `recv_exit_status()`. Ne pas composer la commande en `"bash -c " + repr(cmd)` : `repr()` échappe les sauts de ligne en `\n` littéraux que `bash -c` n'interprète pas (reproduit : `bash: line 1: echo A\necho B: No such file or directory`, rc 127). Le 29/10/2026, la variante `bash -c` a été abandonnée après un `NameError` local, avant tout envoi ; la variante `bash -s` a rendu `RC 0` sur les phases A et B.
6. **La vérité des routes vient du code de la passerelle**, jamais du contenu du répertoire `web_cloud`.
7. **Un lot page + API est atomique.** Une page publique et les JSON consommés par son API (ex. `oeuvre-universelle` : 3 pages + `resume.json` + `manifeste_anteriorite.json`) se déploient avec la même sauvegarde et la même vérification. Déployer une seule page crée une divergence entre ce que lit l'utilisateur et ce que renvoie l'API.
8. **Un journal vide ou illisible est INCONCLUSIF.** Une lecture sans sudo peut rendre `LINES 0` avec un code 0 et un stderr vide ; ce n'est pas une preuve d'absence de 5xx. Lire les journaux avec `sudo -n` et ne conclure qu'avec une fenêtre et un décompte lisibles.
9. **Une liste de chemins traversant Windows → VPS est en LF.** L'écrire en octets (`write_bytes`, jointure `b"\n"`), jamais avec `write_text` qui traduit en `\r\n` sous Windows ; côté distant, retirer un `\r` final avant tout usage. Une liste corrompue produit une sauvegarde vide, pas une erreur visible.
10. **L'ordre tests → génération → déploiement est imposé, et une seule racine Merkle doit coïncider partout.** La suite œuvre rescelle le manifeste sans réécrire les pages ; lancée après génération, elle laisse les pages sur l'ancienne racine. `--verifier` reste vert car il compare les hachages des fichiers au manifeste stocké. Exiger la même racine dans les trois pages, `resume.json`, le manifeste et l'API.
11. **Retoucher la copie que le routeur ouvre, pas un homonyme.** Avant toute retouche d'une page, résoudre le chemin exact dans le handler (`chemin in [...]` puis `Path(__file__).resolve().parent / "web_cloud" / "<fichier>"`), puis chercher les variantes de la même page dans le workspace. Un nom différent ne prouve pas un fichier différent : `HUB_PONTS_SYNCHRONES_AL_MIZAN.html` et `hub_ponts_synchrones.html` sont la même page. Comparer les octets, retoucher le seul fichier servi, et traiter la suppression d'une copie non servie comme une opération distincte, confirmée, avec taille et SHA-256 relevés avant le `rm`.

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

### 3.1 Quelle copie est réellement servie ?

Une demande « applique ce layout à l'original » ne nomme pas le fichier que le routeur ouvre. Le 28/10/2026, `HUB_PONTS_SYNCHRONES_AL_MIZAN.html` (racine, 25 900 o, sha `86719d15…`) a été retouché en premier ; le handler ne sert que `ASTRO-Q°ODE_SYSTEME/web_cloud/hub_ponts_synchrones.html` (28 440 o avant retouche, sha `af301dbf…`). Le doublon racine était pré-audit : pas de bandeau de transparence, « Stabilité 99.83% », « Bride 0.6225 Scellée ». Le déployer aurait fait régresser l'invariant 1.

Résoudre le handler, puis lister les variantes par tokens — un nom différent ne prouve pas une page différente. Adapter `"/ponts"` et le basename à la page visée. La copie racine ayant été supprimée, l'exemple ci-dessous utilise une variante encore présente ; remplacer `CANDIDAT` par le candidat listé. La liste est volatile : des prototypes peuvent apparaître pendant la session (constaté le 28/10), donc relister juste avant de choisir.

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
grep -n 'chemin in \[.*"/ponts"' -A 8 passerelle_api_vps_mizan.py
```

```text
923:        elif chemin in ["/ponts", "/hub-ponts", "/ponts-synchrones", "/hub"]:
924:            chemin_ponts = Path(__file__).resolve().parent / "web_cloud" / "hub_ponts_synchrones.html"
```

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
find . -type f -iname '*.html' -not -path './.git/*' \
  | grep -iE 'ponts|synchrones' | sort
CANDIDAT="ASTRO-Q°ODE_SYSTEME/ponts_synchrones_al_mizan.html"
sha256sum "$CANDIDAT" "ASTRO-Q°ODE_SYSTEME/web_cloud/hub_ponts_synchrones.html"
diff -u "$CANDIDAT" "ASTRO-Q°ODE_SYSTEME/web_cloud/hub_ponts_synchrones.html" | head -80
```

Décision :

- Seul le chemin rendu par le handler est servi. Les autres copies ne changent rien en production : un accès direct par nom de fichier répond 404 (invariant 6). Ne pas les retoucher « au cas où ».
- Un candidat n'est pas forcément un doublon : le 28/10, `ASTRO-Q°ODE_SYSTEME/ponts_synchrones_al_mizan.html` (15 385 o, sha `2ca9fea1…`) partage les tokens mais porte un autre titre et n'est référencé par aucun handler de la passerelle. Le diff tranche ; ne rien supprimer sans demande.
- Lire le diff avant d'écrire. Une copie sans bandeau de transparence, avec « Stabilité 99.83% » ou « Bride 0.6225 Scellée », est antérieure à l'audit : la déployer ferait régresser l'invariant 1.
- Comparer aussi le fichier servi local au fichier distant : le local peut contenir des changements jamais déployés (28/10 : 27 848 o en ligne, 28 440 o en local, trois liens CGU/CGV/Signalement absents de la production). Trancher leur inclusion avec l'utilisateur avant d'envoyer.
- Supprimer une copie non servie est une opération distincte : vérifier les références vivantes, relever taille et SHA-256, demander confirmation, puis `rm`. Ne jamais la supprimer comme effet de bord de la retouche.

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

Le démarrage local est **fail-closed** depuis le durcissement du 27/10/2026 : `secret_webhooks_requis()` lit `MIZAN_WEBHOOK_SECRET` et `__main__` refuse de démarrer si la variable manque, avant d'ouvrir le port.

```text
[ERREUR] Démarrage refusé : MIZAN_WEBHOOK_SECRET absent : signature des webhooks impossible.
```

Pour une validation locale en lecture seule, fournir une valeur factice à usage unique sur un port libre. Ne jamais l'écrire dans un fichier ni la réutiliser en production : le service VPS charge le vrai secret via `EnvironmentFile=`. Sans `MIZAN_VPS_API_KEY`, les routes protégées restent fermées — suffisant pour tester des pages et des JSON publics, pas pour un parcours authentifié.

Vérifier le port **avant** de démarrer : une passerelle d'une session précédente peut y rester à l'écoute et servir son ancien code. Constaté le 29/10/2026 : PID 10668 à l'écoute sur 18095 renvoyait `{"succes": false, "erreur": "Route GET introuvable"}` sur `/quatrieme-dimension`, alors que la source courante contient ces handlers (`passerelle_api_vps_mizan.py:154-159`). Ce 404 simule une route manquante. Prendre un autre port plutôt que de tuer un PID inconnu ; si son arrêt est nécessaire, relever d'abord son heure de démarrage et son chemin. Si 18096 est aussi pris, prendre 18097.

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
PORT=18095
if netstat -ano | grep ":$PORT" | grep -q LISTENING; then PORT=18096; fi
nohup env PYTHONIOENCODING=utf-8 MIZAN_WEBHOOK_SECRET=local-test-only \
  py -3 passerelle_api_vps_mizan.py --port "$PORT" > ./.qoder_tmp_gw.log 2>&1 &
sleep 4
tail -3 ./.qoder_tmp_gw.log
curl -s -o /dev/null -w '%{http_code}\n' "http://127.0.0.1:$PORT/api/v1/sante"
```

Si le journal affiche le refus, la cause est le secret, pas le port. N'utiliser `8095` que si un passage navigateur exige le port exact et qu'il est libre. Arrêter le processus du port réellement ouvert — relire ce port dans la bannière du journal, pas dans une variable de shell perdue entre deux appels :

```bash
PORT=$(grep -o 'PORT [0-9]*' ./.qoder_tmp_gw.log | tail -1 | awk '{print $NF}')
pid=$(netstat -ano | grep ":$PORT" | grep LISTENING | awk '{print $NF}' | head -1)
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

**Contrôler les membres avant transfert.** Un `py_compile` local laisse un `__pycache__/*.pyc` dans la racine : s'il entre dans la liste, l'archive l'installe sur le VPS. Filtrer `__pycache__` et `*.pyc` dans tout le lot, pas seulement sous `web_cloud`, puis exiger :

```bash
test "$(tar -tzf ./.qoder_tmp_site.tar.gz | grep -Ec '(^|/)__pycache__/|\.pyc$')" -eq 0
test "$(tar -tzf ./.qoder_tmp_site.tar.gz | wc -l)" -eq "$(wc -l < ./.qoder_tmp_liste.txt)"
```

Un compte égal ne prouve rien : le 30/10/2026, 8 membres pour 8 lignes de liste, dont `__pycache__/passerelle_api_vps_mizan.cpython-314.pyc` installé en `644` puis retiré par un `stat` + `rm` explicites.

**Phase A — sauvegarde.** Remplacer `23` par le compte imprimé localement, puis transmettre le bloc par `cli.exec_command("sudo -n bash -s")` : `stdin.write(cmd)`, `stdin.channel.shutdown_write()`, lecture de `stdout`/`stderr`, puis `recv_exit_status()`. Ne pas l'envoyer en `bash -c` (invariant 5) :

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
2. Chemin nouveau : `ubuntu:ubuntu` et mode d'un frère de même extension dans le même répertoire (page HTML → page sœur, `.json`/`.md` → voisin de même extension, `.py` → `.py` voisin) ; à défaut `644`, et `666` pour un `.html`. Dans `web_cloud/`, le frère `.json` vaut `666` (quatre relevés le 29/10/2026) : un nouveau JSON y prend `666`, et un `666` existant ne se « corrige » pas en `644`. Le `644` ne vaut que hors `web_cloud` (ex. `resultats/oeuvre_universelle/`).
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

### Lot purement statique — prouver qu'aucun générateur ne réécrira les pages

Un lot de pages et de JSON générés hors du VPS se déploie sans redémarrage. Avant d'écrire « la page ne sera pas écrasée par l'ancienne logique », prouver sur le VPS qu'aucun générateur ni planificateur ne réécrit ces fichiers :

```bash
sudo -n bash -c '
R=/opt/al-mizan/ASTRO-Q°ODE_SYSTEME
find "$R" \( -name "quatrieme_dimension.py" -o -name "generer_page_quatrieme_dimension.py" \) -print
crontab -l -u ubuntu 2>/dev/null | grep -v "^#" || true
crontab -l -u root 2>/dev/null | grep -v "^#" || true
grep -RIs "quatrieme_dimension" /etc/cron* /etc/systemd/system 2>/dev/null || true
systemctl list-timers --all --no-pager | grep -i "quatrieme\|oeuvre\|riemann" || true
'
```

Attendu : aucune sortie. Le 29/10/2026, `find` n'a rendu aucun moteur, le cron utilisateur était vide (la commande ajoutée contrôle aussi celui de root), aucun service ou cron ne citait le générateur, et les timers listés ne concernaient que le système (sysstat, fwupd, certbot, apt…). La conclusion se limite à cet état daté : un générateur installé plus tard, ou une exécution manuelle, rouvre la question. Si `find` trouve un générateur sans planificateur, écrire « générateur présent, non planifié », pas « aucune réécriture possible ».

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

### Lot trilingue issu du registre — page, hub et câblage

Avant d'écrire le générateur, lire les constantes de forme de `ASTRO-Q°ODE_SYSTEME/oeuvre_universelle/qualite_accessibilite_pages.py` : `NB_TABLES = 4`, `NB_H2 = 9`, `NB_H3 = 13`, `NB_LIENS = 24`, `NB_STATUTS = 26` (lignes 80-84) et `cible_nombre == 11` (ligne 415). La page doit rendre exactement 1 h1, 9 h2, 13 h3, 4 tableaux, 26 pastilles, 24 liens, 11 cibles, 26 `th[scope]` dont 12 `row` et 1 svg : constaté le 30/10/2026 sur les trois pages `justice_restitution*`. Un dixième texte légal se pose en liste dans `#source`, pas en cinquième tableau, car C-QA08 compte 4 tableaux.

Une entrée de registre transforme le lot en page + hub + câblage. Points à synchroniser, tous rencontrés le 30/10/2026 : entrée `JUS-02` dans `registre_problemes_monde.py` (ligne 555 ; 21 problèmes, 7 strates, 6 contrats) et fonction dans `modeles_reference.py` ; les trois `meta` de `generer_page_oeuvre.py` en f-string `f"{len(R.PROBLEMES)} …"` (FR/EN/AR ; l'arabe portait « عشرون » en toutes lettres) ; compteurs de `ASTRO-Q°ODE_SYSTEME/tests/test_oeuvre_universelle.py` et `ASTRO-Q°ODE_SYSTEME/tests/test_site_public_mizan.py` ; carte du portail avant les cartes existantes, sans renuméroter les tags (SYS-01, ECO-01) ; 3 URL de sitemap ; 5 routes de page (`/justice-restitution`, `/justice-restitution/`, `/en`, `/ar`, `/justice_restitution`) et le bloc JSON de `passerelle_api_vps_mizan.py` (`/justice-restitution.json`, `/justice-restitution/resultats.json`). Puis régénérer le hub et resceller le manifeste : le portail est scellé, les pages hub ne le sont pas ; exiger la même racine dans les 3 pages, `resume.json`, le manifeste et l'API. Le lot atomique inclut pages hub + `resume.json` + manifeste + JSON de la nouvelle page (23 fichiers le 30/10/2026).

Si un autre lot local doit rester non déployé, construire le lot depuis des variantes élaguées : retirer de la passerelle ses routes et son bloc JSON, du sitemap ses 3 URL, du portail sa carte ; puis asserter les comptes (`justice == 3`, `retro == 3`, jeton adverse absent, liens attendus présents). Déployer la variante, jamais la copie de travail.

Compiler la copie du lot avec `py_compile.compile(..., cfile=<hors lot>)`, puis asserter l'absence de `__pycache__` et de `.pyc` dans le lot : l'appel sans `cfile` écrit un cache adjacent, qui a fait échouer l'assertion le 30/10/2026. Vérifier un lien généré en cherchant le jeton (`/justice-restitution`), pas la guillemet : le hub émet `href='/justice-restitution'` en guillemets simples, le portail en doubles ; un `grep 'href="/…"'` rend 0 sur un lien servi.

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

- **Égalité de contenu** : pour chaque route, télécharger, calculer SHA-256 et comparer au fichier local. Les pages lues en mode texte par la passerelle diffèrent en brut (CRLF Windows → LF) : normaliser avant de conclure, et dire explicitement quelles routes sont identiques en brut et lesquelles seulement après normalisation. Exemple daté (lot 4D, 29/10/2026) : les trois HTML étaient `brut DIFF | LF EGAL`, le JSON `brut EGAL` avec le même SHA-256 (`49ec7172…`) des deux côtés ; ne pas annoncer « égal seulement après normalisation » pour un JSON identique en brut. Comparer au fichier **du lot stagé** (`.qoder/tmp/lot/…`), pas à l'original du dépôt, quand un lot voisin non déployé modifie le même fichier : le 30/10/2026, `/` (`d33ac95d…` servi) et `/sitemap.xml` (`e40a1636…` servi) différaient des originaux du dépôt (`3a99f0fc…`, `a95772e4…`), qui portaient le lot `reglement-dettes-redistribution` resté local (404 public). Un DIFF n'est une dérive qu'après comparaison au lot stagé. L'égalité octet pour octet se prouve par `size_download`/`Content-Length` et SHA-256, jamais par `$body_bytes_sent` : une page servie en `Transfer-Encoding: chunked` journalise 43 863 o pour un corps de 43 803 o (+60 o de tramage constatés le 30/10/2026).
- **Routes** : tous les statuts 200 attendus, favicon `image/x-icon`, aucun 404 sur les alias.
- **En-têtes** : les contrôler par GET, `curl -s -D - -o /dev/null <url>`. `curl -I` ne prouve rien : `do_HEAD` est une sonde de connectivité qui répond toujours `200` en `text/html` (`passerelle_api_vps_mizan.py:436-441`), sans résoudre la route — une route inexistante répond aussi `200`. Constaté le 29/10/2026 sur la route JSON : `text/html` en HEAD, puis `application/json` + `Content-Length: 15106` + `nosniff` + `no-cache` en GET. Les six en-têtes se vérifient sur `/` en GET.
- **Dialogue** : réponse fonctionnelle et honnête (aucun matériel quantique physique revendiqué).
- **Console** : scénarios simulés générés, aucune erreur JavaScript.
- **Journaux** : déléguer le tri à `verifier-journaux-nginx-vps`, mais contrôler d'abord la lisibilité. `ls -l /var/log/nginx/access.log` montre `640 www-data:adm` ; sans sudo, `wc -l` répond `Permission denied` et un `tail | awk` peut rendre `LINES 0` avec un code 0 et un stderr vide. Ce n'est pas « 0 réponse 5xx » : marquer `INCONCLUSIF`, puis lire avec `sudo -n` après avoir vérifié `sudo -n true` → 0 (invariant 5) ; aucune saisie de mot de passe. Ne conclure qu'avec la fenêtre `SINCE …`, `LINES n`, le nombre de 5xx et de 404 ; un 404 isolé de robot (`/wp-admin/install.php`) n'est pas une régression du site. Fenêtrer sur la date entre crochets avec une ancre qui ne suppose pas le début de ligne : `sudo -n grep -F "[$SINCE" /var/log/nginx/access.log | grep -cE '" 5[0-9][0-9] '`. Ancrer un motif sur le début de ligne rend `LINES 0` alors que des lignes existent, car la ligne combinée commence par l'IP (reproduit : 0 contre 1 le 29/10/2026 ; le 30/10, `LOG_LISIBLE oui` et `FENETRE_LIGNES 0` alors que `tail -3` montrait des GET à 02:01:26, puis 11 lignes / 8 retro / 0 5xx / 0 404 après correction). Avant de conclure `LINES 0`, afficher `tail -3` du journal : un journal lisible et vide est une ancre fausse, pas une absence de trafic.
- **Parité trilingue** : dériver les motifs du HTML produit, pas de l'intention. Les alternates sont en guillemets simples (`rel='alternate' hreflang=`), et `count("class='langue")` compte aussi `class='langues'` (4 au lieu de 3) : soustraire `class='langues'` ou ancrer `langue on'`. Un contrôle écrit en guillemets doubles a rendu 4 faux FAIL sur des pages conformes (28/10). Parser les attributs avec les deux styles de guillemets, `re.findall(r"(\w[\w:-]*)\s*=\s*(['\"])(.*?)\2", tag)` — trois groupes, donc déballer trois valeurs : un parseur limité aux guillemets doubles n'a vu que 1 alternate sur 4 (`x-default` seul) le 30/10/2026 et a conclu à tort à des alternates incomplets ; le parseur corrigé rend 4 alternates + canonical sur chaque page.

Rapport final : tableau `changement → preuve → étiquette`, sauvegardes disponibles, commande de restauration, et liste explicite de ce qui reste non vérifié.

## 9. Pièges Windows constatés

- **Chemin contenant `°`** : `cd ".../ASTRO-Q*ODE_SYSTEME"` échoue en `No such file or directory` alors que le chemin littéral fonctionne. Utiliser le chemin exact, ou les outils Read/Glob.
- **Console cp1252** : imprimer du texte accentué ou des caractères de cadre lève `UnicodeEncodeError`. Exporter `PYTHONIOENCODING=utf-8` ; pour inspecter des caractères exacts, afficher `ligne.encode('unicode_escape').decode('ascii')`.
- **Code Python inline multiligne** : `py -3 -c "..."` avec apostrophes, `\n` et `%d` mélangés produit `SyntaxError: unterminated string literal` (constaté deux fois). Écrire le script dans `.qoder/tmp/*.py` avec Write, l'exécuter, puis supprimer le fichier.
- **`/tmp` non partagé** : un fichier créé par `curl -o /tmp/x.json` n'est pas vu par un processus Python qui ouvre `/tmp/x.json` (`FileNotFoundError`). Écrire les temporaires dans le workspace (`./.qoder_tmp_x.json`) et les supprimer.
- **Art ASCII** : les espaces de tête sont significatifs. Afficher les lignes exactes avant toute édition et copier la sous-chaîne depuis la sortie, sans la retaper.
- **Port occupé** : une instance précédente reste à l'écoute. Identifier le PID (`netstat -ano | grep ":PORT" | grep LISTENING`) puis `taskkill //F //PID`. Ne pas tester une route sur un port déjà tenu : l'ancien processus sert son code et rend 404 des routes présentes dans la source courante (29/10/2026, PID 10668 sur 18095). Prendre un autre port plutôt que de tuer un PID inconnu (§5.3).
- **Interpréteur** : utiliser `py -3` ; l'alias Microsoft Store de `python` peut échouer.
- **`$USER` sous sudo** : dans `sudo -n bash -c '...'`, `$USER` vaut l'utilisateur cible (`root`), pas `ubuntu`. Écrire l'utilisateur applicatif en clair et vérifier avec `stat -c '%U %G %a'`.
- **Journaux `640 www-data:adm`** : sans sudo, `LINES 0` est un faux négatif, pas une absence de 5xx ; ancre la fenêtre sur `[` + date et non sur le début de ligne (§8).
- **Liste de fichiers CRLF** : une liste écrite par `Path.write_text` sous Windows arrive avec `\r\n`. La boucle distante `while read` garde le `\r` : `chown: cannot access 'passerelle_api_vps_mizan.py'$'\r'` ; la sauvegarde copie 0 fichier (archive de 159 octets), puis l'extraction écrase quand même les fichiers existants. Constaté le 28/10/2026 : 20 fichiers extraits, dont 8 écrasés sans sauvegarde exploitable. Écrire avec `write_bytes` et retirer `\r` côté distant.
- **Horodatage de sauvegarde** : le calculer sur le serveur (`date +%Y%m%d-%H%M%S`), pas avec l'horloge locale, pour que le nom `.bak-<ts>` se situe dans les journaux du VPS.
- **Paramiko** : sur une commande bavarde, lire `stdout`/`stderr` avant `recv_exit_status()`. Les scripts de la session appelaient `recv_exit_status()` d'abord et ne passaient que parce que la sortie restait courte.
- **Carte de modes `stat`** : `%n` rend le chemin absolu ; dans `/tmp/al_mizan_modes.txt`, le nom est précédé de `/` et suivi de `|`. `grep "|$f"` ne matche pas → `grep -F "/$f|"` (sonde locale sur les quatre formes : 0, 0, 1, 1).
- **Enveloppe de l'API manifeste** : la réponse est `{"succes": …, "manifeste": {…}}` ; `mj["racine_merkle_sha256"]` lève `KeyError` (constaté 28/10). Lire `mj["manifeste"]["racine_merkle_sha256"]`.
- **Copie homonyme d'une page** : `HUB_PONTS_SYNCHRONES_AL_MIZAN.html` (racine) et `hub_ponts_synchrones.html` (`web_cloud`) sont la même page sous deux noms. Le 28/10, la première a été retouchée alors que le routeur ne sert que la seconde ; le doublon était pré-audit. Résoudre le handler et differ avant d'éditer (invariant 11, §3.1).
- **Nettoyage** : supprimer le temporaire `/tmp` dans la même commande que l'installation et la copie distante du workspace (`./.qoder/tmp/remote_*.py`) après le diff.

## Ressources

- `references/preuves-session-2026-10-27.md` — commandes, sorties et horodatages de la session d'origine, avec distinction vérifié / non vérifié.
- `references/preuves-redeploiement-oeuvre-2026-10-27.md` — redéploiement du lot œuvre universelle (5 fichiers), journaux `640 www-data:adm`, faux négatif `LINES 0`, absence de redémarrage et limites.
- `references/preuves-echec-sauvegarde-2026-10-28.md` — échec de sauvegarde par liste CRLF sur le lot Riemann : `BACKUP_FICHIERS 0`, archive de 159 octets, 8 fichiers écrasés en `root:root`, réparation et limites.
- `references/preuves-lot-mixte-riemann-2026-10-28.md` — lot mixte de 19 fichiers (13 existants, 6 nouveaux) : carte des modes, piège `grep`, boucle de modes rejouée en fixture avec ses gardes, ordre tests → génération et double racine Merkle, faux FAIL de parité trilingue, sonde tar Windows et limites.
- `references/preuves-copie-servie-hub-ponts-2026-10-28.md` — copie servie vs doublon racine : handler lignes 922-931, diff pré-audit/audité, déploiement du seul fichier servi, suppressions confirmées et troisième variante non servie.
- `references/preuves-lot-4d-2026-10-29.md` — lot statique 4D : passerelle locale fail-closed, PID résiduel 10668 sur 18095 et faux 404, validation sur 18096, sauvegarde et 4/4 hashes, absence de générateur/cron/timer distant, égalité brut/LF et limites.
- `references/preuves-lot-lqg-2026-10-29.md` — lot LQG (7 fichiers) : transport `bash -s` après échec `bash -c`/`repr`, sauvegarde 3 fichiers `c0f7614d…`, modes 666 de `web_cloud`, fenêtre de journaux ancrée sur `[` + date, `do_HEAD` vs GET et limites.
- `references/preuves-lot-justice-restitution-2026-10-30.md` — lot justice/restitution (23 fichiers) : forme imposée par les contrôles qualité, synchronisation registre/hub/portail/sitemap/passerelle, variante élaguée du lot règlement resté local, `cfile` hors lot, racine Merkle rescellée et limites.
- `verifier-journaux-nginx-vps` — tri des journaux nginx (délégation de l'étape 6).
- `skill-file-qa` — validation post-écriture de ce Skill (frontmatter, références, blocs de code).
