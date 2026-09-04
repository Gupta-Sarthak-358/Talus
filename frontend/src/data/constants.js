/**
 * Talus — Live domain constants (SIH26001 NER landslide)
 * No mock arrays here. Former MOCK_* pruned 2026-09-03.
 * Live data: /api/zones, /api/reports/queue, /api/simulation/*, /api/roads/status, /api/alerts/dispatch
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

/**
 * What-If UI presets — derived from real thresholds (Monga 2026 MDL, Dahal & Hasegawa 2008 Himalayan).
 * These are UI shortcuts that populate slider values; execution is live via POST /api/simulation/what-if.
 * Not mock data — they drive live model inference.
 */
export const WHAT_IF_PRESETS = [
  {
    id: "monsoon-s3",
    name: "🌧️ S3 Extreme 24h Rain (132 mm)",
    description: "Overrides S3 rainfall_24h_mm to 132 mm (forecast peak). Demonstrates live ML counterfactual.",
    values: {
      rainfall_24h: 132,
      blast_vibration: 10,
      crack_density: 0.5,
      slope_angle: 28,
    },
    targetZone: "S3",
    expectedImpact: "S3 risk score shifts 66 → 74 (delta = +8 pts). Live counterfactual via /api/simulation/what-if.",
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
