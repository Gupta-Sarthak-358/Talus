# TALUS Assumptions — SIH26001

**Status:** Built — validated 2025-11-15 · Each assumption is falsifiable and owned. `5` validated via `673/73 dated` temporal `metrics.md:32` (n=807 RF AUC 0.8568 Brier 0.0978), `2` via `CCI v09.2 0.271` `manifest.sample.json:22` + SWI `swi.py:14`, `3` via `USGS n27_e088` `usgs_s234.json:1` D8 90 voids 0.17%, `4` via `OSM 1014/226/504` `roads_osm_provenance.json:1` (demo topology) — all logged. · **Source:** `docs/SIH26001_RESEARCH.md` §6–§9

## Data

1. **IMD 0.25° gridded rainfall resolves pilot triggers at historical-truth scale (+ live blend).** 0.25° (~27 km) is coarse vs slope scale; hyperlocal cloudbursts will be missed at trigger resolution. Historical truth remains `ind2024_rfp25.nc` (1901–2024) `14.0/327.3/712.2`; live skill comes from Open-Meteo 7-day blend (1h cache, `GET /api/forecast/live:1154`) + IMD_API_KEY district feed gated (`GET /api/forecast/imd-live:1124`). Mitigation: observed vs forecast provenance always separated (fixtures fallback honest); GPM cross-check deferred to post-pilot adapter.
2. **CCI v09.2 soil moisture is a usable saturation proxy** at prototype scale despite 0.25° cell (same-cell all 12 slopes window-mean 0.271). Tagged `satellite-observed` (stronger than ERA5 reanalysis, which was never needed) everywhere it appears. Warning layer upgrades it via **JMA 3-tank SWI** `swi.py:14` L1=15 L2=60 L3=60 a1=0.10 b1=0.12 (rainfall + forecast blend → `tanh(SWI/100)`), mitigating quasi-static 0.271.
3. **SRTM 30m resolves pilot terrain features** (slope/TWI/SPI/drain) adequately for susceptibility (not for site engineering). Void handling 90/0.17% neighbour-mean filled, slope neighbourhoods void-free, D8 priority-flood on 7.7×5.9km crop `usgs_s234.json:1`.
4. **OSM roads/rivers presence is proven, geometry is demo topology.** Overpass bbox queries prove counts Gangtok 1014 / Lachung 226 / Darjeeling 504 `roads_osm_provenance.json:1` (example NH310A way 47416074), but R1–R4 geometry is centroid-aligned deterministic to keep R2 avoidance + R4 bottleneck isolation pedagogical (`data.py:118` `GRAPH`, `main.py:496` `_road_graphs_for` drops R2 from hazard graph). Stated in provenance.json note and admin panel; `osm-qa-unverified` kept until full OSM trace routing replaces demo topology.
5. **Undated inventory events can seed season-window positives** without corrupting the target, provided `event-date:approximate` tags flow to missing-evidence and a dated-only temporal holdout is reported. **Validated:** `673/73 dated` temporal `done:true` `manifest.training.json:144` `RF AUC 0.8568 Brier 0.0978` `metrics.md:32` (earlier 61-cluster rescue superseded by 2025-11-14 stable split).
6. **Negative sampling at >300 m from known landslides** yields true negatives often enough for the prototype (buffer distance frozen in model plan; sensitivity on buffer reported). **Built:** `2936 rows 1468+1468` negatives `>300m` `seed 42` `manifest.training.json:42`, `wound 4/2936` rare appended.
7. **Bhukosh vector will eventually give per-slope lithology/lineament.** Meanwhile, **published-map uniform PROXY** (`lingtse_granite_gneiss`, lineament 0.8) is honest until vector is reachable; timeout evidence `bhukosh_vector_attempt.json:1` (WFS/WMS 15s both) justifies omission from X (`manifest.training.json:263`). Assumption that re-running `extract_lithology.py --wfs` when reachable will replace uniform without schema change.

## Modeling

8. **RF + XGBoost transfer from v1's pattern** to NER features with published AUC 0.89–0.96 as realistic bar (not promise). **Achieved OOF:** RF 0.9338 XGB 0.9418 LGBM 0.9406 vs LR 0.8914 `metrics.md:9`; previous stale 0.8983 expunged.
9. **Spatial-cluster CV (KMeans-8, GroupKFold) + temporal holdout** is sufficient validation for a prototype (no field deployment claim). Temporal `807` 673/73 AUC 0.8568 Brier 0.0978 `metrics.md:32` is the clean check; isotonic same-OOF optimism is disclosed `calibration.md:8`.
10. **LHASA 2.0 over NER is a fair beat-the-global benchmark** (resolution and target differences documented, not hidden); plus **SWI 3-tank** is assumed to improve warning skill over single soil_moisture 0.271 (stated as overlay, not as scoring lever — score stays frozen `raw_proba*100`).
11. **Per-zone local effective-rain thresholds** (Gangtok 385/395/410/375 `warning_thresholds.json:1`) + quake-conditioned −25% (USGS 26 `usgs_quakes.json:1`) improve warning state specificity over global `_WARN_EFFECTIVE_RAIN 390` — operational, not learned, updated `0.9*old+0.1*event`.
12. **12 demo slopes sufficiently exercise the product**, but Gram Panchayat-scale mapping needs expanded NGEN tiling — limitation §8, not a missed assumption.

## Product

13. **4 NER roles + admin cover the PS alert chain** (villager / district officer / state manager / rescue + admin PIN 9999 observability). Language matrix `en/hi/ne/as/bn` seeded (`main.py:86` `DECISIONS_TRANSLATIONS`); full NER coverage needs community co-design (deferred). Yellow/Red kits (what/why/rain/shelters/phones) cover immediate field use.
14. **PWA + SMS-adapter + recorded-fixture demo satisfies "multilingual + offline"** at prototype depth; real gateway integration and field testing are post-hackathon work. PWA `sw.js:1` shell cached + `manifest.webmanifest:1` 192/512 + `talus_report_outbox` outbox proves offline; `/api` never served stale.
15. **GSI RLFS complementarity** — assumption that positioning as "the AI/ML decision layer GSI asked for" (not a replacement) is the credible and cooperative stance. Observed vs forecast separation preserves RLFS threshold language.

## Process

16. **Pilot-first, then scale.** One cluster fully working beats eight states thinly mapped; 3 corridors (Gangtok/Lachung/Darjeeling) now prove multi-location before NER-wide tiling. Expansion is a roadmap item, not MVP.
17. **Cloud PostGIS is post-demo, not pre-demo.** Assumption that `docker-compose.prod.yml` (postgis:16-3.4, `https://talus-sih26001.onrender.com/health` via docs/LIVE_HOST_EVIDENCE.md) `postgis/postgis:16-3.4` path + `AUTO_ALERT_*` + `IMD_API_KEY` gated live feed together prove production readiness without claiming live flood-scale today.

---

**2025-11-15 deltas (WILL→PARTIAL, frozen 12 untouched):**

- Panchayat tiling 100 tiles (10x10, 26.95-28.05N/88.05-89.0E) `data/sih26001/evidence/panchayat_tiles.json` heuristic/live-RF, `GET /api/panchayat/tiles` (frozen 12 S/N/D untouched)
- Copernicus COP30 vs SRTM `copernicus_dem_comparison.json` S1 28.3→28.7 Δ0.4° `GET /api/terrain/copernicus`
- Dense AWS 10-min 12 gauges (4/corridor) `backend/app/aws_ingest.py` MQTT QA `GET /api/aws/gauges`
- PostGIS prod `docker-compose.prod.yml` postgis:16-3.4 + `GET /api/db/status` (fixture/postgis) + `docs/LIVE_HOST_EVIDENCE.md` `https://talus-sih26001.onrender.com/health`
- CBE bearer `docs/CBE_CONTRACT.md` `POST /api/alerts/cbe` → `runs/cbe_dispatch.jsonl` simulated until DoT
