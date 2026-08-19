# data

Raw, processed, and synthetic data for the Talus prototype.

- `raw/` — source datasets (IMD rainfall, DEM, Crack-Seg). Data files are git-ignored; only schema/notes are committed.
- `processed/` — engineered features (rainfall, terrain, crack features).
- `synthetic/` — generated training data with versioned metadata.

See `docs/03_DATA_PLAN.md` for the full plan and provenance table.
See `data/README.md` (top-level) for usage rules.