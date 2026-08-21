import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';

/**
 * Risk-aware routing. Live contract: POST /api/routes/safe
 * Body: { start: {zone_id, lat, lng}, end: {zone_id, lat, lng} }
 * Returns risk_aware_route / shortest_route with lat-lng paths and
 * avoided_zones.
 */

export async function calculateRoute({ start = { zone_id: 'A', lat: 20.51, lng: 80.115 },
                                       end = { zone_id: 'D', lat: 20.58, lng: 80.165 } } = {}) {
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
    return {
      status: 'success',
      timestamp: new Date().toISOString(),
      origin: start,
      destination: end,
      normalRoute: {
        path: normal.path || [],
        distanceKm: +(normalDist).toFixed(2),
        riskExposureScore: normalRisk,
      },
      riskAwareRoute: {
        path: aware.path || [],
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
