import React from 'react';
import RiskBadge from '../Common/RiskBadge';
import { ShieldCheck, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';

import { useTalusContext } from '../../context/TalusContext';
export default function RiskScoreGauge({ score = 0, band = 'LOW', confidence = 85, trend = {}, isSimulated = false }) {
  const { role, t } = useTalusContext();
  const isVillager = role === 'villager';
  const rawHigh = t('confidence.high');
  const rawMed = t('confidence.medium');
  const rawLow = t('confidence.low');
  const confidenceLabel = confidence >= 75 ? (rawHigh === 'confidence.high' ? 'High certainty' : rawHigh) : confidence >= 60 ? (rawMed === 'confidence.medium' ? 'Medium certainty' : rawMed) : (rawLow === 'confidence.low' ? 'Low certainty' : rawLow);
  const certaintyLabel = t('zone.certainty');
  const certaintyText = certaintyLabel === 'zone.certainty' ? 'Certainty:' : certaintyLabel;
  // Score color
  const getScoreColor = () => {
    if (score >= 85) return 'text-risk-critical';
    if (score >= 66) return 'text-risk-high';
    if (score >= 41) return 'text-risk-moderate';
    if (score >= 21) return 'text-risk-low';
    return 'text-risk-verylow';
  };

  const getProgressColor = () => {
    if (score >= 85) return 'bg-risk-critical';
    if (score >= 66) return 'bg-risk-high';
    if (score >= 41) return 'bg-risk-moderate';
    if (score >= 21) return 'bg-risk-low';
    return 'bg-risk-verylow';
  };

  const TrendIcon = trend.direction === 'rising' ? TrendingUp : trend.direction === 'falling' ? TrendingDown : Minus;
  const trendColor = trend.direction === 'rising' ? 'text-risk-critical' : trend.direction === 'falling' ? 'text-risk-verylow' : 'text-mine-muted';

  if (isVillager) {
    return (
      <div className="bg-mine-darker border border-mine-border rounded-xl p-4 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <RiskBadge band={band} size="lg" />
          {isSimulated && (
            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-risk-moderate/20 text-mine-text border border-risk-moderate/40 animate-pulse">
              SIMULATED
            </span>
          )}
          <span className="text-xs font-bold text-mine-text">{confidenceLabel}</span>
        </div>
        {/* Simple bar, no numbers */}
        <div className="w-full h-2.5 bg-mine-dark rounded-full overflow-hidden p-0.5 border border-mine-border">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${getProgressColor()}`}
            style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
          ></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl p-4 shadow-sm space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] font-semibold text-mine-muted uppercase tracking-wider flex items-center gap-1.5">
            <span>{t('zone.riskScore')}</span>
            {isSimulated && (
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-risk-moderate/20 text-mine-text border border-risk-moderate/40 animate-pulse">
                {t('zone.simulated')}
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-4xl font-extrabold font-mono tracking-tight ${getScoreColor()}`}>
              {score}
            </span>
            <span className="text-sm font-semibold text-mine-muted font-mono">/ 100</span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-1.5">
          <RiskBadge band={band} size="lg" />
          <div className="flex items-center gap-1 text-[11px] font-semibold font-mono">
            <TrendIcon className={`w-3.5 h-3.5 ${trendColor}`} />
            <span className={trendColor}>{trend.badge || t('trend.stable')}</span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="w-full h-2.5 bg-mine-dark rounded-full overflow-hidden p-0.5 border border-mine-border">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${getProgressColor()}`}
            style={{ width: `${Math.min(100, Math.max(5, score))}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-[9px] text-mine-muted font-mono px-0.5">
          <span>0 (Very Low)</span>
          <span>40 (Mod)</span>
          <span>65 (High)</span>
          <span>100 (Critical)</span>
        </div>
      </div>

      {/* Model Confidence — villager sees words, officer sees % + certainty */}
      <div className="flex items-center justify-between pt-2 border-t border-mine-border text-xs">
        <div className="flex items-center gap-1.5 text-mine-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-talus-600" />
          <span>{isVillager ? certaintyText : t('zone.confidence')}</span>
        </div>
        <div className="flex items-center gap-2">
          {!isVillager && (
            <div className="w-16 h-1.5 bg-mine-dark rounded-full overflow-hidden">
              <div className="h-full bg-talus-600 rounded-full" style={{ width: `${confidence}%` }}></div>
            </div>
          )}
          <span className={`font-bold ${isVillager ? 'text-mine-text text-xs' : 'font-mono text-mine-text'}`}>{isVillager ? confidenceLabel : `${confidence}%`}</span>
        </div>
      </div>
      {!isVillager && <div className="text-[10px] text-mine-muted font-mono pl-5">Calibrated (isotonic, Brier 0.10) — see Model Card</div>}
    </div>
  );
}
