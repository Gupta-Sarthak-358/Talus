/**
 * Mine GIS and Geometrical Coordinates for Open-Pit Topography
 * Centered around an open-pit mine layout (coordinates relative to a synthetic mine bounding box)
 */

export const MINE_CENTER = [23.7540, 86.4250]; // Open-cast mining belt coordinate center
export const MINE_ZOOM = 15;

// Defined Mine Zones with realistic terraced polygons
export const MINE_ZONES_GEOJSON = [
  {
    id: "A",
    name: "Zone A — North Highwall",
    type: "Highwall Sector",
    benches: "Benches 01–04",
    coordinates: [
      [23.7610, 86.4200],
      [23.7615, 86.4270],
      [23.7575, 86.4285],
      [23.7565, 86.4215],
    ],
    centroid: [23.7591, 86.4242],
    area_hectares: 14.2,
    sensorIds: ["INC-A01", "PZ-A02"],
  },
  {
    id: "B",
    name: "Zone B — East Haulage & Toe",
    type: "Critical Haulage & Slope",
    benches: "Benches 05–08",
    coordinates: [
      [23.7575, 86.4285],
      [23.7615, 86.4270],
      [23.7580, 86.4350],
      [23.7525, 86.4345],
      [23.7535, 86.4280],
    ],
    centroid: [23.7565, 86.4315],
    area_hectares: 18.6,
    sensorIds: ["SEIS-B01", "PZ-B02", "RADAR-01"],
  },
  {
    id: "C",
    name: "Zone C — Central Pit Floor & Sump",
    type: "Pit Floor / Dewatering Sump",
    benches: "Pit Bottom Floor",
    coordinates: [
      [23.7565, 86.4215],
      [23.7575, 86.4285],
      [23.7535, 86.4280],
      [23.7505, 86.4230],
      [23.7520, 86.4190],
    ],
    centroid: [23.7540, 86.4240],
    area_hectares: 21.0,
    sensorIds: ["SUMP-C01", "FLOW-C02"],
  },
  {
    id: "D",
    name: "Zone D — South Ramp & Staging",
    type: "Access Ramp & Staging",
    benches: "Ramp System S",
    coordinates: [
      [23.7520, 86.4190],
      [23.7505, 86.4230],
      [23.7535, 86.4280],
      [23.7485, 86.4290],
      [23.7460, 86.4210],
    ],
    centroid: [23.7500, 86.4240],
    area_hectares: 16.8,
    sensorIds: ["INC-D01"],
  },
  {
    id: "E",
    name: "Zone E — West Overburden & Crusher",
    type: "Overburden Dump / Crusher Ridge",
    benches: "Dump Terraces 1-2",
    coordinates: [
      [23.7610, 86.4200],
      [23.7565, 86.4215],
      [23.7520, 86.4190],
      [23.7460, 86.4210],
      [23.7480, 86.4140],
      [23.7580, 86.4130],
    ],
    centroid: [23.7545, 86.4165],
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
    coordinates: [23.7455, 86.4200],
    capacity: "120 Personnel",
    status: "Active / Clear",
  },
  {
    id: "AP-2",
    name: "Assembly Point 2 (West Crusher Station)",
    type: "assembly",
    coordinates: [23.7595, 86.4125],
    capacity: "80 Personnel",
    status: "Active / Clear",
  },
  {
    id: "CRUSHER-01",
    name: "Primary In-Pit Crusher #1",
    type: "facility",
    coordinates: [23.7585, 86.4145],
    status: "Operational",
  },
  {
    id: "WORKSHOP-01",
    name: "Heavy Equipment Maintenance Workshop",
    type: "facility",
    coordinates: [23.7465, 86.4280],
    status: "Operational",
  },
  {
    id: "EXC-04",
    name: "Electric Shovel / Excavator Site #4",
    type: "equipment",
    coordinates: [23.7590, 86.4230],
    zone: "A",
    status: "Operating (2 Operators)",
  },
  {
    id: "TRUCK-12",
    name: "Haul Truck #12 (CAT 793F)",
    type: "equipment",
    coordinates: [23.7555, 86.4320],
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
    coordinates: [23.7580, 86.4135],
    zone: "E",
    status: "online",
    reading: "Rainfall: 42 mm/24h",
  },
  {
    id: "SEIS-B01",
    name: "Triaxial Seismograph #B01",
    type: "Blast Vibration (PPV)",
    coordinates: [23.7550, 86.4330],
    zone: "B",
    status: "degraded", // Stale / degraded to highlight missing evidence
    reading: "PPV: 24.5 mm/s (Stale > 3h)",
  },
  {
    id: "RADAR-01",
    name: "Ground-Based SAR Slope Radar",
    type: "Displacement / Velocity",
    coordinates: [23.7515, 86.4170],
    zone: "E",
    status: "online",
    reading: "Velocity: 1.8 mm/day",
  },
  {
    id: "PZ-B02",
    name: "Vibrating Wire Piezometer PZ-02",
    type: "Pore Water Pressure",
    coordinates: [23.7585, 86.4310],
    zone: "B",
    status: "online",
    reading: "Pressure: 142 kPa",
  },
  {
    id: "INC-A01",
    name: "In-Place Inclinometer I-A01",
    type: "Subsurface Shear Strain",
    coordinates: [23.7600, 86.4250],
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
      color: "#ef4444",
      dashArray: "6, 6",
      waypoints: [
        [23.7590, 86.4230], // Zone A origin
        [23.7580, 86.4280],
        [23.7565, 86.4315], // Traverses dead center of risky Zone B
        [23.7535, 86.4320], // Near unstable toe
        [23.7490, 86.4290],
        [23.7455, 86.4200], // Assembly Point 1
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
      color: "#10b981",
      dashArray: null,
      waypoints: [
        [23.7590, 86.4230], // Zone A origin
        [23.7565, 86.4215], // Diverts down through safe Zone C ramp
        [23.7540, 86.4235],
        [23.7510, 86.4210], // Follows protected Zone D haul corridor
        [23.7475, 86.4200],
        [23.7455, 86.4200], // Assembly Point 1
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
      color: "#ef4444",
      dashArray: "6, 6",
      waypoints: [
        [23.7555, 86.4320],
        [23.7525, 86.4310],
        [23.7490, 86.4295],
        [23.7465, 86.4280],
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
      color: "#10b981",
      dashArray: null,
      waypoints: [
        [23.7555, 86.4320],
        [23.7540, 86.4260],
        [23.7505, 86.4240],
        [23.7475, 86.4260],
        [23.7465, 86.4280],
      ]
    }
  }
};
