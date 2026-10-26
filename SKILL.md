---
name: github-pr-create-merge-sans-gh
description: "Créer et fusionner une pull request GitHub sans gh CLI, quand le navigateur n'est pas connecté, en réutilisant les identifiants de Git Credential Manager via git credential fill et l'API REST : sondage en lecture seule des permissions et des méthodes de fusion, recalcul après fetch de origin/main, du merge-base et du diff à trois points, création idempotente de la PR, attente de mergeable, fusion rebase prioritaire, puis contrôle du SHA de fusion, de main distant, du fast-forward local et des blobs. Après la fusion, si les fichiers source divergent, échantillonner SHA-256 et mtime avant de conclure, sans rollback ni republication non demandée. Utiliser pour « gh absent », « créer une pull request », « merge PR to main », « rebase merge », « mergeable », « base a avancé », « MISMATCH après fusion », « écriture concurrente », ou une page de connexion GitHub. 中文触发：无 gh、创建 PR、合并 PR 到 main、rebase 合并、mergeable 轮询、base 前进、合并后 MISMATCH、并发写入。"
---

# Créer et fusionner une pull request GitHub sans gh

## Portée

Ce Skill couvre github.com, avec un jeton déjà stocké par un credential helper Git. Il ne couvre pas GitHub Enterprise, la création de jetons, la connexion au navigateur, le contournement des protections de branche, le force push, ni la republication automatique après divergence des sources.

## Autorisations et actions irréversibles

- Sonde et lecture : libres.
- Création de PR : uniquement sur demande explicite.
- Fusion : uniquement sur demande explicite, avec la branche cible confirmée. Si l'utilisateur demande seulement de créer la PR, s'arrêter après l'étape 3 et donner l'URL.
- Ne jamais pousser directement sur `main` pour contourner la PR ; ne jamais faire de force push ; ne pas supprimer la branche de travail sans instruction.
- Une fusion modifie un état partagé. En cas d'ambiguïté sur la cible, demander avant d'agir.

## Sécurité des identifiants

- Lire le jeton avec `git credential fill` (lecture seule). Ne pas utiliser `git credential approve` ni `reject`, et ne pas modifier la configuration Git.
- Le jeton reste en mémoire : jamais affiché, jamais écrit sur disque, jamais passé en argument de commande.
- Ne pas saisir d'identifiants dans le navigateur. Une page de connexion GitHub prouve seulement que la session navigateur n'est pas authentifiée ; elle ne bloque pas l'API.
- Si le credential helper échoue, s'arrêter. Ne pas demander à l'utilisateur de coller un jeton dans la conversation.
- Le script n'imprime que le nom d'utilisateur et des statuts non secrets.

## Étape 0 — Constater l'environnement

Définir une fois les variables des étapes suivantes ; remplacer chaque valeur entre `<...>`. `SKILL` pointe vers le dossier local du Skill et doit être adapté après un déplacement. Les étapes 2, 5 et 6 restent centrées sur `main`.

```bash
SKILL="C:/Users/Administrateur/.qoder/skills/github-pr-create-merge-sans-gh"
DEPOT="<chemin-absolu-du-depot>"
REPO="<owner/repo>"
BASE="main"
BRANCH="<branche-head>"
PREFIXE="<chemin-relatif-du-perimetre>"
BASE_AVANT="<sha-origin/main-avant-la-pr>"
HEAD_PR="<sha-du-head-de-pr>"
BODY="<fichier-utf8-du-corps-de-pr>"
N="<numero-de-pr>"
CHEMIN="<chemin-relatif-dans-le-depot>"
SOURCE="<dossier-source-du-skill>"
```

Ne pas laisser ces variables vides : `py -3 "$SKILL/..."` ou `git -C "$DEPOT"` s'exécuterait sur un chemin vide.

```bash
command -v gh || true
git config --get credential.helper || true
git -C "$DEPOT" remote get-url origin
git -C "$DEPOT" status -sb
git -C "$DEPOT" branch --show-current
```

- Si `gh` est absent, utiliser `scripts/github_pr_api.py` ; ne pas installer `gh` sans demande.
- Extraire `owner/repo` de l'URL `origin` (HTTPS ou SSH) dans `REPO` et vérifier que le dépôt local est bien celui de la PR.
- Relever le head : branche locale et SHA. Si le worktree est sale, ne pas committer ni pousser implicitement ; la PR ne doit contenir que les commits déjà poussés.

## Étape 1 — Sonder l'API en lecture seule

```bash
py -3 "$SKILL/scripts/github_pr_api.py" probe --repo "$REPO" --head "$BRANCH"
```

Sortie attendue : `CREDENTIAL_USER`, `REPO`, `PERMISSIONS`, `MERGE_METHODS`, `OPEN_PRS`.

- Arrêter si `push=false`, ou si l'API renvoie 401/403.
- Noter si `rebase=true`. Si `rebase=false`, ne pas supposer qu'une fusion rebase est possible : demander la méthode.
- Si une PR ouverte existe déjà pour ce head, la réutiliser ; ne pas créer de doublon.

## Étape 2 — Recalculer la portée après fetch

```bash
git -C "$DEPOT" fetch origin
git -C "$DEPOT" rev-parse origin/main "$BRANCH"
git -C "$DEPOT" ls-remote origin refs/heads/main "refs/heads/$BRANCH"
git -C "$DEPOT" merge-base origin/main "$BRANCH"
git -C "$DEPOT" diff --stat origin/main..."$BRANCH"
git -C "$DEPOT" diff --name-status origin/main..."$BRANCH"
git -C "$DEPOT" log --oneline origin/main.."$BRANCH"
```

- La base peut avoir avancé depuis la préparation : ne jamais réutiliser un SHA de base mémorisé. Cas vérifié : `origin/main` avait avancé de `3a4732a` à `ddfd179`, tandis que le merge-base restait `3a4732a`.
- Le diff à trois points compare le merge-base à la tête de branche ; c'est lui qui délimite la portée réelle de la PR.
- Vérifier que seuls les fichiers attendus apparaissent. Toute surprise (fichier supplémentaire, suppression, binaire) impose un arrêt et une explication.
- Consigner base distante, merge-base, head SHA et liste des fichiers.

## Étape 3 — Créer la PR

Préparer un corps UTF-8 dans un fichier temporaire : résumé, portée exacte, validations exécutées, mention explicite de ce qui n'a pas été testé.

```bash
py -3 "$SKILL/scripts/github_pr_api.py" create \
  --repo "$REPO" --head "$BRANCH" --base "$BASE" \
  --title "Titre de la PR" --body-file "$BODY" --yes
```

- `create` exige `--yes` et refuse avant tout appel réseau sans ce drapeau.
- La commande est idempotente : une PR ouverte pour le même head est réutilisée (`PR_EXISTING`).
- Consigner numéro, URL, head SHA, base et état `open`.
- Si l'utilisateur n'a demandé que la création, s'arrêter ici.

## Étape 4 — Fusionner

Uniquement après instruction explicite de fusion et confirmation de la branche cible.

```bash
py -3 "$SKILL/scripts/github_pr_api.py" merge \
  --repo "$REPO" --pr "$N" --method rebase --yes
```

- `merge` exige `--yes` et refuse avant tout appel réseau sans ce drapeau.
- Le script interroge `mergeable` jusqu'à 15 fois à 2 secondes d'intervalle. `null` persistant ou `false` : abandon, sans contournement.
- La méthode par défaut est `rebase` ; elle produit un historique linéaire. Le script ne bascule pas silencieusement vers `merge`. Pour utiliser `merge` ou `squash`, le décider explicitement et le déclarer dans le rapport.
- Sortie attendue : `MERGE_REBASE status=200 merged=True`, puis `PR_FINAL`, `REMOTE_MAIN` et `VERIFY_MATCH true`.
- En cas de 405/409 (protection de branche, conflit, checks requis) : rapporter le message et s'arrêter. Ne pas désactiver une protection ni forcer.

## Étape 5 — Vérifier après fusion

```bash
git -C "$DEPOT" fetch origin
git -C "$DEPOT" rev-parse origin/main
git -C "$DEPOT" ls-remote origin refs/heads/main
git -C "$DEPOT" log --oneline -3 origin/main
git -C "$DEPOT" diff --name-status "$BASE_AVANT"..origin/main
git -C "$DEPOT" ls-tree -r origin/main -- "$PREFIXE"
for oid in $(git -C "$DEPOT" ls-tree -r origin/main -- "$PREFIXE" | awk '{print $3}'); do
  git -C "$DEPOT" cat-file blob "$oid" | sha256sum
done
git -C "$DEPOT" merge --ff-only origin/main
git -C "$DEPOT" diff --name-status "$HEAD_PR" origin/main -- "$PREFIXE"
```

- Immédiatement après la fusion, comparer le SHA de fusion de l'API, `origin/main`, `ls-remote` et le fast-forward local : ils doivent désigner le même commit. Si `main` a avancé depuis, le SHA de fusion doit être un ancêtre de `origin/main`, pas nécessairement la tête.
- Recalculer les SHA-256 des blobs distants et les comparer aux empreintes validées avant la PR.
- Le diff limité au préfixe entre le head de PR et `origin/main` doit être vide après une fusion rebase.
- Vérifier que le worktree est propre et que la branche locale est à jour avec `git status -sb`.
- Si le dépôt contient un vérificateur d'archive, utiliser `publier-skill-qoder-vers-depot-git` et son script `verifier_archive_skill.py` en mode `--from remote`.

## Étape 6 — Traiter une divergence des sources après fusion

Un `MISMATCH` du vérificateur ne prouve pas une corruption de l'archive. Il peut signaler une écriture concurrente dans les fichiers source.

```bash
oid=$(git -C "$DEPOT" ls-tree -r origin/main -- "$CHEMIN" | awk '{print $3}')
git -C "$DEPOT" cat-file blob "$oid" > /tmp/publie
sha256sum /tmp/publie "$SOURCE/$CHEMIN"
stat -c '%y %s %n' "$SOURCE/$CHEMIN"
for i in 1 2 3; do sha256sum "$SOURCE/$CHEMIN"; stat -c '%y %s' "$SOURCE/$CHEMIN"; sleep 2; done
```

- Vérifier que `oid` est non vide et désigne un seul fichier ; sinon le chemin est absent ou ambigu. Ne pas utiliser `git show "origin/main:$CHEMIN"` sous Git Bash : MSYS réécrit l'argument en `origin\main;...` et Git répond `ambiguous argument`. Extraire l'OID puis lire le blob évite cette conversion.
- Comparer le blob publié au fichier source, puis les mtime. Trois échantillons identiques à 2 secondes d'intervalle établissent la stabilité.
- Si les blobs publiés correspondent à la version validée et que les sources ont changé après la copie : conclure à une dérive des sources, pas à un échec de fusion.
- Ne pas restaurer, écraser ou republier les sources sans instruction explicite. Ne pas pousser ces changements dans le cadre de la PR déjà fusionnée.
- Si les sources changent encore pendant l'échantillonnage, s'arrêter et rapporter ; ne pas figer un état instable.
- La republication après dérive est un flux distinct (branche temporaire, validation, nouvelle PR) ; elle n'est pas couverte par ce Skill et n'a pas été validée dans la session source.

## Échecs fréquents

| Symptôme | Cause probable | Action |
|---|---|---|
| `command -v gh` vide | CLI absent | Utiliser l'API et le credential helper |
| Page GitHub de connexion | Session navigateur non authentifiée | Ne pas saisir d'identifiants ; passer par l'API |
| 401 / 403 | Jeton absent, expiré ou permissions insuffisantes | Arrêter ; ne pas deviner un autre jeton |
| `PR_CREATE_FAIL 422` | Aucun commit entre base et head, ou head inconnu | Vérifier la branche poussée et la base |
| `mergeable` reste `null` | Calcul GitHub en cours | Réessayer plus tard ; ne pas forcer |
| `mergeable=false` | Conflit ou base incompatible | Arrêter ; résoudre explicitement |
| `rebase` refusé | Méthode désactivée ou conflit | Demander ; ne pas basculer silencieusement |
| 405 / 409 à la fusion | Protection de branche, checks requis, conflit | Rapporter ; ne pas contourner |
| `VERIFY_MATCH false` après une fusion réussie | `main` a avancé après la fusion | Vérifier que le SHA de fusion est un ancêtre de `origin/main` |
| `MISMATCH` après fusion | Source modifiée après la copie | Échantillonner hash et mtime ; distinguer dérive et corruption |
| `git show "origin/main:chemin"` renvoie `ambiguous argument 'origin\main;...'` | MSYS réécrit `ref:chemin` sous Git Bash | Extraire l'OID avec `ls-tree -r`, puis `cat-file blob "$oid"` |
| Tour interrompu | Session ou outil interrompu | Relire l'état réel ; ne pas déclarer la fusion ou la republication réussie |

## Ressources

- `scripts/github_pr_api.py` : sonde, création idempotente, fusion avec attente de `mergeable`, statut. Lecture seule pour `probe` et `status` ; `create` et `merge` exigent `--yes`.
- `references/evidence-2026-10-26.md` : preuves datées de la session source, vérifications locales des branches du script et des étapes 2/5/6, conversion MSYS de `ref:chemin`, et limite de la republication non exécutée.
- Skills liés : `publier-skill-qoder-vers-depot-git` pour l'archivage et le vérificateur ; `skill-file-qa` pour la validation d'un Skill ; `commit-skill-work` pour le commit local et la séparation des changements.

## Limites

- github.com uniquement ; l'API GitHub Enterprise n'est pas gérée.
- Aucune création de jeton, aucun flux OAuth, aucune automatisation de connexion navigateur.
- Aucun contournement de protection de branche, de checks requis ou de politique de fusion.
- Aucune fusion automatique : `--yes` est une confirmation technique, pas une autorisation à la place de l'utilisateur.
