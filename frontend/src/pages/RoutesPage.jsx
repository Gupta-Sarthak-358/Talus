import React, { useEffect } from 'react';
import { useTalusContext } from '../context/TalusContext';
import RoadStatusCard from '../components/Routing/RoadStatusCard';

export default function RoutesPage() {
  const { setIsRouteModalOpen } = useTalusContext();
  useEffect(() => { setIsRouteModalOpen(true); }, []);
  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      <RoadStatusCard />
      <div className="bg-mine-card border border-mine-border rounded-2xl p-4 text-xs text-mine-muted text-center">
        Modal is open — compare <code className="font-mono">Shortest via R2 (89)</code> vs <code className="font-mono">Safe via R3+R4 (66)</code>. Deep link <code className="font-mono">/routes</code>.
      </div>
    </main>
  );
}
