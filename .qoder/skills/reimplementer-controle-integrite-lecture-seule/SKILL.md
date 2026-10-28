---
name: reimplementer-controle-integrite-lecture-seule
description: "Réimplémenter en lecture seule un contrôle d'intégrité interne (live vs copie de référence) en script stdlib autonome : inventorier le périmètre depuis le code source (exclusions, journaux auto-écrits), ne jamais importer le paquet audité, sortie ASCII stricte pour console Windows cp1252, calibrer les codes de sortie sur données réelles avant de les rendre bloquants (séparer dérive de code et churn par zone, --strict, précédence PERTE > DERIVE > CHURN > OK), puis prouver la non-écriture par un harnais hors installation (hash d'arborescence avant/après, matrice d'exit codes, absence de __pycache__, journal tronqué ignoré). Utiliser quand un contrôle interne se déclenche pendant la vérification, quand un diagnostic échoue en permanence sur des écarts attendus, ou avant de câbler un garde en CI. 中文触发：只读重实现完整性校验、自愈误触发、诊断永久红灯、按区域校准退出码、churn 与真实漂移、证明不写盘。English: read-only integrity guard reimplementation, self-healing false trigger, exit-code calibration with expected churn, off-install fixture, no-write proof."
---

# Réimplémenter un contrôle d'intégrité en lecture seule

## Vue d'ensemble

Reconstruire un contrôle interne (comparaison live vs copie de référence,
auto-guérison, garde de fichiers protégés) comme un script stdlib autonome qui
lit sans écrire, ne déclenche pas les effets de bord du paquet audité, et dont
les codes de sortie sont calibrés sur des données réelles avant d'être utilisés
comme porte CI.

Le Skill fournit un comparateur générique et un harnais hors installation. Le
cas Al-Mizan du 2026-10-27 sert de preuve ; il ne faut pas recopier ses chemins
ni son nombre d'écarts dans un autre projet.

## Quand utiliser

- Un contrôle interne se déclenche pendant une vérification et bloque le travail.
- Un script de diagnostic échoue en permanence sur des écarts attendus
  (churn d'actes, miroirs, timestamps) et ne distingue plus une vraie dérive.
- Il faut reproduire un contrôle sans importer le paquet audité, sans créer de
  `__pycache__` et sans lancer sa fonction de guérison.
- Avant de câbler un nouveau garde en CI, ou après avoir constaté qu'un garde
  existant est toujours rouge.

## Quand ne pas utiliser

- Auditer les effets de bord d'une commande déjà qualifiée de lecture seule :
  `verifier-effets-de-bord-verification-lecture-seule`.
- Tester un pré-contrôle CLI (`--yes`, secret) par espions :
  `tester-garde-cli-sans-effets-de-bord`.
- Comparer le verdict de deux outils sur les mêmes fixtures :
  `verifier-jugement-cli-par-fixtures`.
- Diagnostiquer la réversion A231/A232 d'Al-Mizan :
  `diagnostiquer-reversion-guerison-mizan`.
- Vérifier la structure ou les références d'un Skill : `skill-file-qa`.
- Réparer un contrat de sortie documentaire :
  `reparer-contrat-sortie-skill` ou `verifier-parite-doc-script-skill`.
- Classer des affirmations avant de les écrire :
  `verify-skill-doc-claims-before-edit`.

## Contrat non négociable

1. **Lecture seule** : aucun `mkdir`, aucune écriture, aucune suppression, aucun
   bytecode. Lancer avec `-B`.
2. **Aucun import du paquet audité** : pas de `import` du module, pas d'appel à
   sa fonction de contrôle ou de guérison. Le script ne dépend que de la
   bibliothèque standard.
3. **Périmètre extrait de la source**, pas de mémoire : constantes d'exclusion,
   répertoires interdits, extensions, mapping live/référence, états, journal.
4. **Preuve figée** : SHA-256 du fichier source et numéros de ligne associés.
   Les lignes ne valent que pour ce hash ; si le hash change, relire.
5. **Sortie ASCII stricte** : la console Windows cp1252/cp850 ne doit rien
   casser. Échapper les caractères non ASCII dans l'émetteur.
6. **Codes séparés** : 0 pour `OK`/`CHURN`, 1 pour `PERTE`/`DERIVE`, 2 pour
   usage, plan, racine, journal explicite ou lecture impossible.
7. **Calibrer avant de bloquer** : la première passe est une mesure, pas un
   verdict. Ne pas câbler un `exit 1` global avant d'avoir classé les zones.
8. **Zones** : `blocking` pour le code et les invariants réels ; `churn` pour
   les fichiers réécrits à chaque cycle. Un `ABSENT_LIVE` reste une `PERTE`
   dans toutes les zones.
9. **Précédence** : `PERTE > DERIVE > CHURN > OK`. Un fichier illisible produit
   `ERROR` (2), car l'intégrité ne peut pas être certifiée.
10. **`--strict` explicite** : le mode strict transforme le churn en dérive ;
    il ne doit pas être le défaut d'une CI sur une zone churn.
11. **Harnais hors installation** : fixture dans un répertoire temporaire,
    matrice des codes, hash d'arborescence avant/après, absence de
    `__pycache__`.
12. **Rapport honnête** : heure UTC, compteurs par zone, invariants, éléments
    non testés. Ne jamais réutiliser un compte d'une passe antérieure.

## Workflow

### 1. Figer le contrat depuis la source

Lire le module audité et noter :

- les constantes `EXCLUDE_*`, `ZONES_STOP`, `PROTECTED`, `IGNORE` ;
- les journaux, fichiers d'état et inbox/outbox à exclure ;
- les extensions comparées ;
- les fonctions de mapping live/référence et leurs replis ;
- la clé exacte (relative au module, au sous-dossier ou au nom de fichier) ;
- le format du journal (`phase`, `ok`, clé, type).

Consigner `chemin`, `lignes`, `SHA-256` et l'heure UTC du relevé.

### 2. Écrire le plan JSON

Décrire chaque zone avec `live_root`, `ref_roots`, `include`,
`exclude_dirs`, `exclude_globs`, `policy`. Le détail du schéma et un exemple
complet sont dans `references/perimetre-et-calibrage.md`.

Commande de contrôle :

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/reimplementer-controle-integrite-lecture-seule/scripts/controle_integrite_lecture_seule.py" \
  --plan "C:/chemin/du/projet/plan_integrite.json" \
  --base "C:/chemin/du/projet" \
  --journal-lines 5 \
  --since "2026-10-27T15:10:00Z"
```

### 3. Première passe : mesurer

Lire la ligne globale et les lignes `ZONE=...`. Vérifier :

- `DERIVES=0` sur les zones `blocking` si le code est sain ;
- `PERTES=0` si aucune référence orpheline n'est attendue ;
- `CHURN` et `NOUVEAUX` peuvent être non nuls et changer entre deux passes ;
- `RESULT CHURN` et exit 0 en mode par défaut.

Ne pas conclure d'un total global : un total stable peut cacher une dérive de
code compensée par du churn.

### 4. Classer et calibrer

- Zone réécrite à chaque cycle : `policy: churn`.
- Code ou invariant réel : `policy: blocking`.
- Référence orpheline : `PERTE`, bloquante.
- Live seul : `ABSENT_REF`, information.

Rejouer avec `--strict` pour vérifier que le churn devient bien `DERIVE` :

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/reimplementer-controle-integrite-lecture-seule/scripts/controle_integrite_lecture_seule.py" \
  --plan "C:/chemin/du/projet/plan_integrite.json" \
  --base "C:/chemin/du/projet" \
  --strict
```

### 5. Harnais hors installation

Le comparateur est livré avec un harnais qui crée son propre fixture :

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/reimplementer-controle-integrite-lecture-seule/scripts/harnais_lecture_seule.py"
```

Attendu : `RESULT PASS`, exit 0, tous les cas `A` à `L` passés, dont
`L_readonly_tree`, `L_no_pycache`, `K_cp1252`, la matrice des exits et la
précédence `PERTE` sur `DERIVE`.

### 6. Rejeu et clôture

Rejouer les commandes documentées, puis rapporter :

- la passe réelle (UTC, base, plan) ;
- les compteurs par zone et le résultat ;
- les invariants (`DERIVES`, `PERTES`) plutôt qu'un total figé ;
- les branches non testées, notamment `UNREADABLE` ;
- la décision CI : défaut non strict sur les zones churn, `--strict` seulement
  sur décision explicite.

## Contrat de sortie

| Sortie | Signification | Exit |
|---|---|---|
| `RESULT OK` | aucun écart | 0 |
| `RESULT CHURN N` | seuls des `DIFF` en zones `churn`, sans `--strict` | 0 |
| `RESULT PERTE N` | au moins un `ABSENT_LIVE`, toutes zones | 1 |
| `RESULT DERIVE N code=A churn=B` | `DIFF` bloquant, ou churn avec `--strict` | 1 |
| `RESULT ERROR unreadable=N` | au moins un fichier illisible | 2 |
| `RESULT USAGE ...` | plan, racine, journal explicite ou `--only` invalide | 2 |

Ligne globale :

```text
VERIFIES=342 SAME=227 NOUVEAUX=18 ECARTS=97 PERTES=0 DERIVES=0 CHURN=97 ILLISIBLES=0
```

Ligne de zone :

```text
ZONE=code POLICY=blocking VERIFIES=66 SAME=48 NOUVEAUX=18 DIFFS=0 PERTES=0 ILLISIBLES=0
```

Ligne de fichier :

```text
CLE=src/foo.py ETAT=DIFF ZONE=code SHA_LIVE=... SHA_REF=... MTIME_LIVE=... MTIME_REF=...
```

## Exemple de calibration observée

Cas Al-Mizan, 2026-10-27, passe générique vers `15:34Z` :

- défaut : `VERIFIES=342 SAME=227 NOUVEAUX=18 ECARTS=97 PERTES=0 DERIVES=0
  CHURN=97`, `RESULT CHURN 97`, exit 0 ;
- `--strict` : `VERIFIES=342 SAME=239 NOUVEAUX=0 ECARTS=103 PERTES=0
  DERIVES=0 CHURN=103`, `RESULT DERIVE 103 code=0 churn=103`, exit 1 ;
- code : 66 fichiers, 0 `DIFF`, 0 `PERTE` ; actes : 112 / 26 `DIFF` ;
  mémoire : 164 / 71 `DIFF` ;
- journal : 128 événements, 0 événement de code depuis `15:10Z` ;
- hash de l'arbre code identique avant/après.

Les compteurs diffèrent de la passe source (`125`) parce qu'un cycle concurrent
réécrit les données. C'est précisément pourquoi le rapport doit citer l'heure et
les invariants, pas un nombre figé.

## Pièges

- Importer le module audité déclenche ses effets de bord et crée un cache.
- `mtime` ne prouve rien : `shutil.copy2` préserve l'ancien timestamp.
- Un journal de 16 Mo ne se charge pas entièrement : lire la queue, ignorer la
  première ligne partielle et les lignes invalides.
- Une sortie non ASCII casse la console Windows ; utiliser l'émetteur ASCII.
- Un `exit 1` global sur les actes rend le garde inutile.
- Un fixture dans l'installation peut être détecté par le contrôle lui-même.
- Deux passes consécutives peuvent différer : comparer les invariants par zone.
- `ABSENT_LIVE` en zone churn reste une `PERTE` ; ne pas le reclasser.

## Modèle de rapport

```text
Contrôle de référence : <fichier> SHA-256 <hash>, <n> lignes
Plan : <chemin>, zones <liste>, policies <liste>
Passe : <UTC>, base <chemin>
Compteurs : VERIFIES=<n> SAME=<n> NOUVEAUX=<n> ECARTS=<n> PERTES=<n>
            DERIVES=<n> CHURN=<n> ILLISIBLES=<n>
Zones : code <...> ; actes <...> ; memoire <...>
Journal : EVENEMENTS=<n> CODE=<n> SINCE=<UTC>
Harnais : pass=<n> fail=0, read-only=<oui/non>, pycache=<aucun>
Décision : défaut exit=<0/1/2> ; --strict exit=<0/1/2>
Non testé : UNREADABLE, <autres branches>
```

## Ressources

- `scripts/controle_integrite_lecture_seule.py` : comparateur générique,
  lecture seule, sortie ASCII, plan JSON, journal en queue, exits 0/1/2.
- `scripts/harnais_lecture_seule.py` : fixture hors installation, matrice des
  exits, précédence, journal tronqué, preuve de non-écriture, absence de cache.
- `references/perimetre-et-calibrage.md` : extraction du périmètre, schéma du
  plan, table de décision, cas Al-Mizan et limites.
- Cas source détaillé : Skill `diagnostiquer-reversion-guerison-mizan`,
  fichiers `C:/Users/Administrateur/.qoder/skills/diagnostiquer-reversion-guerison-mizan/scripts/verifier_reversion.py`
  et `C:/Users/Administrateur/.qoder/skills/diagnostiquer-reversion-guerison-mizan/references/cas-2026-10-27.md`.
