#!/usr/bin/env python3
"""
NGEN Gangtok pilot — minimal honest validator for the frozen sample fixtures.

What it checks (beginner-friendly):
- CSV is exactly the frozen 22-column schema, no extra columns, <=20 rows, S1-S4 present, IDs unique.
- Required fields are not empty, numeric fields are numbers, categorical fields are text.
- No uppercase FILL placeholder remains (honesty check).
- Manifest is valid JSON, declares Gangtok pilot + EPSG:4326, and does not claim not_available sources as real.
- Always warns that non-IMD values are STUB/demo (S1 rainfall is REAL-verified, see NGEN_PROVENANCE_S1.md).

Usage:
  python scripts/validate_ngen_sample.py
  python scripts/validate_ngen_sample.py --csv data/sih26001/fixtures/feature_matrix.sample.csv --manifest data/sih26001/fixtures/manifest.sample.json

Exit 0 = valid, non-zero = invalid. Uses only Python standard library.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# Frozen schema — must match docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md + scripts/check_scaffold.py
EXPECTED_FEATURES = [
    "zone_id", "time_window", "slope_angle", "elevation", "aspect",
    "curvature", "twi", "spi", "rainfall_24h_mm", "rainfall_7d_mm",
    "rainfall_30d_mm", "soil_moisture", "ndvi", "lulc", "lithology",
    "distance_to_road", "distance_to_river", "lineament_density",
    "drain_density", "previous_landslide", "event", "evidence_quality",
]

# Numeric fields — must be parseable as numbers.
# soil_moisture 0-1, ndvi -1 to 1, previous_landslide/event 0/1 are checked more strictly where noted.
NUMERIC_FIELDS = [
    "slope_angle", "elevation", "aspect", "curvature", "twi", "spi",
    "rainfall_24h_mm", "rainfall_7d_mm", "rainfall_30d_mm",
    "soil_moisture", "ndvi", "distance_to_road", "distance_to_river",
    "lineament_density", "drain_density", "previous_landslide", "event",
]

# Categorical fields — must be non-empty text (not just whitespace, not a number-only string that looks like missing).
CATEGORICAL_FIELDS = ["lulc", "lithology", "evidence_quality"]

REQUIRED_ZONES = {"S1", "S2", "S3", "S4"}
MAX_ROWS = 20

DEFAULT_CSV = Path("data/sih26001/fixtures/feature_matrix.sample.csv")
DEFAULT_MANIFEST = Path("data/sih26001/fixtures/manifest.sample.json")


def fail(msg: str, errors: list[str]) -> None:
    errors.append(msg)


def validate_csv(csv_path: Path, errors: list[str]) -> list[dict] | None:
    if not csv_path.exists():
        fail(f"CSV missing: {csv_path} (expected data/sih26001/fixtures/feature_matrix.sample.csv)", errors)
        return None

    text = csv_path.read_text(encoding="utf-8")
    if "FILL" in text:
        fail(f"CSV contains uppercase placeholder 'FILL' — replace with honest null/STUB note (found in {csv_path})", errors)

    try:
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames
            if header is None:
                fail(f"CSV header missing in {csv_path}", errors)
                return None
            # 2 & 3: exact schema, reject unexpected columns
            if header != EXPECTED_FEATURES:
                fail(
                    f"CSV header mismatch in {csv_path}\n"
                    f"  Expected (22 cols): {EXPECTED_FEATURES}\n"
                    f"  Found ({len(header)} cols): {header}\n"
                    f"  Hint: do not add, remove, rename, or reorder columns.",
                    errors,
                )
                # continue to also check rows for better messages, but header is blocker
            rows = list(reader)
    except Exception as exc:
        fail(f"CSV could not be read: {csv_path}: {exc}", errors)
        return None

    # 4: no more than 20 rows
    if len(rows) > MAX_ROWS:
        fail(f"CSV has {len(rows)} rows, but maximum allowed is {MAX_ROWS} (file: {csv_path})", errors)
    if len(rows) == 0:
        fail(f"CSV has no data rows (file: {csv_path})", errors)
        return rows

    # 5 & 6: S1-S4 present, IDs unique
    zone_ids = [r.get("zone_id", "").strip() for r in rows]
    missing = REQUIRED_ZONES - set(zone_ids)
    if missing:
        fail(f"CSV missing required zone(s): {sorted(missing)} — S1, S2, S3, S4 must all be present", errors)
    if len(zone_ids) != len(set(zone_ids)):
        dups = [z for z in set(zone_ids) if zone_ids.count(z) > 1]
        fail(f"CSV has duplicate zone_id(s): {dups} — each zone_id must be unique", errors)

    # 7: required fields not empty (every cell in the 22 cols should not be empty/whitespace)
    for i, row in enumerate(rows, start=2):  # start=2 accounts for header line 1
        for col in EXPECTED_FEATURES:
            val = row.get(col, "")
            if val is None or str(val).strip() == "":
                fail(f"Row {i} zone {row.get('zone_id','?')}: required field '{col}' is empty", errors)

    # 8: numeric fields contain valid numbers
    for i, row in enumerate(rows, start=2):
        zid = row.get("zone_id", "?")
        for col in NUMERIC_FIELDS:
            val = str(row.get(col, "")).strip()
            if val == "":
                continue  # already flagged as empty above
            try:
                num = float(val)
            except ValueError:
                fail(f"Row {i} zone {zid}: field '{col}' should be a number, but found '{val}'", errors)
                continue
            # tighter checks for a few bounded fields — beginner-friendly range hints
            if col == "soil_moisture" and not (0 <= num <= 1):
                fail(f"Row {i} zone {zid}: soil_moisture should be 0 to 1, found {num}", errors)
            if col == "ndvi" and not (-1 <= num <= 1):
                fail(f"Row {i} zone {zid}: ndvi should be -1 to 1, found {num}", errors)
            if col in ("previous_landslide", "event") and num not in (0, 1, 0.0, 1.0):
                fail(f"Row {i} zone {zid}: {col} should be 0 or 1, found '{val}'", errors)

    # 9: categorical fields contain valid text (not empty, not purely numeric when text is expected)
    for i, row in enumerate(rows, start=2):
        zid = row.get("zone_id", "?")
        for col in CATEGORICAL_FIELDS:
            val = str(row.get(col, "")).strip()
            if val == "":
                continue
            # evidence_quality has a small controlled vocabulary — warn if unexpected, but allow dated/approx variants
            if col == "evidence_quality" and val not in ("dated", "dated-only-negative", "approximate", "season-window"):
                # not a hard fail — some teams use custom tags — but flag if it looks like a number
                try:
                    float(val)
                    fail(f"Row {i} zone {zid}: evidence_quality should be text like 'dated', found numeric '{val}'", errors)
                except ValueError:
                    pass
            if col in ("lulc", "lithology"):
                # should be text codes like BUILT, FOREST, schist — flag if it is just a number
                try:
                    float(val)
                    fail(f"Row {i} zone {zid}: {col} should be text (e.g. 'BUILT' or 'schist'), found numeric '{val}'", errors)
                except ValueError:
                    pass

    return rows


def validate_manifest(manifest_path: Path, errors: list[str]) -> dict | None:
    if not manifest_path.exists():
        fail(f"Manifest missing: {manifest_path} (expected data/sih26001/fixtures/manifest.sample.json)", errors)
        return None

    text = manifest_path.read_text(encoding="utf-8")
    if "FILL" in text:
        fail(f"Manifest contains uppercase placeholder 'FILL' — replace with null/[]/status:not_available (found in {manifest_path})", errors)

    try:
        data = json.loads(text)
    except Exception as exc:
        fail(f"Manifest is not valid JSON: {manifest_path}: {exc}", errors)
        return None

    # 12: declares Gangtok pilot and EPSG:4326
    pilot = str(data.get("pilot", ""))
    crs = str(data.get("crs", ""))
    if "Gangtok" not in pilot:
        fail(f"Manifest pilot should mention 'Gangtok' (found pilot='{pilot}' in {manifest_path})", errors)
    if "EPSG:4326" not in crs:
        fail(f"Manifest crs should be 'EPSG:4326' (found crs='{crs}' in {manifest_path})", errors)

    # 13: does not claim unavailable sources as real
    sources = data.get("sources", {})
    if not isinstance(sources, dict):
        fail(f"Manifest 'sources' should be an object (found {type(sources).__name__})", errors)
    else:
        for name, meta in sources.items():
            if not isinstance(meta, dict):
                continue
            status = meta.get("status")
            if status == "not_available":
                # honest manifest should have date null, tiles empty, export null where applicable
                if "date" in meta and meta["date"] not in (None,):
                    fail(
                        f"Manifest sources[{name}] status is 'not_available' but date is '{meta['date']}' — should be null",
                        errors,
                    )
                if "tiles" in meta:
                    tiles = meta["tiles"]
                    if not isinstance(tiles, list) or len(tiles) != 0:
                        fail(
                            f"Manifest sources[{name}] status is 'not_available' but tiles is {tiles!r} — should be []",
                            errors,
                        )
                if "export" in meta and meta["export"] not in (None,):
                    fail(
                        f"Manifest sources[{name}] status is 'not_available' but export is '{meta['export']}' — should be null",
                        errors,
                    )
                if "extract" in meta and meta["extract"] not in (None,):
                    fail(
                        f"Manifest sources[{name}] status is 'not_available' but extract is '{meta['extract']}' — should be null",
                        errors,
                    )
                if "version" in meta and isinstance(meta["version"], str) and "FILL" in meta["version"]:
                    fail(
                        f"Manifest sources[{name}].version still contains 'FILL' — use null or honest version string",
                        errors,
                    )

    # checksums should be {} when nothing is available yet — flag FILL leftovers
    checksums = data.get("checksums", {})
    if isinstance(checksums, dict):
        for k, v in checksums.items():
            if isinstance(v, str) and "FILL" in v:
                fail(f"Manifest checksums[{k}] contains 'FILL' — should be {{}} or honest sha256", errors)
    # sampling ratio should be null when not_available
    sampling = data.get("sampling", {})
    if isinstance(sampling, dict) and sampling.get("ratio") is not None and isinstance(sampling.get("ratio"), str) and "FILL" in str(sampling.get("ratio")):
        fail("Manifest sampling.ratio contains 'FILL' — should be null", errors)

    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="NGEN Gangtok pilot — honest sample validator (STUB/demo safe)")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="path to feature_matrix.sample.csv")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="path to manifest.sample.json")
    args = parser.parse_args()

    errors: list[str] = []

    print(f"Checking CSV: {args.csv}")
    print(f"Checking manifest: {args.manifest}")
    print()

    validate_csv(args.csv, errors)
    validate_manifest(args.manifest, errors)

    # 14: always print STUB/demo warning — never hide that this is not scientific data
    print()
    print("=" * 72)
    print("WARNING: This sample is PARTLY stub: S1-S4 rainfall (24h/7d/30d),")
    print("road/river distances, NDVI, LULC, all six DEM derivatives, soil")
    print("moisture, lithology, lineament and labels are REAL/PROXY-verified")
    print("(IMD/Overpass/Sentinel-2/WorldCover/USGS/CCI/NESAC/Bhuvan/Bhusanket);")
    print("drain density is PROXY (measured window).")
    print("See docs/sih26001/NGEN_PROVENANCE_S1.md.")
    print("=" * 72)
    print()

    if errors:
        print(f"VALIDATION FAILED: {len(errors)} issue(s) found:")
        for i, e in enumerate(errors, 1):
            print(f"  {i}. {e}")
        print()
        print("Fix the issues above, then re-run: python scripts/validate_ngen_sample.py")
        return 1

    print("NGEN SAMPLE OK: schema 22 cols, S1-S4 present, <=20 rows, honest manifest, no FILL.")
    print("Next: run tests with  python -m unittest discover -s tests -p \"test_*.py\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
