import json
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
SCRATCH = r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe"
d = pd.read_csv(f"{SCRATCH}\\seeds_42_116.csv")
d["seed"] = d["seed"].astype(int)

print("=== 1. test-world comparability: 87-91 vs 112-116 ===")
for name, seeds in [("test 87-91 (50-seed study)", range(87, 92)), ("test 112-116 (75-seed study)", range(112, 117))]:
    t = d[d.seed.isin(list(seeds))]
    print(f"{name}: mean={t.instability_score.mean():.1f} std={t.instability_score.std():.1f} "
          f"bands={t.risk_label.value_counts().to_dict()}")

print("\n=== 2. apples-to-apples: same test 112-116, train 40 vs 65 seeds ===")
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from lightgbm import LGBMRegressor
from config import FEATURES, CATEGORICAL_FEATURES

te = d[d.seed.isin(range(112, 117))].reset_index(drop=True)
yte = te["instability_score"].values.astype(float)
nums = [c for c in FEATURES if c not in CATEGORICAL_FEATURES]
cats = CATEGORICAL_FEATURES + ["zone_id"]
for ntrain, tag in [(40, "42-81"), (65, "42-106")]:
    tr = d[d.seed.isin(range(42, 42 + ntrain))].reset_index(drop=True)
    pre = ColumnTransformer([("n", StandardScaler(), nums), ("c", OneHotEncoder(handle_unknown="ignore"), cats)])
    pre.fit(tr[FEATURES + ["zone_id"]])
    m = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=6,
                      random_state=0, n_jobs=-1, verbose=-1)
    m.fit(pre.transform(tr[FEATURES + ["zone_id"]]), ytr := tr["instability_score"].values.astype(float))
    p = m.predict(pre.transform(te[FEATURES + ["zone_id"]]))
    from sklearn.metrics import r2_score
    print(f"train {tag} ({ntrain} seeds) -> test 112-116: R2={r2_score(yte, p):.3f}")

print("\n=== 3. transition frequency across ALL 75 worlds ===")
cross_strict, cross_loose, band_changes = 0, 0, 0
for (s, z), g in d.groupby(["seed", "zone_id"], sort=False):
    fos = g["fos"].values
    labels = g["risk_label"].astype(str).values
    band_changes += int((labels[1:] != labels[:-1]).sum())
    for t in range(31, len(fos)):
        if fos[t] < 1.0 and fos[t - 1] >= 1.0:
            cross_loose += 1
            if fos[t - 30:t].min() >= 1.2:
                cross_strict += 1
print(f"day-scale FoS>=1.0 -> <1.0 crossings (loose): {cross_loose}")
print(f"after >=30 stable days >=1.2 (strict): {cross_strict}")
print(f"risk_label changes between consecutive days: {band_changes}")

print("\n=== 4. per-zone band spread (how pinned are zones?) ===")
piv = d.pivot_table(index="zone_id", columns="risk_label", values="instability_score",
                    aggfunc="count", fill_value=0)
print(piv.to_string())

r = json.load(open(f"{SCRATCH}\\extended_study_results.json", encoding="utf-8"))
print("\n=== 5. classification per-class detail (lightgbm) ===")
pc = r["B_classification"]["lightgbm"]["per_class"]
for k, v in pc.items():
    print(f"{k:10s} P={v['precision']:.3f} R={v['recall']:.3f} F1={v['f1']:.3f} support={v['support']}")