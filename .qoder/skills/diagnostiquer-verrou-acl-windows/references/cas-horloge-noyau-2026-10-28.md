# Cas horloge_noyau — 2026-10-28

Source : session Qoder `8d7c4c1e-100e-4ad8-99ba-b97d06e57371`, projet `C--Users-Administrateur-Desktop-IMAM8MAHDI`. Lecture `read_chat_session` (turnLimit 20, `includeToolOutputs: true`) le 2026-10-28 : `runtimeState: ready`, `activeTurnId: null`, `revision: 44`, `hasMoreBefore: false`. Sortie complète archivée dans `%TEMP%` par l'outil puis relue par plages.

Les sorties d'outils sont recopiées telles quelles. Les accents y apparaissent en `?` : artefact de codepage de la console, pas une corruption du fichier.

## Séquence vérifiée

| Heure UTC | Événement |
| :--- | :--- |
| 02:48:27 | tour précédent : 10 en-têtes SPDX basculés |
| 02:48:55 | « Étends les en-têtes aux 283 fichiers » → 5 échecs, arrêt, demande d'accord |
| 02:56:20 | « Corrige la ligne 371, laisse horloge_noyau » |
| 02:56:20 | vérification finale : `WITH_SPDX 278`, `HORLOGE_MODIFIE=0` |

## Échecs verbatim

```text
PermissionError: [Errno 13] Permission denied: 'horloge_noyau\\__init__.py'
  (traceback pathlib write_bytes, ligne 32)

FILES 283 WITH_SPDX 146 READONLY 5
RO horloge_noyau\__init__.py
RO horloge_noyau\architecture_informe_couche_matiere_table_mizan.py
RO horloge_noyau\horloge_logique_mizan.py
RO horloge_noyau\tests\test_horloge_noyau_complet.py
RO horloge_noyau\verrou.py
```

```text
PermissionError: [WinError 5] Acc?s refus?: 'horloge_noyau\\__init__.py'
  (traceback sans frame pathlib, ligne 33)
```

## ACL verbatim (session)

```text
A    R               ...\horloge_noyau\__init__.py
--- ACL ---
horloge_noyau\__init__.py BUILTIN\Administrateurs:(I)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
                          PC-JG45TT2\Administrateur:(I)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
                          AUTORITE NT\Syst?me:(I)(F)
                          BUILTIN\Administrateurs:(I)(F)
                          PC-JG45TT2\Administrateur:(I)(F)
--- ACL dossier ---
horloge_noyau BUILTIN\Administrateurs:(OI)(CI)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
              PC-JG45TT2\Administrateur:(OI)(CI)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
--- ACL tests ---
horloge_noyau\tests BUILTIN\Administrateurs:(I)(OI)(CI)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
```

Compteurs de reprise : `FILES 283 DONE 146 TODO 137`, `TODO_READONLY 5`, `TODO_WRITABLE 132`. État final : `WITH_SPDX 278`, `SYNTAX_ERRORS 0`, `CACHE_NEW=0`, `HORLOGE_MODIFIE=0`.

Décision de l'utilisateur, verbatim : « Corrige la ligne 371, laisse horloge_noyau ».

## Recoupement live du 2026-10-28

Le verrou est toujours en place sur `ASTRO-Q°ODE_SYSTEME\horloge_noyau` :

```text
horloge_noyau BUILTIN\Administrateurs:(OI)(CI)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
              PC-JG45TT2\Administrateur:(OI)(CI)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
              AUTORITE NT\Syst?me:(I)(OI)(CI)(F)
              BUILTIN\Administrateurs:(I)(OI)(CI)(F)
              PC-JG45TT2\Administrateur:(I)(OI)(CI)(F)
```

L'ACE est **explicite** sur le dossier (aucun `(I)`), donc héritée `(I)` sur chaque fichier enfant. Entrées présentes : `VERROU.json`, `verrou.py`, `__init__.py`, `architecture_informe_couche_matiere_table_mizan.py`, `horloge_logique_mizan.py`, `tests/`, `sceau/`, `actes/`, `__pycache__/`. Attribut `R` relevé live sur les 4 `.py` de la racine et sur `VERROU.json` ; le 5e `.py` (sous `tests/`) n'est relevé `RO` que par la session. Aucun sous-dossier ne porte `R`.

Piège d'inventaire : `Desktop\IMAM8MAHDI` contient deux arbres `ASTRO*` ; `ASTRO-QODE-IMAM8MAHDI\horloge_noyau` n'a **aucune** ACE `DENY` (seulement `(F)`), avec les mêmes tailles de fichiers. Vérifier le chemin exact avant de conclure.

## Reproduction en fixture (hors production)

Fixture `%TEMP%\acl-ab-*`, propriétaire = compte courant, ACE appliquée par `icacls DOSSIER /deny UTILISATEUR:(OI)(CI)(WD,AD,WA)` — masque volontairement sans `WDAC` pour rester supprimable. Aucune écriture tentée sur le vrai `horloge_noyau`.

| Cas | Résultat mesuré |
| :--- | :--- |
| A — attribut `R` seul, aucune ACE | `write_text` → `[Errno 13] Permission denied` ; `chmod(S_IWRITE)` → OK ; écriture → OK |
| B — DENY `WD,AD,WA`, **sans** attribut `R` | `write_text`/`write_bytes` → `[Errno 13]`, `winerror=None` ; `READONLY_ATTR False` |
| B — `os.chmod(S_IWRITE)` | refusé, `errno=13 winerror=5` |
| B — `attrib -R` (fichier `R` + DENY `WA`) | rc **0**, stdout « Acc?s refus? - … », attribut `R` toujours posé |
| B — `icacls /remove:d` | rc 0, écriture rétablie (car `WDAC` non refusé) |
| Nettoyage | `attrib -R` puis `rmtree` : fixture supprimée, `%TEMP%\acl-*` vide |

## Classification des affirmations

| Affirmation | Statut | Preuve |
| :--- | :--- | :--- |
| lot bloqué à 146/283 sur le même fichier, reprise identique | REPRODUIT | dump, deux tours |
| `Errno 13` (I/O Python) et `WinError 5` (changement d'attribut) désignent le même refus | REPRODUIT | dump + fixtures A/B |
| l'erreur `[WinError 5]` du dump vient d'un `os.chmod` | VÉRIFIÉ | JSONL `8d7c4c1e…` ligne 358 : `os.chmod(p, stat.S_IWRITE)` en `<stdin>` 33, apparié au résultat 360 ; traceback sans frame `pathlib` ; rendu reproduit en fixture B |
| un refus d'écriture peut survenir **sans** attribut `R` | REPRODUIT | fixture B |
| `R` seul est corrigé par `chmod(S_IWRITE)` | REPRODUIT | fixture A |
| `chmod`/`attrib -R` ne peuvent rien quand `WA` est refusé | REPRODUIT | fixture B |
| `attrib -R` peut sortir rc 0 en imprimant « Accès refusé » sans changer l'attribut | REPRODUIT | fixture B |
| `DENY` est évalué avant `ALLOW`, un `(F)` simultané est sans effet | DOCUMENTÉ | sémantique Windows ; non testé en fixture |
| `WDAC`/`WO` refusés ⇒ `icacls /grant`, `/remove:d`, `/setowner` impossibles | DOCUMENTÉ | sémantique Windows ; corroboré par le besoin de `takeown` dans le cas réel |
| `takeown` franchit l'ACE puis permet de la retirer | NON VÉRIFIÉ | refusé par l'utilisateur, jamais exécuté |
| 5 fichiers `.py` bloqués, 278 en-têtes posés, sous-arbre intact | REPRODUIT | `WITH_SPDX 278`, `HORLOGE_MODIFIE=0` |
| l'ACE du dossier est explicite, celle des fichiers héritée `(I)` | REPRODUIT | `icacls` live du 2026-10-28 |

## Limites

- Les commandes exécutées ne figurent pas dans `read_chat_session` (seuls les noms et sorties d'outils) ; l'appel `chmod` a été retrouvé dans le JSONL de la session (ligne 358, `<stdin>` 33), pas dans le dump. Ne jamais citer une commande comme si elle venait du dump ; pour cette réconciliation, voir `reconcilier-commande-non-enregistree-session`.
- Aucune fixture avec `WDAC`/`WO` refusés n'a été créée : elle serait devenue indélébile sans `takeown`, ce qui aurait reproduit le problème à nettoyer.
- Aucune preuve d'exécution runtime du lot : seuls les compteurs d'écriture et les empreintes ont été mesurés.
