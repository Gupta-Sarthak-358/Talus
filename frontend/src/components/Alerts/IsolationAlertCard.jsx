import React, { useEffect, useState } from 'react';
import { AlertTriangle, ShieldAlert, Route, Radio } from 'lucide-react';
import { apiRequest } from '../../services/api';
import { useTalusContext } from '../../context/TalusContext';

export default function IsolationAlertCard() {
  const { activeLocation } = useTalusContext();
  const [iso, setIso] = useState(null);

  useEffect(() => {
    let stop = false;
    apiRequest(`/isolation?location=${encodeURIComponent(activeLocation)}`)
      .then((d) => { if (!stop) setIso(d); })
      .catch(() => { if (!stop) setIso(null); });
    return () => { stop = true; };
  }, [activeLocation]);

  if (!iso) return null;
  if (!iso.corridor_isolated && !iso.corridor_may_isolate) return null;

  const isBlocked = iso.corridor_isolated;
  return (
    <div className={`rounded-2xl border p-4 flex items-start gap-3 ${isBlocked ? 'bg-red-950/30 border-red-500/40' : 'bg-amber-950/20 border-amber-500/30'}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${isBlocked ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'}`}>
        {isBlocked ? <ShieldAlert className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
      </div>
      <div className="min-w-0 flex-1 space-y-1">
        <div className={`text-sm font-extrabold ${isBlocked ? 'text-red-300' : 'text-amber-300'}`}>
          {isBlocked ? `Isolation — ${iso.isolated_zones.join(', ')} cut off` : `May isolate — ${iso.at_risk_zones.join(', ')} at risk`}
        </div>
        <p className="text-xs text-mine-text leading-relaxed">
          {isBlocked
            ? `Only road to ${iso.isolated_zones.join(', ')} is blocked. No alternative. People in ${iso.isolated_zones.join(', ')} cannot reach the valley via ${iso.valley_hub}.`
            : `Single road left to ${iso.at_risk_zones.join(', ')} while risk is High/Critical. If that road blocks, the village will be isolated.`}
        </p>
        <p className="text-[11px] text-mine-muted">
          Bottleneck: R1 {iso.bottleneck.R1} · R2 {iso.bottleneck.R2} · R3 {iso.bottleneck.R3} · R4 {iso.bottleneck.R4}
        </p>
        {iso.action && (
          <p className="text-xs font-semibold text-mine-text bg-mine-darker border border-mine-border rounded-lg px-2.5 py-1.5 mt-1">
            <Route className="w-3 h-3 inline mr-1 text-talus-600" /> {iso.action}
          </p>
        )}
        <p className="text-[11px] text-mine-muted flex items-center gap-1">
          <Radio className="w-3 h-3" /> Alert sent to district & state authorities — response prioritized for isolated villages
        </p>
      </div>
    </div>
  );
}
