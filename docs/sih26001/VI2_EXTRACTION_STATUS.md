# VI-2 Extraction Status: INFRASTRUCTURE-BLOCKED (2026-09-18, no scores, no claims)

## Validated before the block

- URL scheme correct: one `geo.cc.tif` opened successfully via GDAL range reads
  (2711×2900, EPSG:4326, 1 band) before throttling began.
- Pair census complete: per-frame pair lists + per-event pre-T counts in
  `runs/phase_v/vi2_feasibility.json` (listings need no bulk transfer).
- Filenames: `<pair>.geo.unw.tif` (unwrapped, radians → mm LOS via λ/4π),
  `<pair>.geo.cc.tif` (coherence 0–1), `<pair>.geo.diff_pha.tif` (wrapped filtered).
- GWS index pages are throttled together with file reads; STAC/IMD/CCI unaffected.

## The block

Anonymous access from this host to `data.ceda.ac.uk` LiCSAR files escalated
during probing: GDAL range reads → 404s, then all TIFF GETs → 404, then PNGs →
404, UA-independent, persisting >5 min. Diagnosis: IP-level anonymous throttle
after a day of heavy archive use. NOT a data-availability finding (feasibility
PASS stands) and NOT worked around (no parallel clients, no UA spoofing —
service etiquette is part of the method).

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
