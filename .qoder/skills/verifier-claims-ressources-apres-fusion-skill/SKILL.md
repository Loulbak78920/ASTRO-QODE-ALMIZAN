---
name: verifier-claims-ressources-apres-fusion-skill
description: "Après qu'une autre session a fusionné du contenu dans un Skill qu'on vient de mettre à jour, vérifier que le PASS de skill-file-qa ne masque pas une fausse référence : relire le SKILL.md fusionné depuis le disque, compter les marqueurs de ses propres éditions, extraire chaque affirmation « fichier — contenu » de la section Ressources, compter un jeton distinctif dans le fichier cité (0 = CLAIM_EMPTY, même avec « local references: N checked »), attribuer chaque fichier par SHA-256 (le sien ou réécrit par l'autre session), puis ne pas modifier les lignes d'un écrivain encore actif et revérifier les affirmations après quiescence avant tout alignement. Utiliser quand Files (N) ou le hash de SKILL.md dérive pendant la validation, quand une session concurrente ajoute un script ou une section, ou avant de livrer un paquet fusionné. 用于合并后校验资源声明与文件内容、自有编辑存活、并发写入归属。"
---

# Vérifier les affirmations de ressources après une fusion

## Objectif et limites

Après une mise à jour, une autre session peut fusionner du contenu dans le même Skill pendant la validation. Un `RESULT PASS` de `skill-file-qa` prouve alors que les chemins se résolvent, pas que les descriptions de la section « Ressources » correspondent au contenu des fichiers cités : le validateur affiche `PASS local references: N checked` sans lire le sens de la prose.

Ce Skill couvre ce contrôle étroit : ses propres éditions ont-elles survécu, et chaque contenu annoncé existe-t-il réellement dans le fichier cité ?

Il ne remplace pas :

- `verifier-reecriture-concurrente-paquet-skill` : baseline complète, qualification de la dérive, reconstruction JSONL, rapport FINAL/PROVISIONAL ;
- `audit-skill-during-live-creation` : preuve d'activité de l'écrivain et attente de quiescence ;
- `skill-update-concurrency-safe` : sauvegarde, écriture minimale, fusion des ajouts ;
- `verifier-parite-doc-script-skill` : contrat documentation/script (clés, codes de retour) ;
- `auditer-paquet-skill-concurrent-sans-modification` : audit lecture seule d'un paquet tiers ;
- `skill-file-qa` : ce que le validateur vérifie réellement.

## Quand l'utiliser

- `Files (N)` ou le SHA-256 de `SKILL.md` a changé entre deux contrôles, ou pendant la validation.
- Une session concurrente a ajouté une section, un piège, une case de checklist ou un script.
- La section « Ressources » annonce un thème dans une référence, et il faut savoir s'il y est vraiment.
- On s'apprête à livrer ou à archiver un paquet issu d'une fusion.

## Contrat non négociable

1. **PASS ne prouve pas la parité sémantique.** Le validateur résout les chemins et compte les références locales ; il ne compare pas les descriptions au contenu.
2. **Relire depuis le disque.** L'état en contexte et les éditions précédentes ne sont pas la version fusionnée. Rouvrir le fichier réel avant tout comptage.
3. **Compter ses propres marqueurs.** Pour chaque édition personnelle, choisir une phrase distinctive et exiger le nombre exact attendu dans le `SKILL.md` fusionné. Un marqueur absent ou en double est `OWN_EDIT_LOST` tant que la cause n'est pas établie.
4. **Une affirmation se vérifie par un jeton distinctif.** Le chemin seul ne suffit pas : compter une expression stable, sensible à la casse et aux accents, dans le fichier cité.
5. **Zéro occurrence est un constat daté, pas un verdict définitif.** Tant qu'un écrivain est actif, le classer `PROVISIONAL` : le contenu peut arriver après le constat.
6. **Attribution par empreinte.** Un fichier identique à son empreinte post-édition est le sien ; un fichier dont le SHA-256 diffère et dont le mtime suit est réécrit par l'autre session ; un fichier absent de la baseline est `AJOUTE`.
7. **Écrivain actif, zéro écriture.** Ne pas corriger les lignes d'une session encore en cours ; constater, rapporter, attendre.
8. **Revérifier avant d'aligner.** Après quiescence, rejouer les comptages avant toute édition : la session propriétaire a peut-être déjà rendu l'affirmation vraie.
9. **Ne pas fabriquer le contenu manquant.** Ajouter une section à une référence pour faire taire un comptage est une écriture de contenu, pas une correction de forme : elle exige une autorisation explicite.

## Procédure

### 1. Figer l'état et l'inventaire

Relever la liste réelle des fichiers, leur taille et leur SHA-256, puis échantillonner deux fois à au moins 2 s d'intervalle. Noter aussi la sortie de `skill-file-qa` : `Files (N)`, `PASS local references: N checked`, empreinte de début et de fin.

Conserver la baseline hors du paquet. Si elle manque, utiliser celle de `verifier-reecriture-concurrente-paquet-skill` ; sans baseline, l'état antérieur est inconnu, pas « inchangé ».

### 2. Qualifier la dérive et attribuer

| Observation | Qualification |
|---|---|
| SHA-256 égal à l'empreinte post-édition | `MINE` |
| SHA-256 différent, mtime postérieur à votre écriture | `REECRIT_PAR_AUTRE` |
| fichier absent de votre baseline | `AJOUTE` |
| fichier de votre baseline disparu | `SUPPRIME` |
| mtime changé, SHA-256 identique | `REECRIT_IDENTIQUE` : pas de dérive de contenu |

L'attribution repose sur les empreintes, pas sur le style du texte. Si l'auteur doit être nommé, déléguer la reconstruction et l'attribution à `verifier-reecriture-concurrente-paquet-skill` plutôt que de deviner.

### 3. Compter ses propres marqueurs

Choisir, pour chaque édition, une phrase que personne d'autre n'écrirait à cet endroit, puis compter :

```bash
py -3 -B scripts/verifier_claims.py CIBLE \
  --marker "Établir d'abord l'origine de asideH@1" \
  --marker "taskkill //F //PID@2"
```

Un total conforme montre que les éditions sont encore là. Il ne prouve pas que l'autre session ne les a pas déplacées ou contredites : lire les sections concernées.

### 4. Extraire les affirmations de la section Ressources

Pour chaque ligne de la forme « `chemin` — liste de contenus », isoler les contenus annoncés et choisir un jeton par contenu vérifiable.

| Règle | Exemple valide | À éviter |
|---|---|---|
| ≥ 2 mots, spécifique au thème | `repli CDP` | `mesures`, `limites`, `commandes` |
| Présent tel quel si l'affirmation est vraie | `contrôle de hauteur` | reformulation approximative |
| Casse et accents exacts | `arrêt du serveur` | `arret du serveur` |
| Un jeton par contenu distinct | `largeurs exactes` | un seul jeton pour cinq thèmes |

Une affirmation trop générale peut réussir avec un seul jeton alors que plusieurs contenus manquent : dans ce cas, multiplier les jetons plutôt que conclure sur le premier.

### 5. Compter et rendre un verdict

```bash
py -3 -B scripts/verifier_claims.py CIBLE \
  --claim "references/modeles-harnais.md::repli CDP" \
  --claim "references/cas-verifie-hub-ponts.md::repli CDP" \
  --marker "Établir d'abord l'origine de asideH@1"
```

Codes : `0` toutes les affirmations sont soutenues et tous les marqueurs conformes ; `1` au moins un écart (`CLAIM_EMPTY`, `CLAIM_MISSING`, `CLAIM_INVALID_PATH`, `CLAIM_ENCODING_ERROR`, `MARKER_MISMATCH`) ; `2` argument malformé ou `SKILL.md` illisible. Le script est en lecture seule et n'écrit ni cache ni fichier.

| Observation | Verdict |
|---|---|
| toutes les affirmations ≥ 1, marqueurs exacts, dérive attribuée | `COHERENT` |
| au moins un `CLAIM_EMPTY` sur un fichier stable et non réécrit | `CLAIM_EMPTY` |
| marqueur absent ou nombre différent de l'attendu | `OWN_EDIT_LOST` |
| dérive constatée sans baseline ou sans attribution | `DRIFT_UNATTRIBUTED` |
| écrivain actif pendant le constat | `INDETERMINE` (`PROVISIONAL`) |

### 6. Décider et agir

- **`COHERENT`** : livrer ou archiver, en rappelant que le contrôle porte sur les jetons vérifiés, pas sur toute la prose.
- **`INDETERMINE`** : ne rien écrire. Enregistrer les comptages avec l'heure, l'empreinte des fichiers et le `runtimeState` de la session propriétaire. Attendre la quiescence selon `audit-skill-during-live-creation`.
- **`CLAIM_EMPTY` après quiescence** : revérifier d'abord ; si le contenu manque toujours, deux issues seulement.
  - corriger la ligne d'affirmation (retirer le thème non soutenu), avec sauvegarde hors paquet, puis `skill-file-qa` et empreintes ;
  - ajouter le contenu à la référence uniquement avec autorisation explicite, puis revalider : c'est une écriture de contenu.
- **`OWN_EDIT_LOST`** : ne pas réappliquer à l'aveugle. Récupérer sa version depuis la sauvegarde ou le JSONL, diffuser, puis demander la décision.
- **`DRIFT_UNATTRIBUTED`** : ne pas éditer ; fournir les empreintes et laisser la qualification à l'audit de réécriture.

## Diagnostic

| Symptôme | Cause probable | Action |
|---|---|---|
| `PASS local references: 3 checked` et un thème absent du fichier | le validateur vérifie les chemins | compter le jeton ; `CLAIM_EMPTY` |
| `Files (3)` puis `Files (4)` pendant la validation | ajout concurrent | inventaire complet et attribution |
| `SKILL.md` change plusieurs fois pendant le contrôle | écrivain actif | zéro écriture, `INDETERMINE` |
| marqueur personnel introuvable | édition écrasée ou reformulée | `OWN_EDIT_LOST`, récupérer la version |
| `CLAIM_EMPTY` puis soutenu après quelques minutes | contenu ajouté par le propriétaire | ne rien éditer, reclasser `COHERENT` |
| jeton présent une fois mais plusieurs thèmes annoncés | affirmation trop large | multiplier les jetons |
| jeton accentué introuvable | casse, accents ou apostrophe différente | copier le jeton depuis le fichier cible |
| script rc=2 | format `PATH::TOKEN` ou `TOKEN@N` invalide | corriger l'argument |

## Cas vérifié (2026-10-28, session f1a9b558)

Mise à jour de `mesurer-layout-avec-harnais-iframe` ; la session `632937de` a fusionné une section CDP et ajouté un script de capture (`capturer_cdp.mjs`) pendant la validation. `Files (3)` est passé à `Files (4)` et le SHA-256 de `SKILL.md` a dérivé de `f83870ec…` à `426c3935…`. Les marqueurs personnels sont restés présents (1, 2, 1). `SKILL.md:147-148` annonçait « repli CDP » dans les deux références, où le comptage donnait `0` à 11:52 ; le validateur rendait pourtant `RESULT PASS`, 10 pass / 0 fail / 0 warn. À 12:02, le propriétaire avait ajouté le contenu (7 et 5 occurrences de `CDP`) : l'affirmation était devenue vraie sans édition de l'autre session, mais le jeton minuscule « repli CDP » restait à 0, le titre réel étant « Repli CDP ». Un jeton se copie dans le fichier cité, jamais dans la ligne d'affirmation. Détail et empreintes dans `references/cas-fusion-2026-10-28.md`.

Enseignement : le constat négatif était réel mais transitoire. Écrire à 11:52 aurait soit dupliqué le travail du propriétaire, soit supprimé une affirmation correcte. Un jeton mal copié produit en plus un faux `CLAIM_EMPTY`.

## Checklist

- [ ] `SKILL.md` relu depuis le disque après la fusion, pas depuis le contexte.
- [ ] Inventaire complet avec taille et SHA-256, deux échantillons stables.
- [ ] Sortie `skill-file-qa` conservée, avec `Files (N)` et `local references: N checked`.
- [ ] Chaque fichier attribué `MINE`, `REECRIT_PAR_AUTRE` ou `AJOUTE`.
- [ ] Chaque édition personnelle comptée avec un marqueur distinctif.
- [ ] Chaque affirmation de la section Ressources associée à un jeton distinctif.
- [ ] Comptages exécutés avec le script, codes de retour lus sans pipe.
- [ ] `CLAIM_EMPTY` daté et marqué `PROVISIONAL` si l'écrivain est actif.
- [ ] Aucune écriture dans le paquet tant que l'écrivain n'est pas quiescent.
- [ ] Revérification après quiescence avant tout alignement.
- [ ] Empreintes finales relevées, dont celles des références et scripts.
- [ ] Limites du contrôle énoncées : jetons vérifiés, pas la prose entière.

## Ressources

- `scripts/verifier_claims.py` — comptage lecture seule des jetons cités et des marqueurs personnels, inventaire taille/SHA-256, sortie JSON optionnelle, codes 0/1/2.
- `references/cas-fusion-2026-10-28.md` — preuves brutes de la fusion, chaîne d'empreintes, fenêtre 11:52–12:02, limites de reproductibilité.
- `verifier-reecriture-concurrente-paquet-skill` — baseline, dérive, reconstruction JSONL, rapport FINAL/PROVISIONAL.
- `audit-skill-during-live-creation` — activité de l'écrivain et quiescence.
- `skill-update-concurrency-safe` — sauvegarde et écriture minimale.
