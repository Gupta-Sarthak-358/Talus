"""Track A v2: priority tiers, precision/provenance statuses, contamination checks (SIH26001).

Reads trackA_candidates.csv, upgrades schema, runs automated contamination checks
on exact rows, writes back + runs/trackA_v2.json. Fuzzy rows keep replay-only status.
Run: mnemo-venv python scripts/trackA_v2.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
OUT = REPO / "runs" / "trackA_v2.json"

LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


STATUS_MAP = {"mined-exact": None}  # set per-row below


def main() -> int:
    d = pd.read_csv(TRACKER)
    # precision status from existing status/date fields
    def precision(r):
        if r["status"] == "mined-exact":
            return "EXACT_MULTI_SOURCE" if r["slide_no"] in (
                "NEWS-DARJ-20150701", "NEWS-NH10-20211020") else "EXACT_VERIFIED"
        if pd.notna(r["month_hint"]) and str(r["month_hint"]).strip():
            return "MONTH_CONFIRMED"
        if int(r["year"]) > 0:
            return "YEAR_ONLY"
        return "UNDATED"
    d["precision_status"] = [precision(r) for _, r in d.iterrows()]

    def priority(r):
        if r["precision_status"].startswith("EXACT"):
            return "mined"
        if r["precision_status"] == "MONTH_CONFIRMED":
            return "A"
        if r["precision_status"] == "YEAR_ONLY":
            return "B"
        return "C"
    d["priority"] = [priority(r) for _, r in d.iterrows()]
    for c in ("source_tier", "contam_geo", "contam_dem", "contam_rain",
              "contam_soil", "contam_sat", "contam_seis", "contam_prox_m"):
        if c not in d.columns:
            d[c] = ""
    d.to_csv(TRACKER, index=False)

    # contamination checks on exact rows only
    mat = pd.read_csv(REPO / "data/sih26001/processed/feature_matrix.training.csv")
    side = pd.read_csv(REPO / "data/sih26001/processed/training_sidecar.csv")
    pla, plo = side["lat"].to_numpy(), side["lon"].to_numpy()
    checks = []
    for i, r in d[d["precision_status"].str.startswith("EXACT")].iterrows():
        la, lo = float(r["lat"]), float(r["lon"])
        dd = pd.Timestamp(r["exact_date"]) if str(r["exact_date"]).strip() else None
        geo = bool(LON0 <= lo <= LON1 and LAT0 <= la <= LAT1)
        dem = bool(88.0 <= lo <= 89.0 and 27.0 <= la <= 28.0)
        rain = True  # IMD national grid; per-year file check below
        try:
            yy = int(str(r["exact_date"])[:4])
            rain = (REPO / f"data/raw/imd/ind{yy}_rfp25.nc").exists()
        except Exception:
            rain = False
        soil = True  # v09.2 deep archive; per-window check at replay build
        sat = "S2-available-check-at-replay"
        # training-positive proximity (reported, not a reject reason)
        sep = float(2 * 6371000.0 * np.arcsin(np.sqrt(
            np.sin(np.radians(pla - la) / 2) ** 2 + np.cos(np.radians(la)) * np.cos(np.radians(pla))
            * np.sin(np.radians(plo - lo) / 2) ** 2)).min())
        d.at["contam_geo"] if False else None
        checks.append({"slide_no": r["slide_no"], "geo": geo, "dem": dem,
                       "rain": rain, "soil": soil, "sat": sat,
                       "train_prox_m": round(sep, 1)})
    for c in checks:
        m = (d["slide_no"] == c["slide_no"])
        d.loc[m, "contam_geo"] = str(c["geo"])
        d.loc[m, "contam_dem"] = str(c["dem"])
        d.loc[m, "contam_rain"] = str(c["rain"])
        d.loc[m, "contam_soil"] = str(c["soil"])
        d.loc[m, "contam_sat"] = str(c["sat"])
        d.loc[m, "contam_prox_m"] = str(c["train_prox_m"])
    d.to_csv(TRACKER, index=False)
    res = {"n": len(d), "exact": int(d["precision_status"].str.startswith("EXACT").sum()),
           "checks": checks}
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    log(f"tracker v2: {len(d)} rows, exact={res['exact']}; checks on {len(checks)} exact rows")
    for c in checks:
        log(f"  {c['slide_no']}: geo={c['geo']} dem={c['dem']} rain={c['rain']} prox={c['train_prox_m']}m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
