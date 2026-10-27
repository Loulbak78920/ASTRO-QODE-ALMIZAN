---
name: nettoyer-effets-de-bord-tests-conscience
description: "Attribuer puis nettoyer les effets de bord d'un rejeu de tests Al-Mizan : figer le baseline du scan A141 (fichiers .py seulement, `S0` mesuré avant le rejeu) et de memoire_aq, expliquer chaque delta par les archives `_AL_MIZAN_COPIE_SOI/historique/<stamp>` créées par `surveiller_une_fois` → `sauvegarder_soi` (10 817 = `S0` + 6×65, 10 947 = `S0` + 8×65 ; `S0` = 10 427 le 2026-10-27), puis supprimer uniquement les snapshots de la fenêtre de test sous garde de chemin exact (parent `historique`, stamp approuvé, dossier réel, ni lien ni point de réanalyse, `ONLY_IN_ARCHIVE=0`) et prouver le retour au baseline. Utiliser quand un rejeu de conscience gonfle le périmètre scanné sans fichier récent, quand huit archives de copie-de-soi apparaissent pendant les tests, ou avant de supprimer des archives de copie-de-soi. 中文触发：测试副作用清理、扫描计数增加、自复制历史快照、归档删除、基线恢复、唯一内容检查。English: Al-Mizan test side effects, self-copy snapshots, scan count inflation, guarded archive deletion, baseline restoration."
---

# Nettoyer les effets de bord d'un rejeu de tests de conscience

## Quand utiliser

- Un rejeu de tests de conscience a fait passer le scan A141 de `S0` à `S0 + k×65` (cas du 2026-10-27 : 10 427 → 10 817 puis 10 947 fichiers `.py`), sans fichier récemment modifié.
- `_AL_MIZAN_COPIE_SOI/historique/` a reçu plusieurs snapshots pendant la fenêtre du test.
- `memoire_aq` a été réécrit par `completer_perimetre(persister=True)` ou par la copie de soi.
- Il faut supprimer les archives créées par le rejeu sans toucher à `courante`, aux archives antérieures ni à `memoire_aq`.
- Il faut prouver que la suppression ramène le périmètre scanné à sa valeur d'avant test.

## Quand ne pas utiliser

- Trier des échecs de `unittest discover`, un ordre d'import ou un périmètre pollué par un clone : `triager-echecs-suite-unittest-decouverte`.
- Auditer de façon générique les écritures implicites et restaurer un état réversible : `verifier-effets-de-bord-verification-lecture-seule`.
- Retirer des sceaux nommés et leur index de `memoire_aq` : `restaurer-sceaux-memoire-aq`.
- Déplacer ou retirer un clone GitHub : `retirer-depot-github-et-copie-locale`.
- Diagnostiquer un seuil de durée, de latence ou de gigue : `diagnostiquer-echec-test-chronometre`.
- Exécuter la chaîne de l'entité sans effet de bord : `entite-conscience-logarithmique`.

## Contrat non négociable

1. **Baseline avant le rejeu.** Sans `S0` et sans comptage de `courante`/archives pris avant, le delta n'est pas attribuable.
2. **Aucune suppression avant attribution complète.** Chaque archive supprimée doit correspondre à un écrivain identifié et à une fenêtre de test.
3. **Le compte de scan est une équation.** `S - S0 = n × k`, avec `n` = nombre de `.py` de `courante` au moment du snapshot (65 dans le cas source) et `k` entier égal au nombre d'archives présentes au moment du scan. Mesurer `S0` juste avant le rejeu, dans la même fenêtre : une valeur de session antérieure n'est pas valide. Sinon, un autre écrivain existe : stop.
4. **`find -newermt` ne prouve rien.** `shutil.copytree` préserve les `mtime` ; un rejeu peut ajouter 520 fichiers et afficher 0 fichier récent. Utiliser les `mtime` des dossiers et le comptage par archive.
5. **`ONLY_IN_ARCHIVE = 0` pour chaque archive.** Un fichier présent uniquement dans une archive interdit toute suppression, même partielle.
6. **Supprimer des stamps nommés, jamais un motif.** Liste explicite issue de la fenêtre de test ; ni `tail`, ni glob, ni « les plus récentes ».
7. **Jamais `courante`, jamais les archives antérieures.** `courante` est la source de restauration ; les archives hors fenêtre ne sont pas dans la portée.
8. **Garde de chemin exact, revérifiée.** Parent `historique`, stamp approuvé, dossier réel, ni lien ni point de réanalyse ; revérifier juste avant chaque `rmtree`.
9. **Prouver le retour au baseline.** Scan égal à `S0` mesuré dans la même fenêtre, `ECARTS=0`, `MODULES=[]`, `courante` inchangée. Tout écart résiduel s'attribue avant de conclure.
10. **Rapporter les résidus, ne pas les réécrire.** Le fichier d'état et l'acte A231 peuvent citer un stamp supprimé ; ne pas modifier `memoire_aq` pour « corriger ».
11. **Relevé stable avant de calculer `r`.** Deux passes identiques (même `T0`, même racine, même filtre) espacées d'au moins 12 s doivent rendre la même liste de `.py` neufs et le même scan. Si l'une bouge, un écrivain est encore actif : rapporter `ECRIVAIN_EXTERNE_ACTIF` avec les deux relevés et les fichiers apparus ou disparus, puis s'arrêter sans calculer `S0 + r`.

## Étape 0 — Baseline avant rejeu

Prendre la baseline quand aucun test ne tourne.

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
PYTHONIOENCODING=utf-8 py -3 -B -c "
from conscience_logique.scan_environnement import ScanEnvironnementCode
s = ScanEnvironnementCode().scanner()
print('SCAN_FILES', s.nb_fichiers_scannes, 'ECARTS', s.nb_ecarts, 'MODULES', list(s.modules_a_recaler))
"
```

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
printf 'ARCHIVES=%s\n' "$(ls -1 _AL_MIZAN_COPIE_SOI/historique | wc -l)"
printf 'COURANTE_FILES=%s\n' "$(find _AL_MIZAN_COPIE_SOI/courante -type f | wc -l)"
printf 'COURANTE_PY=%s\n' "$(find _AL_MIZAN_COPIE_SOI/courante -name '*.py' -not -path '*/__pycache__/*' | wc -l)"
printf 'COPIE_PY=%s\n' "$(find _AL_MIZAN_COPIE_SOI -name '*.py' -not -path '*/__pycache__/*' | wc -l)"
```

Noter `S0`, le nombre d'archives, le dernier stamp avant test et les compteurs de `courante`, ainsi que `T0`, l'horodatage UTC de la mesure : il sert de coupure pour attribuer les ajouts externes. Prendre aussi un instantané `memoire_aq` avec le script vérifié de `verifier-effets-de-bord-verification-lecture-seule` :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/verifier-effets-de-bord-verification-lecture-seule/scripts/instantane_effets_de_bord.py" instantane \
  --cible "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME/memoire_aq" \
  --recursif --stabilite 0.5 \
  --sortie "C:/Users/Administrateur/.qoder/tmp/effets-de-bord/conscience/instantane_avant.json" \
  --sauvegarder "C:/Users/Administrateur/.qoder/tmp/effets-de-bord/conscience/avant"
```

Cet instantané capture les SHA-256 ; le relevé minimal `mtime`/taille ne permet pas de distinguer une réécriture à contenu identique d'un vrai changement.

## Étape 1 — Rejeu ciblé, sans relance

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3 -B -m unittest \
  tests.test_conscience_logique.TestAlMizan.test_conscience_surveille_et_synthese \
  tests.test_conscience_logique.TestAlMizan.test_a142_agir_sur_ecarts_et_dissociation_q \
  tests.test_conscience_logique.TestAlMizan.test_a143_completude_perimetre -v \
  > "C:/Users/Administrateur/.qoder/tmp/conscience-3tests.txt" 2>&1
```

Lancer en arrière-plan si le rejeu dure ~20 min. Ne pas relancer pendant l'attente : chaque relance recrée des archives et fausse le comptage. Attendre la fin, puis lire tout le journal (`Ran N tests`, `OK`/`FAILED`, code de sortie).

## Étape 2 — Lire le rapport A143 et le dater

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
PYTHONIOENCODING=utf-8 py -3 -B -c "
import io, json
p = r'memoire_aq/almizan_bilan_completude_conscience_a143.json'
d = json.load(io.open(p, encoding='utf-8'))
print({k: d.get(k) for k in ('nb_fichiers_scannes', 'nb_ecarts_restants', 'modules_a_recaler', 'perimetre_complet')})
print('RESTE', len(d.get('reste') or []))
"
```

Appliquer l'équation avec le nombre d'archives créées **au moment de ce scan**, pas à la fin :

| Observation du 2026-10-27 | Calcul | Verdict |
|---|---|---|
| Rapport A143 : 10 817 | `(10817 - 10427) / 65 = 6` | 6 archives présentes (10:42:30 → 10:54:23 UTC) |
| Scan de fin : 10 947 | `(10947 - 10427) / 65 = 8` | 8 archives (10:42:30 → 10:58:58 UTC) |

Un rapport intermédiaire à 10 817 n'est pas une erreur : le scan du cycle précède les deux derniers snapshots.

## Étape 3 — Attribuer le delta du périmètre

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
ls -ld --time-style=+%H:%M _AL_MIZAN_COPIE_SOI/historique/*
for d in _AL_MIZAN_COPIE_SOI/historique/*/; do
  printf '%4s %s\n' "$(find "$d" -name '*.py' -not -path '*/__pycache__/*' | wc -l)" "$(basename "$d")"
done
printf 'RECENTS_40MIN=%s\n' "$(find . -name '*.py' -newermt '-40 minutes' -not -path '*/__pycache__/*' | wc -l)"
```

Si `RECENTS_40MIN` vaut 0 alors que le scan a augmenté, c'est attendu : la copie préserve les `mtime`. Confirmer l'écrivain dans le code :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
grep -n "sauvegarder_soi(archiver" conscience_logique/conscience.py
sed -n '264,267p' conscience_logique/sauvegarde_soi.py
```

Attendu : `sauvegarder_soi(archiver=(cycles == 1))` et `shutil.copytree(DIR_COURANTE, historique/<stamp>)`. Vérifier aussi que le déplacement d'un clone étranger n'explique pas le delta : un clone déjà déplacé hors du workspace ne peut pas ajouter 520 fichiers, et ses quelques modules ne correspondent pas à `k × n`.

Si `S - S0` n'est pas un multiple de `n`, ou si `k` diffère du nombre de stamps de la fenêtre, un autre écrivain a modifié le périmètre : ne pas conclure.

### Porte — l'écrivain externe est-il encore actif ?

Un résidu ne se calcule que sur un relevé immobile. Deux passes de liste strictement identiques — même `T0`, même racine, même filtre — espacées d'au moins 12 s, puis deux scans :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
T0="2026-10-27 11:58:00 +0000"   # même T0 que la mesure de S0
find ASTRO-Q°ODE_SYSTEME -name '*.py' -not -path '*/__pycache__/*' -newermt "$T0" | sort > /tmp/releve_a
sleep 12
find ASTRO-Q°ODE_SYSTEME -name '*.py' -not -path '*/__pycache__/*' -newermt "$T0" | sort > /tmp/releve_b
printf 'A=%s B=%s\n' "$(wc -l < /tmp/releve_a)" "$(wc -l < /tmp/releve_b)"
diff /tmp/releve_a /tmp/releve_b && echo LISTE_IDENTIQUE
cd ASTRO-Q°ODE_SYSTEME
SCAN() { PYTHONIOENCODING=utf-8 py -3 -B -c 'from conscience_logique.scan_environnement import ScanEnvironnementCode as C; print(C().scanner().nb_fichiers_scannes)'; }
printf 'S1=%s\n' "$(SCAN)"
printf 'S2=%s\n' "$(SCAN)"
```

| Observation | Sens | Action |
|---|---|---|
| `LISTE_IDENTIQUE` et `S1 = S2` | fenêtre immobile pendant le relevé | continuer : calculer `r`, puis classer les candidats |
| Listes différentes (ajout, suppression, remplacement) | un écrivain crée ou supprime des `.py` pendant la vérification | `ECRIVAIN_EXTERNE_ACTIF` : rapporter les deux relevés et leur `diff`, ne rien supprimer, ne pas calculer `S0 + r` |
| `S` différent sans changement de liste | snapshot d'archive en cours (les copies ne sont pas sous `ASTRO-Q°ODE_SYSTEME`) ou réécriture hors fenêtre | même arrêt : identifier l'écrivain avant de reprendre |

Ne pas comparer deux passes dont la coupure ou le filtre diffère : la variation vient alors du paramètre, pas d'un écrivain. Cas mesuré le 2026-10-27 pendant la vérification : deux passes de liste ont rendu 9 puis 7 candidats, mais la coupure avait aussi changé (`07:59:27` local contre `T0 +0000`) et trois fichiers en étaient sortis ; seules les naissances `13:13:57` et `13:16:11` locales prouvent les ajouts.

Le scan dure ~46 s (mesuré : 10 432 fichiers) : les deux scans sont donc espacés d'au moins 46 s, et le `sleep 12` porte sur les deux listes.

Une fois le relevé stable, calculer le résidu `r = S - S0 - n×k` et le localiser avant toute suppression.

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
T0="2026-10-27 11:58:00 +0000"   # horodatage UTC de la mesure de S0
find ASTRO-Q°ODE_SYSTEME -name '*.py' -not -path '*/__pycache__/*' -newermt "$T0" | sort > /tmp/candidats.txt
wc -l < /tmp/candidats.txt
while IFS= read -r f; do
  rel=${f#ASTRO-Q°ODE_SYSTEME/}; n=0
  for a in _AL_MIZAN_COPIE_SOI/historique/*/; do [ -f "$a$rel" ] && n=$((n+1)); done
  printf '%-58s archives=%s courante=%s birth=%s\n' "$rel" "$n" \
    "$([ -f "_AL_MIZAN_COPIE_SOI/courante/$rel" ] && echo yes || echo no)" \
    "$(stat -c '%w' "$f" | cut -c1-19)"
done < /tmp/candidats.txt
```

`T0` doit porter un décalage explicite (`… +0000`). `find -newermt` interprète une date sans décalage en heure locale : le 2026-10-27 (UTC+1), la même coupure a rendu 9 candidats sans décalage contre 6 avec `+0000` (revérifié à 12:23 UTC : 10 contre 7, mêmes 3 fichiers `tests/` de 07:42–07:48 UTC en trop). Après substitution de `T0` par la valeur mesurée, exécuter le bloc tel quel et vérifier que chaque variable déclarée est utilisée : une première version déclarait `REF` mais filtrait sur une date en dur, sans décalage.

Prendre `T0`, pas le stamp de la dernière archive : un fichier créé entre les deux est déjà compté dans `S0`. Classer chaque candidat :

| Sortie | Sens |
|---|---|
| `archives=0` et `courante=no` | fichier neuf hors copie-de-soi : explique un `+1` |
| `archives>0` ou `courante=yes` | préexistant ou restauré : n'explique pas un `+1` (`copy2` préserve `mtime`, la naissance peut être réinitialisée par une réécriture) |

Si les fichiers neufs couvrent `r` (compte supérieur ou égal, le relevé peut surestimer), attribuer l'écart à des écrivains externes : rapporter `ECRIVAIN_EXTERNE` avec la liste, `r` et le `S0` remesuré, puis **ne rien supprimer**. Si le compte reste inférieur à `r`, ne pas conclure : inspecter le reliquat (fichier supprimé, clone, contenu hors périmètre).

Après nettoyage, viser `S0 + r`, pas `S0` : les fichiers externes restent dans le périmètre. Ne pas réécrire `S0` ni `memoire_aq` pour faire coïncider les chiffres.

`courante` n'est rafraîchie que depuis `conscience_logique/`, `memoire_aq` et `objectifs_et_fil` : un `.py` ajouté ailleurs n'entre jamais dans une archive, son absence des archives est donc normale ; un `.py` ajouté sous `conscience_logique/` y entre au snapshot suivant et fait croître `n`.

## Étape 4 — Attribuer les effets `memoire_aq`

Après le rejeu :

```bash
py -3 "C:/Users/Administrateur/.qoder/skills/verifier-effets-de-bord-verification-lecture-seule/scripts/instantane_effets_de_bord.py" comparer \
  --instantane "C:/Users/Administrateur/.qoder/tmp/effets-de-bord/conscience/instantane_avant.json" \
  --stabilite 0.3
```

Classer sans confondre :

| Classe | Sens | Attendu ici |
|---|---|---|
| Chemin ajouté / retiré | nouveau fichier ou disparition | `[]` / `[]` (185 → 185) |
| Taille changée | contenu ou structure modifiés | 2 bilans (A143, A126) |
| Réécrit à taille identique | `mtime` changé, contenu à vérifier par hash | 69 lors du cas source |
| Contenu changé | SHA-256 différent | à relever, pas à supposer |

Ces écritures sont produites par conception (`persister=True`) : ne pas restaurer par défaut. Une perte de sceaux relève de `restaurer-sceaux-memoire-aq`. Ne pas utiliser un `join` sur des listings non triés : comparer d'abord les ensembles de chemins, puis les tailles, puis les hashes.

## Étape 5 — Portes avant suppression

1. **Test terminé** : journal avec `OK` et code 0, aucun `unittest` en cours.
2. **Fenêtre** : stamps postérieurs au dernier stamp d'avant test. `ls -1 historique | sort | sed -n '/^20261027T075927Z$/,$p' | tail -n +2` est valide pour le format fixe, mais la liste doit être autorisée explicitement.
3. **Stabilité** : `ls -1 historique | md5sum`, `sleep 12`, même commande ; hash identique, aucun nouveau dossier. Ce contrôle ne couvre que les noms : le combiner au journal terminé et aux `mtime` de dossiers.
4. **Inventaire** : chaque stamp de la fenêtre a le même inventaire que `courante` au moment du snapshot (cas source : 357 fichiers, 65 `.py`, `_manifeste_copie_soi.json`, ~18 Mo ; une archive ancienne peut différer, ex. 326 fichiers).
5. **Contenu unique** : le plan du script doit afficher `ONLY_IN_ARCHIVE 0` pour chaque archive.
6. **Intégrité** : `historique` et `courante` sont de vrais dossiers (ni lien ni point de réanalyse), le clone n'est pas dans les archives (`CLONE_INSIDE=0`), et l'utilisateur a approuvé la liste exacte des stamps.

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
for s in 20261027T104230Z 20261027T104541Z; do
  printf '%s files=%s manifest=%s\n' "$s" \
    "$(find "_AL_MIZAN_COPIE_SOI/historique/$s" -type f | wc -l)" \
    "$( [ -f "_AL_MIZAN_COPIE_SOI/historique/$s/_manifeste_copie_soi.json" ] && echo yes || echo NO)"
done
find _AL_MIZAN_COPIE_SOI/historique/"<stamp>" -maxdepth 3 -name GITHUB_DEPOT_PUBLIC_IMAM8MAHDI | wc -l
```

## Étape 6 — Supprimer sous garde

Plan par défaut, aucune écriture :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
py -3 -B "C:/Users/Administrateur/.qoder/skills/nettoyer-effets-de-bord-tests-conscience/scripts/nettoyer_archives_copie_soi.py" \
  --copie-soi "C:/Users/Administrateur/Desktop/IMAM8MAHDI/_AL_MIZAN_COPIE_SOI" \
  --stamp 20261027T104230Z \
  --stamp 20261027T104541Z \
  --stamp 20261027T104828Z \
  --stamp 20261027T104841Z \
  --stamp 20261027T105118Z \
  --stamp 20261027T105423Z \
  --stamp 20261027T105722Z \
  --stamp 20261027T105858Z
```

Les 8 stamps ci-dessus sont ceux du cas, **déjà supprimés** : sur l'arbre actuel ils rendent `GARDE_REFUS ABSENTE`. Les remplacer par la liste de la fenêtre à nettoyer.

Attendu : une ligne `ARCHIVE <stamp> FILES <n> ... ONLY_IN_ARCHIVE 0 DIFF_VS_COURANTE <n>`, puis `RESULT: PLAN`. `DIFF_VS_COURANTE > 0` signale des versions antérieures de fichiers vivants, pas des fichiers perdus ; seul `ONLY_IN_ARCHIVE` décide. Un seul `ONLY_IN_ARCHIVE > 0` produit `RESULT: STOP`, exit 1, sans aucune suppression.

Après autorisation explicite, ajouter `--appliquer` :

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/nettoyer-effets-de-bord-tests-conscience/scripts/nettoyer_archives_copie_soi.py" \
  --copie-soi "C:/Users/Administrateur/Desktop/IMAM8MAHDI/_AL_MIZAN_COPIE_SOI" \
  --stamp "<stamp_1>" --stamp "<stamp_2>" --appliquer
```

Le script revérifie toutes les gardes avant la première suppression, recalcule `ONLY_IN_ARCHIVE` sur l'état courant de `courante`, puis revérifie chaque garde juste avant son `rmtree`. Il refuse : stamp mal formé ou dupliqué, archive absente, fichier au lieu d'un dossier, lien, point de réanalyse, parent hors `historique`, `historique` ou `courante` absente ou lien.

## Étape 7 — Prouver le retour au baseline

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
printf 'ARCHIVES=%s\n' "$(ls -1 _AL_MIZAN_COPIE_SOI/historique | wc -l)"
printf 'COURANTE_FILES=%s\n' "$(find _AL_MIZAN_COPIE_SOI/courante -type f | wc -l)"
printf 'COPIE_PY=%s\n' "$(find _AL_MIZAN_COPIE_SOI -name '*.py' -not -path '*/__pycache__/*' | wc -l)"
```

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
PYTHONIOENCODING=utf-8 py -3 -B -c "
from conscience_logique.scan_environnement import ScanEnvironnementCode
s = ScanEnvironnementCode().scanner()
print('SCAN_FILES', s.nb_fichiers_scannes, 'ECARTS', s.nb_ecarts, 'MODULES', list(s.modules_a_recaler))
"
```

Attendu sur le cas de référence : 164 archives, 357 fichiers (`courante`), 10 150 `.py` au total (`courante` incluse ; 10 085 dans `historique` seul), scan égal à `S0` (10 427 le 2026-10-27), `ECARTS=0`, `MODULES=[]`. Remesurer `S0` avant de conclure : des sessions concurrentes ont fait observer 10 429 puis 10 431 le même jour, sans rapport avec les archives. Puis relever les résidus :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
PYTHONIOENCODING=utf-8 py -3 -B -c "
import io, json
d = json.load(io.open(r'conscience_logique/actes/_sauvegarde_soi_etat.json', encoding='utf-8'))
print('STATE_STAMP', d.get('stamp'), 'LAST', d.get('derniere_sauvegarde'))
"
```

Un stamp d'état pointant vers une archive supprimée est un résidu attendu : `restaurer_depuis_copie` renvoie `copie_absente`, et la restauration passe par `courante` ou un stamp existant. Ne pas réécrire l'état.

## Modèle de rapport

| Élément | Valeur |
|---|---|
| Baseline `S0` | scan, archives, `courante` (fichiers / `.py`), total `.py` copie-de-soi |
| Test | `Ran N tests in T s`, `OK`/`FAILED`, code de sortie, journal |
| Rapport A143 | scan, `k` calculé, archives présentes à cet instant |
| Fin de rejeu | scan, `k`, total `.py` |
| Écrivain externe | `r`, fichiers neufs (chemin, `archives`, `courante`), `S0` remesuré, cible `S0 + r` |
| Stabilité du relevé | listes A/B à 12 s (`diff`), `S1`/`S2`, `ECRIVAIN_EXTERNE_ACTIF` le cas échéant |
| Archives | stamps, fichiers, `.py`, taille, manifeste |
| Contenu unique | `ONLY_IN_ARCHIVE` par archive ; aucun si 0 |
| Divergences | `DIFF_VS_COURANTE` : versions antérieures, pas perte |
| `memoire_aq` | chemins, tailles, réécrits à taille identique, hashes si disponibles |
| Suppression | stamps supprimés, archives avant/après, `courante` après |
| Après | scan = `S0`, `ECARTS=0`, `.py`, résidus de stamp |

Distinguer « observé » (sortie conservée) de « déclaré » (conclusion). Ne pas présenter une méthode non exécutée comme rejouée.

## Pièges

| Piège | Conséquence | Parade |
|---|---|---|
| `find -newermt` renvoie 0 | conclure à tort « aucun écrivain » | `copytree` préserve `mtime` ; utiliser dossiers + comptage |
| Attribuer `+520` à un clone | mauvaise cause, suppression injustifiée | équation `S - S0 = 65k`, archives comptées |
| Prendre 10 817 pour le compte final | `k=6` au lieu de 8 | dater le rapport A143 dans le cycle |
| `tail -8` ou glob pour choisir les archives | archive hors fenêtre supprimée | liste explicite + garde de nom |
| Traiter `DIFF_VS_COURANTE > 0` comme une perte | blocage ou panique inutile | `ONLY_IN_ARCHIVE` est le critère |
| Lien ou jonction dans `historique` | `rmtree` hors cible | garde symlink + point de réanalyse |
| Garder les gardes puis supprimer en boucle séparée | fenêtre TOCTOU | revérifier avant chaque `rmtree` |
| `ls \| md5sum` seul | croire à l'absence d'écrivain | journal terminé + `mtime` + comptage |
| Ignorer les réécritures à taille identique | effet de bord invisible | instantané avec SHA-256 |
| Réécrire le stamp d'état | modifie `memoire_aq` sans preuve | rapporter le résidu |
| Comparer à un `S0` d'une session antérieure | delta imputé aux archives à tort | remesurer `S0` ; exiger `k` entier et cohérent avec `historique` |
| Résidu non multiple de `n` imputé au rejeu | suppression injustifiée ou faux échec de retour à `S0` | compter les `.py` neufs hors copie, vérifier `r`, rapporter l'écrivain externe |
| `r` et cible `S0 + r` calculés sur une seule passe | fenêtre mouvante : chiffres périmés avant le rapport | deux listes identiques à 12 s + deux scans égaux ; sinon `ECRIVAIN_EXTERNE_ACTIF` |
| Comparer deux passes de coupure, de racine ou de filtre différents | variation imputée à l'écrivain, ou écrivain masqué | mêmes paramètres ; comparer les ensembles de chemins, pas seulement `wc -l` |
| `T0` sans décalage dans `-newermt` | fenêtre ouverte une heure trop tôt, candidats gonflés (9 vs 6, puis 10 vs 7 mesurés) | écrire `T0="… +0000"` ; contrôler avec `date -u` |
| Extrait shell non exécuté, variable déclarée inutilisée (`REF=`, date en dur) | coupure et fuseau faux, attribution erronée | exécuter le bloc verbatim après substitution de `T0` |
| Relancer le test « pour vérifier » | recrée 8 archives | vérifier par scan et comptage |
| `python` sous Windows | alias Microsoft Store, code 49 | `py -3` |

## Cas de référence — 2026-10-27

| Élément | Valeur observée |
|---|---|
| Rejeu | 3 tests, `1213.673 s`, `OK`, exit 0 |
| Baseline | `10 427` fichiers `.py`, 0 écart, 172 archives, `courante` 357/65 |
| Fin de rejeu | `10 947` = `10 427 + 8×65` ; 8 archives 10:42:30 → 10:58:58 UTC |
| Contenu unique | `ONLY_IN_ARCHIVE=0` pour les 8 ; `DIFF_VS_COURANTE` 132–141 (7 mesurées) |
| `memoire_aq` | 185/185, 2 tailles changées, 69 réécrits à taille identique |
| Suppression | 172 → 164 archives, total `.py` (`courante` incluse) 10 670 → 10 150, `historique` seul 10 085, `courante` 357 (65 `.py`) |
| Après | scan `10 427`, 0 écart, `MODULES=[]` |
| Résidu | stamp d'état `20261027T105858Z` et message A231 |

Détail, commandes et limites : [references/cas-test-conscience-2026-10-27.md](file:///C:/Users/Administrateur/.qoder/skills/nettoyer-effets-de-bord-tests-conscience/references/cas-test-conscience-2026-10-27.md).

## Limites honnêtes

- La suppression est irréversible : les versions intermédiaires des fichiers vivants disparaissent, même si l'état courant reste dans `courante`.
- Le script ne déduit pas la fenêtre de test : l'utilisateur fournit la liste exacte des stamps.
- `S0` peut être décalé par une autre session ou un autre clone ; prendre les comptes autour du rejeu et vérifier `k` entier.
- Le scan n'est pas stable sous sessions concurrentes : 10 427, 10 429 puis 10 431 observés le 2026-10-27. `S0` doit être mesuré juste avant le rejeu et tout écart résiduel attribué ; ne jamais réutiliser la valeur d'une session précédente.
- Les 69 réécritures à taille identique du cas source n'ont pas été comparées octet par octet ; seul `mtime`/taille a été relevé.
- Le hash de listing sur 12 s ne couvre que les noms ; il ne prouve pas l'immobilité des contenus.
- Une fenêtre stable de 12 s (listes) et ~92 s (deux scans à 46 s) ne prouve pas l'absence d'écrivain au-delà : reprendre la porte si un ajout apparaît plus tard.
- Le contenu de `courante` n'a pas été hashé avant/après le rejeu dans le cas source ; seul son jeu de 357 fichiers est prouvé.
- Le scan ne compte que les `.py` hors exclusions (`horloge_noyau`, `secrets`, caches, `.git`, environnements virtuels) : un ajout d'une autre nature ne change pas le compte.
- Ce Skill ne remplace ni le triage des échecs, ni l'audit générique des effets de bord, ni la restauration des sceaux.

## Ressources

- Dossier de preuve complet : `C:\Users\Administrateur\.qoder\skills\nettoyer-effets-de-bord-tests-conscience\references\cas-test-conscience-2026-10-27.md`
- Carte du code, équation d'attribution et gabarit de garde : `C:\Users\Administrateur\.qoder\skills\nettoyer-effets-de-bord-tests-conscience\references\attribution-et-garde.md`
- Plan et suppression sous garde : `C:\Users\Administrateur\.qoder\skills\nettoyer-effets-de-bord-tests-conscience\scripts\nettoyer_archives_copie_soi.py`
- Auto-test du script (fixtures temporaires, gardes et atomicité) : `C:\Users\Administrateur\.qoder\skills\nettoyer-effets-de-bord-tests-conscience\scripts\tester_nettoyage_archives.py`
- Instantané et comparaison `memoire_aq` : `C:\Users\Administrateur\.qoder\skills\verifier-effets-de-bord-verification-lecture-seule\scripts\instantane_effets_de_bord.py`
- Triage des échecs et périmètre pollué : `C:\Users\Administrateur\.qoder\skills\triager-echecs-suite-unittest-decouverte\SKILL.md`
- Restauration des sceaux : `C:\Users\Administrateur\.qoder\skills\restaurer-sceaux-memoire-aq\SKILL.md`
- Validateur de paquet Skill : `C:\Users\Administrateur\.qoder\skills\skill-file-qa\scripts\validate_skill.py`
- Substitution d'arguments dans le corps injecté (symptôme : le texte injecté montre des mots du prompt à la place des variables positionnelles) : `C:\Users\Administrateur\.qoder\skills\harden-skill-argument-substitution\SKILL.md`

Si le Skill est déplacé, remplacer le préfixe `C:\Users\Administrateur\.qoder\skills\nettoyer-effets-de-bord-tests-conscience` par le nouveau chemin.
