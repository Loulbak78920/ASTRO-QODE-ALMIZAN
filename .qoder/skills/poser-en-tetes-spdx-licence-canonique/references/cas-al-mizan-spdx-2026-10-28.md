# Cas Al-Mizan : en-têtes SPDX et licence canonique (2026-10-28)

## Source

- Session Qoder `8d7c4c1e-100e-4ad8-99ba-b97d06e57371`, titre « 创建可复用 Skill »,
  relue pendant ce travail (`revision 11`, `hasMoreBefore: false`) ; son premier
  message est horodaté 2026-10-28T02:19:36Z.
- Au moment de la lecture : `runtimeState: running`, `activeTurnId: 3939f8e8-aa32-4705-83a4-7ed609355a9f`
  (tour « Étends les en-têtes aux 283 fichiers »), donc **non conclu**.
- Relue après livraison : `revision 44`, `runtimeState: ready`, `activeTurnId: null`,
  `hasMoreBefore: false` — session terminée ; le tour « Étends » a abouti.
- Dépôt concerné : `C:\Users\Administrateur\Desktop\IMAM8MAHDI`, arbre `ASTRO-Q°ODE_SYSTEME`.

| Tour (UTC) | Message utilisateur | Sortie finale |
|---|---|---|
| 02:35:31 | « ajouter les en-têtes SPDX et la licence AGPL » | `CHANGED 10`, `HEADERS_OK 10`, `COOKIE_STILL_LINE1 10`, `CACHE_NEW=0` |
| 02:48:27 | « Bascule les en-têtes en GPL-3.0-only OR AGPL-3.0-only » | `SWITCHED 10`, `HEADERS_DUAL 10`, `OLD_EXPRESSION_LEFT 0` |
| 02:48:55 | « Étends les en-têtes aux 283 fichiers » | inventaire seul avant la coupure (`TOTAL 283`, `CRLF 36`, `SHEBANG 2`, `HASH_FIRST_NO_COOKIE 1`) |

## La correction qui porte la leçon

Le premier passage a posé `SPDX-License-Identifier: AGPL-3.0-only` alors que
`LICENSE.md:3-11` déclare un **dual** : « GPL-3.0 **ou** AGPL-3.0 ». L'utilisateur a
dû demander la bascule explicite en `GPL-3.0-only OR AGPL-3.0-only`.

Enseignement : un identifiant SPDX par fichier est un **octroi**. Un identifiant
unique restreint le droit accordé par le document de licence du dépôt. L'expression
fidèle se dérive du document, jamais de l'intention supposée de la demande
(« la licence AGPL » ne suffit pas quand le dépôt est dual).

## Fichiers de licence

- `LICENSE.md` (711 octets, 2026-10-22) nomme deux fichiers : `LICENSE-GPL:8` et
  `LICENSE-AGPL:11`.
- `LICENSE-AGPL` installé le 2026-10-28 : 34 523 octets, LF seul (661 `\n`, 0 `\r\n`),
  pas de BOM, se termine par `<https://www.gnu.org/licenses/>.\n`,
  SHA-256 `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0`
  — identique au texte servi par gnu.org le même jour.
- `LICENSE-GPL` **absent** au 2026-10-28T02:51:28Z, alors que `LICENSE.md` et les
  en-têtes `GPL-3.0-only` le nomment : référence pendante, à traiter explicitement.
- Contrôle postérieur (2026-10-28T03:00:44Z) : `LICENSE-GPL` désormais présent,
  35 149 octets, LF seul, sans BOM, SHA-256
  `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` — identique au
  texte FSF. Il a été créé par la session source encore active, pas par ce paquet :
  la référence n'est plus pendante à cet instant.
- `NOTICE.txt:6` fournit le titulaire recopié mot pour mot dans les en-têtes :
  `Copyright (C) 2026 IMAM8MAHDI / Astro-Code Ecosystem.`

## Textes FSF de référence (mesurés le 2026-10-28)

| Fichier | URL | Octets | SHA-256 | Première ligne |
|---|---|---|---|---|
| `gpl-3.0.txt` | `https://www.gnu.org/licenses/gpl-3.0.txt` | 35 149 | `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` | `GNU GENERAL PUBLIC LICENSE` / `Version 3, 29 June 2007` |
| `agpl-3.0.txt` | `https://www.gnu.org/licenses/agpl-3.0.txt` | 34 523 | `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0` | `GNU AFFERO GENERAL PUBLIC LICENSE` / `Version 3, 19 November 2007` |

Les deux sont en LF, sans BOM. Ces empreintes sont datées : si un téléchargement
diffère, constater la divergence et la signaler, ne pas ajuster l'attendu en silence.

## Sondes d'outillage reproduites hors Skills (2026-10-28)

| Sonde | Résultat mesuré | Conséquence |
|---|---|---|
| `sed -i 's/x = 1/x = 2/'` sur un fichier CRLF | `CRLF 2` → `CRLF 0` | `sed` réécrit tout le fichier en LF : interdit pour changer un identifiant SPDX |
| `py -3 -B -c "py_compile.compile(...)"` | crée `__pycache__/accent.cpython-314.pyc` | `-B` ne protège pas `py_compile` ; vérifier par `ast.parse` |
| `ast.parse(data.decode("utf-8-sig"))` | aucun fichier créé | contrôle syntaxique sans résidu |
| `open(p).read()` sans encodage | `locale.getpreferredencoding(False)` = `cp1252` | lire les octets et décoder en UTF-8 explicitement |
| `/tmp/…` passé à `py -3` natif | `FileNotFoundError` | les chemins MSYS ne traversent pas vers Python Windows ; utiliser un chemin `cygpath -w` ou projet |

## Harnais du paquet (22 assertions)

Script `scripts/poser_entetes_spdx.py`, harnais jetable hors arborescence de Skills,
un dossier par cas, assertions sur les octets après écriture :

| Cas | Attendu | Résultat |
|---|---|---|
| A cookie LF | en-tête après le cookie, octets exacts | PASS |
| B cookie CRLF | 4 `\r\n`, 0 LF seul | PASS |
| C shebang + cookie CRLF | cookie reste ligne 2, en-tête lignes 3-4 | PASS |
| D shebang sans cookie | en-tête après le shebang | PASS |
| E ni shebang ni cookie | en-tête avant la docstring | PASS |
| F BOM | `REFUSED a.py bom`, fichier intact, rc 1 | PASS |
| G fins de ligne mixtes | `REFUSED a.py mixed_eol`, rc 1 | PASS |
| H en-tête déjà présent | `SKIPPED`, octets inchangés, rc 0 | PASS |
| I expression différente | `DIFFERS`, aucune écriture, rc 1 | PASS |
| J `--remplacer` CRLF | `SWITCHED`, valeur relue = expression cible, CRLF préservés | PASS |
| K second passage | `SKIPPED`, octets stables | PASS |
| L cookie ligne 3 | `REFUSED a.py cookie_too_deep`, rc 1 | PASS |
| M expression invalide | `FAIL  invalid SPDX expression`, rc 2 | PASS |
| N syntaxe invalide | `REFUSED a.py ast_error`, aucune écriture, rc 1 | PASS |
| O sans `--appliquer` | `WOULD_CHANGED`, aucune écriture, rc 0 | PASS |
| P fichier vide | deux lignes + fin de ligne, rc 0 | PASS |
| Q sous-dossier `.qoder` | ignoré | PASS |
| R fichier sans fin de ligne | absence préservée | PASS |
| Résidus | aucun `__pycache__` dans la fixture ni dans le Skill | PASS |

Deux défauts réels ont été trouvés par ce harnais avant livraison : l'exclusion
`.qoder` s'appliquait aux composants **absolus** du chemin (une racine située sous
`~/.qoder` était donc entièrement ignorée, `TOTAL 0`), et un fichier vide ressortait
sans fin de ligne. Corrigés puis rejoués : `FAILS 0`.

## Rejeu indépendant (2026-10-28T03:05Z)

Rejeu hors Skills, par un harnais distinct de celui de l'auteur (supprimé depuis) :
les 18 situations du tableau ci-dessus, plus deux cas ajoutés — cookie en ligne 2
précédé d'un commentaire, et cookie en ligne 6. Résultat après correction : 20 cas,
0 échec, aucun `__pycache__`.

Défaut trouvé par ce rejeu et corrigé dans le script : `anchor_index` exigeait que le
cookie soit à l'index `start`, donc un cookie PEP 263 valide en **ligne 2** précédé
d'un simple commentaire était refusé `cookie_too_deep`. Le script accepte désormais
un cookie en ligne 1 ou 2 et ne refuse que les lignes 3 à 8 ; le cas L (cookie
ligne 3) reste refusé.

## État du dépôt au 2026-10-28T02:51:28Z (UTC, instantané)

- 283 fichiers `.py` au total, dont 9 sous `.qoder/tmp` ; 278 portent
  `SPDX-License-Identifier: GPL-3.0-only OR AGPL-3.0-only`, soit 269 hors `.qoder/tmp`.
  36 fichiers sont en CRLF au total, 35 hors `.qoder/tmp` (recompté à 03:05Z :
  identique au décompte de 02:51:28Z).
- `LICENSE-GPL` toujours absent à cet instant (présent au contrôle de 03:00:44Z) ;
  `LICENSE-AGPL` conforme à l'empreinte ci-dessus.
- Le tour d'extension étant encore en cours à la lecture, **aucun décompte final
  283/283 ne peut être affirmé** : état `UNVERIFIED`.

## Contrôle postérieur des 283 fichiers (2026-10-28T03:07Z)

Audit en lecture seule de `ASTRO-Q°ODE_SYSTEME` sous `py -3 -B`, `ast.parse`
compris, sans écriture ni cache :

| Mesure | Valeur |
|---|---:|
| fichiers `.py` | 283 |
| en-tête `GPL-3.0-only OR AGPL-3.0-only` | 278 |
| en-tête `AGPL-3.0-only` seul | 0 |
| sans en-tête | 5 |
| `ast.parse` en erreur | 0 |
| fichiers CRLF | 36 |
| BOM | 0 |
| fins de ligne mixtes | 0 |
| en-tête placé avant le cookie | 0 |

Les 5 fichiers sans en-tête sont ceux de `horloge_noyau` : `__init__.py`,
`architecture_informe_couche_matiere_table_mizan.py`, `horloge_logique_mizan.py`,
`tests/test_horloge_noyau_complet.py` et `verrou.py`. Tous portent l'attribut `R`,
et `icacls horloge_noyau` montre un DENY explicite :

```text
<dossier> BUILTIN\Administrateurs:(OI)(CI)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
          <compte>:(OI)(CI)(DENY)(DE,WDAC,WO,WD,AD,WEA,DC,WA)
          ... (I)(OI)(CI)(F) hérités
```

Les ACE explicites priment sur les droits hérités : le lot de la session source s'est
arrêté sur ces fichiers, et `icacls` explique le refus malgré le `(I)(F)` du compte.
Décision de l'utilisateur : laisser `horloge_noyau` intact, ne pas forcer l'ACL.

`plateforme_cybersecurite_saas_almizan.py` était cassé avant le lot (`:371`, `]` au
lieu de `}`) ; corrigé d'un caractère sur demande, il parse désormais et aucun des
283 fichiers ne produit d'erreur `ast.parse`. Le manifeste du lot est resté sous
`%TEMP%\spdx-headers-apres-2026-10-28.json`.

## Contrôle de parité des ajouts (2026-10-28T03:10Z)

Fixture jetable hors Skills (`%TEMP%`, supprimée après contrôle), trois cas :

| Cas | Sortie réelle | Effet |
|---|---|---|
| `a.py` valide, attribut `R` | `REFUSED a.py io_error:Permission denied`, rc 1 | octets inchangés |
| `b.py` cassé à la ligne 1 | `REFUSED b.py ast_error:3:invalid syntax`, rc 1 | octets inchangés |
| `c.py` CRLF | `CHANGED c.py`, `crlf 3`, `lf 3` | en-tête ajouté, CRLF préservé |

Sur `b.py`, l'erreur d'origine est en ligne 1 (`invalid syntax`) et se retrouve en
ligne 3 après insertion : même message, `ligne + 2`. `AST_OK 2` pour `CHANGED 1`
s'explique par `a.py`, parsé avant que son écriture n'échoue sur l'attribut `R`.

## Classement honnête

| Affirmation | Statut |
|---|---|
| En-têtes posés sur 10 modules après le cookie, cache nul, cookie ligne 1 | **Observé** (session) |
| Bascule dual demandée par l'utilisateur et appliquée sur 10 fichiers | **Observé** (session) |
| `LICENSE-AGPL` = texte FSF exact, LF, sans BOM | **Observé** (session + revérifié ici) |
| `LICENSE-GPL` absent malgré la référence de `LICENSE.md` | **Observé** (ici) |
| `sed` normalise les fins de ligne, `py_compile` écrit malgré `-B`, `/tmp` invisible pour `py -3` | **Vérifié par fixture** (ici) |
| Comportement du script sur les 18 situations du harnais | **Vérifié par fixture** (ici) |
| Extension aux 283 fichiers | **Observé** (contrôle postérieur : 278/283, 5 bloqués par un DENY explicite) |
| DENY explicite sur `horloge_noyau`, attribut `R` | **Observé** (`icacls`, `attrib`) |
| Manifeste de lot déposé sous `%TEMP%` | **Observé** (fichier présent le 2026-10-28) |
| Politique « ancre après le shebang quand le cookie manque » | **Prescrite** après arbitrage utilisateur, non observée dans la session |
| Empreintes gnu.org valables après le 2026-10-28 | **Non vérifié** (à re-mesurer) |

## Limites

- Cible Python uniquement ; les autres langages et les blocs SPDX multi-lignes ne
  sont pas couverts.
- Le script n'installe aucune licence : le téléchargement et sa vérification restent
  des gestes explicites, visibles dans le rapport.
- Les artefacts générés (HTML, JSON) ne reçoivent pas d'en-tête : leurs générateurs
  en portent un.
- Le script refuse BOM et fins de ligne mixtes au lieu de choisir : la décision
  revient à l'humain.
- Une empreinte de licence est un fait daté, pas une garantie permanente.
