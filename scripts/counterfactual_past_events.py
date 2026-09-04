"""Retrospective counterfactuals: what would Talus have said before past Sikkim slides?

Method (honest, reproducible — see docs/EVIDENCE_TALUS_COUNTERFACTUALS.md):
  For each dated, rainfall-triggered inventory/news event E at site S on date D:
  1. Static terrain features = nearest training-matrix row to S (documented
     analogue; haversine distance logged). Soil/NDVI/LULC/OSM ride from that
     row (quasi-static proxies — logged, same pedigree as the pilot).
  2. Rainfall 24h/7d/30d = ACTUAL trailing sums from the repo's own IMD
     0.25-degree archive (data/raw/imd/indYYYY_rfp25.nc), nearest cell to S,
     recomputed for each day in [D-14, D].
  3. Saved RF (ml/models/sih26001_rf_v1.joblib) + fitted encoder + isotonic
     calibrator -> daily P(event). Score = P*100; bands = backend FROZEN_BANDS
     (<50 Very Low, <65 Low, <75 Moderate, <85 High, else Critical).
  4. First-crossing dates for Moderate/High/Critical -> lead time vs D.

Never invented: rainfall (IMD archive), terrain (training matrix), model
(frozen bundle), band edges (backend), impact facts (cited news/Govt).

Outputs (git-ignored scratch + committed summary):
  data/sih26001/processed/counterfactual_*.csv (daily P per case)
  data/sih26001/evidence/counterfactual_summary.json (COMMITTED)

Run: py scripts/counterfactual_past_events.py (needs sklearn/pandas/xarray)
"""
from __future__ import annotations

import datetime
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[1]
NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density"]

CASES = [
    {
        "id": "mangan-jun2024",
        "title": "Mangan district disaster, 12-13 June 2024",
        "site": (27.51, 88.53),
        "site_name": "Mangan town (Pakshep/Ambhithang slide cluster)",
        "event_date": "2024-06-13",
        "event_note": "Slide nights of June 12-13; 9 dead statewide (6 Mangan + 3 Namchi Jun 10); "
                      "~1,500-2,000 tourists stranded; NH-10 blocked, North Sikkim isolated; "
                      "Mangan station >220 mm/24h (IMD); red alert only on Jun 13.",
        "sources": ["Reuters 2024-06-14", "Indian Express 2024-06-13", "HT 2024-06-13",
                    "ET 2024-06-15", "livemint 2024-06-16 (IMD red-alert text)"],
    },
    {
        "id": "dipudara-aug2024",
        "title": "Dipudara (Teesta-V) slide, 20 Aug 2024 07:30",
        "site": (27.2525, 88.4606),
        "site_name": "Dipudara, Balutar, Singtam-Dikchu road (SI/GAN/78A07/2024/48)",
        "event_date": "2024-08-20",
        "event_note": "GIS building of 510 MW Teesta-V destroyed; 6 houses damaged; "
                      "Singtam-Dikchu road cut. ZERO casualties ONLY because 7 days of "
                      "precursor slides triggered manual evacuation (Sikkim Govt PR 20-Aug-2024).",
        "sources": ["sikkim.gov.in PR 20-Aug-2024", "The Hindu 2024-08-20", "Indian Express 2024-08-20",
                    "Down To Earth 2024-08-20/24", "SANDRP 2024-08-21 (coords 27.2515, 88.4594)"],
    },
    {
        "id": "lumsay-jun2022",
        "title": "Lumsay Slide, Adampul road, June 2022 (month-known)",
        "site": (27.32633333, 88.59544444),
        "site_name": "Lumsay Slide (SKM/Gangtok/78A11/2022), ~1.1 km from S3 Tadong",
        "event_date": "2022-06-30",
        "event_date_fuzzy": "month-only in GSI report; analysed against the wettest June spell, flagged",
        "event_note": "Debris slide on Adampul road; site later selected for the National Landslide "
                      "Mitigation Project (SSDMA/NDMA consultation Jan 2026) — chronic hazard. "
                      "June 2022 also killed 5 statewide with 40 vehicles stranded in North Sikkim (HT 17-Jun-2022).",
        "sources": ["GSI landslide_report.pdf p675 (Sl.26787)", "HT 2022-06-17", "Sikkim Chronicle 2026-01-08"],
    },
    {
        "id": "sichey-jun2021",
        "title": "Sichey house-burial, ~8 June 2021 (date-fuzzy)",
        "site": (27.33787, 88.609377),
        "site_name": "Sichey near Tamang Gumpa, Gangtok (Upper Sichey slide footprint)",
        "event_date": "2021-06-08",
        "event_date_fuzzy": "article 09-Jun-2021 reports slide 'around 7 PM' after 'last few days' of heavy rain; analysed at 08-Jun, flagged",
        "event_note": "Landslide buried a house kitchen at ~7 PM; 1 dead (40-yr woman), 70-yr mother injured; "
                      "Gangtok water project damaged -> city water crisis; NH-31A commuters stranded 4 hrs. "
                      "Same Upper Sichey footprint that slid again 31-Jul-2025.",
        "sources": ["The Sikkim Today 2021-06-09", "Sikkim NOW May-2011 (Upper Sichey chronic slides, 8cm rain precedent)"],
    },
    {
        "id": "nh10-oct2022",        "title": "NH-10 19/20 Mile blockade, 9 Oct 2022",
        "site": (27.13, 88.51),
        "site_name": "NH-10 19/20 Mile, Singtam-Rangpo (14th Mile one-way, 32 Mile blocked)",
        "event_date": "2022-10-09",
        "event_note": "Boulders jammed NH-10 at 19/20 Mile + 32 Mile; Sikkim cut off from India; "
                      "hundreds stranded 3+ hrs; 200 tourists stranded statewide by Oct 12; "
                      "Rateychu pipeline burst -> Greater Gangtok water crisis. Post-monsoon (October) case.",
        "sources": ["Economic Times 2022-10-09", "IndiaTodayNE 2022-10-09", "The Hindu 2022-10-12",
                    "Outlook 2022-10-12", "HT 2022-10-13 (600+ rescued, IMD red alert had been issued)"],
    },
]


def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def band(score):
    if score < 50:
        return "Very Low"
    if score < 65:
        return "Low"
    if score < 75:
        return "Moderate"
    if score < 85:
        return "High"
    return "Critical"


def nearest_row(lat, lon, mat, side):
    dlat = np.radians(side["lat"].to_numpy() - lat)
    dlon = np.radians(side["lon"].to_numpy() - lon)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat)) * np.cos(np.radians(side["lat"].to_numpy())) * np.sin(dlon / 2) ** 2
    d = 2 * 6371000.0 * np.arcsin(np.sqrt(a))
    j = int(np.argmin(d))
    return j, round(float(d[j]), 1)


def imd_series(year, lat, lon, d0, d1):
    import xarray as xr
    ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{year}_rfp25.nc"))
    s = ds.RAINFALL.sel(LATITUDE=lat, LONGITUDE=lon, method="nearest")
    cell = (round(float(s.LATITUDE), 2), round(float(s.LONGITUDE), 2))
    vals = pd.Series(np.asarray(s.sel(TIME=slice(d0, d1)).values, dtype=float),
                     index=pd.to_datetime(s.sel(TIME=slice(d0, d1)).TIME.values))
    ds.close()
    return vals, cell


def main():
    rf = joblib.load(str(REPO / "ml/models/sih26001_rf_v1.joblib"))
    iso = joblib.load(str(REPO / "ml/models/sih26001_iso_v1.joblib"))["isotonic"]
    model, enc = rf["model"], rf["encoder"]
    mat = pd.read_csv(str(REPO / "data/sih26001/processed/feature_matrix.training.csv"))
    side = pd.read_csv(str(REPO / "data/sih26001/processed/training_sidecar.csv"))
    dyn_fp = REPO / "data/sih26001/processed/counterfactual_dynamic.json"
    dyn = json.loads(dyn_fp.read_text())["cases"] if dyn_fp.exists() else {}
    if dyn:
        log("dynamic inputs loaded (soil daily 2024 cases; NDVI pre-event scenes)")
    else:
        log("WARNING: no dynamic-inputs file — all non-rainfall inputs quasi-static")
    outdir = REPO / "data/sih26001/processed"
    summary = {"generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "model": "ml/models/sih26001_rf_v1.joblib + isotonic (frozen bundle)",
               "bands": "<50 Very Low, <65 Low, <75 Moderate, <85 High, else Critical (backend FROZEN_BANDS)",
               "cases": []}
    for c in CASES:
        lat, lon = c["site"]
        D = pd.Timestamp(c["event_date"])
        j, dist_m = nearest_row(lat, lon, mat, side)
        base = mat.iloc[j]
        analogue_in_training_as_positive = bool(base["event"] == 1)
        log(f"{c['id']}: analogue row {base.zone_id} ({base.lulc}, {dist_m:.0f} m away), "
            f"event {c['event_date']}" + (" [FUZZY DATE]" if c.get("event_date_fuzzy") else ""))
        rain, cell = imd_series(D.year, lat, lon,
                                (D - pd.Timedelta(days=45)).strftime("%Y-%m-%d"),
                                D.strftime("%Y-%m-%d"))
        rain = rain.fillna(0.0)
        dcase = dyn.get(c["id"], {})
        dsoil = (dcase.get("soil") or {})
        dndvi = dcase.get("ndvi")
        soil_src = ("daily CCI " + str(dcase.get("soil_meta", {}).get("cell"))
                    if dsoil else "matrix quasi-static (no 2024 zip coverage)" if not dcase else "matrix quasi-static")
        ndvi_src = ("S2 " + str((dcase.get("ndvi_meta") or {}).get("date"))
                    if dndvi is not None else "matrix quasi-static")
        rows = []
        for day in pd.date_range(D - pd.Timedelta(days=30), D, freq="D"):
            ds_ = day.strftime("%Y-%m-%d")
            w = rain.loc[:ds_]
            r24 = float(w.iloc[-1])
            r7 = float(w.iloc[-7:].sum()) if len(w) >= 7 else float(w.sum())
            r30 = float(w.iloc[-30:].sum()) if len(w) >= 30 else float(w.sum())
            feat = {k: base[k] for k in NUMERIC if k != "spi_log"}
            feat["spi_log"] = float(np.log1p(max(base["spi"], 0)))
            feat.update({"rainfall_24h_mm": round(r24, 1), "rainfall_7d_mm": round(r7, 1),
                         "rainfall_30d_mm": round(r30, 1),
                         "soil_moisture": dsoil.get(ds_, base["soil_moisture"]) if dsoil.get(ds_) is not None else base["soil_moisture"],
                         "ndvi": dndvi if dndvi is not None else base["ndvi"],
                         "lulc": base["lulc"]})
            X = pd.DataFrame([feat])
            p_raw = float(model.predict_proba(enc.transform(X))[0, 1])
            p_cal = float(iso.predict([p_raw])[0])
            score = round(p_cal * 100, 1)
            rows.append({"date": day.strftime("%Y-%m-%d"), "rain_24h": round(r24, 1),
                         "rain_7d": round(r7, 1), "rain_30d": round(r30, 1),
                         "soil_moisture": feat["soil_moisture"], "ndvi": feat["ndvi"],
                         "p_raw": round(p_raw, 4), "p_cal": round(p_cal, 4),
                         "score": score, "band": band(score)})
        df = pd.DataFrame(rows)
        df.to_csv(outdir / f"counterfactual_{c['id']}.csv", index=False)
        first = {}
        for level, thr in [("Moderate", 65), ("High", 75), ("Critical", 85)]:
            hit = df[df.score >= thr]
            first[level] = (hit.iloc[0]["date"], float(hit.iloc[0]["score"])) if len(hit) else (None, None)
        peak = df.loc[df.score.idxmax()]
        summary["cases"].append({
            "id": c["id"], "title": c["title"], "site": c["site_name"],
            "event_date": c["event_date"],
            "event_date_fuzzy": c.get("event_date_fuzzy"),
            "event_note": c["event_note"], "sources": c["sources"],
            "terrain_analogue_row": base.zone_id, "analogue_distance_m": dist_m,
            "analogue_lulc": base.lulc,
            "analogue_was_training_positive": analogue_in_training_as_positive,
            "soil_source": soil_src,
            "ndvi_source": ndvi_src,
            "ndvi_value": dndvi if dndvi is not None else round(float(base["ndvi"]), 3),
            "imd_cell": list(cell),
            "first_moderate": {"date": first["Moderate"][0], "score": first["Moderate"][1]},
            "first_high": {"date": first["High"][0], "score": first["High"][1]},
            "first_critical": {"date": first["Critical"][0], "score": first["Critical"][1]},
            "peak": {"date": peak["date"], "score": float(peak["score"]), "band": peak["band"]},
            "event_day": df[df.date == c["event_date"]].iloc[0].to_dict() if c["event_date"] in set(df.date) else None,
        })
        fc = first["Critical"][0] or first["High"][0] or first["Moderate"][0]
        log(f"  -> first High/Critical: High {first['High'][0]} / Critical {first['Critical'][0]}; "
            f"peak {peak['score']} ({peak['band']}) on {peak['date']}")
    with open(REPO / "data/sih26001/evidence/counterfactual_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    log("summary -> data/sih26001/evidence/counterfactual_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
