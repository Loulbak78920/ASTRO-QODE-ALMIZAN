# Certificat `RH(T*)` et antériorité publiée

Statuts utilisés : **vérifié** (recalculé ou relu sur disque le 2026-10-28),
**sourcé** (vérifié par source externe citée), **méthode** (issue de la session
source, non exécutée à cette échelle), **non vérifié**.

## 1. Énoncé borné

> `RH(T*)` : pour tout zéro `ρ = β + iγ` de `ζ` avec `0 < γ ≤ T*`, on a `β = 1/2`
> et le zéro est simple.

Ce que `RH(T*)` établit : rien au-delà de `T*`. Ce qu'elle n'établit pas :
l'hypothèse de Riemann pour l'infinité des zéros, ni l'éligibilité au prix Clay.
Aucune hauteur finie, `10`, `10⁹` ou `10¹³`, n'implique l'infinité.

## 2. Certificat en trois parties — **méthode**

```text
(1)  N(T*) = 1 + θ(T*)/π + (1/π)·Im ln ζ(1/2 + iT*)
     θ(t)  = Im ln Γ(1/4 + it/2) − (t/2)·ln π
     [principe de l'argument, borné au contour]

(2)  Z(t) = e^{iθ(t)}·ζ(1/2 + it) change de signe exactement une fois
     sur chaque intervalle de Gram ]g_n, g_n+1[  (règle de Rosser vérifiée)

(3)  nombre de changements de signe = N(T*)
     ⇒ aucun zéro hors de la droite, aucun zéro multiple sous T*
```

Les étapes (1) et (3) exigent une **arithmétique d'intervalle** avec bornes
d'erreur explicites. Un calcul `mpmath` à 20 chiffres décimaux est exploratoire :
il ne certifie pas. La règle de Rosser doit être vérifiée, pas supposée.

Cette structure n'a pas été exécutée jusqu'à `T = 10⁴` dans la session source :
le tour suivant de l'utilisateur a demandé les en-têtes SPDX et la licence AGPL.
La présenter comme « déjà calculée » serait faux.

## 3. Modèle de coût — **vérifié** (calcul local)

Pour `T > 0` :

```text
N(T) ≈ (T/2π)·(ln(T/2π) − 1) + 7/8
```

C'est le comptage **lissé** de Riemann–von Mangoldt, sans le terme `S(T)`.
Il ne donne pas le nombre exact de zéros sous `T` : `N(50) ≈ 9,42` alors que le
projet trouve `10` zéros sous `t = 50` (voir le JSON du projet, section
`comptage`). Toujours distinguer :

- **hauteur** `T` : borne supérieure de la partie imaginaire ;
- **nombre de zéros** `N(T)` : comptage, lissé ou exact.

Inversion numérique (script `scripts/qualifier_portee.py`, calcul du 2026-10-28) :

| zéros visés | hauteur `T*` | évaluations de `Z(t)` (ordre) |
| ---: | ---: | ---: |
| 10 | 51,73 | 10 |
| 1 000 | 1 420,1 | 1 000 |
| 10 000 | 9 878,1 | 10 000 |
| 1 000 000 | 600 270 | 10⁶ |
| 10⁹ | 3,7187×10⁸ | 10⁹ à 10¹⁰ |

Coût par évaluation : la formule de Riemann–Siegel emploie de l'ordre de
`√T` termes, donc le travail croît plus vite que le nombre d'évaluations.
L'ordre de grandeur « décennies à un siècle » pour `10⁹` en Python/`mpmath` est
une **inférence de mise à l'échelle, non une mesure**. Aucun banc d'essai n'a été
exécuté dans la session source.

## 4. Antériorité publiée — **sourcé** (recherche du 2026-10-28)

| Source | Unité annoncée | Valeur | Équivalent | Remarque |
| :--- | :--- | ---: | :--- | :--- |
| van de Lune, te Riele, Winter (1986) | nombre de zéros | 1,5×10⁹ | hauteur ≈ 5,45×10⁸ | premiers zéros vérifiés |
| Gourdon (2004) | nombre de zéros | 10¹³ | hauteur ≈ 2,45×10¹² | calcul non certifié en intervalle |
| Platt–Trudgian (2021) | **hauteur** `T` | 3×10¹² | ≈ 1,24×10¹³ zéros | arithmétique d'intervalle, résultat rigoureux |

Piège de lecture : la colonne « valeur » ne mélange pas les unités. Un objectif
de `10⁹` **zéros** est déjà couvert par 1986 ; une hauteur de `3×10¹²` couvre
beaucoup plus que `10⁹` zéros. Comparer uniquement après conversion.

À `10⁹` zéros, la seule qualification honnête est **reproduction**, sans
antériorité ni nouveauté. L'antériorité mathématique s'établit par une preuve,
pas par un calcul plus long.

Sources :

- Platt & Trudgian, *The Riemann hypothesis is true up to 3·10¹²*,
  Bull. London Math. Soc. 53 (2021), <https://arxiv.org/abs/2004.09765> et
  <https://londmathsoc.onlinelibrary.wiley.com/doi/10.1112/blms.12460>.
- van de Lune, te Riele & Winter, *On the zeros of the Riemann zeta function in
  the critical strip. IV*, <https://ir.cwi.nl/pub/1869/1869D.pdf> ; référence
  bibliographique <https://t5k.org/references/refs.cgi?author=Lune>.
- Gourdon, *The 10¹³ first zeros of the Riemann zeta function* (2004),
  <http://numbers.computation.free.fr/Constants/Miscellaneous/zetazeroscompute.html>.

## 5. Échelle livrable

| Livrable | Zéros | Statut |
| :--- | ---: | :--- |
| `T = 10³` | ≈ 649 | reproductible en minutes, sans valeur d'antériorité |
| `T = 10⁴` | ≈ 10 143 | reproductible en dizaines de minutes, sans valeur d'antériorité |
| `T = 10⁶` | ≈ 1,75×10⁶ | jours de calcul, toujours sans antériorité |
| `T = 3,7×10⁸` | 10⁹ | décennies estimées, déjà couvert depuis 1986 |

Tout artefact livré doit conserver `hypothese_demontree: false`, une `portee`
explicite et une liste `limites`. Un titre « preuve » ou « vrai jusqu'à N » est
interdit, même si le calcul est exact sur sa plage.
