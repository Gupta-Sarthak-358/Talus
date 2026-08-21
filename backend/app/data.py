from __future__ import annotations

import math
from datetime import datetime, timezone

from .schemas import CRACK_SEVERITIES, Features, RISK_BANDS

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

INITIAL_FEATURES = {
    "A": {
        "rainfall_24h_mm": 20.0, "rainfall_7d_mm": 90.0, "slope_angle_deg": 35.0,
        "slope_height_m": 12.0, "rock_type": "lateritic_soil", "crack_density": 0.10,
        "crack_severity": "normal", "blast_frequency_per_week": 1.0,
        "blast_vibration_ppv_mms": 4.0, "days_since_inspection": 3,
        "prior_incident": 0, "groundwater_proxy": 0.20,
    },
    "B": {
        "rainfall_24h_mm": 35.0, "rainfall_7d_mm": 140.0, "slope_angle_deg": 58.0,
        "slope_height_m": 45.0, "rock_type": "sandstone", "crack_density": 0.42,
        "crack_severity": "moderate", "blast_frequency_per_week": 2.0,
        "blast_vibration_ppv_mms": 9.5, "days_since_inspection": 12,
        "prior_incident": 0, "groundwater_proxy": 0.35,
    },
    "C": {
        "rainfall_24h_mm": 25.0, "rainfall_7d_mm": 110.0, "slope_angle_deg": 42.0,
        "slope_height_m": 18.0, "rock_type": "clayey_sandstone", "crack_density": 0.22,
        "crack_severity": "minor", "blast_frequency_per_week": 1.0,
        "blast_vibration_ppv_mms": 5.5, "days_since_inspection": 7,
        "prior_incident": 0, "groundwater_proxy": 0.28,
    },
    "D": {
        "rainfall_24h_mm": 22.0, "rainfall_7d_mm": 95.0, "slope_angle_deg": 38.0,
        "slope_height_m": 15.0, "rock_type": "lateritic_soil", "crack_density": 0.15,
        "crack_severity": "normal", "blast_frequency_per_week": 1.0,
        "blast_vibration_ppv_mms": 4.5, "days_since_inspection": 5,
        "prior_incident": 0, "groundwater_proxy": 0.24,
    },
}

INITIAL_RISK = {
    "A": {"score": 22, "confidence": 0.81},
    "B": {"score": 48, "confidence": 0.78},
    "C": {"score": 35, "confidence": 0.79},
    "D": {"score": 28, "confidence": 0.80},
}

INITIAL_HISTORY = {
    "A": [("2026-08-19T08:00:00Z", 22)],
    "B": [("2026-08-19T09:00:00Z", 48)],
    "C": [("2026-08-19T08:00:00Z", 35)],
    "D": [("2026-08-19T08:00:00Z", 28)],
}

GRAPH = {
    "A": ["B", "C"],
    "B": ["A", "D"],
    "C": ["A", "D"],
    "D": ["B", "C"],
}

SEVERITY_WEIGHT = {"normal": 0.0, "minor": 3.0, "moderate": 6.0, "severe": 10.0, "critical": 14.0}

SCALE = 0.735


def mock_contributions(f: Features) -> dict[str, float]:
    return {
        "rainfall_24h_mm": min(1.0, f.rainfall_24h_mm / 80.0) * 40.0,
        "rainfall_7d_mm": min(1.0, f.rainfall_7d_mm / 250.0) * 20.0,
        "slope_angle_deg": min(1.0, max(0.0, (f.slope_angle_deg - 35.0) / 40.0)) * 20.0,
        "crack_density": f.crack_density * 30.0,
        "crack_severity": SEVERITY_WEIGHT[f.crack_severity],
        "blast_frequency_per_week": min(1.0, f.blast_frequency_per_week / 8.0) * 6.0,
        "blast_vibration_ppv_mms": min(1.0, f.blast_vibration_ppv_mms / 25.0) * 6.0,
        "days_since_inspection": min(1.0, f.days_since_inspection / 30.0) * 6.0,
        "prior_incident": 8.0 if f.prior_incident else 0.0,
        "groundwater_proxy": f.groundwater_proxy * 8.0,
    }


def risk_band(score: int) -> str:
    if score >= 80:
        return "Critical"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Moderate"
    if score >= 15:
        return "Low"
    return "Very Low"


def compute_risk(f: Features) -> tuple[int, list[dict]]:
    contribs = mock_contributions(f)
    score = int(round(sum(contribs.values()) * SCALE))
    score = max(0, min(100, score))
    top = sorted(contribs.items(), key=lambda kv: kv[1], reverse=True)[:4]
    return score, [{"feature": k, "shap_value": round(v, 1)} for k, v in top]


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
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.features: dict[str, Features] = {z: Features(**INITIAL_FEATURES[z]) for z in INITIAL_FEATURES}
        self.risk: dict[str, int] = {z: INITIAL_RISK[z]["score"] for z in INITIAL_RISK}
        self.confidence: dict[str, float] = {z: INITIAL_RISK[z]["confidence"] for z in INITIAL_RISK}
        self.history: dict[str, list[tuple[str, int]]] = {
            z: [h for h in INITIAL_HISTORY[z]] for z in INITIAL_HISTORY
        }
        self.updated_at: dict[str, str] = {z: now_iso() for z in INITIAL_RISK}

    def trend(self, zone_id: str) -> tuple[str, bool]:
        return detect_trend(self.history[zone_id])

    def recompute(self, zone_id: str, features: Features) -> None:
        self.features[zone_id] = features
        score, _ = compute_risk(features)
        self.risk[zone_id] = score
        self.history[zone_id].append((now_iso(), score))
        self.history[zone_id] = self.history[zone_id][-12:]
        self.updated_at[zone_id] = now_iso()


store = ZoneStore()