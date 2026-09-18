"""VI-2 ablation: base-only vs sat-only vs full (diagnostic, same protocol)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from pathlib import Path
REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    p = pd.read_csv(REPO / "runs/phase_v/vi2/vi2_predictions.csv")
    dev = p[p.side == "development"]
    ho = p[p.side == "held-out"]
    satcols = ["unw_recent_mm", "unw_trend_mm", "cc_recent", "cc_trend",
               "unw_valid_frac", "geom_agree"]
    for cols, tag in [(["p_cal"], "base-only"), (satcols, "sat-only"),
                      (["p_cal"] + satcols, "full")]:
        clf = XGBClassifier(n_estimators=50, max_depth=2, learning_rate=0.1,
                            subsample=0.9, random_state=42, n_jobs=2, eval_metric="logloss")
        Xd = dev[cols].to_numpy(dtype=float)
        yd = dev["y"].to_numpy()
        clf.fit(Xd, yd)
        iso = IsotonicRegression(out_of_bounds="clip").fit(
            clf.predict_proba(Xd)[:, 1], yd)
        ph = iso.predict(clf.predict_proba(ho[cols].to_numpy(dtype=float))[:, 1])
        yh = ho["y"].to_numpy()
        rall = float((ho.assign(pf=ph).groupby("event")["pf"].apply(
            lambda s: (s * 100 >= 75).any())).mean())
        print(f"{tag} alert-recall={rall:.2f} auc={roc_auc_score(yh, ph):.3f} "
              f"brier={np.mean((ph - yh) ** 2):.4f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
