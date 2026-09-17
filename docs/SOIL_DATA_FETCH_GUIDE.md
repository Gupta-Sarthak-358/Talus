# Soil data — provenance & refresh guide (SIH26001 · 2025-11-14)

> 2025-11-15 deltas: Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched); Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`; Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`; PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`; CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT


Current truth: soil inputs are **ESA CCI COMBINED v09.2 daily** (1978–2024 window-means, `C3S-SOILMOISTURE-L3S-SSMV-COMBINED-DAILY-*` ~2.4 MB/day, 0.25° global, `flag` kill-bits `4|8|16|32`, `sm` m³/m³) plus **JMA 3-tank SWI** (`backend/app/swi.py` `L1=15 L2=60 L3=60` → `tanh(SWI/100)`) for warning overlay only. Scoring stays frozen on the 17-feat `soil_moisture` proxy. This replaces the rain-fix-era “event-anchored soil TODO” — what to fetch now is refresh, not backfill.

## What is live today

- **CCI v09.2**: 1978–2024 dailies in `data/raw/soil/v09.2/` (May–Oct window-means used for NGEN). Produces per-zone `soil_moisture` 0.27-class window mean. Mountain gaps (frozen/snow/RFI) → masked + `evidence_quality` tagged `approximate`.
- **SWI 3-tank**: `swi.py` consumes `rainfall_7d + 0.3*rainfall_30d` + optional `forecast_daily` (Open-Meteo 3d) → `GET /api/soil/swi` + `GET /api/warning/state` SWI reason stamp. Normalized 0–1.
- **API**: `GET /api/soil/swi?location=gangtok|lachung|darjeeling` (JMA per zone, forecast blend), `GET /api/warning/state` shows SWI alongside effective rain / wound / forecast / quake.

## Refreshing CCI (use this, not blind mirror)

`scripts/download_cci_soil.py` pulls May–Oct dailies via CEDA JSON listing into `data/raw/soil/v09.2/` (stdlib only, skips existing, logs `_fetch_log.jsonl`). Default 2006–2024 ≈ 3.5k files ≈ 8 GB; full 1978–2024 ≈ 40 GB (script subsets bbox on read).

```bash
python scripts/download_cci_soil.py --probe 2024
python scripts/download_cci_soil.py
python scripts/download_cci_soil.py --start 1978 --end 2024  # full tail
```

- Where: CEDA Archive `https://data.ceda.ac.uk/neodc/esacci/soil_moisture/data/daily_files/COMBINED/` (latest `v09.2` dir) or ESA CCI portal `https://esa-soilmoisture-cci.org` (TCDR COMBINED).
- Where to put: `data/raw/soil/v09.2/` (git-ignored, LOCAL ONLY — never commit). Loader globs `C3S-SOILMOISTURE-*.nc`.
- After fetch: `python scripts/build_training_matrix.py` + `python scripts/train_sih26001.py` to re-ablate; expect `no_soil` delta currently −0.0074 — with event-daily soil it should grow.
- Version note: current window-means are v09.2; on landing, overlap-check June 2024 at the bbox — small bias → tag rows by version; large bias → recompute 2024 window in v09.2 for consistency.

## Live sensor / reanalysis options (next-layer, not current)

| Option | Product | Why | Access | Put | Tag |
|---|---|---|---|---|---|
| ERA5-Land hourly | `volumetric_soil_water_layer_1` 0–7 cm, 0.1°, 1950–present | Best Himalayan resolution, fills 1965–2005 CCI cannot see; backfill + cross-check | Copernicus CDS `cds.climate.copernicus.eu` (free, `cdsapi`, area `[28,88,27,89]`) | `data/raw/soil/era5land_*.nc` | `reanalysis-assimilation` |
| GLDAS Noah | `GLDAS_NOAH025_3H` `SoilMoi0_10cm_inst` 0.25° 2000–present | Second opinion 2000+ if CCI gaps bad over Sikkim | NASA GES DISC / Giovanni | `data/raw/soil/gldas_*.nc` | `reanalysis` |
| In-situ (future) | Adapter-fixture ready | Ground truth | Field network | `data/raw/soil/in_situ/` | `in-situ` |

**Not worth it for training**: SMAP L4 (2015+, 9 km) — too late for 1965–2015 inventory; IMD in-situ soil — no public historical network for Sikkim.

## When you have new files

Tell which option + year span landed; `scripts/event_soil_upgrade.py` (mirrors `event_rain_upgrade.py` tiers: exact-date window → that-year June-window mean → quasi-static fallback, per-row `soil_source` tags, same 22-col schema) + manifest + retrain + re-ablate. The ablated `soil_moisture` proxy → observed SWI transition is the expected unlock.

## Honesty tags

Every row carries `evidence_quality`: `REAL` (direct CCI cell), `PROXY` (reanalysis/model blend), `STUB` (none — zero STUBs shipped, `feature_matrix.sample.csv` validator-enforced). Gaps are `approximate` in `missing_evidence`.