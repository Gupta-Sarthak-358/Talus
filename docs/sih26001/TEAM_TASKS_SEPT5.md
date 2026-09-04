# Sept-5 Team Tasks (handout — pick one lane, stay in it)

**Source of truth:** `docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md` + fixtures in
`data/sih26001/fixtures/`. Demo is Sept 5. Nothing outside the contract ships.

## Lane A — Frontend (1 person) → `feature/sih26001/frontend-sept5`

* Branch off `feature/sih26001/demo-scaffold`.
* Header/footer: Mine Safety → NER Landslide, SIH26001 / MDoNER.
* Map centre → 27.3389, 88.6065. Zones → S1–S4 names from `slopes.json`.
* Decision panel renders 4 roles: villager / district_officer / state_manager / rescue_team (no logic change, strings come from API).
* Add 3 static panels wired to contract paths: road-status list (`GET /api/roads/status`), alert preview (`POST /api/alerts/dispatch` fixture), report form (`POST /api/reports` → appears in queue).
* Provenance footnote on Screen 1: IMD + SRTM + Bhusanket + ERA5 + Sentinel-2 + OSM + sensor-fixture.
* Done = `start_demo.ps1` shows S1-S4 coloured + all 6 clicks work against fixtures.

## Lane B — Backend + merge (1–2 persons) → `feature/sih26001/backend-sept5`

* Branch off `feature/sih26001/demo-scaffold`. One person is **merger** (only merger merges to `SIH26001`).
* `backend/app/main.py`: rename `DECISIONS_BY_BAND` roles to the 4 NER roles; rename zones A–D → S1–S4; load scores/bands/confidence from `slopes.json` (keep v1 API shapes).
* Add 4 fixture endpoints exactly as §2: `GET /api/roads/status`, `POST+GET /api/reports*`, `POST /api/alerts/dispatch`, `GET /api/forecast/rainfall`. In-memory only, `fixture:true` flag, no live SMS/network.
* `GET /api/simulation/templates` returns `monga-mdl` + `dahal-144` from `forecast.json`.
* Done = validator green + `start_demo.ps1` boots + `GET /api/zones` returns S1-S4 with 89/78/66/52.

## Lane C — Data → features (rest) → `feature/sih26001/ngen-pilot`

* Branch off `feature/sih26001/demo-scaffold`. Pilot extent ONLY (Gangtok cluster). No 8-state talk.
* Split: (1) rain+moisture → `rainfall_24h/7d/30d_mm`, `soil_moisture`; (2) SRTM→slope/elev/aspect/curv/TWI/SPI + OSM→`distance_to_road/river` + Sentinel-2 NDVI/LULC stub (constant allowed if tagged); (3) Bhusanket filter + negatives (>300 m) → `event` + `manifest.json`.
* Output format MUST match `feature_matrix.sample.csv` + `manifest.sample.json` (17 features, column order frozen). Full matrix stays git-ignored; commit ≤20-row sample only.
* Target for Sept 5: 1 real slope row with all 17 filled + manifest. Full train is bonus — if RF trains, swap at most ONE fixture score; else present matrix+manifest as "training-ready, spatial-CV next".
* Done = sample CSV loads, every value has provenance, validator green.

## Daily checkpoint (5 min)

* Scaffold merged? Frontend on fixtures? Backend serving S1-S4? Data team: how many of 17 filled for S1?
* Anything outside contract → cut, do not chase. Demo runs on fixtures even if backend or training slips.
