"""Live SIH26001 susceptibility scoring for the demo pilot (12 NGEN rows).

Loads the Phase-1 trained artifacts (ml/models/sih26001_rf_v1.joblib +
sih26001_iso_v1.joblib, git-ignored) and scores the frozen NGEN sample rows
(data/sih26001/fixtures/feature_matrix.sample.csv) through the SAME recipe
as scripts/train_sih26001.py: 14 base cols, spi -> spi_log, encoder
transform, RF predict_proba, isotonic calibration.

Contract:
- score = int(round(raw_proba * 100)); confidence = calibrated P (0-1 float,
  same scale as the fixture confidences the frontend already handles);
  band via model_service.band_for_score.
- Weights absent (fresh clone) or any failure -> return None per zone and
  the caller keeps frozen fixture scores. NEVER fabricate: live_scores is
  True only when every served zone scored cleanly.
- SHAP is optional (shap lib may be absent where the server runs); caller
  keeps the fixture-SHAP fallback.
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
             "drain_density"]


def _valid_row(row: dict) -> bool:
    try:
        for c in BASE_COLS:
            v = float(row[c])
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
        rec = {c: float(row[c]) for c in BASE_COLS}
        rec["lulc"] = str(row["lulc"]).strip()
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
            score = int(round(p * 100))
            from . import model_service
            return {"score": score, "confidence": round(cal, 3),
                    "band": model_service.band_for_score(score),
                    "raw_proba": round(p, 4)}
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
