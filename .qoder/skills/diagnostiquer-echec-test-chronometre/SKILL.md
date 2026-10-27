---
name: diagnostiquer-echec-test-chronometre
description: "Diagnostiquer et corriger un test dont l'assertion mesure une duree, une latence, une gigue ou un timeout (AssertionError: X not less than Y, latence moyenne au-dessus du seuil, gigue superieure a 100 %, reprises LLM de 10 s) : reproduire le test seul puis le module et la suite, lire la source exacte de la mesure, profiler chaque etape, rechercher les scans complets, les ecritures par element et les reprises reseau non bornees, corriger la cause racine par cache d'empreinte, ecriture groupee et budget global, puis re-prouver test isole, module, suite ciblee et porte de validation sans modifier le seuil. Utiliser pour un echec chronometre, un test dit instable ou flaky, une performance qui derape, ou avant de qualifier un echec d'alea. 中文触发：计时测试失败、延迟断言、抖动、超时、性能回归、不要改阈值、先复现再修复。"
---

# Diagnostiquer un test qui mesure une durée

## Quand utiliser

- Un test échoue sur une assertion de durée, de latence, de gigue, de débit ou de budget : `assertLess`, `assertGreater`, `assertAlmostEqual` sur un temps.
- Un test est présenté comme « instable », « flaky » ou « aléa » parce qu'il passe parfois.
- Une suite cible devient lente ou dépasse un seuil après une modification.

## Quand ne pas utiliser

- L'échec ne dépend pas du temps : appliquer la Skill du domaine.
- Le seuil lui-même est faux ou obsolète : c'est une décision produit, pas un diagnostic.
- Il faut rejouer un fixture à l'identique : `replay-skill-reference-fixtures`.

## Règles non négociables

1. **Ne pas modifier le seuil** ni l'assertion pour faire passer le test. La règle projet est portée par `entite-conscience-logarithmique` (section Tests) ; ce Skill ne la réécrit pas.
2. **Ne pas qualifier d'aléa avant** d'avoir reproduit le test seul, le module, puis la suite, et profilé les étapes.
3. **Nommer le test complètement** : `module.Classe.methode`. La forme `module.methode` produit un `_FailedTest` et un `AttributeError`, pas un verdict.
4. **Mesurer chaque étape** avant de corriger. Une durée totale ne localise pas le coût.
5. **Conserver le résultat métier** : même nombre d'éléments, même score, même sortie. Une optimisation qui change le résultat n'est pas une correction.

## Procédure

### 1. Geler l'état et capturer l'échec

Relever la ligne d'assertion, la valeur observée, le seuil, l'identifiant complet du test, le code de sortie et la durée.

Si le test écrit (sceaux, journal, fichiers), prendre un instantané avant : appliquer `verifier-effets-de-bord-verification-lecture-seule` et, pour `memoire_aq`, `restaurer-sceaux-memoire-aq`.

Utiliser `py -3.12` et `PYTHONIOENCODING=utf-8`. Le piège de l'alias `python` (code 49) est couvert par `verifier-livrables-csv-html-windows-fr`.

### 2. Reproduire à trois niveaux

Exemple issu du cas de référence ; remplacer le test par celui qui échoue.

```bash
cd "C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME"
PYTHONIOENCODING=utf-8 py -3.12 -m unittest -v tests.test_logique_horloge_synchronisation.TestSynchronisationTotale.test_p7_trame_dans_une_seule_pulsation
PYTHONIOENCODING=utf-8 py -3.12 -m unittest -v tests.test_logique_horloge_synchronisation
```

Puis lancer la suite ciblée ou la suite complète documentée par le projet.

Pour chaque niveau, noter la valeur, la durée et le code de sortie. Interpréter :

- échec aux trois niveaux : défaut systémique ;
- échec seulement en suite : charge, interférence ou coût cumulé, pas une preuve d'aléa ;
- échec unique : répéter au moins deux fois avant toute conclusion.

### 3. Lire l'assertion et la source de la mesure

- Ouvrir la ligne d'assertion et la fonction qui produit la valeur.
- Identifier le chronomètre : début, fin, ce qui est inclus.
- Identifier l'agrégation : moyenne, maximum, percentile, dernière valeur.
- Vérifier si la mesure inclut la préparation, l'audit, les reprises réseau, le fallback ou la persistance.
- Cas typique : une moyenne sur trois points masque un point à 21 s.

### 4. Profiler chaque étape

Entourer chaque étape de `time.perf_counter()` et imprimer les millisecondes et le pourcentage du budget. Séparer au minimum :

| Étape | Question |
|---|---|
| Lecture | combien de fichiers, combien de Mo ? |
| Analyse | combien d'objets parsés ? |
| Persistance | combien d'écritures ? |
| Réseau | combien de tentatives, quel timeout ? |
| Fallback | quand est-il déclenché, combien de temps ajoute-t-il ? |

Une étape qui consomme plus que le budget total est la cible. Ne pas optimiser au hasard.

### 5. Chercher les trois motifs de coût

1. **Scan complet par appel** : N fichiers relus et reparsés à chaque appel.
2. **Persistance par élément** : N écritures ou N rechargements pour un seul appel.
3. **Reprises non bornées** : N tentatives réseau, chacune avec un timeout neuf.

Ajouter les variantes : cache jamais invalidé, démarrage à froid, fallback qui double le budget.

Quantifier chaque motif : N, coût unitaire, coût total, part du budget.

### 6. Corriger la cause racine

- **Cache** : clé = empreinte du contenu ; hydrater depuis les résultats déjà persistés ; ignorer les fichiers inchangés.
- **Écriture groupée** : auditer sans sceller, puis persister une seule fois.
- **Budget global** : une seule date limite pour toutes les tentatives ; passer le temps restant à chaque appel ; basculer en fallback quand il est épuisé.
- **Équivalence** : même N, même score, même sortie. Comparer avant/après.
- **Seuil inchangé** : le test doit passer parce que le coût a baissé, pas parce que la limite a bougé.

### 7. Re-prouver dans le même ordre

1. Test seul.
2. Module entier.
3. Suite ciblée.
4. Porte de validation du projet.

Comparer les valeurs et durées avant/après. Vérifier les effets de bord de la suite (sceaux, journal) et restaurer si nécessaire. Si un échec externe subsiste, le déclarer externe ; ne pas le tolérer silencieusement.

## Pièges vérifiés

| Signature | Cause | Action |
|---|---|---|
| `_FailedTest` + `AttributeError: module ... has no attribute test_...` | classe omise dans le nom | utiliser `module.Classe.methode` |
| échec en suite, succès isolé | charge, interférence ou coût cumulé | ne pas conclure à l'aléa ; profiler |
| échec isolé et en module | défaut systémique | corriger la cause, pas le seuil |
| moyenne sous le seuil, un point au-dessus | agrégation qui masque l'outlier | inspecter les points, pas seulement la moyenne |
| trame à 170–180 % d'un budget de 1 s | 76 analyses + 76 écritures par trame | cache par empreinte + écriture groupée |
| un tour à 21 s pour un seuil de 10 s | 3 modèles × timeout de 10 s | budget global + temps restant + fallback |
| cache chaud mais score modifié | clé trop large ou entrée périmée | clé sur le contenu, invalidation explicite |
| suite « verte » mais index de sceaux modifié | les tests écrivent | instantané avant, restauration après |

## Vérification finale

- [ ] Identifiant complet du test utilisé.
- [ ] Valeur, durée et code de sortie relevés aux trois niveaux.
- [ ] Assertion et source de la mesure lues.
- [ ] Étapes profilées avec leur part du budget.
- [ ] Trois motifs de coût vérifiés et quantifiés.
- [ ] Seuil et assertion inchangés.
- [ ] Même N, même score, même sortie.
- [ ] Test seul, module, suite et porte re-exécutés.
- [ ] Effets de bord mesurés et restaurés si nécessaire.
- [ ] Échec externe résiduel déclaré comme tel.

## Ne remplace pas

- `entite-conscience-logarithmique` pour la chaîne projet, le jeu de tests et la règle de seuil.
- `restaurer-sceaux-memoire-aq` et `verifier-effets-de-bord-verification-lecture-seule` pour les écritures de `memoire_aq`.
- `verifier-livrables-csv-html-windows-fr` pour `py -3`, le code 49 et l'encodage.
- `replay-skill-reference-fixtures` pour le rejeu d'un fixture.
- `audit-session-evidence` pour la provenance des preuves.

## Cas vérifié

Le 2026-10-26, deux tests chronométrés ont échoué puis ont été corrigés à la racine.

- 68 tests ciblés : 66 réussites, 2 échecs, 121.651 s.
- Gigue `test_p7` : 153.395 en suite, 132.7286 seul, 143.7172 sur le module, pour un seuil de 100.
- Télémétrie : 16137.075 ms en suite, 10210.114 ms seul, pour un seuil de 10000 ms.
- Causes : 76 analyses et 76 écritures par trame ; 3 modèles avec un timeout neuf de 10 s.
- Après correction : module horloge 9/9 en 1.187 s, suite 68/68 en 53.011 s, porte 35/35, seuils inchangés.

Les valeurs, commandes, profiling et correctifs sont dans `references/cas-tests-chronometres-2026-10-26.md`. La fiche suit la discipline de `write-skill-evidence-case-study`.

## Ressources

- `references/cas-tests-chronometres-2026-10-26.md` : cas complet, commandes, valeurs, correctifs et limites.
