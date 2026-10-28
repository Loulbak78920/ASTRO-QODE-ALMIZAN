# Cas vérifié — page Riemann trilingue (2026-10-28)

## Source

- Session : `de5bacf6-50d0-42ce-b890-f3149acbbd91`, titre « Équations et résolution de l'ignorance ».
- État lu : `runtimeState=ready`, `activeTurnId=null`, `revision=23`, `hasMoreBefore=true`.
- Fenêtre lue : les 8 derniers messages. L'historique antérieur n'a pas été lu ; aucune conclusion de ce document ne s'appuie sur lui.
- Demandes humaines identifiées :
  - `2026-10-27T23:02:42.270Z` — « Déployer les pages et routes sur le VPS ».
  - `2026-10-28T00:31:35.799Z` — « Corriger la page Riemann pour qu'elle soit trilingue ».
- Accord de déploiement donné dans la session pour le lot de 19 fichiers (« Déployer maintenant »). Cet accord ne vaut pas pour un lot ultérieur.

## Artefacts constatés

Valeurs relevées sur disque le 2026-10-28 après le déploiement. Elles peuvent avoir changé depuis ; les recalculer avant de s'en servir.

| Fichier | Octets | SHA-256 |
|---|---:|---|
| `oeuvre_universelle/generer_page_riemann.py` | 47 642 | `828ae5d593566254d6372912ab6fc88f5a1aacbb842e8ba59a93b6616f21b87f` |
| `web_cloud/hypothese_riemann.html` | 77 451 | `d052616c39fc0d10902068664aab1082c630927482a140aa993863738d68e770` |
| `web_cloud/hypothese_riemann_en.html` | 76 683 | `f69b0cd69959f2e1ab44ec701adcd6b910a2f113e9bda541180d882c488f7fa3` |
| `web_cloud/hypothese_riemann_ar.html` | 78 911 | `e4312ce9be1b21437915ad4610b90da2f5f9eb845c0ca057efa32838c07c3529` |
| `web_cloud/hypothese_riemann.pdf` | 406 336 | `11a793000415798b797bca28ce51b70bf6dd3d30b9d5e99ff2a04980ccd7e118` |
| `web_cloud/hypothese_riemann.png` | 156 934 | `9f442027fe71e812aa0d6af64e2883783261415ddc8d7644ef5d4991d9104963` |
| `web_cloud/sitemap.xml` | 5 544 | `d092cdf51e68d1257a4bdc5991336b732cc1ee90af49e01ab0d459cb726e37b9` |
| `passerelle_api_vps_mizan.py` | 102 141 | `7944197bb683a60a1f986d1bbaad1bee82539cd93f9f333edb44c7fee5fa86fd` |
| `oeuvre_universelle/manifeste_anteriorite.py` | 7 501 | `9b58a3726886e9d0c25ae128974d044f06ca232ed83a7d1157985762b9b6245f` |
| `resultats/oeuvre_universelle/manifeste_anteriorite.json` | 39 427 | `28035f51c20e8930570a2df720b0aab38d3043f0daba1f16319e0b627760d503` |
| `resultats/oeuvre_universelle/resume.json` | 98 583 | `28332dbfced2b80ec473c38b08f76426993bcb13c35c575beb0d249d0a73f84f` |

Manifeste : 156 fichiers, racine `43b0bf0a5ae1d575458841f0ff023f2f84352430f2e9af712ebede12d4a697d1`, généré à `2026-10-28T00:41:49Z`. PDF : 11 pages (recompté avec pypdf).

## Portée des preuves

- **Recalculé localement lors de la création du Skill** : empreintes et tailles des fichiers ci-dessus, comptage des blocs et titres d'équations, exécution du script de parité (89 contrôles, 0 échec, code 0), contrôles négatifs sur copies mutées hors du Skill.
- **Repris du rapport de session, non rejoués** : 47 tests, déploiement 19/19, sauvegarde, journaux nginx, 404 attribués. Les tests régénèrent le manifeste et le déploiement touche la production : ils n'ont pas été relancés pour documenter ce Skill.
- **Non vérifié** : rendu visuel navigateur, contenu réellement servi après la date du 2026-10-28.

## Étapes vérifiées

1. **Dictionnaire** : `LANGUES = ("fr", "en", "ar")`, `CHEMINS` à trois routes, `PAGES` à trois chemins. `T` contient 43 clés par langue, dont 8 titres d'équations, 5 entrées de navigation, 3 actions et 3 en-têtes de tableaux. `dir` vaut `ltr` en FR/EN et `rtl` en AR.
2. **Génération** : trois pages complètes, une figure PNG et SVG en ligne, un PDF FR. Tailles ci-dessus.
3. **Contrôles** : 8 titres d'équations par langue ; 9 blocs `<div class="eq…">` par page (un bloc `eq-cle` sans titre) ; 3 alternates + x-default ; canonique propre à chaque langue ; sélecteur FR/EN/العربية avec un seul actif ; formulaire, tableaux, `pre` et `code` en `direction:ltr` dans la page arabe ; aucun résidu FR dans les corps EN/AR.
4. **Passerelle** : 9 routes de page (3 canoniques, 3 alias `hypothese-riemann`, 3 alias `oeuvre-universelle/riemann`), 3 alias PDF, 2 alias PNG, servis en UTF-8.
5. **Sitemap** : trois URL `/riemann`, `/riemann/en`, `/riemann/ar`, plus le PDF.
6. **Manifeste** : trois pages, le PDF et le PNG ajoutés aux globs ; manifeste et œuvre régénérés.
7. **Tests** : 47 tests verts (30 œuvre, 8 site public, 9 spectre Triniter).
8. **Déploiement** : 19 fichiers, 19/19 SHA-256 identiques local/distant ; sauvegarde de 13 fichiers existants (`lot-trilingue-20261028-004344`, SHA-256 `32a501b3…`), modes conservés, service et nginx actifs.
9. **Journaux** : 142 lignes, 46×200 + 2×301 sur les routes concernées, 0 réponse 5xx, `error.log` vide. Les 10×404 sont des sondes robots et deux accès par nom de fichier non servis par conception.

## Échecs observés et corrections

| Échec | Cause réelle | Correction |
|---|---|---|
| `FAIL hreflang x3 fr/en/ar` sur les trois pages | l'assertion cherchait `hreflang="fr"` alors que le générateur écrit `hreflang='fr'` ; le `x-default` est en guillemets doubles | asserter une regex tolérante aux deux formes ; le balisage était correct |
| Sélecteur compté trop haut | `class='langues'` était compté comme un lien de langue | compter les `<a class='langue…>` du bloc, pas les classes |
| 8 titres d'équations pour 9 blocs | un bloc `eq-cle` n'a pas de titre | asserter titres `= 8` et blocs `>= 8`, jamais l'égalité |
| Racine Merkle incohérente | la suite de tests régénère le manifeste après la génération des pages ; les pages gardaient `e6bf222e…` alors que le manifeste portait `43b0bf0a…` | tout régénérer après le dernier changement, puis asserter page / `resume.json` / manifeste |
| `KeyError: 'racine_merkle_sha256'` | le JSON d'API imbrique la racine sous `manifeste` | lire `donnees["manifeste"]["racine_merkle_sha256"]` |
| `SyntaxError: unterminated string literal` | script Python inline mêlant apostrophes et guillemets | écrire le script dans un fichier temporaire avant exécution |

## Limites

- Le PDF reste **en français** : dossier destiné à l'Institut Clay, pas un document trilingue. La page l'indique explicitement.
- Aucune validation visuelle navigateur n'a été faite ; la validation est structurelle et porte sur le contenu servi.
- L'hypothèse de Riemann reste **non démontrée** dans les trois langues ; ce lot n'ajoute aucune revendication de preuve ni de prix.
- Les valeurs de ce document sont un instantané du 2026-10-28 ; elles ne prouvent pas l'état actuel.

## Reproduction du contrôle de parité

Remplacer `SKILL_DIR` par le répertoire installé de ce Skill et `RACINE` par la racine du projet. Commande en lecture seule, exécutable depuis n'importe quel répertoire.

```bash
# cwd : libre ; SKILL_DIR et RACINE remplacés avant exécution
py -3 -B "<SKILL_DIR>/scripts/verifier_parite_trilingue.py" \
  --racine "<RACINE>" \
  --generateur "oeuvre_universelle/generer_page_riemann.py"
```

Résultat attendu sur cet instantané : 89 contrôles, 0 échec, `RESULT: PASS`, code retour 0.
