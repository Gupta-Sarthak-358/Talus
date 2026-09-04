import React from 'react';
import { useTalusContext } from '../context/TalusContext';
import { Link } from 'react-router-dom';
import RiskSummaryCards from '../components/RiskSummary/RiskSummaryCards';
import QuickStatsBar from '../components/RiskSummary/QuickStatsBar';
import RoadStatusCard from '../components/Routing/RoadStatusCard';
import { Map, FileText, FlaskConical, Navigation, ArrowRight, ShieldAlert } from 'lucide-react';

export default function Overview() {
  const { zones, locationData, t } = useTalusContext();
  const critical = zones.filter(z => z.risk_band === 'CRITICAL');
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <RiskSummaryCards />
      <QuickStatsBar />
      {/* Corridor picker + quick nav */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="lg:col-span-2 bg-mine-card border border-mine-border rounded-2xl p-4">
          <h3 className="text-xs font-bold text-mine-text uppercase tracking-wider flex items-center gap-1.5">
            <Map className="w-3.5 h-3.5 text-talus-600" />
            Active Corridor — {locationData.label}
          </h3>
          <p className="text-[11px] text-mine-muted mt-1">Click GIS Map to inspect slopes, or jump to Reports/Lab/Routes. Zones: {zones.map(z=>`${z.id} ${z.risk_score}`).join(' · ')}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link to="/map" className="px-3 py-1.5 bg-talus-600 hover:bg-talus-500 text-white rounded-lg text-xs font-bold flex items-center gap-1">Open GIS Map <ArrowRight className="w-3 h-3" /></Link>
            <Link to="/reports" className="px-3 py-1.5 bg-mine-darker hover:bg-mine-dark border border-mine-border rounded-lg text-xs font-semibold flex items-center gap-1"><FileText className="w-3 h-3" /> Reports</Link>
            <Link to="/lab" className="px-3 py-1.5 bg-mine-darker hover:bg-mine-dark border border-mine-border rounded-lg text-xs font-semibold flex items-center gap-1"><FlaskConical className="w-3 h-3" /> Scenario Lab</Link>
            <Link to="/routes" className="px-3 py-1.5 bg-mine-darker hover:bg-mine-dark border border-mine-border rounded-lg text-xs font-semibold flex items-center gap-1"><Navigation className="w-3 h-3" /> Routes</Link>
          </div>
          {critical.length > 0 && (
            <div className="mt-3 p-2 bg-risk-critical/10 border border-risk-critical/30 rounded-lg text-xs flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-risk-critical" />
              <span className="text-risk-critical font-bold">{critical.map(z=>z.id).join(', ')} — {t('alerts.critical')} — inspect on GIS Map</span>
            </div>
          )}
        </div>
        <div className="bg-mine-darker border border-mine-border rounded-2xl p-4">
          <h4 className="text-xs font-bold text-mine-text">How to demo (URL-shareable)</h4>
          <ul className="mt-2 space-y-1 text-[11px] text-mine-muted list-disc pl-4">
            <li><code className="font-mono">/map?zone=S1&lang=ne</code> — share S1 Nepali view</li>
            <li><code className="font-mono">/reports</code> — POST /api/reports demo</li>
            <li><code className="font-mono">/lab</code> — ML vs Causal What-If</li>
            <li><code className="font-mono">/routes</code> — R2 avoidance proof</li>
          </ul>
          <p className="mt-2 text-[11px] text-mine-muted">All screens use <code className="font-mono">useTalusContext</code> (formerly MineContext) + <code>LOCATIONS</code>.</p>
        </div>
      </div>
      <RoadStatusCard />
    </main>
  );
}
