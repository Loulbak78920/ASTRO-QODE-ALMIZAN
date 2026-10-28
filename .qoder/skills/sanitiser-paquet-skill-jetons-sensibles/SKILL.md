---
name: sanitiser-paquet-skill-jetons-sensibles
description: "Assainir un paquet Skill qui a recopié des jetons personnels (date et lieu de naissance, communes, départements, codes postaux, GPS) : geler les empreintes avant écriture, auditer avec un scanneur masqué qui n'affiche jamais les valeurs, remplacer à la main par les marqueurs JJ/MM/AAAA, <commune>, <département>, <code>, prouver l'absence sur une copie négative avec AUCUN_JETON_EN_CLAIR, puis distinguer le SHA-256 du fichier manifeste de l'empreinte_liste et relancer skill-file-qa. Ne pas utiliser pour un dossier de publication complet. 中文触发：Skill 包脱敏、删除出生日期与住址、掩码扫描、标记回填、哈希来源纠正、负向夹具。English: sanitize skill package, redact personal tokens, masked scanner, proof of absence, hash provenance."
---

# Assainir un paquet Skill qui recopie des jetons personnels

## Quand utiliser

- Un paquet Skill existe déjà et ses exemples reprennent des valeurs réelles : date de naissance (ISO ou française), commune, département, code postal, GPS, adresse.
- Un audit externe, une relecture ou un scan interne signale une valeur en clair dans `SKILL.md`, une référence ou une docstring de script.
- Il faut non seulement réécrire, mais **prouver** qu'il ne reste aucun jeton en clair, sans jamais réafficher les valeurs.

## Ne pas utiliser

- Pour caviarder un dossier public de preuves, sceller son manifeste, gérer des exemptions ou qualifier des DOIs : `publier-preuves-anteriorite-caviardees`.
- Pour créer un Skill ou arbitrer son contenu : skill-creator.
- Pour réécrire l'historique Git, supprimer un dépôt ou modifier des permissions : hors périmètre.

## Délégation

| Besoin | Propriétaire | Ce qui reste ici |
|---|---|---|
| Caviardage d'un dossier publié, exemptions, manifeste, clone anonyme | `publier-preuves-anteriorite-caviardees` | Seulement le paquet Skill |
| Validation statique après écriture | `skill-file-qa` | Fournir le paquet et exiger `RESULT PASS` |
| Fichiers modifiés pendant l'écriture | `skill-update-concurrency-safe` | Geler puis comparer les empreintes |
| Empreinte avant modification | `verifier-fraicheur-preuves-skill` | Recalculer size/mtime/SHA-256 |
| Rédaction du cas et des limites | `write-skill-evidence-case-study` | Cas sans valeurs, avec compteurs et empreintes |
| Recommandation automatique à vérifier | `verify-skill-recommendation-claims` | Confronter chaque affirmation aux fichiers |

## Entrées et invariants

- **Paquet** : répertoire contenant SKILL.md, references/ et scripts/.
- **Jetons** : un par ligne, fichier **hors** du paquet ou stdin. Jamais dans le Skill, jamais dans un argument de commande, jamais dans un rapport.
- **Marqueurs** : `JJ/MM/AAAA`, `<commune>`, `<département>`, `<code>`. Les GPS et adresses se suppriment, ils ne se remplacent pas par un marqueur qui garderait la structure du domicile.
- **Ancres conservées** : hash, transaction, ABI, signature, DOI. Un jeton qui n'apparaît que dans une suite hexadécimale n'est pas une donnée personnelle : c'est une coïncidence de chiffres, à garder intacte.
- **Aucune exemption** : le scanneur ne connaît pas de liste d'exceptions. Seule classe tolérée : `HEX_ONLY`.
- **Lecture seule** : le scanneur ne modifie aucun fichier et n'écrit aucun cache.

## Étape 0 — Geler avant d'écrire

Relever size, mtime et SHA-256 de chaque fichier, dans un répertoire temporaire hors du paquet :

```bash
(cd "<paquet>" && find . -type f -not -path './.git/*' | sort | xargs sha256sum) > <tmp>/avant.sha256
(cd "<paquet>" && find . -type f -not -path './.git/*' -printf '%s|%T@|%p\n' | sort) > <tmp>/avant.stat
```

- Relever aussi le nombre de fichiers et le répertoire cible : un paquet absent ne se confond pas avec un paquet vide.
- Si un fichier change entre l'instantané et la fin, arrêter : c'est une écriture concurrente, pas un résidu. Déléguer à `skill-update-concurrency-safe`.
- Ne pas créer de sauvegarde contenant les valeurs réelles dans le paquet ou dans un dossier publié.

## Étape 1 — Auditer sans afficher

```bash
py -3 -B scripts/auditer_jetons.py --dossier "<paquet>" --tokens-file - < <tokens.txt>
```

Contrat de sortie :

| Sortie | Sens | Code |
|---|---|---|
| `SCANNED n` / `TOKENS n` | fichiers texte lus / jetons dédupliqués | — |
| `CLEAR rel token#k lines=… first=…` | jeton en clair, chemin masqué | 1 |
| `ENCODED rel token#k lines=… first=…` | jeton encodé en hexadécimal (jetons ≥ 4 caractères) | 1 |
| `PATH_JETON rel token#k` | jeton dans un nom de fichier ou de répertoire | 1 |
| `HEX_ONLY rel token#k lines=… first=…` | occurrence uniquement dans une suite de 16 hexadécimaux ou plus | 0 |
| `SUMMARY token#k clear=… encoded=… hex_only=… path=…` | nombre de fichiers par classe, pas d'occurrences | — |
| `AUCUN_JETON_EN_CLAIR` + `RESULT OK` | aucun jeton hors hexadécimal | 0 |
| `JETONS_EN_CLAIR n` + `RESULT FAIL` | n fichiers avec au moins un jeton en clair, encodé ou dans un chemin | 1 |
| `DOSSIER_ABSENT`, `TOKENS_FILE_ABSENT`, `TOKENS_VIDES` | entrée invalide | 2 |

- Le chemin affiché est masqué par `<token#k>` ; `<token#k>` renvoie à la ligne k du fichier de jetons, que l'utilisateur seul peut ouvrir.
- Un même couple fichier-jeton est classé une seule fois, par priorité `CLEAR` > `ENCODED` > `HEX_ONLY` ; `PATH_JETON` s'ajoute.
- Les caractères non ASCII des chemins sont échappés en `\xNN` : la sortie reste ASCII.
- `HEX_ONLY` n'est pas une exemption déclarée : c'est un fait recalculé à chaque exécution. Ne jamais élargir à un fichier entier.
- Si `TOKENS n` ne correspond pas au fichier attendu, vérifier les lignes vides, les commentaires `#` et les doublons avant de conclure.

## Étape 2 — Remplacer à la main

- Traiter un jeton à la fois, relire la ligne avec cinq lignes de contexte, pas seulement le diff.
- Ordre spécifique → générique : la date complète avant l'année, `<commune> (<département>, <code>, France)` avant `<département>`, sinon il reste `France ()`.
- Préserver les `|` des tableaux, l'indentation des listes et les clôtures de blocs de code.
- Réécrire la phrase, pas seulement la valeur : `né le [caviarde] à **France**` devient `né le [caviarde] en **France**`.
- Ne jamais tronquer, rehasher ou « corriger » une ancre cryptographique pour faire passer le scan. Si le jeton n'existe que dans l'ancre, c'est `HEX_ONLY` : garder l'ancre et documenter le faux positif.
- Ne pas écrire de commentaire du type « valeur retirée le … » : il recrée un indice.
- Relancer l'étape 1 après chaque passe. Quatre passes ont été nécessaires dans le cas de référence.

Résidus observés et corrigés dans le cas 2026-10-27 :

| Résidu | Origine | Correction |
|---|---|---|
| `[caviarde] ([caviarde])` | date ISO et date française remplacées séparément | une seule règle de fusion |
| `né le [caviarde] à **France**` | préposition « à » devant un pays | réécrire en « en **France** » |
| `France, <département>, France` | commune puis département remplacés séparément | règle dédiée avant la générique |
| `France ()` | parenthèse orpheline après suppression d'une ville | supprimer la parenthèse |
| `city: "France"` | clé de lieu résiduelle en YAML/CFF | supprimer la ligne, pas la valeur seule |
| doubles espaces | valeur retirée au milieu d'une phrase | normaliser `[ ]{2,}` hors blocs de code |
| cellule de tableau vide | valeur supprimée sans réécriture | réécrire la cellule ou la ligne |

- En JSON, supprimer la **clé** et resérialiser ; un `re.sub` sur du JSON casse les virgules et l'ordre des champs.
- Ne pas recopier les valeurs réelles dans le cas de référence : le cas ne contient que des marqueurs, des compteurs et des empreintes.

## Étape 3 — Prouver l'absence

1. Rejouer l'étape 1 sur le paquet : attendre `AUCUN_JETON_EN_CLAIR`, `RESULT OK`, code 0.
2. **Test négatif** : copier le paquet dans un répertoire temporaire, planter un jeton synthétique qui n'appartient à personne, et exiger un échec.

```bash
cp -a "<paquet>" <tmp>/fixture
printf 'JETON_TEST_9f3c\n' > <tmp>/tokens-test.txt
printf 'JETON_TEST_9f3c\n' >> <tmp>/fixture/references/<fichier>.md
py -3 -B scripts/auditer_jetons.py --dossier <tmp>/fixture --tokens-file <tmp>/tokens-test.txt
# attendu : CLEAR ... JETONS_EN_CLAIR 1 RESULT FAIL, code 1
rm -rf <tmp>/fixture <tmp>/tokens-test.txt
```

- Si la fixture passe `AUCUN_JETON_EN_CLAIR`, le test est vacant : le scanneur ou le montage est faux, pas le paquet.
- Vérifier qu'aucune valeur de jeton n'apparaît dans la sortie, y compris dans un tuyau, un log ou une capture d'écran.
- Vérifier qu'aucun fichier de jetons n'a été copié dans le paquet : s'il y était, le supprimer et rescanner, car il a peut-être été publié.
- Un code 0 sans test négatif ne prouve pas l'absence ; il prouve seulement que le scanneur n'a rien trouvé dans ce qu'il a lu.

## Étape 4 — Hachages et validation statique

Deux valeurs différentes se confondent facilement :

| Valeur | Ce qu'elle couvre | Où la lire |
|---|---|---|
| SHA-256 du fichier manifeste | les octets de `MANIFESTE_SHA256.json` | `sha256sum`, `stat` |
| `empreinte_liste` | la concaténation `sha256  chemin` des entrées, pas le fichier | champ JSON du manifeste |

```bash
sha256sum "<paquet>/05_EMPREINTES/MANIFESTE_SHA256.json"
stat -c '%s' "<paquet>/05_EMPREINTES/MANIFESTE_SHA256.json"
py -3 -c "import json;d=json.load(open('<paquet>/05_EMPREINTES/MANIFESTE_SHA256.json',encoding='utf-8'));print(d['nb_fichiers'], d['empreinte_liste'])"
```

- Dans le cas de référence, `ab6d393c…` était `empreinte_liste` ; le fichier de 7 345 octets valait `ed0287e1…`. `.gitattributes` faisait 8 octets, pas 10.
- Après la dernière écriture, calculer le SHA-256 complet **et** la taille de chaque fichier ; consigner ces valeurs dans le rapport ou le cas, jamais en auto-référence dans le fichier qu'elles couvrent.
- Si le paquet est publié, ne plus modifier un octet après le scellement : le manifeste ne se régénère pas sans changer `captured_at_utc` et son propre hash.

Validation statique :

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<paquet>" \
  --workspace "<racine-workspace>" --stable-seconds 2 --stability-timeout 30
```

- Exiger `RESULT PASS`, code 0, `Files (N)` égal au nombre réel, les références locales et inter-Skills résolues, et une empreinte stable pendant la validation.
- Si `skill-file-qa` a changé depuis la dernière utilisation, relire son contrat avant de citer ses compteurs.

## Rapport final

| Section | Contenu exigé |
|---|---|
| Paquet | chemin, nombre de fichiers, empreintes finales (SHA-256 + octets) |
| Audit | `SCANNED`, `TOKENS`, lignes `CLEAR`/`ENCODED`/`PATH_JETON`/`HEX_ONLY` masquées, verdict |
| Test négatif | jeton synthétique planté, sortie attendue, code obtenu |
| Résidus | tableau avant/après par catégorie, sans valeurs |
| Hachages | hash du fichier manifeste et `empreinte_liste` distingués |
| QA | `RESULT PASS`, `Files (N)`, références vérifiées, empreinte stable |
| Non vérifié | ce qui n'a pas été relu, notamment les valeurs d'origine (jamais réaffichées) |

## Pièges

| Piège | Conséquence | Parade |
|---|---|---|
| Scan qui affiche la valeur | la fuite se déplace dans le terminal ou le log | sortie masquée, jeton par index |
| Fichier de jetons dans le paquet | il est scanné puis publié | fichier dehors ou stdin, supprimer après usage |
| Jeton passé en argument | historique du shell | `--tokens-file -` et stdin |
| `re.sub` global sur du Markdown | tableaux et listes cassés | remplacement manuel, relecture contextuelle |
| Hash tronqué pour faire passer le scan | preuve détruite | garder l'ancre, accepter `HEX_ONLY` |
| Exempter un fichier entier | données personnelles publiées | aucune exemption dans ce scanneur |
| Confondre hash du manifeste et `empreinte_liste` | affirmation fausse dans la documentation | calculer les deux séparément |
| Code 0 sans test négatif | gate vacant | planter un jeton synthétique |
| Recopier les valeurs dans le cas | réintroduction | marqueurs, compteurs, empreintes |
| Régénérer après publication | `MISMATCH` chez les tiers | geler après la dernière génération |
| Ignorer une écriture concurrente | empreintes instables | geler, comparer, déléguer |

## Ressources

- `scripts/auditer_jetons.py` — scanneur masqué, lecture seule, codes 0/1/2.
- `references/cas-2026-10-27-paquet-skill.md` — cas réel : compteurs, empreintes, correction de provenance, limites.
- Après écriture, valider avec `skill-file-qa` ; en cas de fichier modifié pendant la passe, `skill-update-concurrency-safe` ; pour l'empreinte initiale, `verifier-fraicheur-preuves-skill` ; pour rédiger le cas, `write-skill-evidence-case-study` ; pour vérifier une recommandation automatique, `verify-skill-recommendation-claims` ; pour un dossier publié, `publier-preuves-anteriorite-caviardees`.
