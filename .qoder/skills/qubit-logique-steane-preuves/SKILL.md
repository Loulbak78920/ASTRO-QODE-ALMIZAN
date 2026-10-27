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

Maintenance de `scripts/auditer_livraison_qubit.py` :

- affecter puis appeler sur deux lignes : `SKILL_DIR=… py -3 "$SKILL_DIR/…"` s'étend
  avant l'affectation et échoue en `can't open file '…Git\scripts…'`, code 2 ;
- module chargé par chemin avec `@dataclass` : enregistrer `sys.modules[spec.name]`
  avant `exec_module`, sinon `AttributeError: 'NoneType' object has no attribute '__dict__'` ;
- conserver `sys.dont_write_bytecode = True` : l'audit ne crée aucun `__pycache__` ;
- n'émettre que de l'ASCII : une console cp1252 remplace `°` par `\ufffd` ;
- après édition : PASS réel, puis fixture à empreinte mutée → `RESULT FAIL (1/7)`, code 1.

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
| `AttributeError: 'NoneType' object has no attribute '__dict__'` | module `@dataclass` chargé par chemin sans `sys.modules` | `sys.modules[spec.name] = module` avant `exec_module` |
| `--help` affiche `\ufffd` au lieu de `°` | sortie non ASCII sous console cp1252 | libellés ASCII (`ASTRO-Q-ODE_SYSTEME`) |

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

## Ressources

- `references/preuves-et-pieges.md` — équations, valeurs exactes, preuves des pièges.
- `scripts/auditer_livraison_qubit.py` — audit lecture seule de la livraison.
- Projet : `docs/QUBIT_LOGIQUE.md`, `docs/API_PASSERELLE_VPS.md`,
  `docs/EXPLOITATION_VPS.md`.
