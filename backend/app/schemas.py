from typing import Literal, Optional

from pydantic import BaseModel, Field

ROCK_TYPES = [
    "lateritic_soil",
    "sandstone",
    "clayey_sandstone",
    "clay",
    "variegated_sandy_clay",
    "carbonaceous_clay",
    "aquifer_sand",
    "lignite",
    "overburden_mixed",
]

CRACK_SEVERITIES = ["normal", "minor", "moderate", "severe", "critical"]

RISK_BANDS = ["Very Low", "Low", "Moderate", "High", "Critical"]
TRENDS = ["stable", "rising", "rapidly_increasing"]
ROLES = ["worker", "safety_officer", "mine_manager", "rescue_team"]


class Features(BaseModel):
    rainfall_24h_mm: float = Field(ge=0)
    rainfall_7d_mm: float = Field(ge=0)
    slope_angle_deg: float = Field(ge=0)
    slope_height_m: float = Field(ge=0)
    rock_type: Literal[*ROCK_TYPES]
    crack_density: float = Field(ge=0, le=1)
    crack_severity: Literal[*CRACK_SEVERITIES]
    blast_frequency_per_week: float = Field(ge=0)
    blast_vibration_ppv_mms: float = Field(ge=0)
    days_since_inspection: int = Field(ge=0)
    prior_incident: Literal[0, 1]
    groundwater_proxy: float = Field(ge=0, le=1)


class ZoneSummary(BaseModel):
    zone_id: str
    risk_score: int
    risk_band: str
    confidence: float
    trend: str


class ZoneDetail(ZoneSummary):
    name: str
    geometry: dict
    updated_at: str


class ZoneFeaturesResponse(BaseModel):
    zone_id: str
    features: Features
    missing_features: list[str]


class TrendPoint(BaseModel):
    t: str
    risk_score: int


class TrendResponse(BaseModel):
    zone_id: str
    rapid_increase: bool
    history: list[TrendPoint]


class Contribution(BaseModel):
    feature: str
    shap_value: float


class ExplanationResponse(BaseModel):
    zone_id: str
    risk_score: int
    base_value: float
    contributions: list[Contribution]


class DecisionItem(BaseModel):
    role: str
    message: str
    action: str
    priority: str


class DecisionResponse(BaseModel):
    zone_id: str
    risk_score: int
    risk_band: str
    decisions: list[DecisionItem]


class PredictRequest(BaseModel):
    zone_id: str
    features: Features


class PredictResponse(BaseModel):
    zone_id: str
    risk_score: int
    risk_band: str
    confidence: float
    missing_evidence: list[str]


class PathPoint(BaseModel):
    lat: float
    lng: float


class RoutePoint(BaseModel):
    zone_id: str
    lat: float
    lng: float


class RouteRequest(BaseModel):
    start: RoutePoint
    end: RoutePoint


class RouteResult(BaseModel):
    path: list[PathPoint]
    total_cost: float
    max_risk_exposed: int


class RouteResponse(BaseModel):
    risk_aware_route: RouteResult
    shortest_route: RouteResult
    avoided_zones: list[str]


class WhatIfRequest(BaseModel):
    zone_id: str
    overrides: dict


class WhatIfResponse(BaseModel):
    zone_id: str
    baseline: PredictResponse
    simulated: PredictResponse
    delta: int
    contributions: list[Contribution]