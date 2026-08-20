"""Phase 1B geology sampler (static per zone).

Loads the grounded, normalized Neyveli geotechnical table
(data/processed/geotech/neyveli_geotech_parameters.csv) and assigns one
Cuddalore Group material class per zone, drawn once from a grounded candidate
set, with c/phi/gamma sampled from the row's min-max ranges. parameter_regime is
taken verbatim from the row -- total_undrained and effective_stress never mix.

Lignite is deliberately NOT used yet: its grounding row has no cohesion/friction
and its parameter_regime label ("literature") is outside the frozen schema enum.
The mineral bench therefore samples the dominant seam-host sediment until a
grounded lignite geotech row exists (documented in the ledger).
"""
from pathlib import Path

import numpy as np
import pandas as pd

from generator_schema import BASE_DIR

GEOTECH_CSV = BASE_DIR / "data" / "processed" / "geotech" / "neyveli_geotech_parameters.csv"

# Grounded candidate materials per zone (lithological section, observations.md §11).
ZONE_MATERIALS = {
    "ZONE_A": ["lateritic_soil", "clayey_sandstone"],  # top OB cap / dominant OB
    "ZONE_B": ["clayey_sandstone", "variegated_sandy_clay"],  # dominant / major weak OB
    "ZONE_C": ["clayey_sandstone"],  # seam-host sediment (lignite row incomplete)
    "ZONE_D": ["sandstone", "variegated_sandy_clay"],  # deep floor / near-aquifer units
}

GEOLOGY_STREAM = 3000
_ZONE_INDEX = {z: i for i, z in enumerate(ZONE_MATERIALS)}
G = 9.81  # m/s2


def _sample_range(rng, lo, hi, default=None):
    if pd.isna(lo) or pd.isna(hi):
        return default
    lo, hi = float(lo), float(hi)
    if hi <= lo:
        return lo
    return float(rng.uniform(lo, hi))


def generate_geology(zone_id, seed):
    """Return static per-zone geology (deterministic in seed).

    material_class, cohesion_kpa, friction_angle_deg, unit_weight_kn_m3,
    parameter_regime -- all drawn once per zone from the grounded table.
    """
    rows = pd.read_csv(GEOTECH_CSV)
    rng = np.random.default_rng(np.random.SeedSequence([seed, GEOLOGY_STREAM, _ZONE_INDEX[zone_id]]))

    material = str(rng.choice(ZONE_MATERIALS[zone_id]))
    row = rows[rows["material"] == material].iloc[0]

    cohesion_kpa = _sample_range(rng, row["cohesion_kPa_min"], row["cohesion_kPa_max"], default=0.0)
    friction_angle_deg = _sample_range(rng, row["friction_phi_deg_min"], row["friction_phi_deg_max"], default=0.0)

    density_min = float(row["density_kg_m3_min"])
    density_max = float(row["density_kg_m3_max"])
    density = float(rng.uniform(density_min, density_max)) if density_max > density_min else density_min
    unit_weight_kn_m3 = round(density * G / 1000.0, 3)

    return {
        "material_class": material,
        "cohesion_kpa": round(cohesion_kpa, 2),
        "friction_angle_deg": round(friction_angle_deg, 2),
        "unit_weight_kn_m3": unit_weight_kn_m3,
        "parameter_regime": str(row["parameter_regime"]),
    }