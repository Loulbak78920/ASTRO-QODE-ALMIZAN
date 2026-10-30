# Règlement des dettes et redistribution — équations, chemins d'explication et résultats

Version 1.0 — 30 octobre 2026
Corpus normatif : Coran 2:275-279, 2:280, 2:282, 2:245, 2:261, 9:60, 4:11-12, 5:8, 16:90, 49:10.
Module : [`reglement_dettes_redistribution.py`](reglement_dettes_redistribution.py)
Générateur de pages : [`generer_page_reglement_dettes_redistribution.py`](generer_page_reglement_dettes_redistribution.py)
Tests : [`../tests/test_reglement_dettes_redistribution.py`](../tests/test_reglement_dettes_redistribution.py)
Pages publiques : `/reglement-dettes-redistribution`, `/en`, `/ar` · JSON : `GET /reglement-dettes-redistribution.json`

---

## 1. Statut honnête

| Élément | Statut |
| :--- | :--- |
| Règles coraniques citées (riba, report, qard hasan, zakat, succession, justice, réconciliation) | **Référencées par verset et paraphrasées** — aucune traduction n'est présentée comme officielle |
| Constantes de zakat et de nisab (1/40 ; 85 g d'or ; 595 g d'argent) | **Reprises du moteur du dossier** (`moteur_economie_islamique_mizan.py`) |
| Calculs (13 équations, 13 contrôles) | **Arithmétique exacte reproductible** sur des règles déclarées |
| Scénarios agrégés (capacité, stabilisateur, inégalité, indice) | **Modèles déclarés** — aucune donnée réelle, aucune prévision |
| Parabole des sept épis (2:261) | **Parabole révélée** — ce n'est pas un taux de rendement |
| Succession | **Un cas déclaré** — le module n'est pas un calculateur général (awl, radd exclus) |
| Collecte, transfert ou contrainte réelle | **Aucun** — le module ne détient aucun fonds et ne perçoit aucune zakat |
| Mesure de la justice, de la paix ou de l'abondance | **Aucune** — les indices sont des conventions internes |

La demande initiale porte une exigence de « complétude complète ». Le module ne
la traite pas comme une propriété du monde : il montre la **complétude du
protocole déclaré** (8/8 catégories coraniques, 4/4 piliers reliés, conservation
exacte du flux). Aucun système ne peut garantir la justice, la paix ou
l'abondance à l'échelle mondiale ; prétendre le contraire serait un dol.

---

## 2. La logique du dossier, appliquée

Le dossier traite chaque thème selon le même patron :

1. **Un sujet → un module** qui pose les équations et les résout.
2. **Chaque équation porte un chemin** : fonction du module → contrôle numérique.
3. **Chaque résultat porte un statut** : `OPÉRATIONNEL`, `SIMULÉ` ou `SPÉCIFIÉ`.
4. **Un artefact JSON** sert de source unique aux pages FR/EN/AR.
5. **Une page trilingue** reprend les mêmes chiffres, sans variante locale.
6. **Des ponts explicites** relient le thème aux quatre piliers du dossier, avec
   leur limite déclarée.

Règle de bride : `MIZAN = 0.6225` ne s'applique qu'aux grandeurs sans dimension.
Ici, les grandeurs sont des montants (€), des taux, des fractions exactes ou des
indices bornés dans `[0,1]`. La bride n'est appliquée qu'à l'indice de justice et
de paix, qui est déjà normalisé par construction.

---

## 3. Les treize équations

| ID | Formule | Résultat | Statut | Chemin d'explication |
| :-- | :--- | :--- | :--- | :--- |
| EQ-01 | `Z = τ·A·1[A ≥ N]` ; `τ = 1/40` ; `N = 595 g Ag` | Z(1 000 €) = 25,000000 € · Z(500 €) = 0 € · N = 517,391304 € | OPÉRATIONNEL | `zakat_legale()` → C01 |
| EQ-02 | Coran 9:60 : huit catégories ; `Σ s_k = 1` | 8 catégories · Σ = 1 · s_k = 1/8 | SPÉCIFIÉ | `categories_coraniques()` → C02 |
| EQ-03 | `D' = D − min(C,D) − F` ; `0 ≤ F ≤ D − min(C,D)` | reste 500 € · remise totale ⇒ 0 € · remise excessive plafonnée à 700 € | OPÉRATIONNEL | `reglement_insolvabilite()` → C03 |
| EQ-04 | Qard `R = C` ; riba `R = C(1+r)^n` | qard 10 000 € · riba 5 %/10 ans : surcoût 6 288,946268 € | OPÉRATIONNEL | `qard_hasan_vs_riba()` → C04 |
| EQ-05 | `C = max(0, Y−E)` ; `durée = ⌈D/C⌉` | capacité 800 €/an · 5 ans · revenu ≤ dépenses ⇒ report | SIMULÉ | `capacite_remboursement()` → C05 |
| EQ-06 | conjoint 1/8 · père 1/6 · mère 1/6 · reste 13/24 · fils:fille = 2:1 | Σ = 1 · ratio 2 · conjoint 9 000 € | OPÉRATIONNEL | `succession_fixes()` → C06 |
| EQ-07 | `I_Z = τ·W` ; rotation `1/τ` | 25 000 000 000 € · rotation 40 ans | SIMULÉ | `zakat_stabilisateur()` → C07 |
| EQ-08 | `G = (a−b)/(2(a+b))` ; `G' = G − t/(a+b)` | 0,250000 → 0,125000 (t=25) → 0,000000 (t=50) | SIMULÉ | `redistribution_inegalite()` → C08 |
| EQ-09 | `7 × 100 = 700` ; flux `700·Z` | 700 · 17 500 € pour Z = 25 € | SPÉCIFIÉ | `parabole_abondance()` → C09 |
| EQ-10 | `W_n = W_0(1−τ)^n` ; `n½ = ln(1/2)/ln(1−τ)` | demi-vie 27,377851 ans · W(40)/W0 = 0,363232 | OPÉRATIONNEL | `continuite_zakat()` → C10 |
| EQ-11 | `Z = Σ A_k + R` | 25 € = 22,5 € + 2,5 € | OPÉRATIONNEL | `conservation_flux()` → C11 |
| EQ-12 | `J = 1−T` ; `T = 0,40 t_riba + 0,20 t_partage + 0,20 t_zakat + 0,20 t_adossement` | halal J = 1 · usuraire T = 0,68, J = 0,32 | SPÉCIFIÉ | `indice_justice_paix()` → C12 |
| EQ-13 | P1↔mandat · P2↔écrit · P3↔registre sans clé · P4↔audit et recours | 4/4 piliers · K = 1,000000 | SPÉCIFIÉ | `ponts_quatre_piliers()` → C13 |

---

## 4. Dérivations

### 4.1 Zakat légale (EQ-01)

La zakat est un prélèvement annuel de **1/40 (2,5 %)** sur la richesse qui
dépasse le **nisab**, après une année lunaire de possession. Le nisab retenu par
le moteur du dossier est de **595 g d'argent** (ou 85 g d'or), converti aux
constantes d'étalonnage A097/A105 :

```text
N_Ag = 595 g × (1 000 / 1 150) €/g = 517,391304… €
N_Au = 85 g × (1 000 / 14,5) €/g   = 5 862,068966… €
Z    = τ·A  si A ≥ N,  sinon 0,  τ = 0,025
```

Pour un patrimoine de 1 000 €, `Z = 25 €`. Pour 500 €, `Z = 0` : le seuil
protège les petits patrimoines. La part par catégorie (1/8 de Z) vaut 3,125 €
pour l'exemple.

**Limite** : les seuils utilisent l'étalonnage du dossier, pas les cours réels
en temps réel. Le module ne vérifie ni la possession pendant une année lunaire
ni l'origine licite du patrimoine.

### 4.2 Les huit catégories (EQ-02)

Le verset 9:60 énumère huit catégories de bénéficiaires : les pauvres, les
nécessiteux, ceux qui ont la charge de la collecte, ceux dont les cœurs sont à
rallier, l'affranchissement, les endettés, la cause de Dieu et le voyageur en
détresse. Le Coran fixe les **catégories**, pas des parts égales. Le module
retient `s_k = 1/8` comme **convention de calcul déclarée**, avec
`Σ s_k = 1` et `s_k ≥ 0`.

**Limite** : la répartition effective relève de l'autorité compétente et du
contexte ; le module ne prétend pas que huit parts égales soient une prescription.

### 4.3 Insolvabilité, report et remise (EQ-03)

Le verset 2:280 demande de **reporter** l'échéance du débiteur en difficulté
jusqu'à ce qu'il retrouve de l'aisance, et déclare meilleure la **remise** de la
dette. Le module formalise :

```text
versé          = min(C, D)
reste avant    = D − versé
remise utile   = min(max(F,0), reste avant)
reste final    = reste avant − remise utile ≥ 0
```

Pour `D = 1 000`, `C = 300`, `F = 200` : versé 300, reste 500. Pour `F = 700`,
le reste est nul. Une remise demandée de 1 000 est **plafonnée** à 700 : on ne
remet pas plus que ce qui reste dû.

**Limite** : le module ne juge ni la bonne foi du débiteur ni celle du créancier ;
il ne produit aucune contrainte d'exécution.

### 4.4 Qard hasan contre riba (EQ-04)

Le prêt d'honneur (2:245) restitue le capital sans surplus : `R = C`. Le prêt à
intérêt compose : `R = C(1+r)^n`. Pour 10 000 € à 5 % sur 10 ans, le surcoût est :

```text
10 000 × (1,05¹⁰ − 1) = 6 288,946268… €
```

Le moteur du dossier fixe `TAUX_RIBA_MAXIMUM_AUTORISE = 0`. Le module ne calcule
pas un « intérêt halal » : il montre l'écart entre les deux régimes.

**Limite** : le calcul ne couvre ni l'inflation, ni les frais de service réels,
ni les contrats participatifs (mudaraba, musharaka, murabaha), traités par le
moteur d'économie islamique.

### 4.5 Capacité de remboursement (EQ-05)

Avant de fixer un versement, il faut mesurer ce que le débiteur peut réellement
consacrer après ses **besoins essentiels** :

```text
C = max(0, Y − E)
versement = min(C, D)
durée = ⌈D/C⌉ si C > 0
```

Pour `Y = 3 000`, `E = 2 200`, `D = 4 000` : `C = 800`, versement 800, durée
5 ans. Pour `Y = 2 000`, `E = 2 200` : `C = 0`, donc report (2:280), pas de
contrainte.

**Limite** : la frontière entre besoins essentiels et dépenses discrétionnaires
est une convention sociale ; le module la prend comme paramètre déclaré.

### 4.6 Succession, parts fixes (EQ-06)

Le verset 4:11 fixe les parts du conjoint, des parents et des enfants. Le cas
déclaré est : conjoint, père, mère, un fils, une fille, après paiement des
dettes. En fractions exactes :

```text
conjoint = 1/8
père     = 1/6
mère     = 1/6
reste    = 1 − (1/8 + 1/6 + 1/6) = 13/24
fils     = (2/3)·(13/24) = 13/36
fille    = (1/3)·(13/24) = 13/72
Σ        = 1
```

Pour une masse de 72 000 € : conjoint 9 000 €, père 12 000 €, mère 12 000 €,
fils 26 000 €, fille 13 000 €. Le rapport fils/fille vaut exactement 2.

**Limite** : cas unique. Le module ne traite ni `awl` (dépassement de la somme
des parts), ni `radd` (retour du surplus), ni les autres configurations
(grands-parents, frères et sœurs, épouses multiples, testament). Un calculateur
successoral complet exigerait un moteur distinct et une validation savante.

### 4.7 Zakat agrégée (EQ-07)

À l'échelle d'une masse `W`, l'injection annuelle est `I_Z = τ·W`. Le temps de
rotation `1/τ = 40 ans` : à flux constant et sans croissance, la zakat fait
circuler l'équivalent de la masse en quarante ans. Pour `W = 10¹² €`,
`I_Z = 25 × 10⁹ €`.

**Limite** : modèle agrégé, sans comportement des agents, sans fuite vers
l'épargne, sans croissance. Ce n'est pas une prévision macroéconomique.

### 4.8 Redistribution et inégalité (EQ-08)

Modèle-jouet à deux groupes de même taille, revenus `a > b`, revenu total
constant. Le Gini vaut :

```text
G = (a − b) / (2(a + b))
```

Un transfert `t` du groupe haut vers le groupe bas donne :

```text
G' = (a − b − 2t) / (2(a + b)) = G − t/(a + b)
```

Pour `a = 150`, `b = 50` : `G = 0,25`. Avec `t = 25`, `G' = 0,125`. Avec
`t = 50 = (a−b)/2`, `G' = 0`.

**Limite** : deux groupes, même taille, revenu total constant. Ce n'est ni une
mesure de la distribution réelle ni une prévision ; c'est une identité de
modèle.

### 4.9 Parabole de l'abondance (EQ-09)

Le verset 2:261 compare la dépense dans la voie de Dieu à un grain qui produit
sept épis, chaque épi portant cent grains : `7 × 100 = 700`. Le module pose un
flux illustratif `700·Z`, soit 17 500 € pour `Z = 25 €`.

**Limite** : c'est une **parabole révélée**, pas un taux de rendement, pas une
promesse de multiplication financière. Le module ne l'utilise dans aucun calcul
de solvabilité ou de prévision.

### 4.10 Continuité du flux (EQ-10)

Si un stock `W_0` est soumis chaque année au taux `τ` sans croissance, le stock
restant après `n` années est `W_n = W_0(1−τ)^n`. La demi-vie est :

```text
n½ = ln(1/2) / ln(1−τ) = 27,377851… ans
W_40/W_0 = 0,975⁴⁰ = 0,363232…
```

La continuité ne vient pas de l'accumulation, mais du **flux** : un stock non
renouvelé est continuellement réduit par la zakat.

**Limite** : modèle sans croissance, sans réinvestissement, sans inflation.

### 4.11 Conservation du flux (EQ-11)

Le circuit déclaré ne perd aucune unité :

```text
R   = ρ·Z
A_k = (1−ρ)·Z/8
Z   = Σ_k A_k + R
```

Pour `Z = 25 €` et `ρ = 0,10` : réserve 2,5 €, distributable 22,5 €, allocation
2,8125 € par catégorie, total 25 €. C'est une identité comptable, pas une
observation.

**Limite** : la réserve est une convention de gouvernance ; le module ne dit pas
quel taux de réserve est juste.

### 4.12 Indice de justice et de paix (EQ-12)

Le dossier dispose déjà d'un indice de tension économique dans
`equations_economie_mondiale_mizan.py` :

```text
T = 0,40·t_riba + 0,20·t_partage + 0,20·t_zakat + 0,20·t_adossement
J = 1 − T
```

Scénario halal pur (`r = 0`, partage 50/50, zakat payée, adossement 100 %) :
`T = 0`, `J = 1`. Scénario usuraire (`r = 5 %`, partage 0, zakat non payée,
adossement 10 %) : `T = 0,68`, `J = 0,32`.

**Limite** : indice **conventionnel** du dossier. Il ne mesure ni la paix
sociale, ni la justice réelle, ni la conformité religieuse d'une personne.

### 4.13 Quatre piliers et complétude du protocole (EQ-13)

Chaque pilier du dossier reçoit un répondant dans le protocole de dette :

| Pilier | Question | Règle de dette | Limite |
| :--- | :--- | :--- | :--- |
| P1 — Identité et mandat | Qui agit, à quel titre ? | parties identifiées, mandat écrit, signature (2:282) | le module ne vérifie pas l'identité réelle |
| P2 — Intégrité et provenance | Ce qui s'exécute est-il ce qui a été signé ? | écriture, témoins, empreinte SHA-256 | l'empreinte prouve le contenu, pas les faits |
| P3 — Confidentialité et maîtrise | Qui peut lire, restaurer, effacer ? | registre accessible, aucune clé privée détenue | aucune garde de fonds |
| P4 — Résilience et preuve | Que reste-t-il après l'attaque ? | journal d'audit, quittance, recours, réconciliation (49:10) | preuve documentaire, pas exécution forcée |

`K = 4/4 = 1,000000` exprime la **complétude du protocole déclaré**, pas la
complétude du monde.

---

## 5. Résultats

```text
équations           13
contrôles           13/13
statuts             6 OPÉRATIONNEL · 3 SIMULÉ · 4 SPÉCIFIÉ
zakat 1 000 €       25,000000 €
nisab argent        517,391304 €
qard vs riba        6 288,946268 € de surcoût (5 % / 10 ans)
succession 72 000 € Σ parts = 1 · fils 26 000 € · fille 13 000 €
demi-vie zakat      27,377851 ans
Gini                0,250000 → 0,125000 → 0,000000
indice usuraire     T = 0,680000 · J = 0,320000
complétude          4/4 piliers · K = 1,000000
```

---

## 6. Code et utilisation

Depuis `ASTRO-Q°ODE_SYSTEME/` :

```bash
PYTHONIOENCODING=utf-8 py -3 oeuvre_universelle/reglement_dettes_redistribution.py
PYTHONIOENCODING=utf-8 py -3 -m unittest tests.test_reglement_dettes_redistribution -v
PYTHONIOENCODING=utf-8 py -3 oeuvre_universelle/generer_page_reglement_dettes_redistribution.py
```

Le module expose `resoudre()` et `verifier(donnees)`. `resoudre()` renvoie
`version`, `source`, `invariants`, `equations`, `controles`, `resume`.
`verifier()` renvoie `True` si les 13 contrôles passent. Le script sort en 1 si
un contrôle échoue.

---

## 7. Intégration au site

| Élément | Valeur |
| :--- | :--- |
| Routes HTML | `/reglement-dettes-redistribution`, `/reglement-dettes-redistribution/`, `/en`, `/ar` |
| JSON public | `/reglement-dettes-redistribution.json` |
| Pages | `web_cloud/reglement_dettes_redistribution.html`, `_en.html`, `_ar.html` |
| Archive | `resultats/oeuvre_universelle/reglement_dettes_redistribution.json` |
| Sitemap | trois `<loc>` (fr, en, ar) |
| Portail | carte `feature-link` tag `ECO-01` |
| Tests du site | `tests/test_site_public_mizan.py` (pages, JSON, sitemap) |

---

## 8. Limites

- **Aucune mesure** : le module calcule des règles et des identités, il ne mesure
  ni la pauvreté, ni la paix, ni l'abondance.
- **Aucun transfert** : aucun fonds n'est détenu, perçu ou distribué.
- **Nisab calibré** : les seuils viennent de l'étalonnage du dossier, pas des
  cours réels.
- **Succession partielle** : un cas déclaré, sans `awl`, `radd` ni testament.
- **Modèles agrégés** : capacité, stabilisateur et Gini sont des modèles-jouets
  à hypothèses explicites.
- **Parabole** : le facteur 700 n'est pas un rendement.
- **Indice** : `J = 1−T` est une convention interne, pas une mesure de justice.
- **Complétude** : `K = 1` ne vaut que pour le protocole déclaré ; il ne dit rien
  de la complétude du monde.
- **Aucune autorité** : le module ne remplace ni un juge, ni un savant, ni une
  institution de zakat.

---

## 9. Contrôles

| ID | Contrôle | Attendu | Obtenu |
| :-- | :--- | :--- | :--- |
| C01 | Zakat au-dessus/en dessous du nisab | 25,000000 / 0,000000 | 25,000000 / 0,000000 |
| C02 | Huit catégories, somme exacte 1 | 8 / 1 | 8 / 1 |
| C03 | Report, remise totale, remise plafonnée | 500 / 0 / 700 | 500 / 0 / 700 |
| C04 | Qard sans surcoût ; riba 5 %/10 ans | 6 288,946268 | 6 288,946268 |
| C05 | Capacité 800 €/an, 5 ans, report si C = 0 | 800 / 5 | 800 / 5 |
| C06 | Parts exactes, ratio 2, conjoint 9 000 € | 1 / 2 / 9 000 | 1 / 2 / 9 000 |
| C07 | Injection 2,5 %, rotation 40 ans | 40,000000 | 40,000000 |
| C08 | Gini 0,25 → 0,125 → 0 | 0,25 / 0,125 / 0 | 0,25 / 0,125 / 0 |
| C09 | Parabole 7 × 100 = 700 | 700 / 17 500 | 700 / 17 500 |
| C10 | Demi-vie 27,377851 ans | 27,377851 / 0,363232 | 27,377851 / 0,363232 |
| C11 | Conservation du flux | 25,000000 | 25,000000 |
| C12 | Indice usuraire T = 0,68, J = 0,32 | 0,680000 / 0,320000 | 0,680000 / 0,320000 |
| C13 | Quatre piliers, K = 1 | 4 / 1,000000 | 4 / 1,000000 |
