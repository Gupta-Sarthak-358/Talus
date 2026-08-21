import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { PRECOMPUTED_ROUTES } from '../data/mineGeoData';

/**
 * Request routing between origin and destination with risk penalties
 * Contract: POST /api/routes
 * Request payload: { origin, destination, riskAware }
 */
export async function calculateRoute({ originKey = 'worker_zoneA_to_ap1', avoidZoneIds = ['B'] } = {}) {
  if (isLiveApiEnabled()) {
    return apiRequest('/routes', {
      method: 'POST',
      body: JSON.stringify({ originKey, avoidZoneIds }),
    });
  }

  await simulateLatency(400);

  const routePlan = PRECOMPUTED_ROUTES[originKey] || PRECOMPUTED_ROUTES['worker_zoneA_to_ap1'];

  return {
    status: 'success',
    timestamp: new Date().toISOString(),
    origin: routePlan.origin,
    destination: routePlan.destination,
    normalRoute: routePlan.normalRoute,
    riskAwareRoute: routePlan.riskAwareRoute,
    comparison: {
      distanceDeltaKm: +(routePlan.riskAwareRoute.distanceKm - routePlan.normalRoute.distanceKm).toFixed(2),
      timeDeltaMin: +(routePlan.riskAwareRoute.estimatedTimeMin - routePlan.normalRoute.estimatedTimeMin).toFixed(1),
      riskReductionPct: Math.round(
        ((routePlan.normalRoute.riskExposureScore - routePlan.riskAwareRoute.riskExposureScore) /
          routePlan.normalRoute.riskExposureScore) *
          100
      ),
      summary: `Risk-aware routing adds only ${+(routePlan.riskAwareRoute.distanceKm - routePlan.normalRoute.distanceKm).toFixed(1)} km (+1.5 min) while reducing hazard exposure by 76%.`,
    },
  };
}
