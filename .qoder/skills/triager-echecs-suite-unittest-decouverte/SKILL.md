---
name: triager-echecs-suite-unittest-decouverte
description: "Trier les échecs d'une exécution `unittest discover` où les modules ciblés passent : distinguer artefact d'ordre d'import (constante de configuration capturée à l'import), assertion périmée face à un artefact réel, test sensible à la charge, socket non fermé (ResourceWarning) et périmètre de scan pollué par un clone étranger ; reproduire chaque mode en isolé, corriger à la source, puis prouver par un rejeu avec clé absente à l'import et une porte `-W error::ResourceWarning`. Utiliser quand la suite complète échoue alors qu'un module de test est vert, qu'un test REST rend 401 seulement en découverte, qu'une assertion compte 8 au lieu de 9, qu'un message attendu a changé, ou que des sockets restent ouverts. 中文触发：unittest 全量发现失败、单模块通过、导入顺序、配置常量在导入时固化、断言过期、ResourceWarning 未关闭套接字、扫描到外部仓库。English: unittest discovery failures, import-order artifact, stale assertion, load-sensitive test, unclosed socket, foreign clone in scan perimeter."
---

# Trier les échecs d'une découverte `unittest`

## Quand utiliser

- La suite complète (`unittest discover`) échoue alors que chaque module ciblé passe seul.
- Un test REST renvoie 401 uniquement en découverte, ou une constante de configuration semble vide.
- Une assertion de comptage ou de message ne correspond plus à l'artefact réel.
- La sortie contient `ResourceWarning: unclosed <socket.socket ...>`.
- Le périmètre scanné contient un clone étranger et des tests échouent sur des modules que vous n'avez pas modifiés.
- La découverte dure des heures et il faut décider quoi corriger sans relancer à l'aveugle.

## Quand ne pas utiliser

- Échec d'un seuil de durée, de latence, de gigue ou de timeout : appliquer `diagnostiquer-echec-test-chronometre`.
- Rejouer un fixture documenté à l'identique : `replay-skill-reference-fixtures`.
- Accepter un paquet Skill après écriture : `skill-file-qa`.
- Incident en production : suivre la procédure de déploiement du domaine.

## Règles non négociables

1. Ne jamais modifier un test avant d'avoir reproduit son mode d'échec : isolé, module, puis découverte.
2. Ne jamais changer un seuil de performance pour faire passer un test.
3. Ne jamais supprimer un import « inutilisé » sans chercher `mock.patch.object(<module>`, `getattr(<module>` et les accès indirects.
4. Ne jamais « corriger » une assertion avant d'avoir exécuté l'artefact qu'elle décrit.
5. Ne jamais modifier, déplacer ni exclure silencieusement un dépôt étranger trouvé dans le périmètre scanné.
6. Corriger `ResourceWarning` à la source (`server_close()`, context managers), jamais en filtrant les avertissements.
7. Ne jamais filtrer la sortie d'une longue découverte avec un pipe `grep` avant de l'avoir conservée : les tracebacks disparaissent et chaque échec doit être relancé.

## Étape 1 — Baseline reproductible

Exécuter d'abord les modules ciblés ensemble, puis la découverte complète :

```bash
py -3 -B -m unittest tests.test_passerelle_api_vps tests.test_sas_biometrique_souverain -v
py -3 -B -m unittest discover -s tests -t . -v > journal_decouverte.txt 2>&1
```

- Lancer la découverte en arrière-plan si elle dure des heures ; ne rien modifier pendant ce temps.
- Relever `Ran N tests in T s`, chaque ligne `FAIL:` et `ERROR:`, et le premier `AssertionError` de chaque échec.
- Conserver le journal : c'est la seule baseline fiable après des corrections.
- Ne pas piper cette sortie vers `grep -E '^(FAIL|ERROR|Ran|FAILED)'` : le filtre ne garde que les noms et le résumé, perd les tracebacks et impose des relances ciblées (constaté sur 272 tests : 7 noms, aucun stack). Compter depuis le journal (`grep -c '^FAIL:' journal_decouverte.txt`, `grep -c '^ERROR:' journal_decouverte.txt`), puis lire les blocs `FAIL:`/`ERROR:` entiers.
- Sous Windows, `python` peut être l'alias Microsoft Store (code 49) ; utiliser `py -3`.

## Étape 2 — Classer avant de corriger

| Symptôme observé | Indice décisif | Catégorie |
|---|---|---|
| Vert seul, rouge avec un autre module ou en découverte | la valeur lue change selon l'ordre d'import | Ordre d'import |
| `9 != 8`, message introuvable | l'artefact réel diffère de l'attendu | Assertion périmée |
| Dépasse un seuil uniquement pendant la suite complète | vert en isolé sur machine calme | Charge |
| `unclosed <socket.socket ...>` | serveur arrêté sans `server_close()` | Ressource |
| Échec sur des modules non touchés, chemins d'un autre dépôt | clone imbriqué dans la racine scannée | Périmètre pollué |
| Reproductible en isolé avec la même cause | la cause est dans le code testé | Régression réelle |

Un échec non reproductible seul n'est pas automatiquement un artefact : prouver le mécanisme avant de conclure.

## Étape 3 — Artefact d'ordre d'import

Mécanisme : une constante est capturée à l'import, avant qu'un autre module de test ne pose l'environnement.

```python
CLE = os.environ.get("API_KEY", "")

def authentifie(token):
    return token == CLE
```

Le module ciblé passait parce qu'il posait sa clé avant son propre import ; en découverte, un autre module importe la cible le premier et `CLE` reste vide.

Reproduire sans modifier le code :

1. Rejouer les deux modules ensemble et constater l'échec.
2. Afficher la valeur capturée à l'import et la valeur de l'environnement au moment de la requête.
3. Importer d'abord le module fautif, puis exécuter le test ciblé.

Corriger à la source : lire l'environnement à chaque appel et fermer par défaut.

```python
def cle_attendue() -> str:
    return os.environ.get("API_KEY", "").strip()

def authentifie(token: str) -> bool:
    cle = cle_attendue()
    if not cle:
        return False
    return hmac.compare_digest(token, cle)
```

Corriger les tests : poser la variable avant l'import, ou patcher l'environnement au moment du test.

```python
with mock.patch.dict(os.environ):
    os.environ.pop("API_KEY", None)
    # requête protégée : doit répondre 401
```

Ne pas patcher la constante du module : cela validerait l'ordre d'import, pas le comportement de sécurité.

Preuve en deux volets :

- Sonde : import avec variable absente, `cle_attendue()` renvoie `""` ; après `os.environ["API_KEY"] = "x"`, elle renvoie `"x"`.
- Rejeu : découverte lancée avec la variable absente au démarrage du processus ; les tests protégés passent et un jeton arbitraire reçoit 401.

Piège : supprimer `import module as m` parce que le grep ne trouve que `m.CONSTANTE` dans les tests. `mock.patch.object(m, "CONSTANTE", ...)` casse alors en `NameError`, et seul le test de repli échoue.

## Étape 4 — Assertion périmée

1. Exécuter l'artefact réel : tous les scripts du dossier, la route, le message produit.
2. Compter depuis l'artefact, pas depuis la constante écrite dans le test.
3. Si l'artefact est correct, aligner l'assertion sur le comportement honnête, pas sur l'ancienne formulation.
4. Si l'artefact est faux, corriger la source, pas le test.
5. Mettre à jour la docstring et conserver une assertion qui vérifie encore quelque chose.

Exemple : neuf scripts `.aq` présents et exécutables, l'assertion passe de `8` à `9` ; un message commercial remplacé par une formulation honnête impose de vérifier les termes qui portent le sens (« partage 50/50 », « Riba 0 % »), pas seulement une sous-chaîne commode.

## Étape 5 — Charge et temps

- Rejouer le test seul, sur machine calme, sans la suite complète.
- S'il passe, classer « sensible à la charge », ne pas toucher au seuil et documenter la durée de la suite complète.
- S'il échoue seul avec la même mesure, appliquer `diagnostiquer-echec-test-chronometre` (profiler, cache d'empreinte, budget global).

## Étape 6 — Ressources non libérées

Poser la porte :

```bash
py -3 -B -W error::ResourceWarning -m unittest tests.test_passerelle_api_vps -v
```

Corriger à la source :

```python
def arreter(self):
    """Arrête le serveur et libère le port d'écoute."""
    if not self.httpd:
        return
    self.httpd.shutdown()
    self.httpd.server_close()
    if self.thread:
        self.thread.join(timeout=5.0)
        self.thread = None
    self.httpd = None
```

Dans `tearDownClass`, appeler seulement `arreter()` : un `server_close()` supplémentaire après coup est redondant ou inopérant puisque `httpd` vaut `None`.

Fermer aussi les réponses d'erreur (`urllib.error.HTTPError`) avec un context manager ou un `close()` explicite. Compléter la porte d'avertissements par une re-liaison du port (`socket.bind`), qui échoue si la socket écoute encore. Ne pas utiliser `-W ignore::ResourceWarning`, `warnings.filterwarnings` ni `gc.collect()` comme correctif.

## Étape 7 — Périmètre scanné pollué

- Localiser le préfixe étranger dans les messages (`assertEqual(..., 0, msg=modules_a_recaler)`).
- Prouver le périmètre avant d'accuser le code : afficher la racine réellement scannée et la constante qui la fixe (ex. `RACINE_DEPOT = RACINE_SYSTEME.parent`), puis vérifier que le dépôt étranger contient son propre `.git`.
- Vérifier que les chemins ne viennent pas de vos changements (dépôt, session, date).
- Écrire zéro fichier dans ce dépôt : ne pas supprimer, déplacer ni exclure ; rapporter comme résidu et demander à l'ayant droit.
- Ne pas attribuer ces échecs au correctif en cours ni les compter comme régression.

## Étape 8 — Porte de sortie

### Hygiène des caches

1. Prendre un instantané horodaté avant toute suppression :

```bash
find . -name "*.pyc" -printf "%TY-%Tm-%Td %TH:%TM %p\n" | sort
```

2. Identifier les fichiers créés pendant la fenêtre de la session et appartenant aux modules exécutés.
3. Supprimer par chemins explicites, jamais par `rm -rf __pycache__`.
4. Conserver les `.pyc` plus anciens et ceux d'une autre version (`cpython-312` à côté de `cpython-314`), souvent produits par une session concurrente.

Utiliser `-B` pendant les sondes évite d'en créer de nouveaux. La liste à supprimer se construit depuis l'instantané, pas depuis un glob.

### Checklist

- [ ] Modules ciblés verts ensemble, pas seulement séparément.
- [ ] Port re-liable par `socket.bind` après la classe.
- [ ] Sonde d'ordre d'import : absent à l'import, présent après `setenv`.
- [ ] Rejeu de découverte avec variable absente au démarrage du processus.
- [ ] `-W error::ResourceWarning` sans aucun avertissement.
- [ ] Chaque échec restant classé et justifié ; résidus listés.
- [ ] Aucun seuil modifié.
- [ ] Seuls les caches créés par la session supprimés ; versions et fenêtres antérieures conservées.

## Modèle de rapport

| Test | Catégorie | Preuve | Correctif | Re-vérification | Résidu |
|---|---|---|---|---|---|
| `tests.test_x::test_06` | Ordre d'import | 401 en découverte, vert seul ; constante vide à l'import | lecture à chaque requête + patch d'environnement | sonde + rejeu sans clé | aucun |
| `tests.test_y::test_a` | Périmètre pollué | chemins `depot_etranger/...` | aucun | repro isolé | à traiter par l'ayant droit |

Conclure « corrections appliquées et vérifiées localement » seulement si la porte de sortie est entièrement passée ; sinon lister explicitement les échecs résiduels et leur cause.

Séparer les preuves observées (sortie brute conservée) des conclusions déclarées (résumé sans sortie correspondante) ; ne pas présenter une méthode non exécutée comme rejouée.

## Pièges

| Piège | Conséquence | Parade |
|---|---|---|
| Constante lue à l'import | échec seulement en découverte | fonction lue à chaque appel |
| Test qui patche la constante | valide l'ordre, pas la sécurité | patcher `os.environ` |
| `setdefault` au niveau module d'un test | fuite d'environnement vers les autres tests | `mock.patch.dict` local ; ne pas dépendre de la fuite |
| `setdefault` alors que la variable est exportée vide | la valeur vide reste | `get(...) or "clé_test"` puis réassignation explicite |
| Assertion sur une constante importée | teste l'ordre d'import, pas la requête | asserter avec la valeur locale du test |
| `server_close()` après `arreter()` | double fermeture inutile | fermer uniquement dans `arreter()` |
| Import supprimé car « inutilisé » | `NameError` dans le test de repli | chercher `mock.patch.object` avant suppression |
| Assertion mise à jour avant exécution | le test décrit une fiction | exécuter l'artefact d'abord |
| `ResourceWarning` filtré | socket réellement fuité | `shutdown()` + `server_close()` |
| Suite complète en avant-plan | bloque des heures | arrière-plan + journal |
| `python` alias Microsoft Store | code 49 | `py -3` |

## Ressources

- `references/modeles-correctifs.md` — modèles avant/après pour l'ordre d'import, l'isolation des tests, le cycle de vie du serveur et la mise à jour d'assertion.
- `references/cas-passerelle-mizan-2026-10-27.md` — dossier de preuve complet : 272 tests, sept échecs triés, correctifs et limites de preuve.
