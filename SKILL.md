---
name: mesure-cesium-133-geolocalisee
description: "Re-mesurer, vérifier et sceller les métriques quantiques du césium-133 géolocalisé d'IMAM8MAHDI : géolocalisation et heure Windows, décodage w32tm/cp850, altitude Open-Meteo avec contrôle SRTM30m, géodésie WGS84 et temps sidéral IAU, snapshot SHA-256 et empreinte du script, double preuve Monade 9/9 + 23/23, puis régénération gardée de la strate S19 du tableau maître. Utiliser pour toute re-mesure Cs-133, vérification de snapshot ou de preuve Monade, diagnostic zoneinfo/w32tm/SRTM, ou régénération du tableau dépendant de S19. 中文触发：铯-133、地理定位、量子指标、快照校验、Monade 证明、主表 S19。"
---

# Césium-133 géolocalisé — re-mesure et preuve

Re-mesurer ou auditer la mesure Cs-133 scellée et son verrou S19, sans modifier les bibliothèques scellées ni éditer les livrables à la main. Le Skill voisin `tableau-maitre-sequentiel` reste la référence pour la structure du tableau ; ce Skill couvre la chaîne de mesure, le snapshot et la double preuve Monade.

## Quand l'utiliser

- Re-mesurer E, T, λ, recul, gravité WGS84, dilatations, GMST/LAST et cycles Cs-133 depuis la position et l'heure du poste.
- Vérifier un snapshot existant : `empreinte_contenu_sha256`, `empreinte.script_sha256`, 23/23 et 9/9.
- Diagnostiquer `zoneinfo`, `w32tm`, Open-Meteo/SRTM, `KeyError`, `ZeroDivisionError` ou `S19 refusee`.
- Régénérer le tableau après une nouvelle mesure, en conservant S19 cohérente avec le snapshot.

Ne pas utiliser pour modifier les formules physiques, le schéma du tableau, S6 ou `horloge_noyau/` : suivre `tableau-maitre-sequentiel` et demander une décision explicite.

## Contrat non négociable

1. **Sources uniques** : `ASTRO-Q°ODE_SYSTEME/outils/mesurer_metriques_cesium_133.py` acquiert et scelle ; `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_cesium_133.py` calcule et valide ; `ASTRO-Q°ODE_SYSTEME/donnees/mesure_quantique_cesium_133.json` est la preuve. Ne pas recopier les formules dans un rapport ou un script ad hoc.
2. **Snapshot généré** : ne jamais éditer le JSON à la main. `empreinte_contenu_sha256` couvre le JSON canonique sans ce champ ; `empreinte.script_sha256` lie le script de mesure. Toute modification du script ou du contenu invalide l'ancien snapshot : refaire la mesure.
3. **Double preuve** : les 23 contrôles de `valider_metriques_cesium_133`, les 9 couches de `confirmer_harmonie_et_prouver_justesse` et `preuve_totale = true` sont requis. Le générateur refuse S19 sinon (`RuntimeError: S19 refusee`) ; ne pas contourner.
4. **Un seul bind** : `MonadeSupreme.unit(engagement).bind(_valider_et_sceller).isoler()`. Le bind retourne `0 : HÉLIUM` en cas d'échec ; un second bind validerait un jeton déjà dégradé. Le jeton attendu est `SCEAU_MONADE_CS133`.
5. **Temps** : `time.time_ns()` + fuseau Windows (`tzutil /g`) + offset local + `w32tm /query /status`. Pas de `zoneinfo` (tzdata absent sur ce poste). Décoder les octets de sous-processus en `utf-8`, puis `cp850`, puis `cp1252`.
6. **Altitude** : Open-Meteo Elevation en primaire, OpenTopoData SRTM30m en contrôle ; conserver `altitude_spread_m`. L'altitude Windows n'est un repli que si `vertical_accuracy > 0`. `--latitude/--longitude` ou `--altitude` sont des overrides, pas une géolocalisation.
7. **Limites honnêtes** : ne jamais présenter la position comme GPS certifiée, l'altitude comme corrigée du géoïde, l'horloge comme TAI/UTC certifiée, la phase quantique comme mesurée, ou les décalages relativistes comme interférométriques. Reprendre les 5 limites du snapshot dans le rapport.
8. **Écritures** : ne rien écrire dans `horloge_noyau/`, ne pas modifier `lib_cesium_133.py` sans décision explicite, ne jamais éditer CSV/HTML à la main. Seul le moissonneur écrit le snapshot ; seul le générateur écrit le tableau.

## Fichiers et commandes

- Moissonneur : `ASTRO-Q°ODE_SYSTEME/outils/mesurer_metriques_cesium_133.py`
- Calcul et validation : `ASTRO-Q°ODE_SYSTEME/bibliotheques/lib_cesium_133.py`
- Snapshot : `ASTRO-Q°ODE_SYSTEME/donnees/mesure_quantique_cesium_133.json`
- Tests ciblés : `ASTRO-Q°ODE_SYSTEME/tests/test_metriques_cesium_133.py`
- Générateur : `ASTRO-Q°ODE_SYSTEME/generer_tableau_maitre_sequentiel.py`
- Validateur du tableau : `C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py`

```bash
# Verification lecture seule du snapshot, des hashes, de la Monade et de S19
py -3.12 "C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"

# Re-mesure (ecrit le snapshot par defaut)
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3.12 outils/mesurer_metriques_cesium_133.py

# Tests cibles
py -3.12 -m unittest tests.test_metriques_cesium_133 -v

# Regeneration du tableau (verifie le snapshot et les 9 couches)
py -3.12 generer_tableau_maitre_sequentiel.py

# Validation structurelle du tableau
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

`py -3.12` (3.12.7 vérifié) est la convention du dépôt ; `py -3` fonctionne aussi sur ce poste. Ne pas utiliser l'alias Microsoft Store `python`. Garder les messages console en ASCII.

## Procédure

### 0. Préflight

1. Vérifier les cinq fichiers ci-dessus et l'accès en lecture à `horloge_noyau/`.
2. Lancer le vérificateur en lecture seule. S'il échoue, diagnostiquer avant toute re-mesure ; ne pas régénérer le tableau pour masquer l'échec.
3. Noter les hashes et les compteurs de départ pour comparer après l'opération.

### 1. Vérifier l'état courant (lecture seule)

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

Attendre `OK - mesure Cs-133 verifiee`, puis vérifier dans la sortie : 23/23, 9/9 stocké et 9/9 live, `preuve_totale True`, S19 19 lignes, hashes cohérents. Lancer aussi les tests ciblés.

### 2. Re-mesurer

1. Autoriser la localisation Windows (Paramètres > Confidentialité > Localisation) et vérifier que le fournisseur répond `Ready` / `Granted`.
2. Lancer le moissonneur sans option pour une mesure géolocalisée.
3. En cas d'échec, choisir explicitement un repli et le déclarer :
   - position indisponible : `--latitude` + `--longitude` (override, non géolocalisé) ;
   - altitude indisponible : `--altitude` (override) ;
   - pas de réseau : `--no-network --altitude`.
4. Attendre `OK - Cesium-133 mesure geolocalisee`, puis relever le nouveau couple de hashes, la position, l'altitude, l'écart SRTM, l'heure et la précision `w32tm`.
5. Ne pas éditer le snapshot produit.

### 3. Vérifier le nouveau snapshot

```bash
py -3.12 "C:\Users\Administrateur\.qoder\skills\mesure-cesium-133-geolocalisee\scripts\verifier_mesure_cesium.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI" --snapshot-only
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3.12 -m unittest tests.test_metriques_cesium_133 -v
```

- Si `script de mesure modifie` apparaît : le script a changé après la mesure ; refaire la mesure avec la version courante, ne pas réécrire le hash.
- Si 23/23 ou 9/9 échoue : ne pas régénérer le tableau ; corriger la cause et re-mesurer.
- Comparer les nouvelles valeurs aux attentes physiques (ν₀, E, T, λ, g) et signaler tout écart.

### 4. Régénérer et valider le tableau

```bash
cd "C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
py -3.12 generer_tableau_maitre_sequentiel.py
py -3.12 "C:\Users\Administrateur\.qoder\skills\tableau-maitre-sequentiel\scripts\verifier_tableau_maitre.py" --root "C:\Users\Administrateur\Desktop\IMAM8MAHDI"
```

Attendre le résumé `OK - N entrees sequentielles - M strates` puis le validateur canonique. Vérifier que S19 reste 19 lignes `CS-01..CS-19`, SEQ contiguës, CS-18 `PREUVE ARCHITECTURE = 9/9`, CS-19 `PREUVE TOTALE = true` + `SCEAU_MONADE_CS133`, et que les `SOURCE` S19 portent le nouveau hash de snapshot (CS-19 porte aussi le hash du script). Relancer le vérificateur du Skill pour contrôler l'ensemble.

### 5. Rapporter

```text
Mesure Cs-133 : <date UTC> | <fuseau> | w32tm <precision ou absente>
Position : <lat> <N/S> <lon> <E/W> +/-<accuracy> m | altitude <m> (ecart SRTM <m>)
Hashes : contenu <12...> | script <12...>
Monade : metriques 23/23 | architecture 9/9 (stockee et live) | preuve_totale true
Tableau : N entrees / M strates | S19 19 lignes CS-01..CS-19 | SEQ <debut>-<fin>
Limites : 5 limites du snapshot reprises telles quelles
Fichiers : <chemins absolus>
Mesure / calcule / override : <distinguer explicitement>
```

### 6. Maintenir ce Skill

Après une mesure acceptée et un tableau régénéré, mettre à jour la baseline de `references/contrat-mesure-et-limites.md` par édition ciblée, puis relancer `skill-file-qa`. Ne pas réécrire le Skill entier. Si les 23 contrôles, les 9 couches, le schéma du snapshot ou le nombre de lignes S19 changent, mettre à jour le contrat et le vérificateur ensemble.

## Pièges observés

| Symptôme | Cause | Correctif |
|---|---|---|
| `ZoneInfo` introuvable / `load_tzdata` échoue | tzdata absent sur ce poste | `tzutil /g` + `astimezone()` ; ne pas installer tzdata comme prérequis |
| `w32tm` illisible ou caractères `?` | octets console Windows lus en UTF-8 | décoder `utf-8 → cp850 → cp1252` ; parser `ns` dans la ligne Précision |
| `KeyError: 'resolution_python_s'` dans le générateur | `_H` pointe `metriques.temps`, la valeur est dans `snapshot.temps` | utiliser `_H_SYS['resolution_python_s']` |
| Contrôle SRTM absent | lecture de `metriques.position` | lire `snapshot['position']['details_altitude']['opentopodata_srtm30m']['elevation_m']` |
| `ZeroDivisionError: float division by zero` | `nu0 = 0` dans un test de métriques altérées | retourner `structure_valide=False` avant toute division ; le test doit produire HÉLIUM, pas une exception |
| `RuntimeError: S19 refusee` | preuve snapshot ou architecture incomplète | re-vérifier le snapshot et les 9 couches ; ne pas contourner |
| `snapshot: script de mesure modifie depuis la mesure` | script modifié après la mesure | refaire la mesure ; ne jamais éditer `script_sha256` |
| `UnicodeEncodeError` cp1252 | flèche, exposant ou accent dans un `print()` | sortie ASCII, `_ascii`, `py -3.12` |
| `altitude indisponible` avec `--no-network` | aucune source d'altitude | fournir `--altitude` ou laisser l'altitude Windows valide ; sinon échouer honnêtement |
| `w32tm` indisponible | service ou droits | continuer avec la résolution Python, signaler l'absence de précision NTP |
| `SOURCE` S19 ne contient pas le nouveau hash | tableau non régénéré après la mesure | lancer le générateur ; ne pas éditer le CSV/HTML |
| S19 modifiée à la main | édition directe du livrable | restaurer par régénération ; S19 est dérivée du snapshot |

## Définition de terminé

- [ ] Vérificateur : hashes contenu + script valides, 23/23, 9/9 stocké et live, `preuve_totale true`, pas d'état HÉLIUM.
- [ ] Tests ciblés verts (`tests.test_metriques_cesium_133`).
- [ ] S19 : 19 lignes `CS-01..CS-19`, SEQ contiguës, preuves CS-18/CS-19, `SOURCE` alignées sur le snapshot courant.
- [ ] Validateur canonique du tableau : 0 échec ; S6 toujours 40/313/63.
- [ ] Rapport : mesuré / calculé / override distingués, 5 limites reprises, chemins absolus.
- [ ] Aucune écriture dans `horloge_noyau/`, aucune édition manuelle du snapshot, du CSV ou du HTML.
- [ ] Si le Skill a été modifié : `skill-file-qa` PASS avec 0 FAIL.

## Ressources

- `scripts/verifier_mesure_cesium.py` : orchestration lecture seule du snapshot, des hashes, de la Monade et de S19 ; sortie ASCII, codes 0/1/2.
- `references/contrat-mesure-et-limites.md` : schéma, 23 contrôles, 9 couches, baseline vérifiée, intégration S19, arbre de décision et limites.
- `references/skill-zh.md` et `references/contrat-mesure-et-limites-zh.md` : traductions chinoises complètes ; la version française fait foi.
- `tableau-maitre-sequentiel` : validateur canonique et contrat de structure du tableau.
- `skill-file-qa` : QA de structure après édition de ce Skill.
- `verifier-livrables-csv-html-windows-fr` : console Windows, CSV BOM/`;`, contrôle HTML.
- `validation-navigateur-par-repli` : contrôle visuel optionnel avec repli structurel.
