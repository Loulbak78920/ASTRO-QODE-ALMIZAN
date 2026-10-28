---
name: generer-page-publique-trilangue
description: "Convertir une page publique Al-Mizan en version trilingue FR/EN/AR depuis un générateur Python unique : dictionnaire T aux clés strictement égales, constantes LANGUES/CHEMINS/PAGES, sélecteur à trois langues, canonique par langue, trois alternates hreflang plus x-default, RTL avec formules, tableaux et code forcés en LTR, figure neutre en langue, PDF français assumé, puis câblage des routes de la passerelle, du sitemap, des globs du manifeste, des tests et de la documentation, avant validation locale et redéploiement confirmé. Utiliser pour rendre trilingue une page existante (Riemann, œuvre universelle), corriger un sélecteur ou des alternates, ajouter l'arabe RTL, ou contrôler la parité des traductions avant publication. 用于把 Al-Mizan 公共页面改为法语、英语、阿拉伯语三语版本：统一翻译字典、hreflang、RTL、页面路由、sitemap、清单与测试。"
---

# Générer une page publique trilingue

## Objectif

Produire trois pages HTML complètes (FR, EN, AR) depuis un seul générateur, avec en-têtes linguistiques corrects, arabe en RTL, figure scientifique neutre, puis câbler les routes, le sitemap, le manifeste, les tests et la documentation. Le flux a été exécuté et vérifié sur la page Riemann le 2026-10-28 ; le détail des preuves est dans `references/cas-riemann-2026-10-28.md`.

## Frontière avec les autres Skills

| Besoin | Skill à utiliser |
|---|---|
| Générer ou corriger les trois pages, le sélecteur, les alternates, le RTL, la figure, le PDF FR | ce Skill |
| Assertions structurelles génériques, échappement des chaînes, navigateur de repli | `verifier-page-generee-multilingue` |
| Sauvegarde, envoi sur le VPS, redémarrage, journaux nginx | `deployer-site-sans-dol-vps` |
| Contrôle de forme du paquet Skill après écriture | `skill-file-qa` |

Ne pas recopier ici la chaîne de déploiement : la charger depuis `deployer-site-sans-dol-vps`, et seulement après accord explicite sur le lot.

## 1. Invariants

1. **Un seul générateur, un seul dictionnaire.** Chaque langue est une entrée de `T` ; aucun texte visible ne reste en dur dans le corps HTML.
2. **Les clés de `T` sont identiques dans toutes les langues.** Une clé manquante est une page incomplète, pas une traduction partielle acceptable. Sur la page Riemann : 43 clés par langue.
3. **Les routes ont une source unique.** `CHEMINS` alimente le canonique, les alternates, le sélecteur et la passerelle. Aucune URL n'est recopiée à la main dans le corps.
4. **Chaque page déclare sa langue et sa direction.** `lang="fr|en|ar"` ; `dir="rtl"` uniquement pour l'arabe.
5. **Trois alternates et un x-default.** Le x-default pointe la version française. Ne jamais compter les `hreflang` bruts : le sélecteur en ajoute un par langue.
6. **Le RTL ne s'applique jamais aux mathématiques.** `html[dir="rtl"]` force `direction:ltr` et `text-align:left` sur les formules, tableaux, `pre` et `code`.
7. **La figure reste neutre en langue.** Libellés mathématiques et symboles uniquement, jamais de texte arabe façonné par matplotlib. Une seule figure partagée, PNG et SVG en ligne, avec légende traduite par langue.
8. **Le PDF reste en français.** C'est un dossier destiné à l'Institut Clay, pas un document trilingue. La page doit le dire (`note_pdf`) au lieu de laisser croire à un PDF traduit.
9. **La traduction ne change aucune revendication.** Statut épistémique, badges, limites et absence de preuve sont traduits, jamais adoucis ni supprimés.
10. **Le lot page + API est atomique.** Les pages, la figure, le PDF, la passerelle, le sitemap, le manifeste régénéré, les tests et la doc partent ensemble.

## 2. Étape 0 — Figer la base

Avant toute écriture :

1. Relever `size`, `mtime` et `SHA-256` du générateur, des trois pages, du PDF, du PNG, du sitemap et de la passerelle.
2. Identifier les points d'intégration réels : routes de la passerelle, sitemap, globs du manifeste, tests, table de routes de la documentation, capacité du moteur Triniter.
3. Lire le générateur existant et conserver ce qui fonctionne (vérification numérique, textes honnêtes, mise en page) ; ne pas réécrire une page déjà valide pour le seul plaisir de l'uniformiser.

```bash
# cwd : <RACINE> ; <RACINE> = C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME
grep -n -m 40 "riemann" passerelle_api_vps_mizan.py
grep -n "<loc>.*riemann" web_cloud/sitemap.xml
grep -n "hypothese_riemann" oeuvre_universelle/manifeste_anteriorite.py
```

Remplacer le motif `riemann` par le nom de la nouvelle page. Vérifier que chaque point trouvé sera modifié dans le même lot.

## 3. Constantes et dictionnaire

Ajouter en tête du générateur :

```python
LANGUES = ("fr", "en", "ar")
CHEMINS = {"fr": "/riemann", "en": "/riemann/en", "ar": "/riemann/ar"}
PAGES = {
    "fr": WEB_CLOUD / "hypothese_riemann.html",
    "en": WEB_CLOUD / "hypothese_riemann_en.html",
    "ar": WEB_CLOUD / "hypothese_riemann_ar.html",
}
```

Construire `T` avec, pour chaque langue, au minimum : `lang`, `dir`, `locale`, `titre`, `description`, `og_titre`, `nav`, `h1`, `lead`, badges, avertissements, sections, légende de figure, en-têtes de tableaux, `eq_titres`, `actions`, `note_pdf`, `pied`.

Règles de rédaction :

- Traduire les **huit titres d'équations** et les en-têtes de tableaux ; les formules elles-mêmes restent identiques.
- Conserver les valeurs numériques calculées hors du dictionnaire : elles sont injectées par `_corps`.
- Adapter le séparateur décimal (`_fr` avec espace fine insécable et virgule ; `_n` pour EN/AR) sans changer les chiffres.
- Écrire l'arabe avec un vocabulaire mathématique vérifié ; ne pas translittérer les formules.
- Garder dans chaque langue la phrase de statut (« non démontrée » / *unproven* / **غير مُبرهنة**) et la phrase de limites.

Contrôler la parité avant de générer :

```bash
# cwd : <RACINE> ; <SKILL_DIR> = C:\Users\Administrateur\.qoder\skills\generer-page-publique-trilangue
py -3 -B "<SKILL_DIR>/scripts/verifier_parite_trilingue.py" \
  --racine "<RACINE>" \
  --generateur "oeuvre_universelle/generer_page_riemann.py"
```

Le script lit le générateur par AST (aucune exécution) et les pages produites. Il vérifie : parité des clés, clés structurantes, longueurs de `nav`/`actions`/`eq_titres`, `lang`/`dir`, canonique, alternates et x-default, sélecteur à trois liens, nombre de titres d'équations, résidus d'une autre langue, figure neutre, signatures PDF/PNG. Il imprime `RESULT: PASS` (code 0), `RESULT: FAIL` (code 1) ou une erreur d'usage (code 2).

## 4. Sélecteur et en-tête de page

`_nav(lang)` doit produire **exactement trois** liens de langue, avec la langue courante marquée :

```python
langues = "".join(
    f"<a class='langue{' on' if code == lang else ''}' href='{CHEMINS[code]}' "
    f"hreflang='{code}' lang='{code}'>{libelle}</a>"
    for code, libelle in (("fr", "FR"), ("en", "EN"), ("ar", "العربية"))
)
```

- Les liens de navigation du site restent identiques dans les trois langues ; seuls leurs libellés changent.
- Ne pas ajouter de lien de langue hors de ce bloc : les contrôles comptent les liens du sélecteur, pas les occurrences brutes de `class='langues'`.
- `_html_page` émet `lang`, `dir`, un canonique propre à la langue, **trois** `<link rel="alternate" hreflang="…">` et un `x-default` vers la version FR.
- Le générateur peut écrire les alternates en guillemets simples et le `x-default` en guillemets doubles : les assertions doivent accepter les deux formes, jamais supposer une seule.

## 5. CSS RTL

Ajouter les surcharges, pas une feuille parallèle :

```css
html[dir="rtl"] body{font-family:'Segoe UI',Tahoma,'Traditional Arabic',Arial,sans-serif}
html[dir="rtl"] header.site nav .langues{margin-left:0;padding-left:0;border-left:0;
     margin-right:14px;padding-right:12px;border-right:1px solid #34506a}
html[dir="rtl"] .formule,html[dir="rtl"] table,html[dir="rtl"] pre,html[dir="rtl"] code{
     direction:ltr;text-align:left}
```

Vérifier dans la page arabe que `dir="rtl"` est présent **et** que la règle LTR des formules existe. Un `dir="rtl"` seul ne suffit pas : sans la seconde règle, les équations et les tableaux s'inversent.

## 6. Figure neutre

- Tracer la figure avec des libellés purement mathématiques (`Re(s)`, `Im(s)`, `Z(t)`, symboles) et une police standard.
- Ne jamais passer de texte arabe à matplotlib : le façonnage des ligatures n'est pas fiable et produirait une figure incohérente.
- Produire le PNG et un SVG en ligne ; remplacer `width`/`height` du SVG par `width="100%" height="auto"`.
- Traduire seulement `fig_legende` et, si présente, l'alternative textuelle.
- Vérifier que le bloc `<svg>` ne contient aucun caractère arabe ; le script le contrôle.

## 7. PDF français

- Construire une page d'impression en français (`_html_impression`), avec couverture, sommaire, avertissement de statut et annexe de reproduction.
- Imprimer avec Chrome headless (`--headless=new`, `--no-pdf-header-footer`, `--print-to-pdf`), puis refuser un fichier qui ne commence pas par `%PDF`.
- Ne pas promettre un PDF trilingue. La page affiche une note (`note_pdf`) qui renvoie au dossier français ; c'est une limite assumée, pas un oubli.

## 8. Générer et contrôler localement

```bash
# cwd : <RACINE> ; régénère les 3 pages, le PNG et le PDF
py -3 oeuvre_universelle/generer_page_riemann.py
```

Puis :

1. Relever taille et SHA-256 des trois pages, du PDF et du PNG.
2. Compter les titres d'équations et les blocs d'équations **séparément** : sur la page Riemann, 8 titres et 9 blocs (`eq` + `eq-cle`), un bloc n'ayant pas de titre. Ne jamais asserter l'égalité entre ces deux compteurs.
3. Écrire les assertions à partir du balisage réel (`grep -o`), pas de l'intention. Un `hreflang` en guillemets simples fait échouer un `assertIn('hreflang="fr"')` alors que le lien existe.
4. Si une assertion échoue, inspecter le HTML avant de « corriger » la page : l'erreur est souvent dans le test.

## 9. Câbler la passerelle, le sitemap et le manifeste

- Passerelle : ajouter les routes canoniques **et** les alias existants de la page (sur Riemann, 9 routes : 3 canoniques, 3 alias `hypothese-riemann`, 3 alias `oeuvre-universelle/riemann`), plus les alias PDF et PNG. Servir en UTF-8.
- Sitemap : une URL par langue, avec la date du jour.
- Manifeste : ajouter les trois pages, le PDF et le PNG aux globs de `GLOBS_SELECTIONNES`, puis régénérer.
- Ordre de régénération : générateur → pages/PDF/PNG → œuvres qui affichent la racine → manifeste → vérification croisée.
- **Piège vérifié :** la suite de tests régénère le manifeste. Si des pages embarquent la racine Merkle, elles gardent l'ancienne valeur (`e6bf222e…`) alors que le manifeste porte la nouvelle (`43b0bf0a…`). Régénérer l'ensemble après le dernier changement et asserter l'égalité page / `resume.json` / manifeste.
- Le JSON d'API peut imbriquer la racine sous `manifeste` : lire `donnees["manifeste"]["racine_merkle_sha256"]` et non la clé de premier niveau, sinon `KeyError`.

## 10. Tests et documentation

- Tests unitaires de la page : `lang`/`dir`, canonique, trois alternates, présence des titres d'équations dans chaque langue, PDF et PNG.
- Tests du site public : trois routes canoniques, alias, titres attendus par langue, sitemap.
- Capacité du moteur Triniter : mentionner `fr/en/ar` si la fiche décrit les langues.
- Documentation des routes : une ligne par route et alias, avec la mention de statut (par exemple « non démontrée » en FR, *unproven* en EN, **غير مُبرهنة** en AR).
- Sur le lot Riemann : 47 tests verts (30 œuvre, 8 site public, 9 spectre Triniter).

```bash
# cwd : <RACINE> ; ÉCRIT resultats/ (manifeste, résumé) via les tests : lancer après avoir figé les empreintes
py -3 -m unittest tests.test_oeuvre_universelle tests.test_site_public_mizan -v
```

Après la suite, revérifier la racine du manifeste et l'égalité avec les pages, car les tests peuvent l'avoir régénéré.

## 11. Déploiement

1. Demander un accord explicite pour **ce** lot : un accord antérieur ne le couvre pas.
2. Charger `deployer-site-sans-dol-vps` et suivre son runbook (sauvegarde vérifiée, liste LF, restauration des modes, égalité SHA-256).
3. Vérifier après déploiement : routes 200 avec le bon `Content-Type`, contenu servi par langue, PDF et PNG binairement identiques, racine du manifeste, sitemap.
4. Lire les journaux avec `sudo -n` sur une fenêtre datée ; un journal vide est inconclusif. Attribuer les 404 avant de conclure à une régression.
5. Rapporter les limites : PDF FR, absence de validation visuelle navigateur si elle n'a pas eu lieu, statut épistémique inchangé.

## 12. Erreurs vérifiées

| Symptôme | Cause | Action |
|---|---|---|
| `FAIL hreflang x3` alors que les liens existent | assertion en guillemets doubles, générateur en guillemets simples | asserter une regex tolérante, ou la forme réellement produite |
| Sélecteur compté à 4 ou 6 | `class='langues'` compté en plus des liens | compter les `<a class='langue…>` du bloc, pas les classes |
| 8 titres mais 9 blocs d'équations | un bloc `eq-cle` sans titre | asserter les titres `= 8` et les blocs `>= 8`, jamais l'égalité |
| Racine Merkle incohérente après tests | les tests régénèrent le manifeste après la génération des pages | tout régénérer dans l'ordre, puis asserter page / résumé / manifeste |
| `KeyError: 'racine_merkle_sha256'` | la racine est sous la clé `manifeste` | lire `donnees["manifeste"]["…"]` |
| `SyntaxError: unterminated string literal` | script Python inline avec apostrophes et guillemets mêlés | écrire le script dans un fichier temporaire, puis l'exécuter |
| Page arabe correcte mais équations inversées | `dir="rtl"` sans règle LTR sur `.formule` | ajouter la règle `direction:ltr` et la vérifier |
| PDF absent ou corrompu | Chrome introuvable ou impression échouée | vérifier le chemin de Chrome et la signature `%PDF` avant de poursuivre |

## 13. Rapport et checklist

Rapport final :

- **Lot** : trois pages, figure, PDF, passerelle, sitemap, manifeste, tests, doc.
- **Parité** : nombre de clés par langue, titres d'équations, alternates, sélecteur.
- **Commandes** : codes retour et sorties clés du script de parité et des tests.
- **Production** : nombre de fichiers, égalité SHA-256, sauvegarde, journaux.
- **Limites** : PDF FR, validation visuelle absente, historique de session non lu.

Checklist :

- [ ] Les clés de `T` sont identiques dans les trois langues.
- [ ] `lang` et `dir` sont corrects page par page.
- [ ] Trois alternates et un x-default vers le FR.
- [ ] Le sélecteur contient exactement trois liens, un seul actif.
- [ ] Le canonique de chaque page pointe son propre chemin.
- [ ] Les formules, tableaux, `pre` et `code` restent LTR en arabe.
- [ ] La figure ne contient aucun texte arabe.
- [ ] Le PDF est français et la page le dit.
- [ ] Les neuf routes et les alias PDF/PNG sont servis en UTF-8.
- [ ] Le sitemap contient les trois URL.
- [ ] Les cinq artefacts sont scellés par le manifeste, sans dérive de racine.
- [ ] Les tests et la documentation des routes sont à jour.
- [ ] Le script de parité a produit `RESULT: PASS` sur les pages réelles et `RESULT: FAIL` sur une copie mutée hors du Skill.
- [ ] Aucune revendication de preuve n'a été ajoutée ou renforcée par la traduction.

## Ressources

- `scripts/verifier_parite_trilingue.py` — contrôle déterministe du générateur (AST) et des trois pages.
- `references/cas-riemann-2026-10-28.md` — cas vérifié : tailles, empreintes, échecs réels, déploiement et limites.
