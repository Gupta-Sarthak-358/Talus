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


def _mine_road_graph() -> MineRoadGraph:
    """Adapt the demo topology and center distances to the routing domain."""
    mine_road_graph = MineRoadGraph()
    for zone_id in data.ZONE_CENTERS:
        mine_road_graph.add_zone(zone_id)

    for start_zone_id, neighbors in data.GRAPH.items():
        for end_zone_id in neighbors:
            if mine_road_graph.graph.has_edge(start_zone_id, end_zone_id):
                continue
            mine_road_graph.add_road(
                start_zone_id,
                end_zone_id,
                length=data.distance(
                    data.ZONE_CENTERS[start_zone_id], data.ZONE_CENTERS[end_zone_id]
                ),
                adjacent_zones=(start_zone_id, end_zone_id),
            )

    return mine_road_graph


MINE_ROAD_GRAPH = _mine_road_graph()


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
    feats = data.store.features[zone_id]
    if data.fixture_zone(zone_id) is not None:
        missing = data.fixture_missing_evidence(zone_id)
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
    trend, rapid = data.store.trend(zone_id)
    return TrendResponse(
        zone_id=zone_id,
        rapid_increase=rapid,
        history=[{"t": t, "risk_score": s} for t, s in data.store.history[zone_id]],
    )


@app.get("/api/zones/{zone_id}/explanation", response_model=ExplanationResponse)
def get_explanation(zone_id: str):
    _zone_or_404(zone_id)
    try:
        letter = zone_id.split("_")[-1]
        _, contribs = data.compute_risk(letter, data.store.features[zone_id])
        svc = data.model_service.get_service()
        expl = svc.explain(letter, data.store.features[zone_id].model_dump())
        base_value = expl["base_value"]
    except Exception:
        # Scaffold: v1 model has no S1-S4 — serve frozen fixture SHAP
        # (slopes.json contributions, `shap` mapped to API `shap_value`).
        fx = data.fixture_zone(zone_id)
        if fx is None:
            raise
        base_value = float(fx["base_value"])
        contribs = [
            {"feature": c["feature"], "shap_value": c["shap"]}
            for c in fx["contributions"]
        ]
    return ExplanationResponse(
        zone_id=zone_id,
        risk_score=data.store.risk[zone_id],
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
    comparison = compare_routes(
        MINE_ROAD_GRAPH,
        start,
        end,
        data.store.risk,
        ROUTING_ALPHA,
    )
    shortest = {
        "path": data.interpolate(
            [data.ZONE_CENTERS[zone_id] for zone_id in comparison.shortest_route.path]
        ),
        "total_cost": comparison.shortest_route.total_cost,
        "max_risk_exposed": comparison.shortest_route.max_risk_exposed,
    }
    aware = {
        "path": data.interpolate(
            [data.ZONE_CENTERS[zone_id] for zone_id in comparison.risk_aware_route.path]
        ),
        "total_cost": comparison.risk_aware_route.total_cost,
        "max_risk_exposed": comparison.risk_aware_route.max_risk_exposed,
    }
    return RouteResponse(
        risk_aware_route=aware,
        shortest_route=shortest,
        avoided_zones=comparison.avoided_zones,
    )


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
_REPORTS: list[dict] = _load_fixture("reports.json")["reports"]
_ALERTS = _load_fixture("alerts.json")
_FORECAST = _load_fixture("forecast.json")


@app.get("/api/roads/status")
def roads_status():
    return {"segments": _ROADS["segments"]}


@app.post("/api/reports")
def create_report(body: dict):
    rid = f"REP-{len(_REPORTS) + 1:03d}"
    rec = {"id": rid, "status": "queued", **body}
    _REPORTS.append(rec)
    return {"id": rid, "status": "queued"}


@app.get("/api/reports/queue")
def reports_queue():
    return {"reports": _REPORTS}


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
