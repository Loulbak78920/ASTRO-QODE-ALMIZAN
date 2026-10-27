---
name: valider-harnais-fixture-windows-msys
description: "Valider un harnais de fixture Git jetable sous Windows/Git Bash/MSYS comme une porte d'acceptation ordonnée : compiler le script, l'exécuter deux fois avec des racines et des commits différents, exiger au moins un contrôle négatif réellement exécuté, vérifier l'absence de résidus, puis lancer skill-file-qa avec le dossier du Skill en argument positionnel (--skill, abréviation argparse de --skills-root : sans valeur exit 2, avec un dossier faux PASS à 0 référence) et un nombre de fichiers exact après retrait des __pycache__ générés. Utiliser après avoir écrit ou modifié un script de fixture, quand deux PASS pourraient être recyclés, quand Files (N) inclut un .pyc, quand un clone rend rc=128 avec /C:/ (voir diagnostiquer-clone-git-file-uri-msys), ou quand un Edit signale que le fichier a changé. Ne remplace pas les Skills de fixture spécifiques. 中文触发：夹具验收门禁、py_compile、双跑、负向控制、残留检查、__pycache__、Files (N)、--skill 假 PASS、skill_dir、文件已变化、双采样、file:///、rc=128、MSYS_NO_PATHCONV。"
---

# Valider un harnais de fixture Git sous Windows/Git Bash

## État et portée

Cette Skill est une **porte d'acceptation** pour un script de harnais de fixture Git jetable. Elle ne fournit ni fixture ni script : elle fixe l'ordre des vérifications, les tokens attendus, les codes de retour et les conditions de sortie.

Elle ne remplace pas les Skills spécialisés :

- `tester-publication-isolee-skill` pour la fixture de publication isolée ;
- `diagnostiquer-clone-git-file-uri-msys` pour la matrice MSYS et le diagnostic `rc=128` ;
- `tester-garde-derive-git` pour un garde de dérive Git seul ;
- `skill-update-concurrency-safe` pour la stabilité et les éditions concurrentes ;
- `skill-file-qa` pour la validation statique d'un Skill.

Un `RESULT PASS` ne couvre que la fixture réellement exécutée. Il ne prouve ni un dépôt réel, ni un remote réseau, ni la sûreté d'un push, ni une concurrence réelle entre sessions.

## Objectif

Empêcher trois faux positifs :

1. un seul PASS recyclé présenté comme deux exécutions ;
2. un `Files (N)` qui inclut un cache et un `RESULT PASS` qui ne vérifie pas le script ;
3. une édition appliquée sur une vue périmée du fichier.

La porte exige, dans cet ordre : compilation, première exécution, seconde exécution avec une fixture fraîche et un identifiant différent, au moins un contrôle négatif réellement observé, contrôle des résidus, QA avec un nombre de fichiers exact, puis rapport honnête.

## Quand l'utiliser

- Après avoir écrit ou modifié un harnais de fixture Git sous Windows/Git Bash.
- Quand deux PASS consécutifs pourraient provenir de la même sortie ou du même commit.
- Quand `Files (N)` contient un `.pyc` ou quand la QA passe alors que le script n'a pas été exécuté.
- Quand `validate_skill.py --skill` rend 2, ou passe avec `skill references: 0 found` alors que le paquet déclare des références.
- Quand un clone local rend `rc=128` avec un chemin `/C:/...`.
- Quand un Edit signale que le fichier a changé depuis la dernière lecture.
- Avant de déclarer un harnais « vérifié » ou de le livrer.

Ne pas utiliser pour : publier un Skill, tester un dépôt de production, pousser vers un hôte réseau, diagnostiquer seul un file URI MSYS, tester seul un garde de dérive, ou valider statiquement un Skill sans exécuter son harnais.

## Contrat non négociable

1. **Fixture jetable unique.** Tout se passe sous `$HOME/.qoder/tmp/<prefixe>-<unique>`. Ne jamais utiliser un dépôt de travail ni un chemin fourni par l'utilisateur comme cible. Supprimer uniquement la racine créée par cette exécution. Dans `finally`, rendre les fichiers inscriptibles, réessayer, puis vérifier l'absence. Un `rmtree` silencieux n'est pas une preuve de nettoyage.

2. **Environnement de sous-processus fixé.** Poser `LC_ALL=C`, `GIT_TERMINAL_PROMPT=0`, un délai explicite et une sortie ASCII. Ne pas exporter `MSYS_NO_PATHCONV` ni `MSYS2_ARG_CONV_EXCL` globalement. Si un outil en a besoin, les limiter à son sous-processus. Si l'environnement les hérite, construire le remote local avec `"file://" + path.resolve().as_posix()` (deux barres) : c'est une défense mesurée sur Git 2.52.0.windows.1, pas une règle générale. Pour la cause racine et la matrice, utiliser `diagnostiquer-clone-git-file-uri-msys`.

3. **Clone sans configuration locale, mais pas tous les clones.** Interdire toute configuration locale uniquement pour un clone dont le but est de prouver l'état isolé ou distant. Passer l'identité par `-c user.name=... -c user.email=... -c commit.gpgsign=false`, puis vérifier l'absence locale de `core.autocrlf`, `user.name` et `user.email`. Un clone jetable ordinaire peut écrire sa configuration locale ; voir `tester-garde-derive-git`.

4. **Compiler avant d'exécuter.** Utiliser `ast.parse` par défaut, sans cache. Si une vraie compilation bytecode est exigée, poser `PYTHONPYCACHEPREFIX` vers un dossier temporaire ; sinon supprimer le cache généré avant la QA. Une syntaxe valide ne prouve pas le comportement.

5. **Deux exécutions fraîches.** Créer deux racines de fixture distinctes. Chaque exécution doit rendre le code 0 et le token de succès documenté (`RESULT PASS` ou équivalent). L'identifiant propre à l'exécution (hash de commit, identifiant de run ou racine) doit différer. Un hash identique ou une sortie byte-identique signale une sortie recyclée : enquêter, ne pas accepter.

6. **Au moins un contrôle négatif observé.** Choisir un contrôle qui échouerait si le harnais était à vide : `--verifier` absent rend 2 sans créer de fixture ; un hash abrégé rend `STOP_HEAD` code 1 sans déplacer les refs ; un préfixe de nettoyage incorrect rend `REFUS` code 1. Le contrôle doit être exécuté dans cette session. Un contrôle seulement documenté ne compte pas ; sans contrôle, la porte est incomplète.

7. **Résidus attribués avant suppression.** Vérifier `$HOME/.qoder/tmp` pour les préfixes du harnais et exiger l'absence de résidu. Si un dossier correspond au préfixe mais n'a pas été créé par cette exécution, le signaler sans le supprimer. Supprimer seulement la racine de cette exécution après le contrôle de préfixe.

8. **QA avec argument positionnel.** Si le harnais appartient à un paquet Skill, prendre un instantané des caches avant la QA, lancer `validate_skill.py "$SKILL_DIR" --workspace ... --stable-seconds 2`, puis exiger le code 0, `RESULT PASS`, un `Files (N)` exact, le compteur `skill references: <N> checked` attendu et aucun nouveau cache. `--skill` n'est pas une option distincte : argparse l'abrège en `--skills-root`. Sans valeur, il rend 2 ; suivi d'un dossier, il peut rendre `RESULT PASS` avec `skill references: 0 found`, un faux PASS. Passer `skill_dir` en positionnel et refuser `0 found` quand le paquet déclare des références. Supprimer uniquement les caches créés par cette session ; ne jamais supprimer un cache préexistant. La QA ne lit ni n'exécute les scripts : `Code blocks: python=0` ne vaut pas vérification du script.

9. **Édition concurrente.** Si un Edit rend `The file changed since your last read`, arrêter. Relire, échantillonner deux fois `size`, `mtime` et `SHA-256` à au moins 2 secondes d'intervalle, puis faire une édition minimale. Si le fichier change encore, arrêter et rapporter. Voir `skill-update-concurrency-safe`.

10. **Rapport honnête.** Ne rapporter que les branches réellement exécutées. Distinguer « re-vérifié dans cette session », « observé dans la source » et « non exécuté ». Ne jamais recycler un ancien PASS. Ne pas committer ni pousser sans instruction explicite. Si l'utilisateur réduit le périmètre à `SKILL.md`, suivre `skill-staged-delivery` et ne pas revendiquer de validation fonctionnelle.

## Boucle fixe

### 0. Préflight

```bash
git --version
py -3 -c "import sys;print(sys.version.split()[0])"
git config --system --get core.autocrlf || echo "core.autocrlf systeme: unset"
printf 'MSYS_NO_PATHCONV=%s\n' "${MSYS_NO_PATHCONV:-unset}"
printf 'MSYS2_ARG_CONV_EXCL=%s\n' "${MSYS2_ARG_CONV_EXCL:-unset}"
printf 'TMP=%s\n' "$HOME/.qoder/tmp"
```

Vérifier que le harnais existe, que la racine temporaire existe et qu'aucun cache du paquet n'est déjà présent. Noter Git, Python, `core.autocrlf` et l'état des variables MSYS. Si elles sont définies dans le parent, le noter sans modifier la configuration de l'utilisateur.

### 1. Compilation

```bash
py -3 -c "import ast,pathlib,sys; ast.parse(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))" "<harnais>.py"
```

Attendre le code 0. Si une compilation bytecode est indispensable :

```bash
harnais="<chemin-du-harnais>.py"
cache="$HOME/.qoder/tmp/pycache-$(date +%s)-$$"
PYTHONPYCACHEPREFIX="$cache" py -3 -m py_compile "$harnais"
test ! -e "$(dirname "$harnais")/__pycache__"
rm -rf "$cache"
```

Exiger qu'aucun cache n'apparaisse dans le dossier du harnais. S'il en apparaît un, le supprimer uniquement s'il vient de cette compilation, puis revérifier.

### 2. Première exécution

```bash
py -3 "<harnais>.py" <arguments>
```

Attendre le code 0 et le token de succès documenté. Enregistrer la racine de fixture, le hash de commit ou l'identifiant de run, le hash du vérificateur, le nombre de PASS et la ligne de nettoyage. Si le code diffère de 0, arrêter : la porte échoue ; une seconde exécution ne répare pas la première.

### 3. Seconde exécution

Relancer la même commande avec une nouvelle racine. Attendre le code 0 et le token de succès, avec un identifiant différent de la première exécution.

Si l'identifiant est identique :

- vérifier qu'aucun fichier de sortie ni `--keep` n'a été réutilisé ;
- vérifier que la racine a bien été créée dans cette exécution (`mtime`, chemin) ;
- ne pas compter une sortie recopiée comme second PASS.

Enregistrer les deux identifiants.

### 4. Contrôle négatif

Exécuter un contrôle propre au harnais. Exemples :

```bash
py -3 "<harnais>.py" --verifier "C:/chemin/absent/verifier.py"
```

Attendre le code 2 et l'absence de fixture créée. Un contrôle intégré peut aussi être utilisé : hash abrégé → `STOP_HEAD` code 1 et refs inchangées ; préfixe de nettoyage incorrect → `REFUS` code 1. Enregistrer le token, le code et les effets de bord. Si le contrôle passe alors qu'il devait échouer, le harnais est à vide ou trop permissif : corriger le harnais, pas l'attendu.

### 5. Clone rc=128 avec `/C:/`

Arrêter la porte et diagnostiquer avant toute modification :

```bash
py -3 "$HOME/.qoder/skills/diagnostiquer-clone-git-file-uri-msys/scripts/diagnostiquer_clone_file_uri.py" --url-forms three
```

Suivre le verdict du diagnostic. Correctif préféré : retirer l'export global des variables MSYS ; si un outil en a besoin, les limiter à son sous-processus. La forme d'URL à deux barres n'est utilisée que si la matrice la justifie, ou comme défense explicitement déclarée. Ne pas modifier la configuration Git globale ou système, ne pas changer `core.autocrlf` pour masquer l'échec, puis reprendre à l'étape 1.

### 6. Cache et QA

Si le harnais appartient à un paquet Skill :

```bash
find "<dossier-skill>" \( -name __pycache__ -o -name '*.pyc' \) -print
```

Noter les chemins avant la QA. Supprimer uniquement les chemins nouveaux créés par cette session. Si un dossier de cache contient autre chose que des `.pyc`, ne pas le supprimer à l'aveugle : le signaler.

```bash
py -3 "$HOME/.qoder/skills/skill-file-qa/scripts/validate_skill.py" "<dossier-skill>" \
  --workspace "<racine-workspace>" \
  --stable-seconds 2 --stability-timeout 30
```

Exiger le code 0, `RESULT PASS`, un `Files (N)` exact, `PASS name`, `PASS description: single line`, un corps de moins de 500 lignes, des références locales résolues (0 si le paquet n'en a pas), le compteur `skill references: <N> checked` attendu (refuser `0 found` si le paquet en déclare) et la lecture de la ligne `Code blocks`. Si `python=0` alors que le paquet contient des scripts Python, exécuter la vérification de syntaxe séparément. Revérifier l'absence de cache après la QA.

Si le harnais est autonome et n'appartient à aucun paquet Skill, la QA ne s'applique pas : le dire explicitement ; compilation, exécutions, contrôle négatif et résidus restent obligatoires.

### 7. Résidus, empreintes, rapport

- Vérifier `$HOME/.qoder/tmp` pour les préfixes du harnais et exiger l'absence de résidu.
- Attribuer toute correspondance inattendue avant toute suppression ; ne jamais supprimer la fixture d'une autre session.
- Relever `size`, `mtime` et `SHA-256` de tout fichier livré, puis les échantillonner une seconde fois après au moins 2 secondes.
- Produire le rapport ci-dessous.

```text
Harnais : <chemin> | sha256 <hash>
Environnement : Windows <version>, Git <version>, Python <version>, core.autocrlf=<valeur>, MSYS vars=<set|unset>
Compilation : <ast.parse|py_compile> EXIT <n> | cache hors du Skill oui/non
Exécution 1 : EXIT <n> | PASS <token> | commit/run <hash> | fixture <chemin>
Exécution 2 : EXIT <n> | PASS <token> | commit/run <hash> | différent oui/non
Contrôle négatif : <commande> EXIT <n> | token <...> | effet de bord <aucun|...>
Résidus : <aucun|liste> | nettoyage vérifié oui/non
QA : EXIT <n> | <n> PASS / <n> FAIL / <n> WARN | Files (N) | local references <n> | skill references <n>
Empreinte : <bytes> | <mtime> | <sha256> | double échantillon stable oui/non
Portée : fixture locale uniquement ; production, réseau, concurrence non testés
```

## Table des erreurs

| Symptôme | Cause | Action |
|---|---|---|
| `git clone rc=128` avec `fatal: '/C:/...' does not appear...` | variables MSYS exportées et URL à trois barres | arrêter la porte, lancer `diagnostiquer-clone-git-file-uri-msys`, retirer l'export global ; deux barres seulement si mesuré |
| `validate_skill.py --skill` rend 2 ou passe avec `skill references: 0 found` | `--skill` est l'abréviation argparse de `--skills-root` : sans valeur exit 2 ; avec un dossier, la recherche des références inter-Skills est réduite et la QA peut passer à 0 | passer le dossier en premier argument positionnel ; exiger le compteur `skill references: N checked` attendu, jamais `0 found` si le paquet déclare des références |
| `Files (N)` contient un cache `.pyc` et la QA passe | la QA compte les caches et le dossier des scripts est autorisé | prendre un instantané, supprimer seulement le cache de cette session, relancer et exiger `Files (N)` exact |
| `The file changed since your last read` | écriture concurrente ou vue périmée | arrêter, relire, double échantillon à 2 secondes, édition minimale ; arrêter si cela change encore |
| deux PASS avec le même hash ou la même racine | sortie recyclée, `--keep` ou journal recopié | créer une fixture fraîche, vérifier le `mtime` de la racine, relancer ; ne pas compter comme second PASS |
| le contrôle négatif réussit alors qu'il devait échouer | harnais à vide ou trop permissif | corriger le harnais ou ses assertions, pas l'attendu |
| résidu `isolated-publish-*` ou préfixe du harnais | nettoyage échoué ou fixture d'une autre session | attribuer, supprimer seulement la racine de cette exécution, `chmod` + réessais + vérification |
| `UnicodeEncodeError` ou `charmap` | page de code de la console Windows, pas corruption du fichier | sortie ASCII ou `backslashreplace`, `PYTHONUTF8=1` ou `-X utf8` ; ne pas accuser l'encodage du fichier |
| `M base.txt` après clone | différence `core.autocrlf`, pas MSYS | traiter séparément ; ne pas écrire `core.autocrlf` dans un clone isolé ; voir `tester-garde-derive-git` |
| QA PASS mais script cassé | la QA ne lit ni n'exécute les scripts | exécuter syntaxe, exécutions réelles et contrôle négatif |

## Checklist de livraison

- [ ] Racine de fixture fraîche ; seule la racine de cette exécution est supprimée ; absence vérifiée après `chmod` et réessais.
- [ ] Environnement de sous-processus fixé ; variables MSYS non exportées globalement ; forme d'URL choisie et justifiée.
- [ ] Configuration locale absente uniquement pour les clones d'isolement ; identité par `-c` ; valeurs locales vérifiées absentes.
- [ ] Compilation avant exécution ; aucun cache laissé dans le paquet, ou cache supprimé et QA relancée.
- [ ] Deux exécutions fraîches, toutes deux PASS, avec un identifiant de commit ou de run différent.
- [ ] Au moins un contrôle négatif exécuté, avec le code, le token et l'absence d'effet de bord indésirable.
- [ ] Résidus vérifiés et attribués ; aucune fixture étrangère supprimée.
- [ ] QA avec argument positionnel, code 0, `Files (N)` exact, `skill references: N checked` attendu, références locales résolues, ligne `Code blocks` lue.
- [ ] Edit périmé traité par relecture, double échantillon à 2 secondes et édition minimale.
- [ ] Rapport distinguant re-vérifié, observé dans la source et non exécuté ; aucun PASS recyclé ; aucun commit ni push.
- [ ] Si le périmètre a été réduit : livraison partielle déclarée selon `skill-staged-delivery`, sans revendication fonctionnelle.

## Skills liés

- `diagnostiquer-clone-git-file-uri-msys` — cause racine, matrice quatre conditions et correctif minimal.
- `tester-publication-isolee-skill` — fixture de publication isolée et règle du clone sans configuration locale.
- `tester-garde-derive-git` — un clone jetable ordinaire peut écrire sa configuration locale.
- `skill-update-concurrency-safe` — double échantillon, édition minimale, relance de la QA et nettoyage des caches.
- `skill-file-qa` — validation structurelle et manifeste `Files (N)`.
- `skill-package-integrity-audit` — intégrité du paquet et audit des caches après la QA.
- `replay-skill-reference-fixtures` — rejouer les sorties documentées sans recycler une preuve périmée.
- `probe-cli-args-beyond-msys-rewrite` — quand l'argv lui-même est réécrit par MSYS.
- `skill-staged-delivery` — livraison partielle limitée à `SKILL.md`.
- `publier-skill-qoder-vers-depot-git` — publication réelle, hors périmètre de cette porte.

## Provenance et limites

- **Source observée** (session `b8448766-bcf0-40dc-9ea5-9622f129877e`, lue le 2026-10-26, revision 97, `hasMoreBefore=false`) : clone `rc=128` avec `/C:/` sous `MSYS_NO_PATHCONV=1` ; `validate_skill.py --skill` sans valeur rend 2 ; `Files (4)` avec un `.pyc` puis `Files (3)` après suppression ; Edit signalant un fichier changé, puis double échantillon stable ; deux PASS avec des hashes différents (`ef41a7de`/`921b00d6`, `ec809439`/`1fd1b0ec`).
- **Portée ajustée par l'utilisateur** (source `b8448766`) : « 先只更新 SKILL.md，脚本和证据稍后 », puis « 创建测试脚本和证据文件 ». La session `2ae40150` a demandé d'étendre `tester-publication-isolee-skill` au lieu de créer ce Skill ; la session `471fb8cd` a ensuite fixé ce dossier, confirmé le create (« 确认不改回扩展 tester-publication-isolee-skill ») et écrit le fichier. Aucun fichier n'avait été écrit dans les deux tentatives précédentes.
- **Écriture et première validation** (session `471fb8cd-a93f-435f-9f88-7110d005738f`, lue le 2026-10-26, revision 51, `hasMoreBefore=false`) : création du seul `SKILL.md` ; QA `EXIT 0`, `RESULT PASS`, `Files (1)`, 9 PASS, description 891 caractères, corps 232 lignes ; empreinte finale `bbcca2b9…` (19 951 octets).
- **Re-vérifié le 2026-10-26** : Git 2.52.0.windows.1, Python 3.14.7, `core.autocrlf=true`, variables MSYS absentes du parent ; clone à trois barres `rc=128`, à deux barres `rc=0` ; `validate_skill.py --skill` sans valeur `rc=2`. Un `rmtree(ignore_errors=True)` a laissé la fixture de sonde ; `chmod` + réessais + vérification d'absence l'ont supprimée. `py_compile` sous `PYTHONPYCACHEPREFIX` n'a créé aucun cache à côté du harnais. Une sonde de Skill a rendu `Files (3)` avec un `.pyc` puis `Files (2)` après suppression, `RESULT PASS` dans les deux cas.
- **Contrôle de mise à jour (2026-10-26)** : avant édition, QA `EXIT 0`, `RESULT PASS`, `Files (1)`, 9 PASS, description 891 caractères, 10 références inter-Skills ; `--skill` seul `rc=2`, mais `validate_skill.py "$SKILL_DIR" --skill "$SKILL_DIR"` rend `RESULT PASS` avec `skill references: 0 found` (faux PASS observé) ; après édition, QA `EXIT 0`, `RESULT PASS`, `Files (1)`, 9 PASS, description 982 caractères, 10 références inter-Skills ; double échantillon à 2,2 s stable.
- **Non exécuté** : le harnais de publication complet, un dépôt réel, un remote réseau, une concurrence réelle entre sessions, un push. Un PASS ne couvre que la fixture exécutée.
- **Non modifié** : `tester-publication-isolee-skill` et ses fichiers ; sa ligne 144 contient encore une formulation historique sur les variables MSYS, que ce Skill ne reprend pas.

## Définition de terminé

- [x] `SKILL.md` présent, frontmatter valide, `name` égal au dossier, description sur une ligne et ≤1024 caractères.
- [x] Corps de moins de 500 lignes, sections complètes, aucun marqueur de travail inachevé.
- [x] `skill-file-qa` : code 0, `RESULT PASS`, `Files (1)`, références locales 0, 10 références inter-Skills vérifiées.
- [x] Assertions documentées (trois barres, deux barres, `--skill` sans valeur, faux PASS `--skill <dossier>`, double échantillon) réexécutées et rapportées.
- [x] Aucun cache ni temporaire dans le Skill ; empreinte stable sur deux échantillons.
- [x] Rapport final distinguant re-vérifié, observé et non exécuté ; aucun commit ni push.
