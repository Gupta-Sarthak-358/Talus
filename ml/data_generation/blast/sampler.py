"""Phase 1C blast sampler (per zone, time-resolved).

Latent event model per neyveli_blasting.md §5 (BLAST-05). The ML-facing
columns (blast_frequency_per_week, blast_vibration_ppv_mms) are emitted from
richer physics; **Interpretation A** for the weekly rate (documented pre-1D):

    mine-wide rate 14-28/wk (derived, §1.2, drawn once on a dedicated stream)
        -> allocated across the REPRESENTED blasting zones (A+B = 14-28/wk)
        -> blast_occurs per day
        -> charge per delay W ~ 100-600 kg (mode ~300)
        -> receiver distance D from synthetic layout (zone-static)
        -> dominant_frequency_hz from 5-27 Hz 3-bin model (P<8Hz ~ 0.45)
        -> ppv = 858.90 * (D/sqrt(W))^(-1.58)  + lognormal scatter (target r ~ 0.86)

Every generated event is a real blast affecting the modelled system; no
operational rate is hidden on unrepresented benches (the previous /5-bench
partition under-generated A+B to ~5.6-11.2/wk -- corrected).

Constants K/b/r and the structure distances are LOADED from
data/processed/blasting/neyveli_blast_constants.csv -- never re-fit. DGMS
Circular 7/1997 thresholds live in the same CSV as regulatory REFERENCE only
(builder's note: they are NOT used to label risk; risk labelling is deferred to
the crack/slope track).

Zoning: only OB benches are blasted (ZONE_A, ZONE_B). The lignite bench
(ZONE_C) and pit floor (ZONE_D) are not blasted (research §1.3), so their rate
is 0 and they never produce an event. Unblasted days expose PPV = 0 mm/s.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from generator_schema import BASE_DIR

BLAST_CONSTANTS_CSV = BASE_DIR / "data" / "processed" / "blasting" / "neyveli_blast_constants.csv"

# Synthetic receiver distances (m): zone centroid/edge -> nearest exposed structure.
ZONE_RECEIVER_DISTANCE_M = {
    "ZONE_A": 300.0,  # upper OB: village east ~300 m
    "ZONE_B": 150.0,  # middle OB: hutments 150 m from Mine II boundary
    "ZONE_C": 400.0,  # mineral bench: south village ~400 m (unblasted zone)
    "ZONE_D": 500.0,  # pit floor: site office/road ~500 m (unblasted zone)
}

# Only OB benches are represented as blast-capable in the synthetic layout:
# ZONE_A (upper OB) and ZONE_B (middle OB). The lignite bench (ZONE_C) and pit
# floor (ZONE_D) are never blasted (research §1.3).
BLAST_ZONES = ("ZONE_A", "ZONE_B")
# Weekly-rate prior (derived, §1.2): 14-28 MINE-WIDE blasts/week. The generator
# allocates this whole rate across the represented blasting zones (A+B sum to
# 14-28/wk) so every generated event is a real blast affecting the modelled
# system. No blasts are silently hidden on unrepresented benches.
WEEKLY_RATE_RANGE = (14.0, 28.0)
# Upper-OB bench keeps a majority share of the weekly schedule; the rest goes
# to the middle-OB bench. Shares sum to 1 by construction.
BENCH_SHARE_RANGE = (0.40, 0.60)
MCD_RANGE_KG = (100.0, 600.0)
MCD_MODE_KG = 300.0
# Frequency model (BLAST-03): cumulative-bin split <8: 45% | 8-25: 50% | >25: 5%.
FREQ_BINS = ((0.45, 5.0, 8.0), (0.95, 8.0, 25.0), (1.0, 25.0, 27.0))
# Lognormal scatter multiplier sigma (log space); calibrates the observed PPV
# scatter toward the NIRM Table 2.1 regression r ~ 0.86.
SCATTER_SIGMA = 0.40
PPV_CEILING_MMS = 100.0

BLAST_STREAM = 5000
BLAST_MINE_STREAM = 5001
_ZONE_INDEX = {z: i for i, z in enumerate(ZONE_RECEIVER_DISTANCE_M)}


def _constants():
    rows = pd.read_csv(BLAST_CONSTANTS_CSV)
    get = lambda k: float(rows[rows["key"] == k]["value"].iloc[0])
    return get("K"), get("b")


def generate_blast(timeline, zone_id, seed):
    """Return per-zone blast state DataFrame (deterministic in seed).

    Interpretation A (documented): the 14-28/wk derived rate is MINE-WIDE. It
    is drawn once (dedicated stream) and allocated across the represented
    blasting zones so ZONE_A + ZONE_B = 14-28/wk -- every generated event is a
    real blast affecting the modelled system, none are hidden on unrepresented
    benches. Only A/B blast; C/D are never blasted (rate 0).

    Columns match the schema: blast_occurs (bool), blast_frequency_per_week,
    charge_per_delay_kg, blast_distance_m, dominant_frequency_hz,
    blast_vibration_ppv_mms. Non-blast days carry 0.0 (no event) so the module
    emits no NaNs for ML projection.
    """
    n = len(timeline)
    K, b = _constants()
    mine_rng = np.random.default_rng(np.random.SeedSequence([seed, BLAST_MINE_STREAM]))
    rng = np.random.default_rng(np.random.SeedSequence([seed, BLAST_STREAM, _ZONE_INDEX[zone_id]]))

    active = zone_id in BLAST_ZONES
    if active:
        mine_rate = float(mine_rng.uniform(*WEEKLY_RATE_RANGE))
        share_a = float(mine_rng.uniform(*BENCH_SHARE_RANGE))
        share = share_a if zone_id == "ZONE_A" else 1.0 - share_a
        weekly_rate = mine_rate * share
    else:
        weekly_rate = 0.0
    p_day = min(1.0, weekly_rate / 7.0)

    dist_m = ZONE_RECEIVER_DISTANCE_M[zone_id]

    charge = np.zeros(n)
    freq = np.zeros(n)
    ppv = np.zeros(n)
    occurs = np.zeros(n, dtype=bool)

    for t in range(n):
        if rng.random() >= p_day:
            continue
        occurs[t] = True
        w = float(rng.triangular(MCD_RANGE_KG[0], MCD_MODE_KG, MCD_RANGE_KG[1]))
        charge[t] = w
        r = float(rng.random())
        for prob, lo, hi in FREQ_BINS:
            if r < prob:
                freq[t] = float(rng.uniform(lo, hi))
                break
        sd = dist_m / np.sqrt(w)
        raw = K * sd ** (-b)
        scatter = float(rng.lognormal(0.0, SCATTER_SIGMA))
        ppv[t] = min(raw * scatter, PPV_CEILING_MMS)

    return pd.DataFrame(
        {
            "blast_occurs": occurs,
            "blast_frequency_per_week": np.full(n, weekly_rate),
            "charge_per_delay_kg": charge,
            "blast_distance_m": np.full(n, dist_m),
            "dominant_frequency_hz": freq,
            "blast_vibration_ppv_mms": ppv,
        }
    )