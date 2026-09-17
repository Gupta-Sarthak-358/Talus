"""E16c: held-out out-of-zone dynamic preview (SIH26001).

10 northernmost held-out Darjeeling-district events (hills-fringe, most comparable
regime): event-year JJAS-peak rain (IMD local) + year-window soil (v09.2 local) +
seismic recompute (ref=event year) + effective-rain vs E14 DARJ bands.
Terrain/optical/OSM need Copernicus tiles + STAC scenes (queued, specified below).
No model scoring (terrain unavailable) — tests threshold generalisation only.
Outputs: runs/e16c.json. Run: mnemo-venv python scripts/e16c_heldout_preview.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "runs" / "e16c.json"

LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    import build_training_matrix as B
    import event_rain_upgrade as ER
    import event_soil_upgrade as ES
    pos = B.load_positives()
    inside = ((pos["lon"] >= LON0) & (pos["lon"] <= LON1)
              & (pos["lat"] >= LAT0) & (pos["lat"] <= LAT1)).to_numpy()
    held = pos[~inside].reset_index(drop=True)
    cand = held[(held["district"] == "Darjeeling") & (held["year"] >= 1978)].copy()
    cand = cand.sort_values("lat", ascending=False).head(10).reset_index(drop=True)
    log(f"held-out Darjeeling dated>=1978: {(held['district'] == 'Darjeeling').sum()}; "
        f"pilot northernmost 10 lat {cand['lat'].min():.3f}-{cand['lat'].max():.3f}")

    quakes = json.loads((REPO / "data/sih26001/evidence/usgs_quakes.json").read_text(encoding="utf-8"))["events"]
    qlat = np.array([q["lat"] for q in quakes])
    qlon = np.array([q["lon"] for q in quakes])
    qyr = np.array([q["year"] for q in quakes])
    ref_stack, ref_lat, ref_lon, _ = ES.window_grid(2024, [f"2024-06-{d:02d}" for _, d in ES.WIN])
    ref_spatial = float(np.nanmean(ref_stack))

    res: dict = {"events": [], "bands": {"DARJ_eff_med": 527, "note": "E14 south candidate bands (matrix regime)"}}
    for _, r in cand.iterrows():
        la, lo, yy = float(r["lat"]), float(r["lon"]), int(r["year"])
        g30, g7, g1, alat, alon = ER.year_grids(yy)
        ri, ci = ER.nearest_idx(alat, alon, np.array([la]), np.array([lo]))
        r30, r7, r1 = round(float(g30[ri[0], ci[0]]), 1), round(float(g7[ri[0], ci[0]]), 1), round(float(g1[ri[0], ci[0]]), 1)
        stack, salat, salon, n = ES.window_grid(yy, [f"{yy}-06-{d:02d}" for _, d in ES.WIN])
        if n and salat is not None:
            sri, sci = ES.nearest_idx(salat, salon, np.array([la]), np.array([lo]))
            sm = ES.cell_means(stack, sri, sci)
            smv = round(float(np.clip(sm[0] if not np.isnan(sm[0]) else ref_spatial, 0, 1)), 4)
            ssrc = "event-year-window-soil"
        else:
            smv, ssrc = ref_spatial, "quasistatic-v092-fallback"
        d = 2 * 6371.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(qlat - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(qlat))
            * np.sin(np.radians(qlon - lo) / 2) ** 2))
        hit = (qyr < yy) & (d <= 50.0)
        eff = round(r7 + 0.3 * r30, 1)
        res["events"].append({
            "slide_no": r["slide_no"], "lat": round(la, 4), "lon": round(lo, 4), "year": yy,
            "rain24": r1, "rain7": r7, "rain30": r30, "eff": eff,
            "soil": smv, "soil_source": ssrc,
            "seismic_n50": int(hit.sum()),
            "eff_vs_darj_med": round(eff - 527, 1),
            "terrain": "PENDING (outside n27_e088; needs Copernicus tile + hydro graft)",
            "optical": "PENDING (needs pre-event STAC scene search)",
            "osm": "PENDING (needs small Overpass queries)"})
    effs = [e["eff"] for e in res["events"]]
    res["summary"] = {"n": len(effs), "eff_med": round(float(np.median(effs)), 1),
                      "frac_above_darj_med": round(float(np.mean([e > 527 for e in effs])), 2),
                      "verdict": "dynamic plausibility only; full replay queued behind terrain extraction"}
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"wrote {OUT}: eff_med {res['summary']['eff_med']} vs DARJ 527, "
        f"frac_above {res['summary']['frac_above_darj_med']}")
    for e in res["events"]:
        log(f"  {e['slide_no']} {e['year']} ({e['lat']},{e['lon']}): eff {e['eff']} "
            f"d{e['eff_vs_darj_med']:+.0f} soil {e['soil']} seis_n50 {e['seismic_n50']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
