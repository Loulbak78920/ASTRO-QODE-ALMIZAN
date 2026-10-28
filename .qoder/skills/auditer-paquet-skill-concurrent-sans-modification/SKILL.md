---
name: auditer-paquet-skill-concurrent-sans-modification
description: "Audit en lecture seule d'un paquet Skill écrit par une autre session, qu'on ne doit pas modifier : inventaire size/mtime_ns/SHA-256, détection d'une réécriture pendant l'audit avec relecture de la dernière version et liaison de chaque constat à son empreinte (le PASS de skill-file-qa ne couvre que SKILL.md), recoupement des affirmations du paquet avec les preuves brutes (SHA-256 complet recalculé contre un préfixe cité, ligne de documentation, ligne d'incident dans le JSONL source caviardée), exercice du script sur une fixture jetable hors Skill avec un faux secret jamais affiché, preuve d'absence d'écriture et de __pycache__, correction de l'assertion fautive du harnais plutôt que du script audité, rejeu de skill-file-qa, rapport couverture et limites, confirmation que la cible non créée reste absente. Utiliser quand un paquet concurrent apparaît, quand l'utilisateur choisit de le conserver, ou quand un fichier change pendant l'audit. 中文触发：并发 Skill 只读审计、包在审计中被改写、论断与原始证据对账、一次性夹具契约测试、修正测试而非被测脚本。"
---

# Auditer un paquet Skill concurrent sans le modifier

## Quand l'utiliser

- Un paquet Skill écrit par une autre session apparaît et la création du vôtre est suspendue parce que l'utilisateur a choisi de le conserver.
- Un fichier du paquet change pendant que vous l'auditez.
- Le PASS de `skill-file-qa` ne suffit pas : il faut recouper les affirmations du paquet avec des preuves brutes et exercer son script.
- Il faut prouver qu'aucune écriture n'a eu lieu sous les racines de Skills et qu'aucun secret n'a été affiché.

## Quand ne pas l'utiliser

| Besoin | Skill à utiliser |
| --- | --- |
| Décider garder, reprendre ou scinder un doublon concurrent | `adopt-concurrent-duplicate-skill` |
| Prouver qu'un écrivain est encore actif, attendre le silence | `audit-skill-during-live-creation` |
| Reconstruire un paquet après PASS, dérive multi-fichiers, harnais, rejeu | `verifier-reecriture-concurrente-paquet-skill` |
| Extraire les preuves d'une session source | `audit-session-evidence` |
| Vérifier une citation `fichier:ligne` | `verifier-citations-lignes-skill` |
| Auditer les effets de bord d'une vérification « lecture seule » | `verifier-effets-de-bord-verification-lecture-seule` |
| Auditer le contrat d'un outil avant de le réutiliser | `audit-skill-tool-contracts` |
| Intégrité du paquet, caches, manifeste | `skill-package-integrity-audit` |

## Invariants non négociables

1. **Zéro écriture sous les racines de Skills.** Les fixtures et sorties temporaires vivent dans `%TEMP%` ou `.qoder/tmp/<SESSION>/`, jamais dans le paquet audité ni dans un autre Skill.
2. **Faux secrets uniquement** (`FAKE_SECRET_...`). Toute ligne source citée est caviardée en `<secret>` ; ne jamais afficher, journaliser ni recopier un secret réel.
3. **Chaque constat est lié à une empreinte complète** : `size`, `mtime_ns` et SHA-256 entier du fichier concerné. Un préfixe ou un horodatage seul ne suffit pas.
4. **Un PASS ne fige rien.** `skill-file-qa` ne scelle que `SKILL.md` ; les autres fichiers peuvent changer. Tout paquet non silencieux donne des constats `PROVISOIRE`, jamais `FINAL`.
5. **Ne jamais modifier le paquet audité pour faire passer un test.** En cas d'échec, trier `BUG_HARNAIS` contre `BUG_SCRIPT` avec `repr(stdout)` avant toute décision. Si l'utilisateur autorise une correction, l'audit s'arrête et devient une mise à jour.
6. **Aucune conclusion finale** tant qu'un écrivain peut être actif.
7. **Ne pas supprimer les résidus étrangers** (`__pycache__`, fixtures imbriquées, `.tmp`) : les signaler, supprimer seulement les vôtres.

## Procédure

### 0. Figer la cible et la session

- Vérifier l'absence de la cible avant tout `mkdir`, aux deux racines. Si elle existe : ne pas écraser, basculer vers le flux de mise à jour de `skill-creator` ou vous arrêter selon `adopt-concurrent-duplicate-skill`.
- Noter l'identifiant de session, la session source, le chemin absolu du paquet, et annoncer `MODE=LECTURE SEULE`.

```bash
PKG="$HOME/.qoder/skills/<nom>"
PROJ="$PWD/.qoder/skills/<nom>"
[ -e "$PKG" ] && echo "CIBLE PRESENTE" || echo "CIBLE ABSENTE"
[ -e "$PROJ" ] && echo "PROJET PRESENT" || echo "PROJET ABSENT"
```

### 1. Empreintes et dérive

Prendre deux scans complets (avant lecture, puis après) et comparer. Toute différence impose de relire la dernière version et de rattacher les constats à la nouvelle empreinte ; l'ancienne devient `HISTORIQUE` ou `EXPIRÉ`.

```bash
PYTHONIOENCODING=utf-8 py -3 -B - "$PKG" <<'PY'
import hashlib, os, sys
pkg = sys.argv[1]
rows = []
for root, _, files in os.walk(pkg):
    for name in files:
        p = os.path.join(root, name)
        st = os.stat(p)
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        rows.append((os.path.relpath(p, pkg), st.st_size, st.st_mtime_ns, h))
for rel, size, mtime_ns, h in sorted(rows):
    print(size, mtime_ns, h, rel)
PY
```

- Comparer les deux sorties ligne à ligne (mêmes chemins, mêmes tailles, mêmes hashes).
- Un fichier vu par `skill-file-qa` mais absent de `find`/`os.walk` révèle un écrivain actif : suspendre la conclusion.
- Consigner les heures locales avec offset et garder le SHA-256 complet dans le rapport.

### 2. QA statique

```bash
cd "$HOME/.qoder/skills/skill-file-qa" && PYTHONIOENCODING=utf-8 py -3 -B scripts/validate_skill.py "$PKG"
```

- Attendre `RESULT PASS`, `Files (N)` cohérent avec l'inventaire, empreinte stable.
- Re-scanner immédiatement après : le PASS ne protège pas contre une écriture postérieure.
- Ne corriger ni les `WARN` ni les `FAIL` du paquet d'autrui ; les rapporter avec la ligne concernée.

### 3. Provenance des affirmations

Pour chaque affirmation vérifiable du paquet (`SKILL.md` et références) :

- recalculer le SHA-256 complet et la taille, puis comparer à la valeur citée (préfixe, hash, date) ;
- lire la ligne de documentation exacte citée ;
- rechercher la preuve brute dans le JSONL source et la caviarder.

```bash
sha256sum "$FILE"
stat -c '%s %Y %n' "$FILE"
sed -n '66,70p' "$DOC"
```

Recherche JSONL sans jamais écrire le secret dans le paquet : construire le motif en mémoire et n'imprimer que le contexte gauche suivi de `<secret>`.

```python
import re, sys
pattern = re.compile(sys.argv[2])
with open(sys.argv[1], encoding="utf-8") as source:
    for number, line in enumerate(source, 1):
        for match in pattern.finditer(line):
            print(number, line[max(0, match.start() - 70):match.start()] + "<secret>")
```

Classer chaque affirmation : `SUPPORTED` (preuve recalculée), `OVERSTATED` (la preuve ne dit pas ce qui est affirmé), `CONTRADICTED`, `UNVERIFIED` (preuve absente ou illisible). Citer `fichier:ligne` et la fenêtre d'empreinte.

### 4. Fixture jetable du contrat fonctionnel

- Créer la fixture hors des racines de Skills et n'employer que de faux secrets.
- Exécuter chaque cas sans pipe, en capturant le code de retour séparément.
- Assertions minimales par cas : code attendu, clés/valeurs attendues, secret absent de `stdout` et `stderr`, cible inchangée, aucune écriture hors fixture, aucun `__pycache__`/`.pyc`/`.tmp`.

```bash
FIXTURE="${TEMP:-/tmp}/audit_contrat_${SESSION:0:8}.py"
PYTHONIOENCODING=utf-8 py -3 -B "$FIXTURE" >"${TEMP:-/tmp}/out.txt" 2>"${TEMP:-/tmp}/err.txt"; rc=$?
```

- En cas d'écart, afficher `repr(stdout)` et `repr(stderr)` ; décider `BUG_HARNAIS` ou `BUG_SCRIPT`.
- Si l'attente est fausse (racine par défaut différente de l'intuition, séparateur de chemin, casse), corriger l'attente du harnais — pas le script audité.
- Rejouer l'ensemble des cas jusqu'à `N/N` et noter le nombre de cas et le faux secret utilisé.

### 5. Recontrôle, expiration et rapport

- Après une modification légitime du propriétaire, recalculer les empreintes : l'audit devient `EXPIRÉ`. Réauditer la dernière version ; ne jamais restaurer votre instantané.
- Supprimer uniquement vos fixtures et sorties temporaires ; laisser les résidus étrangers en place et les mentionner.
- Si la cible n'a pas été créée, revérifier son absence aux deux racines avant de conclure.
- Livrer le rapport ci-dessous, sans conclusion au-delà de ce qui a été observé.

## Modèle de rapport

```text
MODE: LECTURE SEULE
CIBLE NON CREEE: oui/non — absence vérifiée aux deux racines (horodatage)
PAQUET AUDITE: <chemin> — <N> fichiers
ECRIVAIN: actif / silencieux / inconnu (preuve)
EMPREINTES: <fichier> size mtime_ns SHA-256 (scan 1 / scan 2)
DERIVE: aucune | <fichier> ancien → nouveau (fenêtre horaire)
QA: RESULT PASS/FAIL — Files (N) — WARN/FAIL détaillés
AFFIRMATIONS:
  - "<citation>" → SUPPORTED/OVERSTATED/CONTRADICTED/UNVERIFIED (preuve, hash)
FIXTURE: <N>/<N> cas, faux secret <nom>, sorties hors racines
POST-AUDIT: inchangé | EXPIRÉ par <fichier> à <heure>
COUVERTURE: étapes réellement exécutées
LIMITES: ce qui n'a pas été prouvé
```

## Pièges

- **PASS ≠ paquet figé** : seule l'empreinte de `SKILL.md` est scellée ; référence et script doivent être mesurés séparément.
- **`find` incomplet = écrivain actif** : si le validateur voit un fichier absent de votre inventaire, ne concluez pas, refaites le scan.
- **Racine par défaut contre-intuitive** : dans le cas de référence, le script remontait à `secrets.parent.parent` (répertoire projet), d'où un préfixe `projet\` attendu à tort. Le stdout réel a tranché en faveur du harnais.
- **Correction légitime après audit** : elle périme vos hashes ; l'audit s'expire, il ne se « répare » pas.
- **Stabilité entre deux scans ≠ exhaustivité** : un fichier jamais listé reste non audité.
- **`python` peut être l'alias Microsoft Store** (code 49) : utiliser `py -3`.
- **Console cp1252** : garder les assertions ASCII et forcer `PYTHONIOENCODING=utf-8`.
- **Résidus d'autrui** : un `__pycache__` ou une fixture imbriquée préexistante se signale, ne se supprime pas.

## Checklist de fin

- [ ] Absence de la cible vérifiée aux deux racines (si non créée)
- [ ] Deux scans d'empreintes, dérive expliquée et datée
- [ ] `RESULT PASS` avec `Files (N)` cohérent et empreinte stable
- [ ] Chaque affirmation classée et liée à un SHA-256 complet
- [ ] Fixture `N/N` hors racines, faux secret absent des sorties
- [ ] Aucune écriture sous les racines, aucun cache ajouté
- [ ] Audit marqué `EXPIRÉ` si le paquet a changé après
- [ ] Rapport livré avec couverture et limites explicites

## Ressources

- [references/cas-audit-concurrent-2026-10-28.md](references/cas-audit-concurrent-2026-10-28.md) — cas vérifié : décision de conserver le paquet concurrent, dérive 6 386 → 6 555 octets, harnais 15/15 après correction de l'attente, audit expiré par des écritures légitimes postérieures.
