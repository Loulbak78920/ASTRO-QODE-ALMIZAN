---
name: ancrer-anteriorite-depot-github-public
description: "Prouver qu'un fichier était publié dans un dépôt GitHub public et retrouver son premier commit : paginer tout l'historique, interroger commits?path= pour le commit qui introduit le chemin, télécharger le brut à ce SHA, comparer octets et fins de ligne, puis distinguer dates serveur et dates de commit déclarées par le client. Utiliser pour dater la première publication d'un fichier, reproduire une divergence entre copie locale et copie publiée, corriger un faux négatif dû à un premier commit incomplet, ou contrer une affirmation d'antériorité. 中文触发：证明文件首次公开发布、首个 commit、GitHub 提交分页、raw 字节比对、CRLF 差异、服务器时间与客户端时间。English: prove a file's first public commit in a GitHub repo, paginate history, per-path commit lookup, raw byte and CRLF comparison, server vs client timestamps."
---

# Ancrer l'antériorité d'un fichier dans un dépôt GitHub public

## Quand utiliser

- Établir à quel commit un fichier a été **publié pour la première fois** dans un dépôt GitHub public.
- Vérifier qu'une copie locale est identique, octet pour octet, à la version servie par GitHub.
- Reproduire ou corriger un faux négatif du type « aucun fichier publié » alors que les fichiers existent.
- Répondre à une affirmation d'antériorité en produisant une chronologie datée et des empreintes.

## Quand ne pas utiliser

- Constituer ou publier un dossier d'antériorité caviardé : utiliser `publier-preuves-anteriorite-caviardees`.
- Créer ou fusionner une pull request : utiliser `github-pr-create-merge-sans-gh`.
- Réconcilier une preuve d'API déjà consignée avec son état actuel : utiliser `verifier-preuves-api-temporelles`.
- Prouver la date de création d'une œuvre indépendamment de sa publication : ce Skill ne le fait pas.

## Ce que l'ancrage établit — et ce qu'il n'établit pas

| Élément | Établi par | Limite à écrire dans la restitution |
|---|---|---|
| `created_at`, `pushed_at` | serveur GitHub | `pushed_at` date le dernier push, pas chaque commit |
| Présence du blob à un SHA | serveur GitHub (`raw`) | l'historique peut être réécrit, le dépôt supprimé ou rendu privé |
| Date de commit | client Git | déclarative : peut précéder la création du dépôt ou être antidatée |
| Égalité SHA-256 local/publié | calcul local | prouve l'identité du contenu, jamais la date |
| Premier commit touchant un chemin | API GitHub | peut suivre un renommage ou un déplacement |

Ne jamais écrire « opposable », « certifié » ou « horodatage indépendant » à propos d'une date de commit. Le cas de référence montre un commit daté `2026-10-22T06:48:48Z` dans un dépôt créé par GitHub à `2026-10-22T07:04:32Z` : la date du commit précède la création du dépôt, ce qui prouve qu'elle est déclarative.

## Procédure

### 1. Qualifier le dépôt

```text
GET https://api.github.com/repos/owner/repo
```

Lire `visibility`, `private`, `created_at`, `pushed_at`, `default_branch`. Un `404` signifie « absent ou non visible » : sans jeton, les deux cas sont indistinguables. Classer `NON_ETABLI`, ne pas conclure à une suppression.

### 2. Paginer tout l'historique

```text
GET https://api.github.com/repos/owner/repo/commits?per_page=100&page=N
```

Incrémenter `N` jusqu'à recevoir un lot de moins de 100 éléments. Ne jamais s'arrêter au premier lot : dans le cas de référence, le premier appel a renvoyé exactement 100 commits sur 213. Conserver chaque réponse brute.

### 3. Trouver le premier commit d'un chemin

```text
GET https://api.github.com/repos/owner/repo/commits?path=chemin/du/fichier.ext&per_page=100&page=N
```

- La liste est triée du plus récent au plus ancien : le premier commit touchant le chemin est le **dernier élément du dernier lot**.
- Si un lot contient exactement 100 éléments, poursuivre la pagination avant de conclure.
- Encoder le chemin (`urllib.parse.quote`) : accents, espaces, caractères comme `°`.
- Ne jamais déduire la présence d'un fichier de l'arbre du premier commit : cet arbre ne contient que les fichiers de ce commit. Le cas de référence y a perdu 5 fichiers sur 5.

### 4. Télécharger le brut au SHA trouvé

```text
https://raw.githubusercontent.com/owner/repo/SHA40/chemin/du/fichier.ext
```

- Toujours le SHA complet (40 hexadécimaux), jamais `/blob/` (HTML) ni l'URL de branche (contenu mobile).
- Vérifier que le SHA appartient bien à un commit renvoyé par l'API, pas à un objet arbitraire.
- Conserver les octets téléchargés et leur SHA-256 dans le dossier de sortie.

### 5. Comparer les octets, puis les fins de ligne

- Égalité stricte : `sha256(copie_locale) == sha256(octets_publies)`.
- Égalité hors CRLF : comparer après remplacement de `\r\n` par `\n`. Git stocke LF ; un clone Windows avec `core.autocrlf=true` produit CRLF.
- Rapporter les deux verdicts séparément. Ne jamais conclure « identique » sur une comparaison de texte décodé : BOM, encodage et fins de ligne faussent le résultat.
- Un contenu non identique reste une **preuve de publication** : archiver les octets publiés et leur hash, puis qualifier la divergence (version antérieure ou ultérieure). Ne pas la traiter comme une absence.

### 6. Écrire le verdict

| Verdict | Conditions |
|---|---|
| `ANCRAGE_PUBLIE_ETABLI` | dépôt public, chaque fichier demandé publié, chaque copie locale identique octet pour octet |
| `ANCRAGE_PUBLIE_PARTIEL` | au moins un fichier publié, mais divergence ou fichier absent |
| `NON_ETABLI` | dépôt non public, aucun fichier publié, ou erreur d'accès |

Joindre systématiquement la note : les dates de commit sont déclaratives, seuls `created_at`, `pushed_at` et la disponibilité du brut au SHA sont établis par GitHub, et aucun horodatage indépendant n'est produit.

## Pièges vérifiés

| Piège | Symptôme observé | Correction |
|---|---|---|
| Arbre du premier commit supposé complet | `0/5 fichiers suivis publies` | interroger `commits?path=` pour chaque fichier |
| Premier lot pris pour l'historique | 100 commits au lieu de 213 | paginer jusqu'à un lot inférieur à 100 |
| Mauvaise extrémité de la liste | commit le plus récent pris pour le premier | prendre le dernier élément du dernier lot |
| Nom de copie locale approximatif | copie locale signalée absente | lister le dossier et recopier le nom exact (`05_CODE_SOURCE_`, pas `05_CONTRAT_`) |
| CRLF entre dépôt et Windows | hash différent, texte identique | second verdict après normalisation LF |
| URL `/blob/` ou de branche | HTML ou contenu du jour | `raw.githubusercontent.com` au SHA |
| Message de commit cité comme preuve | DOI ou URL pouvant être morts | ne rien conclure du message de commit |

## Script

```bash
py -3 scripts/verifier_anteriorite_depot.py \
  --depot owner/repo \
  --fichier "chemin/publie.ext=/chemin/copie/locale.ext" \
  --fichier "autre/chemin.ext" \
  --sortie /chemin/de/sortie
```

- `GITHUB_TOKEN` est lu dans l'environnement s'il existe et n'est jamais affiché. Sans jeton, la limite est de 60 requêtes par heure.
- Produit `anteriorite.json`, `snapshots/` (réponses brutes) et `publications/` (octets servis par GitHub).
- Affiche des lignes `CLE=VALEUR` : `DEPOT`, `VISIBILITE`, `CREE_LE_SERVEUR`, `COMMITS_TOTAL`, `FICHIER`, `PUBLIE`, `COMMIT`, `DATE_CLIENT`, `IDENTIQUE_OCTETS`, `IDENTIQUE_HORS_CRLF`, `VERDICT`, `RAISON`.
- Un fichier non publié affiche `PUBLIE=False` et `IDENTIQUE_OCTETS=NA` : aucune comparaison n'est effectuée, une absence n'est pas une divergence.
- Codes de retour : `0` ancrage établi, `1` partiel ou non établi, `2` accès impossible (HTTP, réseau, limite d'API).

Contrôle d'acceptation minimal :

```bash
py -3 scripts/verifier_anteriorite_depot.py --help
py -3 scripts/verifier_anteriorite_depot.py --depot owner/repo \
  --fichier "CITATION.cff=/chemin/CITATION.cff" --sortie ./sortie
```

Attendu sur un fichier publié identique : `PUBLIE=True`, `IDENTIQUE_OCTETS=True`, `VERDICT=ANCRAGE_PUBLIE_ETABLI`, code de retour `0`. Sur une copie volontairement convertie en CRLF : `IDENTIQUE_OCTETS=False`, `IDENTIQUE_HORS_CRLF=True`.

## Limites

- GitHub peut réécrire l'historique, supprimer le dépôt ou changer sa visibilité : réexécuter et dater chaque relevé.
- Un commit publié ne date pas la création de l'œuvre, seulement sa présence publique à un instant que le client déclare.
- Un renommage ou un déplacement fait apparaître un premier commit plus tardif que la création réelle du contenu.
- Le message de commit n'est pas une preuve : le cas de référence cite un DOI qui ne résout pas.
- Aucun horodatage qualifié (eIDAS, Software Heritage) n'est produit ici ; ne pas l'affirmer sans l'avoir exécuté.

## Ressources

- `scripts/verifier_anteriorite_depot.py` — pagination, recherche du premier commit par chemin, téléchargement brut, comparaison octets/CRLF, verdict.
- `references/cas-2026-10-28-astro-qode-alimzan.md` — faux négatif 0/5, correction, résultats mesurés et limites de l'interprétation.
