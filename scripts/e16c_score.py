"""E16c scoring: frozen prod RF + deterministic G-south iso on held-out rows (SIH26001).

Iso refit mirrors E15 (corrected pool, south rows, prod raw) so the calibrator is
identical by construction. Bands = backend FROZEN_BANDS; E14 south op point 0.5
recorded alongside (matrix-regime, for comparison — regime-mismatch caveat applies).
Outputs: runs/e16c_full.json. Run: mnemo-venv python scripts/e16c_score.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "runs" / "e16c_full.json"
LAT_SPLIT = 27.15


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def band_of(score: float) -> str:
    if score < 50:
        return "Very Low"
    if score < 65:
        return "Low"
    if score < 75:
        return "Moderate"
    if score < 85:
        return "High"
    return "Critical"


def build_X(mat: pd.DataFrame) -> pd.DataFrame:
    X = mat[["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
             "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
             "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
             "drain_density", "seismic_dist_km", "seismic_n50_rate",
             "seismic_years_since", "lulc"]].copy()
    X["spi_log"] = np.log1p(X["spi"].clip(lower=0))
    return X.drop(columns=["spi"])


def main() -> int:
    from sklearn.isotonic import IsotonicRegression
    m0 = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    s0 = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    exm, exs = [], []
    for tag in ("e15", "e15c"):
        mm = pd.read_csv(REPO / "data/sih26001/processed" / f"{tag}_negatives.csv")
        ss = pd.read_csv(REPO / "data/sih26001/processed" / f"{tag}_sidecar.csv")
        keep = (mm["distance_to_road"] < 1000).to_numpy()
        exm.append(mm[keep])
        exs.append(ss[keep])
    mat = pd.concat([m0] + exm, ignore_index=True)
    side = pd.concat([s0] + exs, ignore_index=True)
    y = mat["event"].to_numpy().astype(int)
    X = build_X(mat)
    lat = side["lat"].to_numpy()
    south = ((side["district"] == "Darjeeling").to_numpy()
             | ((side["district"] == "background").to_numpy() & (lat < LAT_SPLIT)))

    blob = joblib.load(REPO / "ml/models/sih26001_rf_v1.joblib")
    model, enc = blob["model"], blob["encoder"]

    def score_raw(df: pd.DataFrame) -> np.ndarray:
        full = df.copy()
        if "recent_disturbance" not in full.columns:
            full["recent_disturbance"] = 0.0
        return model.predict_proba(enc.transform(full))[:, 1]

    s_idx = np.where(south)[0]
    iso_s = IsotonicRegression(out_of_bounds="clip").fit(score_raw(X.iloc[s_idx]), y[s_idx])

    h = pd.read_csv(REPO / "runs" / "e16c_features.csv")
    hs = pd.read_csv(REPO / "runs" / "e16c_sidecar.csv")
    assert (hs["lat"] < LAT_SPLIT).all(), "pilot must be southern for G-south iso"
    Xh = build_X(h)
    if "recent_disturbance" not in Xh.columns:
        Xh["recent_disturbance"] = 0.0
    p_raw = model.predict_proba(enc.transform(Xh))[:, 1]
    p_cal = iso_s.predict(p_raw)
    scores = np.round(p_cal * 100, 1)
    bands = [band_of(s) for s in scores]

    # analogue distance to nearest training row (in or out of study)
    tlat, tlon = side["lat"].to_numpy(), side["lon"].to_numpy()
    res: dict = {"events": []}
    for i, row in h.iterrows():
        la, lo = float(hs["lat"].iloc[i]), float(hs["lon"].iloc[i])
        d = 2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(tlat - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(tlat))
            * np.sin(np.radians(tlon - lo) / 2) ** 2))
        j = int(np.argmin(d))
        res["events"].append({
            "slide_no": hs["slide_no"].iloc[i], "year": int(hs["year"].iloc[i]),
            "lat": la, "lon": lo,
            "p_raw": round(float(p_raw[i]), 4), "p_cal": round(float(p_cal[i]), 4),
            "score": round(float(scores[i]), 1), "band": bands[i],
            "ge_e14_op05": bool(p_cal[i] >= 0.5),
            "analogue_row": side["zone_id"].iloc[j], "analogue_dist_m": round(float(d[j]), 1),
            "analogue_event": int(y[j])})
    n = len(res["events"])
    n_alert = sum(1 for e in res["events"] if e["band"] in ("High", "Critical"))
    n_op = sum(1 for e in res["events"] if e["ge_e14_op05"])
    res["summary"] = {"n": n, "recall_band_high_plus": round(n_alert / n, 3),
                      "recall_e14_op05": round(n_op / n, 3),
                      "tier2_south_alert_reference": 0.836,
                      "verdict": ("held-out recall within noise of in-sample Tier-2 south "
                                  if abs(n_alert / n - 0.836) <= 0.2 else
                                  "held-out recall materially below Tier-2 south")}
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"held-out: {n_alert}/{n} band>=High, {n_op}/{n} E14-op2177; Tier-2 south ref 0.836")
    for e in res["events"]:
        log(f"  {e['slide_no']} {e['year']}: score {e['score']} [{e['band']}] "
            f"op05={e['ge_e14_op05']} analogue {e['analogue_row']}@{e['analogue_dist_m']}m(ev={e['analogue_event']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
