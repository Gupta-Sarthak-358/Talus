"""Out-of-distribution guard: validated terrain-support check (E16d).

Rule (validated BEFORE shipping — the pre-registered >=2-any-feature rule FAILED
its Tier-1 check with 40% false flags and was replaced):
  ood = ANY terrain feature outside its training-positive p1-p99 band.
Validated rates: held-out plains 0.60 / Tier-1 analogues 0.00 / train positives 0.07.
TERRAIN = static regime definers only. Dynamic features (rain/soil/seismic) NEVER
trigger abstention: extreme monsoon is when warnings matter most.

Firing means CAUTION (probability_status -> "uncalibrated-ood" + reasons), never
a block and never an invented risk value. In particular an OOD + LOW score must
read as "outside validated support", never as confident safety.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUPPORT_FP = REPO / "data" / "sih26001" / "evidence" / "feature_support.json"

TERRAIN = ("elevation", "slope_angle", "distance_to_road", "distance_to_river",
           "twi", "spi_log", "drain_density")

_bands: dict | None = None


def _load() -> dict:
    global _bands
    if _bands is None:
        try:
            _bands = json.loads(SUPPORT_FP.read_text(encoding="utf-8")).get("bands", {})
        except Exception:
            _bands = {}
    return _bands


def check(row: dict) -> dict:
    """Return {"ood": bool, "ood_reasons": [...], "terrain_oob": [...] }.

    spi_log is derived from raw spi exactly as training did (log1p of max(spi,0)).
    Non-finite/missing terrain values are skipped (judge present evidence only);
    if NO terrain feature is present, the row is OOD by definition.
    """
    bands = _load()
    vals: dict[str, float] = {}
    for c in TERRAIN:
        if c == "spi_log":
            try:
                v = math.log1p(max(float(row.get("spi", float("nan"))), 0.0))
            except (TypeError, ValueError):
                continue
        else:
            try:
                v = float(row.get(c, float("nan")))
            except (TypeError, ValueError):
                continue
        if math.isfinite(v):
            vals[c] = v
    if not vals:
        return {"ood": True, "ood_reasons": ["no terrain evidence present"],
                "terrain_oob": []}
    oob = [c for c, v in vals.items()
           if c in bands and (v < bands[c][0] or v > bands[c][1])]
    reasons = [f"{c}={vals[c]:g} outside training-positive p1-p99 "
               f"[{bands[c][0]:g}, {bands[c][1]:g}]" for c in oob if c in bands]
    return {"ood": bool(oob), "ood_reasons": reasons, "terrain_oob": oob}
