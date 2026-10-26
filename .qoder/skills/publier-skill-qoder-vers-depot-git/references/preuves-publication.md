# Preuves de publication — archiver un Skill vers `main`

Transcription des sorties d'outils observées lors de la publication du 2026-10-26, complétée par une re-vérification indépendante le même jour. Les hashes et commits ci-dessous sont des faits datés, pas des constantes à réutiliser.

## Dépôts impliqués

| Élément | Rôle observé | Remote |
|---|---|---|
| Racine `C:\Users\Administrateur\Desktop\IMAM8MAHDI` | n'est pas un dépôt (`EXIT=128`, `fatal: not a git repository`) | — |
| `ASTRO-QODE-IMAM8MAHDI` | dépôt imbriqué, intact pendant l'opération | `https://github.com/Loulbak78920/ASTRO-QODE-IMAM8MAHDI.git` |
| `GITHUB_DEPOT_PUBLIC_IMAM8MAHDI` | dépôt cible de la publication | `https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN.git` |
| `~/.qoder/skills/mesure-cesium-133-geolocalisee` | Skill source, dépôt local sans `origin` | — |

## Séquence observée

1. Commit du Skill local : `8739656` — `feat(skill): ajouter le playbook Cs-133 geolocalise`, 5 fichiers, 1 024 insertions, worktree propre.
2. Push du Skill sur le remote partagé, branche dédiée `skill/mesure-cesium-133-geolocalisee` ; HEAD distant `87396560c229b9ce656d5cef490dab9d55ac5f90`. Cette branche a une **racine indépendante** : aucun ancêtre commun avec `main` (`a1ee407` à ce moment).
3. Branche de fusion créée depuis `main` : `merge/skill-mesure-cesium-133-geolocalisee` sur `a1ee407`.
4. Copie des 5 fichiers vers `.qoder/skills/mesure-cesium-133-geolocalisee/`, puis comparaison SHA-256 source/copie :

```text
IDENTIQUE SKILL.md 69edd22d352c05870d5c7a33bfa210ec8f9bf9253fcb731e99fdd6445b5b575d
IDENTIQUE references/contrat-mesure-et-limites.md 18c969c4360728ebc41b4a3dca69b04d23d50dc325b37937c0d8bbb41bbb7197
IDENTIQUE references/contrat-mesure-et-limites-zh.md 8ceb3d152991470b096728255e8f78561bc8affb3b108a768fe9cc8aa1e54460
IDENTIQUE references/skill-zh.md 130fafbd476ce43b00f004e573500ed75f49bb602afdb560e77db7893e7122cd
IDENTIQUE scripts/verifier_mesure_cesium.py d820610b5b55508d9bf73e09726aa5e09ef6420c9af53c146e3f95572abc9c21
```

5. Commit `3a4732abfd8eee7d7c0303f399045d3ada1489a0` — `feat(skills): ajouter le Skill mesure-cesium-133-geolocalisee` ; parent `a1ee40740a58d95d378410a5d79932934caad31f` ; 5 fichiers ajoutés, 0 suppression, 1 024 insertions.
6. `main` avancé en fast-forward `a1ee407..3a4732a` (aucun merge commit), puis push :

```text
To https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN.git
   a1ee407..3a4732a  main -> main
```

7. `git ls-remote origin refs/heads/main` → `3a4732abfd8eee7d7c0303f399045d3ada1489a0`.
8. Blobs distants comparés à la source : 5/5 identiques après correction MSYS (voir ci-dessous).
9. Branche temporaire supprimée ; `main` propre et synchronisé.

## Échec MSYS reproduit

Premier contrôle des blobs `origin/main`, cinq fois de suite :

```text
fatal: ambiguous argument 'origin\main;.qoder\skills\mesure-cesium-133-geolocalisee\SKILL.md': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
MISMATCH SKILL.md
```

Cause : Git Bash convertit l'argument `origin/main:<chemin>` comme une liste de chemins Windows (`:` → `;`, `/` → `\`). Le résultat est `EXIT=128` et un `MISMATCH` sur tous les fichiers, alors que la copie est correcte.

Correctif vérifié deux fois sur le même poste :

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' git -C "<depot>" show "origin/main:<chemin>"
```

- sans les variables : `EXIT=128` ;
- avec les deux variables : `EXIT=0` et contenu du blob affiché.

Le script `scripts/verifier_archive_skill.py` contourne le problème : il appelle `git` par `subprocess` sans shell et force ces deux variables dans l'environnement enfant.

## Re-vérification indépendante (2026-10-26)

| Contrôle | Commande | Résultat |
|---|---|---|
| QA du Skill | `validate_skill.py` sur ce dossier | `RESULT PASS`, 9 pass / 0 fail / 0 warn |
| Archives distantes | `--source ~/.qoder/skills/mesure-cesium-133-geolocalisee --repo GITHUB_DEPOT_PUBLIC_IMAM8MAHDI --ref origin/main --from remote` | 5/5 `OK`, `RESULT PASS`, `EXIT=0` |
| Archives worktree | même commande `--from worktree` | 5/5 `OK`, `EXIT=0` ; `git status` vide |
| Destination erronée | `--dest .qoder/skills/inexistant --from remote` | 5 × `MISSING`, `RESULT FAIL`, `EXIT=1` |
| Arguments manquants | script sans argument | argparse, `EXIT=2` |

## Réserve

La copie publiée est une **archive** : les chemins relatifs du Skill peuvent viser l'arborescence du projet principal, absente du dépôt public. Le Skill fonctionnel reste dans le dossier utilisateur. La branche distante indépendante `skill/mesure-cesium-133-geolocalisee` n'a pas été fusionnée et reste sur `origin` ; sa suppression éventuelle exige une instruction explicite.
