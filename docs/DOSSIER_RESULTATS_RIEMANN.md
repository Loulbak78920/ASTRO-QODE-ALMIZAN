# Dossier de résultats — Hypothèse de Riemann

Projet IMAM8MAHDI / AL-MIZAN · état vérifié au **2026-10-28**.
Ce dossier remplace les fragments dispersés : il réunit ce qui est **démontré**, ce qui est **calculé ici**, ce qui reste **ouvert**, et ce qui n'est **pas soutenu** par les artefacts.

## 0. Règle de lecture

| Statut | Signification |
| :--- | :--- |
| **DÉMONTRÉ** | théorème publié et accepté, valable pour tous les cas de son énoncé |
| **CALCULÉ** | résultat numérique reproductible, borné à une plage ou à une hauteur |
| **OUVERT** | conjecture non résolue |
| **NON SOUTENU** | affirmation absente de la littérature ou contredite par elle |
| **SPÉCULATIF** | piste de recherche sans conséquence technologique établie |

Correspondance avec les statuts du registre AL-MIZAN : `OPÉRATIONNEL` = page et scripts exécutables ; `SIMULÉ` = calcul numérique reproductible, non preuve ; `SPÉCIFIÉ` = énoncé d'une preuve à venir. L'entrée `MAT-01` du registre est `SIMULÉ`.

## 1. Verdict consolidé

| Objet | Statut | Preuve ou artefact | Portée |
| :--- | :--- | :--- | :--- |
| Aucun zéro de ζ sur le mur σ = 1 | **DÉMONTRÉ** | Hadamard et de la Vallée Poussin, 1896 | tout `t`, `s ≠ 1` |
| Aucun zéro sur le mur σ = 0 | **DÉMONTRÉ** | équation fonctionnelle `ξ(s) = ξ(1−s)` | tout `t`, `s ≠ 0` |
| Tous les zéros non triviaux dans `0 < σ < 1` | **DÉMONTRÉ** | corollaire des deux précédents | tout `t` |
| Région sans zéros `σ ≥ 1 − c/log t` | **DÉMONTRÉ** | de la Vallée Poussin, 1896 | `t` grand |
| Une infinité de zéros sur `σ = ½` | **DÉMONTRÉ** | Hardy, 1914 | infinité |
| Au moins 5/12 des zéros sur `σ = ½` | **DÉMONTRÉ** | Pratt–Robles–Zaharescu–Zeindler, 2019 | proportion ≈ 41,7 % |
| Vérification locale `t ≤ 50` | **CALCULÉ** | `riemann_comptage.json` | 10 zéros, écart 0 |
| Certificat borné `T* = 10 000` | **CALCULÉ** | `riemann_certificat_T1e4.json` | 10 142 zéros, écart 0, **cohérence interne** |
| Hauteur `3×10¹²` vérifiée | **CALCULÉ (publié)** | Platt–Trudgian, 2021 | ≈ 1,24×10¹³ zéros |
| **Hypothèse de Riemann complète** | **OUVERT** | — | aucun zéro hors de `σ = ½` |
| Une preuve de RH casserait RSA | **NON SOUTENU** | aucune réduction connue | voir §5 |
| RH expliquerait les flux Internet | **NON SOUTENU** | aucun lien établi | voir §5 |
| RH donnerait les niveaux d'énergie quantiques | **SPÉCULATIF** | programme Hilbert–Pólya | voir §5 |

## 2. Résultats calculés dans ce projet

### 2.1 Vérification `t ≤ 50` — `riemann_comptage.json`

Méthode 1 : principe de l'argument sur le rectangle `[−0,5 ; 1,5] × [0,5 ; T]`.
Méthode 2 : changements de signe de `Z(t) = e^{iθ(t)} ζ(1/2 + it)` avec raffinement.
Précision `mpmath` : 20 chiffres. Pas de scan : 0,05.

| `T` | zéros par contour | zéros sur la droite | écart |
| ---: | ---: | ---: | ---: |
| 20 | 1 | 1 | 0 |
| 30 | 3 | 3 | 0 |
| 40 | 6 | 6 | 0 |
| 50 | 10 | 10 | 0 |

- `ecart_max = 0`.
- `hypothese_demontree = false`, `portee = "0.5 < t < 50"`.
- Limite explicite du JSON : « vérification numérique seulement : aucune démonstration ».
- Les deux méthodes appliquent des principes distincts au **même noyau ζ** (`mpmath`) : c'est un recoupement, pas une certification formelle indépendante.

### 2.2 Certificat borné `T* = 10 000` — `riemann_certificat_T1e4.json`

Titre : « Certificat numerique borne RH(T\*) a T\* = 10000 ».
`hypothese_demontree = false`, `statut = "coherent"`, `portee = "0 < gamma <= 10000 (hauteur T*)"`.
Unité : **hauteur** `T` (ordonnée γ), **pas** un nombre de zéros.

| Grandeur | Valeur mesurée |
| :--- | ---: |
| Zéros sur la droite critique sous `T*` | **10 142** |
| `N(chemin)` indépendant | **10 142** |
| Écart entre les deux comptages | **0** |
| `θ(T*)/π` | 10 141,965348189959 |
| `N(T)` lissé (Riemann–von Mangoldt) | 10 142,965347526813 |
| Écart comptage entier vs `θ/π + S` | 1,12×10⁻⁹ |
| Résidu max de `Z(t)` aux zéros | 1,83×10⁻⁹ |
| Premier zéro | 14,134725141804722 |
| Dernier zéro sous `T*` | 9 998,850397089733 |
| Espacement minimal | 0,037698497624660376 |
| Paire serrée (k = 6 708) | 7 005,0629 / 7 005,1006, recontrôlée au pas 0,005 → 2 changements de signe |
| Règle de Rosser | vérifiée sur 9 302 blocs complets, **0 échec** |
| Points de Gram proches d'un zéro | 0 |
| Autotests | `N(50) = 10`, `N(1000) = 649` — conformes |
| Échantillon `mpmath` (16 points) | écart max Euler–Maclaurin vs `mpmath` = 9,0×10⁻¹¹ |
| Comparaison au comptage projet | 10 zéros, écart max 7,0×10⁻¹¹ |
| Point de Gram `g₀` | 17,845599540411847 vs attendu 17,84559954041086 (écart 9,9×10⁻¹³) |
| Durée d'exécution | 131,4 s |

Limites déclarées par l'artefact lui-même :

- pas d'arithmétique d'intervalle, donc **pas un certificat formel** ;
- le comptage `N(T)` et le scan reposent sur le **même noyau ζ** : l'égalité est une **cohérence**, pas une preuve indépendante ;
- loi de Gram non vérifiée partout (816 blocs de longueur > 1, 822 intervalles vides, 1 638 violations) — c'est attendu, la loi de Gram est une heuristique, pas un théorème ; la règle de Rosser, elle, est vérifiée ;
- pas de revendication d'antériorité : la hauteur `10⁴` est couverte depuis longtemps.

### 2.3 Contrôle indépendant du 2026-10-28 (lecture seule)

- `sha256(riemann_comptage.json) = a9a19af3…08f28a1` — conforme au pack.
- `sha256(riemann_certificat_T1e4.json) = d4e4bd52…b897b` — conforme au pack.
- Résidus recalculés à `mpmath` dps 30 sur les zéros du comptage `t ≤ 50` :

| k | `t` | résidu JSON | résidu recalculé |
| ---: | ---: | ---: | ---: |
| 1 | 14,1347251417346938 | 7,57×10⁻¹⁸ | 7,56893×10⁻¹⁸ |
| 2 | 21,022039638771555 | 8,38×10⁻¹⁸ | 8,38023×10⁻¹⁸ |
| 3 | 25,0108575801456888 | 5,05×10⁻¹⁷ | 5,04604×10⁻¹⁷ |

- Contrôles structurels : 10 zéros sous `t = 50`, `ecart_max = 0`, comptages contour = droite à chaque `T`, `10 142 = N(chemin)`, autotests conformes, `hypothese_demontree = false` dans les deux JSON.
- **RESULT : PASS**.

## 3. Preuves analytiques des murs

### 3.1 Mur `σ = 1` — Hadamard et de la Vallée Poussin (1896)

Pour `σ > 1`, le logarithme du produit eulérien donne

```
log ζ(σ + it) = Σ_p Σ_{k≥1} p^(−kσ) e^(−ik t log p) / k
```

En combinant `3 log ζ(σ) + 4 Re log ζ(σ+it) + Re log ζ(σ+2it)` :

```
Σ_p Σ_k [3 + 4 cos(k t log p) + cos(2k t log p)] / (k p^(kσ)) ≥ 0
```

car `3 + 4 cos x + cos 2x = 2(1 + cos x)² ≥ 0`. Donc

```
|ζ(σ)³ · ζ(σ+it)⁴ · ζ(σ+2it)| ≥ 1        (σ > 1)
```

Si `ζ(1+it₀) = 0` avec `t₀ ≠ 0`, alors quand `σ → 1⁺` : `ζ(σ)³ ~ (σ−1)^(−3)` et `ζ(σ+it₀)⁴ = O((σ−1)⁴)`, donc le produit tend vers `0`, contredisant `≥ 1`. **Aucun zéro sur `σ = 1`**, sauf le pôle `s = 1`.

### 3.2 Mur `σ = 0` — équation fonctionnelle

`ξ(s) = ½ s(s−1) π^(−s/2) Γ(s/2) ζ(s)` est entière et vérifie `ξ(s) = ξ(1−s)`.
Un zéro de `ζ` en `s = it₀` (`t₀ ≠ 0`) donnerait `ξ(it₀) = 0`, donc `ξ(1−it₀) = 0`, donc un zéro de `ζ` sur `σ = 1`, interdit. De plus `ζ(0) = −1/2 ≠ 0`.

### 3.3 Corollaire et résultats voisins

Tous les zéros non triviaux sont **strictement à l'intérieur** de `0 < σ < 1`.
Ce qui est aussi démontré, sans prouver RH :

- région sans zéros `σ ≥ 1 − c/log t` (de la Vallée Poussin, 1896) ;
- une infinité de zéros sur `σ = ½` (Hardy, 1914) ;
- au moins 5/12 des zéros sur `σ = ½` (Pratt–Robles–Zaharescu–Zeindler, 2019).

**Ce qui n'est pas démontré** : que *tous* les zéros intérieurs soient sur `σ = ½`. Les murs sont fermés ; l'intérieur reste ouvert.

## 4. Antériorité — comparaison après conversion d'unité

| Source | Unité | Valeur | Équivalent |
| :--- | :--- | ---: | ---: |
| van de Lune, te Riele, Winter (1986) | zéros | 1,5×10⁹ | hauteur ≈ 5,45×10⁸ |
| Gourdon (2004) | zéros | 10¹³ | hauteur ≈ 2,45×10¹² |
| Platt–Trudgian (2021) | **hauteur** | 3×10¹² | ≈ 1,24×10¹³ zéros |

Conséquence : `T* = 10 000` et `t ≤ 50` sont des **reproductions locales**. Aucune antériorité, aucune nouveauté, aucune revendication de prix.

## 5. Impact réel — réponse point par point à l'évaluation externe

| Affirmation externe | Verdict | Justification |
| :--- | :--- | :--- |
| « Le calcul `t = 50` confirme localement la théorie » | **EXACT, MAIS LOCAL** | 10 zéros, deux comptages égaux ; aucune portée au-delà de `t = 50` |
| « La littérature a vérifié jusqu'aux 10¹³ premiers zéros » | **EXACT** | Gourdon (2004) : 10¹³ zéros ; Platt–Trudgian (2021) : hauteur 3×10¹² ≈ 1,24×10¹³ zéros |
| « Une preuve universelle aurait un impact planétaire » | **PARTIELLEMENT EXACT** | événement mathématique majeur (problème du millénaire, 1 M$), refonte de la théorie analytique des nombres ; pas de « planétaire » technologique démontré |
| « Cela casserait la cryptographie RSA » | **NON SOUTENU** | aucune réduction connue de la factorisation à RH. Sous GRH, le test de Miller–Rabin devient déterministe (Miller 1976 ; borne de Bach 1990) et des bornes explicites s'améliorent — cela change des **garanties algorithmiques**, pas la dureté de RSA |
| « Cela modifierait la modélisation des flux Internet » | **NON SOUTENU** | aucun lien causal établi dans la littérature |
| « Cela éclairerait les niveaux d'énergie en physique quantique » | **SPÉCULATIF** | interprétation spectrale de Hilbert–Pólya : programme de recherche, aucune conséquence technologique établie |
| « Double algorithme Python fiable » | **EXACT À PORTÉE LIMITÉE** | deux principes distincts sur le même noyau ζ ; à `T* = 10⁴` c'est une **cohérence**, pas une preuve indépendante |
| « Visualisation claire et reproductible » | **EXACT** | page publique FR/EN/AR, figures, cartes X, empreintes SHA-256 |

Synthèse d'impact, dans la logique AL-MIZAN :

| Niveau | Impact | Statut |
| :--- | :--- | :--- |
| Technique & code | fort, mais borné à `t ≤ 50` et `T* = 10⁴` | **CALCULÉ** |
| Pédagogique | fort : visualisation et reproduction | **OPÉRATIONNEL** |
| Recherche fondamentale | nul : reproduction, pas découverte | **SIMULÉ** |
| Technologies (RSA, Internet, quantique) | aucun effet démontré par ce dossier | **NON SOUTENU / SPÉCULATIF** |

## 6. Ce qu'il faudrait pour une preuve analytique

1. Prouver l'absence de zéros hors de `σ = ½` pour **tout** `t`, pas seulement sous une hauteur finie. La région sans zéros connue s'arrête à `1 − c/log t` ; aucune méthode connue ne la pousse à `½`.
2. Contrôler le terme `S(T) = arg ζ(1/2 + iT)/π` ou une structure spectrale/arithmétique équivalente. Les vérifications numériques ne franchissent jamais cette étape.
3. Fournir un certificat formel en arithmétique d'intervalle, avec noyaux indépendants. Le certificat actuel est en double précision et partage le même noyau ζ.
4. Passer la relecture par les pairs. Aucun des artefacts du projet ne prétend le faire.

Un calcul plus long, même à `10⁹` zéros, ne change pas la nature de la conclusion : il déplace la borne, pas la preuve.

## 7. Reproductibilité

Depuis `ASTRO-Q°ODE_SYSTEME/` :

```bash
py -3 oeuvre_universelle/riemann_verification.py
py -3 oeuvre_universelle/riemann_certificat_T1e4.py
```

- `riemann_verification.py` réécrit `riemann_comptage.json` ; le certificat prend ≈ 131 s et réécrit `riemann_certificat_T1e4.json`.
- **Attention** : ces scripts écrivent un horodatage et une durée, donc **toute réexécution change les SHA-256**. Pour contrôler sans modifier les artefacts scellés, copier le dossier dans un répertoire temporaire et y exécuter les scripts.
- Attendu, à l'identique : `ecart_max = 0` ; `10 142 = N(chemin)` ; autotests `N(50) = 10`, `N(1000) = 649` ; `hypothese_demontree = false`.

## 8. Inventaire et empreintes (2026-10-28)

| Fichier | SHA-256 |
| :--- | :--- |
| `oeuvre_universelle/riemann_verification.py` | `3445b6a18745b9c9f12f363f6d95eaa0ea8adc4a3fa164552a68705f7c614ae5` |
| `oeuvre_universelle/riemann_certificat_T1e4.py` | `646d7493a56d041a4134e590a6c443fe396f0a6386ac72056821d68771cb65d4` |
| `oeuvre_universelle/generer_visuels_x_riemann.py` | `de621a2990091748f69ea10847ff96391bf2601b1cd6b57a808c956712aa17de` |
| `resultats/oeuvre_universelle/riemann_comptage.json` | `a9a19af327187570277e655dfd8adee532b1436e0a23e88fbdfe1102808f28a1` |
| `resultats/oeuvre_universelle/riemann_certificat_T1e4.json` | `d4e4bd5246d0e8ca2eff8d2d2bde6b494e139bf50febb6730061c319934b897b` |
| `web_cloud/hypothese_riemann.html` | `d052616c39fc0d10902068664aab1082c630927482a140aa993863738d68e770` |
| `docs/POSTS_X_RIEMANN_FR_EN_AR.md` | `2f85b99eb4162fc88806010eef6675185b340263fd25e68ca1ac6c14c26ece9e` |
| `visuels_x/riemann_fr.html` | `13042f53dc2f39873032837c3d1204229ea261e10cb2e2bd710eabd31ca3be38` |
| `visuels_x/riemann_en.html` | `f28e5f46554f23d3ac550919b68485d7d53f4be58ba2f27e9e420c8cfcf70c24` |
| `visuels_x/riemann_ar.html` | `a2a14b8a9e8a343ad939038172c69baed0f61e2aea9694c66b572b1a9b0376f9` |
| `visuels_x/riemann_fr.png` | `0b1395d75ac2b130ebcdd8dc2b686d550feee04cc979ccdcd7925adbb0c2cc37` |
| `visuels_x/riemann_en.png` | `0bb15abae81251ccb10550d8f9aae0d192e0424ea68d86cd0287477a77578558` |
| `visuels_x/riemann_ar.png` | `3c2047741ac462c8ace0f972b630e7f43a12b72b0188e586ca27cdd12596142b` |

Ce dossier ne contient pas sa propre empreinte (circularité évitée).

## 9. Conclusion

Le projet détient quatre choses concrètes et vérifiables :

1. une vérification locale `t ≤ 50` à deux principes, écart 0, recoupée le 2026-10-28 ;
2. un certificat borné `T* = 10⁴` cohérent sur 10 142 zéros, avec ses limites déclarées ;
3. les preuves analytiques classiques des **murs** `σ = 0` et `σ = 1` ;
4. une chaîne de publication honnête (page FR/EN/AR, posts X, cartes, empreintes).

Il ne détient **aucune preuve analytique de l'hypothèse de Riemann**, et aucun calcul fini ne peut en tenir lieu. Toute communication doit conserver la formulation : **murs démontrés, intérieur ouvert**.
