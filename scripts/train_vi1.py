"""VI-1: minimal sequence representation on frozen VI-0 population. ONE change only.

Sequences: dev events (6 snaps, ordered) + background windows (31 daily rows).
Model: Linear(D->16) + GRU(16,1 layer,batch_first) + per-step head, BCE pos_weight,
fixed 300 epochs Adam 1e-3 seed 42. Isotonic on episode-grouped OOF (6-fold),
refit on full dev population, freeze. Held-out: same 60 rows via VI-0 assembly path.
Decision rules identical to VI-0 (FROZEN_BANDS + dev-Youden op). No satellite.
Outputs runs/phase_v/vi1/. Run: mnemo-venv python scripts/train_vi1.py (needs torch)
"""
from __future__ import annotations

import glob
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
POP = REPO / "data/sih26001/processed/vi0_training.csv"
SIDE = REPO / "data/sih26001/processed/vi0_sidecar.csv"
RDIR = REPO / "runs" / "phase_v" / "daily_replay"
SPLIT = REPO / "splits" / "championship_split_v1.json"
OUTDIR = REPO / "runs" / "phase_v" / "vi1"
MODELDIR = REPO / "ml" / "models"
SEED = 42
EPOCHS = 300
NUM = ["slope_angle", "elevation", "aspect", "curvature", "twi", "spi_log",
       "rainfall_24h_mm", "rainfall_3d_mm", "rainfall_7d_mm", "rainfall_30d_mm",
       "soil_moisture", "soil_change_7d", "rain_accel_7d", "ndvi", "distance_to_road",
       "distance_to_river", "drain_density", "seismic_dist_km", "seismic_n50_rate",
       "seismic_years_since", "recent_disturbance"]


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def band(score: float) -> str:
    if score < 50:
        return "Very Low"
    if score < 65:
        return "Low"
    if score < 75:
        return "Moderate"
    if score < 85:
        return "High"
    return "Critical"


STATE = {"Very Low": "NORMAL", "Low": "NORMAL", "Moderate": "WATCH", "High": "ALERT",
         "Critical": "CRITICAL"}


def build_sequences(m, s):
    m = m.reset_index(drop=True)
    s = s.reset_index(drop=True)
    seqs = []
    dev_ev = s[s["kind"] == "dev-event"]
    for slide, g in dev_ev.groupby("slide_no"):
        g = g.sort_values("date")
        seqs.append({"id": slide, "X": m.loc[g.index][NUM + ["lulc"]].copy(),
                     "y": m.loc[g.index, "y7d"].to_numpy(dtype=np.float32),
                     "meta": s.loc[g.index, ["slide_no", "date"]].copy()})
    bg = s[s["kind"] == "background"]
    for (zid, ym), g in bg.groupby([bg["slide_no"], bg["date"].str[:7]]):
        g = g.sort_values("date")
        seqs.append({"id": f"{zid}|{ym}", "X": m.loc[g.index][NUM + ["lulc"]].copy(),
                     "y": m.loc[g.index, "y7d"].to_numpy(dtype=np.float32),
                     "meta": s.loc[g.index, ["slide_no", "date"]].copy()})
    return seqs


def main() -> int:
    import sys
    import warnings
    warnings.filterwarnings("ignore")
    import torch
    import torch.nn as nn
    from torch.nn.utils.rnn import pad_sequence, pack_padded_sequence, pad_packed_sequence
    from sklearn.model_selection import GroupKFold
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import roc_auc_score, average_precision_score
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log(f"device: {dev}")

    m = pd.read_csv(POP)
    s = pd.read_csv(SIDE)
    ho_ids = {r["slide_no"] for r in json.load(open(SPLIT))["events"] if r["side"] == "held-out"}
    assert not s["slide_no"].isin(ho_ids).any(), "held-out in population!"
    cats = sorted(m["lulc"].unique().tolist())
    mu, sd = m[NUM].mean(), m[NUM].std().replace(0, 1)

    def encode(df):
        Xn = ((df[NUM] - mu) / sd).to_numpy(dtype=np.float32)
        oh = np.zeros((len(df), len(cats)), dtype=np.float32)
        oh[np.arange(len(df)), df["lulc"].map({c: i for i, c in enumerate(cats)})] = 1.0
        return np.concatenate([Xn, oh], axis=1)

    D = len(NUM) + len(cats)

    class Seq(nn.Module):
        def __init__(self):
            super().__init__()
            self.inp = nn.Linear(D, 16)
            self.gru = nn.GRU(16, 16, num_layers=1, batch_first=True)
            self.head = nn.Linear(16, 1)

        def forward(self, x, lens):
            h = torch.relu(self.inp(x))
            pk = pack_padded_sequence(h, lens.cpu(), batch_first=True, enforce_sorted=False)
            o, _ = self.gru(pk)
            o, _ = pad_packed_sequence(o, batch_first=True)
            return self.head(o).squeeze(-1)

    seqs = build_sequences(m, s)
    log(f"sequences: {len(seqs)} (dev-event {sum(1 for q in seqs if not q['id'].startswith('BG@'))})")
    Xall = [torch.from_numpy(encode(q["X"])) for q in seqs]
    yall = [torch.from_numpy(q["y"]) for q in seqs]
    lens = torch.tensor([len(q) for q in Xall])
    # episode groups for OOF: dev-event slide_no, background window id
    groups = np.array([q["id"] if not q["id"].startswith("BG@") else q["id"] for q in seqs])
    pos = float(sum(float(q["y"].sum()) for q in seqs))
    pw = (sum(len(q) for q in Xall) - pos) / max(pos, 1)
    log(f"pos_weight={pw:.1f}")

    def fit_predict(tr_idx, te_idx, epochs=EPOCHS):
        net = Seq().to(dev)
        opt = torch.optim.Adam(net.parameters(), lr=1e-3)
        loss = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([pw], device=dev))
        Xb = pad_sequence([Xall[i] for i in tr_idx], batch_first=True).to(dev)
        yb = pad_sequence([yall[i] for i in tr_idx], batch_first=True).to(dev)
        lb = torch.tensor([len(Xall[i]) for i in tr_idx])
        mask = (torch.arange(Xb.shape[1]).unsqueeze(0) < lb.unsqueeze(1)).to(dev)
        net.train()
        for _ in range(epochs):
            opt.zero_grad()
            out = net(Xb, lb)
            l = loss(out[mask], yb[mask])
            l.backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            Xe = pad_sequence([Xall[i] for i in te_idx], batch_first=True).to(dev)
            le = torch.tensor([len(Xall[i]) for i in te_idx])
            pe = torch.sigmoid(net(Xe, le)).cpu().numpy()
        # pe rows align with te_idx order; slice each to its true length
        offs = np.cumsum([0] + [len(Xall[i]) for i in te_idx])
        res = np.full(int(offs[-1]), np.nan)
        for pos, i in enumerate(te_idx):
            res[offs[pos]:offs[pos + 1]] = pe[pos, :len(Xall[i])]
        return res, net

    # OOF over sequence groups (6-fold)
    gkf = GroupKFold(n_splits=6)
    idx = np.arange(len(seqs))
    oof_rows = []
    for tr, te in gkf.split(idx, np.zeros(len(idx)), groups):
        pr, _ = fit_predict(tr, te, epochs=EPOCHS)
        k = 0
        for i in te:
            for t in range(len(Xall[i])):
                oof_rows.append({"seq": seqs[i]["id"], "t": t, "p": float(pr[k]),
                                 "y": float(yall[i][t])})
                k += 1
    oofd = pd.DataFrame(oof_rows)
    yo, po = oofd["y"].to_numpy(), oofd["p"].to_numpy()
    from sklearn.metrics import roc_auc_score as auc
    log(f"OOF auc={auc(yo, po):.4f} brier={np.mean((po - yo) ** 2):.4f}")
    iso = IsotonicRegression(out_of_bounds="clip").fit(po, yo)
    cal = iso.predict(po)
    log(f"OOF-cal brier={np.mean((cal - yo) ** 2):.4f}")
    # Youden op on dev-OOF raw
    cands = sorted(np.unique(np.quantile(po, np.linspace(0, 1, 401))))
    J = [((po[yo == 1] >= t).mean() + (po[yo == 0] < t).mean() - 1, t) for t in cands]
    op_thr = max(J)[1]
    log(f"dev op: rawP >= {op_thr:.4f} (J={max(J)[0]:.3f})")

    # refit on all dev sequences, freeze
    pall, netf = fit_predict(idx, idx, epochs=EPOCHS)
    MODELDIR.mkdir(parents=True, exist_ok=True)
    torch.save({"state": netf.state_dict(), "mu": mu.to_dict(), "sd": sd.to_dict(),
                "cats": cats, "seed": SEED, "epochs": EPOCHS},
               MODELDIR / "vi1_gru_v1.pt")
    joblib.dump({"isotonic": iso, "fit_on": "vi1 sequence grouped-OOF"},
                MODELDIR / "vi1_iso_v1.joblib", compress=3)

    # ---- frozen held-out run (V-B reconstructions, VI-0 assembly path) ----
    sys.path.insert(0, str(REPO / "backend"))
    from app import support as _support
    import xarray as xr
    MAT = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    SIDE0 = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    mlat, mlon = SIDE0["lat"].to_numpy(), SIDE0["lon"].to_numpy()
    quakes = json.load(open(REPO / "data/sih26001/evidence/usgs_quakes.json"))["events"]
    SOILDIR = REPO / "data/raw/soil/v09.2"
    track = pd.read_csv(REPO / "data/sih26001/evidence/trackA_candidates.csv")
    rec = {r["slide_no"]: bool("chronic" in str(r["event_identity"]).lower()
                               or "DISTINCT date" in str(r["event_identity"]))
           for _, r in track.iterrows()}

    def soil_on(date, la, lo):
        import warnings as _w
        fp = SOILDIR / ("ESACCI-SOILMOISTURE-L3S-SSMV-COMBINED-"
                        f"{pd.Timestamp(date):%Y%m%d}000000-fv09.2.nc")
        if not fp.exists():
            return None
        try:
            sds = xr.open_dataset(str(fp))
            da = sds["sm"] if "sm" in sds.data_vars else sds[
                [x for x in sds.data_vars if "sm" in x.lower()][0]]
            c = float(da.sel(lat=la, lon=lo, method="nearest").values.flat[0])
            if np.isfinite(c):
                sds.close()
                return round(c, 4)
            laa = np.asarray(sds["lat"].values).ravel()
            loo = np.asarray(sds["lon"].values).ravel()
            ii, jj = int(np.argmin(np.abs(laa - la))), int(np.argmin(np.abs(loo - lo)))
            with _w.catch_warnings():
                _w.simplefilter("ignore")
                mm = float(np.nanmean(da.isel(lat=slice(max(0, ii - 1), ii + 2),
                                              lon=slice(max(0, jj - 1), jj + 2)).values))
            sds.close()
            return round(mm, 4) if np.isfinite(mm) else None
        except Exception:
            return None

    hrows = []
    for f in sorted(glob.glob(str(RDIR / "event_*.json"))):
        e = json.load(open(f, encoding="utf-8"))
        if e["slide_no"] not in ho_ids:
            continue
        la, lo = e["lat"], e["lon"]
        ai = int(np.argmin(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(mlat - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(mlat))
            * np.sin(np.radians(mlon - lo) / 2) ** 2))))
        base = MAT.iloc[ai]
        ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{pd.Timestamp(e['event_date']).year}_rfp25.nc"))
        rs = ds.RAINFALL.sel(LATITUDE=la, LONGITUDE=lo, method="nearest")
        rain = pd.Series(np.asarray(rs.values, dtype=float),
                         index=pd.to_datetime(rs.TIME.values)).fillna(0.0)
        ds.close()
        feats = []
        for key, sn in sorted(e["snapshots"].items(),
                              key=lambda kv: pd.Timestamp(kv[1]["grid_end"])):
            gd = str(sn["grid_end"])
            w = rain.loc[:gd]
            sm = soil_on(gd, la, lo)
            sm7 = soil_on(str(pd.Timestamp(gd).date() - pd.Timedelta(days=7)), la, lo)
            r7 = float(w.iloc[-7:].sum())
            prior = [q for q in quakes if q["date"] < gd and
                     2 * 6371.0 * np.arcsin(np.sqrt(np.sin(np.radians(q["lat"] - la) / 2) ** 2
                     + np.cos(np.radians(la)) * np.cos(np.radians(q["lat"]))
                     * np.sin(np.radians(q["lon"] - lo) / 2) ** 2)) <= 50.0]
            dall = [2 * 6371.0 * np.arcsin(np.sqrt(np.sin(np.radians(q["lat"] - la) / 2) ** 2
                    + np.cos(np.radians(la)) * np.cos(np.radians(q["lat"]))
                    * np.sin(np.radians(q["lon"] - lo) / 2) ** 2))
                    for q in quakes if q["date"] < gd]
            feats.append({"slope_angle": sn["terrain"]["slope_deg"], "elevation": sn["terrain"]["elevation_m"],
                          "aspect": sn["terrain"]["aspect_deg"], "curvature": sn["terrain"]["curvature"],
                          "twi": sn["terrain"]["twi"], "spi_log": float(np.log1p(max(sn["terrain"]["spi"], 0))),
                          "rainfall_24h_mm": sn["rainfall_24h_mm"]["value"],
                          "rainfall_3d_mm": sn["rainfall_3d_mm"]["value"],
                          "rainfall_7d_mm": sn["rainfall_7d_mm"]["value"],
                          "rainfall_30d_mm": sn["rainfall_30d_mm"]["value"],
                          "soil_moisture": sm if sm is not None else float(base["soil_moisture"]),
                          "soil_change_7d": round((sm or 0) - (sm7 or 0), 4),
                          "rain_accel_7d": round(r7 - float(w.iloc[-14:-7].sum()), 1),
                          "ndvi": float(base["ndvi"]), "distance_to_road": float(base["distance_to_road"]),
                          "distance_to_river": float(base["distance_to_river"]),
                          "drain_density": sn["terrain"]["drain_density"],
                          "seismic_dist_km": round(float(min(dall)) if dall else 999.0, 2),
                          "seismic_n50_rate": round(len(prior) / max(pd.Timestamp(gd).year - 1965, 1), 4),
                          "seismic_years_since": min(pd.Timestamp(gd).year - max([q["year"] for q in prior]), 60) if prior else 60,
                          "recent_disturbance": 0.0, "lulc": str(base["lulc"]),
                          "_snap": key, "_gd": gd, "_spi": sn["terrain"]["spi"]})
        df = pd.DataFrame(feats)
        Xn = ((df[NUM] - mu) / sd).to_numpy(dtype=np.float32)
        oh = np.zeros((len(df), len(cats)), dtype=np.float32)
        oh[np.arange(len(df)), df["lulc"].map({c: i for i, c in enumerate(cats)})] = 1.0
        netf.eval()
        with torch.no_grad():
            praw = torch.sigmoid(netf(torch.from_numpy(np.concatenate([Xn, oh], 1)).unsqueeze(0).to(dev),
                                      torch.tensor([len(df)]))).cpu().numpy()[0].tolist()
        for f_, pr in zip(feats, praw):
            pc = float(iso.predict([pr])[0])
            sc, bd = int(round(pr * 100)), band(int(round(pr * 100)))
            ood = _support.check({k: v for k, v in f_.items() if not k.startswith("_")}
                                 | {"spi": f_["_spi"]})
            hrows.append({"event": e["slide_no"], "episode": e["episode"], "snapshot": f_["_snap"],
                          "grid_end": f_["_gd"], "raw_score": sc, "band": bd, "warning": STATE[bd],
                          "op_alert": bool(pr >= op_thr), "p_cal": round(pc, 4),
                          "probability_status": "uncalibrated-ood" if ood["ood"] else "calibrated",
                          "ood": bool(ood["ood"]), "recurrent": rec.get(e["slide_no"], False),
                          "region": "SOUTH" if la < 27.15 else "NORTH"})
    h = pd.DataFrame(hrows)
    assert len(h) == 60 and not ((h["ood"]) & (h["probability_status"] == "calibrated")).any()
    h["y"] = h["snapshot"].isin(["T-7", "T-3", "T-1", "T"]).astype(int)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    h.to_csv(OUTDIR / "vi1_heldout.csv", index=False)
    y, pr = h["y"].to_numpy(), h["p_cal"].to_numpy()
    sc = {"dev_oof_auc": round(float(roc_auc_score(yo, po)), 4),
          "dev_op_thr": round(float(op_thr), 4),
          "heldout": {"n": len(h),
                      "recall_op_alert_devfixed": round(float(h.groupby("event")["op_alert"].any().mean()), 4),
                      "recall_watch": round(float(h.groupby("event")["warning"].apply(
                          lambda s: s.isin(["WATCH", "ALERT", "CRITICAL"]).any()).mean()), 4),
                      "recall_alert": round(float(h.groupby("event")["warning"].apply(
                          lambda s: s.isin(["ALERT", "CRITICAL"]).any()).mean()), 4),
                      "recall_critical": round(float(h.groupby("event")["warning"].apply(
                          lambda s: (s == "CRITICAL").any()).mean()), 4),
                      "imminence_auc": round(float(roc_auc_score(y, pr)), 4),
                      "imminence_pr": round(float(average_precision_score(y, pr)), 4),
                      "brier7": round(float(np.mean((pr - y) ** 2)), 4),
                      "recurrent_alert": round(float(h[h["recurrent"]].groupby("event")["warning"].apply(
                          lambda s: s.isin(["ALERT", "CRITICAL"]).any()).mean()), 4)
                      if h["recurrent"].any() else None,
                      "novel_alert": round(float(h[~h["recurrent"]].groupby("event")["warning"].apply(
                          lambda s: s.isin(["ALERT", "CRITICAL"]).any()).mean()), 4)}}
    fw = []
    for ev, g in h.groupby("event"):
        g = g.sort_values("grid_end")
        d = {"event": ev}
        for lvl, bands in (("WATCH", ["Moderate", "High", "Critical"]),
                           ("ALERT", ["High", "Critical"]), ("CRITICAL", ["Critical"])):
            hit = g[g["band"].isin(bands)]
            d[lvl] = None if hit.empty else (str(hit["grid_end"].iloc[0]), int(
                (pd.to_datetime(g["grid_end"].max()).date() - pd.to_datetime(
                    hit["grid_end"].iloc[0]).date()).days))
        fw.append(d)
    json.dump({"scorecard": sc, "first_warnings": fw}, open(OUTDIR / "vi1_report.json", "w"), indent=2)
    log(f"heldout={sc['heldout']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
