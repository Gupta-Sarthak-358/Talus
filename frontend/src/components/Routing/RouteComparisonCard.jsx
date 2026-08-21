import React from 'react';
import { ShieldCheck, AlertOctagon, Clock, Navigation, ArrowRight } from 'lucide-react';

export default function RouteComparisonCard({ routePlan }) {
  if (!routePlan) return null;

  const { normalRoute, riskAwareRoute, comparison } = routePlan;

  return (
    <div className="space-y-4">
      {/* Summary Highlight */}
      <div className="p-3 bg-emerald-950/20 border border-emerald-500/40 rounded-xl text-xs text-emerald-300 flex items-start gap-2.5 shadow-md">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-emerald-200 uppercase tracking-wide">
            Risk-Aware Route Recommendation
          </div>
          <p className="text-[11px] text-emerald-300/90 leading-relaxed">
            {comparison.summary}
          </p>
        </div>
      </div>

      {/* Side-by-Side Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* 1. Shortest / Normal Route */}
        <div className="p-3.5 bg-red-950/10 border border-red-500/30 rounded-xl space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
              Shortest / Normal Route
            </span>
            <AlertOctagon className="w-4 h-4 text-red-400" />
          </div>

          <div>
            <div className="text-sm font-bold text-slate-100">{normalRoute.name}</div>
            <div className="text-[11px] text-red-300 mt-0.5">
              Traverses {normalRoute.passesThroughHazardZone}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-xs border-t border-red-500/20">
            <div>
              <div className="text-[10px] text-slate-400 font-sans">Distance</div>
              <div className="font-bold text-slate-200">{normalRoute.distanceKm} km</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-400 font-sans">Risk Exposure</div>
              <div className="font-bold text-red-400">{normalRoute.riskExposureScore} (HIGH)</div>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 italic">
            ⚠ {normalRoute.hazardDescription}
          </div>
        </div>

        {/* 2. Risk-Aware Route */}
        <div className="p-3.5 bg-emerald-950/20 border border-emerald-500/40 rounded-xl space-y-2.5 shadow-lg shadow-emerald-500/5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded border border-emerald-500/30">
              Recommended Safe Route
            </span>
            <Navigation className="w-4 h-4 text-emerald-400" />
          </div>

          <div>
            <div className="text-sm font-bold text-white">{riskAwareRoute.name}</div>
            <div className="text-[11px] text-emerald-300 mt-0.5">
              Avoids all active highwall hazard sectors
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-1 font-mono text-xs border-t border-emerald-500/20">
            <div>
              <div className="text-[10px] text-slate-400 font-sans">Distance</div>
              <div className="font-bold text-white">{riskAwareRoute.distanceKm} km (+0.3 km)</div>
            </div>
            <div>
              <div className="text-[10px] text-slate-400 font-sans">Risk Exposure</div>
              <div className="font-bold text-emerald-400">{riskAwareRoute.riskExposureScore} (LOW)</div>
            </div>
          </div>

          <div className="text-[10px] text-emerald-300/90">
            ✓ {riskAwareRoute.hazardDescription}
          </div>
        </div>
      </div>
    </div>
  );
}
