"""Phase 1E calibration / sensitivity audit (diagnostic only -- NO model changes).

Purpose (user request, 2026-08-20):
  Quantify why the frozen 1B constants pin each zone to a single risk band.
  For every zone, report baseline dry/intact, wet, cracked, wet+cracked, and
  wet+cracked+blast counterfactual FoS+band under the CURRENT 1E formulation,
  plus the per-driver sensitivity of FoS to (a) rainfall/pore pressure,
  (b) crack-density degradation, (c) blast-induced damage. Then classify the
  pinning as: expected-from-constants / insufficient coupling / c-phi regime /
  implementation issue.

Nothing in the model or validator is modified by this script.
"""
import sys
import json

import numpy as np

sys.path.insert(0, ".")
from generator_schema import BASE_DIR, ZONES, GEOTECH_CSV
from generator_v1 import build_internal_state, build_timeline
from instability.sampler import (
    fos_slope, fos_floor, pore_ratio, cohesion_retention,
    band_labels, CRITICAL_FOS, HIGH_FOS, MODERATE_FOS, LOW_FOS, FOS_CAP,
    RU_WET, WATER_FILL_RU_BOOST, WETTING_SAT_MM, K_CRACK, D_REF,
    OPEN_CRACK_RETENTION, STEEP_FACE_DEG, HEAVE_REF_KPA,
)
import pandas as pd


def band_of(fos):
    r, _ = band_labels(np.array([fos]))
    return r[0]


def sensitivity_row(z, seed=42, proxy_wet=None):
    """Build one counterfactual table row for a bench zone."""
    tl = build_timeline("2024-01-01", 365)
    df = build_internal_state(tl, seed)
    zsub = df[df["zone_id"] == z].sort_values("timestamp")
    row = zsub.iloc[0]
    c, phi = float(row["cohesion_kpa"]), float(row["friction_angle_deg"])
    g = float(row["unit_weight_kn_m3"])
    h, th = float(row["slope_height_m"]), float(row["slope_angle_deg"])
    face = float(row["bench_face_angle_deg"])

    # Observed crack state in this zone (real generator output).
    dens_max = float(zsub["crack_density"].max())
    dens_p95 = float(zsub["crack_density"].quantile(0.95))
    sev_p95 = str(sorted(zsub["crack_severity"].unique(), key=lambda s: ["normal", "minor", "moderate", "severe", "critical"].index(s))[-2])

    # Blast reality: does blast move density/severity in this zone?
    if z in ("ZONE_A", "ZONE_B"):
        bl = zsub[zsub["blast_occurs"]]
        nonbl = zsub[~zsub["blast_occurs"]]
        dens_bl = float(bl["crack_density"].mean()) if len(bl) else np.nan
        dens_non = float(nonbl["crack_density"].mean()) if len(nonbl) else np.nan
        sev_bl = str(bl["crack_severity"].mode().iloc[0]) if len(bl) else "n/a"
        sev_non = str(nonbl["crack_severity"].mode().iloc[0]) if len(nonbl) else "n/a"
    else:
        dens_bl = dens_non = sev_bl = sev_non = np.nan

    # Representative wetting proxy.
    if proxy_wet is None:
        proxy_wet = WETTING_SAT_MM  # saturation reference (180 mm)
    p_dry, p_wet = 0.0, proxy_wet

    # ---- Counterfactual states (current formulation, no changes) -------
    def fos(r_u, density, sev, filled):
        ret = cohesion_retention(density, sev, filled, face)
        return float(fos_slope(c, phi, g, h, th, 0.0, filled, density, sev, face,
                               r_u_override=r_u, retention_override=ret))

    dry_intact = fos(0.0, 0.0, "normal", False)                     # 1
    wet_intact = fos(pore_ratio(p_wet, False), 0.0, "normal", False)  # 2
    wet_cracked_ordinary = fos(pore_ratio(p_wet, True), dens_p95, sev_p95, True)  # 4 (water-filled crack)
    wet_cracked_open = fos(pore_ratio(p_wet, True), 0.9, "critical", True)        # open-crack branch if face>=60
    wet_cracked_blast = fos(pore_ratio(p_wet, True), 1.0, "critical", True)       # blast-damaged terminal state

    # ---- Per-driver sensitivity (holding everything else fixed) --------
    # (a) pore-pressure / rainfall: sweep r_u at INTACT retention.
    r_sweep = [0.0, 0.15, RU_WET, RU_WET + WATER_FILL_RU_BOOST]
    dp_rain = [fos(ru, 0.0, "normal", False) for ru in r_sweep]
    # analytic: dFoS/dr_u = -tan(phi)/tan(theta)  (per unit r_u)
    an_dru = -np.tan(np.radians(phi)) / np.tan(np.radians(th))
    # (b) crack-density degradation: at dry r_u, sweep density under ordinary budget.
    dens_sweep = [0.0, 0.5, 1.0]
    dc_crack = [fos(0.0, d, "moderate", False) for d in dens_sweep]
    an_dret = c * 0.1 / (g * h * np.sin(np.radians(th)) * np.cos(np.radians(th)))  # per 0.1 retention
    # (c) blast-induced crack state: density -> severity escalation (terminal).
    db_blast = [wet_cracked_ordinary, wet_cracked_open, wet_cracked_blast]

    return {
        "zone": z, "material": str(row["material_class"]), "c": c, "phi": phi,
        "g": g, "h": h, "theta": th, "face": face, "regime": str(row["parameter_regime"]),
        "dens_max": dens_max, "dens_p95": dens_p95, "sev_p95": sev_p95,
        "dens_bl": dens_bl, "dens_non": dens_non, "sev_bl": sev_bl, "sev_non": sev_non,
        "states": {
            "dry_intact": dry_intact,
            "wet_intact": wet_intact,
            "wet_cracked_ordinary": wet_cracked_ordinary,
            "wet_cracked_open": wet_cracked_open,
            "wet_cracked_blast": wet_cracked_blast,
        },
        "sensitivity": {
            "an_dFoS_dr_u_per_unit": an_dru,
            "rain_r_sweep": {"r_u": r_sweep, "fos": dp_rain},
            "an_dFoS_per_0.1_retention": an_dret,
            "crack_dens_sweep": {"density": dens_sweep, "fos_ret": dc_crack},
            "blast_chain": db_blast,
        },
        "denominator_gamma_h_sct": g * h * np.sin(np.radians(th)) * np.cos(np.radians(th)),
        "cohesion_term_c_den": c / (g * h * np.sin(np.radians(th)) * np.cos(np.radians(th))),
        "friction_term_tan_phi_tan_th": np.tan(np.radians(phi)) / np.tan(np.radians(th)),
    }


def floor_row(seed=42):
    tl = build_timeline("2024-01-01", 365)
    df = build_internal_state(tl, seed)
    d = df[df["zone_id"] == "ZONE_D"].sort_values("timestamp")
    pp = d["pore_pressure_kpa"].to_numpy()
    thrust = float(d["groundwater_thrust_kpa"].iloc[0])
    return {
        "zone": "ZONE_D", "material": str(d["material_class"].iloc[0]),
        "thrust_kpa": thrust, "p50_pp": float(np.median(pp)), "p95_pp": float(np.quantile(pp, 0.95)),
        "fos_dry": float(fos_floor(thrust, False)), "fos_p50": float(fos_floor(np.median(pp), False)),
        "fos_p95": float(fos_floor(np.quantile(pp, 0.95), True)),
        "band_dry": band_of(fos_floor(thrust, False)),
        "band_p50": band_of(fos_floor(np.median(pp), False)),
        "band_p95": band_of(fos_floor(np.quantile(pp, 0.95), True)),
        "check": "floor-uplift branch; h=0 => no infinite slope. HEAVE_REF=490.",
    }


def main():
    seeds = [42, 43, 44, 45, 46]
    rows = []
    for z in ["ZONE_A", "ZONE_B", "ZONE_C"]:
        rows.append(sensitivity_row(z, seed=42))
    rows.append(floor_row())
    rows.append({})  # placeholder for cross-seed summary

    print("=" * 100)
    print("PHASE 1E DIAGNOSTIC AUDIT -- counterfactual FoS states (seed 42)")
    print("Current formulation untouched. Bands: <0.80 crit, <1.00 high, <1.20 mod, <1.50 low, >=1.50 vlow.")
    print("=" * 100)
    for r in rows:
        if not r:
            continue
        if r["zone"] == "ZONE_D":
            print(f"\n[ZONE_D] {r['material']} | thrust={r['thrust_kpa']:.0f} kPa | p50={r['p50_pp']:.0f} p95={r['p95_pp']:.0f}")
            print(f"  FoS dry={r['fos_dry']:.2f} ({r['band_dry']}) | FoS p50={r['fos_p50']:.2f} ({r['band_p50']}) | FoS p95+filled={r['fos_p95']:.2f} ({r['band_p95']})")
            print(f"  {r['check']}")
            continue
        st = r["states"]
        print(f"\n[{r['zone']}] {r['material']} | c={r['c']:.0f} phi={r['phi']:.0f} g={r['g']:.1f} | "
              f"h={r['h']:.1f} m theta={r['theta']:.1f}deg face={r['face']:.0f}deg regime={r['regime']}")
        print(f"  geometry-driven terms: gamma*h*sin*cos={r['denominator_gamma_h_sct']:.1f} | "
              f"c/(gamma*h*s*cos)={r['cohesion_term_c_den']:.2f} | tan(phi)/tan(theta)={r['friction_term_tan_phi_tan_th']:.2f}")
        print(f"  observed crack stats: dens_max={r['dens_max']:.2f} dens_p95={r['dens_p95']:.2f} sev_p95={r['sev_p95']}")
        if not np.isnan(r["dens_bl"]):
            print(f"  blast reality: mean density blast-days={r['dens_bl']:.2f} vs non-blast={r['dens_non']:.2f} | "
                  f"severity mode blast={r['sev_bl']} vs non-blast={r['sev_non']}")
        print(f"  INCR driving gradient (each state ADDS the named driver):")
        print(f"    dry+intact            FoS={st['dry_intact']:.2f}  -> {band_of(st['dry_intact'])}")
        print(f"    wet+intact            FoS={st['wet_intact']:.2f}  -> {band_of(st['wet_intact'])}")
        print(f"    wet+cracked(ordinary) FoS={st['wet_cracked_ordinary']:.2f}  -> {band_of(st['wet_cracked_ordinary'])}")
        print(f"    wet+cracked(open)     FoS={st['wet_cracked_open']:.2f}  -> {band_of(st['wet_cracked_open'])}")
        print(f"    wet+cracked+blast     FoS={st['wet_cracked_blast']:.2f}  -> {band_of(st['wet_cracked_blast'])}")
        sen = r["sensitivity"]
        print(f"  SENSITIVITY (driver isolation):")
        print(f"    a) pore-pressure/rainfall: analytic dFoS/dr_u = {sen['an_dFoS_dr_u_per_unit']:+.3f} per unit r_u "
              f"(FoS at r_u {sen['rain_r_sweep']['r_u']}: {[round(f,2) for f in sen['rain_r_sweep']['fos']]})")
        print(f"    b) crack-density budget: analytic dFoS per +0.1 retention = {sen['an_dFoS_per_0.1_retention']:+.4f} "
              f"(FoS at density {sen['crack_dens_sweep']['density']}: {[round(f,2) for f in sen['crack_dens_sweep']['fos_ret']]})")
        print(f"    c) blast-to-cracks chain: FoS {[round(f,2) for f in sen['blast_chain']]}")

    # Cross-seed: does pinning persist or is it a seed-42 pathology?
    print("\n" + "=" * 100)
    print("CROSS-SEED BAND PINNING (42-46): does each zone stay pinned regardless of seed?")
    print("=" * 100)
    for z in ["ZONE_A", "ZONE_B", "ZONE_C", "ZONE_D"]:
        bands_by_seed = {}
        fos_ranges = {}
        for seed in seeds:
            tl = build_timeline("2024-01-01", 365)
            df = build_internal_state(tl, seed)
            s = df[df["zone_id"] == z]["fos"]
            rb = df[df["zone_id"] == z]["risk_label"].unique()
            bands_by_seed[seed] = sorted(map(str, rb))
            fos_ranges[seed] = (round(float(s.min()), 2), round(float(s.max()), 2))
        print(f"  {z}: bands per seed = {bands_by_seed}")
        print(f"      FoS ranges per seed = {fos_ranges}")


if __name__ == "__main__":
    main()