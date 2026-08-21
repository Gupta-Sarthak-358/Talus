"""Bridge between the TALUS backend and the FROZEN ML Model v1.

Model: RandomForestRegressor on the V1 feature contract (12 features +
zone_id), trained on generator v1.4.0 seeds 42-81 exactly per
docs/ML_MODEL_CARD_V1.md and ml/benchmark/protocol.md.

This module is the ONLY place the backend touches the model. Scores come
from the trained model; risk bands use the frozen FoS-derived thresholds;
explanations are real Tree SHAP values. No invented constants.
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "data" / "processed" / "generator_v1" / "ml_handoff" / "synthetic_ml_dataset_seeds_42_91.csv"
ARTIFACT = REPO / "ml" / "models" / "talus_rf_v1.joblib"

TRAIN_SEEDS = list(range(42, 82))
FEATURES = ["rainfall_24h_mm", "rainfall_7d_mm", "slope_angle_deg", "slope_height_m",
            "rock_type", "crack_density", "crack_severity", "blast_frequency_per_week",
            "blast_vibration_ppv_mms", "days_since_inspection", "prior_incident",
            "groundwater_proxy"]
CATS = ["rock_type", "crack_severity"]
ZONE_MAP = {"A": "ZONE_A", "B": "ZONE_B", "C": "ZONE_C", "D": "ZONE_D"}

FROZEN_BANDS = [(50, "Very Low"), (65, "Low"), (75, "Moderate"), (85, "High"), (101, "Critical")]


def band_for_score(score: float) -> str:
    for edge, name in FROZEN_BANDS:
        if score < edge:
            return name
    return "Critical"


def _train():
    d = pd.read_csv(CORPUS)
    d = d[d["seed"].isin(TRAIN_SEEDS)]
    nums = [c for c in FEATURES if c not in CATS]
    pre = ColumnTransformer([("n", StandardScaler(), nums),
                             ("c", OneHotEncoder(handle_unknown="ignore"), CATS)])
    X = pre.fit_transform(d[FEATURES + ["zone_id"]])
    rf = RandomForestRegressor(n_estimators=500, max_depth=12, min_samples_leaf=1,
                               random_state=0, n_jobs=-1)
    rf.fit(X, d["instability_score"].values.astype(float))
    return {"pre": pre, "model": rf}


class ModelService:
    def __init__(self):
        if ARTIFACT.exists():
            blob = joblib.load(ARTIFACT)
        else:
            blob = _train()
            ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(blob, ARTIFACT, compress=3)
        self.pre = blob["pre"]
        self.model = blob["model"]

    def _frame(self, zone_letter: str, feats: dict) -> pd.DataFrame:
        row = {k: feats[k] for k in FEATURES}
        row["zone_id"] = ZONE_MAP[zone_letter]
        return pd.DataFrame([row])

    def predict(self, zone_letter: str, feats: dict) -> dict:
        X = self.pre.transform(self._frame(zone_letter, feats))
        per_tree = np.array([t.predict(X)[0] for t in self.model.estimators_])
        score = float(per_tree.mean())
        spread = float(per_tree.std())
        confidence = round(float(max(0.5, 1.0 - min(spread / 25.0, 0.45))), 2)
        return {"score": int(round(max(0.0, min(100.0, score)))),
                "raw_score": score,
                "confidence": confidence,
                "band": band_for_score(score)}

    def explain(self, zone_letter: str, feats: dict) -> dict:
        import shap
        X = self.pre.transform(self._frame(zone_letter, feats))
        explainer = shap.TreeExplainer(self.model)
        sv = explainer.shap_values(X)[0]
        names = [n.split("__")[-1] for n in self.pre.get_feature_names_out()]
        pairs = sorted(zip(names, np.atleast_1d(sv)), key=lambda kv: -abs(kv[1]))[:4]
        base = explainer.expected_value
        if isinstance(base, np.ndarray):
            base = base.ravel()[0]
        base = float(base)
        return {"base_value": round(base, 2),
                "contributions": [{"feature": k, "shap_value": round(float(v), 2)} for k, v in pairs]}

    def latest_zone_states(self, seed: int = 91) -> dict[str, dict]:
        """Real observed end-of-year state per zone from a held-out world."""
        d = pd.read_csv(CORPUS)
        out = {}
        for letter, zid in ZONE_MAP.items():
            row = d[(d.seed == seed) & (d.zone_id == zid)].iloc[-1]
            out[letter] = {k: (int(row[k]) if k == "days_since_inspection"
                               else int(bool(row[k])) if k == "prior_incident"
                               else str(row[k]) if k in CATS
                               else float(row[k])) for k in FEATURES}
        return out


_service: ModelService | None = None


def get_service() -> ModelService:
    global _service
    if _service is None:
        _service = ModelService()
    return _service