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
  // Offline fallback still shows the FROZEN model's outputs for the seed-91
  // states -- mock telemetry is illustrative, but scores/bands/confidence
  // must never contradict the real model.
  const REAL = {
    A: { score: 89, band: 'CRITICAL', confidence: 91 },
    B: { score: 100, band: 'CRITICAL', confidence: 100 },
    C: { score: 66, band: 'MODERATE', confidence: 44 },
    D: { score: 99, band: 'CRITICAL', confidence: 95 },
  };
  mergedZones.forEach((z) => {
    const r = REAL[z.id];
    if (r) { z.risk_score = r.score; z.risk_band = r.band; z.confidence = r.confidence; }
  });
  return { status: 'success', timestamp: new Date().toISOString(), zones: mergedZones };
}

export async function getZoneById(zoneId) {
  if (isLiveApiEnabled()) {
    const [detail, explanation, features, trend] = await Promise.all([
      apiRequest(`/zones/${zoneId}`),
      apiRequest(`/zones/${zoneId}/explanation`).catch(() => null),
      apiRequest(`/zones/${zoneId}/features`).catch(() => null),
      apiRequest(`/zones/${zoneId}/trend`).catch(() => null),
    ]);
    const f = features?.features || {};
    const mock = MOCK_ZONES.find((z) => z.id === zoneId) || {};
    return {
      id: detail.zone_id,
      name: detail.name,
      sector: mock.sector || '',
      risk_score: detail.risk_score,
      risk_band: bandUpper(detail.risk_band),
      confidence: confPct(detail.confidence),
      status: bandUpper(detail.risk_band) === 'CRITICAL' ? 'Critical - active monitoring' : 'Normal Operations',
      geometry: detail.geometry,
      updated_at: detail.updated_at,
      missingEvidence: features?.missing_features || [],
      telemetry: {
        slope_angle: f.slope_angle_deg,
        rock_type: f.rock_type,
        crack_density: f.crack_density,
        rainfall_24h: f.rainfall_24h_mm,
        blast_vibration_ppv: f.blast_vibration_ppv_mms,
        groundwater_proxy: f.groundwater_proxy,
      },
      shap: (explanation?.contributions || []).map((c) => ({
        feature: c.feature,
        value: c.shap_value,
        rawValue: `${c.shap_value > 0 ? '+' : ''}${c.shap_value}`,
        description: c.shap_value > 0 ? 'increases predicted risk' : 'decreases predicted risk',
      })),
      shapBaseValue: explanation?.base_value ?? null,
      trend: {
        direction: trend?.rapid_increase ? 'rapidly_increasing' : 'stable',
        rapid: !!trend?.rapid_increase,
        history: (trend?.history || []).map((p) => ({ time: p.t, risk: p.risk_score, label: p.t })),
      },
    };
  }

  await simulateLatency(200);
  const zone = MOCK_ZONES.find((z) => z.id === zoneId);
  if (!zone) {
    throw Object.assign(new Error(`Zone ${zoneId} not found`), { status: 404 });
  }
  const geo = MINE_ZONES_GEOJSON.find((g) => g.id === zoneId);
  return {
    ...zone,
    geometry: geo ? { coordinates: geo.coordinates, centroid: geo.centroid, benches: geo.benches } : null,
  };
}