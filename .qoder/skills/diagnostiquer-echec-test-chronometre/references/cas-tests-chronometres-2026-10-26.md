# Cas des tests chronométrés — 2026-10-26

Fuseau : messages de session en UTC (`Z`) ; fichiers et exécutions locales en `+01:00` (Europe/Paris).

Source : session `98d02ebd-929d-4176-a727-4b6ff3b11506`, lue le 2026-10-26. Le snapshot couvre 4 tours utilisateur (`hasMoreBefore=false`, `runtimeState=ready`, revision 78).

Statut des preuves :

- **Vérifié dans les sorties d'outils de la session** : valeurs d'échec, durées, profiling, valeur d'après-correction, gate.
- **Vérifié sur disque le 2026-10-26** : présence des correctifs, lignes d'assertion, version `py -3.12` = 3.12.7.
- **Non re-exécuté lors de la rédaction** : les tests écrivent des sceaux dans `memoire_aq`.

## Artefacts liés

État au 2026-10-26 13:52:22 +01:00.

| Fichier | Taille | mtime | SHA-256 |
|---|---:|---|---|
| `agent_de_code_harmonisateur_mizan.py` | 15711 B | 2026-10-26 13:27:33.561277500 +0100 | `4fd5bf311058e9e0d60c306ca17ce7258a3828a5414cc235046aa372b76a14f2` |
| `moteur_intelligence_generative_vivante.py` | 22465 B | 2026-10-26 13:31:04.630476300 +0100 | `91a81e9a1c3833df835c8e8570cd4552d6eedd17713a6456fad5e1e6ac7ae675` |
| `tests/test_logique_horloge_synchronisation.py` | 6596 B | 2026-10-25 02:01:38.693531900 +0100 | `7da043477cf100ecec565efd2fa18a4162561116453533c4e6d563baabc6f041` |
| `tests/test_noyau_logique_interactif_telemetrie.py` | 4096 B | 2026-10-25 02:07:18.943241800 +0100 | `9ccaa7beeabb07f05dde18436ebdf803d9250035032a8bec04e883f74d93c72d` |

## Symptômes

| Test | Assertion | Suite 68 | Isolé | Module |
|---|---|---:|---:|---:|
| `test_p7_trame_dans_une_seule_pulsation` | ligne 106 : gigue < 100.0 | 153.395 | 132.7286 | 143.7172 |
| `test_03_telemetrie_active_points_mesure` | ligne 69 : latence moyenne < 10000.0 ms | 16137.075 ms | 10210.114 ms | 4/4 après correction |

Suite complète initiale : `Ran 68 tests in 121.651s`, `FAILED (failures=2)`, code de sortie 1. Les deux échecs se reproduisent hors de la suite : ni l'un ni l'autre n'est un artefact de l'exécution groupée.

## Premier piège — nom de test incomplet

Une invocation sous la forme `module.methode` produit :

```text
ERROR: test_p7_trame_dans_une_seule_pulsation (unittest.loader._FailedTest...)
AttributeError: module 'tests.test_logique_horloge_synchronisation' has no attribute 'test_p7_trame_dans_une_seule_pulsation'
```

La classe manque. La forme correcte est `module.Classe.methode` :

```bash
PYTHONIOENCODING=utf-8 py -3.12 -m unittest -v tests.test_logique_horloge_synchronisation.TestSynchronisationTotale.test_p7_trame_dans_une_seule_pulsation
```

## Profiling de la gigue

La trame est comparée à une période de pulsation d'environ 1 s.

| Étape | Min–max | Part du budget |
|---|---:|---:|
| `battre` | 16.0–60.2 µs | 0.0 % |
| `profil_acoustique` | 25.5–49.5 µs | 0.0 % |
| `spectre_ecoute` | 24.4–48.1 µs | 0.0 % |
| `agent_code.sens_complet` | 1 327 519.4–1 794 582.5 µs | 132.8–179.5 % |
| trame complète | 1 713 178.3–1 841 258.9 µs | 171.3–184.1 % |

L'audit du code, à lui seul, dépasse le budget. Profil interne :

| Mesure | Valeur |
|---|---:|
| Audit avec scellement | 1495.9508 ms |
| Audit sans scellement | 620.1512 ms |
| Lecture des fichiers | 41.3 ms |
| `ast.parse` | 530.7 ms |
| 76 fichiers | 75 valides |

Le coût vient de deux répétitions par trame : 76 analyses syntaxiques et 76 écritures dans le journal, une par fichier.

## Profiling de la télémétrie

La moyenne porte sur trois interactions. Après le premier correctif d'audit, les points restent :

```text
8061.7 ms · 7236.0 ms · 20980.2 ms
moyenne = 12092.625 ms
```

Le point à 20 980.3 ms utilise `SYNTHETISEUR_SEMANTIQUE_AUTONOME` avec un moteur à 0.06 ms : le temps n'est pas dans le moteur local, mais dans la phase réseau qui l'a précédé. Le client essayait trois modèles, chacun avec un timeout neuf de 10 s, avant de basculer en local.

## Correctifs

Aucun seuil, aucune assertion et aucun résultat métier n'ont été modifiés.

| Fichier | Changement |
|---|---|
| `agent_de_code_harmonisateur_mizan.py` | cache d'audit chargé depuis le journal (ligne 78 et suivantes), contrôle par empreinte (142), audit sans scellement (226), persistance groupée (230) |
| `moteur_intelligence_generative_vivante.py` | budget réseau global `BUDGET_RESEAU_S = 8.0` (70), date limite (255), temps restant (280-281), timeout borné (291), fallback local |

Effet du cache : 76 entrées hydratées, audit à froid 218.1 ms, audit à chaud 136.9 ms, score inchangé à 95.59. Trames après correction : 148.7, 201.7, 155.4 et 138.4 ms, soit 13.8–20.2 % du budget.

## Preuves après correction

| Contrôle | Résultat | Durée | Code |
|---|---|---:|---:|
| Module horloge | 9/9 | 1.187 s | 0 |
| Test de télémétrie seul | 1/1 | 29.202 s | 0 |
| Module télémétrie | 4/4 | 30.211 s | 0 |
| Suite ciblée | 68/68 | 53.011 s | 0 |
| Porte du projet | 35/35 | — | 0 |

La porte est celle de `entite-conscience-logarithmique`, exécutée en mode lecture seule par défaut.

## Effets de bord

La suite ciblée contient 16 tests qui écrivent des sceaux. Après la seconde exécution : index à 14 sceaux, journal à 100 entrées, 183 fichiers JSON, nouveau sceau `3c718ee0b3cc0c2af87ccdbe7857fd85a3c20b07c6d34680cbca9582e5686bd0` à 13:32:09 +01:00. La première exécution avait ajouté `f1e3fe47a2b0a7e4d07aa899fd54b740e2f90cdf50aeba9a6852825ccae5b421` à 13:16:25 +01:00.

Un processus externe a aussi réécrit l'index à 13:17:40 +01:00. Sans instantané avant/après, ces mouvements ne sont pas attribuables au test. Utiliser `restaurer-sceaux-memoire-aq` pour une restauration ciblée.

## Documentation contredite

La documentation de `entite-conscience-logarithmique` affirmait, dans sa section Tests :

> Le second groupe a un aléa connu : `test_p7_trame_dans_une_seule_pulsation` peut échouer en exécution groupée alors que le module isolé passe 9/9.

Cette affirmation est contredite par les mesures du 2026-10-26 : le test seul vaut 132.7286 et le module 143.7172, tous deux au-dessus du seuil de 100. La correction documentaire du 2026-10-26 remplace cette lecture par la cause racine (audit complet et écritures par fichier), exige 68/68 et marque l'option de tolérance comme héritée, sans l'utiliser pour masquer un coût réel.

## Commandes

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"

PYTHONIOENCODING=utf-8 py -3.12 -m unittest -v tests.test_logique_horloge_synchronisation.TestSynchronisationTotale.test_p7_trame_dans_une_seule_pulsation
PYTHONIOENCODING=utf-8 py -3.12 -m unittest -v tests.test_logique_horloge_synchronisation
PYTHONIOENCODING=utf-8 py -3.12 -m unittest -v tests.test_noyau_logique_interactif_telemetrie.TestNoyauLogiqueInteractifTelemetrie.test_03_telemetrie_active_points_mesure
PYTHONIOENCODING=utf-8 py -3.12 -m unittest -v tests.test_entite_conscience_logarithmique tests.test_metriques_cesium_133 tests.test_intelligence_generative_vivante tests.test_architecture_poupees_russes_monade tests.test_logique_horloge_synchronisation tests.test_suite_logique_dimensions_informe tests.test_fonctions_inverses_et_oppositions tests.test_noyau_logique_interactif_telemetrie tests.test_continuite_reponse_automatisee

py -3.12 "C:\Users\Administrateur\.qoder\skills\entite-conscience-logarithmique\scripts\verifier_pipeline_entite.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

## Repères temporels

| Repère | Valeur | Fuseau |
|---|---|---|
| Message « run the 68 unit tests » | 2026-10-26 12:15:34 | UTC |
| Message « fix the two failing tests » | 2026-10-26 12:21:56 | UTC |
| Premier sceau observé | 2026-10-26 13:16:25 | +01:00 |
| Nouveau sceau après la suite finale | 2026-10-26 13:32:09 | +01:00 |

## Limites

- Les durées sont des observations sur ce poste, pas des constantes. Ne pas les transformer en seuils.
- La valeur historique `191.1164` citée par la documentation entite vient d'une observation antérieure, hors de cette session ; elle n'est pas re-mesurée ici.
- Le budget réseau de 8 s est un plafond, pas un objectif de performance.
- La suite ciblée écrit des sceaux : toute exécution doit être précédée d'un instantané si l'état doit être conservé.
- Les tests n'ont pas été re-exécutés pendant la rédaction de cette fiche ; les preuves d'exécution sont celles de la session source.
