"""Phase 1C groundwater sampler (per zone).

Physical chain from the research freeze (neyveli_geology.md §3.4, cracks §1.4):
    rainfall accumulation -> wetting memory (lag/persistence) -> pore pressure
Groundwater does NOT redraw randomly every day. A zone-static engineering
component (aquifer thrust) is sampled once per zone; the transient response is
an exponential wetting memory of the mine-wide rainfall series, giving lag and
persistence instead of same-day reaction.

Zoning (grounded): ZONE_D sits on the confined aquifer below lignite
(thrust 490-785 kPa -> floor heave); OB benches A/B receive semi-confined
seepage; ZONE_C (mineral bench near seam) is intermediate.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from generator_schema import ZONES

# Zone-static aquifer thrust ranges (kPa) -- engineering input, sampled once.
THRUST_RANGES_KPA = {
    "ZONE_A": (20.0, 60.0),  # semi-confined seepage into upper OB benches
    "ZONE_B": (40.0, 120.0),  # stronger seepage lower in OB
    "ZONE_C": (100.0, 300.0),  # near-seam, semi/confined boundary
    "ZONE_D": (490.0, 785.0),  # confined below lignite -> floor heave driving
}

# Pore-pressure transient gain: kPa per mm of wetting memory.
RESPONSE_KPA_PER_MM = 1.0
# Wetting-memory decay time constant (days). Lag/persistence of groundwater.
WETNESS_TAU_DAYS = 12.0

# groundwater_state bands (kPa), absolute.
STATE_BANDS_KPA = [
    ("dry", 0.0, 60.0),
    ("normal", 60.0, 150.0),
    ("elevated", 150.0, 300.0),
    ("high", 300.0, 500.0),
    ("critical", 500.0, np.inf),
]

GW_STREAM = 4000
_ZONE_INDEX = {z: i for i, z in enumerate(ZONES)}


def _state_from_kpa(pp):
    for name, lo, hi in STATE_BANDS_KPA:
        if lo <= pp < hi:
            return name
    return "critical"


def _wetting_memory(rainfall_mm, alpha):
    w = np.zeros(len(rainfall_mm))
    cur = 0.0
    for t, r in enumerate(rainfall_mm):
        cur = alpha * cur + r
        w[t] = cur
    return w


def generate_groundwater(rainfall_mm, zone_id, seed):
    """Return per-zone state DataFrame for the timeline (deterministic).

    Columns: groundwater_state (category), pore_pressure_kpa,
    groundwater_thrust_kpa, groundwater_proxy. rainfall_mm is the mine-wide
    daily series for the matching timeline.
    """
    rng = np.random.default_rng(np.random.SeedSequence([seed, GW_STREAM, _ZONE_INDEX[zone_id]]))

    thrust_lo, thrust_hi = THRUST_RANGES_KPA[zone_id]
    thrust_kpa = float(rng.uniform(thrust_lo, thrust_hi))

    alpha = float(np.exp(-1.0 / WETNESS_TAU_DAYS))
    wetness = _wetting_memory(rainfall_mm, alpha)
    transient = RESPONSE_KPA_PER_MM * wetness
    pore_pressure = thrust_kpa + transient

    states = [_state_from_kpa(v) for v in pore_pressure]
    return pd.DataFrame(
        {
            "groundwater_state": pd.Categorical(states, categories=[s[0] for s in STATE_BANDS_KPA], ordered=True),
            "pore_pressure_kpa": pore_pressure,
            "groundwater_thrust_kpa": thrust_kpa,
            "groundwater_proxy": wetness,
        }
    )