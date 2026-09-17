# VI-2 Extraction Status: INFRASTRUCTURE-BLOCKED (2026-09-18, no scores, no claims)

## Validated before the block

- URL scheme correct: one `geo.cc.tif` opened successfully via GDAL range reads
  (2711×2900, EPSG:4326, 1 band) before throttling began.
- Pair census complete: per-frame pair lists + per-event pre-T counts in
  `runs/phase_v/vi2_feasibility.json` (listings need no bulk transfer).
- Filenames: `<pair>.geo.unw.tif` (unwrapped, radians → mm LOS via λ/4π),
  `<pair>.geo.cc.tif` (coherence 0–1), `<pair>.geo.diff_pha.tif` (wrapped filtered).
- GWS index pages are throttled together with file reads; STAC/IMD/CCI unaffected.

## The block (updated: NOT IP throttle, NOT login)

Fresh-IP retest: identical 404s. Discriminating probes show CEDA root (200),
listings (200), and small metadata files (200) all serve anonymously — while
every file under `interferograms/` 404s (PNG+TIFF, old+`.future` paths).
No 401s anywhere. Diagnosis revised: the interferogram file subtree itself is
unavailable (backend migration/outage; portal warned of `LiCSAR_products` →
`.future` moves), not client throttling and not an auth wall. Feasibility PASS
stands (availability proven from listings + one completed GeoTIFF open).
Resume probe: single PNG GET; on 200, run the paced runbook. If durable, check
COMET portal news / CEDA status before any further action.

## Resume runbook (single client, off-peak)

1. Wait for throttle reset; verify with one PNG GET.
2. Per event (dev first, then held-out, then background): ≤4 pairs
   (recent + mid + baseline, secondary ≤ T−1, short baselines preferred),
   unw + cc only, sequential with ≥10 s pacing + exponential backoff.
3. Window stats (1 km box, robust medians/spreads/valid-fraction) via
   `scripts/lics_pilot.py` pattern; assert CRS/units/nodata/date-gate per read.
4. Mantam pilot validates units + sign convention BEFORE batch; batch writes
   `runs/phase_v/vi2/sar_features.json` + audit; model fitting stays closed
   until the extraction audit passes.

## Scope guard

Extraction extracts. No scores, no fusion, no threshold talk until the audit
passes. VI-2 justification and gates unchanged.
