# TALUS v2 Demo Scenario — SIH26001 (skeleton, NOT frozen)

**Status:** Skeleton — numbers will be frozen against the real v2 model once
it exists. Do not quote any number here to judges. · **Trace to:**
`01_REQUIREMENTS_SIH26001.md`

(Replaces nothing yet. v1 demo `docs/06_DEMO_SCENARIO.md` stays frozen for
the mine track.)

---

## Pilot extent

TBD by ADR (candidate: best-dated-inventory district cluster — Sikkim or
Nagaland, per research §3.2). All screens below run on the frozen pilot +
frozen scenario with recorded fixtures (no live network).

## Screen 1 — NER overview

GIS heatmap, 5-band colors. Pilot units colored by score/band. Road overlay
shows open / at-risk / blocked. Village priority flags visible.

*Freeze later: unit count, band distribution, fixture IDs.*

## Screen 2 — "Why?" (selected high-risk unit)

Tree SHAP panel: base value + top contributions with NER feature names
(e.g. `distance_to_road`, `rainfall_7d_mm`, `slope_angle`, `soil_moisture`).

*Freeze later: real SHAP values from the trained model. Say out loud what the
top drivers are and which evidence is missing.*

## Screen 3 — ML what-if (counterfactual) + documented caveat

Raise `rainfall_24h_mm` on a moderate unit; show score movement **with the
off-manifold caveat**: "Single-feature overrides break realistic correlations,
so this is a counterfactual, not a causal answer. For causal questions we use
the rainfall scenario engine."

*Freeze later: input values, output scores.*

## Screen 4 — Causal what-if (rainfall threshold scenario)

Threshold replay: Monga 2026 MDL curve (E = −11.10 + 0.62×D) and/or
Dahal–Hasegawa >144 mm/day preset over the pilot monsoon window. Show
saturation trajectory → FoS divergence → newly escalated units + evidence
timeline with physical causes (not SHAP).

*Freeze later: preset definition, divergence numbers, escalated unit IDs.*

## Screen 5 — Roads + routing

Risk-aware route between two pilot points avoids a high-risk segment;
shortest path crosses it. Road-status panel lists at-risk/blocked segments.

*Freeze later: origin/destination, avoided segments.*

## Screen 6 — Field report + alert (if committed)

Officer queue shows a geo-tagged test report; escalation fixture triggers a
multilingual test alert (2+ languages) and an offline-capture→sync pass.

## Rehearsal checklist (activate at freeze)

- [ ] Pilot extent + fixtures reproduce deterministically
- [ ] Scores/confidence match committed calibration artifact
- [ ] SHAP values match model artifact
- [ ] Off-manifold caveat spoken before Screen 3
- [ ] Threshold preset + divergence numbers reproduce
- [ ] Routing avoids the documented segment
- [ ] No network calls; everything local/ recorded fixture
- [ ] Limitations slide ready (see `08_LIMITATIONS_SIH26001.md`)

## PS (a)–(g) traceability checklist

| PS bullet | Covered in | Demo screen |
|---|---|---|
| (a) multi-source data (rain, moisture, satellite, terrain, history) | NGEN + FR-01 | Screen 1 (provenance footnote) |
| (b) AI/ML high-risk prediction | FR-02/03/04 | Screens 1–2 |
| (c) real-time alerts to admins + communities | FR-11 (+ FR-06 roles) | Screen 6 (fixture) |
| (d) GIS mapping of roads, villages, infrastructure | FR-07/09 | Screens 1, 5 |
| (e) geo-tagged citizen/field uploads | FR-10 | Screen 6 (officer queue) |
| (f) dashboards: severity, roads, weather forecast, emergency priority | FR-09 | Screens 1, 5 |
| (g) multilingual + offline | FR-12 | Screen 6 (2+ languages, sync pass) |
| Expected Solution: IMD/satellite/sensor integration | Sensor adapter (02 §5, 03 §A) | Fixture noted Screen 1 |
| Expected Solution: cloud + offline sync | Cloud path (02 §5) | Architecture slide, not live demo |

## Explicitly NOT claimed (carry into the frozen version)

- Scores are not probability of a specific landslide; confidence is calibrated
  P(elevated susceptibility) under the prototype target.
- No in-situ sensors were used; deployment needs partner feeds.
- Bands are prototype operational bands, not safety standards.
