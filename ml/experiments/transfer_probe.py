"""Transfer-learning probe (temp work, nothing committed).

Question: does a physics prior learned over a BROAD parameter distribution
(an 'external' slope-stability simulator built on the same published
infinite-slope equation) reduce how many Neyveli worlds are needed?

Method:
  1. SOURCE DOMAIN: ~120K random slope cases sampled from published geotech
     ranges (neyveli_geotech_parameters.csv) + wide geometry/wetting/crack
     ranges; FoS computed with the FROZEN physics functions. Non-causal ML
     features emitted as noise. This stands in for the Xu-et-al-style
     pretrained surrogate (no public checkpoint exists -> reproduce concept).
  2. PRETRAIN MLP on source -> INSTABILITY_SCORE.
  3. DATA-EFFICIENCY CURVE: fine-tune pretrained vs scratch-trained twin at
     N in {5,10,20,40} train seeds (42..41+N). Val seeds 82-86 for early
     stopping. Test 87-91 evaluated once per config (descriptive curve;
     final-model selection remains validation-only).
  4. LightGBM per N for tree context. Zero-shot source model also reported.
  5. Simplified TrAdaBoost.R2 (Pardoe-Stone style) at N=5 and N=20.
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
from lightgbm import LGBMRegressor
from sklearn.tree import DecisionTreeRegressor

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\data_generation")
from instability.sampler import fos_slope, instability_score

sys.path.insert(0, r"C:\Users\satvi\Desktop\Talus\ml\benchmark")
from config import FEATURES, CATEGORICAL_FEATURES, VAL_SEEDS, TEST_SEEDS

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
OUT = Path(r"C:\Users\satvi\AppData\Local\Temp\opencode\talus_ml_probe\transfer_results.json")
CORPUS = r"C:\Users\satvi\Desktop\Talus\data\processed\generator_v1\ml_handoff\synthetic_ml_dataset_seeds_42_91.csv"
GEOTECH = r"C:\Users\satvi\Desktop\Talus\data\processed\geotech\neyveli_geotech_parameters.csv"
SEED = 0
np.random.seed(SEED)
torch.manual_seed(SEED)
RES = {"device": str(DEVICE), "note": "test touched once per N-config; descriptive data-efficiency curve", "runs": {}}


def metrics(y, p):
    return {"mae": float(mean_absolute_error(y, p)),
            "rmse": float(np.sqrt(mean_squared_error(y, p))),
            "r2": float(r2_score(y, p))}


# ---------------------------------------------------------- source domain ----
ROCKS = ["lateritic_soil", "clayey_sandstone", "variegated_sandy_clay", "sandstone"]
ZONES = ["ZONE_A", "ZONE_B", "ZONE_C", "ZONE_D"]
SEVS = ["normal", "minor", "moderate", "severe", "critical"]


def rock_params():
    g = pd.read_csv(GEOTECH)
    out = {}
    for r in ROCKS:
        row = g[g.material == r].iloc[0]
        out[r] = dict(c=(float(row["cohesion_kPa_min"]), float(row["cohesion_kPa_max"])),
                      phi=(float(row["friction_phi_deg_min"]), float(row["friction_phi_deg_max"])),
                      gamma=(float(row["density_kg_m3_min"]) / 1000.0, float(row["density_kg_m3_max"]) / 1000.0))
    return out


RP = rock_params()


def sample_source(n):
    rock = np.random.choice(ROCKS, n)
    c = np.array([np.random.uniform(*RP[r]["c"]) for r in rock])
    phi = np.array([np.random.uniform(*RP[r]["phi"]) for r in rock])
    gamma = np.array([np.random.uniform(*RP[r]["gamma"]) for r in rock])
    h = np.random.uniform(2.0, 40.0, n)
    theta = np.random.uniform(10.0, 75.0, n)
    face = np.random.uniform(35.0, 90.0, n)
    proxy = np.exp(np.random.uniform(np.log(0.5), np.log(250.0), n))
    wf_prob = np.clip(proxy / 150.0, 0.05, 0.9)
    wf = np.random.rand(n) < wf_prob
    dens = np.random.uniform(0.05, 2.0, n)
    sev = np.random.choice(SEVS, n)
    fos = fos_slope(c, phi, gamma, h, theta, proxy, wf, dens, sev, face)
    ok = np.isfinite(fos)
    df = pd.DataFrame({
        "rainfall_24h_mm": np.exp(np.random.uniform(np.log(0.1), np.log(120.0), n)) * ok,
        "rainfall_7d_mm": np.exp(np.random.uniform(np.log(0.5), np.log(400.0), n)) * ok,
        "slope_angle_deg": theta, "slope_height_m": h, "rock_type": rock,
        "crack_density": dens, "crack_severity": sev,
        "blast_frequency_per_week": np.random.uniform(0, 28, n),
        "blast_vibration_ppv_mms": np.where(np.random.rand(n) < 0.3, np.exp(np.random.uniform(np.log(1.0), np.log(80.0), n)), 0.0),
        "days_since_inspection": np.random.randint(0, 30, n),
        "prior_incident": np.zeros(n, dtype=bool),
        "groundwater_proxy": proxy, "zone_id": np.random.choice(ZONES, n),
        "instability_score": np.round(instability_score(fos), 1),
    })
    return df[ok]


# ------------------------------------------------------------------ nets ----
class MLP(nn.Module):
    def __init__(self, din, widths=(256, 128, 64)):
        super().__init__()
        layers, d = [], din
        for w in widths:
            layers += [nn.Linear(d, w), nn.GELU(), nn.Dropout(0.15)]
            d = w
        layers += [nn.Linear(d, 1)]
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x).squeeze(-1)


def encode_fit(df):
    nums = [c for c in FEATURES if c not in CATEGORICAL_FEATURES]
    cats = CATEGORICAL_FEATURES + ["zone_id"]
    pre = ColumnTransformer([("n", StandardScaler(), nums),
                             ("c", OneHotEncoder(handle_unknown="ignore"), cats)])
    pre.fit(df[FEATURES + ["zone_id"]])
    return pre


def enc(pre, df):
    return pre.transform(df[FEATURES + ["zone_id"]]).astype(np.float32)


def train_earlystop(model, Xtr, ytr, Xva, yva, lr, max_epochs, patience, bs=512):
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    lossf = nn.MSELoss()
    Xt = torch.tensor(Xtr, device=DEVICE)
    yt = torch.tensor(ytr, device=DEVICE)
    Xv = torch.tensor(Xva, device=DEVICE)
    best, state, wait, ep_ok = 1e18, None, 0, 0
    for ep in range(max_epochs):
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


def eval_test(model, pre, te):
    model.eval()
    with torch.no_grad():
        p = model(torch.tensor(enc(pre, te), device=DEVICE)).cpu().numpy()
    return metrics(te["instability_score"].values.astype(float), p)


# ------------------------------------------------------------ main flow ----
def main():
    tr_all = pd.read_csv(CORPUS)
    tr_all["seed"] = tr_all["seed"].astype(int)
    va = tr_all[tr_all.seed.isin(VAL_SEEDS)].reset_index(drop=True)
    te = tr_all[tr_all.seed.isin(TEST_SEEDS)].reset_index(drop=True)
    yva = va["instability_score"].values.astype(float)
    yte = te["instability_score"].values.astype(float)

    t0 = time.time()
    src = sample_source(120_000)
    print(f"source cases: {len(src)} ({time.time()-t0:.1f}s)", flush=True)
    RES["source_cases"] = int(len(src))

    pre_src = encode_fit(src)
    Xsrc = enc(pre_src, src)
    net = MLP(Xsrc.shape[1]).to(DEVICE)
    t0 = time.time()
    train_earlystop(net, Xsrc, src["instability_score"].values.astype(np.float32),
                    enc(pre_src, va), yva.astype(np.float32), lr=1e-3, max_epochs=80, patience=8)
    print(f"pretrain done ({time.time()-t0:.0f}s)", flush=True)
    RES["zero_shot_source_on_test"] = eval_test(net, pre_src, te)
    print(f"[zero-shot] source model on Neyveli test: {RES['zero_shot_source_on_test']}", flush=True)
    OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")

    for N in [5, 10, 20, 40]:
        sub = tr_all[tr_all.seed.isin(list(range(42, 42 + N)))].reset_index(drop=True)
        ysub = sub["instability_score"].values.astype(np.float32)
        block = {}

        pre_n = encode_fit(sub)
        m_scratch = MLP(pre_n.transform(sub[:1]).shape[1]).to(DEVICE)
        e1 = train_earlystop(m_scratch, enc(pre_n, sub), ysub, enc(pre_n, va), yva.astype(np.float32), lr=1e-3, max_epochs=200, patience=15)
        block["scratch_mlp"] = {"test": eval_test(m_scratch, pre_n, te), "epochs": e1}

        m_ft = MLP(pre_n.transform(sub[:1]).shape[1]).to(DEVICE)
        m_ft.load_state_dict(net.state_dict())
        e2 = train_earlystop(m_ft, enc(pre_n, sub), ysub, enc(pre_n, va), yva.astype(np.float32), lr=1e-3, max_epochs=200, patience=15)
        block["pretrained_finetune"] = {"test": eval_test(m_ft, pre_n, te), "epochs": e2}

        lgbm = LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=6,
                             random_state=SEED, n_jobs=-1, verbose=-1)
        lgbm.fit(pre_n.transform(sub), ysub)
        block["lightgbm"] = {"test": metrics(yte, lgbm.predict(pre_n.transform(te)))}

        RES["runs"][f"N={N}"] = block
        print(f"[N={N:2d}] scratch R2={block['scratch_mlp']['test']['r2']:.3f}  "
              f"finetune R2={block['pretrained_finetune']['test']['r2']:.3f}  "
              f"lgbm R2={block['lightgbm']['test']['r2']:.3f}", flush=True)
        OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")

    # ---------------- simplified TrAdaBoost.R2 (Pardoe-Stone style) --------
    def tradaboost(N, T=30, depth=6, n_src=20_000):
        sub = tr_all[tr_all.seed.isin(list(range(42, 42 + N)))].reset_index(drop=True)
        pre = encode_fit(pd.concat([src.sample(min(5000, len(src)), random_state=SEED), sub], ignore_index=True))
        S = enc(pre, src.sample(n_src, random_state=SEED))
        yS = src.sample(n_src, random_state=SEED)["instability_score"].values.astype(float)
        Ttr = enc(pre, sub)
        yT = sub["instability_score"].values.astype(float)
        Te = enc(pre, te)
        wS = np.full(len(S), 0.5 / len(S))
        wT = np.full(len(Ttr), 0.5 / len(Ttr))
        hyps, betas = [], []
        for t in range(T):
            w = np.concatenate([wS, wT])
            w /= w.sum()
            dt = DecisionTreeRegressor(max_depth=depth, random_state=SEED)
            dt.fit(np.vstack([S, Ttr]), np.concatenate([yS, yT]), sample_weight=w)
            pT = dt.predict(Ttr)
            eps = np.abs(pT - yT) / max(np.abs(pT - yT).max(), 1e-9)
            eps_bar = float(eps.mean())
            if eps_bar >= 0.5:
                break
            beta = 1.0 / (1.0 + np.sqrt(eps_bar / (1.0 - eps_bar)))
            pS = dt.predict(S)
            epsS = np.abs(pS - yS) / max(np.abs(pT - yT).max(), 1e-9)
            wS = wS[:len(S)] * (beta ** epsS)
            hyps.append(dt)
            betas.append(np.log(1.0 / beta))
        ens = np.average(np.stack([h.predict(Te) for h in hyps[-len(hyps)//2:]]), axis=0,
                         weights=np.maximum(betas[-len(hyps)//2:], 1e-6))
        return {"test": metrics(yte, ens), "rounds": len(hyps)}

    for N in [5, 20]:
        r = tradaboost(N)
        RES["runs"][f"N={N}"]["tradaboost_r2"] = r
        print(f"[N={N:2d}] tradaboost R2={r['test']['r2']:.3f} ({r['rounds']} rounds)", flush=True)
        OUT.write_text(json.dumps(RES, indent=2), encoding="utf-8")

    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()