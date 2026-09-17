import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/api';
import { LOCATIONS } from '../../data/locations';

const CORRIDORS = ['gangtok', 'lachung', 'darjeeling', 'arunachal', 'assam', 'manipur', 'meghalaya', 'mizoram'];

export default function CorridorComparison() {
  const [rows, setRows] = useState(null);
  useEffect(() => {
    let stop = false;
    Promise.all(
      CORRIDORS.map(async (loc) => {
        try {
          const ws = await apiRequest(`/warning/state?location=${loc}`);
          const iso = await apiRequest(`/isolation?location=${loc}`).catch(() => null);
          return { loc, state: ws.corridor_state, zone: ws.corridor_zone, isolated: iso?.corridor_isolated || false, support: ws.model_support || 'unknown' };
        } catch {
          return { loc, state: '—', zone: '—', isolated: false, support: 'unknown' };
        }
      })
    ).then((r) => !stop && setRows(r));
    return () => { stop = true; };
  }, []);

  if (!rows) return null;
  return (
    <div className="bg-white border-2 border-zinc-200 rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-zinc-900 text-white flex items-center justify-between">
        <span className="text-xs font-black tracking-wide">Corridor Triage — 8 live · 3 validated-regime, 5 operational-inference</span>
        <span className="text-[11px] text-zinc-300">Scores outside Sikkim/Darjeeling are live data, not calibrated validity</span>
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
              <div className={`inline-flex px-2 py-1 rounded-lg text-xs font-black border ${r.state === 'CRITICAL' || r.state === 'EVACUATE' || r.state === 'RESTRICT' ? 'bg-red-600 text-white border-red-700' : r.state === 'ALERT' ? 'bg-amber-400 text-zinc-900 border-amber-500' : 'bg-emerald-600 text-white border-emerald-700'}`}>
                {r.state} {r.zone && `· ${r.zone}`} {r.isolated && '· ISOLATED'}
              </div>
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
