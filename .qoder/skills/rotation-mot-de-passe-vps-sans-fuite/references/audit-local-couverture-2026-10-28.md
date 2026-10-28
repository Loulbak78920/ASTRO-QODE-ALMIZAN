# Couverture réelle de l'audit local `auditer_secrets_locaux.py` (2026-10-28)

Objet : `RESULT OK` ne signifie pas « aucun secret nulle part ». Il signifie « aucune occurrence **exacte** de `mot_de_passe_ssh` dans les **N** fichiers que le script a bien voulu lire, et pas de `<secrets>.tmp` à côté du JSON ». Ce document fixe la portée exacte, avec les sorties observées.

Version auditée : 6 555 octets, SHA-256 `128f1695961670110dc98d016ecc35bf311b2c884ebfe1eb0aa652caff1584a9` (données de §4 et §5 produites avec ces mêmes octets).

## 1. Ce que chaque ligne de sortie prouve

| Ligne | Signification | Effet sur rc |
|---|---|---|
| `FICHIER json=ok` | JSON lisible et objet | 1 si illisible/non-objet |
| `CLES manquantes=…` | `hote`, `user`, `mot_de_passe_ssh` non vides | 1 si manquante |
| `TEMPORAIRE non_vide=oui` | `mot_de_passe_temporaire` non vide | **aucun** (AVERTISSEMENT) |
| `PERMANENT coherent=non` | `mot_de_passe_permanent` ≠ `mot_de_passe_ssh` | **aucun** (AVERTISSEMENT) |
| `RESIDU tmp=…` | seul `<fichier de secrets>.tmp` existe | 1 |
| `SCAN racine=ok fichiers=N` | N fichiers retenus par le filtre de §2 | aucun |
| `FUITE total=…` | occurrences exactes de `mot_de_passe_ssh` | 1 si > 0 |
| `ANTIPATTERN total=…` | lignes contenant `sudo -S` ou `bash -s` | **aucun**, jamais |

`PERMANENT coherent=oui` est aussi imprimé quand `mot_de_passe_permanent` est **absent** (clé non requise) : ce n'est pas une preuve de cohérence.

## 2. Périmètre : ce qui n'est jamais lu

Constats de lecture de code ; le §3 rejoue ceux qui portent sur le périmètre de fichiers et l'encodage, et le §7 indique ce qui reste INFERRED.

| Limite | Code | Conséquence |
|---|---|---|
| Liste blanche d'extensions (+ noms `.env*`) | `EXTENSIONS`, l. 23-27 | `.log`, `.csv`, `.xml`, `.sql`, `.dist`, fichier sans extension : jamais lus |
| 7 dossiers ignorés | `DOSSIERS_IGNORES`, l. 22 | `.git`, `__pycache__`, `node_modules`, `.venv`, `venv`, `.qoder`, `.mypy_cache` : jamais lus |
| Taille ≤ 2 000 000 octets | `TAILLE_MAX_FICHIER`, l. 21 ; `_est_analyse`, l. 34-42 | fichier plus gros ignoré, **sans compteur** |
| Une seule valeur recherchée : `mot_de_passe_ssh` | l. 89 | une fuite de `mot_de_passe_permanent` ou du temporaire n'est pas signalée |
| Décodage `utf-8` avec `errors="ignore"` | l. 125 | fichier UTF-16/UTF-32 : contenu illisible, fuite non détectée |
| Un seul nom de temporaire : `<secrets>.tmp` | l. 105 | `.swp`, `.bak` du JSON, `~` : non contrôlés comme résidus |
| Anti-modèles limités à `sudo -S` et `bash -s` | `MOTIFS_ANTIPATTERN`, l. 28-31 | `echo <mdp>`, `passwd` interactif, secret en argv : non signalés |
| Aucun contrôle d'ACL, de permissions, de `gitignore`, ni hors de `--racine` | (absent du code) | ne pas présenter `RESULT OK` comme preuve de confinement |

Non détectés aussi : secret transformé (URL-encodé, base64, JSON échappé), secret tronqué, secret dans un fichier binaire, secret hors de la racine.

## 3. Fixtures jetables du 2026-10-28 (verbatim, secret factice)

Racine `…\.qoder\tmp\rota-borne-20261028`, secrets `secrets\ovh.json`, `--racine` = racine du fixture. Secret factice remplacé par `<secret>` ; `secret_in_output=False` pour les cinq cas.

**A. Contrôle positif** — `notes.md` contient le secret, rc=1 :

```text
SCAN racine=ok fichiers=1
FUITE total=1
  FUITE notes.md:2
ANTIPATTERN total=0
FAIL secret hors du fichier de secrets: 1 occurrence(s)
RESULT FAIL
```

**B. Trois copies du secret, aucune vue** — `journal.log`, `gros.py` (2 099 999 octets) et `node_modules\mod.py` contiennent le secret, rc=0 :

```text
SCAN racine=ok fichiers=0
FUITE total=0
ANTIPATTERN total=0
RESULT OK
```

C'est la démonstration centrale : `fichiers=0` + `RESULT OK` avec trois copies du secret sur disque.

**C. `.py` normal** — `petit.py`, rc=1 : `SCAN … fichiers=1`, `FUITE total=1`, `FUITE petit.py:2`, `RESULT FAIL`.

**D. Résidu** — `secrets\ovh.json.tmp` présent, rc=1 : `RESIDU tmp=ovh.json.tmp` puis `FAIL residu .tmp: ovh.json.tmp`.

**E. Encodage** — `enc.py` en UTF-16 contenant le secret, rc=0 : `SCAN … fichiers=1`, `FUITE total=0`, `RESULT OK`.

Fixture supprimée après les cinq exécutions ; aucune sortie n'a contenu le secret.

## 4. Premier run réel (projet `ASTRO-Q°ODE_SYSTEME`)

Exécuté le 2026-10-28 avec les octets de la version auditée, racine `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME` :

```text
SCAN racine=ok fichiers=698
FUITE total=0
ANTIPATTERN total=46
  ANTIPATTERN deploiement_vps\deploiement_automatique_ovh.py:106 sudo -S
  ANTIPATTERN ... tronque (26 de plus)
RESULT OK
AUDIT_RC=0
```

Lecture correcte : 698 fichiers éligibles lus, aucune occurrence exacte du secret, 46 lignes d'anti-modèles (les 20 affichées sont toutes `sudo -S` ; les 26 masquées n'ont pas été inspectées) — un passif de scripts de déploiement existants, pas une fuite. Les 46 ne changent pas le rc.

## 5. L'incident de la version initiale (même jour)

La première version comparait les composants **absolus** (`chemin.parts`) à `DOSSIERS_IGNORES` (`_fichiers`, l. 45-58). Un fixture créé sous `…\.qoder\tmp\…` contenait donc `.qoder` dans son chemin : tous les fichiers étaient ignorés. Le harnais affichait `ECHECS 6`, et chaque cas fautif montrait `SCAN racine=ok fichiers=0` suivi de `RESULT OK`.

Correction : comparaison sur `chemin.relative_to(racine).parts[:-1]`. Après correction, le harnais rend `ECHECS 0` / `HARNESS_RC=0` ; `.bak`, `.old`, `.orig`, `.save` ont été ajoutés aux extensions analysées. La leçon reste valable même après correction : **`fichiers=0` n'est jamais un succès** (cf. §3-B).

## 6. Mode d'emploi de la sortie

1. Lire `fichiers=N` avant tout : `N=0` → arrêter, la racine ou le projet est hors périmètre.
2. `FUITE total=0` ne couvre que §2 ; pour un doute hors périmètre (`.log`, gros fichier, autre nom), faire un `grep -F` ciblé plutôt que conclure.
3. `ANTIPATTERN` est une liste de migration (`sudo -n`), pas un critère de réussite.
4. Toujours associer l'audit local aux contrôles distants de §2.5 du SKILL.md : le refus de l'ancien mot de passe et la connexion par clé ne sont pas observables ici.

## 7. Classement des affirmations

| Affirmation | Niveau |
|---|---|
| 698 fichiers, 0 fuite, 46 anti-modèles, rc 0 | REPRODUCED (sortie verbatim, version auditée) |
| Trois fuites invisibles avec `fichiers=0` et `RESULT OK` | REPRODUCED (§3-B) |
| `.log`/gros fichier/dossier ignoré hors périmètre | REPRODUCED (§3-B) |
| UTF-16 non détecté | REPRODUCED (§3-E) |
| Seul `mot_de_passe_ssh` est recherché ; un seul nom de `.tmp` ; ACL et `gitignore` non contrôlés | INFERRED (lecture du code, non exercé isolément) |
| Bug des composants absolus et sa correction | REPRODUCED (JSONL de la session de création + harnais `ECHECS 0`) |
