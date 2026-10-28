---
name: publier-preuves-anteriorite-caviardees
description: "Construire et publier un dossier public de preuves d'antériorité : inventorier les preuves datées (Git, déploiement on-chain, DOIs), caviarder identité et domicile sans casser le Markdown ni les JSON, scanner les résidus avec exemptions prouvées, sceller un manifeste SHA-256 vérifiable après clone (`.gitattributes * -text`, manifeste auto-exclu), créer le dépôt public via l'API GitHub avec le jeton GCM sans jamais l'afficher, puis valider par clone anonyme et qualifier chaque preuve sans surpromesse (NON_EXISTANT_404, ENREGISTREMENT_SUPPRIME_410, INDETERMINE_AU_RELEVE). Utiliser quand il faut rendre vérifiables la paternité et la date d'une œuvre sans publier les originaux ni les données personnelles. 中文触发：公开前序/在先性证据、脱敏发布、SHA-256 清单克隆校验、链上时间戳、DOI 核实、GCM 建公开仓库、匿名克隆验收。English: public prior-art proof dossier, redacted publication, reproducible SHA-256 manifest, on-chain timestamp, DOI qualification, anonymous clone validation."
---

# Publier un dossier public de preuves d'antériorité

## Quand utiliser

- L'utilisateur veut rendre publiquement vérifiables **qui** a écrit une œuvre et **quand** elle existait, sans publier le code source ni ses données personnelles.
- Des preuves datées existent déjà ailleurs : commits sur un dépôt public, déploiement de contrat on-chain, dépôt privé, DOIs déclarés.
- Il faut un manifeste SHA-256 reproductible par un tiers après clone, et une publication vérifiée hors de la session authentifiée.

## Ce que le dossier prouve — et ce qu'il ne prouve pas

| Élément | Ce qu'il établit | Limite à écrire dans le dossier |
|---|---|---|
| Historique Git public | Publication par ce compte, à ces dates, tel que l'hébergeur l'affiche | Le propriétaire peut réécrire l'historique : preuve de publication, pas horodatage indépendant |
| Déploiement on-chain | Date et contenu horodatés par le réseau | Indépendant seulement si le tiers refait les appels RPC lui-même |
| Manifeste SHA-256 | Intégrité des fichiers publiés à la date de scellement | N'établit pas l'antériorité de l'œuvre |
| DOI déclaré | Rien tant que l'enregistrement ne résout pas au relevé | Qualifier 404 / 410 / indéterminé, jamais « vérifié » |
| Dépôt privé | Existence pour le propriétaire | Non vérifiable par un tiers : le dire |

Ne jamais écrire « preuve légale », « certifié » ou « opposable » : le dossier documente des faits datés, il ne produit pas de qualification juridique.

## Étape 0 — Cadrer avec l'utilisateur, une seule fois

Poser les trois choix en une fois, avec une recommandation, puis les inscrire dans le `README.md` du dossier :

1. **Périmètre du caviardage** — recommandé : retirer date et lieu de naissance, GPS, communes de résidence ; conserver nom, e-mail, nationalité, organisation et ancres cryptographiques, qui portent l'attribution et la licence.
2. **Cible** — un nouveau dépôt dédié, jamais le dépôt source ni un dépôt existant.
3. **Horodatage tiers** (Software Heritage) — demander explicitement ; s'il n'est pas exécuté, écrire « non effectué » et laisser la commande.

Ne pas créer le dépôt ni publier avant confirmation explicite de la cible.

## Étape 1 — Inventorier les preuves

Relever chaque preuve avec **l'horodatage UTC du relevé** ; les compteurs bougent tant que les dépôts vivent.

```bash
cd "<depot-public>"
git rev-list --count HEAD
git log --format='%ae' | sort | uniq -c | sort -rn
git log --reverse --format='%H|%aI|%ae|%s' | head -1
git log -1 --format='%H|%aI|%ae|%s'
git ls-files | wc -l
```

Vérifier qu'aucun secret n'est suivi **avant** de publier quoi que ce soit :

```bash
git ls-files | grep -iE '(^|/)(\.env|secrets?/|.*\.key$|client_secret.*\.json$)' || echo AUCUN_SECRET_SUIVI
```

Preuves on-chain : appeler le RPC public et conserver les réponses brutes.

```bash
curl -s https://mainnet.base.org -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getTransactionReceipt","params":["0x<txhash>"]}'
```

Contrôler `status = 0x1`, `contractAddress`, `blockNumber` ; puis `eth_getBlockByNumber` pour l'horodatage et `eth_getCode` pour la taille (`(len(hex)-2)/2`). Un `403` isolé du RPC est transitoire : réessayer, ne pas le consigner comme résultat.

DOIs : les qualifier avec le script, pas à la main (étape 8).

Dépôt privé : `git ls-remote --heads <url>` ; consigner le code de retour et la note « non vérifiable publiquement ».

## Étape 2 — Construire hors du workspace

Créer le dossier sous `.qoder/tmp/<nom-du-dossier>`. Le construire dans l'arbre source pollue les scans du projet et expose les copies caviardées aux mécanismes d'auto-copie.

```
README.md  VERIFIER.md  STATUT_VERIFICATION.md  LICENCE_ET_DROITS.md  .gitattributes
01_IDENTITE_ET_ATTRIBUTION/   identité + acte d'antériorité, caviardés
02_LICENCES/                  licence publique et contrat d'exploitation
03_OEUVRE/                    synthèse, métadonnées de citation, artefact du contrat
04_PREUVES_EXTERNES/          relevés Base / Git / DOIs + README, horodatés UTC
05_EMPREINTES/                MANIFESTE_SHA256.json + verifier_empreintes.py
06_CORRESPONDANCE_ORIGINAUX/  table source locale ↔ copie publiée
```

`EMPREINTES_ARTEFACTS_NON_PUBLIES.json` liste les originaux non publiés avec `bytes`, `sha256` et `raison_non_publie` (archive ZIP contenant les originaux, source dont un commentaire porte la date de naissance, PDF). Le manifeste de ces empreintes ne se vérifie pas par un tiers : il sert à l'auteur à rapprocher les copies de ses originaux, et le fichier doit le dire.

## Étape 3 — Caviarder en deux passes

**Passe structurelle** pour les JSON : supprimer les clés, pas les motifs. Un `re.sub` sur du JSON casse la structure ou laisse des virgules orphelines.

```python
import json, re

DROP = {"date_naissance_iso", "coordonnees_gps_<commune>", "city", "birthPlace"}
REPL = [(r"\bJJ/MM/AAAA\b", "[caviarde]"), (r"\b<commune>\b", "France")]

def scrub(value):
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if k not in DROP}
    if isinstance(value, list):
        return [scrub(item) for item in value]
    if isinstance(value, str):
        for pattern, replacement in REPL:
            value = re.sub(pattern, replacement, value)
        return value
    return value

with open("IDENTITE.json", encoding="utf-8") as handle:
    data = json.load(handle)
print(json.dumps(scrub(data), ensure_ascii=False, indent=2))
```

**Passe textuelle** pour le Markdown : règles ordonnées du plus spécifique au plus générique, puis normalisation des résidus. L'ordre compte : `<commune> (<département>, <code>, France)` doit être traité avant `<département>`, sinon il reste `France ()`.

Règles de sûreté :

- Chaque remplacement doit préserver les `|` des tableaux et l'indentation des listes : après écriture, relire les lignes touchées avec leur contexte, pas seulement le diff.
- Garder `[caviarde]` comme marqueur unique et stable : il rend la table de correspondance lisible.
- Après chaque itération, rescaner (étape 4) et traiter les résidus un par un ; quatre passes ont été nécessaires dans le cas de référence.

Résidus observés et corrigés dans le cas 2026-10-27 :

| Résidu | Origine | Correction |
|---|---|---|
| `(Coordonnées: )` | suppression des valeurs GPS, parenthèse conservée | retirer la parenthèse vide |
| `France, <département>, France` | remplacements successifs de la ville puis du département | règle dédiée avant la règle générique |
| `né le [caviarde] à **France**` | préposition « à » devant un pays | réécrire en « en **France** » |
| `[caviarde] ([caviarde])` | date ISO et date française remplacées séparément | règle de fusion |
| `city: "France"` | clé de lieu résiduelle en YAML/CFF | supprimer la ligne `city:` |
| doubles espaces | valeurs retirées au milieu d'une phrase | normaliser `[ ]{2,}` |

## Étape 4 — Scanner jusqu'à `REDACTION_OK`

Écrire les jetons interdits (date, ville, département, GPS, codes postaux) dans un fichier, un par ligne. Ce fichier reste hors du dossier publié et hors du Skill : les valeurs réelles ne se recopient pas dans la documentation.

```bash
py -3 scripts/preparer_publication.py scan --dossier "<dossier>" \
  --tokens-file "<tokens.txt>" --skip "05_EMPREINTES/MANIFESTE_SHA256.json" \
  --exempt "04_PREUVES_EXTERNES/BASE_MAINNET_TRANSACTION.json:<jeton-court>" \
  --exempt "03_OEUVRE/SMART_CONTRACT/ARTEFACT_BYTECODE_ET_ABI.json:<jeton-court>"
```

Sortie attendue : une ligne `EXEMPT ... hex_only=yes` par exemption, `SCANNED n`, `REDACTION_OK`, code 0.

Une exemption n'est acceptée que si **toutes** les occurrences du jeton sont dans des chaînes hexadécimales (`hex_only=yes`). Toute occurrence en clair donne `hex_only=no` et `REDACTION_PROBLEMS`, code 1 : l'exemption est refusée. Une exemption déclarée mais inutilisée est signalée `EXEMPT_UNUSED`, pour qu'aucune ne dorme dans la documentation.

Prouver en plus que le texte sensible n'existe ni en clair ni encodé en hexadécimal :

```bash
py -3 scripts/preparer_publication.py absence --dossier "<dossier>" \
  --needle "JJ/MM/AAAA" --needle "AAAA-MM-JJ" --needle "<commune>"
```

Attendu : `ABSENCE_OK`, code 0. Les exemptions ne couvrent que des artefacts **publics** (transaction et bytecode lisibles on-chain) ; jamais un document d'identité, une licence ou un historique Git.

## Étape 5 — Sceller les empreintes

Copier d'abord le vérificateur dans le dossier, puis générer le manifeste : le vérificateur fait partie des fichiers empreintés.

```bash
mkdir -p "<dossier>/05_EMPREINTES"
cp scripts/verifier_empreintes.py "<dossier>/05_EMPREINTES/"
py -3 scripts/preparer_publication.py manifeste --dossier "<dossier>"
py -3 scripts/verifier_empreintes.py --dossier "<dossier>"
```

Attendu : `GITATTRIBUTES_WRITTEN * -text` (ou `PRESENT`), `FILES n`, `MANIFEST_SHA256 <hex>`, puis `RESULT OK`, code 0.

Trois invariants :

1. **`.gitattributes` = `* -text`** avant le premier commit. Sans lui, un clone Windows convertit LF en CRLF et le vérificateur renvoie `MISMATCH` sur des fichiers intacts.
2. **Le manifeste s'exclut lui-même** ; le vérificateur exclut le manifeste et `.git`, sinon il se signale en `EXTRA`.
3. **Le manifeste n'est plus régénéré après publication** : `captured_at_utc` change à chaque exécution, donc son SHA-256 aussi. Générer une dernière fois, puis geler.

Le contrat de sortie du vérificateur est stable : `OK=`, `MISMATCH`, `MISSING`, `EXTRA`, `RESULT OK|FAIL`, codes 0/1 (2 si le manifeste manque). Le fichier copié fonctionne sans argument depuis `05_EMPREINTES/`.

## Étape 6 — Créer le dépôt public avec le jeton GCM

Le jeton est lu depuis Git Credential Manager et ne doit jamais apparaître : ni `echo`, ni URL, ni argument persisté, ni fichier.

```bash
TOKEN=$(printf "protocol=https\nhost=github.com\n\n" | git credential fill 2>/dev/null | sed -n 's/^password=//p')
if [ -z "$TOKEN" ]; then echo NO_CREDENTIALS; exit 1; fi
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/user | py -3 -c "import sys,json;d=json.load(sys.stdin);print('LOGIN',d.get('login'))"
```

Vérifier le compte, puis créer le dépôt (nom libre, visibilité explicite, pas d'initialisation distante) :

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d '{"name":"<NOM>","description":"<description ASCII>","private":false,"has_issues":true,"has_wiki":false,"has_projects":false,"auto_init":false}' \
  | py -3 -c "import sys,json;d=json.load(sys.stdin);print('FULL_NAME',d.get('full_name'));print('PRIVATE',d.get('private'));print('HTML_URL',d.get('html_url'));print('MSG',d.get('message'))"
unset TOKEN
```

`PRIVATE False` et `MSG None` sont requis. Si `MSG` est non nul (nom déjà pris, droits insuffisants), s'arrêter : ne pas deviner un autre nom.

Puis pousser sans jamais mettre le jeton dans l'URL distante ; GCM répond au helper d'identification :

```bash
cd "<dossier>"
git init -b main
git add -A
git -c user.name="<nom>" -c user.email="<email>" commit -m "Preuves d'anteriorite - <oeuvre>"
git remote add origin "https://github.com/<owner>/<NOM>.git"
git push -u origin main
```

Si `git push` échoue en `Repository not found`, appliquer `diagnostiquer-push-github-depot-absent` plutôt que recréer un dépôt.

## Étape 7 — Vérifier depuis l'extérieur

Une poussée réussie ne prouve pas que le dépôt est public et intègre. Refaire les contrôles en anonyme, dans un dossier neuf :

```bash
curl -s https://api.github.com/repos/<owner>/<NOM> \
  | py -3 -c "import sys,json;d=json.load(sys.stdin);print('PRIVATE',d.get('private'));print('VISIBILITY',d.get('visibility'));print('DEFAULT_BRANCH',d.get('default_branch'));print('SIZE_KB',d.get('size'));print('PUSHED_AT',d.get('pushed_at'))"
curl -s -A "Mozilla/5.0" -o /dev/null -w "README_HTTP %{http_code}\n" \
  https://raw.githubusercontent.com/<owner>/<NOM>/main/README.md
rm -rf "<clone-temporaire>"
git clone -q "https://github.com/<owner>/<NOM>.git" "<clone-temporaire>"
(cd "<clone-temporaire>" && py -3 05_EMPREINTES/verifier_empreintes.py)
```

Attendu : `PRIVATE False`, `VISIBILITY public`, `README_HTTP 200`, `RESULT OK`. `SIZE_KB 0` juste après la poussée est un retard de l'API, pas un échec.

Sur le clone, refaire le scan des jetons et la recherche de secrets :

```bash
grep -rniF -f "<tokens.txt>" . --exclude-dir=.git \
  | grep -v "SMART_CONTRACT/ARTEFACT" | grep -v "BASE_MAINNET_TRANSACTION" || echo AUCUN_JETON
grep -rniE "BEGIN [A-Z ]*PRIVATE KEY|ssh-rsa|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20}" . \
  --exclude-dir=.git || echo AUCUN_SECRET
```

Compter aussi les fichiers suivis (`git ls-files | wc -l`) et vérifier qu'il vaut N + 1 (les N fichiers empreintés plus le manifeste). Ce contrôle croisé attrape un fichier oublié avant le manifeste.

## Étape 8 — Qualifier les preuves sans dol

```bash
py -3 scripts/preparer_publication.py dois \
  --out "<dossier>/04_PREUVES_EXTERNES/RAPPORT_VERIFICATION_DOIS.json" \
  10.5281/zenodo.<id> [autres...]
```

| Verdict | Signification | Formulation publiée |
|---|---|---|
| `RESOLU` | handle `doi.org` valide et enregistrement 200 au relevé | « résout au relevé du <UTC> » |
| `NON_EXISTANT_404` | aucun handle | « n'existe pas au relevé » |
| `ENREGISTREMENT_SUPPRIME_410` | handle présent, enregistrement supprimé | « enregistrement supprimé au relevé » |
| `INDETERMINE_AU_RELEVE` | refus HTTP, réseau, état inattendu | « non confirmé au relevé » |

Écrire dans `STATUT_VERIFICATION.md`, section « Ce qui n'a pas été vérifié » : les DOIs non résolus, le dépôt privé, l'absence d'archivage tiers, et le fait que les compteurs Git sont un instantané. Le script réessaie trois fois et accepte 200/404/410 ; un `403` ou une coupure donne `INDETERMINE`, jamais un verdict inventé.

## Modèle de rapport final

| Section | Contenu exigé |
|---|---|
| Dépôt | URL, commit publié, nombre de fichiers suivis, `RESULT OK` du clone anonyme |
| Preuves | tableau preuve / nature / vérifiable par un tiers (Oui/Non) |
| DOIs | tableau DOI / HTTP / verdict, sans reformulation optimiste |
| Contrôles | visibilité API, HTTP anonyme, scan jetons, scan secrets, comptage croisé |
| Non publiés | artefacts et raison, avec empreintes |
| Copie de travail | chemin, pour que l'auteur puisse la déplacer |

## Pièges

| Piège | Conséquence | Parade |
|---|---|---|
| Scanner des jetons courts (une année, par exemple) | faux positifs bloquants | exemption `REL:TOKEN`, acceptée seulement si `hex_only=yes` |
| Exempter un document entier pour faire passer le scan | données personnelles publiées | exemption par fichier **et** jeton, avec preuve hexadécimale |
| `re.sub` sur du JSON | structure cassée, clés perdues | passe structurelle par clés puis sérialisation |
| Remplacement générique avant le spécifique | `France ()`, `France, <département>, France` | ordre spécifique → générique, puis relecture contextuelle |
| `[caviarde]` seul dans une phrase | phrase dénaturée | réécrire la préposition, pas seulement la valeur |
| Manifeste qui s'inclut | hash impossible à stabiliser | auto-exclusion, vérificateur qui exclut le manifeste |
| Absence de `* -text` | `MISMATCH` au clone Windows | `.gitattributes` avant le premier commit |
| Régénérer le manifeste après publication | `MISMATCH` chez tous les tiers | geler après la dernière génération |
| Jeton GCM affiché ou mis dans l'URL | fuite de credential | `sed` sur la sortie, `unset`, remote sans jeton |
| `git push` réussi pris pour une preuve | dépôt privé ou incomplet | API `private=false` + clone anonyme + vérificateur |
| En-tête `Authorization: Bearer ` vide après `unset TOKEN` | 401 au lieu des champs attendus | appeler sans en-tête : c'est l'appel anonyme qui prouve la visibilité |
| DOI déclaré présenté comme vérifié | surpromesse | verdicts 404/410/indéterminé, section « non vérifié » |
| Compteur Git figé dans le dossier | chiffre périmé dès le lendemain | horodater le relevé en UTC et le dire instantané |

## Ressources

- `scripts/preparer_publication.py` — `manifeste`, `scan`, `absence`, `dois` ; sortie ASCII, codes 0/1/2.
- `scripts/verifier_empreintes.py` — recalcul du manifeste, à copier dans `05_EMPREINTES/`.
- `references/caviardage-et-empreintes.md` — règles de caviardage, catalogue de résidus, contrat du manifeste et du vérificateur, protocole d'exemption.
- `references/cas-preuves-2026-10-27.md` — cas réel vérifié : chiffres, commit, verdicts DOI, limites.
- Après écriture du paquet, valider avec `skill-file-qa`. Pour les opérations GitHub authentifiées, voir `github-pr-create-merge-sans-gh` ; en cas de dépôt introuvable, `diagnostiquer-push-github-depot-absent`.
