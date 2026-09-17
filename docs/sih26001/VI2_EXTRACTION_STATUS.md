# VI-2 Extraction Status: INFRASTRUCTURE-BLOCKED (2026-09-18, no scores, no claims)

## Validated before the block

- URL scheme correct: one `geo.cc.tif` opened successfully via GDAL range reads
  (2711×2900, EPSG:4326, 1 band) before throttling began.
- Pair census complete: per-frame pair lists + per-event pre-T counts in
  `runs/phase_v/vi2_feasibility.json` (listings need no bulk transfer).
- Filenames: `<pair>.geo.unw.tif` (unwrapped, radians → mm LOS via λ/4π),
  `<pair>.geo.cc.tif` (coherence 0–1), `<pair>.geo.diff_pha.tif` (wrapped filtered).
- GWS index pages are throttled together with file reads; STAC/IMD/CCI unaffected.

## The block (updated: COMET migration in flight, NOT IP/auth/throttle)

Fresh-IP retest + `.future`-repo investigation: the new repo
(`gws-access/.../LiCSAR_products.future/`) EXISTS with frame/pair-dir indexes,
but pair file reads 404 on both old (`data.ceda.ac.uk/.../LiCSAR_products/...`)
and new paths; small metadata files + all listings still serve (200, anonymous,
no 401s anywhere). Diagnosis: index migrated, file payloads not yet transferred
— mid-migration breakage on COMET's side. LiCSBAS01_get_geotiff.py would resolve
to the same file backends and fail identically; cloning it changes nothing until
the payloads land. Feasibility PASS stands (pair census + one completed GeoTIFF
open pre-date the breakage). Resume probe: single pair-PNG GET on EITHER path;
on 200, run the paced runbook. If durable, check COMET portal news.

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

## Third-party confirmation + correction (2026-09-18)

Independent web fetch of the exact dap enclosure URL: **404**. Three clients
across two local networks plus one external: same result. Verdict: current DAP payload
unavailability / migration-service inconsistency (no claim about which internal
component; the 404 proves non-service, not mechanism).
Correction: the 4,092,260-byte 200 was MEASURED ONLY (Content-Length match to
metadata, ~00:25 IST) — bytes were not persisted, so no file/hash exists. The
observation stands as a logged measurement, not an artifact. Lesson recorded:
persist first successful payload reads immediately.

## Breakthrough + new finding (`.public` XML → dap enclosure)

The `.public` pair dirs carry `.tif.xml` EPOS records whose enclosure URL is
`https://dap.ceda.ac.uk/...` (NOT `data.ceda.ac.uk` — index vs download hosts,
per CEDA's own docs), with bonus metadata: baselines, 0.001° resolution,
footprint polygon, CC-BY-4.0. A full 4,092,260-byte TIFF + PNG served 200 via dap.
Minutes later ALL dap pair reads 404 (touched and untouched URLs, both UAs) —
upstream flapping, not client state. Verdict: correct host found, backend unstable
tonight. STOP probing; resume = single PNG GET on dap enclosure URL, then runbook.

## CDSE escape hatch assessed (2026-09-18)

- GRD-change via CDSE/GEE: REJECTED as experiment — M1-A closed the amplitude-change
  observable (sat-only AUC 0.500); a different host tests nothing new.
- SLC self-processing: RAW MATERIAL CONFIRMED (CDSE holds both Mantam pair SLCs,
  3.6–8 GB each) but requires user CDSE registration + ISCE/GAMMA chain + validation
  ≈ weeks. Parked unless LiCSAR stays down long-term AND scope is explicitly approved.
- Primary remains LiCSAR resume probe (4 MB products vs 8 GB raws).

## First payload landed via browser (2026-09-18)

`20160730_20160811.geo.cc.tif` (4,092,260 B, sha f5cb39296adbb667, local-only per
raw-archive convention): 2711×2900 EPSG:4326 uint8 0–255 coherence scale.
Mantam 11×11 window median 9/255 (≈0.035) vs frame mean ≈0.29 — severe local
decorrelation in the 12 d before collapse (monsoon/vegetation/surface-change
nulls apply; unw phase needed for the deformation half).
Needed next: same pair `.geo.unw.tif` + mid pair `20160718_20160730` unw+cc.
PILOT VALIDATED (browser-supplied pair 20160730_20160811): unw float32 radians
(Mantam n=3/121 valid, med 0.608 rad ≈ +5.4 mm LOS, range −1.25..+1.0; sign =
toward-sensor per LiCSAR convention, recorded assumption); cc uint8 0–255.
Key finding: unw coverage 2.5% where coherence lost — deformation observable
degrades to coherence-loss itself on monsoon slopes (anticipated null stands).
File hashes: cc f5cb39296adbb667 (4092260 B), unw 70176ed5d8147169 (14670110 B).
Lesson: re-verify size+hash AFTER move (caught a partial-file read). Batch GO.

## Scope guard

Extraction extracts. No scores, no fusion, no threshold talk until the audit
passes. VI-2 justification and gates unchanged.
