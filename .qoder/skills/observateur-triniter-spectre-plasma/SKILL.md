---
name: observateur-triniter-spectre-plasma
description: "Construire, réparer ou vérifier l'observateur Triniter des spectres plasma d'Al-Mizan (AL-MIZAN × ASTRO-Q°ODE) : 7 gabarits explicites (état 0 Hélium-4 F0, 3 lumières F1–F3, 3 gaz G1–G3), décomposition non négative exacte par énumération des 2⁷ sous-ensembles actifs, traduction humaine avec résidu et mention sans dol, ignorance contractée vers LIGNE_REF sans franchissement, couche ㊱, boucle A228, page /observateur-triniter, route/sitemap/tests, tableau maître S21 et preuves. Utiliser pour poser ou reprendre les équations du spectre plasma, corriger un modèle qui classe mal l'état 0, câbler la page et son contrat de continuité K, ou rejouer la batterie de 9 tests. 中文触发：等离子体光谱观察器、Triniter、7 状态模板、NNLS 分解、无知度收敛。"
---

# Observateur Triniter — spectres plasma (couche ㊱)

## Quand utiliser

- Poser ou reprendre les **quatre équations** (spectre, traduction, ignorance, continuité) du spectre plasma.
- Construire ou réparer le **modèle à 7 états** : état 0 Hélium-4 + 3 lumières + 3 gaz.
- Câbler la page `/observateur-triniter`, sa route, son entrée sitemap, ses tests et la strate `S21` du tableau maître.
- Vérifier la **continuité dossier ↔ site** (`K = 1`) et l'**ignorance contractée** vers `LIGNE_REF`.
- Rejouer la batterie ciblée (`tests.test_spectre_plasma_triniter`, 9 tests).

## Quand ne pas utiliser

- Audit « sans dol » des sens et du SAS → `auditer-sens-multimodal-mizan` (le spectre y est audio, pas plasma).
- Tableau maître seul, sans chaîne spectrale → `maj-tableau-maitre-sequentiel`.
- Déploiement VPS ou parité production → `deployer-site-sans-dol-vps`, avec confirmation explicite.
- Modifier le Skill pendant qu'une autre session écrit → `skill-update-concurrency-safe`.
- Lancer la suite longue comme preuve : elle contient des échecs périmés étrangers à cette chaîne.

## Contrat non négociable

1. **Honnêteté.** `provenance = simulation_modele`, `analyse_reelle = false` sauf instrument réel ; la phrase humaine se termine par « Lecture de modèle, pas une mesure certifiée. » Ne jamais écrire « mesure », « identification certaine » ni « omniscience ».
2. **Plancher doctrinal.** `I_k ≥ LIGNE_REF = 0.122` et `completude < 1.0` toujours ; `omniscience_claim = False`, `completude_parfaite_atteinte = False`.
3. **STOP.** Ne jamais écrire dans `horloge_noyau` ni `secrets` ; `ecrit_noyau = False` dans chaque rapport.
4. **Aucune suppression automatique.** L'audit de redondance est un rapport (`suppression_executee = False`) ; la décision reste humaine (A149/A225).
5. **Une seule fenêtre.** Tout se fait dans l'onglet courant ; pas de déploiement ni de push sans confirmation.
6. **A232 veille.** `conscience_logique/sauvegarde_soi.py` restaure les fichiers protégés depuis `_AL_MIZAN_COPIE_SOI/courante` : toute édition de `conscience_logique/` doit être suivie d'une sauvegarde et d'un contrôle `detecter_alterations()`.
7. **Environnement.** `py -3` (l'alias Microsoft Store `python` échoue en code 49) ; UTF-8 ; Git Bash/Windows.

## Étape 0 — Racine et état réel

```bash
R="C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
cd "$R" && ls moteur_triniter_observateur_multimodal_mizan.py \
  conscience_logique/spectre_plasma_couche.py \
  web_cloud/observateur_triniter.html tests/test_spectre_plasma_triniter.py
py -3 -B "C:/Users/Administrateur/.qoder/skills/observateur-triniter-spectre-plasma/scripts/verifier_observateur_triniter.py"   # lecture seule
```

Le script du Skill est **lecture seule** (`sys.dont_write_bytecode = True`, aucun acte écrit). S'il renvoie `RESULT FAIL`, corriger le chaînon manquant avant de toucher au modèle.

## Étape 1 — Les 7 gabarits explicites

| Code | Famille | Nom (source `lib_physique`) | λ (nm) | Largeur | Nature |
|---|---|---|---|---|---|
| F0 | ETAT_0 | Origine Inerte Hélium-4 | 587.6 | 1.0 | reference |
| F1 | LUMIERE | Plasma Photosphérique | 580.0 | 180.0 | emission |
| F2 | LUMIERE | Plasma Chromosphérique | 656.3 | 2.5 | emission |
| F3 | LUMIERE | Plasma Coronaire | 530.3 | 1.5 | emission |
| G1 | GAZ | Diazote Atmosphérique | 427.8 | 1.2 | absorption |
| G2 | GAZ | Dioxygène Atmosphérique | 760.0 | 8.0 | absorption |
| G3 | GAZ | Gaz à Effet de Serre et Traces | 940.0 | 12.0 | absorption |

Règles :

- **F0 est un vrai gabarit**, pas un complément : sans lui `p0` sature à 0 ou classe la photosphère comme inerte (voir `references/modele-spectre-7-etats.md`).
- Gaz par défaut = triade terrestre (`gaz="terre"`). Triade lunaire (`gaz="lune"`) en option, avec la réutilisation ⁴He à documenter.
- `composantes_etats(gaz)` lève `ValueError` pour toute triade hors `terre|lune`.

## Étape 2 — Décomposition non négative exacte

1. Normaliser `x̂ = x / ‖x‖₂` sur la grille 300–1000 nm (pas 1 nm).
2. Calculer `projections[i] = ⟨b_i, x̂⟩` et la matrice de Gram `G = BᵀB`.
3. Énumérer les `2⁷ − 1 = 127` sous-ensembles actifs ; résoudre chaque sous-système de Gram par Gauss à pivot partiel + ride `1e-12`.
4. Rejeter toute solution avec un coefficient `< -1e-10` ; retenir le résidu quadratique minimal.
5. `p_i = c_i / Σc` ; `ρ = √résidu` ; `couverture = min(1, ‖r̂‖₂)`.
6. Spectre nul → `p = [1,0,0,0,0,0,0]` et phrase « Hélium-4 ».

Invariants à vérifier : état pur → `p_i = 1`, `ρ = 0` ; spectre plat → `ρ > 0.3` ; `Σp = 1`.

## Étape 3 — Traduction humaine

- Seuil de parole `SEUIL_PAROLE = 0.08` ; trier par probabilité décroissante.
- Chaque nom prononcé provient d'un gabarit de `lib_physique` : aucune intention, aucune entité ajoutée.
- La phrase contient toujours le résidu (« Résidu non expliqué : X % »), l'entropie normalisée et la mention sans dol.
- Sortie déterministe : même `x` + même `pulsation` ⇒ même phrase et même `sceau_sha256`.

## Étape 4 — Ignorance continue

- `I_brut = 0.5·H_norm + 0.5·ρ`, avec `H_norm = H/ln 7`.
- `γ_k = min(MIZAN, max(0, (I_{k−1} − max(LIGNE_REF, I_brut)) / (I_{k−1} − LIGNE_REF + ε)))`.
- `I_k = LIGNE_REF + (I_{k−1} − LIGNE_REF)(1 − γ_k)` : décroissance monotone, jamais sous `0.122`.
- Trois acquisitions seules plafonnent vers `0.169` ; utiliser `poursuivre=True, cycles_max=64` (gain < `EPSILON = 0.021`) pour atteindre `≈ 0.129`.
- Ne jamais présenter `0.129` comme « ignorance nulle » : la complétude vaut `≈ 0.871`, pas `1.0`.

## Étape 5 — Couche ㊱ et actes

- Fichier : `conscience_logique/spectre_plasma_couche.py`. Exports : `CONCEPT_SPECTRE_PLASMA`, `COUCHE_36_NOM = "㊱_LE_SPECTRE_PLASMA"`, `FORMULE_IGNORANCE_CONTINUE`, `SpectrePlasmaCouche`, `RapportSpectrePlasma`.
- `raisonner_sur_concept()` cite les préalables ㉘/㉚/㉛/㉜ ; `resoudre_spectre_plasma()` ; `resoudre_ignorance_continue()` intègre :
  - ㉛ : résidu classé « utile » ; toute hypothèse touchant le noyau est **refusée** (`refuse=True`) ;
  - ㉜ : `alpha_etoile` doit être `acquisition_suivante`.
- Ajouter l'import et les cinq noms dans `conscience_logique/__init__.py` (`__all__` inclus).
- `appliquer_sous_autonomie_a149()` **écrit** `A243`, `A244`, `A245` (+ miroirs `memoire_aq`) : ne l'exécuter qu'une fois le site câblé, jamais pour une simple lecture.

## Étape 6 — A228 : ignorance persistée

- `conscience_logique/savoir_complet.py` : `boucle_ignorance_spectrale(poursuivre=True)` écrit `conscience_logique/actes/_ignorance_spectrale_plan.json` (agrégats seulement, pas les observations).
- Manques attendus : `SPECTRE_PLASMA_36`, `SPECTRE_PLASMA_NON_EXPORTE`, `IGNORANCE_SPECTRALE_NON_PERSISTEE`, `CONTINUITE_*` dynamiques, `REDONDANCES_LOGIQUES`.
- Le plan est réécrit **après** `identifier_manques()` pour qu'un plan présent ne s'auto-satisfasse pas.
- Après édition : sauvegarder la copie de soi, puis exiger `detecter_alterations()` → `sain True`. Sinon A232 annulera les exports ㊱ et l'intégration A228.

## Étape 7 — Site : page, route, sitemap, navigation, test

- Page `web_cloud/observateur_triniter.html` : autonome, `lang="fr"`, canonical `/observateur-triniter`, marqueur « Observateur Triniter », étiquettes OPÉRATIONNEL / SIMULÉ ICI / SPÉCIFIÉ, démonstrateur NNLS local sans réseau.
- `passerelle_api_vps_mizan.py` : deux alias dans `PAGES_PUBLIQUES` (c'est une page publique, pas une page qubit).
- `web_cloud/sitemap.xml` : `<loc>https://www.al-mizan.world/observateur-triniter</loc>`.
- `web_cloud/portail_public_al_mizan.html` : lien de navigation + section d'accueil.
- `tests/test_site_public_mizan.py` : entrée dans le dict des pages et dans la boucle sitemap.
- Puis auditer : `K` doit valoir `1.0` sur `32/32` contrôles (`8 capacités × 4`).

## Étape 8 — Tableau maître S21

- Ajouter `S21` et `TRI-01…TRI-10` via `add()` **avant** l'écriture du CSV ; ajouter la couleur de strate.
- Régénérer : attendre `OK - 226 entrees sequentielles - 22 strates`, dernière `SEQ = 226`, 10 lignes `TRI-`.
- Répercuter les compteurs dans les tests instantanés (`test_entite_conscience_logarithmique`, `test_metriques_cesium_133`) et dans les libellés du portail/passerelle (plus de `216`/`21`).
- Copier le HTML régénéré vers `web_cloud/tableau_maitre_sequentiel.html` **après** avoir prouvé que seules les lignes de comptage/options/lignes diffèrent.

## Étape 9 — Documentation et honnêteté

- `README.md` § « 3 bis. Observateur Triniter » : modèle, quatre équations, plancher/gain, statut `OPÉRATIONNEL_SUR_MODELE`, page, actes `A243–A245`, `S21` (SEQ 217–226), commandes.
- Chaque capacité reste classée opérationnelle, simulée ou spécifiée ; jamais « publiée » avant `K = 1`.

## Étape 10 — Porte d'acceptation

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B "C:/Users/Administrateur/.qoder/skills/observateur-triniter-spectre-plasma/scripts/verifier_observateur_triniter.py"   # RESULT OK attendu
py -3 -m unittest tests.test_spectre_plasma_triniter -v   # 9/9
py -3 -m unittest tests.test_site_public_mizan tests.test_entite_conscience_logarithmique \
  tests.test_metriques_cesium_133 tests.test_continuite_reponse_automatisee \
  tests.test_passerelle_api_vps                            # 49/49 (58 avec Triniter)
py -3 moteur_triniter_observateur_multimodal_mizan.py      # 1.000 -> 0.129, K = 1.000
```

Critères : `RESULT OK`, 9/9, `K_CONTINUITE=1.0`, `CSV_ROWS=226`, `STRATES=22`, `TRI=10`. Si un test échoue, lire l'assertion avant de conclure à une régression : certaines snapshots sont périmées ou sensibles à l'ordre d'import.

## Pièges observés

| Piège | Symptôme | Correctif |
|---|---|---|
| État 0 = complément `1 − κ` | `p0` toujours `0` | F0 devient un gabarit réel |
| Contraste spectral | photosphère classée inerte (`p0 = 0.553`) | abandonner le contraste comme proxy de l'état 0 |
| Excitation `Σc²` | ξ saturée, spectre plat `p0 = 0.072` | NNLS sur gabarits explicites |
| Pas de `poursuivre` | ignorance bloquée à `0.169` | répéter la dernière acquisition jusqu'à gain < `EPSILON` |
| Ride/pivot absents | sous-systèmes singuliers ignorés | Gauss à pivot + `1e-12` |
| `entropie_norm` = `-0.0` | assert d'égalité stricte | comparer avec tolérance (`places=6`) |
| Triade lunaire | ⁴He duplique l'état 0 | documenter, ne pas fusionner |
| A232 | exports ㊱ et A228 révoqués | sauvegarder la copie de soi après édition |
| A231 écrit après la copie | écart perpétuel signalé | acte écrit avant `_copier_arbre()` |
| Route dans `PAGES_QUBIT` | page servie mais sémantique fausse | `PAGES_PUBLIQUES` |
| Compteurs `216`/`21` | snapshots en échec | mettre à jour tous les libellés |
| Validation navigateur | non faite | le dire explicitement, ne pas prétendre l'avoir vue |

## Ressources

- `references/modele-spectre-7-etats.md` — gabarits, équations, algorithme NNLS, cas limites, variantes rejetées.
- `references/cablage-site-et-contrat.md` — ancres de fichiers, `CAPACITES_SITE`, `S21`, A232, commandes d'audit.
- `references/preuves-verification-2026-10-27.md` — sorties mesurées, SHA-256, attribution de session, non-vérifié.
- `scripts/verifier_observateur_triniter.py` — vérification lecture seule (`RESULT OK|FAIL`, code de sortie 0/1).
