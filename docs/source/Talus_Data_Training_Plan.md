# Talus — Data & Training Plan

Everything needed to go from "we have an architecture" to "we have a trained, demoable risk engine." Three parts: what real data/info actually exists and where, how to generate synthetic training data that's physically grounded rather than arbitrary, and how to train and validate the models.

---

## Part 1 — Information needed, and what's actually available

The risk engine needs features across five categories. Below: what each needs, and the real source found for it (or the honest absence of one).

### Environmental
- **Rainfall** — real, high-quality source exists: **IMD gridded rainfall data**, 0.25°×0.25° resolution, daily, 1901–2024, from India Meteorological Department, Pune. https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html (also NetCDF format available). This is genuinely usable, not a stretch — pick a real mine-region's grid cell and pull its actual historical rainfall distribution to ground your synthetic rainfall values.
- **Groundwater / pore pressure** — no direct public feed for a specific mine. Treat as a derived/proxy variable from rainfall + time-since-last-rain in the synthetic generator (see Part 2).

### Geological / Topographic
- **Slope angle, slope height, terrain** — real sources: **ISRO Bhuvan CartoDEM** (1–3 arc-sec / 30–90m resolution, free, India-specific, from Cartosat-1) at https://bhuvan-app3.nrsc.gov.in/data/, or **NASA/USGS SRTM** (30–90m, global) via https://www.opendem.info/download_srtm.html or Google Earth Engine. Either gives you real elevation data to derive slope angle/height for an actual open-pit geometry — genuinely usable, not synthetic.
- **Rock type / geotechnical classification** — no single public Indian mine-specific dataset found. Use published rock-strength parameter ranges (cohesion, friction angle by rock type — sedimentary/igneous/metamorphic) from geotechnical literature as lookup tables, not a live dataset.

### Operational
- **Blasting frequency, blast vibration** — no public dataset exists for Indian open-pit mines. This must be synthetic, generated from realistic ranges reported in mining literature (typical peak particle velocity thresholds, blast frequency patterns), not fabricated arbitrarily.

### Visual / Structural (crack detection)
- **Crack imagery** — real, usable dataset confirmed: **Ultralytics Crack Segmentation Dataset**, 4,029 annotated images (3,717 train / 200 val / 112 test), single "crack" class, roads and walls. https://docs.ultralytics.com/datasets/segment/crack-seg — pairs directly with YOLO for instance segmentation, comes with a ready training recipe. Important honesty note (carried over from the pitch): this is road/wall crack imagery, **not mine-rock-face imagery** — a real domain gap. Use it to train the crack-detection *mechanism* (detecting and measuring cracks), and be upfront that mine-specific fine-tuning data doesn't exist publicly.

### Historical / Incident Data
- **Global landslide/rockfall event history** — real, substantial source: **NASA's Cooperative Open Online Landslide Repository (COOLR)**, which includes the Global Landslide Catalog (GLC, compiled since 2007, rainfall-triggered events worldwide with lat/lng, date, trigger type) at https://landslides.nasa.gov. This is landslides broadly, not rockfall-in-mines specifically, but it's real, dated, geolocated event data — useful for validating that your synthetic rainfall→risk correlation matches real-world patterns.
- **Academic benchmark for susceptibility modeling** — a genuine benchmark dataset exists: 7,360 slope units with landslide presence/absence and standard topographic/geomorphological variables, published specifically as a reference benchmark for susceptibility modeling research. https://www.sciencedirect.com/science/article/pii/S0012825224002551 — useful for checking your synthetic feature distributions and model behavior against a real academic standard.
- **Kaggle rockfall/landslide datasets** — several exist (e.g. kaggle.com/datasets/lukhilaksh/rockfall-dataset, kaggle.com/datasets/rajumavinmar/landslide-dataset) but are small, uncurated, community-uploaded — worth a look for inspiration on feature naming/structure, not something to build a credible pipeline on directly. Say so if asked, rather than presenting them as a primary source.
- **Landslide4Sense** — a real, well-documented remote-sensing benchmark (Sentinel-2 multispectral + slope + DEM, pixel-labeled, 3,799 train / 245 val / 800 test patches) at https://github.com/iarai/Landslide4Sense-2022. More relevant if you ever extend to satellite-image-based detection than to your current tabular risk engine, but worth knowing about.

### What has no public source at all — state this plainly in your own docs
Real Indian open-pit mine sensor telemetry (geotech instrumentation, actual blast logs, mine-specific incident records) does not exist publicly. This is the same honest limitation already baked into the PPT — nothing new, just confirmed by this research pass rather than assumed.

---

## Part 2 — Synthetic dataset generation method

The goal is a synthetic dataset that's **physically grounded**, not just randomly sampled — so the model learns real relationships (rainfall raises risk, steep slopes raise risk) instead of noise, and so your "why is this zone risky" SHAP explanations are demo-honest rather than arbitrary.

**Step 1 — Define the feature schema.**
Per zone: rainfall (mm, last 24h/7d), slope angle (°), slope height (m), rock type (categorical), crack density (from crack-detection features, if simulating), crack severity (derived), blasting frequency (events/week), blast vibration (peak particle velocity, mm/s), days since last inspection, prior incident flag (0/1), groundwater proxy (derived).

**Step 2 — Sample realistic feature values, not arbitrary ones.**
- Rainfall: sample from the *actual* IMD historical distribution for a real mining region's grid cell, not a made-up range.
- Slope angle/height: sample from real geometry ranges reported in open-pit mining literature (bench angles commonly 45–70°, overall slope angles 30–45°) or, better, derive directly from a real CartoDEM/SRTM tile of an actual mine area.
- Rock type: assign from a small categorical set, each tied to literature-typical cohesion/friction-angle ranges.
- Blasting/vibration: sample from literature-reported peak particle velocity and blast-frequency ranges for open-pit operations — labeled clearly as literature-derived, not measured.

**Step 3 — Generate labels using a physics-informed formula, not random assignment.**
Compute an approximate **Factor of Safety (FoS)** per synthetic zone using a simplified infinite-slope stability model:

```
FoS ≈ (c + (γ·h·cos²θ − u)·tanφ) / (γ·h·sinθ·cosθ)
```

where c = cohesion (from rock type), φ = friction angle (from rock type, degraded by crack density), θ = slope angle, h = slope height, γ = unit weight of rock, and u = pore pressure (derived from rainfall/groundwater proxy). Add a stochastic disturbance term scaled by blast vibration to represent blast-induced destabilization. Convert FoS to a risk label: lower FoS → higher risk category, with the same 5-band scheme as the pitch (Very Low → Critical). This is the exact "where does your risk score come from" defensible answer from your PPT — this step is what makes that answer literally true rather than aspirational.

**Step 4 — Add realistic noise and missingness.**
Add Gaussian noise to labels so the relationship isn't perfectly clean (real geotechnical risk isn't deterministic). Randomly null out some features per zone (e.g. missing vibration reading) to justify the "confidence score + missing evidence" feature already in your design — this isn't decorative, it directly feeds the confidence-calibration step in training.

**Step 5 — Sanity-check against real-world patterns.**
Check that your synthetic dataset reproduces known real-world correlations before training on it: rainfall should correlate positively with risk (consistent with rainfall-rockfall seasonal-link findings from real research), steep slope + high crack density should dominate high-risk zones. If these don't hold, the generator has a bug, not the model.

**Step 6 — Document and version it.**
Log the generation seed, feature ranges, and formula version. Tag every record as `synthetic: true` in the dataset itself — this is what lets you say "the prototype validates the architecture" honestly, both in the PPT and if a judge asks to see the data.

---

## Part 3 — Training plan

**Risk engine (Random Forest):**
1. Split by zone/spatial group, not random row split — synthetic zones sharing a generation seed are correlated, so a random split leaks information. Aim for 70/15/15 train/val/test.
2. Train a Random Forest classifier (risk band) or regressor (0–100 score); tune `n_estimators`, `max_depth`, `min_samples_leaf` via cross-validation on the training set.
3. **Calibrate the output probability** — Platt scaling or isotonic regression on top of the raw RF output — this is what turns a raw prediction into the "confidence: 76%" number the pitch depends on. Don't skip this; an uncalibrated model's probabilities are not trustworthy confidence values.
4. Evaluate with a reliability diagram / Brier score (calibration quality), not just accuracy — and weight recall on the "Critical" band more heavily than overall accuracy, since missing a real critical zone is far costlier than a false alarm on a low-risk one.

**Explainability (SHAP):**
- `TreeExplainer` works natively and fast on Random Forest — no extra training needed, but sanity-check it: confirm rainfall and crack density consistently show positive SHAP contribution to risk across zones, and that nothing flips sign in a way that doesn't make physical sense. This is your safeguard against presenting a broken model as "explainable."

**Crack detection (YOLO-seg on Crack-Seg dataset):**
- Fine-tune a YOLO segmentation model (`yolo26n-seg` or similar) on the Ultralytics Crack-Seg dataset — a ready training recipe is provided in their docs, genuinely a low-effort integration.
- Output crack length/density/orientation as structured features, feed *those* into the Random Forest risk engine as inputs — don't wire the CV model's output directly to a severity claim (consistent with the "generic crack imagery ≠ mine-specific severity" framing already in your Feasibility slide).

**Testing before the demo:**
- Feature ablation: remove one feature at a time, confirm risk score moves in the expected direction.
- Out-of-distribution check: feed an extreme synthetic zone (very steep slope, heavy rain, high crack density) and confirm it lands in Critical — this is your live what-if-simulator sanity check before judges touch it.
- Keep a fixed, rehearsed demo scenario (same seed, same zone) so the live demo is reproducible, not a live dice roll.

---

## Summary table — sources at a glance

| Data need | Real source found | Usable as-is? |
|---|---|---|
| Rainfall | IMD gridded data (imdpune.gov.in) | Yes |
| Slope/terrain | ISRO Bhuvan CartoDEM / SRTM | Yes |
| Crack imagery | Ultralytics Crack-Seg (4,029 images) | Yes, with noted domain gap (roads/walls, not mine rock) |
| Historical incidents | NASA COOLR/GLC | Yes, for pattern validation — global landslides, not mine-specific |
| Susceptibility benchmark | ScienceDirect 7,360-slope-unit benchmark | Yes, for sanity-checking synthetic data |
| Rock type/geotech params | None public | No — literature lookup tables only |
| Blast vibration/frequency | None public | No — literature-derived ranges only |
| Mine-specific sensor telemetry | None public | No — synthetic throughout |
