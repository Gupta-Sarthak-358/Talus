"""Tiny SHAP microservice — load model once, explain one row per request.

Isolates the ~250MB TreeExplainer from the main API so both fit Render free 512MB.
Endpoint: POST /explain  { zone_id, features: {...} }  -> { base_value, contributions, shap_provenance }
Health: GET /health
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

REPO = Path(__file__).resolve().parents[1]
RF_BLOB = REPO / "ml" / "models" / "sih26001_rf_v1.joblib"
ISO_BLOB = REPO / "ml" / "models" / "sih26001_iso_v1.joblib"

app = FastAPI(title="TALUS SHAP Service", version="1.0")

_live = None
_explainer = None


def _get_live():
    global _live, _explainer
    if _live is not None:
        return _live, _explainer
    import joblib
    import shap
    if not RF_BLOB.exists() or not ISO_BLOB.exists():
        raise RuntimeError("weights missing")
    rf_blob = joblib.load(RF_BLOB)
    _live = rf_blob
    # Build explainer once — single row later, no background dataset
    _explainer = shap.TreeExplainer(rf_blob["model"])
    return _live, _explainer


@app.get("/health")
def health():
    ok = RF_BLOB.exists() and ISO_BLOB.exists()
    return {"status": "ok" if ok else "missing_weights", "model": str(RF_BLOB.name)}


@app.post("/explain")
def explain(payload: dict):
    zone_id = payload.get("zone_id", "S1")
    features = payload.get("features") or payload
    if not isinstance(features, dict):
        raise HTTPException(status_code=422, detail="features must be an object")
    try:
        live, explainer = _get_live()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    # Reuse backend's framing without importing the whole app (avoid circular heavy imports)
    # Minimal reimplementation: BASE_COLS + seismic lookup + spi_log + encoder transform
    try:
        import math
        import json

        BASE_COLS = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
                     "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
                     "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
                     "drain_density", "recent_disturbance"]
        SEISMIC_COLS = ["seismic_dist_km", "seismic_n50_rate", "seismic_years_since"]
        QUAKES_FP = REPO / "data" / "sih26001" / "evidence" / "usgs_quakes.json"
        import math as _math
        # Seismic lookup (same as sih26001_model._seismic_lookup, but inline)
        quakes = []
        try:
            quakes = json.loads(QUAKES_FP.read_text(encoding="utf-8"))["events"]
        except Exception:
            pass
        # Resolve zone centroid if seismic cols missing
        if not all(c in features for c in SEISMIC_COLS):
            # Try slopes fixtures for centroid
            lat = lon = None
            for fn in ("slopes.json", "slopes.lachung.json", "slopes.darjeeling.json",
                       "slopes.arunachal.json", "slopes.assam.json", "slopes.manipur.json",
                       "slopes.meghalaya.json", "slopes.mizoram.json"):
                try:
                    import json as _j
                    for z in _j.loads((REPO / f"data/sih26001/fixtures/{fn}").read_text(encoding="utf-8"))["zones"]:
                        if z["zone_id"] == zone_id:
                            lat, lon = float(z["geometry"]["lat"]), float(z["geometry"]["lon"])
                            break
                    if lat is not None:
                        break
                except Exception:
                    continue
            if lat is not None and quakes:
                best, n50, last = math.inf, 0, None
                for q in quakes:
                    d = 2*6371.0*_math.asin(_math.sqrt(
                        _math.sin(_math.radians(q["lat"]-lat)/2)**2
                        + _math.cos(_math.radians(lat))*_math.cos(_math.radians(q["lat"]))
                        * _math.sin(_math.radians(q["lon"]-lon)/2)**2))
                    best = min(best, d)
                    if d <= 50.0 and q["year"] < 2024:
                        n50 += 1
                        last = q["year"] if last is None else max(last, q["year"])
                features = {**features,
                            "seismic_dist_km": round(best,2),
                            "seismic_n50_rate": round(n50/59.0,4),
                            "seismic_years_since": float(min(2024-last,60)) if last else 60.0}
            else:
                features = {**features, "seismic_dist_km": 60.0, "seismic_n50_rate": 0.0, "seismic_years_since": 60.0}

        import pandas as pd
        rec = {c: float(features.get(c, 0)) for c in BASE_COLS}
        rec["lulc"] = str(features.get("lulc", "FOREST")).strip() or "FOREST"
        for c in SEISMIC_COLS:
            rec[c] = float(features.get(c, 0))
        X = pd.DataFrame([rec])
        X["spi_log"] = X["spi"].clip(lower=0).apply(lambda v: math.log1p(v))
        X = X.drop(columns=["spi"])
        Xn = live["encoder"].transform(X)
        sv = explainer.shap_values(Xn)
        if isinstance(sv, list):
            sv = sv[1] if len(sv) > 1 else sv[0]
        import numpy as np
        sv = np.asarray(sv)
        if sv.ndim == 3:
            sv = sv[:, :, 1] if sv.shape[2] > 1 else sv[:, :, 0]
        sv = np.atleast_2d(sv)[0]
        try:
            names = [n.split("__")[-1] for n in live["encoder"].get_feature_names_out()]
        except Exception:
            names = live.get("features", []) or [f"f{i}" for i in range(len(sv))]
        pairs = sorted(zip(names, [float(v) for v in sv]), key=lambda kv: -abs(kv[1]))[:4]
        base = explainer.expected_value
        if not isinstance(base, float):
            try:
                base = float(np.asarray(base).ravel()[1])
            except Exception:
                base = float(np.asarray(base).ravel()[0])
        return {
            "zone_id": zone_id,
            "base_value": round(float(base), 2),
            "contributions": [{"feature": k, "shap_value": round(float(v), 2)} for k, v in pairs],
            "shap_provenance": "live",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
