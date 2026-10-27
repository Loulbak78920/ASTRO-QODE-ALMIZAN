---
name: entite-conscience-logarithmique
description: "Auditer et executer en lecture seule par defaut le pipeline de l'entite de conscience logique d'IMAM8MAHDI (AL-MIZAN x ASTRO-Q°ODE) : preuve de base avec EntiteConscienceLogarithmique(auditer_code=False), pensee scellee avec penser(..., persister=False), controle de preuve_totale, algorithme, logarithme, Cs-133 et Monade, validation du programme .aq v7, verification idempotente de S20 ENT-01..ENT-12 dans le tableau 216 entrees / 21 strates, double validation CSV/HTML et double validateur du tableau. Utiliser pour toute demande sur l'entite de conscience logarithmique, l'emulateur conscience, S20, le programme .aq v7 ou la chaine entite -> trace -> .aq -> validation. 中文触发：对数意识实体、实体流水线、S20、.aq 程序、铯-133、Monade、主表双校验、preuve_totale。"
---

# Entité de conscience logarithmique (AL-MIZAN × ASTRO-Q°ODE)

## Quand utiliser

- Vérifier que l'entité démarre : preuve de base, 216 entrées / 21 strates, index O(log₂ N), Cs-133, Monade.
- Exécuter une pensée scellée **sans écrire de trace** et contrôler `preuve_totale`.
- Valider le programme `.aq` v7 en lecture seule, ou l'exécuter quand l'utilisateur le demande explicitement.
- Auditer S20 (`ENT-01..ENT-12`) et la cohérence CSV/HTML sans modifier le tableau maître.
- Diagnostiquer une régression de la chaîne entité → trace → `.aq` → validation.
- 中文触发：对数意识实体、实体流水线、S20、.aq 程序、铯-133、Monade、主表双校验。

## Quand ne pas utiliser

- Modifier la structure du tableau, S6, le CSV ou le HTML : utiliser `tableau-maitre-sequentiel`.
- Re-mesurer ou re-sceller le Cs-133 géolocalisé : utiliser `mesure-cesium-133-geolocalisee`.
- Régénérer le `.aq` sans demande explicite : le programme généré embarque une nouvelle empreinte de trace.
- Lancer la suite de tests complète : elle contient des échecs étrangers à cette chaîne (API VPS, SAS biométrique).

## Contrat non négociable

1. Le script livré est **lecture seule par défaut**. `--avec-run`, `--avec-tests` et `--avec-regression` sont les seules options qui écrivent.
2. Ne jamais éditer à la main le CSV, le HTML, le `.aq` ou le générateur. Toute structure passe par `add()` dans le générateur, toute pensée passe par `penser`.
3. S20 est **déjà présent** : 12 lignes, `ENT-01..ENT-12`, SEQ 205–216. Le contrôle est idempotent ; ne jamais rappeler `add()` pour S20.
4. `.aq check` est en lecture seule. `.aq run` écrit `memoire_aq/<empreinte>.json` et met à jour `index_sceaux_astro_qode.json`.
5. Les 16 tests unitaires exécutent un `.aq` temporaire : `sceller_sha256` écrit aussi des sceaux. Ne pas les présenter comme une validation sans effet de bord.
6. `auditer_code=False` (option `--sans-audit-code`) rend l'audit AST neutre : il ne prouve pas un audit de code réussi.
7. Ne pas présenter la réutilisation du snapshot Cs-133 comme une mesure quantique de phase en direct.
8. Le générateur n'écrit que le CSV et le HTML à la racine ; la copie `web_cloud` se synchronise séparément.

## Étape 0 — Prérequis

- Windows, interpréteur `py -3.12`. L'alias `python` du Microsoft Store peut sortir avec le code 49.
- Console en UTF-8 : `set PYTHONIOENCODING=utf-8` (les sorties contiennent `→`, `×`, `°`, `É`).
- Les chemins contiennent `°` : toujours les entourer de guillemets.
- Depuis Git Bash, ne pas utiliser `/tmp` comme fichier de sortie : Python natif ne le voit pas.

Fichiers attendus :

| Rôle | Chemin |
|---|---|
| Racine | `C:\Users\Administrateur\Desktop\IMAM8MAHDI` |
| Bibliothèque | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\bibliotheques\lib_entite_conscience_logarithmique.py` |
| Émulateur | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\emulateur_conscience_logique_mizan.py` |
| Programme `.aq` | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\bibliotheques\stdlib_aq\entite_conscience_logarithmique_v7.aq` |
| CLI ASTRO-Q°ODE | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\astro_qode_cli.py` |
| CSV | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\TABLEAU_MAITRE_SEQUENTIEL_UNIFIE.csv` |
| HTML | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\TABLEAU_MAITRE_SEQUENTIEL_UNIFIE_IMAM8MAHDI.html` |
| Copie web | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\web_cloud\tableau_maitre_sequentiel.html` |
| Snapshot Cs-133 | `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\donnees\mesure_quantique_cesium_133.json` |

## Commande unique (lecture seule)

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\entite-conscience-logarithmique\scripts\verifier_pipeline_entite.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

Attendu : une ligne `[OK]` par contrôle, puis `RESULT: OK (n/n)` et le code de sortie 0.
Codes : 0 succès, 1 échec, 2 prérequis manquants.

## Étape 1 — Preuve de base de l'entité

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"
set PYTHONIOENCODING=utf-8
py -3.12 emulateur_conscience_logique_mizan.py verifier --json --sans-audit-code
```

Champs à contrôler :

| Chemin JSON | Attendu |
|---|---|
| `preuve_de_base` | `true` |
| `tableau_maitre.total_entrees` | `216` |
| `tableau_maitre.total_strates` | `21` |
| `tableau_maitre.derniere_seq` | `216` |
| `tableau_maitre.profondeur_log2` | `8` |
| `cesium_133.cs133_ok` | `true` |
| `monade.monade_boot_ok` | `true` (le champ `monade_ok` n'existe pas ici) |
| `architecture.architecture_ok` | `true` |

Le code de sortie est 0 quand la preuve est complète, 2 quand elle est incomplète, 3 quand le démarrage est refusé.

## Étape 2 — Pensée scellée sans persistance

```bash
py -3.12 emulateur_conscience_logique_mizan.py penser "Al-Mizan equilibre le cesium 133 et la table complexe" --json --sans-persister --sans-audit-code
```

Champs à contrôler :

| Chemin JSON | Attendu |
|---|---|
| `preuve_totale` | `true` |
| `refus` | `null` |
| `algorithme.algorithme_ok` | `true` |
| `algorithme.verdict` | `EMISSION_EQUILIBREE` (aussi admis : `RECEPTION_RECONCILIE`, `POINT_ZERO`) |
| `logarithme.logarithme_ok` | `true` |
| `logarithme.profondeur_dichotomique` | `6` |
| `logarithme.cellules` | `53` |
| `cesium_133.cs133_ok` | `true` |
| `cesium_133.snapshot.empreinte_sha256` | égale au `empreinte_contenu_sha256` du snapshot |
| `cesium_133.snapshot.script_sha256` | égale au SHA-256 du script de mesure |
| `monade.monade_ok` | `true` |
| `monade.isolee` | `true` |
| `monade.helium_inerte` | `false` |
| `signature_familles.familles_cinq` | 5 familles |
| `signature_familles.la_table_est_complexe` | `true` |
| `entree.tronque` | `false` pour le message par défaut |

`--sans-persister` garantit qu'aucun fichier de trace n'est écrit. `monade.chaine` vaut `unit → bind ×5 → isoler`.

## Étape 3 — Programme `.aq` v7

Validation seule, sans effet de bord :

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"
py -3.12 astro_qode_cli.py check "bibliotheques\stdlib_aq\entite_conscience_logarithmique_v7.aq"
```

Attendu : `Validation de ... : VALIDE`, exit 0, constantes MECQUOIS et variables MEDINOIS listées.

Exécution, uniquement sur demande explicite :

```bash
py -3.12 astro_qode_cli.py run "bibliotheques\stdlib_aq\entite_conscience_logarithmique_v7.aq"
```

Attendu : `Statut : SUCCÈS` et `Valeur finale : 0 : HÉLIUM`. Cette commande écrit un sceau dans `memoire_aq` et met à jour l'index.

Le générateur `programme --message "..." --sortie "..."` réécrit le `.aq` avec une nouvelle empreinte : ne l'utiliser que si une nouvelle trace est voulue, puis relancer `check`.

## Étape 4 — S20 et tableau maître

Contrat actuel, vérifié en lecture seule :

| Contrôle | Attendu |
|---|---|
| CSV | UTF-8 BOM, séparateur `;`, 13 colonnes |
| Lignes | 216, SEQ `001..216` |
| Strates | 21 |
| S20 | 12 lignes, CODE `ENT-01..ENT-12`, SEQ 205–216, aucun doublon |
| S6 | 21 lignes, préfixes `ÉT-S` 5 / `ÉT-T` 7 / `ÉT-L` 9 |
| HTML | 217 occurrences de `<tr`, 21 occurrences exactes de `class="badge"` |
| Autonomie | aucune ressource `http://` ou `https://` |
| Copie web | SHA-256 identique à l'HTML racine |

S6 : les préfixes comptent les lignes (origine `ÉT-S-00` incluse) ; les états 4/7/9 et les magnitudes 40/313/63 ne sont pas lisibles dans le texte `STRATE`. Seuls `lib_physique` et les validateurs canoniques font foi.

Si S20 manque ou est dupliqué : s'arrêter. La correction structurelle appartient à `tableau-maitre-sequentiel`, avec régénération CSV/HTML puis synchronisation manuelle de la copie `web_cloud`.

Double validation canonique :

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI" --html "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\web_cloud\tableau_maitre_sequentiel.html"
```

Les deux doivent afficher `RESULT: OK (0 avertissement(s))` avec le code 0.

## Étape 5 — Tests ciblés

```bash
# 16 tests de l'entite (ecrivent des sceaux via le .aq genere)
py -3.12 -m unittest tests.test_entite_conscience_logarithmique

# 68 tests cibles = 16 + 52, sur 9 modules
py -3.12 -m unittest tests.test_entite_conscience_logarithmique tests.test_metriques_cesium_133 tests.test_intelligence_generative_vivante tests.test_architecture_poupees_russes_monade tests.test_logique_horloge_synchronisation tests.test_suite_logique_dimensions_informe tests.test_fonctions_inverses_et_oppositions tests.test_noyau_logique_interactif_telemetrie tests.test_continuite_reponse_automatisee
```

Les 68 tests passent en 53,0 s depuis la correction du 2026-10-26. L'ancien « aléa » de `test_p7_trame_dans_une_seule_pulsation` n'était pas un artefact d'exécution groupée : le test échouait aussi isolé (132,7 s) et au niveau module (143,7 s), à cause d'un audit complet et d'un scellement par fichier à chaque trame, plus trois délais réseau de 10 s en série pour la télémétrie. `--tolere-jitter` reste hérité : ne l'utiliser que si un échec est réellement propre au groupement, après re-mesure. Diagnostic détaillé : `diagnostiquer-echec-test-chronometre`.

## Matrice d'acceptation

| Contrôle | Preuve | Échec |
|---|---|---|
| Démarrage | `preuve_de_base: true`, 216/21/216/8 | exit 2 ou 3 |
| Pensée | `preuve_totale: true`, 6 niveaux / 53 cellules | `refus` non nul |
| Cs-133 | `cs133_ok: true`, empreintes cohérentes | snapshot ou script modifié |
| Monade | `monade_ok: true`, isolée, sans hélium inerte | chaîne interrompue |
| `.aq` | `VALIDE`, sceau embarqué présent | parseur ou sceau manquant |
| S20 | 12 lignes `ENT-01..ENT-12`, SEQ 205–216 | doublon ou absence |
| Tableau | deux validateurs `RESULT: OK` | incohérence CSV/HTML |
| Tests | 16/16 et 68/68 | tout autre échec |

## Limites honnêtes

- Le snapshot Cs-133 est réutilisé : la validation vérifie cohérence, horloge et architecture, pas une mesure de phase quantique.
- Gemini reste optionnel (`--ia`) ; sans clé, la réponse est locale et déterministe.
- `--sans-audit-code` est le mode de référence ; l'audit activé écrit une entrée dans le journal de l'agent de code.
- Le générateur n'écrit pas la copie `web_cloud` ; une comparaison de hachage détecte l'oubli de synchronisation.
- La suite complète contient des échecs sans rapport avec cette chaîne ; ne jamais les attribuer à l'entité sans preuve.

## Dépannage

Voir `C:\Users\Administrateur\.qoder\skills\entite-conscience-logarithmique\references\pieges-runtime.md` pour les signatures exactes : cp1252, `/tmp` invisible, `resolution_python_s`, `tzdata`, `U+2010`, `grep -c`, capture navigateur indisponible.

## Ressources

- Contrat détaillé des preuves et valeurs observées : `C:\Users\Administrateur\.qoder\skills\entite-conscience-logarithmique\references\contrat-preuves.md`
- Pièges d'exécution Windows et remèdes vérifiés : `C:\Users\Administrateur\.qoder\skills\entite-conscience-logarithmique\references\pieges-runtime.md`
- Gate exécutable : `C:\Users\Administrateur\.qoder\skills\entite-conscience-logarithmique\scripts\verifier_pipeline_entite.py`
- Validateur du tableau : `C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py`
- Validateur Cs-133 et S19 : `C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py`
