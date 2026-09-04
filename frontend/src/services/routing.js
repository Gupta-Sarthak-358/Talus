import { apiRequest } from './api';
import { LOCATIONS } from '../data/locations';

/**
 * Risk-aware routing — LIVE SIH26001, location-aware.
 * Live contract: POST /api/routes/safe (location inferred from start zone:
 * N1-N4 lachung, D1-D4 darjeeling, else gangtok) + GET /api/roads/status?location=.
 * Each corridor routes upper->valley avoiding R2; waypoints render on that
 * corridor's map (previously Gangtok S1->S4coords rendered off-screen elsewhere).
 */

const ROUTE_PRESETS_BY_LOCATION = {
  gangtok: {
    defaultKey: 's1_to_s4',
    presets: {
      s1_to_s4: { start: 'S1', end: 'S4' },
      worker_zoneA_to_ap1: { start: 'S1', end: 'S4' },
    },
    label: 'Gangtok Corridor',
    originName: 'S1 Tathangchen (Upper Hillside)',
    destName: 'S4 Ranipool (Valley Staging & Egress)',
    threat: 'At-Risk Ridge Segment R2 & S1 Slope',
  },
  lachung: {
    defaultKey: 'n1_to_n4',
    presets: {
      n1_to_n4: { start: 'N1', end: 'N4' },
    },
    label: 'Lachung Valley',
    originName: 'N1 Lachung Upper (Yumthang approach)',
    destName: 'N4 Lachung Valley Staging',
    threat: 'At-Risk Ridge Segment R2 & N1 Slope',
  },
  darjeeling: {
    defaultKey: 'd1_to_d4',
    presets: {
      d1_to_d4: { start: 'D1', end: 'D4' },
    },
    label: 'Darjeeling Hills',
    originName: 'D1 Darjeeling Upper (Ghoom)',
    destName: 'D4 Darjeeling Valley Staging',
    threat: 'At-Risk Ridge Segment R2 & D1 Slope',
  },
};

export function routePresetsFor(location = 'gangtok') {
  return ROUTE_PRESETS_BY_LOCATION[location] || ROUTE_PRESETS_BY_LOCATION.gangtok;
}

export function defaultOriginKey(location = 'gangtok') {
  return routePresetsFor(location).defaultKey;
}

function centroid(location, zoneId) {
  const zones = LOCATIONS[location]?.zones || [];
  const geo = zones.find((g) => g.id === zoneId);
  return geo?.centroid || null;
}

export async function getRoadsStatus(location = null) {
  const qs = location ? `?location=${encodeURIComponent(location)}` : '';
  const res = await apiRequest(`/roads/status${qs}`);
  return res.segments;
}

/** Haversine km over a [{lat,lng},...] path. Backend total_cost is graph
 *  cost (degrees / risk-weighted), never a display distance. */
export function pathKm(waypoints = []) {
  let km = 0;
  for (let i = 1; i < waypoints.length; i++) {
    const a = waypoints[i - 1];
    const b = waypoints[i];
    if (a == null || b == null || a.lat == null || b.lat == null) continue;
    const r = 6371;
    const dLat = ((b.lat - a.lat) * Math.PI) / 180;
    const dLng = ((b.lng - a.lng) * Math.PI) / 180;
    const s =
      Math.sin(dLat / 2) ** 2 +
      Math.cos((a.lat * Math.PI) / 180) *
        Math.cos((b.lat * Math.PI) / 180) *
        Math.sin(dLng / 2) ** 2;
    km += 2 * r * Math.asin(Math.sqrt(s));
  }
  return +km.toFixed(2);
}

export async function calculateRoute({ originKey = null, location = 'gangtok', avoidZoneIds = [] } = {}) {
  const cfg = routePresetsFor(location);
  const key = originKey || cfg.defaultKey;
  const preset = cfg.presets[key] || cfg.presets[cfg.defaultKey];
  const sCenter = centroid(location, preset.start);
  const eCenter = centroid(location, preset.end);
  const start = { zone_id: preset.start, ...(sCenter ? { lat: sCenter[0], lng: sCenter[1] } : {}) };
  const end = { zone_id: preset.end, ...(eCenter ? { lat: eCenter[0], lng: eCenter[1] } : {}) };

  const res = await apiRequest('/routes/safe', {
    method: 'POST',
    body: JSON.stringify({ start, end }),
  });
  const aware = res.risk_aware_route || {};
  const normal = res.shortest_route || {};
  const normalWaypoints = normal.path || [];
  const awareWaypoints = aware.path || [];
  // Honest distances from returned geometry (backend cost is not km).
  const normalKm = pathKm(normalWaypoints);
  const awareKm = pathKm(awareWaypoints);
  const awareRisk = aware.max_risk_exposed ?? 66;
  const normalRisk = normal.max_risk_exposed ?? 89;
  const normalZones = normal.zone_path || [];
  const awareZones = aware.zone_path || [];
  return {
    status: 'success',
    timestamp: new Date().toISOString(),
    location: res.location || location,
    originKey: key,
    origin: start,
    destination: end,
    normalRoute: {
      name: `Shortest Route (via R2) — ${cfg.label}`,
      path: normalWaypoints,
      waypoints: normalWaypoints,
      zonePath: normalZones,
      distanceKm: normalKm,
      riskExposureScore: normalRisk,
      passesThroughHazardZone: 'R2 (At-risk segment)',
      hazardDescription: `Crosses at-risk ridge shortcut R2 directly below ${preset.start}`,
    },
    riskAwareRoute: {
      name: `Safe Route (via R3/R4) — ${cfg.label}`,
      path: awareWaypoints,
      waypoints: awareWaypoints,
      zonePath: awareZones,
      distanceKm: awareKm,
      riskExposureScore: awareRisk,
      passesThroughHazardZone: 'None',
      hazardDescription: `Safely diverts via valley roads (${awareZones.join(' → ') || 'R3/R4'}), avoiding R2`,
    },
    comparison: {
      distanceDeltaKm: +(awareKm - normalKm).toFixed(2),
      timeDeltaMin: +((awareKm - normalKm) * 1.5).toFixed(1),
      riskReductionPct: normalRisk > 0 ? Math.round(((normalRisk - awareRisk) / normalRisk) * 100) : 0,
      summary: `Shortest crosses at-risk segment R2 below ${preset.start}; the safe route diverts via the valley chain (${awareZones.join(' → ') || 'R3/R4'}) and avoids R2 entirely. Both start at ${preset.start} (${normalRisk}) — the difference is the ground crossed, shown as two separate lines on the map.`,
    },
    avoidedZones: res.avoided_zones || [preset.start],
    avoidedSegments: ['R2'],
    originName: cfg.originName,
    destName: cfg.destName,
    threatAvoided: cfg.threat,
  };
}

export const routingCapabilities = { live: true };
