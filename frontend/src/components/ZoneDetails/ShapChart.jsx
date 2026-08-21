import React from 'react';
import { HelpCircle, Info, Sparkles } from 'lucide-react';

export default function ShapChart({ shap = [], baseRisk = 15, currentRisk = 82, zoneName = 'Zone B' }) {
  if (!shap || shap.length === 0) {
    return (
      <div className="p-4 bg-mine-darker/60 rounded-xl border border-mine-border/60 text-center text-xs text-slate-400">
        No feature attribution explanation available for this zone.
      </div>
    );
  }

  // Find maximum value to scale horizontal bars proportionally
  const maxValue = Math.max(...shap.map((s) => s.value), 20);

  return (
    <div className="bg-mine-darker/90 border border-mine-border rounded-xl p-4 shadow-md space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-talus-400" />
          <h4 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
            Why is this Risk High? (SHAP Explanation)
          </h4>
        </div>
        <div className="text-[10px] text-slate-400 font-mono">
          Base: <span className="text-slate-300 font-bold">{baseRisk}</span> → Current: <span className="text-orange-400 font-bold">{currentRisk}</span>
        </div>
      </div>

      <p className="text-[11px] text-slate-400 leading-relaxed">
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
                <div className="flex items-center gap-1.5 font-medium text-slate-200">
                  <span className={`w-1.5 h-1.5 rounded-full ${isTopDriver ? 'bg-orange-400 animate-pulse' : 'bg-talus-400'}`}></span>
                  <span className="truncate max-w-[180px] sm:max-w-none">{item.feature}</span>
                </div>
                <div className="flex items-center gap-2 font-mono shrink-0">
                  {item.rawValue && (
                    <span className="text-[10px] text-slate-400 bg-mine-dark px-1.5 py-0.5 rounded border border-mine-border/50">
                      {item.rawValue}
                    </span>
                  )}
                  <span className={`font-bold ${item.value > 12 ? 'text-orange-400' : 'text-talus-300'}`}>
                    +{item.value}
                  </span>
                </div>
              </div>

              {/* Bar track */}
              <div className="w-full h-2 bg-mine-dark rounded-full overflow-hidden p-0.5 border border-mine-border/40">
                <div
                  className={`h-full rounded-full transition-all duration-700 ease-out ${
                    item.value > 12
                      ? 'bg-gradient-to-r from-orange-500 to-red-500'
                      : 'bg-gradient-to-r from-talus-500 to-indigo-500'
                  }`}
                  style={{ width: `${barWidth}%` }}
                ></div>
              </div>

              {item.description && (
                <div className="text-[10px] text-slate-400 pl-3">
                  {item.description}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Explanation Footnote */}
      <div className="p-2 bg-talus-950/30 border border-talus-500/20 rounded-lg text-[10px] text-slate-300 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-talus-400 shrink-0 mt-0.5" />
        <span>
          Non-linear interaction: Rainfall infiltration increases pore-water pressure, amplifying crack density sensitivity along steep slope shear planes.
        </span>
      </div>
    </div>
  );
}
