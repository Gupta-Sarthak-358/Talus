import React, { useState } from 'react';
import { useMineContext } from '../../context/MineContext';
import { Layers, ChevronUp, ChevronDown, CheckSquare, Square } from 'lucide-react';

const RISK_BAND_KEYS = [
  { label: 'CRITICAL (85–100)', color: '#ef4444', border: 'border-red-500', bg: 'bg-red-500' },
  { label: 'HIGH (66–84)', color: '#f97316', border: 'border-orange-500', bg: 'bg-orange-500' },
  { label: 'MODERATE (41–65)', color: '#f59e0b', border: 'border-amber-500', bg: 'bg-amber-500' },
  { label: 'LOW (21–40)', color: '#22c55e', border: 'border-green-500', bg: 'bg-green-500' },
  { label: 'VERY LOW (0–20)', color: '#10b981', border: 'border-emerald-500', bg: 'bg-emerald-500' },
];

export default function MapLegend() {
  const { mapLayers, toggleMapLayer } = useMineContext();
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="absolute bottom-4 left-4 z-[400] bg-mine-card/95 border border-mine-border/90 rounded-xl shadow-2xl backdrop-blur-md text-xs text-slate-300 w-64 overflow-hidden transition-all">
      {/* Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="px-3 py-2 bg-mine-darker/90 border-b border-mine-border flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-1.5 font-semibold text-slate-100">
          <Layers className="w-3.5 h-3.5 text-talus-400" />
          <span>Mine Map GIS Layers</span>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        ) : (
          <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
        )}
      </div>

      {isExpanded && (
        <div className="p-3 space-y-3 max-h-80 overflow-y-auto">
          {/* Risk Color Scales */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
              Operational Risk Bands
            </div>
            <div className="space-y-1">
              {RISK_BAND_KEYS.map((b) => (
                <div key={b.label} className="flex items-center gap-2 text-[11px]">
                  <span
                    className="w-3 h-3 rounded-sm shrink-0 border border-black/40 shadow-sm"
                    style={{ backgroundColor: b.color }}
                  ></span>
                  <span className="font-mono text-slate-300">{b.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Layer Toggles */}
          <div className="border-t border-mine-border/70 pt-2.5 space-y-1.5">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Display Overlays
            </div>

            <button
              onClick={() => toggleMapLayer('routes')}
              className="w-full flex items-center justify-between py-1 text-slate-300 hover:text-white transition-colors"
            >
              <span className="flex items-center gap-2">
                <span className="w-2.5 h-0.5 bg-emerald-400 inline-block"></span>
                Safe vs Normal Routes
              </span>
              {mapLayers.routes ? (
                <CheckSquare className="w-3.5 h-3.5 text-talus-400" />
              ) : (
                <Square className="w-3.5 h-3.5 text-slate-600" />
              )}
            </button>

            <button
              onClick={() => toggleMapLayer('sensors')}
              className="w-full flex items-center justify-between py-1 text-slate-300 hover:text-white transition-colors"
            >
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block"></span>
                Telemetry Sensors
              </span>
              {mapLayers.sensors ? (
                <CheckSquare className="w-3.5 h-3.5 text-talus-400" />
              ) : (
                <Square className="w-3.5 h-3.5 text-slate-600" />
              )}
            </button>

            <button
              onClick={() => toggleMapLayer('infrastructure')}
              className="w-full flex items-center justify-between py-1 text-slate-300 hover:text-white transition-colors"
            >
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 bg-amber-400 inline-block"></span>
                Assembly & Facilities
              </span>
              {mapLayers.infrastructure ? (
                <CheckSquare className="w-3.5 h-3.5 text-talus-400" />
              ) : (
                <Square className="w-3.5 h-3.5 text-slate-600" />
              )}
            </button>

            <button
              onClick={() => toggleMapLayer('hazardGlow')}
              className="w-full flex items-center justify-between py-1 text-slate-300 hover:text-white transition-colors"
            >
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse inline-block"></span>
                Hazard Pulse Animation
              </span>
              {mapLayers.hazardGlow ? (
                <CheckSquare className="w-3.5 h-3.5 text-talus-400" />
              ) : (
                <Square className="w-3.5 h-3.5 text-slate-600" />
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
