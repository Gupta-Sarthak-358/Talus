import React from 'react';
import { useMineContext } from '../../context/MineContext';
import { CloudRain, Wind, Radio, Users, Compass, Gauge } from 'lucide-react';

export default function QuickStatsBar() {
  const { zones, activeSimulation } = useMineContext();

  const totalPersonnel = zones.reduce((acc, z) => acc + (z.activePersonnel || 0), 0);
  const rainfallVal = activeSimulation ? activeSimulation.inputs.rainfall_24h : 42;

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

        {/* Personnel In Pit */}
        <div className="flex items-center gap-2 border-l border-mine-border/60 pl-4">
          <Users className="w-4 h-4 text-talus-400" />
          <span className="text-slate-400">Tracked Pit Personnel:</span>
          <span className="font-mono font-semibold text-white">{totalPersonnel} on shift</span>
        </div>

        {/* Slope Radar Status */}
        <div className="hidden sm:flex items-center gap-2 border-l border-mine-border/60 pl-4">
          <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span className="text-slate-400">In-Pit Slope Radar:</span>
          <span className="font-semibold text-emerald-300">Active (Scan: 0.04 mm/hr)</span>
        </div>
      </div>

      <div className="flex items-center gap-3 text-[11px] text-slate-400">
        <span className="flex items-center gap-1">
          <Compass className="w-3.5 h-3.5 text-slate-400" />
          Datum: WGS84 / UTM 45N
        </span>
      </div>
    </div>
  );
}
