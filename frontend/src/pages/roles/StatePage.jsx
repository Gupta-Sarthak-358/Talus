import React, { useEffect } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskSummaryCards from '../../components/RiskSummary/RiskSummaryCards';
import QuickStatsBar from '../../components/RiskSummary/QuickStatsBar';
import { Link } from 'react-router-dom';
import { Sliders, Navigation } from 'lucide-react';

export default function StatePage() {
  const { setRole, zones } = useTalusContext();
  useEffect(() => setRole('state_manager'), []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-mine-darker border border-mine-border rounded-xl px-4 py-2 flex items-center justify-between text-xs">
        <span className="font-bold text-mine-text">State Disaster Manager (SSDMA) — Triage across corridors</span>
        <span className="text-mine-muted">{zones.length} slopes · Gangtok/Lachung/Darjeeling</span>
      </div>
      <RiskSummaryCards />
      <QuickStatsBar />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <Link to="/lab" className="p-4 bg-mine-card border border-mine-border rounded-2xl hover:border-talus-500 flex items-center gap-3">
          <Sliders className="w-5 h-5 text-talus-600" />
          <div><div className="text-xs font-bold text-mine-text">Simulate Monsoon & Causal Replay</div><div className="text-[11px] text-mine-muted">Monga/Dahal thresholds across all corridors</div></div>
        </Link>
        <Link to="/routes" className="p-4 bg-mine-card border border-mine-border rounded-2xl hover:border-talus-500 flex items-center gap-3">
          <Navigation className="w-5 h-5 text-risk-verylow" />
          <div><div className="text-xs font-bold text-mine-text">Corridor Routing — R2 Avoidance</div><div className="text-[11px] text-mine-muted">S1→S4 4.8km via R2 (89) vs 6.2km via R3+R4 (66)</div></div>
        </Link>
      </div>
    </main>
  );
}
