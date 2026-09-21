import React, { useEffect, useState } from 'react';
import { Siren, ChevronRight } from 'lucide-react';
import { apiRequest } from '../../services/api';
import { useTalusContext } from '../../context/TalusContext';

const STATE_STYLE = {
  NORMAL: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  WATCH: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
  ALERT: 'bg-orange-500/15 text-orange-300 border-orange-500/30',
  CRITICAL: 'bg-red-500/15 text-red-300 border-red-500/30',
  RESTRICT: 'bg-amber-600/20 text-amber-200 border-amber-500/40',
  EVACUATE: 'bg-red-700/30 text-red-100 border-red-600/50 animate-pulse',
};

/**
 * Warning state machine (NORMAL → WATCH → ALERT → CRITICAL), live from
 * GET /api/warning/state. Every state carries its reasons + the officer
 * action — the card answers "what is the warning and why", never just a %.
 */
export default function WarningStateCard() {
  const { activeLocation } = useTalusContext();
  const [data, setData] = useState(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    let stop = false;
    apiRequest(`/warning/state?location=${encodeURIComponent(activeLocation)}`)
      .then((d) => { if (!stop) { setData(d); setOffline(false); } })
      .catch(() => { if (!stop) setOffline(true); });
    return () => { stop = true; };
  }, [activeLocation]);

  if (offline || !data) {
    if (!data) return null;
    return (
      <div className="bg-mine-darker border border-mine-border rounded-xl px-4 py-2 text-xs text-mine-muted">
        Warning states unreachable — backend offline.
      </div>
    );
  }

  return (
    <div className="bg-mine-card border border-mine-border rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-mine-darker border-b border-mine-border flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Siren className="w-4 h-4 text-red-300" />
          <span className="text-xs font-bold text-mine-text">{t('warning.corridorTitle')}</span>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-mine-muted">
          <span>highest:</span>
          <span className={`font-bold px-2 py-0.5 rounded-full border ${STATE_STYLE[data.corridor_state]}`}>
            {data.corridor_state} · {data.corridor_zone}
          </span>
        </div>
      </div>
      <div className="divide-y divide-mine-border/50">
        {data.states.map((s) => (
          <div key={s.zone_id} className="px-4 py-2.5 flex items-start gap-3">
            <div className="flex flex-col gap-1 shrink-0">
              <span className={`mt-0.5 text-[10px] font-bold px-2 py-0.5 rounded-full border whitespace-nowrap ${STATE_STYLE[s.state]}`}>
                {s.zone_id} · {s.state}
              </span>
              {s.ood && (
                <span
                  className="text-[9px] font-bold px-2 py-0.5 rounded-full border whitespace-nowrap bg-violet-500/15 text-violet-300 border-violet-500/40"
                  title={(s.ood_reasons || []).join('; ') || 'Outside validated terrain support'}
                >
                  OOD — caution, not confirmed low risk
                </span>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-[11px] text-mine-muted">
                {s.reasons.join(' · ')}
              </div>
              <div className="text-[11px] text-mine-text mt-0.5 flex items-start gap-1">
                <ChevronRight className="w-3 h-3 mt-0.5 shrink-0 text-talus-600" />
                <span><strong>Action ({s.action.priority}):</strong> {s.action.message}</span>
              </div>
            </div>
            <span className="text-[11px] font-mono text-mine-muted whitespace-nowrap">{s.score}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
