# Dossier de preuve — découverte `unittest` Al-Mizan (2026-10-27)

## Provenance

- Session source : `55f63550-7c8d-4f9e-b0a9-e73686cc2765`, titre « Mettre à jour le site web ».
- État à la lecture : `runtimeState: ready`, `activeTurnId: null`, `queuedTurnCount: 0`, `pendingInteractionCount: 0`, `revision: 1134`, `hasMoreBefore: true`.
- Lecture : `read_chat_session` avec `turnLimit: 12`, `includeToolOutputs: true`, `maxOutputCharsPerItem: 4000`.
- Réponse MCP supérieure à 25 000 tokens, enregistrée dans :
  `C:\Users\Administrateur\.qoder\tmp\C--Users-Administrateur-Desktop-IMAM8MAHDI\56fad23c-1804-4432-978c-471f9def4ce0\tool-results\builtin_read_chat_session_ec0d0cf9e40e.txt`
- SHA-256 du snapshot : `ec0d0cf9e40e9f46ec89f2022210df1d3105bb866782f1a87b25c6a3494eb092`.
- Contenu parsé : 13 messages — 2 utilisateur, 5 assistant, 6 système.
- Les entrées `tools` du snapshot contiennent nom, statut et sortie, mais **pas les paramètres d'entrée** : les commandes exactes ne sont pas rejouables depuis cette fenêtre.

## Portée

- Tour 0, `2026-10-27T05:22:42.141Z` : « verifie bien la reconnaissence multimodale par les sens ».
- Tour 2, `2026-10-27T05:30:07.053Z` : « Lance les corrections localement ».
- Portée fixée : local uniquement. Aucun déploiement, aucune rotation de secret, aucune modification de production.
- Aucune correction de méthode explicite par l'utilisateur dans la fenêtre.

## Chronologie

| Heure UTC | Message | Fait |
|---|---|---|
| 05:22:42 | M0 utilisateur | demande d'audit |
| 05:22:42 | M1 assistant | audit ; SAS seul 5 tests avec `test_04` en échec ; 25 tests en 11,260 s, `failures=1` |
| 05:30:07 | M2 utilisateur | « Lance les corrections localement » |
| 05:30:07 | M3 assistant | reproduction du couple SAS + passerelle, `setdefault`, sockets, caches |
| 07:41:20 | M4 assistant | lecture par requête ; découverte 272 tests, 7066,575 s, `failures=6, errors=1` |
| 08:01:16 | M5 assistant | bilan : 21/21 ciblés, 11/11 sans clé à l'import, résiduels |
| 08:02:52 | M6–M12 système | fin de session |

## Les sept problèmes triés

| # | Test | Catégorie | Preuve |
|---|---|---|---|
| 1 | `tests.test_passerelle_api_vps.TestPasserelleAPIVPS.test_06_securite_commandes_authentification` | Ordre d'import | `ERROR`, 401 sur la requête avec jeton, ligne 162 |
| 2 | `tests.test_conscience_logique.TestAlMizan.test_a142_agir_sur_ecarts_et_dissociation_q` | Périmètre pollué | échec attribué au clone `GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` |
| 3 | `tests.test_conscience_logique.TestAlMizan.test_a143_completude_perimetre` | Périmètre pollué | idem |
| 4 | `tests.test_conscience_logique.TestAlMizan.test_conscience_surveille_et_synthese` | Périmètre pollué | idem |
| 5 | `tests.test_logique_horloge_synchronisation.TestSynchronisationTotale.test_p7_trame_dans_une_seule_pulsation` | Charge | échoue en découverte, vert en ciblé (bilan M5) |
| 6 | `tests.test_suite_complete.TestSystemeCompletAstroQode.test_06_execution_monade_supreme_v2_et_stdlib` | Assertion périmée | neuf scripts `.aq` ; assertion alignée, ligne 238 |
| 7 | `tests.test_suite_complete.TestSystemeCompletAstroQode.test_24_noyau_logique_interactif_telemetrie_basescan` | Assertion périmée | formulation « partage 50/50 » et « Riba 0 % », lignes 947–948 |

### Détail de l'échec d'ordre d'import

- État initial : `passerelle_api_vps_mizan.py:83` contenait
  `CLE_API_VPS_DEFAUT = os.environ.get("MIZAN_VPS_API_KEY", "mizan_vps_souverain_secret_2026")`.
- `tests/test_sas_biometrique_souverain.py:27` importe la passerelle dès son en-tête.
- En découverte, un module importe la passerelle avant que le test de la passerelle ne pose son environnement : la constante est figée à `""`.
- Le `os.environ.setdefault` exécuté ensuite ne peut plus remplir une constante déjà calculée.
- L'assistant confirme : « the SAS test module imports the gateway first, so `CLE_API_VPS` is captured empty ».

### Détail des sockets

- `ResourceWarning: unclosed <socket.socket fd=616, family=2, type=1, proto=0, laddr=('0.0.0.0', 8098)>`.
- `ResourceWarning: unclosed <socket.socket fd=868, family=2, type=1, proto=0, laddr=('0.0.0.0', 8097)>`.
- Un run affiche `Ran 16 tests in 1.851s` / `OK` **et** un `ResourceWarning` sur 8098 : les tests passent, la socket fuit.
- `arreter()` initial ne faisait que `self.httpd.shutdown()`.

### Détail des caches

- Fenêtres observées : `bibliotheques` et `outils` à 05:47, `tests` à 06:05, racine à 06:35.
- Des `.pyc` `cpython-312` et `cpython-314` plus anciens coexistent dans les mêmes `__pycache__`.
- L'assistant déclare n'avoir supprimé que les fichiers de la session ; la commande exacte n'est pas capturée.

## État final du code (relu le 2026-10-27)

- `passerelle_api_vps_mizan.py:84-86` : `cle_api_vps_attendue()` lit `os.environ.get("MIZAN_VPS_API_KEY", "").strip()`.
- `passerelle_api_vps_mizan.py:390-403` : vérification par appel, fermeture si vide, `hmac.compare_digest`.
- `passerelle_api_vps_mizan.py:1932-1941` : `shutdown`, `server_close`, `join(timeout=5.0)`, références remises à `None`.
- `grep -rn "CLE_API_VPS" --include=*.py .` : aucun résultat, les importateurs ont été migrés.
- `tests/test_passerelle_api_vps.py:25-27` : `CLE_TEST_API = os.environ.setdefault(...)` avant l'import ; assertion sur `CLE_TEST_API` ligne 157.
- `tests/test_sas_biometrique_souverain.py:44-49` : `tearDownClass` appelle seulement `arreter()`.
- `tests/test_suite_complete.py:238` : `assertEqual(len(fichiers_aq), 9)`.
- `tests/test_suite_complete.py:947-948` : `partage 50/50` et `Riba 0 %`.
- Clone étranger présent à `IMAM8MAHDI/GITHUB_DEPOT_PUBLIC_IMAM8MAHDI`, non modifié.

## Correctifs appliqués

1. Lire la clé à chaque requête, fermeture par défaut, comparaison constante conservée.
2. Poser `MIZAN_VPS_API_KEY` avant l'import dépendant dans les tests, asserter avec la valeur locale.
3. `shutdown` + `server_close` + `join(timeout=5.0)` + remise à `None`.
4. Aligner deux assertions sur l'artefact réel après exécution.
5. Nettoyer uniquement les `.pyc` de la fenêtre de session.

## Matrice observé / déclaré / non étayé

| Affirmation | Statut | Base |
|---|---|---|
| SAS seul 5 tests, `test_04` échoue d'abord | OBSERVÉ | sortie brute M1 |
| Passerelle seule 11/11 | DÉCLARÉ | bilan M5 |
| 401 sur requête authentifiée en découverte | OBSERVÉ | trace `test_06` ligne 162 |
| 272 tests, 7066,575 s, 6 échecs + 1 erreur | OBSERVÉ | sortie brute M4 |
| Les 7 échecs listés ci-dessus | OBSERVÉ | sortie brute M4 |
| Constante vide au premier import | OBSERVÉ + DÉCLARÉ | code et affirmations M3/M4 |
| `ResourceWarning` ports 8097 et 8098 | OBSERVÉ | sorties M3 |
| 16 tests `OK`, warning encore présent | OBSERVÉ | sortie M3 |
| 11/11 avec clé absente à l'import | DÉCLARÉ | affirmation M4/M5 |
| 21/21 ciblés sans `ResourceWarning` | DÉCLARÉ | affirmation M5 |
| Seuls les `.pyc` de la session supprimés | DÉCLARÉ + OBSERVÉ partiel | texte M3 et horodatages |
| Porte `-W error::ResourceWarning` | NON CAPTURÉE dans cette session | 0 occurrence dans le snapshot ; gate prescrite par ce Skill |
| Cause de l'échec `test_04` initial | NON CAPTURÉE | test vert plus tard, raison absente |

Vérification complémentaire du JSONL brut de la session (2026-10-27) : la porte `-W error::ResourceWarning` y figure 5 fois et la sortie `Ran 21 tests in 3.312s` / `OK` y est présente. La mention « non capturée » ci-dessus ne vaut donc que pour le snapshot borné, pas pour le journal complet.

## Résiduels et limites

- 3 échecs de conscience attribués à la copie étrangère `GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` (6 modules divergents selon M5). Ni modifiée ni exclue du scan ; à traiter par l'ayant droit.
- `HMAC_SECRET_WEBHOOKS` conserve une valeur par défaut codée en dur ; non corrigé.
- En attente d'autorisation : déploiement production, rotation de `MIZAN_VPS_API_KEY` et du mot de passe SSH, correction du mode 666, SMTP, exclusion de l'administrateur des statistiques publiques.
- Aucune ré-exécution des tests pour ce dossier : décision de s'appuyer sur les preuves de session et d'éviter les effets de bord (`memoire_aq`, ports 8096/8098).
- Le snapshot ne contient pas les paramètres d'entrée des outils ; les commandes du Skill sont des modèles, pas un rejeu littéral.

## Empreintes

- `SKILL.md` de `triager-echecs-suite-unittest-decouverte` après fusion et ajout de la règle anti-`grep` : 13 202 octets, 219 lignes, SHA-256 `e6f805a585cd7f7ebbac7ce79ac2065587c4b79d25c3cfecbf24a3caaa3eb63e` (2026-10-27).
- `references/modeles-correctifs.md` : 6 557 octets, 202 lignes, SHA-256 `033fd5c7d34ff70265efd2c8abbaa2e480ffedd6cfbbc2326f1e6959e7e61ba7`.
- Ce dossier de preuve est référencé par son nom et son contenu ; son empreinte propre est reportée dans le compte rendu de session, car elle change à chaque mise à jour de ce paragraphe.
