"""
Tests for scripts/validate_ngen_sample.py — stdlib unittest, no external deps.

Each test uses a temporary copy of the real fixtures (tempfile), so the
real data/sih26001/fixtures files are never modified.
"""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

# Import the validator module directly (stdlib only)
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_ngen_sample as v  # noqa: E402


REAL_CSV = ROOT / "data/sih26001/fixtures/feature_matrix.sample.csv"
REAL_MANIFEST = ROOT / "data/sih26001/fixtures/manifest.sample.json"


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)
    return header, rows


def write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


class TestValidateNGENSample(unittest.TestCase):
    def test_valid_sample_passes(self):
        """The committed sample should be valid (STUB/demo is allowed, FILL is not)."""
        errors: list[str] = []
        v.validate_csv(REAL_CSV, errors)
        v.validate_manifest(REAL_MANIFEST, errors)
        self.assertEqual(errors, [], f"Expected no errors for valid sample, got: {errors}")

    def test_invalid_missing_column(self):
        """A header missing one required column should fail."""
        header, rows = read_csv(REAL_CSV)
        header2 = [c for c in header if c != "slope_angle"]  # drop one
        rows2 = [{k: r[k] for k in header2} for r in rows]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            write_csv(p, header2, rows2)
            errors: list[str] = []
            v.validate_csv(p, errors)
            self.assertTrue(any("header mismatch" in e for e in errors), f"Should flag header mismatch: {errors}")

    def test_missing_S1(self):
        """CSV without S1 should fail (S1-S4 required)."""
        header, rows = read_csv(REAL_CSV)
        rows2 = [r for r in rows if r["zone_id"] != "S1"]
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            write_csv(p, header, rows2)
            errors: list[str] = []
            v.validate_csv(p, errors)
            self.assertTrue(any("missing required zone" in e and "S1" in e for e in errors), f"Should flag missing S1: {errors}")

    def test_duplicate_zone_id(self):
        """Duplicate zone_id should fail."""
        header, rows = read_csv(REAL_CSV)
        rows2 = rows + [dict(rows[0])]  # duplicate S1
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            write_csv(p, header, rows2)
            errors: list[str] = []
            v.validate_csv(p, errors)
            self.assertTrue(any("duplicate zone_id" in e for e in errors), f"Should flag duplicate: {errors}")

    def test_uppercase_FILL_placeholder(self):
        """Uppercase FILL anywhere in CSV should fail (honesty check)."""
        header, rows = read_csv(REAL_CSV)
        rows2 = [dict(r) for r in rows]
        rows2[0]["elevation"] = "FILL"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            write_csv(p, header, rows2)
            # Also need to ensure raw text contains FILL — write_csv will write FILL literally
            errors: list[str] = []
            v.validate_csv(p, errors)
            self.assertTrue(any("FILL" in e for e in errors), f"Should flag FILL placeholder: {errors}")

    def test_excessive_row_count(self):
        """More than 20 rows should fail."""
        header, rows = read_csv(REAL_CSV)
        # repeat rows to exceed 20
        rows2 = (rows * 6)[:21]  # 21 rows
        # make zone_ids unique to avoid duplicate error masking the count check
        for i, r in enumerate(rows2):
            r["zone_id"] = f"S{i+10}"
        # put back S1-S4 so presence check does not hide row-count check
        rows2[0]["zone_id"] = "S1"
        rows2[1]["zone_id"] = "S2"
        rows2[2]["zone_id"] = "S3"
        rows2[3]["zone_id"] = "S4"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            write_csv(p, header, rows2)
            errors: list[str] = []
            v.validate_csv(p, errors)
            self.assertTrue(any("maximum allowed is 20" in e for e in errors), f"Should flag row count: {errors}")

    def test_invalid_numeric_value(self):
        """A non-numeric value in a numeric column should fail."""
        header, rows = read_csv(REAL_CSV)
        rows2 = [dict(r) for r in rows]
        rows2[0]["slope_angle"] = "not_a_number"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            write_csv(p, header, rows2)
            errors: list[str] = []
            v.validate_csv(p, errors)
            self.assertTrue(any("should be a number" in e for e in errors), f"Should flag invalid numeric: {errors}")

    def test_invalid_manifest(self):
        """Manifest with FILL or missing pilot should fail."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            p.write_text('{"pilot":"Nowhere","crs":"EPSG:4326","sources":{},"sampling":{},"checksums":{}}', encoding="utf-8")
            errors: list[str] = []
            v.validate_manifest(p, errors)
            self.assertTrue(any("Gangtok" in e for e in errors), f"Should flag missing Gangtok pilot: {errors}")

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            data = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
            data["sources"]["imd_gridded"]["date"] = "FILL"  # reintroduce FILL
            p.write_text(json.dumps(data), encoding="utf-8")
            errors = []
            v.validate_manifest(p, errors)
            self.assertTrue(any("FILL" in e for e in errors), f"Should flag FILL in manifest: {errors}")

    def test_incorrect_CRS_or_pilot(self):
        """Wrong CRS or pilot should fail."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            data = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
            data["crs"] = "EPSG:3857"
            p.write_text(json.dumps(data), encoding="utf-8")
            errors: list[str] = []
            v.validate_manifest(p, errors)
            self.assertTrue(any("EPSG:4326" in e for e in errors), f"Should flag wrong CRS: {errors}")

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            data = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
            data["pilot"] = "Mumbai cluster"
            p.write_text(json.dumps(data), encoding="utf-8")
            errors = []
            v.validate_manifest(p, errors)
            self.assertTrue(any("Gangtok" in e for e in errors), f"Should flag wrong pilot: {errors}")

    def test_not_available_source_claiming_date(self):
        """A source with status not_available but a real date should fail (honesty)."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.json"
            data = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
            data["sources"]["era5_soil"]["date"] = "2024-01-01"  # claims real date while not_available
            p.write_text(json.dumps(data), encoding="utf-8")
            errors: list[str] = []
            v.validate_manifest(p, errors)
            self.assertTrue(any("not_available" in e and "date" in e for e in errors), f"Should flag dishonest not_available: {errors}")


if __name__ == "__main__":
    unittest.main()
