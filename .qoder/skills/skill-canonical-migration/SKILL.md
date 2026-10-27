---
name: skill-canonical-migration
description: "Migrer sans destruction une capacité existante vers un Skill canonique tout en conservant l'ancien Skill comme couche de compatibilité : lire l'ancien SKILL.md, ses références et ses scripts, conserver les règles encore valides, corriger les affirmations contredites par les artefacts réels, ajouter la priorité au canonique, laisser le validateur historique octet pour octet inchangé, ne pas supprimer ni archiver l'ancien Skill, puis valider les deux Skills, exécuter les deux validateurs, comparer les empreintes des artefacts du projet et distinguer fichier écrit et Skill enregistré. Utiliser pour une normalisation de Skill, une coexistence canonical/legacy, une couche de compatibilité, un audit de migration, une double validation, ou quand l'utilisateur demande une création sans écraser un Skill homonyme. 中文触发：Skill 规范化、canonical/legacy 并存、旧 Skill 兼容层、迁移审计、create 不覆盖、旧 Skill 保留。"
---

# Migration non destructive vers un Skill canonique

## Objectif

Faire converger une capacité existante vers un Skill canonique, tout en conservant l'ancien Skill comme couche de compatibilité mince. La migration est non destructive : le répertoire historique reste en place, son validateur garde exactement les mêmes octets, et les artefacts du projet ne sont pas modifiés.

Le Skill canonique porte la procédure, les invariants et le validateur de référence. L'ancien Skill conserve son entrée, mais déclare explicitement que le canonique fait foi. En cas de divergence, le canonique et son validateur gagnent.

## Portée et limites

Appliquer cette procédure lorsque :

- une même capacité possède déjà un ancien Skill et qu'un Skill canonique doit être créé ou mis à jour ;
- l'utilisateur demande une création sans écraser un Skill homonyme ;
- deux entrées doivent coexister, l'ancienne devenant une couche de compatibilité ;
- il faut auditer une migration déjà faite, comparer deux validateurs et prouver que le projet n'a pas bougé.

Ne pas appliquer cette procédure pour :

- une simple modification d'un seul Skill : suivre directement skill-creator ;
- une suppression, un archivage ou un renommage de l'ancien Skill : ce sont des actions destructrices distinctes, à autoriser explicitement et séparément ;
- un livrable bilingue : utiliser `bilingual-skill-parity` ;
- une correction isolée d'un script ou d'une référence sans besoin de canonique.

Une réponse globale comme « TOUT » ne remplace jamais une autorisation destructive ciblée. Si l'utilisateur répond à des options mutuellement exclusives par un mot ambigu, poser une question concrète avant d'écrire.

## Règles non négociables

1. **Charger skill-creator** avant toute création, mise à jour ou renommage de Skill. Ne pas réécrire un Skill existant sans avoir lu son contenu réel.
2. **Créer sans écraser** : vérifier le répertoire cible avant d'écrire. S'il existe, passer en mode mise à jour, lire l'existant et conserver les règles encore valides.
3. **Validateur historique invariant** : enregistrer son SHA-256 avant la migration. Après la migration, le SHA-256 doit être identique. Ne pas le modifier, le reformater, le renommer ni le supprimer. Le validateur canonique peut être plus strict ; l'ancien reste intact.
4. **Ancien Skill conservé** : ne pas supprimer, archiver ou renommer son répertoire sans autorisation explicite portant sur un chemin et une action précis. Une migration non destructive ne fait aucune de ces trois choses.
5. **Priorité canonique** : en tête de l'ancien SKILL.md, indiquer le nom du Skill canonique, le chemin de son validateur, la règle « en cas de divergence, le canonique fait foi » et « ne pas supprimer sans décision explicite ».
6. **Corriger seulement les règles fausses** : conserver les invariants, procédures, sources et pièges encore valides. Corriger avec preuve les affirmations contredites par les artefacts ou les scripts réels. Ne pas réécrire une règle correcte par préférence stylistique.
7. **Artefacts du projet en lecture seule** : générateur, CSV, HTML, bibliothèques scellées, verrou et fichiers de référence ne doivent pas changer pendant la migration. Comparer les empreintes avant et après.
8. **Double validation** : exécuter la vérification structurelle sur les deux Skills, puis les deux validateurs de domaine. Un validateur historique plus faible ne remplace jamais les contrôles du canonique.
9. **Fichier écrit n'est pas Skill enregistré** : un fichier valide sur disque peut ne pas être chargé dans la session. Distinguer les deux et indiquer `/skills reload` ou un redémarrage si nécessaire.

## Procédure de migration

**0. Préflight en lecture seule.** Lire la session source et vérifier les corrections, échecs et étapes déjà validées. Ne pas inventer un contenu non lu. Vérifier le répertoire cible : absent, préparer une création ; présent, lire et préparer une mise à jour. Identifier le nom canonique, le répertoire historique, son validateur et la racine du projet. Enregistrer les empreintes de l'ancien SKILL.md, de ses références, de son validateur et des artefacts du projet dans un fichier temporaire hors du projet.

```bash
AUDIT="${TMPDIR:-/tmp}/skill-canonical-migration-audit"
mkdir -p "$AUDIT"
LEGACY="<repertoire-du-skill-historique>"
CANONICAL="<repertoire-du-skill-canonique>"
PROJECT="<racine-du-projet>"
sha256sum "$LEGACY/SKILL.md" "$LEGACY"/references/* "$LEGACY"/scripts/* > "$AUDIT/legacy-before.sha256"
sha256sum "$PROJECT/<artefact-1>" "$PROJECT/<artefact-2>" > "$AUDIT/project-before.sha256"
```

Sur Windows, Git Bash fournit `sha256sum`. En PowerShell, utiliser `Get-FileHash -Algorithm SHA256`. Ne jamais placer le fichier de baseline dans le projet.

Lancer une première fois `skill-file-qa` sur l'ancien Skill, puis le validateur historique (et le validateur canonique s'il existe déjà) pour connaître l'état de départ. Pour lire une session, le paramètre est `sessionId`, pas `session_id`.

**1. Lire l'ancien Skill et lister les conflits.** Lire intégralement l'ancien SKILL.md, ses références et ses scripts, y compris l'en-tête et les options CLI du validateur. Ne pas se contenter d'un résumé. Comparer chaque affirmation avec l'état réel : nombres d'entrées, plages, dates dynamiques ou figées, clés de couleur, existence des scripts, commandes et options. Classer chaque point en « encore valide », « faux ou obsolète » ou « dupliqué par le canonique ». Pour un point faux, noter la preuve et la correction attendue. Pour un point valide, le conserver. Pour une procédure complète dupliquée, la remplacer par un renvoi au canonique.

**2. Établir le Skill canonique.** Suivre les règles de skill-creator : frontmatter valide, description sur une ligne, corps court, ressources seulement si nécessaires. Le canonique doit être autosuffisant : procédure, validateur et références ne dépendent pas de l'ancien Skill. Il peut citer des Skills génériques comme `skill-file-qa`. Écrire explicitement qu'il est canonique, que l'ancien Skill est une couche de compatibilité et qu'en cas de divergence il fait foi. Le validateur canonique doit être en lecture seule, produire une sortie ASCII et définir des codes de retour clairs. Le tester sur des cas positifs et négatifs. Si un validateur existant est repris, conserver l'ancien intact et faire évoluer une copie séparée.

**3. Transformer l'ancien Skill en couche de compatibilité.** Ajouter la déclaration suivante après le titre, en adaptant la langue de l'ancien Skill :

```markdown
Skill de compatibilité. Le Skill canonique `<nom-canonique>` et son validateur font foi ; en cas de divergence, suivre le canonique. Ne pas supprimer ce Skill sans décision explicite.
```

Ajouter ou mettre à jour la section des ressources pour citer le SKILL.md canonique, le chemin absolu de son validateur et les différences de couverture. Conserver les règles de domaine encore valides, corriger uniquement les affirmations fausses et remplacer la procédure complète dupliquée par « suivre le canonique ». Ne pas toucher au validateur historique. Vérifier son empreinte. Ne pas supprimer, archiver ni renommer le répertoire.

Si l'ancien SKILL.md cite un script absent, le signaler. Ne pas fabriquer un script pour faire disparaître l'écart. Sous autorisation explicite, restaurer le script ou documenter qu'il s'agit d'une ressource historique.

**4. Double validation et preuve de non-régression.** Vérifier la structure des deux Skills avec `skill-file-qa` :

```bash
py -3 "<skill-file-qa>/scripts/validate_skill.py" "$CANONICAL" --workspace "$PROJECT"
py -3 "<skill-file-qa>/scripts/validate_skill.py" "$LEGACY" --workspace "$PROJECT"
```

Rapporter le nombre réel de PASS, FAIL et WARN. Ne pas recopier un nombre mémorisé : le validateur peut évoluer. Corriger tout FAIL avant de continuer. Expliquer chaque WARN.

Exécuter ensuite les deux validateurs de domaine, séparément :

```bash
py -3.12 "$LEGACY/scripts/<validateur-historique>.py" --root "$PROJECT"
py -3.12 "$CANONICAL/scripts/<validateur-canonique>.py" --root "$PROJECT"
```

Noter les codes de retour, les FAIL et les WARN. Si le validateur historique est plus faible, le dire : son succès ne prouve pas les contrôles supplémentaires du canonique. Pour les cas négatifs, travailler sur une copie temporaire hors du projet : casser un numéro de séquence, un invariant, ajouter une ressource externe, retirer un fichier ou figer une date. Vérifier que le validateur échoue avec le code attendu. Ne jamais modifier le projet pour tester un échec. Si aucun cas négatif n'est exécuté, écrire explicitement « non déclenché ».

Comparer les empreintes :

```bash
sha256sum -c "$AUDIT/legacy-before.sha256"
sha256sum -c "$AUDIT/project-before.sha256"
```

Le validateur historique et les artefacts du projet doivent être OK. L'ancien SKILL.md et ses références peuvent changer : lister leurs empreintes avant et après et qualifier la modification d'intentionnelle. Si un artefact du projet change, arrêter, enquêter et restaurer avant de conclure.

Enfin, vérifier la présence des deux répertoires et la liste des Skills chargés. Un Skill écrit sur disque mais absent de la liste n'est pas encore enregistré : indiquer `/skills reload` ou un redémarrage.

**5. Rapporter.** Comparer l'attendu et l'observé, citer les chemins absolus, et distinguer validation structurelle, validation de domaine, validation visuelle et chargement runtime. Ne jamais transformer un FAIL en succès, ni un WARN non expliqué en validation complète.

## Conflits et conditions d'arrêt

| Situation | Action |
|---|---|
| Le répertoire cible existe alors que l'utilisateur demande une création | Ne pas écraser ; lire l'existant et passer en mise à jour, ou demander la décision. |
| Le validateur historique est absent | Signaler l'écart ; ne pas le fabriquer ; demander s'il faut restaurer ou documenter la couverture manquante. |
| Le validateur historique diffère du canonique | Conserver ses octets ; documenter la différence de couverture ; le canonique fait foi. |
| Une écriture concurrente est détectée | Relire les fichiers vivants, fusionner ou préserver les changements récents ; ne pas écraser. |
| La réponse de l'utilisateur est ambiguë (« TOUT ») | Poser une question concrète ; n'exécuter que le sous-ensemble non destructif explicitement compris. |
| L'ancien SKILL.md contredit les artefacts | Corriger avec preuve ; conserver les règles valides ; ne pas aligner sur un souvenir. |
| Un artefact du projet change pendant la migration | Arrêter, enquêter et restaurer ; ne pas déclarer la migration réussie. |
| `skill-file-qa` retourne FAIL | Corriger et relancer ; aucun succès tant que le FAIL subsiste. |
| Le nouveau Skill n'apparaît pas dans la liste | Vérifier le fichier, puis `/skills reload` ou redémarrer ; ne pas confondre fichier et Skill chargé. |
| Une suppression, un archivage ou un renommage est demandé | Exiger une autorisation explicite sur le chemin et l'action ; ce n'est pas couvert par la migration standard. |

## Modèle de rapport

```text
Canonical : <chemin> — créé/mis à jour, <n> fichiers
Legacy    : <chemin> — conservé, couche de compatibilité
Validateur legacy SHA-256 : <avant> == <après> : OK/FAIL
SKILL.md/reference legacy : <avant> -> <après> (modification intentionnelle)
skill-file-qa : canonical <x> PASS / legacy <y> PASS
Validateur canonical : EXIT <0/1/2>, <n> FAIL, <n> WARN
Validateur legacy    : EXIT <0/1/2>, <n> FAIL, <n> WARN
Projet : <n> empreintes inchangées : OK/FAIL
Enregistrement : sur disque ; /skills reload requis | visible
Non fait : suppression/archivage/renommage (autorisation explicite requise)
```

## Cas vérifié

Le 2026-10-25, la migration de `tableau-maitre-sequentiel` (canonique) et `maj-tableau-maitre-sequentiel` (historique) a été exécutée et contrôlée. Le validateur historique est resté au SHA-256 `5248a2db…` avant et après. L'ancien SKILL.md et sa référence ont été corrigés intentionnellement, sans suppression ni archivage. Les deux Skills ont passé la vérification structurelle ; la session source enregistre 8 PASS par Skill, tandis que la version actuelle de `skill-file-qa` en rapporte 9 : le rapport doit utiliser la sortie réelle, pas un nombre figé. Les deux validateurs de domaine ont retourné EXIT 0 avec 0 avertissement, et les cinq artefacts clés du projet étaient inchangés à la fin de la migration.

Deux réponses « TOUT » ont été reçues pour des options mutuellement exclusives. Seul le sous-ensemble non destructif a été exécuté ; aucune suppression, archivage ou renommage n'a eu lieu. Les empreintes historiques, les cas négatifs et les écarts entre l'état de la session et l'état actuel sont détaillés dans `references/cas-tableau-maitre-sequentiel.md`.

## Ressources et définition de terminé

- `references/cas-tableau-maitre-sequentiel.md` : preuves historiques, empreintes avant/après, cas négatifs et limites de l'instantané.
- `skill-file-qa` : contrôle structurel, format et syntaxe des deux Skills.
- `tableau-maitre-sequentiel` : exemple de Skill canonique.
- `maj-tableau-maitre-sequentiel` : exemple de couche de compatibilité conservée.
- `bilingual-skill-parity` : à utiliser si un livrable bilingue est demandé à la place d'un Skill monolingue.
- `validation-navigateur-par-repli` : repli de validation visuelle lorsqu'un écran est requis ; ne jamais déclarer un visuel vérifié sans capture réussie.

Définition de terminé :

- [ ] Répertoire cible vérifié : création sans écrasement ou mise à jour après lecture.
- [ ] Validateur historique identique avant et après (SHA-256).
- [ ] Ancien Skill conservé ; aucune suppression, archivage ou renommage.
- [ ] Priorité canonique et chemin du validateur canonique présents dans l'ancien SKILL.md.
- [ ] Règles valides conservées ; affirmations fausses corrigées avec preuve.
- [ ] Vérification structurelle des deux Skills : PASS, FAIL et WARN rapportés.
- [ ] Deux validateurs de domaine exécutés ; codes de retour et avertissements rapportés.
- [ ] Artefacts du projet inchangés (empreintes comparées).
- [ ] Cas négatifs exécutés ou explicitement marqués comme non déclenchés.
- [ ] Rapport distinguant disque et chargement ; `/skills reload` mentionné si nécessaire.
- [ ] Aucune action destructive non autorisée.
