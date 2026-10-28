# Pack de publication X — Hypothèse de Riemann (FR / EN / AR)

Version du 2026-10-28. Pack destiné à une publication manuelle sur X.
Chaque post tient sous 280 caractères (URL comptée pour 23).

## Règles de publication

1. Ne jamais écrire « preuve » ou « résolue » pour l'hypothèse elle-même.
2. Séparer trois statuts : **DÉMONTRÉ** (théorèmes publiés), **CALCULÉ** (vérification numérique reproductible), **OUVERT** (hypothèse de Riemann).
3. Nommer l'unité : **hauteur** `T` (ordonnée γ) ou **nombre de zéros** `N(T)`. 10⁹ zéros ≠ hauteur 10⁹.
4. Aucune revendication d'antériorité ni de prix Clay.
5. Lier la page publique de la langue du post.

## Résultats immuables (source des posts)

| Fait | Statut | Source |
| :--- | :--- | :--- |
| Aucun zéro de ζ sur le mur σ = 1 | DÉMONTRÉ | Hadamard et de la Vallée Poussin, 1896 |
| Aucun zéro sur le mur σ = 0 | DÉMONTRÉ | équation fonctionnelle ξ(s) = ξ(1−s) |
| Région sans zéros σ ≥ 1 − c/log t | DÉMONTRÉ | de la Vallée Poussin, 1896 |
| Une infinité de zéros sur σ = ½ | DÉMONTRÉ | Hardy, 1914 |
| Au moins 2/5 des zéros sur σ = ½ | DÉMONTRÉ | Conrey, 1989 (≈ 41,7 % aujourd'hui) |
| Hauteur 3×10¹² vérifiée numériquement | CALCUL PUBLIÉ | Platt–Trudgian, 2021 |
| Projet : t ≤ 50, deux méthodes, écart 0 | CALCUL REPRODUCTIBLE | `resultats/oeuvre_universelle/riemann_comptage.json` |
| Projet : cohérence à T\* = 10 000, 10 142 zéros, écart 0 | CALCUL INTERNE (même noyau ζ) | `resultats/oeuvre_universelle/riemann_certificat_T1e4.json` |
| Tous les zéros sur σ = ½ (RH) | OUVERT | — |

Chiffres vérifiés dans les artefacts :

- `t = 20, 30, 40, 50` → comptage par principe de l'argument `1, 3, 6, 10` ; zéros sur la droite `1, 3, 6, 10` ; écart max `0`.
- `T* = 10 000` → `10 142` zéros sur la droite, `N(chemin) = 10 142`, écart `0`, résidu max `1,83×10⁻⁹`, espacement minimal `0,0377`.
- `N(T)` lissé n'est pas le comptage exact : à `T = 50`, `N(50) ≈ 9,42` alors que le projet compte 10 zéros.

Empreintes SHA-256 des sources (à citer pour l'immuabilité) :

| Fichier | SHA-256 |
| :--- | :--- |
| `riemann_verification.py` | `3445b6a18745b9c9f12f363f6d95eaa0ea8adc4a3fa164552a68705f7c614ae5` |
| `riemann_comptage.json` | `a9a19af327187570277e655dfd8adee532b1436e0a23e88fbdfe1102808f28a1` |
| `riemann_certificat_T1e4.py` | `646d7493a56d041a4134e590a6c443fe396f0a6386ac72056821d68771cb65d4` |
| `riemann_certificat_T1e4.json` | `d4e4bd5246d0e8ca2eff8d2d2bde6b494e139bf50febb6730061c319934b897b` |
| `hypothese_riemann.html` | `d052616c39fc0d10902068664aab1082c630927482a140aa993863738d68e770` |

---

## FR — Fil de 4 posts

### FR-1 (1/4)
Hypothèse de Riemann : murs démontrés, intérieur ouvert. 1) Aucun zéro de ζ sur σ=1 (Hadamard–de la Vallée Poussin, 1896). 2) Aucun sur σ=0 (équation fonctionnelle). 3) Les zéros non triviaux sont donc dans 0<σ<1. Qu'ils soient tous sur σ=½ reste ouvert. al-mizan.world/riemann

### FR-2 (2/4)
Pourquoi σ=1 est sans zéro : 3+4cosθ+cos2θ = 2(1+cosθ)² ≥ 0 ⟹ |ζ(σ)³ζ(σ+it)⁴ζ(σ+2it)| ≥ 1 pour σ>1. Si ζ(1+it)=0, le membre de gauche → 0 quand σ→1⁺ : contradiction. C'est l'équivalent analytique du théorème des nombres premiers.

### FR-3 (3/4)
Aussi établis : région sans zéro σ ≥ 1−c/log t (de la Vallée Poussin) ; une infinité de zéros sur σ=½ (Hardy 1914) ; au moins 2/5 des zéros sur la droite (Conrey 1989, ≈41,7 % aujourd'hui). Aucun de ces résultats ne prouve l'hypothèse.

### FR-4 (4/4)
Numérique ≠ preuve. La page vérifie t≤50 par deux méthodes (comptages 1,3,6,10 ; écart 0) et publie un certificat de cohérence à T=10⁴ (10 142 zéros ; écart 0). Aucune revendication au-delà. Méthodes et limites : al-mizan.world/riemann #RiemannHypothesis #maths

## EN — Thread of 4 posts

### EN-1 (1/4)
Riemann hypothesis: what is proven, what is not. 1) ζ has no zeros on the wall σ=1 (Hadamard–de la Vallée Poussin, 1896). 2) None on σ=0 (functional equation). 3) So all nontrivial zeros lie inside 0<σ<1. Whether all lie on σ=½ remains OPEN. al-mizan.world/riemann/en

### EN-2 (2/4)
Why σ=1 is zero-free: 3+4cosθ+cos2θ = 2(1+cosθ)² ≥ 0 ⟹ |ζ(σ)³ζ(σ+it)⁴ζ(σ+2it)| ≥ 1 for σ>1. If ζ(1+it)=0 the left side → 0 as σ→1⁺: contradiction. This is the analytic equivalent of the prime number theorem.

### EN-3 (3/4)
Also established: zero-free region σ ≥ 1−c/log t (de la Vallée Poussin); infinitely many zeros on σ=½ (Hardy 1914); at least 2/5 of the zeros on the line (Conrey 1989, ≈41.7% today). None of these proves the hypothesis.

### EN-4 (4/4)
Numerics ≠ proof. The page checks t≤50 by two methods (counts 1,3,6,10; gap 0) and a coherence certificate at T=10⁴ (10,142 zeros; gap 0). No claim beyond that. Methods and limits: al-mizan.world/riemann/en #RiemannHypothesis #math

## AR — سلسلة من 4 منشورات

### AR-1 (1/4)
فرضية ريمان: ما هو مُبرهَن وما ليس مُبرهَنًا. ١) لا أصفار لـζ على الحافة σ=1 (هادامار ودي لا فالي پوسان، 1896). ٢) ولا أصفار على σ=0 (بالمعادلة الدالية). ٣) إذن كل الأصفار غير البديهية داخل 0<σ<1. أما أن تكون كلها على σ=½ فما زال مفتوحًا. al-mizan.world/riemann/ar

### AR-2 (2/4)
لماذا σ=1 خالٍ من الأصفار: 3+4cosθ+cos2θ = 2(1+cosθ)² ≥ 0 ⟹ |ζ(σ)³ζ(σ+it)⁴ζ(σ+2it)| ≥ 1 عندما σ>1. لو كان ζ(1+it)=0 لانتهى الطرف الأيسر إلى 0 عند σ→1⁺. تناقض. وهذا مكافئ لنظرية الأعداد الأولية.

### AR-3 (3/4)
ومُبرهَن أيضًا: منطقة خالية من الأصفار σ ≥ 1−c/log t (دي لا فالي پوسان)؛ عدد لا نهائي من الأصفار على σ=½ (هاردي 1914)؛ 2/5 من الأصفار على الأقل على الخط (كونري 1989، ≈41.7% اليوم). لا شيء من هذا يُبرهن الفرضية.

### AR-4 (4/4)
الحساب العددي ليس برهانًا. تتحقق الصفحة من t≤50 بطريقتين (العدّ 1,3,6,10؛ الفرق 0) وتنشر شهادة اتساق عند T=10⁴ (10,142 صفرًا؛ الفرق 0). لا ادعاء بعد ذلك. الطرائق والحدود: al-mizan.world/riemann/ar #RiemannHypothesis #رياضيات

## Hashtags par langue

- FR : `#RiemannHypothesis #maths #AlMizan`
- EN : `#RiemannHypothesis #math #AlMizan`
- AR : `#RiemannHypothesis #رياضيات #AlMizan`

## Visuels 16:9 (3200 × 1800)

Cartes générées par `oeuvre_universelle/generer_visuels_x_riemann.py`, rendues par Chrome headless.
Chaque carte affiche : murs σ = 0 et σ = 1 sans zéros (démontré), bande 0 < σ < 1, et l'ouverture sur σ = ½.

| Langue | Fichier | SHA-256 |
| :--- | :--- | :--- |
| FR | `resultats/oeuvre_universelle/visuels_x/riemann_fr.png` | `0b1395d75ac2b130ebcdd8dc2b686d550feee04cc979ccdcd7925adbb0c2cc37` |
| EN | `resultats/oeuvre_universelle/visuels_x/riemann_en.png` | `0bb15abae81251ccb10550d8f9aae0d192e0424ea68d86cd0287477a77578558` |
| AR | `resultats/oeuvre_universelle/visuels_x/riemann_ar.png` | `3c2047741ac462c8ace0f972b630e7f43a12b72b0188e586ca27cdd12596142b` |

Textes alternatifs (accessibilité X) :

- FR : « Carte Riemann : les murs σ=0 et σ=1 sont sans zéros (démontré) ; les zéros non triviaux sont dans la bande 0<σ<1 ; leur position sur σ=½ reste ouverte. »
- EN : « Riemann card: the walls σ=0 and σ=1 are zero-free (proven); all nontrivial zeros lie in 0<σ<1; whether all lie on σ=½ remains open. »
- AR : « بطاقة ريمان: الحافتان σ=0 وσ=1 بلا أصفار (مُبرهَن)؛ الأصفار غير البديهية داخل الشريط 0<σ<1؛ أما موقعها على σ=½ فما زال مفتوحًا. »

## Note de circularité

Ce fichier ne contient pas sa propre empreinte. Les empreintes listées couvrent les sources citées, pas ce pack.
