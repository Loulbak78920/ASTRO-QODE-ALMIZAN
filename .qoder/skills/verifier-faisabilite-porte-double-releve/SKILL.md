---
name: verifier-faisabilite-porte-double-releve
description: "Valider qu'une porte à double relevé proposée dans une mise à jour de Skill est exécutable : extraire les observables, chronométrer sur l'arbre réel l'observation coûteuse et la bon marché, remplacer l'intervalle annoncé s'il est inférieur au coût mesuré, faire porter le sleep sur l'observable bon marché, exiger des passes strictement identiques (même coupure avec décalage, même racine, même filtre) et l'égalité des ensembles triés plutôt que des comptes, distinguer un écart dû à la coupure d'une activité d'écrivain, puis rapporter la cadence réelle, la fenêtre et la variance comme limites. Utiliser quand une mise à jour annonce « deux relevés à ~12 s », quand une preuve de stabilité repose sur `wc -l`, quand le coût d'un scan est inconnu ou a changé, ou avant d'écrire une porte de stabilité. 中文触发：双次读数门可行性、间隔小于测量成本、同一截止时间的集合比较、计数相等但成员不同、外部写入者仍活动。English: double-read gate feasibility, interval below measurement cost, set equality across identical passes, count equality false pass, active external writer."
---

# Vérifier la faisabilité d'une porte à double relevé

## Vue d'ensemble

Une porte à double relevé prouve qu'une fenêtre est immobile en comparant deux observations identiques espacées d'un intervalle. Elle n'est valable que si l'intervalle est réalisable pour chaque observable, si les deux passes partagent exactement les mêmes paramètres et si la comparaison porte sur les ensembles. Ce Skill chronomètre la porte sur l'arbre réel, la réécrit si l'intervalle est inférieur au coût mesuré, puis rend un verdict falsifiable.

## Quand utiliser

- Une mise à jour de Skill annonce « deux relevés à ~12 s », « deux passes à 10 s », avec `wc -l`, `S` remesuré ou un compteur agrégé.
- Une preuve de stabilité repose sur l'égalité de comptes, sans `diff` ni identité des paramètres.
- Le coût d'un scan, d'un `find` ou d'un import est inconnu, ancien, ou a changé depuis la session qui l'a documenté.
- Avant d'écrire une porte de stabilité dans un Skill, ou avant de faire confiance à une porte existante.

## Quand ne pas utiliser

- Vérifier la provenance et la formulation d'une recommandation : `verify-skill-recommendation-claims`, `verify-skill-doc-claims-before-edit`.
- Diagnostiquer un test qui échoue sur une durée, une latence ou une gigue : `diagnostiquer-echec-test-chronometre`.
- Prouver qu'une vérification est sans effet de bord : `verifier-effets-de-bord-verification-lecture-seule`.
- Attribuer ou nettoyer les archives de copie de soi : `nettoyer-effets-de-bord-tests-conscience`.
- Rejouer un fixture documenté, commande par commande : `replay-skill-reference-fixtures`.

## Contrat non négociable

1. **Pas d'intervalle sans coût mesuré.** Une porte qui annonce une durée sans avoir chronométré ses commandes sur l'arbre réel n'est pas une porte.
2. **Chronométrer la commande exacte de la porte, pas un équivalent.** `find` a coûté 0,43–0,49 s là où le script Python a coûté 0,05 s ; inversement, un scan a coûté 46 s dans la session source et 58–83 s ici.
3. **Lier chaque durée à sa charge.** Noter `SCAN_FILES`, le nombre de fichiers listés ou la taille du périmètre avec la durée : une durée sans charge n'est pas comparable.
4. **Deux mesures pour un observable coûteux ou variable.** Retenir le maximum pour décider la faisabilité, et rapporter la variance.
5. **Le `sleep` porte sur l'observable bon marché.** Ne jamais annoncer un intervalle inférieur au coût d'un scan : le déplacer sur la liste, faire les deux scans dos à dos, et rapporter la cadence réelle.
6. **Deux passes = mêmes paramètres.** Même coupure avec décalage explicite, même racine, même filtre, même interpréteur, même environnement, même locale de tri.
7. **Comparer les ensembles triés.** Des comptes égaux avec des membres différents sont un faux positif ; un `wc -l` seul ne prouve rien.
8. **Un écart entre coupures différentes ne prouve rien.** La variation vient du paramètre, pas d'un écrivain.
9. **Un canal stable ne prouve pas l'autre.** Une liste stable avec `S1 ≠ S2` signale un écrivain hors filtre ou une observation non déterministe : ne pas conclure.
10. **Verdict et fenêtre explicites.** Aucune stabilité n'est prouvée au-delà de la fenêtre mesurée.

## Étape 0 — Extraire la porte proposée

Lire le texte de la mise à jour et remplir ce tableau avant toute exécution :

| Élément | À relever |
|---|---|
| Observable coûteux | commande exacte, charge attendue, coût connu ou inconnu |
| Observable bon marché | commande exacte, filtre, racine |
| Intervalle annoncé | durée et observable auquel elle s'applique |
| Critère annoncé | comptes, ensembles, `diff`, seuil |
| Paramètres | coupure, racine, exclusions, interpréteur, environnement |

Si la porte ne nomme pas ses paramètres, la classer `PORTE_NON_PROUVEE` jusqu'à ce qu'ils soient écrits.

## Étape 1 — Chronométrer les deux observables

Exécuter la commande exacte de la porte, sur l'arbre réel, avec un `T0` porteur de son décalage :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
T0="2026-10-27 11:58:00 +0000"
time (find "ASTRO-Q°ODE_SYSTEME" -name '*.py' -not -path '*/__pycache__/*' -newermt "$T0" | LC_ALL=C sort > /dev/null)
time (cd "ASTRO-Q°ODE_SYSTEME" && PYTHONIOENCODING=utf-8 py -3 -B -c 'from conscience_logique.scan_environnement import ScanEnvironnementCode as C; print(C().scanner().nb_fichiers_scannes)')
```

Répéter le scan au moins deux fois et noter `SCAN_FILES` à chaque passe. Si l'observation est censée être en lecture seule, prendre un instantané de `memoire_aq` avant et après avec `verifier-effets-de-bord-verification-lecture-seule` : une écriture pendant la mesure invalide la conclusion de stabilité, pas la durée relevée.

## Étape 2 — Recalculer la faisabilité

```text
attente(observable) = max(0, intervalle_annonce - cout(observable))
```

| Observable | Coût mesuré | Intervalle annoncé | Attente | Verdict |
|---|---|---|---|---|
| liste `.py` (`find`) | 0,43–0,49 s | 12 s | 11,5 s | faisable |
| scan A141 | 46–83 s | 12 s | 0 s | infaisable tel quel |

Si l'intervalle est inférieur au coût de l'observable coûteux, rendre `PORTE_A_REECRIRE` et réécrire la porte ainsi :

- `sleep` de l'intervalle entre les deux relevés bon marché ;
- deux scans dos à dos, leur espacement étant leur propre durée ;
- durée totale rapportée : `COUT_A + INTERVALLE + COUT_B + 2 × COUT_SCAN` ;
- aucune mention d'un intervalle de 12 s pour le scan.

Ne pas raccourcir le scan, ne pas paralléliser deux mesures qui écrivent, ne pas présenter l'intervalle annoncé comme respecté.

## Étape 3 — Prototyper la double passe en lecture seule

Le script ne traite que le canal bon marché ; il refuse une coupure sans décalage et un `--sortie` situé dans `--racine`.

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/verifier-faisabilite-porte-double-releve/scripts/porte_double_releve.py" \
  --racine "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME" \
  --coupure "2026-10-27 11:58:00 +0000" \
  --intervalle 12 \
  --sortie "C:/Users/Administrateur/.qoder/tmp/porte-double-releve/20261027T1240Z"
```

Lire `LISTE_A`, `LISTE_B`, `ENSEMBLES_IDENTIQUES`, `ENTRES`, `SORTIS`, `COUT_A`, `COUT_B`, `ECART_DEBUTS`, `FENETRE`, `MARGE`, `SHA256_A`, `SHA256_B`, `VERDICT`. Codes de retour : `0` listes identiques, `1` listes différentes (constat, pas panne), `2` erreur d'usage ou d'environnement. Les listes sont écrites en UTF-8 sous `--sortie` ; la sortie console reste ASCII.

Puis mesurer les deux scans, dans l'ordre :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
SCAN() { PYTHONIOENCODING=utf-8 py -3 -B -c 'from conscience_logique.scan_environnement import ScanEnvironnementCode as C; print(C().scanner().nb_fichiers_scannes)'; }
printf 'S1=%s\n' "$(SCAN)"
printf 'S2=%s\n' "$(SCAN)"
```

Si l'intervalle annoncé dépasse le coût du scan, insérer `max(0, intervalle - coût_scan)` entre `S1` et `S2` ; sinon les laisser dos à dos et le rapporter.

Repli sans script, en Git Bash :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
T0="2026-10-27 11:58:00 +0000"
RELEVE() { find "ASTRO-Q°ODE_SYSTEME" -name '*.py' -not -path '*/__pycache__/*' -newermt "$T0" | LC_ALL=C sort > "$1"; printf '%s=%s\n' "$(basename "$1")" "$(wc -l < "$1")"; }
RELEVE /tmp/releve_a
sleep 12
RELEVE /tmp/releve_b
diff /tmp/releve_a /tmp/releve_b > /dev/null; printf 'DIFF_RC=%s\n' "$?"
```

`DIFF_RC=1` est un constat à rapporter. Ne pas l'écrire sous `&&` : le code serait avalé.

## Étape 4 — Vérifier l'identité des paramètres

Contrôler, pour les deux passes et pour la mesure de référence :

- coupure identique, avec décalage explicite (`+0000`), et contrôlée avec `date -u` ;
- racine identique (pas le parent dans une passe et l'enfant dans l'autre) ;
- filtre identique (`*.py`, mêmes exclusions, même casse) ;
- interpréteur et environnement identiques (`py -3`, `-B`, `PYTHONIOENCODING=utf-8`) ;
- locale de tri identique (`LC_ALL=C`) ;
- critère identique : ensembles triés, pas comptes seuls ;
- répertoire de travail identique pour les chemins relatifs.

Un seul paramètre différent suffit à rendre `PORTE_NON_PROUVEE`. Exemple documenté par le Skill consommateur : `T0` sans décalage ouvre la fenêtre une heure trop tôt et gonfle les candidats (9 vs 6, puis 10 vs 7) ; deux passes à coupures différentes ont rendu 9 puis 7 candidats sans qu'un écrivain soit nécessaire. Le 2026-10-27 à 12:49Z, les deux coupures ont rendu 8 = 8 sur l'arbre courant : l'égalité de comptes ne prouve pas l'identité des fenêtres, elle prouve seulement que tous les candidats sont postérieurs aux deux coupures.

## Étape 5 — Interpréter les deux canaux

| Listes bon marché | Scans `S1` / `S2` | Verdict |
|---|---|---|
| identiques | égaux | `PORTE_FAISABLE` sur la fenêtre mesurée |
| identiques | différents | écrivain hors filtre ou observation non déterministe : `PORTE_NON_PROUVEE`, attribuer avant de conclure |
| différentes | quelconques | `ECRIVAIN_EXTERNE_ACTIF` : rapporter le `diff`, ne pas calculer de cible |
| une seule passe | — | `PORTE_NON_PROUVEE` |

Le cas du 2026-10-27 illustre la deuxième ligne : listes `8 = 8` identiques à 12 s, mais `S1 = 10 432` et `S2 = 10 426` à 62 ms d'écart, avec des actes `memoire_aq` écrits pendant la mesure. Le canal bon marché était stable ; le canal coûteux ne l'était pas.

## Étape 6 — Rapporter

```text
PORTE_PROPOSEE=<texte>
OBSERVABLE_COUTEUX=<commande> COUT=<s> CHARGE=<n>
OBSERVABLE_BON_MARCHE=<commande> COUT=<s>
INTERVALLE_ANNONCE=<s>
ATTENTE_COUTEUX=<s> ATTENTE_BON_MARCHE=<s>
LISTE_A=<n> LISTE_B=<n> ENSEMBLES_IDENTIQUES=<yes|no>
S1=<n> S2=<n>
ECART_DEBUTS=<s> PORTE_S=<s>
VERDICT=<PORTE_FAISABLE|PORTE_A_REECRIRE|PORTE_NON_PROUVEE|ECRIVAIN_EXTERNE_ACTIF>
FENETRE_COUVERTE=<s> LIMITE=<ce que la mesure ne prouve pas>
```

Joindre les deux valeurs de coût, la variance et la charge : ce sont elles qui rendent le verdict vérifiable.

## Pièges

| Piège | Effet | Parade |
|---|---|---|
| `wc -l` seul | comptes égaux, membres différents | `diff` des listes triées, `ENTRES`/`SORTIS` |
| `T0` sans décalage | fenêtre ouverte une heure trop tôt, candidats gonflés | écriture `+0000`, contrôle `date -u` |
| Coupures, racines ou filtres différents entre passes | la variation vient du paramètre, pas d'un écrivain | checklist de l'étape 4 |
| `sleep` entre deux scans coûteux | l'intervalle annoncé est impossible à tenir | `sleep` sur la liste, scans dos à dos |
| Durée sans charge | 46 s et 83 s pour le même `SCAN_FILES` passent pour la même mesure | noter `SCAN_FILES` avec chaque durée |
| `diff` sous `&&` | code 1 avalé, faux « identique » | capturer `DIFF_RC` séparément |
| `wc -l` sur fichier absent | affiche 0, fausse stabilité | vérifier l'existence du fichier de liste |
| `sort` sans locale fixe | ordre différent entre passes | `LC_ALL=C` des deux côtés |
| Une seule passe | aucune comparaison | deux passes minimum |
| Prototype exécuté pendant qu'un autre écrivain travaille | valeurs périmées avant le rapport | lire `S1`/`S2`, `memoire_aq`, puis attribuer |

## Limites honnêtes

- 12 s de liste et deux scans durent environ 150 s : la stabilité n'est prouvée que sur cette fenêtre.
- Le coût varie (46–83 s pour le même périmètre) ; un seul échantillon sous-estime.
- Le script ne chronomètre pas le scan, n'attribue pas les écrivains et ne prouve pas la lecture seule.
- Les deux canaux ne sont pas échantillonnés simultanément : un écrivain peut agir entre eux.
- Un scan qui lit le même arbre que la liste peut être déterministe alors que la liste bouge, ou l'inverse : mesurer les deux.

## Cas de référence

`references/cas-porte-double-releve-2026-10-27.md` consigne la porte proposée, les deux corrections, les mesures UTC/locales et ce qui reste inconnu. Le Skill consommateur est `nettoyer-effets-de-bord-tests-conscience` ; sa porte est citée comme cas, pas modifiée ici.

## Ressources

- `scripts/porte_double_releve.py` — double passe bon marché, chronométrage, égalité d'ensembles, sortie ASCII, codes 0/1/2.
- `references/cas-porte-double-releve-2026-10-27.md` — preuves et reproduction.
