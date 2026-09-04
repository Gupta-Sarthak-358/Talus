import { apiRequest } from './api';
import { getZones } from './zones';

/**
 * Risk summary + alerts — LIVE SIH26001 (real /api/zones + /api/zones/{id}/decision).
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
  const { zones } = await getZones();
  return summarize(zones);
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

export async function acknowledgeAlert(alertId) {
  return { status: 'success', acknowledgedId: alertId, timestamp: new Date().toISOString() };
}
