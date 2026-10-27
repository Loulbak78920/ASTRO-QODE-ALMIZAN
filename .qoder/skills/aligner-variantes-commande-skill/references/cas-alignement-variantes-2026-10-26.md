# Cas — alignement des variantes de commande (2026-10-26)

## Provenance

- Session source : `e9a3ca61-bd38-4436-9a11-c51830242eb9`, titre « 创建恢复 Skill 方案 ». Snapshot lu le 2026-10-26 : `runtimeState=cold`, `revision=0`, 2 messages, `hasMoreBefore=false`. C'est un tour unique : demande de création, puis rapport final de l'agent.
- Le snapshot ne contient pas les sorties d'outils détaillées (seulement les noms et statuts). Les nombres et les sorties cités ici proviennent du rapport final de cette session et du fichier de référence du paquet cible, pas d'une ré-exécution des harnais d'origine.
- Paquet cible observé : `C:/Users/Administrateur/.qoder/skills/restaurer-skill-apres-bascule-main`.
  - `SKILL.md` : 16 182 octets, SHA-256 `31a97a1019af1de2b8f092a77004090b1210a38133f9801d5fbe1d5114c0c106`, CR=0, variables positionnelles 0.
  - `references/cas-bascule-main-2026-10-26.md` : 12 373 octets, SHA-256 `624cdc9ffe27a82854690ddca6bfc24364b126b76d72e28eddc8294965b68225`, CR=0, variables positionnelles 0.
  - Ces empreintes sont datées ; elles ne sont pas des constantes.
- Mise à jour du 2026-10-26 : session source `b04fed25-1f00-438c-aeaf-5af8192939dc`, `runtimeState=ready`, `revision=66`, `activeTurnId=null` au moment de la rédaction. Le contrôle positif synthétique DRIFT→ALIGNED y a été exécuté, puis rejoué pendant cette mise à jour avec le code d'inventaire extrait du `SKILL.md` sur disque. Les comptes de la section dédiée viennent de cette ré-exécution, pas seulement du rapport final de la session.

## Situation observée

La restauration avait été corrigée dans une seule section. Les autres mentions décrivaient encore une autre approche :

- la `description` et l'étape 1 utilisaient `ls-tree` + `cat-file blob` ;
- l'étape 5 d'une version intermédiaire utilisait `git rev-parse --verify "main:<chemin>"` ;
- le tableau des pièges affirmait que la syntaxe à deux-points était ambiguë et recommandait `ls-tree` ;
- les references mélangeaient plusieurs comptes d'assertions sans dire quelle forme chacun couvrait.

Le PASS structurel du validateur n'a pas détecté ces contradictions : il ne compare pas les sections entre elles.

## Matrice des quatre formes

| Forme | Emplacements observés | Exercée par | Assertions | Couverture réelle | Incompatibilité | Statut |
|---|---|---|---|---|---|---|
| `ls-tree` + `awk` (troisième champ) | harnais de bascule du paquet cible | 2 cas, racines et commits différents | 80 (26 + 54) | création de `main`, bascule, EOL de l'archive, octets restaurés, statut | contient une variable positionnelle numérique, donc substituable à l'appel | `FIXTURE_VERIFIED` pour le flux ; rejetée comme forme livrée |
| `cut -d' ' -f3` | envisagée, aucune fixture passante | aucune | 0 | aucune | la sortie sépare l'OID du chemin par une tabulation ; le champ contient OID + tabulation + chemin | `STRUCTURALLY_BROKEN` |
| `rev-parse --verify "main:<chemin>"` | étape 5 d'une version intermédiaire | fixture dédiée | 19 | extraction de l'OID | contredit l'étape 1 et le piège sur la syntaxe à deux-points du même paquet | `FIXTURE_VERIFIED` isolément ; rejetée pour incohérence interne |
| `ls-tree` + `read -r` | forme livrée | fixture dédiée | 25 | OID 40 hexadécimaux, type `blob`, octets identiques, CR=0, statut, chemin absent → OID vide, garde en échec sans fichier créé | aucune connue | `FIXTURE_VERIFIED`, canonique |

Mesures complémentaires, à ne pas confondre avec la forme livrée :

| Mesure | Source | Assertions | Portée |
|---|---|---|---|
| harnais indépendant | session parallèle `8627a51e-b148-4690-9f79-42c204bc799b` | 46 | deux racines et deux commits différents ; flux complet |
| rejeu de l'extrait documentaire | session source `e9a3ca61` | 11 | extrait du `SKILL.md` après remplacement des placeholders ; SHA-256, CR, statut |
| rejeu de création de ce Skill | 2026-10-26, cette création | 16 | extrait lignes 115–122 du paquet cible ; SHA-256, CR, statut, garde sur chemin absent |

Le paquet cible affiche un bloc `read -r` sous « commande centrale exercée » tout en précisant que le harnais à 80 extrayait l'OID par `awk`. La présentation peut laisser croire que les 80 assertions couvrent la forme livrée ; ce n'est pas le cas. Les comptes restent séparés : 80 pour le flux avec extraction par `awk`, 25 pour l'extraction livrée.

## Corrections de harnais

1. **Harnais à 80 assertions, premier essai** : 4 échecs parce que l'archive de `main` avait été écrite avec un texte différent du fichier validé. Le défaut venait du harnais, pas de la procédure. Après alignement des octets, 80/80 passent.
2. **Fixture de la forme livrée, premier essai** : 1 échec parce que l'assertion comparait `HEAD` à une référence de reflog (`main@{0}`). L'assertion mesurait autre chose que l'état attendu. Après correction, 25/25 passent.
3. **Rejeu de création, premier essai** : 1 échec parce que l'assertion attendait `?? references/preuve.md` alors que `git status --porcelain` replie le répertoire non suivi en `?? references/`. La forme enregistrée dans le paquet cible était bien `?? references/`. Après correction de l'assertion et ajout d'un contrôle `-uall`, 16/16 passent.

Règle conservée : un fixture doit d'abord reproduire les octets et la forme d'état validés ; sinon ses échecs accusent à tort la procédure. Ne jamais affaiblir une assertion pour obtenir un PASS.

## Faux positif d'un scan shell

Reproduction exécutée le 2026-10-26 dans un répertoire temporaire :

- un fichier contient une ligne `session e9a3ca61-bd38-4436-9a11-c51830242eb9` ;
- une commande `bash` interne reçoit un motif `grep` en guillemets doubles contenant une référence positionnelle ; l'argument transmis est le début de l'identifiant de session ;
- la substitution d'argument remplace la référence par le texte de l'argument, et `grep` trouve l'identifiant de session.

Sorties observées :

```text
1:session e9a3ca61-bd38-4436-9a11-c51830242eb9
RC_GREP=0
BYTE_SCAN_TOTAL=0
```

Le hit shell est donc un faux positif : le fichier ne contient aucune variable positionnelle. Les niveaux d'échappement produisent aussi des faux négatifs (motif ancré ou barre oblique inversée en trop). Conséquence : reclasser toute sortie shell avec le scan octet de l'étape 6, et ne compter que les octets.

## Vérification faite lors de la création

- Extrait source : lignes 115–122 de `restaurer-skill-apres-bascule-main/SKILL.md`, fichier source SHA-256 `31a97a10…`.
- Placeholders remplacés : `<nom>` → `demo`, `<fichier>` → `preuve`.
- Extrait produit : SHA-256 `6488d7ad22b6ab73badbebf473f0d26c7ec2a7a1e8032bb060123729b99fa1e4`.
- Fixture : dépôt nu, monorepo `main` avec un `SKILL.md` racine différent, archive sous `.qoder/skills/demo/`, dépôt Skill à histoire distincte, HEAD détaché, bascule `main`.
- Résultat : `REPLAY pass=16 fail=0`.
- Assertions couvertes : code de bascule 0, racine remplacée, `references/` absent avant restauration, code de l'extrait 0, SHA-256 du `SKILL.md` et de la reference égaux aux octets validés, CR=0 pour les deux, statut par défaut ` M SKILL.md` + `?? references/`, statut `-uall` avec le fichier exact, OID de 40 hexadécimaux, type `blob`, chemin absent → OID vide, garde en échec, aucun fichier créé.
- Les valeurs SHA-256 `762ffce3…` et `6e40bc52…` observées dans le fixture sont propres à ce fixture ; elles ne sont pas des empreintes de production.
- Les deux heredocs ont été extraits du `SKILL.md` écrit et exécutés : inventaire sur un fixture à deux variantes (4 `HIT`, rc=0), scan octet sur un fixture sans variable (0, rc=0), sur un fixture avec deux formes (2, rc=1) et sur le paquet lui-même (0, rc=0).

## Vérification indépendante (2026-10-26, adoption)

Le paquet a été créé par une session concurrente (`96f7e72c-8f2b-47c4-a522-fa34cfd3f122`, révision 79, `ready`) après l'ouverture de la tâche. Les octets finaux ont été adoptés, pas réécrits.

- Octets adoptés avant les corrections de cette session : `SKILL.md` 16 450 octets, SHA-256 `696859794a970837981bc8652f8ba9de31f7849206d93a54a16f9071fde80c30` ; reference 10 509 octets, SHA-256 `899652919d15ed88b033345963939891bb342b1eca70f056dcb457a0d40bf246`.
- `skill-file-qa` sur ces octets : PASS, 9 pass / 0 fail / 0 warn, `Files (2)`, corps 234 lignes, description 1 014 caractères, 7 références inter-Skills.
- Scan octet : `POSVAR_TOTAL=0`, `CR=0` pour les deux fichiers, aucun `__pycache__`.
- Rejeu indépendant de l'extrait canonique, extrait du paquet cible aux lignes 115–122 : `REPLAY pass=16 fail=0`, SHA-256 de l'extrait `6488d7ad22b6ab73badbebf473f0d26c7ec2a7a1e8032bb060123729b99fa1e4`.
- Les hashes `762ffce3…` et `6e40bc52…` du fixture d'origine ne sont pas reproduits : le contenu de ce fixture diffère. L'assertion utilisée compare l'archive et le fichier restauré octet pour octet, pas à ces valeurs.
- Faux positif shell reproduit le 2026-10-26 : `bash -c` avec un motif passé en argument, `RC_GREP=0` sur l'identifiant de session, `BYTE_SCAN_TOTAL=0` sur le même fichier.
- Corrections apportées ensuite : garde `MISSING SKILL.md` et motif absent avec code 2 (étape 1) ; plage de lignes générique à l'étape 5 ; rapport `bytes` et `CR` par fichier à l'étape 6, avec exigence `CR=0`.
- Le rejeu à 16 assertions a été exécuté avant ces corrections puis rejoué après, sans changement ; il porte sur l'extrait du paquet cible et reste indépendant des trois corrections. `skill-file-qa` et le scan octet ont été relancés après.

## Contrôle positif synthétique du scan (2026-10-26)

Un inventaire à 0 `HIT` ne prouve pas l'absence de dérive : il peut venir d'un motif erroné. Le contrôle monte un paquet synthétique en phase DRIFT, vérifie que le scan détecte la forme écartée, l'aligne puis réinventorie.

Paquet synthétique : `SKILL.md` + `references/cas.md`, phase DRIFT avec trois `git rev-parse --verify "main:…"`, phase ALIGNED avec `ls-tree` + `read -r`. Motifs passés au scan : `rev-parse --verify` (forme écartée, discriminant) et `read -r` (forme canonique).

| État | `rev-parse --verify` | `read -r` | `ls-tree` |
|---|---|---|---|
| DRIFT | 3 | 0 | 0 |
| ALIGNED | 0 | 1 | 2 |

- `DRIFT_OLD_HITS=3`, `ALIGNED_OLD_HITS=0`, `ALIGNED_CANONICAL_HITS=1` : le scan détecte la dérive connue et son absence après alignement.
- Gardes : sans motif, code 2 avec `USAGE: <dossier-skill> <motif> [motif ...]` ; cible sans `SKILL.md`, code 2 avec `MISSING SKILL.md: …`.
- Correction d'une ambiguïté : le rapport source annonçait « 对齐后 0 个 ». La ré-exécution montre 0 `rev-parse --verify`, mais 3 `HIT` au total en phase ALIGNED (2 `ls-tree`, 1 `read -r`). « 0 » qualifie la forme écartée, jamais le total.
- `ls-tree` ne discrimine pas : 0 `HIT` en DRIFT, 2 en ALIGNED, car il apparaît aussi dans la forme canonique. Un contrôle fondé sur ce motif seul conclurait à tort à l'absence de dérive.
- Paquet réel avant mise à jour : 3 `HIT` `rev-parse --verify` (liste d'arguments du scan et deux mentions historiques) et 4 `HIT` `read -r` (liste d'arguments, matrice, application), aucun en section normative. Le total n'est donc pas nul et ne doit pas l'être.
- Empreintes du paquet avant mise à jour : `SKILL.md` 17 633 octets, SHA-256 `cc3aac6388086c704d81ae63979e2badced7cbcc2f97ecfbe317927be835ab67` ; reference 12 500 octets, SHA-256 `c488575a74011c4426499dc5402d3567d0d7d90e7734f73121e81eda7d9f97ab`.
- Le paquet synthétique et le script de contrôle ont été supprimés après exécution ; `NO_FIXTURE_RESIDUE`.

## Application au présent paquet

Le présent `SKILL.md` mentionne les formes écartées uniquement dans le modèle mental, les règles, le tableau des pièges, la liste d'arguments du scan, le fixture de contrôle de l'étape 1bis et les procédures de rejeu, jamais comme commande normative concurrente. La forme canonique décrite est `ls-tree` + `read -r` avec variables nommées. Les quatre formes sont nommées dans ce document pour l'historique, avec leur statut. Le scan du paquet réel n'est donc pas nul : l'exigence est 0 `HIT` normatif, pas 0 `HIT` total.

## Limites

- Les harnais à 80, 46, 19 et 11 assertions n'ont pas été ré-exécutés ici ; ils sont rapportés par la session source ou par le paquet cible. Seul le rejeu à 16 assertions a été exécuté lors de cette création.
- Le fixture à 25 assertions n'était pas disponible sous forme de script ; sa couverture est reprise telle que documentée. Le rejeu à 16 assertions est une vérification indépendante de l'extrait, pas une reproduction du fixture à 25.
- La forme canonique a été extraite du paquet cible à l'empreinte indiquée. Si ce paquet change, extraire à nouveau et comparer les octets.
- Non observé : un `origin/main` qui avance pendant l'opération, un dépôt shallow, plusieurs worktrees, une exécution sous un shell autre que Bash.
- Le contrôle synthétique prouve que le scan détecte les motifs choisis sur un paquet connu ; il ne prouve pas que le paquet cible est aligné. L'alignement de la cible se juge par la classification des `HIT`, pas par un total nul.
- Le contrôle ne couvre que deux motifs (`rev-parse --verify`, `read -r`) ; un motif propre à une autre variante doit être validé de la même façon avant d'être accepté.

## Statut des affirmations

| Affirmation | Statut | Base |
|---|---|---|
| une réparation partielle laisse les autres sections incohérentes | vérifié dans le paquet cible | `description`, étape 1, étape 5 intermédiaire, tableau des pièges |
| le PASS structurel ne détecte pas ces contradictions | vérifié par la nature du validateur | le validateur ne compare pas les sections |
| `cut -d' '` casse l'extraction de l'OID | vérifié par la structure de sortie | tabulation entre OID et chemin |
| la forme à 19 assertions fonctionne isolément | rapporté par le paquet cible | fixture dédiée |
| la forme livrée est couverte par 25 assertions | rapporté par le paquet cible | fixture dédiée |
| les 80 assertions couvrent la forme livrée | **faux** | le harnais extrayait l'OID par `awk` |
| un scan shell peut produire un faux positif | vérifié le 2026-10-26 | reproduction ci-dessus |
| le rejeu de l'extrait livré passe | vérifié le 2026-10-26 | `REPLAY pass=16 fail=0` |
| le paquet adopté passe QA et le rejeu indépendant | vérifié le 2026-10-26 | PASS 9/0/0, `POSVAR_TOTAL=0`, `CR=0`, `REPLAY pass=16 fail=0` |
| le statut par défaut replie `references/` | vérifié le 2026-10-26 | `status_exact` et `status_uall_exact` |
| le scan détecte une dérive connue avant alignement | vérifié le 2026-10-26 | `DRIFT_OLD=3`, `ALIGNED_OLD=0`, `ALIGNED_CANON=1`, gardes rc=2 |
| `ls-tree` discrimine une dérive | **faux** | 0 `HIT` en DRIFT, 2 en ALIGNED |
| un paquet aligné peut garder des `HIT` non normatifs | vérifié le 2026-10-26 | paquet réel avant mise à jour : 3 `rev-parse --verify` + 4 `read -r`, hors sections normatives |
| le comportement au-delà des cas cités | non vérifié | non observé |

## Différences avec la recommandation automatique

- La recommandation proposait un script `inventorier_variantes.py` et un scan octet intégré. Le périmètre retenu par l'utilisateur est `SKILL.md` + reference, sans script : l'inventaire et le scan sont des heredocs en lecture seule, testés sur fixtures avant écriture.
- La recommandation citait deux leçons (faux positif shell, assertion erronée). Ce document les reprend, reproduit la première et ajoute un troisième cas d'assertion erronée observé lors du rejeu de création (repliement du répertoire non suivi).
- La recommandation annonçait 80/19/25 comme si les trois mesures étaient comparables. Elles ne le sont pas : chaque compte est rattaché à la forme exacte et à sa couverture.
- La recommandation proposait `ls-tree` parmi les motifs à détecter, sans voir qu'il apparaît aussi dans la forme canonique. Le contrôle utilise `rev-parse --verify` comme motif de la forme écartée et `read -r` comme motif de la forme canonique ; `ls-tree` est explicitement rejeté comme discriminant.
- La recommandation présentait « 0 » comme un résultat global. Il est requalifié : 0 `HIT` de la forme écartée, et 0 `HIT` normatif sur le paquet réel ; le total peut rester non nul.
