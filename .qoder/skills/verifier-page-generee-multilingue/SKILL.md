---
name: verifier-page-generee-multilingue
description: "Vérifier une page HTML générée en plusieurs langues en dérivant les assertions du générateur réel plutôt que de l'intention : compter les cartes, accepter hreflang en guillemets simples comme doubles, traiter les apostrophes encodées en &#x27;, détecter les entités doublement encodées, vérifier le RTL, tester le filtre par dispatchEvent, puis exécuter scripts/verifier_page_multilingue.py pour un verdict RESULT: PASS/FAIL reproductible. Utiliser après génération ou régénération d'une page FR/EN/AR, quand un test échoue sur une chaîne visible à l'écran, quand un compteur de cartes ou d'équations ne correspond pas, ou avant de déclarer une page vérifiée. 用于多语言生成页面的结构断言、测试与生成器不一致、hreflang 引号与 &#x27; 转义造成的假失败。"
---

# Vérifier une page générée multilingue

## Objectif

Prouver la structure d'une page HTML générée en plusieurs langues (FR/EN/AR) par des assertions comparant un attendu à un observé, puis par une vérification navigateur. Une assertion se dérive **de la sortie réelle du générateur**, jamais de ce que la page « devrait » produire.

## Frontière avec les autres Skills

| Besoin | Skill à utiliser |
|---|---|
| Échec de capture, `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`, repli structurel, fraîcheur des preuves | `validation-navigateur-par-repli` |
| `py -3`, `UnicodeEncodeError` cp1252, empreintes avant/après, CSV/HTML du projet | `verifier-livrables-csv-html-windows-fr` |
| Assertions multilingues, échappement, cardinalités, filtre de recherche | ce Skill |

Ne pas recopier la chaîne de repli navigateur ici : la charger depuis `validation-navigateur-par-repli`.

## 0. Figer la version avant toute assertion

Relever `SHA-256`, taille et `mtime` des pages, puis les recalculer après la campagne. Si une valeur change, les preuves sont invalides et la vérification recommence. Le script imprime le chemin absolu, le `SHA-256` complet, la taille et le `mtime` de chaque page.

## 1. Dériver l'assertion de la sortie

Avant d'écrire ou de corriger un test, observer ce que le générateur produit réellement :

```bash
grep -o 'hreflang=[^ >]*' PAGE.html | sort | uniq -c
grep -c '<article class="carte"' PAGE.html
grep -o 'class="equation"' PAGE.html | wc -l
grep -o '<html lang="[a-z]*" dir="[a-z]*"' PAGE.html
```

Puis vérifier la source de l'échappement (par exemple `_ech` qui appelle `html.escape(..., quote=True)`) et le type réel des champs du registre. Un `AttributeError` dans un test signale souvent un type supposé, pas une page cassée.

## 2. Invariants par langue

- `lang` de `<html>` égale la langue de la page ; `dir="rtl"` pour l'arabe, `dir="ltr"` sinon.
- Nombre exact de cartes identique dans chaque langue ; le nombre d'équations peut dépasser ce total.
- Chaque page déclare un `hreflang` pour **toutes** les langues du jeu, quelle que soit la forme des guillemets.
- `h1` non vide et propre à la langue.
- Aucune entité doublement encodée (`&amp;#`, `&amp;amp;`).

## 3. Erreurs vérifiées et action

| Symptôme | Cause | Action |
|---|---|---|
| `assertIn('hreflang="fr"', page)` échoue alors que le lien existe | le générateur écrit `hreflang='fr'` (guillemets simples) ; seule la liaison `x-default` est en guillemets doubles | asserter `hreflang='fr'` ou une regex tolérante aux deux formes ; vérifier par `grep` avant d'écrire |
| La chaîne cherchée est visible à l'écran mais absente du test | `html.escape(quote=True)` encode `'` en `&#x27;` | chercher la forme encodée, ou une sous-chaîne sans apostrophe |
| `class="equation"` compte 20 pour 19 cartes | la classe est réutilisée hors carte (bloc de hachage `<pre class="equation">`) | asserter `<article class="carte"` == N et `class="equation"` >= N |
| `AttributeError: 'list' object has no attribute 'strip'` | le champ `variables` du registre est une liste de `{symbole, sens}`, pas une chaîne | asserter une liste non vide, puis les clés de chaque élément |
| Test RTL vert par accident | `assertIn('dir="rtl"', page if ar else 'dir="ltr"')` teste une chaîne littérale pour les langues non arabes | écrire un `if`/`else` explicite avec `page` dans les deux branches |
| Comptes de libellés de statut incohérents | les pages EN/AR conservent des libellés FR (statut brut du registre) | ne pas asserter un nombre de libellés par langue ; asserter la présence, pas la quantité |
| `debordement_horizontal: true` alors que la mise en page est correcte | viewport `0x0` : `scrollWidth > innerWidth` est vrai quel que soit le contenu | lire `window.innerWidth` d'abord ; à 0, déclarer la mesure inexploitable, pas un défaut |
| Sortie unittest de plus de 100 Ko | les messages d'assertion embarquent le source complet de la page | rediriger vers un fichier puis `grep` les lignes `FAIL`/`ERROR`/`AssertionError` |
| `UnicodeEncodeError: 'charmap' codec can't encode character` | console cp1252 et caractères comme `≈` ou `→` | `PYTHONIOENCODING=utf-8` ou sortie ASCII échappée |

## 4. Vérification navigateur

Servir les pages localement, puis n'utiliser que des assertions déterministes :

```bash
py -3 -m http.server 8765 --directory web_cloud
```

Tester le filtre en modifiant la valeur du champ et en déclenchant l'événement, puis compter les cartes non masquées avant de réinitialiser :

```js
() => { const c=[...document.querySelectorAll('.carte')]; const i=document.getElementById('recherche'); i.value='zakat'; i.dispatchEvent(new Event('input',{bubbles:true})); const n=c.filter(x=>!x.hidden).length; document.getElementById('reset').click(); return JSON.stringify({cartes:c.length,visibles:n,lang:document.documentElement.lang,dir:document.documentElement.dir}); }
```

Adapter le mot recherché à la langue (`zakat`, `liquidity`, `الزكاة`). Si `take_screenshot` échoue, suivre `validation-navigateur-par-repli` et marquer la preuve visuelle comme indisponible : ne jamais présenter une validation structurelle comme une validation visuelle.

## 5. Script d'assertion

Depuis le répertoire qui contient `web_cloud/` (ici `ASTRO-Q°ODE_SYSTEME`), remplacer `SKILL_DIR` par le chemin absolu du répertoire de ce Skill :

```bash
py -3 -B "SKILL_DIR/scripts/verifier_page_multilingue.py" \
  --page fr=web_cloud/oeuvre_universelle.html \
  --page en=web_cloud/oeuvre_universelle_en.html \
  --page ar=web_cloud/oeuvre_universelle_ar.html \
  --cartes 19
```

Options : `--dir ar=rtl` pour forcer une direction, `--sans-x-default` pour ne pas exiger `x-default`. Le script vérifie existence, taille, UTF-8, `lang`/`dir`, cartes, équations, `hreflang` de toutes les langues fournies, `x-default`, `h1`, entités doublement encodées. Sortie ASCII uniquement, une ligne `OK`/`FAIL` par contrôle, verdict `RESULT: PASS` ou `RESULT: FAIL`. Codes retour : 0 pour PASS, 1 pour FAIL, 2 pour erreur d'usage (argument `LANGUE=CHEMIN` mal formé, langue ou chemin vide, langue dupliquée).

Après toute modification du script, prouver qu'il n'est pas vacant : sur une copie hors du Skill, retirer un marqueur de carte ou une langue `hreflang`, puis exiger `RESULT: FAIL` et un code retour 1.

## 6. Rapport

- **Version** : chemins absolus, `SHA-256`, taille et `mtime` des pages.
- **Structure** : un tableau attendu / observé par contrôle et par langue, avec le code retour du script.
- **Navigateur** : assertions DOM avec valeurs, et statut visuel explicite.
- **Limites** : ce qui n'a pas été vérifié. Un `RESULT: PASS` ne prouve ni l'exactitude du contenu, ni la véracité des statuts affichés (OPÉRATIONNEL / SIMULÉ / SPÉCIFIÉ), ni le déploiement. Ne jamais transformer un PASS structurel en revendication de contenu.

## Ressources

- `scripts/verifier_page_multilingue.py` — vérificateur CLI déterministe, sans dépendance hors bibliothèque standard.
- `references/cas-verifie-page-oeuvre.md` — cas réel : échecs observés, corrections, preuves navigateur et limites.

## Checklist finale

- [ ] Les pages ont été régénérées dans la session courante et leurs empreintes relevées avant et après.
- [ ] Chaque assertion découle d'un `grep` ou d'une lecture du générateur, pas d'une supposition.
- [ ] Le nombre de cartes est asserté exactement ; le nombre d'équations au minimum.
- [ ] `hreflang` est vérifié pour toutes les langues, formes de guillemets acceptées.
- [ ] Les chaînes contenant une apostrophe sont cherchées sous forme encodée.
- [ ] `dir` est asserté par branche explicite, jamais par `assertIn` conditionnel.
- [ ] Le script a produit `RESULT: PASS` sur les pages réelles et `RESULT: FAIL` sur une fixture mutée.
- [ ] Le rapport sépare structure, navigateur et limites ; aucune revendication visuelle sans capture.
