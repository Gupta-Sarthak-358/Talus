import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { MINE_ZONES_GEOJSON } from '../data/mineGeoData';

/**
 * Risk-aware routing. Live contract: POST /api/routes/safe
 * Body: { start: {zone_id, lat, lng}, end: {zone_id, lat, lng} }
 * Returns risk_aware_route / shortest_route with lat-lng paths and
 * avoided_zones.
 */

const ROUTE_PRESET_ZONES = {
  worker_zoneA_to_ap1: { start: 'A', end: 'D' },
  truck_zoneB_to_workshop: { start: 'B', end: 'C' },
};

function centroid(zoneId) {
  const geo = MINE_ZONES_GEOJSON.find((g) => g.id === zoneId);
  return geo?.centroid || null;
}

export async function calculateRoute({ originKey = 'worker_zoneA_to_ap1', avoidZoneIds = [] } = {}) {
  const preset = ROUTE_PRESET_ZONES[originKey] || ROUTE_PRESET_ZONES['worker_zoneA_to_ap1'];
  const sCenter = centroid(preset.start);
  const eCenter = centroid(preset.end);
  const start = { zone_id: preset.start, ...(sCenter ? { lat: sCenter[0], lng: sCenter[1] } : {}) };
  const end = { zone_id: preset.end, ...(eCenter ? { lat: eCenter[0], lng: eCenter[1] } : {}) };

  if (isLiveApiEnabled()) {
    const res = await apiRequest('/routes/safe', {
      method: 'POST',
      body: JSON.stringify({ start, end }),
    });
    const aware = res.risk_aware_route || {};
    const normal = res.shortest_route || {};
    const awareDist = aware.total_cost ?? 0;
    const normalDist = normal.total_cost ?? 0;
    const awareRisk = aware.max_risk_exposed ?? 0;
    const normalRisk = normal.max_risk_exposed ?? 0;
    // MineMap draws Polylines from `.waypoints` (lat-lng objects from the API)
    return {
      status: 'success',
      timestamp: new Date().toISOString(),
      origin: start,
      destination: end,
      normalRoute: {
        path: normal.path || [],
        waypoints: normal.path || [],
        distanceKm: +(normalDist).toFixed(2),
        riskExposureScore: normalRisk,
      },
      riskAwareRoute: {
        path: aware.path || [],
        waypoints: aware.path || [],
        distanceKm: +(awareDist).toFixed(2),
        riskExposureScore: awareRisk,
      },
      comparison: {
        distanceDeltaKm: +(awareDist - normalDist).toFixed(2),
        timeDeltaMin: +((awareDist - normalDist) * 1.5).toFixed(1),
        riskReductionPct: normalRisk > 0
          ? Math.round(((normalRisk - awareRisk) / normalRisk) * 100)
          : 0,
        summary:
          `Risk-aware routing avoids zones [${(res.avoided_zones || []).join(', ') || 'none'}] ` +
          `at a cost delta of ${(awareDist - normalDist).toFixed(2)} (graph cost units).`,
      },
      avoidedZones: res.avoided_zones || [],
    };
  }

  await simulateLatency(400);
  return {
    status: 'offline',
    message: 'Routing requires the live backend (VITE_USE_LIVE_API=true). ' +
             'The risk graph lives in the FastAPI service.',
    origin: start, destination: end,
    normalRoute: { path: [], distanceKm: 0, riskExposureScore: 0 },
    riskAwareRoute: { path: [], distanceKm: 0, riskExposureScore: 0 },
    comparison: { distanceDeltaKm: 0, timeDeltaMin: 0, riskReductionPct: 0,
                  summary: 'Offline mode: no route computed.' },
    avoidedZones: [],
  };
}

export const routingCapabilities = { live: isLiveApiEnabled };
