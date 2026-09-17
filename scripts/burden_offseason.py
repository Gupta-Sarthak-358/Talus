"""Off-season background burden (SIH26001 Phase IV-C).

60 background windows (30 S + 30 N, seed 43 = fresh sample) x 31 days in
Nov-Feb (non-monsoon), band pipeline (prod RF+iso, FROZEN_BANDS) — same warning
definition as E15 Tier-B monsoon run. Compares monsoon vs off-season burden.
Outputs: runs/burden_offseason.json. Run: mnemo-venv python scripts/burden_offseason.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "runs" / "burden_offseason.json"

SEED = 43
LAT_SPLIT = 27.15
OFF_MONTHS = [(2023, 11), (2023, 12), (2024, 1), (2024, 2)]


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


def main() -> int:
    import joblib
    import counterfactual_past_events as CPE
    blob = joblib.load(REPO / "ml/models/sih26001_rf_v1.joblib")
    model, enc = blob["model"], blob["encoder"]
    iso = joblib.load(REPO / "ml/models/sih26001_iso_v1.joblib")["isotonic"]
    mat = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    y = mat["event"].to_numpy().astype(int)
    rng = np.random.default_rng(SEED)
    bg = np.where(y == 0)[0]
    lat_all = side["lat"].to_numpy()
    pick = np.concatenate([rng.choice(bg[lat_all[bg] < LAT_SPLIT], 30, replace=False),
                           rng.choice(bg[lat_all[bg] >= LAT_SPLIT], 30, replace=False)])
    RAIN_CACHE: dict = {}

    def imd_window(year, lat0, lon0, d0, d1):
        import xarray as xr
        key = (year, round(lat0, 2), round(lon0, 2))
        if key not in RAIN_CACHE:
            ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{year}_rfp25.nc"))
            s = ds.RAINFALL.sel(LATITUDE=lat0, LONGITUDE=lon0, method="nearest")
            vals = pd.Series(np.asarray(s.sel(TIME=slice("2023-01-01", "2024-12-31")).values, dtype=float),
                             index=pd.to_datetime(s.sel(TIME=slice("2023-01-01", "2024-12-31")).TIME.values))
            RAIN_CACHE[key] = vals.fillna(0.0)
            ds.close()
        return RAIN_CACHE[key]

    res: dict = {"windows": []}
    for i in pick:
        la, lo = float(side["lat"].iloc[i]), float(side["lon"].iloc[i])
        yr, mo = OFF_MONTHS[int(rng.integers(0, len(OFF_MONTHS)))]
        d0 = pd.Timestamp(f"{yr}-{mo:02d}-01")
        base = mat.iloc[i]
        hot = 0
        top = "NORMAL"
        for day in pd.date_range(d0, d0 + pd.Timedelta(days=30), freq="D"):
            ds_ = day.strftime("%Y-%m-%d")
            w = imd_window(yr, la, lo, "", ds_)
            sw = w.loc[:ds_]
            feat = {k: base[k] for k in CPE.NUMERIC if k != "spi_log"}
            feat["spi_log"] = float(np.log1p(max(base["spi"], 0)))
            feat.update({"rainfall_24h_mm": round(float(sw.iloc[-1]), 1),
                         "rainfall_7d_mm": round(float(sw.iloc[-7:].sum()), 1),
                         "rainfall_30d_mm": round(float(sw.iloc[-30:].sum()), 1),
                         "lulc": base["lulc"], "recent_disturbance": 0.0})
            pr = float(model.predict_proba(enc.transform(pd.DataFrame([feat])))[0, 1])
            pc = float(iso.predict([pr])[0])
            b = band(round(pc * 100, 1))
            if b in ("High", "Critical"):
                hot += 1
                top = b if top != "Critical" else top
        res["windows"].append({"zone": base["zone_id"],
                               "region": "SOUTH" if la < LAT_SPLIT else "NORTH",
                               "window": d0.strftime("%Y-%m"), "hot_days": hot, "top": top})
    n = len(res["windows"])
    res["summary"] = {
        "frac_any_hot": round(float(np.mean([w["hot_days"] > 0 for w in res["windows"]])), 3),
        "mean_hot_days": round(float(np.mean([w["hot_days"] for w in res["windows"]])), 1),
        "monsoon_reference": {"frac_any_hot": 28 / 60, "mean_hot_days": 5.8,
                              "note": "E15 Tier-B, same band pipeline, monsoon windows"}}
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"off-season: {res['summary']['frac_any_hot']} any-hot, mean {res['summary']['mean_hot_days']} "
        f"vs monsoon 0.467/5.8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
