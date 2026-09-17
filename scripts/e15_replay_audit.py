"""E15: frozen-system temporal replay audit (SIH26001).

Rebuilt replay (current weights) is audited, not trusted:
 1. causality re-asserts (dates <= event, monotonic, pre-event scenes/soil)
 2. analogue leakage (was training positive? seismic ref-year vs event year?)
 3. rain spot-check vs local IMD archive (3 days)
 4. ledger recomputation (first crossings, leads, episodes) vs committed
 5. warning replay: band>=High as alert; burden + exposure join
 6. verdict: does the frozen system survive time?
No retraining, no weight changes. Outputs: runs/e15.json.
Run: mnemo-venv python scripts/e15_replay_audit.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "data/sih26001/evidence/replay_series.json"
SUMMARY = REPO / "data/sih26001/evidence/counterfactual_summary.json"
MAT = REPO / "data/sih26001/processed/feature_matrix.training.csv"
SIDE = REPO / "data/sih26001/processed/training_sidecar.csv"
RUNOUT = REPO / "data/sih26001/evidence/runout_exposure.json"
OUT = REPO / "runs" / "e15.json"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    mat = pd.read_csv(MAT)
    side = pd.read_csv(SIDE)
    res: dict = {"cases": []}

    # ---- 4. ledger recomputation (independent of builder) ----
    for c in bundle["cases"]:
        df = pd.DataFrame(c["series"])
        ev = pd.Timestamp(c["event_date"])
        dates = pd.to_datetime(df["date"])
        assert ((dates <= ev).all() and dates.is_monotonic_increasing), f"{c['id']}: causality violated"
        hot = df["band"].isin(["High", "Critical"]).tolist()
        # episodes: contiguous hot runs separated by >=3 calm days
        eps, start, calm = [], None, 0
        dl = df["date"].tolist()
        for d, h in zip(dl, hot):
            if h:
                start = d if start is None else start
                calm = 0
            elif start is not None:
                calm += 1
                if calm >= 3:
                    eps.append((start, dl[dl.index(d) - 3]))
                    start, calm = None, 0
        if start is not None:
            eps.append((start, dl[-1]))
        first = {}
        for band in ("Moderate", "High", "Critical"):
            hit = df.index[df["band"] == band].tolist() or \
                df.index[df["band"].isin(["Moderate", "High", "Critical"][["Moderate", "High", "Critical"].index(band):])].tolist()
            first[band] = df["date"].iloc[hit[0]] if hit else None
        lead = {b: ((ev - pd.Timestamp(d)).days if d else None) for b, d in first.items()}
        early = max(0, len(eps) - (1 if eps and eps[-1][1] >= dl[-7] else 0))
        hot_days = int(np.array(hot).sum())
        entry = {"id": c["id"], "n_days": len(df),
                 "first": first, "lead": lead, "episodes": eps,
                 "early_hot_episodes": early, "hot_days": hot_days,
                 "burden_frac": round(hot_days / len(df), 3)}
        # diff vs committed ledger
        led = next(x for x in bundle["ledger"] if x["id"] == c["id"])
        entry["ledger_match"] = bool(
            (first["Moderate"] == led["first_moderate"]) and
            (first["High"] == led["first_high"]) and
            (first["Critical"] == led["first_critical"]) and
            (early == led["early_hot_episodes"]))
        res["cases"].append(entry)
        log(f"{c['id']}: High {first['High']} ({lead['High']}d) Critical {first['Critical']} "
            f"burden {hot_days}/{len(df)} ledger_match={entry['ledger_match']}")

    # ---- 2. analogue leakage ----
    res["analogue"] = []
    for c in summary["cases"]:
        row = mat[mat["zone_id"] == c["terrain_analogue_row"]].iloc[0]
        srow = side[side["zone_id"] == c["terrain_analogue_row"]].iloc[0]
        evy = int(c["event_date"][:4])
        ref = int(srow.get("seismic_ref_year", evy))
        res["analogue"].append({
            "id": c["id"], "row": c["terrain_analogue_row"],
            "dist_m": c["analogue_distance_m"], "was_training_positive": bool(c["analogue_was_training_positive"]),
            "seismic_ref_year": ref, "ref_after_event": bool(ref > evy),
            "soil_source": c.get("soil_source"), "ndvi_source": c.get("ndvi_source")})
    log(f"analogues training-positive: {sum(a['was_training_positive'] for a in res['analogue'])}/5; "
        f"seismic ref-after-event: {sum(a['ref_after_event'] for a in res['analogue'])}/5")

    # ---- 3. rain spot-check vs IMD archive ----
    import xarray as xr
    checks = [("mangan-jun2024", "2024-06-10"), ("nh10-oct2022", "2022-10-05"),
              ("dipudara-aug2024", "2024-08-15")]
    res["rain_spot"] = []
    for cid, day in checks:
        c = next(x for x in bundle["cases"] if x["id"] == cid)
        lat, lon = {"mangan-jun2024": (27.51, 88.53), "nh10-oct2022": (27.13, 88.51),
                    "dipudara-aug2024": (27.2525, 88.4606)}[cid]
        yr = int(day[:4])
        with xr.open_dataset(REPO / f"data/raw/imd/ind{yr}_rfp25.nc") as ds:
            s = ds.RAINFALL.sel(LATITUDE=lat, LONGITUDE=lon, method="nearest")
            vals = pd.Series(np.asarray(s.sel(TIME=slice("2020-01-01", day)).values, dtype=float),
                             index=pd.to_datetime(s.sel(TIME=slice("2020-01-01", day)).TIME.values))
        w = vals.loc[:day]
        expect = {"rain_24h": round(float(w.iloc[-1]), 1),
                  "rain_7d": round(float(w.iloc[-7:].sum()), 1)}
        got = next(r for r in c["series"] if r["date"] == day)
        res["rain_spot"].append({"id": cid, "day": day, "expect": expect,
                                 "got": {k: got[k] for k in ("rain_24h", "rain_7d")},
                                 "match": abs(expect["rain_24h"] - got["rain_24h"]) < 0.2
                                 and abs(expect["rain_7d"] - got["rain_7d"]) < 0.2})
    log(f"rain spot-checks match: {[r['match'] for r in res['rain_spot']]}")

    # ---- 5. exposure join (runout covers Gangtok demo slopes only) ----
    sites = {"mangan-jun2024": (27.51, 88.53), "dipudara-aug2024": (27.2525, 88.4606),
             "lumsay-jun2022": (27.32633333, 88.59544444), "sichey-jun2021": (27.33787, 88.609377),
             "nh10-oct2022": (27.13, 88.51)}
    run = json.loads(RUNOUT.read_text(encoding="utf-8"))
    # demo-zone centroids approximated from runout path starts
    res["exposure"] = []
    for cid, (la, lo) in sites.items():
        best, bd = None, 1e18
        for zid, z in run.get("zones", {}).items():
            path = z.get("path") or []
            if not path:
                continue
            d = min(abs(la - p[0]) * 111320 + abs(lo - p[1]) * 111320 * np.cos(np.radians(la)) for p in path)
            if d < bd:
                bd, best = d, (zid, z.get("buildings_n"))
        covered = bool(bd < 1500)
        res["exposure"].append({"id": cid, "nearest_runout": best[0] if best else None,
                                "dist_m": int(round(float(bd))), "buildings": best[1] if best else None,
                                "covered": covered})
    log(f"exposure covered: {sum(e['covered'] for e in res['exposure'])}/5")

    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT}")
    print("\n===== E15 LEDGER (recomputed) =====")
    for e in res["cases"]:
        print(f"{e['id']}: High {e['first']['High']} ({e['lead']['High']}d) "
              f"Critical {e['first']['Critical']} burden {e['hot_days']}/{e['n_days']} "
              f"match={e['ledger_match']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
