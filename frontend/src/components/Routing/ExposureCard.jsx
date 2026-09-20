import React, { useEffect, useState } from 'react';
import { TriangleAlert } from 'lucide-react';
import { apiRequest } from '../../services/api';

/**
 * Hazard ≠ risk: for each zone, what a modeled failure would threaten —
 * OSM buildings and road meters in the screening runout path, plus the
 * nearest road segment. Numbers from GET /api/runout/exposure, labeled
 * screening approximation, never observed damage.
 */
export default function ExposureCard() {
  const [zones, setZones] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let stop = false;
    const load = async () => {
      try {
        const b = await apiRequest('/runout/exposure');
        const raw = b.zones || null;
        if (!raw) { if (!stop) setZones(null); return; }
        // Operational-risk delta per zone — triage by consequence-amplified risk, not raw building count.
        const ids = Object.keys(raw).slice(0, 8);
        const deltas = {};
        await Promise.all(ids.map(async (id) => {
          try {
            const e = await apiRequest(`/zones/${id}/exposure`).catch(() => null);
            deltas[id] = e?.operational_risk?.delta ?? 0;
          } catch { deltas[id] = 0; }
        }));
        if (!stop) { setZones(raw); setFailed(false); }
        // stash deltas on the bundle for ranking below
        if (!stop) setZones(Object.fromEntries(Object.entries(raw).map(([id, z]) => [id, { ...z, _opDelta: deltas[id] ?? 0 }])));
      } catch { if (!stop) { setZones(null); setFailed(true); } }
    };
    load();
    return () => { stop = true; };
  }, []);

  if (!zones) {
    if (failed) return <div className="bg-white border-2 border-zinc-200 rounded-2xl p-4 text-xs text-zinc-600">Exposure unavailable — backend offline.</div>;
    return null;
  }
  const ranked = Object.entries(zones)
    .map(([id, z]) => ({ id, ...z }))
    .sort((a, b) => ((b._opDelta ?? 0) - (a._opDelta ?? 0)) || (b.buildings_n - a.buildings_n))
    .slice(0, 4);
  const worst = ranked[0];
  if (!worst) return null;

  return (
    <div className="bg-white border-2 border-zinc-200 rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-zinc-900 text-white flex items-center gap-2">
        <TriangleAlert className="w-4 h-4" />
        <span className="text-xs font-black">If it fails — who gets hit? (Recommended staging)</span>
      </div>
      <div className="px-4 py-3">
        <p className="text-[11px] text-zinc-700">
          Worst modeled case: <strong>{worst.id}</strong> threatens{' '}
          <strong>~{worst.buildings_n} buildings</strong>
          {worst._opDelta != null && <span> · operational risk Δ+{worst._opDelta}</span>}
          {worst.nearest_road_seg && (
            <span> · nearest road {worst.nearest_road_seg} ({worst.nearest_road_m}m)</span>
          )}.
        </p>
        <div className="mt-2 space-y-1">
          {ranked.map((z) => (
            <div key={z.id} className="flex items-center justify-between text-[11px] font-mono text-zinc-600">
              <span>{z.id} · {z.length_m}m path</span>
              <span>~{z.buildings_n} bldg · {Object.values(z.road_m || {}).reduce((a, b) => a + b, 0)}m road{ z._opDelta ? ` · Δ+${z._opDelta}` : ''}</span>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-zinc-500 mt-2">
          Screening approximation (steepest-descent on SRTM, 100m band, cap 400/zone).
          Modeled risk only — final staging with qualified personnel.
        </p>
      </div>
    </div>
  );
}
