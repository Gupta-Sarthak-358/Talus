/**
 * Talus Comprehensive Mock Dataset
 * Simulates ML Risk Engine (Random Forest + SHAP), Temporal Trend Engine,
 * Role-Based Decision Engine, and Geotechnical CV Crack Analysis.
 */

export const RISK_BANDS = {
  VERY_LOW: { label: "VERY LOW", color: "text-[#5e7f3a]", bg: "bg-[#5e7f3a]/15", border: "border-[#5e7f3a]/30", badgeColor: "#5e7f3a", range: [0, 20] },
  LOW: { label: "LOW", color: "text-[#a68a3c]", bg: "bg-[#a68a3c]/15", border: "border-[#a68a3c]/30", badgeColor: "#a68a3c", range: [21, 40] },
  MODERATE: { label: "MODERATE", color: "text-[#d99a24]", bg: "bg-[#d99a24]/15", border: "border-[#d99a24]/30", badgeColor: "#d99a24", range: [41, 65] },
  HIGH: { label: "HIGH", color: "text-[#d96b24]", bg: "bg-[#d96b24]/15", border: "border-[#d96b24]/30", badgeColor: "#d96b24", range: [66, 84] },
  CRITICAL: { label: "CRITICAL", color: "text-[#c74732]", bg: "bg-[#c74732]/15", border: "border-[#c74732]/30", badgeColor: "#c74732", range: [85, 100] },
};

export const ROLES = [
  { id: "safety_officer", label: "Safety Officer", badge: "Safety Lead", description: "Geotechnical monitoring, early intervention & hazard escalation" },
  { id: "worker", label: "Frontline Worker / Operator", badge: "Field Ops", description: "Immediate safety guidance, hazard avoidance & safe routing" },
  { id: "mine_manager", label: "Mine Operations Manager", badge: "Shift Lead", description: "Operational continuity, resource dispatch & evacuation decisions" },
  { id: "rescue_team", label: "Rescue & Emergency Team", badge: "First Responder", description: "Safe access corridors, casualty extraction & slope stability response" },
];

export const MOCK_ZONES = [
  {
    id: "A",
    name: "Zone A — North Highwall",
    sector: "North Sector",
    risk_score: 34,
    risk_band: "LOW",
    confidence: 91,
    base_risk: 14,
    status: "Normal Operations",
    activePersonnel: 4,
    activeEquipment: "1x Electric Shovel",
    telemetry: {
      slope_angle: 48, // degrees
      rock_type: "Sandstone / Siltstone (RMR 68)",
      crack_density: 3.2, // cracks/m²
      rainfall_24h: 35, // mm
      blast_vibration_ppv: 12.4, // mm/s
      inclinometer_rate: 0.12, // mm/day
    },
    shap: [
      { feature: "Slope Angle (48°)", value: 8, rawValue: "48°", description: "Moderate bench incline" },
      { feature: "Rock Type (RMR 68)", value: 5, rawValue: "Sandstone", description: "Competent bedded rock" },
      { feature: "Rainfall 24h (35mm)", value: 4, rawValue: "35 mm", description: "Light to moderate drainage" },
      { feature: "Crack Density", value: 2, rawValue: "3.2 /m²", description: "Normal hairline joints" },
      { feature: "Blast Vibration", value: 1, rawValue: "12.4 mm/s", description: "Below threshold (15 mm/s)" },
    ],
    trend: {
      direction: "stable",
      delta: "+2 pts in 4h",
      badge: "Stable",
      history: [
        { time: "09:00", risk: 32, label: "09:00 AM" },
        { time: "10:00", risk: 33, label: "10:00 AM" },
        { time: "11:00", risk: 33, label: "11:00 AM" },
        { time: "12:00", risk: 34, label: "12:00 PM" },
        { time: "13:00 (Live)", risk: 34, label: "01:00 PM" },
      ],
    },
    missing_evidence: [],
    role_actions: {
      worker: {
        header: "STANDARD ACCESS PERMITTED",
        action: "Operate with standard PPE. Maintain radio contact on Channel 4.",
        caution: "Stay clear of highwall toe during heavy downpour.",
        routeRecommended: "Route 1 (Standard North Haul)",
        urgency: "Routine",
      },
      safety_officer: {
        header: "ROUTINE MONITORING",
        action: "Next visual inspection scheduled for 16:00. Piezometer levels normal.",
        caution: "Ensure drainage culvert #3 remains unobstructed.",
        routeRecommended: "Normal Inspection Route",
        urgency: "Normal",
      },
      mine_manager: {
        header: "FULL PRODUCTION CLEARANCE",
        action: "Normal haul truck cycle authorized. Target output on schedule.",
        caution: "Review blasting plan for next shift.",
        routeRecommended: "Standard Haulage",
        urgency: "Normal",
      },
      rescue_team: {
        header: "STANDBY / ACCESS CLEAR",
        action: "All access corridors in Zone A are open and clear for emergency response.",
        caution: "None.",
        routeRecommended: "Direct North Gate",
        urgency: "Clear",
      },
    },
  },
  {
    id: "B",
    name: "Zone B — East Haulage & Toe",
    sector: "East Highwall Complex",
    risk_score: 82,
    risk_band: "HIGH",
    confidence: 76,
    base_risk: 16,
    status: "ESCALATING HAZARD — RESTRICTED ACCESS",
    activePersonnel: 6,
    activeEquipment: "2x Haul Trucks (CAT 793F)",
    telemetry: {
      slope_angle: 64, // degrees (Steep)
      rock_type: "Weathered Shale / Mudstone (RMR 38)",
      crack_density: 16.8, // cracks/m² (Severe tension cracks)
      rainfall_24h: 88, // mm (Heavy monsoon accumulation)
      blast_vibration_ppv: 34.2, // mm/s (High dynamic shock)
      inclinometer_rate: 3.8, // mm/day (Rapid accelerating shear)
    },
    shap: [
      { feature: "Slope Angle (64° Highwall)", value: 18, rawValue: "64°", description: "Exceeds safe design angle" },
      { feature: "Rock Type (Weathered Shale)", value: 16, rawValue: "RMR 38 (Weak)", description: "Low shear strength along bedding" },
      { feature: "Crack Density (Tension Joints)", value: 14, rawValue: "16.8 /m²", description: "Active crest tension crack widening" },
      { feature: "Rainfall 24h (88mm Monsoon)", value: 11, rawValue: "88 mm", description: "Pore-pressure saturation at toe" },
      { feature: "Blast Vibration (Recent Shot)", value: 7, rawValue: "34.2 mm/s", description: "Dynamic shock triggered joint slip" },
    ],
    trend: {
      direction: "rising",
      delta: "+41 pts in 4h (Rapid Escalation)",
      badge: "↑ Rising Rapidly",
      history: [
        { time: "09:00", risk: 41, label: "09:00 AM" },
        { time: "10:00", risk: 53, label: "10:00 AM" },
        { time: "11:00", risk: 68, label: "11:00 AM" },
        { time: "12:00", risk: 78, label: "12:00 PM" },
        { time: "13:00 (Live)", risk: 82, label: "01:00 PM" },
      ],
    },
    missing_evidence: [
      { sensor: "Seismograph #B01", reason: "Signal stale > 3h (telemetry lag)", impact: "Vibration decay confidence slightly reduced" },
      { sensor: "Recent Geotechnical Borehole", reason: "Last sampled 60 days ago", impact: "Groundwater phreatic surface interpolated" },
    ],
    missing_evidence_warning: "Risk should be interpreted with incomplete evidence: Live blast vibration sensor #B01 is degraded. Geotechnical confidence calibrated at 76%.",
    role_actions: {
      worker: {
        header: "SAFE ROUTE GUIDANCE — AVOID ZONE B",
        action: "Halt ground operations in Zone B immediately. Do NOT enter the East Haul Road.",
        caution: "Follow Risk-Aware Route 4 to Designated Assembly Area 1 immediately.",
        routeRecommended: "Safe Bypass via Zone C/D",
        urgency: "Immediate Action",
      },
      safety_officer: {
        header: "EARLY RISK INTERVENTION & INSPECTION",
        action: "Zone B risk increased 61 → 82. Primary drivers: Rainfall (88mm) + Tension Crack Propagation (16.8/m²).",
        caution: "Prioritize emergency geotechnical prism survey. Erect exclusion cordon at Bench 06 crest.",
        routeRecommended: "Survey Approach from West Ridge",
        urgency: "High Priority",
      },
      mine_manager: {
        header: "OPERATIONAL RE-ROUTING & SHIFT DECISION",
        action: "Zone B has entered HIGH risk. 3 operational haul corridors affected.",
        caution: "Divert all loaded haulers to South Ramp bypass. Evaluate temporary work stoppage for East Shovel crew.",
        routeRecommended: "Emergency Haulage Protocol 2B",
        urgency: "Urgent Decision",
      },
      rescue_team: {
        header: "RISK-AWARE EMERGENCY RESPONSE",
        action: "Zone B highwall toe is unstable with high rockfall hazard. Avoid direct entry via East Ramp.",
        caution: "Recommended safe staging approach via South Ramp (Route C). Prepare stabilization spotters.",
        routeRecommended: "Route C (Reinforced South Corridor)",
        urgency: "Response Standby",
      },
    },
  },
  {
    id: "C",
    name: "Zone C — Central Pit Floor & Sump",
    sector: "Central Pit Basin",
    risk_score: 58,
    risk_band: "MODERATE",
    confidence: 84,
    base_risk: 15,
    status: "ELEVATED MONITORING — WATER ACCUMULATION",
    activePersonnel: 3,
    activeEquipment: "1x Dewatering Pump Rig",
    telemetry: {
      slope_angle: 32, // degrees
      rock_type: "Massive Sandstone (RMR 55)",
      crack_density: 5.4, // cracks/m²
      rainfall_24h: 88, // mm
      blast_vibration_ppv: 18.2, // mm/s
      inclinometer_rate: 0.45, // mm/day
    },
    shap: [
      { feature: "Rainfall 24h Accumulation", value: 16, rawValue: "88 mm", description: "Surface runoff pooling in sump" },
      { feature: "Rock Type (RMR 55)", value: 11, rawValue: "Sandstone", description: "Moderate strength bench base" },
      { feature: "Slope Angle (32°)", value: 8, rawValue: "32°", description: "Low angle floor transition" },
      { feature: "Crack Density", value: 5, rawValue: "5.4 /m²", description: "Minor floor heave joints" },
      { feature: "Blast Vibration", value: 3, rawValue: "18.2 mm/s", description: "Damped through floor rock" },
    ],
    trend: {
      direction: "rising",
      delta: "+17 pts in 4h",
      badge: "↗ Gradual Rise",
      history: [
        { time: "09:00", risk: 41, label: "09:00 AM" },
        { time: "10:00", risk: 46, label: "10:00 AM" },
        { time: "11:00", risk: 52, label: "11:00 AM" },
        { time: "12:00", risk: 56, label: "12:00 PM" },
        { time: "13:00 (Live)", risk: 58, label: "01:00 PM" },
      ],
    },
    missing_evidence: [],
    role_actions: {
      worker: {
        header: "PROCEED WITH CAUTION",
        action: "Watch for standing water and slick ramp surfaces. Speed limit reduced to 15 km/h.",
        caution: "Maintain 30m buffer from sump pump discharge channels.",
        routeRecommended: "Central High Berm Road",
        urgency: "Caution",
      },
      safety_officer: {
        header: "SUMP CAPACITY SURVEILLANCE",
        action: "Verify dewatering pump #2 flow rate. Monitor pore-pressure transducers at pit bottom.",
        caution: "Inspect sump bank stability every 2 hours during rainfall.",
        routeRecommended: "Pump Station Ramp",
        urgency: "Monitoring",
      },
      mine_manager: {
        header: "PUMPING CAPACITY ALLOCATION",
        action: "Authorize backup diesel dewatering pump unit to prevent haul ramp submergence.",
        caution: "Ensure drainage does not undermine Zone D ramp foundation.",
        routeRecommended: "Standard Operations",
        urgency: "Operational",
      },
      rescue_team: {
        header: "CORRIDOR ACCESSIBLE",
        action: "Zone C floor is navigable by 4WD and heavy response vehicles.",
        caution: "Avoid saturated sump margins.",
        routeRecommended: "Main Spine Ramp",
        urgency: "Clear",
      },
    },
  },
  {
    id: "D",
    name: "Zone D — South Ramp & Staging",
    sector: "South Ramp System",
    risk_score: 28,
    risk_band: "LOW",
    confidence: 88,
    base_risk: 12,
    status: "STABLE ACCESS CORRIDOR",
    activePersonnel: 8,
    activeEquipment: "Haulage Fleet Dispatch & Workshop",
    telemetry: {
      slope_angle: 36, // degrees
      rock_type: "Competent Granulite / Gneiss (RMR 78)",
      crack_density: 2.1, // cracks/m²
      rainfall_24h: 30, // mm
      blast_vibration_ppv: 8.5, // mm/s
      inclinometer_rate: 0.08, // mm/day
    },
    shap: [
      { feature: "Slope Angle (36° Engineered Ramp)", value: 6, rawValue: "36°", description: "Engineered switchback ramp" },
      { feature: "Rock Type (RMR 78 Competent)", value: 4, rawValue: "Granulite", description: "High compressive rock strength" },
      { feature: "Rainfall 24h", value: 3, rawValue: "30 mm", description: "Well-graded concrete drainage ditch" },
      { feature: "Crack Density", value: 2, rawValue: "2.1 /m²", description: "No active tension cracks" },
      { feature: "Blast Vibration", value: 1, rawValue: "8.5 mm/s", description: "Far-field attenuation" },
    ],
    trend: {
      direction: "stable",
      delta: "-1 pt in 4h",
      badge: "Stable",
      history: [
        { time: "09:00", risk: 29, label: "09:00 AM" },
        { time: "10:00", risk: 28, label: "10:00 AM" },
        { time: "11:00", risk: 28, label: "11:00 AM" },
        { time: "12:00", risk: 27, label: "12:00 PM" },
        { time: "13:00 (Live)", risk: 28, label: "01:00 PM" },
      ],
    },
    missing_evidence: [],
    role_actions: {
      worker: {
        header: "PRIMARY SAFE TRANSIT ROUTE",
        action: "Designated as primary haul and evacuation corridor for all pit shifts.",
        caution: "Adhere to one-way traffic signage.",
        routeRecommended: "South Spine Haulway",
        urgency: "Clear",
      },
      safety_officer: {
        header: "DESIGNATED REFUGE CORRIDOR",
        action: "Confirm emergency muster station lights and sirens operational at Assembly Point 1.",
        caution: "Keep crash barriers inspected.",
        routeRecommended: "Access Ramp S",
        urgency: "Routine",
      },
      mine_manager: {
        header: "CLEAR ARTERY FOR TRAFFIC RE-ROUTING",
        action: "Route all diverted traffic from Zone B through South Ramp #2.",
        caution: "Manage convoy spacing to prevent congestion.",
        routeRecommended: "Main Arterial",
        urgency: "Optimized",
      },
      rescue_team: {
        header: "PRIMARY COMMAND & STAGING POINT",
        action: "Staging area at Workshop 01 is clear and fully equipped with triage supplies.",
        caution: "Keep lane 1 clear for rapid medical egress.",
        routeRecommended: "Staging Depot D",
        urgency: "Ready",
      },
    },
  },
  {
    id: "E",
    name: "Zone E — West Overburden & Crusher",
    sector: "West Ridge Dump",
    risk_score: 14,
    risk_band: "VERY LOW",
    confidence: 95,
    base_risk: 10,
    status: "STABILIZED EMBANKMENT",
    activePersonnel: 5,
    activeEquipment: "Primary Crusher #1 & Dozer D10",
    telemetry: {
      slope_angle: 26, // degrees (Terraced)
      rock_type: "Compacted Waste Terraces (RMR 72)",
      crack_density: 1.2, // cracks/m²
      rainfall_24h: 22, // mm
      blast_vibration_ppv: 4.1, // mm/s
      inclinometer_rate: 0.04, // mm/day
    },
    shap: [
      { feature: "Slope Angle (26° Terraced)", value: 2, rawValue: "26°", description: "Low inclination stabilized benches" },
      { feature: "Compacted Overburden", value: 1, rawValue: "Compacted", description: "Compacted berm with hydro-seeding" },
      { feature: "Rainfall 24h", value: 1, rawValue: "22 mm", description: "Engineered cascade runoff catchments" },
    ],
    trend: {
      direction: "stable",
      delta: "0 pts in 4h",
      badge: "Stable",
      history: [
        { time: "09:00", risk: 14, label: "09:00 AM" },
        { time: "10:00", risk: 14, label: "10:00 AM" },
        { time: "11:00", risk: 14, label: "11:00 AM" },
        { time: "12:00", risk: 15, label: "12:00 PM" },
        { time: "13:00 (Live)", risk: 14, label: "01:00 PM" },
      ],
    },
    missing_evidence: [],
    role_actions: {
      worker: {
        header: "STANDARD INDUSTRIAL ACCESS",
        action: "Crusher tipping bays operational. Follow standard dump protocols.",
        caution: "Maintain spotter communication during reverse dumping.",
        routeRecommended: "Crusher Access West",
        urgency: "Normal",
      },
      safety_officer: {
        header: "BENCH SETTLEMENT STABLE",
        action: "Subsurface radar confirms 0.04 mm/day stability. No anomalies.",
        caution: "Routine radar scan checks.",
        routeRecommended: "West Berm Road",
        urgency: "Routine",
      },
      mine_manager: {
        header: "CRUSHER THROUGHOUT AT 100%",
        action: "Crusher feed operating at nominal 2,400 TPH capacity.",
        caution: "Maintain stockpile management.",
        routeRecommended: "Feed Hopper Route",
        urgency: "Normal",
      },
      rescue_team: {
        header: "SECONDARY HELIPAD / EVAC POINT",
        action: "West Ridge Flat cleared for medevac helicopter landing if required.",
        caution: "Keep windsock visible.",
        routeRecommended: "West Crest Pad",
        urgency: "Standby",
      },
    },
  },
];

export const MOCK_ALERTS = [
  {
    id: "ALT-01",
    zoneId: "B",
    zoneName: "Zone B — East Haulage & Toe",
    severity: "HIGH",
    title: "Zone B Risk Escalation (61 → 82 / 100)",
    summary: "Rapid geotechnical risk escalation detected on Benches 06–08 due to heavy monsoon infiltration and tension crack opening.",
    drivers: ["Rainfall: 88mm / 24h", "Crack Density: 16.8/m²", "Slope Angle: 64° Highwall"],
    timestamp: "2 mins ago",
    rawTimestamp: "2026-08-21T12:58:00Z",
    acknowledged: false,
    roleDirectives: {
      worker: "EVACUATE East Haulage immediately. Divert to Route 4 (Assembly Point 1).",
      safety_officer: "Issue urgent inspection hold. Deploy drone crack survey and check piezometers.",
      mine_manager: "Halt hauler dispatch through East Ramp. Activate contingency routing protocol.",
      rescue_team: "Stage rescue vehicle at South Ramp Depot. Avoid direct entry below highwall toe.",
    },
  },
  {
    id: "ALT-02",
    zoneId: "C",
    zoneName: "Zone C — Central Pit Floor",
    severity: "MODERATE",
    title: "Surface Water Accumulation in Sump Area",
    summary: "Water table rise in central sump. Floor gradient indicates minor runoff pooling near hauler turn.",
    drivers: ["Rainfall Accumulation: 88mm", "Sump Flow: 320 m³/h"],
    timestamp: "18 mins ago",
    rawTimestamp: "2026-08-21T12:42:00Z",
    acknowledged: false,
    roleDirectives: {
      worker: "Exercise reduced speed (15 km/h) on wet central ramp.",
      safety_officer: "Verify dewatering pump rig #2 status and floor stability.",
      mine_manager: "Authorize auxiliary drainage diesel pump.",
      rescue_team: "Floor remains accessible; use 4WD for central transit.",
    },
  },
  {
    id: "ALT-03",
    zoneId: "B",
    zoneName: "Zone B — Seismograph Telemetry Degraded",
    severity: "MODERATE",
    title: "Telemetry Data Degraded (Sensor SEIS-B01)",
    summary: "Seismograph #B01 signal delayed > 3h. ML model confidence adjusted to 76% under missing evidence protocol.",
    drivers: ["Sensor Timeout: 184 mins", "Missing Blast Vibration live feed"],
    timestamp: "45 mins ago",
    rawTimestamp: "2026-08-21T12:15:00Z",
    acknowledged: true,
    roleDirectives: {
      worker: "Standard telemetry warning in effect.",
      safety_officer: "Dispatch instrumentation tech to inspect telemetry gateway SEIS-B01.",
      mine_manager: "Note confidence uncertainty on shift log.",
      rescue_team: "Rely on optical radar telemetry for slope movement.",
    },
  },
];

export const WHAT_IF_PRESETS = [
  {
    id: "monsoon",
    name: "🌧️ Heavy Monsoon Downpour",
    description: "Simulates severe 24h rainfall (95 mm) with pore pressure escalation across highwalls",
    values: {
      rainfall_24h: 95,
      blast_vibration: 20,
      crack_density: 18,
      slope_angle: 64,
    },
    expectedImpact: "Zone B escalates into CRITICAL (89/100); Zone C increases to HIGH (72/100)",
  },
  {
    id: "blast",
    name: "💥 Deep Production Blast Shock",
    description: "Simulates high-yield bench blast (PPV 42 mm/s) near East Highwall shear zone",
    values: {
      rainfall_24h: 40,
      blast_vibration: 42,
      crack_density: 14,
      slope_angle: 64,
    },
    expectedImpact: "Vibration contribution spikes (+22 pts SHAP), increasing dynamic instability",
  },
  {
    id: "cracking",
    name: "⚡ Progressive Crest Tension Cracking",
    description: "Simulates rapid tension crack widening detected by drone inspection (24 cracks/m²)",
    values: {
      rainfall_24h: 30,
      blast_vibration: 12,
      crack_density: 24,
      slope_angle: 68,
    },
    expectedImpact: "Crack density becomes primary SHAP contributor (+28 pts); imminent planar slip risk",
  },
  {
    id: "baseline",
    name: "☀️ Dry Stabilized Baseline",
    description: "Simulates dry conditions, fully repaired drainage, and low vibration",
    values: {
      rainfall_24h: 5,
      blast_vibration: 6,
      crack_density: 2,
      slope_angle: 45,
    },
    expectedImpact: "All zones return to LOW / VERY LOW operational baseline risk",
  },
];

export const CV_SAMPLE_ANALYSES = [
  {
    id: "CV-B01",
    zoneId: "B",
    zoneName: "Zone B — Bench 07 Crest",
    imageName: "drone_highwall_bench07_ortho.jpg",
    captureTimestamp: "2026-08-21 11:30 AM (DJI Matrice 350 RTK)",
    resolution: "1.2 cm/pixel GSD",
    crackCount: 4,
    maxCrackLengthMeters: 5.4,
    totalCrackLengthMeters: 14.8,
    crackDensityPerSqm: 16.8,
    dominantOrientation: "N 42° E (Parallel to Highwall Strike)",
    shearDisplacementMm: 12.5,
    aiModel: "YOLOv8-Seg + UNet Geotechnical Crack Profiler (Simulated backend CV)",
    confidence: 94.2,
    riskInterpretation: "High severity tension crack opening along bedding plane. Direct indicator of incipient planar failure.",
    detectedCracks: [
      { id: 1, label: "Tension Crack #1", length: "5.4 m", width: "3.2 cm", strike: "N42°E", severity: "Severe" },
      { id: 2, label: "Secondary Splinter", length: "3.8 m", width: "1.8 cm", strike: "N38°E", severity: "Moderate" },
      { id: 3, label: "Hairline Joint Set", length: "2.9 m", width: "0.6 cm", strike: "N45°E", severity: "Minor" },
      { id: 4, label: "Toe Bulge Fracture", length: "2.7 m", width: "2.1 cm", strike: "N40°E", severity: "High" },
    ]
  }
];
