# AL-MIZAN — Quick verification / Vérification rapide

**For laboratories / Pour les laboratoires:** This is a 5-minute orientation, not a 5-minute physical proof.

## 1. What is already mathematically testable? / Ce qui est vérifiable
Two-pole basis `v=(-3,2)`, `w=(2,3)`:
```text
A=(-3 Q_K+2 Q_J)/13
B=( 2 Q_K+3 Q_J)/13
R=2 Q_K+3 Q_J=13 B
Z=A+iB
Z'=(-gamma+i omega) Z   [ASSUMPTION / HYPOTHÈSE]
```
Run `python research/verify_al_mizan.py` (Python 3 standard library). It verifies algebra and a conditional constant-parameter solution, **not** experimental validity.

## 2. How to test on data / Comment tester sur données
For a *possible* two-voltage experiment, provide two independent CSV files, strictly time-ordered and non-overlapping:
```csv
t_s,qk_v,qj_v,sigma_qk_v,sigma_qj_v
```
Use actual measurements, not generated values. Preserve instrument provenance, units, calibration and uncertainty records. Execute:
```bash
python research/experiment_two_channel_voltage.py --calibration calibration.csv --validation validation.csv
```
The script estimates gamma and omega on calibration only, predicts held-out validation, and reports vector RMSE versus persistence baseline. It **does not** incorporate a full metrological uncertainty test or demonstrate that fitted parameters are independent physical laws. This is an initial screening tool, not a conclusive experiment.

## 3. What would count as stronger evidence? / Preuve expérimentale plus solide
- Define Q_K and Q_J independently, with physical units and without encoding the desired 2:3 relation.
- Derive gamma and omega *before* validation from an independent physical mechanism, not from the same outcome.
- Preregister uncertainty bounds, reference models, predicted events, and failure criteria.
- Replicate on independent datasets or instruments; report negative results too.

## 4. Respond / Répondre
[Open international research issue #12](https://github.com/Loulbak78920/ASTRO-QODE-ALMIZAN/issues/12) · [Full bilingual invitation](INTERNATIONAL_EXPERIMENTAL_COLLABORATION.md) · [Mathematical dossier](../publications/2026-11-03_AL_MIZAN_THEOREME_HARMONIQUE_ET_LIMITES_PHYSIQUES.md).

**Status:** Open for independent replication. No universal physical validation established.
