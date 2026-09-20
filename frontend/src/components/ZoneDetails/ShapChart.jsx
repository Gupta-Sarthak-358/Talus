import React from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { HelpCircle, Info, Sparkles } from 'lucide-react';

export default function ShapChart({ shap = [], baseRisk = null, currentRisk = 82, zoneName = 'Zone B', provenance = 'unknown' }) {
  const { t } = useTalusContext();
  if (!shap || shap.length === 0) {
    // While SHAP service wakes (cold start ~15s), show retrying — not empty error.
    return (
      <div className="p-4 bg-mine-darker rounded-xl border border-mine-border text-center text-xs text-mine-muted">
        <span className="inline-flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" /> Waking explanation service — retrying…</span>
      </div>
    );
  }

  // Find maximum value to scale horizontal bars proportionally
  const maxValue = Math.max(...shap.map((s) => s.value), 20);

  return (
    <div className="bg-mine-darker border border-mine-border rounded-xl p-4 shadow-sm space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-talus-600" />
          <h4 className="text-xs font-bold text-mine-text uppercase tracking-wider">
            {t('shap.title')}
          </h4>
        </div>
        <div className="text-[10px] text-mine-muted font-mono">
          {t('shap.base')} <span className="text-mine-text font-bold">{baseRisk ?? '—'}</span> {t('shap.current')} <span className="text-risk-high font-bold">{currentRisk}</span>
          <span className={`ml-1.5 px-1 py-px rounded border text-[9px] font-bold ${provenance === 'live' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' : 'bg-amber-500/10 text-amber-400 border-amber-500/30'}`}>
            {provenance === 'live' ? 'LIVE TreeSHAP' : provenance === 'fixture' ? 'FIXTURE attribution' : 'SHAP'}
          </span>
        </div>
      </div>

      <p className="text-[11px] text-mine-muted leading-relaxed">
        Feature contribution breakdown identifying primary geotechnical and environmental drivers:
      </p>

      {/* Horizontal Bar Chart */}
      <div className="space-y-2.5 pt-1">
        {shap.map((item, index) => {
          const barWidth = Math.min(100, Math.max(8, (item.value / maxValue) * 100));
          const isTopDriver = index === 0;

          return (
            <div key={item.feature} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1.5 font-medium text-mine-text">
                  <span className={`w-1.5 h-1.5 rounded-full ${isTopDriver ? 'bg-risk-high animate-pulse' : 'bg-talus-600'}`}></span>
                  <span className="truncate max-w-[180px] sm:max-w-none">{item.feature}</span>
                </div>
                <div className="flex items-center gap-2 font-mono shrink-0">
                  {item.rawValue && (
                    <span className="text-[10px] text-mine-muted bg-mine-card px-1.5 py-0.5 rounded border border-mine-border">
                      {item.rawValue}
                    </span>
                  )}
                  <span className={`font-bold ${item.value > 12 ? 'text-risk-high' : 'text-talus-600'}`}>
                    +{item.value}
                  </span>
                </div>
              </div>

              {/* Bar track */}
              <div className="w-full h-2 bg-mine-dark rounded-full overflow-hidden p-0.5 border border-mine-border">
                <div
                  className={`h-full rounded-full transition-all duration-700 ease-out ${
                    item.value > 12
                      ? 'bg-risk-high'
                      : index === 0
                      ? 'bg-talus-600'
                      : index === 1
                      ? 'bg-talus-500'
                      : 'bg-talus-400'
                  }`}
                  style={{ width: `${barWidth}%` }}
                ></div>
              </div>

              {item.description && (
                <div className="text-[10px] text-mine-muted pl-3">
                  {item.description}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Explanation Footnote */}
      <div className="p-2 bg-mine-card border border-mine-border rounded-lg text-[10px] text-mine-text flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-talus-600 shrink-0 mt-0.5" />
        <span>
          Non-linear interaction: Rainfall infiltration increases pore-water pressure, amplifying crack density sensitivity along steep slope shear planes.
        </span>
      </div>
    </div>
  );
}
