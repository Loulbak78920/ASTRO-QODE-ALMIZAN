---
name: tableau-maitre-sequentiel
description: "Générer, étendre ou auditer le tableau maître séquentiel unifié d'IMAM8MAHDI (AL-MIZAN × ASTRO-Q°ODE) : lire les sources scellées, ajouter des briques via add() avec SEQ automatique 001..N, régénérer l'unique générateur Python vers le CSV Excel français (UTF-8 BOM, séparateur « ; », 13 colonnes) et le dashboard HTML autonome, puis valider la numérotation continue, les invariants S6 40/313/63, la cohérence CSV/HTML, l'autonomie hors ligne et les pièges Windows cp1252. Couvre aussi les strates mesurées (S19 Cs-133) : mesure géolocalisée, snapshot scellé SHA-256, preuve Monade 9/9 + 23/23 et refus du générateur si la preuve est incomplète. Utiliser pour toute demande de tableau maître ou séquentiel, de strate, de SEQ, de CSV français, de dashboard autonome, de Cs-133 ou de snapshot scellé de ce dépôt. 中文触发：主表、顺序表、顺序编号、法语 CSV、离线仪表盘、铯-133、密封快照。"
---

# Tableau maître séquentiel unifié

Skill canonique pour générer, étendre et auditer le tableau maître séquentiel d'IMAM8MAHDI. Le Skill voisin `maj-tableau-maitre-sequentiel` reste disponible pour compatibilité ; en cas de divergence, ce Skill et son validateur font foi.

## Quand l'utiliser

- L'utilisateur envoie de nouvelles briques (concepts, images, actes, exports) à harmoniser.
- Il faut ajouter, corriger ou relier une strate sans casser la séquence.
- Il faut ajouter ou rafraîchir une strate mesurée (S19 Cs-133) à partir d'un snapshot scellé.
- Il faut vérifier le CSV, le HTML, les invariants S6 ou l'autonomie du dashboard.

## Contrat non négociable

1. **Source unique** : `ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py`. Le CSV et le HTML à la racine sont des artefacts générés ; ne jamais les éditer à la main.
2. **13 colonnes** : `COLONNES` est la référence. Ne pas modifier le schéma pour un ajout de contenu.
3. **SEQ automatique** : `add()` attribue `SEQ` avec `f"{len(ROWS) + 1:03d}"`. Ne jamais écrire de numéro à la main ; la suite doit rester `001..N` sans trou.
4. **Strates contiguës** : chaque strate forme un bloc. Un nouveau domaine crée `S<n+1>` après la dernière strate, avant `# Écriture du CSV`. Une extension décale les SEQ suivantes : le signaler.
5. **S6 scellé** : 20 états + origine Hélium = 21 lignes, magnitudes 40 / 313 / 63, comptes Soleil 4 plasma / Terre 7 / Lune 9, plus l'origine Hélium 0 hors comptes. La distribution exacte vient de `lib_physique._repartir_somme_unique` ; ne jamais la coder en dur. Ne pas ajouter de ligne S6 sans décision explicite et preuve de la source.
6. **Horloge A137** : `horloge_noyau/` est lisible et exécutable, jamais modifiable. Ne rien y écrire.
7. **Valeurs dérivées** : appeler l'algorithme de la source de vérité ; ne pas remplacer un appel par une liste de nombres, même si la somme est correcte.
8. **Livrables** : CSV UTF-8 BOM avec séparateur `;` ; HTML autonome (CSS/JS inline, aucune ressource externe) et strictement aligné sur le CSV.
9. **Date** : le HTML utilise `DATE_GENERATION = date.today().isoformat()`. Ne pas coder la date en dur.
10. **Clé unique** : `SEQ`. `CODE` n'est pas unique (5 doublons S6 hérités) ; ne pas l'utiliser comme clé.
11. **Strates mesurées (S19)** : le script de mesure, `lib_cesium_133.py`, le snapshot et les preuves sont en lecture seule. Ne relancer la mesure que sur demande explicite : elle remplace le snapshot scellé. Toute modification du script de mesure ou de la bibliothèque de calcul impose une nouvelle mesure.
12. **Verrou Monade** : le générateur doit conserver `verifier_snapshot_cesium_133`, `confirmer_harmonie_et_prouver_justesse`, le contrôle `preuve_totale` et le refus `RuntimeError("S19 refusee…")`. Ne jamais commenter, contourner ou remplacer ce verrou par des valeurs figées. Le validateur canonique ne vérifie pas la sémantique de S19 ; les tests ciblés en sont responsables.

## Fichiers et commande de contrôle

- Générateur : `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\generer_tableau_maitre_sequentiel.py`
- CSV : `C:\Users\Administrateur\Desktop\IMAM8MAHDI\TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv`
- HTML : `C:\Users\Administrateur\Desktop\IMAM8MAHDI\TABLEAU_MAITRE_SEQUENTIEL_UNIFIE_IMAM8MAHDI.html`
- Validateur canonique : `C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py`
- Palette de référence : `HUB_PONTS_SYNCHRONES_AL_MIZAN.html` (variables `:root`, lecture seule)

Sources amont (lecture seule) : les 4 tablettes `QUBITS8INFORME/tablette_apprise_{chiffres,alphabet,ponctuation}.csv` et `QUBITS8INFORME/tablettes_apprise_opérateur.csv` (S1–S4), `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_informe.py` (S5, LA TABLE 96 = 2×4×4×3), `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_physique.py` (S6), `ASTRO-Q°ODE_SYSTEME/horloge_noyau/` (A137). Détail et comptes : `references/cartographie-strates.md` § Sources amont.

Chaîne Cs-133 (lecture seule, sauf mesure explicitement demandée) :

- Calcul : `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_cesium_133.py`
- Mesure : `ASTRO-Q°ODE_SYSTEME/outils/mesurer_metriques_cesium_133.py`
- Snapshot scellé : `ASTRO-Q°ODE_SYSTEME/donnees/mesure_quantique_cesium_133.json`
- Tests : `ASTRO-Q°ODE_SYSTEME/tests/test_metriques_cesium_133.py`

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

Codes retour : `0` OK, `1` violation du contrat, `2` entrée manquante ou illisible. `--strict-warnings` transforme les avertissements en échec. `--allow-external` rétrograde le contrôle d'autonomie HTML en avertissement. Les options `--csv`, `--html`, `--generator`, `--lib` et `--lock` permettent de tester une copie sans toucher au dépôt.

## Procédure

### 1. Établir la référence (lecture seule)

Lire, dans cet ordre :

- Le générateur : `add()`, la dernière strate, `DATE_GENERATION`, le commentaire `# Écriture du CSV`.
- Les 4 tablettes `QUBITS8INFORME/` (S1–S4) et `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_informe.py` (S5) : vérifier les libellés avant recopie.
- `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_physique.py` : `_repartir_somme_unique` (source de vérité).
- `ASTRO-Q°ODE_SYSTEME/horloge_noyau/VERROU.json` : confirmer `ecriture: false`.
- `references/cartographie-strates.md` : carte, plages, distribution S6 et exceptions.
- Lancer le validateur pour obtenir l'état de départ.
- S19 : lire la structure réelle du snapshot et les preuves (voir § 3bis) avant de coder le moindre accès.

### 2. Cartographier le contenu

- Nouveau domaine ou lot autonome : nouvelle strate `S<n+1>` en fin de tableau. C'est le choix par défaut, car il préserve les SEQ existantes. S19 est occupée par Cs-133 : la prochaine strate est S20.
- Extension ou correction : ajouter les lignes dans le bloc de la strate. Toutes les SEQ suivantes se décalent ; le signaler dans le rapport.
- `source` obligatoire pour chaque ligne.
- Un lien `matiere`, `terre`, `lune`, `soleil` ou `quantique_bio` quand le contenu s'y prête. Ne pas inventer de lien pour un axiome S0 ou une constante pure ; les exceptions historiques sont documentées dans la référence.
- Ne pas ajouter de matière non scellée à S6 : créer une strate liée à S6.

### 2bis. Images de référence

- Traiter une image jointe comme une spécification de contenu et de colonnes ; ne transcrire que les libellés lisibles.
- Plusieurs images d'un même domaine : une seule strate, colonnes fusionnées ; citer chaque image dans `SOURCE` (ex. `Image Q-BIO Harmonizer`, `Image portes logiques séquentielles`).
- Une image ne fournit jamais une valeur scellée : les magnitudes et constantes restent calculées par `lib_physique.py`.
- Ne pas supposer qu'une image jointe existe dans le dépôt. Si elle n'est plus accessible ou reste illisible, le signaler au lieu de prétendre l'avoir relue.

### 3. Ajouter les entrées

Insérer le bloc après la dernière strate et avant `# Écriture du CSV` :

```python
S20 = "S20 · Thème de la nouvelle strate"
add(S20, "CODE-1", "Famille logique", "Élément",
    "Rôle / description en français",
    matiere="lien avec la strate matière",
    terre="cycle Terre", lune="cycle Lune", soleil="cycle Soleil",
    quantique_bio="lien couche quantique / BIO",
    valeur="valeur ou formule", source="source précise")
```

- Ne pas écrire `SEQ` : `add()` s'en charge.
- Ajouter la clé de couleur exacte dans `COULEURS_STRATE`, sinon le badge est bleu par défaut.
- Mettre à jour le docstring d'en-tête (nombre d'entrées et plage SEQ).
- Conserver l'ordre et la contiguïté des strates.
- La date HTML est dynamique ; ne rien coder en dur.

### 3bis. Chaîne « strate mesurée » (S19 · Cs-133)

Une strate mesurée se dérive d'un snapshot scellé ; elle ne se code jamais à partir de valeurs supposées. Pour la mesure détaillée, suivre `mesure-cesium-133-geolocalisee` ; cette section ne couvre que l'articulation avec le tableau.

1. **Lire la structure réelle du snapshot** avant d'écrire un accès : `metriques.transition`, `metriques.recul`, `metriques.relativite` (gravité, dilatations), `metriques.cycles` (`resolution_python_s`, `precision_windows_s`, `cycles_cesium`), `metriques.position` (provider, `details_altitude.opentopodata_srtm30m`), `metriques.temps`, `metriques.temps_sideral`.
2. **Mesurer uniquement sur demande explicite** : la mesure remplace le snapshot scellé. Commande et options détaillées dans `mesure-cesium-133-geolocalisee`. Sortie attendue : `Monade architecture 9/9 | metriques 23/23 | preuve totale True`.
3. **Vérifier le snapshot indépendamment** : `verifier_snapshot_cesium_133(snapshot, script_mesure)` renvoie le snapshot (dict), pas un verdict. Lire `preuve_totale`, `validation_monade.metriques.controles_ok/controles_total`, `validation_monade.architecture.couches_ok`. Empreintes : `empreinte_contenu_sha256` et `empreinte.script_sha256` (imbriquée).
4. **Insérer via `add()` uniquement** : 19 lignes `CS-01..CS-19` (instantané : SEQ 186–204). Chaque valeur vient du snapshot ; `SOURCE` cite le hash de contenu et celui du script. Conserver le bloc `_PREUVE_TOTALE` et son `RuntimeError` : si le snapshot, les 23 contrôles ou les 9 couches manquent, la génération doit échouer, pas produire un tableau partiel.
5. **Après toute modification du script de mesure ou de `lib_cesium_133.py`**, refaire la mesure puis régénérer. Ne jamais éditer le snapshot, les lignes S19 ou les hashes à la main pour faire passer la génération.

### 4. Traiter les valeurs dérivées

- Utiliser `_repartir_somme_unique` du générateur (copie de `lib_physique.py`) ou l'importer en lecture seule.
- Ne jamais remplacer un appel par des littéraux, même si la somme est correcte.
- S6 : ne pas modifier les totaux 40 / 313 / 63. Le validateur compare la distribution complète, pas seulement la somme.
- S19 : aucune valeur recopiée ; tout est lu du snapshot vérifié (voir § 3bis).
- Vérifier avec le validateur avant de conclure.

### 5. Régénérer

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"
py -3.12 generer_tableau_maitre_sequentiel.py
```

Attendre `OK - N entrees sequentielles - M strates`, puis vérifier que les deux chemins affichés sont ceux de la racine du dépôt.

S19 étant conditionnelle, un snapshot absent ou invalide interrompt la génération : corriger la preuve (voir § 3bis), ne pas contourner le verrou.

Si `UnicodeEncodeError` apparaît, les fichiers ont peut-être déjà été écrits : garder les messages console en ASCII et consulter `verifier-livrables-csv-html-windows-fr`. Ne pas utiliser l'alias `python` de Microsoft Store ; utiliser `py -3.12`.

### 6. Valider

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

Le validateur vérifie : BOM et séparateur CSV, 13 colonnes, champs obligatoires, SEQ `001..N`, strates contiguës et numérotées `S0..S<n>`, S6 (sommes, comptes, distribution, code/magnitude, source), parité de `_repartir_somme_unique` avec `lib_physique.py`, `add()` et son schéma, couleurs, docstring, date dynamique, verrou A137, égalité cellule par cellule CSV/HTML, badges, options, titre, sous-titre, dernière SEQ et autonomie HTML.

Un avertissement n'est pas un échec, mais il doit être corrigé s'il entre dans le périmètre, sinon être signalé.

Le validateur ne couvre pas les sources S1–S5 ni la palette. Vérifier en plus, en lecture seule :

- Tablettes S1–S4 : 19 / 19 / 19 / 9 lignes ; S5 : LA TABLE 96 dans `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_informe.py`.
- Images de référence : appliquer § 2bis (fusion par domaine, libellés cités dans `SOURCE`, aucune valeur scellée déduite d'une image, image inaccessible signalée).
- Palette : les valeurs `:root` du HTML égalent celles de `HUB_PONTS_SYNCHRONES_AL_MIZAN.html` ; les noms de variables diffèrent (alias : `--accent-blue` ↔ `--blue`, `--text-dim` ↔ `--dim`, etc.).

Le validateur contrôle la structure et la parité CSV/HTML de S19, pas sa sémantique. Rejouer les tests ciblés (23 contrôles, 9 couches, refus d'un snapshot altéré et d'une fréquence nulle) :

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"
py -3.12 -m unittest tests.test_metriques_cesium_133 -v
py -3.12 -m unittest tests.test_metriques_cesium_133 tests.test_architecture_poupees_russes_monade tests.test_suite_complete tests.test_incarnation_tripartite_completude tests.test_logique_horloge_synchronisation tests.test_moteur_trinite_temps_physique
```

Attendre 9 tests puis 71 tests `OK`.

Pour le contrôle navigateur, suivre `verifier-livrables-csv-html-windows-fr` ou `validation-navigateur-par-repli` : ouvrir le fichier, exécuter `evaluate_script` avec une fonction fléchée, puis viser une capture par cible — en-tête (N entrées / M strates) et dernières lignes de la strate mesurée — sans boucle de retry. Si le viewport est masqué (`NATIVE_BROWSER_VIEWPORT_UNAVAILABLE`), ne pas réessayer et annoncer une validation structurelle uniquement.

### 7. Rapporter

```text
N entrées · M strates · SEQ 001–N
S6 40/313/63 · 4/7/9 + origine 0 : OK
CSV 13 colonnes / BOM / ; : OK
HTML N lignes · M badges · 13 cellules · contenu = CSV : OK
Autonomie HTML : OK (0 ressource externe)
Mesure Cs-133 : snapshot <sha8>… · script <sha8>… · 9/9 · 23/23 · preuve_totale = true
Visuel : vérifié | non vérifié (viewport masqué)
Fichiers : <chemins absolus>
```

Comparer attendu / observé, citer les chemins, distinguer validation structurelle et visuelle. Pour S19, citer les limites réelles (GPS non certifié, altitude DEM, NTP non TAI/UTC, phase quantique non mesurée).

### 8. Maintenir ce Skill

Appliquer le flux de mise à jour de `skill-creator` : relire ce fichier et `references/cartographie-strates.md`, conserver les règles valides, puis modifier par ajout ciblé. Ne pas réécrire le fichier entier.

- QA de structure après toute édition :

```bash
py -3 "C:\Users\Administrateur\.qoder\skills\skill-file-qa\scripts\validate_skill.py" "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel" --workspace "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

Exiger `RESULT PASS` et 0 FAIL. Un `FAIL local reference not found` signale le plus souvent un chemin local amputé de son préfixe de dépôt.

- Pour les fichiers du dépôt cités en relatif, écrire le chemin complet depuis la racine, par exemple `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_informe.py`. Un chemin réduit au sous-dossier (préfixe `ASTRO-Q°ODE_SYSTEME/` omis) échoue à la QA. Les ressources internes au Skill gardent leurs chemins dans les dossiers `scripts` et `references` ; les commandes de contrôle peuvent garder un chemin absolu.
- Revalider sur les artefacts réels tout compte, plage ou source modifié avant de mettre à jour `references/cartographie-strates.md`.
- Ne pas déclarer la mise à jour terminée avant la QA PASS et la revalidation des faits touchés.

## Pièges observés

| Symptôme | Cause | Correctif |
|---|---|---|
| Sommes 39 / 312 / 62 | valeurs d'état codées en dur | appeler `_repartir_somme_unique`, valider la distribution |
| Sommes correctes mais distribution fausse | seule la somme a été vérifiée | comparer la liste triée à la source scellée |
| SEQ décalée | insertion au milieu ou numéro manuel | nouvelle strate en fin ; `add()` uniquement |
| HTML différent du CSV | CSV édité à la main ou génération partielle | régénérer les deux livrables, relancer le validateur |
| Badge bleu par défaut | clé absente de `COULEURS_STRATE` | ajouter le libellé exact de la strate |
| Docstring obsolète | plage SEQ non mise à jour | mettre à jour le docstring d'en-tête |
| Date figée | date codée en dur | utiliser `DATE_GENERATION = date.today().isoformat()` |
| Ressource externe | CDN, police ou script distant | tout inline ; vérifier avec le validateur |
| `UnicodeEncodeError` cp1252 | flèche, emoji, accent ou caractère cerclé (①) dans un `print()` | messages console ASCII ; `py -3.12` |
| `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE` | viewport in-app masqué | validation structurelle, pas de nouveau screenshot |
| `CODE` utilisé comme clé | doublons S6 hérités | utiliser `SEQ` comme clé unique |
| Lien inventé | règle « un lien partout » mal appliquée | exceptions S0 / constantes pures documentées |
| Image jointe absente du dépôt | libellé non versionné ou illisible | citer l'image dans `SOURCE` ; ne pas inventer ; signaler si elle n'est plus accessible |
| `KeyError: 'gravite_normale_m_s2'` ou `'resolution_python_s'` | clé lue dans le mauvais bloc du snapshot | gravité → `relativite`, résolution → `cycles`, provider/SRTM → `position` |
| `verifie` / `monade_juste` à `None` | `verifier_snapshot_cesium_133` renvoie le snapshot, pas un verdict | lire `preuve_totale` et `validation_monade.*` |
| `KeyError: 'script_sha256'` | empreinte imbriquée | lire `empreinte.script_sha256` ; le hash de contenu est `empreinte_contenu_sha256` |
| `ZeroDivisionError: float division by zero` | fréquence ν0 nulle dans un snapshot altéré | refus fail-closed : `nu0 <= 0` → `structure_valide: False` ; le test doit obtenir Hélium, pas un crash |
| `RuntimeError: S19 refusee` | snapshot/script modifié ou preuve incomplète | refaire la mesure avec le script inchangé ; ne pas contourner le verrou |
| Compteurs 185/19 affichés | docstring ou prompt figés | dériver de `total_entrees()` / `total_strates()` ; mettre à jour après régénération |
| `FAIL local reference not found` dans skill-file-qa | chemin local amputé de son préfixe de dépôt | réécrire le chemin complet depuis la racine, relancer la QA |

## Ressources

- `scripts/verifier_tableau_maitre.py` : validateur déterministe, lecture seule, sortie ASCII, codes 0/1/2.
- `references/cartographie-strates.md` : carte S0–S19, plages, distribution S6, S19 (mesure, preuves, limites), règles et exceptions.
- `mesure-cesium-133-geolocalisee` : re-mesure, vérification du snapshot et double preuve Monade ; complément de § 3bis.
- `skill-file-qa` : QA de structure après édition du Skill (frontmatter, références locales et inter-Skills, blocs de code).
- `verifier-livrables-csv-html-windows-fr` : chaîne Windows FR (stdout ASCII, CSV BOM/`;`, `evaluate_script`, repli viewport).
- `validation-navigateur-par-repli` : repli navigateur si le screenshot échoue.
- `maj-tableau-maitre-sequentiel` : Skill de compatibilité conservé ; ne pas le supprimer sans décision explicite.

## Définition de terminé

- [ ] Contenu rattaché à une strate, avec `source`, et un lien quand il existe (exceptions documentées).
- [ ] Générateur modifié via `add()` ; docstring et couleur à jour ; aucun livrable édité à la main.
- [ ] CSV et HTML régénérés ; résumé ASCII attendu.
- [ ] Validateur : 0 échec ; avertissements expliqués ou corrigés.
- [ ] S6 : 40/313/63, comptes 4/7/9 + origine 0, distribution identique à `lib_physique.py`.
- [ ] S19 (si touchée) : snapshot SHA-256 valide, script de mesure inchangé, `preuve_totale = true`, 9/9 + 23/23, verrou du générateur intact.
- [ ] S19 : tests ciblés verts (9 puis 71) ; limites de mesure citées dans le rapport.
- [ ] Sources S1–S5 vérifiées : tablettes 19/19/19/9, LA TABLE 96, chemins complets.
- [ ] Images de référence traitées selon § 2bis : fusion par domaine, libellés dans `SOURCE`, aucune valeur scellée déduite, image inaccessible signalée.
- [ ] Palette : valeurs `:root` du HTML égales à celles de `HUB_PONTS_SYNCHRONES_AL_MIZAN.html` (alias de noms).
- [ ] HTML : N lignes, M badges, 13 cellules, contenu = CSV, 0 ressource externe.
- [ ] Rapport avec N, M, plage SEQ, S6, contrôle HTML, hashes de mesure S19, chemins et statut visuel réel.
- [ ] Si le Skill a été modifié : `skill-file-qa` PASS (0 FAIL), aucune référence locale abrégée, faits modifiés revalidés.
- [ ] Aucune écriture dans `horloge_noyau/`, les bibliothèques scellées, le snapshot Cs-133, le CSV ou le HTML à la main.
