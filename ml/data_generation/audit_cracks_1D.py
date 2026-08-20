"""Audit the Phase 1D CRACKS track across an ensemble of seeds (pre-freeze gate).

Runs the generator for `seeds` synthetic years and measures, per zone:
  * time-to-depth-cap  -> does B reach its geometric cap too often / too smoothly?
  * max growth rate    -> does the research-defined >20 mm/day acute threshold ever
                          appear (6-12 day failure-window signal, CRACK-05.2)?
  * final depth/width  -> realized geometric caps per zone
  * family proportions -> zone-mechanism consistency expected by the research
  * severity proportions
  * material monotonicity (unit-level): for fixed inputs, does higher MATERIAL_WEAKNESS
    produce >= higher crack growth (the documented direction)?

Exit code 0 if all audit gates hold (see REQUIRED at the bottom), 1 otherwise.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generator_v1 import build_timeline, build_internal_state
from generator_schema import ZONES

ACUTE_TREND_MM_DAY = 20.0  # Leonardos & Terezopoulos 2002 failure-window signal (CRACK-05.2)


def audit_zone(df, zone_id):
    z = df[df["zone_id"] == zone_id].sort_values("timestamp").reset_index(drop=True)
    depth = z["crack_depth_m"].to_numpy()
    growth = z["crack_growth_rate_mm_day"].to_numpy()
    cap = depth.max() / max(depth.max(), 1e-9)
    bench_h = float(z["bench_height_m"].iloc[0]) if zone_id != "ZONE_D" else None
    cap_m = 0.5 * bench_h if bench_h else 1.5
    hits_cap = bool((depth >= cap_m - 1e-9).any())
    time_to_cap = None
    if hits_cap:
        idx = int(np.argmax(depth >= cap_m - 1e-9))
        time_to_cap = (pd.to_datetime(z["timestamp"].iloc[idx]) - pd.to_datetime(z["timestamp"].iloc[0])).days
    frac_acute = float((growth > ACUTE_TREND_MM_DAY).mean())
    return {
        "zone": zone_id,
        "final_depth_m": float(depth[-1]),
        "final_width_mm": float(z["crack_width_mm"].iloc[-1]),
        "final_depth_frac": float(depth[-1] / cap_m),
        "max_depth_m": float(depth.max()),
        "max_growth_mm_day": float(growth.max()),
        "p99_growth_mm_day": float(np.quantile(growth, 0.99)),
        "frac_growth_over_20": frac_acute,
        "hits_depth_cap": hits_cap,
        "time_to_cap_days": time_to_cap,
        "family": z["crack_family"].value_counts().to_dict(),
        "severity": z["crack_severity"].value_counts().to_dict(),
    }


def run_audit(seeds, days):
    rows = []
    acutes_per_seed = []
    family_contingency = {}
    for seed in range(seeds):
        timeline = build_timeline("2024-01-01", days)
        df = build_internal_state(timeline, seed)
        for z in ZONES:
            r = audit_zone(df, z)
            rows.append(r)
            for f, n in r["family"].items():
                family_contingency[(z, f)] = family_contingency.get((z, f), 0) + n
        acutes_per_seed.append(int((df["crack_growth_rate_mm_day"] > ACUTE_TREND_MM_DAY).sum()))
    summary = pd.DataFrame(rows)
    return summary, acutes_per_seed, family_contingency


def monotonicity_check():
    """Unit-level: with identical inputs, rising MATERIAL_WEAKNESS must not reduce growth.

    The exact expressions used in generate_cracks all pass growth through
    `susceptibility(weak)` (DIRECTION CONTRACT in cracks/material.py): tension
    and hydraulic are multiplied by sus; density_base rises with sus. The
    documented direction (cracks research line 88 "material weakness (clay >
    sandstone)", line 169 "cracks concentrate in the weakest materials") is:
    weakness up -> susceptibility up -> crack growth up.
    """
    from cracks.material import susceptibility, MATERIAL_WEAKNESS
    from cracks.sampler import TENSION_RATE, HYDRAULIC_GAIN

    def terms(weak):
        sus = susceptibility(weak)
        steep = 0.8
        tension = 1.0 * TENSION_RATE * steep * sus * 1.0
        hydraulic = HYDRAULIC_GAIN * 1.0 * sus
        density = 0.25 * (0.5 + sus)
        return tension, hydraulic, density

    weaks = sorted(MATERIAL_WEAKNESS.values())
    ok = True
    names = ("tension", "hydraulic", "density")
    for i, name in enumerate(names):
        vals = [terms(w)[i] for w in weaks]
        nondecreasing = all(b >= a - 1e-12 for a, b in zip(vals, vals[1:]))
        if not nondecreasing:
            ok = False
        print(f"  material monotonicity [{name}]: {'OK' if nondecreasing else 'BACKWARDS'} -> "
              f"weak {weaks[0]:.2f}->{weaks[-1]:.2f}: {vals[0]:.3f}->{vals[-1]:.3f}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--days", type=int, default=365)
    args = ap.parse_args()

    print(f"Auditing CRACKS across {args.seeds} seeds x {args.days} days")
    summary, acutes, fam = run_audit(args.seeds, args.days)
    print("\n=== Per-zone ensemble medians (P50 / P90 across seeds) ===")
    for z in ZONES:
        zs = summary[summary["zone"] == z]
        cap_frac = zs["final_depth_frac"]
        print(f"{z}: final depth/cap P50={cap_frac.median():.2f} P90={cap_frac.quantile(.9):.2f}")
        print(f"      hits cap in {(zs['hits_depth_cap'].mean()*100):.0f}% of seeds | "
              f"time-to-cap P50={zs['time_to_cap_days'].median():.0f} d P90={zs['time_to_cap_days'].quantile(.9):.0f} d")
        print(f"      max growth P50={zs['max_growth_mm_day'].median():.1f} P90={zs['max_growth_mm_day'].quantile(.9):.1f} "
              f"| frac days > 20 mm/day P50={zs['frac_growth_over_20'].median():.5f}")

    acute_total = int(sum(acutes))
    seeds_with_acute = int(sum(1 for a in acutes if a > 0))
    print(f"\n=== Acute threshold ({ACUTE_TREND_MM_DAY} mm/day) coverage ===")
    print(f"days >20 across {len(acutes)} seeds: {acute_total} | seeds with >=1 acute day: {seeds_with_acute}/{len(acutes)}")
    print("DOCUMENTED POLICY: the >20 mm/day rate is the 6-12 day PRE-FAILURE WINDOW")
    print("signal (CRACK-05.2). The routine-operations baseline is NOT expected to")
    print("reach it (structural ceiling ~10 mm/day at max PPV + peak wetting); that")
    print("crisis window is the domain of the 1E/1F stress-event layer, not the")
    print("baseline. The audit therefore asserts the baseline stays BELOW the window.")
    max_growth_overall = float(summary["max_growth_mm_day"].max())

    print("\n=== Family contingency (rows across all seeds) ===")
    import pandas as pd
    fc = pd.Series(fam, name="rows").reset_index()
    fc.columns = ["zone", "family", "count"]
    print(fc.pivot(index="zone", columns="family", values="count").fillna(0).astype(int))

    print("\n=== Material monotonicity (unit-level, must be non-decreasing) ===")
    ok_mono = monotonicity_check()

    gates = []
    # G1: no zone reaches its depth cap in a huge majority of seeds (B inspected).
    b_cap_rate = summary[summary["zone"] == "ZONE_B"]["hits_depth_cap"].mean()
    gates.append(("B depth-cap rate <= 65% of seeds (audit item 1)", b_cap_rate <= 0.65, f"rate={b_cap_rate:.0%}"))
    # G2: baseline must NOT fabricate pre-failure-window (>20 mm/day) states; the
    #     routine year stays below the failure window by construction (item 4).
    gates.append(("baseline stays below 20 mm/day failure window (audit item 4)",
                  max_growth_overall < ACUTE_TREND_MM_DAY, f"max={max_growth_overall:.1f}"))
    # G3: material direction non-decreasing.
    gates.append(("material weakness coupling direction (audit item 2)", ok_mono, ""))

    all_pass = all(g[1] for g in gates)
    print("\n=== Audit gates ===")
    for name, ok, detail in gates:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))

    print(f"\nAUDIT {'PASS' if all_pass else 'FAIL'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()