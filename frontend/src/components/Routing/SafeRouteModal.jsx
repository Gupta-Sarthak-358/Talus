import React, { useState } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RouteComparisonCard from './RouteComparisonCard';
import { routePresetsFor, defaultOriginKey } from '../../services/routing';
import { Navigation, X, Play, MapPin, Compass, ShieldAlert } from 'lucide-react';

export default function SafeRouteModal() {
  const {
    isRouteModalOpen,
    setIsRouteModalOpen,
    activeRoutePlan,
    executeRouting,
    activeLocation,
    t,
  } = useTalusContext();

  const corridor = routePresetsFor(activeLocation);
  const ROUTE_PRESETS = Object.entries(corridor.presets).map(([key, p]) => ({
    key,
    label: `${p.start} → ${p.end} Staging`,
    origin: key === corridor.defaultKey ? corridor.originName : `${p.start} (Upper)`,
    destination: key === corridor.defaultKey ? corridor.destName : `${p.end} (Valley Staging)`,
    threatAvoided: corridor.threat,
  }));

  const [selectedRouteKey, setSelectedRouteKey] = useState(corridor.defaultKey);
  const [calculating, setCalculating] = useState(false);
  // If the corridor switched while the modal was closed, fall back to its default preset
  const effectiveKey = ROUTE_PRESETS.some((p) => p.key === selectedRouteKey)
    ? selectedRouteKey
    : corridor.defaultKey;

  if (!isRouteModalOpen) return null;

  const handleCalculate = async () => {
    setCalculating(true);
    try {
      await executeRouting({ originKey: effectiveKey, location: activeLocation });
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-mine-card border border-mine-border rounded-2xl shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-4 bg-mine-darker border-b border-mine-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-risk-verylow/15 text-risk-verylow flex items-center justify-center">
              <Navigation className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-mine-text">{t('routing.title')}</h3>
              <p className="text-[11px] text-mine-muted">
                {t('routing.subtitle')}
              </p>
            </div>
          </div>

          <button
            onClick={() => setIsRouteModalOpen(false)}
            className="p-1.5 rounded-lg hover:bg-mine-dark text-mine-muted hover:text-mine-text transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 overflow-y-auto">
          {/* Origin / Destination Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-mine-text">
              {t('routing.selectScenario')}
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {ROUTE_PRESETS.map((preset) => (
                <button
                  key={preset.key}
                  onClick={() => setSelectedRouteKey(preset.key)}
                  className={`p-3 rounded-xl text-left border transition-all ${
                    effectiveKey === preset.key
                      ? 'bg-talus-600/15 border-talus-600 text-mine-text shadow-sm'
                      : 'bg-mine-darker hover:bg-mine-dark border-mine-border text-mine-text'
                  }`}
                >
                  <div className="text-xs font-bold text-mine-text">{preset.label}</div>
                  <div className="text-[11px] text-mine-muted mt-1 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-talus-600" />
                    <span>{t('routing.from')} {preset.origin}</span>
                  </div>
                  <div className="text-[11px] text-mine-muted flex items-center gap-1">
                    <Compass className="w-3 h-3 text-risk-verylow" />
                    <span>{t('routing.to')} {preset.destination}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Action Trigger */}
          <div className="flex justify-end">
            <button
              onClick={handleCalculate}
              disabled={calculating}
              className="flex items-center gap-2 px-4 py-2 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-xs font-bold transition-all shadow-sm disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{calculating ? t('routing.calculating') : t('routing.calculate')}</span>
            </button>
          </div>

          {/* Comparison Output */}
          <RouteComparisonCard routePlan={activeRoutePlan} />
        </div>

        {/* Footer */}
        <div className="p-4 bg-mine-darker border-t border-mine-border flex items-center justify-between text-xs text-mine-muted">
          <span>{t('routing.bothProjected')}</span>
          <button
            onClick={() => setIsRouteModalOpen(false)}
            className="px-3 py-1.5 bg-mine-card hover:bg-mine-dark text-mine-text border border-mine-border rounded-lg text-xs font-semibold transition-colors"
          >
            {t('routing.viewOnMap')}
          </button>
        </div>
      </div>
    </div>
  );
}
