"""Seismic-memory conditioning features (Taiwan-precedent lane, honest framing).

We do NOT claim quakes cause today's slides. We test whether recent/significant
seismic history carries useful conditioning signal — the model decides.

USGS FDSN catalog (M5+, bbox 26.5-28.5N/87.5-89.5E, 1965-2024) is fetched once
and committed as data/sih26001/evidence/usgs_quakes.json (~26 events, tiny).

Per-row features (no leakage: only quakes with year < row reference year):
  ref_year            slide year if known, else rain_year if known, else 2024
  seismic_dist_km     distance to nearest M5+ ever (static geography)
  seismic_n50_prior   count of M5+ within 50km strictly before ref_year
  seismic_years_since ref_year minus last prior M5+ year within 50km (cap 60;
                      60 = none on record — arid but explicit)

Schema: matrix 22 -> 25 columns (git-ignored); committed 20-row sample stays
22-col fixture order; manifest documents the extension. Serving path
(backend/app/sih26001_model.py) resolves per-zone as-of-2024 values from the
same committed quake table + fixture geometries (separate edit).

Run (py311, stdlib+pd/np): Python311/python.exe scripts/event_seismic_upgrade.py
Then (mnemo): add cols to train/ablate NUMERIC, retrain, ablate, physics, replays.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PROCDIR = REPO / "data/sih26001/processed"
EVIDDIR = REPO / "data/sih26001/evidence"
FIXDIR = REPO / "data/sih26001/fixtures"
MATRIX_CSV = PROCDIR / "feature_matrix.training.csv"
SIDECAR_CSV = PROCDIR / "training_sidecar.csv"
SAMPLE_CSV = EVIDDIR / "feature_matrix.training.sample.csv"
MANIFEST = REPO / "data/sih26001/manifest.training.json"
QUAKES = EVIDDIR / "usgs_quakes.json"
BACKUP = REPO / "runs" / "seismic_upgrade_backup"
SEED = 42
CAP_YEARS = 60
USGS = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
        "&starttime=1965-01-01&endtime=2025-01-01&minmagnitude=5"
        "&minlatitude=26.5&maxlatitude=28.5&minlongitude=87.5&maxlongitude=89.5"
        "&orderby=time")
UA = {"User-Agent": "TALUS-SIH26001-prototype/1.0 (research use)"}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def haversine_m(lat1, lon1, lat2, lon2) -> np.ndarray:
    r = 6371000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin(np.radians(lat2 - lat1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def fetch_quakes() -> list[dict]:
    req = urllib.request.Request(USGS, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    out = []
    epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
    for f in d["features"]:
        p, c = f["properties"], f["geometry"]["coordinates"]
        # epoch arithmetic (Windows fromtimestamp rejects pre-1970 negatives)
        dt = epoch + datetime.timedelta(milliseconds=int(p["time"]))
        out.append({"mag": round(float(p["mag"]), 1),
                    "place": p["place"],
                    "date": dt.strftime("%Y-%m-%d"),
                    "year": int(dt.year),
                    "lat": round(float(c[1]), 3), "lon": round(float(c[0]), 3)})
    return out


def main() -> int:
    if QUAKES.exists():
        quakes = json.loads(QUAKES.read_text(encoding="utf-8"))["events"]
        log(f"quake table cached: {len(quakes)} events")
    else:
        quakes = fetch_quakes()
        QUAKES.write_text(json.dumps({
            "source": "USGS FDSN event API (M5+, 26.5-28.5N/87.5-89.5E, 1965-2024)",
            "fetched": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
            "n": len(quakes), "events": quakes}, indent=1), encoding="utf-8")
        log(f"fetched {len(quakes)} M5+ events -> {QUAKES}")
    qlat = np.array([q["lat"] for q in quakes])
    qlon = np.array([q["lon"] for q in quakes])
    qyr = np.array([q["year"] for q in quakes])
    log(f"largest: {max(quakes, key=lambda q: q['mag'])['mag']} "
        f"({max(quakes, key=lambda q: q['mag'])['date']})")

    mat = pd.read_csv(MATRIX_CSV)
    side = pd.read_csv(SIDECAR_CSV)
    assert len(mat) == len(side) == 2936
    BACKUP.mkdir(parents=True, exist_ok=True)
    shutil.copy(MATRIX_CSV, BACKUP / "feature_matrix.training.csv")
    shutil.copy(SIDECAR_CSV, BACKUP / "training_sidecar.csv")

    lat = side["lat"].to_numpy(float)
    lon = side["lon"].to_numpy(float)
    ref = side["year"].to_numpy(int).copy()
    need = ref <= 0
    ref[need] = side.loc[need, "rain_year"].to_numpy(int)
    ref[ref <= 0] = 2024
    log(f"ref years: slide-year {int((side['year'].to_numpy(int) > 0).sum())}, "
        f"rain-year fallback {int(need.sum())} (<=0 -> 2024)")

    dist = haversine_m(lat[:, None], lon[:, None], qlat[None, :], qlon[None, :]) / 1000.0
    seismic_dist = np.round(dist.min(axis=1), 2)
    n50 = np.zeros(len(mat), dtype=int)
    since = np.full(len(mat), CAP_YEARS, dtype=int)
    for i in range(len(mat)):
        prior = qyr < ref[i]
        within = dist[i] <= 50.0
        hit = prior & within
        n50[i] = int(hit.sum())
        if hit.any():
            since[i] = int(min(ref[i] - int(qyr[hit].max()), CAP_YEARS))
    # RATE not count: raw counts are confounded with catalog exposure
    # (positives avg ref 2017.6 vs negatives 2001.9). Rate = M5+/observable-year.
    exposure = np.clip(ref - 1965, 1, None)
    rate = np.round(n50 / exposure, 4)
    mat["seismic_dist_km"] = seismic_dist
    mat["seismic_n50_rate"] = rate
    mat["seismic_years_since"] = since
    assert not mat.isna().any().any()
    mat.to_csv(MATRIX_CSV, index=False)
    side["seismic_ref_year"] = ref
    side.to_csv(SIDECAR_CSV, index=False)
    log(f"seismic_dist med {np.median(seismic_dist):.1f}km; rows with prior M5+<=50km: "
        f"{int((n50 > 0).sum())}; median years-since {int(np.median(since[since < CAP_YEARS])) if (since < CAP_YEARS).any() else 'n/a'}")

    header = pd.read_csv(FIXDIR / "feature_matrix.sample.csv", nrows=0).columns.tolist()
    assert len(header) == 22
    y = mat["event"].to_numpy(int)
    rng = np.random.default_rng(SEED)
    pi = rng.choice(np.where(y == 1)[0], size=min(10, int((y == 1).sum())), replace=False)
    ni = rng.choice(np.where(y == 0)[0], size=min(10, int((y == 0).sum())), replace=False)
    samp = mat.iloc[sorted(np.concatenate([pi, ni]).tolist())][header]
    assert not samp.isna().any().any() and "FILL" not in samp.to_csv()
    samp.to_csv(SAMPLE_CSV, index=False)

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    st = man.get("stats", {})
    st["matrix_shape"] = [2936, 25]
    st["matrix_sha256"] = sha256(MATRIX_CSV)
    st["sidecar_sha256"] = sha256(SIDECAR_CSV)
    st["sample_sha256"] = sha256(SAMPLE_CSV)
    st["seismic_upgrade"] = {
        "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "quakes": len(quakes),
        "rows_with_prior_M5_50km": int((n50 > 0).sum()),
        "note": "conditioning only (Taiwan precedent): dist-to-nearest-M5+ (static), "
                "count<=50km before ref-year, years-since capped 60. Model decides if useful.",
    }
    man["stats"] = st
    feats = man.get("features", {})
    feats["seismic"] = ("USGS FDSN M5+ 1965-2024 bbox (committed evidence/usgs_quakes.json): "
                        "dist-to-nearest, prior-count<=50km, years-since (cap 60); ref = slide "
                        "year else rain_year else 2024; strictly-before (no leakage).")
    man["features"] = feats
    MANIFEST.write_text(json.dumps(man, indent=2), encoding="utf-8")
    log("matrix 25 cols; sample stays 22; manifest updated. NEXT: NUMERIC+=3, retrain.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
