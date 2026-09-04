import React, { useEffect } from 'react';
import { useTalusContext } from '../context/TalusContext';
import RoadStatusCard from '../components/Routing/RoadStatusCard';

export default function RoutesPage() {
  const { setIsRouteModalOpen, t } = useTalusContext();
  useEffect(() => { setIsRouteModalOpen(true); }, []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <RoadStatusCard />
      <div className="bg-mine-card border border-mine-border rounded-2xl p-4 text-xs text-mine-muted text-center">
        {t('page.routes_body')}
      </div>
    </main>
  );
}
