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

const ZONE_DISPLAY = { A: 'North Highwall', B: 'East Haulage & Toe', C: 'SW bench', D: 'NE bench' };
function mockName(id) {
  return ZONE_DISPLAY[id] || 'bench';
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
  // Offline fallback uses the real frozen-model outputs (seed-91 states).
  return [
    { id: 'A', risk_band: 'CRITICAL', confidence: 91, activePersonnel: 4 },
    { id: 'B', risk_band: 'CRITICAL', confidence: 100, activePersonnel: 2 },
    { id: 'C', risk_band: 'MODERATE', confidence: 44, activePersonnel: 6 },
    { id: 'D', risk_band: 'CRITICAL', confidence: 95, activePersonnel: 0 },
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
    activePersonnelInHazard: bands
      .filter((z) => z.band === 'HIGH' || z.band === 'CRITICAL')
      .reduce((acc, z) => acc + (z.activePersonnel || 0), 0),
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
          zoneName: `Zone ${z.id} — ${mockName(z.id)}`,
          title: `${cap(band)} risk detected in Zone ${z.id}`,
          summary: decision?.message || `Zone ${z.id} is ${band.toLowerCase()} risk`,
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
  return {
    alerts: [
      { id: 'zone-b-critical', zoneId: 'B', zoneName: 'Zone B — East Haulage & Toe',
        title: 'Critical risk detected in Zone B',
        summary: 'Zone B is critical risk', severity: 'CRITICAL',
        action: 'prioritize inspection', drivers: [], acknowledged: false,
        timestamp: new Date().toISOString() },
    ],
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