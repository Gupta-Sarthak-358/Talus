# TALUS Limitations — SIH26001

**Status:** Built — freeze 2026-09-04 · **Branch:** `SIH26001 @ 68c0c28` · **Source:** `docs/SIH26001_RESEARCH.md` §11.3–§11.4

## What we do NOT claim

- We are **not** replacing GSI RLFS — we complement it with AI/ML.
- We are **not** doing real-time InSAR (requires hardware).
- We are **not** deploying IoT sensors (A-LEWS/AmritaWNA's domain).
- We do **not** predict exact landslide locations/times — we predict
 susceptibility.
- We do **not** predict flash floods — rainfall is a landslide-trigger proxy,
 not a hydrological flood model. Road blockages are covered as derived
 road-status, not flood mapping.
- We do **not** claim field-validated production accuracy — this is a prototype.

## Honest limitations (say before asked)

1. **Satellite/CCI soil moisture 0.271, not in-situ sensors** — resolution `0.25°` same-cell all slopes `gangtok_soil_cci.meta.json:3`, limits at slope scale (cf. Marino et al. 2020) — `CCI` stronger than `ERA5` but still quasi-static.
2. **Inventory incompleteness** — `672/764` pos `year 0` undated `training_sidecar.csv:1`; `92→108 dated` after rescue `16` clusters `build_training_matrix.py:294`; small slides unreported — candidate sidecar `reports.json:1` is the mitigation.
3. **Static model** — conditioning factors don't change; only rainfall + soil + NDVI (quasi-static `S2B_45RXL_20241129` `s234_ndvi.json:1`) are dynamic. `lithology/lineament` uniform `0.8` `lingtse_granite_gneiss` omitted from `X` `manifest.training.json:263`.
4. **No live sensor integration** in the prototype — adapter fixture only.
5. **Multilingual NER coverage needs community co-design** beyond the pilot
 language matrix.
6. **Offline sync needs field testing** — demonstrated as architecture, not
 proven in deployment.
7. **IMD grid coarseness** (~27 km) misses hyperlocal cloudbursts — same-cell `27.25/88.50` all Sikkim `manifest.training.json:30` rain `1991-2020` climatology proxy `rainfall_30d 390-484` `metrics.md:39`.
8. **OSM rural gaps** — `6698 roads/1320 rivers` bulk `out center` `manifest.training.json:30` `center-approx` vs pilot `48/12` `s1_osm_nearest.json:1` geometry, `osm-qa-unverified` kept.
9. **Prototype bands ≠ safety standards.** Operational decisions remain with
 qualified authorities — `calibrated Brier 0.1019` same-OOF optimism `calibration.md:3`, clean check is temporal `AUC 0.9264`.

## Field reporting — demo honesty (new in this build)

* Citizen/field reports are **unverified input** — `verified` status requires an officer `PATCH` review (demo role-toggle only; real auth + moderation are post-hackathon). Until verified, a report never promotes to a training `event` or a `previous_landslide` label — it lives in a candidate sidecar with `crowd-verified` + photo SHA256.
* Photo/video **bytes are never committed** (metadata-only lane per contract §4 + `.gitignore:46`); only `{filename,mime,size_bytes,sha256,exif_lat,exif_lon}` is stored, with an explicit `consent: true` gate. EXIF vs claimed >200m is flagged; unsupported mime is flagged; per-boot rate cap 20 is a demo guard, not production moderation.
* Offline outbox is `localStorage` + retry + sync badge (no service worker — `6` below). Full PWA + background sync + content moderation are post-hackathon.

## Carryover discipline from v1

- Confidence is calibrated P(elevated susceptibility), never "probability of
 failure."
- ML counterfactuals labeled counterfactual; causal claims via scenario
 engine only.
- Every score ships with missing evidence. A confident-looking number with
 hidden gaps is a bug, not a feature.
