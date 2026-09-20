import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/api';
import { Grid3x3, Download } from 'lucide-react';

const PAGE_SIZE = 8;

export default function PanchayatTiles() {
  const [tiles, setTiles] = useState(null);
  const [failed, setFailed] = useState(false);
  const [page, setPage] = useState(0);
  useEffect(() => {
    let stop = false;
    apiRequest('/panchayat/tiles').then((d) => { if (!stop) { setTiles(d.tiles || []); setFailed(false); } }).catch(() => { if (!stop) { setTiles([]); setFailed(true); } });
    return () => { stop = true; };
  }, []);
  if (!tiles) return null;
  if (failed && tiles.length === 0) {
    return (
      <div className="bg-white border-2 border-zinc-200 rounded-2xl p-4 text-xs text-zinc-600">
        Panchayat tiles unavailable — backend offline.
        <button onClick={() => window.location.reload()} className="ml-2 px-2 py-1 bg-zinc-900 text-white rounded-lg text-[11px] font-bold focus-visible:ring-2">Retry</button>
      </div>
    );
  }
  const totalPages = Math.max(1, Math.ceil(tiles.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const visible = tiles.slice(safePage * PAGE_SIZE, safePage * PAGE_SIZE + PAGE_SIZE);
  return (
    <div className="bg-white border-2 border-zinc-200 rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-zinc-900 text-white flex items-center justify-between flex-wrap gap-2">
        <span className="text-xs font-black flex items-center gap-1.5"><Grid3x3 className="w-4 h-4" /> Panchayat Tiles — {tiles.length} scored, {visible.length} shown</span>
        <span className="flex items-center gap-2">
          <span className="text-[11px] text-zinc-300 font-mono">p.{safePage + 1}/{totalPages}</span>
          <a href="/data/sih26001/processed/feature_matrix.panchayat.csv" className="text-[11px] font-bold text-white hover:text-zinc-200 flex items-center gap-1 focus-visible:ring-2"><Download className="w-3 h-3" /> CSV</a>
        </span>
      </div>
      <div className="p-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
        {visible.map((t) => {
          const band = String(t.band || '').toUpperCase();
          return (
            <div key={t.zone_id} className={`p-2 rounded-xl border text-center ${band === 'CRITICAL' ? 'bg-red-50 border-red-200' : band === 'HIGH' ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'}`}>
              <div className="font-mono font-black text-xs text-zinc-900">{t.zone_id}</div>
              <div className="text-[11px] font-bold text-zinc-700">{t.risk_score} {t.band}</div>
              <div className="text-[10px] text-zinc-500">{t.elevation}m · {t.slope_angle}°</div>
            </div>
          );
        })}
      </div>
      <div className="px-4 py-2 bg-zinc-50 border-t border-zinc-200 flex items-center justify-between gap-2">
        <span className="text-[11px] text-zinc-600">Scored via same sih26001_rf_v1; frozen 12-slope sample untouched. Full {tiles.length} at GET /api/panchayat/tiles.</span>
        <span className="flex gap-1 shrink-0">
          <button disabled={safePage === 0} onClick={() => setPage((p) => Math.max(0, p - 1))} aria-label="Previous panchayat page" className="px-2 py-1 rounded-lg border border-zinc-300 text-[11px] font-bold disabled:opacity-40 focus-visible:ring-2">Prev</button>
          <button disabled={safePage >= totalPages - 1} onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} aria-label="Next panchayat page" className="px-2 py-1 rounded-lg border border-zinc-300 text-[11px] font-bold disabled:opacity-40 focus-visible:ring-2">Next</button>
        </span>
      </div>
    </div>
  );
}
