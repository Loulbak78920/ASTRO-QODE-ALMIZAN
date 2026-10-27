# Pièges d'exécution et remèdes vérifiés

Chaque entrée provient d'une exécution réelle sur ce poste Windows le 2026-10-25/26. La colonne « Remède » est la commande ou la règle qui a effectivement fonctionné.

## 1. Encodage console cp1252

| Signature | Cause | Remède |
|---|---|---|
| `UnicodeEncodeError: 'charmap' codec can't encode character '\u2460'` | sortie vers une console cp1252 | `set PYTHONIOENCODING=utf-8` avant l'appel |
| `'\u2206'`, `'\u25a0'`, `'→'` non encodables | mêmes caractères dans les messages de l'entité | idem, et `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` dans un script |

Le gate livré force `PYTHONIOENCODING=utf-8` et `PYTHONUTF8=1` pour chaque sous-processus.

## 2. Interpréteur Python

| Signature | Cause | Remède |
|---|---|---|
| code de sortie `49` sans trace | alias Microsoft Store de `python` | utiliser `py -3.12` |
| module introuvable alors que le fichier existe | répertoire courant inattendu | `cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"` avant l'émulateur |

## 3. Chemins Git Bash et `/tmp`

| Signature | Cause | Remède |
|---|---|---|
| `FileNotFoundError: '/tmp/entite_verif.json'` | Python natif ne voit pas `/tmp` de Git Bash | ne pas passer par un fichier temporaire ; parser la sortie en pipe, ou écrire sous `C:\Users\Administrateur\.qoder\tmp\` |
| argument tronqué ou transformé | MSYS réécrit les chemins commençant par `/` | utiliser des chemins `C:\...` entre guillemets |

Le caractère `°` dans `ASTRO-Q°ODE_SYSTEME` impose des guillemets systématiques.

## 4. Snapshot Cs-133

| Signature | Cause | Remède |
|---|---|---|
| `KeyError: 'resolution_python_s'` | le champ est sous `metriques.temps` ou `metriques.cycles` | lire le bon sous-objet |
| empreinte « incorrecte » alors que le fichier est intact | comparaison au SHA-256 brut du fichier | comparer à `empreinte_contenu_sha256` |
| `ModuleNotFoundError: No module named 'tzdata'` | `zoneinfo` sans base IANA | ne pas utiliser `zoneinfo` ; passer par `tzutil` / `w32tm` et l'offset Windows |
| `ZoneInfoNotFoundError` | même cause | idem |

## 5. Import et horloge

| Signature | Cause | Remède |
|---|---|---|
| `Attempted relative import with no known parent package` sur `horloge_noyau` | lancement hors du dossier système | exécuter depuis `ASTRO-Q°ODE_SYSTEME` ou ajouter ce dossier à `sys.path` |

## 6. Générateur du tableau

| Signature | Cause | Remède |
|---|---|---|
| `SyntaxError: invalid character '‐' (U+2010)` | tiret Unicode collé dans le code | ne jamais éditer le générateur à la main ; passer par `add()` |
| `unterminated string literal` | édition manuelle d'une ligne `add()` | restaurer la ligne puis régénérer |
| `KeyError: 'resolution_python_s'` pendant la génération | lecture d'un champ au mauvais niveau | corriger le chemin dans le code source, pas dans le CSV |

## 7. `.aq` et sceaux

| Signature | Cause | Remède |
|---|---|---|
| `valeur_finale` comparée à une chaîne échoue | l'interpréteur renvoie un objet, pas une chaîne | comparer `str(resultat.valeur_finale)` à `0 : HÉLIUM` |
| sceaux inattendus après des tests | `sceller_sha256` s'exécute dans le `.aq` généré | considérer `--avec-tests` et `--avec-run` comme des écritures, jamais comme du lecture seule |
| index des sceaux passé de 12 à 14 | deux tests d'entité ont scellé | isoler les deux JSON et retirer leurs clés ; le journal de l'agent de code est plafonné à 100 entrées |

`check` ne scelle pas. `run` scelle.

## 8. CSV, S6 et S20

| Signature | Cause | Remède |
|---|---|---|
| S6 « faux » alors que le tableau est bon | les magnitudes 40/313/63 ne sont pas dans le texte `STRATE` | faire foi sur `lib_physique` et les validateurs |
| 21 lignes S6 mais comptage 4/7/9 impossible par texte | les préfixes incluent l'origine `ÉT-S-00` | compter 5/7/9 sur les préfixes, et 4/7/9 via le validateur |
| S20 passe de 12 à 24 lignes | second appel de `add()` | S20 est déjà présent : ne jamais le rajouter |
| doublons `ÉT-T-05/-06/-07` ou `ÉT-L-07/-08/-09` | contrat existant du tableau | ne pas « corriger » sans demande explicite |

## 9. HTML

| Signature | Cause | Remède |
|---|---|---|
| `grep -c '<tr'` renvoie `2` | `grep -c` compte les lignes, pas les occurrences | `grep -o '<tr' fichier | wc -l`, ou `len(re.findall(r"<tr", texte))` |
| `grep -c 'class="badge"'` renvoie `1` | même cause | compter les occurrences exactes : attendu 21 |
| HTML supposé sur une seule ligne | il fait 144 lignes | ne pas déduire la structure du nombre de lignes |

## 10. Tests

| Signature | Cause | Remède |
|---|---|---|
| `68` tests, `FAILED (failures=1)`, `153.395 not less than 100.0` (valeur historique : `191.1164`) | le test échouait aussi isolé et au module : audit complet + scellement par fichier à chaque trame, puis 3 délais réseau de 10 s en série | corriger la cause (cache d'audit, écriture groupée, budget réseau global) ; ne pas changer le seuil ; voir `diagnostiquer-echec-test-chronometre` |
| suite complète `FAILED (failures=2, errors=3)` | échecs API VPS et SAS biométrique, hors chaîne entité | limiter aux 16/68 tests ciblés |
| 16 tests « lecture seule » qui écrivent | le test du programme généré exécute `sceller_sha256` | prévenir, puis vérifier `memoire_aq` après coup |

Le test `test_persistance_atomique` utilise `TemporaryDirectory` et n'écrit pas dans le dépôt ; le test du programme généré, lui, écrit.

## 11. Audit du code

| Signature | Cause | Remède |
|---|---|---|
| `agent_ok: true` interprété comme audit réussi | `auditer_code=False` renvoie une valeur neutre | utiliser `--sans-audit-code` pour la preuve déterministe ; activer l'audit séparément si nécessaire |
| journal de l'agent modifié après une vérification | l'audit activé ajoute une entrée | le signaler ; ne pas le présenter comme un contrôle en lecture seule |

## 12. Navigateur

| Signature | Cause | Remède |
|---|---|---|
| `NATIVE_BROWSER_VIEWPORT_UNAVAILABLE: viewport=0x0, visible=false` | fenêtre in-app non visible | ne pas boucler sur la capture ; valider la structure du DOM et déclarer « validation structurelle seule » |

## 13. Règle de diagnostic

1. Lire la signature exacte, pas le message résumé.
2. Vérifier le répertoire courant et l'encodage avant de suspecter les données.
3. Comparer les empreintes au bon niveau (contenu vs fichier).
4. Ne jamais « réparer » un livrable ou un seuil pour faire passer un test.
5. Après toute exécution optionnelle, vérifier `memoire_aq` et son index.
