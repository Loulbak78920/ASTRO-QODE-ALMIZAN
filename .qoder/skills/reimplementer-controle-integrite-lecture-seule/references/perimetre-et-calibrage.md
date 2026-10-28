# Périmètre et calibration d'un contrôle d'intégrité en lecture seule

## 1. Objet et limites

Ce document accompagne `scripts/controle_integrite_lecture_seule.py`. Il sert à
reconstruire un contrôle interne (comparaison live vs copie de référence,
auto-guérison, garde de fichiers protégés) **sans importer le paquet audité** et
sans écrire dans le projet.

Limites à énoncer dans tout rapport :

- Le comparateur prouve l'**égalité structurelle** de fichiers (SHA-256), pas
  l'équivalence sémantique du contrôle d'origine.
- Les compteurs peuvent changer entre deux passes si un écrivain concurrent
  tourne (cycles de conscience, tests, sauvegarde automatique).
- Un fichier absent de la référence est une information (`ABSENT_REF`), pas une
  perte ; un fichier absent du live est une `PERTE` et prime sur tout le reste.
- La branche `UNREADABLE` n'est pas couverte par le harnais standard : elle
  demande un verrou ou une ACL Windows, à déclarer comme non testée.

## 2. Extraire le périmètre depuis la source

### 2.1 Chercher les invariants, pas les chemins de mémoire

Dans le module audité, inventorier :

- les constantes d'exclusion : `EXCLUDE_*`, `ZONES_STOP`, `PROTECTED`, `IGNORE`,
  noms de fichiers d'état et journaux auto-écrits ;
- les répertoires interdits ou non protégés (cache, journaux, inbox/outbox) ;
- les extensions réellement comparées (`.py`, `.json`, `.txt`, `.md`) ;
- les fonctions qui calculent la clé et le chemin : `_chemin_live`,
  `_chemin_copie`, `detecter_alterations`, `sauvegarder_soi` ;
- les replis de référence (par exemple un miroir secondaire pour les actes).

Ne pas déduire le périmètre d'un `find` global : les fichiers d'état changent à
chaque cycle et produiraient un faux positif permanent.

### 2.2 Cartographier live et référence

Pour chaque zone, noter :

- la racine live et la ou les racines de référence ;
- la clé relative utilisée par le contrôle (relative au module, au sous-dossier
  ou au nom de fichier) ;
- l'ordre des replis : la première référence existante gagne ;
- les exclusions par nom de répertoire et par motif de chemin.

Le piège vérifié en session : une clé `__init__.py` est relative à
`conscience_logique/`, pas à sa racine ; un `_chemin_copie` qui préfixe
`conscience_logique/` en trop renvoie `None` et transforme un fichier identique
en `ABSENT_COPIE`. Un second piège : le live d'une clé `actes/x.json` est sous
`<module>/conscience_logique/`, pas sous `<module>/`.

### 2.3 États et journal

Reproduire les états du contrôle : `SAME`, `DIFF`, `ABSENT_LIVE`, `ABSENT_REF`,
`UNREADABLE`. Pour le journal d'audit :

- ne lire que la queue (un journal peut dépasser 16 Mo) ;
- supprimer la première ligne si la fenêtre commence au milieu d'une ligne ;
- ignorer les lignes JSON invalides sans faire échouer le contrôle ;
- filtrer `phase` et `ok`, puis séparer les clés de code des clés de données ;
- comparer `--since` en lexicographique sur des dates UTC ISO.

### 2.4 Figer la preuve

Avant de citer une ligne de code ou un comportement :

- calculer le SHA-256 du fichier source et le nombre de lignes ;
- associer les numéros de ligne à ce hash exact ;
- si le hash change, relire le fichier au lieu de réutiliser les lignes ;
- noter l'heure UTC de la passe réelle et les compteurs observés.

## 3. Plan JSON

Le comparateur ne code aucun chemin de projet. Le plan décrit les zones :

```json
{
  "zones": [
    {
      "name": "code",
      "live_root": "src",
      "ref_roots": ["ref/src"],
      "include": ["**/*.py"],
      "exclude_dirs": ["__pycache__", ".git"],
      "exclude_globs": ["_verify_*.py"],
      "policy": "blocking"
    },
    {
      "name": "actes",
      "live_root": "src/actes",
      "ref_roots": ["ref/src/actes", "ref/objectifs_et_fil"],
      "include": ["*.json", "*.txt", "*.md"],
      "policy": "churn"
    }
  ],
  "journal": {
    "path": "src/actes/_journal.jsonl",
    "key_field": "cle",
    "phase_field": "phase",
    "phase_value": "guerison",
    "ok_field": "ok",
    "churn_prefixes": ["actes/", "memoire_aq/"]
  }
}
```

- `ref_roots` est une liste : les replis sont essayés dans l'ordre, la première
  référence existante pour une clé gagne.
- `include` vide signifie « tous les fichiers » ; `exclude_dirs` élague des noms
  de répertoires à tout niveau ; `exclude_globs` filtre le chemin relatif.
- `policy: blocking` transforme un `DIFF` en `DERIVE` (exit 1) ;
  `policy: churn` le transforme en `CHURN` (exit 0 par défaut).
- Un `ABSENT_LIVE` est une `PERTE` dans toutes les zones, y compris `churn`.

## 4. Calibrer sur données réelles

### 4.1 La première passe est une mesure

Lancer le comparateur sans `--strict` et lire les compteurs par zone. Ne pas
câbler le garde en CI à ce stade : un `exit 1` global sur un churn permanent est
un faux positif garanti.

### 4.2 Classer les zones par comportement observé

- Zone dont les fichiers changent à chaque cycle (timestamps réécrits, miroirs
  d'actes) : `churn`.
- Zone de code ou de configuration dont un `DIFF` signale une régression réelle :
  `blocking`.
- Fichier présent uniquement dans la référence : `PERTE`, toujours bloquante.
- Fichier présent uniquement dans le live : `ABSENT_REF`, information.

### 4.3 Table de décision

| Condition observée | Résultat | Exit |
|---|---|---|
| Au moins un `ABSENT_LIVE` | `PERTE` | 1 |
| Un `DIFF` en zone `blocking` | `DERIVE` | 1 |
| `DIFF` en zone `churn` avec `--strict` | `DERIVE` | 1 |
| `DIFF` en zone `churn` sans `--strict` | `CHURN` | 0 |
| Aucun écart | `OK` | 0 |
| Fichier illisible, plan ou racine invalide | `ERROR` / `USAGE` | 2 |

Précédence : `PERTE > DERIVE > CHURN > OK`. Un `ABSENT_LIVE` en zone `churn`
reste une `PERTE` ; il ne devient jamais un churn.

## 5. Harnais hors installation

Le harnais crée un fixture temporaire avec un plan minimal et exécute le
comparateur dans un processus enfant (`-B`, sans bytecode). Il vérifie :

| Cas | Attendu |
|---|---|
| Baseline | `RESULT OK`, exit 0 |
| Code `DIFF` | `RESULT DERIVE 1 code=1 churn=0`, exit 1 |
| Donnée `DIFF` | `RESULT CHURN 1`, exit 0 |
| Donnée `DIFF` + `--strict` | `RESULT DERIVE 1 code=0 churn=1`, exit 1 |
| Référence orpheline | `RESULT PERTE 1`, exit 1, prioritaire sur `DERIVE` |
| Fichier live seul | `ABSENT_REF` + `RESULT OK`, exit 0 |
| Journal tronqué et ligne invalide | seules les lignes valides sont comptées |
| `--journal` explicite absent | `RESULT USAGE`, exit 2 |
| Racine live ou référence absente | `RESULT USAGE`, exit 2 |
| Sortie sous `PYTHONIOENCODING=cp1252` | aucune `UnicodeEncodeError` |
| Arborescence du fixture | SHA-256 identique avant/après |
| Installation | aucun `__pycache__` ni `.pyc` |

Le fixture doit rester **hors** de l'installation et hors du projet audité :
un fixture placé dans l'arborescence peut être détecté par le contrôle lui-même
ou modifier le périmètre.

## 6. Cas Al-Mizan du 2026-10-27

### 6.1 Défauts trouvés par le harnais

À `15:19:22Z`, la première exécution du harnais de la session source donne
`FAIL A_same_3` : le comparateur ne retrouvait pas `__init__.py` identique. Les
deux causes sont la racine de clé et le chemin live de la zone code. Après
correction de `_chemin_copie` / `_chemin_live`, le harnais passe `17/17`, avec
`A_readonly_tree`, `A_reset_repertoire_interdit` et l'absence de `__pycache__`.

### 6.2 Calibration réelle

À `15:20:37Z`, la passe réelle sur Al-Mizan donne :

```
VERIFIES=342 SAME=217 NOUVEAUX=0 REVERSIONNABLES=125 CODE=0 ACTES=63 MEMOIRE=62
JOURNAL_GUERISONS=127 JOURNAL_CODE_GUERISONS=0 SINCE=2026-10-27T15:10:00Z
RESULT CHURN 125
EXIT=0
```

Les 125 écarts sont tous dans `actes/` et `memoire_aq/`, aucun dans le code.
C'est la justification du découpage par zone et de `--strict`.

### 6.3 Rejeu du contrôle générique

Le comparateur générique de ce Skill, avec un plan équivalent, a été exécuté en
lecture seule sur le même arbre le 2026-10-27 (passe vers `15:34Z`) :

- défaut : `VERIFIES=342 SAME=227 NOUVEAUX=18 ECARTS=97 PERTES=0 DERIVES=0
  CHURN=97 ILLISIBLES=0`, `RESULT CHURN 97`, exit 0 ;
- `--strict` : `VERIFIES=342 SAME=239 NOUVEAUX=0 ECARTS=103 PERTES=0 DERIVES=0
  CHURN=103`, `RESULT DERIVE 103 code=0 churn=103`, exit 1 ;
- journal : `JOURNAL_EVENEMENTS=128 JOURNAL_CODE_EVENEMENTS=0` depuis
  `2026-10-27T15:10:00Z` ;
- hash de l'arbre code avant/après :
  `ab19c6d57f8f9e8c6211ccbc89e1cfebbda50b09a6f09e174cfa96129a8ed6f1`
  (identique) ;
- zones : `code` 66 fichiers / 0 DIFF / 0 PERTE, `actes` 112 / 26 DIFF,
  `memoire` 164 / 71 DIFF.

Les compteurs diffèrent de 125 parce qu'un cycle concurrent réécrit les actes et
les miroirs entre les passes. L'invariant à retenir est `DERIVES=0`,
`PERTES=0`, `RESULT CHURN`, exit 0 par défaut ; le nombre 125 n'est pas une
constante.

### 6.4 Preuves sources

Fichiers cités, hash relevé le 2026-10-27 :

- `sauvegarde_soi.py` : 781 lignes, 25 671 octets,
  SHA-256 `b4f82c3defc8f197093ff5807da69e639bd36d209ee9947fccaf15a91676daa8`.
  Les ancres `sauvegarder_soi` 157, acte 187, copies 198-216, périmètre 445
  ne valent que pour ce hash.
- `verifier_reversion.py` : 317 lignes, 11 734 octets,
  SHA-256 `6ec3fa60631dfbeffaf23b4f89d048142bbfc5f89ce0712c6926ea82862cfdf2`.
- `SKILL.md` de `diagnostiquer-reversion-guerison-mizan` : 213 lignes,
  10 830 octets,
  SHA-256 `453c686480c1cc0e9416e21f97f8cd6747901fc2a696a406b33f99b5bc6a2cc5`.
- `cas-2026-10-27.md` (Skill `diagnostiquer-reversion-guerison-mizan`) :
  `86d9bfd1431bd9aad63c4251d0231965e395c3001dd13af6e1b4fe4c22b56808`.
- `mecanisme-a232.md` (même Skill) :
  `6fe1e08c0985607372d34ddd23d1c356cebbd540e1d1a2ee02e6cd24225c0c2c`.

Le validateur `skill-file-qa` de la session source a rendu `PASS 9/0/0` à
`15:23:07Z` ; le rejeu des commandes documentées a rendu `RESULT CHURN 125` et
`EXIT=0` à `15:23:14Z`.

## 7. Pièges

- **Importer le paquet audité** déclenche ses effets de bord et crée
  `__pycache__`. Le comparateur doit rester un script stdlib autonome.
- **mtime** n'est pas une preuve : `shutil.copy2` préserve l'ancien mtime ; un
  fichier restauré peut paraître plus ancien que l'édition perdue.
- **Journal** : le charger entièrement peut coûter 16 Mo et plus ; lire la queue,
  ignorer la première ligne partielle et les lignes invalides.
- **cp1252** : toute sortie non ASCII casse la console Windows ; utiliser
  l'émetteur ASCII ou `PYTHONIOENCODING`.
- **Churn permanent** : un `exit 1` global sur les actes rend le garde inutile ;
  mesurer, classer, puis calibrer.
- **Concurrence** : deux passes consécutives peuvent donner des compteurs
  différents ; comparer les invariants par zone, pas seulement le total.
- **Fixture dans l'installation** : il peut être détecté par le contrôle ou
  modifier le périmètre ; le créer dans un répertoire temporaire.
- **`ABSENT_LIVE` en zone churn** : reste une `PERTE` ; ne pas le reclasser en
  churn pour faire passer le garde.

## 8. Checklist avant câblage CI

- [ ] Le plan JSON couvre toutes les zones protégées et exclut journaux/états.
- [ ] Une passe réelle a été exécutée en lecture seule, avec heure UTC et
  compteurs par zone.
- [ ] Les zones à churn permanent sont en `policy: churn` ; le code est
  `blocking`.
- [ ] `PERTE`, `DERIVE`, `CHURN`, `OK` et les exits 0/1/2 sont couverts par le
  harnais hors installation.
- [ ] L'arborescence du fixture est identique avant/après ; aucun `__pycache__`.
- [ ] La commande CI par défaut n'utilise pas `--strict` sur une zone churn,
  sauf décision explicite documentée.
- [ ] Le rapport indique ce qui est observé, déduit, et non testé.
