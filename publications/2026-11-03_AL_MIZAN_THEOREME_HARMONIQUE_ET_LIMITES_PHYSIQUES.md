# Al-Mizan — Théorème harmonique des deux pôles, calculs et statut scientifique

**Version publique : 1.0 — 3 novembre 2026**  
**Auteur revendiqué du projet Al-Mizan : Ahmed EL BAHLOUL (GitHub : Loulbak78920)**  
**Dépôt :** https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN

> **Objet de l'archive.** Documenter publiquement, à la date du commit GitHub, l'état précis des propositions, calculs et démonstrations d'Al-Mizan. Cette publication établit une trace de divulgation datée ; elle ne constitue ni une validation scientifique de l'universalité, ni une certification juridique incontestable de paternité. Les équations mathématiques standard et les lois physiques connues ne sont pas revendiquées comme des inventions originales.

## 1. Deux pôles et équilibre

On considère les valeurs initiales proposées :

```text
Q_K(0) = -2304
Q_J(0) = +1536
q(0) = 768 (-3, 2)^T
```

Avec `v=(-3,2)^T`, `w=(2,3)^T`, on a `v·w=0` et `||v||²=||w||²=13`. Toute configuration `q=(Q_K,Q_J)^T` admet une décomposition unique :

```text
q = A v + B w
A = (-3 Q_K + 2 Q_J)/13
B = ( 2 Q_K + 3 Q_J)/13
R = 2 Q_K + 3 Q_J = 13 B
```

La compensation `R=0` équivaut exactement à `B=0`. Le rapport initial `Q_J/Q_K=-2/3` découle des nombres initiaux choisis ; son caractère physiquement nécessaire n'est pas démontré.

## 2. Théorème harmonique conditionnel

**Hypothèses.** Les fonctions réelles `gamma(t)` et `omega(t)` sont continues ; `A,B` satisfont :

```text
A' = -gamma(t) A - omega(t) B
B' =  omega(t) A - gamma(t) B
Z = A + i B
Z' = (-gamma(t) + i omega(t)) Z
```

**Solution exacte**, avec `Z(0)=768` :

```text
Gamma(t) = integral_0^t gamma(s) ds
Phi(t)   = integral_0^t omega(s) ds
Z(t)     = 768 exp(-Gamma(t)) exp(i Phi(t))
A(t)     = 768 exp(-Gamma(t)) cos(Phi(t))
B(t)     = 768 exp(-Gamma(t)) sin(Phi(t))
Q_K(t)   = 768 exp(-Gamma(t)) [-3 cos(Phi(t)) + 2 sin(Phi(t))]
Q_J(t)   = 768 exp(-Gamma(t)) [ 2 cos(Phi(t)) + 3 sin(Phi(t))]
R(t)     = 9984 exp(-Gamma(t)) sin(Phi(t))
```

**Preuve.** La dérivée de `Z(t)` est `(-gamma+i omega)Z`. L'orthogonalité de `v,w` donne `||q||²=13(A²+B²)`. Pour `Z(0) != 0` et tout temps fini, l'exponentielle ne s'annule pas. Par conséquent :

```text
E = A²+B²
E' = -2 gamma(t) E
M = q q^T
det(M) = 0
rank(M) = 1
trace(M) = ||q||² = 13 E
R(t)=0  <=>  Phi(t) belongs to pi*Z
```

La dernière équivalence suppose l'état initial réel positif ci-dessus. Si `gamma>0` constant, le centre `q=0` est approché asymptotiquement mais n'est jamais atteint en temps fini depuis un état initial non nul. Si `gamma<0`, l'amplitude croît.

**Statut :** théorème démontré *sous les hypothèses de l'équation différentielle*, non preuve que la nature obéit à cette équation.

## 3. Universalité de représentation et limite de prédiction

Pour toute amplitude différentiable `a(t)>0` et toute phase différentiable `phi(t)`, la définition `Z(t)=a(t)exp(i phi(t))` vérifie identiquement :

```text
Z' = (-gamma + i omega) Z
gamma = -a'/a
omega = phi'
```

Cette identité est générale, mais **n'est pas prédictive** lorsque `gamma` et `omega` sont simplement recalculées à partir de la trajectoire déjà observée. Une loi physique exige qu'elles soient dérivées indépendamment d'un mécanisme testable.

## 4. Comparaison avec la mécanique Soleil–Terre–Lune

Dans le modèle gravitationnel newtonien isolé à trois corps :

```text
r_i'' = G sum_(j != i) m_j (r_j-r_i)/||r_j-r_i||³
E_grav = sum_i (m_i/2)||r_i'||² - G sum_(i<j) m_i m_j / r_ij
dE_grav/dt = 0
```

Le modèle harmonique impose `E'=-2 gamma E` pour son amplitude quadratique `E`. On ne peut identifier cette quantité à l'énergie gravitationnelle totale isolée sans contraintes supplémentaires ; une telle identification avec facteur constant et énergie non nulle imposerait `gamma=0`.

À titre de test d'une interprétation possible des pôles comme accélérations gravitationnelles subies par la Terre :

```text
g_S = G m_S / r_ST² ≈ 0.00593 m/s²
g_L = G m_L / r_TL² ≈ 0.0000332 m/s²
g_L/g_S ≈ 0.0056 != 2/3
```

Cette interprétation simple ne reproduit donc pas le rapport 2:3. Les chiffres sont des ordres de grandeur fondés sur distances moyennes, non une analyse de toutes les interprétations possibles.

Une phase astronomique géocentrique peut être définie par `phi_STL=longitude(Lune)-longitude(Soleil)`. L'hypothèse `omega=phi_STL'` ne devient une prédiction nouvelle que si les variables physiques et leur évolution sont définies indépendamment de cette phase.

## 5. Nombre 13 et centre F0

Le nombre `13=3²+2²` est démontré comme norme quadratique de la base choisie. Un découpage de la phase en 13 secteurs `2 pi k/13` est possible, mais ce découpage n'est pas imposé par la gravitation. Une année tropique contient environ `365.2422/29.5306 ≈ 12.3683` lunaisons synodiques moyennes, pas exactement 13.

La valeur `F0=0.122` intervient comme paramètre de la matrice initiale ; aucune dérivation physique indépendante de cette valeur n'est établie ici.

## 6. Matrice de contraction 4×4 : distinction des modèles

La matrice de travail est `C=S U`, avec :

```text
S = [[.122, .0305, .061, .0152],
     [.0305, .5005, .021, .042],
     [.061, .021, .6015, .0105],
     [.0152, .042, .0105, .6225]]
a = (sqrt(5)-1)/2 ; b = sqrt(2)-1
U = [[a, b, a*b, .122],
     [b, a, .5005, a*b],
     [a*b, .5005, .6015, b],
     [.122, a*b, b, .6225]]
```

Les calculs numériques précédents donnent `||C||_2 ≈ 0.97106244 < 1` et `det(C) ≈ 0.000233358 != 0`. Donc `||C^n x||_2 <= ||C||_2^n ||x||_2`, ce qui démontre la convergence vers zéro, sans atteinte finie depuis un état non nul. **Attention :** cette dynamique linéaire 4D n'est pas démontrée équivalente à la dynamique 2D de `q`. En particulier, elle ne préserve pas en général la symétrie et le rang un d'une vectorisation de `q q^T`.

## 7. Statut des revendications et protocole de réfutation

**Démontré :** décomposition orthogonale, identité du résidu, solution de l'ODE postulée, évolution quadratique, propriété de rang un, contraction de `C` pour la matrice numérique spécifiée.

**Non démontré :** universalité physique, origine naturelle des coefficients 2 et 3, valeur universelle de F0, nécessité astronomique de 13 états, identification de `C` avec l'évolution des pôles.

Pour progresser scientifiquement :
1. Définir `Q_K,Q_J` comme observables mesurables avec unités, sans y incorporer d'avance le rapport 2:3.
2. Déduire `gamma,omega` de principes physiques indépendants, sans les ajuster à la trajectoire à expliquer.
3. Prédire des événements ou valeurs numériques avant leur observation, avec incertitudes et conditions de réfutation.
4. Confronter ces prédictions à des données indépendantes et à des modèles de référence.

## 8. Déclaration d'antériorité documentaire

Le titulaire du compte GitHub `Loulbak78920` publie ici, sous la revendication d'auteur du projet Al-Mizan indiquée en tête, cette version textuelle datée. Le **SHA du commit GitHub**, son URL et l'historique du dépôt permettent de référencer le contenu effectivement rendu public. Les dates de commits ne sont pas des horodatages juridiquement certifiés. Pour renforcer la preuve d'existence à date certaine en France, conserver ce fichier exact et son empreinte SHA-256, puis déposer le même contenu via le service **e-Soleau de l'INPI**, en conservant le récépissé. Ce dépôt ne prouve pas à lui seul la nouveauté scientifique ni n'accorde un monopole sur des idées ou formules mathématiques.

**Note de méthode :** cette publication archive une contribution théorique en cours d'évaluation ; elle ne prétend pas avoir résolu la question d'une « loi universelle de la nature ».
