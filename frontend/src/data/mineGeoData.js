/**
 * Mine GIS and Geometrical Coordinates for Open-Pit Topography
 * Centered around an open-pit mine layout (coordinates relative to a synthetic mine bounding box)
 */

export const MINE_CENTER = [11.47, 79.48]; // Neyveli Mine-II excavation belt (SW of township; IMD cell 11.50N 79.50E)
export const MINE_ZOOM = 15;

// Defined Mine Zones with realistic terraced polygons
export const MINE_ZONES_GEOJSON = [
  {
    id: "A",
    name: "Zone A — North Highwall",
    type: "Highwall Sector",
    benches: "Benches 01–04",
    coordinates: [
      [11.477, 79.475],
      [11.4775, 79.482],
      [11.4735, 79.4835],
      [11.4725, 79.4765],
    ],
    centroid: [11.4751, 79.4792],
    area_hectares: 14.2,
    sensorIds: ["INC-A01", "PZ-A02"],
  },
  {
    id: "B",
    name: "Zone B — East Haulage & Toe",
    type: "Critical Haulage & Slope",
    benches: "Benches 05–08",
    coordinates: [
      [11.4735, 79.4835],
      [11.4775, 79.482],
      [11.474, 79.49],
      [11.4685, 79.4895],
      [11.4695, 79.483],
    ],
    centroid: [11.4725, 79.4865],
    area_hectares: 18.6,
    sensorIds: ["SEIS-B01", "PZ-B02", "RADAR-01"],
  },
  {
    id: "C",
    name: "Zone C — Central Pit Floor & Sump",
    type: "Pit Floor / Dewatering Sump",
    benches: "Pit Bottom Floor",
    coordinates: [
      [11.4725, 79.4765],
      [11.4735, 79.4835],
      [11.4695, 79.483],
      [11.4665, 79.478],
      [11.468, 79.474],
    ],
    centroid: [11.47, 79.479],
    area_hectares: 21.0,
    sensorIds: ["SUMP-C01", "FLOW-C02"],
  },
  {
    id: "D",
    name: "Zone D — South Ramp & Staging",
    type: "Access Ramp & Staging",
    benches: "Ramp System S",
    coordinates: [
      [11.468, 79.474],
      [11.4665, 79.478],
      [11.4695, 79.483],
      [11.4645, 79.484],
      [11.462, 79.476],
    ],
    centroid: [11.466, 79.479],
    area_hectares: 16.8,
    sensorIds: ["INC-D01"],
  },
  {
    id: "E",
    name: "Zone E — West Overburden & Crusher",
    type: "Overburden Dump / Crusher Ridge",
    benches: "Dump Terraces 1-2",
    coordinates: [
      [11.477, 79.475],
      [11.4725, 79.4765],
      [11.468, 79.474],
      [11.462, 79.476],
      [11.464, 79.469],
      [11.474, 79.468],
    ],
    centroid: [11.4705, 79.4715],
    area_hectares: 26.4,
    sensorIds: ["WX-E01", "SEIS-E02"],
  },
];

// Open-Pit Infrastructure & Landmarks
export const MINE_INFRASTRUCTURE = [
  {
    id: "AP-1",
    name: "Assembly Point 1 (South Safe Zone)",
    type: "assembly",
    coordinates: [11.4615, 79.475],
    capacity: "120 Personnel",
    status: "Active / Clear",
  },
  {
    id: "AP-2",
    name: "Assembly Point 2 (West Crusher Station)",
    type: "assembly",
    coordinates: [11.4755, 79.4675],
    capacity: "80 Personnel",
    status: "Active / Clear",
  },
  {
    id: "CRUSHER-01",
    name: "Primary In-Pit Crusher #1",
    type: "facility",
    coordinates: [11.4745, 79.4695],
    status: "Operational",
  },
  {
    id: "WORKSHOP-01",
    name: "Heavy Equipment Maintenance Workshop",
    type: "facility",
    coordinates: [11.4625, 79.483],
    status: "Operational",
  },
  {
    id: "EXC-04",
    name: "Electric Shovel / Excavator Site #4",
    type: "equipment",
    coordinates: [11.475, 79.478],
    zone: "A",
    status: "Operating (2 Operators)",
  },
  {
    id: "TRUCK-12",
    name: "Haul Truck #12 (CAT 793F)",
    type: "equipment",
    coordinates: [11.4715, 79.487],
    zone: "B",
    status: "In Transit / High Risk Corridor",
  },
];

// Sensor Stations deployed across pit
export const MINE_SENSORS = [
  {
    id: "WX-E01",
    name: "Meteorological Station #01",
    type: "Weather / Rain Gauge",
    coordinates: [11.474, 79.4685],
    zone: "E",
    status: "online",
    reading: "Rainfall: 42 mm/24h",
  },
  {
    id: "SEIS-B01",
    name: "Triaxial Seismograph #B01",
    type: "Blast Vibration (PPV)",
    coordinates: [11.471, 79.488],
    zone: "B",
    status: "degraded", // Stale / degraded to highlight missing evidence
    reading: "PPV: 24.5 mm/s (Stale > 3h)",
  },
  {
    id: "RADAR-01",
    name: "Ground-Based SAR Slope Radar",
    type: "Displacement / Velocity",
    coordinates: [11.4675, 79.472],
    zone: "E",
    status: "online",
    reading: "Velocity: 1.8 mm/day",
  },
  {
    id: "PZ-B02",
    name: "Vibrating Wire Piezometer PZ-02",
    type: "Pore Water Pressure",
    coordinates: [11.4745, 79.486],
    zone: "B",
    status: "online",
    reading: "Pressure: 142 kPa",
  },
  {
    id: "INC-A01",
    name: "In-Place Inclinometer I-A01",
    type: "Subsurface Shear Strain",
    coordinates: [11.476, 79.48],
    zone: "A",
    status: "online",
    reading: "Deflection: 0.4 mm",
  },
];

// Routing Graph Waypoints & Calculated Paths
export const PRECOMPUTED_ROUTES = {
  "worker_zoneA_to_ap1": {
    origin: "Zone A (Worker Crew #3)",
    destination: "Assembly Point 1",
    normalRoute: {
      id: "normal_route_1",
      name: "Shortest Route (via Zone B East Ramp)",
      distanceKm: 1.2,
      estimatedTimeMin: 4.5,
      riskExposureScore: 0.76,
      riskExposureBand: "HIGH",
      passesThroughHazardZone: "Zone B",
      hazardDescription: "Directly traverses active rockfall trajectory below East Highwall Toe",
      color: "#c74732",
      dashArray: "6, 6",
      waypoints: [
        [11.475, 79.478], // Zone A origin
        [11.474, 79.483],
        [11.4725, 79.4865], // Traverses dead center of risky Zone B
        [11.4695, 79.487], // Near unstable toe
        [11.465, 79.484],
        [11.4615, 79.475], // Assembly Point 1
      ]
    },
    riskAwareRoute: {
      id: "risk_aware_route_1",
      name: "Risk-Aware Safe Route (via Central Sump & West Ridge)",
      distanceKm: 1.5,
      estimatedTimeMin: 6.0,
      riskExposureScore: 0.18,
      riskExposureBand: "LOW",
      passesThroughHazardZone: "None",
      hazardDescription: "Safely diverts around hazardous Zone B highwall, adhering to reinforced benches",
      color: "#5e7f3a",
      dashArray: null,
      waypoints: [
        [11.475, 79.478], // Zone A origin
        [11.4725, 79.4765], // Diverts down through safe Zone C ramp
        [11.47, 79.4785],
        [11.467, 79.476], // Follows protected Zone D haul corridor
        [11.4635, 79.475],
        [11.4615, 79.475], // Assembly Point 1
      ]
    }
  },
  "truck_zoneB_to_workshop": {
    origin: "Zone B (Haul Truck #12)",
    destination: "Maintenance Workshop",
    normalRoute: {
      id: "normal_route_2",
      name: "Direct Toe Haul Road",
      distanceKm: 0.8,
      estimatedTimeMin: 3.0,
      riskExposureScore: 0.84,
      riskExposureBand: "CRITICAL",
      passesThroughHazardZone: "Zone B Highwall",
      hazardDescription: "Runs along toe of unstable bench facing potential planar slide",
      color: "#c74732",
      dashArray: "6, 6",
      waypoints: [
        [11.4715, 79.487],
        [11.4685, 79.486],
        [11.465, 79.4845],
        [11.4625, 79.483],
      ]
    },
    riskAwareRoute: {
      id: "risk_aware_route_2",
      name: "Upper Berm Bypass Route",
      distanceKm: 1.3,
      estimatedTimeMin: 5.2,
      riskExposureScore: 0.22,
      riskExposureBand: "LOW",
      passesThroughHazardZone: "None",
      hazardDescription: "Routes up through stabilized secondary switchback",
      color: "#5e7f3a",
      dashArray: null,
      waypoints: [
        [11.4715, 79.487],
        [11.47, 79.481],
        [11.4665, 79.479],
        [11.4635, 79.481],
        [11.4625, 79.483],
      ]
    }
  }
};
