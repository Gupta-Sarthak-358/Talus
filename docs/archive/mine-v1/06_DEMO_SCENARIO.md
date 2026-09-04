> **ARCHIVED — Mine V1 (SIH25071 open-pit). Active track is SIH26001 NER landslide — see docs/sih26001/. Do not use for new work.**

---

# Talus Demo Scenario — v2 (re-frozen against real Model v1)

Status: FROZEN. Supersedes the v1 expectations (which were written against the
mock scorer and are historically interesting but operationally wrong).
Every number below is reproduced by the frozen RF Model v1 + isotonic
calibration + Scenario Engine v1.5, all deterministic (fixed seeds).

## Initial state (real corpus: last day of held-out world seed 91)

| Zone | Risk | Band | Confidence* |
|---|---|---|---|
| A | 89 | Critical | 0.91 |
| B | 100 | Critical | 1.00 |
| C | 66 | Moderate | 0.44 |
| D | 99 | Critical | 0.95 |

\* confidence = isotonic-calibrated P(score >= 75) -- calibrated probability of
elevated SYNTHETIC risk under the prototype target definition. Calibration fit
on out-of-fold train-seed predictions; evaluated on validation seeds only
(Brier 0.081 vs 0.116 naive; ECE 0.095 vs 0.157).

## Demo narrative (honest version)

### Screen 1 — Mine overview
Zones colored by score/band above. A/B/D chronically critical, C moderate --
independently reproduces the generator's known structure.

### Screen 2 — "Why?" (Zone C)
Real Tree SHAP (base value 53.92):

| Feature | SHAP |
|---|---|
| crack_severity_critical | +19.71 |
| slope_angle_deg | -15.68 |
| rock_type_clayey_sandstone | +11.47 |
| slope_height_m | -8.40 |

### Screen 3 — ML What-If (counterfactual) + its documented caveat
Raising rainfall_24h to 150 mm on Zone C: score stays ~65-68 (Moderate).
Raising groundwater_proxy stepwise 182 -> 500: score drifts DOWN to 58.

**Say this out loud:** "Single-feature overrides move the input off the
manifold of realistically correlated states, so the ML counterfactual is not
a causal answer. For causal questions, TALUS uses the Scenario Engine."

### Screen 4 — Causal What-If (the showstopper)
Historical template replay: Dec-1902 (1,088 mm/month, max day 297.6 mm --
IMD provenance), Zone C, injected day 550 of a 3-year horizon.

Expected outputs:
- max groundwater proxy: **840.8 mm**
- open-crack branch FIRES (critical AND water-filled AND face >= 60 deg):
  **true**
- **FoS divergence vs baseline: -0.761**, first at day ~553
- **51 days** diverge by > 0.01 FoS
- Evidence Timeline: >= 25 cause-attributed events, e.g.
  "day 368: heavy rainfall (+74 mm/24h), groundwater proxy rose (+71 mm),
  cracks became water-filled"

Narrative: "A single extreme storm barely moves the score. Repeated extreme
exposure accumulates crack damage until a physical threshold activates and
stability drops. Acute shock is not accumulated deterioration -- TALUS knows
the difference."

### Screen 5 — Routing
Risk-aware route A -> D avoids Zone B (`avoided_zones: ["B"]`); shortest route
crosses it.

## Rehearsal checklist

- [ ] Initial scores reproduce: 89 / 100 / 66 / 99 (deterministic, seed 91 states)
- [ ] Zone C explanation returns real SHAP (base 53.92, values above)
- [ ] Confidence values match calibrator artifact (talus_calibration_v1.joblib)
- [ ] ML what-if on C: acknowledge off-manifold caveat before showing
- [ ] Causal Dec-1902 3-year: branch fired = true, divergence -0.761
- [ ] Evidence timeline events carry physical causes (not SHAP)
- [ ] Routing avoids B
- [ ] No network calls; everything local

## Explicitly NOT claimed

- Scores are not probability of failure; confidence is calibrated P(elevated
  synthetic risk) under the prototype target definition.
- No real mine telemetry was used; deployment requires a mining-partner feed.
- Thresholds are prototype operational bands, not calibrated safety standards.
