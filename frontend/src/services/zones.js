import { apiRequest } from './api';
import { MINE_ZONES_GEOJSON, LOCATIONS } from '../data/mineGeoData';

/**
 * Zone services — LIVE SIH26001 (real NGEN + USGS/IMD/CCI/WorldCover).
 *   GET /api/zones, /api/zones/{id}, /{id}/features, /{id}/explanation, /{id}/trend
 * Scores/bands from frozen fixtures S1-S4 89/78/66/52 (16/17 REAL/PROXY) + training 1528×22 backing.
 */

function bandUpper(band) {
  return String(band || '').toUpperCase().replace(' ', '_');
}

function confPct(confidence) {
  const c = typeof confidence === 'number' ? confidence : parseFloat(confidence);
  return Math.round((Number.isFinite(c) ? (c <= 1 ? c * 100 : c) : 0));
}

function mapLiveZone(z) {
  const geo = MINE_ZONES_GEOJSON.find((g) => g.id === z.zone_id);
  return {
    id: z.zone_id,
    name: z.name || `Zone ${z.zone_id}`,
    sector: geo?.sector || '',
    risk_score: z.risk_score,
    risk_band: bandUpper(z.risk_band),
    confidence: confPct(z.confidence),
    status: bandUpper(z.risk_band) === 'CRITICAL' ? 'Critical - active monitoring'
          : bandUpper(z.risk_band) === 'HIGH' ? 'Elevated risk' : 'Normal Operations',
    geometry: geo ? { coordinates: geo.coordinates, centroid: geo.centroid, benches: geo.benches } : null,
    trend: z.trend || null,
  };
}

export async function getZones(location = null) {
  const qs = location ? `?location=${encodeURIComponent(location)}` : '';
  const res = await apiRequest(`/zones${qs}`);
  const live = (res.zones || []).map(mapLiveZone);
  const locKey = location || res.location || 'gangtok';
  const locZones = LOCATIONS[locKey]?.zones || MINE_ZONES_GEOJSON;
  const merged = live.map((zone) => {
    let geo = MINE_ZONES_GEOJSON.find((g) => g.id === zone.id);
    if (!geo) geo = locZones.find((g) => g.id === zone.id);
    return {
      ...zone,
      geometry: geo ? { coordinates: geo.coordinates, centroid: geo.centroid, benches: geo.benches } : zone.geometry,
    };
  });
  return { status: 'success', timestamp: new Date().toISOString(), zones: merged, location: locKey };
}

export async function getZoneById(zoneId, lang = null) {
  const langQs = lang ? `?lang=${encodeURIComponent(lang)}` : '';
  const [detail, explanation, features, trend, decision, history] = await Promise.all([
    apiRequest(`/zones/${zoneId}`),
    apiRequest(`/zones/${zoneId}/explanation`).catch(() => null),
    apiRequest(`/zones/${zoneId}/features`).catch(() => null),
    apiRequest(`/zones/${zoneId}/trend`).catch(() => null),
    apiRequest(`/zones/${zoneId}/decision${langQs}`).catch(() => null),
    apiRequest(`/zones/${zoneId}/history`).catch(() => null),
  ]);
  const f = features?.features || {};
  const role_actions = {};
  for (const d of decision?.decisions || []) {
    role_actions[d.role] = {
      header: `${d.role.replace(/_/g, ' ').toUpperCase()} — ${d.priority} priority`,
      action: d.message,
      caution: d.action,
      routeRecommended: d.role === 'villager' || d.role === 'rescue_team',
      urgency: d.priority === 'immediate' ? 'Immediate Action'
             : d.priority === 'high' ? 'High Priority'
             : d.priority === 'standby' ? 'Standby' : 'Operational',
    };
  }
  const missing_evidence = features?.missing_features || [];
  const rich = {
    id: detail.zone_id,
    name: detail.name,
    sector: '',
    risk_score: detail.risk_score,
    risk_band: bandUpper(detail.risk_band),
    confidence: confPct(detail.confidence),
    status: bandUpper(detail.risk_band) === 'CRITICAL' ? 'Critical - active monitoring' : 'Normal Operations',
    geometry: detail.geometry,
    updated_at: detail.updated_at,
    missingEvidence: missing_evidence,
    missing_evidence,
    role_actions,
    telemetry: {
      slope_angle: f.slope_angle,
      rainfall_24h: f.rainfall_24h_mm,
      rainfall_7d: f.rainfall_7d_mm,
      rainfall_30d: f.rainfall_30d_mm,
      soil_moisture: f.soil_moisture,
    },
    shap: (explanation?.contributions || []).map((c) => ({
      feature: c.feature,
      value: c.shap_value ?? c.shap,
      rawValue: `${(c.shap_value ?? c.shap) > 0 ? '+' : ''}${c.shap_value ?? c.shap}`,
      description: (c.shap_value ?? c.shap) > 0 ? 'increases predicted risk' : 'decreases predicted risk',
    })),
    shapBaseValue: explanation?.base_value ?? null,
    trend: {
      direction: trend?.rapid_increase ? 'rapidly_increasing' : 'stable',
      rapid: !!trend?.rapid_increase,
      history: (trend?.history || []).map((p) => ({
        time: p.t, risk: p.risk_score, label: p.t,
      })),
      historySource: 'live_api',
    },
  };
  return { zone: rich, ...rich };
}
