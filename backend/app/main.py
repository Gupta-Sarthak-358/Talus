from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from . import data
from .schemas import (
    CausalWhatIfRequest,
    CausalWhatIfResponse,
    DecisionResponse,
    ExplanationResponse,
    Features,
    PredictRequest,
    PredictResponse,
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

DECISIONS_BY_BAND = {
    "Critical": [
        {"role": "worker", "message": "Avoid Zone B", "action": "safe route guidance", "priority": "immediate"},
        {"role": "safety_officer", "message": "Prioritize inspection of Zone B", "action": "early risk intervention", "priority": "high"},
        {"role": "mine_manager", "message": "Coordinate evacuation of Zone B", "action": "operational decision", "priority": "high"},
        {"role": "rescue_team", "message": "Use safer approach route to Zone B", "action": "risk-aware response", "priority": "standby"},
    ],
    "High": [
        {"role": "worker", "message": "Restrict entry to this zone", "action": "restricted access", "priority": "high"},
        {"role": "safety_officer", "message": "Inspect this zone today", "action": "early risk intervention", "priority": "high"},
        {"role": "mine_manager", "message": "Review operations in this zone", "action": "operational decision", "priority": "medium"},
        {"role": "rescue_team", "message": "Standby near this zone", "action": "risk-aware response", "priority": "standby"},
    ],
    "Moderate": [
        {"role": "worker", "message": "Exercise caution in this zone", "action": "awareness", "priority": "normal"},
        {"role": "safety_officer", "message": "Schedule an inspection this week", "action": "monitoring", "priority": "normal"},
        {"role": "mine_manager", "message": "Monitor this zone's trend", "action": "monitoring", "priority": "normal"},
        {"role": "rescue_team", "message": "No action required", "action": "none", "priority": "none"},
    ],
}


def _zone_or_404(zone_id: str) -> None:
    if zone_id not in data.store.features:
        raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")


def _decisions(zone_id: str, score: int) -> list[dict]:
    band = data.risk_band(score)
    rows = DECISIONS_BY_BAND.get(band, DECISIONS_BY_BAND["Moderate"])
    out = []
    for row in rows:
        item = dict(row)
        if zone_id in item["message"]:
            item["message"] = item["message"].replace("Zone B", zone_id)
        out.append(item)
    return out


@app.get("/")
def root():
    return {"service": "Talus Risk API", "docs": "/docs",
            "status": "frozen ML Model v1 (RF, generator v1.4.0) + Scenario Engine v1.5"}


@app.get("/api/zones", response_model=dict)
def list_zones():
    zones = []
    for zid in data.store.features:
        trend, _ = data.store.trend(zid)
        zones.append(
            ZoneSummary(
                zone_id=zid,
                risk_score=data.store.risk[zid],
                risk_band=data.risk_band(data.store.risk[zid]),
                confidence=data.store.confidence[zid],
                trend=trend,
            )
        )
    return {"zones": zones}


@app.get("/api/zones/{zone_id}", response_model=ZoneDetail)
def get_zone(zone_id: str):
    _zone_or_404(zone_id)
    trend, _ = data.store.trend(zone_id)
    return ZoneDetail(
        zone_id=zone_id,
        name=data.ZONE_NAMES[zone_id],
        geometry=data.ZONE_GEOMETRY[zone_id],
        risk_score=data.store.risk[zone_id],
        risk_band=data.risk_band(data.store.risk[zone_id]),
        confidence=data.store.confidence[zone_id],
        trend=trend,
        updated_at=data.store.updated_at[zone_id],
    )


@app.get("/api/zones/{zone_id}/features", response_model=ZoneFeaturesResponse)
def get_features(zone_id: str):
    _zone_or_404(zone_id)
    return ZoneFeaturesResponse(
        zone_id=zone_id,
        features=data.store.features[zone_id],
        missing_features=data.missing_evidence(data.store.features[zone_id]),
    )


@app.get("/api/zones/{zone_id}/trend", response_model=TrendResponse)
def get_trend(zone_id: str):
    _zone_or_404(zone_id)
    trend, rapid = data.store.trend(zone_id)
    return TrendResponse(
        zone_id=zone_id,
        rapid_increase=rapid,
        history=[{"t": t, "risk_score": s} for t, s in data.store.history[zone_id]],
    )


@app.get("/api/zones/{zone_id}/explanation", response_model=ExplanationResponse)
def get_explanation(zone_id: str):
    _zone_or_404(zone_id)
    letter = zone_id.split("_")[-1]
    _, contribs = data.compute_risk(letter, data.store.features[zone_id])
    svc = data.model_service.get_service()
    expl = svc.explain(letter, data.store.features[zone_id].model_dump())
    return ExplanationResponse(
        zone_id=zone_id,
        risk_score=data.store.risk[zone_id],
        base_value=expl["base_value"],
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
    return {"zone_id": zone_id, "seed": seed, "points": hist}


@app.get("/api/zones/{zone_id}/decision", response_model=DecisionResponse)
def get_decision(zone_id: str):
    _zone_or_404(zone_id)
    score = data.store.risk[zone_id]
    return DecisionResponse(
        zone_id=zone_id,
        risk_score=score,
        risk_band=data.risk_band(score),
        decisions=_decisions(zone_id, score),
    )


@app.post("/api/risk/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    _zone_or_404(req.zone_id)
    data.store.recompute(req.zone_id, req.features)
    score = data.store.risk[req.zone_id]
    return PredictResponse(
        zone_id=req.zone_id,
        risk_score=score,
        risk_band=data.risk_band(score),
        confidence=data.store.confidence[req.zone_id],
        missing_evidence=data.missing_evidence(req.features),
    )


@app.post("/api/routes/safe", response_model=RouteResponse)
def safe_route(req: RouteRequest):
    start = min(data.ZONE_CENTERS, key=lambda z: data.distance(req.start.model_dump(), data.ZONE_CENTERS[z]))
    end = min(data.ZONE_CENTERS, key=lambda z: data.distance(req.end.model_dump(), data.ZONE_CENTERS[z]))
    risk = data.store.risk
    shortest_path, shortest_cost, _ = data._dijkstra(start, end, risk, 0.0)
    aware_path, aware_cost, aware_max = data._dijkstra(start, end, risk, RISK_WEIGHT)
    _, shortest_max = shortest_path, max((risk.get(n, 0) for n in shortest_path), default=0)
    shortest = {"path": data.interpolate([data.ZONE_CENTERS[z] for z in shortest_path]),
                "total_cost": shortest_cost, "max_risk_exposed": shortest_max}
    aware = {"path": data.interpolate([data.ZONE_CENTERS[z] for z in aware_path]),
             "total_cost": aware_cost, "max_risk_exposed": aware_max}
    avoided = [z for z in shortest_path if z not in aware_path]
    return RouteResponse(risk_aware_route=aware, shortest_route=shortest, avoided_zones=avoided)


@app.post("/api/simulation/what-if", response_model=WhatIfResponse,
          description="ML COUNTERFACTUAL: overrides observed features and re-predicts "
                      "with the frozen RF. Not a causal simulation -- use "
                      "/api/simulation/causal-what-if for physics-based trajectories.")
def what_if(req: WhatIfRequest):
    _zone_or_404(req.zone_id)
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
    from . import scenario_service
    return TemplatesResponse(templates=scenario_service.list_templates())


@app.post("/api/simulation/causal-what-if", response_model=CausalWhatIfResponse,
          description="CAUSAL PHYSICS What-If (Scenario Engine v1.5): modifies causes "
                      "(rain realization / blast schedule) and lets the frozen generator "
                      "v1.4.0 chain propagate them into a day-by-day FoS/risk trajectory.")
def causal_what_if(req: CausalWhatIfRequest):
    _zone_or_404(req.zone_id)
    from . import scenario_service
    try:
        result = scenario_service.run_causal(
            zone_letter=req.zone_id, kind=req.kind, start_day=req.start_day,
            duration_days=req.duration_days, params=req.params,
            horizon_days=req.horizon_days, seed=req.seed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return CausalWhatIfResponse(**result)