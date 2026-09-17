import React, { useState } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { Layers, ChevronUp, ChevronDown, CheckSquare, Square } from 'lucide-react';

const RISK_BAND_KEYS = [
  { key: 'critical', color: '#c74732', border: 'border-[#c74732]', bg: 'bg-[#c74732]' },
  { key: 'high', color: '#d96b24', border: 'border-[#d96b24]', bg: 'bg-[#d96b24]' },
  { key: 'moderate', color: '#d99a24', border: 'border-[#d99a24]', bg: 'bg-[#d99a24]' },
  { key: 'low', color: '#a68a3c', border: 'border-[#a68a3c]', bg: 'bg-[#a68a3c]' },
  { key: 'very_low', color: '#5e7f3a', border: 'border-[#5e7f3a]', bg: 'bg-[#5e7f3a]' },
];

const ROAD_LEGEND = [
  { key: 'blocked', color: '#c74732', dash: 'dotted' },
  { key: 'at_risk', color: '#d97706', dash: 'dashed' },
  { key: 'open', color: '#5e7f3a', dash: 'solid' },
];

export default function MapLegend() {
  const { mapLayers, toggleMapLayer, t, role } = useTalusContext();
  const isVillager = role === 'villager';
  const [isExpanded, setIsExpanded] = useState(!isVillager);

  return (
    <div className="absolute bottom-4 left-4 z-[400] bg-mine-card border border-mine-border rounded-xl shadow-lg text-xs text-mine-text w-64 overflow-hidden transition-all">
      {/* Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="px-3 py-2 bg-mine-darker border-b border-mine-border flex items-center justify-between cursor-pointer select-none"
      >
        <div className="flex items-center gap-1.5 font-semibold text-mine-text">
          <Layers className="w-3.5 h-3.5 text-talus-600" />
          <span>{t('map.legend')}</span>
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
              {t('map.riskBands')}
            </div>
            <div className="space-y-1">
              {RISK_BAND_KEYS.map((b) => (
                <div key={b.key} className="flex items-center gap-2 text-[11px]">
                  <span
                    className="w-3 h-3 rounded-sm shrink-0 border border-mine-border shadow-sm"
                    style={{ backgroundColor: b.color }}
                  ></span>
                  <span className="font-mono text-mine-text">{t(`map.legend.${b.key}`)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Road Network Legend */}
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-mine-muted mb-1.5">
              {t('map.roadNetwork')}
            </div>
            <div className="space-y-1">
              {ROAD_LEGEND.map((r) => (
                <div key={r.key} className="flex items-center gap-2 text-[11px]">
                  <span
                    className="w-4 h-1 rounded-sm shrink-0"
                    style={{ backgroundColor: r.color }}
                  ></span>
                  <span className="text-mine-text">{t(`road.legend.${r.key}`)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Layer Toggles — hidden for villager (ops/mgmt only) */}
          {!isVillager && (
            <div className="border-t border-mine-border pt-2.5 space-y-1.5">
              <div className="text-[10px] font-semibold uppercase tracking-wider text-mine-muted mb-1">
                {t('map.displayOverlays')}
              </div>

              <button
                onClick={() => toggleMapLayer('routes')}
                className="w-full flex items-center justify-between py-1 text-mine-text hover:text-talus-600 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-0.5 bg-risk-verylow inline-block"></span>
                  {t('map.safeVsNormal')}
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
                  {t('map.telemetrySensors')}
                </span>
                {mapLayers.sensors ? (
                  <CheckSquare className="w-3.5 h-3.5 text-talus-600" />
                ) : (
                  <Square className="w-3.5 h-3.5 text-mine-border" />
                )}
              </button>

              <button
                onClick={() => toggleMapLayer('runout')}
                className="w-full flex items-center justify-between py-1 text-mine-text hover:text-talus-600 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <span className="w-4 h-0.5 bg-risk-critical inline-block" style={{ borderTop: '2px dashed #c74732', height: 0 }}></span>
                  {t('map.runout') || 'Runout path'}
                </span>
                {mapLayers.runout ? (
                  <CheckSquare className="w-3.5 h-3.5 text-talus-600" />
                ) : (
                  <Square className="w-3.5 h-3.5 text-mine-border" />
                )}
              </button>

              <button
                onClick={() => toggleMapLayer('wounds')}
                className="w-full flex items-center justify-between py-1 text-mine-text hover:text-talus-600 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-amber-400 inline-block"></span>
                  {t('map.vegetation') || 'Vegetation change'}
                </span>
                {mapLayers.wounds ? (
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
                  {t('map.hazardPulse')}
                </span>
                {mapLayers.hazardGlow ? (
                  <CheckSquare className="w-3.5 h-3.5 text-talus-600" />
                ) : (
                  <Square className="w-3.5 h-3.5 text-mine-border" />
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
