# TALUS Championship Rule v1 (FROZEN 2026-09-18)

No event admitted after this date may move the boundary. Attractive candidates
(Soureni/Dilaram Oct-2025 and any future finds) go to transfer/post-championship.

## Eligibility (all must hold)

1. EXACT calendar incident date (day-level), independently corroborated.
2. Identifiable point/area location resolvable to ~1km or better.
3. INSIDE the frozen NGEN box: lon 88.06-88.96, lat 27.00-28.00.
4. DEM coverage (SRTM N27 tiles on disk) + IMD yearly rainfall file on disk.
5. Mechanism in {natural slope failure, rainfall-triggered slide, road-cut slope
   failure, landslide-induced road blockage, mass-exposure slope failure}.
6. Not the same physical failure as an existing row (episode discipline:
   same episode != same sample; distinct points/times stay distinct;
   aggregates and re-reports are guards, not samples).
7. No post-event information in the future feature window (checked at replay build).

## Exclusions (even when rainfall-associated)

- Tunnel-face / underground excavation collapse (Bhalu Khola precedent).
- Quarry / excavation-site collapse (Melthum precedent).
- Vehicle accidents on rain-hit roads (Lingzya precedent).
- Structural collapses (guard-walls, buildings) without slope failure.
- GLOF/flash-flood cascades whose trigger is outside the regime (Chungthang).
- Month/year aggregates with no exact date/point (Nagaland-2018, Jun-17-2022).

## Populations

- Championship: eligible rows only (target 30; quality over quota).
- Transfer: exact-date credible events outside support (never in calibration).
- Provisional: evidence incomplete (one step away).
- Rejected: evidence says no. Deferred: retrieval unavailable (429s etc.).
- Post-championship study: support-envelope expansion (Mirik-2025 etc.).

## Split law (for when the pool fills)

Development/held-out assignment is frozen BEFORE any held-out scoring.
Held-out events become untouchable: no calibration, threshold, OOD-rule, or
feature decision may use them afterwards. Same-episode rows (e.g. Dipudara
Aug-20/Aug-21, overlapping T-30 at one point) must fall on the SAME side of
the split — never one in dev and one in held-out.
