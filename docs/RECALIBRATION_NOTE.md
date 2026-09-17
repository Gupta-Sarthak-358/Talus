# Recalibration for Deployment Prevalence (SIH26001)

**Problem**: training matrix is balanced 1468 pos / 1468 neg (pi_train = 0.5) for learnability, but real NER hillslope-day prevalence is ~1% (pi_real ≈ 0.01). Raw isotonic calibrated on 50% is honest for OOF Brier/ECE but over-states absolute P(landslide) in the field — the SK→WB Brier blowup (0.29→0.11 between directions) is the same symptom.

**Fix (Bayes prevalence correction)** — no retraining, no score change:

```
p_real = p_cal * (pi_real/pi_train) / [ p_cal*(pi_real/pi_train) + (1-p_cal)*((1-pi_real)/(1-pi_train)) ]
       with pi_train=0.5, pi_real=0.01 => p_real = p_cal*0.02 / (p_cal*0.02 + (1-p_cal)*1.98)
```

- Score (0–100) stays frozen: `score = round(p_raw*100)` — bands, decisions, routing, warning state unchanged.
- Confidence shown to officers remains `p_cal` (prototype target) with label "prototype-window".
- Added field `confidence_real_1pct` = p_real — shown as "per hillslope-day at ~1% base rate" in the API/evidence, for judge Q&A.
- Per-corridor note: Lachung/Darjeeling reweight identically; region-specific isotonic is post-hackathon (needs ≥200 dated positives/corridor).

**Evidence**: see `ml/sih26001/reports/calibration.md` (Brier 0.081→0.11 recalibrated) and `/api/model/calib?pi_real=0.01` response.

**Frontend**: ZoneIntelligencePanel now shows both: "Prototype 72% · ~1% base rate → 2.1% / hillslope-day" — never replaces the band.
