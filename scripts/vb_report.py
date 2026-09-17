"""V-B full batch report: manifest + event table + provenance totals + split check.

Reads runs/phase_v/daily_replay/event_*.json + splits/championship_split_v1.json.
Writes runs/phase_v/{reconstruction_manifest.json, event_table.json, audit_full.json}.
Blocking gates: 23/23 events, 138/138 snapshots, temporal assertions, 0 post-event
leakage, split/episode integrity vs frozen manifest. No modeling.
Run (any python): python scripts/vb_report.py
"""
from __future__ import annotations

import glob
import hashlib
import json
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RDIR = REPO / "runs" / "phase_v" / "daily_replay"
SPLIT = REPO / "splits" / "championship_split_v1.json"


def log(m: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


FEATS = ["rainfall_24h_mm", "rainfall_3d_mm", "rainfall_7d_mm", "rainfall_30d_mm",
         "soil_moisture"]


def main() -> int:
    files = sorted(glob.glob(str(RDIR / "event_*.json")))
    events = [json.load(open(f, encoding="utf-8")) for f in files]
    assert len(events) == 23, f"events: {len(events)}"
    snaps = sum(len(e["snapshots"]) for e in events)
    assert snaps == 138, f"snapshots: {snaps}"

    prov: dict = {}
    table, leak, pending_err, terrain_warn = [], 0, [], []
    for e in events:
        row = {"event": e["slide_no"], "episode": e["episode"], "date": e["event_date"],
               "snapshots": len(e["snapshots"]), "leakage": 0, "issues": []}
        for k, v in e["snapshots"].items():
            for f in FEATS:
                o = v[f]
                assert o["observation_timestamp"] <= v["grid_end"], (e["slide_no"], k, f)
                prov.setdefault(f, {}).setdefault(o["provenance"].split(" ")[0], 0)
                prov[f][o["provenance"].split(" ")[0]] += 1
            sp = v["satellite"]
            prov.setdefault("satellite", {}).setdefault(sp["provenance"], 0)
            prov["satellite"][sp["provenance"]] += 1
            for coll, c in sp["collections"].items():
                if "error" in c:
                    pending_err.append(f"{e['slide_no']}/{k}/{coll}")
                for s in ([c["best"]] if c.get("best") else []) + ([c["usable_lt30"]] if c.get("usable_lt30") else []):
                    if s and s[1] > v["grid_end"]:
                        leak += 1
                        row["leakage"] += 1
            for f in ("seismic", "terrain", "disturbance"):
                p = v[f].get("provenance", "?")
                prov.setdefault(f, {}).setdefault(p, 0)
                prov[f][p] += 1
            sm = v["soil_moisture"]["value"]
            assert sm is None or 0.0 <= sm <= 1.0, (e["slide_no"], k, sm)
        t = e["snapshots"]["T"]["terrain"]
        if not (-500 < t["elevation_m"] < 9000 and 0 <= t["slope_deg"] < 90
                and -2 < t["twi"] < 30 and 0 <= t["drain_density"] < 20):
            terrain_warn.append(e["slide_no"])
            row["issues"].append("terrain-range")
        if t["slope_deg"] < 2:
            row["issues"].append("flat-cell-note")
        table.append(row)

    # split-integrity cross-check vs frozen manifest
    man = json.load(open(SPLIT, encoding="utf-8"))
    mside = {r["slide_no"]: r["side"] for r in man["events"]}
    assert set(mside) == {e["slide_no"] for e in events}, "event-id drift"
    d = pd.read_csv(REPO / "data/sih26001/evidence/trackA_candidates.csv")
    ep = d[d["slide_no"].isin(mside)].copy()
    ep["side"] = ep["slide_no"].map(mside)
    assert (ep.groupby("related_episode_id")["side"].nunique() == 1).all(), "episode split!"
    split_ok = True

    code = hashlib.sha256(open(REPO / "scripts/reconstruct_event.py", "rb").read()).hexdigest()[:12]
    manifest = {"contract": "Mantam pilot + upgrades (3d rain, seismic detail, STAC scenes, D8 terrain)",
                "code_sha": code, "events": 23, "snapshots": 138,
                "T_convention": "T-day grid excluded; T shares grid state with T-1"}
    (REPO / "runs" / "phase_v" / "reconstruction_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    pd.DataFrame(table).to_csv(REPO / "runs" / "phase_v" / "event_table.csv", index=False)
    audit = {"coverage": {"events": "23/23", "snapshots": f"{snaps}/138"},
             "temporal_assertions": "PASS", "post_event_leakage": leak,
             "satellite_query_errors": pending_err, "terrain_warnings": terrain_warn,
             "provenance_totals": prov,
             "split_crosscheck": {"episodes_intact": split_ok, "manifest": "championship_split_v1"},
             "verdict": "V-B PASS" if (leak == 0 and not pending_err and not terrain_warn
                                       or (leak == 0 and not pending_err)) else "V-B REVIEW"}
    (REPO / "runs" / "phase_v" / "reconstruction_audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8")
    log(f"events 23/23, snapshots {snaps}/138, leak={leak}, sat_errors={len(pending_err)}, "
        f"terrain_warn={terrain_warn}")
    log("provenance: " + json.dumps(prov))
    log("verdict: " + audit["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
