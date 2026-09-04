from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from . import model_service
from .schemas import Features

# Sept-5 scaffold: fixture dir + loaders. Zone identity (names, centers,
# graph) comes from slopes.json — the frozen contract. Do not hand-edit
# values here; edit the fixture + contract + validator instead.
# Multi-location: locations.json registry (gangtok live, lachung/darjeeling preview)
FIX = Path(__file__).resolve().parents[2] / "data" / "sih26001" / "fixtures"


def _load_json(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def _load_json_optional(name: str):
    p = FIX / name
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


_SLOPES = _load_json("slopes.json")
_FIXTURE_ZONES: dict[str, dict] = {z["zone_id"]: z for z in _SLOPES["zones"]}
_FIXTURE_HISTORIES: dict[str, list[dict]] = _SLOPES.get("histories", {})

# Multi-location fixtures (if locations.json exists)
_LOCATIONS_CFG = _load_json_optional("locations.json")
_FIXTURE_BY_LOCATION: dict[str, dict[str, dict]] = {"gangtok": _FIXTURE_ZONES}
_HISTORIES_BY_LOCATION: dict[str, dict[str, list[dict]]] = {"gangtok": _FIXTURE_HISTORIES}
if _LOCATIONS_CFG:
    for loc in _LOCATIONS_CFG.get("locations", []):
        loc_id = loc.get("id")
        if loc_id == "gangtok":
            continue
        f = loc.get("file")
        if f:
            try:
                data = _load_json(f)
                _FIXTURE_BY_LOCATION[loc_id] = {z["zone_id"]: z for z in data.get("zones", [])}
                _HISTORIES_BY_LOCATION[loc_id] = data.get("histories", {})
            except Exception:
                pass


def _load_feature_rows() -> dict[str, dict]:
    """4-row NGEN-format sample (17 NER features + keys) keyed by zone."""
    rows: dict[str, dict] = {}
    with (FIX / "feature_matrix.sample.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parsed: dict = {}
            for k, v in row.items():
                try:
                    parsed[k] = int(v)
                    continue
                except ValueError:
                    pass
                try:
                    parsed[k] = float(v)
                except ValueError:
                    parsed[k] = v
            rows[row["zone_id"]] = parsed
    # Mirror gangtok rows to preview zones for API compatibility (same 17-feature schema)
    if "S1" in rows:
        for loc_id in _FIXTURE_BY_LOCATION:
            if loc_id == "gangtok":
                continue
            for zid in _FIXTURE_BY_LOCATION[loc_id]:
                if zid not in rows:
                    # clone S1 row and patch zone_id
                    clone = dict(rows["S1"])
                    clone["zone_id"] = zid
                    rows[zid] = clone
    return rows


_FEATURE_ROWS = _load_feature_rows()

ZONE_NAMES = {zid: z["name"] for zid, z in _FIXTURE_ZONES.items()}

ZONE_CENTERS = {
    zid: {"lat": z["geometry"]["lat"], "lng": z["geometry"]["lon"]}
    for zid, z in _FIXTURE_ZONES.items()
}


def _box(lat: float, lon: float, d: float = 0.002) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[
            [lon - d, lat - d], [lon + d, lat - d], [lon + d, lat + d],
            [lon - d, lat + d], [lon - d, lat - d],
        ]],
    }


ZONE_GEOMETRY = {
    zid: _box(c["lat"], c["lng"]) for zid, c in ZONE_CENTERS.items()
}

# Per-location derived maps
ZONE_NAMES_BY_LOCATION: dict[str, dict[str, str]] = {}
ZONE_CENTERS_BY_LOCATION: dict[str, dict[str, dict]] = {}
ZONE_GEOMETRY_BY_LOCATION: dict[str, dict[str, dict]] = {}
for loc_id, zones in _FIXTURE_BY_LOCATION.items():
    ZONE_NAMES_BY_LOCATION[loc_id] = {zid: z["name"] for zid, z in zones.items()}
    ZONE_CENTERS_BY_LOCATION[loc_id] = {zid: {"lat": z["geometry"]["lat"], "lng": z["geometry"]["lon"]} for zid, z in zones.items()}
    ZONE_GEOMETRY_BY_LOCATION[loc_id] = {zid: _box(c["lat"], c["lng"]) for zid, c in ZONE_CENTERS_BY_LOCATION[loc_id].items()}

# Fixture topology: S1:[S2,S3], S2:[S1,S3], S3:[S1,S2,S4], S4:[S3].
# Routing S1->S4 can avoid S2 via S3.
GRAPH = {
    "S1": ["S2", "S3"],
    "S2": ["S1", "S3"],
    "S3": ["S1", "S2", "S4"],
    "S4": ["S3"],
}

# Per-location graphs (same topology, remapped ids)
GRAPH_BY_LOCATION: dict[str, dict[str, list[str]]] = {"gangtok": GRAPH}
for loc_id, zones in _FIXTURE_BY_LOCATION.items():
    if loc_id == "gangtok":
        continue
    # assume zones ordered like S1-S4 → N1-N4 etc, keep same connectivity
    zids = sorted(zones.keys())
    # Build mapping S1->first, S2->second, etc
    gangtok_ids = ["S1","S2","S3","S4"]
    remap = {gangtok_ids[i]: zids[i] for i in range(min(len(gangtok_ids), len(zids)))}
    g = {}
    for src, dsts in GRAPH.items():
        if src in remap:
            g[remap[src]] = [remap.get(d, d) for d in dsts if d in remap]
    GRAPH_BY_LOCATION[loc_id] = g


def fixture_zone(zone_id: str, location: str = "gangtok") -> dict | None:
    """Raw fixture row for zone (location-aware)."""
    zones = _FIXTURE_BY_LOCATION.get(location) or _FIXTURE_ZONES
    return zones.get(zone_id)


def fixture_missing_evidence(zone_id: str, location: str = "gangtok") -> list[str]:
    z = ( _FIXTURE_BY_LOCATION.get(location) or _FIXTURE_ZONES).get(zone_id)
    return list(z.get("missing_evidence", [])) if z else []


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


def _edge_cost(start: str, end: str, risk: dict[str, int], risk_weight: float, location: str = "gangtok") -> float:
    centers = ZONE_CENTERS_BY_LOCATION.get(location) or ZONE_CENTERS
    d = distance(centers[start], centers[end])
    exposure = risk.get(end, 0)
    return d * (1.0 + risk_weight * exposure / 100.0)


def _dijkstra(start: str, end: str, risk: dict[str, int], risk_weight: float, location: str = "gangtok") -> tuple[list[str], float, int]:
    centers = ZONE_CENTERS_BY_LOCATION.get(location) or ZONE_CENTERS
    graph = GRAPH_BY_LOCATION.get(location) or GRAPH
    nodes = list(centers)
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
        for nxt in graph.get(current, []):
            alt = dist[current] + _edge_cost(current, nxt, risk, risk_weight, location)
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
    """Sept-5 scaffold: zone states seeded from frozen fixtures
    (slopes.json scores/confidence/histories + feature_matrix.sample.csv),
    never from the v1 model. v1 model calls remain available for
    explanation fallback only. Now location-aware."""

    def __init__(self, location: str = "gangtok") -> None:
        self.location = location
        self.reset()

    def reset(self) -> None:
        zones = _FIXTURE_BY_LOCATION.get(self.location) or _FIXTURE_ZONES
        histories = _HISTORIES_BY_LOCATION.get(self.location) or _FIXTURE_HISTORIES
        self.features: dict[str, dict] = {}
        self.risk: dict[str, int] = {}
        self.confidence: dict[str, float] = {}
        self.history: dict[str, list[tuple[str, int]]] = {}
        self.trend_label: dict[str, str] = {}
        self.updated_at: dict[str, str] = {}
        stamp = now_iso()
        for zid, z in zones.items():
            self.features[zid] = dict(_FEATURE_ROWS.get(zid, {}))
            self.risk[zid] = int(z["risk_score"])
            self.confidence[zid] = float(z["confidence"])
            hist = [
                (p["t"], int(p["risk_score"]))
                for p in histories.get(zid, [])
            ] or [(stamp, int(z["risk_score"]))]
            self.history[zid] = hist
            self.trend_label[zid] = z.get("trend", "stable")
            self.updated_at[zid] = stamp

    def trend(self, zone_id: str) -> tuple[str, bool]:
        _, rapid = detect_trend(self.history[zone_id])
        return self.trend_label.get(zone_id, "stable"), rapid

    def recompute(self, zone_id: str, features: Features) -> None:
        self.features[zone_id] = features
        svc = model_service.get_service()
        pred = svc.predict(zone_id, features.model_dump())
        self.risk[zone_id] = pred["score"]
        self.confidence[zone_id] = pred["confidence"]
        self.history[zone_id].append((now_iso(), pred["score"]))
        self.history[zone_id] = self.history[zone_id][-12:]
        self.updated_at[zone_id] = now_iso()


# Default store (gangtok) for backward compat + per-location stores
store = ZoneStore("gangtok")
stores: dict[str, ZoneStore] = {"gangtok": store}
for loc_id in _FIXTURE_BY_LOCATION:
    if loc_id not in stores:
        stores[loc_id] = ZoneStore(loc_id)

def get_store(location: str = "gangtok") -> ZoneStore:
    return stores.get(location) or store
