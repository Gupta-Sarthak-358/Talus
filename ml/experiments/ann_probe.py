"""ANN probe under the frozen benchmark protocol (temp work, nothing committed).

Models:
  1. MLP on the 12 snapshot features (+zone one-hot) -- sanity benchmark.
  2. LSTM over 14-day windows of dynamic features + static context -- attacks
     the state-memory weakness found in the directionality audit.

Protocol: train seeds 42-81, validation 82-86 (early stopping / selection),
test 87-91 touched ONCE at the end. Same splits as the tree benchmark.
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
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
from config import FEATURES, CATEGORICAL_FEATURES, TRAIN_SEEDS, VAL_SEEDS, TEST_SEEDS

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
OUT = Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\ann_results.json")
CORPUS = r"C:\Users\satvi\Desktop\Talus\data\processed\generator_v1\ml_handoff\synthetic_ml_dataset_seeds_42_91.csv"
SEED = 0
np.random.seed(SEED)
torch.manual_seed(SEED)

RESULTS = {"device": str(DEVICE), "torch": torch.__version__, "cuda_available": torch.cuda.is_available(), "models": {}}


def metrics(y, p):
    return {"mae": float(mean_absolute_error(y, p)),
            "rmse": float(np.sqrt(mean_squared_error(y, p))),
            "r2": float(r2_score(y, p))}


def load():
    d = pd.read_csv(CORPUS)
    d["seed"] = d["seed"].astype(int)
    base = d[d.seed <= 81].groupby("zone_id").agg(baseline_inst=("instability_score", "min"),
                                                  baseline_fos=("fos", "max")).reset_index()
    d = d.merge(base, on="zone_id", how="left")
    d["delta_instability"] = d["instability_score"] - d["baseline_inst"]
    d["delta_fos"] = d["fos"] - d["baseline_fos"]
    tr = d[d.seed.isin(TRAIN_SEEDS)].reset_index(drop=True)
    va = d[d.seed.isin(VAL_SEEDS)].reset_index(drop=True)
    te = d[d.seed.isin(TEST_SEEDS)].reset_index(drop=True)
    return tr, va, te


TARGET_COL = {"abs_instability": "instability_score",
              "delta_instability": "delta_instability",
              "delta_fos": "delta_fos"}


def target(df, t):
    return df[TARGET_COL[t]].values.astype(np.float32)


# ---------------------------------------------------------------- MLP ----
class MLP(nn.Module):
    def __init__(self, din):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(din, 128), nn.GELU(), nn.Dropout(0.15),
            nn.Linear(128, 64), nn.GELU(), nn.Dropout(0.15),
            nn.Linear(64, 32), nn.GELU(),
            nn.Linear(32, 1))

    def forward(self, x):
        return self.net(x).squeeze(-1)


def run_mlp(tr, va, te, tname, max_epochs=200, patience=15, bs=512, lr=1e-3):
    nums = [c for c in FEATURES if c not in CATEGORICAL_FEATURES]
    cats = CATEGORICAL_FEATURES + ["zone_id"]
    pre = ColumnTransformer([("n", StandardScaler(), nums),
                             ("c", OneHotEncoder(handle_unknown="ignore"), cats)])
    Xtr = pre.fit_transform(tr[FEATURES + ["zone_id"]]).astype(np.float32)
    Xva = pre.transform(va[FEATURES + ["zone_id"]]).astype(np.float32)
    Xte = pre.transform(te[FEATURES + ["zone_id"]]).astype(np.float32)
    ytr, yva, yte = target(tr, tname), target(va, tname), target(te, tname)

    model = MLP(Xtr.shape[1]).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    lossf = nn.MSELoss()
    Xtr_t = torch.tensor(Xtr, device=DEVICE)
    ytr_t = torch.tensor(ytr, device=DEVICE)
    Xva_t = torch.tensor(Xva, device=DEVICE)

    best_rmse, best_state, wait, best_ep = 1e18, None, 0, -1
    for ep in range(max_epochs):
        model.train()
        perm = torch.randperm(len(Xtr_t), device=DEVICE)
        for i in range(0, len(perm), bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            loss = lossf(model(Xtr_t[idx]), ytr_t[idx])
            loss.backward()
            opt.step()
        model.eval()
        with torch.no_grad():
            pv = model(Xva_t).cpu().numpy()
        rmse = float(np.sqrt(mean_squared_error(yva, pv)))
        if rmse < best_rmse - 1e-5:
            best_rmse, wait, best_ep = rmse, 0, ep
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        pte = model(torch.tensor(Xte, device=DEVICE)).cpu().numpy()
        pva = model(torch.tensor(Xva, device=DEVICE)).cpu().numpy()
    return {"val": metrics(yva, pva), "test": metrics(yte, pte),
            "epochs": best_ep + 1, "params": sum(p.numel() for p in model.parameters())}


# --------------------------------------------------------------- LSTM ----
DYN = ["rainfall_24h_mm", "rainfall_7d_mm", "crack_density", "sev_ord",
       "blast_frequency_per_week", "blast_vibration_ppv_mms",
       "days_since_inspection", "prior_incident_f", "groundwater_proxy"]
STAT_NUM = ["slope_angle_deg", "slope_height_m"]
SEV_ORDER = {"normal": 0.0, "minor": 1.0, "moderate": 2.0, "severe": 3.0, "critical": 4.0}
ROCKS = sorted(["clayey_sandstone", "lateritic_soil", "sandstone", "variegated_sandy_clay"])
ZONES = ["ZONE_A", "ZONE_B", "ZONE_C", "ZONE_D"]
L = 14


def encode_frame(df):
    g = df.copy()
    g["sev_ord"] = g["crack_severity"].astype(str).map(SEV_ORDER)
    g["prior_incident_f"] = g["prior_incident"].astype(float)
    rock = np.zeros((len(g), len(ROCKS)), dtype=np.float32)
    for i, r in enumerate(ROCKS):
        rock[:, i] = (g["rock_type"].values == r)
    zone = np.zeros((len(g), len(ZONES)), dtype=np.float32)
    for i, z in enumerate(ZONES):
        zone[:, i] = (g["zone_id"].values == z)
    static = np.hstack([g[STAT_NUM].values.astype(np.float32), rock, zone])
    dyn = g[DYN].values.astype(np.float32)
    return dyn, static


class SeqNet(nn.Module):
    def __init__(self, din, dstat, h=64):
        super().__init__()
        self.lstm = nn.LSTM(din, h, batch_first=True)
        self.head = nn.Sequential(nn.Linear(h + dstat, 64), nn.GELU(), nn.Dropout(0.1), nn.Linear(64, 1))

    def forward(self, x, s):
        o, _ = self.lstm(x)
        h = o[:, -1]
        return self.head(torch.cat([h, s], dim=1)).squeeze(-1)


def build_windows(df, ycol):
    ycol = TARGET_COL[ycol]
    seqs, stats, ys = [], [], []
    for _, g in df.groupby(["seed", "zone_id"], sort=False):
        g = g.reset_index(drop=True)
        if len(g) < L:
            continue
        dyn, stat = encode_frame(g)
        y = g[ycol].values.astype(np.float32)
        for t in range(L - 1, len(g)):
            seqs.append(dyn[t - L + 1:t + 1])
            stats.append(stat[t])
            ys.append(y[t])
    return np.stack(seqs), np.stack(stats), np.array(ys, dtype=np.float32)


def run_lstm(tr, va, te, tname, max_epochs=60, patience=8, bs=512, lr=1e-3):
    S_tr, St_tr, y_tr = build_windows(tr, tname)
    S_va, St_va, y_va = build_windows(va, tname)
    S_te, St_te, y_te = build_windows(te, tname)

    mu, sd = S_tr.reshape(-1, S_tr.shape[-1]).mean(0), S_tr.reshape(-1, S_tr.shape[-1]).std(0) + 1e-6
    norm = lambda S: ((S - mu) / sd).astype(np.float32)
    smu, ssd = St_tr[:, :2].mean(0), St_tr[:, :2].std(0) + 1e-6
    snorm = lambda A: np.hstack([((A[:, :2] - smu) / ssd), A[:, 2:]]).astype(np.float32)

    mk = lambda S, St: (torch.tensor(norm(S), device=DEVICE), torch.tensor(snorm(St), device=DEVICE))
    Xtr_s, Xtr_st = mk(S_tr, St_tr)
    Xva_s, Xva_st = mk(S_va, St_va)
    Xte_s, Xte_st = mk(S_te, St_te)
    ytr_t = torch.tensor(y_tr, device=DEVICE)

    model = SeqNet(len(DYN), St_tr.shape[1]).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    lossf = nn.MSELoss()

    best_rmse, best_state, wait, best_ep = 1e18, None, 0, -1
    for ep in range(max_epochs):
        model.train()
        perm = torch.randperm(len(Xtr_s), device=DEVICE)
        for i in range(0, len(perm), bs):
            idx = perm[i:i + bs]
            opt.zero_grad()
            loss = lossf(model(Xtr_s[idx], Xtr_st[idx]), ytr_t[idx])
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        model.eval()
        with torch.no_grad():
            pv = model(Xva_s, Xva_st).cpu().numpy()
        rmse = float(np.sqrt(mean_squared_error(y_va, pv)))
        if rmse < best_rmse - 1e-5:
            best_rmse, wait, best_ep = rmse, 0, ep
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        pte = model(Xte_s, Xte_st).cpu().numpy()
        pva = model(Xva_s, Xva_st).cpu().numpy()
    n_train_windows = len(y_tr)
    return {"val": metrics(y_va, pva), "test": metrics(y_te, pte),
            "epochs": best_ep + 1, "train_windows": int(n_train_windows),
            "window_len_days": L,
            "params": sum(p.numel() for p in model.parameters())}


def main():
    tr, va, te = load()
    print(f"device={DEVICE} cuda={torch.cuda.is_available()} rows tr/va/te={len(tr)}/{len(va)}/{len(te)}", flush=True)
    targets = ["abs_instability", "delta_instability", "delta_fos"]

    for t in targets:
        t0 = time.time()
        r = run_mlp(tr, va, te, t)
        dt = round(time.time() - t0, 1)
        RESULTS["models"][f"mlp::{t}"] = {**r, "train_sec": dt}
        print(f"[MLP ] {t:20s} test R2={r['test']['r2']:.3f} MAE={r['test']['mae']:.3f} "
              f"RMSE={r['test']['rmse']:.3f} (val R2={r['val']['r2']:.3f}, {r['epochs']}ep, {dt}s)", flush=True)
        OUT.write_text(json.dumps(RESULTS, indent=2), encoding="utf-8")

    for t in targets:
        t0 = time.time()
        r = run_lstm(tr, va, te, t)
        dt = round(time.time() - t0, 1)
        RESULTS["models"][f"lstm14::{t}"] = {**r, "train_sec": dt}
        print(f"[LSTM] {t:20s} test R2={r['test']['r2']:.3f} MAE={r['test']['mae']:.3f} "
              f"RMSE={r['test']['rmse']:.3f} (val R2={r['val']['r2']:.3f}, {r['epochs']}ep, {dt}s)", flush=True)
        OUT.write_text(json.dumps(RESULTS, indent=2), encoding="utf-8")

    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()