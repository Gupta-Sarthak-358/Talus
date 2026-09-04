import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { CloudRain, Radio, Users, Compass } from 'lucide-react';

export default function QuickStatsBar() {
  const { zones, activeSimulation, selectedZoneData, locationData, scoringMode, t } = useTalusContext();

  // Live rainfall: from selected zone telemetry or active simulation override
  const liveRainfall = selectedZoneData?.telemetry?.rainfall_24h ?? selectedZoneData?.telemetry?.rainfall_24h_mm ?? null;
  const rainfallVal = activeSimulation?.inputs?.rainfall_24h ?? liveRainfall ?? 42;

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs text-mine-text">
      <div className="flex items-center gap-5 flex-wrap">
        {/* Weather Indicator */}
        <div className="flex items-center gap-2">
          <CloudRain className={`w-4 h-4 ${rainfallVal > 60 ? 'text-risk-moderate animate-bounce' : 'text-mine-muted'}`} />
          <span className="text-mine-muted">{t('quick.rainfall')}</span>
          <span className="font-mono font-semibold text-mine-text">
            {rainfallVal} mm {rainfallVal > 60 && <span className="text-[10px] text-risk-high font-bold ml-1">{t('quick.monsoonSaturation')}</span>}
          </span>
        </div>

        {/* Slopes Monitored — per corridor */}
        <div className="flex items-center gap-2 border-l border-mine-border pl-4">
          <Users className="w-4 h-4 text-talus-600" />
          <span className="text-mine-muted">{t('quick.slopesMonitored')}</span>
          <span className="font-mono font-semibold text-mine-text">{zones.map(z=>z.id).join('–')} ({zones.length})</span>
        </div>

        {/* Model Status */}
        <div className="hidden sm:flex items-center gap-2 border-l border-mine-border pl-4">
          <Radio className="w-4 h-4 text-risk-verylow animate-pulse" />
          <span className="text-mine-muted">{t('quick.riskEngine')}</span>
          <span className="font-semibold text-risk-verylow">{scoringMode === 'live-rf' ? t('quick.liveModel') : t('quick.frozenModel')}</span>
        </div>
      </div>

      <div className="flex items-center gap-3 text-[11px] text-mine-muted">
        <span className="flex items-center gap-1 font-mono">
          <Compass className="w-3.5 h-3.5 text-mine-muted" />
          {locationData.label} · {locationData.center[0].toFixed(4)}, {locationData.center[1].toFixed(4)} (EPSG:4326)
        </span>
      </div>
    </div>
  );
}