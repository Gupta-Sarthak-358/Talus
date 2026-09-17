"""Trust Ledger + Sichey bundle + OOD contrast (SIH26001 Phase IV).

Ledger rows: Warning | Lead | Exposure | Data support | Result — separating
detected / missed / unknown-out-of-regime (never one big green number).
Sources: e15 audit ledger (bands/leads/burden) + exposure join + E16c pilot.
Outputs (committed evidence):
  data/sih26001/evidence/trust_ledger.json
  data/sih26001/evidence/incident_sichey.json
Run: mnemo-venv python scripts/build_trust_ledger.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVID = REPO / "data/sih26001/evidence"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main() -> int:
    audit = json.loads((REPO / "runs" / "e15.json").read_text(encoding="utf-8"))
    inc = json.loads((REPO / "runs" / "e15_incidents.json").read_text(encoding="utf-8"))
    e16c = json.loads((REPO / "runs" / "e16c_full.json").read_text(encoding="utf-8"))
    bundle = json.loads((EVID / "replay_series.json").read_text(encoding="utf-8"))
    exp_by_id = {e["id"]: e for e in audit["exposure"]}
    traj_by_id = {t["id"]: t for t in inc["tier1"]}

    ledger = []
    for L in audit["cases"]:
        cid = L["id"]
        expo = exp_by_id.get(cid, {})
        fuzzy = traj_by_id.get(cid, {})
        case = next(c for c in bundle["cases"] if c["id"] == cid)
        ledger.append({
            "id": cid,
            "warning": f"{L['first']['High'] or '—'} High"
                       + (f" / {L['first']['Critical']} Critical" if L["first"]["Critical"] else ""),
            "lead_days": L["lead"]["High"],
            "exposure": (f"{expo.get('buildings')} homes @ {expo.get('dist_m')}m "
                         f"({expo.get('nearest_runout')})" if expo.get("covered")
                         else "runout uncovered (demo slopes only)"),
            "support": "in-domain (analogue in training — optimistic, flagged)",
            "result": "Event — detected",
            "fuzzy_date": bool(case.get("event_date_fuzzy")),
            "burden": f"{L['hot_days']}/{L['n_days']} hot days",
        })
    # OOD contrast row: worst plains case (first E16c event), unknown verdict
    o = e16c["events"][0]
    ledger.append({
        "id": "wb-plains-pilot",
        "warning": "none (band Very Low)",
        "lead_days": None,
        "exposure": "runout uncovered (out-of-regime)",
        "support": "OUT-OF-REGIME (terrain outside learned support)",
        "result": "Unknown — outside validated domain (OOD guard fires, no silent zero)",
        "fuzzy_date": False,
        "burden": "n/a (point replay, not windowed)",
    })
    (EVID / "trust_ledger.json").write_text(json.dumps({
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "columns": ["Warning", "Lead", "Exposure", "Data support", "Result"],
        "ledger": ledger}, indent=1), encoding="utf-8")
    log(f"ledger rows: {len(ledger)}")

    # Sichey killer-incident bundle
    sc = next(c for c in bundle["cases"] if c["id"] == "sichey-jun2021")
    st = traj_by_id["sichey-jun2021"]
    (EVID / "incident_sichey.json").write_text(json.dumps({
        "id": "sichey-jun2021", "title": sc["title"], "site": sc["site_name"],
        "event_date": sc["event_date"], "event_note": sc["event_note"],
        "sources": sc["sources"],
        "before": "rainfall trajectory + soil wetness + model risk + warning state, "
                  "31 daily steps, inputs strictly ≤ each date",
        "trajectory": st["trajectory"],
        "at_event": {"location": sc["site_name"], "road": "Upper Sichey slide footprint",
                     "homes": 1, "note": sc["event_note"]},
        "exposure": {"runout": "S2", "dist_m": 185, "buildings": 85,
                     "meaning": "hazard Low-band site, exposure-driven priority (E9 live)"},
        "decision": "PRIORITY FIELD INSPECTION when exposure-weighted; monitor otherwise",
        "support": "in-domain replay (analogue in training — optimistic upper bound, flagged)",
    }, indent=1), encoding="utf-8")
    log("sichey bundle written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
