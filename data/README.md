# data

Raw, processed, and synthetic data for the Talus prototype.

**Rule: datasets live outside git.** Data files under `data/` are git-ignored (`data/raw/*`, `data/processed/*`, `data/synthetic/*`). Only the following are committed:

- `README.md` (this file)
- Schemas / `.schema.*` files
- `.meta.json` and `metadata.json` records
- `.sample.csv` small sample rows

Large raw datasets, feature stores, and trained-model inputs live outside normal git (Git LFS, Drive, Hugging Face, or internal storage).

---

## Layout

```text
data/
├── raw/                  ← source datasets (large, outside git where sensible)
│   ├── imd/              → IMD gridded rainfall (0.25°, 1901–2024)
│   ├── dem/              → Copernicus GLO-30 tile (region terrain)
│   └── crack_seg/        → Ultralytics Crack-Seg dataset (4,029 images)
│
├── processed/            ← engineered features + grounded constants
│   ├── imd/              → IMD extraction + analysis (rainfall features)
│   ├── terrain/          → DEM-derived elevation/slope (regional layer)
│   ├── geotech/          → Neyveli material constants (grounded)
│   ├── blasting/         → Neyveli blast/PPV constants (grounded)
│   ├── cracks/           → crack-state constants (grounded)
│   └── crack_features/   → crack length/density/orientation (CV output, Tier 2+)
│
├── synthetic/            ← generated training data
│   └── v1/               → train/validation/test + metadata.json
│
└── README.md
```

## Synthetic data versioning

Each version directory under `synthetic/` must contain a `metadata.json`:

```json
{
  "dataset": "talus_synthetic_v1",
  "seed": 42,
  "generator_version": "1.0",
  "created": "2026-08-19",
  "source_distributions": ["IMD rainfall", "literature-derived rock parameters"],
  "label_method": "physics-informed FoS",
  "synthetic": true
}
```

This is how we know, six months later, where the numbers came from. See `data/synthetic/v1/metadata.json` and `docs/03_DATA_PLAN.md`.