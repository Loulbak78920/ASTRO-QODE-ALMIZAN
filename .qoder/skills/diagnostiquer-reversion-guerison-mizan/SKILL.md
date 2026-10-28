---
name: diagnostiquer-reversion-guerison-mizan
description: "Diagnostiquer et arrêter une réversion de guérison Al-Mizan : une édition récente est écrasée par la copie A231 (`_AL_MIZAN_COPIE_SOI/courante`), souvent avec un mtime ancien car `shutil.copy2` le préserve, d'où un `ImportError: cannot import name` ou des tests rouges sans fichier récent. Utiliser scripts/verifier_reversion.py en lecture seule pour comparer live vs copie par zone (code/actes/objectifs/memoire_aq), lire le journal A232, classer PERTE/DERIVE/CHURN, réappliquer l'édition, rafraîchir la sauvegarde, corriger l'ordre A231 sous garde et prouver `sain True` deux fois avec `JOURNAL_CODE_GUERISONS=0`. Après une suite longue, 146 écarts limités à actes/objectifs/memoire_aq avec zéro fichier code se règlent par une sauvegarde de référence, pas par une restauration. 中文触发：旧副本覆盖新代码、导入名消失、自愈还原旧版本、长套件后 146 个差异、基线刷新、objectifs 计划文件 churn。English: Al-Mizan healing reversion, stale self-copy restore, ImportError after edit, post-suite baseline refresh, A232 integrity journal."
---

# Diagnostiquer une réversion de guérison — Al-Mizan A231/A232

## Quand utiliser

- Un fichier `.py` modifié aujourd'hui a repris un contenu ancien, ou son mtime
  est antérieur à l'édition.
- `ImportError: cannot import name 'X' … Did you mean: 'Y'?` après une édition
  qui était valide avant.
- Des tests deviennent rouges sans fichier récemment modifié.
- `detecter_alterations()` reste `sain False` avec un petit nombre d'écarts qui
  réapparaissent après chaque `sauvegarder_soi`.
- Après une suite longue, `sain False` avec des écarts limités à
  actes/objectifs/memoire (`code_altere []`).
- Il faut distinguer un vrai écart de code d'un churn normal des actes et des
  miroirs `memoire_aq`.

## Quand ne pas utiliser

- Nettoyer les archives `historique/<stamp>` et le scan A141 après un rejeu de
  tests : `nettoyer-effets-de-bord-tests-conscience`.
- Trier une suite `unittest discover` qui échoue alors que les modules ciblés
  passent : `triager-echecs-suite-unittest-decouverte`.
- Extraire les preuves brutes d'une session Qoder : `extraire-preuves-session-qoder`.
- Auditer les écritures implicites d'une vérification « lecture seule » :
  `verifier-effets-de-bord-verification-lecture-seule`.
- Valider la forme d'un Skill ou d'un livrable : `skill-file-qa`,
  `verifier-livrables-csv-html-windows-fr`.

## Contrat non négociable

1. **Lire avant d'écrire.** Constater par SHA-256, pas par mtime.
2. **Jamais restaurer le live depuis `courante`.** La copie est en retard par
   construction ; c'est elle qui a causé la réversion.
3. **Diagnostic en lecture seule.** `scripts/verifier_reversion.py` n'importe
   jamais `conscience_logique` : un import peut déclencher `verifier_et_guerir`.
4. **Zones STOP.** Ne jamais écrire ni restaurer dans `horloge_noyau/` ou
   `secrets/`; ne jamais afficher de secret.
5. **Code différent = bloquant** (`RESULT DERIVE`, exit 1). Actes et miroirs
   différents = churn attendu (`RESULT CHURN`, exit 0) sauf `--strict`.
6. **Fichier absent du live = perte** (`RESULT PERTE`, exit 1) : le recréer
   avant tout cycle, sinon la guérison le restaurera depuis la copie.
7. **Ne jamais réécrire ni tronquer le journal A232**
   (`actes/_guerison_integrite_journal.jsonl`). Filtrer avec `--since`.
8. **Correction A231 seulement sous garde** : exactement les fichiers d'acte
   A231 flaggés, `CODE=0`, copie en retard d'un acte. Sinon STOP et qualifier.
9. **Deux passes de clôture**, pas une : `sain True` deux fois de suite.
10. **`JOURNAL_CODE_GUERISONS=0`** sur la fenêtre postérieure à la correction.
11. **A225 / honnêteté** : pas de scellage tant que l'état est bancal ; ne pas
    déclarer un mécanisme réparé sans sortie observée.

## Symptômes et première lecture

| Symptôme | Cause probable | Preuve à produire |
|---|---|---|
| nom importé disparu du module | couple `__init__.py` + module restaurés séparément | `CLE=… ETAT=DIFF ZONE=code` sur les deux |
| mtime d'hier sur un fichier édité aujourd'hui | `copy2` a recopié l'ancien mtime | `MTIME_LIVE` < date d'édition |
| tests rouges, `find -newermt` vide | guérison déjà passée | rafale `guerison` dans le journal |
| 2 écarts A231 après chaque sauvegarde | acte écrit après la copie | ordre A231 = `False` (étape 5) |
| 60+ écarts actes/memoire, `CODE=0` | churn des cycles | `RESULT CHURN`, exit 0 |
| 146 écarts après une suite longue, `CODE=0` | actes, plans `_*` et miroirs réécrits | `zones {actes, objectifs, memoire_aq}`, `code_altere []` (étape 5 bis) |

## Étape 1 — Constater sans écrire

Depuis la racine du dépôt :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
py -3 -B "C:/Users/Administrateur/.qoder/skills/diagnostiquer-reversion-guerison-mizan/scripts/verifier_reversion.py" \
  --journal 20 --since "2026-10-27T14:50:00Z"
```

Le script compare chaque fichier protégé au SHA-256 de la copie et affiche, par
écart : `CLE`, `ETAT` (`DIFF` ou `ABSENT_LIVE`), `ZONE`
(`code|actes|memoire_aq`), les deux préfixes SHA-256 et les deux mtimes. Le
projet distingue une quatrième zone, `objectifs` : les fichiers `actes/_*.json`
(plans et états). Le script les compte dans `ACTES` ; c'est un churn, jamais du
code. Puis une ligne de synthèse `VERIFIES=… SAME=… NOUVEAUX=… REVERSIONNABLES=… CODE=…
ACTES=… MEMOIRE=…`, et, avec `--journal`, `JOURNAL_GUERISONS=…
JOURNAL_CODE_GUERISONS=… SINCE=…` suivi des événements.

Options utiles : `--chemin` (répétable, restreint la vérification), `--tout`
(affiche aussi `SAME` et `ABSENT_COPIE`), `--strict` (churn bloquant),
`--systeme` et `--copie` si l'arborescence diffère.

## Étape 2 — Qualifier

| Résultat | Exit | Sens | Suite |
|---|---|---|---|
| `RESULT OK` | 0 | tout est identique | rien à réparer, ne pas toucher |
| `RESULT CHURN n (…code intègre)` | 0 | actes/memoire réécrits par les cycles | rapporter, ne pas « corriger » |
| `RESULT DERIVE n code=k churn=c` | 1 | `k` fichiers `.py` divergent | étape 3 |
| `RESULT PERTE n` | 1 | `n` fichiers présents dans la copie manquent au live | étape 4 |
| `RESULT USAGE …` | 2 | racine, module ou copie absents | corriger le chemin |

`JOURNAL_CODE_GUERISONS` compte les guérisons de `.py` (hors `actes/` et
`memoire_aq/`) dans la fenêtre : c'est l'indicateur direct d'une réversion de
code.

## Étape 3 — Réparer un écart de code (DERIVE)

1. Identifier l'édition perdue : comparer le `SHA_LIVE` au contenu édité, pas à
   la copie.
2. Réappliquer l'édition **sur le fichier live** (c'est la source de vérité).
3. Si le module importe un nom défini dans un autre fichier restauré,
   réappliquer les deux éditions et vérifier l'import avant d'aller plus loin.
4. Rafraîchir empreintes et copie :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
PYTHONIOENCODING=utf-8 py -3 -B -c "
from conscience_logique.sauvegarde_soi import sauvegarder_soi, detecter_alterations
r = sauvegarder_soi(archiver=True)
print('saved', r.ok, r.horodatage)
d = detecter_alterations()
print('sain', d.get('sain'), 'alterations', d.get('nb_alterations'))
for a in d.get('alterations', [])[:10]:
    print(' -', a.get('cle'), a.get('type'), a.get('guerir'))
"
```

`archiver=True` crée une archive `historique/<stamp>` : c'est attendu, et sa
suppression éventuelle relève de `nettoyer-effets-de-bord-tests-conscience`.

## Étape 4 — Rétablir une perte (PERTE)

Un fichier absent du live sera restauré par la copie au prochain cycle. Avant
cela :

1. Si le contenu attendu est connu (édition, sauvegarde locale), le recréer.
2. Si le fichier a été **supprimé volontairement**, retirer aussi sa copie dans
   `_AL_MIZAN_COPIE_SOI/courante` (et son entrée d'index si elle existe), sinon
   la guérison le fera revenir.
3. Ne jamais restaurer un fichier **modifié** depuis la copie : étape 3.

## Étape 5 — Corriger l'ordre A231 (sous garde)

Appliquer uniquement si **toutes** ces conditions sont réunies :

- le diagnostic ne montre que les fichiers d'acte A231 (acte + miroir) comme
  `DIFF`, avec `CODE=0` ;
- après une sauvegarde, ils réapparaissent `hash_different` à chaque passe ;
- la copie contient l'acte de la sauvegarde **précédente**, pas la courante.

Sinon STOP : un autre écrivain ou une autre cause existe, et déplacer du code
masquerait le vrai problème.

Contrôle d'ordre, sans modification :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B -c "
import pathlib
t = pathlib.Path('conscience_logique/sauvegarde_soi.py').read_text(encoding='utf-8')
corps = t[t.index('def sauvegarder_soi'):]
i_acte = corps.index('_ecrire_json(CHEMIN_ACTE, acte)')
i_copie = corps.index('_copier_arbre(')
print('ORDRE_A231_ACTE_AVANT_COPIE', i_acte < i_copie)
"
```

Si `False`, écrire l'acte **avant** la copie en trois gestes, sans changer son
contenu :

1. Calculer une seule fois `horodatage = _iso()` et `message = (…)` en tête de
   fonction, juste après `stamp = …`.
2. Écrire `CHEMIN_ACTE` puis `CHEMIN_MIROIR` avec cet `acte`, avant la section
   `# 1) Module code + actes locaux` qui contient `_copier_arbre`.
3. Supprimer le bloc tardif (acte + miroir) ; laisser `enregistrer_empreintes_saines()`
   en fin de fonction.

Le `RapportSauvegardeSoi` doit réutiliser les mêmes `horodatage` et `message` :
deux appels à `_iso()` produiraient un acte et un rapport datés différemment, et
le contrôle A232 signalerait de nouveau un écart. Puis relancer le contrôle
(`True`) et une double passe de clôture. Détail du mécanisme :
`references/mecanisme-a232.md`.

## Étape 5 bis — Rafraîchir la baseline après une suite longue

Une suite longue (26 tests, 22 121 s = 6 h 08) réécrit la pile d'actes et les
plans `_*`. À la fin, `detecter_alterations()` peut rendre `sain False` avec
146 écarts. Ce n'est une régression que si un `.py` est flaggé.

Première lecture sans importer le paquet (étape 1) : attendu `CODE=0` et
`RESULT CHURN n` (le script compte les `objectifs` dans `ACTES`). Si `CODE` n'est
pas nul, aller à l'étape 3 ; la ventilation ci-dessous ne sert qu'à confirmer
les zones avant le rafraîchissement :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B -c "
from conscience_logique.sauvegarde_soi import detecter_alterations
d = detecter_alterations()
zones, code = {}, []
for a in d.get('alterations', []):
    zones[a.get('zone')] = zones.get(a.get('zone'), 0) + 1
    if a.get('zone') == 'code':
        code.append(a.get('cle'))
print('sain', d.get('sain'), 'alterations', d.get('nb_alterations'))
print('zones', zones)
print('code_altere', code)
"
```

- `code_altere []` et zones incluses dans `{actes, objectifs, memoire_aq}` →
  rafraîchir la référence, pas « réparer » :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B -c "
from conscience_logique.sauvegarde_soi import sauvegarder_soi, detecter_alterations
r = sauvegarder_soi(archiver=True)
d = detecter_alterations()
print('saved', r.ok, 'sain', d.get('sain'), 'alterations', d.get('nb_alterations'))
"
```

- Attendu : `saved True sain True alterations 0`, puis batterie ciblée rejouée
  (58 tests, ~8 s).
- `code_altere` non vide → étape 3 : un `.py` flaggé après une suite longue est
  une réversion réelle, pas du churn.
- `archiver=True` crée `historique/<stamp>` : son éventuel nettoyage relève de
  `nettoyer-effets-de-bord-tests-conscience`.

## Étape 6 — Clore et rapporter

Critères de clôture, tous exigés :

1. Deux `sauvegarder_soi` consécutifs rendent `sain True` avec `alterations 0`.
2. Le script rend `CODE=0` et `JOURNAL_CODE_GUERISONS=0` sur la fenêtre
   postérieure à la correction.
3. Les tests ciblés du module repassent (par exemple 58 tests ciblés, ~8 s).
   Ne pas lancer `unittest discover` complet (~118 min) pour ce diagnostic.
4. Le churn actes/objectifs/memoire résiduel est rapporté comme attendu, avec
   ses compteurs, sans être « réparé ».
5. Après une suite longue : `code_altere []`, baseline rafraîchie (étape 5 bis),
   `sain True`, puis batterie ciblée rejouée.

Rapport minimal :

| Élément | Valeur |
|---|---|
| Symptôme et première observation (UTC) | … |
| `CLE`/`ETAT`/`ZONE` des écarts de code | … |
| Cause (réversion / ordre A231 / autre) | … |
| Édition réappliquée (fichiers) | … |
| Double passe `sain` | … / … |
| `JOURNAL_CODE_GUERISONS` après correction | 0 |
| Churn résiduel `ACTES`/`OBJECTIFS`/`MEMOIRE` | … / … / … |
| `zones` et `code_altere` après suite longue | … / … |
| Tests ciblés | N exécutés, OK |

## Pièges

- `find -newermt` ne prouve rien ici : `copy2` conserve l'ancien mtime.
- Un mtime ancien ne signifie pas « fichier ancien » : vérifier le SHA-256.
- Le journal A232 dépasse 16 Mo ; ne jamais le charger entièrement ni le
  tronquer. Le script n'en lit que la queue.
- Une ligne de journal tronquée est normale : elle est ignorée, pas « réparée ».
- La console Windows (cp1252) casse les accents : le script émet de l'ASCII
  strict ; ne pas remplacer cette sortie par des `print` bruts.
- `python` peut être l'alias Microsoft Store : utiliser `py -3`.
- Un clone étranger dans le périmètre fausse les comptages de scan et les
  suites de conscience ; ce n'est pas une réversion.
- Un fichier neuf (`ABSENT_COPIE`) ne sera jamais guéri : son absence de la
  copie n'est pas un problème, sauf s'il doit être restauré un jour.

## Ressources

- `scripts/verifier_reversion.py` — comparaison lecture seule (stdlib, ASCII,
  317 lignes, SHA-256 `6ec3fa60631dfbeffaf23b4f89d048142bbfc5f89ce0712c6926ea82862cfdf2`).
- `references/mecanisme-a232.md` — périmètre protégé, détection, guérison,
  déclencheurs, churn, ordre A231.
- `references/cas-2026-10-27.md` — chronologie vérifiée de l'incident et
  contrôles de clôture réellement exécutés.
