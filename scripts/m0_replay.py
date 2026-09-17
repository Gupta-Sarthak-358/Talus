"""V-C M0: frozen-system replay over V-B reconstructions. NO RETRAINING, NO TUNING.

Serving recipe (exact production path backend/app/sih26001_model.py):
  row -> encoder -> RF predict_proba (RAW) -> score=int(raw*100) -> FROZEN_BANDS
  -> warning state; confidence = isotonic CALIBRATED P; OOD via support.check
  (E16d: ood -> probability_status uncalibrated-ood, never silent low-risk).
Row assembly: V-B event dynamics+terrain; ndvi/distances/lulc/recent_disturbance
ride nearest training-row analogue (distance logged, E15 precedent); seismic from
COMMITTED usgs_quakes.json filtered < snapshot (dist/n50/years_since/rate).
Labels (declared constructs): y_imminent7 = snapshot in {T-7,T-3,T-1,T}.
Lead = event_date - first-warning grid_end (snapshot resolution).
Outputs runs/phase_v/m0/. Run: mnemo-venv python scripts/m0_replay.py
"""
from __future__ import annotations

import glob
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backend"))
RDIR = REPO / "runs" / "phase_v" / "daily_replay"
OUTDIR = REPO / "runs" / "phase_v" / "m0"
SPLIT = REPO / "splits" / "championship_split_v1.json"
LAT_SPLIT = 27.15

NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density", "seismic_dist_km", "seismic_n50_rate", "seismic_years_since",
           "recent_disturbance"]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def band(score: int) -> str:
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


def main() -> int:
    from app import support as _support
    blob = joblib.load(REPO / "ml/models/sih26001_rf_v1.joblib")
    model, enc = blob["model"], blob["encoder"]
    iso = joblib.load(REPO / "ml/models/sih26001_iso_v1.joblib")["isotonic"]
    mat = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    mlat, mlon = side["lat"].to_numpy(), side["lon"].to_numpy()
    quakes = json.load(open(REPO / "data/sih26001/evidence/usgs_quakes.json"))["events"]
    split = {r["slide_no"]: r["side"] for r in json.load(open(SPLIT))["events"]}
    track = pd.read_csv(REPO / "data/sih26001/evidence/trackA_candidates.csv")
    rec = {r["slide_no"]: bool("chronic" in str(r["event_identity"]).lower()
                               or "DISTINCT date" in str(r["event_identity"]))
           for _, r in track.iterrows()}

    rows = []
    for f in sorted(glob.glob(str(RDIR / "event_*.json"))):
        e = json.load(open(f, encoding="utf-8"))
        la, lo, ev = e["lat"], e["lon"], pd.Timestamp(e["event_date"]).date()
        ai = int(np.argmin(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(mlat - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(mlat))
            * np.sin(np.radians(mlon - lo) / 2) ** 2))))
        base = mat.iloc[ai]
        adist = float(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(mlat[ai] - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(mlat[ai]))
            * np.sin(np.radians(mlon[ai] - lo) / 2) ** 2)))
        for key, s in e["snapshots"].items():
            gd = pd.Timestamp(s["grid_end"]).date()
            feat = {"slope_angle": s["terrain"]["slope_deg"], "elevation": s["terrain"]["elevation_m"],
                    "aspect": s["terrain"]["aspect_deg"], "curvature": s["terrain"]["curvature"],
                    "twi": s["terrain"]["twi"], "spi_log": float(np.log1p(max(s["terrain"]["spi"], 0))),
                    "rainfall_24h_mm": s["rainfall_24h_mm"]["value"],
                    "rainfall_7d_mm": s["rainfall_7d_mm"]["value"],
                    "rainfall_30d_mm": s["rainfall_30d_mm"]["value"],
                    "soil_moisture": s["soil_moisture"]["value"],
                    "ndvi": float(base["ndvi"]), "distance_to_road": float(base["distance_to_road"]),
                    "distance_to_river": float(base["distance_to_river"]),
                    "drain_density": s["terrain"]["drain_density"],
                    "recent_disturbance": 0.0, "lulc": str(base["lulc"])}
            prior = [q for q in quakes if q["date"] < str(gd) and
                     2 * 6371.0 * np.arcsin(np.sqrt(
                         np.sin(np.radians(q["lat"] - la) / 2) ** 2 + np.cos(np.radians(la))
                         * np.cos(np.radians(q["lat"])) * np.sin(np.radians(q["lon"] - lo) / 2) ** 2)) <= 50.0]
            dall = [2 * 6371.0 * np.arcsin(np.sqrt(
                np.sin(np.radians(q["lat"] - la) / 2) ** 2 + np.cos(np.radians(la))
                * np.cos(np.radians(q["lat"])) * np.sin(np.radians(q["lon"] - lo) / 2) ** 2))
                for q in quakes if q["date"] < str(gd)]
            feat["seismic_dist_km"] = round(float(min(dall)) if dall else 999.0, 2)
            feat["seismic_n50_rate"] = round(len(prior) / max(gd.year - 1965, 1), 4)
            feat["seismic_years_since"] = min(gd.year - max([q["year"] for q in prior]), 60) if prior else 60
            ood = _support.check({**feat, "spi": s["terrain"]["spi"]})
            pr = float(model.predict_proba(enc.transform(pd.DataFrame([feat])))[0, 1])
            pc = float(iso.predict([pr])[0])
            sc, bd = int(round(pr * 100)), band(int(round(pr * 100)))
            rows.append({"event": e["slide_no"], "episode": e["episode"], "side": split[e["slide_no"]],
                         "snapshot": key, "grid_end": str(gd), "raw_score": sc, "band": bd,
                         "warning": STATE[bd], "p_cal": round(pc, 4),
                         "probability_status": "uncalibrated-ood" if ood["ood"] else "calibrated",
                         "ood": bool(ood["ood"]), "ood_reasons": ";".join(ood["ood_reasons"]),
                         "ge_op05": bool(pc >= 0.5), "soil_prov": s["soil_moisture"]["provenance"],
                         "analogue_m": round(adist, 1), "recurrent": rec.get(e["slide_no"], False),
                         "region": "SOUTH" if la < LAT_SPLIT else "NORTH"})
    p = pd.DataFrame(rows)
    assert len(p) == 138 and set(p["probability_status"]) <= {"calibrated", "uncalibrated-ood"}
    assert not ((p["ood"]) & (p["probability_status"] == "calibrated")).any(), "OOD invariant broken"
    OUTDIR.mkdir(parents=True, exist_ok=True)
    p.to_csv(OUTDIR / "predictions.csv", index=False)

    # trajectories + first warnings
    p["dt"] = pd.to_datetime(p["grid_end"])
    trajs, firsts = [], []
    for ev, g in p.groupby("event"):
        g = g.sort_values("dt")
        trajs.append({"event": ev, "side": g["side"].iloc[0],
                      **{f"{r['snapshot']}": f"{r['warning']}/{r['raw_score']}/{r['p_cal']}"
                         for _, r in g.iterrows()}})
        fw = {}
        for lvl, bands in (("WATCH", ["Moderate", "High", "Critical"]),
                           ("ALERT", ["High", "Critical"]), ("CRITICAL", ["Critical"])):
            hit = g[g["band"].isin(bands)]
            fw[lvl] = None if hit.empty else (hit["dt"].iloc[0].date().isoformat(),
                                              int((pd.Timestamp(g["grid_end"].max()).date()
                                                   - hit["dt"].iloc[0].date()).days))
        firsts.append({"event": ev, "side": g["side"].iloc[0], **fw})
    pd.DataFrame(trajs).to_csv(OUTDIR / "event_trajectories.csv", index=False)
    pd.DataFrame([{"event": f["event"], "side": f["side"],
                   "first_watch": (f["WATCH"] or [None, None])[0],
                   "lead_watch_d": (f["WATCH"] or [None, None])[1],
                   "first_alert": (f["ALERT"] or [None, None])[0],
                   "lead_alert_d": (f["ALERT"] or [None, None])[1],
                   "first_critical": (f["CRITICAL"] or [None, None])[0],
                   "lead_critical_d": (f["CRITICAL"] or [None, None])[1]} for f in firsts]).to_csv(
        OUTDIR / "first_warnings.csv", index=False)

    def metrics(g, name):
        from sklearn.metrics import roc_auc_score, average_precision_score
        y = g["snapshot"].isin(["T-7", "T-3", "T-1", "T"]).astype(int).to_numpy()
        pr = g["p_cal"].to_numpy()
        return {"subset": name, "n": len(g),
                "recall_watch": round(float((g.groupby("event")["warning"].apply(
                    lambda s: s.isin(["WATCH", "ALERT", "CRITICAL"]).any())).mean()), 4),
                "recall_alert": round(float((g.groupby("event")["warning"].apply(
                    lambda s: s.isin(["ALERT", "CRITICAL"]).any())).mean()), 4),
                "recall_critical": round(float((g.groupby("event")["warning"].apply(
                    lambda s: (s == "CRITICAL").any())).mean()), 4),
                "imminence_auc": round(float(roc_auc_score(y, pr)), 4),
                "imminence_pr": round(float(average_precision_score(y, pr)), 4),
                "brier7": round(float(np.mean((pr - y) ** 2)), 4)}

    scorecard = {"label_def": "y=1 iff snapshot in {T-7,T-3,T-1,T} (7-day imminence construct)",
                 "overall": metrics(p, "all"), "dev": metrics(p[p["side"] == "development"], "dev"),
                 "heldout": metrics(p[p["side"] == "held-out"], "heldout"),
                 "recurrent": metrics(p[p["recurrent"]], "recurrent"),
                 "novel": metrics(p[~p["recurrent"]], "novel"),
                 "north": metrics(p[p["region"] == "NORTH"], "north"),
                 "south": metrics(p[p["region"] == "SOUTH"], "south")}
    json.dump(scorecard, open(OUTDIR / "scorecard.json", "w"), indent=2)

    tb = json.load(open(REPO / "runs" / "e15_replay_audit.json")) if (REPO / "runs" / "e15_replay_audit.json").exists() else {}
    off = json.load(open(REPO / "runs" / "burden_offseason.json"))
    burden = {"note": "background burden from frozen-scorer band runs (same RF+iso+bands family)",
              "monsoon_TierB": tb.get("tier_b", tb.get("TierB", "see e15_replay_audit")),
              "offseason": off.get("summary"),
              "m0_event_hot_occupancy": {e: int((g["warning"].isin(["ALERT", "CRITICAL"])).sum())
                                        for e, g in p.groupby("event")}}
    json.dump(burden, open(OUTDIR / "burden.json", "w"), indent=2, default=str)

    oodr = {"n_ood_snapshots": int(p["ood"].sum()),
            "ood_events": sorted(p[p["ood"]]["event"].unique().tolist()),
            "invariant": "ood -> uncalibrated-ood holds on all 138 (asserted)"}
    json.dump(oodr, open(OUTDIR / "ood_report.json", "w"), indent=2)
    prov = {"soil_by_snapshot": p.groupby("soil_prov").size().to_dict(),
            "note": "full REAL/PROXY/MISSING in runs/phase_v/reconstruction_audit.json"}
    json.dump(prov, open(OUTDIR / "provenance_report.json", "w"), indent=2)

    fails = []
    for f in firsts:
        if f["side"] == "held-out" and f["ALERT"] is None:
            g = p[p["event"] == f["event"]]
            t = g[g["snapshot"] == "T"].iloc[0]
            mechs = []
            if t["ood"]:
                mechs.append("OOD-involved")
            if t["raw_score"] >= 75 and t["p_cal"] < 0.5:
                mechs.append("calibration-compression")
            if float(g[g["snapshot"] == "T"]["raw_score"].iloc[0]) < 65:
                mechs.append("low-raw-throughout")
            if f["event"] and rec.get(f["event"]):
                mechs.append("chronic-site")
            fails.append({"event": f["event"], "T_state": f"{t['warning']}/{t['raw_score']}/{t['p_cal']}",
                          "first_watch": f["WATCH"], "mechanisms": mechs or ["unexplained"],
                          "sar_available": "per V-B (138/138 SAR-backed usable)"})
    json.dump(fails, open(OUTDIR / "failure_ledger.json", "w"), indent=2)
    log(f"scored 138; heldout alert-recall={scorecard['heldout']['recall_alert']}; "
        f"failures={len(fails)}; ood_snaps={oodr['n_ood_snapshots']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
