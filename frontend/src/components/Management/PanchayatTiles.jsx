import React, { useEffect, useState } from 'react';
import { apiRequest } from '../../services/api';
import { Grid3x3, Download } from 'lucide-react';

export default function PanchayatTiles() {
  const [tiles, setTiles] = useState(null);
  useEffect(() => {
    let stop = false;
    apiRequest('/panchayat/tiles').then((d) => !stop && setTiles(d.tiles?.slice(0, 12) || [])).catch(() => !stop && setTiles([]));
    return () => { stop = true; };
  }, []);
  if (!tiles) return null;
  return (
    <div className="bg-white border-2 border-zinc-200 rounded-2xl overflow-hidden">
      <div className="px-4 py-2.5 bg-zinc-900 text-white flex items-center justify-between">
        <span className="text-xs font-black flex items-center gap-1.5"><Grid3x3 className="w-4 h-4" /> Panchayat Tiles — 100 scored, 12 preview</span>
        <a href="/data/sih26001/processed/feature_matrix.panchayat.csv" className="text-[11px] font-bold text-white hover:text-zinc-200 flex items-center gap-1"><Download className="w-3 h-3" /> CSV</a>
      </div>
      <div className="p-3 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2">
        {(tiles||[]).map((t) => (
          <div key={t.zone_id} className={`p-2 rounded-xl border text-center ${t.band === 'Critical' ? 'bg-red-50 border-red-200' : t.band === 'High' ? 'bg-amber-50 border-amber-200' : 'bg-emerald-50 border-emerald-200'}`}>
            <div className="font-mono font-black text-xs text-zinc-900">{t.zone_id}</div>
            <div className="text-[11px] font-bold text-zinc-700">{t.risk_score} {t.band}</div>
            <div className="text-[10px] text-zinc-500">{t.elevation}m · {t.slope_angle}°</div>
          </div>
        ))}
      </div>
      <div className="px-4 py-2 bg-zinc-50 text-[11px] text-zinc-600 border-t border-zinc-200">Scored via same sih26001_rf_v1; frozen 12-slope sample untouched per scaffold. Full 100 at GET /api/panchayat/tiles.</div>
    </div>
  );
}
