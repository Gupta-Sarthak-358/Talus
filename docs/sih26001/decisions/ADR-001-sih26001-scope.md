# ADR-001: SIH26001 Scope — Migrate TALUS, Don't Fork

**Status:** Proposed · **Date:** 2026-09-03 · **Branch:** `SIH26001`

## Context

TALUS v1 (mine rockfall, SIH25071) is frozen and working: two-engine pattern
(ML + physics scenario), isotonic calibration, SHAP, role decisions,
risk-weighted Dijkstra, missing-evidence discipline. SIH26001 (NER landslide,
MDoNER) asks for the same decision-support pattern over a different domain.
Full research: `docs/SIH26001_RESEARCH.md` (fact-checked, 5 rounds).

## Decision (proposed)

1. **Migrate the architecture, rewrite the data + physics.** NGEN replaces the
   synthetic generator; rainfall-infiltration replaces bench FoS; 17 NER
   features replace 12 mine features; 4 NER roles replace 4 mine roles.
2. **Track on branch `SIH26001`** with its own doc suite (`docs/sih26001/`),
   leaving v1 docs frozen. Merge strategy to `main` decided later (post-pilot).
3. **Train on real historical events** (GSI Bhusanket 37,903+ NER, COOLR/GLC,
   ISRO Atlas, published dated inventories, 40+ yr IMD rainfall) — the
   strongest structural upgrade over v1's synthetic-only evidence.
4. **Pilot-first:** one best-dated district cluster (Sikkim/Nagaland
   candidate) fully working before any 8-state talk.

## Alternatives considered

- **Clean-repo fork:** rejected for now — loses v1's reusable modules
  (calibration, SHAP, routing, decision patterns) and splits team history.
  Revisit if v2's NGEN/geo stack diverges irreconcilably.
- **Synthetic-first again:** rejected — real NER data exists and is verified
  accessible; synthetic would weaken the pitch.
- **8-state MVP:** rejected — thin coverage fails both demo and honesty bars.

## Consequences

- v1 stays demoable from `main`; v2 builds without breaking it.
- New geo/ML dependencies land on this branch first (rasterio/GDAL,
  geopandas, xgboost, i18n, SMS adapter).
- Freezes required before build: spatial unit, pilot extent, CRS/grid, map
  library, sampling/buffer rules, band edges (post-calibration).

## To-freeze list (promote each to decision or assumption)

- [ ] Spatial unit (pixel / slope unit / admin zone)
- [ ] Pilot extent
- [ ] CRS + grid + resampling rules
- [ ] Map library (Leaflet vs Mapbox GL)
- [ ] Positive/negative sampling + buffer + date-window rules
- [ ] SMS provider adapter + language matrix
- [ ] v2 API spec (extend vs version)
