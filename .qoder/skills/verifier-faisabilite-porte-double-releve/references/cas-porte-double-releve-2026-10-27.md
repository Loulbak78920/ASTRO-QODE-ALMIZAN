# Cas — porte à double relevé du 2026-10-27

## Provenance

| Élément | Valeur |
|---|---|
| Session source | `6c2b1ab8-86ff-4f42-a368-4e24a2312a2a` |
| Lecture | `read_chat_session` (turnLimit 20, includeToolOutputs true) ; revision 57, `runtimeState` running, `hasMoreBefore` false |
| Dernier message utilisateur lu | « confirmez ce plan », 2026-10-27T12:34:05.927Z |
| Plan proposé | 2026-10-27T12:27:06.230Z |
| Skill consommateur | `nettoyer-effets-de-bord-tests-conscience/SKILL.md`, 27 926 o, SHA-256 `a07d1a86…`, porte ligne 130, « ~46 s » ligne 156, au 2026-10-27T12:49Z |
| Mesures propres | 2026-10-27T12:36–12:49Z, local UTC+1 |

La session source était encore en cours (`running`) : ses valeurs sont des observations datées, pas un état final. Le consommateur était réécrit pendant la lecture (24 393 → 27 926 o) ; il n'a pas été modifié ici.

Aucune correction utilisateur explicite dans les messages lus : le seul message utilisateur est la confirmation du plan. Les écarts corrigés ici (intervalle de 12 s appliqué au scan, « 9 vs 6 » présenté comme preuve d'un écrivain, `S1 = S2` traité comme propriété) viennent des mesures, pas d'une consigne utilisateur.

## Porte proposée

« Deux relevés à ~12 s d'intervalle (`wc -l` + `S` remesuré) ; si le compte bouge, rapporter `ECRIVAIN_EXTERNE_ACTIF` et s'arrêter.

Observables :

- coûteux : scan A141, `ScanEnvironnementCode().scanner().nb_fichiers_scannes` ;
- bon marché : `find ASTRO-Q°ODE_SYSTEME -name '*.py' -not -path '*/__pycache__/*' -newermt "$T0" | sort`.

## Mesures

| Mesure | Valeur | Contexte |
|---|---|---|
| Scan source | 46,013 s, `SCAN_FILES 10432` | session source |
| Scan isolé | 72,848 s, `SCAN_FILES 10432`, `memoire_aq` inchangé | 12:36–12:37Z |
| Scans appariés | 82,636 s puis 57,880 s ; `S1 = 10 432`, `S2 = 10 426` ; écart des départs 62 ms | 12:38–12:39Z |
| Listes A/B (`find`) | 0,425 s / 0,490 s ; 8 = 8 ; `diff` vide | 12:37Z |
| Listes A/B (script) | 0,05 s / 0,02 s ; 8 = 8 ; SHA identiques `cbdb09f9…` | 12:45–12:46Z |
| Arbre `.py` sous `ASTRO-Q°ODE_SYSTEME` | 252 = 252 à 7 s d'écart | 12:40Z |
| `memoire_aq` pendant les scans appariés | actes écrits à 13:38:54 locales (12:38:54Z) | 12:39Z |
| Coupure sans / avec décalage | 8 = 8 | 12:49Z |

## Verdicts

| Affirmation | Statut | Preuve |
|---|---|---|
| Intervalle 12 s infaisable pour le scan | SUPPORTED | 12 < 46 (source) et 12 < 58–83 (ici) |
| `sleep` à porter sur les listes | SUPPORTED | listes 8 = 8 à 12 s, `diff` vide |
| Égalité d'ensembles, pas de comptes | SUPPORTED | passes 9 puis 7 à coupures différentes (documenté par le consommateur) ; `diff` requis |
| « 9 vs 6 / 10 vs 7 » = activité d'écrivain | CONTRADICTED | c'est l'effet du `T0` sans décalage, déjà documenté |
| `S1 = S2 = 10 432` comme propriété | NOT REPRODUCED | 10 432 → 10 426 à 62 ms, `memoire_aq` modifié |
| `T0` sans décalage gonfle les candidats | NON REPRODUIT AUJOURD'HUI | 8 = 8 à 12:49Z, tous les candidats postérieurs aux deux coupures |
| Delta exact de 6 fichiers entre `S1` et `S2` | UNKNOWN | écrivain concurrent probable, non attribué |

## Ce qui est établi

- Le coût du scan varie fortement pour la même charge (46–83 s) : une valeur recopiée n'est pas une mesure.
- Les listes peuvent être stables pendant que le scan bouge : les deux canaux doivent être mesurés séparément.
- La comparaison de comptes entre coupures différentes ne prouve rien ; ici elle coïncide même (8 = 8), ce qui ne prouve pas l'identité des fenêtres.
- `memoire_aq` a changé pendant la paire de scans ; un scan isolé ne l'a pas modifié. Un écrivain concurrent est probable, non identifié.

## Ce qui reste inconnu

- L'auteur des actes `memoire_aq` et des 6 fichiers d'écart entre `S1` et `S2`.
- L'état final de la session source, encore `running` à la lecture.
- La raison exacte de la baisse `10 432 → 10 426` (suppression, déplacement ou changement d'exclusion).

## Reproduction

Comparer les coupures, sans scan (rapide) :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI"
find "ASTRO-Q°ODE_SYSTEME" -name '*.py' -not -path '*/__pycache__/*' -newermt "2026-10-27 11:58:00" | wc -l
find "ASTRO-Q°ODE_SYSTEME" -name '*.py' -not -path '*/__pycache__/*' -newermt "2026-10-27 11:58:00 +0000" | wc -l
```

Attendu au 2026-10-27 à 12:49Z : `8` et `8`, car tous les candidats sont postérieurs aux deux coupures. Ce résultat ne reproduit pas le cas historique « 9 vs 6, puis 10 vs 7 », qui dépendait d'un état antérieur de l'arbre.

Double passe bon marché, 12 s :

```bash
py -3 -B "C:/Users/Administrateur/.qoder/skills/verifier-faisabilite-porte-double-releve/scripts/porte_double_releve.py" \
  --racine "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME" \
  --coupure "2026-10-27 11:58:00 +0000" \
  --intervalle 12 \
  --sortie "C:/Users/Administrateur/.qoder/tmp/porte-double-releve/20261027T1246Z"
```

Attendu : `LISTE_A=8`, `LISTE_B=8`, `ENSEMBLES_IDENTIQUES=yes`, `VERDICT=LISTE_STABLE`, code 0.

Scans appariés, environ 140 s, sensibles aux écrivains concurrents :

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
SCAN() { PYTHONIOENCODING=utf-8 py -3 -B -c 'from conscience_logique.scan_environnement import ScanEnvironnementCode as C; print(C().scanner().nb_fichiers_scannes)'; }
printf 'S1=%s\n' "$(SCAN)"
printf 'S2=%s\n' "$(SCAN)"
```

Mesuré : `S1=10432`, `S2=10426`, avec `memoire_aq` modifié pendant la paire.

## Empreintes au moment de la rédaction

| Fichier | SHA-256 |
|---|---|
| `SKILL.md` (ce paquet) | `3b02aa08a87655896ad7cd72b80f9bd51b070891d7c039225a0a9d051ee747e2` |
| `scripts/porte_double_releve.py` | `cbb77ccbd7332af36ae11111f674661beb727a59da37c80e4f2c322a9c9bcce1` |
| consommateur `SKILL.md` | `a07d1a86b77048355d60cd366fa1bb089acad5a90256ab3fd6819609a247fc85` |

`SKILL.md` : description de 1018 caractères, corps de 194 lignes. Le consommateur reste en cours de réécriture ; ses numéros de ligne ne valent que dans la fenêtre du 2026-10-27T12:49Z.
