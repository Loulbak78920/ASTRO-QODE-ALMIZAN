---
name: poser-en-tetes-spdx-licence-canonique
description: "Poser ou corriger les en-têtes SPDX d'un dépôt et y installer le texte de licence canonique : lire LICENSE, NOTICE et CITATION pour relever le titulaire et la licence réellement déclarée, dériver l'expression SPDX exacte (un identifiant par fichier est un octroi et ne doit pas restreindre un dual, forme fidèle `GPL-3.0-only OR AGPL-3.0-only`), télécharger le texte FSF par curl direct depuis gnu.org avec contrôle taille, SHA-256, LF et absence de BOM, insérer les deux lignes après le cookie PEP 263 ou le shebang de façon idempotente en préservant les fins de ligne, vérifier par ast.parse sous py -3 -B sans créer de __pycache__, puis signaler les références de licence restées sans fichier. Utiliser pour des en-têtes SPDX, une licence AGPL ou GPL, une bascule d'identifiant SPDX, l'extension d'en-têtes à un arbre de fichiers, ou un fichier de licence référencé mais absent. 中文触发：SPDX 文件头、许可证原文、AGPL/GPL 双许可、许可证标识符切换、批量加文件头、行尾保持、ast.parse 校验。"
---

# Poser les en-têtes SPDX et installer la licence canonique

## Portée

Traiter un dépôt de code Python : fixer l'expression SPDX fidèle au document de
licence, installer le texte canonique, poser deux lignes d'en-tête par fichier sans
réécrire les autres octets, puis le prouver. Ce Skill ne choisit pas la licence à la
place de l'auteur et n'installe aucun texte sans contrôle d'empreinte.

## 1. Établir l'expression avant toute écriture

1. Lire `LICENSE.md`, `LICENSE`, `COPYING`, `NOTICE.txt` et `CITATION.cff`.
2. Relever la licence déclarée et le titulaire **exact**.
3. En déduire l'expression :
   - un seul texte → identifiant simple ; `-only` sauf mention explicite « or later » ;
   - deux licences au choix → `A OR B` ;
   - permission additionnelle → `A WITH B`.
4. Recopier le titulaire depuis `NOTICE` mot pour mot ; ne rien inventer.
5. Fixer le périmètre : racine, exclusions (copies, archives, `.qoder`, `__pycache__`),
   et exclusion des artefacts générés (HTML, JSON) dont les générateurs portent l'en-tête.

**Invariant** : un identifiant SPDX par fichier est un octroi. Un identifiant unique
restreint le droit accordé par le document de licence. Si la demande dit « AGPL » mais
que le document est dual, écrire `GPL-3.0-only OR AGPL-3.0-only` et le dire.

## 2. Installer les textes de licence canoniques

Télécharger le texte FSF brut, sans outil qui résume ou reformate :

```bash
curl -sS -o LICENSE-AGPL https://www.gnu.org/licenses/agpl-3.0.txt
curl -sS -o LICENSE-GPL  https://www.gnu.org/licenses/gpl-3.0.txt
```

Vérifier chaque fichier (octets, empreinte, LF seul, pas de BOM, première ligne) :

```bash
py -3 -B -c "
import hashlib, sys
for p in sys.argv[1:]:
    d = open(p, 'rb').read()
    print(p, len(d), hashlib.sha256(d).hexdigest(),
          'crlf', d.count(b'\r\n'), 'lf', d.count(b'\n'),
          'bom', d[:3] == b'\xef\xbb\xbf', 'first', d.split(b'\n')[0].decode())
" LICENSE-AGPL LICENSE-GPL
```

Empreintes mesurées le 2026-10-28 :

| Fichier | Octets | SHA-256 |
|---|---|---|
| AGPL-3.0 | 34 523 | `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0` |
| GPL-3.0 | 35 149 | `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` |

Une divergence est un fait à signaler (gnu.org a changé, ou la réponse est
interceptée) ; ne jamais ajuster l'attendu en silence pour faire passer le contrôle.
Ces empreintes sont datées : les re-mesurer avant de les citer comme actuelles.

Ensuite, chaque fichier nommé par le document de licence doit exister. Lister les
noms cités et relever ceux qui manquent ; une référence pendante (document renvoyant
à un `LICENSE-GPL` absent) se traite explicitement, jamais par omission.

## 3. Poser les en-têtes

Toujours en deux temps : lecture seule, puis écriture.

```bash
py -3 -B scripts/poser_entetes_spdx.py --racine <DIR> \
  --licence "GPL-3.0-only OR AGPL-3.0-only" \
  --titulaire "2026 IMAM8MAHDI / Astro-Code Ecosystem" \
  --exclure _AL_MIZAN_COPIE_SOI
```

Lire les lignes `WOULD_CHANGED`, `REFUSED` et `DIFFERS`, puis rejouer avec
`--appliquer`. Pour changer volontairement une expression déjà présente, ajouter
`--remplacer` ; sans ce drapeau, un identifiant différent est signalé `DIFFERS` et
laissé intact.

Règles d'ancrage appliquées par le script :

| Situation | Insertion |
|---|---|
| cookie `# -*- coding: utf-8 -*-` en ligne 1 ou 2 | après le cookie, qui reste en place (PEP 263) |
| shebang seul | après le shebang |
| ni shebang ni cookie | en tête de fichier, avant la docstring |
| cookie détecté lignes 3 à 8 | `REFUSED cookie_too_deep` ; plus bas, ce n'est plus un cookie PEP 263 et il n'est pas détecté |
| BOM, fins de ligne mixtes, non UTF-8, syntaxe invalide | `REFUSED`, aucune écriture |

Le script est idempotent (`SKIPPED` si l'expression est déjà là), préserve le style
de fin de ligne du fichier et l'absence de fin de ligne finale, et valide le texte
modifié par `ast.parse` avant écriture. Il n'écrit jamais les lignes de licence.

### Lots partiels et fichiers bloqués

Un lot peut s'arrêter sur un fichier non inscriptible : le script imprime
`REFUSED <fichier> io_error:Permission denied`, poursuit et rend `RESULT FAIL`.
Un DENY explicite sur le compte bloque l'écriture même pour un administrateur,
malgré un `(I)(F)` hérité ; `icacls <dossier>` le montre. Ne pas contourner par
`attrib -R`, `takeown` ni `icacls /reset` : relever les fichiers bloqués, les
exclure (`--exclure <sous-dossier>`) seulement sur décision explicite, et
recompter. Pour établir l'origine du verrou, appliquer
`diagnostiquer-verrou-acl-windows`. Cas mesuré : 278 fichiers traités sur 283,
les 5 restants sous `horloge_noyau`, tous marqués `R` (dont un dans `tests/`).

Après chaque lot partiel, recompter l'expression **entière** et écrire un
manifeste `(chemin relatif, octets, SHA-256)` des fichiers traités. Le déposer
sous `tempfile.gettempdir()` : un chemin `/tmp` n'est pas résolu par le `py -3`
Windows de cette machine. Recomptes mesurés de la même campagne : 10, puis 146, puis 278.

### Fichier déjà cassé avant le lot

`REFUSED <fichier> ast_error:<ligne>:<message>` sur un fichier déjà invalide
n'est pas une régression. Avant d'insérer, parser les octets d'origine ; si le
parse échoue, relever `(ligne, message)`. Après insertion, exiger le même message
et `ligne + 2` (les deux lignes d'en-tête ajoutées). Cas mesuré :
`plateforme_cybersecurite_saas_almizan.py:371`, `]` au lieu de `}`, corrigé d'un
seul caractère sur demande explicite. Ne jamais réparer la syntaxe sans demande.

## 4. Vérifier après écriture

Ne pas se contenter du `RESULT` du script ; recouper :

```bash
head -4 <UN_FICHIER_MODIFIE>
grep -rh "SPDX-License-Identifier" --include=*.py <DIR> | sed 's/^ *//' | sort | uniq -c
find <DIR> -name __pycache__ -o -name '*.pyc'
py -3 -B -c "
import ast, sys
for p in sys.argv[1:]:
    ast.parse(open(p, 'rb').read().decode('utf-8-sig'), filename=p)
print('AST_OK', len(sys.argv) - 1)
" <FICHIERS_MODIFIES>
```

Contrôles attendus :

- le décompte par expression est celui du périmètre annoncé, et l'expression est
  comparée **entière** (une bascule laisse l'ancien jeton à l'intérieur du nouveau,
  donc une recherche de sous-chaîne ne prouve rien) ;
- le cookie est resté en ligne 1 ou 2, le shebang en ligne 1 ;
- un fichier CRLF avant l'écriture l'est encore (`CRLF == LF`), et le nombre de
  fichiers CRLF non traités n'a pas bougé ;
- aucun `__pycache__` ni `*.pyc` créé par la vérification ;
- seuls les fichiers annoncés ont changé (diff Git, ou comparaison des empreintes) ;
- le manifeste du lot couvre exactement les fichiers annoncés, et le recompte de
  l'expression entière égale ce total.

## Pièges vérifiés

| Piège | Effet mesuré | Geste correct |
|---|---|---|
| `sed -i` pour changer l'identifiant | convertit tout le fichier CRLF en LF | édition au niveau octets par le script |
| `py_compile` sous `py -3 -B` | écrit `__pycache__` malgré `-B` | `ast.parse` uniquement |
| `open(p).read()` sans encodage | défaut `cp1252` sur cette machine, texte mal décodé | lire les octets, décoder en UTF-8 |
| chemin `/tmp/...` passé à `py -3` natif | `FileNotFoundError` : chemin MSYS invisible | chemin `cygpath -w` ou dossier du projet |
| en-tête posé avant le cookie | cookie déplacé hors des lignes 1-2, donc inopérant | ancre après le cookie |
| identifiant unique sur un dual | restreint l'octroi du dépôt | expression `A OR B` |
| `OLD_EXPRESSION_LEFT` par sous-chaîne | l'ancien jeton est contenu dans le nouveau | comparer la valeur extraite en entier |
| racine trop haute | en-têtes dans les copies et archives | racine étroite, `--exclure` |
| `WebFetch` sur le texte de licence | texte résumé ou reformaté | `curl` du fichier brut gnu.org |
| DENY explicite `icacls` sur un dossier | `REFUSED … io_error:Permission denied` malgré un `(I)(F)` hérité | ne pas forcer l'ACL ; exclure et signaler |
| fichier déjà cassé + `ast.parse` du texte inséré | refus pris pour une régression du lot | parser l'original, comparer message et `ligne + 2` |

## Frontières

- `skill-file-qa` valide le paquet d'un Skill ; il ne vérifie pas les en-têtes d'un dépôt.
- `lock-lf-endings-skill-repo` fige les fins de ligne par `.gitattributes` ; ici on les
  préserve à l'écriture, sans configurer Git.
- `verifier-unicode-fichiers-windows` outille les assertions d'octets non-ASCII sur
  Windows ; l'utiliser si un contrôle porte sur des accents.
- `sceller-manifeste-integrite-sans-circularite` intervient après : sceller un
  manifeste quand des en-têtes viennent d'être ajoutés.
- `requalifier-preuves-calcul-fini` mentionne l'en-tête SPDX comme sous-étape d'un cas
  Riemann ; pour poser, basculer ou étendre réellement des en-têtes, appliquer ce
  Skill-ci.

## Ressources

- `scripts/poser_entetes_spdx.py` — insertion idempotente, sortie ASCII, rc 0/1/2
  (`2` = usage ou environnement). Options : `--racine`, `--licence`, `--titulaire`,
  `--extension`, `--exclure`, `--appliquer`, `--remplacer`, `--verbose`.
- `references/cas-al-mizan-spdx-2026-10-28.md` — cas daté : sorties réelles, correction
  de l'utilisateur, empreintes des textes, sondes d'outillage, 22 assertions du harnais,
  classement observé / vérifié / prescrit / non vérifié.

## Critères de sortie

- Expression SPDX justifiée par le document de licence, titulaire recopié de `NOTICE`.
- Textes de licence installés, empreinte et fins de ligne relevées et conformes.
- Script : `RESULT PASS`, `REFUSED 0` ou chaque refus expliqué ; `AST_OK` compte les
  textes qui ont passé `ast.parse`, y compris un fichier dont l'écriture échoue
  ensuite, donc `AST_OK` peut dépasser `CHANGED`.
- Recoupement indépendant sur au moins trois fichiers, cookie et EOL vérifiés.
- Références de licence pendantes listées, avec la décision prise.
- Aucun `__pycache__` ajouté, aucun commit ni push sans demande explicite.
