import React, { useState } from 'react';
import { useMineContext } from '../../context/MineContext';
import { Layers, ChevronUp, ChevronDown, CheckSquare, Square } from 'lucide-react';

const RISK_BAND_KEYS = [
  { label: 'CRITICAL (85–100)', color: '#c74732', border: 'border-[#c74732]', bg: 'bg-[#c74732]' },
  { label: 'HIGH (75–84)', color: '#d96b24', border: 'border-[#d96b24]', bg: 'bg-[#d96b24]' },
  { label: 'MODERATE (65–74)', color: '#d99a24', border: 'border-[#d99a24]', bg: 'bg-[#d99a24]' },
  { label: 'LOW (50–64)', color: '#a68a3c', border: 'border-[#a68a3c]', bg: 'bg-[#a68a3c]' },
  { label: 'VERY LOW (<50)', color: '#5e7f3a', border: 'border-[#5e7f3a]', bg: 'bg-[#5e7f3a]' },
];

const ROAD_LEGEND = [
  { label: 'R1 Blocked (Debris)', color: '#c74732', dash: 'dotted' },
  { label: 'R2 At-Risk (Avoided)', color: '#d97706', dash: 'dashed' },
  { label: 'R3 / R4 Open', color: '#5e7f3a', dash: 'solid' },
];

export default function MapLegend() {
  const { mapLayers, toggleMapLayer } = useMineContext();
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="absolute bottom-4 left-4 z-[400] bg-mine-card border border-mine-border rounded-xl shadow-lg text-xs text-mine-text w-64 overflow-hidden transition-all">
      {/* Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="px-3 py-2 bg-mine-darker border-b border-mine-border flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-1.5 font-semibold text-mine-text">
          <Layers className="w-3.5 h-3.5 text-talus-600" />
          <span>Landslide GIS Layers</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-mine-muted" />
        ) : (
          <ChevronUp className="w-3.5 h-3.5 text-mine-muted" />
        )}
      </div>

      {isExpanded && (
        <div className="p-3 space-y-3 max-h-80 overflow-y-auto">
          {/* Risk Color Scales */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-mine-muted mb-1.5">
              Susceptibility Risk Bands
            </div>
            <div className="space-y-1">
              {RISK_BAND_KEYS.map((b) => (
                <div key={b.label} className="flex items-center gap-2 text-[11px]">
                  <span
                    className="w-3 h-3 rounded-sm shrink-0 border border-mine-border shadow-sm"
                    style={{ backgroundColor: b.color }}
                  ></span>
                  <span className="font-mono text-mine-text">{b.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Road Network Legend */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-mine-muted mb-1.5">
              Road Network (R1–R4)
            </div>
            <div className="space-y-1">
              {ROAD_LEGEND.map((r) => (
                <div key={r.label} className="flex items-center gap-2 text-[11px]">
                  <span
                    className="w-4 h-1 rounded-sm shrink-0"
                    style={{ backgroundColor: r.color }}
                  ></span>
                  <span className="text-mine-text">{r.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Layer Toggles */}
          <div className="border-t border-mine-border pt-2.5 space-y-1.5">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-mine-muted mb-1">
              Display Overlays
            </div>

            <button
              onClick={() => toggleMapLayer('routes')}
              className="w-full flex items-center justify-between py-1 text-mine-text hover:text-talus-600 transition-colors"
            >
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-0.5 bg-risk-verylow inline-block"></span>
                Safe vs Normal Routes
              </span>
              {mapLayers.routes ? (
                <CheckSquare className="w-3.5 h-3.5 text-talus-600" />
              ) : (
                <Square className="w-3.5 h-3.5 text-mine-border" />
              )}
            </button>

            <button
              onClick={() => toggleMapLayer('sensors')}
              className="w-full flex items-center justify-between py-1 text-mine-text hover:text-talus-600 transition-colors"
            >
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-talus-600 inline-block"></span>
                Telemetry Sensors
              </span>
              {mapLayers.sensors ? (
                <CheckSquare className="w-3.5 h-3.5 text-talus-600" />
              ) : (
                <Square className="w-3.5 h-3.5 text-mine-border" />
              )}
            </button>

            <button
              onClick={() => toggleMapLayer('infrastructure')}
              className="w-full flex items-center justify-between py-1 text-mine-text hover:text-talus-600 transition-colors"
            >
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-risk-moderate inline-block"></span>
                Assembly & Facilities
              </span>
              {mapLayers.infrastructure ? (
                <CheckSquare className="w-3.5 h-3.5 text-talus-600" />
              ) : (
                <Square className="w-3.5 h-3.5 text-mine-border" />
              )}
            </button>

            <button
              onClick={() => toggleMapLayer('hazardGlow')}
              className="w-full flex items-center justify-between py-1 text-mine-text hover:text-talus-600 transition-colors"
            >
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-risk-critical animate-pulse inline-block"></span>
                Hazard Pulse Animation
              </span>
              {mapLayers.hazardGlow ? (
                <CheckSquare className="w-3.5 h-3.5 text-talus-600" />
              ) : (
                <Square className="w-3.5 h-3.5 text-mine-border" />
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
