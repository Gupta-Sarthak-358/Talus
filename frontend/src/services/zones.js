import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { MOCK_ZONES } from '../data/mockData';
import { MINE_ZONES_GEOJSON } from '../data/mineGeoData';

/**
 * Fetch all mine zones summary and geometry
 * Contract: GET /api/zones
 */
export async function getZones() {
  if (isLiveApiEnabled()) {
    return apiRequest('/zones');
  }

  // Simulated latency for smooth UX
  await simulateLatency(250);

  // Combine mock zones with GeoJSON coordinates
  const mergedZones = MOCK_ZONES.map((zone) => {
    const geo = MINE_ZONES_GEOJSON.find((g) => g.id === zone.id);
    return {
      ...zone,
      geometry: geo ? { coordinates: geo.coordinates, centroid: geo.centroid, benches: geo.benches } : null,
    };
  });

  return {
    status: 'success',
    timestamp: new Date().toISOString(),
    zones: mergedZones,
  };
}

/**
 * Fetch complete zone intelligence by ID (Risk, SHAP, Trends, Telemetry, Role actions)
 * Contract: GET /api/zones/{zone_id}
 */
export async function getZoneById(zoneId) {
  if (isLiveApiEnabled()) {
    return apiRequest(`/zones/${zoneId}`);
  }

  await simulateLatency(200);

  const zone = MOCK_ZONES.find((z) => z.id === zoneId);
  if (!zone) {
    throw new Error(`Zone with ID '${zoneId}' not found.`);
  }

  const geo = MINE_ZONES_GEOJSON.find((g) => g.id === zone.id);

  return {
    status: 'success',
    zone: {
      ...zone,
      geometry: geo ? { coordinates: geo.coordinates, centroid: geo.centroid, benches: geo.benches } : null,
    },
  };
}
