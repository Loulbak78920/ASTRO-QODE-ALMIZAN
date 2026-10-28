---
name: prototyper-variante-layout-sur-copie
description: "Produire une variante de mise en page d'une page HTML autonome sans toucher l'original : identifier la source réellement servie, figer size/mtime/SHA-256, copier en <BASE>.PROTO_<spec>.html, n'éditer que le CSS de structure en exprimant la répartition par calc((100% - gap) * ratio) pour que le ratio reste exact malgré la gouttière, ajouter min-width: 0, le point de rupture et un wrapper overflow-x pour les tableaux larges, puis prouver par script et par mesures navigateur que texte, adresses et script inline sont identiques et que l'original n'a pas bougé. Utiliser pour tester une grille 62/38 ou toute répartition asymétrique sur une page existante, quand un tableau déborde d'une colonne étroite, quand un panneau latéral ne tient pas en position collante, ou avant d'appliquer un layout à la source servie. 用于在副本上试做 HTML 布局变体，并证明原文件未被修改。"
---

# Prototyper une variante de layout sur copie

## Objectif

Livrer une copie `PROTO_` d'une page HTML autonome avec une nouvelle structure de grille, sans modifier l'original, et prouver cette absence de régression par une empreinte `stat` et une comparaison de contenu.

## Quand l'utiliser

- Tester un ratio de colonnes (62/38, 70/30…) sur une page existante avant de toucher la vraie source.
- Une colonne devient étroite et un tableau ou une adresse longue déborde.
- Un panneau latéral doit rester visible au défilement.
- Un intervenant propose un CSS « prêt à intégrer » dont on veut mesurer l'effet réel.

## Quand ne pas l'utiliser

- Modifier le texte, les liens ou le comportement d'une page : ce n'est plus une variante de layout, faire valider chaque écart séparément.
- Déployer : ce Skill produit une copie locale, rien d'autre.
- Page dont le CSS vit dans un fichier externe : la copie n'est plus autonome, mesurer avec la feuille réelle et documenter l'écart.

## Étape 0 — Identifier la page réellement servie

Avant toute copie, vérifier quel fichier une route sert réellement. La copie à la racine d'un workspace n'est pas forcément la source déployée : elle peut précéder un audit de contenu (cas vérifié : racine 24 756 o sans bandeau de transparence, source servie 28 440 o avec l'audit).

- Si une passerelle sert la page, partir de la source servie, pas du doublon racine.
- Si plusieurs copies diffèrent, comparer leurs blocs CSS séparément du contenu : un layout peut s'appliquer à une version dont le texte a déjà été validé.

## Étape 1 — Figer l'empreinte de l'original

Enregistrer `size`, `mtime_ns` et `sha256` **avant** la moindre écriture. Une empreinte prise après coup ne prouve rien.

Remplacer `<skill-dir>` par le dossier d'installation de ce Skill, `<original>` par le chemin absolu de la page source, `<baseline.json>` par un fichier JSON sous `.qoder/tmp` :

```bash
py -3 "<skill-dir>/scripts/verifier_prototype.py" \
  --original "<original>" \
  --record-baseline "<baseline.json>"
```

Le script n'écrit que le JSON demandé ; il ne touche pas la page.

## Étape 2 — Copier sous un nom explicite

Copier dans le même dossier sous `<BASE>.PROTO_<spec>.html`, où `<spec>` décrit le layout (`62-38`, `70-30-col-droite`). Ne jamais éditer l'original.

Le nom `PROTO_` rend le statut évident et évite qu'une copie de travail soit prise pour la source servie. Supprimer la copie quand elle n'est plus utile, ou la laisser à l'utilisateur.

## Étape 3 — N'éditer que la structure

| Autorisé | Interdit |
|---|---|
| Règles de grille, gouttière, `padding`, `max-width` dans `<style>` | Tout nœud de texte |
| Nouvelles classes structurelles (`page-head`, `primary-pane`, `secondary-pane`) | Adresses `0x…`, liens, libellés de bouton |
| Wrappers autour de blocs déplacés, `<main>` / `<aside>` | Script inline, `id` référencés par le JS, attributs `onclick` |
| `overflow-x`, point de rupture, `position: sticky` | Ordre des adresses, contenu des tableaux |

Déplacer des blocs existants d'un conteneur à un autre est structurel ; réécrire leur contenu ne l'est pas. Si un libellé doit raccourcir pour tenir dans une colonne étroite, le proposer à l'utilisateur au lieu de l'appliquer en silence.

### Grille avec gouttière

La formule naïve `calc(100% * r)` + `calc(100% * (1 - r))` **plus** un `gap` déborde exactement de la gouttière (mesuré : 24 px de débordement). Soustraire le `gap` avant d'appliquer le ratio :

```css
:root {
  --ratio: 0.62;
  --gap: 24px;
}
body {
  margin: 0 auto;
  padding: var(--gap);
  max-width: 1400px;
  box-sizing: border-box;
  display: grid;
  grid-template-columns:
    calc((100% - var(--gap)) * var(--ratio))
    calc((100% - var(--gap)) * (1 - var(--ratio)));
  gap: var(--gap);
  align-items: start;
}
.page-head {
  grid-column: 1 / -1;
}
.primary-pane {
  min-width: 0;
}
.secondary-pane {
  min-width: 0;
  position: sticky;
  top: var(--gap);
}
.table-scroll {
  overflow-x: auto;
}
@media (max-width: 1024px) {
  body {
    grid-template-columns: 1fr;
  }
  .secondary-pane {
    position: static;
  }
}
```

- `min-width: 0` sur chaque zone : sans lui, un contenu large (adresse, mot long) élargit la piste de grille et annule le ratio.
- `<body>` en grille : l'en-tête reste pleine largeur avec `grid-column: 1 / -1`.
- `position: sticky` ne fonctionne que si l'ancêtre défile et si le panneau est plus court que la fenêtre ; sinon il paraît inactif sans être cassé.
- Un tableau de contrats (adresses de 42 caractères) déborde à 62 % de largeur : l'envelopper dans `<div class="table-scroll">` plutôt que réduire la police.

Squelette du corps :

```text
<body>
  <div class="page-head">…en-tête, nav, bandeaux pleine largeur…</div>
  <main class="primary-pane">…cartes, tableaux, contenu…</main>
  <aside class="secondary-pane">…indicateurs, action…</aside>
</body>
```

## Étape 4 — Vérifier par script

Remplacer `<prototype>` par le chemin de la copie :

```bash
py -3 "<skill-dir>/scripts/verifier_prototype.py" \
  --original "<original>" \
  --prototype "<prototype>" \
  --baseline "<baseline.json>"
```

Contrôles : original inchangé (`size`, `mtime_ns`, `sha256`), prototype réellement différent, blocs `<script>` identiques octet pour octet, multiset des adresses `0x…{40}` **hors `<style>` et `<script>`** (le script est déjà comparé au caractère près ; un calldata plus long n'est pas compté comme adresse), multiset des nœuds de texte (un bloc déplacé ne déclenche pas de faux positif), équilibre des balises. Codes : 0 = PASS, 1 = FAIL, 2 = usage ou entrée illisible.

Un FAIL se corrige dans le CSS ou les wrappers, jamais en modifiant l'original ni en assouplissant la vérification.

## Étape 5 — Mesurer au navigateur

- Le navigateur embarqué peut n'offrir que ~543 px de large : il applique le point de rupture et ne montre jamais le layout desktop. Mesurer dans des iframes de largeur réelle (1280, 1440, 1920).
- Vérifier à chaque largeur : largeur des deux colonnes, ratio = col1 / (col1 + col2), débordement horizontal de la page (`scrollWidth - clientWidth`), nombre d'éléments dont le texte est tronqué, erreurs console.
- Pour le collage, prendre une fenêtre de hauteur réaliste (~900 px) et relever `scrollY`, le haut et le bas du panneau après défilement. Une iframe plus haute que la page ne défile pas assez : `sticky` paraît alors inactif alors qu'il fonctionne.
- Une page publique peut interdire l'encadrement (`X-Frame-Options: SAMEORIGIN`, `frame-ancestors 'self'`). Comparer par SHA-256 les octets servis et la copie locale, puis rendre la copie locale : sans ressource externe, le rendu est fidèle.
- Si capture ou script de page sont indisponibles, appliquer `validation-navigateur-par-repli`.

## Étape 6 — Rapporter

Joindre la preuve d'intégrité et les mesures, pas seulement une capture.

| Contrôle | Résultat attendu |
|---|---|
| Colonnes | `<largeur1> / <largeur2>` px, ratio calculé |
| Gouttière | valeur du `gap`, sans arrondi |
| Débordement horizontal | 0 px |
| Texte tronqué | 0 élément |
| Panneau collant | ancrage `top` constaté, hauteur du panneau vs fenêtre |
| Console | aucune erreur |
| Original | `size`, `mtime`, `sha256` identiques à l'empreinte d'étape 1 |

Indiquer ce qui reste hors périmètre : rien n'est déployé, la copie `PROTO_` est locale, et toute retouche de texte attend une validation.

## Cas vérifié (2026-10-28)

Page `hub_ponts_synchrones.html` :

- Prototype `PROTO_62-38` produit depuis la copie racine (24 756 o, mtime `2026-10-23 15:07:57`), laissée intacte après écriture de la copie.
- Même layout ensuite appliqué à la source réellement servie (29 409 o, sha256 `a63d6885…`), distincte de la copie racine par son audit de contenu ; texte audité conservé (131 lignes, même multiset), script et adresses identiques.
- Ratio 0,6200 à 1280, 1440 et 1920 px (823,36 / 504,63 px à 1440), gouttière 24 px, corps plafonné à 1 400 px.
- Tableau de passerelle contenu (781 px requis pour 781 disponibles) grâce à `.table-scroll`.
- Panneau collant ancré à `top: 24px` dès 350 px de défilement sur une fenêtre de 900 px ; un premier essai dans une iframe de 1 200 px avait rendu `stickyHeld: false` par manque de défilement.
- Rejeu de `scripts/verifier_prototype.py` sur les octets servis (copie plus une règle CSS) : PASS, 1 bloc script identique, 29 adresses hors script, 124 nœuds de texte.
- Le code fourni au départ ciblait `styles.css`, `--mizan-ratio` et `--mizan` : aucun n'existait, et sa grille en pourcentages cumulait 100 % + gouttière.

## Ressources

- `scripts/verifier_prototype.py` — empreinte de l'original et comparaison original ↔ prototype (scripts, adresses, texte, balises).
