"""E16d: OOD boundary experiment (SIH26001).

For held-out plains events (+ Tier-1 in-domain cases + training positives):
per-feature support position vs training-positive distribution, Mahalanobis
distance, kNN feature-space distance, geographic distance — each vs p_raw/p_cal.
Validates the abstention rule (>=2 features outside p1-p99 bands) BEFORE it ships:
flag rate must be high out-of-regime, low in-domain.
Outputs: runs/e16d.json + data/sih26001/evidence/feature_support.json (committed).
Run: mnemo-venv python scripts/e16d_ood_boundary.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "runs" / "e16d.json"
SUPPORT = REPO / "data/sih26001/evidence/feature_support.json"

NUMERIC = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
           "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
           "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
           "drain_density", "seismic_dist_km", "seismic_n50_rate",
           "seismic_years_since"]
FEATS = [c for c in NUMERIC if c != "spi_log"] + ["spi"]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def build_X(mat: pd.DataFrame) -> pd.DataFrame:
    X = mat[["slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
             "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
             "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
             "drain_density", "seismic_dist_km", "seismic_n50_rate",
             "seismic_years_since", "lulc"]].copy()
    X["spi_log"] = np.log1p(X["spi"].clip(lower=0))
    return X.drop(columns=["spi"])


def main() -> int:
    from scipy.spatial.distance import cdist
    m0 = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    s0 = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    h = pd.read_csv(REPO / "runs" / "e16c_features.csv")
    hs = pd.read_csv(REPO / "runs" / "e16c_sidecar.csv")
    e16c = json.loads((REPO / "runs" / "e16c_full.json").read_text(encoding="utf-8"))
    hscores = {e["slide_no"]: (e["p_raw"] if "p_raw" in e else None) for e in e16c["events"]}

    pos = m0[m0["event"] == 1].reset_index(drop=True)
    P = pos[FEATS].copy()
    P["spi_log"] = np.log1p(P["spi"].clip(lower=0))
    P = P.drop(columns=["spi"])
    mu, sd = P[NUMERIC].mean().to_numpy(), P[NUMERIC].std().to_numpy()

    bands = {c: [round(float(P[c].quantile(0.01)), 4), round(float(P[c].quantile(0.99)), 4)]
             for c in NUMERIC}
    # regularized covariance for Mahalanobis (Ledoit-Wolf-free: diagonal load 1e-3)
    Zp = ((P[NUMERIC].to_numpy() - mu) / sd)
    cov = np.cov(Zp.T) + 1e-3 * np.eye(len(NUMERIC))
    inv = np.linalg.inv(cov)
    # Tier-1 in-domain reference: analogue rows from replay bundle
    bundle = json.loads((REPO / "data/sih26001/evidence/replay_series.json").read_text(encoding="utf-8"))
    summ = json.loads((REPO / "data/sih26001/evidence/counterfactual_summary.json").read_text(encoding="utf-8"))
    t1_rows = [c["terrain_analogue_row"] for c in summ["cases"]]

    blob = joblib.load(REPO / "ml/models/sih26001_rf_v1.joblib")
    model, enc = blob["model"], blob["encoder"]

    def score_df(df: pd.DataFrame) -> np.ndarray:
        X = build_X(df)
        if "recent_disturbance" not in X.columns:
            X["recent_disturbance"] = 0.0  # E8-removed; const satisfies encoder schema
        return model.predict_proba(enc.transform(X))[:, 1]

    def feats_of(df: pd.DataFrame) -> pd.DataFrame:
        F = df[FEATS].copy()
        F["spi_log"] = np.log1p(F["spi"].clip(lower=0))
        return F.drop(columns=["spi"])

    def describe(df: pd.DataFrame, tag: str) -> list:
        F = feats_of(df)
        Z = ((F[NUMERIC].to_numpy() - mu) / sd)
        mahal = np.sqrt(np.einsum("ij,jk,ik->i", Z, inv, Z))
        knn = np.sort(cdist(Z, Zp), axis=1)[:, 4]  # 5th-nearest training positive
        oob = [int(((F[c] < bands[c][0]) | (F[c] > bands[c][1])).sum()) for c in NUMERIC]
        oob_count = np.array([[int((row[c] < bands[c][0]) or (row[c] > bands[c][1])) for c in NUMERIC]
                              for _, row in F.iterrows()]).sum(axis=1)
        pr = score_df(df)
        out = []
        for i in range(len(df)):
            out.append({"mahal": round(float(mahal[i]), 2), "knn5": round(float(knn[i]), 2),
                        "oob_count": int(oob_count[i]),
                        "oob_features": [c for c in NUMERIC
                                         if float(F[c].iloc[i]) < bands[c][0] or float(F[c].iloc[i]) > bands[c][1]],
                        "p_raw": round(float(pr[i]), 4)})
        log(f"{tag}: mahal_med {np.median(mahal):.2f} knn5_med {np.median(knn):.2f} "
            f"oob>=2 frac {np.mean(oob_count >= 2):.2f} p_raw_med {np.median(pr):.3f}")
        return out

    res: dict = {}
    res["heldout"] = describe(h, "heldout-plains")
    # in-domain references: Tier-1 analogues (training rows) + random training positives
    ana = m0[m0["zone_id"].isin(t1_rows)].reset_index(drop=True)
    res["tier1_analogues"] = describe(ana, "tier1-analogues")
    rng = np.random.default_rng(42)
    samp = pos.iloc[rng.choice(len(pos), 200, replace=False)].reset_index(drop=True)
    res["trainpos_sample"] = describe(samp, "trainpos-sample")

    # correlations over held-out: distance vs scores
    hh = np.array([d["mahal"] for d in res["heldout"]])
    kk = np.array([d["knn5"] for d in res["heldout"]])
    pp = np.array([d["p_raw"] for d in res["heldout"]])
    from scipy.stats import spearmanr
    res["correlation"] = {
        "mahal_vs_p_raw": round(float(spearmanr(hh, pp).statistic), 3),
        "knn5_vs_p_raw": round(float(spearmanr(kk, pp).statistic), 3)}
    log(f"spearman mahal-p_raw {res['correlation']['mahal_vs_p_raw']}, "
        f"knn5-p_raw {res['correlation']['knn5_vs_p_raw']}")

    # rule validation: >=2 OOB features
    def flagrate(rows):
        return round(float(np.mean([r["oob_count"] >= 2 for r in rows])), 3)
    res["rule_ge2_oob"] = {"heldout": flagrate(res["heldout"]),
                           "tier1_analogues": flagrate(res["tier1_analogues"]),
                           "trainpos_sample": flagrate(res["trainpos_sample"])}
    log(f"rule>=2 OOB flag rate: {res['rule_ge2_oob']}")

    SUPPORT.write_text(json.dumps({
        "method": "p1-p99 bands over 1468 training positives (E16d); abstention rule: >=2 OOB features",
        "n_pos": len(pos), "bands": bands,
        "standardizer": {"mean": [round(float(v), 4) for v in mu],
                         "std": [round(float(v), 4) for v in sd]},
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=1), encoding="utf-8")
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT} + {SUPPORT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
