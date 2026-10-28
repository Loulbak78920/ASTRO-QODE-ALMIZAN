---
name: qubit-logique-steane-preuves
description: "Construire, prouver, régénérer et exposer le qubit logique Steane [[7,1,3]] d'IMAM8MAHDI (AL-MIZAN x ASTRO-Q°ODE) : vérifier stabilisateurs, distance, Knill-Laflamme (211 Pauli) et 21 corrections, recalculer les taux exacts et le Monte Carlo, auditer le budget DAC/horloge/CMOS, régénérer les artefacts JSON/MD/CSV/SVG, contrôler l'API read-only avec 404 honnête et la page /qubit-logique. Utiliser pour rejouer qubit_logique_mizan.py --verifier/--rapport, expliquer QUBIT_LOGIQUE.md, corriger la page ou auditer resume.json ; déclencheurs 逻辑量子比特, Steane 码, [[7,1,3]] 验证, qubit logique."
---

# Qubit logique Steane `[[7,1,3]]` — preuves et livraison

## Portée

Rejouer, auditer et livrer l'objet **logiciel** `[[7,1,3]]` du projet IMAM8MAHDI :
énumération exacte du code, preuves calculées, taux d'erreur exacts, budget matériel
paramétré, artefacts, API et page publique.

Utiliser cette skill pour :

- rejouer `qubit_logique_mizan.py --verifier` et retrouver les valeurs de référence ;
- auditer un `resume.json`, sa fraîcheur et les artefacts livrés ;
- expliquer ou corriger `docs/QUBIT_LOGIQUE.md`, la page `/qubit-logique` ou l'API ;
- régénérer les artefacts avant une archive de déploiement.

Ne pas l'utiliser pour : une mesure physique, un seuil de code de surface simulé,
un contrat de jeton, ou une revue par les pairs (hors périmètre logiciel).

## Racine et fichiers

```bash
SYSTEME="${MIZAN_SYSTEME:-C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME}"
cd "$SYSTEME"
```

Sous Windows FR, utiliser `py -3` : `python` peut être l'alias Microsoft Store
(échec code 49).

| Fichier | Rôle |
| :--- | :--- |
| `qubit_logique_mizan.py` | Module de preuve, simulation exacte, budget, génération |
| `resultats/qubit_logique/` | 11 artefacts : `resume.json`, rapport MD, 7 CSV, 2 SVG |
| `tests/test_qubit_logique_mizan.py` | 26 tests des preuves et du modèle |
| `tests/test_qubit_http_mizan.py` | 3 tests page/API |
| `passerelle_api_vps_mizan.py` | Routes `/qubit-logique` et `/api/v1/qubit_logique` |
| `web_cloud/qubit_logique.html` | Page publique autonome (CSS/JS inline) |
| `docs/QUBIT_LOGIQUE.md` | Documentation de référence du livrable |

## Procédure

### 1 — Rejouer les preuves

```bash
py -3 qubit_logique_mizan.py --verifier
```

Attendu, code retour 0 :

```text
PASS
distance=3 poids_min=3 paulis=211 corrections=21 seuil=0.081082
```

En cas de `FAIL`, diagnostiquer avec le tableau des pièges. Ne jamais affaiblir une
assertion, une tolérance ou un décompte pour faire passer la commande.

### 2 — Rejouer les tests

```bash
py -3 -m unittest tests.test_qubit_logique_mizan -v
py -3 -m unittest tests.test_qubit_http_mizan -v
```

Attendu : 26 tests `OK`, puis 3 tests `OK`. Les tests HTTP démarrent un serveur local
sur un port éphémère et le referment.

### 3 — Auditer la livraison et la fraîcheur

```bash
SKILL_DIR="${SKILL_DIR:-C:/Users/Administrateur/.qoder/skills/qubit-logique-steane-preuves}"
py -3 "$SKILL_DIR/scripts/auditer_livraison_qubit.py" --racine "$SYSTEME"
```

`SKILL_DIR` peut être remplacé par le chemin « Base directory for this skill » si la
skill est installée ailleurs.

Le script est **lecture seule**. Il recalcule les preuves, compare
`resume.json.source.sha256` au module courant, vérifie les 11 artefacts, la page, les
routes et le sitemap. Attendu : `RESULT PASS`.

Si l'empreinte diverge, le module a changé après la génération : annoncer l'écriture
puis régénérer.

```bash
py -3 qubit_logique_mizan.py --rapport
```

`--rapport` écrit les 11 artefacts et réenregistre l'empreinte. Le relancer avant toute
archive. Ne jamais éditer un artefact à la main ni figer l'empreinte dans un document.

### 4 — Modifier sans affaiblir la preuve

Invariants à conserver (détail mathématique : `references/preuves-et-pieges.md`) :

- `ESPACE_C` = noyau de `H` (16 mots), `ESPACE_DUAL` = lignes de `H` (8),
  opérateurs logiques = `C \ C⊥` (8), poids de `C` = `{0,3,4,7}`, distance 3 ;
- Knill–Laflamme sur **211** Pauli de poids ≤ 2, via `P E P` proportionnelle à `P` ;
- opérateurs logiques vérifiés par `P·X_L·P = σ_x` et `P·Z_L·P = σ_z` ;
- correction exhaustive des **21** Pauli de poids 1 ; échecs dès le poids 2 ;
- taux exact par énumération des **16 384** motifs, jamais par échantillonnage seul ;
- Monte Carlo reproductible (graine `20261027`, 200 000 échantillons) recoupé par
  l'intervalle de confiance qui **contient** le taux exact.

Toute modification du module impose : relancer `--verifier`, les deux suites de tests,
puis `--rapport`, puis l'audit. Mettre à jour `docs/QUBIT_LOGIQUE.md` et les tests dans
le même changement.

### 5 — Exposer sans surpromettre

| Élément | Valeur |
| :--- | :--- |
| Page | `/qubit-logique` (alias `/qubit_logique`, `/qubit`) |
| API | `GET /api/v1/qubit_logique` (alias `/api/v1/qubit-logique`, `/api/v1/qubit`) |
| Source API | `resultats/qubit_logique/resume.json`, relu à chaque requête |

L'API est en lecture seule. Si l'artefact manque, elle répond **404** avec la commande
`py -3 qubit_logique_mizan.py --rapport`. La page doit conserver ses équations même si
l'API échoue, et afficher le préfixe de l'empreinte reçue.

Vérification locale (serveur déjà lancé) :

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8095/qubit-logique
curl -s http://127.0.0.1:8095/api/v1/qubit_logique | head -c 200
```

La page utilise des noms de champs contenant `1e-4` : accès **entre crochets** uniquement
(`materiel["gigue_requise_pour_1e-4_s"]`). Un contrôle syntaxique Node doit ignorer les
blocs `type="application/ld+json"`.

### 6 — Livrer (uniquement sur autorisation explicite)

1. Régénérer : `--verifier` puis `--rapport`.
2. Auditer : script d'audit, attendu `RESULT PASS`.
3. Archiver les fichiers modifiés seulement ; exclure `__pycache__`, `*.pyc`, `secrets/`
   et `memoire_aq/almizan_comptes.sqlite3`.
4. Inclure au minimum : module, page, portail, `sitemap.xml`, `resume.json`, rapport,
   CSV et SVG.
5. Après déploiement : page 200, API `succes: true`, alias et 404 vérifiés.

Cette skill ne déploie rien d'elle-même.

### 7 — Valider le paquet lui-même

```bash
SKILL_DIR="${SKILL_DIR:-C:/Users/Administrateur/.qoder/skills/qubit-logique-steane-preuves}"
QA_DIR="${QA_DIR:-C:/Users/Administrateur/.qoder/skills/skill-file-qa}"
py -3 "$QA_DIR/scripts/validate_skill.py" "$SKILL_DIR" --workspace "$SYSTEME"
```

Attendu : `Summary: 9 pass, 0 fail, 0 warn`, `RESULT PASS`, code 0. Le `--workspace`
doit désigner `ASTRO-Q°ODE_SYSTEME`, racine des références `docs/`, `resultats/`,
`tests/` et `web_cloud/` ; avec la racine du dépôt, ces 7 références échouent.

Les 11 références locales comptées sont **9 fichiers + `references/` + `scripts/`** ;
`docs/`, `resultats/`, `tests/` et `web_cloud/` ne sont comptées qu'à travers leurs
fichiers (ni préfixe ressource ni extension).

#### Prouver que le `PASS` n'est pas vide

Rejouer les quatre cas depuis `$SYSTEME` : A doit passer, B–D doivent échouer avec
le message indiqué. Un `PASS` qui ne se laisse pas mettre en défaut ne prouve rien.

| Cas | Variante | Attendu |
| :--- | :--- | :--- |
| A | `--workspace "$SYSTEME"` | `9 pass, 0 fail, 0 warn`, `RESULT PASS`, rc 0 |
| B | `--workspace` = racine `IMAM8MAHDI` | `8 pass, 7 fail`, rc 1 ; 7 × `FAIL local reference not found` |
| C | copie temporaire + marqueur de tâche non résolu (convention `TODO`, en début de ligne) | `8 pass, 1 fail` : `FAIL content: 1 unresolved TODO marker(s)`, rc 1 |
| D | copie temporaire, une occurrence de `references/preuves-et-pieges.md` remplacée par un fichier absent | `8 pass, 1 fail` : `FAIL local reference not found: 'references/absent-fixture.md'`, rc 1 |

```bash
BASE="${QA_NEG_DIR:-C:/Users/Administrateur/.qoder/tmp/qa-neg-probe}"
for c in todo ref; do
  mkdir -p "$BASE/$c/qubit-logique-steane-preuves"
  cp -R "$SKILL_DIR/." "$BASE/$c/qubit-logique-steane-preuves/"
done
```

Conserver le nom de dossier `qubit-logique-steane-preuves` dans les copies : un
répertoire renommé fait échouer le contrôle `name`. Éviter `~/.qoder/skills/`, où la
copie serait vue comme une skill installée. Après C et D : `rm -rf "$BASE"`,
revérifier les trois SHA-256 et `find . -name '__pycache__' -o -name '*.pyc'` → `0`.

#### Écrire seulement si la mise à jour n'est pas déjà appliquée

Une autre session peut avoir appliqué la modification pendant la planification.
Avant toute écriture :

1. Double-échantillonner `SKILL.md`, `references/` et `scripts/` (taille, mtime,
   SHA-256 à 5 s d'intervalle) et relire le contenu courant, jamais un souvenir.
2. Lire l'état de la session source avec `read_chat_session` : `runtimeState: running`
   ou `activeTurnId` non nul impose zéro écriture ; attendre la fin du tour.
3. Mapper chaque modification prévue en `CURRENT`, `ALREADY_APPLIED`, `PARTIAL` ou
   `ABSENT`, avec une ancre exacte (`fichier:ligne`).
4. Tout `ALREADY_APPLIED` : ne rien réécrire, exécuter seulement la validation et
   `Prouver la version chargée` ; une seconde copie du même paragraphe est un défaut.
5. `PARTIAL`/`ABSENT` : si l'empreinte diffère de la dernière lecture, relocaliser
   l'ancre sur le contenu courant avant l'`Edit`, puis vérifier après écriture que le
   paragraphe n'est pas dupliqué et que l'empreinte a changé.
6. Vérifier dans le JSONL de la session nommée les assertions du rationale sur un
   échec d'outil ou une absence d'écriture : compter les `tool_use` `Write`/`Edit`
   et les `tool_result` en erreur. Un échec réel d'une session concurrente ne
   s'attribue pas à la session source citée ; une session sans `Edit` ne peut pas
   en avoir vu un échouer. Ne pas recopier une cause non vérifiée dans le paquet.
7. Une sortie `read_chat_session` volumineuse est persistée dans un fichier : ne pas
   l'imprimer directement sous cp1252 (`UnicodeEncodeError: 'charmap' ...`). La lire
   avec `PYTHONIOENCODING=utf-8` et n'afficher que de l'ASCII (`ascii()` ou
   `ensure_ascii=True`) ; analyser le fichier persisté, jamais l'aperçu tronqué.

Méthode complète : `adopt-source-session-update` (adoption d'une mise à jour source)
et `skill-update-concurrency-safe` (écriture concurrente).

Maintenance de `scripts/auditer_livraison_qubit.py` :

- affecter puis appeler sur deux lignes : `SKILL_DIR=… py -3 "$SKILL_DIR/…"` s'étend
  avant l'affectation et échoue en `can't open file '…Git\scripts…'`, code 2 ;
- module à annotations différées (`from __future__ import annotations`) chargé par
  chemin : enregistrer `sys.modules[spec.name]` avant `exec_module`, sinon
  `AttributeError: 'NoneType' object has no attribute '__dict__'` ;
- conserver `sys.dont_write_bytecode = True` : l'audit ne crée aucun `__pycache__` ;
- n'émettre que de l'ASCII : une console cp1252 remplace `°` par `\ufffd` ;
- après édition : PASS réel, puis fixture à empreinte mutée → `RESULT FAIL (1/7)`, code 1.

Méthode complète — contrat de sortie 0/1/2, trois contrôles négatifs obligatoires,
socle réutilisable : `auditer-livraison-skill-module-projet`.

#### Prouver la version chargée

L'agent ne peut pas exécuter `/skills reload` : ne pas demander à l'utilisateur de le faire.
Après toute modification du paquet, prouver la liaison par une invocation en lecture seule.

1. Relever `sha256sum SKILL.md` avant d'écrire, puis après l'écriture.
2. Invoquer cette skill avec l'outil Skill. Le résultat de l'outil se limite à
   `Launching skill: qubit-logique-steane-preuves`, sans chemin : la preuve est dans le
   message injecté, dont la première ligne annonce `Base directory for this skill:`
   suivie du répertoire cible, et dont le corps contient un marqueur unique ajouté par la
   modification (titre ou ligne de checklist), relu sur disque.
3. Après l'appel : SHA-256 inchangé et `find . -name '__pycache__' -o -name '*.pyc' | wc -l`
   vaut `0`.

Si le marqueur manque alors que le disque est à jour, l'invocation a servi une version
périmée : consigner `UNVERIFIED`, ne pas annoncer un rechargement réussi. Méthode
complète : `verify-skill-runtime-binding` et `verify-injected-skill-body-freshness`.

## Pièges vérifiés

| Symptôme | Cause | Correction |
| :--- | :--- | :--- |
| `FAIL` alors que distance/Pauli/corrections semblent bons | opérateurs logiques comparés par produits scalaires sur un même état | comparer les matrices `P·X_L·P` à `σ_x` et `P·Z_L·P` à `σ_z` |
| `AttributeError: 'tuple' object has no attribute 'isdisjoint'` | `ESPACE_C` est un tuple | envelopper dans `set()` avant `isdisjoint`/`issubset` |
| confusion « poids 7 » / `0b0000111` | l'entier 7 n'est pas le poids de Hamming | `0b0000111` a le poids **3** ; `X_L = Z^⊗7` a le poids 7 |
| `SyntaxError: Numeric separators ...` | `materiel.gigue_requise_pour_1e-4_s` | accès crochet : `materiel["gigue_requise_pour_1e-4_s"]` |
| `SyntaxError: Unexpected token ':'` au contrôle Node | script JSON-LD inclus dans l'extraction | ne garder que les scripts JavaScript exécutables |
| `KeyError: 'preuves'` ou `'n'` | schéma `resume.json` supposé | clés réelles : `source`, `statut`, `code`, `resultats`, `materiel`, `surface`, `limites` |
| test de ratio `p²` échoue | tolérance relative au lieu d'absolue | `taux/(p²)` comparé à `C` avec `delta=0.02` à `p=1e-4` |
| tests de monotonie inversés | sens des relations | DAC ↑ quand la cible se resserre ; gigue ↓ ; décohérence ↑ avec `t_g` |
| page bloquée sur « Chargement… » | API 404 ou erreur JS | vérifier `resume.json`, syntaxe JS, accès crochets |
| `Edit` sans occurrence dans `docs/` | accents, CRLF ou texte déplacé | relire la zone exacte avant d'éditer |
| `validate_skill.py` : 7 « local reference not found » | `--workspace` par défaut = cwd ; références relatives à `ASTRO-Q°ODE_SYSTEME` | `--workspace "$SYSTEME"` → 9 pass, 0 fail |
| `can't open file '…\Git\scripts\auditer_livraison_qubit.py'`, code 2 | `SKILL_DIR=…` affecté sur la ligne de l'appel | deux lignes : affecter, puis appeler |
| `AttributeError: 'NoneType' object has no attribute '__dict__'` | module à annotations différées chargé par chemin sans `sys.modules` ; `@dataclass` seul ne suffit pas | `sys.modules[spec.name] = module` avant `exec_module` |
| `--help` affiche `\ufffd` au lieu de `°` | sortie non ASCII sous console cp1252 | libellés ASCII (`ASTRO-Q-ODE_SYSTEME`) |
| `Launching skill: …` renvoyé seul, sans chemin | le résultat de l'outil ne porte pas le répertoire résolu | lire le message injecté : première ligne `Base directory for this skill: …` plus marqueur du corps |
| `UnicodeEncodeError: 'charmap' codec can't encode ...` en lisant une session | sortie `read_chat_session` accentuée imprimée sous cp1252 | lire le fichier persisté avec `PYTHONIOENCODING=utf-8` ; n'imprimer que `ascii()` / `ensure_ascii=True` |

## Honnêteté (obligatoire)

| Élément | Statut à publier |
| :--- | :--- |
| Code, preuves, décodeur | **Opérationnel** (logiciel, calcul exact) |
| Taux d'erreur | **Simulé exactement** pour le modèle de capacité de code |
| DAC, horloge, bruit 1/f, CMOS | **Modèle d'ingénierie** paramétré, non mesuré |
| Qubit physique | **Non réalisé** : aucun QPU, cryostat ni capteur |
| Reconnaissance par les pairs | **Non acquise** : revue externe requise |

Ne jamais présenter la projection de surface comme une simulation, ni une empreinte
comme une preuve d'exécution indépendante.

## Checklist de fin

- [ ] `--verifier` : `PASS`, code 0, ligne de métriques conforme
- [ ] 26 tests unitaires et 3 tests HTTP verts
- [ ] script d'audit : `RESULT PASS`
- [ ] `resume.json.source.sha256` = SHA-256 du module courant
- [ ] 11 artefacts présents et non vides
- [ ] page 200, API 200, alias, 404 honnête sans artefact
- [ ] libellés opérationnel / simulé / spécifié conservés
- [ ] aucune empreinte figée dans la documentation
- [ ] paquet : `validate_skill.py --workspace "$SYSTEME"` → `RESULT PASS`
- [ ] preuve non vide : B → 7 `FAIL`, C/D → 1 `FAIL` ; SHA-256 inchangés, 0 résidu `qa-neg-*`, 0 cache
- [ ] après édition du paquet : invocation en lecture seule → `Base directory` = répertoire cible, marqueur présent, SHA-256 inchangé, 0 cache

## Ressources

- `references/preuves-et-pieges.md` — équations, valeurs exactes, preuves des pièges.
- `scripts/auditer_livraison_qubit.py` — audit lecture seule de la livraison.
- Projet : `docs/QUBIT_LOGIQUE.md`, `docs/API_PASSERELLE_VPS.md`,
  `docs/EXPLOITATION_VPS.md`.
