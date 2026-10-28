---
name: publier-workflow-ci-github
description: "Publier un workflow GitHub Actions depuis un workspace non-git : préflight SHA-256 et git ls-remote, clone isolé sous ~/.qoder/tmp (--depth 1, GIT_TERMINAL_PROMPT=0), copie du seul fichier de workflow, contrôle du diff et du YAML (on: lu comme True), gardes hashFiles, exécution locale des étapes non gardées avant commit, sauvegarde puis restauration des artefacts suivis réécrits, push fast-forward sans force, preuve octet par octet via raw.githubusercontent + SHA-256, et interprétation d'un run queued ou échoué à 0 étape comme blocage de planification (facturation) sans annoncer une CI verte. Pour « pousser le workflow V5.1 », publier .github/workflows, run Actions queued 0 étape, billing lock, hashFiles, fichier brut, dépôt public réduit. 中文：发布 GitHub Actions 工作流、推送 workflow、run 一直 queued、0 步骤、计费锁定、原始文件哈希、非 git 工作区。English: publish GitHub Actions workflow, push workflow file, queued run zero steps, billing lock, raw SHA-256, non-git workspace."
---

# Publier un workflow GitHub Actions depuis un workspace non-git

## Portée

Le fichier de workflow vit dans un dossier de travail qui n'est pas un dépôt Git, ou dans un dépôt local qui n'est pas la cible. Cette procédure le publie dans un dépôt GitHub public sans initialiser de dépôt dans le workspace, sans toucher aux autres fichiers et sans absorber le travail d'autres sessions.

Elle ne couvre pas : l'archivage d'un paquet Skill (`publier-skill-qoder-vers-depot-git`), la création ou la fusion de PR (`github-pr-create-merge-sans-gh`), ni le diagnostic d'un push `Repository not found` (`diagnostiquer-push-github-depot-absent`).

## Règles non négociables

1. Le push est une action partagée : n'agir qu'après une demande explicite de l'utilisateur.
2. Jamais `--force`, jamais `git add -A` ni `git add .`.
3. Ne jamais écrire « CI verte » ou « CI réparée » tant qu'un run n'a pas exécuté au moins une étape.
4. Prouver les octets publiés (SHA-256 + comparaison binaire), pas seulement l'acceptation du push.
5. Si `main` a avancé entre le clone et le push, s'arrêter et relire la branche ; ne pas écraser.

## 1. Préflight lecture seule

```bash
WF="<chemin du workflow local>"
REPO="https://github.com/<owner>/<repo>.git"
BRANCH=main
sha256sum "$WF"; wc -c "$WF"
GIT_TERMINAL_PROMPT=0 git ls-remote "$REPO" 'refs/heads/*' | head -20
```

- Noter le SHA-256 et la taille de départ : c'est la référence de la preuve finale.
- `main` et `master` peuvent coexister, comme les branches `skill/*`, `merge/*` et les refs `pull/*`. Identifier la branche réellement servie, ne pas la supposer.
- Vérifier que le helper d'identification est disponible (`git config --get credential.helper` → `manager`), sans jamais afficher de secret.

## 2. Clone isolé

```bash
CLONE="$HOME/.qoder/tmp/push-workflow-$(date +%Y%m%d-%H%M%S)"
GIT_TERMINAL_PROMPT=0 git clone --depth 1 --branch "$BRANCH" "$REPO" "$CLONE"
cd "$CLONE" && git rev-parse HEAD
```

- `HEAD` doit égaler l'OID distant relevé à l'étape 1. Sinon, s'arrêter.
- Le clone vit hors du workspace : aucune création de `.git` dans le projet.

## 3. Copie minimale et contrôle du diff

```bash
cp "$WF" "$CLONE/.github/workflows/<fichier>.yml"
cd "$CLONE"
git status --short
git diff --stat
git diff -- .github/workflows/<fichier>.yml
```

- Exactement un fichier modifié. Tout autre chemin est un signal d'arrêt.
- Lire le diff complet, pas seulement le stat : il doit correspondre au workflow attendu.
- Vérifier la structure avec PyYAML. YAML 1.1 lit `on:` comme le booléen `True` ; tester `d.get("on")` **et** `d.get(True)`.

```bash
PYTHONIOENCODING=utf-8 py -3 -B -c "
import yaml
d = yaml.safe_load(open('.github/workflows/<fichier>.yml', encoding='utf-8'))
trig = d.get('on') or d.get(True)
job = d['jobs'][next(iter(d['jobs']))]
print('NAME', d.get('name'))
print('TRIGGERS', sorted(trig))
print('STEPS', len(job['steps']))
print('GUARDED', [s['name'] for s in job['steps'] if 'if' in s])
"
```

## 4. Vérifier les gardes `hashFiles`

```bash
py -3 -B scripts/verifier_publication_ci.py guards --dir "$CLONE" \
  --workflow .github/workflows/<fichier>.yml
```

- `ABSENT` : l'étape sera ignorée sur ce dépôt. C'est le cas prévu pour un dépôt public réduit au noyau.
- `PRESENT` : l'étape s'exécutera réellement et doit passer.
- Une garde ne doit pas masquer un échec présent dans l'arbre complet ; elle documente une différence de périmètre.

## 5. Préflight local des étapes non gardées

Exécuter les commandes `run:` non gardées **dans le clone**, avant le commit, pour ne pas publier un workflow rouge. Ne pas exécuter les étapes gardées si leurs fichiers sont absents.

```bash
cd "$CLONE"
run_step() {
  printf '=== %s ===\n' "$*"
  PYTHONIOENCODING=utf-8 "$@" > "$HOME/.qoder/tmp/ci-step.log" 2>&1
  rc=$?
  if [ "$rc" -eq 0 ]; then
    tail -3 "$HOME/.qoder/tmp/ci-step.log"
  else
    tail -20 "$HOME/.qoder/tmp/ci-step.log"
    exit 1
  fi
  printf 'RC=%s\n' "$rc"
}
run_step py -3 -B astro_qode_cli.py test
run_step py -3 -B astro_qode_cli.py unisson
run_step py -3 -B astro_qode_cli.py qasm BELL
run_step py -3 -B astro_qode_cli.py seal --verify
```

Ces commandes doivent être des contrôles, pas des déploiements. Si une étape échoue, corriger le workflow ou le dépôt cible ; ne pas pousser en espérant que la CI diffère.

## 6. Restaurer les effets de bord avant de committer

Une exécution locale peut réécrire des fichiers suivis (sceaux, tableaux de bord, index). Les détecter, les sauvegarder, les restaurer, puis indexer uniquement le workflow.

```bash
cd "$CLONE"
git status --short
# Remplacer memoire_aq par les chemins réellement réécrits
SIDE_EFFECTS="memoire_aq"
git diff -- $SIDE_EFFECTS > "$HOME/.qoder/tmp/push-workflow-sideeffects.diff"
git checkout -- $SIDE_EFFECTS
git add -- .github/workflows/<fichier>.yml
git status --short
git diff --cached --stat
```

- `git diff --cached --stat` doit montrer un seul fichier.
- Conserver le diff des effets de bord pour le rapport ; ne jamais le publier.

## 7. Commit et push fast-forward

```bash
git commit -m "$(cat <<'EOF'
ci: publier le workflow <version>

<raison en une ou deux lignes>
EOF
)"
GIT_TERMINAL_PROMPT=0 git push origin "$BRANCH" 2>&1 | tail -5
echo "PUSH_RC=${PIPESTATUS[0]}"
```

- Attendu : `PUSH_RC=0` et `ancien..nouveau  main -> main`.
- `PIPESTATUS[0]` capture le code de `git`, pas celui de `tail`.
- Rejet non-fast-forward : revenir au clone, relire la branche, réappliquer le commit ; ne jamais forcer.

## 8. Preuve octet par octet

```bash
git ls-remote "$REPO" "refs/heads/$BRANCH"
git -C "$CLONE" show "HEAD:.github/workflows/<fichier>.yml" \
  > "$HOME/.qoder/tmp/published-workflow.yml"
py -3 -B scripts/verifier_publication_ci.py raw --repo "$REPO" --branch "$BRANCH" \
  --path .github/workflows/<fichier>.yml \
  --local "$HOME/.qoder/tmp/published-workflow.yml"
```

- Exiger `BYTES_EQUAL yes` et `RESULT MATCH` (RC=0).
- `--local` doit pointer les octets réellement poussés (`git show HEAD:…`), pas le fichier vivant du workspace : une édition postérieure au push produit un `MISMATCH` sans que le push soit en cause.
- `raw.githubusercontent.com` peut servir l'ancien blob juste après un push (cache CDN). En cas de `MISMATCH` immédiat, relire le blob **au commit** avant de conclure : `GET /repos/<owner>/<repo>/contents/<chemin>?ref=<sha>` (header `application/vnd.github.raw`) ou `git show HEAD:<chemin>` dans le clone.
- L'OID `refs/heads/<branche>` doit être celui du commit poussé.

## 9. Interpréter le run Actions

```bash
py -3 -B scripts/verifier_publication_ci.py run --repo <owner/name> --run-id <id>
```

| Classe | Sens |
|---|---|
| `QUEUED_ZERO_STEPS` | Aucune étape dispatchée. Attendre n'est pas une preuve ; vérifier l'état du compte, ne pas conclure « CI verte ». |
| `COMPLETED_NO_STEPS` | Le run échoue sans exécuter une seule étape : blocage au niveau du planificateur, pas une preuve d'erreur YAML. |
| `STARTED` | Un runner a démarré : lire les étapes et les journaux avant de conclure. |
| `COMPLETED_SUCCESS` / `COMPLETED_FAILURE` | Verdict réel : citer les étapes, pas seulement la conclusion. |

- En anonyme : annotations `[]`, `/logs` renvoie 403, la page du run est rendue en JavaScript. Un `BlobNotFound` sur `/logs` confirme seulement qu'aucune étape n'a écrit de journal.
- Avec le jeton du gestionnaire d'identifiants — jamais affiché — `GET /repos/<owner>/<repo>/commits/<sha>/check-runs` puis `GET /repos/<owner>/<repo>/check-runs/<id>/annotations` donnent le message réel : par exemple « The job was not started because your account is locked due to a billing issue. » C'est une preuve directe.
- Sans cette lecture authentifiée, l'attribution à un verrou de facturation reste une **inférence** : l'étiqueter comme telle.
- Un `notice` qui disparaît d'un run au suivant (ex. migration `ubuntu-latest`) prouve que GitHub a évalué le nouveau YAML : utile pour distinguer un contenu non pris en compte d'un blocage de planification.

## 10. Rapport

Énoncer : dépôt et branche ; OID avant → après ; un seul fichier et son diffstat ; SHA-256 local et distant avec `MATCH` ; RC de chaque étape exécutée localement ; effets de bord restaurés ; statut et classe du run ; et, si aucune étape n'a tourné, que la CI n'est pas verte.

## Pièges Windows

- `/tmp/...` écrit par `curl` n'est pas lisible par `py -3` (il résout `\tmp` sur le lecteur courant). Écrire sous `$HOME/.qoder/tmp/` ou convertir avec `cygpath -w`.
- La console cp1252 affiche les accents en `�` : c'est un défaut d'affichage, pas une corruption. Utiliser `PYTHONIOENCODING=utf-8` pour les contrôles.
- `.gitattributes` avec `* text=auto eol=lf` produit des avertissements CRLF→LF au checkout : normal. Vérifier que le workflow publié reste UTF-8 sans BOM.
- `python` peut être l'alias Microsoft Store ; utiliser `py -3`.
- Sous MSYS, quoter les globs de refs (`'refs/heads/*'`) pour éviter la conversion de chemins.

## Ressources

- `scripts/verifier_publication_ci.py` — contrôles lecture seule : `refs`, `guards`, `raw`, `run`. Ne clone pas, ne commit pas, ne pousse pas.
- `references/cas-verifie-2026-10-27.md` — preuves de la publication V5.1, corrections de parcours et limites observées.
