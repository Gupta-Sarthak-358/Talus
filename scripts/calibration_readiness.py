"""Calibration-readiness audit: can each championship event yield an uncontaminated
daily T-30 -> T history? (SIH26001 Phase IV-B prep — verification only, no modeling.)

Checks per eligible event:
  rain: IMD yearly file present (1901-2024 on disk)
  soil: v09.2 CCI daily era (>=1979)
  seismic: USGS catalog (historical, queried at replay build)
  satellite: S2A era (>=2015-06-23) else L8 era (>=2013) else none
  lulc_era: WorldCover static 2020/21 — flag anachronism for pre-2020 events (limitation, not block)
  window_overlap: another championship event within 2km whose T-30 window overlaps
Outputs runs/calibration_readiness.json. Run: mnemo-venv python scripts/calibration_readiness.py
"""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
OUT = REPO / "runs" / "calibration_readiness.json"
S2_START = dt.date(2015, 6, 23)
L8_START = dt.date(2013, 2, 11)


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    d = pd.read_csv(TRACKER)
    e = d[d["eligible_for_championship"].astype(str) == "True"].copy()
    e["dt"] = pd.to_datetime(e["exact_date"])
    rows = []
    for i, r in e.iterrows():
        day = r["dt"].date()
        yy = day.year
        rain = (REPO / f"data/raw/imd/ind{yy}_rfp25.nc").exists()
        # T-30 may cross Jan 1 -> need previous year too
        if (day - dt.timedelta(days=30)).year != yy:
            rain = rain and (REPO / f"data/raw/imd/ind{yy-1}_rfp25.nc").exists()
        soil = yy >= 1979
        sat = "S2" if day >= S2_START else ("L8" if day >= L8_START else "none")
        lulc_flag = "anachronism-static2020" if yy < 2020 else "era-ok"
        ov = []
        for j, q in e.iterrows():
            if i == j:
                continue
            dist = float(2 * 6371000.0 * np.arcsin(np.sqrt(
                np.sin(np.radians(q["lat"] - r["lat"]) / 2) ** 2
                + np.cos(np.radians(r["lat"])) * np.cos(np.radians(q["lat"]))
                * np.sin(np.radians(q["lon"] - r["lon"]) / 2) ** 2)))
            if dist < 2000 and abs((q["dt"] - r["dt"]).days) < 30:
                ov.append(f"{q['slide_no']}({dist:.0f}m)")
        ready = bool(rain and soil and sat != "none")
        rows.append({"slide_no": r["slide_no"], "date": str(r["exact_date"]), "rain": rain,
                     "soil_v092": soil, "seismic": "USGS-catalog", "satellite": sat,
                     "lulc": lulc_flag, "window_overlap": ov,
                     "verdict": "ready" if (ready and not ov) else ("conditional" if ready else "blocked")})
    res = {"n": len(rows), "ready": sum(1 for x in rows if x["verdict"] == "ready"),
           "conditional": sum(1 for x in rows if x["verdict"] == "conditional"),
           "blocked": sum(1 for x in rows if x["verdict"] == "blocked"), "events": rows}
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"ready={res['ready']} conditional={res['conditional']} blocked={res['blocked']}")
    for x in rows:
        if x["verdict"] != "ready" or x["lulc"].startswith("anachronism"):
            log(f"  {x['slide_no']}: {x['verdict']} sat={x['satellite']} lulc={x['lulc']} overlap={x['window_overlap']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
