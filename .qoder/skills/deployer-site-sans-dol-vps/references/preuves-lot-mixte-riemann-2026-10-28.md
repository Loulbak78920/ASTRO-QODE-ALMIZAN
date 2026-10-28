# Preuves — lot mixte, modes et double racine Merkle (28/10/2026)

## Source

| Élément | Valeur |
| :--- | :--- |
| Session | `de5bacf6-50d0-42ce-b890-f3149acbbd91`, titre « Équations et résolution de l'ignorance » |
| Lecture | 2026-10-28, `runtimeState = ready`, `activeTurnId = null`, `revision = 21`, `hasMoreBefore = true`, `turnLimit = 12` |
| Demandes | 2026-10-28T00:03:28Z : page Riemann, figure et PDF ; 2026-10-28T00:31:35Z : « Corriger la page Riemann pour qu'elle soit trilingue » |
| Déploiement | 2026-10-28T00:43:25Z (script écrit), 00:43:33Z (correction), 00:43:35Z (exécution) |
| Vérifications | jusqu'à 00:46:56Z |
| Correction utilisateur | la première page était en français ; la trilingualisation est une demande ultérieure de l'utilisateur |

Les heures des messages et des sorties de la session sont en UTC. Le nom de sauvegarde `lot-trilingue-20261028-004344` est calculé sur le serveur et cohérent avec 00:43:44 UTC.

## Lot déployé — 19 fichiers, 13 existants, 6 nouveaux

`BACKUP_FICHIERS 13` et 13 lignes de modes correspondent aux 13 fichiers déjà présents. Les 6 autres n'existaient pas sur le VPS avant l'extraction.

| Fichier | SHA-256 local = distant | Octets | Avant |
| :--- | :--- | ---: | :--- |
| `passerelle_api_vps_mizan.py` | `7944197bb683a60a1f986d1bbaad1bee82539cd93f9f333edb44c7fee5fa86fd` | 102141 | existant |
| `moteur_triniter_observateur_multimodal_mizan.py` | `13ffe2db65554f90c6e225132f0dd7001dc854c6ce24cf47a3936a3dec83110a` | 31797 | existant |
| `oeuvre_universelle/generer_page_riemann.py` | `828ae5d593566254d6372912ab6fc88f5a1aacbb842e8ba59a93b6616f21b87f` | 47642 | existant |
| `oeuvre_universelle/manifeste_anteriorite.py` | `9b58a3726886e9d0c25ae128974d044f06ca232ed83a7d1157985762b9b6245f` | 7501 | existant |
| `web_cloud/hypothese_riemann.html` | `d052616c39fc0d10902068664aab1082c630927482a140aa993863738d68e770` | 77451 | existant |
| `web_cloud/hypothese_riemann.pdf` | `11a793000415798b797bca28ce51b70bf6dd3d30b9d5e99ff2a04980ccd7e118` | 406336 | existant |
| `web_cloud/hypothese_riemann.png` | `9f442027fe71e812aa0d6af64e2883783261415ddc8d7644ef5d4991d9104963` | 156934 | existant |
| `web_cloud/oeuvre_universelle.html` | `ed707f6e793ae7460fb9678ff30ec9e6b6129af617c8de891a213b01db345c4f` | 122424 | existant |
| `web_cloud/oeuvre_universelle_en.html` | `dba3cfccae6d7b3ee08e5e588b61a8c1f6d9812be491d31c19cef3c02af03269` | 118883 | existant |
| `web_cloud/oeuvre_universelle_ar.html` | `cd25c3df16f53e57088c751cf87dc4f50f0f1d14adc50136e2106c334d8ba3a0` | 128326 | existant |
| `web_cloud/sitemap.xml` | `d092cdf51e68d1257a4bdc5991336b732cc1ee90af49e01ab0d459cb726e37b9` | 5544 | existant |
| `resultats/oeuvre_universelle/manifeste_anteriorite.json` | `28035f51c20e8930570a2df720b0aab38d3043f0daba1f16319e0b627760d503` | 39427 | existant |
| `resultats/oeuvre_universelle/resume.json` | `28332dbfced2b80ec473c38b08f76426993bcb13c35c575beb0d249d0a73f84f` | 98583 | existant |
| `web_cloud/hypothese_riemann_en.html` | `f69b0cd69959f2e1ab44ec701adcd6b910a2f113e9bda541180d882c488f7fa3` | 76683 | **nouveau** |
| `web_cloud/hypothese_riemann_ar.html` | `e4312ce9be1b21437915ad4610b90da2f5f9eb845c0ca057efa32838c07c3529` | 78911 | **nouveau** |
| `resultats/oeuvre_universelle/manifeste_anteriorite.md` | `3db2705712d3932031e0382770ac5f3cbd1279ace8c2a8dc68326ab03ee3c73a` | 19541 | **nouveau** |
| `docs/API_PASSERELLE_VPS.md` | `0a92fdbe5096194f3f58b21116bb4311f19af55c1de8ae380316e029469e8ca9` | 28927 | **nouveau** |
| `tests/test_oeuvre_universelle.py` | `be691cc198559d7b8eb42f690cb9fcf15b50c9372e4e4d402e69a724971449d5` | 16754 | **nouveau** |
| `tests/test_site_public_mizan.py` | `ae9a9aa72af3965d3964a4c4f9ac8af8446601c502ce505c3b20fc8b36c8b133` | 17936 | **nouveau** |

Sauvegarde : `/opt/al-mizan/sauvegardes/lot-trilingue-20261028-004344/sauvegarde.tar.gz`, SHA-256 `32a501b3ae5397e81a814b87e80dcaf8af584b26b6128e585625edb6366f9058`, `BACKUP_FICHIERS 13`.

Après installation, le script compare les empreintes : `fichiers comparés: 19 écarts: 0`.

## Carte des modes (phase A)

Sortie brute de `stat -c '%n|%U|%G|%a'` pour les 13 fichiers existants :

```text
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/passerelle_api_vps_mizan.py|ubuntu|ubuntu|666
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/moteur_triniter_observateur_multimodal_mizan.py|ubuntu|ubuntu|666
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/oeuvre_universelle/generer_page_riemann.py|ubuntu|ubuntu|644
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/oeuvre_universelle/manifeste_anteriorite.py|ubuntu|ubuntu|644
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/hypothese_riemann.html|ubuntu|ubuntu|666
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/hypothese_riemann.pdf|ubuntu|ubuntu|644
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/hypothese_riemann.png|ubuntu|ubuntu|644
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/oeuvre_universelle.html|ubuntu|ubuntu|666
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/oeuvre_universelle_en.html|ubuntu|ubuntu|666
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/oeuvre_universelle_ar.html|ubuntu|ubuntu|666
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/web_cloud/sitemap.xml|ubuntu|ubuntu|666
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/resultats/oeuvre_universelle/manifeste_anteriorite.json|ubuntu|ubuntu|644
/opt/al-mizan/ASTRO-Q°ODE_SYSTEME/resultats/oeuvre_universelle/resume.json|ubuntu|ubuntu|644
```

Le script exécuté appliquait ensuite, pour chaque chemin extrait : le mode mappé s'il existait, sinon `ubuntu:ubuntu` et le mode de `web_cloud/hypothese_riemann.html` (`DEFAUT_MODE`, 666). Ce défaut unique a donc visé les six nouveaux fichiers, y compris les deux `.md` et les deux `.py`. **Aucun `stat` après extraction n'a été exécuté pour les nouveaux fichiers** : l'affirmation du rapport final « modes conservés (666 pages/passerelle, 644 JSON/PDF/PNG) » n'est prouvée que pour les fichiers mappés.

## Piège de correspondance `grep`

Premier jet du script :

```text
DEFAUT_MODE=$(grep '|web_cloud/hypothese_riemann.html$' /tmp/al_mizan_modes.txt | cut -d'|' -f4 || true)
ligne=$(grep -F "|$f" /tmp/al_mizan_modes.txt | head -1 || true)
```

Ces deux formes ne peuvent pas matcher : `%n` rend un chemin absolu, donc `web_cloud/...` est précédé de `/` et suivi de `|`, jamais précédé de `|` ni en fin de ligne. Correction appliquée à 00:43:33Z, avant l'unique exécution :

```text
DEFAUT_MODE=$(grep -F 'web_cloud/hypothese_riemann.html|' /tmp/al_mizan_modes.txt | cut -d'|' -f4 || true)
ligne=$(grep -F "$f|" /tmp/al_mizan_modes.txt | head -1 || true)
```

Reproduction locale, sur une ligne identique à la carte (fixture supprimée ensuite) :

```text
pat=[|web_cloud/hypothese_riemann.html] matches=0
pat=[|web_cloud/hypothese_riemann.html$] matches=0
pat=[web_cloud/hypothese_riemann.html|] matches=1
pat=[/web_cloud/hypothese_riemann.html|] matches=1
```

Le Skill retient `grep -F "/$f|"`, qui suppose un chemin relatif du type `web_cloud/...`.

## Tar produit sous Windows — modes

Sonde hors production (fichier local, `tarfile` Python, extraction locale) :

```text
local mode 0o666
member mode 0o666 uid/gid 0 0 uname  gname
extracted mode 0o666
```

Un membre de tar créé sous Windows ne porte donc pas le `644` voulu pour un JSON : côté Linux, sans `chmod`, il est recréé en `666` et, sans `chown`, en `root:root`. C'est le mode d'échec déjà observé le 28/10 à 00:22 (`root root 666`). Le `stat` final du Skill a été ajouté pour rendre ce point vérifiable.

## Boucle de modes de la phase B — fixture locale

Les lignes de la boucle documentée ont été extraites du bloc `bash` de SKILL.md et rejouées sur une fixture hors Skill : deux fichiers existants, deux nouveaux, table `stat` produite sur le poste.

```text
--- plan ---
passerelle_api_vps_mizan.py|Administrateur|UNKNOWN|644
web_cloud/oeuvre_universelle.html|Administrateur|UNKNOWN|644
web_cloud/nouvelle_page.html|ubuntu|ubuntu|644
resultats/nouveau.json|ubuntu|ubuntu|644
```

Les deux premiers viennent de la carte (propriétaire `Administrateur`, celui du poste Windows) ; les deux nouveaux de l'héritage par voisin (`ubuntu:ubuntu`, mode du fichier sœur). MSYS ne conserve pas `chmod 666` : les modes sœurs rendent `644`, donc la fixture prouve la correspondance et l'héritage, pas les valeurs 666/644 du VPS.

Repli sans voisin du même type (`docs/guide.html` sans autre `.html`, `docs/note.txt` sans autre `.txt`) :

```text
web_cloud/page.html|Administrateur|UNKNOWN|644
docs/guide.html|ubuntu|ubuntu|666
docs/note.txt|ubuntu|ubuntu|644
```

Gardes `test -f` / comptage, lignes recopiées du bloc, exécutées avec un manifeste de deux lignes :

```text
ok               rc=0
fichier_absent   rc=5
compte_faux      rc=5
```

## Double racine Merkle

`tests.test_oeuvre_universelle` appelle `construire_manifeste(ecrire=True)` (ligne 198 du fichier de tests) : lancer la suite après la génération rescelle le manifeste sans réécrire les pages.

| Heure UTC | Événement | Racine observée |
| :--- | :--- | :--- |
| 00:37:32 | `generer_page_oeuvre.py` : pages + `resume.json` | `e6bf222e…` (`genere_le_utc 2026-10-28T00:37:32Z`) |
| 00:39:28 | suite `tests.test_oeuvre_universelle` | manifeste rescellé |
| 00:40:09 | `manifeste_anteriorite.py --verifier` | `43b0bf0a…`, `ok: true`, `156` fichiers |
| 00:40:35 | `grep -c 43b0bf0a…` sur 3 pages + `resume.json` | `0` dans les quatre fichiers |
| 00:40:39 | lecture de `resume.json` | `e6bf222e…`, `00:37:32Z` |
| 00:40:47 | régénération + `--verifier` | `43b0bf0a…` partout |
| 00:40:54 | comptage dans 3 pages + `resume.json` | `1`, `1`, `1`, resume `True`, `156` |
| 00:41:00 | 3 suites ensemble | `Ran 47 tests … OK` (rescelle à nouveau) |
| 00:41:27 | après la suite | manifeste `43b0bf0a… 00:41:14Z`, resume `43b0bf0a… 00:40:49Z` |
| 00:41:48 | régénération finale + `--verifier` + empreintes | `43b0bf0a…` ; lot de 19 fichiers figé |

Sortie du contrôle qui a révélé la divergence :

```text
web_cloud/oeuvre_universelle.html:0
web_cloud/oeuvre_universelle_en.html:0
web_cloud/oeuvre_universelle_ar.html:0
resultats/oeuvre_universelle/resume.json:0
No matches found
```

Le vérificateur ne pouvait pas la voir :

```python
def verifier_manifeste() -> Dict[str, Any]:
    ...
    manifeste = json.loads(chemin.read_text(encoding="utf-8"))
    for f in manifeste.get("fichiers", []):
        ...
        if actuel != f["sha256"]:
            ecarts.append(...)
    return {"ok": not ecarts, ..., "racine_merkle_sha256": manifeste.get("racine_merkle_sha256")}
```

Il compare les hachages des fichiers listés au manifeste **stocké** et réaffiche la racine stockée. Les pages régénérées après lui, ou générées avant lui, restent cohérentes avec ce manifeste tant que leurs octets n'ont pas changé ; leur racine embarquée peut différer sans qu'aucun écart ne soit signalé.

Après la suite de 00:41:00, la racine reste `43b0bf0a…` mais l'estampille du manifeste (`00:41:14Z`) diffère de celle du `resume.json` (`00:40:49Z`) : la régénération finale de 00:41:48Z a réaligné les deux avant l'envoi.

## Enveloppe de l'API manifeste

Premier contrôle direct :

```text
Traceback (most recent call last):
  File "<stdin>", line 29, in <module>
KeyError: 'racine_merkle_sha256'
```

Clés réelles de la réponse : `['succes', 'manifeste']`, puis `['titre', 'auteur', 'genere_le_utc', 'nb_fichiers', 'octets_total', 'racine_merkle_sha256', 'fichiers', 'preuve_integrite', 'preuve_anteorite_legale', 'causalite_mondiale_prouvee', 'limite', 'instructions']`. Lecture correcte : `json["manifeste"]["racine_merkle_sha256"]`.

## Faux FAIL de parité trilingue

Premier contrôle, écrit avec des guillemets doubles et un comptage naïf :

```text
FAIL hreflang x3 fr
FAIL hreflang x3 en
FAIL hreflang x3 ar
OK   x-default
FAIL switcher 3x all
FAILS 4
```

Le HTML produit est pourtant conforme :

```text
9:<link rel='alternate' hreflang='fr' href='https://www.al-mizan.world/riemann'>
10:<link rel='alternate' hreflang='en' href='https://www.al-mizan.world/riemann/en'>
11:<link rel='alternate' hreflang='ar' href='https://www.al-mizan.world/riemann/ar'>
88:...<span class='langues'><a class='langue on' ...>FR</a><a class='langue' ...>EN</a><a class='langue' ...>العربية</a></span>
```

`hreflang=` est en guillemets simples ; `count("class='langue")` compte aussi `class='langues'`, d'où 4 au lieu de 3. Contrôle corrigé, sur les pages générées puis sur le site :

```text
OK   hreflang alternates = 3
OK   switcher links = 3
OK   selected per lang
OK   rtl css present
OK   8 equations each
OK   no leftover fr in en body
OK   no leftover fr in ar body
FAILS 0
```

## Vérifications en direct

17 contrôles de contenu, `FAILS 0` : mentions « non démontrée » / « aucune démonstration » / « unproven », `dir="rtl"` et formulation arabe, `hreflang`, sélecteur à trois langues, canoniques, PDF et PNG **binairement identiques**, racine `43b0bf0a…` et `156` fichiers via l'API, sitemap EN/AR.

Routes (extrait) :

```text
/riemann                                 200 text/html; charset=utf-8 75422
/riemann/en                              200 text/html; charset=utf-8 74654
/riemann/ar                              200 text/html; charset=utf-8 76882
/hypothese-riemann.pdf                   200 application/pdf 406336
/hypothese_riemann.png                   200 image/png 156934
/api/v1/oeuvre-universelle/manifeste     200 application/json; charset=utf-8 40417
```

Les pages EN/AR locales (76683 et 78911 octets) diffèrent en brut du contenu servi (74654 et 76882) ; après normalisation LF, les deux comparaisons rendent `True`. C'est le comportement déjà documenté au §8 du SKILL.md.

Journaux, fenêtre `28/Oct/2026:00:20` :

```text
LINES 142
RIEMANN_STATUS      46 200       2 301
RIEMANN_5XX 0
TOTAL_5XX 0
TOTAL_404 10
ERROR_LOG_TAIL
```

## Limites

- Les modes finaux des six nouveaux fichiers n'ont pas été imprimés ; le défaut unique (666 de la page sœur) est une lecture du script, pas une mesure après extraction.
- Le `grep` fautif est resté dans le premier jet du script mais n'a jamais été exécuté en production : correction à 00:43:33Z, exécution à 00:43:35Z.
- La sonde tar et la sonde `grep` sont locales (Windows, `tarfile` / Git Bash) ; elles expliquent le mécanisme, elles ne mesurent pas le VPS.
- La fixture de la phase B n'exécute ni `chown` ni `chmod` (absents sous MSYS pour ces propriétaires) et ses modes sont ceux que MSYS rapporte ; l'application après extraction reste non rejouée. Le garde `rc=4` (sauvegarde absente) n'a pas été exercé, seul le garde des modes (`rc=5`).
- Aucun rendu visuel navigateur ; validation structurelle et sur le contenu servi uniquement.
- Le PDF reste en français ; seule la page est trilingue.
- Aucune restauration n'a été rejouée : la sauvegarde existe, son rejeu n'est pas prouvé.
- La référence CRLF cite `revision = 32` pour une lecture antérieure ; celle-ci rend `21`. Les instantanés ne sont pas comparables (fenêtre et `turnLimit` différents) et aucune conclusion n'en est tirée.
- Valeurs datées du 28/10/2026 ; les revérifier avant réutilisation.
