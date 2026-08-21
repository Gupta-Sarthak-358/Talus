import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { MOCK_ALERTS, MOCK_ZONES } from '../data/mockData';

/**
 * Fetch top-level risk metrics
 * Contract: GET /api/risk/summary
 */
export async function getRiskSummary(zones = MOCK_ZONES) {
  if (isLiveApiEnabled()) {
    return apiRequest('/risk/summary');
  }

  await simulateLatency(150);

  const criticalCount = zones.filter((z) => z.risk_band === 'CRITICAL').length;
  const highCount = zones.filter((z) => z.risk_band === 'HIGH').length;
  const moderateCount = zones.filter((z) => z.risk_band === 'MODERATE').length;
  const lowCount = zones.filter((z) => z.risk_band === 'LOW' || z.risk_band === 'VERY_LOW').length;

  // Average confidence across all zones
  const avgConfidence = Math.round(
    zones.reduce((acc, z) => acc + (z.confidence || 80), 0) / zones.length
  );

  return {
    criticalCount,
    highCount,
    moderateCount,
    lowCount,
    totalZones: zones.length,
    dataQualityConfidence: avgConfidence,
    activePersonnelInHazard: zones
      .filter((z) => z.risk_band === 'HIGH' || z.risk_band === 'CRITICAL')
      .reduce((acc, z) => acc + (z.activePersonnel || 0), 0),
    systemStatus: criticalCount > 0 ? 'CRITICAL_ALERT' : highCount > 0 ? 'HIGH_ALERT' : 'NORMAL_OPERATIONS',
  };
}

/**
 * Fetch active risk alerts
 * Contract: GET /api/alerts
 */
export async function getAlerts() {
  if (isLiveApiEnabled()) {
    return apiRequest('/alerts');
  }

  await simulateLatency(200);
  return {
    alerts: [...MOCK_ALERTS],
  };
}

/**
 * Acknowledge or dismiss an alert
 * Contract: POST /api/alerts/{id}/acknowledge
 */
export async function acknowledgeAlert(alertId) {
  if (isLiveApiEnabled()) {
    return apiRequest(`/alerts/${alertId}/acknowledge`, { method: 'POST' });
  }

  await simulateLatency(100);
  return {
    status: 'success',
    acknowledgedId: alertId,
    timestamp: new Date().toISOString(),
  };
}
