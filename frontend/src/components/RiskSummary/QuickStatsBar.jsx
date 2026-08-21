import React from 'react';
import { useMineContext } from '../../context/MineContext';
import { CloudRain, Wind, Radio, Users, Compass, Gauge } from 'lucide-react';

export default function QuickStatsBar() {
  const { zones, activeSimulation } = useMineContext();

  const rainfallVal = activeSimulation?.inputs?.rainfall_24h ?? 42;

  return (
    <div className="bg-mine-darker/80 border border-mine-border/60 rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-300">
      <div className="flex items-center gap-5 flex-wrap">
        {/* Weather Indicator */}
        <div className="flex items-center gap-2">
          <CloudRain className={`w-4 h-4 ${rainfallVal > 60 ? 'text-blue-400 animate-bounce' : 'text-slate-400'}`} />
          <span className="text-slate-400">Pit Rainfall (24h):</span>
          <span className="font-mono font-semibold text-white">
            {rainfallVal} mm {rainfallVal > 60 && <span className="text-[10px] text-amber-400 font-bold ml-1">[MONSOON SATURATION]</span>}
          </span>
        </div>

        {/* Zones Monitored */}
        <div className="flex items-center gap-2 border-l border-mine-border/60 pl-4">
          <Users className="w-4 h-4 text-talus-400" />
          <span className="text-slate-400">Zones Monitored:</span>
          <span className="font-mono font-semibold text-white">{zones.length}</span>
        </div>

        {/* Model Status */}
        <div className="hidden sm:flex items-center gap-2 border-l border-mine-border/60 pl-4">
          <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span className="text-slate-400">Risk Engine:</span>
          <span className="font-semibold text-emerald-300">Frozen Model v1 (calibrated)</span>
        </div>
      </div>

      <div className="flex items-center gap-3 text-[11px] text-slate-400">
        <span className="flex items-center gap-1">
          <Compass className="w-3.5 h-3.5 text-slate-400" />
          Neyveli Mine-II · WGS84
        </span>
      </div>
    </div>
  );
}
