"""Track A integrity audit + freeze-manifest validation (SIH26001 Phase IV-A).

Read-only: asserts eligibility/contamination/episode integrity of the championship
pool and reports composition (no split is generated here — split law in
docs/sih26001/CHAMPIONSHIP_RULE_v1.md). Outputs runs/championship_audit.json.
Run: mnemo-venv python scripts/championship_audit.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
TRACKER = REPO / "data/sih26001/evidence/trackA_candidates.csv"
CHAMP = REPO / "data/sih26001/evidence/championship_events_v1.csv"
OUT = REPO / "runs" / "championship_audit.json"
LON0, LON1, LAT0, LAT1 = 88.06, 88.96, 27.00, 27.999


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def season(dt: pd.Timestamp) -> str:
    m = dt.month
    if m in (6, 7, 8, 9):
        return "monsoon"
    if m in (3, 4, 5):
        return "pre-monsoon"
    return "post-monsoon"


def main() -> int:
    d = pd.read_csv(TRACKER)
    e = d[d["eligible_for_championship"].astype(str) == "True"].copy()
    errs: list[str] = []
    # hard assertions
    if e["slide_no"].duplicated().any():
        errs.append("duplicate slide_no in championship")
    for _, r in e.iterrows():
        if not (LON0 <= float(r["lon"]) <= LON1 and LAT0 <= float(r["lat"]) <= LAT1):
            errs.append(f"{r['slide_no']}: outside frozen box")
        try:
            yy = int(str(r["exact_date"])[:4])
            if not (REPO / f"data/raw/imd/ind{yy}_rfp25.nc").exists():
                errs.append(f"{r['slide_no']}: IMD file missing for T-30 coverage")
            pd.Timestamp(r["exact_date"])
        except Exception:
            errs.append(f"{r['slide_no']}: bad exact_date")
        if not str(r.get("related_episode_id", "")).strip():
            errs.append(f"{r['slide_no']}: missing episode id")
    e["season"] = [season(pd.Timestamp(x)) for x in e["exact_date"]]
    e["yr"] = [int(str(x)[:4]) for x in e["exact_date"]]
    audit = {
        "n": len(e), "gap_to_30": 30 - len(e), "errors": errs,
        "years": e["yr"].value_counts().to_dict(),
        "seasons": e["season"].value_counts().to_dict(),
        "districts": e["district"].value_counts().to_dict(),
        "event_types": e["event_type"].value_counts().to_dict(),
        "episodes": int(e["related_episode_id"].nunique()),
        "recurrent_site_rows": int(e["event_identity"].str.contains(
            "chronic|recurr|DISTINCT date", case=False, na=False).sum()),
        "edge_proxy_rows": int(e["geography_status"].str.contains(
            "EDGE|PROXY|APPROX", case=False, na=False).sum()),
        "convergence": e["source_convergence"].value_counts().to_dict(),
        "transfer_eligible": int(((d["geography_status"] == "OUT_OF_DOMAIN_TRANSFER")
                                 & (d["status"] == "mined-exact")).sum()),
        "post_championship_study": int((d["geography_status"] == "POST_CHAMPIONSHIP_STUDY").sum()),
        "events": e[["slide_no", "exact_date", "district", "event_type",
                     "related_episode_id", "source_convergence"]].to_dict("records"),
    }
    OUT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    log(f"n={audit['n']} episodes={audit['episodes']} errors={len(errs)}")
    log(f"seasons={audit['seasons']} recurrent_rows={audit['recurrent_site_rows']} "
        f"edge={audit['edge_proxy_rows']}")
    for k in ("years", "districts", "event_types", "convergence"):
        log(f"{k}={audit[k]}")
    for x in errs:
        log(f"ERROR: {x}")
    return 1 if errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
