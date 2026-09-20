import React, { useEffect, useState } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import { apiRequest } from '../../services/api';
import RiskSummaryCards from '../../components/RiskSummary/RiskSummaryCards';
import QuickStatsBar from '../../components/RiskSummary/QuickStatsBar';
import TrustLedgerCard from '../../components/Alerts/TrustLedgerCard';
import CorridorComparison from '../../components/Management/CorridorComparison';
import PanchayatTiles from '../../components/Management/PanchayatTiles';
import { Link } from 'react-router-dom';
import { Sliders, Navigation, Download } from 'lucide-react';

/**
 * State triage — cross-corridor ops (8 corridors, 32 zones).
 * Corridor matrix first (<5s triage, exposure-sorted), then panchayat 100 paginated, then trust ledger.
 * Never shows villager hero or district queue; villager never sees trust/exposure details.
 */
export default function StatePage() {
  const { setRole, zones, scoringMode, t } = useTalusContext();
  const liveZones = zones || [];
  const [exporting, setExporting] = useState(false);
  useEffect(() => setRole('state_manager'), []);
  const exportPanchayat = async () => {
    setExporting(true);
    try {
      const d = await apiRequest('/panchayat/tiles');
      const blob = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'panchayat_tiles.json'; a.click();
      URL.revokeObjectURL(url);
    } catch { /* ErrorState lives in PanchayatTiles — export stays silent, never invented */ }
    finally { setExporting(false); }
  };
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-zinc-900 text-white rounded-xl px-4 py-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="font-black text-sm tracking-wide">{t('state.title')}</div>
          <div className="text-xs text-zinc-300 font-mono">{liveZones.length} slopes · {t('state.corridors')} · {scoringMode === 'live-rf' ? t('quick.liveModel') : t('quick.frozenModel')}</div>
        </div>
        <button onClick={exportPanchayat} disabled={exporting} aria-label="Export panchayat tiles live" className="px-3 py-2 bg-white text-zinc-900 rounded-xl text-xs font-black flex items-center gap-1.5 focus-visible:ring-2 disabled:opacity-60">
          <Download className="w-4 h-4" /> {exporting ? 'Exporting…' : 'Export Panchayat JSON'}
        </button>
      </div>

      {/* Management: corridor matrix first — senior wants <5s cross-corridor triage */}
      <CorridorComparison />

      <RiskSummaryCards />
      <QuickStatsBar />
      <PanchayatTiles />
      <TrustLedgerCard />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Link to="/lab" className="p-4 bg-white border-2 border-zinc-200 rounded-2xl hover:border-zinc-900 flex items-center gap-3 focus-visible:ring-2">
          <Sliders className="w-5 h-5 text-zinc-700" />
          <div><div className="text-xs font-black text-zinc-900">{t('state.sim_t')}</div><div className="text-[11px] text-zinc-600">{t('state.sim_d')}</div></div>
        </Link>
        <Link to="/routes" className="p-4 bg-white border-2 border-zinc-200 rounded-2xl hover:border-zinc-900 flex items-center gap-3 focus-visible:ring-2">
          <Navigation className="w-5 h-5 text-emerald-700" />
          <div><div className="text-xs font-black text-zinc-900">{t('state.route_t')}</div><div className="text-[11px] text-zinc-600">{t('state.route_d')}</div></div>
        </Link>
      </div>
    </main>
  );
}
