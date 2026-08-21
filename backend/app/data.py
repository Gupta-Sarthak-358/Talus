from __future__ import annotations

import math
from datetime import datetime, timezone

from . import model_service
from .schemas import Features

ZONE_NAMES = {
    "A": "Zone A — SE bench",
    "B": "Zone B — NW bench",
    "C": "Zone C — SW bench",
    "D": "Zone D — NE bench",
}

ZONE_GEOMETRY = {
    "A": {"type": "Polygon", "coordinates": [[[80.10, 20.50], [80.13, 20.50], [80.13, 20.52], [80.10, 20.52], [80.10, 20.50]]]},
    "B": {"type": "Polygon", "coordinates": [[[80.15, 20.53], [80.18, 20.53], [80.18, 20.55], [80.15, 20.55], [80.15, 20.53]]]},
    "C": {"type": "Polygon", "coordinates": [[[80.10, 20.55], [80.13, 20.55], [80.13, 20.57], [80.10, 20.57], [80.10, 20.55]]]},
    "D": {"type": "Polygon", "coordinates": [[[80.15, 20.57], [80.18, 20.57], [80.18, 20.59], [80.15, 20.59], [80.15, 20.57]]]},
}

ZONE_CENTERS = {
    "A": {"lat": 20.51, "lng": 80.115},
    "B": {"lat": 20.54, "lng": 80.165},
    "C": {"lat": 20.56, "lng": 80.115},
    "D": {"lat": 20.58, "lng": 80.165},
}

GRAPH = {
    "A": ["B", "C"],
    "B": ["A", "D"],
    "C": ["A", "D"],
    "D": ["B", "C"],
}


def risk_band(score: int) -> str:
    """Frozen FoS-derived thresholds (docs/ML_MODEL_CARD_V1.md)."""
    return model_service.band_for_score(score)


def compute_risk(zone_letter: str, f: Features) -> tuple[int, list[dict]]:
    svc = model_service.get_service()
    payload = f.model_dump()
    pred = svc.predict(zone_letter, payload)
    expl = svc.explain(zone_letter, payload)
    return pred["score"], expl["contributions"]


def missing_evidence(f: Features) -> list[str]:
    """FR-03: evidence gaps derived from feature provenance (03_DATA_PLAN),
    plus any fields that arrive null. PPV is modeled (NIRM attenuation), the
    groundwater proxy is a wetting-memory transient, and crack features are
    sampler states -- none are in-situ sensor telemetry."""
    gaps = []
    if f.blast_vibration_ppv_mms is None:
        gaps.append("blast_vibration_ppv_mms")
    gaps += [
        "in_situ_vibration_telemetry (PPV is attenuation-modeled)",
        "piezometer_groundwater_sensor (proxy is rainfall-derived)",
        "crack_imagery_cv_feed (severity from inspection sampler)",
    ]
    return gaps


def apply_overrides(current: Features, overrides: dict) -> Features:
    unknown = sorted(set(overrides) - set(Features.model_fields))
    if unknown:
        raise ValueError(f"Unknown override fields: {unknown}")
    return Features(**{**current.model_dump(), **overrides})


def detect_trend(history: list[tuple[str, int]]) -> tuple[str, bool]:
    if len(history) < 3:
        return "stable", False
    last3 = [score for _, score in history[-3:]]
    deltas = [b - a for a, b in zip(last3[:-1], last3[1:])]
    rapid = all(d >= 8 for d in deltas) or sum(deltas) >= 25
    if rapid:
        return "rapidly_increasing", True
    if last3[-1] > last3[0]:
        return "rising", False
    return "stable", False


def distance(a: dict, b: dict) -> float:
    return math.sqrt((a["lat"] - b["lat"]) ** 2 + (a["lng"] - b["lng"]) ** 2)


def _edge_cost(start: str, end: str, risk: dict[str, int], risk_weight: float) -> float:
    d = distance(ZONE_CENTERS[start], ZONE_CENTERS[end])
    exposure = risk.get(end, 0)
    return d * (1.0 + risk_weight * exposure / 100.0)


def _dijkstra(start: str, end: str, risk: dict[str, int], risk_weight: float) -> tuple[list[str], float, int]:
    nodes = list(ZONE_CENTERS)
    dist = {n: math.inf for n in nodes}
    prev = {n: None for n in nodes}
    dist[start] = 0.0
    unvisited = set(nodes)
    while unvisited:
        current = min(unvisited, key=lambda n: dist[n])
        if dist[current] == math.inf:
            break
        unvisited.discard(current)
        if current == end:
            break
        for nxt in GRAPH.get(current, []):
            alt = dist[current] + _edge_cost(current, nxt, risk, risk_weight)
            if alt < dist[nxt]:
                dist[nxt] = alt
                prev[nxt] = current
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    max_risk = max((risk.get(n, 0) for n in path), default=0)
    return path, round(dist[end], 2), max_risk


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def interpolate(points: list[dict]) -> list[dict]:
    if len(points) < 2:
        return points
    out = []
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        mid = {"lat": round((a["lat"] + b["lat"]) / 2, 5), "lng": round((a["lng"] + b["lng"]) / 2, 5)}
        out.append(a)
        out.append(mid)
    out.append(points[-1])
    return out


class ZoneStore:
    """Zone states bootstrapped from the frozen model on real corpus rows
    (last day of held-out world seed 91), never hardcoded constants."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        svc = model_service.get_service()
        states = svc.latest_zone_states(seed=91)
        self.features: dict[str, Features] = {}
        self.risk: dict[str, int] = {}
        self.confidence: dict[str, float] = {}
        self.history: dict[str, list[tuple[str, int]]] = {}
        self.updated_at: dict[str, str] = {}
        stamp = now_iso()
        for z, f in states.items():
            self.features[z] = Features(**f)
            pred = svc.predict(z, f)
            self.risk[z] = pred["score"]
            self.confidence[z] = pred["confidence"]
            self.history[z] = [(stamp, pred["score"])]
            self.updated_at[z] = stamp

    def trend(self, zone_id: str) -> tuple[str, bool]:
        return detect_trend(self.history[zone_id])

    def recompute(self, zone_id: str, features: Features) -> None:
        self.features[zone_id] = features
        svc = model_service.get_service()
        pred = svc.predict(zone_id, features.model_dump())
        self.risk[zone_id] = pred["score"]
        self.confidence[zone_id] = pred["confidence"]
        self.history[zone_id].append((now_iso(), pred["score"]))
        self.history[zone_id] = self.history[zone_id][-12:]
        self.updated_at[zone_id] = now_iso()


store = ZoneStore()