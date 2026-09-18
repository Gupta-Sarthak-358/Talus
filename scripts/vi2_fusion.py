"""VI-2 fusion: frozen M0 base + LiCSAR coherence/phase features (H2 test).

Per-event SAR summary (frozen definitions): per frame recent unw median (mm),
trend = recent - baseline (mm), recent coherence (/255), coherence trend,
recent valid fraction, cross-geometry sign agreement. unw void -> NaN (XGB-native).
Model: XGB tiny (50xd2) on DEV ONLY (y=imminence7), isotonic on dev.
Bands: SAME FROZEN_BANDS edges (declared reuse). OOD carried from M0.
Held-out comparison + rescue on 7 M0 misses. No tuning, no satellite beyond LiCSAR.
Outputs runs/phase_v/vi2/. Run: mnemo-venv python scripts/vi2_fusion.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
M0 = REPO / "runs" / "phase_v" / "m0" / "predictions.csv"
SAR = REPO / "runs" / "phase_v" / "vi2" / "sar_features.json"
OUTDIR = REPO / "runs" / "phase_v" / "vi2"
SEED = 42
RAD2MM = 0.05546576 / (4 * np.pi) * 1000.0


def log(m: str) -> None:
    import time
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
FCOLS = ["p_cal", "unw_recent_mm", "unw_trend_mm", "cc_recent", "cc_trend",
         "unw_valid_frac", "geom_agree"]


def feat_for(pairs, frame_prefix):
    sel = [r for r in pairs if r["frame"].startswith(frame_prefix)]
    by = {r["slot"]: r for r in sel}
    out = {}
    for k in ("recent", "baseline"):
        r = by.get(k)
        if r and r["unw"].get("median") is not None:
            out[f"{k}_unw"] = r["unw"]["median"] * RAD2MM
            out[f"{k}_n"] = r["unw"]["n_valid"]
        else:
            out[f"{k}_unw"], out[f"{k}_n"] = np.nan, 0
        c = by.get(k)
        out[f"{k}_cc"] = c["cc"]["median"] if c and c["cc"].get("median") is not None else np.nan
    out["trend"] = out["recent_unw"] - out["baseline_unw"]
    out["cc_trend"] = out["recent_cc"] - out["baseline_cc"]
    return out


def main() -> int:
    from xgboost import XGBClassifier
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import roc_auc_score, average_precision_score

    p = pd.read_csv(M0)
    sar = json.load(open(SAR, encoding="utf-8"))
    rows = []
    for _, r in p.iterrows():
        v = sar[r["event"]]
        a = feat_for(v["pairs"], "048")
        b = feat_for(v["pairs"], "012")
        agree = int(np.sign(a["trend"]) == np.sign(b["trend"])) if all(
            np.isfinite([a["trend"], b["trend"]])) and a["trend"] != 0 and b["trend"] != 0 else 0
        rows.append({"unw_recent_mm": np.nanmean([a["recent_unw"], b["recent_unw"]]),
                     "unw_trend_mm": np.nanmean([a["trend"], b["trend"]]),
                     "cc_recent": np.nanmean([a["recent_cc"], b["recent_cc"]]),
                     "cc_trend": np.nanmean([a["cc_trend"], b["cc_trend"]]),
                     "unw_valid_frac": np.nanmean([a["recent_n"] / 121.0, b["recent_n"] / 121.0]),
                     "geom_agree": agree})
    f = pd.DataFrame(rows)
    for c in FCOLS:
        if c != "p_cal":
            p[c] = f[c].to_numpy()
    p["y"] = p["snapshot"].isin(["T-7", "T-3", "T-1", "T"]).astype(int)
    dev0, _ho0 = p[p["side"] == "development"], p[p["side"] == "held-out"]
    clf = XGBClassifier(n_estimators=50, max_depth=2, learning_rate=0.1, subsample=0.9,
                        random_state=SEED, n_jobs=2, eval_metric="logloss")
    clf.fit(dev0[FCOLS].to_numpy(dtype=float), dev0["y"].to_numpy())
    iso = IsotonicRegression(out_of_bounds="clip").fit(
        clf.predict_proba(dev0[FCOLS].to_numpy(dtype=float))[:, 1], dev0["y"].to_numpy())
    p["p_fused"] = iso.predict(clf.predict_proba(p[FCOLS].to_numpy(dtype=float))[:, 1]).round(4)
    p["fused_score"] = (p["p_fused"] * 100).round(0).astype(int)
    p["fused_band"] = p["fused_score"].apply(band)
    p["fused_warning"] = p["fused_band"].map(STATE)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p.to_csv(OUTDIR / "vi2_predictions.csv", index=False)
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

    m0sc = json.load(open(REPO / "runs/phase_v/m0/scorecard.json"))
    sc = {"heldout_vi2": metrics(ho, "heldout-vi2"), "dev_vi2": metrics(dev, "dev-vi2"),
          "heldout_m0": m0sc["heldout"]}
    json.dump(sc, open(OUTDIR / "vi2_scorecard.json", "w"), indent=2)
    fails = json.load(open(REPO / "runs/phase_v/m0/failure_ledger.json"))
    rescue = []
    for fl in fails:
        g = p[p["event"] == fl["event"]].sort_values("grid_end")
        hit = g[g["fused_warning"].isin(["ALERT", "CRITICAL"])]
        if hit.empty:
            verdict, lead, first = "NOT RESCUED", None, None
        else:
            lead = int((pd.to_datetime(g["grid_end"].max()).date() - pd.to_datetime(
                hit["grid_end"].iloc[0]).date()).days)
            verdict, first = ("RESCUED" if lead > 0 else "RESCUED-AT-T"), str(hit["grid_end"].iloc[0])
        rescue.append({"event": fl["event"], "m0_mechanisms": fl["mechanisms"],
                       "first_alert": first, "lead_d": lead, "verdict": verdict})
    json.dump(rescue, open(OUTDIR / "rescue.json", "w"), indent=2)
    log(f"heldout VI-2 alert-recall={sc['heldout_vi2']['recall_alert']} "
        f"(M0 {sc['heldout_m0']['recall_alert']}) auc={sc['heldout_vi2']['imminence_auc']} "
        f"brier={sc['heldout_vi2']['brier7']}")
    log("rescue: " + str([(r["event"], r["verdict"], r["lead_d"]) for r in rescue]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
