---
name: verifier-script-reseau-sous-quota-api
description: "Vérifier le contrat d'un script de Skill qui appelle une API en ligne quand le quota est presque épuisé : lire le quota sans le consommer, chiffrer le coût en appels de chaque scénario depuis les points d'appel du script, exécuter le seul parcours CLI à plus forte valeur qui tient dans le budget en réservant un appel au test négatif 404, couvrir les branches restantes hors quota (téléchargement brut raw.githubusercontent.com à un SHA épinglé, import du module par chemin puis appel des fonctions pures, compile() pour la syntaxe), retirer le __pycache__ créé par l'import, puis déclarer chaque parcours prouvé par exécution, prouvé par fonction ou non exécuté. 中文触发：API 配额只剩几次、GitHub rate limit、脚本每次运行消耗 5-6 个请求、只跑最高价值 CLI 路径、离线覆盖分支、import 生成 __pycache__。English: verify a network Skill script's contract under a nearly exhausted API quota, budget requests per scenario, reserve a request for a 404 negative test, cover branches offline via raw download and direct function import."
---

# Vérifier un script réseau sous quota API presque épuisé

## Quand utiliser

- Le quota restant est à un chiffre (`X-RateLimit-Remaining: 9`) et un run du script coûte 5 à 6 requêtes.
- Le reset tombe dans quelques dizaines de minutes : l'acceptation complète est impossible maintenant.
- Un rapport ou un autre agent affirme « acceptation complète » alors que seul un parcours a pu être exécuté.
- Il faut prouver un contrat (rc, clés de sortie, branches CRLF/divergence) sans dépenser le quota d'un tiers.

## Principe

Un contrat se prouve par trois voies de coût décroissant. Le budget décide de la répartition, pas l'envie de tout exécuter.

| Voie | Coût | Prouve |
|---|---|---|
| Exécution CLI de bout en bout | 1 métadonnées + pages + 1 par chemin | rc, stdout réel, enchaînement |
| Import du module + fonctions pures | 0 | logique de comparaison et de verdict |
| Inspection (`compile()`, `--help`) | 0 | syntaxe, contrat d'arguments |

## Étape 1 — Lire le quota sans le consommer

```bash
curl -s -o /dev/null -D - https://api.github.com/rate_limit -H "User-Agent: quota-audit" \
  | grep -iE '^(HTTP/|x-ratelimit-(remaining|reset))'
date -u '+%Y-%m-%dT%H:%M:%SZ'
```

- Convertir `X-RateLimit-Reset` (epoch) en UTC et calculer le délai restant : c'est lui qui départage « fractionner » et « attendre ».
- Sonder `/repos/<owner>/<repo>` renvoie les mêmes en-têtes mais consomme une requête : réserver cette sonde au cas où l'on veut aussi la visibilité.
- Sans `GITHUB_TOKEN`, la limite est de 60 req/h. Ne jamais extraire un jeton de Git Credential Manager pour relever la limite sans accord explicite de l'utilisateur.

## Étape 2 — Chiffrer le coût avant d'exécuter

Lire les points d'appel du script (`urlopen`, `requete`, `API`) et compter par run : 1 métadonnées de dépôt + `ceil(commits / per_page)` pages de commits + 1 par chemin (`commits?path=`), plus une page par tranche de 100 commits sur ce chemin.

```bash
py -3 scripts/estimer_cout_quota.py --commits 213 --fichiers 1 --budget 9 --reserve 1
```

rc 0 et `TIENT=OUI` si le run tient ; rc 3 et `TIENT=NON` sinon ; rc 2 sur argument invalide. Exemple mesuré : 213 commits, 1 fichier → `COUT_REQUETES=5` ; 2 fichiers → `6`.

Écrire ensuite le plan chiffré avant de lancer quoi que ce soit : `restant − réserve − coût = reliquat`, et la liste des parcours qui ne seront pas exécutés.

## Étape 3 — Un seul run CLI, le plus informatif

- Choisir le scénario dont le rc=0 établit l'affirmation principale, avec une copie locale réelle en entrée.
- Fixture et dossier de sortie hors du dossier du Skill (sous `~/.qoder/tmp/<sujet>`).
- Capturer `RC=$?` sur la commande elle-même, avant tout pipe : `cmd; echo "RC=$?"`, jamais `cmd | tail` puis rc.
- Recopier la sortie telle quelle (clés `KEY=VALUE`, pas de reformulation) dans le dossier de cas.

## Étape 4 — Réserver un appel au test négatif

Un dépôt inexistant échoue dès le premier appel : c'est le test négatif le moins cher (1 requête, rc attendu 2, `ERREUR=HTTP_404_SUR_...`). Le planifier **avant** le run principal, dans la réserve, pour qu'il ne soit pas sacrifié en fin de quota.

## Étape 5 — Couvrir les branches restantes à coût nul

1. **Contenu brut** : télécharger le fichier à un SHA épinglé via `raw.githubusercontent.com` — hors quota de l'API REST — puis comparer `sha256sum` aux valeurs du dossier de cas.
2. **Import par chemin** : `importlib.util.spec_from_file_location` puis appel direct des fonctions pures (comparaison, verdict). Construire les fixtures locales dans le dossier temporaire : copie convertie en CRLF (doit donner `IDENTIQUE_OCTETS=False`, `IDENTIQUE_HORS_CRLF=True`) et copie divergente (doit donner le verdict partiel ou non établi).
3. **Syntaxe et arguments** : `compile(source, nom, "exec")` sur le texte du script et `--help`, sans exécution réseau.

**Piège vérifié : l'import crée un dossier de bytecode `__pycache__` à côté du script installé** (18 808 o mesurés). Poser `sys.dont_write_bytecode = True` avant `exec_module`, ou lancer `py -3 -B`. Après la session de vérification, exiger un `find <skill> -name __pycache__` vide et supprimer tout `.pyc`. Voir `reutiliser-script-skill-comme-oracle` pour la variante outillée.

## Étape 6 — Nettoyer et valider

```bash
find "<skill>" -name __pycache__ -o -name '*.pyc'
rm -rf "$TMPDIR/tmp/<sujet>"
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<skill>"
```

## Étape 7 — Déclarer le périmètre réellement prouvé

Produire un tableau à trois colonnes et s'y tenir : **prouvé par exécution CLI**, **prouvé par appel de fonction / inspection**, **non exécuté**. Interdits : écrire « acceptation complète », présenter une couverture par fonction comme un passage de bout en bout, ou omettre la raison (quota, reset à venir, token absent). Si le reset est proche, exposer le choix « attendre » vs « fractionner » à l'utilisateur au lieu de trancher seul.

## Erreurs fréquentes

| Symptôme | Cause | Correctif |
|---|---|---|
| `TIENT=NON`, rc 3 | run plus cher que budget − réserve | réduire le nombre de fichiers ou attendre le reset |
| `__pycache__` dans le paquet du Skill | import sans `-B` / `dont_write_bytecode` | supprimer le `.pyc`, relancer l'import protégé |
| Quota cru inchangé après une sonde | l'appel visait `/repos/...` | relever via `/rate_limit` |
| `UnicodeEncodeError` cp1252 | sortie non ASCII dans la console Windows | `PYTHONIOENCODING=utf-8`, sortie `KEY=VALUE` ASCII |
| rc faux après un pipe | `cmd \| tail` masque le code du script | lire `$?` avant tout pipe |
| Branche « fichier absent » annoncée prouvée | seul `verdict()` a été appelé | la déclarer « prouvée par fonction », pas par exécution |

## Ressources

- `scripts/estimer_cout_quota.py` — coût en requêtes d'un run, hors ligne, rc 0/3/2.
- `references/cas-2026-10-28-quota-github-9-requetes.md` — relevé mesuré : 9 requêtes, reset 12:31:05Z, run 5 appels rc=0, 404 rc=2, branches hors quota, résidu `__pycache__`.
- Skills liés, à ne pas dupliquer : `audit-skill-tool-contracts` (contrat réel du script), `verifier-jugement-cli-par-fixtures` (fixtures A/B), `reutiliser-script-skill-comme-oracle` (import sans bytecode), `verifier-parite-doc-script-skill` (parité doc/script).
