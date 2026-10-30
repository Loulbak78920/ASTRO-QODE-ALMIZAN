# Preuves — lot justice/restitution, forme de page et câblage du registre (30/10/2026)

## Source

| Élément | Valeur |
| :--- | :--- |
| Session | `bd9314ec-9a1f-4e04-a26f-618198732b6d`, titre « Résoudre équations avec code » |
| Lecture | 2026-10-30, `runtimeState = running`, `activeTurnId = 34a34a90…` (« Déployer /reglement-dettes-redistribution », encore `streaming`), `revision = 14`, `hasMoreBefore = true`, `turnLimit = 6` |
| Tour utile | demande initiale 2026-10-30T02:04:23Z (vidéo OneCoin, équations, code, restitution) ; déploiement du lot justice à 02:20:25Z ; vérification publique à 02:21Z |
| Portée retenue | Seul le lot justice/restitution, terminé et vérifié, est cité. Le tour règlement ouvert à 02:23:43Z était encore `streaming` à la lecture : ses sorties ne sont pas une preuve ici. Ce lot a ensuite été déployé séparément à 02:28Z, hors de ce dossier. |
| Correction utilisateur | aucune dans ce segment (le résumé de session, enregistrement 2168, le note explicitement) |

Les messages et les enregistrements sont en UTC (`Z`) ; les sorties d'outils sont horodatées par le système local. Les entrées de commandes proviennent du JSONL du projet (types `tool_use`), les sorties des `tool_result` appariés. Numéros de ligne cités : ligne du fichier JSONL, pas du message.

## 1. Forme de page imposée par `qualite_accessibilite_pages.py`

Le module `ASTRO-Q°ODE_SYSTEME/oeuvre_universelle/qualite_accessibilite_pages.py` code la forme en dur : `NB_TABLES = 4`, `NB_H2 = 9`, `NB_H3 = 13`, `NB_LIENS = 24`, `NB_STATUTS = 26` (lignes 80-84, relues sur disque le 2026-10-30), et `m0["cible_nombre"] == 11` (ligne 415). Les contrôles C-QA06 à C-QA13 comparent la page réelle à ces constantes.

Pages produites par `generer_page_justice_restitution.py` : 39 433 o (FR), 37 897 o (EN), 42 473 o (AR). Structure mesurée sur chacune : 1 h1, 9 h2, 13 h3, 4 tableaux, 26 pastilles de statut, 26 `th[scope]` dont 12 `row`, 24 `<a>`, 7 `hreflang`, 1 svg ; 13/13 contrôles numériques et 13/13 contrôles qualité (enregistrement 2168, section 3).

Décision de conception : les dix bases légales sont rendues en liste dans `#source`, pas en cinquième tableau, parce que C-QA08 exige exactement 4 tableaux. Ajouter un tableau « pour la lisibilité » casse le contrôle.

Piège d'interprétation : `analyser_pages()["resume"]["statuts"]` rend `{"OPÉRATIONNEL": 12, "SIMULÉ": 1}`. Ce décompte décrit les 13 contrôles du module qualité (12 calculés, 1 dérivé du CSS), pas les étiquettes de la page. Le module justice, lui, déclare `{"OPÉRATIONNEL": 0, "SIMULÉ": 11, "SPÉCIFIÉ": 2}`. Ne pas conclure à une incohérence entre les deux.

## 2. Synchronisation registre → hub → portail → sitemap → passerelle

L'ajout d'une entrée au registre (21e problème) casse des compteurs écrits en dur ailleurs. Points corrigés, tous constatés :

| Fichier | Changement | Preuve |
| :--- | :--- | :--- |
| `oeuvre_universelle/registre_problemes_monde.py` | `JUS-02` inséré avant `GOV-01` (ligne 555, strate D, `restitution_avoirs`, `lien="/justice-restitution"`) ; registre à 21 problèmes / 7 strates / 6 contrats | enregistrement 2168 |
| `oeuvre_universelle/modeles_reference.py` | `restitution_avoirs()` ligne 515 | idem |
| `oeuvre_universelle/generer_page_oeuvre.py` | trois `meta` remplacés par `f"{len(R.PROBLEMES)} …"` (FR ligne 77, EN 133, AR 189) ; l'arabe portait « عشرون » en toutes lettres | enregistrements 1785-1788 |
| `tests/test_oeuvre_universelle.py` | compteurs 20 → 21, `test_vingt_et_un_problemes_et_sept_strates`, `test_vingt_et_une_cartes_par_langue`, nouveau `test_restitution_avoirs_bornee` | enregistrement 2168 |
| `tests/test_site_public_mizan.py` | `nb_problemes` et `len(problemes)` 20 → 21 | idem |
| `web_cloud/portail_public_al_mizan.html` | carte `JUS-02` insérée avant `ECO-01`, tags existants non renumérotés | ligne 1815 (état relu) |
| `web_cloud/sitemap.xml` | 3 URL `/justice-restitution{,/en,/ar}` ; 50 `<loc>` au total | lignes 148, 154, 160 |
| `passerelle_api_vps_mizan.py` | 5 routes de page (lignes 175-179) et bloc JSON `/justice-restitution.json` + `/justice-restitution/resultats.json` (lignes 1102-1103) | état relu |

Avant ces corrections, `test_oeuvre_universelle` échouait avec `AssertionError: 21 != 20 : fr` sur l'ancien nom `test_dix_neuf_cartes_par_langue` (enregistrement 1823) : le nom du test était déjà faux avant le lot. Corriger l'assertion vers le compte honnête (21), jamais l'inverse.

Le hub régénéré porte 21 cartes par langue. Racine Merkle finale `2a13664d82f15d2c21b462a46f1f179e77cf25148be140d4122d75afba085272`, identique dans les trois pages hub, `resume.json` et le manifeste (enregistrement 1918 : `_fr True cards 21`, `_en True cards 21`, `_ar True cards 21`, `resume root True 21`).

La racine a changé trois fois : `42599f22…` → `4b490fad…` → `2a13664d…`. Ce n'est pas une dérive non expliquée : chaque rescellement suit une modification d'un fichier scellé (test, portail). Le portail est scellé ; les pages hub ne le sont pas, ce qui évite la circularité. L'ordre `tests → génération → déploiement` (invariant 10) reste la règle : un test lancé après la génération resscelle le manifeste sans réécrire les pages.

## 3. Lot additif isolé d'un lot voisin non déployé

Au moment du déploiement justice (02:20Z), le lot `reglement-dettes-redistribution` était présent localement mais non déployé. Le lot justice a donc été construit depuis des variantes élaguées, pas depuis la copie de travail :

- passerelle : suppression des routes règlement et du bloc JSON `0.ECO` ;
- sitemap : suppression des 3 URL règlement (`retires == 3` asserté) ;
- portail : suppression de la carte `ECO-01` ;
- assertions : `justice == 3`, `retro == 3`, jeton `reglement` absent, liens justice et rétro présents (un chacun).

À cette date, les routes `/reglement-dettes-redistribution` et `.json` répondaient 404 en public. Ce 404 est historique : le lot règlement a été déployé plus tard, à 02:28Z, dans un tour distinct. Ne pas s'en servir comme état courant.

## 4. Construction, compilation et archive

`ASTRO-Q°ODE_SYSTEME/.qoder/tmp/construire_lot_justice.py` construit `lot_justice/` (23 fichiers), archive `al_mizan_justice.tar.gz` (309 908 o) et une liste en LF (`write_bytes`).

`py_compile.compile(path)` écrit `__pycache__/<nom>.cpython-314.pyc` à côté du fichier compilé. Le premier build a donc échoué sur sa propre assertion d'absence de cache. Correction (enregistrement 1963) :

```python
py_compile.compile(
    str(LOT / "passerelle_api_vps_mizan.py"),
    cfile=str(RACINE / ".qoder" / "tmp" / "passerelle_lot_justice.pyc"),
    doraise=True,
)
assert not any("__pycache__" in p.parts for p in LOT.rglob("*"))
```

Autres erreurs du build : `FileNotFoundError` en copiant `lot_justice/oeuvre_universelle/…` (corrigé par `(LOT / nom).parent.mkdir(parents=True, exist_ok=True)`) ; `ModuleNotFoundError: module_ia_autonome_boucle_fermee_mizan` en lançant la passerelle du lot (Python ajoute le dossier du script, pas le cwd : `PYTHONPATH` vers la racine du dépôt) ; alias `python` Microsoft Store absent (`py -3`) ; fichier `/tmp` invisible depuis Python Windows (écrire dans `.qoder/tmp`).

## 5. Déploiement et preuves

Phase A : `BACKUP_FICHIERS 14`, `TAR_ENTRIES 14`, SHA-256 `181d53d1e6e0ba914093dc667fbd02566053cb26409f973aa4a17bc5c175c87f`, 214 085 o, sauvegarde `/opt/al-mizan/sauvegardes/lot-20261030-022025/sauvegarde.tar.gz` (enregistrement 2093). Neuf fichiers du lot étaient nouveaux ; les 14 autres existaient.

Phase B : rc 0, `TS=20261030-022025`, modes réappliqués (`666` pour passerelle, portail, sitemap, hub, tests ; `644` pour modules, doc, JSON, manifeste), redémarrage de `al-mizan-api-vps` (3 `.py` livrés), aucun `.pyc` récent.

Preuves consignées dans le rapport final de session (enregistrement 2200) : 23 fichiers déployés, **23/23 SHA-256 distants identiques aux locaux** ; 26/26 tests justice, 57/57 œuvre (sortie `Ran 57 tests … OK`, enregistrement 1837), 8/8 site public ; 13/13 contrôles numériques et 13/13 qualité.

Fenêtre nginx (enregistrement 2109), ancre `30/Oct/2026:02` :

```text
LIGNES 49
JUSTICE 8
5XX 0
404 8
```

Les 8 requêtes justice sont en 200. Extrait :

```text
[30/Oct/2026:02:21:01 +0000] "GET /justice-restitution.json HTTP/1.1" 200 27723
[30/Oct/2026:02:21:03 +0000] "GET /justice-restitution HTTP/1.1" 200 39485
[30/Oct/2026:02:21:03 +0000] "GET /justice-restitution/en HTTP/1.1" 200 37949
[30/Oct/2026:02:21:04 +0000] "GET /justice-restitution/ar HTTP/1.1" 200 42533
```

Le JSON public fait exactement 27 723 o, taille du fichier local. Les pages HTML journalisent 52 à 60 o de plus que le fichier (39 485 vs 39 433 ; 37 949 vs 37 897 ; 42 533 vs 42 473) : tramage chunked, pas une différence de contenu. `body_bytes_sent` ne prouve jamais l'égalité octet pour octet.

Les 8 réponses 404 de la fenêtre comprennent des sondes délibérées du lot règlement (encore non déployé) et du bruit de robots ; elles ne sont pas une régression des routes justice.

## 6. Faux négatif : guillemets du lien généré

La vérification du lien de la carte hub avec `href="/justice-restitution"` (guillemets doubles) rend 0. Le générateur du hub émet `href='/justice-restitution'` (guillemets simples), compté 1 ; le portail, lui, utilise des guillemets doubles. Chercher le jeton `/justice-restitution`, puis qualifier le style de guillemets, pour ne pas relancer un « correctif » sur un lien déjà servi.

## 7. Limites et statut des affirmations

| Affirmation | Statut |
| :--- | :--- |
| Forme 9 h2 / 13 h3 / 4 tableaux / 26 pastilles / 24 liens / 11 cibles ; 13/13 + 13/13 | vérifiée par sortie de session et relecture des constantes sur disque |
| 23/23 SHA-256 distants identiques ; sauvegarde 14 fichiers / 214 085 o | consignée dans le rapport final (enregistrement 2200) et la phase A (2093) ; non rejouée dans ce dossier |
| 26/26, 57/57, 8/8 tests | sorties de session (`Ran 26`, `Ran 57 … OK`, `Ran 8`) ; pas de rejeu dans ce dossier |
| 0 × 5xx, 49 lignes, 8 justice | sortie brute de la fenêtre nginx (2109) |
| Rendu visuel | **non vérifié** : `take_screenshot` a rendu `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE` (viewport 0×0) ; le contrôle est structurel/DOM seulement |
| Module 0 OPÉRATIONNEL / 11 SIMULÉ / 2 SPÉCIFIÉ | déclaré par le module ; montants = paramètres, pas mesures |
| Lot règlement non déployé | vrai à 02:20Z ; faux depuis 02:28Z (déploiement séparé) |

Restaurer : `tar -xzf /opt/al-mizan/sauvegardes/lot-20261030-022025/sauvegarde.tar.gz -C /opt/al-mizan/ASTRO-Q°ODE_SYSTEME && systemctl restart al-mizan-api-vps`. Les 9 fichiers ajoutés ne sont pas retirés par cette commande ; une restauration complète exige de les supprimer explicitement après relevé de leurs chemins.
