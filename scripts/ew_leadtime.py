"""Early-warning lead-time evaluation on frozen M0 outputs (descriptive, no modeling).

Persistent escalation per EW_LEADTIME_CRITERION.md + background false-escalation
approximation + evidence drivers per event. Outputs runs/phase_v/ew/.
Run: mnemo-venv python scripts/ew_leadtime.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
M0 = REPO / "runs" / "phase_v" / "m0" / "predictions.csv"
SPLIT = REPO / "splits" / "championship_split_v1.json"
FOS = REPO / "runs" / "phase_v" / "vi2pb" / "physics_features.json"
OUTDIR = REPO / "runs" / "phase_v" / "ew"
LVL = {"WATCH": ["Moderate", "High", "Critical"], "ALERT": ["High", "Critical"]}


def log(m: str) -> None:
    import time
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    p = pd.read_csv(M0)
    p["dt"] = pd.to_datetime(p["grid_end"])
    fos = json.load(open(FOS, encoding="utf-8"))
    rows = []
    for ev, g in p.groupby("event"):
        g = g.sort_values("dt").reset_index(drop=True)
        Tend = g["dt"].max().date()
        evd = pd.Timestamp(Tend)
        r = {"event": ev, "side": g["side"].iloc[0], "T": str(g["grid_end"].max())}
        for lvl, bands in LVL.items():
            ok = g["band"].isin(bands).tolist()
            first = None
            for i in range(len(g)):
                if all(ok[i:]):
                    first = i
                    break
            if first is None:
                r[f"first_{lvl.lower()}"], r[f"lead_{lvl.lower()}_d"] = None, None
            else:
                r[f"first_{lvl.lower()}"] = str(g.loc[first, "grid_end"])
                r[f"lead_{lvl.lower()}_d"] = (Tend - g.loc[first, "dt"].date()).days
        t = g[g["snapshot"] == "T"].iloc[0]
        f = fos.get(ev, {}).get("snapshots", {}).get("T", {})
        r.update({"T_band": t["band"], "T_rain30": float(g[g["snapshot"] == "T"]["raw_score"].iloc[0]),
                  "fos_med_T": f.get("fos_median"), "ood_T": bool(t["ood"])})
        rows.append(r)
    t = pd.DataFrame(rows)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUTDIR / "leadtime.csv", index=False)

    def dist(col):
        v = t[col].dropna()
        return {"n": int(v.notna().sum()), "miss": int(t[col].isna().sum()),
                "median": float(v.median()) if len(v) else None,
                "p25": float(v.quantile(0.25)) if len(v) else None,
                "ge14": int((v >= 14).sum()), "ge7": int((v >= 7).sum()),
                "ge3": int((v >= 3).sum())} if True else {}

    rep = {"n_events": len(t),
           "watch": dist("lead_watch_d"), "alert": dist("lead_alert_d"),
           "dev_watch_med": float(t[t.side == "development"]["lead_watch_d"].median()),
           "held_watch_med": float(t[t.side == "held-out"]["lead_watch_d"].median()),
           "dev_alert_med": float(t[t.side == "development"]["lead_alert_d"].median()),
           "held_alert_med": float(t[t.side == "held-out"]["lead_alert_d"].median())}
    # background: >=3 hot-day windows (upper-bound proxy, contiguity unmeasured)
    tb = None
    for cand in ("runs/e15_incidents.json", "runs/e16.json"):
        try:
            tb = json.load(open(REPO / cand))
            break
        except Exception:
            continue
    off = json.load(open(REPO / "runs/burden_offseason.json"))
    rep["background_proxy"] = {
        "monsoon_TierB": (tb.get("tierB") or tb.get("tier_b") or tb.get("TierB", "see-artifact")) if tb else "missing",
        "offseason": off.get("summary")}
    json.dump(rep, open(OUTDIR / "leadtime_report.json", "w"), indent=2, default=str)
    log(json.dumps(rep, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
