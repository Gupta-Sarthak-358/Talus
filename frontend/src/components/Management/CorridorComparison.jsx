import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/api';
import { LOCATIONS } from '../../data/locations';

const CORRIDORS = ['gangtok', 'lachung', 'darjeeling', 'arunachal', 'assam', 'manipur', 'meghalaya', 'mizoram'];

export default function CorridorComparison() {
  const [rows, setRows] = useState(null);
  const [failed, setFailed] = useState(false);
  const [fetchedAt, setFetchedAt] = useState(null);
  useEffect(() => {
    let stop = false;
    const load = async () => {
      try {
        const out = await Promise.all(
          CORRIDORS.map(async (loc) => {
            try {
              const [ws, iso] = await Promise.all([
                apiRequest(`/warning/state?location=${loc}`),
                apiRequest(`/isolation?location=${loc}`).catch(() => null),
              ]);
              // Operational-risk delta for the corridor's highest-state zone — drives triage sort.
              // Falls back to 0 when exposure is unavailable (never blocks triage).
              let opDelta = 0;
              let opScore = null;
              if (ws.corridor_zone) {
                try {
                  const exp = await apiRequest(`/zones/${ws.corridor_zone}/exposure`).catch(() => null);
                  opDelta = exp?.operational_risk?.delta ?? 0;
                  opScore = exp?.operational_risk?.score ?? null;
                } catch { /* exposure optional — triage still live on warning+isolation */ }
              }
              return { loc, state: ws.corridor_state, zone: ws.corridor_zone, isolated: iso?.corridor_isolated || false, mayIsolate: iso?.corridor_may_isolate || false, support: ws.model_support || 'unknown', opDelta, opScore };
            } catch {
              return { loc, state: 'UNAVAILABLE', zone: '—', isolated: false, mayIsolate: false, support: 'unknown', opDelta: 0, opScore: null };
            }
          })
        );
        // Triage order: operational-risk delta desc, then EVACUATE/RESTRICT/CRITICAL first, then isolated.
        const rank = { EVACUATE: 5, RESTRICT: 4, CRITICAL: 3, ALERT: 2, WATCH: 1, NORMAL: 0, UNAVAILABLE: -1 };
        out.sort((a, b) => (b.opDelta - a.opDelta) || ((rank[b.state] ?? 0) - (rank[a.state] ?? 0)) || ((b.isolated ? 1 : 0) - (a.isolated ? 1 : 0)));
        if (!stop) { setRows(out); setFailed(false); setFetchedAt(Date.now()); }
      } catch {
        if (!stop) setFailed(true);
      }
    };
    load();
    return () => { stop = true; };
  }, []);

  if (failed && !rows) {
    return (
      <div className="bg-white border-2 border-zinc-200 rounded-2xl p-4 text-xs text-zinc-600">
        Corridor triage unavailable — backend offline.
        <button onClick={() => window.location.reload()} className="ml-2 px-2 py-1 bg-zinc-900 text-white rounded-lg text-[11px] font-bold focus-visible:ring-2">Retry</button>
      </div>
    );
  }
  if (!rows) return null;
  const stale = fetchedAt && (Date.now() - fetchedAt > 15 * 60 * 1000);
  return (
    <div className="bg-white border-2 border-zinc-200 rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-zinc-900 text-white flex items-center justify-between flex-wrap gap-2">
        <span className="text-xs font-black tracking-wide">Corridor Triage — 8 live · 3 validated-regime, 5 operational-inference</span>
        <span className="flex items-center gap-2 text-[11px] text-zinc-300">
          <span>Scores outside Sikkim/Darjeeling are live data, not calibrated validity</span>
          <span className={`px-1.5 py-0.5 rounded font-bold border ${stale ? 'bg-amber-500/20 text-amber-200 border-amber-500/40' : 'bg-emerald-500/20 text-emerald-200 border-emerald-500/40'}`}>{stale ? 'STALE' : 'LIVE'}</span>
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 divide-y sm:divide-y-0 sm:divide-x divide-zinc-200">
        {(rows||[]).map((r) => {
          const loc = LOCATIONS[r.loc] || { label: r.loc, zones: [], badge: '' };
          const validated = r.support === 'validated-regime';
          return (
            <div key={r.loc} className="p-4 space-y-1">
              <div className="text-xs font-black text-zinc-900">{loc.label}</div>
              <div className="text-[11px] text-zinc-600">{(loc.zones||[]).length} slopes · {loc.badge}</div>
              <div className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold border ${validated ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : 'bg-amber-100 text-amber-800 border-amber-300'}`}>
                {validated ? 'VALIDATED REGIME' : 'OPERATIONAL INFERENCE'}
              </div>
              <div className={`inline-flex px-2 py-1 rounded-lg text-xs font-black border focus-visible:ring-2 ${r.state === 'CRITICAL' || r.state === 'EVACUATE' || r.state === 'RESTRICT' ? 'bg-red-600 text-white border-red-700' : r.state === 'ALERT' ? 'bg-amber-400 text-zinc-900 border-amber-500' : r.state === 'UNAVAILABLE' ? 'bg-zinc-200 text-zinc-600 border-zinc-300' : 'bg-emerald-600 text-white border-emerald-700'}`}>
                {r.state} {r.zone && r.zone !== '—' && `· ${r.zone}`} {r.isolated && '· ISOLATED'} {r.mayIsolate && !r.isolated && '· MAY ISOLATE'}
              </div>
              <div className="text-[11px] text-zinc-600 font-mono">Operational risk {r.opScore != null ? `${r.opScore} (Δ+${r.opDelta})` : `Δ+${r.opDelta}`} · exposure-sorted</div>
            </div>
          );
        })}
      </div>
      <div className="px-4 py-2 bg-zinc-50 border-t border-zinc-200 flex gap-4 text-[11px] text-zinc-600">
        <span>Model trained + validated on Sikkim/Darjeeling geography only (2936 rows)</span>
        <span className="hidden sm:inline">AR/AS/MN/ML/MZ: same live pipeline, scores are operational inference</span>
      </div>
    </div>
  );
}
