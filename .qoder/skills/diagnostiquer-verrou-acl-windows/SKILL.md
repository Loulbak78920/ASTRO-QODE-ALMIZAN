---
name: diagnostiquer-verrou-acl-windows
description: "Diagnostiquer un refus d'écriture Windows qui persiste malgré un attribut lecture seule apparemment corrigé — PermissionError [Errno 13] ou [WinError 5] sur un fichier, lot d'écriture qui s'arrête toujours au même dossier, attrib R encore affiché, icacls révélant une ACE DENY. Distinguer l'attribut R (symptôme, parfois absent) d'un refus explicite, rappeler que Windows évalue DENY avant ALLOW donc qu'un (F) simultané ne rétablit rien, décoder le masque (WD, AD, WA, WDAC, WO, DE) pour prouver qu'aucun os.chmod, attrib -R ou icacls /grant ne peut aboutir, puis s'arrêter et demander l'accord avant tout takeown ou retrait d'ACE ; laisser le sous-arbre verrouillé intact, terminer les autres fichiers du lot et prouver zéro modification du sous-arbre."
---

# Diagnostiquer un verrou ACL Windows

## Vue d'ensemble

Un refus d'écriture qui survit au retrait de l'attribut lecture seule ne vient pas de l'attribut : il vient d'une ACE `DENY`. Ce skill mène du symptôme à la preuve `icacls`, puis s'arrête à une porte de décision — désarmer une ACE est une modification de garde d'intégrité, jamais une correction d'erreur.

## Déclencheurs

- `PermissionError` `[Errno 13]` ou `[WinError 5]` sur un fichier qui existe et dont on est propriétaire.
- Un lot de N fichiers s'arrête toujours au même dossier, y compris après reprise.
- `attrib`/`ls` affichent `R`, mais `attrib -R` ou un `chmod` ne rétablit pas l'écriture.
- `icacls` montre `(DENY)` **et** `(F)` pour les mêmes principaux.
- Question posée : « pourquoi l'écriture échoue alors que ce compte est administrateur ? »

## Procédure

### 1. Quantifier l'arrêt avant toute reprise

Compter : total, déjà écrits, restants, restants en lecture seule, restants inscriptibles. Deux échecs identiques au même fichier = diagnostic, pas nouvelle tentative.

### 2. Classer l'erreur Python

| Message | Trace d'appel | Lecture |
| :--- | :--- | :--- |
| `[Errno 13] Permission denied: 'f'` | `open`/`write_text`/`write_bytes` | refus d'ouverture en écriture |
| `[WinError 5] Accès refusé: 'f'` | traceback **sans** frame `pathlib` | typiquement `os.chmod`/`SetFileAttributesW` : le changement d'attribut lui-même est refusé |

Les deux sont le même refus d'accès Windows. Le second est plus informatif : il prouve que `WA` est refusé, donc que l'attribut ne peut pas être modifié.

### 3. Lire l'attribut, sans conclure

`attrib`, `ls -l`, ou `os.stat(f).st_file_attributes & stat.FILE_ATTRIBUTE_READONLY`.

`R` est un symptôme : une écriture peut être refusée **sans** `R` (reproduit), et `R` seul est corrigé par `chmod` (reproduit). L'attribut ne prouve ni n'exclut l'ACL.

### 4. Lire l'ACL : fichier, dossier, puis parents

Remplacements valables pour tous les blocs bash de ce document : `CHEMIN_FICHIER` et `CHEMIN_DOSSIER` = fichier et dossier bloqués, `CIBLE` = l'un des deux ; cwd = dossier de ce Skill.

```bash
icacls "CHEMIN_FICHIER"
icacls "CHEMIN_DOSSIER"
```

Une ACE portant `(I)` est héritée : corriger l'enfant ne sert à rien, il faut trouver le premier ancêtre dont la ligne n'a pas `(I)`. Trier avec le script en lecture seule :

```bash
py -3 -B scripts/diagnostiquer_verrou_acl.py "CIBLE"
```

Sortie stable, ASCII, sans écriture : `VERDICT STOP_DENY` + rc 10 ; `VERDICT ATTRIBUTE_ONLY` ou `NO_DENY_FOUND` + rc 0 ; `ERROR` + rc 2.

### 5. Décoder le masque

| Jeton | Droit | Conséquence observée |
| :--- | :--- | :--- |
| `WD`, `AD` | Write data, Append data | aucun octet écrit, aucun fichier créé |
| `WA` | Write attributes | `chmod(S_IWRITE)` et `attrib -R` impossibles |
| `WDAC`, `WO` | Write DACL, Write owner | `icacls /grant`, `/remove:d`, `/setowner` impossibles |
| `DE`, `DC` | Delete, Delete child | suppression impossible, y compris des enfants |
| `WEA` | Write extended attributes | pas de flux/EA modifiable |
| `RC`, `RD`, `X`, `S` | Read control/data, execute, sync | non refusés ici : lecture et exécution restent possibles |

`DENY` est évalué avant `ALLOW` : un `(F)` accordé aux mêmes principaux ne rétablit rien. Seul un contournement par privilège (`takeown`, `SeTakeOwnershipPrivilege`) franchit une ACE `WDAC`.

### 6. Décider, puis s'arrêter

Chercher les signes de verrou volontaire : `verrou.py`, `VERROU.json`, `__init__.py`, sous-dossiers `sceau/`, `actes/`. Un sous-arbre gelé sur un noyau d'horloge ou une chaîne de sceaux est une garde d'intégrité, pas un bug.

Présenter les preuves et **demander l'accord**. Sans accord explicite, ne jamais :

- exécuter `takeown`, `icacls /remove:d`, `/grant`, `/reset`, ni couper l'héritage ;
- déplacer, renommer ou supprimer le sous-arbre ;
- relancer en boucle, ni exécuter sous `SYSTEM`/`TrustedInstaller` pour contourner ;
- élever l'agent ou changer les droits du dossier parent « pour débloquer ».

Si l'accord est donné : relever l'ACL et le propriétaire verbatim d'abord, puis `takeown`, retrait de l'ACE, restauration du propriétaire et de l'attribut `R` s'il était posé. Cette branche n'a pas été exercée dans le paquet de preuves ; la présenter comme une procédure à vérifier, pas comme un résultat mesuré.

### 7. Terminer le reste et prouver

Intercepter `PermissionError` **par fichier** et continuer le lot. Puis produire :

| Mesure | Attendu |
| :--- | :--- |
| fichiers traités | total moins la liste bloquée |
| fichiers bloqués | énumérés un par un |
| sous-arbre bloqué | empreintes et mtime identiques avant/après |
| propriétaire du sous-arbre | inchangé (`(Get-Acl CHEMIN).Owner`) |
| `takeown` exécuté | 0 |

## Modèle de rapport

```text
BLOQUES 5/283
SOUS_ARBRE horloge_noyau  (5 .py + VERROU.json, attribut R)
DENY BUILTIN\Administrateurs + PC\Administrateur  mask=DE,WDAC,WO,WD,AD,WEA,DC,WA
     explicite sur le dossier, herite (I) sur les fichiers
ALLOW_F_COEXISTS yes  -> sans effet, DENY evalue d'abord
CAN_WRITE_DATA False  CAN_WRITE_ATTRIB False  CAN_EDIT_ACL False
INTOUCHE 5/5  ecarts d'empreinte 0  proprietaire inchange
DECISION REQUISE takeown + retrait du DENY, ou conserver la garde
```

## Anti-patrons

| Geste | Pourquoi il échoue |
| :--- | :--- |
| relancer le même lot après échec | même ACE, même fichier, même refus |
| `chmod -R u+w` / `attrib -R /S /D` | `WA` refusé ; `attrib` peut sortir en rc 0 en imprimant « Accès refusé » |
| se fier au code retour d'`attrib` | rc 0 avec attribut inchangé (reproduit) |
| `icacls /grant` ou `/remove:d` | `WDAC`/`WO` refusés |
| `takeown` immédiat | contourne une garde d'intégrité sans accord |
| supprimer ou déplacer le dossier | `DE`/`DC` refusés, et destruction d'un verrou volontaire |
| conclure « c'est un antivirus » | aucune preuve ; l'ACL est lisible et suffit |
| corriger l'enfant d'une ACE `(I)` | l'ACE vit sur l'ancêtre |

## Vérification

```bash
py -3 -B scripts/diagnostiquer_verrou_acl.py "CIBLE"
```

- `STOP_DENY` + rc 10 sur le dossier verrouillé ; `NO_DENY_FOUND` + rc 0 sur un dossier inscriptible ; `ATTRIBUTE_ONLY` + rc 0 sur un fichier `R` sans DENY.
- `--json` émet `verdict`, `denied_applying`, `denied_rights`, `can_*`, sans champ `code`.
- `READONLY_ATTR` et `CAN_WRITE_*` sont indépendants : `CAN_WRITE_DATA` ne reflète que l'ACL.
- Relever les empreintes SHA-256 du sous-arbre bloqué avant et après le lot.

## Ressources

- [scripts/diagnostiquer_verrou_acl.py](scripts/diagnostiquer_verrou_acl.py) — triage lecture seule, `icacls` sur le fichier et ses ancêtres, masque décodé, rc 0/10/2.
- [references/cas-horloge-noyau-2026-10-28.md](references/cas-horloge-noyau-2026-10-28.md) — preuves verbatim de la session source, recoupement live et reproduction en fixture.
- Skill voisin : `poser-en-tetes-spdx-licence-canonique` (lot d'écriture qui a rencontré ce verrou).
