# Talus Model Plan

**Status:** Frozen for MVP · Trace to: `docs/02_ARCHITECTURE.md`, `docs/03_DATA_PLAN.md`

The complete training methodology for the Talus risk engine.

---

## 1. Pipeline

```text
Data
 ↓
Feature processing
 ↓
Physics-informed synthetic label (FoS)
 ↓
Train / validation / test split (by zone group)
 ↓
Random Forest
 ↓
Probability calibration
 ↓
Risk probability
 ↓
Risk score (0–100) + confidence
 ↓
SHAP explanation
```

## 2. Label Generation

Synthetic labels are produced by a physics-informed method (full details in `docs/03_DATA_PLAN.md`).

FoS is approximated using a simplified infinite-slope stability model:

```text
FoS ≈ (c + (γ·h·cos²θ − u)·tanφ) / (γ·h·sinθ·cosθ)
```

- Lower FoS → higher risk.
- The resulting FoS is mapped to prototype risk bands (Very Low → Critical).
- A stochastic disturbance term scaled by blast vibration represents blast-induced destabilization.

Risk labels are **not** randomly assigned; they follow a physically sensible relationship so SHAP explanations are demo-honest.

## 3. Training

- **Split:** 70 / 15 / 15 train / validation / test.
- **Split strategy:** by **zone / spatial group**, not random rows — synthetic zones sharing a generation seed are correlated; a random split leaks information.
- **Model:** Random Forest (`scikit-learn`).
- **Targets:** either risk band (classification) or 0–100 score (regression); final MVP exposes both score and band.
- **Hyperparameters:** tune `n_estimators`, `max_depth`, `min_samples_leaf` via cross-validation on the training set.
- **Calibration:** Platt scaling or isotonic regression on top of raw RF output (`CalibratedClassifierCV`). This converts raw probability into the reported **confidence** value. Required, not optional.

## 4. Explainability

- **SHAP `TreeExplainer`** — native and fast on Random Forest.
- **Sanity check:** rainfall and crack density should show consistently positive SHAP contributions to risk; nothing should flip sign in a way that violates physics.
- This is the safeguard against presenting a broken model as "explainable."

## 5. Evaluation

Metrics:

- MAE / RMSE (regression) — if scoring 0–100.
- Precision / recall (classification) — if banding.
- **Critical-band recall** — weighted more heavily than overall accuracy; missing a real critical zone is costlier than a false alarm on a low-risk zone.
- **Brier score** — calibration quality.
- **Reliability diagram** — visual calibration check.

Also:

- **Feature ablation** — remove one feature at a time; risk score must move in the expected direction.
- **Out-of-distribution check** — an extreme synthetic zone (very steep, heavy rain, high crack density) must land in Critical. This doubles as the live what-if-simulator sanity check.

## 6. CV (Crack Detection) — Tier 2+

- Fine-tune a YOLO segmentation model (`yolo26n-seg` or similar) on the Ultralytics Crack-Seg dataset.
- Output structured features: crack **length, density, orientation**.
- Feed those features into the Random Forest risk engine.
- Do **not** wire CV output directly to a mine-specific severity claim (see `docs/08_LIMITATIONS.md`).

## 7. Reproducibility

- Fixed `SYNTHETIC_SEED` (default 42) and versioned generator config.
- Model artifacts are git-ignored; metadata (params, metrics, data version) is committed.
- Fixed, rehearsed demo scenario → reproducible output, not a live dice roll.

---

*Note: prototype thresholds, not calibrated safety standards. Final operational decisions remain with qualified personnel.*