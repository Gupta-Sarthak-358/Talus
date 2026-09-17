import React, { useEffect, useState } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskMap from '../../components/RiskMap/RiskMap';
import ZoneIntelligencePanel from '../../components/ZoneDetails/ZoneIntelligencePanel';
import RoadStatusCard from '../../components/Routing/RoadStatusCard';
import WarningStateCard from '../../components/Alerts/WarningStateCard';
import IsolationAlertCard from '../../components/Alerts/IsolationAlertCard';
import OpsQueuePreview from '../../components/Ops/OpsQueuePreview';
import { FileText, Bell } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * Ops console — senior wants split state: warning/isolation sticky top, map 60% + intel/queue tabs 40%, road bottom.
 * District never sees villager hero; villager never sees queue SHAP.
 */
export default function DistrictPage() {
  const { setRole, zones = [], reports = [], t } = useTalusContext();
  const safeReports = reports || [];
  const safeZones = zones || [];
  const [tab, setTab] = useState('intel'); // intel | queue | road
  useEffect(() => setRole('district_officer'), []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-zinc-900 text-white rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span className="font-black tracking-wide">{t('role.district_officer')} — {t('district.closure')}</span>
        <span className="text-zinc-300 font-mono">{safeZones.length} slopes · {t('district.sub')}</span>
      </div>

      <div className="flex gap-2">
        <Link to="/reports" className="flex-1 py-2.5 bg-zinc-900 hover:bg-black text-white rounded-xl text-xs font-black text-center flex items-center justify-center gap-1.5 focus-visible:ring-2"><FileText className="w-4 h-4" /> {t('district.review_queue')} — {safeReports.length}</Link>
        <button onClick={() => document.getElementById('ops-alerts')?.scrollIntoView({ behavior: 'smooth' })} className="px-4 py-2.5 bg-white border-2 border-zinc-900 text-zinc-900 rounded-xl text-xs font-black flex items-center gap-1.5"><Bell className="w-4 h-4" /> {t('district.multilang')}</button>
      </div>

      {/* Sticky command bar — ops wants always visible */}
      <div className="ops-sticky-top space-y-3 bg-mine-darkest/95 backdrop-blur py-2 -mx-3 px-3 sm:mx-0 sm:px-0 sm:bg-transparent sm:backdrop-blur-none sm:static">
        <IsolationAlertCard />
        <WarningStateCard />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <div className="lg:col-span-7 xl:col-span-7 h-[640px] lg:sticky lg:top-[88px] order-2 lg:order-1 border-2 border-zinc-200 rounded-2xl overflow-hidden">
          <RiskMap />
        </div>
        <div className="lg:col-span-5 xl:col-span-5 space-y-3 order-1 lg:order-2">
          <div className="bg-white border-2 border-zinc-200 rounded-2xl p-1 flex gap-1">
            {[
              ['intel', 'Intel'],
              ['queue', `Queue ${safeReports.filter((r) => r.status === 'flagged').length ? `· ${safeReports.filter((r) => r.status === 'flagged').length} flagged` : ''}`],
              ['road', 'Road'],
            ].map(([k, label]) => (
              <button
                key={k}
                onClick={() => setTab(k)}
                aria-pressed={tab === k}
                className={`flex-1 py-2 rounded-xl text-xs font-black ${tab === k ? 'bg-zinc-900 text-white' : 'text-zinc-600 hover:bg-zinc-100'}`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="bg-white border-2 border-zinc-200 rounded-2xl p-4 min-h-[280px]">
            {tab === 'intel' && <ZoneIntelligencePanel />}
            {tab === 'queue' && <OpsQueuePreview reports={safeReports} t={t} />}
            {tab === 'road' && <RoadStatusCard />}
          </div>
          {/* keep other panels mounted for senior dev cache correctness, visually hidden */}
          <div className="hidden" aria-hidden><ZoneIntelligencePanel /></div>
        </div>
      </div>

      <div id="ops-alerts" className="bg-white border-2 border-zinc-200 rounded-2xl p-4">
        <h3 className="text-xs font-black text-zinc-900">Road Network — Operational</h3>
        <div className="mt-2"><RoadStatusCard /></div>
      </div>
    </main>
  );
}
