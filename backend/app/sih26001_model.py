"""Live SIH26001 susceptibility scoring for the demo pilot (12 NGEN rows).

Loads the Phase-1 trained artifacts (ml/models/sih26001_rf_v1.joblib +
sih26001_iso_v1.joblib, git-ignored) and scores the frozen NGEN sample rows
(data/sih26001/fixtures/feature_matrix.sample.csv) through the SAME recipe
 as scripts/train_sih26001.py: 14 base cols (+3 seismic-memory when the
bundle was trained with them), spi -> spi_log, encoder transform, RF
predict_proba, isotonic calibration.

Contract:
- score = int(round(raw_proba * 100)); confidence = calibrated P (0-1 float,
  same scale as the fixture confidences the frontend already handles);
  band via model_service.band_for_score.
- Weights absent (fresh clone) or any failure -> return None per zone and
  the caller keeps frozen fixture scores. NEVER fabricate: live_scores is
  True only when every served zone scored cleanly.
- SHAP is optional (shap lib may be absent where the server runs); caller
  keeps the fixture-SHAP fallback.
- Seismic-memory cols (17-feature bundle): per-zone as-of-2024 values resolved
  from the committed evidence/usgs_quakes.json + fixture geometries at import.
  Documented demo-pilot approximation (fixture NGEN rows carry no seismic cols);
  per-row seismic arrives with the NGEN refresh. Encoder mismatch (old 14-col
  bundle) -> score_row returns None per zone (honest fallback, never crash).
"""
from __future__ import annotations

import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RF_BLOB = REPO / "ml" / "models" / "sih26001_rf_v1.joblib"
ISO_BLOB = REPO / "ml" / "models" / "sih26001_iso_v1.joblib"

BASE_COLS = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
             "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
             "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
             "drain_density", "recent_disturbance"]
SEISMIC_COLS = ["seismic_dist_km", "seismic_n50_rate", "seismic_years_since"]
QUAKES_FP = REPO / "data" / "sih26001" / "evidence" / "usgs_quakes.json"
_SLOPES_FPS = [REPO / "data" / "sih26001" / "fixtures" / f for f in
               ("slopes.json", "slopes.lachung.json", "slopes.darjeeling.json",
                "slopes.arunachal.json", "slopes.assam.json", "slopes.manipur.json",
                "slopes.meghalaya.json", "slopes.mizoram.json")]


def _seismic_lookup() -> dict[str, dict[str, float]]:
    """Per-zone as-of-2024 seismic values from committed quake table + geometries."""
    import json
    import math as _math
    try:
        quakes = json.loads(QUAKES_FP.read_text(encoding="utf-8"))["events"]
    except Exception:
        return {}
    zones: dict[str, tuple[float, float]] = {}
    for fp in _SLOPES_FPS:
        try:
            for z in json.loads(fp.read_text(encoding="utf-8"))["zones"]:
                zones[z["zone_id"]] = (float(z["geometry"]["lat"]),
                                       float(z["geometry"]["lon"]))
        except Exception:
            continue
    out: dict[str, dict[str, float]] = {}
    for zid, (la, lo) in zones.items():
        best_d, n50, last_yr = math.inf, 0, None
        for q in quakes:
            d = 2 * 6371.0 * _math.asin(_math.sqrt(
                _math.sin(_math.radians(q["lat"] - la) / 2) ** 2
                + _math.cos(_math.radians(la)) * _math.cos(_math.radians(q["lat"]))
                * _math.sin(_math.radians(q["lon"] - lo) / 2) ** 2))
            best_d = min(best_d, d)
            if d <= 50.0 and q["year"] < 2024:
                n50 += 1
                last_yr = q["year"] if last_yr is None else max(last_yr, q["year"])
        out[zid] = {"seismic_dist_km": round(best_d, 2),
                    # rate = count / observable years (2024-1965 = 59 for all demo zones)
                    "seismic_n50_rate": round(n50 / 59.0, 4),
                    "seismic_years_since": float(min(2024 - last_yr, 60)) if last_yr else 60.0}
    return out


_SEISMIC_BY_ZONE = _seismic_lookup()


def _valid_row(row: dict) -> bool:
    try:
        for c in BASE_COLS:
            # recent_disturbance is new 18th col — sample.csv 12 rows have no col, default 0 (wound 4/2936)
            if c == "recent_disturbance" and c not in row:
                continue
            v = float(row.get(c, 0))
            if not math.isfinite(v):
                return False
        if not str(row.get("lulc", "")).strip():
            return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


class Sih26001Live:
    def __init__(self) -> None:
        import joblib
        import pandas as pd  # noqa: F401 (ensures pandas present for encoder)
        rf_blob = joblib.load(RF_BLOB)
        iso_blob = joblib.load(ISO_BLOB)
        self.model = rf_blob["model"]
        self.encoder = rf_blob["encoder"]
        self.iso = iso_blob["isotonic"]
        self.trained_features = list(rf_blob.get("features", []))

    def _frame(self, row: dict):
        import pandas as pd
        rec = {c: float(row.get(c, 0)) for c in BASE_COLS}
        rec["lulc"] = str(row["lulc"]).strip()
        # Seismic cols: prefer row values (WhatIf/future NGEN rows); else the
        # committed as-of-2024 per-zone lookup (documented approximation).
        if all(c in row for c in SEISMIC_COLS):
            for c in SEISMIC_COLS:
                rec[c] = float(row[c])
        else:
            seis = _SEISMIC_BY_ZONE.get(str(row.get("zone_id", ""))) if _SEISMIC_BY_ZONE else None
            if not seis:
                # Pending NER states fallback — conservative 60km/0/60 (no nearby M5.5 <50km)
                seis = {"seismic_dist_km": 60.0, "seismic_n50_rate": 0.0, "seismic_years_since": 60.0}
            rec.update(seis)
        X = pd.DataFrame([rec])
        X["spi_log"] = X["spi"].clip(lower=0).apply(lambda v: math.log1p(v))
        X = X.drop(columns=["spi"])
        return X

    def score_row(self, row: dict) -> dict | None:
        """Score one NGEN sample row; None if anything is off (caller falls back)."""
        if not _valid_row(row):
            return None
        try:
            Xn = self.encoder.transform(self._frame(row))
            p = float(self.model.predict_proba(Xn)[0][1])
            if not math.isfinite(p):
                return None
            p = min(max(p, 0.0), 1.0)
            cal = float(self.iso.predict([p])[0])
            cal = min(max(cal, 0.0), 1.0)
            # Prevalence-corrected confidence for ~1% field base rate (Bayes)
            # pi_train=0.5 (balanced matrix) -> pi_real=0.01 (NER hillslope-day)
            # p_real = p_cal*0.02 / (p_cal*0.02 + (1-p_cal)*1.98)
            p_real = cal * 0.02 / (cal * 0.02 + (1 - cal) * 1.98) if 0 < cal < 1 else cal
            p_real = min(max(float(p_real), 0.0), 1.0)
            score = int(round(p * 100))
            from . import model_service
            from . import support as _support
            ood = _support.check(row)
            return {"score": score, "confidence": round(cal, 3),
                    "confidence_real_1pct": round(p_real, 4),
                    "band": model_service.band_for_score(score),
                    "raw_proba": round(p, 4),
                    "ood": ood["ood"], "ood_reasons": ood["ood_reasons"],
                    "probability_status": ("uncalibrated-ood" if ood["ood"]
                                           else "calibrated")}
        except Exception:
            return None

    def explain_row(self, row: dict, top_k: int = 4) -> dict | None:
        """Real TreeSHAP contributions for one row; None if shap unavailable."""
        try:
            import shap
        except Exception:
            return None
        if not _valid_row(row):
            return None
        try:
            Xn = self.encoder.transform(self._frame(row))
            explainer = shap.TreeExplainer(self.model)
            sv = explainer.shap_values(Xn)
            if isinstance(sv, list):
                sv = sv[1] if len(sv) > 1 else sv[0]
            import numpy as np
            sv = np.atleast_2d(sv)[0]
            try:
                names = [n.split("__")[-1] for n in self.encoder.get_feature_names_out()]
            except Exception:
                names = self.trained_features or [f"f{i}" for i in range(len(sv))]
            pairs = sorted(zip(names, [float(v) for v in sv]),
                           key=lambda kv: -abs(kv[1]))[:top_k]
            base = explainer.expected_value
            if not isinstance(base, float):
                try:
                    base = float(np.asarray(base).ravel()[1])
                except Exception:
                    base = float(np.asarray(base).ravel()[0])
            return {"base_value": round(float(base), 2),
                    "contributions": [{"feature": k, "shap_value": round(float(v), 2)}
                                      for k, v in pairs]}
        except Exception:
            return None


_live: Sih26001Live | None = None
_live_attempted = False


def get_live() -> Sih26001Live | None:
    """Singleton; None when weights are absent (fresh clone -> fixture mode)."""
    global _live, _live_attempted
    if _live is None and not _live_attempted:
        _live_attempted = True
        try:
            if RF_BLOB.exists() and ISO_BLOB.exists():
                _live = Sih26001Live()
                print(f"[sih26001] live RF+isotonic loaded ({RF_BLOB.name})")
            else:
                print("[sih26001] weights absent -> fixture scoring (honest fallback)")
        except Exception as exc:  # noqa: BLE001
            print(f"[sih26001] live load failed ({exc}) -> fixture scoring")
            _live = None
    return _live


def reset_live_flag() -> None:
    global _live, _live_attempted
    _live, _live_attempted = None, False
