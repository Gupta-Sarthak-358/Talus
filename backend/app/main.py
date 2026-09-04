from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from routing.comparison import compare_routes
from routing.graph import MineRoadGraph

from . import data
from .schemas import (
    CausalWhatIfRequest,
    CausalWhatIfResponse,
    DecisionResponse,
    ExplanationResponse,
    Features,
    PhotoMeta,
    PredictRequest,
    PredictResponse,
    ReportIn,
    ReportOut,
    ReportReviewIn,
    RouteRequest,
    RouteResponse,
    TemplatesResponse,
    TrendResponse,
    WhatIfRequest,
    WhatIfResponse,
    ZoneDetail,
    ZoneFeaturesResponse,
    ZoneSummary,
)

app = FastAPI(title="Talus Risk API", version="0.1.0")

_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

RISK_WEIGHT = 3.0
# Calibrated so that avoiding a Critical-adjacent detour outweighs the
# +0.6% base-length difference on the canonical A->D corridor
# (deterministic geometry; avoidance holds for alpha >= ~0.13).
ROUTING_ALPHA = 0.2

DECISIONS_BY_BAND = {
    # Sept-5 scaffold: copied verbatim from data/sih26001/fixtures/slopes.json
    # "decisions". Frozen roles: villager | district_officer | state_manager |
    # rescue_team (contract SCAFFOLD_CONTRACT_SEPT5.md §2). Do not invent messages.
    "Critical": [
        {"role": "villager", "message": "Avoid the S1 hillside road for 2 days. Use the valley route.", "action": "avoid-route guidance (Nepali/Hindi/English)", "priority": "immediate"},
        {"role": "district_officer", "message": "Close the S1 stretch, evacuate Tathangchen upper first.", "action": "closure + evacuation coordination", "priority": "high"},
        {"role": "state_manager", "message": "Prioritise S1 over S2–S4. Stage machines at Ranipool.", "action": "resource allocation", "priority": "high"},
        {"role": "rescue_team", "message": "Approach S1 from the south. Do not use the short ridge road.", "action": "risk-aware approach", "priority": "standby"},
    ],
    "High": [
        {"role": "villager", "message": "Avoid the Chandmari road-cut after heavy rain.", "action": "avoid-route guidance", "priority": "high"},
        {"role": "district_officer", "message": "Inspect S2 today, restrict night movement.", "action": "inspection + restriction", "priority": "high"},
        {"role": "state_manager", "message": "Hold one team for S2 if S1 stabilises.", "action": "reserve allocation", "priority": "medium"},
        {"role": "rescue_team", "message": "Standby near S2.", "action": "standby", "priority": "standby"},
    ],
    "Moderate": [
        {"role": "villager", "message": "Caution on Tadong paths during rain.", "action": "awareness", "priority": "normal"},
        {"role": "district_officer", "message": "Schedule S3 inspection this week.", "action": "monitoring", "priority": "normal"},
        {"role": "state_manager", "message": "Monitor S3 trend.", "action": "monitoring", "priority": "normal"},
        {"role": "rescue_team", "message": "No action required.", "action": "none", "priority": "none"},
    ],
    "Low": [
        {"role": "villager", "message": "No restriction for Ranipool.", "action": "none", "priority": "none"},
        {"role": "district_officer", "message": "Routine watch on S4.", "action": "monitoring", "priority": "normal"},
        {"role": "state_manager", "message": "No allocation for S4.", "action": "none", "priority": "none"},
        {"role": "rescue_team", "message": "No action required.", "action": "none", "priority": "none"},
    ],
}

# Multilingual decisions — translations for hi/ne (en is base). Keys are band -> role -> message
DECISIONS_TRANSLATIONS = {
    "hi": {
        "Critical": {
            "villager": "S1 पहाड़ी सड़क 2 दिन तक न लें। घाटी मार्ग का उपयोग करें।",
            "district_officer": "S1 खंड बंद करें, थाथांगचेन ऊपरी क्षेत्र को पहले खाली करें।",
            "state_manager": "S1 को S2–S4 पर प्राथमिकता दें। रानीपूल में मशीनें तैनात करें।",
            "rescue_team": "S1 के दक्षिण से पहुँचें। छोटी रिज सड़क का उपयोग न करें।",
        },
        "High": {
            "villager": "भारी बारिश के बाद चंडमारी रोड-कट से बचें।",
            "district_officer": "आज S2 का निरीक्षण करें, रात में आवाजाही सीमित करें।",
            "state_manager": "यदि S1 स्थिर हो तो S2 के लिए एक टीम आरक्षित रखें।",
            "rescue_team": "S2 के पास स्टैंडबाय रहें।",
        },
        "Moderate": {
            "villager": "बारिश के दौरान ताडोंग पगडंडियों पर सावधानी बरतें।",
            "district_officer": "इस सप्ताह S3 का निरीक्षण निर्धारित करें।",
            "state_manager": "S3 के रुझान पर नजर रखें।",
            "rescue_team": "कोई कार्रवाई आवश्यक नहीं।",
        },
        "Low": {
            "villager": "रानीपूल के लिए कोई प्रतिबंध नहीं।",
            "district_officer": "S4 पर सामान्य निगरानी रखें।",
            "state_manager": "S4 के लिए कोई आवंटन नहीं।",
            "rescue_team": "कोई कार्रवाई आवश्यक नहीं।",
        },
    },
    "ne": {
        "Critical": {
            "villager": "S1 पहाडी बाटो २ दिन नजानुहोस्। उपत्यका बाटो प्रयोग गर्नुहोस्।",
            "district_officer": "S1 खण्ड बन्द गर्नुहोस्, थाथाङचेन माथिल्लो क्षेत्र पहिले खाली गर्नुहोस्।",
            "state_manager": "S1 लाई S2–S4 भन्दा प्राथमिकता दिनुहोस्। रानिपुलमा मेसिन तैनाथ गर्नुहोस्।",
            "rescue_team": "S1 मा दक्षिणबाट पुग्नुहोस्। छोटो रिज बाटो प्रयोग नगर्नुहोस्।",
        },
        "High": {
            "villager": "भारी वर्षा पछि चन्द्रमारी रोड-कटबाट जोगिनुहोस्।",
            "district_officer": "आज S2 निरीक्षण गर्नुहोस्, राति आवतजावत सीमित गर्नुहोस्।",
            "state_manager": "यदि S1 स्थिर भए S2 का लागि एक टोली आरक्षित राख्नुहोस्।",
            "rescue_team": "S2 नजिक स्ट्यान्डबाइ बस्नुहोस्।",
        },
        "Moderate": {
            "villager": "वर्षाको समयमा ताडोङ बाटोमा सावधानी अपनाउनुहोस्।",
            "district_officer": "यो हप्ता S3 निरीक्षण तालिका बनाउनुहोस्।",
            "state_manager": "S3 प्रवृत्ति निगरानी गर्नुहोस्।",
            "rescue_team": "कुनै कार्य आवश्यक छैन।",
        },
        "Low": {
            "villager": "रानिपुलका लागि कुनै प्रतिबन्ध छैन।",
            "district_officer": "S4 मा नियमित निगरानी गर्नुहोस्।",
            "state_manager": "S4 का लागि कुनै आवंटन छैन।",
            "rescue_team": "कुनै कार्य आवश्यक छैन।",
        },
    },
}


def _location_for_zone(zone_id: str) -> str:
    if zone_id.startswith("N"):
        return "lachung"
    if zone_id.startswith("D"):
        return "darjeeling"
    return "gangtok"

def _store_for_zone(zone_id: str):
    return data.get_store(_location_for_zone(zone_id))

def _zone_or_404(zone_id: str) -> None:
    # check all locations (gangtok + preview)
    for store in data.stores.values():
        if zone_id in store.features:
            return
    raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")


def _decisions(zone_id: str, score: int, lang: str = "en") -> list[dict]:
    band = data.risk_band(score)
    rows = DECISIONS_BY_BAND.get(band, DECISIONS_BY_BAND["Moderate"])
    trans = DECISIONS_TRANSLATIONS.get(lang, {}) if lang != "en" else {}
    band_trans = trans.get(band, {}) if trans else {}
    out = []
    for row in rows:
        item = dict(row)
        # Apply translation if available
        if band_trans and row["role"] in band_trans:
            item["message"] = band_trans[row["role"]]
        if zone_id in item["message"]:
            item["message"] = item["message"].replace("Zone B", zone_id)
        out.append(item)
    return out


# NOTE: the v1 single-graph MINE_ROAD_GRAPH was removed 2026-09-05 — routing
# is per-corridor via _road_graphs_for() (full + hazard graphs). The shared
# routing/ lib (graph/search/cost/compare) is untouched.


@app.get("/")
def root():
    return {"service": "Talus Risk API", "docs": "/docs",
            "status": "frozen ML Model v1 (RF, generator v1.4.0) + Scenario Engine v1.5"}


@app.get("/api/zones", response_model=dict)
def list_zones(location: str | None = None):
    # location-aware: ?location=gangtok|lachung|darjeeling (default gangtok for compat)
    # also supports ?zone_id prefix inference; if location omitted but zones include N/D, return requested location's zones
    if location and location in data.stores:
        store = data.get_store(location)
    else:
        store = data.store
    zones = []
    for zid in store.features:
        trend, _ = store.trend(zid)
        zones.append(
            ZoneSummary(
                zone_id=zid,
                risk_score=store.risk[zid],
                risk_band=data.risk_band(store.risk[zid]),
                confidence=store.confidence[zid],
                trend=trend,
            )
        )
    return {"zones": zones, "location": getattr(store, 'location', 'gangtok'),
            "scoring": "live-rf" if getattr(store, 'live_scores', False) else "fixture"}


@app.get("/api/zones/{zone_id}", response_model=ZoneDetail)
def get_zone(zone_id: str):
    _zone_or_404(zone_id)
    store = _store_for_zone(zone_id)
    loc = _location_for_zone(zone_id)
    names = data.ZONE_NAMES_BY_LOCATION.get(loc) or data.ZONE_NAMES
    geoms = data.ZONE_GEOMETRY_BY_LOCATION.get(loc) or data.ZONE_GEOMETRY
    trend, _ = store.trend(zone_id)
    return ZoneDetail(
        zone_id=zone_id,
        name=names.get(zone_id, zone_id),
        geometry=geoms.get(zone_id, {"type":"Polygon","coordinates":[]}),
        risk_score=store.risk[zone_id],
        risk_band=data.risk_band(store.risk[zone_id]),
        confidence=store.confidence[zone_id],
        trend=trend,
        updated_at=store.updated_at[zone_id],
    )


@app.get("/api/zones/{zone_id}/features", response_model=ZoneFeaturesResponse)
def get_features(zone_id: str):
    _zone_or_404(zone_id)
    store = _store_for_zone(zone_id)
    loc = _location_for_zone(zone_id)
    feats = store.features[zone_id]
    if data.fixture_zone(zone_id, loc) is not None:
        missing = data.fixture_missing_evidence(zone_id, loc)
    else:
        missing = data.missing_evidence(feats)
    return ZoneFeaturesResponse(
        zone_id=zone_id,
        features=feats.model_dump() if hasattr(feats, "model_dump") else feats,
        missing_features=missing,
    )


@app.get("/api/zones/{zone_id}/trend", response_model=TrendResponse)
def get_trend(zone_id: str):
    _zone_or_404(zone_id)
    store = _store_for_zone(zone_id)
    trend, rapid = store.trend(zone_id)
    return TrendResponse(
        zone_id=zone_id,
        rapid_increase=rapid,
        history=[{"t": t, "risk_score": s} for t, s in store.history[zone_id]],
    )


@app.get("/api/zones/{zone_id}/explanation", response_model=ExplanationResponse)
def get_explanation(zone_id: str):
    _zone_or_404(zone_id)
    store = _store_for_zone(zone_id)
    loc = _location_for_zone(zone_id)
    # Live SIH26001 TreeSHAP over the zone's NGEN row (weights present only).
    try:
        from . import sih26001_model
        live = sih26001_model.get_live()
        real = live.explain_row(store.features[zone_id]) if live is not None else None
    except Exception:
        real = None
    if real is not None:
        return ExplanationResponse(
            zone_id=zone_id,
            risk_score=store.risk[zone_id],
            base_value=real["base_value"],
            contributions=real["contributions"],
        )
    try:
        letter = zone_id.split("_")[-1]
        _, contribs = data.compute_risk(letter, store.features[zone_id])
        svc = data.model_service.get_service()
        expl = svc.explain(letter, store.features[zone_id].model_dump() if hasattr(store.features[zone_id], 'model_dump') else store.features[zone_id])
        base_value = expl["base_value"]
    except Exception:
        # Scaffold: v1 model has no S1-S4 — serve frozen fixture SHAP
        # (slopes.json contributions, `shap` mapped to API `shap_value`).
        fx = data.fixture_zone(zone_id, loc)
        if fx is None:
            raise
        base_value = float(fx["base_value"])
        contribs = [
            {"feature": c["feature"], "shap_value": c["shap"]}
            for c in fx["contributions"]
        ]
    return ExplanationResponse(
        zone_id=zone_id,
        risk_score=store.risk[zone_id],
        base_value=base_value,
        contributions=contribs,
    )


@app.get("/api/zones/{zone_id}/history")
def get_zone_history(zone_id: str, seed: int = 91):
    """Deterministic daily instability series (365 days) for one zone-world,
    straight from the frozen corpus. This is the real day-by-day signal the
    trend chart should draw -- not session prediction logs."""
    _zone_or_404(zone_id)
    from . import model_service
    hist = model_service.get_service().daily_history(zone_id, seed=seed)
    return {"zone_id": zone_id, "seed": seed, "points": hist, "location": _location_for_zone(zone_id)}


@app.get("/api/zones/{zone_id}/decision", response_model=DecisionResponse)
def get_decision(zone_id: str, lang: str = "en"):
    _zone_or_404(zone_id)
    store = _store_for_zone(zone_id)
    score = store.risk[zone_id]
    # lang=en/hi/ne, fallback to en
    if lang not in ("en", "hi", "ne"):
        lang = "en"
    return DecisionResponse(
        zone_id=zone_id,
        risk_score=score,
        risk_band=data.risk_band(score),
        decisions=_decisions(zone_id, score, lang),
    )


@app.post("/api/risk/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    _zone_or_404(req.zone_id)
    store = _store_for_zone(req.zone_id)
    store.recompute(req.zone_id, req.features)
    score = store.risk[req.zone_id]
    return PredictResponse(
        zone_id=req.zone_id,
        risk_score=score,
        risk_band=data.risk_band(score),
        confidence=store.confidence[req.zone_id],
        missing_evidence=data.missing_evidence(req.features),
    )


@app.post("/api/routes/safe", response_model=RouteResponse)
def safe_route(req: RouteRequest):
    # location-aware: N1-N4 -> lachung, D1-D4 -> darjeeling (strict 2-char ids
    # so v1 single-letter zones A-D still resolve to gangtok), else gangtok.
    # Each corridor routes on its own centers/graph/risk so waypoints render
    # on that corridor's map instead of off-screen at Gangtok.
    loc = _route_location(req.start.zone_id)
    centers = data.ZONE_CENTERS_BY_LOCATION.get(loc) or data.ZONE_CENTERS
    store = data.get_store(loc)
    start = min(centers, key=lambda z: data.distance(req.start.model_dump(), centers[z]))
    end = min(centers, key=lambda z: data.distance(req.end.model_dump(), centers[z]))
    # Shortest uses the full graph INCLUDING the R2 ridge shortcut, so it
    # honestly crosses the at-risk segment. Risk-aware uses the hazard graph
    # (shortcut closed while its adjacent slope is Critical/High), minus any
    # caller-requested avoid_zones (validated below, never start/end).
    full_graph, hazard_graph = _road_graphs_for(loc)
    avoid = [z for z in (req.avoid_zones or []) if z not in (start, end)]
    for z in avoid:
        if z not in hazard_graph.graph:
            raise HTTPException(status_code=422, detail=f"avoid_zones: unknown zone {z!r}")
    if avoid:
        hazard_graph = _without_zones(hazard_graph, avoid)
    shortest_comparison = compare_routes(full_graph, start, end, store.risk, ROUTING_ALPHA)
    try:
        aware_comparison = compare_routes(hazard_graph, start, end, store.risk, ROUTING_ALPHA)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"no risk-aware route: {exc}")
    shortest = {
        "path": data.interpolate(
            [centers[zone_id] for zone_id in shortest_comparison.shortest_route.path]
        ),
        "zone_path": list(shortest_comparison.shortest_route.path),
        # Raw graph cost (degrees for shortest, risk-weighted for aware).
        # Clients must NOT display this as km — see frontend haversine.
        "total_cost": shortest_comparison.shortest_route.total_cost,
        "max_risk_exposed": shortest_comparison.shortest_route.max_risk_exposed,
    }
    aware = {
        "path": data.interpolate(
            [centers[zone_id] for zone_id in aware_comparison.risk_aware_route.path]
        ),
        "zone_path": list(aware_comparison.risk_aware_route.path),
        "total_cost": aware_comparison.risk_aware_route.total_cost,
        "max_risk_exposed": aware_comparison.risk_aware_route.max_risk_exposed,
    }
    comparison = aware_comparison
    aware_ids = set(aware["zone_path"])
    avoided = [z for z in shortest["zone_path"] if z not in aware_ids]
    return RouteResponse(
        risk_aware_route=aware,
        shortest_route=shortest,
        avoided_zones=avoided,
        location=loc,
    )


def _route_location(zone_id: str) -> str:
    zid = (zone_id or "").strip().upper()
    if len(zid) == 2 and zid[0] == "N" and zid[1:].isdigit():
        return "lachung"
    if len(zid) == 2 and zid[0] == "D" and zid[1:].isdigit():
        return "darjeeling"
    return "gangtok"


# (full graph with R2 shortcut, hazard graph without it). The shortcut is the
# fixture R2 ridge segment; it is closed to risk-aware routing while its
# adjacent upper slope is Critical/High. Cached per location; the band check
# re-runs per call so a de-escalated slope reopens the shortcut honestly.
_LOCATION_GRAPHS: dict[str, tuple[MineRoadGraph, MineRoadGraph, str, str]] = {}


def _road_graphs_for(location: str) -> tuple[MineRoadGraph, MineRoadGraph]:
    """(full_graph, hazard_graph) per corridor.

    Full graph = zone topology + the direct upper->valley R2 ridge shortcut
    (fixture roads.json R2; adjacent to the upper slope whose tension-crack
    hazard makes the segment at-risk). Shortest-path routing uses it, so the
    shortest route honestly crosses R2. Hazard graph drops the shortcut while
    the upper slope is Critical/High, so risk-aware routing deterministically
    diverts via the valley road chain (R3+R4) — exactly the avoidance the
    fixtures and UI describe. Band is read live from the corridor store.
    """
    centers = data.ZONE_CENTERS_BY_LOCATION.get(location) or data.ZONE_CENTERS
    store = data.get_store(location)
    zids = sorted(store.features)
    upper, valley = zids[0], zids[-1]
    upper_band = data.risk_band(store.risk[upper])
    cache_key = (location, upper_band)
    if cache_key not in _LOCATION_GRAPHS:
        graph = data.GRAPH_BY_LOCATION.get(location) or data.GRAPH
        full = MineRoadGraph()
        for zid in centers:
            full.add_zone(zid)
        for start_zone_id, neighbors in graph.items():
            for end_zone_id in neighbors:
                if full.graph.has_edge(start_zone_id, end_zone_id):
                    continue
                full.add_road(
                    start_zone_id,
                    end_zone_id,
                    length=data.distance(centers[start_zone_id], centers[end_zone_id]),
                    adjacent_zones=(start_zone_id, end_zone_id),
                )
        # R2 ridge shortcut: straight upper->valley, adjacent to the upper
        # slope (fixture R2 adjacent_slope). Shorter than any valley chain,
        # so pure-length routing always takes it.
        full.add_road(
            upper,
            valley,
            length=data.distance(centers[upper], centers[valley]),
            adjacent_zones=(upper, valley),
        )
        hazard = MineRoadGraph()
        for zid in centers:
            hazard.add_zone(zid)
        for a, b, edata in full.graph.edges(data=True):
            if {a, b} == {upper, valley} and upper_band in ("Critical", "High"):
                continue
            hazard.add_road(a, b, length=edata["length"],
                            adjacent_zones=edata["adjacent_zones"])
        _LOCATION_GRAPHS[cache_key] = (full, hazard, upper, valley)
    full, hazard, _, _ = _LOCATION_GRAPHS[cache_key]
    return full, hazard


def _road_graph_for(location: str) -> MineRoadGraph:
    """Backward-compat: full per-corridor graph (with R2 shortcut)."""
    full, _ = _road_graphs_for(location)
    return full


def _without_zones(graph: MineRoadGraph, drop: list[str]) -> MineRoadGraph:
    """Copy of graph with zones removed (officer closures for risk-aware)."""
    g = MineRoadGraph()
    drop_set = set(drop)
    for node in graph.graph.nodes:
        if node not in drop_set:
            g.add_zone(node)
    for a, b, edata in graph.graph.edges(data=True):
        if a not in drop_set and b not in drop_set:
            g.add_road(a, b, length=edata["length"],
                       adjacent_zones=edata["adjacent_zones"])
    return g


@app.post("/api/simulation/what-if", response_model=WhatIfResponse,
          description="ML COUNTERFACTUAL: overrides observed features and re-predicts "
                      "with the frozen RF. Not a causal simulation -- use "
                      "/api/simulation/causal-what-if for physics-based trajectories. "
                      "Unavailable for ZONE_D (uplift failure mode is aquifer-driven; "
                      "surface-feature overrides cannot represent it).")
def what_if(req: WhatIfRequest):
    _zone_or_404(req.zone_id)
    if req.zone_id == "D":
        raise HTTPException(
            status_code=422,
            detail=("ML counterfactual is not valid for ZONE_D: its failure mode is "
                    "confined-aquifer floor heave (FoS = reference / pore pressure), which "
                    "surface-feature overrides cannot represent. Use the causal Scenario "
                    "Engine with groundwater scenarios instead."))
    _zone_or_404(req.zone_id)
    if data.fixture_zone(req.zone_id) is not None:
        # Scaffold: v1 model has no S-zones — serve the recorded demo.
        return _fixture_what_if(req.zone_id)
    current = data.store.features[req.zone_id]
    try:
        merged = data.apply_overrides(current, req.overrides)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors(include_url=False))
    baseline_score = data.store.risk[req.zone_id]
    simulated_score, contribs = data.compute_risk(req.zone_id, merged)
    baseline = PredictResponse(
        zone_id=req.zone_id,
        risk_score=baseline_score,
        risk_band=data.risk_band(baseline_score),
        confidence=data.store.confidence[req.zone_id],
        missing_evidence=data.missing_evidence(data.store.features[req.zone_id]),
    )
    simulated = PredictResponse(
        zone_id=req.zone_id,
        risk_score=simulated_score,
        risk_band=data.risk_band(simulated_score),
        confidence=data.model_service.get_service().calibrated_confidence(simulated_score),
        missing_evidence=data.missing_evidence(merged),
    )
    return WhatIfResponse(
        zone_id=req.zone_id,
        baseline=baseline,
        simulated=simulated,
        delta=simulated_score - baseline_score,
        contributions=contribs,
    )


@app.get("/api/simulation/templates", response_model=TemplatesResponse)
def list_scenario_templates():
    # Scaffold: frozen fixture templates (monga-mdl + dahal-144) from
    # forecast.json. v1 scenario_service kept for later lanes.
    return TemplatesResponse(templates=[
        {"template_id": t["id"],
         "source": f"IMD-fixture (recorded): {t['name']} — {t['formula']}"}
        for t in _FORECAST["templates"]
    ])


@app.post("/api/simulation/causal-what-if",
          description="CAUSAL PHYSICS What-If (Scenario Engine v1.5): modifies causes "
                      "and lets the frozen generator chain propagate them. Scaffold: "
                      "S-zones serve the recorded forecast.json causal_demo fixture; "
                      "v1 model path unchanged (response_model dropped so the fixture "
                      "dict passes through; v1 still returns CausalWhatIfResponse).")
def causal_what_if(req: CausalWhatIfRequest):
    _zone_or_404(req.zone_id)
    if data.fixture_zone(req.zone_id) is not None:
        return _FORECAST["causal_demo"]
    from . import scenario_service
    try:
        result = scenario_service.run_causal(
            zone_letter=req.zone_id, kind=req.kind, start_day=req.start_day,
            duration_days=req.duration_days, params=req.params,
            horizon_days=req.horizon_days, seed=req.seed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return CausalWhatIfResponse(**result)


# ---- Sept-5 scaffold fixture endpoints (in-memory, offline) ---------------
# Loaded once at import from data/sih26001/fixtures/*.json. No live calls:
# alerts dispatch returns the fixture (no SMS), forecast is recorded.

_FIX_DIR = Path(__file__).resolve().parents[2] / "data" / "sih26001" / "fixtures"


def _load_fixture(name: str):
    return json.loads((_FIX_DIR / name).read_text(encoding="utf-8"))


_ROADS = _load_fixture("roads.json")
_ALERTS = _load_fixture("alerts.json")
_FORECAST = _load_fixture("forecast.json")


# ---- field reporting state (PS e -> FR-10, Screen 6) -----------------------
# Seed from fixtures/reports.json (kept compatible with new schema). In-memory
# per contract §4; candidate-label promotion is explicit, never auto (see docs).
import math as _math

_REPORTS_SEED: list[dict] = _load_fixture("reports.json")["reports"]

def _normalize_report_seed(raw: dict) -> dict:
    """Upgrade legacy fixture shape (lat/lon + photo string) to ReportOut shape."""
    rec = dict(raw)
    # legacy keys: lat/lon -> normalize, photo string -> dropped, reporter -> reporter_role
    if "lat" in rec and "lon" not in rec:
        rec["lon"] = rec.pop("lat")
    # map legacy lat/lon already correct; ensure new keys present with defaults for old fixture
    rec.setdefault("type", rec.get("type", "crack"))
    rec.setdefault("text", rec.get("text", "Field report"))
    rec.setdefault("captured_at", rec.get("captured_at", data.now_iso()))
    rec.setdefault("reporter_role", rec.get("reporter_role", rec.get("reporter", "field_officer")))
    rec.pop("reporter", None)
    # photo legacy was a string placeholder; normalize to PhotoMeta or None
    photo = rec.get("photo")
    if isinstance(photo, str):
        rec["photo"] = None
    # ensure consent true for fixture (honest consent)
    rec.setdefault("consent", True)
    # ensure lat/lon present (fixture has them)
    rec.setdefault("status", "queued")
    rec.setdefault("created_at", rec.get("captured_at", data.now_iso()))
    rec.setdefault("flagged_reason", None)
    # validate through schema to enforce types, then dump
    try:
        # allow legacy flagged field
        if "lat" in rec and "lon" in rec:
            # ensure floats
            rec["lat"] = float(rec["lat"])
            rec["lon"] = float(rec["lon"])
        out = ReportOut.model_validate(rec)
        return out.model_dump()
    except Exception:
        # fallback: keep raw but ensure required keys for demo
        rec["id"] = rec.get("id", "REP-001")
        return rec

_REPORTS: list[dict] = [_normalize_report_seed(r) for r in _REPORTS_SEED]

# Simple per-process rate cap (demo-sized abuse guard): 20 reports per boot
_REPORT_RATE_LIMIT = 20

def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = _math.radians(lat1), _math.radians(lat2)
    dphi = _math.radians(lat2 - lat1)
    dlam = _math.radians(lon2 - lon1)
    a = _math.sin(dphi / 2) ** 2 + _math.cos(p1) * _math.cos(p2) * _math.sin(dlam / 2) ** 2
    return 2 * r * _math.asin(_math.sqrt(a))

def _report_flagged_reason(rep: dict) -> tuple[str, str] | None:
    """Return (status, reason) if report should be flagged, else None."""
    photo = rep.get("photo") or {}
    ex_lat = photo.get("exif_lat") if isinstance(photo, dict) else None
    ex_lon = photo.get("exif_lon") if isinstance(photo, dict) else None
    if ex_lat is not None and ex_lon is not None:
        try:
            dist = _haversine_m(float(rep["lat"]), float(rep["lon"]), float(ex_lat), float(ex_lon))
            if dist > 200:
                return ("flagged", f"EXIF GPS {dist:.0f}m from claimed location (>200m) — flagged for officer check")
        except Exception:
            pass
    # mime whitelist check (if provided)
    mime = photo.get("mime") if isinstance(photo, dict) else None
    if mime is not None:
        allowed = {"image/jpeg", "image/png", "image/webp", "video/mp4"}
        if mime not in allowed:
            return ("flagged", f"Unsupported media type {mime} — flagged")
    return None


@app.get("/api/roads/status")
def roads_status(location: str = "gangtok"):
    # location-aware: Gangtok coords are canonical in roads.json; Lachung/
    # Darjeeling reuse the same R1-R4 topology shifted by the documented
    # fixture offsets (same constants as frontend locations.js) until NGEN
    # extraction lands. Default gangtok behavior unchanged (validator-safe).
    return _road_segments_for(location)


# ---- per-corridor road geometry (fixture-preview) ---------------------------
# Shift offsets mirror frontend/src/data/locations.js so both layers agree.
_ROAD_SHIFT = {
    "gangtok": (0.0, 0.0),
    "lachung": (0.35, 0.135),
    "darjeeling": (-0.298, -0.337),
}
_ROAD_ZONE_PREFIX = {"gangtok": "S", "lachung": "N", "darjeeling": "D"}


def _road_segments_for(location: str) -> dict:
    loc = location if location in _ROAD_SHIFT else "gangtok"
    dlat, dlon = _ROAD_SHIFT[loc]
    prefix = _ROAD_ZONE_PREFIX[loc]
    out = []
    for seg in _ROADS["segments"]:
        s = dict(seg)
        adj = str(s.get("adjacent_slope", ""))
        if len(adj) == 2 and adj[0] == "S" and adj[1:].isdigit():
            local_adj = f"{prefix}{adj[1:]}"
            s["adjacent_slope"] = local_adj
            for key in ("name", "description"):
                if isinstance(s.get(key), str):
                    s[key] = s[key].replace(adj, local_adj)
        s["coordinates"] = [[round(lat + dlat, 5), round(lon + dlon, 5)]
                            for lat, lon in s.get("coordinates", [])]
        if loc != "gangtok":
            s["description"] = (s.get("description", "")
                                + " [fixture-preview geometry cloned from Gangtok; pending NGEN extraction]")
        out.append(s)
    return {"segments": out, "location": loc, "preview": loc != "gangtok"}


@app.post("/api/reports", response_model=ReportOut)
def create_report(body: ReportIn):
    if len(_REPORTS) >= _REPORT_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Report rate limit reached for this session (demo cap 20)")
    if body.consent is not True:
        raise HTTPException(status_code=422, detail="consent must be true — you must consent to sharing photo + location with authorities")
    # captured_at honesty: must parse as ISO, not in far future (>24h ahead)
    try:
        # allow both with and without timezone; normalize
        from datetime import datetime, timezone as _tz
        ts = body.captured_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_tz.utc)
        now = datetime.now(_tz.utc)
        if dt > now:
            # allow up to 1h clock skew, else flag
            delta = (dt - now).total_seconds()
            if delta > 3600:
                raise HTTPException(status_code=422, detail="captured_at is in the future")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=422, detail="captured_at must be ISO-8601 (e.g. 2026-09-04T09:30:00+05:30)")

    # zone validation: Gangtok live + Lachung/Darjeeling preview (expanded NER)
    allowed_zones = set(data.ZONE_CENTERS) | {"N1","N2","N3","N4","D1","D2","D3","D4"}
    if body.zone_id not in allowed_zones:
        raise HTTPException(status_code=422, detail=f"zone_id must be one of {sorted(allowed_zones)}")

    # build record
    rid = f"REP-{len(_REPORTS) + 1:03d}"
    rec = body.model_dump()
    # keep lat/lon as floats for storage
    rec["id"] = rid
    rec["created_at"] = data.now_iso()

    # EXIF / mime flagging (honesty-critical, per plan §3A)
    flagged = _report_flagged_reason(rec)
    if flagged:
        status, reason = flagged
        rec["status"] = status
        rec["flagged_reason"] = reason
    else:
        rec["status"] = "queued"
        rec["flagged_reason"] = None

    # validate full ReportOut before storing (ensures expiry of any bad coercion)
    out = ReportOut.model_validate(rec)
    dump = out.model_dump()
    _REPORTS.append(dump)
    return dump


@app.get("/api/reports/queue")
def reports_queue(status: str | None = None):
    if status is not None and status not in {"queued", "verified", "dismissed", "flagged"}:
        raise HTTPException(status_code=422, detail="status filter must be one of queued|verified|dismissed|flagged")
    if status is None:
        return {"reports": _REPORTS}
    return {"reports": [r for r in _REPORTS if r.get("status") == status]}


@app.patch("/api/reports/{report_id}")
def review_report(report_id: str, body: ReportReviewIn):
    for r in _REPORTS:
        if r.get("id") == report_id:
            # simple state machine: only queued or flagged can transition; verified/dismissed are terminal for demo
            if r.get("status") in {"verified", "dismissed"} and body.status != r.get("status"):
                raise HTTPException(status_code=409, detail=f"Report {report_id} already {r.get('status')} — cannot transition to {body.status}")
            r["status"] = body.status
            if body.reason:
                r["flagged_reason"] = body.reason
            # record reviewer (demo; real auth is post-hackathon per limitations)
            if body.reviewer_role:
                r["reviewer_role"] = body.reviewer_role
            return r
    raise HTTPException(status_code=404, detail=f"Report {report_id} not found")


@app.post("/api/alerts/dispatch")
def dispatch_alerts():
    return _ALERTS


@app.get("/api/forecast/rainfall")
def forecast_rainfall():
    return _FORECAST


def _fixture_what_if(zone_id: str) -> WhatIfResponse:
    """Sept-5 scaffold: recorded ML-counterfactual demo (forecast.json
    ml_whatif_demo: S3 66 -> 74, delta 8). Baseline from the fixture-seeded
    store; the caveat badge is frontend-side per contract Screen 3."""
    demo = _FORECAST["ml_whatif_demo"]
    base = data.store.risk[zone_id]
    sim = int(demo["simulated_score"])
    fx = data.fixture_zone(zone_id)
    baseline = PredictResponse(
        zone_id=zone_id,
        risk_score=base,
        risk_band=data.risk_band(base),
        confidence=data.store.confidence[zone_id],
        missing_evidence=data.fixture_missing_evidence(zone_id),
    )
    simulated = PredictResponse(
        zone_id=zone_id,
        risk_score=sim,
        risk_band=data.risk_band(sim),
        confidence=data.store.confidence[zone_id],
        missing_evidence=data.fixture_missing_evidence(zone_id),
    )
    contribs = [
        {"feature": c["feature"], "shap_value": c["shap"]}
        for c in fx["contributions"]
    ]
    return WhatIfResponse(
        zone_id=zone_id,
        baseline=baseline,
        simulated=simulated,
        delta=sim - base,
        contributions=contribs,
    )
