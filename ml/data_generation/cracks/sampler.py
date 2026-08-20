"""Phase 1D crack sampler (per zone, time-resolved damage state).

Converts the 1A-1C environment into a temporal DAMAGE STATE (defines 1D,
documented pre-implementation): cracks are NOT independent daily samples.
They carry memory -- state_t = state_{t-1} + growth_t -- and grow through
mechanism-specific contributions drawn from the CRACK track, never a random
weighted sum.

Mechanisms (neyveli_cracks.md CRACK-01/03/05):
  TENSION/crest  - steep benches, stress relief + rain-driven hydraulic
                   weakening (USACE crack-fills-with-water). A/B/C.
  BLAST-induced  - PPV step growth on existing cracks; NO fresh nucleation at
                   distance; only blasted zones (A/B) can ever receive it.
  DESICCATION    - shrink-swell of fine-grained clay surfaces, anti-correlated
                   with recent rainfall (opens on drying). Small in sandy
                   benches; scales with material clay content.
  SEEPAGE        - semi-confined aquifer contact; B (stronger seepage) only.
  FLOOR HEAVE    - ZONE_D ONLY: confined-aquifer thrust 490-785 kPa (geology
                   §3.4) drives heave cracks on the pit floor.

Zone mapping (CRACK-03 spatial anchoring):
  ZONE_A upper OB: tension base, blast-capable, weak seepage.
  ZONE_B middle OB: tension base, blast-capable, STRONG seepage.
  ZONE_C mineral seam: tension (steep 75), NO blast, intermediate GW.
  ZONE_D pit floor: FLOOR HEAVE only (no blast, no crest tension).

Physical invariants enforced (CRACK-02):
  - crack_depth <= 1/3-1/2 of the bench/slope height (sampled once per zone).
  - growth never negative (damage accumulates; no healing below zero).
  - depth/width/severity are monotone non-decreasing with damage.
  - classifier lives in 1E, NOT here: this module emits crack state only.
"""
import numpy as np
import pandas as pd

from generator_schema import ZONES
from cracks.material import susceptibility, MATERIAL_WEAKNESS, CLAY_LIKE

# Sampling latents per zone (drawn once, then evolve deterministically).
CRACK_STREAM = 6000
_ZONE_INDEX = {z: i for i, z in enumerate(ZONES)}

# Depth cap fraction bounds: 1/3..1/2 of the bench height (CRACK-02).
DEPTH_CAP_FRAC_MIN = 1.0 / 3.0
DEPTH_CAP_FRAC_MAX = 1.0 / 2.0

# Tension/hydraulic activity per mm of equivalent material-driven loading.
TENSION_RATE = 0.18       # mm/day slow creep (seasonal, scales with steepness)
HYDRAULIC_GAIN = 0.6      # how strongly groundwater extra loads growth
BLAST_RATE = 0.8          # mm/day per (PPV / 12.5 mm/s) unit above damage threshold
DESICCATION_RATE = 0.15   # mm/day max on fully dried clay surfaces
SEEPAGE_GAIN = 0.45       # mm/day extra at ZONE_B under elevated GW
HEAVE_RATE = 0.5          # mm/day per (thrust/490 - 1) unit on the floor
# Depth progression: mm/day of opening -> m of crack deepening per active day.
DEPTH_DAILY_M_PER_MM = 0.012
# Width progression: mm/day of opening accumulates almost directly into width.
WIDTH_DAILY_MM_PER_MM = 0.85

# PPV above this (mm/s) initiates non-negligible blast step growth (legacy
# Neyveli safe level 12.5 mm/s); scaled relative, per BLAST track. Blasts below
# this threshold contribute only a negligible seismic tick, not crack growth.
BLAST_NORMALISATION_PPV = 12.5
BLAST_DAMAGE_PPV = 10.0

# Desiccation requires a fine-grained clay-like material and recent dry spell.
DRYDAYS_FOR_DESICCATION = 14
# Elevation of groundwater proxy (mm memory) considered "elevated wetting".
WETTING_THRESHOLD_MM = 60.0


def _clip(v, lo=0.0, hi=None):
    if hi is not None:
        v = min(v, hi)
    return max(v, lo)


def generate_cracks(timeline, rain, groundwater, blast, terrain, geology, zone_cfg, seed, zone_id=None):
    """Return per-zone crack state DataFrame (deterministic in seed).

    Inputs are the per-zone upstream states (rain = mine-wide rainfall rows,
    groundwater/blast = per-zone DataFrames, terrain/geology = per-zone dicts,
    zone_cfg = ZONES[zone_id]). Columns emitted follow the schema:
    crack_family, crack_width_mm, crack_depth_m, crack_length_m,
    crack_density, water_filled, crack_growth_rate_mm_day, crack_severity.
    """
    if zone_id is None:
        raise ValueError("cracks sampler requires zone_id argument")
    n = len(timeline)
    rng = np.random.default_rng(np.random.SeedSequence([seed, CRACK_STREAM, _ZONE_INDEX[zone_id]]))

    mat = geology["material_class"]
    weak = MATERIAL_WEAKNESS[mat]
    sus = susceptibility(weak)  # weakness up -> susceptibility up -> growth up (DIRECTION CONTRACT)
    clayness = CLAY_LIKE[mat]

    bench_h = float(zone_cfg["bench_height_m"]) if zone_cfg["bench_height_m"] > 0 else float(terrain["slope_height_m"])
    depth_cap_frac = float(rng.uniform(DEPTH_CAP_FRAC_MIN, DEPTH_CAP_FRAC_MAX))
    depth_cap_m = depth_cap_frac * max(bench_h, 0.5)

    # Flat floor: heave cracks bulge, they do not penetrate a tall bench; cap
    # depth well below the surface but still bounded.
    if zone_id == "ZONE_D":
        depth_cap_m = float(rng.uniform(0.6, 1.5))

    steep = _clip(terrain["slope_angle_deg"] / 75.0)

    length_m = float(rng.uniform(20.0, 200.0))
    # Weaker material -> more, denser crack mesh (sus from DIRECTION CONTRACT).
    density_base = float(rng.uniform(0.1, 0.4)) * (0.5 + sus)

    # Per-zone persistent activities (latent tendencies, drawn once).
    tension_activity = float(rng.uniform(0.6, 1.4))
    blast_activity = float(rng.uniform(0.6, 1.4)) if zone_id in ("ZONE_A", "ZONE_B") else 0.0

    demands = zone_id == "ZONE_D"
    floor_heave_active = zone_id == "ZONE_D"

    # Rolling counters.
    depths = np.zeros(n)
    widths = np.zeros(n)
    growths = np.zeros(n)
    density = np.full(n, np.nan)
    growth_trend = np.zeros(n)
    families = []
    water_filled = np.zeros(n, dtype=bool)
    term_tension = np.zeros(n)
    term_hydraulic = np.zeros(n)
    term_blast = np.zeros(n)
    term_seepage = np.zeros(n)
    term_desiccation = np.zeros(n)

    depth = 0.0
    width = 0.0
    grow = 0.0
    dry_days = 0
    trend_window = np.zeros(7)

    for t in range(n):
        r7 = float(rain["rainfall_7d_mm"].iloc[t])
        wet_today = bool(rain["wet_day"].iloc[t])
        gw = groundwater.iloc[t]
        bl = blast.iloc[t]

        wetting = float(gw["groundwater_proxy"])
        wetting_norm = _clip(wetting / WETTING_THRESHOLD_MM, 0.0, 3.0)
        wet_state = wetting > WETTING_THRESHOLD_MM

        dry_days = 0 if wet_today else dry_days + 1

        # ---------- mechanism terms (mm/day) ----------
        # Tension creep is SEASONAL: near-quiescent in the dry, elevated when
        # wetting reactivates the slope (expansion via seasonal rain cycles,
        # CRACK-05.1). It is NOT a constant background ratchet.
        wet_factor = 0.15 + 0.85 * _clip(wetting_norm / 1.5, 0.0, 1.0)
        # Material susceptibility amplifies tension creep (clay > sandstone).
        tension = tension_activity * TENSION_RATE * steep * sus * wet_factor
        hydraulic = HYDRAULIC_GAIN * wetting_norm * sus
        blast_term = 0.0
        if zone_id in ("ZONE_A", "ZONE_B") and bool(bl["blast_occurs"]):
            ppv = float(bl["blast_vibration_ppv_mms"])
            if ppv > BLAST_DAMAGE_PPV:
                blast_term = blast_activity * BLAST_RATE * _clip((ppv - BLAST_DAMAGE_PPV) / BLAST_NORMALISATION_PPV)
        seepage = 0.0
        if zone_id == "ZONE_B" and wet_state:
            seepage = SEEPAGE_GAIN * wetting_norm
        desiccation = 0.0
        if clayness > 0.5 and dry_days >= DRYDAYS_FOR_DESICCATION and not demands:
            desiccation = DESICCATION_RATE * clayness * _clip(dry_days / 30.0, 0.0, 1.0)
        heave = 0.0
        if floor_heave_active:
            thrust = float(gw["groundwater_thrust_kpa"])
            heave = HEAVE_RATE * max((thrust / 490.0 - 1.0), 0.0) * (0.5 + 0.5 * wetting_norm)

        grow = tension + hydraulic + blast_term + seepage + desiccation + heave
        term_tension[t] = tension
        term_hydraulic[t] = hydraulic
        term_blast[t] = blast_term
        term_seepage[t] = seepage
        term_desiccation[t] = desiccation

        # Damage accumulation (memory): opening accumulates width; deepening is
        # a fraction of the opening; both capped, never negative.
        width = min(width + grow * WIDTH_DAILY_MM_PER_MM, 150.0)
        if zone_id == "ZONE_D":
            width = min(width, 60.0)
        depth = min(depth + grow * DEPTH_DAILY_M_PER_MM, depth_cap_m)

        # water_filled: crack void holds water under rain or elevated GW.
        wf = bool(wet_today or r7 > 15.0 or wet_state or (zone_id == "ZONE_D" and wet_state))
        water_filled[t] = wf

        family = "none"
        if depth > 0.05 or width > 1.0:
            if zone_id == "ZONE_D":
                family = "floor_heave"
            else:
                # Dominant-driver family: the mechanism contributing most to
                # today's growth names the crack (blast must clear other terms).
                dominant = np.argmax([tension, hydraulic, blast_term, seepage, desiccation, 0.0])
                fams = ["tension_crest", "tension_crest", "blast_induced", "seepage", "desiccation", "tension_crest"]
                family = fams[dominant] if dominant != 5 else "tension_crest"
        families.append(family)

        depths[t] = depth
        widths[t] = width
        growths[t] = grow
        trend_window[t % 7] = grow
        growth_trend[t] = float(np.mean(trend_window))

        depth_ratio = depth / max(depth_cap_m, 1e-6)
        density[t] = density_base + 0.4 * _clip(depth_ratio * 2.0, 0.0, 1.0) + 0.2 * _clip(grow / 10.0, 0.0, 1.0)
        density[t] = _clip(density[t], 0.05, 2.5)

    # Severity ranking (CRACK-04 decision surface). It is CUMULATIVE STATE only
    # and must ratchet with the crack (never downgrade). Depth ratio is the
    # primary axis: penetration of the crack into the reserved bench layer
    # (cap = 1/3-1/2 bench height). Width/opening stays an independent ML
    # feature (crack_width_mm), and the >20 mm/day 6-12 day failure-window
    # trend signal (Leonardos & Terezopoulos 2002) remains in
    # crack_growth_rate_mm_day rather than being conflated into the label.
    severities = []
    for t in range(n):
        ratio = depths[t] / max(depth_cap_m, 1e-6)
        if ratio >= 0.49:
            sev = "critical"
        elif ratio >= 0.33:
            sev = "severe"
        elif ratio >= 0.20:
            sev = "moderate"
        elif ratio >= 0.10:
            sev = "minor"
        else:
            sev = "normal"
        severities.append(sev)

    cat = pd.Categorical
    return pd.DataFrame(
        {
            "crack_family": cat(families, categories=["none", "tension_crest", "desiccation", "blast_induced", "seepage", "floor_heave"], ordered=False),
            "crack_width_mm": widths,
            "crack_depth_m": depths,
            "crack_length_m": np.full(n, length_m),
            "crack_density": density,
            "water_filled": water_filled,
            "crack_growth_rate_mm_day": growths,
            "crack_severity": cat(severities, categories=["normal", "minor", "moderate", "severe", "critical"], ordered=True),
        }
    )