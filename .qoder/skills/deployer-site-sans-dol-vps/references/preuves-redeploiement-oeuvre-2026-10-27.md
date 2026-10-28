# Preuves — redéploiement du lot « œuvre universelle » (27/10/2026)

## Source

| Élément | Valeur |
| :--- | :--- |
| Session | `9948e777-3bfe-4fbe-81f2-f538f0479ee3`, titre « 创建可复用技能 » |
| Lecture | 2026-10-28, `runtimeState = running`, `revision = 11`, `hasMoreBefore = false` |
| Demandes | 23:29:55Z « Redéployer la page sur al-mizan.world » ; 23:35:39Z « Vérifier le rendu visuel sur al-mizan.world » ; 23:44:09Z « ouvrir le navigateur in-app et relancer une capture sur /oeuvre-universelle » |
| Correction utilisateur | aucune sur le déploiement ; le faux négatif des journaux est une auto-correction de l'agent |

Les heures des messages sont en UTC. Les sorties d'outils sont datées en heure locale du poste (UTC+1) lorsqu'elles le sont.

## Périmètre lu dans la passerelle

| Route | Fichier |
| :--- | :--- |
| `/oeuvre-universelle`, `/oeuvre-universelle/` | `web_cloud/oeuvre_universelle.html` |
| `/oeuvre-universelle/en` | `web_cloud/oeuvre_universelle_en.html` |
| `/oeuvre-universelle/ar` | `web_cloud/oeuvre_universelle_ar.html` |
| `/api/v1/oeuvre-universelle` | `resultats/oeuvre_universelle/resume.json` |
| `/api/v1/oeuvre-universelle/manifeste` | `resultats/oeuvre_universelle/manifeste_anteriorite.json` |

Les routes proviennent du routeur (`passerelle_api_vps_mizan.py`, entrées `/oeuvre-universelle*` et `/api/v1/oeuvre-universelle*`), pas des noms de fichiers.

## Fichiers déployés — 5, même sauvegarde

Sauvegarde distante : `.bak-20261027-233326`. Propriétaire : `ubuntu:ubuntu` dans tous les cas.

| Fichier | SHA-256 avant | SHA-256 après | Mode |
| :--- | :--- | :--- | :--- |
| `web_cloud/oeuvre_universelle.html` | `5eef92fc3dcfd72471bb53f5358f291f564910bdab55717da4af954ea3941aaa` | `2a25372ee91aad648fc46da26bd705da115cde33d9263566cfa3f6863faf06e2` | `666` |
| `web_cloud/oeuvre_universelle_en.html` | `db122f5a3bdf01dee89364629c7ef0a5b355705bdbbef4060d0003d11b3fd326` | `d7a03de5df4fdc1af0f35c05e4ceadee48d5718cca38d7059598830e76a58486` | `666` |
| `web_cloud/oeuvre_universelle_ar.html` | `a83f3a2e947d1ebbd273fa2ce97a3ed9ac9ef6dfbe4a5100c69eca0fae3d5545` | `23bde38178df85bd2c24b602ca50d51100a1c011be464433fe6591e256276150` | `666` |
| `resultats/oeuvre_universelle/resume.json` | `5b5ff89a9851fb51db9a33b497f91770d23498e035e71ce8822141f82b932046` | `e24ca7cf99cfc2d03035a0c89e0311f4a136988da7b58cbe1b236fc470f6f4ec` | `644` |
| `resultats/oeuvre_universelle/manifeste_anteriorite.json` | `cf165d41b534cdaaf5ea314d2613e19284671f88bd93b508048acceee36284a4` | `a597e9a918007061bdeef3235363e2830b8e9335a318fe94983bdbc17deafe45` | `644` |

L'égalité SHA-256 local/distant a été revérifiée après installation. Les empreintes distantes avant remplacement correspondaient au scellement précédent : aucune version plus récente n'a été écrasée.

## Vérification en direct

```text
/oeuvre-universelle HTTP 200 raw_eq False norm_eq True utc True root True
/oeuvre-universelle/en HTTP 200 raw_eq False norm_eq True utc True root True
/oeuvre-universelle/ar HTTP 200 raw_eq False norm_eq True utc True root True
/api/v1/oeuvre-universelle HTTP 200 has_utc True has_root True
/api/v1/oeuvre-universelle/manifeste HTTP 200 has_utc True has_root True
```

Racine Merkle : `9e47b14b24ef39240fd00623ee1871e6c465e63ae3bd115322fd6fac598be86d`. Estampille affichée : `2026-10-27T23:26:32Z`.

Contrôle HTTP normalisé (préfixes de 16 caractères affichés par le script) :

```text
200 /oeuvre-universelle      bytes=109428 sha256_norm=a966616b9715d3a7 equal=True
200 /oeuvre-universelle/en   bytes=107105 sha256_norm=b8d75db4a55b4fb6 equal=True
200 /oeuvre-universelle/ar   bytes=104553 sha256_norm=84d82d3b9cc68f73 equal=True
```

`raw_eq = False` est attendu : la passerelle lit les pages avec `read_text` et normalise CRLF en LF.

## Aucun redémarrage

`_servir_page_web_cloud` ouvre le HTML à chaque requête ; le handler API ouvre `resume.json` et `manifeste_anteriorite.json` à chaque requête. Le nouveau contenu et la nouvelle estampille ont été servis immédiatement après l'installation, sans redémarrage du service.

## Régénération du manifeste — même racine, pages différentes

| Passe | UTC du scellement | Racine Merkle | `oeuvre_universelle.html` |
| :--- | :--- | :--- | :--- |
| 1 | `2026-10-27T23:25:59Z` | `9e47b14b…be86d` | `74fff61023375394` (préfixe affiché) |
| 2 | `2026-10-27T23:26:32Z` | `9e47b14b…be86d` | `2a25372ee91aad648fc46da26bd705da115cde33d9263566cfa3f6863faf06e2` |

Même racine et mêmes compteurs (`149` fichiers, `7 597 390` octets), mais les pages changent : elles affichent `genere_le_utc`, `nb_fichiers` et `octets_total`. La passe 1 a produit les pages déployées avant régénération ; la passe 2 a produit celles qui ont été redéployées. Toute régénération impose donc de redéployer les trois pages et les deux JSON.

## Journaux — faux négatif puis lecture correcte

Droits constatés :

```text
-rw-r----- 1 www-data adm 1418046 Oct 27 23:34 access.log
-rw-r----- 1 www-data adm 1676578 Oct 26 23:59 access.log.1
wc: /var/log/nginx/access.log: Permission denied
      0 total
```

Triage délégué avant correction :

```text
RC=0 OUT=LINES 0 5XX 0 404 0 ERR=
RC=0 OUT=0 ERR=
```

Le stderr du premier triage était vide ; la cause (fichier `640 www-data:adm`) est établie par `ls -l` et par le `Permission denied` de `wc`, pas par cette sortie.

Lecture avec `sudo -S`, mot de passe sur stdin (méthode historique ; depuis, `sudo -n` est préféré — invariant 5 du SKILL.md) :

```text
OUT SINCE 27/Oct/2026:23:25 LINES 54 5XX 0 404 1 OEUVRE 10
ERR
```

Le seul 404 est un scan de robot : `172.69.150.107 404 /wp-admin/install.php?step=1`. Dix requêtes sur `oeuvre-universelle` dans la fenêtre.

## Contrôle navigateur

La capture visuelle a échoué une fois avec `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE` (`viewport=0x0`, `visible=false`, `attached=false`, `visibilityState=hidden`). Aucune boucle de réessai.

Contrôle structurel DOM sur les trois routes : `lang`/`dir` corrects (`ar` en `rtl`), racine et estampille présentes, `149` fichiers, `28` lignes de tableaux, aucune cellule vide, aucune erreur console. La typographie, les espacements et le rendu mobile restent non observés.

## Piège Windows — Python inline

Deux échecs de syntaxe avec du code multiligne passé en `-c` :

```text
File "<stdin>", line 18
    actual={str(p.relative_to(R)).replace('\','/') for p in _fichiers()}
SyntaxError: unterminated string literal (detected at line 18)

File "...\.qoder\tmp\check_logs_nginx.py", line 18
    '{printf \"LINES %d 5XX %d 404 %d\\n\", n, f5+0, f404+0}'"
SyntaxError: unterminated string literal (detected at line 18)
```

La correction a consisté à écrire le script avec Write, puis à l'exécuter.

## Limites

- Aucune preuve visuelle : capture indisponible ; seules les assertions DOM ont été obtenues.
- Aucun retour arrière exécuté : les sauvegardes existent, mais aucune restauration n'a été testée.
- Le premier déploiement des pages de l'œuvre n'est pas dans cette session ; elle ne contient que le redéploiement des cinq fichiers.
- Le mode `666` des pages est un constat, pas le résultat d'un audit de sécurité.
- Les valeurs sont datées du 27–28/10/2026 ; les revérifier avant réutilisation.
