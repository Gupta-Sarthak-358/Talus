"""Risk-weighted road-edge cost calculation for Talus routing."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from numbers import Real
from typing import Hashable


def risk_weighted_edge_cost(
    length: Real,
    adjacent_zone_ids: Iterable[Hashable],
    zone_risks: Mapping[Hashable, Real],
    alpha: Real,
) -> float:
    """Return an edge cost using Talus's specified risk-weighting formula.

    ``cost = length * (1 + alpha * max(adjacent zone risks))``

    Zone risks are prototype scores in the inclusive range 0--100.  Every
    adjacent zone must have a corresponding risk value.
    """
    _require_finite_number(length, "length")
    _require_finite_number(alpha, "alpha")

    if length < 0:
        raise ValueError("length cannot be negative")
    if alpha < 0:
        raise ValueError("alpha cannot be negative")

    zone_ids = tuple(adjacent_zone_ids)
    if not zone_ids:
        raise ValueError("at least one adjacent zone is required")

    risks: list[Real] = []
    for zone_id in zone_ids:
        if zone_id not in zone_risks:
            raise ValueError(f"missing risk for adjacent zone {zone_id!r}")

        risk = zone_risks[zone_id]
        _require_finite_number(risk, f"risk for adjacent zone {zone_id!r}")
        if not 0 <= risk <= 100:
            raise ValueError("zone risks must be between 0 and 100")
        risks.append(risk)

    return float(length * (1 + alpha * max(risks)))


def _require_finite_number(value: object, name: str) -> None:
    """Raise a clear error unless ``value`` is a finite real number."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
