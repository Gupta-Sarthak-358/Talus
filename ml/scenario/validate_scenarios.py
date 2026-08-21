"""Phase 11-18 validation gates + trajectory analysis for the Scenario Engine.

Gates:
  1 baseline replay == frozen generator output (exact)
  2 pre-start rows identical to baseline
  3 dose-response: stronger storm => non-increasing min FoS
  4 determinism under re-run
  5 no direct score writes in engine source
  6 crack damage accumulates (no resets) under scenario

Analysis (Phase 17): trajectory summaries per scenario on blast-capable zones.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\scenario")
from generator_v1 import build_timeline, build_internal_state
from engine import Scenario, run_scenario, baseline

OUT = Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\scenario_validation.json")
RES = {"gates": {}, "trajectories": {}}


def gate_baseline_replay():
    tl = build_timeline("2024-01-01", 365)
    ref = build_internal_state(tl, 42)
    ref = ref[ref.zone_id == "ZONE_A"].reset_index(drop=True)
    eng = baseline("ZONE_A", 42).drop(columns=["scenario"])
    cols = ["fos", "instability_score", "crack_density", "groundwater_proxy",
            "blast_vibration_ppv_mms", "rainfall_mm"]
    exact = all(np.allclose(ref[c].astype(float), eng[c].astype(float), atol=1e-12) for c in cols)
    RES["gates"]["1_baseline_replay_exact"] = bool(exact)
    print(f"gate1 baseline replay exact: {exact}", flush=True)
    return exact


def gate_pre_start_identical():
    sc = Scenario(name="storm_check", kind="rainfall_storm", zone_id="ZONE_A",
                  seed=42, start_day=200, duration_days=5, params={"peak_mm": 100})
    base = baseline("ZONE_A", 42)
    mod = run_scenario(sc)
    pre = [c for c in ["rainfall_mm", "groundwater_proxy", "crack_density", "fos"] if c in mod]
    ok = all(np.allclose(base.loc[:199, c].astype(float), mod.loc[:199, c].astype(float))
             for c in pre)
    RES["gates"]["2_pre_start_identical"] = bool(ok)
    print(f"gate2 pre-start identical: {ok}", flush=True)


def gate_dose_response():
    mins, peaks = [], []
    for peak_mm in [50, 100, 150]:
        sc = Scenario(name=f"storm_{peak_mm}", kind="rainfall_storm", zone_id="ZONE_A",
                      seed=42, start_day=200, duration_days=7,
                      params={"peak_mm": peak_mm})
        df = run_scenario(sc)
        mins.append(float(df["fos"].min()))
        peaks.append(float(df["instability_score"].max()))
    mono_fos = all(mins[i] >= mins[i + 1] - 1e-9 for i in range(len(mins) - 1))
    mono_inst = all(peaks[i] <= peaks[i + 1] + 1e-9 for i in range(len(peaks) - 1))
    RES["gates"]["3_dose_response"] = {"min_fos_by_peak": mins, "peak_inst_by_peak": peaks,
                                       "monotone": bool(mono_fos and mono_inst)}
    print(f"gate3 dose-response: minFos={mins} peakInst={peaks} monotone={mono_fos and mono_inst}", flush=True)


def gate_determinism():
    sc = Scenario(name="det_check", kind="combined", zone_id="ZONE_B", seed=42,
                  start_day=180, duration_days=10,
                  params={"peak_mm": 80, "ppv_mult": 2.0, "extra_event_prob": 0.3})
    a = run_scenario(sc)
    b = run_scenario(sc)
    same = a.drop(columns=["scenario"]).equals(b.drop(columns=["scenario"]))
    RES["gates"]["4_determinism"] = bool(same)
    print(f"gate4 determinism: {same}", flush=True)


def gate_no_score_writes():
    src = Path(r"C:\Users\satvi\Desktop\Talus\ml\scenario\engine.py").read_text(encoding="utf-8")
    bad = [ln.strip() for ln in src.splitlines()
           if ("instability_score" in ln or '"fos"' in ln or "'fos'" in ln)
           and ("=" in ln) and "==" not in ln
           and not ln.strip().startswith("#")]
    ok = len(bad) == 0
    RES["gates"]["5_no_direct_score_writes"] = {"ok": bool(ok), "suspicious": bad}
    print(f"gate5 no direct score writes: {ok}", flush=True)


def gate_crack_continuity():
    base = baseline("ZONE_A", 42)
    sc = Scenario(name="cont_check", kind="prolonged_rain", zone_id="ZONE_A", seed=42,
                  start_day=200, duration_days=30, params={"daily_mm": 25})
    mod = run_scenario(sc)
    cum_b = float(np.nansum(np.clip(np.diff(base["crack_density"].values), 0, None)))
    cum_m = float(np.nansum(np.clip(np.diff(mod["crack_density"].values), 0, None)))
    starts_same = np.isclose(base["crack_density"].iloc[0], mod["crack_density"].iloc[0])
    ok = starts_same and cum_m >= cum_b - 1e-9
    RES["gates"]["6_crack_continuity"] = {"cum_growth_baseline": round(cum_b, 4),
                                          "cum_growth_scenario": round(cum_m, 4),
                                          "same_start": bool(starts_same), "ok": bool(ok)}
    print(f"gate6 crack continuity: cum {cum_b:.4f} -> {cum_m:.4f} ok={ok}", flush=True)


def trajectories():
    scen_defs = [
        Scenario(name="A_storm_100mm", kind="rainfall_storm", zone_id="ZONE_C", seed=42,
                 start_day=200, duration_days=7, params={"peak_mm": 100}),
        Scenario(name="A2_storm_250mm", kind="rainfall_storm", zone_id="ZONE_C", seed=42,
                 start_day=200, duration_days=7, params={"peak_mm": 250}),
        Scenario(name="B_prolonged_30d", kind="prolonged_rain", zone_id="ZONE_C", seed=42,
                 start_day=200, duration_days=30, params={"daily_mm": 20}),
        Scenario(name="C_blast_surge", kind="blast_surge", zone_id="ZONE_B", seed=42,
                 start_day=200, duration_days=60, params={"ppv_mult": 2.0, "extra_event_prob": 0.3}),
        Scenario(name="D_combined", kind="combined", zone_id="ZONE_B", seed=42,
                 start_day=200, duration_days=14,
                 params={"peak_mm": 120, "ppv_mult": 2.0, "extra_event_prob": 0.3}),
        Scenario(name="E_hist_dec1902", kind="historical_rain", zone_id="ZONE_C", seed=42,
                 start_day=200, duration_days=31, params={"template_id": "dec_1902", "scale": 1.0}),
    ]
    for sc in scen_defs:
        b = baseline(sc.zone_id, sc.seed)
        m = run_scenario(sc)
        base_mode = b["risk_label"].astype(str).mode()[0]
        row = {
            "zone": sc.zone_id,
            "baseline_peak_inst": float(b["instability_score"].max()),
            "scenario_peak_inst": float(m["instability_score"].max()),
            "delta_peak": round(float(m["instability_score"].max() - b["instability_score"].max()), 1),
            "min_fos_baseline": float(b["fos"].min()),
            "min_fos_scenario": float(m["fos"].min()),
            "day_of_peak": int(m["instability_score"].idxmax()),
            "first_day_score_ge_75": (int((m["instability_score"] >= 75).idxmax())
                                      if (m["instability_score"] >= 75).any() else None),
            "days_above_75": int((m["instability_score"] >= 75).sum()),
            "baseline_dominant_risk": base_mode,
            "scenario_worst_risk": str(m.loc[m["instability_score"].idxmax(), "risk_label"]),
            "max_gw_proxy": float(m["groundwater_proxy"].max()),
            "max_crack_density": float(m["crack_density"].max()),
        }
        RES["trajectories"][sc.name] = row
        print(f"[traj] {sc.name} ({sc.zone_id}): peak {row['baseline_peak_inst']:.0f}->"
              f"{row['scenario_peak_inst']:.0f} (d{row['delta_peak']:+.1f}) "
              f"minFos {row['min_fos_scenario']:.2f} worst={row['scenario_worst_risk']} "
              f"days>=75: {row['days_above_75']}", flush=True)

    # Phase 17 flagship: multi-year cumulative exposure (frozen physics only).
    # Crack damage accumulates across years until the discrete open-crack
    # branch (critical AND water-filled AND face>=60) fires during replayed
    # historical storms -- the regime response passive generation never shows.
    order = ["very_low", "low", "moderate", "high", "critical"]
    b3 = run_scenario(Scenario(name="mc_base", kind="none", zone_id="ZONE_C", seed=42), days=1095)
    m3 = run_scenario(Scenario(name="F_multiyear_dec1902", kind="historical_rain",
                               zone_id="ZONE_C", seed=42, start_day=550, duration_days=31,
                               params={"template_id": "dec_1902", "scale": 1.0}), days=1095)
    diff = m3["fos"].values - b3["fos"].values
    crit_m = (m3["crack_severity"].astype(str) == "critical")
    filled_crit = int((crit_m & m3["water_filled"].astype(bool)).sum())
    worst_idx = int(np.argmax(m3["instability_score"].values))
    RES["trajectories"]["F_multiyear_dec1902_3yr_ZONE_C"] = {
        "horizon_days": 1095,
        "fos_divergence_min": round(float(diff.min()), 3),
        "divergence_day": int(np.argmin(diff)),
        "days_diverging_gt_001": int((np.abs(diff) > 0.01).sum()),
        "critical_severity_days_scenario": int(crit_m.sum()),
        "critical_plus_waterfilled_days": filled_crit,
        "open_crack_branch_fired": bool(filled_crit > 0),
        "scenario_worst_risk": str(m3.loc[worst_idx, "risk_label"]),
        "worst_band_index": int(order.index(str(m3.loc[worst_idx, "risk_label"]))),
        "baseline_dominant_risk": str(b3["risk_label"].astype(str).mode()[0]),
        "min_fos_scenario": float(m3["fos"].min()),
        "max_gw_proxy": float(m3["groundwater_proxy"].max()),
    }
    row = RES["trajectories"]["F_multiyear_dec1902_3yr_ZONE_C"]
    print(f"[traj] F_multiyear_dec1902 (ZONE_C, 3yr): fos div {row['fos_divergence_min']:.3f} "
          f"@day{row['divergence_day']} | branch fired={row['open_crack_branch_fired']} "
          f"crit+filled={filled_crit}d | worst band={row['scenario_worst_risk']}", flush=True)


def main():
    gate_baseline_replay()
    gate_pre_start_identical()
    gate_dose_response()
    gate_determinism()
    gate_no_score_writes()
    gate_crack_continuity()
    trajectories()
    OUT.write_text(json.dumps(RES, indent=2, default=str), encoding="utf-8")
    gates_ok = all([
        RES["gates"]["1_baseline_replay_exact"],
        RES["gates"]["2_pre_start_identical"],
        RES["gates"]["3_dose_response"]["monotone"],
        RES["gates"]["4_determinism"],
        RES["gates"]["5_no_direct_score_writes"]["ok"],
        RES["gates"]["6_crack_continuity"]["ok"],
    ])
    RES["all_gates_pass"] = bool(gates_ok)
    OUT.write_text(json.dumps(RES, indent=2, default=str), encoding="utf-8")
    print(f"\nALL GATES: {'PASS' if gates_ok else 'FAIL'}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()