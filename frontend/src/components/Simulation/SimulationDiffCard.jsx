import React from 'react';
import RiskBadge from '../Common/RiskBadge';
import { ArrowRight, TrendingUp, TrendingDown, Sparkles, ShieldAlert } from 'lucide-react';

export default function SimulationDiffCard({ simulationResult, baselineZone }) {
  if (!simulationResult) return null;

  const { risk_score, risk_band, confidence, delta, isEscalated, shap, explanationText } = simulationResult;
  const baseScore = baselineZone ? baselineZone.risk_score : 82;
  const baseBand = baselineZone ? baselineZone.risk_band : 'HIGH';

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl p-4 space-y-3 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-mine-text">
          <Sparkles className="w-4 h-4 text-talus-600" />
          <h4 className="text-xs font-bold uppercase tracking-wider">
            Simulated Risk Delta
          </h4>
        </div>
        <span
          className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${
            isEscalated
              ? 'bg-risk-critical/15 text-risk-critical border border-risk-critical/30'
              : 'bg-risk-verylow/15 text-risk-verylow border border-risk-verylow/30'
          }`}
        >
          {delta} pts vs Baseline
        </span>
      </div>

      {/* Before / After Comparison */}
      <div className="grid grid-cols-2 gap-3 p-3 bg-mine-card rounded-lg border border-mine-border text-center">
        <div>
          <div className="text-[10px] text-mine-muted uppercase font-semibold">Baseline Risk</div>
          <div className="text-xl font-bold font-mono text-mine-text mt-1">{baseScore} / 100</div>
          <div className="mt-1">
            <RiskBadge band={baseBand} size="sm" />
          </div>
        </div>

        <div className="border-l border-mine-border pl-2">
          <div className="text-[10px] text-talus-600 uppercase font-semibold">Simulated Risk</div>
          <div className="text-xl font-bold font-mono text-risk-high mt-1">{risk_score} / 100</div>
          <div className="mt-1">
            <RiskBadge band={risk_band} size="sm" />
          </div>
        </div>
      </div>

      {/* Explanation Text */}
      <p className="text-[11px] text-mine-text leading-relaxed">
        {explanationText}
      </p>

      {/* Dynamic SHAP Preview */}
      <div className="space-y-1 pt-1">
        <div className="text-[10px] uppercase font-bold text-mine-muted">
          Top Shifted Risk Drivers:
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {shap.slice(0, 2).map((s) => (
            <div
              key={s.feature}
              className="p-1.5 bg-mine-darker rounded border border-mine-border text-[11px] flex justify-between"
            >
              <span className="text-mine-text truncate">{s.feature.split('(')[0]}</span>
              <span className="font-mono font-bold text-risk-high">+{s.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
