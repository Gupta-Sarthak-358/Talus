"""VI-T0B: small GRU on frozen matrix_v1. Static-embed + trajectory + fusion.

GRU(32) over dynamic sequence; static -> Linear(8) site embedding; concat ->
Dense(16) -> sigmoid. <10k params. Same 5 grouped site-folds as T0A. Per-row
BCE with pos_weight, mask-padded to 61 steps, fixed 120 epochs (baseline, no
tuning), seed-fixed. Metrics pooled OOF: AUC/AP/Brier/ECE y14+y7 + escalation
table. Dev only. No held-out. Outputs runs/phase_v/vit0b/.
Run: mnemo-venv python scripts/train_vit_t0b.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import average_precision_score, roc_auc_score

REPO = Path(__file__).resolve().parents[1]
OUTDIR = REPO / "runs" / "phase_v" / "vit0b"
EPOCHS = 600
SEED = 42


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def brier(y, p) -> float:
    return round(float(np.mean((p - y) ** 2)), 4)


def ece(y, p, bins=10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    e = 0.0
    for b in range(bins):
        m = (p >= edges[b]) & (p <= edges[b + 1])
        if m.sum() == 0:
            continue
        e += (m.sum() / len(p)) * abs(y[m].mean() - p[m].mean())
    return round(float(e), 4)


def metrics(y, p) -> dict:
    return {"auc": round(float(roc_auc_score(y, p)), 4),
            "ap": round(float(average_precision_score(y, p)), 4),
            "brier": brier(y, p), "ece": ece(y, p)}


class GRUHead(nn.Module):
    def __init__(self, ndyn: int, nstat: int):
        super().__init__()
        self.gru = nn.GRU(ndyn, 32, batch_first=True)
        self.stat = nn.Sequential(nn.Linear(nstat, 8), nn.ReLU())
        self.fuse = nn.Sequential(nn.Linear(40, 16), nn.ReLU(), nn.Dropout(0.3),
                                  nn.Linear(16, 1))
        n = sum(p.numel() for p in self.parameters())
        log(f"params: {n}")

    def forward(self, xd, xs):
        _, h = self.gru(xd)
        h = h.squeeze(0)
        s = self.stat(xs)
        return self.fuse(torch.cat([h, s], dim=1)).squeeze(1)


def main() -> int:
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log(f"device: {dev}")
    d = pd.read_csv(REPO / "data/vit/matrix_v1.csv", parse_dates=["date"])
    recipe = json.load(open(REPO / "data/vit/matrix_v1_recipe.json"))
    DYN, STAT = recipe["dyn"], recipe["static"]
    d = d.sort_values(["traj_id", "date"]).reset_index(drop=True)
    trajs = [{"id": t, "site": g["slide_no"].iloc[0], "fold": g["fold"].iloc[0],
              "dyn": g[DYN].to_numpy(float), "stat": g[STAT].iloc[0].to_numpy(float),
              "y14": g["y14"].to_numpy(float), "y7": g["y7"].to_numpy(float),
              "idx": g.index.to_numpy()}
             for t, g in d.groupby("traj_id")]
    log(f"trajectories: {len(trajs)}")
    T = 61
    oof = pd.Series(index=d.index, dtype=float)
    for fold in sorted(d["fold"].unique()):
        tr = [t for t in trajs if t["fold"] != fold]
        te = [t for t in trajs if t["fold"] == fold]
        med = np.nanmedian(np.concatenate([t["dyn"] for t in tr]), axis=0)
        mu = np.nanmean(np.concatenate([np.where(np.isnan(t["dyn"]), med, t["dyn"])
                                        for t in tr]), axis=0)
        sd = np.nanstd(np.concatenate([np.where(np.isnan(t["dyn"]), med, t["dyn"])
                                       for t in tr]), axis=0) + 1e-6
        smu = np.nanmean(np.stack([t["stat"] for t in tr]), axis=0)
        ssd = np.nanstd(np.stack([t["stat"] for t in tr]), axis=0) + 1e-6

        def prep(t):
            xd = np.where(np.isnan(t["dyn"]), med, t["dyn"])
            n = len(xd)
            pad = np.zeros((T - n, len(DYN)))
            mask = np.zeros(T)
            mask[:n] = 1.0
            return ((np.vstack([xd, pad]) - mu) / sd).astype(np.float32), \
                ((t["stat"] - smu) / ssd).astype(np.float32), mask.astype(np.float32)

        Xdtr = torch.stack([torch.from_numpy(prep(t)[0]) for t in tr]).to(dev)
        Xstr = torch.stack([torch.from_numpy(prep(t)[1]) for t in tr]).to(dev)
        Mtr = torch.stack([torch.from_numpy(prep(t)[2]) for t in tr]).to(dev)
        Ytr = torch.stack([torch.nn.functional.pad(torch.from_numpy(t["y14"]).float(),
                                                   (0, T - len(t["y14"]))) for t in tr]).to(dev)
        net = GRUHead(len(DYN), len(STAT)).to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
        crit = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([10.0]).to(dev),
                                    reduction="none")
        net.train()
        best_loss, wait = 1e9, 0
        for ep in range(EPOCHS):
            opt.zero_grad()
            logits = net(Xdtr, Xstr).unsqueeze(1).expand(-1, T)
            loss = (crit(logits, Ytr) * Mtr).sum() / Mtr.sum()
            loss.backward()
            opt.step()
            lv = float(loss)
            if lv < best_loss - 1e-4:
                best_loss, wait = lv, 0
            else:
                wait += 1
            if wait >= 40:
                break
        net.eval()
        with torch.no_grad():
            for t in te:
                xd, xs, _ = prep(t)
                n = len(t["dyn"])
                out, _ = net.gru(torch.from_numpy(xd).unsqueeze(0).to(dev))
                s = net.stat(torch.from_numpy(xs).unsqueeze(0).to(dev))
                sc = net.fuse(torch.cat(
                    [out.squeeze(0)[:n], s.expand(n, -1)], dim=1)).squeeze(1)
                oof.loc[t["idx"]] = torch.sigmoid(sc).cpu().numpy()
        log(f"fold {fold}: epochs={ep + 1} train_loss={best_loss:.4f}")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    res = {"pooled_raw14": metrics(d["y14"].to_numpy(), oof.to_numpy()),
           "pooled_raw7": metrics(d["y7"].to_numpy(), oof.to_numpy()),
           "epochs": EPOCHS, "seed": SEED, "note": "uncalibrated (calibration at freeze)"}
    json.dump(res, open(OUTDIR / "vit0b_cv.json", "w"), indent=2)
    keys = d[["slide_no", "traj_id", "stratum", "date", "y14", "y7", "fold"]].copy()
    keys["gru"] = oof.to_numpy()
    keys.to_csv(OUTDIR / "oof_preds.csv", index=False)
    log(f"gru: AUC14={res['pooled_raw14']['auc']} Brier={res['pooled_raw14']['brier']} | "
        f"AUC7={res['pooled_raw7']['auc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
