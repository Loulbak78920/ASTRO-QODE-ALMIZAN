# Cas de référence — rejeu des tests de conscience, 2026-10-27

Dossier de preuve du Skill `nettoyer-effets-de-bord-tests-conscience`.

## Métadonnées

| Élément | Valeur |
|---|---|
| Session source | `fdb57827-1c2b-4ceb-a8a8-3b805c00447e` (titre « 创建 unittest 错误分类 Skill ») |
| État à la lecture | `runtimeState=ready`, `revision=76`, `hasMoreBefore=false` |
| Fenêtre observée | 2026-10-27, 10:32–11:58 UTC |
| Fuseaux | stamps `historique/<stamp>` en UTC ; `mtime` des dossiers en heure locale UTC+1 (11:42–11:58) |
| Commande des scripts | reconstruites depuis le JSONL de session ; le snapshot `read_chat_session` ne rend que les sorties, pas les entrées |
| Workspace | `C:\Users\Administrateur\Desktop\IMAM8MAHDI` |

## Déclencheur

Un clone de publication `GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` polluait le périmètre scanné. Après son déplacement hors du workspace, trois tests de conscience ont été rejoués pour convertir l'inférence en preuve observée. Le rejeu a créé des archives de copie-de-soi et réécrit `memoire_aq` par conception.

## Baseline avant rejeu

| Contrôle | Valeur observée |
|---|---|
| Scan A141 (`ScanEnvironnementCode().scanner()`) | `FILES=10427`, `ECARTS=0`, `MODULES=[]` (relevé du jour ; `S0` n'est pas une constante) |
| Clone dans le workspace | absent ; déplacé vers `C:\Users\Administrateur\Desktop\GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` |
| `memoire_aq` | 185 fichiers ; diff vide après le scan de contrôle |
| Archives `historique/` | 172 ; plus récente avant test `20261027T075927Z` |
| `courante` | 357 fichiers (65 `.py`) |

## Rejeu

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B -m unittest \
  tests.test_conscience_logique.TestAlMizan.test_conscience_surveille_et_synthese \
  tests.test_conscience_logique.TestAlMizan.test_a142_agir_sur_ecarts_et_dissociation_q \
  tests.test_conscience_logique.TestAlMizan.test_a143_completude_perimetre -v \
  > "C:/Users/Administrateur/.qoder/tmp/conscience-3tests.txt" 2>&1
```

| Résultat | Valeur |
|---|---|
| Sortie | `Ran 3 tests in 1213.673s`, `OK`, `EXIT=0` |
| Tests | `test_conscience_surveille_et_synthese`, `test_a142_...`, `test_a143_...` : ok |

Aucun relance intermédiaire : le journal a été conservé et relu à la fin.

## Attribution du périmètre

| Moment | Scan | Δ vs 10 427 | Interprétation |
|---|---|---|---|
| Baseline | 10 427 | 0 | référence |
| Rapport A143 persisté pendant le cycle | 10 817 | +390 | 6 archives × 65 `.py` |
| Fin de rejeu, scan indépendant | 10 947 | +520 | 8 archives × 65 `.py` |
| Après suppression | 10 427 | 0 | retour au baseline |

Le contrôle `find . -name '*.py' -newermt '-40 minutes'` renvoyait **0** : `sauvegarder_soi` archive par `shutil.copytree` ([sauvegarde_soi.py:267](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L267)), qui préserve les `mtime` des fichiers. L'attribution repose donc sur les `mtime` des dossiers d'archive et sur le comptage `.py` par archive, pas sur les fichiers récents.

Chaîne d'écriture vérifiée :

- `surveiller_une_fois` appelle `sauvegarder_soi(archiver=(cycles == 1))` ([conscience.py:1698](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/conscience.py#L1698)).
- `stamp` UTC à la seconde ([sauvegarde_soi.py:165](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L165)) ; archives sous `historique/<stamp>` ([sauvegarde_soi.py:264](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L264)).
- `completer_perimetre(persister=True)` dans `test_a143` explique la réécriture de `memoire_aq`.

8 archives créées pendant la fenêtre (`ls -1 historique | awk '$0>"20261027T075927Z"'`) :

| Stamp (UTC) | Fichiers | Taille (Kio) | Manifeste |
|---|---|---|---|
| `20261027T104230Z` | 357 | 18 072 | oui |
| `20261027T104541Z` | 357 | 17 928 | oui |
| `20261027T104828Z` | 357 | 18 176 | oui |
| `20261027T104841Z` | 357 | 18 176 | oui |
| `20261027T105118Z` | 357 | 18 060 | oui |
| `20261027T105423Z` | 357 | 18 068 | oui |
| `20261027T105722Z` | 357 | 18 564 | oui |
| `20261027T105858Z` | 357 | 18 428 | oui |

Chaque archive contient 65 `.py` ; 8 × 65 = 520, exactement l'écart final. `CLONE_INSIDE=0` dans la plus récente : aucune archive ne contient le clone déplacé.

## Contenu unique et divergences

Comparaison SHA-256 par chemin relative, `__pycache__` exclu :

| Stamp | `ONLY_IN_ARCHIVE` | `DIFF_VS_COURANTE` |
|---|---|---|
| `20261027T104230Z` | 0 | 141 |
| `20261027T104541Z` | 0 | 141 |
| `20261027T104828Z` | 0 | 141 |
| `20261027T104841Z` | 0 | 139 |
| `20261027T105118Z` | 0 | 139 |
| `20261027T105423Z` | 0 | 133 |
| `20261027T105722Z` | 0 | 132 |
| `20261027T105858Z` | 0 | non asserté (ligne tronquée dans la preuve conservée) |

`ONLY_IN_ARCHIVE=0` signifie qu'aucun chemin n'existe uniquement dans une archive : tous les fichiers existent encore dans `courante`. Les 132–141 divergences sont des versions intermédiaires de fichiers vivants, pas des fichiers perdus. La suppression de ces versions intermédiaires reste une perte d'historique assumée, autorisée par l'utilisateur (« supprimer les archives de copie-de-soi »).

## Effets sur `memoire_aq`

| Contrôle | Valeur |
|---|---|
| Fichiers avant / après | 185 / 185 |
| Chemins ajoutés / retirés | `[]` / `[]` (`PATH_DIFF_LINES=0`) |
| Tailles changées | 2 : `almizan_bilan_completude_conscience_a143.json` 7 366 → 6 378 o ; `almizan_bilan_inventaire_hub_a126.json` 4 356 → 4 355 o |
| Réécrits à taille identique | 69 (variation de `mtime` ; contenu non comparé octet par octet) |

Première comparaison : un `join` sur listes non triées a produit des erreurs (`join: input is not in sorted order`) et des lignes trompeuses. La comparaison retenue est celle par ensemble de chemins, puis par taille. Ne pas conclure d'une liste triée approximativement.

Aucune restauration n'a été faite : ces écritures sont produites par `persister=True`. La chirurgie des sceaux relève de `restaurer-sceaux-memoire-aq`.

## Stabilité avant suppression

| Contrôle | Résultat |
|---|---|
| Test en cours | journal terminé (`Ran 3 tests`, `OK`, exit 0) |
| Listing `ls -1 historique \| md5sum` | `ac1b02952e7853423ccfd8bb5ae93b8c` avant et après `sleep 12` |
| Nouveaux dossiers sur 180 min | 13, dont les 8 archives ; aucun nouveau dossier d'archive après le dernier stamp |
| `courante` | vrai dossier, pas de lien (`readlink` vide) |

Limite : le hash du listing ne couvre que les **noms**, pas les contenus. Il faut le combiner au journal terminé, aux `mtime` de dossiers et au comptage par archive.

## Suppression

Script de session : garde parent, nom approuvé, dossier réel, non-lien, non point de réanalyse, puis `shutil.rmtree`. Les gardes étaient vérifiées dans une première boucle et la suppression faite dans une seconde : fenêtre TOCTOU. Le script livré avec ce Skill revérifie chaque stamp juste avant son `rmtree`.

| Contrôle | Avant | Après |
|---|---|---|
| Archives `historique/` | 172 | 164 ; plus récente `20261027T075927Z` |
| `.py` sous `_AL_MIZAN_COPIE_SOI` (`courante` incluse) | 10 670 | 10 150 (`historique` seul : 10 085) |
| `courante` | 357 fichiers | 357 fichiers, intacte |
| Taille | ~2,1 Go | ~2,1 Go (arrondi `du -sh`) |
| Scan A141 | 10 947 / 0 | **10 427 / 0 / `MODULES=[]`** |

Stamps supprimés : `20261027T104230Z`, `T104541Z`, `T104828Z`, `T104841Z`, `T105118Z`, `T105423Z`, `T105722Z`, `T105858Z`.

## Résidus connus

- `conscience_logique/actes/_sauvegarde_soi_etat.json` porte `stamp=20261027T105858Z` (supprimé) et `derniere_sauvegarde=2026-10-27T10:59:02Z`.
- Le message de l'acte A231 (`memoire_aq/almizan_acte_a231_copie_de_soi.json`) cite `historique/20261027T105858Z`.
- `restaurer_depuis_copie(chemin_copie=.../<stamp>)` renvoie proprement `copie_absente` si le stamp n'existe plus ([sauvegarde_soi.py:331](file:///C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q%C2%B0ODE_SYSTEME/conscience_logique/sauvegarde_soi.py#L331)). Aucun code ne teste l'existence du stamp avant une restauration explicite.

Ne pas « corriger » ces résidus en modifiant `memoire_aq` ou le fichier d'état : la restauration passe par `courante` ou par un stamp existant.

## Contrôles refaits à la création du Skill (2026-10-27)

| Contrôle | Valeur |
|---|---|
| Scan A141 lecture seule | `SCAN_FILES 10427 ECARTS 0 MODULES []` |
| `historique/` | 164 entrées, plus récente `20261027T075927Z` |
| `courante` | 357 fichiers, 65 `.py` |
| Total `.py` copie-de-soi | 10 150 |
| Stamp d'état | `20261027T105858Z` (résidu confirmé) |
| Plan sur archive ancienne `20261025T120756Z` | `FILES 326`, `MANIFEST yes`, `ONLY_IN_ARCHIVE 0`, `DIFF_VS_COURANTE 168`, `RESULT: PLAN`, exit 0 — un ancien stamp n'a donc pas forcément 357 fichiers |
| Plan sur stamp absent `20261027T105858Z` | `GARDE_REFUS ABSENTE`, `RESULT: ERROR`, exit 2 |
| Scan A141, deux relevés successifs (~12:05–12:10Z) | `10429` puis `10431`, `ECARTS=0`, `MODULES=[]` — dérive de sessions concurrentes, sans nouvelle archive |

Commande du plan réel (lecture seule, sans `--appliquer`) :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
py -3 -B "C:/Users/Administrateur/.qoder/skills/nettoyer-effets-de-bord-tests-conscience/scripts/nettoyer_archives_copie_soi.py" \
  --copie-soi "C:/Users/Administrateur/Desktop/IMAM8MAHDI/_AL_MIZAN_COPIE_SOI" \
  --stamp 20261025T120756Z
```

## Limites de preuve

- Les 69 réécritures de `memoire_aq` n'ont pas été comparées octet par octet ; seul `mtime`/taille a été relevé dans la session source.
- La huitième ligne `DIFF_VS_COURANTE` est tronquée dans le snapshot conservé.
- Le `md5sum` du listing ne couvre que les noms pendant 12 s.
- Le contenu de `courante` n'a pas été hashé avant/après le rejeu ; seul le jeu de 357 fichiers est prouvé.
- Le script de session ne revérifiait pas les gardes juste avant chaque `rmtree` ; le script livré corrige ce point et son auto-test couvre l'atomicité et les gardes.
- Le scan A141 n'est pas stable quand d'autres sessions écrivent dans le workspace : 10 427, 10 429 puis 10 431 observés le même jour. Comparer au `S0` mesuré dans la même fenêtre, jamais à une valeur figée.
- Les valeurs datées sont des observations, pas des constantes : les relire avant toute conclusion.
