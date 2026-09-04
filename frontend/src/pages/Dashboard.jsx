import React from 'react';
import { useMineContext } from '../context/MineContext';
import RiskSummaryCards from '../components/RiskSummary/RiskSummaryCards';
import QuickStatsBar from '../components/RiskSummary/QuickStatsBar';
import MineMap from '../components/RiskMap/MineMap';
import ZoneIntelligencePanel from '../components/ZoneDetails/ZoneIntelligencePanel';
import RoadStatusCard from '../components/Routing/RoadStatusCard';
import ReportModal from '../components/Reports/ReportModal';
import WhatIfDrawer from '../components/Simulation/WhatIfDrawer';
import SafeRouteModal from '../components/Routing/SafeRouteModal';
import CvCrackModal from '../components/ComputerVision/CvCrackModal';
import AlertPanel from '../components/Alerts/AlertPanel';
import { ErrorState } from '../components/Common/LoadingSkeleton';

export default function Dashboard() {
  const { error, refreshData } = useMineContext();

  if (error) {
    return (
      <div className="max-w-xl mx-auto my-20 p-4">
        <ErrorState message={error} onRetry={refreshData} />
      </div>
    );
  }

  return (
    <main className="max-w-[1920px] mx-auto px-3 sm:px-4 py-4 space-y-4">
      {/* 1. Risk Summary KPIs */}
      <RiskSummaryCards />

      {/* 2. Quick Operations & Weather Telemetry Bar */}
      <QuickStatsBar />

      {/* 3. Main Command Center Grid: Map (Left) + Zone Intelligence (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Left: Interactive Landslide GIS Map & Routing (7 cols on large displays) */}
        <div className="lg:col-span-7 xl:col-span-7 h-[640px] xl:h-[720px] sticky top-20">
          <MineMap />
        </div>

        {/* Right: Selected Slope Risk Intelligence & Decision Actions (5 cols) */}
        <div className="lg:col-span-5 xl:col-span-5 space-y-4">
          <ZoneIntelligencePanel />
        </div>
      </div>

      {/* 4. Road Network Status (R1-R4) with R2 Avoidance */}
      <RoadStatusCard />

      {/* Drawers & Modals */}
      <WhatIfDrawer />
      <SafeRouteModal />
      <ReportModal />
      <CvCrackModal />
      <AlertPanel />
    </main>
  );
}
