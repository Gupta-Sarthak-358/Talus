"""Single-process local sensor simulator for the SIH26001 judge-phone demo.

Why local, not Render: Render free-tier cold-starts add 30-60s latency and
cost a second deployment; the hackathon demo is offline-first on one laptop
+ one judge phone. This script ticks deterministic, seeded sensor deltas for
all 12 pilot zones (S1-S4/N1-N4/D1-D4) and writes them where the backend
serves them. No scores, bands, roles, slopes.json, roads.json or contract
are touched — sensor deltas only (see docs/REALTIME_SHOWCASE_MEMO.md).

Outputs (both git-ignored under runs/):
  runs/live_feed.json   latest tick snapshot (served by GET /api/live/feed)
  runs/sim_audit.jsonl  append-only audit trail (served by GET /api/live/audit)

Committed honest sample: data/sih26001/fixtures/live_feed.sample.json
(backend falls back to it when the simulator is not running).

Run (any python, stdlib only):
  python scripts/local_sensor_sim.py --once            # single tick (default tick 0)
  python scripts/local_sensor_sim.py --ticks 120 --interval 5   # live demo loop
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "runs"
FEED = RUNS / "live_feed.json"
AUDIT = RUNS / "sim_audit.jsonl"
SEED = 42
ALERT_RAIN_1H_MM = 20.0  # demo threshold; an audit event is logged, nothing auto-closes

ZONES = ["S1", "S2", "S3", "S4", "N1", "N2", "N3", "N4", "D1", "D2", "D3", "D4"]
# Corridor monsoon baselines (mm/h scale, stated demo assumption — NOT measurements).
BASE_RAIN = {"S": 2.5, "N": 3.5, "D": 4.5}


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def tick_snapshot(tick: int) -> dict:
    rng = random.Random(SEED + tick)
    zones = {}
    for zid in ZONES:
        base = BASE_RAIN[zid[0]]
        # slow diurnal-ish wave + jitter, deterministic per (seed, tick, zone)
        wave = base * (1.0 + 0.6 * __import__("math").sin(tick / 6.0 + ord(zid[1]) * 0.7))
        rain_1h = round(max(0.0, wave + rng.gauss(0, 0.8)), 2)
        soil_delta = round(min(0.05, max(-0.05, rng.gauss(0.002, 0.008))), 4)
        battery = round(max(15.0, 98.0 - tick * 0.05 - rng.random() * 2.0), 1)
        rssi = round(-70.0 + rng.gauss(0, 6), 1)
        # seeded occasional stale node proves the UI handles gaps honestly
        status = "stale" if rng.random() < 0.03 else ("low-batt" if battery < 20 else "ok")
        zones[zid] = {
            "rain_1h_mm": rain_1h,
            "soil_delta": soil_delta,
            "battery_pct": battery,
            "rssi_dbm": rssi,
            "status": status,
        }
    return {
        "mode": "simulated",
        "sim": "scripts/local_sensor_sim.py v1",
        "seed": SEED,
        "tick": tick,
        "issued_at": now_iso(),
        "zones": zones,
    }


def audit_event(record: dict) -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def write_feed(snap: dict) -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    FEED.write_text(json.dumps(snap, indent=2), encoding="utf-8")


def run_tick(tick: int) -> dict:
    snap = tick_snapshot(tick)
    write_feed(snap)
    audit_event({"tick": tick, "issued_at": snap["issued_at"], "event": "tick",
                 "detail": f"sim tick {tick}: 12 zones, seed {SEED}"})
    for zid, z in snap["zones"].items():
        if z["rain_1h_mm"] >= ALERT_RAIN_1H_MM:
            audit_event({"tick": tick, "issued_at": snap["issued_at"], "event": "demo-threshold",
                         "detail": f"{zid} rain_1h {z['rain_1h_mm']}mm >= {ALERT_RAIN_1H_MM}mm (simulated; no auto-action)"})
    return snap


def main() -> int:
    ap = argparse.ArgumentParser(description="TALUS local sensor simulator (seeded, offline)")
    ap.add_argument("--ticks", type=int, default=1, help="ticks to run (default 1)")
    ap.add_argument("--interval", type=float, default=5.0, help="seconds between ticks (default 5)")
    ap.add_argument("--from-tick", type=int, default=0, help="starting tick (default 0)")
    ap.add_argument("--once", action="store_true", help="single tick and exit")
    args = ap.parse_args()
    n = 1 if args.once else max(1, args.ticks)
    for i in range(n):
        tick = args.from_tick + i
        snap = run_tick(tick)
        wettest = max(snap["zones"].items(), key=lambda kv: kv[1]["rain_1h_mm"])
        print(f"tick {tick}: wettest {wettest[0]} {wettest[1]['rain_1h_mm']}mm/h "
              f"-> runs/live_feed.json (+ audit)", flush=True)
        if i < n - 1:
            time.sleep(max(0.0, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
