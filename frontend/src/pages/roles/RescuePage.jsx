import React, { useEffect } from 'react';
import { useTalusContext } from '../../context/TalusContext';
import RiskMap from '../../components/RiskMap/RiskMap';
import RoadStatusCard from '../../components/Routing/RoadStatusCard';
import RouteComparisonCard from '../../components/Routing/RouteComparisonCard';

export default function RescuePage() {
  const { setRole, activeRoutePlan, t } = useTalusContext();
  useEffect(() => setRole('rescue_team'), []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <div className="bg-risk-critical/10 border border-risk-critical/30 rounded-xl px-4 py-2 text-xs font-bold text-risk-critical">{t('rescue.banner')}</div>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-7 h-[560px]"><RiskMap /></div>
        <div className="lg:col-span-5 space-y-3">
          <RouteComparisonCard routePlan={activeRoutePlan} />
          <RoadStatusCard />
        </div>
      </div>
    </main>
  );
}
