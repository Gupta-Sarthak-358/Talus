"""Extended-data study: 75 synthetic worlds (seeds 42-116). Temp work only.

The 50-world benchmark stays FROZEN as primary. This corpus answers:
  A. regression at larger coverage (same frozen configs, no retuning)
  B. classification at scale (macro F1, balanced acc, per-class, CM, critical recall)
  C. full transfer curve N in {5,10,20,40,65} (pretrained vs scratch)
  D. extreme-event transition detection (lead time on deterioration crossings)

Splits (seed-intact): train 42-106 (65), validation 107-111 (5), test 112-116 (5).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (f1_score, balanced_accuracy_score, confusion_matrix,
                             precision_recall_fscore_support)
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from lightgbm import LGBMRegressor, LGBMClassifier

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
from generator_v1 import build_timeline, build_internal_state, project_ml
from instability.sampler import fos_slope, instability_score

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
from config import FEATURES, CATEGORICAL_FEATURES

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SCRATCH = Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe")
CORPUS75 = SCRATCH / "seeds_42_116.csv"
OUT = SCRATCH / "extended_study_results.json"
SEED = 0
np.random.seed(SEED)
torch.manual_seed(SEED)

TRAIN_SEEDS = list(range(42, 107))
VAL_SEEDS = list(range(107, 112))
TEST_SEEDS = list(range(112, 117))
LABELS = ["very_low", "low", "moderate", "high", "critical"]

RES = {"splits": {"train": f"42-106 (65)", "val": "107-111", "test": "112-116"},
       "generator": "frozen v1.4.0", "runs": {}}


def generate_corpus():
    if CORPUS75.exists():
        return pd.read_csv(CORPUS75)
    frames = []
    t0 = time.time()
    for seed in range(42, 117):
        tl = build_timeline("2024-01-01", 365)
        df = build_internal_state(tl, seed)
        ml = project_ml(df)
        ml["zone_id"] = df["zone_id"].astype(str)
        for c in ["fos", "instability_score", "risk_label"]:
            ml[c] = df[c]
        ml["seed"] = seed
        frames.append(ml)
    d = pd.concat(frames, ignore_index=True)
    d.to_csv(CORPUS75, index=False)
    print(f"corpus: {len(d)} rows ({time.time()-t0:.0f}s)", flush=True)
    return d


def metrics_reg(y, p):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    return {"mae": float(mean_absolute_error(y, p)),
            "rmse": float(np.sqrt(mean_squared_error(y, p))),
            "r2": float(r2_score(y, p))}


def load_parts(d):
    base = d[d.seed.isin(TRAIN_SEEDS)].groupby("zone_id").agg(
        baseline_inst=("instability_score", "min"), baseline_fos=("fos", "max")).reset_index()
    d = d.merge(base, on="zone_id", how="left")
    d["delta_instability"] = d["instability_score"] - d["baseline_inst"]
    d["delta_fos"] = d["fos"] - d["baseline_fos"]
    tr = d[d.seed.isin(TRAIN_SEEDS)].reset_index(drop=True)
    va = d[d.seed.isin(VAL_SEEDS)].reset_index(drop=True)
    te = d[d.seed.isin(TEST_SEEDS)].reset_index(drop=True)
    return tr, va, te


def encoders(tr):
    nums = [c for c in FEATURES if c not in CATEGORICAL_FEATURES]
    cats = CATEGORICAL_FEATURES + ["zone_id"]
    pre = ColumnTransformer([("n", StandardScaler(), nums),
                             ("c", OneHotEncoder(handle_unknown="ignore"), cats)])
    pre.fit(tr[FEATURES + ["zone_id"]])
    return pre


# ------------------------------------------------------------- A. regression ----
def part_a(tr, va, te, pre):
    out = {}
    Xtr = pre.transform(tr[FEATURES + ["zone_id"]])
    Xva = pre.transform(va[FEATURES + ["zone_id"]])
    Xte = pre.transform(te[FEATURES + ["zone_id"]])
    for tname, ycol in [("abs_instability", "instability_score"),
                        ("delta_instability", "delta_instability"),
                        ("delta_fos", "delta_fos")]:
        ytr, yva, yte = tr[ycol].values.astype(float), va[ycol].values.astype(float), te[ycol].values.astype(float)
        block = {}
        lgbm = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=6,
                             random_state=SEED, n_jobs=-1, verbose=-1)
        lgbm.fit(Xtr, ytr)
        block["lightgbm"] = metrics_reg(yte, lgbm.predict(Xte))
        rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=SEED, n_jobs=-1)
        rf.fit(Xtr, ytr)
        block["random_forest"] = metrics_reg(yte, rf.predict(Xte))
        out[tname] = block
        print(f"[A] {tname}: lgbm R2={block['lightgbm']['r2']:.3f} rf R2={block['random_forest']['r2']:.3f}", flush=True)
    RES["A_regression"] = out


# --------------------------------------------------------- B. classification ----
def part_b(tr, va, te, pre):
    Xtr = pre.transform(tr[FEATURES + ["zone_id"]])
    Xte = pre.transform(te[FEATURES + ["zone_id"]])
    ytr = tr["risk_label"].astype(str).values
    yte = te["risk_label"].astype(str).values
    out = {}
    for name, clf in [
        ("dummy_mostfreq", None),
        ("random_forest", RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                                 class_weight="balanced", random_state=SEED, n_jobs=-1)),
        ("lightgbm", LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=6,
                                    class_weight="balanced", random_state=SEED, n_jobs=-1, verbose=-1)),
    ]:
        if clf is None:
            maj = pd.Series(ytr).value_counts().index[0]
            pred = np.full(len(yte), maj)
        else:
            clf.fit(Xtr, ytr)
            pred = clf.predict(Xte)
        pr, rec, f1, supp = precision_recall_fscore_support(yte, pred, labels=LABELS, zero_division=0)
        cm = confusion_matrix(yte, pred, labels=LABELS)
        out[name] = {
            "macro_f1": float(f1_score(yte, pred, average="macro", zero_division=0)),
            "balanced_acc": float(balanced_accuracy_score(yte, pred)),
            "accuracy": float((yte == pred).mean()),
            "critical_recall": float(rec[LABELS.index("critical")]),
            "per_class": {LABELS[i]: {"precision": round(float(pr[i]), 3), "recall": round(float(rec[i]), 3),
                                      "f1": round(float(f1[i]), 3), "support": int(supp[i])} for i in range(5)},
            "confusion_matrix": cm.tolist(),
        }
        print(f"[B] {name}: macroF1={out[name]['macro_f1']:.3f} balAcc={out[name]['balanced_acc']:.3f} "
              f"critRecall={out[name]['critical_recall']:.3f}", flush=True)
    RES["B_classification"] = out
    RES["B_train_class_counts"] = {k: int(v) for k, v in tr["risk_label"].value_counts().items()}


# ------------------------------------------------------- C. transfer curve ----
class MLP(nn.Module):
    def __init__(self, din):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(din, 256), nn.GELU(), nn.Dropout(0.15),
                                 nn.Linear(256, 128), nn.GELU(), nn.Dropout(0.15),
                                 nn.Linear(128, 64), nn.GELU(), nn.Linear(64, 1))

    def forward(self, x):
        return self.net(x).squeeze(-1)


ROCK_PARAMS = {
    "lateritic_soil": ((588, 883), (18, 30), (1.98, 2.10)),
    "clayey_sandstone": ((29, 157), (25, 40), (2.00, 2.40)),
    "variegated_sandy_clay": ((245, 981), (15, 35), (1.90, 2.30)),
    "sandstone": ((29, 157), (25, 40), (2.00, 2.40)),
}
ZONES = ["ZONE_A", "ZONE_B", "ZONE_C", "ZONE_D"]
SEVS = ["normal", "minor", "moderate", "severe", "critical"]


def sample_source(n):
    rock = np.random.choice(list(ROCK_PARAMS), n)
    c = np.array([np.random.uniform(*ROCK_PARAMS[r][0]) for r in rock])
    phi = np.array([np.random.uniform(*ROCK_PARAMS[r][1]) for r in rock])
    gamma = np.array([np.random.uniform(*ROCK_PARAMS[r][2]) for r in rock])
    h = np.random.uniform(2.0, 40.0, n)
    theta = np.random.uniform(10.0, 75.0, n)
    face = np.random.uniform(35.0, 90.0, n)
    proxy = np.exp(np.random.uniform(np.log(0.5), np.log(250.0), n))
    wf = np.random.rand(n) < np.clip(proxy / 150.0, 0.05, 0.9)
    dens = np.random.uniform(0.05, 2.0, n)
    sev = np.random.choice(SEVS, n)
    fos = fos_slope(c, phi, gamma, h, theta, proxy, wf, dens, sev, face)
    ok = np.isfinite(fos)
    return pd.DataFrame({
        "rainfall_24h_mm": np.exp(np.random.uniform(np.log(0.1), np.log(120.0), n)) * ok,
        "rainfall_7d_mm": np.exp(np.random.uniform(np.log(0.5), np.log(400.0), n)) * ok,
        "slope_angle_deg": theta, "slope_height_m": h, "rock_type": rock,
        "crack_density": dens, "crack_severity": sev,
        "blast_frequency_per_week": np.random.uniform(0, 28, n),
        "blast_vibration_ppv_mms": np.where(np.random.rand(n) < 0.3, np.exp(np.random.uniform(np.log(1.0), np.log(80.0), n)), 0.0),
        "days_since_inspection": np.random.randint(0, 30, n),
        "prior_incident": np.zeros(n, dtype=bool),
        "groundwater_proxy": proxy, "zone_id": np.random.choice(ZONES, n),
        "instability_score": np.round(instability_score(fos), 1)})[ok]


def train_es(model, Xtr, ytr, Xva, yva, lr, max_ep, patience, bs=512):
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    lossf = nn.MSELoss()
    Xt, yt = torch.tensor(Xtr, device=DEVICE), torch.tensor(ytr, device=DEVICE)
    Xv = torch.tensor(Xva, device=DEVICE)
    best, state, wait, ep_ok = 1e18, None, 0, 0
    for ep in range(max_ep):
        model.train()
        perm = torch.randperm(len(Xt), device=DEVICE)
        for i in range(0, len(perm), bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            lossf(model(Xt[idx]), yt[idx]).backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            pv = model(Xv).cpu().numpy()
        rm = float(np.sqrt(mean_squared_error(yva, pv)))
        if rm < best - 1e-5:
            best, wait, ep_ok = rm, 0, ep
            state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= patience:
                break
    model.load_state_dict(state)
    return ep_ok + 1


from sklearn.metrics import mean_squared_error


def part_c(d, tr, va, te, pre):
    src = sample_source(120_000)
    pre_src = ColumnTransformer([("n", StandardScaler(), [c for c in FEATURES if c not in CATEGORICAL_FEATURES]),
                                 ("c", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES + ["zone_id"])])
    pre_src.fit(src[FEATURES + ["zone_id"]])
    Xsrc = pre_src.transform(src[FEATURES + ["zone_id"]]).astype(np.float32)
    net = MLP(Xsrc.shape[1]).to(DEVICE)
    train_es(net, Xsrc, src["instability_score"].values.astype(np.float32),
             pre_src.transform(va[FEATURES + ["zone_id"]]).astype(np.float32),
             va["instability_score"].values.astype(np.float32), lr=1e-3, max_ep=80, patience=8)
    curve = {}
    Xte_all = pre.transform(te[FEATURES + ["zone_id"]])
    yte = te["instability_score"].values.astype(float)
    for N in [5, 10, 20, 40, 65]:
        sub = d[d.seed.isin(list(range(42, 42 + N)))].reset_index(drop=True)
        ysub = sub["instability_score"].values.astype(np.float32)
        Xsub = pre.transform(sub[FEATURES + ["zone_id"]]).astype(np.float32)
        Xva_e = pre.transform(va[FEATURES + ["zone_id"]]).astype(np.float32)
        yva_e = va["instability_score"].values.astype(np.float32)

        m_s = MLP(Xsub.shape[1]).to(DEVICE)
        train_es(m_s, Xsub, ysub, Xva_e, yva_e, lr=1e-3, max_ep=200, patience=15)
        m_s.eval()
        with torch.no_grad():
            p_s = m_s(torch.tensor(Xte_all.astype(np.float32), device=DEVICE)).cpu().numpy()

        m_f = MLP(Xsrc.shape[1]).to(DEVICE)
        m_f.load_state_dict(net.state_dict())
        train_es(m_f, Xsub, ysub, Xva_e, yva_e, lr=1e-3, max_ep=200, patience=15)
        m_f.eval()
        with torch.no_grad():
            p_f = m_f(torch.tensor(Xte_all.astype(np.float32), device=DEVICE)).cpu().numpy()

        curve[f"N={N}"] = {"scratch": metrics_reg(yte, p_s), "pretrained_finetune": metrics_reg(yte, p_f)}
        print(f"[C] N={N:2d}: scratch={curve[f'N={N}']['scratch']['r2']:.3f} "
              f"finetune={curve[f'N={N}']['pretrained_finetune']['r2']:.3f}", flush=True)
    RES["C_transfer_curve"] = curve


# --------------------------------------------- D. extreme-event transitions ----
def part_d(tr, va, te, pre):
    Xtr = pre.transform(tr[FEATURES + ["zone_id"]])
    models = {}
    lgbm = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=6,
                         random_state=SEED, n_jobs=-1, verbose=-1)
    lgbm.fit(Xtr, tr["instability_score"].values.astype(float))
    models["lightgbm"] = lgbm
    rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, random_state=SEED, n_jobs=-1)
    rf.fit(Xtr, tr["instability_score"].values.astype(float))
    models["random_forest"] = rf

    te = te.copy()
    te["pred_lgbm"] = lgbm.predict(pre.transform(te[FEATURES + ["zone_id"]]))
    te["pred_rf"] = rf.predict(pre.transform(te[FEATURES + ["zone_id"]]))

    THR_WARN, THR_CROSS, LOOKBACK, HORIZON = 70.0, 75.0, 30, 10
    events = []
    for (s, z), g in te.groupby(["seed", "zone_id"], sort=False):
        g = g.reset_index(drop=True)
        fos = g["fos"].values
        for t in range(LOOKBACK, len(g)):
            if fos[t] < 1.0 and fos[t - 1] >= 1.0 and fos[max(0, t - LOOKBACK):t].min() >= 1.2:
                events.append((s, z, t, g))
    out = {}
    for mname in ["lightgbm", "random_forest"]:
        detected, leads = 0, []
        for s, z, t, g in events:
            preds = g[mname].values
            warn_days = [k for k in range(max(0, t - HORIZON), t) if preds[k] >= THR_WARN]
            if warn_days:
                detected += 1
                leads.append(t - warn_days[0])
        out[mname] = {"events": len(events), "detected": detected,
                      "detection_rate": round(detected / max(len(events), 1), 3),
                      "mean_lead_days": round(float(np.mean(leads)), 2) if leads else None,
                      "max_lead_days": int(max(leads)) if leads else None}
        print(f"[D] {mname}: {out[mname]}", flush=True)
    RES["D_transition_detection"] = out
    RES["D_event_definition"] = ("crossing FoS<1.0 after >=30 stable days (FoS>=1.2); warning = predicted "
                                 f"instability>={THR_WARN} within {HORIZON} days before crossing")


def main():
    d = generate_corpus()
    tr, va, te = load_parts(d)
    pre = encoders(tr)
    print(f"rows tr/va/te = {len(tr)}/{len(va)}/{len(te)}", flush=True)
    part_a(tr, va, te, pre)
    OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")
    part_b(tr, va, te, pre)
    OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")
    part_c(d, tr, va, te, pre)
    OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")
    part_d(tr, va, te, pre)
    OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()