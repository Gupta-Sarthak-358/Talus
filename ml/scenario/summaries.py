"""Phase 19: compact scenario summaries, comparison tables, serialization.

Produces decision-ready summaries (not 365-row dumps), provenance metadata,
and edge-case gates for the Scenario Engine.
"""
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\scenario")
from engine import Scenario, run_scenario, baseline, TEMPLATES
from generator_schema import GENERATOR_VERSION
from instability.sampler import CRITICAL_FOS, HIGH_FOS

ORDER = ["very_low", "low", "moderate", "high", "critical"]


def _template_provenance(sc):
    if sc.kind != "historical_rain":
        return None
    tid = sc.params.get("template_id", "dec_1902")
    a, b = TEMPLATES[tid]
    imd = pd.read_csv(r"C:\Users\satvi\Desktop\Talus\data\processed\imd\neyveli_rainfall_1901_2024.csv",
                      parse_dates=["timestamp"])
    w = imd[(imd.timestamp >= a) & (imd.timestamp <= b)]
    return {"template_id": tid, "imd_window": [a, b], "source": "IMD 0.25deg Neyveli grid 11.5N 79.5E",
            "window_total_mm": round(float(w.rainfall_mm.sum()), 1),
            "window_max_day_mm": round(float(w.rainfall_mm.max()), 1),
            "scale": float(sc.params.get("scale", 1.0))}


def summarize(sc, horizon_days=365):
    b = baseline(sc.zone_id, sc.seed, days=horizon_days)
    m = run_scenario(sc, days=horizon_days)
    diff = m["instability_score"].values - b["instability_score"].values
    onset = int(np.argmax(np.abs(diff) > 1.0)) if (np.abs(diff) > 1.0).any() else None
    worst = int(np.argmax(m["instability_score"].values))
    return {
        "scenario": sc.name, "kind": sc.kind, "zone": sc.zone_id,
        "start_day": sc.start_day, "duration_days": sc.duration_days,
        "params": sc.params, "seed": sc.seed, "horizon_days": horizon_days,
        "generator_version": GENERATOR_VERSION,
        "template_provenance": _template_provenance(sc),
        "baseline_min_fos": round(float(b["fos"].min()), 3),
        "scenario_min_fos": round(float(m["fos"].min()), 3),
        "delta_min_fos": round(float(m["fos"].min() - b["fos"].min()), 3),
        "baseline_peak_instability": float(b["instability_score"].max()),
        "scenario_peak_instability": float(m["instability_score"].max()),
        "delta_peak_instability": round(float(m["instability_score"].max() - b["instability_score"].max()), 1),
        "baseline_days_high_or_critical": int(b["risk_label"].astype(str).isin(["high", "critical"]).sum()),
        "scenario_days_high_or_critical": int(m["risk_label"].astype(str).isin(["high", "critical"]).sum()),
        "peak_crack_growth_mm_day": round(float(m["crack_growth_rate_mm_day"].max()), 3),
        "peak_pore_pressure_kpa": round(float(m["pore_pressure_kpa"].max()), 1),
        "max_groundwater_proxy_mm": round(float(m["groundwater_proxy"].max()), 1),
        "first_response_day": onset,
        "worst_day": worst,
        "worst_day_risk": str(m.loc[worst, "risk_label"]),
    }


def print_summary(s):
    lines = [
        f"Scenario: {s['scenario']}  ({s['kind']}, zone {s['zone']}, "
        f"day {s['start_day']}+{s['duration_days']}d, seed {s['seed']})",
        f"  Baseline min FoS:        {s['baseline_min_fos']:.3f}",
        f"  Scenario min FoS:        {s['scenario_min_fos']:.3f}   (d {s['delta_min_fos']:+.3f})",
        f"  Baseline peak score:     {s['baseline_peak_instability']:.0f}",
        f"  Scenario peak score:     {s['scenario_peak_instability']:.0f}   (d {s['delta_peak_instability']:+.1f})",
        f"  Days High/Critical:      {s['baseline_days_high_or_critical']} -> {s['scenario_days_high_or_critical']}",
        f"  Peak crack growth:       {s['peak_crack_growth_mm_day']:.3f} mm/day",
        f"  Peak pore pressure:      {s['peak_pore_pressure_kpa']:.1f} kPa",
        f"  Max groundwater proxy:   {s['max_groundwater_proxy_mm']:.1f} mm",
        f"  First response day:      {s['first_response_day']}",
        f"  Worst day:               day {s['worst_day']} ({s['worst_day_risk']})",
    ]
    if s["template_provenance"]:
        t = s["template_provenance"]
        lines.append(f"  Template:                {t['template_id']} [{t['imd_window'][0]}..{t['imd_window'][1]}] "
                     f"total {t['window_total_mm']}mm, max day {t['window_max_day_mm']}mm (x{t['scale']})")
    return "\n".join(lines)


def compare(summaries):
    rows = []
    for s in summaries:
        rows.append({"scenario": s["scenario"], "zone": s["zone"],
                     "peak_inst": s["scenario_peak_instability"],
                     "d_peak": s["delta_peak_instability"],
                     "min_fos": s["scenario_min_fos"],
                     "days_high+crit": s["scenario_days_high_or_critical"],
                     "peak_growth": s["peak_crack_growth_mm_day"],
                     "peak_gw": s["max_groundwater_proxy_mm"],
                     "onset_day": s["first_response_day"]})
    return pd.DataFrame(rows)


def serialize_trajectory(df, sc, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"trajectory_{sc.name}.csv"
    df.to_csv(csv_path, index=False)
    meta = {"scenario": asdict(sc), "generator_version": GENERATOR_VERSION,
            "template_provenance": _template_provenance(sc),
            "rows": int(len(df)), "note": "trajectory produced by frozen physics chain; scores never written directly"}
    meta_path = out_dir / f"trajectory_{sc.name}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return csv_path, meta_path


def edge_cases():
    """Phase 19 edge-case gates."""
    res = {}
    zc = "ZONE_C"

    zero = run_scenario(Scenario(name="edge_scale0", kind="historical_rain", zone_id=zc,
                                 seed=42, start_day=200, duration_days=31,
                                 params={"template_id": "dec_1902", "scale": 0.0}))
    base = baseline(zc, 42)
    res["scale0_equals_baseline"] = bool(np.allclose(zero["fos"], base["fos"]))

    d0 = run_scenario(Scenario(name="edge_start0", kind="rainfall_storm", zone_id=zc,
                               seed=42, start_day=0, duration_days=5, params={"peak_mm": 80}))
    res["start_day_zero_runs"] = bool(len(d0) == 365 and np.isfinite(d0["fos"]).all())

    long_s = Scenario(name="edge_overrun", kind="rainfall_storm", zone_id=zc, seed=42,
                      start_day=360, duration_days=30, params={"peak_mm": 60})
    over = run_scenario(long_s)
    res["overrun_clips_safely"] = bool(len(over) == 365 and np.isfinite(over["fos"]).all())

    surge_c = run_scenario(Scenario(name="edge_blastC", kind="blast_surge", zone_id=zc,
                                    seed=42, start_day=200, duration_days=30,
                                    params={"ppv_mult": 2.0, "extra_event_prob": 0.5}))
    res["blast_surge_nonblast_zone_noop"] = bool(
        np.allclose(surge_c["blast_vibration_ppv_mms"], base["blast_vibration_ppv_mms"]))

    try:
        run_scenario(Scenario(name="edge_bad", kind="meteor_shower", zone_id=zc, seed=42))
        res["unknown_kind_raises"] = False
    except ValueError:
        res["unknown_kind_raises"] = True

    short_t = run_scenario(Scenario(name="edge_shortT", kind="historical_rain", zone_id=zc,
                                    seed=42, start_day=200, duration_days=90,
                                    params={"template_id": "apr_1931", "scale": 1.0}))
    res["short_template_pads"] = bool(len(short_t) == 365 and np.isfinite(short_t["fos"]).all())

    return res


if __name__ == "__main__":
    defs = [
        Scenario(name="A_storm_100mm", kind="rainfall_storm", zone_id="ZONE_C", seed=42,
                 start_day=200, duration_days=7, params={"peak_mm": 100}),
        Scenario(name="B_prolonged_30d", kind="prolonged_rain", zone_id="ZONE_C", seed=42,
                 start_day=200, duration_days=30, params={"daily_mm": 20}),
        Scenario(name="D_combined_ZONE_B", kind="combined", zone_id="ZONE_B", seed=42,
                 start_day=200, duration_days=14,
                 params={"peak_mm": 120, "ppv_mult": 2.0, "extra_event_prob": 0.3}),
        Scenario(name="E_dec1902_1yr", kind="historical_rain", zone_id="ZONE_C", seed=42,
                 start_day=200, duration_days=31, params={"template_id": "dec_1902"}),
        Scenario(name="F_dec1902_3yr", kind="historical_rain", zone_id="ZONE_C", seed=42,
                 start_day=550, duration_days=31, params={"template_id": "dec_1902"},
                 scenario_seed=0),
    ]
    sums = []
    for sc in defs:
        h = 1095 if sc.name.startswith("F_") else 365
        s = summarize(sc, horizon_days=h)
        sums.append(s)
        print(print_summary(s), flush=True)
        print(flush=True)

    print("=== COMPARISON TABLE ===")
    print(compare(sums).to_string(index=False))

    print("\n=== EDGE CASES ===")
    edges = edge_cases()
    for k, v in edges.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    out_dir = Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\scenario_outputs")
    csvp, metap = serialize_trajectory(run_scenario(defs[4], days=1095), defs[4], out_dir)
    print(f"\nserialized flagship trajectory -> {csvp.name} + .meta.json")

    Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\phase19_summaries.json").write_text(
        json.dumps({"summaries": sums, "edge_cases": edges}, indent=2, default=str), encoding="utf-8")
    print("all edge cases PASS" if all(edges.values()) else "EDGE FAILURES PRESENT")