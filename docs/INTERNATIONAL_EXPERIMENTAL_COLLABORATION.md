# AL-MIZAN — International experimental collaboration / Collaboration expérimentale internationale

**Status:** Open call for independent proposals; no laboratory participation or physical validation is claimed.

## FR — Appel aux laboratoires et chercheurs

Le projet AL-MIZAN recherche des laboratoires, équipes universitaires et chercheurs indépendants disposant d'instruments ou de données publiques pour **mettre à l'épreuve** son modèle harmonique à deux pôles. Aucun équipement ni financement n'est demandé au porteur du projet pour commencer une analyse sur données publiques.

**Base mathématique :** [dossier et limites scientifiques](../publications/2026-11-03_AL_MIZAN_THEOREME_HARMONIQUE_ET_LIMITES_PHYSIQUES.md). **Code d'analyse :** [protocole deux tensions](../research/experiment_two_channel_voltage.py). Le choix des tensions n'est qu'un banc d'essai possible, pas une interprétation physique imposée par le théorème.

### Contributions demandées
1. Proposer deux observables physiques indépendantes Q_K et Q_J, avec unités, méthode de mesure, provenance et incertitudes, **sans définir les observables à partir du rapport 2:3**.
2. Fournir un jeu de données horodatées (ou un lien public et sa licence) comprenant une période de calibration et une période de validation indépendante, idéalement avec données brutes et métadonnées instrumentales.
3. Déterminer gamma et omega par un mécanisme physique indépendant des résultats à prédire ; à défaut, signaler explicitement que leur estimation est seulement statistique.
4. Préenregistrer les prédictions, leurs marges d'incertitude, les critères d'échec et au moins un modèle de référence.
5. Partager aussi les résultats négatifs, les erreurs, les contre-exemples et les scripts reproductibles.

**Format minimal du CSV :** `t_s,qk_v,qj_v,sigma_qk_v,sigma_qj_v` pour l'essai électrique. Les colonnes sigma sont facultatives dans l'outil initial, mais indispensables pour une interprétation métrologique sérieuse. Pour d'autres observables, documenter les unités et adapter explicitement le protocole.

**Exécution :** `python research/experiment_two_channel_voltage.py --calibration calibration.csv --validation validation.csv`

**Soumettre une proposition :** [ouvrir une issue](https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN/issues/new) ou [une pull request](https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN/pulls). Indiquer : organisme ou statut indépendant, phénomène mesuré, provenance/licence des données, instrument, incertitudes, protocole, conditions de réfutation, coordonnées de contact publiques si souhaitées. Ne pas publier de données personnelles ou de secrets d'accès.

**Important :** publier cet appel ne signifie pas qu'un laboratoire a été contacté ou a accepté de collaborer. Les preuves algébriques du modèle ne démontrent pas une loi physique universelle. Respecter la licence et l'attribution du dépôt.

## EN — Call for laboratories and independent researchers

AL-MIZAN invites independent experimental teams to propose **falsifiable** tests of its two-pole harmonic model using existing instruments or openly licensed datasets. No participation, endorsement or experimental confirmation is implied.

Please provide independently defined, dimensionally consistent observables Q_K and Q_J; measurement units, timestamps, provenance and uncertainty; independent parameter determination where possible; separated calibration and held-out validation data; preregistered predictions and failure criteria; and comparisons with established baselines. Negative findings and counterexamples are explicitly welcome.

See the [mathematical dossier](../publications/2026-11-03_AL_MIZAN_THEOREME_HARMONIQUE_ET_LIMITES_PHYSIQUES.md) and [reproducible analysis script](../research/experiment_two_channel_voltage.py). Submit a [GitHub issue](https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN/issues/new) or [pull request](https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN/pulls). Please respect the repository license, attribution and dataset licenses.
