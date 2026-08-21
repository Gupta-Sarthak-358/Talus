# TALUS Scenario Engine v1.5 — Specification (Phase 10 contract)

Status: extension layer over FROZEN generator v1.4.0. No base physics is
modified; scenarios inject modified CAUSES (weather realization, blast
schedule) into the existing frozen chain:

    scenario causes
        -> RAIN (modified realization)
        -> GROUNDWATER   (frozen sampler, fed modified rain)
        -> CRACKS        (frozen sampler, fed modified rain/gw/blast)
        -> BLAST         (frozen schedule + surge overlay)
        -> FoS           (frozen instability sampler)
        -> instability_score / risk_label

FORBIDDEN: any write to fos / instability_score / risk_label outside the
frozen `generate_instability`. Scenarios never touch scores directly.

## Scenario contract

    Scenario(
        name           unique id
        kind           none | rainfall_storm | prolonged_rain |
                       blast_surge | combined | historical_rain
        zone_id        ZONE_A..ZONE_D
        seed           base generator seed (world draw)
        start_day      first modified day (0-indexed)
        duration_days  length of injection window
        params         kind-specific:
                         rainfall_storm:  peak_mm (triangular profile)
                         prolonged_rain:  daily_mm (flat)
                         historical_rain: template_id, scale
                         blast_surge:     ppv_mult, extra_event_prob
                         combined:        union of the above
        scenario_seed  deterministic stream for stochastic overlays
    )

Determinism: same (scenario, seed) => byte-identical trajectory.
RNG streams derive from SeedSequence([seed, 9000, crc32(name)]).

## Historical templates (provenance: IMD Neyveli grid 11.5N 79.5E)

Replayed as additive daily overlays from `neyveli_rainfall_1901_2024.csv`:

    dec_1902   1088 mm/month, max day 298 mm
    apr_1931    430 mm/month, max day 333 mm
    nov_2015    974 mm/month, max day 327 mm
    dec_1996    805 mm/month, max day 156 mm

## Outputs

Day-by-day trajectory frame (per zone): timestamp, rainfall state,
groundwater state, crack state, blast state, fos, instability_score,
risk_label, plus `scenario` tag. Consumers receive TRAJECTORIES, not
single numbers.

## Validation gates (Phase 18)

1. baseline replay == frozen generator output (exact equality)
2. pre-start rows identical to baseline (injection touches only its window)
3. dose-response: stronger storm => non-increasing min FoS
4. determinism under re-run
5. no direct score writes in engine source
6. crack damage accumulates from the same initial state (no resets)
