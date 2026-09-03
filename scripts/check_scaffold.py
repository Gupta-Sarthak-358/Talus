"""Sept-5 scaffold validator — offline, stdlib only.

Checks the frozen contract:
- fixture JSONs parse + IDs/scores/bands/roles match SCAFFOLD_CONTRACT_SEPT5.md
- roads demo route avoids the at-risk segment
- alerts cover en/hi/ne with fixture:true
- forecast templates include monga-mdl + dahal-144
- feature_matrix.sample.csv has all 17 features + keys in order
Run: python scripts/check_scaffold.py
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data" / "sih26001" / "fixtures"

EXPECTED_SCORES = {"S1": 89, "S2": 78, "S3": 66, "S4": 42}
EXPECTED_BANDS = {"S1": "Critical", "S2": "High", "S3": "Moderate", "S4": "Low"}
EXPECTED_ROLES = {"villager", "district_officer", "state_manager", "rescue_team"}
EXPECTED_FEATURES = [
    "zone_id", "time_window", "slope_angle", "elevation", "aspect",
    "curvature", "twi", "spi", "rainfall_24h_mm", "rainfall_7d_mm",
    "rainfall_30d_mm", "soil_moisture", "ndvi", "lulc", "lithology",
    "distance_to_road", "distance_to_river", "lineament_density",
    "drain_density", "previous_landslide", "event", "evidence_quality",
]

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load_json(name: str):
    p = FIX / name
    if not p.exists():
        fail(f"missing {name}")
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"{name} invalid JSON: {exc}")
        return None


def main() -> int:
    slopes = load_json("slopes.json")
    roads = load_json("roads.json")
    reports = load_json("reports.json")
    alerts = load_json("alerts.json")
    forecast = load_json("forecast.json")

    if slopes:
        zones = {z.get("zone_id"): z for z in slopes.get("zones", [])}
        for zid, score in EXPECTED_SCORES.items():
            z = zones.get(zid)
            if not z:
                fail(f"slopes.json missing {zid}")
                continue
            if z.get("risk_score") != score:
                fail(f"{zid} score {z.get('risk_score')} != frozen {score}")
            if z.get("risk_band") != EXPECTED_BANDS[zid]:
                fail(f"{zid} band {z.get('risk_band')} != frozen {EXPECTED_BANDS[zid]}")
        dec = slopes.get("decisions", {})
        for band, rows in dec.items():
            roles = {r.get("role") for r in rows}
            if roles != EXPECTED_ROLES:
                fail(f"decisions[{band}] roles {sorted(roles)} != {sorted(EXPECTED_ROLES)}")

    if roads:
        segs = {s.get("id"): s for s in roads.get("segments", [])}
        if segs.get("R2", {}).get("status") != "at-risk":
            fail("roads.json R2 must be at-risk (demo avoidance)")
        demo = roads.get("demo_route", {})
        via = demo.get("risk_aware_route", {}).get("via", [])
        if "R2" in via:
            fail("risk_aware_route must avoid R2")
        if demo.get("avoided_segments") != ["R2"]:
            fail("demo_route.avoided_segments must be ['R2']")

    if reports:
        reps = reports.get("reports", [])
        if not reps or reps[0].get("zone_id") not in EXPECTED_SCORES:
            fail("reports.json needs >=1 report with valid zone_id")
        if any("lat" not in r or "lon" not in r for r in reps):
            fail("reports.json entries need lat+lon (geo-tagged)")

    if alerts:
        if alerts.get("fixture") is not True:
            fail("alerts.json fixture must be true (no live SMS in demo)")
        if alerts.get("languages") != ["en", "hi", "ne"]:
            fail("alerts.json languages must be ['en','hi','ne']")

    if forecast:
        tids = {t.get("id") for t in forecast.get("templates", [])}
        if tids != {"monga-mdl", "dahal-144"}:
            fail(f"forecast.json templates {sorted(tids)} != monga-mdl+dahal-144")

    csv_path = FIX / "feature_matrix.sample.csv"
    if not csv_path.exists():
        fail("missing feature_matrix.sample.csv")
    else:
        with csv_path.open(newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))
        if header != EXPECTED_FEATURES:
            fail(f"feature_matrix.sample.csv header mismatch: {header}")

    if not (FIX / "manifest.sample.json").exists():
        fail("missing manifest.sample.json")

    if errors:
        print("SCAFFOLD CHECK FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("SCAFFOLD OK: S1-S4 89/78/66/42, roles, R2-avoidance, en/hi/ne, templates, 17-feature schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
