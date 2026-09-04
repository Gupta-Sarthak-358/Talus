import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { getZones } from './zones';

/**
 * Risk summary + alerts. Live mode derives both from the real /api/zones
 * feed (frozen RF scores + calibrated confidence). Alerts are synthesized
 * from zone states via the decision endpoint contract.
 */

function bandUpper(band) {
  return String(band || '').toUpperCase().replace(' ', '_');
}

function cap(s) {
  return String(s || '').charAt(0).toUpperCase() + String(s || '').slice(1).toLowerCase();
}

const ZONE_DISPLAY = {
  S1: 'Tathangchen (upper)',
  S2: 'Chandmari (road-cut)',
  S3: 'Tadong (mid)',
  S4: 'Ranipool (valley)'
};
function mockName(id) {
  return ZONE_DISPLAY[id] || 'slope';
}

export async function getRiskSummary() {
  if (isLiveApiEnabled()) {
    const { zones } = await getZones();
    return summarize(zones);
  }

  await simulateLatency(150);
  return summarize(MOCK_FALLBACK_ZONES());
}

function MOCK_FALLBACK_ZONES() {
  // Frozen SIH26001 contract scores & bands
  return [
    { id: 'S1', risk_score: 89, risk_band: 'CRITICAL', confidence: 82, activePersonnel: 0 },
    { id: 'S2', risk_score: 78, risk_band: 'HIGH', confidence: 74, activePersonnel: 0 },
    { id: 'S3', risk_score: 66, risk_band: 'MODERATE', confidence: 61, activePersonnel: 0 },
    { id: 'S4', risk_score: 52, risk_band: 'LOW', confidence: 58, activePersonnel: 0 },
  ];
}

function summarize(zones) {
  const bands = zones.map((z) => ({ ...z, band: bandUpper(z.risk_band) }));
  const criticalCount = bands.filter((z) => z.band === 'CRITICAL').length;
  const highCount = bands.filter((z) => z.band === 'HIGH').length;
  const moderateCount = bands.filter((z) => z.band === 'MODERATE').length;
  const lowCount = bands.filter((z) => z.band === 'LOW' || z.band === 'VERY_LOW').length;
  const avgConfidence = Math.round(
    bands.reduce((acc, z) => acc + (z.confidence || 0), 0) / Math.max(zones.length, 1)
  );
  return {
    criticalCount,
    highCount,
    moderateCount,
    lowCount,
    totalZones: zones.length,
    dataQualityConfidence: avgConfidence,
    activePersonnelInHazard: 0,
    systemStatus: criticalCount > 0 ? 'CRITICAL_ALERT' : highCount > 0 ? 'HIGH_ALERT' : 'NORMAL_OPERATIONS',
  };
}

export async function getAlerts() {
  if (isLiveApiEnabled()) {
    const { zones } = await getZones();
    const alerts = [];
    for (const z of zones) {
      const band = bandUpper(z.risk_band);
      if (band === 'CRITICAL' || band === 'HIGH') {
        let decision = null;
        try {
          const d = await apiRequest(`/zones/${z.id}/decision`);
          decision = d.decisions?.[0];
        } catch { /* keep alert without decision text */ }
        alerts.push({
          id: `zone-${z.id}-${band.toLowerCase()}`,
          zoneId: z.id,
          zoneName: `${z.id} — ${mockName(z.id)}`,
          title: `${cap(band)} risk detected on ${z.id} (${mockName(z.id)})`,
          summary: decision?.message || `${z.id} is ${band.toLowerCase()} risk`,
          severity: band,
          action: decision?.action || 'monitor',
          drivers: [],
          acknowledged: false,
          timestamp: new Date().toISOString(),
        });
      }
    }
    return { alerts };
  }

  await simulateLatency(200);
  const { MOCK_ALERTS } = await import('../data/mockData');
  return {
    alerts: MOCK_ALERTS,
  };
}

export async function acknowledgeAlert(alertId) {
  if (isLiveApiEnabled()) {
    // Acknowledgement is a UI concern in the prototype; no backend store yet.
    return { status: 'success', acknowledgedId: alertId, timestamp: new Date().toISOString() };
  }
  await simulateLatency(100);
  return { status: 'success', acknowledgedId: alertId, timestamp: new Date().toISOString() };
}