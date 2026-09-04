import { apiRequest, isLiveApiEnabled, simulateLatency } from './api';
import { MOCK_ZONES } from '../data/mockData';
import { MINE_ZONES_GEOJSON } from '../data/mineGeoData';

/**
 * Zone services. Live mode consumes the REAL backend:
 *   GET /api/zones, /api/zones/{id}, /{id}/features, /{id}/explanation, /{id}/trend
 * Backend scores/bands come from frozen ML Model v1 (RF) with isotonic
 * calibrated confidence (0-1 -> reported as %).
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

export async function getZones() {
  if (isLiveApiEnabled()) {
    const res = await apiRequest('/zones');
    const live = (res.zones || []).map(mapLiveZone);
    const merged = live.map((zone) => {
      const geo = MINE_ZONES_GEOJSON.find((g) => g.id === zone.id);
      return {
        ...zone,
        geometry: geo ? { coordinates: geo.coordinates, centroid: geo.centroid, benches: geo.benches } : zone.geometry,
      };
    });
    return { status: 'success', timestamp: new Date().toISOString(), zones: merged };
  }

  await simulateLatency(250);
  const mergedZones = MOCK_ZONES.map((zone) => {
    const geo = MINE_ZONES_GEOJSON.find((g) => g.id === zone.id);
    return {
      ...zone,
      geometry: geo ? { coordinates: geo.coordinates, centroid: geo.centroid, benches: geo.benches } : null,
    };
  });
  // Frozen SIH26001 contract outputs
  const REAL = {
    S1: { score: 89, band: 'CRITICAL', confidence: 82 },
    S2: { score: 78, band: 'HIGH', confidence: 74 },
    S3: { score: 66, band: 'MODERATE', confidence: 61 },
    S4: { score: 52, band: 'LOW', confidence: 58 },
  };
  mergedZones.forEach((z) => {
    const r = REAL[z.id];
    if (r) { z.risk_score = r.score; z.risk_band = r.band; z.confidence = r.confidence; }
  });
  return { status: 'success', timestamp: new Date().toISOString(), zones: mergedZones };
}

export async function getZoneById(zoneId) {
  if (isLiveApiEnabled()) {
    const [detail, explanation, features, trend, decision, history] = await Promise.all([
      apiRequest(`/zones/${zoneId}`),
      apiRequest(`/zones/${zoneId}/explanation`).catch(() => null),
      apiRequest(`/zones/${zoneId}/features`).catch(() => null),
      apiRequest(`/zones/${zoneId}/trend`).catch(() => null),
      apiRequest(`/zones/${zoneId}/decision`).catch(() => null),
      apiRequest(`/zones/${zoneId}/history`).catch(() => null),
    ]);
    const f = features?.features || {};
    const mock = MOCK_ZONES.find((z) => z.id === zoneId) || {};
    // RoleActionCard expects role_actions keyed by role id (FR-06 live wiring)
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
      ...mock,
      id: detail.zone_id,
      name: detail.name,
      sector: mock.sector || '',
      risk_score: detail.risk_score,
      risk_band: bandUpper(detail.risk_band),
      confidence: confPct(detail.confidence),
      status: bandUpper(detail.risk_band) === 'CRITICAL' ? 'Critical - active monitoring' : 'Normal Operations',
      geometry: detail.geometry,
      updated_at: detail.updated_at,
      missingEvidence: missing_evidence,
      missing_evidence,
      role_actions: Object.keys(role_actions).length > 0 ? role_actions : mock.role_actions,
      telemetry: {
        ...(mock.telemetry || {}),
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
        historySource: 'scaffold_fixture',
      },
    };
    // Context consumers read result.zone -- wrap while keeping fields at top level.
    return { zone: rich, ...rich };
  }

  await simulateLatency(200);
  const zone = MOCK_ZONES.find((z) => z.id === zoneId);
  if (!zone) {
    throw Object.assign(new Error(`Zone ${zoneId} not found`), { status: 404 });
  }
  const geo = MINE_ZONES_GEOJSON.find((g) => g.id === zoneId);
  const richOffline = {
    ...zone,
    geometry: geo ? { coordinates: geo.coordinates, centroid: geo.centroid, benches: geo.benches } : null,
  };
  return { zone: richOffline, ...richOffline };
}