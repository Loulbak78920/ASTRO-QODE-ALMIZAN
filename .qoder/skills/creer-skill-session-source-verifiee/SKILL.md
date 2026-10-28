---
name: creer-skill-session-source-verifiee
description: "Créer ou mettre à jour un Skill étroit depuis une session Qoder source vérifiée : inventorier les preuves malgré la troncature de read_chat_session ou un message humain en messageStream=thinking, auditer la couverture des Skills installés, faire trancher le périmètre et le paquet par l'utilisateur, tester les compteurs et cas négatifs hors installation, puis valider avec skill-file-qa. Utiliser quand la tâche est de créer un Skill à partir d'une session source, quand read_chat_session renvoie OUTPUT TRUNCATED, quand un message utilisateur est invisible, quand un compteur de script est douteux, ou quand un Skill existant couvre déjà une partie du besoin. 关键词：来源会话建 Skill、会话截断、覆盖矩阵、用户裁决、反例测试、写入后验收。Ne remplace pas les Skills spécialisés cités dans la chaîne."
---

# Créer un Skill depuis une session source vérifiée

## Quand l'utiliser

- Créer ou mettre à jour un Skill à partir d'une session Qoder citée par identifiant.
- `read_chat_session` renvoie `OUTPUT TRUNCATED`, `hasMoreBefore=true` ou une fenêtre récente seulement.
- Un message humain semble absent alors que la session contient une demande.
- Un Skill existant couvre déjà une partie du besoin et le périmètre doit être arbitré.
- Un script de Skill émet un compteur que la session ne permet pas de vérifier.

## Quand ne pas l'utiliser

- Audit complet d'une chaîne de références, d'intentions ou de fraîcheur : `audit-session-evidence`.
- Extraction brute d'un JSONL ou appariement tool_use/tool_result : `extraire-preuves-session-qoder`.
- Matrice de couverture seule : `auditer-couverture-skill-avant-creation`.
- Budget et nombre de fichiers seuls : `planifier-budget-paquet-skill`.
- QA d'un paquet déjà écrit : `skill-file-qa`.
- Renommage, déplacement ou simple changement de format : suivre `skill-creator` sans nouvelle assertion.

## Règles non négociables

1. Charger `skill-creator` avant d'écrire ; `create` ne remplace jamais un dossier homonyme.
2. Ne jamais compléter une session tronquée par déduction. Lire le fichier `tool-results` ou le JSONL.
3. Filtrer les messages humains par `role`, pas par `messageStream` seul ; `thinking` peut porter une vraie demande.
4. `read_chat_session` ne rend que les noms et statuts des outils. Citer les sorties ; classer chaque commande « vérifiée » ou « recommandée ».
5. Écrire la matrice de couverture avant le plan. Si un Skill existant couvre l'essentiel, faire choisir à l'utilisateur entre créer étroit, étendre ou ne pas créer.
6. Un compteur se déduit des ensembles, pas des totaux. Tester le cas « aucun candidat revu » et attendre zéro.
7. Recompter les fichiers de périmètre sur disque. Ne pas déduire un total d'une liste partielle.

## Chaîne en six étapes

### 1. Préflight

```bash
T="<skill-dir>"
test ! -e "$T" && echo CIBLE_ABSENTE
```

- Si la cible existe, passer en update : lire `SKILL.md`, les références et les scripts, puis suivre `skill-update-concurrency-safe`. Ne pas écraser.
- Vérifier un homonyme dans les deux racines de Skills, projet et utilisateur.
- Relire la cible juste avant la première écriture ; si elle est apparue entre-temps, arrêter et appliquer `adopt-concurrent-duplicate-skill`.

### 2. Inventaire des preuves

- Lire la session avec `read_chat_session` en bornant la sortie.
- Si `OUTPUT TRUNCATED`, lire le fichier `tool-results` cité, ou extraire le JSONL :

```bash
py -3 -B "$HOME/.qoder/skills/extraire-preuves-session-qoder/scripts/extract_session_evidence.py" \
  <session.jsonl> --users --max-chars 2000
```

- Remplir un tableau : fait | sortie citée | statut | ligne JSONL.
- Statuts admis : `REPRODUIT`, `RECOMMANDÉ`, `INFÉRÉ`. Un statut `REPRODUIT` exige la sortie exacte, pas un résumé.
- Consigner `sessionId`, `revision`, `runtimeState`, `hasMoreBefore` et l'heure de lecture.
- Si le JSONL est utilisé, relever ses lignes, sa taille et son SHA-256 avant et après l'extraction.

### 3. Matrice de couverture

- Envoyer les capacités du paquet à `auditer-couverture-skill-avant-creation`.
- Verdict par capacité : `COVERED`, `PARTIAL` ou `ABSENT`.
- `COVERED` : proposer une mise à jour, pas une création.
- `PARTIAL` : écrire les non-usages et la délégation avant de créer.
- `ABSENT` : créer.
- Ne jamais conclure « aucun Skill ne couvre » sans avoir cherché dans les deux racines, les références et les scripts.

### 4. Décision de périmètre par l'utilisateur

- Poser deux questions au maximum : périmètre (étroit, extension, pas de création) et paquet (`SKILL.md` seul, avec références, avec script).
- Enregistrer la réponse. Ne pas choisir à sa place quand la couverture est proche.
- Annoncer le nombre de fichiers, le budget de lignes et les ressources incluses ou exclues avant écriture.
- Toute modification du nombre de références ou de scripts impose de recalculer et de représenter le paquet complet.

### 5. Rédaction et tests du paquet

- Écrire `SKILL.md` d'abord, puis les références et scripts.
- Placer la procédure à chaque usage dans `SKILL.md` ; les preuves et cas dans le dossier `references` ; seul le code déterministe réutilisé dans un dossier `scripts`.
- Ne pas créer `README.md`, `CHANGELOG.md` ni guide d'installation.
- Tester chaque script hors installation : un cas positif, un cas négatif, et un cas où le compteur doit valoir zéro.
- Vérifier que le dossier de fixture est supprimé et que l'installation n'a pas changé pendant le test.

### 6. Validation et rapport

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<skill-dir>" \
  --workspace "<workspace-root>" --skills-root "$HOME/.qoder/skills"
```

- Attendu : `RESULT PASS`, `Files (N)` égal au paquet annoncé, `Fingerprint (start)` égal à `Fingerprint (final)`.
- Relire les fichiers réels, puis relever les empreintes et les lignes :

```bash
find "<skill-dir>" -type f | sort
sha256sum "<skill-dir>/SKILL.md" "<skill-dir>"/references/*.md
wc -l "<skill-dir>/SKILL.md"
```

- Vérifier que chaque nom de Skill entre backticks existe dans une racine de Skills.
- Vérifier chaque numéro de ligne cité dans les références contre le fichier ou le JSONL cité.
- Si un contrôle échoue, corriger et relancer. Ne pas annoncer la création ou la mise à jour.
- Le rapport final distingue ce qui est vérifié, ce qui est seulement statique et ce qui reste non vérifié.

## Pièges observés

| Piège | Preuve | Correction |
| :--- | :--- | :--- |
| Sortie de session tronquée | `~94992 tokens (284 976 characters)` puis un fichier `tool-results` cité | Lire le fichier complet ou le JSONL ; ne pas déduire le contenu manquant |
| Message humain invisible | filtre `messageStream in (None, final, response)` ; la demande réelle était en `thinking` | Filtrer par `role` ; inclure `thinking` ; un résultat vide n'est pas une absence |
| Commandes absentes des métadonnées d'outils | `read_chat_session` rend des noms et statuts, pas les lignes de commande | Citer les sorties et classer « vérifiée » ou « recommandée » |
| Couverture proche d'un Skill existant | un Skill couvrait déjà la compilation, `--overwrite`, le pipe et le nettoyage | Produire la matrice, puis faire trancher le périmètre par l'utilisateur |
| Compteur faux après test | `CANDIDATS_REVUS=1` alors qu'aucun `--revu` n'était fourni | Dériver le compteur de l'ensemble réel ; tester le cas zéro |
| Total hors périmètre faux | 13 fichiers, 5 dans le périmètre, mais « 6 hors périmètre » écrit | Recompter : 8 hors périmètre, puis séparer exacts et plages |

## Délégation

| Besoin | Skill |
| :--- | :--- |
| Chaîne de références, attribution des intentions, fraîcheur | `audit-session-evidence` |
| JSONL, tool_use/tool_result, erreurs et extraits | `extraire-preuves-session-qoder` |
| Matrice de couverture et décision créer/étendre | `auditer-couverture-skill-avant-creation` |
| Budget, nombre de fichiers et confirmation du paquet | `planifier-budget-paquet-skill` |
| Niveau de preuve des assertions avant écriture | `verify-skill-doc-claims-before-edit` |
| Écriture sûre et concurrence | `skill-update-concurrency-safe` |
| QA de livraison et fingerprint | `skill-file-qa` |
| Cas de référence et dossier de preuves | `write-skill-evidence-case-study` |

## Checklist de livraison

- [ ] `skill-creator` chargé ; cible absente ou update explicitement confirmé.
- [ ] Session, tour utile, `revision` et heure de lecture consignés.
- [ ] Messages humains filtrés par `role` ; `thinking` inclus.
- [ ] Chaque fait porte une sortie citée et un statut.
- [ ] Chaque commande est marquée « vérifiée » ou « recommandée ».
- [ ] Matrice de couverture avec verdicts et numéros de ligne.
- [ ] Périmètre et paquet confirmés par l'utilisateur.
- [ ] Scripts testés hors installation ; compteur à zéro couvert.
- [ ] `RESULT PASS`, `Files (N)` et empreintes relevés.
- [ ] Références locales et inter-Skills résolues.
- [ ] Aucun `README.md`, cache ou fichier hors cible.

## Ressources

- `references/cas-verifie-session-e0b0457c-2026-10-28.md` : preuves de la session source, lignes JSONL, sorties exactes et limites.
