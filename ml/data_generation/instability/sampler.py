"""Phase 1E instability & risk sampler (deterministic, FoS-driven).

Chain (spec §7.5, LOCKED):
    physical parameters (c, phi, gamma, theta, h) [1B, consumed unchanged]
        -> factor of safety (infinite slope, driven below by 1B-1D state)
        -> slope_condition (4 physical states)
        -> instability_score (0-100, monotone decreasing in FoS)
        -> risk_label (5 operational bands)

This module NEVER draws random numbers. FoS is a pure function of the 1B-1D
state, so two identical states always produce the identical label (spec §7.5:
"FoS is its only source - no random noise").

SEMANTICS (documented decisions for 1E):
  u (benches A/B/C)
    = pore-pressure RATIO applied to the normal stress gamma*h*cos^2(theta),
      per the standard infinite-slope pore-pressure formulation:
        FoS = (c_eff + gamma*h*cos^2(theta)*(1 - r_u)*tan(phi))
                        / (gamma*h*sin(theta)*cos(theta))
    r_u grows with the 1C wetting transient (groundwater_proxy, mm) and is
    amplified by water-filled cracks (USACE assumption). The zone-static
    confined-aquifer THRUST is deliberately NOT placed on a shallow bench slip
    plane: plan §D defines u as "rainfall + groundwater proxy"; the thrust is
    the floor-heave driver handled by ZONE_D's uplift branch. Using the raw
    thrust (100-785 kPa) on a 6 m bench forces gamma*h*cos^2 < u and a negative
    / unphysical effective stress; the ratio form keeps FoS physical and in
    [0, ~2.5] (cap contract).

  ZONE_D (pit floor, h=0, theta~0)
    The infinite-slope has no slope. Failure mode is UPLIFT/heave by the
    confined aquifer (geology §3.4, cracks heave term). FoS_D is the ratio of
    the documented 490 kPa activation reference to the current pore pressure
    (thrust + transient), so it is chronically high/critical and still rises
    with rainfall - exactly the documented condition (groundwater §semantics).

  c_eff (CRACK-DENSITY CONTRACT, LOCKED):
    ordinary path c_eff = c*(1 - k_crack*min(crack_density/D_REF, 1)), k~0.10,
    so even crack_density -> 1 costs at most ~10% (Lu 2022). The -50% branch is
    reserved for the steep engineered open-crack worst case (Michalowski 2013):
    requires critical severity + water_filled + bench face >= 60 deg. It is a
    distinct branch, not a continuous function of density.

  Blast never touches FoS directly; it lowers c_eff through the blast-induced
  crack state (crack_growth/pvp path), per contract.

Constants keep the cracked-cohesion budget monotone so the validator's
counterfactual ordering gate (dry >= wet >= cracked >= cracked+blast) always
holds within a zone.
"""
import numpy as np
import pandas as pd

from generator_schema import SLOPE_CONDITIONS, RISK_LABELS

# ---- Bands (spec §7.5, prototype thresholds) -----------------------------
CRITICAL_FOS = 0.80
HIGH_FOS = 1.00
MODERATE_FOS = 1.20
LOW_FOS = 1.50
FOS_CAP = 2.5
FOS_FLOOR = 0.5  # score saturates at 100 below this

# ---- Pore-pressure ratio -------------------------------------------------
# r_u reaches ~RU_WET at fully saturated wetting; water-filled cracks add a
# hydrostatic wall-pressure boost; never exceed R_U_MAX (keeps 1-r_u > 0.4).
RU_WET = 0.35
WATER_FILL_RU_BOOST = 0.15
R_U_MAX = 0.55
# Saturation reference = 3x the cracks wetting threshold (cracks normalizes
# wetting by 60 mm and clips at 3x for its wet factor; keep the same clock).
WETTING_SAT_MM = 180.0

# ---- Crack-density -> cohesion retention (CRACK-DENSITY CONTRACT) --------
K_CRACK = 0.10
D_REF = 1.0
OPEN_CRACK_RETENTION = 0.50  # Michalowski -50% branch
STEEP_FACE_DEG = 60.0

# ---- ZONE_D floor-heave (uplift) reference -------------------------------
# Same activation threshold used by the cracks heave term (thrust/490 - 1).
HEAVE_REF_KPA = 490.0


def _cos_sin(theta_deg):
    th = np.radians(np.asarray(theta_deg, dtype=float))
    return np.cos(th), np.sin(th)


def pore_ratio(proxy_mm, water_filled):
    """r_u in [0, R_U_MAX] from wetting transient + water-filled cracks."""
    wet = np.clip(np.asarray(proxy_mm, dtype=float) / WETTING_SAT_MM, 0.0, 1.0)
    r_u = RU_WET * wet
    filled = np.asarray(water_filled, dtype=bool)
    r_u = np.where(filled, r_u + WATER_FILL_RU_BOOST, r_u)
    return np.clip(r_u, 0.0, R_U_MAX)


def cohesion_retention(crack_density, crack_severity, water_filled, bench_face_deg):
    """c_eff/c in [0.5, 1.0]: ordinary -10% line + reserved -50% branch."""
    density = np.asarray(crack_density, dtype=float)
    ret = 1.0 - K_CRACK * np.minimum(density / D_REF, 1.0)
    sev = np.asarray(crack_severity)
    critical = sev == "critical"
    filled = np.asarray(water_filled, dtype=bool)
    steep = np.asarray(bench_face_deg, dtype=float) >= STEEP_FACE_DEG
    open_crack = critical & filled & steep
    return np.where(open_crack, OPEN_CRACK_RETENTION, ret)


def fos_bench(c_kpa, phi_deg, gamma_kn_m3, h_m, theta_deg, r_u, retention):
    """Infinite-slope FoS (spec §7.5). Cap keeps dry-intact benches bounded."""
    cos_t, sin_t = _cos_sin(theta_deg)
    den = np.asarray(gamma_kn_m3, dtype=float) * h_m * sin_t * cos_t
    if np.any(den <= 0):
        return np.full(np.broadcast(np.asarray(c_kpa), den).shape, np.nan)
    c_eff = np.asarray(c_kpa, dtype=float) * retention
    num = c_eff + (1.0 - np.asarray(r_u, dtype=float)) * (
        np.asarray(gamma_kn_m3, dtype=float) * h_m * cos_t ** 2
    ) * np.tan(np.radians(phi_deg))
    return np.minimum(num / den, FOS_CAP)


def fos_slope(c_kpa, phi_deg, gamma_kn_m3, h_m, theta_deg, proxy_mm, water_filled,
              crack_density, crack_severity, bench_face_deg, r_u_override=None,
              retention_override=None):
    """FoS for a bench zone from raw 1B-1D state (used by generator + validator).

    r_u_override / retention_override let the counterfactual gate construct
    states that differ only in the driver under test.
    """
    r_u = (pore_ratio(proxy_mm, water_filled)
           if r_u_override is None else np.asarray(r_u_override, dtype=float))
    ret = (cohesion_retention(crack_density, crack_severity, water_filled, bench_face_deg)
           if retention_override is None else np.asarray(retention_override, dtype=float))
    return fos_bench(c_kpa, phi_deg, gamma_kn_m3, h_m, theta_deg, r_u, ret)


def fos_floor(pore_pressure_kpa, water_filled=False):
    """ZONE_D uplift FoS: HEAVE_REF / current pore pressure."""
    pp = np.asarray(pore_pressure_kpa, dtype=float)
    filled = np.asarray(water_filled, dtype=bool)
    pp_eff = np.where(filled, pp * (1.0 + WATER_FILL_RU_BOOST), pp)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(pp_eff > 0, HEAVE_REF_KPA / pp_eff, FOS_CAP)


def band_labels(fos):
    """risk_label + slope_condition from FoS (spec §7.5 tables)."""
    fos = np.asarray(fos, dtype=float)
    risk = np.full(len(fos), "very_low", dtype=object)
    cond = np.full(len(fos), "stable", dtype=object)
    risk[fos < CRITICAL_FOS] = "critical"
    cond[fos < CRITICAL_FOS] = "failed"
    risk[(fos >= CRITICAL_FOS) & (fos < HIGH_FOS)] = "high"
    cond[(fos >= CRITICAL_FOS) & (fos < HIGH_FOS)] = "unstable"
    risk[(fos >= HIGH_FOS) & (fos < MODERATE_FOS)] = "moderate"
    cond[(fos >= HIGH_FOS) & (fos < MODERATE_FOS)] = "marginal"
    risk[(fos >= MODERATE_FOS) & (fos < LOW_FOS)] = "low"
    cond[(fos >= MODERATE_FOS) & (fos < LOW_FOS)] = "stable"
    risk[fos >= LOW_FOS] = "very_low"
    cond[fos >= LOW_FOS] = "stable"
    return pd.Categorical(risk, categories=RISK_LABELS, ordered=True), \
        pd.Categorical(cond, categories=SLOPE_CONDITIONS, ordered=True)


def instability_score(fos):
    """0-100, monotone decreasing in FoS. Piecewise-linear over [FLOOR, CAP]."""
    score = 100.0 * (FOS_CAP - np.asarray(fos, dtype=float)) / (FOS_CAP - FOS_FLOOR)
    return np.clip(score, 0.0, 100.0)


def generate_instability(df):
    """Set fos, slope_condition, instability_score, risk_label on df (returns df).

    Deterministic: purely functional of the 1B-1D columns already in df.
    Bench zones use the infinite slope; ZONE_D (floor, h=0) uses the uplift
    branch.
    """
    fos = np.empty(len(df), dtype=float)
    filled = df["water_filled"].fillna(False).astype(bool).to_numpy()

    bench = df["zone_id"].isin(["ZONE_A", "ZONE_B", "ZONE_C"]).to_numpy()
    if bench.any():
        b = df[bench]
        fos[bench] = fos_slope(
            b["cohesion_kpa"].to_numpy(),
            b["friction_angle_deg"].to_numpy(),
            b["unit_weight_kn_m3"].to_numpy(),
            b["slope_height_m"].to_numpy(),
            b["slope_angle_deg"].to_numpy(),
            b["groundwater_proxy"].to_numpy(),
            b["water_filled"].fillna(False).to_numpy(),
            b["crack_density"].to_numpy(),
            b["crack_severity"].astype(str).to_numpy(),
            b["bench_face_angle_deg"].to_numpy(),
        )

    floor = df["zone_id"] == "ZONE_D"
    if floor.any():
        f = df[floor]
        fos[floor] = fos_floor(f["pore_pressure_kpa"].to_numpy(),
                               f["water_filled"].fillna(False).to_numpy(dtype=bool))

    risk, cond = band_labels(fos)
    df["fos"] = fos
    df["slope_condition"] = cond
    df["instability_score"] = np.round(instability_score(fos), 1)
    df["risk_label"] = risk
    return df


if __name__ == "__main__":
    from generator_v1 import build_internal_state, build_timeline

    tl = build_timeline("2024-01-01", 365)
    df = build_internal_state(tl, 42)
    generate_instability(df)
    stats = df.groupby("zone_id").agg(
        fos_min=("fos", "min"), fos_p50=("fos", "median"), fos_max=("fos", "max"),
        risk_min=("risk_label", "min"), risk_max=("risk_label", "max"))
    print(stats.round(2))