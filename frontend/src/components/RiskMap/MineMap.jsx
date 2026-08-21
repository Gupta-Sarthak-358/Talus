import React, { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, Polyline, Marker, Popup, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useMineContext } from '../../context/MineContext';
import { MINE_CENTER, MINE_ZOOM, MINE_SENSORS, MINE_INFRASTRUCTURE } from '../../data/mineGeoData';
import { RISK_BANDS } from '../../data/mockData';
import MapLegend from './MapLegend';
import { AlertOctagon, Navigation, Shield, Radio, ShieldAlert, Maximize2, Compass, Layers } from 'lucide-react';

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

const assemblyIcon = createCustomIcon(
  `<div class="w-7 h-7 rounded-full bg-[#5e7f3a]/20 border-2 border-[#5e7f3a] flex items-center justify-center text-[#5e7f3a] shadow-md backdrop-blur-sm">
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/></svg>
  </div>`,
  'assembly-point-pin'
);

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

// Map Controller component to ensure proper bounds and size recalculation
function MapController() {
  const map = useMap();

  useEffect(() => {
    // Invalidate map size on initial mount to fix layout bounding
    const timer = setTimeout(() => {
      map.invalidateSize();
      map.setView(MINE_CENTER, MINE_ZOOM);
    }, 150);
    return () => clearTimeout(timer);
  }, [map]);

  return null;
}

// Synthetic Bench Topographic Contours (RL Elevations) to provide rich, offline-independent pit geography
const BENCH_CONTOURS = [
  // Upper Crest (RL +240m)
  {
    name: 'Pit Crest Rim (RL +240m)',
    coords: [
      [23.7620, 86.4180],
      [23.7625, 86.4290],
      [23.7590, 86.4370],
      [23.7510, 86.4360],
      [23.7445, 86.4290],
      [23.7445, 86.4180],
      [23.7530, 86.4110],
      [23.7620, 86.4180],
    ],
    color: '#997e67',
    dash: '6, 4',
  },
  // Mid Bench 04 (RL +180m)
  {
    name: 'Mid Bench 04 (RL +180m)',
    coords: [
      [23.7595, 86.4205],
      [23.7600, 86.4270],
      [23.7570, 86.4330],
      [23.7525, 86.4325],
      [23.7475, 86.4270],
      [23.7475, 86.4200],
      [23.7535, 86.4145],
      [23.7595, 86.4205],
    ],
    color: '#b8a695',
    dash: '4, 4',
  },
  // Lower Bench 08 (RL +120m)
  {
    name: 'Lower Bench 08 (RL +120m)',
    coords: [
      [23.7575, 86.4220],
      [23.7578, 86.4265],
      [23.7550, 86.4295],
      [23.7525, 86.4285],
      [23.7500, 86.4250],
      [23.7510, 86.4205],
      [23.7550, 86.4180],
      [23.7575, 86.4220],
    ],
    color: '#d2c3b3',
    dash: '3, 3',
  },
];

export default function MineMap() {
  const {
    zones,
    selectedZoneId,
    selectZone,
    activeRoutePlan,
    mapLayers,
    activeSimulation,
  } = useMineContext();

  const [tileMode, setTileMode] = useState('dark'); // 'dark', 'osm', 'vector'

  // Zone colors lookup
  const getZoneFillColor = (band) => {
    const meta = RISK_BANDS[band];
    return meta ? meta.badgeColor : '#5e7f3a';
  };

  return (
    <div className="relative w-full h-full min-h-[480px] bg-mine-darkest rounded-2xl overflow-hidden border border-mine-border shadow-md flex flex-col">
      {/* Top Banner on Map */}
      <div className="absolute top-3 left-3 z-[400] bg-mine-card border border-mine-border rounded-lg px-3 py-1.5 text-xs font-medium text-mine-text flex items-center gap-2 shadow-sm">
        <span className="w-2 h-2 rounded-full bg-talus-600 animate-pulse"></span>
        <span className="font-semibold">Open-Pit Mine GIS Layout</span>
        <span className="text-mine-muted font-mono">|</span>
        <span className="text-mine-muted text-[11px]">Click any zone polygon to inspect risk intelligence</span>
      </div>

      {/* Top-Right Map Controls: Reset View / Basemap Mode */}
      <div className="absolute top-3 right-3 z-[400] flex items-center gap-1.5 bg-mine-card border border-mine-border rounded-lg p-1 shadow-sm">
        <button
          onClick={() => setTileMode(tileMode === 'dark' ? 'osm' : tileMode === 'osm' ? 'vector' : 'dark')}
          className="px-2 py-1 bg-mine-darker hover:bg-mine-dark text-mine-text rounded text-[10px] font-mono font-semibold flex items-center gap-1 transition-colors"
          title="Switch Basemap Style"
        >
          <Layers className="w-3 h-3 text-talus-600" />
          <span>Layer: {tileMode.toUpperCase()}</span>
        </button>
      </div>

      <MapContainer
        center={MINE_CENTER}
        zoom={MINE_ZOOM}
        scrollWheelZoom={true}
        className="w-full h-full flex-1"
        zoomControl={false}
        attributionControl={false}
      >
        <MapController />

        {/* Dynamic Basemap Layer with Graceful Offline Handling */}
        {tileMode === 'dark' && (
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png"
            maxZoom={19}
            subdomains="abcd"
          />
        )}

        {tileMode === 'osm' && (
          <TileLayer
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            maxZoom={19}
          />
        )}

        {/* Topographic Bench Elevation Contours (Always Visible, completely independent of external tile availability) */}
        {BENCH_CONTOURS.map((contour, i) => (
          <Polyline
            key={i}
            positions={contour.coords}
            pathOptions={{
              color: contour.color,
              weight: 1.5,
              dashArray: contour.dash,
              opacity: 0.7,
            }}
          >
            <Tooltip sticky direction="top">
              <span className="text-[10px] font-mono text-mine-text">{contour.name}</span>
            </Tooltip>
          </Polyline>
        ))}

        {/* Terraced Mine Pit Zone Polygons */}
        {zones.map((zone) => {
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
                      {isSelected && <span className="text-[10px] text-talus-600 font-normal">(Selected)</span>}
                    </div>
                    <div className="text-[11px] flex items-center gap-2">
                      <span className="font-mono font-bold" style={{ color: fillColor }}>
                        Risk: {zone.risk_score}/100 [{zone.risk_band}]
                      </span>
                      <span className="text-mine-muted">Conf: {zone.confidence}%</span>
                    </div>
                    {zone.shap && zone.shap[0] && (
                      <div className="text-[10px] text-mine-muted">
                        Primary: {zone.shap[0].feature} (+{zone.shap[0].value})
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
                        <span>{zone.name} — Hazard Zone</span>
                      </div>
                      <p className="text-[11px] text-mine-text">
                        Risk Score: <strong className="text-risk-critical">{zone.risk_score}</strong> / 100 ({zone.risk_band})
                      </p>
                      <p className="text-[10px] text-mine-muted">
                        Pore-pressure & crack density escalating. Immediate avoidance recommended.
                      </p>
                    </div>
                  </Popup>
                </Marker>
              )}
            </React.Fragment>
          );
        })}

        {/* Sensor Node Markers */}
        {mapLayers.sensors &&
          MINE_SENSORS.map((sensor) => (
            <Marker key={sensor.id} position={sensor.coordinates} icon={sensorIcon}>
              <Popup>
                <div className="p-1 space-y-1">
                  <div className="flex items-center gap-1 text-talus-600 font-semibold text-xs">
                    <Radio className="w-3.5 h-3.5" />
                    <span>{sensor.name}</span>
                  </div>
                  <div className="text-[11px] text-mine-text font-mono">{sensor.reading}</div>
                  <div className="text-[10px] text-mine-muted flex items-center justify-between">
                    <span>Type: {sensor.type}</span>
                    <span
                      className={`font-semibold ${
                        sensor.status === 'online' ? 'text-risk-verylow' : 'text-risk-moderate'
                      }`}
                    >
                      [{sensor.status.toUpperCase()}]
                    </span>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

        {/* Infrastructure & Assembly Point Markers */}
        {mapLayers.infrastructure &&
          MINE_INFRASTRUCTURE.map((item) => (
            <Marker key={item.id} position={item.coordinates} icon={assemblyIcon}>
              <Popup>
                <div className="p-1 space-y-1">
                  <div className="flex items-center gap-1 text-risk-verylow font-semibold text-xs">
                    <Shield className="w-3.5 h-3.5" />
                    <span>{item.name}</span>
                  </div>
                  {item.capacity && (
                    <div className="text-[11px] text-mine-text">Capacity: {item.capacity}</div>
                  )}
                  <div className="text-[10px] text-mine-muted">Status: {item.status}</div>
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
                      Distance: {activeRoutePlan.normalRoute.distanceKm} km | Exposure: HIGH (
                      {activeRoutePlan.normalRoute.riskExposureScore})
                    </div>
                    <div className="text-[10px] text-risk-critical">
                      ⚠ Direct rockfall hazard in {activeRoutePlan.normalRoute.passesThroughHazardZone}
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
                      Distance: {activeRoutePlan.riskAwareRoute.distanceKm} km | Exposure: LOW (
                      {activeRoutePlan.riskAwareRoute.riskExposureScore})
                    </div>
                    <div className="text-[10px] text-risk-verylow">
                      ✓ Safely bypasses unstable highwall sectors
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
