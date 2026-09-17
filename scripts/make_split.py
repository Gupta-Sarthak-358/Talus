"""Championship split manifest v1 (Phase V-A.2). NO MODELING, NO PERFORMANCE USED.

Assignment rationale (fixed before any held-out scoring):
- episode grouping: same related_episode_id never split (Dipudara pair together);
- chronic-site distribution: 29-Mile hits and Birik/20-Mile recurrences spread across sides;
- temporal realism: both sides span 2015-2024, held-out is NOT the newest-N;
- geography: both sides cover Gangtok/Mangan/Darjeeling/Kalimpong + outliers.
Held-out (10): Mantam-2016, Pubung-2019, 29Mile-Jul21, BirikDara-2022, Yumthang-2022,
20Mile-Sep22 (same episode as Yumthang — integrity over count), Pathing-2022,
Sokpay-2023, Dipudara-pair-2024. Dev (13): the rest.
Writes splits/championship_split_v1.json + asserts constraints.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CHAMP = REPO / "data/sih26001/evidence/championship_events_v1.csv"
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
OUTDIR = REPO / "splits"
OUT = OUTDIR / "championship_split_v1.json"

HELDOUT = {"NEWS-MANTAM-20160813", "NEWS-PUBUNG-20190708", "NEWS-29MILE-20210711",
           "NEWS-BIRIKDARA-20220802", "NEWS-YUMTHANG-20220831", "NEWS-20MILE-20220901",
           "NEWS-PATHING-20221124", "NEWS-SOKPAY-20230326", "NEWS-DIPUDARA-20240820",
           "NEWS-DIPUDARA-20240821"}


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    d = pd.read_csv(TRACKER)
    e = d[d["eligible_for_championship"].astype(str) == "True"].copy()
    assert len(e) == 23, f"pool changed: {len(e)}"
    assert HELDOUT <= set(e["slide_no"]), "held-out id not in pool"
    e["side"] = ["held-out" if s in HELDOUT else "development" for s in e["slide_no"]]
    # constraint 1: episode integrity
    ep = e.groupby("related_episode_id")["side"].nunique()
    assert (ep == 1).all(), f"split episode: {ep[ep > 1]}"
    # constraint 2: chronic-site spread (29-Mile on both sides)
    m29 = e[e["slide_no"].str.contains("29MILE")]
    assert set(m29["side"]) == {"development", "held-out"}, "29-Mile stacked"
    # constraint 3: temporal realism — held-out is not the newest-N
    dev_years = sorted(int(str(x)[:4]) for x in e[e["side"] == "development"]["exact_date"])
    ho_years = sorted(int(str(x)[:4]) for x in e[e["side"] == "held-out"]["exact_date"])
    assert min(ho_years) < 2020 and max(dev_years) == 2024, "temporal stacking"
    # constraint 4: geography both sides (multi-district)
    assert e[e["side"] == "held-out"]["district"].nunique() >= 5
    assert e[e["side"] == "development"]["district"].nunique() >= 5
    manifest = {
        "version": "championship_split_v1", "frozen": "2026-09-18",
        "rule": "no model performance used; constraints asserted in scripts/make_split.py",
        "dev_n": int((e["side"] == "development").sum()),
        "heldout_n": int((e["side"] == "held-out").sum()),
        "dev_years": dev_years, "heldout_years": ho_years,
        "law": "held-out untouchable: no calibration/threshold/OOD/feature decision may use it",
        "events": e[["slide_no", "exact_date", "district", "related_episode_id",
                     "side"]].to_dict("records"),
    }
    OUTDIR.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log(f"dev={manifest['dev_n']} held-out={manifest['heldout_n']} "
        f"ho_years={ho_years} dev_years={dev_years}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
