/**
 * SIH26001 Sept-5 Demo Mock & Fixture Dataset
 * Pilot: Gangtok cluster, Sikkim (27.3389, 88.6065)
 * Frozen scores: S1=89 Critical, S2=78 High, S3=66 Moderate, S4=52 Low
 * Frozen roles: villager | district_officer | state_manager | rescue_team
 * Contract: docs/sih26001/SCAFFOLD_CONTRACT_SEPT5.md
 */

export const RISK_BANDS = {
  VERY_LOW: { label: "VERY LOW", color: "text-[#5e7f3a]", bg: "bg-[#5e7f3a]/15", border: "border-[#5e7f3a]/30", badgeColor: "#5e7f3a", range: [0, 49] },
  LOW: { label: "LOW", color: "text-[#a68a3c]", bg: "bg-[#a68a3c]/15", border: "border-[#a68a3c]/30", badgeColor: "#a68a3c", range: [50, 64] },
  MODERATE: { label: "MODERATE", color: "text-[#d99a24]", bg: "bg-[#d99a24]/15", border: "border-[#d99a24]/30", badgeColor: "#d99a24", range: [65, 74] },
  HIGH: { label: "HIGH", color: "text-[#d96b24]", bg: "bg-[#d96b24]/15", border: "border-[#d96b24]/30", badgeColor: "#d96b24", range: [75, 84] },
  CRITICAL: { label: "CRITICAL", color: "text-[#c74732]", bg: "bg-[#c74732]/15", border: "border-[#c74732]/30", badgeColor: "#c74732", range: [85, 100] },
};

export const ROLES = [
  {
    id: "villager",
    label: "Villager / Community",
    badge: "Community",
    description: "Multilingual safety guidance, hillside road avoidance & community evacuation alerts"
  },
  {
    id: "district_officer",
    label: "District Disaster Officer",
    badge: "District Admin",
    description: "Stretch closure orders, field team dispatch, incident reports & priority evacuation"
  },
  {
    id: "state_manager",
    label: "State Disaster Manager (SSDMA)",
    badge: "State Ops",
    description: "Cross-district priority triage, heavy machinery staging at Ranipool & reserve team allocations"
  },
  {
    id: "rescue_team",
    label: "NDRF / SDRF Rescue Team",
    badge: "First Responder",
    description: "Risk-aware approach corridors, avoidance of at-risk roads (R2) & incident staging"
  },
];

export const MOCK_ZONES = [
  {
    id: "S1",
    name: "S1 — Tathangchen (upper)",
    village: "Tathangchen",
    sector: "Gangtok Upper Hillside",
    risk_score: 89,
    risk_band: "CRITICAL",
    confidence: 82,
    base_risk: 55,
    status: "CRITICAL RISK — IMMEDIATE EVACUATION / CLOSURE",
    activePersonnel: 0,
    activeEquipment: "Debris flow monitors",
    telemetry: {
      slope_angle: 38.5,
      rainfall_24h: 88,
      rainfall_7d: 185,
      rainfall_30d: 380,
      soil_moisture: 0.84,
      distance_to_road: 45,
      distance_to_river: 120,
      elevation: 1680,
      ndvi: 0.32,
    },
    shap: [
      { feature: "distance_to_road", value: 12.5, rawValue: "45 m", description: "Proximity to cut slope accelerates instability" },
      { feature: "rainfall_7d_mm", value: 9.0, rawValue: "185 mm", description: "Antecedent 7-day soaking triggers pore pressure" },
      { feature: "slope_angle", value: 7.5, rawValue: "38.5°", description: "Steep upper catchment incline" },
      { feature: "soil_moisture", value: 5.0, rawValue: "84% (proxy)", description: "Near saturation threshold" },
    ],
    trend: {
      direction: "rising",
      delta: "+31 pts in season",
      badge: "↑ Escalating",
      history: [
        { time: "2026-06-01", risk: 58, label: "01 Jun" },
        { time: "2026-06-20", risk: 66, label: "20 Jun" },
        { time: "2026-07-10", risk: 78, label: "10 Jul" },
        { time: "2026-08-15 (Live)", risk: 89, label: "15 Aug" },
      ],
    },
    missing_evidence: ["soil_moisture:reanalysis-proxy", "event-date:approximate"],
    missing_evidence_warning: "Risk interpreted with proxy evidence: Soil moisture from ERA5 reanalysis proxy; historical event date approximate.",
    role_actions: {
      villager: {
        header: "IMMEDIATE EVACUATION / AVOID ROAD",
        action: "Avoid the S1 hillside road for 2 days. Use the valley route.",
        caution: "avoid-route guidance (Nepali/Hindi/English)",
        routeRecommended: "Safe Valley Route (via R3/R4)",
        urgency: "Immediate Action",
      },
      district_officer: {
        header: "ROAD CLOSURE & EVACUATION COORDINATION",
        action: "Close the S1 stretch, evacuate Tathangchen upper first.",
        caution: "closure + evacuation coordination",
        routeRecommended: "Emergency Evacuation Corridor S3-S4",
        urgency: "High Priority",
      },
      state_manager: {
        header: "PRIORITY RESOURCE ALLOCATION",
        action: "Prioritise S1 over S2–S4. Stage machines at Ranipool.",
        caution: "resource allocation",
        routeRecommended: "Ranipool Machine Depot",
        urgency: "High Priority",
      },
      rescue_team: {
        header: "RISK-AWARE SOUTH APPROACH",
        action: "Approach S1 from the south. Do not use the short ridge road.",
        caution: "risk-aware approach",
        routeRecommended: "Approach from South (Avoid R2)",
        urgency: "Standby",
      },
    },
  },
  {
    id: "S2",
    name: "S2 — Chandmari (road-cut)",
    village: "Chandmari",
    sector: "Chandmari Road Corridor",
    risk_score: 78,
    risk_band: "HIGH",
    confidence: 74,
    base_risk: 55,
    status: "HIGH RISK — RESTRICTED NIGHT MOVEMENT",
    activePersonnel: 0,
    activeEquipment: "Tension crack sensor",
    telemetry: {
      slope_angle: 42.0,
      rainfall_24h: 75,
      rainfall_7d: 140,
      rainfall_30d: 310,
      soil_moisture: 0.72,
      distance_to_road: 15,
      distance_to_river: 210,
      elevation: 1540,
      ndvi: 0.28,
    },
    shap: [
      { feature: "distance_to_road", value: 10.0, rawValue: "15 m", description: "Steep road-cut face destabilizing toe" },
      { feature: "rainfall_24h_mm", value: 6.5, rawValue: "75 mm", description: "Recent downpour lubrication" },
      { feature: "slope_angle", value: 4.0, rawValue: "42°", description: "Engineered cut angle exceeded" },
      { feature: "ndvi", value: 2.5, rawValue: "0.28", description: "Sparse vegetation cover on cut slope" },
    ],
    trend: {
      direction: "rising",
      delta: "+16 pts in season",
      badge: "↑ Escalating",
      history: [
        { time: "2026-06-01", risk: 62, label: "01 Jun" },
        { time: "2026-07-01", risk: 70, label: "01 Jul" },
        { time: "2026-08-01 (Live)", risk: 78, label: "01 Aug" },
      ],
    },
    missing_evidence: ["distance_to_road:osm-qa-unverified"],
    missing_evidence_warning: "Risk interpreted with proxy evidence: Road distance from unverified OpenStreetMap QA geometry.",
    role_actions: {
      villager: {
        header: "CAUTION ON CHANDMARI ROAD-CUT",
        action: "Avoid the Chandmari road-cut after heavy rain.",
        caution: "avoid-route guidance",
        routeRecommended: "Alternate Bypass",
        urgency: "High Priority",
      },
      district_officer: {
        header: "INSPECTION & MOVEMENT RESTRICTION",
        action: "Inspect S2 today, restrict night movement.",
        caution: "inspection + restriction",
        routeRecommended: "Patrol Corridor S2",
        urgency: "High Priority",
      },
      state_manager: {
        header: "RESERVE TEAM STAGING",
        action: "Hold one team for S2 if S1 stabilises.",
        caution: "reserve allocation",
        routeRecommended: "Gangtok Central Depot",
        urgency: "Operational",
      },
      rescue_team: {
        header: "STANDBY NEAR CHANDMARI",
        action: "Standby near S2.",
        caution: "standby",
        routeRecommended: "Staging Area S2",
        urgency: "Standby",
      },
    },
  },
  {
    id: "S3",
    name: "S3 — Tadong (mid)",
    village: "Tadong",
    sector: "Tadong Mid-Slope",
    risk_score: 66,
    risk_band: "MODERATE",
    confidence: 61,
    base_risk: 55,
    status: "MODERATE RISK — CONTINUOUS SURVEILLANCE",
    activePersonnel: 0,
    activeEquipment: "Pore pressure telemetry",
    telemetry: {
      slope_angle: 28.0,
      rainfall_24h: 45,
      rainfall_7d: 110,
      rainfall_30d: 260,
      soil_moisture: 0.65,
      distance_to_road: 85,
      distance_to_river: 90,
      elevation: 1320,
      ndvi: 0.45,
    },
    shap: [
      { feature: "rainfall_7d_mm", value: 5.0, rawValue: "110 mm", description: "Moderate cumulative monsoon wetting" },
      { feature: "slope_angle", value: 3.5, rawValue: "28°", description: "Mid-elevation settlement incline" },
      { feature: "soil_moisture", value: 2.5, rawValue: "65%", description: "Elevated soil pore saturation" },
    ],
    trend: {
      direction: "stable",
      delta: "+14 pts in season",
      badge: "↗ Stable Rise",
      history: [
        { time: "2026-06-01", risk: 52, label: "01 Jun" },
        { time: "2026-07-01", risk: 58, label: "01 Jul" },
        { time: "2026-08-01 (Live)", risk: 66, label: "01 Aug" },
      ],
    },
    missing_evidence: ["previous_landslide:inventory-incomplete"],
    missing_evidence_warning: "Risk interpreted with proxy evidence: Historical landslide inventory incomplete for mid-Tadong.",
    role_actions: {
      villager: {
        header: "CAUTION ON TADONG PATHS",
        action: "Caution on Tadong paths during rain.",
        caution: "awareness",
        routeRecommended: "Main Spine Road",
        urgency: "Caution",
      },
      district_officer: {
        header: "SCHEDULE ROUTINE INSPECTION",
        action: "Schedule S3 inspection this week.",
        caution: "monitoring",
        routeRecommended: "Tadong Inspection Track",
        urgency: "Normal",
      },
      state_manager: {
        header: "MONITOR TREND ESCALATION",
        action: "Monitor S3 trend.",
        caution: "monitoring",
        routeRecommended: "Standard Operations",
        urgency: "Normal",
      },
      rescue_team: {
        header: "NO IMMEDIATE ACTION",
        action: "No action required.",
        caution: "none",
        routeRecommended: "Corridor Clear",
        urgency: "Clear",
      },
    },
  },
  {
    id: "S4",
    name: "S4 — Ranipool (valley)",
    village: "Ranipool",
    sector: "Ranipool Valley Floor",
    risk_score: 52,
    risk_band: "LOW",
    confidence: 58,
    base_risk: 55,
    status: "LOW RISK — SECURE EVACUATION CORRIDOR",
    activePersonnel: 0,
    activeEquipment: "River stage station",
    telemetry: {
      slope_angle: 14.0,
      rainfall_24h: 30,
      rainfall_7d: 80,
      rainfall_30d: 210,
      soil_moisture: 0.52,
      distance_to_road: 20,
      distance_to_river: 35,
      elevation: 910,
      ndvi: 0.58,
    },
    shap: [
      { feature: "elevation", value: -6.0, rawValue: "910 m", description: "Valley floor topography stabilizes slope" },
      { feature: "ndvi", value: -4.0, rawValue: "0.58", description: "Dense riparian vegetation roots" },
      { feature: "distance_to_river", value: -3.0, rawValue: "35 m", description: "Engineered river retaining walls" },
    ],
    trend: {
      direction: "stable",
      delta: "+4 pts in season",
      badge: "Stable",
      history: [
        { time: "2026-06-01", risk: 48, label: "01 Jun" },
        { time: "2026-07-01", risk: 50, label: "01 Jul" },
        { time: "2026-08-01 (Live)", risk: 52, label: "01 Aug" },
      ],
    },
    missing_evidence: [],
    missing_evidence_warning: null,
    role_actions: {
      villager: {
        header: "NO ACCESS RESTRICTION",
        action: "No restriction for Ranipool.",
        caution: "none",
        routeRecommended: "Open Corridor",
        urgency: "Clear",
      },
      district_officer: {
        header: "ROUTINE VALLEY WATCH",
        action: "Routine watch on S4.",
        caution: "monitoring",
        routeRecommended: "Valley Access Road",
        urgency: "Normal",
      },
      state_manager: {
        header: "NO ALLOCATION REQUIRED",
        action: "No allocation for S4.",
        caution: "none",
        routeRecommended: "Staging Area Clear",
        urgency: "Normal",
      },
      rescue_team: {
        header: "NO ACTION REQUIRED",
        action: "No action required.",
        caution: "none",
        routeRecommended: "Assembly Hub Open",
        urgency: "Clear",
      },
    },
  },
];

export const MOCK_ALERTS = [
  {
    id: "ALT-01",
    zoneId: "S1",
    zoneName: "S1 — Tathangchen (upper)",
    severity: "CRITICAL",
    title: "S1 Tathangchen Escalated to Critical (89 / 100)",
    summary: "Critical landslide risk for 2 days. Antecedent rainfall (185 mm / 7d) and steep slope angle (38.5°) exceed safety threshold.",
    drivers: ["distance_to_road: 45m (+12.5)", "rainfall_7d: 185mm (+9.0)", "slope_angle: 38.5° (+7.5)"],
    timestamp: "Just now",
    rawTimestamp: "2026-09-04T08:00:00Z",
    acknowledged: false,
    roleDirectives: {
      villager: "Avoid the S1 hillside road for 2 days. Use the valley route.",
      district_officer: "Close the S1 stretch, evacuate Tathangchen upper first.",
      state_manager: "Prioritise S1 over S2–S4. Stage machines at Ranipool.",
      rescue_team: "Approach S1 from the south. Do not use the short ridge road (avoid R2).",
    },
  },
  {
    id: "ALT-02",
    zoneId: "S2",
    zoneName: "S2 — Chandmari (road-cut)",
    severity: "HIGH",
    title: "S2 Chandmari Road-Cut Movement (78 / 100)",
    summary: "Active tension crack opening above road-cut. Night movement restricted.",
    drivers: ["distance_to_road: 15m (+10.0)", "rainfall_24h: 75mm (+6.5)"],
    timestamp: "25 mins ago",
    rawTimestamp: "2026-09-04T07:35:00Z",
    acknowledged: false,
    roleDirectives: {
      villager: "Avoid the Chandmari road-cut after heavy rain.",
      district_officer: "Inspect S2 today, restrict night movement.",
      state_manager: "Hold one team for S2 if S1 stabilises.",
      rescue_team: "Standby near S2.",
    },
  },
];

export const WHAT_IF_PRESETS = [
  {
    id: "monsoon-s3",
    name: "🌧️ S3 Extreme 24h Rain (132 mm)",
    description: "Overrides S3 rainfall_24h_mm to 132 mm (forecast peak). Demonstrates ML Counterfactual fixture.",
    values: {
      rainfall_24h: 132,
      blast_vibration: 10,
      crack_density: 0.5,
      slope_angle: 28,
    },
    targetZone: "S3",
    expectedImpact: "S3 risk score shifts 66 → 74 (delta = +8 pts). Shows ML counterfactual caveat badge.",
  },
  {
    id: "monga-mdl",
    name: "📊 Monga 2026 MDL Preset",
    description: "E = -11.10 + 0.62*D (24<D<1440h). Threshold saturation curve: S3 Moderate(66) → High(78).",
    values: {
      rainfall_24h: 96,
      blast_vibration: 10,
      crack_density: 0.6,
      slope_angle: 32,
    },
    targetZone: "S3",
    expectedImpact: "S3 saturates past the physical threshold: newly escalated to High (78).",
  },
  {
    id: "dahal-144",
    name: "🏔️ Dahal-Hasegawa (>144 mm/day)",
    description: "Empirical Himalayan threshold (>144 mm/day rainfall leads to widespread planar release).",
    values: {
      rainfall_24h: 144,
      blast_vibration: 15,
      crack_density: 1.2,
      slope_angle: 38,
    },
    targetZone: "S1",
    expectedImpact: "Triggers widespread Himalayan threshold alarms across S1 & S2.",
  },
  {
    id: "baseline",
    name: "☀️ Dry Reference Baseline",
    description: "Low antecedent moisture and dry conditions across the Gangtok cluster.",
    values: {
      rainfall_24h: 5,
      blast_vibration: 5,
      crack_density: 0.2,
      slope_angle: 28,
    },
    targetZone: "S3",
    expectedImpact: "Returns slopes to stable baseline scores.",
  },
];

export const CV_SAMPLE_ANALYSES = [
  {
    id: "CV-S2",
    zoneId: "S2",
    zoneName: "S2 — Chandmari Road-Cut",
    imageName: "chandmari_roadcut_ortho.jpg",
    captureTimestamp: "2026-09-04 09:30 AM (Field Drone)",
    resolution: "1.5 cm/pixel GSD",
    crackCount: 2,
    maxCrackLengthMeters: 5.2,
    totalCrackLengthMeters: 8.6,
    crackDensityPerSqm: 1.4,
    dominantOrientation: "N 35° E (Sub-parallel to road cut)",
    shearDisplacementMm: 8.5,
    aiModel: "YOLOv8-Seg Geotechnical Profiler (Fixture)",
    confidence: 88.5,
    riskInterpretation: "Fresh tension crack ~5 m long above Chandmari road-cut. Matches field report REP-001.",
    detectedCracks: [
      { id: 1, label: "Tension Crack #1", length: "5.2 m", width: "2.4 cm", strike: "N35°E", severity: "High" },
      { id: 2, label: "Toe Shearing Seep", length: "3.4 m", width: "1.1 cm", strike: "N30°E", severity: "Moderate" },
    ]
  }
];

export const MOCK_REPORTS = [
  {
    id: "REP-001",
    zone_id: "S2",
    type: "crack",
    text: "Fresh crack above Chandmari road-cut, ~5 m long.",
    lat: 27.3381,
    lon: 88.6121,
    captured_at: "2026-09-04T09:30:00+05:30",
    reporter: "field-officer-fixture",
    photo: "fixture-only (no binary in repo)",
    status: "queued"
  }
];

export const MOCK_MULTILINGUAL_ALERT = {
  fixture: true,
  trigger: "S1 escalated to Critical (fixture)",
  queued: 3,
  languages: ["en", "hi", "ne"],
  messages: [
    { lang: "en", title: "English", text: "LANDSLIDE ALERT (S1 Tathangchen): Critical risk for 2 days. Avoid hillside road. Follow officer instructions." },
    { lang: "hi", title: "Hindi (हिन्दी)", text: "भूस्खलन चेतावनी (S1): 2 दिन तक गंभीर खतरा। पहाड़ी सड़क से बचें। अधिकारी के निर्देश मानें। (फिक्सचर)" },
    { lang: "ne", title: "Nepali (नेपाली)", text: "पहिरो चेतावनी (S1): २ दिन गम्भीर जोखिम। डाँडा बाटो नजानुहोस्। अधिकारीको निर्देशन पालना गर्नुहोस्। (फिक्सचर)" }
  ],
  offline_note: "Cached on device. Queued sync when network returns (fixture)."
};

