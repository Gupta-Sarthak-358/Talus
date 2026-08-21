import React from 'react';
import { useMineContext } from '../../context/MineContext';
import { CloudRain, Radio, Users, Compass } from 'lucide-react';

export default function QuickStatsBar() {
  const { zones, activeSimulation } = useMineContext();

  const rainfallVal = activeSimulation?.inputs?.rainfall_24h ?? 42;

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs text-mine-text">
      <div className="flex items-center gap-5 flex-wrap">
        {/* Weather Indicator */}
        <div className="flex items-center gap-2">
          <CloudRain className={`w-4 h-4 ${rainfallVal > 60 ? 'text-risk-moderate animate-bounce' : 'text-mine-muted'}`} />
          <span className="text-mine-muted">Pit Rainfall (24h):</span>
          <span className="font-mono font-semibold text-mine-text">
            {rainfallVal} mm {rainfallVal > 60 && <span className="text-[10px] text-risk-high font-bold ml-1">[MONSOON SATURATION]</span>}
          </span>
        </div>

        {/* Zones Monitored */}
        <div className="flex items-center gap-2 border-l border-mine-border pl-4">
          <Users className="w-4 h-4 text-talus-600" />
          <span className="text-mine-muted">Zones Monitored:</span>
          <span className="font-mono font-semibold text-mine-text">{zones.length}</span>
        </div>

        {/* Model Status */}
        <div className="hidden sm:flex items-center gap-2 border-l border-mine-border pl-4">
          <Radio className="w-4 h-4 text-risk-verylow animate-pulse" />
          <span className="text-mine-muted">Risk Engine:</span>
          <span className="font-semibold text-risk-verylow">Frozen Model v1 (calibrated)</span>
        </div>
      </div>

      <div className="flex items-center gap-3 text-[11px] text-mine-muted">
        <span className="flex items-center gap-1">
          <Compass className="w-3.5 h-3.5 text-mine-muted" />
          Neyveli Mine-II · WGS84
        </span>
      </div>
    </div>
  );
}