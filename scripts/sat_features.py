"""M1-A satellite evidence features per championship event (Phase V-D prep).

S1 GRD: same-relative-orbit + same-direction VV pair (late <= T-1, baseline in
[T-60,T-30]); GCP-geocoded window means (annotation XML grid, bilinear);
dB differences (relative; calibration approximately cancels). VH bonus if present.
Optical: best-usable (cloud<30) S2/L8 pair, NDVI change; else MISSING.
No bulk downloads: STAC queries + annotation XMLs + COG/window range reads only.
Outputs runs/phase_v/m1/sat_features.json. Run (py311): python scripts/sat_features.py
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

os.environ["AWS_NO_SIGN_REQUEST"] = "YES"
REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
OUT = REPO / "runs" / "phase_v" / "m1" / "sat_features.json"
STAC = "https://earth-search.aws.element84.com/v1/search"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def stac(coll, lon, lat, start, end, limit=20):
    b = {"collections": [coll], "intersects": {"type": "Point", "coordinates": [lon, lat]},
         "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z", "limit": limit}
    req = urllib.request.Request(STAC, data=json.dumps(b).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=40)).get("features", [])


def gcps(annotation_url):
    xml = urllib.request.urlopen(annotation_url, timeout=60).read().decode()
    root = ET.fromstring(xml)
    pts = []
    for g in root.findall(".//geolocationGridPoint"):
        pts.append((int(g.findtext("line")), int(g.findtext("pixel")),
                    float(g.findtext("latitude")), float(g.findtext("longitude")),
                    float(g.findtext("incidenceAngle"))))
    return pts


def interp_gcps(pts, lat, lon):
    arr = np.array(pts)
    d2 = (arr[:, 2] - lat) ** 2 + (arr[:, 3] - lon) ** 2
    i = int(np.argmin(d2))
    # local bilinear on nearest 2x2 in (line,pixel) index space via grid structure
    lines = np.unique(arr[:, 0])
    li = int(np.argmin(np.abs(lines - arr[i, 0])))
    li0, li1 = max(0, li - 1), min(len(lines) - 1, li + 1)
    sel = arr[(arr[:, 0] >= lines[li0]) & (arr[:, 0] <= lines[li1])]
    px = np.unique(sel[:, 1])
    pj = int(np.argmin(np.abs(px - arr[i, 1])))
    pj0, pj1 = max(0, pj - 1), min(len(px) - 1, pj + 1)
    q = sel[(sel[:, 1] >= px[pj0]) & (sel[:, 1] <= px[pj1])]
    # inverse-distance fallback (robust to irregular grids)
    w = 1.0 / (np.maximum((q[:, 2] - lat) ** 2 + (q[:, 3] - lon) ** 2, 1e-12))
    return float(np.sum(w * q[:, 1]) / np.sum(w)), float(np.sum(w * q[:, 0]) / np.sum(w)), \
        float(np.sum(w * q[:, 4]) / np.sum(w))


def s1_mean(tiff_url, lat, lon, half_deg=0.005):
    import rasterio
    base = tiff_url.rsplit("/measurement/", 1)[0]
    if base.startswith("s3://"):
        bucket, key = base[5:].split("/", 1)
        base = f"https://{bucket}.s3.amazonaws.com/{key}"
    pol = "vv" if "iw-vv" in tiff_url else "vh"
    pts = gcps(base + f"/annotation/iw-{pol}.xml")
    px, ln, inc = interp_gcps(pts, lat, lon)
    with rasterio.open("/vsis3/" + tiff_url.replace("s3://", "")) as src:
        r0, r1 = max(0, int(ln - 60)), int(ln + 60)
        c0, c1 = max(0, int(px - 60)), int(px + 60)
        w = src.read(1, window=((r0, r1), (c0, c1))).astype(float)
    # ~60px = 600m half-side at 10m; restrict to ~1km box around center
    cy, cx = w.shape[0] // 2, w.shape[1] // 2
    w = w[max(0, cy - 50):cy + 50, max(0, cx - 50):cx + 50]
    w = np.where(w <= 0, np.nan, w)
    assert np.isfinite(w).sum() > 100, "S1 window empty"
    return float(np.nanmean(w)), float(inc)


def cog_mean(href, lat, lon, half_deg=0.005):
    import rasterio
    url = "/vsicurl/" + href if href.startswith("http") else href
    with rasterio.open(url) as src:
        assert src.crs and src.crs.to_epsg() == 4326, f"unexpected CRS {src.crs}"
        rr, cc = src.index(lon, lat)
        res = abs(src.transform[0])
        h = max(2, int(half_deg / res))
        w = src.read(1, window=((max(0, rr - h), rr + h + 1), (max(0, cc - h), cc + h + 1))).astype(float)
    w = np.where(w <= 0, np.nan, w)
    assert np.isfinite(w).sum() > 10, "COG window empty"
    return float(np.nanmean(w))


def main() -> int:
    d = pd.read_csv(TRACKER)
    e = d[d["eligible_for_championship"].astype(str) == "True"]
    out = {}
    for _, r in e.iterrows():
        sid, lat, lon = r["slide_no"], float(r["lat"]), float(r["lon"])
        T = pd.Timestamp(r["exact_date"]).date()
        res: dict = {"event": sid, "T": str(T)}
        # --- S1 pair ---
        try:
            cands = stac("sentinel-1-grd", lon, lat, T - dt.timedelta(days=60), T - dt.timedelta(days=1))
            late = [f for f in cands if f["properties"]["datetime"][:10] <= str(T - dt.timedelta(days=1))]
            late = sorted(late, key=lambda f: f["properties"]["datetime"], reverse=True)
            done = False
            for L in late:
                lp = L["properties"]
                bl = [f for f in cands
                      if f["properties"]["datetime"][:10] <= str(T - dt.timedelta(days=30))
                      and f["properties"].get("sat:relative_orbit") == lp.get("sat:relative_orbit")
                      and f["properties"].get("sat:orbit_state") == lp.get("sat:orbit_state")
                      and "vv" in f["assets"] and "VV" in (lp.get("sar:polarizations") or ["VV"])]
                if not bl:
                    continue
                B = sorted(bl, key=lambda f: f["properties"]["datetime"], reverse=True)[0]
                lv, linc = s1_mean(L["assets"]["vv"]["href"], lat, lon)
                bv, _ = s1_mean(B["assets"]["vv"]["href"], lat, lon)
                feat = {"s1_dvv_db": round(float(10 * np.log10(lv / bv)), 2),
                        "s1_base_vv_db": round(float(10 * np.log10(bv)), 2),
                        "s1_late": L["id"][:32], "s1_base": B["id"][:32],
                        "s1_rel_orbit": lp.get("sat:relative_orbit"),
                        "s1_incidence": round(linc, 1),
                        "s1_dt_days": (pd.Timestamp(lp["datetime"][:10]).date()
                                       - pd.Timestamp(B["properties"]["datetime"][:10]).date()).days,
                        "s1_dvh_db": None, "provenance": "REAL"}
                if "vh" in L["assets"] and "vh" in B["assets"]:
                    lvv, _ = s1_mean(L["assets"]["vh"]["href"], lat, lon)
                    bvv, _ = s1_mean(B["assets"]["vh"]["href"], lat, lon)
                    feat["s1_dvh_db"] = round(float(10 * np.log10(lvv / bvv)), 2)
                res["s1"] = feat
                done = True
                break
            if not done:
                res["s1"] = {"provenance": "MISSING-no-pair", "reason": "no same-track VV pair"}
        except Exception as ex:
            res["s1"] = {"provenance": "PENDING-error", "error": str(ex)[:120]}
        # --- optical NDVI pair ---
        try:
            opt = []
            for coll, red, nir in (("sentinel-2-l2a", "red", "nir"),
                                   ("landsat-c2-l2", "red", "nir08")):
                for f in stac(coll, lon, lat, T - dt.timedelta(days=90), T - dt.timedelta(days=1)):
                    cl = float(f["properties"].get("eo:cloud_cover", 100))
                    if cl < 30 and red in f["assets"] and nir in f["assets"]:
                        opt.append((f["properties"]["datetime"][:10], cl, f["assets"][red]["href"],
                                    f["assets"][nir]["href"]))
            opt.sort(reverse=True)
            late_o = next((o for o in opt if o[0] <= str(T - dt.timedelta(days=1))), None)
            base_o = next((o for o in opt if o[0] <= str(T - dt.timedelta(days=30))), None)
            if late_o and base_o and late_o != base_o:
                def ndvi(o):
                    r_ = cog_mean(o[2], lat, lon)
                    n_ = cog_mean(o[3], lat, lon)
                    return (n_ - r_) / (n_ + r_) if (n_ + r_) > 0 else float("nan")
                ln, bn = ndvi(late_o), ndvi(base_o)
                assert np.isfinite(ln) and np.isfinite(bn), "NDVI non-finite"
                res["optical"] = {"ndvi_change": round(float(ln - bn), 3),
                                  "late_ndvi": round(float(ln), 3),
                                  "late_date": late_o[0], "base_date": base_o[0],
                                  "provenance": "REAL"}
            else:
                res["optical"] = {"provenance": "MISSING-no-pair"}
        except Exception as ex:
            res["optical"] = {"provenance": "PENDING-error", "error": str(ex)[:120]}
        out[sid] = res
        log(f"{sid}: s1={res['s1'].get('s1_dvv_db', res['s1']['provenance'])} "
            f"opt={res['optical'].get('ndvi_change', res['optical']['provenance'])}")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
