---
name: corriger-references-locales-skill-sous-projet
description: "Réparer un FAIL « local reference not found » quand un Skill décrit un sous-projet du workspace : reproduire l'échec, prouver que le fichier existe sous un sous-dossier (ex. ASTRO-Q°ODE_SYSTEME/), préfixer les jetons backtick par le chemin relatif exact au workspace au lieu de renommer le fichier ou de déplacer --workspace, réaligner les commandes des blocs clôturés par cd vers ce sous-dossier, rejouer validate_skill.py jusqu'à RESULT PASS, puis recalculer les SHA-256 cités et signaler toute dérive. Complète qualifier-chemins-references-skill et reparer-paquet-skill-echecs-qa ; ne traite ni les autres causes de FAIL ni les références de Skills. Utiliser quand validate_skill.py renvoie local reference not found sur un chemin projet-relatif valide sur disque, quand un sous-dossier du workspace est omis dans un chemin, ou quand une commande citée ne s'exécute pas depuis le répertoire documenté. 中文触发：Skill 本地引用修复、子目录路径前缀、local reference not found。"
---

# Réparer les références locales d'un Skill qui décrit un sous-projet

## Portée

Cas unique : le validateur renvoie `local reference not found` pour une référence dont le fichier existe réellement dans le workspace, sous un sous-dossier du projet. Sa résolution est fermée — dossier du Skill, puis racine passée à `--workspace` — donc la cause est un chemin incomplet, jamais un fichier manquant.

| Besoin | Skill |
| :--- | :--- |
| Contrat de collecte, jetons ignorés, pré-qualification | `qualifier-chemins-references-skill` |
| Triage des autres causes de FAIL (racine imbriquée, jeton faux, cache) | `reparer-paquet-skill-echecs-qa` |
| Acceptation statique complète | `skill-file-qa` |
| Variantes de commande incohérentes après réparation | `aligner-variantes-commande-skill` |
| Fraîcheur des empreintes citées | `verifier-fraicheur-preuves-skill` |

## 1. Reproduire et localiser

1. Relever la sortie exacte : chaque ligne `FAIL local reference not found`, puis `Summary` et code de retour. Ne corriger que les références listées.
2. Prouver que le fichier existe, sans supposer son emplacement :

   ```bash
   find "<workspace>" -name "<fichier>" -not -path "*/.git/*"
   ```

3. En déduire le chemin relatif au workspace, sous-dossier compris. C'est ce chemin exact qui doit figurer dans le Skill.

Si `find` ne rend rien, ce n'est pas un préfixe : arrêter et passer à `reparer-paquet-skill-echecs-qa`.

## 2. Choisir la correction

| Situation | Correction |
| :--- | :--- |
| Fichier du projet, rangé sous un sous-dossier | préfixer la référence par ce sous-dossier, workspace inchangé |
| Ressource propre au Skill | la placer dans le Skill et la citer relativement au Skill |
| Fichier hors de toute racine connue | le copier sous le Skill, ou renoncer à le citer |

Interdits : renommer le fichier pour faire passer le test, écrire `..`, citer un chemin absolu, déplacer `--workspace` pour une seule référence. Les trois derniers ne sont même pas contrôlés : le PASS deviendrait muet sur ces chemins.

## 3. Préfixer sans casser les commandes

Réécrire chaque jeton compté — corps, tableaux, listes — avec le chemin complet. Les commandes des blocs clôturés ne sont pas collectées ; elles doivent pourtant rester exécutables.

```bash
# avant : chemin projet-relatif, échoue depuis la racine
py -3 deploiement_vps/rotation_secret_webhooks.py --verifier

# après : on entre dans le sous-dossier, la commande reste relative
cd ASTRO-Q°ODE_SYSTEME
py -3 deploiement_vps/rotation_secret_webhooks.py --verifier
```

Préférer un `cd` vers le sous-dossier au préfixage de chaque commande, et garder un seul workspace pour tout le Skill.

## 4. Rejouer jusqu'au PASS

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<dossier-skill>" \
  --workspace "<racine-projet>" --stable-seconds 2 --stability-timeout 30
```

Exiger `PASS local references: N checked`, `RESULT PASS`, rc 0. La ligne de compte n'apparaît que si aucune référence ne manque : comparer N à l'inventaire de l'étape 1, sinon un jeton ignoré en silence passerait pour une preuve.

## 5. Recalculer les empreintes citées

Une correction de chemin périme vite les SHA-256 écrits à côté. Recalculer chaque empreinte citée et rapporter la dérive observée au lieu d'affirmer qu'elle est nulle.

Cas vérifié le 2026-10-28 : sur sept empreintes recalculées pendant la session, cinq avaient changé quelques heures plus tard — unité systemd de 724 à 722 octets — sans lien avec la réparation.

## 6. Pièges vérifiés

| Piège | Effet | Parade |
| :--- | :--- | :--- |
| Renommer le fichier | casse les autres citations sans corriger la cause | préfixer le chemin |
| `..` dans la référence | ignoré, jamais vérifié | chemin complet depuis la racine |
| Chemin absolu | ignoré, QA vert sans preuve | chemin relatif |
| `--workspace` déplacé vers le sous-dossier | les références au dossier du Skill ou à la racine cassent | un seul workspace, la racine projet |
| Extension non contrôlée ou nom de fichier nu | jamais compté : `.service`, `.key` | vérifier à la main, ne rien conclure du PASS |
| Commande nue dans un bloc clôturé | jamais comptée | exécuter l'extrait depuis le répertoire documenté |
| Empreinte non recalculée après correction | preuve périmée | recalculer et dater la dérive |

## 7. Critères de sortie

- Les références listées par le FAIL sont réécrites ; aucune autre n'a changé de sens.
- `RESULT PASS`, rc 0, `PASS local references: N checked` avec N égal à l'inventaire.
- Les commandes citées s'exécutent depuis le répertoire que le Skill indique.
- Les empreintes citées sont recalculées ; toute dérive est datée.
- Aucun `__pycache__` ni fichier temporaire laissé dans le paquet.

## Ressources

Aucune ressource embarquée : le contrat de collecte et le script de qualification appartiennent à `qualifier-chemins-references-skill`. Ce Skill ne fait que la réparation et la preuve.
