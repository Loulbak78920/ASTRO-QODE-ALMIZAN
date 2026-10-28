# Modèles de harnais

Remplacer les sélecteurs, chemins et largeurs par ceux de la page courante. Tous les scripts supposent un document encadré de même origine que le harnais.

## 1. Harnais de mesure

Fichier sous `.qoder/tmp/`, servi par la même racine que la page.

```html
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Harnais de mesure</title>
<style>
  body { margin: 0; background: #333; font-family: monospace; color: #eee; }
  iframe { display: block; border: 0; background: #fff; margin: 0 0 8px; }
  #w1920 { width: 1920px; height: 900px; }
  #w1440 { width: 1440px; height: 900px; }
  #w1280 { width: 1280px; height: 900px; }
  #w1000 { width: 1000px; height: 900px; }
</style>
</head>
<body>
  <iframe id="w1920" src="/CHEMIN/VERS/PAGE.html"></iframe>
  <iframe id="w1440" src="/CHEMIN/VERS/PAGE.html"></iframe>
  <iframe id="w1280" src="/CHEMIN/VERS/PAGE.html"></iframe>
  <iframe id="w1000" src="/CHEMIN/VERS/PAGE.html"></iframe>
</body>
</html>
```

Les iframes dépassent la fenêtre hôte : c'est voulu, la mesure se fait dans leur `contentDocument`.

## 2. Script de mesure

```js
() => {
  const measure = (id) => {
    const f = document.getElementById(id);
    const d = f && f.contentDocument;
    const w = f && f.contentWindow;
    if (!d) return { id: id, error: 'contentDocument inaccessible (origine differente ?)' };
    const q = (s) => d.querySelector(s);
    const p = q('.primary-pane');
    const s = q('.secondary-pane');
    const t = q('.table-scroll');
    const tb = q('.table-usd');
    const pr = p && p.getBoundingClientRect();
    const sr = s && s.getBoundingClientRect();
    const cards = Array.from(d.querySelectorAll('.card'));
    const rows = {};
    cards.forEach((c) => {
      const top = Math.round(c.getBoundingClientRect().top);
      rows[top] = (rows[top] || 0) + 1;
    });
    const clipped = Array.from(d.querySelectorAll('.primary-pane *, .secondary-pane *'))
      .filter((e) => {
        const cs = getComputedStyle(e);
        const scrolls = e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1;
        return scrolls && cs.overflowX === 'visible' && cs.overflowY === 'visible';
      })
      .slice(0, 10)
      .map((e) => e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0]);
    return {
      id: id,
      viewport: w.innerWidth,
      mediaMobile: w.matchMedia('(max-width: 1024px)').matches,
      grid: getComputedStyle(d.body).gridTemplateColumns,
      bodyW: d.body.clientWidth,
      ratio: pr && sr ? +(pr.width / (pr.width + sr.width)).toFixed(4) : null,
      gap: pr && sr ? Math.round(sr.left - pr.right) : null,
      asidePosition: s ? getComputedStyle(s).position : null,
      overflowX: d.documentElement.scrollWidth - d.documentElement.clientWidth,
      table: t && tb ? { box: t.clientWidth, content: tb.scrollWidth, fits: tb.scrollWidth <= t.clientWidth } : null,
      cards: cards.length,
      cardsPerRow: cards.length ? Math.max(...Object.keys(rows).map((k) => rows[k])) : 0,
      clipped: clipped
    };
  };
  return { w1920: measure('w1920'), w1440: measure('w1440'), w1280: measure('w1280'), w1000: measure('w1000') };
}
```

`clipped` est une heuristique : seuls les éléments réellement visibles et sans `overflow` caché sont retenus. Un `text-overflow: ellipsis` voulu n'apparaît pas, un bloc coupé par un parent `overflow: hidden` non plus. Les ancêtres d'un élément qui déborde apparaissent en cascade : remonter au premier élément fautif au lieu de compter chaque ligne.

## 3. Sonde sticky

À exécuter après la mesure. L'iframe est ramenée à 900 px ; `maxScroll` conditionne l'interprétation. Le verdict est calculé dans la sonde à partir de `budget` et des `bottom` mesurés.

```js
() => {
  const f = document.getElementById('w1440');
  f.style.height = '900px';
  const w = f.contentWindow;
  const d = f.contentDocument;
  const s = d.querySelector('.secondary-pane');
  const topCss = parseFloat(w.getComputedStyle(s).top) || 0;
  const maxScroll = d.documentElement.scrollHeight - w.innerHeight;
  const out = {
    viewportH: w.innerHeight,
    docH: d.documentElement.scrollHeight,
    asideH: s.clientHeight,
    asideScrollH: s.scrollHeight,
    maxScroll: maxScroll,
    topCss: topCss,
    budget: s.clientHeight + 2 * topCss,
    samples: []
  };
  [0, 200, 300, 350, 450, maxScroll].forEach(function (y) {
    w.scrollTo(0, y);
    const b = s.getBoundingClientRect();
    out.samples.push({ asked: y, actual: Math.round(w.scrollY), top: Math.round(b.top), bottom: Math.round(b.bottom) });
  });
  w.scrollTo(0, 350);
  s.scrollTop = 0;
  const first = s.firstElementChild.getBoundingClientRect();
  s.scrollTop = s.scrollHeight;
  const last = s.lastElementChild.getBoundingClientRect();
  const sb = s.getBoundingClientRect();
  out.internal = {
    firstTopAt0: Math.round(first.top),
    lastBottomAtEnd: Math.round(last.bottom),
    asideBottom: Math.round(sb.bottom),
    lastFullyVisible: last.bottom <= sb.bottom + 1,
    reachedScrollTop: Math.round(s.scrollTop)
  };
  s.scrollTop = 0;
  w.scrollTo(0, 0);
  const plateau = out.samples.filter(function (x) { return Math.abs(x.top - topCss) <= 1; });
  const end = out.samples[out.samples.length - 1];
  const bottomCut = plateau.some(function (x) { return x.bottom > out.viewportH; });
  out.plateauSamples = plateau.length;
  out.verdict = plateau.length < 2
    ? 'NON_CONCLUANT'
    : (out.budget > out.viewportH || bottomCut || end.top < topCss - 1 ? 'STICKY_OVERFLOW' : 'STICKY_OK');
  return out;
}
```

Lecture : `actual` peut être inférieur à `asked` (défilement borné). Un plateau de `top` ne suffit pas : un panneau de hauteur `asideH` ancré à `topCss` n'est entièrement visible que si `budget = asideH + 2 × topCss ≤ viewportH`, et `bottom` doit rester ≤ `viewportH` sur le plateau.

- `STICKY_OVERFLOW` : `budget > viewportH`, un `bottom > viewportH` sur le plateau, ou `top < topCss` à `maxScroll` (bas de colonne atteint, panneau poussé vers le haut). Le `bottom` mesuré dit si le contenu est réellement sous le pli ou si seule la marge basse manque.
- `STICKY_OK` : plateau d'au moins deux échantillons, budget respecté, `top = topCss` et `bottom ≤ viewportH` jusqu'à `maxScroll`.
- `NON_CONCLUANT` : moins de deux échantillons au plateau avant `maxScroll` ; l'iframe est trop haute pour la page, ce n'est pas un défaut CSS.

`internal` ne concerne qu'un panneau plafonné (`max-height` + `overflow-y: auto`) : après `s.scrollTop = s.scrollHeight`, `reachedScrollTop` doit approcher la course réelle `asideScrollH - asideH` et `lastFullyVisible` doit être vrai. Un `lastFullyVisible` faux, ou `reachedScrollTop` nul alors que le panneau déborde, signifie que le plafond masque la fin du contenu.

### Vérifier que `asideH` vient du contenu

À exécuter avant d'appliquer le budget. Même largeur, trois hauteurs d'iframe ; l'iframe revient à 900 px en sortie.

```js
() => {
  const f = document.getElementById('w1440');
  const out = {};
  [700, 900, 1100].forEach((h) => {
    f.style.height = h + 'px';
    const w = f.contentWindow;
    const s = w.document.querySelector('.secondary-pane');
    out['h' + h] = {
      viewportH: w.innerHeight,
      asideH: Math.round(s.getBoundingClientRect().height),
      asideScrollH: s.scrollHeight,
      childH: Array.from(s.children).map((c) => Math.round(c.getBoundingClientRect().height))
    };
  });
  f.style.height = '900px';
  return out;
}
```

Lecture : `asideH` constant avec des `childH` qui le recomposent (mesuré `900 = 408 + 20 + 472`) = hauteur de contenu. `asideH` qui suit `viewportH` = plafond de fenêtre (`max-height`, `100vh`) : le budget `asideH + 2 × topCss` dépassera `innerHeight` sans que ce soit un défaut, et `STICKY_OVERFLOW` ne se déduit plus de ce seul critère. Une égalité `asideH == viewportH` sur une seule hauteur ne tranche pas.

## 4. En-tête et chevauchement

```js
() => {
  const d = document.getElementById('w1440').contentDocument;
  const box = (e) => {
    const b = e.getBoundingClientRect();
    return { x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height) };
  };
  const head = d.querySelector('.page-head');
  const title = d.querySelector('.page-head h1');
  const action = d.querySelector('.page-head a, .page-head button');
  const p = box(d.querySelector('.primary-pane'));
  const s = box(d.querySelector('.secondary-pane'));
  const T = title ? box(title) : null;
  const A = action ? box(action) : null;
  const fs = title ? parseFloat(getComputedStyle(title).fontSize) : null;
  const overlap = T && A ? !(T.x + T.w <= A.x || A.x + A.w <= T.x || T.y + T.h <= A.y || A.y + A.h <= T.y) : null;
  return {
    head: head ? box(head) : null,
    title: T,
    action: A,
    titleFontSize: fs,
    titleSingleLine: T && fs ? T.h <= fs * 1.5 : null,
    headSpansColumns: head ? box(head).w >= (s.x + s.w - p.x) - 1 : null,
    overlap: overlap
  };
}
```

## 5. Harnais de capture

```html
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Harnais de capture</title>
<style>
  body { margin: 0; background: #333; font-family: monospace; color: #eee; }
  .scaler { width: 518px; height: 450px; overflow: hidden; margin: 4px; }
  .scaler iframe { width: 1440px; height: 1250px; border: 0; background: #fff; transform: scale(0.36); transform-origin: top left; }
  .phone { margin: 4px; }
  .phone iframe { width: 390px; height: 844px; border: 0; }
</style>
</head>
<body>
  <div class="scaler"><iframe id="w1440" src="/CHEMIN/VERS/PAGE.html"></iframe></div>
  <div class="phone"><iframe id="w390" src="/CHEMIN/VERS/PAGE.html"></iframe></div>
</body>
</html>
```

Calcul : `wrapper = iframe × échelle` (1440 × 0.36 = 518,4 ; 1250 × 0.36 = 450). Fixer la hauteur de l'iframe à `scrollHeight` mesuré avant la capture, puis recalculer la hauteur du wrapper.

## 6. Commandes

```bash
netstat -ano | grep ":PORT" | head -3
cd RACINE && py -3 -m http.server PORT --bind 127.0.0.1
curl -sI URL | grep -iE "x-frame-options|content-security-policy"
curl -s URL | sha256sum
sha256sum FICHIER
```

`TaskStop` sur l'identifiant retourné au lancement arrête le serveur. S'il échoue (`exit 255`, « Accès refusé » sur un processus enfant), prouver l'arrêt par l'absence de ligne `LISTENING` ; les sockets `TIME_WAIT` ne comptent pas.

```bash
netstat -ano | grep ":PORT" | grep LISTENING   # vide = serveur arrêté
taskkill //F //PID N                           # seulement si une ligne LISTENING subsiste
```

Nettoyage : `rm -f .qoder/tmp/HARNAIS.html .qoder/tmp/CAPTURE.png`.

## 7. Repli CDP — largeurs CSS exactes

`--window-size` ne garantit pas la largeur rendue : sous Chrome headless, 375 px demandés rendent `innerWidth=500` et 1024 px rendent 1008, alors que le PNG garde la taille demandée. Le script du Skill fixe la largeur par CDP.

```bash
node SCRIPTS/capturer_cdp.mjs DOSSIER_SORTIE URL 1920 1440 1024 1000 768 375
CAPTURE_PREFIX=ponts node SCRIPTS/capturer_cdp.mjs DOSSIER_SORTIE URL 375   # ponts-375.png
CHROME_PATH=/chemin/chrome node SCRIPTS/capturer_cdp.mjs …                    # binaire non standard
```

Prérequis : Node ≥ 22 (`WebSocket` et `fetch` globaux), un Chrome installé au chemin par défaut ou dans `CHROME_PATH`. Le script crée son propre profil (`DOSSIER_SORTIE/prof-cdp`) et le supprime en fin d'exécution.

Sortie réelle du 2026-10-28 (page `d317f0ec…`, 29 598 o), deux largeurs rejouées :

```text
{"width":1024,"innerWidth":1024,"innerHeight":900,"scrollHeight":2220,"scrollWidth":1009,"mobile":false,"file":"…\\ponts-1024.png","bytes":341209}
{"width":375,"innerWidth":375,"innerHeight":900,"scrollHeight":3741,"scrollWidth":375,"mobile":true,"file":"…\\ponts-375.png","bytes":314467}
DONE
```

Contrat : `innerWidth` égale la largeur demandée, sinon `WIDTH_MISMATCH` (code 3) et aucune capture pour cette largeur ; `clip.height = scrollHeight` ; `innerHeight` est la hauteur de sonde (900) ; `mobile` est vrai à ≤ 500 px, avec barre de défilement en surimpression (`scrollWidth = largeur`), contre une gouttière de 15 px en desktop (`scrollWidth = largeur − 15`, comme dans une iframe). Codes de retour : 0 succès, 2 Chrome ou port DevTools indisponible, 3 `WIDTH_MISMATCH`, 4 échec CDP, 64 arguments invalides.
