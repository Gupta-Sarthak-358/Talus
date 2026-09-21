import React, { useEffect } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskMap from '../../components/RiskMap/RiskMap';
import RoadStatusCard from '../../components/Routing/RoadStatusCard';
import RouteComparisonCard from '../../components/Routing/RouteComparisonCard';
import ExposureCard from '../../components/Routing/ExposureCard';
import WarningStateCard from '../../components/Alerts/WarningStateCard';
import IsolationAlertCard from '../../components/Alerts/IsolationAlertCard';

/**
 * Rescue ingress — first-responder ops (NDRF/SDRF).
 * Sticky isolation+warning top, map 7 + exposure/route/road 5. Side first on mobile.
 * Safety language: Recommended route / Recommended staging — never guaranteed safe.
 * Villager never sees exposure details or road catalogue; rescue never sees district queue.
 */
export default function RescuePage() {
  const { setRole, activeRoutePlan, zones, roads, t } = useTalusContext();
  const liveZones = zones || [];
  const liveRoads = roads || [];
  const r2 = liveRoads.find((s) => s.id === 'R2');
  useEffect(() => setRole('rescue_team'), []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-red-700 text-white rounded-xl px-4 py-2.5 text-xs font-black tracking-wide flex flex-wrap items-center justify-between gap-2">
        <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-white animate-pulse" /> {t('rescue.banner')}</span>
        <span className="font-mono font-bold text-red-100">{liveZones.length} slopes · {liveRoads.length} segments LIVE</span>
      </div>
      <div className="space-y-3">
        <IsolationAlertCard />
        <WarningStateCard />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        <div className="lg:col-span-7 h-[620px] lg:sticky lg:top-[88px] order-2 lg:order-1 border-2 border-red-200 rounded-2xl overflow-hidden">
          <RiskMap />
        </div>
        <div className="lg:col-span-5 space-y-3 order-1 lg:order-2">
          <div className="bg-white border-2 border-zinc-200 rounded-2xl p-4">
            <h3 className="text-xs font-black text-zinc-900">Recommended ingress — avoid R2 ridge{r2 ? ` (${r2.status})` : ''}</h3>
            <p className="text-xs text-zinc-600 mt-1">Recommended route avoids at-risk ridge shortcut. Follow green solid (recommended), not red dashed (shortest). Final ingress with qualified personnel.</p>
          </div>
          <ExposureCard />
          <RouteComparisonCard routePlan={activeRoutePlan} />
          <RoadStatusCard compact />
        </div>
      </div>
    </main>
  );
}
