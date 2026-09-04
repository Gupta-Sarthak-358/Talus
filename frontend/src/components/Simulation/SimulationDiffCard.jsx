import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskBadge from '../Common/RiskBadge';
import { ArrowRight, TrendingUp, TrendingDown, Sparkles, ShieldAlert } from 'lucide-react';

export default function SimulationDiffCard({ simulationResult, baselineZone }) {
  const { t } = useTalusContext();
  if (!simulationResult) return null;

  const { risk_score, risk_band, confidence, delta, isEscalated, shap, explanationText,
          baselineScore, baselineBand } = simulationResult;
  // Use the backend's pre-override prediction as baseline (falls back to the
  // selected zone's current score only if the API didn't send one).
  const baseScore = baselineScore ?? (baselineZone ? baselineZone.risk_score : 82);
  const baseBand = baselineBand ?? (baselineZone ? baselineZone.risk_band : 'HIGH');

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl p-4 space-y-3 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-mine-text">
          <Sparkles className="w-4 h-4 text-talus-600" />
          <h4 className="text-xs font-bold uppercase tracking-wider">
            {t('simdiff.title')}
          </h4>
        </div>
        <span
          title={`Simulated (${risk_score}) minus the pre-override prediction (${baseScore}). Positive = the model predicts higher risk under the changed inputs.`}
          className={`text-xs font-bold font-mono px-2 py-0.5 rounded cursor-help ${
            isEscalated
              ? 'bg-risk-critical/15 text-risk-critical border border-risk-critical/30'
              : 'bg-risk-verylow/15 text-risk-verylow border border-risk-verylow/30'
          }`}
        >
          Risk change: {delta > 0 ? '+' : ''}{delta} pts
        </span>
      </div>
      <p className="text-[10px] text-mine-muted -mt-1">
        Same frozen model. Current inputs vs. overridden inputs. Delta = right minus left.
        {Math.abs(delta) < 2 && ' Overrides barely move this zone -- its risk is dominated by static structure.'}
      </p>

      {/* Before / After Comparison */}
      <div className="grid grid-cols-2 gap-3 p-3 bg-mine-card rounded-lg border border-mine-border text-center">
        <div>
          <div className="text-[10px] text-mine-muted uppercase font-semibold">{t('simdiff.current')}</div>
          <div className="text-[9px] text-mine-muted -mt-0.5">Model prediction from observed inputs</div>
          <div className="text-xl font-bold font-mono text-mine-text mt-1">{baseScore} / 100</div>
          <div className="mt-1">
            <RiskBadge band={baseBand} size="sm" />
          </div>
        </div>

        <div className="border-l border-mine-border pl-2">
          <div className="text-[10px] text-talus-600 uppercase font-semibold">{t('simdiff.whatif')}</div>
          <div className="text-[9px] text-mine-muted -mt-0.5">Model prediction with your overrides</div>
          <div className="text-xl font-bold font-mono text-risk-high mt-1">{risk_score} / 100</div>
          <div className="mt-1">
            <RiskBadge band={risk_band} size="sm" />
          </div>
        </div>
      </div>

      {/* Required Caveat Badge (Contract Screen 3) */}
      <div className="p-2.5 bg-amber-500/15 border border-amber-500/30 rounded-xl text-amber-300 flex items-start gap-2">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-[11px] leading-snug">
          <span className="font-bold uppercase tracking-wider text-[10px] block text-amber-400">
            {t('simdiff.caveat')}
          </span>
          {simulationResult.caveat || 'Counterfactual only — single-feature override breaks correlations. Causal questions use the threshold engine.'}
        </div>
      </div>

      {/* Explanation Text */}
      <p className="text-[11px] text-mine-text leading-relaxed">
        {explanationText}
      </p>

      {/* Dynamic SHAP Preview */}
      <div className="space-y-1 pt-1">
        <div className="text-[10px] uppercase font-bold text-mine-muted">
          {t('simdiff.drivers')}
        </div>
        <div className="grid grid-cols-2 gap-1.5">
          {shap.slice(0, 2).map((s) => (
            <div
              key={s.feature}
              className="p-1.5 bg-mine-darker rounded border border-mine-border text-[11px] flex justify-between"
            >
              <span className="text-mine-text truncate">{s.feature.split('(')[0]}</span>
              <span className={`font-mono font-bold ${s.value >= 0 ? 'text-risk-high' : 'text-risk-verylow'}`}>
                {s.value >= 0 ? '+' : ''}{s.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
