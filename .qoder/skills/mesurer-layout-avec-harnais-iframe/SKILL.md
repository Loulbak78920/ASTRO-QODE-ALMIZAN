---
name: mesurer-layout-avec-harnais-iframe
description: "Mesurer un layout desktop quand le navigateur in-app n'offre qu'un viewport étroit : mesurer innerWidth, servir la racine du projet en HTTP local sur 127.0.0.1 pour que harnais et page partagent la même origine, charger la page dans des iframes de largeur fixe (1920, 1440, 1280, 1000) pour forcer les media queries desktop, mesurer via contentDocument (viewport, matchMedia, gridTemplate, ratio, gouttière, débordement, tableau, cartes, texte tronqué), distinguer un bug CSS d'un point de rupture, vérifier sticky en défilant contentWindow sur une hauteur réaliste et en relisant top et bottom (STICKY_OVERFLOW si asideH + 2 × topCss > innerHeight), capturer avec transform scale dans un wrapper clippé, puis arrêter le serveur et supprimer le harnais. Utiliser quand une mesure directe renvoie une seule colonne, un ratio 0.5 ou un aside static, quand une capture 1440 px est tronquée par le viewport in-app, ou avant de conclure qu'un layout desktop est cassé. 用于窄视口强制桌面断点、iframe 定宽测量、sticky 复核、缩放截图与临时服务器清理。"
---

# Mesurer un layout desktop avec un harnais d'iframes

## Quand l'utiliser

- Une mesure directe dans le navigateur in-app renvoie une seule colonne, `ratio=0.5` ou `asidePosition=static`, alors que le layout desktop est attendu.
- Il faut juger un rendu à 1280, 1440 ou 1920 px sans pouvoir élargir la fenêtre hôte.
- Une capture paraît tronquée à droite ou en bas, et il faut distinguer un défaut de layout d'un artefact de capture.
- `position: sticky` semble inactif et il faut savoir si le CSS est en cause ou si la fenêtre testée ne défile pas assez.

## Hors périmètre

- Écrire ou modifier le layout, choisir un ratio de colonnes, vérifier que le texte et le script n'ont pas bougé : utiliser `prototyper-variante-layout-sur-copie`.
- Capture indisponible (`NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`), forme exacte de `evaluate_script`, fraîcheur des preuves : utiliser `validation-navigateur-par-repli`.
- Déploiement, routage, en-têtes de production.

## Principe

1. Une iframe crée son propre viewport : les media queries de la page encadrée répondent à sa largeur CSS, pas à celle de la fenêtre hôte. C'est le levier.
2. `contentDocument` n'est lisible qu'entre documents de même origine : même schéma, même hôte, même port. `file://` vers `http://` est cross-origin (mesuré : `SecurityError`), et deux ports sont deux origines. L'accès `file://` vers `file://` dépend des options du navigateur (observé accessible dans le navigateur in-app) : ne pas en dépendre, servir les deux documents par le même `http.server`.
3. Une capture du hôte est clippée à la largeur du hôte. Il faut réduire visuellement l'iframe (`transform: scale`), jamais rétrécir sa largeur CSS, sinon les media queries changent.

## Procédure

### 1. Mesurer la largeur réelle avant tout

```js
() => ({ innerWidth: innerWidth, outerWidth: outerWidth, dpr: devicePixelRatio })
```

Si `innerWidth` atteint déjà la largeur cible, mesurer directement : le harnais n'apporte rien. Sinon, le noter (cas vérifiés : 543 px, et 0 quand la surface in-app est masquée) et continuer. Un `innerWidth` de 0 n'est pas une largeur nulle : c'est une surface indisponible, à traiter comme un viewport étroit et à signaler dans les limites.

### 2. Servir harnais et page depuis une origine unique

- Choisir un port libre (`netstat -ano | grep ":PORT"`), puis lancer en arrière-plan depuis la racine qui contient la page et `.qoder/tmp` : `py -3 -m http.server PORT --bind 127.0.0.1`.
- Écrire le harnais sous `.qoder/tmp/`, avec un `src` relatif à cette racine. Le harnais et l'iframe doivent être servis par le même processus. Ne pas compter sur un accès `file://` vers `file://`, même si le profil courant l'autorise : il n'est pas portable.
- Si la page vient d'une route de passerelle : vérifier `curl -sI URL` pour `X-Frame-Options` et `frame-ancestors`, et ne pas oublier que la route est sur un autre port que le harnais. Si l'encadrement est refusé ou l'origine différente, servir le fichier statique depuis la racine du harnais et prouver que les octets sont identiques (`curl -s URL | sha256sum` contre `sha256sum FICHIER`). Ne jamais mélanger deux origines en espérant lire le DOM.
- Le message « Successfully navigated » prouve seulement le chargement, pas le rendu.

### 3. Écrire le harnais de mesure

Utiliser le modèle de `references/modeles-harnais.md`. Quatre iframes suffisent : 1920, 1440 et 1280 pour les largeurs desktop, 1000 comme sonde de point de rupture. Hauteur 900 px, sans `transform` à ce stade.

### 4. Mesurer dans chaque iframe

Exécuter le script de mesure du modèle. Il lit `contentDocument`, et renvoie pour chaque largeur : `viewport`, `mediaMobile`, `grid`, `ratio`, `gap`, `asidePosition`, `overflowX`, `table`, `cards`, `cardsPerRow`, `clipped`. Un `error` explicite vaut mieux qu'un objet vide : il signale une origine différente ou un sélecteur absent.

### 5. Décider : bug CSS ou point de rupture

- Si `mediaMobile` est vrai, la largeur testée est sous le point de rupture : une seule colonne et un `gap` négatif sont attendus, pas un bug.
- Juger le layout desktop sur une largeur où `mediaMobile` est faux (1440). Si la grille y reste sur une piste, c'est un vrai défaut.
- `ratio` se calcule sur les largeurs des deux zones ; `gridTemplate` reste la valeur de référence quand un `max-width` centre le corps.
- `table.fits` et `overflowX` se lisent par largeur : un tableau peut tenir à 1440 et déborder à 1000 sans que le CSS soit cassé.
- `cardsPerRow` se calcule par regroupement des `top` arrondis ; le nombre de `top` distincts est le nombre de rangées, pas de cartes par rangée.

### 6. Vérifier sticky séparément

Établir d'abord l'origine de `asideH` : mesurer le panneau à trois hauteurs d'iframe (700, 900, 1100). Une hauteur constante dont les enfants la recomposent (mesuré : `900 = 408 + 20 + 472`) vient du contenu ; une hauteur qui suit `innerHeight` trahit un plafond de type `100vh`, et le budget ci-dessous ne s'interprète plus de la même façon. Un `asideH` exactement égal à `innerHeight` est une coïncidence à écarter par cette variation, pas une preuve.

Utiliser une iframe dédiée de 900 px de haut, pas l'iframe de capture. Avant de conclure, calculer `maxScroll = scrollHeight - innerHeight` et vérifier qu'il dépasse le seuil d'ancrage. Défiler `contentWindow`, relever `w.scrollY` réellement atteint (il peut être borné), puis lire `top` **et** `bottom` du panneau à chaque échantillon. Remettre le défilement à 0 à la fin.

Un plateau `top = topCss` sur deux échantillons ne suffit pas : un panneau aussi haut que la fenêtre reste ancré en haut pendant que son bas passe sous le pli. Une fois `asideH` établi comme hauteur de contenu, le budget de hauteur est `asideH + 2 × topCss` ; s'il dépasse `innerHeight`, le verdict est `STICKY_OVERFLOW`, même si `top` plafonne. Relever `bottom` sur le plateau : `bottom > innerHeight` montre la coupure effective, un `bottom` encore visible avec budget dépassé signale une marge basse inférieure à `topCss`.

| Constat | Verdict |
|---|---|
| `asideH + 2 × topCss > innerHeight` | `STICKY_OVERFLOW` : marge basse insuffisante ; `bottom` dit si le contenu est réellement coupé |
| plateau atteint, budget respecté, `top = topCss` et `bottom ≤ innerHeight` jusqu'à `maxScroll` | `STICKY_OK` |
| plateau tenu puis `top < topCss` à `maxScroll` | `STICKY_OVERFLOW` : bas de colonne atteint, panneau poussé vers le haut |
| plateau jamais atteint avant `maxScroll` | `NON_CONCLUANT` : iframe trop haute pour la page, pas un défaut CSS |

Panneau plafonné (`max-height` + `overflow-y: auto`) : un `bottom` contenu ne prouve pas que le contenu est atteignable. Relever `asideScrollH` et `clientHeight`, défiler le panneau lui-même jusqu'au bout et vérifier que la dernière ligne reste sous le bas du panneau (`lastBottom ≤ asideBottom + 1`) ; sinon le plafond masque du contenu.

### 7. Capturer à l'échelle

- Wrapper de dimensions fixes = taille de l'iframe × échelle, `overflow: hidden`.
- Iframe à largeur réelle, `transform: scale(ECHELLE)`, `transform-origin: top left`, et hauteur ≥ `scrollHeight` de la page pour éviter une fausse coupure basse.
- Avec un hôte de 543 px : iframe 1440×1250, échelle 0.36, wrapper 518×450.
- Prendre une capture pleine page, puis l'inspecter. Bord droit coupé : baisser l'échelle. Bas coupé : augmenter la hauteur de l'iframe.
- Si la capture renvoie `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`, ne pas boucler : marquer la preuve visuelle indisponible et valider la structure (`offsetWidth`, `getBoundingClientRect`, `transform`, dimensions du wrapper). La marche à suivre pour retenter une capture est dans `validation-navigateur-par-repli`.
- Relever les messages console après la dernière navigation.

### 7 bis. Repli CDP quand la largeur doit être exacte

`--window-size` ne fixe pas la largeur CSS sous Chrome headless : mesuré, une demande de 375 px rend `innerWidth=500` (largeur minimale) et une demande de 1024 rend 1008 (‑16 px de cadre), pour un PNG pourtant large de 375 ou 1024 px. Un texte coupé à droite sur un PNG de 375 px alors que l'iframe de 375 px ne déborde pas est cet artefact, pas un défaut de layout. Contrôle préalable : `--dump-dom` sur une `data:` URL qui écrit `innerWidth`.

```bash
node scripts/capturer_cdp.mjs DOSSIER_SORTIE URL 1920 1440 1024 1000 768 375
```

Le script (Node ≥ 22, `CHROME_PATH` pour changer de binaire) fixe `Emulation.setDeviceMetricsOverride` (DPR 1, `mobile` vrai à ≤ 500 px), attend `readyState=complete` et `document.fonts.ready`, refuse toute largeur non exacte (`WIDTH_MISMATCH`, code 3), capture `Page.captureScreenshot` avec un `clip` de la hauteur `scrollHeight`, puis ferme Chrome et supprime son profil. Il imprime une ligne JSON par largeur (`width`, `innerWidth`, `scrollHeight`, `scrollWidth`, `mobile`, `file`, `bytes`) et écrit `PREFIX-LARGEUR.png` (`CAPTURE_PREFIX`, défaut `capture`). En desktop la gouttière de défilement subsiste (`scrollWidth = largeur − 15`), comme dans les iframes ; en mobile elle est en surimpression (`clientWidth = largeur`), donc le contenu est plus large qu'en iframe à la même largeur nominale.

### 8. Nettoyer et prouver l'absence d'effet de bord

- Arrêter le serveur en arrière-plan (`TaskStop` sur l'identifiant retourné au lancement). En cas d'échec (`exit 255`, « Accès refusé » sur un processus enfant), exiger `netstat -ano | grep ":PORT" | grep LISTENING` vide : des sockets `TIME_WAIT` subsistent après fermeture et ne prouvent pas un serveur vivant. Un PID encore en écoute se termine par `taskkill //F //PID N` (double barre sous Git Bash).
- Supprimer le harnais, la capture de travail et les scripts jetables, sauf si l'utilisateur demande les preuves.
- Relever `sha256sum` et `size` de la page avant et après la campagne : identiques, sinon les mesures ne portent pas sur la version finale.

## Pièges vérifiés

| Symptôme observé | Cause | Action |
|---|---|---|
| `viewport=543`, `ratio=0.5`, `gridTemplate="480px"`, `aside static`, `gap=-480` | largeur sous le point de rupture | juger à 1440 ; confirmer avec `mediaMobile` |
| `contentDocument` nul ou `SecurityError` | harnais et page sur deux origines (`file://` vers `http://`, autre port) | un seul `http.server`, même schéma/hôte/port |
| `contentDocument` lisible en `file://` sur un profil | accès dépendant des options du navigateur | ne pas en dépendre : servir les deux en HTTP |
| `innerWidth=0` et capture `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE` | surface in-app masquée | mesurer dans l'iframe ; marquer le visuel indisponible, suivre `validation-navigateur-par-repli` |
| iframe vide ou refusée sur une route | `X-Frame-Options` ou `frame-ancestors` | `curl -sI` ; resservir les octets statiques après égalité SHA-256 |
| `w.scrollTo(0, 500)` puis `scrollY=347` | défilement borné par `maxScroll` | lire `scrollY` réel, échantillonner au-delà du seuil |
| `stickyHeld:false` avec iframe de 1200 px | pas assez de défilement (261 px mesurés) | iframe de 900 px ; vérifier plateau et budget, sinon `NON_CONCLUANT` |
| plateau `top=24` à 350 et 450 px, `bottom=924` sur 900, puis `top=-24` à `maxScroll=498` | panneau de 900 px dans une fenêtre de 900 : budget `asideH + 2 × topCss = 948` dépassé | `STICKY_OVERFLOW` ; le plafonnement CSS relève de `prototyper-variante-layout-sur-copie`, puis remesurer |
| panneau plafonné, `bottom` contenu, dernière ligne inatteignable | `overflow-y` sans course interne suffisante | défiler le panneau jusqu'au bout ; exiger `lastBottom ≤ asideBottom + 1` |
| bas de page coupé sur la capture | hauteur d'iframe < `scrollHeight` | iframe ≥ `scrollHeight`, wrapper = hauteur × échelle |
| bord droit coupé | viewport hôte étroit | réduire l'échelle, jamais la largeur CSS de l'iframe |
| PNG de 375 px au texte coupé à droite, `innerWidth=500` | `--headless=new` impose 500 px de largeur minimale | capturer par CDP (`scripts/capturer_cdp.mjs`) |
| `--window-size=1024` rend `innerWidth=1008`, `innerHeight = H − 95` | cadre de fenêtre retranché de la taille demandée | ne pas déduire la largeur CSS du nom du PNG ; repli CDP |
| `cardsPerRow=2` pour 4 cartes sur 2 rangées | comptage des `top` distincts = rangées | regrouper par `top`, rapporter le maximum par rangée |
| `TaskStop` échoue (`exit 255`) avec « Accès refusé » sur un PID enfant, puis `TIME_WAIT` sur le port | arrêt partiel de l'arbre de processus ; `TIME_WAIT` = connexions fermées, pas un écouteur | exiger l'absence de ligne `LISTENING` ; si un PID écoute encore, `taskkill //F //PID N` |
| `asideH` exactement égal à `innerHeight` (`900 = 408 + 20 + 472`) | hauteur de contenu qui coïncide avec la hauteur d'iframe | remesurer à 700 et 1100 px : `asideH` constant = contenu, `asideH` qui suit `innerHeight` = plafond de fenêtre |

## Rapport

Pour chaque largeur : `viewport`, `mediaMobile`, `grid`, `ratio`, `gap`, `bodyW`, `overflowX`, `table`, `cardsPerRow`, éléments tronqués. Séparément : échantillons sticky (demandé, réel, `top`, `bottom`), budget `asideH + 2 × topCss` contre `innerHeight`, verdict (`STICKY_OK`, `STICKY_OVERFLOW`, `NON_CONCLUANT`), et pour un panneau plafonné `asideScrollH`/`clientHeight` avec la dernière ligne atteinte ou non ; chemin, échelle et largeur CSS réellement rendue (`innerWidth`) de chaque capture, messages console, port et racine servis, `sha256`/`size` de la page avant et après. Terminer par les limites : largeur réellement testée, ressources externes, origine utilisée, éléments non couverts.

## Checklist

- [ ] `innerWidth` mesuré avant de monter le harnais.
- [ ] Harnais et page servis par le même `http.server`, même origine.
- [ ] Chaque mesure renvoie `viewport` et `mediaMobile`, pas seulement un ratio.
- [ ] Le layout desktop est jugé sur une largeur où `mediaMobile` est faux.
- [ ] Sticky testé sur une iframe de hauteur réaliste, avec `maxScroll` et `scrollY` réels.
- [ ] Plateau sticky jugé sur `top` **et** `bottom` jusqu'à `maxScroll`, pas sur deux échantillons seulement.
- [ ] Budget `asideH + 2 × topCss` comparé à `innerHeight`, verdict sticky explicite.
- [ ] `asideH` remesuré à au moins trois hauteurs d'iframe avant d'appliquer le budget sticky.
- [ ] Panneau plafonné : défilement interne mené jusqu'à la dernière ligne.
- [ ] Capture produite par `transform: scale` dans un wrapper clippé, bord droit et bas contrôlés.
- [ ] Chaque capture prouve sa largeur CSS par `innerWidth`, pas par la largeur du fichier PNG.
- [ ] Erreurs console relevées.
- [ ] Serveur arrêté, harnais supprimé, `sha256`/`size` de la page inchangés.
- [ ] Arrêt du serveur prouvé par l'absence de `LISTENING`, pas par le seul code de retour de `TaskStop`.

## Ressources

- `scripts/capturer_cdp.mjs` — capture pleine page à largeurs CSS exactes par CDP (`Emulation.setDeviceMetricsOverride`), pour remplacer `--window-size` quand le PNG doit faire exactement la largeur demandée.
- `references/modeles-harnais.md` — harnais de mesure, script de mesure, sonde sticky, contrôle de la hauteur du panneau, en-tête et chevauchement, harnais de capture, commandes, repli CDP.
- `references/cas-verifie-hub-ponts.md` — mesures réelles du 2026-10-28, auto-test, fausse alerte sticky, débordement bas d'un panneau non plafonné, contrôle de hauteur et arrêt du serveur, repli CDP et largeurs exactes, limites.
