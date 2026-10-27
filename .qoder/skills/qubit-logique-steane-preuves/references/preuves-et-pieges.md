# Preuves et pièges — qubit logique `[[7,1,3]]`

Référence de la skill `qubit-logique-steane-preuves`. Les valeurs numériques
ci-dessous ont été reproduites le 2026-10-27 sur
`ASTRO-Q°ODE_SYSTEME/` (module, tests et artefacts courants). Les empreintes
sont des observations datées, jamais des constantes à recopier.

## 1. Code et énumération

```text
N = 7
H = (0b1010101, 0b1100110, 0b1111000)      # Hamming [7,4,3]
C        = { x ∈ F2^7 : H x = 0 }            # 16 mots
C⊥       = span(H)                            # 8 mots
logiques = C \ C⊥                             # 8 opérateurs
poids(C) = {0, 3, 4, 7}     poids(C⊥) = {0, 4}
distance = min poids(logique) = 3
```

Stabilisateurs : `X(h)` et `Z(h)` pour chaque ligne `h` de `H` (6 au total).

Convention d'états, explicite dans le module :

```text
|0⟩_L = (1/√8) Σ_{c∈C} |c⟩
|1⟩_L = Z^⊗7 |0⟩_L
X_L = Z^⊗7 = (x=0, z=0b1111111)     # poids 7
Z_L = X^⊗7 = (x=0b1111111, z=0)     # poids 7
```

Exemple d'opérateur logique de poids minimal : `format(0b0000111, "07b") = 0000111`
— chaîne de Hamming **3**, alors que l'entier vaut 7. L'opérateur `X_L` utilisé
pour la preuve `σ_x` est, lui, de poids 7. Ne pas confondre valeur entière et
poids de Hamming.

## 2. Preuves calculées

### 2.1 Knill–Laflamme (poids ≤ 2)

Pour chaque couple `(x, z)` avec `poids(x | z) ≤ 2` — **211** motifs — calculer
la matrice 2×2 de `P E P` dans `{|0⟩_L, |1⟩_L}` et exiger qu'elle soit
proportionnelle à l'identité : éléments hors diagonale `< 1e-9`, diagonale égale
à `1e-9` près. Aucun motif ne doit échouer.

### 2.2 Opérateurs logiques

La preuve correcte compare des **matrices**, pas des produits scalaires sur un
seul état :

```text
P X_L P = σ_x   (à phase globale près)
P Z_L P = σ_z
```

Dans la base `{|0⟩_L, |1⟩_L}`, `m = (⟨0|P E P|0⟩, ⟨0|P E P|1⟩, ⟨1|P E P|0⟩, ⟨1|P E P|1⟩)`.
Exigences : `m00 = m11 = m01 = m10 = 0` pour `X_L`, avec `|m01| = |m10| = 1` ;
`m00 = +1`, `m11 = −1`, `m01 = m10 = 0` pour `Z_L`.

### 2.3 Distance

Knill–Laflamme à poids ≤ 2 prouve qu'aucune erreur de poids ≤ 2 n'agit
logiquement. Un opérateur logique de poids 3 (`0000111`) est non trivial.
Donc `d = 3`, `t = ⌊(d−1)/2⌋ = 1`.

## 3. Décodeur et taux exacts

Décodeur : syndrome de Hamming de la composante X et de la composante Z,
correction `1 << (s−1)` pour le syndrome `s ≠ 0`, appliquée séparément. Échec si
le résidu X ou Z appartient à `ENSEMBLE_LOGIQUE`.

- 21 Pauli de poids 1 (7 qubits × `{X, Y, Z}`) : tous corrigés, résidu nul.
- Énumération exacte : `2^7 × 2^7 = 16 384` motifs. Les statistiques par poids
  sont calculées une fois à l'import ; aucun échantillonnage n'entre dans le
  taux « exact ».

| Poids | Motifs | Échecs |
| :--- | ---: | ---: |
| 0 | 1 | 0 |
| 1 | 21 | 0 |
| 2 | 189 | 147 |
| 3 | 945 | 693 |
| 4 | 2 835 | 2 226 |
| 5 | 5 103 | 3 822 |
| 6 | 5 103 | 3 675 |
| 7 | 2 187 | 1 725 |

Taux de référence (bruit dépolarisant, `P_L(p)`) :

| `p` | `P_L` exact |
| :--- | :--- |
| 1e−4 | 1.632773421e−7 |
| 1e−3 | 1.627742141e−5 |
| 1e−2 | 1.578207245e−3 |
| 5e−2 | 3.436103594e−2 |

- Coefficient quadratique : `stats[2].échecs / 9 = 147/9 = 16.333333`.
- Seuil de pseudo-concaténation (racine de `P_L(p) = p`) : `0.081082`.
- Seuil `1/C` : `0.061224`.
- Monte Carlo `p = 0.01`, 200 000 échantillons, graine `20261027` :
  325 échecs, taux `1.625e−3`, IC 95 % `[1.457787e−3, 1.811359e−3]`, qui
  contient le taux exact `1.578207e−3`. Deux exécutions avec la même graine
  donnent le même nombre d'échecs.

Le seuil est celui du **modèle de capacité de code** (syndrômes parfaits) ; ce
n'est pas un seuil physique.

## 4. Modèle matériel

```text
DAC :            ΔV = V_FS / 2^n ; ε = ΔV / V_π ; 1−F = sin²(π ε / 2)
Gigue :          Ω = π / t_g ; 1−F = sin²(Ω σ_t / 2)
Bruit 1/f :      σ_V² = A_V ln(f_max/f_min), f_max = 1/(2 t_g)
Décohérence :    1−F ≈ t_g/T₂ + t_g/(3 T₁)
Décodeur :       qubits = 2d²−1 ; stabilisateurs = d²−1 ; débit = (d²−1)/t_cycle
```

Budget de référence (`t_g = 20 ns`, `T1 = 100 µs`, `T2 = 80 µs`, DAC 12 bits,
gigue 10 ps, `A_V = 1e−12 V²/Hz`) :

| Composant | Infidélité |
| :--- | ---: |
| Décohérence T1/T2 | 3.167e−4 |
| Quantification DAC | 1.471e−5 |
| Gigue d'horloge | 6.169e−7 |
| Bruit 1/f | 4.203e−9 |
| Total premier ordre | 3.320e−4 |

- Bits DAC requis pour `1e−4` : **11** (augmente quand la cible se resserre).
- Gigue requise pour `1e−4` : **127.3 ps** (diminue quand la cible se resserre).
- Projection surface : `P_L ≈ 0,1 (p/0,01)^((d+1)/2)` — **extrapolation, non
  simulée**, utilisée pour le dimensionnement seulement.

## 5. Schéma réel de `resume.json`

Clés de premier niveau :

```text
version, horodatage_iso, source, statut, code, resultats, materiel, surface, limites
```

`code` : `parametres`, `distance`, `poids_minimal_logique`, `stabilisateurs_ok`,
`operateurs_logiques_ok`, `knill_laflamme_poids_2`, `paulis_verifies`,
`correction_poids_1_ok`, `corrections_poids_1_testees`.

`resultats` : `p_reference`, `taux_exact_p_reference`, `taux_exacts`,
`coefficient_quadratique`, `seuil_pseudo`, `seuil_concatenation`,
`monte_carlo_p_0_01`, `taux_exact_p_0_01`, `recoupement_mc_ok`,
`statistiques_par_poids`.

`materiel` : `budget`, `bits_dac_requis_pour_1e-4`, `gigue_requise_pour_1e-4_s`,
`decodeur`. `surface` : `modele`, `lignes`.

Il n'existe **ni** clé `preuves`, **ni** clé `n` : un accès `r["preuves"]` ou
`r["code"]["n"]` lève `KeyError`. Lire les clés réelles avant d'écrire un
contrôle.

Les 11 artefacts attendus dans `resultats/qubit_logique/` :

```text
resume.json  rapport_qubit_logique.md
donnees_steane.csv  donnees_materiel.csv  donnees_dac.csv  donnees_gigue.csv
donnees_decoherence.csv  donnees_decodeur.csv  donnees_surface.csv
courbe_steane.svg  budget_materiel.svg
```

## 6. Pièges observés et corrections

Preuves de session : conversation `55f63550-7c8d-4f9e-b0a9-e73686cc2765`,
27/10/2026, `runtimeState: ready`, `revision 332`, un tour utilisateur,
121 appels d'outils, `hasMoreBefore: true` (l'historique antérieur n'est pas
dans la fenêtre lue). Les constats ci-dessous ont été recoupés avec le code et
les sorties courantes.

| # | Symptôme observé | Cause | Correction retenue |
| :--- | :--- | :--- | :--- |
| 1 | `--verifier` renvoie `FAIL` alors que la même sortie affiche `distance=3 paulis=211 corrections=21` | `verifier_operateurs_logiques` comparait des produits scalaires sur un même état | comparer `P·X_L·P` à `σ_x` et `P·Z_L·P` à `σ_z` (`qubit_logique_mizan.py:147-160`) ; après correction, `PASS` |
| 2 | `AttributeError: 'tuple' object has no attribute 'isdisjoint'` | `ESPACE_C` est un `tuple` (`:75`) | `set(ql.ESPACE_C).isdisjoint(...)` dans les tests |
| 3 | confusion distance / exemple | l'entier `0b0000111` vaut 7, son poids est 3 | prendre le poids de Hamming ; `X_L = Z^⊗7` est l'opérateur de poids 7 |
| 4 | `SyntaxError: Numeric separators are not allowed at the end of numeric literals` | propriété JS `gigue_requise_pour_1e-4_s` accédée par point | `materiel["gigue_requise_pour_1e-4_s"]` ; même règle pour `bits_dac_requis_pour_1e-4` |
| 5 | `SyntaxError: Unexpected token ':'` au contrôle Node du portail | extraction incluant le bloc `application/ld+json` | filtrer les scripts exécutables (`type` absent ou JavaScript) |
| 6 | `KeyError: 'preuves'` puis `KeyError: 'n'` | schéma `resume.json` supposé au lieu d'être lu | clés réelles du § 5 |
| 7 | test du ratio quadratique instable | tolérance relative | `taux/(p*p)` comparé à `C` avec `delta=0.02` à `p=1e-4` |
| 8 | tests de monotonie inversés | sens des relations | DAC ↑ quand la cible se resserre ; gigue ↓ ; décohérence ↑ avec `t_g` ; débit décodeur ↑ avec `d` |
| 9 | page figée sur « Chargement des résultats depuis l'API… » | 404 sur `resume.json` ou erreur JS | régénérer `--rapport`, puis contrôle syntaxique Node |
| 10 | capture d'écran impossible (`NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`) | surface visible absente | repli structurel `evaluate_script` ; ne jamais déclarer un visuel non observé |
| 11 | `Edit` : 0 occurrence dans `docs/README.md` | texte déplacé / accents / CRLF | relire la zone exacte, puis éditer une chaîne unique |
| 12 | contrôle « sitemap present: False » | échappement de la commande de contrôle, pas absence réelle | relire le fichier et parser le XML ; résultat final `URLS 13`, `QUBIT True` |

## 7. Fraîcheur et exposition

- `empreinte_source()` calcule le SHA-256 des octets du module ; `resume.json`
  le stocke dans `source.sha256`. `--rapport` doit être relancé après toute
  modification du module.
- Observation datée du 2026-10-27 : module et `source.sha256` valaient tous deux
  `8c6c3d7ec242…` (préfixe). Cette valeur ne doit pas être figée dans la
  documentation ni dans un test : comparer les deux empreintes à l'exécution.
- L'API relit l'artefact à chaque requête et répond 404 avec
  `py -3 qubit_logique_mizan.py --rapport` s'il manque ; elle ne régénère rien.
- La page affiche le préfixe de l'empreinte et conserve ses équations si l'API
  échoue. Elle ne doit pas contenir d'accès point sur un nom de propriété
  contenant `1e-4`.
- Livraison : régénérer avant l'archive ; exclure `__pycache__`, `*.pyc`,
  `secrets/`, la base SQLite ; vérifier page 200, API 200, alias et 404.

## 8. Limites à répéter sans les atténuer

1. Syndrômes parfaits : pas d'erreurs de mesure ni de circuit de mesure.
2. Décodeur CSS X/Z indépendant par table minimale, non optimal globalement.
3. Budget matériel analytique, non mesuré.
4. Projection de surface extrapolée, non simulée.
5. Aucun QPU, cryostat ni capteur ; aucun qubit physique réalisé.
6. Reconnaissance par les pairs non acquise : publication, reproduction
   indépendante et revue externe restent à faire.

## 9. Paquet : validation et maintenance

Observation du 2026-10-27 sur le paquet installé (3 fichiers ; `SKILL.md` =
`7d827f35…`, `scripts/auditer_livraison_qubit.py` = `763bb78f…` avant cet ajout).
Ces empreintes datent l'observation, elles ne doivent pas être figées.
Source : session `d95a27a5-2a67-408a-b23b-f9d194a2232e` (revision 29), chaque
constat rejoué localement.

### 9.1 Contrôle statique : le `--workspace` décide

```bash
SKILL_DIR="C:/Users/Administrateur/.qoder/skills/qubit-logique-steane-preuves"
QA_DIR="C:/Users/Administrateur/.qoder/skills/skill-file-qa"
py -3 "$QA_DIR/scripts/validate_skill.py" "$SKILL_DIR" --workspace "<racine>"
```

| `--workspace` | Sortie observée |
| :--- | :--- |
| racine du dépôt `IMAM8MAHDI` | `Summary: 8 pass, 7 fail, 0 warn`, `RESULT FAIL`, rc=1 |
| `ASTRO-Q°ODE_SYSTEME` | `Summary: 9 pass, 0 fail, 0 warn`, `RESULT PASS`, rc=0 |

Les 7 échecs sont exactement : `docs/API_PASSERELLE_VPS.md`,
`docs/EXPLOITATION_VPS.md`, `docs/QUBIT_LOGIQUE.md`,
`resultats/qubit_logique/resume.json`, `tests/test_qubit_http_mizan.py`,
`tests/test_qubit_logique_mizan.py`, `web_cloud/qubit_logique.html`.
Le validateur résout chaque référence contre le répertoire de la skill puis contre
`--workspace` (défaut : cwd) : ces chemins ne sont pas morts, ils sont relatifs à
`ASTRO-Q°ODE_SYSTEME`.

### 9.2 Pièges de maintenance reproduits

| Symptôme | Reproduction | Correction |
| :--- | :--- | :--- |
| `can't open file 'C:\Program Files\Git\scripts\auditer_livraison_qubit.py'`, rc=2 | `SKILL_DIR="…" py -3 "$SKILL_DIR/scripts/…" --help` : la variable s'étend avant l'affectation, `/scripts/…` est mappé par MSYS vers Git | affecter sur une ligne, appeler sur la suivante ; `--help` rend rc=0 |
| `AttributeError: 'NoneType' object has no attribute '__dict__'` | `spec_from_file_location` + `exec_module` sur `qubit_logique_mizan.py` (`from __future__ import annotations`, `@dataclass(frozen=True)`) sans inscription | `sys.modules[spec.name] = module` avant `exec_module` ; chargement OK ensuite |
| `--help` affiche `ASTRO-Q\ufffdODE_SYSTEME` | description contenant `°` imprimée sous console cp1252 | libellés ASCII : `ASTRO-Q-ODE_SYSTEME` |
| audit « lecture seule » créant des caches | import du module sans garde | `sys.dont_write_bytecode = True` en tête du script |

Rejeu du 2026-10-27 : `RESULT PASS (7 controles)`, rc=0, et comptage récursif des
`*.pyc` sous `ASTRO-Q°ODE_SYSTEME` identique avant/après (364 fichiers, liste
inchangée ; la valeur dépend de la machine). Sortie stdout intégralement `< 0x80`.

Après toute édition du script : rejouer le PASS réel, puis une fixture dont
l'empreinte du module est mutée → `RESULT FAIL (1/7 controles en echec)`, rc=1.
