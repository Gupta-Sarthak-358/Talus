import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, Marker, Popup, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useTalusContext } from '../../context/TalusContext';
import { RISK_BANDS } from '../../data/constants';
import { apiRequest } from '../../services/api';
import MapLegend from './MapLegend';
import { AlertOctagon, Navigation, Radio, ShieldAlert, Maximize2, Compass, Layers } from 'lucide-react';

// Custom Leaflet DivIcon helpers
function createCustomIcon(htmlContent, className = '', size = [28, 28]) {
  return L.divIcon({
    html: htmlContent,
    className: `custom-mine-icon ${className}`,
    iconSize: size,
    iconAnchor: [size[0] / 2, size[1] / 2],
    popupAnchor: [0, -size[1] / 2],
  });
}

const sensorIcon = createCustomIcon(
  `<div class="w-6 h-6 rounded-full bg-[#664930]/20 border border-[#664930] flex items-center justify-center text-[#664930] shadow-md">
    <div class="w-2 h-2 rounded-full bg-[#664930] animate-ping"></div>
  </div>`,
  'sensor-node-pin'
);

const criticalHazardIcon = createCustomIcon(
  `<div class="w-9 h-9 rounded-full bg-[#c74732]/25 border-2 border-[#c74732] flex items-center justify-center text-[#c74732] shadow-lg animate-pulse">
    <svg class="w-5 h-5 text-[#c74732]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
  </div>`,
  'hazard-pulse-pin'
);

// Map Controller — recenters when active corridor changes (Gangtok/Lachung/Darjeeling)
function MapController({ center, zoom }) {
  const map = useMap();

  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
      map.setView(center, zoom);
    }, 150);
    return () => clearTimeout(timer);
  }, [map, center, zoom]);

  // Also fly when corridor switches without remount
  useEffect(() => {
    map.flyTo(center, zoom, { duration: 0.6 });
  }, [map, center, zoom]);

  return null;
}

export default function RiskMap() {
  const {
    zones,
    selectedZoneId,
    selectZone,
    activeRoutePlan,
    mapLayers,
    activeSimulation,
    locationData,
    activeLocation,
    roads: liveRoads,
    t,
    role,
  } = useTalusContext();

  const mapCenter = locationData?.center || [27.3389, 88.6065];
  const mapZoom = locationData?.zoom || 13;
  // Live per-corridor segments from GET /api/roads/status?location= (carry
  // coordinates); fall back to the static fixture geometry pre-load.
  const roadSegments = (Array.isArray(liveRoads) && liveRoads.length > 0 && liveRoads[0]?.coordinates)
    ? liveRoads
    : (locationData?.roads || []);

  const [tileMode, setTileMode] = useState('osm'); // 'osm' default (no key) | 'dark' | 'light'

  // Live sensor feed (local simulator or committed sample via /api/live/feed).
  // Pins render ONLY from this feed, labeled SIMULATED — no static instruments.
  const [liveFeed, setLiveFeed] = useState(null);
  useEffect(() => {
    let stop = false;
    const poll = async () => {
      try {
        const res = await apiRequest('/live/feed');
        if (!stop) setLiveFeed(res.feed || null);
      } catch {
        if (!stop) setLiveFeed(null);
      }
    };
    poll();
    const timer = setInterval(poll, 15000);
    return () => { stop = true; clearInterval(timer); };
  }, []);
  const sensorPins = useMemo(() => {
    if (!liveFeed?.zones) return [];
    return (zones || [])
      .filter((z) => z.geometry?.centroid && liveFeed.zones[z.id])
      .map((z) => ({ zone: z, feed: liveFeed.zones[z.id] }));
  }, [zones, liveFeed]);

  // Runout screening paths (committed evidence bundle, labeled approximation).
  const [runout, setRunout] = useState(null);
  useEffect(() => {
    let stop = false;
    apiRequest('/runout/exposure')
      .then((b) => { if (!stop) setRunout(b.zones || null); })
      .catch(() => { if (!stop) setRunout(null); });
    return () => { stop = true; };
  }, []);

  // Wound candidates (review queue, NOT confirmed cuts).
  const [wounds, setWounds] = useState(null);
  useEffect(() => {
    let stop = false;
    apiRequest('/wounds')
      .then((b) => { if (!stop) setWounds(b.corridors || null); })
      .catch(() => { if (!stop) setWounds(null); });
    return () => { stop = true; };
  }, []);
  const woundPins = useMemo(() => {
    if (!wounds) return [];
    return Object.values(wounds).flatMap((c) => c.candidates || []);
  }, [wounds]);

  // Zone colors lookup
  const getZoneFillColor = (band) => {
    const meta = RISK_BANDS[band];
    return meta ? meta.badgeColor : '#5e7f3a';
  };

  return (
    <div className="relative w-full h-full min-h-[480px] bg-mine-darkest rounded-2xl overflow-hidden border border-mine-border shadow-md flex flex-col">
        {/* Top Banner on Map — villager: no SHAP jargon */}
      <div className="absolute top-3 left-3 z-[400] bg-mine-card border border-mine-border rounded-lg px-3 py-1.5 text-xs font-medium text-mine-text flex items-center gap-2 shadow-sm">
        <span className={`w-2 h-2 rounded-full ${locationData?.live ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
        <span className="font-semibold">{t(`location.${locationData?.id}`) !== `location.${locationData?.id}` ? t(`location.${locationData.id}`) : (locationData?.label || 'Gangtok')} {t('map.title')} ({(zones||[]).map(z=>z.id).join('–') || locationData?.id || 'S1-S4'})</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold border ${locationData?.live ? 'bg-emerald-500/15 text-emerald-700 border-emerald-500/30' : 'bg-amber-500/15 text-amber-700 border-amber-500/30'}`}>{locationData?.live ? t('common.live_ngen') : t('common.no_data')}</span>
        <span className="text-mine-muted font-mono">|</span>
        <span className="text-mine-muted text-[11px]">{role === 'villager' ? t('villager.tap_map') : t('map.clickSlope')}</span>
      </div>

      {/* Top-Right Map Controls: Reset View / Basemap Mode */}
      <div className="absolute top-3 right-3 z-[400] flex items-center gap-1.5 bg-mine-card border border-mine-border rounded-lg p-1 shadow-sm">
        <button
          onClick={() => setTileMode(tileMode === 'osm' ? 'dark' : tileMode === 'dark' ? 'light' : 'osm')}
          className="px-2 py-1 bg-mine-darker hover:bg-mine-dark text-mine-text rounded text-[10px] font-mono font-semibold flex items-center gap-1 transition-colors"
          title={t('map.switch_layer')}
        >
          <Layers className="w-3 h-3 text-talus-600" />
          <span>{t('map.layer')}: {tileMode.toUpperCase()}</span>
        </button>
      </div>

      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        scrollWheelZoom={true}
        className="w-full h-full flex-1"
        zoomControl={false}
        attributionControl={true}
      >
        <MapController center={mapCenter} zoom={mapZoom} />

        {/* Basemap: OSM default (no key, most reliable). CARTO dark/light optional. */}
        {tileMode === 'dark' && (
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png"
            maxZoom={19}
            subdomains="abcd"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
        )}

        {tileMode === 'osm' && (
          <TileLayer
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
        )}

        {tileMode === 'light' && (
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png"
            maxZoom={19}
            subdomains="abcd"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
        )}

        {/* Road Network with live status coloring — per corridor */}
        {(roadSegments||[]).map((road) => {
          const isBlocked = road.status === 'blocked';
          const isAtRisk = road.status === 'at-risk';
          const color = isBlocked ? '#c74732' : isAtRisk ? '#d97706' : '#5e7f3a';
          return (
            <Polyline
              key={road.id}
              positions={road.coordinates}
              pathOptions={{
                color: color,
                weight: isBlocked ? 4.5 : isAtRisk ? 4 : 3,
                dashArray: isAtRisk ? '5, 5' : isBlocked ? '2, 3' : null,
                opacity: 0.9,
              }}
            >
              <Tooltip sticky direction="top">
                <div className="text-xs space-y-0.5 p-0.5">
                  <div className="font-bold flex items-center gap-1.5" style={{ color }}>
                    <span>{road.id} — {road.name}</span>
                    <span className="text-[10px] uppercase font-mono px-1 rounded bg-mine-dark border border-mine-border">
                      [{road.status}]
                    </span>
                  </div>
                  <div className="text-[11px] text-mine-text">{road.description}</div>
                  {isAtRisk && (
                    <div className="text-[10px] text-amber-400 font-medium">
                      ⚠ {t('map.bypassed')}
                    </div>
                  )}
                  {isBlocked && (
                    <div className="text-[10px] text-risk-critical font-medium">
                      ✕ {t('map.road_closed')}
                    </div>
                  )}
                </div>
              </Tooltip>
            </Polyline>
          );
        })}

        {/* NER Slope Zone Polygons (S1-S4 Gangtok) */}
        {(zones||[]).map((zone) => {
          if (!zone.geometry || !zone.geometry.coordinates) return null;
          const isSelected = zone.id === selectedZoneId;
          const fillColor = getZoneFillColor(zone.risk_band);
          const isCriticalOrHigh = zone.risk_band === 'CRITICAL' || zone.risk_band === 'HIGH';

          return (
            <React.Fragment key={zone.id}>
              <Polygon
                positions={zone.geometry.coordinates}
                pathOptions={{
                  fillColor: fillColor,
                  fillOpacity: isSelected ? 0.65 : 0.38,
                  color: isSelected ? '#664930' : fillColor,
                  weight: isSelected ? 3.5 : 1.8,
                  dashArray: isSelected ? '4, 4' : null,
                }}
                eventHandlers={{
                  click: () => selectZone(zone.id),
                }}
              >
                <Tooltip direction="center" sticky offset={[0, 0]}>
                  <div className="p-1 space-y-0.5">
                    <div className="font-bold text-mine-text flex items-center gap-1">
                      <span>{zone.name}</span>
                      {isSelected && <span className="text-[10px] text-talus-600 font-normal">({t('map.selected')})</span>}
                    </div>
                    <div className="text-[11px] flex items-center gap-2">
                      <span className="font-mono font-bold" style={{ color: fillColor }}>
                        {t('map.risk')} {zone.risk_score}/100 [{zone.risk_band}]
                      </span>
                      <span className="text-mine-muted">{t('map.conf')} {zone.confidence}%</span>
                    </div>
                    {zone.shap && zone.shap[0] && (
                      <div className="text-[10px] text-mine-muted">
                        {t('map.primary')} {zone.shap[0].feature} (+{zone.shap[0].value})
                      </div>
                    )}
                  </div>
                </Tooltip>
              </Polygon>

              {/* Pulsing Critical Warning Marker at centroid of High/Critical zone */}
              {isCriticalOrHigh && mapLayers.hazardGlow && zone.geometry.centroid && (
                <Marker position={zone.geometry.centroid} icon={criticalHazardIcon}>
                  <Popup>
                    <div className="p-1 space-y-1">
                      <div className="flex items-center gap-1.5 text-risk-critical font-bold text-xs">
                        <ShieldAlert className="w-4 h-4" />
                        <span>{zone.name} — {t('map.high_hazard')}</span>
                      </div>
                      <p className="text-[11px] text-mine-text">
                        {t('map.risk_score')} <strong className="text-risk-critical">{zone.risk_score}</strong> / 100 ({zone.risk_band})
                      </p>
                      <p className="text-[10px] text-mine-muted">
                        {t('map.high_pore')}
                      </p>
                    </div>
                  </Popup>
                </Marker>
              )}
            </React.Fragment>
          );
        })}

         {/* Live sensor pins — from /api/live/feed */}
        {mapLayers.sensors &&
          sensorPins.map(({ zone, feed }) => (
            <Marker key={zone.id} position={zone.geometry.centroid} icon={sensorIcon}>
              <Popup>
                <div className="p-1 space-y-1">
                  <div className="flex items-center gap-1 text-talus-600 font-semibold text-xs">
                    <Radio className="w-3.5 h-3.5" />
                    <span>{zone.id} sensor</span>
                    {role !== 'villager' && (
                      <span className="text-[9px] font-bold px-1.5 py-px rounded-full bg-amber-500/10 text-amber-600 border border-amber-500/20">SIM</span>
                    )}
                  </div>
                  <div className="text-[11px] text-mine-text font-mono">
                    rain 1h {feed.rain_1h_mm.toFixed(1)}mm · Δsoil {feed.soil_delta >= 0 ? '+' : ''}{feed.soil_delta.toFixed(3)}
                  </div>
                  <div className="text-[10px] text-mine-muted flex items-center justify-between font-mono">
                    <span>batt {feed.battery_pct.toFixed(0)}% · {feed.rssi_dbm.toFixed(0)} dBm</span>
                    <span className={`font-semibold ${feed.status === 'ok' ? 'text-risk-verylow' : 'text-risk-moderate'}`}>
                      [{feed.status.toUpperCase()}]
                    </span>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

        {/* Runout paths — downstream risk if slope fails */}
        {mapLayers.runout && runout &&
          Object.entries(runout)
            .filter(([, z]) => Array.isArray(z.path) && z.path.length >= 2)
            .map(([zid, z]) => (
              <Polyline
                key={`runout-${zid}`}
                positions={z.path}
                pathOptions={{ color: '#c74732', weight: 2, dashArray: '2, 5', opacity: 0.75 }}
              >
                <Tooltip sticky direction="top">
                  <div className="text-[11px] p-0.5">
                    <div className="font-bold text-mine-text">{zid} runout — {z.length_m}m</div>
                    <div className="text-mine-muted">~{z.buildings_n} buildings downstream</div>
                  </div>
                </Tooltip>
              </Polyline>
            ))}

        {/* Vegetation change — field check before action */}
        {mapLayers.wounds && woundPins.map((w, i) => (
          <Marker key={`wound-${i}`} position={[w.lat, w.lon]} icon={sensorIcon}>
            <Popup>
              <div className="text-[11px] p-0.5">
                <div className="font-bold text-mine-text">Vegetation change near {w.seg}</div>
                <div className="text-mine-muted font-mono">NDVI {w.ndvi_pre} → {w.ndvi_post} (Δ{w.drop})</div>
                <div className="text-mine-muted">Possible fresh disturbance — field team to verify.</div>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Routing Overlays (Normal vs Risk-Aware Route) */}
        {mapLayers.routes && activeRoutePlan && (
          <>
            {/* 1. Normal (Shortest / Dangerous) Route (Red / Amber Dashed) */}
            {activeRoutePlan.normalRoute && (
              <Polyline
                positions={activeRoutePlan.normalRoute.waypoints}
                pathOptions={{
                  color: '#c74732',
                  weight: 3.5,
                  dashArray: '6, 6',
                  opacity: 0.85,
                }}
              >
                <Tooltip sticky direction="top">
                  <div className="text-xs space-y-0.5">
                    <div className="font-bold text-risk-critical flex items-center gap-1">
                      <AlertOctagon className="w-3.5 h-3.5" />
                      <span>{activeRoutePlan.normalRoute.name}</span>
                    </div>
                    <div className="text-[11px] text-mine-text">
                      {t('route.distance')}: {activeRoutePlan.normalRoute.distanceKm} km | {t('route.exposure')}: {activeRoutePlan.normalRoute.riskExposureScore}
                    </div>
                    <div className="text-[10px] text-risk-critical">
                      ⚠ {t('map.direct_hazard')} {activeRoutePlan.normalRoute.passesThroughHazardZone}
                    </div>
                  </div>
                </Tooltip>
              </Polyline>
            )}

            {/* 2. Risk-Aware (Safe Diversion) Route (Solid Emerald / Cyan) */}
            {activeRoutePlan.riskAwareRoute && (
              <Polyline
                positions={activeRoutePlan.riskAwareRoute.waypoints}
                pathOptions={{
                  color: '#5e7f3a',
                  weight: 4.5,
                  opacity: 0.95,
                }}
              >
                <Tooltip sticky direction="top">
                  <div className="text-xs space-y-0.5">
                    <div className="font-bold text-risk-verylow flex items-center gap-1">
                      <Navigation className="w-3.5 h-3.5" />
                      <span>{activeRoutePlan.riskAwareRoute.name}</span>
                    </div>
                    <div className="text-[11px] text-mine-text">
                      {t('route.distance')}: {activeRoutePlan.riskAwareRoute.distanceKm} km | {t('route.exposure')}: {activeRoutePlan.riskAwareRoute.riskExposureScore}
                    </div>
                    <div className="text-[10px] text-risk-verylow">
                      ✓ {t('map.safe_bypass')}
                    </div>
                  </div>
                </Tooltip>
              </Polyline>
            )}
          </>
        )}
      </MapContainer>

      {/* Collapsible Map Legend & Layer Toggles */}
      <MapLegend />
    </div>
  );
}

// Backward compat — MineMap deprecated, use RiskMap
export const MineMap = RiskMap;
