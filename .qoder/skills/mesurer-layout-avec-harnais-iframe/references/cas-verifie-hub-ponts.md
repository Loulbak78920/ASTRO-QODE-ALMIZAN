# Cas vérifié — mesures par harnais d'iframes

Trois jeux de preuves : la session source (mesures réelles sur une page de production locale), l'auto-test de ce Skill sur une fixture jetable, et une session de contrôle de la hauteur du panneau et de l'arrêt du serveur.

## Sources

- Session `527776b5-c1d9-4dc9-9f08-ded973d156c9`, titre « Implémentation CSS Mizan », tours `d60632cf` (10:03–10:08 UTC) et `46b14e90` (10:10 UTC).
- JSONL `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\527776b5-c1d9-4dc9-9f08-ded973d156c9.jsonl`, 2 076 022 octets, `sha256 87177cfb…f9402`, mtime local 2026-10-28 11:13:41. Les numéros de ligne ci-dessous ne valent que pour cette empreinte.
- Auto-test du 2026-10-28, fixture `.qoder/tmp/harness-fixture-20261028` (supprimée après relevé) : `page.html` `e6674b60…cdcc`, `harness.html` `733ecce4…b699`, `capture.html` `c1650ee3…7e85`.
- Session `41745dcd-d658-4a9c-85be-09529f43e38e`, titre « 创建可复用 Skill » (2026-10-28), tours `cb2ee1ad` (10:18 UTC) et `c83d617f` (10:23 UTC) : sonde sticky sur les variantes `PROTO_70-30` puis `PROTO_70-30-scroll`.
- JSONL de cette session : `41745dcd-d658-4a9c-85be-09529f43e38e.jsonl`, 1 070 354 octets, `sha256 c96c4cf4…48e86`.
- Session `4006da34-228a-497b-b895-707e45c586ac`, titre « 更新部署 Skill », tour `02b7ec29` (10:36 UTC, `completed`) : sonde sticky, contrôle de hauteur du panneau et arrêt du serveur sur la page servie en production.
- JSONL de cette session : `4006da34-228a-497b-b895-707e45c586ac.jsonl`, snapshot du 2026-10-28 11:41 +0100, 1 932 145 octets, `sha256 d38624fe…96afc5`. La session était encore `running` à la lecture : ce snapshot ne couvre que les tours cités.

## A. Session source

### A1. Mesure directe : point de rupture, pas bug CSS

Navigation `file:///…/HUB_PONTS_SYNCHRONES_AL_MIZAN.PROTO_62-38.html`, puis `evaluate_script` (JSONL ligne 60) :

```text
viewport 543 | bodyW 528 | gridTemplate "480px" | primaryW 480 | secondaryW 480
ratio 0.5 | gap -480 | asideSticky "static" | overflowX 0
tableW 438 | tableContentW 566 | tableOverflows true
```

543 px est sous le point de rupture `max-width: 1024px` : une seule colonne et un `gap` négatif sont attendus. Conclusion erronée à éviter : « le 62/38 est cassé ».

### A2. Harnais servi en HTTP, iframes de largeur fixe

`py -3 -m http.server 8099 --bind 127.0.0.1` depuis la racine, harnais `.qoder/tmp/proto-harness.html`, iframes 1440×900 et 1000×900 (JSONL ligne 79) :

| Largeur | `mediaMobile` | `gridTemplate` | ratio | gap | aside |
|---|---|---|---|---|---|
| 1440 | faux | `823.359px 504.625px` | 0.62 | 24 | sticky |
| 1000 | vrai | `937px` | 0.5 | -937 | static |

À 1440 : `pageOverflowX 0`, tableau 781/781 (`fits`), 4 cartes de 402 px, 2 rangées. À 1000 : le point de rupture s'applique, ce n'est pas une régression.

Le champ `cardsPerRow` de la session comptait les `top` distincts, donc des rangées (2 pour 4 cartes) : le modèle de ce Skill regroupe par `top` et rapporte le maximum par rangée.

### A3. Sticky mesuré dans `contentWindow`

Iframe 1440×900, `w.scrollTo(0, 500)` (JSONL ligne 110) :

```text
iframeScrollY 347 | asideTopBefore 24 | asideTopAfter 24 | stickyHeld true
asideH 700 | docH 1247 | asideBottomGapAtScroll 176
```

La demande 500 est bornée à 347 : lire `w.scrollY` réel, pas la valeur demandée.

### A4. Capture à l'échelle

Wrapper `.scaler` 518×324, iframe 1440×900, `transform: scale(0.36)`, `transform-origin: top left` (JSONL lignes 86, 113). La page mesurant 1199 px de haut, l'iframe de 900 px coupait le bas : passage à un wrapper 518×450 avec iframe 1440×1250 avant capture.

### A5. Route servie et re-hébergement

`/ponts`, `/hub-ponts`, `/ponts-synchrones` répondent 200 `text/html`, 29 409 octets (JSONL ligne 373) ; le fichier local est 29 409 octets, `sha256 a63d6885…620bf` (ligne 485). Harnais et page sont servis par le même `http.server` (port 18099, même origine) ; une page publique refusant l'encadrement doit être re-servie depuis cette origine après égalité de taille et de SHA-256.

Mesures finales (JSONL ligne 406) : à 1440, `grid 823.359px 504.625px`, `ratio 0.62`, `gap 24`, `headSpans true`, `aside sticky`, tableau 781/781, `jsFn true`, `overflowX 0` ; à 390, une colonne `327px`, tableau 285/566 non contenu, `overflowX 0`.

### A6. Fausse alerte sticky

Iframe de 1200 px de haut (JSONL ligne 412) : `docH 1461`, `maxScroll 261`, `asideH 846`, `top` 326 → 226 → 126 → 65 pour y = 0/100/200/261. Le panneau n'atteint jamais `top: 24` : `stickyHeld false`. Iframe ramenée à 900 px (ligne 418) : `maxScroll 561`, `top 76` à y = 250, puis `top 24` à y = 350, 500 et 561, `bottom 870`.

Règle : vérifier `maxScroll` avant d'interpréter ; une iframe trop haute rend le test non concluant.

## B. Auto-test de ce Skill

Fixture : deux colonnes 62/38, point de rupture 1024, aside `sticky`, cartes et tableau, servie par `py -3 -m http.server 18099 --bind 127.0.0.1`.

### B1. Origine

| Harnais → iframe | `contentDocument` | Erreur |
|---|---|---|
| `file://` → `file://` (même dossier) | accessible | aucune |
| `file://` → `http://127.0.0.1:18099` | nul | `SecurityError: … Blocked a frame with origin "file://" from accessing a cross-origin frame.` |

L'accès `file://` vers `file://` a fonctionné dans ce profil, contrairement à l'hypothèse initiale : il dépend des options du navigateur et ne doit pas être la méthode. Le cross-origin `file://` vers `http://` est refusé.

### B2. Mesures HTTP

| Largeur | `mediaMobile` | `grid` | ratio | gap | aside | tableau |
|---|---|---|---|---|---|---|
| 1920 | faux | `823.359px 504.625px` | 0.62 | 24 | sticky | 821/821 |
| 1440 | faux | `823.359px 504.625px` | 0.62 | 24 | sticky | 821/821 |
| 1280 | faux | `739.656px 453.328px` | 0.62 | 24 | sticky | 738/738 |
| 1000 | vrai | `937px` | 0.5 | -937 | static | 935/935 |

`bodyW` 1400 à 1440 et 1920 (plafond `max-width`), `overflowX 0` partout. À 1280, `clipped` a signalé `div.cards`, `div.card` et `p` en cascade : les adresses de la fixture ne se coupent pas, ce qui illustre l'heuristique et sa remontée aux ancêtres.

### B3. Sticky

`viewportH 900`, `docH 1148`, `asideH 720`, `maxScroll 248`, `topCss 24`. `top` passe de 128 (y = 0) à 24 dès y = 200, puis reste à 24 jusqu'à 248 ; une demande de 300 est bornée à `actual 248`. Plateau confirmé.

### B4. Capture

Iframe 1440×1250, `transform: matrix(0.36, …)`, `transform-origin: 0px 0px`, rect 518,4×450, wrapper 518×450 `overflow: hidden`, `contentViewport 1440`, contenu 1250 px entièrement dans l'iframe. La structure de capture est validée.

En revanche, `take_screenshot` a répondu `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE` (`viewport=0x0, visible=false, attached=false, visibilityState=hidden`) et `innerWidth` du hôte valait 0. Aucune preuve visuelle n'est revendiquée pour cet auto-test ; le comportement de repli est celui de `validation-navigateur-par-repli`.

### B5. Console

`list_console_messages` : aucune entrée.

## C. Panneau sticky plus haut que la fenêtre (session 41745dcd)

Variantes de la même page servie, iframe 1440 × 900, `topCss 24`, `docH 1398`, `maxScroll 498`. Les deux sorties ci-dessous sont les résultats bruts de `evaluate_script` (tours `cb2ee1ad` et `c83d617f`).

### C1. Sans plafond : faux succès si seul `top` est lu

```json
{"asideH": 900, "viewportH": 900, "topCss": 24, "maxScroll": 498,
 "samples": [
  {"asked": 0,   "actual": 0,   "top": 326, "bottom": 1226},
  {"asked": 200, "actual": 200, "top": 126, "bottom": 1026},
  {"asked": 300, "actual": 300, "top": 26,  "bottom": 926},
  {"asked": 350, "actual": 350, "top": 24,  "bottom": 924},
  {"asked": 450, "actual": 450, "top": 24,  "bottom": 924},
  {"asked": 498, "actual": 498, "top": -24, "bottom": 876}
 ]}
```

`top` plafonne bien à 24 sur deux échantillons, mais `bottom = 924` sur une fenêtre de 900 : 24 px sous le pli. À `maxScroll`, le panneau est poussé vers le haut (`top = -24`). `budget = 900 + 2 × 24 = 948 > 900` ⇒ `STICKY_OVERFLOW`. L'ancienne règle « plateau sur deux échantillons » concluait à tort au succès.

### C2. Plafonné en desktop : `STICKY_OK`

Règle appliquée (via `prototyper-variante-layout-sur-copie`) : sous `@media (min-width: 1025px)`, `max-height: calc(100vh - 2 * var(--mizan-gap))` et `overflow-y: auto` sur `.secondary-pane`.

```json
{"asideH": 852, "asideScrollH": 900, "viewportH": 900, "topCss": 24, "maxScroll": 498,
 "samples": [
  {"asked": 0,   "actual": 0,   "top": 326, "bottom": 1178},
  {"asked": 200, "actual": 200, "top": 126, "bottom": 978},
  {"asked": 300, "actual": 300, "top": 26,  "bottom": 878},
  {"asked": 350, "actual": 350, "top": 24,  "bottom": 876},
  {"asked": 450, "actual": 450, "top": 24,  "bottom": 876},
  {"asked": 498, "actual": 498, "top": 24,  "bottom": 876}
 ],
 "internal": {"firstTopAt0": 24, "lastBottomAtEnd": 876, "asideBottom": 876,
              "lastFullyVisible": true, "reachedScrollTop": 48}}
```

`budget = 852 + 48 = 900 = viewportH`, `bottom = 876 ≤ 900`, plateau tenu à `maxScroll`. Défilement interne `48 = 900 - 852` atteint, dernière ligne à 876 = bas du panneau : le plafond ne masque rien.

### C3. Règle dérivée

- Le plateau de `top` est nécessaire mais non suffisant ; `bottom` et `budget = asideH + 2 × topCss` décident.
- Un panneau plafonné exige une preuve de défilement interne ; un `bottom` contenu seul ne prouve pas l'accessibilité de la fin du contenu.
- Les fichiers `PROTO_70-30` et `PROTO_70-30-scroll` ont été supprimés à la demande de l'utilisateur (tour `55fc8811`) ; seules les sorties ci-dessus et l'historique de session subsistent.

## D. Hauteur du panneau et arrêt du serveur (session 4006da34)

Page 70/30 servie (29 409 o, `88ff31b9…`), copie statique sous `.qoder/tmp/` servie sur `127.0.0.1:18700` : la route publique répond `X-Frame-Options: SAMEORIGIN` et `frame-ancestors 'self'`. Hôte `innerWidth = 0`, capture indisponible (`NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`).

### D1. Sonde sticky brute

Iframe 1440 × 900, `topCss 24`, `docH 1398`, `maxScroll 498`, `asideH 900`, `asideScrollH 900`, `maxHeightCss "none"`, `overflowY "visible"` :

```json
{"samples": [
  {"asked": 0,   "actual": 0,   "top": 326, "bottom": 1226},
  {"asked": 200, "actual": 200, "top": 126, "bottom": 1026},
  {"asked": 300, "actual": 300, "top": 26,  "bottom": 926},
  {"asked": 350, "actual": 350, "top": 24,  "bottom": 924},
  {"asked": 450, "actual": 450, "top": 24,  "bottom": 924},
  {"asked": 498, "actual": 498, "top": -24, "bottom": 876}
 ]}
```

`budget = 900 + 48 = 948 > 900` ⇒ `STICKY_OVERFLOW` ; `bottom = 924` (24 px sous le pli), puis `top = -24` à `maxScroll`.

### D2. Contrôle de hauteur : coïncidence écartée

```json
{"h700":  {"asideH": 900, "asideScrollH": 900, "childH": [408, 472], "viewportH": 700},
 "h900":  {"asideH": 900, "asideScrollH": 900, "childH": [408, 472], "viewportH": 900},
 "h1100": {"asideH": 900, "asideScrollH": 900, "childH": [408, 472], "viewportH": 1100}}
```

`asideH` reste à 900 quand la fenêtre varie : la hauteur vient du contenu (408 + 20 de gouttière + 472), pas du viewport. L'égalité `asideH = innerHeight = 900` à la hauteur de référence était une coïncidence ; sans cette remesure, le panneau aurait pu passer pour un panneau plafonné à `100vh`.

### D3. Arrêt du serveur après échec de `TaskStop`

```text
Failed to terminate process tree pid=4776: Command failed with exit code 255:
le processus de PID 10596 (processus enfant de PID 3408) n'a pas été arrêté. Raison : Accès refusé.
```

Sur le port 18700 ensuite : aucun PID en écoute, seulement trois sockets `TCP 127.0.0.1:18700 … TIME_WAIT 0`. Le serveur était donc arrêté malgré l'échec rapporté ; `TIME_WAIT` ne signale qu'une connexion fermée. Les accents de la sortie `taskkill` sont apparus corrompus (console cp1252) : citer `exit code 255` et la chaîne ASCII, sans recopier les caractères accentués.

Page inchangée avant/après : `88ff31b9…`, 29 409 o, en local comme en production ; console sans message.

## E. Repli CDP — captures à largeurs exactes (2026-10-28)

Contexte : production locale `/ponts`, `take_screenshot` in-app indisponible (`viewport=0x0`). Les captures ont été produites par Chrome headless local piloté par CDP, hors navigateur in-app.

### E1. Rognage de `--window-size`

Sonde `--dump-dom` sur une `data:` URL écrivant `innerWidth` × `innerHeight`, profil Chrome dédié :

| Demandé | `innerWidth` | `innerHeight` |
|---|---|---|
| 375×800 | 500 | 705 |
| 500×800 | 500 | 705 |
| 700×800 | 684 | 705 |
| 1024×900 | 1008 | 805 |

La largeur est bornée à 500 px, et le cadre retranche 16 px en largeur et 95 px en hauteur. Le PNG, lui, garde la taille demandée : un PNG de 375 px dont le contenu est rendu à 500 px montre un texte tronqué à droite sans aucun débordement CSS (iframe 375 : `overflowX=visible`, `bodyScrollW=360`). La première capture a été rejetée sur ce constat ; le même rendu rejoué par CDP est complet.

### E2. Campagne CDP

Six largeurs, `innerWidth` vérifié égal à la cible, `Emulation.setDeviceMetricsOverride`, DPR 1, `mobile` vrai à 375 :

| PNG | dimensions | octets | SHA-256 |
|---|---|---|---|
| `ponts-1920.png` | 1920×1398 | 352 859 | `c8846eed…2dbc3c` |
| `ponts-1440.png` | 1440×1398 | 345 920 | `340b1208…26cfeaf4` |
| `ponts-1024.png` | 1024×2220 | 341 209 | `ebdd737c…0312bf` |
| `ponts-1000.png` | 1000×2173 | 338 928 | `02418c67…9e7027` |
| `ponts-768.png` | 768×2488 | 342 275 | `23149316…20414e` |
| `ponts-375.png` | 375×3741 | 314 467 | `c60e4f71…8bdaa1` |

Rejeu du script du Skill sur 1024 et 375 : octets et SHA-256 identiques (`ebdd737c…`, `c60e4f71…`), donc reproductible depuis le paquet installé.

### E3. Version de page et concurrence

La page a été réécrite deux fois pendant la campagne par une autre session : `a63d6885…` (ratio 0.62) puis `88ff31b9…` (ratio 0.70, 29 409 o) ; l'état final est `d317f0ec…`, 29 598 o, mtime 11:40:09, `--mizan-ratio: 0.70`. Le delta est un `@media (min-width: 1025px)` ajoutant `max-height: calc(100vh - 2 * var(--mizan-gap))` et `overflow-y: auto` à `.secondary-pane` (cas C2), sans effet à 375 px. Les six PNG et le rejeu portent sur `d317f0ec…`, hash inchangé avant et après ; les mesures et captures du premier lot (0.62) ont été jetées.

### E4. Mesures 375 px

Iframe 375×900 (gouttière desktop 15 px) : `mediaMobile=true`, grille `312px` sur une colonne, aside `static`, `overflowX=visible`, `bodyScrollW=360`, tableau 566 px dans une boîte de 270 (défilement interne), 4 cartes sur 4 rangées, `h1` sur 140 px, `scrollHeight=3903`. Émulation mobile (sans gouttière) : contenu 327 px, `scrollHeight=3741`. L'écart de hauteur vient de la largeur utile, pas d'un défaut de layout.

## Limites

- `X-Frame-Options` et `frame-ancestors` de la route de production n'ont pas été mesurés dans la session source ; le contrôle `curl -sI` reste obligatoire avant de conclure qu'une route peut être encadrée.
- L'auto-test de la section B n'a pas produit de capture visible ; seules les dimensions et le transform ont été assertés.
- Les captures de la section E viennent de Chrome headless local piloté par CDP, pas du navigateur in-app ; l'émulation `mobile` ne couvre ni un DPR > 1 ni le tactile.
- Les largeurs testées sont celles du harnais ; un comportement dépendant de la hauteur (sticky) exige une iframe séparée.
- Le verdict `STICKY_OVERFLOW` sur budget dépassé est conservateur : si `bottom ≤ viewportH`, le panneau est visible mais sa marge basse est inférieure à `topCss` ; le rapport doit le dire au lieu d'annoncer une coupure.
- Le cas C provient de deux exécutions réelles sur des variantes supprimées depuis ; il n'a pas été rejoué sur une fixture indépendante.
- La sonde `internal` suppose que `firstElementChild` et `lastElementChild` représentent le contenu du panneau.
- Le cas D provient du tour `02b7ec29` d'une session encore `running` à la lecture (snapshot JSONL du 2026-10-28 11:41) ; le tour suivant modifiait la page servie et n'est pas couvert.
- Le contrôle de hauteur D2 n'a été exécuté qu'à largeur 1440 : un plafond dépendant de la largeur n'est pas détecté.
- Les numéros de ligne JSONL sont liés à l'empreinte `87177cfb…f9402` du fichier.
