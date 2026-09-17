import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/api';
import { LOCATIONS } from '../../data/locations';

const CORRIDORS = ['gangtok', 'lachung', 'darjeeling'];

export default function CorridorComparison() {
  const [rows, setRows] = useState(null);
  useEffect(() => {
    let stop = false;
    Promise.all(
      CORRIDORS.map(async (loc) => {
        try {
          const ws = await apiRequest(`/warning/state?location=${loc}`);
          const iso = await apiRequest(`/isolation?location=${loc}`).catch(() => null);
          return { loc, state: ws.corridor_state, zone: ws.corridor_zone, isolated: iso?.corridor_isolated || false };
        } catch {
          return { loc, state: '—', zone: '—', isolated: false };
        }
      })
    ).then((r) => !stop && setRows(r));
    return () => { stop = true; };
  }, []);

  if (!rows) return null;
  return (
    <div className="bg-white border-2 border-zinc-200 rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-zinc-900 text-white flex items-center justify-between">
        <span className="text-xs font-black tracking-wide">Corridor Triage — 3 live, 5 pending</span>
        <span className="text-[11px] text-zinc-300">Gangtok · Lachung · Darjeeling · +5 NER states</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-zinc-200">
        {(rows||[]).map((r) => {
          const loc = LOCATIONS[r.loc] || { label: r.loc, zones: [], badge: '' };
          return (
            <div key={r.loc} className="p-4 space-y-1">
              <div className="text-xs font-black text-zinc-900">{loc.label}</div>
              <div className="text-[11px] text-zinc-600">{(loc.zones||[]).length} slopes · {loc.badge}</div>
              <div className={`inline-flex px-2 py-1 rounded-lg text-xs font-black border ${r.state === 'CRITICAL' || r.state === 'EVACUATE' || r.state === 'RESTRICT' ? 'bg-red-600 text-white border-red-700' : r.state === 'ALERT' ? 'bg-amber-400 text-zinc-900 border-amber-500' : 'bg-emerald-600 text-white border-emerald-700'}`}>
                {r.state} {r.zone && `· ${r.zone}`} {r.isolated && '· ISOLATED'}
              </div>
            </div>
          );
        })}
      </div>
      <div className="px-4 py-2 bg-zinc-50 border-t border-zinc-200 flex gap-4 text-[11px] text-zinc-600">
        <span>Arunachal: No data — NGEN pending</span>
        <span className="hidden sm:inline">Assam Hills: pending</span>
        <span className="hidden sm:inline">Meghalaya/Manipur/Mizoram: pending honest</span>
      </div>
    </div>
  );
}
