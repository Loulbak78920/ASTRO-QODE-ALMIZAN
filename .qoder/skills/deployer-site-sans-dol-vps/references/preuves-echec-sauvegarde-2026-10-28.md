# Preuves — échec de sauvegarde par liste CRLF (28/10/2026)

## Source

| Élément | Valeur |
| :--- | :--- |
| Session | `de5bacf6-50d0-42ce-b890-f3149acbbd91`, titre « Équations et résolution de l'ignorance » |
| Lecture | 2026-10-28, `runtimeState = running`, `activeTurnId = 5c69ca15…`, `revision = 32`, `hasMoreBefore = true`, `turnLimit = 12` |
| Tour concerné | `154f29cc` — demande humaine du 2026-10-28T00:03:28Z : publier un dossier Riemann honnête sur le site |
| Horodatage du lot | nom de sauvegarde `lot-riemann-20261028-002247` (calculé sur le serveur) |
| Correction utilisateur | aucune sur ce déploiement ; l'échec est constaté et corrigé par l'agent |

Le snapshot `read_chat_session` a été tronqué et relu depuis son fichier de sauvegarde. Les heures des messages sont en UTC ; les sorties d'outils ne portent pas toutes une heure.

## Déroulement constaté

1. Archive locale de 20 fichiers : `ARCHIVE lot_riemann.tar.gz 896550 octets, 20 fichiers`.
2. Transfert réussi : `TRANSFERT ok`.
3. Sauvegarde distante annoncée puis vide : `BACKUP_FICHIERS 0`.
4. `chown` avorté sur un nom terminé par un retour chariot.
5. L'extraction avait déjà eu lieu : 8 fichiers existants écrasés sans sauvegarde exploitable.

L'agent attribue la cause à la liste de chemins écrite par `Path.write_text` sous Windows : les fins de ligne `\r\n` restent attachées aux noms côté VPS. Le `\r` est directement visible dans l'erreur `chown` ; la cause `write_text` est un auto-rapport, non rejoué dans cette session.

## Sorties brutes

Échec de la phase unique sauvegarde + installation :

```text
ARCHIVE lot_riemann.tar.gz 896550 octets, 20 fichiers
TRANSFERT ok
BACKUP /opt/al-mizan/sauvegardes/lot-riemann-20261028-002247.tar.gz
BACKUP_SHA 63904ef8bd2821dd113a361aef254c86e4b2c77a90814f9fa99dec6ec45577bf
BACKUP_FICHIERS 0

STDERR:
chown: cannot access 'passerelle_api_vps_mizan.py'$'\r': No such file or directory

RC: 1
```

La sauvegarde annoncée ne contient rien :

```text
drwxr-xr-x 2 root   root   4096 Oct 28 00:22 lot-riemann-20261028-002247
-rw-r--r-- 1 root   root   159 Oct 28 00:22 lot-riemann-20261028-002247.tar.gz
```

Une archive gzip vide pèse 159 octets : le SHA-256 ci-dessus ne prouve donc pas qu'une sauvegarde existe.

## Fichiers réellement en place avant extraction

Le relevé `PRESENT` compte 8 fichiers déjà présents, donc écrasés : `passerelle_api_vps_mizan.py`, `web_cloud/oeuvre_universelle.html`, `_en.html`, `_ar.html`, `web_cloud/sitemap.xml`, `resultats/oeuvre_universelle/resume.json`, `manifeste_anteriorite.json`, `MANIFESTE_ANTERIORITE.md`. Les 12 autres chemins de l'archive étaient `ABSENT`.

Après l'extraction, l'état courant montre des fichiers en `root root 666`, par exemple :

```text
root root 666 101745 passerelle_api_vps_mizan.py
root root 666 122424 web_cloud/oeuvre_universelle.html
root root 666 426081 web_cloud/hypothese_riemann.pdf
root root 666  98583 resultats/oeuvre_universelle/resume.json
```

Le `chown` avorté explique le propriétaire `root` ; le mode `666` est un constat, pas une recommandation.

## Réparation

L'agent reconstruit une sauvegarde depuis les `.bak-*` existants, réapplique les propriétaires et revérifie :

```text
BACKUP_SHA 73ba09da5862312fdd279352c1b1c72eaa8ac0a94bbaae308df2ee1997c5e527
BACKUP_FICHIERS 8
ACTIVE active
NGINX active

RC: 0
HASH_IDENTIQUES 20 / 20
PROBE /riemann 200 text/html; charset=utf-8 91092
PROBE /oeuvre-universelle 200 text/html; charset=utf-8 120705
PROBE /api/v1/oeuvre-universelle 200 application/json; charset=utf-8 100561
```

Les `.bak-*` utilisés datent de `23:09` et `23:33` le 27/10, soit des déploiements antérieurs. Ils ne sont pas garantis égaux octet pour octet à l'état qui précédait l'écrasement de 00:22 ; ils ne doivent pas être présentés comme une restauration exacte.

## Reproduction locale du garde (hors production)

Fixture hors du Skill : trois chemins listés, dont un absent, `liste_crlf.txt` écrit avec `\r\n`. Les chemins de la fixture sont adaptés (`--force-local` pour `tar` sous Windows) ; la logique est celle de la phase A.

```text
write_text("a.txt\nb.txt\n")  -> 14 octets, 2 CR
write_bytes(b"a.txt\nb.txt\n") -> 12 octets, 0 CR

LF                        -> BACKUP_FICHIERS 2, archive 177 octets, rc 0
CRLF + garde              -> STOP liste CRLF, rc 2
CRLF sans garde + strip   -> BACKUP_FICHIERS 2, rc 0
CRLF sans garde ni strip  -> STOP sauvegarde vide, rc 3
phase B sans archive      -> STOP sauvegarde absente, rc 4
```

Le garde compte les octets CR avec `tr -cd '\r' | wc -c`. `grep -c $'\r'` a été écarté : sous Git Bash il a compté 2 lignes sur un fichier LF, donc il ne distinguait pas les deux cas. Sur le VPS, `tr` est également disponible.

## Lecture et limites

- Le compte `BACKUP_FICHIERS 8` est celui de la réparation, pas de la phase initiale (0).
- Le nombre de fichiers écrasés vient de la liste `PRESENT` (8) et du rapport de l'agent ; aucun diff fichier par fichier avant/après n'a été conservé.
- Aucune restauration n'a été exécutée en production : les sauvegardes existent, leur rejeu n'est pas prouvé.
- `sudo -n true` → 0 est établi par la mémoire projet, pas rejoué dans cette session ; le Skill demande de le revérifier.
- Le mot de passe envoyé à `sudo -S` avec `bash -s` a été recraché dans stderr lors d'un triage de journaux de la même session : ne plus transmettre de secret sur stdin.
- Les valeurs sont datées du 28/10/2026 ; les revérifier avant réutilisation.
