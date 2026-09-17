import { apiRequest } from './api';
import { getZones } from './zones';
import { translations } from '../i18n/translations';

/**
 * Risk summary + alerts — LIVE SIH26001 (real /api/zones + /api/zones/{id}/decision).
 */

function bandUpper(band) {
  return String(band || '').toUpperCase().replace(' ', '_');
}

function cap(s) {
  return String(s || '').charAt(0).toUpperCase() + String(s || '').slice(1).toLowerCase();
}

/** Live display name from /api/zones (getZones maps z.name); id fallback keeps N/D corridors honest. */
function zoneDisplayName(z) {
  return z.name || z.id;
}

export async function getRiskSummary(zones = null) {
  const list = zones || (await getZones()).zones;
  return summarize(list);
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
    systemStatus: criticalCount > 0 ? 'CRITICAL_ALERT' : highCount > 0 ? 'HIGH_ALERT' : 'NORMAL_OPERATIONS',
  };
}

export async function getAlerts(lang = 'en') {
  const { zones } = await getZones();
  const t = (k) => (translations[lang] || translations.en)[k] || translations.en[k] || k;
  const alerts = [];
  for (const z of zones) {
    const band = bandUpper(z.risk_band);
    if (band === 'CRITICAL' || band === 'HIGH') {
      let decision = null;
      try {
        const d = await apiRequest(`/zones/${z.id}/decision?lang=${encodeURIComponent(lang)}`);
        // decisions are role-ordered: villager is first
        decision = d.decisions?.[0];
      } catch { /* keep alert without decision text */ }
      const bandLabel = band === 'CRITICAL' ? t('alerts.critical') : band === 'HIGH' ? t('alerts.high') : cap(band);
      alerts.push({
        id: `zone-${z.id}-${band.toLowerCase()}-${lang}`,
        zoneId: z.id,
        zoneName: `${z.id} — ${zoneDisplayName(z)}`,
        title: `${bandLabel} — ${z.id} (${zoneDisplayName(z)})`,
        summary: decision?.message || t('alerts.fallback'),
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

/**
 * Real server-side acknowledgement (POST /api/alerts/ack). Offline the call
 * throws and the caller must NOT mark the alert — no fake acks.
 */
export async function acknowledgeAlert(alertId) {
  return apiRequest('/alerts/ack', {
    method: 'POST',
    body: JSON.stringify({ alert_id: alertId }),
  });
}
