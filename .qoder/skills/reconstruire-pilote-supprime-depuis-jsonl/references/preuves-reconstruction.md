# Preuves de reconstruction (2026-10-26)

Portée : session de reconstruction `b8448766-bcf0-40dc-9ea5-9622f129877e` et session source `c4fcd88c-4b53-4843-a74c-f4a901244e96`. Mesures exécutées avec `py -3` sous Windows. Aucun fichier temporaire n'est livré ; aucun code reconstruit n'a été exécuté.

## 1. Sessions et JSONL

| Rôle | Session | JSONL | Empreinte relevée |
|---|---|---|---|
| Reconstruction | `b8448766-…` | `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\b8448766-bcf0-40dc-9ea5-9622f129877e.jsonl` | 445 lignes, 1 602 605 octets, `sha256=2fc67b1093a75a435d6cc8c2ca3939e8789977a67802ecf4f6b128f59eadc71f` |
| Source du pilote | `c4fcd88c-…` | `C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\c4fcd88c-4b53-4843-a74c-f4a901244e96.jsonl` | 478 lignes, 1 744 756 octets, `sha256=b049387ee6803c301649da88ff5f35df940059bb64de50faf8f5380a6ffed6b4` |

La session source était encore alimentée pendant l'audit ; son empreinte est un instantané daté, pas une constante. Voir §5.

## 2. Entrées du pilote dans `c4fcd88c-…`

| Entrée | Outil | Mesure |
|---|---|---|
| 252 | `Write` | 22 064 caractères, 564 lignes |
| 264 | `Edit` | `occurrence=1` |
| 279 | `Edit` | `occurrence=1` |
| 283 | `Edit` | `occurrence=1` |
| 289 | `Edit` | `occurrence=1` |
| 294 | `Edit` | `occurrence=1` |
| 298 | `Edit` | `occurrence=1` |
| 307 | `Edit` | `occurrence=1` |

Cible : `C:\Users\Administrateur\.qoder\tmp\isolated_publish_flow_test.py`.

Résultat final : 567 lignes, 22 347 caractères, 22 347 octets UTF-8, saut de ligne final présent.

## 3. Commande et sortie mesurées

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/reconstruire-pilote-supprime-depuis-jsonl/scripts/rejouer_pilote_jsonl.py" \
  --jsonl "C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/c4fcd88c-4b53-4843-a74c-f4a901244e96.jsonl" \
  --file "C:/Users/Administrateur/.qoder/tmp/isolated_publish_flow_test.py" \
  --expect-writes 1 --expect-write-chars 22064 \
  --expect-edits 7 --expect-lines 567 --expect-chars 22347
```

```text
JSONL C:\Users\Administrateur\.qoder\projects\C--Users-Administrateur-Desktop-IMAM8MAHDI\c4fcd88c-4b53-4843-a74c-f4a901244e96.jsonl
JSONL_FINGERPRINT size=1744756 mtime_ns=1793016940135931000 lines=478 sha256=b049387ee6803c301649da88ff5f35df940059bb64de50faf8f5380a6ffed6b4
TARGET C:\Users\Administrateur\.qoder\tmp\isolated_publish_flow_test.py
WRITE entry=252 chars=22064 lines=564
EDIT entry=264 occurrence=1
EDIT entry=279 occurrence=1
EDIT entry=283 occurrence=1
EDIT entry=289 occurrence=1
EDIT entry=294 occurrence=1
EDIT entry=298 occurrence=1
EDIT entry=307 occurrence=1
EVENTS writes=1 write_chars=22064 edits=7
RESULT lines=567 chars=22347 bytes_utf8=22347 trailing_newline=true
CLAIM PASS writes=1 write_chars=22064 edits=7 lines=567 chars=22347
```

Code de retour : 0.

## 4. Déclarations corrigées

| Déclaration initiale | Valeur mesurée | Preuve de la correction |
|---|---|---|
| 568 lignes finales | 567 lignes | `Edit` entrée 358 de `b8448766-…`, horodatage `2026-10-26T11:40:10Z` |
| `Write` de 23 714 caractères | 22 064 caractères | `Edit` entrée 366 de `b8448766-…`, horodatage `2026-10-26T11:40:18Z` |
| « récupéré depuis le JSONL » | « reconstituable, non livré » | mêmes éditions |

Déclencheur : le `tool_result` de l'entrée 318 de `b8448766-…` affiche `edits_applied 7 lines 567 chars 22347`. L'agent a corrigé ses propres nombres après cette mesure. Aucun message utilisateur de cette session ne demande la correction ; ce n'est pas une correction utilisateur.

Les anciennes valeurs `568` et `23 714` ne subsistent que comme exemples négatifs explicitement étiquetés dans le tableau des échecs ; elles ne doivent pas être traitées comme des déclarations courantes.

## 5. JSONL actif : croissance observée

Relevés successifs du même fichier source, sans exécuter le script entre les trois premiers :

| Heure locale | Taille (octets) | SHA-256 |
|---|---|---|
| 2026-10-26 13:15:21 | 1 733 028 | `796c490880f7648f04ab0e3fd2e92eaba096b2b5ad96277806d56479173c6105` |
| 2026-10-26 13:15:24 | 1 736 678 | `a81336a9e27abc3f040492c544dd2f0caee7a8c9a5a90cb9f7c057b0fdfce527` |
| 2026-10-26 13:15:28 | 1 739 865 | `0d3b6851daa7d7edf739080503730dab2198f1539b67811eb8867d126d6d5eae` |

Le fichier est passé de 1 586 492 octets (premier relevé de l'audit) à 1 744 756 octets, soit +158 264 octets, puis est resté stable pendant les mesures finales. Les entrées 252 à 307 et le résultat du rejeu n'ont pas changé : les ajouts sont postérieurs.

Le script ouvre le JSONL avec `read_bytes()` et n'écrit jamais dedans ; le contrôle `real-jsonl-unchanged` du harnais (§7) compare le même SHA-256 avant et après une exécution. Une session active peut donc étendre son JSONL indépendamment du script. Conséquence : ne pas figer le SHA-256 comme attendu ; vérifier les nombres `Write`/`Edit`/lignes/caractères. Le script signale `WARN jsonl_changed_during_read` si la taille change pendant sa lecture.

## 6. Sélection de la session

Relevé de l'audit : le nom du pilote apparaît dans trois JSONL du projet — `9bd2ebf7-…` (12 lignes), `b8448766-…` (10 lignes), `c4fcd88c-…` (25 lignes). Seul `c4fcd88c-…` contient le `Write` (entrée 252) et les 7 `Edit`. Le nombre de mentions ne prouve rien : la sélection se fait sur la présence du `Write` pour le chemin exact.

## 7. Contrôles positifs et négatifs (15/15)

Harnais synthétique temporaire, hors paquet. Il crée ses fixtures dans un répertoire temporaire et exécute le script livré.

```text
PASS positive-real rc=0 expected_rc=0 needle='CLAIM PASS'
PASS claim-568 rc=1 expected_rc=1 needle='CLAIM FAIL lines expected=568 measured=567'
PASS claim-23714 rc=1 expected_rc=1 needle='CLAIM FAIL write_chars expected=23714 measured=22064'
PASS edit-miss rc=1 expected_rc=1 needle='EDIT MISS'
PASS edit-ambiguous rc=1 expected_rc=1 needle='EDIT AMBIGUOUS entry=1 occurrence=2'
PASS multiple-paths rc=2 expected_rc=2 needle='multiple target paths'
PASS unsupported-tool rc=2 expected_rc=2 needle='unsupported tool MultiEdit'
PASS sidechain-only rc=2 expected_rc=2 needle='sidechain'
PASS no-target rc=2 expected_rc=2 needle='no Write/Edit for target'
PASS duplicate-id-same rc=0 expected_rc=0 needle='CLAIM PASS writes=1'
PASS duplicate-id-diff rc=2 expected_rc=2 needle='duplicate tool_use id with different input'
PASS dump rc=0 expected_rc=0 needle='DUMP'
PASS dump-bytes-lines size=22347
PASS dump-refuses-existing rc=2 expected_rc=2 needle='dump target exists'
PASS real-jsonl-unchanged b049387ee6803c301649da88ff5f35df940059bb64de50faf8f5380a6ffed6b4 b049387ee6803c301649da88ff5f35df940059bb64de50faf8f5380a6ffed6b4
RESULT PASS 15/15
```

`dump-bytes-lines` vérifie 22 347 octets et 567 lignes. `real-jsonl-unchanged` compare le SHA-256 du JSONL source avant et après l'exécution du script.

## 8. Frontière observé / reconstitué / non prouvé

- **Observé** : entrées 252–307, mesures 22 064 / 564 / 567 / 22 347, corrections des entrées 358 et 366, croissance du JSONL actif, 15 contrôles PASS, refus d'écrasement du `--dump`.
- **Reconstitué** : le script livré est une réécriture testée, pas le pilote d'origine. Le pilote d'origine est reconstituable depuis le JSONL mais n'est pas livré. Aucune affirmation sur son exécution ou son comportement.
- **Non prouvé** : l'exécution du pilote, sa correction sémantique, l'absence de contenu non enregistré, l'immutabilité d'une session active, la reconstruction d'un fichier créé par heredoc/`apply_patch`/`MultiEdit`, la sécurité d'un `--dump` exécuté ensuite.

## 9. Empreintes des livrables

| Fichier | Octets | Lignes | SHA-256 |
|---|---:|---:|---|
| `SKILL.md` | 14 811 | 180 | `4d481dec3c5dccf8028705fb9a813b58ff6a75535c7006551af4fb7b6c7c8c2e` |
| `scripts/rejouer_pilote_jsonl.py` | 9 938 | 276 | `bf53914760c049858ff2a23eb779d2baf3318bd2f82f14f11746c1c9988ce3ed` |

Relevées le 2026-10-26 après `skill-file-qa` (`RESULT PASS`, 9 pass / 0 fail / 0 warn, 3 fichiers). Le SHA-256 de ce fichier de preuves ne peut pas figurer ici de façon stable : il est relevé après sa dernière écriture et reporté dans le message de livraison.
