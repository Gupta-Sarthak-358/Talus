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
    crack_density: float = Field(ge=0, le=2.5)
    crack_severity: Literal[*CRACK_SEVERITIES]
    blast_frequency_per_week: float = Field(ge=0)
    blast_vibration_ppv_mms: float = Field(ge=0)
    days_since_inspection: int = Field(ge=0)
    prior_incident: Literal[0, 1]
    groundwater_proxy: float = Field(ge=0, le=1000)


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


# ---- causal physics What-If (Scenario Engine v1.5) -----------------------

CAUSAL_KINDS = ["none", "rainfall_storm", "prolonged_rain", "blast_surge",
                "combined", "historical_rain"]


class CausalWhatIfRequest(BaseModel):
    zone_id: Literal["A", "B", "C", "D"]
    kind: Literal[*CAUSAL_KINDS]
    start_day: int = Field(default=200, ge=0)
    duration_days: int = Field(default=7, ge=1)
    params: dict = Field(default_factory=dict)
    horizon_days: int = Field(default=365, ge=30, le=1500)
    seed: int = Field(default=42)


class TrajectoryPoint(BaseModel):
    day: int
    fos: float
    instability_score: float
    risk_label: str
    baseline_fos: float


class ScenarioProvenance(BaseModel):
    template_id: Optional[str] = None
    imd_window: Optional[list[str]] = None
    window_total_mm: Optional[float] = None
    window_max_day_mm: Optional[float] = None
    source: str = "IMD 0.25deg Neyveli grid 11.5N 79.5E"


class TemplatesResponse(BaseModel):
    templates: list[ScenarioProvenance]


class CausalSummary(BaseModel):
    baseline_min_fos: float
    scenario_min_fos: float
    delta_min_fos: float
    baseline_peak_instability: float
    scenario_peak_instability: float
    delta_peak_instability: float
    baseline_days_high_or_critical: int
    scenario_days_high_or_critical: int
    first_response_day: Optional[int] = None
    worst_day: int
    worst_day_risk: str
    max_groundwater_proxy_mm: float
    open_crack_branch_fired: bool


class CausalWhatIfResponse(BaseModel):
    zone_id: str
    scenario_name: str
    mode: str = "causal_physics"
    generator_version: str
    summary: CausalSummary
    provenance: Optional[ScenarioProvenance] = None
    trajectory: list[TrajectoryPoint]