import React from 'react';
import RiskBadge from '../Common/RiskBadge';
import { ShieldCheck, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function RiskScoreGauge({ score = 0, band = 'LOW', confidence = 85, trend = {}, isSimulated = false }) {
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

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl p-4 shadow-sm space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-[11px] font-semibold text-mine-muted uppercase tracking-wider flex items-center gap-1.5">
            <span>Risk Score & Operational Band</span>
            {isSimulated && (
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-risk-moderate/20 text-mine-text border border-risk-moderate/40 animate-pulse">
                SIMULATED
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
            <span className={trendColor}>{trend.badge || 'Stable'}</span>
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

      {/* Model Confidence & Telemetry Reliability */}
      <div className="flex items-center justify-between pt-2 border-t border-mine-border text-xs">
        <div className="flex items-center gap-1.5 text-mine-muted">
          <ShieldCheck className="w-3.5 h-3.5 text-talus-600" />
          <span>Model Confidence:</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-16 h-1.5 bg-mine-dark rounded-full overflow-hidden">
            <div
              className="h-full bg-talus-600 rounded-full"
              style={{ width: `${confidence}%` }}
            ></div>
          </div>
          <span className="font-mono font-bold text-mine-text">{confidence}%</span>
        </div>
      </div>
    </div>
  );
}
