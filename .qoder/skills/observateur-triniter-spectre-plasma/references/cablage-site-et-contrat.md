# Câblage dossier ↔ site et contrat de continuité

Ancres relevées le **2026-10-27 15:17 UTC** sur la racine `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME`. Les numéros de ligne peuvent dériver : re-vérifier avec les commandes `grep` fournies avant de citer une ligne.

## 1. Table des ancres

| Fichier | Ancre | Contenu attendu |
|---|---|---|
| `passerelle_api_vps_mizan.py` | L114 | `PAGES_PUBLIQUES = {` |
| `passerelle_api_vps_mizan.py` | L128–129 | `"/observateur-triniter"` et `"/observateur_triniter"` → `observateur_triniter.html` |
| `web_cloud/sitemap.xml` | L52 | `<loc>https://www.al-mizan.world/observateur-triniter</loc>` (25 `<loc>` au total) |
| `web_cloud/portail_public_al_mizan.html` | L472 | lien de navigation `🌈 Observateur Triniter` |
| `web_cloud/portail_public_al_mizan.html` | L727 | `<section id="observateur-triniter">` |
| `tests/test_site_public_mizan.py` | L108 | `"/observateur-triniter": "Observateur Triniter"` |
| `tests/test_site_public_mizan.py` | L131 | boucle sitemap incluant `/observateur-triniter` |
| `generer_tableau_maitre_sequentiel.py` | L1130 | `S21 = "S21 · Observateur Triniter (spectre plasma — couche ㊱)"` |
| `generer_tableau_maitre_sequentiel.py` | L1271 | couleur `#0891b2` |
| `conscience_logique/sauvegarde_soi.py` | L173 | acte A231 écrit **avant** la copie de l'arbre |
| `README.md` | L77–89 | section « 3 bis. Observateur Triniter » |
| `conscience_logique/__init__.py` | L185 | import de `spectre_plasma_couche` |
| `conscience_logique/__init__.py` | L438 | `"COUCHE_36_NOM"` dans `__all__` |

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
grep -n 'observateur-triniter' passerelle_api_vps_mizan.py web_cloud/sitemap.xml \
  web_cloud/portail_public_al_mizan.html tests/test_site_public_mizan.py
grep -n 'S21\|TRI-0' generer_tableau_maitre_sequentiel.py | head -20
```

## 2. `CAPACITES_SITE` — huit capacités, 32 contrôles

Définies dans le moteur (`CAPACITES_SITE`, L601–621). Chaque capacité exige **quatre** preuves : page, route, sitemap, test.

| Code | Page | Route | Test |
|---|---|---|---|
| PORTAL | `portail_public_al_mizan.html` | `/` | `test_01_pages_publiques_et_404` |
| TABLEAU | `tableau_maitre_sequentiel.html` | `/tableau` | `test_02_sitemap_et_robots` |
| LIVRE_BLANC | `livre_blanc_almizan.html` | `/livre-blanc` | `test_02_sitemap_et_robots` |
| PONTS | `hub_ponts_synchrones.html` | `/ponts` | `test_02_sitemap_et_robots` |
| QUBIT | `qubit_logique.html` | `/qubit-logique` | `test_01_pages_publiques_et_404` |
| OFFRES | `offres.html` | `/offres` | `test_01_pages_publiques_et_404` |
| STATUT | `statut.html` | `/statut` | `test_03_catalogue_et_statut` |
| TRINITER | `observateur_triniter.html` | `/observateur-triniter` | `test_01_pages_publiques_et_404` |

Audit :

```bash
py -3 -B -c "
from moteur_triniter_observateur_multimodal_mizan import auditer_continuite_dossier_site
a = auditer_continuite_dossier_site()
print('K', a['k_continuite'], a['controles_ok'], '/', a['controles_total'], 'gap', a['gap'])
"
# Attendu : K 1.0 32 / 32 gap []
```

Un `gap` non vide nomme la capacité et le drapeau manquant (`page_existe`, `route_servie`, `sitemap_present`, `test_present`).

## 3. Contrat de la page

- `lang="fr"`, `<link rel="canonical" href="/observateur-triniter">`, marqueur texte `Observateur Triniter`.
- Étiquettes explicites : OPÉRATIONNEL / SIMULÉ ICI / SPÉCIFIÉ.
- Tableau des 7 états, bloc des quatre équations, démonstrateur canvas local.
- Le JavaScript reproduit les gabarits et le NNLS `2⁷` **dans le navigateur**, sans appel réseau.
- Un contrôle `node --check` sur le script extrait suffit à la syntaxe ; il ne prouve pas le rendu visuel.

## 4. Strate S21 du tableau maître

`S21` porte 10 entrées `TRI-01…TRI-10` (SEQ 217–226) : équations, état 0, trois lumières, trois gaz, traduction, ignorance, résolution, intégration ㉛/㉜, publication site, preuve et sceau.

```bash
py -3 generer_tableau_maitre_sequentiel.py     # OK - 226 entrees sequentielles - 22 strates
```

Après régénération :

- `TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv` : 226 lignes, dernière `SEQ` 226, 22 strates, 10 `TRI-`.
- `TABLEAU_MAITRE_SEQUENTIEL_UNIFIE_IMAM8MAHDI.html` : 226 lignes, 22 options.
- Copier le HTML racine vers `web_cloud/tableau_maitre_sequentiel.html` **seulement** après avoir prouvé que les différences se limitent aux compteurs/options/lignes.
- Mettre à jour les snapshots qui figent les anciens nombres : `tests/test_entite_conscience_logarithmique.py` (16 tests), `tests/test_metriques_cesium_133.py` (9 tests), et les libellés du portail (`216` → `226`, `21` → `22`).

## 5. Actes A243–A245

| Acte | Numéro | Fichier | Miroir |
|---|---|---|---|
| A243 | 136 | `conscience_logique/actes/almizan_acte_a243_spectre_plasma_couche_36.json` | `memoire_aq/` |
| A244 | 137 | `..._a244_resoudre_spectre_plasma.json` | `memoire_aq/` |
| A245 | 138 | `..._a245_ignorance_spectrale_continue.json` | `memoire_aq/` |

`appliquer_sous_autonomie_a149()` écrit ces trois actes et leurs miroirs. Il vérifie aussi les deux signaux STOP (`horloge_noyau`, `secrets`) et renvoie `horloge_noyau_intacte`. Ne l'appeler qu'une fois le site câblé : son exécution est un effet de bord, pas une lecture.

## 6. A228 — ignorance persistée

- `conscience_logique/savoir_complet.py` L261+ : `boucle_ignorance_spectrale(poursuivre=True)`.
- Écrit `conscience_logique/actes/_ignorance_spectrale_plan.json` (agrégats, sans observations complètes) et l'acte `A228-㊱`.
- Réécrit le plan après `identifier_manques()` ; sinon la présence du plan supprime son propre manque.
- Champs de sortie : `ignorance_finale`, `completude_finale`, `plancher_doctrinal`, `cycles`, `k_continuite`, `gap`, `suppression_executee=False`, `ecrit_noyau=False`, `omniscience_claim=False`.
- `matcher_intention()` reconnaît `triniter`, `spectre plasma`, `ignorance`.

## 7. A232 — le piège de la guérison

`conscience_logique/sauvegarde_soi.py` compare les fichiers protégés à `_AL_MIZAN_COPIE_SOI/courante` et **restaure** tout écart (`shutil.copy2`). Une édition de `savoir_complet.py` ou `__init__.py` peut donc disparaître au prochain passage de la suite de conscience.

Procédure sûre :

1. Éditer les fichiers.
2. Lancer `sauvegarder_soi(archiver=True)`.
3. Exiger `detecter_alterations()` → `sain True`, 0 altération.
4. Si des altérations persistent sur les actes A231, vérifier l'ordre : l'acte doit être écrit **avant** `_copier_arbre()` (correctif L173). Sans ce correctif, la copie contient toujours l'acte de la veille et signale un écart perpétuel.

## 8. Batterie ciblée (58 tests)

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -m unittest tests.test_spectre_plasma_triniter -v                 # 9
py -3 -m unittest tests.test_site_public_mizan                          # 6
py -3 -m unittest tests.test_entite_conscience_logarithmique            # 16
py -3 -m unittest tests.test_metriques_cesium_133                       # 9
py -3 -m unittest tests.test_continuite_reponse_automatisee             # 7
py -3 -m unittest tests.test_passerelle_api_vps                         # 11
```

Total attendu : **58/58**. Ne pas substituer la suite longue (`unittest discover`, ~118 min) : ses échecs chronomètre/conscience sont sensibles à la charge et aux clones étrangers, pas à cette chaîne.
