import React from 'react';
import { useMineContext } from '../../context/MineContext';
import { AlertTriangle, ShieldAlert, CheckCircle2, Database, TrendingUp } from 'lucide-react';

const idsOf = (zones) => zones.map((z) => z.id).join(', ') || '—';

export default function RiskSummaryCards() {
  const { riskSummary, zones, selectZone, selectedZoneId } = useMineContext();

  if (!riskSummary) return null;

  const criticalZones = zones.filter((z) => z.risk_band === 'CRITICAL');
  const highZones = zones.filter((z) => z.risk_band === 'HIGH');
  const moderateZones = zones.filter((z) => z.risk_band === 'MODERATE');
  const lowZones = zones.filter((z) => z.risk_band === 'LOW' || z.risk_band === 'VERY_LOW');

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {/* Critical & High Risk Zones Card */}
      <div
        onClick={() => {
          if (criticalZones.length > 0) selectZone(criticalZones[0].id);
          else if (highZones.length > 0) selectZone(highZones[0].id);
        }}
        className="cursor-pointer bg-mine-card hover:bg-mine-dark border border-red-500/30 hover:border-red-500/60 rounded-xl p-3.5 transition-all shadow-md group relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full blur-xl group-hover:bg-red-500/10 transition-all"></div>
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-red-500/20 text-red-400 flex items-center justify-center">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold text-red-400 uppercase tracking-wider px-2 py-0.5 rounded bg-red-500/10 border border-red-500/20">
            Escalated
          </span>
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white font-mono">
            {riskSummary.criticalCount + riskSummary.highCount}
          </span>
          <span className="text-xs text-slate-400 font-medium">
            High / Critical Zone{riskSummary.criticalCount + riskSummary.highCount !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-mine-border/60 pt-1.5 gap-1">
          <span className="truncate">Zones: {idsOf([...criticalZones, ...highZones])}</span>
          <span className="text-red-400 font-semibold flex items-center gap-0.5 shrink-0">
            <TrendingUp className="w-3 h-3" /> Action req.
          </span>
        </div>
      </div>

      {/* Moderate Risk Card */}
      <div
        onClick={() => {
          if (moderateZones.length > 0) selectZone(moderateZones[0].id);
        }}
        className="cursor-pointer bg-mine-card hover:bg-mine-dark border border-amber-500/30 hover:border-amber-500/60 rounded-xl p-3.5 transition-all shadow-md group relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-xl group-hover:bg-amber-500/10 transition-all"></div>
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold text-amber-400 uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
            Surveillance
          </span>
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white font-mono">
            {riskSummary.moderateCount}
          </span>
          <span className="text-xs text-slate-400 font-medium">
            Moderate Zone{riskSummary.moderateCount !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-mine-border/60 pt-1.5 gap-1">
          <span className="truncate">Zones: {idsOf(moderateZones)}</span>
          <span className="text-amber-400 font-medium shrink-0">Monitoring</span>
        </div>
      </div>

      {/* Stable / Low Risk Card */}
      <div
        onClick={() => {
          if (lowZones.length > 0) selectZone(lowZones[0].id);
        }}
        className="cursor-pointer bg-mine-card hover:bg-mine-dark border border-emerald-500/30 hover:border-emerald-500/60 rounded-xl p-3.5 transition-all shadow-md group relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl group-hover:bg-emerald-500/10 transition-all"></div>
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
            Nominal
          </span>
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white font-mono">
            {riskSummary.lowCount}
          </span>
          <span className="text-xs text-slate-400 font-medium">
            Stable Zone{riskSummary.lowCount !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-mine-border/60 pt-1.5 gap-1">
          <span className="truncate">Zones: {idsOf(lowZones)}</span>
          <span className="text-emerald-400 font-medium shrink-0">No escalation</span>
        </div>
      </div>

      {/* Data Quality & Model Confidence Card */}
      <div className="bg-mine-card border border-talus-500/30 rounded-xl p-3.5 transition-all shadow-md relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-24 bg-talus-500/5 rounded-full blur-xl"></div>
        <div className="flex items-center justify-between">
          <div className="w-8 h-8 rounded-lg bg-talus-500/20 text-talus-400 flex items-center justify-center">
            <Database className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold text-talus-300 uppercase tracking-wider px-2 py-0.5 rounded bg-talus-500/10 border border-talus-500/20">
            Evidence Quality
          </span>
        </div>
        <div className="mt-2.5 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white font-mono">
            {riskSummary.dataQualityConfidence}%
          </span>
          <span className="text-xs text-slate-400 font-medium">Mean Calibrated Confidence</span>
        </div>
        <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 border-t border-mine-border/60 pt-1.5 gap-1">
          <span className="truncate">3 provenance gaps (modeled PPV / GW proxy / no CV feed)</span>
          <span className="text-amber-400 font-medium shrink-0">Flagged</span>
        </div>
      </div>
    </div>
  );
}