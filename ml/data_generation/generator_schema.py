from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
GEOTECH_CSV = BASE_DIR / "data" / "processed" / "geotech" / "neyveli_geotech_parameters.csv"

GENERATOR_VERSION = "1.1.0"
SCHEMA_VERSION = "1.0"
GROUNDING_VERSION = "2026-08-20"
PHASES_COMPLETED = ["1A", "1B"]
RESEARCH_FREEZE = True

ZONES = {
    "ZONE_A": {
        "role": "upper_ob_bench",
        "bench_height_m": 25.0,
        "bench_face_angle_deg": 60.0,
        "distance_to_crest_m": 10.0,
        "bench_height_range_m": (18.0, 25.0),
        "face_angle_range_deg": (45.0, 75.0),
        "source_type": "mine_specific",
        "confidence": "high",
    },
    "ZONE_B": {
        "role": "middle_ob_bench",
        "bench_height_m": 18.0,
        "bench_face_angle_deg": 55.0,
        "distance_to_crest_m": 20.0,
        "bench_height_range_m": (18.0, 25.0),
        "face_angle_range_deg": (45.0, 75.0),
        "source_type": "mine_specific",
        "confidence": "high",
    },
    "ZONE_C": {
        "role": "mineral_lignite_bench",
        "bench_height_m": 6.0,
        "bench_face_angle_deg": 75.0,
        "distance_to_crest_m": 5.0,
        "bench_height_range_m": (6.0, 6.0),
        "face_angle_range_deg": (75.0, 75.0),
        "source_type": "approved_mining_plan_2022",
        "confidence": "medium",
    },
    "ZONE_D": {
        "role": "pit_floor",
        "bench_height_m": 0.0,
        "bench_face_angle_deg": 5.0,
        "distance_to_crest_m": 0.0,
        "bench_height_range_m": (0.0, 0.0),
        "face_angle_range_deg": (0.0, 10.0),
        "source_type": "mine_specific",
        "confidence": "high",
    },
}

MATERIAL_CLASSES = [
    "lateritic_soil",
    "clayey_sandstone",
    "sandstone",
    "clay",
    "variegated_sandy_clay",
    "carbonaceous_clay",
    "aquifer_sand",
    "lignite",
    "overburden_mixed",
]

RAINFALL_REGIMES = ["dry", "normal", "wet", "storm"]
GROUNDWATER_STATES = ["dry", "normal", "elevated", "high", "critical"]
CRACK_FAMILIES = ["none", "tension_crest", "desiccation", "blast_induced", "seepage", "floor_heave"]
CRACK_SEVERITIES = ["normal", "minor", "moderate", "severe", "critical"]
SLOPE_CONDITIONS = ["stable", "marginal", "unstable", "failed"]
RISK_LABELS = ["low", "moderate", "high", "critical"]
PARAMETER_REGIMES = ["total_undrained", "effective_stress"]

INTERNAL_FIELDS = [
    ("timestamp", "datetime64[ns]"),
    ("zone_id", "str"),
    ("rainfall_mm", "float"),
    ("rainfall_3d_mm", "float"),
    ("rainfall_7d_mm", "float"),
    ("wet_day", "bool"),
    ("rainfall_regime", "category"),
    ("elevation_m", "float"),
    ("regional_slope_deg", "float"),
    ("bench_height_m", "float"),
    ("bench_face_angle_deg", "float"),
    ("distance_to_crest_m", "float"),
    ("slope_angle_deg", "float"),
    ("slope_height_m", "float"),
    ("material_class", "category"),
    ("cohesion_kpa", "float"),
    ("friction_angle_deg", "float"),
    ("unit_weight_kn_m3", "float"),
    ("parameter_regime", "category"),
    ("groundwater_state", "category"),
    ("pore_pressure_kpa", "float"),
    ("groundwater_thrust_kpa", "float"),
    ("blast_occurs", "bool"),
    ("blast_frequency_per_week", "float"),
    ("charge_per_delay_kg", "float"),
    ("blast_distance_m", "float"),
    ("dominant_frequency_hz", "float"),
    ("blast_vibration_ppv_mms", "float"),
    ("crack_family", "category"),
    ("crack_width_mm", "float"),
    ("crack_depth_m", "float"),
    ("crack_length_m", "float"),
    ("crack_density", "float"),
    ("water_filled", "bool"),
    ("crack_growth_rate_mm_day", "float"),
    ("crack_severity", "category"),
    ("days_since_inspection", "int"),
    ("prior_incident", "bool"),
    ("groundwater_proxy", "float"),
    ("slope_condition", "category"),
    ("instability_score", "float"),
    ("risk_label", "category"),
    ("synthetic", "bool"),
]

ML_FIELDS = [
    "rainfall_24h_mm",
    "rainfall_7d_mm",
    "slope_angle_deg",
    "slope_height_m",
    "rock_type",
    "crack_density",
    "crack_severity",
    "blast_frequency_per_week",
    "blast_vibration_ppv_mms",
    "days_since_inspection",
    "prior_incident",
    "groundwater_proxy",
]

ML_PROJECTION = {
    "rainfall_24h_mm": "rainfall_mm",
    "rainfall_7d_mm": "rainfall_7d_mm",
    "slope_angle_deg": "slope_angle_deg",
    "slope_height_m": "slope_height_m",
    "rock_type": "material_class",
    "crack_density": "crack_density",
    "crack_severity": "crack_severity",
    "blast_frequency_per_week": "blast_frequency_per_week",
    "blast_vibration_ppv_mms": "blast_vibration_ppv_mms",
    "days_since_inspection": "days_since_inspection",
    "prior_incident": "prior_incident",
    "groundwater_proxy": "groundwater_proxy",
}

CATEGORY_ENUMS = {
    "rainfall_regime": RAINFALL_REGIMES,
    "material_class": MATERIAL_CLASSES,
    "parameter_regime": PARAMETER_REGIMES,
    "groundwater_state": GROUNDWATER_STATES,
    "crack_family": CRACK_FAMILIES,
    "crack_severity": CRACK_SEVERITIES,
    "slope_condition": SLOPE_CONDITIONS,
    "risk_label": RISK_LABELS,
}

PHYSICS_FIELDS_1A = [
    "rainfall_mm",
    "rainfall_3d_mm",
    "rainfall_7d_mm",
    "wet_day",
    "rainfall_regime",
    "elevation_m",
    "regional_slope_deg",
    "slope_angle_deg",
    "slope_height_m",
    "material_class",
    "cohesion_kpa",
    "friction_angle_deg",
    "unit_weight_kn_m3",
    "parameter_regime",
    "groundwater_state",
    "pore_pressure_kpa",
    "groundwater_thrust_kpa",
    "blast_occurs",
    "blast_frequency_per_week",
    "charge_per_delay_kg",
    "blast_distance_m",
    "dominant_frequency_hz",
    "blast_vibration_ppv_mms",
    "crack_family",
    "crack_width_mm",
    "crack_depth_m",
    "crack_length_m",
    "crack_density",
    "water_filled",
    "crack_growth_rate_mm_day",
    "crack_severity",
    "groundwater_proxy",
    "slope_condition",
    "instability_score",
    "risk_label",
]

BASE_STATE_FIELDS_1A = [
    "timestamp",
    "zone_id",
    "bench_height_m",
    "bench_face_angle_deg",
    "distance_to_crest_m",
    "days_since_inspection",
    "prior_incident",
    "synthetic",
]
