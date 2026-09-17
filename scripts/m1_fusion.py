"""M1-A satellite-evidence fusion vs M0 (Phase V-D). NOTHING FROZEN IS RETRAINED.

Fusion inputs per snapshot: [M0 p_cal, s1_dvv_db, s1_base_vv_db, s1_dt_days,
s1_dvh_db (NaN-tolerant), vh_flag]. Optical excluded (Requester-Pays blocked,
documented). Event-level sat features constant across snapshots; dynamics from p_cal.
Model: XGB tiny (50 trees, depth 2) trained on DEV ONLY (y=imminence7 construct),
isotonic on dev. Bands: SAME FROZEN_BANDS edges on fused*100 (declared reuse, not
tuning). OOD carried from M0; status mapping frozen; + sat_evidence reporting label
(|dvv|>=1.5 strong, >=0.5 moderate else none — convention, not optimized).
Burden: rebuilt Tier-B monsoon (seed 42, same construction) + off-season windows
through M0-path AND M1 (per-window S1 pairs). Held-out comparison only.
Outputs runs/phase_v/m1/. Run: mnemo-venv python scripts/m1_fusion.py
"""
from __future__ import annotations

import glob
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
M0 = REPO / "runs" / "phase_v" / "m0" / "predictions.csv"
SAT = REPO / "runs" / "phase_v" / "m1" / "sat_features.json"
SPLIT = REPO / "splits" / "championship_split_v1.json"
OUTDIR = REPO / "runs" / "phase_v" / "m1"
LAT_SPLIT = 27.15
SEED = 42


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def band(score: float) -> str:
    if score < 50:
        return "Very Low"
    if score < 65:
        return "Low"
    if score < 75:
        return "Moderate"
    if score < 85:
        return "High"
    return "Critical"


STATE = {"Very Low": "NORMAL", "Low": "NORMAL", "Moderate": "WATCH", "High": "ALERT",
         "Critical": "CRITICAL"}
FCOLS = ["p_cal", "s1_dvv_db", "s1_base_vv_db", "s1_dt_days", "s1_dvh_db", "vh_flag"]


def main() -> int:
    from xgboost import XGBClassifier
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import roc_auc_score, average_precision_score

    p = pd.read_csv(M0)
    sat = json.load(open(SAT, encoding="utf-8"))
    for _, r in p.iterrows():
        s = sat[r["event"]]["s1"]
        for c, k in (("s1_dvv_db", "s1_dvv_db"), ("s1_base_vv_db", "s1_base_vv_db"),
                     ("s1_dt_days", "s1_dt_days"), ("s1_dvh_db", "s1_dvh_db")):
            p.loc[_, c] = s.get(k)
        p.loc[_, "vh_flag"] = int(s.get("s1_dvh_db") is not None)
    assert (p["s1_dvv_db"].notna()).all(), "S1 must cover all events"
    p["y"] = p["snapshot"].isin(["T-7", "T-3", "T-1", "T"]).astype(int)
    dev0, ho0 = p[p["side"] == "development"], p[p["side"] == "held-out"]
    clf = XGBClassifier(n_estimators=50, max_depth=2, learning_rate=0.1, subsample=0.9,
                        random_state=SEED, n_jobs=2, eval_metric="logloss")
    clf.fit(dev0[FCOLS].to_numpy(dtype=float), dev0["y"].to_numpy())
    iso = IsotonicRegression(out_of_bounds="clip").fit(
        clf.predict_proba(dev0[FCOLS].to_numpy(dtype=float))[:, 1], dev0["y"].to_numpy())
    p["p_fused"] = iso.predict(clf.predict_proba(p[FCOLS].to_numpy(dtype=float))[:, 1]).round(4)
    p["fused_score"] = (p["p_fused"] * 100).round(0).astype(int)
    p["fused_band"] = p["fused_score"].apply(band)
    p["fused_warning"] = p["fused_band"].map(STATE)
    p["sat_evidence"] = pd.cut(p["s1_dvv_db"].abs(), [-0.01, 0.5, 1.5, 1e9],
                               labels=["none", "moderate", "strong"])
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p.to_csv(OUTDIR / "m1_predictions.csv", index=False)
    dev, ho = p[p["side"] == "development"], p[p["side"] == "held-out"]

    def metrics(g, name):
        y, pr = g["y"].to_numpy(), g["p_fused"].to_numpy()
        return {"subset": name, "n": len(g),
                "recall_watch": round(float((g.groupby("event")["fused_warning"].apply(
                    lambda s: s.isin(["WATCH", "ALERT", "CRITICAL"]).any())).mean()), 4),
                "recall_alert": round(float((g.groupby("event")["fused_warning"].apply(
                    lambda s: s.isin(["ALERT", "CRITICAL"]).any())).mean()), 4),
                "recall_critical": round(float((g.groupby("event")["fused_warning"].apply(
                    lambda s: (s == "CRITICAL").any())).mean()), 4),
                "imminence_auc": round(float(roc_auc_score(y, pr)), 4),
                "imminence_pr": round(float(average_precision_score(y, pr)), 4),
                "brier7": round(float(np.mean((pr - y) ** 2)), 4)}

    m0sc = json.load(open(REPO / "runs" / "phase_v" / "m0" / "scorecard.json"))
    sc = {"heldout_m1": metrics(ho, "heldout-m1"), "dev_m1": metrics(dev, "dev-m1"),
          "heldout_m0": m0sc["heldout"], "dev_m0": m0sc["dev"]}
    json.dump(sc, open(OUTDIR / "m1_scorecard.json", "w"), indent=2)

    # rescue analysis on the 7 M0 held-out misses
    fails = json.load(open(REPO / "runs" / "phase_v" / "m0" / "failure_ledger.json"))
    rescue = []
    for f in fails:
        g = p[p["event"] == f["event"]].sort_values("grid_end")
        hit = g[g["fused_warning"].isin(["ALERT", "CRITICAL"])]
        if hit.empty:
            verdict = "NOT RESCUED"
            lead = None
        else:
            lead = int((pd.to_datetime(g["grid_end"].max()).date() - pd.to_datetime(
                hit["grid_end"].iloc[0]).date()).days)
            verdict = "RESCUED" if lead > 0 else "RESCUED-AT-T"
        rescue.append({"event": f["event"], "m0_mechanisms": f["mechanisms"],
                       "m1_first_alert": None if hit.empty else str(hit["grid_end"].iloc[0]),
                       "lead_d": lead, "verdict": verdict,
                       "dvv": float(g["s1_dvv_db"].iloc[0]),
                       "sat_evidence": str(g["sat_evidence"].iloc[0])})
    json.dump(rescue, open(OUTDIR / "rescue.json", "w"), indent=2)
    log(f"heldout M1 alert-recall={sc['heldout_m1']['recall_alert']} "
        f"(M0 {sc['heldout_m0']['recall_alert']}); "
        f"rescued={[r['event'] for r in rescue if r['verdict'].startswith('RESCUED')]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
