"""Phase 1B terrain sampler (static per zone).

Two provenance layers, per observations.md Entries 7 & 10:
- DEM-derived regional context: elevation_m, regional_slope_deg.
- Mine-engineering bench layer (NOT the DEM): slope_angle_deg, slope_height_m.

All values are drawn once per zone and held constant over time -- terrain does
not respawn every morning. Using the ZONES engineering geometry (25/18/6 m
benches at 45-75 deg faces) keeps the regional-terrain != bench-geometry rule.
"""
from pathlib import Path

import numpy as np

from generator_schema import ZONES

# DEM mine-focus anchors (terrain_summary.json): ground +15..+27 m MSL,
# overburden 45-112 m, seam intercalations near pit floor, pit floor to -97 m.
# Bench-to-elevation mapping uses bench location in the excavated sequence.
ELEVATION_RANGES_M = {
    "ZONE_A": (10.0, 27.0),  # upper OB bench: near original ground level
    "ZONE_B": (0.0, 15.0),  # middle OB bench: one bench lower
    "ZONE_C": (-85.0, -30.0),  # mineral/lignite bench: seam level under OB
    "ZONE_D": (-97.0, -40.0),  # pit floor: deepest excavated surface
}

# Regional flat coastal plain context, not bench faces.
REGIONAL_SLOPE_RANGE_DEG = (0.3, 6.0)

TERRAIN_STREAM = 2000
_ZONE_INDEX = {z: i for i, z in enumerate(ZONES)}


def generate_terrain(zone_id, seed):
    """Return static per-zone terrain values (deterministic in seed).

    slope_angle_deg / slope_height_m come from the mine-engineering layer
    (bench faces), elevation and regional slope from DEM-derived ranges.
    """
    cfg = ZONES[zone_id]
    rng = np.random.default_rng(np.random.SeedSequence([seed, TERRAIN_STREAM, _ZONE_INDEX[zone_id]]))

    elevation_m = float(rng.uniform(*ELEVATION_RANGES_M[zone_id]))
    regional_slope_deg = float(rng.uniform(*REGIONAL_SLOPE_RANGE_DEG))

    lo, hi = cfg["face_angle_range_deg"]
    slope_angle_deg = float(rng.uniform(lo, hi)) if hi > lo else float(lo)

    h_lo, h_hi = cfg["bench_height_range_m"]
    slope_height_m = float(rng.uniform(h_lo, h_hi)) if h_hi > h_lo else float(h_lo)

    return {
        "elevation_m": elevation_m,
        "regional_slope_deg": regional_slope_deg,
        "slope_angle_deg": slope_angle_deg,
        "slope_height_m": slope_height_m,
    }