# Contrat de mesure Cs-133 et limites

Instantané de référence vérifié le 2026-10-26. Les valeurs de mesure sont datées ; seuls les invariants de structure et de preuve sont permanents. Une nouvelle mesure change les hashes et les valeurs : mettre à jour la baseline après acceptation.

## 1. Chaîne de mesure

| Étape | Fichier | Rôle |
|---|---|---|
| Acquisition | `ASTRO-Q°ODE_SYSTEME/outils/mesurer_metriques_cesium_133.py` | Position Windows, heure système, fuseau, `w32tm`, altitude DEM, recalcul, double preuve, snapshot |
| Calcul | `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_cesium_133.py` | Constantes SI/CODATA, WGS84, GMST IAU 1982, 23 contrôles, Monade, vérification du snapshot |
| Preuve | `ASTRO-Q°ODE_SYSTEME/donnees/mesure_quantique_cesium_133.json` | Snapshot JSON hashé, `preuve_totale`, limites |
| Intégration | `ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py` | Strate S19, `verifier_snapshot_cesium_133` + `confirmer_harmonie_et_prouver_justesse`, refus si preuve incomplète |
| Tests | `ASTRO-Q°ODE_SYSTEME/tests/test_metriques_cesium_133.py` | Formules, snapshot scellé, altération refusée, 9 couches, S19 dans le CSV |

Le moissonneur ne mesure pas la phase quantique : il calcule les métriques à partir d'une position, d'un instant et de constantes. Les décalages relativistes sont calculés par rapport aux références indiquées, pas mesurés par interférométrie.

## 2. Snapshot et hashes

Clés de premier niveau :

```text
schema, genere_le_utc, methode, temps, position, constantes,
metriques, validation_monade, preuve_totale, limites, empreinte,
empreinte_contenu_sha256
```

- `schema` : `MESURE_QUANTIQUE_CESIUM_133/v1`.
- `empreinte_contenu_sha256` : SHA-256 du JSON canonique de tous les champs sauf lui-même.
- JSON canonique : `json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)`.
- `empreinte.script_sha256` : SHA-256 des octets du script de mesure.
- `verifier_snapshot_cesium_133(snapshot, script)` contrôle : schéma, empreinte de contenu, empreinte du script si fournie, recalcul des 23 contrôles, égalité avec les contrôles stockés, verdict monadique recalculé, preuve d'architecture stockée, `preuve_totale=True`.

Conséquences :

- Modifier le snapshot à la main casse `empreinte_contenu_sha256`.
- Modifier le script de mesure casse `script_sha256`, même si le snapshot reste intact.
- Dans les deux cas, la seule réparation conforme est de refaire la mesure ; on ne réécrit jamais un hash.

## 3. Les 23 contrôles de métriques

| # | Contrôle | Vérifie |
|---|---|---|
| 1 | `atome_cs133` | Z=55, N=78, A=133, spin 7/2, niveaux F=3 et F=4 |
| 2 | `frequence_si` | ν₀ exactement 9 192 631 770 Hz |
| 3 | `energie_coherente` | E = hν₀ |
| 4 | `energie_ev_coherente` | E en eV = E / e |
| 5 | `temperature_coherente` | T = E / k_B |
| 6 | `temperature_mk_coherente` | T en mK = T × 1000 |
| 7 | `longueur_onde_coherente` | λ = c / ν₀ |
| 8 | `longueur_onde_mm_coherente` | λ en mm = λ × 1000 |
| 9 | `impulsion_coherente` | p = h / λ |
| 10 | `recul_coherent` | ν_rec = hν₀² / (2mc²), E_rec = hν_rec |
| 11 | `position_valide` | latitude −90..90, longitude −180..180, précision ≥ 0 |
| 12 | `altitude_valide` | altitude −500..9000 m, écart ≥ 0 |
| 13 | `sources_valides` | sources géolocalisation et altitude non vides |
| 14 | `gravite_valide` | 9,0..10,0 m/s² |
| 15 | `rayon_valide` | 6,3..6,5 Mm |
| 16 | `rotation_valide` | vitesse 0..500 m/s, vitesse de référence ≥ 0 |
| 17 | `dilatation_gravitationnelle_coherente` | g·h/c², signe et cycles/24 h |
| 18 | `dilatation_cinetique_coherente` | v²/(2c²), signe et cycles/24 h |
| 19 | `dilatation_locale_coherente` | gravité − (v² − v_ref²)/(2c²) |
| 20 | `dilatation_totale_coherente` | −GM/(r c²) − cinétique |
| 21 | `temps_sideral_valide` | GMST/LAST dans 0..360°, LAST heures = degrés/15 |
| 22 | `cycles_valides` | `unix_ns` entier > 0, durée 0..86 400 s, cycles = ν₀ × durée, incertitudes > 0 |
| 23 | `horodatage_valide` | UTC, local et fuseau non vides, offset −12 h..+14 h |

Garde-fou important : si la structure est illisible ou si `nu0 <= 0`, le validateur retourne `{"structure_valide": False}` avant toute division. Un test qui force `frequence_hz = 0` doit produire une Monade HÉLIUM, pas `ZeroDivisionError`.

## 4. Les 9 couches d'architecture

`confirmer_harmonie_et_prouver_justesse()` retourne `couches_ok` :

| # | Couche | Vérifie |
|---|---|---|
| 1 | `①_informe_quatre_familles` | quatre familles calculées + décomposition M=24434 |
| 2 | `②_etats_de_matiere` | polarité ±313 et ancre M=24434 |
| 3 | `③_complexe_point_zero` | COMPLEXE = LA TABLE = point zéro |
| 4 | `④_q_degre_derives_table` | Q° dérivés de LA TABLE, pas 313/24434 |
| 5 | `cycles_trinite_calcules_depuis_zero` | dx/dy/dz/dt calculés, somme dt cohérente, domaine −9..+9 |
| 6 | `trajectoire_zero_expansion` | trajectoire zéro → expansion complète |
| 7 | `horloge_deduite_du_noyau` | horloge déduite du même noyau, pas de valeurs arbitraires |
| 8 | `sync_cinq_familles` | synchronisation matière ↔ cinq familles, M=24434, COMPLEXE = table |
| 9 | `⑤_monade_juste` | `unit` + `isoler` + âme gouverne + HÉLIUM de secours valide |

La preuve d'ensemble exige `monade_juste` et les 9 couches vraies. Le générateur exige en plus que la preuve stockée dans le snapshot soit vraie.

## 5. Chaîne Monade

```text
engagement = empreinte_contenu(metriques)
monade = MonadeSupreme.unit(engagement).bind(_valider_et_sceller).isoler()
jeton attendu = SCEAU_MONADE_CS133
```

- `_valider_et_sceller` lève une exception si un contrôle est faux ; `bind` attrape l'exception et retourne `0 : HÉLIUM` isolé.
- `monade_juste` exige : jeton attendu, `est_isolee`, pas HÉLIUM, et `OMEGA_MONAD_SOUL.gouverne(jeton)`.
- Un seul bind. Un second bind s'appliquerait au résultat (éventuellement HÉLIUM) et ne réparerait rien.
- Le snapshot stocke `validation_monade.metriques` (contrôles, verdict, historique) et `validation_monade.architecture` (verdict des 9 couches).

## 6. Baseline vérifiée

Instantané du 2026-10-25T23:25:24.555975Z, vérifié le 2026-10-26 :

| Élément | Valeur |
|---|---|
| Hash contenu | `8fb08b28d390796192d5cf738f3e6e09cb59d5c2321a7b861f746cb8d2c3016b` |
| Hash script | `bfb95373f1557874be30c510667fd8348e5f05fcd959efcdc57fc538d0248da0` |
| Temps UTC / local | `2026-10-25T23:25:24.555975Z` / `2026-10-26T00:25:24.555975+01:00` |
| Fuseau / offset | `Romance Standard Time` / `+3600 s` |
| Position | `45.044766577161575 N`, `5.039379914878178 E`, précision horizontale 143 m |
| Altitude | 153,0 m (Open-Meteo), contrôle SRTM30m 157,0 m, écart 4,0 m |
| `w32tm` | source `time.windows.com,0x9`, précision 119,209 ns |
| Résolution Python | 15,625 ms ; incertitude utilisée = max = 15,625 ms |
| Transition | ν₀ 9 192 631 770 Hz ; E 6,091102297113866e-24 J (38,0177 µeV) ; T 441,1767434817876 mK ; λ 32,61225571749406 mm |
| Recul | ν_rec 1,4114726315157167e-6 Hz ; E_rec 9,352516671228239e-40 J |
| Gravité WGS84 | 9,805766130413133 m/s² ; rayon géocentrique 6 367 625,834832317 m |
| Dilatations | gravitationnelle +1,6692890939018852e-14 ; cinétique 6,028278557180383e-13 ; local/mer 1,666401898995543e-14 ; total/infini −6,970991601083279e-10 |
| Cycles/24 h | gravitationnel +13,258218203640274 ; cinétique −478,79203665438274 ; local/mer +13,235286849086672 ; total/infini −553 666,3965549042 |
| GMST / LAST | 25,71241535898298° / 30,75179527386116° (2,0501196849240775 h) |
| Cycles depuis minuit | 775 164 592 245 089,8 ± 143 634 871,4 |
| Monade | métriques 23/23, architecture 9/9, `preuve_totale=true` |
| Tableau | 204 entrées / 20 strates ; S19 19 lignes `CS-01..CS-19`, SEQ 186–204 |

Cette baseline sert de régression. Elle n'est pas une constante physique : une nouvelle mesure change position, heure, cycles, hashes et donc les lignes S19.

## 7. Intégration S19 dans le générateur

- S19 : `S19 · Césium-133 géolocalisé (métriques quantiques mesurées)`.
- 19 entrées `CS-01..CS-19` : atome, transition, définition SI, conversions, recul, position, géodésie, relativité, horodatage, temps sidéral, cycles, double preuve.
- Le générateur appelle `verifier_snapshot_cesium_133(snapshot, script)` puis `confirmer_harmonie_et_prouver_justesse()`. Si une preuve manque : `RuntimeError: S19 refusee: preuve Monade incomplete (snapshot ou architecture)`.
- Blocs à ne pas confondre :
  - `_H = snapshot["metriques"]["temps"]` : heure utilisée dans le calcul.
  - `_H_SYS = snapshot["temps"]` : bloc système complet, avec `w32tm`, `resolution_python_s`, `precision_windows_s`, `incertitude_utilisee_s`.
  - `_P_SYS = snapshot["position"]` : bloc position complet, avec `details_altitude`.
- Contrôle SRTM : `_P_SYS["details_altitude"]["opentopodata_srtm30m"]["elevation_m"]` ; ne pas le chercher dans `metriques.position`.
- `_SOURCE` inclut `donnees/mesure_quantique_cesium_133.json · SHA-256 <16 premiers caractères>…`. CS-19 inclut aussi `script SHA-256 <16 premiers caractères>…`.
- Toute ligne S19 est dérivée du snapshot. Ne pas éditer le CSV ou le HTML ; régénérer.

## 8. Arbre de décision

| Symptôme | Diagnostic | Action |
|---|---|---|
| `empreinte de contenu invalide` | snapshot modifié ou corrompu | restaurer une copie valide ; sinon re-mesurer |
| `script de mesure modifie depuis la mesure` | script modifié après la mesure | re-mesurer avec la version courante ; ne pas éditer le hash |
| Un ou plusieurs contrôles 23/23 faux | formule, position, temps ou source incohérents | lire les noms des contrôles ; corriger la cause ; re-mesurer |
| Une couche 9/9 fausse | dérive de l'architecture scellée | inspecter `couches_ok` ; ne pas régénérer le tableau ; demander une décision |
| `monade_juste=false`, `etat_helium=true` | au moins un contrôle a échoué | diagnostiquer les contrôles ; re-mesurer après correction |
| `S19 refusee` | preuve snapshot ou architecture incomplète | re-vérifier le snapshot et les 9 couches ; ne pas contourner |
| Position indisponible | permission ou fournisseur Windows | autoriser la localisation ; sinon override explicite et déclaré |
| Altitude indisponible | réseau ou API DEM | fournir `--altitude` ; sinon altitude Windows valide ; sinon échouer |
| `w32tm` indisponible | service ou droits | continuer avec la résolution Python ; signaler l'absence de trace NTP |
| `SOURCE` S19 sans le nouveau hash | tableau non régénéré | lancer le générateur |
| `UnicodeEncodeError` | console cp1252 | sortie ASCII ; `py -3.12` |

## 9. Limites honnêtes

Reprendre ces cinq limites dans tout rapport :

1. Position Wi-Fi/cellulaire : précision horizontale fournie par Windows, non GPS certifié.
2. Altitude DEM orthométrique : géoïde non modélisé ; l'écart entre sources est reporté (par exemple 153 m vs 157 m).
3. Horloge système non certifiée TAI/UTC ; la synchronisation NTP Windows est tracée par `w32tm`.
4. La phase quantique n'est pas mesurée : seuls les cycles et décalages théoriques sont calculés.
5. Les décalages relativistes sont calculés par rapport aux références indiquées, pas mesurés par interférométrie.

Ne pas transformer une valeur calculée en mesure expérimentale. Ne pas présenter l'override de position ou d'altitude comme une géolocalisation.

## 10. Maintenance

- Après une mesure acceptée et un tableau régénéré : mettre à jour la baseline (§ 6), les hashes, les comptes S19 et la date de vérification.
- Si les 23 contrôles, les 9 couches, le schéma du snapshot ou le nombre de lignes S19 changent : mettre à jour `SKILL.md`, ce document et `scripts/verifier_mesure_cesium.py` ensemble.
- Après toute édition du Skill : lancer `skill-file-qa` et exiger `RESULT PASS` avec 0 FAIL.
- Ne jamais déclarer une mesure ou une régénération réussie sans la sortie réelle du vérificateur, des tests et du validateur du tableau.
