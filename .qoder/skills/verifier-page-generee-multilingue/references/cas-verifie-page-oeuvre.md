# Cas vérifié : pages FR/EN/AR de l'œuvre universelle

Source : session `de5bacf6-50d0-42ce-b890-f3149acbbd91`, lue le 2026-10-28 à la révision 167 (JSONL `de5bacf6-….jsonl`, lignes ~1880–2390). Les constats de structure ont été re-vérifiés sur disque le même jour dans `ASTRO-Q°ODE_SYSTEME`.

Contexte : génération d'un registre de 19 problèmes répartis en 6 strates, puis de trois pages (`web_cloud/oeuvre_universelle.html`, `_en.html`, `_ar.html`) par `oeuvre_universelle/generer_page_oeuvre.py`.

## Faits vérifiés sur disque (2026-10-28)

| Fait | Valeur observée |
|---|---|
| `<article class="carte"` par page | 19 (fr, en, ar) |
| `class="equation"` par page | 20 (fr, en, ar) — la 20e est un bloc de hachage hors carte, `<pre class="equation">` |
| `hreflang` | `'ar'`, `'en'`, `'fr'` en guillemets simples, 2 occurrences chacun ; `x-default` en guillemets doubles, 1 occurrence ; 1 par page |
| `<html lang dir>` | fr/ltr, en/ltr, ar/rtl |
| Échappement | `_ech(v) = html.escape(str(v), quote=True)` (générateur, lignes 243–244) donc `'` → `&#x27;` |
| Champ `variables` du registre | liste de dictionnaires `{symbole, sens}` pour les 19 entrées |
| `<h1>` par page | 1, texte propre à la langue |

Lignes du générateur concernées : 480 et 696 (`hreflang='{code}'`), 732 (`hreflang="x-default"`).

## Échecs observés et corrections

| Test | Sortie observée | Cause | Correction retenue |
|---|---|---|---|
| `test_codes_uniques_et_structure` | `ERROR` sur `self.assertTrue(entree["variables"].strip(), entree["code"])` | `variables` est une liste | `assertTrue(entree["variables"])` puis boucle sur `symbole`/`sens` |
| `test_liens_api_et_langues` | `FAIL` sur `self.assertIn(f'hreflang="{autre}"', page)` | le générateur écrit des guillemets simples | `self.assertIn(f"hreflang='{autre}'", page)` |
| `test_dix_neuf_cartes_par_langue` | 20 occurrences de `class="equation"` pour 19 cartes | classe réutilisée hors carte | `assertEqual(page.count('<article class="carte"'), 19)` et `assertGreaterEqual(page.count('class="equation"'), 19)` |
| `test_statuts_et_limites_publies` | `"preuve antérieure"` et `"non instrumentée"` introuvables | formulations et périmètre différents de l'intention | assertions remplacées par `"source non déployée"`, `"preuve d&#x27;intégrité"`, `"OpenTimestamps"` |
| `test_aucune_promesse_absolue` | `"aucun système n'est infaillible"` absent du texte comparé | apostrophe encodée `&#x27;` dans le HTML | chercher `n&#x27;est infaillible` (FR) et `no system is infallible` (EN) |
| Assertion `dir` | branche non arabe comparant `'dir="rtl"'` à la chaîne `'dir="ltr"'` | `assertIn(a, b)` conditionnel mal formé | `if langue == "ar": … else: …`, confirmé dans le test final |

Sortie d'échec volumineuse : le rapport unittest atteignait 113,6 Ko parce que les messages d'assertion embarquent le source de la page ; l'isolement des deux tests en échec a été fait par redirection vers un fichier puis `grep` des lignes `FAIL`, `ERROR`, `Traceback`, `AssertionError`.

## Vérification navigateur

Serveur local : `py -3 -m http.server 8765 --directory web_cloud`. Navigation réussie sur les trois pages.

`take_screenshot` a échoué avec :

```
NATIVE_BROWSER_VIEWPORT_UNAVAILABLE: In-app Browser did not provide a visible surface with a positive viewport within 1000ms (operation=screenshot, viewport=0x0, visible=false, attached=false, cdpAttached=true, visibilityState=hidden).
```

Repli `evaluate_script` (paramètre `function` obligatoire) :

| Page | `cartes` | `lang` / `dir` | Recherche | `h1` |
|---|---|---|---|---|
| fr | 19 | fr / ltr | `zakat` → 1 visible | `L'Œuvre universelle` |
| en | 19 | en / ltr | `liquidity` → 2 visibles | `The Universal Work` |
| ar | 19 | ar / rtl | `الزكاة` → 1 visible | `العمل الكوني` |

Le premier relevé indiquait `debordement_horizontal: true`. La mesure a été écartée : `window.innerWidth` valait 0 (viewport masqué), donc `scrollWidth > innerWidth` était vrai indépendamment du contenu. Aucun élément débordant n'a été identifié.

## Ce qui n'a pas été vérifié

- **Aucune preuve visuelle** : aucune capture n'a réussi. La validation est structurelle uniquement ; le rendu CSS n'a pas été vu.
- Le `RESULT: PASS` structurel ne dit rien de l'exactitude des 19 résultats, de la véracité des statuts affichés, ni de l'état de production.
- Les pages du projet peuvent être régénérées : aucune empreinte n'est figée dans ce document, seulement des cardinalités et des formes d'échappement re-mesurées à la date indiquée.
