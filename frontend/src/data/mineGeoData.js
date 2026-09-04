/**
 * GIS and Geometrical Coordinates for Gangtok Cluster, Sikkim (SIH26001 Sept-5 Demo)
 * Pilot Center: Gangtok cluster (27.3389, 88.6065, EPSG:4326 demo)
 * Slopes: S1 (Tathangchen), S2 (Chandmari), S3 (Tadong), S4 (Ranipool)
 */

export const MINE_CENTER = [27.3389, 88.6065]; // Gangtok cluster centre
export const MINE_ZOOM = 13;

// Defined Slope Zones with realistic hill-slope bounding polygons
export const MINE_ZONES_GEOJSON = [
  {
    id: "S1",
    name: "S1 — Tathangchen (upper)",
    village: "Tathangchen",
    type: "Upper Hillside Slope",
    benches: "Upper Ridge Corridor",
    coordinates: [
      [27.3485, 88.5960],
      [27.3490, 88.6050],
      [27.3420, 88.6060],
      [27.3410, 88.5970],
    ],
    centroid: [27.3450, 88.6000],
    area_hectares: 18.5,
    sensorIds: ["IMD-GTK-01", "INC-S1-01"],
  },
  {
    id: "S2",
    name: "S2 — Chandmari (road-cut)",
    village: "Chandmari",
    type: "Active Road-Cut Slope",
    benches: "Highway Cut Benches",
    coordinates: [
      [27.3415, 88.6080],
      [27.3420, 88.6160],
      [27.3345, 88.6165],
      [27.3340, 88.6085],
    ],
    centroid: [27.3380, 88.6120],
    area_hectares: 14.2,
    sensorIds: ["EXT-S2-01", "PZ-S2-02"],
  },
  {
    id: "S3",
    name: "S3 — Tadong (mid)",
    village: "Tadong",
    type: "Mid-Slope Inhabited Sector",
    benches: "Mid Valley Transition",
    coordinates: [
      [27.3290, 88.6020],
      [27.3295, 88.6110],
      [27.3210, 88.6115],
      [27.3205, 88.6025],
    ],
    centroid: [27.3250, 88.6065],
    area_hectares: 22.0,
    sensorIds: ["SM-S3-01", "FLOW-S3-02"],
  },
  {
    id: "S4",
    name: "S4 — Ranipool (valley)",
    village: "Ranipool",
    type: "Valley Staging & Egress",
    benches: "River Basin Flats",
    coordinates: [
      [27.3190, 88.5900],
      [27.3195, 88.6000],
      [27.3110, 88.6005],
      [27.3105, 88.5905],
    ],
    centroid: [27.3150, 88.5950],
    area_hectares: 28.4,
    sensorIds: ["STG-S4-01", "WX-S4-02"],
  },
];

// Road Network Segments from data/sih26001/fixtures/roads.json
export const ROAD_SEGMENTS = [
  {
    id: "R1",
    name: "Tathangchen link",
    status: "blocked",
    adjacent_slope: "S1",
    description: "Tathangchen access link — completely blocked by debris",
    coordinates: [
      [27.3450, 88.6000],
      [27.3425, 88.6030],
      [27.3400, 88.6045],
    ],
    color: "#c74732", // Critical red
  },
  {
    id: "R2",
    name: "Ridge shortcut S1-S4",
    status: "at-risk",
    adjacent_slope: "S1",
    description: "Ridge shortcut S1-S4 — severe tension crack hazard (avoided by safe routing)",
    coordinates: [
      [27.3450, 88.6000],
      [27.3370, 88.6020],
      [27.3280, 88.5980],
      [27.3150, 88.5950],
    ],
    color: "#d96b24", // High orange
  },
  {
    id: "R3",
    name: "Valley road S3-S4",
    status: "open",
    adjacent_slope: "S3",
    description: "Valley road S3-S4 — open and monitored",
    coordinates: [
      [27.3450, 88.6000],
      [27.3350, 88.6090],
      [27.3250, 88.6065],
    ],
    color: "#5e7f3a", // Safe green
  },
  {
    id: "R4",
    name: "Ranipool approach",
    status: "open",
    adjacent_slope: "S4",
    description: "Ranipool approach corridor — reinforced and clear",
    coordinates: [
      [27.3250, 88.6065],
      [27.3200, 88.6010],
      [27.3150, 88.5950],
    ],
    color: "#5e7f3a", // Safe green
  },
];

// NER Infrastructure & Staging Landmarks
export const MINE_INFRASTRUCTURE = [
  {
    id: "AP-1",
    name: "Ranipool Staging & Evacuation Center",
    type: "assembly",
    coordinates: [27.3140, 88.5940],
    capacity: "450 Evacuees / SDRF Staging",
    status: "Active / Clear",
  },
  {
    id: "AP-2",
    name: "Tadong Community Shelter",
    type: "assembly",
    coordinates: [27.3235, 88.6050],
    capacity: "180 Personnel",
    status: "Active / Monitored",
  },
  {
    id: "DISPATCH-01",
    name: "Gangtok District Disaster Emergency Ops (DEOC)",
    type: "facility",
    coordinates: [27.3320, 88.6140],
    status: "Operational 24/7",
  },
  {
    id: "DEPOT-01",
    name: "PWD Heavy Machine Staging Depot",
    type: "facility",
    coordinates: [27.3160, 88.5965],
    status: "Earthmovers & Excavators Ready",
  },
];

// Sensor Stations deployed across pilot cluster
export const MINE_SENSORS = [
  {
    id: "IMD-GTK-01",
    name: "IMD Gangtok Automatic Weather Station",
    type: "Rain Gauge / IMD Fixture",
    coordinates: [27.3465, 88.6025],
    zone: "S1",
    status: "online",
    reading: "24h Rain: 88 mm (Peak: 132 mm forecast)",
  },
  {
    id: "EXT-S2-01",
    name: "Chandmari Road-Cut Crack Extensometer",
    type: "Displacement / Tension Joint",
    coordinates: [27.3385, 88.6130],
    zone: "S2",
    status: "degraded",
    reading: "Displacement: 5.4 mm (OSM QA unverified)",
  },
  {
    id: "SM-S3-01",
    name: "Tadong Soil Moisture Probe",
    type: "ERA5 Reanalysis Proxy",
    coordinates: [27.3260, 88.6075],
    zone: "S3",
    status: "online",
    reading: "Soil Saturation: 76% (Near Threshold)",
  },
  {
    id: "STG-S4-01",
    name: "Ranipool River Stage Gauge",
    type: "River Basin Hydrology",
    coordinates: [27.3145, 88.5935],
    zone: "S4",
    status: "online",
    reading: "Water Level: 2.1 m (Normal discharge)",
  },
];

// Precomputed Routing Paths according to roads.json:
// origin: S1 (Tathangchen), destination: S4 (Ranipool)
// Shortest: via R2 (crosses at-risk R2)
// Risk-Aware: via S1 -> S3 -> S4 using R3 and R4 (avoids R2)
export const PRECOMPUTED_ROUTES = {
  "worker_zoneA_to_ap1": {
    origin: "S1 — Tathangchen (upper)",
    destination: "S4 — Ranipool (valley)",
    normalRoute: {
      id: "normal_route_1",
      name: "Shortest Route (via Ridge Shortcut R2)",
      distanceKm: 4.8,
      total_cost: 10.0,
      estimatedTimeMin: 18,
      riskExposureScore: 89,
      riskExposureBand: "CRITICAL",
      passesThroughHazardZone: "S1 & R2 (At-Risk Ridge)",
      hazardDescription: "Directly traverses at-risk segment R2 below Tathangchen tension crack zone",
      color: "#c74732",
      dashArray: "6, 6",
      waypoints: [
        [27.3450, 88.6000], // S1
        [27.3370, 88.6020], // R2 midpoint
        [27.3280, 88.5980], // R2 lower
        [27.3150, 88.5950], // S4 Ranipool
      ]
    },
    riskAwareRoute: {
      id: "risk_aware_route_1",
      name: "Risk-Aware Safe Route (via Tadong Valley R3 + R4)",
      distanceKm: 6.2,
      total_cost: 12.5,
      estimatedTimeMin: 24,
      riskExposureScore: 66,
      riskExposureBand: "MODERATE",
      passesThroughHazardZone: "None (Bypasses R2 & S1)",
      hazardDescription: "Avoids at-risk segment R2 and critical slope S1; diverts safely through Tadong Valley",
      color: "#5e7f3a",
      dashArray: null,
      waypoints: [
        [27.3450, 88.6000], // S1 origin
        [27.3350, 88.6090], // R3 descent
        [27.3250, 88.6065], // S3 Tadong
        [27.3200, 88.6010], // R4 approach
        [27.3150, 88.5950], // S4 Ranipool
      ]
    },
    avoidedZones: ["S1"],
    avoidedSegments: ["R2"],
  },
  "s1_to_s4": {
    origin: "S1 — Tathangchen",
    destination: "S4 — Ranipool Staging",
    normalRoute: {
      id: "shortest_r2",
      name: "Shortest Route (via R2)",
      distanceKm: 4.8,
      total_cost: 10.0,
      estimatedTimeMin: 18,
      riskExposureScore: 89,
      riskExposureBand: "CRITICAL",
      passesThroughHazardZone: "R2 Ridge Shortcut",
      hazardDescription: "Crosses segment R2 directly adjacent to unstable slope S1",
      color: "#c74732",
      dashArray: "6, 6",
      waypoints: [
        [27.3450, 88.6000],
        [27.3370, 88.6020],
        [27.3280, 88.5980],
        [27.3150, 88.5950],
      ]
    },
    riskAwareRoute: {
      id: "safe_r3_r4",
      name: "Safe Route (via R3 & R4)",
      distanceKm: 6.2,
      total_cost: 12.5,
      estimatedTimeMin: 24,
      riskExposureScore: 66,
      riskExposureBand: "MODERATE",
      passesThroughHazardZone: "None",
      hazardDescription: "Safely diverts via Tadong and Ranipool approach, completely avoiding R2",
      color: "#5e7f3a",
      dashArray: null,
      waypoints: [
        [27.3450, 88.6000],
        [27.3350, 88.6090],
        [27.3250, 88.6065],
        [27.3200, 88.6010],
        [27.3150, 88.5950],
      ]
    },
    avoidedZones: ["S1"],
    avoidedSegments: ["R2"],
  }
};

