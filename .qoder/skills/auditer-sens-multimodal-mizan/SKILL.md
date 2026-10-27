---
name: auditer-sens-multimodal-mizan
description: "Auditer sans dol la reconnaissance multimodale d'Al-Mizan (AL-MIZAN x ASTRO-Q°ODE) : inventorier les modules et routes sensorielles (vue, ouïe/STT, spectre, prosodie, TTS, toucher, vibrations, identité biométrique SAS), classer chaque capacité en opérationnel / simulé / spécifié, exécuter des sondes locales réelles, des tests ciblés, une parité SHA-256 local↔VPS et des lectures de production non destructives, puis rapporter la matrice des sens et les chaînes de contournement d'authentification. Utiliser pour vérifier la reconnaissance par les sens, le SAS biométrique, la transcription vocale, le spectre d'écoute, la vision caméra ou le toucher, ou pour préparer un rapport « sans dol » sur ces capacités. 中文触发：多模态感官审计、视觉、听觉、语音转写、生物识别 SAS、真实与模拟能力矩阵。"
---

# Auditer les sens multimodaux d'Al-Mizan

## Quand utiliser

- Vérifier ce que le système **reconnaît réellement** par la vue, l'ouïe, la parole, le toucher ou l'identité biométrique.
- Classer chaque capacité en **opérationnel / simulé / spécifié**, avec preuve locale et contrôle de production.
- Auditer le SAS biométrique, la transcription vocale, le spectre d'écoute, la vision caméra, la thermique.
- Préparer un rapport « sans dol » ou une liste de correctifs hiérarchisés.

## Quand ne pas utiliser

- Déployer ou corriger la production : `deployer-site-sans-dol-vps`, puis confirmation explicite de l'utilisateur.
- Documenter la passerelle HTTP : `documenter-passerelle-python-stdlib`.
- Exécuter le pipeline de conscience ou le programme `.aq` : `entite-conscience-logarithmique`.
- Lancer toute la suite de tests comme preuve de non-régression : elle contient des échecs périmés étrangers à cette chaîne.

## Contrat non négociable

1. **Lecture seule par défaut.** Sans option, le script `scripts/auditer_sens_mizan.py` n'écrit rien. `--sondes` allume réellement caméra et micro ; `--tests` exécute des tests SAS qui peuvent écrire `memoire_aq` ; `--production` et `--parite` restent en lecture seule.
2. **Capture ≠ reconnaissance.** Un SHA-256 de frame ou un RMS audio prouve une capture, jamais une identification. Ne jamais écrire « reconnaît », « identifie » ou « vérifie » sans comparaison à une référence.
3. **Jamais d'exploitation en production.** Interdiction d'appeler `/sas/valider` sur al-mizan.world. La preuve de contournement se fait en local, puis se corrèle à la parité SHA-256 du code.
4. **Aucun secret imprimé.** Contrôler la présence des variables et les permissions, jamais leur valeur.
5. **Effets de bord annoncés.** Caméra et micro s'allument réellement ; ne pas appeler le TTS (son), ni `capturer_tout()` (écrit un état capteurs).
6. **Test périmé ≠ régression produit.** Lire l'assertion avant de conclure.
7. **Correctif ≠ audit.** Un tour de correction séparé, sans suite de tests exécutée, ne se présente jamais comme vérifié.

## Étape 0 — Racine et outils

La racine réelle est `C:\Users\Administrateur\Desktop\IMAM8MAHDI\ASTRO-Q°ODE_SYSTEME`. L'ancien chemin `AppData\Local\Programs\Qoder\ASTRO-Q°ODE_SYSTEME` a échoué (`No such file or directory`).

```bash
R="C:/Users/Administrateur/Desktop/IMAM8MAHDI/ASTRO-Q°ODE_SYSTEME"
cd "$R" && pwd && ls passerelle_api_vps_mizan.py module_sas_biometrique_souverain.py
```

- Interpréteur : `py -3` (l'alias Microsoft Store `python` peut sortir en code 49).
- Console UTF-8 : `export PYTHONIOENCODING=utf-8`.
- Le chemin contient `°` : toujours entre guillemets.
- Scripts jetables dans `$TEMP`, jamais dans le dépôt.

## Étape 1 — Inventaire

```bash
cd "$R" && ls *biometr* *voix* *acoust* *spectre* *vision* *multimodal* *sens* 2>/dev/null
grep -rliE "multimodal|face_recognition|visage|empreinte vocale|speaker|whisper|opencv|librosa|sounddevice" --include='*.py' . | head -40
grep -niE "biometr|voix|audio|vision|sensor|multimodal|sas" passerelle_api_vps_mizan.py | head -40
```

Les dix modules de référence et les routes attendues sont listés dans `references/preuves-2026-10-27.md`.

## Étape 2 — Lire et classer avant de sonder

Pour chaque sens, répondre dans cet ordre :

1. **Y a-t-il une mesure ?** Chercher l'acquisition réelle (caméra, micro, FFT, WMI).
2. **Y a-t-il une comparaison ?** Chercher une référence, un seuil, une similarité. Une case « remplie » n'est pas une correspondance.
3. **Le facteur est-il déclaré par le client ?** Chercher les champs de requête utilisés directement comme preuve.
4. **Y a-t-il une bibliothèque réelle ?** `whisper`, `vosk`, `mediapipe`, `face_recognition`, `insightface`, `deepface`, `webrtcvad`, `librosa`, `speech_recognition`, `torchaudio`, `dlib`. Leur absence invalide toute revendication de STT ou de reconnaissance faciale.
5. **La route est-elle câblée ?** Un module non importé par la passerelle n'est pas une capacité de production.

Signaux typiques à lire dans le code :

- `transcrire_audio_binaire` : retourne un texte constant, latence fabriquée, ignore les octets.
- `lire_pour_comprendre` : renvoie toujours les mêmes formes/gestes, quel que soit le paramètre.
- `analyser_flux_spectral` : accepte des pourcentages fournis par le client, dB figé.
- `evaluer_preuve_multimodale` : sous-chaîne de phrase, booléen de visage, longueur de passkey.
- `verifier_preuve_pleniere` : teste si un emplacement contient une empreinte, pas si elle correspond.
- `est_session_souveraine_active("")` : retourne vrai sans jeton quand une session existe.

## Étape 3 — Sondes locales réelles

```bash
export PYTHONIOENCODING=utf-8
py -3 -B "C:/Users/Administrateur/.qoder/skills/auditer-sens-multimodal-mizan/scripts/auditer_sens_mizan.py" --sondes
```

Le script exécute : capture caméra (empreinte seulement), capture micro (PCM + RMS), STT sur silence et bruit aléatoire, spectre par défaut et avec bandes plausibles, lecture `lire_pour_comprendre("")`, souris/clavier/thermique.

Assertions attendues :

- Caméra : `accessible=true`, `empreinte_sha256` présent, `flux_brut_stocke=false`.
- Micro : `octets_hashes` > 0, `rms` renseigné, aucune identité du locuteur.
- STT : **textes identiques et non vides** sur silence et bruit → simulé. Deux textes vides signifient module désactivé ou coupé : non concluant, jamais « simulé » ni « opérationnel ».
- Spectre : mêmes constantes avec ou sans signal → simulé.
- Vision : formes/gestes constants, `integrable_doctrine=true` → gabarit, pas perception.
- Toucher : thermique à vérifier (un `raw` Kelvin interprété comme dixièmes de Kelvin produit ≈ −243 °C).

Ne pas conclure depuis une seule sonde : croiser avec la lecture du code.

**Fraîcheur.** Un autre tour peut modifier les modules pendant l'audit. Relire les hashes avant et après les sondes ; une preuve n'est valable que pour le hash mesuré. Si un hash change en cours de route, re-mesurer au lieu de fusionner deux versions.

## Étape 4 — Tests ciblés

```bash
cd "$R" && py -3 -B -m unittest tests.test_passerelle_api_vps tests.test_comptes_http_mizan \
  tests.test_site_public_mizan tests.test_sas_biometrique_souverain 2>&1 \
  | grep -aE "^(OK|FAILED|Ran |ERROR:|FAIL:)" | head -20
```

La sortie complète dépasse 89 Ko : la filtrer, ne pas la charger. Pour un échec, extraire l'assertion réelle et vérifier si elle vise un texte retiré du portail (test périmé) ou un comportement cassé.

## Étape 5 — Production, non destructive (opt-in)

```bash
py -3 -B ".../scripts/auditer_sens_mizan.py" --production
```

Autorisé : `GET /api/v1/voix`, `/api/v1/voix/acoustique`, `/api/v1/ecoute/spectre`, `/api/v1/auth/statut_session`, `/api/v1/etat`, et `POST /api/v1/auth/sas_biometrique/challenge`. Interdit : `/sas/valider`, toute création de session, toute rotation de clé.

## Étape 6 — Parité local ↔ VPS (opt-in)

```bash
py -3 -B ".../scripts/auditer_sens_mizan.py" --parite
```

Le script utilise `paramiko` et `deploiement_vps.charger_credentials_ovh`, calcule `sha256sum` à distance, compare aux hashes locaux et lit `systemctl is-active` + `NRestarts`. Aucun mot de passe affiché. Une divergence de hash interdit de transposer une preuve locale en preuve de production.

## Étape 7 — Secrets et permissions

Contrôler **par présence**, jamais par valeur :

```bash
grep -q MIZAN_VPS_API_KEY /etc/systemd/system/al-mizan-api-vps.service && echo PRESENT || echo ABSENT
systemctl show al-mizan-api-vps -p Environment --value | grep -q MIZAN_SOUVERAIN_SECRET && echo PRESENT || echo ABSENT
stat -c '%a %U:%G %n' /opt/al-mizan/ASTRO-Q°ODE_SYSTEME/memoire_aq/*.json
```

Un fichier de session en `666` est lisible et inscriptible par tout utilisateur local : le signaler. Sur Windows, les modes POSIX ne sont pas une preuve de permission : utiliser les ACL.

## Étape 8 — Rapport

Produire un tableau par sens avec trois colonnes : **production**, **poste local**, **statut honnête**. Puis :

1. Chaîne de contournement, si elle existe, avec fichier et fonction (pas seulement un numéro de ligne).
2. Écarts « sans dol » : valeurs simulées présentées comme mesures réelles, divulgations manquantes.
3. Tests exécutés et résultat exact, échecs périmés distingués.
4. Correctifs hiérarchisés, sans déploiement non confirmé.

Libellés autorisés : `opérationnel`, `partiel`, `simulé`, `spécifié`, `non exposé`, `cassé`. Interdits sans preuve : `reconnaît`, `identifie`, `authentifie`, `certifie`.

## Pièges vérifiés

| Piège | Réalité | Réflexe |
|---|---|---|
| Ancien chemin `AppData\...\Qoder` | Inexistant | `pwd` puis `Desktop\IMAM8MAHDI` |
| Sortie `unittest` de 89 Ko | Tronquée ou sauvegardée | `grep -aE "^(OK|FAILED|Ran )"` |
| STT qui « répond » | Même texte sur silence et bruit | Comparer deux entrées opposées |
| SHA-256 de frame | Empreinte, pas visage reconnu | Chercher une référence et un seuil |
| Facteurs SAS « vrais » | Déclarés par le client | Lire la requête, pas le message |
| Session vide « souveraine » | `est_session_souveraine_active("")` vrai | Tester sans jeton |
| Thermique négative | Conversion Kelvin erronée | Vérifier `raw` et l'unité |
| Test rouge | Assertion sur un texte retiré | Lire l'assertion avant de conclure |
| `°` dans les chemins | Rupture de quoting | Guillemets systématiques |

## Ressources

- `references/preuves-2026-10-27.md` — commandes et sorties observées, limites, hashes.
- `scripts/auditer_sens_mizan.py` — inventaire, classification statique, sondes, production, parité, tests.
