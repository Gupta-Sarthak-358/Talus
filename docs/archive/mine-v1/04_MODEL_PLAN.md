> **ARCHIVED — Mine V1 (SIH25071 open-pit). Active track is SIH26001 NER landslide — see docs/sih26001/. Do not use for new work.**

---

# Talus Model Plan

**Status:** Updated for Research Freeze · Trace to: `docs/02_ARCHITECTURE.md`, `docs/03_DATA_PLAN.md`, `docs/05_FEATURE_SCHEMA.md`

The ML methodology. **Physics lives in the generator, not in the Random Forest.** The RF learns the mapping from a physics-informed synthetic state to the risk target; it does not discover geotechnical physics.

---

## 1. Pipeline

```text
GENERATOR v1 (physics-informed synthetic state)
     ↓  per zone per timestep: internal fields → ML-facing features
Physics-informed state
     ↓
Risk target (FoS-informed risk band / score)
     ↓
Train / validation / test split (by zone group)
     ↓
Random Forest
     ↓
Probability calibration
     ↓
Risk probability → risk score (0–100) + confidence
     ↓
SHAP explanation
```

Key distinction: the **generator** encodes the physics (rainfall process, bench geometry, material parameters, PPV attenuation, crack growth, FoS); the **model** only maps measured-looking features to the risk target. See `docs/GENERATOR_V1_SPEC.md` and `docs/05_FEATURE_SCHEMA.md`.

## 2. Label Generation

Risk labels come from the physics-informed generator (details in `docs/03_DATA_PLAN.md` §D and `docs/GENERATOR_V1_SPEC.md`):

- Simplified infinite-slope FoS:

  ```text
  FoS ≈ (c + (γ·h·cos²θ − u)·tanφ) / (γ·h·sinθ·cosθ)
  ```

- c, φ from GENOLOGY constants (degraded by crack density); u from rainfall/groundwater + water-filled cracks; θ, h from TERRAIN bench layer; blast disturbance + crack severity modulate the stochastic disturbance term.
- Lower FoS → higher risk. FoS is mapped to risk bands (Very Low → Critical).
- Labels are **not randomly assigned** — they follow physically sensible relationships so SHAP explanations are demo-honest.

## 3. Feature Categories (used by generator + model)

Every feature used downstream is one of five kinds. This distinction is the contract in `docs/05_FEATURE_SCHEMA.md`:

| Kind | Meaning | Examples |
|---|---|---|
| **Observed / sourced** | drawn from a real grounding distribution | `rainfall_24h_mm`, `rainfall_7d_mm`, `slope_angle_deg` (DEM part) |
| **Derived-physical** | computed from physics inside the generator | `blast_vibration_ppv_mms` (attenuation), `crack_depth_m`, `pore_pressure_kpa`, FoS |
| **Synthetic / scenario** | designed, not measured anywhere | `prior_incident`, `days_since_inspection`, `missing_features` |
| **Latent / internal** | generator internals, NOT exported to ML/API | `charge_per_delay_kg`, `blast_distance_m`, `dominant_frequency_hz`, `water_filled` |
| **ML-facing** | the stable external schema consumed by model + API | the 12 fields in `docs/05_FEATURE_SCHEMA.md` |

Rule: internal fields may evolve freely; **ML-facing names are frozen** for Member 3.

## 4. Training

- **Split:** 70 / 15 / 15 train / validation / test.
- **Split strategy:** by **zone / spatial group**, not random rows — synthetic zones sharing a generation seed are correlated; a random split leaks information.
- **Model:** Random Forest (`scikit-learn`).
- **Targets:** risk band (classification) and/or 0–100 score (regression); MVP exposes both.
- **Hyperparameters:** tune `n_estimators`, `max_depth`, `min_samples_leaf` via cross-validation.
- **Calibration:** `CalibratedClassifierCV` (Platt / isotonic) on top of raw RF output → reported **confidence**. Required, not optional.

## 5. Explainability

- **SHAP `TreeExplainer`** — native and fast on Random Forest.
- **Sanity check:** rainfall and crack density show consistently positive SHAP contributions to risk; nothing flips sign in a way that violates physics. (Physics is enforced in the generator; SHAP should reflect it.)
- Safeguard against presenting a broken model as "explainable."

## 6. Evaluation

- MAE / RMSE (regression) and/or precision / recall (classification).
- **Critical-band recall** weighted above overall accuracy.
- **Brier score** + reliability diagram — calibration quality.
- **Feature ablation** — removing one feature must move risk in the expected direction.
- **Out-of-distribution check** — an extreme synthetic zone (very steep, heavy rain, high crack density, blast) must land in Critical; doubles as the what-if-simulator sanity check.

## 7. Generator Validation Gates (before any training)

Physics, distribution, and provenance checks must pass first — see `docs/GENERATOR_V1_SPEC.md` §10. If the generator's synthetic state breaks physics (e.g. FoS out of a bounded range, crack depth > bench height, PPV worse than the attenuation law allows), the fix is in the generator, not the model.

## 8. CV (Crack Detection) — Tier 2+

- Fine-tune a YOLO segmentation model on Ultralytics Crack-Seg.
- Output structured features: crack **length, density, orientation**.
- These feed the risk engine's `crack_density` / crack-feature inputs; **not** wired directly to a mine-specific severity claim (`docs/08_LIMITATIONS.md`).

## 9. Reproducibility

- Fixed `SYNTHETIC_SEED` (default 42) and versioned generator config (`docs/GENERATOR_V1_SPEC.md` §9).
- Model artifacts git-ignored; metadata (params, metrics, data version) committed.
- Fixed, rehearsed demo scenario → reproducible output, not a live dice roll.

---

*Note: prototype thresholds, not calibrated safety standards. Final operational decisions remain with qualified personnel.*