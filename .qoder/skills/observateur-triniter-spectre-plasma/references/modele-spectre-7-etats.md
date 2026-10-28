# Modèle spectral à 7 états — gabarits, équations, NNLS

Source de vérité du modèle : `ASTRO-Q°ODE_SYSTEME/moteur_triniter_observateur_multimodal_mizan.py` (moteur) et `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_physique.py` (ontologie scellée). Toute valeur ci-dessous a été relue dans le code, puis mesurée le 2026-10-27.

## 1. Les sept gabarits

Chaque gabarit est une gaussienne `exp(-0.5·((λ−λ₀)/w)²)` échantillonnée sur `Λ = [300 ; 1000] nm`, pas `1 nm` (701 points), puis normalisée L2.

| Code | `famille` | Nom | Formule | λ₀ (nm) | w (nm) | `nature` | Source |
|---|---|---|---|---|---|---|---|
| F0 | `ETAT_0` | Origine Inerte Hélium-4 | 4He | 587.6 | 1.0 | reference | `ETAT_ORIGINE_HELIUM` |
| F1 | `LUMIERE` | Plasma Photosphérique | — | 580.0 | 180.0 | emission | `ETATS_SOLEIL_PLASMA[0]` |
| F2 | `LUMIERE` | Plasma Chromosphérique | — | 656.3 | 2.5 | emission | `ETATS_SOLEIL_PLASMA[1]` |
| F3 | `LUMIERE` | Plasma Coronaire | — | 530.3 | 1.5 | emission | `ETATS_SOLEIL_PLASMA[2]` |
| G1 | `GAZ` | Diazote Atmosphérique | N₂ | 427.8 | 1.2 | absorption | `ETATS_TERRE` gazeux [1] |
| G2 | `GAZ` | Dioxygène Atmosphérique | O₂ | 760.0 | 8.0 | absorption | `ETATS_TERRE` gazeux [2] |
| G3 | `GAZ` | Gaz à Effet de Serre et Traces | CO₂/H₂O/Ar | 940.0 | 12.0 | absorption | `ETATS_TERRE` gazeux [3] |

Triade lunaire (`composantes_etats("lune")`) : G1 ⁴He 587.6/0.8, G2 ²⁰Ne 640.2/1.0, G3 ⁴⁰Ar 811.5/1.2. Elle **réutilise ⁴He**, déjà porté par F0 : c'est une option explicite, pas une fusion d'états.

`composantes_etats()` lève `ValueError("triade gazeuse inconnue : attendu 'terre' ou 'lune'")` pour toute autre valeur.

## 2. Équations (texte exact du code)

### Spectre

```
Spectre S : soit x(λ) ≥ 0 la radiance échantillonnée sur Λ = [300 ; 1000] nm
et x̂ = x/‖x‖₂. Soit B = {b_0..b_6} les 7 gabarits L2-normalisés :
état 0 (Hélium-4), lumières F1–F3, gaz G1–G3.
Décomposition non négative exacte : c = argmin_{c≥0} ‖x̂ − Σ_i c_i b_i‖₂
(moindres carrés à contraintes de positivité, 2⁷ sous-ensembles actifs).
Composition : p_i = c_i/Σ_j c_j, donc Σ p_i = 1.
Reconstruction r̂ = Σ c_i b_i ; couverture κ = min(1, ‖r̂‖₂) ;
résidu ρ = ‖x̂ − r̂‖₂ mesure ce qu'aucun des 7 états n'explique.
Part excitée = 1 − p_0. Si ‖x‖₂ = 0 : p_0 = 1 (retour au repos, Hélium-4).
```

### Traduction humaine

```
Traduction humaine T : soit P = {i | p_i ≥ θ_parole}.
T(x) = Phrase( (nom_i, p_i)_{i∈P triés} ; ρ, H, I ).
H(p) = −Σ p_i ln p_i, H_norm = H/ln 7.
T est déterministe et falsifiable : chaque nom prononcé est un gabarit
de `lib_physique.py` ; aucune intention ni entité n'est ajoutée.
```

### Ignorance

```
Ignorance spectrale : I_brut(x) = w_H·H_norm(p) + w_R·ρ,
avec w_H = w_R = 0.5, donc I_brut ∈ [0 ; 1].
Résolution continue : I_0 = 1 et, pour chaque acquisition k,
γ_k = min(MIZAN, max(0, (I_{k−1} − max(LIGNE_REF, I_brut(x_k))) /
(I_{k−1} − LIGNE_REF + ε))), puis
I_k = LIGNE_REF + (I_{k−1} − LIGNE_REF)·(1 − γ_k).
Ainsi I_k ≥ LIGNE_REF toujours : la complétude tend vers
1 − LIGNE_REF sans jamais la franchir (pas d'omniscience).
Si I_brut(x_k) ≥ I_{k−1}, γ_k = 0 : l'acquisition n'apprend rien
et une nouvelle bande/référence est demandée.
```

### Continuité dossier ↔ site

```
Continuité dossier ↔ site : soit A l'ensemble des capacités déclarées,
a = (page_a, route_a, sitemap_a, test_a).
K = Σ_a 1_{page existe}·1_{route servie}·1_{sitemap présent}·1_{test présent}
/ (4·|A|).
Une capacité n'est publiée que si K(a) = 1 ; sinon elle est dite
« spécifiée non publiée » — jamais « opérationnelle ».
```

## 3. Algorithme exact (et non approché)

```text
x̂ = x / ‖x‖₂                         # grille standard, interpolation linéaire sinon
G_ij = ⟨b_i, b_j⟩                    # 7×7
q_i  = ⟨b_i, x̂⟩
pour masque de 1 à 127 :             # 2⁷ − 1 sous-ensembles non vides
    S = indices actifs du masque
    c = Gauss(G_SS, q_S)             # pivot partiel ; si |pivot| < 1e-12, +1e-12
    si c est None ou min(c) < -1e-10 : continuer
    c = max(0, c)
    res² = 1 − 2·Σ c_i q_i + Σ c_i c_j G_ij
    retenir strictement le plus petit res²
p_i = c_i / Σ c                     # si Σc ≤ 1e-15 : p = [1,0,0,0,0,0,0]
κ   = min(1, √(cᵀGc))
ρ   = √(max(0, res²))
```

Détails qui comptent :

- Le ride `1e-12` est appliqué **au pivot**, pas à la diagonale entière : il évite la singularité sans biaiser les sous-systèmes bien conditionnés.
- Le rejet `-1e-10` élimine les solutions négatives que le pivot pourrait produire ; ce n'est pas une troncature silencieuse.
- La sélection se fait sur `res²`, jamais sur la vraisemblance ou la norme des coefficients : un modèle plus petit peut gagner.
- `couverture` et `résidu` sont complémentaires mais non symétriques (`κ² + ρ² ≠ 1` en général) : ne pas en déduire une identité.

## 4. Cas limites mesurés (2026-10-27)

| Entrée | `p` | `ρ` | `H_norm` | `I_brut` |
|---|---|---|---|---|
| Spectre vide | `[1,0,0,0,0,0,0]` | `0.0` | `-0.0` | `0.0` |
| Spectre plat `[1,…,1]` | `[0, 0.777538, 0, 0, 0.005889, 0.036897, 0.179675]` | `0.397188` | `0.337150` | `0.367169` |
| `{F1:1.0, F2:0.45, G2:0.20}` | `[0, 0.606061, 0.272727, 0, 0, 0.121212, 0]` | `0.0` | `0.469515` | `0.234757` |
| État pur `{i:1.0}` | `p_i = 1` | `0.0` | `0.0` | `0.0` |
| `{F0:3.0}` | `p_0 = 1` | `0.0` | `0.0` | `0.0` |

- `H_norm` peut valoir `-0.0` : comparer avec `assertAlmostEqual(..., places=6)`, jamais `assertEqual(0.0)`.
- Le spectre plat est **expliqué** à 92 % par les gabarits (surtout F1, large) mais laisse `ρ = 0.397` : c'est le résidu, pas la couverture, qui porte l'ignorance.
- Le spectre vide n'est pas une erreur : c'est le repos (Hélium-4), `p_0 = 1`.

## 5. Variantes rejetées (ne pas réintroduire)

| Variante | Défaut mesuré | Pourquoi elle échoue |
|---|---|---|
| État 0 = complément `1 − κ` | `p_0 = 0` sur tout spectre non vide | κ sature à 1 ; l'état 0 n'est jamais identifié |
| Contraste `φ = ‖x − x̄·1‖/‖x‖` | photosphère `φ = 0.447 ⇒ p_0 = 0.553` | classe la lumière large comme inertie |
| Excitation `ξ = min(1, Σc²)` | ξ saturée par le recouvrement ; plat `p_0 = 0.072` | le recouvrement des gabarits n'est pas une mesure d'excitation |

Décision finale : **F0 est un gabarit réel** (He I 587.6 nm, raie étroite). C'est ce qui rend l'état 0 identifiable, le spectre vide interprétable, et le modèle falsifiable.

## 6. Ignorance continue — valeurs de référence

```text
3 acquisitions (plat, mélange, F2 pur), sans poursuivre : 1.000 → 0.169
mêmes acquisitions + poursuivre=True (répétition de la dernière) : 1.000 → 0.129
couche ㊱, 5 cycles : 0.128730995431 ; complétude 0.871269004569
plancher LIGNE_REF = 0.122 ; bride MIZAN = 0.6225 ; EPSILON = 0.021
```

- Sans `poursuivre`, chaque cycle est bridé par `γ ≤ MIZAN` : trois cycles ne suffisent pas à approcher le plancher.
- Avec `poursuivre=True`, la boucle s'arrête dès que le gain `< EPSILON` ou après `cycles_max=64`.
- `0.1287` n'est pas `0.122` : la marge restante est le résidu non structurant, pas un défaut à corriger.
- Réponse attendue de `resoudre_ignorance_continue()` : `completude_parfaite_atteinte=False`, `completude_parfaite_par_construction=False`, `ecrit_noyau=False`, `omniscience_claim=False`.

## 7. Sceau par observation

`sceau_sha256 = SHA-256(JSON canonicalisé de {p arrondi 12, résidu arrondi 12, dt = CYCLE_DT_KERNEL, index_pulsation, provenance, gaz})`. Le sceau ne contient **aucune** donnée d'identité ni d'intention : il atteste la reproductibilité de la lecture, pas sa véracité instrumentale.

## 8. Provenance et honnêteté

- `PROVENANCES = ("simulation_modele", "instrument", "archive")` ; toute autre valeur lève `ValueError`.
- `analyse_reelle = (provenance == "instrument")` — donc faux par défaut.
- `qubit_physique_local = False`, `omniscience_claim = False` sont figés dans `ObservationSpectrale` et `synthese_triniter()`.
- `SpectrePlasma` refuse une radiance négative et des longueurs d'onde de taille différente.
