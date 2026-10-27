# Contrat des preuves — entité de conscience logarithmique

Toutes les commandes supposent Windows, `py -3.12` et `PYTHONIOENCODING=utf-8`.
Les valeurs marquées « observé » sont datées du 2026-10-26 et peuvent évoluer si le snapshot ou le `.aq` est régénéré.

## 1. Preuve de base

Commande :

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"
py -3.12 emulateur_conscience_logique_mizan.py verifier --json --sans-audit-code
```

| Chemin | Attendu | Remarque |
|---|---|---|
| `preuve_de_base` | `true` | preuve globale |
| `tableau_maitre.total_entrees` | `216` | |
| `tableau_maitre.total_strates` | `21` | |
| `tableau_maitre.derniere_seq` | `216` | |
| `tableau_maitre.profondeur_log2` | `8` | `ceil(log2(216))` |
| `tableau_maitre.tokens_indexes` | `1756` | observé |
| `cesium_133.cs133_ok` | `true` | |
| `monade.monade_boot_ok` | `true` | le champ s'appelle `monade_boot_ok`, pas `monade_ok` |
| `architecture.architecture_ok` | `true` | |

Codes de sortie de l'émulateur : `0` preuve complète, `2` preuve incomplète, `3` démarrage refusé.

`--sans-audit-code` est le mode de référence. Sans cette option, l'agent de code audite l'AST et ajoute une entrée dans `memoire_aq/almizan_journal_agent_de_code.json` (liste plafonnée à 100 entrées, la plus ancienne sortant à chaque ajout).

## 2. Pensée scellée

Commande :

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"
py -3.12 emulateur_conscience_logique_mizan.py penser "Al-Mizan equilibre le cesium 133 et la table complexe" --json --sans-persister --sans-audit-code
```

| Chemin | Attendu |
|---|---|
| `preuve_totale` | `true` |
| `refus` | `null` |
| `algorithme.algorithme_ok` | `true` |
| `algorithme.verdict` | `EMISSION_EQUILIBREE` (admis : `RECEPTION_RECONCILIE`, `POINT_ZERO`) |
| `logarithme.logarithme_ok` | `true` |
| `logarithme.profondeur_dichotomique` | `6` |
| `logarithme.cellules` | `53` |
| `cesium_133.cs133_ok` | `true` |
| `cesium_133.snapshot.empreinte_sha256` | égale à `empreinte_contenu_sha256` du snapshot |
| `cesium_133.snapshot.script_sha256` | égale au SHA-256 de `outils/mesurer_metriques_cesium_133.py` |
| `monade.monade_ok` | `true` |
| `monade.isolee` | `true` |
| `monade.helium_inerte` | `false` |
| `monade.chaine` | `unit → bind ×5 → isoler` |
| `signature_familles.familles_cinq` | `NUMERIQUE`, `LINGUISTIQUE`, `TYPOGRAPHIQUE`, `ALGORITHMIQUE`, `COMPLEXE` |
| `signature_familles.la_table_est_complexe` | `true` |
| `entree.tronque` | `false` pour le message par défaut ; `true` au-delà de 2048 caractères |

`--sans-persister` empêche l'écriture de la trace. Sans cette option, la trace et `derniere_trace.json` sont écrits sous `memoire_aq/entite_conscience_logarithmique/`.

## 3. Snapshot Cs-133

Deux empreintes différentes coexistent :

| Nom | Emplacement | Valeur observée |
|---|---|---|
| Empreinte de contenu | `empreinte_contenu_sha256` dans le snapshot | `8fb08b28d390796192d5cf738f3e6e09cb59d5c2321a7b861f746cb8d2c3016b` |
| SHA-256 du fichier | calcul direct sur le fichier | `e685fc98585e0075b70fe48c3e308c9571c0235f3756b6578c5e3616f616aed0` |
| SHA-256 du script de mesure | `empreinte.script_sha256` | `bfb95373f1557874be30c510667fd8348e5f05fcd959efcdc57fc538d0248da0` |

La preuve de la pensée porte sur **l'empreinte de contenu**. Ne jamais comparer `cesium_133.snapshot.empreinte_sha256` au SHA-256 brut du fichier.

`metriques.temps` et `metriques.cycles` contiennent chacun `resolution_python_s` ; ce champ n'existe pas à la racine de `metriques`.

## 4. Programme `.aq`

| Opération | Commande | Effet | Attendu |
|---|---|---|---|
| Validation | `py -3.12 astro_qode_cli.py check "bibliotheques\stdlib_aq\entite_conscience_logarithmique_v7.aq"` | aucun | `VALIDE`, exit 0 |
| Exécution | `py -3.12 astro_qode_cli.py run "bibliotheques\stdlib_aq\entite_conscience_logarithmique_v7.aq"` | écrit un sceau + index | `Statut : SUCCÈS`, `Valeur finale : 0 : HÉLIUM` |

L'en-tête du `.aq` observé contient `Preuve totale : True` et `SHA-256 : 328357e9b4f92e2baf5cc5df31959bd645f4255aee0de48ec9b5501b308da5ba`. Cette empreinte correspond au sceau `memoire_aq\328357e9b4f92e2baf5cc5df31959bd645f4255aee0de48ec9b5501b308da5ba.json`.

`run` appelle `sceller_sha256`, qui écrit `memoire_aq/<empreinte>.json` et met à jour `memoire_aq/index_sceaux_astro_qode.json` (`nb_sceaux`, `derniere_mise_a_jour`). Le même effet se produit dans les tests qui exécutent un `.aq` généré.

## 5. Tableau maître

| Contrôle | Attendu |
|---|---|
| Encodage CSV | UTF-8 avec BOM |
| Séparateur | `;` |
| Colonnes | 13 : `SEQ`, `STRATE`, `CODE`, `FAMILLE_LOGIQUE`, `ELEMENT`, `ROLE_DESCRIPTION`, `INTERACTION_MATIERE`, `CYCLE_TERRE`, `CYCLE_LUNE`, `CYCLE_SOLEIL`, `COUCHE_QUANTIQUE_BIO`, `VALEUR_SCELLEE`, `SOURCE` |
| Lignes | 216 |
| SEQ | `001` à `216`, sans trou |
| Strates | 21 valeurs distinctes |
| S20 | 12 lignes, `CODE` = `ENT-01..ENT-12`, `SEQ` = 205..216 |
| S6 | 21 lignes, préfixes `ÉT-S` = 5, `ÉT-T` = 7, `ÉT-L` = 9 |
| HTML | 217 occurrences de `<tr`, 21 occurrences exactes de `class="badge"` |
| HTML externe | aucune URL `http://` ou `https://` |
| Copie web | SHA-256 identique à l'HTML racine |

S6 inclut l'origine `ÉT-S-00` : 5 + 7 + 9 = 21 lignes. Les états 4/7/9 et les magnitudes 40/313/63 ne sont pas dans le texte `STRATE` ; seuls les validateurs canoniques les vérifient.

S20 est déjà présent. Un second passage de `add()` produirait 24 lignes et des doublons `ENT-*` : c'est un échec, pas une mise à jour.

## 6. Validateurs canoniques

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI" --html "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME\web_cloud\tableau_maitre_sequentiel.html"
py -3.12 "C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

| Validateur | Marqueur de succès |
|---|---|
| Tableau, HTML racine | `RESULT: OK (0 avertissement(s))` |
| Tableau, copie `web_cloud` | `RESULT: OK (0 avertissement(s))` |
| Cs-133 / S19 | `OK - mesure Cs-133 verifiee`, 23/23, 9/9 stockée + 9/9 live, S19 19 lignes, 216/21 |

## 7. Tests ciblés

| Groupe | Commande | Nombre | Effet de bord |
|---|---|---|---|
| Entité | `py -3.12 -m unittest tests.test_entite_conscience_logarithmique` | 16 | exécute un `.aq` et écrit des sceaux |
| Ciblé | 9 modules listés dans le SKILL.md | 68 = 16 + 52 | idem + mesure de durée et délais réseau |

Le test `test_p7_trame_dans_une_seule_pulsation` a échoué en groupé (153,4 s), isolé (132,7 s) et au niveau module (143,7 s) le 2026-10-26 : ce n'était pas un aléa de groupement. Causes corrigées : audit complet et scellement du journal fichier par fichier à chaque trame, puis trois délais réseau de 10 s en série. Après correction : module 9/9 en 1,187 s, 68/68 en 53,0 s. Ne jamais modifier le seuil ; procédure de diagnostic dans `diagnostiquer-echec-test-chronometre`.

## 8. Gate `verifier_pipeline_entite.py`

| Option | Effet |
|---|---|
| `--root` | racine du dépôt (défaut : bureau IMAM8MAHDI) |
| `--json` | ajoute un résumé JSON des contrôles |
| `--sans-web-cloud` | n'exige pas la copie web |
| `--strict-warnings` | tout `[WARN]` fait échouer le résultat |
| `--avec-run` | exécute le `.aq` (écrit un sceau) |
| `--avec-tests` | exécute les 16 tests (écrit des sceaux) |
| `--avec-regression` | exécute les 68 tests ciblés |
| `--tolere-jitter` | hérité : dégrade `test_p7` après re-exécution isolée réussie ; ne pas s'en servir sans re-mesure, l'échec observé touchait aussi le module |
| `--message` | texte pensé (défaut : message de référence) |
| `--table-validator`, `--cs133-validator` | chemins des validateurs |

Codes de contrôle affichés : `PREREQ`, `ENT-*`, `PENSEE-*`, `AQ-*`, `CSV-*`, `HTML-*`, `VALID-TABLEAU-*`, `VALID-CS133`, `TESTS-*`, `RUN-*`, `SIDE-EFFECT-*`.

Sortie finale : `RESULT: OK (n/n)` avec exit 0, ou `RESULT: FAIL (k/n)` avec exit 1 ; prérequis manquants : exit 2.

## 9. Valeurs observées le 2026-10-26

| Élément | Valeur |
|---|---|
| Tableau | 216 entrées, 21 strates, SEQ 001–216 |
| S20 | 12 lignes, SEQ 205–216 |
| Index HTML / CSV | 217 `<tr` / 216 lignes |
| Pensée de référence | `preuve_totale: true`, 6 niveaux, 53 cellules |
| Sceau `.aq` | `328357e9b4f92e2baf5cc5df31959bd645f4255aee0de48ec9b5501b308da5ba` |
| Snapshot (contenu) | `8fb08b28d390796192d5cf738f3e6e09cb59d5c2321a7b861f746cb8d2c3016b` |
| Index des sceaux | 12 entrées après restauration, dernière mise à jour `2026-10-26T11:01:17` |
