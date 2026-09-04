import React, { useEffect } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskSummaryCards from '../../components/RiskSummary/RiskSummaryCards';
import QuickStatsBar from '../../components/RiskSummary/QuickStatsBar';
import { Link } from 'react-router-dom';
import { Sliders, Navigation } from 'lucide-react';

export default function StatePage() {
  const { setRole, zones, t } = useTalusContext();
  useEffect(() => setRole('state_manager'), []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-mine-darker border border-mine-border rounded-xl px-4 py-2 flex items-center justify-between text-xs">
        <span className="font-bold text-mine-text">{t('state.title')}</span>
        <span className="text-mine-muted">{zones.length} slopes · {t('state.corridors')}</span>
      </div>
      <RiskSummaryCards />
      <QuickStatsBar />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Link to="/lab" className="p-4 bg-mine-card border border-mine-border rounded-2xl hover:border-talus-500 flex items-center gap-3">
          <Sliders className="w-5 h-5 text-talus-600" />
          <div><div className="text-xs font-bold text-mine-text">{t('state.sim_t')}</div><div className="text-[11px] text-mine-muted">{t('state.sim_d')}</div></div>
        </Link>
        <Link to="/routes" className="p-4 bg-mine-card border border-mine-border rounded-2xl hover:border-talus-500 flex items-center gap-3">
          <Navigation className="w-5 h-5 text-risk-verylow" />
          <div><div className="text-xs font-bold text-mine-text">{t('state.route_t')}</div><div className="text-[11px] text-mine-muted">{t('state.route_d')}</div></div>
        </Link>
      </div>
    </main>
  );
}
