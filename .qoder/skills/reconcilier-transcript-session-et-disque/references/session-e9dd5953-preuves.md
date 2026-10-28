# Preuves — sessions e9dd5953 et 026949af (28/10/2026)

Conventions : messages du JSONL en UTC (`Z`) ; sorties `stat` en heure locale (`+01:00`). Les deux valeurs sont données quand la comparaison compte.

## 1. Canal d'observation

- 11:53:37.867Z — `mcp_call` `read_chat_session` avec `{"chatSessionId": "026949af-b05f-4dc2-8655-0b52096810f8"}`.
- 11:53:38.865Z — résultat verbatim :

```
Error: read_chat_session (builtin MCP Server) tool parameter validation failed: params must have required property 'sessionId'
```

- 11:53:40.846Z — reprise avec `sessionId` ; 11:53:41.083Z — `runtimeState: running`, `revision: 41`, `activeTurnId: 641088df-feb5-46a4-8dd6-6647507406f7`, `hasMoreBefore: false`.
- Corps tronqué dans ce snapshot (budget par défaut de 2 000 caractères) :

```
Deux points à noter :
1
…
```

- Dump JSONL de 11:54:06.438Z, phrase entière :

```
1. Sans `--simuler`, le script demande votre clé privée et envoie une **transaction réelle** ...
```

- 026949af : 137 lignes au dump de 11:54:06Z ; 359 enregistrements dont 49 `active-leaf` à 12:02:25Z ; 528 puis 535 enregistrements dont 194 puis 197 `active-leaf` aux mesures de 12:03–12:04Z. Le fichier a donc crû pendant la vérification.
- La queue contient `last-prompt` et `workspace-directories` sans timestamp ISO, `runtime-config` et `active-leaf` avec epoch-ms. Le dernier Write/Edit horodaté reste un Edit de `deploy_evm_reseau.py` à 11:59:04.483Z ; les tours suivants n'en ajoutent aucun au moment de la mesure.
- Limite : la lecture de e9dd5953 s'arrête à 11:54:15Z. 026949af a continué : Write/Edit jusqu'à 11:59:04.483Z, puis un tour utilisateur à 12:00:07.880Z (« Commit ces changements ») et un enregistrement `user` à 12:04:16.451Z. Au 12:04Z, `runtimeState: running`, `activeTurnId: dd3fd973-…`, `revision: 44`, `hasMoreBefore: true`. Relecture à 12:06Z : `runtimeState: ready`, `activeTurnId: null`, `revision: 55` ; le JSONL s'arrête à 551 enregistrements / 203 `active-leaf` (mtime 12:04:37Z). Toute affirmation sur son état final est `PROVISIONAL`.

## 2. Dialogues de recherche

Périmètre : `ASTRO-Q°ODE_SYSTEME`, `--include=*.py`.

| Heure (UTC) | Commande | Sortie |
|---|---|---|
| 11:54:22.721Z | `grep -rln --include=*.py "Desktop.{0,3}Al-Mizan" .` | 0 ligne |
| 11:54:37.953Z (résultat 11:54:39.175Z) | `grep -rlnE --include=*.py 'Desktop.{0,3}Al-Mizan' .` | 20 fichiers |
| idem | `grep -rn --include=*.py -F 'Desktop\Al-Mizan' . \| head` | 7 fichiers, lignes 51/92/77/77/92/112/112 |
| 12:02:25Z | `grep -rlnF --include=*.py 'Desktop\Al-Mizan' .` | 0 |
| 12:02:25Z | `grep -rlnE --include=*.py 'Desktop.{0,3}Al-Mizan' .` | 13 |
| 12:02:25Z | `grep -rlnE --include=*.py 'resolution_abi_mizan' .` (contrôle positif) | 8 |

- En BRE, `{0,3}` est littéral : le motif cherche la chaîne `{0,3}` et ne peut pas correspondre.
- Décomposition des 20 fichiers ERE : 13 prose + 7 code. Après les réparations : 0 code + 13 prose. Les 13 restants sont des docstrings ou du texte entre backticks, vérifié en lisant les lignes matchées, par exemple `bibliotheques/lib_almizan_extension.py:8` et `module_continuite_reponse_automatisee_mizan.py:9`.
- Deux questions, deux nombres : « reste-t-il un chemin codé en dur ? » → 0 ; « le nom apparaît-il encore ? » → 13.

## 3. `mtime` contre Write/Edit

| Mesure | Valeur locale | UTC | Dernier Edit enregistré | Écart | Verdict |
|---|---|---|---|---|---|
| 11:54:37Z | `2026-10-28 12:49:25.114179000 +0100` | 11:49:25.114Z | 11:49:25.163Z | 49 ms | `CONFIRMÉ` |
| 12:02:25Z | `2026-10-28 12:54:44.575742600 +0100` | 11:54:44.575Z | 11:54:44.526Z (deux Edits) | 49 ms | `CONFIRMÉ` |

- L'ancien dossier classait la première mesure `NON_ATTRIBUÉ` en comparant `12:49` local à `11:49Z` ; en UTC l'écart est de 49 ms.
- Dérive de contenu entre les deux mesures : 8561 octets / `2a9e3fcc…` à 11:54:37Z, puis 7804 octets / `70a8c716…` à 11:54:44Z. Le second état vient du remplacement du chargeur inline par `from resolution_abi_mizan import charger_abi`.

## 4. Écritures tardives

- 11:54:40.885Z — Write `resolution_abi_mizan.py`.
- 11:54:44.526Z — deux Edits de `valider_et_sceller_tout_one_click.py`.
- 11:54:55.507–11:54:55.508Z — sept Edits (six `sceller_*` et `passerelle_ancrage_blockchain.py`).
- 11:55:04.057Z — cinq Edits ; 11:55:11.786Z — deux ; 11:55:14.865Z — un.
- 11:59:04.483Z — Edit de `deploy_evm_reseau.py`.

Conséquence : le grep de 11:54:39Z montrant 7 littéraux était vrai pendant environ 16 secondes. La première écriture de masse suit à 11:54:55Z.

## 5. Correction d'un dossier déjà livré (28/10/2026)

Fichier : `reparer-chemin-artefact-absolu-script-python/references/session-026949af-preuves.md`.

- Constat du 2026-10-28 à 12:02:25Z : lignes 64-66 annonçaient 8561 octets / `2a9e3fcc…` / mtime `12:49:25`, alors que le disque portait 7804 octets / `70a8c716…` / mtime `12:54:44.575 +0100` ; l'en-tête « état disque au 12:55 » ne correspondait à aucune mesure (11:54:37Z = 12:54:37 local).
- Ligne 67 : l'écriture de 12:49 était dite « non attribuée par la transcription » ; l'Edit de 11:49:25.163Z l'explique, à 49 ms près.
- Lignes 87-101 : le tableau annonçait 7 scripts « non modifiés au contrôle de 12:55 » ; les sept Edits commencent à 11:54:55Z et `-F` rend 0 à 12:02:25Z.
- Corrigé le 2026-10-28 à la demande de l'utilisateur (quatre Edits de 12:08:27.611Z à 12:09:08.067Z, session `0f454a00`) : empreintes réelles (§4), attribution par Edit, tableau requalifié en inventaire historique, §7 requalifié en `PROVISIONAL`. De ces modifications, seules les sections 4, 6 et 7 du dossier ont changé ; ses sections 1-3 et 5 sont intactes.
- En parallèle, une autre session (`67d9cce8`) réécrit le `SKILL.md` du même dossier depuis 12:09:22Z (Edits à 12:09:22, 12:09:41, 12:09:50 et 12:10:25Z) : elle y remplace l'étape 5 autocalculée par une délégation à `verifier-abi-locale-contrat-deploye`. Ce fichier n'est pas de mon périmètre ; son état est mouvant et le §6 corrigé ci-dessus ne lui est pas rattaché.

## 6. Limites

- Les métadonnées du snapshot sont ponctuelles ; la session source était active et a continué après la lecture.
- Les mesures « actuelles » datent du 2026-10-28T12:02:25Z ; elles ont été rejouées à l'identique à 12:06Z (`-F` 0, ERE 13, contrôle positif 8, script 7804 octets / `70a8c716…`). Le JSONL de 026949af est passé de 359 à 551 enregistrements pendant la vérification, puis s'est arrêté à 12:04:37Z. Ces mesures restent `PROVISIONAL` : toute écriture postérieure les invalide.
- Aucune commande des journaux n'a été exécutée : seuls `stat`, `sha256sum`, `grep`, `sed` et une lecture JSONL en Python ont servi.
- Les 13 fichiers ERE sont classés prose après lecture des lignes matchées ; deux exemples sont cités, les 11 autres n'ont pas été reproduits ici.
- Le contrôle positif `resolution_abi_mizan` rend 8 fichiers : les 7 scripts réparés et le script principal.
