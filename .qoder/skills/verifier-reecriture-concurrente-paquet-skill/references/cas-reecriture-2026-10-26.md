# Cas de réécriture concurrente d'un paquet Skill — 2026-10-26

**Date du cas** : 2026-10-26 (UTC ; traces locales UTC+01:00)
**Paquet examiné** : `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule`
**Statut** : cas vérifié ; le paquet a été livré avec 4 fichiers, dont 2 réécrits après une QA verte. La réécriture est un correctif légitime conservé. L'auteur de la réécriture n'est pas identifié.

## 1. Artefacts et empreintes

Les empreintes ci-dessous sont des valeurs complètes. Les versions « baseline » ne sont plus sur disque ; elles ont été reconstruites depuis le JSONL et comparées à la baseline enregistrée.

| Artefact | Version | Taille | mtime | SHA-256 |
|---|---|---:|---|---|
| `SKILL.md` du paquet | courante | 15 154 B | 2026-10-26T13:29:08.317483200+01:00 | `6d755440b877d69484533eee0eba663abfb0f23dca54673364102f5fd3f6b632` |
| `references/cas-entite-2026-10-26.md` | courante | 9 792 B | 2026-10-26T13:29:35.563770600+01:00 | `bf4a778a1868bbe548eb9ce7f3940970b1d07627fc65459c1f5799570fd8319c` |
| `references/protocole-restauration.md` | courante | 15 676 B | 2026-10-26T13:36:15.187788200+01:00 | `1de3f4edd8b7e7b3f489d7d83586588f4b706876efeab1b8b87fe7659481fff9` |
| `scripts/instantane_effets_de_bord.py` | courante | 29 761 B | 2026-10-26T13:35:36.191303400+01:00 | `a500711817f826e03b0903cbb3aed78b73a2bbc638c919887f17578316723081` |
| `scripts/instantane_effets_de_bord.py` | baseline reconstruite | 29 725 B | mtime d'origine 2026-10-26T13:19:16+01:00 (manifeste initial) | `be2b86b425b424aed034e980e400241a631830ebe4c1b74fecd7d9c781181e97` |
| `references/protocole-restauration.md` | baseline reconstruite | 15 240 B | mtime d'origine 2026-10-26T13:19:33+01:00 (manifeste initial) | `fc2618d6f77d5a027f028fdc08081b4e106e8cf1a3cc4bb4fa6d69cf0517a290` |
| JSONL de la session `ad2dd331` | lu le 2026-10-26 | 2 494 566 B | mtime_ns 1793018389873281700 ; 13:39:49.873281700+01:00 | `aa21d32303a20458c8b3bec236a7513157b93a23b1f796f6b07d33356c3f3470` |
| Harnais tiers, version en échec | reconstruite depuis le Write | 12 159 B | Write à 2026-10-26T12:36:13.594Z ; fichier temporaire 13:47:42.291778900+01:00 | `2fb80d0b9714087873e395a7bf31b8dfae7ce60b11c2ef9538553c2681a23904` |
| Harnais tiers, version courante | courante | 12 374 B | 2026-10-26T13:40:30.487511300+01:00 | `73ff7c5c8c92afcc303b9a8fe620a7d1fa0bfdfb732f2f85b8199feb46a93916` |
| `resultat_avant_correction.txt` | artefact | 2 626 B | 2026-10-26T13:36:29.727598200+01:00 | `436da1befc5d02da3d089544e1d4ace7c81a028aae815f664dc6fd4d615fb335` |
| `resultat_final.txt` | artefact | 2 589 B | 2026-10-26T13:40:56.329701200+01:00 | `6f6eaa6e4089c81690b61382a0a367ca70ffe97abb813018b65737ab0b8e17ad` |
| Harnais indépendant | artefact | 6 499 B | 2026-10-26T13:38:45.238863300+01:00 | `a3619eb03d3bc7847b68f335bba88a4abda442955614321fe96fe17f0ffd4194` |

Le paquet contient aussi un répertoire `.git` créé le 2026-10-26 à 13:44:49+01:00. Le validateur l'exclut (`list_files` ignore tout chemin dont une partie est `.git`) : `Files (4)` pour 4 fichiers de contenu, alors qu'un `find` brut comptait 35 fichiers, objets Git compris. Une empreinte de contenu ne doit donc pas inclure `.git`, `__pycache__` ni `*.pyc`.

## 2. Sources examinées

| Session | revision | runtimeState | activeTurnId | hasMoreBefore | JSONL | Rôle |
|---|---:|---|---|---|---|---|
| `f8e5b9ec-206e-491a-9f15-cce018837aea` | 48 | ready | null | false | 940 142 B, 128 lignes, `263a67fb79c5a29584a5b24304a639b4b78d1b3c05c4acfb3c21694b83137dfb`, mtime 13:43:45.803365300+01:00 | Demande de création et proposition non exécutée ; aucun Write/Edit du paquet |
| `ad2dd331-82dc-4327-8dc7-3a1cdf7fdb6b` | 43 | ready | null | false | 2 494 566 B, 765 lignes, `aa21d32303a20458c8b3bec236a7513157b93a23b1f796f6b07d33356c3f3470`, mtime 13:39:49.873281700+01:00 | Auteur de la baseline du paquet ; QA et rapport final |
| `7f7ab757-10c4-445e-864c-f47686b48836` | 135 | ready | null | false | 1 925 315 B, 476 lignes, `7c0233d9a9fa56831f68d4b8d5befa40c66d3069115f6462a0d1f9a8957b071c`, mtime 13:41:52.781631100+01:00 | Auteur du harnais tiers ; aucun Write/Edit du paquet trouvé |

Les champs `runtimeState`, `activeTurnId`, `revision` et `hasMoreBefore` ont été lus après les faits. Ils prouvent l'état de la session au moment de la lecture, pas l'état du tour d'écriture au moment de l'incident. Les trois sessions sont `ready` avec `activeTurnId: null` à la lecture ; aucune ne contient de correction utilisateur de ce cas. `f8e5b9ec` ne contient qu'un tour utilisateur et une proposition ; elle n'a écrit aucun fichier.

## 3. Chronologie

### 3.1 Heure locale (UTC+01:00)

| Heure locale | Événement | Preuve |
|---|---|---|
| 13:15:53 | Write du protocole par `ad2dd331` | JSONL `ad2dd331`, entrée 215 |
| 13:16:28 | Write du script par `ad2dd331` | JSONL `ad2dd331`, entrée 223 |
| 13:19:16 | Dernière édition du script ; baseline 29 725 B | JSONL `ad2dd331`, entrée 294 |
| 13:19:35 | Dernière édition du protocole ; baseline 15 240 B | JSONL `ad2dd331`, entrée 309 |
| 13:29:08 | mtime de `SKILL.md` ; la QA rapporte `PASS` 9/0/0 | empreinte du validateur ; rapport de `ad2dd331` |
| 13:35:36 | Script réécrit : 29 761 B, `a5007118…` | disque |
| 13:36:15 | Protocole réécrit : 15 676 B, `1de3f4ed…` | disque |
| 13:36:29 | Résultat tiers : 35/37, échecs 4a/4b | `resultat_avant_correction.txt` |
| 13:38:45 | Harnais indépendant écrit | `harnais.py` |
| 13:40:30 | Harnais tiers courant : 12 374 B, `73ff7c5c…` | disque |
| 13:40:56 | Résultat tiers final : 38/38 | `resultat_final.txt` |
| 13:44:49 | Commit Git dans le paquet | `.git/logs/HEAD` |
| 13:45:55–13:47:42 | Dumps et extraction de vérification, hors incident | répertoires temporaires |

### 3.2 Événements JSONL (UTC)

| Heure UTC | Session | Événement |
|---|---|---|
| 12:15:53.221Z | `ad2dd331` | Write du protocole, 14 771 caractères, 274 lignes |
| 12:16:28.663Z | `ad2dd331` | Write du script, 28 889 caractères, 814 lignes |
| 12:16:50.130Z | `ad2dd331` | Edit du script |
| 12:19:03.827Z | `ad2dd331` | Edit du script |
| 12:19:10.951Z | `ad2dd331` | Edit du script |
| 12:19:16.723Z | `ad2dd331` | Edit du script ; baseline 29 725 B |
| 12:19:35.259Z | `ad2dd331` | Edit du protocole ; baseline 15 240 B |
| 12:36:13.594Z | `7f7ab757` | Write du harnais, 12 159 caractères, 323 lignes |
| 12:40:32.555Z | `7f7ab757` | Edit du harnais ; ajout de `snap3` et `4pre` |
| 12:40:57.729Z | `f8e5b9ec` | Tour utilisateur de création |
| 12:40:57.791Z | `f8e5b9ec` | Proposition de l'assistant, non exécutée |

Aucun Write/Edit du paquet n'apparaît dans `ad2dd331` après 12:19:35Z, ni dans `7f7ab757`. Ce constat ne couvre pas les écritures faites par Bash ; l'auteur de la réécriture reste donc non identifié.

## 4. Portée réelle de la QA

Le validateur de `skill-file-qa` termine par :

```python
def finish_fingerprint(skill_md: Path, start_fp: Fingerprint, report: Reporter) -> None:
```

et l'appelle avec `skill_md` aux lignes 410 et 525. La stabilité et l'empreinte avant/après portent donc sur `SKILL.md` seul. `Files (4)` est une liste de noms, pas une empreinte de contenu. Le validateur est en lecture seule pour les fichiers du Skill.

Le `list_files` ignore `.git` :

```python
if ".git" in rel.parts:
    continue
```

Conséquence : un `RESULT PASS` obtenu à 13:29 ne prouve pas que le script et le protocole n'ont pas changé à 13:35 et 13:36. La QA finale rejouée pendant cette vérification a de nouveau rendu `PASS` 9/0/0, avec une empreinte de `SKILL.md` à 15 154 B, mtime 13:29:08+01:00, `6d755440…`, inchangée.

## 5. Reconstruction des versions antérieures

Le JSONL `ad2dd331` a été rejoué avec le script de `reconstruire-pilote-supprime-depuis-jsonl`, vers un répertoire temporaire. Le JSONL était en lecture seule et son empreinte a été relevée.

### 5.1 Script

```text
JSONL_FINGERPRINT size=2494566 mtime_ns=1793018389873281700 lines=765 sha256=aa21d32303a20458c8b3bec236a7513157b93a23b1f796f6b07d33356c3f3470
WRITE entry=223 chars=28889 lines=814
EDIT entry=230 occurrence=1
EDIT entry=284 occurrence=1
EDIT entry=288 occurrence=1
EDIT entry=294 occurrence=1
EVENTS writes=1 write_chars=28889 edits=4
RESULT lines=838 chars=29725 bytes_utf8=29725 trailing_newline=true
DUMP ... bytes=29725 sha256=be2b86b425b424aed034e980e400241a631830ebe4c1b74fecd7d9c781181e97
CLAIM PASS writes=1 edits=4
RC=0
```

Le hash du dump est exactement la baseline du script : `be2b86b4…`, 29 725 B, 838 lignes.

### 5.2 Protocole

```text
JSONL_FINGERPRINT size=2494566 mtime_ns=1793018389873281700 lines=765 sha256=aa21d32303a20458c8b3bec236a7513157b93a23b1f796f6b07d33356c3f3470
WRITE entry=215 chars=14771 lines=274
EDIT entry=309 occurrence=1
EVENTS writes=1 write_chars=14771 edits=1
RESULT lines=277 chars=14900 bytes_utf8=15240 trailing_newline=true
DUMP ... bytes=15240 sha256=fc2618d6f77d5a027f028fdc08081b4e106e8cf1a3cc4bb4fa6d69cf0517a290
CLAIM PASS writes=1 edits=1
RC=0
```

Le hash du dump est exactement la baseline du protocole : `fc2618d6…`, 15 240 B, 277 lignes.

Le script de rejeu n'a pas d'option de coupure temporelle : il rejoue la chaîne finale de la session. Ici, `ad2dd331` n'a plus édité ces deux fichiers après 12:19:35Z, ce qui permet l'égalité exacte. Si la même session avait édité après la baseline, le dump aurait représenté une version plus récente et il aurait fallu écrire « inconnu ».

## 6. Diff et attribution

Le diff entre la baseline reconstruite et la version courante ne contient que des correctifs de schéma et une ligne de documentation.

### 6.1 Script examiné, lignes 30–31

```diff
-TS_KEYS = ("horodatage", "horodatage_utc", "timestamp", "date", "ts")
-FILE_KEYS = ("fichier", "file", "chemin", "path", "nom_fichier")
+TS_KEYS = ("horodatage_iso", "horodatage", "horodatage_utc", "timestamp", "date", "ts")
+FILE_KEYS = ("chemin_fichier", "fichier", "file", "chemin", "path", "nom_fichier")
```

### 6.2 Protocole examiné, lignes 151, 154 et 265

```diff
-    for cle in ("horodatage", "horodatage_utc", "timestamp", "date", "ts"):
+    for cle in ("horodatage_iso", "horodatage", "horodatage_utc", "timestamp", "date", "ts"):
-    for cle in ("fichier", "file", "chemin", "path", "nom_fichier"):
+    for cle in ("chemin_fichier", "fichier", "file", "chemin", "path", "nom_fichier"):
@@
+| Supposer les noms de clés des entrées | Le journal réel utilise `horodatage_iso` et `chemin_fichier` ; avec des alias incomplets, toutes les entrées sont « sans signature » et une éviction reste invisible. | Vérifier le schéma sur une entrée réelle avant de conclure ; les alias supportés incluent `horodatage_iso`, `horodatage`, `timestamp` et `chemin_fichier`, `fichier`, `chemin`. |
```

Le delta est un correctif légitime : le journal réel utilise `horodatage_iso` et `chemin_fichier`, et les alias incomplets rendaient les entrées « sans signature ». Il n'y a ni règle supprimée, ni seuil affaibli, ni garde retirée. Décision : conserver la version courante ; ne pas rétablir la baseline.

## 7. Audit du test tiers

### 7.1 Version qui a échoué

Le harnais a un unique Write à 12:36:13.594Z, suivi d'un Edit à 12:40:32.555Z. La version en échec est celle du Write :

- 12 159 B, 323 lignes, SHA-256 `2fb80d0b9714087873e395a7bf31b8dfae7ce60b11c2ef9538553c2681a23904` ;
- `snap2` apparaît 7 fois, `snap3` 0 fois ;
- le test 4 compare `v2` à `snap2`, instantané pris après l'écriture de `v1`.

Le résultat du 13:36:29 contient :

```text
PASS 3c contenu modifie code 1 :: code=1
PASS 3d contenu modifie [MODIFIE]
FAIL 4a reecriture identique code 0 :: code=1
FAIL 4b reecriture identique signalee :: ['[MODIFIE] fichier module.txt (2 -> 2 octets)', 'RESULT: CHANGEMENTS (1 changement(s), 0 avertissement(s))']
...
HARNESS RESULT: FAIL (35/37)
  ECHEC: 4a reecriture identique code 0
  ECHEC: 4b reecriture identique signalee
```

Le test 4 est faux : il réécrit `v2` puis compare à `snap2`, qui décrit encore `v1`. Il doit signaler `MODIFIE`, pas `REECRIT-IDENTIQUE`. Ce n'est pas une régression du produit.

### 7.2 Version courante

L'Edit du 12:40:32Z ajoute `snap3` (instantané de `v2`) et un contrôle `4pre`, puis compare la réécriture de `v2` à `snap3` :

```diff
     # 4. reecriture identique (mtime change, contenu identique)
+    snap3 = ROOT / "sortie" / "instantane_v2.json"
+    code, _ = run(["instantane", "--cible", str(cible), "--recursif", "--sortie", str(snap3)])
+    check("4pre instantane de v2 code 0", code == 0, f"code={code}")
     time.sleep(0.05)
     (cible / "module.txt").write_text("v2", encoding="utf-8")
-    code, out = run(["comparer", "--instantane", str(snap2)])
+    code, out = run(["comparer", "--instantane", str(snap3)])
```

Le harnais courant est 12 374 B, 326 lignes, `73ff7c5c…`. Son `resultat_final.txt` contient :

```text
PASS 4pre instantane de v2 code 0 :: code=0
PASS 4a reecriture identique code 0 :: code=0
PASS 4b reecriture identique signalee :: ['[REECRIT-IDENTIQUE] fichier module.txt (contenu identique, mtime change)', 'RESULT: OK (1 avertissement(s))']
...
HARNESS RESULT: PASS (38/38)
```

Le résultat 38/38 est le contenu de l'artefact produit par l'auteur du harnais. Il n'a pas été ré-exécuté pendant cette vérification ; il est donc rapporté, pas reproduit ici. L'ancien verdict 35/37 est périmé, car le harnais a changé.

## 8. Re-test indépendant

Le harnais indépendant a été ré-exécuté pendant cette vérification. Il est hors du paquet et vérifie notamment que la cible n'est pas modifiée. Sortie :

```text
PASS 1a instantane code 0 :: code=0
PASS 1b instantane RESULT OK
PASS 1c manifeste present
PASS 1d cible intacte
PASS 2a comparer inchange code 0 :: code=0
PASS 2b comparer inchange RESULT OK
PASS 3a reecriture identique code 0 :: code=0
PASS 3b reecriture identique signalee :: ['[REECRIT-IDENTIQUE] fichier module.txt (contenu identique, mtime change)', 'RESULT: OK (1 avertissement(s))']
PASS 4a contenu modifie code 1 :: code=1
PASS 4b contenu modifie [MODIFIE]
PASS 5a instantane eviction pret :: code=0
PASS 6a eviction longueur constante code 1 :: code=1
PASS 6b eviction ATTENTION :: ['[MODIFIE] fichier journal.json (544 -> 544 octets)', '[ATTENTION] journal.json: 1 entree(s) disparue(s) dans journal (longueur inchangee: eviction possible): 2026-10-26T10:00:00Z|f0.py', '[AJOUTE] journal.json: 1 entree(s) dans journal: 2026-10-26T11:00:00Z|f9.py', 'RESULT: CHANGEMENTS (3 changement(s), 0 avertissement(s))']
PASS 6c signatures reconnues :: ['[MODIFIE] fichier journal.json (544 -> 544 octets)', '[ATTENTION] journal.json: 1 entree(s) disparue(s) dans journal (longueur inchangee: eviction possible): 2026-10-26T10:00:00Z|f0.py', '[AJOUTE] journal.json: 1 entree(s) dans journal: 2026-10-26T11:00:00Z|f9.py', 'RESULT: CHANGEMENTS (3 changement(s), 0 avertissement(s))']
PASS 7a ecrivain actif code 2 :: code=2
PASS 7b ecrivain actif INSTABLE
PASS 8a sauvegarde dans cible refusee :: code=2
PASS 8b message sauvegarde dans cible :: ['[ERREUR] sauvegarde impossible: le repertoire de sauvegarde ne doit pas etre dans la cible: C:\\Users\\Administrateur\\.qoder\\tmp\\verif-mine-20261026\\work\\memoire_aq']
PASS 9a ecrasement refuse sans --force :: code=2
PASS 9b ecrasement accepte avec --force :: code=0
PASS 10 script inchange par les tests
PASS 11 aucun cache dans le Skill :: []

HARNESS RESULT: PASS (22/22)
RC=0
```

Après l'exécution, le script et le protocole du paquet avaient toujours les hashes `a5007118…` et `1de3f4ed…`. Le harnais indépendant ne modifie pas le paquet et ne laisse pas de cache.

## 9. Écart corrigé

- Assertion d'origine (résumé de la session `f8e5b9ec`) : le harnais tiers final aurait 37/37.
- Sortie observée (`resultat_final.txt`, 13:40:56.329701200+01:00) : `HARNESS RESULT: PASS (38/38)`.
- Correction : ce cas retient 38/38. Le chiffre 37/37 n'est pas reproduit et n'est plus utilisé.

## 10. Grades

| Observation | Grade | Base |
|---|---|---|
| Empreintes de la baseline | FINAL | dumps rejoués égaux aux empreintes enregistrées |
| Empreintes de la version courante | FINAL | disque, lues deux fois |
| Portée de la QA limitée à `SKILL.md` | FINAL | code du validateur et sortie observée |
| Reconstruction des deux versions | FINAL | égalité SHA-256 exacte |
| Diff et attribution du correctif | FINAL | diff rejoué, lignes citées |
| Version du harnais en échec | FINAL | Write unique, hash complet |
| Résultat tiers 35/37 | FINAL | contenu de l'artefact |
| Résultat tiers 38/38 | PROVISIONAL pour l'exécution | artefact lu, harnais non ré-exécuté ici |
| Re-test indépendant 22/22 | FINAL | ré-exécuté, cible inchangée |
| QA finale `PASS` | FINAL pour `SKILL.md` seulement | portée du validateur |
| Auteur de la réécriture | NON IDENTIFIÉ | aucun Write/Edit du paquet dans les sessions examinées ; Bash non couvert |
| Assertion 37/37 | INVALID | contredite par `resultat_final.txt` |

## 11. Limites

- Aucune baseline antérieure à 13:19 n'a été observée ; l'état d'avant cette heure est inconnu.
- Le rejeu ne couvre que les `Write` et `Edit` de la chaîne principale. Il ignore les sidechains et s'arrête sur les outils non supportés, `EDIT MISS` et `EDIT AMBIGUOUS`. Une écriture par Bash n'apparaît pas.
- Le script de rejeu n'a pas de coupure temporelle ; il ne peut pas produire une version intermédiaire si la session a continué à éditer.
- La QA ne vérifie que `SKILL.md` ; les hashes des références et scripts sont enregistrés séparément.
- Le résultat tiers 38/38 n'a pas été ré-exécuté ici ; seul son artefact a été lu.
- `.git` a été créé après l'incident ; il est exclu des empreintes de contenu. Un commit modifie `.git`, pas le contenu des 4 fichiers.
- Les JSONL peuvent croître ; leurs empreintes ci-dessus sont datées du 2026-10-26 et doivent être revérifiées avant réutilisation.
- Ce fichier ne contient pas son propre SHA-256 : une valeur auto-référente serait immédiatement fausse. Les hashes de `SKILL.md` et de ce fichier sont enregistrés dans le rapport de livraison.

## 12. Commandes de reproduction

Rejeu du script et du protocole :

```bash
py -3 "<dossier-de-reconstruire-pilote-supprime-depuis-jsonl>/scripts/rejouer_pilote_jsonl.py" \
  --jsonl "C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/ad2dd331-82dc-4327-8dc7-3a1cdf7fdb6b.jsonl" \
  --file "C:/Users/Administrateur/.qoder/skills/verifier-effets-de-bord-verification-lecture-seule/scripts/instantane_effets_de_bord.py" \
  --expect-writes 1 --expect-edits 4 \
  --dump "<tmp>/avant_script.py"

py -3 "<dossier-de-reconstruire-pilote-supprime-depuis-jsonl>/scripts/rejouer_pilote_jsonl.py" \
  --jsonl "C:/Users/Administrateur/.qoder/projects/C--Users-Administrateur-Desktop-IMAM8MAHDI/ad2dd331-82dc-4327-8dc7-3a1cdf7fdb6b.jsonl" \
  --file "C:/Users/Administrateur/.qoder/skills/verifier-effets-de-bord-verification-lecture-seule/references/protocole-restauration.md" \
  --expect-writes 1 --expect-edits 1 \
  --dump "<tmp>/avant_protocole.md"
```

Diff et QA :

```bash
diff -u "<tmp>/avant_script.py" "C:/Users/Administrateur/.qoder/skills/verifier-effets-de-bord-verification-lecture-seule/scripts/instantane_effets_de_bord.py"
diff -u "<tmp>/avant_protocole.md" "C:/Users/Administrateur/.qoder/skills/verifier-effets-de-bord-verification-lecture-seule/references/protocole-restauration.md"

py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "C:/Users/Administrateur/.qoder/skills/verifier-effets-de-bord-verification-lecture-seule" \
  --workspace "C:/Users/Administrateur/Desktop/IMAM8MAHDI" \
  --stable-seconds 2 --stability-timeout 30
```

Le harnais indépendant se lance depuis son propre répertoire ; il recrée son sous-répertoire de travail et n'écrit pas dans le paquet.

## 13. Constat postérieur (2026-10-26, après rédaction)

Relevé lors de la vérification finale de ce Skill, après l'écriture de cet archive :

- Le paquet contient désormais 5 fichiers de contenu. `scripts/tester_instantane.py` est apparu à 2026-10-26T13:57:53.262225100+01:00 (24 235 B, `b203e500…`), puis son contenu a changé à 13:58:50.306317500+01:00 : même taille, SHA-256 `6184122ec59f21afb7489253b03d63d4e4ea542be017e256920174a1f8d5c924`. Le premier hash était déjà périmé au second relevé.
- Les quatre fichiers documentés au §1 n'ont pas changé : leurs empreintes ont été revérifiées et sont identiques (`6d755440…`, `bf4a778a…`, `1de3f4ed…`, `a5007118…`). La dérive est donc `AJOUTE`, pas `MODIFIE`.
- Le nouveau fichier est un auto-test isolé de `instantane_effets_de_bord.py` (fixtures jetables, sortie ASCII, codes 0/1/2). Il n'a été ni exécuté ni audité ici. Trois échantillons identiques ont été pris entre 13:59:59 et 14:00:04+01:00, mais une écriture venait d'avoir lieu et l'écrivain n'est pas identifié : son état est `PROVISIONAL`, pas `FINAL`.
- `Files (N)` reste un inventaire : il valait 4 au relevé initial et doit être réexaminé après tout ajout.
- Cet archive décrit l'état observé jusqu'au 2026-10-26T13:56:31+01:00, complété par ce constat postérieur ; toute empreinte dite « courante » doit être revérifiée avant réutilisation.
