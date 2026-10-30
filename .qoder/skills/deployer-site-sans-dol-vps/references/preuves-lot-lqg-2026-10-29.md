# Preuves — lot LQG, transport `bash -s`, modes `web_cloud`, fenêtre de journaux et `do_HEAD` (29/10/2026)

## Source

| Élément | Valeur |
| :--- | :--- |
| Session | `51bc92e6-6e0f-4c87-bd4d-e20bf36d0a1f`, titre « Mise à jour site web » |
| Tours utiles | 2026-10-29T20:00:14Z (demande LQG + mise à jour du site) et 2026-10-29T20:11:47Z (« LES TROIS ») |
| Lecture | 2026-10-29, `runtimeState = running`, `activeTurnId = 47247abd-5a3b-4c5e-8111-c30f38c0f8dd`, `revision = 11`, `hasMoreBefore = false` |
| Portée retenue | Seuls les deux tours terminés sont cités. Le troisième tour (« Contrôle le rendu visuel des 3 pages en prod », ouvert à 20:17:41Z) était encore `streaming` à la lecture : ses captures ne sont pas une preuve dans ce dossier. |

Les heures des messages et des enregistrements sont en UTC (`Z`) ; les sorties d'outils sont horodatées par le système local (+0100). Les entrées de commandes proviennent du JSONL du projet (types `tool_use`), les sorties des `tool_result` appariés.

## 1. Transport distant : `bash -c` + `repr` écarté, `bash -s` retenu

Version initiale, enregistrement `557` (2026-10-29T20:13:26Z) :

```python
stdin, stdout, stderr = cli.exec_command("sudo -n bash -c " + repr(cmd), timeout=120)
```

Le script local s'arrête avant d'exploiter la sortie, enregistrement `563` (20:13:51Z) :

```text
Exit code 1
UPLOADED 80773 285
Traceback (most recent call last):
  File "...\.qoder\tmp\lqg_deploy.py", line 101, in <module>
    out = stdout.read().decode("utf-8", "replace")
          ^^^^^^
NameError: name 'stdout' is not defined
```

La cause du `NameError` est structurelle (la variable n'existe pas dans ce chemin du script), pas un refus du serveur : aucune commande distante n'a été exécutée dans cet essai. La forme `repr(cmd)` a néanmoins un défaut indépendant, reproduit hors VPS le 29/10/2026 :

```text
$ py -3 -c "print(repr('echo A\necho B'))" > r.txt; bash -c "$(cat r.txt)"
bash: line 1: echo A\necho B: No such file or directory
rc=127
```

`repr()` encode les sauts de ligne en deux caractères `\` + `n`, que `bash -c` reçoit littéralement.

Version retenue, enregistrements `595` (20:15:11Z) puis `601` (20:15:23Z) :

```python
stdin, stdout, stderr = cli.exec_command("sudo -n bash -s", timeout=timeout)
stdin.write(cmd)
stdin.channel.shutdown_write()
out = stdout.read().decode("utf-8", "replace")
err = stderr.read().decode("utf-8", "replace")
rc = stdout.channel.recv_exit_status()
print("RC", rc)
```

```text
RC 0
TS 20261029-201520
```

## 2. Lot déployé (7 fichiers)

| Contrôle | Valeur observée |
| :--- | :--- |
| Transfert | `/tmp/al_mizan_update.tar.gz` 80 773 o, `/tmp/al_mizan_liste.txt` 285 o (`UPLOADED 80773 285`) |
| Sauvegarde | `/opt/al-mizan/sauvegardes/lot-20261029-201520/sauvegarde.tar.gz`, `BACKUP_FICHIERS 3`, sha `c0f7614ddfcb678fb983e7a9f6b0a264ab9c12b5869ff6c9ac0c51474b79fd30` |
| Fichiers sauvegardés | `passerelle_api_vps_mizan.py`, `web_cloud/sitemap.xml`, `web_cloud/portail_public_al_mizan.html` |
| Extraction | 7 chemins (3 ci-dessus + 3 pages LQG + `gravitation_quantique_boucles_resultats.json`) |
| Modes après extraction | `ubuntu:ubuntu 666` pour les 7 |
| Redémarrage | `active` ; `ActiveEnterTimestamp=Thu 2026-10-29 20:15:34 UTC` |
| Routes locales | `portail=200 lqg=200 json=200` |

## 3. Vérification publique

```text
/gravitation-quantique-boucles     200 text/html; charset=utf-8 32269
/gravitation-quantique-boucles/en  200 text/html; charset=utf-8 31260
/gravitation-quantique-boucles/ar  200 text/html; charset=utf-8 33722
/gravitation-quantique-boucles.json 200 application/json; charset=utf-8 15106
/sitemap.xml                       200 application/xml; charset=utf-8 7209
/                                  200 text/html; charset=utf-8 130957
```

| Fichier | Brut | LF normalisé | SHA (préfixe 16) |
| :--- | :--- | :--- | :--- |
| `gravitation_quantique_boucles.html` | DIFF | EGAL | `5db07420e39f9727` |
| `gravitation_quantique_boucles_en.html` | DIFF | EGAL | `526d8cbd69956096` |
| `gravitation_quantique_boucles_ar.html` | DIFF | EGAL | `c59a52e2fdbcc6b8` |
| `gravitation_quantique_boucles_resultats.json` | EGAL | EGAL | `3ba603c9ffdeb560` |
| `sitemap.xml` | EGAL | EGAL | `fbdf6859c09a5843` |
| `portail_public_al_mizan.html` | EGAL | EGAL | `b0587db82e5ac1df` |

Les HTML ne sont identiques qu'après normalisation CRLF → LF (invariant 9). Les tailles publiques sont celles servies en LF.

## 4. Modes de `web_cloud/`

Relevé `stat -c '%n|%U|%G|%a' web_cloud/*.json` (enregistrement `628`, 20:16:26Z) :

```text
web_cloud/gravitation_quantique_boucles_resultats.json|ubuntu|ubuntu|666
web_cloud/quatrieme_dimension_resultats.json|ubuntu|ubuntu|666
web_cloud/sessions_paiement_mobile.json|ubuntu|ubuntu|666
web_cloud/traducteur_multimedia_resultats.json|ubuntu|ubuntu|666
```

Quatre voisins `.json` en `666` : la règle « mode d'un frère de même extension » rend `666` pour un nouveau JSON de `web_cloud/`, et non `644`. Le `644` constaté sur les deux JSON de `resultats/oeuvre_universelle/` (28/10/2026) ne s'étend pas à `web_cloud/`.

## 5. Fenêtre de journaux : faux négatif et ancrage

Essai `awk` sur position absolue (enregistrement `628`) :

```text
SINCE 29/Oct/2026:19:56 LINES 0 5xx 0
```

Code 0 et stderr vide alors que la fenêtre contient des lignes. Filtre ancré sur la date entre crochets (enregistrement `638`, 20:16:43Z, motif `29/Oct/2026:20:1[5-9]` puis `20:2[0-9]`) :

```text
LINES 9 5xx 0 4xx 0
```

Reproduction hors VPS sur une ligne combinée type :

```text
$ awk -v s="29/Oct/2026:20:15" 'index($0,s)==1' log1.txt | wc -l
0
$ grep -c "\[29/Oct/2026:20:1[5-9]" log1.txt
1
```

La ligne commence par l'IP du client ; la date apparaît après le préfixe `[`. `index($0,s)==1` ne peut donc jamais matcher.

## 6. `do_HEAD` : 200 `text/html` quelle que soit la route

Sonde `curl -sI` sur la route JSON (enregistrement `628`) :

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.12.3
Content-Type: text/html; charset=utf-8
```

Même route en GET avec `curl -s -D - -o /dev/null` (enregistrement `638`) :

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.12.3
Date: Thu, 29 Oct 2026 20:16:41 GMT
Content-Type: application/json; charset=utf-8
Content-Length: 15106
X-Content-Type-Options: nosniff
Cache-Control: no-cache
```

Le handler `do_HEAD` du code local (relu le 29/10/2026, `passerelle_api_vps_mizan.py:436-441`) ne résout aucune route :

```python
def do_HEAD(self):
    """Gestionnaire de requêtes HEAD conforme pour vérification SSL et sondes réseau."""
    self.send_response(200)
    self.send_header("Content-Type", "text/html; charset=utf-8")
    self.send_header("X-Powered-By", "Al-Mizan-Souverain-135MHz")
    self.end_headers()
```

Il répond `200` même sur un chemin inexistant : un HEAD ne prouve ni le type, ni l'existence de la route. La vérification d'en-têtes se fait en GET.

## 7. Nettoyage

```text
TEMP_CLEAN
```

Les temporaires locaux (`lqg_*.py`, `lqg_site.tar.gz`, `lqg_liste.txt`, `pub_*.out`) et les temporaires distants (`/tmp/al_mizan_*`) ont été supprimés ; la sauvegarde `lot-20261029-201520` reste en place.

## Limites

- Le troisième tour de la session source (contrôle visuel en production) était encore en cours à la lecture : aucune conclusion visuelle de production n'est tirée ici. Les captures `lqg_prod_*.png` ont été écrites à 21:18 heure locale, après la lecture des tours 1 et 2.
- La fenêtre de journaux couvre environ deux minutes après le redémarrage de 20:15:34 UTC ; elle ne prouve pas l'absence de 5xx plus tard.
- Les hashes sont cités en préfixe de 16 caractères, tels que la sortie les a imprimés ; aucun hash complet de page n'a été capturé dans cette session.
- La présentation par l'assistant source (« 13 cartes, 4 tableaux, 8 sections, hreflang ×3 ») n'est pas reprise ici comme preuve : ce dossier ne cite que les sorties d'outils.
