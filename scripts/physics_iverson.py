"""VI-2P-B physics branch: Iverson-response FoS ensemble (NO FITTING, NO SCORES).

Per championship event × snapshot: trailing-30d IMD pulses -> linearized
pore-pressure response -> infinite-slope FoS over frozen parameter ensemble
(4 D0 x 3 H x 3 Kz x 3 c' x 3 phi = 324 combos). Outputs per snapshot:
fos_median, fos_min, fos_frac_below_1 (+ fos_drop_7d derived in audit).
Leakage: pulses dated <= snapshot grid-end; T-day grid excluded (V-B rule).
Outputs runs/phase_v/vi2pb/physics_features.json + audit. No model, no thresholds.
Run (mnemo-venv): python scripts/physics_iverson.py
"""
from __future__ import annotations

import glob
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RDIR = REPO / "runs" / "phase_v" / "daily_replay"
OUTDIR = REPO / "runs" / "phase_v" / "vi2pb"

D0S = [1e-6, 1e-5, 1e-4, 1e-3]
HS = [1.0, 2.0, 3.0]
KZS = [1e-6, 1e-5, 1e-4]
CS = [0.0, 2000.0, 5000.0]
PHIS = [25.0, 30.0, 35.0]
GAMMA, GAMMAW = 18000.0, 9810.0


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def R(ts):
    ts = np.asarray(ts, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.sqrt(ts / np.pi) * np.exp(-1.0 / ts) - np.vectorize(
            lambda v: 1.0 if v <= 0 else __import__("math").erfc(1.0 / np.sqrt(v)))(ts)
    return np.where(ts > 0, out, 0.0)


def main() -> int:
    import xarray as xr
    RAIN = {}
    feats = {}
    for f in sorted(glob.glob(str(RDIR / "event_*.json"))):
        e = json.load(open(f, encoding="utf-8"))
        la, lo = e["lat"], e["lon"]
        beta = float(np.radians(e["snapshots"]["T"]["terrain"]["slope_deg"]))
        flat = beta < np.radians(5.0)
        ev = pd.Timestamp(e["event_date"]).date()
        key = (ev.year, round(la, 2), round(lo, 2))
        if key not in RAIN:
            ds = xr.open_dataset(str(REPO / f"data/raw/imd/ind{ev.year}_rfp25.nc"))
            s = ds.RAINFALL.sel(LATITUDE=la, LONGITUDE=lo, method="nearest")
            RAIN[key] = pd.Series(np.asarray(s.values, dtype=float),
                                  index=pd.to_datetime(s.TIME.values)).fillna(0.0)
            ds.close()
        rain = RAIN[key]
        snaps = {}
        for skey, sn in e["snapshots"].items():
            gd = pd.Timestamp(sn["grid_end"]).date()
            assert gd <= ev, "post-event pulse!"
            hist = rain.loc[:pd.Timestamp(gd)].iloc[-30:]
            assert (hist.index.date <= gd).all()
            pulses = (hist.values / 1000.0) / 86400.0  # m/s per day
            n = len(pulses)
            ages = (np.arange(n, 0, -1) - 0.5) * 86400.0  # pulse mid-age, seconds
            Iavg = float(hist.mean() / 1000.0 / 86400.0)
            fos_all = []
            for D0 in D0S:
                for H in HS:
                    Tstar = ages * D0 / H ** 2
                    dT = 86400.0 * D0 / H ** 2
                    Resp = R(Tstar) - R(Tstar - dT)
                    for Kz in KZS:
                        psi_tr = np.sum((pulses / Kz) * H * Resp)
                        psi = psi_tr + (Iavg / Kz) * H * 0.5
                        psi = float(min(max(psi, 0.0), H))
                        for c in CS:
                            for ph in PHIS:
                                t = np.tan(np.radians(ph))
                                num = c + (GAMMA * H - psi * GAMMAW) * (np.cos(beta) ** 2) * t
                                den = GAMMA * H * np.sin(beta) * np.cos(beta)
                                fos_all.append(num / den if den > 0 else np.inf)
            fos_all = np.array(fos_all)
            if flat:
                snaps[skey] = {"grid_end": str(gd), "fos_median": None, "fos_min": None,
                               "fos_frac_below_1": None, "n_combos": 0,
                               "provenance": "ABSTAIN-flat (infinite-slope invalid below 5 deg)"}
                continue
            assert np.isfinite(fos_all).all(), "non-finite FoS"
            snaps[skey] = {"grid_end": str(gd), "fos_median": round(float(np.median(fos_all)), 3),
                           "fos_min": round(float(fos_all.min()), 3),
                           "fos_frac_below_1": round(float((fos_all < 1.0).mean()), 3),
                           "n_combos": len(fos_all), "provenance": "ANALYTICAL-ensemble"}
        snaps["T-1"]["fos_drop_note"] = "drop_7d computed in audit"
        feats[e["slide_no"]] = {"event_date": str(ev), "beta_deg": round(float(np.degrees(beta)), 1),
                                "snapshots": snaps}
        t = snaps["T"]
        log(f"{e['slide_no']}: FoS_med T={t['fos_median']} min={t['fos_min']} "
            f"frac<1={t['fos_frac_below_1']}")
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "physics_features.json").write_text(json.dumps(feats, indent=2), encoding="utf-8")
    # audit: fos_drop_7d + sanity (FoS should generally decrease toward T in wet events)
    aud = {"events": len(feats), "combos": 324, "leakage": "pulses <= grid-end asserted",
           "drops": {}}
    for sid, v in feats.items():
        sn = v["snapshots"]
        if sn["T"]["fos_median"] is None:
            aud["drops"][sid] = "ABSTAIN-flat"
            continue
        d7 = round(sn["T"]["fos_median"] - sn["T-7"]["fos_median"], 3)
        aud["drops"][sid] = d7
    neg = sum(1 for v in aud["drops"].values() if isinstance(v, float) and v < 0)
    ndef = sum(1 for v in aud["drops"].values() if isinstance(v, float))
    aud["events_with_T7_to_T_FoS_decline"] = f"{neg}/{ndef} defined (rest ABSTAIN-flat)"
    (OUTDIR / "physics_audit.json").write_text(json.dumps(aud, indent=2), encoding="utf-8")
    log(f"declining FoS T-7->T: {neg}/{len(feats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
