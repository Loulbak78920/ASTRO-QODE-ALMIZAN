---
name: attester-validation-officielle-skill
description: "Attester la validation officielle d'un Skill lorsqu'aucune base de validation n'existe : inventorier en lecture seule les registres candidats (projet, ~/.qoder, instantanés qoder-skill-inventory, dépôt d'archive), classer chaque piste (compteurs d'usage, inventaire en lecture seule, registres métier sans Skills), faire trancher par l'utilisateur l'emplacement et le format avant écriture, puis ajouter une section datée « Validation officielle » dans references/ (commande, RESULT, comptes, description, lignes, SHA-256, mtime), rejouer skill-file-qa sans modifier SKILL.md, republier l'archive et vérifier les blobs distants. Utiliser pour « marquer le Skill comme validé », « enregistrer la validation dans la base de données », « attester qu'un Skill est validé » sans base de Skills ; ne jamais inventer un registre, écrire dans skill-usage.json ou créer une base sans accord. 中文触发：标记 Skill 已验证、验证状态入库、无验证数据库、官方验证记录。English: mark skill validated, validation registry."
---

# Attester la validation officielle d'un Skill

## Objectif

Inscrire la validation officielle d'un Skill dans une preuve durable quand aucune base de Skills n'existe, sans inventer de registre ni surpromettre. La validation est un fait mesuré — validateur officiel exécuté dans la session courante, empreinte stable — pas une déclaration.

## Règles non négociables

1. La validation se prouve par une exécution réelle de `skill-file-qa` dans cette session. Un PASS antérieur, rapporté par une autre session ou déduit d'une archive, est une piste, pas une preuve.
2. Inventaire négatif d'abord, en lecture seule. Aucune écriture avant la décision de l'utilisateur.
3. Ne jamais créer de registre par défaut, ne pas écrire dans `skill-usage.json`, ne pas présenter une fiche de preuve comme une base de données.
4. `references/` est en ajout seul : ne pas réécrire l'historique, ne pas corriger une ancienne section de validation — en ajouter une nouvelle.
5. Quand aucun registre n'existe, l'emplacement et le format sont tranchés par l'utilisateur (`AskUserQuestion`), pas par l'agent.
6. Re-valider après écriture ; `SKILL.md` doit rester inchangé.
7. Republier seulement si demandé ; pousser uniquement sur demande explicite.
8. Le rapport dit « aucune base de Skills ; statut inscrit dans la fiche de preuve », jamais « marqué dans la base ».

## Préconditions

- Le paquet cible est stable : deux échantillons `size`/`mtime`/`SHA-256` identiques avant d'écrire.
- Le paquet ne contient ni `__pycache__` ni `*.pyc`.
- L'état d'archive est connu : commit publié de référence, ou « non publié ».

## Étape 1 — Figer la validation officielle

Exécuter le validateur, sans pipe (le code de sortie doit être capturé directement) :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/skill-file-qa/scripts/validate_skill.py" \
  "<SKILL_DIR>" --workspace "<WORKSPACE>" --stable-seconds 2
```

- Exiger `RESULT PASS` et un code 0. En cas de FAIL : s'arrêter, corriger le paquet, relancer. Ne pas documenter un FAIL comme une validation.
- Consigner : N pass / N fail / N warn, version PyYAML, `Files (N)`, description (1 ligne / N caractères), corps (N lignes), références locales et références de Skills résolues, `Fingerprint (start)` et `(final)` (octets, mtime local, SHA-256), nombre de caches.
- Si une archive existe, comparer le SHA-256 validé aux blobs publiés (`git ls-tree` ou vérification dédiée). Sinon, noter « non publié ».

## Étape 2 — Inventaire négatif des registres

```bash
py -3 scripts/inventorier_registres_validation.py \
  --workspace "<WORKSPACE>" \
  --archive "<ARCHIVE_REPO>" \
  --skills-root "C:/Users/Administrateur/.qoder/skills" \
  --skills-root "<WORKSPACE>/.qoder/skills"
```

Lire la sortie :

| Sortie | Signification | Suite |
|---|---|---|
| `EXIT=0` + `VERDICT=NO_SKILL_VALIDATION_REGISTRY` | aucune base de Skills | étape 3 |
| `EXIT=1` + `ENTRY=CANDIDATE` | un fichier/table cite des Skills avec un statut | lire le candidat, le soumettre à l'utilisateur, ne rien écrire |
| `EXIT=2` | usage ou IO | corriger les chemins, relancer |

Ce que chaque emplacement prouve :

| Emplacement | Contenu typique | Ce que cela prouve |
|---|---|---|
| Projet | `REGISTRE_ETAT_CIVIL_*`, `registre_empreintes`, `registre_economie_*` | données métier, aucun statut de Skill |
| `~/.qoder/skill-usage.json` | `usageCount`, `lastUsedAt` | usage seulement, jamais une validation |
| `<WORKSPACE>/.qoder/snapshots/*.json` | `format: qoder-skill-inventory/1` | inventaire sans statut, ne pas y écrire |
| Dépôt d'archive | `.qoder/skills/…`, registres métier | archive, pas de registre de validation |
| `~/.qoder/**/*.db` | aucun fichier de Skills | pas de base locale |

Un `grep` récursif sur un gros espace de travail peut expirer (20 s observé) ; ce timeout ne prouve aucune absence. Restreindre le chemin et le motif, ou utiliser le script.

## Étape 3 — Faire trancher l'emplacement

Poser une seule question avec `AskUserQuestion`, en recommandant la fiche de preuve :

- **Fiche de preuve du Skill (recommandé)** : section datée dans `references/`, liée au paquet, republiée avec lui.
- **Nouveau registre JSON local** : hors des racines Skills (par exemple `~/.qoder/skill-validation.json`), schéma minimal `name`, `sha256`, `date`, `validateur`, `RESULT`, à maintenir ensuite.
- **Tableau maître du projet** : déléguer à `tableau-maitre-sequentiel` ou `maj-tableau-maitre-sequentiel`.
- **Une autre base existante** : demander le chemin et le type (SQLite, MySQL, QMind…). Ne pas en supposer une.

Règles : ne pas recommander un nouveau registre sans que l'utilisateur le demande ; un registre créé ne doit pas vivre dans le paquet Skill ; noter la décision et son libellé exact dans le rapport.

## Étape 4 — Écrire la section datée

Avant l'édition :

- Relire le fichier de références réel (les sessions concurrentes peuvent l'avoir modifié).
- Relever `size`, `mtime`, `SHA-256`. Si l'un diffère de la dernière valeur connue, relire avant d'éditer.

Ajouter en fin de fichier, sans toucher au contenu existant :

```text
## Validation officielle — <AAAA-MM-JJ>

Exécutée après la publication <commit> (ou "paquet non publié"), sans modification du paquet. Commande :

py -3 "<VALIDATEUR>" "<SKILL_DIR>" --workspace "<WORKSPACE>" --stable-seconds 2

- RESULT PASS, code 0 : <N> pass, <N> fail, <N> warn ; PyYAML <version>.
- Files (<N>) ; description 1 ligne / <N> caractères ; corps <N> lignes ; <N> références locales et <N> références de Skills résolues.
- Frappe stable : <octets> o, mtime <ISO local avec fuseau>, SHA-256 <complet>, identique avant et après contrôle.
- Aucun __pycache__ ni *.pyc créé ; le validateur n'écrit pas dans le Skill.
- Correspondance archive : <commit, blobs vérifiés N/N, ou non publié>.
```

Règles : une section par exécution ; date locale avec fuseau ; ne pas recopier la section d'une autre session sans rejouer le validateur.

## Étape 5 — Re-valider et mesurer

- Rejouer exactement la commande de l'étape 1.
- Attendre `RESULT PASS`, code 0, `Files (N)` inchangé, et un `Fingerprint` de `SKILL.md` identique à la valeur d'avant écriture.
- Relever le nouveau SHA-256 du fichier de références séparément : l'empreinte du validateur ne couvre que `SKILL.md`.
- Vérifier 0 cache après l'opération.

## Étape 6 — Republier l'archive

Déléguer à `publier-skill-qoder-vers-depot-git` :

- Créer la branche temporaire depuis `origin/main` (nom horodaté si `merge/skill-<nom>` existe).
- Copier seulement `SKILL.md`, `references/`, `scripts/`, sans cache ; comparer les SHA-256 (N/N).
- Committer, avancer `main` en `--ff-only`, pousser **uniquement si demandé**.
- Vérifier les blobs sur `origin/main`, supprimer la branche temporaire avec `-d`, ne pas toucher aux branches d'autres sessions.
- Sans demande de push : conserver la branche et le dire.

## Étape 7 — Rapport

| Étape | Résultat attendu |
|---|---|
| Validation | `RESULT PASS`, code 0, N pass / 0 fail / 0 warn, empreinte stable |
| Inventaire | `VERDICT=NO_SKILL_VALIDATION_REGISTRY` et nombre de candidats |
| Décision | libellé exact choisi par l'utilisateur |
| Section | fichier, lignes ajoutées, SHA-256 avant/après |
| Re-QA | PASS, `SKILL.md` inchangé, nouveau hash references |
| Archive | commit, fast-forward, push oui/non, blobs N/N |
| Nettoyage | branche temporaire supprimée, worktree propre |

Ligne d'honnêteté obligatoire : « aucune base de Skills n'existe ; le statut est inscrit dans la fiche de preuve ». Si un registre a été créé sur décision explicite, le nommer et donner son chemin.

## Pièges

| Symptôme | Cause | Réaction |
|---|---|---|
| « base de données » dans la demande, aucune base trouvée | registre supposé, inexistant | inventaire puis décision ; ne pas en créer un par défaut |
| `grep -r registre` renvoie beaucoup de fichiers | registres métier (`REGISTRE_ETAT_CIVIL…`) | classer `BUSINESS_REGISTRY`, ne pas les prendre pour des Skills |
| Le `grep` expire au bout de 20 s | espace de travail volumineux | pas une preuve d'absence ; restreindre ou utiliser le script |
| `skill-usage.json` pris pour un registre | il ne contient que `usageCount`/`lastUsedAt` | classer `USAGE_COUNTERS_ONLY` |
| Écrire dans un instantané `qoder-skill-inventory/1` | fichier généré, sans statut | ne pas y écrire ; c'est un inventaire |
| PASS d'une session antérieure réutilisé | preuve périmée | rejouer le validateur dans la session courante |
| Section ajoutée sur un fichier non relu | écriture concurrente écrasée | relire et comparer `size`/`mtime`/SHA-256 avant l'édition |
| `SKILL.md` modifié pendant la re-validation | empreinte différente | s'arrêter, expliquer, rejouer la validation |
| `Files (N)` augmenté après écriture | cache ou fichier parasite | retirer le cache, relancer le validateur |
| Fast-forward refusé | `origin/main` a avancé | relire branche/HEAD/`origin/main`, attribuer la dérive, ne pas forcer |
| Annonce « validé dans la base » | fiche de preuve confondue avec une base | reformuler : aucune base, fiche de preuve |

## Checklist

- [ ] Validateur exécuté dans cette session : `RESULT PASS`, code 0
- [ ] `Fingerprint` start = final, SHA-256 de `SKILL.md` noté
- [ ] Inventaire exécuté, `VERDICT` et candidats notés
- [ ] Décision utilisateur enregistrée mot pour mot
- [ ] Section datée ajoutée en fin de fichier, hash avant/après
- [ ] Re-QA PASS, `SKILL.md` inchangé, hash references séparé
- [ ] Archive en fast-forward et blobs N/N (si publication demandée)
- [ ] Rapport sans « base de données » abusif, 0 cache

## Ne pas utiliser pour

- Exécuter la validation seule : `skill-file-qa`.
- Publier ou archiver sans validation : `publier-skill-qoder-vers-depot-git`.
- Vérifier la fraîcheur de preuves déjà écrites : `verifier-fraicheur-preuves-skill`.
- Constituer un dossier public de preuves d'antériorité : `publier-preuves-anteriorite-caviardees`.

## Ressources

- `references/cas-2026-10-27.md` — cas source, inventaire négatif mesuré, décision, empreintes, limites.
- `scripts/inventorier_registres_validation.py` — inventaire lecture seule, sortie ASCII, codes 0/1/2.
